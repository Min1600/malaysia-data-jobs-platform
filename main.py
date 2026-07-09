import os
import requests
import pandas as pd
import streamlit as st

# ... your existing code displaying data tables ...

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
if st.sidebar.button("🚀 Trigger Cloud Scraper"):
    # Fetch your hidden access token from Hugging Face environment variables
    gh_token = os.environ.get("GH_PAT")
    
    # Change these to match your exact github profile details
    GITHUB_USERNAME = "Min1600"
    REPO_NAME = "malaysia-data-jobs-platform"
    WORKFLOW_FILE = "run-web-scraper.yml"  # Name of your workflow file
    
    if not gh_token:
        st.sidebar.error("Missing 'GH_PAT' Secret in Hugging Face Settings.")
    else:
        with st.spinner("Waking up GitHub Action Runner..."):
            url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/actions/workflows/{WORKFLOW_FILE}/dispatches"
            headers = {
                "Authorization": f"token {gh_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            payload = {
                "ref": "main", # Run on your main branch code
                "inputs": {
                    "job_type": job_input,
                    "location": loc_input,
                    "date_range": date_input
                }
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 204:
                st.sidebar.success("🎉 GitHub Workflow started! Your fresh data will show up here in a few minutes.")
            else:
                st.sidebar.error(f"Failed to connect. Error {response.status_code}: {response.text}")          