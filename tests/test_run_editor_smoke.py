from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
import plistlib
import shutil
import subprocess
import sys
import tempfile
import tarfile
import unittest
from unittest import mock
from pathlib import Path

import openai_asset_generation
import run_editor


def build_upload_payload(name: str, raw: bytes) -> dict:
    return {
        "name": name,
        "dataBase64": base64.b64encode(raw).decode("utf-8"),
    }


def build_fake_wav_bytes() -> bytes:
    return (
        b"RIFF"
        b"\x24\x00\x00\x00"
        b"WAVE"
        b"fmt "
        b"\x10\x00\x00\x00"
        b"\x01\x00"
        b"\x01\x00"
        b"\x44\xac\x00\x00"
        b"\x88\x58\x01\x00"
        b"\x02\x00"
        b"\x10\x00"
        b"data"
        b"\x00\x00\x00\x00"
    )


def build_fake_png_bytes() -> bytes:
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
    )


def build_fake_glb_bytes(payload: dict) -> bytes:
    json_chunk = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    json_chunk += b" " * ((4 - len(json_chunk) % 4) % 4)
    chunk_type_json = 0x4E4F534A
    total_length = 12 + 8 + len(json_chunk)
    return (
        b"glTF"
        + (2).to_bytes(4, "little")
        + total_length.to_bytes(4, "little")
        + len(json_chunk).to_bytes(4, "little")
        + chunk_type_json.to_bytes(4, "little")
        + json_chunk
    )


def create_fake_runtime_archive(archive_path: Path, platform_key: str) -> Path:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "python"
        if platform_key == run_editor.EDITOR_PLATFORM_WINDOWS:
            executable = root / "python.exe"
        else:
            executable = root / "bin" / "python3"
        executable.parent.mkdir(parents=True, exist_ok=True)
        executable.write_text("fake-python", encoding="utf-8")
        if platform_key != run_editor.EDITOR_PLATFORM_WINDOWS:
            executable.chmod(0o755)

        with tarfile.open(archive_path, "w:gz") as archive:
            archive.add(root, arcname="python")
    return archive_path


def create_fake_nwjs_runtime_dir(runtime_dir: Path, platform_key: str) -> Path:
    config = run_editor.get_nwjs_runtime_config(platform_key)
    runtime_dir.mkdir(parents=True, exist_ok=True)

    if platform_key == run_editor.NWJS_GAME_PLATFORM_MACOS:
        app_bundle = runtime_dir / str(config.get("appBundleName") or "nwjs.app")
        (app_bundle / "Contents" / "MacOS").mkdir(parents=True, exist_ok=True)
        (app_bundle / "Contents" / "Resources").mkdir(parents=True, exist_ok=True)
        executable_path = app_bundle / "Contents" / "MacOS" / "nwjs"
        executable_path.write_text("fake-nwjs", encoding="utf-8")
        executable_path.chmod(0o755)
        with (app_bundle / "Contents" / "Info.plist").open("wb") as plist_file:
            plistlib.dump({"CFBundleExecutable": "nwjs", "CFBundleName": "nwjs"}, plist_file)
        return runtime_dir

    for file_name in config.get("requiredFiles") or []:
        file_path = runtime_dir / str(file_name)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text("fake-runtime", encoding="utf-8")
        if file_path.name in {"nw", "nw.exe"}:
            file_path.chmod(0o755)
    for dir_name in config.get("requiredDirs") or []:
        (runtime_dir / str(dir_name)).mkdir(parents=True, exist_ok=True)
    return runtime_dir


def create_fake_iscc_script(script_path: Path) -> Path:
    script_path.write_text(
        """#!/bin/sh
set -eu
output_dir=""
output_base="CanvasiaEngineEditorSetup"
for arg in "$@"; do
  case "$arg" in
    /O*) output_dir="${arg#/O}" ;;
    /F*) output_base="${arg#/F}" ;;
  esac
done
if [ -z "$output_dir" ]; then
  output_dir="$(pwd)"
fi
mkdir -p "$output_dir"
printf 'fake-windows-installer' > "$output_dir/$output_base.exe"
""",
        encoding="utf-8",
    )
    script_path.chmod(0o755)
    return script_path


def create_fake_signtool_script(script_path: Path) -> Path:
    script_path.write_text(
        """#!/bin/sh
set -eu
exit 0
""",
        encoding="utf-8",
    )
    script_path.chmod(0o755)
    return script_path


class RunEditorSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_root = Path(self.temp_dir.name)
        self.sample_dir = self.test_root / "template_project"
        shutil.copytree(run_editor.ROOT_DIR / "template_project", self.sample_dir)
        self.projects_dir = self.test_root / "projects"
        self.exports_dir = self.test_root / "exports"
        self.runtime_cache_dir = self.test_root / ".export_runtime_cache"
        self.local_runtime_dirs = [
            self.test_root / "desktop_runtime",
            self.test_root / "desktop_runtime" / "windows",
        ]
        self.fake_nwjs_runtime_dirs = {
            run_editor.NWJS_GAME_PLATFORM_WINDOWS: create_fake_nwjs_runtime_dir(
                self.test_root / "fake_nwjs_windows_runtime",
                run_editor.NWJS_GAME_PLATFORM_WINDOWS,
            ),
            run_editor.NWJS_GAME_PLATFORM_MACOS: create_fake_nwjs_runtime_dir(
                self.test_root / "fake_nwjs_macos_runtime",
                run_editor.NWJS_GAME_PLATFORM_MACOS,
            ),
            run_editor.NWJS_GAME_PLATFORM_LINUX: create_fake_nwjs_runtime_dir(
                self.test_root / "fake_nwjs_linux_runtime",
                run_editor.NWJS_GAME_PLATFORM_LINUX,
            ),
        }
        self.portable_runtime_archives = {
            run_editor.EDITOR_PLATFORM_MACOS: create_fake_runtime_archive(
                self.test_root / "fake_macos_runtime.tar.gz",
                run_editor.EDITOR_PLATFORM_MACOS,
            ),
            run_editor.EDITOR_PLATFORM_WINDOWS: create_fake_runtime_archive(
                self.test_root / "fake_windows_runtime.tar.gz",
                run_editor.EDITOR_PLATFORM_WINDOWS,
            ),
            run_editor.EDITOR_PLATFORM_LINUX: create_fake_runtime_archive(
                self.test_root / "fake_linux_runtime.tar.gz",
                run_editor.EDITOR_PLATFORM_LINUX,
            ),
        }
        self.fake_iscc = create_fake_iscc_script(self.test_root / "fake_iscc.sh")
        self.fake_signtool = create_fake_signtool_script(self.test_root / "fake_signtool.sh")

        self.original_globals = {
            "PROJECTS_DIR": run_editor.PROJECTS_DIR,
            "SAMPLE_PROJECT_DIR": run_editor.SAMPLE_PROJECT_DIR,
            "EXPORTS_DIR": run_editor.EXPORTS_DIR,
            "EXPORT_RUNTIME_CACHE_DIR": run_editor.EXPORT_RUNTIME_CACHE_DIR,
            "LOCAL_NWJS_RUNTIME_DIRS": run_editor.LOCAL_NWJS_RUNTIME_DIRS,
            "TEMPLATE_DIR": run_editor.TEMPLATE_DIR,
            "DATA_DIR": run_editor.DATA_DIR,
            "CHAPTERS_DIR": run_editor.CHAPTERS_DIR,
            "PROJECT_PATH": run_editor.PROJECT_PATH,
            "CURRENT_PROJECT_INFO": dict(run_editor.CURRENT_PROJECT_INFO),
            "HAS_SELECTED_PROJECT": run_editor.HAS_SELECTED_PROJECT,
        }
        self.original_env = {
            run_editor.get_portable_runtime_override_env_var(platform_key): os.environ.get(
                run_editor.get_portable_runtime_override_env_var(platform_key)
            )
            for platform_key in self.portable_runtime_archives
        }
        self.original_env.update(
            {
                run_editor.get_nwjs_runtime_dir_override_env_var(platform_key): os.environ.get(
                    run_editor.get_nwjs_runtime_dir_override_env_var(platform_key)
                )
                for platform_key in self.fake_nwjs_runtime_dirs
            }
        )
        self.original_env[run_editor.EDITOR_WINDOWS_ISCC_ENV] = os.environ.get(run_editor.EDITOR_WINDOWS_ISCC_ENV)
        self.original_env[run_editor.EDITOR_WINDOWS_SIGNTOOL_ENV] = os.environ.get(run_editor.EDITOR_WINDOWS_SIGNTOOL_ENV)
        self.original_env[run_editor.EDITOR_WINDOWS_CERT_SUBJECT_ENV] = os.environ.get(
            run_editor.EDITOR_WINDOWS_CERT_SUBJECT_ENV
        )

        run_editor.PROJECTS_DIR = self.projects_dir
        run_editor.SAMPLE_PROJECT_DIR = self.sample_dir
        run_editor.EXPORTS_DIR = self.exports_dir
        run_editor.EXPORT_RUNTIME_CACHE_DIR = self.runtime_cache_dir
        run_editor.LOCAL_NWJS_RUNTIME_DIRS = self.local_runtime_dirs
        run_editor.TEMPLATE_DIR = self.sample_dir
        run_editor.DATA_DIR = self.sample_dir / "data"
        run_editor.CHAPTERS_DIR = run_editor.DATA_DIR / "chapters"
        run_editor.PROJECT_PATH = self.sample_dir / "project.json"
        run_editor.CURRENT_PROJECT_INFO = {
            "projectId": run_editor.SAMPLE_PROJECT_ID,
            "kind": "sample",
            "projectDir": str(self.sample_dir),
        }
        run_editor.HAS_SELECTED_PROJECT = False
        for platform_key, archive_path in self.portable_runtime_archives.items():
            os.environ[run_editor.get_portable_runtime_override_env_var(platform_key)] = str(archive_path)
        for platform_key, runtime_dir in self.fake_nwjs_runtime_dirs.items():
            os.environ[run_editor.get_nwjs_runtime_dir_override_env_var(platform_key)] = str(runtime_dir)
        os.environ[run_editor.EDITOR_WINDOWS_ISCC_ENV] = str(self.fake_iscc)
        os.environ[run_editor.EDITOR_WINDOWS_SIGNTOOL_ENV] = str(self.fake_signtool)
        os.environ[run_editor.EDITOR_WINDOWS_CERT_SUBJECT_ENV] = "Canvasia Engine Project"

    def tearDown(self) -> None:
        run_editor.PROJECTS_DIR = self.original_globals["PROJECTS_DIR"]
        run_editor.SAMPLE_PROJECT_DIR = self.original_globals["SAMPLE_PROJECT_DIR"]
        run_editor.EXPORTS_DIR = self.original_globals["EXPORTS_DIR"]
        run_editor.EXPORT_RUNTIME_CACHE_DIR = self.original_globals["EXPORT_RUNTIME_CACHE_DIR"]
        run_editor.LOCAL_NWJS_RUNTIME_DIRS = self.original_globals["LOCAL_NWJS_RUNTIME_DIRS"]
        run_editor.TEMPLATE_DIR = self.original_globals["TEMPLATE_DIR"]
        run_editor.DATA_DIR = self.original_globals["DATA_DIR"]
        run_editor.CHAPTERS_DIR = self.original_globals["CHAPTERS_DIR"]
        run_editor.PROJECT_PATH = self.original_globals["PROJECT_PATH"]
        run_editor.CURRENT_PROJECT_INFO = self.original_globals["CURRENT_PROJECT_INFO"]
        run_editor.HAS_SELECTED_PROJECT = self.original_globals["HAS_SELECTED_PROJECT"]
        for env_key, env_value in self.original_env.items():
            if env_value is None:
                os.environ.pop(env_key, None)
            else:
                os.environ[env_key] = env_value
        self.temp_dir.cleanup()

    def test_write_json_keeps_original_file_when_dump_fails(self) -> None:
        target_path = self.test_root / "atomic_write.json"
        target_path.write_text('{"ok": true}\n', encoding="utf-8")

        with mock.patch.object(run_editor.json, "dump", side_effect=RuntimeError("simulated json failure")):
            with self.assertRaisesRegex(RuntimeError, "simulated json failure"):
                run_editor.write_json(target_path, {"ok": False})

        self.assertEqual(target_path.read_text(encoding="utf-8"), '{"ok": true}\n')
        self.assertFalse(list(self.test_root.glob(".atomic_write.json.*.tmp")))

    def assert_export_manifest_has_subtle_engine_signature(self, manifest: dict) -> None:
        self.assertEqual(manifest["engine"]["signature"], run_editor.EXPORT_ENGINE_SIGNATURE)
        self.assertEqual(manifest["protection"]["profile"], run_editor.EXPORT_PROTECTION_PROFILE)
        self.assertEqual(manifest["protection"]["provenanceFile"], run_editor.EXPORT_PROVENANCE_FILE_NAME)
        self.assertFalse(manifest["protection"]["visibleWatermark"])
        self.assertIn("file_fingerprints", manifest["protection"]["checks"])
        self.assertEqual(
            manifest["protection"]["verifiers"]["python"],
            run_editor.EXPORT_PROVENANCE_VERIFIER_SCRIPT_NAME,
        )
        self.assertNotIn("Made with", json.dumps(manifest, ensure_ascii=False))

    def assert_export_provenance_file(self, export_result: dict, expected_paths: set[str]) -> dict:
        provenance_path = Path(export_result["provenancePath"])
        self.assertTrue(provenance_path.is_file())
        payload = json.loads(provenance_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["profile"], run_editor.EXPORT_PROTECTION_PROFILE)
        self.assertEqual(payload["engine"]["signature"], run_editor.EXPORT_ENGINE_SIGNATURE)
        self.assertFalse(payload["protection"]["visibleWatermark"])
        self.assertTrue(payload["protection"]["notEncryption"])
        self.assertRegex(payload["summary"]["seal"], r"^[0-9a-f]{64}$")
        self.assertEqual(export_result["provenanceSeal"], payload["summary"]["seal"])
        provenance_paths = {entry["path"] for entry in payload["files"]}
        self.assertTrue(expected_paths.issubset(provenance_paths))
        self.assertIn(run_editor.EXPORT_PROVENANCE_VERIFIER_SCRIPT_NAME, provenance_paths)
        self.assertIn(run_editor.EXPORT_PROVENANCE_MAC_VERIFIER_NAME, provenance_paths)
        self.assertIn(run_editor.EXPORT_PROVENANCE_LINUX_VERIFIER_NAME, provenance_paths)
        self.assertIn(run_editor.EXPORT_PROVENANCE_WINDOWS_VERIFIER_NAME, provenance_paths)
        manifest_entry = next(entry for entry in payload["files"] if entry["path"] == "export_manifest.json")
        manifest_digest = hashlib.sha256((provenance_path.parent / "export_manifest.json").read_bytes()).hexdigest()
        self.assertEqual(manifest_entry["sha256"], manifest_digest)
        self.assertTrue(Path(export_result["provenanceVerifierPath"]).is_file())
        self.assertTrue(Path(export_result["provenanceVerifierMacPath"]).is_file())
        self.assertTrue(Path(export_result["provenanceVerifierLinuxPath"]).is_file())
        self.assertTrue(Path(export_result["provenanceVerifierWindowsPath"]).is_file())
        verifier_result = subprocess.run(
            [sys.executable, str(Path(export_result["provenanceVerifierPath"])), str(provenance_path.parent)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(verifier_result.returncode, 0, verifier_result.stdout + verifier_result.stderr)
        verifier_payload = json.loads(verifier_result.stdout)
        self.assertEqual(verifier_payload["status"], "pass")
        self.assertTrue(verifier_payload["sealMatched"])
        self.assertNotIn("Made with", json.dumps(payload, ensure_ascii=False))
        return payload

    def assert_export_provenance_verifier_detects_tamper(self, export_result: dict, relative_path: str) -> None:
        target_path = Path(export_result["buildPath"]) / relative_path
        self.assertTrue(target_path.is_file())
        with target_path.open("a", encoding="utf-8") as file_handle:
            file_handle.write("\n/* tamper probe */\n")
        verifier_result = subprocess.run(
            [sys.executable, str(Path(export_result["provenanceVerifierPath"])), str(Path(export_result["buildPath"]))],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(verifier_result.returncode, 0)
        verifier_payload = json.loads(verifier_result.stdout)
        self.assertEqual(verifier_payload["status"], "fail")
        self.assertIn(relative_path, {item["path"] for item in verifier_payload["changedFiles"]})

    def create_blank_project_with_chapter(self) -> tuple[dict, dict]:
        run_editor.create_blank_project("自动化测试项目")
        chapter_result = run_editor.create_chapter("第一章", "开场")
        return run_editor.get_current_project_summary(), chapter_result

    def save_scene_with_blocks(self, chapter_id: str, scene: dict, blocks: list[dict]) -> dict:
        updated_scene = copy.deepcopy(scene)
        updated_scene["blocks"] = blocks
        run_editor.save_scene(chapter_id, updated_scene["id"], updated_scene)
        return updated_scene

    def test_starter_kit_bootstraps_first_scene_for_playable_demo(self) -> None:
        self.create_blank_project_with_chapter()

        result = run_editor.create_starter_kit(
            character_name="小葵",
            background_name="放学后的教室",
            bgm_name="第一天的风",
        )

        self.assertEqual(result["createdLabels"], ["第一个角色", "第一张背景", "第一首 BGM"])
        self.assertFalse(any(result["starterOverview"].values()))
        self.assertTrue(result["sceneBootstrap"]["applied"])
        self.assertEqual(
            result["sceneBootstrap"]["insertedLabels"],
            ["BGM 卡片", "背景卡片", "角色出场卡片", "第一句角色台词"],
        )
        self.assertEqual(len(result["sceneBootstrap"]["insertedBlockIds"]), 4)

        bundle = run_editor.load_project_bundle()
        first_scene = bundle["chapters"][0]["scenes"][0]
        first_blocks = first_scene["blocks"][:4]
        self.assertEqual([block["type"] for block in first_blocks], ["music_play", "background", "character_show", "dialogue"])
        self.assertEqual(result["sceneBootstrap"]["insertedBlockIds"], [block["id"] for block in first_blocks])

        created_assets_by_type = {asset["type"]: asset for asset in result["createdAssets"]}
        created_character = result["createdCharacter"]
        self.assertEqual(first_blocks[0]["assetId"], created_assets_by_type["bgm"]["id"])
        self.assertEqual(first_blocks[0]["fadeInMs"], 600)
        self.assertEqual(first_blocks[1]["assetId"], created_assets_by_type["background"]["id"])
        self.assertEqual(first_blocks[1]["transition"], "fade")
        self.assertEqual(first_blocks[2]["characterId"], created_character["id"])
        self.assertEqual(first_blocks[2]["expressionId"], "expr_default")
        self.assertEqual(first_blocks[3]["speakerId"], created_character["id"])
        self.assertIn("开始", first_blocks[3]["text"])
        self.assertEqual(first_scene["blocks"][4]["type"], "narration")

    def test_project_creation_scene_save_and_settings(self) -> None:
        project_summary, chapter_result = self.create_blank_project_with_chapter()

        self.assertEqual(project_summary["title"], "自动化测试项目")
        self.assertEqual(project_summary["editorMode"], "beginner")

        updated_scene = self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {
                    "id": "block_001",
                    "type": "dialogue",
                    "speakerId": "heroine",
                    "expressionId": "",
                    "text": "你好，欢迎来到自动化测试。",
                }
            ],
        )

        result = run_editor.save_project_settings(
            resolution={"width": 1920, "height": 1080},
            release_version="1.2.3-beta",
            editor_mode="advanced",
            runtime_settings={"formalSaveSlotCount": 60},
            dialog_box_config={
                "preset": "transparent",
                "shape": "capsule",
                "widthPercent": 82,
                "minHeight": 132,
                "backgroundColor": "#10243a",
                "backgroundOpacity": 12,
                "borderColor": "#6fdfff",
                "borderOpacity": 0,
                "textColor": "#f0f6ff",
                "speakerColor": "#ffffff",
                "panelAssetFit": "contain",
                "anchor": "center",
                "offsetXPercent": 12,
                "offsetYPercent": -8,
            },
            game_ui_config={
                "preset": "minimal",
                "layoutPreset": "cinematic",
                "titleLayout": "poster",
                "fontStyle": "serif",
                "fontFamily": "Noto Serif CJK SC",
                "fontAssetId": "font_story_serif",
                "surfaceStyle": "minimal",
                "brandMode": "hidden",
                "sidePanelMode": "hidden",
                "sidePanelPosition": "left",
                "topbarPosition": "bottom",
                "hudPosition": "bottom-right",
                "titleCardAnchor": "right",
                "titleCardOffsetXPercent": -7,
                "titleCardOffsetYPercent": 5,
                "layoutGap": 26,
                "sidePanelWidth": 356,
                "backgroundColor": "#05070c",
                "backgroundAccentColor": "#ffffff",
                "panelColor": "#080a10",
                "panelOpacity": 48,
                "textColor": "#f7f7f7",
                "mutedTextColor": "#c6c8cf",
                "accentColor": "#ffffff",
                "accentAltColor": "#aeb5c6",
                "buttonTextColor": "#101216",
                "borderColor": "#ffffff",
                "borderOpacity": 16,
                "cornerRadius": 10,
                "backdropBlur": 2,
                "stageVignette": 20,
                "motionIntensity": 10,
                "titleBackgroundAssetId": "asset_title_bg",
                "titleBackgroundFit": "contain",
                "titleBackgroundOpacity": 55,
                "titleLogoAssetId": "asset_title_logo",
                "panelFrameAssetId": "asset_panel_frame",
                "panelFrameOpacity": 41,
                "panelFrameSlice": {"top": 12, "right": 18, "bottom": 20, "left": 14},
                "buttonFrameAssetId": "asset_button_frame",
                "buttonHoverFrameAssetId": "asset_button_hover",
                "buttonPressedFrameAssetId": "asset_button_pressed",
                "buttonDisabledFrameAssetId": "asset_button_disabled",
                "buttonFrameOpacity": 36,
                "buttonFrameSlice": {"top": 8, "right": 16, "bottom": 10, "left": 16},
                "saveSlotFrameAssetId": "asset_save_frame",
                "systemPanelFrameAssetId": "asset_system_frame",
                "uiOverlayAssetId": "asset_overlay_grid",
                "uiOverlayOpacity": 9,
            },
            particle_custom_presets=[
                {
                    "name": "暴雪测试",
                    "config": {
                        "action": "start",
                        "preset": "snow",
                        "density": 48,
                    },
                }
            ],
            variables={
                "variables": [
                    {
                        "id": "var_affection",
                        "name": "好感度",
                        "type": "number",
                        "defaultValue": 0,
                    },
                    {
                        "id": "var_route",
                        "name": "路线标记",
                        "type": "string",
                        "defaultValue": "common",
                    },
                ]
            },
        )

        bundle = run_editor.load_project_bundle()
        saved_scene = bundle["chapters"][0]["scenes"][0]
        saved_project = bundle["project"]

        self.assertEqual(saved_scene["id"], updated_scene["id"])
        self.assertEqual(saved_scene["blocks"][0]["text"], "你好，欢迎来到自动化测试。")
        self.assertEqual(result["project"]["releaseVersion"], "1.2.3-beta")
        self.assertEqual(saved_project["editorMode"], "advanced")
        self.assertEqual(saved_project["resolution"]["width"], 1920)
        self.assertEqual(saved_project["runtimeSettings"]["formalSaveSlotCount"], 60)
        self.assertEqual(saved_project["dialogBoxConfig"]["preset"], "transparent")
        self.assertEqual(saved_project["dialogBoxConfig"]["shape"], "capsule")
        self.assertEqual(saved_project["dialogBoxConfig"]["widthPercent"], 82)
        self.assertEqual(saved_project["dialogBoxConfig"]["backgroundColor"], "#10243a")
        self.assertEqual(saved_project["dialogBoxConfig"]["anchor"], "center")
        self.assertEqual(saved_project["dialogBoxConfig"]["offsetXPercent"], 12)
        self.assertEqual(saved_project["dialogBoxConfig"]["offsetYPercent"], -8)
        self.assertEqual(saved_project["gameUiConfig"]["preset"], "minimal")
        self.assertEqual(saved_project["gameUiConfig"]["layoutPreset"], "cinematic")
        self.assertEqual(saved_project["gameUiConfig"]["titleLayout"], "poster")
        self.assertEqual(saved_project["gameUiConfig"]["fontStyle"], "serif")
        self.assertEqual(saved_project["gameUiConfig"]["fontFamily"], "Noto Serif CJK SC")
        self.assertEqual(saved_project["gameUiConfig"]["fontAssetId"], "font_story_serif")
        self.assertEqual(saved_project["gameUiConfig"]["brandMode"], "hidden")
        self.assertEqual(saved_project["gameUiConfig"]["sidePanelMode"], "hidden")
        self.assertEqual(saved_project["gameUiConfig"]["sidePanelPosition"], "left")
        self.assertEqual(saved_project["gameUiConfig"]["topbarPosition"], "bottom")
        self.assertEqual(saved_project["gameUiConfig"]["hudPosition"], "bottom-right")
        self.assertEqual(saved_project["gameUiConfig"]["titleCardAnchor"], "right")
        self.assertEqual(saved_project["gameUiConfig"]["titleCardOffsetXPercent"], -7)
        self.assertEqual(saved_project["gameUiConfig"]["titleCardOffsetYPercent"], 5)
        self.assertEqual(saved_project["gameUiConfig"]["layoutGap"], 26)
        self.assertEqual(saved_project["gameUiConfig"]["sidePanelWidth"], 356)
        self.assertEqual(saved_project["gameUiConfig"]["panelOpacity"], 48)
        self.assertEqual(saved_project["gameUiConfig"]["titleBackgroundAssetId"], "asset_title_bg")
        self.assertEqual(saved_project["gameUiConfig"]["titleBackgroundFit"], "contain")
        self.assertEqual(saved_project["gameUiConfig"]["titleBackgroundOpacity"], 55)
        self.assertEqual(saved_project["gameUiConfig"]["titleLogoAssetId"], "asset_title_logo")
        self.assertEqual(saved_project["gameUiConfig"]["panelFrameAssetId"], "asset_panel_frame")
        self.assertEqual(saved_project["gameUiConfig"]["panelFrameOpacity"], 41)
        self.assertEqual(saved_project["gameUiConfig"]["panelFrameSlice"], {"top": 12, "right": 18, "bottom": 20, "left": 14})
        self.assertEqual(saved_project["gameUiConfig"]["buttonFrameAssetId"], "asset_button_frame")
        self.assertEqual(saved_project["gameUiConfig"]["buttonHoverFrameAssetId"], "asset_button_hover")
        self.assertEqual(saved_project["gameUiConfig"]["buttonPressedFrameAssetId"], "asset_button_pressed")
        self.assertEqual(saved_project["gameUiConfig"]["buttonDisabledFrameAssetId"], "asset_button_disabled")
        self.assertEqual(saved_project["gameUiConfig"]["buttonFrameOpacity"], 36)
        self.assertEqual(saved_project["gameUiConfig"]["buttonFrameSlice"], {"top": 8, "right": 16, "bottom": 10, "left": 16})
        self.assertEqual(saved_project["gameUiConfig"]["saveSlotFrameAssetId"], "asset_save_frame")
        self.assertEqual(saved_project["gameUiConfig"]["systemPanelFrameAssetId"], "asset_system_frame")
        self.assertEqual(saved_project["gameUiConfig"]["uiOverlayAssetId"], "asset_overlay_grid")
        self.assertEqual(saved_project["gameUiConfig"]["uiOverlayOpacity"], 9)
        self.assertEqual(saved_project["particleCustomPresets"][0]["name"], "暴雪测试")
        self.assertEqual(bundle["variables"]["variables"][0]["id"], "var_affection")
        self.assertEqual(bundle["variables"]["variables"][1]["defaultValue"], "common")

    def test_project_center_hides_internal_packaging_smoke_projects_and_keeps_mode_choice(self) -> None:
        hidden_result = run_editor.create_blank_project("原生 Runtime 打包烟测", editor_mode="advanced")
        visible_result = run_editor.create_blank_project("公开测试项目", editor_mode="advanced")

        project_center = run_editor.get_project_center_payload()
        project_titles = [project["title"] for project in project_center["projects"]]

        self.assertEqual(hidden_result["project"]["editorMode"], "advanced")
        self.assertEqual(visible_result["project"]["editorMode"], "advanced")
        self.assertNotIn("原生 Runtime 打包烟测", project_titles)
        self.assertIn("公开测试项目", project_titles)

    def test_project_doctor_repairs_safe_structure_issues(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()
        second_scene = run_editor.create_scene(chapter_result["chapterId"], "第二场")
        chapter_path = run_editor.CHAPTERS_DIR / f"{chapter_result['chapterId']}.json"
        chapter_doc = run_editor.read_json(chapter_path)
        chapter_doc["sceneOrder"] = ["missing_scene", second_scene["sceneId"], second_scene["sceneId"]]
        run_editor.write_json(chapter_path, chapter_doc)

        project_doc = run_editor.read_json(run_editor.PROJECT_PATH)
        project_doc["entrySceneId"] = "missing_entry"
        project_doc["chapterOrder"] = ["ghost_chapter", chapter_result["chapterId"], chapter_result["chapterId"]]
        run_editor.write_json(run_editor.PROJECT_PATH, project_doc)

        result = run_editor.repair_project_doctor()
        repaired_project = run_editor.read_json(run_editor.PROJECT_PATH)
        repaired_chapter = run_editor.read_json(chapter_path)
        repair_codes = {item["code"] for item in result["repairs"]}
        repair_by_code = {item["code"]: item for item in result["repairs"]}

        self.assertTrue(result["changed"])
        self.assertEqual(result["requestedCodes"], ["entry_scene", "chapter_order", "scene_order"])
        self.assertEqual(repair_codes, {"entry_scene", "chapter_order", "scene_order"})
        self.assertEqual(repaired_project["entrySceneId"], second_scene["sceneId"])
        self.assertEqual(repaired_project["chapterOrder"], [chapter_result["chapterId"]])
        self.assertEqual(
            repaired_chapter["sceneOrder"],
            [second_scene["sceneId"], chapter_result["sceneId"]],
        )
        self.assertIn("移除重复章节引用 1 个", repair_by_code["chapter_order"]["detail"])
        self.assertIn("移除重复场景引用 1 个", repair_by_code["scene_order"]["detail"])

    def test_project_doctor_dry_run_previews_without_writing(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()
        second_scene = run_editor.create_scene(chapter_result["chapterId"], "第二场")
        chapter_path = run_editor.CHAPTERS_DIR / f"{chapter_result['chapterId']}.json"
        chapter_doc = run_editor.read_json(chapter_path)
        chapter_doc["sceneOrder"] = ["missing_scene", second_scene["sceneId"], second_scene["sceneId"]]
        run_editor.write_json(chapter_path, chapter_doc)

        project_doc = run_editor.read_json(run_editor.PROJECT_PATH)
        project_doc["entrySceneId"] = "missing_entry"
        project_doc["chapterOrder"] = ["ghost_chapter", chapter_result["chapterId"], chapter_result["chapterId"]]
        run_editor.write_json(run_editor.PROJECT_PATH, project_doc)

        result = run_editor.repair_project_doctor(dry_run=True)
        previewed_project = run_editor.read_json(run_editor.PROJECT_PATH)
        previewed_chapter = run_editor.read_json(chapter_path)
        repair_codes = {item["code"] for item in result["repairs"]}

        self.assertFalse(result["changed"])
        self.assertTrue(result["wouldChange"])
        self.assertTrue(result["dryRun"])
        self.assertEqual(result["requestedCodes"], ["entry_scene", "chapter_order", "scene_order"])
        self.assertEqual(repair_codes, {"entry_scene", "chapter_order", "scene_order"})
        self.assertEqual(previewed_project["entrySceneId"], "missing_entry")
        self.assertEqual(previewed_project["chapterOrder"], ["ghost_chapter", chapter_result["chapterId"], chapter_result["chapterId"]])
        self.assertEqual(previewed_chapter["sceneOrder"], ["missing_scene", second_scene["sceneId"], second_scene["sceneId"]])

    def test_project_doctor_clears_stale_chapter_order_when_no_chapters_exist(self) -> None:
        run_editor.create_blank_project("空章节修复测试")
        project_doc = run_editor.read_json(run_editor.PROJECT_PATH)
        project_doc["chapterOrder"] = ["deleted_chapter"]
        run_editor.write_json(run_editor.PROJECT_PATH, project_doc)

        result = run_editor.repair_project_doctor(["chapter_order"])
        repaired_project = run_editor.read_json(run_editor.PROJECT_PATH)

        self.assertTrue(result["changed"])
        self.assertEqual(repaired_project["chapterOrder"], [])
        self.assertEqual(result["repairs"][0]["code"], "chapter_order")
        self.assertIn("移除无效章节引用 1 个", result["repairs"][0]["detail"])

    def test_project_doctor_deduplicates_order_lists_without_other_damage(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()
        second_scene = run_editor.create_scene(chapter_result["chapterId"], "第二场")
        chapter_path = run_editor.CHAPTERS_DIR / f"{chapter_result['chapterId']}.json"
        chapter_doc = run_editor.read_json(chapter_path)
        chapter_doc["sceneOrder"] = [
            chapter_result["sceneId"],
            chapter_result["sceneId"],
            second_scene["sceneId"],
        ]
        run_editor.write_json(chapter_path, chapter_doc)

        project_doc = run_editor.read_json(run_editor.PROJECT_PATH)
        project_doc["chapterOrder"] = [chapter_result["chapterId"], chapter_result["chapterId"]]
        run_editor.write_json(run_editor.PROJECT_PATH, project_doc)

        result = run_editor.repair_project_doctor(["chapter_order", "scene_order"])
        repaired_project = run_editor.read_json(run_editor.PROJECT_PATH)
        repaired_chapter = run_editor.read_json(chapter_path)
        repair_by_code = {item["code"]: item for item in result["repairs"]}

        self.assertTrue(result["changed"])
        self.assertEqual(repaired_project["chapterOrder"], [chapter_result["chapterId"]])
        self.assertEqual(repaired_chapter["sceneOrder"], [chapter_result["sceneId"], second_scene["sceneId"]])
        self.assertIn("移除重复章节引用 1 个", repair_by_code["chapter_order"]["detail"])
        self.assertIn("移除重复场景引用 1 个", repair_by_code["scene_order"]["detail"])

    def test_project_doctor_ignores_unknown_repair_codes(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()
        project_doc = run_editor.read_json(run_editor.PROJECT_PATH)
        project_doc["entrySceneId"] = "missing_entry"
        run_editor.write_json(run_editor.PROJECT_PATH, project_doc)

        result = run_editor.repair_project_doctor(["unknown_code"])
        repaired_project = run_editor.read_json(run_editor.PROJECT_PATH)

        self.assertFalse(result["changed"])
        self.assertFalse(result["wouldChange"])
        self.assertEqual(result["requestedCodes"], [])
        self.assertEqual(result["ignoredCodes"], ["unknown_code"])
        self.assertEqual(result["repairs"], [])
        self.assertEqual(repaired_project["entrySceneId"], "missing_entry")

        mixed_result = run_editor.repair_project_doctor(["entry_scene", "unknown_code"], dry_run=True)
        mixed_project = run_editor.read_json(run_editor.PROJECT_PATH)

        self.assertFalse(mixed_result["changed"])
        self.assertTrue(mixed_result["wouldChange"])
        self.assertEqual(mixed_result["requestedCodes"], ["entry_scene"])
        self.assertEqual(mixed_result["ignoredCodes"], ["unknown_code"])
        self.assertEqual([repair["code"] for repair in mixed_result["repairs"]], ["entry_scene"])
        self.assertEqual(mixed_project["entrySceneId"], "missing_entry")

    def test_character_presentation_can_bind_live2d_and_model3d_assets(self) -> None:
        self.create_blank_project_with_chapter()
        sprite_asset = run_editor.import_assets(
            "sprite",
            [build_upload_payload("fallback.png", build_fake_png_bytes())],
        )["assets"][0]
        live2d_asset = run_editor.import_assets(
            "live2d",
            [
                build_upload_payload(
                    "hero.model3.json",
                    json.dumps(
                        {
                            "Version": 3,
                            "FileReferences": {
                                "Moc": "hero.moc3",
                                "Textures": ["textures/texture_00.png"],
                                "Motions": {"Idle": [{"File": "motions/idle.motion3.json"}]},
                            },
                        }
                    ).encode("utf-8"),
                )
            ],
        )["assets"][0]
        live2d_source_path = run_editor.resolve_asset_source_path(live2d_asset["path"])
        self.assertIsNotNone(live2d_source_path)
        assert live2d_source_path is not None
        (live2d_source_path.parent / "textures").mkdir(parents=True, exist_ok=True)
        (live2d_source_path.parent / "motions").mkdir(parents=True, exist_ok=True)
        (live2d_source_path.parent / "hero.moc3").write_bytes(b"fake-moc3")
        (live2d_source_path.parent / "textures" / "texture_00.png").write_bytes(build_fake_png_bytes())
        (live2d_source_path.parent / "motions" / "idle.motion3.json").write_text("{}", encoding="utf-8")
        model3d_asset = run_editor.import_assets(
            "model3d",
            [
                build_upload_payload(
                    "hero.gltf",
                    json.dumps(
                        {
                            "asset": {"version": "2.0"},
                            "buffers": [{"uri": "hero.bin"}],
                            "images": [{"uri": "textures/body.png"}],
                        }
                    ).encode("utf-8"),
                )
            ],
        )["assets"][0]
        model3d_source_path = run_editor.resolve_asset_source_path(model3d_asset["path"])
        self.assertIsNotNone(model3d_source_path)
        assert model3d_source_path is not None
        (model3d_source_path.parent / "textures").mkdir(parents=True, exist_ok=True)
        (model3d_source_path.parent / "hero.bin").write_bytes(b"fake-bin")
        (model3d_source_path.parent / "textures" / "body.png").write_bytes(build_fake_png_bytes())
        run_editor.write_json(
            run_editor.DATA_DIR / "characters.json",
            {
                "characters": [
                    {
                        "id": "char_hero",
                        "displayName": "高级角色",
                        "defaultSpriteId": sprite_asset["id"],
                        "expressions": [
                            {"id": "expr_default", "name": "默认", "spriteAssetId": sprite_asset["id"]},
                            {"id": "expr_smile", "name": "微笑", "spriteAssetId": sprite_asset["id"]},
                        ],
                    }
                ]
            },
        )

        result = run_editor.update_character_presentation(
            "char_hero",
            {
                "mode": "model3d",
                "fallbackSpriteAssetId": sprite_asset["id"],
                "live2d": {"modelAssetId": live2d_asset["id"], "blink": True, "breath": True, "lipSync": True},
                "model3d": {"modelAssetId": model3d_asset["id"], "idleAnimation": "Idle"},
            },
            [
                {
                    "expressionId": "expr_default",
                    "layerAssetIds": [sprite_asset["id"]],
                    "live2dExpression": "smile",
                    "live2dMotion": "idle_01",
                    "model3dExpression": "joy",
                    "model3dAnimation": "IdleHappy",
                }
            ],
        )

        self.assertEqual(result["character"]["presentation"]["mode"], "model3d")
        self.assertEqual(result["character"]["presentation"]["model3d"]["modelAssetId"], model3d_asset["id"])
        self.assertEqual(result["character"]["expressions"][0]["live2dExpression"], "smile")
        self.assertEqual(result["character"]["expressions"][0]["model3dAnimation"], "IdleHappy")
        self.assertIn("角色3D 模型入口：高级角色", run_editor.collect_asset_usages(model3d_asset["id"]))
        self.assertIn("角色差分图层：高级角色 / 默认", run_editor.collect_asset_usages(sprite_asset["id"]))
        self.assertEqual(run_editor.choose_smart_asset_type("hero.model3.json"), "live2d")
        self.assertEqual(run_editor.choose_smart_asset_type("smile.exp3.json"), "live2d")
        self.assertEqual(run_editor.choose_smart_asset_type("hero.vrm"), "model3d")
        self.assertEqual(
            run_editor.get_asset_export_suffix({"type": "live2d", "path": "assets/live2d/hero.model3.json"}, None),
            ".model3.json",
        )
        export_result = run_editor.export_native_runtime_build()
        release_check_payload = json.loads(
            (Path(export_result["buildPath"]) / run_editor.NATIVE_RUNTIME_RELEASE_CHECK_NAME).read_text(encoding="utf-8")
        )
        issue_codes = {issue.get("code") for issue in release_check_payload["issues"]}
        exported_game_data = json.loads(
            (Path(export_result["buildPath"]) / "game_data.json").read_text(encoding="utf-8")
        )
        model_preview_description = subprocess.run(
            [
                sys.executable,
                str(Path(export_result["buildPath"]) / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--describe-model-preview",
                str(export_result["buildPath"]),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(model_preview_description.returncode, 0, model_preview_description.stdout + model_preview_description.stderr)
        model_preview_payload = json.loads(model_preview_description.stdout)
        self.assertEqual(model_preview_payload["summary"]["advancedCharacterCount"], 1)
        self.assertEqual(model_preview_payload["entries"][0]["status"], "ready")
        self.assertEqual(model_preview_payload["entries"][0]["dependencyHealth"]["status"], "ready")
        self.assertTrue(model_preview_payload["entries"][0]["expressionMapping"]["incomplete"])
        exported_live2d = next(
            asset for asset in exported_game_data["assets"]["assets"] if asset["id"] == live2d_asset["id"]
        )
        live2d_export_path = Path(export_result["buildPath"]) / exported_live2d["exportUrl"]
        self.assertTrue(live2d_export_path.is_file())
        self.assertTrue((live2d_export_path.parent / "hero.moc3").is_file())
        self.assertTrue((live2d_export_path.parent / "textures" / "texture_00.png").is_file())
        self.assertTrue((live2d_export_path.parent / "motions" / "idle.motion3.json").is_file())
        exported_model3d = next(
            asset for asset in exported_game_data["assets"]["assets"] if asset["id"] == model3d_asset["id"]
        )
        model3d_export_path = Path(export_result["buildPath"]) / exported_model3d["exportUrl"]
        self.assertTrue(model3d_export_path.is_file())
        self.assertTrue((model3d_export_path.parent / "hero.bin").is_file())
        self.assertTrue((model3d_export_path.parent / "textures" / "body.png").is_file())
        self.assertIn("character_presentation_mapping_incomplete", issue_codes)
        self.assertNotIn("live2d_model3_dependency_missing", issue_codes)
        self.assertNotIn("model3d_gltf_dependency_missing", issue_codes)
        self.assertNotIn("character_presentation_asset_missing", issue_codes)

    def test_scene3d_assets_export_with_dependencies_and_native_preview_report(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()
        scene3d_asset = run_editor.import_assets(
            "scene3d",
            [
                build_upload_payload(
                    "classroom_scene.gltf",
                    json.dumps(
                        {
                            "asset": {"version": "2.0"},
                            "scene": 0,
                            "scenes": [{"name": "Classroom", "nodes": [0, 1]}],
                            "nodes": [{"name": "Room", "mesh": 0}, {"name": "CameraRig", "camera": 0}],
                            "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "material": 0}]}],
                            "accessors": [{}, {}],
                            "materials": [
                                {
                                    "name": "Wall Paint",
                                    "alphaMode": "BLEND",
                                    "doubleSided": True,
                                    "pbrMetallicRoughness": {"baseColorTexture": {"index": 0}},
                                }
                            ],
                            "textures": [{"source": 0}],
                            "buffers": [{"uri": "classroom.bin"}],
                            "images": [{"uri": "textures/walls.png"}],
                            "cameras": [{"type": "perspective"}],
                            "animations": [
                                {
                                    "name": "Idle Camera",
                                    "channels": [{"sampler": 0, "target": {"node": 1, "path": "rotation"}}],
                                    "samplers": [{"input": 0, "output": 1, "interpolation": "LINEAR"}],
                                }
                            ],
                            "extensions": {"KHR_lights_punctual": {"lights": [{"name": "Window Light", "type": "directional"}]}},
                        }
                    ).encode("utf-8"),
                )
            ],
        )["assets"][0]
        scene3d_source_path = run_editor.resolve_asset_source_path(scene3d_asset["path"])
        self.assertIsNotNone(scene3d_source_path)
        assert scene3d_source_path is not None
        (scene3d_source_path.parent / "textures").mkdir(parents=True, exist_ok=True)
        (scene3d_source_path.parent / "classroom.bin").write_bytes(b"fake-scene-bin")
        (scene3d_source_path.parent / "textures" / "walls.png").write_bytes(build_fake_png_bytes())

        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {
                    "id": "block_001",
                    "type": "background",
                    "assetId": scene3d_asset["id"],
                    "scene3dPreview": {"yaw": 118, "pitch": 46, "zoom": 1.35, "interactionEnabled": False},
                },
                {"id": "block_002", "type": "narration", "text": "这是一个 3D 可交互场景入口。"},
            ],
        )

        self.assertEqual(run_editor.choose_smart_asset_type("classroom_scene.gltf"), "scene3d")
        self.assertEqual(run_editor.choose_smart_asset_type("hero.glb"), "model3d")

        export_result = run_editor.export_native_runtime_build()
        exported_game_data = json.loads((Path(export_result["buildPath"]) / "game_data.json").read_text(encoding="utf-8"))
        exported_scene3d = next(
            asset for asset in exported_game_data["assets"]["assets"] if asset["id"] == scene3d_asset["id"]
        )
        scene3d_export_path = Path(export_result["buildPath"]) / exported_scene3d["exportUrl"]
        self.assertTrue(scene3d_export_path.is_file())
        self.assertTrue((scene3d_export_path.parent / "classroom.bin").is_file())
        self.assertTrue((scene3d_export_path.parent / "textures" / "walls.png").is_file())

        release_check_payload = json.loads(
            (Path(export_result["buildPath"]) / run_editor.NATIVE_RUNTIME_RELEASE_CHECK_NAME).read_text(encoding="utf-8")
        )
        issue_codes = {issue.get("code") for issue in release_check_payload["issues"]}
        self.assertNotIn("scene3d_gltf_dependency_missing", issue_codes)
        self.assertNotIn("scene3d_gltf_empty_structure", issue_codes)

        asset3d_payload = json.loads(
            (Path(export_result["buildPath"]) / run_editor.NATIVE_RUNTIME_3D_ASSET_REPORT_NAME).read_text(encoding="utf-8")
        )
        asset3d_summary_text = (Path(export_result["buildPath"]) / run_editor.NATIVE_RUNTIME_3D_ASSET_SUMMARY_NAME).read_text(
            encoding="utf-8"
        )
        self.assertEqual(asset3d_payload["status"], "ready")
        self.assertEqual(asset3d_payload["summary"]["assetCount"], 1)
        self.assertEqual(asset3d_payload["summary"]["scene3dCount"], 1)
        self.assertEqual(asset3d_payload["summary"]["totalNodes"], 2)
        self.assertEqual(asset3d_payload["summary"]["totalTextureSlots"], 1)
        self.assertEqual(asset3d_payload["summary"]["textureSlotReadyCount"], 1)
        self.assertEqual(asset3d_payload["summary"]["textureSlotIssueCount"], 0)
        self.assertEqual(asset3d_payload["summary"]["gltfIntegrityIssueCount"], 0)
        self.assertEqual(asset3d_payload["summary"]["performanceBudgetIssueCount"], 0)
        self.assertEqual(asset3d_payload["entries"][0]["previewProbe"]["status"], "ready")
        self.assertEqual(asset3d_payload["entries"][0]["gltfIntegrityProbe"]["status"], "ready")
        self.assertEqual(asset3d_payload["entries"][0]["performanceBudgetProbe"]["status"], "ready")
        self.assertEqual(asset3d_payload["entries"][0]["previewProbe"]["materials"][0]["name"], "Wall Paint")
        self.assertEqual(asset3d_payload["entries"][0]["previewProbe"]["materials"][0]["textureSlots"][0]["uri"], "textures/walls.png")
        self.assertEqual(asset3d_payload["entries"][0]["previewProbe"]["animations"][0]["targetPaths"], ["rotation"])
        self.assertEqual(asset3d_payload["entries"][0]["previewProbe"]["lightCount"], 1)
        self.assertEqual(asset3d_payload["entries"][0]["usageCount"], 1)
        self.assertEqual(export_result["asset3dReportStatus"], "ready")
        self.assertEqual(export_result["asset3dReportDigest"]["status"], "ready")
        self.assertIn("暂无明显 3D 风险", export_result["asset3dReportDigest"]["summaryLine"])
        self.assertIn("# 3D 资产清单摘要", asset3d_summary_text)
        self.assertIn("Wall Paint", asset3d_summary_text)
        self.assertIn("Idle Camera", asset3d_summary_text)

        scene3d_description = subprocess.run(
            [
                sys.executable,
                str(Path(export_result["buildPath"]) / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--describe-scene3d-preview",
                str(export_result["buildPath"]),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(scene3d_description.returncode, 0, scene3d_description.stdout + scene3d_description.stderr)
        scene3d_payload = json.loads(scene3d_description.stdout)
        self.assertEqual(scene3d_payload["status"], "ready")
        self.assertEqual(scene3d_payload["summary"]["scene3dAssetCount"], 1)
        self.assertEqual(scene3d_payload["entries"][0]["usageCount"], 1)
        self.assertEqual(scene3d_payload["entries"][0]["dependencyHealth"]["status"], "ready")
        self.assertEqual(scene3d_payload["entries"][0]["structureSummary"]["status"], "ready")
        self.assertEqual(scene3d_payload["entries"][0]["structureSummary"]["nodes"], 2)
        self.assertEqual(scene3d_payload["entries"][0]["structureSummary"]["meshes"], 1)
        self.assertEqual(scene3d_payload["entries"][0]["structureSummary"]["materials"], 1)
        self.assertEqual(scene3d_payload["entries"][0]["structureSummary"]["textures"], 1)
        self.assertEqual(scene3d_payload["entries"][0]["structureSummary"]["animations"], 1)
        self.assertEqual(scene3d_payload["entries"][0]["usages"][0]["previewConfig"]["yaw"], 118)
        self.assertEqual(scene3d_payload["entries"][0]["usages"][0]["previewConfig"]["pitch"], 46)
        self.assertEqual(scene3d_payload["entries"][0]["usages"][0]["previewConfig"]["zoom"], 1.35)
        self.assertFalse(scene3d_payload["entries"][0]["usages"][0]["previewConfig"]["interactionEnabled"])

        asset3d_description = subprocess.run(
            [
                sys.executable,
                str(Path(export_result["buildPath"]) / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--describe-3d-assets",
                str(export_result["buildPath"]),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(asset3d_description.returncode, 0, asset3d_description.stdout + asset3d_description.stderr)
        asset3d_description_payload = json.loads(asset3d_description.stdout)
        self.assertEqual(asset3d_description_payload["entries"][0]["structureSummary"]["defaultSceneName"], "Classroom")

        asset3d_markdown_description = subprocess.run(
            [
                sys.executable,
                str(Path(export_result["buildPath"]) / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--describe-3d-assets-markdown",
                str(export_result["buildPath"]),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            asset3d_markdown_description.returncode,
            0,
            asset3d_markdown_description.stdout + asset3d_markdown_description.stderr,
        )
        self.assertIn("材质贴图槽", asset3d_markdown_description.stdout)
        self.assertIn("内部引用", asset3d_markdown_description.stdout)
        self.assertIn("性能预算", asset3d_markdown_description.stdout)

    def test_scene3d_glb_assets_are_statically_probed_before_native_release(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()
        scene3d_asset = run_editor.import_assets(
            "scene3d",
            [
                build_upload_payload(
                    "compact_scene.glb",
                    build_fake_glb_bytes(
                        {
                            "asset": {"version": "2.0"},
                            "scene": 0,
                            "scenes": [{"name": "Compact GLB Scene", "nodes": [0]}],
                            "nodes": [{"name": "Room", "mesh": 0}],
                            "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "material": 0}]}],
                            "accessors": [{}],
                            "materials": [{"name": "Embedded Paint"}],
                        }
                    ),
                )
            ],
        )["assets"][0]
        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {"id": "block_001", "type": "background", "assetId": scene3d_asset["id"]},
                {"id": "block_002", "type": "narration", "text": "这是一个 GLB 场景。"},
            ],
        )

        export_result = run_editor.export_native_runtime_build()
        build_dir = Path(export_result["buildPath"])
        release_check_payload = json.loads((build_dir / run_editor.NATIVE_RUNTIME_RELEASE_CHECK_NAME).read_text(encoding="utf-8"))
        issue_codes = {issue.get("code") for issue in release_check_payload["issues"]}
        self.assertNotIn("scene3d_glb_json_invalid", issue_codes)
        self.assertNotIn("scene3d_glb_container_issue", issue_codes)

        asset3d_payload = json.loads((build_dir / run_editor.NATIVE_RUNTIME_3D_ASSET_REPORT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(asset3d_payload["status"], "ready")
        self.assertEqual(asset3d_payload["summary"]["totalNodes"], 1)
        self.assertEqual(asset3d_payload["summary"]["totalMaterials"], 1)
        self.assertEqual(asset3d_payload["summary"]["gltfIntegrityIssueCount"], 0)
        self.assertEqual(asset3d_payload["summary"]["glbContainerIssueCount"], 0)
        self.assertEqual(asset3d_payload["summary"]["performanceBudgetIssueCount"], 0)
        entry = asset3d_payload["entries"][0]
        self.assertEqual(entry["structureSummary"]["sourceType"], "glb")
        self.assertEqual(entry["gltfIntegrityProbe"]["status"], "ready")
        self.assertEqual(entry["glbContainerProbe"]["status"], "ready")
        self.assertEqual(entry["performanceBudgetProbe"]["status"], "ready")
        self.assertEqual(entry["previewProbe"]["materials"][0]["name"], "Embedded Paint")

    def test_native_runtime_release_check_flags_3d_performance_budget_risks(self) -> None:
        self.create_blank_project_with_chapter()
        scene3d_asset = run_editor.import_assets(
            "scene3d",
            [
                build_upload_payload(
                    "heavy_scene.gltf",
                    json.dumps(
                        {
                            "asset": {"version": "2.0"},
                            "scene": 0,
                            "scenes": [{"name": "Heavy Scene", "nodes": [0]}],
                            "nodes": [{"name": "Massive Room", "mesh": 0}],
                            "meshes": [
                                {
                                    "primitives": [
                                        {"attributes": {"POSITION": 0}, "indices": 1, "material": 0},
                                        {"attributes": {"POSITION": 2}, "indices": 3, "material": 1},
                                    ]
                                }
                            ],
                            "accessors": [
                                {"count": 420000},
                                {"count": 900000},
                                {"count": 390000},
                                {"count": 720000},
                            ],
                            "materials": [{"name": f"Material {index}"} for index in range(90)],
                            "textures": [{} for _ in range(100)],
                            "images": [{"bufferView": 0} for _ in range(100)],
                            "animations": [
                                {
                                    "name": "Massive Camera Move",
                                    "channels": [
                                        {"sampler": channel_index, "target": {"node": 0, "path": "translation"}}
                                        for channel_index in range(320)
                                    ],
                                    "samplers": [{"input": 0, "output": 1} for _ in range(320)],
                                }
                            ],
                        }
                    ).encode("utf-8"),
                )
            ],
        )["assets"][0]

        export_result = run_editor.export_native_runtime_build()
        build_dir = Path(export_result["buildPath"])
        release_check_payload = json.loads((build_dir / run_editor.NATIVE_RUNTIME_RELEASE_CHECK_NAME).read_text(encoding="utf-8"))
        issue_codes = {issue.get("code") for issue in release_check_payload["issues"]}
        self.assertIn("scene3d_gltf_performance_budget_risk", issue_codes)
        self.assertEqual(export_result["asset3dReportDigest"]["status"], "needs_attention")
        self.assertTrue(export_result["asset3dReportDigest"]["topIssues"])
        self.assertIn("性能预算", export_result["asset3dReportDigest"]["topIssues"][0]["summary"])
        self.assertEqual(export_result["asset3dReportDigest"]["topIssues"][0]["assetId"], scene3d_asset["id"])
        self.assertIn(scene3d_asset["id"], export_result["asset3dReportDigest"]["issueAssetIds"])
        self.assertEqual(export_result["asset3dReportDigest"]["issueAssets"][0]["assetId"], scene3d_asset["id"])
        self.assertTrue(export_result["asset3dReportDigest"]["issueAssets"][0]["issueBreakdown"])

        asset3d_payload = json.loads((build_dir / run_editor.NATIVE_RUNTIME_3D_ASSET_REPORT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(asset3d_payload["status"], "needs_attention")
        self.assertGreaterEqual(asset3d_payload["summary"]["performanceBudgetIssueCount"], 4)
        self.assertEqual(asset3d_payload["summary"]["estimatedVertexCount"], 810000)
        self.assertEqual(asset3d_payload["summary"]["estimatedTriangleCount"], 540000)
        budget_probe = asset3d_payload["entries"][0]["performanceBudgetProbe"]
        self.assertEqual(budget_probe["status"], "needs_attention")
        budget_metrics = {issue.get("metric") for issue in budget_probe["issues"]}
        self.assertIn("estimatedVertexCount", budget_metrics)
        self.assertIn("estimatedTriangleCount", budget_metrics)

    def test_variable_rename_migrates_story_references(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()
        run_editor.save_project_settings(
            variables={
                "variables": [
                    {
                        "id": "var_score",
                        "name": "分数",
                        "type": "number",
                        "defaultValue": 0,
                        "min": 0,
                        "max": 100,
                    },
                    {
                        "id": "var_route",
                        "name": "路线",
                        "type": "string",
                        "defaultValue": "common",
                    },
                ]
            }
        )
        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {"id": "block_001", "type": "variable_add", "variableId": "var_score", "value": 3},
                {
                    "id": "block_002",
                    "type": "choice",
                    "options": [
                        {
                            "id": "choice_01",
                            "text": "继续",
                            "gotoSceneId": chapter_result["sceneId"],
                            "effects": [
                                {"type": "variable_set", "variableId": "var_score", "value": 5},
                            ],
                        }
                    ],
                },
                {
                    "id": "block_003",
                    "type": "condition",
                    "branches": [
                        {
                            "id": "branch_01",
                            "when": [{"variableId": "var_score", "operator": ">=", "value": 3}],
                            "gotoSceneId": chapter_result["sceneId"],
                        }
                    ],
                },
            ],
        )

        result = run_editor.rename_project_variable(
            old_variable_id="var_score",
            variable={
                "id": "var_points",
                "name": "积分",
                "type": "number",
                "defaultValue": 10,
                "min": 0,
                "max": 120,
            },
        )
        bundle = run_editor.load_project_bundle()
        saved_scene = bundle["chapters"][0]["scenes"][0]

        self.assertEqual(result["migration"]["referenceCount"], 3)
        self.assertEqual(bundle["variables"]["variables"][0]["id"], "var_points")
        self.assertEqual(bundle["variables"]["variables"][0]["name"], "积分")
        self.assertEqual(saved_scene["blocks"][0]["variableId"], "var_points")
        self.assertEqual(saved_scene["blocks"][1]["options"][0]["effects"][0]["variableId"], "var_points")
        self.assertEqual(saved_scene["blocks"][2]["branches"][0]["when"][0]["variableId"], "var_points")

    def test_native_runtime_release_check_flags_gltf_material_texture_slot_issues(self) -> None:
        self.create_blank_project_with_chapter()
        run_editor.import_assets(
            "scene3d",
            [
                build_upload_payload(
                    "broken_material_scene.gltf",
                    json.dumps(
                        {
                            "asset": {"version": "2.0"},
                            "scene": 0,
                            "scenes": [{"name": "Broken Material Scene", "nodes": [0]}],
                            "nodes": [{"name": "Room", "mesh": 0}],
                            "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "material": 0}]}],
                            "accessors": [{}],
                            "materials": [
                                {
                                    "name": "Broken Wall",
                                    "pbrMetallicRoughness": {"baseColorTexture": {"index": 3}},
                                }
                            ],
                            "textures": [],
                            "images": [],
                        }
                    ).encode("utf-8"),
                )
            ],
        )

        export_result = run_editor.export_native_runtime_build()
        build_dir = Path(export_result["buildPath"])
        release_check_payload = json.loads((build_dir / run_editor.NATIVE_RUNTIME_RELEASE_CHECK_NAME).read_text(encoding="utf-8"))
        issue_codes = {issue.get("code") for issue in release_check_payload["issues"]}
        self.assertIn("scene3d_gltf_material_texture_slot_issue", issue_codes)

        asset3d_payload = json.loads((build_dir / run_editor.NATIVE_RUNTIME_3D_ASSET_REPORT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(asset3d_payload["status"], "needs_attention")
        self.assertEqual(asset3d_payload["summary"]["textureSlotIssueCount"], 1)
        self.assertEqual(asset3d_payload["entries"][0]["previewProbe"]["materials"][0]["textureSlots"][0]["status"], "missing_texture")

    def test_native_runtime_release_check_flags_gltf_internal_reference_issues(self) -> None:
        self.create_blank_project_with_chapter()
        run_editor.import_assets(
            "scene3d",
            [
                build_upload_payload(
                    "broken_integrity_scene.gltf",
                    json.dumps(
                        {
                            "asset": {"version": "2.0"},
                            "scene": 2,
                            "scenes": [{"name": "Broken Integrity Scene", "nodes": [4]}],
                            "nodes": [{"name": "Room", "mesh": 3, "children": [9]}],
                            "meshes": [{"primitives": [{"attributes": {"POSITION": 7}, "material": 5}]}],
                            "materials": [{"name": "Broken Material"}],
                            "animations": [
                                {
                                    "name": "Broken Move",
                                    "channels": [{"sampler": 4, "target": {"node": 8, "path": "rotateAround"}}],
                                    "samplers": [{"input": 10, "output": 11}],
                                }
                            ],
                        }
                    ).encode("utf-8"),
                )
            ],
        )

        export_result = run_editor.export_native_runtime_build()
        build_dir = Path(export_result["buildPath"])
        release_check_payload = json.loads((build_dir / run_editor.NATIVE_RUNTIME_RELEASE_CHECK_NAME).read_text(encoding="utf-8"))
        issue_codes = {issue.get("code") for issue in release_check_payload["issues"]}
        self.assertIn("scene3d_gltf_integrity_issue", issue_codes)

        asset3d_payload = json.loads((build_dir / run_editor.NATIVE_RUNTIME_3D_ASSET_REPORT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(asset3d_payload["status"], "needs_attention")
        self.assertGreaterEqual(asset3d_payload["summary"]["gltfIntegrityIssueCount"], 6)
        integrity_probe = asset3d_payload["entries"][0]["gltfIntegrityProbe"]
        self.assertEqual(integrity_probe["status"], "needs_attention")
        integrity_codes = {issue.get("code") for issue in integrity_probe["issues"]}
        self.assertIn("gltf_default_scene_missing", integrity_codes)
        self.assertIn("gltf_scene_node_missing", integrity_codes)

    def test_native_runtime_release_check_flags_invalid_glb_container(self) -> None:
        self.create_blank_project_with_chapter()
        run_editor.import_assets(
            "scene3d",
            [build_upload_payload("broken_container.glb", b"not-a-valid-glb")],
        )

        export_result = run_editor.export_native_runtime_build()
        build_dir = Path(export_result["buildPath"])
        release_check_payload = json.loads((build_dir / run_editor.NATIVE_RUNTIME_RELEASE_CHECK_NAME).read_text(encoding="utf-8"))
        issue_codes = {issue.get("code") for issue in release_check_payload["issues"]}
        self.assertIn("scene3d_glb_json_invalid", issue_codes)

        asset3d_payload = json.loads((build_dir / run_editor.NATIVE_RUNTIME_3D_ASSET_REPORT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(asset3d_payload["status"], "needs_attention")
        self.assertEqual(asset3d_payload["entries"][0]["status"], "invalid")
        self.assertEqual(asset3d_payload["entries"][0]["glbContainerProbe"]["status"], "invalid")

    def test_creative_assistant_generates_local_insertable_story_blocks(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()

        result = run_editor.build_creative_assistant_result(
            {
                "mode": "starter_demo",
                "prompt": "雨夜校园悬疑恋爱，女主知道一个秘密",
                "sceneId": chapter_result["sceneId"],
            }
        )

        self.assertEqual(result["mode"], "starter_demo")
        self.assertTrue(result["insertable"])
        self.assertGreaterEqual(result["blockCount"], 4)
        self.assertFalse(result["privacy"]["sentToExternalService"])
        self.assertIn("本地模板助手", result["privacy"]["message"])
        block_types = [block["type"] for block in result["blocks"]]
        self.assertIn("dialogue", block_types)
        self.assertIn("choice", block_types)
        choice_block = next(block for block in result["blocks"] if block["type"] == "choice")
        self.assertGreaterEqual(len(choice_block["options"]), 2)

    def test_creative_assistant_openai_provider_uses_model_result(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()
        model_result = {
            "title": "模型生成标题",
            "summary": "模型根据当前场景生成了可插入的开场。",
            "guidance": ["先用一句旁白建立气氛。", "第二张卡片交给角色抛出钩子。"],
            "assetPrompts": ["近未来雨夜街角，蓝紫色霓虹，视觉小说背景"],
            "blocks": [
                {"type": "narration", "text": "雨声落在透明穹顶上，像一段倒放的倒计时。"},
                {"type": "dialogue", "speakerId": "heroine", "text": "如果我说，今晚之后一切都会重来呢？"},
                {
                    "type": "choice",
                    "options": [
                        {"text": "追问时间循环", "gotoSceneId": chapter_result["sceneId"]},
                        {"text": "先陪她离开", "gotoSceneId": chapter_result["sceneId"]},
                    ],
                },
            ],
        }
        response_payload = {
            "output": [
                {
                    "content": [
                        {
                            "type": "output_text",
                            "text": json.dumps(model_result, ensure_ascii=False),
                        }
                    ]
                }
            ]
        }

        class FakeResponse:
            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, *_args: object) -> bool:
                return False

            def read(self) -> bytes:
                return json.dumps(response_payload, ensure_ascii=False).encode("utf-8")

        def fake_urlopen(request, timeout=0):
            self.assertEqual(timeout, 45)
            self.assertEqual(request.full_url, run_editor.CREATIVE_ASSISTANT_OPENAI_ENDPOINT)
            self.assertEqual(request.get_header("Authorization"), "Bearer test-openai-key")
            body = json.loads(request.data.decode("utf-8"))
            self.assertEqual(body["model"], "gpt-test")
            self.assertEqual(body["input"][0]["content"][0]["type"], "input_text")
            self.assertIn("近未来 AI 少女", body["input"][0]["content"][0]["text"])
            return FakeResponse()

        with mock.patch("run_editor.urlopen", fake_urlopen):
            result = run_editor.build_creative_assistant_result(
                {
                    "provider": "openai",
                    "apiKey": "test-openai-key",
                    "model": "gpt-test",
                    "mode": "script",
                    "prompt": "近未来 AI 少女在雨夜发现时间循环",
                    "sceneId": chapter_result["sceneId"],
                }
            )

        self.assertEqual(result["provider"]["mode"], "openai")
        self.assertEqual(result["provider"]["status"], "model")
        self.assertEqual(result["provider"]["model"], "gpt-test")
        self.assertTrue(result["privacy"]["sentToExternalService"])
        self.assertEqual(result["title"], "模型生成标题")
        self.assertEqual(result["blockCount"], 3)
        self.assertEqual(result["blocks"][1]["speakerId"], "heroine")
        self.assertEqual(result["blocks"][2]["options"][0]["gotoSceneId"], chapter_result["sceneId"])

    def test_creative_assistant_compatible_provider_uses_chat_completions(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()
        model_result = {
            "title": "兼容模型标题",
            "summary": "DeepSeek 兼容接口返回了可插入剧情。",
            "guidance": ["先写误会，再给一次选择。"],
            "assetPrompts": ["雨夜校园，蓝色背光，视觉小说背景"],
            "blocks": [
                {"type": "narration", "text": "窗外的雨把走廊灯切成一格一格的影子。"},
                {"type": "choice", "options": [
                    {"text": "追上去", "gotoSceneId": chapter_result["sceneId"]},
                    {"text": "留在原地", "gotoSceneId": chapter_result["sceneId"]},
                ]},
            ],
        }
        response_payload = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(model_result, ensure_ascii=False),
                    }
                }
            ]
        }

        class FakeResponse:
            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, *_args: object) -> bool:
                return False

            def read(self) -> bytes:
                return json.dumps(response_payload, ensure_ascii=False).encode("utf-8")

        def fake_urlopen(request, timeout=0):
            self.assertEqual(timeout, 45)
            self.assertEqual(request.full_url, "https://api.deepseek.com/chat/completions")
            self.assertEqual(request.get_header("Authorization"), "Bearer test-deepseek-key")
            body = json.loads(request.data.decode("utf-8"))
            self.assertEqual(body["model"], "deepseek-v4-flash")
            self.assertEqual(body["messages"][0]["role"], "system")
            self.assertIn("只输出 JSON 对象", body["messages"][0]["content"])
            self.assertIn("雨夜校园误会", body["messages"][1]["content"])
            return FakeResponse()

        with mock.patch("run_editor.urlopen", fake_urlopen):
            result = run_editor.build_creative_assistant_result(
                {
                    "provider": "deepseek",
                    "apiKey": "test-deepseek-key",
                    "mode": "script",
                    "prompt": "雨夜校园误会",
                    "sceneId": chapter_result["sceneId"],
                }
            )

        self.assertEqual(result["provider"]["mode"], "deepseek")
        self.assertEqual(result["provider"]["status"], "model")
        self.assertEqual(result["provider"]["model"], "deepseek-v4-flash")
        self.assertTrue(result["privacy"]["sentToExternalService"])
        self.assertIn("DeepSeek API Key", result["privacy"]["message"])
        self.assertEqual(result["title"], "兼容模型标题")
        self.assertEqual(result["blockCount"], 2)

    def test_openai_asset_generation_saves_image_without_persisting_key(self) -> None:
        self.create_blank_project_with_chapter()
        response_payload = {
            "data": [
                {
                    "b64_json": base64.b64encode(build_fake_png_bytes()).decode("utf-8"),
                }
            ]
        }
        captured = {}

        class FakeResponse:
            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, *_args: object) -> bool:
                return False

            def read(self, *_args: object) -> bytes:
                return json.dumps(response_payload).encode("utf-8")

        def fake_urlopen(request, timeout=0):
            self.assertEqual(timeout, 90)
            self.assertEqual(request.full_url, openai_asset_generation.OPENAI_ASSET_GENERATION_ENDPOINT)
            self.assertEqual(request.get_header("Authorization"), "Bearer test-openai-image-key")
            body = json.loads(request.data.decode("utf-8"))
            captured["body"] = body
            self.assertEqual(body["model"], "gpt-image-test")
            self.assertEqual(body["size"], "1536x1024")
            self.assertEqual(body["quality"], "high")
            self.assertEqual(body["output_format"], "png")
            self.assertIn("视觉小说背景", body["prompt"])
            self.assertIn("visual novel background", body["prompt"])
            self.assertIn("soft blue lighting", body["prompt"])
            return FakeResponse()

        with mock.patch("openai_asset_generation.urlopen", fake_urlopen):
            result = run_editor.generate_openai_asset(
                {
                    "assetType": "background",
                    "prompt": "雨夜校园，视觉小说背景",
                    "styleHint": "soft blue lighting",
                    "assetName": "雨夜校园背景",
                    "apiKey": "test-openai-image-key",
                    "model": "gpt-image-test",
                    "size": "1536x1024",
                    "quality": "high",
                    "outputFormat": "png",
                }
            )

        asset = result["asset"]
        self.assertEqual(asset["type"], "background")
        self.assertEqual(asset["name"], "雨夜校园背景")
        self.assertTrue((run_editor.TEMPLATE_DIR / asset["path"]).is_file())
        self.assertIn("AI生成", asset["tags"])
        self.assertTrue(result["privacy"]["sentToExternalService"])
        self.assertFalse(result["privacy"]["apiKeyStored"])
        assets_doc = run_editor.read_json(run_editor.DATA_DIR / "assets.json")
        self.assertNotIn("test-openai-image-key", json.dumps(assets_doc, ensure_ascii=False))
        self.assertIn("visual novel background", captured["body"]["prompt"])
        self.assertIn("soft blue lighting", captured["body"]["prompt"])

    def test_openai_asset_generation_binds_sprite_to_character_expression(self) -> None:
        self.create_blank_project_with_chapter()
        run_editor.write_json(
            run_editor.DATA_DIR / "characters.json",
            {
                "characters": [
                    {
                        "id": "char_hero",
                        "displayName": "蓝白女主",
                        "defaultSpriteId": "",
                        "expressions": [],
                    }
                ]
            },
        )
        response_payload = {
            "data": [
                {
                    "b64_json": base64.b64encode(build_fake_png_bytes()).decode("utf-8"),
                }
            ]
        }
        captured = {}

        class FakeResponse:
            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, *_args: object) -> bool:
                return False

            def read(self, *_args: object) -> bytes:
                return json.dumps(response_payload).encode("utf-8")

        def fake_urlopen(request, timeout=0):
            body = json.loads(request.data.decode("utf-8"))
            captured["body"] = body
            self.assertEqual(body["model"], "gpt-image-test")
            self.assertEqual(body["size"], "1024x1536")
            self.assertEqual(body["background"], "transparent")
            self.assertIn("清透蓝白", body["prompt"])
            return FakeResponse()

        with mock.patch("openai_asset_generation.urlopen", fake_urlopen):
            result = run_editor.generate_openai_asset(
                {
                    "assetType": "sprite",
                    "prompt": "原创女主角半身立绘，校服，透明背景",
                    "styleHint": "清透蓝白",
                    "assetName": "女主微笑立绘",
                    "apiKey": "test-openai-image-key",
                    "model": "gpt-image-test",
                    "size": "1024x1536",
                    "quality": "high",
                    "background": "transparent",
                    "outputFormat": "png",
                    "characterBinding": {
                        "characterId": "char_hero",
                        "expressionId": "expr_smile",
                        "expressionName": "微笑",
                        "setAsDefaultSprite": True,
                    },
                }
            )

        asset = result["asset"]
        binding = result["characterBinding"]
        self.assertEqual(asset["type"], "sprite")
        self.assertEqual(binding["characterId"], "char_hero")
        self.assertEqual(binding["characterName"], "蓝白女主")
        self.assertEqual(binding["expressionId"], "expr_smile")
        self.assertEqual(binding["expressionName"], "微笑")
        self.assertTrue(binding["setAsDefaultSprite"])
        self.assertEqual(binding["assetId"], asset["id"])
        self.assertIn("清透蓝白", captured["body"]["prompt"])

        characters_doc = run_editor.read_json(run_editor.DATA_DIR / "characters.json")
        character = characters_doc["characters"][0]
        self.assertEqual(character["defaultSpriteId"], asset["id"])
        self.assertEqual(character["presentation"]["fallbackSpriteAssetId"], asset["id"])
        self.assertEqual(character["expressions"][0]["id"], "expr_smile")
        self.assertEqual(character["expressions"][0]["name"], "微笑")
        self.assertEqual(character["expressions"][0]["spriteAssetId"], asset["id"])
        self.assertNotIn("test-openai-image-key", json.dumps(characters_doc, ensure_ascii=False))

    def test_openai_asset_generation_rolls_back_when_character_binding_fails(self) -> None:
        self.create_blank_project_with_chapter()
        characters_path = run_editor.DATA_DIR / "characters.json"
        run_editor.write_json(
            characters_path,
            {
                "characters": [
                    {
                        "id": "char_hero",
                        "displayName": "蓝白女主",
                        "defaultSpriteId": "",
                        "expressions": [],
                    }
                ]
            },
        )
        assets_path = run_editor.DATA_DIR / "assets.json"
        before_assets = run_editor.read_json(assets_path)
        before_characters = run_editor.read_json(characters_path)
        sprite_dir = run_editor.TEMPLATE_DIR / run_editor.ASSET_DIRECTORIES["sprite"]
        before_sprite_files = {path.name for path in sprite_dir.glob("*") if path.is_file()} if sprite_dir.is_dir() else set()
        generation_meta = {
            "model": "gpt-image-test",
            "size": "1024x1536",
            "quality": "high",
            "background": "transparent",
            "outputFormat": "png",
            "prompt": "原创女主角半身立绘，校服，透明背景",
        }

        with (
            mock.patch.object(
                run_editor,
                "call_openai_asset_generation_model",
                return_value=(build_fake_png_bytes(), generation_meta),
            ),
            mock.patch.object(
                run_editor,
                "bind_sprite_asset_to_character",
                side_effect=RuntimeError("simulated binding failure"),
            ),
        ):
            with self.assertRaisesRegex(RuntimeError, "simulated binding failure"):
                run_editor.generate_openai_asset(
                    {
                        "assetType": "sprite",
                        "prompt": "原创女主角半身立绘，校服，透明背景",
                        "assetName": "失败回滚立绘",
                        "apiKey": "test-openai-image-key",
                        "model": "gpt-image-test",
                        "size": "1024x1536",
                        "quality": "high",
                        "background": "transparent",
                        "outputFormat": "png",
                        "characterBinding": {
                            "characterId": "char_hero",
                            "expressionId": "expr_smile",
                            "expressionName": "微笑",
                            "setAsDefaultSprite": True,
                        },
                    }
                )

        after_sprite_files = {path.name for path in sprite_dir.glob("*") if path.is_file()} if sprite_dir.is_dir() else set()
        self.assertEqual(run_editor.read_json(assets_path), before_assets)
        self.assertEqual(run_editor.read_json(characters_path), before_characters)
        self.assertEqual(after_sprite_files, before_sprite_files)

    def test_openai_asset_generation_rejects_non_sprite_character_binding(self) -> None:
        self.create_blank_project_with_chapter()
        run_editor.write_json(
            run_editor.DATA_DIR / "characters.json",
            {
                "characters": [
                    {
                        "id": "char_hero",
                        "displayName": "蓝白女主",
                        "defaultSpriteId": "",
                        "expressions": [],
                    }
                ]
            },
        )
        with self.assertRaisesRegex(ValueError, "只有立绘素材可以在生成后绑定到角色表情"):
            run_editor.generate_openai_asset(
                {
                    "assetType": "background",
                    "prompt": "雨夜校园，视觉小说背景",
                    "apiKey": "test-openai-image-key",
                    "characterBinding": {
                        "characterId": "char_hero",
                        "expressionName": "默认",
                    },
                }
            )

    def test_openai_asset_generation_requires_api_key(self) -> None:
        self.create_blank_project_with_chapter()
        with self.assertRaisesRegex(ValueError, "API Key"):
            run_editor.generate_openai_asset(
                {
                    "assetType": "sprite",
                    "prompt": "原创女主角立绘，透明背景",
                    "apiKey": "",
                }
            )

    def test_openai_asset_generation_rejects_transparent_jpeg(self) -> None:
        self.create_blank_project_with_chapter()
        with self.assertRaisesRegex(ValueError, "JPEG 不支持透明背景"):
            run_editor.generate_openai_asset(
                {
                    "assetType": "sprite",
                    "prompt": "原创女主角立绘，透明背景",
                    "apiKey": "test-openai-image-key",
                    "background": "transparent",
                    "outputFormat": "jpeg",
                }
            )

    def test_openai_asset_generation_rejects_overlong_prompt(self) -> None:
        self.create_blank_project_with_chapter()
        with self.assertRaisesRegex(ValueError, "提示词超过 1400 字"):
            run_editor.generate_openai_asset(
                {
                    "assetType": "background",
                    "prompt": "长" * 1401,
                    "apiKey": "test-openai-image-key",
                }
            )

    def test_openai_asset_generation_rejects_overlong_style_hint(self) -> None:
        self.create_blank_project_with_chapter()
        with self.assertRaisesRegex(ValueError, "画风补充超过 260 字"):
            run_editor.generate_openai_asset(
                {
                    "assetType": "background",
                    "prompt": "雨夜校园，视觉小说背景",
                    "styleHint": "清" * 261,
                    "apiKey": "test-openai-image-key",
                }
            )

    def test_openai_asset_generation_rejects_invalid_model_name(self) -> None:
        self.create_blank_project_with_chapter()
        with self.assertRaisesRegex(ValueError, "模型名只能包含英文字母"):
            run_editor.generate_openai_asset(
                {
                    "assetType": "background",
                    "prompt": "雨夜校园，视觉小说背景",
                    "apiKey": "test-openai-image-key",
                    "model": "坏 model",
                }
            )

    def test_openai_asset_generation_empty_model_uses_default(self) -> None:
        self.create_blank_project_with_chapter()
        image_payload = {
            "data": [
                {
                    "b64_json": base64.b64encode(build_fake_png_bytes()).decode("utf-8"),
                }
            ]
        }
        captured = {}

        class FakeResponse:
            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, *_args: object) -> bool:
                return False

            def read(self, *_args: object) -> bytes:
                return json.dumps(image_payload).encode("utf-8")

        def fake_urlopen(request, timeout=0):
            body = json.loads(request.data.decode("utf-8"))
            captured["model"] = body["model"]
            return FakeResponse()

        with mock.patch("openai_asset_generation.urlopen", fake_urlopen):
            run_editor.generate_openai_asset(
                {
                    "assetType": "background",
                    "prompt": "雨夜校园，视觉小说背景",
                    "apiKey": "test-openai-image-key",
                    "model": "",
                }
            )

        self.assertEqual(captured["model"], openai_asset_generation.OPENAI_ASSET_GENERATION_DEFAULT_MODEL)

    def test_openai_asset_generation_rejects_invalid_image_bytes(self) -> None:
        self.create_blank_project_with_chapter()
        response_payload = {
            "data": [
                {
                    "b64_json": base64.b64encode(b"not-a-real-image").decode("utf-8"),
                }
            ]
        }

        class FakeResponse:
            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, *_args: object) -> bool:
                return False

            def read(self, *_args: object) -> bytes:
                return json.dumps(response_payload).encode("utf-8")

        with mock.patch("openai_asset_generation.urlopen", lambda *_args, **_kwargs: FakeResponse()):
            with self.assertRaisesRegex(openai_asset_generation.OpenAiAssetGenerationError, "不是可保存的 PNG"):
                run_editor.generate_openai_asset(
                    {
                        "assetType": "background",
                        "prompt": "雨夜校园，视觉小说背景",
                        "assetName": "坏图片",
                        "apiKey": "test-openai-image-key",
                        "outputFormat": "png",
                    }
                )

        assets_doc = run_editor.read_json(run_editor.DATA_DIR / "assets.json")
        self.assertNotIn("坏图片", json.dumps(assets_doc, ensure_ascii=False))

    def test_asset_import_replace_and_delete_with_usage_protection(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()

        with self.assertRaises(ValueError) as single_context:
            run_editor.import_assets(
                "background",
                [build_upload_payload("wrong_bgm.mp3", b"fake-audio")],
            )
        self.assertIn("wrong_bgm.mp3", str(single_context.exception))
        self.assertIn("智能导入", str(single_context.exception))
        self.assertFalse((run_editor.TEMPLATE_DIR / "assets/backgrounds/wrong_bgm.mp3").exists())
        with self.assertRaises(ValueError) as mixed_context:
            run_editor.import_assets(
                "background",
                [
                    build_upload_payload("atomic_ok.png", b"fake-image-before-error"),
                    build_upload_payload("atomic_bad.mp3", b"fake-audio-before-error"),
                    build_upload_payload("atomic_bad.wav", b"fake-voice-before-error"),
                ],
            )
        mixed_message = str(mixed_context.exception)
        self.assertIn("atomic_bad.mp3", mixed_message)
        self.assertIn("atomic_bad.wav", mixed_message)
        self.assertIn("智能导入", mixed_message)
        self.assertFalse((run_editor.TEMPLATE_DIR / "assets/backgrounds/atomic_ok.png").exists())
        original_write_bytes = Path.write_bytes

        def fail_second_asset_write(path: Path, data: bytes) -> int:
            if path.name == "rollback_bad.png":
                raise OSError("simulated disk write failure")
            return original_write_bytes(path, data)

        with mock.patch.object(Path, "write_bytes", fail_second_asset_write):
            with self.assertRaisesRegex(OSError, "simulated disk write failure"):
                run_editor.import_assets(
                    "background",
                    [
                        build_upload_payload("rollback_ok.png", b"fake-image-before-disk-error"),
                        build_upload_payload("rollback_bad.png", b"fake-image-disk-error"),
                    ],
                )
        self.assertFalse((run_editor.TEMPLATE_DIR / "assets/backgrounds/rollback_ok.png").exists())
        self.assertFalse((run_editor.TEMPLATE_DIR / "assets/backgrounds/rollback_bad.png").exists())
        assets_after_rollback = run_editor.read_json(run_editor.DATA_DIR / "assets.json").get("assets", [])
        self.assertFalse(any(asset.get("path", "").endswith("rollback_ok.png") for asset in assets_after_rollback))

        import_result = run_editor.import_assets(
            "background",
            [build_upload_payload("bg_classroom.png", b"fake-image-1")],
        )
        asset = import_result["assets"][0]

        self.assertEqual(asset["type"], "background")
        self.assertTrue((run_editor.TEMPLATE_DIR / asset["path"]).is_file())

        font_import = run_editor.import_assets(
            "auto",
            [build_upload_payload("story_font.ttf", b"fake-font-data")],
        )
        font_asset = font_import["assets"][0]
        self.assertEqual(font_asset["type"], "font")
        self.assertTrue(font_asset["path"].startswith("assets/fonts/"))

        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {
                    "id": "block_001",
                    "type": "background",
                    "assetId": asset["id"],
                    "transition": "fade",
                }
            ],
        )

        with self.assertRaisesRegex(ValueError, "还在被使用|先解除引用"):
            run_editor.delete_asset(asset["id"])

        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {
                    "id": "block_001",
                    "type": "narration",
                    "text": "背景引用已经解除。",
                }
            ],
        )

        with self.assertRaisesRegex(ValueError, "不能用.*替换背景素材|请上传"):
            run_editor.replace_asset_file(
                asset["id"],
                build_upload_payload("wrong_bgm.mp3", b"fake-audio"),
            )
        self.assertTrue((run_editor.TEMPLATE_DIR / asset["path"]).is_file())

        replace_result = run_editor.replace_asset_file(
            asset["id"],
            build_upload_payload("bg_evening.png", b"fake-image-2"),
        )
        self.assertTrue((run_editor.TEMPLATE_DIR / replace_result["asset"]["path"]).is_file())

        delete_result = run_editor.delete_asset(asset["id"])
        self.assertEqual(delete_result["deletedAssetId"], asset["id"])
        self.assertFalse((run_editor.TEMPLATE_DIR / replace_result["asset"]["path"]).exists())

    def test_video_blocks_export_to_web_runtime(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()

        import_result = run_editor.import_assets(
            "auto",
            [build_upload_payload("opening_movie.mp4", b"fake-video-data")],
        )
        video_asset = import_result["assets"][0]
        self.assertEqual(video_asset["type"], "video")
        self.assertTrue(video_asset["path"].startswith("assets/video/"))

        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {
                    "id": "block_video",
                    "type": "video_play",
                    "assetId": video_asset["id"],
                    "title": "Opening Movie",
                    "fit": "contain",
                    "volume": 75,
                    "startTimeSeconds": 1.5,
                    "endTimeSeconds": 4,
                    "skippable": True,
                },
                {
                    "id": "block_credits",
                    "type": "credits_roll",
                    "title": "STAFF",
                    "subtitle": "Thank you for playing",
                    "lines": ["企划：Creator", "测试：Canvasia Engine"],
                    "durationSeconds": 12,
                    "background": "dark",
                    "skippable": True,
                },
            ],
        )

        export_result = run_editor.export_web_build()
        build_dir = Path(export_result["buildPath"])
        exported_video = build_dir / "assets" / "video" / f"{video_asset['id']}.mp4"
        index_html = (build_dir / "index.html").read_text(encoding="utf-8")

        self.assertTrue(exported_video.is_file())
        self.assertIn('"type": "video_play"', index_html)
        self.assertIn('"type": "credits_roll"', index_html)
        self.assertIn("Opening Movie", index_html)

    def test_video_blocks_export_to_native_runtime_bridge(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()

        import_result = run_editor.import_assets(
            "auto",
            [build_upload_payload("opening_movie.mp4", b"fake-video-data")],
        )
        video_asset = import_result["assets"][0]

        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {
                    "id": "block_video",
                    "type": "video_play",
                    "assetId": video_asset["id"],
                    "title": "Opening Movie",
                    "fit": "contain",
                    "volume": 75,
                    "startTimeSeconds": 1.5,
                    "endTimeSeconds": 4,
                    "skippable": True,
                },
                {
                    "id": "block_after_video",
                    "type": "narration",
                    "text": "视频之后继续剧情。",
                },
            ],
        )

        export_result = run_editor.export_native_runtime_build()
        build_dir = Path(export_result["buildPath"])

        release_check_payload = json.loads((build_dir / run_editor.NATIVE_RUNTIME_RELEASE_CHECK_NAME).read_text(encoding="utf-8"))
        issue_codes = {issue.get("code") for issue in release_check_payload["issues"]}
        self.assertEqual(release_check_payload["status"], "warn")
        self.assertTrue(
            {"video_native_external_player_bridge", "video_native_external_player_missing"} & issue_codes
        )

        video_bridge_description = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--describe-video-bridge",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(video_bridge_description.returncode, 0, video_bridge_description.stdout + video_bridge_description.stderr)
        video_bridge_payload = json.loads(video_bridge_description.stdout)
        self.assertEqual(video_bridge_payload["summary"]["videoAssetCount"], 1)
        self.assertEqual(video_bridge_payload["summary"]["videoBlockCount"], 1)
        self.assertEqual(video_bridge_payload["entries"][0]["externalPlaybackMode"], "system_player_bridge")
        self.assertEqual(video_bridge_payload["entries"][0]["embeddedPlaybackMode"], "pyav_audio_video_sync")
        self.assertEqual(video_bridge_payload["entries"][0]["fallbackEmbeddedPlaybackMode"], "opencv_embedded_playback")
        self.assertEqual(video_bridge_payload["entries"][0]["nativePreviewMode"], "cinematic_bridge_card")
        self.assertEqual(video_bridge_payload["nativePreviewMode"], "cinematic_bridge_card")
        self.assertTrue(
            any(option["id"] == "pyav_audio_video_sync" for option in video_bridge_payload["backendOptions"])
        )
        self.assertTrue(
            any(option["id"] == "opencv_frame_preview" for option in video_bridge_payload["backendOptions"])
        )
        self.assertTrue(
            any(option["id"] == "opencv_embedded_playback" for option in video_bridge_payload["backendOptions"])
        )
        self.assertTrue(video_bridge_payload["entries"][0]["exists"])
        self.assertTrue(video_bridge_payload["entries"][0]["extensionSupported"])
        self.assertEqual(video_bridge_payload["entries"][0]["usages"][0]["title"], "Opening Movie")

        video_backend_description = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--describe-video-backends",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(video_backend_description.returncode, 0, video_backend_description.stdout + video_backend_description.stderr)
        video_backend_payload = json.loads(video_backend_description.stdout)
        self.assertEqual(video_backend_payload["nativePreviewMode"], "cinematic_bridge_card")
        self.assertEqual(video_backend_payload["videoAssetCount"], 1)
        self.assertEqual(video_backend_payload["previewProbeCommand"], "python runtime_player.py --probe-video-preview .")
        self.assertTrue(
            any(
                option["optionalRequirements"] == run_editor.NATIVE_RUNTIME_VIDEO_REQUIREMENTS_NAME
                for option in video_backend_payload["backendOptions"]
                if option.get("optionalRequirements")
            )
        )

        video_preview_probe = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--probe-video-preview",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(video_preview_probe.returncode, 0, video_preview_probe.stdout + video_preview_probe.stderr)
        video_preview_payload = json.loads(video_preview_probe.stdout)
        self.assertEqual(video_preview_payload["backendId"], "opencv_frame_preview")
        self.assertEqual(video_preview_payload["summary"]["videoAssetCount"], 1)
        self.assertIn(
            video_preview_payload["status"],
            {"optional_dependency_missing", "pygame_missing", "ready", "partial", "all_failed"},
        )

    def test_voice_placeholder_and_match_workflow(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()

        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {
                    "id": "block_001",
                    "type": "dialogue",
                    "speakerId": "heroine",
                    "expressionId": "",
                    "text": "这句台词会生成语音占位。",
                }
            ],
        )

        placeholder_result = run_editor.create_voice_placeholder(
            chapter_result["sceneId"],
            "block_001",
        )

        self.assertFalse(placeholder_result["alreadyBound"])
        self.assertEqual(placeholder_result["asset"]["type"], "voice")

        asset_name = placeholder_result["asset"]["name"]
        match_result = run_editor.match_voice_files_to_placeholders(
            [build_upload_payload(f"{asset_name}.wav", build_fake_wav_bytes())],
            [placeholder_result["assetId"]],
        )

        self.assertEqual(match_result["matchedCount"], 1)
        matched_asset = match_result["assets"][0]
        self.assertTrue((run_editor.TEMPLATE_DIR / matched_asset["path"]).is_file())

        bundle = run_editor.load_project_bundle()
        saved_block = bundle["chapters"][0]["scenes"][0]["blocks"][0]
        self.assertEqual(saved_block["voiceAssetId"], placeholder_result["assetId"])

    def test_legacy_project_auto_migrates_when_opened(self) -> None:
        legacy_dir = self.projects_dir / "legacy_story"
        chapters_dir = legacy_dir / "data" / "chapters"
        chapters_dir.mkdir(parents=True, exist_ok=True)

        run_editor.write_json(
            legacy_dir / "project.json",
            {
                "title": "旧项目",
                "template": "legacy_template",
                "resolution": {"width": 1280, "height": 720},
                "chapterOrder": ["missing_chapter", "chapter_opening"],
                "createdAt": "2026-04-01T10:00:00+08:00",
            },
        )
        run_editor.write_json(
            legacy_dir / "data" / "assets.json",
            [
                {
                    "type": "background",
                    "name": "旧背景",
                    "path": "assets/backgrounds/legacy_bg.png",
                }
            ],
        )
        run_editor.write_json(
            legacy_dir / "data" / "characters.json",
            [
                {
                    "displayName": "旧角色",
                    "defaultPosition": "unknown",
                    "expressions": [
                        {
                            "name": "默认",
                            "spriteAssetId": "sprite_legacy_default",
                        }
                    ],
                }
            ],
        )
        run_editor.write_json(
            chapters_dir / "chapter_01.json",
            {
                "chapterId": "chapter_opening",
                "name": "旧章节",
                "scenes": [
                    {
                        "name": "旧开场",
                        "blocks": [
                            {
                                "type": "dialogue",
                                "text": "这是旧格式里的第一句。",
                            }
                        ],
                    },
                    {
                        "id": "scene_ready",
                        "blocks": "not-a-list",
                    },
                ],
            },
        )

        summary = run_editor.activate_project("legacy_story")
        bundle = run_editor.load_project_bundle()

        self.assertEqual(summary["projectId"], "legacy_story")
        self.assertEqual(bundle["project"]["formatVersion"], run_editor.PROJECT_FORMAT_VERSION)
        self.assertEqual(bundle["project"]["projectId"], "legacy_story")
        self.assertEqual(bundle["project"]["releaseVersion"], run_editor.DEFAULT_EXPORT_RELEASE_VERSION)
        self.assertEqual(bundle["project"]["editorMode"], run_editor.DEFAULT_EDITOR_MODE)
        self.assertEqual(bundle["project"]["chapterOrder"], ["chapter_opening"])
        self.assertTrue(bundle["project"]["entrySceneId"])

        assets_doc = run_editor.read_json(legacy_dir / "data" / "assets.json")
        self.assertEqual(assets_doc["formatVersion"], run_editor.PROJECT_FORMAT_VERSION)
        self.assertEqual(len(assets_doc["assets"]), 1)
        self.assertTrue(assets_doc["assets"][0]["id"].startswith("bg_"))
        self.assertEqual(assets_doc["assets"][0]["tags"], [])

        characters_doc = run_editor.read_json(legacy_dir / "data" / "characters.json")
        self.assertEqual(characters_doc["formatVersion"], run_editor.PROJECT_FORMAT_VERSION)
        self.assertEqual(len(characters_doc["characters"]), 1)
        self.assertTrue(characters_doc["characters"][0]["id"].startswith("char_"))
        self.assertEqual(characters_doc["characters"][0]["defaultPosition"], "center")
        self.assertEqual(characters_doc["characters"][0]["presentation"]["mode"], "sprite")
        self.assertIn("live2d", characters_doc["characters"][0]["presentation"])
        self.assertTrue(characters_doc["characters"][0]["expressions"][0]["id"].startswith("expr_"))
        self.assertEqual(characters_doc["characters"][0]["expressions"][0]["layerAssetIds"], [])
        self.assertEqual(run_editor.choose_smart_asset_type("hero.model3.json"), "live2d")
        self.assertEqual(run_editor.choose_smart_asset_type("hero.pose3.json"), "live2d")
        self.assertEqual(run_editor.choose_smart_asset_type("hero.glb"), "model3d")

        variables_doc = run_editor.read_json(legacy_dir / "data" / "variables.json")
        self.assertEqual(variables_doc["formatVersion"], run_editor.PROJECT_FORMAT_VERSION)
        self.assertEqual(variables_doc["variables"], [])

        chapter_doc = run_editor.read_json(chapters_dir / "chapter_01.json")
        self.assertEqual(chapter_doc["formatVersion"], run_editor.PROJECT_FORMAT_VERSION)
        self.assertEqual(chapter_doc["sceneOrder"], [scene["id"] for scene in chapter_doc["scenes"]])
        self.assertEqual(chapter_doc["scenes"][0]["status"], "drafting")
        self.assertEqual(chapter_doc["scenes"][0]["priority"], "normal")
        self.assertEqual(chapter_doc["scenes"][0]["blocks"][0]["id"], "block_001")
        self.assertEqual(chapter_doc["scenes"][1]["blocks"], [])

        history = run_editor.build_history_payload(legacy_dir)
        self.assertGreaterEqual(history["totalSnapshots"], 2)
        self.assertEqual(history["currentSnapshot"]["kind"], "migration")

    def test_web_export_build_smoke(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()

        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {
                    "id": "block_001",
                    "type": "dialogue",
                    "speakerId": "heroine",
                    "expressionId": "",
                    "text": "这是网页导出烟测。",
                }
            ],
        )

        export_result = run_editor.export_web_build()

        build_dir = Path(export_result["buildPath"])
        manifest_path = Path(export_result["manifestPath"])
        self.assertEqual(export_result["target"], run_editor.EXPORT_TARGET_WEB)
        self.assertTrue((build_dir / "index.html").is_file())
        self.assertTrue((build_dir / "player.js").is_file())
        self.assertTrue((build_dir / "player.css").is_file())
        self.assertTrue((build_dir / "launch_splash.svg").is_file())
        self.assertTrue((build_dir / "app_icon.png").is_file())
        self.assertTrue((build_dir / "app_icon.ico").is_file())
        self.assertTrue(manifest_path.is_file())

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["engine"]["exportTarget"], run_editor.EXPORT_TARGET_WEB)
        self.assert_export_manifest_has_subtle_engine_signature(manifest)
        self.assertEqual(
            manifest["engine"]["releaseVersion"],
            run_editor.DEFAULT_EXPORT_RELEASE_VERSION,
        )
        provenance = self.assert_export_provenance_file(
            export_result,
            {"export_manifest.json", "index.html", "player.js", "player.css"},
        )
        self.assertEqual(provenance["build"]["target"], run_editor.EXPORT_TARGET_WEB)
        self.assert_export_provenance_verifier_detects_tamper(export_result, "player.css")

    def test_native_runtime_release_check_flags_variable_logic_errors(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()
        ending_result = run_editor.create_scene(chapter_result["chapterId"], "结局")
        run_editor.save_project_settings(
            variables={
                "variables": [
                    {
                        "id": "var_route",
                        "name": "路线标记",
                        "type": "string",
                        "defaultValue": "common",
                    },
                    {
                        "id": "var_flag",
                        "name": "剧情开关",
                        "type": "boolean",
                        "defaultValue": "not-a-boolean",
                    },
                    {
                        "id": "var_score",
                        "name": "分数",
                        "type": "number",
                        "defaultValue": 150,
                        "min": 0,
                        "max": 100,
                    },
                    {
                        "id": "var_bad_range",
                        "name": "坏范围",
                        "type": "number",
                        "defaultValue": 5,
                        "min": 10,
                        "max": 1,
                    },
                ]
            },
        )

        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {
                    "id": "block_intro",
                    "type": "narration",
                    "text": "这里故意放一些坏逻辑，验证发布前自检会拦截。",
                },
                {
                    "id": "block_bad_add",
                    "type": "variable_add",
                    "variableId": "var_route",
                    "value": 1,
                },
                {
                    "id": "block_bad_choice",
                    "type": "choice",
                    "options": [
                        {
                            "id": "choice_001",
                            "text": "继续",
                            "gotoSceneId": ending_result["sceneId"],
                            "effects": [
                                {
                                    "type": "variable_set",
                                    "variableId": "var_missing",
                                    "value": True,
                                }
                            ],
                        }
                    ],
                },
                {
                    "id": "block_bad_condition",
                    "type": "condition",
                    "branches": [
                        {
                            "id": "branch_001",
                            "when": [
                                {
                                    "variableId": "var_route",
                                    "operator": ">",
                                    "value": "heroine",
                                }
                            ],
                            "gotoSceneId": "scene_missing",
                        }
                    ],
                    "elseGotoSceneId": ending_result["sceneId"],
                },
            ],
        )

        export_result = run_editor.export_native_runtime_build()
        build_dir = Path(export_result["buildPath"])
        release_check_payload = json.loads((build_dir / run_editor.NATIVE_RUNTIME_RELEASE_CHECK_NAME).read_text(encoding="utf-8"))
        issue_codes = {issue.get("code") for issue in release_check_payload["issues"]}

        self.assertEqual(release_check_payload["status"], "fail")
        self.assertEqual(release_check_payload["summary"]["logicIssueCount"], 7)
        self.assertTrue(
            {
                "logic_variable_default_type_mismatch",
                "logic_variable_default_out_of_range",
                "logic_variable_range_invalid",
                "logic_variable_type_mismatch",
                "logic_variable_missing",
                "logic_condition_operator_mismatch",
                "logic_target_missing",
            }
            <= issue_codes
        )

    def test_native_runtime_export_build_smoke(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()
        ui_assets = run_editor.import_assets(
            "ui",
            [
                build_upload_payload("title_background.png", build_fake_png_bytes()),
                build_upload_payload("title_logo.png", build_fake_png_bytes()),
                build_upload_payload("panel_frame.png", build_fake_png_bytes()),
                build_upload_payload("button_frame.png", build_fake_png_bytes()),
                build_upload_payload("button_hover_frame.png", build_fake_png_bytes()),
                build_upload_payload("button_pressed_frame.png", build_fake_png_bytes()),
                build_upload_payload("button_disabled_frame.png", build_fake_png_bytes()),
                build_upload_payload("save_slot_frame.png", build_fake_png_bytes()),
                build_upload_payload("system_panel_frame.png", build_fake_png_bytes()),
                build_upload_payload("ui_overlay.png", build_fake_png_bytes()),
            ],
        )["assets"]
        run_editor.save_project_settings(
            language="ja-JP",
            supported_languages=["zh-CN", "ja-JP", "en-US"],
            runtime_settings={"formalSaveSlotCount": 60},
            game_ui_config={
                "preset": "paper",
                "layoutPreset": "compact",
                "titleLayout": "left",
                "fontStyle": "serif",
                "surfaceStyle": "solid",
                "brandMode": "project",
                "sidePanelMode": "compact",
                "sidePanelPosition": "left",
                "topbarPosition": "top",
                "hudPosition": "bottom-left",
                "titleCardAnchor": "left",
                "titleCardOffsetXPercent": 3,
                "titleCardOffsetYPercent": 2,
                "layoutGap": 16,
                "sidePanelWidth": 280,
                "titleBackgroundAssetId": ui_assets[0]["id"],
                "titleLogoAssetId": ui_assets[1]["id"],
                "titleBackgroundFit": "contain",
                "titleBackgroundOpacity": 33,
                "panelFrameAssetId": ui_assets[2]["id"],
                "panelFrameSlice": {"top": 9, "right": 11, "bottom": 13, "left": 15},
                "buttonFrameAssetId": ui_assets[3]["id"],
                "buttonHoverFrameAssetId": ui_assets[4]["id"],
                "buttonPressedFrameAssetId": ui_assets[5]["id"],
                "buttonDisabledFrameAssetId": ui_assets[6]["id"],
                "panelFrameOpacity": 22,
                "buttonFrameOpacity": 12,
                "buttonFrameSlice": {"top": 7, "right": 12, "bottom": 7, "left": 12},
                "saveSlotFrameAssetId": ui_assets[7]["id"],
                "systemPanelFrameAssetId": ui_assets[8]["id"],
                "uiOverlayAssetId": ui_assets[9]["id"],
                "uiOverlayOpacity": 5,
            },
        )

        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {"id": "block_001", "type": "background", "assetId": ""},
                {
                    "id": "block_001b",
                    "type": "particle_effect",
                    "action": "start",
                    "preset": "snow",
                    "intensity": "medium",
                    "speed": "medium",
                    "wind": "still",
                    "area": "full",
                },
                {"id": "block_001c", "type": "screen_flash", "color": "white", "intensity": "soft", "duration": "short"},
                {"id": "block_001d", "type": "camera_zoom", "action": "zoom_in", "strength": "light", "focus": "center"},
                {"id": "block_001e", "type": "screen_filter", "action": "apply", "preset": "memory", "strength": "soft"},
                {
                    "id": "block_002",
                    "type": "dialogue",
                    "speakerId": "heroine",
                    "expressionId": "",
                    "text": "这是原生 Runtime 包烟测。",
                },
            ],
        )

        export_result = run_editor.export_native_runtime_build()

        build_dir = Path(export_result["buildPath"])
        manifest_path = Path(export_result["manifestPath"])
        self.assertEqual(export_result["target"], run_editor.EXPORT_TARGET_NATIVE_RUNTIME)
        self.assertTrue((build_dir / "game_data.json").is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_README_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_REQUIREMENTS_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_BUILD_REQUIREMENTS_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_VIDEO_REQUIREMENTS_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_APP_BUILDER_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_BRAND_LOGO_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_RELEASE_CHECK_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_RC_REPORT_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_RELEASE_CONTROL_REPORT_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_RELEASE_CONTROL_JSON_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_FILE_INTEGRITY_REPORT_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_FILE_INTEGRITY_MARKDOWN_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_3D_ASSET_REPORT_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_3D_ASSET_SUMMARY_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_3D_ASSET_DIGEST_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_MAC_COMMAND_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_LINUX_COMMAND_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_WINDOWS_COMMAND_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_MAC_RC_COMMAND_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_LINUX_RC_COMMAND_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_WINDOWS_RC_COMMAND_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_MAC_RELEASE_CONTROL_COMMAND_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_LINUX_RELEASE_CONTROL_COMMAND_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_WINDOWS_RELEASE_CONTROL_COMMAND_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_MAC_FILE_INTEGRITY_COMMAND_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_LINUX_FILE_INTEGRITY_COMMAND_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_WINDOWS_FILE_INTEGRITY_COMMAND_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_MAC_APP_BUILDER_COMMAND_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_LINUX_APP_BUILDER_COMMAND_NAME).is_file())
        self.assertTrue((build_dir / run_editor.NATIVE_RUNTIME_WINDOWS_APP_BUILDER_COMMAND_NAME).is_file())
        self.assertTrue(Path(export_result["archivePath"]).is_file())
        self.assertTrue(Path(export_result["archiveChecksumPath"]).is_file())
        self.assertTrue(Path(export_result["archiveChecksumJsonPath"]).is_file())
        self.assertTrue(Path(export_result["archiveVerifierMacPath"]).is_file())
        self.assertTrue(Path(export_result["archiveVerifierLinuxPath"]).is_file())
        self.assertTrue(Path(export_result["archiveVerifierWindowsPath"]).is_file())
        self.assertTrue(Path(export_result["releaseArtifactIndexPath"]).is_file())
        self.assertTrue(Path(export_result["releaseArtifactIndexJsonPath"]).is_file())
        self.assertTrue(Path(export_result["releaseNotesPath"]).is_file())
        self.assertTrue(manifest_path.is_file())
        native_game_data = json.loads((build_dir / "game_data.json").read_text(encoding="utf-8"))
        self.assertEqual(native_game_data["i18n"]["defaultLanguage"], "ja-JP")
        self.assertEqual(native_game_data["i18n"]["supportedLanguages"], ["zh-CN", "ja-JP", "en-US"])
        native_player_source = (build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME).read_text(encoding="utf-8")
        self.assertIn('("language", "语言")', native_player_source)

        archive_sha256 = hashlib.sha256(Path(export_result["archivePath"]).read_bytes()).hexdigest()
        self.assertEqual(export_result["archiveSha256"], archive_sha256)
        self.assertTrue(export_result["archiveChecksumPublicUrl"].endswith(".zip.sha256"))
        self.assertTrue(export_result["archiveChecksumJsonPublicUrl"].endswith(".zip.checksum.json"))
        self.assertTrue(export_result["archiveVerifierMacPublicUrl"].endswith(".zip.verify.command"))
        self.assertTrue(export_result["archiveVerifierLinuxPublicUrl"].endswith(".zip.verify.sh"))
        self.assertTrue(export_result["archiveVerifierWindowsPublicUrl"].endswith(".zip.verify.bat"))
        self.assertTrue(export_result["releaseNotesPublicUrl"].endswith(".zip.release-notes.md"))
        self.assertIn(archive_sha256, Path(export_result["archiveChecksumPath"]).read_text(encoding="utf-8"))
        self.assertIn(archive_sha256, Path(export_result["archiveVerifierMacPath"]).read_text(encoding="utf-8"))
        self.assertIn(archive_sha256, Path(export_result["archiveVerifierWindowsPath"]).read_text(encoding="utf-8"))
        archive_checksum_payload = json.loads(Path(export_result["archiveChecksumJsonPath"]).read_text(encoding="utf-8"))
        self.assertEqual(archive_checksum_payload["algorithm"], "sha256")
        self.assertEqual(archive_checksum_payload["sha256"], archive_sha256)
        self.assertEqual(archive_checksum_payload["archiveName"], export_result["archiveName"])
        self.assertGreater(archive_checksum_payload["archiveSizeBytes"], 0)
        release_artifact_payload = json.loads(Path(export_result["releaseArtifactIndexJsonPath"]).read_text(encoding="utf-8"))
        self.assertEqual(release_artifact_payload["archive"]["name"], export_result["archiveName"])
        self.assertEqual(release_artifact_payload["archive"]["sha256"], archive_sha256)
        self.assertEqual(release_artifact_payload["archive"]["releaseNotesDraft"], export_result["releaseNotesName"])
        self.assertEqual(release_artifact_payload["archive"]["verifiers"]["macos"], export_result["archiveVerifierMacName"])
        self.assertTrue(any(item["name"] == export_result["archiveVerifierWindowsName"] for item in release_artifact_payload["uploadArtifacts"]))
        self.assertTrue(
            any(
                item["name"] == export_result["releaseNotesName"] and item["type"] == "release_notes_draft"
                for item in release_artifact_payload["uploadArtifacts"]
            )
        )
        self.assertGreaterEqual(export_result["releaseArtifactUploadCount"], 5)
        self.assertTrue(export_result["releaseArtifactIndexPublicUrl"].endswith(".zip.release-artifacts.md"))
        self.assertTrue(export_result["releaseArtifactIndexJsonPublicUrl"].endswith(".zip.release-artifacts.json"))
        release_artifact_markdown = Path(export_result["releaseArtifactIndexPath"]).read_text(encoding="utf-8")
        self.assertIn("# 原生 Runtime 发布附件索引", release_artifact_markdown)
        self.assertIn("运行 .verify.command / .verify.sh / .verify.bat", release_artifact_markdown)
        self.assertIn("Release Notes 摘要", release_artifact_markdown)
        release_notes_markdown = Path(export_result["releaseNotesPath"]).read_text(encoding="utf-8")
        self.assertIn("# Canvasia Engine 原生 Runtime Preview", release_notes_markdown)
        self.assertIn("GitHub Release", release_notes_markdown)
        self.assertIn(export_result["archiveName"], release_notes_markdown)
        self.assertIn(archive_sha256, release_notes_markdown)
        self.assertIn("下载后验证", release_notes_markdown)

        linux_archive_verifier = subprocess.run(
            ["bash", str(Path(export_result["archiveVerifierLinuxPath"]))],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(linux_archive_verifier.returncode, 0, linux_archive_verifier.stdout + linux_archive_verifier.stderr)
        self.assertIn("SHA-256", linux_archive_verifier.stdout)

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["engine"]["exportTarget"], run_editor.EXPORT_TARGET_NATIVE_RUNTIME)
        self.assert_export_manifest_has_subtle_engine_signature(manifest)
        provenance = self.assert_export_provenance_file(
            export_result,
            {
                "export_manifest.json",
                run_editor.NATIVE_RUNTIME_PLAYER_NAME,
                "game_data.json",
            },
        )
        self.assertEqual(provenance["build"]["target"], run_editor.EXPORT_TARGET_NATIVE_RUNTIME)
        self.assertEqual(manifest["runtime"]["mode"], "pygame_native")
        self.assertTrue(manifest["runtime"]["canBuildStandaloneApp"])
        self.assertEqual(manifest["runtime"]["releaseCandidateReport"], run_editor.NATIVE_RUNTIME_RC_REPORT_NAME)
        self.assertEqual(manifest["runtime"]["releaseControlReport"], run_editor.NATIVE_RUNTIME_RELEASE_CONTROL_REPORT_NAME)
        self.assertEqual(manifest["runtime"]["releaseControlJson"], run_editor.NATIVE_RUNTIME_RELEASE_CONTROL_JSON_NAME)
        self.assertEqual(manifest["runtime"]["releaseControlReporter"]["macos"], run_editor.NATIVE_RUNTIME_MAC_RELEASE_CONTROL_COMMAND_NAME)
        self.assertEqual(manifest["runtime"]["releaseControlReporter"]["linux"], run_editor.NATIVE_RUNTIME_LINUX_RELEASE_CONTROL_COMMAND_NAME)
        self.assertEqual(manifest["runtime"]["releaseControlReporter"]["windows"], run_editor.NATIVE_RUNTIME_WINDOWS_RELEASE_CONTROL_COMMAND_NAME)
        self.assertEqual(manifest["runtime"]["acceptanceReport"], run_editor.NATIVE_RUNTIME_ACCEPTANCE_REPORT_NAME)
        self.assertEqual(manifest["runtime"]["acceptanceJson"], run_editor.NATIVE_RUNTIME_ACCEPTANCE_JSON_NAME)
        self.assertEqual(manifest["runtime"]["acceptanceReporter"]["macos"], run_editor.NATIVE_RUNTIME_MAC_ACCEPTANCE_COMMAND_NAME)
        self.assertEqual(manifest["runtime"]["acceptanceReporter"]["linux"], run_editor.NATIVE_RUNTIME_LINUX_ACCEPTANCE_COMMAND_NAME)
        self.assertEqual(manifest["runtime"]["acceptanceReporter"]["windows"], run_editor.NATIVE_RUNTIME_WINDOWS_ACCEPTANCE_COMMAND_NAME)
        self.assertEqual(manifest["runtime"]["fileIntegrityReport"], run_editor.NATIVE_RUNTIME_FILE_INTEGRITY_REPORT_NAME)
        self.assertEqual(manifest["runtime"]["fileIntegrityMarkdown"], run_editor.NATIVE_RUNTIME_FILE_INTEGRITY_MARKDOWN_NAME)
        self.assertEqual(manifest["runtime"]["fileIntegrityChecker"]["macos"], run_editor.NATIVE_RUNTIME_MAC_FILE_INTEGRITY_COMMAND_NAME)
        self.assertEqual(manifest["runtime"]["fileIntegrityChecker"]["linux"], run_editor.NATIVE_RUNTIME_LINUX_FILE_INTEGRITY_COMMAND_NAME)
        self.assertEqual(manifest["runtime"]["fileIntegrityChecker"]["windows"], run_editor.NATIVE_RUNTIME_WINDOWS_FILE_INTEGRITY_COMMAND_NAME)
        self.assertEqual(manifest["runtime"]["asset3dReport"], run_editor.NATIVE_RUNTIME_3D_ASSET_REPORT_NAME)
        self.assertEqual(manifest["runtime"]["asset3dSummary"], run_editor.NATIVE_RUNTIME_3D_ASSET_SUMMARY_NAME)
        self.assertEqual(manifest["runtime"]["asset3dDigest"], run_editor.NATIVE_RUNTIME_3D_ASSET_DIGEST_NAME)
        self.assertEqual(manifest["files"]["releaseCandidateReport"], run_editor.NATIVE_RUNTIME_RC_REPORT_NAME)
        self.assertEqual(manifest["files"]["releaseControlReport"], run_editor.NATIVE_RUNTIME_RELEASE_CONTROL_REPORT_NAME)
        self.assertEqual(manifest["files"]["releaseControlJson"], run_editor.NATIVE_RUNTIME_RELEASE_CONTROL_JSON_NAME)
        self.assertEqual(manifest["files"]["macReleaseControlReporter"], run_editor.NATIVE_RUNTIME_MAC_RELEASE_CONTROL_COMMAND_NAME)
        self.assertEqual(manifest["files"]["linuxReleaseControlReporter"], run_editor.NATIVE_RUNTIME_LINUX_RELEASE_CONTROL_COMMAND_NAME)
        self.assertEqual(manifest["files"]["windowsReleaseControlReporter"], run_editor.NATIVE_RUNTIME_WINDOWS_RELEASE_CONTROL_COMMAND_NAME)
        self.assertEqual(manifest["files"]["acceptanceReport"], run_editor.NATIVE_RUNTIME_ACCEPTANCE_REPORT_NAME)
        self.assertEqual(manifest["files"]["acceptanceJson"], run_editor.NATIVE_RUNTIME_ACCEPTANCE_JSON_NAME)
        self.assertEqual(manifest["files"]["macAcceptanceReporter"], run_editor.NATIVE_RUNTIME_MAC_ACCEPTANCE_COMMAND_NAME)
        self.assertEqual(manifest["files"]["linuxAcceptanceReporter"], run_editor.NATIVE_RUNTIME_LINUX_ACCEPTANCE_COMMAND_NAME)
        self.assertEqual(manifest["files"]["windowsAcceptanceReporter"], run_editor.NATIVE_RUNTIME_WINDOWS_ACCEPTANCE_COMMAND_NAME)
        self.assertEqual(manifest["files"]["fileIntegrityReport"], run_editor.NATIVE_RUNTIME_FILE_INTEGRITY_REPORT_NAME)
        self.assertEqual(manifest["files"]["fileIntegrityMarkdown"], run_editor.NATIVE_RUNTIME_FILE_INTEGRITY_MARKDOWN_NAME)
        self.assertEqual(manifest["files"]["macFileIntegrityChecker"], run_editor.NATIVE_RUNTIME_MAC_FILE_INTEGRITY_COMMAND_NAME)
        self.assertEqual(manifest["files"]["linuxFileIntegrityChecker"], run_editor.NATIVE_RUNTIME_LINUX_FILE_INTEGRITY_COMMAND_NAME)
        self.assertEqual(manifest["files"]["windowsFileIntegrityChecker"], run_editor.NATIVE_RUNTIME_WINDOWS_FILE_INTEGRITY_COMMAND_NAME)
        self.assertEqual(manifest["files"]["asset3dReport"], run_editor.NATIVE_RUNTIME_3D_ASSET_REPORT_NAME)
        self.assertEqual(manifest["files"]["asset3dSummary"], run_editor.NATIVE_RUNTIME_3D_ASSET_SUMMARY_NAME)
        self.assertEqual(manifest["files"]["asset3dDigest"], run_editor.NATIVE_RUNTIME_3D_ASSET_DIGEST_NAME)

        exported_3d_digest = json.loads((build_dir / run_editor.NATIVE_RUNTIME_3D_ASSET_DIGEST_NAME).read_text(encoding="utf-8"))
        self.assertEqual(exported_3d_digest["status"], export_result["asset3dReportDigest"]["status"])
        self.assertTrue(export_result["asset3dDigestPublicUrl"].endswith(run_editor.NATIVE_RUNTIME_3D_ASSET_DIGEST_NAME))

        release_check_payload = json.loads((build_dir / run_editor.NATIVE_RUNTIME_RELEASE_CHECK_NAME).read_text(encoding="utf-8"))
        self.assertEqual(release_check_payload["status"], "pass")
        self.assertEqual(release_check_payload["summary"]["errors"], 0)

        exported_rc_payload = json.loads((build_dir / run_editor.NATIVE_RUNTIME_RC_REPORT_NAME).read_text(encoding="utf-8"))
        self.assertIn(exported_rc_payload["status"], {"preview_ready", "preview_ready_with_warnings"})
        self.assertEqual(exported_rc_payload["summary"]["blockers"], 0)
        self.assertEqual(export_result["releaseCandidateReportStatus"], exported_rc_payload["status"])
        self.assertEqual(export_result["releaseCandidateReportSummary"]["blockers"], 0)
        self.assertGreaterEqual(export_result["releaseCandidateReadinessEstimate"]["desktopPreviewPercent"], 75)
        self.assertTrue(export_result["releaseCandidateReportPublicUrl"].endswith(run_editor.NATIVE_RUNTIME_RC_REPORT_NAME))

        release_control_payload = json.loads((build_dir / run_editor.NATIVE_RUNTIME_RELEASE_CONTROL_JSON_NAME).read_text(encoding="utf-8"))
        self.assertEqual(release_control_payload["formatVersion"], 1)
        self.assertEqual(release_control_payload["project"]["title"], "自动化测试项目")
        self.assertIn(release_control_payload["qualityGate"]["status"], {"ready", "needs_review"})
        self.assertEqual(release_control_payload["releaseCheck"]["status"], "pass")
        self.assertIn(release_control_payload["releaseCandidate"]["status"], {"preview_ready", "preview_ready_with_warnings"})
        self.assertEqual(release_control_payload["asset3d"]["status"], export_result["asset3dReportDigest"]["status"])
        self.assertTrue(release_control_payload["nextSteps"])
        release_control_markdown = (build_dir / run_editor.NATIVE_RUNTIME_RELEASE_CONTROL_REPORT_NAME).read_text(encoding="utf-8")
        self.assertIn("# 原生 Runtime 发布总控报告", release_control_markdown)
        self.assertIn("## 核心指标", release_control_markdown)
        self.assertTrue(export_result["releaseControlReportPublicUrl"].endswith(run_editor.NATIVE_RUNTIME_RELEASE_CONTROL_REPORT_NAME))
        self.assertTrue(export_result["releaseControlJsonPublicUrl"].endswith(run_editor.NATIVE_RUNTIME_RELEASE_CONTROL_JSON_NAME))
        self.assertTrue(export_result["macReleaseControlReporterPublicUrl"].endswith(run_editor.NATIVE_RUNTIME_MAC_RELEASE_CONTROL_COMMAND_NAME))
        self.assertTrue(export_result["linuxReleaseControlReporterPublicUrl"].endswith(run_editor.NATIVE_RUNTIME_LINUX_RELEASE_CONTROL_COMMAND_NAME))
        self.assertTrue(export_result["windowsReleaseControlReporterPublicUrl"].endswith(run_editor.NATIVE_RUNTIME_WINDOWS_RELEASE_CONTROL_COMMAND_NAME))

        release_control_cli_json = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--release-control-json",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(release_control_cli_json.returncode, 0, release_control_cli_json.stdout + release_control_cli_json.stderr)
        release_control_cli_payload = json.loads(release_control_cli_json.stdout)
        self.assertEqual(release_control_cli_payload["project"]["title"], "自动化测试项目")
        self.assertIn(release_control_cli_payload["qualityGate"]["status"], {"ready", "needs_review"})

        release_control_cli_markdown = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--release-control-report",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(release_control_cli_markdown.returncode, 0, release_control_cli_markdown.stdout + release_control_cli_markdown.stderr)
        self.assertIn("# 原生 Runtime 发布总控报告", release_control_cli_markdown.stdout)

        release_control_cli_write = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--write-release-control-reports",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(release_control_cli_write.returncode, 0, release_control_cli_write.stdout + release_control_cli_write.stderr)

        integrity_payload = json.loads((build_dir / run_editor.NATIVE_RUNTIME_FILE_INTEGRITY_REPORT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(integrity_payload["formatVersion"], 1)
        self.assertEqual(integrity_payload["algorithm"], "sha256")
        self.assertGreater(integrity_payload["summary"]["fileCount"], 10)
        integrity_paths = {entry["path"] for entry in integrity_payload["files"]}
        self.assertIn("game_data.json", integrity_paths)
        self.assertIn(run_editor.NATIVE_RUNTIME_PLAYER_NAME, integrity_paths)
        self.assertIn("export_manifest.json", integrity_paths)
        self.assertIn(run_editor.EXPORT_PROVENANCE_FILE_NAME, integrity_paths)
        self.assertNotIn(run_editor.NATIVE_RUNTIME_FILE_INTEGRITY_REPORT_NAME, integrity_paths)
        integrity_markdown = (build_dir / run_editor.NATIVE_RUNTIME_FILE_INTEGRITY_MARKDOWN_NAME).read_text(encoding="utf-8")
        self.assertIn("# 原生 Runtime 文件完整性报告", integrity_markdown)
        self.assertTrue(export_result["fileIntegrityReportPublicUrl"].endswith(run_editor.NATIVE_RUNTIME_FILE_INTEGRITY_REPORT_NAME))
        self.assertTrue(export_result["fileIntegrityMarkdownPublicUrl"].endswith(run_editor.NATIVE_RUNTIME_FILE_INTEGRITY_MARKDOWN_NAME))
        self.assertTrue(export_result["macFileIntegrityCheckerPublicUrl"].endswith(run_editor.NATIVE_RUNTIME_MAC_FILE_INTEGRITY_COMMAND_NAME))
        self.assertTrue(export_result["linuxFileIntegrityCheckerPublicUrl"].endswith(run_editor.NATIVE_RUNTIME_LINUX_FILE_INTEGRITY_COMMAND_NAME))
        self.assertTrue(export_result["windowsFileIntegrityCheckerPublicUrl"].endswith(run_editor.NATIVE_RUNTIME_WINDOWS_FILE_INTEGRITY_COMMAND_NAME))

        acceptance_payload = json.loads((build_dir / run_editor.NATIVE_RUNTIME_ACCEPTANCE_JSON_NAME).read_text(encoding="utf-8"))
        self.assertEqual(acceptance_payload["formatVersion"], 1)
        self.assertIn(acceptance_payload["acceptanceGate"]["status"], {"ready_for_manual_acceptance", "needs_manual_review"})
        self.assertGreaterEqual(len(acceptance_payload["automatedChecks"]), 5)
        self.assertTrue({"macos", "windows", "linux"} <= {entry["id"] for entry in acceptance_payload["platformMatrix"]})
        self.assertTrue(acceptance_payload["manualCheckGroups"])
        self.assertTrue(acceptance_payload["recommendedCommands"])
        acceptance_markdown = (build_dir / run_editor.NATIVE_RUNTIME_ACCEPTANCE_REPORT_NAME).read_text(encoding="utf-8")
        self.assertIn("# 原生 Runtime 发布验收清单", acceptance_markdown)
        self.assertIn("## 人工逐项点测", acceptance_markdown)
        self.assertIn("- [ ]", acceptance_markdown)
        self.assertEqual(export_result["acceptanceStatus"], acceptance_payload["acceptanceGate"]["status"])
        self.assertTrue(export_result["acceptanceReportPublicUrl"].endswith(run_editor.NATIVE_RUNTIME_ACCEPTANCE_REPORT_NAME))
        self.assertTrue(export_result["acceptanceJsonPublicUrl"].endswith(run_editor.NATIVE_RUNTIME_ACCEPTANCE_JSON_NAME))
        self.assertTrue(export_result["macAcceptanceReporterPublicUrl"].endswith(run_editor.NATIVE_RUNTIME_MAC_ACCEPTANCE_COMMAND_NAME))
        self.assertTrue(export_result["linuxAcceptanceReporterPublicUrl"].endswith(run_editor.NATIVE_RUNTIME_LINUX_ACCEPTANCE_COMMAND_NAME))
        self.assertTrue(export_result["windowsAcceptanceReporterPublicUrl"].endswith(run_editor.NATIVE_RUNTIME_WINDOWS_ACCEPTANCE_COMMAND_NAME))

        integrity_cli_verify = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--verify-file-integrity",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(integrity_cli_verify.returncode, 0, integrity_cli_verify.stdout + integrity_cli_verify.stderr)
        integrity_verify_payload = json.loads(integrity_cli_verify.stdout)
        self.assertEqual(integrity_verify_payload["status"], "pass")
        self.assertEqual(integrity_verify_payload["summary"]["missingCount"], 0)
        self.assertEqual(integrity_verify_payload["summary"]["changedCount"], 0)

        acceptance_cli_json = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--acceptance-check",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(acceptance_cli_json.returncode, 0, acceptance_cli_json.stdout + acceptance_cli_json.stderr)
        acceptance_cli_payload = json.loads(acceptance_cli_json.stdout)
        self.assertEqual(acceptance_cli_payload["project"]["title"], "自动化测试项目")
        self.assertIn(
            acceptance_cli_payload["acceptanceGate"]["status"],
            {"ready_for_manual_acceptance", "needs_manual_review"},
        )

        acceptance_cli_markdown = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--acceptance-report",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            acceptance_cli_markdown.returncode,
            0,
            acceptance_cli_markdown.stdout + acceptance_cli_markdown.stderr,
        )
        self.assertIn("# 原生 Runtime 发布验收清单", acceptance_cli_markdown.stdout)

        acceptance_cli_write = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--write-acceptance-reports",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(acceptance_cli_write.returncode, 0, acceptance_cli_write.stdout + acceptance_cli_write.stderr)

        doctor_description = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--doctor",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(doctor_description.returncode, 0, doctor_description.stdout + doctor_description.stderr)
        doctor_payload = json.loads(doctor_description.stdout)
        self.assertEqual(doctor_payload["status"], "pass")
        self.assertEqual(doctor_payload["summary"]["failed"], 0)
        self.assertTrue(
            {
                "bundle_structure",
                "release_check",
                "save_load",
                "settings",
                "asset3d_report",
                "model_preview_bridge",
                "scene3d_preview_bridge",
                "video_preview_probe",
            }
            <= {check["id"] for check in doctor_payload["checks"]}
        )

        rc_description = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--release-candidate-report",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(rc_description.returncode, 0, rc_description.stdout + rc_description.stderr)
        rc_payload = json.loads(rc_description.stdout)
        self.assertIn(rc_payload["status"], {"preview_ready", "preview_ready_with_warnings"})
        self.assertEqual(rc_payload["summary"]["blockers"], 0)
        self.assertEqual(rc_payload["summary"]["asset3dStatus"], "no_3d_assets")
        self.assertGreaterEqual(rc_payload["readinessEstimate"]["desktopPreviewPercent"], 75)
        self.assertTrue({"macos", "windows", "linux"} <= {entry["id"] for entry in rc_payload["platformMatrix"]})
        self.assertTrue(
            {"doctor_release_check", "packaging_scaffold"} <= {gate["id"] for gate in rc_payload["gates"]}
        )
        self.assertTrue(rc_payload["nextActions"])

        game_data = json.loads((build_dir / "game_data.json").read_text(encoding="utf-8"))
        self.assertIn("gameUiConfig", game_data["project"])
        self.assertEqual(game_data["project"]["gameUiConfig"]["preset"], "paper")
        self.assertEqual(game_data["project"]["gameUiConfig"]["layoutPreset"], "compact")
        self.assertEqual(game_data["project"]["gameUiConfig"]["titleLayout"], "left")
        self.assertEqual(game_data["project"]["gameUiConfig"]["sidePanelPosition"], "left")
        self.assertEqual(game_data["project"]["gameUiConfig"]["hudPosition"], "bottom-left")
        self.assertEqual(game_data["project"]["gameUiConfig"]["titleCardAnchor"], "left")
        self.assertEqual(game_data["project"]["gameUiConfig"]["sidePanelWidth"], 280)
        self.assertEqual(game_data["project"]["gameUiConfig"]["titleBackgroundAssetId"], ui_assets[0]["id"])
        self.assertEqual(game_data["project"]["gameUiConfig"]["titleLogoAssetId"], ui_assets[1]["id"])
        self.assertEqual(game_data["project"]["gameUiConfig"]["titleBackgroundFit"], "contain")
        self.assertEqual(game_data["project"]["gameUiConfig"]["titleBackgroundOpacity"], 33)
        self.assertEqual(game_data["project"]["gameUiConfig"]["panelFrameAssetId"], ui_assets[2]["id"])
        self.assertEqual(game_data["project"]["gameUiConfig"]["panelFrameSlice"], {"top": 9, "right": 11, "bottom": 13, "left": 15})
        self.assertEqual(game_data["project"]["gameUiConfig"]["buttonFrameAssetId"], ui_assets[3]["id"])
        self.assertEqual(game_data["project"]["gameUiConfig"]["buttonHoverFrameAssetId"], ui_assets[4]["id"])
        self.assertEqual(game_data["project"]["gameUiConfig"]["buttonPressedFrameAssetId"], ui_assets[5]["id"])
        self.assertEqual(game_data["project"]["gameUiConfig"]["buttonDisabledFrameAssetId"], ui_assets[6]["id"])
        self.assertEqual(game_data["project"]["gameUiConfig"]["buttonFrameSlice"], {"top": 7, "right": 12, "bottom": 7, "left": 12})
        self.assertEqual(game_data["project"]["gameUiConfig"]["saveSlotFrameAssetId"], ui_assets[7]["id"])
        self.assertEqual(game_data["project"]["gameUiConfig"]["systemPanelFrameAssetId"], ui_assets[8]["id"])
        self.assertEqual(game_data["project"]["gameUiConfig"]["uiOverlayAssetId"], ui_assets[9]["id"])

        app_builder_description = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_APP_BUILDER_NAME),
                "--describe",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(app_builder_description.returncode, 0, app_builder_description.stdout + app_builder_description.stderr)
        app_builder_payload = json.loads(app_builder_description.stdout)
        self.assertEqual(app_builder_payload["gameData"], "game_data.json")
        self.assertEqual(app_builder_payload["runtimePlayer"], run_editor.NATIVE_RUNTIME_PLAYER_NAME)
        self.assertEqual(app_builder_payload["outputDir"], "native_app_dist")
        self.assertEqual(app_builder_payload["packageManifest"], "native_app_package_manifest.json")
        self.assertTrue(app_builder_payload["plannedArchiveName"].endswith("-preview.zip"))
        self.assertEqual(app_builder_payload["optionalVideoRequirements"], run_editor.NATIVE_RUNTIME_VIDEO_REQUIREMENTS_NAME)
        self.assertIn(app_builder_payload["platform"], {"macos", "windows", "linux", "unknown"})
        self.assertTrue(app_builder_payload["bundleIdentifier"].startswith("com.canvasia."))
        self.assertTrue(app_builder_payload["distributionNotes"])
        self.assertTrue(app_builder_payload["dataEntries"])
        self.assertFalse(app_builder_payload["missingAssetPaths"])
        self.assertEqual(app_builder_payload["releaseCheck"]["status"], "pass")
        self.assertIn(app_builder_payload["releaseCandidateReport"]["status"], {"preview_ready", "preview_ready_with_warnings"})
        self.assertEqual(app_builder_payload["releaseCandidateReport"]["summary"]["blockers"], 0)
        self.assertEqual(app_builder_payload["releaseControl"]["reportName"], run_editor.NATIVE_RUNTIME_RELEASE_CONTROL_REPORT_NAME)
        self.assertEqual(app_builder_payload["releaseControl"]["jsonName"], run_editor.NATIVE_RUNTIME_RELEASE_CONTROL_JSON_NAME)
        self.assertTrue(app_builder_payload["releaseControl"]["report"]["exists"])
        self.assertTrue(app_builder_payload["releaseControl"]["json"]["exists"])
        self.assertTrue(all(entry["exists"] for entry in app_builder_payload["releaseControl"]["refreshers"]))
        self.assertIn(app_builder_payload["releaseControl"]["json"]["qualityGate"]["status"], {"ready", "needs_review"})
        self.assertIn("# 原生 Runtime 发布总控报告", app_builder_payload["releaseControl"]["report"]["preview"])
        self.assertEqual(app_builder_payload["fileIntegrity"]["reportName"], run_editor.NATIVE_RUNTIME_FILE_INTEGRITY_REPORT_NAME)
        self.assertEqual(app_builder_payload["fileIntegrity"]["markdownName"], run_editor.NATIVE_RUNTIME_FILE_INTEGRITY_MARKDOWN_NAME)
        self.assertTrue(app_builder_payload["fileIntegrity"]["report"]["exists"])
        self.assertTrue(app_builder_payload["fileIntegrity"]["markdown"]["exists"])
        self.assertTrue(all(entry["exists"] for entry in app_builder_payload["fileIntegrity"]["checkers"]))
        self.assertGreater(app_builder_payload["fileIntegrity"]["report"]["summary"]["fileCount"], 10)
        self.assertIn("# 原生 Runtime 文件完整性报告", app_builder_payload["fileIntegrity"]["markdown"]["preview"])
        self.assertEqual(app_builder_payload["asset3d"]["reportName"], run_editor.NATIVE_RUNTIME_3D_ASSET_REPORT_NAME)
        self.assertEqual(app_builder_payload["asset3d"]["summaryName"], run_editor.NATIVE_RUNTIME_3D_ASSET_SUMMARY_NAME)
        self.assertEqual(app_builder_payload["asset3d"]["digestName"], run_editor.NATIVE_RUNTIME_3D_ASSET_DIGEST_NAME)
        self.assertEqual(app_builder_payload["asset3d"]["report"]["status"], "no_3d_assets")
        self.assertTrue(app_builder_payload["asset3d"]["summary"]["exists"])
        self.assertTrue(app_builder_payload["asset3d"]["digest"]["exists"])
        self.assertEqual(app_builder_payload["asset3d"]["digest"]["status"], "no_3d_assets")
        self.assertIn("# 3D 资产清单摘要", app_builder_payload["asset3d"]["summary"]["preview"])
        self.assertEqual(app_builder_payload["video"]["backendReport"]["status"], "no_video")
        self.assertEqual(app_builder_payload["video"]["previewProbe"]["status"], "no_video")
        self.assertTrue(
            any(entry["source"] == run_editor.NATIVE_RUNTIME_BRAND_LOGO_NAME for entry in app_builder_payload["dataEntries"])
        )

        title_screen_description = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--describe-title-screen",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(title_screen_description.returncode, 0, title_screen_description.stdout + title_screen_description.stderr)
        title_screen_payload = json.loads(title_screen_description.stdout)
        self.assertEqual(title_screen_payload["status"], "ready")
        self.assertTrue(title_screen_payload["engineBrandLogoExists"])
        self.assertIn("start", {item["key"] for item in title_screen_payload["menuItems"]})
        self.assertIn("settings", {item["key"] for item in title_screen_payload["menuItems"]})

        validation = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--validate-bundle",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)

        save_load_validation = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--exercise-save-load",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(save_load_validation.returncode, 0, save_load_validation.stdout + save_load_validation.stderr)

        settings_validation = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--exercise-settings",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(settings_validation.returncode, 0, settings_validation.stdout + settings_validation.stderr)

        archive_validation = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--exercise-archives",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(archive_validation.returncode, 0, archive_validation.stdout + archive_validation.stderr)

        particle_validation = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--exercise-particles",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(particle_validation.returncode, 0, particle_validation.stdout + particle_validation.stderr)

        visual_effect_validation = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--exercise-visual-effects",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(visual_effect_validation.returncode, 0, visual_effect_validation.stdout + visual_effect_validation.stderr)

        profile_validation = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--exercise-profile",
                str(build_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(profile_validation.returncode, 0, profile_validation.stdout + profile_validation.stderr)

        save_dialog_description = subprocess.run(
            [
                sys.executable,
                str(build_dir / run_editor.NATIVE_RUNTIME_PLAYER_NAME),
                "--describe-save-dialog",
                str(build_dir),
                "--page",
                "1",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(save_dialog_description.returncode, 0, save_dialog_description.stdout + save_dialog_description.stderr)
        dialog_payload = json.loads(save_dialog_description.stdout)
        self.assertEqual(dialog_payload["slotCount"], 60)
        self.assertEqual(dialog_payload["pageCount"], 10)
        self.assertEqual(dialog_payload["page"], 1)
        self.assertEqual(dialog_payload["visibleSlots"][0]["slotIndex"], 6)

    def test_windows_nwjs_build_smoke(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()

        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {
                    "id": "block_001",
                    "type": "dialogue",
                    "speakerId": "heroine",
                    "expressionId": "",
                    "text": "这是 Windows 桌面导出烟测。",
                }
            ],
        )

        export_result = run_editor.export_windows_nwjs_build()

        manifest_path = Path(export_result["manifestPath"])
        self.assertEqual(export_result["target"], run_editor.EXPORT_TARGET_WINDOWS_NWJS)
        self.assertTrue(Path(export_result["launcherPath"]).is_file())
        self.assertTrue(Path(export_result["startHelperPath"]).is_file())
        self.assertTrue(Path(export_result["archivePath"]).is_file())
        self.assertTrue(manifest_path.is_file())

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["engine"]["exportTarget"], run_editor.EXPORT_TARGET_WINDOWS_NWJS)
        self.assert_export_manifest_has_subtle_engine_signature(manifest)
        provenance = self.assert_export_provenance_file(
            export_result,
            {"export_manifest.json", "app/index.html", "app/player.js", "app/player.css"},
        )
        self.assertEqual(provenance["build"]["target"], run_editor.EXPORT_TARGET_WINDOWS_NWJS)

    def test_macos_nwjs_build_smoke(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()

        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {
                    "id": "block_001",
                    "type": "dialogue",
                    "speakerId": "heroine",
                    "expressionId": "",
                    "text": "这是 macOS 桌面导出烟测。",
                }
            ],
        )

        export_result = run_editor.export_macos_nwjs_build()

        manifest_path = Path(export_result["manifestPath"])
        self.assertEqual(export_result["target"], run_editor.EXPORT_TARGET_MACOS_NWJS)
        self.assertTrue(Path(export_result["appBundlePath"]).is_dir())
        self.assertTrue(Path(export_result["startHelperPath"]).is_file())
        self.assertTrue(Path(export_result["archivePath"]).is_file())
        self.assertTrue(manifest_path.is_file())

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["engine"]["exportTarget"], run_editor.EXPORT_TARGET_MACOS_NWJS)
        self.assert_export_manifest_has_subtle_engine_signature(manifest)
        provenance = self.assert_export_provenance_file(
            export_result,
            {"export_manifest.json", "app/index.html", "app/player.js", "app/player.css"},
        )
        self.assertEqual(provenance["build"]["target"], run_editor.EXPORT_TARGET_MACOS_NWJS)
        self.assertEqual(manifest["runtime"]["version"], run_editor.NWJS_RUNTIME_VERSION)

    def test_project_i18n_settings_export_to_web_runtime(self) -> None:
        run_editor.create_blank_project("国际化测试")
        run_editor.save_project_settings(
            language="ja-JP",
            supported_languages=["zh-CN", "ja-JP", "en-US"],
        )
        chapter_result = run_editor.create_chapter("第一章", "教室")
        run_editor.write_json(
            run_editor.DATA_DIR / "characters.json",
            run_editor.normalize_characters_document(
                {
                    "characters": [
                        {
                            "id": "char_heroine",
                            "displayName": "林若曦",
                            "displayNameTranslations": {
                                "ja-JP": "林ルオシー",
                                "en-US": "Lin Ruoxi",
                            },
                        }
                    ]
                }
            ),
        )
        scene = chapter_result["scene"]
        scene["nameTranslations"] = {"ja-JP": "教室", "en-US": "Classroom"}
        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            scene,
            [
                {
                    "id": "block_dialogue",
                    "type": "dialogue",
                    "speakerId": "char_heroine",
                    "text": "今天的风，好像有点甜。",
                    "textTranslations": {
                        "ja-JP": "今日の風、少し甘い気がする。",
                        "en-US": "The wind feels a little sweet today.",
                    },
                },
                {
                    "id": "block_choice",
                    "type": "choice",
                    "options": [
                        {
                            "id": "opt_home",
                            "text": "一起回家吧",
                            "textTranslations": {
                                "ja-JP": "一緒に帰ろう",
                                "en-US": "Let's go home together",
                            },
                            "gotoSceneId": scene["id"],
                        }
                    ],
                },
            ],
        )

        export_result = run_editor.export_web_build()
        manifest = json.loads(Path(export_result["manifestPath"]).read_text(encoding="utf-8"))
        self.assertEqual(manifest["project"]["language"], "ja-JP")
        self.assertEqual(manifest["project"]["supportedLanguages"], ["zh-CN", "ja-JP", "en-US"])

        index_html = Path(export_result["indexPath"]).read_text(encoding="utf-8")
        self.assertIn('"defaultLanguage": "ja-JP"', index_html)
        self.assertIn('"supportedLanguages": [', index_html)
        self.assertIn('"今日の風、少し甘い気がする。"', index_html)
        self.assertIn('"Let\\u0027s go home together"', index_html.replace("'", "\\u0027"))
        self.assertIn("languageSelect", Path(export_result["buildPath"], "index.html").read_text(encoding="utf-8"))
        player_js = Path(export_result["buildPath"], "player.js").read_text(encoding="utf-8")
        self.assertIn("function handleLanguageChange", player_js)
        self.assertIn("getLocalizedValue", player_js)

    def test_linux_nwjs_build_smoke(self) -> None:
        _, chapter_result = self.create_blank_project_with_chapter()

        self.save_scene_with_blocks(
            chapter_result["chapterId"],
            chapter_result["scene"],
            [
                {
                    "id": "block_001",
                    "type": "dialogue",
                    "speakerId": "heroine",
                    "expressionId": "",
                    "text": "这是 Linux 桌面导出烟测。",
                }
            ],
        )

        export_result = run_editor.export_linux_nwjs_build()

        build_dir = Path(export_result["buildPath"])
        manifest_path = Path(export_result["manifestPath"])
        self.assertEqual(export_result["target"], run_editor.EXPORT_TARGET_LINUX_NWJS)
        self.assertTrue(Path(export_result["launcherPath"]).is_file())
        self.assertTrue(Path(export_result["startHelperPath"]).is_file())
        self.assertTrue(Path(export_result["archivePath"]).is_file())
        self.assertTrue((build_dir / "package.nw").is_file())
        self.assertTrue(manifest_path.is_file())

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["engine"]["exportTarget"], run_editor.EXPORT_TARGET_LINUX_NWJS)
        self.assert_export_manifest_has_subtle_engine_signature(manifest)
        provenance = self.assert_export_provenance_file(
            export_result,
            {"export_manifest.json", "app/index.html", "app/player.js", "app/player.css", "package.nw"},
        )
        self.assertEqual(provenance["build"]["target"], run_editor.EXPORT_TARGET_LINUX_NWJS)
        self.assertEqual(manifest["runtime"]["version"], run_editor.NWJS_RUNTIME_VERSION)

    def test_editor_desktop_build_smoke(self) -> None:
        export_result = run_editor.export_editor_desktop_build()

        build_dir = Path(export_result["buildPath"])
        bundle_dir = Path(export_result["bundleDirPath"])
        manifest_path = Path(export_result["manifestPath"])
        self.assertEqual(export_result["target"], run_editor.EXPORT_TARGET_EDITOR_DESKTOP)
        self.assertTrue(bundle_dir.is_dir())
        self.assertTrue((bundle_dir / "run_editor.py").is_file())
        self.assertTrue((bundle_dir / "prototype_editor" / "index.html").is_file())
        self.assertTrue((bundle_dir / "export_player_template" / "player.js").is_file())
        self.assertTrue((bundle_dir / "template_project" / "project.json").is_file())
        self.assertTrue((bundle_dir / "projects").is_dir())
        self.assertTrue((bundle_dir / "exports").is_dir())
        self.assertTrue((build_dir / run_editor.EDITOR_START_COMMAND_NAME).is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_START_WINDOWS_NAME).is_file())
        self.assertTrue((build_dir / "launch_splash.svg").is_file())
        self.assertTrue((build_dir / "app_icon.png").is_file())
        self.assertTrue((build_dir / "app_icon.ico").is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_DISTRIBUTION_SNAPSHOT_NAME).is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_COMMERCIAL_README_NAME).is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_SIGNING_GUIDE_NAME).is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_SIGNING_ENV_EXAMPLE_NAME).is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_SIGNING_CHECK_SCRIPT_NAME).is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_SIGNING_CHECK_COMMAND_NAME).is_file())
        self.assertTrue(Path(export_result["archivePath"]).is_file())
        self.assertTrue(manifest_path.is_file())
        self.assertTrue(Path(export_result["signingGuidePath"]).is_file())
        self.assertTrue(Path(export_result["signingEnvExamplePath"]).is_file())
        self.assertTrue(Path(export_result["signingCheckScriptPath"]).is_file())
        self.assertTrue(Path(export_result["signingCheckCommandPath"]).is_file())

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["engine"]["packageTarget"], run_editor.EXPORT_TARGET_EDITOR_DESKTOP)
        self.assertEqual(manifest["engine"]["releaseVersion"], run_editor.EDITOR_PACKAGE_VERSION)
        self.assertEqual(manifest["editorPackage"]["bundleDirName"], run_editor.EDITOR_BUNDLE_DIR_NAME)
        self.assertIn("embeddedRuntime", manifest["editorPackage"])
        self.assertIn("commercialRelease", manifest["editorPackage"])
        self.assertIn(export_result["embeddedRuntimeMode"], {run_editor.EDITOR_RUNTIME_SOURCE_CONDA_PACK, run_editor.EDITOR_RUNTIME_SOURCE_SYSTEM})
        if export_result["embeddedRuntimeIncluded"]:
            self.assertTrue((bundle_dir / run_editor.EDITOR_RUNTIME_DIR_NAME / "bin" / "python3").is_file())

        if run_editor.should_build_editor_macos_app():
            self.assertTrue((build_dir / run_editor.EDITOR_MAC_APP_NAME).is_dir())
            self.assertTrue((build_dir / run_editor.EDITOR_MAC_APP_NAME / "Contents" / "Resources" / run_editor.EDITOR_BUNDLE_DIR_NAME / "run_editor.py").is_file())
            self.assertTrue((build_dir / run_editor.EDITOR_MAC_INSTALLER_NAME).is_file())

    def test_editor_desktop_suite_build_smoke(self) -> None:
        export_result = run_editor.export_editor_desktop_suite_build()
        build_dir = Path(export_result["buildPath"])
        manifest_path = Path(export_result["manifestPath"])

        self.assertEqual(export_result["target"], run_editor.EXPORT_TARGET_EDITOR_DESKTOP_SUITE)
        self.assertTrue(manifest_path.is_file())
        self.assertTrue((build_dir / "README_三系统编辑器套装先看这里.txt").is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_DISTRIBUTION_SNAPSHOT_NAME).is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_SIGNING_GUIDE_NAME).is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_SIGNING_ENV_EXAMPLE_NAME).is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_SIGNING_CHECK_SCRIPT_NAME).is_file())
        self.assertTrue((build_dir / run_editor.EDITOR_SIGNING_CHECK_COMMAND_NAME).is_file())
        self.assertEqual(len(export_result["packages"]), 3)
        self.assertTrue(Path(export_result["signingGuidePath"]).is_file())
        self.assertTrue(Path(export_result["signingEnvExamplePath"]).is_file())
        self.assertTrue(Path(export_result["signingCheckScriptPath"]).is_file())
        self.assertTrue(Path(export_result["signingCheckCommandPath"]).is_file())

        platform_map = {package["platform"]: package for package in export_result["packages"]}
        self.assertIn(run_editor.EDITOR_PLATFORM_MACOS, platform_map)
        self.assertIn(run_editor.EDITOR_PLATFORM_WINDOWS, platform_map)
        self.assertIn(run_editor.EDITOR_PLATFORM_LINUX, platform_map)

        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_MACOS]["archivePath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["archivePath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_LINUX]["archivePath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["runtimeInfo"]["runtimeDirPath"]).is_dir())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_LINUX]["runtimeInfo"]["runtimeDirPath"]).is_dir())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_MACOS]["runtimeInfo"]["runtimeDirPath"]).is_dir())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["commercialReadmePath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["signingGuidePath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["signingEnvExamplePath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["signingCheckScriptPath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["signingCheckCommandPath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["windowsInstallerScriptPath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["windowsInstallerExePath"]).is_file())
        self.assertEqual(
            platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["windowsInstallerCompileStatusLabel"],
            "已编译 Windows 安装器",
        )
        self.assertEqual(
            platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["windowsSigningStatusLabel"],
            "已签名并加时间戳",
        )
        self.assertTrue(platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["windowsInstallerSigned"])
        self.assertEqual(
            platform_map[run_editor.EDITOR_PLATFORM_WINDOWS]["signingInfo"]["statusLabel"],
            "已签名并加时间戳",
        )
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_LINUX]["commercialReadmePath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_LINUX]["signingGuidePath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_LINUX]["signingEnvExamplePath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_LINUX]["signingCheckScriptPath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_LINUX]["signingCheckCommandPath"]).is_file())
        self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_LINUX]["linuxInstallScriptPath"]).is_file())

        if run_editor.should_build_editor_macos_app():
            self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_MACOS]["appPath"]).is_dir())
            self.assertTrue(Path(platform_map[run_editor.EDITOR_PLATFORM_MACOS]["installerPath"]).is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
