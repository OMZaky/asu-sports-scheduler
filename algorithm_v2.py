import os
import itertools
from collections import defaultdict
import random
from dotenv import load_dotenv
from supabase import create_client, Client

# ==========================================
# --- TOURNAMENT CONFIGURATION (V2) ---
# ==========================================

# 1. Exact Dates Mapping
DATE_MAPPING = {
    "Saturday": "Nov 7, 2026",
    "Sunday": "Nov 8, 2026",
    "Monday": "Nov 9, 2026",
    "Tuesday": "Nov 10, 2026",
    "Wednesday": "Nov 11, 2026",
    "Thursday": "Nov 12, 2026"
}

# 2. Lock Teams Together
# Define lists of teams that MUST be in the same group.
LOCKED_GROUPS = [
    # Example: ["Eldido", "Wax"],
    # Example: ["Royal house", "Mazareeta fc"]
]

# 3. Opening Match Configuration
# Force a specific match to happen at an exact day/time.
# The algorithm will automatically ensure they are in the same group.
# Set to None if you don't want a forced opening match.
OPENING_MATCH = {
    "team_a": "Under CTRL ",
    "team_b": "Eldido",
    "day": "Saturday",
    "time": "12:00"
}
# OPENING_MATCH = None

# ==========================================

def get_minutes(time_str):
    """Convert HH:MM to minutes from midnight."""
    h, m = map(int, time_str.split(':'))
    return h * 60 + m

def attempt_schedule(teams_list, availability_map, locked_groups, opening_match, group_size=4):
    groups = [[] for _ in range(4)]
    available_teams = list(teams_list)
    
    # Combine user locks + opening match lock
    locks = list(locked_groups)
    if opening_match:
        locks.append([opening_match["team_a"], opening_match["team_b"]])
        
    # Place locked teams safely
    for i, locked in enumerate(locks):
        target_group = groups[i % 4]
        for team in locked:
            if team in available_teams and len(target_group) < group_size:
                target_group.append(team)
                available_teams.remove(team)
                
    # Fill remaining spots randomly
    random.shuffle(available_teams)
    for group in groups:
        while len(group) < group_size and available_teams:
            group.append(available_teams.pop())
            
    matches = []
    for group in groups:
        for match in list(itertools.combinations(group, 2)):
            matches.append({"type": "Group Stage", "teams": match})
            
    MAX_CONCURRENT_MATCHES = 2
    booked_slots = defaultdict(int)
    team_schedule = defaultdict(set)
    final_schedule = []
    unscheduled = []
    
    # Process Opening Match explicitly
    if opening_match:
        om_slot = f"{opening_match['day']}-{opening_match['time']}"
        t_a = opening_match["team_a"]
        t_b = opening_match["team_b"]
        
        match_to_remove = None
        for m in matches:
            if (m["teams"][0] == t_a and m["teams"][1] == t_b) or (m["teams"][0] == t_b and m["teams"][1] == t_a):
                match_to_remove = m
                break
                
        if match_to_remove:
            matches.remove(match_to_remove)
            booked_slots[om_slot] += 1
            team_schedule[t_a].add(om_slot)
            team_schedule[t_b].add(om_slot)
            
            final_schedule.append({
                "Match": f"{t_a} vs {t_b}",
                "Type": "Group Stage (OPENING MATCH)",
                "Time": om_slot,
                "Pitch": f"Pitch {booked_slots[om_slot]}"
            })

    # Sort remaining matches by the LEAST number of common slots
    matches.sort(key=lambda m: len(availability_map[m["teams"][0]].intersection(availability_map[m["teams"][1]])))

    for match_info in matches:
        team_a, team_b = match_info["teams"]
        common_slots = list(availability_map[team_a].intersection(availability_map[team_b]))
        
        def score_slot(slot):
            bonus = 0
            day, time_str = slot.split('-')
            
            if any(existing.startswith(f"{day}-") for existing in team_schedule[team_a]):
                bonus -= 50
            if any(existing.startswith(f"{day}-") for existing in team_schedule[team_b]):
                bonus -= 50
                
            time_mins = get_minutes(time_str)
            if 600 <= time_mins <= 1020:
                bonus += 1
                
            # Extra bonus for 12:00 PM
            if time_mins == 720:
                bonus += 5

            days_order = {"Saturday": 1, "Sunday": 2, "Monday": 3, "Tuesday": 4, "Wednesday": 5, "Thursday": 6}
            return (-bonus, days_order.get(day, 7), time_mins)

        common_slots.sort(key=score_slot)
        
        scheduled = False
        for slot in common_slots:
            if booked_slots[slot] < MAX_CONCURRENT_MATCHES:
                if slot not in team_schedule[team_a] and slot not in team_schedule[team_b]:
                    booked_slots[slot] += 1
                    team_schedule[team_a].add(slot)
                    team_schedule[team_b].add(slot)
                    
                    pitch_num = booked_slots[slot]
                    final_schedule.append({
                        "Match": f"{team_a} vs {team_b}",
                        "Type": match_info["type"],
                        "Time": slot,
                        "Pitch": f"Pitch {pitch_num}"
                    })
                    scheduled = True
                    break 
        
        if not scheduled:
            unscheduled.append(f"{team_a} vs {team_b} ({match_info['type']})")
            
    # Calculate Knockout Risk Score
    knockout_risk = 0
    if len(groups) == 4:
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                for team1 in groups[i]:
                    for team2 in groups[j]:
                        common = availability_map[team1].intersection(availability_map[team2])
                        if len(common) == 0:
                            if (i == 0 and j == 1) or (i == 2 and j == 3):
                                knockout_risk += 100
                            else:
                                knockout_risk += 10
            
    return len(unscheduled), knockout_risk, groups, final_schedule, unscheduled, booked_slots

