from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent
OUTPUT_PATH = ROOT / "Giai_thich_code_thiet_lap_project.docx"


def build_content() -> list[tuple[str, str]]:
    today = datetime.now().strftime("%d/%m/%Y")
    return [
        ("Title", "Giải Thích Code Thiết Lập Project Small-Chatbot_RAG"),
        ("Normal", f"Ngày tạo tài liệu: {today}"),
        (
            "Normal",
            "Phạm vi: tài liệu này giải thích toàn bộ phần code và file cấu hình hiện có trong repo, tập trung vào các thành phần dùng để thiết lập pipeline dữ liệu, huấn luyện và suy luận của project.",
        ),
        ("Heading1", "1. Bức tranh tổng thể"),
        (
            "Normal",
            "Repo gốc `Small-Chatbot_RAG` hiện khá nhỏ. Phần thực sự chứa logic nằm trong thư mục `character-llm`. Nhìn theo ý tưởng kiến trúc, project này muốn xây một chatbot nhập vai nhân vật theo pipeline: scrape thông tin nhân vật từ wiki, chia nhỏ văn bản, tạo cặp dữ liệu train, fine-tune mô hình, sau đó phục vụ qua giao diện chat hoặc FastAPI.",
        ),
        (
            "Normal",
            "Điểm quan trọng là code hiện tại mới ở mức scaffold hoặc prototype. Nghĩa là cấu trúc thư mục và ý tưởng luồng xử lý đã có, nhưng nhiều bước vẫn đang là placeholder, chưa thực sự fine-tune mô hình hoặc gọi LLM thật.",
        ),
        ("Heading1", "2. Cấu trúc thư mục và vai trò"),
        (
            "Normal",
            "`README.md` ở thư mục gốc: mô tả repo ở mức rất ngắn, chỉ nói đây là một chatbot nhỏ có hệ thống RAG.",
        ),
        (
            "Normal",
            "`character-llm/README.md`: README chính của project con. File này mô tả quickstart, pipeline dự kiến và layout thư mục.",
        ),
        (
            "Normal",
            "`character-llm/.env.example`: mẫu biến môi trường để người dùng điền API key, tên model nền và tên nhân vật.",
        ),
        (
            "Normal",
            "`character-llm/.gitignore`: quy định những thứ không nên commit như secrets, model weights, dữ liệu thô, cache và log.",
        ),
        (
            "Normal",
            "`character-llm/requirements.txt`: danh sách dependency cho scrape dữ liệu, xử lý dữ liệu, fine-tune và phục vụ API.",
        ),
        (
            "Normal",
            "`character-llm/data/`: nơi chứa dữ liệu theo từng giai đoạn của pipeline. `raw/` là dữ liệu thô, `processed/` là dữ liệu đã chunk, `training/` là dữ liệu huấn luyện cuối cùng.",
        ),
        (
            "Normal",
            "`character-llm/scripts/`: các script chuẩn bị dữ liệu gồm scrape, chunk, tạo training pairs và validate JSONL.",
        ),
        (
            "Normal",
            "`character-llm/training/`: phần huấn luyện và đánh giá mô hình.",
        ),
        (
            "Normal",
            "`character-llm/inference/`: phần suy luận, gồm một hàm chat đơn giản và một API FastAPI.",
        ),
        (
            "Normal",
            "`character-llm/models/`: thư mục để chứa model đã fine-tune. Trong repo mới chỉ có `.gitkeep` để giữ thư mục.",
        ),
        (
            "Normal",
            "`character-llm/notebooks/exploration.ipynb`: notebook thử nghiệm. Hiện chỉ có 1 cell markdown giới thiệu, chưa có code phân tích dữ liệu.",
        ),
        ("Heading1", "3. Giải thích các file thiết lập mức project"),
        ("Heading2", "3.1 `README.md` ở thư mục gốc"),
        (
            "Normal",
            "File gốc chỉ chứa tiêu đề `Small-Chatbot_RAG` và một dòng mô tả ngắn. Nó có vai trò như nhãn của repo, chứ chưa hướng dẫn cách chạy hoặc giải thích kiến trúc.",
        ),
        ("Heading2", "3.2 `character-llm/README.md`"),
        (
            "Normal",
            "README này mô tả đúng tinh thần của dự án: một LLM được fine-tune để roleplay một nhân vật cụ thể. Phần Quickstart yêu cầu clone repo, vào thư mục project, copy `.env.example` thành `.env`, rồi cài dependency bằng `pip install -r requirements.txt`.",
        ),
        (
            "Normal",
            "README cũng mô tả layout thư mục theo ba tầng dữ liệu: `raw`, `processed`, `training`; sau đó là `scripts`, `training`, `inference`, `models`, `notebooks`. Đây là một cấu trúc hợp lý cho project NLP nhỏ vì mỗi giai đoạn dữ liệu được tách biệt rõ.",
        ),
        (
            "Normal",
            "Có một câu ghi kiểu 'thiết lập các file sau cho project, bỏ trống các file py'. Điều này cho thấy repo ban đầu được dựng như một khung sườn trước, rồi các file Python mới được điền dần.",
        ),
        ("Heading2", "3.3 `.env.example`"),
        (
            "Normal",
            "File mẫu môi trường khai báo 5 biến: `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `HF_TOKEN`, `BASE_MODEL`, `CHARACTER_NAME`.",
        ),
        (
            "Normal",
            "`ANTHROPIC_API_KEY` và `GEMINI_API_KEY` gợi ý rằng tác giả định dùng API của Anthropic hoặc Gemini để sinh dữ liệu huấn luyện hoặc làm bước hỗ trợ nào đó. `HF_TOKEN` dùng cho Hugging Face nếu cần tải model, tokenizer hoặc push checkpoint. `BASE_MODEL` là model nền dự định fine-tune. `CHARACTER_NAME` là tên nhân vật cần roleplay.",
        ),
        (
            "Normal",
            "Tuy nhiên ở trạng thái hiện tại, `.env` chưa thật sự được nạp tự động trong code. Repo không có `python-dotenv`, và các script cũng không gọi hàm load `.env`. Điều đó có nghĩa là việc copy `.env.example` thành `.env` mới chỉ là bước chuẩn bị; bản thân code hiện tại chưa tận dụng đầy đủ file `.env` này.",
        ),
        ("Heading2", "3.4 `.gitignore`"),
        (
            "Normal",
            "`.gitignore` loại bỏ các nhóm dữ liệu hợp lý cho dự án ML: secrets (`.env`, `*.key`), model weights (`models/`, `*.bin`, `*.safetensors`, `*.pt`, `*.ckpt`), dữ liệu thô (`data/raw/`), cache Python (`__pycache__`, `*.pyc`, `.venv/`), checkpoint notebook và log huấn luyện (`wandb/`, `runs/`).",
        ),
        (
            "Normal",
            "Về mặt thiết lập repo, file này rất quan trọng vì nó ngăn việc commit dữ liệu nhạy cảm hoặc file nặng lên Git. Với project LLM, đây là thói quen gần như bắt buộc.",
        ),
        ("Heading1", "4. Phân tích dependency trong `requirements.txt`"),
        (
            "Normal",
            "Danh sách thư viện chia thành nhiều nhóm chức năng. `requests` và `beautifulsoup4` phục vụ scrape nội dung HTML. `pandas` và `tqdm` dành cho xử lý hoặc theo dõi dữ liệu, dù trong code hiện chưa dùng tới. `anthropic` và `google-genai` được chuẩn bị cho khả năng gọi model bên ngoài.",
        ),
        (
            "Normal",
            "`torch`, `transformers`, `peft`, `trl`, `datasets` là bộ thư viện quen thuộc cho fine-tune LLM bằng Hugging Face và PEFT/LoRA. `fastapi` và `uvicorn` là cặp thư viện cho phục vụ API suy luận.",
        ),
        (
            "Normal",
            "Có hai điểm kỹ thuật cần ghi chú. Thứ nhất, `train.py` import `yaml`, nhưng `requirements.txt` lại không có `PyYAML`. Nếu dựng môi trường mới hoàn toàn, script train có thể lỗi `ModuleNotFoundError` cho `yaml`. Thứ hai, repo hiện cũng không có `python-dotenv`, nên `.env` không được nạp tự động.",
        ),
        ("Heading1", "5. Dữ liệu hiện có trong project"),
        (
            "Normal",
            "Trạng thái dữ liệu hiện tại cho thấy pipeline mới chỉ được dựng khung. `data/raw/character_wiki.txt` đang rỗng. `data/processed/chunks.json` hiện chỉ chứa `[]`. `data/training/train.jsonl` và `eval.jsonl` cũng đang rỗng.",
        ),
        (
            "Normal",
            "Điều này rất đáng chú ý khi giải thích project: repo đã có đầy đủ nơi đặt dữ liệu, nhưng gần như chưa có dữ liệu thật để train hoặc đánh giá. Nói cách khác, phần setup thư mục đã xong, còn phần nội dung dữ liệu chưa được lấp đầy.",
        ),
        ("Heading1", "6. Giải thích từng script trong `scripts/`"),
        ("Heading2", "6.1 `scripts/scraper.py`"),
        (
            "Normal",
            "Đây là điểm bắt đầu của pipeline dữ liệu. Ý tưởng rất đơn giản: nhận URL của trang wiki về nhân vật, tải HTML bằng `requests`, parse HTML bằng `BeautifulSoup`, lấy toàn bộ text bên trong các thẻ `<p>`, rồi ghép các đoạn văn thành một chuỗi lớn.",
        ),
        (
            "Normal",
            "Hàm `scrape_character_wiki(url: str) -> str` làm ba việc: gửi HTTP GET với `timeout=15`, gọi `raise_for_status()` để lỗi HTTP không bị nuốt, sau đó parse `response.text` và lấy `p.get_text(strip=True)` cho mọi thẻ đoạn văn. Kết quả cuối cùng được ghép bằng hai dấu xuống dòng để giữ cảm giác tách đoạn.",
        ),
        (
            "Normal",
            "Hàm `save_raw_text(output_path: str, text: str)` chỉ có nhiệm vụ ghi văn bản ra file với mã hóa UTF-8. Việc tách riêng hàm lưu file khỏi hàm scrape là một thiết kế tốt vì dễ test và dễ tái sử dụng.",
        ),
        (
            "Normal",
            "Khối `if __name__ == \"__main__\":` dùng `argparse` để biến file này thành script dòng lệnh. Script nhận `url` và `output`. Ý đồ là nếu người dùng không chỉ định output thì sẽ dùng `../data/raw/character_wiki.txt`.",
        ),
        (
            "Normal",
            "Nhưng có một chi tiết quan trọng: `output` đang được khai báo là positional argument, không phải optional argument. Trong `argparse`, positional argument vẫn bắt buộc dù có `default`, trừ khi khai báo thêm `nargs=\"?\"`. Nói cách khác, phần default ở đây gần như không phát huy tác dụng theo cách README gợi ý.",
        ),
        (
            "Normal",
            "Về chất lượng dữ liệu, script này mới là bản đơn giản. Nó không lọc quảng cáo, box điều hướng, nội dung trùng, footnote hoặc phần không liên quan. Nó cũng không có retry hay giới hạn tốc độ. Tuy vậy, với vai trò code thiết lập, file này dựng đúng điểm đầu vào của pipeline.",
        ),
        ("Heading2", "6.2 `scripts/chunker.py`"),
        (
            "Normal",
            "Sau khi có một văn bản dài, bước tiếp theo là chia nhỏ ra để thuận tiện cho embedding, retrieval hoặc tạo cặp train. Script `chunker.py` đảm nhiệm đúng vai trò đó.",
        ),
        (
            "Normal",
            "Hàm `chunk_text(text, chunk_size=1000, overlap=200)` tách text theo khoảng trắng bằng `text.split()`, rồi trượt một cửa sổ trên danh sách từ. Mỗi chunk gồm tối đa 1000 từ, và chunk sau lùi lại 200 từ để giữ overlap. Cách làm này giúp thông tin nằm ở ranh giới hai chunk không bị mất hoàn toàn.",
        ),
        (
            "Normal",
            "Hàm `load_raw_text(path)` đọc file input bằng `Path(path).read_text(encoding=\"utf-8\")`. Hàm `save_chunks(chunks, path)` ghi danh sách chunk thành JSON có `ensure_ascii=False` và `indent=2`, nhờ đó file đầu ra vừa giữ tiếng Việt đẹp vừa dễ đọc bằng mắt.",
        ),
        (
            "Normal",
            "Phần CLI của script cho phép truyền `input`, `output`, `--chunk-size`, `--overlap`. Giống `scraper.py`, `input` và `output` đang là positional arguments, nên default được ghi trong code không khiến chúng trở thành tùy chọn thực sự.",
        ),
        (
            "Normal",
            "Thiết kế chunk theo từ là hợp lý cho prototype, nhưng chưa bảo toàn cấu trúc ngữ nghĩa như đoạn văn, mục lục hay heading. Vì vậy nếu sau này muốn dùng cho retrieval nghiêm túc, có thể cần chunk theo token hoặc theo đoạn văn.",
        ),
        ("Heading2", "6.3 `scripts/generate_pairs.py`"),
        (
            "Normal",
            "Đây là file quan trọng nhất trong khâu chuẩn bị training data, vì nó chịu trách nhiệm biến từng chunk kiến thức thành cặp `input`/`output` để fine-tune.",
        ),
        (
            "Normal",
            "Hàm `generate_prompt_for_chunk(chunk, character_name)` tạo ra một prompt tiếng Anh dạng: 'Generate a conversation snippet where {character_name} explains the following information: {chunk}'. Ý tưởng là dùng một mô hình khác viết hộ một đoạn hội thoại mang phong cách của nhân vật.",
        ),
        (
            "Normal",
            "Hàm `generate_training_pairs(chunks, character_name)` lặp qua từng chunk, tạo prompt tương ứng và trả về danh sách dict với hai khóa `input` và `output`.",
        ),
        (
            "Normal",
            "Tuy nhiên, phần `output` hiện vẫn chỉ là chuỗi cố định `<MODEL_RESPONSE>`. Nghĩa là script chưa gọi API Anthropic, Gemini hay bất kỳ model nào để sinh câu trả lời thật. File này mới dựng khung dữ liệu, chưa tạo được dữ liệu huấn luyện hữu ích.",
        ),
        (
            "Normal",
            "Có hai lỗi kỹ thuật rõ ràng trong file này. Lỗi thứ nhất: `load_chunks()` và `save_jsonl()` đều dùng `json`, nhưng `json` chỉ được import bên trong khối `__main__`. Nếu import module này rồi gọi các hàm helper từ nơi khác, code sẽ gặp `NameError: name 'json' is not defined`.",
        ),
        (
            "Normal",
            "Lỗi thứ hai nghiêm trọng hơn ở phần CLI. Script khai báo positional arguments tên `train-output` và `eval-output`. `argparse` sẽ tạo thuộc tính tên có dấu gạch ngang, trong khi code lại truy cập `args.train_output` và `args.eval_output`. Khi chạy thực tế, script vỡ với `AttributeError: 'Namespace' object has no attribute 'train_output'`.",
        ),
        (
            "Normal",
            "Ngoài ra, cách tách `eval` hiện tại chỉ đơn giản lấy 10 phần trăm đầu của danh sách `pairs` bằng `pairs[: max(1, len(pairs) // 10)]`. Danh sách không được shuffle, không có random seed, nên tập đánh giá có thể không đại diện nếu dữ liệu gốc có thứ tự chủ đề.",
        ),
        (
            "Normal",
            "Về mặt thiết lập, `generate_pairs.py` thể hiện đúng ý tưởng của bước chuyển từ knowledge chunks sang supervised fine-tuning data. Nhưng ở hiện trạng hiện nay, nó vẫn là một bản mock-up hơn là pipeline sinh dữ liệu hoàn chỉnh.",
        ),
        ("Heading2", "6.4 `scripts/validate_data.py`"),
        (
            "Normal",
            "Script này làm nhiệm vụ kiểm tra cấu trúc JSONL trước khi train. Hàm `validate_jsonl(path)` kiểm tra file có tồn tại hay không, sau đó đọc từng dòng, bỏ qua dòng trống, parse JSON và xác nhận mỗi record là dict có đủ hai trường `input` và `output`.",
        ),
        (
            "Normal",
            "Điểm hay là lỗi được báo kèm số dòng, giúp người dùng sửa nhanh khi có record hỏng. Đây là một bước vệ sinh dữ liệu rất hợp lý trước khi đem vào trainer.",
        ),
        (
            "Normal",
            "Tuy nhiên script chỉ kiểm tra cú pháp và schema tối thiểu. Nó không kiểm tra độ dài, nội dung rỗng, duplicate hay chất lượng câu trả lời. Một chi tiết nữa là file JSONL rỗng vẫn được xem là hợp lệ; khi mình chạy thử trên `train.jsonl` rỗng, script báo `Validation passed: True`.",
        ),
        ("Heading1", "7. Phần huấn luyện trong `training/`"),
        ("Heading2", "7.1 `training/config.yaml`"),
        (
            "Normal",
            "File YAML này định nghĩa các tham số huấn luyện: `model_name`, `learning_rate`, `batch_size`, `epochs`, `max_seq_length`, `warmup_steps`, `evaluation_steps`, `save_steps`, `output_dir`.",
        ),
        (
            "Normal",
            "`output_dir` trỏ tới `../models/character-model`, phù hợp với cấu trúc repo. `batch_size`, `epochs`, `warmup_steps`, `evaluation_steps`, `save_steps` là các tham số quen thuộc khi fine-tune model transformer.",
        ),
        (
            "Normal",
            "Có hai điểm đáng chú ý. Thứ nhất, `model_name: ${BASE_MODEL}` chỉ là một chuỗi literal trong YAML. `yaml.safe_load()` không tự thay `${BASE_MODEL}` bằng biến môi trường, nên nếu không có bước nội suy bổ sung, giá trị nhận được vẫn là đúng chuỗi `${BASE_MODEL}`.",
        ),
        (
            "Normal",
            "Thứ hai, trong môi trường hiện tại `yaml.safe_load()` đọc `learning_rate: 2e-5` thành chuỗi `'2e-5'`, không phải float. Nếu sau này truyền thẳng vào optimizer hoặc training arguments, code sẽ phải ép kiểu hoặc viết lại giá trị theo dạng chắc chắn parse thành số như `2.0e-5`.",
        ),
        ("Heading2", "7.2 `training/train.py`"),
        (
            "Normal",
            "File `train.py` là entrypoint cho huấn luyện. Hàm `load_config(path='config.yaml')` mở file YAML và trả về dict bằng `yaml.safe_load`. Hàm `train()` gọi `load_config('config.yaml')`, in cấu hình đã nạp, rồi in tiếp chuỗi `Starting training loop... (placeholder)`.",
        ),
        (
            "Normal",
            "Điều này cho thấy phần train thật chưa được viết. Hiện chưa có các thành phần quan trọng như nạp dataset JSONL, load tokenizer/model, cấu hình PEFT/LoRA, collator, trainer, logging, checkpoint hay evaluation loop.",
        ),
        (
            "Normal",
            "Một chi tiết vận hành rất quan trọng là `config.yaml` được mở bằng đường dẫn tương đối theo thư mục chạy hiện tại, không phải theo vị trí file script. Khi chạy `python character-llm/training/train.py` từ thư mục gốc repo, script lỗi `FileNotFoundError` vì nó tìm `config.yaml` ở sai nơi. Script chỉ chạy được nếu `cwd` đang là `character-llm/training` hoặc nếu người dùng tự sửa đường dẫn.",
        ),
        (
            "Normal",
            "Tóm lại, `train.py` hiện đóng vai trò chứng minh điểm móc vào pipeline nhiều hơn là thực hiện huấn luyện thật.",
        ),
        ("Heading2", "7.3 `training/evaluate.py`"),
        (
            "Normal",
            "File đánh giá còn đơn giản hơn. Hàm `evaluate(model_path='../models/character-model')` chỉ in thông báo đang đánh giá model ở path nào đó, rồi kết thúc. Không có metric, không có tập dữ liệu đánh giá, cũng không có logic sinh đáp án.",
        ),
        (
            "Normal",
            "Dù vậy, file này cho thấy tác giả đã tách riêng khái niệm `train` và `evaluate`, nghĩa là về mặt kiến trúc đã nghĩ đến vòng đời chuẩn của mô hình.",
        ),
        ("Heading1", "8. Phần suy luận trong `inference/`"),
        ("Heading2", "8.1 `inference/chat.py`"),
        (
            "Normal",
            "File này là giao diện chat đơn giản nhất. Hàm `chat(prompt: str) -> str` chỉ trả về chuỗi giả lập `[stub response] Character replies to: {prompt}`. Nếu chạy như script, nó nhận một prompt từ dòng lệnh và in kết quả.",
        ),
        (
            "Normal",
            "Vai trò của file là tạo một API nội bộ thật nhỏ để sau này thay logic stub bằng việc load model và generate text. Đây là một cách tách lớp hợp lý: nơi khác có thể gọi hàm `chat()` mà không cần biết chi tiết mô hình.",
        ),
        ("Heading2", "8.2 `inference/api.py`"),
        (
            "Normal",
            "File `api.py` dùng FastAPI để dựng HTTP endpoint. `app = FastAPI()` khởi tạo ứng dụng. Hai lớp Pydantic `ChatRequest` và `ChatResponse` định nghĩa schema request và response với một trường duy nhất là prompt hoặc response.",
        ),
        (
            "Normal",
            "Decorator `@app.post('/chat', response_model=ChatResponse)` đăng ký endpoint POST `/chat`. Hàm `chat_endpoint(request)` tạo ra chuỗi giả lập `[stub] Character would answer: {request.prompt}` và bọc lại bằng `ChatResponse`.",
        ),
        (
            "Normal",
            "Nếu chạy trực tiếp file này, khối `__main__` sẽ gọi `uvicorn.run(app, host='0.0.0.0', port=8000)`. Đây là cách phổ biến để khởi động server local phục vụ thử nghiệm hoặc tích hợp frontend.",
        ),
        (
            "Normal",
            "Có một điểm kiến trúc chưa tối ưu: `api.py` không tái sử dụng hàm `chat()` trong `chat.py`, mà tự tạo một stub response riêng. Nếu sau này thay stub bằng model thật, hai file có nguy cơ bị lệch logic nếu không được hợp nhất.",
        ),
        ("Heading1", "9. Notebook và tài nguyên phụ"),
        (
            "Normal",
            "`notebooks/exploration.ipynb` hiện chỉ có một cell markdown với nội dung giới thiệu notebook khám phá dữ liệu. Chưa có cell code nào. Điều đó nghĩa là notebook mới được dựng để giữ chỗ, chưa đóng góp logic vào pipeline.",
        ),
        (
            "Normal",
            "`models/.gitkeep` chỉ có tác dụng giữ thư mục `models/` tồn tại trong Git dù thư mục rỗng. Đây là một mẹo rất phổ biến trong các repo cần thư mục output nhưng không muốn commit file nặng.",
        ),
        ("Heading1", "10. Luồng setup end-to-end mà project đang hướng tới"),
        (
            "Normal",
            "Nếu ghép tất cả file lại với nhau, luồng làm việc dự kiến của project là như sau.",
        ),
        (
            "Normal",
            "Bước 1: người dùng chuẩn bị môi trường bằng cách cài dependency trong `requirements.txt`, tạo `.env`, điền API key và chọn `BASE_MODEL` cùng `CHARACTER_NAME`.",
        ),
        (
            "Normal",
            "Bước 2: chạy `scraper.py` để lấy kiến thức về nhân vật và lưu vào `data/raw/character_wiki.txt`.",
        ),
        (
            "Normal",
            "Bước 3: chạy `chunker.py` để chia text thô thành danh sách chunk nhỏ và lưu trong `data/processed/chunks.json`.",
        ),
        (
            "Normal",
            "Bước 4: chạy `generate_pairs.py` để biến mỗi chunk thành một cặp huấn luyện `input`/`output`, sau đó ghi vào `train.jsonl` và `eval.jsonl`.",
        ),
        (
            "Normal",
            "Bước 5: chạy `validate_data.py` để chắc chắn JSONL không hỏng định dạng.",
        ),
        (
            "Normal",
            "Bước 6: chạy `train.py` để fine-tune mô hình nền với cấu hình từ `config.yaml` và lưu model vào `models/character-model`.",
        ),
        (
            "Normal",
            "Bước 7: chạy `evaluate.py` để đánh giá model, rồi dùng `chat.py` hoặc `api.py` để trò chuyện với nhân vật.",
        ),
        (
            "Normal",
            "Đó là thiết kế logic của dự án. Nhưng hiện tại nhiều bước trong số này vẫn chưa hoàn thiện về mặt thực thi thực tế.",
        ),
        ("Heading1", "11. Những điểm chưa hoàn thiện hoặc cần lưu ý"),
        (
            "Normal",
            "1. Dự án hiện là scaffold: `train.py`, `evaluate.py`, `chat.py`, `api.py` đều đang dùng placeholder hoặc stub, chưa nối tới model thật.",
        ),
        (
            "Normal",
            "2. `generate_pairs.py` có lỗi chạy CLI thật sự do đặt tên positional argument với dấu gạch ngang nhưng lại truy cập bằng dấu gạch dưới.",
        ),
        (
            "Normal",
            "3. Cùng file đó còn có lỗi phạm vi import: `json` chỉ được import trong `__main__`, làm cho helper function không an toàn nếu tái sử dụng từ module khác.",
        ),
        (
            "Normal",
            "4. `train.py` phụ thuộc vào thư mục chạy hiện tại vì dùng `config.yaml` theo đường dẫn tương đối đơn giản.",
        ),
        (
            "Normal",
            "5. `requirements.txt` thiếu `PyYAML`, dù code train cần `yaml`.",
        ),
        (
            "Normal",
            "6. `.env` hiện mới là chỗ để người dùng điền giá trị, chứ chưa được load tự động; `BASE_MODEL` trong YAML cũng chưa được nội suy thành biến môi trường thật.",
        ),
        (
            "Normal",
            "7. Dữ liệu ví dụ hiện rỗng, nên cả pipeline chưa có đầu vào thật để chứng minh end-to-end.",
        ),
        (
            "Normal",
            "8. `validate_data.py` có thể báo pass cho file trống, nên nếu chỉ dựa vào script này, người dùng có thể tưởng rằng dữ liệu đã sẵn sàng để train dù thực tế không có record nào.",
        ),
        ("Heading1", "12. Kết luận"),
        (
            "Normal",
            "Toàn bộ code thiết lập của project này cho thấy một ý tưởng khá rõ ràng: xây chatbot nhân vật theo pipeline dữ liệu chuẩn, từ scrape tri thức tới phục vụ API. Về mặt tổ chức thư mục và phân vai file, repo được sắp xếp tốt cho một prototype học máy nhỏ.",
        ),
        (
            "Normal",
            "Tuy nhiên, nếu nhìn đúng hiện trạng mã nguồn, đây vẫn là bộ khung nhiều hơn là sản phẩm đã hoàn thiện. Các file đã nói lên rất rõ ý đồ của tác giả, nhưng để chạy thành một hệ thống hoàn chỉnh vẫn cần bổ sung logic sinh dữ liệu thật, logic fine-tune thật, cơ chế load `.env`, sửa đường dẫn và khắc phục các lỗi CLI hiện có.",
        ),
        (
            "Normal",
            "Vì vậy cách hiểu chính xác nhất là: project đã thiết lập xong kiến trúc và các điểm móc chính, nhưng chưa đi hết chặng cuối để trở thành một chatbot character-LLM vận hành đầy đủ.",
        ),
    ]


