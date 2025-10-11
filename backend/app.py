from pathlib import Path
from typing import List
import mimetypes
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import get_settings
from models import (
    AskRequest, AskResponse, Citation, HealthResponse, 
    StatsResponse, IngestResponse, ErrorResponse
)
from logger import setup_app_logger, get_logger
from cache import get_query_cache
import ingest
import rag
import numpy as np

# Asegurar tipos para módulos ES (.mjs) y sourcemaps
mimetypes.add_type("text/javascript", ".mjs")
mimetypes.add_type("application/javascript", ".mjs")
mimetypes.add_type("application/json", ".map")

# Configuración
settings = get_settings()

# Logging
logger = setup_app_logger(
    log_file=settings.logs_dir / settings.log_file,
    log_level=settings.log_level
)
app_logger = get_logger("rag_offline.app")

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Cache
query_cache = get_query_cache(
    max_size=100,
    ttl=settings.cache_ttl_seconds
) if settings.enable_cache else None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida de la aplicación"""
    app_logger.info("🚀 Iniciando RAG Offline Soberano...")
    app_logger.info(f"📁 Directorio de docs: {settings.docs_dir}")
    app_logger.info(f"🗄️  Directorio de store: {settings.store_dir}")
    app_logger.info(f"🤖 Modelo LLM: {settings.llm_model_full_path}")
    app_logger.info(f"📊 Embedder: {settings.embedding_model_id}")
    
    # Pre-cargar LLM si es necesario
    try:
        if settings.llm_model_full_path.exists():
            app_logger.info("⏳ Cargando modelo LLM...")
            rag._load_llm()
            app_logger.info("✅ LLM cargado correctamente")
        else:
            app_logger.warning(f"⚠️  Modelo LLM no encontrado en: {settings.llm_model_full_path}")
    except Exception as e:
        app_logger.error(f"❌ Error cargando LLM: {e}")
    
    yield
    
    # Cleanup
    app_logger.info("🛑 Deteniendo aplicación...")
    if query_cache:
        stats = query_cache.get_stats()
        app_logger.info(f"📊 Stats de caché: {stats}")


app = FastAPI(
    title="RAG Offline Soberano",
    description="Sistema RAG local con FAISS + llama.cpp",
    version="1.0.0",
    lifespan=lifespan
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS con origins específicos
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === PDF.js estático dentro del backend ===
PDFJS_DIR = (Path(__file__).resolve().parent / "assets" / "pdfjs").resolve()
app.mount("/pdfjs", StaticFiles(directory=PDFJS_DIR, html=True), name="pdfjs")

# Servir archivos de docs (para descarga directa)
app.mount("/files", StaticFiles(directory=settings.docs_dir, html=False), name="files")


@app.get("/file/{name:path}")
def serve_file(name: str):
    """
    Sirve un archivo de /backend/data/docs por nombre exacto.
    Se usa como origen del visor PDF.js: /pdfjs/web/viewer.html?file=<URL-encoded>
    """
    docs_root = settings.docs_dir.resolve()
    target = (settings.docs_dir / name).resolve()

    # Evitar path traversal
    try:
        target.relative_to(docs_root)
    except Exception:
        raise HTTPException(status_code=400, detail="Ruta inválida (fuera de docs).")

    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail=f"No encontrado: {name}")

    media = "application/pdf" if target.suffix.lower() == ".pdf" else "application/octet-stream"
    headers = {"Content-Disposition": f'inline; filename="{target.name}"'}
    return FileResponse(path=str(target), media_type=media, headers=headers)


@app.on_event("startup")
def ensure_dirs():
    """Asegurar que existen los directorios necesarios"""
    settings.ensure_directories()


@app.get("/")
def root():
    return {"ok": True, "service": "rag-offline-soberano", "version": "1.0.0"}


# -------------------------
# Health & Stats
# -------------------------
@app.get("/health", response_model=HealthResponse)
def health_check():
    """
    Health check endpoint para monitoreo.
    """
    try:
        llm_loaded = rag._LLM is not None
        index_exists = settings.store_dir.joinpath("faiss.index").exists()
        
        chunks_count = 0
        if index_exists:
            try:
                _, chunks, _, _ = ingest.load_index()
                chunks_count = len(chunks)
            except Exception:
                pass
        
        status = "ok" if (llm_loaded or index_exists) else "degraded"
        
        return HealthResponse(
            status=status,
            llm_loaded=llm_loaded,
            index_exists=index_exists,
            chunks_count=chunks_count,
            version="1.0.0"
        )
    except Exception as e:
        app_logger.error(f"Error en health check: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=StatsResponse)
def get_stats():
    """
    Estadísticas del sistema RAG.
    """
    try:
        index, chunks, sources, _ = ingest.load_index()
        
        unique_sources = len(set(sources))
        avg_size = float(np.mean([len(c) for c in chunks])) if chunks else 0.0
        dim = index.d if hasattr(index, 'd') else None
        
        return StatsResponse(
            total_documents=unique_sources,
            total_chunks=len(chunks),
            avg_chunk_size=round(avg_size, 2),
            index_dimension=dim,
            embedder_model=settings.embedding_model_id
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Índice no encontrado. Ingesta documentos primero.")
    except Exception as e:
        app_logger.error(f"Error obteniendo estadísticas: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cache/stats")
def cache_stats():
    """Estadísticas del caché de queries"""
    if not query_cache:
        return {"enabled": False}
    
    stats = query_cache.get_stats()
    stats["enabled"] = True
    return stats


@app.post("/cache/clear")
def clear_cache():
    """Limpia el caché de queries"""
    if query_cache:
        query_cache.clear()
        app_logger.info("Caché limpiado manualmente")
        return {"ok": True, "message": "Caché limpiado"}
    return {"ok": False, "message": "Caché no habilitado"}


@app.get("/documents")
def list_documents():
    """
    Lista todos los documentos indexados con estadísticas.
    Útil para ver qué hay en el corpus.
    """
    try:
        index, chunks, sources, pages = ingest.load_index_safe()
        
        # Agrupar chunks por documento
        doc_stats = {}
        for i, (chunk, source) in enumerate(zip(chunks, sources)):
            if source not in doc_stats:
                doc_stats[source] = {
                    "name": source,
                    "chunks": 0,
                    "total_chars": 0,
                    "has_pages": False
                }
            doc_stats[source]["chunks"] += 1
            doc_stats[source]["total_chars"] += len(chunk)
            if pages[i] is not None:
                doc_stats[source]["has_pages"] = True
        
        # Convertir a lista ordenada
        documents = sorted(doc_stats.values(), key=lambda x: x["name"])
        
        return {
            "total_documents": len(documents),
            "total_chunks": len(chunks),
            "documents": documents
        }
        
    except FileNotFoundError:
        return {
            "total_documents": 0,
            "total_chunks": 0,
            "documents": []
        }
    except Exception as e:
        app_logger.error(f"Error listando documentos: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------
# Ingesta
# -------------------------
@app.post("/ingest", response_model=IngestResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def ingest_files(request: Request, files: List[UploadFile] = File(...)):
    """
    Sube documentos y actualiza/crea el índice (FAISS + meta enriquecida).
    Validación de tamaño y tipo de archivo.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No se proporcionaron archivos")
    
    saved_paths: List[Path] = []
    
    try:
        for f in files:
            # Validar tamaño
            content = await f.read()
            if len(content) > settings.max_file_size_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=f"Archivo {f.filename} excede el límite de {settings.max_file_size_mb}MB"
                )
            
            # Validar extensión
            ext = Path(f.filename).suffix.lower()
            if ext not in [".pdf", ".md", ".markdown", ".txt"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Tipo no soportado: {ext}. Usa PDF, MD o TXT."
                )
            
            # Guardar archivo
            dest = settings.docs_dir / f.filename
            dest.write_bytes(content)
            saved_paths.append(dest)
            app_logger.info(f"Archivo guardado: {f.filename} ({len(content)} bytes)")
        
        # Indexar
        app_logger.info(f"Iniciando indexación de {len(saved_paths)} archivos...")
        index, chunks, sources, pages = ingest.build_or_update_index(saved_paths)
        
        # Invalidar caché al agregar nuevos documentos
        if query_cache:
            query_cache.clear()
            app_logger.info("Caché invalidado tras ingesta")
        
        app_logger.info(f"✅ Indexación completada: {len(chunks)} chunks")
        
        return IngestResponse(
            ok=True,
            chunks_indexed=len(chunks),
            files=[p.name for p in saved_paths],
            duplicates_skipped=0  # TODO: implementar contador real
        )
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error en ingesta: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error al procesar archivos: {str(e)}")


