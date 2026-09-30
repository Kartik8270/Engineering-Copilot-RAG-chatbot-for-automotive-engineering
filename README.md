# Engineering Copilot — RAG chatbot for automotive engineering

Ask questions over manuals, project reports and troubleshooting records and get **cited** answers with an
**evidence indicator**. If the documents don't contain the answer, it says so instead of guessing.

## Architecture
PDF → `pdfplumber` (text, tables, metadata, section headings) → section-aware chunks →
`sentence-transformers` embeddings → Chroma (cosine) → top-k retrieval → confidence scoring →
Claude (LangChain) answer with `(doc, §section, p.page)` citations. FastAPI serves it, Streamlit is the UI.

## Run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # add ANTHROPIC_API_KEY (works without it in extractive mode)
python scripts/make_sample_docs.py   # optional demo PDFs in sample_docs/

uvicorn app.api:app --reload         # terminal 1
streamlit run ui/streamlit_app.py    # terminal 2 -> upload sample_docs/*.pdf, then ask:
# "Our motor assembly has excessive vibration. Have we seen similar issues before?"
```

## Evaluate
Ingest the sample PDFs (via the UI or `/upload`), then: `python -m eval.run_eval`
Reports recall@k, hit rate, MRR, answer keyword coverage and correct-refusal rate.
Edit `eval/eval_set.json` to add questions from your own documents.

## Confidence logic (`app/rag.py`)
Based on top cosine similarity: `< MIN_SCORE` → **none** (refuses, no LLM call); `≥ HIGH_SCORE` → **high**;
in between → medium/low. Tune `MIN_SCORE` / `HIGH_SCORE` in `.env` using the eval set.

## Extension ideas
OCR for scanned PDFs, hybrid BM25 + vector search, cross-encoder reranking, metadata filters (project/date),
ingest maintenance CSV/Excel, streaming responses, auth and per-team document collections.
