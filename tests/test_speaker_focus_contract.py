from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path

from native_runtime.runtime_speaker_focus import build_native_speaker_focus_pose


ROOT_DIR = Path(__file__).resolve().parents[1]
WEB_MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_speaker_focus.js"


class SpeakerFocusContractTests(unittest.TestCase):
    def test_web_and_native_pose_math_stays_aligned(self) -> None:
        scenarios = [
            {
                "characterId": "a",
                "activeCharacterId": "b",
                "visibleCharacterIds": ["a", "b"],
                "gameUiConfig": {"speakerFocusMode": "soft", "speakerFocusIntensity": 65},
                "visualComfortMode": "standard",
            },
            {
                "characterId": "b",
                "activeCharacterId": "b",
                "visibleCharacterIds": ["a", "b"],
                "gameUiConfig": {"speakerFocusMode": "cinematic", "speakerFocusIntensity": 80},
                "visualComfortMode": "gentle",
            },
            {
                "characterId": "a",
                "activeCharacterId": "a",
                "visibleCharacterIds": ["a"],
                "gameUiConfig": {"speakerFocusMode": "soft"},
                "visualComfortMode": "static",
            },
        ]
        script = textwrap.dedent(
            f"""
            import {{ buildSpeakerFocusPose }} from {json.dumps(WEB_MODULE_PATH.as_uri())};
            const scenarios = {json.dumps(scenarios)};
            process.stdout.write(JSON.stringify(scenarios.map((item) => buildSpeakerFocusPose(item))));
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
            build_native_speaker_focus_pose(
                character_id=item["characterId"],
                active_character_id=item["activeCharacterId"],
                visible_character_ids=item["visibleCharacterIds"],
                game_ui_config=item["gameUiConfig"],
                visual_comfort_mode=item["visualComfortMode"],
            )
            for item in scenarios
        ]
        self.assertEqual(web_poses, native_poses)

    def test_editor_export_and_native_runtime_are_all_wired(self) -> None:
        run_editor_source = (ROOT_DIR / "run_editor.py").read_text(encoding="utf-8")
        runtime_registry_source = (ROOT_DIR / "export_runtime_module_registry.py").read_text(encoding="utf-8")
        player_source = (ROOT_DIR / "export_player_template" / "player.js").read_text(encoding="utf-8")
        editor_source = (ROOT_DIR / "prototype_editor" / "app.js").read_text(encoding="utf-8")
        native_source = (ROOT_DIR / "native_runtime" / "runtime_player.py").read_text(encoding="utf-8")
        character_cards_source = (
            ROOT_DIR / "export_player_template" / "runtime_character_cards.js"
        ).read_text(encoding="utf-8")
        native_character_renderer_source = (
            ROOT_DIR / "native_runtime" / "runtime_character_renderer.py"
        ).read_text(encoding="utf-8")
        player_css = (ROOT_DIR / "export_player_template" / "player.css").read_text(encoding="utf-8")
        editor_css = (ROOT_DIR / "prototype_editor" / "styles.css").read_text(encoding="utf-8")

        self.assertIn('("SpeakerFocus", "runtime_speaker_focus.js")', runtime_registry_source)
        self.assertIn('NATIVE_RUNTIME_SPEAKER_FOCUS_NAME = "runtime_speaker_focus.py"', run_editor_source)
        self.assertIn('from "./runtime_character_cards.js"', player_source)
        self.assertIn('from "./runtime_speaker_focus.js"', character_cards_source)
        self.assertIn("buildSpeakerFocusPresentation", character_cards_source)
        self.assertIn("renderCharacterCards", editor_source)
        self.assertIn("render_native_characters(self, target)", native_source)
        self.assertIn("speaker_focus_controller.build_render_poses", native_character_renderer_source)
        self.assertIn("--speaker-focus-brightness", player_css)
        self.assertIn("--speaker-focus-brightness", editor_css)


if __name__ == "__main__":
    unittest.main()
