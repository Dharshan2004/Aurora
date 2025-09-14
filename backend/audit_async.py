import queue, threading
from audit_store import SessionLocal, AuditEvent

_q = queue.Queue(maxsize=10000)

def _worker():
    while True:
        item = _q.get()
        if item is None:
            break
        try:
            with SessionLocal() as s:
                s.add(AuditEvent(**item))
                s.commit()
        except Exception:
            pass
        finally:
            _q.task_done()

_thread = threading.Thread(target=_worker, daemon=True)
_thread.start()

def audit_enqueue(event: dict):
    try:
        _q.put_nowait(event)
    except queue.Full:
        pass
