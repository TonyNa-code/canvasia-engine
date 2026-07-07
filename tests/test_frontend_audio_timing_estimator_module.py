from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "audio_timing_estimator.js"


class FrontendAudioTimingEstimatorModuleTests(unittest.TestCase):
    def test_audio_timing_estimator_counts_text_media_and_waits_without_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorAudioTimingEstimator;
            const blocks = [
              {{ type: "dialogue", text: "你好世界" }},
              {{ type: "choice", options: [{{ text: "留下" }}, {{ text: "离开" }}] }},
              {{ type: "wait", durationSeconds: 1.5 }},
              {{ type: "video_play", startTimeSeconds: 2, endTimeSeconds: 8 }},
              {{ type: "screen_flash", duration: "short" }},
            ];
            const dialogue = tools.estimateBlockTiming(blocks[0], {{ textCharactersPerSecond: 4, minimumTextSeconds: 0.5 }});
            const wait = tools.estimateBlockTiming(blocks[2]);
            const video = tools.estimateBlockTiming(blocks[3]);
            const range = tools.estimateBlockRangeTiming(blocks, 0, blocks.length - 1, {{
              textCharactersPerSecond: 4,
              minimumTextSeconds: 0.5,
              choiceDecisionSeconds: 2,
            }});
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              readableCharacters: tools.countReadableCharacters(" A 你 👩‍💻 "),
              dialogue,
              wait,
              video,
              range,
              zeroLabel: tools.formatEstimatedDuration(0),
              minuteLabel: tools.formatEstimatedDuration(125),
              shortHint: tools.buildAudioSegmentTimingHint({{
                tone: "short",
                durationLabel: "约 5 秒",
                readableCharacterCount: 12,
                textBlockCount: 1,
                waitSeconds: 1.5,
              }}),
              silentHint: tools.buildAudioSegmentTimingHint({{ tone: "silent", estimatedSeconds: 0 }}),
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

        self.assertIn("estimateBlockRangeTiming", payload["keys"])
        self.assertEqual(payload["readableCharacters"], 5)
        self.assertEqual(payload["dialogue"]["estimatedSeconds"], 1)
        self.assertEqual(payload["dialogue"]["textBlockCount"], 1)
        self.assertEqual(payload["wait"]["waitSeconds"], 1.5)
        self.assertEqual(payload["video"]["mediaBlockCount"], 1)
        self.assertEqual(payload["video"]["estimatedSeconds"], 6)
        self.assertEqual(payload["range"]["blockCount"], 5)
        self.assertGreater(payload["range"]["estimatedSeconds"], 10)
        self.assertEqual(payload["range"]["tone"], "balanced")
        self.assertEqual(payload["zeroLabel"], "约 0 秒")
        self.assertEqual(payload["minuteLabel"], "约 2分5秒")
        self.assertIn("含等待 2 秒", payload["shortHint"])
        self.assertIn("几乎没有正文", payload["silentHint"])


if __name__ == "__main__":
    unittest.main()
