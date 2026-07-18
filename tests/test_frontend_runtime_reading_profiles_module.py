from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_reading_profiles.js"
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


class FrontendRuntimeReadingProfilesModuleTests(unittest.TestCase):
    def test_profiles_apply_detect_and_sanitize_player_preferences(self) -> None:
        payload = run_node_module(
            """
            const base = { language: "ja-JP", bgmVolume: 64 };
            const large = tools.applyReadingProfile(base, "large");
            const custom = { ...large, dialogBoxOpacityPercent: 60 };
            process.stdout.write(JSON.stringify({
              ids: tools.READING_PROFILE_IDS,
              large,
              largeDetected: tools.detectReadingProfile(large),
              customDetected: tools.detectReadingProfile(custom),
              customSummary: tools.getReadingProfileSummary(custom),
              safeScale: tools.getSafeReadingTextScalePercent(999),
              safeOpacity: tools.getSafeDialogBoxOpacityPercent(-10),
              stored: settingsTools.sanitizePlaybackSettings({
                textScalePercent: 999,
                dialogBoxOpacityPercent: -10,
              }),
              globalReady: globalThis.CanvasiaRuntimeReadingProfiles?.getReadingProfileLabel("comfortable"),
            }));
            """
        )

        self.assertEqual(payload["ids"], ["standard", "comfortable", "large", "calm"])
        self.assertEqual(payload["large"]["language"], "ja-JP")
        self.assertEqual(payload["large"]["bgmVolume"], 64)
        self.assertEqual(payload["large"]["textSpeed"], "slow")
        self.assertEqual(payload["large"]["textScalePercent"], 125)
        self.assertEqual(payload["large"]["visualComfort"], "gentle")
        self.assertEqual(payload["largeDetected"], "large")
        self.assertEqual(payload["customDetected"], "custom")
        self.assertEqual(payload["customSummary"]["label"], "自定义组合")
        self.assertEqual(payload["safeScale"], 125)
        self.assertEqual(payload["safeOpacity"], 0)
        self.assertEqual(payload["stored"]["textScalePercent"], 125)
        self.assertEqual(payload["stored"]["dialogBoxOpacityPercent"], 0)
        self.assertEqual(payload["globalReady"], "舒适阅读")


if __name__ == "__main__":
    unittest.main()
