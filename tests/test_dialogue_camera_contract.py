from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path

from native_runtime.runtime_dialogue_camera import build_native_dialogue_camera_pose


ROOT_DIR = Path(__file__).resolve().parents[1]
WEB_MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_dialogue_camera.js"


class DialogueCameraContractTests(unittest.TestCase):
    def test_web_and_native_automatic_camera_math_stays_aligned(self) -> None:
        scenarios = [
            {
                "activeCharacterId": "a",
                "visibleCharacters": [
                    {"characterId": "a", "position": "left", "stage": {"offsetX": 4}},
                    {"characterId": "b", "position": "right"},
                ],
                "gameUiConfig": {"dialogueCameraMode": "soft", "dialogueCameraIntensity": 58},
                "visualComfortMode": "standard",
            },
            {
                "activeCharacterId": "b",
                "visibleCharacters": [
                    {"characterId": "a", "position": "left"},
                    {"characterId": "b", "position": "right", "stage": {"offsetX": -3}},
                ],
                "gameUiConfig": {"dialogueCameraMode": "cinematic", "dialogueCameraIntensity": 80},
                "visualComfortMode": "gentle",
            },
            {
                "activeCharacterId": "a",
                "visibleCharacters": [{"characterId": "a", "position": "left"}],
                "gameUiConfig": {"dialogueCameraMode": "soft"},
                "visualComfortMode": "static",
            },
        ]
        script = textwrap.dedent(
            f"""
            import {{ buildDialogueCameraPose }} from {json.dumps(WEB_MODULE_PATH.as_uri())};
            const scenarios = {json.dumps(scenarios)};
            process.stdout.write(JSON.stringify(scenarios.map((item) => buildDialogueCameraPose(item))));
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
        web_poses = json.loads(completed.stdout)
        native_poses = [
            build_native_dialogue_camera_pose(
                active_character_id=item["activeCharacterId"],
                visible_characters=item["visibleCharacters"],
                game_ui_config=item["gameUiConfig"],
                visual_comfort_mode=item["visualComfortMode"],
            )
            for item in scenarios
        ]
        self.assertEqual(web_poses, native_poses)

    def test_editor_export_and_native_runtime_are_all_wired(self) -> None:
        run_editor_source = (ROOT_DIR / "run_editor.py").read_text(encoding="utf-8")
        player_source = (ROOT_DIR / "export_player_template" / "player.js").read_text(encoding="utf-8")
        editor_source = (ROOT_DIR / "prototype_editor" / "app.js").read_text(encoding="utf-8")
        native_source = (ROOT_DIR / "native_runtime" / "runtime_player.py").read_text(encoding="utf-8")
        native_stage_renderer_source = (
            ROOT_DIR / "native_runtime" / "runtime_stage_renderer.py"
        ).read_text(encoding="utf-8")
        player_css = (ROOT_DIR / "export_player_template" / "player.css").read_text(encoding="utf-8")
        editor_css = (ROOT_DIR / "prototype_editor" / "styles.css").read_text(encoding="utf-8")

        self.assertIn('"runtime_dialogue_camera.js"', run_editor_source)
        self.assertIn('NATIVE_RUNTIME_DIALOGUE_CAMERA_NAME = "runtime_dialogue_camera.py"', run_editor_source)
        self.assertIn('from "./runtime_dialogue_camera.js"', player_source)
        self.assertIn("dialogueCameraTools.buildStageCameraPresentation", editor_source)
        self.assertIn("render_native_stage_surface(self, stage_surface)", native_source)
        self.assertIn("dialogue_camera_controller.build_render_pose", native_stage_renderer_source)
        self.assertIn("--dialogue-camera-transition-ms", player_css)
        self.assertIn("--dialogue-camera-transition-ms", editor_css)


if __name__ == "__main__":
    unittest.main()
