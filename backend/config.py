import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = str(BASE_DIR / "data")
POLICY_DIR = os.getenv("POLICY_DIR", str(Path(DATA_DIR) / "policies"))
SKILL_MAP_DIR = os.getenv("SKILL_MAP_DIR", str(Path(DATA_DIR) / "skills"))

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

# LLM
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "512"))