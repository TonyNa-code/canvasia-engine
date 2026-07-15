from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any


CHOICE_CONTINUE_TARGET = "__continue__"
CHOICE_SAFETY_OPTION_ID = "__canvasia_choice_safety_continue__"
CHOICE_AVAILABILITY_ALWAYS = "always"
CHOICE_AVAILABILITY_HIDE = "hide_when_false"
CHOICE_AVAILABILITY_DISABLE = "disable_when_false"
CHOICE_AVAILABILITY_MODES = {
    CHOICE_AVAILABILITY_ALWAYS,
    CHOICE_AVAILABILITY_HIDE,
    CHOICE_AVAILABILITY_DISABLE,
}


def _clean_text(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def normalize_choice_availability_mode(value: Any) -> str:
    aliases = {
        "hide": CHOICE_AVAILABILITY_HIDE,
        "hidden": CHOICE_AVAILABILITY_HIDE,
        "disable": CHOICE_AVAILABILITY_DISABLE,
        "disabled": CHOICE_AVAILABILITY_DISABLE,
        "locked": CHOICE_AVAILABILITY_DISABLE,
    }
    candidate = aliases.get(_clean_text(value), _clean_text(value, CHOICE_AVAILABILITY_ALWAYS))
    return candidate if candidate in CHOICE_AVAILABILITY_MODES else CHOICE_AVAILABILITY_ALWAYS


def get_choice_availability_rules(option: dict[str, Any] | None) -> list[dict[str, Any]]:
    source = option or {}
    rules = source.get("choiceAvailabilityWhen", source.get("availabilityWhen", source.get("when", [])))
    return [rule for rule in rules if isinstance(rule, dict)] if isinstance(rules, list) else []


def inspect_choice_option_availability(
    option: dict[str, Any] | None,
    evaluate_rules: Callable[[list[dict[str, Any]]], bool] | None = None,
) -> dict[str, Any]:
    source = option or {}
    mode = normalize_choice_availability_mode(source.get("choiceAvailabilityMode", source.get("availabilityMode")))
    rules = get_choice_availability_rules(source)
    matched = True if mode == CHOICE_AVAILABILITY_ALWAYS else bool(rules and evaluate_rules and evaluate_rules(rules))
    visible = mode != CHOICE_AVAILABILITY_HIDE or matched
    enabled = visible and (mode != CHOICE_AVAILABILITY_DISABLE or matched)
    return {
        "mode": mode,
        "rules": rules,
        "matched": matched,
        "visible": visible,
        "enabled": enabled,
        "lockedReason": "" if enabled else _clean_text(
            source.get("choiceLockedReason", source.get("lockedReason")),
            "条件尚未满足",
        ),
    }


def create_choice_safety_option(text: str = "继续剧情（安全兜底）") -> dict[str, Any]:
    return {
        "id": CHOICE_SAFETY_OPTION_ID,
        "text": _clean_text(text, "继续剧情（安全兜底）"),
        "gotoSceneId": CHOICE_CONTINUE_TARGET,
        "effects": [],
        "choiceAvailabilityMode": CHOICE_AVAILABILITY_ALWAYS,
        "choiceAvailabilityMatched": True,
        "choiceVisible": True,
        "choiceEnabled": True,
        "choiceLockedReason": "",
        "isChoiceSafetyFallback": True,
    }


def resolve_runtime_choice_options(
    choice_options: Iterable[dict[str, Any]] | None,
    evaluate_rules: Callable[[list[dict[str, Any]]], bool] | None = None,
    *,
    include_safety_fallback: bool = True,
    safety_text: str = "继续剧情（安全兜底）",
) -> dict[str, Any]:
    all_options: list[dict[str, Any]] = []
    for index, raw_option in enumerate(choice_options or []):
        option = dict(raw_option) if isinstance(raw_option, dict) else {}
        availability = inspect_choice_option_availability(option, evaluate_rules)
        option.update(
            {
                "id": _clean_text(option.get("id"), f"choice_option_{index + 1}"),
                "choiceAvailabilityMode": availability["mode"],
                "choiceAvailabilityMatched": availability["matched"],
                "choiceVisible": availability["visible"],
                "choiceEnabled": availability["enabled"],
                "choiceLockedReason": availability["lockedReason"],
                "isChoiceSafetyFallback": False,
            }
        )
        all_options.append(option)

    authored_visible_options = [option for option in all_options if option["choiceVisible"]]
    selectable_options = [option for option in authored_visible_options if option["choiceEnabled"]]
    all_unavailable = not selectable_options
    safety_option = create_choice_safety_option(safety_text) if all_unavailable and include_safety_fallback else None
    runtime_options = [*authored_visible_options, safety_option] if safety_option else authored_visible_options
    return {
        "allOptions": all_options,
        "authoredVisibleOptions": authored_visible_options,
        "selectableOptions": selectable_options,
        "runtimeOptions": runtime_options,
        "safetyOption": safety_option,
        "allUnavailable": all_unavailable,
        "hiddenCount": sum(not option["choiceVisible"] for option in all_options),
        "lockedCount": sum(not option["choiceEnabled"] for option in authored_visible_options),
    }


def is_choice_option_selectable(option: dict[str, Any] | None) -> bool:
    source = option or {}
    return source.get("choiceVisible") is not False and source.get("choiceEnabled") is not False


def find_selectable_choice_index(options: list[dict[str, Any]] | None, start_index: int = 0, direction: int = 1) -> int:
    items = options or []
    if not items:
        return -1
    step = -1 if direction < 0 else 1
    for offset in range(len(items)):
        index = (start_index + offset * step) % len(items)
        if is_choice_option_selectable(items[index]):
            return index
    return -1
