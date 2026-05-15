# RAG-Chatbot_LLM_classic

Project chatbot roleplay theo kieu Character LLM + RAG. Sau khi don lai cau truc, repo chi dung mot nguon cau hinh va mot nguon du lieu chung o root de tranh trung `env`, `data` va cac file utility.

## Cau truc hien tai

```text
Small-Chatbot_RAG/
|- character-llm/
|  |- inference/
|  |- scripts/
|  `- training/
|- data/
|  |- manual_facts/
|  |- processed/
|  |- training/
|  `- vectordb/
|- docs/
|- notebooks/
|- tools/
|- .env
|- README.md
`- requirements.txt
```

## Quy uoc moi

- Chi dung mot file `.env` o root: `D:\\Small-Chatbot_RAG\\.env`
- Chi dung mot thu muc du lieu o root: `D:\\Small-Chatbot_RAG\\data\\...`
- `docs/` chua tai lieu mo ta va file `.docx`
- `tools/` chua script phu tro nhu test API hoac generate tai lieu
- `archive/legacy-data/root-vectordb-premerge/` giu lai ban `vectordb` cu o root truoc khi hop nhat

## Cai dat

```bash
pip install -r requirements.txt
```

## Dataset can co de chay RAG

Toi thieu can:

1. `data/processed/chunks.json`
2. `data/vectordb/`

Neu chua co `vectordb/`, hay chay buoc build index ben duoi.

## Chay nhanh

### 1) Build / embed index cho Chroma

```bash
python character-llm/inference/retrieval.py
```

Script se doc `data/processed/chunks.json` va luu persistent index vao `data/vectordb/`.

### 2) Chat CLI

```bash
python character-llm/inference/chat.py
```

`chat.py` hien goi Ollama voi context tu retrieval.

### 3) API stub

```bash
python character-llm/inference/api.py
```

Endpoint hien co:

- `POST /chat`
- Body: `{ "prompt": "..." }`

### 4) Test nhanh Gemini key

```bash
python tools/test_api.py
```

Script nay doc key tu root `.env` roi goi truc tiep Gemini `generateContent`.

## Pipeline du lieu

### 1) Scrape

```bash
python character-llm/scripts/scraper.py "URL_PAGE" --character-name "Kamisato Ayaka"
```

Mac dinh output: `data/raw/document.json`

### 2) Clean

```bash
python character-llm/scripts/cleaner.py
```

Mac dinh output: `data/processed/document_clean.json`

### 3) Chunk

```bash
python character-llm/scripts/chunker.py
```

Mac dinh output: `data/processed/chunks.json`

## Ghi chu van hanh

- Neu thay doi `data/processed/chunks.json`, nen chay lai `character-llm/inference/retrieval.py` de rebuild `data/vectordb/`
- Notebook thu nghiem hien nam o `notebooks/exploration.ipynb`
- Tai lieu tom tat nam o `docs/`

## Checklist

- [ ] Co `data/processed/chunks.json`
- [ ] Co `data/vectordb/`
- [ ] Da dien root `.env`
- [ ] Chay `python character-llm/inference/retrieval.py` neu can build index
- [ ] Chay `python character-llm/inference/chat.py` de chat
