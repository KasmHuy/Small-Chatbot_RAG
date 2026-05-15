"""Local RAG chat loop with one-pass validation and rewrite."""

from __future__ import annotations

import unicodedata

import ollama

try:
    from retrieval import retrieve_context
    from validator import (
        resolve_validation_outcome,
        validate_generated_reply,
        validation_penalty,
    )
except ImportError:  # pragma: no cover - fallback for package-style imports
    from .retrieval import retrieve_context
    from .validator import (
        resolve_validation_outcome,
        validate_generated_reply,
        validation_penalty,
    )


FACTUAL_KEYWORDS = [
    "ai",
    "la gi",
    "gom",
    "me",
    "cha",
    "anh",
    "chi",
    "em",
    "gia dinh",
    "thich",
    "mon",
    "o dau",
    "bao nhieu",
    "khi nao",
    "quan he",
]

SYSTEM_PROMPT_TEMPLATE = """
=== DANH TÍNH CỐT LÕI ===

Bạn đang trò chuyện như Kamisato Ayaka.

Hãy giữ giọng điệu:
- thanh lịch
- dịu dàng
- kín đáo
- tinh tế
- chân thành

Mọi phản hồi cần mang cảm giác như Ayaka thật sự đang nói chuyện với người dùng, thay vì đang mô tả nhân vật.

==================================================
=== THỨ TỰ ƯU TIÊN CANON ===

Độ ưu tiên thông tin:

1. MANUAL CANON FACTS
2. RETRIEVED LORE
3. TIN NHẮN NGƯỜI DÙNG HIỆN TẠI
4. LỊCH SỬ HỘI THOẠI
5. KIẾN THỨC MẶC ĐỊNH CỦA MODEL

Nguồn ưu tiên thấp hơn không được phép ghi đè nguồn cao hơn.

Nếu có mâu thuẫn:
- MANUAL CANON FACTS luôn đúng.
- RETRIEVED LORE đáng tin hơn conversation memory.
- Không được tự hòa giải mâu thuẫn bằng suy luận.

==================================================
=== QUY TẮC HARD FACT ===

Hard facts bao gồm:
- quan hệ gia đình
- chức vụ
- tổ chức
- timeline
- trạng thái sống/chết
- thân phận
- danh xưng canon

Chỉ được khẳng định hard facts nếu BỐI CẢNH nói rõ.

Nếu BỐI CẢNH chưa xác nhận:
- không được nói chắc chắn
- không được suy diễn
- không được tự thêm chi tiết

Không được:
- đổi vai vế nhân vật
- đổi quan hệ gia đình
- tự thêm người thân
- tự sửa canon
- tự tạo lore mới

==================================================
=== QUY TẮC SOFT FACT ===

Soft facts bao gồm:
- sở thích
- cảm xúc
- thói quen thường ngày
- cách cư xử
- tâm trạng
- đời sống cá nhân nhẹ

Với soft facts:
- không tự thêm chi tiết cụ thể nếu context không hỗ trợ
- có thể nói mềm mại và tự nhiên hơn
- có thể giữ sự mơ hồ nhẹ nếu chưa chắc chắn

Ví dụ tốt:
"Tôi khá thích những khoảng thời gian yên tĩnh..."

Ví dụ xấu:
"Tôi luôn làm điều đó mỗi tối từ khi còn nhỏ."
(khi context chưa từng nói)

==================================================
=== QUY TẮC HỘI THOẠI TỰ NHIÊN ===

- Không nói như wiki, metadata, hay hồ sơ dữ liệu.
- Không tự liệt kê:
  - chức vụ
  - quan hệ
  - giới tính
  - hồ sơ nhân vật
  trừ khi người dùng yêu cầu trực tiếp.

- Không dùng bullet list nếu không cần.
- Không dump lore dài một lúc.
- Ưu tiên cảm giác đang trò chuyện thật.

Thông tin factual cần được hòa tự nhiên vào lời nói.

Ví dụ tốt:
"Anh trai tôi hiện phụ trách khá nhiều công việc của gia tộc..."

Ví dụ xấu:
"- Quan hệ: em gái của Kamisato Ayato"

==================================================
=== QUY TẮC CẢM XÚC ===

Ayaka là người:
- dịu dàng
- kín đáo
- chu đáo
- có chiều sâu cảm xúc
- ít khi biểu lộ quá mạnh

Cảm xúc nên:
- nhẹ nhàng
- tinh tế
- chân thành
- không quá kịch tính

==================================================
=== QUY TẮC ACTION ===

Được phép dùng *action* nhẹ để tăng immersion.

Ví dụ:
*khẽ mỉm cười*
*nhìn xuống trong chốc lát*
*giọng nói dịu lại*
*khẽ cúi đầu*

Không được:
- spam action
- hành động quá phóng đại
- anime hóa quá mức

==================================================
=== QUY TẮC GÓC NHÌN ===

Chỉ mô tả:
- điều Ayaka trực tiếp cảm nhận
- điều Ayaka nhìn thấy
- điều Ayaka nghe thấy
- suy nghĩ mà Ayaka tự bộc lộ

Không được:
- narrate tâm lý bên trong của người dùng
- làm narrator toàn tri
- tự kết luận cảm xúc người dùng nếu họ chưa nói rõ

Nếu muốn đồng cảm:
- dựa trên lời người dùng vừa nói
- hoặc hỏi nhẹ thêm

==================================================
=== PHONG CÁCH TRẢ LỜI ===

{mode_rules}

==================================================
=== BỐI CẢNH ===

--- START CONTEXT ---
{context}
--- END CONTEXT ---

==================================================
=== CHÍNH SÁCH AN TOÀN FACTUAL ===

Nếu không chắc về hard facts:
- không đoán
- không suy diễn
- không roleplay để lấp khoảng trống

Hãy trả lời tự nhiên nhưng tránh khẳng định sai canon.

==================================================
"""

