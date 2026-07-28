from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "rich_text_editor.js"


class FrontendRichTextEditorModuleTests(unittest.TestCase):
    def test_editor_wraps_selection_and_requires_ruby_reading(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const runtimeTools = {{
              buildRuntimeRichTextSummary(value) {{
                const text = String(value ?? "");
                return {{ label: text.includes("[[") ? "已有文字表现" : "使用普通文字" }};
              }},
              stripRuntimeRichText(value) {{
                return String(value ?? "").replace(/\\[\\[(?:em|whisper)=([^\\]]+)\\]\\]/g, "$1");
              }},
            }};
            const summaryNode = {{ textContent: "" }};
            const colorInput = {{ value: "#ff6b9e" }};
            const readingInput = {{ value: "" }};
            const card = {{
              querySelector(selector) {{
                if (selector === "[data-rich-text-summary]") return summaryNode;
                if (selector === "[data-rich-text-color]") return colorInput;
                if (selector === "[data-rich-text-reading]") return readingInput;
                return null;
              }},
            }};
            const detailRow = {{ querySelector: () => card }};
            const events = [];
            const textarea = {{
              tagName: "TEXTAREA",
              value: "漢字很重要",
              selectionStart: 0,
              selectionEnd: 2,
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
            const tools = context.window.CanvasiaEditorRichText;
            const markup = tools.renderRichTextEditor("editorDialogueText", textarea.value, {{ runtimeTools }});
            const missingReading = tools.applyRichTextAction(
              {{ dataset: {{ textareaId: "editorDialogueText", richTextAction: "ruby" }} }},
              {{ document: documentRef, runtimeTools }}
            );
            readingInput.value = "かんじ";
            const rubyResult = tools.applyRichTextAction(
              {{ dataset: {{ textareaId: "editorDialogueText", richTextAction: "ruby" }} }},
              {{ document: documentRef, runtimeTools }}
            );
            textarea.selectionStart = textarea.value.indexOf("重要");
            textarea.selectionEnd = textarea.selectionStart + 2;
            const colorResult = tools.applyRichTextAction(
              {{ dataset: {{ textareaId: "editorDialogueText", richTextAction: "color" }} }},
              {{ document: documentRef, runtimeTools }}
            );
            const valueBeforeEmpty = textarea.value;
            textarea.selectionEnd = textarea.selectionStart;
            const emptyResult = tools.applyRichTextAction(
              {{ dataset: {{ textareaId: "editorDialogueText", richTextAction: "emphasis" }} }},
              {{ document: documentRef, runtimeTools }}
            );
            process.stdout.write(JSON.stringify({{
              markup,
              value: textarea.value,
              missingReading,
              rubyResult,
              colorResult,
              emptyResult,
              valueBeforeEmpty,
              events,
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
        self.assertIn("文字表现", payload["markup"])
        self.assertIn('data-action="insert-rich-text"', payload["markup"])
        self.assertFalse(payload["missingReading"]["ok"])
        self.assertTrue(payload["rubyResult"]["ok"])
        self.assertTrue(payload["colorResult"]["ok"])
        self.assertFalse(payload["emptyResult"]["ok"])
        self.assertEqual(payload["value"], payload["valueBeforeEmpty"])
        self.assertIn("[[ruby=漢字|かんじ]]", payload["value"])
        self.assertIn("[[color=#ff6b9e|重要]]", payload["value"])
        self.assertEqual(payload["events"], ["input", "input"])
        self.assertEqual(payload["summary"], "已有文字表现")


if __name__ == "__main__":
    unittest.main()
