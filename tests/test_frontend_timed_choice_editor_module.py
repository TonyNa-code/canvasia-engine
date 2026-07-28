from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "timed_choice_editor.js"


class FrontendTimedChoiceEditorModuleTests(unittest.TestCase):
    def test_editor_renders_safe_controls_and_reads_canonical_fields(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const runtimeTools = {{
              TIMED_CHOICE_PRESET_SECONDS: [5, 10, 15, 30],
              getSafeTimedChoiceSeconds(value) {{
                const number = Number.parseFloat(value ?? 0);
                return number > 0 ? Math.min(Math.max(number, 1), 300) : 0;
              }},
              sanitizeTimedChoiceConfig(block) {{
                const timeoutSeconds = this.getSafeTimedChoiceSeconds(block.timeoutSeconds ?? 0);
                return {{
                  enabled: timeoutSeconds > 0,
                  timeoutSeconds,
                  timeoutOptionId: String(block.timeoutOptionId ?? "").trim(),
                }};
              }},
            }};
            const context = {{ window: {{}}, CanvasiaRuntimeTimedChoices: runtimeTools }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorTimedChoice;
            const markup = tools.renderTimedChoiceEditor(
              {{ timeoutSeconds: 15, timeoutOptionId: "route_b" }},
              {{
                runtimeTools,
                choiceOptions: [
                  {{ id: "route_a", text: "普通路线" }},
                  {{ id: "route_b", text: "追上 <她>" }},
                ],
              }}
            );
            const fields = {{
              editorChoiceTimeoutSeconds: {{ value: "custom" }},
              editorChoiceTimeoutCustomSeconds: {{ value: "18.5" }},
              editorChoiceTimeoutOptionId: {{ value: "route_b" }},
            }};
            const updated = tools.readTimedChoiceEditor(
              {{ id: "choice_1", choiceTimeoutSeconds: 9, choiceTimeoutOptionId: "legacy" }},
              {{ runtimeTools, document: {{ getElementById: (id) => fields[id] }} }}
            );
            fields.editorChoiceTimeoutSeconds.value = "0";
            const disabled = tools.readTimedChoiceEditor(updated, {{
              runtimeTools,
              document: {{ getElementById: (id) => fields[id] }},
            }});
            process.stdout.write(JSON.stringify({{ markup, updated, disabled, keys: Object.keys(tools).sort() }}));
            """
        )
        completed = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["keys"], ["readTimedChoiceEditor", "renderTimedChoiceEditor"])
        self.assertIn("限时选择", payload["markup"])
        self.assertIn("15 秒", payload["markup"])
        self.assertIn("追上 &lt;她&gt;", payload["markup"])
        self.assertIn('value="route_b" selected', payload["markup"])
        self.assertEqual(payload["updated"]["timeoutSeconds"], 18.5)
        self.assertEqual(payload["updated"]["timeoutOptionId"], "route_b")
        self.assertNotIn("choiceTimeoutSeconds", payload["updated"])
        self.assertNotIn("choiceTimeoutOptionId", payload["updated"])
        self.assertNotIn("timeoutSeconds", payload["disabled"])
        self.assertNotIn("timeoutOptionId", payload["disabled"])


if __name__ == "__main__":
    unittest.main()
