# -*- coding: utf-8 -*-
"""
Seed script: Insert expert evaluation data into MySQL.

All data extracted from original dashboard (screenshots + raw text copy).
Total: 53 evaluations from 6 experts.

Run: python evaluation/seed_expert_data.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from app.config import DATABASE_URL
from app.models import db, ExpertEvaluation
from datetime import datetime

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

FIXED_QUESTIONS = [
    "Apa saja predikat kelulusan program sarjana dan syarat IPK-nya?",
    "Bagaimana prosedur pengajuan cuti akademik?",
    "Apa saja bentuk-bentuk pelanggaran integritas akademik?",
    "Bagaimana cara mengajukan klaim kegiatan di SINEMA?",
    "Berapa total poin minimal untuk mendapat nilai mutu A?",
    "Apa saja bidang kegiatan ekstrakurikuler yang diakui?",
    "Apa perbedaan tugas akhir skripsi dan non-skripsi?",
    "Bagaimana prosedur seminar proposal tugas akhir?",
    "Bagaimana cara mengajukan Transkrip Ekstrakurikuler Mahasiswa (TEM) di SINEMA?",
    "Bagaimana cara menghindari plagiarisme dalam penulisan karya ilmiah?",
]

# =====================================================
# ACTUAL DATA FROM SCREENSHOTS (per-question scores)
# Columns: (akurasi, relevansi, kejelasan)
# =====================================================

# Andi Arham Adam - Screenshot 4 (rows 1-10), 26/02/2026 21:39-21:48
ANDI_SCORES = {
    0: (5, 5, 5),  # Q1: predikat kelulusan
    1: (5, 4, 5),  # Q2: cuti akademik
    2: (5, 5, 5),  # Q3: pelanggaran integritas
    3: (5, 5, 5),  # Q4: klaim kegiatan SINEMA
    4: (5, 5, 5),  # Q5: poin minimal
    5: (5, 5, 5),  # Q6: bidang kegiatan
    6: (5, 5, 5),  # Q7: perbedaan TA
    7: (5, 5, 5),  # Q8: seminar proposal
    8: (5, 5, 5),  # Q9: TEM
    9: (5, 5, 5),  # Q10: plagiarisme
}

# Bakri - Screenshot 3 (rows 11-20), 26/02/2026 22:32-22:43
# Note: Bakri evaluated in non-sequential order
BAKRI_SCORES = {
    3: (4, 5, 5),  # Q4: klaim kegiatan (row 11)
    4: (4, 5, 5),  # Q5: poin minimal (row 12)
    5: (5, 5, 5),  # Q6: bidang kegiatan (row 13)
    8: (5, 5, 5),  # Q9: TEM (row 14)
    0: (5, 4, 5),  # Q1: predikat kelulusan (row 15)
    1: (5, 5, 5),  # Q2: cuti akademik (row 16)
    2: (5, 5, 5),  # Q3: pelanggaran integritas (row 17)
    6: (5, 5, 5),  # Q7: perbedaan TA (row 18)
    7: (5, 5, 5),  # Q8: seminar proposal (row 19)
    9: (5, 5, 5),  # Q10: plagiarisme (row 20)
}

# Yusuf Anshori - Screenshot 2 (rows 21-30), 26/02/2026 23:07-23:13
YUSUF_SCORES = {
    0: (3, 4, 4),  # Q1: predikat kelulusan
    1: (5, 4, 5),  # Q2: cuti akademik
    2: (4, 4, 4),  # Q3: pelanggaran integritas
    3: (5, 5, 5),  # Q4: klaim kegiatan
    4: (4, 4, 4),  # Q5: poin minimal
    5: (3, 4, 4),  # Q6: bidang kegiatan
    6: (3, 3, 3),  # Q7: perbedaan TA
    7: (3, 3, 3),  # Q8: seminar proposal
    8: (3, 3, 3),  # Q9: TEM
    9: (3, 3, 3),  # Q10: plagiarisme
}

# Anita Ahmad Kasim - Screenshot 1 (rows 31-40), 26/02/2026 23:59 - 27/02/2026 00:10
ANITA_SCORES = {
    0: (5, 5, 5),  # Q1: predikat kelulusan
    1: (5, 5, 5),  # Q2: cuti akademik
    2: (5, 5, 5),  # Q3: pelanggaran integritas
    3: (5, 5, 5),  # Q4: klaim kegiatan
    4: (5, 5, 5),  # Q5: poin minimal
    5: (5, 5, 4),  # Q6: bidang kegiatan
    6: (5, 5, 4),  # Q7: perbedaan TA
    7: (5, 5, 5),  # Q8: seminar proposal
    8: (5, 5, 5),  # Q9: TEM
    9: (5, 5, 5),  # Q10: plagiarisme
}

# Nouval Trezandy Lapatta - 3 evaluations, 27/02/2026 01:29-01:32
NOUVAL_SCORES = {
    0: (5, 5, 5),  # Q1: predikat kelulusan
    1: (5, 5, 5),  # Q2: cuti akademik
    2: (4, 5, 4),  # Q3: pelanggaran integritas
}

# Muh Dadang Anshari - 10 evaluations, 27/02/2026 01:33-01:36
DADANG_SCORES = {
    0: (5, 5, 5),  # Q1: predikat kelulusan
    1: (4, 5, 5),  # Q2: cuti akademik
    2: (4, 5, 4),  # Q3: pelanggaran integritas
    3: (5, 5, 5),  # Q4: klaim kegiatan
    4: (5, 5, 4),  # Q5: poin minimal
    5: (5, 5, 5),  # Q6: bidang kegiatan
    6: (4, 5, 4),  # Q7: perbedaan TA
    7: (5, 5, 5),  # Q8: seminar proposal
    8: (4, 5, 5),  # Q9: TEM
    9: (5, 4, 5),  # Q10: plagiarisme
}

ALL_EXPERTS = [
    ("Andi Arham Adam", "Dosen Fakultas Teknik", ANDI_SCORES,
     datetime(2026, 2, 26, 21, 39, 0)),
    ("Bakri", "Dosen Fakultas Teknik", BAKRI_SCORES,
     datetime(2026, 2, 26, 22, 32, 0)),
    ("Yusuf Anshori", "Dosen Fakultas Teknik", YUSUF_SCORES,
     datetime(2026, 2, 26, 23, 7, 0)),
    ("Anita Ahmad Kasim", "Staff Kemahasiswaan", ANITA_SCORES,
     datetime(2026, 2, 26, 23, 59, 0)),
    ("Nouval Trezandy Lapatta", "Mahasiswa", NOUVAL_SCORES,
     datetime(2026, 2, 27, 1, 29, 0)),
    ("Muh Dadang Anshari", "Dosen Fakultas Teknik", DADANG_SCORES,
     datetime(2026, 2, 27, 1, 33, 0)),
]


def _do_seed():
    """Core seed logic — must be called within a Flask app context."""
    existing = ExpertEvaluation.query.count()
    if existing > 0:
        print(f"⚠️  Database sudah berisi {existing} evaluasi. Skipping seed.")
        return
    
    count = 0
    for name, jabatan, scores_dict, base_time in ALL_EXPERTS:
        for q_idx, (akurasi, relevansi, kejelasan) in scores_dict.items():
            question = FIXED_QUESTIONS[q_idx]
            ev = ExpertEvaluation(
                expert_name=name,
                expert_jabatan=jabatan,
                question=question,
                answer="",
                score_akurasi=akurasi,
                score_relevansi=relevansi,
                score_kejelasan=kejelasan,
                comment="",
                created_at=base_time,
            )
            db.session.add(ev)
            count += 1
        
        n = len(scores_dict)
        avg_a = sum(s[0] for s in scores_dict.values()) / n
        avg_r = sum(s[1] for s in scores_dict.values()) / n
        avg_k = sum(s[2] for s in scores_dict.values()) / n
        print(f"  ✅ {name}: {n} evaluasi (akurasi={avg_a:.2f}, relevansi={avg_r:.2f}, kejelasan={avg_k:.2f})")
    
    db.session.commit()
    print(f"\n✅ Total: {count} evaluasi dari {len(ALL_EXPERTS)} expert berhasil di-seed!")


def seed():
    """Entry point for standalone execution or being called from expert_evaluation.py."""
    from flask import current_app
    try:
        current_app.config
        _do_seed()
    except RuntimeError:
        app = create_app()
        with app.app_context():
            db.create_all()
            _do_seed()


if __name__ == "__main__":
    seed()
