"""
Sistema de caché en memoria con TTL para respuestas de queries.
Implementa un LRU cache con expiración temporal.
"""
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
import hashlib
import json
from threading import Lock


class CacheEntry:
    """Entrada individual del caché con timestamp"""
    
    def __init__(self, value: Any, ttl_seconds: int):
        self.value = value
        self.created_at = datetime.utcnow()
        self.expires_at = self.created_at + timedelta(seconds=ttl_seconds)
    
    def is_expired(self) -> bool:
        """Verifica si la entrada ha expirado"""
        return datetime.utcnow() > self.expires_at
    
    def get_age_seconds(self) -> float:
        """Retorna la edad de la entrada en segundos"""
        return (datetime.utcnow() - self.created_at).total_seconds()


class QueryCache:
    """
    Caché thread-safe con TTL para queries del sistema RAG.
    Implementa un LRU simple con límite de tamaño.
    """
    
    def __init__(self, max_size: int = 100, default_ttl: int = 300):
        """
        Args:
            max_size: Número máximo de entradas en caché
            default_ttl: TTL por defecto en segundos (5 minutos)
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = Lock()
        self._hits = 0
        self._misses = 0
    
    def _generate_key(self, question: str, source: Optional[str] = None) -> str:
        """
        Genera una clave única para la query.
        
        Args:
            question: Pregunta del usuario
            source: Fuente opcional
        
        Returns:
            Hash SHA256 de la combinación pregunta+fuente
        """
        data = {
            "question": question.strip().lower(),
            "source": (source or "").strip().lower()
        }
        key_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(key_str.encode('utf-8')).hexdigest()
    
    def get(self, question: str, source: Optional[str] = None) -> Optional[Any]:
        """
        Obtiene un valor del caché si existe y no ha expirado.
        
        Args:
            question: Pregunta del usuario
            source: Fuente opcional
        
        Returns:
            Valor cacheado o None si no existe o expiró
        """
        key = self._generate_key(question, source)
        
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                return None
            
            if entry.is_expired():
                # Eliminar entrada expirada
                del self._cache[key]
                self._misses += 1
                return None
            
            self._hits += 1
            return entry.value
    
    def set(
        self, 
        question: str, 
        value: Any, 
        source: Optional[str] = None,
        ttl: Optional[int] = None
    ):
        """
        Almacena un valor en el caché.
        
        Args:
            question: Pregunta del usuario
            value: Valor a cachear
            source: Fuente opcional
            ttl: TTL personalizado en segundos (usa default_ttl si es None)
        """
        key = self._generate_key(question, source)
        ttl = ttl or self._default_ttl
        
        with self._lock:
            # Implementar política LRU simple: eliminar la entrada más antigua si llegamos al límite
            if len(self._cache) >= self._max_size and key not in self._cache:
                self._evict_oldest()
            
            self._cache[key] = CacheEntry(value, ttl)
    
    def _evict_oldest(self):
        """Elimina la entrada más antigua del caché"""
        if not self._cache:
            return
        
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at
        )
        del self._cache[oldest_key]
    
    def invalidate(self, question: str, source: Optional[str] = None):
        """
        Invalida una entrada específica del caché.
        
        Args:
            question: Pregunta del usuario
            source: Fuente opcional
        """
        key = self._generate_key(question, source)
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self):
        """Limpia todo el caché"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def cleanup_expired(self) -> int:
        """
        Elimina todas las entradas expiradas.
        
        Returns:
            Número de entradas eliminadas
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estadísticas del caché.
        
        Returns:
            Diccionario con estadísticas
        """
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0.0
            
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 2),
                "default_ttl": self._default_ttl
            }


# Instancia global del caché
_query_cache: Optional[QueryCache] = None


def get_query_cache(max_size: int = 100, ttl: int = 300) -> QueryCache:
    """
    Obtiene o crea la instancia global del caché.
    
    Args:
        max_size: Tamaño máximo del caché
        ttl: TTL por defecto en segundos
    
    Returns:
        Instancia del QueryCache
    """
    global _query_cache
    if _query_cache is None:
        _query_cache = QueryCache(max_size=max_size, default_ttl=ttl)
    return _query_cache
