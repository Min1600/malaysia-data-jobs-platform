import psycopg2
import psycopg2.extras
import json
import os
from dotenv import load_dotenv
from huggingface_hub import hf_hub_download
from pathlib import Path
from huggingface_hub import snapshot_download
from zoneinfo import ZoneInfo

load_dotenv()
POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASS = os.environ.get("POSTGRES_PASS")
HF_TOKEN = os.environ.get("HF_TOKEN")

def insert_data(website):

    files_succeeded = 0
    files_failed = 0
    total_inserted = 0
    total_duplicates = 0

    repo_dir = snapshot_download(
        repo_id="Amin1600/Web_Scraper_Data",
        repo_type="dataset",
        allow_patterns=f"job_data/raw/{website}/*",
        token=HF_TOKEN,
        tqdm_class=None
    )

    target_folder = Path(repo_dir) / "job_data" / "raw" / website

    conn = psycopg2.connect(
        host="localhost",
        port="5433",
        database="jobs",
        user=POSTGRES_USER,
        password=POSTGRES_PASS
    )
    cur = conn.cursor()

    for job_file in target_folder.rglob('*.jsonl'):

        cur.execute(
            "SELECT 1 FROM file_metadata WHERE file_name = %s",
            (job_file.name,)
        )
        if cur.fetchone():
            print(f"Skipping {job_file.name} (already loaded)")
            continue

        # Build rows, tolerating bad JSON lines individually
        rows = []
        with open(job_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                try:
                    job = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"⚠️ Skipping malformed line {line_num} in {job_file.name}: {e}")
                    continue

                rows.append((
                    job.get("source"),
                    job.get("search_term"),
                    job.get("job_id"),
                    job.get("url"),
                    job.get("collection_timestamp"),
                    job.get("job_title"),
                    job.get("company"),
                    job.get("location"),
                    job.get("employment_type"),
                    job.get("salary_min"),
                    job.get("salary_max"),
                    job.get("department"),
                    job.get("posting_date"),
                    job.get("job_description"),
                    job.get("requirements"),
                    json.dumps(job.get("skills", [])),
                    job.get("raw_html")
                ))

        if not rows:
            print(f"No valid rows in {job_file.name}, skipping.")
            continue

        try:
            inserted = psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO stg_jobs (
                    source, search_term, job_id, url, collection_timestamp,
                    job_title, company, location, employment_type, salary_min,
                    salary_max, department, posting_date, job_description,
                    requirements, skills, raw_html
                )
                VALUES %s
                ON CONFLICT (source, job_id)
                DO NOTHING
                RETURNING job_id;
                """,
                rows,
                template="(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)",
                page_size=100,
                fetch=True
            )

            num_inserted = len(inserted)
            num_duplicates = len(rows) - num_inserted

            cur.execute(
                "INSERT INTO file_metadata (file_name) VALUES (%s)",
                (job_file.name,)
            )
            conn.commit()

            total_inserted += num_inserted
            total_duplicates += num_duplicates
            files_succeeded += 1

            print(f"✅ {job_file.name}: {num_inserted} inserted, {num_duplicates} duplicates skipped")

        except Exception as e:
            conn.rollback()
            files_failed += 1
            print(f"❌ {job_file.name} failed, transaction rolled back: {e}")
            continue

    print("\n--- INSERTION REPORT ---")
    print(f"Files loaded: {files_succeeded}")
    print(f"Files failed: {files_failed}")
    print(f"Total rows inserted: {total_inserted}")
    print(f"Total duplicates skipped: {total_duplicates}")

    cur.close()
    conn.close()


if __name__ == "__main__":

    scraped_websites = ["linkedin", "jobstreet"]
    for website in scraped_websites:
        insert_data(website)