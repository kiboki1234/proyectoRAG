"""
Script para limpiar el índice FAISS de documentos que fueron borrados.
Elimina chunks de documentos que ya no existen en backend/data/docs/
"""
import json
from pathlib import Path

# Rutas
meta_path = Path('backend/data/store/meta.json')
docs_dir = Path('backend/data/docs')

print("="*70)
print("🧹 LIMPIEZA DE ÍNDICE - Documentos Borrados")
print("="*70)

# Verificar que existe meta.json
if not meta_path.exists():
    print("❌ No existe meta.json - nada que limpiar")
    exit(1)

# Cargar meta
meta = json.load(meta_path.open(encoding='utf-8'))
old_count = len(meta['chunks'])
old_sources = set(meta['sources'])

print(f"\n📊 Estado actual:")
print(f"   Chunks totales: {old_count}")
print(f"   Documentos únicos en índice: {len(old_sources)}")

# Archivos que SÍ existen físicamente
existing_files = set()
for pattern in ['*.pdf', '*.md', '*.markdown', '*.txt']:
    for p in docs_dir.glob(pattern):
        if p.is_file():
            existing_files.add(p.name)

print(f"   Archivos en docs/: {len(existing_files)}")

# Identificar documentos borrados (en índice pero no en filesystem)
deleted_docs = old_sources - existing_files

if not deleted_docs:
    print("\n✅ No hay documentos borrados - índice limpio")
    exit(0)

print(f"\n🗑️  Documentos borrados encontrados ({len(deleted_docs)}):")
for doc in sorted(deleted_docs):
    count = sum(1 for s in meta['sources'] if s == doc)
    print(f"   - {doc} ({count} chunks)")

# Confirmar
print("\n⚠️  Esto eliminará estos documentos del índice.")
response = input("¿Continuar? (s/N): ")

if response.lower() != 's':
    print("❌ Operación cancelada")
    exit(0)

# Filtrar chunks de documentos existentes
keep_indices = [
    i for i, source in enumerate(meta['sources'])
    if source in existing_files
]

meta['chunks'] = [meta['chunks'][i] for i in keep_indices]
meta['sources'] = [meta['sources'][i] for i in keep_indices]
meta['pages'] = [meta['pages'][i] for i in keep_indices]

new_count = len(meta['chunks'])
removed = old_count - new_count

# Guardar
meta_path.write_text(
    json.dumps(meta, indent=2, ensure_ascii=False),
    encoding='utf-8'
)

print(f"\n✅ Limpieza completada:")
print(f"   Chunks antes: {old_count}")
print(f"   Chunks después: {new_count}")
print(f"   Eliminados: {removed}")

print("\n⚠️  IMPORTANTE:")
print("   1. Debes reconstruir el índice FAISS")
print("   2. Opción A: Elimina backend/data/store/faiss.index")
print("   3. Opción B: Usa el endpoint POST /rebuild")
print("   4. Reinicia el backend")

print("\n" + "="*70)
