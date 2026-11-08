import os
import json
import psycopg2
import psycopg2.extras
import logging
import time
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"), max_retries = 0)
POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASS = os.environ.get("POSTGRES_PASS")
HF_TOKEN = os.environ.get("HF_TOKEN")

logging.basicConfig(
    level = logging.INFO,
    filename = "ai_enrichment.log",
    # format of file message
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

def pull():
  
  conn = psycopg2.connect(
        host="localhost",
        port="5433",
        database="jobs",
        user=POSTGRES_USER,
        password=POSTGRES_PASS
    )
  cur = conn.cursor()
  cur.execute("""
    SELECT
        s.job_description
    FROM silver_jobs s
    LEFT JOIN ai_enrichment a
        ON s.job_key = a.job_key
    WHERE a.job_key IS NULL
    LIMIT 10;
  """)
  test = cur.fetchall()
  print(test)  # e.g. [(101,), (102,), (105,), ...]
  cur.close()
  conn.close()

def ai_enrichment(ai_model):

  # define structure of output
  class JobRequirements(BaseModel):
      skills: list[str]
      requirements: list[str]

  conn = psycopg2.connect(
        host="localhost",
        port="5433",
        database="jobs",
        user=POSTGRES_USER,
        password=POSTGRES_PASS
    )
  cur = conn.cursor()
  logger.debug("selecting table")

  cur.execute(""" 
  SELECT 
  s.job_key, 
  s.job_description 
  FROM silver_jobs s
  LEFT JOIN ai_enrichment a 
  ON s.job_key = a.job_key
  WHERE a.job_key IS NULL
  LIMIT 5;
  """)
  job_descriptions = cur.fetchall()
  logger.debug("iterating start")
  # Llama 3.3 70B Versatile (llama-3.3-70b-versatile)
  # Tokens Per Day (TPD): 100,000
  # Tokens Per Minute (TPM): 12,000
  # Requests Per Day (RPD): 1,000
  # Requests Per Minute (RPM): 30

  # llama-3.1-8b-instant(llama-3.1-8b-instant)
  # Tokens Per Day (TPD): 500,000
  # Tokens Per Minute (TPM): 6,000
  # Requests Per Day (RPD): 14,400
  # Requests Per Minute (RPM): 30
  for job_key, job_description in job_descriptions:
    logger.info(f"{job_key}:{job_description}")
    # Call Groq's Chat Completion with Structured Outputs
    completion = client.chat.completions.create(
        model=ai_model, # Highly intelligent open-source model
        messages=[
            {
                "role": "system",
                "content": """
    You are an information extraction assistant specializing in job postings.
    Your task is to analyze the job description and extract:
    1. Technical and professional skills
    2. Candidate requirements

    from the job description into a raw JSON object matching the requested schema
    Follow these rules carefully.

    SKILLS:
    - Extract specific technical skills, tools, software, programming languages,
      frameworks, databases, platforms, methodologies, and relevant professional
      competencies explicitly mentioned in the job description.
    - Examples include: Python, SQL, Excel, Power BI, Tableau, Java, AWS,
      Azure, Snowflake, dbt, Airflow, Git, Docker, Machine Learning.
    - Skills should primarily contain technical skills, tools, technologies, programming languages, databases, platforms, and role-specific professional competencies. 
      Do not include generic soft skills such as communication, teamwork, leadership, or problem-solving as skills. 
      Include those in requirements when they are explicitly stated as candidate requirements.
    - Only extract skills and requirements that are explicitly supported by the job description. Do not infer skills based on the job title, responsibilities, industry, or commonly associated technologies.
    - Use concise, standardized names where possible.
    - Do not include duplicate skills.
    - Return an empty list if no skills can be identified.

    REQUIREMENTS:
    - Extract explicit requirements that a candidate is expected or preferred
      to meet.
    - Include years of experience, education, qualifications, certifications,
      technical knowledge, professional experience, language requirements,
      and other eligibility criteria.
    - Preserve the meaning of the original requirement but rewrite it concisely.
    - Each requirement should be a standalone statement.
    - Do not simply copy the entire job description.
    - Do not include responsibilities or descriptions of what the employee will do
      unless they also represent a candidate requirement.
    - Do not invent requirements that are not present in the job description.
    - Return an empty list if no requirements can be identified.

    IMPORTANT:
    - Only extract information supported by the provided job description.
    - Do not guess or infer requirements that are not stated.
    - Keep each skill concise.
    - Keep each requirement concise and informative.
    - Normalize obvious variations of the same skill to a consistent name.
    - For example, use "SQL" instead of "SQL skills" or "SQL querying" when the
      description clearly refers to SQL.
    - Use "Power BI" rather than variations such as "Microsoft Power BI".
    - Do not merge distinct technologies simply because they are related.
        """
            },
        {
      "role": "user",
      "content": job_description
        }
        ],
        # Tell Groq to strictly follow your Pydantic schema structure
        response_format={
          "type": "json_schema", 
          "json_schema":{
            "name": "jd_schema",
            "strict": True,
            "schema": JobRequirements.model_json_schema()
            }
          },
        temperature=0.1,
        reasoning_effort="low"
    )
    usage = completion.usage

    logger.info(f"Prompt tokens: {usage.prompt_tokens}")
    logger.info(f"Completion tokens: {usage.completion_tokens}")

    if usage.prompt_tokens_details:
        logger.info(
            f"Cached tokens: "
            f"{usage.prompt_tokens_details.cached_tokens}"
        )
    raw_json_string = completion.choices[0].message.content
    python_dict = json.loads(raw_json_string)
    #print(python_dict)
    skills_json = json.dumps(python_dict.get("SKILLS") or python_dict.get("skills"))
    reqs_json = json.dumps(python_dict.get("REQUIREMENTS") or python_dict.get("requirements"))
    logger.info(f"Skills: {skills_json}")
    logger.info(f"Requirement Summary: {reqs_json}")
    cur.execute("""
        INSERT INTO ai_enrichment (
            job_key,
            skills,
            requirements,
            ai_model,
            ai_prompt_version
        ) 
        VALUES (%s, %s, %s, %s, %s);
        """, (
            job_key, 
            skills_json,
            reqs_json,
            ai_model,
            "1.0.0" 
        )
    )
    conn.commit()
    time.sleep(60)
  cur.close()
  conn.close()
if __name__ == "__main__":
  ai_enrichment("openai/gpt-oss-120b")
