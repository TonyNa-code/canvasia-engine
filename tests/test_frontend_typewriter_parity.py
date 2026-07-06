from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EDITOR_TYPEWRITER_PATH = ROOT_DIR / "prototype_editor" / "modules" / "typewriter.js"
RUNTIME_TEXT_EFFECTS_PATH = ROOT_DIR / "export_player_template" / "runtime_text_effects.js"


class FrontendTypewriterParityTests(unittest.TestCase):
    def test_editor_preview_and_web_runtime_typewriter_rules_match(self) -> None:
        script = textwrap.dedent(
            f"""
            import fs from "node:fs";
            import vm from "node:vm";
            import * as runtimeTools from {json.dumps(RUNTIME_TEXT_EFFECTS_PATH.as_uri())};

            const editorSandbox = {{}};
            vm.createContext(editorSandbox);
            vm.runInContext(fs.readFileSync({json.dumps(str(EDITOR_TYPEWRITER_PATH))}, "utf8"), editorSandbox);
            const editorTools = editorSandbox.CanvasiaEditorTypewriter;

            function compare(label, editorValue, runtimeValue) {{
              if (JSON.stringify(editorValue) !== JSON.stringify(runtimeValue)) {{
                throw new Error(`${{label}} mismatch: editor=${{JSON.stringify(editorValue)}} runtime=${{JSON.stringify(runtimeValue)}}`);
              }}
              return {{ label, value: editorValue }};
            }}

            const revealCases = [
              ["emoji surrogate", "A💙B", 1],
              ["partial surrogate recovery", "A💙B", 2],
              ["family emoji", "A👨‍👩‍👧‍👦B", 1],
              ["flag emoji", "A🇯🇵B", 1],
              ["skin tone emoji", "A👍🏽B", 1],
              ["combining accent", "e\\u0301!", 0],
              ["latin word group", "abc def", 0],
              ["opening quote cn", "“再见。”", 0],
              ["opening quote en", '"Hi" there', 0],
              ["closing quote cn", "“再见。”下一句", "“再见。”下一句".indexOf("。")],
              ["closing quote en", '"Hi" there', '"Hi" there'.indexOf("i")],
            ];

            const pauseCases = [
              ["cn full stop", "世界！", ""],
              ["quoted cn full stop", "“再见。”", ""],
              ["cn comma", "嗯，", ""],
              ["en full stop", "Hello.", ""],
              ["ascii ellipsis", "Wait...", ""],
              ["quoted ascii ellipsis", '"Wait..."', ""],
              ["decimal period", "3.", "3.14"],
              ["version period", "v1.", "v1.2"],
              ["domain period", "example.", "example.com"],
              ["numeric sentence", "Chapter 1.", ""],
              ["honorific abbreviation", "Mr.", "Mr. Smith"],
              ["latin abbreviation", "e.g.", "e.g. this"],
              ["terminal abbreviation", "Dr.", ""],
            ];

            const speedCases = [
              ["bad speed", "bad", "Hello", "Hello world"],
              ["slow comma", "slow", "Hello,", "Hello, world"],
              ["normal cn punctuation", "normal", "世界！", "世界！下一句"],
              ["fast plain", "fast", "Hello", "Hello"],
              ["instant punctuation", "instant", "世界！", "世界！"],
            ];

            const results = [];

            for (const [label, text, index] of revealCases) {{
              results.push(compare(
                `nextIndex:${{label}}`,
                editorTools.getNextTypewriterIndex(text, index),
                runtimeTools.getNextTypewriterIndex(text, index)
              ));
            }}

            for (const [label, text, fullText] of pauseCases) {{
              results.push(compare(
                `pause:${{label}}`,
                editorTools.getTypewriterPunctuationPause(text, fullText),
                runtimeTools.getTypewriterPunctuationPause(text, fullText)
              ));
            }}

            for (const [label, speed, visibleText, fullText] of speedCases) {{
              results.push(compare(
                `delay:${{label}}`,
                editorTools.getTypewriterStepDelay(speed, visibleText, fullText),
                runtimeTools.getTypewriterStepDelay(speed, visibleText, fullText)
              ));
            }}

            results.push(compare(
              "safeSpeed:fallback",
              editorTools.getSafeTypewriterTextSpeed("turbo"),
              runtimeTools.getSafeRuntimeTextSpeed("turbo")
            ));
            results.push(compare(
              "safeSpeed:fast",
              editorTools.getSafeTypewriterTextSpeed("fast"),
              runtimeTools.getSafeRuntimeTextSpeed("fast")
            ));

            process.stdout.write(JSON.stringify({{
              compared: results.length,
              labels: results.map((result) => result.label),
            }}));
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
        payload = json.loads(completed.stdout)
        self.assertGreaterEqual(payload["compared"], 30)
        self.assertIn("nextIndex:family emoji", payload["labels"])
        self.assertIn("pause:latin abbreviation", payload["labels"])
        self.assertIn("delay:instant punctuation", payload["labels"])


if __name__ == "__main__":
    unittest.main()
