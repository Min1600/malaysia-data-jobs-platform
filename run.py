import os
import logging
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import HfApi

# Import modules
from ingestion.jobstreet.jobstreet_scraper import js_scraper, get_total_pages
from ingestion.linkedin.linkedin_scraper import ld_scraper

#load_dotenv()
app_logger = logging.getLogger(__name__)

def upload_artifacts_to_hf():
    """Beams local JSONL data and active log files to permanent HF Dataset storage"""

    token = os.environ.get("HF_TOKEN")

    if not token:
        app_logger.warning("⚠️ HF_TOKEN not found in environment variables. Skipping cloud sync.")
        return

    api = HfApi(token=token)
    repo_target = "Amin1600/Web_Scraper_Data" 
    
    app_logger.info("📦 Commencing synchronization with Hugging Face Dataset vault...")
    
    try:
        # 1. Upload your data folder contents (.jsonl files)
        if os.path.exists("data") and os.listdir("data"):
            api.upload_folder(
                folder_path="data",
                path_in_repo="job_data", # Folder name inside your dataset repo
                repo_id=repo_target,
                repo_type="dataset"
            )
            app_logger.info("🎉 Scraping data (.jsonl) successfully backed up to HF Datasets!")

        # 2. Upload your logs folder contents (.log files)
        if os.path.exists("logs") and os.listdir("logs"):
            api.upload_folder(
                folder_path="logs",
                path_in_repo="logs", # Folder name inside your dataset repo
                repo_id=repo_target,
                repo_type="dataset"
            )
            app_logger.info("🎉 System execution logs successfully backed up to HF Datasets!")

    except Exception as e:
        app_logger.error(f"❌ Failed to sync files to Hugging Face Dataset: {e}")


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
            upload_artifacts_to_hf()
    
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
        upload_artifacts_to_hf()

    else:
        app_logger.warning('🛑 Undetermined run type task is unable to start!')

if __name__ == "__main__":
    pass