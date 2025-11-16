"""
Directory Watcher Utility

Detect new files in a directory. Uses watchdog when available, otherwise falls back to polling by mtime.
"""

from pathlib import Path
from typing import List, Set
import time

try:
    from watchdog.observers import Observer  # type: ignore
    from watchdog.events import FileSystemEventHandler  # type: ignore
    WATCHDOG_AVAILABLE = True
except Exception:
    WATCHDOG_AVAILABLE = False


class PollingWatcher:
    """Simple polling-based watcher that records seen files by mtime."""

    def __init__(self, directory: Path, patterns: Set[str]):
        self.directory = Path(directory)
        self.patterns = {p.lower() for p in patterns}
        self._seen: dict[str, float] = {}

    def scan(self) -> List[Path]:
        if not self.directory.exists():
            return []
        new_files: List[Path] = []
        for p in self.directory.iterdir():
            if not p.is_file():
                continue
            if p.suffix.lower() not in self.patterns:
                continue
            mtime = p.stat().st_mtime
            key = str(p)
            if key not in self._seen or self._seen[key] < mtime:
                # Consider as new/updated
                new_files.append(p)
                self._seen[key] = mtime
        return new_files


def get_new_files(directory: Path, patterns: List[str], seen: Set[str] | None = None) -> List[Path]:
    """
    Return list of new files in directory matching patterns. Stateless convenience.
    """
    directory = Path(directory)
    pats = {s.lower() for s in patterns}
    if not directory.exists():
        return []
    results: List[Path] = []
    for p in directory.iterdir():
        if p.is_file() and p.suffix.lower() in pats:
            if seen is None or str(p) not in seen:
                results.append(p)
    return results
