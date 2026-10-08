import os
import itertools
from collections import defaultdict
import random
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime, timedelta

# ==========================================
# --- TOURNAMENT CONFIGURATION (V3) ---
# ==========================================

TOURNAMENT_START_DATE = None

LOCKED_GROUPS = [
    ["Under CTRL ", "Nezam eltayebat", "khaly w sohabo", "3azema"],
    ["Last dance"],
    ["El hagamin ", "Royal house"],
    ["3 sayma"]
]

OPENING_MATCH = {
    "team_a": "Under CTRL ",
    "team_b": "khaly w sohabo",
    "day": "Sunday",
    "time": "12:00"
}
# OPENING_MATCH = None

MAX_MATCHES_PER_DAY = 4

# ==========================================

def get_minutes(time_str):
    h, m = map(int, time_str.split(':'))
    return h * 60 + m

def attempt_schedule(teams_list, availability_map, locked_groups, opening_match, num_weeks, group_size=4):
    groups = [[] for _ in range(4)]
    available_teams = list(teams_list)
    
    locks = list(locked_groups)
    if opening_match:
        locks.append([opening_match["team_a"], opening_match["team_b"]])
        
    for i, locked in enumerate(locks):
        target_group = groups[i % 4]
        for team in locked:
            if team in available_teams and len(target_group) < group_size:
                target_group.append(team)
                available_teams.remove(team)
                
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
    matches_per_day = defaultdict(int)
    team_schedule = defaultdict(set)
    final_schedule = []
    unscheduled = []
    
    days_order = {"Saturday": 1, "Sunday": 2, "Monday": 3, "Tuesday": 4, "Wednesday": 5, "Thursday": 6}

    if opening_match:
        om_slot = f"W1-{opening_match['day']}-{opening_match['time']}"
        om_day_key = f"W1-{opening_match['day']}"
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
            matches_per_day[om_day_key] += 1
            team_schedule[t_a].add(om_slot)
            team_schedule[t_b].add(om_slot)
            
            final_schedule.append({
                "Match": f"{t_a} vs {t_b}",
                "Type": "Group Stage (OPENING MATCH)",
                "Time": om_slot,
                "Pitch": f"Pitch {booked_slots[om_slot]}"
            })

    # Sort remaining matches by least overlapping availability
    matches.sort(key=lambda m: len(availability_map[m["teams"][0]].intersection(availability_map[m["teams"][1]])))

    for match_info in matches:
        team_a, team_b = match_info["teams"]
        common_slots = list(availability_map[team_a].intersection(availability_map[team_b]))
        
        def score_slot(slot):
            bonus = 0
            w_str, day, time_str = slot.split('-')
            week_num = int(w_str[1:])
            d_ord = days_order.get(day, 7)
            time_mins = get_minutes(time_str)
            
            day_key = f"{w_str}-{day}"
            if any(existing.startswith(f"{day_key}-") for existing in team_schedule[team_a]):
                bonus -= 50
            if any(existing.startswith(f"{day_key}-") for existing in team_schedule[team_b]):
                bonus -= 50
                
            if 600 <= time_mins <= 1020:
                bonus += 1
            if time_mins == 720:
                bonus += 5

            return (-bonus, week_num, d_ord, time_mins)

        common_slots.sort(key=score_slot)
        
        scheduled = False
        for slot in common_slots:
            w_str, day, time_str = slot.split('-')
            week_num = int(w_str[1:])
            d_ord = days_order.get(day, 7)
            t_mins = get_minutes(time_str)
            day_key = f"{w_str}-{day}"
            
            # Constraint 1: Must be AFTER opening match
            if opening_match:
                om_week = 1
                om_day_order = days_order.get(opening_match['day'], 7)
                om_time = get_minutes(opening_match['time'])
                
                if week_num < om_week: continue
                if week_num == om_week and d_ord < om_day_order: continue
                if week_num == om_week and d_ord == om_day_order and t_mins <= om_time: continue

            # Constraint: Matches must not be later than 16:30 (990 minutes)
            if t_mins > 990:
                continue

            # Constraint 2: Max matches per day
            if matches_per_day[day_key] >= MAX_MATCHES_PER_DAY:
                continue
                
            # Constraint 3: Max 1 match per team per day
            if any(s.startswith(f"{day_key}-") for s in team_schedule[team_a]): continue
            if any(s.startswith(f"{day_key}-") for s in team_schedule[team_b]): continue

            if booked_slots[slot] < MAX_CONCURRENT_MATCHES:
                booked_slots[slot] += 1
                matches_per_day[day_key] += 1
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
            
    return len(unscheduled), knockout_risk, groups, final_schedule, unscheduled, booked_slots, matches_per_day

