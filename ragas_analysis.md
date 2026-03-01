# 📈 Analisis Hasil Evaluasi RAGAS — SINEMA RAG Chatbot

## Overview

| Item | Nilai |
|------|-------|
| **Total Sampel** | 50 |
| **Model Evaluator** | Gemma 3 27B (Google AI) |
| **Embeddings** | - (3 metrik tanpa answer_relevancy) |
| **Kategori** | 5 (panduan_akademik, poin_ekstrakurikuler, ta_skripsi, integritas_akademik, website_sinema) |

---

## Statistik Keseluruhan

| Metrik | Mean | Median | Min | Max | Std |
|--------|------|--------|-----|-----|-----|
| **Faithfulness** | **0.6582** | 0.7208 | 0.00 | 1.00 | 0.2379 |
| **Context Precision** | **0.4670** | 0.4995 | 0.00 | 1.00 | 0.3579 |
| **Context Recall** | **0.8400** | 1.0000 | 0.00 | 1.00 | 0.3433 |

### Interpretasi:

- **Context Recall (0.84)** — **Baik**. 80% dari sampel mendapat skor 1.0 (40/50). Retriever berhasil mengambil informasi yang dibutuhkan di sebagian besar kasus.
- **Faithfulness (0.66)** — **Cukup**. LLM kadang menambahkan informasi di luar konteks (halusinasi ringan). Median 0.72 lebih representatif karena ada beberapa outlier rendah.
- **Context Precision (0.47)** — **Rendah**. Banyak konteks yang di-retrieve tidak relevan. Retriever mengambil terlalu banyak dokumen yang kurang tepat.

---

## Per Kategori

| Kategori | N | Faithfulness | Context Precision | Context Recall |
|----------|---|-------------|-------------------|----------------|
| **integritas_akademik** | 7 | **0.8225** ✅ | **0.5648** | **0.9524** ✅ |
| **panduan_akademik** | 16 | 0.6610 | **0.6262** ✅ | **0.9375** ✅ |
| **ta_skripsi** | 10 | **0.7318** | 0.3987 | **1.0000** ✅ |
| **poin_ekstrakurikuler** | 10 | 0.6479 | 0.3645 ⚠️ | 0.7333 ⚠️ |
| **website_sinema** | 7 | **0.3968** ❌ | **0.2491** ❌ | **0.4286** ❌ |

### Temuan Per Kategori:

#### ✅ Kategori Terbaik: `integritas_akademik`
- Semua metrik tinggi: faithfulness 0.82, recall 0.95
- Dokumen integritas akademik terstruktur → mudah di-retrieve dan di-generate

#### ✅ Kategori Baik: `panduan_akademik` & `ta_skripsi`
- Recall sempurna untuk ta_skripsi (1.0) — semua info ditemukan
- Precision panduan_akademik paling tinggi (0.63) — retriever tepat

#### ⚠️ Kategori Bermasalah: `poin_ekstrakurikuler`
- Recall turun ke 0.73 — beberapa info poin tidak ter-retrieve
- Precision rendah (0.36) — banyak dokumen irrelevan ikut diambil
- Kemungkinan penyebab: data tabel poin sulit di-chunk/parse

#### ❌ Kategori Terburuk: `website_sinema`
- **Semua metrik rendah**: faith=0.40, prec=0.25, recall=0.43
- 4 dari 7 sampel punya recall = 0 (informasi tidak ditemukan sama sekali)
- Penyebab: dokumen tentang website SINEMA mungkin kurang lengkap di knowledge base, atau format data website berbeda dari dokumen akademik

---

## Distribusi Context Recall

| Skor | Jumlah Sampel | Persentase |
|------|--------------|------------|
| **1.0** | 40 | 80% |
| 0.67 | 1 | 2% |
| 0.50 | 2 | 4% |
| 0.33 | 1 | 2% |
| **0.0** | 6 | 12% |

> [!IMPORTANT]
> 80% sampel mendapat recall sempurna (1.0), tapi 12% gagal total (0.0). Ini menunjukkan pola **all-or-nothing**: retriever biasanya menemukan semua info, tapi untuk topik tertentu (website SINEMA, poin spesifik) gagal sama sekali.

---

## Sampel Bermasalah

### Faithfulness Rendah (< 0.3) — 5 sampel
| ID | Kategori | Skor | Pertanyaan |
|----|----------|------|------------|
| 3 | panduan_akademik | 0.25 | Berapa lama masa studi maksimal untuk program D4? |
| 34 | ta_skripsi | 0.00 | Berapa lama waktu maksimal untuk menyelesaikan tugas akhir? |
| 46 | website_sinema | 0.00 | Apa saja status pengajuan di SINEMA? |
| 49 | website_sinema | 0.17 | Berapa lama proses verifikasi pengajuan di SINEMA? |
| 50 | website_sinema | 0.00 | Apa yang harus dilakukan jika pengajuan ditolak di SINEMA? |

> Chatbot mengarang jawaban (halusinasi) untuk pertanyaan website SINEMA, karena konteks yang relevan tidak tersedia.

### Context Recall = 0 — 6 sampel
| ID | Kategori | Pertanyaan |
|----|----------|------------|
| 22 | poin_ekstrakurikuler | Berapa poin untuk mengikuti seminar tingkat universitas? |
| 24 | poin_ekstrakurikuler | Berapa poin untuk menjadi asisten praktikum? |
| 44 | website_sinema | Apa itu SINEMA? |
| 45 | website_sinema | Bagaimana cara mengajukan klaim kegiatan di SINEMA? |
| 46 | website_sinema | Apa saja status pengajuan di SINEMA? |
| 50 | website_sinema | Apa yang harus dilakukan jika pengajuan ditolak di SINEMA? |

> Retriever tidak menemukan informasi apapun yang relevan untuk pertanyaan-pertanyaan ini.

---

## Rekomendasi Perbaikan

### 1. Knowledge Base
- **Tambahkan dokumen website SINEMA** ke knowledge base (panduan pengguna, FAQ)
- **Perbaiki chunking** untuk tabel poin ekstrakurikuler agar data tabular bisa di-retrieve lebih baik

### 2. Retriever
- **Tuning retriever** untuk meningkatkan precision: kurangi jumlah chunks yang di-retrieve atau gunakan re-ranking
- **Evaluate embedding model** — mungkin perlu fine-tune untuk domain akademik Bahasa Indonesia

### 3. Generator (LLM)
- **Tambahkan guardrail** agar LLM tidak mengarang jawaban saat konteks tidak tersedia
- Implementasikan **"I don't know" response** jika confidence rendah

---

## Kesimpulan

| Aspek | Rating | Penjelasan |
|-------|--------|------------|
| **Retriever** | ⭐⭐⭐☆☆ | Recall tinggi (0.84) tapi precision rendah (0.47). Perlu tuning. |
| **Generator** | ⭐⭐⭐☆☆ | Faithfulness cukup (0.66) tapi ada halusinasi di topik kurang familiar. |
| **Overall RAG** | ⭐⭐⭐☆☆ | Sistem bekerja baik untuk topik akademik umum, tapi lemah di website SINEMA dan detail poin. |
