from github import Github
from datetime import datetime, timezone, timedelta
import os
import re
from collections import defaultdict

def get_contribution_streak(user):
    contribution_dates = defaultdict(bool)
    today = datetime.now(timezone.utc).date()
    
    # Get all pages of events
    events = user.get_events()
    print(f"Fetching events for user {user.login}...")
    
    # First, mark all dates with contributions
    page_count = 0
    for event in events:
        page_count += 1
        if event.type in ['PushEvent', 'CreateEvent', 'PullRequestEvent', 'IssuesEvent']:
            event_date = event.created_at.date()
            contribution_dates[event_date] = True
            print(f"Found contribution on {event_date}: {event.type}")
            
        if page_count >= 300:
            break
    
    # Calculate current streak
    current_streak = 0
    longest_streak = 0
    current_date = today
    
    # Look back up to 365 days
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
    
    # Update the streak count in the README
    streak_pattern = r'Current Contribution Streak: \*\*\d+\*\*'
    new_streak_text = f'Current Contribution Streak: **{streak_count}**'
    
    if re.search(streak_pattern, content):
        updated_content = re.sub(streak_pattern, new_streak_text, content)
    else:
        # If the streak section doesn't exist, add it at the end
        updated_content = f'{content}\n\n{new_streak_text}'
    
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
