from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_dialogue_camera.js"


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


class FrontendRuntimeDialogueCameraModuleTests(unittest.TestCase):
    def test_dialogue_camera_config_and_pose_are_safe(self) -> None:
        payload = run_node_module(
            """
            const config = tools.getDialogueCameraConfig({
              dialogueCameraMode: "broken",
              dialogueCameraIntensity: 999,
              dialogueCameraTransitionMs: -20,
            });
            const left = tools.buildDialogueCameraPose({
              activeCharacterId: "hero",
              visibleCharacters: [
                { characterId: "hero", position: "left", stage: { offsetX: 4 } },
                { characterId: "heroine", position: "right" },
              ],
              gameUiConfig: { dialogueCameraMode: "soft", dialogueCameraIntensity: 50 },
            });
            const gentleRight = tools.buildDialogueCameraPose({
              activeCharacterId: "heroine",
              visibleCharacters: [
                { characterId: "hero", position: "left" },
                { characterId: "heroine", position: "right", stage: { offsetX: -2 } },
              ],
              gameUiConfig: {
                dialogueCameraMode: "cinematic",
                dialogueCameraIntensity: 80,
                dialogueCameraTransitionMs: 600,
              },
              visualComfortMode: "gentle",
            });
            const staticPose = tools.buildDialogueCameraPose({
              activeCharacterId: "hero",
              visibleCharacters: [{ characterId: "hero", position: "left" }],
              visualComfortMode: "static",
            });
            process.stdout.write(JSON.stringify({ config, left, gentleRight, staticPose }));
            """
        )

        self.assertEqual(payload["config"], {
            "dialogueCameraMode": "soft",
            "dialogueCameraIntensity": 100,
            "dialogueCameraTransitionMs": 0,
        })
        self.assertTrue(payload["left"]["active"])
        self.assertEqual(payload["left"]["focusPercent"], 28)
        self.assertEqual(payload["left"]["panPercent"], 1.65)
        self.assertEqual(payload["left"]["zoomScale"], 1.011)
        self.assertEqual(payload["gentleRight"]["panPercent"], -1.882)
        self.assertEqual(payload["gentleRight"]["zoomScale"], 1.014)
        self.assertEqual(payload["gentleRight"]["transitionMs"], 420)
        self.assertFalse(payload["staticPose"]["active"])
        self.assertEqual(payload["staticPose"]["panPercent"], 0)
        self.assertEqual(payload["staticPose"]["zoomScale"], 1)

    def test_explicit_camera_blocks_override_only_their_axis(self) -> None:
        payload = run_node_module(
            """
            const shared = {
              activeCharacterId: "hero",
              visibleCharacters: [
                { characterId: "hero", position: "left", stage: { offsetX: 4 } },
                { characterId: "heroine", position: "right" },
              ],
              gameUiConfig: { dialogueCameraMode: "soft", dialogueCameraIntensity: 50 },
            };
            const zoomOnly = tools.buildStageCameraPresentation({
              ...shared,
              cameraZoom: { action: "zoom_in", strength: "medium", focus: "left" },
            });
            const both = tools.buildStageCameraPresentation({
              ...shared,
              cameraZoom: { action: "zoom_out", strength: "light", focus: "right" },
              cameraPan: { target: "right", strength: "heavy" },
            });
            process.stdout.write(JSON.stringify({ zoomOnly, both }));
            """
        )

        self.assertTrue(payload["zoomOnly"]["autoActive"])
        self.assertEqual(payload["zoomOnly"]["zoomScale"], 1.16)
        self.assertEqual(payload["zoomOnly"]["panPercent"], 1.65)
        self.assertEqual(payload["zoomOnly"]["transformOrigin"], "28% 52%")
        self.assertFalse(payload["both"]["autoActive"])
        self.assertEqual(payload["both"]["zoomScale"], 0.96)
        self.assertEqual(payload["both"]["panPercent"], -12)
        self.assertIn("--dialogue-camera-transition-ms:520ms", payload["both"]["style"])


if __name__ == "__main__":
    unittest.main()
