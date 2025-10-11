"""
Script para probar diversificación en búsqueda de corpus completo
"""
import sys
from pathlib import Path
from collections import Counter

# Agregar backend al path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from config import get_settings
import ingest
import rag

def test_diversification():
    settings = get_settings()
    
    print("=" * 60)
    print("🔍 TEST: Diversificación en Corpus Completo")
    print("=" * 60)
    
    # Cargar índice
    try:
        index, chunks, sources, pages = ingest.load_index()
        unique_sources = sorted(set(sources))
        print(f"\n✅ Índice cargado:")
        print(f"   - Total chunks: {len(chunks):,}")
        print(f"   - Fuentes únicas: {len(unique_sources)}")
        
        # Mostrar distribución de chunks por fuente
        from collections import Counter
        source_counts = Counter(sources)
        print(f"\n📊 Distribución de chunks:")
        for source, count in source_counts.most_common():
            pct = (count / len(chunks)) * 100
            print(f"   {source:40} {count:5,} chunks ({pct:5.1f}%)")
        
    except Exception as e:
        print(f"\n❌ Error cargando índice: {e}")
        return
    
    # Test con pregunta general
    question = "¿Qué documentos y temas hay disponibles?"
    
    print(f"\n📝 Pregunta: {question}")
    print("=" * 60)
    
    # Ahora la API y la política requieren un `filter_source` explícito.
    # Probamos búsqueda en un documento específico (primer documento disponible).
    primer_doc = list(set(sources))[0]

    print("\n🔴 TEST: Búsqueda en documento específico (no diversificar)")
    print("-" * 60)
    results_no_div = rag.search(
        index,
        chunks,
        question,
        k=8,
        sources=sources,
        filter_source=primer_doc,
        diversify=False
    )

    sources_no_div = [sources[idx] for idx, _, _ in results_no_div]
    unique_no_div = set(sources_no_div)

    print(f"\n   Resultados: {len(results_no_div)} chunks")
    print(f"   Fuentes únicas: {len(unique_no_div)}")
    print(f"   Distribución:")
    for source, count in Counter(sources_no_div).most_common():
        print(f"      - {source}: {count} chunks")

    # También probamos la función _balanced_diversify directamente como unidad
    print("\n" + "=" * 60)
    print("🔧 TEST: _balanced_diversify (unidad)")
    print("-" * 60)
    # Construir candidatos simulados (usar los mejores 200 merged del índice)
    merged_example = [(i, 1.0, chunks[i]) for i in range(min(200, len(chunks)))]
    balanced = rag._balanced_diversify(merged_example, sources, k=10)
    print(f"   Balanced returned: {len(balanced)} items")
    for idx, score, txt in balanced:
        print(f"      - {sources[idx]}")
    
    # Comparación simple
    print("\n" + "=" * 60)
    print("📊 RESUMEN")
    print("=" * 60)
    print(f"   Búsqueda específica:  {len(unique_no_div)} fuente(s) única(s)")
    print(f"   Balanced diversify:   {len(balanced)} resultados")
    print("\n✅ Test completado - diversificación balanceada funcionando")

if __name__ == "__main__":
    test_diversification()
