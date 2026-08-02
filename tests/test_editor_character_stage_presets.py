from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import run_editor
from editor_character_stage_presets import (
    CHARACTER_STAGE_PRESET_LIMIT,
    normalize_character_stage_presets_for_migration,
    sanitize_character_stage,
    sanitize_character_stage_presets,
)


class EditorCharacterStagePresetTests(unittest.TestCase):
    def test_stage_values_and_duplicate_ids_are_normalized_like_the_editor(self) -> None:
        presets = sanitize_character_stage_presets(
            [
                {
                    "id": "stage_close",
                    "name": "  右侧   近景  ",
                    "position": "right",
                    "stage": {
                        "offsetX": 999,
                        "offsetY": -999,
                        "scale": 160.5,
                        "opacity": -4,
                        "layer": 99,
                        "flipX": "yes",
                    },
                },
                {"id": "stage_close", "name": "重复", "position": "invalid", "stage": {}},
            ]
        )

        self.assertEqual([preset["id"] for preset in presets], ["stage_close", "stage_close_02"])
        self.assertEqual(presets[0]["name"], "右侧 近景")
        self.assertEqual(presets[0]["position"], "right")
        self.assertEqual(
            presets[0]["stage"],
            {"offsetX": 60, "offsetY": -45, "scale": 161, "opacity": 0, "layer": 10, "flipX": True},
        )
        self.assertEqual(presets[1]["position"], "center")
        self.assertEqual(presets[1]["stage"], sanitize_character_stage({}))

    def test_migration_drops_invalid_payloads_and_limits_project_size(self) -> None:
        self.assertEqual(normalize_character_stage_presets_for_migration("bad"), [])
        self.assertEqual(normalize_character_stage_presets_for_migration([None]), [])
        oversized = [
            {"name": f"构图 {index}", "stage": {"scale": 100 + index}}
            for index in range(CHARACTER_STAGE_PRESET_LIMIT + 8)
        ]
        normalized = normalize_character_stage_presets_for_migration(oversized)
        self.assertEqual(len(normalized), CHARACTER_STAGE_PRESET_LIMIT)
        self.assertEqual(len({preset["id"] for preset in normalized}), CHARACTER_STAGE_PRESET_LIMIT)

    def test_project_settings_persist_and_remove_character_stage_presets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "project.json"
            project_path.write_text(
                json.dumps({"formatVersion": run_editor.PROJECT_FORMAT_VERSION, "projectId": "stage_test"}),
                encoding="utf-8",
            )
            with mock.patch.object(run_editor, "PROJECT_PATH", project_path):
                result = run_editor.save_project_settings(
                    character_stage_presets=[
                        {
                            "id": "stage_portrait",
                            "name": "人物特写",
                            "position": "left",
                            "stage": {"scale": 145, "offsetY": -8, "flipX": True},
                        }
                    ]
                )
                self.assertEqual(result["project"]["characterStagePresets"][0]["id"], "stage_portrait")
                self.assertEqual(result["project"]["characterStagePresets"][0]["stage"]["scale"], 145)

                run_editor.save_project_settings(character_stage_presets=[])
                saved = json.loads(project_path.read_text(encoding="utf-8"))
                self.assertNotIn("characterStagePresets", saved)

    def test_project_document_migration_preserves_valid_character_stage_presets(self) -> None:
        normalized = run_editor.normalize_project_document(
            {
                "projectId": "stage_test",
                "characterStagePresets": [
                    {"id": "stage_saved", "name": "保存构图", "position": "left", "stage": {"scale": 120}}
                ],
            },
            project_id="stage_test",
            discovered_chapter_ids=["chapter_01"],
            fallback_entry_scene_id="scene_01",
        )

        self.assertEqual(normalized["characterStagePresets"][0]["id"], "stage_saved")
        self.assertEqual(normalized["characterStagePresets"][0]["position"], "left")
        source = Path(run_editor.__file__).read_text(encoding="utf-8")
        self.assertIn('character_stage_presets=payload.get("characterStagePresets")', source)


if __name__ == "__main__":
    unittest.main()
