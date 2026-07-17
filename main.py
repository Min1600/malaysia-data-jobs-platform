import streamlit as st
import os
import logging
import threading
import time
import requests
import pandas as pd
from datetime import datetime
from huggingface_hub import hf_hub_download
from zoneinfo import ZoneInfo
from scraper import job_scraper

HF_TOKEN = os.environ.get("HF_TOKEN")

# ==========================================
# STREAMLIT USER INTERFACE & BUTTONS
# ==========================================
main_logger = logging.getLogger(__name__)

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
