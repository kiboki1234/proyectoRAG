"""
Tests unitarios para el sistema de caché.
"""
import pytest
import time
from backend.cache import QueryCache, CacheEntry


class TestCacheEntry:
    """Tests para CacheEntry"""
    
    def test_entry_creation(self):
        """Test creación de entrada"""
        entry = CacheEntry("test_value", ttl_seconds=10)
        assert entry.value == "test_value"
        assert not entry.is_expired()
    
    def test_entry_expiration(self):
        """Test expiración de entrada"""
        entry = CacheEntry("test_value", ttl_seconds=1)
        assert not entry.is_expired()
        time.sleep(1.1)
        assert entry.is_expired()
    
    def test_entry_age(self):
        """Test edad de entrada"""
        entry = CacheEntry("test_value", ttl_seconds=10)
        time.sleep(0.5)
        age = entry.get_age_seconds()
        assert 0.4 < age < 0.6


class TestQueryCache:
    """Tests para QueryCache"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.cache = QueryCache(max_size=5, default_ttl=10)
    
    def test_cache_set_and_get(self):
        """Test básico de set/get"""
        self.cache.set("test question", "test answer")
        result = self.cache.get("test question")
        assert result == "test answer"
    
    def test_cache_miss(self):
        """Test cache miss"""
        result = self.cache.get("non-existent")
        assert result is None
    
    def test_cache_with_source(self):
        """Test con filtro de source"""
        self.cache.set("question", "answer1", source="doc1.pdf")
        self.cache.set("question", "answer2", source="doc2.pdf")
        
        result1 = self.cache.get("question", source="doc1.pdf")
        result2 = self.cache.get("question", source="doc2.pdf")
        
        assert result1 == "answer1"
        assert result2 == "answer2"
    
    def test_cache_expiration(self):
        """Test expiración de caché"""
        cache = QueryCache(max_size=5, default_ttl=1)
        cache.set("question", "answer")
        
        # Antes de expirar
        assert cache.get("question") == "answer"
        
        # Después de expirar
        time.sleep(1.1)
        assert cache.get("question") is None
    
    def test_cache_lru_eviction(self):
        """Test evicción LRU cuando se alcanza max_size"""
        cache = QueryCache(max_size=3, default_ttl=100)
        
        cache.set("q1", "a1")
        cache.set("q2", "a2")
        cache.set("q3", "a3")
        
        # Cache lleno, agregar uno más debe eliminar el más antiguo
        time.sleep(0.1)
        cache.set("q4", "a4")
        
        assert cache.get("q1") is None  # Evicted
        assert cache.get("q2") == "a2"
        assert cache.get("q3") == "a3"
        assert cache.get("q4") == "a4"
    
    def test_cache_clear(self):
        """Test limpieza completa del caché"""
        self.cache.set("q1", "a1")
        self.cache.set("q2", "a2")
        
        self.cache.clear()
        
        assert self.cache.get("q1") is None
        assert self.cache.get("q2") is None
        stats = self.cache.get_stats()
        assert stats["size"] == 0
    
    def test_cache_invalidate(self):
        """Test invalidación específica"""
        self.cache.set("q1", "a1")
        self.cache.set("q2", "a2")
        
        self.cache.invalidate("q1")
        
        assert self.cache.get("q1") is None
        assert self.cache.get("q2") == "a2"
    
    def test_cache_stats(self):
        """Test estadísticas del caché"""
        # Generar hits y misses
        self.cache.set("q1", "a1")
        
        self.cache.get("q1")  # Hit
        self.cache.get("q1")  # Hit
        self.cache.get("q2")  # Miss
        
        stats = self.cache.get_stats()
        
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["size"] == 1
        assert stats["max_size"] == 5
        assert 60 < stats["hit_rate"] < 70  # ~66.67%
    
    def test_cleanup_expired(self):
        """Test limpieza de entradas expiradas"""
        cache = QueryCache(max_size=10, default_ttl=1)
        
        cache.set("q1", "a1")
        cache.set("q2", "a2", ttl=10)  # Esta no expira pronto
        
        time.sleep(1.1)
        
        removed = cache.cleanup_expired()
        
        assert removed == 1
        assert cache.get("q1") is None
        assert cache.get("q2") == "a2"
    
    def test_case_insensitive_questions(self):
        """Test que las preguntas son case-insensitive"""
        self.cache.set("Test Question", "answer")
        
        result1 = self.cache.get("test question")
        result2 = self.cache.get("TEST QUESTION")
        
        assert result1 == "answer"
        assert result2 == "answer"