def generate_schedule():
    env_path = os.path.join(os.path.dirname(__file__), "web", ".env.local")
    load_dotenv(dotenv_path=env_path)
    url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    key = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("Error: Supabase credentials not found.")
        return

    supabase: Client = create_client(url, key)
    
    print("Fetching data from Supabase...")
    teams_response = supabase.table("teams").select("*").execute()
    availability_response = supabase.table("availability").select("*").execute()
    
    teams_data = teams_response.data
    avail_data = availability_response.data
    
    if not teams_data:
        print("No teams found.")
        return

    teams = [t['team_name'] for t in teams_data]
    team_id_to_name = {t['id']: t['team_name'] for t in teams_data}
    
    availability_map = defaultdict(set)
    for a in avail_data:
        team_name = team_id_to_name.get(a['team_id'])
        if team_name:
            availability_map[team_name].add(f"{a['day']}-{a['time']}")

    if len(teams) < 4:
        print("Need at least 4 teams.")
        return

    print("\nRunning 50,000 full Monte Carlo simulations (V2) with user constraints...")
    
    best_unscheduled_count = float('inf')
    best_risk_score = float('inf')
    best_groups = None
    best_schedule = None
    best_unscheduled_list = None
    best_booked_slots = None
    
    for i in range(50000):
        u_count, risk, g, sched, u_list, b_slots = attempt_schedule(list(teams), availability_map, LOCKED_GROUPS, OPENING_MATCH)
        
        if u_count < best_unscheduled_count:
            best_unscheduled_count = u_count
            best_risk_score = risk
            best_groups = g
            best_schedule = sched
            best_unscheduled_list = u_list
            best_booked_slots = b_slots
            
        elif u_count == best_unscheduled_count and risk < best_risk_score:
            best_risk_score = risk
            best_groups = g
            best_schedule = sched
            best_unscheduled_list = u_list
            best_booked_slots = b_slots

    print("\n--- TOURNAMENT DRAW (GROUP STAGE) ---")
    if best_unscheduled_count > 0:
        print(f"Note: Still {best_unscheduled_count} impossible matches.")
    else:
        print("Found a 100% PERFECT Group Stage draw!")

    # 3. Knockout Stage Logic
    all_possible_slots = set()
    for slots in availability_map.values():
        all_possible_slots.update(slots)
        
    days_order = {"Saturday": 1, "Sunday": 2, "Monday": 3, "Tuesday": 4, "Wednesday": 5, "Thursday": 6}
    sorted_all_slots = sorted(list(all_possible_slots), key=lambda x: (days_order.get(x.split('-')[0], 7), get_minutes(x.split('-')[1])), reverse=True)
    
    knockout_matches = [
        "Final (TBD vs TBD)",
        "Semi-Final 1 (TBD vs TBD)",
        "Semi-Final 2 (TBD vs TBD)",
        "Quarter-Final 1 (TBD vs TBD)",
        "Quarter-Final 2 (TBD vs TBD)",
        "Quarter-Final 3 (TBD vs TBD)",
        "Quarter-Final 4 (TBD vs TBD)"
    ]
    
    MAX_CONCURRENT_MATCHES = 2
    for ko_match in knockout_matches:
        scheduled = False
        for slot in sorted_all_slots:
            if best_booked_slots[slot] < MAX_CONCURRENT_MATCHES:
                best_booked_slots[slot] += 1
                pitch_num = best_booked_slots[slot]
                best_schedule.append({
                    "Match": ko_match,
                    "Type": "Knockout",
                    "Time": slot,
                    "Pitch": f"Pitch {pitch_num}"
                })
                scheduled = True
                break
        if not scheduled:
            best_unscheduled_list.append(f"{ko_match} (Knockout)")

    # 4. Output Results
    output_lines = []
    
    output_lines.append("--- TOURNAMENT GROUPS ---")
    for i, group in enumerate(best_groups):
        output_lines.append(f"Group {chr(65+i)}: {', '.join(group)}")
        
    output_lines.append("\n--- FINAL TOURNAMENT SCHEDULE ---")
    
    # Sort primarily by Day/Time, but ensure Opening Match is first on its day
    best_schedule.sort(key=lambda x: (
        days_order.get(x["Time"].split('-')[0], 7), 
        get_minutes(x["Time"].split('-')[1]),
        0 if "OPENING MATCH" in x["Type"] else 1
    ))
    
    current_time = None
    for match in best_schedule:
        if match["Time"] != current_time:
            current_time = match["Time"]
            day, time = current_time.split("-")
            exact_date = DATE_MAPPING.get(day, "Unknown Date")
            output_lines.append(f"\n[ {day}, {exact_date} at {time} ]")
            
        output_lines.append(f"  - [{match['Type']}] {match['Match']} ({match['Pitch']})")

    if best_unscheduled_list:
        output_lines.append("\nWARNING: Could not schedule:")
        for m in best_unscheduled_list:
            output_lines.append(f"  - {m}")
    else:
        output_lines.append("\nAll matches successfully scheduled!")

    final_output = "\n".join(output_lines)
    print(final_output)
    
    with open("tournament_schedule_v2.txt", "w", encoding="utf-8") as f:
        f.write(final_output)
        
    print("\nSchedule saved to 'tournament_schedule_v2.txt'!")

if __name__ == "__main__":
    generate_schedule()
