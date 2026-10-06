import json
import itertools
from collections import defaultdict
import random

def get_minutes(time_str):
    """Convert HH:MM to minutes from midnight."""
    h, m = map(int, time_str.split(':'))
    return h * 60 + m

def is_adjacent(slot1, slot2):
    """Check if two slots are on the same day and exactly 30 mins apart."""
    day1, time1 = slot1.split('-')
    day2, time2 = slot2.split('-')
    if day1 != day2:
        return False
    return abs(get_minutes(time1) - get_minutes(time2)) == 30

def generate_schedule(data_file):
    # 1. Load Data
    try:
        with open(data_file, 'r') as f:
            teams_data = json.load(f)
    except FileNotFoundError:
        print(f"Please create {data_file} with the collected data.")
        return

    teams = [t['teamName'] for t in teams_data]
    if len(teams) < 4:
        print("Need at least 4 teams for Group Stages + Knockouts.")
        return

    availability_map = {}
    for t in teams_data:
        slots = set([f"{s['day']}-{s['time']}" for s in t['availability']])
        availability_map[t['teamName']] = slots

    # 2. Tournament Structure: Group Stages
    print("--- 🎲 TOURNAMENT DRAW 🎲 ---")
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
        
        # Determine the best slot based on consecutive matches & prime time
        def score_slot(slot):
            bonus = 0
            # If the slot is adjacent to ANY already scheduled match for team A, they get a bonus (consecutive matches)
            if any(is_adjacent(slot, existing) for existing in team_schedule[team_a]):
                bonus += 2  # +2 weight for consecutive
            # If the slot is adjacent to ANY already scheduled match for team B, they get a bonus
            if any(is_adjacent(slot, existing) for existing in team_schedule[team_b]):
                bonus += 2  # +2 weight for consecutive
                
            day, time_str = slot.split('-')
            time_mins = get_minutes(time_str)
            
            # Prime time bonus: between 10 AM (600 mins) and 5 PM (1020 mins)
            if 600 <= time_mins <= 1020:
                bonus += 1  # +1 weight for prime time

            # We want to sort by bonus DESCENDING, and then chronologically ascending.
            days_order = {"Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4, "Friday": 5, "Saturday": 6, "Sunday": 7}
            return (-bonus, days_order.get(day, 8), time_mins)

        # Sort the common slots with our consecutive match scoring
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

    # 4. Output Results
    print("--- 🏆 FINAL TOURNAMENT SCHEDULE 🏆 ---")
    
    # Sort for final output
    days_order = {"Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4, "Friday": 5, "Saturday": 6, "Sunday": 7}
    final_schedule.sort(key=lambda x: (days_order.get(x["Time"].split('-')[0], 8), get_minutes(x["Time"].split('-')[1])))
    
    current_time = None
    for match in final_schedule:
        if match["Time"] != current_time:
            current_time = match["Time"]
            day, time = current_time.split("-")
            print(f"\n📅 {day} at {time}:")
            
        print(f"  ⚽ [{match['Type']}] {match['Match']} ({match['Pitch']})")

    if unscheduled:
        print("\n⚠️ WARNING: Could not find common 30-min times for the following matches:")
        for m in unscheduled:
            print(f"  - {m}")
    else:
        print("\n✅ All group stage matches successfully scheduled with consecutive matches & prime daytime favored!")

if __name__ == "__main__":
    generate_schedule("teams_data.json")
