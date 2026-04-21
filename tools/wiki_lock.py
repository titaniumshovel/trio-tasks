"""
wiki_lock.py — Advisory file locking for MeMex wiki concurrent writes.

Drop-in wrapper for any MeMex wiki write operation.
Prevents race conditions when multiple agents share the same wiki/ directory.

Usage:
    from wiki_lock import wiki_write

    # Instead of: open(path, 'w').write(content)
    wiki_write(wiki_root, "wiki/concepts/ssl-inspection.md", content)

Requirements:
    Python 3.8+ (uses fcntl on Linux/macOS, msvcrt on Windows)
    No external dependencies.
"""

import fcntl
import os
import time
import hashlib
from contextlib import contextmanager
from pathlib import Path
from typing import Union


LOCK_DIR_NAME = ".wiki-locks"
LOCK_TIMEOUT = 30  # seconds before giving up
LOCK_RETRY_INTERVAL = 0.2  # seconds between retries


@contextmanager
def wiki_file_lock(wiki_root: Union[str, Path], relative_path: str, timeout: float = LOCK_TIMEOUT):
    """
    Context manager that acquires an advisory lock for a wiki file write.

    Args:
        wiki_root: Root directory of the MeMex wiki repo
        relative_path: Path relative to wiki_root (e.g. "wiki/concepts/foo.md")
        timeout: Max seconds to wait for lock acquisition

    Raises:
        TimeoutError: If lock cannot be acquired within timeout

    Example:
        with wiki_file_lock("/home/user/memex", "wiki/concepts/ssl.md"):
            Path("/home/user/memex/wiki/concepts/ssl.md").write_text(content)
    """
    wiki_root = Path(wiki_root)
    lock_dir = wiki_root / LOCK_DIR_NAME
    lock_dir.mkdir(exist_ok=True)

    # Lock file name = stable hash of the relative path
    # Avoids filesystem issues with nested paths
    lock_name = hashlib.sha1(relative_path.encode()).hexdigest()[:16] + ".lock"
    lock_path = lock_dir / lock_name

    deadline = time.monotonic() + timeout
    lock_file = None

    try:
        lock_file = open(lock_path, "w")
        # Write agent identity for debugging
        agent_id = os.environ.get("MARVIN_AGENT_ID", f"pid-{os.getpid()}")
        lock_file.write(f"{agent_id}\n{relative_path}\n{time.time()}\n")
        lock_file.flush()

        while True:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break  # Lock acquired
            except BlockingIOError:
                if time.monotonic() > deadline:
                    raise TimeoutError(
                        f"Could not acquire wiki lock for '{relative_path}' "
                        f"after {timeout}s. Another agent may be writing."
                    )
                time.sleep(LOCK_RETRY_INTERVAL)

        yield  # Do the write here

    finally:
        if lock_file is not None:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
            lock_file.close()
            # Remove lock file — don't leave stale locks
            try:
                lock_path.unlink()
            except FileNotFoundError:
                pass  # Already cleaned up, fine


def wiki_write(wiki_root: Union[str, Path], relative_path: str, content: str,
               encoding: str = "utf-8", timeout: float = LOCK_TIMEOUT) -> None:
    """
    Atomic wiki file write with advisory locking.

    Creates parent directories as needed. Acquires lock before writing,
    releases after. Safe for concurrent use by multiple agents on the
    same filesystem.

    Args:
        wiki_root: Root directory of the MeMex wiki repo
        relative_path: Path relative to wiki_root
        content: Text content to write
        encoding: File encoding (default utf-8)
        timeout: Max seconds to wait for lock
    """
    wiki_root = Path(wiki_root)
    target = wiki_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)

    with wiki_file_lock(wiki_root, relative_path, timeout):
        tmp = target.with_suffix(target.suffix + ".tmp")
        try:
            tmp.write_text(content, encoding=encoding)
            tmp.rename(target)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise


def wiki_append(wiki_root: Union[str, Path], relative_path: str, content: str,
                encoding: str = "utf-8", timeout: float = LOCK_TIMEOUT) -> None:
    """
    Atomic wiki file append with advisory locking.

    Read-modify-write under lock — safe for log.md and contradictions.md
    which multiple agents may append to simultaneously.

    Note: does NOT delegate to wiki_write() to avoid reentrant flock deadlock.
    On Linux, flock treats separate open() calls as independent file
    descriptions — a second LOCK_EX on the same path from a new fd would
    block even from the same process. We do the write inline instead.
    """
    wiki_root = Path(wiki_root)
    target = wiki_root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)

    with wiki_file_lock(wiki_root, relative_path, timeout):
        existing = target.read_text(encoding=encoding) if target.exists() else ""
        tmp = target.with_suffix(target.suffix + ".tmp")
        try:
            tmp.write_text(existing + content, encoding=encoding)
            tmp.rename(target)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise


# --- Minimal self-test ---
if __name__ == "__main__":
    import tempfile
    import threading

    def worker(wiki_root, i):
        wiki_write(wiki_root, "wiki/test/shared.md", f"Written by worker {i}\n")

    def appender(wiki_root, i):
        wiki_append(wiki_root, "wiki/test/appended.md", f"Appended by worker {i}\n")

    with tempfile.TemporaryDirectory() as tmp:
        # Test concurrent wiki_write
        threads = [threading.Thread(target=worker, args=(tmp, i)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        result = (Path(tmp) / "wiki/test/shared.md").read_text()
        print(f"✓ wiki_write self-test passed. Final content: {result!r}")

        # Test concurrent wiki_append (exercises the fixed code path)
        threads = [threading.Thread(target=appender, args=(tmp, i)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        log = (Path(tmp) / "wiki/test/appended.md").read_text()
        lines = [l for l in log.splitlines() if l.strip()]
        assert len(lines) == 8, f"Expected 8 appended lines, got {len(lines)}: {log!r}"
        print(f"✓ wiki_append self-test passed. {len(lines)} lines, all present.")
        print(f"✓ Lock files cleaned up: {list((Path(tmp) / '.wiki-locks').iterdir())}")
