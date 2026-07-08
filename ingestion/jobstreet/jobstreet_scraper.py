import json
import random
import math
import re
import time
import logging
import os
from datetime import datetime
from bs4 import BeautifulSoup
from curl_cffi import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

# url for website to be scraped and path to save ingested data into
BASE_URL = f"https://my.jobstreet.com/data-analyst-jobs/in-Kuala-Lumpur"

# create relative path for linkedin scraped data
ABS_PATH = os.path.join("data", "raw", "jobstreet")

# create directories if they don't exist
os.makedirs(ABS_PATH, exist_ok=True)

# scraping timeline, if None then scrape all job listings
daily, weekly, monthly = 1,7,31

js_logger = logging.getLogger(__name__)

def get_total_pages(job_type, date_range = None, location = "Kuala Lumpur"):
    """
    calculates total number of pages of job listings for the specific job type, location and dates provided

    Args:
        job_type: the title of job 
        date_range: when job was listed, defaults to None, meaning all job listings available
        location: where the job is located, defaults to Kuala Lumpur

    Returns:
        Number of pages on jobstreet webpage containing job listings
    """
    js_logger.debug(f"Collecting number of pages of {job_type} job listings in {location} from jobstreet.")

    params = {
    "keyword" : job_type,
    "where" : location,
    "daterange": date_range,
    "page": 1
    }

    # test connection 
    try:

        # requests data from jobstreet
        response = requests.get(BASE_URL, params=params, headers=HEADERS, impersonate="chrome", timeout = 10)
        response.raise_for_status() # Automatically triggers HTTPError if status is 4xx or 5xx
    
    # Catches bad status codes (4xx or 5xx)
    except requests.exceptions.HTTPError as e:
        js_logger.error(f"🛑 HTTP Error occurred: {e.response.status_code} - {e.response.reason}. Unable to determine number of pages aborting task!")
        return None
    
    # Catches connection drops, timeouts, DNS issues where NO response was given
    except requests.exceptions.RequestException as e:
        js_logger.error(f"💥 Network level error occurred (No response received): {e}. Unable to determine number of pages aborting task!")
        return None

    # use beautiful soup to get text from page
    soup = BeautifulSoup(response.text, "html.parser")
    
    # get no of jobs available
    no_of_jobs = soup.find(attrs={"data-automation": "totalJobsMessage"})

    if no_of_jobs:
        total_jobs = no_of_jobs.text
    else:
        return None

    # convert to int type for calculation
    total_jobs = int(re.sub(r'[^\d]', '', total_jobs))

    # calculate number of pages (jobstreet has 30 jobs per page)
    pages = math.ceil(int(total_jobs) / 30)

    js_logger.debug(f"Found {pages} pages")

    return pages




def get_jobs(response, filename, seen_ids):
    """
    Scrape job listings from jobstreet and save them to a jsonl file

    Args:
        response: requested data from jobstreet webpage
        filename: name and location of file to save the scraped data
        seen_ids: set containing jobs ids of jobs already saved

    Returns:
        Total number of jobs collected
    """

    # use beautiful soup to get text from page
    soup = BeautifulSoup(response.text, "html.parser")
    
    # locate all job listings on website page
    job_cards = soup.find_all("article", attrs={"data-automation": "normalJob"})
    num_jobs = len(job_cards)

    # iterate over all job listings found to get data from each one
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

        # locates any repeated jobs
        if job_id in seen_ids:
            num_jobs -= 1
            continue
        
        # removes repeated jobs by adding to set() data type
        seen_ids.add(job_id)

        # Extract meta elements from card layout
        company_el = card.find("a", attrs={"data-automation": "jobCompany"})
        location_el = card.find("a", attrs={"data-automation": "jobLocation"})
        salary_el = card.find("span", attrs={"data-automation": "jobSalary"})
        
        # Call Detail Page for full Job Description
        detail_res = requests.get(job_url, headers=HEADERS, impersonate="chrome")
        full_desc = ""
        desc_el = None
        
        if detail_res.status_code == 200:

            # get job description/details
            detail_soup = BeautifulSoup(detail_res.text, "html.parser")

            # Extract Raw Description Text
            desc_el = detail_soup.find(attrs={"data-automation": "jobAdDetails"})
            full_desc = desc_el.text.strip() if desc_el else ""

        # if no response from description page skip job (dont write to file)
        else:
            print(f"❌ Skipped ID {job_id}: Detail page unreachable.")
            num_jobs -= 1
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

        try:
            # save to jsonl file
            with open(filename, "a", encoding="utf-8") as f:
                json_line = json.dumps(raw_record, ensure_ascii=False)
                f.write(json_line + "\n")

        except IOError as e:
            # Catches disk full, permission denied, or missing directory errors
            js_logger.error(f"💾 File write failed! Could not append job to {filename}. Error: {e}")
            return num_jobs
        
        except TypeError as e:
            # Catches situations where raw_record contains an object json cannot serialize (e.g., datetime objects)
            js_logger.error(f"JSON serialization failed for job data. Serialization Error: {e}")
            return num_jobs

    return num_jobs




