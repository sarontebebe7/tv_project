import requests
import time
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

with open("/workspaces/tv_project/cron_log.txt", "a") as log:
    from datetime import datetime
    log.write(f"{datetime.now()}: Started {__file__}\n")

base_date = datetime.today()

day_map = {
    'Pondelok': 0,
    'Utorok': 1,
    'Streda': 2,
    'Štvrtok': 3,
    'Piatok': 4,
    'Sobota': 5,
    'Nedeľa': 6
}

date_lookup = {}
for name, weekday_index in day_map.items():
    delta = weekday_index - base_date.weekday()
    if delta < 0:
        delta += 7
    date_lookup[name] = (base_date + timedelta(days=delta)).strftime('%d.%m.%Y')

url = 'https://tv-program.sk/national-geographic/cely-den/'
response = requests.get(url)
soup = BeautifulSoup(response.content.decode('utf-8', errors='replace'), 'html.parser')

channel_tag = soup.select_one('.page__title-name')
channel_name = channel_tag.text.strip() if channel_tag else 'Unknown'

all_programs = []
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
        return {
            'Original Name': '',
            'Year': '',
            'Description': '',
            'Score': '',
            'Genre': ''
        }

    original_name_tag = soup.find('strong', string=lambda s: s and 'Pôvodný názov' in s)
    original_name = original_name_tag.find_next('span').text.strip() if original_name_tag and original_name_tag.find_next('span') else ''

    year_tag = soup.find('strong', string=lambda s: s and 'Rok výroby' in s)
    year = year_tag.find_next('span').text.strip() if year_tag and year_tag.find_next('span') else ''

    description_tag = soup.select_one('.post__body p')
    description = description_tag.text.strip() if description_tag else ''

    score_tag = soup.select_one('.bg-warning .h3')
    score = score_tag.text.strip() if score_tag else ''

    genre_tag = soup.select_one('.tagy')
    genre = genre_tag.text.strip() if genre_tag else ''

    return {
        'Original Name': original_name,
        'Year': year,
        'Description': description,
        'Score': score,
        'Genre': genre
    }

# Only keep programs for today's date


today_str = datetime.today().strftime('%d.%m.%Y')
today_programs = [p for p in all_programs if p['Date'] == today_str]

with open('tv_programs_national.txt', 'w', encoding='utf-8') as file:
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