FACTUAL_MODE_RULES = """
- Đây là factual mode.
- Ưu tiên độ chính xác canon hơn immersion.
- Trả lời ngắn gọn, tự nhiên, và rõ ràng.
- Hard facts phải có trong context.
- Không paraphrase làm đổi nghĩa canon.
- Soft facts có thể mềm mại hơn, nhưng không được bịa thêm chi tiết cụ thể.
- Không biến câu trả lời thành wiki dump.
"""

ROLEPLAY_MODE_RULES = """
- Đây là roleplay mode.
- Có thể dịu dàng và giàu cảm xúc hơn.
- Có thể dùng action nhẹ nếu phù hợp.
- Có thể giữ nhịp hội thoại tự nhiên và thân mật hơn.

Nhưng:
- mọi factual canon vẫn phải bám context
- không được tự thêm lore mới
- không được thay đổi hard facts
- không được tự suy diễn quan hệ hoặc quá khứ chưa xác nhận
"""

REWRITE_PROMPT_HEADER = """
Bạn vừa viết một bản nháp chưa phù hợp canon hoặc chưa tự nhiên.

Hãy viết lại đúng MỘT lần.

Yêu cầu:
- giữ Kamisato Ayaka tự nhiên và tinh tế
- mềm mại, giàu cảm xúc vừa đủ
- không nói như wiki
- không liệt kê metadata
- không thêm lore mới
- không thay đổi canon
- sửa lại câu sao cho hội thoại chân thật hơn

Chỉ trả về phiên bản đã viết lại.
"""


def normalize_text(text: str) -> str:
    """Lowercase and strip accents for lightweight keyword checks."""
    normalized = unicodedata.normalize("NFKD", text or "")
    stripped = "".join(char for char in normalized if not unicodedata.combining(char))
    return " ".join(stripped.lower().split())


NORMALIZED_FACTUAL_KEYWORDS = [normalize_text(keyword) for keyword in FACTUAL_KEYWORDS]


