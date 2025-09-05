import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = str(BASE_DIR / "data")
POLICY_DIR = os.getenv("POLICY_DIR", str(Path(DATA_DIR) / "policies"))
SKILL_DIR = os.getenv("SKILL_DIR", str(Path(DATA_DIR) / "skills"))

# Vector store
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "chroma_db"))

# Audit
AURORA_SECRET_KEY = os.getenv("AURORA_SECRET_KEY", "CHANGE_ME_FOR_PROD")
AUDIT_DB_PATH = os.getenv("AUDIT_DB_PATH", str(BASE_DIR / "audit.db"))

# Retrieval defaults
TOP_K = int(os.getenv("RETRIEVE_TOP_K", "4"))
MIN_SCORE = float(os.getenv("RETRIEVE_MIN_SCORE", "0.0"))

SERVICE_NAME = os.getenv("SERVICE_NAME", "aurora-backend")
ENV = os.getenv("ENV", "dev")
