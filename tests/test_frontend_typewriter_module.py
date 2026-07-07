from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "typewriter.js"


class FrontendTypewriterModuleTests(unittest.TestCase):
    def test_typewriter_handles_graphemes_quotes_abbreviations_and_punctuation_without_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}}, Intl }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorTypewriter;
            const emojiText = "A👩‍💻B";
            const quoteText = "「你好」 世界";
            const fullText = "Dr. A arrives. 好吗？";
            const emojiNext = tools.getNextCodePointIndex(emojiText, 1);
            const quoteFirstStep = tools.getNextTypewriterIndex(quoteText, 0);
            const quoteSecondStep = tools.getNextTypewriterIndex(quoteText, quoteFirstStep);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              safeSpeeds: [
                tools.getSafeTypewriterTextSpeed("fast"),
                tools.getSafeTypewriterTextSpeed("missing"),
              ],
              emojiCluster: emojiText.slice(1, emojiNext),
              quoteFirstStep,
              quoteFirstVisible: quoteText.slice(0, quoteFirstStep),
              quoteSecondVisible: quoteText.slice(0, quoteSecondStep),
              trailingCloserIndex: tools.includeTypewriterTrailingClosers("你好。」下一句", 3),
              pauseQuestion: tools.getTypewriterPunctuationPause("好吗？", fullText),
              pauseEllipsis: tools.getTypewriterPunctuationPause("等等……", "等等……"),
              pauseComma: tools.getTypewriterPunctuationPause("然后，", "然后，继续"),
              pauseInlinePeriod: tools.getTypewriterPunctuationPause("v1.", "v1.2"),
              pauseAbbreviation: tools.getTypewriterPunctuationPause("Dr.", fullText),
              delayFastQuestion: tools.getTypewriterStepDelay("fast", "好吗？", fullText),
              delayInstant: tools.getTypewriterStepDelay("instant", "好吗？", fullText),
              pauseAnchor: tools.getTypewriterPauseAnchorText("“结束。”"),
              pauseAnchorChar: tools.getTypewriterPauseAnchorChar("“结束。”"),
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

        self.assertIn("getNextTypewriterIndex", payload["keys"])
        self.assertEqual(payload["safeSpeeds"], ["fast", "normal"])
        self.assertEqual(payload["emojiCluster"], "👩‍💻")
        self.assertEqual(payload["quoteFirstVisible"], "「你")
        self.assertEqual(payload["quoteSecondVisible"], "「你好」 ")
        self.assertGreater(payload["trailingCloserIndex"], 3)
        self.assertEqual(payload["pauseQuestion"], 260)
        self.assertEqual(payload["pauseEllipsis"], 220)
        self.assertEqual(payload["pauseComma"], 140)
        self.assertEqual(payload["pauseInlinePeriod"], 0)
        self.assertEqual(payload["pauseAbbreviation"], 0)
        self.assertEqual(payload["delayFastQuestion"], 278)
        self.assertEqual(payload["delayInstant"], 0)
        self.assertEqual(payload["pauseAnchor"], "“结束。")
        self.assertEqual(payload["pauseAnchorChar"], "。")


if __name__ == "__main__":
    unittest.main()
