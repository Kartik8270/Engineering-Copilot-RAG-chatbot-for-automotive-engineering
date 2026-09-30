"""Retrieval, confidence scoring, cited answer generation, conversation memory."""
from langchain_anthropic import ChatAnthropic

from .config import (ANTHROPIC_API_KEY, HIGH_SCORE, LLM_MODEL, MIN_SCORE, TOP_K)
from .vectorstore import get_store

SESSIONS: dict[str, list[tuple[str, str]]] = {}  # session_id -> [(role, text)]

NO_ANSWER = ("I couldn't find anything in the uploaded documents that answers this. "
             "Try rephrasing, or upload the relevant manual/report.")

SYSTEM = """You are Engineering Copilot, an assistant for automotive engineers.
Answer ONLY from the numbered context excerpts. Rules:
- If the context does not contain the answer, say so plainly; never guess or use outside knowledge.
- Cite every claim like (M-104, §3.2, p.4) using the excerpt headers.
- For troubleshooting questions, list the matching records first, then a short 'Suggested next steps' list
  that is directly supported by those records.
- Be concise and technical."""

_llm = None


def get_llm():
    global _llm
    if _llm is None and ANTHROPIC_API_KEY:
        _llm = ChatAnthropic(model=LLM_MODEL, temperature=0, max_tokens=1024,
                             api_key=ANTHROPIC_API_KEY)
    return _llm


def retrieve(query: str, k: int = TOP_K):
    """-> list of (Document, cosine relevance score), best first."""
    return get_store().similarity_search_with_relevance_scores(query, k=k)


def confidence(hits) -> dict:
    if not hits:
        return {"level": "none", "score": 0.0, "supporting_documents": 0}
    top = hits[0][1]
    supporting = len({d.metadata["doc_id"] for d, s in hits if s >= MIN_SCORE})
    if top < MIN_SCORE:
        level = "none"
    elif top >= HIGH_SCORE and supporting >= 1:
        level = "high"
    elif top >= (MIN_SCORE + HIGH_SCORE) / 2:
        level = "medium"
    else:
        level = "low"
    return {"level": level, "score": round(float(top), 3), "supporting_documents": supporting}


def _condense(llm, history, question: str) -> str:
    if not history or llm is None:
        return question
    hist = "\n".join(f"{r}: {t}" for r, t in history[-6:])
    prompt = ("Rewrite the final question as a standalone search query, resolving pronouns and "
              "references using the conversation. Output only the query.\n\n"
              f"{hist}\n\nFinal question: {question}\nStandalone query:")
    return str(llm.invoke(prompt).content).strip() or question


def _format_context(hits) -> str:
    blocks = []
    for i, (d, _) in enumerate(hits, 1):
        m = d.metadata
        blocks.append(f"[{i}] ({m['doc_id']}, §{m['section']}, p.{m['page']})\n{d.page_content}")
    return "\n\n".join(blocks)


def _sources(hits) -> list[dict]:
    seen, out = set(), []
    for d, s in hits:
        m = d.metadata
        key = (m["source"], m["page"], m["section"])
        if key in seen:
            continue
        seen.add(key)
        out.append({"doc_id": m["doc_id"], "source": m["source"], "page": m["page"],
                    "section": m["section"], "type": m["type"], "score": round(float(s), 3),
                    "snippet": d.page_content[:300]})
    return out


def answer(question: str, session_id: str = "default") -> dict:
    history = SESSIONS.setdefault(session_id, [])
    llm = get_llm()
    query = _condense(llm, history, question)
    hits = retrieve(query)
    conf = confidence(hits)
    relevant = [(d, s) for d, s in hits if s >= MIN_SCORE]

    if not relevant:
        text, sources = NO_ANSWER, []
    elif llm is None:  # no API key: extractive fallback so the app still works
        text = ("(LLM disabled — showing top matching excerpts)\n\n" + "\n\n".join(
            f"• {d.metadata['doc_id']} §{d.metadata['section']} p.{d.metadata['page']}: "
            f"{d.page_content[:250]}" for d, _ in relevant))
        sources = _sources(relevant)
    else:
        msgs = [("system", SYSTEM)]
        for role, t in history[-6:]:
            msgs.append(("human" if role == "user" else "ai", t))
        msgs.append(("human", f"Context:\n{_format_context(relevant)}\n\nQuestion: {question}"))
        text = str(llm.invoke(msgs).content)
        sources = _sources(relevant)

    history += [("user", question), ("assistant", text)]
    return {"answer": text, "confidence": conf, "sources": sources,
            "session_id": session_id, "search_query": query}


def reset(session_id: str) -> None:
    SESSIONS.pop(session_id, None)
