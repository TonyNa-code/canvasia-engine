from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_story_text.js"
RICH_MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_rich_text.js"


class FrontendRuntimeStoryTextModuleTests(unittest.TestCase):
    def test_rich_text_and_pacing_share_visible_boundaries(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as story from {json.dumps(MODULE_PATH.as_uri())};
            import * as rich from {json.dumps(RICH_MODULE_PATH.as_uri())};

            const source = "先[[em=重要]][[pause=0.35]]再[[ruby=漢字|かんじ]][[color=#FF6699|心动]][[whisper=轻声]]";
            const plan = story.parseRuntimeStoryText(source);
            const malformed = rich.parseRuntimeRichText("保留[[color=red|文字]]和[[ruby=字|]]");
            const unsafe = story.renderRuntimeStoryText("[[em=<img src=x onerror=alert(1)>]]");
            const partialRuby = story.renderRuntimeStoryText(plan, {{ visibleEnd: 5 }});
            const full = story.renderRuntimeStoryText(plan);

            process.stdout.write(JSON.stringify({{
              plan,
              malformed,
              unsafe,
              partialRuby,
              full,
              stripped: story.stripRuntimeStoryText(source),
              summary: rich.buildRuntimeRichTextSummary(source),
              globalsAttached: Boolean(globalThis.CanvasiaRuntimeRichText && globalThis.CanvasiaRuntimeStoryText),
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
        self.assertEqual(payload["plan"]["plainText"], "先重要再漢字心动轻声")
        self.assertEqual(payload["plan"]["cues"][0]["index"], 3)
        self.assertEqual(
            [segment["type"] for segment in payload["plan"]["segments"]],
            ["emphasis", "ruby", "color", "whisper"],
        )
        self.assertEqual(payload["stripped"], payload["plan"]["plainText"])
        self.assertIn("[[color=red|文字]]", payload["malformed"]["plainText"])
        self.assertIn("[[ruby=字|]]", payload["malformed"]["plainText"])
        self.assertNotIn("<img", payload["unsafe"])
        self.assertIn("&lt;img", payload["unsafe"])
        self.assertNotIn("<ruby", payload["partialRuby"])
        self.assertIn("<ruby", payload["full"])
        self.assertIn("runtime-rich-text-color", payload["full"])
        self.assertEqual(payload["summary"]["ruby"], 1)
        self.assertTrue(payload["globalsAttached"])


if __name__ == "__main__":
    unittest.main()
