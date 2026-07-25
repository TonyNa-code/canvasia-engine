from __future__ import annotations

import unittest

from project_variable_migration import replace_variable_reference_in_block


class ProjectVariableMigrationTests(unittest.TestCase):
    def test_story_references_and_localized_tokens_are_migrated_together(self) -> None:
        input_block = {
            "type": "text_input",
            "variableId": "player_name",
            "prompt": "Name for {{ player_name }}",
            "promptTranslations": {"zh-CN": "{{player_name}} 的名字"},
        }
        choice_block = {
            "type": "choice",
            "options": [
                {
                    "text": "Ask {{player_name}}",
                    "textTranslations": {"ja-JP": "{{ player_name }} に聞く"},
                    "choiceLockedReason": "{{player_name}} is not ready",
                    "effects": [{"type": "variable_set", "variableId": "player_name", "value": "A"}],
                }
            ],
        }

        input_changes = replace_variable_reference_in_block(input_block, "player_name", "hero_name")
        choice_changes = replace_variable_reference_in_block(choice_block, "player_name", "hero_name")

        self.assertEqual(input_changes, 3)
        self.assertEqual(input_block["variableId"], "hero_name")
        self.assertEqual(input_block["prompt"], "Name for {{hero_name}}")
        self.assertEqual(input_block["promptTranslations"]["zh-CN"], "{{hero_name}} 的名字")
        self.assertEqual(choice_changes, 4)
        self.assertEqual(choice_block["options"][0]["text"], "Ask {{hero_name}}")
        self.assertEqual(choice_block["options"][0]["textTranslations"]["ja-JP"], "{{hero_name}} に聞く")
        self.assertEqual(choice_block["options"][0]["choiceLockedReason"], "{{hero_name}} is not ready")
        self.assertEqual(choice_block["options"][0]["effects"][0]["variableId"], "hero_name")


if __name__ == "__main__":
    unittest.main()
