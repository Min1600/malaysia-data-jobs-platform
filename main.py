import os
import pandas as pd
import streamlit as st

st.title("🇲🇾 Malaysian Data Analyst Job Market Tracker")
st.write("Data updated automatically every night via GitHub Actions.")

DATA_FILE = "linkedin_jobs.jsonl"

# 🌟 1. Check if the file actually exists first
if os.path.exists(DATA_FILE):
    try:
        # 🌟 2. Ensure the file is not completely empty
        if os.path.getsize(DATA_FILE) > 0:
            df = pd.read_json(DATA_FILE, lines=True)
            
            st.subheader("Latest Job Openings")
            # Using standard indexing instead of selective columns to prevent KeyErrors
            st.dataframe(df)
        else:
            st.warning("⚠️ The data file is empty. Waiting for the first scraper data dump.")
            
    except Exception as e:
        st.error(f"Error parsing data file: {e}")
else:
    # 🌟 3. If file isn't there yet, show a clean message instead of freezing!
    st.warning("⏳ 'linkedin_jobs.jsonl' not found yet.")
    st.info("The application is running fine! It will populate automatically once your GitHub Actions script runs its first push.")