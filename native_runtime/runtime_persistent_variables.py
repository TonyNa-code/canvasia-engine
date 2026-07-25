from __future__ import annotations

from typing import Any


RUNTIME_VARIABLE_SCOPES = ("save", "persistent")
PERSISTENT_VARIABLE_STORE_FORMAT_VERSION = 1


def get_safe_runtime_variable_scope(value: object) -> str:
    return "persistent" if str(value or "").strip().lower() == "persistent" else "save"


def is_persistent_runtime_variable(variable: dict | None) -> bool:
    return get_safe_runtime_variable_scope((variable or {}).get("scope")) == "persistent"


def get_persistent_runtime_variables(variables: list[dict] | None) -> list[dict]:
    return [
        variable
        for variable in variables or []
        if isinstance(variable, dict) and variable.get("id") and is_persistent_runtime_variable(variable)
    ]


def _safe_number(value: object, fallback: float = 0) -> float | int:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = float(fallback)
    return int(parsed) if parsed.is_integer() else parsed


def _number_bound(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def coerce_persistent_runtime_variable_value(variable: dict, value: object) -> object:
    variable_type = str(variable.get("type") or "string").strip().lower()
    fallback = variable.get("defaultValue")

    if variable_type == "number":
        next_value = _safe_number(value, _safe_number(fallback, 0))
        min_value = _number_bound(variable.get("min", variable.get("minValue")))
        max_value = _number_bound(variable.get("max", variable.get("maxValue")))
        if min_value is not None:
            next_value = max(float(next_value), min_value)
        if max_value is not None:
            next_value = min(float(next_value), max_value)
        return int(next_value) if float(next_value).is_integer() else next_value

    if variable_type == "boolean":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "on"}:
                return True
            if normalized in {"false", "0", "no", "off", ""}:
                return False
        return fallback if isinstance(fallback, bool) else bool(value)

    if value is None:
        return fallback if isinstance(fallback, str) else ""
    return str(value)


def _persistent_value_source(value: object) -> dict:
    if not isinstance(value, dict):
        return {}
    nested_values = value.get("values")
    return nested_values if isinstance(nested_values, dict) else value


def sanitize_persistent_runtime_variable_state(
    value: object,
    variables: list[dict] | None,
) -> dict[str, object]:
    source = _persistent_value_source(value)
    result: dict[str, object] = {}
    for variable in get_persistent_runtime_variables(variables):
        variable_id = str(variable.get("id") or "")
        raw_value = source.get(variable_id, variable.get("defaultValue"))
        result[variable_id] = coerce_persistent_runtime_variable_value(variable, raw_value)
    return result


def merge_persistent_runtime_variable_state(
    variable_state: dict | None,
    variables: list[dict] | None,
    persistent_state: object,
) -> dict[str, object]:
    merged = dict(variable_state) if isinstance(variable_state, dict) else {}
    merged.update(sanitize_persistent_runtime_variable_state(persistent_state, variables))
    return merged


def collect_persistent_runtime_variable_state(
    variable_state: dict | None,
    variables: list[dict] | None,
) -> dict[str, object]:
    return sanitize_persistent_runtime_variable_state(variable_state or {}, variables)


def build_persistent_runtime_variable_store(
    variable_state: dict | None,
    variables: list[dict] | None,
    *,
    updated_at: str = "",
) -> dict[str, Any]:
    return {
        "formatVersion": PERSISTENT_VARIABLE_STORE_FORMAT_VERSION,
        "updatedAt": str(updated_at or ""),
        "values": collect_persistent_runtime_variable_state(variable_state, variables),
    }


def get_persistent_runtime_variable_summary(
    variable_state: dict | None,
    variables: list[dict] | None,
) -> dict[str, Any]:
    definitions = get_persistent_runtime_variables(variables)
    values = sanitize_persistent_runtime_variable_state(variable_state or {}, variables)
    changed_count = sum(
        1
        for variable in definitions
        if values.get(str(variable.get("id") or ""))
        != coerce_persistent_runtime_variable_value(variable, variable.get("defaultValue"))
    )
    return {
        "count": len(definitions),
        "changedCount": changed_count,
        "values": values,
    }
