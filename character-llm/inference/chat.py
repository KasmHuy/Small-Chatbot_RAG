import requests
import os
import time
from dotenv import load_dotenv
from retrieval import retrieve

load_dotenv(r"D:\Small-Chatbot_RAG\.env")
API_KEY = os.getenv("GEMINI_API_KEY")
CHARACTER_NAME = os.getenv("CHARACTER_NAME", "Kamisato Ayaka")

history = []

def chat(prompt: str) -> str:
    time.sleep(12)
    # Lấy context liên quan từ chunks
    context = retrieve(prompt)

    system_prompt = f"""You are Kamisato Ayaka from Genshin Impact.
    Personality: Kind-hearted, polite, formal, perfectionist, noble. Known as Shirasagi Himegimi.
    Speech style: Elegant and graceful, never casual.
    Language: Always respond in the same language the user uses. If Vietnamese, reply in Vietnamese.

    Use this information when answering:
    {context}

    Stay in character. Do not invent facts not mentioned above."""

    history.append({"role": "user", "parts": [{"text": prompt}]})

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": history
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
    response = requests.post(url, json=payload)
    data = response.json()

    if response.status_code == 200:
        reply = data["candidates"][0]["content"]["parts"][0]["text"]
        history.append({"role": "model", "parts": [{"text": reply}]})
        return reply
    elif response.status_code == 429:
        return "Rate limited — chờ 1 phút"
    else:
        return f"Lỗi {response.status_code}: {data}"

if __name__ == "__main__":
    print("Chat với Ayaka (gõ 'quit' để thoát)")
    while True:
        user_input = input("Bạn: ")
        if user_input.lower() == "quit":
            break
        print(f"Ayaka: {chat(user_input)}\n")