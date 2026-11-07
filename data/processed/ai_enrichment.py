import os
import json
import logging
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, ValidationError

load_dotenv()
logger = logging.getLogger(__name__)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASS = os.environ.get("POSTGRES_PASS")

BATCH_SIZE = 5

EXTRACTION_PROMPT = """Extract skills and requirements from each job posting below. Return JSON matching the schema, with one result per job_index.

SKILLS: technical tools, languages, frameworks, databases, platforms, methodologies explicitly mentioned. No soft skills like communication/teamwork - put those under requirements if explicitly required. Normalize names ("SQL" not "SQL skills", "Power BI" not "Microsoft Power BI"). No duplicates, no invented or implied skills.

REQUIREMENTS: explicit candidate requirements only (experience, education, certifications, language, eligibility), rewritten as concise standalone statements. Do not copy the description text or include job responsibilities. No invented requirements.

Use an empty list for either field if nothing qualifies.

Jobs:
{jobs_block}
"""


class JobExtraction(BaseModel):
    job_index: int
    skills: list[str]
    requirements: list[str]


class BatchExtraction(BaseModel):
    results: list[JobExtraction]


def get_connection():
    return psycopg2.connect(
        host="localhost",
        port="5433",
        database="jobs",
        user=POSTGRES_USER,
        password=POSTGRES_PASS
    )


def chunked(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def ai_enrichment(ai_model, limit=None):
    conn = get_connection()
    cur = conn.cursor()

    query = """
        SELECT s.job_key, s.job_description
        FROM silver_jobs s
        LEFT JOIN ai_enrichment a
            ON s.job_key = a.job_key
        WHERE a.job_key IS NULL
    """
    if limit:
        query += " LIMIT %s"
        cur.execute(query, (limit,))
    else:
        cur.execute(query)

    jobs = cur.fetchall()
    logger.info(f"{len(jobs)} jobs pending enrichment")

    total_enriched = 0

    for batch in chunked(jobs, BATCH_SIZE):
        jobs_block = "\n\n".join(
            f"[{i}] {description}" for i, (_, description) in enumerate(batch)
        )

        try:
            completion = client.chat.completions.create(
                model=ai_model,
                messages=[
                    {"role": "user", "content": EXTRACTION_PROMPT.format(jobs_block=jobs_block)}
                ],
                response_format={"type": "json_object", "schema": BatchExtraction.model_json_schema()},
                temperature=0.1,
            )
            parsed = BatchExtraction.model_validate_json(completion.choices[0].message.content)
        except (ValidationError, json.JSONDecodeError) as e:
            logger.error(f"Batch returned invalid structure, skipping batch: {e}")
            continue
        except Exception as e:
            logger.error(f"Groq request failed, skipping batch: {e}")
            continue

        rows = []
        for result in parsed.results:
            if not 0 <= result.job_index < len(batch):
                logger.warning(f"Dropping result with out-of-range job_index {result.job_index}")
                continue
            job_key, _ = batch[result.job_index]
            rows.append((
                job_key,
                json.dumps(result.skills),
                json.dumps(result.requirements),
                ai_model,
                "1.1.0"
            ))

        if not rows:
            continue

        try:
            psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO ai_enrichment (
                    job_key, skills, requirements, ai_model, ai_prompt_version
                )
                VALUES %s
                """,
                rows,
            )
            conn.commit()
            total_enriched += len(rows)
            logger.info(f"Enriched {len(rows)}/{len(batch)} jobs in batch")
        except Exception as e:
            conn.rollback()
            logger.error(f"Insert failed for batch, rolled back: {e}")

    logger.info(f"Done. {total_enriched}/{len(jobs)} jobs enriched")
    cur.close()
    conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ai_enrichment("openai/gpt-oss-120b", limit=5)
