# Character LLM

Fine-tuned LLM để roleplay nhân vật X từ [game/anime/novel].

## Quickstart

```bash
git clone https://github.com/you/character-llm
cd character-llm
cp .env.example .env    # điền API keys
pip install -r requirements.txt
```

## Pipeline

Thiết lập các file sau cho project, bỏ trống các file py

## Project layout

- `data/`
  - `raw/` — Data thô scrape từ wiki
  - `processed/` — Đã chunk + clean
  - `training/` — Training pairs cuối cùng
- `scripts/` — Chuẩn bị dữ liệu và kiểm tra format
- `training/` — Fine-tune và đánh giá
- `inference/` — Chat và API wrapper
- `models/` — Gitignored model weights
- `notebooks/` — Thử nghiệm, khám phá dữ liệu
