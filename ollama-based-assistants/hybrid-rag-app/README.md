# 📄 Hybrid RAG PDF Chatbot

A local Retrieval-Augmented Generation (RAG) application that lets you chat with your PDF documents.  
It uses a **hybrid search** (dense semantic + sparse BM25) and an **ollama** local LLM (Qwen3 8B) to answer questions.

## 🔍 What is Hybrid RAG?

The retriever combines two search strategies:

- **Semantic search** – uses `nomic-embed-text` embeddings to find conceptually similar text.
- **Keyword search (BM25)** – matches exact words from your question.

Results are merged with equal weight to improve answer quality.

## 🧰 Stack

- **UI**: Streamlit
- **LLM**: ollama + Qwen3 8B
- **Embeddings**: nomic-embed-text (ollama)
- **Vector Store**: InMemory (langchain-core)
- **PDF Loader**: PDFPlumber
- **Retrievers**: BM25 + custom hybrid ensemble

## 🚀 Quick Start

### 1. Install ollama and pull models

```bash
# Install ollama from https://ollama.com
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

### 2. Clone or create project folder

```bash
mkdir rag-app
cd rag-app
# Place app.py, requirements.txt, README.md inside
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Download NLTK data (if using default tokenizer)

```bash
python -c "import nltk; nltk.download('punkt_tab')"
```

If you switched to `str.split` inside the code, this step is optional.

### 5. Run the application

```bash
streamlit run app.py
```

Open `http://localhost:8501`, upload a PDF, and start asking questions.

## 📂 Project Structure

```
rag-app/
├── app.py               # Main application
├── requirements.txt
├── README.md
└── pdfs/                # Uploaded PDFs stored here (auto-created)
```

## ⚙️ Customisation

- **LLM**: Change `LLM_MODEL` in `app.py` to any ollama model (e.g. `llama3:8b`).
- **Embedding model**: Switch `EMBED_MODEL` to `bge-m3` for multilingual support.
- **Hybrid weights**: Adjust `weights=[0.5, 0.5]` inside `build_retrievers()`.
- **Context size**: Modify `chunk_size` and `chunk_overlap` in `RecursiveCharacterTextSplitter`.
- **Korean PDFs**: Replace `preprocess_func=lambda x: x.split()` with a Korean tokenizer (e.g. `Okt`).

## ❗ Troubleshooting

| Issue                                       | Solution                                                                                                                                            |
| ------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ModuleNotFoundError: langchain.retrievers` | The code uses a custom `SimpleHybridRetriever` – no extra install needed.                                                                           |
| `LookupError: punkt_tab`                    | Run `nltk.download('punkt_tab')` or switch to `lambda x: x.split()` in the BM25 preprocessor.                                                       |
| Spinner hangs forever                       | Check terminal logs. If `[RETRIEVE]` doesn't appear, ollama may be down. Test with `curl http://localhost:11434/api/embeddings` and `api/generate`. |
| Slow responses                              | Qwen3 8B works with CPU but is faster on a GPU. Reduce number of retrieved documents (e.g., top 4) in `SimpleHybridRetriever`.                      |
