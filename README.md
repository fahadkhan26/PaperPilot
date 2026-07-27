# PaperPilot ✈️📄

PaperPilot is a conversational RAG application designed to handle PDF documents. It features a React/Vite frontend and a FastAPI backend powered by LangChain, utilizing a highly optimized, multi-stage retrieval and ingestion pipeline.

## 🌟 Core Features & Architecture

### 1. Structure-Aware Ingestion
* **`pymupdf4llm` Integration:** The system converts documents to Markdown first, allowing it to split chunks intelligently based on Markdown headers. This preserves the semantic structure and logical flow of technical documents and reports.

### 2. Multi-Stage Retrieval Pipeline
* **Hybrid Retrieval:** Combines the semantic understanding of Vector/Embeddings search with the exact-keyword matching of a BM25 Retriever to ensure high accuracy across both broad concepts and specific terminology.
* **MultiQuery Generation:** The system uses a `MultiQueryRetriever` to automatically generate multiple variations of the user's query from different perspectives, maximizing the chances of finding the right context.
* **Cross-Encoder Reranking:** After retrieving a broad set of candidate chunks, the pipeline passes them through a specialized Reranker model. This mathematically re-evaluates and reorders the chunks based on true relevance to the query, filtering out noise before it reaches the generation phase.

### 3. Smart Conversational Memory
* **History-Aware Context:** Employs a history-aware retriever that rephrases follow-up questions into standalone queries based on the ongoing conversation, allowing for natural, multi-turn interactions.
* **Summarized State Management:** To prevent context-window overflow and keep processing times fast, raw AI responses are dynamically summarized before being appended to the sliding-window chat history.

## 🛠️ Tech Stack

* **Frontend:** React, Vite
* **Backend:** FastAPI, Python
* **RAG Orchestration:** LangChain
* **Vector Store:** ChromaDB
* **Document Processing:** `pymupdf4llm`

## 🚀 Getting Started

### Backend Setup
1. Navigate to the backend directory.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   
3. Run the FastAPI server:
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload

```
### Frontend Setup

1. Navigate to the frontend directory.
2. Install Node modules:
```bash
npm install
```


3. Start the Vite development server:
```bash
npm run dev

```



## 🧠 State Management & Session Clearing

PaperPilot is built to handle one document context at a time to prevent vector cache poisoning. Uploading a new PDF automatically flushes the previous in-memory vector store and chat history, ensuring the AI remains strictly focused on the current document.
