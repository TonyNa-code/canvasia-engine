from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EDITOR_DIR = ROOT_DIR / "prototype_editor"
INDEX_PATH = EDITOR_DIR / "index.html"
SCRIPT_SRC_PATTERN = re.compile(r"<script\b[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>", re.IGNORECASE)


class FrontendEntrypointModuleTests(unittest.TestCase):
    def test_editor_modules_are_loaded_before_app_entrypoint(self) -> None:
        html = INDEX_PATH.read_text(encoding="utf-8")
        scripts = SCRIPT_SRC_PATTERN.findall(html)

        required_scripts = [
            "./modules/story_block_catalog.js",
            "./modules/story_block_editors.js",
            "./modules/story_templates.js",
            "./modules/editor_common.js",
            "./modules/export_file_names.js",
            "./modules/variables.js",
            "./modules/project_runtime_settings.js",
            "./modules/project_settings.js",
            "./modules/dialog_box_readability.js",
            "./modules/validation_cache.js",
            "./modules/system_dialog.js",
            "./modules/ui_theme.js",
            "./modules/preview_save.js",
            "./modules/recent_workspace.js",
            "./modules/editor_filters.js",
            "./modules/dashboard_search_panel.js",
            "./modules/dashboard_primary_actions.js",
            "./modules/script_readability.js",
            "./modules/scene_pacing_advisor.js",
            "./modules/scene_polish.js",
            "./modules/scene_mood_recipes.js",
            "./modules/script_voice.js",
            "./modules/voice_match_review_panel.js",
            "./modules/voice_production_sheet.js",
            "./modules/screenplay_exporter.js",
            "./modules/renpy_exporter.js",
            "./modules/audio_timing_estimator.js",
            "./modules/director_cue_sheet.js",
            "./modules/script_importer.js",
            "./modules/route_analyzer.js",
            "./modules/route_testing_report.js",
            "./modules/scene_production_board.js",
            "./modules/preview_regression.js",
            "./modules/playtest_handoff_report.js",
            "./modules/choice_consequence_sheet.js",
            "./modules/variable_influence_sheet.js",
            "./modules/audio_cue_sheet.js",
            "./modules/project_polish.js",
            "./modules/project_polish_receipt_panel.js",
            "./modules/audio_cue_sheet_panel.js",
            "./modules/stage_direction_sheet.js",
            "./modules/presentation_timeline.js",
            "./modules/localization_coverage.js",
            "./modules/runtime_capability_matrix.js",
            "./modules/production_backlog.js",
            "./modules/release_candidate_manifest.js",
            "./modules/release_evidence_pack.js",
            "./modules/unlockable_content_manifest.js",
            "./modules/visual_effects.js",
            "./modules/particle_effects.js",
            "./modules/project_history.js",
            "./modules/project_history_panel.js",
            "./modules/asset_usage_map.js",
            "./modules/asset_catalog.js",
            "./modules/beginner_assets_guide.js",
            "./modules/beginner_character_guide.js",
            "./modules/asset_footprint.js",
            "./modules/runtime_preload_budget.js",
            "./modules/asset_dependency_sheet.js",
            "./modules/asset_rights_sheet.js",
            "./modules/openai_asset_generator.js",
            "./modules/beginner_tutorial.js",
            "./modules/project_center.js",
            "./modules/creative_assistant.js",
            "./modules/editor_mode.js",
            "./modules/release_version.js",
            "./modules/project_doctor.js",
            "./modules/project_doctor_panel.js",
            "./modules/project_milestones.js",
            "./modules/project_milestones_panel.js",
            "./modules/release_control.js",
            "./modules/release_control_panel.js",
            "./modules/typewriter.js",
            "./modules/command_palette.js",
            "./app.js",
        ]
        for script in required_scripts:
            self.assertIn(script, scripts)

        for module_script in required_scripts[:-1]:
            module_path = EDITOR_DIR / module_script.removeprefix("./")
            self.assertTrue(module_path.is_file(), f"Missing editor module: {module_path}")

        app_index = scripts.index("./app.js")
        for module_script in required_scripts[:-1]:
            self.assertLess(
                scripts.index(module_script),
                app_index,
                f"{module_script} must load before app.js",
            )


if __name__ == "__main__":
    unittest.main()
