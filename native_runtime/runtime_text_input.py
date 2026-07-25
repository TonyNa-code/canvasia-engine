from __future__ import annotations

import math
import re
from typing import Any, Callable


TEXT_INPUT_VARIABLE_TYPES = {"string", "number"}
TEXT_INPUT_MIN_LENGTH = 1
TEXT_INPUT_MAX_LENGTH = 200
TEXT_INPUT_DEFAULT_LENGTH = 32
TEXT_VARIABLE_TOKEN_PATTERN = re.compile(r"\{\{\s*([0-9A-Za-z_\-\u3400-\u9fff]{1,64})\s*\}\}")


def clamp_text_input_length(value: object, fallback: int = TEXT_INPUT_DEFAULT_LENGTH) -> int:
    try:
        parsed = int(round(float(value)))
    except (TypeError, ValueError):
        parsed = fallback
    return min(TEXT_INPUT_MAX_LENGTH, max(TEXT_INPUT_MIN_LENGTH, parsed))


def normalize_text_input_block(block: dict | None) -> dict:
    source = block if isinstance(block, dict) else {}
    prompt = str(source.get("prompt") or "").strip()
    return {
        "variableId": str(source.get("variableId") or "").strip(),
        "prompt": prompt or "请输入内容",
        "placeholder": str(source.get("placeholder") or "").strip(),
        "defaultValue": "" if source.get("defaultValue") is None else str(source.get("defaultValue")),
        "maxLength": clamp_text_input_length(source.get("maxLength")),
        "allowEmpty": source.get("allowEmpty") is True,
    }


def collect_runtime_text_variable_ids(*values: object) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for value in values:
        nested_values = value if isinstance(value, (list, tuple)) else [value]
        for nested_value in nested_values:
            for match in TEXT_VARIABLE_TOKEN_PATTERN.finditer(str(nested_value or "")):
                variable_id = match.group(1)
                if variable_id not in seen:
                    seen.add(variable_id)
                    found.append(variable_id)
    return found


def format_runtime_variable_value(value: object, true_label: str = "是", false_label: str = "否") -> str:
    if isinstance(value, bool):
        return true_label if value else false_label
    return "" if value is None else str(value)


def interpolate_runtime_text(
    text: object,
    variable_values: dict | None = None,
    variables_by_id: dict | None = None,
    *,
    keep_unknown: bool = True,
) -> str:
    values = variable_values if isinstance(variable_values, dict) else {}
    definitions = variables_by_id if isinstance(variables_by_id, dict) else {}

    def replace(match: re.Match[str]) -> str:
        variable_id = match.group(1)
        variable = definitions.get(variable_id)
        if variable_id not in values and not isinstance(variable, dict):
            return match.group(0) if keep_unknown else ""
        fallback = variable.get("defaultValue") if isinstance(variable, dict) else ""
        value = values.get(variable_id, fallback)
        return format_runtime_variable_value(value)

    return TEXT_VARIABLE_TOKEN_PATTERN.sub(replace, str(text or ""))


def sanitize_text_input_value(
    raw_value: object,
    block: dict | None,
    variable: dict | None,
    *,
    normalize_value: Callable[[object], object] | None = None,
    trim: bool = True,
) -> dict:
    config = normalize_text_input_block(block)
    variable_definition = variable if isinstance(variable, dict) else {}
    variable_type = str(variable_definition.get("type") or "string").strip().lower()
    if variable_type not in TEXT_INPUT_VARIABLE_TYPES:
        return {"ok": False, "error": "玩家输入只支持文本或数字变量。", "value": None, "text": ""}

    text = str(raw_value or "")
    if trim:
        text = text.strip()
    if not text and config["defaultValue"]:
        text = config["defaultValue"].strip() if trim else config["defaultValue"]
    if not text and not config["allowEmpty"]:
        return {
            "ok": False,
            "error": "请先填写内容，或在卡片中允许留空。",
            "value": None,
            "text": text,
        }
    if len(text) > config["maxLength"]:
        return {
            "ok": False,
            "error": f"最多可以输入 {config['maxLength']} 个字符。",
            "value": None,
            "text": text,
        }

    value: object = text
    if variable_type == "number":
        try:
            numeric_value = float(text)
        except (TypeError, ValueError):
            numeric_value = math.nan
        if not math.isfinite(numeric_value):
            return {"ok": False, "error": "这里需要填写一个有效数字。", "value": None, "text": text}
        value = int(numeric_value) if int(numeric_value) == numeric_value else numeric_value
    if normalize_value is not None:
        value = normalize_value(value)
    return {"ok": True, "error": "", "value": value, "text": text}


