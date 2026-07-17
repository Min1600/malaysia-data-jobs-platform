import streamlit as st
import logging
import sys
import os
import threading
import time
import requests
import pandas as pd
from datetime import datetime
from huggingface_hub import hf_hub_download
from zoneinfo import ZoneInfo


HF_TOKEN = os.environ.get("HF_TOKEN")
# ==========================================
# 1. CORE INFRASTRUCTURE: LOGGING (Runs ONCE)
# ==========================================
@st.cache_resource
def initialize_global_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Clean out any accidental duplicate handlers on boot
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Mute sub-loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    # File Handler Setup
    os.makedirs("logs", exist_ok=True)

    # Convert the current clock time into an actual string representation
    kl_timezone = ZoneInfo("Asia/Kuala_Lumpur")
    date_str = datetime.now(kl_timezone).strftime('%d-%m-%Y(%H-%M)')

    file_handler = logging.FileHandler(
        filename=os.path.join("logs", f"{date_str}-job-scraper.log"),
        mode='a', # append to file
        encoding='utf-8'
    )


    file_handler.setLevel(logging.INFO) 
    file_formatter = logging.Formatter('%(asctime)s:%(name)s - [%(levelname)s]: %(message)s')
    file_handler.setFormatter(file_formatter)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG) 
    console_formatter = logging.Formatter('[%(levelname)s]: %(message)s')
    console_handler.setFormatter(console_formatter)

    # Attach handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return "Logging successfully initialized"


initialize_global_logging()
main_logger = logging.getLogger(__name__)
main_logger.info("Application UI successfully booted up!")

# ==========================================
# 2. STREAMLIT USER INTERFACE & BUTTONS
# ==========================================


def fetch_data(website):
    kl_timezone = ZoneInfo("Asia/Kuala_Lumpur")
    current_time = datetime.now(kl_timezone).strftime('%d-%m-%Y')
    try:
        # 1. Pull the specific data vault file down from your private dataset
        local_file_path = hf_hub_download(
            repo_id="Amin1600/Web_Scraper_Data",
            filename=f"job_data/raw/{website}/{current_time}.jsonl",
            repo_type="dataset",
            token=HF_TOKEN
        )
        
        # 2. Read it directly into a Pandas DataFrame
        df = pd.read_json(local_file_path, lines=True)
        main_logger.info(f"📊 Successfully loaded {len(df)} jobs rows from {website} uploaded on {current_time}.")

        target_columns = ["job_title", "company", "salary_min", "posting_date", "industry", "skills", "employment_type"]
        existing_columns = [col for col in target_columns if col in df.columns]
        
        return df[existing_columns]

    except Exception as e:
        main_logger.warning(f"❌ Error downloading database: {e}")
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

# The Activation Button for scraper
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



def keep_alive(space_url, interval_seconds=7200):
    """
    Pings hugging face every 2 hours to ensure it doesnt go to sleep

    Args:
        space_url: url of hugging face server
        interval_seconds: how often to ping the server in seconds

    Return:
        None
    """
    
    while True:
        try:
            # Self-ping the space UI to keep the container awake
            response = requests.get(space_url, timeout=10)
            main_logger.debug(f"💓 Keep-alive ping sent to {space_url}. Status: {response.status_code}")
        except Exception as e:
            main_logger.debug(f"⚠️ Keep-alive ping failed: {e}")
        
        time.sleep(interval_seconds)

# Using st.cache_resource ensures this code block executes EXACTLY ONCE 
# when the server boots up, and never again during page refreshes.
@st.cache_resource
def start_lifetime_keep_alive():
    MY_SPACE_URL = "http://localhost:8501/_stcore/health"
    
    keep_alive_thread = threading.Thread(
        target=keep_alive, 
        args=(MY_SPACE_URL,), 
        daemon=True # Dies cleanly if the Streamlit server stops
    )
    keep_alive_thread.start()
    return "Keep-alive thread deployed successfully."

# Trigger the guarded thread launcher
keep_alive_status = start_lifetime_keep_alive()