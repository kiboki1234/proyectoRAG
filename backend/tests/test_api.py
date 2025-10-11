"""
Tests para endpoints de la API usando TestClient de FastAPI.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)


class TestHealthEndpoints:
    """Tests para endpoints de health y stats"""
    
    def test_root_endpoint(self):
        """Test endpoint raíz"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["service"] == "rag-offline-soberano"
        assert "version" in data
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "llm_loaded" in data
        assert "index_exists" in data
        assert "chunks_count" in data
        assert data["status"] in ["ok", "degraded", "error"]
    
    def test_cache_stats(self):
        """Test cache stats endpoint"""
        response = client.get("/cache/stats")
        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data


class TestDebugEndpoints:
    """Tests para endpoints de debug"""
    
    def test_debug_paths(self):
        """Test debug paths endpoint"""
        response = client.get("/debug/paths")
        assert response.status_code == 200
        data = response.json()
        assert "docs_dir" in data
        assert "store_dir" in data
        assert "llm_model" in data
        assert "logs_dir" in data
    
    def test_debug_pdfjs(self):
        """Test debug pdfjs endpoint"""
        response = client.get("/debug/pdfjs")
        assert response.status_code == 200
        data = response.json()
        assert "PDFJS_DIR" in data
        assert "exists" in data


class TestSourcesEndpoint:
    """Tests para endpoint de sources"""
    
    def test_list_sources(self):
        """Test listar sources"""
        response = client.get("/sources")
        assert response.status_code == 200
        data = response.json()
        assert "sources" in data
        assert isinstance(data["sources"], list)


class TestAskEndpoint:
    """Tests para endpoint /ask"""
    
    def test_ask_without_index(self):
        """Test ask sin índice creado (debe fallar)"""
        response = client.post(
            "/ask",
            json={"question": "test question"}
        )
        # Puede ser 400 (no index) o 404 (no passages)
        assert response.status_code in [400, 404, 500]
    
    def test_ask_with_invalid_question(self):
        """Test ask con pregunta inválida"""
        # Pregunta muy corta
        response = client.post(
            "/ask",
            json={"question": "ab"}
        )
        assert response.status_code == 422  # Validation error
    
    def test_ask_with_empty_question(self):
        """Test ask con pregunta vacía"""
        response = client.post(
            "/ask",
            json={"question": "   "}
        )
        assert response.status_code == 422
    
    def test_ask_with_path_traversal_source(self):
        """Test ask con path traversal en source"""
        response = client.post(
            "/ask",
            json={
                "question": "test question",
                "source": "../../../etc/passwd"
            }
        )
        assert response.status_code == 422


class TestIngestEndpoint:
    """Tests para endpoint /ingest"""
    
    def test_ingest_without_files(self):
        """Test ingest sin archivos"""
        response = client.post("/ingest", files=[])
        assert response.status_code == 422  # FastAPI validation error
    
    def test_ingest_with_invalid_extension(self):
        """Test ingest con extensión inválida"""
        files = {
            "files": ("test.exe", b"fake content", "application/octet-stream")
        }
        response = client.post("/ingest", files=files)
        assert response.status_code in [400, 422]


class TestCacheEndpoints:
    """Tests para endpoints de caché"""
    
    def test_clear_cache(self):
        """Test limpiar caché"""
        response = client.post("/cache/clear")
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data
