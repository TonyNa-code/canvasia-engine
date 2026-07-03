from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Hashable


CacheSignature = Hashable


def build_file_cache_signature(path: Path) -> tuple:
    try:
        stat_result = path.stat()
    except OSError:
        return (path.as_posix(), "missing")

    return (
        path.as_posix(),
        "file" if path.is_file() else "other",
        stat_result.st_size,
        stat_result.st_mtime_ns,
    )


@dataclass
class SnapshotCache:
    signature: CacheSignature | None = None
    payload: Any = None

    def clear(self) -> None:
        self.signature = None
        self.payload = None

    def get_or_build(
        self,
        build_signature: Callable[[], CacheSignature],
        build_payload: Callable[[], Any],
    ) -> Any:
        current_signature = build_signature()
        if self.payload is not None and self.signature == current_signature:
            return copy.deepcopy(self.payload)

        payload = build_payload()
        self.signature = build_signature()
        self.payload = copy.deepcopy(payload)
        return payload
