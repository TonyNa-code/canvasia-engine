from __future__ import annotations

import math
from collections.abc import Callable


DEFAULT_CREDITS_DURATION_SECONDS = 18
MIN_CREDITS_DURATION_SECONDS = 4
MAX_CREDITS_DURATION_SECONDS = 180
CREDITS_BACKGROUNDS = ("dark", "light", "transparent")


def _clean_text(value: object, fallback: str = "", limit: int = 240) -> str:
    text = str(value or "").strip()
    return (text or fallback)[:limit]


def get_safe_credits_duration_seconds(value: object) -> int:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = DEFAULT_CREDITS_DURATION_SECONDS
    return round(max(MIN_CREDITS_DURATION_SECONDS, min(MAX_CREDITS_DURATION_SECONDS, number)))


def get_safe_credits_background(value: object) -> str:
    background = str(value or "").strip()
    return background if background in CREDITS_BACKGROUNDS else "dark"


def get_credits_lines(value: object) -> list[str]:
    source = value if isinstance(value, list) else str(value or "").splitlines()
    lines = [_clean_text(line, limit=160) for line in source]
    return [line for line in lines if line][:240]


def sanitize_native_credits_block(
    block: dict | None,
    *,
    localize_value: Callable[[dict, str, str], str] | None = None,
) -> dict:
    source = block if isinstance(block, dict) else {}

    def localized(key: str, fallback: str) -> str:
        if callable(localize_value):
            return _clean_text(localize_value(source, key, fallback), fallback)
        return _clean_text(source.get(key), fallback)

    return {
        "title": localized("title", "STAFF"),
        "subtitle": localized("subtitle", ""),
        "lines": get_credits_lines(source.get("lines")) or ["感谢游玩。"],
        "durationSeconds": get_safe_credits_duration_seconds(source.get("durationSeconds")),
        "background": get_safe_credits_background(source.get("background")),
        "skippable": source.get("skippable") is not False,
    }


def build_native_credits_playback(
    block: dict | None,
    *,
    started_at_ms: int,
    localize_value: Callable[[dict, str, str], str] | None = None,
) -> dict:
    credits = sanitize_native_credits_block(block, localize_value=localize_value)
    return {
        **credits,
        "startedAtMs": max(0, int(started_at_ms or 0)),
        "durationMs": credits["durationSeconds"] * 1000,
    }


def build_native_credits_line(
    block: dict | None,
    *,
    started_at_ms: int,
    block_label: str = "片尾字幕",
    localize_value: Callable[[dict, str, str], str] | None = None,
) -> dict:
    playback = build_native_credits_playback(
        block,
        started_at_ms=started_at_ms,
        localize_value=localize_value,
    )
    text = "\n".join([playback["title"], playback["subtitle"], *playback["lines"]]).strip()
    return {
        "type": "credits_roll",
        "speakerId": None,
        "speakerName": "片尾字幕",
        "text": text,
        "voiceAssetId": None,
        "creditsPlayback": playback,
        "blockLabel": block_label,
    }


def get_native_credits_status(playback: dict | None) -> str:
    return (
        "片尾字幕正在滚动；Enter / 点击可跳过"
        if (playback or {}).get("skippable") is not False
        else "片尾字幕正在滚动；播放结束后自动继续"
    )


def get_native_credits_progress(playback: dict | None, now_ms: int) -> float:
    source = playback if isinstance(playback, dict) else {}
    duration_ms = max(1, int(source.get("durationMs") or DEFAULT_CREDITS_DURATION_SECONDS * 1000))
    elapsed_ms = max(0, int(now_ms or 0) - int(source.get("startedAtMs") or 0))
    return max(0.0, min(1.0, elapsed_ms / duration_ms))


def is_native_credits_complete(playback: dict | None, now_ms: int) -> bool:
    return get_native_credits_progress(playback, now_ms) >= 1.0


def can_advance_native_credits(playback: dict | None, now_ms: int) -> bool:
    source = playback if isinstance(playback, dict) else {}
    return source.get("skippable") is not False or is_native_credits_complete(source, now_ms)


