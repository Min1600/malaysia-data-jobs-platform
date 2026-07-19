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
import numpy as np

HF_TOKEN = os.environ.get("HF_TOKEN")

# ==========================================
# STREAMLIT USER INTERFACE & BUTTONS
# ==========================================
main_logger = logging.getLogger(__name__)

kl_timezone = ZoneInfo("Asia/Kuala_Lumpur")
current_time = datetime.now(kl_timezone).strftime('%d-%m-%Y')

#@st.cache_data
def fetch_data(website, current_time):

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

        target_columns = ["job_title", "company", "url", "posting_date", "industry", "skills"]
        existing_columns = [col for col in target_columns if col in df.columns]
        check = ["job_title", "company"]
        return df[["job_title", "company","search_term"]]
    except Exception as e:
        main_logger.warning(f"❌ Error downloading database: {e}")
        return None

def fetch_no_copies(website, current_time):
    
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

        target_columns = ["job_title", "company", "url", "posting_date", "industry", "skills"]
        existing_columns = [col for col in target_columns if col in df.columns]
        check = ["job_title", "company"]
        new_df = df.drop_duplicates(subset=check)
        return new_df[["job_title", "company","search_term"]]
    except Exception as e:
        main_logger.warning(f"❌ Error downloading database: {e}")
        return None

st.write("Today's scraped data")
st.header("Linkedin Data")
st.write(fetch_data('linkedin',current_time))
st.write(fetch_no_copies('linkedin',current_time))
st.header("Jobstreet Data")
st.write(fetch_data('jobstreet',current_time))
st.write(fetch_no_copies('jobstreet',current_time))

st.sidebar.header("⚙️ Live Scraper Controller")
st.sidebar.write("Serch for job postings of your choice!")

with st.sidebar.form("manual scraper form"):
    job_input = st.text_input("Job Title Keyword", "Data Analyst")
    loc_input = st.text_input("Target Location", "Kuala Lumpur")
    date_input = st.selectbox(
        "Date Range Filter", 
        options=["all", "daily", "weekly", "monthly"]
    )

    backend_date_range = None if date_input == 'all' else date_input

    # The Activation Button for scraper
    if st.form_submit_button("🚀 Run Scraper"):
        with st.status("🛰️ Initializing Scraping Engines...", expanded=True) as status:
            try:
                status.write("🕵️ Fetching proxies and connecting to job boards...")
                
                # Run the scraper synchronously inside the status block
                job_scraper(
                    job_title=job_input,
                    target_location=loc_input,
                    date_range=backend_date_range,
                    run_type="manual"
                )
                
                status.write("📦 Packing raw listings and pushing data to Hugging Face...")
                status.update(label="🎉 Manual Scrape Completed Successfully!", state="complete", expanded=False)
                st.success("Data updated! Refreshing view...")
                
                # Force Streamlit to clear data cache and read the brand new file!
                st.cache_data.clear()
                st.rerun()

            except Exception as e:
                status.update(label="❌ Scraper pipeline encountered an error", state="error")
                st.error(f"Execution failed: {e}")
