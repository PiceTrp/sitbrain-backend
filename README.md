# Sitbrain-backend - RAG Chat API

FastAPI-based RAG service for uploading documents and chatting with their content using AI.

![Example](https://raw.githubusercontent.com/PiceTrp/sitbrain-backend/main/assets/rag_qa.png)

## Quick Start

### Prerequisites

- Python 3.12+
- uv (fast Python package manager)
- Qdrant server running
- Google AI API key

### Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv pip install -r requirements.txt

# Or sync with pyproject.toml
uv sync
```

### Run

```bash
# Start Qdrant
docker compose up -d

# Start API
uv run python -m uvicorn app.main:app

# Start Gradio UI (optional)
uv run python gradio_app.py
```

## API Usage

### Upload Document

```bash
curl -X POST "http://localhost:8080/api/v1/documents/upload" \
  -F "file=@document.pdf"
```

### Chat

```bash
curl -X POST "http://localhost:8080/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?"}'
```

### Health Check

```bash
curl http://localhost:8080/health
```

## Features

- Upload PDF, DOCX, TXT files
- Vector storage with Qdrant
- Chat using Google Gemini
- Gradio web interface
- Optimized service management

## Tech Stack

- **Backend**: FastAPI, Langchain
- **Vector DB**: Qdrant
- **LLM**: Google Gemini
- **Embeddings**: OpenAI
- **Frontend**: Gradio
