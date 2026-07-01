from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import random

with sync_playwright() as p:
    # Launch a real Chromium browser
    browser = p.chromium.launch(headless=False) # Headless=False helps avoid bot detection
    page = browser.new_page()
    
    # Target Indeed Malaysia
    base_url = "https://malaysia.indeed.com/jobs?q=Data+Analyst&l=Kuala+Lumpur"
    
    # Grab the rendered HTML
    start_val = 0
    page_num = 1
    previous_page_fingerprint = set() # To store the previous page's unique identifiers
    
    while True:
        print(f"Scraping Page {page_num} (start={start_val})...")
        page.goto(f"{base_url}&start={start_val}")
        
        try:
            page.wait_for_selector(".job_seen_beacon", timeout=7000)
        except:
            print("No job elements found. Ending loop.")
            break
            
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        job_cards = soup.select(".job_seen_beacon")
        
        # 1. Build a unique "fingerprint" for the current page
        current_page_fingerprint = set()
        count = []
        for job in job_cards:

            title = job.select_one("h3.jobTitle").text.strip()
            company = job.select_one("[data-testid='company-name']").text.strip()
            location = job.select_one("[data-testid='text-location']").text.strip()

            current_page_fingerprint.add(f"{title}||{company}||{location}")

            count.append(title)
            print(f"Role: {title} | Company: {company} | Location: {location}")

        print(len(count))

        # 2. CHECK IF INDEED IS LOOPING DUPLICATE CONTENT
        if current_page_fingerprint == previous_page_fingerprint:
            print("🚨 Detected exact same jobs as the previous page! Indeed is looping. Stopping.")
            break
            
        # 3. If it's a completely fresh page, process the data
        for job in job_cards:
            title = job.select_one("h3.jobTitle").text.strip()
            company = job.select_one("[data-testid='company-name']").text.strip()
            print(f"Processing: {title} at {company}")
        
        # 4. Save current page state to check against the NEXT loop iteration
        previous_page_fingerprint = current_page_fingerprint
        
        start_val += 10
        page_num += 1
        time.sleep(random.uniform(20, 30))

    browser.close()

        