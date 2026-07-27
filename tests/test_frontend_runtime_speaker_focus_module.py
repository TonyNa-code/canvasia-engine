from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_speaker_focus.js"


def run_node_module(script_body: str) -> dict:
    script = textwrap.dedent(
        f"""
        import * as tools from {json.dumps(MODULE_PATH.as_uri())};
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


class FrontendRuntimeSpeakerFocusModuleTests(unittest.TestCase):
    def test_focus_config_and_poses_are_safe_and_composable(self) -> None:
        payload = run_node_module(
            """
            const config = tools.getSpeakerFocusConfig({
              speakerFocusMode: "broken",
              speakerFocusIntensity: 999,
              speakerFocusTransitionMs: -20,
            });
            const shared = {
              activeCharacterId: "heroine",
              visibleCharacterIds: ["hero", "heroine"],
              gameUiConfig: { speakerFocusMode: "soft", speakerFocusIntensity: 65 },
            };
            const active = tools.buildSpeakerFocusPose({ ...shared, characterId: "heroine" });
            const muted = tools.buildSpeakerFocusPose({ ...shared, characterId: "hero" });
            const neutral = tools.buildSpeakerFocusPose({
              ...shared,
              characterId: "hero",
              visibleCharacterIds: ["hero"],
            });
            const staticActive = tools.buildSpeakerFocusPose({
              ...shared,
              characterId: "heroine",
              visualComfortMode: "static",
            });
            const presentation = tools.buildSpeakerFocusPresentation({ ...shared, characterId: "hero" });
            process.stdout.write(JSON.stringify({ config, active, muted, neutral, staticActive, presentation }));
            """
        )

        self.assertEqual(payload["config"], {
            "speakerFocusMode": "soft",
            "speakerFocusIntensity": 100,
            "speakerFocusTransitionMs": 0,
        })
        self.assertEqual(payload["active"]["role"], "active")
        self.assertEqual(payload["active"]["scaleMultiplier"], 1.012)
        self.assertEqual(payload["active"]["layerBoost"], 100)
        self.assertEqual(payload["muted"]["role"], "muted")
        self.assertEqual(payload["muted"]["opacityMultiplier"], 0.87)
        self.assertEqual(payload["muted"]["brightnessMultiplier"], 0.883)
        self.assertEqual(payload["neutral"]["role"], "neutral")
        self.assertEqual(payload["neutral"]["opacityMultiplier"], 1)
        self.assertEqual(payload["staticActive"]["scaleMultiplier"], 1)
        self.assertEqual(payload["staticActive"]["transitionMs"], 0)
        self.assertIn("is-speaker-focus-muted", payload["presentation"]["classNames"])
        self.assertIn("--speaker-focus-opacity:0.870", payload["presentation"]["style"])

    def test_focus_requires_a_visible_active_speaker(self) -> None:
        payload = run_node_module(
            """
            const missingSpeaker = tools.buildSpeakerFocusPose({
              characterId: "hero",
              activeCharacterId: "missing",
              visibleCharacterIds: ["hero", "heroine"],
            });
            const disabled = tools.buildSpeakerFocusPose({
              characterId: "hero",
              activeCharacterId: "heroine",
              visibleCharacterIds: ["hero", "heroine"],
              gameUiConfig: { speakerFocusMode: "off" },
            });
            process.stdout.write(JSON.stringify({ missingSpeaker, disabled }));
            """
        )

        self.assertEqual(payload["missingSpeaker"]["role"], "neutral")
        self.assertEqual(payload["disabled"]["role"], "neutral")


if __name__ == "__main__":
    unittest.main()
