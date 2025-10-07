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
url = 'https://www.tv-program.sk/bbc-earth/cely-den/'
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
    original_name = ''
    original_name_tag = soup.find('strong', string=lambda s: s and 'Pôvodný názov' in s)
    if original_name_tag:
        span = original_name_tag.find_next('span')
        if span:
            original_name = span.text.strip()

    # Extract year
    year = ''
    year_tag = soup.find('strong', string=lambda s: s and 'Rok výroby' in s)
    if year_tag:
        span = year_tag.find_next('span')
        if span:
            year = span.text.strip()

    # Extract description (try .post__body p, fallback to .fs-7)
    description = ''
    description_tag = soup.select_one('.post__body p')
    if not description_tag:
        description_tag = soup.select_one('.fs-7')
    if description_tag:
        description = description_tag.text.strip()

    # Extract score (try .bg-warning .h3, fallback to yellow box)
    score = ''
    score_tag = soup.select_one('.bg-warning .h3')
    if not score_tag:
        # Try to find yellow box with percentage
        score_box = soup.find('div', style=lambda s: s and 'background-color' in s)
        if score_box:
            score = score_box.text.strip()
    else:
        score = score_tag.text.strip()

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
final_programs = []
for i, program in enumerate(all_programs): #### FOR ALL FILMS
################# SCRAP ADDITIONAL INFO FOR FIRST FIVE FILMS ONLY ############  for i, program in enumerate(all_programs[:5]):

    start_time = program['Start Time Obj']
    if start_time and i + 1 < len(all_programs):
        next_start = all_programs[i + 1]['Start Time Obj']
        duration = int((next_start - start_time).total_seconds() / 60)
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

    final_programs.append({
        'Title': program['Title'],
        'Day': program['Day'],
        'Date': program['Date'],
        'Start Time': program['Start Time'],
        'End Time': end_time.strftime('%H:%M') if end_time else '',
        'Duration': f'{duration} min' if duration else '',
        'Channel': program['Channel'],
        'Link': program['Link'],
        'Original Name': details['Original Name'],
        'Year': details['Year'],
        'Description': details['Description'],
        'Score': details['Score'],
        'Genre': details['Genre']
    })



# Only keep programs for today's date
today_str = datetime.today().strftime('%d.%m.%Y')
today_programs = [p for p in all_programs if p['Date'] == today_str]

with open('tv_programs_bbc.txt', 'w', encoding='utf-8') as file:
    for i, program in enumerate(today_programs):
        start_time = program['Start Time Obj']
        if start_time and i + 1 < len(today_programs):
            next_start = today_programs[i + 1]['Start Time Obj']
            duration = int((next_start - start_time).total_seconds() / 60)
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

        # Write directly to file
        for key, value in {
            'Title': program['Title'],
            'Day': program['Day'],
            'Date': program['Date'],
            'Start Time': program['Start Time'],
            'End Time': end_time.strftime('%H:%M') if end_time else '',
            'Duration': f'{duration} min' if duration else '',
            'Channel': program['Channel'],
            'Link': program['Link'],
            'Original Name': details['Original Name'],
            'Year': details['Year'],
            'Description': details['Description'],
            'Score': details['Score'],
            'Genre': details['Genre']
        }.items():
            file.write(f"{key}: {value}\n")
        file.write("-" * 40 + "\n")


