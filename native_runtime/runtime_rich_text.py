from __future__ import annotations

import re
from typing import Any


RUNTIME_RICH_TEXT_KINDS = ("emphasis", "whisper", "color", "ruby")
_RICH_TEXT_MARKER_PATTERN = re.compile(
    r"\[\[\s*(em|whisper|color|ruby)\s*=\s*([^\[\]]*?)\s*\]\]",
    re.IGNORECASE,
)
_SAFE_COLOR_PATTERN = re.compile(r"^#[0-9a-f]{6}$", re.IGNORECASE)


def _parse_marker(command: Any, payload: Any) -> dict[str, Any] | None:
    safe_command = str(command or "").strip().lower()
    safe_payload = str(payload or "")
    if safe_command in {"em", "whisper"}:
        if not safe_payload:
            return None
        return {
            "type": "emphasis" if safe_command == "em" else "whisper",
            "text": safe_payload,
        }

    separator_index = safe_payload.find("|")
    if separator_index <= 0 or separator_index >= len(safe_payload) - 1:
        return None
    left = safe_payload[:separator_index].strip()
    right = safe_payload[separator_index + 1 :]
    if safe_command == "color":
        color = left.lower() if _SAFE_COLOR_PATTERN.fullmatch(left) else ""
        return {"type": "color", "color": color, "text": right} if color and right else None
    if safe_command == "ruby":
        annotation = right.strip()[:48]
        return {"type": "ruby", "text": left, "annotation": annotation} if left and annotation else None
    return None


def _append_literal(
    source_text: str,
    source_start: int,
    source_end: int,
    plain_parts: list[str],
    source_to_plain: list[int],
    plain_length: int,
) -> int:
    literal = source_text[source_start:source_end]
    plain_parts.append(literal)
    for offset in range(len(literal) + 1):
        source_to_plain[source_start + offset] = plain_length + offset
    return plain_length + len(literal)


def parse_runtime_rich_text(value: Any) -> dict[str, Any]:
    source_text = str(value or "")
    plain_parts: list[str] = []
    segments: list[dict[str, Any]] = []
    source_to_plain = [0] * (len(source_text) + 1)
    source_index = 0
    plain_length = 0

    for match in _RICH_TEXT_MARKER_PATTERN.finditer(source_text):
        plain_length = _append_literal(
            source_text,
            source_index,
            match.start(),
            plain_parts,
            source_to_plain,
            plain_length,
        )
        marker = _parse_marker(match.group(1), match.group(2))
        if marker is None:
            plain_length = _append_literal(
                source_text,
                match.start(),
                match.end(),
                plain_parts,
                source_to_plain,
                plain_length,
            )
            source_index = match.end()
            continue

        for index in range(match.start(), match.end()):
            source_to_plain[index] = plain_length
        segment_start = plain_length
        plain_parts.append(str(marker["text"]))
        plain_length += len(str(marker["text"]))
        source_to_plain[match.end()] = plain_length
        segments.append({**marker, "start": segment_start, "end": plain_length})
        source_index = match.end()

    plain_length = _append_literal(
        source_text,
        source_index,
        len(source_text),
        plain_parts,
        source_to_plain,
        plain_length,
    )
    source_to_plain[len(source_text)] = plain_length
    return {
        "sourceText": source_text,
        "plainText": "".join(plain_parts),
        "segments": segments,
        "sourceToPlain": source_to_plain,
        "hasMarkup": bool(segments),
    }


def strip_runtime_rich_text(value: Any) -> str:
    return str(parse_runtime_rich_text(value)["plainText"])


def map_runtime_rich_text_source_index(plan: dict[str, Any] | None, source_index: Any) -> int:
    mapping = list((plan or {}).get("sourceToPlain") or [0])
    try:
        safe_index = int(source_index or 0)
    except (TypeError, ValueError):
        safe_index = 0
    safe_index = max(0, min(safe_index, len(mapping) - 1))
    try:
        return int(mapping[safe_index] or 0)
    except (TypeError, ValueError):
        return 0


def build_runtime_rich_text_summary(value: Any) -> dict[str, Any]:
    plan = parse_runtime_rich_text(value)
    counts = {kind: 0 for kind in RUNTIME_RICH_TEXT_KINDS}
    for segment in plan["segments"]:
        counts[str(segment.get("type") or "")] += 1
    label_parts = []
    for kind, suffix in (
        ("emphasis", "处强调"),
        ("whisper", "处低声"),
        ("color", "处变色"),
        ("ruby", "处注音"),
    ):
        if counts[kind]:
            label_parts.append(f"{counts[kind]} {suffix}")
    return {
        **counts,
        "hasMarkup": bool(plan["hasMarkup"]),
        "label": " · ".join(label_parts) if label_parts else "使用普通文字",
    }