def paragraph_xml(text: str, style: str) -> str:
    escaped = escape(text)
    style_xml = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>'
    return (
        f"<w:p>{style_xml}"
        f'<w:r><w:t xml:space="preserve">{escaped}</w:t></w:r>'
        f"</w:p>"
    )


def build_document_xml(content: list[tuple[str, str]]) -> str:
    paragraphs = "".join(paragraph_xml(text, style) for style, text in content)
    section = (
        "<w:sectPr>"
        '<w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/>'
        "</w:sectPr>"
    )
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{paragraphs}{section}</w:body>"
        "</w:document>"
    )


def build_styles_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Calibri" w:cs="Calibri"/>
        <w:sz w:val="22"/>
        <w:szCs w:val="22"/>
      </w:rPr>
    </w:rPrDefault>
  </w:docDefaults>
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:qFormat/>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Title">
    <w:name w:val="Title"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:pPr>
      <w:spacing w:after="240"/>
    </w:pPr>
    <w:rPr>
      <w:b/>
      <w:sz w:val="32"/>
      <w:szCs w:val="32"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:pPr>
      <w:spacing w:before="240" w:after="120"/>
    </w:pPr>
    <w:rPr>
      <w:b/>
      <w:sz w:val="28"/>
      <w:szCs w:val="28"/>
    </w:rPr>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading2">
    <w:name w:val="heading 2"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:qFormat/>
    <w:pPr>
      <w:spacing w:before="180" w:after="80"/>
    </w:pPr>
    <w:rPr>
      <w:b/>
      <w:sz w:val="24"/>
      <w:szCs w:val="24"/>
    </w:rPr>
  </w:style>
