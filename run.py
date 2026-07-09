import os
import logging
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Import modules
from ingestion.jobstreet.jobstreet_scraper import js_scraper, get_total_pages
from ingestion.linkedin.linkedin_scraper import ld_scraper

# Setup
ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

# Read variables injected by GitHub Actions environment blocks
job_title = os.environ.get("JOB_TYPE", "Data Analyst")
target_location = os.environ.get("LOCATION", "Kuala Lumpur")
date_range = os.environ.get("DATE_RANGE", "None")
run_type = os.environ.get("RUN_TYPE")

# Standardize "N/A" string back into Python's actual None type
if date_range == "None":
    date_range = None

# Logging
os.makedirs("logs", exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")

# 1. Initialize the master root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG) # Master threshold level

# Mute the specific sub-loggers
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

# 2. Create Handler #1: For writing to a file
timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
file_handler = logging.FileHandler(f"logs/app-{timestamp}.log")
file_handler.setLevel(logging.INFO) 
file_formatter = logging.Formatter('%(asctime)s:%(name)s - [%(levelname)s]: %(message)s')
file_handler.setFormatter(file_formatter)

# 3. Create Handler #2: For streaming to terminal screen
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG) 
console_formatter = logging.Formatter('[%(levelname)s]: %(message)s')
console_handler.setFormatter(console_formatter)

# 4. Tie both handlers to the root logger
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# initialize logger for current file (main.py)
main_logger = logging.getLogger(__name__)



if __name__ == "__main__":
    
    if run_type == 'daily':
        # 🌟 Define all the jobs you want to track automatically every night!
        DAILY_JOBS = [
            "Data Analyst"
        ]

        s_target_location = 'Kuala Lumpur'
        ld_date_range = "r86400"
        js_date_range = 1

        for job in DAILY_JOBS:

            main_logger.info(f"⏰ Starting Scheduled web scraper run for {job} job listings.")

            main_logger.info("🚀 Scraping jobs from Jobstreet")
            js_scraper(job_type = job, location = s_target_location, date_range = js_date_range)

            main_logger.info("🚀 Scraping jobs from Linkedin")
            ld_scraper(job_type = job, location = s_target_location, date_range = ld_date_range)

            main_logger.info("🏁 All scraping tasks completed successfully.")
    
    elif run_type == 'manual':

        if date_range == 'daily':
            ld_date_range = "r86400"
            js_date_range = 1

        main_logger.info(f"Starting web scraper run for {job_title} job listings.")
        main_logger.info("🚀 Scraping jobs from Jobstreet")
        js_scraper(job_type = job_title, location = target_location, date_range = js_date_range)

        main_logger.info("🚀 Scraping jobs from Linkedin")
        ld_scraper(job_type = job_title, location = target_location, date_range = ld_date_range)

        main_logger.info("🏁 All scraping tasks completed successfully.")

    else:
        main_logger.warning('🛑 Undetermined run type task is unable to start!')