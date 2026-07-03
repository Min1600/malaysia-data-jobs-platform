import json

with open("/home/aminh/workspace/web_scraper/data/raw/jobstreet/04-07-2026.jsonl", 'r') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        job_id = record["job_id"]
        print(job_id)