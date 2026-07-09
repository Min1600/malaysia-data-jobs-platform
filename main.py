import streamlit as st
import logging
import sys
import threading
from datetime import datetime
from run import job_scraper
from apscheduler.schedulers.background import BackgroundScheduler


st.sidebar.header("⚙️ Live Scraper Controller")
st.sidebar.write("Trigger an on-demand cloud scraping run on GitHub Actions.")

# 1. UI Input fields
job_input = st.sidebar.text_input("Job Title Keyword", "Data Analyst")
loc_input = st.sidebar.text_input("Target Location", "Kuala Lumpur")
date_input = st.sidebar.selectbox(
    "Date Range Filter", 
    options=["all", "daily", "weekly", "monthly"]
)

if date_input == 'all':
    date_input = 'None'
# 2. Map frontend inputs to match your backend python variables
#date_mapping = {"all": "None", "daily": "r86400", "weekly": "r604800", "monthly": "r2592000"}

# 3. The Activation Button
if st.sidebar.button("🚀 Run Scraper"):

    # 🌟 Create a separate background thread so the UI doesn't freeze!
    scraper_thread = threading.Thread(
        target=job_scraper,
        kwargs={
            "job_title": job_input,
            "target_location": loc_input,
            "date_range": date_input,
            "run_type": "manual"
        }
    )
    # Start the background task
    scraper_thread.start()


# 🌟 1. Configure the global root logger ONLY ONCE on application startup
if "logger_initialized" not in st.session_state: # Streamlit specific safety guard
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Mute sub-loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    # File Handler
    import os
    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    file_handler = logging.FileHandler(f"logs/app-{timestamp}.log")
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

# 🌟 2. Now initialize file-specific loggers anywhere using __name__
main_logger = logging.getLogger(__name__)
main_logger.info("Application UI successfully booted up!")

def daily_scraper():
    # Injected values are passed directly into the function call here!
    start_scraping_routine(
        job_title="Data Analyst",
        target_location="Kuala Lumpur",
        date_range="daily",
        run_type="scheduled"
    )

scheduler = BackgroundScheduler()
# Runs every single night
scheduler.add_job(automated_job, 'cron', hour=16, minute=0)
scheduler.start()