import os
import logging
import sys
from fastapi import FastAPI, Query, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Import modules


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
file_handler.setLevel(logging.INFO) # Capture everything Info and up
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# 3. Create Handler #2: For streaming to terminal screen
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG) # Show even minor debug logs in terminal
console_formatter = logging.Formatter('▶ [%(levelname)s] %(message)s')
console_handler.setFormatter(console_formatter)

# 4. Tie both handlers to the root logger
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

main_logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Data Platform Host",
    description="API for malaysian jobs web scraping",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"Hello": "World"}


if __name__ == "__main__":
    # Configure a quick, temporary local Root Logger just for this terminal test
    logging.basicConfig(
        level=logging.INFO, # Sets it to INFO so your test logs actually show up!
        format='[LOCAL TEST] %(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("🧪 Running isolated scraper test script...")
    # run_linkedin_scrape()