import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

from data.ingestion import process_and_ingest_pdf
from retrievers.retrievers import get_vector_store
from chains.chains import build_rag_chain, build_summary_chain

app = FastAPI(title="PaperPilot RAG API", description="Backend for local PDF RAG system")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app_state = {
    "documents": [],
    "chat_history": [],
    "rag_chain": None,
    "summary_chain": build_summary_chain(),
}

TEMP_UPLOAD_DIR = "./temp_uploads"
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)


STREAM_ERROR_MARKER = "\x00ERR\x00"

FALLBACK_PHRASE = "The given document does not contain context to this query."


class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    app_state["documents"] = []
    app_state["chat_history"] = []
    app_state["rag_chain"] = None

    file_path = os.path.join(TEMP_UPLOAD_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        vector_store, final_chunks = process_and_ingest_pdf(file_path)
        
        app_state["documents"] = final_chunks

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


def _finalize_turn(query: str, full_response: str) -> None:

    if FALLBACK_PHRASE in full_response:
        ai_summary = FALLBACK_PHRASE
        print(f"\n---\nAI Summary Bypassed: {ai_summary}\n---\n")
    else:
        ai_summary = app_state["summary_chain"].invoke({"response": full_response})
        print(f"\n---\nAI Summary: {ai_summary}\n---\n")

    app_state["chat_history"].extend([
        HumanMessage(content=query),
        AIMessage(content=ai_summary)
    ])
    app_state["chat_history"] = app_state["chat_history"][-10:]


@app.post("/chat/stream")
async def chat_with_document_stream(request: ChatRequest):

    if not app_state["documents"] or app_state["rag_chain"] is None:
        raise HTTPException(
            status_code=400,
            detail="No documents have been ingested yet. Please upload a PDF first."
        )

    def token_stream():
        full_response = ""
        try:
            for chunk in app_state["rag_chain"].stream({
                "input": request.query,
                "chat_history": app_state["chat_history"]
            }):
                full_response += chunk
                yield chunk
        except Exception as e:
            yield f"{STREAM_ERROR_MARKER}{str(e)}"
            return

        _finalize_turn(request.query, full_response)

    return StreamingResponse(token_stream(), media_type="text/plain")


@app.post("/chat", response_model=ChatResponse)
async def chat_with_document(request: ChatRequest):

    if not app_state["documents"] or app_state["rag_chain"] is None:
        raise HTTPException(
            status_code=400, 
            detail="No documents have been ingested yet. Please upload a PDF first."
        )

    try:
        full_response = ""
        chunks = app_state["rag_chain"].stream({
            "input": request.query,
            "chat_history": app_state["chat_history"]
        })
        for chunk in chunks:
            full_response += chunk

        _finalize_turn(request.query, full_response)

        return ChatResponse(answer=full_response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear")
async def clear_history():
    """Wipes the current chat memory."""
    app_state["chat_history"] = []
    return {"message": "Chat history cleared."}