@app.post("/ingest/all", response_model=IngestResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
def ingest_all_from_folder(request: Request):
    """
    Indexa/reindexa todo lo que esté en /data/docs.
    """
    try:
        files: List[Path] = []
        for pattern in ("*.pdf", "*.md", "*.markdown", "*.txt"):
            files.extend(settings.docs_dir.glob(pattern))
        files = [f for f in files if f.is_file()]
        
        if not files:
            raise HTTPException(status_code=400, detail="No hay archivos en la carpeta docs/")
        
        app_logger.info(f"Indexando {len(files)} archivos desde docs/...")
        index, chunks, sources, pages = ingest.build_or_update_index(files)
        
        # Invalidar caché
        if query_cache:
            query_cache.clear()
        
        app_logger.info(f"✅ Indexación completa: {len(chunks)} chunks")
        
        return IngestResponse(
            ok=True,
            files=[f.name for f in files],
            chunks_indexed=len(chunks),
        )
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error en ingest/all: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sources")
def list_sources():
    """
    Lista nombres de archivos disponibles (en filesystem y/o presentes en el índice).
    """
    try:
        names = set()
        # 1) del filesystem
        for pattern in ("*.pdf", "*.md", "*.markdown", "*.txt"):
            for p in settings.docs_dir.glob(pattern):
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
    except Exception as e:
        app_logger.error(f"Error listando fuentes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------
# Preguntar
# -------------------------
@app.post("/ask", response_model=AskResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def ask(request: Request, req: AskRequest):
    """
    Recupera pasajes relevantes y genera respuesta con el LLM local.
    Respuestas siempre en el idioma de la pregunta.
    Usa caché para queries frecuentes.
    """
    try:
        # Intentar obtener del caché
        if query_cache:
            cached_response = query_cache.get(req.question, req.source)
            if cached_response:
                app_logger.info(f"✅ Cache hit para: {req.question[:50]}...")
                return cached_response
        
        app_logger.info(f"🔍 Query: {req.question[:100]}... | Source: {req.source}")
        
        # Carga segura del índice
        try:
            index, chunks, sources, pages = ingest.load_index_safe()
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Normaliza el filtro por archivo y exigir valor válido
        source_param = (req.source or "").strip()
        if not source_param:
            raise HTTPException(status_code=400, detail="Debes especificar un documento (no se permite 'todo el corpus').")

        app_logger.info(
            f"🔍 Búsqueda RAG - Question: {req.question[:100]}... | Filter: '{source_param}' | Total docs: {len(set(sources))}"
        )

        # Recuperación híbrida + rerank (siempre se requiere un documento específico)
        k_value = settings.top_k

        passages = rag.search(
            index,
            chunks,
            req.question,
            k=k_value,
            sources=sources,
            filter_source=source_param,
            diversify=False,  # No diversificar automáticamente
        )
        
        app_logger.info(
            f"🎯 Recuperados {len(passages)} pasajes "
            f"(k={k_value}, diversify=False, "
            f"fuentes: {len(set(sources[p[0]] for p in passages))})"
        )
        
        if not passages:
            if source_param:
                detail = f"No hay pasajes relevantes en el documento '{source_param}' para esta pregunta"
            else:
                detail = "No hay pasajes relevantes en el corpus para esta pregunta"
            app_logger.warning(f"⚠️  Sin resultados: {detail}")
            raise HTTPException(status_code=404, detail=detail)

        # LLM y prompt con clipping por tokens reales
        llm = rag._load_llm()
        prompt = rag.build_prompt_clipped(llm, req.question, passages)
        answer = rag.generate_answer(llm, prompt, temp=0.0)

        # Citas (manteniendo índices alineados)
        citations: List[Citation] = []
        for i, s, t in passages:
            src_name = sources[i] if 0 <= i < len(sources) else None
            pg = pages[i] if 0 <= i < len(pages) else None
            citations.append(
                Citation(
                    id=int(i),
                    score=float(s),
                    text=t[:400],
                    page=pg,
                    source=src_name
                )
            )

        response = AskResponse(answer=answer, citations=citations)
        
        # Cachear la respuesta
        if query_cache:
            query_cache.set(req.question, response, req.source)
            app_logger.info(f"💾 Respuesta cacheada")
        
        app_logger.info(f"✅ Respuesta generada con {len(citations)} citas")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error en /ask: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# -------------------------
# Debug
# -------------------------
@app.get("/debug/paths")
def debug_paths():
    return {
        "docs_dir": str(settings.docs_dir.resolve()),
        "store_dir": str(settings.store_dir.resolve()),
        "llm_model": str(settings.llm_model_full_path),
        "logs_dir": str(settings.logs_dir)
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
