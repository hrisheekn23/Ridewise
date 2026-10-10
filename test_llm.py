import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

env_path = Path(__file__).parent / ".env"
print("env path:", env_path, "| exists:", env_path.exists())
print("loaded:", load_dotenv(env_path, override=True))
print("key found:", bool(os.getenv("NEOSTATS_API_KEY")))

client = OpenAI(
    base_url=os.getenv("NEOSTATS_BASE_URL"),
    api_key=os.getenv("NEOSTATS_API_KEY"),
)
r = client.chat.completions.create(
    model=os.getenv("NEOSTATS_MODEL"),
    messages=[{"role": "user", "content": "What is the capital of France?"}],
)
print(r.choices[0].message.content)