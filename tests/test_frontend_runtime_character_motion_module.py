from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_character_motion.js"


class FrontendRuntimeCharacterMotionModuleTests(unittest.TestCase):
    def test_runtime_character_motion_normalizes_stage_and_css_state(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};
            const previous = {{
              characterId: "hero",
              expressionId: "neutral",
              position: "left",
              stage: {{ offsetX: -200, offsetY: 12, scale: 90, opacity: 80, layer: 2, flipX: false }},
            }};
            const target = {{
              characterId: "hero",
              expressionId: "smile",
              position: "right",
              stage: {{ offsetX: 8, offsetY: -4, scale: 130, opacity: 100, layer: 4, flipX: true }},
            }};
            const event = tools.buildCharacterMotionEvent(previous, target, {{ durationMs: 900, easing: "spring" }});
            process.stdout.write(JSON.stringify({{
              stage: tools.getSafeCharacterStage(previous.stage),
              event,
              targetStyle: tools.getCharacterStageStyle(target.stage, target.position),
              motionStyle: tools.getCharacterMotionStyle(event),
              invalidEasing: tools.getSafeCharacterMotionEasing("warp"),
              clampedDuration: tools.getSafeCharacterMotionDurationMs(99999),
              positionPercent: tools.getCharacterPositionPercent("right"),
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
        self.assertEqual(payload["stage"]["offsetX"], -60)
        self.assertEqual(payload["event"]["durationMs"], 900)
        self.assertEqual(payload["event"]["easing"], "spring")
        self.assertIn("--sprite-position-x:76%", payload["targetStyle"])
        self.assertIn("--sprite-from-position-x:24%", payload["motionStyle"])
        self.assertIn("--sprite-motion-ms:900ms", payload["motionStyle"])
        self.assertEqual(payload["invalidEasing"], "ease_out")
        self.assertEqual(payload["clampedDuration"], 10000)
        self.assertEqual(payload["positionPercent"], 76)


if __name__ == "__main__":
    unittest.main()