</w:styles>
"""


def build_content_types_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
"""


def build_root_rels_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""


def build_document_rels_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
"""


def build_core_xml() -> str:
    created = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    title = escape("Giải thích code thiết lập project Small-Chatbot_RAG")
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:dcterms="http://purl.org/dc/terms/"
  xmlns:dcmitype="http://purl.org/dc/dcmitype/"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>{title}</dc:title>
  <dc:creator>Codex</dc:creator>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{created}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{created}</dcterms:modified>
</cp:coreProperties>
"""


def build_app_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
  xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Microsoft Office Word</Application>
  <DocSecurity>0</DocSecurity>
  <ScaleCrop>false</ScaleCrop>
  <HeadingPairs>
    <vt:vector size="2" baseType="variant">
      <vt:variant><vt:lpstr>Title</vt:lpstr></vt:variant>
      <vt:variant><vt:i4>1</vt:i4></vt:variant>
    </vt:vector>
  </HeadingPairs>
  <TitlesOfParts>
    <vt:vector size="1" baseType="lpstr">
      <vt:lpstr>Document</vt:lpstr>
    </vt:vector>
  </TitlesOfParts>
  <Company></Company>
  <LinksUpToDate>false</LinksUpToDate>
  <SharedDoc>false</SharedDoc>
  <HyperlinksChanged>false</HyperlinksChanged>
  <AppVersion>16.0000</AppVersion>
</Properties>
"""


def write_docx(output_path: Path) -> None:
    content = build_content()
    with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", build_content_types_xml())
        docx.writestr("_rels/.rels", build_root_rels_xml())
        docx.writestr("docProps/core.xml", build_core_xml())
        docx.writestr("docProps/app.xml", build_app_xml())
        docx.writestr("word/document.xml", build_document_xml(content))
        docx.writestr("word/styles.xml", build_styles_xml())
        docx.writestr("word/_rels/document.xml.rels", build_document_rels_xml())


if __name__ == "__main__":
    write_docx(OUTPUT_PATH)
    print(f"Created: {OUTPUT_PATH}")
