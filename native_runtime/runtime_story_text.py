from __future__ import annotations

from typing import Any

try:
    from .runtime_rich_text import (
        map_runtime_rich_text_source_index,
        parse_runtime_rich_text,
    )
    from .runtime_text_pacing import parse_runtime_text_pacing
except ImportError:  # pragma: no cover - exported native packages import from the same directory.
    from runtime_rich_text import (
        map_runtime_rich_text_source_index,
        parse_runtime_rich_text,
    )
    from runtime_text_pacing import parse_runtime_text_pacing


def parse_runtime_story_text(value: Any) -> dict[str, Any]:
    source_text = str(value or "")
    pacing_plan = parse_runtime_text_pacing(source_text)
    rich_plan = parse_runtime_rich_text(pacing_plan["plainText"])
    cues = [
        {
            **cue,
            "index": map_runtime_rich_text_source_index(rich_plan, cue.get("index")),
        }
        for cue in pacing_plan.get("cues") or []
    ]
    return {
        "sourceText": source_text,
        "plainText": rich_plan["plainText"],
        "cues": cues,
        "segments": rich_plan["segments"],
        "hasCues": bool(cues),
        "hasMarkup": bool(rich_plan["hasMarkup"]),
    }


def strip_runtime_story_text(value: Any) -> str:
    return str(parse_runtime_story_text(value)["plainText"])
