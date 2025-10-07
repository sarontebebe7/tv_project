import requests
import time
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

with open("/workspaces/tv_project/cron_log.txt", "a") as log:
    from datetime import datetime
    log.write(f"{datetime.now()}: Started {__file__}\n")

# Base date: today is Thursday, 2 October 2025
base_date = datetime.today()


# Slovak day names mapped to weekday index (0 = Monday)
day_map = {
    'Pondelok': 0,
    'Utorok': 1,
    'Streda': 2,
    'Štvrtok': 3,
    'Piatok': 4,
    'Sobota': 5,
    'Nedeľa': 6
}

# Generate date lookup for the week
date_lookup = {}
for name, weekday_index in day_map.items():
    delta = weekday_index - base_date.weekday()
    if delta < 0:
        delta += 7  # wrap to next week
    date_lookup[name] = (base_date + timedelta(days=delta)).strftime('%d.%m.%Y')

# Scrape the page
url = 'https://tv-program.sk/discovery-channel/cely-den/'
response = requests.get(url)
soup = BeautifulSoup(response.content.decode('utf-8', errors='replace'), 'html.parser')

# Extract channel name
channel_tag = soup.select_one('.page__title-name')
channel_name = channel_tag.text.strip() if channel_tag else 'Unknown'

all_programs = []

# Loop through each day block
for day_block in soup.select('.programme-list'):
    day_tag = day_block.select_one('.programme-list__header .col-auto.h4')
    day_name = day_tag.text.strip() if day_tag else 'Unknown'
    date_str = date_lookup.get(day_name, '')

    for item in day_block.select('.programme-list__item'):
        time_tag = item.select_one('time.programme-list__time')
        title_tag = item.select_one('a.programme-list__title')

        start_time_str = time_tag.text.strip() if time_tag else None
        title = title_tag.text.strip() if title_tag else None
        link = title_tag.get('href') if title_tag else None

        try:
            start_time_obj = datetime.strptime(start_time_str, '%H:%M')
        except:
            start_time_obj = None

        all_programs.append({
            'Title': title,
            'Day': day_name,
            'Date': date_str,
            'Start Time': start_time_str,
            'Start Time Obj': start_time_obj,
            'Channel': channel_name,
            'Link': link
        })

def scrape_program_details(relative_url):
    full_url = f'https://www.tv-program.sk{relative_url}'
    try:
        response = requests.get(full_url, timeout=10)
        time.sleep(0.5) 
        soup = BeautifulSoup(response.content.decode('utf-8', errors='replace'), 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {full_url}: {e}")
        return {
            'Original Name': '',
            'Year': '',
            'Description': '',
            'Score': '',
            'Genre': ''
        }



    # Extract original name
    original_name_tag = soup.find('strong', string='Pôvodný názov:')
    original_name = original_name_tag.find_next('span').text.strip() if original_name_tag else ''

    # Extract year
    year_tag = soup.find('strong', string='Rok výroby:')
    year = year_tag.find_next('span').text.strip() if year_tag else ''

    # Extract description
    description_tag = soup.select_one('.post__body p')
    description = description_tag.text.strip() if description_tag else ''

    # Extract score
    score_tag = soup.select_one('.bg-warning .h3')
    score = score_tag.text.strip() if score_tag else ''

    # Genre (if available)
    genre_tag = soup.select_one('.tagy')
    genre = genre_tag.text.strip() if genre_tag else ''

    return {
        'Original Name': original_name,
        'Year': year,
        'Description': description,
        'Score': score,
        'Genre': genre
    }


# Calculate durations across the full list
## Removed duplicate and misplaced blocks. All logic now runs after all_programs is defined.

today_str = datetime.today().strftime('%d.%m.%Y')
today_programs = [p for p in all_programs if p['Date'] == today_str]

# Defensive: If 'Start Time Obj' is missing, skip the entry
with open('tv_programs_disc.txt', 'w', encoding='utf-8') as file:
    for i, program in enumerate(today_programs):
        if 'Start Time Obj' not in program or program['Start Time Obj'] is None:
            continue
        start_time = program['Start Time Obj']
        if start_time and i + 1 < len(today_programs):
            next_start = today_programs[i + 1].get('Start Time Obj')
            duration = int((next_start - start_time).total_seconds() / 60) if next_start else 50
            if duration <= 0:
                duration = 50
            end_time = start_time + timedelta(minutes=duration)
        elif start_time:
            duration = 50
            end_time = start_time + timedelta(minutes=duration)
        else:
            duration = ''
            end_time = ''

        details = scrape_program_details(program['Link'])

        for key, value in {
            'Title': program.get('Title', ''),
            'Day': program.get('Day', ''),
            'Date': program.get('Date', ''),
            'Start Time': program.get('Start Time', ''),
            'End Time': end_time.strftime('%H:%M') if end_time else '',
            'Duration': f'{duration} min' if duration else '',
            'Channel': program.get('Channel', ''),
            'Link': program.get('Link', ''),
            'Original Name': details.get('Original Name', ''),
            'Year': details.get('Year', ''),
            'Description': details.get('Description', ''),
            'Score': details.get('Score', ''),
            'Genre': details.get('Genre', '')
        }.items():
            file.write(f"{key}: {value}\n")
        file.write("-" * 40 + "\n")


