from fastapi import FastAPI, Query, Request, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse
from ingestion.linkedin import ld_scraper