def _run_scrape(job_type, date_range = None, location = "Kuala Lumpur"):
    """
    Reqeuests data from jobstreet webpage

    Args:
        job_type: the title of job 
        date_range: when job was listed, defaults to None, meaning all job listings available
        location: where the job is located, defaults to Kuala Lumpur

    Returns:
        Total number of jobs collected
    """
    
    page_counter = 1
    total_collected = 0
    seen_ids = set()
    max_pages = get_total_pages(job_type, date_range, location)

    if not max_pages:
        return total_collected

    # requests data as long as there are pages to scrape
    while page_counter <= max_pages:

        js_logger.info(f"🔄 Requesting Page {page_counter}...")

        # request specific page from jobstreet website
        params = {
            "keyword" : job_type,
            "where" : location,
            "daterange": date_range,
            "page": page_counter
        }

        # test connection 
        try:
            response = requests.get(BASE_URL, params=params, headers=HEADERS, impersonate="chrome", timeout = 10)
            response.raise_for_status() # Automatically triggers HTTPError if status is 4xx or 5xx
        
        # Catches bad status codes (4xx or 5xx)
        except requests.exceptions.HTTPError as e:
            js_logger.error(f"🛑 HTTP Error occurred: {e.response.status_code} - {e.response.reason}. Stopping task.")
            break
        
        # Catches connection drops, timeouts, DNS issues where NO response was given
        except requests.exceptions.RequestException as e:
            js_logger.error(f"💥 Network level error occurred (No response received): {e}. Stopping task.")
            break

        # Save jobs with a timeline scraped on the same day into its own file
        if date_range is None:
            filename = os.path.join(ABS_PATH, "historic.jsonl")
        else:
            current_time = datetime.now().strftime('%d-%m-%Y')
            filename = os.path.join(ABS_PATH, f"{current_time}.jsonl")
        
        # get total number of jobs on current page
        num_jobs = get_jobs(response, filename, seen_ids)

        # add to final total
        total_collected += num_jobs

        js_logger.info(f"Collected {num_jobs} new jobs on Page {page_counter}")

        page_counter += 1
        time.sleep(random.uniform(4.0, 8.0)) # Anti-bot protection

    return total_collected




def js_scraper(job_type, date_range = None, location = "Kuala Lumpur"):
    """
    Runs web scraper

    Args:
        job_type: the title of job 
        date_range: when job was listed, defaults to None, meaning all job listings available
        location: where the job is located, defaults to Kuala Lumpur

    Returns:
        nothing
    """

    assert date_range in [daily, weekly, monthly, None], 'date_range parameter needs to be daily, weekly, monthly or None'

    # no date_range given means scrape all available data on jobstreet webapge
    if date_range is None:

        js_logger.info(f"Collecting all job street {job_type} job listings in {location}.")

        # run the jobstreet job scraper and get total number of jobs collected
        total_collected = _run_scrape(job_type, date_range, location)
        js_logger.info(f"\n✅ Full run complete. Successfully saved {total_collected} {job_type} jobs in {location} from jobstreet!")

    # scrape based on date_range timeline given
    elif date_range in [daily, weekly, monthly]:

        # phrase to use based on scraping cut off time
        timelines= {
            daily: "last 24 hours",
            weekly: "last week",
            monthly: "last month"
        }


        # get the phrase to use based on the date_range given
        freq_type = timelines[date_range]

        js_logger.info(f"Collecting all jobstreet {job_type} job listings from the {freq_type} in {location}")

        # run the jobstreet job scraper and get total number of jobs collected
        total_collected = _run_scrape(job_type, date_range, location)
        js_logger.info(f"✨ Full run complete. Successfully saved {total_collected} {job_type} job listings in {location} from jobstreet, posted within the {freq_type}")
    else:
        js_logger.warning('Error, input needs to be 1,7,31 or None')
    