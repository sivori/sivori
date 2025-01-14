from github import Github
from datetime import datetime, timezone, timedelta
import os
import re
from collections import defaultdict
import requests

def get_contribution_data(token):
    headers = {
        'Authorization': f'Bearer {token}',
    }
    
    query = """
    query {
      viewer {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
      }
    }
    """
    
    response = requests.post(
        'https://api.github.com/graphql',
        json={'query': query},
        headers=headers
    )
    
    print(f"Response status code: {response.status_code}")
    print(f"Response headers: {response.headers}")
    print(f"Response body: {response.text}")
    
    if response.status_code != 200:
        print(f"Error from GitHub API: {response.status_code}")
        print(f"Response: {response.text}")
        raise Exception("Failed to fetch contribution data")
    
    data = response.json()
    if 'errors' in data:
        print(f"GraphQL Errors: {data['errors']}")
        raise Exception("GraphQL query failed")
        
    return data

def get_contribution_streak(user):
    contribution_dates = defaultdict(bool)
    today = datetime.now(timezone.utc).date()
    
    # Get contribution data from GraphQL API
    token = os.environ['GITHUB_TOKEN']
    data = get_contribution_data(token)
    
    # Parse the contribution data
    weeks = data['data']['viewer']['contributionsCollection']['contributionCalendar']['weeks']
    for week in weeks:
        for day in week['contributionDays']:
            date = datetime.strptime(day['date'], '%Y-%m-%d').date()
            if day['contributionCount'] > 0:
                contribution_dates[date] = True
                print(f"Found contributions on {date}: {day['contributionCount']}")
    
    # Calculate current streak
    current_streak = 0
    streak_active = False
    
    for i in range(365):
        check_date = today - timedelta(days=i)
        
        if contribution_dates[check_date]:
            current_streak += 1
            streak_active = True
            print(f"Counting {check_date} in streak")
        else:
            # If this is today or yesterday, continue the streak
            if i <= 1 and current_streak > 0:
                print(f"No contributions on {check_date}, but within 1-day grace period")
                continue
                
            if streak_active:
                print(f"Streak breaks at {check_date} (no contributions)")
                streak_active = False
                break
    
    print(f"Final streak count: {current_streak}")
    
    # Print full contribution timeline for verification
    print("\nFull contribution timeline for the last 14 days:")
    for i in range(14):
        check_date = today - timedelta(days=i)
        status = "✓" if contribution_dates[check_date] else "✗"
        print(f"{check_date}: {status}")
    
    return current_streak

def update_readme(streak_count):
    with open('README.md', 'r') as file:
        content = file.read()
    
    # Create compact retro ASCII art display
    streak_ascii = f"""
```
╔══════════════════════════════════════════════════════╗
║  ░██████╗████████╗██████╗░███████╗░█████╗░██╗░░██╗   ║
║  ██╔════╝╚══██╔══╝██╔══██╗██╔════╝██╔══██╗██║░██╔╝   ║
║  ╚█████╗░░░░██║░░░██████╔╝█████╗░░███████║█████═╝░   ║
║  ░╚═══██╗░░░██║░░░██╔══██╗██╔══╝░░██╔══██║██╔═██╗░   ║
║  ██████╔╝░░░██║░░░██║░░██║███████╗██║░░██║██║░╚██╗   ║
║  ╚═════╝░░░░╚═╝░░░╚═╝░░╚═╝╚══════╝╚═╝░░╚═╝╚═╝░░╚═╝   ║
║─────────────────────────────────────────────────────║
║  LEVEL: {min(streak_count // 7, 99):>2}  ►  CURRENT: {streak_count:>3}  ►  RANK: {["ROOKIE", "CODER", "HACKER", "MASTER"][min(streak_count // 10, 3)]:>6}  ║
╚══════════════════════════════════════════════════════╝
```"""

    # Update the streak count in the README
    streak_pattern = r'Current Contribution Streak: \*\*\d+\*\*'
    new_streak_text = streak_ascii
    
    if re.search(streak_pattern, content):
        updated_content = re.sub(streak_pattern, new_streak_text, content)
    else:
        updated_content = f'{content}\n\n{streak_ascii}'
    
    with open('README.md', 'w') as file:
        file.write(updated_content)
    
    print(f"Updated README.md with streak count: {streak_count}")

def main():
    # Initialize GitHub client
    g = Github(os.environ['GITHUB_TOKEN'])
    
    # Get the repository owner
    repo = g.get_repo(os.environ['GITHUB_REPOSITORY'])
    user = repo.owner
    
    # Calculate streak
    streak = get_contribution_streak(user)
    
    # Update README
    update_readme(streak)

if __name__ == '__main__':
    main()
