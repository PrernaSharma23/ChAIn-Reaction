
import threading
from src.util.logger import log


def run_async(func, *args, **kwargs):
    thread = threading.Thread(target=_run_with_error_handling, args=(func, args, kwargs), daemon=True)
    thread.start()


def _run_with_error_handling(func, args, kwargs):
    try:
        func(*args, **kwargs)
    except Exception as e:
        log.error(f"Background task failed: {e}", exc_info=True)
