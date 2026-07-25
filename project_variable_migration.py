from __future__ import annotations

import re


def replace_variable_reference_in_block(block: dict, old_variable_id: str, new_variable_id: str) -> int:
    """Rename one variable across a story block and return the number of changed references."""
    changed = 0
    block_type = block.get("type")

    if block_type in {"variable_set", "variable_add", "text_input"} and block.get("variableId") == old_variable_id:
        block["variableId"] = new_variable_id
        changed += 1

    token_pattern = re.compile(r"\{\{\s*" + re.escape(old_variable_id) + r"\s*\}\}")

    def replace_text_field(source: dict, key: str) -> int:
        field_changes = 0
        value = source.get(key)
        if isinstance(value, str):
            next_value, count = token_pattern.subn("{{" + new_variable_id + "}}", value)
            if count:
                source[key] = next_value
                field_changes += count
        translations = source.get(f"{key}Translations")
        if isinstance(translations, dict):
            for language, translated_value in list(translations.items()):
                if not isinstance(translated_value, str):
                    continue
                next_value, count = token_pattern.subn("{{" + new_variable_id + "}}", translated_value)
                if count:
                    translations[language] = next_value
                    field_changes += count
        return field_changes

    changed += replace_text_field(block, "text")
    changed += replace_text_field(block, "prompt")

    if block_type == "choice":
        for option in block.get("options") or []:
            if not isinstance(option, dict):
                continue
            changed += replace_text_field(option, "text")
            changed += replace_text_field(option, "choiceLockedReason")
            for effect in option.get("effects") or []:
                if isinstance(effect, dict) and effect.get("variableId") == old_variable_id:
                    effect["variableId"] = new_variable_id
                    changed += 1

    if block_type == "condition":
        for branch in block.get("branches") or []:
            if not isinstance(branch, dict):
                continue
            for rule in branch.get("when") or []:
                if isinstance(rule, dict) and rule.get("variableId") == old_variable_id:
                    rule["variableId"] = new_variable_id
                    changed += 1

    return changed
