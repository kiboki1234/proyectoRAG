from __future__ import annotations
from pathlib import Path
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import DOCS_DIR
from models import AskRequest, AskResponse, Citation
import ingest
import rag

app = FastAPI(title="RAG Offline Soberano")

# CORS (ajusta orígenes para tu front)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"ok": True, "service": "rag-offline-soberano"}

@app.post("/ingest")
async def ingest_files(files: List[UploadFile] = File(...)):
    saved_paths: List[Path] = []
    for f in files:
        content = await f.read()
        ext = Path(f.filename).suffix.lower()
        if ext not in [".pdf", ".md", ".markdown", ".txt"]:
            raise HTTPException(status_code=400, detail=f"Tipo no soportado: {ext}")
        dest = DOCS_DIR / f.filename
        dest.write_bytes(content)
        saved_paths.append(dest)

    index, chunks, sources = ingest.build_or_update_index(saved_paths)
    return {"ok": True, "chunks_indexed": len(chunks)}

@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    try:
        index, chunks, sources = ingest.load_index()
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))

    passages = rag.search(
        index,
        chunks,
        req.question,
        sources=sources,
        filter_source=req.source,   # <- filtro opcional por nombre de archivo
    )
    if not passages:
        raise HTTPException(status_code=404, detail="No hay pasajes relevantes")

    llm = rag._load_llm()
    prompt = rag.build_prompt_clipped(llm, req.question, passages)
    answer = rag.generate_answer(llm, prompt)

    citations = [Citation(id=int(i), score=float(s), text=t[:400]) for i, s, t in passages]
    return AskResponse(answer=answer, citations=citations)
