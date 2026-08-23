from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path

from native_runtime.runtime_voice_reactive_motion import build_native_voice_reactive_motion_pose


ROOT_DIR = Path(__file__).resolve().parents[1]
WEB_MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_voice_reactive_motion.js"


class VoiceReactiveMotionContractTests(unittest.TestCase):
    def test_web_and_native_motion_math_stays_aligned(self) -> None:
        scenarios = [
            {
                "characterId": "hero",
                "activeCharacterId": "hero",
                "voiceActive": True,
                "voiceLevel": 0.75,
                "gameUiConfig": {
                    "voiceReactiveMotionMode": "soft",
                    "voiceReactiveMotionIntensity": 58,
                },
                "visualComfortMode": "standard",
                "isLeaving": False,
            },
            {
                "characterId": "heroine",
                "activeCharacterId": "heroine",
                "voiceActive": True,
                "voiceLevel": 0.92,
                "gameUiConfig": {
                    "voiceReactiveMotionMode": "cinematic",
                    "voiceReactiveMotionIntensity": 80,
                },
                "visualComfortMode": "gentle",
                "isLeaving": False,
            },
            {
                "characterId": "hero",
                "activeCharacterId": "heroine",
                "voiceActive": True,
                "voiceLevel": 0.8,
                "gameUiConfig": {"voiceReactiveMotionMode": "soft"},
                "visualComfortMode": "standard",
                "isLeaving": False,
            },
            {
                "characterId": "hero",
                "activeCharacterId": "hero",
                "voiceActive": True,
                "voiceLevel": 0.8,
                "gameUiConfig": {"voiceReactiveMotionMode": "cinematic"},
                "visualComfortMode": "static",
                "isLeaving": False,
            },
        ]
        script = textwrap.dedent(
            f"""
            import {{ buildVoiceReactiveMotionPose }} from {json.dumps(WEB_MODULE_PATH.as_uri())};
            const scenarios = {json.dumps(scenarios)};
            process.stdout.write(JSON.stringify(scenarios.map((item) => buildVoiceReactiveMotionPose(item))));
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
            build_native_voice_reactive_motion_pose(
                character_id=item["characterId"],
                active_character_id=item["activeCharacterId"],
                voice_active=item["voiceActive"],
                voice_level=item["voiceLevel"],
                game_ui_config=item["gameUiConfig"],
                visual_comfort_mode=item["visualComfortMode"],
                is_leaving=item["isLeaving"],
            )
            for item in scenarios
        ]
        self.assertEqual(web_poses, native_poses)

    def test_editor_web_export_and_native_runtime_are_all_wired(self) -> None:
        run_editor_source = (ROOT_DIR / "run_editor.py").read_text(encoding="utf-8")
        runtime_registry_source = (ROOT_DIR / "export_runtime_module_registry.py").read_text(encoding="utf-8")
        player_source = (ROOT_DIR / "export_player_template" / "player.js").read_text(encoding="utf-8")
        editor_source = (ROOT_DIR / "prototype_editor" / "app.js").read_text(encoding="utf-8")
        native_source = (ROOT_DIR / "native_runtime" / "runtime_player.py").read_text(encoding="utf-8")
        player_css = (ROOT_DIR / "export_player_template" / "player.css").read_text(encoding="utf-8")
        editor_css = (ROOT_DIR / "prototype_editor" / "styles.css").read_text(encoding="utf-8")

        self.assertIn('("VoiceReactiveMotion", "runtime_voice_reactive_motion.js")', runtime_registry_source)
        self.assertIn('NATIVE_RUNTIME_VOICE_REACTIVE_MOTION_NAME = "runtime_voice_reactive_motion.py"', run_editor_source)
        self.assertIn('from "./runtime_voice_reactive_motion.js"', player_source)
        self.assertIn("previewVoiceReactiveMotionController.start", editor_source)
        self.assertIn("self.voice_reactive_motion_controller = NativeVoiceReactiveMotionController()", native_source)
        self.assertIn("voice_motion_controller.start(", native_source)
        self.assertIn("render_native_characters(self, target)", native_source)
        self.assertIn("--voice-reactive-scale", player_css)
        self.assertIn("--voice-reactive-scale", editor_css)


if __name__ == "__main__":
    unittest.main()
