"""
Central configuration. Everything that might need to change (API key, model
names, folder locations) lives here and is read from environment variables /
the .env file, so nobody has to edit Python code to reconfigure the app.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# backend/.env
BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

DATA_DIR = BACKEND_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma_db"
DB_PATH = DATA_DIR / "app.db"
EXCEL_PATH = DATA_DIR / "Master_Candidate_Database.xlsx"

for d in (DATA_DIR, UPLOADS_DIR, CHROMA_DIR):
    d.mkdir(parents=True, exist_ok=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Two separate models, tuned for two different jobs. Each is high-volume/cheap
# vs. low-volume/quality-sensitive respectively - see GEMINI_SETUP.md for why.
# Change either any time (no code changes needed).

# EXTRACTION runs on every uploaded file (high volume, mechanical task) ->
# a "Lite" model is plenty and keeps bulk-upload cost down.
GEMINI_EXTRACTION_MODEL = os.getenv("GEMINI_EXTRACTION_MODEL", "gemini-3.5-flash-lite").strip()

# CHAT answers recruiter questions (lower volume, quality matters more) ->
# the full Flash model gives noticeably better reasoning/comparison answers.
GEMINI_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-3.5-flash").strip()

# Back-compat: if someone still sets the old single GEMINI_MODEL var, use it
# for both jobs unless the specific vars above are also set.
_legacy_model = os.getenv("GEMINI_MODEL", "").strip()
if _legacy_model:
    GEMINI_EXTRACTION_MODEL = os.getenv("GEMINI_EXTRACTION_MODEL", _legacy_model).strip()
    GEMINI_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", _legacy_model).strip()

# Embedding model used for the RAG vector store (same job either way, so just one).
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001").strip()
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "768"))

DATABASE_URL = f"sqlite:///{DB_PATH}"

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "20"))
