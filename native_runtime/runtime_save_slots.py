from __future__ import annotations


def is_formal_save_slot_protected(snapshot: object) -> bool:
    return isinstance(snapshot, dict) and snapshot.get("protected") is True


def can_mutate_formal_save_slot(snapshot: object) -> bool:
    return not is_formal_save_slot_protected(snapshot)


def normalize_formal_save_slots(values: object, slot_count: int) -> list[dict | None]:
    safe_count = max(0, int(slot_count or 0))
    source = values if isinstance(values, list) else []
    result: list[dict | None] = []
    for index in range(safe_count):
        snapshot = source[index] if index < len(source) else None
        if not isinstance(snapshot, dict):
            result.append(None)
            continue
        normalized = dict(snapshot)
        normalized["protected"] = is_formal_save_slot_protected(snapshot)
        result.append(normalized)
    return result


def with_formal_save_slot_protection(snapshot: object, protected: bool) -> dict | None:
    if not isinstance(snapshot, dict):
        return None
    updated = dict(snapshot)
    updated["protected"] = bool(protected)
    return updated


def toggle_formal_save_slot_protection(snapshot: object) -> dict | None:
    return with_formal_save_slot_protection(snapshot, not is_formal_save_slot_protected(snapshot))


__all__ = [
    "can_mutate_formal_save_slot",
    "is_formal_save_slot_protected",
    "normalize_formal_save_slots",
    "toggle_formal_save_slot_protection",
    "with_formal_save_slot_protection",
]
