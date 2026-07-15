from __future__ import annotations

import unittest

from native_runtime.runtime_choice_availability import (
    CHOICE_SAFETY_OPTION_ID,
    find_selectable_choice_index,
    resolve_runtime_choice_options,
)


class NativeRuntimeChoiceAvailabilityTests(unittest.TestCase):
    def test_resolves_gated_options_and_prevents_dead_end(self) -> None:
        variables = {"affection": 2, "has_key": False}

        def evaluate_rules(rules: list[dict]) -> bool:
            return all(variables.get(rule["variableId"]) == rule["value"] for rule in rules)

        result = resolve_runtime_choice_options(
            [
                {"id": "hidden", "choiceAvailabilityMode": "hide_when_false", "choiceAvailabilityWhen": [{"variableId": "affection", "value": 5}]},
                {"id": "locked", "choiceAvailabilityMode": "disable_when_false", "choiceLockedReason": "需要钥匙", "choiceAvailabilityWhen": [{"variableId": "has_key", "value": True}]},
            ],
            evaluate_rules,
        )
        self.assertTrue(result["allUnavailable"])
        self.assertEqual([option["id"] for option in result["runtimeOptions"]], ["locked", CHOICE_SAFETY_OPTION_ID])
        self.assertFalse(result["runtimeOptions"][0]["choiceEnabled"])
        self.assertEqual(result["runtimeOptions"][0]["choiceLockedReason"], "需要钥匙")
        self.assertEqual(find_selectable_choice_index(result["runtimeOptions"], 0), 1)


if __name__ == "__main__":
    unittest.main()
