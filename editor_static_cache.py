from __future__ import annotations

from datetime import timezone
from email.utils import formatdate, parsedate_to_datetime
from pathlib import Path


EDITOR_STATIC_CACHE_CONTROL = "private, max-age=0, must-revalidate"
EDITOR_STATIC_CACHE_PREFIXES = (
    "/prototype_editor/",
    "/export_player_template/",
    "/template_project/assets/",
    "/projects/",
)
EDITOR_STATIC_CACHE_EXCLUDED_PARTS = (
    "/data/",
    "/.canvasia_history/",
    "/.tony_na_history/",
)
EDITOR_STATIC_CACHE_EXTENSIONS = {
    ".avif",
    ".css",
    ".gif",
    ".html",
    ".ico",
    ".jpeg",
    ".jpg",
    ".js",
    ".m4a",
    ".mp3",
    ".mp4",
    ".ogg",
    ".otf",
    ".png",
    ".svg",
    ".ttf",
    ".wav",
    ".webm",
    ".webp",
    ".woff",
    ".woff2",
}


def normalize_request_path(path: str) -> str:
    clean_path = "/" + str(path or "").split("?", 1)[0].split("#", 1)[0].lstrip("/")
    return clean_path.replace("\\", "/")


def is_editor_static_cache_candidate(request_path: str, file_path: Path) -> bool:
    clean_path = normalize_request_path(request_path)
    if not any(clean_path.startswith(prefix) for prefix in EDITOR_STATIC_CACHE_PREFIXES):
        return False
    if any(part in clean_path for part in EDITOR_STATIC_CACHE_EXCLUDED_PARTS):
        return False
    if file_path.suffix.lower() not in EDITOR_STATIC_CACHE_EXTENSIONS:
        return False
    try:
        return file_path.is_file()
    except OSError:
        return False


def build_editor_static_etag(file_path: Path) -> str:
    stat_result = file_path.stat()
    return f'W/"canvasia-{stat_result.st_size:x}-{stat_result.st_mtime_ns:x}"'


def build_editor_static_cache_headers(file_path: Path) -> dict[str, str]:
    stat_result = file_path.stat()
    return {
        "Cache-Control": EDITOR_STATIC_CACHE_CONTROL,
        "ETag": build_editor_static_etag(file_path),
        "Last-Modified": formatdate(stat_result.st_mtime, usegmt=True),
    }


def normalize_etag(value: str) -> str:
    return str(value or "").strip().removeprefix("W/")


def request_etag_matches(if_none_match_header: str | None, etag: str) -> bool:
    if not if_none_match_header:
        return False
    request_etags = [item.strip() for item in if_none_match_header.split(",") if item.strip()]
    if "*" in request_etags:
        return True
    normalized_etag = normalize_etag(etag)
    return any(item == etag or normalize_etag(item) == normalized_etag for item in request_etags)


def request_modified_since_matches(if_modified_since_header: str | None, file_path: Path) -> bool:
    if not if_modified_since_header:
        return False
    try:
        request_datetime = parsedate_to_datetime(if_modified_since_header)
    except (IndexError, OverflowError, TypeError, ValueError):
        return False
    if request_datetime is None:
        return False
    if request_datetime.tzinfo is None:
        request_datetime = request_datetime.replace(tzinfo=timezone.utc)
    try:
        modified_at_seconds = int(file_path.stat().st_mtime)
    except OSError:
        return False
    return modified_at_seconds <= int(request_datetime.timestamp())


__all__ = [
    "EDITOR_STATIC_CACHE_CONTROL",
    "build_editor_static_cache_headers",
    "build_editor_static_etag",
    "is_editor_static_cache_candidate",
    "normalize_request_path",
    "request_etag_matches",
    "request_modified_since_matches",
]
