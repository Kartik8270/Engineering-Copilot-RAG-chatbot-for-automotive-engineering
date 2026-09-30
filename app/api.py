import shutil

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from . import rag
from .config import UPLOAD_DIR
from .ingest import ingest_pdf
from .vectorstore import add_chunks, list_documents

app = FastAPI(title="Engineering Copilot")


class ChatRequest(BaseModel):
    question: str
    session_id: str = "default"


@app.get("/health")
def health():
    return {"status": "ok", "llm_enabled": rag.get_llm() is not None}


@app.post("/upload")
def upload(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported.")
    dest = UPLOAD_DIR / file.filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        chunks, info = ingest_pdf(dest)
    except Exception as e:
        raise HTTPException(422, f"Could not parse PDF: {e}")
    if not chunks:
        raise HTTPException(422, "No extractable text (scanned PDF? add OCR).")
    add_chunks(chunks, dest.name)
    return info


@app.get("/documents")
def documents():
    return list_documents()


@app.post("/chat")
def chat(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(400, "Empty question.")
    return rag.answer(req.question, req.session_id)


@app.delete("/chat/{session_id}")
def clear(session_id: str):
    rag.reset(session_id)
    return {"cleared": session_id}
