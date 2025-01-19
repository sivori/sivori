from github import Github
from datetime import datetime, timezone, timedelta
import os
import re
from collections import defaultdict
import requests
from PIL import Image, ImageDraw, ImageFont
import os.path

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

def create_streak_image(streak_count):
    """Create an image with the streak information"""
    # Set up image dimensions
    width = 800
    height = 200
    
    # Create new image with dark background
    image = Image.new('RGB', (width, height), color='#0D1117')
    draw = ImageDraw.Draw(image)
    
    # Try to load custom font, fall back to default if not found
    try:
        # You'll need to provide these font files or use different ones
        title_font = ImageFont.truetype('fonts/Roboto-Bold.ttf', 60)
        stats_font = ImageFont.truetype('fonts/Roboto-Regular.ttf', 40)
    except IOError:
        # Fallback to default font
        title_font = ImageFont.load_default()
        stats_font = ImageFont.load_default()
    
    # Calculate level and rank
    level = min(streak_count // 7, 99)
    ranks = ["ROOKIE", "CODER", "HACKER", "MASTER"]
    rank = ranks[min(streak_count // 10, 3)]
    
    # Draw streak title
    draw.text((40, 30), 'GitHub Streak', fill='#58A6FF', font=title_font)
    
    # Draw stats
    stats_y = 100
    draw.text((40, stats_y), f'Level: {level}', fill='#C9D1D9', font=stats_font)
    draw.text((250, stats_y), f'Current: {streak_count}', fill='#C9D1D9', font=stats_font)
    draw.text((500, stats_y), f'Rank: {rank}', fill='#C9D1D9', font=stats_font)
    
    # Save image
    os.makedirs('assets', exist_ok=True)
    image_path = 'assets/streak.png'
    image.save(image_path)
    return image_path

def update_readme(streak_count):
    # Create the streak image
    image_path = create_streak_image(streak_count)
    
    with open('README.md', 'r') as file:
        content = file.read()
    
    # Create content with both ASCII art and image
    streak_content = f"""
![GitHub Streak](assets/streak.png)

╔══════════════════════════════════════════════════════╗
║  ░██████╗████████╗██████╗░███████╗░█████╗░██╗░░██╗   ║
║  ██╔════╝╚══██╔══╝██╔══██╗██╔════╝██╔══██╗██║░██╔╝   ║
║  ╚█████╗░░░░██║░░░██████╔╝█████╗░░███████║█████═╝░   ║
║  ░╚═══██╗░░░██║░░░██╔══██╗██╔══╝░░██╔══██║██╔═██╗░   ║
║  ██████╔╝░░░██║░░░██║░░██║███████╗██║░░██║██║░╚██╗   ║
║  ╚═════╝░░░░╚═╝░░░╚═╝░░╚═╝╚══════╝╚═╝░░╚═╝╚═╝░░╚═╝   ║
║───────────────────────────────────────────────────-──║
║  LEVEL: {min(streak_count // 7, 99):>2}  ►  CURRENT: {streak_count:>3}  ►  RANK: {["ROOKIE", "CODER", "HACKER", "MASTER"][min(streak_count // 10, 3)]:>6}    ║
╚══════════════════════════════════════════════════════╝
```"""

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
║───────────────────────────────────────────────────-──║
║  LEVEL: {min(streak_count // 7, 99):>2}  ►  CURRENT: {streak_count:>3}  ►  RANK: {["ROOKIE", "CODER", "HACKER", "MASTER"][min(streak_count // 10, 3)]:>6}    ║
╚══════════════════════════════════════════════════════╝
```"""

    # Find the section markers
    start_marker = '<!--START_SECTION:streak-->'
    end_marker = '<!--END_SECTION:streak-->'
    
    start_index = content.find(start_marker)
    end_index = content.find(end_marker)
    
    if start_index != -1 and end_index != -1:
        # Replace everything between the markers with the new content
        before_section = content[:start_index + len(start_marker)]
        after_section = content[end_index:]
        updated_content = f'{before_section}\n\n{streak_ascii}\n\n{after_section}'
    else:
        # If markers don't exist, append to the end
        updated_content = f'{content}\n\n{start_marker}\n\n{streak_ascii}\n\n{end_marker}'
    
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
