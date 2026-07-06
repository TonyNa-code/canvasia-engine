from __future__ import annotations

import re
import unicodedata

try:
    from .runtime_player_settings import TEXT_SPEED_PRESETS, get_safe_text_speed
except ImportError:  # pragma: no cover - exported native packages import from the same directory.
    from runtime_player_settings import TEXT_SPEED_PRESETS, get_safe_text_speed


TYPEWRITER_SENTENCE_PAUSE_MS = 260
TYPEWRITER_CLAUSE_PAUSE_MS = 140
TYPEWRITER_ELLIPSIS_PAUSE_MS = 220
TYPEWRITER_LEADING_OPENERS = "“‘\"'（([{【〔〈《「『"
TYPEWRITER_TRAILING_CLOSERS = "”’\"'）)]}】〕〉》」』"
TYPEWRITER_PERIOD_ABBREVIATIONS = {
    "mr",
    "mrs",
    "ms",
    "dr",
    "prof",
    "sr",
    "jr",
    "st",
    "vs",
    "etc",
    "e.g",
    "i.e",
    "u.s",
    "u.k",
    "no",
    "fig",
    "vol",
    "ch",
    "dept",
    "inc",
    "ltd",
    "co",
}


def is_regional_indicator_symbol(char: str) -> bool:
    if not char:
        return False
    return 0x1F1E6 <= ord(char[0]) <= 0x1F1FF


def is_typewriter_grapheme_extension(char: str) -> bool:
    if not char:
        return False
    code_point = ord(char[0])
    return (
        unicodedata.category(char[0]) in {"Mn", "Mc", "Me"}
        or 0xFE00 <= code_point <= 0xFE0F
        or 0xE0100 <= code_point <= 0xE01EF
        or 0x1F3FB <= code_point <= 0x1F3FF
    )


def get_next_typewriter_cluster_index(text: str, current_index: int) -> int:
    safe_text = str(text or "")
    safe_index = max(0, min(len(safe_text), int(current_index or 0)))
    if safe_index >= len(safe_text):
        return len(safe_text)

    next_index = safe_index + 1

    if (
        is_regional_indicator_symbol(safe_text[safe_index])
        and next_index < len(safe_text)
        and is_regional_indicator_symbol(safe_text[next_index])
    ):
        return next_index + 1

    while next_index < len(safe_text):
        current_char = safe_text[next_index]
        previous_char = safe_text[next_index - 1] if next_index > 0 else ""

        if is_typewriter_grapheme_extension(current_char):
            next_index += 1
            continue
        if previous_char == "\u200d":
            next_index += 1
            continue
        if current_char == "\u200d":
            next_index = min(len(safe_text), next_index + 2)
            continue
        break

    return next_index


def get_next_typewriter_index(text: str, current_index: int) -> int:
    safe_text = str(text or "")
    safe_index = max(0, min(len(safe_text), int(current_index or 0)))
    if safe_index >= len(safe_text):
        return len(safe_text)

    next_index = get_next_typewriter_cluster_index(safe_text, safe_index)
    current_char = safe_text[safe_index]
    next_index = include_typewriter_leading_follower(safe_text, safe_index, next_index)

    if re.match(r"[A-Za-z0-9]", current_char):
        grouped = 1
        while next_index < len(safe_text) and grouped < 3 and re.match(r"[A-Za-z0-9]", safe_text[next_index]):
            next_index = get_next_typewriter_cluster_index(safe_text, next_index)
            grouped += 1

    next_index = include_typewriter_trailing_closers(safe_text, next_index)

    while next_index < len(safe_text) and safe_text[next_index].isspace():
        next_index = get_next_typewriter_cluster_index(safe_text, next_index)
    return next_index


