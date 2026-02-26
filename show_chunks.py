import json

data = json.load(open('vector_db/documents.json', 'r', encoding='utf-8'))

# Filter hanya .md
md_chunks = [d for d in data if d.get('metadata', {}).get('source', '').endswith('.md')]

# Cari chunk substantif dari 2 dokumen berbeda
# Skip: TOC, nama tim, daftar pustaka, konten pendek
skip = ['DAFTAR', 'Tim Task', 'Pengarah', '....', 'McCabe', 'Staf Administrasi', 
        'https://', 'Ketua Tim', 'Penanggung Jawab', 'Dokumentasi']

def is_good(chunk):
    c = chunk.get('content', '')
    if len(c) < 600:
        return False
    first_300 = c[:300]
    return not any(kw in first_300 for kw in skip)

examples = []
seen = set()

# Prioritas: chunk tentang aturan/ketentuan
for chunk in md_chunks:
    src = chunk['metadata'].get('source', '')
    content = chunk.get('content', '')
    if src in seen:
        continue
    if not is_good(chunk):
        continue
    # Prefer chunks with keywords about rules
    if any(kw in content[:300].lower() for kw in ['pasal', 'syarat', 'ketentuan', 'mahasiswa', 'wajib']):
        examples.append(chunk)
        seen.add(src)
    if len(examples) == 2:
        break

# Fallback if not enough
if len(examples) < 2:
    for chunk in md_chunks:
        src = chunk['metadata'].get('source', '')
        if src in seen:
            continue
        if is_good(chunk):
            examples.append(chunk)
            seen.add(src)
        if len(examples) == 2:
            break

lines = []
lines.append("=" * 70)
lines.append("  CONTOH HASIL CHUNKING DOKUMEN")
lines.append("  (chunk_size=1000, chunk_overlap=300)")
lines.append("=" * 70)

for i, chunk in enumerate(examples, 1):
    meta = chunk.get('metadata', {})
    content = chunk.get('content', '')
    preview = content[:500] + "\n    [... sisa konten dipotong ...]" if len(content) > 500 else content

    lines.append("")
    lines.append("-" * 70)
    lines.append(f"  CHUNK CONTOH {i}")
    lines.append("-" * 70)
    lines.append(f"  Source     : {meta.get('source', '-')}")
    lines.append(f"  Heading    : {meta.get('heading', '-')}")
    lines.append(f"  Category   : {meta.get('category', '-')}")
    lines.append(f"  Index      : {meta.get('chunk_index', '-')} dari {meta.get('total_chunks', '-')}")
    lines.append(f"  Length     : {len(content)} karakter")
    lines.append(f"  Snippet    : {meta.get('snippet', '-')}")
    lines.append("-" * 70)
    lines.append("  ISI CHUNK:")
    lines.append("")
    for line in preview.split('\n'):
        lines.append(f"    {line}")
    lines.append("")

lines.append("=" * 70)
lines.append(f"  Total chunks knowledge base: {len(md_chunks)}")
lines.append("=" * 70)

with open('chunk_preview.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print("Done! Buka chunk_preview.md untuk screenshot")
