import logging
import sys
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from scraper import job_scraper, SEARCH_TERMS

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

def daily_scraper():
    for job in SEARCH_TERMS:
        job_scraper(
            job_title=job,
            target_location="Kuala Lumpur",
            date_range="daily",
            run_type="scheduled"
        )


if __name__ == "__main__":
    daily_scraper()