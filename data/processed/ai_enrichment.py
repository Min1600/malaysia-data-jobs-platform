import os
import json
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
POSTGRES_USER = os.environ.get("POSTGRES_USER")
POSTGRES_PASS = os.environ.get("POSTGRES_PASS")
HF_TOKEN = os.environ.get("HF_TOKEN")

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

  # Llama 3.3 70B Versatile (llama-3.3-70b-versatile)
  # Tokens Per Day (TPD): 100,000
  # Tokens Per Minute (TPM): 12,000R
  # Requests Per Day (RPD): 1,000
  # Requests Per Minute (RPM): 30
  for job_key, job_description in job_descriptions:
    # Call Groq's Chat Completion with Structured Outputs
    completion = client.chat.completions.create(
        model=ai_model, # Highly intelligent open-source model
        messages=[
            {
                "role": "user",
                "content": f"""You are an information extraction assistant specializing in job postings.
    Your task is to analyze {job_description} and extract:
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
    - Do not invent skills that are not explicitly mentioned or clearly implied.
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
            }
        ],
        # Tell Groq to strictly follow your Pydantic schema structure
        response_format={"type": "json_object", "schema": JobRequirements.model_json_schema()},
        temperature=0.1,
    )

    raw_json_string = completion.choices[0].message.content
    python_dict = json.loads(raw_json_string)
    #print(python_dict)
    skills_json = json.dumps(python_dict.get("SKILLS") or python_dict.get("skills"))
    reqs_json = json.dumps(python_dict.get("REQUIREMENTS") or python_dict.get("requirements"))

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
  cur.close()
  conn.close()

if __name__ == "__main__":
  ai_enrichment("llama-3.3-70b-versatile")
