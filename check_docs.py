import json
from pathlib import Path
from collections import Counter

meta = json.load(Path('backend/data/store/meta.json').open(encoding='utf-8'))
counts = Counter(meta['sources'])
sorted_counts = sorted(counts.items(), key=lambda x: x[1])

print('\n' + '='*70)
print('Documentos ordenados por cantidad de chunks:')
print('='*70 + '\n')

for source, count in sorted_counts:
    if count == 0:
        status = 'SIN CHUNKS'
    elif count < 5:
        status = 'POCOS'
    else:
        status = 'OK'
    
    print(f"{status:12} {source:45} {count:5} chunks")

no_chunks = [s for s, c in counts.items() if c == 0]
if no_chunks:
    print(f'\n PROBLEMA: {len(no_chunks)} documentos sin chunks:')
    for doc in no_chunks:
        print(f'  - {doc}')
