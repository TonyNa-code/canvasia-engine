from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import os
import platform
import plistlib
import re
import socket
import struct
import subprocess
import shutil
import sys
import tarfile
import tempfile
import webbrowser
import zipfile
import zlib
from datetime import datetime
from difflib import SequenceMatcher
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from editor_local_security import is_local_editor_host, is_local_editor_origin
from editor_snapshot_cache import SnapshotCache, build_file_cache_signature
from editor_static_cache import (
    build_editor_static_cache_headers,
    is_editor_static_cache_candidate,
    request_etag_matches,
)
from export_choice_consequence_sheet import (
    EXPORT_CHOICE_CONSEQUENCE_CSV_NAME,
    EXPORT_CHOICE_CONSEQUENCE_JSON_NAME,
    EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME,
)
from export_variable_influence_sheet import (
    EXPORT_VARIABLE_INFLUENCE_CSV_NAME,
    EXPORT_VARIABLE_INFLUENCE_JSON_NAME,
    EXPORT_VARIABLE_INFLUENCE_REPORT_NAME,
)
from export_package_guide import EXPORT_PLAYTEST_GUIDE_FILE_NAME, write_export_playtest_guide_file
from export_route_playtest_workbook import (
    EXPORT_ROUTE_PLAYTEST_WORKBOOK_CSV_NAME,
    EXPORT_ROUTE_PLAYTEST_WORKBOOK_JSON_NAME,
    EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME,
)
from export_asset_rights import (
    EXPORT_ASSET_RIGHTS_CSV_NAME,
    EXPORT_ASSET_RIGHTS_JSON_NAME,
    EXPORT_ASSET_RIGHTS_REPORT_NAME,
    write_export_asset_rights_files,
)
from export_audio_cue_sheet import (
    EXPORT_AUDIO_CUE_SHEET_CSV_NAME,
    EXPORT_AUDIO_CUE_SHEET_JSON_NAME,
    EXPORT_AUDIO_CUE_SHEET_REPORT_NAME,
    write_export_audio_cue_sheet_files,
)
from export_stage_direction_sheet import (
    EXPORT_STAGE_DIRECTION_CSV_NAME,
    EXPORT_STAGE_DIRECTION_JSON_NAME,
    EXPORT_STAGE_DIRECTION_REPORT_NAME,
    write_export_stage_direction_files,
)
from export_presentation_timeline import (
    EXPORT_PRESENTATION_TIMELINE_CSV_NAME,
    EXPORT_PRESENTATION_TIMELINE_JSON_NAME,
    EXPORT_PRESENTATION_TIMELINE_REPORT_NAME,
    write_export_presentation_timeline_files,
)
from export_voice_production import (
    EXPORT_VOICE_PRODUCTION_CSV_NAME,
    EXPORT_VOICE_PRODUCTION_JSON_NAME,
    EXPORT_VOICE_PRODUCTION_REPORT_NAME,
    write_export_voice_production_files,
)
from export_localization_audit import (
    EXPORT_LOCALIZATION_AUDIT_JSON_NAME,
    EXPORT_LOCALIZATION_AUDIT_REPORT_NAME,
)
from export_quality_reports import write_export_quality_report_bundle
from export_release_evidence_pack import (
    EXPORT_RELEASE_EVIDENCE_PACK_NAME,
    write_export_release_evidence_pack_file,
)
from export_release_readiness import (
    EXPORT_RELEASE_READINESS_JSON_NAME,
    EXPORT_RELEASE_READINESS_REPORT_NAME,
)
from export_release_control import (
    build_native_runtime_release_control_markdown as build_release_control_markdown_payload,
    build_native_runtime_release_control_next_steps as build_release_control_next_steps,
    build_native_runtime_release_control_payload as build_release_control_payload,
    get_native_runtime_release_control_status as get_release_control_status,
)
from export_runtime_preload import (
    RUNTIME_PRELOAD_MANIFEST_FILE_NAME,
    RUNTIME_PRELOAD_REPORT_FILE_NAME,
    build_runtime_preload_manifest,
    write_runtime_preload_files,
)
from native_runtime.runtime_performance import (
    PERFORMANCE_BUDGET_MARKDOWN_NAME as NATIVE_RUNTIME_PERFORMANCE_BUDGET_MARKDOWN_NAME,
    PERFORMANCE_BUDGET_REPORT_NAME as NATIVE_RUNTIME_PERFORMANCE_BUDGET_REPORT_NAME,
)
from export_story_route_map import (
    EXPORT_STORY_ROUTE_MAP_JSON_NAME,
    EXPORT_STORY_ROUTE_MAP_REPORT_NAME,
)
from export_unlockable_manifest import (
    UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME,
    UNLOCKABLE_CONTENT_REPORT_FILE_NAME,
    build_export_unlockable_content_manifest,
    write_unlockable_content_manifest_file,
    write_unlockable_content_report_file,
)
from renpy_export import (
    RENPY_MANIFEST_FILE_NAME,
    RENPY_OPTIONS_FILE_NAME,
    RENPY_QUALITY_MARKDOWN_FILE_NAME,
    RENPY_QUALITY_REPORT_FILE_NAME,
    RENPY_README_FILE_NAME,
    RENPY_REVIEW_FILE_NAME,
    RENPY_SCRIPT_FILE_NAME,
    RENPY_SCREENS_FILE_NAME,
    RENPY_VERIFY_SCRIPT_FILE_NAME,
    write_renpy_starter_project,
)
from openai_asset_generation import (
    call_openai_asset_generation_model,
    normalize_openai_asset_generation_type,
)
from project_runtime_settings import (
    build_default_project_runtime_settings,
    sanitize_project_runtime_settings,
)


ROOT_DIR = Path(__file__).resolve().parent
PROJECTS_DIR = ROOT_DIR / "projects"
SAMPLE_PROJECT_DIR = ROOT_DIR / "template_project"
SAMPLE_PROJECT_ID = "sample_heartbeat"
DEFAULT_PORT = 8765
EXPORTS_DIR = ROOT_DIR / "exports"
EXPORT_TEMPLATE_DIR = ROOT_DIR / "export_player_template"
EXPORT_PLAYER_SCRIPT_FILES = (
    "runtime_conditions.js",
    "player.js",
    "runtime_controls.js",
    "runtime_settings.js",
    "runtime_audio.js",
    "runtime_preload.js",
)
NATIVE_RUNTIME_TEMPLATE_DIR = ROOT_DIR / "native_runtime"
EXPORT_RUNTIME_CACHE_DIR = ROOT_DIR / ".export_runtime_cache"
SUPPORTED_RESOLUTIONS = {(1280, 720), (1920, 1080)}
VARIABLE_ID_PATTERN = re.compile(r"^[0-9A-Za-z_\-\u4e00-\u9fff]{1,64}$")
HISTORY_DIR_NAME = ".canvasia_history"
HISTORY_SNAPSHOTS_DIR_NAME = "snapshots"
HISTORY_MANIFEST_FILE_NAME = "history_manifest.json"
HISTORY_FORMAT_VERSION = 1
MAX_HISTORY_SNAPSHOTS = 40
SESSION_STATE_FILE_NAME = "session_state.json"
SESSION_FORMAT_VERSION = 1
EXPORT_MANIFEST_FORMAT_VERSION = 1
EXPORT_ENGINE_SIGNATURE = {
    "id": "tne",
    "by": "Tony-Na",
}
EXPORT_PROVENANCE_FORMAT_VERSION = 1
EXPORT_PROVENANCE_FILE_NAME = "tony-na-provenance.json"
EXPORT_PROVENANCE_VERIFIER_SCRIPT_NAME = "verify_tony_na_provenance.py"
EXPORT_PROVENANCE_MAC_VERIFIER_NAME = "verify_tony_na_provenance.command"
EXPORT_PROVENANCE_LINUX_VERIFIER_NAME = "verify_tony_na_provenance.sh"
EXPORT_PROVENANCE_WINDOWS_VERIFIER_NAME = "verify_tony_na_provenance.bat"
EXPORT_PROTECTION_PROFILE = "light-origin-integrity"
PROJECT_FORMAT_VERSION = 3
DEFAULT_EXPORT_RELEASE_VERSION = "1.0.0-preview"
DEFAULT_PROJECT_LANGUAGE = "zh-CN"
SUPPORTED_PROJECT_LANGUAGES = {
    "zh-CN": "简体中文",
    "ja-JP": "日本語",
    "en-US": "English",
}
DEFAULT_EDITOR_MODE = "beginner"
DEFAULT_DIALOG_BOX_CONFIG = {
    "preset": "moonlight",
    "shape": "rounded",
    "widthPercent": 76,
    "minHeight": 148,
    "paddingX": 18,
    "paddingY": 14,
    "backgroundColor": "#0c1422",
    "backgroundOpacity": 92,
    "borderColor": "#79dcff",
    "borderOpacity": 18,
    "textColor": "#f3f6ff",
    "speakerColor": "#ffffff",
    "hintColor": "#c8d6ea",
    "blurStrength": 10,
    "borderWidth": 1,
    "shadowStrength": 30,
    "panelAssetId": "",
    "panelAssetOpacity": 0,
    "panelAssetFit": "cover",
    "anchor": "bottom",
    "offsetXPercent": 0,
    "offsetYPercent": 0,
}
DEFAULT_GAME_UI_CONFIG = {
    "preset": "stellar",
    "layoutPreset": "balanced",
    "titleLayout": "center",
    "fontStyle": "modern",
    "fontFamily": "",
    "fontAssetId": "",
    "surfaceStyle": "glass",
    "brandMode": "project",
    "sidePanelMode": "full",
    "sidePanelPosition": "right",
    "topbarPosition": "top",
    "hudPosition": "top",
    "titleCardAnchor": "center",
    "titleCardOffsetXPercent": 0,
    "titleCardOffsetYPercent": 0,
    "layoutGap": 20,
    "sidePanelWidth": 320,
    "backgroundColor": "#071120",
    "backgroundAccentColor": "#6bd5ff",
    "panelColor": "#0c1422",
    "panelOpacity": 88,
    "textColor": "#f3f7ff",
    "mutedTextColor": "#bacce4",
    "accentColor": "#79dcff",
    "accentAltColor": "#7b7cff",
    "buttonTextColor": "#f8fcff",
    "borderColor": "#79dcff",
    "borderOpacity": 18,
    "cornerRadius": 22,
    "backdropBlur": 14,
    "stageVignette": 42,
    "motionIntensity": 70,
    "titleBackgroundAssetId": "",
    "titleBackgroundFit": "cover",
    "titleBackgroundOpacity": 42,
    "titleLogoAssetId": "",
    "panelFrameAssetId": "",
    "panelFrameOpacity": 18,
    "panelFrameSlice": {"top": 24, "right": 24, "bottom": 24, "left": 24},
    "buttonFrameAssetId": "",
    "buttonHoverFrameAssetId": "",
    "buttonPressedFrameAssetId": "",
    "buttonDisabledFrameAssetId": "",
    "buttonFrameOpacity": 24,
    "buttonFrameSlice": {"top": 18, "right": 18, "bottom": 18, "left": 18},
    "saveSlotFrameAssetId": "",
    "systemPanelFrameAssetId": "",
    "uiOverlayAssetId": "",
    "uiOverlayOpacity": 8,
}
ASSET_DIRECTORIES = {
    "background": Path("assets/backgrounds"),
    "sprite": Path("assets/sprites"),
    "cg": Path("assets/cg"),
    "bgm": Path("assets/bgm"),
    "sfx": Path("assets/sfx"),
    "voice": Path("assets/voice"),
    "video": Path("assets/video"),
    "ui": Path("assets/ui"),
    "font": Path("assets/fonts"),
    "live2d": Path("assets/live2d"),
    "model3d": Path("assets/models"),
    "scene3d": Path("assets/scenes3d"),
}
ASSET_ID_PREFIXES = {
    "background": "bg",
    "sprite": "sprite",
    "cg": "cg",
    "bgm": "bgm",
    "sfx": "sfx",
    "voice": "voice",
    "video": "video",
    "ui": "ui",
    "font": "font",
    "live2d": "live2d",
    "model3d": "model3d",
    "scene3d": "scene3d",
}
ASSET_TYPE_LABELS = {
    "background": "背景",
    "sprite": "立绘",
    "cg": "CG",
    "bgm": "音乐",
    "sfx": "音效",
    "voice": "语音",
    "video": "视频",
    "ui": "界面素材",
    "font": "字体",
    "live2d": "Live2D",
    "model3d": "3D 模型",
    "scene3d": "3D 场景",
}
ASSET_RIGHTS_TEXT_LIMITS = {
    "license": 160,
    "sourceUrl": 500,
    "author": 160,
    "credit": 220,
    "aiProvider": 120,
    "prompt": 2000,
}
ASSET_RIGHTS_BOOLEAN_FIELDS = {"generatedByAi", "attributionRequired"}
ASSET_COMMERCIAL_USE_LABELS = {
    "unknown": "未确认",
    "allowed": "可商用",
    "forbidden": "不可商用",
}
BLOCK_LABELS = {
    "background": "切换背景",
    "dialogue": "台词",
    "narration": "旁白",
    "character_show": "显示角色",
    "character_hide": "隐藏角色",
    "music_play": "播放音乐",
    "music_stop": "停止音乐",
    "sfx_play": "播放音效",
    "video_play": "播放视频",
    "credits_roll": "片尾字幕",
    "particle_effect": "粒子特效",
    "screen_shake": "屏幕震动",
    "screen_flash": "闪屏",
    "screen_fade": "黑场淡入淡出",
    "camera_zoom": "镜头推近拉远",
    "camera_pan": "镜头平移",
    "screen_filter": "回忆滤镜",
    "depth_blur": "景深模糊",
    "jump": "跳转",
    "variable_set": "设置变量",
    "variable_add": "修改变量",
    "choice": "选项",
    "condition": "条件判断",
}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif"}
AUDIO_EXTENSIONS = {".mp3", ".ogg", ".wav", ".m4a", ".aac", ".flac"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".m4v"}
FONT_EXTENSIONS = {".ttf", ".otf", ".ttc"}
MODEL3D_EXTENSIONS = {".glb", ".gltf", ".vrm", ".fbx", ".obj"}
LIVE2D_EXTENSION_SUFFIXES = (
    ".model3.json",
    ".moc3",
    ".motion3.json",
    ".physics3.json",
    ".cdi3.json",
    ".pose3.json",
    ".exp3.json",
    ".userdata3.json",
)
ASSET_REPLACE_EXTENSION_GROUPS = {
    "background": IMAGE_EXTENSIONS,
    "sprite": IMAGE_EXTENSIONS,
    "cg": IMAGE_EXTENSIONS,
    "ui": IMAGE_EXTENSIONS,
    "bgm": AUDIO_EXTENSIONS,
    "sfx": AUDIO_EXTENSIONS,
    "voice": AUDIO_EXTENSIONS,
    "video": VIDEO_EXTENSIONS,
    "font": FONT_EXTENSIONS,
    "model3d": MODEL3D_EXTENSIONS,
    "scene3d": MODEL3D_EXTENSIONS,
}
ASSET_REPLACE_EXTENSION_HINTS = {
    "background": "png、jpg、webp、gif 或 avif",
    "sprite": "png、jpg、webp、gif 或 avif",
    "cg": "png、jpg、webp、gif 或 avif",
    "ui": "png、jpg、webp、gif 或 avif",
    "bgm": "mp3、ogg、wav、m4a、aac 或 flac",
    "sfx": "mp3、ogg、wav、m4a、aac 或 flac",
    "voice": "mp3、ogg、wav、m4a、aac 或 flac",
    "video": "mp4、webm、mov 或 m4v",
    "font": "ttf、otf 或 ttc",
    "live2d": "model3.json、moc3、motion3.json、physics3.json、pose3.json、exp3.json 等 Live2D 文件",
    "model3d": "glb、gltf、vrm、fbx 或 obj",
    "scene3d": "glb、gltf、vrm、fbx 或 obj",
}
EXPORT_TARGET_WEB = "web"
EXPORT_TARGET_NATIVE_RUNTIME = "native_runtime"
EXPORT_TARGET_WINDOWS_NWJS = "windows_nwjs"
EXPORT_TARGET_MACOS_NWJS = "macos_nwjs"
EXPORT_TARGET_LINUX_NWJS = "linux_nwjs"
EXPORT_TARGET_EDITOR_DESKTOP = "editor_desktop"
EXPORT_TARGET_EDITOR_DESKTOP_SUITE = "editor_desktop_suite"
EXPORT_TARGET_RENPY_DRAFT = "renpy_draft"
NWJS_RUNTIME_VERSION = "v0.105.0"
NWJS_GAME_PLATFORM_WINDOWS = "windows"
NWJS_GAME_PLATFORM_MACOS = "macos"
NWJS_GAME_PLATFORM_LINUX = "linux"
NWJS_GAME_RUNTIME_PLATFORM_CONFIG = {
    NWJS_GAME_PLATFORM_WINDOWS: {
        "label": "Windows",
        "target": EXPORT_TARGET_WINDOWS_NWJS,
        "archiveFormat": "zip",
        "archiveName": f"nwjs-{NWJS_RUNTIME_VERSION}-win-x64.zip",
        "runtimeCacheSuffix": "win_x64",
        "runtimeExecutable": "nw.exe",
        "localRuntimeDirs": ["windows"],
        "requiredFiles": [
            "nw.exe",
            "icudtl.dat",
            "libEGL.dll",
            "libGLESv2.dll",
            "nw_100_percent.pak",
            "resources.pak",
            "v8_context_snapshot.bin",
        ],
        "requiredDirs": ["locales"],
    },
    NWJS_GAME_PLATFORM_MACOS: {
        "label": "macOS",
        "target": EXPORT_TARGET_MACOS_NWJS,
        "archiveFormat": "zip",
        "runtimeCacheSuffix": "osx",
        "localRuntimeDirs": ["macos"],
        "appBundleName": "nwjs.app",
        "requiredFiles": [
            "Contents/Info.plist",
            "Contents/MacOS/nwjs",
        ],
        "requiredDirs": ["Contents/Resources"],
    },
    NWJS_GAME_PLATFORM_LINUX: {
        "label": "Linux",
        "target": EXPORT_TARGET_LINUX_NWJS,
        "archiveFormat": "gztar",
        "archiveName": f"nwjs-{NWJS_RUNTIME_VERSION}-linux-x64.tar.gz",
        "runtimeCacheSuffix": "linux_x64",
        "runtimeExecutable": "nw",
        "localRuntimeDirs": ["linux"],
        "requiredFiles": [
            "nw",
            "icudtl.dat",
            "resources.pak",
            "v8_context_snapshot.bin",
        ],
        "requiredDirs": ["locales"],
    },
}
LOCAL_NWJS_RUNTIME_DIRS = [
    ROOT_DIR / "desktop_runtime",
    ROOT_DIR / "desktop_runtime" / "windows",
]
LOCAL_NWJS_RUNTIME_GUIDE_NAME = "README_把_NWJS_运行壳放这里.txt"
EDITOR_PACKAGE_VERSION = "1.0.0-preview"
EDITOR_BUNDLE_DIR_NAME = "editor_bundle"
EDITOR_MAC_APP_NAME = "Canvasia Engine Editor.app"
EDITOR_MAC_APP_EXECUTABLE = "CanvasiaEngineEditor"
EDITOR_MAC_INSTALLER_NAME = "Canvasia Engine Editor Installer.pkg"
EDITOR_EDITOR_README_NAME = "README_编辑器包先看这里.txt"
EDITOR_COMMERCIAL_README_NAME = "README_编辑器发布维护先看这里.txt"
EDITOR_SIGNING_GUIDE_NAME = "README_编辑器签名与公证维护说明.md"
EDITOR_SIGNING_ENV_EXAMPLE_NAME = "editor_signing.env.example"
EDITOR_SIGNING_CHECK_SCRIPT_NAME = "check_editor_signing_readiness.py"
EDITOR_SIGNING_CHECK_COMMAND_NAME = "run_signing_readiness.command"
EDITOR_SIGNING_GUIDE_SOURCE = ROOT_DIR / "docs" / "maintainers" / "release" / "editor_signing_guide.md"
EDITOR_SIGNING_ENV_EXAMPLE_SOURCE = ROOT_DIR / "docs" / "maintainers" / "release" / "editor_signing.env.example"
EDITOR_SIGNING_CHECK_SCRIPT_SOURCE = ROOT_DIR / "tools" / "release" / "check_editor_signing_readiness.py"
EDITOR_SIGNING_CHECK_COMMAND_SOURCE = ROOT_DIR / "tools" / "release" / "run_signing_readiness.command"
NATIVE_RUNTIME_PLAYER_SOURCE = NATIVE_RUNTIME_TEMPLATE_DIR / "runtime_player.py"
NATIVE_RUNTIME_PRELOAD_SOURCE = NATIVE_RUNTIME_TEMPLATE_DIR / "runtime_preload.py"
NATIVE_RUNTIME_PERFORMANCE_SOURCE = NATIVE_RUNTIME_TEMPLATE_DIR / "runtime_performance.py"
NATIVE_RUNTIME_SETTINGS_SOURCE = NATIVE_RUNTIME_TEMPLATE_DIR / "runtime_player_settings.py"
NATIVE_RUNTIME_TEXT_EFFECTS_SOURCE = NATIVE_RUNTIME_TEMPLATE_DIR / "runtime_text_effects.py"
NATIVE_RUNTIME_STORAGE_SOURCE = NATIVE_RUNTIME_TEMPLATE_DIR / "runtime_storage.py"
NATIVE_RUNTIME_VARIABLES_SOURCE = NATIVE_RUNTIME_TEMPLATE_DIR / "runtime_variables.py"
NATIVE_RUNTIME_README_SOURCE = NATIVE_RUNTIME_TEMPLATE_DIR / "README.md"
NATIVE_RUNTIME_REQUIREMENTS_SOURCE = NATIVE_RUNTIME_TEMPLATE_DIR / "requirements.txt"
NATIVE_RUNTIME_BUILD_REQUIREMENTS_SOURCE = NATIVE_RUNTIME_TEMPLATE_DIR / "requirements-build.txt"
NATIVE_RUNTIME_VIDEO_REQUIREMENTS_SOURCE = NATIVE_RUNTIME_TEMPLATE_DIR / "requirements-video.txt"
NATIVE_RUNTIME_BRAND_LOGO_SOURCE = ROOT_DIR / "prototype_editor" / "assets" / "canvasia-brand-logo.png"
NATIVE_RUNTIME_PLAYER_NAME = "runtime_player.py"
NATIVE_RUNTIME_PRELOAD_NAME = "runtime_preload.py"
NATIVE_RUNTIME_PERFORMANCE_NAME = "runtime_performance.py"
NATIVE_RUNTIME_SETTINGS_NAME = "runtime_player_settings.py"
NATIVE_RUNTIME_TEXT_EFFECTS_NAME = "runtime_text_effects.py"
NATIVE_RUNTIME_STORAGE_NAME = "runtime_storage.py"
NATIVE_RUNTIME_VARIABLES_NAME = "runtime_variables.py"
NATIVE_RUNTIME_README_NAME = "README_原生_Runtime_包先看这里.md"
NATIVE_RUNTIME_REQUIREMENTS_NAME = "requirements-native-runtime.txt"
NATIVE_RUNTIME_BUILD_REQUIREMENTS_NAME = "requirements-native-runtime-build.txt"
NATIVE_RUNTIME_VIDEO_REQUIREMENTS_NAME = "requirements-native-runtime-video.txt"
NATIVE_RUNTIME_BRAND_LOGO_NAME = "assets/canvasia-brand-logo.png"
NATIVE_RUNTIME_APP_BUILDER_SOURCE = NATIVE_RUNTIME_TEMPLATE_DIR / "build_native_runtime_app.py"
NATIVE_RUNTIME_APP_BUILDER_NAME = "build_native_runtime_app.py"
NATIVE_RUNTIME_RELEASE_CHECK_NAME = "native-runtime-release-check.json"
NATIVE_RUNTIME_RC_REPORT_NAME = "native-runtime-release-candidate-report.json"
NATIVE_RUNTIME_RELEASE_CONTROL_REPORT_NAME = "native-runtime-release-control-report.md"
NATIVE_RUNTIME_RELEASE_CONTROL_JSON_NAME = "native-runtime-release-control-report.json"
NATIVE_RUNTIME_ACCEPTANCE_REPORT_NAME = "native-runtime-release-acceptance.md"
NATIVE_RUNTIME_ACCEPTANCE_JSON_NAME = "native-runtime-release-acceptance.json"
NATIVE_RUNTIME_VN_BASELINE_QUALITY_REPORT_NAME = "native-runtime-vn-baseline-quality.json"
NATIVE_RUNTIME_VN_BASELINE_QUALITY_MARKDOWN_NAME = "native-runtime-vn-baseline-quality.md"
NATIVE_RUNTIME_FILE_INTEGRITY_REPORT_NAME = "native-runtime-file-integrity.json"
NATIVE_RUNTIME_FILE_INTEGRITY_MARKDOWN_NAME = "native-runtime-file-integrity.md"
NATIVE_RUNTIME_3D_ASSET_REPORT_NAME = "native-runtime-3d-asset-report.json"
NATIVE_RUNTIME_3D_ASSET_SUMMARY_NAME = "native-runtime-3d-asset-summary.md"
NATIVE_RUNTIME_3D_ASSET_DIGEST_NAME = "native-runtime-3d-risk-digest.json"
NATIVE_RUNTIME_MAC_COMMAND_NAME = "启动原生Runtime预览.command"
NATIVE_RUNTIME_LINUX_COMMAND_NAME = "run_native_runtime_preview.sh"
NATIVE_RUNTIME_WINDOWS_COMMAND_NAME = "run_native_runtime_preview.bat"
NATIVE_RUNTIME_MAC_RC_COMMAND_NAME = "检查原生Runtime发布候选.command"
NATIVE_RUNTIME_LINUX_RC_COMMAND_NAME = "check_native_runtime_release_candidate.sh"
NATIVE_RUNTIME_WINDOWS_RC_COMMAND_NAME = "check_native_runtime_release_candidate.bat"
NATIVE_RUNTIME_MAC_RELEASE_CONTROL_COMMAND_NAME = "生成原生Runtime发布总控报告.command"
NATIVE_RUNTIME_LINUX_RELEASE_CONTROL_COMMAND_NAME = "generate_native_runtime_release_control.sh"
NATIVE_RUNTIME_WINDOWS_RELEASE_CONTROL_COMMAND_NAME = "generate_native_runtime_release_control.bat"
NATIVE_RUNTIME_MAC_ACCEPTANCE_COMMAND_NAME = "生成原生Runtime发布验收清单.command"
NATIVE_RUNTIME_LINUX_ACCEPTANCE_COMMAND_NAME = "generate_native_runtime_acceptance_checklist.sh"
NATIVE_RUNTIME_WINDOWS_ACCEPTANCE_COMMAND_NAME = "generate_native_runtime_acceptance_checklist.bat"
NATIVE_RUNTIME_MAC_FILE_INTEGRITY_COMMAND_NAME = "校验原生Runtime文件完整性.command"
NATIVE_RUNTIME_LINUX_FILE_INTEGRITY_COMMAND_NAME = "verify_native_runtime_file_integrity.sh"
NATIVE_RUNTIME_WINDOWS_FILE_INTEGRITY_COMMAND_NAME = "verify_native_runtime_file_integrity.bat"
NATIVE_RUNTIME_MAC_APP_BUILDER_COMMAND_NAME = "打包原生Runtime应用.command"
NATIVE_RUNTIME_LINUX_APP_BUILDER_COMMAND_NAME = "build_native_runtime_app.sh"
NATIVE_RUNTIME_WINDOWS_APP_BUILDER_COMMAND_NAME = "build_native_runtime_app.bat"
NATIVE_RUNTIME_REQUIRED_MODULE_FILES = (
    (NATIVE_RUNTIME_PLAYER_SOURCE, NATIVE_RUNTIME_PLAYER_NAME),
    (NATIVE_RUNTIME_PRELOAD_SOURCE, NATIVE_RUNTIME_PRELOAD_NAME),
    (NATIVE_RUNTIME_PERFORMANCE_SOURCE, NATIVE_RUNTIME_PERFORMANCE_NAME),
    (NATIVE_RUNTIME_SETTINGS_SOURCE, NATIVE_RUNTIME_SETTINGS_NAME),
    (NATIVE_RUNTIME_TEXT_EFFECTS_SOURCE, NATIVE_RUNTIME_TEXT_EFFECTS_NAME),
    (NATIVE_RUNTIME_STORAGE_SOURCE, NATIVE_RUNTIME_STORAGE_NAME),
    (NATIVE_RUNTIME_VARIABLES_SOURCE, NATIVE_RUNTIME_VARIABLES_NAME),
)
EDITOR_DISTRIBUTION_CONFIG_NAME = "editor_distribution.json"
EDITOR_DISTRIBUTION_SNAPSHOT_NAME = "editor_distribution.snapshot.json"
EDITOR_WINDOWS_INSTALLER_SCRIPT_NAME = "Canvasia Engine Editor Installer.iss"
EDITOR_LINUX_INSTALL_SCRIPT_NAME = "install_editor.sh"
EDITOR_START_COMMAND_NAME = "启动 Canvasia Engine 编辑器.command"
EDITOR_START_WINDOWS_NAME = "启动 Canvasia Engine 编辑器.cmd"
EDITOR_RUNTIME_DIR_NAME = "runtime"
EDITOR_RUNTIME_CACHE_VERSION = 1
EDITOR_RUNTIME_SOURCE_CONDA_PACK = "conda_pack"
EDITOR_RUNTIME_SOURCE_SYSTEM = "system_python"
EDITOR_RUNTIME_SOURCE_PYTHON_BUILD_STANDALONE = "python_build_standalone"
EDITOR_PORTABLE_PYTHON_RELEASE = "20260414"
EDITOR_PORTABLE_PYTHON_VERSION = "3.13.13"
EDITOR_LINUX_START_NAME = "启动 Canvasia Engine 编辑器.sh"
EDITOR_PLATFORM_MACOS = "macos"
EDITOR_PLATFORM_WINDOWS = "windows"
EDITOR_PLATFORM_LINUX = "linux"
EDITOR_PORTABLE_RUNTIME_TARGETS = {
    EDITOR_PLATFORM_MACOS: {
        "label": "macOS",
        "triplet": "aarch64-apple-darwin",
        "archiveExt": "tar.gz",
        "archiveFormat": "gztar",
    },
    EDITOR_PLATFORM_WINDOWS: {
        "label": "Windows",
        "triplet": "x86_64-pc-windows-msvc",
        "archiveExt": "tar.gz",
        "archiveFormat": "zip",
    },
    EDITOR_PLATFORM_LINUX: {
        "label": "Linux",
        "triplet": "x86_64_v2-unknown-linux-gnu",
        "archiveExt": "tar.gz",
        "archiveFormat": "gztar",
    },
}
EDITOR_EXPORT_FILES = [
    "run_editor.py",
    "editor_local_security.py",
    "editor_snapshot_cache.py",
    "editor_static_cache.py",
    "export_route_playtest_workbook.py",
    "export_choice_consequence_sheet.py",
    "export_variable_influence_sheet.py",
    "export_asset_rights.py",
    "export_audio_cue_sheet.py",
    "export_stage_direction_sheet.py",
    "export_presentation_timeline.py",
    "export_voice_production.py",
    "export_localization_audit.py",
    "export_package_guide.py",
    "export_quality_reports.py",
    "export_release_control.py",
    "export_release_evidence_pack.py",
    "export_release_readiness.py",
    "export_runtime_preload.py",
    "export_story_route_map.py",
    "export_unlockable_manifest.py",
    "openai_asset_generation.py",
    "project_runtime_settings.py",
    "renpy_export.py",
    EDITOR_SIGNING_GUIDE_NAME,
    EDITOR_SIGNING_ENV_EXAMPLE_NAME,
    EDITOR_SIGNING_CHECK_SCRIPT_NAME,
    EDITOR_SIGNING_CHECK_COMMAND_NAME,
]
EDITOR_EXPORT_DIRECTORIES = [
    "prototype_editor",
    "export_player_template",
    "template_project",
    "desktop_runtime",
    "native_runtime",
]
EDITOR_EXPORT_EMPTY_DIRECTORIES = [
    "projects",
    "exports",
]

EDITOR_MAC_APP_IDENTITY_ENV = "CANVASIA_EDITOR_MAC_APP_IDENTITY"
EDITOR_MAC_INSTALLER_IDENTITY_ENV = "CANVASIA_EDITOR_MAC_INSTALLER_IDENTITY"
EDITOR_MAC_NOTARY_PROFILE_ENV = "CANVASIA_EDITOR_MAC_NOTARY_PROFILE"
EDITOR_WINDOWS_ISCC_ENV = "CANVASIA_EDITOR_WINDOWS_ISCC"
EDITOR_WINDOWS_ISCC_RUNNER_ENV = "CANVASIA_EDITOR_WINDOWS_ISCC_RUNNER"
EDITOR_WINDOWS_SIGNTOOL_ENV = "CANVASIA_EDITOR_WINDOWS_SIGNTOOL"
EDITOR_WINDOWS_SIGNTOOL_RUNNER_ENV = "CANVASIA_EDITOR_WINDOWS_SIGNTOOL_RUNNER"
EDITOR_WINDOWS_CERT_SUBJECT_ENV = "CANVASIA_EDITOR_WINDOWS_CERT_SUBJECT"
EDITOR_WINDOWS_CERT_THUMBPRINT_ENV = "CANVASIA_EDITOR_WINDOWS_CERT_THUMBPRINT"
EDITOR_WINDOWS_PFX_PATH_ENV = "CANVASIA_EDITOR_WINDOWS_PFX_PATH"
EDITOR_WINDOWS_PFX_PASSWORD_ENV = "CANVASIA_EDITOR_WINDOWS_PFX_PASSWORD"
EDITOR_WINDOWS_TIMESTAMP_URL_ENV = "CANVASIA_EDITOR_WINDOWS_TIMESTAMP_URL"

TEMPLATE_DIR = SAMPLE_PROJECT_DIR


def build_default_editor_distribution_config() -> dict:
    return {
        "productName": "Canvasia Engine Editor",
        "bundleIdentifier": "com.canvasia.engine.editor",
        "publisherName": "Canvasia Engine Project",
        "companyName": "Canvasia Engine Project",
        "website": "https://github.com/TonyNa-code/canvasia-engine",
        "supportUrl": "https://github.com/TonyNa-code/canvasia-engine/issues",
        "supportEmail": "",
        "copyright": "Copyright (c) 2026 Canvasia Engine Contributors",
        "macOS": {
            "minimumSystemVersion": "12.0",
            "category": "public.app-category.developer-tools",
        },
        "windows": {
            "appId": "com.canvasia.engine.editor",
            "publisher": "Canvasia Engine Project",
            "installerCompilerPath": "",
            "installerCompilerRunner": "",
        },
        "linux": {
            "desktopFileName": "Canvasia Engine Editor.desktop",
            "maintainer": "Canvasia Maintainers",
            "categories": ["Development"],
        },
        "signing": {
            "macAppIdentity": "",
            "macInstallerIdentity": "",
            "macNotaryProfile": "",
            "windowsSignToolPath": "",
            "windowsSignToolRunner": "",
            "windowsCertificateSubject": "",
            "windowsCertificateThumbprint": "",
            "windowsPfxPath": "",
            "windowsPfxPassword": "",
            "windowsTimestampUrl": "http://timestamp.digicert.com",
        },
    }


def merge_nested_dict(base: dict, overrides: dict) -> dict:
    merged = json.loads(json.dumps(base, ensure_ascii=False))
    for key, value in (overrides or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_nested_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


def sanitize_bundle_identifier(value: str, fallback: str) -> str:
    parts = [segment for segment in re.sub(r"[^A-Za-z0-9.]+", ".", value or "").strip(".").split(".") if segment]
    cleaned_parts = []
    for segment in parts:
        safe_segment = re.sub(r"[^A-Za-z0-9-]", "", segment)
        if not safe_segment:
            continue
        if safe_segment[0].isdigit():
            safe_segment = f"app{safe_segment}"
        cleaned_parts.append(safe_segment)
    return ".".join(cleaned_parts) or fallback


def normalize_editor_distribution_config(raw_config: dict | None = None) -> dict:
    merged = merge_nested_dict(build_default_editor_distribution_config(), raw_config or {})
    merged["productName"] = str(merged.get("productName") or "Canvasia Engine Editor").strip() or "Canvasia Engine Editor"
    merged["bundleIdentifier"] = sanitize_bundle_identifier(
        str(merged.get("bundleIdentifier") or ""),
        "com.canvasia.engine.editor",
    )
    merged["publisherName"] = str(merged.get("publisherName") or "Canvasia Engine Project").strip() or "Canvasia Engine Project"
    merged["companyName"] = str(merged.get("companyName") or merged["publisherName"]).strip() or merged["publisherName"]
    merged["website"] = str(merged.get("website") or "").strip()
    default_support_url = "https://github.com/TonyNa-code/canvasia-engine/issues"
    merged["supportUrl"] = str(merged.get("supportUrl") or merged["website"] or default_support_url).strip()
    merged["supportEmail"] = str(merged.get("supportEmail") or "").strip()
    merged["copyright"] = (
        str(merged.get("copyright") or "").strip() or "Copyright (c) 2026 Canvasia Engine Contributors"
    )
    merged["macOS"]["minimumSystemVersion"] = (
        str(merged["macOS"].get("minimumSystemVersion") or "12.0").strip() or "12.0"
    )
    merged["macOS"]["category"] = (
        str(merged["macOS"].get("category") or "public.app-category.developer-tools").strip()
        or "public.app-category.developer-tools"
    )
    merged["windows"]["appId"] = sanitize_bundle_identifier(
        str(merged["windows"].get("appId") or merged["bundleIdentifier"]).strip(),
        merged["bundleIdentifier"],
    )
    merged["windows"]["publisher"] = (
        str(merged["windows"].get("publisher") or merged["companyName"]).strip() or merged["companyName"]
    )
    merged["windows"]["installerCompilerPath"] = str(
        merged["windows"].get("installerCompilerPath") or ""
    ).strip()
    merged["windows"]["installerCompilerRunner"] = str(
        merged["windows"].get("installerCompilerRunner") or ""
    ).strip()
    merged["linux"]["desktopFileName"] = (
        str(merged["linux"].get("desktopFileName") or "Canvasia Engine Editor.desktop").strip()
        or "Canvasia Engine Editor.desktop"
    )
    merged["linux"]["maintainer"] = (
        str(merged["linux"].get("maintainer") or merged["publisherName"]).strip() or merged["publisherName"]
    )
    categories = merged["linux"].get("categories")
    if not isinstance(categories, list):
        categories = ["Development"]
    merged["linux"]["categories"] = [str(item).strip() for item in categories if str(item).strip()] or ["Development"]
    merged["signing"]["macAppIdentity"] = str(merged["signing"].get("macAppIdentity") or "").strip()
    merged["signing"]["macInstallerIdentity"] = str(merged["signing"].get("macInstallerIdentity") or "").strip()
    merged["signing"]["macNotaryProfile"] = str(merged["signing"].get("macNotaryProfile") or "").strip()
    merged["signing"]["windowsSignToolPath"] = str(merged["signing"].get("windowsSignToolPath") or "").strip()
    merged["signing"]["windowsSignToolRunner"] = str(merged["signing"].get("windowsSignToolRunner") or "").strip()
    merged["signing"]["windowsCertificateSubject"] = str(
        merged["signing"].get("windowsCertificateSubject") or ""
    ).strip()
    merged["signing"]["windowsCertificateThumbprint"] = str(
        merged["signing"].get("windowsCertificateThumbprint") or ""
    ).strip()
    merged["signing"]["windowsPfxPath"] = str(merged["signing"].get("windowsPfxPath") or "").strip()
    merged["signing"]["windowsPfxPassword"] = str(merged["signing"].get("windowsPfxPassword") or "").strip()
    merged["signing"]["windowsTimestampUrl"] = str(
        merged["signing"].get("windowsTimestampUrl") or "http://timestamp.digicert.com"
    ).strip() or "http://timestamp.digicert.com"
    return merged


def get_editor_distribution_config_path() -> Path:
    return ROOT_DIR / EDITOR_DISTRIBUTION_CONFIG_NAME


def ensure_editor_distribution_config_file() -> Path:
    config_path = get_editor_distribution_config_path()
    if not config_path.is_file():
        write_json(config_path, build_default_editor_distribution_config())
    return config_path


def load_editor_distribution_config() -> tuple[dict, Path]:
    config_path = ensure_editor_distribution_config_file()
    raw_config = read_json(config_path)
    normalized = normalize_editor_distribution_config(raw_config)
    if raw_config != normalized:
        write_json(config_path, normalized)
    return normalized, config_path
DATA_DIR = TEMPLATE_DIR / "data"
CHAPTERS_DIR = DATA_DIR / "chapters"
PROJECT_PATH = TEMPLATE_DIR / "project.json"
CURRENT_PROJECT_INFO = {
    "projectId": SAMPLE_PROJECT_ID,
    "kind": "sample",
    "projectDir": str(SAMPLE_PROJECT_DIR),
}
HAS_SELECTED_PROJECT = False
CURRENT_SERVER_SESSION_ID = f"server_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"
PROJECT_BUNDLE_CACHE = SnapshotCache()


def find_available_port(start_port: int) -> int:
    port = start_port

    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                port += 1


def build_url(port: int) -> str:
    return f"http://127.0.0.1:{port}/prototype_editor/index.html"


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload: dict) -> None:
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            temp_path = Path(file.name)
            json.dump(payload, file, ensure_ascii=False, indent=2)
            file.write("\n")
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, path)
    except Exception:
        if temp_path is not None:
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise


def normalize_text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []

    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = str(item or "").strip()
        if text and text not in seen:
            normalized.append(text)
            seen.add(text)
    return normalized


def sanitize_release_version_value(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return DEFAULT_EXPORT_RELEASE_VERSION
    if len(text) > 40:
        return DEFAULT_EXPORT_RELEASE_VERSION
    if not re.fullmatch(r"[0-9A-Za-z][0-9A-Za-z._-]{0,39}", text):
        return DEFAULT_EXPORT_RELEASE_VERSION
    return text


def sanitize_project_resolution(value: object) -> dict:
    if isinstance(value, dict):
        try:
            width = int(value.get("width", 0))
            height = int(value.get("height", 0))
        except (TypeError, ValueError):
            width = 0
            height = 0
        if (width, height) in SUPPORTED_RESOLUTIONS:
            return {"width": width, "height": height}
    return {"width": 1920, "height": 1080}


def clamp_int(value: object, fallback: int, minimum: int, maximum: int) -> int:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        numeric = fallback
    return max(minimum, min(maximum, numeric))


def is_valid_hex_color(value: object) -> bool:
    return bool(re.fullmatch(r"#[0-9A-Fa-f]{6}", str(value or "").strip()))


def sanitize_hex_color(value: object, fallback: str) -> str:
    return str(value).strip().lower() if is_valid_hex_color(value) else fallback


def build_default_dialog_box_config() -> dict:
    return dict(DEFAULT_DIALOG_BOX_CONFIG)


def build_default_game_ui_config() -> dict:
    return json.loads(json.dumps(DEFAULT_GAME_UI_CONFIG, ensure_ascii=False))


def sanitize_dialog_box_config(value: object) -> dict:
    source = value if isinstance(value, dict) else {}
    defaults = build_default_dialog_box_config()
    preset = str(source.get("preset") or defaults["preset"]).strip().lower() or defaults["preset"]
    if preset not in {"warm", "moonlight", "paper", "transparent", "custom"}:
        preset = defaults["preset"]

    shape = str(source.get("shape") or defaults["shape"]).strip().lower() or defaults["shape"]
    if shape not in {"rounded", "square", "capsule"}:
        shape = defaults["shape"]

    panel_asset_fit = str(source.get("panelAssetFit") or defaults["panelAssetFit"]).strip().lower() or defaults["panelAssetFit"]
    if panel_asset_fit not in {"cover", "contain"}:
        panel_asset_fit = defaults["panelAssetFit"]

    anchor = str(source.get("anchor") or defaults["anchor"]).strip().lower() or defaults["anchor"]
    if anchor not in {"bottom", "center", "top", "free"}:
        anchor = defaults["anchor"]

    return {
        "preset": preset,
        "shape": shape,
        "widthPercent": clamp_int(source.get("widthPercent"), defaults["widthPercent"], 55, 100),
        "minHeight": clamp_int(source.get("minHeight"), defaults["minHeight"], 96, 320),
        "paddingX": clamp_int(source.get("paddingX"), defaults["paddingX"], 8, 72),
        "paddingY": clamp_int(source.get("paddingY"), defaults["paddingY"], 6, 48),
        "backgroundColor": sanitize_hex_color(source.get("backgroundColor"), defaults["backgroundColor"]),
        "backgroundOpacity": clamp_int(source.get("backgroundOpacity"), defaults["backgroundOpacity"], 0, 100),
        "borderColor": sanitize_hex_color(source.get("borderColor"), defaults["borderColor"]),
        "borderOpacity": clamp_int(source.get("borderOpacity"), defaults["borderOpacity"], 0, 100),
        "textColor": sanitize_hex_color(source.get("textColor"), defaults["textColor"]),
        "speakerColor": sanitize_hex_color(source.get("speakerColor"), defaults["speakerColor"]),
        "hintColor": sanitize_hex_color(source.get("hintColor"), defaults["hintColor"]),
        "blurStrength": clamp_int(source.get("blurStrength"), defaults["blurStrength"], 0, 24),
        "borderWidth": clamp_int(source.get("borderWidth"), defaults["borderWidth"], 0, 4),
        "shadowStrength": clamp_int(source.get("shadowStrength"), defaults["shadowStrength"], 0, 48),
        "panelAssetId": str(source.get("panelAssetId") or "").strip(),
        "panelAssetOpacity": clamp_int(source.get("panelAssetOpacity"), defaults["panelAssetOpacity"], 0, 100),
        "panelAssetFit": panel_asset_fit,
        "anchor": anchor,
        "offsetXPercent": clamp_int(source.get("offsetXPercent"), defaults["offsetXPercent"], -35, 35),
        "offsetYPercent": clamp_int(source.get("offsetYPercent"), defaults["offsetYPercent"], -35, 35),
    }


def sanitize_choice(value: object, allowed: set[str], fallback: str) -> str:
    normalized = str(value or fallback).strip().lower() or fallback
    return normalized if normalized in allowed else fallback


def sanitize_ui_frame_slice(value: object, fallback: dict) -> dict:
    source = value if isinstance(value, dict) else {}
    return {
        "top": clamp_int(source.get("top"), fallback.get("top", 18), 0, 96),
        "right": clamp_int(source.get("right"), fallback.get("right", 18), 0, 96),
        "bottom": clamp_int(source.get("bottom"), fallback.get("bottom", 18), 0, 96),
        "left": clamp_int(source.get("left"), fallback.get("left", 18), 0, 96),
    }


def sanitize_game_ui_config(value: object) -> dict:
    source = value if isinstance(value, dict) else {}
    defaults = build_default_game_ui_config()
    return {
        "preset": sanitize_choice(
            source.get("preset"),
            {"stellar", "warm", "paper", "minimal", "custom"},
            defaults["preset"],
        ),
        "layoutPreset": sanitize_choice(
            source.get("layoutPreset"),
            {"balanced", "cinematic", "compact", "minimal", "custom"},
            defaults["layoutPreset"],
        ),
        "titleLayout": sanitize_choice(
            source.get("titleLayout"),
            {"center", "left", "poster"},
            defaults["titleLayout"],
        ),
        "fontStyle": sanitize_choice(
            source.get("fontStyle"),
            {"modern", "serif", "rounded"},
            defaults["fontStyle"],
        ),
        "fontFamily": str(source.get("fontFamily") or defaults["fontFamily"]).strip()[:80],
        "fontAssetId": str(source.get("fontAssetId") or defaults["fontAssetId"]).strip(),
        "surfaceStyle": sanitize_choice(
            source.get("surfaceStyle"),
            {"glass", "solid", "minimal"},
            defaults["surfaceStyle"],
        ),
        "brandMode": sanitize_choice(
            source.get("brandMode"),
            {"project", "engine", "hidden"},
            defaults["brandMode"],
        ),
        "sidePanelMode": sanitize_choice(
            source.get("sidePanelMode"),
            {"full", "compact", "hidden"},
            defaults["sidePanelMode"],
        ),
        "sidePanelPosition": sanitize_choice(
            source.get("sidePanelPosition"),
            {"right", "left"},
            defaults["sidePanelPosition"],
        ),
        "topbarPosition": sanitize_choice(
            source.get("topbarPosition"),
            {"top", "bottom", "hidden"},
            defaults["topbarPosition"],
        ),
        "hudPosition": sanitize_choice(
            source.get("hudPosition"),
            {"top", "top-left", "top-right", "bottom-left", "bottom-right", "hidden"},
            defaults["hudPosition"],
        ),
        "titleCardAnchor": sanitize_choice(
            source.get("titleCardAnchor"),
            {"center", "left", "right", "top", "bottom", "free"},
            defaults["titleCardAnchor"],
        ),
        "titleCardOffsetXPercent": clamp_int(
            source.get("titleCardOffsetXPercent"),
            defaults["titleCardOffsetXPercent"],
            -35,
            35,
        ),
        "titleCardOffsetYPercent": clamp_int(
            source.get("titleCardOffsetYPercent"),
            defaults["titleCardOffsetYPercent"],
            -35,
            35,
        ),
        "layoutGap": clamp_int(source.get("layoutGap"), defaults["layoutGap"], 8, 48),
        "sidePanelWidth": clamp_int(source.get("sidePanelWidth"), defaults["sidePanelWidth"], 240, 460),
        "backgroundColor": sanitize_hex_color(source.get("backgroundColor"), defaults["backgroundColor"]),
        "backgroundAccentColor": sanitize_hex_color(
            source.get("backgroundAccentColor"),
            defaults["backgroundAccentColor"],
        ),
        "panelColor": sanitize_hex_color(source.get("panelColor"), defaults["panelColor"]),
        "panelOpacity": clamp_int(source.get("panelOpacity"), defaults["panelOpacity"], 35, 100),
        "textColor": sanitize_hex_color(source.get("textColor"), defaults["textColor"]),
        "mutedTextColor": sanitize_hex_color(source.get("mutedTextColor"), defaults["mutedTextColor"]),
        "accentColor": sanitize_hex_color(source.get("accentColor"), defaults["accentColor"]),
        "accentAltColor": sanitize_hex_color(source.get("accentAltColor"), defaults["accentAltColor"]),
        "buttonTextColor": sanitize_hex_color(source.get("buttonTextColor"), defaults["buttonTextColor"]),
        "borderColor": sanitize_hex_color(source.get("borderColor"), defaults["borderColor"]),
        "borderOpacity": clamp_int(source.get("borderOpacity"), defaults["borderOpacity"], 0, 100),
        "cornerRadius": clamp_int(source.get("cornerRadius"), defaults["cornerRadius"], 4, 42),
        "backdropBlur": clamp_int(source.get("backdropBlur"), defaults["backdropBlur"], 0, 28),
        "stageVignette": clamp_int(source.get("stageVignette"), defaults["stageVignette"], 0, 80),
        "motionIntensity": clamp_int(source.get("motionIntensity"), defaults["motionIntensity"], 0, 100),
        "titleBackgroundAssetId": str(source.get("titleBackgroundAssetId") or "").strip(),
        "titleBackgroundFit": sanitize_choice(
            source.get("titleBackgroundFit"),
            {"cover", "contain"},
            defaults["titleBackgroundFit"],
        ),
        "titleBackgroundOpacity": clamp_int(
            source.get("titleBackgroundOpacity"),
            defaults["titleBackgroundOpacity"],
            0,
            100,
        ),
        "titleLogoAssetId": str(source.get("titleLogoAssetId") or "").strip(),
        "panelFrameAssetId": str(source.get("panelFrameAssetId") or "").strip(),
        "panelFrameOpacity": clamp_int(source.get("panelFrameOpacity"), defaults["panelFrameOpacity"], 0, 100),
        "panelFrameSlice": sanitize_ui_frame_slice(source.get("panelFrameSlice"), defaults["panelFrameSlice"]),
        "buttonFrameAssetId": str(source.get("buttonFrameAssetId") or "").strip(),
        "buttonHoverFrameAssetId": str(source.get("buttonHoverFrameAssetId") or "").strip(),
        "buttonPressedFrameAssetId": str(source.get("buttonPressedFrameAssetId") or "").strip(),
        "buttonDisabledFrameAssetId": str(source.get("buttonDisabledFrameAssetId") or "").strip(),
        "buttonFrameOpacity": clamp_int(source.get("buttonFrameOpacity"), defaults["buttonFrameOpacity"], 0, 100),
        "buttonFrameSlice": sanitize_ui_frame_slice(source.get("buttonFrameSlice"), defaults["buttonFrameSlice"]),
        "saveSlotFrameAssetId": str(source.get("saveSlotFrameAssetId") or "").strip(),
        "systemPanelFrameAssetId": str(source.get("systemPanelFrameAssetId") or "").strip(),
        "uiOverlayAssetId": str(source.get("uiOverlayAssetId") or "").strip(),
        "uiOverlayOpacity": clamp_int(source.get("uiOverlayOpacity"), defaults["uiOverlayOpacity"], 0, 100),
    }


def build_unique_slug_id(
    existing_ids: set[str],
    prefix: str,
    raw_name: object,
    *,
    fallback_number: int = 1,
) -> str:
    base_slug = make_slug(str(raw_name or "").strip())
    if not base_slug or base_slug == "asset":
        base_slug = f"{prefix}_{fallback_number:02d}"
    candidate = f"{prefix}_{base_slug}"
    suffix = 2
    while candidate in existing_ids:
        candidate = f"{prefix}_{base_slug}_{suffix:02d}"
        suffix += 1
    existing_ids.add(candidate)
    return candidate


def normalize_particle_presets_for_migration(value: object) -> list[dict]:
    if not isinstance(value, list):
        return []
    try:
        return sanitize_particle_custom_presets(value)
    except ValueError:
        return []


def normalize_language_code(value: object, fallback: str = DEFAULT_PROJECT_LANGUAGE) -> str:
    raw_value = str(value or "").strip()
    if not raw_value:
        return fallback
    if not re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8}){0,2}", raw_value):
        return fallback
    parts = raw_value.split("-")
    normalized_parts = [parts[0].lower()]
    for index, part in enumerate(parts[1:], start=1):
        normalized_parts.append(part.upper() if index == 1 and len(part) in {2, 3} else part)
    return "-".join(normalized_parts)


def normalize_supported_languages(value: object, default_language: str = DEFAULT_PROJECT_LANGUAGE) -> list[str]:
    raw_languages = value if isinstance(value, list) else []
    languages: list[str] = []
    for raw_language in raw_languages:
        language = normalize_language_code(raw_language, "")
        if language and language not in languages:
            languages.append(language)
    if default_language not in languages:
        languages.insert(0, default_language)
    if not languages:
        languages.append(DEFAULT_PROJECT_LANGUAGE)
    return languages[:8]


def normalize_translation_map(value: object) -> dict:
    if not isinstance(value, dict):
        return {}
    translations: dict[str, str] = {}
    for raw_language, raw_text in value.items():
        language = normalize_language_code(raw_language, "")
        text = str(raw_text or "").strip()
        if language and text:
            translations[language] = text[:8000]
    return translations


def normalize_scene_block(block: object, index: int, existing_ids: set[str]) -> dict:
    normalized = dict(block) if isinstance(block, dict) else {}
    block_id = str(normalized.get("id") or "").strip()
    if not block_id or block_id in existing_ids:
        block_id = f"block_{index:03d}"
        suffix = 2
        while block_id in existing_ids:
            block_id = f"block_{index:03d}_{suffix:02d}"
            suffix += 1
    existing_ids.add(block_id)
    normalized["id"] = block_id
    normalized["type"] = str(normalized.get("type") or "narration").strip() or "narration"

    if normalized["type"] == "choice":
        options = normalized.get("options")
        normalized_options = []
        if isinstance(options, list):
            for option in options:
                if not isinstance(option, dict):
                    continue
                normalized_option = dict(option)
                normalized_option["textTranslations"] = normalize_translation_map(
                    normalized_option.get("textTranslations")
                )
                if not normalized_option["textTranslations"]:
                    normalized_option.pop("textTranslations", None)
                normalized_options.append(normalized_option)
        normalized["options"] = normalized_options
    if normalized["type"] == "condition":
        branches = normalized.get("branches")
        normalized["branches"] = branches if isinstance(branches, list) else []
    for translation_key in ("textTranslations", "titleTranslations"):
        translations = normalize_translation_map(normalized.get(translation_key))
        if translations:
            normalized[translation_key] = translations
        else:
            normalized.pop(translation_key, None)
    return normalized


def normalize_scene_document(scene: object, index: int, existing_scene_ids: set[str]) -> dict:
    normalized = dict(scene) if isinstance(scene, dict) else {}
    scene_id = str(normalized.get("id") or "").strip()
    if not scene_id or scene_id in existing_scene_ids:
        scene_id = build_unique_slug_id(existing_scene_ids, "scene", normalized.get("name") or scene_id, fallback_number=index)
    else:
        existing_scene_ids.add(scene_id)
    normalized["id"] = scene_id
    normalized["name"] = str(normalized.get("name") or f"未命名场景 {index}").strip() or f"未命名场景 {index}"
    scene_name_translations = normalize_translation_map(normalized.get("nameTranslations"))
    if scene_name_translations:
        normalized["nameTranslations"] = scene_name_translations
    else:
        normalized.pop("nameTranslations", None)
    normalized["notes"] = str(normalized.get("notes") or "").strip()
    normalized["status"] = str(normalized.get("status") or "drafting").strip() or "drafting"
    if normalized["status"] not in {"outline", "drafting", "polishing", "ready"}:
        normalized["status"] = "drafting"
    normalized["priority"] = str(normalized.get("priority") or "normal").strip() or "normal"
    if normalized["priority"] not in {"normal", "focus", "rush", "parked"}:
        normalized["priority"] = "normal"
    raw_blocks = normalized.get("blocks")
    normalized["blocks"] = []
    block_ids: set[str] = set()
    if isinstance(raw_blocks, list):
        for block_index, block in enumerate(raw_blocks, start=1):
            normalized["blocks"].append(normalize_scene_block(block, block_index, block_ids))
    return normalized


def normalize_chapter_document(chapter: object, fallback_file_stem: str) -> dict:
    normalized = dict(chapter) if isinstance(chapter, dict) else {}
    chapter_id = str(normalized.get("chapterId") or "").strip() or make_slug(fallback_file_stem)
    if not chapter_id.startswith("chapter"):
        chapter_id = f"chapter_{chapter_id}"
    normalized["chapterId"] = chapter_id
    normalized["formatVersion"] = PROJECT_FORMAT_VERSION
    normalized["name"] = str(normalized.get("name") or chapter_id).strip() or chapter_id
    chapter_name_translations = normalize_translation_map(normalized.get("nameTranslations"))
    if chapter_name_translations:
        normalized["nameTranslations"] = chapter_name_translations
    else:
        normalized.pop("nameTranslations", None)
    normalized["notes"] = str(normalized.get("notes") or "").strip()

    raw_scenes = normalized.get("scenes")
    normalized_scenes: list[dict] = []
    existing_scene_ids: set[str] = set()
    if isinstance(raw_scenes, list):
        for index, scene in enumerate(raw_scenes, start=1):
            normalized_scenes.append(normalize_scene_document(scene, index, existing_scene_ids))
    normalized["scenes"] = normalized_scenes

    discovered_scene_ids = [scene.get("id") for scene in normalized_scenes if scene.get("id")]
    ordered_scene_ids: list[str] = []
    seen_scene_ids: set[str] = set()
    for scene_id in normalize_text_list(normalized.get("sceneOrder")):
        if scene_id in discovered_scene_ids and scene_id not in seen_scene_ids:
            ordered_scene_ids.append(scene_id)
            seen_scene_ids.add(scene_id)
    for scene_id in discovered_scene_ids:
        if scene_id not in seen_scene_ids:
            ordered_scene_ids.append(scene_id)
            seen_scene_ids.add(scene_id)
    normalized["sceneOrder"] = ordered_scene_ids
    return normalized


def normalize_assets_document(payload: object) -> dict:
    source = payload if isinstance(payload, dict) else {}
    raw_assets = source.get("assets") if isinstance(source.get("assets"), list) else payload if isinstance(payload, list) else []
    normalized_assets: list[dict] = []
    existing_ids: set[str] = set()
    for index, raw_asset in enumerate(raw_assets, start=1):
        if not isinstance(raw_asset, dict):
            continue
        asset = dict(raw_asset)
        asset_type = str(asset.get("type") or "ui").strip() or "ui"
        asset_id = str(asset.get("id") or "").strip()
        if not asset_id or asset_id in existing_ids:
            asset_id = build_unique_slug_id(existing_ids, ASSET_ID_PREFIXES.get(asset_type, "asset"), asset.get("name") or asset.get("path") or asset_type, fallback_number=index)
        else:
            existing_ids.add(asset_id)
        asset["id"] = asset_id
        asset["type"] = asset_type
        asset["name"] = str(asset.get("name") or asset_id).strip() or asset_id
        asset["path"] = str(asset.get("path") or "").replace("\\", "/").strip()
        asset["tags"] = normalize_text_list(asset.get("tags"))
        asset["favorite"] = bool(asset.get("favorite"))
        rights_payload = {
            field: asset.get(field)
            for field in (*ASSET_RIGHTS_TEXT_LIMITS.keys(), "commercialUse", *ASSET_RIGHTS_BOOLEAN_FIELDS)
            if field in asset
        }
        apply_asset_rights_metadata(asset, rights_payload)
        normalized_assets.append(asset)
    return {
        "formatVersion": PROJECT_FORMAT_VERSION,
        "assets": normalized_assets,
    }


def normalize_characters_document(payload: object) -> dict:
    source = payload if isinstance(payload, dict) else {}
    raw_characters = source.get("characters") if isinstance(source.get("characters"), list) else payload if isinstance(payload, list) else []
    normalized_characters: list[dict] = []
    existing_ids: set[str] = set()
    for index, raw_character in enumerate(raw_characters, start=1):
        if not isinstance(raw_character, dict):
            continue
        character = dict(raw_character)
        character_id = str(character.get("id") or "").strip()
        if not character_id or character_id in existing_ids:
            character_id = build_unique_slug_id(existing_ids, "char", character.get("displayName") or character.get("name") or f"character_{index:02d}", fallback_number=index)
        else:
            existing_ids.add(character_id)
        character["id"] = character_id
        display_name = str(character.get("displayName") or character.get("name") or character_id).strip() or character_id
        character["displayName"] = display_name
        display_name_translations = normalize_translation_map(character.get("displayNameTranslations"))
        if display_name_translations:
            character["displayNameTranslations"] = display_name_translations
        else:
            character.pop("displayNameTranslations", None)
        character["nameColor"] = str(character.get("nameColor") or "#E0E6FF").strip() or "#E0E6FF"
        default_position = str(character.get("defaultPosition") or "center").strip() or "center"
        character["defaultPosition"] = default_position if default_position in {"left", "center", "right"} else "center"
        character["bio"] = str(character.get("bio") or "").strip()
        character["defaultSpriteId"] = str(character.get("defaultSpriteId") or "").strip()
        character["presentation"] = normalize_character_presentation(
            character.get("presentation"),
            character["defaultSpriteId"],
        )

        expressions = character.get("expressions")
        normalized_expressions: list[dict] = []
        expression_ids: set[str] = set()
        if isinstance(expressions, list):
            for expression_index, raw_expression in enumerate(expressions, start=1):
                if not isinstance(raw_expression, dict):
                    continue
                expression = dict(raw_expression)
                expression_id = str(expression.get("id") or "").strip()
                if not expression_id or expression_id in expression_ids:
                    expression_id = build_unique_slug_id(expression_ids, "expr", expression.get("name") or f"expression_{expression_index:02d}", fallback_number=expression_index)
                else:
                    expression_ids.add(expression_id)
                expression["id"] = expression_id
                expression["name"] = str(expression.get("name") or expression_id).strip() or expression_id
                expression["spriteAssetId"] = str(expression.get("spriteAssetId") or "").strip()
                expression["layerAssetIds"] = normalize_text_list(expression.get("layerAssetIds"))
                expression["live2dExpression"] = str(expression.get("live2dExpression") or "").strip()
                expression["live2dMotion"] = str(expression.get("live2dMotion") or "").strip()
                expression["model3dExpression"] = str(expression.get("model3dExpression") or "").strip()
                expression["model3dAnimation"] = str(expression.get("model3dAnimation") or "").strip()
                normalized_expressions.append(expression)
        character["expressions"] = normalized_expressions
        normalized_characters.append(character)
    return {
        "formatVersion": PROJECT_FORMAT_VERSION,
        "characters": normalized_characters,
    }


def normalize_character_presentation(payload: object, fallback_sprite_asset_id: str = "") -> dict:
    source = payload if isinstance(payload, dict) else {}
    mode = str(source.get("mode") or "sprite").strip()
    if mode not in {"sprite", "layered_sprite", "live2d", "model3d"}:
        mode = "sprite"

    fallback_sprite = str(source.get("fallbackSpriteAssetId") or fallback_sprite_asset_id or "").strip()
    live2d_source = source.get("live2d") if isinstance(source.get("live2d"), dict) else {}
    model3d_source = source.get("model3d") if isinstance(source.get("model3d"), dict) else {}

    return {
        "mode": mode,
        "fallbackSpriteAssetId": fallback_sprite,
        "live2d": {
            "modelAssetId": str(live2d_source.get("modelAssetId") or "").strip(),
            "idleMotion": str(live2d_source.get("idleMotion") or "").strip(),
            "blink": bool(live2d_source.get("blink", True)),
            "breath": bool(live2d_source.get("breath", True)),
            "lipSync": bool(live2d_source.get("lipSync", True)),
            "cursorTracking": bool(live2d_source.get("cursorTracking", False)),
        },
        "model3d": {
            "modelAssetId": str(model3d_source.get("modelAssetId") or "").strip(),
            "idleAnimation": str(model3d_source.get("idleAnimation") or "").strip(),
            "cameraPreset": str(model3d_source.get("cameraPreset") or "portrait").strip() or "portrait",
            "lightingPreset": str(model3d_source.get("lightingPreset") or "studio").strip() or "studio",
        },
    }


def collect_character_presentation_asset_ids(character: dict) -> list[tuple[str, str]]:
    presentation = normalize_character_presentation(
        character.get("presentation"),
        str(character.get("defaultSpriteId") or ""),
    )
    items: list[tuple[str, str]] = []
    fallback_sprite_id = str(presentation.get("fallbackSpriteAssetId") or "").strip()
    if fallback_sprite_id:
        items.append((fallback_sprite_id, "高级表现兜底立绘"))

    live2d_asset_id = str((presentation.get("live2d") or {}).get("modelAssetId") or "").strip()
    if live2d_asset_id:
        items.append((live2d_asset_id, "Live2D 模型入口"))

    model3d_asset_id = str((presentation.get("model3d") or {}).get("modelAssetId") or "").strip()
    if model3d_asset_id:
        items.append((model3d_asset_id, "3D 模型入口"))

    for expression in character.get("expressions", []) or []:
        for layer_asset_id in normalize_text_list(expression.get("layerAssetIds")):
            items.append((layer_asset_id, f"差分图层：{expression.get('name') or expression.get('id') or '表情'}"))

    return items


def normalize_variables_document(payload: object) -> dict:
    source = payload if isinstance(payload, dict) else {}
    raw_variables = source.get("variables") if isinstance(source.get("variables"), list) else payload if isinstance(payload, list) else []
    normalized_variables: list[dict] = []
    existing_ids: set[str] = set()
    for index, raw_variable in enumerate(raw_variables, start=1):
        if not isinstance(raw_variable, dict):
            continue
        variable = dict(raw_variable)
        variable_id = str(variable.get("id") or "").strip()
        if not variable_id or variable_id in existing_ids:
            variable_id = build_unique_slug_id(existing_ids, "var", variable.get("name") or f"variable_{index:02d}", fallback_number=index)
        else:
            existing_ids.add(variable_id)
        variable["id"] = variable_id
        variable["name"] = str(variable.get("name") or variable_id).strip() or variable_id
        variable_type = str(variable.get("type") or "string").strip().lower() or "string"
        if variable_type not in {"number", "boolean", "string"}:
            variable_type = "string"
        variable["type"] = variable_type
        if "defaultValue" not in variable:
            variable["defaultValue"] = 0 if variable_type == "number" else False if variable_type == "boolean" else ""
        normalized_variables.append(variable)
    return {
        "formatVersion": PROJECT_FORMAT_VERSION,
        "variables": normalized_variables,
    }


def normalize_project_document(
    payload: object,
    *,
    project_id: str,
    discovered_chapter_ids: list[str],
    fallback_entry_scene_id: str,
) -> dict:
    normalized = dict(payload) if isinstance(payload, dict) else {}
    timestamp = now_iso()
    normalized["formatVersion"] = PROJECT_FORMAT_VERSION
    normalized["projectId"] = str(normalized.get("projectId") or project_id).strip() or project_id
    normalized["title"] = str(normalized.get("title") or normalized["projectId"]).strip() or normalized["projectId"]
    normalized["template"] = str(normalized.get("template") or "blank").strip() or "blank"
    normalized["language"] = normalize_language_code(normalized.get("language"), DEFAULT_PROJECT_LANGUAGE)
    normalized["supportedLanguages"] = normalize_supported_languages(
        normalized.get("supportedLanguages"),
        normalized["language"],
    )
    normalized["releaseVersion"] = sanitize_release_version_value(normalized.get("releaseVersion"))
    editor_mode = str(normalized.get("editorMode") or DEFAULT_EDITOR_MODE).strip().lower() or DEFAULT_EDITOR_MODE
    normalized["editorMode"] = editor_mode if editor_mode in {"beginner", "advanced"} else DEFAULT_EDITOR_MODE
    normalized["resolution"] = sanitize_project_resolution(normalized.get("resolution"))
    normalized["runtimeSettings"] = sanitize_project_runtime_settings(normalized.get("runtimeSettings"))
    normalized["dialogBoxConfig"] = sanitize_dialog_box_config(normalized.get("dialogBoxConfig"))
    normalized["gameUiConfig"] = sanitize_game_ui_config(normalized.get("gameUiConfig"))
    normalized["particleCustomPresets"] = normalize_particle_presets_for_migration(
        normalized.get("particleCustomPresets")
    )
    if not normalized["particleCustomPresets"]:
        normalized.pop("particleCustomPresets", None)

    created_at = str(normalized.get("createdAt") or "").strip()
    updated_at = str(normalized.get("updatedAt") or "").strip()
    normalized["createdAt"] = created_at or updated_at or timestamp
    normalized["updatedAt"] = updated_at or created_at or timestamp

    chapter_order: list[str] = []
    seen_chapter_ids: set[str] = set()
    for chapter_id in normalize_text_list(normalized.get("chapterOrder")):
        if chapter_id in discovered_chapter_ids and chapter_id not in seen_chapter_ids:
            chapter_order.append(chapter_id)
            seen_chapter_ids.add(chapter_id)
    for chapter_id in discovered_chapter_ids:
        if chapter_id not in seen_chapter_ids:
            chapter_order.append(chapter_id)
            seen_chapter_ids.add(chapter_id)
    normalized["chapterOrder"] = chapter_order

    entry_scene_id = str(normalized.get("entrySceneId") or "").strip()
    normalized["entrySceneId"] = entry_scene_id or fallback_entry_scene_id
    return normalized


def migrate_project_directory(project_dir: Path, project_id: str | None = None) -> dict:
    project_path = project_dir / "project.json"
    if not project_path.is_file():
        raise ValueError("项目目录里缺少 project.json。")

    data_dir = project_dir / "data"
    chapters_dir = data_dir / "chapters"
    data_dir.mkdir(parents=True, exist_ok=True)
    chapters_dir.mkdir(parents=True, exist_ok=True)

    project_doc_raw = read_json(project_path)
    assets_path = data_dir / "assets.json"
    characters_path = data_dir / "characters.json"
    variables_path = data_dir / "variables.json"
    assets_raw = read_json(assets_path) if assets_path.is_file() else {}
    characters_raw = read_json(characters_path) if characters_path.is_file() else {}
    variables_raw = read_json(variables_path) if variables_path.is_file() else {}

    normalized_chapter_docs: list[tuple[Path, dict, dict]] = []
    discovered_chapter_ids: list[str] = []
    fallback_entry_scene_id = ""

    for chapter_path in sorted(chapters_dir.glob("chapter_*.json")):
        chapter_raw = read_json(chapter_path)
        normalized_chapter = normalize_chapter_document(chapter_raw, chapter_path.stem)
        normalized_chapter_docs.append((chapter_path, chapter_raw, normalized_chapter))
        chapter_id = str(normalized_chapter.get("chapterId") or "").strip()
        if chapter_id:
            discovered_chapter_ids.append(chapter_id)
        if not fallback_entry_scene_id:
            fallback_entry_scene_id = next(
                (scene_id for scene_id in normalized_chapter.get("sceneOrder", []) if scene_id),
                "",
            )

    normalized_project = normalize_project_document(
        project_doc_raw,
        project_id=project_id or project_dir.name,
        discovered_chapter_ids=discovered_chapter_ids,
        fallback_entry_scene_id=fallback_entry_scene_id,
    )
    normalized_assets = normalize_assets_document(assets_raw)
    normalized_characters = normalize_characters_document(characters_raw)
    normalized_variables = normalize_variables_document(variables_raw)

    pending_writes: list[tuple[Path, dict]] = []
    changed_files: list[str] = []

    def queue_if_changed(path: Path, current_payload: object, next_payload: dict) -> None:
        current_exists = path.is_file()
        if (not current_exists) or current_payload != next_payload:
            pending_writes.append((path, next_payload))
            changed_files.append(str(path.relative_to(project_dir)))

    queue_if_changed(project_path, project_doc_raw, normalized_project)
    queue_if_changed(assets_path, assets_raw, normalized_assets)
    queue_if_changed(characters_path, characters_raw, normalized_characters)
    queue_if_changed(variables_path, variables_raw, normalized_variables)
    for chapter_path, chapter_raw, normalized_chapter in normalized_chapter_docs:
        queue_if_changed(chapter_path, chapter_raw, normalized_chapter)

    if pending_writes:
        ensure_project_history_initialized(project_dir)
        for path, payload in pending_writes:
            write_json(path, payload)
        create_history_snapshot(
            f"自动升级到项目格式 v{PROJECT_FORMAT_VERSION}",
            kind="migration",
            project_dir=project_dir,
        )

    return {
        "project": normalized_project,
        "changed": bool(pending_writes),
        "changedFiles": changed_files,
        "targetFormatVersion": PROJECT_FORMAT_VERSION,
    }


def set_active_project_paths(project_id: str, project_dir: Path, kind: str = "project") -> None:
    global TEMPLATE_DIR, DATA_DIR, CHAPTERS_DIR, PROJECT_PATH, CURRENT_PROJECT_INFO

    previous_project_dir = Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR)
    previous_project_id = str(CURRENT_PROJECT_INFO.get("projectId") or "").strip()
    if previous_project_id and previous_project_dir.is_dir() and previous_project_dir != project_dir:
        mark_project_session_closed(previous_project_dir, reason="switched-project")

    TEMPLATE_DIR = project_dir
    DATA_DIR = TEMPLATE_DIR / "data"
    CHAPTERS_DIR = DATA_DIR / "chapters"
    PROJECT_PATH = TEMPLATE_DIR / "project.json"
    CURRENT_PROJECT_INFO = {
        "projectId": project_id,
        "kind": kind,
        "projectDir": str(project_dir),
    }
    clear_project_bundle_cache()
    migrate_project_directory(project_dir, project_id)
    ensure_project_history_initialized(project_dir)
    mark_project_session_running(project_id, project_dir, kind=kind)


def ensure_project_roots() -> None:
    PROJECTS_DIR.mkdir(exist_ok=True)


def build_project_public_root(project_dir: Path) -> str:
    try:
        relative_root = project_dir.relative_to(ROOT_DIR)
    except ValueError:
        return ""

    encoded = "/".join(quote(part) for part in relative_root.parts if part)
    return f"/{encoded}" if encoded else ""


INTERNAL_PROJECT_TITLE_MARKERS = ("打包烟测", "packaging smoke", "package smoke")


def is_internal_project_summary(summary: dict) -> bool:
    haystack = " ".join(str(summary.get(key) or "") for key in ("projectId", "title", "template")).lower()
    return any(marker in haystack for marker in INTERNAL_PROJECT_TITLE_MARKERS)


def build_project_summary(project_id: str, project_dir: Path, kind: str = "project") -> dict:
    project_path = project_dir / "project.json"
    if not project_path.is_file():
        raise ValueError("项目目录里缺少 project.json。")

    project = migrate_project_directory(project_dir, project_id)["project"]
    chapters_dir = project_dir / "data" / "chapters"
    chapter_files = sorted(chapters_dir.glob("chapter_*.json")) if chapters_dir.is_dir() else []
    scene_count = 0
    for chapter_path in chapter_files:
        chapter = read_json(chapter_path)
        scene_count += len(chapter.get("scenes", []))

    resolution = project.get("resolution") or {"width": 1920, "height": 1080}
    return {
        "projectId": project_id,
        "kind": kind,
        "title": project.get("title") or project_id,
        "template": project.get("template") or "blank",
        "language": project.get("language") or DEFAULT_PROJECT_LANGUAGE,
        "supportedLanguages": project.get("supportedLanguages") or [project.get("language") or DEFAULT_PROJECT_LANGUAGE],
        "editorMode": project.get("editorMode") or DEFAULT_EDITOR_MODE,
        "chapterCount": len(chapter_files),
        "sceneCount": scene_count,
        "updatedAt": project.get("updatedAt") or project.get("createdAt") or "",
        "createdAt": project.get("createdAt") or project.get("updatedAt") or "",
        "resolution": resolution,
        "publicRoot": build_project_public_root(project_dir),
        "isSample": kind == "sample",
    }


def list_local_projects() -> list[dict]:
    ensure_project_roots()
    projects: list[dict] = []

    for project_dir in sorted(path for path in PROJECTS_DIR.iterdir() if path.is_dir()):
        project_path = project_dir / "project.json"
        if not project_path.is_file():
            continue

        try:
            summary = build_project_summary(project_dir.name, project_dir)
            if is_internal_project_summary(summary):
                continue
            projects.append(summary)
        except Exception:
            continue

    projects.sort(
        key=lambda item: (
            item.get("updatedAt") or "",
            item.get("createdAt") or "",
            item.get("title") or "",
        ),
        reverse=True,
    )
    return projects


def get_sample_project_summary() -> dict | None:
    if not (SAMPLE_PROJECT_DIR / "project.json").is_file():
        return None
    return build_project_summary(SAMPLE_PROJECT_ID, SAMPLE_PROJECT_DIR, kind="sample")


def find_project_summary(project_id: str) -> dict | None:
    if project_id == SAMPLE_PROJECT_ID:
        return get_sample_project_summary()

    for project in list_local_projects():
        if project.get("projectId") == project_id:
            return project

    return None


def activate_project(project_id: str) -> dict:
    global HAS_SELECTED_PROJECT
    summary = find_project_summary(project_id)
    if not summary:
        raise ValueError("没有找到要打开的项目。")

    project_dir = SAMPLE_PROJECT_DIR if summary.get("kind") == "sample" else PROJECTS_DIR / summary["projectId"]
    set_active_project_paths(summary["projectId"], project_dir, summary.get("kind") or "project")
    HAS_SELECTED_PROJECT = True
    return summary


def get_current_project_summary() -> dict:
    project_dir = Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR)
    project_id = CURRENT_PROJECT_INFO.get("projectId") or SAMPLE_PROJECT_ID
    kind = CURRENT_PROJECT_INFO.get("kind") or "project"
    return build_project_summary(project_id, project_dir, kind=kind)


def get_project_center_payload() -> dict:
    sample_project = get_sample_project_summary()
    projects = list_local_projects()
    if sample_project:
        projects.append(sample_project)

    return {
        "activeProjectId": CURRENT_PROJECT_INFO.get("projectId") if HAS_SELECTED_PROJECT else None,
        "projects": projects,
    }


def list_chapter_files() -> list[Path]:
    return sorted(CHAPTERS_DIR.glob("chapter_*.json"))


def clear_project_bundle_cache() -> None:
    PROJECT_BUNDLE_CACHE.clear()


def build_project_bundle_cache_signature() -> tuple:
    project_dir = Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR)
    history_root = get_history_root(project_dir)
    watched_files = [
        PROJECT_PATH,
        DATA_DIR / "assets.json",
        DATA_DIR / "characters.json",
        DATA_DIR / "variables.json",
        get_history_manifest_path(project_dir),
        get_session_state_path(project_dir),
        *list_chapter_files(),
    ]
    watched_signatures = [build_file_cache_signature(path) for path in watched_files]

    asset_file_signatures: list[tuple] = []
    try:
        assets_doc = read_json(DATA_DIR / "assets.json")
    except Exception:
        assets_doc = {}
    for asset in assets_doc.get("assets", []) if isinstance(assets_doc, dict) else []:
        if not isinstance(asset, dict):
            continue
        relative_path = str(asset.get("path") or "").strip()
        if not relative_path:
            continue
        asset_file_signatures.append(build_file_cache_signature(TEMPLATE_DIR / relative_path))

    return (
        str(CURRENT_PROJECT_INFO.get("projectId") or SAMPLE_PROJECT_ID),
        str(CURRENT_PROJECT_INFO.get("kind") or "project"),
        project_dir.as_posix(),
        history_root.as_posix(),
        tuple(watched_signatures),
        tuple(asset_file_signatures),
    )


def build_public_asset_path(relative_path: str) -> str:
    normalized = str(relative_path or "").replace("\\", "/").strip("/")
    encoded = "/".join(quote(part) for part in normalized.split("/") if part)
    public_root = build_project_public_root(Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR))
    return f"{public_root}/{encoded}" if encoded and public_root else ""


def enrich_asset_record(asset: dict) -> dict:
    relative_path = asset.get("path", "")
    asset_file = TEMPLATE_DIR / relative_path if relative_path else None
    file_exists = bool(asset_file and asset_file.is_file())
    file_size_bytes = asset_file.stat().st_size if file_exists else None
    public_path = build_public_asset_path(relative_path) if relative_path else ""
    return {
        **asset,
        "fileExists": file_exists,
        "fileSizeBytes": file_size_bytes,
        "publicPath": public_path,
        "favorite": bool(asset.get("favorite")),
    }


def load_assets_document() -> dict:
    assets_doc = read_json(DATA_DIR / "assets.json")
    assets_doc["assets"] = [enrich_asset_record(asset) for asset in assets_doc.get("assets", [])]
    return assets_doc


def build_current_project_summary_from_loaded(project: dict, chapter_docs: list[dict]) -> dict:
    project_dir = Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR)
    project_id = str(CURRENT_PROJECT_INFO.get("projectId") or SAMPLE_PROJECT_ID)
    kind = str(CURRENT_PROJECT_INFO.get("kind") or "project")
    resolution = project.get("resolution") or {"width": 1920, "height": 1080}
    return {
        "projectId": project_id,
        "kind": kind,
        "title": project.get("title") or project_id,
        "template": project.get("template") or "blank",
        "language": project.get("language") or DEFAULT_PROJECT_LANGUAGE,
        "supportedLanguages": project.get("supportedLanguages") or [project.get("language") or DEFAULT_PROJECT_LANGUAGE],
        "editorMode": project.get("editorMode") or DEFAULT_EDITOR_MODE,
        "chapterCount": len(chapter_docs),
        "sceneCount": sum(len(chapter.get("scenes", [])) for chapter in chapter_docs),
        "updatedAt": project.get("updatedAt") or project.get("createdAt") or "",
        "createdAt": project.get("createdAt") or project.get("updatedAt") or "",
        "resolution": resolution,
        "publicRoot": build_project_public_root(project_dir),
        "isSample": kind == "sample",
    }


def build_project_bundle_uncached() -> dict:
    migration_result = migrate_project_directory(
        Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR),
        str(CURRENT_PROJECT_INFO.get("projectId") or SAMPLE_PROJECT_ID),
    )
    project = migration_result["project"]
    chapter_docs = [read_json(path) for path in list_chapter_files()]
    chapter_order = project.get("chapterOrder", [])

    if chapter_order:
        chapter_map = {chapter.get("chapterId"): chapter for chapter in chapter_docs}
        ordered = [chapter_map[chapter_id] for chapter_id in chapter_order if chapter_id in chapter_map]
        remaining = [
            chapter
            for chapter in chapter_docs
            if chapter.get("chapterId") not in set(chapter_order)
        ]
        chapter_docs = ordered + remaining

    return {
        "project": project,
        "currentProject": build_current_project_summary_from_loaded(project, chapter_docs),
        "history": build_history_payload(),
        "sessionRecovery": build_session_recovery_payload(),
        "assets": load_assets_document(),
        "characters": read_json(DATA_DIR / "characters.json"),
        "variables": read_json(DATA_DIR / "variables.json"),
        "chapters": chapter_docs,
    }


def load_project_bundle() -> dict:
    return PROJECT_BUNDLE_CACHE.get_or_build(
        build_project_bundle_cache_signature,
        build_project_bundle_uncached,
    )


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def touch_project(updated_entry_scene_id: str | None = None) -> None:
    project = read_json(PROJECT_PATH)
    project["updatedAt"] = now_iso()

    if updated_entry_scene_id and not project.get("entrySceneId"):
        project["entrySceneId"] = updated_entry_scene_id

    write_json(PROJECT_PATH, project)


def next_generated_id(existing_ids: set[str], prefix: str) -> str:
    number = 1

    while True:
        candidate = f"{prefix}_auto_{number:03d}"
        if candidate not in existing_ids:
            return candidate
        number += 1


def next_named_id(existing_ids: set[str], prefix: str, base_name: str) -> str:
    slug = make_slug(base_name)
    candidate = f"{prefix}_{slug}"
    suffix = 2

    while candidate in existing_ids:
        candidate = f"{prefix}_{slug}_{suffix:02d}"
        suffix += 1

    return candidate


def collect_existing_ids() -> tuple[set[str], set[str]]:
    chapter_ids: set[str] = set()
    scene_ids: set[str] = set()

    for chapter_path in list_chapter_files():
        chapter = read_json(chapter_path)
        chapter_ids.add(chapter.get("chapterId", ""))
        for scene in chapter.get("scenes", []):
            scene_ids.add(scene.get("id", ""))

    chapter_ids.discard("")
    scene_ids.discard("")
    return chapter_ids, scene_ids


def get_complete_chapter_order(project: dict | None = None) -> list[str]:
    current_project = project or read_json(PROJECT_PATH)
    saved_order = current_project.get("chapterOrder", [])
    existing_ids = []

    for chapter_path in list_chapter_files():
      chapter_id = read_json(chapter_path).get("chapterId")
      if chapter_id:
          existing_ids.append(chapter_id)

    return [chapter_id for chapter_id in saved_order if chapter_id in existing_ids] + [
        chapter_id for chapter_id in existing_ids if chapter_id not in saved_order
    ]


def build_starter_scene(scene_id: str, scene_name: str) -> dict:
    return {
        "id": scene_id,
        "name": scene_name,
        "notes": "",
        "status": "drafting",
        "priority": "normal",
        "blocks": [
            {
                "id": "block_001",
                "type": "narration",
                "text": "在这里开始写这一段剧情。",
            }
        ],
    }


CREATIVE_ASSISTANT_MAX_PROMPT_CHARS = 800
CREATIVE_ASSISTANT_OPENAI_ENDPOINT = "https://api.openai.com/v1/responses"
CREATIVE_ASSISTANT_DEFAULT_OPENAI_MODEL = "gpt-5.5"
CREATIVE_ASSISTANT_PROVIDER_CONFIGS = {
    "local": {
        "label": "本地模板助手",
        "default_model": "",
        "kind": "local",
        "endpoint": "",
    },
    "openai": {
        "label": "OpenAI",
        "default_model": CREATIVE_ASSISTANT_DEFAULT_OPENAI_MODEL,
        "kind": "openai_responses",
        "endpoint": CREATIVE_ASSISTANT_OPENAI_ENDPOINT,
    },
    "deepseek": {
        "label": "DeepSeek",
        "default_model": "deepseek-v4-flash",
        "kind": "openai_compatible_chat",
        "endpoint": "https://api.deepseek.com/chat/completions",
    },
    "qwen": {
        "label": "通义千问",
        "default_model": "qwen-plus",
        "kind": "openai_compatible_chat",
        "endpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    },
    "kimi": {
        "label": "Kimi",
        "default_model": "kimi-k2.6",
        "kind": "openai_compatible_chat",
        "endpoint": "https://api.moonshot.cn/v1/chat/completions",
    },
    "zhipu": {
        "label": "智谱 GLM",
        "default_model": "glm-5.1",
        "kind": "openai_compatible_chat",
        "endpoint": "https://open.bigmodel.cn/api/paas/v4/chat/completions",
    },
    "custom": {
        "label": "自定义兼容接口",
        "default_model": "gpt-compatible",
        "kind": "openai_compatible_chat",
        "endpoint": "",
    },
}
CREATIVE_ASSISTANT_PROVIDER_LABELS = {
    provider: config["label"] for provider, config in CREATIVE_ASSISTANT_PROVIDER_CONFIGS.items()
}
CREATIVE_ASSISTANT_MODE_LABELS = {
    "starter_demo": "试玩 Demo 生成",
    "script": "剧情片段生成",
    "advice": "创作诊断建议",
    "polish": "润色当前场景",
}


class CreativeAssistantModelError(RuntimeError):
    pass


def normalize_creative_assistant_provider(value: object) -> str:
    provider = str(value or "local").strip().lower()
    return provider if provider in CREATIVE_ASSISTANT_PROVIDER_LABELS else "local"


def get_creative_assistant_provider_config(provider: object) -> dict:
    return CREATIVE_ASSISTANT_PROVIDER_CONFIGS[normalize_creative_assistant_provider(provider)]


def normalize_creative_assistant_mode(value: object) -> str:
    mode = str(value or "starter_demo").strip()
    return mode if mode in CREATIVE_ASSISTANT_MODE_LABELS else "starter_demo"


def clean_creative_prompt(value: object) -> str:
    prompt = str(value or "").strip()
    prompt = re.sub(r"\s+", " ", prompt)
    return prompt[:CREATIVE_ASSISTANT_MAX_PROMPT_CHARS] or "雨夜校园里，一个秘密把两个人重新拉回彼此身边。"


def clean_creative_assistant_model(value: object, provider: object = "openai") -> str:
    default_model = str(get_creative_assistant_provider_config(provider).get("default_model") or CREATIVE_ASSISTANT_DEFAULT_OPENAI_MODEL)
    model = str(value or "").strip()
    if not model:
        return default_model
    if len(model) > 80 or not re.fullmatch(r"[A-Za-z0-9._:-]+", model):
        return default_model
    return model


def clean_creative_assistant_base_url(value: object) -> str:
    base_url = str(value or "").strip().rstrip("/")
    if not base_url or len(base_url) > 240:
        return ""
    parsed = urlparse(base_url)
    if parsed.scheme == "https" and parsed.netloc:
        return base_url
    if parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1"}:
        return base_url
    return ""


def build_creative_assistant_chat_endpoint(provider: str, payload: dict) -> str:
    provider_config = get_creative_assistant_provider_config(provider)
    if provider == "custom":
        endpoint = clean_creative_assistant_base_url(payload.get("baseUrl"))
        if not endpoint:
            raise CreativeAssistantModelError("自定义兼容接口需要填写有效 Base URL。")
    else:
        endpoint = str(provider_config.get("endpoint") or "").strip().rstrip("/")
    if not endpoint:
        raise CreativeAssistantModelError("当前模型服务没有配置可调用的接口地址。")
    if endpoint.endswith("/chat/completions"):
        return endpoint
    if endpoint.endswith("/v1") or endpoint.endswith("/compatible-mode/v1") or endpoint.endswith("/paas/v4"):
        return f"{endpoint}/chat/completions"
    return f"{endpoint}/chat/completions"


def pick_creative_assistant_flavor(prompt: str) -> dict:
    lowered = prompt.lower()
    has_any = lambda *words: any(word in prompt or word.lower() in lowered for word in words)
    setting = "雨夜校园" if has_any("雨", "校园", "教室", "学校") else "黄昏街角"
    if has_any("科幻", "AI", "机器人", "星", "未来"):
        setting = "近未来城市"
    if has_any("古风", "仙", "宫", "妖"):
        setting = "月色古城"
    mood = "悬疑又温柔" if has_any("悬疑", "秘密", "推理", "失踪") else "清甜但带一点遗憾"
    if has_any("恐怖", "惊悚", "诡异"):
        mood = "压抑、诡异、慢慢逼近真相"
    if has_any("恋爱", "告白", "心动", "青梅竹马"):
        mood = "暧昧、心动、带一点不敢说出口"
    conflict = "一个不能立刻说出口的秘密"
    if has_any("复仇", "背叛"):
        conflict = "一次被误解多年的背叛"
    elif has_any("循环", "轮回", "时间"):
        conflict = "只有主角记得的时间循环"
    elif has_any("失忆", "记忆"):
        conflict = "被刻意抹掉的一段记忆"
    return {"setting": setting, "mood": mood, "conflict": conflict}


def collect_creative_assistant_characters(bundle: dict) -> list[dict]:
    raw_characters = bundle.get("characters", {}).get("characters", [])
    if not isinstance(raw_characters, list):
        return []
    characters = []
    for character in raw_characters:
        if not isinstance(character, dict):
            continue
        character_id = str(character.get("id") or "").strip()
        if not character_id:
            continue
        characters.append(
            {
                "id": character_id,
                "name": str(character.get("displayName") or character.get("name") or character_id).strip()
                or character_id,
            }
        )
    return characters


def find_creative_assistant_scene(bundle: dict, scene_id: object) -> dict | None:
    target_scene_id = str(scene_id or "").strip()
    fallback_scene = None
    for chapter in bundle.get("chapters", []) or []:
        if not isinstance(chapter, dict):
            continue
        for scene in chapter.get("scenes", []) or []:
            if not isinstance(scene, dict):
                continue
            full_scene = {
                **scene,
                "chapterId": chapter.get("chapterId"),
                "chapterName": chapter.get("name") or chapter.get("chapterId"),
            }
            if fallback_scene is None:
                fallback_scene = full_scene
            if target_scene_id and str(scene.get("id") or "") == target_scene_id:
                return full_scene
    return fallback_scene


def build_creative_assistant_blocks(mode: str, prompt: str, scene: dict | None, characters: list[dict]) -> list[dict]:
    flavor = pick_creative_assistant_flavor(prompt)
    scene_name = str((scene or {}).get("name") or "这个场景").strip() or "这个场景"
    target_scene_id = str((scene or {}).get("id") or "").strip()
    speaker = characters[0] if characters else {"id": "", "name": "角色A"}
    partner = characters[1] if len(characters) > 1 else {"id": speaker["id"], "name": "另一个人"}
    speaker_id = speaker.get("id", "")
    partner_id = partner.get("id", "")
    speaker_name = speaker.get("name") or "角色A"
    partner_name = partner.get("name") or "另一个人"

    if mode == "advice":
        return []

    if mode == "polish":
        return [
            {
                "type": "narration",
                "text": f"{scene_name} 的空气被压得很低，像有什么话一直悬在两人之间。",
            },
            {
                "type": "dialogue",
                "speakerId": speaker_id,
                "expressionId": "",
                "text": f"我不是想逃避，只是还没想好该怎么把{flavor['conflict']}告诉你。",
            },
            {
                "type": "narration",
                "text": "这一句之后，场景可以留半拍沉默，再进入选项或下一段情绪推进。",
            },
        ]

    return [
        {
            "type": "narration",
            "text": f"{flavor['setting']}里，{scene_name} 像被一层薄薄的光罩住。{flavor['conflict']}，正悄悄改变今晚的走向。",
        },
        {
            "type": "dialogue",
            "speakerId": speaker_id,
            "expressionId": "",
            "text": f"你有没有觉得，今晚的气氛有点不一样？",
        },
        {
            "type": "dialogue",
            "speakerId": partner_id,
            "expressionId": "",
            "text": f"如果我说，我其实一直在等你问这句话呢？",
        },
        {
            "type": "narration",
            "text": f"{speaker_name} 看向 {partner_name}，那些没来得及说出口的心情，终于在这阵{flavor['mood']}的沉默里浮了上来。",
        },
        {
            "type": "choice",
            "options": [
                {"text": "追问那个秘密", "gotoSceneId": target_scene_id, "effects": []},
                {"text": "先假装什么都没有发生", "gotoSceneId": target_scene_id, "effects": []},
            ],
        },
    ]


def build_local_creative_assistant_result(payload: dict | None) -> dict:
    payload = payload if isinstance(payload, dict) else {}
    mode = normalize_creative_assistant_mode(payload.get("mode"))
    prompt = clean_creative_prompt(payload.get("prompt"))
    bundle = load_project_bundle()
    project = bundle.get("project", {}) if isinstance(bundle.get("project"), dict) else {}
    scene = find_creative_assistant_scene(bundle, payload.get("sceneId"))
    characters = collect_creative_assistant_characters(bundle)
    flavor = pick_creative_assistant_flavor(prompt)
    blocks = build_creative_assistant_blocks(mode, prompt, scene, characters)
    block_count = len(blocks)
    scene_name = str((scene or {}).get("name") or "当前场景")
    title = {
        "starter_demo": "已生成一段可试玩剧情骨架",
        "script": "已生成一段可插入剧情",
        "advice": "已生成创作诊断建议",
        "polish": "已生成当前场景润色片段",
    }.get(mode, "已生成创作建议")
    guidance = [
        f"核心氛围可以先定为：{flavor['mood']}。",
        f"当前最适合推动的矛盾是：{flavor['conflict']}。",
        "新手建议：先做 3-5 分钟可通关 Demo，再扩展分支和素材精修。",
    ]
    if scene and not (scene.get("blocks") or []):
        guidance.append("当前场景还是空的，可以直接插入这段作为第一版开场。")
    elif scene:
        guidance.append("建议插入到当前选中卡片后面，再用预览检查节奏。")
    return {
        "mode": mode,
        "modeLabel": CREATIVE_ASSISTANT_MODE_LABELS[mode],
        "title": title,
        "summary": f"基于「{prompt}」为项目「{project.get('title') or '未命名项目'}」和场景「{scene_name}」生成。",
        "guidance": guidance,
        "blocks": blocks,
        "insertable": block_count > 0,
        "blockCount": block_count,
        "assetPrompts": [
            f"{flavor['setting']}，{flavor['mood']}，适合视觉小说背景概念图",
            f"{flavor['conflict']}，角色半身立绘，情绪克制，二次元视觉小说风格",
        ],
        "provider": {
            "mode": "local",
            "label": CREATIVE_ASSISTANT_PROVIDER_LABELS["local"],
            "status": "ready",
            "model": "",
            "fallback": False,
        },
        "privacy": {
            "mode": "local_template",
            "sentToExternalService": False,
            "message": "当前为本地模板助手：不会上传项目内容，也不会产生 API 调用费用。",
        },
    }


def build_creative_assistant_model_context(payload: dict, prompt: str) -> dict:
    bundle = load_project_bundle()
    project = bundle.get("project", {}) if isinstance(bundle.get("project"), dict) else {}
    scene = find_creative_assistant_scene(bundle, payload.get("sceneId"))
    characters = collect_creative_assistant_characters(bundle)
    current_blocks = []
    if scene:
        for index, block in enumerate(scene.get("blocks", []) or [], start=1):
            if not isinstance(block, dict):
                continue
            block_type = str(block.get("type") or "")
            if block_type not in {"dialogue", "narration", "choice"}:
                continue
            current_blocks.append(
                {
                    "index": index,
                    "type": block_type,
                    "text": str(block.get("text") or "")[:180],
                    "options": [
                        str(option.get("text") or "")[:80]
                        for option in block.get("options", []) or []
                        if isinstance(option, dict)
                    ][:4],
                }
            )
            if len(current_blocks) >= 10:
                break
    return {
        "projectTitle": str(project.get("title") or "未命名项目"),
        "mode": normalize_creative_assistant_mode(payload.get("mode")),
        "modeLabel": CREATIVE_ASSISTANT_MODE_LABELS[normalize_creative_assistant_mode(payload.get("mode"))],
        "prompt": prompt,
        "scene": {
            "id": str((scene or {}).get("id") or ""),
            "name": str((scene or {}).get("name") or "当前场景"),
            "notes": str((scene or {}).get("notes") or "")[:240],
        },
        "characters": characters[:8],
        "currentBlocks": current_blocks,
    }


def build_creative_assistant_response_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "title": {"type": "string"},
            "summary": {"type": "string"},
            "guidance": {"type": "array", "items": {"type": "string"}},
            "assetPrompts": {"type": "array", "items": {"type": "string"}},
            "blocks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": {
                        "type": {"type": "string", "enum": ["narration", "dialogue", "choice"]},
                        "speakerId": {"type": "string"},
                        "expressionId": {"type": "string"},
                        "text": {"type": "string"},
                        "options": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": True,
                                "properties": {
                                    "text": {"type": "string"},
                                    "gotoSceneId": {"type": "string"},
                                },
                            },
                        },
                    },
                },
            },
        },
        "required": ["title", "summary", "guidance", "assetPrompts", "blocks"],
    }


def extract_openai_response_text(response_payload: dict) -> str:
    direct_text = response_payload.get("output_text")
    if isinstance(direct_text, str) and direct_text.strip():
        return direct_text.strip()
    for output_item in response_payload.get("output", []) or []:
        if not isinstance(output_item, dict):
            continue
        for content_item in output_item.get("content", []) or []:
            if not isinstance(content_item, dict):
                continue
            text_value = content_item.get("text")
            if isinstance(text_value, str) and text_value.strip():
                return text_value.strip()
    raise CreativeAssistantModelError("模型没有返回可读取的文本。")


def extract_chat_completion_response_text(response_payload: dict) -> str:
    choices = response_payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise CreativeAssistantModelError("模型没有返回可读取的 choices。")
    message = choices[0].get("message") if isinstance(choices[0], dict) else {}
    content = message.get("content") if isinstance(message, dict) else ""
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or ""))
            else:
                parts.append(str(item))
        content = "".join(parts)
    if isinstance(content, str) and content.strip():
        return content.strip()
    raise CreativeAssistantModelError("模型没有返回可读取的文本。")


def parse_creative_assistant_json_text(response_text: str) -> dict:
    text = str(response_text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        raise CreativeAssistantModelError("模型返回的内容不是有效 JSON。") from error


def sanitize_model_creative_blocks(raw_blocks: object, fallback_scene_id: str) -> list[dict]:
    if not isinstance(raw_blocks, list):
        return []
    blocks: list[dict] = []
    for raw_block in raw_blocks[:12]:
        if not isinstance(raw_block, dict):
            continue
        block_type = str(raw_block.get("type") or "narration").strip()
        if block_type not in {"dialogue", "narration", "choice"}:
            block_type = "narration"
        if block_type == "choice":
            raw_options = raw_block.get("options") if isinstance(raw_block.get("options"), list) else []
            options = []
            for index, option in enumerate(raw_options[:4], start=1):
                if not isinstance(option, dict):
                    continue
                option_text = str(option.get("text") or f"选项 {index}").strip()[:120] or f"选项 {index}"
                options.append(
                    {
                        "text": option_text,
                        "gotoSceneId": str(option.get("gotoSceneId") or fallback_scene_id),
                        "effects": [],
                    }
                )
            if len(options) < 2:
                options = [
                    {"text": "继续追问", "gotoSceneId": fallback_scene_id, "effects": []},
                    {"text": "暂时沉默", "gotoSceneId": fallback_scene_id, "effects": []},
                ]
            blocks.append({"type": "choice", "options": options})
            continue
        text = str(raw_block.get("text") or "").strip()[:600]
        if not text:
            continue
        block = {"type": block_type, "text": text}
        if block_type == "dialogue":
            block["speakerId"] = str(raw_block.get("speakerId") or "")
            block["expressionId"] = str(raw_block.get("expressionId") or "")
        blocks.append(block)
    return blocks


def sanitize_model_creative_result(raw_result: object, local_result: dict, model: str, provider: object = "openai") -> dict:
    if not isinstance(raw_result, dict):
        raise CreativeAssistantModelError("模型返回的 JSON 不是对象。")
    provider = normalize_creative_assistant_provider(provider)
    provider_label = CREATIVE_ASSISTANT_PROVIDER_LABELS[provider]
    fallback_scene_id = ""
    for block in local_result.get("blocks", []) or []:
        if isinstance(block, dict) and block.get("type") == "choice":
            first_option = (block.get("options") or [{}])[0]
            fallback_scene_id = str(first_option.get("gotoSceneId") or "")
            break
    blocks = sanitize_model_creative_blocks(raw_result.get("blocks"), fallback_scene_id)
    guidance = [str(item).strip()[:260] for item in raw_result.get("guidance", []) or [] if str(item).strip()][:6]
    asset_prompts = [str(item).strip()[:260] for item in raw_result.get("assetPrompts", []) or [] if str(item).strip()][:4]
    result = {
        **local_result,
        "title": str(raw_result.get("title") or local_result.get("title") or "模型已生成创作建议").strip()[:120],
        "summary": str(raw_result.get("summary") or local_result.get("summary") or "").strip()[:500],
        "guidance": guidance or local_result.get("guidance", []),
        "assetPrompts": asset_prompts or local_result.get("assetPrompts", []),
        "blocks": blocks,
        "insertable": len(blocks) > 0,
        "blockCount": len(blocks),
        "provider": {
            "mode": provider,
            "label": provider_label,
            "status": "model",
            "model": model,
            "fallback": False,
        },
        "privacy": {
            "mode": f"{provider}_byo_key",
            "sentToExternalService": True,
            "message": f"已使用你提供的 {provider_label} API Key 调用真模型；Key 不会写入项目文件。",
        },
    }
    if not result["summary"]:
        result["summary"] = local_result.get("summary", "")
    return result


def call_openai_creative_assistant(payload: dict, local_result: dict, api_key: str, model: str) -> dict:
    prompt = clean_creative_prompt(payload.get("prompt"))
    context = build_creative_assistant_model_context(payload, prompt)
    request_payload = {
        "model": model,
        "instructions": (
            "你是 Canvasia Engine 内置的视觉小说创作助手。"
            "请根据用户主题和当前项目上下文，生成适合 galgame/视觉小说编辑器直接插入的内容。"
            "只生成原创内容；不要输出 Markdown；不要声称已经生成图片或音频。"
            "blocks 只能使用 narration、dialogue、choice 三类；dialogue 优先使用给定 characters 的 id。"
            "如果 mode 是 advice，可以让 blocks 为空；其他模式尽量提供 3 到 6 张可插入卡片。"
        ),
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": json.dumps(context, ensure_ascii=False, indent=2),
                    }
                ],
            }
        ],
        "max_output_tokens": 1800,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "canvasia_creative_assistant_result",
                "schema": build_creative_assistant_response_schema(),
            }
        },
    }
    request = Request(
        CREATIVE_ASSISTANT_OPENAI_ENDPOINT,
        data=json.dumps(request_payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        error_body = ""
        try:
            error_body = error.read().decode("utf-8")[:500]
        except Exception:
            error_body = ""
        raise CreativeAssistantModelError(f"OpenAI 返回错误 {error.code}：{error_body or error.reason}") from error
    except URLError as error:
        raise CreativeAssistantModelError(f"连接 OpenAI 失败：{error.reason}") from error
    except TimeoutError as error:
        raise CreativeAssistantModelError("连接 OpenAI 超时。") from error
    except Exception as error:
        raise CreativeAssistantModelError(f"调用 OpenAI 失败：{error}") from error
    response_text = extract_openai_response_text(response_data)
    raw_result = parse_creative_assistant_json_text(response_text)
    return sanitize_model_creative_result(raw_result, local_result, model, "openai")


def call_compatible_creative_assistant(payload: dict, local_result: dict, api_key: str, model: str, provider: str) -> dict:
    prompt = clean_creative_prompt(payload.get("prompt"))
    context = build_creative_assistant_model_context(payload, prompt)
    provider_label = CREATIVE_ASSISTANT_PROVIDER_LABELS[provider]
    endpoint = build_creative_assistant_chat_endpoint(provider, payload)
    request_payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是 Canvasia Engine 内置的视觉小说创作助手。"
                    "请根据用户主题和当前项目上下文，生成适合 galgame/视觉小说编辑器直接插入的内容。"
                    "只生成原创内容；不要声称已经生成图片或音频。"
                    "只输出 JSON 对象，不要输出 Markdown 代码块。"
                    "JSON 必须包含 title、summary、guidance、assetPrompts、blocks。"
                    "blocks 只能使用 narration、dialogue、choice 三类；dialogue 优先使用给定 characters 的 id。"
                    "如果 mode 是 advice，可以让 blocks 为空；其他模式尽量提供 3 到 6 张可插入卡片。"
                ),
            },
            {
                "role": "user",
                "content": json.dumps(context, ensure_ascii=False, indent=2),
            },
        ],
        "temperature": 0.75,
        "max_tokens": 1800,
    }
    request = Request(
        endpoint,
        data=json.dumps(request_payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        error_body = ""
        try:
            error_body = error.read().decode("utf-8")[:500]
        except Exception:
            error_body = ""
        raise CreativeAssistantModelError(f"{provider_label} 返回错误 {error.code}：{error_body or error.reason}") from error
    except URLError as error:
        raise CreativeAssistantModelError(f"连接 {provider_label} 失败：{error.reason}") from error
    except TimeoutError as error:
        raise CreativeAssistantModelError(f"连接 {provider_label} 超时。") from error
    except Exception as error:
        raise CreativeAssistantModelError(f"调用 {provider_label} 失败：{error}") from error
    response_text = extract_chat_completion_response_text(response_data)
    raw_result = parse_creative_assistant_json_text(response_text)
    return sanitize_model_creative_result(raw_result, local_result, model, provider)


def build_creative_assistant_result(payload: dict | None) -> dict:
    payload = payload if isinstance(payload, dict) else {}
    local_result = build_local_creative_assistant_result(payload)
    provider = normalize_creative_assistant_provider(payload.get("provider"))
    if provider == "local":
        return local_result
    provider_label = CREATIVE_ASSISTANT_PROVIDER_LABELS[provider]
    api_key = str(payload.get("apiKey") or "").strip()
    model = clean_creative_assistant_model(payload.get("model"), provider)
    if not api_key:
        return {
            **local_result,
            "provider": {
                "mode": provider,
                "label": provider_label,
                "status": "missing_key",
                "model": model,
                "fallback": True,
            },
            "privacy": {
                "mode": "local_fallback_missing_key",
                "sentToExternalService": False,
                "message": "未填写 API Key，已自动使用本地模板助手；不会上传项目内容。",
            },
            "fallbackReason": f"未填写 {provider_label} API Key。",
        }
    try:
        if provider == "openai":
            return call_openai_creative_assistant(payload, local_result, api_key, model)
        return call_compatible_creative_assistant(payload, local_result, api_key, model, provider)
    except CreativeAssistantModelError as error:
        return {
            **local_result,
            "provider": {
                "mode": provider,
                "label": provider_label,
                "status": "fallback",
                "model": model,
                "fallback": True,
            },
            "privacy": {
                "mode": "local_fallback_after_model_error",
                "sentToExternalService": True,
                "message": "真模型调用失败，已自动回落到本地模板助手；API Key 不会写入项目文件。",
            },
            "fallbackReason": str(error),
        }


def save_scene(chapter_id: str, scene_id: str, scene_payload: dict) -> None:
    if not isinstance(scene_payload, dict):
        raise ValueError("传进来的场景内容不是有效对象。")

    if scene_payload.get("id") != scene_id:
        raise ValueError("要保存的场景 ID 和请求里的 sceneId 不一致。")

    for chapter_path in list_chapter_files():
        chapter = read_json(chapter_path)

        if chapter.get("chapterId") != chapter_id:
            continue

        scenes = chapter.get("scenes", [])

        for index, scene in enumerate(scenes):
            if scene.get("id") == scene_id:
                scenes[index] = scene_payload
                scene_order = chapter.setdefault("sceneOrder", [])
                if scene_id not in scene_order:
                    scene_order.append(scene_id)
                write_json(chapter_path, chapter)
                touch_project()
                return

        raise ValueError("找到了章节，但里面没有这个场景。")

    raise ValueError("没有找到对应的章节文件。")


def get_patch_text(value: object, limit: int = 8000) -> str:
    return str(value or "").strip()[:limit]


def get_patch_language(value: object) -> str:
    return normalize_language_code(value, "")


def ensure_translation_map(target: dict, key: str) -> dict:
    map_key = f"{key}Translations"
    translations = target.get(map_key)
    if not isinstance(translations, dict):
        translations = {}
        target[map_key] = translations
    return translations


def build_localization_chapter_context() -> tuple[list[tuple[Path, dict]], dict[str, dict], dict[str, tuple[Path, dict, dict]]]:
    chapter_entries = [(path, read_json(path)) for path in list_chapter_files()]
    chapter_by_id = {
        str(chapter.get("chapterId") or "").strip(): {"path": path, "chapter": chapter}
        for path, chapter in chapter_entries
        if str(chapter.get("chapterId") or "").strip()
    }
    scene_lookup: dict[str, tuple[Path, dict, dict]] = {}
    for path, chapter in chapter_entries:
        for scene in chapter.get("scenes", []) if isinstance(chapter.get("scenes"), list) else []:
            scene_id = str(scene.get("id") or "").strip()
            if scene_id:
                scene_lookup[scene_id] = (path, chapter, scene)
    return chapter_entries, chapter_by_id, scene_lookup


def find_localization_scene_context(
    patch: dict,
    chapter_entries: list[tuple[Path, dict]],
    chapter_by_id: dict[str, dict],
    scene_lookup: dict[str, tuple[Path, dict, dict]],
) -> tuple[Path, dict, dict] | None:
    scene_id = str(patch.get("sceneId") or patch.get("targetId") or "").strip()
    chapter_id = str(patch.get("chapterId") or "").strip()
    if scene_id and chapter_id:
        chapter_entry = chapter_by_id.get(chapter_id)
        chapter = chapter_entry.get("chapter") if chapter_entry else None
        if chapter:
            for scene in chapter.get("scenes", []) if isinstance(chapter.get("scenes"), list) else []:
                if str(scene.get("id") or "").strip() == scene_id:
                    return (chapter_entry["path"], chapter, scene)
    if scene_id in scene_lookup:
        return scene_lookup[scene_id]
    for path, chapter in chapter_entries:
        for scene in chapter.get("scenes", []) if isinstance(chapter.get("scenes"), list) else []:
            if str(scene.get("id") or "").strip() == scene_id:
                return (path, chapter, scene)
    return None


def add_localization_skip(skipped: list[dict], patch: object, reason: str, index: int) -> None:
    source = patch if isinstance(patch, dict) else {}
    skipped.append(
        {
            "index": index,
            "rowNumber": source.get("rowNumber"),
            "kind": source.get("kind"),
            "targetId": source.get("targetId"),
            "language": source.get("language"),
            "reason": reason,
        }
    )


def apply_localization_translation(
    target: dict,
    key: str,
    language: str,
    text: str,
    skipped: list[dict],
    patch: dict,
    index: int,
) -> bool:
    translations = ensure_translation_map(target, key)
    if str(translations.get(language) or "").strip() == text:
        add_localization_skip(skipped, patch, "译文与项目内现有内容相同。", index)
        return False
    translations[language] = text
    return True


def import_localization_patches(patches: object) -> dict:
    if not isinstance(patches, list):
        raise ValueError("翻译导入内容必须是补丁列表。")
    if len(patches) > 2000:
        raise ValueError("一次最多导入 2000 条翻译补丁，请分批处理。")

    characters_path = DATA_DIR / "characters.json"
    characters_doc = normalize_characters_document(read_json(characters_path))
    characters = characters_doc.setdefault("characters", [])
    characters_by_id = {str(character.get("id") or "").strip(): character for character in characters}
    chapter_entries, chapter_by_id, scene_lookup = build_localization_chapter_context()
    dirty_chapter_paths: set[Path] = set()
    dirty_characters = False
    applied: list[dict] = []
    skipped: list[dict] = []

    for index, raw_patch in enumerate(patches, start=1):
        if not isinstance(raw_patch, dict):
            add_localization_skip(skipped, raw_patch, "补丁不是有效对象。", index)
            continue

        kind = str(raw_patch.get("kind") or "").strip()
        target_id = str(raw_patch.get("targetId") or "").strip()
        key = str(raw_patch.get("key") or "").strip()
        language = get_patch_language(raw_patch.get("language"))
        text = get_patch_text(raw_patch.get("text"))

        if not kind or not target_id or not key:
            add_localization_skip(skipped, raw_patch, "缺少类型、目标ID或字段键。", index)
            continue
        if not language:
            add_localization_skip(skipped, raw_patch, "语言代码为空。", index)
            continue
        if not text:
            add_localization_skip(skipped, raw_patch, "译文为空。", index)
            continue

        if kind == "character":
            if key not in {"displayName", "name"}:
                add_localization_skip(skipped, raw_patch, "角色翻译只支持 displayName 或 name 字段。", index)
                continue
            character = characters_by_id.get(target_id)
            if not character:
                add_localization_skip(skipped, raw_patch, "找不到目标角色。", index)
                continue
            if apply_localization_translation(character, key, language, text, skipped, raw_patch, index):
                dirty_characters = True
                applied.append({"kind": kind, "targetId": target_id, "key": key, "language": language})
            continue

        if kind == "chapter":
            if key != "name":
                add_localization_skip(skipped, raw_patch, "章节翻译只支持 name 字段。", index)
                continue
            chapter_entry = chapter_by_id.get(target_id)
            if not chapter_entry:
                add_localization_skip(skipped, raw_patch, "找不到目标章节。", index)
                continue
            chapter = chapter_entry["chapter"]
            if apply_localization_translation(chapter, key, language, text, skipped, raw_patch, index):
                dirty_chapter_paths.add(chapter_entry["path"])
                applied.append({"kind": kind, "targetId": target_id, "key": key, "language": language})
            continue

        scene_context = find_localization_scene_context(raw_patch, chapter_entries, chapter_by_id, scene_lookup)
        if not scene_context:
            add_localization_skip(skipped, raw_patch, "找不到目标场景。", index)
            continue
        chapter_path, chapter, scene = scene_context

        if kind == "scene":
            if key != "name":
                add_localization_skip(skipped, raw_patch, "场景翻译只支持 name 字段。", index)
                continue
            if apply_localization_translation(scene, key, language, text, skipped, raw_patch, index):
                dirty_chapter_paths.add(chapter_path)
                applied.append({"kind": kind, "targetId": str(scene.get("id") or target_id), "key": key, "language": language})
            continue

        blocks = scene.get("blocks") if isinstance(scene.get("blocks"), list) else []
        block = next((candidate for candidate in blocks if str(candidate.get("id") or "").strip() == target_id), None)
        if not block:
            add_localization_skip(skipped, raw_patch, "找不到目标卡片。", index)
            continue

        if kind == "block":
            if key not in {"text", "title"}:
                add_localization_skip(skipped, raw_patch, "卡片翻译只支持 text 或 title 字段。", index)
                continue
            if apply_localization_translation(block, key, language, text, skipped, raw_patch, index):
                dirty_chapter_paths.add(chapter_path)
                applied.append({"kind": kind, "targetId": target_id, "key": key, "language": language})
            continue

        if kind == "choice_option":
            if key != "text":
                add_localization_skip(skipped, raw_patch, "选项翻译只支持 text 字段。", index)
                continue
            option_index = raw_patch.get("optionIndex")
            if not isinstance(option_index, int):
                try:
                    option_index = int(option_index)
                except (TypeError, ValueError):
                    option_index = -1
            options = block.get("options") if isinstance(block.get("options"), list) else []
            if option_index < 0 or option_index >= len(options):
                add_localization_skip(skipped, raw_patch, "找不到目标选项。", index)
                continue
            if apply_localization_translation(options[option_index], key, language, text, skipped, raw_patch, index):
                dirty_chapter_paths.add(chapter_path)
                applied.append({"kind": kind, "targetId": target_id, "key": key, "language": language})
            continue

        add_localization_skip(skipped, raw_patch, "不支持的翻译补丁类型。", index)

    if dirty_characters:
        write_json(characters_path, normalize_characters_document(characters_doc))
    for chapter_path, chapter in chapter_entries:
        if chapter_path in dirty_chapter_paths:
            write_json(chapter_path, normalize_chapter_document(chapter, chapter_path.stem))

    changed = dirty_characters or bool(dirty_chapter_paths)
    if changed:
        touch_project()

    return {
        "changed": changed,
        "applied": applied,
        "skipped": skipped,
        "summary": {
            "patchCount": len(patches),
            "appliedCount": len(applied),
            "skippedCount": len(skipped),
            "characterChanged": dirty_characters,
            "changedChapterFileCount": len(dirty_chapter_paths),
            "languageCount": len({item["language"] for item in applied}),
        },
    }


def save_project_settings(
    *,
    resolution: dict | None = None,
    release_version: str | None = None,
    language: str | None = None,
    supported_languages: list | None = None,
    editor_mode: str | None = None,
    runtime_settings: dict | None = None,
    dialog_box_config: dict | None = None,
    game_ui_config: dict | None = None,
    particle_custom_presets: list | None = None,
    variables: object | None = None,
) -> dict:
    project = read_json(PROJECT_PATH)
    project["formatVersion"] = PROJECT_FORMAT_VERSION

    if resolution is not None:
        width = int(resolution.get("width", 0))
        height = int(resolution.get("height", 0))

        if (width, height) not in SUPPORTED_RESOLUTIONS:
            raise ValueError("当前原型暂时只支持 1280×720 和 1920×1080。")

        project["resolution"] = {
            "width": width,
            "height": height,
        }

    if release_version is not None:
        clean_release_version = str(release_version).strip()
        if clean_release_version:
            if len(clean_release_version) > 40:
                raise ValueError("发布版本不能超过 40 个字符。")
            if not re.fullmatch(r"[0-9A-Za-z][0-9A-Za-z._-]{0,39}", clean_release_version):
                raise ValueError("发布版本只建议使用字母、数字、点、下划线或短横线。")
            project["releaseVersion"] = clean_release_version
        else:
            project.pop("releaseVersion", None)

    if language is not None:
        project["language"] = normalize_language_code(language, DEFAULT_PROJECT_LANGUAGE)

    if supported_languages is not None or language is not None:
        project["supportedLanguages"] = normalize_supported_languages(
            supported_languages if supported_languages is not None else project.get("supportedLanguages"),
            normalize_language_code(project.get("language"), DEFAULT_PROJECT_LANGUAGE),
        )

    if editor_mode is not None:
        normalized_editor_mode = str(editor_mode).strip().lower() or DEFAULT_EDITOR_MODE
        if normalized_editor_mode not in {"beginner", "advanced"}:
            raise ValueError("编辑模式只能是 beginner 或 advanced。")
        project["editorMode"] = normalized_editor_mode

    if runtime_settings is not None:
        current_runtime_settings = project.get("runtimeSettings") if isinstance(project.get("runtimeSettings"), dict) else {}
        incoming_runtime_settings = runtime_settings if isinstance(runtime_settings, dict) else {}
        project["runtimeSettings"] = sanitize_project_runtime_settings(
            {
                **current_runtime_settings,
                **incoming_runtime_settings,
            }
        )

    if dialog_box_config is not None:
        project["dialogBoxConfig"] = sanitize_dialog_box_config(dialog_box_config)

    if game_ui_config is not None:
        project["gameUiConfig"] = sanitize_game_ui_config(game_ui_config)

    if particle_custom_presets is not None:
        cleaned_particle_presets = sanitize_particle_custom_presets(particle_custom_presets)
        if cleaned_particle_presets:
            project["particleCustomPresets"] = cleaned_particle_presets
        else:
            project.pop("particleCustomPresets", None)

    if variables is not None:
        write_json(DATA_DIR / "variables.json", normalize_variables_document(variables))

    project["updatedAt"] = now_iso()
    write_json(PROJECT_PATH, project)
    return {"project": project}


PROJECT_DOCTOR_REPAIR_CODE_ORDER = (
    "entry_scene",
    "chapter_order",
    "scene_order",
)

PROJECT_DOCTOR_REPAIR_CODES = set(PROJECT_DOCTOR_REPAIR_CODE_ORDER)


def split_project_doctor_repair_code_tokens(value: object = None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw_items = re.split(r"[\s,]+", value)
    elif isinstance(value, list):
        raw_items = value
    else:
        return []
    return [str(item or "").strip().lower() for item in raw_items if str(item or "").strip()]


def normalize_project_doctor_repair_codes(value: object = None) -> set[str]:
    if value is None:
        return set(PROJECT_DOCTOR_REPAIR_CODES)
    return {code for code in split_project_doctor_repair_code_tokens(value) if code in PROJECT_DOCTOR_REPAIR_CODES}


def get_unknown_project_doctor_repair_codes(value: object = None) -> list[str]:
    if value is None:
        return []
    unknown_codes: list[str] = []
    for code in split_project_doctor_repair_code_tokens(value):
        if code not in PROJECT_DOCTOR_REPAIR_CODES and code not in unknown_codes:
            unknown_codes.append(code)
    return unknown_codes


def sort_project_doctor_repair_codes(codes: set[str]) -> list[str]:
    return [code for code in PROJECT_DOCTOR_REPAIR_CODE_ORDER if code in codes]


def dedupe_project_doctor_order(items: list[str]) -> tuple[list[str], int]:
    seen: set[str] = set()
    deduped: list[str] = []
    duplicate_count = 0
    for item in items:
        if item in seen:
            duplicate_count += 1
            continue
        seen.add(item)
        deduped.append(item)
    return deduped, duplicate_count


def normalize_project_doctor_order_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := str(item or "").strip())]


def get_first_ordered_scene_id(project: dict, chapters: list[dict]) -> str:
    chapter_by_id = {chapter.get("chapterId"): chapter for chapter in chapters if chapter.get("chapterId")}
    ordered_chapter_ids = [
        chapter_id
        for chapter_id in normalize_text_list(project.get("chapterOrder"))
        if chapter_id in chapter_by_id
    ]
    ordered_chapter_ids.extend(
        chapter.get("chapterId")
        for chapter in chapters
        if chapter.get("chapterId") and chapter.get("chapterId") not in ordered_chapter_ids
    )

    for chapter_id in ordered_chapter_ids:
        chapter = chapter_by_id.get(chapter_id)
        if not chapter:
            continue
        scenes = [scene for scene in chapter.get("scenes", []) if isinstance(scene, dict)]
        scene_by_id = {scene.get("id"): scene for scene in scenes if scene.get("id")}
        scene_order = [
            scene_id
            for scene_id in normalize_text_list(chapter.get("sceneOrder"))
            if scene_id in scene_by_id
        ]
        scene_order.extend(scene.get("id") for scene in scenes if scene.get("id") not in scene_order)
        if scene_order:
            return str(scene_order[0])
    return ""


def repair_project_doctor(repair_codes: object = None, dry_run: bool = False) -> dict:
    selected_codes = normalize_project_doctor_repair_codes(repair_codes)
    ignored_codes = get_unknown_project_doctor_repair_codes(repair_codes)
    project = read_json(PROJECT_PATH)
    chapter_entries = [(path, read_json(path)) for path in list_chapter_files()]
    chapters = [chapter for _, chapter in chapter_entries]
    repairs: list[dict] = []
    skipped: list[dict] = []
    project_changed = False

    if "chapter_order" in selected_codes:
        chapter_ids = [
            str(chapter.get("chapterId") or "").strip()
            for chapter in chapters
            if str(chapter.get("chapterId") or "").strip()
        ]
        chapter_id_set = set(chapter_ids)
        current_order = normalize_project_doctor_order_items(project.get("chapterOrder"))
        valid_order, duplicate_count = dedupe_project_doctor_order(
            [chapter_id for chapter_id in current_order if chapter_id in chapter_id_set]
        )
        valid_order_set = set(valid_order)
        next_order = [*valid_order, *[chapter_id for chapter_id in chapter_ids if chapter_id not in valid_order_set]]
        removed_count = len([chapter_id for chapter_id in current_order if chapter_id and chapter_id not in chapter_id_set])
        appended_count = len([chapter_id for chapter_id in chapter_ids if chapter_id not in valid_order_set])
        if next_order != current_order:
            project["chapterOrder"] = next_order
            project_changed = True
            repairs.append(
                {
                    "code": "chapter_order",
                    "title": "已整理章节顺序",
                    "detail": f"移除无效章节引用 {removed_count} 个，移除重复章节引用 {duplicate_count} 个，补回未进入排序的章节 {appended_count} 个。",
                }
            )
        else:
            skipped.append({"code": "chapter_order", "title": "章节顺序无需修复"})

    if "scene_order" in selected_codes:
        for chapter_file, chapter in chapter_entries:
            scenes = [scene for scene in chapter.get("scenes", []) if isinstance(scene, dict)]
            scene_ids = [str(scene.get("id") or "").strip() for scene in scenes if str(scene.get("id") or "").strip()]
            scene_id_set = set(scene_ids)
            current_order = normalize_project_doctor_order_items(chapter.get("sceneOrder"))
            valid_order, duplicate_count = dedupe_project_doctor_order(
                [scene_id for scene_id in current_order if scene_id in scene_id_set]
            )
            valid_order_set = set(valid_order)
            missing_order = [scene_id for scene_id in scene_ids if scene_id not in valid_order_set]
            next_order = [*valid_order, *missing_order]
            removed_count = len([scene_id for scene_id in current_order if scene_id and scene_id not in scene_id_set])
            if next_order != current_order:
                chapter["sceneOrder"] = next_order
                chapter["updatedAt"] = now_iso()
                if not dry_run:
                    write_json(chapter_file, chapter)
                repairs.append(
                    {
                        "code": "scene_order",
                        "title": f"已整理场景顺序：{chapter.get('name') or chapter.get('chapterId') or chapter_file.stem}",
                        "detail": f"移除无效场景引用 {removed_count} 个，移除重复场景引用 {duplicate_count} 个，补回未进入排序的场景 {len(missing_order)} 个。",
                    }
                )
            else:
                skipped.append(
                    {
                        "code": "scene_order",
                        "title": f"场景顺序无需修复：{chapter.get('name') or chapter.get('chapterId') or chapter_file.stem}",
                    }
                )

    all_scene_ids = {
        str(scene.get("id") or "").strip()
        for chapter in chapters
        for scene in chapter.get("scenes", [])
        if isinstance(scene, dict) and str(scene.get("id") or "").strip()
    }
    if "entry_scene" in selected_codes:
        entry_scene_id = str(project.get("entrySceneId") or "").strip()
        if entry_scene_id not in all_scene_ids:
            fallback_scene_id = get_first_ordered_scene_id(project, chapters)
            if fallback_scene_id:
                project["entrySceneId"] = fallback_scene_id
                project_changed = True
                repairs.append(
                    {
                        "code": "entry_scene",
                        "title": "已修复入口场景",
                        "detail": f"入口场景已改为当前项目里的第一个可用场景：{fallback_scene_id}。",
                    }
                )
            else:
                skipped.append(
                    {
                        "code": "entry_scene",
                        "title": "入口场景无法自动修复",
                        "detail": "项目里还没有可用场景，请先新建章节和场景。",
                    }
                )
        else:
            skipped.append({"code": "entry_scene", "title": "入口场景无需修复"})

    if project_changed and not dry_run:
        project["updatedAt"] = now_iso()
        write_json(PROJECT_PATH, project)

    return {
        "changed": bool(repairs) and not dry_run,
        "wouldChange": bool(repairs),
        "dryRun": bool(dry_run),
        "requestedCodes": sort_project_doctor_repair_codes(selected_codes),
        "ignoredCodes": ignored_codes,
        "repairs": repairs,
        "skipped": skipped,
        "project": project,
    }


def validate_variable_id(value: object) -> str:
    variable_id = str(value or "").strip()
    if not variable_id:
        raise ValueError("变量 ID 不能为空。")
    if not VARIABLE_ID_PATTERN.fullmatch(variable_id):
        raise ValueError("变量 ID 只能使用字母、数字、下划线、短横线或中文，并且不能超过 64 个字符。")
    return variable_id


def replace_variable_reference_in_block(block: dict, old_variable_id: str, new_variable_id: str) -> int:
    changed = 0
    block_type = block.get("type")

    if block_type in {"variable_set", "variable_add"} and block.get("variableId") == old_variable_id:
        block["variableId"] = new_variable_id
        changed += 1

    if block_type == "choice":
        for option in block.get("options") or []:
            if not isinstance(option, dict):
                continue
            for effect in option.get("effects") or []:
                if isinstance(effect, dict) and effect.get("variableId") == old_variable_id:
                    effect["variableId"] = new_variable_id
                    changed += 1

    if block_type == "condition":
        for branch in block.get("branches") or []:
            if not isinstance(branch, dict):
                continue
            for rule in branch.get("when") or []:
                if isinstance(rule, dict) and rule.get("variableId") == old_variable_id:
                    rule["variableId"] = new_variable_id
                    changed += 1

    return changed


def rename_project_variable(*, old_variable_id: object, variable: object) -> dict:
    old_id = validate_variable_id(old_variable_id)
    if not isinstance(variable, dict):
        raise ValueError("变量内容必须是一个对象。")

    next_variable = dict(variable)
    new_id = validate_variable_id(next_variable.get("id"))
    variables_path = DATA_DIR / "variables.json"
    variables_doc = normalize_variables_document(read_json(variables_path))
    variables = variables_doc.get("variables", [])
    target_index = next(
        (index for index, item in enumerate(variables) if item.get("id") == old_id),
        None,
    )

    if target_index is None:
        raise ValueError("没有找到要重命名的变量。")

    if any(item.get("id") == new_id for index, item in enumerate(variables) if index != target_index):
        raise ValueError("这个变量 ID 已经被其他变量使用。")

    next_variable["id"] = new_id
    normalized_next_doc = normalize_variables_document({"variables": [next_variable]})
    normalized_next_variable = normalized_next_doc["variables"][0]
    if normalized_next_variable.get("id") != new_id:
        raise ValueError("变量 ID 无法被安全保存，请换一个更简单的 ID。")

    variables[target_index] = normalized_next_variable
    variables_doc["variables"] = variables
    write_json(variables_path, variables_doc)

    reference_count = 0
    scene_count = 0
    chapter_count = 0

    if old_id != new_id:
        for chapter_path in list_chapter_files():
            chapter = read_json(chapter_path)
            chapter_changed = False
            for scene in chapter.get("scenes") or []:
                if not isinstance(scene, dict):
                    continue
                scene_changed = 0
                for block in scene.get("blocks") or []:
                    if isinstance(block, dict):
                        scene_changed += replace_variable_reference_in_block(block, old_id, new_id)
                if scene_changed:
                    reference_count += scene_changed
                    scene_count += 1
                    chapter_changed = True
            if chapter_changed:
                chapter_count += 1
                write_json(chapter_path, chapter)

    touch_project()
    return {
        "variable": normalized_next_variable,
        "migration": {
            "oldVariableId": old_id,
            "newVariableId": new_id,
            "referenceCount": reference_count,
            "sceneCount": scene_count,
            "chapterCount": chapter_count,
        },
    }


def sanitize_particle_custom_presets(presets: list) -> list[dict]:
    if not isinstance(presets, list):
        raise ValueError("自定义粒子预设必须是一个列表。")

    cleaned: list[dict] = []
    seen_ids: set[str] = set()

    for index, raw_preset in enumerate(presets[:24]):
        if not isinstance(raw_preset, dict):
            raise ValueError("每个自定义粒子预设都必须是一个对象。")

        name = str(raw_preset.get("name", "")).strip()
        if not name:
            continue

        if len(name) > 36:
            raise ValueError("粒子预设名字不能超过 36 个字符。")

        config = raw_preset.get("config")
        if not isinstance(config, dict):
            raise ValueError(f"粒子预设「{name}」缺少有效的配置内容。")

        preset_id = make_slug(str(raw_preset.get("id") or name))
        if not preset_id:
            preset_id = f"particle_preset_{index + 1:02d}"

        candidate_id = preset_id
        suffix = 2
        while candidate_id in seen_ids:
            candidate_id = f"{preset_id}_{suffix:02d}"
            suffix += 1
        seen_ids.add(candidate_id)

        try:
            clean_config = json.loads(json.dumps(config, ensure_ascii=False))
        except (TypeError, ValueError) as error:
            raise ValueError(f"粒子预设「{name}」里有不能保存的数据：{error}") from error

        cleaned.append(
            {
                "id": candidate_id,
                "name": name,
                "config": clean_config,
            }
        )

    return cleaned


def make_slug(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", value or "").strip("_").lower()
    return cleaned or "asset"


def make_project_id(name: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", name or "", flags=re.UNICODE).strip("_-").lower()
    return cleaned or "untitled_project"


def next_project_id(base_name: str) -> str:
    ensure_project_roots()
    candidate = make_project_id(base_name)
    suffix = 2

    while (PROJECTS_DIR / candidate).exists():
        candidate = f"{make_project_id(base_name)}_{suffix:02d}"
        suffix += 1

    return candidate


def create_blank_project(project_name: str, editor_mode: str | None = None) -> dict:
    global HAS_SELECTED_PROJECT
    clean_name = str(project_name or "").strip()
    if not clean_name:
        raise ValueError("新项目至少要有一个名字。")

    ensure_project_roots()
    project_id = next_project_id(clean_name)
    project_dir = PROJECTS_DIR / project_id
    data_dir = project_dir / "data"
    chapters_dir = data_dir / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)

    normalized_editor_mode = str(editor_mode or DEFAULT_EDITOR_MODE).strip().lower() or DEFAULT_EDITOR_MODE
    if normalized_editor_mode not in {"beginner", "advanced"}:
        normalized_editor_mode = DEFAULT_EDITOR_MODE

    timestamp = now_iso()
    project_doc = {
        "projectId": project_id,
        "title": clean_name,
        "template": "blank",
        "language": DEFAULT_PROJECT_LANGUAGE,
        "supportedLanguages": [DEFAULT_PROJECT_LANGUAGE],
        "releaseVersion": DEFAULT_EXPORT_RELEASE_VERSION,
        "editorMode": normalized_editor_mode,
        "resolution": {
            "width": 1920,
            "height": 1080,
        },
        "runtimeSettings": build_default_project_runtime_settings(),
        "dialogBoxConfig": build_default_dialog_box_config(),
        "gameUiConfig": build_default_game_ui_config(),
        "formatVersion": PROJECT_FORMAT_VERSION,
        "chapterOrder": [],
        "entrySceneId": "",
        "createdAt": timestamp,
        "updatedAt": timestamp,
    }

    write_json(project_dir / "project.json", project_doc)
    write_json(data_dir / "assets.json", {"assets": []})
    write_json(data_dir / "characters.json", {"characters": []})
    write_json(data_dir / "variables.json", {"variables": []})
    set_active_project_paths(project_id, project_dir, "project")
    HAS_SELECTED_PROJECT = True

    return {
        "project": build_project_summary(project_id, project_dir, kind="project"),
        "projectCenter": get_project_center_payload(),
    }


def get_history_root(project_dir: Path | None = None) -> Path:
    target_dir = project_dir or Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR)
    return target_dir / HISTORY_DIR_NAME


def get_history_snapshots_dir(project_dir: Path | None = None) -> Path:
    return get_history_root(project_dir) / HISTORY_SNAPSHOTS_DIR_NAME


def get_history_manifest_path(project_dir: Path | None = None) -> Path:
    return get_history_root(project_dir) / HISTORY_MANIFEST_FILE_NAME


def get_session_state_path(project_dir: Path | None = None) -> Path:
    return get_history_root(project_dir) / SESSION_STATE_FILE_NAME


def ensure_history_storage(project_dir: Path | None = None) -> None:
    get_history_snapshots_dir(project_dir).mkdir(parents=True, exist_ok=True)


def load_session_state(project_dir: Path | None = None) -> dict:
    ensure_history_storage(project_dir)
    state_path = get_session_state_path(project_dir)
    if state_path.is_file():
        try:
            payload = read_json(state_path)
        except Exception:
            payload = {}
    else:
        payload = {}

    return {
        "formatVersion": SESSION_FORMAT_VERSION,
        "sessionId": str(payload.get("sessionId") or "").strip(),
        "projectId": str(payload.get("projectId") or "").strip(),
        "kind": str(payload.get("kind") or "project").strip() or "project",
        "status": str(payload.get("status") or "closed").strip() or "closed",
        "startedAt": str(payload.get("startedAt") or "").strip(),
        "closedAt": str(payload.get("closedAt") or "").strip(),
        "lastEndedReason": str(payload.get("lastEndedReason") or "").strip(),
        "lastUnexpectedExitAt": str(payload.get("lastUnexpectedExitAt") or "").strip(),
        "lastUnexpectedExitStartedAt": str(payload.get("lastUnexpectedExitStartedAt") or "").strip(),
        "recoveryNoticeActive": bool(payload.get("recoveryNoticeActive")),
        "noticeAcknowledgedAt": str(payload.get("noticeAcknowledgedAt") or "").strip(),
    }


def save_session_state(payload: dict, project_dir: Path | None = None) -> None:
    ensure_history_storage(project_dir)
    write_json(
        get_session_state_path(project_dir),
        {
            "formatVersion": SESSION_FORMAT_VERSION,
            "sessionId": str(payload.get("sessionId") or "").strip(),
            "projectId": str(payload.get("projectId") or "").strip(),
            "kind": str(payload.get("kind") or "project").strip() or "project",
            "status": str(payload.get("status") or "closed").strip() or "closed",
            "startedAt": str(payload.get("startedAt") or "").strip(),
            "closedAt": str(payload.get("closedAt") or "").strip(),
            "lastEndedReason": str(payload.get("lastEndedReason") or "").strip(),
            "lastUnexpectedExitAt": str(payload.get("lastUnexpectedExitAt") or "").strip(),
            "lastUnexpectedExitStartedAt": str(payload.get("lastUnexpectedExitStartedAt") or "").strip(),
            "recoveryNoticeActive": bool(payload.get("recoveryNoticeActive")),
            "noticeAcknowledgedAt": str(payload.get("noticeAcknowledgedAt") or "").strip(),
        },
    )


def mark_project_session_running(project_id: str, project_dir: Path | None = None, *, kind: str = "project") -> dict:
    target_dir = project_dir or Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR)
    previous_state = load_session_state(target_dir)
    unexpected_exit_detected = previous_state.get("status") == "running" and previous_state.get("sessionId") != CURRENT_SERVER_SESSION_ID
    next_state = {
        **previous_state,
        "sessionId": CURRENT_SERVER_SESSION_ID,
        "projectId": project_id,
        "kind": kind,
        "status": "running",
        "startedAt": now_iso(),
        "closedAt": "",
        "lastEndedReason": "",
        "noticeAcknowledgedAt": previous_state.get("noticeAcknowledgedAt", ""),
    }

    if unexpected_exit_detected:
        next_state["lastUnexpectedExitAt"] = now_iso()
        next_state["lastUnexpectedExitStartedAt"] = previous_state.get("startedAt", "")
        next_state["recoveryNoticeActive"] = True
        next_state["noticeAcknowledgedAt"] = ""

    save_session_state(next_state, target_dir)
    return next_state


def mark_project_session_closed(project_dir: Path | None = None, *, reason: str = "closed") -> dict:
    target_dir = project_dir or Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR)
    payload = load_session_state(target_dir)
    payload["status"] = "closed"
    payload["closedAt"] = now_iso()
    payload["lastEndedReason"] = str(reason or "closed").strip() or "closed"
    save_session_state(payload, target_dir)
    return payload


def build_session_recovery_payload(project_dir: Path | None = None) -> dict:
    payload = load_session_state(project_dir)
    notice_active = bool(payload.get("recoveryNoticeActive"))
    started_at = payload.get("lastUnexpectedExitStartedAt") or payload.get("startedAt") or ""
    return {
        "noticeActive": notice_active,
        "lastUnexpectedExitAt": payload.get("lastUnexpectedExitAt", ""),
        "lastUnexpectedExitStartedAt": started_at,
        "lastEndedReason": payload.get("lastEndedReason", ""),
        "message": (
            f"上次打开这个项目时，编辑器可能没有正常退出。上一次会话开始于 {started_at or '未知时间'}。"
            if notice_active
            else ""
        ),
    }


def acknowledge_session_recovery_notice(project_dir: Path | None = None) -> dict:
    target_dir = project_dir or Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR)
    payload = load_session_state(target_dir)
    payload["recoveryNoticeActive"] = False
    payload["noticeAcknowledgedAt"] = now_iso()
    save_session_state(payload, target_dir)
    return build_session_recovery_payload(target_dir)


def get_project_state_relative_paths(project_dir: Path | None = None) -> list[Path]:
    target_dir = project_dir or Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR)
    paths = [
        Path("project.json"),
        Path("data/assets.json"),
        Path("data/characters.json"),
        Path("data/variables.json"),
    ]
    chapters_dir = target_dir / "data" / "chapters"
    if chapters_dir.is_dir():
        paths.extend(sorted(path.relative_to(target_dir) for path in chapters_dir.glob("*.json")))
    return paths


def load_history_manifest(project_dir: Path | None = None) -> dict:
    ensure_history_storage(project_dir)
    manifest_path = get_history_manifest_path(project_dir)
    if manifest_path.is_file():
        try:
            manifest = read_json(manifest_path)
        except Exception:
            manifest = {}
    else:
        manifest = {}

    entries = manifest.get("entries")
    return {
        "formatVersion": HISTORY_FORMAT_VERSION,
        "currentIndex": int(manifest.get("currentIndex", -1)),
        "entries": entries if isinstance(entries, list) else [],
    }


def save_history_manifest(manifest: dict, project_dir: Path | None = None) -> None:
    ensure_history_storage(project_dir)
    payload = {
        "formatVersion": HISTORY_FORMAT_VERSION,
        "currentIndex": int(manifest.get("currentIndex", -1)),
        "entries": manifest.get("entries", []),
    }
    write_json(get_history_manifest_path(project_dir), payload)


def next_snapshot_id(project_dir: Path | None = None) -> str:
    snapshots_dir = get_history_snapshots_dir(project_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    candidate = f"snapshot_{timestamp}"
    suffix = 2

    while (snapshots_dir / candidate).exists():
        candidate = f"snapshot_{timestamp}_{suffix:02d}"
        suffix += 1

    return candidate


def copy_project_state_to_snapshot(snapshot_dir: Path, project_dir: Path | None = None) -> None:
    target_dir = project_dir or Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR)
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    for relative_path in get_project_state_relative_paths(target_dir):
        source_path = target_dir / relative_path
        if not source_path.is_file():
            continue
        output_path = snapshot_dir / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, output_path)


def restore_project_state_from_snapshot(snapshot_id: str, project_dir: Path | None = None) -> None:
    target_dir = project_dir or Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR)
    snapshot_dir = get_history_snapshots_dir(target_dir) / snapshot_id
    if not snapshot_dir.is_dir():
        raise ValueError("没有找到要恢复的快照。")

    chapters_dir = target_dir / "data" / "chapters"
    if chapters_dir.is_dir():
        for chapter_file in chapters_dir.glob("*.json"):
            chapter_file.unlink()

    for relative_path in get_project_state_relative_paths(snapshot_dir):
        source_path = snapshot_dir / relative_path
        if not source_path.is_file():
            continue
        output_path = target_dir / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, output_path)


def trim_history_manifest(manifest: dict, project_dir: Path | None = None) -> None:
    entries = manifest.get("entries", [])
    current_index = int(manifest.get("currentIndex", -1))

    while len(entries) > MAX_HISTORY_SNAPSHOTS:
        removed = entries.pop(0)
        current_index -= 1
        snapshot_dir = get_history_snapshots_dir(project_dir) / str(removed.get("id", "")).strip()
        if snapshot_dir.is_dir():
            shutil.rmtree(snapshot_dir, ignore_errors=True)

    manifest["entries"] = entries
    manifest["currentIndex"] = max(min(current_index, len(entries) - 1), 0) if entries else -1


def describe_history_relative_path(relative_path: Path, *, current_dir: Path, snapshot_dir: Path) -> str:
    normalized = relative_path.as_posix()
    if normalized == "project.json":
        return "项目设置"
    if normalized == "data/assets.json":
        return "素材库"
    if normalized == "data/characters.json":
        return "角色资料"
    if normalized == "data/variables.json":
        return "变量库"
    if normalized.startswith("data/chapters/"):
        chapter_name = relative_path.stem
        for base_dir in (current_dir, snapshot_dir):
            candidate = base_dir / relative_path
            if candidate.is_file():
                try:
                    chapter_doc = read_json(candidate)
                except Exception:
                    continue
                chapter_name = str(chapter_doc.get("name") or chapter_doc.get("chapterId") or relative_path.stem).strip()
                if chapter_name:
                    break
        return f"章节：{chapter_name or relative_path.stem}"
    return normalized


def ensure_project_history_initialized(project_dir: Path | None = None) -> dict:
    target_dir = project_dir or Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR)
    manifest = load_history_manifest(target_dir)
    entries = manifest.get("entries", [])
    current_index = int(manifest.get("currentIndex", -1))
    current_entry = entries[current_index] if 0 <= current_index < len(entries) else None
    current_snapshot_dir = (
        get_history_snapshots_dir(target_dir) / str(current_entry.get("id", "")).strip()
        if current_entry
        else None
    )

    if entries and current_snapshot_dir and current_snapshot_dir.is_dir():
        return manifest

    snapshots_dir = get_history_snapshots_dir(target_dir)
    if snapshots_dir.is_dir():
        for path in snapshots_dir.iterdir():
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)

    snapshot_id = next_snapshot_id(target_dir)
    snapshot_dir = snapshots_dir / snapshot_id
    copy_project_state_to_snapshot(snapshot_dir, target_dir)
    manifest = {
        "formatVersion": HISTORY_FORMAT_VERSION,
        "currentIndex": 0,
        "entries": [
            {
                "id": snapshot_id,
                "createdAt": now_iso(),
                "label": "当前版本基线",
                "kind": "baseline",
            }
        ],
    }
    save_history_manifest(manifest, target_dir)
    return manifest


def build_history_payload(project_dir: Path | None = None) -> dict:
    target_dir = project_dir or Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR)
    manifest = ensure_project_history_initialized(target_dir)
    entries = manifest.get("entries", [])
    current_index = int(manifest.get("currentIndex", -1))
    timeline_entries = [
        {
            **entry,
            "index": index,
            "isCurrent": index == current_index,
        }
        for index, entry in enumerate(entries)
    ]
    current_entry = timeline_entries[current_index] if 0 <= current_index < len(timeline_entries) else None
    previous_entry = timeline_entries[current_index - 1] if current_index > 0 else None
    next_entry = timeline_entries[current_index + 1] if 0 <= current_index < len(timeline_entries) - 1 else None
    recent_entries = list(reversed(timeline_entries[-6:]))
    timeline_snapshots = list(reversed(timeline_entries))
    return {
        "totalSnapshots": len(entries),
        "currentIndex": current_index,
        "canUndo": current_index > 0,
        "canRedo": 0 <= current_index < len(entries) - 1,
        "currentSnapshot": current_entry,
        "previousSnapshot": previous_entry,
        "nextSnapshot": next_entry,
        "recentSnapshots": recent_entries,
        "timelineSnapshots": timeline_snapshots,
    }


def build_history_restore_preview(
    *,
    target_index: int | None = None,
    snapshot_id: str | None = None,
    project_dir: Path | None = None,
) -> dict:
    target_dir = project_dir or Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR)
    manifest = ensure_project_history_initialized(target_dir)
    entries = manifest.get("entries", [])
    resolved_index = None

    if snapshot_id:
        clean_snapshot_id = str(snapshot_id).strip()
        for index, entry in enumerate(entries):
            if str(entry.get("id", "")).strip() == clean_snapshot_id:
                resolved_index = index
                break
    elif target_index is not None:
        resolved_index = int(target_index)

    if resolved_index is None or not 0 <= resolved_index < len(entries):
        raise ValueError("没有找到要预览的历史版本。")

    entry = entries[resolved_index]
    snapshot_dir = get_history_snapshots_dir(target_dir) / str(entry.get("id", "")).strip()
    current_paths = set(get_project_state_relative_paths(target_dir))
    snapshot_paths = set(get_project_state_relative_paths(snapshot_dir))
    changed_items: list[dict] = []

    for relative_path in sorted(current_paths | snapshot_paths):
        current_path = target_dir / relative_path
        snapshot_path = snapshot_dir / relative_path
        current_exists = current_path.is_file()
        snapshot_exists = snapshot_path.is_file()

        if current_exists != snapshot_exists:
            changed_items.append(
                {
                    "path": relative_path.as_posix(),
                    "label": describe_history_relative_path(relative_path, current_dir=target_dir, snapshot_dir=snapshot_dir),
                    "kind": "created" if snapshot_exists else "removed",
                }
            )
            continue

        if not current_exists or not snapshot_exists:
            continue

        if current_path.read_bytes() != snapshot_path.read_bytes():
            changed_items.append(
                {
                    "path": relative_path.as_posix(),
                    "label": describe_history_relative_path(relative_path, current_dir=target_dir, snapshot_dir=snapshot_dir),
                    "kind": "changed",
                }
            )

    area_labels = [item.get("label") or item.get("path") for item in changed_items]
    preview_text = (
        "当前版本和这份历史版本没有内容差异。"
        if not changed_items
        else f"恢复后会影响 {len(changed_items)} 处内容：{'、'.join(area_labels[:4])}"
        + (" 等" if len(area_labels) > 4 else "")
        + "。"
    )
    return {
        "targetIndex": resolved_index,
        "targetSnapshot": {
            **entry,
            "index": resolved_index,
        },
        "changedFileCount": len(changed_items),
        "changedItems": changed_items[:12],
        "summaryText": preview_text,
    }


def create_history_snapshot(label: str, kind: str = "auto", project_dir: Path | None = None) -> dict:
    target_dir = project_dir or Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR)
    manifest = ensure_project_history_initialized(target_dir)
    entries = manifest.get("entries", [])
    current_index = int(manifest.get("currentIndex", -1))

    if current_index < len(entries) - 1:
        for entry in entries[current_index + 1 :]:
            snapshot_dir = get_history_snapshots_dir(target_dir) / str(entry.get("id", "")).strip()
            if snapshot_dir.is_dir():
                shutil.rmtree(snapshot_dir, ignore_errors=True)
        entries = entries[: current_index + 1]

    snapshot_id = next_snapshot_id(target_dir)
    snapshot_dir = get_history_snapshots_dir(target_dir) / snapshot_id
    copy_project_state_to_snapshot(snapshot_dir, target_dir)
    entries.append(
        {
            "id": snapshot_id,
            "createdAt": now_iso(),
            "label": str(label or "自动快照").strip() or "自动快照",
            "kind": kind,
        }
    )
    manifest["entries"] = entries
    manifest["currentIndex"] = len(entries) - 1
    trim_history_manifest(manifest, target_dir)
    save_history_manifest(manifest, target_dir)
    return build_history_payload(target_dir)


def restore_history_index(target_index: int, project_dir: Path | None = None) -> dict:
    target_dir = project_dir or Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR)
    manifest = ensure_project_history_initialized(target_dir)
    entries = manifest.get("entries", [])

    if not 0 <= target_index < len(entries):
        raise ValueError("没有找到要恢复的历史版本。")

    restore_project_state_from_snapshot(str(entries[target_index].get("id", "")).strip(), target_dir)
    manifest["currentIndex"] = target_index
    save_history_manifest(manifest, target_dir)
    return build_history_payload(target_dir)


def undo_history(project_dir: Path | None = None) -> dict:
    target_dir = project_dir or Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR)
    payload = build_history_payload(target_dir)
    if not payload.get("canUndo"):
        raise ValueError("已经没有更早的版本可以撤销了。")
    return restore_history_index(int(payload["currentIndex"]) - 1, target_dir)


def redo_history(project_dir: Path | None = None) -> dict:
    target_dir = project_dir or Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR)
    payload = build_history_payload(target_dir)
    if not payload.get("canRedo"):
        raise ValueError("已经没有更晚的版本可以重做了。")
    return restore_history_index(int(payload["currentIndex"]) + 1, target_dir)


def restore_history_snapshot(
    *,
    target_index: int | None = None,
    snapshot_id: str | None = None,
    project_dir: Path | None = None,
) -> dict:
    target_dir = project_dir or Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR)
    manifest = ensure_project_history_initialized(target_dir)
    entries = manifest.get("entries", [])

    if snapshot_id:
        clean_snapshot_id = str(snapshot_id).strip()
        for index, entry in enumerate(entries):
            if str(entry.get("id", "")).strip() == clean_snapshot_id:
                return restore_history_index(index, target_dir)
        raise ValueError("没有找到你要恢复的版本。")

    if target_index is None:
        raise ValueError("恢复版本时缺少 targetIndex 或 snapshotId。")

    return restore_history_index(int(target_index), target_dir)


def update_history_snapshot_label(
    *,
    target_index: int | None = None,
    snapshot_id: str | None = None,
    label: str,
    project_dir: Path | None = None,
) -> dict:
    target_dir = project_dir or Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR)
    manifest = ensure_project_history_initialized(target_dir)
    entries = manifest.get("entries", [])
    clean_label = str(label or "").strip()
    if not clean_label:
        raise ValueError("检查点备注不能为空。")

    resolved_index = None
    if snapshot_id:
        clean_snapshot_id = str(snapshot_id).strip()
        for index, entry in enumerate(entries):
            if str(entry.get("id", "")).strip() == clean_snapshot_id:
                resolved_index = index
                break
    elif target_index is not None:
        resolved_index = int(target_index)

    if resolved_index is None or not 0 <= resolved_index < len(entries):
        raise ValueError("没有找到要修改备注的版本。")

    entries[resolved_index]["label"] = clean_label
    save_history_manifest(manifest, target_dir)
    return build_history_payload(target_dir)


def create_manual_history_snapshot(label: str, project_dir: Path | None = None) -> dict:
    target_dir = project_dir or Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR)
    clean_label = str(label or "").strip() or "手动检查点"
    return create_history_snapshot(label=clean_label, kind="manual", project_dir=target_dir)


def record_project_history(label: str, project_dir: Path | None = None) -> dict:
    target_dir = project_dir or Path(CURRENT_PROJECT_INFO.get("projectDir") or SAMPLE_PROJECT_DIR)
    return create_history_snapshot(label=label, kind="auto", project_dir=target_dir)


def attach_history_to_result(result: dict | None, label: str, project_dir: Path | None = None) -> dict:
    payload = dict(result or {})
    try:
        payload["history"] = record_project_history(label, project_dir=project_dir)
    except Exception as error:  # pragma: no cover - keep primary edits from being blocked by history issues
        payload["history"] = build_history_payload(project_dir)
        payload["historyError"] = str(error)
    return payload


def build_starter_kit_overview(assets: list[dict], characters: list[dict]) -> dict:
    return {
        "missingCharacter": len(characters) == 0,
        "missingBackground": not any(asset.get("type") == "background" for asset in assets),
        "missingBgm": not any(asset.get("type") == "bgm" for asset in assets),
    }


def next_named_asset_path(
    existing_paths: set[str],
    asset_type: str,
    base_name: str,
    suffix: str,
) -> str:
    directory = ASSET_DIRECTORIES.get(asset_type, Path("assets/misc"))
    stem = make_slug(base_name)
    candidate = directory / f"{stem}{suffix}"
    counter = 2

    while str(candidate).replace("\\", "/") in existing_paths:
        candidate = directory / f"{stem}_{counter:02d}{suffix}"
        counter += 1

    return str(candidate).replace("\\", "/")


def build_png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    checksum = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack("!I", len(data)) + chunk_type + data + struct.pack("!I", checksum)


def build_rgba_png_bytes(width: int, height: int, pixel_builder) -> bytes:
    rows = bytearray()
    for y in range(height):
        rows.append(0)
        for x in range(width):
            rows.extend(pixel_builder(x, y))
    return b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            build_png_chunk(b"IHDR", struct.pack("!IIBBBBB", width, height, 8, 6, 0, 0, 0)),
            build_png_chunk(b"IDAT", zlib.compress(bytes(rows), 9)),
            build_png_chunk(b"IEND", b""),
        ]
    )


def build_starter_background_placeholder_png_bytes() -> bytes:
    width = 320
    height = 180

    def pixel(x: int, y: int) -> tuple[int, int, int, int]:
        sky = int(28 + 48 * (1 - y / max(height - 1, 1)))
        glow = int(38 * (x / max(width - 1, 1)))
        return (18 + glow, sky, 82 + glow, 255)

    return build_rgba_png_bytes(width, height, pixel)


def build_starter_sprite_placeholder_png_bytes() -> bytes:
    width = 160
    height = 240
    center_x = width // 2

    def pixel(x: int, y: int) -> tuple[int, int, int, int]:
        head = (x - center_x) ** 2 + (y - 60) ** 2 <= 28 ** 2
        body = abs(x - center_x) <= max(12, 34 - abs(y - 142) // 3) and 88 <= y <= 210
        hair = (x - center_x) ** 2 + (y - 72) ** 2 <= 42 ** 2 and y > 42
        if hair and not head:
            return (44, 70, 122, 215)
        if head:
            return (244, 210, 188, 235)
        if body:
            return (78, 135, 210, 230)
        return (0, 0, 0, 0)

    return build_rgba_png_bytes(width, height, pixel)


def build_starter_silent_wav_bytes(duration_seconds: float = 1.2, sample_rate: int = 22050) -> bytes:
    frame_count = max(1, int(sample_rate * duration_seconds))
    channel_count = 1
    bits_per_sample = 16
    block_align = channel_count * bits_per_sample // 8
    byte_rate = sample_rate * block_align
    data = b"\x00" * frame_count * block_align
    return b"".join(
        [
            b"RIFF",
            struct.pack("<I", 36 + len(data)),
            b"WAVEfmt ",
            struct.pack("<IHHIIHH", 16, 1, channel_count, sample_rate, byte_rate, block_align, bits_per_sample),
            b"data",
            struct.pack("<I", len(data)),
            data,
        ]
    )


def write_starter_placeholder_asset_file(asset_record: dict) -> Path | None:
    asset_path = str(asset_record.get("path") or "").strip()
    asset_type = str(asset_record.get("type") or "").strip()
    if not asset_path:
        return None

    target_path = TEMPLATE_DIR / asset_path
    if target_path.exists():
        return None
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if asset_type == "background":
        target_path.write_bytes(build_starter_background_placeholder_png_bytes())
    elif asset_type == "sprite":
        target_path.write_bytes(build_starter_sprite_placeholder_png_bytes())
    elif asset_type == "bgm":
        target_path.write_bytes(build_starter_silent_wav_bytes())
    else:
        return None
    return target_path


def capture_file_snapshots(paths: list[Path]) -> dict[Path, bytes | None]:
    return {path: path.read_bytes() if path.exists() else None for path in paths}


def restore_file_snapshots(snapshots: dict[Path, bytes | None]) -> None:
    for path, content in snapshots.items():
        if content is None:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def build_starter_asset_record(
    asset_type: str,
    asset_name: str,
    existing_ids: set[str],
    existing_paths: set[str],
    tags: list[str],
) -> dict:
    suffix = ".wav" if asset_type == "bgm" else ".png"
    asset_id = next_named_id(existing_ids, ASSET_ID_PREFIXES.get(asset_type, asset_type), asset_name)
    asset_path = next_named_asset_path(existing_paths, asset_type, asset_name, suffix)
    existing_ids.add(asset_id)
    existing_paths.add(asset_path)
    return {
        "id": asset_id,
        "type": asset_type,
        "name": asset_name,
        "path": asset_path,
        "tags": normalize_asset_tags(tags),
        "favorite": False,
    }


def find_first_scene_reference() -> tuple[Path, dict, dict] | None:
    project = read_json(PROJECT_PATH)
    chapter_files = list_chapter_files()
    if not chapter_files:
        return None

    chapter_by_id: dict[str, tuple[Path, dict]] = {}
    remaining: list[tuple[Path, dict]] = []
    for chapter_path in chapter_files:
        chapter = read_json(chapter_path)
        chapter_id = str(chapter.get("chapterId") or "").strip()
        if chapter_id:
            chapter_by_id[chapter_id] = (chapter_path, chapter)
        remaining.append((chapter_path, chapter))

    ordered_refs: list[tuple[Path, dict]] = []
    for chapter_id in normalize_text_list(project.get("chapterOrder")):
        ref = chapter_by_id.get(chapter_id)
        if ref and ref not in ordered_refs:
            ordered_refs.append(ref)
    ordered_refs.extend(ref for ref in remaining if ref not in ordered_refs)

    for chapter_path, chapter in ordered_refs:
        scenes = chapter.get("scenes", [])
        if not isinstance(scenes, list) or not scenes:
            continue
        scene_by_id = {
            str(scene.get("id") or ""): scene
            for scene in scenes
            if isinstance(scene, dict) and str(scene.get("id") or "").strip()
        }
        ordered_scenes = [
            scene_by_id[scene_id]
            for scene_id in normalize_text_list(chapter.get("sceneOrder"))
            if scene_id in scene_by_id
        ]
        ordered_scenes.extend(scene for scene in scenes if isinstance(scene, dict) and scene not in ordered_scenes)
        if ordered_scenes:
            return chapter_path, chapter, ordered_scenes[0]
    return None


def find_first_asset_record(assets: list[dict], asset_type: str) -> dict | None:
    return next((asset for asset in assets if asset.get("type") == asset_type), None)


def find_starter_character_expression(character: dict | None) -> str:
    if not isinstance(character, dict):
        return "expr_default"
    for expression in character.get("expressions", []) or []:
        expression_id = str(expression.get("id") or "").strip()
        if expression_id:
            return expression_id
    return "expr_default"


def bootstrap_starter_kit_first_scene(
    *,
    assets: list[dict],
    characters: list[dict],
    created_character: dict | None,
) -> dict:
    scene_ref = find_first_scene_reference()
    if not scene_ref:
        return {
            "applied": False,
            "insertedLabels": [],
            "insertedBlockIds": [],
            "reason": "项目还没有章节和场景，先创建第一章后会更适合接入起步骨架。",
        }

    chapter_path, chapter, scene = scene_ref
    blocks = scene.setdefault("blocks", [])
    if not isinstance(blocks, list):
        blocks = []
        scene["blocks"] = blocks

    background_asset = find_first_asset_record(assets, "background")
    bgm_asset = find_first_asset_record(assets, "bgm")
    starter_character = created_character or next((character for character in characters if isinstance(character, dict)), None)
    existing_block_ids = {
        str(block.get("id") or "").strip()
        for block in blocks
        if isinstance(block, dict) and str(block.get("id") or "").strip()
    }
    inserted_blocks: list[dict] = []
    inserted_labels: list[str] = []

    if bgm_asset and not any(isinstance(block, dict) and block.get("type") == "music_play" for block in blocks):
        inserted_blocks.append(
            {
                "id": build_unique_slug_id(existing_block_ids, "block", "starter_bgm"),
                "type": "music_play",
                "assetId": bgm_asset["id"],
                "loop": True,
                "fadeInMs": 600,
            }
        )
        inserted_labels.append("BGM 卡片")

    if background_asset and not any(isinstance(block, dict) and block.get("type") == "background" for block in blocks):
        inserted_blocks.append(
            {
                "id": build_unique_slug_id(existing_block_ids, "block", "starter_background"),
                "type": "background",
                "assetId": background_asset["id"],
                "transition": "fade",
            }
        )
        inserted_labels.append("背景卡片")

    if starter_character and not any(isinstance(block, dict) and block.get("type") == "character_show" for block in blocks):
        inserted_blocks.append(
            {
                "id": build_unique_slug_id(existing_block_ids, "block", "starter_character"),
                "type": "character_show",
                "characterId": starter_character["id"],
                "expressionId": find_starter_character_expression(starter_character),
                "position": starter_character.get("defaultPosition") or "left",
                "transition": "fade",
            }
        )
        inserted_labels.append("角色出场卡片")

    if starter_character and not any(isinstance(block, dict) and block.get("type") == "dialogue" for block in blocks):
        inserted_blocks.append(
            {
                "id": build_unique_slug_id(existing_block_ids, "block", "starter_dialogue"),
                "type": "dialogue",
                "speakerId": starter_character["id"],
                "expressionId": find_starter_character_expression(starter_character),
                "text": "今天，就从这里开始吧。",
            }
        )
        inserted_labels.append("第一句角色台词")

    if not inserted_blocks:
        return {
            "applied": False,
            "chapterId": chapter.get("chapterId", ""),
            "sceneId": scene.get("id", ""),
            "sceneName": scene.get("name", ""),
            "insertedLabels": [],
            "insertedBlockIds": [],
            "reason": "首场景已经有基础演出卡片，没有重复插入。",
        }

    scene["blocks"] = inserted_blocks + blocks
    write_json(chapter_path, chapter)
    return {
        "applied": True,
        "chapterId": chapter.get("chapterId", ""),
        "sceneId": scene.get("id", ""),
        "sceneName": scene.get("name", ""),
        "insertedLabels": inserted_labels,
        "insertedBlockIds": [block["id"] for block in inserted_blocks],
    }


def create_starter_kit(
    character_name: str | None = None,
    background_name: str | None = None,
    bgm_name: str | None = None,
) -> dict:
    assets_path = DATA_DIR / "assets.json"
    characters_path = DATA_DIR / "characters.json"
    assets_doc = read_json(assets_path)
    characters_doc = read_json(characters_path)
    assets = assets_doc.setdefault("assets", [])
    characters = characters_doc.setdefault("characters", [])
    starter_overview = build_starter_kit_overview(assets, characters)

    if not any(starter_overview.values()):
        raise ValueError("这个项目的起步骨架已经齐了，可以直接继续写剧情。")

    clean_character_name = str(character_name or "女主角").strip() or "女主角"
    clean_background_name = str(background_name or "第一场背景").strip() or "第一场背景"
    clean_bgm_name = str(bgm_name or "开场 BGM").strip() or "开场 BGM"
    existing_asset_ids = {asset.get("id") for asset in assets if asset.get("id")}
    existing_asset_paths = {str(asset.get("path") or "").replace("\\", "/") for asset in assets if asset.get("path")}
    existing_character_ids = {character.get("id") for character in characters if character.get("id")}
    created_labels: list[str] = []
    created_asset_records: list[dict] = []
    created_character = None
    file_snapshots = capture_file_snapshots([assets_path, characters_path, PROJECT_PATH, *list_chapter_files()])
    created_placeholder_paths: list[Path] = []

    if starter_overview["missingCharacter"]:
        sprite_name = f"{clean_character_name} 默认立绘"
        sprite_record = build_starter_asset_record(
            "sprite",
            sprite_name,
            existing_asset_ids,
            existing_asset_paths,
            ["起步骨架", clean_character_name, "默认", "占位素材", "可替换"],
        )
        assets.append(sprite_record)
        created_asset_records.append(sprite_record)

        character_id = next_named_id(existing_character_ids, "char", clean_character_name)
        existing_character_ids.add(character_id)
        created_character = {
            "id": character_id,
            "displayName": clean_character_name,
            "nameColor": "#E6876A",
            "defaultPosition": "left",
            "bio": "这里先写这个角色的简介和性格关键词。",
            "defaultSpriteId": sprite_record["id"],
            "presentation": normalize_character_presentation(
                {"mode": "sprite", "fallbackSpriteAssetId": sprite_record["id"]},
                sprite_record["id"],
            ),
            "expressions": [
                {
                    "id": "expr_default",
                    "name": "默认",
                    "spriteAssetId": sprite_record["id"],
                }
            ],
        }
        characters.append(created_character)
        created_labels.append("第一个角色")

    if starter_overview["missingBackground"]:
        background_record = build_starter_asset_record(
            "background",
            clean_background_name,
            existing_asset_ids,
            existing_asset_paths,
            ["起步骨架", "背景", "占位素材", "可替换"],
        )
        assets.append(background_record)
        created_asset_records.append(background_record)
        created_labels.append("第一张背景")

    if starter_overview["missingBgm"]:
        bgm_record = build_starter_asset_record(
            "bgm",
            clean_bgm_name,
            existing_asset_ids,
            existing_asset_paths,
            ["起步骨架", "音乐", "占位素材", "可替换"],
        )
        assets.append(bgm_record)
        created_asset_records.append(bgm_record)
        created_labels.append("第一首 BGM")

    try:
        for asset_record in created_asset_records:
            written_path = write_starter_placeholder_asset_file(asset_record)
            if written_path:
                created_placeholder_paths.append(written_path)

        write_json(assets_path, assets_doc)
        write_json(characters_path, characters_doc)
        scene_bootstrap = bootstrap_starter_kit_first_scene(
            assets=assets,
            characters=characters,
            created_character=created_character,
        )
        touch_project()
    except Exception:
        for placeholder_path in reversed(created_placeholder_paths):
            try:
                placeholder_path.unlink(missing_ok=True)
            except OSError:
                pass
        restore_file_snapshots(file_snapshots)
        raise

    return {
        "createdLabels": created_labels,
        "createdCharacter": created_character,
        "createdAssets": [enrich_asset_record(asset_record) for asset_record in created_asset_records],
        "sceneBootstrap": scene_bootstrap,
        "starterOverview": build_starter_kit_overview(assets, characters),
    }


def get_project_directory(project_id: str) -> Path:
    if project_id == SAMPLE_PROJECT_ID:
        return SAMPLE_PROJECT_DIR
    return PROJECTS_DIR / project_id


def rename_project(project_id: str, project_name: str) -> dict:
    if project_id == SAMPLE_PROJECT_ID:
        raise ValueError("示例项目暂时不能直接改名，建议先复制成正式项目再改。")

    clean_name = str(project_name or "").strip()
    if not clean_name:
        raise ValueError("项目名字不能为空。")

    project_dir = get_project_directory(project_id)
    project_path = project_dir / "project.json"
    if not project_path.is_file():
        raise ValueError("没有找到要改名的项目。")

    project = read_json(project_path)
    project["title"] = clean_name
    project["updatedAt"] = now_iso()
    write_json(project_path, project)

    if CURRENT_PROJECT_INFO.get("projectId") == project_id:
        set_active_project_paths(project_id, project_dir, "project")

    return {
        "project": build_project_summary(project_id, project_dir, kind="project"),
        "projectCenter": get_project_center_payload(),
    }


def duplicate_project(source_project_id: str, project_name: str) -> dict:
    global HAS_SELECTED_PROJECT

    source_summary = find_project_summary(source_project_id)
    if not source_summary:
        raise ValueError("没有找到要复制的项目。")

    clean_name = str(project_name or "").strip()
    if not clean_name:
        raise ValueError("复制后的项目名字不能为空。")

    source_dir = get_project_directory(source_project_id)
    if not source_dir.is_dir():
        raise ValueError("源项目目录不存在。")

    new_project_id = next_project_id(clean_name)
    target_dir = PROJECTS_DIR / new_project_id
    shutil.copytree(source_dir, target_dir)
    duplicate_history_dir = get_history_root(target_dir)
    if duplicate_history_dir.is_dir():
        shutil.rmtree(duplicate_history_dir, ignore_errors=True)

    project_path = target_dir / "project.json"
    project = read_json(project_path)
    timestamp = now_iso()
    project["projectId"] = new_project_id
    project["title"] = clean_name
    project["updatedAt"] = timestamp
    project["createdAt"] = timestamp
    write_json(project_path, project)

    set_active_project_paths(new_project_id, target_dir, "project")
    HAS_SELECTED_PROJECT = True

    return {
        "project": build_project_summary(new_project_id, target_dir, kind="project"),
        "projectCenter": get_project_center_payload(),
    }


def delete_project(project_id: str) -> dict:
    global HAS_SELECTED_PROJECT

    if project_id == SAMPLE_PROJECT_ID:
        raise ValueError("示例项目暂时不能删除。")

    project_dir = get_project_directory(project_id)
    if not project_dir.is_dir():
        raise ValueError("没有找到要删除的项目。")

    shutil.rmtree(project_dir)

    if CURRENT_PROJECT_INFO.get("projectId") == project_id:
        set_active_project_paths(SAMPLE_PROJECT_ID, SAMPLE_PROJECT_DIR, "sample")
        HAS_SELECTED_PROJECT = False

    return {
        "deletedProjectId": project_id,
        "projectCenter": get_project_center_payload(),
    }


def build_asset_id(asset_type: str, file_name: str, existing_ids: set[str]) -> str:
    prefix = ASSET_ID_PREFIXES.get(asset_type, asset_type)
    stem = make_slug(Path(file_name).stem)
    candidate = f"{prefix}_{stem}"
    suffix = 2

    while candidate in existing_ids:
        candidate = f"{prefix}_{stem}_{suffix:02d}"
        suffix += 1

    existing_ids.add(candidate)
    return candidate


def build_asset_file_name(file_name: str, existing_names: set[str]) -> str:
    stem = sanitize_export_filename(Path(file_name).stem).lower()
    suffix = Path(file_name).suffix.lower() or ".dat"
    candidate = f"{stem}{suffix}"
    counter = 2

    while candidate in existing_names:
        candidate = f"{stem}_{counter:02d}{suffix}"
        counter += 1

    existing_names.add(candidate)
    return candidate


def display_asset_name(file_name: str) -> str:
    return Path(file_name).stem.replace("_", " ").replace("-", " ").strip() or Path(file_name).name


def decode_uploaded_file(file_item: dict) -> tuple[str, bytes]:
    file_name = file_item.get("name") or ""
    data_base64 = file_item.get("dataBase64") or ""

    if not file_name or not data_base64:
        raise ValueError("上传的文件里有名字或内容缺失的项目。")

    try:
        raw = base64.b64decode(data_base64.encode("utf-8"), validate=True)
    except Exception as error:  # pragma: no cover - defensive fallback
        raise ValueError(f"文件“{file_name}”不是有效的上传内容。") from error

    return file_name, raw


def choose_smart_asset_type(file_name: str, fallback_asset_type: str | None = None) -> str:
    ext = Path(file_name).suffix.lower()
    lower_file_name = file_name.lower()
    slug = make_slug(Path(file_name).stem)

    def has_any(*keywords: str) -> bool:
        return any(keyword in slug for keyword in keywords)

    if any(lower_file_name.endswith(suffix) for suffix in LIVE2D_EXTENSION_SUFFIXES):
        return "live2d"

    if ext in MODEL3D_EXTENSIONS:
        if fallback_asset_type == "scene3d" or has_any(
            "scene",
            "environment",
            "env",
            "level",
            "map",
            "world",
            "room",
            "stage",
            "street",
            "hallway",
            "classroom",
            "rooftop",
            "interior",
            "exterior",
        ):
            return "scene3d"
        return "model3d"

    if ext in VIDEO_EXTENSIONS:
        return "video"

    if ext in FONT_EXTENSIONS:
        return "font"

    if ext in AUDIO_EXTENSIONS:
        if has_any("voice", "cv", "line", "vo"):
            return "voice"
        if has_any("sfx", "se", "effect", "bell", "click", "hit"):
            return "sfx"
        if has_any("bgm", "music", "theme", "song"):
            return "bgm"
        if fallback_asset_type in {"bgm", "sfx", "voice"}:
            return fallback_asset_type
        return "bgm"

    if ext in IMAGE_EXTENSIONS:
        if has_any("ui", "button", "icon", "frame", "textbox", "nameplate"):
            return "ui"
        if has_any("sprite", "char", "character", "pose", "expression", "default", "smile", "shy", "sad"):
            return "sprite"
        if has_any("cg", "event", "still", "memory", "illustration"):
            return "cg"
        if has_any("bg", "background", "scene", "room", "hallway", "classroom", "rooftop", "street", "park"):
            return "background"
        if fallback_asset_type in {"background", "sprite", "cg", "ui"}:
            return fallback_asset_type
        return "background"

    if fallback_asset_type in ASSET_DIRECTORIES:
        return fallback_asset_type

    raise ValueError(f"文件“{file_name}”目前还无法自动判断素材类型。")


def is_replace_file_allowed_for_asset_type(asset_type: str, file_name: str) -> bool:
    clean_asset_type = str(asset_type or "").strip()
    lower_file_name = str(file_name or "").lower()
    ext = Path(lower_file_name).suffix.lower()

    if clean_asset_type == "live2d":
        return any(lower_file_name.endswith(suffix) for suffix in LIVE2D_EXTENSION_SUFFIXES)

    allowed_extensions = ASSET_REPLACE_EXTENSION_GROUPS.get(clean_asset_type)
    if allowed_extensions is None:
        return clean_asset_type in ASSET_DIRECTORIES

    return ext in allowed_extensions


def get_asset_replace_extension_hint(asset_type: str) -> str:
    return ASSET_REPLACE_EXTENSION_HINTS.get(str(asset_type or "").strip(), "与素材类型匹配的文件")


def normalize_asset_tags(tags: list[str] | str | None) -> list[str]:
    if isinstance(tags, str):
        raw_items = re.split(r"[\n,，、;；]+", tags)
    else:
        raw_items = tags or []

    seen: set[str] = set()
    normalized: list[str] = []
    for item in raw_items:
        clean = str(item or "").strip()
        if not clean or clean in seen:
            continue
        normalized.append(clean)
        seen.add(clean)
        if len(normalized) >= 20:
            break

    return normalized


def normalize_asset_rights_text(value: object, max_length: int) -> str:
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    text = re.sub(r"[ \t]+", " ", text)
    return text[:max_length].strip()


def normalize_asset_commercial_use(value: object) -> str:
    text = str(value or "").strip().lower()
    if text in {"allowed", "commercial", "yes", "true", "可商用", "允许商用"}:
        return ASSET_COMMERCIAL_USE_LABELS["allowed"]
    if text in {"forbidden", "noncommercial", "no", "false", "不可商用", "禁止商用", "非商用"}:
        return ASSET_COMMERCIAL_USE_LABELS["forbidden"]
    return ASSET_COMMERCIAL_USE_LABELS["unknown"]


def normalize_asset_rights_metadata(payload: object) -> dict:
    if not isinstance(payload, dict):
        return {}

    normalized: dict[str, object] = {}
    for field, max_length in ASSET_RIGHTS_TEXT_LIMITS.items():
        if field in payload:
            text = normalize_asset_rights_text(payload.get(field), max_length)
            if text:
                normalized[field] = text

    if "commercialUse" in payload:
        normalized["commercialUse"] = normalize_asset_commercial_use(payload.get("commercialUse"))

    for field in ASSET_RIGHTS_BOOLEAN_FIELDS:
        if field in payload:
            normalized[field] = bool(payload.get(field))

    return normalized


def apply_asset_rights_metadata(asset: dict, payload: object) -> None:
    if not isinstance(payload, dict):
        return

    normalized = normalize_asset_rights_metadata(payload)
    for field in ASSET_RIGHTS_TEXT_LIMITS:
        if field in payload:
            if field in normalized:
                asset[field] = normalized[field]
            else:
                asset.pop(field, None)

    if "commercialUse" in payload:
        asset["commercialUse"] = normalized.get("commercialUse", ASSET_COMMERCIAL_USE_LABELS["unknown"])

    for field in ASSET_RIGHTS_BOOLEAN_FIELDS:
        if field in payload:
            asset[field] = bool(normalized.get(field, False))


def delete_asset_file_if_unused(relative_path: str, assets: list[dict], skip_asset_id: str | None = None) -> bool:
    normalized = str(relative_path or "").strip()
    if not normalized:
        return False

    if any(
        asset.get("id") != skip_asset_id and asset.get("path") == normalized
        for asset in assets
    ):
        return False

    asset_file = TEMPLATE_DIR / normalized
    if asset_file.is_file():
        asset_file.unlink()
        return True

    return False


def collect_asset_usages(asset_id: str) -> list[str]:
    bundle = load_project_bundle()
    characters = bundle.get("characters", {}).get("characters", [])
    characters_by_id = {character.get("id"): character for character in characters}
    usages: list[str] = []

    def add_usage(candidate_asset_id: str | None, label: str) -> None:
        if candidate_asset_id == asset_id:
            usages.append(label)

    for character in characters:
        add_usage(character.get("defaultSpriteId"), f"角色默认立绘：{character.get('displayName')}")
        for presentation_asset_id, label in collect_character_presentation_asset_ids(character):
            if label.startswith("差分图层："):
                expression_name = label.split("：", 1)[1]
                add_usage(presentation_asset_id, f"角色差分图层：{character.get('displayName')} / {expression_name}")
            else:
                add_usage(presentation_asset_id, f"角色{label}：{character.get('displayName')}")
        for expression in character.get("expressions", []):
            add_usage(
                expression.get("spriteAssetId"),
                f"角色表情：{character.get('displayName')} / {expression.get('name')}",
            )

    for chapter in bundle.get("chapters", []):
        for scene in chapter.get("scenes", []):
            for block in scene.get("blocks", []):
                add_usage(
                    block.get("assetId"),
                    f"场景：{scene.get('name')} / {BLOCK_LABELS.get(block.get('type'), block.get('type'))}",
                )
                add_usage(block.get("voiceAssetId"), f"场景：{scene.get('name')} / 台词语音")
                if block.get("type") in {"dialogue", "character_show"}:
                    character_id = block.get("speakerId") or block.get("characterId")
                    expression_id = block.get("expressionId")
                    character = characters_by_id.get(character_id)
                    expression = next(
                        (
                            item
                            for item in character.get("expressions", [])
                            if item.get("id") == expression_id
                        ),
                        None,
                    ) if character else None
                    add_usage(
                        expression.get("spriteAssetId") if expression else None,
                        f"场景：{scene.get('name')} / {character.get('displayName') if character else character_id} {expression.get('name') if expression else ''}".strip(),
                    )

    return usages


def import_assets(asset_type: str, files: list[dict], fallback_asset_type: str | None = None) -> dict:
    if asset_type != "auto" and asset_type not in ASSET_DIRECTORIES:
        raise ValueError("请先选一个正确的素材分类，再继续导入。")

    if not files:
        raise ValueError("这次没有收到要导入的文件。")

    assets_path = DATA_DIR / "assets.json"
    assets_doc = read_json(assets_path)
    assets = assets_doc.setdefault("assets", [])
    existing_ids = {asset.get("id") for asset in assets if asset.get("id")}
    existing_names_by_type: dict[str, set[str]] = {}
    imported_assets = []
    grouped_counts: dict[str, int] = {}
    pending_files: list[tuple[str, bytes, str]] = []
    invalid_files: list[tuple[str, str, str]] = []
    written_paths: list[Path] = []

    for file_item in files:
        file_name, raw = decode_uploaded_file(file_item)
        resolved_asset_type = (
            choose_smart_asset_type(file_name, fallback_asset_type)
            if asset_type == "auto"
            else asset_type
        )
        if asset_type != "auto" and not is_replace_file_allowed_for_asset_type(resolved_asset_type, file_name):
            type_label = ASSET_TYPE_LABELS.get(str(resolved_asset_type or ""), str(resolved_asset_type or "素材"))
            extension_hint = get_asset_replace_extension_hint(resolved_asset_type)
            invalid_files.append((file_name, type_label, extension_hint))
            continue
        pending_files.append((file_name, raw, resolved_asset_type))

    if invalid_files:
        _, type_label, extension_hint = invalid_files[0]
        preview_names = [file_name for file_name, _, _ in invalid_files[:8]]
        preview = "\n".join(f"- {file_name}" for file_name in preview_names)
        hidden_count = len(invalid_files) - len(preview_names)
        hidden_text = f"\n- 还有 {hidden_count} 个文件未展开" if hidden_count > 0 else ""
        raise ValueError(
            f"不能将以下文件作为{type_label}素材导入：\n{preview}{hidden_text}\n"
            f"请上传 {extension_hint}，或使用智能导入自动分类。"
        )

    try:
        for file_name, raw, resolved_asset_type in pending_files:
            target_relative_dir = ASSET_DIRECTORIES[resolved_asset_type]
            target_dir = TEMPLATE_DIR / target_relative_dir
            target_dir.mkdir(parents=True, exist_ok=True)
            existing_names = existing_names_by_type.setdefault(
                resolved_asset_type,
                {path.name for path in target_dir.glob("*") if path.is_file()},
            )
            output_name = build_asset_file_name(file_name, existing_names)
            output_path = target_dir / output_name
            written_paths.append(output_path)
            output_path.write_bytes(raw)
            asset_id = build_asset_id(resolved_asset_type, file_name, existing_ids)
            asset_record = {
                "id": asset_id,
                "type": resolved_asset_type,
                "name": display_asset_name(file_name),
                "path": (target_relative_dir / output_name).as_posix(),
                "tags": [],
                "favorite": False,
            }
            assets.append(asset_record)
            imported_assets.append(enrich_asset_record(asset_record))
            grouped_counts[resolved_asset_type] = grouped_counts.get(resolved_asset_type, 0) + 1

        write_json(assets_path, assets_doc)
    except Exception:
        for written_path in reversed(written_paths):
            try:
                written_path.unlink(missing_ok=True)
            except OSError:
                pass
        raise

    touch_project()
    return {
        "assetType": imported_assets[0]["type"] if imported_assets else fallback_asset_type or asset_type,
        "importedCount": len(imported_assets),
        "assets": imported_assets,
        "groupedCounts": grouped_counts,
    }


def generate_openai_asset(payload: dict) -> dict:
    asset_type = normalize_openai_asset_generation_type(payload.get("assetType"))
    character_binding = normalize_openai_asset_character_binding(payload.get("characterBinding"), asset_type)
    image_bytes, generation_meta = call_openai_asset_generation_model(payload, asset_type)
    output_format = generation_meta["outputFormat"]
    extension = ".jpg" if output_format == "jpeg" else f".{output_format}"
    asset_name = (
        str(payload.get("assetName") or "").strip()[:80]
        or f"AI 生成{ASSET_TYPE_LABELS.get(asset_type, '素材')}"
    )

    assets_path = DATA_DIR / "assets.json"
    characters_path = DATA_DIR / "characters.json"
    assets_doc = read_json(assets_path)
    assets_doc_before = json.loads(json.dumps(assets_doc, ensure_ascii=False))
    characters_doc_before = read_json(characters_path) if character_binding else None
    assets = assets_doc.setdefault("assets", [])
    existing_ids = {asset.get("id") for asset in assets if asset.get("id")}
    target_relative_dir = ASSET_DIRECTORIES[asset_type]
    target_dir = TEMPLATE_DIR / target_relative_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    existing_names = {path.name for path in target_dir.glob("*") if path.is_file()}
    output_name = build_asset_file_name(f"{asset_name}{extension}", existing_names)
    output_path = target_dir / output_name
    output_path.write_bytes(image_bytes)

    tags = normalize_asset_tags(
        [
            "AI生成",
            "OpenAI",
            ASSET_TYPE_LABELS.get(asset_type, asset_type),
            generation_meta["model"],
        ]
    )
    asset_record = {
        "id": build_asset_id(asset_type, output_name, existing_ids),
        "type": asset_type,
        "name": asset_name,
        "path": (target_relative_dir / output_name).as_posix(),
        "tags": tags,
        "favorite": False,
        "source": {
            "kind": "openai_image_generation",
            "model": generation_meta["model"],
            "size": generation_meta["size"],
            "quality": generation_meta["quality"],
            "background": generation_meta["background"],
            "outputFormat": generation_meta["outputFormat"],
            "promptPreview": generation_meta["prompt"][:220],
        },
    }

    binding_result = None
    try:
        assets.append(asset_record)
        write_json(assets_path, assets_doc)
        if character_binding:
            binding_result = bind_sprite_asset_to_character(asset_record["id"], character_binding)
        touch_project()
    except Exception:
        try:
            output_path.unlink(missing_ok=True)
        except OSError:
            pass
        try:
            write_json(assets_path, assets_doc_before)
        except Exception:
            pass
        if characters_doc_before is not None:
            try:
                write_json(characters_path, characters_doc_before)
            except Exception:
                pass
        raise

    result = {
        "assetType": asset_type,
        "asset": enrich_asset_record(asset_record),
        "model": generation_meta["model"],
        "size": generation_meta["size"],
        "quality": generation_meta["quality"],
        "background": generation_meta["background"],
        "outputFormat": generation_meta["outputFormat"],
        "privacy": {
            "sentToExternalService": True,
            "apiKeyStored": False,
            "message": "API Key 只随本次请求发送给 OpenAI，没有写入项目文件或素材元数据。",
        },
    }
    if binding_result:
        result["characterBinding"] = binding_result
    return result


def normalize_openai_asset_character_binding(payload: object, asset_type: str) -> dict | None:
    if not isinstance(payload, dict):
        return None

    character_id = str(payload.get("characterId") or "").strip()
    if not character_id:
        return None
    if asset_type != "sprite":
        raise ValueError("只有立绘素材可以在生成后绑定到角色表情。")

    characters_doc = normalize_characters_document(read_json(DATA_DIR / "characters.json"))
    characters = characters_doc.get("characters", [])
    character = next((item for item in characters if item.get("id") == character_id), None)
    if not character:
        raise ValueError("没有找到要绑定立绘的角色。")

    expression_name = str(payload.get("expressionName") or "").strip()[:40] or "默认"
    expression_id = str(payload.get("expressionId") or "").strip()
    existing_expression_ids = {
        str(expression.get("id") or "").strip()
        for expression in character.get("expressions", []) or []
        if str(expression.get("id") or "").strip()
    }
    if not expression_id:
        expression_id = build_unique_slug_id(existing_expression_ids, "expr", expression_name)

    return {
        "characterId": character_id,
        "expressionId": expression_id[:80],
        "expressionName": expression_name,
        "setAsDefaultSprite": bool(payload.get("setAsDefaultSprite", True)),
    }


def bind_sprite_asset_to_character(asset_id: str, binding: dict) -> dict:
    clean_asset_id = str(asset_id or "").strip()
    if not clean_asset_id:
        raise ValueError("绑定角色表情时缺少 sprite 素材。")

    assets_doc = normalize_assets_document(read_json(DATA_DIR / "assets.json"))
    asset = next((item for item in assets_doc.get("assets", []) if item.get("id") == clean_asset_id), None)
    if not asset or asset.get("type") != "sprite":
        raise ValueError("只能把立绘素材绑定到角色表情。")

    characters_path = DATA_DIR / "characters.json"
    characters_doc = normalize_characters_document(read_json(characters_path))
    characters = characters_doc.setdefault("characters", [])
    character = next((item for item in characters if item.get("id") == binding.get("characterId")), None)
    if not character:
        raise ValueError("没有找到要绑定立绘的角色。")

    expressions = character.setdefault("expressions", [])
    expression_id = str(binding.get("expressionId") or "").strip()
    expression_name = str(binding.get("expressionName") or "").strip() or expression_id or "默认"
    expression = next((item for item in expressions if item.get("id") == expression_id), None)
    if not expression:
        existing_expression_ids = {
            str(item.get("id") or "").strip()
            for item in expressions
            if str(item.get("id") or "").strip()
        }
        if not expression_id or expression_id in existing_expression_ids:
            expression_id = build_unique_slug_id(existing_expression_ids, "expr", expression_name)
        expression = {
            "id": expression_id,
            "name": expression_name,
            "spriteAssetId": clean_asset_id,
            "layerAssetIds": [],
            "live2dExpression": "",
            "live2dMotion": "",
            "model3dExpression": "",
            "model3dAnimation": "",
        }
        expressions.append(expression)
    else:
        expression["name"] = expression_name
        expression["spriteAssetId"] = clean_asset_id

    set_as_default = bool(binding.get("setAsDefaultSprite")) or not str(character.get("defaultSpriteId") or "").strip()
    if set_as_default:
        character["defaultSpriteId"] = clean_asset_id
        presentation = normalize_character_presentation(character.get("presentation"), clean_asset_id)
        presentation["fallbackSpriteAssetId"] = clean_asset_id
        character["presentation"] = presentation

    write_json(characters_path, characters_doc)
    return {
        "characterId": character["id"],
        "characterName": character.get("displayName") or character["id"],
        "expressionId": expression["id"],
        "expressionName": expression.get("name") or expression["id"],
        "assetId": clean_asset_id,
        "setAsDefaultSprite": set_as_default,
    }


def replace_asset_file(asset_id: str, file_item: dict) -> dict:
    if not asset_id:
        raise ValueError("替换素材时缺少 assetId。")

    assets_path = DATA_DIR / "assets.json"
    assets_doc = read_json(assets_path)
    assets = assets_doc.setdefault("assets", [])
    asset = next((item for item in assets if item.get("id") == asset_id), None)
    if not asset:
        raise ValueError("没有找到要替换的素材。")

    file_name, raw = decode_uploaded_file(file_item)
    asset_type = asset.get("type")
    target_relative_dir = ASSET_DIRECTORIES.get(asset_type)
    if not target_relative_dir:
        raise ValueError("这个素材类型暂时不支持替换文件。")
    if not is_replace_file_allowed_for_asset_type(asset_type, file_name):
        type_label = ASSET_TYPE_LABELS.get(str(asset_type or ""), str(asset_type or "素材"))
        extension_hint = get_asset_replace_extension_hint(asset_type)
        raise ValueError(
            f"不能用“{file_name}”替换{type_label}素材。请上传 {extension_hint}。"
        )

    target_dir = TEMPLATE_DIR / target_relative_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    current_file_name = Path(asset.get("path", "")).name
    existing_names = {
        path.name
        for path in target_dir.glob("*")
        if path.is_file() and path.name != current_file_name
    }
    output_name = build_asset_file_name(file_name, existing_names)
    output_path = target_dir / output_name
    output_path.write_bytes(raw)

    previous_path = asset.get("path", "")
    asset["path"] = (target_relative_dir / output_name).as_posix()
    write_json(assets_path, assets_doc)
    removed_old_file = False
    if previous_path != asset["path"]:
        removed_old_file = delete_asset_file_if_unused(previous_path, assets, skip_asset_id=asset_id)

    touch_project()
    return {
        "asset": enrich_asset_record(asset),
        "removedOldFile": removed_old_file,
    }


def update_asset_metadata(
    asset_id: str,
    name: str | None = None,
    tags: list[str] | str | None = None,
    favorite: bool | None = None,
    rights: object | None = None,
) -> dict:
    if not asset_id:
        raise ValueError("保存素材信息时缺少 assetId。")

    assets_path = DATA_DIR / "assets.json"
    assets_doc = read_json(assets_path)
    assets = assets_doc.setdefault("assets", [])
    asset = next((item for item in assets if item.get("id") == asset_id), None)
    if not asset:
        raise ValueError("没有找到要保存的素材。")

    if name is not None:
        clean_name = str(name or "").strip()
        if not clean_name:
            raise ValueError("素材名称不能为空。")
        asset["name"] = clean_name

    if tags is not None:
        asset["tags"] = normalize_asset_tags(tags)

    if favorite is not None:
        asset["favorite"] = bool(favorite)

    if rights is not None:
        apply_asset_rights_metadata(asset, rights)

    write_json(assets_path, assets_doc)
    touch_project()
    return {
        "asset": enrich_asset_record(asset),
    }


def update_character_presentation(
    character_id: str,
    presentation_payload: object,
    expression_bindings_payload: object | None = None,
) -> dict:
    if not character_id:
        raise ValueError("保存角色表现配置时缺少 characterId。")

    characters_path = DATA_DIR / "characters.json"
    characters_doc = normalize_characters_document(read_json(characters_path))
    characters = characters_doc.setdefault("characters", [])
    character = next((item for item in characters if item.get("id") == character_id), None)
    if not character:
        raise ValueError("没有找到要保存的角色。")

    character["presentation"] = normalize_character_presentation(
        presentation_payload,
        str(character.get("defaultSpriteId") or ""),
    )
    if isinstance(expression_bindings_payload, list):
        bindings_by_id = {
            str(binding.get("expressionId") or "").strip(): binding
            for binding in expression_bindings_payload
            if isinstance(binding, dict) and str(binding.get("expressionId") or "").strip()
        }
        for expression in character.get("expressions", []) or []:
            binding = bindings_by_id.get(str(expression.get("id") or ""))
            if not binding:
                continue
            expression["layerAssetIds"] = normalize_text_list(binding.get("layerAssetIds"))
            expression["live2dExpression"] = str(binding.get("live2dExpression") or "").strip()
            expression["live2dMotion"] = str(binding.get("live2dMotion") or "").strip()
            expression["model3dExpression"] = str(binding.get("model3dExpression") or "").strip()
            expression["model3dAnimation"] = str(binding.get("model3dAnimation") or "").strip()
    write_json(characters_path, characters_doc)
    touch_project()
    return {"character": character}


def create_voice_placeholder(scene_id: str, block_id: str, preferred_name: str | None = None) -> dict:
    clean_scene_id = str(scene_id or "").strip()
    clean_block_id = str(block_id or "").strip()

    if not clean_scene_id or not clean_block_id:
        raise ValueError("生成语音条目时缺少 sceneId 或 blockId。")

    assets_path = DATA_DIR / "assets.json"
    characters_doc = read_json(DATA_DIR / "characters.json")
    characters_by_id = {
        character.get("id"): character for character in characters_doc.get("characters", []) if character.get("id")
    }
    assets_doc = read_json(assets_path)
    assets = assets_doc.setdefault("assets", [])
    existing_asset_ids = {asset.get("id") for asset in assets if asset.get("id")}
    voice_dir = TEMPLATE_DIR / ASSET_DIRECTORIES["voice"]
    voice_dir.mkdir(parents=True, exist_ok=True)
    existing_file_names = {path.name for path in voice_dir.glob("*") if path.is_file()}

    for chapter_path in list_chapter_files():
        chapter = read_json(chapter_path)
        for scene in chapter.get("scenes", []):
            if scene.get("id") != clean_scene_id:
                continue

            for block_index, block in enumerate(scene.get("blocks", [])):
                if block.get("id") != clean_block_id:
                    continue

                if block.get("type") != "dialogue":
                    raise ValueError("只有台词卡片才能直接生成语音条目。")

                existing_voice_asset_id = str(block.get("voiceAssetId") or "").strip()
                if existing_voice_asset_id:
                    existing_asset = next(
                        (asset for asset in assets if asset.get("id") == existing_voice_asset_id),
                        None,
                    )
                    return {
                        "asset": enrich_asset_record(existing_asset) if existing_asset else None,
                        "assetId": existing_voice_asset_id,
                        "alreadyBound": True,
                        "sceneId": clean_scene_id,
                        "blockId": clean_block_id,
                        "chapterId": chapter.get("chapterId"),
                        "blockIndex": block_index,
                    }

                speaker_id = block.get("speakerId")
                speaker_name = (
                    characters_by_id.get(speaker_id, {}).get("displayName")
                    or speaker_id
                    or "未命名角色"
                )
                chapter_name = chapter.get("name") or chapter.get("chapterId") or "未命名章节"
                scene_name = scene.get("name") or clean_scene_id
                base_display_name = (
                    str(preferred_name or "").strip()
                    or f"{speaker_name}_{chapter_name}_{scene_name}_{block_index + 1:03d}"
                )
                asset_file_name = build_asset_file_name(f"{base_display_name}.wav", existing_file_names)
                asset_id = build_asset_id("voice", asset_file_name, existing_asset_ids)
                asset_record = {
                    "id": asset_id,
                    "type": "voice",
                    "name": base_display_name,
                    "path": (ASSET_DIRECTORIES["voice"] / asset_file_name).as_posix(),
                    "tags": normalize_asset_tags(
                        ["语音占位", "待录音", speaker_name, chapter_name, scene_name]
                    ),
                    "favorite": False,
                }
                assets.append(asset_record)
                block["voiceAssetId"] = asset_id
                write_json(assets_path, assets_doc)
                write_json(chapter_path, chapter)
                touch_project()
                return {
                    "asset": enrich_asset_record(asset_record),
                    "assetId": asset_id,
                    "alreadyBound": False,
                    "sceneId": clean_scene_id,
                    "blockId": clean_block_id,
                    "chapterId": chapter.get("chapterId"),
                    "blockIndex": block_index,
                    "speakerName": speaker_name,
                    "sceneName": scene_name,
                    "chapterName": chapter_name,
                }

            raise ValueError("没有找到要绑定语音的那张台词卡片。")

    raise ValueError("没有找到对应场景，暂时没法生成语音条目。")


def create_voice_placeholders(items: list[dict], preferred_name: str | None = None) -> dict:
    unique_pairs: list[tuple[str, str]] = []
    seen_pairs: set[tuple[str, str]] = set()

    for item in items or []:
        scene_id = str((item or {}).get("sceneId") or "").strip()
        block_id = str((item or {}).get("blockId") or "").strip()
        if not scene_id or not block_id:
            continue
        pair = (scene_id, block_id)
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        unique_pairs.append(pair)

    if not unique_pairs:
        raise ValueError("这次没有收到可生成语音条目的台词列表。")

    assets: list[dict] = []
    created_count = 0
    already_bound_count = 0

    for scene_id, block_id in unique_pairs:
        result = create_voice_placeholder(scene_id, block_id, preferred_name)
        asset = result.get("asset")
        if asset:
            assets.append(asset)
        if result.get("alreadyBound"):
            already_bound_count += 1
        else:
            created_count += 1

    return {
        "assets": assets,
        "createdCount": created_count,
        "alreadyBoundCount": already_bound_count,
        "totalCount": len(unique_pairs),
    }


def asset_has_real_file(asset: dict) -> bool:
    relative_path = str(asset.get("path") or "").strip()
    return bool(relative_path and (TEMPLATE_DIR / relative_path).is_file())


def tokenize_match_slug(value: str) -> list[str]:
    slug = make_slug(value)
    return [token for token in slug.split("_") if token]


def score_voice_match_slug(file_slug: str, candidate_slug: str) -> int:
    clean_file_slug = str(file_slug or "").strip()
    clean_candidate_slug = str(candidate_slug or "").strip()
    if not clean_file_slug or not clean_candidate_slug:
        return 0

    if clean_file_slug == clean_candidate_slug:
        return 140

    score = 0
    if clean_file_slug in clean_candidate_slug or clean_candidate_slug in clean_file_slug:
        score = max(score, 108)

    ratio = SequenceMatcher(None, clean_file_slug, clean_candidate_slug).ratio()
    score = max(score, int(ratio * 92))

    file_tokens = tokenize_match_slug(clean_file_slug)
    candidate_tokens = tokenize_match_slug(clean_candidate_slug)
    if file_tokens and candidate_tokens:
        overlap_count = len(set(file_tokens) & set(candidate_tokens))
        if overlap_count:
            overlap_ratio = overlap_count / max(len(file_tokens), len(candidate_tokens))
            score = max(score, int(overlap_ratio * 118))
            if file_tokens == candidate_tokens:
                score = max(score, 132)

    return score


def score_voice_file_against_asset(file_slug: str, asset: dict) -> tuple[int, str]:
    best_score = 0
    best_basis = ""
    candidate_slugs = [
        ("素材名", make_slug(asset.get("name") or "")),
        ("素材 id", make_slug(asset.get("id") or "")),
        ("路径名", make_slug(Path(str(asset.get("path") or "")).stem)),
    ]

    for basis, candidate_slug in candidate_slugs:
        score = score_voice_match_slug(file_slug, candidate_slug)
        if score > best_score:
            best_score = score
            best_basis = basis

    return best_score, best_basis


def build_voice_placeholder_candidates(assets: list[dict], asset_ids: list[str] | None = None) -> list[dict]:
    assets_by_id = {asset.get("id"): asset for asset in assets if asset.get("id")}
    requested_ids: list[str] = []
    seen_ids: set[str] = set()

    for asset_id in asset_ids or []:
        clean_id = str(asset_id or "").strip()
        if not clean_id or clean_id in seen_ids:
            continue
        requested_ids.append(clean_id)
        seen_ids.add(clean_id)

    if requested_ids:
        return [
            assets_by_id[asset_id]
            for asset_id in requested_ids
            if asset_id in assets_by_id
            and assets_by_id[asset_id].get("type") == "voice"
            and not asset_has_real_file(assets_by_id[asset_id])
        ]

    return [
        asset
        for asset in assets
        if asset.get("type") == "voice" and not asset_has_real_file(asset)
    ]


def match_voice_files_to_placeholders(files: list[dict], asset_ids: list[str] | None = None) -> dict:
    if not files:
        raise ValueError("这次没有收到要匹配的语音文件。")

    assets_path = DATA_DIR / "assets.json"
    assets_doc = read_json(assets_path)
    assets = assets_doc.setdefault("assets", [])
    candidate_assets = build_voice_placeholder_candidates(assets, asset_ids)

    if not candidate_assets:
        raise ValueError("当前没有可匹配的待导入语音占位条目。")

    voice_dir = TEMPLATE_DIR / ASSET_DIRECTORIES["voice"]
    voice_dir.mkdir(parents=True, exist_ok=True)
    existing_file_names = {path.name for path in voice_dir.glob("*") if path.is_file()}
    candidate_assets_by_id = {asset.get("id"): asset for asset in candidate_assets if asset.get("id")}

    prepared_files: list[dict] = []
    unmatched_files: list[dict] = []

    for file_item in files:
        file_name, raw = decode_uploaded_file(file_item)
        if Path(file_name).suffix.lower() not in AUDIO_EXTENSIONS:
            unmatched_files.append(
                {
                    "fileName": file_name,
                    "reason": "这个文件不是支持的语音格式，暂时只能匹配 mp3 / wav / ogg / m4a 等音频。",
                }
            )
            continue

        file_slug = make_slug(Path(file_name).stem)
        candidate_scores = []
        for asset in candidate_assets:
            score, basis = score_voice_file_against_asset(file_slug, asset)
            if score <= 0:
                continue
            candidate_scores.append(
                {
                    "assetId": asset.get("id"),
                    "score": score,
                    "basis": basis,
                    "assetName": asset.get("name") or asset.get("id") or "未命名语音",
                }
            )

        candidate_scores.sort(
            key=lambda item: (item.get("score") or 0, item.get("assetName") or ""),
            reverse=True,
        )
        prepared_files.append(
            {
                "fileName": file_name,
                "raw": raw,
                "fileSlug": file_slug,
                "candidateScores": candidate_scores,
            }
        )

    prepared_files.sort(
        key=lambda item: item["candidateScores"][0]["score"] if item["candidateScores"] else -1,
        reverse=True,
    )

    used_asset_ids: set[str] = set()
    matched_assets: list[dict] = []
    matched_results: list[dict] = []
    ambiguous_files: list[dict] = []

    for prepared in prepared_files:
        available_candidates = [
            candidate
            for candidate in prepared["candidateScores"]
            if candidate.get("assetId") not in used_asset_ids
        ]

        if not available_candidates:
            unmatched_files.append(
                {
                    "fileName": prepared["fileName"],
                    "reason": "这批占位条目里已经没有剩余候选可匹配了。",
                }
            )
            continue

        top_candidate = available_candidates[0]
        second_candidate = available_candidates[1] if len(available_candidates) > 1 else None

        if (top_candidate.get("score") or 0) < 60:
            unmatched_files.append(
                {
                    "fileName": prepared["fileName"],
                    "reason": "没有找到名字足够接近的语音占位条目，建议检查文件名是不是和占位条目接近。",
                }
            )
            continue

        if (
            second_candidate
            and (second_candidate.get("score") or 0) >= 60
            and abs((top_candidate.get("score") or 0) - (second_candidate.get("score") or 0)) < 8
        ):
            ambiguous_files.append(
                {
                    "fileName": prepared["fileName"],
                    "candidates": [
                        {
                            "assetId": candidate.get("assetId"),
                            "assetName": candidate.get("assetName"),
                            "score": candidate.get("score"),
                        }
                        for candidate in available_candidates[:3]
                    ],
                    "reason": "有不止一个语音占位条目都很像这个文件名，暂时不敢自动乱绑。",
                }
            )
            continue

        asset_id = top_candidate.get("assetId")
        asset = candidate_assets_by_id.get(asset_id)
        if not asset:
            unmatched_files.append(
                {
                    "fileName": prepared["fileName"],
                    "reason": "匹配到的语音占位条目暂时找不到了，请再试一次。",
                }
            )
            continue

        current_file_name = Path(str(asset.get("path") or "")).name
        if current_file_name and current_file_name in existing_file_names and not (voice_dir / current_file_name).is_file():
            existing_file_names.discard(current_file_name)

        preferred_output_name = prepared["fileName"]
        current_path_name = Path(str(asset.get("path") or "")).name
        current_path_stem = sanitize_export_filename(Path(current_path_name).stem).lower()
        current_upload_suffix = Path(prepared["fileName"]).suffix.lower() or ".dat"
        if current_path_stem:
            preferred_output_name = f"{current_path_stem}{current_upload_suffix}"

        output_name = build_asset_file_name(preferred_output_name, existing_file_names)
        output_path = voice_dir / output_name
        output_path.write_bytes(prepared["raw"])

        previous_path = str(asset.get("path") or "").strip()
        asset["path"] = (ASSET_DIRECTORIES["voice"] / output_name).as_posix()
        current_tags = [
            tag for tag in normalize_asset_tags(asset.get("tags"))
            if tag not in {"语音占位", "待录音"}
        ]
        asset["tags"] = normalize_asset_tags(current_tags + ["已导入语音"])

        removed_old_file = False
        if previous_path and previous_path != asset["path"]:
            removed_old_file = delete_asset_file_if_unused(previous_path, assets, skip_asset_id=asset_id)

        used_asset_ids.add(asset_id)
        matched_asset = enrich_asset_record(asset)
        matched_assets.append(matched_asset)
        matched_results.append(
            {
                "fileName": prepared["fileName"],
                "assetId": asset_id,
                "assetName": asset.get("name") or asset_id,
                "score": top_candidate.get("score"),
                "matchedBy": top_candidate.get("basis"),
                "removedOldFile": removed_old_file,
                "asset": matched_asset,
            }
        )

    if matched_results:
        write_json(assets_path, assets_doc)
        touch_project()

    return {
        "assets": matched_assets,
        "matches": matched_results,
        "matchedCount": len(matched_results),
        "candidateCount": len(candidate_assets),
        "requestedFileCount": len(files),
        "unmatchedFiles": unmatched_files,
        "ambiguousFiles": ambiguous_files,
    }


def bulk_update_asset_tags(asset_ids: list[str], mode: str, tags: list[str] | str | None) -> dict:
    unique_asset_ids = []
    seen_ids: set[str] = set()
    for asset_id in asset_ids or []:
        clean_id = str(asset_id or "").strip()
        if not clean_id or clean_id in seen_ids:
            continue
        unique_asset_ids.append(clean_id)
        seen_ids.add(clean_id)

    if not unique_asset_ids:
        raise ValueError("当前筛选结果里没有可批量处理的素材。")

    normalized_tags = normalize_asset_tags(tags)
    if not normalized_tags:
        raise ValueError("批量改标签时至少要提供一个标签。")

    if mode not in {"add", "remove"}:
        raise ValueError("批量改标签的模式不正确。")

    assets_path = DATA_DIR / "assets.json"
    assets_doc = read_json(assets_path)
    assets = assets_doc.setdefault("assets", [])
    updated_count = 0

    for asset in assets:
        if asset.get("id") not in seen_ids:
            continue

        current_tags = normalize_asset_tags(asset.get("tags"))
        if mode == "add":
            asset["tags"] = normalize_asset_tags(current_tags + normalized_tags)
        else:
            remove_set = set(normalized_tags)
            asset["tags"] = [tag for tag in current_tags if tag not in remove_set]
        updated_count += 1

    if updated_count == 0:
        raise ValueError("没有找到可以批量处理的素材。")

    write_json(assets_path, assets_doc)
    touch_project()
    return {
        "updatedCount": updated_count,
        "mode": mode,
        "tags": normalized_tags,
    }


def bulk_delete_assets(asset_ids: list[str]) -> dict:
    unique_asset_ids = []
    seen_ids: set[str] = set()
    for asset_id in asset_ids or []:
        clean_id = str(asset_id or "").strip()
        if not clean_id or clean_id in seen_ids:
            continue
        unique_asset_ids.append(clean_id)
        seen_ids.add(clean_id)

    if not unique_asset_ids:
        raise ValueError("当前没有收到要批量删除的素材。")

    assets_path = DATA_DIR / "assets.json"
    assets_doc = read_json(assets_path)
    assets = assets_doc.setdefault("assets", [])
    assets_by_id = {asset.get("id"): asset for asset in assets if asset.get("id")}
    deletable_ids: set[str] = set()
    skipped_used: list[dict] = []
    missing_ids: list[str] = []

    for asset_id in unique_asset_ids:
        asset = assets_by_id.get(asset_id)
        if not asset:
            missing_ids.append(asset_id)
            continue

        usages = collect_asset_usages(asset_id)
        if usages:
            skipped_used.append(
                {
                    "id": asset_id,
                    "name": asset.get("name") or asset_id,
                    "usageCount": len(usages),
                    "usages": usages[:8],
                }
            )
            continue

        deletable_ids.add(asset_id)

    remaining_assets = [asset for asset in assets if asset.get("id") not in deletable_ids]
    removed_file_count = 0
    deleted_asset_names: list[str] = []
    for asset in assets:
        if asset.get("id") not in deletable_ids:
            continue
        deleted_asset_names.append(asset.get("name") or asset.get("id") or "未命名素材")
        if delete_asset_file_if_unused(asset.get("path", ""), remaining_assets):
            removed_file_count += 1

    if deletable_ids:
        assets_doc["assets"] = remaining_assets
        write_json(assets_path, assets_doc)
        touch_project()

    return {
        "deletedCount": len(deletable_ids),
        "deletedAssetIds": [asset_id for asset_id in unique_asset_ids if asset_id in deletable_ids],
        "deletedAssetNames": deleted_asset_names,
        "removedFileCount": removed_file_count,
        "skippedUsedCount": len(skipped_used),
        "skippedUsed": skipped_used,
        "missingIds": missing_ids,
    }


def delete_asset(asset_id: str) -> dict:
    if not asset_id:
        raise ValueError("删除素材时缺少 assetId。")

    assets_path = DATA_DIR / "assets.json"
    assets_doc = read_json(assets_path)
    assets = assets_doc.setdefault("assets", [])
    asset_index = next((index for index, item in enumerate(assets) if item.get("id") == asset_id), -1)
    if asset_index < 0:
        raise ValueError("没有找到要删除的素材。")

    usages = collect_asset_usages(asset_id)
    if usages:
        raise ValueError("这个素材还在被使用，请先解除引用再删除。")

    asset = assets.pop(asset_index)
    removed_file = delete_asset_file_if_unused(asset.get("path", ""), assets)
    write_json(assets_path, assets_doc)
    touch_project()
    return {
        "deletedAssetId": asset_id,
        "assetType": asset.get("type"),
        "removedFile": removed_file,
    }


def create_scene(chapter_id: str, scene_name: str, after_scene_id: str | None = None) -> dict:
    clean_name = (scene_name or "").strip()
    if not clean_name:
        raise ValueError("新场景至少要有一个名字。")

    _, existing_scene_ids = collect_existing_ids()
    new_scene_id = next_generated_id(existing_scene_ids, "scene")
    new_scene = build_starter_scene(new_scene_id, clean_name)

    for chapter_path in list_chapter_files():
        chapter = read_json(chapter_path)

        if chapter.get("chapterId") != chapter_id:
            continue

        scenes = chapter.setdefault("scenes", [])
        scene_order = chapter.setdefault("sceneOrder", [scene.get("id") for scene in scenes if scene.get("id")])

        insert_index = len(scene_order)
        if after_scene_id and after_scene_id in scene_order:
            insert_index = scene_order.index(after_scene_id) + 1

        scene_order.insert(insert_index, new_scene_id)

        scene_insert_index = len(scenes)
        if after_scene_id:
            for index, scene in enumerate(scenes):
                if scene.get("id") == after_scene_id:
                    scene_insert_index = index + 1
                    break

        scenes.insert(scene_insert_index, new_scene)
        write_json(chapter_path, chapter)
        touch_project(updated_entry_scene_id=new_scene_id)
        return {
            "chapterId": chapter_id,
            "sceneId": new_scene_id,
            "scene": new_scene,
        }

    raise ValueError("没有找到要插入场景的章节。")


def create_export_build_dir(prefix: str = "build") -> Path:
    EXPORTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    build_dir = EXPORTS_DIR / f"{prefix}_{timestamp}"
    suffix = 2

    while build_dir.exists():
        build_dir = EXPORTS_DIR / f"{prefix}_{timestamp}_{suffix:02d}"
        suffix += 1

    build_dir.mkdir(parents=True)
    return build_dir


def sanitize_export_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name or "").strip("._")
    return cleaned or "asset"


def get_asset_export_suffix(asset: dict, source_path: Path | None) -> str:
    file_name = (source_path.name if source_path else str(asset.get("path") or "")).lower()
    if str(asset.get("type") or "") == "live2d":
        for suffix in LIVE2D_EXTENSION_SUFFIXES:
            if file_name.endswith(suffix):
                return suffix
    return source_path.suffix if source_path and source_path.suffix else Path(asset.get("path", "")).suffix


def looks_like_live2d_file_reference(value: object) -> bool:
    if not isinstance(value, str):
        return False
    clean_value = value.strip().replace("\\", "/")
    if not clean_value or "://" in clean_value or clean_value.startswith(("data:", "#")):
        return False
    lower_value = clean_value.split("?", 1)[0].split("#", 1)[0].lower()
    if any(lower_value.endswith(suffix) for suffix in LIVE2D_EXTENSION_SUFFIXES[1:]):
        return True
    if any(lower_value.endswith(suffix) for suffix in IMAGE_EXTENSIONS):
        return True
    return "/" in clean_value and "." in clean_value.rsplit("/", 1)[-1]


def collect_live2d_model3_references(model3_payload: object) -> list[str]:
    if not isinstance(model3_payload, dict):
        return []
    file_references = model3_payload.get("FileReferences")
    if not isinstance(file_references, (dict, list)):
        return []

    references: list[str] = []

    def visit(value: object) -> None:
        if isinstance(value, str):
            clean_value = value.strip().replace("\\", "/")
            if looks_like_live2d_file_reference(clean_value):
                references.append(clean_value)
            return
        if isinstance(value, list):
            for item in value:
                visit(item)
            return
        if isinstance(value, dict):
            for item in value.values():
                visit(item)

    visit(file_references)
    unique_references: list[str] = []
    seen_references: set[str] = set()
    for reference in references:
        if reference in seen_references:
            continue
        unique_references.append(reference)
        seen_references.add(reference)
    return unique_references


def resolve_live2d_source_dependency_path(model3_path: Path, reference: str) -> Path | None:
    clean_reference = reference.strip().replace("\\", "/")
    if not clean_reference or "://" in clean_reference:
        return None
    relative_reference = Path(clean_reference)
    if relative_reference.is_absolute() or clean_reference.startswith("/"):
        return None
    model_root = model3_path.parent.resolve()
    candidate_path = (model3_path.parent / relative_reference).resolve()
    try:
        candidate_path.relative_to(model_root)
    except ValueError:
        return None
    return candidate_path


def collect_gltf_references(gltf_payload: object) -> list[str]:
    references: list[str] = []

    def visit(value: object, key: str = "") -> None:
        if isinstance(value, str):
            clean_value = value.strip().replace("\\", "/")
            if key == "uri" and clean_value and not clean_value.startswith(("data:", "#")) and "://" not in clean_value:
                references.append(clean_value)
            return
        if isinstance(value, list):
            for item in value:
                visit(item, key)
            return
        if isinstance(value, dict):
            for item_key, item_value in value.items():
                visit(item_value, str(item_key))

    visit(gltf_payload)
    unique_references: list[str] = []
    seen_references: set[str] = set()
    for reference in references:
        if reference in seen_references:
            continue
        unique_references.append(reference)
        seen_references.add(reference)
    return unique_references


def resolve_model3d_source_dependency_path(model_path: Path, reference: str) -> Path | None:
    clean_reference = reference.strip().replace("\\", "/")
    if not clean_reference or "://" in clean_reference or clean_reference.startswith(("data:", "#")):
        return None
    relative_reference = Path(clean_reference)
    if relative_reference.is_absolute() or clean_reference.startswith("/"):
        return None
    model_root = model_path.parent.resolve()
    candidate_path = (model_path.parent / relative_reference).resolve()
    try:
        candidate_path.relative_to(model_root)
    except ValueError:
        return None
    return candidate_path


def copy_live2d_model3_package(asset: dict, source_path: Path, build_dir: Path) -> tuple[str, list[dict]]:
    package_name = sanitize_export_filename(asset.get("id", "live2d_model"))
    package_rel_dir = Path("assets") / "live2d" / package_name
    target_rel_path = package_rel_dir / source_path.name
    target_path = build_dir / target_rel_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target_path)

    missing_dependencies: list[dict] = []
    try:
        model3_payload = json.loads(source_path.read_text(encoding="utf-8"))
    except Exception:
        return target_rel_path.as_posix(), missing_dependencies

    model_root = source_path.parent.resolve()
    copied_targets: set[Path] = {target_path.resolve()}
    for reference in collect_live2d_model3_references(model3_payload):
        dependency_path = resolve_live2d_source_dependency_path(source_path, reference)
        dependency_rel_path: Path | None = None
        if dependency_path is not None:
            try:
                dependency_rel_path = dependency_path.relative_to(model_root)
            except ValueError:
                dependency_rel_path = None

        if dependency_path is None or dependency_rel_path is None or not dependency_path.is_file():
            missing_dependencies.append(
                {
                    "id": asset.get("id"),
                    "name": f"{asset.get('name') or asset.get('id') or 'Live2D'} / {reference}",
                    "type": "live2d",
                    "path": reference,
                }
            )
            continue

        dependency_target_path = (build_dir / package_rel_dir / dependency_rel_path).resolve()
        if dependency_target_path in copied_targets:
            continue
        dependency_target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dependency_path, dependency_target_path)
        copied_targets.add(dependency_target_path)

    return target_rel_path.as_posix(), missing_dependencies


def copy_model3d_gltf_package(asset: dict, source_path: Path, build_dir: Path) -> tuple[str, list[dict]]:
    asset_type = str(asset.get("type") or "model3d")
    package_name = sanitize_export_filename(asset.get("id", asset_type))
    package_base_dir = "scenes3d" if asset_type == "scene3d" else "models"
    package_rel_dir = Path("assets") / package_base_dir / package_name
    target_rel_path = package_rel_dir / source_path.name
    target_path = build_dir / target_rel_path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, target_path)

    missing_dependencies: list[dict] = []
    try:
        gltf_payload = json.loads(source_path.read_text(encoding="utf-8"))
    except Exception:
        return target_rel_path.as_posix(), missing_dependencies

    model_root = source_path.parent.resolve()
    copied_targets: set[Path] = {target_path.resolve()}
    for reference in collect_gltf_references(gltf_payload):
        dependency_path = resolve_model3d_source_dependency_path(source_path, reference)
        dependency_rel_path: Path | None = None
        if dependency_path is not None:
            try:
                dependency_rel_path = dependency_path.relative_to(model_root)
            except ValueError:
                dependency_rel_path = None

        if dependency_path is None or dependency_rel_path is None or not dependency_path.is_file():
            missing_dependencies.append(
                {
                    "id": asset.get("id"),
                    "name": f"{asset.get('name') or asset.get('id') or '3D 资源'} / {reference}",
                    "type": asset_type,
                    "path": reference,
                }
            )
            continue

        dependency_target_path = (build_dir / package_rel_dir / dependency_rel_path).resolve()
        if dependency_target_path in copied_targets:
            continue
        dependency_target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dependency_path, dependency_target_path)
        copied_targets.add(dependency_target_path)

    return target_rel_path.as_posix(), missing_dependencies


def resolve_asset_source_path(asset_path: str | None) -> Path | None:
    if not asset_path:
        return None

    raw_path = Path(asset_path)
    return raw_path if raw_path.is_absolute() else (TEMPLATE_DIR / raw_path)


def copy_assets_for_export(assets_doc: dict, build_dir: Path) -> tuple[dict, int, list[dict]]:
    export_assets_doc = json.loads(json.dumps(assets_doc, ensure_ascii=False))
    copied_count = 0
    missing_assets: list[dict] = []

    for asset in export_assets_doc.get("assets", []):
        source_path = resolve_asset_source_path(asset.get("path"))
        suffix = get_asset_export_suffix(asset, source_path)
        target_name = f"{sanitize_export_filename(asset.get('id', 'asset'))}{suffix or '.dat'}"
        target_rel_path = Path("assets") / (asset.get("type") or "misc") / target_name
        target_path = build_dir / target_rel_path

        asset["exportUrl"] = None
        asset["isMissing"] = True

        if source_path and source_path.exists() and source_path.is_file():
            if (
                str(asset.get("type") or "") == "live2d"
                and source_path.name.lower().endswith(".model3.json")
            ):
                asset["exportUrl"], missing_dependencies = copy_live2d_model3_package(asset, source_path, build_dir)
                asset["isMissing"] = False
                missing_assets.extend(missing_dependencies)
                copied_count += 1
                continue
            if str(asset.get("type") or "") in {"model3d", "scene3d"} and source_path.suffix.lower() == ".gltf":
                asset["exportUrl"], missing_dependencies = copy_model3d_gltf_package(asset, source_path, build_dir)
                asset["isMissing"] = False
                missing_assets.extend(missing_dependencies)
                copied_count += 1
                continue
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
            asset["exportUrl"] = target_rel_path.as_posix()
            asset["isMissing"] = False
            copied_count += 1
            continue

        missing_assets.append(
            {
                "id": asset.get("id"),
                "name": asset.get("name"),
                "type": asset.get("type"),
                "path": asset.get("path"),
            }
        )

    return export_assets_doc, copied_count, missing_assets


def render_export_index(payload: dict) -> str:
    template = (EXPORT_TEMPLATE_DIR / "index.html").read_text(encoding="utf-8")
    payload_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    return template.replace("__LIGHTWHISPER_GAME_DATA__", payload_json)


def build_export_payload(bundle: dict, assets_doc: dict, copied_assets: int, missing_assets: list[dict]) -> dict:
    project = bundle["project"]
    default_language = normalize_language_code(project.get("language"), DEFAULT_PROJECT_LANGUAGE)
    supported_languages = normalize_supported_languages(project.get("supportedLanguages"), default_language)
    unlockable_manifest = build_export_unlockable_content_manifest(bundle, assets_doc)
    runtime_preload_manifest = build_runtime_preload_manifest(bundle, assets_doc)
    return {
        "project": project,
        "i18n": {
            "formatVersion": 1,
            "defaultLanguage": default_language,
            "fallbackLanguage": DEFAULT_PROJECT_LANGUAGE if DEFAULT_PROJECT_LANGUAGE in supported_languages else default_language,
            "supportedLanguages": supported_languages,
            "languageLabels": {
                language: SUPPORTED_PROJECT_LANGUAGES.get(language, language)
                for language in supported_languages
            },
        },
        "assets": assets_doc,
        "characters": bundle["characters"],
        "variables": bundle["variables"],
        "chapters": bundle["chapters"],
        "buildInfo": {
            "builtAt": now_iso(),
            "copiedAssets": copied_assets,
            "missingAssets": missing_assets,
            "runtimePreloadManifest": runtime_preload_manifest,
            "engineSignature": dict(EXPORT_ENGINE_SIGNATURE),
            "unlockableContentManifest": unlockable_manifest,
            "protection": {
                "profile": EXPORT_PROTECTION_PROFILE,
                "level": "light",
                "provenanceFile": EXPORT_PROVENANCE_FILE_NAME,
                "visibleWatermark": False,
            },
        },
    }


def get_export_release_version(project: dict) -> str:
    for key in ("releaseVersion", "buildVersion", "version"):
        value = str(project.get(key) or "").strip()
        if value:
            return value
    return DEFAULT_EXPORT_RELEASE_VERSION


def clamp_color_channel(value: float) -> int:
    return max(0, min(255, int(round(value))))


def mix_rgb(color_a: tuple[int, int, int], color_b: tuple[int, int, int], ratio: float) -> tuple[int, int, int]:
    safe_ratio = max(0.0, min(1.0, ratio))
    return tuple(
        clamp_color_channel(color_a[index] + (color_b[index] - color_a[index]) * safe_ratio)
        for index in range(3)
    )


def blend_rgba(
    background: tuple[int, int, int, int], overlay: tuple[int, int, int, int]
) -> tuple[int, int, int, int]:
    overlay_alpha = max(0.0, min(1.0, overlay[3] / 255.0))
    background_alpha = max(0.0, min(1.0, background[3] / 255.0))
    out_alpha = overlay_alpha + background_alpha * (1.0 - overlay_alpha)

    if out_alpha <= 0:
        return 0, 0, 0, 0

    return (
        clamp_color_channel(
            (overlay[0] * overlay_alpha + background[0] * background_alpha * (1.0 - overlay_alpha)) / out_alpha
        ),
        clamp_color_channel(
            (overlay[1] * overlay_alpha + background[1] * background_alpha * (1.0 - overlay_alpha)) / out_alpha
        ),
        clamp_color_channel(
            (overlay[2] * overlay_alpha + background[2] * background_alpha * (1.0 - overlay_alpha)) / out_alpha
        ),
        clamp_color_channel(out_alpha * 255.0),
    )


def rounded_rect_signed_distance(
    px: float, py: float, left: float, top: float, width: float, height: float, radius: float
) -> float:
    center_x = left + width * 0.5
    center_y = top + height * 0.5
    inner_half_width = max(0.0, width * 0.5 - radius)
    inner_half_height = max(0.0, height * 0.5 - radius)
    qx = abs(px - center_x) - inner_half_width
    qy = abs(py - center_y) - inner_half_height
    outside_x = max(qx, 0.0)
    outside_y = max(qy, 0.0)
    return (outside_x * outside_x + outside_y * outside_y) ** 0.5 + min(max(qx, qy), 0.0) - radius


def distance_to_segment(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
    dx = x2 - x1
    dy = y2 - y1
    length_squared = dx * dx + dy * dy
    if length_squared <= 0:
        return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5

    projection = ((px - x1) * dx + (py - y1) * dy) / length_squared
    clamped = max(0.0, min(1.0, projection))
    closest_x = x1 + dx * clamped
    closest_y = y1 + dy * clamped
    return ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5


def build_export_icon_palette(project: dict) -> dict:
    presets = [
        {
            "backgroundTop": (13, 18, 44),
            "backgroundBottom": (42, 54, 128),
            "panelTop": (18, 24, 58),
            "panelBottom": (12, 14, 32),
            "heart": (255, 176, 223),
            "shadow": (4, 7, 20),
            "highlight": (154, 234, 255),
            "spark": (255, 214, 248),
            "ring": (223, 235, 255),
            "grid": (118, 134, 219),
            "monogram": (245, 250, 255),
            "monogramAccent": (159, 228, 255),
            "orbit": (122, 118, 255),
        },
        {
            "backgroundTop": (18, 22, 56),
            "backgroundBottom": (95, 82, 186),
            "panelTop": (24, 22, 60),
            "panelBottom": (13, 14, 35),
            "heart": (255, 188, 233),
            "shadow": (5, 6, 18),
            "highlight": (194, 220, 255),
            "spark": (255, 224, 244),
            "ring": (229, 233, 255),
            "grid": (136, 133, 218),
            "monogram": (247, 249, 255),
            "monogramAccent": (180, 224, 255),
            "orbit": (154, 120, 255),
        },
        {
            "backgroundTop": (8, 28, 49),
            "backgroundBottom": (24, 88, 126),
            "panelTop": (12, 27, 48),
            "panelBottom": (8, 17, 30),
            "heart": (255, 180, 216),
            "shadow": (2, 9, 15),
            "highlight": (167, 240, 237),
            "spark": (238, 214, 255),
            "ring": (221, 248, 255),
            "grid": (96, 174, 190),
            "monogram": (243, 251, 249),
            "monogramAccent": (170, 236, 244),
            "orbit": (84, 176, 223),
        },
    ]
    seed_source = f"{project.get('projectId') or ''}:{project.get('title') or ''}"
    preset_index = sum(ord(character) for character in seed_source) % len(presets)
    return presets[preset_index]


def build_export_icon_png(project: dict, size: int = 256) -> bytes:
    palette = build_export_icon_palette(project)
    pixels: list[tuple[int, int, int, int]] = []
    center_x = size * 0.5
    center_y = size * 0.5
    outer_margin = size * 0.06
    outer_left = outer_margin
    outer_top = outer_margin
    outer_size = size - outer_margin * 2
    outer_radius = size * 0.19
    inner_margin = size * 0.14
    inner_left = inner_margin
    inner_top = inner_margin
    inner_size = size - inner_margin * 2
    inner_radius = size * 0.14
    ring_radius_a = size * 0.31
    ring_radius_b = size * 0.23
    ring_thickness = size * 0.012
    aura_a_x = size * 0.24
    aura_a_y = size * 0.18
    aura_b_x = size * 0.82
    aura_b_y = size * 0.22
    aura_radius_a = size * 0.44
    aura_radius_b = size * 0.36
    sparkle_center_x = size * 0.77
    sparkle_center_y = size * 0.22
    sparkle_radius = size * 0.058

    crest_center_x = size * 0.5
    crest_center_y = size * 0.49
    crest_radius = size * 0.205
    crest_inner_radius = size * 0.168
    crest_glow_radius = size * 0.29

    moon_outer_radius = size * 0.11
    moon_inner_radius = size * 0.088
    moon_center_x = size * 0.44
    moon_center_y = size * 0.43
    moon_cut_x = moon_center_x + size * 0.04
    moon_cut_y = moon_center_y - size * 0.012

    petal_a_center_x = size * 0.62
    petal_a_center_y = size * 0.34
    petal_b_center_x = size * 0.67
    petal_b_center_y = size * 0.405
    petal_rx = size * 0.03
    petal_ry = size * 0.075
    petal_a_cos = 0.819
    petal_a_sin = 0.574
    petal_b_cos = 0.643
    petal_b_sin = 0.766

    t_bar_left = size * 0.34
    t_bar_top = size * 0.515
    t_bar_width = size * 0.14
    t_bar_height = size * 0.038
    t_stem_left = size * 0.392
    t_stem_top = size * 0.515
    t_stem_width = size * 0.041
    t_stem_height = size * 0.18
    n_left_left = size * 0.515
    n_left_top = size * 0.515
    n_bar_width = size * 0.041
    n_bar_height = size * 0.18
    n_right_left = size * 0.63
    n_diag_thickness = size * 0.02
    n_diag_x1 = size * 0.536
    n_diag_y1 = size * 0.53
    n_diag_x2 = size * 0.651
    n_diag_y2 = size * 0.69

    def circle_distance(px: float, py: float, cx: float, cy: float, radius: float) -> float:
        return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5 - radius

    def rotated_ellipse_distance(
        px: float,
        py: float,
        cx: float,
        cy: float,
        radius_x: float,
        radius_y: float,
        cos_angle: float,
        sin_angle: float,
    ) -> float:
        dx = px - cx
        dy = py - cy
        rotated_x = dx * cos_angle + dy * sin_angle
        rotated_y = -dx * sin_angle + dy * cos_angle
        return ((rotated_x / max(1.0, radius_x)) ** 2 + (rotated_y / max(1.0, radius_y)) ** 2) ** 0.5 - 1.0

    for y in range(size):
        for x in range(size):
            outer_distance = rounded_rect_signed_distance(x, y, outer_left, outer_top, outer_size, outer_size, outer_radius)
            if outer_distance > 1.4:
                pixels.append((0, 0, 0, 0))
                continue

            outer_alpha = 255 if outer_distance <= -0.8 else clamp_color_channel((1.4 - outer_distance) / 2.2 * 255)
            vertical_ratio = (y - outer_top) / max(1.0, outer_size)
            gradient_color = mix_rgb(palette["backgroundTop"], palette["backgroundBottom"], vertical_ratio)
            pixel = (*gradient_color, outer_alpha)

            dx = (x - center_x) / size
            dy = (y - center_y) / size
            distance_factor = min(1.0, (dx * dx + dy * dy) * 3.2)
            vignette_strength = 1.0 - distance_factor * 0.2
            pixel = (
                clamp_color_channel(pixel[0] * vignette_strength),
                clamp_color_channel(pixel[1] * vignette_strength),
                clamp_color_channel(pixel[2] * vignette_strength),
                pixel[3],
            )

            top_light = max(0.0, 1.0 - (x + y) / max(1.0, size * 0.9))
            if top_light > 0:
                pixel = blend_rgba(pixel, (255, 255, 255, clamp_color_channel(top_light * 48)))

            aura_distance_a = ((x - aura_a_x) ** 2 + (y - aura_a_y) ** 2) ** 0.5
            if aura_distance_a <= aura_radius_a:
                aura_alpha_a = clamp_color_channel((1.0 - aura_distance_a / aura_radius_a) * 52)
                pixel = blend_rgba(pixel, (*palette["spark"], aura_alpha_a))

            aura_distance_b = ((x - aura_b_x) ** 2 + (y - aura_b_y) ** 2) ** 0.5
            if aura_distance_b <= aura_radius_b:
                aura_alpha_b = clamp_color_channel((1.0 - aura_distance_b / aura_radius_b) * 44)
                pixel = blend_rgba(pixel, (*palette["orbit"], aura_alpha_b))

            if outer_distance >= -2.2:
                edge_alpha = clamp_color_channel((1.0 - max(outer_distance, 0.0) / 1.6) * 72)
                pixel = blend_rgba(pixel, (*palette["ring"], edge_alpha))

            inner_distance = rounded_rect_signed_distance(x, y, inner_left, inner_top, inner_size, inner_size, inner_radius)
            if inner_distance <= 0:
                inner_ratio = (y - inner_top) / max(1.0, inner_size)
                inner_color = mix_rgb(palette["panelTop"], palette["panelBottom"], inner_ratio)
                panel_alpha = 255 if inner_distance <= -1.0 else clamp_color_channel((1.0 - max(inner_distance, 0.0)) * 190)
                pixel = blend_rgba(pixel, (*inner_color, panel_alpha))

                grid_step = max(8, int(round(size * 0.105)))
                if ((x - inner_left) % grid_step <= 1) or ((y - inner_top) % grid_step <= 1):
                    pixel = blend_rgba(pixel, (*palette["grid"], 18))

                if inner_distance >= -1.6:
                    inner_stroke_alpha = clamp_color_channel((1.0 - max(inner_distance, 0.0) / 1.4) * 54)
                    pixel = blend_rgba(pixel, (*palette["ring"], inner_stroke_alpha))

            ring_distance_a = abs(((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5 - ring_radius_a)
            if ring_distance_a <= ring_thickness * 2.2:
                ring_alpha_a = clamp_color_channel((1.0 - ring_distance_a / max(1.0, ring_thickness * 2.2)) * 52)
                pixel = blend_rgba(pixel, (*palette["ring"], ring_alpha_a))

            ring_distance_b = abs(((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5 - ring_radius_b)
            if ring_distance_b <= ring_thickness * 1.8:
                ring_alpha_b = clamp_color_channel((1.0 - ring_distance_b / max(1.0, ring_thickness * 1.8)) * 36)
                pixel = blend_rgba(pixel, (*palette["orbit"], ring_alpha_b))

            crest_glow_distance = circle_distance(x, y, crest_center_x, crest_center_y, crest_glow_radius)
            if crest_glow_distance <= 0:
                crest_glow_alpha = clamp_color_channel((1.0 - max(crest_glow_distance, -crest_glow_radius) / crest_glow_radius) * 22)
                pixel = blend_rgba(pixel, (*palette["highlight"], crest_glow_alpha))

            crest_distance = circle_distance(x, y, crest_center_x, crest_center_y, crest_radius)
            if crest_distance <= 0:
                crest_ratio = max(0.0, min(1.0, (y - (crest_center_y - crest_radius)) / max(1.0, crest_radius * 2)))
                crest_color = mix_rgb(palette["panelTop"], palette["backgroundBottom"], crest_ratio * 0.68)
                crest_alpha = 255 if crest_distance <= -1.0 else clamp_color_channel((1.0 - max(crest_distance, 0.0)) * 196)
                pixel = blend_rgba(pixel, (*crest_color, crest_alpha))

            crest_inner_distance = circle_distance(x, y, crest_center_x, crest_center_y, crest_inner_radius)
            if crest_inner_distance <= 0:
                inner_crest_alpha = 255 if crest_inner_distance <= -0.8 else clamp_color_channel((1.0 - max(crest_inner_distance, 0.0)) * 168)
                pixel = blend_rgba(pixel, (*palette["shadow"], inner_crest_alpha))

            crest_ring_distance = abs(((x - crest_center_x) ** 2 + (y - crest_center_y) ** 2) ** 0.5 - crest_radius)
            if crest_ring_distance <= size * 0.018:
                crest_ring_alpha = clamp_color_channel((1.0 - crest_ring_distance / max(1.0, size * 0.018)) * 148)
                pixel = blend_rgba(pixel, (*palette["ring"], crest_ring_alpha))

            moon_outer_distance = circle_distance(x, y, moon_center_x, moon_center_y, moon_outer_radius)
            moon_inner_distance = circle_distance(x, y, moon_cut_x, moon_cut_y, moon_inner_radius)
            if moon_outer_distance <= 0 and moon_inner_distance > 0:
                moon_alpha = 255 if moon_outer_distance <= -0.8 else clamp_color_channel((1.0 - max(moon_outer_distance, 0.0)) * 255)
                moon_color = mix_rgb(palette["ring"], palette["highlight"], 0.18)
                pixel = blend_rgba(pixel, (*moon_color, moon_alpha))
            elif moon_outer_distance <= size * 0.03 and moon_inner_distance > -size * 0.02:
                moon_glow_alpha = clamp_color_channel((1.0 - max(moon_outer_distance, 0.0) / max(1.0, size * 0.03)) * 88)
                pixel = blend_rgba(pixel, (*palette["highlight"], moon_glow_alpha))

            petal_a_distance = rotated_ellipse_distance(
                x, y, petal_a_center_x, petal_a_center_y, petal_rx, petal_ry, petal_a_cos, petal_a_sin
            )
            petal_b_distance = rotated_ellipse_distance(
                x, y, petal_b_center_x, petal_b_center_y, petal_rx * 0.95, petal_ry * 0.92, petal_b_cos, petal_b_sin
            )
            petal_distance = min(petal_a_distance, petal_b_distance)
            if petal_distance <= 0:
                petal_alpha = 255 if petal_distance <= -0.08 else clamp_color_channel((1.0 - max(petal_distance, 0.0)) * 255)
                petal_ratio = max(0.0, min(1.0, (y - size * 0.28) / max(1.0, size * 0.2)))
                petal_color = mix_rgb(palette["heart"], palette["spark"], petal_ratio * 0.55)
                pixel = blend_rgba(pixel, (*petal_color, petal_alpha))
            elif petal_distance <= 0.24:
                petal_glow_alpha = clamp_color_channel((1.0 - petal_distance / 0.24) * 68)
                pixel = blend_rgba(pixel, (*palette["heart"], petal_glow_alpha))

            t_bar_distance = rounded_rect_signed_distance(
                x, y, t_bar_left, t_bar_top, t_bar_width, t_bar_height, size * 0.016
            )
            t_stem_distance = rounded_rect_signed_distance(
                x, y, t_stem_left, t_stem_top, t_stem_width, t_stem_height, size * 0.016
            )
            n_left_distance = rounded_rect_signed_distance(
                x, y, n_left_left, n_left_top, n_bar_width, n_bar_height, size * 0.016
            )
            n_right_distance = rounded_rect_signed_distance(
                x, y, n_right_left, n_left_top, n_bar_width, n_bar_height, size * 0.016
            )
            n_diag_distance = distance_to_segment(x, y, n_diag_x1, n_diag_y1, n_diag_x2, n_diag_y2) - n_diag_thickness

            monogram_distance = min(
                t_bar_distance,
                t_stem_distance,
                n_left_distance,
                n_right_distance,
                n_diag_distance,
            )
            if monogram_distance <= 0:
                monogram_ratio = max(0.0, min(1.0, (y - size * 0.5) / max(1.0, size * 0.22)))
                monogram_color = mix_rgb(palette["monogram"], palette["monogramAccent"], monogram_ratio)
                monogram_alpha = 255 if monogram_distance <= -0.6 else clamp_color_channel((1.0 - max(monogram_distance, 0.0)) * 255)
                pixel = blend_rgba(pixel, (*monogram_color, monogram_alpha))

                highlight_distance = ((x - size * 0.39) ** 2 + (y - size * 0.53) ** 2) ** 0.5
                highlight_radius = size * 0.085
                if highlight_distance <= highlight_radius:
                    highlight_alpha = clamp_color_channel((1.0 - highlight_distance / highlight_radius) * 126)
                    pixel = blend_rgba(pixel, (*palette["highlight"], highlight_alpha))
            elif monogram_distance <= size * 0.035:
                glow_alpha = clamp_color_channel((1.0 - monogram_distance / (size * 0.035)) * 58)
                pixel = blend_rgba(pixel, (*palette["spark"], glow_alpha))

            sparkle_dx = abs(x - sparkle_center_x)
            sparkle_dy = abs(y - sparkle_center_y)
            sparkle_cross = min(
                sparkle_dx / max(1.0, size * 0.016) + sparkle_dy / max(1.0, sparkle_radius),
                sparkle_dx / max(1.0, sparkle_radius) + sparkle_dy / max(1.0, size * 0.016),
            )
            sparkle_diamond = (sparkle_dx + sparkle_dy) / max(1.0, sparkle_radius)
            sparkle_strength = max(0.0, 1.0 - min(sparkle_cross, sparkle_diamond))
            if sparkle_strength > 0:
                sparkle_alpha = clamp_color_channel(sparkle_strength * 228)
                pixel = blend_rgba(pixel, (*palette["spark"], sparkle_alpha))

            pixels.append(pixel)

    scanlines = []
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            red, green, blue, alpha = pixels[y * size + x]
            row.extend((red, green, blue, alpha))
        scanlines.append(bytes(row))

    raw_image = b"".join(scanlines)
    compressed = zlib.compress(raw_image, level=9)

    def png_chunk(chunk_type: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + chunk_type
            + payload
            + struct.pack(">I", zlib.crc32(chunk_type + payload) & 0xFFFFFFFF)
        )

    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", compressed)
        + png_chunk(b"IEND", b"")
    )


def build_export_icon_ico(png_bytes: bytes, size: int = 256) -> bytes:
    icon_directory = struct.pack(
        "<HHHBBBBHHII",
        0,
        1,
        1,
        0 if size >= 256 else size,
        0 if size >= 256 else size,
        0,
        0,
        1,
        32,
        len(png_bytes),
        22,
    )
    return icon_directory + png_bytes


def write_export_icon_files(
    target_dir: Path, png_bytes: bytes, ico_bytes: bytes, file_stem: str = "app_icon"
) -> dict:
    png_path = target_dir / f"{file_stem}.png"
    ico_path = target_dir / f"{file_stem}.ico"
    png_path.write_bytes(png_bytes)
    ico_path.write_bytes(ico_bytes)
    return {
        "pngPath": png_path,
        "icoPath": ico_path,
        "pngFileName": png_path.name,
        "icoFileName": ico_path.name,
        "pngRelativePath": png_path.name,
        "icoRelativePath": ico_path.name,
    }


def build_export_manifest(
    bundle: dict,
    *,
    target: str,
    target_label: str,
    build_id: str,
    copied_assets: int,
    missing_assets: list[dict],
    extra_files: dict | None = None,
    runtime_info: dict | None = None,
) -> dict:
    project = bundle["project"]
    resolution = project.get("resolution") or {"width": 1280, "height": 720}
    total_scenes = sum(len(chapter.get("scenes", [])) for chapter in bundle.get("chapters", []))
    missing_asset_names = [asset.get("name") or asset.get("id") or "未命名素材" for asset in missing_assets]
    runtime_payload = runtime_info or {}

    return {
        "formatVersion": EXPORT_MANIFEST_FORMAT_VERSION,
        "buildId": build_id,
        "builtAt": now_iso(),
        "engine": {
            "name": "Canvasia Engine",
            "exportTarget": target,
            "exportTargetLabel": target_label,
            "releaseVersion": get_export_release_version(project),
            "signature": dict(EXPORT_ENGINE_SIGNATURE),
        },
        "project": {
            "projectId": project.get("projectId"),
            "title": project.get("title"),
            "language": project.get("language") or DEFAULT_PROJECT_LANGUAGE,
            "supportedLanguages": project.get("supportedLanguages") or [
                project.get("language") or DEFAULT_PROJECT_LANGUAGE
            ],
            "resolution": {
                "width": int(resolution.get("width", 1280)),
                "height": int(resolution.get("height", 720)),
            },
            "entrySceneId": project.get("entrySceneId"),
            "chapterCount": len(bundle.get("chapters", [])),
            "sceneCount": total_scenes,
            "characterCount": len(bundle.get("characters", {}).get("characters", [])),
            "variableCount": len(bundle.get("variables", {}).get("variables", [])),
        },
        "assets": {
            "copiedCount": copied_assets,
            "missingCount": len(missing_assets),
            "missingAssetNames": missing_asset_names,
        },
        "protection": {
            "profile": EXPORT_PROTECTION_PROFILE,
            "level": "light",
            "algorithm": "sha256",
            "provenanceFile": EXPORT_PROVENANCE_FILE_NAME,
            "verifiers": {
                "python": EXPORT_PROVENANCE_VERIFIER_SCRIPT_NAME,
                "macos": EXPORT_PROVENANCE_MAC_VERIFIER_NAME,
                "linux": EXPORT_PROVENANCE_LINUX_VERIFIER_NAME,
                "windows": EXPORT_PROVENANCE_WINDOWS_VERIFIER_NAME,
            },
            "visibleWatermark": False,
            "checks": ["engine_signature", "file_fingerprints", "build_seal"],
        },
        "files": extra_files or {},
        "runtime": runtime_payload,
        "warnings": [runtime_payload.get("warning")] if runtime_payload.get("warning") else [],
    }


def write_export_manifest(build_dir: Path, manifest: dict) -> Path:
    manifest_path = build_dir / "export_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def should_include_export_provenance_file(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.name in {EXPORT_PROVENANCE_FILE_NAME, ".DS_Store"}:
        return False
    if "__pycache__" in path.parts:
        return False
    if path.name.endswith((".zip", ".tar", ".tar.gz", ".tgz")):
        return False
    return True


def iter_export_provenance_files(build_dir: Path, roots: list[Path] | None = None) -> list[Path]:
    scan_roots = roots or [build_dir]
    files: list[Path] = []
    for root in scan_roots:
        if not root.exists():
            continue
        if root.is_file():
            if should_include_export_provenance_file(root):
                files.append(root)
            continue
        for path in root.rglob("*"):
            if should_include_export_provenance_file(path):
                files.append(path)
    return sorted(set(files), key=lambda item: item.relative_to(build_dir).as_posix())


def build_export_provenance_payload(
    build_dir: Path,
    bundle: dict,
    manifest: dict,
    *,
    roots: list[Path] | None = None,
) -> dict:
    file_entries = []
    total_bytes = 0
    for path in iter_export_provenance_files(build_dir, roots):
        size_bytes = path.stat().st_size
        total_bytes += size_bytes
        file_entries.append(
            {
                "path": path.relative_to(build_dir).as_posix(),
                "sizeBytes": size_bytes,
                "sha256": calculate_file_sha256(path),
            }
        )

    seal_payload = {
        "engine": manifest.get("engine") or {},
        "project": manifest.get("project") or {},
        "protection": manifest.get("protection") or {},
        "files": file_entries,
    }
    seal_source = json.dumps(seal_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    project = bundle.get("project") or {}
    return {
        "formatVersion": EXPORT_PROVENANCE_FORMAT_VERSION,
        "profile": EXPORT_PROTECTION_PROFILE,
        "createdAt": now_iso(),
        "algorithm": "sha256",
        "engine": {
            "name": manifest.get("engine", {}).get("name") or "Canvasia Engine",
            "releaseVersion": manifest.get("engine", {}).get("releaseVersion") or DEFAULT_EXPORT_RELEASE_VERSION,
            "signature": dict(EXPORT_ENGINE_SIGNATURE),
        },
        "build": {
            "buildId": manifest.get("buildId") or "",
            "target": manifest.get("engine", {}).get("exportTarget") or "",
            "targetLabel": manifest.get("engine", {}).get("exportTargetLabel") or "",
            "projectId": project.get("projectId") or "",
            "projectTitle": project.get("title") or "",
        },
        "protection": {
            "level": "light",
            "visibleWatermark": False,
            "notEncryption": True,
            "purpose": "origin marker and tamper evidence",
        },
        "summary": {
            "fileCount": len(file_entries),
            "totalBytes": total_bytes,
            "seal": hashlib.sha256(seal_source).hexdigest(),
        },
        "files": file_entries,
    }


def write_export_provenance_file(
    build_dir: Path,
    bundle: dict,
    manifest: dict,
    *,
    roots: list[Path] | None = None,
) -> dict:
    provenance_path = build_dir / EXPORT_PROVENANCE_FILE_NAME
    payload = build_export_provenance_payload(build_dir, bundle, manifest, roots=roots)
    provenance_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "provenanceName": provenance_path.name,
        "provenancePath": str(provenance_path),
        "provenanceSeal": payload["summary"]["seal"],
        "provenanceSummary": payload["summary"],
    }


def build_export_provenance_verifier_script() -> str:
    expected_signature = json.dumps(EXPORT_ENGINE_SIGNATURE, ensure_ascii=False, sort_keys=True)
    return f'''#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

PROVENANCE_FILE_NAME = "{EXPORT_PROVENANCE_FILE_NAME}"
MANIFEST_FILE_NAME = "export_manifest.json"
EXPECTED_PROFILE = "{EXPORT_PROTECTION_PROFILE}"
EXPECTED_SIGNATURE = {expected_signature}


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file_handle:
        payload = json.load(file_handle)
    return payload if isinstance(payload, dict) else {{}}


def compact_sha256(payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def verify_bundle(bundle_dir: Path) -> dict:
    provenance_path = bundle_dir / PROVENANCE_FILE_NAME
    manifest_path = bundle_dir / MANIFEST_FILE_NAME
    missing_files = []
    changed_files = []
    errors = []

    if not provenance_path.is_file():
        return {{
            "status": "fail",
            "checkedAt": now_iso(),
            "bundleDir": str(bundle_dir),
            "errors": [f"Missing {{PROVENANCE_FILE_NAME}}"],
            "summary": {{"missingCount": 1, "changedCount": 0, "sealMatched": False}},
        }}

    try:
        provenance = load_json(provenance_path)
    except Exception as error:
        return {{
            "status": "fail",
            "checkedAt": now_iso(),
            "bundleDir": str(bundle_dir),
            "errors": [f"Cannot read {{PROVENANCE_FILE_NAME}}: {{error}}"],
            "summary": {{"missingCount": 0, "changedCount": 0, "sealMatched": False}},
        }}

    manifest = {{}}
    if manifest_path.is_file():
        try:
            manifest = load_json(manifest_path)
        except Exception as error:
            errors.append(f"Cannot read {{MANIFEST_FILE_NAME}}: {{error}}")
    else:
        errors.append(f"Missing {{MANIFEST_FILE_NAME}}")

    for entry in provenance.get("files") or []:
        if not isinstance(entry, dict):
            continue
        relative_path = str(entry.get("path") or "").strip()
        if not relative_path:
            continue
        file_path = bundle_dir / relative_path
        expected_size = int(entry.get("sizeBytes") or 0)
        expected_sha256 = str(entry.get("sha256") or "")
        if not file_path.is_file():
            missing_files.append({{"path": relative_path, "expectedSha256": expected_sha256}})
            continue
        actual_size = file_path.stat().st_size
        actual_sha256 = sha256_file(file_path)
        if actual_size != expected_size or actual_sha256 != expected_sha256:
            changed_files.append(
                {{
                    "path": relative_path,
                    "expectedSizeBytes": expected_size,
                    "actualSizeBytes": actual_size,
                    "expectedSha256": expected_sha256,
                    "actualSha256": actual_sha256,
                }}
            )

    expected_seal = str((provenance.get("summary") or {{}}).get("seal") or "")
    seal_payload = {{
        "engine": manifest.get("engine") or {{}},
        "project": manifest.get("project") or {{}},
        "protection": manifest.get("protection") or {{}},
        "files": provenance.get("files") or [],
    }}
    actual_seal = compact_sha256(seal_payload)
    profile_matched = provenance.get("profile") == EXPECTED_PROFILE
    signature_matched = (provenance.get("engine") or {{}}).get("signature") == EXPECTED_SIGNATURE
    seal_matched = bool(expected_seal) and actual_seal == expected_seal
    status = "pass" if not errors and not missing_files and not changed_files and profile_matched and signature_matched and seal_matched else "fail"
    return {{
        "status": status,
        "checkedAt": now_iso(),
        "bundleDir": str(bundle_dir),
        "profileMatched": profile_matched,
        "signatureMatched": signature_matched,
        "sealMatched": seal_matched,
        "expectedSeal": expected_seal,
        "actualSeal": actual_seal,
        "summary": {{
            "checkedFileCount": len(provenance.get("files") or []),
            "missingCount": len(missing_files),
            "changedCount": len(changed_files),
            "errorCount": len(errors),
        }},
        "missingFiles": missing_files[:50],
        "changedFiles": changed_files[:50],
        "errors": errors[:50],
    }}


def main() -> int:
    bundle_dir = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent
    if bundle_dir.is_file():
        bundle_dir = bundle_dir.parent
    report = verify_bundle(bundle_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''


def build_export_provenance_shell_verifier(script_name: str) -> str:
    return "\n".join(
        [
            "#!/bin/sh",
            "set -eu",
            'cd "$(dirname "$0")"',
            "if command -v python3 >/dev/null 2>&1; then",
            f'  python3 "{script_name}" .',
            "else",
            f'  python "{script_name}" .',
            "fi",
            "",
        ]
    )


def build_export_provenance_windows_verifier(script_name: str) -> str:
    return "\n".join(
        [
            "@echo off",
            "setlocal",
            'cd /d "%~dp0"',
            f'py -3 "{script_name}" .',
            "if %ERRORLEVEL% EQU 0 exit /b 0",
            f'python "{script_name}" .',
            "exit /b %ERRORLEVEL%",
            "",
        ]
    )


def write_export_provenance_verifier_files(build_dir: Path) -> dict:
    script_path = build_dir / EXPORT_PROVENANCE_VERIFIER_SCRIPT_NAME
    mac_path = build_dir / EXPORT_PROVENANCE_MAC_VERIFIER_NAME
    linux_path = build_dir / EXPORT_PROVENANCE_LINUX_VERIFIER_NAME
    windows_path = build_dir / EXPORT_PROVENANCE_WINDOWS_VERIFIER_NAME
    script_path.write_text(build_export_provenance_verifier_script(), encoding="utf-8")
    mac_path.write_text(build_export_provenance_shell_verifier(script_path.name), encoding="utf-8")
    linux_path.write_text(build_export_provenance_shell_verifier(script_path.name), encoding="utf-8")
    windows_path.write_text(build_export_provenance_windows_verifier(script_path.name), encoding="utf-8")
    script_path.chmod(0o755)
    mac_path.chmod(0o755)
    linux_path.chmod(0o755)
    return {
        "provenanceVerifierName": script_path.name,
        "provenanceVerifierPath": str(script_path),
        "provenanceVerifierMacName": mac_path.name,
        "provenanceVerifierMacPath": str(mac_path),
        "provenanceVerifierLinuxName": linux_path.name,
        "provenanceVerifierLinuxPath": str(linux_path),
        "provenanceVerifierWindowsName": windows_path.name,
        "provenanceVerifierWindowsPath": str(windows_path),
        "paths": [script_path, mac_path, linux_path, windows_path],
    }


def build_export_splash_svg(project: dict, release_version: str, target_label: str) -> str:
    title = (project.get("title") or "Canvasia Engine").strip() or "Canvasia Engine"
    subtitle = target_label or "Canvasia Engine 导出试玩包"
    palette = build_export_icon_palette(project)
    background_top = f"rgb({palette['backgroundTop'][0]}, {palette['backgroundTop'][1]}, {palette['backgroundTop'][2]})"
    background_bottom = (
        f"rgb({palette['backgroundBottom'][0]}, {palette['backgroundBottom'][1]}, {palette['backgroundBottom'][2]})"
    )
    heart_color = f"rgb({palette['heart'][0]}, {palette['heart'][1]}, {palette['heart'][2]})"
    spark_color = f"rgb({palette['spark'][0]}, {palette['spark'][1]}, {palette['spark'][2]})"
    highlight_color = f"rgb({palette['highlight'][0]}, {palette['highlight'][1]}, {palette['highlight'][2]})"
    safe_title = html.escape(title)
    safe_subtitle = html.escape(subtitle)
    safe_version = html.escape(release_version)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900" fill="none">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1600" y2="900" gradientUnits="userSpaceOnUse">
      <stop stop-color="{background_top}"/>
      <stop offset="0.52" stop-color="{background_bottom}"/>
      <stop offset="1" stop-color="#120D24"/>
    </linearGradient>
    <radialGradient id="auraA" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(280 188) rotate(22) scale(460 320)">
      <stop stop-color="{heart_color}" stop-opacity="0.34"/>
      <stop offset="1" stop-color="{heart_color}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="auraB" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(1288 176) rotate(122) scale(448 330)">
      <stop stop-color="{highlight_color}" stop-opacity="0.28"/>
      <stop offset="1" stop-color="{highlight_color}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="frameStroke" x1="72" y1="72" x2="1528" y2="828" gradientUnits="userSpaceOnUse">
      <stop stop-color="white" stop-opacity="0.22"/>
      <stop offset="0.5" stop-color="white" stop-opacity="0.06"/>
      <stop offset="1" stop-color="white" stop-opacity="0.16"/>
    </linearGradient>
    <linearGradient id="crestFill" x1="626" y1="248" x2="978" y2="622" gradientUnits="userSpaceOnUse">
      <stop stop-color="{highlight_color}"/>
      <stop offset="0.52" stop-color="{spark_color}"/>
      <stop offset="1" stop-color="{heart_color}"/>
    </linearGradient>
    <radialGradient id="logoGlow" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(800 420) rotate(90) scale(280 280)">
      <stop stop-color="{spark_color}" stop-opacity="0.36"/>
      <stop offset="1" stop-color="{spark_color}" stop-opacity="0"/>
    </radialGradient>
    <pattern id="grid" width="54" height="54" patternUnits="userSpaceOnUse">
      <path d="M54 0H0V54" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>
    </pattern>
    <filter id="softBlur" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="24"/>
    </filter>
  </defs>

  <rect width="1600" height="900" rx="48" fill="url(#bg)"/>
  <rect width="1600" height="900" rx="48" fill="url(#grid)" opacity="0.34"/>
  <rect x="72" y="72" width="1456" height="756" rx="40" fill="rgba(255,255,255,0.03)" stroke="url(#frameStroke)"/>
  <rect x="96" y="96" width="1408" height="708" rx="28" stroke="rgba(255,255,255,0.05)"/>

  <g opacity="0.88">
    <ellipse cx="280" cy="188" rx="460" ry="320" fill="url(#auraA)">
      <animate attributeName="cx" values="272;304;286;272" dur="26s" repeatCount="indefinite"/>
      <animate attributeName="cy" values="188;208;178;188" dur="26s" repeatCount="indefinite"/>
    </ellipse>
    <ellipse cx="1280" cy="170" rx="420" ry="320" fill="url(#auraB)">
      <animate attributeName="cx" values="1280;1248;1294;1280" dur="30s" repeatCount="indefinite"/>
      <animate attributeName="cy" values="170;198;160;170" dur="30s" repeatCount="indefinite"/>
    </ellipse>
  </g>

  <g opacity="0.54">
    <circle cx="800" cy="420" r="208" stroke="rgba(255,255,255,0.14)" stroke-width="1.2">
      <animateTransform attributeName="transform" type="rotate" from="0 800 420" to="360 800 420" dur="28s" repeatCount="indefinite"/>
    </circle>
    <circle cx="800" cy="420" r="146" stroke="rgba(255,255,255,0.12)" stroke-width="1">
      <animateTransform attributeName="transform" type="rotate" from="360 800 420" to="0 800 420" dur="18s" repeatCount="indefinite"/>
    </circle>
    <circle cx="800" cy="420" r="94" stroke="rgba(255,255,255,0.1)" stroke-width="1">
      <animate attributeName="opacity" values="0.3;0.85;0.3" dur="8s" repeatCount="indefinite"/>
    </circle>
  </g>

  <g filter="url(#softBlur)">
    <circle cx="800" cy="420" r="160" fill="url(#logoGlow)">
      <animate attributeName="opacity" values="0.56;0.82;0.56" dur="9s" repeatCount="indefinite"/>
    </circle>
  </g>

  <g>
    <rect x="664" y="282" width="272" height="272" rx="64" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.16)"/>
    <rect x="688" y="306" width="224" height="224" rx="46" fill="rgba(255,255,255,0.03)" stroke="rgba(255,255,255,0.08)"/>
    <circle cx="822" cy="364" r="34" fill="{heart_color}"/>
    <circle cx="832" cy="364" r="27" fill="rgba(84,120,255,0.96)"/>
    <circle cx="800" cy="418" r="92" stroke="url(#crestFill)" stroke-width="3.6"/>
    <circle cx="800" cy="418" r="70" stroke="rgba(255,255,255,0.14)" stroke-width="1.3"/>
    <path d="M720 518V338H736L778 404L820 338H836V518H820V392L783 447H774L736 392V518H720Z" fill="white"/>
    <path d="M858 338H874V518H858V338ZM858 338L960 470V518H942L858 406V338Z" fill="white"/>
    <path d="M690 554C708 525 732 515 764 514C745 536 742 559 750 582C722 580 703 571 690 554Z" fill="{heart_color}"/>
    <path d="M738 578C752 557 772 548 797 547C784 564 783 584 789 602C766 600 750 593 738 578Z" fill="{heart_color}" fill-opacity="0.84"/>
    <path d="M1018 236L1034 194L1050 236L1092 252L1050 268L1034 310L1018 268L976 252L1018 236Z" fill="{spark_color}" fill-opacity="0.9">
      <animate attributeName="opacity" values="0.48;0.92;0.48" dur="7s" repeatCount="indefinite"/>
    </path>
    <path d="M560 602L572 570L584 602L616 614L584 626L572 658L560 626L528 614L560 602Z" fill="rgba(255,255,255,0.74)">
      <animate attributeName="opacity" values="0.24;0.72;0.24" dur="6s" repeatCount="indefinite"/>
    </path>
  </g>

  <g>
    <text x="160" y="642" fill="rgba(159,232,255,0.86)" font-size="20" font-weight="700" letter-spacing="10" font-family="'Avenir Next','PingFang SC','Microsoft YaHei','Noto Sans SC',sans-serif">MOON ARC VISUAL NARRATIVE SYSTEM</text>
    <text x="160" y="714" fill="white" font-size="78" font-weight="700" font-family="'Avenir Next','PingFang SC','Microsoft YaHei','Noto Sans SC',sans-serif">{safe_title}</text>
    <text x="160" y="776" fill="rgba(255,255,255,0.78)" font-size="28" font-weight="500" font-family="'PingFang SC','Microsoft YaHei','Noto Sans SC',sans-serif">{safe_subtitle}</text>
    <text x="160" y="816" fill="rgba(255,255,255,0.58)" font-size="21" font-weight="500" font-family="'PingFang SC','Microsoft YaHei','Noto Sans SC',sans-serif">发布版本 {safe_version} · Canvasia Engine Moonlight Runtime</text>
  </g>
</svg>
"""


def write_export_splash_asset(target_dir: Path, project: dict, release_version: str, target_label: str) -> dict:
    splash_path = target_dir / "launch_splash.svg"
    splash_path.write_text(build_export_splash_svg(project, release_version, target_label), encoding="utf-8")
    return {
        "path": splash_path,
        "fileName": splash_path.name,
        "relativePath": splash_path.name,
    }


def get_editor_package_target_label() -> str:
    if sys.platform == "darwin":
        return "macOS 编辑器桌面包"
    if os.name == "nt":
        return "Windows 编辑器桌面包"
    return "编辑器桌面包"


def should_build_editor_macos_app() -> bool:
    return sys.platform == "darwin"


def get_editor_runtime_cache_root() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches" / "CanvasiaEngine" / "editor_runtime"
    return Path.home() / ".cache" / "CanvasiaEngine" / "editor_runtime"


def get_editor_runtime_cache_dir() -> Path:
    cache_root = get_editor_runtime_cache_root()
    cache_root.mkdir(parents=True, exist_ok=True)
    version_tag = f"v{EDITOR_RUNTIME_CACHE_VERSION}"
    python_tag = f"py{sys.version_info.major}{sys.version_info.minor}"
    machine_tag = sanitize_export_filename(platform.machine())
    runtime_dir = cache_root / f"{version_tag}_{python_tag}_{sys.platform}_{machine_tag}"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    return runtime_dir


def build_editor_runtime_marker() -> dict:
    return {
        "formatVersion": EDITOR_RUNTIME_CACHE_VERSION,
        "pythonVersion": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": sys.platform,
        "machine": platform.machine(),
        "sourcePrefix": sys.prefix,
    }


def get_editor_runtime_marker_path(runtime_dir: Path) -> Path:
    return runtime_dir / "editor_runtime_marker.json"


def has_valid_editor_runtime_marker(runtime_dir: Path) -> bool:
    marker_path = get_editor_runtime_marker_path(runtime_dir)
    python_path = runtime_dir / "bin" / "python3"
    if not marker_path.is_file() or not python_path.is_file():
        return False
    try:
        marker = read_json(marker_path)
    except Exception:
        return False
    return marker == build_editor_runtime_marker()


def write_editor_runtime_marker(runtime_dir: Path) -> Path:
    marker_path = get_editor_runtime_marker_path(runtime_dir)
    write_json(marker_path, build_editor_runtime_marker())
    return marker_path


def is_conda_python_runtime() -> bool:
    conda_prefix = str(os.environ.get("CONDA_PREFIX") or "").strip()
    return bool(conda_prefix and Path(conda_prefix).resolve() == Path(sys.prefix).resolve())


def get_conda_executable() -> str | None:
    conda_executable = shutil.which("conda")
    return conda_executable or None


def build_editor_runtime_archive_name() -> str:
    machine_tag = sanitize_export_filename(platform.machine())
    return f"editor_runtime_py{sys.version_info.major}{sys.version_info.minor}_{sys.platform}_{machine_tag}.tar.gz"


def ensure_editor_runtime_archive_from_conda_pack() -> tuple[Path, str]:
    if not is_conda_python_runtime():
        raise ValueError("当前 Python 不是 conda 环境，暂时没法自动打出内嵌运行时。")

    conda_executable = get_conda_executable()
    if not conda_executable:
        raise ValueError("没有找到 conda 命令，暂时没法自动准备内嵌运行时。")

    conda_pack_executable = shutil.which("conda-pack")
    if not conda_pack_executable:
        raise ValueError("没有找到 conda-pack，暂时没法自动准备内嵌运行时。")

    cache_dir = get_editor_runtime_cache_dir()
    env_dir = cache_dir / "env"
    archive_path = cache_dir / build_editor_runtime_archive_name()
    marker_path = get_editor_runtime_marker_path(env_dir)

    if archive_path.is_file() and has_valid_editor_runtime_marker(env_dir):
        return archive_path, "已复用本机缓存的内嵌 Python 运行时"

    if env_dir.exists():
        shutil.rmtree(env_dir, ignore_errors=True)

    python_series = f"{sys.version_info.major}.{sys.version_info.minor}"
    subprocess.run(
        [
            conda_executable,
            "create",
            "-y",
            "-p",
            str(env_dir),
            f"python={python_series}",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    subprocess.run(
        [
            conda_pack_executable,
            "-p",
            str(env_dir),
            "-o",
            str(archive_path),
            "--force",
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    write_editor_runtime_marker(env_dir)
    return archive_path, "这次自动打包生成的内嵌 Python 运行时"


def extract_editor_runtime_archive(archive_path: Path, target_dir: Path) -> Path:
    if target_dir.exists():
        shutil.rmtree(target_dir, ignore_errors=True)
    target_dir.mkdir(parents=True, exist_ok=True)

    with tarfile.open(archive_path, "r:gz") as archive:
        try:
            archive.extractall(target_dir, filter="data")
        except TypeError:
            archive.extractall(target_dir)

    conda_unpack_path = target_dir / "bin" / "conda-unpack"
    if conda_unpack_path.is_file():
        subprocess.run(
            [str(conda_unpack_path)],
            cwd=target_dir,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

    python_path = target_dir / "bin" / "python3"
    if not python_path.is_file():
        raise ValueError("内嵌 Python 运行时解压完成了，但没有找到 bin/python3。")

    return python_path


def prepare_editor_embedded_runtime(bundle_dir: Path) -> dict:
    runtime_dir = bundle_dir / EDITOR_RUNTIME_DIR_NAME

    try:
        archive_path, source_label = ensure_editor_runtime_archive_from_conda_pack()
        python_path = extract_editor_runtime_archive(archive_path, runtime_dir)
        return {
            "included": True,
            "mode": EDITOR_RUNTIME_SOURCE_CONDA_PACK,
            "modeLabel": "内嵌 Python 运行时",
            "pythonPath": str(python_path),
            "runtimeDirPath": str(runtime_dir),
            "sourceLabel": source_label,
            "sourcePath": str(archive_path),
            "warning": "",
        }
    except Exception as error:
        if runtime_dir.exists():
            shutil.rmtree(runtime_dir, ignore_errors=True)
        return {
            "included": False,
            "mode": EDITOR_RUNTIME_SOURCE_SYSTEM,
            "modeLabel": "系统 Python 启动",
            "pythonPath": "",
            "runtimeDirPath": "",
            "sourceLabel": "",
            "sourcePath": "",
            "warning": str(error),
        }


def get_editor_portable_runtime_cache_dir(platform_key: str) -> Path:
    cache_dir = get_editor_runtime_cache_root() / "portable" / platform_key
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def build_portable_python_asset_name(platform_key: str) -> str:
    target = EDITOR_PORTABLE_RUNTIME_TARGETS[platform_key]
    return (
        f"cpython-{EDITOR_PORTABLE_PYTHON_VERSION}+{EDITOR_PORTABLE_PYTHON_RELEASE}-"
        f"{target['triplet']}-install_only.{target['archiveExt']}"
    )


def build_portable_python_download_url(platform_key: str) -> str:
    asset_name = build_portable_python_asset_name(platform_key)
    encoded_asset_name = quote(asset_name)
    return (
        "https://github.com/astral-sh/python-build-standalone/releases/download/"
        f"{EDITOR_PORTABLE_PYTHON_RELEASE}/{encoded_asset_name}"
    )


def get_portable_runtime_override_env_var(platform_key: str) -> str:
    return f"CANVASIA_EDITOR_RUNTIME_ARCHIVE_{platform_key.upper()}"


def resolve_portable_runtime_override_archive(platform_key: str) -> Path | None:
    raw_value = str(os.environ.get(get_portable_runtime_override_env_var(platform_key)) or "").strip()
    if not raw_value:
        return None
    candidate = Path(raw_value).expanduser()
    return candidate if candidate.is_file() else None


def ensure_portable_python_runtime_archive(platform_key: str) -> tuple[Path, str]:
    override_archive = resolve_portable_runtime_override_archive(platform_key)
    if override_archive:
        return override_archive, "环境变量指定的预编译 Python 运行时"

    cache_dir = get_editor_portable_runtime_cache_dir(platform_key)
    archive_path = cache_dir / build_portable_python_asset_name(platform_key)
    if archive_path.is_file():
        return archive_path, "已复用本机缓存的预编译 Python 运行时"

    download_url = build_portable_python_download_url(platform_key)
    with urlopen(download_url) as response, archive_path.open("wb") as output:
        shutil.copyfileobj(response, output)
    return archive_path, "这次自动下载的预编译 Python 运行时"


def find_python_executable_in_runtime(runtime_dir: Path, platform_key: str) -> Path:
    candidates = []
    if platform_key == EDITOR_PLATFORM_WINDOWS:
        candidates = [
            runtime_dir / "python.exe",
            runtime_dir / "python3.exe",
            runtime_dir / "python" / "python.exe",
            runtime_dir / "python" / "python3.exe",
        ]
    else:
        candidates = [
            runtime_dir / "bin" / "python3",
            runtime_dir / "bin" / "python",
            runtime_dir / "python" / "bin" / "python3",
            runtime_dir / "python" / "bin" / "python",
        ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    for pattern in ("**/python3", "**/python", "**/python.exe", "**/python3.exe"):
        for candidate in runtime_dir.glob(pattern):
            if candidate.is_file():
                return candidate

    raise ValueError("运行时已经解压完成，但没有找到可执行的 Python。")


def extract_portable_python_runtime_archive(platform_key: str, archive_path: Path, runtime_dir: Path) -> Path:
    if runtime_dir.exists():
        shutil.rmtree(runtime_dir, ignore_errors=True)
    runtime_dir.mkdir(parents=True, exist_ok=True)

    with tarfile.open(archive_path, "r:gz") as archive:
        try:
            archive.extractall(runtime_dir, filter="data")
        except (TypeError, OSError):
            shutil.rmtree(runtime_dir, ignore_errors=True)
            runtime_dir.mkdir(parents=True, exist_ok=True)
            try:
                subprocess.run(
                    ["tar", "-xzf", str(archive_path), "-C", str(runtime_dir)],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True,
                )
            except (FileNotFoundError, subprocess.CalledProcessError):
                shutil.rmtree(runtime_dir, ignore_errors=True)
                runtime_dir.mkdir(parents=True, exist_ok=True)
                archive.extractall(runtime_dir)

    python_path = find_python_executable_in_runtime(runtime_dir, platform_key)
    if platform_key != EDITOR_PLATFORM_WINDOWS:
        python_path.chmod(0o755)
    return python_path


def prepare_editor_portable_runtime(bundle_dir: Path, platform_key: str) -> dict:
    runtime_dir = bundle_dir / EDITOR_RUNTIME_DIR_NAME
    archive_path, source_label = ensure_portable_python_runtime_archive(platform_key)
    python_path = extract_portable_python_runtime_archive(platform_key, archive_path, runtime_dir)
    return {
        "included": True,
        "mode": EDITOR_RUNTIME_SOURCE_PYTHON_BUILD_STANDALONE,
        "modeLabel": "预编译内嵌 Python 运行时",
        "pythonPath": str(python_path),
        "runtimeDirPath": str(runtime_dir),
        "sourceLabel": source_label,
        "sourcePath": str(archive_path),
        "warning": "",
    }


def build_editor_root_command_launcher_script() -> str:
    return f"""#!/bin/zsh
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUNDLE_DIR="$SCRIPT_DIR/{EDITOR_BUNDLE_DIR_NAME}"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

for EMBEDDED_PYTHON in \
  "$BUNDLE_DIR/{EDITOR_RUNTIME_DIR_NAME}/bin/python3" \
  "$BUNDLE_DIR/{EDITOR_RUNTIME_DIR_NAME}/bin/python" \
  "$BUNDLE_DIR/{EDITOR_RUNTIME_DIR_NAME}/python/bin/python3" \
  "$BUNDLE_DIR/{EDITOR_RUNTIME_DIR_NAME}/python/bin/python"
do
  if [ -x "$EMBEDDED_PYTHON" ]; then
    cd "$BUNDLE_DIR"
    exec "$EMBEDDED_PYTHON" run_editor.py
  fi
done

if ! command -v python3 >/dev/null 2>&1; then
  if command -v osascript >/dev/null 2>&1; then
    /usr/bin/osascript <<'APPLESCRIPT'
display alert "需要先安装 Python 3" message "Canvasia Engine 编辑器包第一阶段仍然依赖系统里的 Python 3。先安装 Python 3，再双击启动编辑器。" as critical
APPLESCRIPT
  else
    echo "需要先安装 Python 3，才能启动 Canvasia Engine 编辑器包。"
  fi
  exit 1
fi

cd "$BUNDLE_DIR"
exec python3 run_editor.py
"""


def build_editor_root_linux_launcher_script() -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUNDLE_DIR="$SCRIPT_DIR/{EDITOR_BUNDLE_DIR_NAME}"

for EMBEDDED_PYTHON in \
  "$BUNDLE_DIR/{EDITOR_RUNTIME_DIR_NAME}/bin/python3" \
  "$BUNDLE_DIR/{EDITOR_RUNTIME_DIR_NAME}/bin/python" \
  "$BUNDLE_DIR/{EDITOR_RUNTIME_DIR_NAME}/python/bin/python3" \
  "$BUNDLE_DIR/{EDITOR_RUNTIME_DIR_NAME}/python/bin/python"
do
  if [ -x "$EMBEDDED_PYTHON" ]; then
    cd "$BUNDLE_DIR"
    exec "$EMBEDDED_PYTHON" run_editor.py
  fi
done

if ! command -v python3 >/dev/null 2>&1; then
  echo "需要先安装 Python 3，才能启动 Canvasia Engine 编辑器包。"
  exit 1
fi

cd "$BUNDLE_DIR"
exec python3 run_editor.py
"""


def build_editor_root_windows_launcher_script() -> str:
    return f"""@echo off
setlocal
set "BUNDLE_DIR=%~dp0{EDITOR_BUNDLE_DIR_NAME}"
set "EMBEDDED_PYTHON=%BUNDLE_DIR%\\{EDITOR_RUNTIME_DIR_NAME}\\python.exe"
if exist "%EMBEDDED_PYTHON%" (
  cd /d "%BUNDLE_DIR%"
  "%EMBEDDED_PYTHON%" run_editor.py
  exit /b %errorlevel%
)
set "EMBEDDED_PYTHON=%BUNDLE_DIR%\\{EDITOR_RUNTIME_DIR_NAME}\\python3.exe"
if exist "%EMBEDDED_PYTHON%" (
  cd /d "%BUNDLE_DIR%"
  "%EMBEDDED_PYTHON%" run_editor.py
  exit /b %errorlevel%
)
set "EMBEDDED_PYTHON=%BUNDLE_DIR%\\{EDITOR_RUNTIME_DIR_NAME}\\python\\python.exe"
if exist "%EMBEDDED_PYTHON%" (
  cd /d "%BUNDLE_DIR%"
  "%EMBEDDED_PYTHON%" run_editor.py
  exit /b %errorlevel%
)
set "EMBEDDED_PYTHON=%BUNDLE_DIR%\\{EDITOR_RUNTIME_DIR_NAME}\\python\\python3.exe"
if exist "%EMBEDDED_PYTHON%" (
  cd /d "%BUNDLE_DIR%"
  "%EMBEDDED_PYTHON%" run_editor.py
  exit /b %errorlevel%
)

if not exist "%BUNDLE_DIR%\\run_editor.py" (
  echo 没有找到编辑器入口：%BUNDLE_DIR%\\run_editor.py
  pause
  exit /b 1
)

cd /d "%BUNDLE_DIR%"
where python >nul 2>nul
if %errorlevel%==0 (
  python run_editor.py
  exit /b %errorlevel%
)

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 run_editor.py
  exit /b %errorlevel%
)

echo 需要先安装 Python 3，才能启动 Canvasia Engine 编辑器包。
echo 安装 Python 3 后，请重新双击这个启动器。
pause
exit /b 1
"""


def write_editor_root_launchers(build_dir: Path) -> dict:
    command_path = build_dir / EDITOR_START_COMMAND_NAME
    command_path.write_text(build_editor_root_command_launcher_script(), encoding="utf-8")
    command_path.chmod(0o755)

    windows_path = build_dir / EDITOR_START_WINDOWS_NAME
    windows_path.write_text(build_editor_root_windows_launcher_script(), encoding="utf-8")

    linux_path = build_dir / EDITOR_LINUX_START_NAME
    linux_path.write_text(build_editor_root_linux_launcher_script(), encoding="utf-8")
    linux_path.chmod(0o755)

    return {
        "commandPath": command_path,
        "windowsPath": windows_path,
        "linuxPath": linux_path,
    }


def build_editor_package_readme(target_label: str, runtime_info: dict | None = None) -> str:
    runtime_info = runtime_info or {}
    lines = [
        "Canvasia Engine 编辑器本体正式打包（维护发布准备版）",
        "",
        f"当前包类型：{target_label}",
        "这是一份可以直接分发的编辑器桌面包，里面已经带了编辑器前端、样板项目、导出模板和启动器。",
        "",
        "推荐启动方式：",
        f"1. macOS：双击 {EDITOR_START_COMMAND_NAME}",
        f"2. Windows：双击 {EDITOR_START_WINDOWS_NAME}",
        f"3. 如果目录里还有 {EDITOR_MAC_APP_NAME}，也可以直接双击它，它会帮你打开终端启动编辑器。",
        "",
    ]
    if runtime_info.get("included"):
        lines.extend(
            [
                "这次已经把内嵌 Python 运行时一起打进去了：",
                f"- 运行时模式：{runtime_info.get('modeLabel') or '内嵌 Python 运行时'}",
                f"- 运行时来源：{runtime_info.get('sourceLabel') or '当前机器缓存'}",
                f"- 运行时目录：{EDITOR_BUNDLE_DIR_NAME}/{EDITOR_RUNTIME_DIR_NAME}",
                "- 启动器会优先使用这套内嵌运行时，所以目标机器不需要额外先装 Python 3。",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "当前阶段仍然依赖系统里的 Python 3：",
                "- 需要本机已经安装 Python 3。",
                "- 编辑器启动后会自动打开本地浏览器，并用本地 HTTP 服务跑起来。",
            ]
        )
        if runtime_info.get("warning"):
            lines.append(f"- 这次没能自动打进内嵌运行时：{runtime_info['warning']}")
        lines.append("")

    lines.extend(
        [
            "编辑器启动后会自动打开本地浏览器，并用本地 HTTP 服务跑起来。",
            "",
            "包里已经保留：",
            "- prototype_editor：编辑器界面",
            "- export_player_template：导出后的播放器模板",
            "- template_project：示例项目",
            "- desktop_runtime：Windows 导出真壳说明目录",
            "- projects / exports：空目录，后续会在这里生成你的项目和导出结果",
            "",
            "如果你准备继续维护桌面发布链，还可以直接看这些：",
            f"- {EDITOR_COMMERCIAL_README_NAME}",
            f"- {EDITOR_SIGNING_GUIDE_NAME}",
            f"- {EDITOR_SIGNING_ENV_EXAMPLE_NAME}",
            f"- {EDITOR_SIGNING_CHECK_SCRIPT_NAME}",
            f"- {EDITOR_SIGNING_CHECK_COMMAND_NAME}",
        ]
    )
    if should_build_editor_macos_app():
        lines.extend(
            [
                "",
                "macOS 附加说明：",
                f"- {EDITOR_MAC_APP_NAME} 已经会把编辑器资源一起打进去，双击即可直接启动。",
                "- 开发者签名与公证完成后，可作为更接近正式分发标准的安装包发布。",
            ]
        )
    return "\n".join(lines) + "\n"


def write_editor_package_readme(build_dir: Path, target_label: str, runtime_info: dict | None = None) -> Path:
    readme_path = build_dir / EDITOR_EDITOR_README_NAME
    readme_path.write_text(build_editor_package_readme(target_label, runtime_info=runtime_info), encoding="utf-8")
    return readme_path


def write_editor_distribution_snapshot(build_dir: Path, config: dict) -> Path:
    snapshot_path = build_dir / EDITOR_DISTRIBUTION_SNAPSHOT_NAME
    write_json(snapshot_path, config)
    return snapshot_path


def copy_editor_signing_support_files(target_dir: Path) -> dict:
    target_dir.mkdir(parents=True, exist_ok=True)
    guide_source = EDITOR_SIGNING_GUIDE_SOURCE
    env_source = EDITOR_SIGNING_ENV_EXAMPLE_SOURCE
    check_script_source = EDITOR_SIGNING_CHECK_SCRIPT_SOURCE
    check_command_source = EDITOR_SIGNING_CHECK_COMMAND_SOURCE
    guide_target = target_dir / EDITOR_SIGNING_GUIDE_NAME
    env_target = target_dir / EDITOR_SIGNING_ENV_EXAMPLE_NAME
    check_script_target = target_dir / EDITOR_SIGNING_CHECK_SCRIPT_NAME
    check_command_target = target_dir / EDITOR_SIGNING_CHECK_COMMAND_NAME
    shutil.copy2(guide_source, guide_target)
    shutil.copy2(env_source, env_target)
    shutil.copy2(check_script_source, check_script_target)
    shutil.copy2(check_command_source, check_command_target)
    check_command_target.chmod(0o755)
    return {
        "guidePath": str(guide_target),
        "guideName": guide_target.name,
        "envExamplePath": str(env_target),
        "envExampleName": env_target.name,
        "checkScriptPath": str(check_script_target),
        "checkScriptName": check_script_target.name,
        "checkCommandPath": str(check_command_target),
        "checkCommandName": check_command_target.name,
    }


def resolve_editor_signing_settings(config: dict) -> dict:
    signing = config.get("signing") or {}
    return {
        "macAppIdentity": str(os.environ.get(EDITOR_MAC_APP_IDENTITY_ENV) or signing.get("macAppIdentity") or "").strip(),
        "macInstallerIdentity": str(
            os.environ.get(EDITOR_MAC_INSTALLER_IDENTITY_ENV) or signing.get("macInstallerIdentity") or ""
        ).strip(),
        "macNotaryProfile": str(
            os.environ.get(EDITOR_MAC_NOTARY_PROFILE_ENV) or signing.get("macNotaryProfile") or ""
        ).strip(),
    }


def build_editor_commercial_status_label(signing_result: dict) -> str:
    if signing_result.get("notarized"):
        return "已签名并完成公证"
    if signing_result.get("installerSigned") or signing_result.get("appSigned"):
        return "已签名，待公证"
    if signing_result.get("canSign"):
        return "已准备好签名配置，等待执行"
    return "未签名（待填写开发者身份）"


def resolve_windows_signing_settings(config: dict) -> dict:
    signing = config.get("signing") or {}
    sign_tool_path = str(
        os.environ.get(EDITOR_WINDOWS_SIGNTOOL_ENV)
        or signing.get("windowsSignToolPath")
        or shutil.which("signtool")
        or shutil.which("signtool.exe")
        or ""
    ).strip()
    runner_path = str(
        os.environ.get(EDITOR_WINDOWS_SIGNTOOL_RUNNER_ENV)
        or signing.get("windowsSignToolRunner")
        or ""
    ).strip()
    if sign_tool_path and sign_tool_path.lower().endswith(".exe") and os.name != "nt" and not runner_path:
        runner_path = shutil.which("wine64") or shutil.which("wine") or ""

    return {
        "signToolPath": sign_tool_path,
        "signToolRunner": runner_path,
        "certificateSubject": str(
            os.environ.get(EDITOR_WINDOWS_CERT_SUBJECT_ENV)
            or signing.get("windowsCertificateSubject")
            or ""
        ).strip(),
        "certificateThumbprint": str(
            os.environ.get(EDITOR_WINDOWS_CERT_THUMBPRINT_ENV)
            or signing.get("windowsCertificateThumbprint")
            or ""
        ).strip(),
        "pfxPath": str(
            os.environ.get(EDITOR_WINDOWS_PFX_PATH_ENV)
            or signing.get("windowsPfxPath")
            or ""
        ).strip(),
        "pfxPassword": str(
            os.environ.get(EDITOR_WINDOWS_PFX_PASSWORD_ENV)
            or signing.get("windowsPfxPassword")
            or ""
        ),
        "timestampUrl": str(
            os.environ.get(EDITOR_WINDOWS_TIMESTAMP_URL_ENV)
            or signing.get("windowsTimestampUrl")
            or "http://timestamp.digicert.com"
        ).strip()
        or "http://timestamp.digicert.com",
    }


def build_windows_signing_status_label(result: dict) -> str:
    if result.get("installerSigned"):
        return "已签名并加时间戳"
    if result.get("canSign"):
        return "已准备好签名配置，等待执行"
    return "未签名（待配置 Windows 证书/签名工具）"


def build_editor_windows_installer_base_name(config: dict) -> str:
    app_name = config.get("productName") or "Canvasia Engine Editor"
    return sanitize_export_filename(app_name) or "CanvasiaEngineEditorSetup"


def build_editor_windows_installer_script(config: dict) -> str:
    app_name = config.get("productName") or "Canvasia Engine Editor"
    app_id = (config.get("windows") or {}).get("appId") or config.get("bundleIdentifier") or "com.canvasia.engine.editor"
    publisher = (config.get("windows") or {}).get("publisher") or config.get("companyName") or "Canvasia Engine Project"
    website = config.get("website") or config.get("supportUrl") or "https://github.com/TonyNa-code/canvasia-engine"
    support_url = config.get("supportUrl") or website
    support_contact = config.get("supportEmail") or support_url
    output_base_name = build_editor_windows_installer_base_name(config)
    return f"""; Canvasia Engine Editor Windows 安装包脚本（Inno Setup）
; 用法：在 Windows 上安装 Inno Setup 后，直接编译这份 .iss。
[Setup]
AppId={{{app_id}}}
AppName={app_name}
AppVersion={EDITOR_PACKAGE_VERSION}
AppPublisher={publisher}
AppPublisherURL={website}
AppSupportURL={support_url}
AppUpdatesURL={support_url}
DefaultDirName={{autopf}}\\{app_name}
DefaultGroupName={app_name}
OutputDir=.
OutputBaseFilename={output_base_name}
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern
DisableProgramGroupPage=yes
UninstallDisplayIcon={{app}}\\app_icon.ico
SetupIconFile=app_icon.ico
LicenseFile=
InfoBeforeFile=README_编辑器包先看这里.txt
AppContact={support_contact}

[Files]
Source: "editor_bundle\\*"; DestDir: "{{app}}\\editor_bundle"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "{EDITOR_START_WINDOWS_NAME}"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "app_icon.ico"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "app_icon.png"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "launch_splash.svg"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "{EDITOR_EDITOR_README_NAME}"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "{EDITOR_COMMERCIAL_README_NAME}"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{autoprograms}}\\{app_name}"; Filename: "{{app}}\\{EDITOR_START_WINDOWS_NAME}"; IconFilename: "{{app}}\\app_icon.ico"
Name: "{{autodesktop}}\\{app_name}"; Filename: "{{app}}\\{EDITOR_START_WINDOWS_NAME}"; IconFilename: "{{app}}\\app_icon.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加选项："

[Run]
Filename: "{{app}}\\{EDITOR_START_WINDOWS_NAME}"; Description: "立即启动 {app_name}"; Flags: nowait postinstall skipifsilent
"""


def write_editor_windows_installer_script(build_dir: Path, config: dict) -> Path:
    script_path = build_dir / EDITOR_WINDOWS_INSTALLER_SCRIPT_NAME
    script_path.write_text(build_editor_windows_installer_script(config), encoding="utf-8")
    return script_path


def resolve_windows_installer_compiler_settings(config: dict) -> dict:
    windows = config.get("windows") or {}
    compiler_path = str(
        os.environ.get(EDITOR_WINDOWS_ISCC_ENV)
        or windows.get("installerCompilerPath")
        or ""
    ).strip()
    runner_path = str(
        os.environ.get(EDITOR_WINDOWS_ISCC_RUNNER_ENV)
        or windows.get("installerCompilerRunner")
        or ""
    ).strip()

    if not compiler_path:
        for candidate in (
            shutil.which("iscc"),
            shutil.which("ISCC"),
            str(Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe")) if os.name == "nt" else "",
            str(Path("C:/Program Files/Inno Setup 6/ISCC.exe")) if os.name == "nt" else "",
        ):
            clean_candidate = str(candidate or "").strip()
            if clean_candidate and Path(clean_candidate).exists():
                compiler_path = clean_candidate
                break

    if compiler_path and compiler_path.lower().endswith(".exe") and os.name != "nt" and not runner_path:
        runner_path = shutil.which("wine64") or shutil.which("wine") or ""

    return {
        "compilerPath": compiler_path,
        "runnerPath": runner_path,
        "canCompile": bool(compiler_path) and (os.name == "nt" or not compiler_path.lower().endswith(".exe") or bool(runner_path)),
    }


def build_windows_installer_compile_status_label(result: dict) -> str:
    if result.get("compiled"):
        return "已编译 Windows 安装器"
    if result.get("canCompile"):
        return "已准备好编译器，待执行"
    return "未编译（待配置 Inno Setup 编译器）"


def attempt_windows_editor_installer_compile(build_dir: Path, script_path: Path, config: dict) -> dict:
    settings = resolve_windows_installer_compiler_settings(config)
    output_base_name = build_editor_windows_installer_base_name(config)
    installer_path = build_dir / f"{output_base_name}.exe"
    result = {
        "canCompile": bool(settings.get("canCompile")),
        "compiled": False,
        "statusLabel": "",
        "messages": [],
        "compilerPath": settings.get("compilerPath") or "",
        "runnerPath": settings.get("runnerPath") or "",
        "installerPath": "",
        "installerName": "",
    }

    compiler_path = str(settings.get("compilerPath") or "").strip()
    runner_path = str(settings.get("runnerPath") or "").strip()
    if not compiler_path:
        result["statusLabel"] = build_windows_installer_compile_status_label(result)
        result["messages"].append("没有找到 Inno Setup 编译器，已保留 .iss 模板。")
        return result

    if not settings.get("canCompile"):
        result["statusLabel"] = build_windows_installer_compile_status_label(result)
        result["messages"].append("找到了 Windows 版 ISCC.exe，但当前环境缺少可用运行器（例如 wine）。")
        return result

    command = []
    if runner_path:
        command.append(runner_path)
    command.extend(
        [
            compiler_path,
            f"/O{build_dir}",
            f"/F{output_base_name}",
            str(script_path),
        ]
    )

    try:
        subprocess.run(
            command,
            cwd=build_dir,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except Exception as error:
        result["statusLabel"] = "Windows 安装器编译失败"
        result["messages"].append(str(error))
        return result

    if installer_path.is_file():
        result["compiled"] = True
        result["installerPath"] = str(installer_path)
        result["installerName"] = installer_path.name
        result["messages"].append("已成功编译出 Windows 安装器。")
    else:
        result["messages"].append("编译命令执行完成，但没有找到最终的 .exe 安装器。")

    result["statusLabel"] = build_windows_installer_compile_status_label(result)
    return result


def attempt_windows_editor_signing(installer_path: Path | None, config: dict) -> dict:
    settings = resolve_windows_signing_settings(config)
    has_certificate = bool(
        settings.get("certificateSubject")
        or settings.get("certificateThumbprint")
        or settings.get("pfxPath")
    )
    can_run_tool = bool(settings.get("signToolPath")) and (
        os.name == "nt"
        or not str(settings.get("signToolPath") or "").lower().endswith(".exe")
        or bool(settings.get("signToolRunner"))
    )
    result = {
        "canSign": bool(installer_path and has_certificate and can_run_tool),
        "installerSigned": False,
        "statusLabel": "",
        "messages": [],
        "signToolPath": settings.get("signToolPath") or "",
        "signToolRunner": settings.get("signToolRunner") or "",
        "timestampUrl": settings.get("timestampUrl") or "",
    }

    if not installer_path or not installer_path.is_file():
        result["statusLabel"] = build_windows_signing_status_label(result)
        result["messages"].append("还没有可签名的 Windows 安装器。")
        return result

    if not settings.get("signToolPath"):
        result["statusLabel"] = build_windows_signing_status_label(result)
        result["messages"].append("没有找到 signtool，暂时不能给 Windows 安装器签名。")
        return result

    if str(settings.get("signToolPath") or "").lower().endswith(".exe") and os.name != "nt" and not settings.get("signToolRunner"):
        result["statusLabel"] = build_windows_signing_status_label(result)
        result["messages"].append("找到了 Windows 版 signtool.exe，但当前环境缺少可用运行器（例如 wine）。")
        return result

    command: list[str] = []
    if settings.get("signToolRunner"):
        command.append(str(settings["signToolRunner"]))
    command.extend(
        [
            str(settings["signToolPath"]),
            "sign",
            "/fd",
            "SHA256",
            "/td",
            "SHA256",
        ]
    )

    if settings.get("timestampUrl"):
        command.extend(["/tr", str(settings["timestampUrl"])])
    if settings.get("pfxPath"):
        command.extend(["/f", str(settings["pfxPath"])])
        if settings.get("pfxPassword"):
            command.extend(["/p", str(settings["pfxPassword"])])
    elif settings.get("certificateThumbprint"):
        command.extend(["/sha1", str(settings["certificateThumbprint"])])
    elif settings.get("certificateSubject"):
        command.extend(["/n", str(settings["certificateSubject"])])
    else:
        result["statusLabel"] = build_windows_signing_status_label(result)
        result["messages"].append("还没有配置 Windows 证书信息，可用证书主题、指纹或 PFX。")
        return result

    command.append(str(installer_path))

    try:
        subprocess.run(
            command,
            cwd=installer_path.parent,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        result["installerSigned"] = True
        result["messages"].append("已成功给 Windows 安装器签名。")
    except Exception as error:
        result["messages"].append(str(error))

    result["statusLabel"] = build_windows_signing_status_label(result)
    return result


def build_editor_linux_install_script(config: dict) -> str:
    app_name = config.get("productName") or "Canvasia Engine Editor"
    slug = sanitize_export_filename(app_name) or "canvasia_engine_editor"
    desktop_name = (config.get("linux") or {}).get("desktopFileName") or "Canvasia Engine Editor.desktop"
    return f"""#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_ROOT="${{1:-$HOME/.local/opt/{slug}}}"
DESKTOP_TARGET_DIR="${{XDG_DATA_HOME:-$HOME/.local/share}}/applications"

mkdir -p "$INSTALL_ROOT"
rm -rf "$INSTALL_ROOT/editor_bundle"
cp -R "$SCRIPT_DIR/editor_bundle" "$INSTALL_ROOT/editor_bundle"
cp "$SCRIPT_DIR/{EDITOR_LINUX_START_NAME}" "$INSTALL_ROOT/{EDITOR_LINUX_START_NAME}"
cp "$SCRIPT_DIR/app_icon.png" "$INSTALL_ROOT/app_icon.png"
chmod +x "$INSTALL_ROOT/{EDITOR_LINUX_START_NAME}"

mkdir -p "$DESKTOP_TARGET_DIR"
sed "s|^Exec=.*$|Exec=$INSTALL_ROOT/{EDITOR_LINUX_START_NAME}|; s|^Icon=.*$|Icon=$INSTALL_ROOT/app_icon.png|" \\
  "$SCRIPT_DIR/{desktop_name}" > "$DESKTOP_TARGET_DIR/{desktop_name}"
chmod +x "$DESKTOP_TARGET_DIR/{desktop_name}"

echo "{app_name} 已安装到：$INSTALL_ROOT"
echo "桌面入口已写入：$DESKTOP_TARGET_DIR/{desktop_name}"
"""


def write_editor_linux_install_script(build_dir: Path, config: dict) -> Path:
    script_path = build_dir / EDITOR_LINUX_INSTALL_SCRIPT_NAME
    script_path.write_text(build_editor_linux_install_script(config), encoding="utf-8")
    script_path.chmod(0o755)
    return script_path


def attempt_macos_editor_signing(build_dir: Path, app_path: Path | None, installer_path: Path | None, config: dict) -> dict:
    signing_settings = resolve_editor_signing_settings(config)
    result = {
        "canSign": bool(signing_settings.get("macAppIdentity") or signing_settings.get("macInstallerIdentity")),
        "appSigned": False,
        "installerSigned": False,
        "notarized": False,
        "messages": [],
        "appIdentity": signing_settings.get("macAppIdentity") or "",
        "installerIdentity": signing_settings.get("macInstallerIdentity") or "",
        "notaryProfile": signing_settings.get("macNotaryProfile") or "",
    }

    if sys.platform != "darwin" or not app_path:
        result["statusLabel"] = "当前平台未执行 mac 签名"
        return result

    codesign_path = shutil.which("codesign")
    if signing_settings.get("macAppIdentity") and codesign_path:
        try:
            subprocess.run(
                [
                    codesign_path,
                    "--force",
                    "--deep",
                    "--options",
                    "runtime",
                    "--timestamp",
                    "--sign",
                    signing_settings["macAppIdentity"],
                    str(app_path),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            result["appSigned"] = True
        except subprocess.CalledProcessError as error:
            result["messages"].append(f"App 签名失败：{error.stdout.strip() or error}")
    elif signing_settings.get("macAppIdentity"):
        result["messages"].append("没有找到 codesign，没法执行 App 签名。")
    else:
        result["messages"].append(f"还没有配置 App 签名身份，可通过 {EDITOR_MAC_APP_IDENTITY_ENV} 提供。")

    if installer_path:
        productsign_path = shutil.which("productsign")
        if signing_settings.get("macInstallerIdentity") and productsign_path:
            try:
                signed_pkg_path = build_dir / f"{installer_path.stem}.signed{installer_path.suffix}"
                subprocess.run(
                    [
                        productsign_path,
                        "--sign",
                        signing_settings["macInstallerIdentity"],
                        str(installer_path),
                        str(signed_pkg_path),
                    ],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                shutil.move(str(signed_pkg_path), str(installer_path))
                result["installerSigned"] = True
            except subprocess.CalledProcessError as error:
                result["messages"].append(f"安装包签名失败：{error.stdout.strip() or error}")
        elif signing_settings.get("macInstallerIdentity"):
            result["messages"].append("没有找到 productsign，没法执行安装包签名。")
        else:
            result["messages"].append(f"还没有配置安装包签名身份，可通过 {EDITOR_MAC_INSTALLER_IDENTITY_ENV} 提供。")

        xcrun_path = shutil.which("xcrun")
        if result["installerSigned"] and signing_settings.get("macNotaryProfile") and xcrun_path:
            try:
                subprocess.run(
                    [
                        xcrun_path,
                        "notarytool",
                        "submit",
                        str(installer_path),
                        "--keychain-profile",
                        signing_settings["macNotaryProfile"],
                        "--wait",
                    ],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                subprocess.run(
                    [xcrun_path, "stapler", "staple", str(installer_path)],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                if result["appSigned"]:
                    subprocess.run(
                        [xcrun_path, "stapler", "staple", str(app_path)],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                    )
                result["notarized"] = True
            except subprocess.CalledProcessError as error:
                result["messages"].append(f"安装包公证失败：{error.stdout.strip() or error}")
        elif result["installerSigned"] and signing_settings.get("macNotaryProfile"):
            result["messages"].append("没有找到 xcrun，没法执行公证。")
        elif result["installerSigned"]:
            result["messages"].append(f"还没有配置公证 profile，可通过 {EDITOR_MAC_NOTARY_PROFILE_ENV} 提供。")

    result["statusLabel"] = build_editor_commercial_status_label(result)
    return result


def build_editor_commercial_readme(
    platform_label: str,
    config_path: Path,
    distribution_snapshot_path: Path,
    signing_result: dict,
    config: dict,
    extra_notes: list[str] | None = None,
) -> str:
    lines = [
        f"Canvasia Engine 编辑器发布维护说明（{platform_label}）",
        "",
        f"发行配置文件：{config_path}",
        f"本次打包快照：{distribution_snapshot_path.name}",
        f"产品名：{config.get('productName')}",
        f"包标识：{config.get('bundleIdentifier')}",
        f"发行方：{config.get('publisherName')}",
        f"公司名：{config.get('companyName')}",
        f"维护发布状态：{signing_result.get('statusLabel')}",
        f"Windows 安装器编译状态：{signing_result.get('windowsInstallerStatusLabel') or '未编译（待配置 Inno Setup 编译器）'}",
        f"Windows 安装器签名状态：{signing_result.get('windowsSigningStatusLabel') or '未签名（待配置 Windows 证书/签名工具）'}",
        f"签名操作手册：{EDITOR_SIGNING_GUIDE_NAME}",
        f"环境变量模板：{EDITOR_SIGNING_ENV_EXAMPLE_NAME}",
        f"签名前自检脚本：{EDITOR_SIGNING_CHECK_SCRIPT_NAME}",
        f"签名前自检启动器：{EDITOR_SIGNING_CHECK_COMMAND_NAME}",
        "",
        "继续维护正式安装包与签名链前，请最后确认这些：",
        "1. 填好 editor_distribution.json 里的发行信息。",
        f"2. 如需 mac 正式分发，请提供 {EDITOR_MAC_APP_IDENTITY_ENV} / {EDITOR_MAC_INSTALLER_IDENTITY_ENV} / {EDITOR_MAC_NOTARY_PROFILE_ENV}。",
        f"3. 如需 Windows 正式分发，请提供 {EDITOR_WINDOWS_SIGNTOOL_ENV}，以及证书主题/指纹/PFX（见发行配置）。",
        "4. Windows 包里会附带 Inno Setup 脚本模板；Linux 包里会附带安装脚本和桌面入口。",
        "5. 如果已经配置好 Inno Setup 编译器，Windows 包会直接多出一个可分发的 .exe 安装器。",
        "6. 先运行签名前自检脚本，确认当前机器上的签名工具、证书和公证配置是否齐全。",
        "7. 对外发布前，建议再做一轮完整人工安装与启动走查。",
    ]
    if extra_notes:
        lines.extend(["", *extra_notes])
    messages = [message for message in signing_result.get("messages", []) if message]
    if messages:
        lines.extend(["", "这次打包的签名/公证提示："])
        lines.extend([f"- {message}" for message in messages])
    return "\n".join(lines) + "\n"


def write_editor_commercial_readme(
    build_dir: Path,
    platform_label: str,
    config_path: Path,
    distribution_snapshot_path: Path,
    signing_result: dict,
    config: dict,
    extra_notes: list[str] | None = None,
) -> Path:
    readme_path = build_dir / EDITOR_COMMERCIAL_README_NAME
    readme_path.write_text(
        build_editor_commercial_readme(
            platform_label,
            config_path,
            distribution_snapshot_path,
            signing_result,
            config,
            extra_notes=extra_notes,
        ),
        encoding="utf-8",
    )
    return readme_path


def copy_editor_distribution_tree(target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)

    for file_name in EDITOR_EXPORT_FILES:
        if file_name == EDITOR_SIGNING_GUIDE_NAME:
            source_path = EDITOR_SIGNING_GUIDE_SOURCE
        elif file_name == EDITOR_SIGNING_ENV_EXAMPLE_NAME:
            source_path = EDITOR_SIGNING_ENV_EXAMPLE_SOURCE
        elif file_name == EDITOR_SIGNING_CHECK_SCRIPT_NAME:
            source_path = EDITOR_SIGNING_CHECK_SCRIPT_SOURCE
        elif file_name == EDITOR_SIGNING_CHECK_COMMAND_NAME:
            source_path = EDITOR_SIGNING_CHECK_COMMAND_SOURCE
        else:
            source_path = ROOT_DIR / file_name
        shutil.copy2(source_path, target_dir / file_name)

    for directory_name in EDITOR_EXPORT_DIRECTORIES:
        source_dir = ROOT_DIR / directory_name
        destination_dir = target_dir / directory_name
        if destination_dir.exists():
            shutil.rmtree(destination_dir, ignore_errors=True)
        shutil.copytree(
            source_dir,
            destination_dir,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
        )

    for directory_name in EDITOR_EXPORT_EMPTY_DIRECTORIES:
        (target_dir / directory_name).mkdir(parents=True, exist_ok=True)

    (target_dir / ".editor_package").mkdir(parents=True, exist_ok=True)


def build_editor_package_manifest(
    *,
    build_id: str,
    target_label: str,
    archive_name: str,
    includes_macos_app: bool,
    includes_macos_installer: bool,
    runtime_info: dict | None = None,
    distribution_config: dict | None = None,
    signing_result: dict | None = None,
    windows_installer_result: dict | None = None,
) -> dict:
    runtime_info = runtime_info or {}
    distribution_config = distribution_config or build_default_editor_distribution_config()
    signing_result = signing_result or {}
    windows_installer_result = windows_installer_result or {}
    return {
        "formatVersion": EXPORT_MANIFEST_FORMAT_VERSION,
        "buildId": build_id,
        "builtAt": now_iso(),
        "engine": {
            "name": "Canvasia Engine",
            "packageTarget": EXPORT_TARGET_EDITOR_DESKTOP,
            "packageTargetLabel": target_label,
            "releaseVersion": EDITOR_PACKAGE_VERSION,
        },
        "distribution": {
            "productName": distribution_config.get("productName"),
            "bundleIdentifier": distribution_config.get("bundleIdentifier"),
            "publisherName": distribution_config.get("publisherName"),
            "companyName": distribution_config.get("companyName"),
            "website": distribution_config.get("website"),
            "supportUrl": distribution_config.get("supportUrl"),
            "supportEmail": distribution_config.get("supportEmail"),
        },
        "editorPackage": {
            "bundleDirName": EDITOR_BUNDLE_DIR_NAME,
            "launchers": {
                "macCommand": EDITOR_START_COMMAND_NAME,
                "windowsCommand": EDITOR_START_WINDOWS_NAME,
                "macApp": EDITOR_MAC_APP_NAME if includes_macos_app else "",
                "macInstaller": EDITOR_MAC_INSTALLER_NAME if includes_macos_installer else "",
            },
            "includes": {
                "editorUi": True,
                "exportTemplate": True,
                "sampleProject": True,
                "desktopRuntimeGuide": True,
                "emptyProjectsDir": True,
                "emptyExportsDir": True,
            },
            "archiveName": archive_name,
            "requiresPython3": not runtime_info.get("included"),
            "embeddedRuntime": {
                "included": bool(runtime_info.get("included")),
                "mode": runtime_info.get("mode") or EDITOR_RUNTIME_SOURCE_SYSTEM,
                "modeLabel": runtime_info.get("modeLabel") or "系统 Python 启动",
                "sourceLabel": runtime_info.get("sourceLabel") or "",
                "sourcePath": runtime_info.get("sourcePath") or "",
                "runtimeDirPath": runtime_info.get("runtimeDirPath") or "",
                "warning": runtime_info.get("warning") or "",
            },
            "commercialRelease": {
                "distributionSnapshot": EDITOR_DISTRIBUTION_SNAPSHOT_NAME,
                "commercialReadme": EDITOR_COMMERCIAL_README_NAME,
                "windowsInstallerScript": EDITOR_WINDOWS_INSTALLER_SCRIPT_NAME,
                "windowsInstallerExe": windows_installer_result.get("installerName") or "",
                "windowsInstallerCompiled": bool(windows_installer_result.get("compiled")),
                "windowsInstallerStatus": windows_installer_result.get("statusLabel")
                or "未编译（待配置 Inno Setup 编译器）",
                "windowsInstallerSigned": bool(windows_installer_result.get("installerSigned")),
                "windowsSigningStatus": windows_installer_result.get("signingStatusLabel")
                or "未签名（待配置 Windows 证书/签名工具）",
                "linuxInstallScript": EDITOR_LINUX_INSTALL_SCRIPT_NAME,
                "signingStatus": signing_result.get("statusLabel") or "未签名（待填写开发者身份）",
                "appSigned": bool(signing_result.get("appSigned")),
                "installerSigned": bool(signing_result.get("installerSigned")),
                "notarized": bool(signing_result.get("notarized")),
            },
        },
    }


def write_editor_package_manifest(build_dir: Path, manifest: dict) -> Path:
    manifest_path = build_dir / "editor_package_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def create_macos_editor_app_bundle(
    build_dir: Path,
    bundle_dir: Path,
    distribution_config: dict,
    icon_png_path: Path | None = None,
) -> Path:
    app_dir = build_dir / EDITOR_MAC_APP_NAME
    contents_dir = app_dir / "Contents"
    macos_dir = contents_dir / "MacOS"
    resources_dir = contents_dir / "Resources"
    macos_dir.mkdir(parents=True, exist_ok=True)
    resources_dir.mkdir(parents=True, exist_ok=True)
    app_bundle_dir = resources_dir / EDITOR_BUNDLE_DIR_NAME
    if app_bundle_dir.exists():
        shutil.rmtree(app_bundle_dir, ignore_errors=True)
    shutil.copytree(
        bundle_dir,
        app_bundle_dir,
        symlinks=False,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
    )

    product_name = distribution_config.get("productName") or "Canvasia Engine Editor"
    bundle_identifier = distribution_config.get("bundleIdentifier") or "com.canvasia.engine.editor"
    minimum_system_version = (distribution_config.get("macOS") or {}).get("minimumSystemVersion") or "12.0"
    application_category = (distribution_config.get("macOS") or {}).get("category") or "public.app-category.developer-tools"

    info_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDisplayName</key>
  <string>{html.escape(product_name)}</string>
  <key>CFBundleExecutable</key>
  <string>{EDITOR_MAC_APP_EXECUTABLE}</string>
  <key>CFBundleIdentifier</key>
  <string>{html.escape(bundle_identifier)}</string>
  <key>CFBundleName</key>
  <string>{html.escape(product_name)}</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>{EDITOR_PACKAGE_VERSION}</string>
  <key>CFBundleVersion</key>
  <string>{EDITOR_PACKAGE_VERSION}</string>
  <key>LSMinimumSystemVersion</key>
  <string>{html.escape(minimum_system_version)}</string>
  <key>LSApplicationCategoryType</key>
  <string>{html.escape(application_category)}</string>
  <key>NSHighResolutionCapable</key>
  <true/>
</dict>
</plist>
"""
    (contents_dir / "Info.plist").write_text(info_plist, encoding="utf-8")

    launcher_script = f"""#!/bin/zsh
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BUNDLE_DIR="$APP_ROOT/Resources/{EDITOR_BUNDLE_DIR_NAME}"
EMBEDDED_PYTHON="$BUNDLE_DIR/{EDITOR_RUNTIME_DIR_NAME}/bin/python3"

if [ ! -d "$BUNDLE_DIR" ]; then
  /usr/bin/osascript <<'APPLESCRIPT'
display alert "编辑器资源缺失" message "App 内部没有找到 editor_bundle，请重新导出这份编辑器桌面包。" as critical
APPLESCRIPT
  exit 1
fi

if [ -x "$EMBEDDED_PYTHON" ]; then
  cd "$BUNDLE_DIR"
  exec "$EMBEDDED_PYTHON" run_editor.py
fi

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
if ! command -v python3 >/dev/null 2>&1; then
  /usr/bin/osascript <<'APPLESCRIPT'
display alert "需要先安装 Python 3" message "这个编辑器 App 当前没有内嵌 Python 运行时，请先安装 Python 3 或重新导出一份带内嵌运行时的版本。" as critical
APPLESCRIPT
  exit 1
fi

cd "$BUNDLE_DIR"
exec python3 run_editor.py
"""
    executable_path = macos_dir / EDITOR_MAC_APP_EXECUTABLE
    executable_path.write_text(launcher_script, encoding="utf-8")
    executable_path.chmod(0o755)

    if icon_png_path and icon_png_path.is_file():
        shutil.copy2(icon_png_path, resources_dir / icon_png_path.name)

    return app_dir


def build_macos_editor_installer(build_dir: Path, app_dir: Path, distribution_config: dict) -> Path | None:
    pkgbuild_path = shutil.which("pkgbuild")
    if not pkgbuild_path:
        return None

    installer_root = build_dir / ".editor_pkg_root"
    applications_dir = installer_root / "Applications"
    applications_dir.mkdir(parents=True, exist_ok=True)
    staged_app_dir = applications_dir / app_dir.name
    if staged_app_dir.exists():
        shutil.rmtree(staged_app_dir, ignore_errors=True)
    shutil.copytree(app_dir, staged_app_dir, symlinks=False)

    package_path = build_dir / EDITOR_MAC_INSTALLER_NAME
    subprocess.run(
        [
            pkgbuild_path,
            "--root",
            str(installer_root),
            "--identifier",
            f"{distribution_config.get('bundleIdentifier') or 'com.canvasia.engine.editor'}.installer",
            "--version",
            EDITOR_PACKAGE_VERSION,
            "--install-location",
            "/",
            str(package_path),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return package_path


def build_editor_linux_desktop_entry(distribution_config: dict) -> str:
    app_name = distribution_config.get("productName") or "Canvasia Engine Editor"
    categories = ";".join((distribution_config.get("linux") or {}).get("categories") or ["Development"])
    if not categories.endswith(";"):
        categories += ";"
    return f"""[Desktop Entry]
Type=Application
Name={app_name}
Comment=Canvasia Engine 可视化编辑器
Exec=./{EDITOR_LINUX_START_NAME}
Terminal=true
Icon=app_icon.png
Categories={categories}
"""


def write_editor_linux_desktop_entry(build_dir: Path, distribution_config: dict) -> Path:
    desktop_file_name = (distribution_config.get("linux") or {}).get("desktopFileName") or "Canvasia Engine Editor.desktop"
    desktop_path = build_dir / desktop_file_name
    desktop_path.write_text(build_editor_linux_desktop_entry(distribution_config), encoding="utf-8")
    desktop_path.chmod(0o755)
    return desktop_path


def build_editor_suite_readme(packages: list[dict], distribution_config_path: Path) -> str:
    lines = [
        "Canvasia Engine 三系统编辑器套装",
        "",
        "这份导出会把 macOS / Windows / Linux 三个平台的编辑器包一起整理出来。",
        "每个平台目录里都已经带了编辑器前端、样板项目、导出模板、启动器和内嵌 Python 运行时。",
        f"本次使用的发行配置：{distribution_config_path}",
        f"签名操作手册：{EDITOR_SIGNING_GUIDE_NAME}",
        f"环境变量模板：{EDITOR_SIGNING_ENV_EXAMPLE_NAME}",
        f"签名前自检脚本：{EDITOR_SIGNING_CHECK_SCRIPT_NAME}",
        f"签名前自检启动器：{EDITOR_SIGNING_CHECK_COMMAND_NAME}",
        "",
        "本次已生成的套装：",
    ]
    for package in packages:
        lines.append(
            f"- {package['label']}：{package['archiveName']}"
            + (f"；安装器 {package['installerName']}" if package.get("installerName") else "")
            + (f"；签名状态 {package.get('signingInfo', {}).get('statusLabel')}" if package.get("signingInfo") else "")
        )
    lines.append("")
    lines.append("对应平台目录或压缩包可直接分发给创作者使用。")
    return "\n".join(lines) + "\n"


def write_editor_suite_readme(build_dir: Path, packages: list[dict], distribution_config_path: Path) -> Path:
    readme_path = build_dir / "README_三系统编辑器套装先看这里.txt"
    readme_path.write_text(build_editor_suite_readme(packages, distribution_config_path), encoding="utf-8")
    return readme_path


def build_editor_suite_manifest(build_id: str, packages: list[dict], distribution_config: dict | None = None) -> dict:
    distribution_config = distribution_config or build_default_editor_distribution_config()
    return {
        "formatVersion": EXPORT_MANIFEST_FORMAT_VERSION,
        "buildId": build_id,
        "builtAt": now_iso(),
        "engine": {
            "name": "Canvasia Engine",
            "packageTarget": EXPORT_TARGET_EDITOR_DESKTOP_SUITE,
            "packageTargetLabel": "三系统编辑器套装",
            "releaseVersion": EDITOR_PACKAGE_VERSION,
        },
        "distribution": {
            "productName": distribution_config.get("productName"),
            "bundleIdentifier": distribution_config.get("bundleIdentifier"),
            "publisherName": distribution_config.get("publisherName"),
            "companyName": distribution_config.get("companyName"),
            "website": distribution_config.get("website"),
            "supportUrl": distribution_config.get("supportUrl"),
            "supportEmail": distribution_config.get("supportEmail"),
        },
        "packages": packages,
    }


def write_editor_suite_manifest(build_dir: Path, manifest: dict) -> Path:
    manifest_path = build_dir / "editor_suite_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def build_editor_platform_archive(build_dir: Path, platform_key: str) -> Path:
    target = EDITOR_PORTABLE_RUNTIME_TARGETS[platform_key]
    base_name = str(build_dir)
    archive_format = target.get("archiveFormat") or "zip"
    archive_path = Path(shutil.make_archive(base_name, archive_format, root_dir=build_dir.parent, base_dir=build_dir.name))
    return archive_path


def export_editor_suite_platform_package(
    parent_build_dir: Path,
    platform_key: str,
    distribution_config: dict,
    distribution_config_path: Path,
) -> dict:
    target = EDITOR_PORTABLE_RUNTIME_TARGETS[platform_key]
    platform_dir = parent_build_dir / platform_key
    bundle_dir = platform_dir / EDITOR_BUNDLE_DIR_NAME
    copy_editor_distribution_tree(bundle_dir)
    runtime_info = prepare_editor_portable_runtime(bundle_dir, platform_key)
    distribution_snapshot_path = write_editor_distribution_snapshot(platform_dir, distribution_config)
    signing_support_files = copy_editor_signing_support_files(platform_dir)

    icon_png_bytes = build_export_icon_png({"projectId": f"editor_{platform_key}", "title": distribution_config.get("productName") or "Canvasia Engine Editor"})
    icon_ico_bytes = build_export_icon_ico(icon_png_bytes)
    root_icon_files = write_export_icon_files(platform_dir, icon_png_bytes, icon_ico_bytes)
    write_export_icon_files(bundle_dir, icon_png_bytes, icon_ico_bytes)
    splash_file = write_export_splash_asset(
        platform_dir,
        {"title": distribution_config.get("productName") or "Canvasia Engine Editor", "projectId": f"editor_{platform_key}"},
        EDITOR_PACKAGE_VERSION,
        f"{target['label']} 编辑器包",
    )
    write_export_splash_asset(
        bundle_dir,
        {"title": distribution_config.get("productName") or "Canvasia Engine Editor", "projectId": f"editor_{platform_key}"},
        EDITOR_PACKAGE_VERSION,
        f"{target['label']} 编辑器包",
    )
    launchers = write_editor_root_launchers(platform_dir)
    readme_path = write_editor_package_readme(platform_dir, f"{target['label']} 编辑器包", runtime_info=runtime_info)

    app_path = None
    installer_path = None
    linux_desktop_entry = None
    windows_installer_script = None
    windows_installer_result = {
        "canCompile": False,
        "compiled": False,
        "statusLabel": "未编译（待配置 Inno Setup 编译器）",
        "messages": [],
        "compilerPath": "",
        "runnerPath": "",
        "installerPath": "",
        "installerName": "",
    }
    linux_install_script = None
    windows_signing_result = {
        "canSign": False,
        "installerSigned": False,
        "statusLabel": "未签名（待配置 Windows 证书/签名工具）",
        "messages": [],
        "signToolPath": "",
        "signToolRunner": "",
        "timestampUrl": "",
    }
    signing_result = {
        "statusLabel": "当前平台未执行签名",
        "appSigned": False,
        "installerSigned": False,
        "notarized": False,
        "messages": [],
    }
    if platform_key == EDITOR_PLATFORM_MACOS:
        app_path = create_macos_editor_app_bundle(platform_dir, bundle_dir, distribution_config, root_icon_files["pngPath"])
        installer_path = build_macos_editor_installer(platform_dir, app_path, distribution_config)
        signing_result = attempt_macos_editor_signing(platform_dir, app_path, installer_path, distribution_config)
    elif platform_key == EDITOR_PLATFORM_WINDOWS:
        windows_installer_script = write_editor_windows_installer_script(platform_dir, distribution_config)
        windows_installer_result = attempt_windows_editor_installer_compile(
            platform_dir,
            windows_installer_script,
            distribution_config,
        )
        windows_signing_result = attempt_windows_editor_signing(
            Path(windows_installer_result["installerPath"]) if windows_installer_result.get("installerPath") else None,
            distribution_config,
        )
        windows_installer_result["installerSigned"] = bool(windows_signing_result.get("installerSigned"))
        windows_installer_result["signingStatusLabel"] = (
            windows_signing_result.get("statusLabel") or "未签名（待配置 Windows 证书/签名工具）"
        )
    elif platform_key == EDITOR_PLATFORM_LINUX:
        linux_desktop_entry = write_editor_linux_desktop_entry(platform_dir, distribution_config)
        linux_install_script = write_editor_linux_install_script(platform_dir, distribution_config)

    extra_notes = []
    if windows_installer_script:
        extra_notes.append(f"- 已附带 Windows 安装脚本模板：{windows_installer_script.name}")
        extra_notes.append(f"- Windows 安装器编译状态：{windows_installer_result.get('statusLabel')}")
        if windows_installer_result.get("installerName"):
            extra_notes.append(f"- 已生成 Windows 安装器：{windows_installer_result['installerName']}")
        extra_notes.append(f"- Windows 安装器签名状态：{windows_signing_result.get('statusLabel')}")
    if linux_install_script:
        extra_notes.append(f"- 已附带 Linux 安装脚本：{linux_install_script.name}")
    commercial_readme_path = write_editor_commercial_readme(
        platform_dir,
        f"{target['label']} 编辑器包",
        distribution_config_path,
        distribution_snapshot_path,
        {
            **signing_result,
            "windowsInstallerStatusLabel": windows_installer_result.get("statusLabel"),
            "windowsSigningStatusLabel": windows_signing_result.get("statusLabel"),
            "messages": [
                *(signing_result.get("messages") or []),
                *(windows_installer_result.get("messages") or []),
                *(windows_signing_result.get("messages") or []),
            ],
        },
        distribution_config,
        extra_notes=extra_notes,
    )

    archive_path = build_editor_platform_archive(platform_dir, platform_key)
    return {
        "platform": platform_key,
        "label": target["label"],
        "buildDirName": platform_dir.name,
        "buildPath": str(platform_dir),
        "archiveName": archive_path.name,
        "archivePath": str(archive_path),
        "commandLauncherFileName": launchers["commandPath"].name,
        "windowsLauncherFileName": launchers["windowsPath"].name,
        "linuxLauncherFileName": launchers["linuxPath"].name,
        "readmeName": readme_path.name,
        "readmePath": str(readme_path),
        "runtimeInfo": {
            "included": bool(runtime_info.get("included")),
            "mode": runtime_info.get("mode") or EDITOR_RUNTIME_SOURCE_SYSTEM,
            "modeLabel": runtime_info.get("modeLabel") or "系统 Python 启动",
            "sourceLabel": runtime_info.get("sourceLabel") or "",
            "sourcePath": runtime_info.get("sourcePath") or "",
            "runtimeDirPath": runtime_info.get("runtimeDirPath") or "",
            "warning": runtime_info.get("warning") or "",
        },
        "iconPngName": root_icon_files["pngFileName"],
        "iconIcoName": root_icon_files["icoFileName"],
        "splashName": splash_file["fileName"],
        "distributionSnapshotName": distribution_snapshot_path.name,
        "distributionSnapshotPath": str(distribution_snapshot_path),
        "distributionConfigPath": str(distribution_config_path),
        "signingGuideName": signing_support_files["guideName"],
        "signingGuidePath": signing_support_files["guidePath"],
        "signingGuidePublicUrl": f"/exports/{parent_build_dir.name}/{platform_key}/{signing_support_files['guideName']}",
        "signingEnvExampleName": signing_support_files["envExampleName"],
        "signingEnvExamplePath": signing_support_files["envExamplePath"],
        "signingEnvExamplePublicUrl": (
            f"/exports/{parent_build_dir.name}/{platform_key}/{signing_support_files['envExampleName']}"
        ),
        "signingCheckScriptName": signing_support_files["checkScriptName"],
        "signingCheckScriptPath": signing_support_files["checkScriptPath"],
        "signingCheckScriptPublicUrl": (
            f"/exports/{parent_build_dir.name}/{platform_key}/{signing_support_files['checkScriptName']}"
        ),
        "signingCheckCommandName": signing_support_files["checkCommandName"],
        "signingCheckCommandPath": signing_support_files["checkCommandPath"],
        "signingCheckCommandPublicUrl": (
            f"/exports/{parent_build_dir.name}/{platform_key}/{signing_support_files['checkCommandName']}"
        ),
        "commercialReadmeName": commercial_readme_path.name,
        "commercialReadmePath": str(commercial_readme_path),
        "appName": app_path.name if app_path else "",
        "appPath": str(app_path) if app_path else "",
        "installerName": installer_path.name if installer_path else "",
        "installerPath": str(installer_path) if installer_path else "",
        "windowsInstallerScriptName": windows_installer_script.name if windows_installer_script else "",
        "windowsInstallerScriptPath": str(windows_installer_script) if windows_installer_script else "",
        "windowsInstallerScriptPublicUrl": (
            f"/exports/{parent_build_dir.name}/{platform_key}/{windows_installer_script.name}"
            if windows_installer_script
            else ""
        ),
        "windowsInstallerExeName": windows_installer_result.get("installerName") or "",
        "windowsInstallerExePath": windows_installer_result.get("installerPath") or "",
        "windowsInstallerExePublicUrl": (
            f"/exports/{parent_build_dir.name}/{platform_key}/{windows_installer_result['installerName']}"
            if windows_installer_result.get("installerName")
            else ""
        ),
        "windowsInstallerCompileStatusLabel": windows_installer_result.get("statusLabel")
        or "未编译（待配置 Inno Setup 编译器）",
        "windowsInstallerCompilerPath": windows_installer_result.get("compilerPath") or "",
        "windowsInstallerRunnerPath": windows_installer_result.get("runnerPath") or "",
        "windowsSigningStatusLabel": windows_signing_result.get("statusLabel")
        or "未签名（待配置 Windows 证书/签名工具）",
        "windowsInstallerSigned": bool(windows_signing_result.get("installerSigned")),
        "windowsSignToolPath": windows_signing_result.get("signToolPath") or "",
        "windowsSignToolRunnerPath": windows_signing_result.get("signToolRunner") or "",
        "windowsTimestampUrl": windows_signing_result.get("timestampUrl") or "",
        "linuxDesktopName": linux_desktop_entry.name if linux_desktop_entry else "",
        "linuxDesktopPath": str(linux_desktop_entry) if linux_desktop_entry else "",
        "linuxInstallScriptName": linux_install_script.name if linux_install_script else "",
        "linuxInstallScriptPath": str(linux_install_script) if linux_install_script else "",
        "signingInfo": {
            "statusLabel": (
                windows_signing_result.get("statusLabel")
                if platform_key == EDITOR_PLATFORM_WINDOWS
                else signing_result.get("statusLabel")
            )
            or "未签名（待填写开发者身份）",
            "appSigned": bool(signing_result.get("appSigned")),
            "installerSigned": bool(
                windows_signing_result.get("installerSigned")
                if platform_key == EDITOR_PLATFORM_WINDOWS
                else signing_result.get("installerSigned")
            ),
            "notarized": bool(signing_result.get("notarized")) if platform_key == EDITOR_PLATFORM_MACOS else False,
            "messages": [
                *(signing_result.get("messages") or []),
                *(windows_installer_result.get("messages") or []),
                *(windows_signing_result.get("messages") or []),
            ],
        },
    }


def write_export_app_files(build_dir: Path, export_payload: dict) -> None:
    (build_dir / "index.html").write_text(render_export_index(export_payload), encoding="utf-8")
    shutil.copy2(EXPORT_TEMPLATE_DIR / "player.css", build_dir / "player.css")
    for script_name in EXPORT_PLAYER_SCRIPT_FILES:
        shutil.copy2(EXPORT_TEMPLATE_DIR / script_name, build_dir / script_name)
    runtime_preload_manifest = (export_payload.get("buildInfo") or {}).get("runtimePreloadManifest")
    if isinstance(runtime_preload_manifest, dict):
        write_runtime_preload_files(build_dir, runtime_preload_manifest)
    unlockable_manifest = (export_payload.get("buildInfo") or {}).get("unlockableContentManifest")
    if isinstance(unlockable_manifest, dict):
        write_unlockable_content_manifest_file(build_dir, unlockable_manifest)
        write_unlockable_content_report_file(build_dir, unlockable_manifest)


def format_export_digest_number(value: object) -> str:
    try:
        number = int(value or 0)
    except (TypeError, ValueError):
        number = 0
    return f"{number:,}"


def build_native_3d_asset_export_digest(report_payload: dict | None) -> dict:
    if not isinstance(report_payload, dict):
        return {
            "status": "unavailable",
            "headline": "3D 资产清单暂不可用",
            "summaryLine": "导出时没有拿到可读 3D 报告。",
            "metrics": [],
            "issueAssetIds": [],
            "issueAssets": [],
            "topIssues": [],
            "recommendations": ["手动打开 3D 资产清单确认具体问题。"],
        }

    status = str(report_payload.get("status") or "unavailable")
    summary = report_payload.get("summary") if isinstance(report_payload.get("summary"), dict) else {}
    entries = report_payload.get("entries") if isinstance(report_payload.get("entries"), list) else []
    recommendations = report_payload.get("recommendations") if isinstance(report_payload.get("recommendations"), list) else []

    if status == "no_3d_assets":
        headline = "当前项目没有 3D 资产"
    elif status == "ready":
        headline = "3D 资产发布体检通过"
    elif status == "needs_attention":
        headline = "3D 资产需要发布前处理"
    else:
        headline = "3D 资产清单需要复核"

    risk_counts = {
        "性能预算": int(summary.get("performanceBudgetIssueCount") or 0),
        "GLB/VRM 容器": int(summary.get("glbContainerIssueCount") or 0),
        "内部引用": int(summary.get("gltfIntegrityIssueCount") or 0),
        "贴图槽": int(summary.get("textureSlotIssueCount") or 0),
        "外部依赖": int(summary.get("missingDependencyCount") or 0),
        "空结构": int(summary.get("emptyStructureCount") or 0),
    }
    risk_preview = " / ".join(f"{label} {count}" for label, count in risk_counts.items() if count > 0)
    if not risk_preview:
        risk_preview = "暂无明显 3D 风险" if int(summary.get("assetCount") or 0) else "未检测到 3D 资产"
    summary_line = (
        f"资产 {int(summary.get('assetCount') or 0)} 个，问题 {int(summary.get('issueCount') or 0)} 个；{risk_preview}。"
    )

    metrics = [
        {"label": "3D 资产", "value": f"{int(summary.get('assetCount') or 0)} 个"},
        {"label": "问题", "value": f"{int(summary.get('issueCount') or 0)} 个"},
        {"label": "性能预算", "value": f"{int(summary.get('performanceBudgetIssueCount') or 0)} 项"},
        {"label": "估算三角面", "value": format_export_digest_number(summary.get("estimatedTriangleCount"))},
        {"label": "Draw Call", "value": format_export_digest_number(summary.get("drawCallCount"))},
        {"label": "未使用", "value": f"{int(summary.get('unusedCount') or 0)} 个"},
    ]

    issue_assets = []
    for entry in entries:
        if not isinstance(entry, dict) or str(entry.get("status") or "") == "ready":
            continue
        entry_name = str(entry.get("name") or entry.get("assetId") or "未命名 3D 资产")
        issue_parts: list[str] = []
        issue_breakdown: list[dict] = []
        dependency = entry.get("dependencyHealth") if isinstance(entry.get("dependencyHealth"), dict) else {}
        preview_probe = entry.get("previewProbe") if isinstance(entry.get("previewProbe"), dict) else {}
        integrity_probe = entry.get("gltfIntegrityProbe") if isinstance(entry.get("gltfIntegrityProbe"), dict) else {}
        container_probe = entry.get("glbContainerProbe") if isinstance(entry.get("glbContainerProbe"), dict) else {}
        budget_probe = entry.get("performanceBudgetProbe") if isinstance(entry.get("performanceBudgetProbe"), dict) else {}

        budget_issue_count = int(budget_probe.get("issueCount") or 0)
        if budget_issue_count:
            issue_parts.append(f"性能预算 {budget_issue_count} 项")
            issue_breakdown.append({"code": "performance_budget", "label": "性能预算", "count": budget_issue_count})
        container_issue_count = int(container_probe.get("issueCount") or 0)
        if container_issue_count:
            issue_parts.append(f"容器 {container_issue_count} 项")
            issue_breakdown.append({"code": "glb_container", "label": "GLB/VRM 容器", "count": container_issue_count})
        integrity_issue_count = int(integrity_probe.get("issueCount") or 0)
        if integrity_issue_count:
            issue_parts.append(f"内部引用 {integrity_issue_count} 项")
            issue_breakdown.append({"code": "gltf_integrity", "label": "内部引用", "count": integrity_issue_count})
        texture_issue_count = int(preview_probe.get("textureSlotIssueCount") or 0)
        if texture_issue_count:
            issue_parts.append(f"贴图槽 {texture_issue_count} 项")
            issue_breakdown.append({"code": "texture_slot", "label": "贴图槽", "count": texture_issue_count})
        dependency_gap_count = len(dependency.get("missing") or []) + len(dependency.get("unsafe") or [])
        if dependency_gap_count:
            issue_parts.append(f"依赖 {dependency_gap_count} 项")
            issue_breakdown.append({"code": "dependency", "label": "外部依赖", "count": dependency_gap_count})
        if not issue_parts:
            issue_parts.append(str(entry.get("statusLabel") or "需要复核"))

        usage_preview: list[str] = []
        usages = entry.get("usages") if isinstance(entry.get("usages"), list) else []
        for usage in usages[:3]:
            if not isinstance(usage, dict):
                continue
            if usage.get("kind") == "character_model":
                usage_preview.append(f"角色：{usage.get('characterName') or usage.get('characterId') or '未命名角色'}")
            else:
                scene_label = " / ".join(
                    str(part)
                    for part in [usage.get("chapterName"), usage.get("sceneName")]
                    if str(part or "").strip()
                )
                block_index = usage.get("blockIndex")
                if isinstance(block_index, int):
                    scene_label = f"{scene_label or '场景'} · 第 {block_index + 1} 张卡片"
                usage_preview.append(scene_label or str(usage.get("kindLabel") or "剧情引用"))

        issue_assets.append(
            {
                "assetId": str(entry.get("assetId") or ""),
                "type": str(entry.get("type") or ""),
                "name": entry_name,
                "typeLabel": str(entry.get("typeLabel") or "3D 资产"),
                "exportUrl": str(entry.get("exportUrl") or ""),
                "status": str(entry.get("status") or ""),
                "statusLabel": str(entry.get("statusLabel") or "需要复核"),
                "summary": " / ".join(issue_parts),
                "issueCount": sum(int(item.get("count") or 0) for item in issue_breakdown) or len(issue_parts),
                "issueBreakdown": issue_breakdown,
                "usageCount": int(entry.get("usageCount") or 0),
                "usagePreview": usage_preview,
                "recommendedAction": str(entry.get("recommendedAction") or "复核 3D 资产导入状态。"),
            }
        )

    issue_asset_ids = []
    seen_issue_asset_ids = set()
    for issue in issue_assets:
        asset_id = str(issue.get("assetId") or "").strip()
        if asset_id and asset_id not in seen_issue_asset_ids:
            seen_issue_asset_ids.add(asset_id)
            issue_asset_ids.append(asset_id)

    return {
        "status": status,
        "headline": headline,
        "summaryLine": summary_line,
        "metrics": metrics,
        "riskCounts": risk_counts,
        "issueAssetIds": issue_asset_ids[:50],
        "issueAssets": issue_assets[:50],
        "topIssues": issue_assets[:5],
        "recommendations": [str(recommendation) for recommendation in recommendations[:4]],
    }


def get_native_runtime_release_control_report_names() -> dict:
    return {
        "releaseCheck": NATIVE_RUNTIME_RELEASE_CHECK_NAME,
        "releaseCandidateReport": NATIVE_RUNTIME_RC_REPORT_NAME,
        "asset3dDigest": NATIVE_RUNTIME_3D_ASSET_DIGEST_NAME,
        "releaseControlReport": NATIVE_RUNTIME_RELEASE_CONTROL_REPORT_NAME,
        "releaseControlJson": NATIVE_RUNTIME_RELEASE_CONTROL_JSON_NAME,
        "fileIntegrityReport": NATIVE_RUNTIME_FILE_INTEGRITY_REPORT_NAME,
        "fileIntegrityMarkdown": NATIVE_RUNTIME_FILE_INTEGRITY_MARKDOWN_NAME,
        "vnBaselineQualityMarkdown": NATIVE_RUNTIME_VN_BASELINE_QUALITY_MARKDOWN_NAME,
        "vnBaselineQualityJson": NATIVE_RUNTIME_VN_BASELINE_QUALITY_REPORT_NAME,
        "performanceBudgetMarkdown": NATIVE_RUNTIME_PERFORMANCE_BUDGET_MARKDOWN_NAME,
        "performanceBudgetJson": NATIVE_RUNTIME_PERFORMANCE_BUDGET_REPORT_NAME,
    }


def get_native_runtime_release_control_status(
    release_check_payload: dict | None,
    rc_report_payload: dict | None,
    asset3d_digest: dict | None,
    performance_budget_payload: dict | None = None,
    vn_baseline_quality_payload: dict | None = None,
) -> dict:
    return get_release_control_status(
        release_check_payload,
        rc_report_payload,
        asset3d_digest,
        performance_budget_payload,
        vn_baseline_quality_payload,
    )


def build_native_runtime_release_control_next_steps(
    release_check_payload: dict | None,
    rc_report_payload: dict | None,
    asset3d_digest: dict | None,
    performance_budget_payload: dict | None,
    vn_baseline_quality_payload: dict | None,
    quality_gate: dict,
) -> list[str]:
    return build_release_control_next_steps(
        release_check_payload,
        rc_report_payload,
        asset3d_digest,
        performance_budget_payload,
        vn_baseline_quality_payload,
        quality_gate,
    )


def build_native_runtime_release_control_payload(
    export_payload: dict,
    release_check_payload: dict | None,
    rc_report_payload: dict | None,
    asset3d_digest: dict | None,
    performance_budget_payload: dict | None = None,
    vn_baseline_quality_payload: dict | None = None,
) -> dict:
    return build_release_control_payload(
        export_payload,
        release_check_payload,
        rc_report_payload,
        asset3d_digest,
        performance_budget_payload,
        vn_baseline_quality_payload,
        report_names=get_native_runtime_release_control_report_names(),
        export_target=EXPORT_TARGET_NATIVE_RUNTIME,
        default_release_version=DEFAULT_EXPORT_RELEASE_VERSION,
    )


def build_native_runtime_release_control_markdown(payload: dict) -> str:
    return build_release_control_markdown_payload(
        payload,
        default_release_version=DEFAULT_EXPORT_RELEASE_VERSION,
    )


def refresh_native_runtime_preload_report(build_dir: Path, report_path: Path) -> bool:
    runtime_preload_markdown = subprocess.run(
        [
            sys.executable,
            str(build_dir / NATIVE_RUNTIME_PLAYER_NAME),
            "--describe-runtime-preload-markdown",
            str(build_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if not runtime_preload_markdown.stdout.strip():
        return False
    report_path.write_text(runtime_preload_markdown.stdout.rstrip() + "\n", encoding="utf-8")
    return True


def write_native_runtime_performance_budget_reports(build_dir: Path) -> dict:
    report_path = build_dir / NATIVE_RUNTIME_PERFORMANCE_BUDGET_REPORT_NAME
    markdown_path = build_dir / NATIVE_RUNTIME_PERFORMANCE_BUDGET_MARKDOWN_NAME
    performance_budget = subprocess.run(
        [
            sys.executable,
            str(build_dir / NATIVE_RUNTIME_PLAYER_NAME),
            "--write-performance-budget-reports",
            str(build_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    payload = None
    if report_path.is_file():
        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = None
    if not isinstance(payload, dict):
        message = performance_budget.stderr.strip() or performance_budget.stdout.strip() or "性能预算报告生成失败。"
        payload = {
            "formatVersion": 1,
            "generatedAt": now_iso(),
            "status": "unavailable",
            "summary": {
                "statusLabel": "报告未生成",
                "recommendation": message,
            },
            "issues": [
                {
                    "severity": "warn",
                    "code": "performance_budget_unavailable",
                    "title": "性能预算报告未生成",
                    "detail": message,
                    "suggestion": "可手动运行 python runtime_player.py --write-performance-budget-reports . 重新生成。",
                }
            ],
        }
        report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        markdown_path.write_text(
            "\n".join(
                [
                    "# 原生 Runtime 性能预算报告",
                    "",
                    "- 状态：报告未生成",
                    f"- 原因：{message}",
                    "",
                    "可手动运行：",
                    "",
                    "```bash",
                    "python3 runtime_player.py --write-performance-budget-reports .",
                    "```",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return {
        "performanceBudgetStatus": str(payload.get("status") or "unavailable"),
        "performanceBudgetSummary": summary,
        "performanceBudgetPayload": payload,
        "performanceBudgetReportName": report_path.name,
        "performanceBudgetReportPath": str(report_path),
        "performanceBudgetMarkdownName": markdown_path.name,
        "performanceBudgetMarkdownPath": str(markdown_path),
    }


def write_native_runtime_files(build_dir: Path, export_payload: dict) -> dict:
    game_data_path = build_dir / "game_data.json"
    game_data_path.write_text(json.dumps(export_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    unlockable_manifest = (export_payload.get("buildInfo") or {}).get("unlockableContentManifest")
    unlockable_manifest_path = write_unlockable_content_manifest_file(
        build_dir,
        unlockable_manifest if isinstance(unlockable_manifest, dict) else {},
    )
    unlockable_report_path = write_unlockable_content_report_file(
        build_dir,
        unlockable_manifest if isinstance(unlockable_manifest, dict) else {},
    )
    runtime_preload_manifest = (export_payload.get("buildInfo") or {}).get("runtimePreloadManifest")
    runtime_preload_files = write_runtime_preload_files(
        build_dir,
        runtime_preload_manifest if isinstance(runtime_preload_manifest, dict) else {},
    )

    for source_path, target_name in NATIVE_RUNTIME_REQUIRED_MODULE_FILES:
        shutil.copy2(source_path, build_dir / target_name)
    shutil.copy2(NATIVE_RUNTIME_README_SOURCE, build_dir / NATIVE_RUNTIME_README_NAME)
    shutil.copy2(NATIVE_RUNTIME_REQUIREMENTS_SOURCE, build_dir / NATIVE_RUNTIME_REQUIREMENTS_NAME)
    shutil.copy2(NATIVE_RUNTIME_BUILD_REQUIREMENTS_SOURCE, build_dir / NATIVE_RUNTIME_BUILD_REQUIREMENTS_NAME)
    if NATIVE_RUNTIME_VIDEO_REQUIREMENTS_SOURCE.is_file():
        shutil.copy2(NATIVE_RUNTIME_VIDEO_REQUIREMENTS_SOURCE, build_dir / NATIVE_RUNTIME_VIDEO_REQUIREMENTS_NAME)
    shutil.copy2(NATIVE_RUNTIME_APP_BUILDER_SOURCE, build_dir / NATIVE_RUNTIME_APP_BUILDER_NAME)
    if NATIVE_RUNTIME_BRAND_LOGO_SOURCE.is_file():
        brand_logo_path = build_dir / NATIVE_RUNTIME_BRAND_LOGO_NAME
        brand_logo_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(NATIVE_RUNTIME_BRAND_LOGO_SOURCE, brand_logo_path)

    # Render the public preload report through the copied runtime so it stays aligned with player diagnostics.
    refresh_native_runtime_preload_report(build_dir, Path(runtime_preload_files["runtimePreloadReportPath"]))
    performance_budget_files = write_native_runtime_performance_budget_reports(build_dir)

    mac_launcher_path = build_dir / NATIVE_RUNTIME_MAC_COMMAND_NAME
    linux_launcher_path = build_dir / NATIVE_RUNTIME_LINUX_COMMAND_NAME
    windows_launcher_path = build_dir / NATIVE_RUNTIME_WINDOWS_COMMAND_NAME
    mac_rc_path = build_dir / NATIVE_RUNTIME_MAC_RC_COMMAND_NAME
    linux_rc_path = build_dir / NATIVE_RUNTIME_LINUX_RC_COMMAND_NAME
    windows_rc_path = build_dir / NATIVE_RUNTIME_WINDOWS_RC_COMMAND_NAME
    mac_release_control_path = build_dir / NATIVE_RUNTIME_MAC_RELEASE_CONTROL_COMMAND_NAME
    linux_release_control_path = build_dir / NATIVE_RUNTIME_LINUX_RELEASE_CONTROL_COMMAND_NAME
    windows_release_control_path = build_dir / NATIVE_RUNTIME_WINDOWS_RELEASE_CONTROL_COMMAND_NAME
    mac_acceptance_path = build_dir / NATIVE_RUNTIME_MAC_ACCEPTANCE_COMMAND_NAME
    linux_acceptance_path = build_dir / NATIVE_RUNTIME_LINUX_ACCEPTANCE_COMMAND_NAME
    windows_acceptance_path = build_dir / NATIVE_RUNTIME_WINDOWS_ACCEPTANCE_COMMAND_NAME
    mac_file_integrity_path = build_dir / NATIVE_RUNTIME_MAC_FILE_INTEGRITY_COMMAND_NAME
    linux_file_integrity_path = build_dir / NATIVE_RUNTIME_LINUX_FILE_INTEGRITY_COMMAND_NAME
    windows_file_integrity_path = build_dir / NATIVE_RUNTIME_WINDOWS_FILE_INTEGRITY_COMMAND_NAME
    mac_app_builder_path = build_dir / NATIVE_RUNTIME_MAC_APP_BUILDER_COMMAND_NAME
    linux_app_builder_path = build_dir / NATIVE_RUNTIME_LINUX_APP_BUILDER_COMMAND_NAME
    windows_app_builder_path = build_dir / NATIVE_RUNTIME_WINDOWS_APP_BUILDER_COMMAND_NAME
    release_check_path = build_dir / NATIVE_RUNTIME_RELEASE_CHECK_NAME
    rc_report_path = build_dir / NATIVE_RUNTIME_RC_REPORT_NAME
    release_control_report_path = build_dir / NATIVE_RUNTIME_RELEASE_CONTROL_REPORT_NAME
    release_control_json_path = build_dir / NATIVE_RUNTIME_RELEASE_CONTROL_JSON_NAME
    vn_baseline_report_path = build_dir / NATIVE_RUNTIME_VN_BASELINE_QUALITY_REPORT_NAME
    vn_baseline_markdown_path = build_dir / NATIVE_RUNTIME_VN_BASELINE_QUALITY_MARKDOWN_NAME
    asset3d_report_path = build_dir / NATIVE_RUNTIME_3D_ASSET_REPORT_NAME
    asset3d_summary_path = build_dir / NATIVE_RUNTIME_3D_ASSET_SUMMARY_NAME
    asset3d_digest_path = build_dir / NATIVE_RUNTIME_3D_ASSET_DIGEST_NAME

    mac_launcher_path.write_text(
        "\n".join(
            [
                "#!/bin/bash",
                'set -e',
                'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"',
                'cd "$SCRIPT_DIR"',
                'python3 runtime_player.py game_data.json || {',
                '  echo ""',
                '  echo "原生 Runtime 包没有启动成功。请先确认 Python 3 和 pygame-ce 已安装。"',
                '  echo "安装命令：python3 -m pip install -r requirements-native-runtime.txt"',
                '  echo ""',
                '  read -r -p "按回车关闭..." _',
                '  exit 1',
                '}',
                "",
            ]
        ),
        encoding="utf-8",
    )
    linux_launcher_path.write_text(
        "\n".join(
            [
                "#!/bin/bash",
                'set -e',
                'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"',
                'cd "$SCRIPT_DIR"',
                'python3 runtime_player.py game_data.json',
                "",
            ]
        ),
        encoding="utf-8",
    )
    windows_launcher_path.write_text(
        "\r\n".join(
            [
                "@echo off",
                "cd /d %~dp0",
                "python runtime_player.py game_data.json",
                "if errorlevel 1 (",
                "  echo.",
                "  echo 原生 Runtime 包没有启动成功，请先确认 Python 3 和 pygame-ce 已安装。",
                "  echo 安装命令：python -m pip install -r requirements-native-runtime.txt",
                "  pause",
                ")",
                "",
            ]
        ),
        encoding="utf-8",
    )
    mac_rc_path.write_text(
        "\n".join(
            [
                "#!/bin/bash",
                "set -e",
                "set -o pipefail",
                'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"',
                'cd "$SCRIPT_DIR"',
                'python3 runtime_player.py --release-candidate-report . | tee native-runtime-release-candidate-report.json || {',
                '  echo ""',
                '  echo "发布候选检查发现阻塞项，报告已写入 native-runtime-release-candidate-report.json。"',
                '  echo "请先按报告修复，再继续打包或分发。"',
                '  echo ""',
                '  read -r -p "按回车关闭..." _',
                '  exit 1',
                '}',
                'echo ""',
                'echo "发布候选检查完成，报告已写入 native-runtime-release-candidate-report.json。"',
                'read -r -p "按回车关闭..." _',
                "",
            ]
        ),
        encoding="utf-8",
    )
    linux_rc_path.write_text(
        "\n".join(
            [
                "#!/bin/bash",
                "set -e",
                "set -o pipefail",
                'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"',
                'cd "$SCRIPT_DIR"',
                'python3 runtime_player.py --release-candidate-report . | tee native-runtime-release-candidate-report.json',
                "",
            ]
        ),
        encoding="utf-8",
    )
    windows_rc_path.write_text(
        "\r\n".join(
            [
                "@echo off",
                "cd /d %~dp0",
                "python runtime_player.py --release-candidate-report . > native-runtime-release-candidate-report.json",
                "if errorlevel 1 (",
                "  echo.",
                "  echo 发布候选检查发现阻塞项，报告已写入 native-runtime-release-candidate-report.json。",
                "  echo 请先按报告修复，再继续打包或分发。",
                "  pause",
                "  exit /b 1",
                ")",
                "echo.",
                "echo 发布候选检查完成，报告已写入 native-runtime-release-candidate-report.json。",
                "pause",
                "",
            ]
        ),
        encoding="utf-8",
    )
    mac_release_control_path.write_text(
        "\n".join(
            [
                "#!/bin/bash",
                "set -e",
                'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"',
                'cd "$SCRIPT_DIR"',
                'python3 runtime_player.py --write-release-control-reports . || {',
                '  echo ""',
                '  echo "发布总控报告没有生成成功。请先确认 Python 3 和 pygame-ce 已安装。"',
                '  echo "安装命令：python3 -m pip install -r requirements-native-runtime.txt"',
                '  echo ""',
                '  read -r -p "按回车关闭..." _',
                '  exit 1',
                '}',
                'echo ""',
                'echo "发布总控报告已生成：native-runtime-release-control-report.md / .json"',
                'read -r -p "按回车关闭..." _',
                "",
            ]
        ),
        encoding="utf-8",
    )
    linux_release_control_path.write_text(
        "\n".join(
            [
                "#!/bin/bash",
                "set -e",
                'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"',
                'cd "$SCRIPT_DIR"',
                'python3 runtime_player.py --write-release-control-reports .',
                "",
            ]
        ),
        encoding="utf-8",
    )
    windows_release_control_path.write_text(
        "\r\n".join(
            [
                "@echo off",
                "cd /d %~dp0",
                "python runtime_player.py --write-release-control-reports .",
                "if errorlevel 1 (",
                "  echo.",
                "  echo 发布总控报告没有生成成功，请先确认 Python 3 和 pygame-ce 已安装。",
                "  echo 安装命令：python -m pip install -r requirements-native-runtime.txt",
                "  pause",
                "  exit /b 1",
                ")",
                "echo.",
                "echo 发布总控报告已生成：native-runtime-release-control-report.md / .json",
                "pause",
                "",
            ]
        ),
        encoding="utf-8",
    )
    mac_acceptance_path.write_text(
        "\n".join(
            [
                "#!/bin/bash",
                "set -e",
                'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"',
                'cd "$SCRIPT_DIR"',
                'python3 runtime_player.py --write-acceptance-reports . || {',
                '  echo ""',
                '  echo "发布验收清单没有生成成功。请先运行发布总控报告和文件完整性校验。"',
                '  echo "可手动执行：python3 runtime_player.py --write-acceptance-reports ."',
                '  echo ""',
                '  read -r -p "按回车关闭..." _',
                '  exit 1',
                '}',
                'echo ""',
                'echo "发布验收清单已生成：native-runtime-release-acceptance.md / .json"',
                'read -r -p "按回车关闭..." _',
                "",
            ]
        ),
        encoding="utf-8",
    )
    linux_acceptance_path.write_text(
        "\n".join(
            [
                "#!/bin/bash",
                "set -e",
                'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"',
                'cd "$SCRIPT_DIR"',
                'python3 runtime_player.py --write-acceptance-reports .',
                "",
            ]
        ),
        encoding="utf-8",
    )
    windows_acceptance_path.write_text(
        "\r\n".join(
            [
                "@echo off",
                "cd /d %~dp0",
                "python runtime_player.py --write-acceptance-reports .",
                "if errorlevel 1 (",
                "  echo.",
                "  echo 发布验收清单没有生成成功，请先运行发布总控报告和文件完整性校验。",
                "  echo 可手动执行：python runtime_player.py --write-acceptance-reports .",
                "  pause",
                "  exit /b 1",
                ")",
                "echo.",
                "echo 发布验收清单已生成：native-runtime-release-acceptance.md / .json",
                "pause",
                "",
            ]
        ),
        encoding="utf-8",
    )
    mac_file_integrity_path.write_text(
        "\n".join(
            [
                "#!/bin/bash",
                "set -e",
                'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"',
                'cd "$SCRIPT_DIR"',
                'python3 runtime_player.py --verify-file-integrity . || {',
                '  echo ""',
                '  echo "文件完整性校验未通过。请重新下载或重新导出原生 Runtime 包。"',
                '  echo ""',
                '  read -r -p "按回车关闭..." _',
                '  exit 1',
                '}',
                'echo ""',
                'echo "文件完整性校验通过。"',
                'read -r -p "按回车关闭..." _',
                "",
            ]
        ),
        encoding="utf-8",
    )
    linux_file_integrity_path.write_text(
        "\n".join(
            [
                "#!/bin/bash",
                "set -e",
                'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"',
                'cd "$SCRIPT_DIR"',
                'python3 runtime_player.py --verify-file-integrity .',
                "",
            ]
        ),
        encoding="utf-8",
    )
    windows_file_integrity_path.write_text(
        "\r\n".join(
            [
                "@echo off",
                "cd /d %~dp0",
                "python runtime_player.py --verify-file-integrity .",
                "if errorlevel 1 (",
                "  echo.",
                "  echo 文件完整性校验未通过，请重新下载或重新导出原生 Runtime 包。",
                "  pause",
                "  exit /b 1",
                ")",
                "echo.",
                "echo 文件完整性校验通过。",
                "pause",
                "",
            ]
        ),
        encoding="utf-8",
    )
    mac_app_builder_path.write_text(
        "\n".join(
            [
                "#!/bin/bash",
                "set -e",
                'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"',
                'cd "$SCRIPT_DIR"',
                'python3 -m pip install -r requirements-native-runtime.txt -r requirements-native-runtime-build.txt',
                'python3 build_native_runtime_app.py --mode onedir . || {',
                '  echo ""',
                '  echo "原生 Runtime 应用打包没有完成。请确认 Python 3、pygame-ce 和 PyInstaller 已安装。"',
                '  echo "可手动执行：python3 build_native_runtime_app.py --mode onedir ."',
                '  echo ""',
                '  read -r -p "按回车关闭..." _',
                '  exit 1',
                '}',
                'echo ""',
                'echo "打包完成，输出目录：native_app_dist/"',
                'echo "同时会生成 native_app_package_manifest.json 和平台 Preview zip。"',
                'read -r -p "按回车关闭..." _',
                "",
            ]
        ),
        encoding="utf-8",
    )
    linux_app_builder_path.write_text(
        "\n".join(
            [
                "#!/bin/bash",
                "set -e",
                'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"',
                'cd "$SCRIPT_DIR"',
                'python3 -m pip install -r requirements-native-runtime.txt -r requirements-native-runtime-build.txt',
                'python3 build_native_runtime_app.py --mode onedir .',
                "",
            ]
        ),
        encoding="utf-8",
    )
    windows_app_builder_path.write_text(
        "\r\n".join(
            [
                "@echo off",
                "cd /d %~dp0",
                "python -m pip install -r requirements-native-runtime.txt -r requirements-native-runtime-build.txt",
                "python build_native_runtime_app.py --mode onedir .",
                "if errorlevel 1 (",
                "  echo.",
                "  echo 原生 Runtime 应用打包没有完成，请确认 Python 3、pygame-ce 和 PyInstaller 已安装。",
                "  echo 可手动执行：python build_native_runtime_app.py --mode onedir .",
                "  pause",
                "  exit /b 1",
                ")",
                "echo.",
                "echo 打包完成，输出目录：native_app_dist\\",
                "echo 同时会生成 native_app_package_manifest.json 和平台 Preview zip。",
                "pause",
                "",
            ]
        ),
        encoding="utf-8",
    )
    mac_launcher_path.chmod(0o755)
    linux_launcher_path.chmod(0o755)
    mac_rc_path.chmod(0o755)
    linux_rc_path.chmod(0o755)
    mac_release_control_path.chmod(0o755)
    linux_release_control_path.chmod(0o755)
    mac_acceptance_path.chmod(0o755)
    linux_acceptance_path.chmod(0o755)
    mac_file_integrity_path.chmod(0o755)
    linux_file_integrity_path.chmod(0o755)
    mac_app_builder_path.chmod(0o755)
    linux_app_builder_path.chmod(0o755)

    release_check = subprocess.run(
        [
            sys.executable,
            str(build_dir / NATIVE_RUNTIME_PLAYER_NAME),
            "--release-check",
            str(build_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if release_check.returncode == 0:
        release_check_path.write_text(release_check.stdout, encoding="utf-8")
    else:
        release_check_path.write_text(
            json.dumps(
                {
                    "status": "fail",
                    "checkedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
                    "summary": {"errors": 1, "warnings": 0},
                    "issues": [
                        {
                            "severity": "error",
                            "code": "release_check_generation_failed",
                            "message": release_check.stderr.strip() or release_check.stdout.strip() or "发布前自检生成失败。",
                            "suggestion": "手动运行 python runtime_player.py --release-check . 查看具体问题。",
                            "path": NATIVE_RUNTIME_PLAYER_NAME,
                        }
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    try:
        release_check_payload = json.loads(release_check_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        release_check_payload = {
            "status": "unavailable",
            "summary": {"errors": 1, "warnings": 0},
            "issues": [
                {
                    "severity": "error",
                    "code": "release_check_payload_invalid",
                    "message": "发布前自检报告不是有效 JSON。",
                    "suggestion": "手动运行 python runtime_player.py --release-check . 查看具体问题。",
                }
            ],
        }
    asset3d_report = subprocess.run(
        [
            sys.executable,
            str(build_dir / NATIVE_RUNTIME_PLAYER_NAME),
            "--describe-3d-assets",
            str(build_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    asset3d_report_payload = None
    try:
        asset3d_report_payload = json.loads(asset3d_report.stdout)
        asset3d_report_path.write_text(asset3d_report.stdout, encoding="utf-8")
    except json.JSONDecodeError:
        asset3d_report_payload = {
            "status": "unavailable",
            "checkedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
            "summary": {"assetCount": 0, "issueCount": 1},
            "recommendations": ["手动运行 python runtime_player.py --describe-3d-assets . 查看具体问题。"],
            "message": asset3d_report.stderr.strip() or asset3d_report.stdout.strip() or "3D 资产清单生成失败。",
            "entries": [],
        }
        asset3d_report_path.write_text(
            json.dumps(asset3d_report_payload, ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
    asset3d_summary = subprocess.run(
        [
            sys.executable,
            str(build_dir / NATIVE_RUNTIME_PLAYER_NAME),
            "--describe-3d-assets-markdown",
            str(build_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if asset3d_summary.returncode == 0 and asset3d_summary.stdout.strip():
        asset3d_summary_path.write_text(asset3d_summary.stdout, encoding="utf-8")
    else:
        fallback_message = asset3d_summary.stderr.strip() or asset3d_summary.stdout.strip() or "3D 资产摘要生成失败。"
        asset3d_summary_path.write_text(
            "\n".join(
                [
                    "# 3D 资产清单摘要",
                    "",
                    "Markdown 摘要暂不可用。",
                    "",
                    f"- 原因：{fallback_message}",
                    "- 可改用 native-runtime-3d-asset-report.json 查看机器可读清单。",
                    "",
                ]
            ),
            encoding="utf-8",
        )
    rc_report = subprocess.run(
        [
            sys.executable,
            str(build_dir / NATIVE_RUNTIME_PLAYER_NAME),
            "--release-candidate-report",
            str(build_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    rc_report_payload = None
    try:
        rc_report_payload = json.loads(rc_report.stdout)
        rc_report_path.write_text(rc_report.stdout, encoding="utf-8")
    except json.JSONDecodeError:
        rc_report_payload = {
            "status": "unavailable",
            "checkedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
            "summary": {"blockers": 1, "optionalFailures": 0, "warnings": 0},
            "message": rc_report.stderr.strip() or rc_report.stdout.strip() or "发布候选总报告生成失败。",
            "nextActions": ["手动运行 python runtime_player.py --release-candidate-report . 查看具体问题。"],
        }
        rc_report_path.write_text(
            json.dumps(rc_report_payload, ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
    rc_report_summary = rc_report_payload.get("summary") if isinstance(rc_report_payload, dict) else {}
    rc_report_readiness = rc_report_payload.get("readinessEstimate") if isinstance(rc_report_payload, dict) else {}
    asset3d_report_summary = asset3d_report_payload.get("summary") if isinstance(asset3d_report_payload, dict) else {}
    asset3d_report_digest = build_native_3d_asset_export_digest(asset3d_report_payload if isinstance(asset3d_report_payload, dict) else None)
    asset3d_digest_path.write_text(
        json.dumps(asset3d_report_digest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    release_control_payload = None
    release_control_writer = subprocess.run(
        [
            sys.executable,
            str(build_dir / NATIVE_RUNTIME_PLAYER_NAME),
            "--write-release-control-reports",
            str(build_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if release_control_writer.returncode == 0 and release_control_json_path.is_file():
        try:
            release_control_payload = json.loads(release_control_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            release_control_payload = None
    if not isinstance(release_control_payload, dict):
        release_control_payload = build_native_runtime_release_control_payload(
            export_payload,
            release_check_payload if isinstance(release_check_payload, dict) else None,
            rc_report_payload if isinstance(rc_report_payload, dict) else None,
            asset3d_report_digest,
            performance_budget_files.get("performanceBudgetPayload"),
        )
        release_control_json_path.write_text(
            json.dumps(release_control_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        release_control_report_path.write_text(
            build_native_runtime_release_control_markdown(release_control_payload),
            encoding="utf-8",
        )
        if not vn_baseline_report_path.is_file():
            vn_baseline_report_path.write_text(
                json.dumps(
                    {
                        "formatVersion": 1,
                        "status": "unavailable",
                        "generatedAt": now_iso(),
                        "summary": {
                            "statusLabel": "未生成",
                            "issueCount": 1,
                            "warnCount": 1,
                            "softCount": 0,
                            "recommendation": release_control_writer.stderr.strip()
                            or release_control_writer.stdout.strip()
                            or "可手动运行 python runtime_player.py --write-release-control-reports . 重新生成。",
                        },
                        "metrics": {},
                        "issues": [],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        if not vn_baseline_markdown_path.is_file():
            vn_baseline_markdown_path.write_text(
                "\n".join(
                    [
                        "# 原生 Runtime VN 基础质感报告",
                        "",
                        "报告暂未生成。",
                        "",
                        "- 可手动运行 `python runtime_player.py --write-release-control-reports .` 重新生成。",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

    playtest_guide_path = write_export_playtest_guide_file(
        build_dir,
        project=export_payload.get("project") or {},
        target_label=str((export_payload.get("buildInfo") or {}).get("exportTargetLabel") or "原生 Runtime 包"),
        release_version=str((export_payload.get("buildInfo") or {}).get("releaseVersion") or DEFAULT_EXPORT_RELEASE_VERSION),
        launch_steps=[
            f"macOS：双击 `{NATIVE_RUNTIME_MAC_COMMAND_NAME}`。",
            f"Linux：运行 `./{NATIVE_RUNTIME_LINUX_COMMAND_NAME}`。",
            f"Windows：双击 `{NATIVE_RUNTIME_WINDOWS_COMMAND_NAME}`。",
            f"如果缺依赖，先执行 `python3 -m pip install -r {NATIVE_RUNTIME_REQUIREMENTS_NAME}`。",
        ],
        manifest_name="export_manifest.json",
        unlockable_manifest_name=unlockable_manifest_path.name,
        unlockable_report_name=unlockable_report_path.name,
        provenance_name=EXPORT_PROVENANCE_FILE_NAME,
        extra_reports=[
            runtime_preload_files["runtimePreloadReportName"],
            release_check_path.name,
            rc_report_path.name,
            release_control_report_path.name,
            vn_baseline_markdown_path.name,
            performance_budget_files["performanceBudgetMarkdownName"],
            asset3d_summary_path.name,
            EXPORT_ASSET_RIGHTS_REPORT_NAME,
            EXPORT_AUDIO_CUE_SHEET_REPORT_NAME,
            EXPORT_STAGE_DIRECTION_REPORT_NAME,
            EXPORT_PRESENTATION_TIMELINE_REPORT_NAME,
            EXPORT_VOICE_PRODUCTION_REPORT_NAME,
            NATIVE_RUNTIME_FILE_INTEGRITY_MARKDOWN_NAME,
            NATIVE_RUNTIME_ACCEPTANCE_REPORT_NAME,
        ],
        runtime_notes=[
            "原生 Runtime 仍是 Preview 路线，正式分发前建议在目标系统完整点测。",
            "内嵌视频播放可选 PyAV / FFmpeg；缺少依赖时会尝试降级兜底。",
        ],
        missing_assets=(export_payload.get("buildInfo") or {}).get("missingAssets") or [],
    )

    return {
        "gameDataName": game_data_path.name,
        "gameDataPath": str(game_data_path),
        "unlockableContentManifestName": unlockable_manifest_path.name,
        "unlockableContentManifestPath": str(unlockable_manifest_path),
        "unlockableContentReportName": unlockable_report_path.name,
        "unlockableContentReportPath": str(unlockable_report_path),
        "runtimePreloadManifestName": runtime_preload_files["runtimePreloadManifestName"],
        "runtimePreloadManifestPath": runtime_preload_files["runtimePreloadManifestPath"],
        "runtimePreloadReportName": runtime_preload_files["runtimePreloadReportName"],
        "runtimePreloadReportPath": runtime_preload_files["runtimePreloadReportPath"],
        "runtimePreloadSummary": (
            runtime_preload_manifest.get("summary", {}) if isinstance(runtime_preload_manifest, dict) else {}
        ),
        "playtestGuideName": playtest_guide_path.name,
        "playtestGuidePath": str(playtest_guide_path),
        "playerName": NATIVE_RUNTIME_PLAYER_NAME,
        "playerPath": str(build_dir / NATIVE_RUNTIME_PLAYER_NAME),
        "runtimePreloadModuleName": NATIVE_RUNTIME_PRELOAD_NAME,
        "runtimePreloadModulePath": str(build_dir / NATIVE_RUNTIME_PRELOAD_NAME),
        "runtimePerformanceModuleName": NATIVE_RUNTIME_PERFORMANCE_NAME,
        "runtimePerformanceModulePath": str(build_dir / NATIVE_RUNTIME_PERFORMANCE_NAME),
        "runtimeSettingsModuleName": NATIVE_RUNTIME_SETTINGS_NAME,
        "runtimeSettingsModulePath": str(build_dir / NATIVE_RUNTIME_SETTINGS_NAME),
        "runtimeTextEffectsModuleName": NATIVE_RUNTIME_TEXT_EFFECTS_NAME,
        "runtimeTextEffectsModulePath": str(build_dir / NATIVE_RUNTIME_TEXT_EFFECTS_NAME),
        "runtimeStorageModuleName": NATIVE_RUNTIME_STORAGE_NAME,
        "runtimeStorageModulePath": str(build_dir / NATIVE_RUNTIME_STORAGE_NAME),
        "runtimeVariablesModuleName": NATIVE_RUNTIME_VARIABLES_NAME,
        "runtimeVariablesModulePath": str(build_dir / NATIVE_RUNTIME_VARIABLES_NAME),
        "readmeName": NATIVE_RUNTIME_README_NAME,
        "readmePath": str(build_dir / NATIVE_RUNTIME_README_NAME),
        "requirementsName": NATIVE_RUNTIME_REQUIREMENTS_NAME,
        "requirementsPath": str(build_dir / NATIVE_RUNTIME_REQUIREMENTS_NAME),
        "buildRequirementsName": NATIVE_RUNTIME_BUILD_REQUIREMENTS_NAME,
        "buildRequirementsPath": str(build_dir / NATIVE_RUNTIME_BUILD_REQUIREMENTS_NAME),
        "videoRequirementsName": NATIVE_RUNTIME_VIDEO_REQUIREMENTS_NAME,
        "videoRequirementsPath": str(build_dir / NATIVE_RUNTIME_VIDEO_REQUIREMENTS_NAME),
        "brandLogoName": NATIVE_RUNTIME_BRAND_LOGO_NAME,
        "brandLogoPath": str(build_dir / NATIVE_RUNTIME_BRAND_LOGO_NAME),
        "appBuilderName": NATIVE_RUNTIME_APP_BUILDER_NAME,
        "appBuilderPath": str(build_dir / NATIVE_RUNTIME_APP_BUILDER_NAME),
        "releaseCheckName": release_check_path.name,
        "releaseCheckPath": str(release_check_path),
        "releaseCandidateReportName": rc_report_path.name,
        "releaseCandidateReportPath": str(rc_report_path),
        "releaseControlReportName": release_control_report_path.name,
        "releaseControlReportPath": str(release_control_report_path),
        "releaseControlJsonName": release_control_json_path.name,
        "releaseControlJsonPath": str(release_control_json_path),
        "releaseControlStatus": release_control_payload["qualityGate"]["status"],
        "releaseControlSummary": release_control_payload["qualityGate"]["summary"],
        "vnBaselineQualityReportName": vn_baseline_report_path.name,
        "vnBaselineQualityReportPath": str(vn_baseline_report_path),
        "vnBaselineQualityMarkdownName": vn_baseline_markdown_path.name,
        "vnBaselineQualityMarkdownPath": str(vn_baseline_markdown_path),
        "vnBaselineQualityStatus": str((release_control_payload.get("vnBaselineQuality") or {}).get("status") or "unavailable"),
        "performanceBudgetReportName": performance_budget_files["performanceBudgetReportName"],
        "performanceBudgetReportPath": performance_budget_files["performanceBudgetReportPath"],
        "performanceBudgetMarkdownName": performance_budget_files["performanceBudgetMarkdownName"],
        "performanceBudgetMarkdownPath": performance_budget_files["performanceBudgetMarkdownPath"],
        "performanceBudgetStatus": performance_budget_files["performanceBudgetStatus"],
        "performanceBudgetSummary": performance_budget_files["performanceBudgetSummary"],
        "asset3dReportName": asset3d_report_path.name,
        "asset3dReportPath": str(asset3d_report_path),
        "asset3dSummaryName": asset3d_summary_path.name,
        "asset3dSummaryPath": str(asset3d_summary_path),
        "asset3dDigestName": asset3d_digest_path.name,
        "asset3dDigestPath": str(asset3d_digest_path),
        "asset3dReportStatus": asset3d_report_payload.get("status") if isinstance(asset3d_report_payload, dict) else "unavailable",
        "asset3dReportSummary": asset3d_report_summary if isinstance(asset3d_report_summary, dict) else {},
        "asset3dReportDigest": asset3d_report_digest,
        "releaseCandidateReportStatus": rc_report_payload.get("status") if isinstance(rc_report_payload, dict) else "unavailable",
        "releaseCandidateReportSummary": rc_report_summary if isinstance(rc_report_summary, dict) else {},
        "releaseCandidateReadinessEstimate": rc_report_readiness if isinstance(rc_report_readiness, dict) else {},
        "macLauncherName": mac_launcher_path.name,
        "macLauncherPath": str(mac_launcher_path),
        "linuxLauncherName": linux_launcher_path.name,
        "linuxLauncherPath": str(linux_launcher_path),
        "windowsLauncherName": windows_launcher_path.name,
        "windowsLauncherPath": str(windows_launcher_path),
        "macReleaseCandidateCheckerName": mac_rc_path.name,
        "macReleaseCandidateCheckerPath": str(mac_rc_path),
        "linuxReleaseCandidateCheckerName": linux_rc_path.name,
        "linuxReleaseCandidateCheckerPath": str(linux_rc_path),
        "windowsReleaseCandidateCheckerName": windows_rc_path.name,
        "windowsReleaseCandidateCheckerPath": str(windows_rc_path),
        "macReleaseControlReporterName": mac_release_control_path.name,
        "macReleaseControlReporterPath": str(mac_release_control_path),
        "linuxReleaseControlReporterName": linux_release_control_path.name,
        "linuxReleaseControlReporterPath": str(linux_release_control_path),
        "windowsReleaseControlReporterName": windows_release_control_path.name,
        "windowsReleaseControlReporterPath": str(windows_release_control_path),
        "macAcceptanceReporterName": mac_acceptance_path.name,
        "macAcceptanceReporterPath": str(mac_acceptance_path),
        "linuxAcceptanceReporterName": linux_acceptance_path.name,
        "linuxAcceptanceReporterPath": str(linux_acceptance_path),
        "windowsAcceptanceReporterName": windows_acceptance_path.name,
        "windowsAcceptanceReporterPath": str(windows_acceptance_path),
        "macFileIntegrityCheckerName": mac_file_integrity_path.name,
        "macFileIntegrityCheckerPath": str(mac_file_integrity_path),
        "linuxFileIntegrityCheckerName": linux_file_integrity_path.name,
        "linuxFileIntegrityCheckerPath": str(linux_file_integrity_path),
        "windowsFileIntegrityCheckerName": windows_file_integrity_path.name,
        "windowsFileIntegrityCheckerPath": str(windows_file_integrity_path),
        "macAppBuilderName": mac_app_builder_path.name,
        "macAppBuilderPath": str(mac_app_builder_path),
        "linuxAppBuilderName": linux_app_builder_path.name,
        "linuxAppBuilderPath": str(linux_app_builder_path),
        "windowsAppBuilderName": windows_app_builder_path.name,
        "windowsAppBuilderPath": str(windows_app_builder_path),
    }


def write_native_runtime_file_integrity_reports(build_dir: Path) -> dict:
    report_path = build_dir / NATIVE_RUNTIME_FILE_INTEGRITY_REPORT_NAME
    markdown_path = build_dir / NATIVE_RUNTIME_FILE_INTEGRITY_MARKDOWN_NAME
    integrity_report = subprocess.run(
        [
            sys.executable,
            str(build_dir / NATIVE_RUNTIME_PLAYER_NAME),
            "--write-file-integrity-reports",
            str(build_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if integrity_report.returncode != 0:
        fallback_payload = {
            "formatVersion": 1,
            "algorithm": "sha256",
            "generatedAt": now_iso(),
            "status": "unavailable",
            "summary": {"fileCount": 0, "totalBytes": 0, "totalSizeLabel": "0 B"},
            "message": integrity_report.stderr.strip() or integrity_report.stdout.strip() or "文件完整性报告生成失败。",
            "files": [],
        }
        report_path.write_text(json.dumps(fallback_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        markdown_path.write_text(
            "\n".join(
                [
                    "# 原生 Runtime 文件完整性报告",
                    "",
                    "文件完整性报告暂不可用。",
                    "",
                    f"- 原因：{fallback_payload['message']}",
                    "- 可手动运行 `python3 runtime_player.py --write-file-integrity-reports .` 重新生成。",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return {
            "fileIntegrityStatus": "unavailable",
            "fileIntegritySummary": fallback_payload["summary"],
            "fileIntegrityReportName": report_path.name,
            "fileIntegrityReportPath": str(report_path),
            "fileIntegrityMarkdownName": markdown_path.name,
            "fileIntegrityMarkdownPath": str(markdown_path),
        }

    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        payload = {"summary": {"fileCount": 0, "totalBytes": 0, "totalSizeLabel": "0 B"}}
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return {
        "fileIntegrityStatus": "ready",
        "fileIntegritySummary": summary,
        "fileIntegrityReportName": report_path.name,
        "fileIntegrityReportPath": str(report_path),
        "fileIntegrityMarkdownName": markdown_path.name,
        "fileIntegrityMarkdownPath": str(markdown_path),
    }


def write_native_runtime_acceptance_reports(build_dir: Path) -> dict:
    report_path = build_dir / NATIVE_RUNTIME_ACCEPTANCE_REPORT_NAME
    json_path = build_dir / NATIVE_RUNTIME_ACCEPTANCE_JSON_NAME
    acceptance_report = subprocess.run(
        [
            sys.executable,
            str(build_dir / NATIVE_RUNTIME_PLAYER_NAME),
            "--write-acceptance-reports",
            str(build_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    payload: dict | None = None
    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        payload = None

    if payload is None:
        message = acceptance_report.stderr.strip() or acceptance_report.stdout.strip() or "发布验收清单生成失败。"
        payload = {
            "formatVersion": 1,
            "generatedAt": now_iso(),
            "acceptanceGate": {
                "status": "needs_manual_review",
                "label": "需要人工复核",
                "summary": message,
            },
            "automatedChecks": [],
            "platformMatrix": [],
            "manualCheckGroups": [],
            "recommendedCommands": ["python3 runtime_player.py --write-acceptance-reports ."],
            "includedReports": {},
        }
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report_path.write_text(
            "\n".join(
                [
                    "# 原生 Runtime 发布验收清单",
                    "",
                    "发布验收清单暂不可用。",
                    "",
                    f"- 原因：{message}",
                    "- 可手动运行 `python3 runtime_player.py --write-acceptance-reports .` 重新生成。",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    gate = payload.get("acceptanceGate") if isinstance(payload.get("acceptanceGate"), dict) else {}
    return {
        "acceptanceStatus": str(gate.get("status") or "needs_manual_review"),
        "acceptanceSummary": str(gate.get("summary") or ""),
        "acceptanceReportName": report_path.name,
        "acceptanceReportPath": str(report_path),
        "acceptanceJsonName": json_path.name,
        "acceptanceJsonPath": str(json_path),
    }


def format_export_file_size_label(size_bytes: int) -> str:
    size = float(max(0, size_bytes))
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size_bytes} B"


def calculate_file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_export_archive_checksum_files(archive_path: Path, target_label: str) -> dict:
    sha256 = calculate_file_sha256(archive_path)
    size_bytes = archive_path.stat().st_size
    checksum_path = archive_path.with_name(f"{archive_path.name}.sha256")
    checksum_json_path = archive_path.with_name(f"{archive_path.name}.checksum.json")
    checksum_path.write_text(f"{sha256}  {archive_path.name}\n", encoding="utf-8")
    payload = {
        "formatVersion": 1,
        "algorithm": "sha256",
        "generatedAt": now_iso(),
        "targetLabel": target_label,
        "archiveName": archive_path.name,
        "archivePath": str(archive_path),
        "archiveSizeBytes": size_bytes,
        "archiveSizeLabel": format_export_file_size_label(size_bytes),
        "sha256": sha256,
        "verifyCommands": {
            "macosLinux": f"shasum -a 256 {archive_path.name}",
            "windowsPowerShell": f"Get-FileHash .\\{archive_path.name} -Algorithm SHA256",
            "windowsCmd": f"CertUtil -hashfile {archive_path.name} SHA256",
        },
    }
    checksum_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "archiveSha256": sha256,
        "archiveSizeBytes": size_bytes,
        "archiveSizeLabel": payload["archiveSizeLabel"],
        "archiveChecksumName": checksum_path.name,
        "archiveChecksumPath": str(checksum_path),
        "archiveChecksumJsonName": checksum_json_path.name,
        "archiveChecksumJsonPath": str(checksum_json_path),
    }


def write_export_archive_verifier_scripts(archive_path: Path, sha256: str) -> dict:
    mac_path = archive_path.with_name(f"{archive_path.name}.verify.command")
    linux_path = archive_path.with_name(f"{archive_path.name}.verify.sh")
    windows_path = archive_path.with_name(f"{archive_path.name}.verify.bat")
    archive_name = archive_path.name
    mac_path.write_text(
        "\n".join(
            [
                "#!/bin/bash",
                "set -e",
                'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"',
                'cd "$SCRIPT_DIR"',
                f'ARCHIVE="{archive_name}"',
                f'EXPECTED="{sha256}"',
                'if [ ! -f "$ARCHIVE" ]; then',
                '  echo "找不到压缩包：$ARCHIVE"',
                '  read -r -p "按回车关闭..." _',
                "  exit 1",
                "fi",
                "if command -v python3 >/dev/null 2>&1; then",
                '  ACTUAL="$(python3 - "$ARCHIVE" <<\'PY\'',
                "import hashlib",
                "import sys",
                "path = sys.argv[1]",
                "digest = hashlib.sha256()",
                "with open(path, 'rb') as file_handle:",
                "    for chunk in iter(lambda: file_handle.read(1024 * 1024), b''):",
                "        digest.update(chunk)",
                "print(digest.hexdigest())",
                "PY",
                ')"',
                "else",
                '  ACTUAL="$(shasum -a 256 "$ARCHIVE" | awk \'{print $1}\')"',
                "fi",
                'if [ "$ACTUAL" != "$EXPECTED" ]; then',
                '  echo "压缩包 SHA-256 校验失败。"',
                '  echo "期望：$EXPECTED"',
                '  echo "实际：$ACTUAL"',
                '  echo "请重新下载或重新导出。"',
                '  read -r -p "按回车关闭..." _',
                "  exit 1",
                "fi",
                'echo "压缩包 SHA-256 校验通过：$ARCHIVE"',
                'read -r -p "按回车关闭..." _',
                "",
            ]
        ),
        encoding="utf-8",
    )
    linux_path.write_text(
        "\n".join(
            [
                "#!/bin/bash",
                "set -e",
                'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"',
                'cd "$SCRIPT_DIR"',
                f'ARCHIVE="{archive_name}"',
                f'EXPECTED="{sha256}"',
                'if [ ! -f "$ARCHIVE" ]; then',
                '  echo "找不到压缩包：$ARCHIVE"',
                "  exit 1",
                "fi",
                "if command -v sha256sum >/dev/null 2>&1; then",
                '  ACTUAL="$(sha256sum "$ARCHIVE" | awk \'{print $1}\')"',
                "else",
                '  ACTUAL="$(python3 - "$ARCHIVE" <<\'PY\'',
                "import hashlib",
                "import sys",
                "path = sys.argv[1]",
                "digest = hashlib.sha256()",
                "with open(path, 'rb') as file_handle:",
                "    for chunk in iter(lambda: file_handle.read(1024 * 1024), b''):",
                "        digest.update(chunk)",
                "print(digest.hexdigest())",
                "PY",
                ')"',
                "fi",
                'if [ "$ACTUAL" != "$EXPECTED" ]; then',
                '  echo "压缩包 SHA-256 校验失败。"',
                '  echo "期望：$EXPECTED"',
                '  echo "实际：$ACTUAL"',
                '  echo "请重新下载或重新导出。"',
                "  exit 1",
                "fi",
                'echo "压缩包 SHA-256 校验通过：$ARCHIVE"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    windows_path.write_text(
        "\r\n".join(
            [
                "@echo off",
                "setlocal EnableExtensions",
                f'set "ARCHIVE={archive_name}"',
                f'set "EXPECTED={sha256}"',
                'if not exist "%ARCHIVE%" (',
                "  echo 找不到压缩包：%ARCHIVE%",
                "  pause",
                "  exit /b 1",
                ")",
                "set \"ACTUAL=\"",
                "for /f \"usebackq tokens=*\" %%H in (`powershell -NoProfile -ExecutionPolicy Bypass -Command \"(Get-FileHash -LiteralPath '%ARCHIVE%' -Algorithm SHA256).Hash.ToLower()\"`) do set \"ACTUAL=%%H\"",
                'if "%ACTUAL%"=="" (',
                "  for /f \"tokens=1\" %%H in ('certutil -hashfile \"%ARCHIVE%\" SHA256 ^| findstr /R /V \"hash CertUtil\"') do if not defined ACTUAL set \"ACTUAL=%%H\"",
                ")",
                'if /I not "%ACTUAL%"=="%EXPECTED%" (',
                "  echo 压缩包 SHA-256 校验失败。",
                "  echo 期望：%EXPECTED%",
                "  echo 实际：%ACTUAL%",
                "  echo 请重新下载或重新导出。",
                "  pause",
                "  exit /b 1",
                ")",
                "echo 压缩包 SHA-256 校验通过：%ARCHIVE%",
                "pause",
                "",
            ]
        ),
        encoding="utf-8",
    )
    mac_path.chmod(0o755)
    linux_path.chmod(0o755)
    return {
        "archiveVerifierMacName": mac_path.name,
        "archiveVerifierMacPath": str(mac_path),
        "archiveVerifierLinuxName": linux_path.name,
        "archiveVerifierLinuxPath": str(linux_path),
        "archiveVerifierWindowsName": windows_path.name,
        "archiveVerifierWindowsPath": str(windows_path),
    }


def write_export_release_artifact_index(
    archive_path: Path,
    target_label: str,
    archive_checksum: dict,
    archive_verifiers: dict,
    release_notes: dict,
    internal_reports: list[dict],
) -> dict:
    artifact_json_path = archive_path.with_name(f"{archive_path.name}.release-artifacts.json")
    artifact_markdown_path = archive_path.with_name(f"{archive_path.name}.release-artifacts.md")
    upload_artifacts = [
        {
            "name": archive_path.name,
            "path": str(archive_path),
            "type": "archive",
            "description": "原生 Runtime 可分发压缩包。",
            "required": True,
            "sha256": archive_checksum.get("archiveSha256"),
            "sizeLabel": archive_checksum.get("archiveSizeLabel"),
        },
        {
            "name": archive_checksum.get("archiveChecksumName"),
            "path": archive_checksum.get("archiveChecksumPath"),
            "type": "checksum",
            "description": "压缩包 SHA-256 纯文本校验文件。",
            "required": True,
        },
        {
            "name": archive_checksum.get("archiveChecksumJsonName"),
            "path": archive_checksum.get("archiveChecksumJsonPath"),
            "type": "checksum_json",
            "description": "压缩包校验信息、大小和跨平台验证命令。",
            "required": True,
        },
        {
            "name": archive_verifiers.get("archiveVerifierMacName"),
            "path": archive_verifiers.get("archiveVerifierMacPath"),
            "type": "archive_verifier",
            "description": "macOS 一键校验下载压缩包 SHA-256。",
            "required": False,
        },
        {
            "name": archive_verifiers.get("archiveVerifierLinuxName"),
            "path": archive_verifiers.get("archiveVerifierLinuxPath"),
            "type": "archive_verifier",
            "description": "Linux 一键校验下载压缩包 SHA-256。",
            "required": False,
        },
        {
            "name": archive_verifiers.get("archiveVerifierWindowsName"),
            "path": archive_verifiers.get("archiveVerifierWindowsPath"),
            "type": "archive_verifier",
            "description": "Windows 一键校验下载压缩包 SHA-256。",
            "required": False,
        },
        {
            "name": release_notes.get("releaseNotesName"),
            "path": release_notes.get("releaseNotesPath"),
            "type": "release_notes_draft",
            "description": "可直接复制到 GitHub Release 正文的发布说明草稿。",
            "required": False,
        },
        {
            "name": artifact_markdown_path.name,
            "path": str(artifact_markdown_path),
            "type": "release_notes_helper",
            "description": "发布附件索引，可直接贴到 Release notes 或作为附件上传。",
            "required": False,
        },
        {
            "name": artifact_json_path.name,
            "path": str(artifact_json_path),
            "type": "artifact_manifest",
            "description": "机器可读发布附件索引。",
            "required": False,
        },
    ]
    payload = {
        "formatVersion": 1,
        "generatedAt": now_iso(),
        "targetLabel": target_label,
        "archive": {
            "name": archive_path.name,
            "path": str(archive_path),
            "sha256": archive_checksum.get("archiveSha256"),
            "sizeBytes": archive_checksum.get("archiveSizeBytes"),
            "sizeLabel": archive_checksum.get("archiveSizeLabel"),
            "checksum": archive_checksum.get("archiveChecksumName"),
            "checksumJson": archive_checksum.get("archiveChecksumJsonName"),
            "releaseNotesDraft": release_notes.get("releaseNotesName"),
            "verifiers": {
                "macos": archive_verifiers.get("archiveVerifierMacName"),
                "linux": archive_verifiers.get("archiveVerifierLinuxName"),
                "windows": archive_verifiers.get("archiveVerifierWindowsName"),
            },
        },
        "uploadArtifacts": upload_artifacts,
        "insideArchiveReports": internal_reports,
        "verifySteps": [
            "下载 zip，并把对应系统的一键校验脚本放在同一目录。",
            "运行 .verify.command / .verify.sh / .verify.bat 校验 zip 压缩包 SHA-256。",
            "如果不使用脚本，也可以用 .sha256 或 .checksum.json 里的命令手动校验。",
            "解压后运行 runtime_player.py --verify-file-integrity . 校验包内核心文件。",
            "再运行发布总控脚本或打开 native-runtime-release-control-report.md 复核发布状态。",
        ],
    }
    artifact_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# 原生 Runtime 发布附件索引",
        "",
        f"- 类型：{target_label}",
        f"- 生成时间：{payload['generatedAt']}",
        f"- 压缩包：`{archive_path.name}`",
        f"- 大小：{archive_checksum.get('archiveSizeLabel') or '未知'}",
        f"- SHA-256：`{archive_checksum.get('archiveSha256') or '未生成'}`",
        "",
        "## 建议上传到 GitHub Release 的附件",
        "",
        "| 文件 | 必需 | 说明 |",
        "| --- | --- | --- |",
    ]
    for artifact in upload_artifacts:
        lines.append(
            f"| `{artifact.get('name') or ''}` | {'是' if artifact.get('required') else '否'} | {artifact.get('description') or ''} |"
        )
    lines.extend(["", "## 包内报告", "", "| 文件 | 说明 |", "| --- | --- |"])
    for report in internal_reports:
        lines.append(f"| `{report.get('name') or ''}` | {report.get('description') or ''} |")
    lines.extend(["", "## 下载者验证步骤", ""])
    for index, step in enumerate(payload["verifySteps"], start=1):
        lines.append(f"{index}. {step}")
    lines.extend(
        [
            "",
            "## Release Notes 摘要",
            "",
            "```md",
            f"- 下载 `{archive_path.name}` 后，先运行对应系统的 `.verify` 脚本或用 `{archive_checksum.get('archiveChecksumName')}` 校验压缩包 SHA-256。",
            "- 解压后运行 `python3 runtime_player.py --verify-file-integrity .` 校验包内核心文件。",
            "- 如需发布前复核，打开 `native-runtime-release-control-report.md`。",
            "```",
            "",
        ]
    )
    artifact_markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "releaseArtifactIndexName": artifact_markdown_path.name,
        "releaseArtifactIndexPath": str(artifact_markdown_path),
        "releaseArtifactIndexJsonName": artifact_json_path.name,
        "releaseArtifactIndexJsonPath": str(artifact_json_path),
        "releaseArtifactUploadCount": len(upload_artifacts),
    }


def write_export_release_notes_draft(
    archive_path: Path,
    target_label: str,
    archive_checksum: dict,
    archive_verifiers: dict,
    internal_reports: list[dict],
) -> dict:
    release_notes_path = archive_path.with_name(f"{archive_path.name}.release-notes.md")
    report_names = [str(report.get("name") or "") for report in internal_reports if report.get("name")]
    lines = [
        "# Canvasia Engine 原生 Runtime Preview",
        "",
        f"- 类型：{target_label}",
        "- 这是原生 Runtime Preview 包说明。发布时请按实际附件保留适用内容。",
        "",
        "## 下载",
        "",
        f"- 主包：`{archive_path.name}`",
        f"- 大小：{archive_checksum.get('archiveSizeLabel') or '未知'}",
        f"- SHA-256：`{archive_checksum.get('archiveSha256') or '未生成'}`",
        "",
        "建议同时上传到 GitHub Release 的校验附件：",
        "",
        f"- `{archive_checksum.get('archiveChecksumName')}`",
        f"- `{archive_checksum.get('archiveChecksumJsonName')}`",
        f"- `{archive_verifiers.get('archiveVerifierMacName')}`",
        f"- `{archive_verifiers.get('archiveVerifierLinuxName')}`",
        f"- `{archive_verifiers.get('archiveVerifierWindowsName')}`",
        "",
        "## 首次启动",
        "",
        "- macOS：解压后优先打开 `.app`。未签名 Preview 如被拦截，可右键选择“打开”，并确认来源是官方 Release 页面。",
        "- Windows：解压后运行 `.exe`。如遇 SmartScreen，先完成 SHA-256 校验再继续。",
        "- Linux：解压后运行可执行文件；如缺执行权限，先给启动文件加执行权限。",
        "- 如果这是源码式 Runtime 包而不是已打包 App，请使用随包的 `启动原生Runtime预览.command`、`run_native_runtime_preview.sh` 或 `run_native_runtime_preview.bat`。",
        "",
        "## 下载后验证",
        "",
        "1. 将 zip 和对应系统的 `.verify` 脚本放在同一目录。",
        "2. macOS 双击 `.verify.command`，Linux 运行 `.verify.sh`，Windows 双击 `.verify.bat`。",
        "3. 解压后运行 `python3 runtime_player.py --verify-file-integrity .` 校验包内核心文件。",
        "4. 打开 `native-runtime-release-control-report.md` 查看发布总控结论。",
        "5. 打开 `native-runtime-release-acceptance.md` 按目标系统完成最终人工验收。",
        "",
        "## 包内重点报告",
        "",
    ]
    if report_names:
        for report_name in report_names:
            lines.append(f"- `{report_name}`")
    else:
        lines.append("- 这次导出没有记录额外包内报告。")
    lines.extend(
        [
            "",
            "## 状态说明",
            "",
            "- 原生 Runtime 仍处于 Preview 路线，建议在目标系统完成一次人工逐按钮长流程点测。",
            "- 若 zip 校验失败，请重新下载或重新导出；若包内完整性失败，请不要继续分发该包。",
            "",
        ]
    )
    release_notes_path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "releaseNotesName": release_notes_path.name,
        "releaseNotesPath": str(release_notes_path),
    }


def export_native_runtime_build() -> dict:
    build_dir = create_export_build_dir("native_runtime_build")
    bundle = load_project_bundle()
    export_assets_doc, copied_assets, missing_assets = copy_assets_for_export(bundle["assets"], build_dir)
    export_payload = build_export_payload(bundle, export_assets_doc, copied_assets, missing_assets)
    release_version = get_export_release_version(bundle["project"])
    export_payload["buildInfo"]["releaseVersion"] = release_version
    export_payload["buildInfo"]["exportTargetLabel"] = "原生 Runtime 包（可打包 App）"
    export_payload["buildInfo"]["runtimeMode"] = "pygame_native"
    export_payload["buildInfo"]["runtimeStage"] = "preview"
    runtime_files = write_native_runtime_files(build_dir, export_payload)
    manifest = build_export_manifest(
        bundle,
        target=EXPORT_TARGET_NATIVE_RUNTIME,
        target_label="原生 Runtime 包（可打包 App）",
        build_id=build_dir.name,
        copied_assets=copied_assets,
        missing_assets=missing_assets,
        extra_files={
            "gameData": runtime_files["gameDataName"],
            "playtestGuide": runtime_files["playtestGuideName"],
            "releaseEvidencePack": EXPORT_RELEASE_EVIDENCE_PACK_NAME,
            "assetRights": EXPORT_ASSET_RIGHTS_JSON_NAME,
            "assetRightsReport": EXPORT_ASSET_RIGHTS_REPORT_NAME,
            "assetRightsCsv": EXPORT_ASSET_RIGHTS_CSV_NAME,
            "audioCueSheet": EXPORT_AUDIO_CUE_SHEET_JSON_NAME,
            "audioCueSheetReport": EXPORT_AUDIO_CUE_SHEET_REPORT_NAME,
            "audioCueSheetCsv": EXPORT_AUDIO_CUE_SHEET_CSV_NAME,
            "stageDirection": EXPORT_STAGE_DIRECTION_JSON_NAME,
            "stageDirectionReport": EXPORT_STAGE_DIRECTION_REPORT_NAME,
            "stageDirectionCsv": EXPORT_STAGE_DIRECTION_CSV_NAME,
            "presentationTimeline": EXPORT_PRESENTATION_TIMELINE_JSON_NAME,
            "presentationTimelineReport": EXPORT_PRESENTATION_TIMELINE_REPORT_NAME,
            "presentationTimelineCsv": EXPORT_PRESENTATION_TIMELINE_CSV_NAME,
            "routePlaytestWorkbook": EXPORT_ROUTE_PLAYTEST_WORKBOOK_JSON_NAME,
            "routePlaytestWorkbookReport": EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME,
            "routePlaytestWorkbookCsv": EXPORT_ROUTE_PLAYTEST_WORKBOOK_CSV_NAME,
            "choiceConsequence": EXPORT_CHOICE_CONSEQUENCE_JSON_NAME,
            "choiceConsequenceReport": EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME,
            "choiceConsequenceCsv": EXPORT_CHOICE_CONSEQUENCE_CSV_NAME,
            "variableInfluence": EXPORT_VARIABLE_INFLUENCE_JSON_NAME,
            "variableInfluenceReport": EXPORT_VARIABLE_INFLUENCE_REPORT_NAME,
            "variableInfluenceCsv": EXPORT_VARIABLE_INFLUENCE_CSV_NAME,
            "voiceProduction": EXPORT_VOICE_PRODUCTION_JSON_NAME,
            "voiceProductionReport": EXPORT_VOICE_PRODUCTION_REPORT_NAME,
            "voiceProductionCsv": EXPORT_VOICE_PRODUCTION_CSV_NAME,
            "storyRouteMap": EXPORT_STORY_ROUTE_MAP_JSON_NAME,
            "storyRouteMapReport": EXPORT_STORY_ROUTE_MAP_REPORT_NAME,
            "localizationAudit": EXPORT_LOCALIZATION_AUDIT_JSON_NAME,
            "localizationAuditReport": EXPORT_LOCALIZATION_AUDIT_REPORT_NAME,
            "releaseReadinessSummary": EXPORT_RELEASE_READINESS_JSON_NAME,
            "releaseReadinessReport": EXPORT_RELEASE_READINESS_REPORT_NAME,
            "unlockableContentManifest": runtime_files["unlockableContentManifestName"],
            "unlockableContentReport": runtime_files["unlockableContentReportName"],
            "runtimePreloadManifest": runtime_files["runtimePreloadManifestName"],
            "runtimePreloadReport": runtime_files["runtimePreloadReportName"],
            "playerScript": runtime_files["playerName"],
            "runtimePreloadModule": runtime_files["runtimePreloadModuleName"],
            "runtimePerformanceModule": runtime_files["runtimePerformanceModuleName"],
            "runtimeSettingsModule": runtime_files["runtimeSettingsModuleName"],
            "runtimeTextEffectsModule": runtime_files["runtimeTextEffectsModuleName"],
            "runtimeStorageModule": runtime_files["runtimeStorageModuleName"],
            "runtimeVariablesModule": runtime_files["runtimeVariablesModuleName"],
            "readme": runtime_files["readmeName"],
            "requirements": runtime_files["requirementsName"],
            "buildRequirements": runtime_files["buildRequirementsName"],
            "videoRequirements": runtime_files["videoRequirementsName"],
            "appBuilder": runtime_files["appBuilderName"],
            "releaseCheck": runtime_files["releaseCheckName"],
            "releaseCandidateReport": runtime_files["releaseCandidateReportName"],
            "releaseControlReport": runtime_files["releaseControlReportName"],
            "releaseControlJson": runtime_files["releaseControlJsonName"],
            "vnBaselineQualityReport": runtime_files["vnBaselineQualityReportName"],
            "vnBaselineQualityMarkdown": runtime_files["vnBaselineQualityMarkdownName"],
            "performanceBudgetReport": runtime_files["performanceBudgetReportName"],
            "performanceBudgetMarkdown": runtime_files["performanceBudgetMarkdownName"],
            "acceptanceReport": NATIVE_RUNTIME_ACCEPTANCE_REPORT_NAME,
            "acceptanceJson": NATIVE_RUNTIME_ACCEPTANCE_JSON_NAME,
            "fileIntegrityReport": NATIVE_RUNTIME_FILE_INTEGRITY_REPORT_NAME,
            "fileIntegrityMarkdown": NATIVE_RUNTIME_FILE_INTEGRITY_MARKDOWN_NAME,
            "asset3dReport": runtime_files["asset3dReportName"],
            "asset3dSummary": runtime_files["asset3dSummaryName"],
            "asset3dDigest": runtime_files["asset3dDigestName"],
            "macLauncher": runtime_files["macLauncherName"],
            "linuxLauncher": runtime_files["linuxLauncherName"],
            "windowsLauncher": runtime_files["windowsLauncherName"],
            "macReleaseCandidateChecker": runtime_files["macReleaseCandidateCheckerName"],
            "linuxReleaseCandidateChecker": runtime_files["linuxReleaseCandidateCheckerName"],
            "windowsReleaseCandidateChecker": runtime_files["windowsReleaseCandidateCheckerName"],
            "macReleaseControlReporter": runtime_files["macReleaseControlReporterName"],
            "linuxReleaseControlReporter": runtime_files["linuxReleaseControlReporterName"],
            "windowsReleaseControlReporter": runtime_files["windowsReleaseControlReporterName"],
            "macAcceptanceReporter": runtime_files["macAcceptanceReporterName"],
            "linuxAcceptanceReporter": runtime_files["linuxAcceptanceReporterName"],
            "windowsAcceptanceReporter": runtime_files["windowsAcceptanceReporterName"],
            "macFileIntegrityChecker": runtime_files["macFileIntegrityCheckerName"],
            "linuxFileIntegrityChecker": runtime_files["linuxFileIntegrityCheckerName"],
            "windowsFileIntegrityChecker": runtime_files["windowsFileIntegrityCheckerName"],
            "macAppBuilder": runtime_files["macAppBuilderName"],
            "linuxAppBuilder": runtime_files["linuxAppBuilderName"],
            "windowsAppBuilder": runtime_files["windowsAppBuilderName"],
        },
        runtime_info={
            "mode": "pygame_native",
            "modeLabel": "Python + pygame-ce 原生 Runtime",
            "warning": "导出包已包含 PyInstaller 应用打包脚手架；正式分发前仍建议在目标系统做完整点测。",
            "requiresPython3": True,
            "requiresPygameCE": True,
            "optionalVideoRequirements": runtime_files["videoRequirementsName"],
            "canBuildStandaloneApp": True,
            "appBuilder": runtime_files["appBuilderName"],
            "playtestGuide": runtime_files["playtestGuideName"],
            "releaseEvidencePack": EXPORT_RELEASE_EVIDENCE_PACK_NAME,
            "assetRights": EXPORT_ASSET_RIGHTS_JSON_NAME,
            "assetRightsReport": EXPORT_ASSET_RIGHTS_REPORT_NAME,
            "assetRightsCsv": EXPORT_ASSET_RIGHTS_CSV_NAME,
            "audioCueSheet": EXPORT_AUDIO_CUE_SHEET_JSON_NAME,
            "audioCueSheetReport": EXPORT_AUDIO_CUE_SHEET_REPORT_NAME,
            "audioCueSheetCsv": EXPORT_AUDIO_CUE_SHEET_CSV_NAME,
            "stageDirection": EXPORT_STAGE_DIRECTION_JSON_NAME,
            "stageDirectionReport": EXPORT_STAGE_DIRECTION_REPORT_NAME,
            "stageDirectionCsv": EXPORT_STAGE_DIRECTION_CSV_NAME,
            "presentationTimeline": EXPORT_PRESENTATION_TIMELINE_JSON_NAME,
            "presentationTimelineReport": EXPORT_PRESENTATION_TIMELINE_REPORT_NAME,
            "presentationTimelineCsv": EXPORT_PRESENTATION_TIMELINE_CSV_NAME,
            "routePlaytestWorkbook": EXPORT_ROUTE_PLAYTEST_WORKBOOK_JSON_NAME,
            "routePlaytestWorkbookReport": EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME,
            "routePlaytestWorkbookCsv": EXPORT_ROUTE_PLAYTEST_WORKBOOK_CSV_NAME,
            "choiceConsequence": EXPORT_CHOICE_CONSEQUENCE_JSON_NAME,
            "choiceConsequenceReport": EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME,
            "choiceConsequenceCsv": EXPORT_CHOICE_CONSEQUENCE_CSV_NAME,
            "variableInfluence": EXPORT_VARIABLE_INFLUENCE_JSON_NAME,
            "variableInfluenceReport": EXPORT_VARIABLE_INFLUENCE_REPORT_NAME,
            "variableInfluenceCsv": EXPORT_VARIABLE_INFLUENCE_CSV_NAME,
            "voiceProduction": EXPORT_VOICE_PRODUCTION_JSON_NAME,
            "voiceProductionReport": EXPORT_VOICE_PRODUCTION_REPORT_NAME,
            "voiceProductionCsv": EXPORT_VOICE_PRODUCTION_CSV_NAME,
            "storyRouteMap": EXPORT_STORY_ROUTE_MAP_JSON_NAME,
            "storyRouteMapReport": EXPORT_STORY_ROUTE_MAP_REPORT_NAME,
            "localizationAudit": EXPORT_LOCALIZATION_AUDIT_JSON_NAME,
            "localizationAuditReport": EXPORT_LOCALIZATION_AUDIT_REPORT_NAME,
            "releaseReadinessSummary": EXPORT_RELEASE_READINESS_JSON_NAME,
            "releaseReadinessReport": EXPORT_RELEASE_READINESS_REPORT_NAME,
            "unlockableContentManifest": runtime_files["unlockableContentManifestName"],
            "unlockableContentReport": runtime_files["unlockableContentReportName"],
            "runtimePreloadManifest": runtime_files["runtimePreloadManifestName"],
            "runtimePreloadReport": runtime_files["runtimePreloadReportName"],
            "runtimePreloadSummary": runtime_files["runtimePreloadSummary"],
            "runtimePreloadModule": runtime_files["runtimePreloadModuleName"],
            "runtimePerformanceModule": runtime_files["runtimePerformanceModuleName"],
            "runtimeSettingsModule": runtime_files["runtimeSettingsModuleName"],
            "runtimeTextEffectsModule": runtime_files["runtimeTextEffectsModuleName"],
            "runtimeStorageModule": runtime_files["runtimeStorageModuleName"],
            "runtimeVariablesModule": runtime_files["runtimeVariablesModuleName"],
            "releaseCheck": runtime_files["releaseCheckName"],
            "releaseCandidateReport": runtime_files["releaseCandidateReportName"],
            "releaseControlReport": runtime_files["releaseControlReportName"],
            "releaseControlJson": runtime_files["releaseControlJsonName"],
            "releaseControlStatus": runtime_files["releaseControlStatus"],
            "vnBaselineQualityReport": runtime_files["vnBaselineQualityReportName"],
            "vnBaselineQualityMarkdown": runtime_files["vnBaselineQualityMarkdownName"],
            "vnBaselineQualityStatus": runtime_files["vnBaselineQualityStatus"],
            "performanceBudgetReport": runtime_files["performanceBudgetReportName"],
            "performanceBudgetMarkdown": runtime_files["performanceBudgetMarkdownName"],
            "performanceBudgetStatus": runtime_files["performanceBudgetStatus"],
            "performanceBudgetSummary": runtime_files["performanceBudgetSummary"],
            "releaseControlReporter": {
                "macos": runtime_files["macReleaseControlReporterName"],
                "linux": runtime_files["linuxReleaseControlReporterName"],
                "windows": runtime_files["windowsReleaseControlReporterName"],
            },
            "acceptanceReport": NATIVE_RUNTIME_ACCEPTANCE_REPORT_NAME,
            "acceptanceJson": NATIVE_RUNTIME_ACCEPTANCE_JSON_NAME,
            "acceptanceReporter": {
                "macos": runtime_files["macAcceptanceReporterName"],
                "linux": runtime_files["linuxAcceptanceReporterName"],
                "windows": runtime_files["windowsAcceptanceReporterName"],
            },
            "fileIntegrityReport": NATIVE_RUNTIME_FILE_INTEGRITY_REPORT_NAME,
            "fileIntegrityMarkdown": NATIVE_RUNTIME_FILE_INTEGRITY_MARKDOWN_NAME,
            "fileIntegrityChecker": {
                "macos": runtime_files["macFileIntegrityCheckerName"],
                "linux": runtime_files["linuxFileIntegrityCheckerName"],
                "windows": runtime_files["windowsFileIntegrityCheckerName"],
            },
            "asset3dReport": runtime_files["asset3dReportName"],
            "asset3dSummary": runtime_files["asset3dSummaryName"],
            "asset3dDigest": runtime_files["asset3dDigestName"],
            "asset3dReportStatus": runtime_files["asset3dReportStatus"],
            "releaseCandidateReportStatus": runtime_files["releaseCandidateReportStatus"],
        },
    )
    manifest_path = write_export_manifest(build_dir, manifest)
    asset_rights_files = write_export_asset_rights_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    audio_cue_sheet_files = write_export_audio_cue_sheet_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    stage_direction_files = write_export_stage_direction_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    presentation_timeline_files = write_export_presentation_timeline_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    voice_production_files = write_export_voice_production_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    quality_reports = write_export_quality_report_bundle(
        build_dir,
        bundle=bundle,
        project=bundle["project"],
        manifest=manifest,
        missing_assets=missing_assets,
        unlockable_manifest=(export_payload.get("buildInfo") or {}).get("unlockableContentManifest"),
        base_report_files=[
            manifest_path.name,
            runtime_files["playtestGuideName"],
        ],
        extra_report_files=[
            runtime_files["unlockableContentReportName"],
            runtime_files["unlockableContentManifestName"],
            runtime_files["runtimePreloadReportName"],
            runtime_files["runtimePreloadManifestName"],
            runtime_files["releaseCandidateReportName"],
            runtime_files["releaseControlReportName"],
            runtime_files["vnBaselineQualityMarkdownName"],
            runtime_files["performanceBudgetMarkdownName"],
            runtime_files["asset3dSummaryName"],
            asset_rights_files["assetRightsReportName"],
            asset_rights_files["assetRightsName"],
            asset_rights_files["assetRightsCsvName"],
            audio_cue_sheet_files["audioCueSheetReportName"],
            audio_cue_sheet_files["audioCueSheetName"],
            audio_cue_sheet_files["audioCueSheetCsvName"],
            stage_direction_files["stageDirectionReportName"],
            stage_direction_files["stageDirectionName"],
            stage_direction_files["stageDirectionCsvName"],
            presentation_timeline_files["presentationTimelineReportName"],
            presentation_timeline_files["presentationTimelineName"],
            presentation_timeline_files["presentationTimelineCsvName"],
            EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME,
            EXPORT_ROUTE_PLAYTEST_WORKBOOK_JSON_NAME,
            EXPORT_ROUTE_PLAYTEST_WORKBOOK_CSV_NAME,
            EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME,
            EXPORT_CHOICE_CONSEQUENCE_JSON_NAME,
            EXPORT_CHOICE_CONSEQUENCE_CSV_NAME,
            EXPORT_VARIABLE_INFLUENCE_REPORT_NAME,
            EXPORT_VARIABLE_INFLUENCE_JSON_NAME,
            EXPORT_VARIABLE_INFLUENCE_CSV_NAME,
            voice_production_files["voiceProductionReportName"],
            voice_production_files["voiceProductionName"],
            voice_production_files["voiceProductionCsvName"],
        ],
        platform_notes=[
            "原生 Runtime 是后续 App 化路线的重点包；正式分发前建议至少在目标系统完整跑通一次。",
            "如果要提供给普通玩家，优先使用随包 App 打包脚本生成平台应用。",
        ],
    )
    story_route_map = quality_reports
    localization_audit = quality_reports
    release_readiness = quality_reports
    native_launch_steps = [
        f"macOS：双击 `{NATIVE_RUNTIME_MAC_COMMAND_NAME}`。",
        f"Linux：运行 `./{NATIVE_RUNTIME_LINUX_COMMAND_NAME}`。",
        f"Windows：双击 `{NATIVE_RUNTIME_WINDOWS_COMMAND_NAME}`。",
        f"如果缺依赖，先执行 `python3 -m pip install -r {NATIVE_RUNTIME_REQUIREMENTS_NAME}`。",
    ]
    native_runtime_notes = [
        "原生 Runtime 仍是 Preview 路线，正式分发前建议在目标系统完整点测。",
        "内嵌视频播放可选 PyAV / FFmpeg；缺少依赖时会尝试降级兜底。",
    ]
    evidence_pack_path = write_export_release_evidence_pack_file(
        build_dir,
        project=bundle["project"],
        target_label="原生 Runtime 包（可打包 App）",
        release_version=release_version,
        manifest_name=manifest_path.name,
        playtest_guide_name=runtime_files["playtestGuideName"],
        provenance_name=EXPORT_PROVENANCE_FILE_NAME,
        story_route_map_report_name=story_route_map["storyRouteMapReportName"],
        localization_audit_report_name=localization_audit["localizationAuditReportName"],
        release_readiness_report_name=release_readiness["releaseReadinessReportName"],
        unlockable_report_name=runtime_files["unlockableContentReportName"],
        unlockable_manifest_name=runtime_files["unlockableContentManifestName"],
        launch_steps=native_launch_steps,
        runtime_notes=native_runtime_notes,
        extra_reports=[
            runtime_files["runtimePreloadReportName"],
            runtime_files["releaseCandidateReportName"],
            runtime_files["releaseControlReportName"],
            runtime_files["vnBaselineQualityMarkdownName"],
            runtime_files["performanceBudgetMarkdownName"],
            runtime_files["asset3dSummaryName"],
            asset_rights_files["assetRightsReportName"],
            audio_cue_sheet_files["audioCueSheetReportName"],
            stage_direction_files["stageDirectionReportName"],
            presentation_timeline_files["presentationTimelineReportName"],
            EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME,
            EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME,
            EXPORT_VARIABLE_INFLUENCE_REPORT_NAME,
            voice_production_files["voiceProductionReportName"],
            NATIVE_RUNTIME_FILE_INTEGRITY_MARKDOWN_NAME,
            NATIVE_RUNTIME_ACCEPTANCE_REPORT_NAME,
        ],
        missing_assets=missing_assets,
    )
    provenance_verifiers = write_export_provenance_verifier_files(build_dir)
    provenance_file = write_export_provenance_file(build_dir, bundle, manifest)
    integrity_files = write_native_runtime_file_integrity_reports(build_dir)
    acceptance_files = write_native_runtime_acceptance_reports(build_dir)
    archive_path = Path(shutil.make_archive(str(build_dir), "zip", root_dir=build_dir))
    archive_checksum = write_export_archive_checksum_files(archive_path, "原生 Runtime 包（可打包 App）")
    archive_verifiers = write_export_archive_verifier_scripts(archive_path, archive_checksum["archiveSha256"])
    internal_reports = [
        {"name": manifest_path.name, "description": "导出清单，记录目标、版本、素材缺口和 Runtime 信息。"},
        {"name": runtime_files["playtestGuideName"], "description": "试玩与发布验收指南，给测试员快速确认打开方式和验收重点。"},
        {"name": evidence_pack_path.name, "description": "发布证据包，集中索引试玩指南、路线图、发布总控和验收报告。"},
        {"name": story_route_map["storyRouteMapReportName"], "description": "剧情路线图 Markdown，记录坏跳转、不可达场景和结局候选。"},
        {"name": story_route_map["storyRouteMapName"], "description": "机器可读剧情路线图 JSON。"},
        {"name": localization_audit["localizationAuditReportName"], "description": "本地化覆盖 Markdown 报告，记录多语言漏译位置。"},
        {"name": localization_audit["localizationAuditName"], "description": "机器可读本地化覆盖 JSON。"},
        {"name": release_readiness["releaseReadinessReportName"], "description": "发布试玩就绪摘要，快速判断是否适合发给测试员。"},
        {"name": release_readiness["releaseReadinessSummaryName"], "description": "机器可读发布试玩就绪摘要 JSON。"},
        {"name": runtime_files["unlockableContentManifestName"], "description": "可解锁内容清单 JSON，记录图鉴、回想、成就和结局覆盖。"},
        {"name": runtime_files["unlockableContentReportName"], "description": "可解锁内容 Markdown 报告，方便测试员直接复查 EXTRA / 回想覆盖。"},
        {"name": asset_rights_files["assetRightsReportName"], "description": "素材授权与署名 Markdown 报告，复查商用状态、来源、AI 生成记录和 Staff 草稿。"},
        {"name": asset_rights_files["assetRightsName"], "description": "机器可读素材授权清单 JSON。"},
        {"name": asset_rights_files["assetRightsCsvName"], "description": "可导入表格的素材授权 CSV。"},
        {"name": audio_cue_sheet_files["audioCueSheetReportName"], "description": "音频调度 Markdown 报告，复查 BGM 范围、淡入淡出、音效和语音缺口。"},
        {"name": audio_cue_sheet_files["audioCueSheetName"], "description": "机器可读音频调度清单 JSON。"},
        {"name": audio_cue_sheet_files["audioCueSheetCsvName"], "description": "可导入表格的 BGM / SFX / Voice Cue CSV。"},
        {"name": stage_direction_files["stageDirectionReportName"], "description": "角色舞台 Markdown 报告，复查背景、立绘、登退场、站位、缩放和透明度。"},
        {"name": stage_direction_files["stageDirectionName"], "description": "机器可读角色舞台调度清单 JSON。"},
        {"name": stage_direction_files["stageDirectionCsvName"], "description": "可导入表格的角色舞台 Cue CSV。"},
        {"name": presentation_timeline_files["presentationTimelineReportName"], "description": "演出时间轴 Markdown 报告，复查正文节奏、视觉锚点、音频锚点和硬切问题。"},
        {"name": presentation_timeline_files["presentationTimelineName"], "description": "机器可读演出时间轴 JSON。"},
        {"name": presentation_timeline_files["presentationTimelineCsvName"], "description": "可导入表格的演出事件 CSV。"},
        {"name": EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME, "description": "路线试玩 Markdown 工作簿，给测试员逐条执行分支、结局和坏链修复。"},
        {"name": EXPORT_ROUTE_PLAYTEST_WORKBOOK_JSON_NAME, "description": "机器可读路线试玩工作簿 JSON。"},
        {"name": EXPORT_ROUTE_PLAYTEST_WORKBOOK_CSV_NAME, "description": "可导入表格的路线试玩执行 CSV。"},
        {"name": EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME, "description": "选项后果 Markdown 报告，复查坏跳转、假按钮、重复选项和变量效果。"},
        {"name": EXPORT_CHOICE_CONSEQUENCE_JSON_NAME, "description": "机器可读选项后果清单 JSON。"},
        {"name": EXPORT_CHOICE_CONSEQUENCE_CSV_NAME, "description": "可导入表格的选项后果 CSV。"},
        {"name": EXPORT_VARIABLE_INFLUENCE_REPORT_NAME, "description": "变量影响 Markdown 报告，复查变量读写、条件读取、坏引用和类型错误。"},
        {"name": EXPORT_VARIABLE_INFLUENCE_JSON_NAME, "description": "机器可读变量影响清单 JSON。"},
        {"name": EXPORT_VARIABLE_INFLUENCE_CSV_NAME, "description": "可导入表格的变量影响 CSV。"},
        {"name": voice_production_files["voiceProductionReportName"], "description": "配音生产 Markdown 清单，记录台词录音表、角色进度和优先补录问题。"},
        {"name": voice_production_files["voiceProductionName"], "description": "机器可读配音生产清单 JSON。"},
        {"name": voice_production_files["voiceProductionCsvName"], "description": "可交给配音或表格软件的台词录音 CSV。"},
        {"name": runtime_files["runtimePreloadManifestName"], "description": "Runtime 资源预热清单 JSON，记录首屏和早期路线素材。"},
        {"name": runtime_files["runtimePreloadReportName"], "description": "Runtime 资源预热 Markdown 报告，方便复查卡顿风险。"},
        {"name": runtime_files["runtimePreloadModuleName"], "description": "原生 Runtime 资源预热策略模块。"},
        {"name": runtime_files["runtimeSettingsModuleName"], "description": "原生 Runtime 系统设置模块。"},
        {"name": runtime_files["runtimeTextEffectsModuleName"], "description": "原生 Runtime 打字机和文本效果模块。"},
        {"name": runtime_files["runtimeStorageModuleName"], "description": "原生 Runtime 存档、自动恢复和崩溃日志模块。"},
        {"name": runtime_files["runtimeVariablesModuleName"], "description": "原生 Runtime 变量和条件判断模块。"},
        {"name": runtime_files["releaseCheckName"], "description": "发布前自检 JSON。"},
        {"name": runtime_files["releaseCandidateReportName"], "description": "原生 Runtime 发布候选总报告。"},
        {"name": runtime_files["releaseControlReportName"], "description": "人工验收用发布总控 Markdown。"},
        {"name": runtime_files["releaseControlJsonName"], "description": "机器可读发布总控 JSON。"},
        {"name": runtime_files["vnBaselineQualityMarkdownName"], "description": "视觉小说基础质感 Markdown 报告。"},
        {"name": runtime_files["vnBaselineQualityReportName"], "description": "机器可读 VN 基础质感 JSON。"},
        {"name": runtime_files["performanceBudgetMarkdownName"], "description": "原生 Runtime 性能预算 Markdown，复查包体、素材体积和剧情规模。"},
        {"name": runtime_files["performanceBudgetReportName"], "description": "机器可读原生 Runtime 性能预算 JSON。"},
        {"name": integrity_files["fileIntegrityMarkdownName"], "description": "包内核心文件完整性 Markdown。"},
        {"name": integrity_files["fileIntegrityReportName"], "description": "包内核心文件 SHA-256 JSON。"},
        {"name": provenance_file["provenanceName"], "description": "低调来源标记与文件指纹清单。"},
        {"name": provenance_verifiers["provenanceVerifierName"], "description": "低调来源与文件指纹校验脚本。"},
        {"name": acceptance_files["acceptanceReportName"], "description": "三系统人工验收清单 Markdown。"},
        {"name": acceptance_files["acceptanceJsonName"], "description": "机器可读发布验收清单 JSON。"},
        {"name": runtime_files["asset3dSummaryName"], "description": "3D 资产 Markdown 摘要。"},
        {"name": runtime_files["asset3dDigestName"], "description": "3D 风险精简摘要 JSON。"},
    ]
    release_notes = write_export_release_notes_draft(
        archive_path,
        "原生 Runtime 包（可打包 App）",
        archive_checksum,
        archive_verifiers,
        internal_reports,
    )
    release_artifacts = write_export_release_artifact_index(
        archive_path,
        "原生 Runtime 包（可打包 App）",
        archive_checksum,
        archive_verifiers,
        release_notes,
        internal_reports,
    )
    return {
        "target": EXPORT_TARGET_NATIVE_RUNTIME,
        "targetLabel": "原生 Runtime 包（可打包 App）",
        "buildPath": str(build_dir),
        "releaseVersion": release_version,
        "archivePath": str(archive_path),
        "archiveName": archive_path.name,
        "archivePublicUrl": f"/exports/{archive_path.name}",
        "archiveSha256": archive_checksum["archiveSha256"],
        "archiveSizeBytes": archive_checksum["archiveSizeBytes"],
        "archiveSizeLabel": archive_checksum["archiveSizeLabel"],
        "archiveChecksumName": archive_checksum["archiveChecksumName"],
        "archiveChecksumPath": archive_checksum["archiveChecksumPath"],
        "archiveChecksumPublicUrl": f"/exports/{archive_checksum['archiveChecksumName']}",
        "archiveChecksumJsonName": archive_checksum["archiveChecksumJsonName"],
        "archiveChecksumJsonPath": archive_checksum["archiveChecksumJsonPath"],
        "archiveChecksumJsonPublicUrl": f"/exports/{archive_checksum['archiveChecksumJsonName']}",
        "archiveVerifierMacName": archive_verifiers["archiveVerifierMacName"],
        "archiveVerifierMacPath": archive_verifiers["archiveVerifierMacPath"],
        "archiveVerifierMacPublicUrl": f"/exports/{archive_verifiers['archiveVerifierMacName']}",
        "archiveVerifierLinuxName": archive_verifiers["archiveVerifierLinuxName"],
        "archiveVerifierLinuxPath": archive_verifiers["archiveVerifierLinuxPath"],
        "archiveVerifierLinuxPublicUrl": f"/exports/{archive_verifiers['archiveVerifierLinuxName']}",
        "archiveVerifierWindowsName": archive_verifiers["archiveVerifierWindowsName"],
        "archiveVerifierWindowsPath": archive_verifiers["archiveVerifierWindowsPath"],
        "archiveVerifierWindowsPublicUrl": f"/exports/{archive_verifiers['archiveVerifierWindowsName']}",
        "releaseNotesName": release_notes["releaseNotesName"],
        "releaseNotesPath": release_notes["releaseNotesPath"],
        "releaseNotesPublicUrl": f"/exports/{release_notes['releaseNotesName']}",
        "releaseArtifactIndexName": release_artifacts["releaseArtifactIndexName"],
        "releaseArtifactIndexPath": release_artifacts["releaseArtifactIndexPath"],
        "releaseArtifactIndexPublicUrl": f"/exports/{release_artifacts['releaseArtifactIndexName']}",
        "releaseArtifactIndexJsonName": release_artifacts["releaseArtifactIndexJsonName"],
        "releaseArtifactIndexJsonPath": release_artifacts["releaseArtifactIndexJsonPath"],
        "releaseArtifactIndexJsonPublicUrl": f"/exports/{release_artifacts['releaseArtifactIndexJsonName']}",
        "releaseArtifactUploadCount": release_artifacts["releaseArtifactUploadCount"],
        "copiedAssets": copied_assets,
        "missingAssets": len(missing_assets),
        "missingAssetNames": [asset.get("name") or asset.get("id") or "未命名素材" for asset in missing_assets],
        "runtimeMode": "pygame_native",
        "runtimeModeLabel": "Python + pygame-ce 原生 Runtime",
        "manifestPath": str(manifest_path),
        "manifestName": manifest_path.name,
        "manifestPublicUrl": f"/exports/{build_dir.name}/{manifest_path.name}",
        "playtestGuideName": runtime_files["playtestGuideName"],
        "playtestGuidePath": runtime_files["playtestGuidePath"],
        "playtestGuidePublicUrl": f"/exports/{build_dir.name}/{runtime_files['playtestGuideName']}",
        "releaseEvidencePackName": evidence_pack_path.name,
        "releaseEvidencePackPath": str(evidence_pack_path),
        "releaseEvidencePackPublicUrl": f"/exports/{build_dir.name}/{evidence_pack_path.name}",
        "assetRightsName": asset_rights_files["assetRightsName"],
        "assetRightsPath": asset_rights_files["assetRightsPath"],
        "assetRightsPublicUrl": f"/exports/{build_dir.name}/{asset_rights_files['assetRightsName']}",
        "assetRightsReportName": asset_rights_files["assetRightsReportName"],
        "assetRightsReportPath": asset_rights_files["assetRightsReportPath"],
        "assetRightsReportPublicUrl": f"/exports/{build_dir.name}/{asset_rights_files['assetRightsReportName']}",
        "assetRightsCsvName": asset_rights_files["assetRightsCsvName"],
        "assetRightsCsvPath": asset_rights_files["assetRightsCsvPath"],
        "assetRightsCsvPublicUrl": f"/exports/{build_dir.name}/{asset_rights_files['assetRightsCsvName']}",
        "assetRightsReadinessPercent": asset_rights_files["assetRightsReadinessPercent"],
        "assetRightsBlockerCount": asset_rights_files["assetRightsBlockerCount"],
        "assetRightsWarningCount": asset_rights_files["assetRightsWarningCount"],
        "audioCueSheetName": audio_cue_sheet_files["audioCueSheetName"],
        "audioCueSheetPath": audio_cue_sheet_files["audioCueSheetPath"],
        "audioCueSheetPublicUrl": f"/exports/{build_dir.name}/{audio_cue_sheet_files['audioCueSheetName']}",
        "audioCueSheetReportName": audio_cue_sheet_files["audioCueSheetReportName"],
        "audioCueSheetReportPath": audio_cue_sheet_files["audioCueSheetReportPath"],
        "audioCueSheetReportPublicUrl": f"/exports/{build_dir.name}/{audio_cue_sheet_files['audioCueSheetReportName']}",
        "audioCueSheetCsvName": audio_cue_sheet_files["audioCueSheetCsvName"],
        "audioCueSheetCsvPath": audio_cue_sheet_files["audioCueSheetCsvPath"],
        "audioCueSheetCsvPublicUrl": f"/exports/{build_dir.name}/{audio_cue_sheet_files['audioCueSheetCsvName']}",
        "audioCueSheetReadinessPercent": audio_cue_sheet_files["audioCueSheetReadinessPercent"],
        "audioCueSheetCueCount": audio_cue_sheet_files["audioCueSheetCueCount"],
        "audioCueSheetBlockerCount": audio_cue_sheet_files["audioCueSheetBlockerCount"],
        "audioCueSheetWarningCount": audio_cue_sheet_files["audioCueSheetWarningCount"],
        "stageDirectionName": stage_direction_files["stageDirectionName"],
        "stageDirectionPath": stage_direction_files["stageDirectionPath"],
        "stageDirectionPublicUrl": f"/exports/{build_dir.name}/{stage_direction_files['stageDirectionName']}",
        "stageDirectionReportName": stage_direction_files["stageDirectionReportName"],
        "stageDirectionReportPath": stage_direction_files["stageDirectionReportPath"],
        "stageDirectionReportPublicUrl": f"/exports/{build_dir.name}/{stage_direction_files['stageDirectionReportName']}",
        "stageDirectionCsvName": stage_direction_files["stageDirectionCsvName"],
        "stageDirectionCsvPath": stage_direction_files["stageDirectionCsvPath"],
        "stageDirectionCsvPublicUrl": f"/exports/{build_dir.name}/{stage_direction_files['stageDirectionCsvName']}",
        "stageDirectionReadinessPercent": stage_direction_files["stageDirectionReadinessPercent"],
        "stageDirectionEventCount": stage_direction_files["stageDirectionEventCount"],
        "stageDirectionBlockerCount": stage_direction_files["stageDirectionBlockerCount"],
        "stageDirectionWarningCount": stage_direction_files["stageDirectionWarningCount"],
        "presentationTimelineName": presentation_timeline_files["presentationTimelineName"],
        "presentationTimelinePath": presentation_timeline_files["presentationTimelinePath"],
        "presentationTimelinePublicUrl": f"/exports/{build_dir.name}/{presentation_timeline_files['presentationTimelineName']}",
        "presentationTimelineReportName": presentation_timeline_files["presentationTimelineReportName"],
        "presentationTimelineReportPath": presentation_timeline_files["presentationTimelineReportPath"],
        "presentationTimelineReportPublicUrl": f"/exports/{build_dir.name}/{presentation_timeline_files['presentationTimelineReportName']}",
        "presentationTimelineCsvName": presentation_timeline_files["presentationTimelineCsvName"],
        "presentationTimelineCsvPath": presentation_timeline_files["presentationTimelineCsvPath"],
        "presentationTimelineCsvPublicUrl": f"/exports/{build_dir.name}/{presentation_timeline_files['presentationTimelineCsvName']}",
        "presentationTimelineReadinessPercent": presentation_timeline_files["presentationTimelineReadinessPercent"],
        "presentationTimelineEventCount": presentation_timeline_files["presentationTimelineEventCount"],
        "presentationTimelineBlockerCount": presentation_timeline_files["presentationTimelineBlockerCount"],
        "presentationTimelineWarningCount": presentation_timeline_files["presentationTimelineWarningCount"],
        "routePlaytestWorkbookName": story_route_map["routePlaytestWorkbookName"],
        "routePlaytestWorkbookPath": story_route_map["routePlaytestWorkbookPath"],
        "routePlaytestWorkbookPublicUrl": f"/exports/{build_dir.name}/{story_route_map['routePlaytestWorkbookName']}",
        "routePlaytestWorkbookReportName": story_route_map["routePlaytestWorkbookReportName"],
        "routePlaytestWorkbookReportPath": story_route_map["routePlaytestWorkbookReportPath"],
        "routePlaytestWorkbookReportPublicUrl": f"/exports/{build_dir.name}/{story_route_map['routePlaytestWorkbookReportName']}",
        "routePlaytestWorkbookCsvName": story_route_map["routePlaytestWorkbookCsvName"],
        "routePlaytestWorkbookCsvPath": story_route_map["routePlaytestWorkbookCsvPath"],
        "routePlaytestWorkbookCsvPublicUrl": f"/exports/{build_dir.name}/{story_route_map['routePlaytestWorkbookCsvName']}",
        "routePlaytestReadinessPercent": story_route_map["routePlaytestReadinessPercent"],
        "routePlaytestRouteCaseCount": story_route_map["routePlaytestRouteCaseCount"],
        "routePlaytestEndingCaseCount": story_route_map["routePlaytestEndingCaseCount"],
        "routePlaytestBlockedCaseCount": story_route_map["routePlaytestBlockedCaseCount"],
        "choiceConsequenceName": story_route_map["choiceConsequenceName"],
        "choiceConsequencePath": story_route_map["choiceConsequencePath"],
        "choiceConsequencePublicUrl": f"/exports/{build_dir.name}/{story_route_map['choiceConsequenceName']}",
        "choiceConsequenceReportName": story_route_map["choiceConsequenceReportName"],
        "choiceConsequenceReportPath": story_route_map["choiceConsequenceReportPath"],
        "choiceConsequenceReportPublicUrl": f"/exports/{build_dir.name}/{story_route_map['choiceConsequenceReportName']}",
        "choiceConsequenceCsvName": story_route_map["choiceConsequenceCsvName"],
        "choiceConsequenceCsvPath": story_route_map["choiceConsequenceCsvPath"],
        "choiceConsequenceCsvPublicUrl": f"/exports/{build_dir.name}/{story_route_map['choiceConsequenceCsvName']}",
        "choiceConsequenceReadinessPercent": story_route_map["choiceConsequenceReadinessPercent"],
        "choiceConsequenceOptionCount": story_route_map["choiceConsequenceOptionCount"],
        "choiceConsequenceBlockerCount": story_route_map["choiceConsequenceBlockerCount"],
        "choiceConsequenceWarningCount": story_route_map["choiceConsequenceWarningCount"],
        "variableInfluenceName": story_route_map["variableInfluenceName"],
        "variableInfluencePath": story_route_map["variableInfluencePath"],
        "variableInfluencePublicUrl": f"/exports/{build_dir.name}/{story_route_map['variableInfluenceName']}",
        "variableInfluenceReportName": story_route_map["variableInfluenceReportName"],
        "variableInfluenceReportPath": story_route_map["variableInfluenceReportPath"],
        "variableInfluenceReportPublicUrl": f"/exports/{build_dir.name}/{story_route_map['variableInfluenceReportName']}",
        "variableInfluenceCsvName": story_route_map["variableInfluenceCsvName"],
        "variableInfluenceCsvPath": story_route_map["variableInfluenceCsvPath"],
        "variableInfluenceCsvPublicUrl": f"/exports/{build_dir.name}/{story_route_map['variableInfluenceCsvName']}",
        "variableInfluenceReadinessPercent": story_route_map["variableInfluenceReadinessPercent"],
        "variableInfluenceVariableCount": story_route_map["variableInfluenceVariableCount"],
        "variableInfluenceBlockerCount": story_route_map["variableInfluenceBlockerCount"],
        "variableInfluenceWarningCount": story_route_map["variableInfluenceWarningCount"],
        "voiceProductionName": voice_production_files["voiceProductionName"],
        "voiceProductionPath": voice_production_files["voiceProductionPath"],
        "voiceProductionPublicUrl": f"/exports/{build_dir.name}/{voice_production_files['voiceProductionName']}",
        "voiceProductionReportName": voice_production_files["voiceProductionReportName"],
        "voiceProductionReportPath": voice_production_files["voiceProductionReportPath"],
        "voiceProductionReportPublicUrl": f"/exports/{build_dir.name}/{voice_production_files['voiceProductionReportName']}",
        "voiceProductionCsvName": voice_production_files["voiceProductionCsvName"],
        "voiceProductionCsvPath": voice_production_files["voiceProductionCsvPath"],
        "voiceProductionCsvPublicUrl": f"/exports/{build_dir.name}/{voice_production_files['voiceProductionCsvName']}",
        "voiceProductionReadyPercent": voice_production_files["voiceProductionReadyPercent"],
        "voiceProductionLineCount": voice_production_files["voiceProductionLineCount"],
        "voiceProductionBlockerCount": voice_production_files["voiceProductionBlockerCount"],
        "voiceProductionWarningCount": voice_production_files["voiceProductionWarningCount"],
        "storyRouteMapName": story_route_map["storyRouteMapName"],
        "storyRouteMapPath": story_route_map["storyRouteMapPath"],
        "storyRouteMapPublicUrl": f"/exports/{build_dir.name}/{story_route_map['storyRouteMapName']}",
        "storyRouteMapReportName": story_route_map["storyRouteMapReportName"],
        "storyRouteMapReportPath": story_route_map["storyRouteMapReportPath"],
        "storyRouteMapReportPublicUrl": f"/exports/{build_dir.name}/{story_route_map['storyRouteMapReportName']}",
        "storyRouteMapStatus": story_route_map["storyRouteMapStatus"],
        "localizationAuditName": localization_audit["localizationAuditName"],
        "localizationAuditPath": localization_audit["localizationAuditPath"],
        "localizationAuditPublicUrl": f"/exports/{build_dir.name}/{localization_audit['localizationAuditName']}",
        "localizationAuditReportName": localization_audit["localizationAuditReportName"],
        "localizationAuditReportPath": localization_audit["localizationAuditReportPath"],
        "localizationAuditReportPublicUrl": f"/exports/{build_dir.name}/{localization_audit['localizationAuditReportName']}",
        "localizationAuditStatus": localization_audit["localizationAuditStatus"],
        "localizationAuditCompletionPercent": localization_audit["localizationAuditCompletionPercent"],
        "releaseReadinessSummaryName": release_readiness["releaseReadinessSummaryName"],
        "releaseReadinessSummaryPath": release_readiness["releaseReadinessSummaryPath"],
        "releaseReadinessSummaryPublicUrl": f"/exports/{build_dir.name}/{release_readiness['releaseReadinessSummaryName']}",
        "releaseReadinessReportName": release_readiness["releaseReadinessReportName"],
        "releaseReadinessReportPath": release_readiness["releaseReadinessReportPath"],
        "releaseReadinessReportPublicUrl": f"/exports/{build_dir.name}/{release_readiness['releaseReadinessReportName']}",
        "releaseReadinessStatus": release_readiness["releaseReadinessStatus"],
        "releaseReadinessScore": release_readiness["releaseReadinessScore"],
        "gameDataPath": runtime_files["gameDataPath"],
        "gameDataPublicUrl": f"/exports/{build_dir.name}/{runtime_files['gameDataName']}",
        "unlockableContentManifestName": runtime_files["unlockableContentManifestName"],
        "unlockableContentManifestPath": runtime_files["unlockableContentManifestPath"],
        "unlockableContentManifestPublicUrl": f"/exports/{build_dir.name}/{runtime_files['unlockableContentManifestName']}",
        "unlockableContentReportName": runtime_files["unlockableContentReportName"],
        "unlockableContentReportPath": runtime_files["unlockableContentReportPath"],
        "unlockableContentReportPublicUrl": f"/exports/{build_dir.name}/{runtime_files['unlockableContentReportName']}",
        "runtimePreloadManifestName": runtime_files["runtimePreloadManifestName"],
        "runtimePreloadManifestPath": runtime_files["runtimePreloadManifestPath"],
        "runtimePreloadManifestPublicUrl": f"/exports/{build_dir.name}/{runtime_files['runtimePreloadManifestName']}",
        "runtimePreloadReportName": runtime_files["runtimePreloadReportName"],
        "runtimePreloadReportPath": runtime_files["runtimePreloadReportPath"],
        "runtimePreloadReportPublicUrl": f"/exports/{build_dir.name}/{runtime_files['runtimePreloadReportName']}",
        "runtimePreloadSummary": runtime_files["runtimePreloadSummary"],
        "playerScriptPath": runtime_files["playerPath"],
        "playerScriptName": runtime_files["playerName"],
        "playerScriptPublicUrl": f"/exports/{build_dir.name}/{runtime_files['playerName']}",
        "runtimePreloadModuleName": runtime_files["runtimePreloadModuleName"],
        "runtimePreloadModulePath": runtime_files["runtimePreloadModulePath"],
        "runtimePreloadModulePublicUrl": f"/exports/{build_dir.name}/{runtime_files['runtimePreloadModuleName']}",
        "runtimePerformanceModuleName": runtime_files["runtimePerformanceModuleName"],
        "runtimePerformanceModulePath": runtime_files["runtimePerformanceModulePath"],
        "runtimePerformanceModulePublicUrl": f"/exports/{build_dir.name}/{runtime_files['runtimePerformanceModuleName']}",
        "runtimeSettingsModuleName": runtime_files["runtimeSettingsModuleName"],
        "runtimeSettingsModulePath": runtime_files["runtimeSettingsModulePath"],
        "runtimeSettingsModulePublicUrl": f"/exports/{build_dir.name}/{runtime_files['runtimeSettingsModuleName']}",
        "runtimeTextEffectsModuleName": runtime_files["runtimeTextEffectsModuleName"],
        "runtimeTextEffectsModulePath": runtime_files["runtimeTextEffectsModulePath"],
        "runtimeTextEffectsModulePublicUrl": f"/exports/{build_dir.name}/{runtime_files['runtimeTextEffectsModuleName']}",
        "runtimeStorageModuleName": runtime_files["runtimeStorageModuleName"],
        "runtimeStorageModulePath": runtime_files["runtimeStorageModulePath"],
        "runtimeStorageModulePublicUrl": f"/exports/{build_dir.name}/{runtime_files['runtimeStorageModuleName']}",
        "runtimeVariablesModuleName": runtime_files["runtimeVariablesModuleName"],
        "runtimeVariablesModulePath": runtime_files["runtimeVariablesModulePath"],
        "runtimeVariablesModulePublicUrl": f"/exports/{build_dir.name}/{runtime_files['runtimeVariablesModuleName']}",
        "readmeName": runtime_files["readmeName"],
        "readmePath": runtime_files["readmePath"],
        "readmePublicUrl": f"/exports/{build_dir.name}/{runtime_files['readmeName']}",
        "requirementsName": runtime_files["requirementsName"],
        "requirementsPath": runtime_files["requirementsPath"],
        "requirementsPublicUrl": f"/exports/{build_dir.name}/{runtime_files['requirementsName']}",
        "buildRequirementsName": runtime_files["buildRequirementsName"],
        "buildRequirementsPath": runtime_files["buildRequirementsPath"],
        "buildRequirementsPublicUrl": f"/exports/{build_dir.name}/{runtime_files['buildRequirementsName']}",
        "appBuilderName": runtime_files["appBuilderName"],
        "appBuilderPath": runtime_files["appBuilderPath"],
        "appBuilderPublicUrl": f"/exports/{build_dir.name}/{runtime_files['appBuilderName']}",
        "releaseCheckName": runtime_files["releaseCheckName"],
        "releaseCheckPath": runtime_files["releaseCheckPath"],
        "releaseCheckPublicUrl": f"/exports/{build_dir.name}/{runtime_files['releaseCheckName']}",
        "releaseCandidateReportName": runtime_files["releaseCandidateReportName"],
        "releaseCandidateReportPath": runtime_files["releaseCandidateReportPath"],
        "releaseCandidateReportPublicUrl": f"/exports/{build_dir.name}/{runtime_files['releaseCandidateReportName']}",
        "releaseCandidateReportStatus": runtime_files["releaseCandidateReportStatus"],
        "releaseCandidateReportSummary": runtime_files["releaseCandidateReportSummary"],
        "releaseCandidateReadinessEstimate": runtime_files["releaseCandidateReadinessEstimate"],
        "releaseControlReportName": runtime_files["releaseControlReportName"],
        "releaseControlReportPath": runtime_files["releaseControlReportPath"],
        "releaseControlReportPublicUrl": f"/exports/{build_dir.name}/{runtime_files['releaseControlReportName']}",
        "releaseControlJsonName": runtime_files["releaseControlJsonName"],
        "releaseControlJsonPath": runtime_files["releaseControlJsonPath"],
        "releaseControlJsonPublicUrl": f"/exports/{build_dir.name}/{runtime_files['releaseControlJsonName']}",
        "releaseControlStatus": runtime_files["releaseControlStatus"],
        "releaseControlSummary": runtime_files["releaseControlSummary"],
        "vnBaselineQualityReportName": runtime_files["vnBaselineQualityReportName"],
        "vnBaselineQualityReportPath": runtime_files["vnBaselineQualityReportPath"],
        "vnBaselineQualityReportPublicUrl": f"/exports/{build_dir.name}/{runtime_files['vnBaselineQualityReportName']}",
        "vnBaselineQualityMarkdownName": runtime_files["vnBaselineQualityMarkdownName"],
        "vnBaselineQualityMarkdownPath": runtime_files["vnBaselineQualityMarkdownPath"],
        "vnBaselineQualityMarkdownPublicUrl": f"/exports/{build_dir.name}/{runtime_files['vnBaselineQualityMarkdownName']}",
        "vnBaselineQualityStatus": runtime_files["vnBaselineQualityStatus"],
        "performanceBudgetReportName": runtime_files["performanceBudgetReportName"],
        "performanceBudgetReportPath": runtime_files["performanceBudgetReportPath"],
        "performanceBudgetReportPublicUrl": f"/exports/{build_dir.name}/{runtime_files['performanceBudgetReportName']}",
        "performanceBudgetMarkdownName": runtime_files["performanceBudgetMarkdownName"],
        "performanceBudgetMarkdownPath": runtime_files["performanceBudgetMarkdownPath"],
        "performanceBudgetMarkdownPublicUrl": f"/exports/{build_dir.name}/{runtime_files['performanceBudgetMarkdownName']}",
        "performanceBudgetStatus": runtime_files["performanceBudgetStatus"],
        "performanceBudgetSummary": runtime_files["performanceBudgetSummary"],
        "fileIntegrityReportName": integrity_files["fileIntegrityReportName"],
        "fileIntegrityReportPath": integrity_files["fileIntegrityReportPath"],
        "fileIntegrityReportPublicUrl": f"/exports/{build_dir.name}/{integrity_files['fileIntegrityReportName']}",
        "fileIntegrityMarkdownName": integrity_files["fileIntegrityMarkdownName"],
        "fileIntegrityMarkdownPath": integrity_files["fileIntegrityMarkdownPath"],
        "fileIntegrityMarkdownPublicUrl": f"/exports/{build_dir.name}/{integrity_files['fileIntegrityMarkdownName']}",
        "fileIntegrityStatus": integrity_files["fileIntegrityStatus"],
        "fileIntegritySummary": integrity_files["fileIntegritySummary"],
        "provenanceName": provenance_file["provenanceName"],
        "provenancePath": provenance_file["provenancePath"],
        "provenancePublicUrl": f"/exports/{build_dir.name}/{provenance_file['provenanceName']}",
        "provenanceSeal": provenance_file["provenanceSeal"],
        "provenanceSummary": provenance_file["provenanceSummary"],
        "provenanceVerifierName": provenance_verifiers["provenanceVerifierName"],
        "provenanceVerifierPath": provenance_verifiers["provenanceVerifierPath"],
        "provenanceVerifierPublicUrl": f"/exports/{build_dir.name}/{provenance_verifiers['provenanceVerifierName']}",
        "provenanceVerifierMacName": provenance_verifiers["provenanceVerifierMacName"],
        "provenanceVerifierMacPath": provenance_verifiers["provenanceVerifierMacPath"],
        "provenanceVerifierMacPublicUrl": f"/exports/{build_dir.name}/{provenance_verifiers['provenanceVerifierMacName']}",
        "provenanceVerifierLinuxName": provenance_verifiers["provenanceVerifierLinuxName"],
        "provenanceVerifierLinuxPath": provenance_verifiers["provenanceVerifierLinuxPath"],
        "provenanceVerifierLinuxPublicUrl": f"/exports/{build_dir.name}/{provenance_verifiers['provenanceVerifierLinuxName']}",
        "provenanceVerifierWindowsName": provenance_verifiers["provenanceVerifierWindowsName"],
        "provenanceVerifierWindowsPath": provenance_verifiers["provenanceVerifierWindowsPath"],
        "provenanceVerifierWindowsPublicUrl": f"/exports/{build_dir.name}/{provenance_verifiers['provenanceVerifierWindowsName']}",
        "acceptanceReportName": acceptance_files["acceptanceReportName"],
        "acceptanceReportPath": acceptance_files["acceptanceReportPath"],
        "acceptanceReportPublicUrl": f"/exports/{build_dir.name}/{acceptance_files['acceptanceReportName']}",
        "acceptanceJsonName": acceptance_files["acceptanceJsonName"],
        "acceptanceJsonPath": acceptance_files["acceptanceJsonPath"],
        "acceptanceJsonPublicUrl": f"/exports/{build_dir.name}/{acceptance_files['acceptanceJsonName']}",
        "acceptanceStatus": acceptance_files["acceptanceStatus"],
        "acceptanceSummary": acceptance_files["acceptanceSummary"],
        "asset3dReportName": runtime_files["asset3dReportName"],
        "asset3dReportPath": runtime_files["asset3dReportPath"],
        "asset3dReportPublicUrl": f"/exports/{build_dir.name}/{runtime_files['asset3dReportName']}",
        "asset3dSummaryName": runtime_files["asset3dSummaryName"],
        "asset3dSummaryPath": runtime_files["asset3dSummaryPath"],
        "asset3dSummaryPublicUrl": f"/exports/{build_dir.name}/{runtime_files['asset3dSummaryName']}",
        "asset3dDigestName": runtime_files["asset3dDigestName"],
        "asset3dDigestPath": runtime_files["asset3dDigestPath"],
        "asset3dDigestPublicUrl": f"/exports/{build_dir.name}/{runtime_files['asset3dDigestName']}",
        "asset3dReportStatus": runtime_files["asset3dReportStatus"],
        "asset3dReportSummary": runtime_files["asset3dReportSummary"],
        "asset3dReportDigest": runtime_files["asset3dReportDigest"],
        "macLauncherName": runtime_files["macLauncherName"],
        "macLauncherPath": runtime_files["macLauncherPath"],
        "macLauncherPublicUrl": f"/exports/{build_dir.name}/{runtime_files['macLauncherName']}",
        "linuxLauncherName": runtime_files["linuxLauncherName"],
        "linuxLauncherPath": runtime_files["linuxLauncherPath"],
        "linuxLauncherPublicUrl": f"/exports/{build_dir.name}/{runtime_files['linuxLauncherName']}",
        "windowsLauncherName": runtime_files["windowsLauncherName"],
        "windowsLauncherPath": runtime_files["windowsLauncherPath"],
        "windowsLauncherPublicUrl": f"/exports/{build_dir.name}/{runtime_files['windowsLauncherName']}",
        "macReleaseCandidateCheckerName": runtime_files["macReleaseCandidateCheckerName"],
        "macReleaseCandidateCheckerPath": runtime_files["macReleaseCandidateCheckerPath"],
        "macReleaseCandidateCheckerPublicUrl": f"/exports/{build_dir.name}/{runtime_files['macReleaseCandidateCheckerName']}",
        "linuxReleaseCandidateCheckerName": runtime_files["linuxReleaseCandidateCheckerName"],
        "linuxReleaseCandidateCheckerPath": runtime_files["linuxReleaseCandidateCheckerPath"],
        "linuxReleaseCandidateCheckerPublicUrl": f"/exports/{build_dir.name}/{runtime_files['linuxReleaseCandidateCheckerName']}",
        "windowsReleaseCandidateCheckerName": runtime_files["windowsReleaseCandidateCheckerName"],
        "windowsReleaseCandidateCheckerPath": runtime_files["windowsReleaseCandidateCheckerPath"],
        "windowsReleaseCandidateCheckerPublicUrl": f"/exports/{build_dir.name}/{runtime_files['windowsReleaseCandidateCheckerName']}",
        "macReleaseControlReporterName": runtime_files["macReleaseControlReporterName"],
        "macReleaseControlReporterPath": runtime_files["macReleaseControlReporterPath"],
        "macReleaseControlReporterPublicUrl": f"/exports/{build_dir.name}/{runtime_files['macReleaseControlReporterName']}",
        "linuxReleaseControlReporterName": runtime_files["linuxReleaseControlReporterName"],
        "linuxReleaseControlReporterPath": runtime_files["linuxReleaseControlReporterPath"],
        "linuxReleaseControlReporterPublicUrl": f"/exports/{build_dir.name}/{runtime_files['linuxReleaseControlReporterName']}",
        "windowsReleaseControlReporterName": runtime_files["windowsReleaseControlReporterName"],
        "windowsReleaseControlReporterPath": runtime_files["windowsReleaseControlReporterPath"],
        "windowsReleaseControlReporterPublicUrl": f"/exports/{build_dir.name}/{runtime_files['windowsReleaseControlReporterName']}",
        "macAcceptanceReporterName": runtime_files["macAcceptanceReporterName"],
        "macAcceptanceReporterPath": runtime_files["macAcceptanceReporterPath"],
        "macAcceptanceReporterPublicUrl": f"/exports/{build_dir.name}/{runtime_files['macAcceptanceReporterName']}",
        "linuxAcceptanceReporterName": runtime_files["linuxAcceptanceReporterName"],
        "linuxAcceptanceReporterPath": runtime_files["linuxAcceptanceReporterPath"],
        "linuxAcceptanceReporterPublicUrl": f"/exports/{build_dir.name}/{runtime_files['linuxAcceptanceReporterName']}",
        "windowsAcceptanceReporterName": runtime_files["windowsAcceptanceReporterName"],
        "windowsAcceptanceReporterPath": runtime_files["windowsAcceptanceReporterPath"],
        "windowsAcceptanceReporterPublicUrl": f"/exports/{build_dir.name}/{runtime_files['windowsAcceptanceReporterName']}",
        "macFileIntegrityCheckerName": runtime_files["macFileIntegrityCheckerName"],
        "macFileIntegrityCheckerPath": runtime_files["macFileIntegrityCheckerPath"],
        "macFileIntegrityCheckerPublicUrl": f"/exports/{build_dir.name}/{runtime_files['macFileIntegrityCheckerName']}",
        "linuxFileIntegrityCheckerName": runtime_files["linuxFileIntegrityCheckerName"],
        "linuxFileIntegrityCheckerPath": runtime_files["linuxFileIntegrityCheckerPath"],
        "linuxFileIntegrityCheckerPublicUrl": f"/exports/{build_dir.name}/{runtime_files['linuxFileIntegrityCheckerName']}",
        "windowsFileIntegrityCheckerName": runtime_files["windowsFileIntegrityCheckerName"],
        "windowsFileIntegrityCheckerPath": runtime_files["windowsFileIntegrityCheckerPath"],
        "windowsFileIntegrityCheckerPublicUrl": f"/exports/{build_dir.name}/{runtime_files['windowsFileIntegrityCheckerName']}",
        "macAppBuilderName": runtime_files["macAppBuilderName"],
        "macAppBuilderPath": runtime_files["macAppBuilderPath"],
        "macAppBuilderPublicUrl": f"/exports/{build_dir.name}/{runtime_files['macAppBuilderName']}",
        "linuxAppBuilderName": runtime_files["linuxAppBuilderName"],
        "linuxAppBuilderPath": runtime_files["linuxAppBuilderPath"],
        "linuxAppBuilderPublicUrl": f"/exports/{build_dir.name}/{runtime_files['linuxAppBuilderName']}",
        "windowsAppBuilderName": runtime_files["windowsAppBuilderName"],
        "windowsAppBuilderPath": runtime_files["windowsAppBuilderPath"],
        "windowsAppBuilderPublicUrl": f"/exports/{build_dir.name}/{runtime_files['windowsAppBuilderName']}",
    }


def export_web_build() -> dict:
    build_dir = create_export_build_dir("web_build")
    bundle = load_project_bundle()
    export_assets_doc, copied_assets, missing_assets = copy_assets_for_export(bundle["assets"], build_dir)
    export_payload = build_export_payload(bundle, export_assets_doc, copied_assets, missing_assets)
    release_version = get_export_release_version(bundle["project"])
    splash_file = write_export_splash_asset(build_dir, bundle["project"], release_version, "Canvasia Engine 网页试玩包")
    export_payload["buildInfo"]["releaseVersion"] = release_version
    export_payload["buildInfo"]["exportTargetLabel"] = "网页试玩包"
    export_payload["buildInfo"]["splashImageUrl"] = splash_file["relativePath"]
    write_export_app_files(build_dir, export_payload)
    icon_png_bytes = build_export_icon_png(bundle["project"])
    icon_ico_bytes = build_export_icon_ico(icon_png_bytes)
    icon_files = write_export_icon_files(build_dir, icon_png_bytes, icon_ico_bytes)
    launch_steps = [
        "双击或用浏览器打开 `index.html`。",
        "如果浏览器限制本地文件读取，请回到编辑器导出页使用预览链接，或把整个文件夹放到任意静态服务器。",
        "对外发送时请压缩整个导出文件夹，不要只发送 `index.html`。",
    ]
    runtime_notes = ["网页试玩包适合快速分享和轻量测试；正式发行前仍建议补做目标平台点测。"]
    manifest = build_export_manifest(
        bundle,
        target=EXPORT_TARGET_WEB,
        target_label="网页试玩包",
        build_id=build_dir.name,
        copied_assets=copied_assets,
        missing_assets=missing_assets,
        extra_files={
            "entryHtml": "index.html",
            "playerCss": "player.css",
            "playerJs": "player.js",
            "playerRuntimeConditions": "runtime_conditions.js",
            "playerRuntimeControls": "runtime_controls.js",
            "playerRuntimeSettings": "runtime_settings.js",
            "playerRuntimeAudio": "runtime_audio.js",
            "playerRuntimePreload": "runtime_preload.js",
            "runtimePreloadManifest": RUNTIME_PRELOAD_MANIFEST_FILE_NAME,
            "runtimePreloadReport": RUNTIME_PRELOAD_REPORT_FILE_NAME,
            "playtestGuide": EXPORT_PLAYTEST_GUIDE_FILE_NAME,
            "releaseEvidencePack": EXPORT_RELEASE_EVIDENCE_PACK_NAME,
            "assetRights": EXPORT_ASSET_RIGHTS_JSON_NAME,
            "assetRightsReport": EXPORT_ASSET_RIGHTS_REPORT_NAME,
            "assetRightsCsv": EXPORT_ASSET_RIGHTS_CSV_NAME,
            "audioCueSheet": EXPORT_AUDIO_CUE_SHEET_JSON_NAME,
            "audioCueSheetReport": EXPORT_AUDIO_CUE_SHEET_REPORT_NAME,
            "audioCueSheetCsv": EXPORT_AUDIO_CUE_SHEET_CSV_NAME,
            "stageDirection": EXPORT_STAGE_DIRECTION_JSON_NAME,
            "stageDirectionReport": EXPORT_STAGE_DIRECTION_REPORT_NAME,
            "stageDirectionCsv": EXPORT_STAGE_DIRECTION_CSV_NAME,
            "presentationTimeline": EXPORT_PRESENTATION_TIMELINE_JSON_NAME,
            "presentationTimelineReport": EXPORT_PRESENTATION_TIMELINE_REPORT_NAME,
            "presentationTimelineCsv": EXPORT_PRESENTATION_TIMELINE_CSV_NAME,
            "routePlaytestWorkbook": EXPORT_ROUTE_PLAYTEST_WORKBOOK_JSON_NAME,
            "routePlaytestWorkbookReport": EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME,
            "routePlaytestWorkbookCsv": EXPORT_ROUTE_PLAYTEST_WORKBOOK_CSV_NAME,
            "choiceConsequence": EXPORT_CHOICE_CONSEQUENCE_JSON_NAME,
            "choiceConsequenceReport": EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME,
            "choiceConsequenceCsv": EXPORT_CHOICE_CONSEQUENCE_CSV_NAME,
            "variableInfluence": EXPORT_VARIABLE_INFLUENCE_JSON_NAME,
            "variableInfluenceReport": EXPORT_VARIABLE_INFLUENCE_REPORT_NAME,
            "variableInfluenceCsv": EXPORT_VARIABLE_INFLUENCE_CSV_NAME,
            "voiceProduction": EXPORT_VOICE_PRODUCTION_JSON_NAME,
            "voiceProductionReport": EXPORT_VOICE_PRODUCTION_REPORT_NAME,
            "voiceProductionCsv": EXPORT_VOICE_PRODUCTION_CSV_NAME,
            "storyRouteMap": EXPORT_STORY_ROUTE_MAP_JSON_NAME,
            "storyRouteMapReport": EXPORT_STORY_ROUTE_MAP_REPORT_NAME,
            "localizationAudit": EXPORT_LOCALIZATION_AUDIT_JSON_NAME,
            "localizationAuditReport": EXPORT_LOCALIZATION_AUDIT_REPORT_NAME,
            "releaseReadinessSummary": EXPORT_RELEASE_READINESS_JSON_NAME,
            "releaseReadinessReport": EXPORT_RELEASE_READINESS_REPORT_NAME,
            "unlockableContentManifest": UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME,
            "unlockableContentReport": UNLOCKABLE_CONTENT_REPORT_FILE_NAME,
            "iconPng": icon_files["pngFileName"],
            "iconIco": icon_files["icoFileName"],
            "launchSplash": splash_file["fileName"],
        },
    )
    manifest_path = write_export_manifest(build_dir, manifest)
    asset_rights_files = write_export_asset_rights_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    audio_cue_sheet_files = write_export_audio_cue_sheet_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    stage_direction_files = write_export_stage_direction_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    presentation_timeline_files = write_export_presentation_timeline_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    voice_production_files = write_export_voice_production_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    playtest_guide_path = write_export_playtest_guide_file(
        build_dir,
        project=bundle["project"],
        target_label="网页试玩包",
        release_version=release_version,
        launch_steps=launch_steps,
        manifest_name=manifest_path.name,
        unlockable_manifest_name=UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME,
        unlockable_report_name=UNLOCKABLE_CONTENT_REPORT_FILE_NAME,
        provenance_name=EXPORT_PROVENANCE_FILE_NAME,
        extra_reports=[
            EXPORT_RELEASE_EVIDENCE_PACK_NAME,
            asset_rights_files["assetRightsReportName"],
            audio_cue_sheet_files["audioCueSheetReportName"],
            stage_direction_files["stageDirectionReportName"],
            presentation_timeline_files["presentationTimelineReportName"],
            EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME,
            EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME,
            voice_production_files["voiceProductionReportName"],
            EXPORT_STORY_ROUTE_MAP_REPORT_NAME,
            EXPORT_LOCALIZATION_AUDIT_REPORT_NAME,
            EXPORT_RELEASE_READINESS_REPORT_NAME,
        ],
        runtime_notes=runtime_notes,
        missing_assets=missing_assets,
    )
    quality_reports = write_export_quality_report_bundle(
        build_dir,
        bundle=bundle,
        project=bundle["project"],
        manifest=manifest,
        missing_assets=missing_assets,
        unlockable_manifest=(export_payload.get("buildInfo") or {}).get("unlockableContentManifest"),
        base_report_files=[
            manifest_path.name,
            playtest_guide_path.name,
        ],
        extra_report_files=[
            UNLOCKABLE_CONTENT_REPORT_FILE_NAME,
            UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME,
            asset_rights_files["assetRightsReportName"],
            asset_rights_files["assetRightsName"],
            asset_rights_files["assetRightsCsvName"],
            audio_cue_sheet_files["audioCueSheetReportName"],
            audio_cue_sheet_files["audioCueSheetName"],
            audio_cue_sheet_files["audioCueSheetCsvName"],
            stage_direction_files["stageDirectionReportName"],
            stage_direction_files["stageDirectionName"],
            stage_direction_files["stageDirectionCsvName"],
            presentation_timeline_files["presentationTimelineReportName"],
            presentation_timeline_files["presentationTimelineName"],
            presentation_timeline_files["presentationTimelineCsvName"],
            EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME,
            EXPORT_ROUTE_PLAYTEST_WORKBOOK_JSON_NAME,
            EXPORT_ROUTE_PLAYTEST_WORKBOOK_CSV_NAME,
            EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME,
            EXPORT_CHOICE_CONSEQUENCE_JSON_NAME,
            EXPORT_CHOICE_CONSEQUENCE_CSV_NAME,
            EXPORT_VARIABLE_INFLUENCE_REPORT_NAME,
            EXPORT_VARIABLE_INFLUENCE_JSON_NAME,
            EXPORT_VARIABLE_INFLUENCE_CSV_NAME,
            voice_production_files["voiceProductionReportName"],
            voice_production_files["voiceProductionName"],
            voice_production_files["voiceProductionCsvName"],
        ],
        platform_notes=["网页试玩包适合快速传播；如果要正式上架，建议再导出桌面或原生 Runtime 包做目标系统验收。"],
    )
    story_route_map = quality_reports
    localization_audit = quality_reports
    release_readiness = quality_reports
    evidence_pack_path = write_export_release_evidence_pack_file(
        build_dir,
        project=bundle["project"],
        target_label="网页试玩包",
        release_version=release_version,
        manifest_name=manifest_path.name,
        playtest_guide_name=playtest_guide_path.name,
        provenance_name=EXPORT_PROVENANCE_FILE_NAME,
        story_route_map_report_name=story_route_map["storyRouteMapReportName"],
        localization_audit_report_name=localization_audit["localizationAuditReportName"],
        release_readiness_report_name=release_readiness["releaseReadinessReportName"],
        unlockable_report_name=UNLOCKABLE_CONTENT_REPORT_FILE_NAME,
        unlockable_manifest_name=UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME,
        launch_steps=launch_steps,
        runtime_notes=runtime_notes,
        extra_reports=[
            RUNTIME_PRELOAD_REPORT_FILE_NAME,
            asset_rights_files["assetRightsReportName"],
            audio_cue_sheet_files["audioCueSheetReportName"],
            stage_direction_files["stageDirectionReportName"],
            presentation_timeline_files["presentationTimelineReportName"],
            EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME,
            EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME,
            EXPORT_VARIABLE_INFLUENCE_REPORT_NAME,
            voice_production_files["voiceProductionReportName"],
        ],
        missing_assets=missing_assets,
    )
    provenance_verifiers = write_export_provenance_verifier_files(build_dir)
    provenance_file = write_export_provenance_file(build_dir, bundle, manifest)

    return {
        "target": EXPORT_TARGET_WEB,
        "targetLabel": "网页试玩包",
        "buildId": build_dir.name,
        "buildPath": str(build_dir),
        "indexPath": str(build_dir / "index.html"),
        "publicIndexUrl": f"/exports/{build_dir.name}/index.html",
        "manifestPath": str(manifest_path),
        "manifestPublicUrl": f"/exports/{build_dir.name}/{manifest_path.name}",
        "playtestGuidePath": str(playtest_guide_path),
        "playtestGuidePublicUrl": f"/exports/{build_dir.name}/{playtest_guide_path.name}",
        "releaseEvidencePackName": evidence_pack_path.name,
        "releaseEvidencePackPath": str(evidence_pack_path),
        "releaseEvidencePackPublicUrl": f"/exports/{build_dir.name}/{evidence_pack_path.name}",
        "assetRightsName": asset_rights_files["assetRightsName"],
        "assetRightsPath": asset_rights_files["assetRightsPath"],
        "assetRightsPublicUrl": f"/exports/{build_dir.name}/{asset_rights_files['assetRightsName']}",
        "assetRightsReportName": asset_rights_files["assetRightsReportName"],
        "assetRightsReportPath": asset_rights_files["assetRightsReportPath"],
        "assetRightsReportPublicUrl": f"/exports/{build_dir.name}/{asset_rights_files['assetRightsReportName']}",
        "assetRightsCsvName": asset_rights_files["assetRightsCsvName"],
        "assetRightsCsvPath": asset_rights_files["assetRightsCsvPath"],
        "assetRightsCsvPublicUrl": f"/exports/{build_dir.name}/{asset_rights_files['assetRightsCsvName']}",
        "assetRightsReadinessPercent": asset_rights_files["assetRightsReadinessPercent"],
        "assetRightsBlockerCount": asset_rights_files["assetRightsBlockerCount"],
        "assetRightsWarningCount": asset_rights_files["assetRightsWarningCount"],
        "audioCueSheetName": audio_cue_sheet_files["audioCueSheetName"],
        "audioCueSheetPath": audio_cue_sheet_files["audioCueSheetPath"],
        "audioCueSheetPublicUrl": f"/exports/{build_dir.name}/{audio_cue_sheet_files['audioCueSheetName']}",
        "audioCueSheetReportName": audio_cue_sheet_files["audioCueSheetReportName"],
        "audioCueSheetReportPath": audio_cue_sheet_files["audioCueSheetReportPath"],
        "audioCueSheetReportPublicUrl": f"/exports/{build_dir.name}/{audio_cue_sheet_files['audioCueSheetReportName']}",
        "audioCueSheetCsvName": audio_cue_sheet_files["audioCueSheetCsvName"],
        "audioCueSheetCsvPath": audio_cue_sheet_files["audioCueSheetCsvPath"],
        "audioCueSheetCsvPublicUrl": f"/exports/{build_dir.name}/{audio_cue_sheet_files['audioCueSheetCsvName']}",
        "audioCueSheetReadinessPercent": audio_cue_sheet_files["audioCueSheetReadinessPercent"],
        "audioCueSheetCueCount": audio_cue_sheet_files["audioCueSheetCueCount"],
        "audioCueSheetBlockerCount": audio_cue_sheet_files["audioCueSheetBlockerCount"],
        "audioCueSheetWarningCount": audio_cue_sheet_files["audioCueSheetWarningCount"],
        "stageDirectionName": stage_direction_files["stageDirectionName"],
        "stageDirectionPath": stage_direction_files["stageDirectionPath"],
        "stageDirectionPublicUrl": f"/exports/{build_dir.name}/{stage_direction_files['stageDirectionName']}",
        "stageDirectionReportName": stage_direction_files["stageDirectionReportName"],
        "stageDirectionReportPath": stage_direction_files["stageDirectionReportPath"],
        "stageDirectionReportPublicUrl": f"/exports/{build_dir.name}/{stage_direction_files['stageDirectionReportName']}",
        "stageDirectionCsvName": stage_direction_files["stageDirectionCsvName"],
        "stageDirectionCsvPath": stage_direction_files["stageDirectionCsvPath"],
        "stageDirectionCsvPublicUrl": f"/exports/{build_dir.name}/{stage_direction_files['stageDirectionCsvName']}",
        "stageDirectionReadinessPercent": stage_direction_files["stageDirectionReadinessPercent"],
        "stageDirectionEventCount": stage_direction_files["stageDirectionEventCount"],
        "stageDirectionBlockerCount": stage_direction_files["stageDirectionBlockerCount"],
        "stageDirectionWarningCount": stage_direction_files["stageDirectionWarningCount"],
        "presentationTimelineName": presentation_timeline_files["presentationTimelineName"],
        "presentationTimelinePath": presentation_timeline_files["presentationTimelinePath"],
        "presentationTimelinePublicUrl": f"/exports/{build_dir.name}/{presentation_timeline_files['presentationTimelineName']}",
        "presentationTimelineReportName": presentation_timeline_files["presentationTimelineReportName"],
        "presentationTimelineReportPath": presentation_timeline_files["presentationTimelineReportPath"],
        "presentationTimelineReportPublicUrl": f"/exports/{build_dir.name}/{presentation_timeline_files['presentationTimelineReportName']}",
        "presentationTimelineCsvName": presentation_timeline_files["presentationTimelineCsvName"],
        "presentationTimelineCsvPath": presentation_timeline_files["presentationTimelineCsvPath"],
        "presentationTimelineCsvPublicUrl": f"/exports/{build_dir.name}/{presentation_timeline_files['presentationTimelineCsvName']}",
        "presentationTimelineReadinessPercent": presentation_timeline_files["presentationTimelineReadinessPercent"],
        "presentationTimelineEventCount": presentation_timeline_files["presentationTimelineEventCount"],
        "presentationTimelineBlockerCount": presentation_timeline_files["presentationTimelineBlockerCount"],
        "presentationTimelineWarningCount": presentation_timeline_files["presentationTimelineWarningCount"],
        "routePlaytestWorkbookName": story_route_map["routePlaytestWorkbookName"],
        "routePlaytestWorkbookPath": story_route_map["routePlaytestWorkbookPath"],
        "routePlaytestWorkbookPublicUrl": f"/exports/{build_dir.name}/{story_route_map['routePlaytestWorkbookName']}",
        "routePlaytestWorkbookReportName": story_route_map["routePlaytestWorkbookReportName"],
        "routePlaytestWorkbookReportPath": story_route_map["routePlaytestWorkbookReportPath"],
        "routePlaytestWorkbookReportPublicUrl": f"/exports/{build_dir.name}/{story_route_map['routePlaytestWorkbookReportName']}",
        "routePlaytestWorkbookCsvName": story_route_map["routePlaytestWorkbookCsvName"],
        "routePlaytestWorkbookCsvPath": story_route_map["routePlaytestWorkbookCsvPath"],
        "routePlaytestWorkbookCsvPublicUrl": f"/exports/{build_dir.name}/{story_route_map['routePlaytestWorkbookCsvName']}",
        "routePlaytestReadinessPercent": story_route_map["routePlaytestReadinessPercent"],
        "routePlaytestRouteCaseCount": story_route_map["routePlaytestRouteCaseCount"],
        "routePlaytestEndingCaseCount": story_route_map["routePlaytestEndingCaseCount"],
        "routePlaytestBlockedCaseCount": story_route_map["routePlaytestBlockedCaseCount"],
        "choiceConsequenceName": story_route_map["choiceConsequenceName"],
        "choiceConsequencePath": story_route_map["choiceConsequencePath"],
        "choiceConsequencePublicUrl": f"/exports/{build_dir.name}/{story_route_map['choiceConsequenceName']}",
        "choiceConsequenceReportName": story_route_map["choiceConsequenceReportName"],
        "choiceConsequenceReportPath": story_route_map["choiceConsequenceReportPath"],
        "choiceConsequenceReportPublicUrl": f"/exports/{build_dir.name}/{story_route_map['choiceConsequenceReportName']}",
        "choiceConsequenceCsvName": story_route_map["choiceConsequenceCsvName"],
        "choiceConsequenceCsvPath": story_route_map["choiceConsequenceCsvPath"],
        "choiceConsequenceCsvPublicUrl": f"/exports/{build_dir.name}/{story_route_map['choiceConsequenceCsvName']}",
        "choiceConsequenceReadinessPercent": story_route_map["choiceConsequenceReadinessPercent"],
        "choiceConsequenceOptionCount": story_route_map["choiceConsequenceOptionCount"],
        "choiceConsequenceBlockerCount": story_route_map["choiceConsequenceBlockerCount"],
        "choiceConsequenceWarningCount": story_route_map["choiceConsequenceWarningCount"],
        "variableInfluenceName": story_route_map["variableInfluenceName"],
        "variableInfluencePath": story_route_map["variableInfluencePath"],
        "variableInfluencePublicUrl": f"/exports/{build_dir.name}/{story_route_map['variableInfluenceName']}",
        "variableInfluenceReportName": story_route_map["variableInfluenceReportName"],
        "variableInfluenceReportPath": story_route_map["variableInfluenceReportPath"],
        "variableInfluenceReportPublicUrl": f"/exports/{build_dir.name}/{story_route_map['variableInfluenceReportName']}",
        "variableInfluenceCsvName": story_route_map["variableInfluenceCsvName"],
        "variableInfluenceCsvPath": story_route_map["variableInfluenceCsvPath"],
        "variableInfluenceCsvPublicUrl": f"/exports/{build_dir.name}/{story_route_map['variableInfluenceCsvName']}",
        "variableInfluenceReadinessPercent": story_route_map["variableInfluenceReadinessPercent"],
        "variableInfluenceVariableCount": story_route_map["variableInfluenceVariableCount"],
        "variableInfluenceBlockerCount": story_route_map["variableInfluenceBlockerCount"],
        "variableInfluenceWarningCount": story_route_map["variableInfluenceWarningCount"],
        "voiceProductionName": voice_production_files["voiceProductionName"],
        "voiceProductionPath": voice_production_files["voiceProductionPath"],
        "voiceProductionPublicUrl": f"/exports/{build_dir.name}/{voice_production_files['voiceProductionName']}",
        "voiceProductionReportName": voice_production_files["voiceProductionReportName"],
        "voiceProductionReportPath": voice_production_files["voiceProductionReportPath"],
        "voiceProductionReportPublicUrl": f"/exports/{build_dir.name}/{voice_production_files['voiceProductionReportName']}",
        "voiceProductionCsvName": voice_production_files["voiceProductionCsvName"],
        "voiceProductionCsvPath": voice_production_files["voiceProductionCsvPath"],
        "voiceProductionCsvPublicUrl": f"/exports/{build_dir.name}/{voice_production_files['voiceProductionCsvName']}",
        "voiceProductionReadyPercent": voice_production_files["voiceProductionReadyPercent"],
        "voiceProductionLineCount": voice_production_files["voiceProductionLineCount"],
        "voiceProductionBlockerCount": voice_production_files["voiceProductionBlockerCount"],
        "voiceProductionWarningCount": voice_production_files["voiceProductionWarningCount"],
        "storyRouteMapName": story_route_map["storyRouteMapName"],
        "storyRouteMapPath": story_route_map["storyRouteMapPath"],
        "storyRouteMapPublicUrl": f"/exports/{build_dir.name}/{story_route_map['storyRouteMapName']}",
        "storyRouteMapReportName": story_route_map["storyRouteMapReportName"],
        "storyRouteMapReportPath": story_route_map["storyRouteMapReportPath"],
        "storyRouteMapReportPublicUrl": f"/exports/{build_dir.name}/{story_route_map['storyRouteMapReportName']}",
        "storyRouteMapStatus": story_route_map["storyRouteMapStatus"],
        "localizationAuditName": localization_audit["localizationAuditName"],
        "localizationAuditPath": localization_audit["localizationAuditPath"],
        "localizationAuditPublicUrl": f"/exports/{build_dir.name}/{localization_audit['localizationAuditName']}",
        "localizationAuditReportName": localization_audit["localizationAuditReportName"],
        "localizationAuditReportPath": localization_audit["localizationAuditReportPath"],
        "localizationAuditReportPublicUrl": f"/exports/{build_dir.name}/{localization_audit['localizationAuditReportName']}",
        "localizationAuditStatus": localization_audit["localizationAuditStatus"],
        "localizationAuditCompletionPercent": localization_audit["localizationAuditCompletionPercent"],
        "releaseReadinessSummaryName": release_readiness["releaseReadinessSummaryName"],
        "releaseReadinessSummaryPath": release_readiness["releaseReadinessSummaryPath"],
        "releaseReadinessSummaryPublicUrl": f"/exports/{build_dir.name}/{release_readiness['releaseReadinessSummaryName']}",
        "releaseReadinessReportName": release_readiness["releaseReadinessReportName"],
        "releaseReadinessReportPath": release_readiness["releaseReadinessReportPath"],
        "releaseReadinessReportPublicUrl": f"/exports/{build_dir.name}/{release_readiness['releaseReadinessReportName']}",
        "releaseReadinessStatus": release_readiness["releaseReadinessStatus"],
        "releaseReadinessScore": release_readiness["releaseReadinessScore"],
        "unlockableContentManifestPath": str(build_dir / UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME),
        "unlockableContentManifestPublicUrl": f"/exports/{build_dir.name}/{UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME}",
        "unlockableContentReportPath": str(build_dir / UNLOCKABLE_CONTENT_REPORT_FILE_NAME),
        "unlockableContentReportPublicUrl": f"/exports/{build_dir.name}/{UNLOCKABLE_CONTENT_REPORT_FILE_NAME}",
        "runtimePreloadManifestPath": str(build_dir / RUNTIME_PRELOAD_MANIFEST_FILE_NAME),
        "runtimePreloadManifestPublicUrl": f"/exports/{build_dir.name}/{RUNTIME_PRELOAD_MANIFEST_FILE_NAME}",
        "runtimePreloadReportPath": str(build_dir / RUNTIME_PRELOAD_REPORT_FILE_NAME),
        "runtimePreloadReportPublicUrl": f"/exports/{build_dir.name}/{RUNTIME_PRELOAD_REPORT_FILE_NAME}",
        "runtimePreloadSummary": (export_payload.get("buildInfo") or {}).get("runtimePreloadManifest", {}).get("summary", {}),
        "provenanceName": provenance_file["provenanceName"],
        "provenancePath": provenance_file["provenancePath"],
        "provenancePublicUrl": f"/exports/{build_dir.name}/{provenance_file['provenanceName']}",
        "provenanceSeal": provenance_file["provenanceSeal"],
        "provenanceSummary": provenance_file["provenanceSummary"],
        "provenanceVerifierName": provenance_verifiers["provenanceVerifierName"],
        "provenanceVerifierPath": provenance_verifiers["provenanceVerifierPath"],
        "provenanceVerifierPublicUrl": f"/exports/{build_dir.name}/{provenance_verifiers['provenanceVerifierName']}",
        "provenanceVerifierMacName": provenance_verifiers["provenanceVerifierMacName"],
        "provenanceVerifierMacPath": provenance_verifiers["provenanceVerifierMacPath"],
        "provenanceVerifierMacPublicUrl": f"/exports/{build_dir.name}/{provenance_verifiers['provenanceVerifierMacName']}",
        "provenanceVerifierLinuxName": provenance_verifiers["provenanceVerifierLinuxName"],
        "provenanceVerifierLinuxPath": provenance_verifiers["provenanceVerifierLinuxPath"],
        "provenanceVerifierLinuxPublicUrl": f"/exports/{build_dir.name}/{provenance_verifiers['provenanceVerifierLinuxName']}",
        "provenanceVerifierWindowsName": provenance_verifiers["provenanceVerifierWindowsName"],
        "provenanceVerifierWindowsPath": provenance_verifiers["provenanceVerifierWindowsPath"],
        "provenanceVerifierWindowsPublicUrl": f"/exports/{build_dir.name}/{provenance_verifiers['provenanceVerifierWindowsName']}",
        "releaseVersion": release_version,
        "iconPngPath": str(icon_files["pngPath"]),
        "iconIcoPath": str(icon_files["icoPath"]),
        "iconPngPublicUrl": f"/exports/{build_dir.name}/{icon_files['pngFileName']}",
        "iconIcoPublicUrl": f"/exports/{build_dir.name}/{icon_files['icoFileName']}",
        "splashPath": str(splash_file["path"]),
        "splashPublicUrl": f"/exports/{build_dir.name}/{splash_file['fileName']}",
        "copiedAssets": copied_assets,
        "missingAssets": len(missing_assets),
        "missingAssetNames": [asset.get("name") or asset.get("id") or "未命名素材" for asset in missing_assets[:5]],
    }


def export_renpy_draft_build() -> dict:
    build_dir = create_export_build_dir("renpy_draft_build")
    bundle = load_project_bundle()
    game_dir = build_dir / "game"
    export_assets_doc, copied_assets, missing_assets = copy_assets_for_export(bundle["assets"], game_dir)
    renpy_files = write_renpy_starter_project(build_dir, bundle, export_assets_doc)
    manifest = build_export_manifest(
        bundle,
        target=EXPORT_TARGET_RENPY_DRAFT,
        target_label="Ren'Py Starter Bundle",
        build_id=build_dir.name,
        copied_assets=copied_assets,
        missing_assets=missing_assets,
        extra_files={
            "renpyScript": renpy_files["scriptName"],
            "renpyOptions": renpy_files["optionsName"],
            "renpyScreens": renpy_files["screensName"],
            "renpyManifest": renpy_files["manifestName"],
            "renpyReviewNotes": renpy_files["reviewName"],
            "renpyQualityReport": renpy_files["qualityReportName"],
            "renpyQualityMarkdown": renpy_files["qualityMarkdownName"],
            "renpyVerifier": renpy_files["verifierName"],
            "readme": renpy_files["readmeName"],
        },
        runtime_info={
            "mode": "renpy_starter_bundle",
            "modeLabel": "Ren'Py Starter Bundle",
            "warning": "这是迁移友好的 Ren'Py 起始包；自定义演出、复杂变量逻辑和 UI 仍需在 Ren'Py 中复核。",
            "script": renpy_files["scriptName"],
            "screens": renpy_files["screensName"],
            "reviewNotes": renpy_files["reviewName"],
            "reviewItemCount": renpy_files["warningCount"],
            "qualityStatus": renpy_files["qualityStatus"],
            "qualitySummary": renpy_files["qualitySummary"],
            "verifier": renpy_files["verifierName"],
        },
    )
    manifest_path = write_export_manifest(build_dir, manifest)
    provenance_file = write_export_provenance_file(build_dir, bundle, manifest)
    archive_path = Path(shutil.make_archive(str(build_dir), "zip", root_dir=build_dir))
    archive_checksum = write_export_archive_checksum_files(archive_path, "Ren'Py Starter Bundle")

    return {
        "target": EXPORT_TARGET_RENPY_DRAFT,
        "targetLabel": "Ren'Py Starter Bundle",
        "buildId": build_dir.name,
        "buildPath": str(build_dir),
        "archivePath": str(archive_path),
        "archiveName": archive_path.name,
        "archivePublicUrl": f"/exports/{archive_path.name}",
        "archiveSha256": archive_checksum["archiveSha256"],
        "archiveSizeBytes": archive_checksum["archiveSizeBytes"],
        "archiveSizeLabel": archive_checksum["archiveSizeLabel"],
        "archiveChecksumName": archive_checksum["archiveChecksumName"],
        "archiveChecksumPath": archive_checksum["archiveChecksumPath"],
        "archiveChecksumPublicUrl": f"/exports/{archive_checksum['archiveChecksumName']}",
        "archiveChecksumJsonName": archive_checksum["archiveChecksumJsonName"],
        "archiveChecksumJsonPath": archive_checksum["archiveChecksumJsonPath"],
        "archiveChecksumJsonPublicUrl": f"/exports/{archive_checksum['archiveChecksumJsonName']}",
        "manifestPath": str(manifest_path),
        "manifestPublicUrl": f"/exports/{build_dir.name}/{manifest_path.name}",
        "renpyScriptName": renpy_files["scriptName"],
        "renpyScriptPath": renpy_files["scriptPath"],
        "renpyScriptPublicUrl": f"/exports/{build_dir.name}/{renpy_files['scriptName']}",
        "renpyOptionsName": renpy_files["optionsName"],
        "renpyOptionsPath": renpy_files["optionsPath"],
        "renpyOptionsPublicUrl": f"/exports/{build_dir.name}/{renpy_files['optionsName']}",
        "renpyScreensName": renpy_files["screensName"],
        "renpyScreensPath": renpy_files["screensPath"],
        "renpyScreensPublicUrl": f"/exports/{build_dir.name}/{renpy_files['screensName']}",
        "renpyManifestName": renpy_files["manifestName"],
        "renpyManifestPath": renpy_files["manifestPath"],
        "renpyManifestPublicUrl": f"/exports/{build_dir.name}/{renpy_files['manifestName']}",
        "renpyReviewName": renpy_files["reviewName"],
        "renpyReviewPath": renpy_files["reviewPath"],
        "renpyReviewPublicUrl": f"/exports/{build_dir.name}/{renpy_files['reviewName']}",
        "renpyQualityReportName": renpy_files["qualityReportName"],
        "renpyQualityReportPath": renpy_files["qualityReportPath"],
        "renpyQualityReportPublicUrl": f"/exports/{build_dir.name}/{renpy_files['qualityReportName']}",
        "renpyQualityMarkdownName": renpy_files["qualityMarkdownName"],
        "renpyQualityMarkdownPath": renpy_files["qualityMarkdownPath"],
        "renpyQualityMarkdownPublicUrl": f"/exports/{build_dir.name}/{renpy_files['qualityMarkdownName']}",
        "renpyVerifierName": renpy_files["verifierName"],
        "renpyVerifierPath": renpy_files["verifierPath"],
        "renpyVerifierPublicUrl": f"/exports/{build_dir.name}/{renpy_files['verifierName']}",
        "renpyQualityStatus": renpy_files["qualityStatus"],
        "renpyQualitySummary": renpy_files["qualitySummary"],
        "renpyReadmeName": renpy_files["readmeName"],
        "renpyReadmePath": renpy_files["readmePath"],
        "renpyReadmePublicUrl": f"/exports/{build_dir.name}/{renpy_files['readmeName']}",
        "renpyReviewItemCount": renpy_files["warningCount"],
        "renpySceneCount": renpy_files["sceneCount"],
        "renpyCharacterCount": renpy_files["characterCount"],
        "renpyVariableCount": renpy_files["variableCount"],
        "renpyAssetDefinitionCount": renpy_files["assetDefinitionCount"],
        "provenanceName": provenance_file["provenanceName"],
        "provenancePath": provenance_file["provenancePath"],
        "provenancePublicUrl": f"/exports/{build_dir.name}/{provenance_file['provenanceName']}",
        "provenanceSeal": provenance_file["provenanceSeal"],
        "releaseVersion": get_export_release_version(bundle["project"]),
        "copiedAssets": copied_assets,
        "missingAssets": len(missing_assets),
        "missingAssetNames": [asset.get("name") or asset.get("id") or "未命名素材" for asset in missing_assets[:5]],
    }


def ensure_export_runtime_cache_dir() -> Path:
    EXPORT_RUNTIME_CACHE_DIR.mkdir(exist_ok=True)
    return EXPORT_RUNTIME_CACHE_DIR


def download_remote_file(url: str, target_path: Path) -> None:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 CanvasiaEngine/1.0"})
    with urlopen(request) as response, target_path.open("wb") as output:
        shutil.copyfileobj(response, output)


def get_nwjs_macos_arch() -> str:
    override = str(os.environ.get("CANVASIA_NWJS_MACOS_ARCH") or "").strip().lower()
    if override in {"arm64", "x64"}:
        return override
    machine = platform.machine().lower()
    return "arm64" if machine in {"arm64", "aarch64"} else "x64"


def get_nwjs_runtime_config(platform_key: str) -> dict:
    config = dict(NWJS_GAME_RUNTIME_PLATFORM_CONFIG[platform_key])
    if platform_key == NWJS_GAME_PLATFORM_MACOS:
        macos_arch = get_nwjs_macos_arch()
        archive_name = f"nwjs-{NWJS_RUNTIME_VERSION}-osx-{macos_arch}.zip"
        config["archiveName"] = archive_name
        config["runtimeCacheSuffix"] = f"osx_{macos_arch}"
        config["archLabel"] = "Apple Silicon" if macos_arch == "arm64" else "Intel"
    return config


def get_nwjs_runtime_archive_name(platform_key: str) -> str:
    return str(get_nwjs_runtime_config(platform_key).get("archiveName") or "")


def get_nwjs_runtime_download_url(platform_key: str) -> str:
    archive_name = get_nwjs_runtime_archive_name(platform_key)
    return f"https://dl.nwjs.io/{NWJS_RUNTIME_VERSION}/{archive_name}"


def get_nwjs_runtime_cache_dir(platform_key: str) -> Path:
    config = get_nwjs_runtime_config(platform_key)
    return ensure_export_runtime_cache_dir() / f"nwjs_{NWJS_RUNTIME_VERSION}_{config['runtimeCacheSuffix']}"


def get_nwjs_runtime_dir_override_env_var(platform_key: str) -> str:
    return f"CANVASIA_NWJS_RUNTIME_DIR_{platform_key.upper()}"


def get_nwjs_runtime_archive_override_env_var(platform_key: str) -> str:
    return f"CANVASIA_NWJS_RUNTIME_ARCHIVE_{platform_key.upper()}"


def strip_archive_extensions(name: str) -> str:
    for suffix in (".tar.gz", ".zip", ".tgz", ".tar.xz", ".tar"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return Path(name).stem


def get_nwjs_local_runtime_dirs(platform_key: str) -> list[Path]:
    config = get_nwjs_runtime_config(platform_key)
    local_dirs: list[Path] = []
    for base_dir in LOCAL_NWJS_RUNTIME_DIRS:
        if base_dir not in local_dirs:
            local_dirs.append(base_dir)
    for subdir_name in config.get("localRuntimeDirs") or []:
        candidate = ROOT_DIR / "desktop_runtime" / str(subdir_name)
        if candidate not in local_dirs:
            local_dirs.append(candidate)
    return local_dirs


def ensure_local_nwjs_runtime_dropin_guide() -> Path:
    guide_dir = ROOT_DIR / "desktop_runtime"
    guide_dir.mkdir(parents=True, exist_ok=True)
    guide_path = guide_dir / LOCAL_NWJS_RUNTIME_GUIDE_NAME
    lines = [
        "Canvasia Engine · NW.js 本地运行壳投放说明",
        "",
        "如果你想在外网受限的环境里导出真正的原生桌面包，可以把 NW.js 运行壳手动放到这里。",
        "",
        "当前支持这些运行壳：",
        f"- Windows：{get_nwjs_runtime_archive_name(NWJS_GAME_PLATFORM_WINDOWS)}",
        f"- macOS：{get_nwjs_runtime_archive_name(NWJS_GAME_PLATFORM_MACOS)}",
        f"- Linux：{get_nwjs_runtime_archive_name(NWJS_GAME_PLATFORM_LINUX)}",
        "",
        "支持这几种放法：",
        "1. 直接把压缩包放进 desktop_runtime/ 或对应平台子目录（windows / macos / linux）",
        "2. 解压成目录后放进去",
        "3. 或者用环境变量指定：CANVASIA_NWJS_RUNTIME_DIR_<PLATFORM> / CANVASIA_NWJS_RUNTIME_ARCHIVE_<PLATFORM>",
        "   例如：CANVASIA_NWJS_RUNTIME_DIR_WINDOWS、CANVASIA_NWJS_RUNTIME_ARCHIVE_MACOS",
        "",
        "编辑器下次导出桌面包时，会先找这里的本地运行壳，再尝试联网下载。",
    ]
    guide_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return guide_path


def describe_nwjs_runtime_requirements(platform_key: str) -> str:
    config = get_nwjs_runtime_config(platform_key)
    required_files = " / ".join(config.get("requiredFiles") or [])
    required_dirs = " / ".join(config.get("requiredDirs") or [])
    return f"至少要包含这些文件：{required_files}；以及这些目录：{required_dirs}"


def find_nwjs_macos_app_bundle(runtime_dir: Path) -> Path | None:
    if runtime_dir.name.endswith(".app"):
        return runtime_dir
    direct_bundle = runtime_dir / "nwjs.app"
    if direct_bundle.is_dir():
        return direct_bundle
    first_bundle = next((item for item in runtime_dir.glob("*.app") if item.is_dir()), None)
    return first_bundle


def normalize_nwjs_runtime_dir(platform_key: str, runtime_dir: Path) -> Path:
    if platform_key == NWJS_GAME_PLATFORM_MACOS and runtime_dir.name.endswith(".app"):
        return runtime_dir.parent
    return runtime_dir


def validate_nwjs_runtime_dir(platform_key: str, runtime_dir: Path) -> list[str]:
    runtime_root = normalize_nwjs_runtime_dir(platform_key, runtime_dir)
    config = get_nwjs_runtime_config(platform_key)
    missing_items: list[str] = []

    if platform_key == NWJS_GAME_PLATFORM_MACOS:
        app_bundle = find_nwjs_macos_app_bundle(runtime_root)
        if app_bundle is None:
            return [str(config.get("appBundleName") or "nwjs.app")]
        for file_name in config.get("requiredFiles") or []:
            if not (app_bundle / file_name).is_file():
                missing_items.append(f"{app_bundle.name}/{file_name}")
        for dir_name in config.get("requiredDirs") or []:
            if not (app_bundle / dir_name).is_dir():
                missing_items.append(f"{app_bundle.name}/{dir_name}/")
        return missing_items

    for file_name in config.get("requiredFiles") or []:
        if not (runtime_root / file_name).is_file():
            missing_items.append(file_name)
    for dir_name in config.get("requiredDirs") or []:
        if not (runtime_root / dir_name).is_dir():
            missing_items.append(f"{dir_name}/")
    return missing_items


def copytree_with_symlinks(source: Path, target: Path) -> None:
    shutil.copytree(source, target, dirs_exist_ok=True, symlinks=True)


def extract_nwjs_runtime_archive(platform_key: str, archive_path: Path, runtime_dir: Path) -> None:
    if runtime_dir.exists():
        shutil.rmtree(runtime_dir, ignore_errors=True)
    runtime_dir.mkdir(parents=True, exist_ok=True)

    try:
        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            archive_name = archive_path.name.lower()
            if archive_name.endswith(".zip"):
                extracted = False
                for command in (
                    ["ditto", "-x", "-k", str(archive_path), str(temp_dir)],
                    ["unzip", "-q", str(archive_path), "-d", str(temp_dir)],
                ):
                    try:
                        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        extracted = True
                        break
                    except (FileNotFoundError, subprocess.CalledProcessError):
                        continue
                if not extracted:
                    with zipfile.ZipFile(archive_path, "r") as zip_file:
                        zip_file.extractall(temp_dir)
            else:
                extracted = False
                try:
                    subprocess.run(
                        ["tar", "-xf", str(archive_path), "-C", str(temp_dir)],
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    extracted = True
                except (FileNotFoundError, subprocess.CalledProcessError):
                    pass
                if not extracted:
                    with tarfile.open(archive_path, "r:*") as archive:
                        try:
                            archive.extractall(temp_dir, filter="data")
                        except (TypeError, OSError):
                            archive.extractall(temp_dir)

            extracted_entries = [entry for entry in temp_dir.iterdir() if entry.name != "__MACOSX"]
            if (
                len(extracted_entries) == 1
                and extracted_entries[0].is_dir()
                and not (platform_key == NWJS_GAME_PLATFORM_MACOS and extracted_entries[0].name.endswith(".app"))
            ):
                source_root = extracted_entries[0]
            else:
                source_root = temp_dir
            for item in source_root.iterdir():
                target_path = runtime_dir / item.name
                if item.is_dir():
                    copytree_with_symlinks(item, target_path)
                else:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target_path)
    except Exception as error:
        raise ValueError(f"解压 {get_nwjs_runtime_config(platform_key)['label']} 桌面运行壳失败：{error}") from error

    missing_items = validate_nwjs_runtime_dir(platform_key, runtime_dir)
    if missing_items:
        raise ValueError(
            f"{get_nwjs_runtime_config(platform_key)['label']} 桌面运行壳缺少这些关键文件或目录："
            + " / ".join(missing_items)
            + "。"
            + describe_nwjs_runtime_requirements(platform_key)
        )


def resolve_nwjs_runtime_dir_override(platform_key: str) -> Path | None:
    env_var_names = [get_nwjs_runtime_dir_override_env_var(platform_key)]
    if platform_key == NWJS_GAME_PLATFORM_WINDOWS:
        env_var_names.append("CANVASIA_NWJS_RUNTIME_DIR")
    for env_var_name in env_var_names:
        env_value = str(os.environ.get(env_var_name) or "").strip()
        if env_value:
            candidate = Path(env_value).expanduser()
            if candidate.exists():
                return candidate
    return None


def resolve_nwjs_runtime_archive_override(platform_key: str) -> Path | None:
    env_var_names = [get_nwjs_runtime_archive_override_env_var(platform_key)]
    if platform_key == NWJS_GAME_PLATFORM_WINDOWS:
        env_var_names.append("CANVASIA_NWJS_RUNTIME_ZIP")
    for env_var_name in env_var_names:
        env_value = str(os.environ.get(env_var_name) or "").strip()
        if env_value:
            candidate = Path(env_value).expanduser()
            if candidate.is_file():
                return candidate
    return None


def resolve_local_nwjs_runtime_source(platform_key: str, cache_dir: Path) -> tuple[str, Path, str] | None:
    runtime_dir = cache_dir / "runtime"
    if runtime_dir.is_dir() and not validate_nwjs_runtime_dir(platform_key, runtime_dir):
        return "runtime_dir", runtime_dir, "本地缓存的 NW.js 运行壳"

    archive_path = cache_dir / get_nwjs_runtime_archive_name(platform_key)
    if archive_path.is_file():
        return "archive", archive_path, "你手动放进缓存目录的 NW.js 压缩包"

    env_runtime_dir = resolve_nwjs_runtime_dir_override(platform_key)
    if env_runtime_dir and env_runtime_dir.exists():
        return "runtime_dir", env_runtime_dir, "环境变量指定的 NW.js 目录"

    env_runtime_archive = resolve_nwjs_runtime_archive_override(platform_key)
    if env_runtime_archive:
        return "archive", env_runtime_archive, "环境变量指定的 NW.js 压缩包"

    candidate_names = [
        get_nwjs_runtime_archive_name(platform_key),
        strip_archive_extensions(get_nwjs_runtime_archive_name(platform_key)),
        *(["nwjs.app"] if platform_key == NWJS_GAME_PLATFORM_MACOS else []),
    ]
    for base_dir in get_nwjs_local_runtime_dirs(platform_key):
        for candidate_name in candidate_names:
            candidate_path = base_dir / candidate_name
            if candidate_path.is_dir() and not validate_nwjs_runtime_dir(platform_key, candidate_path):
                return "runtime_dir", candidate_path, "项目目录里手动放入的 NW.js 目录"
            if candidate_path.is_file():
                return "archive", candidate_path, "项目目录里手动放入的 NW.js 压缩包"

    return None


def ensure_nwjs_runtime(platform_key: str) -> tuple[Path, bool, str, str]:
    config = get_nwjs_runtime_config(platform_key)
    cache_dir = get_nwjs_runtime_cache_dir(platform_key)
    runtime_dir = cache_dir / "runtime"
    cache_dir.mkdir(parents=True, exist_ok=True)

    local_source = resolve_local_nwjs_runtime_source(platform_key, cache_dir)
    if local_source:
        source_type, source_path, source_label = local_source
        if source_type == "runtime_dir":
            missing_items = validate_nwjs_runtime_dir(platform_key, source_path)
            if missing_items:
                raise ValueError(
                    "本地 NW.js 运行壳不完整，缺少这些关键文件或目录："
                    + " / ".join(missing_items)
                    + "。"
                    + f"可参考 {ROOT_DIR / 'desktop_runtime' / LOCAL_NWJS_RUNTIME_GUIDE_NAME}。"
                )
            return normalize_nwjs_runtime_dir(platform_key, source_path), False, source_label, str(source_path)
        extract_nwjs_runtime_archive(platform_key, source_path, runtime_dir)
        return runtime_dir, False, source_label, str(source_path)

    archive_path = cache_dir / get_nwjs_runtime_archive_name(platform_key)

    try:
        download_remote_file(get_nwjs_runtime_download_url(platform_key), archive_path)
    except Exception as error:
        raise ValueError(f"下载 {config['label']} 桌面运行壳失败：{error}") from error

    extract_nwjs_runtime_archive(platform_key, archive_path, runtime_dir)
    return runtime_dir, True, "这次自动下载的 NW.js 运行壳", str(archive_path)


def build_nwjs_package_json(project: dict, target_label: str, icon_path: str | None = None) -> dict:
    resolution = project.get("resolution") or {"width": 1280, "height": 720}
    return {
        "name": sanitize_export_filename(project.get("projectId") or project.get("title") or "canvasia_game"),
        "version": get_export_release_version(project),
        "description": f"{project.get('title') or 'Canvasia Engine Game'} {target_label}",
        "main": "index.html",
        "window": {
            "title": project.get("title") or "Canvasia Engine Game",
            "width": int(resolution.get("width", 1280)),
            "height": int(resolution.get("height", 720)),
            "position": "center",
            "resizable": False,
            "toolbar": False,
            "fullscreen": False,
            "icon": icon_path or "app_icon.png",
        },
        "chromium-args": "--disable-features=Translate",
    }


def create_package_nw_archive(app_dir: Path, package_path: Path) -> None:
    with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(app_dir.rglob("*")):
            if path.is_dir():
                continue
            archive.write(path, path.relative_to(app_dir).as_posix())


def build_nwjs_single_file_executable(runtime_executable: Path, package_path: Path, output_path: Path) -> None:
    if output_path.exists():
        output_path.unlink()

    with runtime_executable.open("rb") as runtime_file, package_path.open("rb") as package_file, output_path.open("wb") as output:
        shutil.copyfileobj(runtime_file, output)
        shutil.copyfileobj(package_file, output)


def sanitize_bundle_identifier_fragment(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", value or "").strip("-").lower()
    return cleaned or "game"


def build_game_bundle_identifier(project: dict) -> str:
    fragment = sanitize_bundle_identifier_fragment(project.get("projectId") or project.get("title") or "game")
    return f"com.canvasia.engine.game.{fragment}"


def build_macos_app_bundle_name(project: dict) -> str:
    safe_name = re.sub(r'[\\/:*?"<>|]+', " ", str(project.get("title") or "Canvasia Engine Game")).strip()
    return f"{safe_name or 'Canvasia Engine Game'}.app"


def build_macos_executable_name(project: dict) -> str:
    return sanitize_export_filename(project.get("projectId") or project.get("title") or "CanvasiaGame")


def customize_macos_nwjs_app_bundle(app_bundle_path: Path, project: dict, release_version: str) -> str:
    info_plist_path = app_bundle_path / "Contents" / "Info.plist"
    executable_dir = app_bundle_path / "Contents" / "MacOS"
    if not info_plist_path.is_file():
        raise ValueError("macOS 运行壳缺少 Contents/Info.plist。")

    with info_plist_path.open("rb") as plist_file:
        info_plist = plistlib.load(plist_file)

    old_executable_name = str(info_plist.get("CFBundleExecutable") or "nwjs")
    new_executable_name = build_macos_executable_name(project)
    old_executable_path = executable_dir / old_executable_name
    new_executable_path = executable_dir / new_executable_name

    if old_executable_path.is_file() and old_executable_name != new_executable_name:
        old_executable_path.rename(new_executable_path)
    elif old_executable_path.is_file():
        new_executable_path = old_executable_path

    if not new_executable_path.is_file():
        raise ValueError("macOS 运行壳缺少可执行文件。")
    new_executable_path.chmod(0o755)

    project_title = str(project.get("title") or "Canvasia Engine Game").strip() or "Canvasia Engine Game"
    info_plist["CFBundleDisplayName"] = project_title
    info_plist["CFBundleName"] = project_title
    info_plist["CFBundleExecutable"] = new_executable_name
    info_plist["CFBundleIdentifier"] = build_game_bundle_identifier(project)
    info_plist["CFBundleShortVersionString"] = release_version
    info_plist["CFBundleVersion"] = release_version

    with info_plist_path.open("wb") as plist_file:
        plistlib.dump(info_plist, plist_file)

    return new_executable_name


def build_macos_start_helper_script(app_bundle_name: str) -> str:
    return f"""#!/bin/zsh
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_PATH="$SCRIPT_DIR/{app_bundle_name}"

if [ ! -d "$APP_PATH" ]; then
  echo "没有找到应用包：$APP_PATH"
  read -r -n 1 -s -p "按任意键关闭..."
  echo
  exit 1
fi

open "$APP_PATH"
"""


def write_macos_start_helper(build_dir: Path, app_bundle_name: str) -> Path:
    helper_path = build_dir / "启动游戏.command"
    helper_path.write_text(build_macos_start_helper_script(app_bundle_name), encoding="utf-8")
    helper_path.chmod(0o755)
    return helper_path


def build_linux_start_helper_script(target_name: str) -> str:
    return f"""#!/bin/sh
set -eu
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GAME_TARGET="$SCRIPT_DIR/{target_name}"

if [ ! -f "$GAME_TARGET" ]; then
  echo "没有找到启动文件：$GAME_TARGET"
  exit 1
fi

chmod +x "$GAME_TARGET"
exec "$GAME_TARGET"
"""


def write_linux_start_helper(build_dir: Path, target_name: str) -> Path:
    helper_path = build_dir / "启动游戏.sh"
    helper_path.write_text(build_linux_start_helper_script(target_name), encoding="utf-8")
    helper_path.chmod(0o755)
    return helper_path


def write_macos_package_readme(
    build_dir: Path,
    app_bundle_name: str,
    start_helper_name: str,
    runtime_downloaded: bool,
    runtime_source_label: str,
    manifest_name: str,
    release_version: str,
) -> Path:
    readme_path = build_dir / "README_先看这里.txt"
    lines = [
        "Canvasia Engine macOS 桌面发布包",
        "",
        f"1. 优先双击 {start_helper_name}；也可以直接打开 {app_bundle_name}。",
        "2. 对外分发时，建议把整个文件夹一起打包，不要只拿出 .app 单独发。",
        "3. 应用包里已经内嵌了 Runtime、试玩页面和素材文件。",
        f"4. {manifest_name} 里记录了这次导出的版本、素材缺口和运行壳信息。",
        "",
        f"当前发布版本：{release_version}",
    ]
    lines.append("")
    if runtime_downloaded:
        lines.append(f"这次导出时已经自动下载并缓存了 macOS 运行壳：NW.js {NWJS_RUNTIME_VERSION}")
    else:
        lines.append(f"这次桌面包直接使用了本地 NW.js 运行壳：{runtime_source_label or '已使用本地或缓存运行壳'}")
    readme_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return readme_path


def write_linux_package_readme(
    build_dir: Path,
    executable_name: str,
    start_helper_name: str,
    runtime_downloaded: bool,
    runtime_source_label: str,
    manifest_name: str,
    release_version: str,
) -> Path:
    readme_path = build_dir / "README_先看这里.txt"
    lines = [
        "Canvasia Engine Linux 桌面发布包",
        "",
        f"1. 优先双击 {start_helper_name}；也可以直接运行 ./{executable_name}。",
        "2. 如果当前文件没有可执行权限，可以先执行：chmod +x 启动游戏.sh",
        "3. app/assets 文件夹里是已经复制进来的素材文件。",
        f"4. {manifest_name} 里记录了这次导出的版本、素材缺口和运行壳信息。",
        "",
        f"当前发布版本：{release_version}",
    ]
    lines.append("")
    if runtime_downloaded:
        lines.append(f"这次导出时已经自动下载并缓存了 Linux 运行壳：NW.js {NWJS_RUNTIME_VERSION}")
    else:
        lines.append(f"这次桌面包直接使用了本地 NW.js 运行壳：{runtime_source_label or '已使用本地或缓存运行壳'}")
    readme_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return readme_path


def write_windows_package_readme(
    build_dir: Path,
    executable_name: str,
    runtime_mode: str,
    package_mode_label: str,
    runtime_downloaded: bool,
    runtime_source_label: str,
    manifest_name: str,
    release_version: str,
) -> Path:
    readme_path = build_dir / "README_先看这里.txt"
    lines = [
        "Canvasia Engine Windows 桌面发布包",
        "",
        f"1. 优先双击 启动游戏.cmd；也可以直接双击 {executable_name}。",
        "2. 对外分发时，建议把整个文件夹一起打包，不要只拿出 exe 单独发。",
        "3. app/assets 文件夹里是已经复制进来的素材文件。",
        f"4. {manifest_name} 里记录了这次导出的版本、素材缺口和桌面模式。",
        "5. app_icon.png / app_icon.ico 是这次自动生成的桌面图标文件。",
        "",
        f"当前发布版本：{release_version}",
        f"当前打包方式：{package_mode_label}",
        "",
        "这是一份文件夹版桌面包。",
    ]
    if runtime_mode == "nwjs" and runtime_downloaded:
        lines.append("")
        lines.append(f"这次导出时已经自动下载并缓存了 Windows 运行壳：NW.js {NWJS_RUNTIME_VERSION}")
    elif runtime_mode == "nwjs":
        lines.append("")
        lines.append(
            f"这次桌面包直接使用了本地 NW.js 运行壳：{runtime_source_label or '已使用本地或缓存运行壳'}"
        )
    else:
        lines.append("")
        lines.append("如果当前这份包是 .cmd 启动器版，它会优先尝试调用 Windows 自带的 Edge 或本机的 Chrome。")
    readme_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return readme_path


def build_windows_browser_launcher_script(project_title: str) -> str:
    safe_title = project_title or "Canvasia Engine Game"
    return f"""@echo off
setlocal
set "GAME_DIR=%~dp0app"
set "GAME_INDEX=%GAME_DIR%\\index.html"
set "GAME_TITLE={safe_title}"

if not exist "%GAME_INDEX%" (
  echo 没有找到试玩入口：%GAME_INDEX%
  pause
  exit /b 1
)

set "EDGE_EXE=%ProgramFiles(x86)%\\Microsoft\\Edge\\Application\\msedge.exe"
if exist "%EDGE_EXE%" goto launch_browser
set "EDGE_EXE=%ProgramFiles%\\Microsoft\\Edge\\Application\\msedge.exe"
if exist "%EDGE_EXE%" goto launch_browser

set "EDGE_EXE=%ProgramFiles(x86)%\\Google\\Chrome\\Application\\chrome.exe"
if exist "%EDGE_EXE%" goto launch_browser
set "EDGE_EXE=%ProgramFiles%\\Google\\Chrome\\Application\\chrome.exe"
if exist "%EDGE_EXE%" goto launch_browser

echo 没有找到 Edge 或 Chrome，改用系统默认浏览器打开。
start "" "%GAME_INDEX%"
exit /b 0

:launch_browser
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$p=(Resolve-Path '%GAME_INDEX%').Path; $u=([System.Uri]$p).AbsoluteUri; Start-Process '%EDGE_EXE%' -ArgumentList @('--app=' + $u, '--disable-pinch', '--overscroll-history-navigation=0')"
exit /b 0
"""


def write_windows_browser_launcher(build_dir: Path, project: dict) -> Path:
    launcher_name = sanitize_export_filename(project.get("title") or "") or ""
    if launcher_name in {"", "asset"}:
        launcher_name = sanitize_export_filename(project.get("projectId") or "") or "CanvasiaGame"
    launcher_path = build_dir / f"{launcher_name}.cmd"
    launcher_path.write_text(build_windows_browser_launcher_script(project.get("title") or "Canvasia Engine Game"), encoding="utf-8")
    return launcher_path


def build_windows_start_helper_script(target_name: str) -> str:
    return f"""@echo off
setlocal
set "GAME_TARGET=%~dp0{target_name}"

if not exist "%GAME_TARGET%" (
  echo 没有找到启动文件：%GAME_TARGET%
  pause
  exit /b 1
)

start "" "%GAME_TARGET%"
exit /b 0
"""


def write_windows_start_helper(build_dir: Path, target_name: str) -> Path:
    helper_path = build_dir / "启动游戏.cmd"
    helper_path.write_text(build_windows_start_helper_script(target_name), encoding="utf-8")
    return helper_path


def export_windows_nwjs_build() -> dict:
    build_dir = create_export_build_dir("windows_build")
    bundle = load_project_bundle()
    runtime_guide_path = ensure_local_nwjs_runtime_dropin_guide()
    app_dir = build_dir / "app"
    app_dir.mkdir(parents=True, exist_ok=True)
    export_assets_doc, copied_assets, missing_assets = copy_assets_for_export(bundle["assets"], app_dir)
    export_payload = build_export_payload(bundle, export_assets_doc, copied_assets, missing_assets)
    release_version = get_export_release_version(bundle["project"])
    splash_file = write_export_splash_asset(app_dir, bundle["project"], release_version, "Canvasia Engine Windows 桌面发布包")
    root_splash_file = write_export_splash_asset(build_dir, bundle["project"], release_version, "Canvasia Engine Windows 桌面发布包")
    export_payload["buildInfo"]["releaseVersion"] = release_version
    export_payload["buildInfo"]["exportTargetLabel"] = "Windows 桌面包"
    export_payload["buildInfo"]["splashImageUrl"] = splash_file["relativePath"]
    write_export_app_files(app_dir, export_payload)
    icon_png_bytes = build_export_icon_png(bundle["project"])
    icon_ico_bytes = build_export_icon_ico(icon_png_bytes)
    app_icon_files = write_export_icon_files(app_dir, icon_png_bytes, icon_ico_bytes)
    root_icon_files = write_export_icon_files(build_dir, icon_png_bytes, icon_ico_bytes)
    (app_dir / "package.json").write_text(
        json.dumps(
            build_nwjs_package_json(bundle["project"], "Windows 桌面发布包", icon_path=app_icon_files["pngRelativePath"]),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    package_path = build_dir / "package.nw"
    runtime_mode = "nwjs"
    runtime_mode_label = "NW.js 桌面运行壳"
    runtime_downloaded = False
    runtime_warning = ""
    runtime_source_label = ""
    runtime_source_path = ""
    package_mode = "single_exe"
    package_mode_label = "单文件 EXE + 运行库目录"

    try:
        create_package_nw_archive(app_dir, package_path)
        runtime_dir, runtime_downloaded, runtime_source_label, runtime_source_path = ensure_nwjs_runtime(
            NWJS_GAME_PLATFORM_WINDOWS
        )
        for runtime_path in runtime_dir.iterdir():
            target_path = build_dir / runtime_path.name
            if runtime_path.is_dir():
                shutil.copytree(runtime_path, target_path, dirs_exist_ok=True)
            else:
                shutil.copy2(runtime_path, target_path)

        executable_name = sanitize_export_filename(bundle["project"].get("title") or "") or ""
        if executable_name in {"", "asset"}:
            executable_name = sanitize_export_filename(bundle["project"].get("projectId") or "") or "CanvasiaGame"
        executable_name = f"{executable_name}.exe"

        default_executable = build_dir / "nw.exe"
        launcher_path = build_dir / executable_name
        if default_executable.is_file():
            build_nwjs_single_file_executable(default_executable, package_path, launcher_path)
            default_executable.unlink(missing_ok=True)
            package_path.unlink(missing_ok=True)
        else:
            raise ValueError("桌面运行壳复制完成了，但没有找到 nw.exe。")
    except Exception as error:
        runtime_mode = "edge_launcher"
        runtime_mode_label = "Windows 浏览器启动器"
        package_mode = "browser_launcher"
        package_mode_label = "浏览器启动器文件夹版"
        runtime_warning = str(error)
        if package_path.exists():
            package_path.unlink(missing_ok=True)
        launcher_path = write_windows_browser_launcher(build_dir, bundle["project"])
        executable_name = launcher_path.name

    start_helper_path = write_windows_start_helper(build_dir, executable_name)
    manifest = build_export_manifest(
        bundle,
        target=EXPORT_TARGET_WINDOWS_NWJS,
        target_label="Windows 桌面包",
        build_id=build_dir.name,
        copied_assets=copied_assets,
        missing_assets=missing_assets,
        extra_files={
            "launcher": executable_name,
            "archive": f"{build_dir.name}.zip",
            "appEntry": "app/index.html",
            "appPlayerJs": "app/player.js",
            "appRuntimeConditions": "app/runtime_conditions.js",
            "appRuntimeControls": "app/runtime_controls.js",
            "appRuntimeSettings": "app/runtime_settings.js",
            "appRuntimeAudio": "app/runtime_audio.js",
            "appRuntimePreload": "app/runtime_preload.js",
            "appRuntimePreloadManifest": f"app/{RUNTIME_PRELOAD_MANIFEST_FILE_NAME}",
            "appRuntimePreloadReport": f"app/{RUNTIME_PRELOAD_REPORT_FILE_NAME}",
            "playtestGuide": EXPORT_PLAYTEST_GUIDE_FILE_NAME,
            "releaseEvidencePack": EXPORT_RELEASE_EVIDENCE_PACK_NAME,
            "assetRights": EXPORT_ASSET_RIGHTS_JSON_NAME,
            "assetRightsReport": EXPORT_ASSET_RIGHTS_REPORT_NAME,
            "assetRightsCsv": EXPORT_ASSET_RIGHTS_CSV_NAME,
            "audioCueSheet": EXPORT_AUDIO_CUE_SHEET_JSON_NAME,
            "audioCueSheetReport": EXPORT_AUDIO_CUE_SHEET_REPORT_NAME,
            "audioCueSheetCsv": EXPORT_AUDIO_CUE_SHEET_CSV_NAME,
            "stageDirection": EXPORT_STAGE_DIRECTION_JSON_NAME,
            "stageDirectionReport": EXPORT_STAGE_DIRECTION_REPORT_NAME,
            "stageDirectionCsv": EXPORT_STAGE_DIRECTION_CSV_NAME,
            "presentationTimeline": EXPORT_PRESENTATION_TIMELINE_JSON_NAME,
            "presentationTimelineReport": EXPORT_PRESENTATION_TIMELINE_REPORT_NAME,
            "presentationTimelineCsv": EXPORT_PRESENTATION_TIMELINE_CSV_NAME,
            "routePlaytestWorkbook": EXPORT_ROUTE_PLAYTEST_WORKBOOK_JSON_NAME,
            "routePlaytestWorkbookReport": EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME,
            "routePlaytestWorkbookCsv": EXPORT_ROUTE_PLAYTEST_WORKBOOK_CSV_NAME,
            "choiceConsequence": EXPORT_CHOICE_CONSEQUENCE_JSON_NAME,
            "choiceConsequenceReport": EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME,
            "choiceConsequenceCsv": EXPORT_CHOICE_CONSEQUENCE_CSV_NAME,
            "variableInfluence": EXPORT_VARIABLE_INFLUENCE_JSON_NAME,
            "variableInfluenceReport": EXPORT_VARIABLE_INFLUENCE_REPORT_NAME,
            "variableInfluenceCsv": EXPORT_VARIABLE_INFLUENCE_CSV_NAME,
            "voiceProduction": EXPORT_VOICE_PRODUCTION_JSON_NAME,
            "voiceProductionReport": EXPORT_VOICE_PRODUCTION_REPORT_NAME,
            "voiceProductionCsv": EXPORT_VOICE_PRODUCTION_CSV_NAME,
            "storyRouteMap": EXPORT_STORY_ROUTE_MAP_JSON_NAME,
            "storyRouteMapReport": EXPORT_STORY_ROUTE_MAP_REPORT_NAME,
            "localizationAudit": EXPORT_LOCALIZATION_AUDIT_JSON_NAME,
            "localizationAuditReport": EXPORT_LOCALIZATION_AUDIT_REPORT_NAME,
            "releaseReadinessSummary": EXPORT_RELEASE_READINESS_JSON_NAME,
            "releaseReadinessReport": EXPORT_RELEASE_READINESS_REPORT_NAME,
            "unlockableContentManifest": f"app/{UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME}",
            "unlockableContentReport": f"app/{UNLOCKABLE_CONTENT_REPORT_FILE_NAME}",
            "appPackage": "app/package.json",
            "iconPng": root_icon_files["pngFileName"],
            "iconIco": root_icon_files["icoFileName"],
            "launchSplash": root_splash_file["fileName"],
            "runtimeGuide": str(runtime_guide_path),
            "startHelper": start_helper_path.name,
        },
        runtime_info={
            "mode": runtime_mode,
            "modeLabel": runtime_mode_label,
            "packageMode": package_mode,
            "packageModeLabel": package_mode_label,
            "version": NWJS_RUNTIME_VERSION if runtime_mode == "nwjs" else "",
            "warning": runtime_warning,
            "sourceLabel": runtime_source_label,
            "sourcePath": runtime_source_path,
        },
    )
    manifest_path = write_export_manifest(build_dir, manifest)
    asset_rights_files = write_export_asset_rights_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    audio_cue_sheet_files = write_export_audio_cue_sheet_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    stage_direction_files = write_export_stage_direction_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    presentation_timeline_files = write_export_presentation_timeline_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    voice_production_files = write_export_voice_production_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    readme_path = write_windows_package_readme(
        build_dir,
        executable_name,
        runtime_mode,
        package_mode_label,
        runtime_downloaded,
        runtime_source_label,
        manifest_path.name,
        manifest["engine"]["releaseVersion"],
    )
    launch_steps = [
        "优先双击 `启动游戏.cmd`。",
        f"也可以直接双击 `{executable_name}`。",
        "对外发送时请压缩整个导出文件夹，不要只发送单个 exe 或 cmd。",
    ]
    runtime_notes = [
        f"当前桌面模式：{runtime_mode_label}。",
        f"当前打包方式：{package_mode_label}。",
    ]
    playtest_guide_path = write_export_playtest_guide_file(
        build_dir,
        project=bundle["project"],
        target_label="Windows 桌面包",
        release_version=release_version,
        launch_steps=launch_steps,
        manifest_name=manifest_path.name,
        unlockable_manifest_name=f"app/{UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME}",
        unlockable_report_name=f"app/{UNLOCKABLE_CONTENT_REPORT_FILE_NAME}",
        provenance_name=EXPORT_PROVENANCE_FILE_NAME,
        extra_reports=[
            EXPORT_RELEASE_EVIDENCE_PACK_NAME,
            asset_rights_files["assetRightsReportName"],
            audio_cue_sheet_files["audioCueSheetReportName"],
            stage_direction_files["stageDirectionReportName"],
            presentation_timeline_files["presentationTimelineReportName"],
            EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME,
            EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME,
            voice_production_files["voiceProductionReportName"],
            readme_path.name,
            EXPORT_STORY_ROUTE_MAP_REPORT_NAME,
            EXPORT_LOCALIZATION_AUDIT_REPORT_NAME,
            EXPORT_RELEASE_READINESS_REPORT_NAME,
        ],
        runtime_notes=runtime_notes,
        missing_assets=missing_assets,
    )
    quality_reports = write_export_quality_report_bundle(
        build_dir,
        bundle=bundle,
        project=bundle["project"],
        manifest=manifest,
        missing_assets=missing_assets,
        unlockable_manifest=(export_payload.get("buildInfo") or {}).get("unlockableContentManifest"),
        base_report_files=[
            manifest_path.name,
            readme_path.name,
            playtest_guide_path.name,
        ],
        extra_report_files=[
            f"app/{UNLOCKABLE_CONTENT_REPORT_FILE_NAME}",
            f"app/{UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME}",
            asset_rights_files["assetRightsReportName"],
            asset_rights_files["assetRightsName"],
            asset_rights_files["assetRightsCsvName"],
            audio_cue_sheet_files["audioCueSheetReportName"],
            audio_cue_sheet_files["audioCueSheetName"],
            audio_cue_sheet_files["audioCueSheetCsvName"],
            stage_direction_files["stageDirectionReportName"],
            stage_direction_files["stageDirectionName"],
            stage_direction_files["stageDirectionCsvName"],
            presentation_timeline_files["presentationTimelineReportName"],
            presentation_timeline_files["presentationTimelineName"],
            presentation_timeline_files["presentationTimelineCsvName"],
            EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME,
            EXPORT_ROUTE_PLAYTEST_WORKBOOK_JSON_NAME,
            EXPORT_ROUTE_PLAYTEST_WORKBOOK_CSV_NAME,
            EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME,
            EXPORT_CHOICE_CONSEQUENCE_JSON_NAME,
            EXPORT_CHOICE_CONSEQUENCE_CSV_NAME,
            EXPORT_VARIABLE_INFLUENCE_REPORT_NAME,
            EXPORT_VARIABLE_INFLUENCE_JSON_NAME,
            EXPORT_VARIABLE_INFLUENCE_CSV_NAME,
            voice_production_files["voiceProductionReportName"],
            voice_production_files["voiceProductionName"],
            voice_production_files["voiceProductionCsvName"],
        ],
        platform_notes=[
            f"当前桌面模式：{runtime_mode_label}。",
            "Windows 预览包可能触发 SmartScreen；分发前建议附带来源说明和校验文件。",
        ],
    )
    story_route_map = quality_reports
    localization_audit = quality_reports
    release_readiness = quality_reports
    evidence_pack_path = write_export_release_evidence_pack_file(
        build_dir,
        project=bundle["project"],
        target_label="Windows 桌面包",
        release_version=release_version,
        manifest_name=manifest_path.name,
        playtest_guide_name=playtest_guide_path.name,
        provenance_name=EXPORT_PROVENANCE_FILE_NAME,
        story_route_map_report_name=story_route_map["storyRouteMapReportName"],
        localization_audit_report_name=localization_audit["localizationAuditReportName"],
        release_readiness_report_name=release_readiness["releaseReadinessReportName"],
        unlockable_report_name=f"app/{UNLOCKABLE_CONTENT_REPORT_FILE_NAME}",
        unlockable_manifest_name=f"app/{UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME}",
        launch_steps=launch_steps,
        runtime_notes=runtime_notes,
        extra_reports=[
            readme_path.name,
            asset_rights_files["assetRightsReportName"],
            audio_cue_sheet_files["audioCueSheetReportName"],
            stage_direction_files["stageDirectionReportName"],
            presentation_timeline_files["presentationTimelineReportName"],
            EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME,
            EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME,
            EXPORT_VARIABLE_INFLUENCE_REPORT_NAME,
            voice_production_files["voiceProductionReportName"],
            f"app/{RUNTIME_PRELOAD_REPORT_FILE_NAME}",
        ],
        missing_assets=missing_assets,
    )
    provenance_verifiers = write_export_provenance_verifier_files(build_dir)
    provenance_roots = [
        app_dir,
        manifest_path,
        readme_path,
        playtest_guide_path,
        evidence_pack_path,
        Path(asset_rights_files["assetRightsReportPath"]),
        Path(asset_rights_files["assetRightsPath"]),
        Path(asset_rights_files["assetRightsCsvPath"]),
        Path(audio_cue_sheet_files["audioCueSheetReportPath"]),
        Path(audio_cue_sheet_files["audioCueSheetPath"]),
        Path(audio_cue_sheet_files["audioCueSheetCsvPath"]),
        Path(stage_direction_files["stageDirectionReportPath"]),
        Path(stage_direction_files["stageDirectionPath"]),
        Path(stage_direction_files["stageDirectionCsvPath"]),
        Path(presentation_timeline_files["presentationTimelineReportPath"]),
        Path(presentation_timeline_files["presentationTimelinePath"]),
        Path(presentation_timeline_files["presentationTimelineCsvPath"]),
        Path(story_route_map["routePlaytestWorkbookReportPath"]),
        Path(story_route_map["routePlaytestWorkbookPath"]),
        Path(story_route_map["routePlaytestWorkbookCsvPath"]),
        Path(story_route_map["choiceConsequenceReportPath"]),
        Path(story_route_map["choiceConsequencePath"]),
        Path(story_route_map["choiceConsequenceCsvPath"]),
        Path(story_route_map["variableInfluenceReportPath"]),
        Path(story_route_map["variableInfluencePath"]),
        Path(story_route_map["variableInfluenceCsvPath"]),
        Path(voice_production_files["voiceProductionReportPath"]),
        Path(voice_production_files["voiceProductionPath"]),
        Path(voice_production_files["voiceProductionCsvPath"]),
        Path(story_route_map["storyRouteMapReportPath"]),
        Path(story_route_map["storyRouteMapPath"]),
        Path(localization_audit["localizationAuditReportPath"]),
        Path(localization_audit["localizationAuditPath"]),
        Path(release_readiness["releaseReadinessReportPath"]),
        Path(release_readiness["releaseReadinessSummaryPath"]),
        start_helper_path,
        root_icon_files["pngPath"],
        root_icon_files["icoPath"],
        root_splash_file["path"],
        *provenance_verifiers["paths"],
    ]
    if launcher_path.suffix.lower() in {".cmd", ".bat"}:
        provenance_roots.append(launcher_path)
    provenance_file = write_export_provenance_file(build_dir, bundle, manifest, roots=provenance_roots)
    archive_path = Path(shutil.make_archive(str(build_dir), "zip", root_dir=build_dir.parent, base_dir=build_dir.name))

    return {
        "target": EXPORT_TARGET_WINDOWS_NWJS,
        "targetLabel": "Windows 桌面包",
        "buildId": build_dir.name,
        "buildPath": str(build_dir),
        "launcherPath": str(launcher_path),
        "launcherFileName": executable_name,
        "startHelperPath": str(start_helper_path),
        "startHelperFileName": start_helper_path.name,
        "archivePath": str(archive_path),
        "archivePublicUrl": f"/exports/{archive_path.name}",
        "runtimeMode": runtime_mode,
        "runtimeModeLabel": runtime_mode_label,
        "packageMode": package_mode,
        "packageModeLabel": package_mode_label,
        "runtimeVersion": NWJS_RUNTIME_VERSION if runtime_mode == "nwjs" else "",
        "runtimeDownloaded": runtime_downloaded,
        "runtimeWarning": runtime_warning,
        "runtimeSourceLabel": runtime_source_label,
        "runtimeSourcePath": runtime_source_path,
        "runtimeGuidePath": str(runtime_guide_path),
        "releaseVersion": release_version,
        "manifestPath": str(manifest_path),
        "manifestPublicUrl": f"/exports/{build_dir.name}/{manifest_path.name}",
        "provenanceName": provenance_file["provenanceName"],
        "provenancePath": provenance_file["provenancePath"],
        "provenancePublicUrl": f"/exports/{build_dir.name}/{provenance_file['provenanceName']}",
        "provenanceSeal": provenance_file["provenanceSeal"],
        "provenanceSummary": provenance_file["provenanceSummary"],
        "provenanceVerifierName": provenance_verifiers["provenanceVerifierName"],
        "provenanceVerifierPath": provenance_verifiers["provenanceVerifierPath"],
        "provenanceVerifierPublicUrl": f"/exports/{build_dir.name}/{provenance_verifiers['provenanceVerifierName']}",
        "provenanceVerifierMacName": provenance_verifiers["provenanceVerifierMacName"],
        "provenanceVerifierMacPath": provenance_verifiers["provenanceVerifierMacPath"],
        "provenanceVerifierMacPublicUrl": f"/exports/{build_dir.name}/{provenance_verifiers['provenanceVerifierMacName']}",
        "provenanceVerifierLinuxName": provenance_verifiers["provenanceVerifierLinuxName"],
        "provenanceVerifierLinuxPath": provenance_verifiers["provenanceVerifierLinuxPath"],
        "provenanceVerifierLinuxPublicUrl": f"/exports/{build_dir.name}/{provenance_verifiers['provenanceVerifierLinuxName']}",
        "provenanceVerifierWindowsName": provenance_verifiers["provenanceVerifierWindowsName"],
        "provenanceVerifierWindowsPath": provenance_verifiers["provenanceVerifierWindowsPath"],
        "provenanceVerifierWindowsPublicUrl": f"/exports/{build_dir.name}/{provenance_verifiers['provenanceVerifierWindowsName']}",
        "iconPngPath": str(root_icon_files["pngPath"]),
        "iconIcoPath": str(root_icon_files["icoPath"]),
        "iconPngPublicUrl": f"/exports/{build_dir.name}/{root_icon_files['pngFileName']}",
        "iconIcoPublicUrl": f"/exports/{build_dir.name}/{root_icon_files['icoFileName']}",
        "splashPath": str(root_splash_file["path"]),
        "splashPublicUrl": f"/exports/{build_dir.name}/{root_splash_file['fileName']}",
        "readmePath": str(readme_path),
        "playtestGuidePath": str(playtest_guide_path),
        "playtestGuidePublicUrl": f"/exports/{build_dir.name}/{playtest_guide_path.name}",
        "releaseEvidencePackName": evidence_pack_path.name,
        "releaseEvidencePackPath": str(evidence_pack_path),
        "releaseEvidencePackPublicUrl": f"/exports/{build_dir.name}/{evidence_pack_path.name}",
        "assetRightsName": asset_rights_files["assetRightsName"],
        "assetRightsPath": asset_rights_files["assetRightsPath"],
        "assetRightsPublicUrl": f"/exports/{build_dir.name}/{asset_rights_files['assetRightsName']}",
        "assetRightsReportName": asset_rights_files["assetRightsReportName"],
        "assetRightsReportPath": asset_rights_files["assetRightsReportPath"],
        "assetRightsReportPublicUrl": f"/exports/{build_dir.name}/{asset_rights_files['assetRightsReportName']}",
        "assetRightsCsvName": asset_rights_files["assetRightsCsvName"],
        "assetRightsCsvPath": asset_rights_files["assetRightsCsvPath"],
        "assetRightsCsvPublicUrl": f"/exports/{build_dir.name}/{asset_rights_files['assetRightsCsvName']}",
        "assetRightsReadinessPercent": asset_rights_files["assetRightsReadinessPercent"],
        "assetRightsBlockerCount": asset_rights_files["assetRightsBlockerCount"],
        "assetRightsWarningCount": asset_rights_files["assetRightsWarningCount"],
        "audioCueSheetName": audio_cue_sheet_files["audioCueSheetName"],
        "audioCueSheetPath": audio_cue_sheet_files["audioCueSheetPath"],
        "audioCueSheetPublicUrl": f"/exports/{build_dir.name}/{audio_cue_sheet_files['audioCueSheetName']}",
        "audioCueSheetReportName": audio_cue_sheet_files["audioCueSheetReportName"],
        "audioCueSheetReportPath": audio_cue_sheet_files["audioCueSheetReportPath"],
        "audioCueSheetReportPublicUrl": f"/exports/{build_dir.name}/{audio_cue_sheet_files['audioCueSheetReportName']}",
        "audioCueSheetCsvName": audio_cue_sheet_files["audioCueSheetCsvName"],
        "audioCueSheetCsvPath": audio_cue_sheet_files["audioCueSheetCsvPath"],
        "audioCueSheetCsvPublicUrl": f"/exports/{build_dir.name}/{audio_cue_sheet_files['audioCueSheetCsvName']}",
        "audioCueSheetReadinessPercent": audio_cue_sheet_files["audioCueSheetReadinessPercent"],
        "audioCueSheetCueCount": audio_cue_sheet_files["audioCueSheetCueCount"],
        "audioCueSheetBlockerCount": audio_cue_sheet_files["audioCueSheetBlockerCount"],
        "audioCueSheetWarningCount": audio_cue_sheet_files["audioCueSheetWarningCount"],
        "stageDirectionName": stage_direction_files["stageDirectionName"],
        "stageDirectionPath": stage_direction_files["stageDirectionPath"],
        "stageDirectionPublicUrl": f"/exports/{build_dir.name}/{stage_direction_files['stageDirectionName']}",
        "stageDirectionReportName": stage_direction_files["stageDirectionReportName"],
        "stageDirectionReportPath": stage_direction_files["stageDirectionReportPath"],
        "stageDirectionReportPublicUrl": f"/exports/{build_dir.name}/{stage_direction_files['stageDirectionReportName']}",
        "stageDirectionCsvName": stage_direction_files["stageDirectionCsvName"],
        "stageDirectionCsvPath": stage_direction_files["stageDirectionCsvPath"],
        "stageDirectionCsvPublicUrl": f"/exports/{build_dir.name}/{stage_direction_files['stageDirectionCsvName']}",
        "stageDirectionReadinessPercent": stage_direction_files["stageDirectionReadinessPercent"],
        "stageDirectionEventCount": stage_direction_files["stageDirectionEventCount"],
        "stageDirectionBlockerCount": stage_direction_files["stageDirectionBlockerCount"],
        "stageDirectionWarningCount": stage_direction_files["stageDirectionWarningCount"],
        "presentationTimelineName": presentation_timeline_files["presentationTimelineName"],
        "presentationTimelinePath": presentation_timeline_files["presentationTimelinePath"],
        "presentationTimelinePublicUrl": f"/exports/{build_dir.name}/{presentation_timeline_files['presentationTimelineName']}",
        "presentationTimelineReportName": presentation_timeline_files["presentationTimelineReportName"],
        "presentationTimelineReportPath": presentation_timeline_files["presentationTimelineReportPath"],
        "presentationTimelineReportPublicUrl": f"/exports/{build_dir.name}/{presentation_timeline_files['presentationTimelineReportName']}",
        "presentationTimelineCsvName": presentation_timeline_files["presentationTimelineCsvName"],
        "presentationTimelineCsvPath": presentation_timeline_files["presentationTimelineCsvPath"],
        "presentationTimelineCsvPublicUrl": f"/exports/{build_dir.name}/{presentation_timeline_files['presentationTimelineCsvName']}",
        "presentationTimelineReadinessPercent": presentation_timeline_files["presentationTimelineReadinessPercent"],
        "presentationTimelineEventCount": presentation_timeline_files["presentationTimelineEventCount"],
        "presentationTimelineBlockerCount": presentation_timeline_files["presentationTimelineBlockerCount"],
        "presentationTimelineWarningCount": presentation_timeline_files["presentationTimelineWarningCount"],
        "routePlaytestWorkbookName": story_route_map["routePlaytestWorkbookName"],
        "routePlaytestWorkbookPath": story_route_map["routePlaytestWorkbookPath"],
        "routePlaytestWorkbookPublicUrl": f"/exports/{build_dir.name}/{story_route_map['routePlaytestWorkbookName']}",
        "routePlaytestWorkbookReportName": story_route_map["routePlaytestWorkbookReportName"],
        "routePlaytestWorkbookReportPath": story_route_map["routePlaytestWorkbookReportPath"],
        "routePlaytestWorkbookReportPublicUrl": f"/exports/{build_dir.name}/{story_route_map['routePlaytestWorkbookReportName']}",
        "routePlaytestWorkbookCsvName": story_route_map["routePlaytestWorkbookCsvName"],
        "routePlaytestWorkbookCsvPath": story_route_map["routePlaytestWorkbookCsvPath"],
        "routePlaytestWorkbookCsvPublicUrl": f"/exports/{build_dir.name}/{story_route_map['routePlaytestWorkbookCsvName']}",
        "routePlaytestReadinessPercent": story_route_map["routePlaytestReadinessPercent"],
        "routePlaytestRouteCaseCount": story_route_map["routePlaytestRouteCaseCount"],
        "routePlaytestEndingCaseCount": story_route_map["routePlaytestEndingCaseCount"],
        "routePlaytestBlockedCaseCount": story_route_map["routePlaytestBlockedCaseCount"],
        "choiceConsequenceName": story_route_map["choiceConsequenceName"],
        "choiceConsequencePath": story_route_map["choiceConsequencePath"],
        "choiceConsequencePublicUrl": f"/exports/{build_dir.name}/{story_route_map['choiceConsequenceName']}",
        "choiceConsequenceReportName": story_route_map["choiceConsequenceReportName"],
        "choiceConsequenceReportPath": story_route_map["choiceConsequenceReportPath"],
        "choiceConsequenceReportPublicUrl": f"/exports/{build_dir.name}/{story_route_map['choiceConsequenceReportName']}",
        "choiceConsequenceCsvName": story_route_map["choiceConsequenceCsvName"],
        "choiceConsequenceCsvPath": story_route_map["choiceConsequenceCsvPath"],
        "choiceConsequenceCsvPublicUrl": f"/exports/{build_dir.name}/{story_route_map['choiceConsequenceCsvName']}",
        "choiceConsequenceReadinessPercent": story_route_map["choiceConsequenceReadinessPercent"],
        "choiceConsequenceOptionCount": story_route_map["choiceConsequenceOptionCount"],
        "choiceConsequenceBlockerCount": story_route_map["choiceConsequenceBlockerCount"],
        "choiceConsequenceWarningCount": story_route_map["choiceConsequenceWarningCount"],
        "variableInfluenceName": story_route_map["variableInfluenceName"],
        "variableInfluencePath": story_route_map["variableInfluencePath"],
        "variableInfluencePublicUrl": f"/exports/{build_dir.name}/{story_route_map['variableInfluenceName']}",
        "variableInfluenceReportName": story_route_map["variableInfluenceReportName"],
        "variableInfluenceReportPath": story_route_map["variableInfluenceReportPath"],
        "variableInfluenceReportPublicUrl": f"/exports/{build_dir.name}/{story_route_map['variableInfluenceReportName']}",
        "variableInfluenceCsvName": story_route_map["variableInfluenceCsvName"],
        "variableInfluenceCsvPath": story_route_map["variableInfluenceCsvPath"],
        "variableInfluenceCsvPublicUrl": f"/exports/{build_dir.name}/{story_route_map['variableInfluenceCsvName']}",
        "variableInfluenceReadinessPercent": story_route_map["variableInfluenceReadinessPercent"],
        "variableInfluenceVariableCount": story_route_map["variableInfluenceVariableCount"],
        "variableInfluenceBlockerCount": story_route_map["variableInfluenceBlockerCount"],
        "variableInfluenceWarningCount": story_route_map["variableInfluenceWarningCount"],
        "voiceProductionName": voice_production_files["voiceProductionName"],
        "voiceProductionPath": voice_production_files["voiceProductionPath"],
        "voiceProductionPublicUrl": f"/exports/{build_dir.name}/{voice_production_files['voiceProductionName']}",
        "voiceProductionReportName": voice_production_files["voiceProductionReportName"],
        "voiceProductionReportPath": voice_production_files["voiceProductionReportPath"],
        "voiceProductionReportPublicUrl": f"/exports/{build_dir.name}/{voice_production_files['voiceProductionReportName']}",
        "voiceProductionCsvName": voice_production_files["voiceProductionCsvName"],
        "voiceProductionCsvPath": voice_production_files["voiceProductionCsvPath"],
        "voiceProductionCsvPublicUrl": f"/exports/{build_dir.name}/{voice_production_files['voiceProductionCsvName']}",
        "voiceProductionReadyPercent": voice_production_files["voiceProductionReadyPercent"],
        "voiceProductionLineCount": voice_production_files["voiceProductionLineCount"],
        "voiceProductionBlockerCount": voice_production_files["voiceProductionBlockerCount"],
        "voiceProductionWarningCount": voice_production_files["voiceProductionWarningCount"],
        "storyRouteMapName": story_route_map["storyRouteMapName"],
        "storyRouteMapPath": story_route_map["storyRouteMapPath"],
        "storyRouteMapPublicUrl": f"/exports/{build_dir.name}/{story_route_map['storyRouteMapName']}",
        "storyRouteMapReportName": story_route_map["storyRouteMapReportName"],
        "storyRouteMapReportPath": story_route_map["storyRouteMapReportPath"],
        "storyRouteMapReportPublicUrl": f"/exports/{build_dir.name}/{story_route_map['storyRouteMapReportName']}",
        "storyRouteMapStatus": story_route_map["storyRouteMapStatus"],
        "localizationAuditName": localization_audit["localizationAuditName"],
        "localizationAuditPath": localization_audit["localizationAuditPath"],
        "localizationAuditPublicUrl": f"/exports/{build_dir.name}/{localization_audit['localizationAuditName']}",
        "localizationAuditReportName": localization_audit["localizationAuditReportName"],
        "localizationAuditReportPath": localization_audit["localizationAuditReportPath"],
        "localizationAuditReportPublicUrl": f"/exports/{build_dir.name}/{localization_audit['localizationAuditReportName']}",
        "localizationAuditStatus": localization_audit["localizationAuditStatus"],
        "localizationAuditCompletionPercent": localization_audit["localizationAuditCompletionPercent"],
        "releaseReadinessSummaryName": release_readiness["releaseReadinessSummaryName"],
        "releaseReadinessSummaryPath": release_readiness["releaseReadinessSummaryPath"],
        "releaseReadinessSummaryPublicUrl": f"/exports/{build_dir.name}/{release_readiness['releaseReadinessSummaryName']}",
        "releaseReadinessReportName": release_readiness["releaseReadinessReportName"],
        "releaseReadinessReportPath": release_readiness["releaseReadinessReportPath"],
        "releaseReadinessReportPublicUrl": f"/exports/{build_dir.name}/{release_readiness['releaseReadinessReportName']}",
        "releaseReadinessStatus": release_readiness["releaseReadinessStatus"],
        "releaseReadinessScore": release_readiness["releaseReadinessScore"],
        "copiedAssets": copied_assets,
        "missingAssets": len(missing_assets),
        "missingAssetNames": [asset.get("name") or asset.get("id") or "未命名素材" for asset in missing_assets[:5]],
    }


def export_macos_nwjs_build() -> dict:
    build_dir = create_export_build_dir("macos_build")
    bundle = load_project_bundle()
    runtime_guide_path = ensure_local_nwjs_runtime_dropin_guide()
    app_dir = build_dir / "app"
    app_dir.mkdir(parents=True, exist_ok=True)
    export_assets_doc, copied_assets, missing_assets = copy_assets_for_export(bundle["assets"], app_dir)
    export_payload = build_export_payload(bundle, export_assets_doc, copied_assets, missing_assets)
    release_version = get_export_release_version(bundle["project"])
    splash_file = write_export_splash_asset(app_dir, bundle["project"], release_version, "Canvasia Engine macOS 桌面发布包")
    root_splash_file = write_export_splash_asset(build_dir, bundle["project"], release_version, "Canvasia Engine macOS 桌面发布包")
    export_payload["buildInfo"]["releaseVersion"] = release_version
    export_payload["buildInfo"]["exportTargetLabel"] = "macOS 桌面包"
    export_payload["buildInfo"]["splashImageUrl"] = splash_file["relativePath"]
    write_export_app_files(app_dir, export_payload)
    icon_png_bytes = build_export_icon_png(bundle["project"])
    icon_ico_bytes = build_export_icon_ico(icon_png_bytes)
    app_icon_files = write_export_icon_files(app_dir, icon_png_bytes, icon_ico_bytes)
    root_icon_files = write_export_icon_files(build_dir, icon_png_bytes, icon_ico_bytes)
    (app_dir / "package.json").write_text(
        json.dumps(
            build_nwjs_package_json(bundle["project"], "macOS 桌面发布包", icon_path=app_icon_files["pngRelativePath"]),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    package_path = build_dir / "package.nw"
    create_package_nw_archive(app_dir, package_path)
    runtime_dir, runtime_downloaded, runtime_source_label, runtime_source_path = ensure_nwjs_runtime(NWJS_GAME_PLATFORM_MACOS)
    runtime_bundle = find_nwjs_macos_app_bundle(runtime_dir)
    if runtime_bundle is None:
        raise ValueError("macOS 运行壳里没有找到 nwjs.app。")

    app_bundle_name = build_macos_app_bundle_name(bundle["project"])
    launcher_path = build_dir / app_bundle_name
    copytree_with_symlinks(runtime_bundle, launcher_path)
    executable_name = customize_macos_nwjs_app_bundle(launcher_path, bundle["project"], release_version)
    resources_dir = launcher_path / "Contents" / "Resources"
    resources_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(package_path, resources_dir / "app.nw")
    package_path.unlink(missing_ok=True)
    start_helper_path = write_macos_start_helper(build_dir, app_bundle_name)

    manifest = build_export_manifest(
        bundle,
        target=EXPORT_TARGET_MACOS_NWJS,
        target_label="macOS 桌面包",
        build_id=build_dir.name,
        copied_assets=copied_assets,
        missing_assets=missing_assets,
        extra_files={
            "launcher": app_bundle_name,
            "archive": f"{build_dir.name}.zip",
            "appEntry": "app/index.html",
            "appPlayerJs": "app/player.js",
            "appRuntimeConditions": "app/runtime_conditions.js",
            "appRuntimeControls": "app/runtime_controls.js",
            "appRuntimeSettings": "app/runtime_settings.js",
            "appRuntimeAudio": "app/runtime_audio.js",
            "appRuntimePreload": "app/runtime_preload.js",
            "appRuntimePreloadManifest": f"app/{RUNTIME_PRELOAD_MANIFEST_FILE_NAME}",
            "appRuntimePreloadReport": f"app/{RUNTIME_PRELOAD_REPORT_FILE_NAME}",
            "playtestGuide": EXPORT_PLAYTEST_GUIDE_FILE_NAME,
            "releaseEvidencePack": EXPORT_RELEASE_EVIDENCE_PACK_NAME,
            "assetRights": EXPORT_ASSET_RIGHTS_JSON_NAME,
            "assetRightsReport": EXPORT_ASSET_RIGHTS_REPORT_NAME,
            "assetRightsCsv": EXPORT_ASSET_RIGHTS_CSV_NAME,
            "audioCueSheet": EXPORT_AUDIO_CUE_SHEET_JSON_NAME,
            "audioCueSheetReport": EXPORT_AUDIO_CUE_SHEET_REPORT_NAME,
            "audioCueSheetCsv": EXPORT_AUDIO_CUE_SHEET_CSV_NAME,
            "stageDirection": EXPORT_STAGE_DIRECTION_JSON_NAME,
            "stageDirectionReport": EXPORT_STAGE_DIRECTION_REPORT_NAME,
            "stageDirectionCsv": EXPORT_STAGE_DIRECTION_CSV_NAME,
            "presentationTimeline": EXPORT_PRESENTATION_TIMELINE_JSON_NAME,
            "presentationTimelineReport": EXPORT_PRESENTATION_TIMELINE_REPORT_NAME,
            "presentationTimelineCsv": EXPORT_PRESENTATION_TIMELINE_CSV_NAME,
            "routePlaytestWorkbook": EXPORT_ROUTE_PLAYTEST_WORKBOOK_JSON_NAME,
            "routePlaytestWorkbookReport": EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME,
            "routePlaytestWorkbookCsv": EXPORT_ROUTE_PLAYTEST_WORKBOOK_CSV_NAME,
            "choiceConsequence": EXPORT_CHOICE_CONSEQUENCE_JSON_NAME,
            "choiceConsequenceReport": EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME,
            "choiceConsequenceCsv": EXPORT_CHOICE_CONSEQUENCE_CSV_NAME,
            "variableInfluence": EXPORT_VARIABLE_INFLUENCE_JSON_NAME,
            "variableInfluenceReport": EXPORT_VARIABLE_INFLUENCE_REPORT_NAME,
            "variableInfluenceCsv": EXPORT_VARIABLE_INFLUENCE_CSV_NAME,
            "voiceProduction": EXPORT_VOICE_PRODUCTION_JSON_NAME,
            "voiceProductionReport": EXPORT_VOICE_PRODUCTION_REPORT_NAME,
            "voiceProductionCsv": EXPORT_VOICE_PRODUCTION_CSV_NAME,
            "storyRouteMap": EXPORT_STORY_ROUTE_MAP_JSON_NAME,
            "storyRouteMapReport": EXPORT_STORY_ROUTE_MAP_REPORT_NAME,
            "localizationAudit": EXPORT_LOCALIZATION_AUDIT_JSON_NAME,
            "localizationAuditReport": EXPORT_LOCALIZATION_AUDIT_REPORT_NAME,
            "releaseReadinessSummary": EXPORT_RELEASE_READINESS_JSON_NAME,
            "releaseReadinessReport": EXPORT_RELEASE_READINESS_REPORT_NAME,
            "unlockableContentManifest": f"app/{UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME}",
            "unlockableContentReport": f"app/{UNLOCKABLE_CONTENT_REPORT_FILE_NAME}",
            "appPackage": "app/package.json",
            "iconPng": root_icon_files["pngFileName"],
            "iconIco": root_icon_files["icoFileName"],
            "launchSplash": root_splash_file["fileName"],
            "runtimeGuide": str(runtime_guide_path),
            "startHelper": start_helper_path.name,
        },
        runtime_info={
            "mode": "nwjs",
            "modeLabel": "NW.js 原生 .app 应用包",
            "packageMode": "macos_app",
            "packageModeLabel": "原生 .app 应用包",
            "version": NWJS_RUNTIME_VERSION,
            "warning": "",
            "sourceLabel": runtime_source_label,
            "sourcePath": runtime_source_path,
            "archLabel": get_nwjs_runtime_config(NWJS_GAME_PLATFORM_MACOS).get("archLabel") or "",
        },
    )
    manifest_path = write_export_manifest(build_dir, manifest)
    asset_rights_files = write_export_asset_rights_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    audio_cue_sheet_files = write_export_audio_cue_sheet_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    stage_direction_files = write_export_stage_direction_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    presentation_timeline_files = write_export_presentation_timeline_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    voice_production_files = write_export_voice_production_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    readme_path = write_macos_package_readme(
        build_dir,
        app_bundle_name,
        start_helper_path.name,
        runtime_downloaded,
        runtime_source_label,
        manifest_path.name,
        release_version,
    )
    launch_steps = [
        f"优先双击 `{start_helper_path.name}`。",
        f"也可以直接打开 `{app_bundle_name}`。",
        "对外发送时请压缩整个导出文件夹，不要只发送 .app。",
    ]
    runtime_notes = [
        f"当前运行壳：NW.js {NWJS_RUNTIME_VERSION}。",
        "未签名预览包可能触发 Gatekeeper 提示；正式发布前建议补签名和公证。",
    ]
    playtest_guide_path = write_export_playtest_guide_file(
        build_dir,
        project=bundle["project"],
        target_label="macOS 桌面包",
        release_version=release_version,
        launch_steps=launch_steps,
        manifest_name=manifest_path.name,
        unlockable_manifest_name=f"app/{UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME}",
        unlockable_report_name=f"app/{UNLOCKABLE_CONTENT_REPORT_FILE_NAME}",
        provenance_name=EXPORT_PROVENANCE_FILE_NAME,
        extra_reports=[
            EXPORT_RELEASE_EVIDENCE_PACK_NAME,
            asset_rights_files["assetRightsReportName"],
            audio_cue_sheet_files["audioCueSheetReportName"],
            stage_direction_files["stageDirectionReportName"],
            voice_production_files["voiceProductionReportName"],
            readme_path.name,
            EXPORT_STORY_ROUTE_MAP_REPORT_NAME,
            EXPORT_LOCALIZATION_AUDIT_REPORT_NAME,
            EXPORT_RELEASE_READINESS_REPORT_NAME,
        ],
        runtime_notes=runtime_notes,
        missing_assets=missing_assets,
    )
    quality_reports = write_export_quality_report_bundle(
        build_dir,
        bundle=bundle,
        project=bundle["project"],
        manifest=manifest,
        missing_assets=missing_assets,
        unlockable_manifest=(export_payload.get("buildInfo") or {}).get("unlockableContentManifest"),
        base_report_files=[
            manifest_path.name,
            readme_path.name,
            playtest_guide_path.name,
        ],
        extra_report_files=[
            f"app/{UNLOCKABLE_CONTENT_REPORT_FILE_NAME}",
            f"app/{UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME}",
            asset_rights_files["assetRightsReportName"],
            asset_rights_files["assetRightsName"],
            asset_rights_files["assetRightsCsvName"],
            audio_cue_sheet_files["audioCueSheetReportName"],
            audio_cue_sheet_files["audioCueSheetName"],
            audio_cue_sheet_files["audioCueSheetCsvName"],
            stage_direction_files["stageDirectionReportName"],
            stage_direction_files["stageDirectionName"],
            stage_direction_files["stageDirectionCsvName"],
            presentation_timeline_files["presentationTimelineReportName"],
            presentation_timeline_files["presentationTimelineName"],
            presentation_timeline_files["presentationTimelineCsvName"],
            EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME,
            EXPORT_ROUTE_PLAYTEST_WORKBOOK_JSON_NAME,
            EXPORT_ROUTE_PLAYTEST_WORKBOOK_CSV_NAME,
            EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME,
            EXPORT_CHOICE_CONSEQUENCE_JSON_NAME,
            EXPORT_CHOICE_CONSEQUENCE_CSV_NAME,
            EXPORT_VARIABLE_INFLUENCE_REPORT_NAME,
            EXPORT_VARIABLE_INFLUENCE_JSON_NAME,
            EXPORT_VARIABLE_INFLUENCE_CSV_NAME,
            voice_production_files["voiceProductionReportName"],
            voice_production_files["voiceProductionName"],
            voice_production_files["voiceProductionCsvName"],
        ],
        platform_notes=[
            f"当前运行壳：NW.js {NWJS_RUNTIME_VERSION}。",
            "macOS 未签名预览包可能触发 Gatekeeper；正式发布前建议补签名和公证。",
        ],
    )
    story_route_map = quality_reports
    localization_audit = quality_reports
    release_readiness = quality_reports
    evidence_pack_path = write_export_release_evidence_pack_file(
        build_dir,
        project=bundle["project"],
        target_label="macOS 桌面包",
        release_version=release_version,
        manifest_name=manifest_path.name,
        playtest_guide_name=playtest_guide_path.name,
        provenance_name=EXPORT_PROVENANCE_FILE_NAME,
        story_route_map_report_name=story_route_map["storyRouteMapReportName"],
        localization_audit_report_name=localization_audit["localizationAuditReportName"],
        release_readiness_report_name=release_readiness["releaseReadinessReportName"],
        unlockable_report_name=f"app/{UNLOCKABLE_CONTENT_REPORT_FILE_NAME}",
        unlockable_manifest_name=f"app/{UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME}",
        launch_steps=launch_steps,
        runtime_notes=runtime_notes,
        extra_reports=[
            readme_path.name,
            asset_rights_files["assetRightsReportName"],
            audio_cue_sheet_files["audioCueSheetReportName"],
            stage_direction_files["stageDirectionReportName"],
            EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME,
            EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME,
            EXPORT_VARIABLE_INFLUENCE_REPORT_NAME,
            voice_production_files["voiceProductionReportName"],
            f"app/{RUNTIME_PRELOAD_REPORT_FILE_NAME}",
        ],
        missing_assets=missing_assets,
    )
    provenance_verifiers = write_export_provenance_verifier_files(build_dir)
    provenance_file = write_export_provenance_file(
        build_dir,
        bundle,
        manifest,
        roots=[
            app_dir,
            manifest_path,
            readme_path,
            playtest_guide_path,
            evidence_pack_path,
            Path(asset_rights_files["assetRightsReportPath"]),
            Path(asset_rights_files["assetRightsPath"]),
            Path(asset_rights_files["assetRightsCsvPath"]),
            Path(audio_cue_sheet_files["audioCueSheetReportPath"]),
            Path(audio_cue_sheet_files["audioCueSheetPath"]),
            Path(audio_cue_sheet_files["audioCueSheetCsvPath"]),
            Path(stage_direction_files["stageDirectionReportPath"]),
            Path(stage_direction_files["stageDirectionPath"]),
            Path(stage_direction_files["stageDirectionCsvPath"]),
            Path(presentation_timeline_files["presentationTimelineReportPath"]),
            Path(presentation_timeline_files["presentationTimelinePath"]),
            Path(presentation_timeline_files["presentationTimelineCsvPath"]),
            Path(story_route_map["routePlaytestWorkbookReportPath"]),
            Path(story_route_map["routePlaytestWorkbookPath"]),
            Path(story_route_map["routePlaytestWorkbookCsvPath"]),
            Path(story_route_map["choiceConsequenceReportPath"]),
            Path(story_route_map["choiceConsequencePath"]),
            Path(story_route_map["choiceConsequenceCsvPath"]),
            Path(story_route_map["variableInfluenceReportPath"]),
            Path(story_route_map["variableInfluencePath"]),
            Path(story_route_map["variableInfluenceCsvPath"]),
            Path(voice_production_files["voiceProductionReportPath"]),
            Path(voice_production_files["voiceProductionPath"]),
            Path(voice_production_files["voiceProductionCsvPath"]),
            Path(story_route_map["storyRouteMapReportPath"]),
            Path(story_route_map["storyRouteMapPath"]),
            Path(localization_audit["localizationAuditReportPath"]),
            Path(localization_audit["localizationAuditPath"]),
            Path(release_readiness["releaseReadinessReportPath"]),
            Path(release_readiness["releaseReadinessSummaryPath"]),
            start_helper_path,
            root_icon_files["pngPath"],
            root_icon_files["icoPath"],
            root_splash_file["path"],
            *provenance_verifiers["paths"],
        ],
    )
    archive_path = Path(shutil.make_archive(str(build_dir), "zip", root_dir=build_dir.parent, base_dir=build_dir.name))

    return {
        "target": EXPORT_TARGET_MACOS_NWJS,
        "targetLabel": "macOS 桌面包",
        "buildId": build_dir.name,
        "buildPath": str(build_dir),
        "launcherPath": str(launcher_path),
        "launcherFileName": app_bundle_name,
        "appBundlePath": str(launcher_path),
        "appBundleName": app_bundle_name,
        "appExecutableName": executable_name,
        "startHelperPath": str(start_helper_path),
        "startHelperFileName": start_helper_path.name,
        "archivePath": str(archive_path),
        "archivePublicUrl": f"/exports/{archive_path.name}",
        "runtimeMode": "nwjs",
        "runtimeModeLabel": "NW.js 原生 .app 应用包",
        "packageMode": "macos_app",
        "packageModeLabel": "原生 .app 应用包",
        "runtimeVersion": NWJS_RUNTIME_VERSION,
        "runtimeDownloaded": runtime_downloaded,
        "runtimeWarning": "",
        "runtimeSourceLabel": runtime_source_label,
        "runtimeSourcePath": runtime_source_path,
        "runtimeGuidePath": str(runtime_guide_path),
        "releaseVersion": release_version,
        "manifestPath": str(manifest_path),
        "manifestPublicUrl": f"/exports/{build_dir.name}/{manifest_path.name}",
        "provenanceName": provenance_file["provenanceName"],
        "provenancePath": provenance_file["provenancePath"],
        "provenancePublicUrl": f"/exports/{build_dir.name}/{provenance_file['provenanceName']}",
        "provenanceSeal": provenance_file["provenanceSeal"],
        "provenanceSummary": provenance_file["provenanceSummary"],
        "provenanceVerifierName": provenance_verifiers["provenanceVerifierName"],
        "provenanceVerifierPath": provenance_verifiers["provenanceVerifierPath"],
        "provenanceVerifierPublicUrl": f"/exports/{build_dir.name}/{provenance_verifiers['provenanceVerifierName']}",
        "provenanceVerifierMacName": provenance_verifiers["provenanceVerifierMacName"],
        "provenanceVerifierMacPath": provenance_verifiers["provenanceVerifierMacPath"],
        "provenanceVerifierMacPublicUrl": f"/exports/{build_dir.name}/{provenance_verifiers['provenanceVerifierMacName']}",
        "provenanceVerifierLinuxName": provenance_verifiers["provenanceVerifierLinuxName"],
        "provenanceVerifierLinuxPath": provenance_verifiers["provenanceVerifierLinuxPath"],
        "provenanceVerifierLinuxPublicUrl": f"/exports/{build_dir.name}/{provenance_verifiers['provenanceVerifierLinuxName']}",
        "provenanceVerifierWindowsName": provenance_verifiers["provenanceVerifierWindowsName"],
        "provenanceVerifierWindowsPath": provenance_verifiers["provenanceVerifierWindowsPath"],
        "provenanceVerifierWindowsPublicUrl": f"/exports/{build_dir.name}/{provenance_verifiers['provenanceVerifierWindowsName']}",
        "iconPngPath": str(root_icon_files["pngPath"]),
        "iconIcoPath": str(root_icon_files["icoPath"]),
        "iconPngPublicUrl": f"/exports/{build_dir.name}/{root_icon_files['pngFileName']}",
        "iconIcoPublicUrl": f"/exports/{build_dir.name}/{root_icon_files['icoFileName']}",
        "splashPath": str(root_splash_file["path"]),
        "splashPublicUrl": f"/exports/{build_dir.name}/{root_splash_file['fileName']}",
        "readmePath": str(readme_path),
        "playtestGuidePath": str(playtest_guide_path),
        "playtestGuidePublicUrl": f"/exports/{build_dir.name}/{playtest_guide_path.name}",
        "releaseEvidencePackName": evidence_pack_path.name,
        "releaseEvidencePackPath": str(evidence_pack_path),
        "releaseEvidencePackPublicUrl": f"/exports/{build_dir.name}/{evidence_pack_path.name}",
        "assetRightsName": asset_rights_files["assetRightsName"],
        "assetRightsPath": asset_rights_files["assetRightsPath"],
        "assetRightsPublicUrl": f"/exports/{build_dir.name}/{asset_rights_files['assetRightsName']}",
        "assetRightsReportName": asset_rights_files["assetRightsReportName"],
        "assetRightsReportPath": asset_rights_files["assetRightsReportPath"],
        "assetRightsReportPublicUrl": f"/exports/{build_dir.name}/{asset_rights_files['assetRightsReportName']}",
        "assetRightsCsvName": asset_rights_files["assetRightsCsvName"],
        "assetRightsCsvPath": asset_rights_files["assetRightsCsvPath"],
        "assetRightsCsvPublicUrl": f"/exports/{build_dir.name}/{asset_rights_files['assetRightsCsvName']}",
        "assetRightsReadinessPercent": asset_rights_files["assetRightsReadinessPercent"],
        "assetRightsBlockerCount": asset_rights_files["assetRightsBlockerCount"],
        "assetRightsWarningCount": asset_rights_files["assetRightsWarningCount"],
        "audioCueSheetName": audio_cue_sheet_files["audioCueSheetName"],
        "audioCueSheetPath": audio_cue_sheet_files["audioCueSheetPath"],
        "audioCueSheetPublicUrl": f"/exports/{build_dir.name}/{audio_cue_sheet_files['audioCueSheetName']}",
        "audioCueSheetReportName": audio_cue_sheet_files["audioCueSheetReportName"],
        "audioCueSheetReportPath": audio_cue_sheet_files["audioCueSheetReportPath"],
        "audioCueSheetReportPublicUrl": f"/exports/{build_dir.name}/{audio_cue_sheet_files['audioCueSheetReportName']}",
        "audioCueSheetCsvName": audio_cue_sheet_files["audioCueSheetCsvName"],
        "audioCueSheetCsvPath": audio_cue_sheet_files["audioCueSheetCsvPath"],
        "audioCueSheetCsvPublicUrl": f"/exports/{build_dir.name}/{audio_cue_sheet_files['audioCueSheetCsvName']}",
        "audioCueSheetReadinessPercent": audio_cue_sheet_files["audioCueSheetReadinessPercent"],
        "audioCueSheetCueCount": audio_cue_sheet_files["audioCueSheetCueCount"],
        "audioCueSheetBlockerCount": audio_cue_sheet_files["audioCueSheetBlockerCount"],
        "audioCueSheetWarningCount": audio_cue_sheet_files["audioCueSheetWarningCount"],
        "stageDirectionName": stage_direction_files["stageDirectionName"],
        "stageDirectionPath": stage_direction_files["stageDirectionPath"],
        "stageDirectionPublicUrl": f"/exports/{build_dir.name}/{stage_direction_files['stageDirectionName']}",
        "stageDirectionReportName": stage_direction_files["stageDirectionReportName"],
        "stageDirectionReportPath": stage_direction_files["stageDirectionReportPath"],
        "stageDirectionReportPublicUrl": f"/exports/{build_dir.name}/{stage_direction_files['stageDirectionReportName']}",
        "stageDirectionCsvName": stage_direction_files["stageDirectionCsvName"],
        "stageDirectionCsvPath": stage_direction_files["stageDirectionCsvPath"],
        "stageDirectionCsvPublicUrl": f"/exports/{build_dir.name}/{stage_direction_files['stageDirectionCsvName']}",
        "stageDirectionReadinessPercent": stage_direction_files["stageDirectionReadinessPercent"],
        "stageDirectionEventCount": stage_direction_files["stageDirectionEventCount"],
        "stageDirectionBlockerCount": stage_direction_files["stageDirectionBlockerCount"],
        "stageDirectionWarningCount": stage_direction_files["stageDirectionWarningCount"],
        "presentationTimelineName": presentation_timeline_files["presentationTimelineName"],
        "presentationTimelinePath": presentation_timeline_files["presentationTimelinePath"],
        "presentationTimelinePublicUrl": f"/exports/{build_dir.name}/{presentation_timeline_files['presentationTimelineName']}",
        "presentationTimelineReportName": presentation_timeline_files["presentationTimelineReportName"],
        "presentationTimelineReportPath": presentation_timeline_files["presentationTimelineReportPath"],
        "presentationTimelineReportPublicUrl": f"/exports/{build_dir.name}/{presentation_timeline_files['presentationTimelineReportName']}",
        "presentationTimelineCsvName": presentation_timeline_files["presentationTimelineCsvName"],
        "presentationTimelineCsvPath": presentation_timeline_files["presentationTimelineCsvPath"],
        "presentationTimelineCsvPublicUrl": f"/exports/{build_dir.name}/{presentation_timeline_files['presentationTimelineCsvName']}",
        "presentationTimelineReadinessPercent": presentation_timeline_files["presentationTimelineReadinessPercent"],
        "presentationTimelineEventCount": presentation_timeline_files["presentationTimelineEventCount"],
        "presentationTimelineBlockerCount": presentation_timeline_files["presentationTimelineBlockerCount"],
        "presentationTimelineWarningCount": presentation_timeline_files["presentationTimelineWarningCount"],
        "routePlaytestWorkbookName": story_route_map["routePlaytestWorkbookName"],
        "routePlaytestWorkbookPath": story_route_map["routePlaytestWorkbookPath"],
        "routePlaytestWorkbookPublicUrl": f"/exports/{build_dir.name}/{story_route_map['routePlaytestWorkbookName']}",
        "routePlaytestWorkbookReportName": story_route_map["routePlaytestWorkbookReportName"],
        "routePlaytestWorkbookReportPath": story_route_map["routePlaytestWorkbookReportPath"],
        "routePlaytestWorkbookReportPublicUrl": f"/exports/{build_dir.name}/{story_route_map['routePlaytestWorkbookReportName']}",
        "routePlaytestWorkbookCsvName": story_route_map["routePlaytestWorkbookCsvName"],
        "routePlaytestWorkbookCsvPath": story_route_map["routePlaytestWorkbookCsvPath"],
        "routePlaytestWorkbookCsvPublicUrl": f"/exports/{build_dir.name}/{story_route_map['routePlaytestWorkbookCsvName']}",
        "routePlaytestReadinessPercent": story_route_map["routePlaytestReadinessPercent"],
        "routePlaytestRouteCaseCount": story_route_map["routePlaytestRouteCaseCount"],
        "routePlaytestEndingCaseCount": story_route_map["routePlaytestEndingCaseCount"],
        "routePlaytestBlockedCaseCount": story_route_map["routePlaytestBlockedCaseCount"],
        "choiceConsequenceName": story_route_map["choiceConsequenceName"],
        "choiceConsequencePath": story_route_map["choiceConsequencePath"],
        "choiceConsequencePublicUrl": f"/exports/{build_dir.name}/{story_route_map['choiceConsequenceName']}",
        "choiceConsequenceReportName": story_route_map["choiceConsequenceReportName"],
        "choiceConsequenceReportPath": story_route_map["choiceConsequenceReportPath"],
        "choiceConsequenceReportPublicUrl": f"/exports/{build_dir.name}/{story_route_map['choiceConsequenceReportName']}",
        "choiceConsequenceCsvName": story_route_map["choiceConsequenceCsvName"],
        "choiceConsequenceCsvPath": story_route_map["choiceConsequenceCsvPath"],
        "choiceConsequenceCsvPublicUrl": f"/exports/{build_dir.name}/{story_route_map['choiceConsequenceCsvName']}",
        "choiceConsequenceReadinessPercent": story_route_map["choiceConsequenceReadinessPercent"],
        "choiceConsequenceOptionCount": story_route_map["choiceConsequenceOptionCount"],
        "choiceConsequenceBlockerCount": story_route_map["choiceConsequenceBlockerCount"],
        "choiceConsequenceWarningCount": story_route_map["choiceConsequenceWarningCount"],
        "variableInfluenceName": story_route_map["variableInfluenceName"],
        "variableInfluencePath": story_route_map["variableInfluencePath"],
        "variableInfluencePublicUrl": f"/exports/{build_dir.name}/{story_route_map['variableInfluenceName']}",
        "variableInfluenceReportName": story_route_map["variableInfluenceReportName"],
        "variableInfluenceReportPath": story_route_map["variableInfluenceReportPath"],
        "variableInfluenceReportPublicUrl": f"/exports/{build_dir.name}/{story_route_map['variableInfluenceReportName']}",
        "variableInfluenceCsvName": story_route_map["variableInfluenceCsvName"],
        "variableInfluenceCsvPath": story_route_map["variableInfluenceCsvPath"],
        "variableInfluenceCsvPublicUrl": f"/exports/{build_dir.name}/{story_route_map['variableInfluenceCsvName']}",
        "variableInfluenceReadinessPercent": story_route_map["variableInfluenceReadinessPercent"],
        "variableInfluenceVariableCount": story_route_map["variableInfluenceVariableCount"],
        "variableInfluenceBlockerCount": story_route_map["variableInfluenceBlockerCount"],
        "variableInfluenceWarningCount": story_route_map["variableInfluenceWarningCount"],
        "voiceProductionName": voice_production_files["voiceProductionName"],
        "voiceProductionPath": voice_production_files["voiceProductionPath"],
        "voiceProductionPublicUrl": f"/exports/{build_dir.name}/{voice_production_files['voiceProductionName']}",
        "voiceProductionReportName": voice_production_files["voiceProductionReportName"],
        "voiceProductionReportPath": voice_production_files["voiceProductionReportPath"],
        "voiceProductionReportPublicUrl": f"/exports/{build_dir.name}/{voice_production_files['voiceProductionReportName']}",
        "voiceProductionCsvName": voice_production_files["voiceProductionCsvName"],
        "voiceProductionCsvPath": voice_production_files["voiceProductionCsvPath"],
        "voiceProductionCsvPublicUrl": f"/exports/{build_dir.name}/{voice_production_files['voiceProductionCsvName']}",
        "voiceProductionReadyPercent": voice_production_files["voiceProductionReadyPercent"],
        "voiceProductionLineCount": voice_production_files["voiceProductionLineCount"],
        "voiceProductionBlockerCount": voice_production_files["voiceProductionBlockerCount"],
        "voiceProductionWarningCount": voice_production_files["voiceProductionWarningCount"],
        "storyRouteMapName": story_route_map["storyRouteMapName"],
        "storyRouteMapPath": story_route_map["storyRouteMapPath"],
        "storyRouteMapPublicUrl": f"/exports/{build_dir.name}/{story_route_map['storyRouteMapName']}",
        "storyRouteMapReportName": story_route_map["storyRouteMapReportName"],
        "storyRouteMapReportPath": story_route_map["storyRouteMapReportPath"],
        "storyRouteMapReportPublicUrl": f"/exports/{build_dir.name}/{story_route_map['storyRouteMapReportName']}",
        "storyRouteMapStatus": story_route_map["storyRouteMapStatus"],
        "localizationAuditName": localization_audit["localizationAuditName"],
        "localizationAuditPath": localization_audit["localizationAuditPath"],
        "localizationAuditPublicUrl": f"/exports/{build_dir.name}/{localization_audit['localizationAuditName']}",
        "localizationAuditReportName": localization_audit["localizationAuditReportName"],
        "localizationAuditReportPath": localization_audit["localizationAuditReportPath"],
        "localizationAuditReportPublicUrl": f"/exports/{build_dir.name}/{localization_audit['localizationAuditReportName']}",
        "localizationAuditStatus": localization_audit["localizationAuditStatus"],
        "localizationAuditCompletionPercent": localization_audit["localizationAuditCompletionPercent"],
        "releaseReadinessSummaryName": release_readiness["releaseReadinessSummaryName"],
        "releaseReadinessSummaryPath": release_readiness["releaseReadinessSummaryPath"],
        "releaseReadinessSummaryPublicUrl": f"/exports/{build_dir.name}/{release_readiness['releaseReadinessSummaryName']}",
        "releaseReadinessReportName": release_readiness["releaseReadinessReportName"],
        "releaseReadinessReportPath": release_readiness["releaseReadinessReportPath"],
        "releaseReadinessReportPublicUrl": f"/exports/{build_dir.name}/{release_readiness['releaseReadinessReportName']}",
        "releaseReadinessStatus": release_readiness["releaseReadinessStatus"],
        "releaseReadinessScore": release_readiness["releaseReadinessScore"],
        "copiedAssets": copied_assets,
        "missingAssets": len(missing_assets),
        "missingAssetNames": [asset.get("name") or asset.get("id") or "未命名素材" for asset in missing_assets[:5]],
        "runtimeArchLabel": get_nwjs_runtime_config(NWJS_GAME_PLATFORM_MACOS).get("archLabel") or "",
    }


def export_linux_nwjs_build() -> dict:
    build_dir = create_export_build_dir("linux_build")
    bundle = load_project_bundle()
    runtime_guide_path = ensure_local_nwjs_runtime_dropin_guide()
    app_dir = build_dir / "app"
    app_dir.mkdir(parents=True, exist_ok=True)
    export_assets_doc, copied_assets, missing_assets = copy_assets_for_export(bundle["assets"], app_dir)
    export_payload = build_export_payload(bundle, export_assets_doc, copied_assets, missing_assets)
    release_version = get_export_release_version(bundle["project"])
    splash_file = write_export_splash_asset(app_dir, bundle["project"], release_version, "Canvasia Engine Linux 桌面发布包")
    root_splash_file = write_export_splash_asset(build_dir, bundle["project"], release_version, "Canvasia Engine Linux 桌面发布包")
    export_payload["buildInfo"]["releaseVersion"] = release_version
    export_payload["buildInfo"]["exportTargetLabel"] = "Linux 桌面包"
    export_payload["buildInfo"]["splashImageUrl"] = splash_file["relativePath"]
    write_export_app_files(app_dir, export_payload)
    icon_png_bytes = build_export_icon_png(bundle["project"])
    icon_ico_bytes = build_export_icon_ico(icon_png_bytes)
    app_icon_files = write_export_icon_files(app_dir, icon_png_bytes, icon_ico_bytes)
    root_icon_files = write_export_icon_files(build_dir, icon_png_bytes, icon_ico_bytes)
    (app_dir / "package.json").write_text(
        json.dumps(
            build_nwjs_package_json(bundle["project"], "Linux 桌面发布包", icon_path=app_icon_files["pngRelativePath"]),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    package_path = build_dir / "package.nw"
    create_package_nw_archive(app_dir, package_path)
    runtime_dir, runtime_downloaded, runtime_source_label, runtime_source_path = ensure_nwjs_runtime(NWJS_GAME_PLATFORM_LINUX)
    for runtime_path in runtime_dir.iterdir():
        target_path = build_dir / runtime_path.name
        if runtime_path.is_dir():
            copytree_with_symlinks(runtime_path, target_path)
        else:
            shutil.copy2(runtime_path, target_path)

    executable_name = sanitize_export_filename(bundle["project"].get("title") or "") or ""
    if executable_name in {"", "asset"}:
        executable_name = sanitize_export_filename(bundle["project"].get("projectId") or "") or "CanvasiaGame"

    default_executable = build_dir / "nw"
    launcher_path = build_dir / executable_name
    if not default_executable.is_file():
        raise ValueError("Linux 运行壳复制完成了，但没有找到 nw。")
    shutil.copy2(default_executable, launcher_path)
    launcher_path.chmod(0o755)

    start_helper_path = write_linux_start_helper(build_dir, executable_name)
    manifest = build_export_manifest(
        bundle,
        target=EXPORT_TARGET_LINUX_NWJS,
        target_label="Linux 桌面包",
        build_id=build_dir.name,
        copied_assets=copied_assets,
        missing_assets=missing_assets,
        extra_files={
            "launcher": executable_name,
            "archive": f"{build_dir.name}.tar.gz",
            "appEntry": "app/index.html",
            "appPlayerJs": "app/player.js",
            "appRuntimeConditions": "app/runtime_conditions.js",
            "appRuntimeControls": "app/runtime_controls.js",
            "appRuntimeSettings": "app/runtime_settings.js",
            "appRuntimeAudio": "app/runtime_audio.js",
            "appRuntimePreload": "app/runtime_preload.js",
            "appRuntimePreloadManifest": f"app/{RUNTIME_PRELOAD_MANIFEST_FILE_NAME}",
            "appRuntimePreloadReport": f"app/{RUNTIME_PRELOAD_REPORT_FILE_NAME}",
            "playtestGuide": EXPORT_PLAYTEST_GUIDE_FILE_NAME,
            "releaseEvidencePack": EXPORT_RELEASE_EVIDENCE_PACK_NAME,
            "assetRights": EXPORT_ASSET_RIGHTS_JSON_NAME,
            "assetRightsReport": EXPORT_ASSET_RIGHTS_REPORT_NAME,
            "assetRightsCsv": EXPORT_ASSET_RIGHTS_CSV_NAME,
            "audioCueSheet": EXPORT_AUDIO_CUE_SHEET_JSON_NAME,
            "audioCueSheetReport": EXPORT_AUDIO_CUE_SHEET_REPORT_NAME,
            "audioCueSheetCsv": EXPORT_AUDIO_CUE_SHEET_CSV_NAME,
            "stageDirection": EXPORT_STAGE_DIRECTION_JSON_NAME,
            "stageDirectionReport": EXPORT_STAGE_DIRECTION_REPORT_NAME,
            "stageDirectionCsv": EXPORT_STAGE_DIRECTION_CSV_NAME,
            "presentationTimeline": EXPORT_PRESENTATION_TIMELINE_JSON_NAME,
            "presentationTimelineReport": EXPORT_PRESENTATION_TIMELINE_REPORT_NAME,
            "presentationTimelineCsv": EXPORT_PRESENTATION_TIMELINE_CSV_NAME,
            "routePlaytestWorkbook": EXPORT_ROUTE_PLAYTEST_WORKBOOK_JSON_NAME,
            "routePlaytestWorkbookReport": EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME,
            "routePlaytestWorkbookCsv": EXPORT_ROUTE_PLAYTEST_WORKBOOK_CSV_NAME,
            "choiceConsequence": EXPORT_CHOICE_CONSEQUENCE_JSON_NAME,
            "choiceConsequenceReport": EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME,
            "choiceConsequenceCsv": EXPORT_CHOICE_CONSEQUENCE_CSV_NAME,
            "variableInfluence": EXPORT_VARIABLE_INFLUENCE_JSON_NAME,
            "variableInfluenceReport": EXPORT_VARIABLE_INFLUENCE_REPORT_NAME,
            "variableInfluenceCsv": EXPORT_VARIABLE_INFLUENCE_CSV_NAME,
            "voiceProduction": EXPORT_VOICE_PRODUCTION_JSON_NAME,
            "voiceProductionReport": EXPORT_VOICE_PRODUCTION_REPORT_NAME,
            "voiceProductionCsv": EXPORT_VOICE_PRODUCTION_CSV_NAME,
            "storyRouteMap": EXPORT_STORY_ROUTE_MAP_JSON_NAME,
            "storyRouteMapReport": EXPORT_STORY_ROUTE_MAP_REPORT_NAME,
            "localizationAudit": EXPORT_LOCALIZATION_AUDIT_JSON_NAME,
            "localizationAuditReport": EXPORT_LOCALIZATION_AUDIT_REPORT_NAME,
            "releaseReadinessSummary": EXPORT_RELEASE_READINESS_JSON_NAME,
            "releaseReadinessReport": EXPORT_RELEASE_READINESS_REPORT_NAME,
            "unlockableContentManifest": f"app/{UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME}",
            "unlockableContentReport": f"app/{UNLOCKABLE_CONTENT_REPORT_FILE_NAME}",
            "appPackage": "app/package.json",
            "iconPng": root_icon_files["pngFileName"],
            "iconIco": root_icon_files["icoFileName"],
            "launchSplash": root_splash_file["fileName"],
            "runtimeGuide": str(runtime_guide_path),
            "startHelper": start_helper_path.name,
        },
        runtime_info={
            "mode": "nwjs",
            "modeLabel": "NW.js 原生 Linux 可执行目录",
            "packageMode": "linux_folder",
            "packageModeLabel": "原生 Linux 可执行目录",
            "version": NWJS_RUNTIME_VERSION,
            "warning": "",
            "sourceLabel": runtime_source_label,
            "sourcePath": runtime_source_path,
        },
    )
    manifest_path = write_export_manifest(build_dir, manifest)
    asset_rights_files = write_export_asset_rights_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    audio_cue_sheet_files = write_export_audio_cue_sheet_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    stage_direction_files = write_export_stage_direction_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    presentation_timeline_files = write_export_presentation_timeline_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    voice_production_files = write_export_voice_production_files(build_dir, bundle=bundle, assets_doc=export_assets_doc)
    readme_path = write_linux_package_readme(
        build_dir,
        executable_name,
        start_helper_path.name,
        runtime_downloaded,
        runtime_source_label,
        manifest_path.name,
        release_version,
    )
    launch_steps = [
        f"优先运行 `./{start_helper_path.name}`。",
        f"也可以直接运行 `./{executable_name}`。",
        "如果脚本没有执行权限，先运行 `chmod +x 启动游戏.sh`。",
        "对外发送时请压缩整个导出文件夹，不要只发送单个可执行文件。",
    ]
    runtime_notes = [f"当前运行壳：NW.js {NWJS_RUNTIME_VERSION}。"]
    playtest_guide_path = write_export_playtest_guide_file(
        build_dir,
        project=bundle["project"],
        target_label="Linux 桌面包",
        release_version=release_version,
        launch_steps=launch_steps,
        manifest_name=manifest_path.name,
        unlockable_manifest_name=f"app/{UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME}",
        unlockable_report_name=f"app/{UNLOCKABLE_CONTENT_REPORT_FILE_NAME}",
        provenance_name=EXPORT_PROVENANCE_FILE_NAME,
        extra_reports=[
            EXPORT_RELEASE_EVIDENCE_PACK_NAME,
            asset_rights_files["assetRightsReportName"],
            audio_cue_sheet_files["audioCueSheetReportName"],
            stage_direction_files["stageDirectionReportName"],
            voice_production_files["voiceProductionReportName"],
            readme_path.name,
            EXPORT_STORY_ROUTE_MAP_REPORT_NAME,
            EXPORT_LOCALIZATION_AUDIT_REPORT_NAME,
            EXPORT_RELEASE_READINESS_REPORT_NAME,
        ],
        runtime_notes=runtime_notes,
        missing_assets=missing_assets,
    )
    quality_reports = write_export_quality_report_bundle(
        build_dir,
        bundle=bundle,
        project=bundle["project"],
        manifest=manifest,
        missing_assets=missing_assets,
        unlockable_manifest=(export_payload.get("buildInfo") or {}).get("unlockableContentManifest"),
        base_report_files=[
            manifest_path.name,
            readme_path.name,
            playtest_guide_path.name,
        ],
        extra_report_files=[
            f"app/{UNLOCKABLE_CONTENT_REPORT_FILE_NAME}",
            f"app/{UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME}",
            asset_rights_files["assetRightsReportName"],
            asset_rights_files["assetRightsName"],
            asset_rights_files["assetRightsCsvName"],
            audio_cue_sheet_files["audioCueSheetReportName"],
            audio_cue_sheet_files["audioCueSheetName"],
            audio_cue_sheet_files["audioCueSheetCsvName"],
            stage_direction_files["stageDirectionReportName"],
            stage_direction_files["stageDirectionName"],
            stage_direction_files["stageDirectionCsvName"],
            presentation_timeline_files["presentationTimelineReportName"],
            presentation_timeline_files["presentationTimelineName"],
            presentation_timeline_files["presentationTimelineCsvName"],
            EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME,
            EXPORT_ROUTE_PLAYTEST_WORKBOOK_JSON_NAME,
            EXPORT_ROUTE_PLAYTEST_WORKBOOK_CSV_NAME,
            EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME,
            EXPORT_CHOICE_CONSEQUENCE_JSON_NAME,
            EXPORT_CHOICE_CONSEQUENCE_CSV_NAME,
            EXPORT_VARIABLE_INFLUENCE_REPORT_NAME,
            EXPORT_VARIABLE_INFLUENCE_JSON_NAME,
            EXPORT_VARIABLE_INFLUENCE_CSV_NAME,
            voice_production_files["voiceProductionReportName"],
            voice_production_files["voiceProductionName"],
            voice_production_files["voiceProductionCsvName"],
        ],
        platform_notes=[
            f"当前运行壳：NW.js {NWJS_RUNTIME_VERSION}。",
            "Linux 分发前建议在目标发行版确认启动脚本权限和依赖库可用。",
        ],
    )
    story_route_map = quality_reports
    localization_audit = quality_reports
    release_readiness = quality_reports
    evidence_pack_path = write_export_release_evidence_pack_file(
        build_dir,
        project=bundle["project"],
        target_label="Linux 桌面包",
        release_version=release_version,
        manifest_name=manifest_path.name,
        playtest_guide_name=playtest_guide_path.name,
        provenance_name=EXPORT_PROVENANCE_FILE_NAME,
        story_route_map_report_name=story_route_map["storyRouteMapReportName"],
        localization_audit_report_name=localization_audit["localizationAuditReportName"],
        release_readiness_report_name=release_readiness["releaseReadinessReportName"],
        unlockable_report_name=f"app/{UNLOCKABLE_CONTENT_REPORT_FILE_NAME}",
        unlockable_manifest_name=f"app/{UNLOCKABLE_CONTENT_MANIFEST_FILE_NAME}",
        launch_steps=launch_steps,
        runtime_notes=runtime_notes,
        extra_reports=[
            readme_path.name,
            asset_rights_files["assetRightsReportName"],
            audio_cue_sheet_files["audioCueSheetReportName"],
            stage_direction_files["stageDirectionReportName"],
            EXPORT_ROUTE_PLAYTEST_WORKBOOK_REPORT_NAME,
            EXPORT_CHOICE_CONSEQUENCE_REPORT_NAME,
            EXPORT_VARIABLE_INFLUENCE_REPORT_NAME,
            voice_production_files["voiceProductionReportName"],
            f"app/{RUNTIME_PRELOAD_REPORT_FILE_NAME}",
        ],
        missing_assets=missing_assets,
    )
    provenance_verifiers = write_export_provenance_verifier_files(build_dir)
    provenance_roots = [
        app_dir,
        package_path,
        manifest_path,
        readme_path,
        playtest_guide_path,
        evidence_pack_path,
        Path(asset_rights_files["assetRightsReportPath"]),
        Path(asset_rights_files["assetRightsPath"]),
        Path(asset_rights_files["assetRightsCsvPath"]),
        Path(audio_cue_sheet_files["audioCueSheetReportPath"]),
        Path(audio_cue_sheet_files["audioCueSheetPath"]),
        Path(audio_cue_sheet_files["audioCueSheetCsvPath"]),
        Path(stage_direction_files["stageDirectionReportPath"]),
        Path(stage_direction_files["stageDirectionPath"]),
        Path(stage_direction_files["stageDirectionCsvPath"]),
        Path(presentation_timeline_files["presentationTimelineReportPath"]),
        Path(presentation_timeline_files["presentationTimelinePath"]),
        Path(presentation_timeline_files["presentationTimelineCsvPath"]),
        Path(story_route_map["routePlaytestWorkbookReportPath"]),
        Path(story_route_map["routePlaytestWorkbookPath"]),
        Path(story_route_map["routePlaytestWorkbookCsvPath"]),
        Path(story_route_map["choiceConsequenceReportPath"]),
        Path(story_route_map["choiceConsequencePath"]),
        Path(story_route_map["choiceConsequenceCsvPath"]),
        Path(story_route_map["variableInfluenceReportPath"]),
        Path(story_route_map["variableInfluencePath"]),
        Path(story_route_map["variableInfluenceCsvPath"]),
        Path(voice_production_files["voiceProductionReportPath"]),
        Path(voice_production_files["voiceProductionPath"]),
        Path(voice_production_files["voiceProductionCsvPath"]),
        Path(story_route_map["storyRouteMapReportPath"]),
        Path(story_route_map["storyRouteMapPath"]),
        Path(localization_audit["localizationAuditReportPath"]),
        Path(localization_audit["localizationAuditPath"]),
        Path(release_readiness["releaseReadinessReportPath"]),
        Path(release_readiness["releaseReadinessSummaryPath"]),
        start_helper_path,
        root_icon_files["pngPath"],
        root_icon_files["icoPath"],
        root_splash_file["path"],
        *provenance_verifiers["paths"],
    ]
    provenance_file = write_export_provenance_file(build_dir, bundle, manifest, roots=provenance_roots)
    archive_path = Path(shutil.make_archive(str(build_dir), "gztar", root_dir=build_dir.parent, base_dir=build_dir.name))

    return {
        "target": EXPORT_TARGET_LINUX_NWJS,
        "targetLabel": "Linux 桌面包",
        "buildId": build_dir.name,
        "buildPath": str(build_dir),
        "launcherPath": str(launcher_path),
        "launcherFileName": executable_name,
        "startHelperPath": str(start_helper_path),
        "startHelperFileName": start_helper_path.name,
        "archivePath": str(archive_path),
        "archivePublicUrl": f"/exports/{archive_path.name}",
        "runtimeMode": "nwjs",
        "runtimeModeLabel": "NW.js 原生 Linux 可执行目录",
        "packageMode": "linux_folder",
        "packageModeLabel": "原生 Linux 可执行目录",
        "runtimeVersion": NWJS_RUNTIME_VERSION,
        "runtimeDownloaded": runtime_downloaded,
        "runtimeWarning": "",
        "runtimeSourceLabel": runtime_source_label,
        "runtimeSourcePath": runtime_source_path,
        "runtimeGuidePath": str(runtime_guide_path),
        "releaseVersion": release_version,
        "manifestPath": str(manifest_path),
        "manifestPublicUrl": f"/exports/{build_dir.name}/{manifest_path.name}",
        "provenanceName": provenance_file["provenanceName"],
        "provenancePath": provenance_file["provenancePath"],
        "provenancePublicUrl": f"/exports/{build_dir.name}/{provenance_file['provenanceName']}",
        "provenanceSeal": provenance_file["provenanceSeal"],
        "provenanceSummary": provenance_file["provenanceSummary"],
        "provenanceVerifierName": provenance_verifiers["provenanceVerifierName"],
        "provenanceVerifierPath": provenance_verifiers["provenanceVerifierPath"],
        "provenanceVerifierPublicUrl": f"/exports/{build_dir.name}/{provenance_verifiers['provenanceVerifierName']}",
        "provenanceVerifierMacName": provenance_verifiers["provenanceVerifierMacName"],
        "provenanceVerifierMacPath": provenance_verifiers["provenanceVerifierMacPath"],
        "provenanceVerifierMacPublicUrl": f"/exports/{build_dir.name}/{provenance_verifiers['provenanceVerifierMacName']}",
        "provenanceVerifierLinuxName": provenance_verifiers["provenanceVerifierLinuxName"],
        "provenanceVerifierLinuxPath": provenance_verifiers["provenanceVerifierLinuxPath"],
        "provenanceVerifierLinuxPublicUrl": f"/exports/{build_dir.name}/{provenance_verifiers['provenanceVerifierLinuxName']}",
        "provenanceVerifierWindowsName": provenance_verifiers["provenanceVerifierWindowsName"],
        "provenanceVerifierWindowsPath": provenance_verifiers["provenanceVerifierWindowsPath"],
        "provenanceVerifierWindowsPublicUrl": f"/exports/{build_dir.name}/{provenance_verifiers['provenanceVerifierWindowsName']}",
        "iconPngPath": str(root_icon_files["pngPath"]),
        "iconIcoPath": str(root_icon_files["icoPath"]),
        "iconPngPublicUrl": f"/exports/{build_dir.name}/{root_icon_files['pngFileName']}",
        "iconIcoPublicUrl": f"/exports/{build_dir.name}/{root_icon_files['icoFileName']}",
        "splashPath": str(root_splash_file["path"]),
        "splashPublicUrl": f"/exports/{build_dir.name}/{root_splash_file['fileName']}",
        "readmePath": str(readme_path),
        "playtestGuidePath": str(playtest_guide_path),
        "playtestGuidePublicUrl": f"/exports/{build_dir.name}/{playtest_guide_path.name}",
        "releaseEvidencePackName": evidence_pack_path.name,
        "releaseEvidencePackPath": str(evidence_pack_path),
        "releaseEvidencePackPublicUrl": f"/exports/{build_dir.name}/{evidence_pack_path.name}",
        "assetRightsName": asset_rights_files["assetRightsName"],
        "assetRightsPath": asset_rights_files["assetRightsPath"],
        "assetRightsPublicUrl": f"/exports/{build_dir.name}/{asset_rights_files['assetRightsName']}",
        "assetRightsReportName": asset_rights_files["assetRightsReportName"],
        "assetRightsReportPath": asset_rights_files["assetRightsReportPath"],
        "assetRightsReportPublicUrl": f"/exports/{build_dir.name}/{asset_rights_files['assetRightsReportName']}",
        "assetRightsCsvName": asset_rights_files["assetRightsCsvName"],
        "assetRightsCsvPath": asset_rights_files["assetRightsCsvPath"],
        "assetRightsCsvPublicUrl": f"/exports/{build_dir.name}/{asset_rights_files['assetRightsCsvName']}",
        "assetRightsReadinessPercent": asset_rights_files["assetRightsReadinessPercent"],
        "assetRightsBlockerCount": asset_rights_files["assetRightsBlockerCount"],
        "assetRightsWarningCount": asset_rights_files["assetRightsWarningCount"],
        "audioCueSheetName": audio_cue_sheet_files["audioCueSheetName"],
        "audioCueSheetPath": audio_cue_sheet_files["audioCueSheetPath"],
        "audioCueSheetPublicUrl": f"/exports/{build_dir.name}/{audio_cue_sheet_files['audioCueSheetName']}",
        "audioCueSheetReportName": audio_cue_sheet_files["audioCueSheetReportName"],
        "audioCueSheetReportPath": audio_cue_sheet_files["audioCueSheetReportPath"],
        "audioCueSheetReportPublicUrl": f"/exports/{build_dir.name}/{audio_cue_sheet_files['audioCueSheetReportName']}",
        "audioCueSheetCsvName": audio_cue_sheet_files["audioCueSheetCsvName"],
        "audioCueSheetCsvPath": audio_cue_sheet_files["audioCueSheetCsvPath"],
        "audioCueSheetCsvPublicUrl": f"/exports/{build_dir.name}/{audio_cue_sheet_files['audioCueSheetCsvName']}",
        "audioCueSheetReadinessPercent": audio_cue_sheet_files["audioCueSheetReadinessPercent"],
        "audioCueSheetCueCount": audio_cue_sheet_files["audioCueSheetCueCount"],
        "audioCueSheetBlockerCount": audio_cue_sheet_files["audioCueSheetBlockerCount"],
        "audioCueSheetWarningCount": audio_cue_sheet_files["audioCueSheetWarningCount"],
        "stageDirectionName": stage_direction_files["stageDirectionName"],
        "stageDirectionPath": stage_direction_files["stageDirectionPath"],
        "stageDirectionPublicUrl": f"/exports/{build_dir.name}/{stage_direction_files['stageDirectionName']}",
        "stageDirectionReportName": stage_direction_files["stageDirectionReportName"],
        "stageDirectionReportPath": stage_direction_files["stageDirectionReportPath"],
        "stageDirectionReportPublicUrl": f"/exports/{build_dir.name}/{stage_direction_files['stageDirectionReportName']}",
        "stageDirectionCsvName": stage_direction_files["stageDirectionCsvName"],
        "stageDirectionCsvPath": stage_direction_files["stageDirectionCsvPath"],
        "stageDirectionCsvPublicUrl": f"/exports/{build_dir.name}/{stage_direction_files['stageDirectionCsvName']}",
        "stageDirectionReadinessPercent": stage_direction_files["stageDirectionReadinessPercent"],
        "stageDirectionEventCount": stage_direction_files["stageDirectionEventCount"],
        "stageDirectionBlockerCount": stage_direction_files["stageDirectionBlockerCount"],
        "stageDirectionWarningCount": stage_direction_files["stageDirectionWarningCount"],
        "presentationTimelineName": presentation_timeline_files["presentationTimelineName"],
        "presentationTimelinePath": presentation_timeline_files["presentationTimelinePath"],
        "presentationTimelinePublicUrl": f"/exports/{build_dir.name}/{presentation_timeline_files['presentationTimelineName']}",
        "presentationTimelineReportName": presentation_timeline_files["presentationTimelineReportName"],
        "presentationTimelineReportPath": presentation_timeline_files["presentationTimelineReportPath"],
        "presentationTimelineReportPublicUrl": f"/exports/{build_dir.name}/{presentation_timeline_files['presentationTimelineReportName']}",
        "presentationTimelineCsvName": presentation_timeline_files["presentationTimelineCsvName"],
        "presentationTimelineCsvPath": presentation_timeline_files["presentationTimelineCsvPath"],
        "presentationTimelineCsvPublicUrl": f"/exports/{build_dir.name}/{presentation_timeline_files['presentationTimelineCsvName']}",
        "presentationTimelineReadinessPercent": presentation_timeline_files["presentationTimelineReadinessPercent"],
        "presentationTimelineEventCount": presentation_timeline_files["presentationTimelineEventCount"],
        "presentationTimelineBlockerCount": presentation_timeline_files["presentationTimelineBlockerCount"],
        "presentationTimelineWarningCount": presentation_timeline_files["presentationTimelineWarningCount"],
        "routePlaytestWorkbookName": story_route_map["routePlaytestWorkbookName"],
        "routePlaytestWorkbookPath": story_route_map["routePlaytestWorkbookPath"],
        "routePlaytestWorkbookPublicUrl": f"/exports/{build_dir.name}/{story_route_map['routePlaytestWorkbookName']}",
        "routePlaytestWorkbookReportName": story_route_map["routePlaytestWorkbookReportName"],
        "routePlaytestWorkbookReportPath": story_route_map["routePlaytestWorkbookReportPath"],
        "routePlaytestWorkbookReportPublicUrl": f"/exports/{build_dir.name}/{story_route_map['routePlaytestWorkbookReportName']}",
        "routePlaytestWorkbookCsvName": story_route_map["routePlaytestWorkbookCsvName"],
        "routePlaytestWorkbookCsvPath": story_route_map["routePlaytestWorkbookCsvPath"],
        "routePlaytestWorkbookCsvPublicUrl": f"/exports/{build_dir.name}/{story_route_map['routePlaytestWorkbookCsvName']}",
        "routePlaytestReadinessPercent": story_route_map["routePlaytestReadinessPercent"],
        "routePlaytestRouteCaseCount": story_route_map["routePlaytestRouteCaseCount"],
        "routePlaytestEndingCaseCount": story_route_map["routePlaytestEndingCaseCount"],
        "routePlaytestBlockedCaseCount": story_route_map["routePlaytestBlockedCaseCount"],
        "choiceConsequenceName": story_route_map["choiceConsequenceName"],
        "choiceConsequencePath": story_route_map["choiceConsequencePath"],
        "choiceConsequencePublicUrl": f"/exports/{build_dir.name}/{story_route_map['choiceConsequenceName']}",
        "choiceConsequenceReportName": story_route_map["choiceConsequenceReportName"],
        "choiceConsequenceReportPath": story_route_map["choiceConsequenceReportPath"],
        "choiceConsequenceReportPublicUrl": f"/exports/{build_dir.name}/{story_route_map['choiceConsequenceReportName']}",
        "choiceConsequenceCsvName": story_route_map["choiceConsequenceCsvName"],
        "choiceConsequenceCsvPath": story_route_map["choiceConsequenceCsvPath"],
        "choiceConsequenceCsvPublicUrl": f"/exports/{build_dir.name}/{story_route_map['choiceConsequenceCsvName']}",
        "choiceConsequenceReadinessPercent": story_route_map["choiceConsequenceReadinessPercent"],
        "choiceConsequenceOptionCount": story_route_map["choiceConsequenceOptionCount"],
        "choiceConsequenceBlockerCount": story_route_map["choiceConsequenceBlockerCount"],
        "choiceConsequenceWarningCount": story_route_map["choiceConsequenceWarningCount"],
        "variableInfluenceName": story_route_map["variableInfluenceName"],
        "variableInfluencePath": story_route_map["variableInfluencePath"],
        "variableInfluencePublicUrl": f"/exports/{build_dir.name}/{story_route_map['variableInfluenceName']}",
        "variableInfluenceReportName": story_route_map["variableInfluenceReportName"],
        "variableInfluenceReportPath": story_route_map["variableInfluenceReportPath"],
        "variableInfluenceReportPublicUrl": f"/exports/{build_dir.name}/{story_route_map['variableInfluenceReportName']}",
        "variableInfluenceCsvName": story_route_map["variableInfluenceCsvName"],
        "variableInfluenceCsvPath": story_route_map["variableInfluenceCsvPath"],
        "variableInfluenceCsvPublicUrl": f"/exports/{build_dir.name}/{story_route_map['variableInfluenceCsvName']}",
        "variableInfluenceReadinessPercent": story_route_map["variableInfluenceReadinessPercent"],
        "variableInfluenceVariableCount": story_route_map["variableInfluenceVariableCount"],
        "variableInfluenceBlockerCount": story_route_map["variableInfluenceBlockerCount"],
        "variableInfluenceWarningCount": story_route_map["variableInfluenceWarningCount"],
        "voiceProductionName": voice_production_files["voiceProductionName"],
        "voiceProductionPath": voice_production_files["voiceProductionPath"],
        "voiceProductionPublicUrl": f"/exports/{build_dir.name}/{voice_production_files['voiceProductionName']}",
        "voiceProductionReportName": voice_production_files["voiceProductionReportName"],
        "voiceProductionReportPath": voice_production_files["voiceProductionReportPath"],
        "voiceProductionReportPublicUrl": f"/exports/{build_dir.name}/{voice_production_files['voiceProductionReportName']}",
        "voiceProductionCsvName": voice_production_files["voiceProductionCsvName"],
        "voiceProductionCsvPath": voice_production_files["voiceProductionCsvPath"],
        "voiceProductionCsvPublicUrl": f"/exports/{build_dir.name}/{voice_production_files['voiceProductionCsvName']}",
        "voiceProductionReadyPercent": voice_production_files["voiceProductionReadyPercent"],
        "voiceProductionLineCount": voice_production_files["voiceProductionLineCount"],
        "voiceProductionBlockerCount": voice_production_files["voiceProductionBlockerCount"],
        "voiceProductionWarningCount": voice_production_files["voiceProductionWarningCount"],
        "storyRouteMapName": story_route_map["storyRouteMapName"],
        "storyRouteMapPath": story_route_map["storyRouteMapPath"],
        "storyRouteMapPublicUrl": f"/exports/{build_dir.name}/{story_route_map['storyRouteMapName']}",
        "storyRouteMapReportName": story_route_map["storyRouteMapReportName"],
        "storyRouteMapReportPath": story_route_map["storyRouteMapReportPath"],
        "storyRouteMapReportPublicUrl": f"/exports/{build_dir.name}/{story_route_map['storyRouteMapReportName']}",
        "storyRouteMapStatus": story_route_map["storyRouteMapStatus"],
        "localizationAuditName": localization_audit["localizationAuditName"],
        "localizationAuditPath": localization_audit["localizationAuditPath"],
        "localizationAuditPublicUrl": f"/exports/{build_dir.name}/{localization_audit['localizationAuditName']}",
        "localizationAuditReportName": localization_audit["localizationAuditReportName"],
        "localizationAuditReportPath": localization_audit["localizationAuditReportPath"],
        "localizationAuditReportPublicUrl": f"/exports/{build_dir.name}/{localization_audit['localizationAuditReportName']}",
        "localizationAuditStatus": localization_audit["localizationAuditStatus"],
        "localizationAuditCompletionPercent": localization_audit["localizationAuditCompletionPercent"],
        "releaseReadinessSummaryName": release_readiness["releaseReadinessSummaryName"],
        "releaseReadinessSummaryPath": release_readiness["releaseReadinessSummaryPath"],
        "releaseReadinessSummaryPublicUrl": f"/exports/{build_dir.name}/{release_readiness['releaseReadinessSummaryName']}",
        "releaseReadinessReportName": release_readiness["releaseReadinessReportName"],
        "releaseReadinessReportPath": release_readiness["releaseReadinessReportPath"],
        "releaseReadinessReportPublicUrl": f"/exports/{build_dir.name}/{release_readiness['releaseReadinessReportName']}",
        "releaseReadinessStatus": release_readiness["releaseReadinessStatus"],
        "releaseReadinessScore": release_readiness["releaseReadinessScore"],
        "copiedAssets": copied_assets,
        "missingAssets": len(missing_assets),
        "missingAssetNames": [asset.get("name") or asset.get("id") or "未命名素材" for asset in missing_assets[:5]],
    }


def export_editor_desktop_build() -> dict:
    build_dir = create_export_build_dir("editor_build")
    target_label = get_editor_package_target_label()
    bundle_dir = build_dir / EDITOR_BUNDLE_DIR_NAME
    distribution_config, distribution_config_path = load_editor_distribution_config()
    copy_editor_distribution_tree(bundle_dir)
    embedded_runtime = prepare_editor_embedded_runtime(bundle_dir)
    distribution_snapshot_path = write_editor_distribution_snapshot(build_dir, distribution_config)
    signing_support_files = copy_editor_signing_support_files(build_dir)

    icon_png_bytes = build_export_icon_png(
        {"projectId": "editor_package", "title": distribution_config.get("productName") or "Canvasia Engine Editor"}
    )
    icon_ico_bytes = build_export_icon_ico(icon_png_bytes)
    root_icon_files = write_export_icon_files(build_dir, icon_png_bytes, icon_ico_bytes)
    bundle_icon_files = write_export_icon_files(bundle_dir, icon_png_bytes, icon_ico_bytes)
    splash_file = write_export_splash_asset(
        build_dir,
        {"title": distribution_config.get("productName") or "Canvasia Engine Editor", "projectId": "editor_package"},
        EDITOR_PACKAGE_VERSION,
        target_label,
    )
    bundle_splash_file = write_export_splash_asset(
        bundle_dir,
        {"title": distribution_config.get("productName") or "Canvasia Engine Editor", "projectId": "editor_package"},
        EDITOR_PACKAGE_VERSION,
        target_label,
    )
    launchers = write_editor_root_launchers(build_dir)
    readme_path = write_editor_package_readme(build_dir, target_label, runtime_info=embedded_runtime)

    mac_app_path = None
    mac_installer_path = None
    windows_installer_script = None
    windows_installer_result = {
        "canCompile": False,
        "compiled": False,
        "statusLabel": "未编译（待配置 Inno Setup 编译器）",
        "messages": [],
        "compilerPath": "",
        "runnerPath": "",
        "installerPath": "",
        "installerName": "",
    }
    linux_install_script = None
    windows_signing_result = {
        "canSign": False,
        "installerSigned": False,
        "statusLabel": "未签名（待配置 Windows 证书/签名工具）",
        "messages": [],
        "signToolPath": "",
        "signToolRunner": "",
        "timestampUrl": "",
    }
    signing_result = {
        "statusLabel": "当前平台未执行签名",
        "appSigned": False,
        "installerSigned": False,
        "notarized": False,
        "messages": [],
    }
    if should_build_editor_macos_app():
        mac_app_path = create_macos_editor_app_bundle(build_dir, bundle_dir, distribution_config, root_icon_files["pngPath"])
        mac_installer_path = build_macos_editor_installer(build_dir, mac_app_path, distribution_config)
        signing_result = attempt_macos_editor_signing(build_dir, mac_app_path, mac_installer_path, distribution_config)
    elif os.name == "nt":
        windows_installer_script = write_editor_windows_installer_script(build_dir, distribution_config)
        windows_installer_result = attempt_windows_editor_installer_compile(
            build_dir,
            windows_installer_script,
            distribution_config,
        )
        windows_signing_result = attempt_windows_editor_signing(
            Path(windows_installer_result["installerPath"]) if windows_installer_result.get("installerPath") else None,
            distribution_config,
        )
        windows_installer_result["installerSigned"] = bool(windows_signing_result.get("installerSigned"))
        windows_installer_result["signingStatusLabel"] = (
            windows_signing_result.get("statusLabel") or "未签名（待配置 Windows 证书/签名工具）"
        )
    elif sys.platform.startswith("linux"):
        write_editor_linux_desktop_entry(build_dir, distribution_config)
        linux_install_script = write_editor_linux_install_script(build_dir, distribution_config)

    extra_notes = []
    if windows_installer_script:
        extra_notes.append(f"- 当前包里已附带 Windows 安装脚本模板：{windows_installer_script.name}")
        extra_notes.append(f"- Windows 安装器编译状态：{windows_installer_result.get('statusLabel')}")
        if windows_installer_result.get("installerName"):
            extra_notes.append(f"- 已生成 Windows 安装器：{windows_installer_result['installerName']}")
        extra_notes.append(f"- Windows 安装器签名状态：{windows_signing_result.get('statusLabel')}")
    if linux_install_script:
        extra_notes.append(f"- 当前包里已附带 Linux 安装脚本：{linux_install_script.name}")
    commercial_readme_path = write_editor_commercial_readme(
        build_dir,
        target_label,
        distribution_config_path,
        distribution_snapshot_path,
        {
            **signing_result,
            "windowsInstallerStatusLabel": windows_installer_result.get("statusLabel"),
            "windowsSigningStatusLabel": windows_signing_result.get("statusLabel"),
            "messages": [
                *(signing_result.get("messages") or []),
                *(windows_installer_result.get("messages") or []),
                *(windows_signing_result.get("messages") or []),
            ],
        },
        distribution_config,
        extra_notes=extra_notes,
    )

    archive_path = Path(shutil.make_archive(str(build_dir), "zip", root_dir=build_dir.parent, base_dir=build_dir.name))
    manifest = build_editor_package_manifest(
        build_id=build_dir.name,
        target_label=target_label,
        archive_name=archive_path.name,
        includes_macos_app=bool(mac_app_path),
        includes_macos_installer=bool(mac_installer_path),
        runtime_info=embedded_runtime,
        distribution_config=distribution_config,
        signing_result=signing_result,
        windows_installer_result=windows_installer_result,
    )
    manifest_path = write_editor_package_manifest(build_dir, manifest)

    return {
        "target": EXPORT_TARGET_EDITOR_DESKTOP,
        "targetLabel": target_label,
        "buildId": build_dir.name,
        "buildPath": str(build_dir),
        "bundleDirPath": str(bundle_dir),
        "bundleDirName": bundle_dir.name,
        "archivePath": str(archive_path),
        "archivePublicUrl": f"/exports/{archive_path.name}",
        "releaseVersion": EDITOR_PACKAGE_VERSION,
        "manifestPath": str(manifest_path),
        "manifestPublicUrl": f"/exports/{build_dir.name}/{manifest_path.name}",
        "iconPngPath": str(root_icon_files["pngPath"]),
        "iconIcoPath": str(root_icon_files["icoPath"]),
        "iconPngPublicUrl": f"/exports/{build_dir.name}/{root_icon_files['pngFileName']}",
        "iconIcoPublicUrl": f"/exports/{build_dir.name}/{root_icon_files['icoFileName']}",
        "splashPath": str(splash_file["path"]),
        "splashPublicUrl": f"/exports/{build_dir.name}/{splash_file['fileName']}",
        "distributionConfigPath": str(distribution_config_path),
        "distributionSnapshotPath": str(distribution_snapshot_path),
        "signingGuidePath": signing_support_files["guidePath"],
        "signingGuideName": signing_support_files["guideName"],
        "signingGuidePublicUrl": f"/exports/{build_dir.name}/{signing_support_files['guideName']}",
        "signingEnvExamplePath": signing_support_files["envExamplePath"],
        "signingEnvExampleName": signing_support_files["envExampleName"],
        "signingEnvExamplePublicUrl": f"/exports/{build_dir.name}/{signing_support_files['envExampleName']}",
        "signingCheckScriptPath": signing_support_files["checkScriptPath"],
        "signingCheckScriptName": signing_support_files["checkScriptName"],
        "signingCheckScriptPublicUrl": f"/exports/{build_dir.name}/{signing_support_files['checkScriptName']}",
        "signingCheckCommandPath": signing_support_files["checkCommandPath"],
        "signingCheckCommandName": signing_support_files["checkCommandName"],
        "signingCheckCommandPublicUrl": f"/exports/{build_dir.name}/{signing_support_files['checkCommandName']}",
        "commercialReadmePath": str(commercial_readme_path),
        "bundleIconPngPath": str(bundle_icon_files["pngPath"]),
        "bundleIconIcoPath": str(bundle_icon_files["icoPath"]),
        "bundleSplashPath": str(bundle_splash_file["path"]),
        "readmePath": str(readme_path),
        "commandLauncherPath": str(launchers["commandPath"]),
        "commandLauncherFileName": launchers["commandPath"].name,
        "windowsLauncherPath": str(launchers["windowsPath"]),
        "windowsLauncherFileName": launchers["windowsPath"].name,
        "macAppPath": str(mac_app_path) if mac_app_path else "",
        "macAppName": mac_app_path.name if mac_app_path else "",
        "macInstallerPath": str(mac_installer_path) if mac_installer_path else "",
        "macInstallerName": mac_installer_path.name if mac_installer_path else "",
        "macInstallerPublicUrl": f"/exports/{build_dir.name}/{mac_installer_path.name}" if mac_installer_path else "",
        "windowsInstallerScriptPath": str(windows_installer_script) if windows_installer_script else "",
        "windowsInstallerScriptName": windows_installer_script.name if windows_installer_script else "",
        "windowsInstallerScriptPublicUrl": (
            f"/exports/{build_dir.name}/{windows_installer_script.name}" if windows_installer_script else ""
        ),
        "windowsInstallerExePath": windows_installer_result.get("installerPath") or "",
        "windowsInstallerExeName": windows_installer_result.get("installerName") or "",
        "windowsInstallerExePublicUrl": (
            f"/exports/{build_dir.name}/{windows_installer_result['installerName']}"
            if windows_installer_result.get("installerName")
            else ""
        ),
        "windowsInstallerCompileStatusLabel": windows_installer_result.get("statusLabel")
        or "未编译（待配置 Inno Setup 编译器）",
        "windowsInstallerCompilerPath": windows_installer_result.get("compilerPath") or "",
        "windowsInstallerRunnerPath": windows_installer_result.get("runnerPath") or "",
        "windowsSigningStatusLabel": windows_signing_result.get("statusLabel")
        or "未签名（待配置 Windows 证书/签名工具）",
        "windowsInstallerSigned": bool(windows_signing_result.get("installerSigned")),
        "windowsSignToolPath": windows_signing_result.get("signToolPath") or "",
        "windowsSignToolRunnerPath": windows_signing_result.get("signToolRunner") or "",
        "windowsTimestampUrl": windows_signing_result.get("timestampUrl") or "",
        "linuxInstallScriptPath": str(linux_install_script) if linux_install_script else "",
        "linuxInstallScriptName": linux_install_script.name if linux_install_script else "",
        "requiresPython3": not embedded_runtime.get("included"),
        "embeddedRuntimeIncluded": bool(embedded_runtime.get("included")),
        "embeddedRuntimeMode": embedded_runtime.get("mode") or EDITOR_RUNTIME_SOURCE_SYSTEM,
        "embeddedRuntimeModeLabel": embedded_runtime.get("modeLabel") or "系统 Python 启动",
        "embeddedRuntimePath": embedded_runtime.get("runtimeDirPath") or "",
        "embeddedRuntimePythonPath": embedded_runtime.get("pythonPath") or "",
        "embeddedRuntimeSourceLabel": embedded_runtime.get("sourceLabel") or "",
        "embeddedRuntimeSourcePath": embedded_runtime.get("sourcePath") or "",
        "embeddedRuntimeWarning": embedded_runtime.get("warning") or "",
        "signingStatusLabel": signing_result.get("statusLabel") or "未签名（待填写开发者身份）",
        "appSigned": bool(signing_result.get("appSigned")),
        "installerSigned": bool(signing_result.get("installerSigned")),
        "notarized": bool(signing_result.get("notarized")),
        "signingMessages": [
            *(signing_result.get("messages") or []),
            *(windows_signing_result.get("messages") or []),
        ],
    }


def export_editor_desktop_suite_build() -> dict:
    build_dir = create_export_build_dir("editor_suite")
    distribution_config, distribution_config_path = load_editor_distribution_config()
    package_results = [
        export_editor_suite_platform_package(build_dir, EDITOR_PLATFORM_MACOS, distribution_config, distribution_config_path),
        export_editor_suite_platform_package(build_dir, EDITOR_PLATFORM_WINDOWS, distribution_config, distribution_config_path),
        export_editor_suite_platform_package(build_dir, EDITOR_PLATFORM_LINUX, distribution_config, distribution_config_path),
    ]
    suite_manifest = build_editor_suite_manifest(build_dir.name, package_results, distribution_config)
    manifest_path = write_editor_suite_manifest(build_dir, suite_manifest)
    distribution_snapshot_path = write_editor_distribution_snapshot(build_dir, distribution_config)
    signing_support_files = copy_editor_signing_support_files(build_dir)
    readme_path = write_editor_suite_readme(build_dir, package_results, distribution_config_path)

    return {
        "target": EXPORT_TARGET_EDITOR_DESKTOP_SUITE,
        "targetLabel": "三系统编辑器套装",
        "buildId": build_dir.name,
        "buildPath": str(build_dir),
        "manifestPath": str(manifest_path),
        "manifestPublicUrl": f"/exports/{build_dir.name}/{manifest_path.name}",
        "readmePath": str(readme_path),
        "distributionConfigPath": str(distribution_config_path),
        "distributionSnapshotPath": str(distribution_snapshot_path),
        "signingGuidePath": signing_support_files["guidePath"],
        "signingGuideName": signing_support_files["guideName"],
        "signingGuidePublicUrl": f"/exports/{build_dir.name}/{signing_support_files['guideName']}",
        "signingEnvExamplePath": signing_support_files["envExamplePath"],
        "signingEnvExampleName": signing_support_files["envExampleName"],
        "signingEnvExamplePublicUrl": f"/exports/{build_dir.name}/{signing_support_files['envExampleName']}",
        "signingCheckScriptPath": signing_support_files["checkScriptPath"],
        "signingCheckScriptName": signing_support_files["checkScriptName"],
        "signingCheckScriptPublicUrl": f"/exports/{build_dir.name}/{signing_support_files['checkScriptName']}",
        "signingCheckCommandPath": signing_support_files["checkCommandPath"],
        "signingCheckCommandName": signing_support_files["checkCommandName"],
        "signingCheckCommandPublicUrl": f"/exports/{build_dir.name}/{signing_support_files['checkCommandName']}",
        "packages": package_results,
        "releaseVersion": EDITOR_PACKAGE_VERSION,
    }


def export_project_build(target: str = EXPORT_TARGET_WEB) -> dict:
    target_name = str(target or EXPORT_TARGET_WEB).strip() or EXPORT_TARGET_WEB
    if target_name == EXPORT_TARGET_NATIVE_RUNTIME:
        return export_native_runtime_build()
    if target_name == EXPORT_TARGET_RENPY_DRAFT:
        return export_renpy_draft_build()
    if target_name == EXPORT_TARGET_WINDOWS_NWJS:
        return export_windows_nwjs_build()
    if target_name == EXPORT_TARGET_MACOS_NWJS:
        return export_macos_nwjs_build()
    if target_name == EXPORT_TARGET_LINUX_NWJS:
        return export_linux_nwjs_build()
    if target_name == EXPORT_TARGET_EDITOR_DESKTOP:
        return export_editor_desktop_build()
    if target_name == EXPORT_TARGET_EDITOR_DESKTOP_SUITE:
        return export_editor_desktop_suite_build()
    return export_web_build()


def duplicate_scene(chapter_id: str, scene_id: str, scene_name: str) -> dict:
    clean_name = (scene_name or "").strip()

    if not clean_name:
        raise ValueError("复制后的场景名字不能为空。")

    _, existing_scene_ids = collect_existing_ids()
    new_scene_id = next_generated_id(existing_scene_ids, "scene")

    for chapter_path in list_chapter_files():
        chapter = read_json(chapter_path)

        if chapter.get("chapterId") != chapter_id:
            continue

        scenes = chapter.setdefault("scenes", [])
        scene_order = chapter.setdefault("sceneOrder", [scene.get("id") for scene in scenes if scene.get("id")])
        source_index = next((index for index, scene in enumerate(scenes) if scene.get("id") == scene_id), -1)

        if source_index < 0:
            raise ValueError("找到了章节，但里面没有这个场景。")

        new_scene = json.loads(json.dumps(scenes[source_index], ensure_ascii=False))
        new_scene["id"] = new_scene_id
        new_scene["name"] = clean_name

        scenes.insert(source_index + 1, new_scene)
        order_index = scene_order.index(scene_id) if scene_id in scene_order else source_index
        scene_order.insert(order_index + 1, new_scene_id)
        write_json(chapter_path, chapter)
        touch_project()

        return {
            "chapterId": chapter_id,
            "sceneId": new_scene_id,
            "scene": new_scene,
        }

    raise ValueError("没有找到要复制场景的章节。")


def remap_scene_references_in_block(block: dict, scene_id_map: dict[str, str]) -> None:
    block_type = block.get("type")

    if block_type == "jump":
        target_scene_id = block.get("targetSceneId")
        if target_scene_id in scene_id_map:
            block["targetSceneId"] = scene_id_map[target_scene_id]
        return

    if block_type == "choice":
        for option in block.get("options", []):
            target_scene_id = option.get("gotoSceneId")
            if target_scene_id in scene_id_map:
                option["gotoSceneId"] = scene_id_map[target_scene_id]
        return

    if block_type == "condition":
        else_goto_scene_id = block.get("elseGotoSceneId")
        if else_goto_scene_id in scene_id_map:
            block["elseGotoSceneId"] = scene_id_map[else_goto_scene_id]

        for branch in block.get("branches", []):
            target_scene_id = branch.get("gotoSceneId")
            if target_scene_id in scene_id_map:
                branch["gotoSceneId"] = scene_id_map[target_scene_id]


def duplicate_chapter(chapter_id: str, chapter_name: str) -> dict:
    clean_name = (chapter_name or "").strip()

    if not clean_name:
        raise ValueError("复制后的章节名字不能为空。")

    existing_chapter_ids, existing_scene_ids = collect_existing_ids()
    new_chapter_id = next_generated_id(existing_chapter_ids, "chapter")

    for chapter_path in list_chapter_files():
        chapter = read_json(chapter_path)

        if chapter.get("chapterId") != chapter_id:
            continue

        source_scenes = chapter.get("scenes", [])
        if not source_scenes:
            raise ValueError("这个章节里还没有场景，暂时不能复制。")

        source_scene_order = chapter.get("sceneOrder") or [scene.get("id") for scene in source_scenes if scene.get("id")]
        scene_id_map: dict[str, str] = {}

        for scene_id in source_scene_order:
            if scene_id and scene_id not in scene_id_map:
                new_scene_id = next_generated_id(existing_scene_ids, "scene")
                existing_scene_ids.add(new_scene_id)
                scene_id_map[scene_id] = new_scene_id

        for scene in source_scenes:
            scene_id = scene.get("id")
            if scene_id and scene_id not in scene_id_map:
                new_scene_id = next_generated_id(existing_scene_ids, "scene")
                existing_scene_ids.add(new_scene_id)
                scene_id_map[scene_id] = new_scene_id

        ordered_scene_ids = [scene_id_map.get(scene_id, scene_id) for scene_id in source_scene_order]
        ordered_scene_ids.extend(
            scene_id_map[scene.get("id")]
            for scene in source_scenes
            if scene.get("id") in scene_id_map and scene_id_map[scene.get("id")] not in ordered_scene_ids
        )

        new_chapter = json.loads(json.dumps(chapter, ensure_ascii=False))
        new_chapter["chapterId"] = new_chapter_id
        new_chapter["name"] = clean_name
        new_chapter["sceneOrder"] = ordered_scene_ids

        for scene in new_chapter.get("scenes", []):
            source_scene_id = scene.get("id")
            if source_scene_id in scene_id_map:
                scene["id"] = scene_id_map[source_scene_id]

            for block in scene.get("blocks", []):
                remap_scene_references_in_block(block, scene_id_map)

        write_json(CHAPTERS_DIR / f"{new_chapter_id}.json", new_chapter)

        project = read_json(PROJECT_PATH)
        chapter_order = get_complete_chapter_order(project)
        source_index = chapter_order.index(chapter_id) if chapter_id in chapter_order else len(chapter_order) - 1
        chapter_order.insert(source_index + 1, new_chapter_id)
        project["chapterOrder"] = chapter_order
        project["updatedAt"] = now_iso()
        write_json(PROJECT_PATH, project)

        first_scene_id = next(
            (scene_id for scene_id in new_chapter.get("sceneOrder", []) if scene_id),
            new_chapter.get("scenes", [{}])[0].get("id"),
        )
        first_scene = next(
            (scene for scene in new_chapter.get("scenes", []) if scene.get("id") == first_scene_id),
            new_chapter.get("scenes", [{}])[0],
        )

        return {
            "chapterId": new_chapter_id,
            "sceneId": first_scene_id,
            "chapter": new_chapter,
            "scene": first_scene,
        }

    raise ValueError("没有找到要复制的章节。")


def create_chapter(chapter_name: str, first_scene_name: str) -> dict:
    clean_chapter_name = (chapter_name or "").strip()
    clean_scene_name = (first_scene_name or "").strip()

    if not clean_chapter_name:
        raise ValueError("新章节至少要有一个名字。")
    if not clean_scene_name:
        raise ValueError("新章节的第一个场景也要有名字。")

    existing_chapter_ids, existing_scene_ids = collect_existing_ids()
    new_chapter_id = next_generated_id(existing_chapter_ids, "chapter")
    new_scene_id = next_generated_id(existing_scene_ids, "scene")
    new_scene = build_starter_scene(new_scene_id, clean_scene_name)
    new_chapter = {
        "chapterId": new_chapter_id,
        "name": clean_chapter_name,
        "notes": "",
        "sceneOrder": [new_scene_id],
        "scenes": [new_scene],
    }

    write_json(CHAPTERS_DIR / f"{new_chapter_id}.json", new_chapter)

    project = read_json(PROJECT_PATH)
    chapter_order = project.setdefault("chapterOrder", [])
    if new_chapter_id not in chapter_order:
        chapter_order.append(new_chapter_id)
    project["updatedAt"] = now_iso()
    if not project.get("entrySceneId"):
        project["entrySceneId"] = new_scene_id
    write_json(PROJECT_PATH, project)

    return {
        "chapterId": new_chapter_id,
        "sceneId": new_scene_id,
        "chapter": new_chapter,
        "scene": new_scene,
    }


def rename_scene(chapter_id: str, scene_id: str, scene_name: str) -> dict:
    clean_name = (scene_name or "").strip()

    if not clean_name:
        raise ValueError("场景名字不能为空。")

    for chapter_path in list_chapter_files():
        chapter = read_json(chapter_path)

        if chapter.get("chapterId") != chapter_id:
            continue

        for scene in chapter.get("scenes", []):
            if scene.get("id") == scene_id:
                scene["name"] = clean_name
                write_json(chapter_path, chapter)
                touch_project()
                return {
                    "chapterId": chapter_id,
                    "sceneId": scene_id,
                    "name": clean_name,
                }

        raise ValueError("找到了章节，但里面没有这个场景。")

    raise ValueError("没有找到对应的章节文件。")


def rename_chapter(chapter_id: str, chapter_name: str) -> dict:
    clean_name = (chapter_name or "").strip()

    if not clean_name:
        raise ValueError("章节名字不能为空。")

    for chapter_path in list_chapter_files():
        chapter = read_json(chapter_path)

        if chapter.get("chapterId") != chapter_id:
            continue

        chapter["name"] = clean_name
        write_json(chapter_path, chapter)
        touch_project()
        return {
            "chapterId": chapter_id,
            "name": clean_name,
        }

    raise ValueError("没有找到要改名的章节。")


def delete_scene(chapter_id: str, scene_id: str) -> dict:
    for chapter_path in list_chapter_files():
        chapter = read_json(chapter_path)

        if chapter.get("chapterId") != chapter_id:
            continue

        scenes = chapter.get("scenes", [])
        target_index = next((index for index, scene in enumerate(scenes) if scene.get("id") == scene_id), -1)

        if target_index < 0:
            raise ValueError("找到了章节，但里面没有这个场景。")

        if len(scenes) <= 1:
            raise ValueError("每个章节至少要保留一个场景。")

        scene_order = chapter.setdefault("sceneOrder", [scene.get("id") for scene in scenes if scene.get("id")])
        order_index = scene_order.index(scene_id) if scene_id in scene_order else target_index

        scenes.pop(target_index)
        chapter["sceneOrder"] = [item for item in scene_order if item != scene_id]
        replacement_scene_id = (
            chapter["sceneOrder"][min(order_index, len(chapter["sceneOrder"]) - 1)]
            if chapter["sceneOrder"]
            else chapter["scenes"][0].get("id")
        )

        write_json(chapter_path, chapter)

        project = read_json(PROJECT_PATH)
        if project.get("entrySceneId") == scene_id:
            project["entrySceneId"] = replacement_scene_id
        project["updatedAt"] = now_iso()
        write_json(PROJECT_PATH, project)

        return {
            "chapterId": chapter_id,
            "deletedSceneId": scene_id,
            "replacementSceneId": replacement_scene_id,
        }

    raise ValueError("没有找到要删除场景的章节。")


def move_scene(chapter_id: str, scene_id: str, direction: int) -> dict:
    if direction not in {-1, 1}:
        raise ValueError("移动场景时 direction 只能是 -1 或 1。")

    for chapter_path in list_chapter_files():
        chapter = read_json(chapter_path)

        if chapter.get("chapterId") != chapter_id:
            continue

        scene_order = chapter.setdefault(
            "sceneOrder",
            [scene.get("id") for scene in chapter.get("scenes", []) if scene.get("id")],
        )

        if scene_id not in scene_order:
            raise ValueError("找到了章节，但顺序列表里没有这个场景。")

        current_index = scene_order.index(scene_id)
        target_index = current_index + direction

        if target_index < 0 or target_index >= len(scene_order):
            raise ValueError("这个场景已经不能再往这个方向移动了。")

        scene_order[current_index], scene_order[target_index] = (
            scene_order[target_index],
            scene_order[current_index],
        )

        scene_map = {
            scene.get("id"): scene
            for scene in chapter.get("scenes", [])
            if scene.get("id")
        }
        chapter["scenes"] = [scene_map[scene_id] for scene_id in scene_order if scene_id in scene_map]
        write_json(chapter_path, chapter)
        touch_project()

        return {
            "chapterId": chapter_id,
            "sceneId": scene_id,
            "newIndex": target_index,
        }

    raise ValueError("没有找到要移动场景的章节。")


def move_chapter(chapter_id: str, direction: int) -> dict:
    if direction not in {-1, 1}:
        raise ValueError("移动章节时 direction 只能是 -1 或 1。")

    project = read_json(PROJECT_PATH)
    chapter_order = get_complete_chapter_order(project)

    if chapter_id not in chapter_order:
        raise ValueError("项目顺序里没有这个章节。")

    current_index = chapter_order.index(chapter_id)
    target_index = current_index + direction

    if target_index < 0 or target_index >= len(chapter_order):
        raise ValueError("这个章节已经不能再往这个方向移动了。")

    chapter_order[current_index], chapter_order[target_index] = (
        chapter_order[target_index],
        chapter_order[current_index],
    )
    project["chapterOrder"] = chapter_order
    project["updatedAt"] = now_iso()
    write_json(PROJECT_PATH, project)

    return {
        "chapterId": chapter_id,
        "newIndex": target_index,
    }


def delete_chapter(chapter_id: str) -> dict:
    project = read_json(PROJECT_PATH)
    chapter_order = get_complete_chapter_order(project)

    if chapter_id not in chapter_order:
        raise ValueError("项目里没有这个章节。")

    if len(chapter_order) <= 1:
        raise ValueError("至少要保留一个章节。")

    target_chapter = None
    target_path = None

    for chapter_path in list_chapter_files():
        chapter = read_json(chapter_path)
        if chapter.get("chapterId") == chapter_id:
            target_chapter = chapter
            target_path = chapter_path
            break

    if not target_chapter or not target_path:
        raise ValueError("没有找到要删除的章节文件。")

    current_index = chapter_order.index(chapter_id)
    chapter_order = [item for item in chapter_order if item != chapter_id]
    replacement_chapter_id = chapter_order[min(current_index, len(chapter_order) - 1)]

    replacement_scene_id = ""
    for chapter_path in list_chapter_files():
        chapter = read_json(chapter_path)
        if chapter.get("chapterId") == replacement_chapter_id:
            replacement_scene_id = (
                (chapter.get("sceneOrder") or [scene.get("id") for scene in chapter.get("scenes", []) if scene.get("id")])[0]
                or ""
            )
            break

    target_path.unlink()
    project["chapterOrder"] = chapter_order

    deleted_scene_ids = {
        scene.get("id")
        for scene in target_chapter.get("scenes", [])
        if scene.get("id")
    }

    if project.get("entrySceneId") in deleted_scene_ids:
        project["entrySceneId"] = replacement_scene_id

    project["updatedAt"] = now_iso()
    write_json(PROJECT_PATH, project)

    return {
        "deletedChapterId": chapter_id,
        "replacementChapterId": replacement_chapter_id,
        "replacementSceneId": replacement_scene_id,
    }


class EditorRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self._static_cache_headers: dict[str, str] | None = None
        super().__init__(*args, directory=str(ROOT_DIR), **kwargs)

    def is_allowed_api_request(self, *, require_origin: bool = False) -> bool:
        host = self.headers.get("Host", "")
        if host and not is_local_editor_host(host):
            return False

        if require_origin:
            origin = self.headers.get("Origin", "")
            referer = self.headers.get("Referer", "")
            if origin and not is_local_editor_origin(origin):
                return False
            if not origin and referer and not is_local_editor_origin(referer):
                return False

        return True

    def send_head(self):  # noqa: ANN201, N802
        self._static_cache_headers = None
        parsed = urlparse(self.path)
        file_path = Path(self.translate_path(parsed.path))
        if is_editor_static_cache_candidate(parsed.path, file_path):
            cache_headers = build_editor_static_cache_headers(file_path)
            if request_etag_matches(self.headers.get("If-None-Match"), cache_headers["ETag"]):
                self.send_response(HTTPStatus.NOT_MODIFIED)
                self.send_header("Cache-Control", cache_headers["Cache-Control"])
                self.send_header("ETag", cache_headers["ETag"])
                self.send_header("Last-Modified", cache_headers["Last-Modified"])
                self.end_headers()
                return None
            self._static_cache_headers = cache_headers
        return super().send_head()

    def end_headers(self) -> None:
        cache_headers = self._static_cache_headers
        if cache_headers:
            self.send_header("Cache-Control", cache_headers["Cache-Control"])
            self.send_header("ETag", cache_headers["ETag"])
        super().end_headers()
        self._static_cache_headers = None

    def reject_non_local_api_request(self) -> None:
        self.send_json(
            {
                "ok": False,
                "error": "为了保护本地项目，编辑器 API 只接受来自本机编辑器页面的请求。",
            },
            status=HTTPStatus.FORBIDDEN,
        )

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)

        if parsed.path.startswith("/api/") and not self.is_allowed_api_request():
            self.reject_non_local_api_request()
            return

        if parsed.path == "/api/project-center":
            self.handle_project_center()
            return

        if parsed.path == "/api/project-history":
            self.handle_project_history()
            return

        if parsed.path == "/api/project-data":
            self.handle_project_data()
            return

        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)

        if parsed.path.startswith("/api/") and not self.is_allowed_api_request(require_origin=True):
            self.reject_non_local_api_request()
            return

        if parsed.path == "/api/create-project":
            self.handle_create_project()
            return

        if parsed.path == "/api/open-project":
            self.handle_open_project()
            return

        if parsed.path == "/api/undo-project-history":
            self.handle_undo_project_history()
            return

        if parsed.path == "/api/redo-project-history":
            self.handle_redo_project_history()
            return

        if parsed.path == "/api/restore-project-history":
            self.handle_restore_project_history()
            return

        if parsed.path == "/api/create-project-history-snapshot":
            self.handle_create_project_history_snapshot()
            return

        if parsed.path == "/api/preview-project-history-restore":
            self.handle_preview_project_history_restore()
            return

        if parsed.path == "/api/update-project-history-snapshot":
            self.handle_update_project_history_snapshot()
            return

        if parsed.path == "/api/acknowledge-project-recovery-notice":
            self.handle_acknowledge_project_recovery_notice()
            return

        if parsed.path == "/api/rename-project":
            self.handle_rename_project()
            return

        if parsed.path == "/api/duplicate-project":
            self.handle_duplicate_project()
            return

        if parsed.path == "/api/delete-project":
            self.handle_delete_project()
            return

        if parsed.path == "/api/save-scene":
            self.handle_save_scene()
            return

        if parsed.path == "/api/create-scene":
            self.handle_create_scene()
            return

        if parsed.path == "/api/import-assets":
            self.handle_import_assets()
            return

        if parsed.path == "/api/generate-openai-asset":
            self.handle_generate_openai_asset()
            return

        if parsed.path == "/api/create-voice-placeholder":
            self.handle_create_voice_placeholder()
            return

        if parsed.path == "/api/create-voice-placeholders":
            self.handle_create_voice_placeholders()
            return

        if parsed.path == "/api/match-voice-files":
            self.handle_match_voice_files()
            return

        if parsed.path == "/api/replace-asset":
            self.handle_replace_asset()
            return

        if parsed.path == "/api/delete-asset":
            self.handle_delete_asset()
            return

        if parsed.path == "/api/update-asset-meta":
            self.handle_update_asset_meta()
            return

        if parsed.path == "/api/update-character-presentation":
            self.handle_update_character_presentation()
            return

        if parsed.path == "/api/bulk-update-asset-tags":
            self.handle_bulk_update_asset_tags()
            return

        if parsed.path == "/api/bulk-delete-assets":
            self.handle_bulk_delete_assets()
            return

        if parsed.path == "/api/save-project-settings":
            self.handle_save_project_settings()
            return

        if parsed.path == "/api/import-localization-patches":
            self.handle_import_localization_patches()
            return

        if parsed.path == "/api/repair-project-doctor":
            self.handle_repair_project_doctor()
            return

        if parsed.path == "/api/rename-variable":
            self.handle_rename_variable()
            return

        if parsed.path == "/api/export-build":
            self.handle_export_build()
            return

        if parsed.path == "/api/duplicate-scene":
            self.handle_duplicate_scene()
            return

        if parsed.path == "/api/create-chapter":
            self.handle_create_chapter()
            return

        if parsed.path == "/api/create-starter-kit":
            self.handle_create_starter_kit()
            return

        if parsed.path == "/api/creative-assistant":
            self.handle_creative_assistant()
            return

        if parsed.path == "/api/duplicate-chapter":
            self.handle_duplicate_chapter()
            return

        if parsed.path == "/api/rename-scene":
            self.handle_rename_scene()
            return

        if parsed.path == "/api/rename-chapter":
            self.handle_rename_chapter()
            return

        if parsed.path == "/api/delete-scene":
            self.handle_delete_scene()
            return

        if parsed.path == "/api/move-scene":
            self.handle_move_scene()
            return

        if parsed.path == "/api/move-chapter":
            self.handle_move_chapter()
            return

        if parsed.path == "/api/delete-chapter":
            self.handle_delete_chapter()
            return

        self.send_error(HTTPStatus.NOT_FOUND, "没有这个接口")

    def handle_project_center(self) -> None:
        self.send_json(get_project_center_payload())

    def handle_project_data(self) -> None:
        try:
            self.send_json(load_project_bundle())
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {
                    "ok": False,
                    "error": f"读取项目数据时出了意外问题：{error}",
                    "recovery": build_history_payload(),
                },
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_project_history(self) -> None:
        self.send_json(build_history_payload())

    def handle_create_project(self) -> None:
        try:
            payload = self.read_json_body()
            result = create_blank_project(payload.get("name"), editor_mode=payload.get("editorMode"))
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"新建项目时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_undo_project_history(self) -> None:
        try:
            history = undo_history()
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    "history": history,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {
                    "ok": False,
                    "error": f"撤销到上个版本时出了意外问题：{error}",
                    "recovery": build_history_payload(),
                },
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_redo_project_history(self) -> None:
        try:
            history = redo_history()
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    "history": history,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {
                    "ok": False,
                    "error": f"重做到较新版本时出了意外问题：{error}",
                    "recovery": build_history_payload(),
                },
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_restore_project_history(self) -> None:
        try:
            payload = self.read_json_body()
            history = restore_history_snapshot(
                target_index=payload.get("targetIndex"),
                snapshot_id=payload.get("snapshotId"),
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    "history": history,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {
                    "ok": False,
                    "error": f"恢复指定版本时出了意外问题：{error}",
                    "recovery": build_history_payload(),
                },
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_create_project_history_snapshot(self) -> None:
        try:
            payload = self.read_json_body()
            history = create_manual_history_snapshot(payload.get("label"))
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    "history": history,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {
                    "ok": False,
                    "error": f"创建手动检查点时出了意外问题：{error}",
                    "recovery": build_history_payload(),
                },
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_preview_project_history_restore(self) -> None:
        try:
            payload = self.read_json_body()
            preview = build_history_restore_preview(
                target_index=payload.get("targetIndex"),
                snapshot_id=payload.get("snapshotId"),
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    "preview": preview,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {
                    "ok": False,
                    "error": f"预览恢复差异时出了意外问题：{error}",
                    "recovery": build_history_payload(),
                },
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_update_project_history_snapshot(self) -> None:
        try:
            payload = self.read_json_body()
            history = update_history_snapshot_label(
                target_index=payload.get("targetIndex"),
                snapshot_id=payload.get("snapshotId"),
                label=payload.get("label") or "",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    "history": history,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {
                    "ok": False,
                    "error": f"修改检查点备注时出了意外问题：{error}",
                    "recovery": build_history_payload(),
                },
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_acknowledge_project_recovery_notice(self) -> None:
        try:
            recovery = acknowledge_session_recovery_notice()
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    "sessionRecovery": recovery,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {
                    "ok": False,
                    "error": f"标记异常退出提醒已读时出了意外问题：{error}",
                    "recovery": build_history_payload(),
                },
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_open_project(self) -> None:
        try:
            payload = self.read_json_body()
            project_id = str(payload.get("projectId") or "").strip()
            if not project_id:
                raise ValueError("打开项目时缺少 projectId。")

            project = activate_project(project_id)
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    "project": project,
                    "projectCenter": get_project_center_payload(),
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"打开项目时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_rename_project(self) -> None:
        try:
            payload = self.read_json_body()
            project_id = str(payload.get("projectId") or "").strip()
            if not project_id:
                raise ValueError("改项目名时缺少 projectId。")

            result = attach_history_to_result(
                rename_project(project_id, payload.get("name")),
                f"项目改名：{payload.get('name') or '未命名项目'}",
                get_project_directory(project_id),
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"修改项目名时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_duplicate_project(self) -> None:
        try:
            payload = self.read_json_body()
            project_id = str(payload.get("projectId") or "").strip()
            if not project_id:
                raise ValueError("复制项目时缺少 projectId。")

            result = duplicate_project(project_id, payload.get("name"))
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"复制项目时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_delete_project(self) -> None:
        try:
            payload = self.read_json_body()
            project_id = str(payload.get("projectId") or "").strip()
            if not project_id:
                raise ValueError("删除项目时缺少 projectId。")

            result = delete_project(project_id)
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"删除项目时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_save_scene(self) -> None:
        try:
            payload = self.read_json_body()
            chapter_id = payload.get("chapterId")
            scene_id = payload.get("sceneId")
            scene = payload.get("scene")

            if not chapter_id or not scene_id or scene is None:
                raise ValueError("保存场景时缺少 chapterId、sceneId 或 scene。")

            save_scene(chapter_id, scene_id, scene)
            history = record_project_history(f"保存场景：{scene.get('name') or scene_id}")
            self.send_json(
                {
                    "ok": True,
                    "savedAt": datetime.now().isoformat(timespec="seconds"),
                    "history": history,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"保存时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_creative_assistant(self) -> None:
        try:
            payload = self.read_json_body()
            result = build_creative_assistant_result(payload)
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    "result": result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"智能创作助手生成失败：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_create_scene(self) -> None:
        try:
            payload = self.read_json_body()
            chapter_id = payload.get("chapterId")
            scene_name = payload.get("name")
            after_scene_id = payload.get("afterSceneId")

            if not chapter_id:
                raise ValueError("新建场景时缺少 chapterId。")

            result = attach_history_to_result(
                create_scene(chapter_id, scene_name, after_scene_id),
                f"新建场景：{scene_name or '未命名场景'}",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"新建场景时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_import_assets(self) -> None:
        try:
            payload = self.read_json_body()
            result = attach_history_to_result(
                import_assets(
                    payload.get("assetType"),
                    payload.get("files") or [],
                    payload.get("fallbackAssetType"),
                ),
                f"导入素材：{len(payload.get('files') or [])} 个",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"导入素材时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_generate_openai_asset(self) -> None:
        try:
            payload = self.read_json_body()
            result = generate_openai_asset(payload)
            result = attach_history_to_result(
                result,
                f"AI 生成素材：{result.get('asset', {}).get('name') or '未命名素材'}",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"AI 生成素材时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_create_voice_placeholder(self) -> None:
        try:
            payload = self.read_json_body()
            result = attach_history_to_result(
                create_voice_placeholder(
                    payload.get("sceneId"),
                    payload.get("blockId"),
                    payload.get("preferredName"),
                ),
                "生成语音占位条目",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"生成语音条目时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_create_voice_placeholders(self) -> None:
        try:
            payload = self.read_json_body()
            result = attach_history_to_result(
                create_voice_placeholders(
                    payload.get("items") or [],
                    payload.get("preferredName"),
                ),
                f"批量生成语音条目：{len(payload.get('items') or [])} 句",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"批量生成语音条目时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_match_voice_files(self) -> None:
        try:
            payload = self.read_json_body()
            result = match_voice_files_to_placeholders(
                payload.get("files") or [],
                payload.get("assetIds") or [],
            )
            if result.get("matchedCount"):
                result = attach_history_to_result(
                    result,
                    f"批量匹配语音文件：{result.get('matchedCount')} 个",
                )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"批量匹配语音文件时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_replace_asset(self) -> None:
        try:
            payload = self.read_json_body()
            result = attach_history_to_result(
                replace_asset_file(
                    payload.get("assetId"),
                    payload.get("file") or {},
                ),
                "替换素材文件",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"替换素材时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_delete_asset(self) -> None:
        try:
            payload = self.read_json_body()
            result = attach_history_to_result(
                delete_asset(payload.get("assetId")),
                "删除素材",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"删除素材时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_update_asset_meta(self) -> None:
        try:
            payload = self.read_json_body()
            result = attach_history_to_result(
                update_asset_metadata(
                    payload.get("assetId"),
                    payload.get("name"),
                    payload.get("tags"),
                    payload.get("favorite"),
                    payload.get("rights"),
                ),
                f"修改素材信息：{payload.get('name') or payload.get('assetId') or '未命名素材'}",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"保存素材信息时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_update_character_presentation(self) -> None:
        try:
            payload = self.read_json_body()
            result = attach_history_to_result(
                update_character_presentation(
                    payload.get("characterId"),
                    payload.get("presentation"),
                    payload.get("expressionBindings"),
                ),
                f"修改角色表现：{payload.get('characterId') or '未命名角色'}",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"保存角色表现配置时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_bulk_update_asset_tags(self) -> None:
        try:
            payload = self.read_json_body()
            result = attach_history_to_result(
                bulk_update_asset_tags(
                    payload.get("assetIds") or [],
                    payload.get("mode"),
                    payload.get("tags"),
                ),
                "批量整理素材标签",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"批量改标签时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_bulk_delete_assets(self) -> None:
        try:
            payload = self.read_json_body()
            result = attach_history_to_result(
                bulk_delete_assets(payload.get("assetIds") or []),
                "批量删除未使用素材",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"批量删除素材时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_save_project_settings(self) -> None:
        try:
            payload = self.read_json_body()
            result = attach_history_to_result(
                save_project_settings(
                    resolution=payload.get("resolution"),
                    release_version=payload.get("releaseVersion"),
                    language=payload.get("language"),
                    supported_languages=payload.get("supportedLanguages"),
                    editor_mode=payload.get("editorMode"),
                    runtime_settings=payload.get("runtimeSettings"),
                    dialog_box_config=payload.get("dialogBoxConfig"),
                    game_ui_config=payload.get("gameUiConfig"),
                    particle_custom_presets=payload.get("particleCustomPresets"),
                    variables=payload.get("variables"),
                ),
                "修改项目设置",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"保存项目设置时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_import_localization_patches(self) -> None:
        try:
            payload = self.read_json_body()
            result = attach_history_to_result(
                import_localization_patches(payload.get("patches")),
                "导入多语言翻译",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"导入多语言翻译时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_repair_project_doctor(self) -> None:
        try:
            payload = self.read_json_body()
            result = repair_project_doctor(payload.get("repairCodes"), dry_run=bool(payload.get("dryRun")))
            if result.get("changed"):
                result = attach_history_to_result(result, "项目医生安全修复")
            else:
                result["history"] = build_history_payload()
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"项目医生安全修复时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_rename_variable(self) -> None:
        try:
            payload = self.read_json_body()
            result = attach_history_to_result(
                rename_project_variable(
                    old_variable_id=payload.get("oldVariableId"),
                    variable=payload.get("variable"),
                ),
                "重命名变量并迁移引用",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"迁移变量引用时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_export_build(self) -> None:
        try:
            payload = self.read_json_body()
            result = export_project_build(payload.get("target"))
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"导出发布包时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_duplicate_scene(self) -> None:
        try:
            payload = self.read_json_body()
            chapter_id = payload.get("chapterId")
            scene_id = payload.get("sceneId")
            scene_name = payload.get("name")

            if not chapter_id or not scene_id:
                raise ValueError("复制场景时缺少 chapterId 或 sceneId。")

            result = attach_history_to_result(
                duplicate_scene(chapter_id, scene_id, scene_name),
                f"复制场景：{scene_name or scene_id}",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"复制场景时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_create_chapter(self) -> None:
        try:
            payload = self.read_json_body()
            chapter_name = payload.get("chapterName")
            first_scene_name = payload.get("firstSceneName")
            result = attach_history_to_result(
                create_chapter(chapter_name, first_scene_name),
                f"新建章节：{chapter_name or '未命名章节'}",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"新建章节时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_create_starter_kit(self) -> None:
        try:
            payload = self.read_json_body()
            result = attach_history_to_result(
                create_starter_kit(
                    character_name=payload.get("characterName"),
                    background_name=payload.get("backgroundName"),
                    bgm_name=payload.get("bgmName"),
                ),
                "生成起步骨架",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"生成起步骨架时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_duplicate_chapter(self) -> None:
        try:
            payload = self.read_json_body()
            chapter_id = payload.get("chapterId")
            chapter_name = payload.get("chapterName")

            if not chapter_id:
                raise ValueError("复制章节时缺少 chapterId。")

            result = attach_history_to_result(
                duplicate_chapter(chapter_id, chapter_name),
                f"复制章节：{chapter_name or chapter_id}",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"复制章节时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_rename_scene(self) -> None:
        try:
            payload = self.read_json_body()
            chapter_id = payload.get("chapterId")
            scene_id = payload.get("sceneId")
            scene_name = payload.get("name")

            if not chapter_id or not scene_id:
                raise ValueError("修改场景名时缺少 chapterId 或 sceneId。")

            result = attach_history_to_result(
                rename_scene(chapter_id, scene_id, scene_name),
                f"场景改名：{scene_name or scene_id}",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"修改场景名时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_rename_chapter(self) -> None:
        try:
            payload = self.read_json_body()
            chapter_id = payload.get("chapterId")
            chapter_name = payload.get("name")

            if not chapter_id:
                raise ValueError("修改章节名时缺少 chapterId。")

            result = attach_history_to_result(
                rename_chapter(chapter_id, chapter_name),
                f"章节改名：{chapter_name or chapter_id}",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"修改章节名时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_delete_scene(self) -> None:
        try:
            payload = self.read_json_body()
            chapter_id = payload.get("chapterId")
            scene_id = payload.get("sceneId")

            if not chapter_id or not scene_id:
                raise ValueError("删除场景时缺少 chapterId 或 sceneId。")

            result = attach_history_to_result(
                delete_scene(chapter_id, scene_id),
                "删除场景",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"删除场景时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_move_scene(self) -> None:
        try:
            payload = self.read_json_body()
            chapter_id = payload.get("chapterId")
            scene_id = payload.get("sceneId")
            direction = payload.get("direction")

            if not chapter_id or not scene_id:
                raise ValueError("调整场景顺序时缺少 chapterId 或 sceneId。")

            result = attach_history_to_result(
                move_scene(chapter_id, scene_id, int(direction)),
                "调整场景顺序",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"调整场景顺序时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_move_chapter(self) -> None:
        try:
            payload = self.read_json_body()
            chapter_id = payload.get("chapterId")
            direction = payload.get("direction")

            if not chapter_id:
                raise ValueError("调整章节顺序时缺少 chapterId。")

            result = attach_history_to_result(
                move_chapter(chapter_id, int(direction)),
                "调整章节顺序",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"调整章节顺序时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def handle_delete_chapter(self) -> None:
        try:
            payload = self.read_json_body()
            chapter_id = payload.get("chapterId")

            if not chapter_id:
                raise ValueError("删除章节时缺少 chapterId。")

            result = attach_history_to_result(
                delete_chapter(chapter_id),
                "删除章节",
            )
            self.send_json(
                {
                    "ok": True,
                    "savedAt": now_iso(),
                    **result,
                }
            )
        except json.JSONDecodeError:
            self.send_json({"ok": False, "error": "请求体不是有效 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self.send_json({"ok": False, "error": str(error)}, status=HTTPStatus.BAD_REQUEST)
        except Exception as error:  # pragma: no cover - defensive fallback
            self.send_json(
                {"ok": False, "error": f"删除章节时出了意外问题：{error}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def read_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length)
        return json.loads(raw.decode("utf-8"))

    def send_json(self, payload: dict, status: int = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> None:
    global HAS_SELECTED_PROJECT
    parser = argparse.ArgumentParser(
        description="启动 Canvasia Engine 原型编辑器的本地预览服务。"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"优先尝试的端口号，默认 {DEFAULT_PORT}",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="只启动服务，不自动打开浏览器。",
    )
    args = parser.parse_args()

    ensure_project_roots()
    set_active_project_paths(SAMPLE_PROJECT_ID, SAMPLE_PROJECT_DIR, "sample")
    HAS_SELECTED_PROJECT = False
    port = find_available_port(args.port)
    os.chdir(ROOT_DIR)

    server = ThreadingHTTPServer(("127.0.0.1", port), EditorRequestHandler)
    url = build_url(port)

    print("Canvasia Engine 原型编辑器已启动")
    print(f"本地地址: {url}")
    print("按 Ctrl+C 可以停止服务")

    if not args.no_open:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止本地预览服务")
    finally:
        try:
            mark_project_session_closed(reason="server-stopped")
        except Exception:
            pass
        server.server_close()


if __name__ == "__main__":
    main()
