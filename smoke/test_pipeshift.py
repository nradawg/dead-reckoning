"""Smoke test: Pipeshift — one chat completion through their OpenAI-compatible API."""
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

API_KEY = os.environ.get("PIPESHIFT_API_KEY")
if not API_KEY:
    sys.exit("FAIL: no PIPESHIFT_API_KEY in .env")

MODEL = os.environ.get("PIPESHIFT_MODEL", "deepseek-ai/DeepSeek-V4-Flash")

client = OpenAI(api_key=API_KEY, base_url="https://api.pipeshift.com/api/v0/")
chat = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Reply with exactly: KEPT"},
    ],
    max_tokens=16,
)
reply = chat.choices[0].message.content
print("model reply:", reply)
print(f"PASS: Pipeshift inference works (model={MODEL})")