def append_text_input_value(current_value: object, addition: object, max_length: object) -> str:
    limit = clamp_text_input_length(max_length)
    current = str(current_value or "")
    return (current + str(addition or ""))[:limit]


def render_runtime_text_input_overlay(player: Any) -> None:
    state = player.text_input_state if isinstance(player.text_input_state, dict) else {}
    palette = player.get_active_palette()
    panel = player.pygame.Rect(0, 0, min(player.width - 96, 760), min(player.height - 96, 430))
    panel.center = (player.width // 2, player.height // 2)
    player.pygame.draw.rect(player.screen, (*palette["panel"], 248), panel, border_radius=28)
    player.pygame.draw.rect(player.screen, (*palette["panelBorder"], 110), panel, 2, border_radius=28)
    player.draw_game_ui_panel_frame(panel, "system")

    player.screen.blit(player.font_title.render("玩家输入", True, palette["text"]), (panel.left + 30, panel.top + 26))
    prompt_rect = player.pygame.Rect(panel.left + 30, panel.top + 78, panel.width - 60, 74)
    player.blit_wrapped_text(player.font_body, str(state.get("prompt") or "请输入内容"), prompt_rect, palette["text"], line_gap=5, max_lines=2)

    input_rect = player.pygame.Rect(panel.left + 30, panel.top + 168, panel.width - 60, 62)
    player.pygame.draw.rect(player.screen, (*palette["accent"], 26), input_rect, border_radius=18)
    player.pygame.draw.rect(player.screen, (*palette["accentAlt"], 126), input_rect, 2, border_radius=18)
    value = str(state.get("value") or "")
    display_value = value or str(state.get("placeholder") or "在这里输入...")
    display_color = palette["text"] if value else palette["muted"]
    player.screen.blit(player.font_body.render(display_value[:64], True, display_color), (input_rect.left + 18, input_rect.top + 14))

    error_text = str(state.get("error") or "")
    meta = error_text or f"保存到：{state.get('variableName') or state.get('variableId') or '变量'} · 最多 {state.get('maxLength') or TEXT_INPUT_DEFAULT_LENGTH} 字"
    meta_color = palette.get("warning", palette["accentAlt"]) if error_text else palette["muted"]
    player.screen.blit(player.font_ui.render(meta[:72], True, meta_color), (panel.left + 32, panel.top + 244))

    submit_rect = player.pygame.Rect(panel.right - 210, panel.bottom - 78, 178, 44)
    player.pygame.draw.rect(player.screen, (*palette["accent"], 210), submit_rect, border_radius=22)
    player.draw_game_ui_button_frame(submit_rect, player.get_game_ui_button_state(submit_rect, active=True))
    submit_label = player.font_ui.render("确认并继续", True, palette["text"])
    player.screen.blit(submit_label, submit_label.get_rect(center=submit_rect.center))
    player.overlay_hotspots.append({"kind": "text-input-submit", "rect": submit_rect})

    hint = "输入后按 Enter 确认 · Backspace 删除 · 该答案会写入项目变量并进入存档"
    player.screen.blit(player.font_ui.render(hint, True, palette["muted"]), (panel.left + 30, panel.bottom - 62))


def handle_runtime_text_input_event(player: Any, event: Any) -> bool:
    pygame = player.pygame
    state = player.text_input_state if isinstance(player.text_input_state, dict) else {}
    if event.type == pygame.KEYDOWN:
        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            player.submit_text_input()
            return True
        if event.key == pygame.K_BACKSPACE:
            state["value"] = str(state.get("value") or "")[:-1]
            state["error"] = ""
            return True
        if event.key == pygame.K_ESCAPE:
            state["error"] = "请确认答案后继续剧情。"
            return True
        text_input_event = getattr(pygame, "TEXTINPUT", None)
        unicode_value = str(getattr(event, "unicode", "") or "")
        if text_input_event is None and unicode_value and unicode_value.isprintable():
            state["value"] = append_text_input_value(state.get("value"), unicode_value, state.get("maxLength"))
            state["error"] = ""
            return True
    text_input_event = getattr(pygame, "TEXTINPUT", None)
    if text_input_event is not None and event.type == text_input_event:
        state["value"] = append_text_input_value(state.get("value"), getattr(event, "text", ""), state.get("maxLength"))
        state["error"] = ""
        return True
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        for target in player.overlay_hotspots:
            if target.get("kind") == "text-input-submit" and target["rect"].collidepoint(event.pos):
                player.submit_text_input()
                return True
    return True
