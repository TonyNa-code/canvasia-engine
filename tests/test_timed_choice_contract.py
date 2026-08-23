from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path

from native_runtime.runtime_timed_choices import (
    resolve_timed_choice_target,
    sanitize_timed_choice_config,
    sanitize_timed_choice_state,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
WEB_MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_timed_choices.js"


class TimedChoiceContractTests(unittest.TestCase):
    def test_web_and_native_config_state_and_target_stay_aligned(self) -> None:
        scenarios = [
            {
                "config": {"timeoutSeconds": 10, "timeoutOptionId": "locked"},
                "options": [
                    {"id": "hidden", "choiceVisible": False},
                    {"id": "locked", "choiceEnabled": False},
                    {"id": "safe", "choiceEnabled": True},
                ],
                "state": {"choiceKey": "s:1", "targetOptionId": "safe", "remainingMs": 4200},
            },
            {
                "config": {"choiceTimeoutSeconds": 999, "choiceTimeoutOptionId": "route_b"},
                "options": [
                    {"id": "route_a", "choiceEnabled": True},
                    {"id": "route_b", "choiceEnabled": True},
                ],
                "state": {"choiceKey": "s:2", "targetOptionId": "route_b", "remainingMs": -8},
            },
            {
                "config": {"timeoutSeconds": 0},
                "options": [{"id": "route_a", "choiceEnabled": True}],
                "state": {"choiceKey": "s:3", "remainingMs": 1000},
            },
        ]
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(WEB_MODULE_PATH.as_uri())};
            const scenarios = {json.dumps(scenarios)};
            process.stdout.write(JSON.stringify(scenarios.map((item) => ({{
              config: tools.sanitizeTimedChoiceConfig(item.config),
              target: tools.resolveTimedChoiceTarget(item.options, item.config.timeoutOptionId ?? item.config.choiceTimeoutOptionId),
              state: tools.sanitizeTimedChoiceState(item.state, item.config),
            }}))));
            """
        )
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        web_results = json.loads(completed.stdout)
        native_results = [
            {
                "config": sanitize_timed_choice_config(item["config"]),
                "target": resolve_timed_choice_target(
                    item["options"],
                    item["config"].get("timeoutOptionId", item["config"].get("choiceTimeoutOptionId", "")),
                ),
                "state": sanitize_timed_choice_state(item["state"], item["config"]),
            }
            for item in scenarios
        ]
        self.assertEqual(web_results, native_results)

    def test_editor_export_and_all_runtimes_are_wired(self) -> None:
        run_editor_source = (ROOT_DIR / "run_editor.py").read_text(encoding="utf-8")
        runtime_registry_source = (ROOT_DIR / "export_runtime_module_registry.py").read_text(encoding="utf-8")
        editor_index = (ROOT_DIR / "prototype_editor" / "index.html").read_text(encoding="utf-8")
        editor_source = (ROOT_DIR / "prototype_editor" / "app.js").read_text(encoding="utf-8")
        editor_guard = (ROOT_DIR / "prototype_editor" / "modules" / "module_guard.js").read_text(encoding="utf-8")
        story_editors_source = (ROOT_DIR / "prototype_editor" / "modules" / "story_block_editors.js").read_text(encoding="utf-8")
        player_source = (ROOT_DIR / "export_player_template" / "player.js").read_text(encoding="utf-8")
        native_source = (ROOT_DIR / "native_runtime" / "runtime_player.py").read_text(encoding="utf-8")
        renpy_source = (ROOT_DIR / "renpy_export.py").read_text(encoding="utf-8")

        self.assertIn('("TimedChoices", "runtime_timed_choices.js")', runtime_registry_source)
        self.assertIn('NATIVE_RUNTIME_TIMED_CHOICES_NAME = "runtime_timed_choices.py"', run_editor_source)
        self.assertIn('build_export_runtime_module_manifest("playerRuntime")', run_editor_source)
        self.assertIn('build_export_runtime_module_manifest("appRuntime", "app")', run_editor_source)
        self.assertIn('"runtimeTimedChoicesModule":', run_editor_source)
        self.assertIn('../export_player_template/runtime_timed_choices.js', editor_index)
        self.assertIn('./modules/timed_choice_editor.js', editor_index)
        self.assertIn('globalName: "CanvasiaEditorTimedChoice"', editor_guard)
        self.assertIn("createTimedChoiceController", editor_source)
        self.assertIn("readTimedChoiceEditor", editor_source)
        self.assertIn("timedChoiceState", editor_source)
        self.assertIn("renderTimedChoiceEditor", story_editors_source)
        self.assertIn('from "./runtime_timed_choices.js"', player_source)
        self.assertIn("timedChoiceState", player_source)
        self.assertIn("NativeTimedChoiceController", native_source)
        self.assertIn('"timedChoiceState": timed_choice_state', native_source)
        self.assertIn("canvasia_timed_choice", renpy_source)


if __name__ == "__main__":
    unittest.main()
