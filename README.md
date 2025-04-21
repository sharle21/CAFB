#The project was part of a submission to Capital Area Food Bank Challenge along with @Anagha-0010


# 🧠 CAFBrain: AI Assistant for Content Generation

CAFBrain is a Retrieval-Augmented Generation (RAG) system designed to help the Capital Area Food Bank (CAFB) automatically generate high-quality content like grant proposals, blog posts, social media captions, and PowerPoint slides using internal documents as source material.

---

## 🚀 How to Run This Project

### 📦 1. Install Dependencies

Ensure Python 3.8+ is installed, then run:

```bash
pip install -r requirements.txt
```

---

### 📁 2. Prepare Dataset

Download and organize your dataset in the following structure:

```
CAFBrain_Dataset/
├── text/
├── images/
├── video/
├── captions/
├── sources/
├── metadata.jsonl
```

---

### 🧱 3. Chunk the Data

Run scripts to extract and chunk data from various content types:

```bash
# For text-based content
python scripts/scrape_blogs.py
python scripts/scrape_reports.py
python scripts/scrape_powerpoints.py
python scripts/scrape_collateral.py

# For media-based content (captions & images)
python scripts/scrape_captions.py
python scripts/scrape_image_captions.py
```

---

### 🧬 4. Generate Embeddings and Build FAISS Index

```bash
# Embed text chunks
python embeddings/embed_text_chunks.py

# Embed transcript/image chunks
python embeddings/embed_media_chunks.py
```

---

### 🔌 5. Start the Backend (FastAPI)

Launch the FastAPI server:

```bash
uvicorn api_server:app --reload
```

This powers the retrieval and content generation logic.

---

### 🎛️ 6. Launch the Frontend (Streamlit)

In a new terminal window, start the Streamlit frontend:

```bash
streamlit run streamlit_app/app.py
```

---

### ✨ 7. Use the CAFBrain App

1. Open your browser and go to [http://localhost:8501](http://localhost:8501)
2. Enter a prompt (e.g., “Write a 6-paragraph blog on food access barriers”)
3. Select content type (grant, blog, PPT, etc.)
4. Choose tone and format
5. Edit output in real-time
6. Download result as PDF, DOCX, or PPTX

---

## 📝 Notes

- Some scripts rely on OpenAI API, Whisper, or DALL·E — set up credentials in `.env` or use your API key as needed.
- Outputs are editable in the UI before downloading.
- Best used with CAFB’s internal dataset for meaningful outputs.

---

## 📄 License

This project is for educational and nonprofit use only.

