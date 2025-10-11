"""
Script de diagnóstico para entender el problema del filtro de corpus
"""
import sys
from pathlib import Path

# Agregar backend al path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from config import get_settings
import ingest
import rag

def test_search_behavior():
    """Prueba el comportamiento del filtro source"""
    settings = get_settings()
    
    print("=" * 60)
    print("🔍 DIAGNÓSTICO: Filtro de Corpus")
    print("=" * 60)
    
    # Cargar índice
    try:
        index, chunks, sources, pages = ingest.load_index()
        unique_sources = sorted(set(sources))
        print(f"\n✅ Índice cargado:")
        print(f"   - Total chunks: {len(chunks)}")
        print(f"   - Fuentes únicas: {len(unique_sources)}")
        print(f"   - Documentos: {', '.join(unique_sources[:5])}")
        if len(unique_sources) > 5:
            print(f"                 ... y {len(unique_sources) - 5} más")
    except Exception as e:
        print(f"\n❌ Error cargando índice: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Pregunta de prueba
    question = "¿Qué documentos hay disponibles?"
    
    print(f"\n📝 Pregunta de prueba: {question}")
    
    # Nota: La API ahora requiere un `filter_source` válido. Probamos con
    # un documento específico (primer documento disponible).
    primer_doc = list(set(sources))[0] if sources else None
    if not primer_doc:
        print("No hay documentos para probar")
        return
    print("\n" + "-" * 60)
    print(f"TEST: filter_source='{primer_doc}' (documento específico)")
    print("-" * 60)
    
    results_specific = rag.search(
        index,
        chunks,
        question,
        k=10,
        sources=sources,
        filter_source=primer_doc
    )
    
    print(f"   Resultados: {len(results_specific)} chunks")
    if results_specific:
        fuentes_encontradas = set(sources[idx] for idx, _, _ in results_specific)
        print(f"   Fuentes en resultados: {fuentes_encontradas}")
    
    # Test 3: Con filtro específico (primer documento)
    if sources:
        primer_doc = list(set(sources))[0]
        print("\n" + "-" * 60)
        print(f"TEST 3: filter_source='{primer_doc}' (documento específico)")
        print("-" * 60)
        
        results_specific = rag.search(
            index,
            chunks,
            question,
            k=10,
            sources=sources,
            filter_source=primer_doc
        )
        
        print(f"   Resultados: {len(results_specific)} chunks")
        if results_specific:
            fuentes_encontradas = set(sources[idx] for idx, _, _ in results_specific)
            print(f"   Fuentes en resultados: {fuentes_encontradas}")
    
    # Test 4: Con filtro de cadena inválida
    print("\n" + "-" * 60)
    print("TEST 4: filter_source='archivo_inexistente.pdf' (no existe)")
    print("-" * 60)
    
    results_invalid = rag.search(
        index,
        chunks,
        question,
        k=10,
        sources=sources,
        filter_source="archivo_inexistente.pdf"
    )
    
    print(f"   Resultados: {len(results_invalid)} chunks")
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    print(f"   Archivo específico:       {len(results_specific) if sources else 'N/A'} resultados")
    print(f"   Archivo inexistente:      {len(results_invalid)} resultados")
    
    if len(results_specific) == 0:
        print("\n❌ PROBLEMA DETECTADO: No hay resultados para el documento específico")
    else:
        print("\n✅ Filtrado por documento funcionando correctamente")

if __name__ == "__main__":
    test_search_behavior()
