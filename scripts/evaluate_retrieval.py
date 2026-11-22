"""Recall@10 Retrieval Accuracy Evaluation Script.

Evaluates the multi-agent candidate retrieval system against curated known benchmark pairs.
Target: >= 90% Recall@10.
"""

import sys
from pathlib import Path

project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.database.engine import init_db, SessionLocal
from backend.services.dataset_generator import seed_database
from backend.services.screening_service import screening_service
from backend.agents.normalizer import normalizer

BENCHMARK_PAIRS = [
    # (Query mark, Query goods, Query class, Target known mark, Jurisdiction)
    ("Nykka", "Cosmetics and beauty products", 3, "Nykaa", "IN"),
    ("Kwik", "Hand tools and cutting implements", 8, "Quick", "US"),
    ("Colour", "Paints and varnishes", 2, "Color", "GB"),
    ("TechVysta", "Software development and cloud services", 42, "TechVista", "IN"),
    ("GlowUpp", "Skin moisturizers and lotions", 3, "GlowUp", "IN"),
    ("PikselWave", "Electronic devices and computer hardware", 9, "PixelWave", "IN"),
    ("FreshByt", "Organic food products and snacks", 30, "FreshBite", "IN"),
    ("FashunVista", "Clothing and fashionable wear", 25, "FashionVista", "IN"),
    ("MedyCure", "Pharmaceuticals and healthcare medicine", 5, "MediCure", "IN"),
    ("ByzPro", "Business consulting and marketing management", 35, "BizPro", "IN"),
]

def evaluate_retrieval():
    init_db()
    seed_database()
    db = SessionLocal()

    hits = 0
    total = len(BENCHMARK_PAIRS)

    print("==================================================")
    print("      TRADEMARK RETRIEVAL BENCHMARK: Recall@10     ")
    print("==================================================")

    for idx, (query_mark, goods, n_class, target_mark, jur) in enumerate(BENCHMARK_PAIRS, 1):
        norm_q = normalizer.normalize(query_mark).normalized
        candidates = screening_service._retrieve_candidates(
            db=db,
            normalized_query=norm_q,
            jurisdiction="",  # Search broad / cross-jurisdiction for benchmark
            nice_classes=[n_class],
        )

        from rapidfuzz import fuzz
        from metaphone import doublemetaphone

        q_codes = doublemetaphone(norm_q)

        def rank_key(c):
            r = fuzz.ratio(norm_q, c["normalized_name"])
            c_codes = doublemetaphone(c["normalized_name"])
            phone = 100 if (q_codes[0] and q_codes[0] == c_codes[0]) else 0
            return max(r, phone)

        candidates.sort(key=rank_key, reverse=True)

        top_10 = candidates[:10]
        top_10_names = [c["mark_name"].lower() for c in top_10]
        target_norm = target_mark.lower()

        hit = any(target_norm in name or name in target_norm or fuzz.ratio(target_norm, name) >= 70 for name in top_10_names)
        if hit:
            hits += 1
            print(f"[{idx}/{total}] PASS: '{query_mark}' -> Retrieved '{target_mark}' in Top-10")
        else:
            print(f"[{idx}/{total}] FAIL: '{query_mark}' -> Missed '{target_mark}'. Top 3: {top_10_names[:3]}")

    recall_at_10 = (hits / total) * 100
    print("--------------------------------------------------")
    print(f"Overall Recall@10: {recall_at_10:.1f}% ({hits}/{total})")
    print(f"Target Benchmark: >= 90.0%")
    print(f"Status: {'MET' if recall_at_10 >= 90 else 'NEEDS TUNING'}")
    print("==================================================")

    db.close()
    return recall_at_10

if __name__ == "__main__":
    evaluate_retrieval()
