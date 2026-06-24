from __future__ import annotations

import json
import os
import tempfile
import unittest
import warnings
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
    NATIVE_VIDEO_EMBEDDED_BACKEND_ID,
    NATIVE_VIDEO_SYNC_BACKEND_ID,
    VN_BASELINE_QUALITY_MARKDOWN_NAME,
    VN_BASELINE_QUALITY_REPORT_NAME,
    NativeRuntimePlayer,
    OpenCvEmbeddedVideoPlayback,
    PyAvSynchronizedVideoPlayback,
    build_acceptance_automated_checks,
    build_native_runtime_vn_baseline_quality_report,
    build_vn_baseline_quality_doctor_check,
    build_save_dialog_page_data,
    build_native_video_preview_probe_report,
    ellipsize_text,
    get_native_typewriter_step_delay_ms,
    get_next_typewriter_index,
    get_runtime_screenshot_dir,
    get_typewriter_punctuation_pause_ms,
    load_project_archive_progress,
    load_opencv_video_frame_surface,
    render_native_runtime_vn_baseline_quality_markdown,
    write_native_runtime_vn_baseline_quality_reports,
    write_project_auto_resume,
    wrap_text,
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
            issue_codes = {issue["code"] for issue in report["issues"]}
            self.assertIn("route_target_missing", issue_codes)
            self.assertIn("unreachable_scene", issue_codes)

            markdown = render_native_runtime_vn_baseline_quality_markdown(report)
            self.assertIn("路线跳转目标缺失", markdown)
            self.assertIn("入口不可达场景", markdown)

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
            "buildInfo": {"exportTargetLabel": "Headless Native Runtime"},
        }
        data_path = self.bundle_dir / "game_data.json"
        data_path.write_text(json.dumps(game_data, ensure_ascii=False), encoding="utf-8")
        return data_path

    def assert_screen_has_pixels(self, player: NativeRuntimePlayer) -> None:
        image_to_bytes = getattr(pygame.image, "tobytes", pygame.image.tostring)
        frame_bytes = image_to_bytes(player.screen, "RGB")
        self.assertTrue(any(channel != 0 for channel in frame_bytes))

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

    def test_native_runtime_renders_ui_skin_overlays_headlessly(self) -> None:
        data_path = self.write_game_data()
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="The system font .*", category=UserWarning)
            player = NativeRuntimePlayer(pygame, data_path)

        self.assertIn("主题", player.get_system_menu_item_description("settings"))
        self.assertIn("正式存档", player.get_system_menu_item_description("load"))
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
