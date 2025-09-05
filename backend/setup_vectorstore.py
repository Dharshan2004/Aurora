from pathlib import Path
from .rag.vector_store import build_vectorstore
from .config import POLICY_DIR

if __name__ == "__main__":
    p = Path(POLICY_DIR)
    if not p.exists():
        raise SystemExit(f"Policy dir not found: {p}")
    build_vectorstore(str(p))
    print("Indexed policies into Chroma.")
