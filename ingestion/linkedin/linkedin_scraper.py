import json
import random
import re
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
ABS_PATH = "/home/aminh/workspace/web_scraper/data/raw/linkedin"


def get_jobs(response):

    # use beautiful soup to get text from page
    soup = BeautifulSoup(response.text, "html.parser")

    # get the HTML containers that have job content
    job_cards = soup.find_all("li")

    return job_cards

def scraping(job_cards, abs_path, total_collected, s_type):

    # iterate over each HTML container of elements to get data from one job at a time
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
            total_collected -= 1
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

        # format data to json
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
        if s_type = 'total':
            filename = f"{abs_path}/historic.jsonl"
        elif s_type = 'daily':
            filename = f"{abs_path}/{datetime.now().strftime('%d-%m-%Y')}.jsonl"

        with open(filename, "a", encoding="utf-8") as f:
            json_line = json.dumps(raw_record, ensure_ascii=False)
            f.write(json_line + "\n")

    return total_collected


def _run_scrape(job_type, extra_params=None, max_offset=975, s_type):
    """
    Shared pagination engine for LinkedIn scraping.
    
    max_offset=None means run until the site stops returning results
    (used for the daily/unbounded scrape).
    """
    assert type(job_type) is str, "input for job_type must be a string"

    start_offset = 0
    page_counter = 1
    total_collected = 0

    while max_offset is None or start_offset <= max_offset:

        params = {
            "keywords": job_type,
            "location": "Kuala Lumpur",
            "start": start_offset,
        }
        if extra_params:
            params.update(extra_params)

        print(f"🔄 Requesting Page {page_counter} (Offset start={start_offset})...")

        response = requests.get(BASE_URL, params=params, headers=HEADERS)

        if response.status_code != 200:
            print(f"🛑 Received a non-200 status code: {response.status_code}. Stopping task.")
            break

        job_cards = get_jobs(response)
        print(f"Collected {len(job_cards)} new jobs on Page {page_counter}")

        total_collected += len(job_cards)
        total_collected = scraping(job_cards, ABS_PATH, total_collected, s_type)

        # stop if the site returns nothing more (important for the unbounded case,
        # otherwise ld_daily_scraper loops forever once jobs run out)
        if len(job_cards) == 0:
            break

        start_offset += len(job_cards)
        page_counter += 1
        time.sleep(random.uniform(4.0, 8.0))  # Anti-bot mitigation

    return total_collected


def ld_scraper(job_type):
    total_collected = _run_scrape(job_type, max_offset=975,'total')
    print(f"\n✅ Full run complete. Successfully captured {total_collected} linkedin {job_type} listings!")


def ld_daily_scraper(job_type):
    total_collected = _run_scrape(
        job_type,
        extra_params={"f_TPR": "r86400"},  # 🌟 24-hour lookback
        max_offset=None,
        'daily'
    )
    print(f"\n✨ Daily run complete. Successfully captured {total_collected} linkedin {job_type} listings!")

