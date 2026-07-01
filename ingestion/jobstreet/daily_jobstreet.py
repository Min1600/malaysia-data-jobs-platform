import json
import random
import re
import time
from datetime import datetime
from bs4 import BeautifulSoup
from curl_cffi import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

# Change how many days ago to scrape from
today = "?daterange=1"
three_days = "?daterange=1"
seven_days = "?daterange=7"
fourteen_days = "?daterange=14"
one_month = "?daterange=31"

abs_path = "/home/aminh/workspace/web_scraper/data/raw/jobstreet"
base_url = f"https://my.jobstreet.com/data-analyst-jobs/in-Kuala-Lumpur{today}"
page_counter = 1
total_collected = 0
max_pages = 5 # on jobstreet it says how many there are total

while page_counter <= max_pages:
    print(f"🔄 Requesting Page {page_counter}...")

    # request specific page from jobstreet website
    params = {"page": page_counter}
    response = requests.get(base_url, params=params, headers=HEADERS, impersonate="chrome")
    
    # if no response end loop
    if response.status_code != 200:
        print(f"🛑 Received a non-200 status code: {response.status_code}. Stopping pipeline.")
        break

    # use beautiful soup to get text from page
    soup = BeautifulSoup(response.text, "html.parser")
    
    # locate all HTML containers that have content related to jobs
    job_cards = soup.find_all("article", attrs={"data-automation": "normalJob"})
    
    # error handling if no job cards found or wrong attribute name
    if not job_cards:
        print("🛑 Could not find job listings on the page. Format might have changed or end of pagination.")
        break
       
    print(f"   📊 Found {len(job_cards)} job listings on this page.")
    total_collected += len(job_cards)

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
            desc_el = detail_soup.find(attrs={"data-automation": "jobAdDetails"})
            full_desc = desc_el.text.strip() if desc_el else ""
        else:
            print(f"❌ Skipped ID {job_id}: Detail page unreachable.")
            continue

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

        # save to jsonl file
        filename = f"{abs_path}/historic.jsonl"
        with open(filename, "a", encoding="utf-8") as f:
            json_line = json.dumps(raw_record, ensure_ascii=False)
            f.write(json_line + "\n")

        print(f"✅ Fully ingested: {raw_record['job_title']} at {raw_record['company']} -> Saved to {filename}")
        
        time.sleep(random.uniform(3.0, 6.0))

    page_counter += 1
    time.sleep(random.uniform(4.0, 8.0))

print("Job Complete!")