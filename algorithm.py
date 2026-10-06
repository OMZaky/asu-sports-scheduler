import os
import itertools
from collections import defaultdict
import random
from dotenv import load_dotenv
from supabase import create_client, Client

def get_minutes(time_str):
    """Convert HH:MM to minutes from midnight."""
    h, m = map(int, time_str.split(':'))
    return h * 60 + m



def generate_schedule():
    # 1. Connect to Supabase and Load Data
    env_path = os.path.join(os.path.dirname(__file__), "web", ".env.local")
    load_dotenv(dotenv_path=env_path)
    url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    key = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("Error: Supabase URL or Key not found in .env file.")
        return

    supabase: Client = create_client(url, key)
    
    print("Fetching data from Supabase...")
    teams_response = supabase.table("teams").select("*").execute()
    availability_response = supabase.table("availability").select("*").execute()
    
    teams_data = teams_response.data
    avail_data = availability_response.data
    
    if not teams_data:
        print("No teams found in the database. Please submit some teams on the website first!")
        return

    teams = [t['team_name'] for t in teams_data]
    
    # Map team_id to team_name
    team_id_to_name = {t['id']: t['team_name'] for t in teams_data}
    
    availability_map = defaultdict(set)
    for a in avail_data:
        team_name = team_id_to_name.get(a['team_id'])
        if team_name:
            availability_map[team_name].add(f"{a['day']}-{a['time']}")

    if len(teams) < 4:
        print(f"Only {len(teams)} teams registered. Need at least 4 teams for Group Stages + Knockouts.")
        return

    # 2. Tournament Structure: Group Stages
    print("\n--- TOURNAMENT DRAW (GROUP STAGE) ---")
    random.shuffle(teams)
    
    group_size = 4
    groups = [teams[i:i + group_size] for i in range(0, len(teams), group_size)]
    
    matches = []
    for i, group in enumerate(groups):
        print(f"Group {chr(65+i)}: {', '.join(group)}")
        group_matches = list(itertools.combinations(group, 2))
        for match in group_matches:
            matches.append({"type": "Group Stage", "teams": match})
            
    print(f"\nTotal Group Stage Matches to schedule: {len(matches)}\n")

    # 3. Scheduling logic
    MAX_CONCURRENT_MATCHES = 2
    booked_slots = defaultdict(int)
    team_schedule = defaultdict(set)
    final_schedule = []
    unscheduled = []

    # Sort matches by the LEAST number of common slots (hardest to schedule first)
    matches.sort(key=lambda m: len(availability_map[m["teams"][0]].intersection(availability_map[m["teams"][1]])))

    for match_info in matches:
        team_a, team_b = match_info["teams"]
        common_slots = list(availability_map[team_a].intersection(availability_map[team_b]))
        
        def score_slot(slot):
            bonus = 0
            day, time_str = slot.split('-')
            
            # Penalize multiple matches on the same day for either team (unfavored but acceptable)
            if any(existing.startswith(f"{day}-") for existing in team_schedule[team_a]):
                bonus -= 50
            if any(existing.startswith(f"{day}-") for existing in team_schedule[team_b]):
                bonus -= 50
                
            time_mins = get_minutes(time_str)
            if 600 <= time_mins <= 1020:
                bonus += 1

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

    # 4. Knockout Stage Logic
    # We will reserve slots on the latest available days for the knockouts.
    # Quarter Finals (4 matches), Semi Finals (2 matches), Final (1 match).
    print("--- SCHEDULING KNOCKOUT STAGE ---")
    all_possible_slots = set()
    for slots in availability_map.values():
        all_possible_slots.update(slots)
        
    # Sort all slots chronologically so we can pick the LATEST ones for knockouts
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
    
    for ko_match in knockout_matches:
        scheduled = False
        for slot in sorted_all_slots:
            if booked_slots[slot] < MAX_CONCURRENT_MATCHES:
                booked_slots[slot] += 1
                pitch_num = booked_slots[slot]
                final_schedule.append({
                    "Match": ko_match,
                    "Type": "Knockout",
                    "Time": slot,
                    "Pitch": f"Pitch {pitch_num}"
                })
                scheduled = True
                break
        if not scheduled:
            unscheduled.append(f"{ko_match} (Knockout)")

    # 5. Output Results
    output_lines = []
    output_lines.append("\n--- FINAL TOURNAMENT SCHEDULE ---")
    
    final_schedule.sort(key=lambda x: (days_order.get(x["Time"].split('-')[0], 7), get_minutes(x["Time"].split('-')[1])))
    
    current_time = None
    for match in final_schedule:
        if match["Time"] != current_time:
            current_time = match["Time"]
            day, time = current_time.split("-")
            output_lines.append(f"\n[ {day} at {time} ]")
            
        output_lines.append(f"  - [{match['Type']}] {match['Match']} ({match['Pitch']})")

    if unscheduled:
        output_lines.append("\nWARNING: Could not find available times for the following matches:")
        for m in unscheduled:
            output_lines.append(f"  - {m}")
    else:
        output_lines.append("\nAll group stage and knockout matches successfully scheduled!")

    final_output = "\n".join(output_lines)
    print(final_output)
    
    with open("tournament_schedule.txt", "w", encoding="utf-8") as f:
        f.write(final_output)
        
    print("\nSchedule has been successfully saved to 'tournament_schedule.txt'!")

if __name__ == "__main__":
    generate_schedule()
