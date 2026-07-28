from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_text_pacing.js"


class FrontendRuntimeTextPacingModuleTests(unittest.TestCase):
    def test_parser_boundaries_and_delays_are_safe(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};

            const plan = tools.parseRuntimeTextPacing(
              "A[[pause=0.35]]BC[[speed=slow]]慢慢[[speed=inherit]]结束"
            );
            const invalid = tools.parseRuntimeTextPacing(
              "保留[[pause=oops]]和[[speed=turbo]]"
            );
            const leading = tools.parseRuntimeTextPacing("[[pause=0.8]]开场");
            const localInstant = tools.parseRuntimeTextPacing(
              "A[[speed=instant]][[pause=0.35]]B"
            );
            const groupedNext = (_text, index) => index + 3;
            const boundary = tools.getNextTextPacingIndex(plan, 0, groupedNext);
            const initial = tools.getInitialTextPacingIndex(leading, groupedNext);
            const delay = tools.getTextPacingStepDelay(
              plan,
              1,
              "normal",
              "A",
              plan.plainText,
              (speed) => (speed === "slow" ? 40 : 20)
            );
            const instantDelay = tools.getTextPacingStepDelay(
              plan,
              1,
              "instant",
              "A",
              plan.plainText,
              () => 20
            );
            const localInstantDelay = tools.getTextPacingStepDelay(
              localInstant,
              1,
              "normal",
              "A",
              localInstant.plainText,
              () => 20
            );
            const playerInstantDelay = tools.getTextPacingStepDelay(
              localInstant,
              1,
              "instant",
              "A",
              localInstant.plainText,
              () => 20
            );

            process.stdout.write(JSON.stringify({{
              plan,
              invalid,
              boundary,
              initial,
              delay,
              instantDelay,
              localInstantDelay,
              playerInstantDelay,
              slowSpeed: tools.getTextPacingSpeedAt(plan, 3, "normal"),
              resetSpeed: tools.getTextPacingSpeedAt(plan, 5, "normal"),
              summary: tools.buildTextPacingSummary(plan.sourceText),
              globalAttached: Boolean(globalThis.CanvasiaRuntimeTextPacing),
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
        self.assertEqual(payload["plan"]["plainText"], "ABC慢慢结束")
        self.assertEqual(payload["boundary"], 1)
        self.assertEqual(payload["initial"], 0)
        self.assertEqual(payload["delay"], 370)
        self.assertEqual(payload["instantDelay"], 0)
        self.assertEqual(payload["localInstantDelay"], 350)
        self.assertEqual(payload["playerInstantDelay"], 0)
        self.assertEqual(payload["slowSpeed"], "slow")
        self.assertEqual(payload["resetSpeed"], "normal")
        self.assertIn("[[pause=oops]]", payload["invalid"]["plainText"])
        self.assertIn("[[speed=turbo]]", payload["invalid"]["plainText"])
        self.assertEqual(payload["summary"]["pauseCount"], 1)
        self.assertEqual(payload["summary"]["speedCount"], 2)
        self.assertTrue(payload["globalAttached"])


if __name__ == "__main__":
    unittest.main()
