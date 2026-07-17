from __future__ import annotations

import json
import io
import os
import tempfile
import unittest
import warnings
from contextlib import redirect_stdout
from fractions import Fraction
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

try:
    import pygame
except ModuleNotFoundError:  # pragma: no cover - CI installs pygame-ce for this suite.
    pygame = None

from native_runtime.runtime_player import (
    CRASH_FEEDBACK_JSON_NAME,
    CRASH_FEEDBACK_REPORT_NAME,
    NATIVE_VIDEO_EMBEDDED_BACKEND_ID,
    NATIVE_VIDEO_SYNC_BACKEND_ID,
    SYSTEM_MENU_ITEMS,
    VN_BASELINE_QUALITY_MARKDOWN_NAME,
    VN_BASELINE_QUALITY_REPORT_NAME,
    NativeRuntimePlayer,
    OpenCvEmbeddedVideoPlayback,
    PyAvSynchronizedVideoPlayback,
    build_native_runtime_control_guide,
    build_native_runtime_preload_report,
    build_acceptance_automated_checks,
    build_native_runtime_vn_baseline_quality_report,
    build_project_default_runtime_player_settings,
    build_runtime_preload_doctor_check,
    build_vn_baseline_quality_doctor_check,
    build_save_dialog_page_data,
    build_native_video_preview_probe_report,
    ellipsize_text,
    get_native_typewriter_step_delay_ms,
    get_native_runtime_help_action_shortcut_map,
    get_native_runtime_help_quick_actions,
    get_next_typewriter_index,
    get_runtime_screenshot_dir,
    get_typewriter_punctuation_pause_ms,
    load_project_archive_progress,
    load_opencv_video_frame_surface,
    main as runtime_player_main,
    render_native_runtime_preload_markdown,
    render_native_runtime_crash_feedback_markdown,
    render_native_runtime_vn_baseline_quality_markdown,
    write_native_runtime_crash_feedback_reports,
    write_native_runtime_vn_baseline_quality_reports,
    write_project_auto_resume,
    wrap_text,
)
from native_runtime.runtime_performance import (
    PERFORMANCE_BUDGET_MARKDOWN_NAME,
    PERFORMANCE_BUDGET_REPORT_NAME,
    build_native_runtime_performance_budget_report,
    render_native_runtime_performance_budget_markdown,
)
from native_runtime.runtime_player_settings import (
    DEFAULT_RUNTIME_PLAYER_SETTINGS,
    sanitize_runtime_player_settings,
)
from native_runtime.runtime_key_bindings import RUNTIME_KEY_BINDING_ACTIONS
from native_runtime.runtime_save_thumbnails import (
    build_save_thumbnail_status,
    get_save_thumbnail_path,
)
from native_runtime.runtime_storage import (
    build_runtime_crash_feedback_report,
    sanitize_archive_progress,
    write_runtime_crash_log,
)
from native_runtime.runtime_variables import (
    condition_operator_matches_variable_type,
    evaluate_runtime_operator,
)


UI_ASSET_IDS = [
    "title_background",
    "title_logo",
    "panel_frame",
    "button_frame",
    "button_hover_frame",
    "button_pressed_frame",
    "button_disabled_frame",
    "save_slot_frame",
    "system_panel_frame",
    "ui_overlay",
]


