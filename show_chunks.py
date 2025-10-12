import json

meta = json.load(open('backend/data/store/meta.json', encoding='utf-8'))
indices = [i for i, s in enumerate(meta['sources']) if 'factura-sitio-web-manabivial' in s]

print(f'Total chunks encontrados: {len(indices)}')
print(f'Indices: {indices}\n')

for idx in indices:
    print(f'='*70)
    print(f'Chunk {idx} - Pagina {meta["pages"][idx]}')
    print(f'='*70)
    print(meta['chunks'][idx])
    print()
