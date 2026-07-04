import json
import random
import time
from datetime import datetime, timedelta
import dateutil.parser
import dateutil.tz
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

local_timezone = dateutil.tz.tzlocal()
daily = datetime.now(local_timezone) - timedelta(days=1)
weekly = datetime.now(local_timezone) - timedelta(days=7)
monthly = datetime.now(local_timezone) - timedelta(days=31)

def cut_off(frequency, active):

    assert frequency in ['daily', 'weekly', 'monthly'], 'frequency parameter needs to be daily, weekly, monthly or all time'

    if frequency == 'daily':

        return daily

    elif frequency == 'weekly':

        return weekly

    elif frequency == 'monthly':

        return monthly

def run_scrape(job_type, location, frequency):

    page_counter = 1
    total_jobs = 0
    total_skipped_jobs = 0
    format_job = job_type.replace(" ", "-")
    base_url = f"https://my.hiredly.com/{format_job}-jobs"
    filename = f"/home/aminh/workspace/web_scraper/ingestion/hiredly/{datetime.now().strftime('%Y-%m-%d')}_hiredly.jsonl"
    
    print("🚀 Extracting from Hiredly's Next.js Data Layer...")

    while True:

        skipped_jobs = 0
        print(f"Extracting page {page_counter}")

        params = {
            "location": location,
            "filterOrigin": "jdp-text",
            "page": page_counter
        }

        response = requests.get(base_url, headers=HEADERS, params=params, timeout=10)

        if response.status_code == 200:
        
            soup = BeautifulSoup(response.text, "html.parser")
            
            # 1. Isolate the hidden payload script tag you discovered
            script_tag = soup.find("script", id="__NEXT_DATA__")
            
            if script_tag and script_tag.string:
                # 2. Parse the raw string text directly into a clean Python dictionary
                next_data = json.loads(script_tag.string)

                # 3. Drill down into the Next.js page state tree
                # Note: Next.js structures lookups inside props -> pageProps -> queries or apis.
                # Check your print(next_data) output to confirm the exact key names for their job array!
                page_props = next_data.get("props", {}).get("pageProps", {})

                # Isolate the job array list we saw in your key map
                job_cards = page_props.get("jobs", [])
            
                # If the page returns 0 jobs, we have reached past the final page of results!
                if not job_cards or len(job_cards) == 0:
                    print(f"🏁 Page {page_counter} returned 0 job entries. No more jobs available!")
                    break

                if job_cards:

                    for job in job_cards:

                        if frequency != 'all time':

                            active_at_str = job.get("activeAt")
    
                            if active_at_str:
                                # 2. Parse the job's posting timestamp into a comparable python datetime
                                job_date = dateutil.parser.isoparse(active_at_str)
                                
                                # 3. 🌟 THE DAILY FILTER CHECK 🌟
                                if job_date < cut_off(frequency, active_at_str):
                                    skipped_jobs += 1 
                                    total_skipped_jobs += 1
                                    continue

                        raw_record = {
                            "job_id": job.get("id") or job.get("jobId"),
                            "source": "Hiredly",
                            "url": f"https://my.hiredly.com/jobs/{job.get('slug')}",
                            "collection_timestamp": datetime.utcnow().isoformat(),
                            "job_title": job.get("title") or job.get("jobTitle"),
                            "company": job.get("company", {}).get("name"),
                            "location": job.get("stateRegion", {}) or "Kuala Lumpur",
                            "job_url": job.get("externalJobUrl", {}) or 'N/A',
                            "employment_type": job.get("employmentType") or "Full-Time",
                            "salary_min": job.get("salaryMin") or job.get("minSalary"),
                            "salary_max": job.get("salaryMax") or job.get("maxSalary"),
                            "posting_date": job.get("createdAt") or "Today",
                            "job_description": job.get("description") or "",
                            "requirements": str(job.get("requirements", "")),
                            "skills": [s.get("name") for s in job.get("skills", []) if isinstance(s, dict)], 
                            "raw_json": json.dumps(job) # Perfect raw backup for your Bronze Layer!
                        }
                        
                        with open(filename, "a", encoding="utf-8") as f:
                            f.write(json.dumps(raw_record, ensure_ascii=False) + "\n")

            else:
                print("❌ Could not locate the __NEXT_DATA__ script payload block.")
        else:
            print(f"🛑 Server block or bad path. Status: {response.status_code}")

        jobs_meeting_requirements = len(job_cards) - skipped_jobs
        total_jobs += jobs_meeting_requirements
        print(f"Collected {jobs_meeting_requirements} jobs on Page {page_counter}. ")
        page_counter += 1
        time.sleep(random.uniform(4.0, 8.0))

    if frequency == 'all time':
        print(f"\n✅ Full run complete. Successfully saved {total_jobs} Hiredly {job_type} listings!")
    
    else:
        print(f"{total_skipped_jobs} jobs were not included because it was less than {frequency}")
        print(f"\n✨ Daily run complete. Successfully saved {total_jobs} Hiredly {job_type} listings!")
        
# run_scrape('Data Analyst', 'Kuala Lumpur', 'weekly')