class NativeRuntimeTextHelperTests(unittest.TestCase):
    def test_native_runtime_control_guide_is_data_driven_and_cli_exportable(self) -> None:
        guide = build_native_runtime_control_guide()

        self.assertEqual(guide["runtime"], "native")
        self.assertIn("F2", guide["openHelp"])
        group_keys = [group["key"] for group in guide["groups"]]
        self.assertIn("reading", group_keys)
        self.assertIn("system", group_keys)
        self.assertIn("controller", group_keys)
        reading = next(group for group in guide["groups"] if group["key"] == "reading")
        system = next(group for group in guide["groups"] if group["key"] == "system")
        self.assertTrue(any("Enter" in control["keys"] and "Space" in control["keys"] for control in reading["controls"]))
        self.assertTrue(any("PageUp" in control["keys"] and control["label"] == "剧情回退" for control in reading["controls"]))
        self.assertTrue(any("F6" in control["keys"] and "F7" in control["keys"] for control in system["controls"]))
        self.assertIn("settings", [action["key"] for action in get_native_runtime_help_quick_actions()])
        self.assertIn("rollback", [action["key"] for action in get_native_runtime_help_quick_actions()])

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(runtime_player_main(["--describe-controls"]), 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["runtime"], "native")
        self.assertIn("quickActions", payload)

    def test_native_runtime_defaults_can_follow_project_playback_settings(self) -> None:
        defaults = build_project_default_runtime_player_settings(
            {
                "runtimeSettings": {
                    "defaultTextSpeed": "instant",
                    "defaultUiThemeMode": "dark",
                    "defaultBgmVolume": 64,
                    "defaultSfxVolume": 77,
                    "defaultVoiceVolume": 88,
                    "defaultVoiceDuckingRatio": 35,
                    "defaultVoiceEnabled": False,
                    "defaultVoiceDuckingEnabled": False,
                }
            }
        )

        self.assertEqual(defaults["textSpeed"], "instant")
        self.assertEqual(defaults["themeMode"], "dark")
        self.assertEqual(defaults["bgmVolume"], 64)
        self.assertEqual(defaults["sfxVolume"], 77)
        self.assertEqual(defaults["voiceVolume"], 0)
        self.assertEqual(defaults["voiceDuckingEnabled"], "off")
        self.assertEqual(defaults["voiceDuckingRatio"], 35)

    def test_native_runtime_settings_module_sanitizes_player_preferences(self) -> None:
        settings = sanitize_runtime_player_settings(
            {
                "themeMode": "mystery",
                "displayMode": "cinema",
                "visualComfort": "strobe",
                "textSpeed": "FAST",
                "language": "ja-jp",
                "textScalePercent": 999,
                "dialogBoxOpacityPercent": -20,
                "autoPlayDelayMs": "bad",
                "autoPlayWaitForVoice": "yes",
                "voiceDuckingEnabled": "off",
                "masterVolume": 120,
                "bgmVolume": -5,
                "sfxVolume": 66.4,
                "voiceVolume": "40",
                "voiceDuckingRatio": 5,
                "keyBindings": {"advance": "KeyB", "system": "Escape"},
            }
        )

        self.assertEqual(settings["themeMode"], DEFAULT_RUNTIME_PLAYER_SETTINGS["themeMode"])
        self.assertEqual(settings["displayMode"], DEFAULT_RUNTIME_PLAYER_SETTINGS["displayMode"])
        self.assertEqual(settings["visualComfort"], DEFAULT_RUNTIME_PLAYER_SETTINGS["visualComfort"])
        self.assertEqual(settings["textSpeed"], "fast")
        self.assertEqual(settings["language"], "ja-JP")
        self.assertEqual(settings["textScalePercent"], 125)
        self.assertEqual(settings["dialogBoxOpacityPercent"], 0)
        self.assertEqual(settings["autoPlayDelayMs"], DEFAULT_RUNTIME_PLAYER_SETTINGS["autoPlayDelayMs"])
        self.assertEqual(settings["autoPlayWaitForVoice"], DEFAULT_RUNTIME_PLAYER_SETTINGS["autoPlayWaitForVoice"])
        self.assertEqual(settings["voiceDuckingEnabled"], "off")
        self.assertEqual(settings["masterVolume"], 100)
        self.assertEqual(settings["bgmVolume"], 0)
        self.assertEqual(settings["sfxVolume"], 66)
        self.assertEqual(settings["voiceVolume"], 40)
        self.assertEqual(settings["voiceDuckingRatio"], 15)
        self.assertEqual(settings["keyBindings"]["advance"], "KeyB")
        self.assertEqual(settings["keyBindings"]["system"], "Tab")

    def test_native_runtime_storage_sanitizes_corrupted_archive_progress(self) -> None:
        progress = sanitize_archive_progress(
            {
                "chapterReplayUnlocked": ["chapter_a", "", "chapter_a", "chapter_b"],
                "readTextKeys": ["read_1", "read_1", None, "read_2"],
                "endingCompletionCount": "not-a-number",
                "endingLastCompletedAt": " 2026-04-24T00:00:00+08:00 ",
            }
        )

        self.assertEqual(progress["chapterReplayUnlocked"], ["chapter_a", "chapter_b"])
        self.assertEqual(progress["readTextKeys"], ["read_1", "read_2"])
        self.assertEqual(progress["endingCompletionCount"], 0)
        self.assertEqual(progress["endingLastCompletedAt"], "2026-04-24T00:00:00+08:00")

    def test_native_runtime_crash_feedback_report_redacts_home_path(self) -> None:
        original_home = os.environ.get("HOME")
        with tempfile.TemporaryDirectory() as temp_dir:
            home_dir = Path(temp_dir) / "home"
            bundle_dir = Path(temp_dir) / "bundle"
            home_dir.mkdir(parents=True)
            bundle_dir.mkdir(parents=True)
            os.environ["HOME"] = str(home_dir)
            game_data_path = bundle_dir / "game_data.json"
            try:
                try:
                    raise RuntimeError(f"simulated crash at {home_dir / 'secret' / 'asset.png'}")
                except RuntimeError as error:
                    write_runtime_crash_log(game_data_path, error, "unit_test")

                report = build_runtime_crash_feedback_report(game_data_path, include_logs=True)
                report_json = json.dumps(report, ensure_ascii=False)
                self.assertEqual(report["status"], "has_recent_crashes")
                self.assertEqual(report["summary"]["logCount"], 1)
                self.assertIn("RuntimeError", report["summary"]["latestError"])
                self.assertNotIn(str(home_dir), report_json)
                self.assertIn("~", report_json)

                markdown = render_native_runtime_crash_feedback_markdown(report)
                self.assertIn("# 原生 Runtime 崩溃反馈报告", markdown)
                self.assertIn("unit_test", markdown)
                self.assertNotIn(str(home_dir), markdown)

                template_payload = write_native_runtime_crash_feedback_reports(bundle_dir, include_logs=False)
                self.assertEqual(template_payload["status"], "template")
                self.assertFalse(template_payload["summary"]["includesLocalLogs"])
                self.assertTrue((bundle_dir / CRASH_FEEDBACK_REPORT_NAME).is_file())
                self.assertTrue((bundle_dir / CRASH_FEEDBACK_JSON_NAME).is_file())
                template_markdown = (bundle_dir / CRASH_FEEDBACK_REPORT_NAME).read_text(encoding="utf-8")
                self.assertIn("不包含作者本机日志", template_markdown)
                self.assertNotIn(str(bundle_dir), template_markdown)
            finally:
                if original_home is None:
                    os.environ.pop("HOME", None)
                else:
                    os.environ["HOME"] = original_home

    def test_native_runtime_variable_module_supports_string_condition_operators(self) -> None:
        self.assertTrue(condition_operator_matches_variable_type("string", "contains"))
        self.assertFalse(condition_operator_matches_variable_type("number", "contains"))
        self.assertTrue(evaluate_runtime_operator("good_common_end", "contains", "common"))
        self.assertTrue(evaluate_runtime_operator("good_common_end", "not_contains", "bad"))
        self.assertTrue(evaluate_runtime_operator("good_common_end", "starts_with", "good"))
        self.assertTrue(evaluate_runtime_operator("good_common_end", "ends_with", "end"))
        self.assertFalse(evaluate_runtime_operator("good_common_end", "contains", "bad"))

    def test_native_runtime_performance_budget_reports_missing_and_heavy_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir)
            bg_path = bundle_dir / "assets" / "backgrounds" / "large-bg.png"
            bgm_path = bundle_dir / "assets" / "bgm" / "theme.ogg"
            unused_path = bundle_dir / "assets" / "cg" / "unused.png"
            for path, content in [
                (bg_path, b"b" * 24),
                (bgm_path, b"m" * 6),
                (unused_path, b"u" * 5),
            ]:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
            game_data = {
                "project": {"projectId": "perf_budget_smoke", "title": "Performance Budget Smoke"},
                "assets": {
                    "assets": [
                        {
                            "id": "large_bg",
                            "type": "background",
                            "name": "Large BG",
                            "exportUrl": bg_path.relative_to(bundle_dir).as_posix(),
                        },
                        {
                            "id": "theme_bgm",
                            "type": "bgm",
                            "name": "Theme BGM",
                            "exportUrl": bgm_path.relative_to(bundle_dir).as_posix(),
                        },
                        {
                            "id": "missing_voice",
                            "type": "voice",
                            "name": "Missing Voice",
                            "exportUrl": "assets/voice/missing.ogg",
                        },
                        {
                            "id": "unused_cg",
                            "type": "cg",
                            "name": "Unused CG",
                            "exportUrl": unused_path.relative_to(bundle_dir).as_posix(),
                        },
                    ]
                },
                "characters": {"characters": []},
                "variables": {"variables": []},
                "chapters": [
                    {
                        "chapterId": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_1",
                                "name": "Scene 1",
                                "blocks": [
                                    {"id": "bg", "type": "background", "assetId": "large_bg"},
                                    {"id": "music", "type": "music_play", "assetId": "theme_bgm"},
                                    {
                                        "id": "line",
                                        "type": "dialogue",
                                        "text": "hello",
                                        "voiceAssetId": "missing_voice",
                                    },
                                ],
                            }
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_performance_budget_report(
                bundle_dir,
                budgets={
                    "totalAssetBudgetBytes": 16,
                    "referencedAssetBudgetBytes": 16,
                    "imageAssetBudgetBytes": 20,
                    "singleImageBudgetBytes": 12,
                },
            )
            markdown = render_native_runtime_performance_budget_markdown(report)
            json_stdout = io.StringIO()
            with redirect_stdout(json_stdout):
                self.assertEqual(runtime_player_main(["--performance-budget-json", str(bundle_dir)]), 1)
            md_stdout = io.StringIO()
            with redirect_stdout(md_stdout):
                self.assertEqual(runtime_player_main(["--performance-budget-report", str(bundle_dir)]), 1)
            write_stdout = io.StringIO()
            with redirect_stdout(write_stdout):
                self.assertEqual(runtime_player_main(["--write-performance-budget-reports", str(bundle_dir)]), 1)

            cli_payload = json.loads(json_stdout.getvalue())
            write_payload = json.loads(write_stdout.getvalue())
            self.assertEqual(report["status"], "needs_fix")
            self.assertEqual(report["summary"]["missingReferencedAssetCount"], 1)
            self.assertTrue(any(issue["code"] == "missing_referenced_assets" for issue in report["issues"]))
            self.assertTrue(any(issue["code"] == "totalAssets_over_budget" for issue in report["issues"]))
            self.assertIn("原生 Runtime 性能预算报告", markdown)
            self.assertIn("Missing Voice", markdown)
            self.assertEqual(cli_payload["status"], "needs_fix")
            self.assertIn("原生 Runtime 性能预算报告", md_stdout.getvalue())
            self.assertEqual(write_payload["markdown"], PERFORMANCE_BUDGET_MARKDOWN_NAME)
            self.assertEqual(write_payload["json"], PERFORMANCE_BUDGET_REPORT_NAME)
            self.assertTrue((bundle_dir / PERFORMANCE_BUDGET_MARKDOWN_NAME).is_file())
            self.assertTrue((bundle_dir / PERFORMANCE_BUDGET_REPORT_NAME).is_file())

    def test_runtime_preload_manifest_can_warm_assets_without_window(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir)
            image_path = bundle_dir / "assets" / "ui" / "title.png"
            sound_path = bundle_dir / "assets" / "sfx" / "click.wav"
            video_path = bundle_dir / "assets" / "video" / "op.mp4"
            for path in [image_path, sound_path, video_path]:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"asset")

            class FakeMixer:
                def get_init(self) -> bool:
                    return True

            class FakePygame:
                mixer = FakeMixer()

            player = NativeRuntimePlayer.__new__(NativeRuntimePlayer)
            player.bundle_dir = bundle_dir
            player.pygame = FakePygame()
            player.assets_by_id = {
                "title_ui": {
                    "id": "title_ui",
                    "type": "ui",
                    "exportUrl": image_path.relative_to(bundle_dir).as_posix(),
                },
                "click_sfx": {
                    "id": "click_sfx",
                    "type": "sfx",
                    "exportUrl": sound_path.relative_to(bundle_dir).as_posix(),
                },
                "opening_video": {
                    "id": "opening_video",
                    "type": "video",
                    "exportUrl": video_path.relative_to(bundle_dir).as_posix(),
                },
            }
            player.build_info = {
                "runtimePreloadManifest": {
                    "entries": [
                        {"assetId": "opening_video", "type": "video", "phase": "critical", "priority": 10, "preloadIndex": 3, "sizeBytes": 4096},
                        {"assetId": "click_sfx", "type": "sfx", "phase": "critical", "priority": 90, "preloadIndex": 2, "sizeBytes": 2048},
                        {"assetId": "title_ui", "type": "ui", "phase": "critical", "priority": 100, "preloadIndex": 1, "sizeBytes": 1024},
                    ]
                }
            }
            player.image_cache = {}
            player.sound_cache = {}
            player.runtime_preload_manifest = player.get_runtime_preload_manifest()

            def fake_load_image(asset_id: str | None):
                player.image_cache[asset_id] = f"image:{asset_id}"
                return player.image_cache[asset_id]

            def fake_load_sound(asset_id: str | None):
                player.sound_cache[asset_id] = f"sound:{asset_id}"
                return player.sound_cache[asset_id]

            player._load_image = fake_load_image
            player._load_sound = fake_load_sound

            status = player.preload_runtime_assets()

        self.assertEqual(status["status"], "ready")
        self.assertEqual(status["totalEntries"], 3)
        self.assertEqual(status["loadedImageEntries"], 1)
        self.assertEqual(status["loadedSoundEntries"], 1)
        self.assertEqual(status["readyStreamEntries"], 1)
        self.assertEqual(status["loadedEntries"], 3)
        self.assertEqual(status["totalBytes"], 7168)
        self.assertEqual(status["criticalBytes"], 7168)
        self.assertEqual(status["loadedBytes"], 7168)
        self.assertIn("首屏 7.0 KB", status["summaryText"])
        self.assertIn("合计 7.0 KB", player.get_runtime_preload_status_line())
        self.assertEqual(player.image_cache["title_ui"], "image:title_ui")
        self.assertEqual(player.sound_cache["click_sfx"], "sound:click_sfx")

    def test_runtime_preload_reuses_native_cached_assets_without_reloading(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir)

            class FakeMixer:
                def get_init(self) -> bool:
                    return True

            class FakePygame:
                mixer = FakeMixer()

            player = NativeRuntimePlayer.__new__(NativeRuntimePlayer)
            player.bundle_dir = bundle_dir
            player.pygame = FakePygame()
            player.assets_by_id = {
                "title_ui": {"id": "title_ui", "type": "ui", "exportUrl": "assets/ui/title.png"},
                "click_sfx": {"id": "click_sfx", "type": "sfx", "exportUrl": "assets/sfx/click.wav"},
            }
            player.build_info = {
                "runtimePreloadManifest": {
                    "entries": [
                        {"assetId": "title_ui", "type": "ui", "phase": "critical", "priority": 100, "preloadIndex": 1, "sizeBytes": 1024},
                        {"assetId": "click_sfx", "type": "sfx", "phase": "critical", "priority": 90, "preloadIndex": 2, "sizeBytes": 2048},
                    ]
                }
            }
            player.image_cache = {"title_ui": "image:cached"}
            player.sound_cache = {"click_sfx": "sound:cached"}
            player.runtime_preload_manifest = player.get_runtime_preload_manifest()
            player.runtime_scene_prefetched_asset_ids = set()
            player.current_bgm_asset_id = None

            def fail_load(_asset_id: str | None):
                raise AssertionError("cached preload entries should not reload assets")

            player._load_image = fail_load
            player._load_sound = fail_load

            status = player.preload_runtime_assets()

        self.assertEqual(status["status"], "ready")
        self.assertEqual(status["totalEntries"], 2)
        self.assertEqual(status["pendingEntries"], 0)
        self.assertEqual(status["loadedEntries"], 2)
        self.assertEqual(status["readyEntries"], 2)
        self.assertEqual(status["cachedEntries"], 2)
        self.assertEqual(status["loadedImageEntries"], 1)
        self.assertEqual(status["loadedSoundEntries"], 1)
        self.assertEqual(status["loadedBytes"], 3072)
        self.assertEqual(status["cachedAssetIds"], ["title_ui", "click_sfx"])
        self.assertIn("复用 2", status["summaryText"])
        self.assertIn("资源预热：2/2", player.get_runtime_preload_status_line())

    def test_runtime_preload_manifest_spreads_noncritical_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir)
            title_path = bundle_dir / "assets" / "ui" / "title.png"
            gallery_path = bundle_dir / "assets" / "ui" / "gallery.png"
            ending_path = bundle_dir / "assets" / "video" / "ending.mp4"
            for path in [title_path, gallery_path, ending_path]:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"asset")

            class FakeMixer:
                def get_init(self) -> bool:
                    return True

            class FakePygame:
                mixer = FakeMixer()

            player = NativeRuntimePlayer.__new__(NativeRuntimePlayer)
            player.bundle_dir = bundle_dir
            player.pygame = FakePygame()
            player.title_screen_active = False
            player.assets_by_id = {
                "title_ui": {"id": "title_ui", "type": "ui", "exportUrl": title_path.relative_to(bundle_dir).as_posix()},
                "gallery_ui": {"id": "gallery_ui", "type": "ui", "exportUrl": gallery_path.relative_to(bundle_dir).as_posix()},
                "ending_video": {"id": "ending_video", "type": "video", "exportUrl": ending_path.relative_to(bundle_dir).as_posix()},
            }
            player.build_info = {
                "runtimePreloadManifest": {
                    "entries": [
                        {"assetId": "title_ui", "type": "ui", "phase": "critical", "priority": 100, "preloadIndex": 1, "sizeBytes": 1024},
                        {"assetId": "gallery_ui", "type": "ui", "phase": "early", "priority": 72, "preloadIndex": 2, "sizeBytes": 2048},
                        {"assetId": "ending_video", "type": "video", "phase": "deferred", "priority": 38, "preloadIndex": 3, "sizeBytes": 4096},
                    ]
                }
            }
            player.image_cache = {}
            player.sound_cache = {}
            player.runtime_preload_manifest = player.get_runtime_preload_manifest()
            player.runtime_preload_pending_entries = []
            player.runtime_preload_finished_asset_ids = set()

            def fake_load_image(asset_id: str | None):
                player.image_cache[asset_id] = f"image:{asset_id}"
                return player.image_cache[asset_id]

            player._load_image = fake_load_image
            player._load_sound = lambda asset_id: f"sound:{asset_id}"

            status = player.preload_runtime_assets()
            self.assertEqual(status["status"], "warming")
            self.assertEqual(status["loadedEntries"], 1)
            self.assertEqual(status["pendingEntries"], 2)
            self.assertEqual(status["loadedBytes"], 1024)
            self.assertEqual(status["totalBytes"], 7168)
            self.assertIn("后台继续 2 项", status["summaryText"])
            self.assertIn("已准备 1.0 KB", status["summaryText"])
            self.assertIn("title_ui", player.image_cache)
            self.assertNotIn("gallery_ui", player.image_cache)

            player.update_runtime_preload_queue(max_entries=1)
            self.assertEqual(player.runtime_preload_status["status"], "warming")
            self.assertEqual(player.runtime_preload_status["loadedEntries"], 2)
            self.assertEqual(player.runtime_preload_status["pendingEntries"], 1)
            self.assertEqual(player.runtime_preload_status["loadedBytes"], 3072)
            self.assertIn("gallery_ui", player.image_cache)

            player.update_runtime_preload_queue(max_entries=1)

        self.assertEqual(player.runtime_preload_status["status"], "ready")
        self.assertEqual(player.runtime_preload_status["loadedEntries"], 3)
        self.assertEqual(player.runtime_preload_status["pendingEntries"], 0)
        self.assertEqual(player.runtime_preload_status["loadedBytes"], 7168)
        self.assertIn("合计 7.0 KB", player.runtime_preload_status["summaryText"])

    def test_runtime_preload_uses_project_performance_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir)
            asset_paths = {
                "title_ui": bundle_dir / "assets" / "ui" / "title.png",
                "gallery_ui": bundle_dir / "assets" / "ui" / "gallery.png",
                "album_ui": bundle_dir / "assets" / "ui" / "album.png",
                "menu_ui": bundle_dir / "assets" / "ui" / "menu.png",
                "ending_ui": bundle_dir / "assets" / "ui" / "ending.png",
            }
            for path in asset_paths.values():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"asset")

            class FakeMixer:
                def get_init(self) -> bool:
                    return True

            class FakePygame:
                mixer = FakeMixer()

            player = NativeRuntimePlayer.__new__(NativeRuntimePlayer)
            player.bundle_dir = bundle_dir
            player.pygame = FakePygame()
            player.title_screen_active = False
            player.project = {"runtimeSettings": {"performanceProfile": "high_quality_pc"}}
            player.assets_by_id = {
                asset_id: {
                    "id": asset_id,
                    "type": "ui",
                    "exportUrl": path.relative_to(bundle_dir).as_posix(),
                }
                for asset_id, path in asset_paths.items()
            }
            player.build_info = {
                "runtimePreloadManifest": {
                    "entries": [
                        {"assetId": "title_ui", "type": "ui", "phase": "critical", "priority": 100, "preloadIndex": 1, "sizeBytes": 1024},
                        {"assetId": "gallery_ui", "type": "ui", "phase": "early", "priority": 80, "preloadIndex": 2, "sizeBytes": 2048},
                        {"assetId": "album_ui", "type": "ui", "phase": "deferred", "priority": 60, "preloadIndex": 3, "sizeBytes": 4096},
                        {"assetId": "menu_ui", "type": "ui", "phase": "deferred", "priority": 50, "preloadIndex": 4, "sizeBytes": 8192},
                        {"assetId": "ending_ui", "type": "ui", "phase": "deferred", "priority": 40, "preloadIndex": 5, "sizeBytes": 16384},
                    ]
                }
            }
            player.image_cache = {}
            player.sound_cache = {}
            player.runtime_preload_manifest = player.get_runtime_preload_manifest()
            player.runtime_preload_pending_entries = []
            player.runtime_preload_finished_asset_ids = set()

            def fake_load_image(asset_id: str | None):
                player.image_cache[asset_id] = f"image:{asset_id}"
                return player.image_cache[asset_id]

            player._load_image = fake_load_image
            player._load_sound = lambda asset_id: f"sound:{asset_id}"

            status = player.preload_runtime_assets()
            self.assertEqual(status["performanceProfile"], "high_quality_pc")
            self.assertEqual(status["performanceProfileLabel"], "高画质 PC")
            self.assertEqual(status["frameBudget"], 3)
            self.assertEqual(status["status"], "warming")
            self.assertEqual(status["loadedEntries"], 2)
            self.assertEqual(status["pendingEntries"], 3)
            self.assertEqual(status["criticalBytes"], 3072)
            self.assertIn("档位 高画质 PC", status["summaryText"])
            self.assertIn("gallery_ui", player.image_cache)
            self.assertNotIn("album_ui", player.image_cache)

            player.update_runtime_preload_queue()

        self.assertEqual(player.runtime_preload_status["status"], "ready")
        self.assertEqual(player.runtime_preload_status["loadedEntries"], 5)
        self.assertEqual(player.runtime_preload_status["pendingEntries"], 0)
        self.assertIn("album_ui", player.image_cache)
        self.assertIn("menu_ui", player.image_cache)
        self.assertIn("ending_ui", player.image_cache)

    def test_runtime_preload_report_and_doctor_flag_missing_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir)
            title_path = bundle_dir / "assets" / "ui" / "title.png"
            title_path.parent.mkdir(parents=True, exist_ok=True)
            title_path.write_bytes(b"asset")
            game_data = {
                "project": {"projectId": "preload_report_smoke", "title": "Preload Report Smoke"},
                "assets": {
                    "assets": [
                        {
                            "id": "title_ui",
                            "type": "ui",
                            "name": "Title UI",
                            "exportUrl": title_path.relative_to(bundle_dir).as_posix(),
                        }
                    ]
                },
                "characters": {"characters": []},
                "chapters": [],
                "buildInfo": {
                    "runtimePreloadManifest": {
                        "entries": [
                            {"assetId": "title_ui", "type": "ui", "phase": "critical", "priority": 100},
                            {"assetId": "missing_sfx", "type": "sfx", "phase": "early", "priority": 72},
                        ]
                    }
                },
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_preload_report(bundle_dir)
            doctor_check = build_runtime_preload_doctor_check(bundle_dir)
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(runtime_player_main(["--describe-runtime-preload", str(bundle_dir)]), 1)
            cli_payload = json.loads(stdout.getvalue())
            markdown = render_native_runtime_preload_markdown(report)
            markdown_stdout = io.StringIO()
            with redirect_stdout(markdown_stdout):
                self.assertEqual(runtime_player_main(["--describe-runtime-preload-markdown", str(bundle_dir)]), 1)

        self.assertEqual(report["status"], "needs_fix")
        self.assertEqual(report["summary"]["totalEntries"], 2)
        self.assertEqual(report["summary"]["criticalEntries"], 1)
        self.assertEqual(report["summary"]["missingFileEntries"], 1)
        self.assertEqual(report["summary"]["sizeBudget"]["totalBytes"], 5)
        self.assertEqual(report["summary"]["profileAdvice"]["selectedProfile"], "standard")
        self.assertEqual(report["entries"][0]["sizeBytes"], 5)
        self.assertEqual(report["missingEntries"][0]["assetId"], "missing_sfx")
        self.assertEqual(doctor_check["id"], "runtime_preload")
        self.assertEqual(doctor_check["status"], "fail")
        self.assertEqual(cli_payload["status"], "needs_fix")
        self.assertEqual(cli_payload["missingEntries"][0]["assetId"], "missing_sfx")
        self.assertIn("Runtime 资源预热报告", markdown)
        self.assertIn("体积预算", markdown)
        self.assertIn("档位建议", markdown)
        self.assertIn("missing_sfx", markdown)
        self.assertIn("Runtime 资源预热报告", markdown_stdout.getvalue())
        self.assertIn("missing_sfx", markdown_stdout.getvalue())

    def test_runtime_preload_report_warns_on_large_critical_budget(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir)
            title_path = bundle_dir / "assets" / "ui" / "oversized-title.png"
            title_path.parent.mkdir(parents=True, exist_ok=True)
            with title_path.open("wb") as file_handle:
                file_handle.truncate(100 * 1024 * 1024)
            game_data = {
                "project": {"projectId": "preload_budget_smoke", "title": "Preload Budget Smoke"},
                "assets": {
                    "assets": [
                        {
                            "id": "oversized_title",
                            "type": "ui",
                            "name": "Oversized Title",
                            "exportUrl": title_path.relative_to(bundle_dir).as_posix(),
                        }
                    ]
                },
                "characters": {"characters": []},
                "chapters": [],
                "buildInfo": {
                    "runtimePreloadManifest": {
                        "entries": [
                            {"assetId": "oversized_title", "type": "ui", "phase": "critical", "priority": 100},
                        ]
                    }
                },
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_preload_report(bundle_dir)
            doctor_check = build_runtime_preload_doctor_check(bundle_dir)

        size_budget = report["summary"]["sizeBudget"]
        profile_advice = report["summary"]["profileAdvice"]
        self.assertEqual(report["status"], "needs_review")
        self.assertTrue(size_budget["criticalOverBudget"])
        self.assertEqual(size_budget["criticalBytes"], 100 * 1024 * 1024)
        self.assertEqual(size_budget["largestEntries"][0]["assetId"], "oversized_title")
        self.assertEqual(profile_advice["status"], "should_raise")
        self.assertEqual(profile_advice["recommendedProfile"], "high_quality_pc")
        self.assertEqual(doctor_check["status"], "warn")
        self.assertIn("critical", doctor_check["message"])

    def test_native_runtime_voice_ducking_state_restores_bgm_after_voice_finishes(self) -> None:
        class FakeMusic:
            def __init__(self) -> None:
                self.volume = None

            def set_volume(self, volume: float) -> None:
                self.volume = volume

        class FakeMixer:
            def __init__(self) -> None:
                self.music = FakeMusic()

            def get_init(self) -> bool:
                return True

        class FakePygame:
            def __init__(self) -> None:
                self.mixer = FakeMixer()

        class FakeChannel:
            def __init__(self, busy: bool) -> None:
                self.busy = busy

            def get_busy(self) -> bool:
                return self.busy

        player = NativeRuntimePlayer.__new__(NativeRuntimePlayer)
        player.pygame = FakePygame()
        player.runtime_settings = {
            "masterVolume": 100,
            "bgmVolume": 80,
            "voiceDuckingEnabled": "on",
            "voiceDuckingRatio": 30,
        }
        player.current_bgm_volume_percent = 100
        player.current_voice_volume_percent = 100
        player.current_voice_channel = FakeChannel(True)
        player.voice_playback_active = False

        player.update_voice_playback_state()
        self.assertAlmostEqual(player.pygame.mixer.music.volume, 0.24)
        self.assertTrue(player.voice_playback_active)

        player.current_voice_channel.busy = False
        player.update_voice_playback_state()
        self.assertAlmostEqual(player.pygame.mixer.music.volume, 0.8)
        self.assertFalse(player.voice_playback_active)
        self.assertIsNone(player.current_voice_channel)

    @unittest.skipIf(pygame is None, "pygame-ce is not installed")
    def test_native_runtime_help_shortcut_map_preserves_alt_load_key(self) -> None:
        shortcut_map = get_native_runtime_help_action_shortcut_map(pygame)

        self.assertEqual(shortcut_map[pygame.K_s], "settings")
        self.assertEqual(shortcut_map[pygame.K_F7], "load")
        self.assertEqual(shortcut_map[pygame.K_l], "load")
        self.assertEqual(shortcut_map[pygame.K_m], "system")

    def test_typewriter_groups_latin_text_and_pauses_after_punctuation(self) -> None:
        text = "Hello, 世界！"
        family_text = "A👨‍👩‍👧‍👦B"
        flag_text = "A🇯🇵B"
        skin_tone_text = "A👍🏽B"
        accented_text = "e\u0301!"

        self.assertEqual(get_next_typewriter_index(text, 0), 3)
        self.assertEqual(get_next_typewriter_index(text, 3), 5)
        self.assertEqual(get_next_typewriter_index(family_text, 1), family_text.index("B"))
        self.assertEqual(get_next_typewriter_index(flag_text, 1), flag_text.index("B"))
        self.assertEqual(get_next_typewriter_index(skin_tone_text, 1), skin_tone_text.index("B"))
        self.assertEqual(get_next_typewriter_index(accented_text, 0), accented_text.index("!"))
        opening_sentence = "“再见。”"
        self.assertEqual(get_next_typewriter_index(opening_sentence, 0), opening_sentence.index("见"))
        opening_word = '"Hi" there'
        self.assertEqual(get_next_typewriter_index(opening_word, 0), opening_word.index("i"))
        quoted_sentence = "“再见。”下一句"
        self.assertEqual(
            get_next_typewriter_index(quoted_sentence, quoted_sentence.index("。")),
            quoted_sentence.index("下"),
        )
        quoted_word = '"Hi" there'
        self.assertEqual(get_next_typewriter_index(quoted_word, quoted_word.index("i")), quoted_word.index(" ") + 1)
        self.assertEqual(get_typewriter_punctuation_pause_ms("Hello,"), 140)
        self.assertEqual(get_typewriter_punctuation_pause_ms("世界！"), 260)
        self.assertEqual(get_typewriter_punctuation_pause_ms("“再见。”"), 260)
        self.assertEqual(get_typewriter_punctuation_pause_ms("嗯，"), 140)
        self.assertEqual(get_typewriter_punctuation_pause_ms("Hello."), 260)
        self.assertEqual(get_typewriter_punctuation_pause_ms("Wait..."), 220)
        self.assertEqual(get_typewriter_punctuation_pause_ms('"Wait..."'), 220)
        self.assertEqual(get_typewriter_punctuation_pause_ms("3.", "3.14"), 0)
        self.assertEqual(get_typewriter_punctuation_pause_ms("v1.", "v1.2"), 0)
        self.assertEqual(get_typewriter_punctuation_pause_ms("example.", "example.com"), 0)
        self.assertEqual(get_typewriter_punctuation_pause_ms("Chapter 1."), 260)
        self.assertEqual(get_typewriter_punctuation_pause_ms("Mr.", "Mr. Smith"), 0)
        self.assertEqual(get_typewriter_punctuation_pause_ms("e.g.", "e.g. this"), 0)
        self.assertEqual(get_typewriter_punctuation_pause_ms("Dr."), 260)
        self.assertGreater(
            get_native_typewriter_step_delay_ms("normal", "Hello,"),
            get_native_typewriter_step_delay_ms("normal", "Hello"),
        )
        self.assertEqual(get_native_typewriter_step_delay_ms("instant", "世界！"), 0)

    def test_vn_baseline_quality_report_flags_native_release_polish_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            background_path = bundle_dir / "assets" / "backgrounds" / "classroom.png"
            background_path.parent.mkdir(parents=True, exist_ok=True)
            background_path.write_bytes(b"fake-background")
            model_path = bundle_dir / "assets" / "models" / "heroine.glb"
            model_path.parent.mkdir(parents=True, exist_ok=True)
            model_path.write_bytes(b"fake-model")
            game_data = {
                "project": {
                    "projectId": "native_vn_quality_smoke",
                    "title": "Native VN Quality Smoke",
                    "entrySceneId": "scene_start",
                    "resolution": {"width": 1280, "height": 720},
                },
                "assets": {
                    "assets": [
                        {
                            "id": "classroom_bg",
                            "type": "background",
                            "name": "Classroom",
                            "exportUrl": background_path.relative_to(bundle_dir).as_posix(),
                            "tags": [],
                        },
                        {
                            "id": "heroine_model",
                            "type": "model3d",
                            "name": "Heroine 3D Model",
                            "exportUrl": model_path.relative_to(bundle_dir).as_posix(),
                            "tags": ["3D"],
                        },
                    ]
                },
                "characters": {
                    "characters": [
                        {
                            "id": "heroine",
                            "displayName": "Heroine",
                            "presentation": {
                                "mode": "model3d",
                                "fallbackSpriteAssetId": "",
                                "model3d": {"modelAssetId": "heroine_model"},
                            },
                            "expressions": [{"id": "default", "spriteAssetId": ""}],
                        }
                    ]
                },
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_start",
                                "name": "Opening",
                                "blocks": [
                                    {"id": "bg", "type": "background", "assetId": "classroom_bg"},
                                    {"id": "line", "type": "dialogue", "speakerId": "heroine", "text": "Welcome."},
                                    {
                                        "id": "choice",
                                        "type": "choice",
                                        "options": [{"text": "Continue", "gotoSceneId": ""}],
                                    },
                                ],
                            }
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["status"], "needs_fix")
            self.assertEqual(report["metrics"]["storySceneCount"], 1)
            self.assertEqual(report["metrics"]["choiceCount"], 1)
            self.assertEqual(report["metrics"]["choiceOptionCount"], 1)
            self.assertEqual(report["metrics"]["emptyChoiceOptionCount"], 0)
            self.assertEqual(report["metrics"]["scenesWithBackground"], 1)
            self.assertEqual(report["metrics"]["backgroundBlockCount"], 1)
            self.assertEqual(report["metrics"]["missingBackgroundAssetCount"], 0)
            self.assertEqual(report["metrics"]["sfxPlayCount"], 0)
            self.assertEqual(report["metrics"]["missingSfxAssetCount"], 0)
            self.assertEqual(report["metrics"]["videoAssetCount"], 0)
            self.assertEqual(report["metrics"]["videoPlayCount"], 0)
            self.assertEqual(report["metrics"]["missingVideoAssetCount"], 0)
            self.assertEqual(report["metrics"]["creditsRollCount"], 0)
            self.assertEqual(report["metrics"]["creditsLineCount"], 0)
            self.assertEqual(report["metrics"]["emptyCreditsRollCount"], 0)
            self.assertEqual(report["metrics"]["shortCreditsRollCount"], 0)
            self.assertEqual(report["metrics"]["musicPlayCount"], 0)
            self.assertEqual(report["metrics"]["musicFadeInCount"], 0)
            self.assertEqual(report["metrics"]["voiceBoundLineCount"], 0)
            self.assertEqual(report["metrics"]["missingVoiceAssetCount"], 0)
            self.assertTrue(report["metrics"]["entrySceneExists"])
            self.assertEqual(report["metrics"]["routeTargetMissingCount"], 0)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("character_fallback_sprite", issue_codes)
            self.assertIn("bgm_plan", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("原生 Runtime VN 基础质感报告", markdown)
            self.assertIn("角色立绘覆盖", markdown)
            self.assertIn("空白 / 超长 / 重复选项", markdown)
            self.assertIn("音效点 / 缺失音效", markdown)
            self.assertIn("视频素材 / 播放卡 / 缺失视频", markdown)
            self.assertIn("结局 / 片尾字幕 / 字幕行", markdown)
            self.assertIn("BGM 淡入 / 淡出", markdown)
            self.assertIn("背景转场 / 背景卡", markdown)
            self.assertIn("语音覆盖", markdown)
            self.assertIn("入口场景有效", markdown)

            written = write_native_runtime_vn_baseline_quality_reports(bundle_dir)
            self.assertEqual(written["status"], "needs_fix")
            self.assertTrue((bundle_dir / VN_BASELINE_QUALITY_REPORT_NAME).is_file())
            self.assertTrue((bundle_dir / VN_BASELINE_QUALITY_MARKDOWN_NAME).is_file())

            doctor_check = build_vn_baseline_quality_doctor_check(bundle_dir)
            self.assertEqual(doctor_check["id"], "vn_baseline_quality")
            self.assertEqual(doctor_check["status"], "fail")
            self.assertIn("视觉小说基础质感", doctor_check["message"])

            acceptance_checks = build_acceptance_automated_checks(
                {
                    "releaseCheck": {"status": "pass", "summary": {}},
                    "releaseCandidate": {"status": "preview_ready", "summary": {}, "videoStrategy": {}},
                    "qualityGate": {"status": "blocked", "summary": "VN baseline has fix items."},
                    "asset3d": {"status": "no_3d_assets", "summaryLine": "none"},
                    "vnBaselineQuality": {
                        "status": report["status"],
                        "summary": report["summary"],
                    },
                },
                {"status": "pass", "summary": {}},
            )
            vn_check = next((check for check in acceptance_checks if check["id"] == "vn_baseline_quality"), None)
            self.assertIsNotNone(vn_check)
            self.assertEqual(vn_check["status"], "needs_fix")
            self.assertEqual(vn_check["command"], "python3 runtime_player.py --vn-baseline-quality-report .")

    def test_vn_baseline_quality_report_flags_duplicate_scene_and_block_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            game_data = {
                "project": {
                    "projectId": "native_duplicate_id_quality_smoke",
                    "title": "Native Duplicate ID Quality Smoke",
                    "entrySceneId": "scene_dup",
                },
                "assets": {"assets": []},
                "characters": {"characters": []},
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_dup",
                                "name": "Opening",
                                "blocks": [
                                    {"id": "line_dup", "type": "narration", "text": "First line."},
                                    {"id": "line_dup", "type": "narration", "text": "Second line."},
                                ],
                            },
                            {
                                "id": "scene_dup",
                                "name": "Copied Opening",
                                "blocks": [
                                    {"id": "line_other", "type": "narration", "text": "Copied scene."},
                                ],
                            },
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["status"], "needs_fix")
            self.assertEqual(report["metrics"]["duplicateSceneIdCount"], 1)
            self.assertEqual(report["metrics"]["duplicateBlockIdCount"], 1)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("duplicate_scene_id", issue_codes)
            self.assertIn("duplicate_block_id", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("重复场景 / 重复卡片 ID", markdown)
            self.assertIn("场景 ID 存在重复", markdown)
            self.assertIn("同一场景内存在重复卡片 ID", markdown)

    def test_vn_baseline_quality_report_flags_chapter_structure_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            game_data = {
                "project": {
                    "projectId": "native_chapter_structure_quality_smoke",
                    "title": "Native Chapter Structure Quality Smoke",
                    "entrySceneId": "missing_entry",
                },
                "assets": {"assets": []},
                "characters": {"characters": []},
                "chapters": [
                    {
                        "id": "chapter_dup",
                        "name": "Chapter A",
                        "scenes": [
                            {
                                "id": "scene_a",
                                "name": "Scene A",
                                "blocks": [{"id": "line_a", "type": "narration", "text": "A."}],
                            }
                        ],
                    },
                    {"id": "chapter_dup", "name": "Empty Copy", "scenes": []},
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["status"], "needs_fix")
            self.assertEqual(report["metrics"]["chapterCount"], 2)
            self.assertEqual(report["metrics"]["duplicateChapterIdCount"], 1)
            self.assertEqual(report["metrics"]["emptyChapterCount"], 1)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("duplicate_chapter_id", issue_codes)
            self.assertIn("empty_chapter", issue_codes)
            self.assertIn("entry_scene_missing", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("章节数 / 空章节", markdown)
            self.assertIn("重复章节 ID", markdown)
            self.assertIn("章节 ID 存在重复", markdown)
            self.assertIn("存在没有场景的空章节", markdown)

    def test_vn_baseline_quality_report_flags_missing_scene_and_block_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            game_data = {
                "project": {
                    "projectId": "native_missing_id_quality_smoke",
                    "title": "Native Missing ID Quality Smoke",
                    "entrySceneId": "scene_ok",
                },
                "assets": {"assets": []},
                "characters": {"characters": []},
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "",
                                "name": "Anonymous Scene",
                                "blocks": [{"type": "narration", "text": "Anonymous."}],
                            },
                            {
                                "id": "scene_ok",
                                "name": "Stable Scene",
                                "blocks": [
                                    {"id": "line_ok", "type": "narration", "text": "Stable."},
                                    {"type": "dialogue", "speakerId": "", "text": "Missing card id."},
                                ],
                            },
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["status"], "needs_fix")
            self.assertEqual(report["metrics"]["missingSceneIdCount"], 1)
            self.assertEqual(report["metrics"]["missingBlockIdCount"], 2)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("missing_scene_id", issue_codes)
            self.assertIn("missing_block_id", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("缺失场景 ID", markdown)
            self.assertIn("缺失卡片 ID", markdown)
            self.assertIn("存在没有 ID 的场景", markdown)
            self.assertIn("存在没有 ID 的剧情卡片", markdown)

    def test_vn_baseline_quality_report_flags_duplicate_resource_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            sprite_path = bundle_dir / "assets" / "characters" / "heroine.png"
            sprite_path.parent.mkdir(parents=True, exist_ok=True)
            sprite_path.write_bytes(b"fake-sprite")
            game_data = {
                "project": {
                    "projectId": "native_duplicate_resource_quality_smoke",
                    "title": "Native Duplicate Resource Quality Smoke",
                    "entrySceneId": "scene_start",
                },
                "assets": {
                    "assets": [
                        {
                            "id": "sprite_dup",
                            "type": "character",
                            "name": "Heroine A",
                            "exportUrl": sprite_path.relative_to(bundle_dir).as_posix(),
                        },
                        {
                            "id": "sprite_dup",
                            "type": "character",
                            "name": "Heroine B",
                            "exportUrl": sprite_path.relative_to(bundle_dir).as_posix(),
                        },
                    ]
                },
                "characters": {
                    "characters": [
                        {
                            "id": "heroine",
                            "displayName": "Heroine A",
                            "defaultSpriteAssetId": "sprite_dup",
                            "expressions": [
                                {"id": "smile", "spriteAssetId": "sprite_dup"},
                                {"id": "smile", "spriteAssetId": "sprite_dup"},
                            ],
                        },
                        {
                            "id": "heroine",
                            "displayName": "Heroine B",
                            "defaultSpriteAssetId": "sprite_dup",
                            "expressions": [{"id": "default", "spriteAssetId": "sprite_dup"}],
                        },
                    ]
                },
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_start",
                                "name": "Opening",
                                "blocks": [
                                    {
                                        "id": "line_start",
                                        "type": "dialogue",
                                        "speakerId": "heroine",
                                        "expressionId": "smile",
                                        "text": "Hello.",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["status"], "needs_fix")
            self.assertEqual(report["metrics"]["duplicateAssetIdCount"], 1)
            self.assertEqual(report["metrics"]["duplicateCharacterIdCount"], 1)
            self.assertEqual(report["metrics"]["duplicateExpressionIdCount"], 1)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("duplicate_asset_id", issue_codes)
            self.assertIn("duplicate_character_id", issue_codes)
            self.assertIn("duplicate_expression_id", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("重复素材 / 角色 / 表情 ID", markdown)
            self.assertIn("素材 ID 存在重复", markdown)
            self.assertIn("角色 ID 存在重复", markdown)
            self.assertIn("同一角色内存在重复表情 ID", markdown)

    def test_vn_baseline_quality_report_flags_bgm_continuity_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            game_data = {
                "project": {
                    "projectId": "native_bgm_quality_smoke",
                    "title": "Native BGM Quality Smoke",
                    "entrySceneId": "scene_a",
                },
                "assets": {"assets": []},
                "characters": {"characters": []},
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_a",
                                "name": "A",
                                "blocks": [
                                    {"id": "music_a", "type": "music_play", "assetId": "bgm_a"},
                                    {"id": "line_a", "type": "narration", "text": "First cue."},
                                ],
                            },
                            {
                                "id": "scene_b",
                                "name": "B",
                                "blocks": [
                                    {"id": "music_b", "type": "music_play", "assetId": "bgm_b"},
                                    {"id": "line_b", "type": "narration", "text": "Second cue."},
                                ],
                            },
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["metrics"]["musicPlayCount"], 2)
            self.assertEqual(report["metrics"]["musicScopedCount"], 0)
            self.assertEqual(report["metrics"]["musicFadeInCount"], 0)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("bgm_scope", issue_codes)
            self.assertIn("bgm_fade_in", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("多首 BGM 缺少明确范围", markdown)
            self.assertIn("BGM 播放 / 停止", markdown)

    def test_vn_baseline_quality_report_flags_bgm_after_block_target_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            game_data = {
                "project": {
                    "projectId": "native_bgm_after_block_quality_smoke",
                    "title": "Native BGM After Block Quality Smoke",
                    "entrySceneId": "scene_bgm_scope",
                },
                "assets": {"assets": []},
                "characters": {"characters": []},
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_bgm_scope",
                                "name": "BGM Scope",
                                "blocks": [
                                    {"id": "line_before", "type": "narration", "text": "Before music."},
                                    {
                                        "id": "music_missing_end",
                                        "type": "music_play",
                                        "assetId": "bgm_a",
                                        "endMode": "after_block",
                                        "endBlockId": "line_missing",
                                    },
                                    {
                                        "id": "music_backward_end",
                                        "type": "music_play",
                                        "assetId": "bgm_b",
                                        "endMode": "after_block",
                                        "endBlockId": "line_before",
                                    },
                                    {"id": "line_after", "type": "narration", "text": "After music."},
                                ],
                            }
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["metrics"]["musicPlayCount"], 2)
            self.assertEqual(report["metrics"]["musicScopedCount"], 2)
            self.assertEqual(report["metrics"]["musicAfterBlockScopeCount"], 2)
            self.assertEqual(report["metrics"]["missingMusicEndBlockCount"], 1)
            self.assertEqual(report["metrics"]["backwardMusicEndBlockCount"], 1)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("bgm_after_block_target_missing", issue_codes)
            self.assertIn("bgm_after_block_target_before_play", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("BGM after_block / 缺失结束 / 倒挂结束", markdown)
            self.assertIn("BGM after_block 结束卡片不可用", markdown)
            self.assertIn("BGM after_block 结束点早于播放点", markdown)

    def test_vn_baseline_quality_report_flags_audio_asset_usage_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            bgm_path = bundle_dir / "assets" / "bgm" / "main.ogg"
            unused_bgm_path = bundle_dir / "assets" / "bgm" / "unused.ogg"
            sfx_path = bundle_dir / "assets" / "sfx" / "door.ogg"
            unused_sfx_path = bundle_dir / "assets" / "sfx" / "unused.ogg"
            voice_path = bundle_dir / "assets" / "voices" / "line.ogg"
            unused_voice_path = bundle_dir / "assets" / "voices" / "unused.ogg"
            for path in [bgm_path, unused_bgm_path, sfx_path, unused_sfx_path, voice_path, unused_voice_path]:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"fake-audio")
            game_data = {
                "project": {
                    "projectId": "native_audio_usage_quality_smoke",
                    "title": "Native Audio Usage Quality Smoke",
                    "entrySceneId": "scene_audio",
                },
                "assets": {
                    "assets": [
                        {"id": "bgm_used", "type": "bgm", "name": "Main Theme", "exportUrl": bgm_path.relative_to(bundle_dir).as_posix()},
                        {"id": "bgm_unused", "type": "bgm", "name": "Unused Theme", "exportUrl": unused_bgm_path.relative_to(bundle_dir).as_posix()},
                        {"id": "sfx_used", "type": "sfx", "name": "Door", "exportUrl": sfx_path.relative_to(bundle_dir).as_posix()},
                        {"id": "sfx_unused", "type": "sfx", "name": "Unused SFX", "exportUrl": unused_sfx_path.relative_to(bundle_dir).as_posix()},
                        {"id": "voice_used", "type": "voice", "name": "Line Voice", "exportUrl": voice_path.relative_to(bundle_dir).as_posix()},
                        {"id": "voice_unused", "type": "voice", "name": "Unused Voice", "exportUrl": unused_voice_path.relative_to(bundle_dir).as_posix()},
                    ]
                },
                "characters": {"characters": []},
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_audio",
                                "name": "Audio",
                                "blocks": [
                                    {"id": "music_ok", "type": "music_play", "assetId": "bgm_used", "fadeInMs": 600},
                                    {"id": "music_missing", "type": "music_play", "assetId": "bgm_missing"},
                                    {"id": "sfx_ok", "type": "sfx_play", "assetId": "sfx_used"},
                                    {"id": "line_1", "type": "dialogue", "text": "Audio check.", "voiceAssetId": "voice_used"},
                                ],
                            }
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["metrics"]["bgmAssetCount"], 2)
            self.assertEqual(report["metrics"]["bgmUsedAssetCount"], 1)
            self.assertEqual(report["metrics"]["unusedBgmAssetCount"], 1)
            self.assertEqual(report["metrics"]["missingMusicAssetCount"], 1)
            self.assertEqual(report["metrics"]["sfxAssetCount"], 2)
            self.assertEqual(report["metrics"]["sfxUsedAssetCount"], 1)
            self.assertEqual(report["metrics"]["unusedSfxAssetCount"], 1)
            self.assertEqual(report["metrics"]["voiceAssetCount"], 2)
            self.assertEqual(report["metrics"]["voiceUsedAssetCount"], 1)
            self.assertEqual(report["metrics"]["unusedVoiceAssetCount"], 1)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("bgm_asset_missing", issue_codes)
            self.assertIn("bgm_asset_unused", issue_codes)
            self.assertIn("sfx_asset_unused", issue_codes)
            self.assertIn("voice_asset_unused", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("BGM 素材 / 已入剧情 / 未使用 / 缺失", markdown)
            self.assertIn("音效素材 / 已入剧情 / 未使用", markdown)
            self.assertIn("语音素材 / 已入剧情 / 未使用", markdown)

    def test_vn_baseline_quality_report_flags_save_slot_configuration_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            scenes = [
                {
                    "id": f"scene_{index}",
                    "name": f"Scene {index}",
                    "blocks": [{"id": f"line_{index}", "type": "narration", "text": f"Scene {index}."}],
                }
                for index in range(6)
            ]
            game_data = {
                "project": {
                    "projectId": "native_save_slot_quality_smoke",
                    "title": "Native Save Slot Quality Smoke",
                    "entrySceneId": "scene_0",
                    "runtimeSettings": {"formalSaveSlotCount": 2},
                },
                "assets": {"assets": []},
                "characters": {"characters": []},
                "chapters": [{"id": "chapter_1", "name": "Chapter 1", "scenes": scenes}],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["metrics"]["configuredFormalSaveSlotCount"], 2)
            self.assertEqual(report["metrics"]["formalSaveSlotCount"], 3)
            self.assertEqual(report["metrics"]["saveDialogPageCount"], 1)
            self.assertTrue(report["metrics"]["saveSlotCountClamped"])
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("save_slot_count_clamped", issue_codes)
            self.assertIn("save_slot_count_low", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("正式存档位 / 读档页数", markdown)
            self.assertIn("正式存档位配置超出安全范围", markdown)

    def test_vn_baseline_quality_report_flags_i18n_translation_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            game_data = {
                "project": {
                    "projectId": "native_i18n_quality_smoke",
                    "title": "Native I18n Quality Smoke",
                    "language": "zh-CN",
                    "entrySceneId": "scene_i18n",
                },
                "i18n": {
                    "defaultLanguage": "zh-CN",
                    "fallbackLanguage": "ja-JP",
                    "supportedLanguages": ["zh-CN", "en-US"],
                },
                "assets": {"assets": []},
                "characters": {
                    "characters": [
                        {
                            "id": "heroine",
                            "displayName": "女主角",
                            "displayNameTranslations": {"en-US": "Heroine"},
                            "expressions": [],
                        }
                    ]
                },
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "第一章",
                        "scenes": [
                            {
                                "id": "scene_i18n",
                                "name": "教室",
                                "blocks": [
                                    {
                                        "id": "line_1",
                                        "type": "dialogue",
                                        "speakerId": "heroine",
                                        "text": "你好。",
                                        "textTranslations": {"en-US": "Hello."},
                                    },
                                    {
                                        "id": "choice_i18n",
                                        "type": "choice",
                                        "options": [
                                            {"id": "choice_a", "text": "留下", "gotoSceneId": "scene_i18n"},
                                            {"id": "choice_b", "text": "离开", "gotoSceneId": "scene_i18n"},
                                        ],
                                    },
                                ],
                            }
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["metrics"]["supportedLanguageCount"], 2)
            self.assertEqual(report["metrics"]["targetI18nLanguageCount"], 1)
            self.assertEqual(report["metrics"]["i18nExpectedTranslationCount"], 6)
            self.assertEqual(report["metrics"]["i18nPresentTranslationCount"], 2)
            self.assertEqual(report["metrics"]["i18nTranslationCoveragePercent"], 33.3)
            self.assertFalse(report["metrics"]["i18nFallbackSupported"])
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("i18n_fallback_not_supported", issue_codes)
            self.assertIn("i18n_translation_sparse", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("语言 / 目标语言 / 翻译覆盖", markdown)
            self.assertIn("多语言翻译覆盖偏低", markdown)

    def test_vn_baseline_quality_report_flags_font_asset_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            font_path = bundle_dir / "assets" / "fonts" / "story.woff"
            font_path.parent.mkdir(parents=True)
            font_path.write_bytes(b"fake-woff-font")
            game_data = {
                "project": {
                    "projectId": "native_font_quality_smoke",
                    "title": "Native Font Quality Smoke",
                    "entrySceneId": "scene_font",
                    "gameUiConfig": {
                        "fontStyle": "serif",
                        "fontFamily": "Story Serif",
                        "fontAssetId": "font_story",
                    },
                },
                "assets": {
                    "assets": [
                        {
                            "id": "font_story",
                            "type": "font",
                            "name": "Story Font",
                            "exportUrl": "assets/fonts/story.woff",
                        }
                    ]
                },
                "characters": {"characters": []},
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_font",
                                "name": "Font",
                                "blocks": [
                                    {"id": "line_1", "type": "narration", "text": "字体巡检应该提前发现不推荐格式。"},
                                ],
                            }
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["metrics"]["fontAssetCount"], 1)
            self.assertTrue(report["metrics"]["fontFamilyConfigured"])
            self.assertTrue(report["metrics"]["customFontAssetBound"])
            self.assertFalse(report["metrics"]["fontAssetUsable"])
            self.assertEqual(report["metrics"]["fontExtensionRiskCount"], 1)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("font_extension_risk", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("字体素材 / 已绑定 / 可用", markdown)
            self.assertIn("字体缺失 / 类型风险 / 格式风险", markdown)
            self.assertIn("项目字体格式可能不稳定", markdown)

    def test_vn_baseline_quality_report_flags_voice_binding_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            voice_path = bundle_dir / "assets" / "voices" / "line_1.ogg"
            voice_path.parent.mkdir(parents=True, exist_ok=True)
            voice_path.write_bytes(b"fake-voice")
            game_data = {
                "project": {
                    "projectId": "native_voice_quality_smoke",
                    "title": "Native Voice Quality Smoke",
                    "entrySceneId": "scene_voice",
                },
                "assets": {
                    "assets": [
                        {
                            "id": "voice_ok",
                            "type": "voice",
                            "name": "Line 1 Voice",
                            "exportUrl": voice_path.relative_to(bundle_dir).as_posix(),
                            "tags": [],
                        }
                    ]
                },
                "characters": {"characters": []},
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_voice",
                                "name": "Voice",
                                "blocks": [
                                    {"id": "line_1", "type": "dialogue", "text": "Voiced line.", "voiceAssetId": "voice_ok"},
                                    {"id": "line_2", "type": "dialogue", "text": "Missing voice.", "voiceAssetId": "voice_missing"},
                                    {"id": "line_3", "type": "dialogue", "text": "No voice 1."},
                                    {"id": "line_4", "type": "dialogue", "text": "No voice 2."},
                                    {"id": "line_5", "type": "dialogue", "text": "No voice 3."},
                                ],
                            }
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["status"], "needs_fix")
            self.assertEqual(report["metrics"]["voiceEligibleLineCount"], 5)
            self.assertEqual(report["metrics"]["voiceBoundLineCount"], 2)
            self.assertEqual(report["metrics"]["dialogueVoiceCount"], 2)
            self.assertEqual(report["metrics"]["voiceCoveragePercent"], 40.0)
            self.assertEqual(report["metrics"]["missingVoiceAssetCount"], 1)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("voice_asset_missing", issue_codes)
            self.assertIn("voice_coverage_gap", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("存在已绑定但缺失的语音文件", markdown)
            self.assertIn("语音绑定 / 可配音文本", markdown)

    def test_vn_baseline_quality_report_flags_route_integrity_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            game_data = {
                "project": {
                    "projectId": "native_route_quality_smoke",
                    "title": "Native Route Quality Smoke",
                    "entrySceneId": "scene_start",
                },
                "assets": {"assets": []},
                "characters": {"characters": []},
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_start",
                                "name": "Start",
                                "blocks": [
                                    {
                                        "id": "choice_1",
                                        "type": "choice",
                                        "options": [
                                            {"text": "Go missing", "gotoSceneId": "scene_missing"},
                                            {"text": "Go good", "gotoSceneId": "scene_good"},
                                        ],
                                    }
                                ],
                            },
                            {
                                "id": "scene_good",
                                "name": "Good",
                                "blocks": [{"id": "line_good", "type": "narration", "text": "Reached."}],
                            },
                            {
                                "id": "scene_island",
                                "name": "Island",
                                "blocks": [{"id": "line_island", "type": "narration", "text": "Hidden."}],
                            },
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["status"], "needs_fix")
            self.assertTrue(report["metrics"]["entrySceneExists"])
            self.assertEqual(report["metrics"]["routeTargetMissingCount"], 1)
            self.assertEqual(report["metrics"]["unreachableSceneCount"], 1)
            self.assertEqual(report["metrics"]["linkedSceneCount"], 2)
            self.assertEqual(report["metrics"]["reachableTerminalSceneCount"], 1)
            self.assertEqual(report["metrics"]["reachableCreditsTerminalSceneCount"], 0)
            self.assertEqual(report["metrics"]["reachablePlainTerminalSceneCount"], 1)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("route_target_missing", issue_codes)
            self.assertIn("unreachable_scene", issue_codes)
            self.assertIn("plain_terminal_scene", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("路线跳转目标缺失", markdown)
            self.assertIn("入口不可达场景", markdown)
            self.assertIn("可达终点 / 片尾收束 / 普通断点", markdown)

    def test_vn_baseline_quality_report_flags_empty_navigation_targets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            game_data = {
                "project": {
                    "projectId": "native_empty_navigation_quality_smoke",
                    "title": "Native Empty Navigation Quality Smoke",
                    "entrySceneId": "scene_start",
                },
                "assets": {"assets": []},
                "characters": {"characters": []},
                "variables": {
                    "variables": [
                        {"id": "flag_seen", "name": "Seen", "type": "boolean", "defaultValue": False}
                    ]
                },
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_start",
                                "name": "Start",
                                "blocks": [
                                    {"id": "jump_empty", "type": "jump", "targetSceneId": ""},
                                    {
                                        "id": "condition_empty_targets",
                                        "type": "condition",
                                        "branches": [
                                            {
                                                "id": "branch_empty",
                                                "gotoSceneId": "",
                                                "when": [{"variableId": "flag_seen", "operator": "==", "value": True}],
                                            },
                                            {
                                                "id": "branch_valid",
                                                "gotoSceneId": "scene_end",
                                                "when": [{"variableId": "flag_seen", "operator": "==", "value": False}],
                                            },
                                        ],
                                    },
                                ],
                            },
                            {
                                "id": "scene_end",
                                "name": "End",
                                "blocks": [{"id": "line_end", "type": "narration", "text": "Reached."}],
                            },
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["metrics"]["missingNavigationTargetCount"], 2)
            self.assertEqual(report["metrics"]["implicitConditionFallbackEndCount"], 1)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("navigation_target_empty", issue_codes)
            self.assertIn("condition_fallback_implicit_end", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("空路线目标 / 条件隐式结束", markdown)
            self.assertIn("路线控制卡片缺少跳转目标", markdown)

    def test_vn_baseline_quality_report_flags_logic_variable_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            game_data = {
                "project": {
                    "projectId": "native_logic_quality_smoke",
                    "title": "Native Logic Quality Smoke",
                    "entrySceneId": "scene_logic",
                },
                "assets": {"assets": []},
                "characters": {"characters": []},
                "variables": {
                    "variables": [
                        {"id": "var_score", "name": "Score", "type": "number", "defaultValue": 0},
                        {"id": "var_route", "name": "Route", "type": "string", "defaultValue": "a"},
                    ]
                },
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_logic",
                                "name": "Logic",
                                "blocks": [
                                    {"id": "set_missing", "type": "variable_set", "variableId": "var_missing", "value": 1},
                                    {"id": "add_string", "type": "variable_add", "variableId": "var_route", "value": 2},
                                    {
                                        "id": "choice_logic",
                                        "type": "choice",
                                        "options": [
                                            {
                                                "text": "Gain",
                                                "gotoSceneId": "scene_logic",
                                                "effects": [
                                                    {"type": "variable_add", "variableId": "var_route", "value": 1},
                                                    {"type": "variable_set", "variableId": "var_missing_effect", "value": True},
                                                ],
                                            }
                                        ],
                                    },
                                    {
                                        "id": "condition_logic",
                                        "type": "condition",
                                        "branches": [
                                            {
                                                "id": "branch_1",
                                                "gotoSceneId": "scene_logic",
                                                "when": [{"variableId": "var_route", "operator": ">", "value": "b"}],
                                            },
                                            {"id": "branch_2", "gotoSceneId": "scene_logic", "when": []},
                                        ],
                                    },
                                    {"id": "condition_empty", "type": "condition", "branches": []},
                                ],
                            }
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["status"], "needs_fix")
            self.assertEqual(report["metrics"]["variableCount"], 2)
            self.assertEqual(report["metrics"]["variableSetCount"], 1)
            self.assertEqual(report["metrics"]["variableAddCount"], 1)
            self.assertEqual(report["metrics"]["conditionCount"], 2)
            self.assertEqual(report["metrics"]["conditionBranchCount"], 2)
            self.assertEqual(report["metrics"]["conditionRuleCount"], 1)
            self.assertEqual(report["metrics"]["choiceEffectCount"], 2)
            self.assertEqual(report["metrics"]["logicMissingVariableCount"], 2)
            self.assertEqual(report["metrics"]["logicNonNumberAddCount"], 2)
            self.assertEqual(report["metrics"]["logicOperatorMismatchCount"], 1)
            self.assertEqual(report["metrics"]["conditionEmptyBranchCount"], 2)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("logic_variable_missing", issue_codes)
            self.assertIn("logic_variable_add_type", issue_codes)
            self.assertIn("logic_condition_operator", issue_codes)
            self.assertIn("logic_condition_empty", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("变量 / 条件 / 选项效果", markdown)
            self.assertIn("逻辑缺失变量 / 非数字加减 / 条件符号不匹配", markdown)

    def test_vn_baseline_quality_report_flags_same_target_condition_branches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            game_data = {
                "project": {
                    "projectId": "native_condition_same_target_quality_smoke",
                    "title": "Native Condition Same Target Quality Smoke",
                    "entrySceneId": "scene_start",
                },
                "assets": {"assets": []},
                "characters": {"characters": []},
                "variables": {
                    "variables": [
                        {"id": "route_a", "name": "Route A", "type": "boolean", "defaultValue": False},
                        {"id": "route_b", "name": "Route B", "type": "boolean", "defaultValue": False},
                    ]
                },
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_start",
                                "name": "Start",
                                "blocks": [
                                    {
                                        "id": "condition_same_target",
                                        "type": "condition",
                                        "elseGotoSceneId": "scene_else",
                                        "branches": [
                                            {
                                                "id": "branch_a",
                                                "gotoSceneId": "scene_merge",
                                                "when": [{"variableId": "route_a", "operator": "==", "value": True}],
                                            },
                                            {
                                                "id": "branch_b",
                                                "gotoSceneId": "scene_merge",
                                                "when": [{"variableId": "route_b", "operator": "==", "value": True}],
                                            },
                                        ],
                                    }
                                ],
                            },
                            {
                                "id": "scene_merge",
                                "name": "Merge",
                                "blocks": [{"id": "line_merge", "type": "narration", "text": "Both branches arrive here."}],
                            },
                            {
                                "id": "scene_else",
                                "name": "Else",
                                "blocks": [{"id": "line_else", "type": "narration", "text": "Fallback route."}],
                            },
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["metrics"]["sameTargetConditionCount"], 1)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("condition_same_target", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("同目标条件分支", markdown)
            self.assertIn("部分条件分支结果完全相同", markdown)

    def test_vn_baseline_quality_report_flags_unconsumed_variable_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            game_data = {
                "project": {
                    "projectId": "native_unconsumed_variable_quality_smoke",
                    "title": "Native Unconsumed Variable Quality Smoke",
                    "entrySceneId": "scene_start",
                },
                "assets": {"assets": []},
                "characters": {"characters": []},
                "variables": {
                    "variables": [
                        {"id": "affection", "name": "Affection", "type": "number", "defaultValue": 0},
                    ]
                },
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_start",
                                "name": "Start",
                                "blocks": [
                                    {
                                        "id": "choice_affection",
                                        "type": "choice",
                                        "options": [
                                            {
                                                "text": "Be kind",
                                                "gotoSceneId": "scene_end",
                                                "effects": [
                                                    {"type": "variable_add", "variableId": "affection", "value": 1},
                                                ],
                                            }
                                        ],
                                    }
                                ],
                            },
                            {
                                "id": "scene_end",
                                "name": "End",
                                "blocks": [{"id": "line_end", "type": "narration", "text": "The route ends without reading affection."}],
                            },
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["metrics"]["variableWrittenCount"], 1)
            self.assertEqual(report["metrics"]["conditionReadVariableCount"], 0)
            self.assertEqual(report["metrics"]["routeInfluencingVariableCount"], 0)
            self.assertEqual(report["metrics"]["unconsumedVariableWriteCount"], 1)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("logic_variable_unconsumed_write", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("写入变量 / 条件读取 / 影响路线", markdown)
            self.assertIn("未被条件读取的变量写入", markdown)
            self.assertIn("部分变量变化没有进入路线判断", markdown)

    def test_vn_baseline_quality_report_flags_text_readability_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            long_text = "这一句会被故意写得很长，" * 32
            multiline_text = "\n".join(["第一行", "第二行", "第三行", "第四行", "第五行", "第六行"])
            game_data = {
                "project": {
                    "projectId": "native_text_quality_smoke",
                    "title": "Native Text Quality Smoke",
                    "entrySceneId": "scene_text",
                    "dialogBoxConfig": {
                        "preset": "custom",
                        "widthPercent": 58,
                        "minHeight": 100,
                        "paddingX": 8,
                        "paddingY": 6,
                        "backgroundColor": "#f8fbff",
                        "backgroundOpacity": 32,
                        "textColor": "#ffffff",
                    },
                },
                "assets": {"assets": []},
                "characters": {"characters": []},
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_text",
                                "name": "Text",
                                "blocks": [
                                    {"id": "long_line", "type": "dialogue", "text": long_text},
                                    {"id": "multi_line", "type": "narration", "text": multiline_text},
                                    {"id": "short_line", "type": "dialogue", "text": "第三句用于触发文本框可读性巡检。"},
                                ],
                            }
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["metrics"]["longTextBlockCount"], 1)
            self.assertEqual(report["metrics"]["multilineTextBlockCount"], 1)
            self.assertGreaterEqual(report["metrics"]["dialogBoxReadabilityRiskCount"], 1)
            self.assertEqual(report["metrics"]["dialogBoxBackgroundOpacity"], 32)
            self.assertEqual(report["metrics"]["dialogBoxWidthPercent"], 58)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("long_story_text", issue_codes)
            self.assertIn("multiline_story_text", issue_codes)
            self.assertIn("dialog_box_readability_risk", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("过长文本 / 多换行文本", markdown)
            self.assertIn("文本框可读性风险", markdown)
            self.assertIn("部分文本卡片过长", markdown)

    def test_vn_baseline_quality_report_flags_missing_character_references(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            game_data = {
                "project": {
                    "projectId": "native_character_reference_quality_smoke",
                    "title": "Native Character Reference Quality Smoke",
                    "entrySceneId": "scene_character_refs",
                },
                "assets": {"assets": []},
                "characters": {
                    "characters": [
                        {
                            "id": "heroine",
                            "displayName": "Heroine",
                            "expressions": [{"id": "default", "spriteAssetId": ""}],
                        }
                    ]
                },
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_character_refs",
                                "name": "Character Refs",
                                "blocks": [
                                    {"id": "line_missing_speaker", "type": "dialogue", "speakerId": "ghost", "text": "Missing speaker."},
                                    {"id": "line_missing_expression", "type": "dialogue", "speakerId": "heroine", "expressionId": "smile", "text": "Missing expression."},
                                    {"id": "show_missing_character", "type": "character_show", "characterId": "ghost", "expressionId": "default"},
                                    {"id": "show_missing_expression", "type": "character_show", "characterId": "heroine", "expressionId": "angry"},
                                    {"id": "hide_missing_character", "type": "character_hide", "characterId": "ghost"},
                                ],
                            }
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["metrics"]["missingCharacterReferenceCount"], 3)
            self.assertEqual(report["metrics"]["missingExpressionReferenceCount"], 2)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("character_reference_missing", issue_codes)
            self.assertIn("character_expression_missing", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("缺失角色 / 表情引用", markdown)
            self.assertIn("剧情卡片引用了不存在的角色", markdown)

    def test_vn_baseline_quality_report_flags_static_character_staging(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            game_data = {
                "project": {
                    "projectId": "native_character_stage_quality_smoke",
                    "title": "Native Character Stage Quality Smoke",
                    "entrySceneId": "scene_stage",
                },
                "assets": {"assets": []},
                "characters": {"characters": []},
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_stage",
                                "name": "Stage",
                                "blocks": [
                                    {"id": "show_1", "type": "character_show", "characterId": "heroine", "position": "center", "transition": "none"},
                                    {"id": "show_2", "type": "character_show", "characterId": "heroine", "position": "center", "transition": "none"},
                                    {"id": "show_3", "type": "character_show", "characterId": "heroine", "position": "center", "transition": "none"},
                                    {"id": "show_4", "type": "character_show", "characterId": "heroine", "position": "center", "transition": "none"},
                                    {"id": "line_1", "type": "dialogue", "speakerId": "heroine", "text": "Static staging 1."},
                                    {"id": "line_2", "type": "dialogue", "speakerId": "heroine", "text": "Static staging 2."},
                                    {"id": "line_3", "type": "dialogue", "speakerId": "heroine", "text": "Static staging 3."},
                                ],
                            }
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["metrics"]["characterShowCount"], 4)
            self.assertEqual(report["metrics"]["characterTransitionCount"], 0)
            self.assertEqual(report["metrics"]["characterPositionVariantCount"], 1)
            self.assertEqual(report["metrics"]["characterStageAdjustmentCount"], 0)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("character_transition_missing", issue_codes)
            self.assertIn("character_position_static", issue_codes)
            self.assertIn("character_stage_static", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("人物转场 / 登场", markdown)
            self.assertIn("人物舞台参数没有变化", markdown)

    def test_vn_baseline_quality_report_counts_character_stage_motion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            game_data = {
                "project": {
                    "projectId": "native_character_motion_quality_smoke",
                    "title": "Native Character Motion Quality Smoke",
                    "entrySceneId": "scene_motion",
                },
                "assets": {"assets": []},
                "characters": {
                    "characters": [
                        {
                            "id": "heroine",
                            "displayName": "Heroine",
                            "expressions": [
                                {"id": "default", "spriteAssetId": ""},
                                {"id": "smile", "spriteAssetId": ""},
                            ],
                        }
                    ]
                },
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_motion",
                                "name": "Motion",
                                "blocks": [
                                    {
                                        "id": "show_heroine",
                                        "type": "character_show",
                                        "characterId": "heroine",
                                        "expressionId": "default",
                                        "position": "left",
                                    },
                                    {
                                        "id": "move_heroine",
                                        "type": "character_move",
                                        "characterId": "heroine",
                                        "expressionId": "smile",
                                        "position": "right",
                                        "durationMs": 900,
                                        "easing": "ease_in_out",
                                        "stage": {"offsetX": 24, "scale": 108, "layer": 2},
                                    },
                                    {
                                        "id": "move_missing_expression",
                                        "type": "character_move",
                                        "characterId": "heroine",
                                        "expressionId": "missing",
                                        "position": "center",
                                    },
                                ],
                            }
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(
                json.dumps(game_data, ensure_ascii=False),
                encoding="utf-8",
            )

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["metrics"]["characterShowCount"], 1)
            self.assertEqual(report["metrics"]["characterMoveCount"], 2)
            self.assertEqual(report["metrics"]["characterPositionVariantCount"], 3)
            self.assertEqual(report["metrics"]["characterStageAdjustmentCount"], 1)
            self.assertEqual(report["metrics"]["missingExpressionReferenceCount"], 1)
            self.assertNotIn(
                "character_position_static",
                {issue["code"] for issue in report["issues"]},
            )

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("人物转场 / 登场 / 动作", markdown)
            self.assertIn("1 / 1 / 2", markdown)

    def test_vn_baseline_quality_report_flags_background_asset_and_transition_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            bg_a = bundle_dir / "assets" / "backgrounds" / "classroom.png"
            bg_b = bundle_dir / "assets" / "backgrounds" / "rooftop.png"
            bg_a.parent.mkdir(parents=True, exist_ok=True)
            bg_a.write_bytes(b"fake-bg-a")
            bg_b.write_bytes(b"fake-bg-b")
            game_data = {
                "project": {
                    "projectId": "native_background_quality_smoke",
                    "title": "Native Background Quality Smoke",
                    "entrySceneId": "scene_background",
                },
                "assets": {
                    "assets": [
                        {
                            "id": "bg_a",
                            "type": "background",
                            "name": "Classroom",
                            "exportUrl": bg_a.relative_to(bundle_dir).as_posix(),
                        },
                        {
                            "id": "bg_b",
                            "type": "background",
                            "name": "Rooftop",
                            "exportUrl": bg_b.relative_to(bundle_dir).as_posix(),
                        },
                    ]
                },
                "characters": {"characters": []},
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_background",
                                "name": "Background",
                                "blocks": [
                                    {"id": "bg_1", "type": "background", "assetId": "bg_a", "transition": "none"},
                                    {"id": "bg_2", "type": "background", "assetId": "bg_b", "transition": "none"},
                                    {"id": "bg_3", "type": "background", "assetId": "bg_missing", "transition": "none"},
                                    {"id": "line_1", "type": "narration", "text": "Background check."},
                                ],
                            }
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["status"], "needs_fix")
            self.assertEqual(report["metrics"]["backgroundBlockCount"], 3)
            self.assertEqual(report["metrics"]["backgroundTransitionCount"], 0)
            self.assertEqual(report["metrics"]["backgroundAssetVariantCount"], 3)
            self.assertEqual(report["metrics"]["missingBackgroundAssetCount"], 1)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("background_asset_missing", issue_codes)
            self.assertIn("background_transition_missing", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("存在缺失的背景/CG 文件", markdown)
            self.assertIn("背景转场 / 背景卡", markdown)

    def test_vn_baseline_quality_report_flags_choice_text_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            game_data = {
                "project": {
                    "projectId": "native_choice_quality_smoke",
                    "title": "Native Choice Quality Smoke",
                    "entrySceneId": "scene_choice",
                },
                "assets": {"assets": []},
                "characters": {"characters": []},
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_choice",
                                "name": "Choice",
                                "blocks": [
                                    {
                                        "id": "choice_1",
                                        "type": "choice",
                                        "options": [
                                            {"text": "", "gotoSceneId": "scene_choice"},
                                            {"text": "Ask again", "gotoSceneId": "scene_choice"},
                                            {"text": "Ask again", "gotoSceneId": "scene_choice"},
                                            {"text": "This option is deliberately too long for a compact visual novel choice button", "gotoSceneId": "scene_choice"},
                                            {"text": "Leave", "gotoSceneId": "scene_choice"},
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["status"], "needs_fix")
            self.assertEqual(report["metrics"]["choiceOptionCount"], 5)
            self.assertEqual(report["metrics"]["emptyChoiceOptionCount"], 1)
            self.assertEqual(report["metrics"]["longChoiceOptionCount"], 1)
            self.assertEqual(report["metrics"]["duplicateChoiceOptionCount"], 1)
            self.assertEqual(report["metrics"]["crowdedChoiceBlockCount"], 1)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("empty_choice_option", issue_codes)
            self.assertIn("long_choice_option", issue_codes)
            self.assertIn("duplicate_choice_option", issue_codes)
            self.assertIn("crowded_choice_block", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("存在空白选项按钮", markdown)
            self.assertIn("空白 / 超长 / 重复选项", markdown)

    def test_vn_baseline_quality_report_flags_choice_availability_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            game_data = {
                "project": {
                    "projectId": "native_choice_gate_quality_smoke",
                    "title": "Native Choice Gate Quality Smoke",
                    "entrySceneId": "scene_choice",
                },
                "assets": {"assets": []},
                "characters": {"characters": []},
                "variables": {
                    "variables": [
                        {"id": "affection", "name": "Affection", "type": "number", "defaultValue": 0},
                        {"id": "route_name", "name": "Route", "type": "string", "defaultValue": ""},
                    ]
                },
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_choice",
                                "name": "Choice",
                                "blocks": [
                                    {
                                        "id": "choice_gate",
                                        "type": "choice",
                                        "options": [
                                            {
                                                "id": "hidden",
                                                "text": "Hidden route",
                                                "gotoSceneId": "scene_after",
                                                "choiceAvailabilityMode": "hide_when_false",
                                                "choiceAvailabilityWhen": [
                                                    {"variableId": "affection", "operator": ">=", "value": 5}
                                                ],
                                            },
                                            {
                                                "id": "locked",
                                                "text": "Locked route",
                                                "gotoSceneId": "scene_after",
                                                "choiceAvailabilityMode": "disable_when_false",
                                                "choiceAvailabilityWhen": [],
                                            },
                                            {
                                                "id": "broken",
                                                "text": "Broken route",
                                                "gotoSceneId": "scene_after",
                                                "choiceAvailabilityMode": "hide_when_false",
                                                "choiceAvailabilityWhen": [
                                                    {"variableId": "missing_flag", "operator": "==", "value": True},
                                                    {"variableId": "route_name", "operator": ">", "value": "B"},
                                                ],
                                            },
                                        ],
                                    }
                                ],
                            },
                            {
                                "id": "scene_after",
                                "name": "After",
                                "blocks": [{"id": "line_after", "type": "narration", "text": "After choice."}],
                            },
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(
                json.dumps(game_data, ensure_ascii=False),
                encoding="utf-8",
            )

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            metrics = report["metrics"]
            self.assertEqual(metrics["choiceGatedOptionCount"], 3)
            self.assertEqual(metrics["choiceAvailabilityRuleCount"], 3)
            self.assertEqual(metrics["choiceGateWithoutRulesCount"], 1)
            self.assertEqual(metrics["choiceGateMissingVariableCount"], 1)
            self.assertEqual(metrics["choiceGateOperatorMismatchCount"], 1)
            self.assertEqual(metrics["choiceLockedReasonMissingCount"], 1)
            self.assertEqual(metrics["choiceBlockWithoutAlwaysCount"], 1)
            self.assertEqual(metrics["conditionReadVariableCount"], 2)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("choice_gate_without_rules", issue_codes)
            self.assertIn("choice_gate_missing_variable", issue_codes)
            self.assertIn("choice_gate_operator_mismatch", issue_codes)
            self.assertIn("choice_locked_reason_missing", issue_codes)
            self.assertIn("choice_block_without_always_option", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("条件门控选项 / 判断规则", markdown)
            self.assertIn("条件选项缺少判断规则", markdown)

    def test_vn_baseline_quality_report_flags_no_action_choice_options(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            game_data = {
                "project": {
                    "projectId": "native_choice_action_quality_smoke",
                    "title": "Native Choice Action Quality Smoke",
                    "entrySceneId": "scene_choice_action",
                },
                "assets": {"assets": []},
                "characters": {"characters": []},
                "variables": {
                    "variables": [
                        {"id": "route_hint", "name": "Route Hint", "type": "text", "defaultValue": ""}
                    ]
                },
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_choice_action",
                                "name": "Choice Action",
                                "blocks": [
                                    {
                                        "id": "choice_action",
                                        "type": "choice",
                                        "options": [
                                            {"id": "noop_choice", "text": "Do nothing"},
                                            {
                                                "id": "effect_choice",
                                                "text": "Record and continue",
                                                "effects": [
                                                    {"type": "variable_set", "variableId": "route_hint", "value": "recorded"}
                                                ],
                                            },
                                            {"id": "jump_choice", "text": "Jump", "gotoSceneId": "scene_choice_action"},
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["metrics"]["choiceOptionCount"], 3)
            self.assertEqual(report["metrics"]["noActionChoiceOptionCount"], 1)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("choice_option_no_action", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("无动作选项", markdown)
            self.assertIn("部分选项没有明确动作", markdown)

    def test_vn_baseline_quality_report_flags_same_target_choice_options(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            game_data = {
                "project": {
                    "projectId": "native_choice_same_target_quality_smoke",
                    "title": "Native Choice Same Target Quality Smoke",
                    "entrySceneId": "scene_choice",
                },
                "assets": {"assets": []},
                "characters": {"characters": []},
                "variables": {
                    "variables": [
                        {"id": "route_hint", "name": "Route Hint", "type": "text", "defaultValue": ""}
                    ]
                },
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_choice",
                                "name": "Choice",
                                "blocks": [
                                    {
                                        "id": "same_target_choice",
                                        "type": "choice",
                                        "options": [
                                            {"id": "ask", "text": "Ask softly", "gotoSceneId": "scene_after"},
                                            {"id": "push", "text": "Push harder", "gotoSceneId": "scene_after"},
                                            {
                                                "id": "record",
                                                "text": "Remember this",
                                                "gotoSceneId": "scene_after",
                                                "effects": [
                                                    {"type": "variable_set", "variableId": "route_hint", "value": "remembered"}
                                                ],
                                            },
                                        ],
                                    }
                                ],
                            },
                            {
                                "id": "scene_after",
                                "name": "After",
                                "blocks": [{"id": "line_after", "type": "narration", "text": "After choice."}],
                            },
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["metrics"]["sameTargetChoiceCount"], 1)
            self.assertEqual(report["metrics"]["choiceEffectCount"], 1)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("choice_same_target", issue_codes)
            self.assertNotIn("choice_option_no_action", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("同目标假分支", markdown)
            self.assertIn("部分选项分支结果完全相同", markdown)

    def test_vn_baseline_quality_report_flags_sfx_asset_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            sfx_path = bundle_dir / "assets" / "sfx" / "door.ogg"
            sfx_path.parent.mkdir(parents=True, exist_ok=True)
            sfx_path.write_bytes(b"fake-sfx")
            game_data = {
                "project": {
                    "projectId": "native_sfx_quality_smoke",
                    "title": "Native SFX Quality Smoke",
                    "entrySceneId": "scene_sfx",
                },
                "assets": {
                    "assets": [
                        {
                            "id": "sfx_ok",
                            "type": "sfx",
                            "name": "Door",
                            "exportUrl": sfx_path.relative_to(bundle_dir).as_posix(),
                        }
                    ]
                },
                "characters": {"characters": []},
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_sfx",
                                "name": "SFX",
                                "blocks": [
                                    {"id": "sfx_1", "type": "sfx_play", "assetId": "sfx_ok"},
                                    {"id": "sfx_2", "type": "sfx_play", "assetId": "sfx_missing"},
                                    {"id": "line_1", "type": "narration", "text": "SFX check."},
                                ],
                            }
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["status"], "needs_fix")
            self.assertEqual(report["metrics"]["sfxPlayCount"], 2)
            self.assertEqual(report["metrics"]["missingSfxAssetCount"], 1)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("sfx_asset_missing", issue_codes)
            self.assertNotIn("sfx_plan", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("存在缺失的音效文件", markdown)
            self.assertIn("音效点 / 缺失音效", markdown)

    def test_vn_baseline_quality_report_flags_missing_sfx_plan_for_multi_scene_projects(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            game_data = {
                "project": {
                    "projectId": "native_sfx_plan_quality_smoke",
                    "title": "Native SFX Plan Quality Smoke",
                    "entrySceneId": "scene_a",
                },
                "assets": {"assets": []},
                "characters": {"characters": []},
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {"id": "scene_a", "name": "A", "blocks": [{"id": "line_a", "type": "narration", "text": "A."}]},
                            {"id": "scene_b", "name": "B", "blocks": [{"id": "line_b", "type": "narration", "text": "B."}]},
                            {"id": "scene_c", "name": "C", "blocks": [{"id": "line_c", "type": "narration", "text": "C."}]},
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["metrics"]["sfxPlayCount"], 0)
            self.assertEqual(report["metrics"]["missingSfxAssetCount"], 0)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("sfx_plan", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("缺少基础音效点", markdown)

    def test_vn_baseline_quality_report_flags_video_asset_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            video_path = bundle_dir / "assets" / "video" / "opening.mp4"
            video_path.parent.mkdir(parents=True, exist_ok=True)
            video_path.write_bytes(b"fake-video")
            game_data = {
                "project": {
                    "projectId": "native_video_quality_smoke",
                    "title": "Native Video Quality Smoke",
                    "entrySceneId": "scene_video",
                },
                "assets": {
                    "assets": [
                        {
                            "id": "video_ok",
                            "type": "video",
                            "name": "Opening",
                            "exportUrl": video_path.relative_to(bundle_dir).as_posix(),
                        }
                    ]
                },
                "characters": {"characters": []},
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_video",
                                "name": "Video",
                                "blocks": [
                                    {"id": "video_1", "type": "video_play", "assetId": "video_ok"},
                                    {"id": "video_2", "type": "video_play", "assetId": "video_missing"},
                                    {"id": "line_1", "type": "narration", "text": "Video check."},
                                ],
                            }
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["status"], "needs_fix")
            self.assertEqual(report["metrics"]["videoAssetCount"], 1)
            self.assertEqual(report["metrics"]["videoPlayCount"], 2)
            self.assertEqual(report["metrics"]["missingVideoAssetCount"], 1)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("video_asset_missing", issue_codes)
            self.assertNotIn("video_asset_unused", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("存在缺失的视频文件", markdown)
            self.assertIn("视频素材 / 播放卡 / 缺失视频", markdown)

    def test_vn_baseline_quality_report_flags_unused_video_assets_as_polish(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            video_path = bundle_dir / "assets" / "video" / "pv.mp4"
            video_path.parent.mkdir(parents=True, exist_ok=True)
            video_path.write_bytes(b"fake-video")
            game_data = {
                "project": {
                    "projectId": "native_unused_video_quality_smoke",
                    "title": "Native Unused Video Quality Smoke",
                    "entrySceneId": "scene_video",
                },
                "assets": {
                    "assets": [
                        {
                            "id": "video_unused",
                            "type": "video",
                            "name": "PV",
                            "exportUrl": video_path.relative_to(bundle_dir).as_posix(),
                        }
                    ]
                },
                "characters": {"characters": []},
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_video",
                                "name": "Video",
                                "blocks": [{"id": "line_1", "type": "narration", "text": "Unused video."}],
                            }
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["metrics"]["videoAssetCount"], 1)
            self.assertEqual(report["metrics"]["videoPlayCount"], 0)
            self.assertEqual(report["metrics"]["missingVideoAssetCount"], 0)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("video_asset_unused", issue_codes)
            self.assertNotIn("video_asset_missing", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("视频素材还没有进入剧情", markdown)

    def test_vn_baseline_quality_report_flags_unused_cg_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            used_cg_path = bundle_dir / "assets" / "cg" / "first_cg.png"
            unused_cg_path = bundle_dir / "assets" / "cg" / "secret_cg.png"
            used_cg_path.parent.mkdir(parents=True, exist_ok=True)
            used_cg_path.write_bytes(b"fake-used-cg")
            unused_cg_path.write_bytes(b"fake-unused-cg")
            game_data = {
                "project": {
                    "projectId": "native_cg_quality_smoke",
                    "title": "Native CG Quality Smoke",
                    "entrySceneId": "scene_cg",
                },
                "assets": {
                    "assets": [
                        {
                            "id": "cg_used",
                            "type": "cg",
                            "name": "First CG",
                            "exportUrl": used_cg_path.relative_to(bundle_dir).as_posix(),
                        },
                        {
                            "id": "cg_unused",
                            "type": "cg",
                            "name": "Secret CG",
                            "exportUrl": unused_cg_path.relative_to(bundle_dir).as_posix(),
                        },
                    ]
                },
                "characters": {"characters": []},
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_cg",
                                "name": "CG",
                                "blocks": [
                                    {"id": "cg_block", "type": "background", "assetId": "cg_used", "transition": "fade"},
                                    {"id": "line_1", "type": "narration", "text": "CG unlocked."},
                                ],
                            }
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["metrics"]["cgAssetCount"], 2)
            self.assertEqual(report["metrics"]["cgUsedAssetCount"], 1)
            self.assertEqual(report["metrics"]["unusedCgAssetCount"], 1)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("cg_asset_unused", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("CG 素材 / 已入剧情 / 未使用", markdown)
            self.assertIn("部分 CG 素材还没有进入剧情", markdown)

    def test_vn_baseline_quality_report_flags_credits_roll_content_gaps(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            game_data = {
                "project": {
                    "projectId": "native_credits_quality_smoke",
                    "title": "Native Credits Quality Smoke",
                    "entrySceneId": "scene_credits",
                },
                "assets": {"assets": []},
                "characters": {"characters": []},
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_credits",
                                "name": "Credits",
                                "blocks": [
                                    {
                                        "id": "credits_empty",
                                        "type": "credits_roll",
                                        "title": "",
                                        "subtitle": "",
                                        "lines": [],
                                        "durationSeconds": 0,
                                    },
                                    {
                                        "id": "credits_short",
                                        "type": "credits_roll",
                                        "title": "STAFF",
                                        "lines": ["企划：A", "美术：B"],
                                        "durationSeconds": 3,
                                    },
                                    {"id": "line_1", "type": "narration", "text": "Credits check."},
                                ],
                            }
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["status"], "needs_fix")
            self.assertEqual(report["metrics"]["creditsRollCount"], 2)
            self.assertEqual(report["metrics"]["creditsLineCount"], 2)
            self.assertEqual(report["metrics"]["emptyCreditsRollCount"], 1)
            self.assertEqual(report["metrics"]["shortCreditsRollCount"], 2)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("credits_empty", issue_codes)
            self.assertIn("credits_duration_short", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("片尾字幕内容为空", markdown)
            self.assertIn("空片尾 / 过短片尾", markdown)

    def test_vn_baseline_quality_report_flags_missing_credits_for_ending_scene(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle_dir = Path(temp_dir) / "bundle"
            bundle_dir.mkdir(parents=True)
            game_data = {
                "project": {
                    "projectId": "native_missing_credits_quality_smoke",
                    "title": "Native Missing Credits Quality Smoke",
                    "entrySceneId": "scene_start",
                },
                "assets": {"assets": []},
                "characters": {"characters": []},
                "chapters": [
                    {
                        "id": "chapter_1",
                        "name": "Chapter 1",
                        "scenes": [
                            {
                                "id": "scene_start",
                                "name": "Start",
                                "blocks": [
                                    {
                                        "id": "choice_1",
                                        "type": "choice",
                                        "options": [{"text": "End", "gotoSceneId": "scene_end"}],
                                    }
                                ],
                            },
                            {
                                "id": "scene_end",
                                "name": "End",
                                "blocks": [{"id": "line_end", "type": "narration", "text": "The end."}],
                            },
                        ],
                    }
                ],
            }
            (bundle_dir / "game_data.json").write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")

            report = build_native_runtime_vn_baseline_quality_report(bundle_dir)

            self.assertEqual(report["metrics"]["endingSceneCount"], 1)
            self.assertEqual(report["metrics"]["creditsRollCount"], 0)
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("credits_missing", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("结局缺少片尾收束", markdown)


@unittest.skipIf(pygame is None, "pygame-ce is not installed")
class NativeRuntimeRenderSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original_home = os.environ.get("HOME")
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        os.environ["HOME"] = str(self.root / "home")
        self.bundle_dir = self.root / "bundle"
        self.bundle_dir.mkdir(parents=True)
        pygame.init()

    def tearDown(self) -> None:
        try:
            pygame.quit()
        finally:
            if self.original_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = self.original_home
            self.temp_dir.cleanup()

    def write_ui_asset(self, asset_id: str, color: tuple[int, int, int, int]) -> dict:
        asset_path = self.bundle_dir / "assets" / "ui" / f"{asset_id}.png"
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        surface = pygame.Surface((32, 32), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))
        pygame.draw.rect(surface, color, surface.get_rect(), border_radius=6)
        pygame.draw.rect(surface, (255, 255, 255, 210), surface.get_rect(), width=3, border_radius=6)
        pygame.image.save(surface, str(asset_path))
        return {
            "id": asset_id,
            "type": "ui",
            "name": asset_id.replace("_", " ").title(),
            "exportUrl": asset_path.relative_to(self.bundle_dir).as_posix(),
            "tags": [],
        }

    def write_video_asset(self) -> dict:
        asset_path = self.bundle_dir / "assets" / "video" / "opening.mp4"
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        asset_path.write_bytes(b"fake-video-data")
        return {
            "id": "opening_video",
            "type": "video",
            "name": "Opening Video",
            "exportUrl": asset_path.relative_to(self.bundle_dir).as_posix(),
            "tags": ["OP"],
        }

    def write_model_asset(self) -> dict:
        asset_path = self.bundle_dir / "assets" / "models" / "heroine.glb"
        asset_path.parent.mkdir(parents=True, exist_ok=True)
        asset_path.write_bytes(b"fake-model-data")
        return {
            "id": "heroine_model",
            "type": "model3d",
            "name": "Heroine 3D Model",
            "exportUrl": asset_path.relative_to(self.bundle_dir).as_posix(),
            "tags": ["3D"],
        }

    def write_game_data(self) -> Path:
        assets = [
            self.write_ui_asset(asset_id, (70 + index * 11, 92 + index * 7, 180, 235))
            for index, asset_id in enumerate(UI_ASSET_IDS)
        ]
        assets.append(self.write_video_asset())
        assets.append(self.write_model_asset())
        game_data = {
            "project": {
                "projectId": "native_render_smoke",
                "title": "Native Render Smoke",
                "entrySceneId": "scene_start",
                "resolution": {"width": 720, "height": 405},
                "runtimeSettings": {"formalSaveSlotCount": 12},
                "dialogBoxConfig": {
                    "preset": "moonlight",
                    "backgroundOpacity": 88,
                    "borderOpacity": 28,
                    "borderWidth": 1,
                },
                "gameUiConfig": {
                    "preset": "custom",
                    "titleBackgroundAssetId": "title_background",
                    "titleLogoAssetId": "title_logo",
                    "fontStyle": "serif",
                    "fontFamily": "Noto Sans CJK SC",
                    "panelFrameAssetId": "panel_frame",
                    "panelFrameOpacity": 68,
                    "panelFrameSlice": {"top": 8, "right": 8, "bottom": 8, "left": 8},
                    "buttonFrameAssetId": "button_frame",
                    "buttonHoverFrameAssetId": "button_hover_frame",
                    "buttonPressedFrameAssetId": "button_pressed_frame",
                    "buttonDisabledFrameAssetId": "button_disabled_frame",
                    "buttonFrameOpacity": 72,
                    "buttonFrameSlice": {"top": 8, "right": 8, "bottom": 8, "left": 8},
                    "saveSlotFrameAssetId": "save_slot_frame",
                    "systemPanelFrameAssetId": "system_panel_frame",
                    "uiOverlayAssetId": "ui_overlay",
                    "uiOverlayOpacity": 12,
                },
            },
            "assets": {"assets": assets},
            "characters": {
                "characters": [
                    {
                        "id": "heroine",
                        "displayName": "Heroine",
                        "defaultPosition": "center",
                        "presentation": {
                            "mode": "model3d",
                            "fallbackSpriteAssetId": "",
                            "model3d": {"modelAssetId": "heroine_model", "idleAnimation": "Idle"},
                        },
                        "expressions": [
                            {
                                "id": "expr_default",
                                "name": "Default",
                                "spriteAssetId": "",
                                "model3dExpression": "joy",
                                "model3dAnimation": "IdleHappy",
                            }
                        ],
                    }
                ]
            },
            "variables": {"variables": []},
            "chapters": [
                {
                    "id": "chapter_1",
                    "name": "Chapter 1",
                    "scenes": [
                        {
                            "id": "scene_start",
                            "name": "Opening",
                            "blocks": [
                                {"id": "block_bg", "type": "background", "assetId": "title_background"},
                                {
                                    "id": "block_line",
                                    "type": "dialogue",
                                    "speakerId": "heroine",
                                    "voiceAssetId": "voice_missing_line",
                                    "text": "Native Runtime render smoke.",
                                },
                                {
                                    "id": "block_choice",
                                    "type": "choice",
                                    "options": [
                                        {"text": "Continue", "gotoSceneId": ""},
                                        {"text": "Open archive", "gotoSceneId": ""},
                                    ],
                                },
                            ],
                        }
                    ],
                }
            ],
            "buildInfo": {
                "exportTargetLabel": "Headless Native Runtime",
                "runtimePreloadManifest": {
                    "formatVersion": 1,
                    "entrySceneId": "scene_start",
                    "summary": {
                        "totalEntries": 3,
                        "criticalEntries": 3,
                        "earlyEntries": 0,
                        "deferredEntries": 0,
                        "libraryEntries": 0,
                        "imageEntries": 2,
                        "audioEntries": 0,
                        "videoEntries": 1,
                    },
                    "entries": [
                        {
                            "assetId": "title_background",
                            "type": "ui",
                            "phase": "critical",
                            "priority": 100,
                            "preloadIndex": 1,
                            "reason": "title screen",
                        },
                        {
                            "assetId": "panel_frame",
                            "type": "ui",
                            "phase": "critical",
                            "priority": 92,
                            "preloadIndex": 2,
                            "reason": "system panels",
                        },
                        {
                            "assetId": "opening_video",
                            "type": "video",
                            "phase": "critical",
                            "priority": 84,
                            "preloadIndex": 3,
                            "reason": "opening movie",
                        },
                    ],
                },
            },
        }
        data_path = self.bundle_dir / "game_data.json"
        data_path.write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")
        return data_path

    def assert_screen_has_pixels(self, player: NativeRuntimePlayer) -> None:
        image_to_bytes = getattr(pygame.image, "tobytes", pygame.image.tostring)
        frame_bytes = image_to_bytes(player.screen, "RGB")
        self.assertTrue(any(channel != 0 for channel in frame_bytes))

    def test_runtime_preload_manifest_populates_native_caches(self) -> None:
        data_path = self.write_game_data()
        player = NativeRuntimePlayer(pygame, data_path)

        status = player.runtime_preload_status
        self.assertEqual(status["status"], "ready")
        self.assertEqual(status["totalEntries"], 3)
        self.assertEqual(status["imageEntries"], 2)
        self.assertEqual(status["loadedImageEntries"], 2)
        self.assertEqual(status["streamEntries"], 1)
        self.assertEqual(status["readyStreamEntries"], 1)
        self.assertEqual(status["loadedEntries"], 3)
        self.assertIn("title_background", player.image_cache)
        self.assertIn("panel_frame", player.image_cache)
        self.assertIn("资源预热：3/3", player.get_runtime_preload_status_line())
        self.assertIn("资源预热：3/3", player.status_message)

    def test_visual_save_slots_capture_persist_and_render_scene_thumbnails(self) -> None:
        data_path = self.write_game_data()
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="The system font .*", category=UserWarning)
            player = NativeRuntimePlayer(pygame, data_path)

        player.start_story_from_title()
        player.render()
        player.save_quick()
        player.save_formal_slot(0)

        quick_snapshot = player.save_store["quickSave"]
        formal_snapshot = player.save_store["formalSlots"][0]
        self.assertRegex(quick_snapshot["thumbnailKey"], r"^quick-[0-9a-f]{12}$")
        self.assertRegex(formal_snapshot["thumbnailKey"], r"^formal-0001-[0-9a-f]{12}$")
        quick_path = get_save_thumbnail_path(player.project_id, quick_snapshot["thumbnailKey"])
        formal_path = get_save_thumbnail_path(player.project_id, formal_snapshot["thumbnailKey"])
        self.assertTrue(quick_path.is_file())
        self.assertTrue(formal_path.is_file())
        self.assertGreater(quick_path.stat().st_size, 0)
        self.assertGreater(formal_path.stat().st_size, 0)

        status = build_save_thumbnail_status(player.save_store, player.project_id)
        self.assertEqual(status["availableCount"], 2)
        self.assertEqual(status["missingCount"], 0)
        self.assertIn("缩略图：2/2", player.build_save_summary_line())
        diagnostic_rows = player.get_runtime_diagnostics_report()["sections"][0]["rows"]
        thumbnail_row = next(row for row in diagnostic_rows if row["label"] == "存档缩略图")
        self.assertEqual(thumbnail_row["value"], "2/2")
        self.assertEqual(thumbnail_row["tone"], "ready")

        original_quick_key = quick_snapshot["thumbnailKey"]
        original_persist = player.persist_save_store

        def fail_persist() -> None:
            raise OSError("simulated full disk")

        player.persist_save_store = fail_persist
        player.save_quick()
        player.persist_save_store = original_persist
        self.assertEqual(player.save_store["quickSave"]["thumbnailKey"], original_quick_key)
        self.assertIn("原存档仍然保留", player.status_message)
        quick_files = list(quick_path.parent.glob("quick-*.png"))
        self.assertEqual([path.name for path in quick_files], [quick_path.name])

        player.open_save_dialog("load")
        player.render()
        self.assert_screen_has_pixels(player)
        slot_hotspots = [hotspot for hotspot in player.overlay_hotspots if hotspot.get("kind") == "slot"]
        footer_hotspots = [
            hotspot
            for hotspot in player.overlay_hotspots
            if hotspot.get("kind") in {"prev", "next", "switch", "close"}
        ]
        self.assertEqual(len(slot_hotspots), 2)
        self.assertEqual(len(footer_hotspots), 4)
        self.assertLess(
            max(hotspot["rect"].bottom for hotspot in slot_hotspots),
            min(hotspot["rect"].top for hotspot in footer_hotspots),
        )
        self.assertIsNotNone(player._load_image_file(quick_path))
        self.assertIsNotNone(player._load_image_file(formal_path))

    def test_controller_events_drive_title_reading_and_system_flows(self) -> None:
        data_path = self.write_game_data()
        player = NativeRuntimePlayer(pygame, data_path)

        self.assertEqual(player.overlay_mode, "title")
        self.assertEqual(player.title_menu_index, 0)
        self.assertTrue(player.handle_event(pygame.event.Event(pygame.JOYHATMOTION, hat=0, value=(0, -1))))
        self.assertEqual(player.title_menu_index, 1)
        self.assertTrue(player.handle_event(pygame.event.Event(pygame.JOYHATMOTION, hat=0, value=(0, -1))))
        self.assertEqual(player.title_menu_index, 1)
        repeat_started_at = player.controller_input_state["repeat"]["down"]["startedAt"]
        self.assertTrue(player.handle_controller_repeat(now_ms=repeat_started_at + 420))
        self.assertEqual(player.title_menu_index, 2)
        player.handle_event(pygame.event.Event(pygame.JOYHATMOTION, hat=0, value=(0, 0)))
        self.assertTrue(player.handle_controller_repeat())
        self.assertEqual(player.title_menu_index, 2)
        player.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, button=0))
        self.assertEqual(player.overlay_mode, "load")
        player.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, button=1))
        self.assertEqual(player.overlay_mode, "title")

        player.start_story_from_title()
        player.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, button=3))
        self.assertEqual(player.overlay_mode, "system")
        player.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, button=1))
        self.assertIsNone(player.overlay_mode)
        player.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, button=2))
        self.assertEqual(player.overlay_mode, "history")
        player.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, button=2))
        self.assertIsNone(player.overlay_mode)

        player.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, button=5))
        self.assertTrue(player.auto_play_enabled)
        player.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, button=6))
        self.assertTrue(player.skip_read_enabled)
        player.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, button=0))
        player.handle_event(pygame.event.Event(pygame.JOYBUTTONDOWN, button=0))
        self.assertIsNotNone(player.current_choices)
        player.handle_event(pygame.event.Event(pygame.JOYHATMOTION, hat=0, value=(0, 0)))
        player.handle_event(pygame.event.Event(pygame.JOYHATMOTION, hat=0, value=(0, -1)))
        self.assertEqual(player.current_choice_index, 1)
        diagnostic_rows = player.get_runtime_diagnostics_report()["sections"][0]["rows"]
        controller_row = next(row for row in diagnostic_rows if row["label"] == "手柄输入")
        self.assertEqual(controller_row["value"], "未连接")

    def test_pageup_rollback_restores_story_variables_and_stage_state(self) -> None:
        data_path = self.write_game_data()
        game_data = json.loads(data_path.read_text(encoding="utf-8"))
        game_data["variables"] = {
            "variables": [
                {"id": "affection", "name": "Affection", "type": "number", "defaultValue": 0}
            ]
        }
        blocks = game_data["chapters"][0]["scenes"][0]["blocks"]
        blocks[2:2] = [
            {"id": "block_var", "type": "variable_set", "variableId": "affection", "value": 9},
            {
                "id": "block_move",
                "type": "character_move",
                "characterId": "heroine",
                "position": "right",
                "durationMs": 0,
            },
            {
                "id": "block_filter",
                "type": "screen_filter",
                "action": "apply",
                "preset": "memory",
                "strength": "soft",
            },
        ]
        data_path.write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")
        player = NativeRuntimePlayer(pygame, data_path)

        player.start_story_from_title()
        self.assertEqual(player.current_block_index, 1)
        self.assertEqual(player.variable_state["affection"], 0)
        self.assertEqual(player.visible_characters["heroine"]["position"], "center")
        self.assertEqual(player.get_rollback_status()["availableSteps"], 0)

        player.reveal_current_line_immediately()
        player.advance_dialogue()
        self.assertEqual(player.current_block_index, 5)
        self.assertIsNotNone(player.current_choices)
        self.assertEqual(player.variable_state["affection"], 9)
        self.assertEqual(player.visible_characters["heroine"]["position"], "right")
        self.assertIsNotNone(player.screen_filter_effect)
        self.assertEqual(player.get_rollback_status()["availableSteps"], 1)

        handled = player.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_PAGEUP}))
        self.assertTrue(handled)
        self.assertEqual(player.current_block_index, 1)
        self.assertIsNone(player.current_choices)
        self.assertEqual(player.current_line["text"], "Native Runtime render smoke.")
        self.assertEqual(player.variable_state["affection"], 0)
        self.assertEqual(player.visible_characters["heroine"]["position"], "center")
        self.assertIsNone(player.screen_filter_effect)
        self.assertEqual(player.get_rollback_status()["availableSteps"], 0)
        self.assertIn("已回退到上一句", player.status_message)

    def test_native_runtime_renders_stage_image_layer_to_canvas(self) -> None:
        data_path = self.write_game_data()
        player = NativeRuntimePlayer(pygame, data_path)
        canvas = pygame.Surface((player.width, player.height), pygame.SRCALPHA)
        canvas.fill((0, 0, 0, 0))
        player.visible_stage_images = {
            "smoke_note": {
                "layerId": "smoke_note",
                "assetId": "title_logo",
                "plane": "front",
                "position": "right",
                "transform": {
                    "offsetX": -6,
                    "offsetY": 4,
                    "width": 38,
                    "opacity": 91,
                    "rotation": 8,
                    "layer": 4,
                    "flipX": True,
                },
            }
        }

        self.assertEqual(player.get_renderable_stage_image_items("back"), [])
        front_items = player.get_renderable_stage_image_items("front")
        self.assertEqual([item[0] for item in front_items], ["smoke_note"])
        player.render_stage_images(canvas, "front")

        rendered_bounds = canvas.get_bounding_rect(min_alpha=1)
        self.assertGreater(rendered_bounds.width, 0)
        self.assertGreater(rendered_bounds.width * rendered_bounds.height, 100)

    def test_text_wrapping_preserves_words_newlines_and_ellipsis(self) -> None:
        font = pygame.font.Font(None, 24)
        lines = wrap_text(font, "Hello world from Canvasia Engine\n第二行中文EnglishMix测试", 128)

        self.assertGreaterEqual(len(lines), 3)
        self.assertIn("Hello", lines[0])
        self.assertTrue(any("第二行" in line for line in lines))
        self.assertTrue(all(font.size(line)[0] <= 128 for line in lines if line))
        long_token_lines = wrap_text(font, "Supercalifragilisticexpialidocious", 64)
        self.assertGreater(len(long_token_lines), 1)
        self.assertTrue(all(font.size(line)[0] <= 64 for line in long_token_lines if line))

        clipped = ellipsize_text(font, "This sentence is intentionally too long for the dialogue box.", 120)
        self.assertTrue(clipped.endswith("…"))
        self.assertLessEqual(font.size(clipped)[0], 120)

    def test_optional_opencv_video_frame_loader_builds_surface(self) -> None:
        class FakeFrame:
            shape = (2, 3, 3)

            def tobytes(self) -> bytes:
                return bytes(
                    [
                        255,
                        0,
                        0,
                        0,
                        255,
                        0,
                        0,
                        0,
                        255,
                        255,
                        255,
                        255,
                        80,
                        120,
                        180,
                        16,
                        24,
                        32,
                    ]
                )

        class FakeCapture:
            def __init__(self, video_path: str) -> None:
                self.video_path = video_path
                self.seek_calls: list[tuple[int, float]] = []
                self.released = False

            def isOpened(self) -> bool:
                return True

            def set(self, prop: int, value: float) -> None:
                self.seek_calls.append((prop, value))

            def read(self) -> tuple[bool, FakeFrame]:
                return True, FakeFrame()

            def release(self) -> None:
                self.released = True

        class FakeCv2:
            CAP_PROP_POS_MSEC = 101
            COLOR_BGR2RGB = 202
            last_capture: FakeCapture | None = None

            @classmethod
            def VideoCapture(cls, video_path: str) -> FakeCapture:
                cls.last_capture = FakeCapture(video_path)
                return cls.last_capture

            @staticmethod
            def cvtColor(frame: FakeFrame, color_code: int) -> FakeFrame:
                self.assertEqual(color_code, FakeCv2.COLOR_BGR2RGB)
                return frame

        video_path = self.bundle_dir / "assets" / "video" / "preview.mp4"
        video_path.parent.mkdir(parents=True, exist_ok=True)
        video_path.write_bytes(b"fake-video-container")

        surface, status = load_opencv_video_frame_surface(pygame, video_path, 1.5, cv2_module=FakeCv2)

        self.assertEqual(status, "OpenCV 帧预览")
        self.assertIsNotNone(surface)
        self.assertEqual(surface.get_size(), (3, 2))
        self.assertIsNotNone(FakeCv2.last_capture)
        self.assertEqual(FakeCv2.last_capture.seek_calls, [(FakeCv2.CAP_PROP_POS_MSEC, 1500.0)])
        self.assertTrue(FakeCv2.last_capture.released)

    def test_optional_opencv_embedded_video_playback_advances_frames(self) -> None:
        class FakeFrame:
            shape = (2, 3, 3)

            def __init__(self, seed: int) -> None:
                self.seed = seed

            def tobytes(self) -> bytes:
                return bytes([(self.seed + index * 17) % 255 for index in range(18)])

        class FakeCapture:
            def __init__(self, video_path: str) -> None:
                self.video_path = video_path
                self.index = 0
                self.position_ms = 0.0
                self.released = False

            def isOpened(self) -> bool:
                return True

            def set(self, prop: int, value: float) -> None:
                if prop == FakeCv2.CAP_PROP_POS_MSEC:
                    self.position_ms = value

            def get(self, prop: int) -> float:
                if prop == FakeCv2.CAP_PROP_FPS:
                    return 10.0
                if prop == FakeCv2.CAP_PROP_FRAME_COUNT:
                    return 3.0
                if prop == FakeCv2.CAP_PROP_POS_MSEC:
                    return self.position_ms
                return 0.0

            def read(self) -> tuple[bool, FakeFrame | None]:
                if self.index >= 3:
                    return False, None
                self.index += 1
                self.position_ms = self.index * 100.0
                return True, FakeFrame(self.index * 40)

            def release(self) -> None:
                self.released = True

        class FakeCv2:
            CAP_PROP_POS_MSEC = 101
            CAP_PROP_FPS = 102
            CAP_PROP_FRAME_COUNT = 103
            COLOR_BGR2RGB = 202
            last_capture: FakeCapture | None = None

            @classmethod
            def VideoCapture(cls, video_path: str) -> FakeCapture:
                cls.last_capture = FakeCapture(video_path)
                return cls.last_capture

            @staticmethod
            def cvtColor(frame: FakeFrame, color_code: int) -> FakeFrame:
                return frame

        video_path = self.bundle_dir / "assets" / "video" / "embedded.mp4"
        video_path.parent.mkdir(parents=True, exist_ok=True)
        video_path.write_bytes(b"fake-video-container")

        playback = OpenCvEmbeddedVideoPlayback(
            pygame,
            video_path,
            start_time_seconds=0.0,
            end_time_seconds=0.2,
            cv2_module=FakeCv2,
        )

        opened, message = playback.open()
        self.assertTrue(opened, message)
        playback.play(0)
        playback.update(0)
        self.assertEqual(playback.status, "playing")
        self.assertIsNotNone(playback.current_surface)
        self.assertEqual(playback.current_surface.get_size(), (3, 2))
        playback.update(120)
        self.assertTrue(playback.finished)
        self.assertEqual(playback.status, "finished")
        self.assertEqual(playback.get_progress_ratio(), 1.0)
        self.assertIsNotNone(FakeCv2.last_capture)
        self.assertTrue(FakeCv2.last_capture.released)
        self.assertEqual(NATIVE_VIDEO_EMBEDDED_BACKEND_ID, "opencv_embedded_playback")

    def test_optional_pyav_synchronized_video_playback_uses_timestamps(self) -> None:
        class FakeVideoArray:
            shape = (2, 3, 3)

            def __init__(self, seed: int) -> None:
                self.seed = seed

            def tobytes(self) -> bytes:
                return bytes([(self.seed + index * 13) % 255 for index in range(18)])

        class FakeVideoFrame:
            time_base = Fraction(1, 1000)

            def __init__(self, pts: int, seed: int) -> None:
                self.pts = pts
                self.seed = seed

            def to_rgb(self) -> "FakeVideoFrame":
                return self

            def to_ndarray(self) -> FakeVideoArray:
                return FakeVideoArray(self.seed)

        class FakeAudioArray:
            def tobytes(self) -> bytes:
                return b"\x00\x01" * 2048

        class FakeAudioFrame:
            time_base = Fraction(1, 1000)
            sample_rate = 44100
            samples = 1024

            def __init__(self, pts: int) -> None:
                self.pts = pts

            def to_ndarray(self) -> FakeAudioArray:
                return FakeAudioArray()

        class FakeStream:
            def __init__(self, stream_type: str) -> None:
                self.type = stream_type

        class FakeStreams:
            def __init__(self) -> None:
                self.video = [FakeStream("video")]
                self.audio = [FakeStream("audio")]

        class FakeContainer:
            def __init__(self) -> None:
                self.streams = FakeStreams()
                self.seek_calls: list[int] = []
                self.closed = False

            def seek(self, offset: int, any_frame: bool = False, backward: bool = True) -> None:
                self.seek_calls.append(offset)

            def decode(self, stream: FakeStream):
                if stream.type == "audio":
                    yield FakeAudioFrame(0)
                    yield FakeAudioFrame(100)
                    return
                yield FakeVideoFrame(0, 20)
                yield FakeVideoFrame(100, 80)
                yield FakeVideoFrame(200, 140)

            def close(self) -> None:
                self.closed = True

        class FakeAv:
            opened: list[FakeContainer] = []

            @classmethod
            def open(cls, video_path: str) -> FakeContainer:
                container = FakeContainer()
                cls.opened.append(container)
                return container

        class BusyChannel:
            def get_busy(self) -> bool:
                return True

            def pause(self) -> None:
                return None

            def unpause(self) -> None:
                return None

            def stop(self) -> None:
                return None

        video_path = self.bundle_dir / "assets" / "video" / "pyav-sync.mp4"
        video_path.parent.mkdir(parents=True, exist_ok=True)
        video_path.write_bytes(b"fake-video-container")

        playback = PyAvSynchronizedVideoPlayback(
            pygame,
            video_path,
            start_time_seconds=0.0,
            end_time_seconds=0.22,
            av_module=FakeAv,
        )

        audio_bytes, audio_message = playback._decode_audio_buffer()
        self.assertTrue(audio_bytes, audio_message)
        opened, message = playback.open()
        self.assertTrue(opened, message)
        self.assertEqual(playback.backend_id, NATIVE_VIDEO_SYNC_BACKEND_ID)
        playback.play(0)
        playback.audio_channel = BusyChannel()
        playback.update(0)
        self.assertEqual(playback.status, "playing")
        self.assertIsNotNone(playback.current_surface)
        self.assertEqual(playback.current_surface.get_size(), (3, 2))
        playback.update(120)
        self.assertEqual(playback.status, "playing")
        self.assertIsNotNone(playback.current_surface)
        playback.update(240)
        self.assertTrue(playback.finished)
        self.assertEqual(playback.get_progress_ratio(), 1.0)
        self.assertGreaterEqual(len(FakeAv.opened), 3)

    def test_video_preview_probe_reports_ready_with_optional_backend(self) -> None:
        self.write_game_data()

        class FakeFrame:
            shape = (2, 3, 3)

            def tobytes(self) -> bytes:
                return bytes([255, 255, 255] * 6)

        class FakeCapture:
            def __init__(self, video_path: str) -> None:
                self.video_path = video_path

            def isOpened(self) -> bool:
                return True

            def set(self, prop: int, value: float) -> None:
                return None

            def read(self) -> tuple[bool, FakeFrame]:
                return True, FakeFrame()

            def release(self) -> None:
                return None

        class FakeCv2:
            CAP_PROP_POS_MSEC = 101
            COLOR_BGR2RGB = 202

            @staticmethod
            def VideoCapture(video_path: str) -> FakeCapture:
                return FakeCapture(video_path)

            @staticmethod
            def cvtColor(frame: FakeFrame, color_code: int) -> FakeFrame:
                return frame

        report = build_native_video_preview_probe_report(self.bundle_dir, pygame_module=pygame, cv2_module=FakeCv2)

        self.assertEqual(report["status"], "ready")
        self.assertEqual(report["summary"]["videoAssetCount"], 1)
        self.assertEqual(report["summary"]["successCount"], 1)
        self.assertEqual(report["entries"][0]["status"], "ready")
        self.assertEqual(report["entries"][0]["surfaceSize"], {"width": 3, "height": 2})

    def test_runtime_variables_are_normalized_when_applied_and_restored(self) -> None:
        data_path = self.write_game_data()
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        payload["variables"] = {
            "variables": [
                {"id": "var_score", "name": "Score", "type": "number", "defaultValue": "7", "min": 0, "max": 10},
                {"id": "var_flag", "name": "Flag", "type": "boolean", "defaultValue": "true"},
                {"id": "var_route", "name": "Route", "type": "string", "defaultValue": 12},
            ]
        }
        data_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="The system font .*", category=UserWarning)
            player = NativeRuntimePlayer(pygame, data_path)

        self.assertEqual(player.variable_state["var_score"], 7)
        self.assertIs(player.variable_state["var_flag"], True)
        self.assertEqual(player.variable_state["var_route"], "12")

        player.apply_variable_add({"variableId": "var_score", "value": "3"})
        self.assertEqual(player.variable_state["var_score"], 10)
        player.apply_variable_add({"variableId": "var_score", "value": "99"})
        self.assertEqual(player.variable_state["var_score"], 10)
        player.apply_variable_set({"variableId": "var_flag", "value": "false"})
        self.assertIs(player.variable_state["var_flag"], False)
        player.apply_variable_set({"variableId": "var_route", "value": 100})
        self.assertEqual(player.variable_state["var_route"], "100")
        player.apply_variable_add({"variableId": "var_route", "value": 5})
        self.assertEqual(player.variable_state["var_route"], "100")
        player.apply_variable_set({"variableId": "var_missing", "value": 1})
        self.assertNotIn("var_missing", player.variable_state)

        self.assertTrue(player.evaluate_when([{"variableId": "var_score", "operator": ">=", "value": "10"}]))
        self.assertTrue(player.evaluate_when([{"variableId": "var_flag", "operator": "==", "value": "false"}]))
        self.assertTrue(player.evaluate_when([{"variableId": "var_route", "operator": "==", "value": 100}]))
        self.assertTrue(player.evaluate_when([{"variableId": "var_route", "operator": "contains", "value": "10"}]))
        self.assertTrue(player.evaluate_when([{"variableId": "var_route", "operator": "not_contains", "value": "bad"}]))
        self.assertTrue(player.evaluate_when([{"variableId": "var_route", "operator": "starts_with", "value": "1"}]))
        self.assertTrue(player.evaluate_when([{"variableId": "var_route", "operator": "ends_with", "value": "00"}]))
        snapshot = player.build_save_snapshot("formal")
        self.assertIn("Score:10", snapshot["variableSummaryText"])
        self.assertIn("Flag:关", snapshot["variableSummaryText"])
        dialog_data = build_save_dialog_page_data(
            payload["project"],
            {"quickSave": snapshot, "formalSlots": [snapshot]},
            variables=payload["variables"]["variables"],
        )
        self.assertIn("Score:10", dialog_data["quickSave"]["variableSummaryText"])
        self.assertIn("Route:100", dialog_data["visibleSlots"][0]["variableSummaryText"])
        write_project_auto_resume("native_render_smoke", snapshot)
        resume_item = next(item for item in player.get_title_menu_items() if item["key"] == "resume")
        self.assertIn("Score:10", resume_item["subtitle"])
        player.render_auto_resume_overlay()
        self.assert_screen_has_pixels(player)

        player.restore_from_snapshot(
            {
                "sceneId": "scene_start",
                "sceneName": "Opening",
                "blockIndex": 0,
                "variableState": {
                    "var_score": "42.5",
                    "var_flag": "yes",
                    "var_route": 404,
                    "ghost": "ignored",
                },
                "stageBackgroundAssetId": None,
                "visibleCharacters": {},
                "currentBgmAssetId": None,
                "finished": False,
            }
        )

        self.assertEqual(player.variable_state["var_score"], 10)
        self.assertIs(player.variable_state["var_flag"], True)
        self.assertEqual(player.variable_state["var_route"], "404")
        self.assertNotIn("ghost", player.variable_state)

    def test_choice_continue_target_stays_in_scene_and_applies_effects(self) -> None:
        data_path = self.write_game_data()
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        payload["variables"] = {
            "variables": [
                {"id": "var_score", "name": "Score", "type": "number", "defaultValue": 0},
            ]
        }
        payload["chapters"][0]["scenes"][0]["blocks"] = [
            {
                "id": "choice_continue",
                "type": "choice",
                "options": [
                    {
                        "id": "stay_here",
                        "text": "继续听她说",
                        "gotoSceneId": "__continue__",
                        "effects": [{"type": "variable_add", "variableId": "var_score", "value": 2}],
                    }
                ],
            },
            {"id": "line_after_choice", "type": "narration", "text": "选择后的下一句。"},
        ]
        data_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="The system font .*", category=UserWarning)
            player = NativeRuntimePlayer(pygame, data_path)

        player.start_story_from_title()
        self.assertEqual(player.get_current_scene()["id"], "scene_start")
        self.assertEqual(player.current_block_index, 0)
        self.assertEqual(player.current_choices[0]["gotoSceneId"], "__continue__")

        player.choose_current_option(0)

        self.assertEqual(player.get_current_scene()["id"], "scene_start")
        self.assertEqual(player.current_block_index, 1)
        self.assertIsNone(player.current_choices)
        self.assertEqual(player.variable_state["var_score"], 2)
        self.assertEqual(player.current_line["text"], "选择后的下一句。")

    def test_choice_availability_hides_locks_and_keeps_runtime_recoverable(self) -> None:
        data_path = self.write_game_data()
        payload = json.loads(data_path.read_text(encoding="utf-8"))
        payload["variables"] = {
            "variables": [
                {"id": "affection", "name": "Affection", "type": "number", "defaultValue": 1},
                {"id": "has_key", "name": "Key", "type": "boolean", "defaultValue": False},
            ]
        }
        payload["chapters"][0]["scenes"][0]["blocks"] = [
            {
                "id": "choice_gate",
                "type": "choice",
                "options": [
                    {
                        "id": "secret",
                        "text": "秘密路线",
                        "choiceAvailabilityMode": "hide_when_false",
                        "choiceAvailabilityWhen": [{"variableId": "affection", "operator": ">=", "value": 5}],
                    },
                    {
                        "id": "locked",
                        "text": "打开门",
                        "choiceAvailabilityMode": "disable_when_false",
                        "choiceLockedReason": "需要钥匙",
                        "choiceAvailabilityWhen": [{"variableId": "has_key", "operator": "==", "value": True}],
                    },
                ],
            },
            {"id": "after_gate", "type": "narration", "text": "安全继续后的下一句。"},
        ]
        data_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="The system font .*", category=UserWarning)
            player = NativeRuntimePlayer(pygame, data_path)

        player.start_story_from_title()
        self.assertEqual([option["id"] for option in player.current_choices], ["locked", "__canvasia_choice_safety_continue__"])
        self.assertEqual(player.current_choice_index, 1)
        player.choose_current_option(0)
        self.assertEqual(player.current_block_index, 0)
        self.assertEqual(player.status_message, "需要钥匙")
        player.choose_current_option(1)
        self.assertEqual(player.current_block_index, 1)
        self.assertEqual(player.current_line["text"], "安全继续后的下一句。")

    def test_native_runtime_renders_ui_skin_overlays_headlessly(self) -> None:
        data_path = self.write_game_data()
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="The system font .*", category=UserWarning)
            player = NativeRuntimePlayer(pygame, data_path)

        self.assertIn("主题", player.get_system_menu_item_description("settings"))
        self.assertIn("正式存档", player.get_system_menu_item_description("load"))
        self.assertIn("路线预取", player.get_system_menu_item_description("diagnostics"))
        self.assertEqual(player.get_character_presentation_mode_label(player.characters_by_id["heroine"]), "3D 模型")
        self.assertEqual(player.get_character_model_asset_label(player.characters_by_id["heroine"]), "Heroine 3D Model")
        self.assertIn(
            "3D joy / IdleHappy",
            player.get_character_expression_binding_label(player.characters_by_id["heroine"], "expr_default"),
        )
        model_preview = player.get_character_model_preview_report(player.characters_by_id["heroine"], "expr_default")
        self.assertEqual(model_preview["status"], "ready")
        self.assertIn("GLB 单文件", model_preview["dependencyHealth"]["label"])
        self.assertIn("3D 模型 预览桥：资源完整", player.get_character_model_preview_lines(player.characters_by_id["heroine"], "expr_default"))

        render_steps = [
            lambda: player.render(),
            lambda: (player.open_save_dialog("save"), player.render()),
            lambda: (player.open_save_dialog("load"), player.render()),
            lambda: (player.open_system_menu(), player.render()),
            lambda: (player.open_help_overlay(), player.render()),
            lambda: (player.open_settings_overlay(), player.render()),
            lambda: (player.open_profile_overlay(), player.render()),
            lambda: (player.open_auto_resume_overlay(), player.render()),
            lambda: (player.open_diagnostics_overlay(), player.render()),
            lambda: (player.open_archive_overlay("chapters"), player.render()),
        ]
        for render_step in render_steps:
            render_step()
            self.assert_screen_has_pixels(player)

        player.start_story_from_title()
        player.render()
        self.assert_screen_has_pixels(player)
        player.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_F12}))
        screenshot_files = list(get_runtime_screenshot_dir().glob("native_render_smoke-*.png"))
        self.assertEqual(len(screenshot_files), 1)
        self.assertGreater(screenshot_files[0].stat().st_size, 0)
        player.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_F2}))
        self.assertEqual(player.overlay_mode, "help")
        help_sections = player.get_help_overlay_sections()
        self.assertIn("当前状态", [section["title"] for section in help_sections])
        self.assertTrue(any("主题：" in line for section in help_sections for line in section["lines"]))
        self.assertIn("settings", [action["key"] for action in player.get_help_quick_actions()])
        player.render()
        self.assert_screen_has_pixels(player)
        history_target = next(
            target
            for target in player.overlay_hotspots
            if target.get("kind") == "help-action" and target.get("value") == "history"
        )
        player.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": history_target["rect"].center}))
        self.assertEqual(player.overlay_mode, "history")
        player.close_overlay(preserve_status=True)
        player.open_help_overlay()
        player.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_s}))
        self.assertEqual(player.overlay_mode, "settings")
        player.close_overlay(preserve_status=True)
        player.open_system_menu()
        player.system_menu_index = next(index for index, item in enumerate(SYSTEM_MENU_ITEMS) if item[0] == "diagnostics")
        player.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))
        self.assertEqual(player.overlay_mode, "diagnostics")
        diagnostics_report = player.get_runtime_diagnostics_report()
        self.assertIn("路线预取", [section["title"] for section in diagnostics_report["sections"]])
        player.render()
        self.assert_screen_has_pixels(player)
        player.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))
        self.assertIsNone(player.overlay_mode)
        player.open_help_overlay()
        player.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))
        self.assertIsNone(player.overlay_mode)
        player.handle_event(
            pygame.event.Event(
                pygame.KEYDOWN,
                {"key": pygame.K_SLASH, "unicode": "?", "mod": pygame.KMOD_SHIFT},
            )
        )
        self.assertEqual(player.overlay_mode, "help")
        player.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_F2}))
        self.assertIsNone(player.overlay_mode)
        player.open_settings_overlay()
        player.render()
        self.assert_screen_has_pixels(player)
        player.adjust_runtime_setting("textScalePercent", 1)
        self.assertEqual(player.runtime_settings["textScalePercent"], 110)
        self.assertEqual(player.active_text_scale_percent, 110)
        player.adjust_runtime_setting("dialogBoxOpacityPercent", -1)
        self.assertEqual(player.runtime_settings["dialogBoxOpacityPercent"], 80)
        player.adjust_runtime_setting("autoPlayWaitForVoice", 1)
        self.assertEqual(player.runtime_settings["autoPlayWaitForVoice"], "on")
        player.adjust_runtime_setting("visualComfort", 1)
        self.assertEqual(player.runtime_settings["visualComfort"], "gentle")
        self.assertEqual(player.get_setting_value_label("visualComfort"), "柔和模式")
        voice_mixer_entries = player.get_voice_mixer_entries()
        self.assertGreaterEqual(len(voice_mixer_entries), 1)
        player.open_voice_mixer_overlay()
        player.render()
        self.assert_screen_has_pixels(player)
        selected_voice_profile_id = str(player.get_selected_voice_mixer_entry()["id"])
        player.adjust_voice_mixer_profile(-1)
        self.assertEqual(player.runtime_settings["voiceMix"][selected_voice_profile_id]["volume"], 95)
        player.toggle_selected_voice_mixer_mute()
        self.assertTrue(player.runtime_settings["voiceMix"][selected_voice_profile_id]["muted"])
        player.reset_selected_voice_mixer_profile()
        self.assertNotIn(selected_voice_profile_id, player.runtime_settings["voiceMix"])
        player.close_overlay(preserve_status=True)
        self.assertEqual(player.overlay_mode, "settings")
        player.open_key_bindings_overlay()
        player.key_binding_index = next(
            index for index, action in enumerate(RUNTIME_KEY_BINDING_ACTIONS) if action["id"] == "hide"
        )
        player.render()
        self.assert_screen_has_pixels(player)
        player.begin_selected_key_binding_capture()
        player.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_b, "mod": 0}))
        self.assertEqual(player.runtime_settings["keyBindings"]["hide"], "KeyB")
        self.assertFalse(player.key_binding_capture_action)
        player.close_overlay(preserve_status=True)
        self.assertEqual(player.overlay_mode, "settings")
        player.close_overlay(preserve_status=True)
        player.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_b, "mod": 0}))
        self.assertTrue(player.ui_hidden)
        player.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_b, "mod": 0}))
        self.assertFalse(player.ui_hidden)
        player.open_key_bindings_overlay()
        player.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_r, "mod": 0}))
        self.assertEqual(player.runtime_settings["keyBindings"]["hide"], "KeyU")
        player.close_overlay(preserve_status=True)
        player.close_overlay(preserve_status=True)
        if player.current_line:
            class BusyVoiceChannel:
                def get_busy(self) -> bool:
                    return True

            player.current_voice_channel = BusyVoiceChannel()
            player.reveal_current_line_immediately()
            player.auto_play_enabled = True
            player.auto_play_deadline_ms = 123
            player.update_flow_assist()
            self.assertEqual(player.auto_play_deadline_ms, 0)
            player.current_voice_channel = None
            player.auto_play_enabled = False
        self.assertGreaterEqual(len(player.text_history), 1)
        self.assertTrue(player.font_source_status)
        history_item = player.get_selected_text_history_item()
        self.assertIsNotNone(history_item)
        self.assertEqual(history_item["voiceAssetId"], "voice_missing_line")
        player.play_selected_history_voice()
        self.assertIn("语音素材不可用", player.status_message)
        read_key = str(player.current_line.get("historyKey") or "")
        self.assertTrue(read_key)
        player.mark_current_line_read()
        self.assertIn(read_key, load_project_archive_progress("native_render_smoke")["readTextKeys"])
        snapshot = player.build_save_snapshot("formal")
        self.assertGreaterEqual(len(snapshot["textHistory"]), 1)
        player.text_history = []
        player.text_history_seen_keys = set()
        player.restore_from_snapshot(snapshot)
        self.assertGreaterEqual(len(player.text_history), 1)
        self.assertEqual(player.get_selected_text_history_item()["voiceAssetId"], "voice_missing_line")
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="The system font .*", category=UserWarning)
            second_player = NativeRuntimePlayer(pygame, data_path)
        self.assertIn(read_key, second_player.read_text_keys)

        player.open_text_history_overlay()
        player.render()
        self.assert_screen_has_pixels(player)
        previous_history_index = player.history_scroll_index
        player.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, {"y": -1}))
        self.assertGreaterEqual(player.history_scroll_index, previous_history_index)
        player.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 3, "pos": (0, 0)}))
        self.assertIsNone(player.overlay_mode)
        player.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 3, "pos": (0, 0)}))
        self.assertEqual(player.overlay_mode, "system")
        player.close_overlay(preserve_status=True)
        player.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, {"y": 1}))
        self.assertEqual(player.overlay_mode, "history")
        player.close_overlay(preserve_status=True)

        player.toggle_auto_play()
        self.assertTrue(player.auto_play_enabled)
        player.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 2, "pos": (0, 0)}))
        self.assertTrue(player.ui_hidden)
        self.assertFalse(player.auto_play_enabled)
        player.render()
        self.assert_screen_has_pixels(player)
        player.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (0, 0)}))
        self.assertFalse(player.ui_hidden)
        player.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_u}))
        self.assertTrue(player.ui_hidden)
        player.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_u}))
        self.assertFalse(player.ui_hidden)

        player.toggle_auto_play()
        self.assertTrue(player.auto_play_enabled)
        self.assertFalse(player.skip_read_enabled)
        player.toggle_skip_read()
        self.assertTrue(player.skip_read_enabled)
        self.assertFalse(player.auto_play_enabled)
        player.stop_flow_assist()
        self.assertFalse(player.auto_play_enabled)
        self.assertFalse(player.skip_read_enabled)

        player.overlay_mode = None
        player.current_choices = [
            {"text": "Continue", "gotoSceneId": ""},
            {"text": "Open archive", "gotoSceneId": ""},
        ]
        player.current_choice_index = 1
        player.render()
        self.assert_screen_has_pixels(player)

        video_path = self.bundle_dir / "assets" / "video" / "opening.mp4"
        player.current_choices = None
        player.current_line = {
            "type": "video_play",
            "speakerName": "视频",
            "text": "Video card",
            "videoAssetId": "opening_video",
            "videoAssetPath": str(video_path),
            "videoTitle": "Opening Video",
            "videoFileName": video_path.name,
            "videoStartTimeSeconds": 1.5,
            "videoEndTimeSeconds": 4.0,
            "videoClipLabel": "0:01.5 -> 0:04",
            "videoFit": "contain",
            "videoVolume": 75,
            "videoSkippable": False,
            "videoPreviewMode": "cinematic_bridge_card",
            "videoOpened": False,
        }
        player.render()
        self.assert_screen_has_pixels(player)
        self.assertFalse(player.can_advance_current_line())
        player.current_line["videoOpened"] = True
        self.assertTrue(player.can_advance_current_line())

        selected_entry = player.get_selected_archive_entry()
        if selected_entry:
            player.open_archive_detail(selected_entry)
            player.render()
            self.assert_screen_has_pixels(player)

    def test_native_runtime_applies_background_and_character_transitions(self) -> None:
        data_path = self.write_game_data()
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="The system font .*", category=UserWarning)
            player = NativeRuntimePlayer(pygame, data_path)

        player.stage_background_asset_id = "title_logo"
        player.start_background_transition(
            "title_background",
            {"transition": "fade", "transitionDurationMs": 420},
        )
        self.assertIsNotNone(player.background_transition)
        self.assertEqual(player.background_transition["previousAssetId"], "title_background")
        self.assertEqual(player.background_transition["nextAssetId"], "title_logo")
        self.assertEqual(player.background_transition["durationMs"], 420)
        player.render_background()
        self.assert_screen_has_pixels(player)

        show_transition = player.get_character_transition_state(
            {"transition": "slide_left", "transitionDurationMs": 420},
            "in",
        )
        self.assertIsNotNone(show_transition)
        player.visible_characters["heroine"] = {
            "expressionId": "expr_default",
            "position": "center",
            "stage": {"scale": 100, "opacity": 100},
            "transition": show_transition,
        }
        player.render_characters()
        self.assert_screen_has_pixels(player)

        hide_transition = player.get_character_transition_state(
            {"transition": "rise", "transitionDurationMs": 420},
            "out",
        )
        self.assertIsNotNone(hide_transition)
        player.leaving_characters["heroine"] = {
            "expressionId": "expr_default",
            "position": "center",
            "stage": {"scale": 100, "opacity": 100},
            "transition": hide_transition,
        }
        self.assertGreaterEqual(len(player.get_renderable_character_items()), 2)
        player.render_characters()
        self.assert_screen_has_pixels(player)

        snapshot_visible = player.get_snapshot_visible_characters()
        self.assertNotIn("transition", snapshot_visible["heroine"])
        self.assertNotIn("__leaving", snapshot_visible["heroine"])

        now_ms = player.get_runtime_ticks_ms()
        player.background_transition["startedAtMs"] = now_ms - 1000
        player.background_transition["durationMs"] = 1
        player.leaving_characters["heroine"]["transition"]["startedAtMs"] = now_ms - 1000
        player.leaving_characters["heroine"]["transition"]["durationMs"] = 1
        player.visible_characters["heroine"]["transition"]["startedAtMs"] = now_ms - 1000
        player.visible_characters["heroine"]["transition"]["durationMs"] = 1
        player.prune_finished_native_transitions()

        self.assertIsNone(player.background_transition)
        self.assertEqual(player.leaving_characters, {})
        self.assertNotIn("transition", player.visible_characters["heroine"])

        player.runtime_settings["visualComfort"] = "gentle"
        player.start_background_transition(
            "title_background",
            {"transition": "fade", "transitionDurationMs": 420},
        )
        self.assertEqual(player.background_transition["durationMs"], 231)
        gentle_transition = player.get_character_transition_state(
            {"transition": "slide_left", "transitionDurationMs": 420},
            "in",
        )
        self.assertEqual(gentle_transition["durationMs"], 231)

        player.runtime_settings["visualComfort"] = "static"
        player.start_background_transition(
            "title_background",
            {"transition": "fade", "transitionDurationMs": 420},
        )
        self.assertIsNone(player.background_transition)
        self.assertIsNone(
            player.get_character_transition_state(
                {"transition": "slide_left", "transitionDurationMs": 420},
                "in",
            )
        )
        player.screen_shake_effect = {"intensity": "heavy"}
        self.assertEqual(player.get_stage_shake_offset(), (0, 0))

    def test_long_dialogue_expands_panel_and_marks_overflow(self) -> None:
        data_path = self.write_game_data()
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="The system font .*", category=UserWarning)
            player = NativeRuntimePlayer(pygame, data_path)

        long_text = (
            "This is a deliberately long native Runtime dialogue line with English words, "
            "中文长句，以及 mixed typography. "
            * 8
        )
        player.current_line = {
            "type": "dialogue",
            "speakerId": "heroine",
            "text": long_text,
            "voiceAssetId": "",
            "blockLabel": "台词",
        }
        player.start_current_line_display(long_text)
        player.reveal_current_line_immediately()
        layout = player.build_dialogue_layout(player.current_line)

        self.assertGreater(layout["minHeight"], 176)
        self.assertGreater(len(layout["fullLines"]), 4)
        player.render_dialogue()
        self.assert_screen_has_pixels(player)


if __name__ == "__main__":
    unittest.main()
