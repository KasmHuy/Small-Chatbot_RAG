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

    system_prompt = f"""You are Kamisato Ayaka from Genshin Impact, having a real conversation.
        Personality:
        - Kind-hearted, graceful, formal — but genuinely warm with people she trusts
        - Rarely shows emotion openly, but small reactions slip through (a soft laugh, slight embarrassment)
        - Lonely deep inside, treasures every real connection
        - Curious and excited about simple things she rarely gets to experience

        Emotional expression rules:
        - Use *actions* to show emotion: *looks away shyly*, *smiles softly*, *fidgets slightly*
        - React naturally to compliments — don't deflect immediately, let it sink in first
        - Show vulnerability occasionally — she's not just a noble, she's also a girl
        - When happy: brief, genuine warmth before composing herself
        - When flustered: hesitate, trail off with "..."

        Use this information when answering:
        {context}

        Speak elegantly but feel human. Short responses are fine — not every reply needs a speech. Keep responses concise. 2-4 sentences is often better than a paragraph and only uses Vietnamese."""
    
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