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

# url for website to be scraped and path to save ingested data into
BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
ABS_PATH = "/home/aminh/workspace/web_scraper/data/raw/linkedin"

# set linkedin to have 25 jobs per page, as linkedin stores up to 1000 jobs
PAGE_SIZE = 25

# scraping timeline, if None then scrape all job listings
daily,weekly,monthly = "r86400","r604800","r2592000"

def get_jobs(response):
    """
    Scrapes the data containing the job listings from the response data

    Args:
        response: requested page data

    Returns:
        Number of job listings
    """

    # use beautiful soup to get text from page
    soup = BeautifulSoup(response.text, "html.parser")

    # get the HTML containers that have job content
    job_cards = soup.find_all("li")

    return job_cards




def scraper(job_cards, filename, total_collected, seen_ids):
    """
    Scrape job listings from jobstreet and save them to a jsonl file

    Args:
        job_cards: All job listings from jobstreet webpage
        filename: name and location of file to save the scraped data
        total_collected: number of jobs collected so far
        seen_ids: set containing jobs ids of jobs already saved

    Returns:
        Total number of jobs collected
    """
    
    # iterate over each HTML container of elements to get data from one job at a time
    for card in job_cards:

        # get job url to find job_id for job description url
        link_el = card.find("a", class_="base-card__full-link")
        if not link_el: continue
        job_url = link_el['href'].split("?")[0] # Clean URL
        
        # Extract clean numeric Job ID
        job_id_match = re.search(r'-(\d+)(?:\b|$)', job_url)
        job_id = job_id_match.group(1) if job_id_match else job_url.split("-")[-1]

        # locates any repeated jobs
        if job_id in seen_ids:
            total_collected -= 1
            continue
        
        # removes repeated jobs by adding to set() data type
        seen_ids.add(job_id)

        # Use job_id to get url for full description of job
        details_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

        # Call Detail Page for full Job Description
        detail_res = requests.get(details_url, headers=HEADERS)
        full_desc = ""
        desc_el = None

        # if no response from description page skip job listing
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
        with open(filename, "a", encoding="utf-8") as f:
            json_line = json.dumps(raw_record, ensure_ascii=False)
            f.write(json_line + "\n")

    return total_collected




def _run_scrape(job_type, date_range = None, location = 'Kuala Lumpur', max_jobs = 975):
    """
    Reqeuests data from linkedin webpage

    Args:
        job_type: the title of job 
        date_range: when job was listed, defaults to None, meaning all job listings available
        location: where the job is located, defaults to Kuala Lumpur
        max_jobs: linkedin stores up to 1000 jobs

    Returns:
        Total number of jobs collected
    """

    assert type(job_type) is str, "input for job_type must be a string"

    start_offset = 0
    page_counter = 1
    total_collected = 0
    seen_ids = set()

    # requests data as long as there are pages to scrape
    while max_jobs is None or start_offset <= max_jobs:

        # request specific page from linkedin website
        params = {
            "keywords": job_type,
            "location": location,
            "start": start_offset,
            "f_TPR": date_range
        }

        print(f"🔄 Requesting Page {page_counter} (Offset start={start_offset})...")

        # requests data from jobstreet
        response = requests.get(BASE_URL, params=params, headers=HEADERS)

        # if no response end loop
        if response.status_code != 200:
            print(f"🛑 Received a non-200 status code: {response.status_code}. Stopping task.")
            break

        # collects all job listings
        job_cards = get_jobs(response)

        # updates job listings collected
        total_collected += len(job_cards)

        # Save jobs with a timeline scraped on the same day into its own file
        if date_range is None:
            filename = f"{abs_path}/historic.jsonl"
        else:
            filename = f"{abs_path}/{datetime.now().strftime('%d-%m-%Y')}.jsonl"

        # get total number of jobs on current page and save data to jsonl file
        total_collected = scraper(job_cards, filename, total_collected, seen_ids)

        # stop if the site returns nothing more
        if len(job_cards) == 0:
            break

        print(f"Collected {total_collected} new jobs on Page {page_counter}")

        # increase offset by eaxctly 25, as job cards are not reliable
        start_offset += PAGE_SIZE
        page_counter += 1
        time.sleep(random.uniform(4.0, 8.0))  # Anti-bot mitigation

    return total_collected




def ld_scraper(job_type, date_range = None, location = 'Kuala Lumpur'):
    """
    Runs web scraper

    Args:
        job_type: the title of job 
        date_range: when job was listed, defaults to None, meaning all job listings available
        location: where the job is located, defaults to Kuala Lumpur

    Returns:
        nothing
    """
    assert date_range in ['daily', 'weekly', 'monthly', None], 'date_range parameter needs to be daily, weekly, monthly or None'

    # no date_range given means scrape all available data on linkedin webapge
    if date_range is None:

        # run the linkedin job scraper and get total number of jobs collected
        total_collected = _run_scrape(job_type, location, date_range, max_jobs=975)
        print(f"\n✅ Successfully saved all {job_type} job listings from linkedin. Captured {total_collected} jobs listings!")
    
    # scrape based on date_range timeline given
    elif date_range in [daily, weekly, monthly]:

        # phrase to use based on scraping cut off time
        timelines= {
            daily: "last 24 hours",
            weekly: "last week",
            monthly: "last month"
        }

        # run the linkedin job scraper and get total number of jobs collected
        total_collected = _run_scrape(job_type, location, date_range, max_jobs = None)

        # get the phrase to use based on the date_range given
        freq_type = timelines[date_range]
        
        print(f"✨ Full run complete. Successfully saved {total_collected} {job_type} job listings from linkedin, posted within the {freq_type}")