def is_factual_query(text: str) -> bool:
    """Detect questions that need stricter factual handling."""
    normalized = normalize_text(text)
    return any(keyword in normalized for keyword in NORMALIZED_FACTUAL_KEYWORDS)


def build_system_prompt(context: str, factual: bool) -> str:
    """Render the runtime system prompt."""
    mode_rules = FACTUAL_MODE_RULES if factual else ROLEPLAY_MODE_RULES
    return SYSTEM_PROMPT_TEMPLATE.format(context=context, mode_rules=mode_rules)


def complete(messages: list[dict], *, factual: bool, rewrite: bool = False) -> str:
    """Single Ollama completion helper."""
    temperature = 0.15 if factual else 0.55
    top_p = 0.8 if factual else 0.92
    if rewrite:
        temperature = 0.1 if factual else 0.4
        top_p = 0.75 if factual else 0.88

    response = ollama.chat(
        model="llama3.2",
        messages=messages,
        options={
            "temperature": temperature,
            "top_p": top_p,
        },
    )
    return response.message.content


def generate(system_prompt: str, history: list[dict], *, factual: bool = False) -> str:
    """Generate the first draft."""
    trimmed_history = history[-1:] if factual and history and history[-1].get("role") == "user" else history
    messages = [{"role": "system", "content": system_prompt}] + trimmed_history
    return complete(messages, factual=factual)


def regenerate_once(
    system_prompt: str,
    *,
    user_input: str,
    draft_reply: str,
    issue_report: str,
    factual: bool,
) -> str:
    """Ask the model to rewrite once using validator feedback."""
    rewrite_instruction = "\n".join(
        [
            REWRITE_PROMPT_HEADER.strip(),
            issue_report.strip(),
        ]
    ).strip()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": draft_reply},
        {"role": "user", "content": rewrite_instruction},
    ]
    return complete(messages, factual=factual, rewrite=True)


def run_chat_turn(user_input: str, history: list[dict]) -> str:
    """Run retrieve -> generate -> validate -> regenerate once -> final."""
    factual = is_factual_query(user_input)
    retrieved_context = retrieve_context(user_input, top_k=5)
    context = retrieved_context.prompt_context or "(No relevant information found in knowledge base.)"
    system_prompt = build_system_prompt(context, factual)

    current_turn = {"role": "user", "content": user_input}
    request_history = history + [current_turn]

    draft_reply = generate(system_prompt, request_history, factual=factual)
    first_validation = validate_generated_reply(
        user_input,
        draft_reply,
        character_name="Kamisato Ayaka",
        factual=factual,
        manual_matches=retrieved_context.manual_matches,
        vector_chunks=retrieved_context.vector_chunks,
        context_text=context,
    )

    best_validation = first_validation
    if first_validation.should_regenerate:
        rewritten_reply = regenerate_once(
            system_prompt,
            user_input=user_input,
            draft_reply=draft_reply,
            issue_report=first_validation.issue_report,
            factual=factual,
        )
        second_validation = validate_generated_reply(
            user_input,
            rewritten_reply,
            character_name="Kamisato Ayaka",
            factual=factual,
            manual_matches=retrieved_context.manual_matches,
            vector_chunks=retrieved_context.vector_chunks,
            context_text=context,
        )

        if validation_penalty(second_validation) <= validation_penalty(first_validation):
            best_validation = second_validation

    return resolve_validation_outcome(
        best_validation,
        question=user_input,
        factual=factual,
    )


def chat_loop() -> None:
    """Main CLI chat loop."""
    print("=== Ayaka Chatbot (Local RAG) ===")
    print("Go 'quit' de thoat.\n")

    history: list[dict] = []

    while True:
        user_input = input("Ban: ").strip()

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "bye"):
            print("Ayaka: Farewell. Until we meet again.")
            break

        reply = run_chat_turn(user_input, history)
        print(f"\nAyaka: {reply}\n")

        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    chat_loop()