def build_native_credits_layout(
    width: int,
    height: int,
    playback: dict | None,
    now_ms: int,
    *,
    line_height: int = 38,
    static_mode: bool = False,
) -> dict:
    safe_width = max(320, int(width or 0))
    safe_height = max(240, int(height or 0))
    source = playback if isinstance(playback, dict) else {}
    lines = get_credits_lines(source.get("lines")) or ["感谢游玩。"]
    progress = get_native_credits_progress(source, now_ms)

    if static_mode:
        page_size = max(3, min(10, (safe_height - 300) // max(24, int(line_height))))
        page_count = max(1, math.ceil(len(lines) / page_size))
        page_index = min(page_count - 1, int(progress * page_count))
        visible_lines = lines[page_index * page_size : (page_index + 1) * page_size]
        return {
            "mode": "pages",
            "progress": progress,
            "pageIndex": page_index,
            "pageCount": page_count,
            "visibleLines": visible_lines,
            "contentTop": max(170, int(safe_height * 0.36)),
            "lineHeight": max(24, int(line_height)),
            "maxTextWidth": max(240, min(920, safe_width - 120)),
        }

    title_height = 136
    content_height = title_height + len(lines) * max(24, int(line_height)) + 120
    start_y = safe_height + 56
    end_y = -content_height - 56
    return {
        "mode": "scroll",
        "progress": progress,
        "pageIndex": 0,
        "pageCount": 1,
        "visibleLines": lines,
        "contentTop": round(start_y + (end_y - start_y) * progress),
        "lineHeight": max(24, int(line_height)),
        "maxTextWidth": max(240, min(920, safe_width - 120)),
    }


def _ellipsize(font, text: str, max_width: int) -> str:
    value = str(text or "")
    if font.size(value)[0] <= max_width:
        return value
    suffix = "…"
    while value and font.size(value + suffix)[0] > max_width:
        value = value[:-1]
    return value + suffix


def _blit_center(screen, font, text: str, center_x: int, y: int, color: tuple[int, int, int], max_width: int) -> None:
    surface = font.render(_ellipsize(font, text, max_width), True, color)
    screen.blit(surface, (center_x - surface.get_width() // 2, y))


def render_native_credits(
    *,
    pygame_module,
    screen,
    width: int,
    height: int,
    playback: dict,
    now_ms: int,
    palette: dict,
    font_title,
    font_body,
    font_ui,
    static_mode: bool = False,
) -> dict:
    background = get_safe_credits_background(playback.get("background"))
    if background == "dark":
        screen.fill((7, 11, 22))
        text_color, muted_color, accent_color = (245, 247, 255), (169, 181, 205), palette["accent"]
    elif background == "light":
        screen.fill((241, 239, 232))
        text_color, muted_color, accent_color = (29, 37, 54), (92, 103, 121), (52, 105, 194)
    else:
        veil = pygame_module.Surface((width, height), pygame_module.SRCALPHA)
        veil.fill((5, 9, 20, 172))
        screen.blit(veil, (0, 0))
        text_color, muted_color, accent_color = palette["text"], palette["muted"], palette["accent"]

    atmosphere = pygame_module.Surface((width, height), pygame_module.SRCALPHA)
    pygame_module.draw.circle(atmosphere, (*accent_color, 34), (int(width * 0.76), int(height * 0.18)), max(90, width // 7))
    pygame_module.draw.circle(atmosphere, (*accent_color, 18), (int(width * 0.18), int(height * 0.78)), max(120, width // 5))
    screen.blit(atmosphere, (0, 0))
    pygame_module.draw.line(screen, accent_color, (max(28, width // 14), 44), (min(width - 28, width * 5 // 14), 44), 2)

    layout = build_native_credits_layout(
        width,
        height,
        playback,
        now_ms,
        line_height=font_body.get_height() + 12,
        static_mode=static_mode,
    )
    center_x = width // 2
    max_text_width = int(layout["maxTextWidth"])
    title = _clean_text(playback.get("title"), "STAFF", 80)
    subtitle = _clean_text(playback.get("subtitle"), "", 120)

    if layout["mode"] == "pages":
        _blit_center(screen, font_ui, "CREDITS", center_x, max(78, int(height * 0.13)), accent_color, max_text_width)
        _blit_center(screen, font_title, title, center_x, max(112, int(height * 0.19)), text_color, max_text_width)
        if subtitle:
            _blit_center(screen, font_ui, subtitle, center_x, max(158, int(height * 0.26)), muted_color, max_text_width)
        y = int(layout["contentTop"])
        for line in layout["visibleLines"]:
            _blit_center(screen, font_body, line, center_x, y, text_color, max_text_width)
            y += int(layout["lineHeight"])
        page_label = f"{int(layout['pageIndex']) + 1} / {int(layout['pageCount'])}"
        _blit_center(screen, font_ui, page_label, center_x, height - 72, muted_color, max_text_width)
    else:
        y = int(layout["contentTop"])
        _blit_center(screen, font_ui, "CANVASIA PRESENTS", center_x, y, accent_color, max_text_width)
        y += font_ui.get_height() + 22
        _blit_center(screen, font_title, title, center_x, y, text_color, max_text_width)
        y += font_title.get_height() + 16
        if subtitle:
            _blit_center(screen, font_ui, subtitle, center_x, y, muted_color, max_text_width)
            y += font_ui.get_height() + 38
        else:
            y += 22
        for line in layout["visibleLines"]:
            if -font_body.get_height() <= y <= height + font_body.get_height():
                _blit_center(screen, font_body, line, center_x, y, text_color, max_text_width)
            y += int(layout["lineHeight"])

    hint = "Enter / 点击跳过" if playback.get("skippable") is not False else "片尾播放结束后自动继续"
    hint_surface = font_ui.render(hint, True, muted_color)
    screen.blit(hint_surface, (width - hint_surface.get_width() - 28, height - hint_surface.get_height() - 22))
    return layout


def render_native_credits_for_player(player) -> dict:
    """Bridge the player controller to the standalone credits renderer."""
    return render_native_credits(
        pygame_module=player.pygame,
        screen=player.screen,
        width=player.width,
        height=player.height,
        playback=player.current_line.get("creditsPlayback") or {},
        now_ms=player.pygame.time.get_ticks(),
        palette=player.get_active_palette(),
        font_title=player.font_title,
        font_body=player.font_body,
        font_ui=player.font_ui,
        static_mode=player.runtime_settings.get("visualComfort") == "static",
    )
