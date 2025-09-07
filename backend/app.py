from __future__ import annotations
from pathlib import Path
from typing import List
import mimetypes
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import DOCS_DIR, STORE_DIR
from models import AskRequest, AskResponse, Citation
import ingest
import rag
from fastapi.responses import FileResponse
mimetypes.add_type("text/javascript", ".mjs")
mimetypes.add_type("application/javascript", ".mjs")  # por si algún browser prefiere este
# (opcional) los .map como JSON
mimetypes.add_type("application/json", ".map")

app = FastAPI(title="RAG Offline Soberano")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PDFJS_DIR = (Path(__file__).resolve().parent / "assets" / "pdfjs").resolve()
app.mount("/pdfjs", StaticFiles(directory=PDFJS_DIR, html=True), name="pdfjs")
# === NUEVO: montar archivos estáticos para visualizar PDFs ===
# Servirá cualquier archivo en backend/data/docs como: GET /files/<nombre.pdf>
app.mount("/files", StaticFiles(directory=DOCS_DIR, html=False), name="files")
@app.get("/file/{name:path}")
def serve_file(name: str):
    docs_root = DOCS_DIR.resolve()
    target = (DOCS_DIR / name).resolve()

    # Evita path traversal
    try:
        target.relative_to(docs_root)
    except Exception:
        raise HTTPException(status_code=400, detail="Ruta inválida (fuera de docs).")

    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail=f"No encontrado: {name}")

    # Tipo MIME simple (pdf/otros)
    media = "application/pdf" if target.suffix.lower() == ".pdf" else "application/octet-stream"
    # inline para que se vea en el navegador / iframe
    headers = {"Content-Disposition": f'inline; filename="{target.name}"'}
    return FileResponse(path=str(target), media_type=media, headers=headers)

@app.on_event("startup")
def ensure_dirs():
    for p in [DOCS_DIR, STORE_DIR]:
        p.mkdir(parents=True, exist_ok=True)


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

    index, chunks, sources, pages = ingest.build_or_update_index(saved_paths)
    return {"ok": True, "chunks_indexed": len(chunks)}


@app.post("/ingest/all")
def ingest_all_from_folder():
    files = []
    for pattern in ("*.pdf", "*.md", "*.markdown", "*.txt"):
        files.extend((DOCS_DIR).glob(pattern))
    files = [f for f in files if f.is_file()]
    if not files:
        raise HTTPException(status_code=400, detail="No hay archivos en la carpeta docs/")
    index, chunks, sources, pages = ingest.build_or_update_index(files)
    return {"ok": True, "files": [f.name for f in files], "chunks_indexed": len(chunks)}


@app.get("/sources")
def list_sources():
    names = set()
    # 1) del filesystem
    for pattern in ("*.pdf", "*.md", "*.markdown", "*.txt"):
        for p in DOCS_DIR.glob(pattern):
            if p.is_file():
                names.add(p.name)
    # 2) del índice (si existe)
    try:
        _, _, sources, _ = ingest.load_index()
        for s in sources:
            if s:
                names.add(s)
    except FileNotFoundError:
        pass

    return {"sources": sorted(names)}


@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    try:
        index, chunks, sources, pages = ingest.load_index()
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))

    passages = rag.search(
        index,
        chunks,
        req.question,
        sources=sources,
        filter_source=req.source,
    )
    if not passages:
        raise HTTPException(status_code=404, detail="No hay pasajes relevantes")

    llm = rag._load_llm()
    prompt = rag.build_prompt_clipped(llm, req.question, passages)
    answer = rag.generate_answer(llm, prompt)

    citations = []
    for i, s, t in passages:
        # fuente (nombre del archivo) y página
        src_name = sources[i] if 0 <= i < len(sources) else None
        pg_raw = pages[i] if 0 <= i < len(pages) else None
        # Asegura página base-1 para el visor
        pg = int(pg_raw) + 1 if isinstance(pg_raw, int) and pg_raw >= 0 else None

        citations.append(
            Citation(
                id=int(i),
                score=float(s),
                text=t[:400],
                page=pg,
                source=src_name
            )
        )

    return AskResponse(answer=answer, citations=citations)


@app.get("/debug/paths")
def debug_paths():
    return {
        "docs_dir": str(DOCS_DIR.resolve()),
        "store_dir": str(STORE_DIR.resolve()),
    }
@app.get("/debug/pdfjs")
def debug_pdfjs():
    base = PDFJS_DIR.resolve()
    web = base / "web"
    viewer = web / "viewer.html"
    build = base / "build"
    return {
        "PDFJS_DIR": str(base),
        "exists": base.exists(),
        "web_exists": web.exists(),
        "viewer_exists": viewer.exists(),
        "build_exists": build.exists(),
        "web_children": sorted([p.name for p in web.iterdir()], key=str.lower) if web.exists() else [],
    }