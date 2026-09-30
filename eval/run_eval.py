"""Measures retrieval (recall@k, hit rate, MRR) and answer quality (keyword coverage, refusal accuracy).
Run from project root:  python -m eval.run_eval"""
import json
from pathlib import Path

from app import rag
from app.config import TOP_K

data = json.loads((Path(__file__).parent / "eval_set.json").read_text())
recalls, hits, rrs, kw_scores, refusals = [], [], [], [], []

for i, ex in enumerate(data, 1):
    res = rag.retrieve(ex["question"], TOP_K)
    ranked = []
    for d, _ in res:
        if d.metadata["doc_id"] not in ranked:
            ranked.append(d.metadata["doc_id"])
    out = rag.answer(ex["question"], session_id=f"eval-{i}")  # fresh session per question

    if ex["answerable"]:
        exp = set(ex["expected_docs"])
        found = exp & set(ranked)
        recalls.append(len(found) / len(exp))
        hits.append(1.0 if found else 0.0)
        rrs.append(next((1 / (r + 1) for r, d in enumerate(ranked) if d in exp), 0.0))
        text = out["answer"].lower()
        kw_scores.append(sum(k.lower() in text for k in ex["keywords"]) / len(ex["keywords"]))
    else:
        refusals.append(1.0 if out["confidence"]["level"] == "none" else 0.0)
    print(f"{i}. {ex['question'][:60]:60} conf={out['confidence']['level']:6} top={ranked[:3]}")

avg = lambda xs: round(sum(xs) / len(xs), 3) if xs else None
print("\n=== Results ===")
print(f"Recall@{TOP_K} (docs):       {avg(recalls)}")
print(f"Hit rate:               {avg(hits)}")
print(f"MRR:                    {avg(rrs)}")
print(f"Answer keyword cover:   {avg(kw_scores)}")
print(f"Correct refusals:       {avg(refusals)}")
