import streamlit as st
import logging
import sys
import os
import threading
import pandas as pd
from datetime import datetime
from huggingface_hub import hf_hub_download
from run import job_scraper
from apscheduler.schedulers.background import BackgroundScheduler


HF_TOKEN = os.environ.get("HF_TOKEN")
# ==========================================
# 1. CORE INFRASTRUCTURE: LOGGING (Runs ONCE)
# ==========================================
if "logger_initialized" not in st.session_state:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Clean out any accidental duplicate handlers on boot
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Mute sub-loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    # File Handler
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.now().strftime("%d-%m-%Y(%H:%M:%S)")
    file_handler = logging.FileHandler(f"logs/job-scraper-{timestamp}.log")
    file_handler.setLevel(logging.INFO) 
    file_formatter = logging.Formatter('%(asctime)s:%(name)s - [%(levelname)s]: %(message)s')
    file_handler.setFormatter(file_formatter)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG) 
    console_formatter = logging.Formatter('[%(levelname)s]: %(message)s')
    console_handler.setFormatter(console_formatter)

    # Attach both
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    st.session_state["logger_initialized"] = True

main_logger = logging.getLogger(__name__)
main_logger.info("Application UI successfully booted up!")


# ==========================================
# 2. AUTOMATED CRON SCHEDULER (Runs ONCE)
# ==========================================
def daily_scraper():
    # 🌟 Make sure this matches your function name from run.py (job_scraper)
    job_scraper(
        job_title="Data Analyst",
        target_location="Kuala Lumpur",
        date_range="daily",
        run_type="scheduled"
    )

if "scheduler_initialized" not in st.session_state:
    scheduler = BackgroundScheduler()
    # Runs every single night at 16:00 UTC (Midnight Malaysia Time)
    scheduler.add_job(daily_scraper, 'cron', hour=16, minute=0)
    scheduler.start()
    
    st.session_state["scheduler_initialized"] = True
    main_logger.info("Scheduler successfully armed for midnight runs.")


# ==========================================
# 3. STREAMLIT USER INTERFACE & BUTTONS
# ==========================================


def fetch_data(website):
    current_time = datetime.now().strftime('%d-%m-%Y')
    try:
        # 1. Pull the specific data vault file down from your private dataset
        local_file_path = hf_hub_download(
            repo_id="Amin1600/Web_Scraper_Data",
            filename=f"job_data/raw/{website}/09-07-2026.jsonl",
            repo_type="dataset",
            token=HF_TOKEN
        )
        
        # 2. Read it directly into a Pandas DataFrame
        df = pd.read_json(local_file_path, lines=True)
        print(f"📊 Successfully loaded {len(df)} jobs rows from {website} uploaded on {current_time}.")

        selected_columns = ["job_title", "company", "salary_min", "posting_date", "skills"]
        return df[selected_columns]

    except Exception as e:
        print(f"❌ Error downloading database: {e}")
        return None

st.write("Today's scraped data")
st.header("Linkedin Data")
st.write(fetch_data('linkedin'))
st.header("Jobstreet Data")
st.write(fetch_data('jobstreet'))

st.sidebar.header("⚙️ Live Scraper Controller")
st.sidebar.write("Serch for job postings of your choice!")

# UI Input fields
job_input = st.sidebar.text_input("Job Title Keyword", "Data Analyst")
loc_input = st.sidebar.text_input("Target Location", "Kuala Lumpur")
date_input = st.sidebar.selectbox(
    "Date Range Filter", 
    options=["all", "daily", "weekly", "monthly"]
)

backend_date_range = None if date_input == 'all' else date_input

# The Activation Button
if st.sidebar.button("🚀 Run Scraper"):
    # Create a separate background thread so the UI doesn't freeze!
    scraper_thread = threading.Thread(
        target=job_scraper,
        kwargs={
            "job_title": job_input,
            "target_location": loc_input,
            "date_range": backend_date_range,
            "run_type": "manual"
        }
    )
    scraper_thread.start()
    st.sidebar.success("🛰️ Scraper launched in background thread!")