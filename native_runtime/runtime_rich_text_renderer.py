from __future__ import annotations

from typing import Any


def _safe_color(value: Any, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    text = str(value or "").strip().lower()
    if len(text) == 7 and text.startswith("#"):
        try:
            return tuple(int(text[index : index + 2], 16) for index in (1, 3, 5))
        except ValueError:
            pass
    return tuple(int(channel) for channel in fallback[:3])


def _muted_color(color: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(max(0, min(255, int(round(channel * 0.78)))) for channel in color)


def _get_segment_style(segment: dict[str, Any] | None, base_color: tuple[int, int, int]) -> dict[str, Any]:
    segment = segment or {}
    kind = str(segment.get("type") or "plain")
    return {
        "kind": kind,
        "color": (
            _safe_color(segment.get("color"), base_color)
            if kind == "color"
            else _muted_color(base_color)
            if kind == "whisper"
            else base_color
        ),
        "annotation": str(segment.get("annotation") or ""),
    }


def _get_font(style: dict[str, Any], normal_font: object, bold_font: object) -> object:
    return bold_font if style.get("kind") == "emphasis" else normal_font


def _build_units(
    plan: dict[str, Any],
    visible_end: int,
    normal_font: object,
    bold_font: object,
    ruby_font: object,
    base_color: tuple[int, int, int],
) -> list[dict[str, Any]]:
    text = str(plan.get("plainText") or "")
    safe_end = max(0, min(len(text), int(visible_end)))
    segments = list(plan.get("segments") or [])
    units: list[dict[str, Any]] = []
    cursor = 0
    segment_index = 0

    while cursor < safe_end:
        while segment_index < len(segments) and int(segments[segment_index].get("end") or 0) <= cursor:
            segment_index += 1
        segment = segments[segment_index] if segment_index < len(segments) else None
        segment_start = int((segment or {}).get("start") or -1)
        segment_end = int((segment or {}).get("end") or -1)

        if segment and segment_start == cursor and segment_end > cursor:
            style = _get_segment_style(segment, base_color)
            if style["kind"] == "ruby" and safe_end >= segment_end:
                base_text = text[segment_start:segment_end]
                units.append({
                    **style,
                    "text": base_text,
                    "start": segment_start,
                    "end": segment_end,
                    "width": max(normal_font.size(base_text)[0], ruby_font.size(style["annotation"])[0]),
                    "isRuby": True,
                })
                cursor = segment_end
                continue
            for index in range(segment_start, min(segment_end, safe_end)):
                char = text[index]
                font = _get_font(style, normal_font, bold_font)
                units.append({
                    **style,
                    "text": char,
                    "start": index,
                    "end": index + 1,
                    "width": 0 if char == "\n" else font.size(char)[0],
                    "isRuby": False,
                })
            cursor = min(segment_end, safe_end)
            continue

        next_boundary = min(
            safe_end,
            segment_start if segment and segment_start > cursor else safe_end,
        )
        style = _get_segment_style(None, base_color)
        for index in range(cursor, next_boundary):
            char = text[index]
            units.append({
                **style,
                "text": char,
                "start": index,
                "end": index + 1,
                "width": 0 if char == "\n" else normal_font.size(char)[0],
                "isRuby": False,
            })
        cursor = next_boundary

    return units


def layout_runtime_rich_text(
    plan: dict[str, Any],
    normal_font: object,
    bold_font: object,
    ruby_font: object,
    max_width: int,
    base_color: tuple[int, int, int],
    *,
    visible_end: int | None = None,
    line_gap: int = 8,
) -> dict[str, Any]:
    text = str((plan or {}).get("plainText") or "")
    safe_visible_end = len(text) if visible_end is None else max(0, min(len(text), int(visible_end)))
    safe_width = max(1, int(max_width or 1))
    units = _build_units(plan or {}, safe_visible_end, normal_font, bold_font, ruby_font, base_color)
    lines: list[dict[str, Any]] = []
    current_units: list[dict[str, Any]] = []
    current_width = 0

    def commit_line() -> None:
        nonlocal current_units, current_width
        has_ruby = any(unit.get("isRuby") for unit in current_units)
        height = normal_font.get_height() + line_gap
        if has_ruby:
            height += ruby_font.get_height() + 3
        lines.append({
            "units": current_units,
            "width": current_width,
            "height": height,
            "hasRuby": has_ruby,
        })
        current_units = []
        current_width = 0

    for unit in units:
        if unit["text"] == "\n":
            commit_line()
            continue
        width = int(unit.get("width") or 0)
        if current_units and current_width + width > safe_width:
            commit_line()
        if not current_units and unit["text"].isspace():
            continue
        current_units.append(unit)
        current_width += width

    if current_units or not lines:
        commit_line()
    return {
        "plainText": text[:safe_visible_end],
        "visibleEnd": safe_visible_end,
        "maxWidth": safe_width,
        "lines": lines,
        "lineCount": len(lines),
        "totalHeight": sum(int(line["height"]) for line in lines),
        "hasRuby": any(line["hasRuby"] for line in lines),
    }


def limit_runtime_rich_text_layout(
    layout: dict[str, Any],
    max_lines: int,
    normal_font: object,
    *,
    append_ellipsis: bool = False,
) -> dict[str, Any]:
    safe_max_lines = max(1, int(max_lines or 1))
    source_lines = list((layout or {}).get("lines") or [])
    visible_lines = [
        {**line, "units": [dict(unit) for unit in line.get("units") or []]}
        for line in source_lines[:safe_max_lines]
    ]
    truncated = len(source_lines) > safe_max_lines
    if truncated and append_ellipsis and visible_lines:
        line = visible_lines[-1]
        ellipsis_width = normal_font.size(" …")[0]
        max_width = int((layout or {}).get("maxWidth") or 1)
        while line["units"] and int(line.get("width") or 0) + ellipsis_width > max_width:
            removed = line["units"].pop()
            line["width"] = max(0, int(line.get("width") or 0) - int(removed.get("width") or 0))
        ellipsis_color = tuple((line["units"][-1] if line["units"] else {}).get("color") or (238, 245, 255))
        line["units"].append({
            "kind": "plain",
            "color": ellipsis_color,
            "annotation": "",
            "text": " …",
            "start": -1,
            "end": -1,
            "width": ellipsis_width,
            "isRuby": False,
        })
        line["width"] = int(line.get("width") or 0) + ellipsis_width
    return {
        **(layout or {}),
        "lines": visible_lines,
        "lineCount": len(visible_lines),
        "totalHeight": sum(int(line["height"]) for line in visible_lines),
        "truncated": truncated,
    }


def _render_text_surface(font: object, text: str, color: tuple[int, int, int], shadow_alpha: int = 0) -> tuple[object, object | None]:
    surface = font.render(text, True, color)
    shadow = None
    if shadow_alpha > 0:
        shadow = font.render(text, True, (0, 0, 0))
        shadow.set_alpha(shadow_alpha)
    return surface, shadow


def draw_runtime_rich_text(
    pygame: object,
    screen: object,
    layout: dict[str, Any],
    normal_font: object,
    bold_font: object,
    ruby_font: object,
    position: tuple[int, int],
    *,
    center: bool = False,
    shadow_strength: int = 0,
) -> None:
    start_x, current_y = int(position[0]), int(position[1])
    shadow_alpha = max(0, min(150, int(shadow_strength or 0) * 3))
    for line in (layout or {}).get("lines") or []:
        current_x = start_x - int(line.get("width") or 0) // 2 if center else start_x
        line_height = int(line.get("height") or normal_font.get_height())
        ruby_offset = ruby_font.get_height() + 3 if line.get("hasRuby") else 0
        base_y = current_y + ruby_offset
        for unit in line.get("units") or []:
            style = unit or {}
            text = str(style.get("text") or "")
            width = int(style.get("width") or 0)
            color = tuple(style.get("color") or (238, 245, 255))
            if style.get("isRuby"):
                base_surface, base_shadow = _render_text_surface(normal_font, text, color, shadow_alpha)
                annotation = str(style.get("annotation") or "")
                ruby_surface, ruby_shadow = _render_text_surface(ruby_font, annotation, color, shadow_alpha)
                base_x = current_x + max(0, (width - base_surface.get_width()) // 2)
                ruby_x = current_x + max(0, (width - ruby_surface.get_width()) // 2)
                if base_shadow:
                    screen.blit(base_shadow, (base_x + 2, base_y + 2))
                if ruby_shadow:
                    screen.blit(ruby_shadow, (ruby_x + 1, current_y + 1))
                screen.blit(ruby_surface, (ruby_x, current_y))
                screen.blit(base_surface, (base_x, base_y))
            else:
                font = bold_font if style.get("kind") == "emphasis" else normal_font
                surface, shadow = _render_text_surface(font, text, color, shadow_alpha)
                y = base_y + max(0, normal_font.get_height() - surface.get_height())
                if shadow:
                    screen.blit(shadow, (current_x + 2, y + 2))
                screen.blit(surface, (current_x, y))
            current_x += width
        current_y += line_height
