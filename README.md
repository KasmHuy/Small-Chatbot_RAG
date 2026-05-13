# RAG-Chatbot_LLM_classic (Character LLM + RAG)

Project tạo chatbot roleplay theo kiểu **Character LLM** kết hợp **RAG** (retrieval từ vector DB) để cung cấp ngữ cảnh trước khi sinh câu trả lời.

Repo gồm 2 phần chính:

1) **Pipeline dữ liệu** (scripts):
- Scrape nội dung wiki (MediaWiki API)
- Clean & chuẩn hóa text
- Chunk thành các đoạn phục vụ embedding
- (Tuỳ chọn) Generate training pairs

2) **Inference / RAG** (inference):
- Embed câu hỏi + truy xuất chunk liên quan từ ChromaDB
- Gọi LLM (hiện dùng Gemini API) để generate câu trả lời theo persona
- Có FastAPI wrapper (hiện là stub)

---

## Project layout

- `character-llm/inference/`
  - `retrieval.py`: embed + Chroma persistent + retrieve chunks (dùng các đường dẫn hard-code)
  - `chat.py`: CLI chat loop + gọi Gemini với context từ retrieval
  - `api.py`: FastAPI wrapper (stub)

- `character-llm/scripts/`
  - `scraper.py`: scrape wiki → `document.json` dạng có `sections/entries`
  - `cleaner.py`: clean `document.json`
  - `chunker.py`: chunk → `processed/chunks.json`
  - `generate_pairs.py`: tạo training pairs (JSONL)

- `character-llm/data/`
  - `processed/chunks.json`**retrieval dùng trực tiếp**
  - `vectordb/`**Chroma persistent index**
  - `training/` (train/eval JSONL)

---

## Cài đặt

```bash
pip install -r character-llm/requirements.txt
```

---

## Cấu hình môi trường (.env)

Tạo file **`.env` ở root**: `d:/Small-Chatbot_RAG/.env`.

Code hiện đang load bằng đường dẫn tuyệt đối, nên để đúng vị trí là quan trọng.

Ví dụ:
```env
GEMINI_API_KEY=YOUR_KEY
CHARACTER_NAME=Kamisato Ayaka
```

---

## Quan trọng: đường dẫn hard-code trong code hiện tại

`character-llm/inference/retrieval.py` và `character-llm/inference/chat.py` đang dùng đường dẫn tuyệt đối dạng:
- `D:\Small-Chatbot_RAG\character-llm\data\...`

Vì vậy:
- Repo nên nằm tại **`D:\Small-Chatbot_RAG\...`** như đang setup.
- Nếu bạn đổi ổ/đổi folder, retrieval/chat có thể không tìm thấy data.

---

## Dataset cần có để chạy RAG

Tối thiểu cần:
1. `character-llm/data/processed/chunks.json`
2. `character-llm/data/vectordb/` (Chroma persistent)

Nếu bạn vừa clone mới hoặc chưa có `vectordb/`:
- Hãy chạy bước build index ở dưới.

---

## Chạy nhanh

### 1) Build / Embed index cho Chroma

Chạy:
```bash
python character-llm/inference/retrieval.py
```

Script sẽ embed các chunks trong `character-llm/data/processed/chunks.json` và lưu vào `character-llm/data/vectordb/`.

> Lần chạy đầu có thể chậm (phụ thuộc số chunks và tốc độ API embedding).

---

### 2) Chat (CLI)

Chạy:
```bash
python character-llm/inference/chat.py
```

- Nhập câu hỏi ở prompt
- Gõ `quit` để thoát

> Lưu ý: `chat.py` có `time.sleep(12)` để giảm nguy cơ rate limit.

---

### 3) API (FastAPI)

Hiện tại `character-llm/inference/api.py` là **stub**.

Chạy:
```bash
python -m character-llm.inference.api
```

Endpoint:
- `POST /chat`
- Body: `{ "prompt": "..." }`

---

### 4) Test nhanh `test_api.py`

Chạy:
```bash
python character-llm/test_api.py
```

Script này test trực tiếp Gemini `generateContent` bằng key từ `.env`.

---

## (Tuỳ chọn) Build lại dữ liệu theo pipeline

### 1) Scrape
```bash
python character-llm/scripts/scraper.py "URL_PAGE" --character-name "Kamisato Ayaka"
```
Mặc định output: `../data/raw/document.json`.

### 2) Clean
```bash
python character-llm/scripts/cleaner.py
```
Mặc định output: `../data/processed/document_clean.json`.

### 3) Chunk
```bash
python character-llm/scripts/chunker.py
```
Mặc định output: `../data/processed/chunks.json`.

---

## Ghi chú vận hành

- Nếu bạn thay đổi `processed/chunks.json`, nên chạy lại `retrieval.py` để rebuild `vectordb/`.
- Vector DB có thể khá nặng tùy số lượng chunks.

---

## Quick checklist

- [ ] Đã tạo `d:/Small-Chatbot_RAG/.env`
- [ ] Có `character-llm/data/processed/chunks.json`
- [ ] Có `character-llm/data/vectordb/`
- [ ] Chạy `python character-llm/inference/retrieval.py` nếu cần build index
- [ ] Chạy `python character-llm/inference/chat.py` để chat

