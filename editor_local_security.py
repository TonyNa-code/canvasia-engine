from __future__ import annotations

from urllib.parse import urlparse


LOCAL_EDITOR_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


def extract_host_from_header(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""

    if text.startswith("["):
        bracket_end = text.find("]")
        return text[1:bracket_end] if bracket_end > 0 else text

    return text.rsplit(":", 1)[0] if text.count(":") == 1 else text


def is_local_editor_host(value: object) -> bool:
    host = extract_host_from_header(value).lower().rstrip(".")
    return host in LOCAL_EDITOR_HOSTS


def is_local_editor_origin(value: object) -> bool:
    text = str(value or "").strip()
    if not text:
        return True
    if text == "null":
        return False

    parsed = urlparse(text)
    return parsed.scheme in {"http", "https"} and is_local_editor_host(parsed.netloc)
