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
    
    # Structure: dict[team_name] -> dict[day] -> list[time]
    organized_data = defaultdict(lambda: defaultdict(list))
    
    for a in avail_data:
        team_name = team_id_to_name.get(a['team_id'])
        if team_name:
            organized_data[team_name][a['day']].append(a['time'])

    # 3. Format the output into a GRID
    days_order = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday"]
    
    # Determine column widths
    col_widths = {"Team": 20}
    for day in days_order:
        col_widths[day] = len(day)
        
    # Calculate max width needed for each day based on the data
    for team, days_data in organized_data.items():
        col_widths["Team"] = max(col_widths["Team"], len(team) + 2)
        for day in days_order:
            times = days_data.get(day, [])
            if times:
                sorted_times = sorted(times, key=lambda t: int(t.split(':')[0]) * 60 + int(t.split(':')[1]))
                times_str = ", ".join(sorted_times)
                col_widths[day] = max(col_widths[day], len(times_str) + 2)

    output_lines = []
    
    # Create Header
    header = f"{'Team'.ljust(col_widths['Team'])} | " + " | ".join(day.ljust(col_widths[day]) for day in days_order)
    output_lines.append(header)
    output_lines.append("-" * len(header))
    
    # Create Rows
    for team_id, team_name in team_id_to_name.items():
        team_days = organized_data.get(team_name, {})
        
        row_str = f"{team_name.ljust(col_widths['Team'])} | "
        
        day_strs = []
        for day in days_order:
            times = team_days.get(day, [])
            if times:
                sorted_times = sorted(times, key=lambda t: int(t.split(':')[0]) * 60 + int(t.split(':')[1]))
                times_str = ", ".join(sorted_times)
            else:
                times_str = ""
            day_strs.append(times_str.ljust(col_widths[day]))
            
        row_str += " | ".join(day_strs)
        output_lines.append(row_str)
        
    final_output = "\n".join(output_lines)
    
    # 4. Save to file
    with open("team_availability_report.txt", "w", encoding="utf-8") as f:
        f.write(final_output)
        
    print(final_output)
    print("\n[SUCCESS] Grid Report successfully saved to 'team_availability_report.txt'!")

if __name__ == "__main__":
    fetch_and_format_availability()
