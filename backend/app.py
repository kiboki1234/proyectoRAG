from pathlib import Path
from typing import List
import mimetypes
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import get_settings
from models import (
    AskRequest, AskResponse, Citation, HealthResponse, 
    StatsResponse, IngestResponse, ErrorResponse, FeedbackRequest
)
from logger import setup_app_logger, get_logger
from cache import get_query_cache
from conversation import ConversationManager
from feedback import FeedbackManager
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

# Conversation Manager
conversation_manager = ConversationManager(
    storage_dir=settings.data_dir / "conversations"
)

# Feedback Manager
feedback_manager = FeedbackManager(
    storage_path=settings.data_dir / "feedback" / "feedback.jsonl"
)

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

# Exception handlers globales
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler para errores de validación (422)"""
    app_logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "message": "Los datos enviados no son válidos",
            "details": exc.errors(),
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler para HTTPExceptions (4xx, 5xx)"""
    app_logger.warning(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global para errores no manejados (500)"""
    app_logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "Error interno del servidor",
            "details": str(exc) if settings.debug else None,
            "timestamp": datetime.now().isoformat()
        }
    )

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
        # Si no existe el índice, devolver estadísticas vacías
        app_logger.info("Índice no encontrado, devolviendo estadísticas vacías")
        return StatsResponse(
            total_documents=0,
            total_chunks=0,
            avg_chunk_size=0.0,
            index_dimension=None,
            embedder_model=settings.embedding_model_id
        )
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
    También incluye archivos huérfanos (existen físicamente pero no están indexados).
    Útil para ver qué hay en el corpus.
    """
    try:
        # Cargar índice si existe
        indexed_docs = {}
        try:
            index, chunks, sources, pages = ingest.load_index_safe()
            
            # Agrupar chunks por documento
            for i, (chunk, source) in enumerate(zip(chunks, sources)):
                if source not in indexed_docs:
                    indexed_docs[source] = {
                        "name": source,
                        "chunks": 0,
                        "total_chars": 0,
                        "has_pages": False,
                        "indexed": True
                    }
                indexed_docs[source]["chunks"] += 1
                indexed_docs[source]["total_chars"] += len(chunk)
                if pages[i] is not None:
                    indexed_docs[source]["has_pages"] = True
        except FileNotFoundError:
            # No hay índice, solo archivos físicos
            pass
        
        # Buscar archivos físicos (incluyendo huérfanos)
        physical_files = set()
        for pattern in ("*.pdf", "*.md", "*.markdown", "*.txt"):
            for p in settings.docs_dir.glob(pattern):
                if p.is_file():
                    physical_files.add(p.name)
        
        # Agregar archivos huérfanos (existen físicamente pero no en índice)
        for filename in physical_files:
            if filename not in indexed_docs:
                indexed_docs[filename] = {
                    "name": filename,
                    "chunks": 0,
                    "total_chars": 0,
                    "has_pages": False,
                    "indexed": False  # Marcado como no indexado
                }
        
        # Convertir a lista ordenada
        documents = sorted(indexed_docs.values(), key=lambda x: x["name"])
        
        # Contar chunks totales
        total_chunks = sum(d["chunks"] for d in documents)
        
        return {
            "total_documents": len(documents),
            "total_chunks": total_chunks,
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
    Lista nombres de archivos disponibles SOLO si existen físicamente en docs/.
    No incluye documentos borrados que aún están en el índice.
    """
    try:
        names = set()
        # Solo archivos del filesystem (documentos que realmente existen)
        for pattern in ("*.pdf", "*.md", "*.markdown", "*.txt"):
            for p in settings.docs_dir.glob(pattern):
                if p.is_file():
                    names.add(p.name)
        
        # 🔧 FIX: NO incluir archivos solo del índice
        # Esto previene mostrar documentos que fueron borrados pero aún están en meta.json

        return {"sources": sorted(names)}
    except Exception as e:
        app_logger.error(f"Error listando fuentes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    """
    Elimina un documento completamente:
    1. Archivo físico de docs/
    2. Chunks del índice (meta.json)
    3. Reconstruye índice FAISS
    """
    try:
        doc_path = settings.docs_dir / filename
        
        # Verificar que existe
        if not doc_path.exists():
            raise HTTPException(status_code=404, detail=f"Documento '{filename}' no encontrado")
        
        app_logger.info(f"🗑️  Eliminando documento: {filename}")
        
        # 1. Eliminar archivo físico
        doc_path.unlink()
        app_logger.info(f"✅ Archivo eliminado: {filename}")
        
        # 2. Limpiar índice
        meta_path = settings.store_dir / "meta.json"
        chunks_removed = 0
        
        if meta_path.exists():
            import json
            meta = json.loads(meta_path.read_text(encoding='utf-8'))
            
            # Contar chunks antes
            old_count = len(meta['chunks'])
            
            # Filtrar chunks del documento eliminado
            keep_indices = [
                i for i, s in enumerate(meta['sources'])
                if s != filename
            ]
            
            meta['chunks'] = [meta['chunks'][i] for i in keep_indices]
            meta['sources'] = [meta['sources'][i] for i in keep_indices]
            meta['pages'] = [meta['pages'][i] for i in keep_indices]
            
            chunks_removed = old_count - len(meta['chunks'])
            
            # Guardar meta.json actualizado
            meta_path.write_text(
                json.dumps(meta, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
            
            app_logger.info(f"✅ Eliminados {chunks_removed} chunks del índice")
        
        # 3. Reconstruir índice FAISS
        faiss_path = settings.store_dir / "faiss.index"
        if faiss_path.exists():
            faiss_path.unlink()
            app_logger.info("✅ Índice FAISS marcado para reconstrucción")
        
        return {
            "success": True,
            "message": f"Documento '{filename}' eliminado correctamente",
            "chunks_removed": chunks_removed
        }
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error eliminando documento: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/documents")
async def delete_all_documents():
    """
    Elimina TODOS los documentos:
    1. Todos los archivos de docs/
    2. Todo el índice (meta.json y faiss.index)
    """
    try:
        app_logger.warning("🗑️  Eliminando TODOS los documentos")
        
        # Contar documentos
        doc_count = 0
        for pattern in ("*.pdf", "*.md", "*.markdown", "*.txt"):
            for p in settings.docs_dir.glob(pattern):
                if p.is_file():
                    p.unlink()
                    doc_count += 1
        
        # Eliminar índices
        meta_path = settings.store_dir / "meta.json"
        faiss_path = settings.store_dir / "faiss.index"
        
        if meta_path.exists():
            meta_path.unlink()
        if faiss_path.exists():
            faiss_path.unlink()
        
        app_logger.info(f"✅ Eliminados {doc_count} documentos y los índices")
        
        return {
            "success": True,
            "message": f"Eliminados {doc_count} documentos correctamente",
            "documents_removed": doc_count
        }
        
    except Exception as e:
        app_logger.error(f"Error eliminando todos los documentos: {e}", exc_info=True)
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
    
    Nuevas features:
    - source=None o "*" busca en TODO el corpus con diversificación
    - temperature auto-detectada según tipo de pregunta (o manual)
    - search_mode configurable: single/multi/auto
    """
    try:
        # Intentar obtener del caché
        cached_response = None
        if query_cache:
            cached_response = query_cache.get(req.question, req.source)
            if cached_response:
                app_logger.info(f"✅ Cache hit para: {req.question[:50]}...")
                # Marcar como cacheado
                if isinstance(cached_response, dict):
                    cached_response['cached'] = True
                    return AskResponse(**cached_response)
                return cached_response
        
        app_logger.info(f"🔍 Query: {req.question[:100]}... | Source: {req.source or 'TODO EL CORPUS'}")
        
        # Carga segura del índice
        try:
            index, chunks, sources, pages = ingest.load_index_safe()
        except FileNotFoundError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Determinar modo de búsqueda
        search_mode = req.search_mode or "auto"
        if search_mode == "auto":
            # Si hay source específico → single, sino → multi
            search_mode = "single" if req.source else "multi"
        
        diversify = (search_mode == "multi")
        
        app_logger.info(
            f"🔍 Búsqueda RAG - Question: {req.question[:100]}... | "
            f"Filter: {req.source or 'TODO'} | Search mode: {search_mode} | "
            f"Total docs: {len(set(sources))}"
        )

        # Recuperación híbrida + rerank
        k_value = settings.top_k

        passages = rag.search(
            index,
            chunks,
            req.question,
            k=k_value,
            sources=sources,
            filter_source=req.source,
            diversify=diversify,
        )
        
        app_logger.info(
            f"🎯 Recuperados {len(passages)} pasajes "
            f"(k={k_value}, diversify={diversify}, "
            f"fuentes: {len(set(sources[p[0]] for p in passages))})"
        )
        
        if not passages:
            detail = f"No hay pasajes relevantes en {'el documento ' + req.source if req.source else 'el corpus'} para esta pregunta"
            app_logger.warning(f"⚠️  Sin resultados: {detail}")
            raise HTTPException(status_code=404, detail=detail)

        # Auto-detectar temperatura si no se especificó
        temperature = req.temperature
        if temperature is None:
            temperature = rag._auto_detect_temperature(req.question)
            app_logger.info(f"🌡️  Temperatura auto-detectada: {temperature}")
        else:
            app_logger.info(f"🌡️  Temperatura manual: {temperature}")

        # LLM y prompt con clipping por tokens reales
        llm = rag._load_llm()
        prompt = rag.build_prompt_clipped(llm, req.question, passages)
        answer = rag.generate_answer(llm, prompt, temp=temperature)

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

        response = AskResponse(
            answer=answer,
            citations=citations,
            cached=False,
            search_mode_used=search_mode,
            temperature_used=temperature
        )
        
        # Cachear la respuesta
        if query_cache:
            query_cache.set(req.question, response, req.source)
            app_logger.info(f"💾 Respuesta cacheada")
        
        app_logger.info(f"✅ Respuesta generada con {len(citations)} citas (temp={temperature})")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"Error en /ask: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@app.post("/ask/stream")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def ask_stream(request: Request, req: AskRequest):
    """
    Versión streaming del endpoint /ask.
    Devuelve tokens uno por uno mediante Server-Sent Events (SSE).
    
    Formato del stream:
    - event: token → data: {"token": "...", "done": false}
    - event: citations → data: [citation1, citation2, ...]
    - event: metadata → data: {"cached": false, "search_mode": "single", "temperature": 0.0}
    - event: done → data: {"done": true}
    """
    try:
        # Verificar caché primero
        if query_cache:
            cached = query_cache.get(req.question, req.source)
            if cached:
                app_logger.info(f"✅ Cache hit (stream) para: {req.question[:50]}...")
                # Enviar respuesta cacheada de golpe
                async def send_cached():
                    import json
                    # Metadata
                    yield f"event: metadata\ndata: {json.dumps({'cached': True, 'search_mode_used': getattr(cached, 'search_mode_used', 'single'), 'temperature_used': getattr(cached, 'temperature_used', 0.0)})}\n\n"
                    # Respuesta completa
                    answer = cached.answer if hasattr(cached, 'answer') else str(cached)
                    for char in answer:
                        yield f"event: token\ndata: {json.dumps({'token': char, 'done': False})}\n\n"
                    # Citas
                    citations = cached.citations if hasattr(cached, 'citations') else []
                    if citations:
                        yield f"event: citations\ndata: {json.dumps([c.dict() if hasattr(c, 'dict') else c for c in citations])}\n\n"
                    # Fin
                    yield f"event: done\ndata: {json.dumps({'done': True})}\n\n"
                return StreamingResponse(send_cached(), media_type="text/event-stream")
        
        # Generar respuesta streaming
        async def generate():
            import json
            try:
                # Cargar índice
                index, chunks, sources, pages = ingest.load_index_safe()
                
                # Determinar modo de búsqueda
                search_mode = req.search_mode or "auto"
                if search_mode == "auto":
                    search_mode = "single" if req.source else "multi"
                diversify = (search_mode == "multi")
                
                # Recuperar pasajes
                passages = rag.search(
                    index, chunks, req.question,
                    k=settings.top_k,
                    sources=sources,
                    filter_source=req.source,
                    diversify=diversify,
                )
                
                if not passages:
                    yield f"event: error\ndata: {json.dumps({'error': 'No se encontraron pasajes relevantes'})}\n\n"
                    return
                
                # Auto-detectar temperatura
                temperature = req.temperature if req.temperature is not None else rag._auto_detect_temperature(req.question)
                
                # Enviar metadata
                yield f"event: metadata\ndata: {json.dumps({'cached': False, 'search_mode_used': search_mode, 'temperature_used': temperature})}\n\n"
                
                # Generar respuesta token por token
                llm = rag._load_llm()
                prompt = rag.build_prompt_clipped(llm, req.question, passages)
                
                # Streaming nativo de llama.cpp
                full_answer = ""
                for output in llm(
                    prompt,
                    max_tokens=rag._safe_max_new_tokens(llm, prompt),
                    temperature=temperature,
                    stop=["</s>"],
                    stream=True
                ):
                    token = output["choices"][0]["text"]
                    full_answer += token
                    yield f"event: token\ndata: {json.dumps({'token': token, 'done': False})}\n\n"
                
                # Citas
                citations_data = []
                for i, s, t in passages:
                    src_name = sources[i] if 0 <= i < len(sources) else None
                    pg = pages[i] if 0 <= i < len(pages) else None
                    citations_data.append({
                        "id": int(i),
                        "score": float(s),
                        "text": t[:400],
                        "page": pg,
                        "source": src_name
                    })
                
                yield f"event: citations\ndata: {json.dumps(citations_data)}\n\n"
                
                # Cachear respuesta completa
                if query_cache and full_answer:
                    response_obj = AskResponse(
                        answer=full_answer.strip(),
                        citations=[Citation(**c) for c in citations_data],
                        cached=False,
                        search_mode_used=search_mode,
                        temperature_used=temperature
                    )
                    query_cache.set(req.question, response_obj, req.source)
                
                # Fin
                yield f"event: done\ndata: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                app_logger.error(f"Error en streaming: {e}", exc_info=True)
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(generate(), media_type="text/event-stream")
        
    except Exception as e:
        app_logger.error(f"Error en /ask/stream: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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


# -------------------------
# Conversaciones
# -------------------------
@app.post("/conversations/{conv_id}")
async def save_conversation(conv_id: str, messages: List[dict]):
    """
    Guarda una conversación completa.
    
    Args:
        conv_id: ID único de la conversación
        messages: Lista de mensajes
    
    Returns:
        Status de la operación
    """
    try:
        conversation_manager.save_conversation(conv_id, messages)
        return {"status": "saved", "conv_id": conv_id, "message_count": len(messages)}
    except Exception as e:
        app_logger.error(f"Error saving conversation {conv_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/conversations/{conv_id}")
async def get_conversation(conv_id: str):
    """
    Recupera una conversación por ID.
    
    Args:
        conv_id: ID de la conversación
    
    Returns:
        Conversación completa o 404
    """
    conv = conversation_manager.load_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@app.get("/conversations")
async def list_conversations(limit: int = 50):
    """
    Lista todas las conversaciones (metadata).
    
    Args:
        limit: Número máximo de conversaciones
    
    Returns:
        Lista de conversaciones con metadata
    """
    try:
        return conversation_manager.list_conversations(limit=limit)
    except Exception as e:
        app_logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str):
    """
    Elimina una conversación.
    
    Args:
        conv_id: ID de la conversación
    
    Returns:
        Status de la operación
    """
    deleted = conversation_manager.delete_conversation(conv_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted", "conv_id": conv_id}


# -------------------------
# Feedback
# -------------------------
@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Registra feedback del usuario sobre una respuesta.
    
    Args:
        request: Datos del feedback (message_id, feedback, question, answer, metadata)
    
    Returns:
        Status de la operación
    """
    try:
        feedback_manager.save_feedback(
            request.message_id, 
            request.feedback, 
            request.question, 
            request.answer, 
            request.metadata
        )
        return {
            "status": "ok", 
            "message_id": request.message_id, 
            "feedback": request.feedback
        }
    except Exception as e:
        app_logger.error(f"Error saving feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/feedback/stats")
async def get_feedback_stats():
    """
    Obtiene estadísticas de feedback.
    
    Returns:
        Estadísticas agregadas de feedback
    """
    try:
        return feedback_manager.get_stats()
    except Exception as e:
        app_logger.error(f"Error getting feedback stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/feedback/recent")
async def get_recent_feedback(limit: int = 50):
    """
    Obtiene los últimos feedback registrados.
    
    Args:
        limit: Número máximo de feedback
    
    Returns:
        Lista de feedback recientes
    """
    try:
        return feedback_manager.get_recent_feedback(limit=limit)
    except Exception as e:
        app_logger.error(f"Error getting recent feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))
