from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT_DIR / ".github" / "workflows" / "ci.yml"
EDITOR_INDEX_PATH = ROOT_DIR / "prototype_editor" / "index.html"
SCRIPT_SRC_PATTERN = re.compile(r"<script\b[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>", re.IGNORECASE)
TOP_LEVEL_KEY_PATTERN = re.compile(r"^([A-Za-z0-9_-]+):(?:\s|$)")


def _get_workflow_top_level_blocks() -> dict[str, str]:
    workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
    blocks: dict[str, list[str]] = {}
    current_key: str | None = None

    for line in workflow.splitlines():
        match = TOP_LEVEL_KEY_PATTERN.match(line)
        if match:
            current_key = match.group(1)
            if current_key in blocks:
                raise AssertionError(f"Duplicate top-level workflow key: {current_key}")
            blocks[current_key] = [line]
            continue

        if current_key is not None:
            blocks[current_key].append(line)

    return {key: "\n".join(lines) for key, lines in blocks.items()}


class CiWorkflowCoverageTests(unittest.TestCase):
    def test_ci_hardening_keys_are_top_level(self) -> None:
        blocks = _get_workflow_top_level_blocks()

        for key in ("on", "permissions", "concurrency", "jobs"):
            self.assertIn(key, blocks)

    def test_ci_uses_node_24_compatible_action_versions(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("actions/checkout@v7", workflow)
        self.assertIn("actions/setup-python@v6", workflow)
        self.assertIn("actions/setup-node@v7", workflow)
        self.assertNotIn("FORCE_JAVASCRIPT_ACTIONS_TO_NODE24", workflow)

    def test_ci_uses_least_privilege_permissions(self) -> None:
        blocks = _get_workflow_top_level_blocks()

        self.assertIn("contents: read", blocks["permissions"])
        self.assertNotIn("contents: write", blocks["permissions"])

    def test_ci_cancels_superseded_branch_runs(self) -> None:
        blocks = _get_workflow_top_level_blocks()

        self.assertIn("group: ${{ github.workflow }}-${{ github.ref }}", blocks["concurrency"])
        self.assertIn("cancel-in-progress: true", blocks["concurrency"])

    def test_ci_can_be_run_manually_before_release(self) -> None:
        blocks = _get_workflow_top_level_blocks()

        self.assertIn("workflow_dispatch:", blocks["on"])

    def test_ci_verify_job_has_timeout(self) -> None:
        blocks = _get_workflow_top_level_blocks()

        self.assertIn("verify:", blocks["jobs"])
        self.assertIn("timeout-minutes: 45", blocks["jobs"])

    def test_ci_workflow_coverage_test_is_run_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("tests/test_ci_workflow_coverage.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_ci_workflow_coverage.py' -v",
            workflow,
        )

    def test_local_verify_tool_is_run_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("tools/ci/local_verify.py", workflow)
        self.assertIn("tests/test_local_verify_tool.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_local_verify_tool.py' -v",
            workflow,
        )

    def test_github_status_tool_is_run_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("tools/ci/github_status.py", workflow)
        self.assertIn("tests/test_github_status_tool.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_github_status_tool.py' -v",
            workflow,
        )

    def test_project_health_tool_is_run_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("tools/ci/project_health.py", workflow)
        self.assertIn("tests/test_project_health_tool.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_project_health_tool.py' -v",
            workflow,
        )
        self.assertIn(
            "python tools/ci/project_health.py template_project --json-report verification_reports/project-health-template.json --markdown-report verification_reports/project-health-template.md",
            workflow,
        )

    def test_maintainability_check_tool_is_run_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("tools/ci/maintainability_check.py", workflow)
        self.assertIn("tests/test_maintainability_check_tool.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_maintainability_check_tool.py' -v",
            workflow,
        )
        self.assertIn(
            "python tools/ci/maintainability_check.py --json-report verification_reports/maintainability.json --markdown-report verification_reports/maintainability.md",
            workflow,
        )

    def test_native_runtime_rollback_module_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("native_runtime/runtime_rollback.py", workflow)
        self.assertIn("tests/test_native_runtime_rollback.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_native_runtime_rollback.py' -v",
            workflow,
        )

    def test_cross_runtime_text_history_modules_are_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("native_runtime/runtime_text_history.py", workflow)
        self.assertIn("native_runtime/runtime_text_history_overlay.py", workflow)
        self.assertIn("export_player_template/runtime_text_history.js", workflow)
        self.assertIn("tests/test_native_runtime_text_history.py", workflow)
        self.assertIn("tests/test_native_runtime_text_history_overlay.py", workflow)
        self.assertIn("tests/test_frontend_runtime_text_history_module.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_native_runtime_text_history.py' -v",
            workflow,
        )
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_native_runtime_text_history_overlay.py' -v",
            workflow,
        )
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_frontend_runtime_text_history_module.py' -v",
            workflow,
        )

    def test_cross_runtime_save_slot_protection_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("native_runtime/runtime_save_slots.py", workflow)
        self.assertIn("native_runtime/runtime_save_overlay.py", workflow)
        self.assertIn("export_player_template/runtime_save_slots.js", workflow)
        self.assertIn("tests/test_native_runtime_save_slots.py", workflow)
        self.assertIn("tests/test_native_runtime_save_overlay.py", workflow)
        self.assertIn("tests/test_frontend_runtime_save_slots_module.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_native_runtime_save_slots.py' -v",
            workflow,
        )
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_native_runtime_save_overlay.py' -v",
            workflow,
        )
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_frontend_runtime_save_slots_module.py' -v",
            workflow,
        )

    def test_export_runtime_module_registry_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("export_runtime_module_registry.py", workflow)
        self.assertIn("tests/test_export_runtime_module_registry.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_export_runtime_module_registry.py' -v",
            workflow,
        )

    def test_persistent_variable_contract_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("native_runtime/runtime_persistent_variables.py", workflow)
        self.assertIn("export_player_template/runtime_persistent_variables.js", workflow)
        self.assertIn("tests/test_persistent_variables_contract.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_persistent_variables_contract.py' -v",
            workflow,
        )

    def test_native_runtime_save_thumbnail_module_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("native_runtime/runtime_save_thumbnails.py", workflow)
        self.assertIn("tests/test_native_runtime_save_thumbnails.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_native_runtime_save_thumbnails.py' -v",
            workflow,
        )

    def test_particle_quality_contract_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        for path in (
            "prototype_editor/modules/particle_performance.js",
            "export_player_template/runtime_particle_quality.js",
            "export_player_template/runtime_particle_renderer.js",
            "native_runtime/runtime_particles.py",
            "tests/test_frontend_particle_performance_module.py",
            "tests/test_frontend_runtime_particle_quality_module.py",
            "tests/test_frontend_runtime_particle_renderer_module.py",
            "tests/test_native_runtime_particles.py",
            "tests/test_particle_quality_contract.py",
        ):
            self.assertIn(path, workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_particle_quality_contract.py' -v",
            workflow,
        )

    def test_mobile_reader_runtime_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("export_player_template/runtime_mobile_reader.js", workflow)
        self.assertIn("export_player_template/runtime_mobile_reader_ui.js", workflow)
        self.assertIn("tests/test_frontend_runtime_mobile_reader_module.py", workflow)
        self.assertIn("tests/test_frontend_runtime_mobile_reader_ui_module.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_frontend_runtime_mobile_reader_module.py' -v",
            workflow,
        )
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_frontend_runtime_mobile_reader_ui_module.py' -v",
            workflow,
        )

    def test_project_variable_governance_module_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("prototype_editor/modules/project_variable_governance.js", workflow)
        self.assertIn("tests/test_frontend_project_variable_governance_module.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_frontend_project_variable_governance_module.py' -v",
            workflow,
        )

    def test_native_runtime_credits_module_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("native_runtime/runtime_credits.py", workflow)
        self.assertIn("tests/test_native_runtime_credits.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_native_runtime_credits.py' -v",
            workflow,
        )

    def test_speaker_focus_contract_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("native_runtime/runtime_speaker_focus.py", workflow)
        self.assertIn("export_player_template/runtime_speaker_focus.js", workflow)
        self.assertIn("tests/test_native_runtime_speaker_focus.py", workflow)
        self.assertIn("tests/test_speaker_focus_contract.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_native_runtime_speaker_focus.py' -v",
            workflow,
        )
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_speaker_focus_contract.py' -v",
            workflow,
        )

    def test_dialogue_camera_contract_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("native_runtime/runtime_dialogue_camera.py", workflow)
        self.assertIn("export_player_template/runtime_dialogue_camera.js", workflow)
        self.assertIn("tests/test_native_runtime_dialogue_camera.py", workflow)
        self.assertIn("tests/test_dialogue_camera_contract.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_native_runtime_dialogue_camera.py' -v",
            workflow,
        )
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_dialogue_camera_contract.py' -v",
            workflow,
        )

    def test_voice_reactive_motion_contract_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("native_runtime/runtime_voice_reactive_motion.py", workflow)
        self.assertIn("native_runtime/runtime_character_renderer.py", workflow)
        self.assertIn("native_runtime/runtime_stage_renderer.py", workflow)
        self.assertIn("export_player_template/runtime_voice_reactive_motion.js", workflow)
        self.assertIn("tests/test_native_runtime_voice_reactive_motion.py", workflow)
        self.assertIn("tests/test_voice_reactive_motion_contract.py", workflow)
        self.assertIn("tests/test_native_runtime_stage_renderer.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_native_runtime_voice_reactive_motion.py' -v",
            workflow,
        )
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_voice_reactive_motion_contract.py' -v",
            workflow,
        )

    def test_native_surface_cache_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("native_runtime/runtime_surface_cache.py", workflow)
        self.assertIn("native_runtime/runtime_dialog_panel.py", workflow)
        self.assertIn("tests/test_native_runtime_surface_cache.py", workflow)
        self.assertIn("tests/test_native_runtime_dialog_panel.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_native_runtime_surface_cache.py' -v",
            workflow,
        )
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_native_runtime_dialog_panel.py' -v",
            workflow,
        )

    def test_timed_choice_contract_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("native_runtime/runtime_timed_choices.py", workflow)
        self.assertIn("export_player_template/runtime_timed_choices.js", workflow)
        self.assertIn("prototype_editor/modules/timed_choice_editor.js", workflow)
        self.assertIn("tests/test_native_runtime_timed_choices.py", workflow)
        self.assertIn("tests/test_timed_choice_contract.py", workflow)
        self.assertIn("tests/test_frontend_runtime_timed_choices_module.py", workflow)
        self.assertIn("tests/test_frontend_timed_choice_editor_module.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_native_runtime_timed_choices.py' -v",
            workflow,
        )
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_timed_choice_contract.py' -v",
            workflow,
        )

    def test_text_pacing_contract_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("native_runtime/runtime_text_pacing.py", workflow)
        self.assertIn("export_player_template/runtime_text_pacing.js", workflow)
        self.assertIn("prototype_editor/modules/text_pacing_editor.js", workflow)
        self.assertIn("tests/test_native_runtime_text_pacing.py", workflow)
        self.assertIn("tests/test_text_pacing_contract.py", workflow)
        self.assertIn("tests/test_frontend_runtime_text_pacing_module.py", workflow)
        self.assertIn("tests/test_frontend_text_pacing_editor_module.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_native_runtime_text_pacing.py' -v",
            workflow,
        )
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_text_pacing_contract.py' -v",
            workflow,
        )

    def test_rich_story_text_contract_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        for path in (
            "native_runtime/runtime_rich_text.py",
            "native_runtime/runtime_story_text.py",
            "native_runtime/runtime_rich_text_renderer.py",
            "export_player_template/runtime_rich_text.js",
            "export_player_template/runtime_story_text.js",
            "prototype_editor/modules/rich_text_editor.js",
            "tests/test_native_runtime_story_text.py",
            "tests/test_story_text_contract.py",
            "tests/test_frontend_runtime_story_text_module.py",
            "tests/test_frontend_rich_text_editor_module.py",
        ):
            self.assertIn(path, workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_story_text_contract.py' -v",
            workflow,
        )

    def test_music_transport_contract_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        for path in (
            "native_runtime/runtime_music_transport.py",
            "export_player_template/runtime_music_transport.js",
            "prototype_editor/modules/music_transport_editor.js",
            "tests/test_native_runtime_music_transport.py",
            "tests/test_music_transport_contract.py",
            "tests/test_frontend_runtime_music_transport_module.py",
            "tests/test_frontend_music_transport_editor_module.py",
        ):
            self.assertIn(path, workflow)
        for test_name in (
            "test_native_runtime_music_transport.py",
            "test_music_transport_contract.py",
            "test_frontend_runtime_music_transport_module.py",
            "test_frontend_music_transport_editor_module.py",
        ):
            self.assertIn(
                f"python -m unittest discover -s tests -p '{test_name}' -v",
                workflow,
            )

    def test_video_transport_contract_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        for path in (
            "native_runtime/runtime_video_transport.py",
            "export_player_template/runtime_video_transport.js",
            "prototype_editor/modules/video_transport_editor.js",
            "tests/test_native_runtime_video_transport.py",
            "tests/test_video_transport_contract.py",
            "tests/test_frontend_runtime_video_transport_module.py",
            "tests/test_frontend_video_transport_editor_module.py",
        ):
            self.assertIn(path, workflow)
        for test_name in (
            "test_native_runtime_video_transport.py",
            "test_video_transport_contract.py",
            "test_frontend_runtime_video_transport_module.py",
            "test_frontend_video_transport_editor_module.py",
        ):
            self.assertIn(
                f"python -m unittest discover -s tests -p '{test_name}' -v",
                workflow,
            )

    def test_sfx_transport_contract_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        for path in (
            "native_runtime/runtime_sfx_transport.py",
            "export_player_template/runtime_sfx_transport.js",
            "prototype_editor/modules/sfx_transport_editor.js",
            "tests/test_native_runtime_sfx_transport.py",
            "tests/test_sfx_transport_contract.py",
            "tests/test_frontend_runtime_sfx_transport_module.py",
            "tests/test_frontend_sfx_transport_editor_module.py",
        ):
            self.assertIn(path, workflow)
        for test_name in (
            "test_native_runtime_sfx_transport.py",
            "test_sfx_transport_contract.py",
            "test_frontend_runtime_sfx_transport_module.py",
            "test_frontend_sfx_transport_editor_module.py",
        ):
            self.assertIn(
                f"python -m unittest discover -s tests -p '{test_name}' -v",
                workflow,
            )

    def test_editor_project_presentation_settings_are_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("editor_project_presentation.py", workflow)
        self.assertIn("tests/test_editor_project_presentation.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_editor_project_presentation.py' -v",
            workflow,
        )

    def test_native_runtime_bundle_registry_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("native_runtime_bundle.py", workflow)
        self.assertIn("tests/test_native_runtime_bundle.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_native_runtime_bundle.py' -v",
            workflow,
        )

    def test_native_runtime_controller_input_module_is_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("native_runtime/runtime_input.py", workflow)
        self.assertIn("native_runtime/runtime_key_bindings.py", workflow)
        self.assertIn("tests/test_native_runtime_input.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_native_runtime_input.py' -v",
            workflow,
        )

    def test_public_release_surface_guard_is_run_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("tests/test_release_public_surface.py", workflow)
        self.assertIn(
            "python -m unittest discover -s tests -p 'test_release_public_surface.py' -v",
            workflow,
        )

    def test_editor_entrypoint_modules_are_syntax_checked_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        html = EDITOR_INDEX_PATH.read_text(encoding="utf-8")
        module_scripts = [
            script.removeprefix("./")
            for script in SCRIPT_SRC_PATTERN.findall(html)
            if script.startswith("./modules/")
        ]

        self.assertTrue(module_scripts, "Editor entrypoint should load at least one frontend module.")
        for module_script in module_scripts:
            self.assertIn(
                f"node --check prototype_editor/{module_script}",
                workflow,
                f"{module_script} is loaded before app.js but is missing from the CI frontend syntax check.",
            )

    def test_frontend_module_unit_tests_are_run_in_ci(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        frontend_test_files = sorted((ROOT_DIR / "tests").glob("test_frontend*.py"))

        self.assertTrue(frontend_test_files, "Frontend module tests should be present.")
        for test_file in frontend_test_files:
            test_name = test_file.name
            self.assertIn(
                f"python -m unittest discover -s tests -p '{test_name}' -v",
                workflow,
                f"{test_name} exists but is missing from the CI release tooling test step.",
            )


if __name__ == "__main__":
    unittest.main()
