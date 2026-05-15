import os
from pathlib import Path

import requests
from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")

url = (
    "https://generativelanguage.googleapis.com/v1/"
    f"models/gemini-2.5-flash:generateContent?key={API_KEY}"
)

payload = {
    "contents": [{"parts": [{"text": "Say hello in Vietnamese"}]}]
}

response = requests.post(url, json=payload)
data = response.json()

if response.status_code == 200:
    print(data["candidates"][0]["content"]["parts"][0]["text"])
elif response.status_code == 429:
    print("Rate limited - cho 1 phut roi thu lai")
else:
    print(f"Loi {response.status_code}:", data)

print(response.status_code)
print(data)