def include_typewriter_leading_follower(text: str, current_index: int, index: int) -> int:
    safe_text = str(text or "")
    safe_current_index = max(0, min(len(safe_text), int(current_index or 0)))
    next_index = max(0, min(len(safe_text), int(index or 0)))
    if safe_current_index >= len(safe_text) or safe_text[safe_current_index] not in TYPEWRITER_LEADING_OPENERS:
        return next_index

    while next_index < len(safe_text) and safe_text[next_index] in TYPEWRITER_LEADING_OPENERS:
        next_index = get_next_typewriter_cluster_index(safe_text, next_index)

    return get_next_typewriter_cluster_index(safe_text, next_index) if next_index < len(safe_text) else next_index


def include_typewriter_trailing_closers(text: str, index: int) -> int:
    safe_text = str(text or "")
    next_index = max(0, min(len(safe_text), int(index or 0)))
    while next_index < len(safe_text) and safe_text[next_index] in TYPEWRITER_TRAILING_CLOSERS:
        next_index += 1
    return next_index


def get_typewriter_punctuation_pause_ms(text: str, full_text: str = "") -> int:
    anchor_text = get_typewriter_pause_anchor_text(text)
    anchor_char = get_typewriter_pause_anchor_char(text)
    if re.search(r"(?:\.{3,}|…+)$", anchor_text):
        return TYPEWRITER_ELLIPSIS_PAUSE_MS
    if anchor_char == "." and is_typewriter_inline_period(anchor_text, full_text):
        return 0
    if anchor_char == "." and is_typewriter_abbreviation_period(anchor_text, full_text):
        return 0
    if anchor_char in "。！？!?.":
        return TYPEWRITER_SENTENCE_PAUSE_MS
    if anchor_char in "…—-":
        return TYPEWRITER_ELLIPSIS_PAUSE_MS
    if anchor_char in "，、；;：:,":
        return TYPEWRITER_CLAUSE_PAUSE_MS
    return 0


def get_typewriter_pause_anchor_text(text: str) -> str:
    chars = list(str(text or "").rstrip())
    while len(chars) > 1 and chars[-1] in TYPEWRITER_TRAILING_CLOSERS:
        chars.pop()
    return "".join(chars)


def get_typewriter_pause_anchor_char(text: str) -> str:
    chars = list(get_typewriter_pause_anchor_text(text))
    return chars[-1] if chars else ""


def is_typewriter_inline_period(anchor_text: str, full_text: str = "") -> bool:
    safe_anchor_text = str(anchor_text or "")
    safe_full_text = str(full_text or "")
    previous_char = safe_anchor_text[-2] if len(safe_anchor_text) >= 2 else ""
    next_char = safe_full_text[len(safe_anchor_text) : len(safe_anchor_text) + 1]
    return bool(re.match(r"[A-Za-z0-9]", previous_char) and re.match(r"[A-Za-z0-9]", next_char))


def is_typewriter_abbreviation_period(anchor_text: str, full_text: str = "") -> bool:
    safe_anchor_text = str(anchor_text or "")
    safe_full_text = str(full_text or "")
    token_match = re.search(r"([A-Za-z](?:[A-Za-z]|\.)*)\.$", safe_anchor_text)
    token = token_match.group(1).lower() if token_match else ""
    next_char = safe_full_text[len(safe_anchor_text) : len(safe_anchor_text) + 1]
    return token in TYPEWRITER_PERIOD_ABBREVIATIONS and bool(next_char and next_char.isspace())


def get_native_typewriter_step_delay_ms(speed: str, visible_text: str = "", full_text: str = "") -> int:
    safe_speed = get_safe_text_speed(speed)
    chars_per_second = TEXT_SPEED_PRESETS.get(safe_speed, TEXT_SPEED_PRESETS["normal"])
    if chars_per_second >= TEXT_SPEED_PRESETS["instant"]:
        return 0
    base_delay = max(1, int(round(1000 / max(1, chars_per_second))))
    return base_delay + get_typewriter_punctuation_pause_ms(visible_text, full_text)
