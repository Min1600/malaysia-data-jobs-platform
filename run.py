import os
import logging
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Import modules
from ingestion.jobstreet.jobstreet_scraper import js_scraper, get_total_pages
from ingestion.linkedin.linkedin_scraper import ld_scraper, get_total_pages

# Setup
ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

# Logging
os.makedirs("logs", exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")

# 1. Initialize the master root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG) # Master threshold level

# 2. Create Handler #1: For writing to a file
timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
file_handler = logging.FileHandler(f"logs/app-{timestamp}.log")
file_handler.setLevel(logging.INFO) 
file_formatter = logging.Formatter('%(asctime)s:%(name)s - [%(levelname)s]: %(message)s')
file_handler.setFormatter(file_formatter)

# 3. Create Handler #2: For streaming to terminal screen
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG) 
console_formatter = logging.Formatter('[%(levelname)s]: %(message)s')
console_handler.setFormatter(console_formatter)

# 4. Tie both handlers to the root logger
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# initialize logger for current file (main.py)
main_logger = logging.getLogger(__name__)



if __name__ == "__main__":
    """
    logger.info("⏰ Scheduled automation started...")
    
    logger.info("🚀 Starting JobStreet Scraper...")
    js_scraper()
    
    logger.info("🚀 Starting LinkedIn Scraper...")
    ld_scraper()
    
    logger.info("🏁 All scraping tasks completed successfully.")
    """
    print("Hello World")