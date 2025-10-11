"""
Tests unitarios para modelos Pydantic.
"""
import pytest
from pydantic import ValidationError
from backend.models import AskRequest, Citation, AskResponse, HealthResponse, StatsResponse


class TestAskRequest:
    """Tests para el modelo AskRequest"""
    
    def test_valid_request(self):
        """Test con request válido"""
        req = AskRequest(question="¿Cuál es el RUC?", source="factura.pdf")
        assert req.question == "¿Cuál es el RUC?"
        assert req.source == "factura.pdf"
    
    def test_valid_request_without_source(self):
        """Test sin source (opcional)"""
        req = AskRequest(question="Test question")
        assert req.question == "Test question"
        assert req.source is None
    
    def test_question_too_short(self):
        """Test con pregunta muy corta"""
        with pytest.raises(ValidationError) as exc_info:
            AskRequest(question="ab")
        assert "min_length" in str(exc_info.value).lower()
    
    def test_question_too_long(self):
        """Test con pregunta muy larga"""
        long_question = "a" * 501
        with pytest.raises(ValidationError) as exc_info:
            AskRequest(question=long_question)
        assert "max_length" in str(exc_info.value).lower()
    
    def test_question_empty_after_strip(self):
        """Test con pregunta vacía después de strip"""
        with pytest.raises(ValidationError) as exc_info:
            AskRequest(question="   ")
        assert "vacía" in str(exc_info.value).lower()
    
    def test_source_with_path_traversal(self):
        """Test que rechaza path traversal en source"""
        with pytest.raises(ValidationError) as exc_info:
            AskRequest(question="test", source="../../../etc/passwd")
        assert "inválido" in str(exc_info.value).lower()
    
    def test_source_with_slash(self):
        """Test que rechaza slashes en source"""
        with pytest.raises(ValidationError):
            AskRequest(question="test", source="path/to/file.pdf")


class TestCitation:
    """Tests para el modelo Citation"""
    
    def test_valid_citation(self):
        """Test con citation válida"""
        citation = Citation(
            id=1,
            score=0.85,
            text="Sample text",
            page=5,
            source="doc.pdf"
        )
        assert citation.id == 1
        assert citation.score == 0.85
        assert citation.page == 5
    
    def test_score_out_of_range(self):
        """Test con score fuera de rango"""
        with pytest.raises(ValidationError):
            Citation(id=1, score=1.5, text="text")
    
    def test_negative_page(self):
        """Test con página negativa"""
        with pytest.raises(ValidationError):
            Citation(id=1, score=0.5, text="text", page=0)
    
    def test_text_too_long(self):
        """Test con texto muy largo"""
        long_text = "a" * 1001
        with pytest.raises(ValidationError):
            Citation(id=1, score=0.5, text=long_text)


class TestAskResponse:
    """Tests para el modelo AskResponse"""
    
    def test_valid_response(self):
        """Test con response válida"""
        citations = [
            Citation(id=1, score=0.9, text="text1"),
            Citation(id=2, score=0.8, text="text2")
        ]
        response = AskResponse(answer="Test answer", citations=citations)
        assert response.answer == "Test answer"
        assert len(response.citations) == 2
    
    def test_empty_citations(self):
        """Test con lista vacía de citations"""
        response = AskResponse(answer="Test")
        assert response.citations == []


class TestHealthResponse:
    """Tests para el modelo HealthResponse"""
    
    def test_valid_health_response(self):
        """Test con health response válido"""
        health = HealthResponse(
            status="ok",
            llm_loaded=True,
            index_exists=True,
            chunks_count=100
        )
        assert health.status == "ok"
        assert health.llm_loaded is True
        assert health.chunks_count == 100


class TestStatsResponse:
    """Tests para el modelo StatsResponse"""
    
    def test_valid_stats(self):
        """Test con stats válidas"""
        stats = StatsResponse(
            total_documents=10,
            total_chunks=500,
            avg_chunk_size=850.5,
            index_dimension=768,
            embedder_model="intfloat/multilingual-e5-base"
        )
        assert stats.total_documents == 10
        assert stats.total_chunks == 500
        assert stats.avg_chunk_size == 850.5
    
    def test_negative_counts(self):
        """Test con contadores negativos (deben fallar)"""
        with pytest.raises(ValidationError):
            StatsResponse(
                total_documents=-1,
                total_chunks=100,
                avg_chunk_size=800,
                embedder_model="test"
            )
