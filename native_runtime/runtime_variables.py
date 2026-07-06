from __future__ import annotations

import math


VARIABLE_TYPES = {"number", "boolean", "string"}
NUMERIC_CONDITION_OPERATORS = {">", ">=", "<", "<="}
EQUALITY_CONDITION_OPERATORS = {"==", "=", "!="}
STRING_CONDITION_OPERATORS = {"contains", "not_contains", "starts_with", "ends_with"}


def normalize_variable_type(value: object) -> str:
    variable_type = str(value or "string").strip().lower() or "string"
    return variable_type if variable_type in VARIABLE_TYPES else "string"


def is_number_variable_value(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def variable_value_matches_type(variable_type: str, value: object) -> bool:
    safe_type = normalize_variable_type(variable_type)
    if safe_type == "number":
        return is_number_variable_value(value)
    if safe_type == "boolean":
        return isinstance(value, bool)
    return isinstance(value, str)


def parse_variable_number_bound(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def get_variable_number_bounds(variable: dict | None) -> tuple[float | None, float | None]:
    if not isinstance(variable, dict):
        return None, None
    min_value = parse_variable_number_bound(variable.get("min", variable.get("minValue")))
    max_value = parse_variable_number_bound(variable.get("max", variable.get("maxValue")))
    return min_value, max_value


def clamp_runtime_variable_number(variable: dict | None, value: float) -> float | int:
    min_value, max_value = get_variable_number_bounds(variable)
    next_value = value
    if min_value is not None:
        next_value = max(next_value, min_value)
    if max_value is not None:
        next_value = min(next_value, max_value)
    return int(next_value) if int(next_value) == next_value else next_value


def coerce_runtime_variable_value(variable: dict | None, value: object) -> object:
    variable_type = normalize_variable_type((variable or {}).get("type"))
    fallback = (variable or {}).get("defaultValue")
    if variable_type == "number":
        if isinstance(value, bool):
            fallback_value = fallback if is_number_variable_value(fallback) else 0
            return clamp_runtime_variable_number(variable, float(fallback_value))
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            fallback_value = fallback if is_number_variable_value(fallback) else 0
            return clamp_runtime_variable_number(variable, float(fallback_value))
        if not math.isfinite(numeric_value):
            fallback_value = fallback if is_number_variable_value(fallback) else 0
            return clamp_runtime_variable_number(variable, float(fallback_value))
        return clamp_runtime_variable_number(variable, numeric_value)
    if variable_type == "boolean":
        if isinstance(value, bool):
            return value
        clean_value = str(value).strip().lower()
        if clean_value in {"true", "1", "yes", "on"}:
            return True
        if clean_value in {"false", "0", "no", "off"}:
            return False
        return fallback if isinstance(fallback, bool) else False
    if value is None:
        return fallback if isinstance(fallback, str) else ""
    return value if isinstance(value, str) else str(value)


def condition_operator_matches_variable_type(variable_type: str, operator: object) -> bool:
    safe_operator = str(operator or "==").strip() or "=="
    if safe_operator in EQUALITY_CONDITION_OPERATORS:
        return True
    if safe_operator in NUMERIC_CONDITION_OPERATORS:
        return normalize_variable_type(variable_type) == "number"
    if safe_operator in STRING_CONDITION_OPERATORS:
        return normalize_variable_type(variable_type) == "string"
    return False


def evaluate_runtime_operator(current_value: object, operator: str, target_value: object) -> bool:
    safe_operator = str(operator or "==").strip() or "=="
    if safe_operator in {"==", "="}:
        return current_value == target_value
    if safe_operator == "!=":
        return current_value != target_value
    if safe_operator == "contains":
        return str(target_value) in str(current_value)
    if safe_operator == "not_contains":
        return str(target_value) not in str(current_value)
    if safe_operator == "starts_with":
        return str(current_value).startswith(str(target_value))
    if safe_operator == "ends_with":
        return str(current_value).endswith(str(target_value))
    try:
        left = float(current_value)
        right = float(target_value)
    except (TypeError, ValueError):
        left = str(current_value)
        right = str(target_value)
    if safe_operator == ">":
        return left > right
    if safe_operator == ">=":
        return left >= right
    if safe_operator == "<":
        return left < right
    if safe_operator == "<=":
        return left <= right
    return False
