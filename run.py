import os
import logging
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Import modules
from ingestion.jobstreet.jobstreet_scraper import js_scraper, get_total_pages
from ingestion.linkedin.linkedin_scraper import ld_scraper

app_logger = logging.getLogger(__name__)

def job_scraper(job_title="Data Analyst", target_location="Kuala Lumpur", date_range="daily", run_type="scheduled"):

    if date_range == "None" or date_range is None:
        date_range = None
    
        if run_type == 'scheduled':
        # 🌟 Define all the jobs you want to track automatically every night!
        DAILY_JOBS = [
            "Data Analyst"
        ]

        s_target_location = 'Kuala Lumpur'
        ld_date_range = "r86400"
        js_date_range = 1

        for job in DAILY_JOBS:

            app_logger.info(f"⏰ Starting Scheduled web scraper run for {job} job listings.")

            app_logger.info("🚀 Scraping jobs from Jobstreet")
            js_scraper(job_type = job, location = s_target_location, date_range = js_date_range)

            app_logger.info("🚀 Scraping jobs from Linkedin")
            ld_scraper(job_type = job, location = s_target_location, date_range = ld_date_range)

            app_logger.info("🏁 All scraping tasks completed successfully.")
    
    elif run_type == 'manual':
        app_logger.info(date_range)
        if date_range == 'daily':
            ld_date_range = "r86400"
            js_date_range = 1

        app_logger.info(f"Starting web scraper run for {job_title} job listings.")
        app_logger.info("🚀 Scraping jobs from Jobstreet")
        js_scraper(job_type = job_title, location = target_location, date_range = js_date_range)

        app_logger.info("🚀 Scraping jobs from Linkedin")
        ld_scraper(job_type = job_title, location = target_location, date_range = ld_date_range)

        app_logger.info("🏁 All scraping tasks completed successfully.")

    else:
        app_logger.warning('🛑 Undetermined run type task is unable to start!')

if __name__ == "__main__":
    