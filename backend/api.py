import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

# Clean imports from your modular backend
from data.ingestion import process_and_ingest_pdf
from retrievers.retrievers import get_vector_store
from chains.chains import build_rag_chain, build_summary_chain

app = FastAPI(title="PaperPilot RAG API", description="Backend for local PDF RAG system")

app_state = {
    "documents": [],       # Required in-memory for BM25Retriever
    "chat_history": [],    # Tracks the LangChain message objects
    "rag_chain": None,     # Cached chain — built once per document set, not per request
    "summary_chain": build_summary_chain(),  # Cheap to build; created once at startup
}

TEMP_UPLOAD_DIR = "./temp_uploads"
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)

# ---------------------------------------------------------
# Pydantic Models for Validation
# ---------------------------------------------------------
class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    
# ---------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Accepts a PDF file, processes it via the ingestion orchestrator,
    updates in-memory BM25 state, and rebuilds the cached RAG chain
    (BM25 index, MultiQueryRetriever, and cross-encoder reranker)
    exactly once for the new document set — not on every /chat call.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_path = os.path.join(TEMP_UPLOAD_DIR, file.filename)
    
    try:
        # 1. Save uploaded file temporarily to disk
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Run the full ingestion orchestrator
        # It now unpacks the vector store and the chunks you need!
        vector_store, final_chunks = process_and_ingest_pdf(file_path)
        
        # 3. Save final chunks in memory (Required for BM25 Retriever)
        app_state["documents"].extend(final_chunks)

        # 4. Rebuild the cached RAG chain now that the document set has
        # changed. This is the only place the expensive retriever stack
        # (BM25 indexing + cross-encoder load) should happen.
        app_state["rag_chain"] = build_rag_chain(app_state["documents"])
        
        return {
            "message": f"Successfully ingested {file.filename} into the RAG pipeline.",
            "chunks_created": len(final_chunks)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)



@app.post("/chat", response_model=ChatResponse)
async def chat_with_document(request: ChatRequest):
    """
    Retrieves context, generates an answer, summarizes it (or bypasses if 
    fallback is triggered), and maintains a 10-message sliding window history.

    Flow mirrors pipeline_03.ipynb exactly:
      1. Stream the cached RAG chain and accumulate chunks into full_response.
      2. Check the fallback phrase; bypass or summarize accordingly.
      3. Extend chat_history with the Human/AI messages.
      4. Trim chat_history to the last 10 messages.

    The chain itself is NOT rebuilt here — it's reused from app_state,
    where it was constructed once in /upload.
    """
    if not app_state["documents"] or app_state["rag_chain"] is None:
        raise HTTPException(
            status_code=400, 
            detail="No documents have been ingested yet. Please upload a PDF first."
        )

    try:
        # 1. Execute the cached RAG chain via streaming, accumulating chunks
        # into full_response — matches the notebook's `chain.stream(...)` loop.
        full_response = ""
        chunks = app_state["rag_chain"].stream({
            "input": request.query,
            "chat_history": app_state["chat_history"]
        })
        for chunk in chunks:
            full_response += chunk

        # 2. Define the fallback phrase
        fallback_phrase = "The given document does not contain context to this query."
        
        # 3. Apply the fallback bypass or summarize the AI response
        if fallback_phrase in full_response:
            ai_summary = fallback_phrase
            print(f"\n---\nAI Summary Bypassed: {ai_summary}\n---\n")
        else:
            ai_summary = app_state["summary_chain"].invoke({"response": full_response})
            print(f"\n---\nAI Summary: {ai_summary}\n---\n")
            
        # 4. Append user query and the SUMMARIZED AI response to history
        app_state["chat_history"].extend([
            HumanMessage(content=request.query),
            AIMessage(content=ai_summary)
        ])
        
        # 5. Maintain the sliding window (keep only the last 10 messages)
        app_state["chat_history"] = app_state["chat_history"][-10:]
        
        # Note: We return the `full_response` to the user so they get the detailed answer,
        # but only the `ai_summary` is kept in `app_state["chat_history"]` for the next turn.
        return ChatResponse(answer=full_response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear")
async def clear_history():
    """Wipes the current chat memory."""
    app_state["chat_history"] = []
    return {"message": "Chat history cleared."}