def generate_schedule(num_weeks, output_filename):
    env_path = os.path.join(os.path.dirname(__file__), "web", ".env.local")
    load_dotenv(dotenv_path=env_path)
    url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    key = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    supabase: Client = create_client(url, key)
    
    teams_response = supabase.table("teams").select("*").execute()
    availability_response = supabase.table("availability").select("*").execute()
    teams_data = teams_response.data
    avail_data = availability_response.data
    
    teams = [t['team_name'] for t in teams_data]
    team_id_to_name = {t['id']: t['team_name'] for t in teams_data}
    
    availability_map = defaultdict(set)
    for a in avail_data:
        team_name = team_id_to_name.get(a['team_id'])
        if team_name:
            # Duplicate the slot across all weeks
            for w in range(1, num_weeks + 1):
                availability_map[team_name].add(f"W{w}-{a['day']}-{a['time']}")

    print(f"\nRunning 10,000 Monte Carlo simulations for {num_weeks} WEEKS...")
    
    best_unscheduled_count = float('inf')
    best_risk_score = float('inf')
    best_groups = None
    best_schedule = None
    best_unscheduled_list = None
    best_booked_slots = None
    best_matches_per_day = None
    
    for i in range(10000):
        u_count, risk, g, sched, u_list, b_slots, mpd = attempt_schedule(list(teams), availability_map, LOCKED_GROUPS, OPENING_MATCH, num_weeks)
        
        if u_count < best_unscheduled_count:
            best_unscheduled_count = u_count
            best_risk_score = risk
            best_groups = g
            best_schedule = sched
            best_unscheduled_list = u_list
            best_booked_slots = b_slots
            best_matches_per_day = mpd
            
        elif u_count == best_unscheduled_count and risk < best_risk_score:
            best_risk_score = risk
            best_groups = g
            best_schedule = sched
            best_unscheduled_list = u_list
            best_booked_slots = b_slots
            best_matches_per_day = mpd

    all_possible_slots = set()
    for slots in availability_map.values():
        all_possible_slots.update(slots)
        
    days_order = {"Saturday": 1, "Sunday": 2, "Monday": 3, "Tuesday": 4, "Wednesday": 5, "Thursday": 6}
    sorted_all_slots = sorted(list(all_possible_slots), key=lambda x: (
        int(x.split('-')[0][1:]), 
        days_order.get(x.split('-')[1], 7), 
        get_minutes(x.split('-')[2])
    ), reverse=True)
    
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
            w_str, day, time_str = slot.split('-')
            day_key = f"{w_str}-{day}"
            
            # Constraint: Knockout matches MUST be exactly at 12:00 (Only for 3 week schedule)
            if num_weeks == 3:
                if time_str != "12:00":
                    continue
            else:
                if get_minutes(time_str) > 990:
                    continue
                
            # Constraint: Must be AFTER opening match
            if OPENING_MATCH:
                om_week = 1
                om_day_order = days_order.get(OPENING_MATCH['day'], 7)
                om_time = get_minutes(OPENING_MATCH['time'])
                
                week_num = int(w_str[1:])
                d_ord = days_order.get(day, 7)
                t_mins = get_minutes(time_str)
                
                if week_num < om_week: continue
                if week_num == om_week and d_ord < om_day_order: continue
                if week_num == om_week and d_ord == om_day_order and t_mins <= om_time: continue
            
            if best_matches_per_day[day_key] >= MAX_MATCHES_PER_DAY:
                continue
                
            if best_booked_slots[slot] < MAX_CONCURRENT_MATCHES:
                best_booked_slots[slot] += 1
                best_matches_per_day[day_key] += 1
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

    output_lines = []
    if best_unscheduled_count > 0:
        output_lines.append(f"Note: Still {best_unscheduled_count} impossible matches.")
    else:
        output_lines.append(f"Found a 100% PERFECT Group Stage draw for {num_weeks} weeks!")
        
    output_lines.append(f"Knockout Clash Risk Score: {best_risk_score}\n")
    output_lines.append("--- TOURNAMENT GROUPS ---")
    for i, group in enumerate(best_groups):
        output_lines.append(f"Group {chr(65+i)}: {', '.join(group)}")
        
    output_lines.append("\n--- FINAL TOURNAMENT SCHEDULE ---")
    
    best_schedule.sort(key=lambda x: (
        int(x["Time"].split('-')[0][1:]), 
        days_order.get(x["Time"].split('-')[1], 7), 
        get_minutes(x["Time"].split('-')[2]),
        0 if "OPENING MATCH" in x["Type"] else 1
    ))
    
    try:
        if TOURNAMENT_START_DATE:
            start_date_obj = datetime.strptime(TOURNAMENT_START_DATE, "%Y-%m-%d")
        else:
            today = datetime.today()
            target_day_name = OPENING_MATCH["day"] if OPENING_MATCH else "Saturday"
            weekday_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6}
            target_weekday = weekday_map[target_day_name]
            
            days_ahead = target_weekday - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
                
            target_date_obj = today + timedelta(days=days_ahead)
            offset = days_order[target_day_name] - 1
            start_date_obj = target_date_obj - timedelta(days=offset)
            
        date_mapping = {}
        for w in range(1, num_weeks + 1):
            for day, order in days_order.items():
                day_date = start_date_obj + timedelta(weeks=w-1, days=order - 1)
                date_mapping[f"W{w}-{day}"] = day_date.strftime("%b %d, %Y")
    except Exception as e:
        date_mapping = {}
    
    current_time = None
    for match in best_schedule:
        if match["Time"] != current_time:
            current_time = match["Time"]
            w_str, day, time = current_time.split("-")
            exact_date = date_mapping.get(f"{w_str}-{day}", "Unknown Date")
            output_lines.append(f"\n[ {w_str} - {day}, {exact_date} at {time} ]")
            
        output_lines.append(f"  - [{match['Type']}] {match['Match']} ({match['Pitch']})")

    if best_unscheduled_list:
        output_lines.append("\nWARNING: Could not schedule:")
        for m in best_unscheduled_list:
            output_lines.append(f"  - {m}")
    else:
        output_lines.append("\nAll matches successfully scheduled!")

    final_output = "\n".join(output_lines)
    print(final_output)
    
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(final_output)
    print(f"\nSaved to {output_filename}")

if __name__ == "__main__":
    generate_schedule(num_weeks=2, output_filename="tournament_schedule_2_weeks.txt")
    generate_schedule(num_weeks=3, output_filename="tournament_schedule_3_weeks.txt")
