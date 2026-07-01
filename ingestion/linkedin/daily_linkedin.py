import json
import random
import re
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

abs_path = "/home/aminh/workspace/web_scraper/data/raw/linkedin"
base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

start_offset = 0
page_counter = 1
daily_total = 0

print("🌅 Starting Daily LinkedIn Ingestion Loop [Target: Last 24 Hours in KL]...")

while True:
    # Set parameters optimized specifically for a 24-hour lookback
    params = {
        "keywords": "Data Analyst",
        "location": "Kuala Lumpur",
        "start": start_offset,
        "f_TPR": "r86400"  # 🌟 THE DAILY FILTER: r86400 seconds = 24 hours
    }
    
    response = requests.get(base_url, params=params, headers=HEADERS)
    
    if response.status_code != 200:
        print(f"🛑 Network anomaly (Status {response.status_code}). Aborting daily run.")
        break
        
    soup = BeautifulSoup(response.text, "html.parser")
    job_cards = soup.find_all("li")
    
    # Natural Exit: Since it's only a 24h window, you'll hit 0 cards very quickly!
    if len(job_cards) == 0:
        print(f"🏁 Clean stop. No more new listings found for today.")
        break
        
    print(f"   Collected {len(job_cards)} new jobs on Page {page_counter}")
    daily_total += len(job_cards)
    
    for card in job_cards:
        
        # get job url to find job_id for job description url
        link_el = card.find("a", class_="base-card__full-link")
        if not link_el: continue
        job_url = link_el['href'].split("?")[0] # Clean URL
        
        # Extract clean numeric Job ID
        job_id_match = re.search(r'-(\d+)(?:\b|$)', job_url)
        job_id = job_id_match.group(1) if job_id_match else job_url.split("-")[-1]

        # Use job_id to get url for full description of job
        details_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

        # Call Detail Page for full Job Description
        detail_res = requests.get(details_url, headers=HEADERS)
        full_desc = ""
        desc_el = None

        # if no response from description page continue
        if detail_res.status_code == 200:
            detail_soup = BeautifulSoup(detail_res.text, "html.parser")

            # Extract Raw Description Text
            desc_el = detail_soup.find("div", class_="description__text")
            full_desc = desc_el.text.strip() if desc_el else ""

        else:
            print(f"❌ Skipped ID {job_id}: Detail page unreachable.")
            continue

        # Extract meta elements from card layout 
        title_el = card.find("h3", class_="base-search-card__title")
        company_el = card.find("h4", class_="base-search-card__subtitle")
        loc_el = card.find("span", class_="job-search-card__location")
        date_el = card.find("time", class_="job-search-card__listdate") or card.find("time", class_="job-search-card__listdate--new")
        
        # Extracting specific criteria tags (Employment Type)
        emp_type = "N/A"
        criteria_list = detail_soup.find_all("li", class_="description__job-criteria-item")

        for item in criteria_list:
            if "Employment type" in item.text:
                emp_type = item.text.replace("Employment type", "").strip()

        # format data to json-
        raw_record = {
            "job_id": job_id,
            "source": "LinkedIn",
            "url": job_url,
            "collection_timestamp": datetime.utcnow().isoformat(),
            "job_title": title_el.text.strip() if title_el else "N/A",
            "company": company_el.text.strip() if company_el else "N/A",
            "location": loc_el.text.strip() if loc_el else "N/A",
            "employment_type": emp_type,
            "salary_min": None,  # LinkedIn Guest UI rarely lists MYR salaries openly
            "salary_max": None,  # Will parse these fields in the JobStreet pipeline
            "posting_date": date_el["datetime"] if date_el and date_el.has_attr("datetime") else (date_el.text.strip() if date_el else "N/A"),
            "job_description": full_desc,
            "requirements": "", 
            "skills": [s for s in ["SQL", "Python", "Tableau", "Power BI", "Excel", "Spark"] if s.lower() in full_desc.lower()],
            # Save the full literal HTML block of the description for historical backup
            "raw_html": str(desc_el) if desc_el else ""
        }

        # save to jsonl file
        filename = f"{abs_path}/{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        with open(filename, "a", encoding="utf-8") as f:
            json_line = json.dumps(raw_record, ensure_ascii=False)
            f.write(json_line + "\n")
        

    start_offset += len(job_cards)
    page_counter += 1
    time.sleep(random.uniform(3.5, 6.0)) # Anti-bot mitigation

print(f"\n✨ Daily run complete. Successfully captured {daily_total} fresh listings!")