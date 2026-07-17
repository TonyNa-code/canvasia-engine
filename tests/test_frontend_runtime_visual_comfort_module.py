from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_visual_comfort.js"
SETTINGS_MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_settings.js"


def run_node_module(script_body: str) -> dict:
    script = textwrap.dedent(
        f"""
        import * as tools from {json.dumps(MODULE_PATH.as_uri())};
        import * as settingsTools from {json.dumps(SETTINGS_MODULE_PATH.as_uri())};
        {script_body}
        """
    )
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    return json.loads(completed.stdout)


class FrontendRuntimeVisualComfortModuleTests(unittest.TestCase):
    def test_profiles_sanitize_and_scale_transient_effects(self) -> None:
        payload = run_node_module(
            """
            process.stdout.write(JSON.stringify({
              fallback: tools.getSafeVisualComfortMode("unknown"),
              gentle: tools.getVisualComfortSummary("GENTLE"),
              staticSummary: tools.getVisualComfortSummary("static"),
              gentleShake: tools.scaleVisualMotion(12, "gentle"),
              gentleFlash: tools.scaleVisualFlash(0.8, "gentle"),
              gentleTransition: tools.scaleVisualTransitionMs(600, "gentle"),
              staticTransition: tools.scaleVisualTransitionMs(600, "static"),
              invalidValue: tools.scaleVisualMotion("bad", "standard", 8),
              globalReady: globalThis.CanvasiaRuntimeVisualComfort?.getVisualComfortLabel("static"),
              storedMode: settingsTools.sanitizePlaybackSettings({ visualComfort: "STATIC" }).visualComfort,
            }));
            """
        )

        self.assertEqual(payload["fallback"], "standard")
        self.assertEqual(payload["gentle"]["label"], "柔和模式")
        self.assertEqual(payload["gentle"]["motionPercent"], 35)
        self.assertEqual(payload["staticSummary"]["disablesTransientEffects"], True)
        self.assertAlmostEqual(payload["gentleShake"], 4.2)
        self.assertAlmostEqual(payload["gentleFlash"], 0.24)
        self.assertEqual(payload["gentleTransition"], 330)
        self.assertEqual(payload["staticTransition"], 0)
        self.assertEqual(payload["invalidValue"], 8)
        self.assertEqual(payload["globalReady"], "静态模式")
        self.assertEqual(payload["storedMode"], "static")


if __name__ == "__main__":
    unittest.main()
