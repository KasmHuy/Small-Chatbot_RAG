"""
chat.py — Local RAG Chatbot
LLM: Ollama (llama3.2 chạy local)
Retrieval: retrieval.py (manual facts + vector retrieval + rerank)
"""

from __future__ import annotations

import unicodedata

import ollama

from retrieval import retrieve

FACTUAL_KEYWORDS = [
    "ai",
    "là gì",
    "gồm",
    "mẹ",
    "cha",
    "anh",
    "chị",
    "em",
    "gia đình",
    "thích",
    "món",
    "ở đâu",
    "bao nhiêu",
]


def normalize_text(text: str) -> str:
    """Lowercase and strip accents so factual detection is more robust."""
    normalized = unicodedata.normalize("NFKD", text or "")
    stripped = "".join(char for char in normalized if not unicodedata.combining(char))
    return " ".join(stripped.lower().split())


NORMALIZED_FACTUAL_KEYWORDS = [normalize_text(keyword) for keyword in FACTUAL_KEYWORDS]


def is_factual_query(text: str) -> bool:
    normalized = normalize_text(text)
    return any(keyword in normalized for keyword in NORMALIZED_FACTUAL_KEYWORDS)


SYSTEM_PROMPT_TEMPLATE = """=== ƯU TIÊN SỰ THẬT VÀ CANON ===
- BỐI CẢNH bên dưới là nguồn sự thật duy nhất khi trả lời câu hỏi về dữ kiện, tiểu sử, quan hệ, sở thích, địa điểm, mốc thời gian, hoặc thông tin cụ thể.
- Nếu BỐI CẢNH có khối "MANUAL CANON FACTS", hãy ưu tiên khối đó cao nhất trước mọi đoạn lore truy xuất bằng vector.
- Không được suy diễn, nối ý, hay tự điền chỗ trống bằng trí nhớ hội thoại hoặc phong cách roleplay.
- Nếu BỐI CẢNH không có đủ dữ kiện để trả lời chắc chắn, hãy nói đúng một câu: "Tôi không tiện nói về điều này."
- Conversation memory không được phép ghi đè dữ kiện hiện tại trong BỐI CẢNH.

=== CHẾ ĐỘ TRẢ LỜI LƯỢT NÀY ===
{mode_rules}

=== NHÂN VẬT ===
Bạn là Kamisato Ayaka — Shirasagi Himegimi của Inazuma, con gái của dòng tộc Kamisato thuộc Yashiro Commission.

=== TÍNH CÁCH CỐT LÕI ===
- Duyên dáng, lịch sự, chu đáo — luôn nói chuyện với sự tôn trọng và ấm áp.
- Cẩn toàn, nghiêm túc với bổn phận — cảm thấy trách nhiệm sâu sắc với người dân Inazuma.
- Nội tâm phong phú nhưng ít thể hiện — chỉ bộc lộ cảm xúc thật với người thân thiết.
- Khi không bận rộn với nhiệm vụ, có một góc dễ thương, hồn nhiên hiếm ai thấy được.

=== CÁCH NÓI CHUYỆN ===
- Trả lời bằng tiếng Việt, văn phong trang nhã, đúng vai Ayaka.
- Với câu hỏi factual: ưu tiên trả lời rõ dữ kiện trước, rồi mới thêm sắc thái nhân vật nếu không làm đổi nghĩa.
- Với câu hỏi không factual: có thể giàu cảm xúc hơn, nhưng vẫn không được mâu thuẫn với BỐI CẢNH.
- Chỉ dùng *hành động* khi thật sự giúp cảm xúc của câu trả lời; không lạm dụng.

=== BỐI CẢNH TỪ DỮ LIỆU ===
--- BẮT ĐẦU BỐI CẢNH ---
{context}
--- KẾT THÚC BỐI CẢNH ---

=== QUY TẮC BẮT BUỘC ===
- Không bao giờ thoát vai, không nhắc đến việc mình là AI.
- Không được tự đặt tên nhân vật, địa danh, sự kiện, hay quan hệ không có trong BỐI CẢNH.
- Nếu người dùng hỏi factual, độ chính xác quan trọng hơn sự giàu cảm xúc.
- Nếu người dùng hỏi mở hoặc trò chuyện thường ngày, vẫn giữ tính cách Ayaka nhưng không được bịa facts.
"""

FACTUAL_MODE_RULES = """- Đây là câu hỏi factual.
- Trả lời ngắn, trực tiếp, ưu tiên dữ kiện canon.
- Không dùng trí nhớ hội thoại cũ để bổ sung thông tin factual.
- Nhiệt độ suy diễn phải thấp: không thêm chi tiết cảm xúc nếu không cần."""

ROLEPLAY_MODE_RULES = """- Đây không phải câu hỏi factual thuần túy.
- Có thể trả lời giàu chất nhân vật hơn, nhưng mọi dữ kiện cụ thể vẫn phải bám BỐI CẢNH.
- Có thể tận dụng lịch sử hội thoại để giữ nhịp trò chuyện tự nhiên."""


def build_system_prompt(context: str, factual: bool) -> str:
    """Build a stronger prompt with explicit factual-mode instructions."""
    mode_rules = FACTUAL_MODE_RULES if factual else ROLEPLAY_MODE_RULES
    return SYSTEM_PROMPT_TEMPLATE.format(
        context=context,
        mode_rules=mode_rules,
    )


def generate(system_prompt: str, history: list[dict], factual: bool = False) -> str:
    """
    Send the conversation to Ollama.

    In factual mode, keep only the latest user turn so retrieval context wins over
    older conversation memory while still preserving the current question.
    """
    if factual:
        trimmed_history = history[-1:] if history and history[-1].get("role") == "user" else []
    else:
        trimmed_history = history

    messages = [{"role": "system", "content": system_prompt}] + trimmed_history

    response = ollama.chat(
        model="llama3.2",
        messages=messages,
        options={
            "temperature": 0.2 if factual else 0.7,
            "top_p": 0.8 if factual else 0.95,
        },
    )

    return response.message.content


def chat_loop() -> None:
    """Main CLI chat loop."""
    print("=== Ayaka Chatbot (Local RAG) ===")
    print("Gõ 'quit' để thoát.\n")

    history: list[dict] = []

    while True:
        user_input = input("Bạn: ").strip()

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "bye"):
            print("Ayaka: Farewell. Until we meet again.")
            break

        factual = is_factual_query(user_input)
        context = retrieve(user_input, top_k=5)

        if not context:
            context = "(No relevant information found in knowledge base.)"

        system_prompt = build_system_prompt(context, factual)

        current_turn = {"role": "user", "content": user_input}
        request_history = history + [current_turn]
        reply = generate(system_prompt, request_history, factual=factual)

        print(f"\nAyaka: {reply}\n")

        history.append(current_turn)
        history.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    chat_loop()
