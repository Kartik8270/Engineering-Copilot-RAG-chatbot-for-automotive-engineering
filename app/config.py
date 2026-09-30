import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE / "data" / "uploads"
CHROMA_DIR = BASE / "data" / "chroma"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-6")
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

TOP_K = int(os.getenv("TOP_K", "5"))
MIN_SCORE = float(os.getenv("MIN_SCORE", "0.30"))    # below this: "not in documents"
HIGH_SCORE = float(os.getenv("HIGH_SCORE", "0.55"))  # at/above this: high confidence
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
