import json
import random
import math
import re
import time
from datetime import datetime
from bs4 import BeautifulSoup
from curl_cffi import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

daily = 1
weekly = 7
biweekly = 14
monthly = 31

BASE_URL = f"https://my.jobstreet.com/data-analyst-jobs/in-Kuala-Lumpur"
ABS_PATH = "/home/aminh/workspace/web_scraper/data/raw/jobstreet"

def get_total_pages(job_type, location = "Kuala Lumpur",frequency = None):
    params = {
    "keyword" : job_type,
    "where" : location,
    "daterange": frequency,
    "page": 1
    }
    response = requests.get(BASE_URL, params=params, headers=HEADERS, impersonate="chrome")

    if response.status_code != 200:
        print(f"🛑 Received a non-200 status code: {response.status_code}. Stopping task.")

    # use beautiful soup to get text from page
    soup = BeautifulSoup(response.text, "html.parser")
    
    # get no of jobs available on that day
    no_of_jobs = soup.find(attrs={"data-automation": "totalJobsMessage"})
    total_jobs = no_of_jobs.text if no_of_jobs else None

    # conver to int type for calculation
    total_jobs = int(re.sub(r'[^\d]', '', total_jobs))
    # calculate number of pages (jobstreet has 30 jobs per page)
    pages = math.ceil(int(total_jobs) / 30)

    return pages

def get_jobs(response, abs_path, total_collected, page_counter, frequency, seen_ids):
    copies = 0
    # use beautiful soup to get text from page
    soup = BeautifulSoup(response.text, "html.parser")
    
    # locate all HTML containers that have content related to jobs
    job_cards = soup.find_all("article", attrs={"data-automation": "normalJob"})

    # iterate over each HTML container of elements to get data from one job at a time
    for card in job_cards:

        # Extract title and link elements safely
        title_el = card.find("a", attrs={"data-automation": "jobTitle"})
        if not title_el: continue
        
        # get job description url to view full description of job
        job_url = title_el['href']
        if job_url.startswith("/"):
            job_url = "https://my.jobstreet.com" + job_url
            
        # Parse the unique job ID from the URL (usually a sequence of numbers at the end)
        job_id_match = re.search(r'/job/(\d+)', job_url)
        job_id = job_id_match.group(1) if job_id_match else job_url.split("/")[-1]

        if job_id in seen_ids:
            copies += 1
            total_collected -= 1
            continue
        
        seen_ids.add(job_id)

        # Extract meta elements from card layout
        company_el = card.find("a", attrs={"data-automation": "jobCompany"})
        location_el = card.find("a", attrs={"data-automation": "jobLocation"})
        salary_el = card.find("span", attrs={"data-automation": "jobSalary"})
        
        # Call Detail Page for full Job Description
        detail_res = requests.get(job_url, headers=HEADERS, impersonate="chrome")
        full_desc = ""
        desc_el = None
        
        # if no response from description page continue
        if detail_res.status_code == 200:
            detail_soup = BeautifulSoup(detail_res.text, "html.parser")

            # Extract Raw Description Text
            desc_el = detail_soup.find(attrs={"data-automation": "jobAdDetails"})
            full_desc = desc_el.text.strip() if desc_el else ""
        else:
            print(f"❌ Skipped ID {job_id}: Detail page unreachable.")
            total_collected -= 1
            continue

        total_collected += 1

        # format data to json
        raw_record = {
            "job_id": str(job_id),
            "source": "JobStreet",
            "url": job_url,
            "collection_timestamp": datetime.utcnow().isoformat(),
            "job_title": title_el.text.strip() if title_el else "N/A",
            "company": company_el.text.strip() if company_el else "N/A",
            "location": location_el.text.strip() if location_el else "N/A",
            "employment_type": "N/A", # Will pull from description processing step
            "salary_min": salary_el.text.strip() if salary_el else "N/A",  
            "salary_max": salary_el.text.strip() if salary_el else "N/A",  
            "posting_date": "N/A",
            "job_description": full_desc,
            "requirements": "", 
            "skills": [s for s in ["SQL", "Python", "Tableau", "Power BI", "Excel", "Spark"] if s.lower() in full_desc.lower()],
            # Save the full literal HTML block of the description for historical backup
            "raw_html": str(desc_el) if desc_el else ""
        }

        if frequency == 1:
            filename = f"{abs_path}/{datetime.now().strftime('%d-%m-%Y')}.jsonl"
        else:
            filename = f"{abs_path}/historic.jsonl"

        # save to jsonl file
        with open(filename, "a", encoding="utf-8") as f:
            json_line = json.dumps(raw_record, ensure_ascii=False)
            f.write(json_line + "\n")

    print(f"Collected {total_collected} new jobs on Page {page_counter}")

    return total_collected

def _run_scrape(job_type, location = "Kuala Lumpur", frequency = None):

    page_counter = 1
    total_collected = 0
    seen_ids = set()
    max_pages = get_total_pages(job_type, location ,frequency)

    while page_counter <= max_pages:
        print(f"🔄 Requesting Page {page_counter}...")

        # request specific page from jobstreet website
        params = {
            "keyword" : job_type,
            "where" : location,
            "daterange": frequency,
            "page": page_counter
        }

        response = requests.get(BASE_URL, params=params, headers=HEADERS, impersonate="chrome")
        
        # if no response end loop
        if response.status_code != 200:
            print(f"🛑 Received a non-200 status code: {response.status_code}. Stopping pipeline.")
            break
            
        total_collected += get_jobs(response, ABS_PATH, total_collected, page_counter, frequency, seen_ids)
        page_counter += 1
        time.sleep(random.uniform(4.0, 8.0))

    return total_collected

def js_scraper(job_type, location):
    total_collected = _run_scrape(job_type, location)
    print(f"\n✅ Full run complete. Successfully saved {total_collected} jobstreet {job_type} listings!")

def js_daily_scraper(job_type, location):
    total_collected = _run_scrape(job_type, location, daily)
    print(f"\n✨ Daily run complete. Successfully saved {total_collected} jobstreet {job_type} listings!")

#js_daily_scraper('Data Analyst', 'Kuala Lunpur')