import os
import logging
from fastapi import FastAPI, Query, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Import modules
from ingestion.linkedin.linkedin_scraper import ld_scraper

# Setup
ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

# Logging
os.makedirs("logs", exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
logging.basicConfig(
    filename=f"logs/app-{timestamp}.log",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Data Platform Host",
    description="API for malaysian jobs web scraping",
    version="1.0.0"
)
