"""
File cache with change detection
"""
import hashlib
from pathlib import Path
from typing import Dict, Optional

class FileCache:
    """Cache file contents with change detection"""

    def __init__(self):
        self.cache: Dict[str, tuple] = {}  # path -> (content, mtime, checksum)

    def get(self, path: Path) -> Optional[str]:
        """Get file content, checking for changes"""
        path_str = str(path)
        if not path.exists():
            return None

        current_mtime = path.stat().st_mtime
        current_checksum = self._get_checksum(path)

        if path_str in self.cache:
            cached_content, cached_mtime, cached_checksum = self.cache[path_str]
            if current_mtime == cached_mtime and current_checksum == cached_checksum:
                return cached_content

        # Read fresh
        try:
            content = path.read_text(encoding='utf-8')
            self.cache[path_str] = (content, current_mtime, current_checksum)
            return content
        except Exception:
            return None

    def _get_checksum(self, path: Path) -> str:
        """Get file checksum"""
        try:
            return hashlib.md5(path.read_bytes()).hexdigest()
        except Exception:
            return ""

    def invalidate(self, path: str):
        """Invalidate cache for a specific file"""
        if path in self.cache:
            del self.cache[path]

    def invalidate_pattern(self, pattern: str):
        """Invalidate cache for files matching pattern"""
        paths_to_remove = [p for p in self.cache.keys() if pattern in p]
        for p in paths_to_remove:
            del self.cache[p]

    def invalidate_all(self):
        """Clear entire cache"""
        self.cache.clear()


# Global file cache instance
file_cache = FileCache()
