import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime

# 1. Read existing database and configuration
data_file = 'data.json'
try:
    with open(data_file, 'r') as f:
        data = json.load(f)
except FileNotFoundError:
    data = {
        "config": {"keywords": ["Product Manager"], "locations": ["Germany"]},
        "jobs": [],
        "pipeline": [],
        "last_synced": ""
    }

# Dynamically pull the search terms configured via your UI
SEARCH_TERMS = data.get("config", {}).get("keywords", ["Product Manager"])
LOCATIONS = data.get("config", {}).get("locations", ["Germany"])

def scrape_linkedin_jobs(keyword, location):
    url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    params = {
        "keywords": keyword,
        "location": location,
        "start": 0
    }
    
    jobs = []
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        job_cards = soup.find_all('li')
        
        for card in job_cards:
            try:
                title_elem = card.find('h3', class_='base-search-card__title')
                company_elem = card.find('h4', class_='base-search-card__subtitle')
                location_elem = card.find('span', class_='job-search-card__location')
                link_elem = card.find('a', class_='base-card__full-link')
                
                if title_elem and company_elem:
                    job_id = link_elem['href'].split('?')[0].split('-')[-1] if link_elem else str(time.time())
                    
                    jobs.append({
                        "id": job_id,
                        "title": title_elem.text.strip(),
                        "company": company_elem.text.strip(),
                        "location": location_elem.text.strip() if location_elem else "",
                        "url": link_elem['href'].strip() if link_elem else "",
                        "match": "Pending", 
                        "status": "New"
                    })
            except Exception:
                continue
    return jobs

# 2. Execute scraping
existing_ids = {job['id'] for job in data.get('jobs', [])}
new_jobs_found = 0

for term in SEARCH_TERMS:
    for loc in LOCATIONS:
        print(f"Scraping '{term}' in {loc}...")
        scraped_jobs = scrape_linkedin_jobs(term, loc)
        
        for job in scraped_jobs:
            if job['id'] not in existing_ids:
                data['jobs'].insert(0, job)
                existing_ids.add(job['id'])
                new_jobs_found += 1
        time.sleep(2)

# 3. Save updates
data['last_synced'] = datetime.utcnow().isoformat() + "Z"
with open(data_file, 'w') as f:
    json.dump(data, f, indent=2)

print(f"Successfully added {new_jobs_found} new jobs.")
