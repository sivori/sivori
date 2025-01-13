from github import Github
from datetime import datetime, timezone, timedelta
import os
import re
from collections import defaultdict

def get_contribution_streak(user):
    # Get user's events
    events = user.get_events()
    contribution_dates = defaultdict(bool)
    today = datetime.now(timezone.utc).date()
    
    # First, mark all dates with contributions
    for event in events:
        if event.type in ['PushEvent', 'CreateEvent', 'PullRequestEvent', 'IssuesEvent']:
            contribution_dates[event.created_at.date()] = True
    
    # Calculate current streak
    current_streak = 0
    current_date = today
    
    while contribution_dates[current_date]:
        current_streak += 1
        current_date = current_date - timedelta(days=1)
    
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
