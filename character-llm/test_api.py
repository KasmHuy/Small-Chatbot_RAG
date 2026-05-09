import requests
import os
from dotenv import load_dotenv

load_dotenv(r"D:\Small-Chatbot_RAG\.env")

API_KEY = os.getenv("GEMINI_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={API_KEY}"

payload = {
    "contents": [{"parts": [{"text": "Say hello in Vietnamese"}]}]
}

response = requests.post(url, json=payload)
data = response.json()
response = requests.post(url, json=payload)
data = response.json()

if response.status_code == 200:
    print(data["candidates"][0]["content"]["parts"][0]["text"])
elif response.status_code == 429:
    print("Rate limited — chờ 1 phút rồi thử lại")
else:
    print(f"Lỗi {response.status_code}:", data)
print(response.status_code)
print(response.json())
print(data["candidates"][0]["content"]["parts"][0]["text"])