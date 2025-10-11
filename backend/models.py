from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class AskRequest(BaseModel):
    """Request model para queries al sistema RAG"""
    question: str = Field(
        ..., 
        min_length=3, 
        max_length=500,
        description="Pregunta del usuario"
    )
    source: Optional[str] = Field(
        None, 
        max_length=255,
        description="Nombre (o parte) del archivo a filtrar. None o '*' busca en todo el corpus"
    )
    temperature: Optional[float] = Field(
        None,
        ge=0.0,
        le=2.0,
        description="Temperatura para generación (0.0=factual, 0.7=creativo). Auto-detecta si no se especifica"
    )
    search_mode: Optional[str] = Field(
        "auto",
        description="Modo de búsqueda: 'single' (un doc), 'multi' (varios docs balanceados), 'auto' (detecta por source)"
    )
    
    @field_validator('question')
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Valida que la pregunta no esté vacía después de strip"""
        v = v.strip()
        if not v:
            raise ValueError("La pregunta no puede estar vacía")
        return v
    
    @field_validator('source')
    @classmethod
    def validate_source(cls, v: Optional[str]) -> Optional[str]:
        """Valida y sanitiza el nombre del archivo"""
        if v is None or v == "*":
            return None  # Buscar en todo el corpus
        v = v.strip()
        if not v:
            return None
        # Sanitización básica para prevenir path traversal
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError("Nombre de archivo inválido")
        return v
    
    @field_validator('search_mode')
    @classmethod
    def validate_search_mode(cls, v: Optional[str]) -> str:
        """Valida el modo de búsqueda"""
        if v is None:
            return "auto"
        v = v.lower().strip()
        if v not in ["single", "multi", "auto"]:
            raise ValueError("search_mode debe ser 'single', 'multi' o 'auto'")
        return v

class Citation(BaseModel):
    """Modelo de citación de un fragmento de documento"""
    id: int = Field(..., ge=0, description="ID del chunk en el índice")
    score: float = Field(..., ge=0.0, le=1.0, description="Score de relevancia")
    text: str = Field(..., max_length=1000, description="Texto del fragmento")
    page: Optional[int] = Field(None, ge=1, description="Número de página (base 1)")
    source: Optional[str] = Field(None, max_length=255, description="Nombre del archivo fuente")

class AskResponse(BaseModel):
    """Response model para queries al sistema RAG"""
    answer: str = Field(..., description="Respuesta generada por el LLM")
    citations: List[Citation] = Field(default_factory=list, description="Lista de citas")
    cached: bool = Field(default=False, description="Si la respuesta vino del caché")
    search_mode_used: str = Field(default="single", description="Modo de búsqueda utilizado")
    temperature_used: float = Field(default=0.0, description="Temperatura utilizada en generación")

class HealthResponse(BaseModel):
    """Response model para health check"""
    status: str = Field(..., description="Estado del servicio: ok, degraded, error")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    llm_loaded: bool = Field(..., description="Si el LLM está cargado en memoria")
    index_exists: bool = Field(..., description="Si el índice FAISS existe")
    chunks_count: int = Field(..., ge=0, description="Número de chunks indexados")
    version: str = Field(default="1.0.0", description="Versión del servicio")

class StatsResponse(BaseModel):
    """Response model para estadísticas del sistema"""
    total_documents: int = Field(..., ge=0, description="Total de documentos únicos")
    total_chunks: int = Field(..., ge=0, description="Total de chunks indexados")
    avg_chunk_size: float = Field(..., ge=0.0, description="Tamaño promedio de chunks")
    index_dimension: Optional[int] = Field(None, description="Dimensión de los embeddings")
    embedder_model: str = Field(..., description="Modelo de embeddings utilizado")

class IngestResponse(BaseModel):
    """Response model para ingesta de documentos"""
    ok: bool = Field(..., description="Si la operación fue exitosa")
    chunks_indexed: int = Field(..., ge=0, description="Chunks nuevos indexados")
    files: List[str] = Field(..., description="Nombres de archivos procesados")
    duplicates_skipped: int = Field(default=0, ge=0, description="Chunks duplicados omitidos")

class ErrorResponse(BaseModel):
    """Response model para errores"""
    detail: str = Field(..., description="Descripción del error")
    error_type: str = Field(default="generic", description="Tipo de error")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
