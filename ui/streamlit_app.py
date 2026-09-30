import os
import uuid

import requests
import streamlit as st

API = os.getenv("API_URL", "http://localhost:8000")
BADGE = {"high": "🟢 High", "medium": "🟡 Medium", "low": "🟠 Low", "none": "🔴 No evidence"}

st.set_page_config(page_title="Engineering Copilot", page_icon="🔧", layout="wide")
st.title("🔧 Engineering Copilot")

if "sid" not in st.session_state:
    st.session_state.sid = str(uuid.uuid4())
    st.session_state.msgs = []

with st.sidebar:
    st.header("Documents")
    files = st.file_uploader("Upload engineering PDFs", type="pdf", accept_multiple_files=True)
    if files and st.button("Ingest"):
        for f in files:
            r = requests.post(f"{API}/upload", files={"file": (f.name, f.getvalue(), "application/pdf")})
            if r.ok:
                i = r.json()
                st.success(f"{i['doc_id']}: {i['pages']} pages, {i['chunks']} chunks")
            else:
                st.error(f"{f.name}: {r.json().get('detail', r.text)}")
    try:
        docs = requests.get(f"{API}/documents").json()
        st.caption(f"{len(docs)} document(s) indexed")
        for d in docs:
            st.write(f"• **{d['doc_id']}** — {d['source']}")
    except Exception:
        st.warning("API not reachable. Start it with: uvicorn app.api:app --reload")
    if st.button("New conversation"):
        requests.delete(f"{API}/chat/{st.session_state.sid}")
        st.session_state.msgs = []
        st.rerun()

for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("meta"):
            c = m["meta"]["confidence"]
            st.caption(f"Evidence: {BADGE[c['level']]} (top similarity {c['score']})")
            if m["meta"]["sources"]:
                with st.expander("Sources"):
                    for s in m["meta"]["sources"]:
                        st.markdown(f"**{s['doc_id']}** · §{s['section']} · p.{s['page']} · "
                                    f"{s['type']} · score {s['score']}\n\n> {s['snippet']}")

if q := st.chat_input("Ask about past projects, manuals, maintenance records…"):
    st.session_state.msgs.append({"role": "user", "content": q})
    r = requests.post(f"{API}/chat", json={"question": q, "session_id": st.session_state.sid})
    if r.ok:
        data = r.json()
        st.session_state.msgs.append({"role": "assistant", "content": data["answer"], "meta": data})
    else:
        st.session_state.msgs.append({"role": "assistant", "content": f"Error: {r.text}"})
    st.rerun()
