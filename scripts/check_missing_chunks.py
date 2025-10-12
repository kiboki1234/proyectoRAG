"""
Script para diagnosticar documentos sin chunks en el índice FAISS.
"""
import json
from pathlib import Path
from collections import Counter

def check_documents():
    meta_path = Path('backend/data/store/meta.json')
    
    if not meta_path.exists():
        print("❌ No existe meta.json")
        return
    
    meta = json.load(meta_path.open(encoding='utf-8'))
    
    # Contar chunks por documento
    chunk_counts = Counter(meta['sources'])
    
    print("\n" + "="*70)
    print("📊 REPORTE DE CHUNKS POR DOCUMENTO")
    print("="*70 + "\n")
    
    total_docs = len(chunk_counts)
    total_chunks = sum(chunk_counts.values())
    
    print(f"Total documentos: {total_docs}")
    print(f"Total chunks: {total_chunks}")
    print(f"Promedio chunks/doc: {total_chunks/total_docs:.1f}\n")
    
    # Ordenar por cantidad de chunks (ascendente)
    sorted_counts = sorted(chunk_counts.items(), key=lambda x: x[1])
    
    print("📄 Documentos (ordenados por cantidad de chunks):")
    print("-"*70)
    
    for source, count in sorted_counts:
        if count == 0:
            status = "❌ SIN CHUNKS"
            color = "\033[91m"  # Red
        elif count < 5:
            status = "⚠️  POCOS CHUNKS"
            color = "\033[93m"  # Yellow
        else:
            status = "✅"
            color = "\033[92m"  # Green
        
        reset = "\033[0m"
        print(f"{color}{status:15} {source:45} {count:5} chunks{reset}")
    
    # Documentos problemáticos
    no_chunks = [s for s, c in chunk_counts.items() if c == 0]
    low_chunks = [s for s, c in chunk_counts.items() if 0 < c < 5]
    
    if no_chunks or low_chunks:
        print("\n" + "="*70)
        print("🚨 DOCUMENTOS CON PROBLEMAS")
        print("="*70 + "\n")
        
        if no_chunks:
            print(f"❌ Sin chunks ({len(no_chunks)} documentos):")
            for doc in no_chunks:
                print(f"  - {doc}")
        
        if low_chunks:
            print(f"\n⚠️  Pocos chunks (<5) ({len(low_chunks)} documentos):")
            for doc in low_chunks:
                print(f"  - {doc} ({chunk_counts[doc]} chunks)")
    else:
        print("\n✅ Todos los documentos tienen chunks adecuados")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    check_documents()
