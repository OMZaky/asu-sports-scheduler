import os
from collections import defaultdict
from dotenv import load_dotenv
from supabase import create_client, Client

def fetch_and_format_availability():
    # 1. Connect to Supabase
    env_path = os.path.join(os.path.dirname(__file__), "web", ".env.local")
    load_dotenv(dotenv_path=env_path)
    url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    key = os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("Error: Supabase URL or Key not found in web/.env.local")
        return

    supabase: Client = create_client(url, key)
    
    print("Fetching data from Supabase...\n")
    teams_response = supabase.table("teams").select("*").execute()
    availability_response = supabase.table("availability").select("*").execute()
    
    teams_data = teams_response.data
    avail_data = availability_response.data
    
    if not teams_data:
        print("No teams found in the database.")
        return

    # 2. Group availability by team and day
    team_id_to_name = {t['id']: t['team_name'] for t in teams_data}
    team_id_to_captain = {t['id']: t['captain_name'] for t in teams_data}
    
    # Structure: dict[team_name] -> dict[day] -> list[time]
    organized_data = defaultdict(lambda: defaultdict(list))
    
    for a in avail_data:
        team_name = team_id_to_name.get(a['team_id'])
        if team_name:
            organized_data[team_name][a['day']].append(a['time'])

    # 3. Format the output
    days_order = {"Saturday": 1, "Sunday": 2, "Monday": 3, "Tuesday": 4, "Wednesday": 5, "Thursday": 6}
    
    output_lines = []
    output_lines.append("=========================================")
    output_lines.append("       TEAM AVAILABILITY REPORT")
    output_lines.append("=========================================\n")
    
    for team_id, team_name in team_id_to_name.items():
        captain = team_id_to_captain.get(team_id, "Unknown")
        output_lines.append(f" TEAM: {team_name} (Captain: {captain})")
        
        team_days = organized_data.get(team_name, {})
        if not team_days:
            output_lines.append("   [No availability submitted]")
        else:
            # Sort days chronologically
            sorted_days = sorted(team_days.keys(), key=lambda d: days_order.get(d, 7))
            
            for day in sorted_days:
                # Sort times chronologically
                times = team_days[day]
                sorted_times = sorted(times, key=lambda t: int(t.split(':')[0]) * 60 + int(t.split(':')[1]))
                output_lines.append(f"   - {day}: {', '.join(sorted_times)}")
                
        output_lines.append("-" * 40)
        
    final_output = "\n".join(output_lines)
    
    # 4. Save to file
    with open("team_availability_report.txt", "w", encoding="utf-8") as f:
        f.write(final_output)
        
    print(final_output)
    print("\n Report successfully saved to 'team_availability_report.txt'!")

if __name__ == "__main__":
    fetch_and_format_availability()
