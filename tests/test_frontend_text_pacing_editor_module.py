from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "text_pacing_editor.js"


class FrontendTextPacingEditorModuleTests(unittest.TestCase):
    def test_editor_inserts_pause_and_wraps_selected_text(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const runtimeTools = {{
              buildTextPacingSummary(value) {{
                const text = String(value ?? "");
                const pauseCount = (text.match(/\\[\\[pause=/g) ?? []).length;
                const speedCount = (text.match(/\\[\\[speed=/g) ?? []).length;
                return {{
                  label: pauseCount || speedCount ? `${{pauseCount}} 处停顿 · ${{speedCount}} 次语速变化` : "尚未加入句内节奏",
                  pauseCount,
                  speedCount,
                }};
              }},
            }};
            const summaryNode = {{ textContent: "" }};
            const card = {{ querySelector: () => summaryNode }};
            const detailRow = {{ querySelector: () => card }};
            const events = [];
            const textarea = {{
              tagName: "TEXTAREA",
              value: "她说完了。",
              selectionStart: 1,
              selectionEnd: 1,
              parentElement: detailRow,
              closest: () => detailRow,
              setSelectionRange(start, end) {{ this.selectionStart = start; this.selectionEnd = end; }},
              focus() {{ this.focused = true; }},
              dispatchEvent(event) {{ events.push(event.type); }},
            }};
            const documentRef = {{ getElementById: (id) => id === "editorDialogueText" ? textarea : null }};
            class FakeEvent {{ constructor(type, options) {{ this.type = type; this.bubbles = options?.bubbles; }} }}
            const context = {{ window: {{}}, Event: FakeEvent }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorTextPacing;
            const markup = tools.renderTextPacingEditor("editorDialogueText", textarea.value, {{ runtimeTools }});
            const pauseResult = tools.applyTextPacingAction(
              {{ dataset: {{ textareaId: "editorDialogueText", textPacingAction: "pause-short" }} }},
              {{ document: documentRef, runtimeTools }}
            );
            textarea.selectionStart = 0;
            textarea.selectionEnd = 1;
            const speedResult = tools.applyTextPacingAction(
              {{ dataset: {{ textareaId: "editorDialogueText", textPacingAction: "speed-slow" }} }},
              {{ document: documentRef, runtimeTools }}
            );
            const valueBeforeEmptySelection = textarea.value;
            textarea.selectionStart = 2;
            textarea.selectionEnd = 2;
            const emptySelectionResult = tools.applyTextPacingAction(
              {{ dataset: {{ textareaId: "editorDialogueText", textPacingAction: "speed-fast" }} }},
              {{ document: documentRef, runtimeTools }}
            );
            process.stdout.write(JSON.stringify({{
              markup,
              value: textarea.value,
              pauseResult,
              speedResult,
              emptySelectionResult,
              valueBeforeEmptySelection,
              events,
              focused: textarea.focused,
              summary: summaryNode.textContent,
            }}));
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
        self.assertIn("句内节奏", payload["markup"])
        self.assertIn("data-action=\"insert-text-pacing\"", payload["markup"])
        self.assertTrue(payload["pauseResult"]["ok"])
        self.assertTrue(payload["speedResult"]["ok"])
        self.assertFalse(payload["emptySelectionResult"]["ok"])
        self.assertIn("请先选中", payload["emptySelectionResult"]["label"])
        self.assertEqual(payload["value"], payload["valueBeforeEmptySelection"])
        self.assertIn("[[pause=0.35]]", payload["value"])
        self.assertTrue(payload["value"].startswith("[[speed=slow]]她[[speed=inherit]]"))
        self.assertEqual(payload["events"], ["input", "input"])
        self.assertTrue(payload["focused"])
        self.assertIn("1 处停顿", payload["summary"])


if __name__ == "__main__":
    unittest.main()
