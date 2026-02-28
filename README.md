# 📞 Hệ Thống Phát Hiện Cuộc Gọi Lừa Đảo

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/Groq-LLaMA%203.1%20%7C%20Whisper-F55036?style=for-the-badge" />
  <img src="https://img.shields.io/badge/XGBoost-2.0%2B-337AB7?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
</p>

<p align="center">
  Ứng dụng web sử dụng AI để phân tích file âm thanh cuộc gọi điện thoại,<br/>
  tự động phát hiện và phân loại <strong>14 loại lừa đảo</strong> phổ biến tại Việt Nam theo thời gian thực.
</p>

---

## Mục Lục

- [Giới thiệu](#giới-thiệu)
- [Tính năng nổi bật](#tính-năng-nổi-bật)
- [Kiến trúc hệ thống](#kiến-trúc-hệ-thống)
- [Công nghệ sử dụng](#công-nghệ-sử-dụng)
- [Hướng dẫn cài đặt](#hướng-dẫn-cài-đặt)
  - [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
  - [Cài đặt](#cài-đặt)
  - [Cấu hình](#cấu-hình)
  - [Chạy ứng dụng](#chạy-ứng-dụng)
- [Cấu trúc thư mục](#cấu-trúc-thư-mục)
- [Mô hình Machine Learning](#mô-hình-machine-learning)
  - [Bộ phân loại đa nhãn](#bộ-phân-loại-đa-nhãn)
  - [14 loại lừa đảo](#14-loại-lừa-đảo)
- [Quy trình xử lý](#quy-trình-xử-lý)
- [Ảnh chụp màn hình](#ảnh-chụp-màn-hình)
- [Lộ trình phát triển](#lộ-trình-phát-triển)
- [Đóng góp](#đóng-góp)
- [Giấy phép](#giấy-phép)
- [Lời cảm ơn](#lời-cảm-ơn)

---

## Giới Thiệu

**Hệ Thống Phát Hiện Cuộc Gọi Lừa Đảo** là ứng dụng nghiên cứu khoa học (*NCKH*) được xây dựng trên nền tảng Streamlit. Hệ thống tự động nhận diện các cuộc gọi lừa đảo tiếng Việt qua 4 bước:

1. **Chuyển đổi giọng nói → văn bản** bằng Groq Whisper API, chia theo từng đoạn 10 giây.
2. **Trích xuất đặc trưng ngôn ngữ** — từ khóa đáng ngờ, tín hiệu hành vi — thông qua LLaMA 3.1.
3. **Phân loại lừa đảo** vào 1 trong 14 nhóm thật sự bằng mô hình XGBoost đã huấn luyện.
4. **Trực quan hóa** điểm nghi ngờ theo trục thời gian và sinh cảnh báo cụ thể cho người dùng.

---

## Tính Năng Nổi Bật

| Tính năng | Mô tả |
|---|---|
| 🎙️ **Tải file âm thanh** | Hỗ trợ MP3, WAV, M4A, OGG, MP4 — tối đa 200 MB |
| 📝 **Speech-to-Text** | Groq Whisper `whisper-large-v3`, tiếng Việt, chia chunk 10 giây |
| 🔍 **Trích xuất từ khóa** | LLaMA 3.1-8B-Instant phát hiện từ khóa, tín hiệu đe dọa, trích dẫn đáng ngờ |
| 🤖 **Phân loại lừa đảo** | TF-IDF + XGBoost đa nhãn, 14 loại lừa đảo thực tế |
| 📊 **Biểu đồ điểm nghi ngờ** | Đường SVG hiển thị điểm 0–1 theo từng đoạn 10 giây |
| ⚠️ **Cảnh báo thông minh** | LLM tự sinh cảnh báo và lời khuyên cụ thể theo loại lừa đảo |
| 🎨 **Giao diện tùy chỉnh** | HTML/CSS hoàn toàn tùy biến, ẩn toàn bộ chrome mặc định của Streamlit |

---

## Kiến Trúc Hệ Thống

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit App                            │
│                                                                 │
│  ┌──────────────────┐    ┌───────────────────────────────────┐  │
│  │   Trang chủ      │───▶│        Trang phân tích            │  │
│  │  (upload file)   │    │  (biểu đồ, kết quả, transcript)   │  │
│  └──────────────────┘    └──────────────┬────────────────────┘  │
└─────────────────────────────────────────┼───────────────────────┘
                                          │
                      ┌───────────────────▼────────────────────┐
                      │           Analysis Engine              │
                      │  (điều phối toàn bộ pipeline xử lý)    │
                      └───┬─────────────┬──────────────────────┘
                          │             │
           ┌──────────────▼──┐  ┌───────▼─────────────────────┐
           │  SpeechToText   │  │        LLMClient             │
           │ (Groq Whisper)  │  │  (Groq LLaMA 3.1-8B)        │
           │  chunk 10 giây  │  │  trích xuất từ khóa/tín hiệu │
           └─────────────────┘  └───────┬─────────────────────┘
                                        │
                       ┌────────────────▼────────────────┐
                       │      MultilabelPredictor         │
                       │  TF-IDF + XGBoost (14 nhãn)     │
                       │  Ngưỡng cảnh báo: 0.40          │
                       └─────────────────────────────────┘
```

Mỗi đoạn 10 giây tạo ra một `ChunkResult` với cấu trúc:

```python
{
    "time_label":  "00:10",       # thời điểm bắt đầu (MM:SS)
    "time_end":    "00:20",       # thời điểm kết thúc (MM:SS)
    "time_range":  "00:10-00:20",
    "diem":        0.72,          # điểm nghi ngờ 0–1
    "text":        "...",         # nội dung thoại chuyển đổi
    "keywords":    [...],         # từ khóa trích xuất được
    "loai":        [...]          # loại lừa đảo dự đoán
}
```

---

## Công Nghệ Sử Dụng

| Tầng | Công nghệ |
|---|---|
| Web Framework | [Streamlit](https://streamlit.io/) ≥ 1.28 |
| LLM / STT API | [Groq](https://console.groq.com/) — LLaMA 3.1-8B-Instant + Whisper Large v3 |
| Machine Learning | [XGBoost](https://xgboost.readthedocs.io/) ≥ 2.0, [scikit-learn](https://scikit-learn.org/) ≥ 1.3 |
| Xử lý dữ liệu | [pandas](https://pandas.pydata.org/) ≥ 2.0, [NumPy](https://numpy.org/) ≥ 1.24 |
| Xử lý âm thanh | [pydub](https://github.com/jiaaro/pydub) ≥ 0.25 + FFmpeg |
| Lưu mô hình | [joblib](https://joblib.readthedocs.io/) ≥ 1.3 |
| Biến môi trường | [python-dotenv](https://pypi.org/project/python-dotenv/) ≥ 1.0 |

---

## Hướng Dẫn Cài Đặt

### Yêu Cầu Hệ Thống

- Python **3.10** trở lên
- **FFmpeg** đã cài đặt và có trong `PATH`:
  - **Windows:** `choco install ffmpeg` hoặc tải tại [ffmpeg.org](https://ffmpeg.org/download.html)
  - **Ubuntu/Debian:** `sudo apt install ffmpeg`
  - **macOS:** `brew install ffmpeg`
- **Groq API key** — đăng ký miễn phí tại [console.groq.com](https://console.groq.com/)

### Cài Đặt

```bash
# 1. Clone dự án về máy
git clone https://github.com/<your-username>/call-fraud-detection.git
cd call-fraud-detection

# 2. Tạo và kích hoạt môi trường ảo
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 3. Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

### Cấu Hình

Sao chép file môi trường mẫu và điền API key:

```bash
cp .env.example .env
```

Chỉnh sửa file `.env`:

```dotenv
# .env
GROQ_API_KEY=gsk_your_actual_key_here
```

> **Bảo mật:** Không được commit file `.env` hoặc hard-code API key vào mã nguồn. File `.gitignore` đã được cấu hình sẵn để loại trừ `.env`.

Ứng dụng yêu cầu các file mô hình đã huấn luyện phải có sẵn trong thư mục `models/`:

```
models/
├── mo_hinh_da_lop.pkl          # Mô hình XGBoost đa nhãn
├── tfidf_vectorizer_v2.pkl     # Bộ vector hóa TF-IDF
├── mapping_loai.json           # Ánh xạ chỉ số nhãn → tên loại lừa đảo
└── tu_khoa_dac_trung_loai.json # Từ khóa đặc trưng theo từng loại
```

> Các file `.pkl` không được lưu trên git (file nhị phân). Tải về từ trang release hoặc tự huấn luyện bằng notebook `Mo_hinh_2_Phan_loai_Da_lop_Nhi_phan.ipynb`.

### Chạy Ứng Dụng

```bash
streamlit run app.py
```

Ứng dụng sẽ khởi động tại **http://localhost:8501**.

---

## Cấu Trúc Thư Mục

```
call-fraud-detection/
│
├── app.py                       # Điểm vào: cấu hình Streamlit + bộ điều hướng trang
│
├── views/
│   ├── home_page.py             # Trang 1 – Giao diện tải file (HTML/CSS + widget)
│   └── analysis_page.py         # Trang 2 – Bảng kết quả phân tích
│
├── src/
│   ├── analysis_engine.py       # Pipeline chính: Audio → STT → LLM → ML
│   ├── speech_to_text.py        # Groq Whisper STT, chuyển đổi theo từng chunk
│   ├── llm_client.py            # Groq LLaMA client – trích xuất từ khóa & tín hiệu
│   ├── multilabel_predictor.py  # Bộ phân loại TF-IDF + XGBoost đa nhãn
│   ├── chart_builder.py         # Sinh biểu đồ SVG điểm nghi ngờ theo thời gian
│   ├── upload_handler.py        # Kiểm tra file, cập nhật session_state, điều hướng
│   ├── assets_loader.py         # Tải icon & hình ảnh trang trí dưới dạng base64
│   └── loading_screen.py        # Màn hình loading động trong lúc phân tích
│
├── config/
│   ├── settings.py              # Hằng số trung tâm: đường dẫn, tham số mô hình, nhãn
│   └── keywords.json            # Từ vựng từ khóa lừa đảo định nghĩa sẵn theo nhóm
│
├── models/
│   ├── mo_hinh_da_lop.pkl       # Mô hình XGBoost đã huấn luyện (không lưu trên git)
│   ├── tfidf_vectorizer_v2.pkl  # TF-IDF vectorizer đã huấn luyện (không lưu trên git)
│   ├── mapping_loai.json        # {chỉ_số_nhãn: tên_loại_lừa_đảo}
│   └── tu_khoa_dac_trung_loai.json  # Từ khóa đặc trưng theo từng loại lừa đảo
│
├── data/
│   ├── data_scam_fix.csv        # Tập dữ liệu transcript có nhãn (dữ liệu huấn luyện)
│   └── demo_hoithoai_conga.txt  # Hội thoại mẫu để demo
│
├── assets/
│   ├── icons/                   # Icon SVG/PNG dùng trong giao diện
│   └── decorations/             # Hình ảnh trang trí nền
│
├── .streamlit/
│   └── config.toml              # Cấu hình server & theme Streamlit
│
├── .env.example                 # Mẫu biến môi trường
├── .gitignore
└── requirements.txt
```

---

## Mô Hình Machine Learning

### Bộ Phân Loại Đa Nhãn

Bộ phân loại cốt lõi là **Mô hình 2** (`mo_hinh_da_lop.pkl`), được huấn luyện trên tập transcript cuộc gọi lừa đảo tiếng Việt có nhãn thật.

| Thành phần | Chi tiết |
|---|---|
| Vector hóa | TF-IDF (`tfidf_vectorizer_v2.pkl`), tiếng Việt, n-gram (1–2) |
| Bộ phân loại | XGBoost (`XGBClassifier`), bọc trong `MulticlassAsBinary` cho mỗi nhãn |
| Ngưỡng cảnh báo | **0.40** (thay đổi tại `config/settings.py` → `NGUONG_CANH_BAO`) |
| Số từ khóa tối thiểu | Cần ít nhất 3 từ khóa để kích hoạt dự đoán |
| Notebook huấn luyện | `Mo_hinh_2_Phan_loai_Da_lop_Nhi_phan.ipynb` |

#### Wrapper `MulticlassAsBinary`

Lớp bọc mỏng trích xuất xác suất nhị phân cho một nhãn duy nhất từ mô hình đa lớp, cho phép một mô hình XGBoost thực hiện 14 quyết định nhị phân độc lập:

```python
class MulticlassAsBinary:
    def __init__(self, model, class_idx): ...
    def predict_proba(self, X) -> np.ndarray: ...  # shape (n, 2)
    def predict(self, X) -> np.ndarray: ...         # shape (n,) — 0 hoặc 1
```

### 14 Loại Lừa Đảo

| ID | Loại lừa đảo | Mô tả |
|---|---|---|
| 1 | Giả danh cơ sở giáo dục | Giả làm trường học, giáo viên, ban giám hiệu |
| 2 | Giả danh nhân viên bảo hiểm | Giả làm nhân viên công ty bảo hiểm |
| 3 | Giả mạo cơ quan xuất khẩu lao động | Lừa đảo tuyển dụng đi lao động nước ngoài |
| 4 | Giả mạo cục viễn thông | Giả làm cán bộ Cục Viễn thông/An toàn thông tin |
| 5 | Giả mạo là công an | Giả làm công an, viện kiểm sát, tòa án |
| 6 | Giả mạo người giao hàng | Lừa đảo liên quan đến bưu kiện, đơn hàng |
| 7 | Giả mạo nhà tuyển dụng | Lừa đảo tuyển dụng việc làm giả |
| 8 | Giả mạo đại sứ quán | Giả làm nhân viên đại sứ quán, lãnh sự quán |
| 9 | Lừa đảo liên quan sức khỏe | Bán thuốc giả, dịch vụ y tế giả |
| 10 | Lừa đảo ngoại tình | Dùng thông tin nhạy cảm để tống tiền |
| 11 | Lừa đảo phí điện nước | Thúc ép thanh toán hóa đơn điện/nước giả |
| 12 | Lừa đảo quà tặng | Báo trúng thưởng, yêu cầu đóng phí nhận quà |
| 13 | Lừa đảo tài chính – ngân hàng | Giả nhân viên ngân hàng, đánh cắp thông tin tài khoản |
| 14 | Lừa đảo đe dọa | Đe dọa, ép buộc chuyển tiền qua áp lực tâm lý |

---

## Quy Trình Xử Lý

```
File âm thanh (bytes)
        │
        ▼
┌──────────────────────────────────────────────────────┐
│  SpeechToText.transcribe_chunks_from_bytes()         │
│  • Chia audio thành các đoạn 10 giây bằng pydub      │
│  • Gửi từng đoạn lên Groq Whisper API               │
│  • Ngôn ngữ: Tiếng Việt ("vi")                      │
│  • Model: whisper-large-v3                           │
└─────────────────────┬────────────────────────────────┘
                      │  Danh sách (start_sec, text)
                      ▼
┌──────────────────────────────────────────────────────┐
│  LLMClient.extract_keywords(chunk_text)              │
│  • System prompt → bắt buộc trả về JSON thuần       │
│  • Kết quả: keywords[], signals[], scammer_quote    │
│  • Model: llama-3.1-8b-instant                      │
└─────────────────────┬────────────────────────────────┘
                      │  Dict {keywords, signals, ...}
                      ▼
┌──────────────────────────────────────────────────────┐
│  MultilabelPredictor.predict(keywords)               │
│  • TF-IDF biến đổi chuỗi từ khóa                   │
│  • XGBoost MulticlassAsBinary × 14 nhãn             │
│  • Kết quả: loai_du_doan[], diem_nghi_ngo (0–1)     │
└─────────────────────┬────────────────────────────────┘
                      │  ChunkResult dict
                      ▼
            session_state["chunk_scores"]
                      │
                      ▼
        Trang phân tích hiển thị:
        ├── Tỷ lệ % nghi ngờ lừa đảo (max diem)
        ├── Biểu đồ SVG điểm nghi ngờ theo thời gian
        ├── Tag cloud từ khóa nổi bật
        ├── Bảng transcript theo từng đoạn (có highlight)
        └── Cảnh báo & lời khuyên do LLM sinh ra
```

---

## Ảnh Chụp Màn Hình

> *(Thêm ảnh chụp màn hình khi ứng dụng đã chạy)*

| Trang chủ | Trang kết quả phân tích |
|---|---|
| ![Trang chủ](assets/screenshots/home.png) | ![Kết quả](assets/screenshots/analysis.png) |

---

## Lộ Trình Phát Triển

- [ ] Ghi âm trực tiếp từ microphone (phân tích theo thời gian thực)
- [ ] Hỗ trợ đa ngôn ngữ (tiếng Anh, tiếng Trung)
- [ ] Backend REST API (FastAPI) để tích hợp với hệ thống khác
- [ ] Dockerize ứng dụng để triển khai dễ dàng
- [ ] Hiệu chỉnh điểm tin cậy riêng cho từng loại lừa đảo
- [ ] Xuất báo cáo phân tích dạng PDF
- [ ] Dashboard quản trị hỗ trợ tải file hàng loạt

---

## Đóng Góp

Mọi đóng góp đều được chào đón! Vui lòng thực hiện theo các bước sau:

1. Fork repository này
2. Tạo nhánh tính năng: `git checkout -b feature/ten-tinh-nang`
3. Commit thay đổi: `git commit -m "feat: mô tả tính năng"`
4. Push lên nhánh: `git push origin feature/ten-tinh-nang`
5. Mở Pull Request

Vui lòng tuân theo quy ước [Conventional Commits](https://www.conventionalcommits.org/) khi viết commit message.

---

## Giấy Phép

Dự án được cấp phép theo **MIT License** — xem file [LICENSE](LICENSE) để biết chi tiết.

---

## Lời Cảm Ơn

- [Groq](https://groq.com/) — cung cấp API inference LLM và Whisper tốc độ cao
- [Streamlit](https://streamlit.io/) — nền tảng xây dựng ứng dụng web nhanh chóng
- [XGBoost](https://xgboost.readthedocs.io/) và [scikit-learn](https://scikit-learn.org/) — thư viện ML cốt lõi
- [pydub](https://github.com/jiaaro/pydub) — xử lý và chia nhỏ file âm thanh
- Cộng đồng nghiên cứu an ninh mạng Việt Nam — cung cấp dữ liệu transcript cuộc gọi lừa đảo

---

<p align="center">
  Được xây dựng với ❤️ vì cộng đồng Việt Nam — <i>Bảo vệ người dùng khỏi lừa đảo qua điện thoại</i>
</p>
#   s t r e a m l i t - d e m o - s c a m - p h o n e  
 