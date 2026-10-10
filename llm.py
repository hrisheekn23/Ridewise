import json
import os
import re
from openai import OpenAI

def _client():
    api_key = os.getenv("NEOSTATS_API_KEY", "").strip()
    base_url = os.getenv(
        "NEOSTATS_BASE_URL",
        "https://neo-hackathon.services.ai.azure.com/openai/v1/"
    ).strip()

    if not api_key:
        raise RuntimeError("Set NEOSTATS_API_KEY in your .env file.")

    return OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=35,
        max_retries=1
    )

def _model():
    model = os.getenv("NEOSTATS_MODEL", "Neo-Hackathon").strip()
    if not model:
        raise RuntimeError("Set NEOSTATS_MODEL in your .env file.")
    return model

def generate_sql(question, schema, role, customer_id=None):
    """Ask the provided model for one read-only SQL query; execution is guarded in db.py."""
    scope = ""
    if role == "Customer":
        scope = (
            f"Customer mode. You MUST include a WHERE condition customer_id = '{customer_id}' "
            "in the SQL. Do not query another customer's records. Only ask for rows needed "
            "to answer this user's question."
        )
    else:
        scope = "Support-agent mode. Query only information relevant to the question."

    prompt = f"""
Generate exactly one SQLite SELECT statement, or return NONE if database data is not needed.
Never generate INSERT, UPDATE, DELETE, PRAGMA, schema changes, or multiple statements.
Use only the tables and columns in this schema:
{schema}

Role instructions: {scope}
Question: {question}

Return only SQL, without markdown fences or explanation.
"""
    response = _client().chat.completions.create(
        model=_model(),
        messages=[
            {
                "role": "system",
                "content": "You generate safe, read-only SQLite queries. Follow the schema exactly."
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    sql = (response.choices[0].message.content or "").strip()
    sql = re.sub(r"^```(?:sql)?\s*|\s*```$", "", sql, flags=re.I).strip()

    if sql.upper() == "NONE" or not sql:
        return None

    return sql

def chat_completion(system_prompt, user_prompt, history=None):
    messages = [{"role": "system", "content": system_prompt}]

    for item in history or []:
        if item.get("role") in {"user", "assistant"}:
            messages.append({
                "role": item["role"],
                "content": item["content"]
            })

    messages.append({"role": "user", "content": user_prompt})

    response = _client().chat.completions.create(
        model=_model(),
        messages=messages,
        temperature=0.2,
    )

    return (response.choices[0].message.content or "").strip() or (
        "I couldn't produce an answer from the available evidence."
    )