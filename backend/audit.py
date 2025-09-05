import json, time, sqlite3, hmac, hashlib, threading, queue
from dataclasses import dataclass
from .config import AUDIT_DB_PATH, AURORA_SECRET_KEY

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts_utc INTEGER NOT NULL,
  org_id TEXT,
  user_id TEXT,
  agent_id TEXT NOT NULL,
  question TEXT,
  answer TEXT,
  citations_json TEXT,
  retrieved_docs_json TEXT,
  model_id TEXT,
  latency_ms INTEGER,
  tokens_in INTEGER,
  tokens_out INTEGER,
  consent INTEGER DEFAULT 0,
  hmac_sha256 TEXT NOT NULL
);
"""

@dataclass
class AuditEvent:
    org_id: str | None
    user_id: str | None
    agent_id: str
    question: str | None
    answer: str | None
    citations: list
    retrieved_docs: list
    model_id: str | None
    latency_ms: int | None
    tokens_in: int | None
    tokens_out: int | None
    consent: bool

class AuditLogger:
    def __init__(self, db_path: str = AUDIT_DB_PATH):
        self.db_path = db_path
        self.q: "queue.Queue[AuditEvent]" = queue.Queue(maxsize=10000)
        self._init()
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def _init(self):
        with sqlite3.connect(self.db_path) as con:
            con.execute(SCHEMA); con.commit()

    def log_async(self, e: AuditEvent):
        try: self.q.put_nowait(e)
        except queue.Full: pass

    def _loop(self):
        while True:
            try: e = self.q.get(timeout=0.25)
            except queue.Empty: continue
            payload = {
                "org_id": e.org_id, "user_id": e.user_id, "agent_id": e.agent_id,
                "question": e.question, "answer": e.answer,
                "citations_json": json.dumps(e.citations, ensure_ascii=False),
                "retrieved_docs_json": json.dumps(e.retrieved_docs, ensure_ascii=False),
                "model_id": e.model_id, "latency_ms": e.latency_ms,
                "tokens_in": e.tokens_in, "tokens_out": e.tokens_out,
                "consent": int(bool(e.consent)),
            }
            canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
            sig = hmac.new(AURORA_SECRET_KEY.encode(), canonical, hashlib.sha256).hexdigest()
            with sqlite3.connect(self.db_path) as con:
                con.execute(
                    """INSERT INTO audit_events
                       (ts_utc, org_id, user_id, agent_id, question, answer, citations_json,
                        retrieved_docs_json, model_id, latency_ms, tokens_in, tokens_out,
                        consent, hmac_sha256)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (int(time.time()),
                     payload["org_id"], payload["user_id"], payload["agent_id"],
                     payload["question"], payload["answer"], payload["citations_json"],
                     payload["retrieved_docs_json"], payload["model_id"],
                     payload["latency_ms"], payload["tokens_in"], payload["tokens_out"],
                     payload["consent"], sig)
                )
                con.commit()

    # Admin helpers
    def count(self) -> int:
        with sqlite3.connect(self.db_path) as con:
            return int(con.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0])

    def export_last(self, n: int) -> list[dict]:
        with sqlite3.connect(self.db_path) as con:
            cur = con.execute(
                "SELECT ts_utc, org_id, user_id, agent_id, question, answer, "
                "citations_json, retrieved_docs_json, model_id, latency_ms, "
                "tokens_in, tokens_out, consent, hmac_sha256 "
                "FROM audit_events ORDER BY id DESC LIMIT ?", (n,))
            rows = cur.fetchall()
        out = []
        for r in rows:
            out.append({
                "ts_utc": r[0], "org_id": r[1], "user_id": r[2], "agent_id": r[3],
                "question": r[4], "answer": r[5],
                "citations": json.loads(r[6] or "[]"),
                "retrieved_docs": json.loads(r[7] or "[]"),
                "model_id": r[8], "latency_ms": r[9],
                "tokens_in": r[10], "tokens_out": r[11],
                "consent": bool(r[12]), "hmac_sha256": r[13],
            })
        return out

AUDIT = AuditLogger()
