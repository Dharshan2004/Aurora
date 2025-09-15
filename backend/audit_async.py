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
        except Exception as e:
            error_msg = str(e).lower()
            if "readonly" in error_msg or "read-only" in error_msg:
                # Silently skip audit logging for read-only databases
                pass
            else:
                # Log other errors for debugging
                print(f"Audit logging error: {e}")
        finally:
            _q.task_done()

_thread = threading.Thread(target=_worker, daemon=True)
_thread.start()

def audit_enqueue(event: dict):
    try:
        _q.put_nowait(event)
    except queue.Full:
        pass
