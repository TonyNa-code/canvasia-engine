from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.util
import io
import json
import math
import os
import platform
import random
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
import unicodedata
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path


ASSET_TYPE_IMAGE = {"background", "sprite", "cg", "ui"}
ASSET_TYPE_FONT = {"font"}
DEFAULT_PROJECT_LANGUAGE = "zh-CN"
DEFAULT_GAME_DATA_NAME = "game_data.json"
ENGINE_BRAND_LOGO_RELATIVE_PATH = "assets/canvasia-brand-logo.png"
NATIVE_VIDEO_OPTIONAL_REQUIREMENTS_NAME = "requirements-native-runtime-video.txt"
NATIVE_VIDEO_OPTIONAL_REQUIREMENTS_CANDIDATES = (NATIVE_VIDEO_OPTIONAL_REQUIREMENTS_NAME, "requirements-video.txt")
NATIVE_VIDEO_SYNC_BACKEND_ID = "pyav_audio_video_sync"
NATIVE_VIDEO_EMBEDDED_BACKEND_ID = "opencv_embedded_playback"
TRANSITION_DURATION_DEFAULT_MS = 360
TRANSITION_DURATION_MIN_MS = 0
TRANSITION_DURATION_MAX_MS = 5000
NATIVE_BASIC_TRANSITIONS = {"fade", "none"}
NATIVE_CHARACTER_TRANSITIONS = {"fade", "slide_left", "slide_right", "rise", "pop", "none"}
FILE_INTEGRITY_REPORT_NAME = "native-runtime-file-integrity.json"
FILE_INTEGRITY_MARKDOWN_NAME = "native-runtime-file-integrity.md"
ACCEPTANCE_REPORT_NAME = "native-runtime-release-acceptance.md"
ACCEPTANCE_JSON_NAME = "native-runtime-release-acceptance.json"
VN_BASELINE_QUALITY_REPORT_NAME = "native-runtime-vn-baseline-quality.json"
VN_BASELINE_QUALITY_MARKDOWN_NAME = "native-runtime-vn-baseline-quality.md"
FILE_INTEGRITY_EXCLUDED_FILE_NAMES = {
    FILE_INTEGRITY_REPORT_NAME,
    FILE_INTEGRITY_MARKDOWN_NAME,
    "native_app_package_manifest.json",
    VN_BASELINE_QUALITY_REPORT_NAME,
    VN_BASELINE_QUALITY_MARKDOWN_NAME,
}
FILE_INTEGRITY_EXCLUDED_PREFIXES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".git",
    "native_app_build",
    "native_app_dist",
}
FILE_INTEGRITY_VOLATILE_REPORT_PREFIXES = (
    "native-runtime-release-",
    "native-runtime-3d-",
)
GAME_UI_ASSET_REFERENCE_LABELS = {
    "titleBackgroundAssetId": "标题背景",
    "titleLogoAssetId": "标题 Logo",
    "panelFrameAssetId": "通用面板九宫格",
    "buttonFrameAssetId": "按钮默认九宫格",
    "buttonHoverFrameAssetId": "按钮悬停九宫格",
    "buttonPressedFrameAssetId": "按钮按下九宫格",
    "buttonDisabledFrameAssetId": "按钮禁用九宫格",
    "saveSlotFrameAssetId": "存档卡片九宫格",
    "systemPanelFrameAssetId": "系统面板九宫格",
    "uiOverlayAssetId": "UI 氛围叠层",
}
NATIVE_VIDEO_BACKEND_OPTIONS = [
    {
        "id": "system_player_bridge",
        "label": "系统播放器桥接",
        "kind": "external",
        "pythonPackage": "",
        "moduleName": "",
        "embeddedVideo": False,
        "audio": True,
        "productionReady": True,
        "notes": "默认方案。包体轻、三平台风险低，但无法在 Pygame 窗口内检测真实播放进度。",
    },
    {
        "id": NATIVE_VIDEO_SYNC_BACKEND_ID,
        "label": "PyAV/FFmpeg 音画同步内嵌播放",
        "kind": "embedded_audio_video_sync",
        "pythonPackage": "av>=12",
        "moduleName": "av",
        "embeddedVideo": True,
        "audio": True,
        "productionReady": False,
        "notes": "推荐的商业化路线候选：按音频播放时钟驱动画面帧，支持剪辑区间和播放结束检测；仍需在目标系统实机验证编码兼容性。",
    },
    {
        "id": "opencv_frame_preview",
        "label": "OpenCV 内嵌画面帧预览",
        "kind": "embedded_visual_preview",
        "pythonPackage": "opencv-python>=4.9,<5",
        "moduleName": "cv2",
        "embeddedVideo": True,
        "audio": False,
        "productionReady": False,
        "notes": "用于快速抽帧和发布前画面探针；OpenCV 不负责音频，音画同步优先交给 PyAV/FFmpeg 后端。",
    },
    {
        "id": NATIVE_VIDEO_EMBEDDED_BACKEND_ID,
        "label": "OpenCV 窗口内嵌逐帧播放",
        "kind": "embedded_visual_playback",
        "pythonPackage": "opencv-python>=4.9,<5",
        "moduleName": "cv2",
        "embeddedVideo": True,
        "audio": False,
        "productionReady": False,
        "notes": "PyAV 不可用时的画面播放兜底：可在 Pygame 窗口内播放视频画面并识别结束，但不解音频。",
    },
]
COLOR_BG = (12, 15, 28)
COLOR_PANEL = (18, 24, 40)
COLOR_PANEL_BORDER = (78, 106, 168)
COLOR_TEXT = (243, 246, 255)
COLOR_TEXT_MUTED = (160, 176, 204)
COLOR_ACCENT = (106, 154, 255)
COLOR_ACCENT_ALT = (173, 115, 255)
COLOR_WARNING = (255, 161, 110)
FPS = 60
VN_TEXT_LONG_WARNING_LENGTH = 260
VN_TEXT_LONG_WARNING_LINES = 5
VN_CHOICE_LONG_WARNING_LENGTH = 42
VN_CHOICE_MANY_OPTIONS = 6
VARIABLE_TYPES = {"number", "boolean", "string"}
NUMERIC_CONDITION_OPERATORS = {">", ">=", "<", "<="}
EQUALITY_CONDITION_OPERATORS = {"==", "=", "!="}
SAVE_SHORTCUT_COUNT = 3
SAVE_DIALOG_PAGE_SIZE = 6
DEFAULT_FORMAL_SAVE_SLOT_COUNT = 24
MIN_FORMAL_SAVE_SLOT_COUNT = 3
MAX_FORMAL_SAVE_SLOT_COUNT = 120
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
DIALOG_BOX_PRESETS = {
    "moonlight": {
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
        "panelAssetOpacity": 0,
        "panelAssetFit": "cover",
    },
    "warm": {
        "preset": "warm",
        "shape": "rounded",
        "widthPercent": 76,
        "minHeight": 148,
        "paddingX": 16,
        "paddingY": 14,
        "backgroundColor": "#fffaf5",
        "backgroundOpacity": 92,
        "borderColor": "#8f6548",
        "borderOpacity": 18,
        "textColor": "#332117",
        "speakerColor": "#7f5438",
        "hintColor": "#6d5b4f",
        "blurStrength": 8,
        "borderWidth": 1,
        "shadowStrength": 18,
        "panelAssetOpacity": 0,
        "panelAssetFit": "cover",
    },
    "paper": {
        "preset": "paper",
        "shape": "square",
        "widthPercent": 76,
        "minHeight": 156,
        "paddingX": 18,
        "paddingY": 16,
        "backgroundColor": "#fff7e8",
        "backgroundOpacity": 95,
        "borderColor": "#b08659",
        "borderOpacity": 28,
        "textColor": "#4a2f1d",
        "speakerColor": "#7f5438",
        "hintColor": "#7f6a54",
        "blurStrength": 4,
        "borderWidth": 1,
        "shadowStrength": 16,
        "panelAssetOpacity": 0,
        "panelAssetFit": "cover",
    },
    "transparent": {
        "preset": "transparent",
        "shape": "capsule",
        "widthPercent": 88,
        "minHeight": 132,
        "paddingX": 14,
        "paddingY": 10,
        "backgroundColor": "#08111b",
        "backgroundOpacity": 0,
        "borderColor": "#7fe6ff",
        "borderOpacity": 0,
        "textColor": "#f4f8ff",
        "speakerColor": "#ffffff",
        "hintColor": "#d0daf0",
        "blurStrength": 0,
        "borderWidth": 0,
        "shadowStrength": 0,
        "panelAssetOpacity": 0,
        "panelAssetFit": "cover",
    },
}
SAVE_ROOT_DIR_NAME = ".canvasia-engine"
SAVE_SUBDIR_NAME = "native-runtime-saves"
SETTINGS_SUBDIR_NAME = "native-runtime-settings"
PROGRESS_SUBDIR_NAME = "native-runtime-progress"
PROFILE_SUBDIR_NAME = "native-runtime-profiles"
AUTO_RESUME_SUBDIR_NAME = "native-runtime-autoresume"
LOG_SUBDIR_NAME = "native-runtime-logs"
SCREENSHOT_SUBDIR_NAME = "native-runtime-screenshots"
DEFAULT_RUNTIME_PLAYER_SETTINGS = {
    "themeMode": "auto",
    "displayMode": "windowed",
    "textSpeed": "normal",
    "language": "",
    "textScalePercent": 100,
    "dialogBoxOpacityPercent": 100,
    "autoPlayDelayMs": 1800,
    "autoPlayWaitForVoice": "off",
    "masterVolume": 100,
    "bgmVolume": 85,
    "sfxVolume": 90,
    "voiceVolume": 100,
}
READ_TEXT_KEY_LIMIT = 20000
SNAPSHOT_TEXT_HISTORY_LIMIT = 120
DEFAULT_PLAYER_PROFILE = {
    "firstPlayedAt": None,
    "lastPlayedAt": None,
    "lastEndedAt": None,
    "totalPlayMs": 0,
    "sessionCount": 0,
    "resumedCount": 0,
    "returnToTitleCount": 0,
}
RUNTIME_THEME_MODES = ("auto", "light", "dark")
RUNTIME_DISPLAY_MODES = ("windowed", "fullscreen")
TEXT_SPEED_PRESETS = {
    "slow": 24,
    "normal": 42,
    "fast": 72,
    "instant": 10000,
}
TEXT_SPEED_LABELS = {
    "slow": "慢",
    "normal": "标准",
    "fast": "快",
    "instant": "瞬时",
}
TYPEWRITER_SENTENCE_PAUSE_MS = 260
TYPEWRITER_CLAUSE_PAUSE_MS = 140
TYPEWRITER_ELLIPSIS_PAUSE_MS = 220
TYPEWRITER_LEADING_OPENERS = "“‘\"'（([{【〔〈《「『"
TYPEWRITER_TRAILING_CLOSERS = "”’\"'）)]}】〕〉》」』"
TYPEWRITER_PERIOD_ABBREVIATIONS = {
    "mr",
    "mrs",
    "ms",
    "dr",
    "prof",
    "sr",
    "jr",
    "st",
    "vs",
    "etc",
    "e.g",
    "i.e",
    "u.s",
    "u.k",
    "no",
    "fig",
    "vol",
    "ch",
    "dept",
    "inc",
    "ltd",
    "co",
}
RUNTIME_LANGUAGE_LABELS = {
    "zh-CN": "简体中文",
    "ja-JP": "日本語",
    "en-US": "English",
}
AUTO_PLAY_DELAY_PRESETS = (900, 1400, 1800, 2400, 3200)
TEXT_SCALE_PRESETS = (90, 100, 110, 125)
DIALOG_BOX_OPACITY_PRESETS = (0, 35, 60, 80, 100)
RUNTIME_TOGGLE_MODES = ("off", "on")
SYSTEM_MENU_ITEMS = [
    ("continue", "继续"),
    ("help", "操作帮助"),
    ("history", "文本历史"),
    ("archives", "资料馆"),
    ("profile", "玩家档案"),
    ("auto-resume", "续玩记录"),
    ("save", "正式存档"),
    ("load", "读取存档"),
    ("settings", "体验设置"),
    ("quick-save", "快速存档"),
    ("quick-load", "快速读档"),
    ("restart", "回到开头"),
    ("exit", "退出预览"),
]
TITLE_MENU_ITEMS = [
    ("start", "开始游戏"),
    ("resume", "继续上次"),
    ("load", "读取存档"),
    ("settings", "体验设置"),
    ("archives", "资料馆"),
    ("exit", "退出"),
]
SETTINGS_MENU_ITEMS = [
    ("themeMode", "界面主题"),
    ("displayMode", "显示模式"),
    ("textSpeed", "文字速度"),
    ("language", "语言"),
    ("textScalePercent", "文字大小"),
    ("dialogBoxOpacityPercent", "文本框透明度"),
    ("autoPlayDelayMs", "自动播放间隔"),
    ("autoPlayWaitForVoice", "自动播放等语音"),
    ("masterVolume", "总音量"),
    ("bgmVolume", "BGM 音量"),
    ("sfxVolume", "音效音量"),
    ("voiceVolume", "语音音量"),
]
NATIVE_VIDEO_PREVIEW_MODE = "cinematic_bridge_card"
DEFAULT_SCENE3D_PREVIEW = {"yaw": 32.0, "pitch": 34.0, "zoom": 1.0, "interactionEnabled": True}
CHARACTER_PRESENTATION_MODE_LABELS = {
    "sprite": "普通立绘",
    "layered_sprite": "差分立绘",
    "live2d": "Live2D",
    "model3d": "3D 模型",
}
ARCHIVE_MENU_ITEMS = {
    "chapters": "章节回放",
    "music": "音乐鉴赏",
    "gallery": "CG 回想",
    "locations": "地点图鉴",
    "characters": "角色图鉴",
    "narrations": "旁白摘录",
    "relations": "关系图鉴",
    "voices": "语音回听",
    "endings": "结局回放",
    "achievements": "成就馆",
}
ARCHIVE_MENU_SEQUENCE = tuple(ARCHIVE_MENU_ITEMS.keys())
NATIVE_PARTICLE_PRESET_DEFAULTS = {
    "snow": {"density": 40, "sizeMin": 5, "sizeMax": 14, "speed": 90, "drift": 18, "color": (255, 255, 255), "accent": (214, 238, 255), "shape": "flake"},
    "rain": {"density": 54, "sizeMin": 2, "sizeMax": 4, "speed": 300, "drift": 32, "color": (164, 208, 255), "accent": (219, 239, 255), "shape": "rain"},
    "petals": {"density": 30, "sizeMin": 10, "sizeMax": 18, "speed": 84, "drift": 30, "color": (255, 191, 221), "accent": (255, 226, 238), "shape": "petal"},
    "dust": {"density": 24, "sizeMin": 3, "sizeMax": 8, "speed": 26, "drift": 10, "color": (244, 230, 191), "accent": (255, 245, 221), "shape": "glow"},
    "embers": {"density": 34, "sizeMin": 4, "sizeMax": 10, "speed": 72, "drift": 18, "color": (255, 142, 82), "accent": (255, 217, 148), "shape": "ember"},
    "sparkles": {"density": 22, "sizeMin": 6, "sizeMax": 12, "speed": 34, "drift": 12, "color": (175, 213, 255), "accent": (235, 243, 255), "shape": "spark"},
    "bubbles": {"density": 18, "sizeMin": 10, "sizeMax": 20, "speed": -42, "drift": 12, "color": (150, 220, 255), "accent": (239, 250, 255), "shape": "bubble"},
    "confetti": {"density": 28, "sizeMin": 6, "sizeMax": 12, "speed": 110, "drift": 42, "color": (118, 159, 255), "accent": (185, 115, 255), "shape": "confetti"},
    "smoke": {"density": 20, "sizeMin": 18, "sizeMax": 42, "speed": -24, "drift": 16, "color": (149, 164, 196), "accent": (214, 222, 242), "shape": "smoke"},
    "flame": {"density": 24, "sizeMin": 10, "sizeMax": 22, "speed": -110, "drift": 12, "color": (255, 132, 63), "accent": (255, 214, 104), "shape": "flame"},
    "stardust": {"density": 28, "sizeMin": 4, "sizeMax": 10, "speed": 20, "drift": 8, "color": (126, 173, 255), "accent": (201, 140, 255), "shape": "star"},
    "glyphs": {"density": 16, "sizeMin": 12, "sizeMax": 22, "speed": 12, "drift": 6, "color": (124, 167, 255), "accent": (196, 126, 255), "shape": "glyph"},
}
NATIVE_PARTICLE_INTENSITY_MULTIPLIER = {"light": 0.65, "medium": 1.0, "heavy": 1.45}
NATIVE_PARTICLE_SPEED_MULTIPLIER = {"slow": 0.72, "medium": 1.0, "fast": 1.35}
NATIVE_PARTICLE_WIND_VALUE = {"left": -26, "still": 0, "right": 26}
NATIVE_PARTICLE_AREA_RANGES = {
    "full": (0.04, 0.96),
    "left": (0.04, 0.46),
    "center": (0.28, 0.72),
    "right": (0.54, 0.96),
}
EFFECT_DURATION_SECONDS = {"short": 0.42, "medium": 0.72, "long": 1.2}
SHAKE_DISTANCE = {"light": 4, "medium": 9, "heavy": 16}
FLASH_COLORS = {"white": (255, 255, 255), "warm": (255, 206, 138), "red": (255, 94, 94), "black": (0, 0, 0)}
FLASH_ALPHA = {"soft": 86, "medium": 146, "strong": 210}
FADE_COLORS = {"black": (0, 0, 0), "white": (255, 255, 255)}
CAMERA_ZOOM_SCALE = {
    ("zoom_in", "light"): 1.045,
    ("zoom_in", "medium"): 1.085,
    ("zoom_in", "heavy"): 1.13,
    ("zoom_out", "light"): 0.985,
    ("zoom_out", "medium"): 0.96,
    ("zoom_out", "heavy"): 0.925,
}
CAMERA_PAN_OFFSET = {"left": 0.055, "right": -0.055}
CAMERA_PAN_STRENGTH_MULTIPLIER = {"light": 0.62, "medium": 1.0, "heavy": 1.44}
SCREEN_FILTER_WASH = {
    "memory": ((255, 207, 150), 38),
    "mono": ((180, 190, 205), 42),
    "dream": ((172, 145, 255), 44),
    "cold": ((122, 184, 255), 42),
}
SCREEN_FILTER_STRENGTH_MULTIPLIER = {"soft": 0.62, "medium": 1.0, "strong": 1.38}
SCREEN_COLOR_GRADE_DEFAULTS = {
    "brightness": 100,
    "contrast": 100,
    "saturation": 100,
    "hue": 0,
    "temperature": 0,
    "vignette": 0,
}
SCREEN_COLOR_GRADE_LIMITS = {
    "brightness": (40, 180),
    "contrast": (40, 180),
    "saturation": (0, 220),
    "hue": (-180, 180),
    "temperature": (-100, 100),
    "vignette": (0, 100),
}
DEPTH_BLUR_ALPHA = {"soft": 24, "medium": 42, "strong": 64}
SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
SUPPORTED_AUDIO_EXTENSIONS = {".ogg", ".wav", ".mp3"}
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".m4v"}
SUPPORTED_FONT_EXTENSIONS = {".ttf", ".otf", ".ttc"}
SUPPORTED_LIVE2D_SUFFIXES = (
    ".model3.json",
    ".moc3",
    ".motion3.json",
    ".physics3.json",
    ".cdi3.json",
    ".pose3.json",
    ".exp3.json",
    ".userdata3.json",
)
LIVE2D_REFERENCE_SUFFIXES = SUPPORTED_LIVE2D_SUFFIXES[1:] + (".png", ".jpg", ".jpeg", ".webp", ".bmp")
SUPPORTED_MODEL3D_EXTENSIONS = {".glb", ".gltf", ".vrm", ".fbx", ".obj"}
SUPPORTED_SCENE3D_EXTENSIONS = SUPPORTED_MODEL3D_EXTENSIONS
LARGE_IMAGE_WARNING_BYTES = 18 * 1024 * 1024
LARGE_AUDIO_WARNING_BYTES = 30 * 1024 * 1024
LARGE_VIDEO_WARNING_BYTES = 300 * 1024 * 1024
MAX_EMBEDDED_VIDEO_AUDIO_BUFFER_BYTES = 96 * 1024 * 1024


class NativeRuntimeError(RuntimeError):
    pass


def load_game_data(game_data_path: Path) -> dict:
    if not game_data_path.is_file():
        raise NativeRuntimeError(f"没有找到游戏数据文件：{game_data_path}")
    return json.loads(game_data_path.read_text(encoding="utf-8"))


def normalize_language_code(value: object, fallback: str = DEFAULT_PROJECT_LANGUAGE) -> str:
    raw_value = str(value or "").strip()
    if not raw_value or not re.fullmatch(r"[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8}){0,2}", raw_value):
        return fallback
    parts = raw_value.split("-")
    normalized = [parts[0].lower()]
    for index, part in enumerate(parts[1:], start=1):
        normalized.append(part.upper() if index == 1 and len(part) in {2, 3} else part)
    return "-".join(normalized)


def normalize_supported_languages(value: object, default_language: str = DEFAULT_PROJECT_LANGUAGE) -> list[str]:
    languages: list[str] = []
    for raw_language in value if isinstance(value, list) else []:
        language = normalize_language_code(raw_language, "")
        if language and language not in languages:
            languages.append(language)
    if default_language and default_language not in languages:
        languages.insert(0, default_language)
    return languages or [DEFAULT_PROJECT_LANGUAGE]


def looks_like_live2d_file_reference(value: object) -> bool:
    if not isinstance(value, str):
        return False
    clean_value = value.strip().replace("\\", "/")
    if not clean_value or "://" in clean_value or clean_value.startswith(("data:", "#")):
        return False
    lower_value = clean_value.split("?", 1)[0].split("#", 1)[0].lower()
    if any(lower_value.endswith(suffix) for suffix in LIVE2D_REFERENCE_SUFFIXES):
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


def resolve_live2d_dependency_path(model3_path: Path, reference: str, bundle_dir: Path) -> Path | None:
    clean_reference = reference.strip().replace("\\", "/")
    if not clean_reference or "://" in clean_reference:
        return None
    relative_reference = Path(clean_reference)
    if relative_reference.is_absolute() or clean_reference.startswith("/"):
        return None
    candidate_path = (model3_path.parent / relative_reference).resolve()
    bundle_root = bundle_dir.resolve()
    try:
        candidate_path.relative_to(bundle_root)
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


def summarize_gltf_payload_structure(gltf_payload: object, source_type: str = "gltf") -> dict:
    empty_counts = {
        "nodes": 0,
        "meshes": 0,
        "meshPrimitives": 0,
        "materials": 0,
        "images": 0,
        "textures": 0,
        "animations": 0,
        "cameras": 0,
        "skins": 0,
        "lights": 0,
        "scenes": 0,
        "nodeWithMeshCount": 0,
    }
    if not isinstance(gltf_payload, dict):
        return {
            **empty_counts,
            "status": "invalid",
            "sourceType": source_type,
            "defaultSceneIndex": None,
            "defaultSceneName": "",
            "label": "结构：gltf 入口不是对象",
        }

    def count_list(key: str) -> int:
        value = gltf_payload.get(key)
        return len(value) if isinstance(value, list) else 0

    nodes = gltf_payload.get("nodes") if isinstance(gltf_payload.get("nodes"), list) else []
    meshes = gltf_payload.get("meshes") if isinstance(gltf_payload.get("meshes"), list) else []
    scenes = gltf_payload.get("scenes") if isinstance(gltf_payload.get("scenes"), list) else []
    extensions = gltf_payload.get("extensions") if isinstance(gltf_payload.get("extensions"), dict) else {}
    light_extension = extensions.get("KHR_lights_punctual") if isinstance(extensions.get("KHR_lights_punctual"), dict) else {}
    lights = light_extension.get("lights") if isinstance(light_extension.get("lights"), list) else []
    mesh_primitive_count = sum(
        len(mesh.get("primitives")) if isinstance(mesh, dict) and isinstance(mesh.get("primitives"), list) else 0
        for mesh in meshes
    )
    node_with_mesh_count = sum(1 for node in nodes if isinstance(node, dict) and "mesh" in node)
    raw_default_scene_index = gltf_payload.get("scene")
    default_scene_index = raw_default_scene_index if isinstance(raw_default_scene_index, int) else None
    default_scene_name = ""
    if default_scene_index is not None and 0 <= default_scene_index < len(scenes):
        default_scene = scenes[default_scene_index]
        if isinstance(default_scene, dict):
            default_scene_name = str(default_scene.get("name") or "")
    texture_count = max(count_list("textures"), count_list("images"))
    structure = {
        "nodes": len(nodes),
        "meshes": len(meshes),
        "meshPrimitives": mesh_primitive_count,
        "materials": count_list("materials"),
        "images": count_list("images"),
        "textures": texture_count,
        "animations": count_list("animations"),
        "cameras": count_list("cameras"),
        "skins": count_list("skins"),
        "lights": len(lights),
        "scenes": len(scenes),
        "nodeWithMeshCount": node_with_mesh_count,
        "defaultSceneIndex": default_scene_index,
        "defaultSceneName": default_scene_name,
        "sourceType": source_type,
    }
    if len(nodes) == 0 and len(meshes) == 0:
        return {**structure, "status": "empty", "label": "结构：未发现节点/网格"}

    label_parts = [f"{len(nodes)} 节点", f"{len(meshes)} 网格"]
    if mesh_primitive_count:
        label_parts.append(f"{mesh_primitive_count} primitive")
    if count_list("materials"):
        label_parts.append(f"{count_list('materials')} 材质")
    if texture_count:
        label_parts.append(f"{texture_count} 贴图")
    if count_list("animations"):
        label_parts.append(f"{count_list('animations')} 动画")
    if len(lights):
        label_parts.append(f"{len(lights)} 灯光")
    if default_scene_name:
        label_parts.append(f"默认场景 {default_scene_name}")
    return {**structure, "status": "ready", "label": "结构：" + " · ".join(label_parts)}


def summarize_gltf_structure(model_path: Path | None) -> dict:
    empty_counts = {
        "nodes": 0,
        "meshes": 0,
        "meshPrimitives": 0,
        "materials": 0,
        "images": 0,
        "textures": 0,
        "animations": 0,
        "cameras": 0,
        "skins": 0,
        "lights": 0,
        "scenes": 0,
        "nodeWithMeshCount": 0,
        "defaultSceneIndex": None,
        "defaultSceneName": "",
    }
    if not model_path:
        return {**empty_counts, "status": "unknown", "sourceType": "", "label": "结构：待检测"}

    extension = model_path.suffix.lower()
    if extension in {".gltf", ".glb", ".vrm"}:
        payload, source_type, container_probe, error = load_gltf_static_payload(model_path)
        if payload is None:
            return {
                **empty_counts,
                "status": "invalid",
                "sourceType": source_type,
                "label": f"结构：{error or '入口异常'}",
                "containerProbe": container_probe or {},
            }
        structure = summarize_gltf_payload_structure(payload, source_type)
        if container_probe:
            structure["containerProbe"] = container_probe
            if container_probe.get("status") == "needs_attention" and structure.get("status") == "ready":
                structure["status"] = "partial"
            structure["label"] = f"{structure.get('label') or '结构：已解析'} · {container_probe.get('label')}"
        return structure
    if extension in {".fbx", ".obj"}:
        return {
            **empty_counts,
            "status": "unsupported",
            "sourceType": extension[1:],
            "label": "结构：需转换为 gltf/glb 后分析",
        }
    return {**empty_counts, "status": "unknown", "sourceType": extension[1:], "label": "结构：待检测"}


GLTF_MATERIAL_TEXTURE_SLOTS = [
    ("baseColorTexture", "基础色贴图", ("pbrMetallicRoughness", "baseColorTexture")),
    ("metallicRoughnessTexture", "金属/粗糙度贴图", ("pbrMetallicRoughness", "metallicRoughnessTexture")),
    ("normalTexture", "法线贴图", ("normalTexture",)),
    ("occlusionTexture", "遮蔽贴图", ("occlusionTexture",)),
    ("emissiveTexture", "自发光贴图", ("emissiveTexture",)),
]
GLTF_ANIMATION_TARGET_PATHS = {"translation", "rotation", "scale", "weights"}
GLB_MAGIC = b"glTF"
GLB_VERSION = 2
GLB_JSON_CHUNK_TYPE = 0x4E4F534A
GLB_BIN_CHUNK_TYPE = 0x004E4942
GLTF_PERFORMANCE_BUDGETS = {
    "model3d": {
        "estimatedVertexCount": 120_000,
        "estimatedTriangleCount": 70_000,
        "drawCallCount": 64,
        "materialCount": 32,
        "textureCount": 48,
        "animationChannelCount": 180,
        "skinCount": 4,
    },
    "scene3d": {
        "estimatedVertexCount": 350_000,
        "estimatedTriangleCount": 200_000,
        "drawCallCount": 160,
        "materialCount": 80,
        "textureCount": 96,
        "animationChannelCount": 300,
        "skinCount": 8,
    },
}


def get_gltf_list(gltf_payload: dict, key: str) -> list:
    value = gltf_payload.get(key)
    return value if isinstance(value, list) else []


def get_nested_dict(source: dict, path: tuple[str, ...]) -> dict:
    current: object = source
    for key in path:
        if not isinstance(current, dict):
            return {}
        current = current.get(key)
    return current if isinstance(current, dict) else {}


def get_glb_chunk_type_label(chunk_type: int) -> str:
    if chunk_type == GLB_JSON_CHUNK_TYPE:
        return "JSON"
    if chunk_type == GLB_BIN_CHUNK_TYPE:
        return "BIN"
    raw = chunk_type.to_bytes(4, "little", signed=False)
    if all(32 <= byte <= 126 for byte in raw):
        return raw.decode("ascii", errors="replace")
    return f"0x{chunk_type:08X}"


def build_glb_container_issue(code: str, path: str, message: str, suggestion: str) -> dict:
    return {"code": code, "path": path, "message": message, "suggestion": suggestion}


def parse_glb_json_payload(model_path: Path) -> tuple[dict | None, dict]:
    source_type = model_path.suffix.lower().lstrip(".") or "glb"
    try:
        raw = model_path.read_bytes()
    except Exception as error:
        return None, {
            "status": "invalid",
            "sourceType": source_type,
            "label": f"GLB 容器：无法读取文件（{error}）",
            "fileSize": 0,
            "declaredLength": 0,
            "version": None,
            "chunkCount": 0,
            "jsonByteLength": 0,
            "binByteLength": 0,
            "issueCount": 1,
            "issues": [
                build_glb_container_issue(
                    "glb_file_read_failed",
                    str(model_path),
                    f"无法读取 {source_type.upper()} 文件。",
                    "确认文件没有被移动、锁定或损坏后重新导出。",
                )
            ],
            "chunks": [],
        }

    file_size = len(raw)
    issues: list[dict] = []
    if file_size < 12:
        return None, {
            "status": "invalid",
            "sourceType": source_type,
            "label": "GLB 容器：文件头不足 12 字节",
            "fileSize": file_size,
            "declaredLength": 0,
            "version": None,
            "chunkCount": 0,
            "jsonByteLength": 0,
            "binByteLength": 0,
            "issueCount": 1,
            "issues": [
                build_glb_container_issue(
                    "glb_header_too_short",
                    "header",
                    "GLB/VRM 文件头不足，无法读取 magic、version 和 length。",
                    "重新从建模工具导出完整的 GLB/VRM 文件。",
                )
            ],
            "chunks": [],
        }

    magic = raw[:4]
    version = int.from_bytes(raw[4:8], "little")
    declared_length = int.from_bytes(raw[8:12], "little")
    if magic != GLB_MAGIC:
        issues.append(
            build_glb_container_issue(
                "glb_magic_invalid",
                "header.magic",
                "文件头 magic 不是 glTF。",
                "确认文件确实是 GLB/VRM，而不是改后缀的其他格式。",
            )
        )
    if version != GLB_VERSION:
        issues.append(
            build_glb_container_issue(
                "glb_version_unsupported",
                "header.version",
                f"GLB version 为 {version}，当前静态检查按 2.0 解析。",
                "建议重新导出为 glTF/GLB 2.0。",
            )
        )
    if declared_length != file_size:
        issues.append(
            build_glb_container_issue(
                "glb_declared_length_mismatch",
                "header.length",
                f"GLB 声明长度 {declared_length} 与实际文件大小 {file_size} 不一致。",
                "重新导出文件，避免二进制包被截断或拼接了额外数据。",
            )
        )

    if magic != GLB_MAGIC or version != GLB_VERSION or declared_length < 12:
        return None, {
            "status": "invalid",
            "sourceType": source_type,
            "label": "GLB 容器：文件头异常",
            "fileSize": file_size,
            "declaredLength": declared_length,
            "version": version,
            "chunkCount": 0,
            "jsonByteLength": 0,
            "binByteLength": 0,
            "issueCount": len(issues),
            "issues": issues[:16],
            "chunks": [],
        }

    data_limit = min(file_size, declared_length)
    chunks: list[dict] = []
    offset = 12
    json_payload: dict | None = None
    json_byte_length = 0
    bin_byte_length = 0
    while offset + 8 <= data_limit:
        chunk_length = int.from_bytes(raw[offset : offset + 4], "little")
        chunk_type = int.from_bytes(raw[offset + 4 : offset + 8], "little")
        chunk_start = offset + 8
        chunk_end = chunk_start + chunk_length
        type_label = get_glb_chunk_type_label(chunk_type)
        chunks.append({"type": type_label, "byteLength": chunk_length, "offset": offset})
        if chunk_end > data_limit:
            issues.append(
                build_glb_container_issue(
                    "glb_chunk_overflow",
                    f"chunks[{len(chunks) - 1}]",
                    f"{type_label} chunk 超出 GLB 声明长度。",
                    "重新导出文件，或检查打包/上传过程是否截断了二进制数据。",
                )
            )
            break
        chunk_data = raw[chunk_start:chunk_end]
        if chunk_type == GLB_JSON_CHUNK_TYPE and json_payload is None:
            json_byte_length = chunk_length
            try:
                decoded = chunk_data.rstrip(b" \t\r\n\x00").decode("utf-8")
                parsed = json.loads(decoded)
            except Exception as error:
                issues.append(
                    build_glb_container_issue(
                        "glb_json_chunk_invalid",
                        f"chunks[{len(chunks) - 1}]",
                        f"JSON chunk 无法解析：{error}",
                        "重新导出有效的 GLB/VRM，或先转成 .gltf 方便定位 JSON 问题。",
                    )
                )
            else:
                if isinstance(parsed, dict):
                    json_payload = parsed
                else:
                    issues.append(
                        build_glb_container_issue(
                            "glb_json_root_invalid",
                            f"chunks[{len(chunks) - 1}]",
                            "JSON chunk 根节点不是对象。",
                            "重新导出有效的 glTF 2.0 JSON 内容。",
                        )
                    )
        elif chunk_type == GLB_BIN_CHUNK_TYPE:
            bin_byte_length += chunk_length
        offset = chunk_end

    if offset < data_limit:
        issues.append(
            build_glb_container_issue(
                "glb_trailing_bytes",
                "chunks",
                "GLB chunk 表末尾存在无法解析的尾部字节。",
                "重新导出文件，确认所有 chunk 都按 4 字节对齐。",
            )
        )
    if json_payload is None and not any(issue.get("code") == "glb_json_chunk_invalid" for issue in issues):
        issues.append(
            build_glb_container_issue(
                "glb_json_chunk_missing",
                "chunks",
                "GLB/VRM 缺少 JSON chunk，无法读取结构和材质元数据。",
                "重新导出标准 GLB/VRM 文件；标准文件必须包含一个 JSON chunk。",
            )
        )

    issue_count = len(issues)
    if json_payload is None:
        status = "invalid"
    elif issue_count:
        status = "needs_attention"
    else:
        status = "ready"
    label = (
        f"{source_type.upper()} 容器：JSON {json_byte_length} bytes / BIN {bin_byte_length} bytes"
        if json_payload is not None
        else f"{source_type.upper()} 容器：无法读取 JSON chunk"
    )
    if issue_count:
        label += f" · {issue_count} 个容器问题"
    return json_payload, {
        "status": status,
        "sourceType": source_type,
        "label": label,
        "fileSize": file_size,
        "declaredLength": declared_length,
        "version": version,
        "chunkCount": len(chunks),
        "jsonByteLength": json_byte_length,
        "binByteLength": bin_byte_length,
        "issueCount": issue_count,
        "issues": issues[:16],
        "chunks": chunks[:8],
    }


def load_gltf_static_payload(model_path: Path) -> tuple[dict | None, str, dict | None, str]:
    extension = model_path.suffix.lower()
    source_type = extension.lstrip(".") or "unknown"
    if extension == ".gltf":
        try:
            payload = json.loads(model_path.read_text(encoding="utf-8"))
        except Exception as error:
            return None, "gltf", None, f"gltf JSON 异常：{error}"
        if not isinstance(payload, dict):
            return None, "gltf", None, "gltf 入口不是对象"
        return payload, "gltf", None, ""
    if extension in {".glb", ".vrm"}:
        payload, container_probe = parse_glb_json_payload(model_path)
        error = "" if payload is not None else str(container_probe.get("label") or "GLB 容器异常")
        return payload, source_type, container_probe, error
    return None, source_type, None, "不是可静态解析的 glTF/GLB/VRM 文件"


def build_gltf_integrity_probe(gltf_payload: object) -> dict:
    if not isinstance(gltf_payload, dict):
        return {
            "status": "invalid",
            "label": "完整性：gltf 入口不是对象",
            "issueCount": 1,
            "issues": [
                {
                    "code": "gltf_root_invalid",
                    "path": "$",
                    "message": "glTF 根节点不是对象。",
                    "suggestion": "请重新导出有效的 .gltf，或改用自包含 .glb。",
                }
            ],
        }

    issues: list[dict] = []
    scenes = get_gltf_list(gltf_payload, "scenes")
    nodes = get_gltf_list(gltf_payload, "nodes")
    meshes = get_gltf_list(gltf_payload, "meshes")
    materials = get_gltf_list(gltf_payload, "materials")
    textures = get_gltf_list(gltf_payload, "textures")
    images = get_gltf_list(gltf_payload, "images")
    cameras = get_gltf_list(gltf_payload, "cameras")
    skins = get_gltf_list(gltf_payload, "skins")
    accessors = get_gltf_list(gltf_payload, "accessors")
    samplers = get_gltf_list(gltf_payload, "samplers")
    extensions = gltf_payload.get("extensions") if isinstance(gltf_payload.get("extensions"), dict) else {}
    light_extension = extensions.get("KHR_lights_punctual") if isinstance(extensions.get("KHR_lights_punctual"), dict) else {}
    lights = light_extension.get("lights") if isinstance(light_extension.get("lights"), list) else []

    def add_issue(code: str, path: str, message: str, suggestion: str) -> None:
        issues.append({"code": code, "path": path, "message": message, "suggestion": suggestion})

    def check_index(value: object, collection: list, code: str, path: str, label: str) -> None:
        if value is None:
            return
        if not isinstance(value, int) or not (0 <= value < len(collection)):
            add_issue(code, path, f"{label} 指向不存在的索引：{value}", "回到 DCC/建模工具重新导出，或修正 glTF 内部索引引用。")

    if "scene" in gltf_payload:
        check_index(gltf_payload.get("scene"), scenes, "gltf_default_scene_missing", "scene", "默认场景")

    for scene_index, scene in enumerate(scenes):
        scene = scene if isinstance(scene, dict) else {}
        scene_nodes = scene.get("nodes") if isinstance(scene.get("nodes"), list) else []
        for node_position, node_index in enumerate(scene_nodes):
            check_index(
                node_index,
                nodes,
                "gltf_scene_node_missing",
                f"scenes[{scene_index}].nodes[{node_position}]",
                "场景节点",
            )

    for node_index, node in enumerate(nodes):
        node = node if isinstance(node, dict) else {}
        check_index(node.get("mesh"), meshes, "gltf_node_mesh_missing", f"nodes[{node_index}].mesh", "节点网格")
        check_index(node.get("camera"), cameras, "gltf_node_camera_missing", f"nodes[{node_index}].camera", "节点相机")
        check_index(node.get("skin"), skins, "gltf_node_skin_missing", f"nodes[{node_index}].skin", "节点骨骼")
        children = node.get("children") if isinstance(node.get("children"), list) else []
        for child_position, child_index in enumerate(children):
            check_index(
                child_index,
                nodes,
                "gltf_node_child_missing",
                f"nodes[{node_index}].children[{child_position}]",
                "子节点",
            )
        node_extensions = node.get("extensions") if isinstance(node.get("extensions"), dict) else {}
        light_ref = node_extensions.get("KHR_lights_punctual") if isinstance(node_extensions.get("KHR_lights_punctual"), dict) else {}
        check_index(light_ref.get("light"), lights, "gltf_node_light_missing", f"nodes[{node_index}].extensions.KHR_lights_punctual.light", "节点灯光")

    for mesh_index, mesh in enumerate(meshes):
        mesh = mesh if isinstance(mesh, dict) else {}
        primitives = mesh.get("primitives") if isinstance(mesh.get("primitives"), list) else []
        if not primitives:
            add_issue(
                "gltf_mesh_without_primitives",
                f"meshes[{mesh_index}].primitives",
                "网格没有 primitive，渲染时可能不可见。",
                "确认模型导出时包含实际几何体，或删除空网格。",
            )
        for primitive_index, primitive in enumerate(primitives):
            primitive = primitive if isinstance(primitive, dict) else {}
            primitive_path = f"meshes[{mesh_index}].primitives[{primitive_index}]"
            check_index(primitive.get("material"), materials, "gltf_primitive_material_missing", f"{primitive_path}.material", "primitive 材质")
            check_index(primitive.get("indices"), accessors, "gltf_primitive_indices_accessor_missing", f"{primitive_path}.indices", "primitive 索引 accessor")
            attributes = primitive.get("attributes") if isinstance(primitive.get("attributes"), dict) else {}
            if not attributes:
                add_issue(
                    "gltf_primitive_without_attributes",
                    f"{primitive_path}.attributes",
                    "primitive 没有 attributes，渲染后端可能无法构建顶点。",
                    "至少确认 POSITION accessor 存在；如果是占位模型，发布前请替换为正式资源。",
                )
            for attribute_name, accessor_index in attributes.items():
                check_index(
                    accessor_index,
                    accessors,
                    "gltf_attribute_accessor_missing",
                    f"{primitive_path}.attributes.{attribute_name}",
                    f"{attribute_name} accessor",
                )

    for texture_index, texture in enumerate(textures):
        texture = texture if isinstance(texture, dict) else {}
        check_index(texture.get("source"), images, "gltf_texture_image_missing", f"textures[{texture_index}].source", "纹理图片")
        check_index(texture.get("sampler"), samplers, "gltf_texture_sampler_missing", f"textures[{texture_index}].sampler", "纹理采样器")

    for skin_index, skin in enumerate(skins):
        skin = skin if isinstance(skin, dict) else {}
        joints = skin.get("joints") if isinstance(skin.get("joints"), list) else []
        for joint_position, joint_index in enumerate(joints):
            check_index(joint_index, nodes, "gltf_skin_joint_missing", f"skins[{skin_index}].joints[{joint_position}]", "骨骼 joint")
        check_index(skin.get("inverseBindMatrices"), accessors, "gltf_skin_inverse_bind_accessor_missing", f"skins[{skin_index}].inverseBindMatrices", "inverseBindMatrices accessor")

    animations = get_gltf_list(gltf_payload, "animations")
    for animation_index, animation in enumerate(animations):
        animation = animation if isinstance(animation, dict) else {}
        animation_samplers = animation.get("samplers") if isinstance(animation.get("samplers"), list) else []
        channels = animation.get("channels") if isinstance(animation.get("channels"), list) else []
        if not channels:
            add_issue(
                "gltf_animation_without_channels",
                f"animations[{animation_index}].channels",
                "动画没有 channel，运行时不会产生可见变化。",
                "确认动画导出设置包含目标节点和 transform 通道。",
            )
        for sampler_index, sampler in enumerate(animation_samplers):
            sampler = sampler if isinstance(sampler, dict) else {}
            check_index(sampler.get("input"), accessors, "gltf_animation_input_accessor_missing", f"animations[{animation_index}].samplers[{sampler_index}].input", "动画 input accessor")
            check_index(sampler.get("output"), accessors, "gltf_animation_output_accessor_missing", f"animations[{animation_index}].samplers[{sampler_index}].output", "动画 output accessor")
        for channel_index, channel in enumerate(channels):
            channel = channel if isinstance(channel, dict) else {}
            channel_path = f"animations[{animation_index}].channels[{channel_index}]"
            check_index(channel.get("sampler"), animation_samplers, "gltf_animation_sampler_missing", f"{channel_path}.sampler", "动画 channel sampler")
            target = channel.get("target") if isinstance(channel.get("target"), dict) else {}
            check_index(target.get("node"), nodes, "gltf_animation_target_node_missing", f"{channel_path}.target.node", "动画目标节点")
            target_path = str(target.get("path") or "").strip()
            if target_path and target_path not in GLTF_ANIMATION_TARGET_PATHS:
                add_issue(
                    "gltf_animation_target_path_unknown",
                    f"{channel_path}.target.path",
                    f"动画目标路径暂不常见：{target_path}",
                    "建议使用 translation、rotation、scale 或 weights；自定义扩展动画需要后续渲染后端专门适配。",
                )

    issue_count = len(issues)
    label = "完整性：内部索引可解析" if issue_count == 0 else f"完整性：发现 {issue_count} 个内部引用问题"
    return {
        "status": "ready" if issue_count == 0 else "needs_attention",
        "label": label,
        "issueCount": issue_count,
        "issues": issues[:24],
    }


def get_gltf_accessor_count(accessors: list, index: object) -> int:
    if not isinstance(index, int) or not (0 <= index < len(accessors)):
        return 0
    accessor = accessors[index] if isinstance(accessors[index], dict) else {}
    count = accessor.get("count")
    return int(count) if isinstance(count, int) and count > 0 else 0


def estimate_gltf_triangle_count(mode: int, element_count: int) -> int:
    if element_count <= 0:
        return 0
    if mode == 4:
        return element_count // 3
    if mode in {5, 6}:
        return max(0, element_count - 2)
    return 0


def build_gltf_performance_budget_probe(gltf_payload: object, asset_type: str) -> dict:
    if not isinstance(gltf_payload, dict):
        return {
            "status": "invalid",
            "label": "预算：无法读取 glTF 元数据",
            "issueCount": 1,
            "issues": [
                {
                    "metric": "root",
                    "message": "glTF 根节点不是对象，无法估算性能预算。",
                    "suggestion": "重新导出有效的 glTF/GLB/VRM 后再检查预算。",
                }
            ],
            "metrics": {},
            "limits": GLTF_PERFORMANCE_BUDGETS.get(asset_type, GLTF_PERFORMANCE_BUDGETS["scene3d"]),
            "primitives": [],
        }

    meshes = get_gltf_list(gltf_payload, "meshes")
    materials = get_gltf_list(gltf_payload, "materials")
    textures = get_gltf_list(gltf_payload, "textures")
    images = get_gltf_list(gltf_payload, "images")
    animations = get_gltf_list(gltf_payload, "animations")
    skins = get_gltf_list(gltf_payload, "skins")
    accessors = get_gltf_list(gltf_payload, "accessors")
    limits = GLTF_PERFORMANCE_BUDGETS.get(asset_type, GLTF_PERFORMANCE_BUDGETS["scene3d"])
    primitive_entries: list[dict] = []
    estimated_vertex_count = 0
    estimated_triangle_count = 0
    draw_call_count = 0
    unknown_geometry_count = 0

    for mesh_index, mesh in enumerate(meshes):
        mesh = mesh if isinstance(mesh, dict) else {}
        primitives = mesh.get("primitives") if isinstance(mesh.get("primitives"), list) else []
        for primitive_index, primitive in enumerate(primitives):
            primitive = primitive if isinstance(primitive, dict) else {}
            draw_call_count += 1
            mode = primitive.get("mode", 4)
            mode = int(mode) if isinstance(mode, int) else 4
            attributes = primitive.get("attributes") if isinstance(primitive.get("attributes"), dict) else {}
            position_accessor = attributes.get("POSITION")
            vertex_count = get_gltf_accessor_count(accessors, position_accessor)
            index_count = get_gltf_accessor_count(accessors, primitive.get("indices"))
            element_count = index_count or vertex_count
            triangle_count = estimate_gltf_triangle_count(mode, element_count)
            estimated_vertex_count += vertex_count
            estimated_triangle_count += triangle_count
            if vertex_count == 0:
                unknown_geometry_count += 1
            primitive_entries.append(
                {
                    "meshIndex": mesh_index,
                    "primitiveIndex": primitive_index,
                    "mode": mode,
                    "vertexCount": vertex_count,
                    "indexCount": index_count,
                    "estimatedTriangleCount": triangle_count,
                    "materialIndex": primitive.get("material") if isinstance(primitive.get("material"), int) else None,
                }
            )

    animation_channel_count = sum(
        len(animation.get("channels")) if isinstance(animation, dict) and isinstance(animation.get("channels"), list) else 0
        for animation in animations
    )
    metrics = {
        "estimatedVertexCount": estimated_vertex_count,
        "estimatedTriangleCount": estimated_triangle_count,
        "drawCallCount": draw_call_count,
        "materialCount": len(materials),
        "textureCount": max(len(textures), len(images)),
        "animationChannelCount": animation_channel_count,
        "skinCount": len(skins),
        "unknownGeometryPrimitiveCount": unknown_geometry_count,
    }
    issue_labels = {
        "estimatedVertexCount": "顶点数",
        "estimatedTriangleCount": "三角面",
        "drawCallCount": "draw call",
        "materialCount": "材质数量",
        "textureCount": "贴图数量",
        "animationChannelCount": "动画通道",
        "skinCount": "骨骼/skin 数量",
    }
    issues = []
    for metric, limit in limits.items():
        value = int(metrics.get(metric) or 0)
        if value > int(limit):
            label = issue_labels.get(metric, metric)
            issues.append(
                {
                    "metric": metric,
                    "label": label,
                    "value": value,
                    "limit": int(limit),
                    "message": f"{label} {value} 超过建议预算 {limit}。",
                    "suggestion": "建议合批网格、降低面数、压缩材质数量或拆分场景后再发布。",
                }
            )

    issue_count = len(issues)
    label = (
        f"预算：{draw_call_count} draw call / {estimated_triangle_count} 三角面 / {estimated_vertex_count} 顶点"
    )
    if issue_count:
        label += f" · {issue_count} 项超预算"
    elif unknown_geometry_count:
        label += f" · {unknown_geometry_count} 个 primitive 缺少可估算顶点数"
    return {
        "status": "needs_attention" if issue_count else "ready",
        "label": label,
        "issueCount": issue_count,
        "issues": issues,
        "metrics": metrics,
        "limits": limits,
        "primitives": primitive_entries[:24],
    }


def resolve_gltf_texture_uri(
    model_path: Path,
    bundle_dir: Path,
    textures: list,
    images: list,
    texture_index: int | None,
) -> dict:
    if texture_index is None or not (0 <= texture_index < len(textures)):
        return {"status": "missing_texture", "textureIndex": texture_index, "imageIndex": None, "uri": ""}
    texture = textures[texture_index] if isinstance(textures[texture_index], dict) else {}
    image_index = texture.get("source")
    if not isinstance(image_index, int) or not (0 <= image_index < len(images)):
        return {"status": "missing_image", "textureIndex": texture_index, "imageIndex": image_index, "uri": ""}
    image = images[image_index] if isinstance(images[image_index], dict) else {}
    uri = str(image.get("uri") or "").strip()
    if not uri and image.get("bufferView") is not None:
        return {"status": "embedded", "textureIndex": texture_index, "imageIndex": image_index, "uri": ""}
    if uri.startswith("data:"):
        return {"status": "embedded", "textureIndex": texture_index, "imageIndex": image_index, "uri": "data:"}
    if not uri:
        return {"status": "missing_uri", "textureIndex": texture_index, "imageIndex": image_index, "uri": ""}
    dependency_path = resolve_model3d_dependency_path(model_path, uri, bundle_dir)
    if dependency_path is None:
        status = "unsafe_uri"
    elif dependency_path.is_file():
        status = "ready"
    else:
        status = "missing_file"
    return {
        "status": status,
        "textureIndex": texture_index,
        "imageIndex": image_index,
        "uri": uri,
    }


def summarize_gltf_preview_probe(model_path: Path | None, bundle_dir: Path) -> dict:
    empty_summary = {
        "materialCount": 0,
        "texturedMaterialCount": 0,
        "textureSlotCount": 0,
        "textureSlotReadyCount": 0,
        "textureSlotIssueCount": 0,
        "animationCount": 0,
        "animationChannelCount": 0,
        "cameraCount": 0,
        "lightCount": 0,
    }
    if not model_path:
        return {**empty_summary, "status": "unknown", "label": "预览探针：待检测", "materials": [], "animations": [], "cameras": [], "lights": []}

    extension = model_path.suffix.lower()
    if extension in {".gltf", ".glb", ".vrm"}:
        gltf_payload, _source_type, container_probe, error = load_gltf_static_payload(model_path)
        if gltf_payload is None:
            return {
                **empty_summary,
                "status": "invalid",
                "label": f"预览探针：{error or '入口异常'}",
                "materials": [],
                "animations": [],
                "cameras": [],
                "lights": [],
                "containerProbe": container_probe or {},
            }

        textures = get_gltf_list(gltf_payload, "textures")
        images = get_gltf_list(gltf_payload, "images")
        materials = get_gltf_list(gltf_payload, "materials")
        animations = get_gltf_list(gltf_payload, "animations")
        nodes = get_gltf_list(gltf_payload, "nodes")
        cameras = get_gltf_list(gltf_payload, "cameras")
        extensions = gltf_payload.get("extensions") if isinstance(gltf_payload.get("extensions"), dict) else {}
        light_extension = extensions.get("KHR_lights_punctual") if isinstance(extensions.get("KHR_lights_punctual"), dict) else {}
        lights = light_extension.get("lights") if isinstance(light_extension.get("lights"), list) else []

        material_entries = []
        texture_slot_count = 0
        texture_slot_ready_count = 0
        texture_slot_issue_count = 0
        for material_index, material in enumerate(materials):
            material = material if isinstance(material, dict) else {}
            slot_entries = []
            for slot_key, slot_label, slot_path in GLTF_MATERIAL_TEXTURE_SLOTS:
                slot_config = get_nested_dict(material, slot_path)
                if not slot_config:
                    continue
                texture_index = slot_config.get("index")
                texture_index = texture_index if isinstance(texture_index, int) else None
                texture_info = resolve_gltf_texture_uri(model_path, bundle_dir, textures, images, texture_index)
                slot_status = str(texture_info.get("status") or "unknown")
                texture_slot_count += 1
                if slot_status in {"ready", "embedded"}:
                    texture_slot_ready_count += 1
                else:
                    texture_slot_issue_count += 1
                slot_entries.append(
                    {
                        "slot": slot_key,
                        "label": slot_label,
                        "textureIndex": texture_info.get("textureIndex"),
                        "imageIndex": texture_info.get("imageIndex"),
                        "uri": texture_info.get("uri") or "",
                        "status": slot_status,
                    }
                )
            material_extensions = material.get("extensions") if isinstance(material.get("extensions"), dict) else {}
            material_entries.append(
                {
                    "index": material_index,
                    "name": str(material.get("name") or f"Material {material_index + 1}"),
                    "alphaMode": str(material.get("alphaMode") or "OPAQUE"),
                    "doubleSided": bool(material.get("doubleSided")),
                    "unlit": "KHR_materials_unlit" in material_extensions,
                    "textureSlots": slot_entries,
                    "textureSlotCount": len(slot_entries),
                }
            )

        animation_entries = []
        animation_channel_count = 0
        for animation_index, animation in enumerate(animations):
            animation = animation if isinstance(animation, dict) else {}
            channels = animation.get("channels") if isinstance(animation.get("channels"), list) else []
            samplers = animation.get("samplers") if isinstance(animation.get("samplers"), list) else []
            target_paths: list[str] = []
            target_nodes: list[str] = []
            for channel in channels:
                channel = channel if isinstance(channel, dict) else {}
                target = channel.get("target") if isinstance(channel.get("target"), dict) else {}
                target_path = str(target.get("path") or "").strip()
                if target_path and target_path not in target_paths:
                    target_paths.append(target_path)
                node_index = target.get("node")
                if isinstance(node_index, int) and 0 <= node_index < len(nodes):
                    node = nodes[node_index] if isinstance(nodes[node_index], dict) else {}
                    node_name = str(node.get("name") or f"Node {node_index}")
                    if node_name not in target_nodes:
                        target_nodes.append(node_name)
            animation_channel_count += len(channels)
            animation_entries.append(
                {
                    "index": animation_index,
                    "name": str(animation.get("name") or f"Animation {animation_index + 1}"),
                    "channelCount": len(channels),
                    "samplerCount": len(samplers),
                    "targetPaths": target_paths,
                    "targetNodes": target_nodes[:8],
                }
            )

        camera_entries = [
            {
                "index": camera_index,
                "name": str((camera if isinstance(camera, dict) else {}).get("name") or f"Camera {camera_index + 1}"),
                "type": str((camera if isinstance(camera, dict) else {}).get("type") or "unknown"),
            }
            for camera_index, camera in enumerate(cameras)
        ]
        light_entries = [
            {
                "index": light_index,
                "name": str((light if isinstance(light, dict) else {}).get("name") or f"Light {light_index + 1}"),
                "type": str((light if isinstance(light, dict) else {}).get("type") or "unknown"),
                "intensity": (light if isinstance(light, dict) else {}).get("intensity"),
            }
            for light_index, light in enumerate(lights)
        ]
        if texture_slot_issue_count or (container_probe and container_probe.get("status") == "needs_attention"):
            status = "needs_attention"
        elif materials or animations or cameras or lights:
            status = "ready"
        else:
            status = "minimal"

        label_parts = []
        if materials:
            label_parts.append(f"{len(materials)} 材质")
        if texture_slot_count:
            label_parts.append(f"{texture_slot_ready_count}/{texture_slot_count} 贴图槽可读")
        if animations:
            label_parts.append(f"{len(animations)} 动画")
        if cameras:
            label_parts.append(f"{len(cameras)} 相机")
        if lights:
            label_parts.append(f"{len(lights)} 灯光")
        label = "预览探针：" + (" · ".join(label_parts) if label_parts else "未发现材质/动画/相机元数据")
        return {
            "status": status,
            "label": label,
            "materialCount": len(materials),
            "texturedMaterialCount": sum(1 for entry in material_entries if entry["textureSlotCount"] > 0),
            "textureSlotCount": texture_slot_count,
            "textureSlotReadyCount": texture_slot_ready_count,
            "textureSlotIssueCount": texture_slot_issue_count,
            "animationCount": len(animations),
            "animationChannelCount": animation_channel_count,
            "cameraCount": len(cameras),
            "lightCount": len(lights),
            "materials": material_entries[:12],
            "animations": animation_entries[:12],
            "cameras": camera_entries[:8],
            "lights": light_entries[:8],
            "containerProbe": container_probe or {},
        }

    if extension in {".fbx", ".obj"}:
        return {
            **empty_summary,
            "status": "needs_conversion",
            "label": "预览探针：建议先转换为 gltf/glb 后读取材质/动画",
            "materials": [],
            "animations": [],
            "cameras": [],
            "lights": [],
        }
    return {**empty_summary, "status": "unknown", "label": "预览探针：待检测", "materials": [], "animations": [], "cameras": [], "lights": []}


def resolve_model3d_dependency_path(model_path: Path, reference: str, bundle_dir: Path) -> Path | None:
    clean_reference = reference.strip().replace("\\", "/")
    if not clean_reference or "://" in clean_reference or clean_reference.startswith(("data:", "#")):
        return None
    relative_reference = Path(clean_reference)
    if relative_reference.is_absolute() or clean_reference.startswith("/"):
        return None
    candidate_path = (model_path.parent / relative_reference).resolve()
    bundle_root = bundle_dir.resolve()
    try:
        candidate_path.relative_to(bundle_root)
    except ValueError:
        return None
    return candidate_path


def resolve_default_game_data_path() -> Path:
    candidates: list[Path] = []
    packaged_base = getattr(sys, "_MEIPASS", None)
    if getattr(sys, "frozen", False):
        if packaged_base:
            candidates.append(Path(packaged_base) / DEFAULT_GAME_DATA_NAME)
        candidates.append(Path(sys.executable).resolve().parent / DEFAULT_GAME_DATA_NAME)
    candidates.append(Path.cwd() / DEFAULT_GAME_DATA_NAME)
    candidates.append(Path(__file__).resolve().parent / DEFAULT_GAME_DATA_NAME)
    if not getattr(sys, "frozen", False) and packaged_base:
        candidates.append(Path(packaged_base) / DEFAULT_GAME_DATA_NAME)
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    return candidates[0].resolve()


def resolve_game_data_argument(game_data_value: str) -> Path:
    candidate = Path(game_data_value)
    if game_data_value == DEFAULT_GAME_DATA_NAME and not candidate.is_file():
        return resolve_default_game_data_path()
    return candidate.resolve()


def get_external_video_opener_command(video_path: Path) -> list[str] | None:
    if sys.platform.startswith("win"):
        return None
    if sys.platform == "darwin":
        opener = shutil.which("open")
        return [opener or "open", str(video_path)]
    if sys.platform.startswith("linux"):
        opener = shutil.which("xdg-open")
        if opener:
            return [opener, str(video_path)]
        gio = shutil.which("gio")
        if gio:
            return [gio, "open", str(video_path)]
    return None


def get_external_video_opener_label() -> str:
    if sys.platform.startswith("win"):
        return "Windows 默认视频播放器"
    if sys.platform == "darwin":
        return "macOS 默认视频播放器"
    if sys.platform.startswith("linux"):
        if shutil.which("xdg-open"):
            return "Linux xdg-open 默认视频播放器"
        if shutil.which("gio"):
            return "Linux gio 默认视频播放器"
    return "系统默认视频播放器"


def can_open_external_video() -> bool:
    if sys.platform.startswith("win"):
        return hasattr(os, "startfile")
    return get_external_video_opener_command(Path("preview.mp4")) is not None


def is_optional_python_module_available(module_name: str) -> bool:
    if not module_name:
        return True
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ValueError):
        return False


def import_optional_python_module(module_name: str):
    if not module_name:
        return None
    try:
        return importlib.import_module(module_name)
    except Exception:
        return None


def get_native_video_backend_options(bundle_dir: Path | None = None) -> list[dict]:
    candidate_root = bundle_dir or Path(".")
    optional_requirements_name = next(
        (
            file_name
            for file_name in NATIVE_VIDEO_OPTIONAL_REQUIREMENTS_CANDIDATES
            if (candidate_root / file_name).is_file()
        ),
        NATIVE_VIDEO_OPTIONAL_REQUIREMENTS_NAME,
    )
    options = []
    for option in NATIVE_VIDEO_BACKEND_OPTIONS:
        option_copy = dict(option)
        if option_copy["id"] == "system_player_bridge":
            available = can_open_external_video()
            option_copy.update(
                {
                    "available": available,
                    "status": "ready" if available else "needs_system_opener",
                    "openerLabel": get_external_video_opener_label() if available else "",
                    "installCommand": "",
                }
            )
        else:
            available = is_optional_python_module_available(str(option_copy.get("moduleName") or ""))
            option_copy.update(
                {
                    "available": available,
                    "status": "available" if available else "optional_dependency_missing",
                    "optionalRequirements": optional_requirements_name,
                    "installCommand": f"python -m pip install -r {optional_requirements_name}",
                }
            )
        options.append(option_copy)
    return options


def open_external_video(video_path: Path) -> tuple[bool, str]:
    if not video_path.is_file():
        return False, f"视频文件不存在：{video_path.name}"
    try:
        if sys.platform.startswith("win"):
            if not hasattr(os, "startfile"):
                return False, "当前 Windows Python 环境没有 os.startfile，无法唤起默认播放器。"
            os.startfile(str(video_path))  # type: ignore[attr-defined]
        else:
            command = get_external_video_opener_command(video_path)
            if not command:
                return False, "当前系统没有找到可用的默认视频打开器。"
            subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as error:
        return False, f"打开视频失败：{error}"
    return True, f"已交给{get_external_video_opener_label()}播放。"


def opencv_frame_to_pygame_surface(pygame, frame, cv2_module=None) -> tuple[object | None, str]:
    cv2 = cv2_module if cv2_module is not None else import_optional_python_module("cv2")
    try:
        if cv2 is not None and hasattr(cv2, "cvtColor") and hasattr(cv2, "COLOR_BGR2RGB"):
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width = frame.shape[:2]
        if width <= 0 or height <= 0:
            return None, "视频帧尺寸无效"
        surface = pygame.image.frombuffer(frame.tobytes(), (int(width), int(height)), "RGB").copy()
        return surface, "OpenCV 视频帧"
    except Exception as error:
        return None, f"OpenCV 视频帧转换失败：{error}"


def array_like_to_bytes(array_like) -> bytes:
    if array_like is None:
        return b""
    if isinstance(array_like, bytes):
        return array_like
    if isinstance(array_like, bytearray):
        return bytes(array_like)
    if hasattr(array_like, "tobytes"):
        return bytes(array_like.tobytes())
    return bytes(array_like)


def pyav_video_frame_to_pygame_surface(pygame, frame) -> tuple[object | None, str]:
    try:
        rgb_frame = frame.to_rgb() if hasattr(frame, "to_rgb") else frame
        array = rgb_frame.to_ndarray()
        height, width = array.shape[:2]
        if width <= 0 or height <= 0:
            return None, "PyAV 视频帧尺寸无效"
        surface = pygame.image.frombuffer(array_like_to_bytes(array), (int(width), int(height)), "RGB").copy()
        return surface, "PyAV 视频帧"
    except Exception as error:
        return None, f"PyAV 视频帧转换失败：{error}"


def load_opencv_video_frame_surface(
    pygame,
    video_path: Path,
    start_time_seconds: float = 0.0,
    cv2_module=None,
) -> tuple[object | None, str]:
    cv2 = cv2_module if cv2_module is not None else import_optional_python_module("cv2")
    if cv2 is None:
        return None, "未安装 OpenCV：使用桥接卡"
    if not video_path.is_file():
        return None, "视频文件不存在"

    capture = None
    try:
        capture = cv2.VideoCapture(str(video_path))
        if hasattr(capture, "isOpened") and not capture.isOpened():
            return None, "OpenCV 无法打开视频"
        if start_time_seconds > 0 and hasattr(cv2, "CAP_PROP_POS_MSEC") and hasattr(capture, "set"):
            capture.set(cv2.CAP_PROP_POS_MSEC, float(start_time_seconds) * 1000.0)
        ok, frame = capture.read()
        if not ok or frame is None:
            return None, "OpenCV 未读取到画面帧"
        surface, message = opencv_frame_to_pygame_surface(pygame, frame, cv2)
        return surface, "OpenCV 帧预览" if surface is not None else message
    except Exception as error:
        return None, f"OpenCV 帧预览失败：{error}"
    finally:
        if capture is not None and hasattr(capture, "release"):
            try:
                capture.release()
            except Exception:
                pass


class OpenCvEmbeddedVideoPlayback:
    backend_id = NATIVE_VIDEO_EMBEDDED_BACKEND_ID
    backend_label = "OpenCV 内嵌画面"
    audio_enabled = False
    clock_source = "video"

    def __init__(
        self,
        pygame,
        video_path: Path,
        start_time_seconds: float = 0.0,
        end_time_seconds: float = 0.0,
        fit_mode: str = "contain",
        cv2_module=None,
    ) -> None:
        self.pygame = pygame
        self.video_path = video_path
        self.start_time_seconds = max(0.0, float(start_time_seconds or 0.0))
        self.end_time_seconds = max(0.0, float(end_time_seconds or 0.0))
        self.fit_mode = fit_mode if fit_mode in {"contain", "cover"} else "contain"
        self.cv2 = cv2_module if cv2_module is not None else import_optional_python_module("cv2")
        self.capture = None
        self.current_surface = None
        self.status = "stopped"
        self.status_message = "尚未播放"
        self.frame_interval_ms = 1000.0 / 30.0
        self.next_frame_due_ms = 0
        self.started_at_ms = 0
        self.elapsed_ms = int(round(self.start_time_seconds * 1000.0))
        self.duration_ms = 0
        self.finished = False
        self.paused = False
        self.last_error = ""

    def _get_cv2_prop(self, name: str):
        return getattr(self.cv2, name, None) if self.cv2 is not None else None

    def _get_capture_float(self, prop_name: str, fallback: float = 0.0) -> float:
        prop = self._get_cv2_prop(prop_name)
        if prop is None or not self.capture or not hasattr(self.capture, "get"):
            return fallback
        try:
            value = float(self.capture.get(prop))
            if math.isfinite(value) and value > 0:
                return value
        except Exception:
            return fallback
        return fallback

    def open(self) -> tuple[bool, str]:
        if self.cv2 is None:
            self.status = "unavailable"
            self.status_message = "未安装 OpenCV，无法窗口内嵌播放"
            return False, self.status_message
        if not self.video_path.is_file():
            self.status = "file_missing"
            self.status_message = "视频文件不存在"
            return False, self.status_message
        try:
            self.capture = self.cv2.VideoCapture(str(self.video_path))
            if hasattr(self.capture, "isOpened") and not self.capture.isOpened():
                self.release()
                self.status = "open_failed"
                self.status_message = "OpenCV 无法打开视频"
                return False, self.status_message
            fps = self._get_capture_float("CAP_PROP_FPS", 30.0)
            self.frame_interval_ms = 1000.0 / max(1.0, min(120.0, fps))
            frame_count = self._get_capture_float("CAP_PROP_FRAME_COUNT", 0.0)
            if frame_count > 0 and fps > 0:
                self.duration_ms = int(round(frame_count / fps * 1000.0))
            if self.start_time_seconds > 0 and hasattr(self.cv2, "CAP_PROP_POS_MSEC") and hasattr(self.capture, "set"):
                self.capture.set(self.cv2.CAP_PROP_POS_MSEC, self.start_time_seconds * 1000.0)
            self.elapsed_ms = int(round(self.start_time_seconds * 1000.0))
            self.status = "ready"
            self.status_message = "内嵌播放就绪"
            return True, self.status_message
        except Exception as error:
            self.release()
            self.status = "open_failed"
            self.status_message = f"OpenCV 内嵌播放失败：{error}"
            self.last_error = self.status_message
            return False, self.status_message

    def play(self, now_ms: int) -> None:
        if not self.capture and self.status != "ready":
            return
        self.paused = False
        self.finished = False
        self.status = "playing"
        self.status_message = "内嵌播放中"
        self.started_at_ms = now_ms
        self.next_frame_due_ms = 0

    def pause(self) -> None:
        if self.status == "playing":
            self.paused = True
            self.status = "paused"
            self.status_message = "内嵌播放已暂停"

    def resume(self, now_ms: int) -> None:
        if self.status == "paused":
            self.paused = False
            self.status = "playing"
            self.status_message = "内嵌播放中"
            self.next_frame_due_ms = now_ms

    def toggle_pause(self, now_ms: int) -> None:
        if self.status == "playing":
            self.pause()
        elif self.status == "paused":
            self.resume(now_ms)

    def update(self, now_ms: int) -> None:
        if self.status != "playing" or self.paused or self.finished or not self.capture:
            return
        if self.next_frame_due_ms and now_ms < self.next_frame_due_ms:
            return
        if self.end_time_seconds > 0 and self.elapsed_ms >= int(round(self.end_time_seconds * 1000.0)):
            self.mark_finished()
            return
        try:
            ok, frame = self.capture.read()
        except Exception as error:
            self.last_error = f"OpenCV 读取视频帧失败：{error}"
            self.status_message = self.last_error
            self.mark_finished()
            return
        if not ok or frame is None:
            self.mark_finished()
            return
        surface, message = opencv_frame_to_pygame_surface(self.pygame, frame, self.cv2)
        if surface is None:
            self.last_error = message
            self.status_message = message
            self.mark_finished()
            return
        self.current_surface = surface
        position_ms = self._get_capture_float("CAP_PROP_POS_MSEC", 0.0)
        if position_ms > 0:
            self.elapsed_ms = int(round(position_ms))
        else:
            self.elapsed_ms += int(round(self.frame_interval_ms))
        if self.end_time_seconds > 0 and self.elapsed_ms >= int(round(self.end_time_seconds * 1000.0)):
            self.mark_finished()
            return
        self.next_frame_due_ms = int(now_ms + self.frame_interval_ms)

    def mark_finished(self) -> None:
        self.finished = True
        self.paused = False
        self.status = "finished"
        self.status_message = "内嵌播放已结束"
        self.release()

    def release(self) -> None:
        if self.capture is not None and hasattr(self.capture, "release"):
            try:
                self.capture.release()
            except Exception:
                pass
        self.capture = None

    def get_progress_ratio(self) -> float:
        if self.end_time_seconds > self.start_time_seconds:
            start_ms = self.start_time_seconds * 1000.0
            end_ms = self.end_time_seconds * 1000.0
            return clamp((self.elapsed_ms - start_ms) / max(1.0, end_ms - start_ms), 0.0, 1.0)
        if self.duration_ms > 0:
            return clamp(self.elapsed_ms / self.duration_ms, 0.0, 1.0)
        return 1.0 if self.finished else 0.0


class PyAvSynchronizedVideoPlayback:
    backend_id = NATIVE_VIDEO_SYNC_BACKEND_ID
    backend_label = "PyAV 音画同步"
    audio_enabled = True
    clock_source = "audio"

    def __init__(
        self,
        pygame,
        video_path: Path,
        start_time_seconds: float = 0.0,
        end_time_seconds: float = 0.0,
        fit_mode: str = "contain",
        volume: int = 100,
        av_module=None,
    ) -> None:
        self.pygame = pygame
        self.video_path = video_path
        self.start_time_seconds = max(0.0, float(start_time_seconds or 0.0))
        self.end_time_seconds = max(0.0, float(end_time_seconds or 0.0))
        self.fit_mode = fit_mode if fit_mode in {"contain", "cover"} else "contain"
        self.volume = clamp_int(volume, 0, 100, 100) / 100
        self.av = av_module if av_module is not None else import_optional_python_module("av")
        self.video_container = None
        self.video_stream = None
        self.video_frames = None
        self.pending_video_surface = None
        self.pending_video_time_seconds = 0.0
        self.current_surface = None
        self.audio_sound = None
        self.audio_channel = None
        self.audio_buffer_bytes = 0
        self.status = "stopped"
        self.status_message = "尚未播放"
        self.started_at_ms = 0
        self.paused_at_ms = 0
        self.total_paused_ms = 0
        self.elapsed_ms = int(round(self.start_time_seconds * 1000.0))
        self.duration_ms = 0
        self.finished = False
        self.paused = False
        self.last_error = ""

    def _open_container(self):
        if self.av is None:
            return None
        return self.av.open(str(self.video_path))

    def _stream_time_seconds(self, frame, fallback: float = 0.0) -> float:
        try:
            if getattr(frame, "pts", None) is not None and getattr(frame, "time_base", None):
                return float(frame.pts * frame.time_base)
        except Exception:
            pass
        return fallback

    def _get_streams(self, container, media_type: str) -> list:
        streams = getattr(container, "streams", None)
        if streams is None:
            return []
        typed_streams = getattr(streams, media_type, None)
        if typed_streams is not None:
            return list(typed_streams)
        try:
            return [stream for stream in streams if getattr(stream, "type", "") == media_type]
        except TypeError:
            return []

    def _seek_container(self, container) -> None:
        if self.start_time_seconds <= 0 or not hasattr(container, "seek"):
            return
        try:
            container.seek(int(self.start_time_seconds * 1_000_000), any_frame=False, backward=True)
        except TypeError:
            try:
                container.seek(int(self.start_time_seconds * 1_000_000))
            except Exception:
                return
        except Exception:
            return

    def _get_mixer_format(self) -> tuple[int, int, int]:
        mixer_state = None
        try:
            mixer_state = self.pygame.mixer.get_init()
        except Exception:
            mixer_state = None
        if not mixer_state:
            try:
                self.pygame.mixer.init(frequency=44100, size=-16, channels=2)
                mixer_state = self.pygame.mixer.get_init()
            except Exception:
                mixer_state = None
        if not mixer_state:
            return (44100, -16, 2)
        frequency, sample_format, channels = mixer_state
        return int(frequency or 44100), int(sample_format or -16), int(channels or 2)

    def _iter_resampled_audio_frames(self, frame, frequency: int, channels: int):
        layout = "stereo" if channels != 1 else "mono"
        try:
            resampler_cls = self.av.audio.resampler.AudioResampler
            resampler = getattr(self, "_audio_resampler", None)
            if resampler is None:
                resampler = resampler_cls(format="s16", layout=layout, rate=frequency)
                self._audio_resampler = resampler
            resampled = resampler.resample(frame)
            if resampled is None:
                return []
            if isinstance(resampled, list):
                return resampled
            return [resampled]
        except Exception:
            return [frame]

    def _decode_audio_buffer(self) -> tuple[bytes, str]:
        if self.av is None:
            return b"", "未安装 PyAV"
        container = None
        chunks: list[bytes] = []
        total_bytes = 0
        frequency, _sample_format, channels = self._get_mixer_format()
        try:
            container = self._open_container()
            if container is None:
                return b"", "PyAV 无法打开媒体"
            audio_streams = self._get_streams(container, "audio")
            if not audio_streams:
                return b"", "视频没有音频轨"
            audio_stream = audio_streams[0]
            self._seek_container(container)
            for frame in container.decode(audio_stream):
                frame_time = self._stream_time_seconds(frame, 0.0)
                frame_duration = 0.0
                try:
                    if getattr(frame, "sample_rate", None) and getattr(frame, "samples", None):
                        frame_duration = float(frame.samples) / float(frame.sample_rate)
                except Exception:
                    frame_duration = 0.0
                if frame_time + frame_duration < self.start_time_seconds:
                    continue
                if self.end_time_seconds > 0 and frame_time > self.end_time_seconds:
                    break
                for audio_frame in self._iter_resampled_audio_frames(frame, frequency, channels):
                    if self.end_time_seconds > 0 and self._stream_time_seconds(audio_frame, frame_time) > self.end_time_seconds:
                        break
                    audio_bytes = array_like_to_bytes(audio_frame.to_ndarray())
                    if not audio_bytes:
                        continue
                    chunks.append(audio_bytes)
                    total_bytes += len(audio_bytes)
                    if total_bytes > MAX_EMBEDDED_VIDEO_AUDIO_BUFFER_BYTES:
                        return b"".join(chunks), "音频缓冲较大，已截断到安全上限"
            payload = b"".join(chunks)
            if not payload:
                return b"", "未读取到可播放音频"
            return payload, "PyAV 音频已解码"
        except Exception as error:
            return b"", f"PyAV 音频解码失败：{error}"
        finally:
            if container is not None and hasattr(container, "close"):
                try:
                    container.close()
                except Exception:
                    pass

    def open(self) -> tuple[bool, str]:
        if self.av is None:
            self.status = "unavailable"
            self.status_message = "未安装 PyAV，无法音画同步播放"
            return False, self.status_message
        if not self.video_path.is_file():
            self.status = "file_missing"
            self.status_message = "视频文件不存在"
            return False, self.status_message
        try:
            self.video_container = self._open_container()
            if self.video_container is None:
                self.status = "open_failed"
                self.status_message = "PyAV 无法打开视频"
                return False, self.status_message
            video_streams = self._get_streams(self.video_container, "video")
            if not video_streams:
                self.status = "open_failed"
                self.status_message = "视频没有可解码画面轨"
                return False, self.status_message
            self.video_stream = video_streams[0]
            self._seek_container(self.video_container)
            self.video_frames = self.video_container.decode(self.video_stream)
            audio_bytes, audio_message = self._decode_audio_buffer()
            mixer_ready = False
            try:
                mixer_ready = bool(self.pygame.mixer.get_init())
            except Exception:
                mixer_ready = False
            if audio_bytes and mixer_ready:
                try:
                    self.audio_sound = self.pygame.mixer.Sound(buffer=audio_bytes)
                    self.audio_sound.set_volume(self.volume)
                    self.audio_buffer_bytes = len(audio_bytes)
                except Exception as error:
                    self.audio_enabled = False
                    self.clock_source = "video"
                    audio_message = f"音频缓冲创建失败：{error}"
            if not self.audio_sound:
                self.audio_enabled = False
                self.clock_source = "video"
            self.duration_ms = int(round(max(0.0, self.end_time_seconds - self.start_time_seconds) * 1000.0))
            self.status = "ready"
            self.status_message = "PyAV 音画同步就绪" if self.audio_sound else f"PyAV 画面就绪（{audio_message}）"
            return True, self.status_message
        except Exception as error:
            self.release()
            self.status = "open_failed"
            self.status_message = f"PyAV 音画同步打开失败：{error}"
            self.last_error = self.status_message
            return False, self.status_message

    def play(self, now_ms: int) -> None:
        self.paused = False
        self.finished = False
        self.status = "playing"
        self.started_at_ms = now_ms
        self.total_paused_ms = 0
        self.paused_at_ms = 0
        self.elapsed_ms = int(round(self.start_time_seconds * 1000.0))
        if self.audio_sound:
            try:
                self.audio_channel = self.audio_sound.play()
            except Exception:
                self.audio_channel = None
                self.audio_enabled = False
                self.clock_source = "video"
        self.status_message = "PyAV 音画同步播放中" if self.audio_channel else "PyAV 画面播放中（音频不可用）"

    def pause(self) -> None:
        if self.status == "playing":
            self.paused = True
            self.status = "paused"
            self.paused_at_ms = self.pygame.time.get_ticks()
            if self.audio_channel:
                try:
                    self.audio_channel.pause()
                except Exception:
                    pass
            self.status_message = "PyAV 播放已暂停"

    def resume(self, now_ms: int) -> None:
        if self.status == "paused":
            if self.paused_at_ms:
                self.total_paused_ms += max(0, now_ms - self.paused_at_ms)
            self.paused_at_ms = 0
            self.paused = False
            self.status = "playing"
            if self.audio_channel:
                try:
                    self.audio_channel.unpause()
                except Exception:
                    pass
            self.status_message = "PyAV 音画同步播放中" if self.audio_channel else "PyAV 画面播放中（音频不可用）"

    def toggle_pause(self, now_ms: int) -> None:
        if self.status == "playing":
            self.pause()
        elif self.status == "paused":
            self.resume(now_ms)

    def get_playback_seconds(self, now_ms: int) -> float:
        if self.status == "paused" and self.paused_at_ms:
            now_ms = self.paused_at_ms
        elapsed = max(0, now_ms - self.started_at_ms - self.total_paused_ms)
        self.elapsed_ms = int(round(self.start_time_seconds * 1000.0 + elapsed))
        return self.elapsed_ms / 1000.0

    def _next_video_surface(self):
        if self.video_frames is None:
            return None, None, "视频迭代器不存在"
        try:
            frame = next(self.video_frames)
        except StopIteration:
            return None, None, "视频播放到结尾"
        except Exception as error:
            return None, None, f"PyAV 视频解码失败：{error}"
        frame_time = self._stream_time_seconds(frame, self.start_time_seconds)
        surface, message = pyav_video_frame_to_pygame_surface(self.pygame, frame)
        return surface, frame_time, message

    def update(self, now_ms: int) -> None:
        if self.status != "playing" or self.paused or self.finished:
            return
        playback_seconds = self.get_playback_seconds(now_ms)
        if self.end_time_seconds > 0 and playback_seconds >= self.end_time_seconds:
            self.mark_finished()
            return

        while True:
            if self.pending_video_surface is not None:
                if self.pending_video_time_seconds <= playback_seconds + 0.012:
                    self.current_surface = self.pending_video_surface
                    self.pending_video_surface = None
                    continue
                break

            surface, frame_time, message = self._next_video_surface()
            if surface is None:
                self.last_error = "" if message == "视频播放到结尾" else str(message or "")
                self.mark_finished()
                break
            if frame_time is None:
                frame_time = playback_seconds
            if frame_time < self.start_time_seconds - 0.04:
                continue
            if self.end_time_seconds > 0 and frame_time > self.end_time_seconds:
                self.mark_finished()
                break
            if frame_time <= playback_seconds + 0.012:
                self.current_surface = surface
                continue
            self.pending_video_surface = surface
            self.pending_video_time_seconds = frame_time
            break

        if self.audio_channel and not self.audio_channel.get_busy() and self.status == "playing":
            if self.end_time_seconds <= 0 or playback_seconds >= self.start_time_seconds + 0.25:
                self.mark_finished()

    def mark_finished(self) -> None:
        self.finished = True
        self.paused = False
        self.status = "finished"
        self.status_message = "PyAV 音画同步播放已结束"
        self.release(stop_audio=True)

    def release(self, stop_audio: bool = True) -> None:
        if stop_audio and self.audio_channel:
            try:
                self.audio_channel.stop()
            except Exception:
                pass
        self.audio_channel = None
        self.audio_sound = None
        if self.video_container is not None and hasattr(self.video_container, "close"):
            try:
                self.video_container.close()
            except Exception:
                pass
        self.video_container = None
        self.video_frames = None

    def get_progress_ratio(self) -> float:
        if self.end_time_seconds > self.start_time_seconds:
            start_ms = self.start_time_seconds * 1000.0
            end_ms = self.end_time_seconds * 1000.0
            return clamp((self.elapsed_ms - start_ms) / max(1.0, end_ms - start_ms), 0.0, 1.0)
        if self.duration_ms > 0:
            return clamp(self.elapsed_ms / self.duration_ms, 0.0, 1.0)
        return 1.0 if self.finished else 0.0


def validate_bundle(bundle_dir: Path) -> None:
    data_path = bundle_dir / DEFAULT_GAME_DATA_NAME
    payload = load_game_data(data_path)
    required_keys = {"project", "assets", "characters", "variables", "chapters"}
    missing_keys = sorted(required_keys - set(payload))
    if missing_keys:
        raise NativeRuntimeError(f"游戏数据缺少这些字段：{', '.join(missing_keys)}")

    chapters = payload.get("chapters") or []
    if not isinstance(chapters, list) or not chapters:
        raise NativeRuntimeError("游戏数据里没有任何章节。")

    assets = (payload.get("assets") or {}).get("assets") or []
    for asset in assets:
        export_url = str(asset.get("exportUrl") or "").strip()
        if not export_url or asset.get("isMissing"):
            continue
        if not (bundle_dir / export_url).is_file():
            raise NativeRuntimeError(f"导出资源不存在：{export_url}")


def get_bundle_relative_path(bundle_dir: Path, path: Path) -> str:
    return path.relative_to(bundle_dir).as_posix()


def should_include_file_integrity_entry(bundle_dir: Path, path: Path) -> bool:
    if not path.is_file():
        return False
    relative = get_bundle_relative_path(bundle_dir, path)
    parts = Path(relative).parts
    if any(part in FILE_INTEGRITY_EXCLUDED_PREFIXES for part in parts):
        return False
    file_name = path.name
    if file_name in FILE_INTEGRITY_EXCLUDED_FILE_NAMES:
        return False
    if any(file_name.startswith(prefix) for prefix in FILE_INTEGRITY_VOLATILE_REPORT_PREFIXES):
        return False
    if file_name == ".DS_Store" or file_name.endswith((".pyc", ".pyo")):
        return False
    return True


def iter_file_integrity_paths(bundle_dir: Path) -> list[Path]:
    if not bundle_dir.is_dir():
        raise NativeRuntimeError(f"导出包目录不存在：{bundle_dir}")
    paths: list[Path] = []
    for root, dir_names, file_names in os.walk(bundle_dir):
        dir_names[:] = [
            name
            for name in dir_names
            if name not in FILE_INTEGRITY_EXCLUDED_PREFIXES
        ]
        root_path = Path(root)
        for file_name in file_names:
            path = root_path / file_name
            if should_include_file_integrity_entry(bundle_dir, path):
                paths.append(path)
    return sorted(paths, key=lambda item: get_bundle_relative_path(bundle_dir, item))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def format_file_size_label(size_bytes: int) -> str:
    size = float(max(0, size_bytes))
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size_bytes} B"


def build_native_runtime_file_integrity_report(bundle_dir: Path) -> dict:
    files = []
    total_bytes = 0
    for path in iter_file_integrity_paths(bundle_dir):
        relative_path = get_bundle_relative_path(bundle_dir, path)
        size_bytes = path.stat().st_size
        total_bytes += size_bytes
        files.append(
            {
                "path": relative_path,
                "sizeBytes": size_bytes,
                "sizeLabel": format_file_size_label(size_bytes),
                "sha256": sha256_file(path),
            }
        )
    largest_files = sorted(files, key=lambda item: int(item.get("sizeBytes") or 0), reverse=True)[:10]
    return {
        "formatVersion": 1,
        "algorithm": "sha256",
        "generatedAt": now_iso(),
        "bundleDir": str(bundle_dir),
        "scope": "导出包核心文件；不包含可重新生成的诊断报告、完整性报告、缓存和本机 App 构建输出。",
        "summary": {
            "fileCount": len(files),
            "totalBytes": total_bytes,
            "totalSizeLabel": format_file_size_label(total_bytes),
            "largestFiles": largest_files,
        },
        "files": files,
    }


def render_native_runtime_file_integrity_markdown(report: dict) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    files = report.get("files") if isinstance(report.get("files"), list) else []
    largest_files = summary.get("largestFiles") if isinstance(summary.get("largestFiles"), list) else []
    lines = [
        "# 原生 Runtime 文件完整性报告",
        "",
        f"- 生成时间：{format_markdown_value(report.get('generatedAt'))}",
        f"- 算法：{format_markdown_value(report.get('algorithm'), 'sha256')}",
        f"- 范围：{format_markdown_value(report.get('scope'))}",
        "",
        "## 总览",
        "",
        "| 指标 | 值 |",
        "| --- | --- |",
        f"| 文件数 | {int(summary.get('fileCount') or 0)} |",
        f"| 总大小 | {format_markdown_value(summary.get('totalSizeLabel'), '0 B')} |",
        "",
    ]
    if largest_files:
        lines.extend(["## 最大文件", "", "| 文件 | 大小 |", "| --- | ---: |"])
        for item in largest_files:
            if isinstance(item, dict):
                lines.append(
                    f"| `{format_markdown_value(item.get('path'))}` | {format_markdown_value(item.get('sizeLabel'), '0 B')} |"
                )
        lines.append("")
    lines.extend(["## 校验命令", "", "```bash", "python3 runtime_player.py --verify-file-integrity .", "```", ""])
    lines.extend(["## 文件指纹", "", "| 文件 | 大小 | SHA-256 |", "| --- | ---: | --- |"])
    for item in files:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"| `{format_markdown_value(item.get('path'))}` | "
            f"{format_markdown_value(item.get('sizeLabel'), '0 B')} | "
            f"`{format_markdown_value(item.get('sha256'))}` |"
        )
    lines.append("")
    return "\n".join(lines)


def write_native_runtime_file_integrity_reports(bundle_dir: Path) -> dict:
    report = build_native_runtime_file_integrity_report(bundle_dir)
    (bundle_dir / FILE_INTEGRITY_REPORT_NAME).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / FILE_INTEGRITY_MARKDOWN_NAME).write_text(
        render_native_runtime_file_integrity_markdown(report),
        encoding="utf-8",
    )
    return report


def load_native_runtime_file_integrity_report(bundle_dir: Path) -> dict:
    report_path = bundle_dir / FILE_INTEGRITY_REPORT_NAME
    if not report_path.is_file():
        raise NativeRuntimeError(f"缺少文件完整性报告：{FILE_INTEGRITY_REPORT_NAME}")
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise NativeRuntimeError(f"文件完整性报告不是有效 JSON：{error}") from error
    if not isinstance(report, dict) or not isinstance(report.get("files"), list):
        raise NativeRuntimeError("文件完整性报告格式不正确。")
    return report


def build_native_runtime_file_integrity_verification(bundle_dir: Path) -> dict:
    expected_report = load_native_runtime_file_integrity_report(bundle_dir)
    expected_files = {
        str(item.get("path") or ""): item
        for item in expected_report.get("files") or []
        if isinstance(item, dict) and str(item.get("path") or "").strip()
    }
    current_report = build_native_runtime_file_integrity_report(bundle_dir)
    current_files = {
        str(item.get("path") or ""): item
        for item in current_report.get("files") or []
        if isinstance(item, dict) and str(item.get("path") or "").strip()
    }
    missing_files = []
    changed_files = []
    for path, expected in expected_files.items():
        current = current_files.get(path)
        if not current:
            missing_files.append({"path": path, "expectedSha256": expected.get("sha256")})
            continue
        if current.get("sha256") != expected.get("sha256") or current.get("sizeBytes") != expected.get("sizeBytes"):
            changed_files.append(
                {
                    "path": path,
                    "expectedSizeBytes": expected.get("sizeBytes"),
                    "actualSizeBytes": current.get("sizeBytes"),
                    "expectedSha256": expected.get("sha256"),
                    "actualSha256": current.get("sha256"),
                }
            )
    extra_files = [
        current_files[path]
        for path in sorted(set(current_files) - set(expected_files))
    ]
    status = "fail" if missing_files or changed_files else ("warn" if extra_files else "pass")
    return {
        "status": status,
        "checkedAt": now_iso(),
        "bundleDir": str(bundle_dir),
        "algorithm": expected_report.get("algorithm") or "sha256",
        "summary": {
            "expectedFileCount": len(expected_files),
            "currentFileCount": len(current_files),
            "missingCount": len(missing_files),
            "changedCount": len(changed_files),
            "extraCount": len(extra_files),
        },
        "missingFiles": missing_files[:50],
        "changedFiles": changed_files[:50],
        "extraFiles": extra_files[:50],
    }


def print_native_runtime_file_integrity_report(bundle_dir: Path) -> dict:
    report = build_native_runtime_file_integrity_report(bundle_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def print_native_runtime_file_integrity_markdown_report(bundle_dir: Path) -> dict:
    report = build_native_runtime_file_integrity_report(bundle_dir)
    print(render_native_runtime_file_integrity_markdown(report), end="")
    return report


def print_native_runtime_file_integrity_verification(bundle_dir: Path) -> dict:
    report = build_native_runtime_file_integrity_verification(bundle_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def add_release_check_issue(
    issues: list[dict],
    severity: str,
    code: str,
    message: str,
    suggestion: str = "",
    path: str = "",
) -> None:
    issues.append(
        {
            "severity": severity,
            "code": code,
            "message": message,
            "suggestion": suggestion,
            "path": path,
        }
    )


def get_release_check_status(issues: list[dict]) -> str:
    if any(issue.get("severity") == "error" for issue in issues):
        return "fail"
    if any(issue.get("severity") == "warning" for issue in issues):
        return "warn"
    return "pass"


def normalize_variable_type(value: object) -> str:
    variable_type = str(value or "string").strip().lower() or "string"
    return variable_type if variable_type in VARIABLE_TYPES else "string"


def is_number_variable_value(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def variable_value_matches_type(variable_type: str, value: object) -> bool:
    safe_type = normalize_variable_type(variable_type)
    if safe_type == "number":
        return is_number_variable_value(value)
    if safe_type == "boolean":
        return isinstance(value, bool)
    return isinstance(value, str)


def parse_variable_number_bound(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def get_variable_number_bounds(variable: dict | None) -> tuple[float | None, float | None]:
    if not isinstance(variable, dict):
        return None, None
    min_value = parse_variable_number_bound(variable.get("min", variable.get("minValue")))
    max_value = parse_variable_number_bound(variable.get("max", variable.get("maxValue")))
    return min_value, max_value


def clamp_runtime_variable_number(variable: dict | None, value: float) -> float | int:
    min_value, max_value = get_variable_number_bounds(variable)
    next_value = value
    if min_value is not None:
        next_value = max(next_value, min_value)
    if max_value is not None:
        next_value = min(next_value, max_value)
    return int(next_value) if int(next_value) == next_value else next_value


def coerce_runtime_variable_value(variable: dict | None, value: object) -> object:
    variable_type = normalize_variable_type((variable or {}).get("type"))
    fallback = (variable or {}).get("defaultValue")
    if variable_type == "number":
        if isinstance(value, bool):
            fallback_value = fallback if is_number_variable_value(fallback) else 0
            return clamp_runtime_variable_number(variable, float(fallback_value))
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            fallback_value = fallback if is_number_variable_value(fallback) else 0
            return clamp_runtime_variable_number(variable, float(fallback_value))
        if not math.isfinite(numeric_value):
            fallback_value = fallback if is_number_variable_value(fallback) else 0
            return clamp_runtime_variable_number(variable, float(fallback_value))
        return clamp_runtime_variable_number(variable, numeric_value)
    if variable_type == "boolean":
        if isinstance(value, bool):
            return value
        clean_value = str(value).strip().lower()
        if clean_value in {"true", "1", "yes", "on"}:
            return True
        if clean_value in {"false", "0", "no", "off"}:
            return False
        return fallback if isinstance(fallback, bool) else False
    if value is None:
        return fallback if isinstance(fallback, str) else ""
    return value if isinstance(value, str) else str(value)


def condition_operator_matches_variable_type(variable_type: str, operator: object) -> bool:
    safe_operator = str(operator or "==").strip() or "=="
    if safe_operator in EQUALITY_CONDITION_OPERATORS:
        return True
    if safe_operator in NUMERIC_CONDITION_OPERATORS:
        return normalize_variable_type(variable_type) == "number"
    return False


def get_export_variable_map(payload: dict) -> tuple[list[dict], dict[str, dict], set[str]]:
    variables_doc = payload.get("variables") if isinstance(payload.get("variables"), dict) else {}
    variables = variables_doc.get("variables") if isinstance(variables_doc.get("variables"), list) else []
    variables_by_id: dict[str, dict] = {}
    duplicate_ids: set[str] = set()
    for variable in variables:
        if not isinstance(variable, dict):
            continue
        variable_id = str(variable.get("id") or "").strip()
        if not variable_id:
            continue
        if variable_id in variables_by_id:
            duplicate_ids.add(variable_id)
            continue
        variables_by_id[variable_id] = variable
    return variables, variables_by_id, duplicate_ids


def get_export_logic_issue_count(issues: list[dict]) -> int:
    logic_codes = {
        "logic_target_missing",
        "logic_variable_missing",
        "logic_variable_type_mismatch",
        "logic_variable_default_type_mismatch",
        "logic_variable_range_invalid",
        "logic_variable_default_out_of_range",
        "logic_condition_operator_mismatch",
        "logic_choice_effect_unknown",
        "logic_variable_duplicate_id",
    }
    return sum(1 for issue in issues if issue.get("code") in logic_codes)


def build_release_check_report(bundle_dir: Path) -> dict:
    issues: list[dict] = []
    data_path = bundle_dir / DEFAULT_GAME_DATA_NAME
    payload: dict | None = None
    try:
        payload = load_game_data(data_path)
    except Exception as error:
        add_release_check_issue(
            issues,
            "error",
            "game_data_missing_or_invalid",
            f"无法读取 {DEFAULT_GAME_DATA_NAME}：{error}",
            "重新导出原生 Runtime 包，确认 game_data.json 没有被移动或手动改坏。",
            DEFAULT_GAME_DATA_NAME,
        )
        return {
            "status": get_release_check_status(issues),
            "checkedAt": now_iso(),
            "bundleDir": str(bundle_dir),
            "projectTitle": "",
            "summary": {"errors": 1, "warnings": 0, "assetCount": 0, "sceneCount": 0},
            "issues": issues,
        }

    try:
        validate_bundle(bundle_dir)
    except NativeRuntimeError as error:
        add_release_check_issue(
            issues,
            "error",
            "bundle_validation_failed",
            str(error),
            "先修复导出包结构或缺失素材，再继续打包 App。",
            DEFAULT_GAME_DATA_NAME,
        )

    project = payload.get("project") if isinstance(payload.get("project"), dict) else {}
    project_title = str(project.get("title") or project.get("name") or "未命名项目")
    chapters = payload.get("chapters") if isinstance(payload.get("chapters"), list) else []
    scenes = iter_export_scenes(chapters)
    scene_ids = {str(scene.get("id") or "") for scene in scenes if scene.get("id")}
    entry_scene_id = str(project.get("entrySceneId") or "").strip()
    if not scenes:
        add_release_check_issue(
            issues,
            "error",
            "no_scene",
            "项目里没有可播放场景。",
            "至少创建一个章节和一个场景，并设置入口场景。",
        )
    elif entry_scene_id and entry_scene_id not in scene_ids:
        add_release_check_issue(
            issues,
            "error",
            "entry_scene_missing",
            f"入口场景不存在：{entry_scene_id}",
            "在项目设置里重新选择一个仍然存在的入口场景。",
        )
    elif not entry_scene_id:
        add_release_check_issue(
            issues,
            "warning",
            "entry_scene_auto_fallback",
            "项目没有显式入口场景，Runtime 会自动使用第一个场景。",
            "正式发布前建议设置入口场景，避免章节排序变化后进入错误位置。",
        )

    dialogue_like_count = sum(
        1
        for scene in scenes
        for block in scene.get("blocks", []) or []
        if str(block.get("type") or "") in {"dialogue", "narration", "choice"}
    )
    if scenes and dialogue_like_count == 0:
        add_release_check_issue(
            issues,
            "warning",
            "no_dialogue_or_choice",
            "当前导出包没有检测到台词、旁白或选项块。",
            "如果这不是纯演出测试包，建议补一段可读剧情再发布。",
        )

    long_text_warnings = []
    for scene in scenes:
        scene_name = str(scene.get("name") or scene.get("id") or "未命名场景")
        for block_index, block in enumerate(scene.get("blocks", []) or []):
            block_type = str(block.get("type") or "")
            if block_type not in {"dialogue", "narration"}:
                continue
            text = str(block.get("text") or "")
            if len(text) > VN_TEXT_LONG_WARNING_LENGTH or text.count("\n") >= VN_TEXT_LONG_WARNING_LINES:
                long_text_warnings.append((scene_name, block_index, len(text), text.count("\n") + 1))
    for scene_name, block_index, text_length, line_count in long_text_warnings[:5]:
        add_release_check_issue(
            issues,
            "warning",
            "long_dialogue_text",
            f"长文本可能影响阅读节奏：{scene_name} 第 {block_index + 1} 张卡（{text_length} 字 / {line_count} 行）",
            "原生 Runtime 会尽量动态增高文本框并提示查看历史；正式发布前建议拆成多张台词卡，阅读节奏会更像商业 VN。",
            f"{scene_name}#{block_index + 1}",
        )

    choice_text_warnings = []
    for scene in scenes:
        scene_name = str(scene.get("name") or scene.get("id") or "未命名场景")
        for block_index, block in enumerate(scene.get("blocks", []) or []):
            if str(block.get("type") or "") != "choice":
                continue
            options = block.get("options") if isinstance(block.get("options"), list) else []
            if len(options) > VN_CHOICE_MANY_OPTIONS:
                choice_text_warnings.append(
                    (
                        "many_choice_options",
                        f"选项数量偏多：{scene_name} 第 {block_index + 1} 张卡（{len(options)} 个选项）",
                        "选项过多会让原生 Runtime 的按钮区变拥挤；建议拆成二级选择，或确认目标分辨率下逐项点测。",
                        f"{scene_name}#{block_index + 1}",
                    )
                )
            for option_index, option in enumerate(options):
                option_text = str(option.get("text") or "")
                if len(option_text) > VN_CHOICE_LONG_WARNING_LENGTH:
                    choice_text_warnings.append(
                        (
                            "long_choice_text",
                            f"选项文案偏长：{scene_name} 第 {block_index + 1} 张卡 / 选项 {option_index + 1}（{len(option_text)} 字）",
                            "长选项会在按钮里被截断；建议改成更短的决策文字，把解释放到前一句旁白或台词里。",
                            f"{scene_name}#{block_index + 1}/option-{option_index + 1}",
                        )
                    )
    for code, message, suggestion, path in choice_text_warnings[:5]:
        add_release_check_issue(issues, "warning", code, message, suggestion, path)

    variables, variables_by_id, duplicate_variable_ids = get_export_variable_map(payload)
    for variable_id in sorted(duplicate_variable_ids):
        add_release_check_issue(
            issues,
            "error",
            "logic_variable_duplicate_id",
            f"变量 ID 重复：{variable_id}",
            "回到编辑器变量库合并或重命名重复变量，避免运行时读到不可预测的值。",
            f"variables.{variable_id}",
        )
    for variable in variables:
        if not isinstance(variable, dict):
            continue
        variable_id = str(variable.get("id") or "").strip()
        if not variable_id:
            continue
        variable_type = normalize_variable_type(variable.get("type"))
        if not variable_value_matches_type(variable_type, variable.get("defaultValue")):
            add_release_check_issue(
                issues,
                "error",
                "logic_variable_default_type_mismatch",
                f"变量默认值类型不匹配：{variable.get('name') or variable_id}",
                "回到变量库把默认值改成对应类型；数字变量用数字，开关变量用 true/false，文本变量用字符串。",
                f"variables.{variable_id}.defaultValue",
            )
        if variable_type == "number":
            raw_min = variable.get("min", variable.get("minValue"))
            raw_max = variable.get("max", variable.get("maxValue"))
            min_value, max_value = get_variable_number_bounds(variable)
            if raw_min is not None and min_value is None:
                add_release_check_issue(
                    issues,
                    "error",
                    "logic_variable_range_invalid",
                    f"数字变量最小值不是有效数字：{variable.get('name') or variable_id}",
                    "把变量范围改成有效数字，或清空最小值。",
                    f"variables.{variable_id}.min",
                )
            if raw_max is not None and max_value is None:
                add_release_check_issue(
                    issues,
                    "error",
                    "logic_variable_range_invalid",
                    f"数字变量最大值不是有效数字：{variable.get('name') or variable_id}",
                    "把变量范围改成有效数字，或清空最大值。",
                    f"variables.{variable_id}.max",
                )
            if min_value is not None and max_value is not None and min_value > max_value:
                add_release_check_issue(
                    issues,
                    "error",
                    "logic_variable_range_invalid",
                    f"数字变量范围上下限反了：{variable.get('name') or variable_id}",
                    "确认最小值小于等于最大值；否则 Runtime 无法判断该把数值夹到哪里。",
                    f"variables.{variable_id}.min/max",
                )
            range_order_is_valid = not (min_value is not None and max_value is not None and min_value > max_value)
            if (
                range_order_is_valid
                and variable_value_matches_type(variable_type, variable.get("defaultValue"))
                and (
                    (min_value is not None and float(variable.get("defaultValue")) < min_value)
                    or (max_value is not None and float(variable.get("defaultValue")) > max_value)
                )
            ):
                add_release_check_issue(
                    issues,
                    "warning",
                    "logic_variable_default_out_of_range",
                    f"数字变量默认值超出范围：{variable.get('name') or variable_id}",
                    "原生 Runtime 会自动夹回范围内；正式发布前建议把默认值直接改到范围内，避免作者和玩家看到的初始状态不一致。",
                    f"variables.{variable_id}.defaultValue",
                )

    def variable_name(variable_id: str) -> str:
        variable = variables_by_id.get(variable_id)
        return str(variable.get("name") or variable_id) if variable else variable_id

    def check_scene_target(scene_id: object, label: str, path: str) -> None:
        target_scene_id = str(scene_id or "").strip()
        if target_scene_id and target_scene_id in scene_ids:
            return
        add_release_check_issue(
            issues,
            "error",
            "logic_target_missing",
            f"{label}不存在：{target_scene_id or '未设置'}",
            "回到剧情编辑器重新选择一个仍然存在的目标场景，否则原生 Runtime 路线会中断或落到空目标。",
            path,
        )

    def check_variable_reference(
        variable_id: object,
        *,
        path: str,
        usage_label: str,
        expected_type: str | None = None,
        value: object = None,
        validate_value: bool = False,
        operator: object = None,
    ) -> None:
        safe_variable_id = str(variable_id or "").strip()
        variable = variables_by_id.get(safe_variable_id)
        if not safe_variable_id or not variable:
            add_release_check_issue(
                issues,
                "error",
                "logic_variable_missing",
                f"{usage_label}引用了不存在的变量：{safe_variable_id or '未设置'}",
                "回到剧情卡片重新选择变量，或先在变量库里创建这个变量。",
                path,
            )
            return

        variable_type = normalize_variable_type(variable.get("type"))
        if expected_type and variable_type != expected_type:
            add_release_check_issue(
                issues,
                "error",
                "logic_variable_type_mismatch",
                f"{usage_label}需要{expected_type}变量，但当前引用的是 {variable_name(safe_variable_id)} ({variable_type})",
                "把这张逻辑卡片改绑到正确类型的变量，或调整变量库里的变量类型。",
                path,
            )
        should_validate_value = validate_value and (not expected_type or variable_type == expected_type)
        if should_validate_value and not variable_value_matches_type(variable_type, value):
            add_release_check_issue(
                issues,
                "error",
                "logic_variable_type_mismatch",
                f"{usage_label}的值类型和变量不匹配：{variable_name(safe_variable_id)}",
                "重新保存这张逻辑卡片，让编辑器按变量类型写入数字、开关或文本值。",
                path,
            )
        if operator is not None and not condition_operator_matches_variable_type(variable_type, operator):
            add_release_check_issue(
                issues,
                "error",
                "logic_condition_operator_mismatch",
                f"条件判断的比较方式和变量类型不匹配：{variable_name(safe_variable_id)} {operator}",
                "文本和开关变量只适合等于/不等于；大于、小于这类比较请改用数字变量。",
                path,
            )

    for scene in scenes:
        scene_name = str(scene.get("name") or scene.get("id") or "未命名场景")
        for block_index, block in enumerate(scene.get("blocks", []) or []):
            if not isinstance(block, dict):
                continue
            block_type = str(block.get("type") or "")
            block_path = f"{scene_name}#{block_index + 1}"
            if block_type == "jump":
                check_scene_target(block.get("targetSceneId"), "跳转目标场景", block_path)
            elif block_type == "variable_set":
                check_variable_reference(
                    block.get("variableId"),
                    path=block_path,
                    usage_label="变量设置卡片",
                    value=block.get("value"),
                    validate_value=True,
                )
            elif block_type == "variable_add":
                check_variable_reference(
                    block.get("variableId"),
                    path=block_path,
                    usage_label="数字变量加减卡片",
                    expected_type="number",
                    value=block.get("value"),
                    validate_value=True,
                )
            elif block_type == "choice":
                options = block.get("options") if isinstance(block.get("options"), list) else []
                for option_index, option in enumerate(options):
                    if not isinstance(option, dict):
                        continue
                    option_path = f"{block_path}/option-{option_index + 1}"
                    check_scene_target(option.get("gotoSceneId"), "选项目标场景", option_path)
                    for effect_index, effect in enumerate(option.get("effects", []) or []):
                        if not isinstance(effect, dict):
                            continue
                        effect_path = f"{option_path}/effect-{effect_index + 1}"
                        effect_type = str(effect.get("type") or "")
                        if effect_type == "variable_add":
                            check_variable_reference(
                                effect.get("variableId"),
                                path=effect_path,
                                usage_label="选项数字变化效果",
                                expected_type="number",
                                value=effect.get("value"),
                                validate_value=True,
                            )
                        elif effect_type == "variable_set":
                            check_variable_reference(
                                effect.get("variableId"),
                                path=effect_path,
                                usage_label="选项变量设置效果",
                                value=effect.get("value"),
                                validate_value=True,
                            )
                        else:
                            add_release_check_issue(
                                issues,
                                "warning",
                                "logic_choice_effect_unknown",
                                f"选项效果类型暂未识别：{effect_type or '未设置'}",
                                "如果这是旧版本或手动编辑的数据，建议在编辑器里重新保存这个选项效果。",
                                effect_path,
                            )
            elif block_type == "condition":
                branches = block.get("branches") if isinstance(block.get("branches"), list) else []
                for branch_index, branch in enumerate(branches):
                    if not isinstance(branch, dict):
                        continue
                    branch_path = f"{block_path}/branch-{branch_index + 1}"
                    check_scene_target(branch.get("gotoSceneId"), "条件分支目标场景", branch_path)
                    rules = branch.get("when") if isinstance(branch.get("when"), list) else []
                    for rule_index, rule in enumerate(rules):
                        if not isinstance(rule, dict):
                            continue
                        rule_path = f"{branch_path}/rule-{rule_index + 1}"
                        check_variable_reference(
                            rule.get("variableId"),
                            path=rule_path,
                            usage_label="条件判断规则",
                            value=rule.get("value"),
                            validate_value=True,
                            operator=rule.get("operator"),
                        )
                check_scene_target(block.get("elseGotoSceneId"), "条件未命中目标场景", f"{block_path}/else")

    formal_slot_count = get_project_formal_save_slot_count(project)
    if formal_slot_count > 80:
        add_release_check_issue(
            issues,
            "warning",
            "many_save_slots",
            f"项目设置了 {formal_slot_count} 个正式存档位。",
            "大体量游戏可以保留；短篇游戏建议减少存档位，让读档界面更清爽。",
        )

    assets_doc = payload.get("assets") if isinstance(payload.get("assets"), dict) else {}
    assets = assets_doc.get("assets") if isinstance(assets_doc.get("assets"), list) else []
    assets_by_id = {str(asset.get("id")): asset for asset in assets if isinstance(asset, dict) and asset.get("id")}
    characters_doc = payload.get("characters") if isinstance(payload.get("characters"), dict) else {}
    characters = characters_doc.get("characters") if isinstance(characters_doc.get("characters"), list) else []
    game_ui_config = project.get("gameUiConfig") if isinstance(project.get("gameUiConfig"), dict) else {}

    for scene in scenes:
        scene_name = str(scene.get("name") or scene.get("id") or "未命名场景")
        for block_index, block in enumerate(scene.get("blocks", []) or []):
            if not isinstance(block, dict) or str(block.get("type") or "").strip() != "background":
                continue
            asset_id = str(block.get("assetId") or "").strip()
            block_path = f"{scene_name}#{block_index + 1}/background"
            if not asset_id:
                continue
            asset = assets_by_id.get(asset_id)
            if not asset:
                add_release_check_issue(
                    issues,
                    "error",
                    "background_asset_missing",
                    f"背景卡片引用了不存在的素材：{asset_id}",
                    "回到剧情编辑器重新选择仍然存在的背景、CG 或 3D 场景。",
                    block_path,
                )
                continue
            asset_type = str(asset.get("type") or "")
            if asset_type not in {"background", "cg", "scene3d"}:
                add_release_check_issue(
                    issues,
                    "warning",
                    "background_asset_type_risk",
                    f"背景卡片绑定的不是背景/CG/3D 场景：{asset.get('name') or asset_id}",
                    f"当前素材类型是 {asset_type or '未知'}；建议改用 background、cg 或 scene3d。",
                    block_path,
                )
            if asset_type == "scene3d":
                raw_config = block.get("scene3dPreview") if isinstance(block.get("scene3dPreview"), dict) else {}
                safe_config = normalize_scene3d_preview_config(raw_config)
                raw_tuple = (
                    raw_config.get("yaw"),
                    raw_config.get("pitch"),
                    raw_config.get("zoom"),
                    raw_config.get("interactionEnabled", True),
                )
                safe_tuple = (
                    safe_config["yaw"],
                    safe_config["pitch"],
                    safe_config["zoom"],
                    safe_config["interactionEnabled"],
                )
                try:
                    raw_numbers = (float(raw_tuple[0]), float(raw_tuple[1]), float(raw_tuple[2]), raw_tuple[3] is not False)
                except (TypeError, ValueError):
                    raw_numbers = None
                if raw_config and raw_numbers != safe_tuple:
                    add_release_check_issue(
                        issues,
                        "warning",
                        "scene3d_preview_config_clamped",
                        f"3D 场景默认视角参数需要修正：{asset.get('name') or asset_id}",
                        "Runtime 会自动夹到安全范围内；建议在背景卡里重新保存 yaw、pitch、zoom 和交互开关。",
                        block_path,
                    )

    def check_character_asset_reference(
        asset_id: str,
        *,
        label: str,
        path: str,
        expected_types: set[str],
        missing_severity: str = "warning",
    ) -> dict | None:
        clean_asset_id = str(asset_id or "").strip()
        if not clean_asset_id:
            add_release_check_issue(
                issues,
                missing_severity,
                "character_presentation_asset_unbound",
                f"{label}还没有绑定素材。",
                "如果这是高级角色表现，建议至少绑定模型入口和兜底立绘；否则 Runtime 会回退到占位显示。",
                path,
            )
            return None

        asset = assets_by_id.get(clean_asset_id)
        if not asset:
            add_release_check_issue(
                issues,
                "error",
                "character_presentation_asset_missing",
                f"{label}引用了不存在的素材：{clean_asset_id}",
                "回到角色页重新选择仍然存在的素材，或先在素材库导入该模型 / 兜底立绘。",
                path,
            )
            return None

        asset_type = str(asset.get("type") or "")
        if expected_types and asset_type not in expected_types:
            add_release_check_issue(
                issues,
                "warning",
                "character_presentation_asset_type_mismatch",
                f"{label}素材类型不匹配：{asset.get('name') or clean_asset_id}",
                f"当前类型是 {asset_type or '未知'}，建议改用 {', '.join(sorted(expected_types))} 类型素材。",
                path,
            )

        export_url = str(asset.get("exportUrl") or "").strip()
        if asset.get("isMissing") or not export_url or not (bundle_dir / export_url).is_file():
            add_release_check_issue(
                issues,
                "warning",
                "character_presentation_asset_file_missing",
                f"{label}素材文件不可用：{asset.get('name') or clean_asset_id}",
                "重新导入或替换这个素材后再导出；否则高级角色表现会在 Runtime 里回退到占位或兜底立绘。",
                export_url or path,
            )
        return asset

    for field_name, label in GAME_UI_ASSET_REFERENCE_LABELS.items():
        asset_id = str(game_ui_config.get(field_name) or "").strip()
        if not asset_id:
            continue
        asset = assets_by_id.get(asset_id)
        check_path = f"gameUiConfig.{field_name}"
        if not asset:
            add_release_check_issue(
                issues,
                "warning",
                "game_ui_asset_reference_missing",
                f"成品 UI 皮肤引用了不存在的素材：{label} ({asset_id})",
                "重新选择这个 UI 素材，或清空该绑定；Runtime 会回退到基础 UI，但自定义皮肤不会完整显示。",
                check_path,
            )
            continue
        export_url = str(asset.get("exportUrl") or "").strip()
        if asset.get("isMissing") or not export_url or not (bundle_dir / export_url).is_file():
            add_release_check_issue(
                issues,
                "warning",
                "game_ui_asset_file_missing",
                f"成品 UI 皮肤素材不可用：{label}",
                "回到素材库重新导入或替换该 UI 素材，再重新导出原生 Runtime 包。",
                export_url or check_path,
            )
        if str(asset.get("type") or "") not in ASSET_TYPE_IMAGE:
            add_release_check_issue(
                issues,
                "warning",
                "game_ui_asset_type_risk",
                f"成品 UI 皮肤绑定的不是图片素材：{label}",
                "九宫格、Logo 和 UI 叠层建议使用 ui/background/cg/sprite 类型图片。",
                export_url or check_path,
            )

    font_asset_id = str(game_ui_config.get("fontAssetId") or "").strip()
    if font_asset_id:
        font_asset = assets_by_id.get(font_asset_id)
        if not font_asset:
            add_release_check_issue(
                issues,
                "warning",
                "font_asset_reference_missing",
                f"项目字体引用了不存在的素材：{font_asset_id}",
                "重新选择字体素材或清空字体绑定；Runtime 会回退到系统字体。",
                f"project.gameUiConfig.fontAssetId={font_asset_id}",
            )
        else:
            font_export_url = str(font_asset.get("exportUrl") or "").strip()
            font_asset_path = bundle_dir / font_export_url if font_export_url else None
            if font_asset.get("isMissing") or not font_export_url or not font_asset_path or not font_asset_path.is_file():
                add_release_check_issue(
                    issues,
                    "warning",
                    "font_asset_file_missing",
                    f"项目字体文件不可用：{font_asset.get('name') or font_asset_id}",
                    "重新导入字体文件，或改用系统字体族。",
                    font_export_url or font_asset_id,
                )
            elif font_asset_path.suffix.lower() not in SUPPORTED_FONT_EXTENSIONS:
                add_release_check_issue(
                    issues,
                    "warning",
                    "font_extension_risk",
                    f"字体格式可能不稳定：{font_asset.get('name') or font_asset_id} ({font_asset_path.suffix or '无扩展名'})",
                    "建议使用 ttf、otf 或 ttc，并确认字体授权允许随游戏分发。",
                    font_export_url,
                )

    for character in characters:
        if not isinstance(character, dict):
            continue
        character_id = str(character.get("id") or "unknown")
        character_name = str(character.get("displayName") or character_id)
        presentation = character.get("presentation") if isinstance(character.get("presentation"), dict) else {}
        mode = str(presentation.get("mode") or "sprite")
        if mode not in CHARACTER_PRESENTATION_MODE_LABELS:
            continue

        fallback_asset_id = str(presentation.get("fallbackSpriteAssetId") or character.get("defaultSpriteId") or "").strip()
        check_character_asset_reference(
            fallback_asset_id,
            label=f"角色 {character_name} 的兜底立绘",
            path=f"characters.{character_id}.presentation.fallbackSpriteAssetId",
            expected_types=set(ASSET_TYPE_IMAGE),
            missing_severity="warning",
        )

        if mode == "live2d":
            live2d = presentation.get("live2d") if isinstance(presentation.get("live2d"), dict) else {}
            model_asset_id = str(live2d.get("modelAssetId") or "").strip()
            model_asset = check_character_asset_reference(
                model_asset_id,
                label=f"角色 {character_name} 的 Live2D 模型入口",
                path=f"characters.{character_id}.presentation.live2d.modelAssetId",
                expected_types={"live2d"},
                missing_severity="warning",
            )
            if model_asset:
                export_url = str(model_asset.get("exportUrl") or model_asset.get("path") or "").lower()
                if not export_url.endswith(".model3.json"):
                    add_release_check_issue(
                        issues,
                        "warning",
                        "character_live2d_entry_not_model3_json",
                        f"角色 {character_name} 的 Live2D 入口建议使用 .model3.json。",
                        "绑定 .model3.json 后，后续渲染层更容易自动找到 moc3、贴图、物理和动作文件。",
                        f"characters.{character_id}.presentation.live2d.modelAssetId",
                    )

        if mode == "model3d":
            model3d = presentation.get("model3d") if isinstance(presentation.get("model3d"), dict) else {}
            model_asset_id = str(model3d.get("modelAssetId") or "").strip()
            model_asset = check_character_asset_reference(
                model_asset_id,
                label=f"角色 {character_name} 的 3D 模型",
                path=f"characters.{character_id}.presentation.model3d.modelAssetId",
                expected_types={"model3d"},
                missing_severity="warning",
            )
            if model_asset:
                export_url = str(model_asset.get("exportUrl") or model_asset.get("path") or "").lower()
                if not re.search(r"\.(glb|gltf|vrm)$", export_url):
                    add_release_check_issue(
                        issues,
                        "warning",
                        "character_model3d_format_risk",
                        f"角色 {character_name} 的 3D 模型建议优先使用 glb、gltf 或 vrm。",
                        "fbx / obj 可以作为记录格式，但后续跨平台 Runtime 更适合先支持 glb、gltf、vrm。",
                        f"characters.{character_id}.presentation.model3d.modelAssetId",
                    )

        expressions = character.get("expressions") if isinstance(character.get("expressions"), list) else []
        if mode in {"layered_sprite", "live2d", "model3d"} and not expressions:
            add_release_check_issue(
                issues,
                "warning",
                "character_presentation_no_expressions",
                f"角色 {character_name} 还没有表情条目。",
                "至少保留一个默认表情，后续差分、Live2D 表情或 3D 动作映射会更稳定。",
                f"characters.{character_id}.expressions",
            )
        if mode == "layered_sprite":
            mapped_count = sum(1 for expression in expressions if expression.get("layerAssetIds"))
        elif mode == "live2d":
            mapped_count = sum(1 for expression in expressions if expression.get("live2dExpression") or expression.get("live2dMotion"))
        elif mode == "model3d":
            mapped_count = sum(1 for expression in expressions if expression.get("model3dExpression") or expression.get("model3dAnimation"))
        else:
            mapped_count = len(expressions)
        if mode in {"layered_sprite", "live2d", "model3d"} and expressions and mapped_count < len(expressions):
            add_release_check_issue(
                issues,
                "warning",
                "character_presentation_mapping_incomplete",
                f"角色 {character_name} 的高级表情映射未覆盖完：{mapped_count}/{len(expressions)}。",
                "不覆盖也能运行，但对应表情会回退到默认外观；正式发布前建议补齐主角和高频角色。",
                f"characters.{character_id}.expressions",
            )

    for asset in assets:
        if not isinstance(asset, dict):
            continue
        asset_name = str(asset.get("name") or asset.get("id") or "未命名素材")
        asset_type = str(asset.get("type") or "misc")
        export_url = str(asset.get("exportUrl") or "").strip()
        if asset.get("isMissing"):
            add_release_check_issue(
                issues,
                "error",
                "asset_marked_missing",
                f"素材缺失：{asset_name}",
                "回到素材库重新绑定文件，或删除未使用的缺失素材后重新导出。",
                export_url or asset_name,
            )
            continue
        if not export_url:
            continue
        asset_path = bundle_dir / export_url
        if not asset_path.is_file():
            add_release_check_issue(
                issues,
                "error",
                "asset_file_missing",
                f"导出资源不存在：{export_url}",
                "重新导出，或检查压缩包解压后是否遗漏 assets 目录。",
                export_url,
            )
            continue
        extension = asset_path.suffix.lower()
        file_size = asset_path.stat().st_size
        if asset_type in ASSET_TYPE_IMAGE and extension not in SUPPORTED_IMAGE_EXTENSIONS:
            add_release_check_issue(
                issues,
                "warning",
                "image_extension_risk",
                f"图片素材格式可能不稳定：{asset_name} ({extension or '无扩展名'})",
                "建议使用 png、jpg、jpeg、bmp 或 webp。",
                export_url,
            )
        if asset_type in {"bgm", "sfx", "voice", "audio"} and extension not in SUPPORTED_AUDIO_EXTENSIONS:
            add_release_check_issue(
                issues,
                "warning",
                "audio_extension_risk",
                f"音频素材格式可能不稳定：{asset_name} ({extension or '无扩展名'})",
                "建议使用 ogg、wav 或 mp3，并在目标系统实机听一遍。",
                export_url,
            )
        if asset_type == "font" and extension not in SUPPORTED_FONT_EXTENSIONS:
            add_release_check_issue(
                issues,
                "warning",
                "font_extension_risk",
                f"字体素材格式可能不稳定：{asset_name} ({extension or '无扩展名'})",
                "建议使用 ttf、otf 或 ttc，并确认字体授权允许随游戏分发。",
                export_url,
            )
        if asset_type == "live2d" and not any(str(asset_path.name).lower().endswith(suffix) for suffix in SUPPORTED_LIVE2D_SUFFIXES):
            add_release_check_issue(
                issues,
                "warning",
                "live2d_extension_risk",
                f"Live2D 素材入口可能不完整：{asset_name} ({asset_path.name})",
                "建议至少绑定 .model3.json 作为模型入口，并随包保留 textures、motions 和 moc3 等依赖文件。",
                export_url,
            )
        if asset_type == "live2d" and str(asset_path.name).lower().endswith(".model3.json"):
            try:
                model3_payload = json.loads(asset_path.read_text(encoding="utf-8"))
            except Exception as error:
                add_release_check_issue(
                    issues,
                    "error",
                    "live2d_model3_json_invalid",
                    f"Live2D 模型入口无法解析：{asset_name}",
                    f"确认 .model3.json 是有效 JSON，并且不是被压缩或损坏的文件。错误：{error}",
                    export_url,
                )
            else:
                live2d_references = collect_live2d_model3_references(model3_payload)
                if not live2d_references:
                    add_release_check_issue(
                        issues,
                        "warning",
                        "live2d_model3_no_file_references",
                        f"Live2D 模型入口没有检测到依赖文件：{asset_name}",
                        "正常的 .model3.json 通常会引用 moc3、textures、motions、physics 等文件；建议确认导入的是完整模型入口。",
                        export_url,
                    )
                unsafe_references: list[str] = []
                missing_references: list[str] = []
                for reference in live2d_references:
                    dependency_path = resolve_live2d_dependency_path(asset_path, reference, bundle_dir)
                    if dependency_path is None:
                        unsafe_references.append(reference)
                    elif not dependency_path.is_file():
                        missing_references.append(reference)
                if unsafe_references:
                    reference_preview = ", ".join(unsafe_references[:4])
                    if len(unsafe_references) > 4:
                        reference_preview += f" 等 {len(unsafe_references)} 项"
                    add_release_check_issue(
                        issues,
                        "warning",
                        "live2d_model3_dependency_path_unsafe",
                        f"Live2D 模型入口引用了导出包外的路径：{asset_name}",
                        f"请把这些引用改成模型目录内的相对路径：{reference_preview}",
                        export_url,
                    )
                if missing_references:
                    reference_preview = ", ".join(missing_references[:4])
                    if len(missing_references) > 4:
                        reference_preview += f" 等 {len(missing_references)} 项"
                    add_release_check_issue(
                        issues,
                        "warning",
                        "live2d_model3_dependency_missing",
                        f"Live2D 模型入口缺少依赖文件：{asset_name}",
                        f"请随 .model3.json 一起导入并导出这些文件：{reference_preview}",
                        export_url,
                    )
        if asset_type in {"model3d", "scene3d"} and extension not in SUPPORTED_MODEL3D_EXTENSIONS:
            asset_label = "3D 场景" if asset_type == "scene3d" else "3D 模型"
            issue_code = "scene3d_extension_risk" if asset_type == "scene3d" else "model3d_extension_risk"
            add_release_check_issue(
                issues,
                "warning",
                issue_code,
                f"{asset_label}格式可能不稳定：{asset_name} ({extension or '无扩展名'})",
                "建议优先使用 glb、gltf 或 vrm；fbx/obj 后续需要转换层或专门渲染后端。",
                export_url,
            )
        if asset_type in {"model3d", "scene3d"} and extension in {".gltf", ".glb", ".vrm"}:
            asset_label = "3D 场景" if asset_type == "scene3d" else "3D 模型"
            issue_prefix = "scene3d" if asset_type == "scene3d" else "model3d"
            gltf_payload, source_type, container_probe, error = load_gltf_static_payload(asset_path)
            if gltf_payload is None:
                add_release_check_issue(
                    issues,
                    "error",
                    f"{issue_prefix}_{source_type}_json_invalid",
                    f"{asset_label}入口无法解析：{asset_name}",
                    f"确认 {extension} 是有效的 glTF/GLB/VRM 文件；如果文件损坏，请从建模工具重新导出。错误：{error}",
                    export_url,
                )
            else:
                if container_probe and int(container_probe.get("issueCount") or 0) > 0:
                    container_issues = [
                        str(issue.get("path") or issue.get("code") or "未知位置")
                        for issue in container_probe.get("issues") or []
                        if isinstance(issue, dict)
                    ]
                    issue_preview = ", ".join(container_issues[:5]) if container_issues else "容器头或 chunk 异常"
                    if len(container_issues) > 5:
                        issue_preview += f" 等 {len(container_issues)} 项"
                    add_release_check_issue(
                        issues,
                        "warning",
                        f"{issue_prefix}_{source_type}_container_issue",
                        f"{asset_label}二进制容器需要复核：{asset_name}",
                        f"{source_type.upper()} 容器存在长度、chunk 或 JSON 包装问题；建议重新导出。位置：{issue_preview}",
                        export_url,
                    )
                structure_summary = summarize_gltf_payload_structure(gltf_payload, source_type)
                if asset_type == "scene3d" and structure_summary.get("status") == "empty":
                    add_release_check_issue(
                        issues,
                        "warning",
                        f"scene3d_{source_type}_empty_structure",
                        f"3D 场景入口缺少可分析结构：{asset_name}",
                        f"建议确认 {extension} 内含 scenes、nodes、meshes；如果只是占位文件，导出前请替换为正式场景。",
                        export_url,
                    )
                preview_probe = summarize_gltf_preview_probe(asset_path, bundle_dir)
                if int(preview_probe.get("textureSlotIssueCount") or 0) > 0:
                    slot_issues: list[str] = []
                    for material in preview_probe.get("materials") or []:
                        if not isinstance(material, dict):
                            continue
                        material_name = str(material.get("name") or "未命名材质")
                        for slot in material.get("textureSlots") or []:
                            if not isinstance(slot, dict):
                                continue
                            if str(slot.get("status") or "") in {"ready", "embedded"}:
                                continue
                            slot_issues.append(
                                f"{material_name}/{slot.get('label') or slot.get('slot')}: {slot.get('status')}"
                            )
                    slot_preview = ", ".join(slot_issues[:4]) if slot_issues else "材质贴图槽索引异常"
                    if len(slot_issues) > 4:
                        slot_preview += f" 等 {len(slot_issues)} 项"
                    add_release_check_issue(
                        issues,
                        "warning",
                        f"{issue_prefix}_{source_type}_material_texture_slot_issue",
                        f"{asset_label}材质贴图槽需要复核：{asset_name}",
                        f"请检查 glTF 材质里的 texture index、image source 和图片文件是否对应；问题：{slot_preview}",
                        export_url,
                    )
                integrity_probe = build_gltf_integrity_probe(gltf_payload)
                if int(integrity_probe.get("issueCount") or 0) > 0:
                    integrity_issues = [
                        str(issue.get("path") or issue.get("code") or "未知位置")
                        for issue in integrity_probe.get("issues") or []
                        if isinstance(issue, dict)
                    ]
                    issue_preview = ", ".join(integrity_issues[:5]) if integrity_issues else "内部索引断链"
                    if len(integrity_issues) > 5:
                        issue_preview += f" 等 {len(integrity_issues)} 项"
                    add_release_check_issue(
                        issues,
                        "warning",
                        f"{issue_prefix}_{source_type}_integrity_issue",
                        f"{asset_label}内部引用需要复核：{asset_name}",
                        f"glTF 内部 scene/node/mesh/material/animation 等索引存在断链；请重新导出或修复这些位置：{issue_preview}",
                        export_url,
                    )
                performance_probe = build_gltf_performance_budget_probe(gltf_payload, asset_type)
                if int(performance_probe.get("issueCount") or 0) > 0:
                    budget_issues = [
                        f"{issue.get('label') or issue.get('metric')} {issue.get('value')}/{issue.get('limit')}"
                        for issue in performance_probe.get("issues") or []
                        if isinstance(issue, dict)
                    ]
                    issue_preview = "，".join(budget_issues[:5]) if budget_issues else "性能预算超限"
                    if len(budget_issues) > 5:
                        issue_preview += f" 等 {len(budget_issues)} 项"
                    add_release_check_issue(
                        issues,
                        "warning",
                        f"{issue_prefix}_{source_type}_performance_budget_risk",
                        f"{asset_label}性能预算偏高：{asset_name}",
                        f"静态估算显示该 3D 资产可能影响低配设备或移动端路线；建议优化后再发布。超预算项：{issue_preview}",
                        export_url,
                    )
                gltf_references = collect_gltf_references(gltf_payload)
                unsafe_references: list[str] = []
                missing_references: list[str] = []
                for reference in gltf_references:
                    dependency_path = resolve_model3d_dependency_path(asset_path, reference, bundle_dir)
                    if dependency_path is None:
                        unsafe_references.append(reference)
                    elif not dependency_path.is_file():
                        missing_references.append(reference)
                if unsafe_references:
                    reference_preview = ", ".join(unsafe_references[:4])
                    if len(unsafe_references) > 4:
                        reference_preview += f" 等 {len(unsafe_references)} 项"
                    add_release_check_issue(
                        issues,
                        "warning",
                        f"{issue_prefix}_{source_type}_dependency_path_unsafe",
                        f"{asset_label}入口引用了导出包外的路径：{asset_name}",
                        f"请把这些引用改成模型目录内的相对路径，或导出为自包含 .glb：{reference_preview}",
                        export_url,
                    )
                if missing_references:
                    reference_preview = ", ".join(missing_references[:4])
                    if len(missing_references) > 4:
                        reference_preview += f" 等 {len(missing_references)} 项"
                    add_release_check_issue(
                        issues,
                        "warning",
                        f"{issue_prefix}_{source_type}_dependency_missing",
                        f"{asset_label}入口缺少依赖文件：{asset_name}",
                        f"请随 {extension} 入口一起导入并导出这些文件，或改用自包含 .glb：{reference_preview}",
                        export_url,
                    )
        if asset_type == "video":
            if extension not in SUPPORTED_VIDEO_EXTENSIONS:
                add_release_check_issue(
                    issues,
                    "warning",
                    "video_extension_risk",
                    f"视频素材格式可能不稳定：{asset_name} ({extension or '无扩展名'})",
                    "建议使用 mp4、webm、mov 或 m4v，并在目标系统实机播放一次。",
                    export_url,
                )
            video_bridge_available = can_open_external_video()
            optional_video_hint = (
                f"如需检查可选窗口内嵌画面播放，可运行 python runtime_player.py --probe-video-preview .，"
                f"或安装 {NATIVE_VIDEO_OPTIONAL_REQUIREMENTS_NAME}。"
            )
            add_release_check_issue(
                issues,
                "warning",
                "video_native_external_player_bridge"
                if video_bridge_available
                else "video_native_external_player_missing",
                f"原生 Runtime 可用 OpenCV 进行实验性内嵌画面播放，并保留系统播放器桥接：{asset_name}",
                (
                    "运行到视频卡时可按 V 尝试窗口内嵌画面播放，按 O 调用"
                    f"{get_external_video_opener_label()}播放音频版；正式发布前仍建议在目标系统实机确认 OP/ED/PV。"
                    + optional_video_hint
                    if video_bridge_available
                    else "当前系统没有检测到可用的视频打开器；可安装可选 OpenCV 后端尝试内嵌画面播放，网页包和 NW.js 桌面包仍可直接播放视频。"
                    + optional_video_hint
                ),
                export_url,
            )
            if file_size > LARGE_VIDEO_WARNING_BYTES:
                add_release_check_issue(
                    issues,
                    "warning",
                    "large_video_asset",
                    f"视频素材偏大：{asset_name} ({file_size // 1024 // 1024} MB)",
                    "建议压缩码率或提供较短 OP/ED 版本，避免 Preview 包体过大。",
                    export_url,
                )
        if asset_type in ASSET_TYPE_IMAGE and file_size > LARGE_IMAGE_WARNING_BYTES:
            add_release_check_issue(
                issues,
                "warning",
                "large_image_asset",
                f"图片素材偏大：{asset_name} ({file_size // 1024 // 1024} MB)",
                "建议压缩或降低分辨率，避免低配机器切场景卡顿。",
                export_url,
            )
        if asset_type in {"bgm", "sfx", "voice", "audio"} and file_size > LARGE_AUDIO_WARNING_BYTES:
            add_release_check_issue(
                issues,
                "warning",
                "large_audio_asset",
                f"音频素材偏大：{asset_name} ({file_size // 1024 // 1024} MB)",
                "建议转成 ogg 或压缩码率，降低发布包体积。",
                export_url,
            )

    error_count = sum(1 for issue in issues if issue.get("severity") == "error")
    warning_count = sum(1 for issue in issues if issue.get("severity") == "warning")
    return {
        "status": get_release_check_status(issues),
        "checkedAt": now_iso(),
        "bundleDir": str(bundle_dir),
        "projectTitle": project_title,
        "summary": {
            "errors": error_count,
            "warnings": warning_count,
            "assetCount": len(assets),
            "sceneCount": len(scenes),
            "formalSaveSlotCount": formal_slot_count,
            "logicIssueCount": get_export_logic_issue_count(issues),
        },
        "issues": issues,
    }


def print_release_check_report(bundle_dir: Path) -> None:
    report = build_release_check_report(bundle_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def get_report_character_presentation(character: dict | None) -> dict:
    character = character or {}
    source = character.get("presentation") if isinstance(character.get("presentation"), dict) else {}
    mode = str(source.get("mode") or "sprite")
    if mode not in CHARACTER_PRESENTATION_MODE_LABELS:
        mode = "sprite"
    live2d = source.get("live2d") if isinstance(source.get("live2d"), dict) else {}
    model3d = source.get("model3d") if isinstance(source.get("model3d"), dict) else {}
    return {
        "mode": mode,
        "fallbackSpriteAssetId": str(source.get("fallbackSpriteAssetId") or character.get("defaultSpriteId") or ""),
        "live2d": {
            "modelAssetId": str(live2d.get("modelAssetId") or ""),
            "idleMotion": str(live2d.get("idleMotion") or ""),
        },
        "model3d": {
            "modelAssetId": str(model3d.get("modelAssetId") or ""),
            "idleAnimation": str(model3d.get("idleAnimation") or ""),
        },
    }


def get_report_character_model_asset_id(character: dict | None) -> str:
    presentation = get_report_character_presentation(character)
    mode = str(presentation.get("mode") or "sprite")
    if mode == "live2d":
        return str((presentation.get("live2d") or {}).get("modelAssetId") or "").strip()
    if mode == "model3d":
        return str((presentation.get("model3d") or {}).get("modelAssetId") or "").strip()
    return ""


def summarize_native_model_dependency_health(bundle_dir: Path, mode: str, model_path: Path | None) -> dict:
    if not model_path:
        return {"total": 0, "missing": [], "unsafe": [], "status": "unknown", "label": "依赖：待检测"}

    lower_name = model_path.name.lower()
    references: list[str] = []
    missing: list[str] = []
    unsafe: list[str] = []
    status = "ready"

    if mode == "live2d" and lower_name.endswith(".model3.json"):
        try:
            references = collect_live2d_model3_references(json.loads(model_path.read_text(encoding="utf-8")))
        except Exception:
            return {"total": 0, "missing": [], "unsafe": [], "status": "invalid", "label": "依赖：入口 JSON 异常"}
        for reference in references:
            dependency_path = resolve_live2d_dependency_path(model_path, reference, bundle_dir)
            if dependency_path is None:
                unsafe.append(reference)
            elif not dependency_path.is_file():
                missing.append(reference)
    elif mode == "model3d" and model_path.suffix.lower() in {".gltf", ".glb", ".vrm"}:
        payload, source_type, container_probe, error = load_gltf_static_payload(model_path)
        if payload is None:
            return {"total": 0, "missing": [], "unsafe": [], "status": "invalid", "label": f"依赖：{error or '入口异常'}"}
        references = collect_gltf_references(payload)
        if container_probe and container_probe.get("status") == "needs_attention":
            status = "partial"
        for reference in references:
            dependency_path = resolve_model3d_dependency_path(model_path, reference, bundle_dir)
            if dependency_path is None:
                unsafe.append(reference)
            elif not dependency_path.is_file():
                missing.append(reference)
        if not references and container_probe:
            return {
                "total": 0,
                "missing": [],
                "unsafe": [],
                "status": status,
                "label": f"依赖：{source_type.upper()} 单文件 / {container_probe.get('label')}",
            }
    elif mode == "model3d" and model_path.suffix.lower() in {".fbx", ".obj"}:
        return {"total": 0, "missing": [], "unsafe": [], "status": "partial", "label": "依赖：需转换/材质复核"}
    elif mode == "live2d":
        return {"total": 0, "missing": [], "unsafe": [], "status": "partial", "label": "依赖：建议绑定 model3.json"}

    if unsafe or missing:
        status = "partial"
    if not references:
        return {"total": 0, "missing": missing, "unsafe": unsafe, "status": status, "label": "依赖：无外部引用"}
    ready_count = max(0, len(references) - len(missing) - len(unsafe))
    label = f"依赖：{ready_count}/{len(references)} 已就绪" if status == "ready" else f"依赖：缺 {len(missing) + len(unsafe)}/{len(references)} 项"
    return {"total": len(references), "missing": missing, "unsafe": unsafe, "status": status, "label": label}


def count_character_model_expression_bindings(character: dict, mode: str) -> tuple[int, int]:
    expressions = character.get("expressions") if isinstance(character.get("expressions"), list) else []
    if mode == "live2d":
        mapped_count = sum(1 for expression in expressions if expression.get("live2dExpression") or expression.get("live2dMotion"))
    elif mode == "model3d":
        mapped_count = sum(1 for expression in expressions if expression.get("model3dExpression") or expression.get("model3dAnimation"))
    elif mode == "layered_sprite":
        mapped_count = sum(1 for expression in expressions if expression.get("layerAssetIds"))
    else:
        mapped_count = len(expressions)
    return len(expressions), mapped_count


def build_native_character_model_preview_report(bundle_dir: Path) -> dict:
    payload = load_game_data(bundle_dir / DEFAULT_GAME_DATA_NAME)
    assets_doc = payload.get("assets") if isinstance(payload.get("assets"), dict) else {}
    assets = assets_doc.get("assets") if isinstance(assets_doc.get("assets"), list) else []
    assets_by_id = {str(asset.get("id")): asset for asset in assets if isinstance(asset, dict) and asset.get("id")}
    characters_doc = payload.get("characters") if isinstance(payload.get("characters"), dict) else {}
    characters = characters_doc.get("characters") if isinstance(characters_doc.get("characters"), list) else []

    entries = []
    for character in characters:
        if not isinstance(character, dict):
            continue
        presentation = get_report_character_presentation(character)
        mode = str(presentation.get("mode") or "sprite")
        if mode not in {"live2d", "model3d"}:
            continue
        fallback_asset_id = str(presentation.get("fallbackSpriteAssetId") or character.get("defaultSpriteId") or "").strip()
        fallback_asset = assets_by_id.get(fallback_asset_id) if fallback_asset_id else None
        fallback_path = get_asset_runtime_path(bundle_dir, fallback_asset)
        model_asset_id = get_report_character_model_asset_id(character)
        model_asset = assets_by_id.get(model_asset_id) if model_asset_id else None
        model_path = get_asset_runtime_path(bundle_dir, model_asset)
        dependency_health = summarize_native_model_dependency_health(bundle_dir, mode, model_path)
        expression_count, mapped_count = count_character_model_expression_bindings(character, mode)

        if not model_asset_id:
            status = "unbound"
        elif not model_asset:
            status = "missing_asset"
        elif not model_path:
            status = "missing_file"
        elif dependency_health.get("status") == "invalid":
            status = "invalid"
        elif dependency_health.get("status") == "partial":
            status = "partial"
        else:
            status = "ready"

        entries.append(
            {
                "characterId": str(character.get("id") or ""),
                "name": str(character.get("displayName") or character.get("id") or "未命名角色"),
                "mode": mode,
                "modeLabel": CHARACTER_PRESENTATION_MODE_LABELS.get(mode, mode),
                "status": status,
                "statusLabel": {
                    "unbound": "模型未绑定",
                    "missing_asset": "素材记录缺失",
                    "missing_file": "模型文件缺失",
                    "invalid": "入口异常",
                    "partial": "需要补强",
                    "ready": "资源完整",
                }.get(status, "待检查"),
                "modelAssetId": model_asset_id,
                "modelAssetName": str((model_asset or {}).get("name") or model_asset_id or "未绑定"),
                "modelExportUrl": str((model_asset or {}).get("exportUrl") or ""),
                "modelFileExists": bool(model_path),
                "dependencyHealth": dependency_health,
                "fallback": {
                    "assetId": fallback_asset_id,
                    "assetName": str((fallback_asset or {}).get("name") or fallback_asset_id or "未绑定"),
                    "status": "ready" if fallback_path else ("missing" if fallback_asset_id else "none"),
                },
                "expressionMapping": {
                    "expressionCount": expression_count,
                    "mappedCount": mapped_count,
                    "incomplete": expression_count > 0 and mapped_count < expression_count,
                },
                "nativePreviewMode": "metadata_bridge",
            }
        )

    asset_issue_count = sum(1 for entry in entries if entry["status"] != "ready")
    mapping_gap_count = sum(1 for entry in entries if entry["expressionMapping"]["incomplete"])
    status = "no_advanced_models" if not entries else ("ready" if asset_issue_count == 0 and mapping_gap_count == 0 else "needs_attention")
    return {
        "status": status,
        "checkedAt": now_iso(),
        "bundleDir": str(bundle_dir),
        "summary": {
            "advancedCharacterCount": len(entries),
            "readyCount": sum(1 for entry in entries if entry["status"] == "ready"),
            "assetIssueCount": asset_issue_count,
            "mappingGapCount": mapping_gap_count,
        },
        "entries": entries,
    }


def print_native_character_model_preview_report(bundle_dir: Path) -> None:
    report = build_native_character_model_preview_report(bundle_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def normalize_scene3d_preview_config(source: dict | None = None) -> dict:
    raw = source if isinstance(source, dict) else {}

    def read_number(key: str, fallback: float, minimum: float, maximum: float) -> float:
        try:
            value = float(raw.get(key, fallback))
        except (TypeError, ValueError):
            value = fallback
        return float(clamp(value, minimum, maximum))

    return {
        "yaw": read_number("yaw", float(DEFAULT_SCENE3D_PREVIEW["yaw"]), 0.0, 359.0),
        "pitch": read_number("pitch", float(DEFAULT_SCENE3D_PREVIEW["pitch"]), 12.0, 72.0),
        "zoom": read_number("zoom", float(DEFAULT_SCENE3D_PREVIEW["zoom"]), 0.55, 1.9),
        "interactionEnabled": raw.get("interactionEnabled", DEFAULT_SCENE3D_PREVIEW["interactionEnabled"]) is not False,
    }


def build_native_scene3d_preview_report(bundle_dir: Path) -> dict:
    payload = load_game_data(bundle_dir / DEFAULT_GAME_DATA_NAME)
    assets_doc = payload.get("assets") if isinstance(payload.get("assets"), dict) else {}
    assets = assets_doc.get("assets") if isinstance(assets_doc.get("assets"), list) else []
    chapters = payload.get("chapters") if isinstance(payload.get("chapters"), list) else []

    scene_usage_by_asset: dict[str, list[dict]] = {}
    for chapter in chapters:
        chapter_name = str(chapter.get("name") or chapter.get("chapterId") or "未命名章节")
        for scene in chapter.get("scenes") or []:
            scene_name = str(scene.get("name") or scene.get("id") or "未命名场景")
            for block_index, block in enumerate(scene.get("blocks") or []):
                if str(block.get("type") or "").strip() != "background":
                    continue
                asset_id = str(block.get("assetId") or "").strip()
                if not asset_id:
                    continue
                scene_usage_by_asset.setdefault(asset_id, []).append(
                    {
                        "chapterName": chapter_name,
                        "sceneId": str(scene.get("id") or ""),
                        "sceneName": scene_name,
                        "blockIndex": block_index,
                        "previewConfig": normalize_scene3d_preview_config(
                            block.get("scene3dPreview") if isinstance(block.get("scene3dPreview"), dict) else None
                        ),
                    }
                )

    entries = []
    for asset in assets:
        if not isinstance(asset, dict) or asset.get("type") != "scene3d":
            continue
        asset_id = str(asset.get("id") or "")
        export_url = str(asset.get("exportUrl") or "").strip()
        asset_path = get_asset_runtime_path(bundle_dir, asset)
        dependency_health = summarize_native_model_dependency_health(bundle_dir, "model3d", asset_path)
        structure_summary = summarize_gltf_structure(asset_path)
        if asset.get("isMissing") or not asset_path:
            status = "missing_file"
        elif dependency_health.get("status") == "invalid" or structure_summary.get("status") == "invalid":
            status = "invalid"
        elif dependency_health.get("status") == "partial" or structure_summary.get("status") in {"empty", "partial"}:
            status = "partial"
        else:
            status = "ready"
        entries.append(
            {
                "assetId": asset_id,
                "name": str(asset.get("name") or asset_id or "未命名 3D 场景"),
                "exportUrl": export_url,
                "fileExists": bool(asset_path),
                "extension": asset_path.suffix.lower() if asset_path else Path(export_url).suffix.lower(),
                "status": status,
                "statusLabel": {
                    "missing_file": "场景文件缺失",
                    "invalid": "入口异常",
                    "partial": "需要补强",
                    "ready": "资源完整",
                }.get(status, "待检查"),
                "dependencyHealth": dependency_health,
                "structureSummary": structure_summary,
                "usageCount": len(scene_usage_by_asset.get(asset_id, [])),
                "usages": scene_usage_by_asset.get(asset_id, []),
                "nativePreviewMode": "interactive_spatial_bridge",
                "controls": ["Left/Right yaw", "Up/Down pitch", "+/- zoom", "0 reset"],
            }
        )

    issue_count = sum(1 for entry in entries if entry["status"] != "ready")
    unused_count = sum(1 for entry in entries if entry["usageCount"] == 0)
    status = "no_scene3d" if not entries else ("ready" if issue_count == 0 else "needs_attention")
    return {
        "status": status,
        "checkedAt": now_iso(),
        "bundleDir": str(bundle_dir),
        "summary": {
            "scene3dAssetCount": len(entries),
            "readyCount": sum(1 for entry in entries if entry["status"] == "ready"),
            "assetIssueCount": issue_count,
            "unusedCount": unused_count,
            "usageCount": sum(entry["usageCount"] for entry in entries),
        },
        "entries": entries,
    }


def print_native_scene3d_preview_report(bundle_dir: Path) -> None:
    report = build_native_scene3d_preview_report(bundle_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def build_native_3d_asset_report(bundle_dir: Path) -> dict:
    payload = load_game_data(bundle_dir / DEFAULT_GAME_DATA_NAME)
    assets_doc = payload.get("assets") if isinstance(payload.get("assets"), dict) else {}
    assets = assets_doc.get("assets") if isinstance(assets_doc.get("assets"), list) else []
    characters_doc = payload.get("characters") if isinstance(payload.get("characters"), dict) else {}
    characters = characters_doc.get("characters") if isinstance(characters_doc.get("characters"), list) else []
    chapters = payload.get("chapters") if isinstance(payload.get("chapters"), list) else []

    usages_by_asset: dict[str, list[dict]] = {}
    for character in characters:
        if not isinstance(character, dict):
            continue
        presentation = get_report_character_presentation(character)
        if str(presentation.get("mode") or "") != "model3d":
            continue
        asset_id = str((presentation.get("model3d") or {}).get("modelAssetId") or "").strip()
        if not asset_id:
            continue
        expression_count, mapped_count = count_character_model_expression_bindings(character, "model3d")
        usages_by_asset.setdefault(asset_id, []).append(
            {
                "kind": "character_model",
                "kindLabel": "角色 3D 模型",
                "characterId": str(character.get("id") or ""),
                "characterName": str(character.get("displayName") or character.get("id") or "未命名角色"),
                "idleAnimation": str((presentation.get("model3d") or {}).get("idleAnimation") or ""),
                "expressionCount": expression_count,
                "mappedExpressionCount": mapped_count,
            }
        )

    for chapter in chapters:
        chapter_name = str(chapter.get("name") or chapter.get("chapterId") or "未命名章节")
        for scene in chapter.get("scenes") or []:
            scene_name = str(scene.get("name") or scene.get("id") or "未命名场景")
            for block_index, block in enumerate(scene.get("blocks") or []):
                if not isinstance(block, dict) or str(block.get("type") or "").strip() != "background":
                    continue
                asset_id = str(block.get("assetId") or "").strip()
                if not asset_id:
                    continue
                usages_by_asset.setdefault(asset_id, []).append(
                    {
                        "kind": "scene_background",
                        "kindLabel": "3D 场景背景",
                        "chapterName": chapter_name,
                        "sceneId": str(scene.get("id") or ""),
                        "sceneName": scene_name,
                        "blockIndex": block_index,
                        "previewConfig": normalize_scene3d_preview_config(
                            block.get("scene3dPreview") if isinstance(block.get("scene3dPreview"), dict) else None
                        ),
                    }
                )

    entries = []
    for asset in assets:
        if not isinstance(asset, dict) or asset.get("type") not in {"model3d", "scene3d"}:
            continue
        asset_type = str(asset.get("type") or "")
        asset_id = str(asset.get("id") or "")
        export_url = str(asset.get("exportUrl") or "").strip()
        asset_path = get_asset_runtime_path(bundle_dir, asset)
        extension = asset_path.suffix.lower() if asset_path else Path(export_url).suffix.lower()
        dependency_health = summarize_native_model_dependency_health(bundle_dir, "model3d", asset_path)
        structure_summary = summarize_gltf_structure(asset_path)
        preview_probe = summarize_gltf_preview_probe(asset_path, bundle_dir)
        integrity_probe = {"status": "skipped", "label": "完整性：仅 glTF/GLB/VRM 可静态检查", "issueCount": 0, "issues": []}
        container_probe = {}
        performance_probe = {"status": "skipped", "label": "预算：仅 glTF/GLB/VRM 可静态估算", "issueCount": 0, "issues": [], "metrics": {}, "limits": {}}
        if asset_path and extension in {".gltf", ".glb", ".vrm"}:
            integrity_payload, _source_type, loaded_container_probe, error = load_gltf_static_payload(asset_path)
            container_probe = loaded_container_probe or {}
            if integrity_payload is None:
                integrity_probe = {
                    "status": "invalid",
                    "label": f"完整性：{error or '入口异常'}",
                    "issueCount": 1,
                    "issues": [
                        {
                            "code": "gltf_static_payload_invalid",
                            "path": export_url,
                            "message": "无法解析 glTF/GLB/VRM 静态元数据。",
                            "suggestion": "重新导出有效的 glTF/GLB/VRM 文件。",
                        }
                    ],
                }
            else:
                integrity_probe = build_gltf_integrity_probe(integrity_payload)
                performance_probe = build_gltf_performance_budget_probe(integrity_payload, asset_type)
        usage_entries = usages_by_asset.get(asset_id, [])

        if asset.get("isMissing") or not asset_path:
            status = "missing_file"
        elif extension not in SUPPORTED_MODEL3D_EXTENSIONS:
            status = "unsupported_extension"
        elif (
            dependency_health.get("status") == "invalid"
            or structure_summary.get("status") == "invalid"
            or integrity_probe.get("status") == "invalid"
        ):
            status = "invalid"
        elif structure_summary.get("status") == "unsupported" or extension in {".fbx", ".obj"}:
            status = "needs_conversion"
        elif (
            dependency_health.get("status") == "partial"
            or structure_summary.get("status") == "empty"
            or structure_summary.get("status") == "partial"
            or preview_probe.get("status") == "needs_attention"
            or integrity_probe.get("status") == "needs_attention"
            or performance_probe.get("status") == "needs_attention"
        ):
            status = "partial"
        else:
            status = "ready"

        action_by_status = {
            "missing_file": "重新导入或替换缺失的 3D 素材文件。",
            "unsupported_extension": "转换为 glb/gltf/vrm 后再导出，减少目标机兼容风险。",
            "invalid": "修复入口 JSON 或换用自包含 glb 文件。",
            "needs_conversion": "建议用 Blender 或资产管线转换为 glb/gltf，并复核材质贴图。",
            "partial": "补齐 glTF 外部依赖，并修复内部索引断链或空结构。",
            "ready": "可进入原生 Runtime Preview 点测。",
        }
        entries.append(
            {
                "assetId": asset_id,
                "type": asset_type,
                "typeLabel": "3D 场景" if asset_type == "scene3d" else "3D 模型",
                "name": str(asset.get("name") or asset_id or "未命名 3D 资产"),
                "exportUrl": export_url,
                "fileExists": bool(asset_path),
                "extension": extension,
                "status": status,
                "statusLabel": {
                    "missing_file": "文件缺失",
                    "unsupported_extension": "格式不支持",
                    "invalid": "入口异常",
                    "needs_conversion": "建议转换",
                    "partial": "需要补强",
                    "ready": "资源完整",
                }.get(status, "待检查"),
                "dependencyHealth": dependency_health,
                "structureSummary": structure_summary,
                "previewProbe": preview_probe,
                "gltfIntegrityProbe": integrity_probe,
                "glbContainerProbe": container_probe,
                "performanceBudgetProbe": performance_probe,
                "usageCount": len(usage_entries),
                "usages": usage_entries,
                "recommendedAction": action_by_status.get(status, "复核 3D 资产导入状态。"),
            }
        )

    issue_entries = [entry for entry in entries if entry.get("status") != "ready"]
    missing_dependency_count = sum(
        len((entry.get("dependencyHealth") or {}).get("missing") or [])
        + len((entry.get("dependencyHealth") or {}).get("unsafe") or [])
        for entry in entries
    )
    conversion_hint_count = sum(
        1
        for entry in entries
        if entry.get("status") == "needs_conversion" or entry.get("extension") in {".fbx", ".obj"}
    )
    empty_structure_count = sum(1 for entry in entries if (entry.get("structureSummary") or {}).get("status") == "empty")
    texture_slot_issue_count = sum(int((entry.get("previewProbe") or {}).get("textureSlotIssueCount") or 0) for entry in entries)
    integrity_issue_count = sum(int((entry.get("gltfIntegrityProbe") or {}).get("issueCount") or 0) for entry in entries)
    container_issue_count = sum(int((entry.get("glbContainerProbe") or {}).get("issueCount") or 0) for entry in entries)
    performance_issue_count = sum(int((entry.get("performanceBudgetProbe") or {}).get("issueCount") or 0) for entry in entries)
    unused_count = sum(1 for entry in entries if entry.get("usageCount") == 0)
    recommendations: list[str] = []
    if missing_dependency_count:
        recommendations.append("补齐 glTF 外部 bin/贴图依赖，或改用自包含 .glb。")
    if container_issue_count:
        recommendations.append("重新导出存在容器问题的 GLB/VRM：文件头、长度或 chunk 包装异常会影响后续渲染后端读取。")
    if texture_slot_issue_count:
        recommendations.append("检查材质贴图槽：有贴图索引、图片 URI 或贴图文件未能被预览探针确认。")
    if integrity_issue_count:
        recommendations.append("修复 glTF 内部索引断链：scene、node、mesh、material、texture 或 animation 引用需要重新导出确认。")
    if performance_issue_count:
        recommendations.append("优化 3D 性能预算：降低面数、合批 draw call、压缩材质/贴图数量，低配设备会更稳。")
    if conversion_hint_count:
        recommendations.append("将 FBX/OBJ 等格式转换为 glb/gltf，并在目标系统实机点测材质。")
    if empty_structure_count:
        recommendations.append("替换缺少 nodes/meshes 的空壳 glTF 场景。")
    if unused_count:
        recommendations.append("清理未使用 3D 资产，或在剧情/角色设置中绑定它们。")
    if entries and not recommendations:
        recommendations.append("3D 资产结构和依赖已通过 Preview 清单检查，下一步做目标系统实机渲染点测。")

    status = "no_3d_assets" if not entries else ("ready" if not issue_entries else "needs_attention")
    return {
        "status": status,
        "checkedAt": now_iso(),
        "bundleDir": str(bundle_dir),
        "summary": {
            "assetCount": len(entries),
            "model3dCount": sum(1 for entry in entries if entry.get("type") == "model3d"),
            "scene3dCount": sum(1 for entry in entries if entry.get("type") == "scene3d"),
            "readyCount": sum(1 for entry in entries if entry.get("status") == "ready"),
            "issueCount": len(issue_entries),
            "unusedCount": unused_count,
            "conversionHintCount": conversion_hint_count,
            "missingDependencyCount": missing_dependency_count,
            "emptyStructureCount": empty_structure_count,
            "textureSlotIssueCount": texture_slot_issue_count,
            "gltfIntegrityIssueCount": integrity_issue_count,
            "glbContainerIssueCount": container_issue_count,
            "performanceBudgetIssueCount": performance_issue_count,
            "textureSlotReadyCount": sum(int((entry.get("previewProbe") or {}).get("textureSlotReadyCount") or 0) for entry in entries),
            "totalTextureSlots": sum(int((entry.get("previewProbe") or {}).get("textureSlotCount") or 0) for entry in entries),
            "totalNodes": sum(int((entry.get("structureSummary") or {}).get("nodes") or 0) for entry in entries),
            "totalMeshes": sum(int((entry.get("structureSummary") or {}).get("meshes") or 0) for entry in entries),
            "totalMaterials": sum(int((entry.get("structureSummary") or {}).get("materials") or 0) for entry in entries),
            "totalTextures": sum(int((entry.get("structureSummary") or {}).get("textures") or 0) for entry in entries),
            "totalAnimations": sum(int((entry.get("structureSummary") or {}).get("animations") or 0) for entry in entries),
            "estimatedVertexCount": sum(int(((entry.get("performanceBudgetProbe") or {}).get("metrics") or {}).get("estimatedVertexCount") or 0) for entry in entries),
            "estimatedTriangleCount": sum(int(((entry.get("performanceBudgetProbe") or {}).get("metrics") or {}).get("estimatedTriangleCount") or 0) for entry in entries),
            "drawCallCount": sum(int(((entry.get("performanceBudgetProbe") or {}).get("metrics") or {}).get("drawCallCount") or 0) for entry in entries),
        },
        "recommendations": recommendations,
        "entries": entries,
    }


def print_native_3d_asset_report(bundle_dir: Path) -> None:
    report = build_native_3d_asset_report(bundle_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def format_markdown_value(value: object, fallback: str = "未记录") -> str:
    text = str(value if value is not None and value != "" else fallback)
    return text.replace("\n", " ").replace("|", "\\|")


def render_native_3d_asset_report_markdown(report: dict) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    entries = report.get("entries") if isinstance(report.get("entries"), list) else []
    recommendations = report.get("recommendations") if isinstance(report.get("recommendations"), list) else []
    lines = [
        "# 3D 资产清单摘要",
        "",
        f"- 状态：{format_markdown_value(report.get('status'))}",
        f"- 检查时间：{format_markdown_value(report.get('checkedAt'))}",
        f"- 导出包：{format_markdown_value(report.get('bundleDir'))}",
        "",
        "## 总览",
        "",
        "| 指标 | 数量 |",
        "| --- | ---: |",
        f"| 3D 资产 | {int(summary.get('assetCount') or 0)} |",
        f"| 3D 模型 | {int(summary.get('model3dCount') or 0)} |",
        f"| 3D 场景 | {int(summary.get('scene3dCount') or 0)} |",
        f"| 需要处理 | {int(summary.get('issueCount') or 0)} |",
        f"| 未使用 | {int(summary.get('unusedCount') or 0)} |",
        f"| glTF 节点 | {int(summary.get('totalNodes') or 0)} |",
        f"| glTF 网格 | {int(summary.get('totalMeshes') or 0)} |",
        f"| 材质 | {int(summary.get('totalMaterials') or 0)} |",
        f"| 贴图槽 | {int(summary.get('totalTextureSlots') or 0)} |",
        f"| 可读贴图槽 | {int(summary.get('textureSlotReadyCount') or 0)} |",
        f"| 贴图槽问题 | {int(summary.get('textureSlotIssueCount') or 0)} |",
        f"| glTF 内部引用问题 | {int(summary.get('gltfIntegrityIssueCount') or 0)} |",
        f"| GLB/VRM 容器问题 | {int(summary.get('glbContainerIssueCount') or 0)} |",
        f"| 性能预算问题 | {int(summary.get('performanceBudgetIssueCount') or 0)} |",
        f"| 估算顶点 | {int(summary.get('estimatedVertexCount') or 0)} |",
        f"| 估算三角面 | {int(summary.get('estimatedTriangleCount') or 0)} |",
        f"| draw call | {int(summary.get('drawCallCount') or 0)} |",
        f"| 动画 | {int(summary.get('totalAnimations') or 0)} |",
        "",
    ]
    if recommendations:
        lines.extend(["## 建议", ""])
        for recommendation in recommendations:
            lines.append(f"- {format_markdown_value(recommendation)}")
        lines.append("")

    if not entries:
        lines.extend(["## 资产", "", "当前导出包没有 3D 模型或 3D 场景资产。", ""])
        return "\n".join(lines).rstrip() + "\n"

    lines.extend(["## 资产详情", ""])
    for index, entry in enumerate(entries, start=1):
        dependency = entry.get("dependencyHealth") if isinstance(entry.get("dependencyHealth"), dict) else {}
        structure = entry.get("structureSummary") if isinstance(entry.get("structureSummary"), dict) else {}
        probe = entry.get("previewProbe") if isinstance(entry.get("previewProbe"), dict) else {}
        integrity = entry.get("gltfIntegrityProbe") if isinstance(entry.get("gltfIntegrityProbe"), dict) else {}
        budget = entry.get("performanceBudgetProbe") if isinstance(entry.get("performanceBudgetProbe"), dict) else {}
        lines.extend(
            [
                f"### {index}. {format_markdown_value(entry.get('typeLabel'))}：{format_markdown_value(entry.get('name'))}",
                "",
                "| 项目 | 内容 |",
                "| --- | --- |",
                f"| 状态 | {format_markdown_value(entry.get('statusLabel'))} |",
                f"| 导出路径 | `{format_markdown_value(entry.get('exportUrl'))}` |",
                f"| 引用次数 | {int(entry.get('usageCount') or 0)} |",
                f"| 依赖 | {format_markdown_value(dependency.get('label'))} |",
                f"| 结构 | {format_markdown_value(structure.get('label'))} |",
                f"| 预览探针 | {format_markdown_value(probe.get('label'))} |",
                f"| 内部引用 | {format_markdown_value(integrity.get('label'))} |",
                f"| 性能预算 | {format_markdown_value(budget.get('label'))} |",
                f"| 建议动作 | {format_markdown_value(entry.get('recommendedAction'))} |",
                "",
            ]
        )
        budget_issues = budget.get("issues") if isinstance(budget.get("issues"), list) else []
        if budget_issues:
            lines.extend(["性能预算风险：", ""])
            for issue in budget_issues[:8]:
                if not isinstance(issue, dict):
                    continue
                lines.append(
                    f"- {format_markdown_value(issue.get('message'))} {format_markdown_value(issue.get('suggestion'), '')}"
                )
            lines.append("")
        integrity_issues = integrity.get("issues") if isinstance(integrity.get("issues"), list) else []
        if integrity_issues:
            lines.extend(["glTF 内部引用问题：", ""])
            for issue in integrity_issues[:8]:
                if not isinstance(issue, dict):
                    continue
                lines.append(
                    f"- `{format_markdown_value(issue.get('path'))}`：{format_markdown_value(issue.get('message'))}"
                )
            lines.append("")
        materials = probe.get("materials") if isinstance(probe.get("materials"), list) else []
        if materials:
            lines.extend(["材质贴图槽：", ""])
            for material in materials[:6]:
                if not isinstance(material, dict):
                    continue
                slots = material.get("textureSlots") if isinstance(material.get("textureSlots"), list) else []
                slot_label = "；".join(
                    f"{format_markdown_value(slot.get('label'))}={format_markdown_value(slot.get('uri'), '内嵌/未记录')}({format_markdown_value(slot.get('status'))})"
                    for slot in slots[:5]
                    if isinstance(slot, dict)
                )
                lines.append(
                    f"- {format_markdown_value(material.get('name'))}：{slot_label or '未绑定贴图槽'}"
                )
            lines.append("")
        animations = probe.get("animations") if isinstance(probe.get("animations"), list) else []
        if animations:
            lines.extend(["动画通道：", ""])
            for animation in animations[:6]:
                if not isinstance(animation, dict):
                    continue
                paths = animation.get("targetPaths") if isinstance(animation.get("targetPaths"), list) else []
                nodes = animation.get("targetNodes") if isinstance(animation.get("targetNodes"), list) else []
                lines.append(
                    f"- {format_markdown_value(animation.get('name'))}：通道 {int(animation.get('channelCount') or 0)}，"
                    f"目标 {format_markdown_value(', '.join(paths), '未记录')}，节点 {format_markdown_value(', '.join(nodes), '未记录')}"
                )
            lines.append("")
        usages = entry.get("usages") if isinstance(entry.get("usages"), list) else []
        if usages:
            lines.extend(["引用位置：", ""])
            for usage in usages[:6]:
                if not isinstance(usage, dict):
                    continue
                if usage.get("kind") == "character_model":
                    lines.append(f"- 角色：{format_markdown_value(usage.get('characterName'))}")
                else:
                    lines.append(
                        f"- 场景：{format_markdown_value(usage.get('chapterName'))} / {format_markdown_value(usage.get('sceneName'))}"
                    )
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def print_native_3d_asset_markdown_report(bundle_dir: Path) -> None:
    report = build_native_3d_asset_report(bundle_dir)
    print(render_native_3d_asset_report_markdown(report), end="")


def collect_video_block_usages(chapters: list[dict]) -> dict[str, list[dict]]:
    usages: dict[str, list[dict]] = {}
    for chapter in chapters:
        chapter_name = str(chapter.get("name") or chapter.get("chapterId") or "未命名章节")
        for scene in chapter.get("scenes") or []:
            scene_id = str(scene.get("id") or "")
            scene_name = str(scene.get("name") or scene_id or "未命名场景")
            for block_index, block in enumerate(scene.get("blocks") or []):
                if str(block.get("type") or "").strip() != "video_play":
                    continue
                asset_id = str(block.get("assetId") or "").strip()
                if not asset_id:
                    continue
                usages.setdefault(asset_id, []).append(
                    {
                        "chapterName": chapter_name,
                        "sceneId": scene_id,
                        "sceneName": scene_name,
                        "blockIndex": block_index,
                        "title": str(block.get("title") or "视频播放"),
                        "startTimeSeconds": block.get("startTimeSeconds"),
                        "endTimeSeconds": block.get("endTimeSeconds"),
                        "skippable": bool(block.get("skippable", True)),
                    }
                )
    return usages


def build_native_video_bridge_report(bundle_dir: Path) -> dict:
    data_path = bundle_dir / DEFAULT_GAME_DATA_NAME
    payload = load_game_data(data_path)
    assets_doc = payload.get("assets") if isinstance(payload.get("assets"), dict) else {}
    assets = assets_doc.get("assets") if isinstance(assets_doc.get("assets"), list) else []
    chapters = payload.get("chapters") if isinstance(payload.get("chapters"), list) else []
    video_usages = collect_video_block_usages(chapters)
    opener_available = can_open_external_video()
    entries = []
    for asset in assets:
        if not isinstance(asset, dict) or asset.get("type") != "video":
            continue
        asset_id = str(asset.get("id") or "")
        export_url = str(asset.get("exportUrl") or "").strip()
        asset_path = bundle_dir / export_url if export_url else None
        extension = asset_path.suffix.lower() if asset_path else ""
        exists = bool(asset_path and asset_path.is_file())
        entries.append(
            {
                "assetId": asset_id,
                "name": str(asset.get("name") or asset_id or "未命名视频"),
                "exportUrl": export_url,
                "exists": exists,
                "extension": extension,
                "extensionSupported": extension in SUPPORTED_VIDEO_EXTENSIONS,
                "externalPlaybackMode": "system_player_bridge",
                "embeddedPlaybackMode": NATIVE_VIDEO_SYNC_BACKEND_ID,
                "fallbackEmbeddedPlaybackMode": NATIVE_VIDEO_EMBEDDED_BACKEND_ID,
                "nativePreviewMode": NATIVE_VIDEO_PREVIEW_MODE,
                "openerAvailable": opener_available,
                "openerLabel": get_external_video_opener_label() if opener_available else "",
                "usages": video_usages.get(asset_id, []),
            }
        )
    return {
        "status": "ready" if entries and opener_available else ("no_video" if not entries else "needs_system_opener"),
        "checkedAt": now_iso(),
        "bundleDir": str(bundle_dir),
        "summary": {
            "videoAssetCount": len(entries),
            "videoBlockCount": sum(len(entry["usages"]) for entry in entries),
            "openerAvailable": opener_available,
        },
        "nativePreviewMode": NATIVE_VIDEO_PREVIEW_MODE,
        "backendOptions": get_native_video_backend_options(bundle_dir),
        "entries": entries,
    }


def print_native_video_bridge_report(bundle_dir: Path) -> None:
    report = build_native_video_bridge_report(bundle_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def build_native_video_backend_report(bundle_dir: Path) -> dict:
    bridge_report = build_native_video_bridge_report(bundle_dir)
    backend_options = bridge_report.get("backendOptions") or get_native_video_backend_options(bundle_dir)
    embedded_candidates = [
        option
        for option in backend_options
        if option.get("embeddedVideo")
    ]
    available_embedded = [option for option in embedded_candidates if option.get("available")]
    bridge_status = bridge_report.get("status")
    if bridge_status == "no_video":
        recommendation = "当前导出包没有视频素材；如果后续加入 OP/ED/PV，可以继续使用系统播放器桥接。"
    elif bridge_status == "ready":
        recommendation = "当前可以使用系统播放器桥接；安装可选视频依赖后，会优先尝试 PyAV/FFmpeg 音画同步内嵌播放，并以 OpenCV 画面播放兜底。"
    else:
        recommendation = "当前系统没有检测到可用外部视频打开器；可安装可选视频依赖尝试 PyAV/FFmpeg 音画同步或 OpenCV 画面播放，或优先发布网页/NW.js 包。"
    if available_embedded:
        recommendation += " 已检测到可选内嵌后端，可用于窗口内视频播放验证。"
    else:
        recommendation += f" 如需尝试实验性内嵌音画同步，可安装 {NATIVE_VIDEO_OPTIONAL_REQUIREMENTS_NAME}。"
    return {
        "status": (
            "no_video"
            if bridge_status == "no_video"
            else ("embedded_candidate_available" if available_embedded else "bridge_only")
        ),
        "checkedAt": now_iso(),
        "bundleDir": str(bundle_dir),
        "nativePreviewMode": NATIVE_VIDEO_PREVIEW_MODE,
        "videoAssetCount": (bridge_report.get("summary") or {}).get("videoAssetCount", 0),
        "videoBlockCount": (bridge_report.get("summary") or {}).get("videoBlockCount", 0),
        "recommendation": recommendation,
        "backendOptions": backend_options,
        "previewProbeCommand": "python runtime_player.py --probe-video-preview .",
    }


def print_native_video_backend_report(bundle_dir: Path) -> None:
    report = build_native_video_backend_report(bundle_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def build_video_preview_probe_entry_without_attempt(entry: dict, status: str, message: str) -> dict:
    usage = (entry.get("usages") or [{}])[0] or {}
    return {
        "assetId": entry.get("assetId"),
        "name": entry.get("name"),
        "exportUrl": entry.get("exportUrl"),
        "exists": bool(entry.get("exists")),
        "startTimeSeconds": normalize_video_time_seconds(usage.get("startTimeSeconds")),
        "attempted": False,
        "status": status,
        "message": message,
        "surfaceSize": None,
    }


def build_native_video_preview_probe_report(
    bundle_dir: Path,
    pygame_module=None,
    cv2_module=None,
    max_assets: int = 3,
) -> dict:
    bridge_report = build_native_video_bridge_report(bundle_dir)
    entries = bridge_report.get("entries") or []
    backend_options = bridge_report.get("backendOptions") or get_native_video_backend_options(bundle_dir)
    base_report = {
        "checkedAt": now_iso(),
        "bundleDir": str(bundle_dir),
        "nativePreviewMode": NATIVE_VIDEO_PREVIEW_MODE,
        "backendId": "opencv_frame_preview",
        "backendOptions": backend_options,
        "bridgeStatus": bridge_report.get("status"),
        "summary": {
            "videoAssetCount": len(entries),
            "probedCount": 0,
            "successCount": 0,
            "failedCount": 0,
        },
        "entries": [],
    }
    if not entries:
        return {
            **base_report,
            "status": "no_video",
            "recommendation": "当前导出包没有视频素材，不需要检查视频内嵌画面。",
        }

    cv2_available = cv2_module is not None or is_optional_python_module_available("cv2")
    if not cv2_available:
        return {
            **base_report,
            "status": "optional_dependency_missing",
            "recommendation": f"未安装 {NATIVE_VIDEO_OPTIONAL_REQUIREMENTS_NAME}，视频卡片会使用影院式桥接卡；需要窗口内嵌画面播放时再安装可选依赖。",
            "entries": [
                build_video_preview_probe_entry_without_attempt(entry, "optional_dependency_missing", "未安装 OpenCV：使用桥接卡")
                for entry in entries[:max_assets]
            ],
        }

    if pygame_module is None:
        os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
        pygame_module = import_optional_python_module("pygame")
    if pygame_module is None:
        return {
            **base_report,
            "status": "pygame_missing",
            "recommendation": "已检测到 OpenCV，但当前 Python 环境缺少 pygame-ce，无法生成 Runtime 预览 Surface。",
            "entries": [
                build_video_preview_probe_entry_without_attempt(entry, "pygame_missing", "缺少 pygame-ce：无法生成预览 Surface")
                for entry in entries[:max_assets]
            ],
        }

    should_quit_pygame = False
    if hasattr(pygame_module, "get_init") and hasattr(pygame_module, "init") and not pygame_module.get_init():
        pygame_module.init()
        should_quit_pygame = True

    probe_entries = []
    try:
        for entry in entries[:max_assets]:
            usage = (entry.get("usages") or [{}])[0] or {}
            start_time = normalize_video_time_seconds(usage.get("startTimeSeconds"))
            export_url = str(entry.get("exportUrl") or "").strip()
            asset_path = bundle_dir / export_url if export_url else None
            if not asset_path or not asset_path.is_file():
                probe_entries.append(
                    {
                        "assetId": entry.get("assetId"),
                        "name": entry.get("name"),
                        "exportUrl": export_url,
                        "exists": False,
                        "startTimeSeconds": start_time,
                        "attempted": False,
                        "status": "file_missing",
                        "message": "视频文件不存在",
                        "surfaceSize": None,
                    }
                )
                continue

            surface, message = load_opencv_video_frame_surface(
                pygame_module,
                asset_path,
                start_time,
                cv2_module=cv2_module,
            )
            surface_size = None
            if surface is not None:
                width, height = surface.get_size()
                surface_size = {"width": int(width), "height": int(height)}
            probe_entries.append(
                {
                    "assetId": entry.get("assetId"),
                    "name": entry.get("name"),
                    "exportUrl": export_url,
                    "exists": True,
                    "startTimeSeconds": start_time,
                    "attempted": True,
                    "status": "ready" if surface is not None else "frame_unavailable",
                    "message": message,
                    "surfaceSize": surface_size,
                }
            )
    finally:
        if should_quit_pygame and hasattr(pygame_module, "quit"):
            pygame_module.quit()

    success_count = sum(1 for entry in probe_entries if entry.get("status") == "ready")
    failed_count = sum(1 for entry in probe_entries if entry.get("status") != "ready")
    if success_count and failed_count:
        status = "partial"
        recommendation = "部分视频可以生成窗口内画面；失败的视频仍会自动回落到系统播放器桥接卡。"
    elif success_count:
        status = "ready"
        recommendation = "OpenCV 视频画面探针通过；视频卡片可显示帧预览并尝试窗口内嵌播放。"
    else:
        status = "all_failed"
        recommendation = "OpenCV 已可用，但没有视频成功生成窗口内画面；请检查编码格式，或继续使用系统播放器桥接。"

    return {
        **base_report,
        "status": status,
        "recommendation": recommendation,
        "summary": {
            "videoAssetCount": len(entries),
            "probedCount": len(probe_entries),
            "successCount": success_count,
            "failedCount": failed_count,
        },
        "entries": probe_entries,
    }


def print_native_video_preview_probe_report(bundle_dir: Path) -> None:
    report = build_native_video_preview_probe_report(bundle_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def get_doctor_status(checks: list[dict]) -> str:
    if any(check.get("status") == "fail" for check in checks):
        return "fail"
    if any(check.get("status") == "warn" for check in checks):
        return "warn"
    return "pass"


def build_doctor_summary(checks: list[dict]) -> dict:
    return {
        "checks": len(checks),
        "passed": sum(1 for check in checks if check.get("status") == "pass"),
        "warnings": sum(1 for check in checks if check.get("status") == "warn"),
        "failed": sum(1 for check in checks if check.get("status") == "fail"),
        "skipped": sum(1 for check in checks if check.get("status") == "skipped"),
    }


def build_doctor_check(
    check_id: str,
    label: str,
    status: str,
    message: str,
    details: dict | None = None,
    output: str = "",
) -> dict:
    return {
        "id": check_id,
        "label": label,
        "status": status,
        "message": message,
        "details": details or {},
        "output": output,
    }


def run_doctor_callable_check(check_id: str, label: str, callback, *args) -> dict:
    output_buffer = io.StringIO()
    try:
        with redirect_stdout(output_buffer):
            callback(*args)
    except NativeRuntimeError as error:
        return build_doctor_check(check_id, label, "fail", str(error), output=output_buffer.getvalue().strip())
    except Exception as error:
        return build_doctor_check(
            check_id,
            label,
            "fail",
            f"{type(error).__name__}: {error}",
            output=output_buffer.getvalue().strip(),
        )
    return build_doctor_check(check_id, label, "pass", "通过", output=output_buffer.getvalue().strip())


def run_doctor_with_temporary_home(callback):
    original_home = os.environ.get("HOME")
    original_userprofile = os.environ.get("USERPROFILE")
    with tempfile.TemporaryDirectory(prefix="canvasia-native-doctor-") as temp_dir:
        temp_home = Path(temp_dir) / "home"
        temp_home.mkdir(parents=True, exist_ok=True)
        os.environ["HOME"] = str(temp_home)
        os.environ["USERPROFILE"] = str(temp_home)
        try:
            return callback()
        finally:
            if original_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = original_home
            if original_userprofile is None:
                os.environ.pop("USERPROFILE", None)
            else:
                os.environ["USERPROFILE"] = original_userprofile


def build_release_check_doctor_check(bundle_dir: Path) -> dict:
    report = build_release_check_report(bundle_dir)
    report_status = str(report.get("status") or "fail")
    summary = report.get("summary") or {}
    if report_status == "pass":
        status = "pass"
        message = "发布前自检通过。"
    elif report_status == "warn":
        status = "warn"
        message = f"发布前自检有 {summary.get('warnings', 0)} 条警告。"
    else:
        status = "fail"
        message = f"发布前自检有 {summary.get('errors', 0)} 个错误。"
    return build_doctor_check("release_check", "发布前自检", status, message, details=report)


def build_vn_baseline_quality_doctor_check(bundle_dir: Path) -> dict:
    report = build_native_runtime_vn_baseline_quality_report(bundle_dir)
    report_status = str(report.get("status") or "needs_fix")
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    if report_status == "ready":
        status = "pass"
        message = "视觉小说基础质感通过。"
    elif report_status == "needs_polish":
        status = "warn"
        message = f"视觉小说基础质感还有 {summary.get('softCount', 0)} 个润色项。"
    else:
        status = "fail"
        message = f"视觉小说基础质感还有 {summary.get('warnCount', 0)} 个需要修复的问题。"
    return build_doctor_check("vn_baseline_quality", "VN 基础质感", status, message, details=report)


def build_report_doctor_check(check_id: str, label: str, report_builder, bundle_dir: Path) -> dict:
    try:
        report = report_builder(bundle_dir)
    except NativeRuntimeError as error:
        return build_doctor_check(check_id, label, "fail", str(error))
    except Exception as error:
        return build_doctor_check(check_id, label, "fail", f"{type(error).__name__}: {error}")
    return build_doctor_check(check_id, label, "pass", "通过", details=report)


def build_video_bridge_doctor_check(bundle_dir: Path) -> dict:
    report = build_native_video_bridge_report(bundle_dir)
    report_status = str(report.get("status") or "")
    summary = report.get("summary") or {}
    if report_status == "needs_system_opener":
        return build_doctor_check(
            "video_bridge",
            "视频播放器桥接",
            "warn",
            "导出包包含视频，但当前系统没有检测到默认视频打开器。",
            details=report,
        )
    if report_status == "no_video":
        return build_doctor_check("video_bridge", "视频播放器桥接", "pass", "没有视频素材，跳过桥接风险。", details=report)
    return build_doctor_check(
        "video_bridge",
        "视频播放器桥接",
        "pass",
        f"检测到 {summary.get('videoAssetCount', 0)} 个视频素材，系统播放器桥接可用。",
        details=report,
    )


def build_video_preview_doctor_check(bundle_dir: Path) -> dict:
    report = build_native_video_preview_probe_report(bundle_dir)
    report_status = str(report.get("status") or "")
    if report_status in {"ready", "no_video", "optional_dependency_missing"}:
        status = "pass"
    elif report_status in {"partial", "pygame_missing", "all_failed"}:
        status = "warn"
    else:
        status = "fail"
    return build_doctor_check(
        "video_preview_probe",
        "视频内嵌画面探针",
        status,
        str(report.get("recommendation") or "视频内嵌画面探针完成。"),
        details=report,
    )


def build_model_preview_doctor_check(bundle_dir: Path) -> dict:
    report = build_native_character_model_preview_report(bundle_dir)
    report_status = str(report.get("status") or "")
    summary = report.get("summary") or {}
    if report_status == "no_advanced_models":
        return build_doctor_check(
            "model_preview_bridge",
            "Live2D/3D 预览桥",
            "pass",
            "当前项目没有高级模型角色，跳过模型预览桥风险。",
            details=report,
        )
    if report_status == "ready":
        return build_doctor_check(
            "model_preview_bridge",
            "Live2D/3D 预览桥",
            "pass",
            f"{summary.get('readyCount', 0)} 个高级模型角色资源完整。",
            details=report,
        )
    return build_doctor_check(
        "model_preview_bridge",
        "Live2D/3D 预览桥",
        "warn",
        f"高级模型角色还有 {summary.get('assetIssueCount', 0)} 个资源问题 / {summary.get('mappingGapCount', 0)} 个映射缺口。",
        details=report,
    )


def build_scene3d_preview_doctor_check(bundle_dir: Path) -> dict:
    report = build_native_scene3d_preview_report(bundle_dir)
    report_status = str(report.get("status") or "")
    summary = report.get("summary") or {}
    if report_status == "no_scene3d":
        return build_doctor_check(
            "scene3d_preview_bridge",
            "3D 场景预览桥",
            "pass",
            "当前项目没有 3D 场景资产，跳过空间预览桥风险。",
            details=report,
        )
    if report_status == "ready":
        return build_doctor_check(
            "scene3d_preview_bridge",
            "3D 场景预览桥",
            "pass",
            f"{summary.get('readyCount', 0)} 个 3D 场景资源完整。",
            details=report,
        )
    return build_doctor_check(
        "scene3d_preview_bridge",
        "3D 场景预览桥",
        "warn",
        f"3D 场景还有 {summary.get('assetIssueCount', 0)} 个资源问题。",
        details=report,
    )


def build_3d_asset_doctor_check(bundle_dir: Path) -> dict:
    report = build_native_3d_asset_report(bundle_dir)
    report_status = str(report.get("status") or "")
    summary = report.get("summary") or {}
    if report_status == "no_3d_assets":
        return build_doctor_check(
            "asset3d_report",
            "3D 资产清单",
            "pass",
            "当前项目没有 3D 模型或 3D 场景资产，跳过 3D 资产风险。",
            details=report,
        )
    if report_status == "ready":
        return build_doctor_check(
            "asset3d_report",
            "3D 资产清单",
            "pass",
            f"{summary.get('readyCount', 0)} 个 3D 资产结构和依赖完整。",
            details=report,
        )
    return build_doctor_check(
        "asset3d_report",
        "3D 资产清单",
        "warn",
        f"{summary.get('issueCount', 0)} 个 3D 资产需要处理，缺失/不安全依赖 {summary.get('missingDependencyCount', 0)} 项。",
        details=report,
    )


def build_native_runtime_doctor_report(bundle_dir: Path) -> dict:
    checks: list[dict] = []
    checks.append(run_doctor_callable_check("bundle_structure", "导出包结构", validate_bundle, bundle_dir))
    checks.append(build_release_check_doctor_check(bundle_dir))
    checks.append(build_vn_baseline_quality_doctor_check(bundle_dir))
    checks.append(
        run_doctor_with_temporary_home(
            lambda: build_report_doctor_check("title_screen", "标题页摘要", build_native_title_screen_report, bundle_dir)
        )
    )
    checks.append(
        run_doctor_with_temporary_home(
            lambda: build_report_doctor_check("save_dialog", "正式存档面板", build_save_dialog_page_data_for_doctor, bundle_dir)
        )
    )

    def run_stateful_checks() -> list[dict]:
        return [
            run_doctor_callable_check("save_load", "存档读写", exercise_save_load, bundle_dir),
            run_doctor_callable_check("settings", "系统设置读写", exercise_runtime_settings, bundle_dir),
            run_doctor_callable_check("archives", "资料馆进度", exercise_archive_progress, bundle_dir),
            run_doctor_callable_check("profile", "玩家档案/自动续玩", exercise_player_profile, bundle_dir),
        ]

    checks.extend(run_doctor_with_temporary_home(run_stateful_checks))
    checks.append(run_doctor_callable_check("particles", "粒子配置", exercise_particle_effect, bundle_dir))
    checks.append(run_doctor_callable_check("visual_effects", "高级演出配置", exercise_visual_effects, bundle_dir))
    checks.append(build_3d_asset_doctor_check(bundle_dir))
    checks.append(build_model_preview_doctor_check(bundle_dir))
    checks.append(build_scene3d_preview_doctor_check(bundle_dir))
    checks.append(build_video_bridge_doctor_check(bundle_dir))
    checks.append(build_report_doctor_check("video_backends", "视频后端能力", build_native_video_backend_report, bundle_dir))
    checks.append(build_video_preview_doctor_check(bundle_dir))

    status = get_doctor_status(checks)
    return {
        "status": status,
        "checkedAt": now_iso(),
        "bundleDir": str(bundle_dir),
        "summary": build_doctor_summary(checks),
        "checks": checks,
    }


def get_release_candidate_platform_tag() -> str:
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform.startswith("linux"):
        return "linux"
    return re.sub(r"[^a-z0-9]+", "-", sys.platform.lower()).strip("-") or "unknown"


def first_existing_bundle_file(bundle_dir: Path, candidates: list[str]) -> str:
    for candidate in candidates:
        if (bundle_dir / candidate).exists():
            return candidate
    return ""


def get_release_candidate_packaging_matrix(bundle_dir: Path) -> list[dict]:
    builder_script = first_existing_bundle_file(bundle_dir, ["build_native_runtime_app.py"])
    runtime_requirements = first_existing_bundle_file(bundle_dir, ["requirements-native-runtime.txt", "requirements.txt"])
    build_requirements = first_existing_bundle_file(bundle_dir, ["requirements-native-runtime-build.txt", "requirements-build.txt"])
    current_platform = get_release_candidate_platform_tag()
    platforms = [
        {
            "id": "macos",
            "label": "macOS",
            "buildScript": first_existing_bundle_file(bundle_dir, ["打包原生Runtime应用.command"]),
            "output": ".app / Preview zip",
            "releaseRequirement": "Developer ID 签名与 notarization",
        },
        {
            "id": "windows",
            "label": "Windows",
            "buildScript": first_existing_bundle_file(bundle_dir, ["build_native_runtime_app.bat"]),
            "output": ".exe 或 onedir / Preview zip",
            "releaseRequirement": "代码签名证书与 SmartScreen 实机验证",
        },
        {
            "id": "linux",
            "label": "Linux",
            "buildScript": first_existing_bundle_file(bundle_dir, ["build_native_runtime_app.sh"]),
            "output": "可执行目录 / Preview zip",
            "releaseRequirement": "目标发行版点测；可继续封装 AppImage、deb/rpm 或 Flatpak",
        },
    ]
    return [
        {
            **platform_entry,
            "currentMachine": platform_entry["id"] == current_platform,
            "pyInstallerBuilderAvailable": bool(builder_script and build_requirements),
            "runtimeRequirements": runtime_requirements,
            "buildRequirements": build_requirements,
            "canAttemptLocalBuild": platform_entry["id"] == current_platform and bool(builder_script and build_requirements),
            "status": (
                "ready_to_build_here"
                if platform_entry["id"] == current_platform and builder_script and build_requirements
                else "build_on_target_platform"
                if builder_script and build_requirements
                else "missing_packaging_files"
            ),
        }
        for platform_entry in platforms
    ]


def build_release_candidate_gate(
    gate_id: str,
    label: str,
    status: str,
    required_for_preview: bool,
    message: str,
    source_check_id: str = "",
) -> dict:
    return {
        "id": gate_id,
        "label": label,
        "status": status,
        "requiredForPreview": required_for_preview,
        "message": message,
        "sourceCheckId": source_check_id,
    }


def build_release_candidate_gates(doctor_report: dict, packaging_matrix: list[dict]) -> list[dict]:
    required_check_ids = {
        "bundle_structure",
        "release_check",
        "title_screen",
        "save_dialog",
        "save_load",
        "settings",
        "archives",
        "profile",
    }
    gates = []
    for check in doctor_report.get("checks", []) or []:
        check_id = str(check.get("id") or "")
        required = check_id in required_check_ids
        gates.append(
            build_release_candidate_gate(
                gate_id=f"doctor_{check_id}",
                label=str(check.get("label") or check_id),
                status=str(check.get("status") or "fail"),
                required_for_preview=required,
                message=str(check.get("message") or ""),
                source_check_id=check_id,
            )
        )

    packaging_ready = all(entry.get("pyInstallerBuilderAvailable") for entry in packaging_matrix)
    gates.append(
        build_release_candidate_gate(
            gate_id="packaging_scaffold",
            label="PyInstaller 打包脚手架",
            status="pass" if packaging_ready else "fail",
            required_for_preview=True,
            message="三平台打包脚本和构建依赖文件已随包提供。" if packaging_ready else "导出包缺少打包脚手架或构建依赖文件。",
        )
    )
    return gates


def get_release_candidate_status(gates: list[dict]) -> str:
    if any(gate.get("status") == "fail" and gate.get("requiredForPreview") for gate in gates):
        return "blocked"
    if any(gate.get("status") == "fail" for gate in gates):
        return "preview_ready_with_optional_failures"
    if any(gate.get("status") == "warn" for gate in gates):
        return "preview_ready_with_warnings"
    return "preview_ready"


def get_release_candidate_next_actions(status: str, gates: list[dict], packaging_matrix: list[dict]) -> list[str]:
    blockers = [gate for gate in gates if gate.get("status") == "fail" and gate.get("requiredForPreview")]
    warnings = [gate for gate in gates if gate.get("status") == "warn"]
    if blockers:
        return [
            f"先修复阻塞项：{gate.get('label')} - {gate.get('message')}"
            for gate in blockers[:6]
        ]
    actions = []
    if warnings:
        actions.append(f"处理 {len(warnings)} 条 Preview 警告，重点看发布前自检、视频后端和目标系统兼容性。")
    target_platforms = [entry["label"] for entry in packaging_matrix if not entry.get("currentMachine")]
    if target_platforms:
        actions.append(f"在目标系统分别运行打包脚本并点测：{', '.join(target_platforms)}。")
    actions.append("正式公开分发前补齐 macOS 签名/公证、Windows 代码签名和杀毒/SmartScreen 实机验证。")
    actions.append("对 OP / ED / PV 做目标平台编码矩阵测试，确认音画同步、跳过和结束回到剧情链都稳定。")
    if status == "preview_ready":
        actions.insert(0, "当前导出包可作为桌面 Preview Release Candidate 继续进入三系统实机打包。")
    return actions


def build_native_runtime_release_candidate_report(bundle_dir: Path) -> dict:
    doctor_report = build_native_runtime_doctor_report(bundle_dir)
    release_check = next(
        (
            check.get("details")
            for check in doctor_report.get("checks", []) or []
            if check.get("id") == "release_check" and isinstance(check.get("details"), dict)
        ),
        {},
    )
    video_backend_report = next(
        (
            check.get("details")
            for check in doctor_report.get("checks", []) or []
            if check.get("id") == "video_backends" and isinstance(check.get("details"), dict)
        ),
        {},
    )
    video_probe_report = next(
        (
            check.get("details")
            for check in doctor_report.get("checks", []) or []
            if check.get("id") == "video_preview_probe" and isinstance(check.get("details"), dict)
        ),
        {},
    )
    asset3d_report = next(
        (
            check.get("details")
            for check in doctor_report.get("checks", []) or []
            if check.get("id") == "asset3d_report" and isinstance(check.get("details"), dict)
        ),
        {},
    )
    packaging_matrix = get_release_candidate_packaging_matrix(bundle_dir)
    gates = build_release_candidate_gates(doctor_report, packaging_matrix)
    status = get_release_candidate_status(gates)
    blockers = [gate for gate in gates if gate.get("status") == "fail" and gate.get("requiredForPreview")]
    optional_failures = [gate for gate in gates if gate.get("status") == "fail" and not gate.get("requiredForPreview")]
    warnings = [gate for gate in gates if gate.get("status") == "warn"]
    desktop_preview_percent = 80 if status.startswith("preview_ready") else 62
    commercial_desktop_percent = 62 if status.startswith("preview_ready") else 48
    mobile_percent = 15
    return {
        "status": status,
        "checkedAt": now_iso(),
        "bundleDir": str(bundle_dir),
        "projectTitle": release_check.get("projectTitle") or "",
        "summary": {
            "blockers": len(blockers),
            "optionalFailures": len(optional_failures),
            "warnings": len(warnings),
            "doctorStatus": doctor_report.get("status"),
            "doctorSummary": doctor_report.get("summary"),
            "releaseCheckStatus": release_check.get("status"),
            "releaseCheckSummary": release_check.get("summary"),
            "asset3dStatus": asset3d_report.get("status"),
            "asset3dSummary": asset3d_report.get("summary"),
            "videoBackendStatus": video_backend_report.get("status"),
            "videoPreviewProbeStatus": video_probe_report.get("status"),
        },
        "readinessEstimate": {
            "desktopPreviewPercent": desktop_preview_percent,
            "commercialDesktopPercent": commercial_desktop_percent,
            "mobileRuntimePercent": mobile_percent,
            "note": "估算基于当前导出包自检、打包脚手架和桌面/商业/手机端剩余工作量；不是性能评分。",
        },
        "gates": gates,
        "platformMatrix": packaging_matrix,
        "videoStrategy": {
            "backendStatus": video_backend_report.get("status"),
            "previewProbeStatus": video_probe_report.get("status"),
            "recommendation": video_backend_report.get("recommendation") or video_probe_report.get("recommendation") or "",
        },
        "asset3dStrategy": {
            "status": asset3d_report.get("status"),
            "summary": asset3d_report.get("summary") or {},
            "recommendations": asset3d_report.get("recommendations") or [],
        },
        "commercialReleaseGaps": [
            "macOS Developer ID 签名、notarization 和 Gatekeeper 实机验证",
            "Windows 代码签名、SmartScreen/杀毒误报验证和安装器链路",
            "Linux 目标发行版点测，以及 AppImage/deb/rpm/Flatpak 等发行形态选择",
            "OP/ED/PV 视频编码矩阵与音画同步长流程测试",
            "完整人工逐按钮长流程点测、崩溃日志可读性和升级覆盖安装验证",
        ],
        "nextActions": get_release_candidate_next_actions(status, gates, packaging_matrix),
    }


def print_native_runtime_release_candidate_report(bundle_dir: Path) -> dict:
    report = build_native_runtime_release_candidate_report(bundle_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def format_release_control_number(value: object) -> str:
    try:
        number = int(value or 0)
    except (TypeError, ValueError):
        number = 0
    return f"{number:,}"


def build_native_runtime_3d_risk_digest(report: dict | None) -> dict:
    if not isinstance(report, dict):
        return {
            "status": "unavailable",
            "headline": "3D 资产清单暂不可用",
            "summaryLine": "没有拿到可读 3D 报告。",
            "metrics": [],
            "riskCounts": {},
            "issueAssetIds": [],
            "issueAssets": [],
            "topIssues": [],
            "recommendations": ["手动运行 --describe-3d-assets 查看具体问题。"],
        }

    status = str(report.get("status") or "unavailable")
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    entries = report.get("entries") if isinstance(report.get("entries"), list) else []
    recommendations = report.get("recommendations") if isinstance(report.get("recommendations"), list) else []
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
    summary_line = f"资产 {int(summary.get('assetCount') or 0)} 个，问题 {int(summary.get('issueCount') or 0)} 个；{risk_preview}。"

    issue_assets: list[dict] = []
    for entry in entries:
        if not isinstance(entry, dict) or str(entry.get("status") or "") == "ready":
            continue
        issue_breakdown: list[dict] = []
        for code, label, probe_name in [
            ("performance_budget", "性能预算", "performanceBudgetProbe"),
            ("glb_container", "GLB/VRM 容器", "glbContainerProbe"),
            ("gltf_integrity", "内部引用", "gltfIntegrityProbe"),
            ("texture_slot", "贴图槽", "previewProbe"),
        ]:
            probe = entry.get(probe_name) if isinstance(entry.get(probe_name), dict) else {}
            raw_count = probe.get("textureSlotIssueCount") if code == "texture_slot" else probe.get("issueCount")
            count = int(raw_count or 0)
            if count:
                issue_breakdown.append({"code": code, "label": label, "count": count})
        dependency = entry.get("dependencyHealth") if isinstance(entry.get("dependencyHealth"), dict) else {}
        dependency_count = len(dependency.get("missing") or []) + len(dependency.get("unsafe") or [])
        if dependency_count:
            issue_breakdown.append({"code": "dependency", "label": "外部依赖", "count": dependency_count})
        if not issue_breakdown:
            issue_breakdown.append({"code": "status", "label": str(entry.get("statusLabel") or "需要复核"), "count": 1})

        usage_preview: list[str] = []
        for usage in (entry.get("usages") if isinstance(entry.get("usages"), list) else [])[:3]:
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
                "name": str(entry.get("name") or entry.get("assetId") or "未命名 3D 资产"),
                "typeLabel": str(entry.get("typeLabel") or "3D 资产"),
                "exportUrl": str(entry.get("exportUrl") or ""),
                "status": str(entry.get("status") or ""),
                "statusLabel": str(entry.get("statusLabel") or "需要复核"),
                "summary": " / ".join(f"{item['label']} {item['count']} 项" for item in issue_breakdown),
                "issueCount": sum(int(item.get("count") or 0) for item in issue_breakdown),
                "issueBreakdown": issue_breakdown,
                "usageCount": int(entry.get("usageCount") or 0),
                "usagePreview": usage_preview,
                "recommendedAction": str(entry.get("recommendedAction") or "复核 3D 资产导入状态。"),
            }
        )

    issue_asset_ids: list[str] = []
    seen_ids: set[str] = set()
    for issue in issue_assets:
        asset_id = str(issue.get("assetId") or "").strip()
        if asset_id and asset_id not in seen_ids:
            seen_ids.add(asset_id)
            issue_asset_ids.append(asset_id)

    return {
        "status": status,
        "headline": headline,
        "summaryLine": summary_line,
        "metrics": [
            {"label": "3D 资产", "value": f"{int(summary.get('assetCount') or 0)} 个"},
            {"label": "问题", "value": f"{int(summary.get('issueCount') or 0)} 个"},
            {"label": "性能预算", "value": f"{int(summary.get('performanceBudgetIssueCount') or 0)} 项"},
            {"label": "估算三角面", "value": format_release_control_number(summary.get("estimatedTriangleCount"))},
            {"label": "Draw Call", "value": format_release_control_number(summary.get("drawCallCount"))},
            {"label": "未使用", "value": f"{int(summary.get('unusedCount') or 0)} 个"},
        ],
        "riskCounts": risk_counts,
        "issueAssetIds": issue_asset_ids[:50],
        "issueAssets": issue_assets[:50],
        "topIssues": issue_assets[:5],
        "recommendations": [str(recommendation) for recommendation in recommendations[:4]],
    }


VN_BASELINE_EFFECT_BLOCK_TYPES = {
    "particle_effect",
    "screen_shake",
    "screen_flash",
    "screen_fade",
    "camera_zoom",
    "camera_pan",
    "screen_filter",
    "depth_blur",
}


def get_vn_baseline_character_sprite_asset_id(character: dict) -> str:
    presentation = character.get("presentation") if isinstance(character.get("presentation"), dict) else {}
    for key in ("fallbackSpriteAssetId", "defaultSpriteId", "spriteAssetId"):
        asset_id = str(presentation.get(key) or character.get(key) or "").strip()
        if asset_id:
            return asset_id
    expressions = character.get("expressions") if isinstance(character.get("expressions"), list) else []
    for expression in expressions:
        if isinstance(expression, dict):
            asset_id = str(expression.get("spriteAssetId") or "").strip()
            if asset_id:
                return asset_id
    return ""


def is_vn_baseline_placeholder_asset(asset: dict) -> bool:
    tags = asset.get("tags") if isinstance(asset.get("tags"), list) else []
    text = " ".join(str(value or "") for value in [asset.get("name"), asset.get("description"), *tags]).lower()
    return "占位素材" in text or "placeholder" in text


def get_vn_baseline_block_text(block: dict) -> str:
    block_type = str(block.get("type") or "").strip()
    if block_type in {"dialogue", "narration"}:
        return str(block.get("text") or "").strip()
    if block_type == "choice":
        options = block.get("options") if isinstance(block.get("options"), list) else []
        return " ".join(str(option.get("text") or "").strip() for option in options if isinstance(option, dict)).strip()
    return ""


def add_vn_baseline_issue(
    issues: list[dict],
    severity: str,
    code: str,
    title: str,
    detail: str,
    suggestion: str,
) -> None:
    issues.append(
        {
            "severity": severity,
            "code": code,
            "title": title,
            "detail": detail,
            "suggestion": suggestion,
        }
    )


def build_native_runtime_vn_baseline_quality_report(bundle_dir: Path) -> dict:
    payload = load_game_data(bundle_dir / DEFAULT_GAME_DATA_NAME)
    project = payload.get("project") if isinstance(payload.get("project"), dict) else {}
    assets_doc = payload.get("assets") if isinstance(payload.get("assets"), dict) else {}
    assets = assets_doc.get("assets") if isinstance(assets_doc.get("assets"), list) else []
    assets_by_id = {str(asset.get("id")): asset for asset in assets if isinstance(asset, dict) and asset.get("id")}
    video_asset_count = sum(1 for asset in assets if isinstance(asset, dict) and asset.get("type") == "video")
    characters_doc = payload.get("characters") if isinstance(payload.get("characters"), dict) else {}
    characters = characters_doc.get("characters") if isinstance(characters_doc.get("characters"), list) else []
    chapters = payload.get("chapters") if isinstance(payload.get("chapters"), list) else []
    scenes = iter_export_scenes(chapters)
    scene_ids = [str(scene.get("id") or "").strip() for scene in scenes if isinstance(scene, dict)]
    valid_scene_ids = {scene_id for scene_id in scene_ids if scene_id}
    entry_scene_id = str(project.get("entrySceneId") or "").strip()

    dialogue_count = 0
    narration_count = 0
    choice_count = 0
    empty_text_count = 0
    character_show_count = 0
    character_hide_count = 0
    character_transition_count = 0
    character_position_values: set[str] = set()
    character_stage_adjustment_count = 0
    scenes_with_background = 0
    background_block_count = 0
    background_transition_count = 0
    background_asset_ids: set[str] = set()
    missing_background_asset_count = 0
    missing_background_asset_names: list[str] = []
    scenes_with_music = 0
    scenes_with_effects = 0
    choice_option_count = 0
    empty_choice_option_count = 0
    long_choice_option_count = 0
    duplicate_choice_option_count = 0
    crowded_choice_block_count = 0
    sfx_play_count = 0
    missing_sfx_asset_count = 0
    missing_sfx_asset_names: list[str] = []
    video_play_count = 0
    missing_video_asset_count = 0
    missing_video_asset_names: list[str] = []
    credits_roll_count = 0
    credits_line_count = 0
    empty_credits_roll_count = 0
    short_credits_roll_count = 0
    short_credits_roll_names: list[str] = []
    music_play_count = 0
    music_stop_count = 0
    music_scoped_count = 0
    music_fade_in_count = 0
    music_fade_out_count = 0
    dialogue_voice_count = 0
    narration_voice_count = 0
    missing_voice_asset_count = 0
    missing_voice_asset_names: list[str] = []
    text_block_count = 0
    total_text_chars = 0

    for scene in scenes:
        blocks = scene.get("blocks") if isinstance(scene.get("blocks"), list) else []
        scene_has_background = False
        scene_has_music = False
        scene_has_effect = False
        for block in blocks:
            if not isinstance(block, dict):
                continue
            block_type = str(block.get("type") or "").strip()
            if block_type == "dialogue":
                dialogue_count += 1
                voice_asset_id = str(block.get("voiceAssetId") or "").strip()
                if voice_asset_id:
                    dialogue_voice_count += 1
                    voice_asset = assets_by_id.get(voice_asset_id)
                    if not voice_asset or not get_asset_runtime_path(bundle_dir, voice_asset):
                        missing_voice_asset_count += 1
                        missing_voice_asset_names.append(str(block.get("id") or voice_asset_id))
            elif block_type == "narration":
                narration_count += 1
                voice_asset_id = str(block.get("voiceAssetId") or "").strip()
                if voice_asset_id:
                    narration_voice_count += 1
                    voice_asset = assets_by_id.get(voice_asset_id)
                    if not voice_asset or not get_asset_runtime_path(bundle_dir, voice_asset):
                        missing_voice_asset_count += 1
                        missing_voice_asset_names.append(str(block.get("id") or voice_asset_id))
            elif block_type == "choice":
                choice_count += 1
                options = block.get("options") if isinstance(block.get("options"), list) else []
                choice_option_count += len(options)
                if len(options) > 4:
                    crowded_choice_block_count += 1
                seen_choice_texts: set[str] = set()
                for option in options:
                    if not isinstance(option, dict):
                        continue
                    option_text = str(option.get("text") or "").strip()
                    normalized_option_text = option_text.lower()
                    if not option_text:
                        empty_choice_option_count += 1
                    elif len(option_text) > 42:
                        long_choice_option_count += 1
                    if normalized_option_text:
                        if normalized_option_text in seen_choice_texts:
                            duplicate_choice_option_count += 1
                        seen_choice_texts.add(normalized_option_text)
            elif block_type == "character_show":
                character_show_count += 1
                character_position_values.add(str(block.get("position") or "center").strip() or "center")
                if get_safe_character_transition(block.get("transition")) != "none" and get_safe_transition_duration_ms(block.get("transitionDurationMs"), 600) > 0:
                    character_transition_count += 1
                stage = get_safe_character_stage(block.get("stage") if isinstance(block.get("stage"), dict) else None)
                if (
                    stage.get("offsetX") != 0
                    or stage.get("offsetY") != 0
                    or stage.get("scale") != 100
                    or stage.get("opacity") != 100
                    or stage.get("layer") != 0
                    or stage.get("flipX")
                ):
                    character_stage_adjustment_count += 1
            elif block_type == "character_hide":
                character_hide_count += 1
                if get_safe_character_transition(block.get("transition")) != "none" and get_safe_transition_duration_ms(block.get("transitionDurationMs"), 600) > 0:
                    character_transition_count += 1
            elif block_type == "background":
                scene_has_background = True
                background_block_count += 1
                background_asset_id = str(block.get("assetId") or "").strip()
                if background_asset_id:
                    background_asset_ids.add(background_asset_id)
                background_asset = assets_by_id.get(background_asset_id) if background_asset_id else None
                if not background_asset or not get_asset_runtime_path(bundle_dir, background_asset):
                    missing_background_asset_count += 1
                    missing_background_asset_names.append(str(block.get("id") or background_asset_id or "未命名背景卡"))
                if get_safe_basic_transition(block.get("transition")) != "none" and get_safe_transition_duration_ms(block.get("transitionDurationMs"), 600) > 0:
                    background_transition_count += 1
            elif block_type == "music_play":
                scene_has_music = True
                music_play_count += 1
                if get_safe_audio_fade_ms(block.get("fadeInMs"), 0) > 0:
                    music_fade_in_count += 1
                if get_safe_audio_fade_ms(block.get("fadeOutMs"), 0) > 0:
                    music_fade_out_count += 1
                if get_safe_music_end_mode(block.get("endMode")) != "until_next_music":
                    music_scoped_count += 1
            elif block_type == "music_stop":
                music_stop_count += 1
                if get_safe_audio_fade_ms(block.get("fadeOutMs"), 0) > 0:
                    music_fade_out_count += 1
            elif block_type == "sfx_play":
                sfx_play_count += 1
                sfx_asset_id = str(block.get("assetId") or "").strip()
                sfx_asset = assets_by_id.get(sfx_asset_id) if sfx_asset_id else None
                if not sfx_asset or not get_asset_runtime_path(bundle_dir, sfx_asset):
                    missing_sfx_asset_count += 1
                    missing_sfx_asset_names.append(str(block.get("id") or sfx_asset_id or "未命名音效卡"))
            elif block_type == "video_play":
                video_play_count += 1
                video_asset_id = str(block.get("assetId") or "").strip()
                video_asset = assets_by_id.get(video_asset_id) if video_asset_id else None
                if not video_asset or not get_asset_runtime_path(bundle_dir, video_asset):
                    missing_video_asset_count += 1
                    missing_video_asset_names.append(str(block.get("id") or video_asset_id or "未命名视频卡"))
            elif block_type == "credits_roll":
                credits_roll_count += 1
                lines = block.get("lines") if isinstance(block.get("lines"), list) else []
                non_empty_lines = [str(line).strip() for line in lines if str(line).strip()]
                credits_line_count += len(non_empty_lines)
                if not str(block.get("title") or "").strip() and not str(block.get("subtitle") or "").strip() and not non_empty_lines:
                    empty_credits_roll_count += 1
                try:
                    credits_duration_seconds = float(block.get("durationSeconds") or 0)
                except (TypeError, ValueError):
                    credits_duration_seconds = 0.0
                if credits_duration_seconds < 4:
                    short_credits_roll_count += 1
                    short_credits_roll_names.append(str(block.get("id") or block.get("title") or "未命名片尾字幕"))
            elif block_type in VN_BASELINE_EFFECT_BLOCK_TYPES:
                scene_has_effect = True
            text = get_vn_baseline_block_text(block)
            if block_type in {"dialogue", "narration", "choice"}:
                text_block_count += 1
                total_text_chars += len(text)
                if not text:
                    empty_text_count += 1
        if scene_has_background:
            scenes_with_background += 1
        if scene_has_music:
            scenes_with_music += 1
        if scene_has_effect:
            scenes_with_effects += 1

    characters_with_sprite = 0
    characters_missing_sprite = []
    for character in characters:
        if not isinstance(character, dict):
            continue
        asset_id = get_vn_baseline_character_sprite_asset_id(character)
        asset = assets_by_id.get(asset_id) if asset_id else None
        if asset_id and asset and get_asset_runtime_path(bundle_dir, asset):
            characters_with_sprite += 1
        else:
            characters_missing_sprite.append(str(character.get("displayName") or character.get("name") or character.get("id") or "未命名角色"))

    placeholder_assets = [
        str(asset.get("name") or asset.get("id") or "未命名素材")
        for asset in assets
        if isinstance(asset, dict) and is_vn_baseline_placeholder_asset(asset)
    ]
    scene_count = len(scenes)
    text_density = round(text_block_count / scene_count, 2) if scene_count else 0.0
    average_text_length = round(total_text_chars / text_block_count, 1) if text_block_count else 0.0
    voice_eligible_line_count = dialogue_count + narration_count
    voice_bound_line_count = dialogue_voice_count + narration_voice_count
    voice_coverage_percent = round(voice_bound_line_count / voice_eligible_line_count * 100, 1) if voice_eligible_line_count else 0.0
    missing_route_targets: list[str] = []
    scene_outgoing_targets: dict[str, list[str]] = {}
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        scene_id = str(scene.get("id") or "").strip()
        if not scene_id:
            continue
        targets = collect_scene_outgoing_targets(scene)
        scene_outgoing_targets[scene_id] = targets
        for target in targets:
            if target not in valid_scene_ids:
                missing_route_targets.append(f"{scene_id}->{target}")
    reachable_scene_ids: set[str] = set()
    if entry_scene_id in valid_scene_ids:
        pending_scene_ids = [entry_scene_id]
        while pending_scene_ids:
            scene_id = pending_scene_ids.pop(0)
            if scene_id in reachable_scene_ids:
                continue
            reachable_scene_ids.add(scene_id)
            for target in scene_outgoing_targets.get(scene_id, []):
                if target in valid_scene_ids and target not in reachable_scene_ids:
                    pending_scene_ids.append(target)
    unreachable_scene_ids = sorted(valid_scene_ids - reachable_scene_ids) if reachable_scene_ids else []
    ending_scene_count = len(build_ending_scene_ids(chapters))
    issues: list[dict] = []

    if not scenes:
        add_vn_baseline_issue(
            issues,
            "warn",
            "no_story_scene",
            "没有可试玩场景",
            "导出包里没有检测到章节场景。",
            "至少创建一个章节和入口场景，再重新导出原生 Runtime 包。",
        )
    elif entry_scene_id not in valid_scene_ids:
        add_vn_baseline_issue(
            issues,
            "warn",
            "entry_scene_missing",
            "入口场景不可用",
            f"项目入口场景指向 {entry_scene_id or '空值'}，但导出包里没有这个场景。",
            "在项目设置里重新指定存在的入口场景，避免玩家启动原生 Runtime 后直接掉到异常或错误章节。",
        )
    if missing_route_targets:
        add_vn_baseline_issue(
            issues,
            "warn",
            "route_target_missing",
            "路线跳转目标缺失",
            f"检测到 {len(missing_route_targets)} 个跳转目标不存在：{', '.join(missing_route_targets[:3])}",
            "检查选项、条件分支和跳转卡片，确保每个目标场景都存在；删除场景后尤其要重新巡检路线。",
        )
    if unreachable_scene_ids:
        add_vn_baseline_issue(
            issues,
            "soft",
            "unreachable_scene",
            "存在入口无法到达的场景",
            f"从入口场景出发，有 {len(unreachable_scene_ids)} 个场景没有被路线连接：{', '.join(unreachable_scene_ids[:3])}",
            "如果这些是正式内容，请用选项、跳转或条件分支接入；如果只是素材草稿，建议标记或移出发布章节。",
        )
    if placeholder_assets:
        add_vn_baseline_issue(
            issues,
            "warn",
            "placeholder_assets",
            "仍有占位素材",
            f"检测到 {len(placeholder_assets)} 个疑似占位素材：{', '.join(placeholder_assets[:3])}",
            "发布前替换占位图、占位音频或临时 UI，避免玩家打开后误以为是半成品。",
        )
    if empty_text_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "empty_story_text",
            "存在空白剧情文本",
            f"检测到 {empty_text_count} 个台词、旁白或选项没有正文。",
            "回到剧情编辑器补齐文本，或删除不再需要的空卡片。",
        )
    if missing_voice_asset_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "voice_asset_missing",
            "存在已绑定但缺失的语音文件",
            f"检测到 {missing_voice_asset_count} 条台词/旁白绑定了语音，但文件没有进入原生包：{', '.join(missing_voice_asset_names[:3])}",
            "重新导入或替换缺失语音素材，再导出原生 Runtime，避免玩家点开后听不到应有配音。",
        )
    if missing_background_asset_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "background_asset_missing",
            "存在缺失的背景/CG 文件",
            f"检测到 {missing_background_asset_count} 张背景卡片没有可用文件：{', '.join(missing_background_asset_names[:3])}",
            "重新导入或替换缺失背景、CG 或 3D 场景素材，再导出原生 Runtime，避免试玩中出现黑屏或占位背景。",
        )
    if missing_sfx_asset_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "sfx_asset_missing",
            "存在缺失的音效文件",
            f"检测到 {missing_sfx_asset_count} 张音效卡片没有可用文件：{', '.join(missing_sfx_asset_names[:3])}",
            "重新导入或替换缺失音效素材，再导出原生 Runtime，避免点击、脚步或演出音效静默失效。",
        )
    if missing_video_asset_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "video_asset_missing",
            "存在缺失的视频文件",
            f"检测到 {missing_video_asset_count} 张视频播放卡片没有可用文件：{', '.join(missing_video_asset_names[:3])}",
            "重新导入或替换缺失 OP、ED、PV 或过场视频素材，再导出原生 Runtime，避免玩家点击播放后只看到占位提示。",
        )
    if empty_credits_roll_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "credits_empty",
            "片尾字幕内容为空",
            f"检测到 {empty_credits_roll_count} 张片尾字幕卡片没有标题、副标题或字幕行。",
            "补齐 STAFF、感谢名单或制作信息；如果暂时不需要片尾，请删除空片尾字幕卡片，避免玩家看到空白收尾。",
        )
    if short_credits_roll_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "credits_duration_short",
            "片尾字幕时长过短",
            f"检测到 {short_credits_roll_count} 张片尾字幕低于 4 秒：{', '.join(short_credits_roll_names[:3])}",
            "将片尾字幕时长调到 8-30 秒，确保 STAFF 和感谢信息能被正常读完。",
        )
    if empty_choice_option_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "empty_choice_option",
            "存在空白选项按钮",
            f"检测到 {empty_choice_option_count} 个选项按钮没有文案。",
            "补齐选项文案或删除空选项，避免玩家在原生 Runtime 里看到空白按钮。",
        )
    if characters and characters_with_sprite < len(characters):
        add_vn_baseline_issue(
            issues,
            "warn",
            "character_fallback_sprite",
            "角色缺少可用立绘兜底",
            f"{len(characters) - characters_with_sprite} 个角色没有可用立绘文件：{', '.join(characters_missing_sprite[:3])}",
            "即使使用 Live2D / 3D，也建议给每个角色绑定一张兜底立绘，降低目标机器不支持模型时的翻车风险。",
        )
    if scene_count and scenes_with_background < scene_count:
        add_vn_baseline_issue(
            issues,
            "warn",
            "background_coverage",
            "背景覆盖不完整",
            f"{scene_count - scenes_with_background} 个场景没有背景卡片。",
            "给每个可试玩场景至少放一张背景、CG 或 3D 场景，避免黑屏式试玩体验。",
        )
    if background_block_count >= 2 and len(background_asset_ids) >= 2 and background_transition_count == 0:
        add_vn_baseline_issue(
            issues,
            "soft",
            "background_transition_missing",
            "背景切换缺少基础转场",
            f"检测到 {background_block_count} 张背景卡片、{len(background_asset_ids)} 个背景素材，但没有淡入淡出转场。",
            "给章节开头或场景切换设置 400-1000ms 的淡入淡出，避免背景硬切影响沉浸感。",
        )
    expected_music_scenes = max(1, math.ceil(scene_count * 0.6)) if scene_count else 0
    if scene_count and scenes_with_music < expected_music_scenes:
        add_vn_baseline_issue(
            issues,
            "soft",
            "bgm_plan",
            "BGM 规划偏少",
            f"当前 {scene_count} 个场景里只有 {scenes_with_music} 个场景主动播放 BGM。",
            "为章节开头、转场或情绪段落设置 BGM 范围；短篇也建议至少有一条明确的音乐进入点。",
        )
    if music_play_count >= 2 and music_scoped_count == 0 and music_stop_count == 0:
        add_vn_baseline_issue(
            issues,
            "soft",
            "bgm_scope",
            "多首 BGM 缺少明确范围",
            f"检测到 {music_play_count} 个 BGM 播放点，但没有 scene_end / after_block 范围或停止音乐卡片。",
            "给关键曲目设置结束范围，或在段落末尾补停止音乐卡片，避免音乐覆盖到不该出现的场景。",
        )
    if music_play_count and music_fade_in_count < music_play_count:
        add_vn_baseline_issue(
            issues,
            "soft",
            "bgm_fade_in",
            "部分 BGM 没有淡入",
            f"{music_play_count - music_fade_in_count} 个 BGM 播放点没有设置淡入时间。",
            "给 BGM 播放卡片设置 400-1000ms 的淡入，减少切歌突兀感。",
        )
    if music_stop_count and music_fade_out_count < music_stop_count:
        add_vn_baseline_issue(
            issues,
            "soft",
            "bgm_fade_out",
            "部分 BGM 没有淡出",
            f"{music_stop_count - music_fade_out_count} 个停止音乐卡片没有设置淡出时间。",
            "给停止音乐卡片设置淡出，让场景切换和静音段落更自然。",
        )
    if voice_bound_line_count and voice_eligible_line_count >= 5 and voice_coverage_percent < 70:
        add_vn_baseline_issue(
            issues,
            "soft",
            "voice_coverage_gap",
            "语音覆盖存在明显断层",
            f"当前 {voice_eligible_line_count} 条台词/旁白里有 {voice_bound_line_count} 条绑定语音，覆盖约 {voice_coverage_percent}%。",
            "如果这是配音试玩版，建议集中补齐主线关键句，或暂时移除零散语音，避免玩家误以为漏配。",
        )
    if scene_count >= 2 and choice_count == 0:
        add_vn_baseline_issue(
            issues,
            "soft",
            "choice_node",
            "缺少可交互选项",
            "多场景项目没有检测到选项节点。",
            "如果目标是视觉小说而非纯电子书，建议至少加入一个选项、分支或可回收差分。",
        )
    if long_choice_option_count:
        add_vn_baseline_issue(
            issues,
            "soft",
            "long_choice_option",
            "部分选项文案偏长",
            f"检测到 {long_choice_option_count} 个选项超过 42 字。",
            "把选项按钮压缩成玩家一眼能读完的行动意图，详细心理活动可以放进下一句旁白。",
        )
    if duplicate_choice_option_count:
        add_vn_baseline_issue(
            issues,
            "soft",
            "duplicate_choice_option",
            "同组选项存在重复文案",
            f"检测到 {duplicate_choice_option_count} 个重复选项文案。",
            "给每个选项写出明确差异，避免玩家以为分支无效或按钮重复。",
        )
    if crowded_choice_block_count:
        add_vn_baseline_issue(
            issues,
            "soft",
            "crowded_choice_block",
            "选项按钮数量偏多",
            f"检测到 {crowded_choice_block_count} 个选项卡片超过 4 个按钮。",
            "如果不是菜单式选择，建议拆成两层选择或减少同屏按钮数量，提升手柄/键盘选择体验。",
        )
    if scene_count >= 3 and sfx_play_count == 0:
        add_vn_baseline_issue(
            issues,
            "soft",
            "sfx_plan",
            "缺少基础音效点",
            "多场景项目没有检测到播放音效卡片。",
            "为门铃、脚步、点击、心跳、短信提示或关键演出补少量音效点，能显著提升试玩完成度。",
        )
    if video_asset_count and video_play_count == 0:
        add_vn_baseline_issue(
            issues,
            "soft",
            "video_asset_unused",
            "视频素材还没有进入剧情",
            f"检测到 {video_asset_count} 个视频素材，但没有播放视频卡片。",
            "如果这些是 OP、ED、PV 或过场动画，建议放入对应章节并跑一次原生 Runtime 视频桥接检查。",
        )
    if scene_count >= 2 and ending_scene_count and credits_roll_count == 0:
        add_vn_baseline_issue(
            issues,
            "soft",
            "credits_missing",
            "结局缺少片尾收束",
            f"检测到 {ending_scene_count} 个收束场景，但没有片尾字幕卡片。",
            "为正式版结局或试玩 Demo 补一个简短 STAFF / Thank You 片尾，能让作品结束感更完整。",
        )
    if dialogue_count >= 3 and character_show_count == 0:
        add_vn_baseline_issue(
            issues,
            "soft",
            "character_stage",
            "人物登场演出偏弱",
            "台词数量已经成段，但没有检测到显示角色卡片。",
            "为主要角色补显示/隐藏、位置、缩放和淡入淡出，让原生试玩更像正式 VN。",
        )
    elif scene_count >= 2 and character_show_count and character_hide_count == 0:
        add_vn_baseline_issue(
            issues,
            "soft",
            "character_hide_missing",
            "角色退场节奏未标记",
            "检测到角色登场，但没有隐藏角色卡片。",
            "章节切换或角色离场时补一个隐藏卡片，避免立绘残留。",
        )
    if character_show_count >= 3 and character_transition_count == 0:
        add_vn_baseline_issue(
            issues,
            "soft",
            "character_transition_missing",
            "人物登场缺少基础转场",
            f"检测到 {character_show_count} 次角色登场，但没有淡入、滑入、上浮或弹出转场。",
            "给主要角色登场/退场设置轻量转场，不需要每张卡都动，但关键情绪点应避免硬切。",
        )
    if character_show_count >= 3 and len(character_position_values) <= 1:
        add_vn_baseline_issue(
            issues,
            "soft",
            "character_position_static",
            "人物站位过于固定",
            f"检测到 {character_show_count} 次角色登场，但只使用了 {len(character_position_values)} 种站位。",
            "为对话双方或重点角色使用 left / center / right 等站位变化，减少所有立绘都堆在同一位置的观感。",
        )
    if character_show_count >= 4 and character_stage_adjustment_count == 0:
        add_vn_baseline_issue(
            issues,
            "soft",
            "character_stage_static",
            "人物舞台参数没有变化",
            "多次角色登场没有检测到缩放、透明度、偏移、翻转或层级调整。",
            "在近景、回忆、压迫感或角色切换时适当使用缩放/透明度/偏移，让立绘调度更接近正式 VN。",
        )
    if scene_count >= 2 and text_density < 2:
        add_vn_baseline_issue(
            issues,
            "soft",
            "text_density",
            "剧情密度偏低",
            f"平均每个场景只有 {text_density} 个台词/旁白/选项块。",
            "若不是纯演出 Demo，建议补足关键对白、旁白和过渡说明。",
        )
    if scene_count >= 3 and scenes_with_effects == 0:
        add_vn_baseline_issue(
            issues,
            "soft",
            "presentation_polish",
            "缺少基础演出润色",
            "多场景项目没有检测到粒子、镜头或屏幕效果。",
            "为关键情绪点补轻量镜头、闪白、滤镜或粒子，不需要堆特效，但要有记忆点。",
        )

    warn_count = sum(1 for issue in issues if issue.get("severity") == "warn")
    soft_count = sum(1 for issue in issues if issue.get("severity") == "soft")
    status = "ready" if not issues else ("needs_fix" if warn_count else "needs_polish")
    return {
        "formatVersion": 1,
        "generatedAt": now_iso(),
        "bundleDir": str(bundle_dir),
        "status": status,
        "project": {
            "projectId": project.get("projectId"),
            "title": project.get("title") or project.get("name") or "未命名项目",
            "language": project.get("language") or DEFAULT_PROJECT_LANGUAGE,
        },
        "summary": {
            "statusLabel": {"ready": "基础完整", "needs_fix": "需要修复", "needs_polish": "建议润色"}.get(status, status),
            "warnCount": warn_count,
            "softCount": soft_count,
            "issueCount": len(issues),
            "recommendation": issues[0]["suggestion"] if issues else "基础视觉小说体验未发现明显缺口，可继续做目标系统实机点测。",
        },
        "metrics": {
            "storySceneCount": scene_count,
            "dialogueCount": dialogue_count,
            "narrationCount": narration_count,
            "choiceCount": choice_count,
            "characterCount": len(characters),
            "charactersWithSpriteCount": characters_with_sprite,
            "characterShowCount": character_show_count,
            "characterHideCount": character_hide_count,
            "characterTransitionCount": character_transition_count,
            "characterPositionVariantCount": len(character_position_values),
            "characterStageAdjustmentCount": character_stage_adjustment_count,
            "scenesWithBackground": scenes_with_background,
            "backgroundBlockCount": background_block_count,
            "backgroundTransitionCount": background_transition_count,
            "backgroundAssetVariantCount": len(background_asset_ids),
            "missingBackgroundAssetCount": missing_background_asset_count,
            "scenesWithMusic": scenes_with_music,
            "scenesWithEffects": scenes_with_effects,
            "choiceOptionCount": choice_option_count,
            "emptyChoiceOptionCount": empty_choice_option_count,
            "longChoiceOptionCount": long_choice_option_count,
            "duplicateChoiceOptionCount": duplicate_choice_option_count,
            "crowdedChoiceBlockCount": crowded_choice_block_count,
            "sfxPlayCount": sfx_play_count,
            "missingSfxAssetCount": missing_sfx_asset_count,
            "videoAssetCount": video_asset_count,
            "videoPlayCount": video_play_count,
            "missingVideoAssetCount": missing_video_asset_count,
            "endingSceneCount": ending_scene_count,
            "creditsRollCount": credits_roll_count,
            "creditsLineCount": credits_line_count,
            "emptyCreditsRollCount": empty_credits_roll_count,
            "shortCreditsRollCount": short_credits_roll_count,
            "musicPlayCount": music_play_count,
            "musicStopCount": music_stop_count,
            "musicScopedCount": music_scoped_count,
            "musicFadeInCount": music_fade_in_count,
            "musicFadeOutCount": music_fade_out_count,
            "voiceEligibleLineCount": voice_eligible_line_count,
            "voiceBoundLineCount": voice_bound_line_count,
            "dialogueVoiceCount": dialogue_voice_count,
            "narrationVoiceCount": narration_voice_count,
            "voiceCoveragePercent": voice_coverage_percent,
            "missingVoiceAssetCount": missing_voice_asset_count,
            "entrySceneExists": entry_scene_id in valid_scene_ids,
            "routeTargetMissingCount": len(missing_route_targets),
            "unreachableSceneCount": len(unreachable_scene_ids),
            "linkedSceneCount": len(reachable_scene_ids),
            "placeholderAssetCount": len(placeholder_assets),
            "emptyTextBlockCount": empty_text_count,
            "textDensity": text_density,
            "averageTextLength": average_text_length,
        },
        "issues": issues,
    }


def render_native_runtime_vn_baseline_quality_markdown(report: dict) -> str:
    project = report.get("project") if isinstance(report.get("project"), dict) else {}
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    metrics = report.get("metrics") if isinstance(report.get("metrics"), dict) else {}
    issues = report.get("issues") if isinstance(report.get("issues"), list) else []
    metric_rows = [
        ("场景数", metrics.get("storySceneCount")),
        ("台词 / 旁白 / 选项", f"{int(metrics.get('dialogueCount') or 0)} / {int(metrics.get('narrationCount') or 0)} / {int(metrics.get('choiceCount') or 0)}"),
        ("选项按钮总数", metrics.get("choiceOptionCount")),
        ("空白 / 超长 / 重复选项", f"{int(metrics.get('emptyChoiceOptionCount') or 0)} / {int(metrics.get('longChoiceOptionCount') or 0)} / {int(metrics.get('duplicateChoiceOptionCount') or 0)}"),
        ("拥挤选项卡", metrics.get("crowdedChoiceBlockCount")),
        ("音效点 / 缺失音效", f"{int(metrics.get('sfxPlayCount') or 0)} / {int(metrics.get('missingSfxAssetCount') or 0)}"),
        ("视频素材 / 播放卡 / 缺失视频", f"{int(metrics.get('videoAssetCount') or 0)} / {int(metrics.get('videoPlayCount') or 0)} / {int(metrics.get('missingVideoAssetCount') or 0)}"),
        ("结局 / 片尾字幕 / 字幕行", f"{int(metrics.get('endingSceneCount') or 0)} / {int(metrics.get('creditsRollCount') or 0)} / {int(metrics.get('creditsLineCount') or 0)}"),
        ("空片尾 / 过短片尾", f"{int(metrics.get('emptyCreditsRollCount') or 0)} / {int(metrics.get('shortCreditsRollCount') or 0)}"),
        ("角色立绘覆盖", f"{int(metrics.get('charactersWithSpriteCount') or 0)} / {int(metrics.get('characterCount') or 0)}"),
        ("人物转场 / 登场", f"{int(metrics.get('characterTransitionCount') or 0)} / {int(metrics.get('characterShowCount') or 0)}"),
        ("人物站位变化", metrics.get("characterPositionVariantCount")),
        ("人物舞台调整", metrics.get("characterStageAdjustmentCount")),
        ("背景覆盖", f"{int(metrics.get('scenesWithBackground') or 0)} / {int(metrics.get('storySceneCount') or 0)}"),
        ("背景转场 / 背景卡", f"{int(metrics.get('backgroundTransitionCount') or 0)} / {int(metrics.get('backgroundBlockCount') or 0)}"),
        ("背景素材变化", metrics.get("backgroundAssetVariantCount")),
        ("缺失背景文件", metrics.get("missingBackgroundAssetCount")),
        ("BGM 进入点", metrics.get("scenesWithMusic")),
        ("BGM 播放 / 停止", f"{int(metrics.get('musicPlayCount') or 0)} / {int(metrics.get('musicStopCount') or 0)}"),
        ("BGM 淡入 / 淡出", f"{int(metrics.get('musicFadeInCount') or 0)} / {int(metrics.get('musicFadeOutCount') or 0)}"),
        ("BGM 明确范围", metrics.get("musicScopedCount")),
        ("语音覆盖", f"{format_markdown_value(metrics.get('voiceCoveragePercent'), '0')}%"),
        ("语音绑定 / 可配音文本", f"{int(metrics.get('voiceBoundLineCount') or 0)} / {int(metrics.get('voiceEligibleLineCount') or 0)}"),
        ("缺失语音文件", metrics.get("missingVoiceAssetCount")),
        ("入口场景有效", "是" if metrics.get("entrySceneExists") else "否"),
        ("路线缺失目标", metrics.get("routeTargetMissingCount")),
        ("入口不可达场景", metrics.get("unreachableSceneCount")),
        ("演出效果场景", metrics.get("scenesWithEffects")),
        ("占位素材", metrics.get("placeholderAssetCount")),
        ("空文本块", metrics.get("emptyTextBlockCount")),
        ("平均剧情块密度", metrics.get("textDensity")),
    ]
    lines = [
        "# 原生 Runtime VN 基础质感报告",
        "",
        f"- 项目：{format_markdown_value(project.get('title'), '未命名项目')}",
        f"- 生成时间：{format_markdown_value(report.get('generatedAt'))}",
        f"- 状态：{format_markdown_value(summary.get('statusLabel'), report.get('status') or 'unknown')}",
        f"- 建议：{format_markdown_value(summary.get('recommendation'))}",
        "",
        "## 基础指标",
        "",
        "| 项目 | 值 |",
        "| --- | --- |",
    ]
    for label, value in metric_rows:
        lines.append(f"| {label} | {format_markdown_value(value, '0')} |")
    lines.append("")
    if issues:
        lines.extend(["## 待处理项", "", "| 严重度 | 项目 | 说明 | 建议 |", "| --- | --- | --- | --- |"])
        for issue in issues:
            if isinstance(issue, dict):
                lines.append(
                    f"| {format_markdown_value(issue.get('severity'), 'soft')} | "
                    f"{format_markdown_value(issue.get('title'), '待处理')} | "
                    f"{format_markdown_value(issue.get('detail'), '-')} | "
                    f"{format_markdown_value(issue.get('suggestion'), '-')} |"
                )
        lines.append("")
    else:
        lines.extend(["## 待处理项", "", "没有发现明显基础质感缺口。", ""])
    lines.extend(
        [
            "## 重新生成",
            "",
            "```bash",
            "python3 runtime_player.py --write-vn-baseline-quality-reports .",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def write_native_runtime_vn_baseline_quality_reports(bundle_dir: Path) -> dict:
    report = build_native_runtime_vn_baseline_quality_report(bundle_dir)
    (bundle_dir / VN_BASELINE_QUALITY_REPORT_NAME).write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / VN_BASELINE_QUALITY_MARKDOWN_NAME).write_text(
        render_native_runtime_vn_baseline_quality_markdown(report),
        encoding="utf-8",
    )
    return report


def print_native_runtime_vn_baseline_quality_json_report(bundle_dir: Path) -> dict:
    report = build_native_runtime_vn_baseline_quality_report(bundle_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def print_native_runtime_vn_baseline_quality_markdown_report(bundle_dir: Path) -> dict:
    report = build_native_runtime_vn_baseline_quality_report(bundle_dir)
    print(render_native_runtime_vn_baseline_quality_markdown(report), end="")
    return report


def get_native_runtime_release_control_status(
    release_check: dict,
    release_candidate: dict,
    asset3d_digest: dict,
    vn_baseline_quality: dict | None = None,
) -> dict:
    release_summary = release_check.get("summary") if isinstance(release_check.get("summary"), dict) else {}
    rc_summary = release_candidate.get("summary") if isinstance(release_candidate.get("summary"), dict) else {}
    vn_summary = (
        vn_baseline_quality.get("summary")
        if isinstance(vn_baseline_quality, dict) and isinstance(vn_baseline_quality.get("summary"), dict)
        else {}
    )
    if (
        release_check.get("status") == "fail"
        or release_candidate.get("status") == "blocked"
        or int(release_summary.get("errors") or 0)
        or int(rc_summary.get("blockers") or 0)
        or int(vn_summary.get("warnCount") or 0)
    ):
        return {
            "status": "blocked",
            "label": "阻塞发布",
            "summary": "存在发布阻塞项或 VN 基础体验缺口，应先修复再进入三系统打包或分发。",
        }
    if (
        release_candidate.get("status") != "preview_ready"
        or int(rc_summary.get("optionalFailures") or 0)
        or int(rc_summary.get("warnings") or 0)
        or bool(asset3d_digest.get("topIssues"))
        or int(vn_summary.get("softCount") or 0)
    ):
        return {
            "status": "needs_review",
            "label": "需要复核",
            "summary": "主链没有阻塞项，但仍有警告、可选能力失败、资产风险或 VN 润色项需要发布前确认。",
        }
    return {
        "status": "ready",
        "label": "可进入发布候选",
        "summary": "导出包自检、RC 汇总和 3D 风险摘要没有发现阻塞项。",
    }


def build_native_runtime_release_control_next_steps(
    release_check: dict,
    release_candidate: dict,
    asset3d_digest: dict,
    vn_baseline_quality: dict,
    quality_gate: dict,
) -> list[str]:
    steps: list[str] = []

    def add_step(value: object) -> None:
        text = str(value or "").strip()
        if text and text not in steps:
            steps.append(text)

    if quality_gate.get("status") == "blocked":
        add_step("先修复发布自检或 RC 报告里的阻塞项，再重新生成发布总控报告。")
    elif quality_gate.get("status") == "needs_review":
        add_step("发布前复核警告项、3D 风险和目标系统 Preview 点测结果。")
    else:
        add_step("在目标系统运行 Preview 包，完成一次人工逐按钮长流程点测。")
    for action in release_candidate.get("nextActions") or []:
        add_step(action)
    for issue in (release_check.get("issues") or [])[:5]:
        if isinstance(issue, dict):
            add_step(issue.get("suggestion") or issue.get("message"))
    for issue in asset3d_digest.get("topIssues") or []:
        if isinstance(issue, dict):
            name = issue.get("name") or issue.get("assetId") or "未命名 3D 资产"
            action = issue.get("recommendedAction") or issue.get("summary") or "复核 3D 资产导入状态。"
            add_step(f"复核 3D 资产「{name}」：{action}")
    for recommendation in asset3d_digest.get("recommendations") or []:
        add_step(recommendation)
    for issue in (vn_baseline_quality.get("issues") if isinstance(vn_baseline_quality.get("issues"), list) else [])[:5]:
        if isinstance(issue, dict):
            title = issue.get("title") or issue.get("code") or "VN 基础质感"
            suggestion = issue.get("suggestion") or issue.get("detail") or "复核基础视觉小说体验。"
            add_step(f"处理 VN 基础质感「{title}」：{suggestion}")
    return steps[:10]


def build_native_runtime_release_control_payload(bundle_dir: Path) -> dict:
    payload = load_game_data(bundle_dir / DEFAULT_GAME_DATA_NAME)
    project = payload.get("project") if isinstance(payload.get("project"), dict) else {}
    build_info = payload.get("buildInfo") if isinstance(payload.get("buildInfo"), dict) else {}
    release_check = build_release_check_report(bundle_dir)
    release_candidate = build_native_runtime_release_candidate_report(bundle_dir)
    asset3d_report = build_native_3d_asset_report(bundle_dir)
    asset3d_digest = build_native_runtime_3d_risk_digest(asset3d_report)
    vn_baseline_quality = build_native_runtime_vn_baseline_quality_report(bundle_dir)
    quality_gate = get_native_runtime_release_control_status(
        release_check,
        release_candidate,
        asset3d_digest,
        vn_baseline_quality,
    )
    return {
        "formatVersion": 1,
        "generatedAt": now_iso(),
        "bundleDir": str(bundle_dir),
        "engine": {
            "name": "Canvasia Engine",
            "target": "native_runtime",
            "targetLabel": "原生 Runtime 包",
            "runtimeMode": "pygame_native",
            "releaseVersion": str(build_info.get("releaseVersion") or "1.0.0-preview"),
        },
        "project": {
            "projectId": project.get("projectId"),
            "title": project.get("title") or release_candidate.get("projectTitle") or "未命名项目",
            "language": project.get("language") or "zh-CN",
            "entrySceneId": project.get("entrySceneId"),
            "resolution": project.get("resolution") or {"width": 1280, "height": 720},
        },
        "qualityGate": quality_gate,
        "releaseCheck": {
            "status": release_check.get("status"),
            "summary": release_check.get("summary") or {},
            "topIssues": (release_check.get("issues") or [])[:8],
        },
        "releaseCandidate": {
            "status": release_candidate.get("status"),
            "summary": release_candidate.get("summary") or {},
            "readinessEstimate": release_candidate.get("readinessEstimate") or {},
            "platformMatrix": release_candidate.get("platformMatrix") or [],
            "videoStrategy": release_candidate.get("videoStrategy") or {},
            "commercialReleaseGaps": release_candidate.get("commercialReleaseGaps") or [],
        },
        "asset3d": asset3d_digest,
        "vnBaselineQuality": {
            "status": vn_baseline_quality.get("status"),
            "summary": vn_baseline_quality.get("summary") or {},
            "metrics": vn_baseline_quality.get("metrics") or {},
            "topIssues": (vn_baseline_quality.get("issues") or [])[:8],
            "markdown": VN_BASELINE_QUALITY_MARKDOWN_NAME,
            "json": VN_BASELINE_QUALITY_REPORT_NAME,
        },
        "nextSteps": build_native_runtime_release_control_next_steps(
            release_check,
            release_candidate,
            asset3d_digest,
            vn_baseline_quality,
            quality_gate,
        ),
        "includedReports": {
            "releaseCheck": "native-runtime-release-check.json",
            "releaseCandidateReport": "native-runtime-release-candidate-report.json",
            "asset3dDigest": "native-runtime-3d-risk-digest.json",
            "releaseControlReport": "native-runtime-release-control-report.md",
            "releaseControlJson": "native-runtime-release-control-report.json",
            "fileIntegrityReport": FILE_INTEGRITY_REPORT_NAME,
            "fileIntegrityMarkdown": FILE_INTEGRITY_MARKDOWN_NAME,
            "acceptanceMarkdown": ACCEPTANCE_REPORT_NAME,
            "acceptanceJson": ACCEPTANCE_JSON_NAME,
            "vnBaselineQualityMarkdown": VN_BASELINE_QUALITY_MARKDOWN_NAME,
            "vnBaselineQualityJson": VN_BASELINE_QUALITY_REPORT_NAME,
        },
    }


def render_native_runtime_release_control_markdown(payload: dict) -> str:
    project = payload.get("project") if isinstance(payload.get("project"), dict) else {}
    engine = payload.get("engine") if isinstance(payload.get("engine"), dict) else {}
    quality_gate = payload.get("qualityGate") if isinstance(payload.get("qualityGate"), dict) else {}
    release_check = payload.get("releaseCheck") if isinstance(payload.get("releaseCheck"), dict) else {}
    release_candidate = payload.get("releaseCandidate") if isinstance(payload.get("releaseCandidate"), dict) else {}
    asset3d = payload.get("asset3d") if isinstance(payload.get("asset3d"), dict) else {}
    vn_baseline = payload.get("vnBaselineQuality") if isinstance(payload.get("vnBaselineQuality"), dict) else {}
    release_summary = release_check.get("summary") if isinstance(release_check.get("summary"), dict) else {}
    rc_summary = release_candidate.get("summary") if isinstance(release_candidate.get("summary"), dict) else {}
    readiness = release_candidate.get("readinessEstimate") if isinstance(release_candidate.get("readinessEstimate"), dict) else {}
    vn_summary = vn_baseline.get("summary") if isinstance(vn_baseline.get("summary"), dict) else {}
    vn_metrics = vn_baseline.get("metrics") if isinstance(vn_baseline.get("metrics"), dict) else {}
    lines = [
        "# 原生 Runtime 发布总控报告",
        "",
        f"- 项目：{format_markdown_value(project.get('title'), '未命名项目')}",
        f"- 版本：{format_markdown_value(engine.get('releaseVersion'), '1.0.0-preview')}",
        f"- 生成时间：{format_markdown_value(payload.get('generatedAt'))}",
        f"- 总体状态：{format_markdown_value(quality_gate.get('label'), '需要复核')}",
        "",
        "## 总结",
        "",
        format_markdown_value(quality_gate.get("summary"), "请结合随包 JSON 报告复核导出状态。"),
        "",
        "## 核心指标",
        "",
        "| 项目 | 值 |",
        "| --- | --- |",
        f"| 发布自检 | {format_markdown_value(release_check.get('status'), 'unavailable')} |",
        f"| 自检错误 / 警告 | {int(release_summary.get('errors') or 0)} / {int(release_summary.get('warnings') or 0)} |",
        f"| RC 状态 | {format_markdown_value(release_candidate.get('status'), 'unavailable')} |",
        f"| RC 阻塞 / 可选失败 / 警告 | {int(rc_summary.get('blockers') or 0)} / {int(rc_summary.get('optionalFailures') or 0)} / {int(rc_summary.get('warnings') or 0)} |",
        f"| 桌面 Preview 估算 | {format_markdown_value(readiness.get('desktopPreviewPercent'), 'n/a')}% |",
        f"| 商业桌面估算 | {format_markdown_value(readiness.get('commercialDesktopPercent'), 'n/a')}% |",
        f"| 3D 摘要 | {format_markdown_value(asset3d.get('summaryLine'), '未生成')} |",
        f"| VN 基础质感 | {format_markdown_value(vn_summary.get('statusLabel'), vn_baseline.get('status') or '未生成')} |",
        "",
    ]
    if vn_baseline:
        lines.extend(["## VN 基础质感", "", "| 指标 | 值 |", "| --- | --- |"])
        for label, value in [
            ("场景数", vn_metrics.get("storySceneCount")),
            ("台词 / 旁白 / 选项", f"{int(vn_metrics.get('dialogueCount') or 0)} / {int(vn_metrics.get('narrationCount') or 0)} / {int(vn_metrics.get('choiceCount') or 0)}"),
            ("选项按钮总数", vn_metrics.get("choiceOptionCount")),
            ("空白 / 超长 / 重复选项", f"{int(vn_metrics.get('emptyChoiceOptionCount') or 0)} / {int(vn_metrics.get('longChoiceOptionCount') or 0)} / {int(vn_metrics.get('duplicateChoiceOptionCount') or 0)}"),
            ("拥挤选项卡", vn_metrics.get("crowdedChoiceBlockCount")),
            ("音效点 / 缺失音效", f"{int(vn_metrics.get('sfxPlayCount') or 0)} / {int(vn_metrics.get('missingSfxAssetCount') or 0)}"),
            ("视频素材 / 播放卡 / 缺失视频", f"{int(vn_metrics.get('videoAssetCount') or 0)} / {int(vn_metrics.get('videoPlayCount') or 0)} / {int(vn_metrics.get('missingVideoAssetCount') or 0)}"),
            ("结局 / 片尾字幕 / 字幕行", f"{int(vn_metrics.get('endingSceneCount') or 0)} / {int(vn_metrics.get('creditsRollCount') or 0)} / {int(vn_metrics.get('creditsLineCount') or 0)}"),
            ("空片尾 / 过短片尾", f"{int(vn_metrics.get('emptyCreditsRollCount') or 0)} / {int(vn_metrics.get('shortCreditsRollCount') or 0)}"),
            ("角色立绘覆盖", f"{int(vn_metrics.get('charactersWithSpriteCount') or 0)} / {int(vn_metrics.get('characterCount') or 0)}"),
            ("人物转场 / 登场", f"{int(vn_metrics.get('characterTransitionCount') or 0)} / {int(vn_metrics.get('characterShowCount') or 0)}"),
            ("人物站位变化", vn_metrics.get("characterPositionVariantCount")),
            ("人物舞台调整", vn_metrics.get("characterStageAdjustmentCount")),
            ("背景覆盖", f"{int(vn_metrics.get('scenesWithBackground') or 0)} / {int(vn_metrics.get('storySceneCount') or 0)}"),
            ("背景转场 / 背景卡", f"{int(vn_metrics.get('backgroundTransitionCount') or 0)} / {int(vn_metrics.get('backgroundBlockCount') or 0)}"),
            ("背景素材变化", vn_metrics.get("backgroundAssetVariantCount")),
            ("缺失背景文件", vn_metrics.get("missingBackgroundAssetCount")),
            ("BGM 进入点", vn_metrics.get("scenesWithMusic")),
            ("BGM 播放 / 停止", f"{int(vn_metrics.get('musicPlayCount') or 0)} / {int(vn_metrics.get('musicStopCount') or 0)}"),
            ("BGM 淡入 / 淡出", f"{int(vn_metrics.get('musicFadeInCount') or 0)} / {int(vn_metrics.get('musicFadeOutCount') or 0)}"),
            ("BGM 明确范围", vn_metrics.get("musicScopedCount")),
            ("语音覆盖", f"{format_markdown_value(vn_metrics.get('voiceCoveragePercent'), '0')}%"),
            ("语音绑定 / 可配音文本", f"{int(vn_metrics.get('voiceBoundLineCount') or 0)} / {int(vn_metrics.get('voiceEligibleLineCount') or 0)}"),
            ("缺失语音文件", vn_metrics.get("missingVoiceAssetCount")),
            ("入口场景有效", "是" if vn_metrics.get("entrySceneExists") else "否"),
            ("路线缺失目标", vn_metrics.get("routeTargetMissingCount")),
            ("入口不可达场景", vn_metrics.get("unreachableSceneCount")),
            ("缺口 / 润色项", f"{int(vn_summary.get('warnCount') or 0)} / {int(vn_summary.get('softCount') or 0)}"),
        ]:
            lines.append(f"| {label} | {format_markdown_value(value, '0')} |")
        top_vn_issues = vn_baseline.get("topIssues") if isinstance(vn_baseline.get("topIssues"), list) else []
        if top_vn_issues:
            lines.extend(["", "优先处理："])
            for issue in top_vn_issues[:5]:
                if isinstance(issue, dict):
                    lines.append(
                        f"- {format_markdown_value(issue.get('title'), 'VN 基础质感')}："
                        f"{format_markdown_value(issue.get('suggestion') or issue.get('detail'), '需要复核')}"
                    )
        lines.append("")
    metrics = asset3d.get("metrics") if isinstance(asset3d.get("metrics"), list) else []
    if metrics:
        lines.extend(["## 3D 风险快照", "", "| 指标 | 值 |", "| --- | --- |"])
        for metric in metrics:
            if isinstance(metric, dict):
                lines.append(f"| {format_markdown_value(metric.get('label'), '指标')} | {format_markdown_value(metric.get('value'), '-')} |")
        lines.append("")
    top_issues = asset3d.get("topIssues") if isinstance(asset3d.get("topIssues"), list) else []
    if top_issues:
        lines.extend(["## 优先处理 3D 资产", ""])
        for issue in top_issues:
            if isinstance(issue, dict):
                lines.append(
                    f"- {format_markdown_value(issue.get('name') or issue.get('assetId'), '未命名 3D 资产')}："
                    f"{format_markdown_value(issue.get('summary') or issue.get('statusLabel'), '需要复核')}"
                )
        lines.append("")
    lines.extend(["## 下一步", ""])
    for index, step in enumerate(payload.get("nextSteps") or ["完成目标系统实机点测。"], start=1):
        lines.append(f"{index}. {format_markdown_value(step)}")
    lines.extend(
        [
            "",
            "## 可重新生成",
            "",
            "```bash",
            "python3 runtime_player.py --write-release-control-reports .",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def write_native_runtime_release_control_reports(bundle_dir: Path) -> dict:
    payload = build_native_runtime_release_control_payload(bundle_dir)
    write_native_runtime_vn_baseline_quality_reports(bundle_dir)
    (bundle_dir / "native-runtime-release-control-report.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / "native-runtime-release-control-report.md").write_text(
        render_native_runtime_release_control_markdown(payload),
        encoding="utf-8",
    )
    return payload


def print_native_runtime_release_control_json_report(bundle_dir: Path) -> dict:
    payload = build_native_runtime_release_control_payload(bundle_dir)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


def print_native_runtime_release_control_markdown_report(bundle_dir: Path) -> dict:
    payload = build_native_runtime_release_control_payload(bundle_dir)
    print(render_native_runtime_release_control_markdown(payload), end="")
    return payload


def build_acceptance_automated_checks(release_control: dict, integrity_verification: dict) -> list[dict]:
    release_check = release_control.get("releaseCheck") if isinstance(release_control.get("releaseCheck"), dict) else {}
    release_candidate = (
        release_control.get("releaseCandidate") if isinstance(release_control.get("releaseCandidate"), dict) else {}
    )
    asset3d = release_control.get("asset3d") if isinstance(release_control.get("asset3d"), dict) else {}
    vn_baseline = (
        release_control.get("vnBaselineQuality") if isinstance(release_control.get("vnBaselineQuality"), dict) else {}
    )
    return [
        {
            "id": "release_check",
            "label": "发布前自检",
            "status": str(release_check.get("status") or "unavailable"),
            "summary": release_check.get("summary") or {},
            "command": "python3 runtime_player.py --release-check .",
        },
        {
            "id": "release_candidate",
            "label": "发布候选总报告",
            "status": str(release_candidate.get("status") or "unavailable"),
            "summary": release_candidate.get("summary") or {},
            "command": "python3 runtime_player.py --release-candidate-report .",
        },
        {
            "id": "release_control",
            "label": "发布总控",
            "status": str((release_control.get("qualityGate") or {}).get("status") or "unavailable"),
            "summary": str((release_control.get("qualityGate") or {}).get("summary") or ""),
            "command": "python3 runtime_player.py --release-control-report .",
        },
        {
            "id": "vn_baseline_quality",
            "label": "VN 基础质感",
            "status": str(vn_baseline.get("status") or "unavailable"),
            "summary": vn_baseline.get("summary") or {},
            "command": "python3 runtime_player.py --vn-baseline-quality-report .",
        },
        {
            "id": "file_integrity",
            "label": "文件完整性",
            "status": str(integrity_verification.get("status") or "unavailable"),
            "summary": integrity_verification.get("summary") or {},
            "command": "python3 runtime_player.py --verify-file-integrity .",
        },
        {
            "id": "video_strategy",
            "label": "视频后端策略",
            "status": str((release_candidate.get("videoStrategy") or {}).get("previewProbeStatus") or "unavailable"),
            "summary": str((release_candidate.get("videoStrategy") or {}).get("recommendation") or ""),
            "command": "python3 runtime_player.py --probe-video-preview .",
        },
        {
            "id": "asset3d",
            "label": "3D 资产风险",
            "status": str(asset3d.get("status") or "unavailable"),
            "summary": str(asset3d.get("summaryLine") or ""),
            "command": "python3 runtime_player.py --describe-3d-assets .",
        },
    ]


def build_acceptance_platform_matrix(release_control: dict) -> list[dict]:
    release_candidate = (
        release_control.get("releaseCandidate") if isinstance(release_control.get("releaseCandidate"), dict) else {}
    )
    platform_matrix = release_candidate.get("platformMatrix") if isinstance(release_candidate.get("platformMatrix"), list) else []
    source = platform_matrix or [
        {"id": "macos", "label": "macOS", "buildScript": "打包原生Runtime应用.command"},
        {"id": "windows", "label": "Windows", "buildScript": "build_native_runtime_app.bat"},
        {"id": "linux", "label": "Linux", "buildScript": "build_native_runtime_app.sh"},
    ]
    rows = []
    for entry in source:
        if not isinstance(entry, dict):
            continue
        rows.append(
            {
                "id": str(entry.get("id") or ""),
                "label": str(entry.get("label") or entry.get("id") or "目标系统"),
                "buildScript": str(entry.get("buildScript") or ""),
                "currentMachine": bool(entry.get("currentMachine")),
                "status": "needs_target_test",
                "requiredManualChecks": [
                    "启动包或 App，确认标题页、开始游戏、读档、设置和退出都能响应。",
                    "完成一轮正式存档、读档、快存、退出重开自动续玩。",
                    "试玩至少一条包含选项、跳转、音频、资料馆入口和视频/3D 兜底提示的路线。",
                    "记录系统安全提示、杀毒/SmartScreen/Gatekeeper 提示和玩家可理解程度。",
                ],
            }
        )
    return rows


def build_acceptance_manual_check_groups() -> list[dict]:
    return [
        {
            "id": "startup",
            "label": "启动与主菜单",
            "items": [
                "首次启动不会闪退，标题页按钮能用。",
                "新开游戏、继续游戏、读档、设置、资料馆、退出路径都可达。",
                "未安装可选视频依赖时，提示清楚且不影响主线试玩。",
            ],
        },
        {
            "id": "reading_flow",
            "label": "阅读主链",
            "items": [
                "台词、旁白、选项、跳转、条件分支和变量变化符合网页预览。",
                "文字速度、自动播放、已读快进、清屏、历史文本和语音回听可用。",
                "鼠标、键盘快捷键和右键菜单不会卡死在覆盖层。",
            ],
        },
        {
            "id": "state",
            "label": "存档 / 设置 / 进度",
            "items": [
                "正式存档位数量符合项目设置，翻页和覆盖存档正常。",
                "快存、正式读档、退出重开自动续玩可恢复到合理位置。",
                "主题、显示模式、语言、文字大小、文本框透明度和音量设置能持久保存。",
            ],
        },
        {
            "id": "extras",
            "label": "资料馆与解锁",
            "items": [
                "章节回放、CG、音乐、地点、角色、结局、成就入口可打开。",
                "详情页、内部选择和返回路径清晰。",
                "未解锁内容不会暴露错误数据或空白死页。",
            ],
        },
        {
            "id": "media",
            "label": "音视频 / 3D / 演出",
            "items": [
                "BGM、音效、语音音量独立可控，切换场景不残留异常声音。",
                "OP/ED/PV 视频能按预期内嵌播放或桥接系统播放器，并能回到剧情链。",
                "3D / Live2D 预览桥和兜底立绘提示清楚，不误导成完整实时渲染。",
                "粒子、镜头、闪屏、淡入淡出、滤镜和景深不会挡住核心文本。",
            ],
        },
        {
            "id": "distribution",
            "label": "分发与升级",
            "items": [
                "压缩包 SHA-256、包内完整性校验和验收报告都随包提供。",
                "覆盖旧版本后，已有存档、设置和进度不会被误删。",
                "崩溃日志位置可找到，错误信息能帮助用户反馈问题。",
            ],
        },
    ]


def get_acceptance_status(release_control: dict, integrity_verification: dict) -> dict:
    quality_gate = release_control.get("qualityGate") if isinstance(release_control.get("qualityGate"), dict) else {}
    quality_status = str(quality_gate.get("status") or "blocked")
    integrity_status = str(integrity_verification.get("status") or "unavailable")
    if quality_status == "blocked" or integrity_status == "fail":
        return {
            "status": "blocked",
            "label": "暂不建议验收",
            "summary": "自动检查存在阻塞项，应先修复后再做人工三系统验收。",
        }
    if quality_status == "needs_review" or integrity_status in {"warn", "unavailable"}:
        return {
            "status": "needs_manual_review",
            "label": "可进入人工复核",
            "summary": "主链没有自动阻塞，但仍需人工确认警告、目标系统表现和分发提示。",
        }
    return {
        "status": "ready_for_manual_acceptance",
        "label": "可进入三系统验收",
        "summary": "自动检查没有发现阻塞项，可以按清单进行目标系统人工点测。",
    }


def build_native_runtime_acceptance_payload(bundle_dir: Path) -> dict:
    release_control = build_native_runtime_release_control_payload(bundle_dir)
    try:
        integrity_verification = build_native_runtime_file_integrity_verification(bundle_dir)
    except NativeRuntimeError as error:
        integrity_verification = {
            "status": "unavailable",
            "checkedAt": now_iso(),
            "summary": {"missingCount": 0, "changedCount": 0, "extraCount": 0},
            "message": str(error),
        }
    acceptance_gate = get_acceptance_status(release_control, integrity_verification)
    project = release_control.get("project") if isinstance(release_control.get("project"), dict) else {}
    engine = release_control.get("engine") if isinstance(release_control.get("engine"), dict) else {}
    manual_groups = build_acceptance_manual_check_groups()
    platform_matrix = build_acceptance_platform_matrix(release_control)
    return {
        "formatVersion": 1,
        "generatedAt": now_iso(),
        "bundleDir": str(bundle_dir),
        "project": project,
        "engine": engine,
        "acceptanceGate": acceptance_gate,
        "automatedChecks": build_acceptance_automated_checks(release_control, integrity_verification),
        "platformMatrix": platform_matrix,
        "manualCheckGroups": manual_groups,
        "summary": {
            "manualGroupCount": len(manual_groups),
            "manualItemCount": sum(len(group.get("items") or []) for group in manual_groups),
            "targetPlatformCount": len(platform_matrix),
            "releaseControlStatus": (release_control.get("qualityGate") or {}).get("status"),
            "fileIntegrityStatus": integrity_verification.get("status"),
        },
        "recommendedCommands": [
            "python3 runtime_player.py --doctor .",
            "python3 runtime_player.py --verify-file-integrity .",
            "python3 runtime_player.py --release-control-report .",
            "python3 runtime_player.py --acceptance-report .",
        ],
        "includedReports": {
            "acceptanceMarkdown": ACCEPTANCE_REPORT_NAME,
            "acceptanceJson": ACCEPTANCE_JSON_NAME,
            "releaseControlMarkdown": "native-runtime-release-control-report.md",
            "releaseControlJson": "native-runtime-release-control-report.json",
            "fileIntegrityJson": FILE_INTEGRITY_REPORT_NAME,
            "fileIntegrityMarkdown": FILE_INTEGRITY_MARKDOWN_NAME,
        },
    }


def render_native_runtime_acceptance_markdown(payload: dict) -> str:
    project = payload.get("project") if isinstance(payload.get("project"), dict) else {}
    engine = payload.get("engine") if isinstance(payload.get("engine"), dict) else {}
    gate = payload.get("acceptanceGate") if isinstance(payload.get("acceptanceGate"), dict) else {}
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    lines = [
        "# 原生 Runtime 发布验收清单",
        "",
        f"- 项目：{format_markdown_value(project.get('title'), '未命名项目')}",
        f"- 版本：{format_markdown_value(engine.get('releaseVersion'), '1.0.0-preview')}",
        f"- 生成时间：{format_markdown_value(payload.get('generatedAt'))}",
        f"- 验收状态：{format_markdown_value(gate.get('label'), '需要复核')}",
        "",
        "## 总结",
        "",
        format_markdown_value(gate.get("summary"), "请按下方清单完成目标系统点测。"),
        "",
        "## 自动检查",
        "",
        "| 检查 | 状态 | 命令 |",
        "| --- | --- | --- |",
    ]
    for check in payload.get("automatedChecks") or []:
        if isinstance(check, dict):
            lines.append(
                f"| {format_markdown_value(check.get('label'), '检查')} | "
                f"{format_markdown_value(check.get('status'), 'unavailable')} | "
                f"`{format_markdown_value(check.get('command'), '-')}` |"
            )
    lines.extend(
        [
            "",
            "## 三系统验收",
            "",
            "| 系统 | 构建脚本 | 当前机器 | 验收状态 |",
            "| --- | --- | --- | --- |",
        ]
    )
    for platform_entry in payload.get("platformMatrix") or []:
        if isinstance(platform_entry, dict):
            lines.append(
                f"| {format_markdown_value(platform_entry.get('label'), '目标系统')} | "
                f"{format_markdown_value(platform_entry.get('buildScript'), '目标系统打包')} | "
                f"{'是' if platform_entry.get('currentMachine') else '否'} | "
                f"{format_markdown_value(platform_entry.get('status'), 'needs_target_test')} |"
            )
    lines.extend(["", "## 人工逐项点测", ""])
    for group in payload.get("manualCheckGroups") or []:
        if not isinstance(group, dict):
            continue
        lines.extend([f"### {format_markdown_value(group.get('label'), '验收项')}", ""])
        for item in group.get("items") or []:
            lines.append(f"- [ ] {format_markdown_value(item)}")
        lines.append("")
    lines.extend(
        [
            "## 建议命令",
            "",
            "```bash",
            *[str(command) for command in payload.get("recommendedCommands") or []],
            "```",
            "",
            "## 验收规模",
            "",
            f"- 人工分组：{int(summary.get('manualGroupCount') or 0)}",
            f"- 人工检查项：{int(summary.get('manualItemCount') or 0)}",
            f"- 目标系统：{int(summary.get('targetPlatformCount') or 0)}",
            "",
        ]
    )
    return "\n".join(lines)


def write_native_runtime_acceptance_reports(bundle_dir: Path) -> dict:
    payload = build_native_runtime_acceptance_payload(bundle_dir)
    (bundle_dir / ACCEPTANCE_JSON_NAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (bundle_dir / ACCEPTANCE_REPORT_NAME).write_text(
        render_native_runtime_acceptance_markdown(payload),
        encoding="utf-8",
    )
    return payload


def print_native_runtime_acceptance_json_report(bundle_dir: Path) -> dict:
    payload = build_native_runtime_acceptance_payload(bundle_dir)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


def print_native_runtime_acceptance_markdown_report(bundle_dir: Path) -> dict:
    payload = build_native_runtime_acceptance_payload(bundle_dir)
    print(render_native_runtime_acceptance_markdown(payload), end="")
    return payload


def build_save_dialog_page_data_for_doctor(bundle_dir: Path) -> dict:
    payload = load_game_data(bundle_dir / "game_data.json")
    project = payload.get("project") or {}
    variables = (payload.get("variables") or {}).get("variables") or []
    save_store = load_project_save_store(
        str(project.get("projectId") or "untitled_project"),
        get_project_formal_save_slot_count(project),
    )
    return build_save_dialog_page_data(project, save_store, page=0, variables=variables)


def print_native_runtime_doctor_report(bundle_dir: Path) -> dict:
    report = build_native_runtime_doctor_report(bundle_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def build_native_title_screen_report(bundle_dir: Path) -> dict:
    payload = load_game_data(bundle_dir / DEFAULT_GAME_DATA_NAME)
    project = payload.get("project") if isinstance(payload.get("project"), dict) else {}
    project_id = str(project.get("projectId") or "untitled_project")
    formal_slot_count = get_project_formal_save_slot_count(project)
    save_store = load_project_save_store(project_id, formal_slot_count)
    formal_slots = save_store.get("formalSlots") or []
    filled_formal_count = sum(1 for item in formal_slots if item)
    title_logo_asset_id = str((project.get("gameUiConfig") or {}).get("titleLogoAssetId") or "").strip()
    assets_doc = payload.get("assets") if isinstance(payload.get("assets"), dict) else {}
    assets = assets_doc.get("assets") if isinstance(assets_doc.get("assets"), list) else []
    assets_by_id = {str(asset.get("id")): asset for asset in assets if isinstance(asset, dict) and asset.get("id")}
    title_logo_asset = assets_by_id.get(title_logo_asset_id) if title_logo_asset_id else None
    title_logo_path = get_asset_runtime_path(bundle_dir, title_logo_asset)
    brand_logo_path = bundle_dir / ENGINE_BRAND_LOGO_RELATIVE_PATH
    auto_resume = load_project_auto_resume(project_id)
    return {
        "status": "ready",
        "checkedAt": now_iso(),
        "bundleDir": str(bundle_dir),
        "projectTitle": str(project.get("title") or project.get("name") or "Canvasia Engine"),
        "titleLogoAssetId": title_logo_asset_id,
        "titleLogoExists": bool(title_logo_path and title_logo_path.is_file()),
        "engineBrandLogo": ENGINE_BRAND_LOGO_RELATIVE_PATH,
        "engineBrandLogoExists": brand_logo_path.is_file(),
        "formalSaveSlotCount": formal_slot_count,
        "filledFormalSaveCount": filled_formal_count,
        "hasAutoResume": auto_resume is not None,
        "menuItems": [
            {
                "key": key,
                "label": label,
                "enabled": key != "resume" or auto_resume is not None,
            }
            for key, label in TITLE_MENU_ITEMS
        ],
    }


def print_native_title_screen_report(bundle_dir: Path) -> None:
    report = build_native_title_screen_report(bundle_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def iter_export_scenes(chapters: list[dict]) -> list[dict]:
    return [scene for chapter in chapters for scene in (chapter.get("scenes") or [])]


def collect_scene_outgoing_targets(scene: dict | None) -> list[str]:
    if not scene:
        return []
    targets = []
    for block in scene.get("blocks", []) or []:
        block_type = str(block.get("type") or "").strip()
        if block_type == "jump":
            target = str(block.get("targetSceneId") or "").strip()
            if target:
                targets.append(target)
        elif block_type == "choice":
            for option in block.get("options", []) or []:
                target = str(option.get("gotoSceneId") or "").strip()
                if target:
                    targets.append(target)
        elif block_type == "condition":
            for branch in block.get("branches", []) or []:
                target = str(branch.get("gotoSceneId") or "").strip()
                if target:
                    targets.append(target)
            fallback = str(block.get("elseGotoSceneId") or "").strip()
            if fallback:
                targets.append(fallback)
    deduped = []
    for target in targets:
        if target not in deduped:
            deduped.append(target)
    return deduped


def build_ending_scene_ids(chapters: list[dict]) -> list[str]:
    scene_ids = []
    for scene in iter_export_scenes(chapters):
        scene_id = str(scene.get("id") or "").strip()
        if scene_id and not collect_scene_outgoing_targets(scene):
            scene_ids.append(scene_id)
    return scene_ids


def build_narration_archive_entry_id(scene_id: str | None, block_id: str | None, block_index: int) -> str:
    safe_scene_id = str(scene_id or "scene").strip() or "scene"
    safe_block_id = str(block_id or "block").strip() or "block"
    return f"{safe_scene_id}:{safe_block_id}:{max(0, int(block_index))}"


def build_relationship_archive_id(left_character_id: str | None, right_character_id: str | None) -> str:
    pair = sorted(
        [
            str(left_character_id or "").strip(),
            str(right_character_id or "").strip(),
        ]
    )
    return "__".join(item for item in pair if item)


def build_voice_replay_entry_id(scene_id: str | None, block_id: str | None, block_index: int) -> str:
    return build_narration_archive_entry_id(scene_id, block_id, block_index)


def mix_rgb(color_a: tuple[int, int, int], color_b: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    ratio = clamp(float(amount), 0.0, 1.0)
    return tuple(
        int(round(channel_a + (channel_b - channel_a) * ratio))
        for channel_a, channel_b in zip(color_a, color_b)
    )


def hex_to_rgb(value: str | None, fallback: tuple[int, int, int]) -> tuple[int, int, int]:
    if isinstance(value, (list, tuple)) and len(value) >= 3:
        try:
            return tuple(clamp_int(channel, 0, 255, fallback[index]) for index, channel in enumerate(value[:3]))
        except Exception:
            return fallback
    safe_value = str(value or "").strip().lstrip("#")
    if len(safe_value) != 6:
        return fallback
    try:
        return tuple(int(safe_value[index : index + 2], 16) for index in range(0, 6, 2))
    except Exception:
        return fallback


def get_safe_native_particle_preset(preset: str | None) -> str:
    safe_preset = str(preset or "").strip()
    return safe_preset if safe_preset in NATIVE_PARTICLE_PRESET_DEFAULTS else "snow"


def get_safe_option(value, allowed: set[str], fallback: str) -> str:
    safe_value = str(value or "").strip()
    return safe_value if safe_value in allowed else fallback


def get_effect_duration_seconds(value) -> float:
    return EFFECT_DURATION_SECONDS.get(get_safe_option(value, set(EFFECT_DURATION_SECONDS), "medium"), EFFECT_DURATION_SECONDS["medium"])


def normalize_native_visual_effect_block(block: dict | None) -> dict:
    block = block or {}
    block_type = str(block.get("type") or "").strip()
    if block_type == "screen_shake":
        return {
            "type": block_type,
            "intensity": get_safe_option(block.get("intensity"), set(SHAKE_DISTANCE), "medium"),
            "duration": get_safe_option(block.get("duration"), set(EFFECT_DURATION_SECONDS), "medium"),
        }
    if block_type == "screen_flash":
        return {
            "type": block_type,
            "color": get_safe_option(block.get("color"), set(FLASH_COLORS), "white"),
            "intensity": get_safe_option(block.get("intensity"), set(FLASH_ALPHA), "medium"),
            "duration": get_safe_option(block.get("duration"), set(EFFECT_DURATION_SECONDS), "medium"),
        }
    if block_type == "screen_fade":
        return {
            "type": block_type,
            "action": get_safe_option(block.get("action"), {"fade_out", "fade_in"}, "fade_out"),
            "color": get_safe_option(block.get("color"), set(FADE_COLORS), "black"),
            "duration": get_safe_option(block.get("duration"), set(EFFECT_DURATION_SECONDS), "medium"),
        }
    if block_type == "camera_zoom":
        return {
            "type": block_type,
            "action": get_safe_option(block.get("action"), {"zoom_in", "zoom_out", "reset"}, "zoom_in"),
            "strength": get_safe_option(block.get("strength"), {"light", "medium", "heavy"}, "medium"),
            "focus": get_safe_option(block.get("focus"), {"left", "center", "right"}, "center"),
        }
    if block_type == "camera_pan":
        return {
            "type": block_type,
            "target": get_safe_option(block.get("target"), {"left", "center", "right"}, "center"),
            "strength": get_safe_option(block.get("strength"), {"light", "medium", "heavy"}, "medium"),
        }
    if block_type == "screen_filter":
        return {
            "type": block_type,
            "action": get_safe_option(block.get("action"), {"apply", "clear"}, "apply"),
            "preset": get_safe_option(block.get("preset"), set(SCREEN_FILTER_WASH), "memory"),
            "strength": get_safe_option(block.get("strength"), {"soft", "medium", "strong"}, "medium"),
            "grade": get_safe_screen_color_grade(block.get("grade")),
        }
    if block_type == "depth_blur":
        return {
            "type": block_type,
            "action": get_safe_option(block.get("action"), {"apply", "clear"}, "apply"),
            "focus": get_safe_option(block.get("focus"), {"left", "center", "right", "full"}, "full"),
            "strength": get_safe_option(block.get("strength"), set(DEPTH_BLUR_ALPHA), "medium"),
        }
    return {"type": block_type}


def normalize_native_particle_effect_config(effect: dict | None) -> dict:
    effect = effect or {}
    preset = get_safe_native_particle_preset(effect.get("preset"))
    defaults = NATIVE_PARTICLE_PRESET_DEFAULTS[preset]
    intensity = str(effect.get("intensity") or "medium").strip()
    if intensity not in NATIVE_PARTICLE_INTENSITY_MULTIPLIER:
        intensity = "medium"
    speed = str(effect.get("speed") or "medium").strip()
    if speed not in NATIVE_PARTICLE_SPEED_MULTIPLIER:
        speed = "medium"
    wind = str(effect.get("wind") or "still").strip()
    if wind not in NATIVE_PARTICLE_WIND_VALUE:
        wind = "still"
    area = str(effect.get("area") or "full").strip()
    if area not in NATIVE_PARTICLE_AREA_RANGES:
        area = "full"
    density = int(round(float(effect.get("density") or defaults["density"])))
    density = max(4, min(240, density))
    size_min = float(effect.get("sizeMin") or defaults["sizeMin"])
    size_max = float(effect.get("sizeMax") or defaults["sizeMax"])
    speed_value = float(effect.get("gravityY") or defaults["speed"])
    drift_value = float(effect.get("spreadX") or defaults["drift"])
    return {
        "action": str(effect.get("action") or "start").strip(),
        "preset": preset,
        "assetId": str(effect.get("assetId") or "").strip(),
        "intensity": intensity,
        "speed": speed,
        "wind": wind,
        "area": area,
        "density": density,
        "sizeMin": max(1.0, min(size_min, size_max)),
        "sizeMax": max(1.0, max(size_min, size_max)),
        "speedValue": speed_value,
        "driftValue": drift_value,
        "color": hex_to_rgb(effect.get("color"), defaults["color"]),
        "accentColor": hex_to_rgb(effect.get("colorAccent"), defaults["accent"]),
        "shape": defaults["shape"],
    }


def build_native_particle_item(config: dict, width: int, height: int) -> dict:
    size = random.uniform(float(config.get("sizeMin") or 4), float(config.get("sizeMax") or 10))
    area_start, area_end = NATIVE_PARTICLE_AREA_RANGES.get(config.get("area"), NATIVE_PARTICLE_AREA_RANGES["full"])
    start_x = random.uniform(width * area_start, width * area_end)
    start_y = random.uniform(-height * 0.2, height * 0.1)
    wind_bias = NATIVE_PARTICLE_WIND_VALUE.get(config.get("wind"), 0)
    speed_multiplier = NATIVE_PARTICLE_SPEED_MULTIPLIER.get(config.get("speed"), 1.0)
    velocity_x = (random.uniform(-1.0, 1.0) * float(config.get("driftValue") or 12) * 0.25) + wind_bias
    base_speed = float(config.get("speedValue") or 90) * speed_multiplier
    velocity_y = base_speed + random.uniform(-0.25, 0.25) * base_speed
    preset = str(config.get("preset") or "snow")
    if preset in {"bubbles", "smoke", "flame", "stardust", "glyphs"}:
        start_y = random.uniform(height * 0.4, height * 0.95)
        velocity_y *= -0.55 if preset != "flame" else -0.82
    lifetime = random.uniform(3.0, 8.0)
    return {
        "x": start_x,
        "y": start_y,
        "vx": velocity_x,
        "vy": velocity_y,
        "size": size,
        "life": lifetime,
        "maxLife": lifetime,
        "spin": random.uniform(-120, 120),
        "rotation": random.uniform(0, 360),
        "colorMix": random.random(),
        "wobble": random.uniform(4.0, 20.0),
        "wobblePhase": random.uniform(0, math.pi * 2),
    }


def build_native_particle_items(config: dict, width: int, height: int) -> list[dict]:
    if str(config.get("action") or "start") == "stop":
        return []
    density = int(config.get("density") or 0)
    density = int(density * NATIVE_PARTICLE_INTENSITY_MULTIPLIER.get(config.get("intensity"), 1.0))
    density = max(4, min(180, density))
    return [build_native_particle_item(config, width, height) for _ in range(density)]


def exercise_particle_effect(bundle_dir: Path) -> None:
    payload = load_game_data(bundle_dir / "game_data.json")
    chapters = payload.get("chapters") or []
    particle_block = None
    for chapter in chapters:
        for scene in chapter.get("scenes") or []:
            for block in scene.get("blocks") or []:
                if str(block.get("type") or "").strip() == "particle_effect":
                    particle_block = block
                    break
            if particle_block:
                break
        if particle_block:
            break
    if not particle_block:
        particle_block = {"type": "particle_effect", "action": "start", "preset": "snow", "intensity": "medium", "speed": "medium", "wind": "still", "area": "full"}

    config = normalize_native_particle_effect_config(particle_block)
    if config["action"] == "stop":
        raise NativeRuntimeError("粒子自检拿到的是 stop 配置，无法验证渲染生成。")
    items = build_native_particle_items(config, 1280, 720)
    if not items:
        raise NativeRuntimeError("粒子条目没有生成。")
    if len(items) < 4:
        raise NativeRuntimeError("粒子条目数量过少，未达到最小预期。")
    print(f"Native runtime particle validation passed: preset={config['preset']} items={len(items)}")


def exercise_visual_effects(bundle_dir: Path) -> None:
    payload = load_game_data(bundle_dir / "game_data.json")
    supported_types = {"screen_shake", "screen_flash", "screen_fade", "camera_zoom", "camera_pan", "screen_filter", "depth_blur"}
    normalized = []
    for chapter in payload.get("chapters") or []:
        for scene in chapter.get("scenes") or []:
            for block in scene.get("blocks") or []:
                if str(block.get("type") or "").strip() in supported_types:
                    normalized.append(normalize_native_visual_effect_block(block))
    if not normalized:
        normalized = [
            normalize_native_visual_effect_block({"type": "screen_flash", "color": "white", "intensity": "soft", "duration": "short"}),
            normalize_native_visual_effect_block({"type": "camera_zoom", "action": "zoom_in", "strength": "light", "focus": "center"}),
            normalize_native_visual_effect_block({"type": "screen_filter", "action": "apply", "preset": "memory", "strength": "soft"}),
        ]
    if any(not item.get("type") for item in normalized):
        raise NativeRuntimeError("高级演出配置规范化失败。")
    print(f"Native runtime visual effects validation passed: {len(normalized)} blocks")


def exercise_player_profile(bundle_dir: Path) -> None:
    payload = load_game_data(bundle_dir / "game_data.json")
    project = payload.get("project") or {}
    project_id = str(project.get("projectId") or "untitled_project")
    chapters = payload.get("chapters") or []
    scene = next((scene for chapter in chapters for scene in (chapter.get("scenes") or []) if scene.get("id")), None)
    if not scene:
        raise NativeRuntimeError("没有可用于测试续玩记录的场景。")

    profile = sanitize_player_profile(
        {
            "firstPlayedAt": now_iso(),
            "lastPlayedAt": now_iso(),
            "lastEndedAt": now_iso(),
            "totalPlayMs": 3210,
            "sessionCount": 2,
            "resumedCount": 1,
            "returnToTitleCount": 1,
        }
    )
    profile_path = write_project_player_profile(project_id, profile)
    loaded_profile = load_project_player_profile(project_id)
    if loaded_profile["sessionCount"] != 2 or loaded_profile["resumedCount"] != 1:
        raise NativeRuntimeError("玩家档案写入后没有正确读回。")

    snapshot = {
        "kind": "auto-resume",
        "savedAt": now_iso(),
        "sceneId": scene.get("id"),
        "sceneName": scene.get("name") or scene.get("id"),
        "blockIndex": 0,
        "variableState": {},
        "stageBackgroundAssetId": None,
        "visibleCharacters": {},
        "currentBgmAssetId": None,
        "finished": False,
        "finishedMessage": "",
        "summaryText": "Native runtime profile self test",
    }
    auto_resume_path = write_project_auto_resume(project_id, snapshot)
    loaded_snapshot = load_project_auto_resume(project_id)
    if not loaded_snapshot or loaded_snapshot.get("sceneId") != scene.get("id"):
        raise NativeRuntimeError("续玩记录写入后没有正确读回。")
    clear_project_auto_resume(project_id)
    if load_project_auto_resume(project_id) is not None:
        raise NativeRuntimeError("续玩记录清除后仍然存在。")
    print(f"Native runtime profile validation passed: profile={profile_path} autoResume={auto_resume_path}")


def exercise_save_load(bundle_dir: Path) -> None:
    payload = load_game_data(bundle_dir / "game_data.json")
    project = payload.get("project") or {}
    formal_slot_count = get_project_formal_save_slot_count(project)
    chapters = payload.get("chapters") or []
    scenes = [scene for chapter in chapters for scene in (chapter.get("scenes") or [])]
    if not scenes:
        raise NativeRuntimeError("没有可用于测试存档的场景。")

    scene = scenes[0]
    snapshot = {
        "kind": "formal",
        "savedAt": now_iso(),
        "sceneId": scene.get("id"),
        "sceneName": scene.get("name") or scene.get("id"),
        "blockIndex": 0,
        "variableState": {
            variable.get("id"): variable.get("defaultValue")
            for variable in (payload.get("variables") or {}).get("variables", [])
            if variable.get("id")
        },
        "stageBackgroundAssetId": None,
        "visibleCharacters": {},
        "currentBgmAssetId": None,
        "finished": False,
        "finishedMessage": "",
        "summaryText": "Native runtime save-load self test",
        "textHistory": [
            {
                "key": "doctor-scene:0:narration:save-load",
                "sceneName": scene.get("name") or scene.get("id"),
                "speakerName": "旁白",
                "text": "Native runtime save-load self test",
                "blockType": "narration",
                "voiceAssetId": "",
            }
        ],
    }

    project_id = str(project.get("projectId") or "untitled_project")
    store = {"quickSave": snapshot, "formalSlots": [snapshot] + [None] * (formal_slot_count - 1)}
    save_path = write_project_save_store(project_id, store)
    loaded = load_project_save_store(project_id, formal_slot_count)
    if loaded.get("quickSave", {}).get("sceneId") != scene.get("id"):
        raise NativeRuntimeError("快速存档写入后没有正确读回。")
    if (loaded.get("formalSlots") or [None])[0].get("sceneId") != scene.get("id"):
        raise NativeRuntimeError("正式存档写入后没有正确读回。")
    if len(loaded.get("quickSave", {}).get("textHistory") or []) != 1:
        raise NativeRuntimeError("存档文本历史写入后没有正确读回。")
    print(f"Native runtime save/load validation passed: {save_path}")


def describe_save_dialog(bundle_dir: Path, page: int = 0) -> None:
    payload = load_game_data(bundle_dir / "game_data.json")
    project = payload.get("project") or {}
    variables = (payload.get("variables") or {}).get("variables") or []
    save_store = load_project_save_store(
        str(project.get("projectId") or "untitled_project"),
        get_project_formal_save_slot_count(project),
    )
    summary = build_save_dialog_page_data(project, save_store, page=page, variables=variables)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def exercise_runtime_settings(bundle_dir: Path) -> None:
    payload = load_game_data(bundle_dir / "game_data.json")
    project = payload.get("project") or {}
    project_id = str(project.get("projectId") or "untitled_project")
    write_project_runtime_settings(
        project_id,
        {
            "themeMode": "dark",
            "displayMode": "fullscreen",
            "textSpeed": "fast",
            "language": "ja-JP",
            "textScalePercent": 110,
            "dialogBoxOpacityPercent": 60,
            "masterVolume": 78,
            "bgmVolume": 65,
            "sfxVolume": 70,
            "voiceVolume": 88,
            "autoPlayWaitForVoice": "on",
        },
    )
    loaded = load_project_runtime_settings(project_id)
    if loaded["themeMode"] != "dark" or loaded["displayMode"] != "fullscreen" or loaded["textSpeed"] != "fast":
        raise NativeRuntimeError("原生 Runtime 设置写入后没有正确读回。")
    if loaded["language"] != "ja-JP":
        raise NativeRuntimeError("原生 Runtime 语言设置读回不正确。")
    if loaded["masterVolume"] != 78 or loaded["voiceVolume"] != 88:
        raise NativeRuntimeError("原生 Runtime 音量设置读回不正确。")
    if loaded["textScalePercent"] != 110 or loaded["dialogBoxOpacityPercent"] != 60:
        raise NativeRuntimeError("原生 Runtime 阅读设置读回不正确。")
    if loaded["autoPlayWaitForVoice"] != "on":
        raise NativeRuntimeError("原生 Runtime 自动播放语音等待设置读回不正确。")
    print(f"Native runtime settings validation passed: {get_project_settings_file_path(project_id)}")


def exercise_archive_progress(bundle_dir: Path) -> None:
    payload = load_game_data(bundle_dir / "game_data.json")
    project = payload.get("project") or {}
    project_id = str(project.get("projectId") or "untitled_project")
    chapters = payload.get("chapters") or []
    assets = (payload.get("assets") or {}).get("assets") or []
    first_chapter_id = str((chapters[0] or {}).get("chapterId") or "")
    bgm_asset_id = next((str(asset.get("id")) for asset in assets if asset.get("type") == "bgm" and asset.get("id")), "")
    cg_asset_id = next((str(asset.get("id")) for asset in assets if asset.get("type") == "cg" and asset.get("id")), "")
    location_asset_id = next((str(asset.get("id")) for asset in assets if asset.get("type") == "background" and asset.get("id")), "")
    characters = (payload.get("characters") or {}).get("characters") or []
    character_id = next((str(character.get("id")) for character in characters if character.get("id")), "")
    valid_character_ids = {str(character.get("id")) for character in characters if character.get("id")}
    ending_scene_id = next((scene_id for scene_id in build_ending_scene_ids(chapters) if scene_id), "")
    narration_id = ""
    voice_replay_id = ""
    relation_id = ""
    for chapter in chapters:
        for scene in chapter.get("scenes") or []:
            encountered_character_ids: list[str] = []
            seen_character_ids: set[str] = set()
            for block_index, block in enumerate(scene.get("blocks") or []):
                speaker_id = str(block.get("speakerId") or "").strip()
                character_ref = str(block.get("characterId") or "").strip()
                for candidate in (speaker_id, character_ref):
                    if candidate and candidate in valid_character_ids and candidate not in seen_character_ids:
                        seen_character_ids.add(candidate)
                        encountered_character_ids.append(candidate)
                if not narration_id and str(block.get("type") or "").strip() == "narration":
                    narration_id = build_narration_archive_entry_id(scene.get("id"), block.get("id"), block_index)
                if not voice_replay_id and block.get("voiceAssetId"):
                    voice_replay_id = build_voice_replay_entry_id(scene.get("id"), block.get("id"), block_index)
                if not relation_id and len(encountered_character_ids) >= 2:
                    relation_id = build_relationship_archive_id(encountered_character_ids[0], encountered_character_ids[1])
            if narration_id and voice_replay_id and relation_id:
                break
        if narration_id and voice_replay_id and relation_id:
            break
    progress = {
        "chapterReplayUnlocked": [first_chapter_id] if first_chapter_id else [],
        "bgmUnlocked": [bgm_asset_id] if bgm_asset_id else [],
        "cgUnlocked": [cg_asset_id] if cg_asset_id else [],
        "locationUnlocked": [location_asset_id] if location_asset_id else [],
        "characterUnlocked": [character_id] if character_id else [],
        "narrationUnlocked": [narration_id] if narration_id else [],
        "relationUnlocked": [relation_id] if relation_id else [],
        "voiceReplayUnlocked": [voice_replay_id] if voice_replay_id else [],
        "endingUnlocked": [ending_scene_id] if ending_scene_id else [],
        "readTextKeys": ["scene_start:1:dialogue:doctor-read-key"],
        "endingCompletionCount": 1 if ending_scene_id else 0,
        "endingLastCompletedAt": "2026-04-24T00:00:00+08:00" if ending_scene_id else None,
    }
    write_project_archive_progress(project_id, progress)
    loaded = load_project_archive_progress(project_id)
    if progress["chapterReplayUnlocked"] != loaded["chapterReplayUnlocked"]:
        raise NativeRuntimeError("章节回放进度写入后没有正确读回。")
    if progress["bgmUnlocked"] != loaded["bgmUnlocked"]:
        raise NativeRuntimeError("音乐鉴赏进度写入后没有正确读回。")
    if progress["cgUnlocked"] != loaded["cgUnlocked"]:
        raise NativeRuntimeError("CG 回想进度写入后没有正确读回。")
    if progress["locationUnlocked"] != loaded["locationUnlocked"]:
        raise NativeRuntimeError("地点图鉴进度写入后没有正确读回。")
    if progress["characterUnlocked"] != loaded["characterUnlocked"]:
        raise NativeRuntimeError("角色图鉴进度写入后没有正确读回。")
    if progress["narrationUnlocked"] != loaded["narrationUnlocked"]:
        raise NativeRuntimeError("旁白摘录进度写入后没有正确读回。")
    if progress["relationUnlocked"] != loaded["relationUnlocked"]:
        raise NativeRuntimeError("关系图鉴进度写入后没有正确读回。")
    if progress["voiceReplayUnlocked"] != loaded["voiceReplayUnlocked"]:
        raise NativeRuntimeError("语音回听进度写入后没有正确读回。")
    if progress["endingUnlocked"] != loaded["endingUnlocked"]:
        raise NativeRuntimeError("结局回放进度写入后没有正确读回。")
    if progress["readTextKeys"] != loaded["readTextKeys"]:
        raise NativeRuntimeError("已读文本进度写入后没有正确读回。")
    if progress["endingCompletionCount"] != loaded["endingCompletionCount"]:
        raise NativeRuntimeError("结局完成次数写入后没有正确读回。")
    print(f"Native runtime archive progress validation passed: {get_project_progress_file_path(project_id)}")


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def get_project_formal_save_slot_count(project: dict | None) -> int:
    runtime_settings = (project or {}).get("runtimeSettings") or {}
    try:
        value = int(runtime_settings.get("formalSaveSlotCount", DEFAULT_FORMAL_SAVE_SLOT_COUNT))
    except Exception:
        value = DEFAULT_FORMAL_SAVE_SLOT_COUNT
    return max(MIN_FORMAL_SAVE_SLOT_COUNT, min(MAX_FORMAL_SAVE_SLOT_COUNT, value))


def clamp_int(value, minimum: int, maximum: int, fallback: int) -> int:
    try:
        numeric = int(round(float(value)))
    except Exception:
        numeric = fallback
    return max(minimum, min(maximum, numeric))


def get_safe_audio_fade_ms(value, fallback: int = 0) -> int:
    return clamp_int(value, 0, 30000, fallback)


def get_safe_volume_percent(value, fallback: int = 100) -> int:
    return clamp_int(value, 0, 100, fallback)


def get_safe_transition_duration_ms(value, fallback: int = TRANSITION_DURATION_DEFAULT_MS) -> int:
    safe_fallback = clamp_int(
        fallback,
        TRANSITION_DURATION_MIN_MS,
        TRANSITION_DURATION_MAX_MS,
        TRANSITION_DURATION_DEFAULT_MS,
    )
    return clamp_int(value, TRANSITION_DURATION_MIN_MS, TRANSITION_DURATION_MAX_MS, safe_fallback)


def get_safe_basic_transition(value) -> str:
    safe_value = str(value or "fade").strip()
    return safe_value if safe_value in NATIVE_BASIC_TRANSITIONS else "fade"


def get_safe_character_transition(value) -> str:
    safe_value = str(value or "fade").strip()
    return safe_value if safe_value in NATIVE_CHARACTER_TRANSITIONS else "fade"


def build_native_transition_state(value, duration_ms, started_at_ms: int, direction: str = "in") -> dict | None:
    transition = get_safe_character_transition(value)
    safe_duration_ms = get_safe_transition_duration_ms(duration_ms)
    if transition == "none" or safe_duration_ms <= 0:
        return None
    return {
        "transition": transition,
        "durationMs": safe_duration_ms,
        "startedAtMs": max(0, int(started_at_ms or 0)),
        "direction": "out" if direction == "out" else "in",
    }


def get_native_transition_progress(state: dict | None, now_ms: int) -> float:
    if not state:
        return 1.0
    duration_ms = max(1, get_safe_transition_duration_ms(state.get("durationMs")))
    started_at_ms = clamp_int(state.get("startedAtMs"), 0, max(0, int(now_ms or 0)), 0)
    return clamp((int(now_ms or 0) - started_at_ms) / duration_ms, 0.0, 1.0)


def ease_out_cubic(progress: float) -> float:
    safe_progress = clamp(progress, 0.0, 1.0)
    return 1.0 - (1.0 - safe_progress) ** 3


def get_safe_music_end_mode(value) -> str:
    safe_value = str(value or "").strip()
    if safe_value in {"until_next_music", "scene_end", "after_block"}:
        return safe_value
    return "until_next_music"


def get_safe_screen_color_grade(source) -> dict:
    grade = source if isinstance(source, dict) else {}
    safe_grade = {}
    for key, fallback in SCREEN_COLOR_GRADE_DEFAULTS.items():
        minimum, maximum = SCREEN_COLOR_GRADE_LIMITS[key]
        safe_grade[key] = clamp_int(grade.get(key), minimum, maximum, fallback)
    return safe_grade


def get_music_scope_from_block(block: dict | None, scene_id: str | None) -> dict:
    source = block or {}
    end_mode = get_safe_music_end_mode(source.get("endMode"))
    end_block_id = str(source.get("endBlockId") or "").strip() if end_mode == "after_block" else ""
    if end_mode == "after_block" and not end_block_id:
        end_mode = "until_next_music"
    return {
        "sceneId": str(scene_id or ""),
        "endMode": end_mode,
        "endBlockId": end_block_id,
        "fadeOutMs": get_safe_audio_fade_ms(source.get("fadeOutMs"), 600),
    }


def parse_hex_color(value, fallback):
    safe_value = str(value or "").strip()
    if len(safe_value) == 7 and safe_value.startswith("#"):
        try:
            return tuple(int(safe_value[index:index + 2], 16) for index in (1, 3, 5))
        except Exception:
            return fallback
    return fallback


def get_safe_frame_slice(value, fallback: dict) -> dict:
    source = value if isinstance(value, dict) else {}
    return {
        "top": clamp_int(source.get("top"), 0, 96, int(fallback.get("top", 18))),
        "right": clamp_int(source.get("right"), 0, 96, int(fallback.get("right", 18))),
        "bottom": clamp_int(source.get("bottom"), 0, 96, int(fallback.get("bottom", 18))),
        "left": clamp_int(source.get("left"), 0, 96, int(fallback.get("left", 18))),
    }


def with_alpha(color, opacity_percent: int) -> tuple[int, int, int, int]:
    alpha = clamp_int(opacity_percent, 0, 100, 100)
    return (*color, int(round(alpha * 2.55)))


def normalize_video_time_seconds(value, fallback: float = 0.0) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = fallback
    if not math.isfinite(numeric):
        numeric = fallback
    return max(0.0, numeric)


def format_video_timestamp(seconds: float | int | None) -> str:
    total_seconds = normalize_video_time_seconds(seconds)
    minutes = int(total_seconds // 60)
    seconds_remainder = total_seconds - minutes * 60
    if seconds_remainder.is_integer():
        return f"{minutes}:{int(seconds_remainder):02d}"
    return f"{minutes}:{seconds_remainder:04.1f}"


def build_video_clip_label(start_time: float, end_time: float) -> str:
    if start_time <= 0 and end_time <= 0:
        return "整段播放"
    return f"{format_video_timestamp(start_time)} -> {format_video_timestamp(end_time) if end_time > 0 else '结尾'}"


def get_safe_project_dialog_box_preset(value) -> str:
    return value if value == "custom" or value in DIALOG_BOX_PRESETS else DEFAULT_DIALOG_BOX_CONFIG["preset"]


def get_safe_project_dialog_box_shape(value) -> str:
    return value if value in {"rounded", "square", "capsule"} else DEFAULT_DIALOG_BOX_CONFIG["shape"]


def get_project_dialog_box_preset_config(preset) -> dict:
    safe_preset = get_safe_project_dialog_box_preset(preset)
    return {
        **DEFAULT_DIALOG_BOX_CONFIG,
        **(DIALOG_BOX_PRESETS.get(safe_preset) or {}),
        "preset": safe_preset,
    }


def get_project_dialog_box_config(project: dict | None) -> dict:
    source = (project or {}).get("dialogBoxConfig") or {}
    base = get_project_dialog_box_preset_config(source.get("preset"))
    return {
        **base,
        "preset": get_safe_project_dialog_box_preset(source.get("preset", base["preset"])),
        "shape": get_safe_project_dialog_box_shape(source.get("shape", base["shape"])),
        "widthPercent": clamp_int(source.get("widthPercent"), 55, 100, base["widthPercent"]),
        "minHeight": clamp_int(source.get("minHeight"), 96, 320, base["minHeight"]),
        "paddingX": clamp_int(source.get("paddingX"), 8, 72, base["paddingX"]),
        "paddingY": clamp_int(source.get("paddingY"), 6, 48, base["paddingY"]),
        "backgroundColor": parse_hex_color(source.get("backgroundColor"), parse_hex_color(base["backgroundColor"], COLOR_PANEL)),
        "backgroundOpacity": clamp_int(source.get("backgroundOpacity"), 0, 100, base["backgroundOpacity"]),
        "borderColor": parse_hex_color(source.get("borderColor"), parse_hex_color(base["borderColor"], COLOR_PANEL_BORDER)),
        "borderOpacity": clamp_int(source.get("borderOpacity"), 0, 100, base["borderOpacity"]),
        "textColor": parse_hex_color(source.get("textColor"), parse_hex_color(base["textColor"], COLOR_TEXT)),
        "speakerColor": parse_hex_color(source.get("speakerColor"), parse_hex_color(base["speakerColor"], COLOR_TEXT)),
        "hintColor": parse_hex_color(source.get("hintColor"), parse_hex_color(base["hintColor"], COLOR_TEXT_MUTED)),
        "blurStrength": clamp_int(source.get("blurStrength"), 0, 24, base["blurStrength"]),
        "borderWidth": clamp_int(source.get("borderWidth"), 0, 4, base["borderWidth"]),
        "shadowStrength": clamp_int(source.get("shadowStrength"), 0, 48, base["shadowStrength"]),
        "panelAssetId": str(source.get("panelAssetId") or "").strip(),
        "panelAssetOpacity": clamp_int(source.get("panelAssetOpacity"), 0, 100, base["panelAssetOpacity"]),
        "panelAssetFit": "contain" if source.get("panelAssetFit") == "contain" else "cover",
        "anchor": get_safe_option(
            source.get("anchor"),
            {"bottom", "center", "top", "free"},
            base["anchor"],
        ),
        "offsetXPercent": clamp_int(source.get("offsetXPercent"), -35, 35, base["offsetXPercent"]),
        "offsetYPercent": clamp_int(source.get("offsetYPercent"), -35, 35, base["offsetYPercent"]),
    }


def get_project_game_ui_config(project: dict | None) -> dict:
    source = (project or {}).get("gameUiConfig") or {}
    base = {**DEFAULT_GAME_UI_CONFIG}
    return {
        **base,
        "preset": get_safe_option(
            source.get("preset"),
            {"stellar", "warm", "paper", "minimal", "custom"},
            base["preset"],
        ),
        "layoutPreset": get_safe_option(
            source.get("layoutPreset"),
            {"balanced", "cinematic", "compact", "minimal", "custom"},
            base["layoutPreset"],
        ),
        "titleLayout": get_safe_option(
            source.get("titleLayout"),
            {"center", "left", "poster"},
            base["titleLayout"],
        ),
        "fontStyle": get_safe_option(source.get("fontStyle"), {"modern", "serif", "rounded"}, base["fontStyle"]),
        "fontFamily": str(source.get("fontFamily") or base.get("fontFamily") or "").strip()[:80],
        "fontAssetId": str(source.get("fontAssetId") or base.get("fontAssetId") or "").strip(),
        "surfaceStyle": get_safe_option(
            source.get("surfaceStyle"),
            {"glass", "solid", "minimal"},
            base["surfaceStyle"],
        ),
        "brandMode": get_safe_option(source.get("brandMode"), {"project", "engine", "hidden"}, base["brandMode"]),
        "sidePanelMode": get_safe_option(
            source.get("sidePanelMode"),
            {"full", "compact", "hidden"},
            base["sidePanelMode"],
        ),
        "sidePanelPosition": get_safe_option(
            source.get("sidePanelPosition"),
            {"right", "left"},
            base["sidePanelPosition"],
        ),
        "topbarPosition": get_safe_option(
            source.get("topbarPosition"),
            {"top", "bottom", "hidden"},
            base["topbarPosition"],
        ),
        "hudPosition": get_safe_option(
            source.get("hudPosition"),
            {"top", "top-left", "top-right", "bottom-left", "bottom-right", "hidden"},
            base["hudPosition"],
        ),
        "titleCardAnchor": get_safe_option(
            source.get("titleCardAnchor"),
            {"center", "left", "right", "top", "bottom", "free"},
            base["titleCardAnchor"],
        ),
        "titleCardOffsetXPercent": clamp_int(
            source.get("titleCardOffsetXPercent"),
            -35,
            35,
            base["titleCardOffsetXPercent"],
        ),
        "titleCardOffsetYPercent": clamp_int(
            source.get("titleCardOffsetYPercent"),
            -35,
            35,
            base["titleCardOffsetYPercent"],
        ),
        "layoutGap": clamp_int(source.get("layoutGap"), 8, 48, base["layoutGap"]),
        "sidePanelWidth": clamp_int(source.get("sidePanelWidth"), 240, 460, base["sidePanelWidth"]),
        "backgroundColor": parse_hex_color(source.get("backgroundColor"), parse_hex_color(base["backgroundColor"], COLOR_BG)),
        "backgroundAccentColor": parse_hex_color(
            source.get("backgroundAccentColor"),
            parse_hex_color(base["backgroundAccentColor"], COLOR_ACCENT),
        ),
        "panelColor": parse_hex_color(source.get("panelColor"), parse_hex_color(base["panelColor"], COLOR_PANEL)),
        "panelOpacity": clamp_int(source.get("panelOpacity"), 35, 100, base["panelOpacity"]),
        "textColor": parse_hex_color(source.get("textColor"), parse_hex_color(base["textColor"], COLOR_TEXT)),
        "mutedTextColor": parse_hex_color(
            source.get("mutedTextColor"),
            parse_hex_color(base["mutedTextColor"], COLOR_TEXT_MUTED),
        ),
        "accentColor": parse_hex_color(source.get("accentColor"), parse_hex_color(base["accentColor"], COLOR_ACCENT)),
        "accentAltColor": parse_hex_color(
            source.get("accentAltColor"),
            parse_hex_color(base["accentAltColor"], COLOR_ACCENT_ALT),
        ),
        "buttonTextColor": parse_hex_color(source.get("buttonTextColor"), parse_hex_color(base["buttonTextColor"], COLOR_TEXT)),
        "borderColor": parse_hex_color(source.get("borderColor"), parse_hex_color(base["borderColor"], COLOR_PANEL_BORDER)),
        "borderOpacity": clamp_int(source.get("borderOpacity"), 0, 100, base["borderOpacity"]),
        "cornerRadius": clamp_int(source.get("cornerRadius"), 4, 42, base["cornerRadius"]),
        "backdropBlur": clamp_int(source.get("backdropBlur"), 0, 28, base["backdropBlur"]),
        "stageVignette": clamp_int(source.get("stageVignette"), 0, 80, base["stageVignette"]),
        "motionIntensity": clamp_int(source.get("motionIntensity"), 0, 100, base["motionIntensity"]),
        "titleBackgroundAssetId": str(source.get("titleBackgroundAssetId") or "").strip(),
        "titleBackgroundFit": "contain" if source.get("titleBackgroundFit") == "contain" else "cover",
        "titleBackgroundOpacity": clamp_int(source.get("titleBackgroundOpacity"), 0, 100, base["titleBackgroundOpacity"]),
        "titleLogoAssetId": str(source.get("titleLogoAssetId") or "").strip(),
        "panelFrameAssetId": str(source.get("panelFrameAssetId") or "").strip(),
        "panelFrameOpacity": clamp_int(source.get("panelFrameOpacity"), 0, 100, base["panelFrameOpacity"]),
        "panelFrameSlice": get_safe_frame_slice(source.get("panelFrameSlice"), base["panelFrameSlice"]),
        "buttonFrameAssetId": str(source.get("buttonFrameAssetId") or "").strip(),
        "buttonHoverFrameAssetId": str(source.get("buttonHoverFrameAssetId") or "").strip(),
        "buttonPressedFrameAssetId": str(source.get("buttonPressedFrameAssetId") or "").strip(),
        "buttonDisabledFrameAssetId": str(source.get("buttonDisabledFrameAssetId") or "").strip(),
        "buttonFrameOpacity": clamp_int(source.get("buttonFrameOpacity"), 0, 100, base["buttonFrameOpacity"]),
        "buttonFrameSlice": get_safe_frame_slice(source.get("buttonFrameSlice"), base["buttonFrameSlice"]),
        "saveSlotFrameAssetId": str(source.get("saveSlotFrameAssetId") or "").strip(),
        "systemPanelFrameAssetId": str(source.get("systemPanelFrameAssetId") or "").strip(),
        "uiOverlayAssetId": str(source.get("uiOverlayAssetId") or "").strip(),
        "uiOverlayOpacity": clamp_int(source.get("uiOverlayOpacity"), 0, 100, base["uiOverlayOpacity"]),
    }


def get_runtime_save_dir() -> Path:
    return Path.home() / SAVE_ROOT_DIR_NAME / SAVE_SUBDIR_NAME


def get_runtime_settings_dir() -> Path:
    return Path.home() / SAVE_ROOT_DIR_NAME / SETTINGS_SUBDIR_NAME


def get_runtime_progress_dir() -> Path:
    return Path.home() / SAVE_ROOT_DIR_NAME / PROGRESS_SUBDIR_NAME


def get_runtime_profile_dir() -> Path:
    return Path.home() / SAVE_ROOT_DIR_NAME / PROFILE_SUBDIR_NAME


def get_runtime_auto_resume_dir() -> Path:
    return Path.home() / SAVE_ROOT_DIR_NAME / AUTO_RESUME_SUBDIR_NAME


def get_runtime_log_dir() -> Path:
    return Path.home() / SAVE_ROOT_DIR_NAME / LOG_SUBDIR_NAME


def get_runtime_screenshot_dir() -> Path:
    return Path.home() / SAVE_ROOT_DIR_NAME / SCREENSHOT_SUBDIR_NAME


def write_runtime_crash_log(game_data_path: Path, error: BaseException, context: str) -> Path:
    log_dir = get_runtime_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    log_path = log_dir / f"runtime-crash-{timestamp}.log"
    lines = [
        "Canvasia Engine Native Runtime Crash Log",
        f"Time: {now_iso()}",
        f"Context: {context}",
        f"Game data: {game_data_path}",
        f"Python: {sys.version.replace(chr(10), ' ')}",
        f"Platform: {platform.platform()}",
        f"Frozen: {bool(getattr(sys, 'frozen', False))}",
        "",
        "Error:",
        f"{type(error).__name__}: {error}",
        "",
        "Traceback:",
        traceback.format_exc(),
        "",
    ]
    log_path.write_text("\n".join(lines), encoding="utf-8")
    return log_path


def wrap_plain_text(text: str, max_chars: int) -> list[str]:
    safe_text = str(text or "")
    lines: list[str] = []
    for raw_line in safe_text.splitlines() or [""]:
        current = raw_line
        while len(current) > max_chars:
            lines.append(current[:max_chars])
            current = current[max_chars:]
        lines.append(current)
    return lines


def show_runtime_error_screen(pygame, message: str, log_path: Path | None) -> None:
    try:
        screen = pygame.display.get_surface()
        if screen is None:
            screen = pygame.display.set_mode((860, 360))
        pygame.display.set_caption("Canvasia Engine Runtime Error")
        font_title = pygame.font.SysFont("Arial", 26, bold=True)
        font_body = pygame.font.SysFont("Arial", 18)
        clock = pygame.time.Clock()
        details = str(log_path) if log_path else "未能写入日志"
        lines = [
            "原生 Runtime 没有成功启动",
            "",
            *wrap_plain_text(message, 54)[:4],
            "",
            "错误日志：",
            *wrap_plain_text(details, 62)[:3],
            "",
            "按 Esc / Return 关闭这个窗口。",
        ]
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                    running = False
            screen.fill(COLOR_BG)
            y = 34
            screen.blit(font_title.render(lines[0], True, COLOR_WARNING), (38, y))
            y += 52
            for line in lines[2:]:
                color = COLOR_TEXT if line else COLOR_TEXT_MUTED
                screen.blit(font_body.render(line, True, color), (38, y))
                y += 26
            pygame.display.flip()
            clock.tick(30)
    except Exception:
        pass


def make_project_save_filename(project_id: str) -> str:
    clean = "".join(character if character.isalnum() or character in {"-", "_"} else "_" for character in project_id)
    clean = clean.strip("_") or "untitled_project"
    return f"{clean}.json"


def get_project_save_file_path(project_id: str) -> Path:
    return get_runtime_save_dir() / make_project_save_filename(project_id)


def get_project_settings_file_path(project_id: str) -> Path:
    return get_runtime_settings_dir() / make_project_save_filename(project_id)


def get_project_progress_file_path(project_id: str) -> Path:
    return get_runtime_progress_dir() / make_project_save_filename(project_id)


def get_project_profile_file_path(project_id: str) -> Path:
    return get_runtime_profile_dir() / make_project_save_filename(project_id)


def get_project_auto_resume_file_path(project_id: str) -> Path:
    return get_runtime_auto_resume_dir() / make_project_save_filename(project_id)


def load_project_save_store(project_id: str, slot_count: int) -> dict:
    save_path = get_project_save_file_path(project_id)
    if not save_path.is_file():
        return {"quickSave": None, "formalSlots": [None] * slot_count}
    try:
        payload = json.loads(save_path.read_text(encoding="utf-8"))
    except Exception:
        return {"quickSave": None, "formalSlots": [None] * slot_count}

    formal_slots = payload.get("formalSlots")
    if not isinstance(formal_slots, list):
        formal_slots = [None] * slot_count
    formal_slots = list(formal_slots[:slot_count])
    while len(formal_slots) < slot_count:
        formal_slots.append(None)
    return {
        "quickSave": payload.get("quickSave"),
        "formalSlots": formal_slots,
    }


def sanitize_player_profile(value: dict | None) -> dict:
    source = value if isinstance(value, dict) else {}

    def clean_optional_time(raw_value):
        safe_value = str(raw_value or "").strip()
        return safe_value or None

    def clean_count(raw_value) -> int:
        try:
            return max(0, int(raw_value or 0))
        except Exception:
            return 0

    return {
        "firstPlayedAt": clean_optional_time(source.get("firstPlayedAt")),
        "lastPlayedAt": clean_optional_time(source.get("lastPlayedAt")),
        "lastEndedAt": clean_optional_time(source.get("lastEndedAt")),
        "totalPlayMs": clean_count(source.get("totalPlayMs")),
        "sessionCount": clean_count(source.get("sessionCount")),
        "resumedCount": clean_count(source.get("resumedCount")),
        "returnToTitleCount": clean_count(source.get("returnToTitleCount")),
    }


def load_project_player_profile(project_id: str) -> dict:
    profile_path = get_project_profile_file_path(project_id)
    if not profile_path.is_file():
        return sanitize_player_profile(DEFAULT_PLAYER_PROFILE)
    try:
        payload = json.loads(profile_path.read_text(encoding="utf-8"))
    except Exception:
        return sanitize_player_profile(DEFAULT_PLAYER_PROFILE)
    return sanitize_player_profile(payload)


def write_project_player_profile(project_id: str, profile: dict) -> Path:
    profile_dir = get_runtime_profile_dir()
    profile_dir.mkdir(parents=True, exist_ok=True)
    profile_path = get_project_profile_file_path(project_id)
    safe_profile = sanitize_player_profile(profile)
    profile_path.write_text(json.dumps(safe_profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return profile_path


def sanitize_text_history_entries(value: object, limit: int = SNAPSHOT_TEXT_HISTORY_LIMIT) -> list[dict]:
    if not isinstance(value, list):
        return []
    result: list[dict] = []
    for item in value[-limit:]:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        key = str(item.get("key") or "").strip()[:180]
        result.append(
            {
                "key": key,
                "sceneName": str(item.get("sceneName") or "").strip()[:80],
                "speakerName": str(item.get("speakerName") or "旁白").strip()[:80],
                "text": text[:2000],
                "blockType": str(item.get("blockType") or "").strip()[:40],
                "voiceAssetId": str(item.get("voiceAssetId") or "").strip()[:120],
            }
        )
    return result


def sanitize_auto_resume_snapshot(value: dict | None) -> dict | None:
    if not isinstance(value, dict):
        return None
    scene_id = str(value.get("sceneId") or "").strip()
    if not scene_id and not bool(value.get("finished")):
        return None
    snapshot = dict(value)
    snapshot["kind"] = str(snapshot.get("kind") or "auto-resume")
    snapshot["savedAt"] = str(snapshot.get("savedAt") or now_iso())
    snapshot["sceneId"] = scene_id
    snapshot["sceneName"] = str(snapshot.get("sceneName") or scene_id or "未命名场景")
    try:
        block_index = int(snapshot.get("blockIndex") or 0)
    except Exception:
        block_index = 0
    snapshot["blockIndex"] = max(0, block_index)
    snapshot["summaryText"] = str(snapshot.get("summaryText") or "").strip()
    snapshot["finished"] = bool(snapshot.get("finished"))
    snapshot["finishedMessage"] = str(snapshot.get("finishedMessage") or "")
    if not isinstance(snapshot.get("variableState"), dict):
        snapshot["variableState"] = {}
    if not isinstance(snapshot.get("visibleCharacters"), dict):
        snapshot["visibleCharacters"] = {}
    snapshot["textHistory"] = sanitize_text_history_entries(snapshot.get("textHistory"))
    return snapshot


def load_project_auto_resume(project_id: str) -> dict | None:
    auto_resume_path = get_project_auto_resume_file_path(project_id)
    if not auto_resume_path.is_file():
        return None
    try:
        payload = json.loads(auto_resume_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return sanitize_auto_resume_snapshot(payload)


def write_project_auto_resume(project_id: str, snapshot: dict) -> Path:
    auto_resume_dir = get_runtime_auto_resume_dir()
    auto_resume_dir.mkdir(parents=True, exist_ok=True)
    auto_resume_path = get_project_auto_resume_file_path(project_id)
    safe_snapshot = sanitize_auto_resume_snapshot(snapshot)
    if safe_snapshot is None:
        safe_snapshot = {"kind": "auto-resume", "savedAt": now_iso(), "sceneId": "", "sceneName": "未命名场景", "blockIndex": 0}
    auto_resume_path.write_text(json.dumps(safe_snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return auto_resume_path


def clear_project_auto_resume(project_id: str) -> Path:
    auto_resume_path = get_project_auto_resume_file_path(project_id)
    try:
        auto_resume_path.unlink()
    except FileNotFoundError:
        pass
    return auto_resume_path


def sanitize_archive_progress(value: dict | None) -> dict:
    source = value or {}

    def clean_id_list(raw_value, limit: int | None = None) -> list[str]:
        if not isinstance(raw_value, list):
            return []
        result = []
        for item in raw_value:
            safe_item = str(item or "").strip()[:180]
            if safe_item and safe_item not in result:
                result.append(safe_item)
            if limit and len(result) >= limit:
                break
        return result

    return {
        "chapterReplayUnlocked": clean_id_list(source.get("chapterReplayUnlocked")),
        "bgmUnlocked": clean_id_list(source.get("bgmUnlocked")),
        "cgUnlocked": clean_id_list(source.get("cgUnlocked")),
        "locationUnlocked": clean_id_list(source.get("locationUnlocked")),
        "characterUnlocked": clean_id_list(source.get("characterUnlocked")),
        "narrationUnlocked": clean_id_list(source.get("narrationUnlocked")),
        "relationUnlocked": clean_id_list(source.get("relationUnlocked")),
        "voiceReplayUnlocked": clean_id_list(source.get("voiceReplayUnlocked")),
        "endingUnlocked": clean_id_list(source.get("endingUnlocked")),
        "readTextKeys": clean_id_list(source.get("readTextKeys"), READ_TEXT_KEY_LIMIT),
        "endingCompletionCount": max(0, int(source.get("endingCompletionCount") or 0)),
        "endingLastCompletedAt": str(source.get("endingLastCompletedAt") or "").strip() or None,
    }


def load_project_archive_progress(project_id: str) -> dict:
    progress_path = get_project_progress_file_path(project_id)
    if not progress_path.is_file():
        return sanitize_archive_progress(None)
    try:
        payload = json.loads(progress_path.read_text(encoding="utf-8"))
    except Exception:
        return sanitize_archive_progress(None)
    return sanitize_archive_progress(payload)


def write_project_archive_progress(project_id: str, progress: dict) -> Path:
    progress_dir = get_runtime_progress_dir()
    progress_dir.mkdir(parents=True, exist_ok=True)
    progress_path = get_project_progress_file_path(project_id)
    safe_payload = sanitize_archive_progress(progress)
    progress_path.write_text(json.dumps(safe_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return progress_path


def sanitize_runtime_player_settings(value: dict | None) -> dict:
    source = value or {}
    theme_mode = str(source.get("themeMode") or DEFAULT_RUNTIME_PLAYER_SETTINGS["themeMode"]).strip().lower()
    if theme_mode not in RUNTIME_THEME_MODES:
        theme_mode = DEFAULT_RUNTIME_PLAYER_SETTINGS["themeMode"]
    display_mode = str(source.get("displayMode") or DEFAULT_RUNTIME_PLAYER_SETTINGS["displayMode"]).strip().lower()
    if display_mode not in RUNTIME_DISPLAY_MODES:
        display_mode = DEFAULT_RUNTIME_PLAYER_SETTINGS["displayMode"]
    text_speed = get_safe_text_speed(source.get("textSpeed"), DEFAULT_RUNTIME_PLAYER_SETTINGS["textSpeed"])
    language = normalize_language_code(source.get("language"), "")
    auto_play_wait_for_voice = str(
        source.get("autoPlayWaitForVoice") or DEFAULT_RUNTIME_PLAYER_SETTINGS["autoPlayWaitForVoice"]
    ).strip().lower()
    if auto_play_wait_for_voice not in RUNTIME_TOGGLE_MODES:
        auto_play_wait_for_voice = DEFAULT_RUNTIME_PLAYER_SETTINGS["autoPlayWaitForVoice"]
    return {
        "themeMode": theme_mode,
        "displayMode": display_mode,
        "textSpeed": text_speed,
        "language": language,
        "textScalePercent": clamp_int(
            source.get("textScalePercent"),
            min(TEXT_SCALE_PRESETS),
            max(TEXT_SCALE_PRESETS),
            DEFAULT_RUNTIME_PLAYER_SETTINGS["textScalePercent"],
        ),
        "dialogBoxOpacityPercent": clamp_int(
            source.get("dialogBoxOpacityPercent"),
            min(DIALOG_BOX_OPACITY_PRESETS),
            max(DIALOG_BOX_OPACITY_PRESETS),
            DEFAULT_RUNTIME_PLAYER_SETTINGS["dialogBoxOpacityPercent"],
        ),
        "autoPlayDelayMs": clamp_int(
            source.get("autoPlayDelayMs"),
            min(AUTO_PLAY_DELAY_PRESETS),
            max(AUTO_PLAY_DELAY_PRESETS),
            DEFAULT_RUNTIME_PLAYER_SETTINGS["autoPlayDelayMs"],
        ),
        "autoPlayWaitForVoice": auto_play_wait_for_voice,
        "masterVolume": clamp_int(source.get("masterVolume"), 0, 100, DEFAULT_RUNTIME_PLAYER_SETTINGS["masterVolume"]),
        "bgmVolume": clamp_int(source.get("bgmVolume"), 0, 100, DEFAULT_RUNTIME_PLAYER_SETTINGS["bgmVolume"]),
        "sfxVolume": clamp_int(source.get("sfxVolume"), 0, 100, DEFAULT_RUNTIME_PLAYER_SETTINGS["sfxVolume"]),
        "voiceVolume": clamp_int(source.get("voiceVolume"), 0, 100, DEFAULT_RUNTIME_PLAYER_SETTINGS["voiceVolume"]),
    }


def get_safe_text_speed(value: object, fallback: str = "normal") -> str:
    safe_fallback = fallback if fallback in TEXT_SPEED_PRESETS else DEFAULT_RUNTIME_PLAYER_SETTINGS["textSpeed"]
    text_speed = str(value or safe_fallback).strip().lower()
    return text_speed if text_speed in TEXT_SPEED_PRESETS else safe_fallback


def is_regional_indicator_symbol(char: str) -> bool:
    if not char:
        return False
    return 0x1F1E6 <= ord(char[0]) <= 0x1F1FF


def is_typewriter_grapheme_extension(char: str) -> bool:
    if not char:
        return False
    code_point = ord(char[0])
    return (
        unicodedata.category(char[0]) in {"Mn", "Mc", "Me"}
        or 0xFE00 <= code_point <= 0xFE0F
        or 0xE0100 <= code_point <= 0xE01EF
        or 0x1F3FB <= code_point <= 0x1F3FF
    )


def get_next_typewriter_cluster_index(text: str, current_index: int) -> int:
    safe_text = str(text or "")
    safe_index = max(0, min(len(safe_text), int(current_index or 0)))
    if safe_index >= len(safe_text):
        return len(safe_text)

    next_index = safe_index + 1

    if (
        is_regional_indicator_symbol(safe_text[safe_index])
        and next_index < len(safe_text)
        and is_regional_indicator_symbol(safe_text[next_index])
    ):
        return next_index + 1

    while next_index < len(safe_text):
        current_char = safe_text[next_index]
        previous_char = safe_text[next_index - 1] if next_index > 0 else ""

        if is_typewriter_grapheme_extension(current_char):
            next_index += 1
            continue
        if previous_char == "\u200d":
            next_index += 1
            continue
        if current_char == "\u200d":
            next_index = min(len(safe_text), next_index + 2)
            continue
        break

    return next_index


def get_next_typewriter_index(text: str, current_index: int) -> int:
    safe_text = str(text or "")
    safe_index = max(0, min(len(safe_text), int(current_index or 0)))
    if safe_index >= len(safe_text):
        return len(safe_text)

    next_index = get_next_typewriter_cluster_index(safe_text, safe_index)
    current_char = safe_text[safe_index]
    next_index = include_typewriter_leading_follower(safe_text, safe_index, next_index)

    if re.match(r"[A-Za-z0-9]", current_char):
        grouped = 1
        while (
            next_index < len(safe_text)
            and grouped < 3
            and re.match(r"[A-Za-z0-9]", safe_text[next_index])
        ):
            next_index = get_next_typewriter_cluster_index(safe_text, next_index)
            grouped += 1

    next_index = include_typewriter_trailing_closers(safe_text, next_index)

    while next_index < len(safe_text) and safe_text[next_index].isspace():
        next_index = get_next_typewriter_cluster_index(safe_text, next_index)
    return next_index


def include_typewriter_leading_follower(text: str, current_index: int, index: int) -> int:
    safe_text = str(text or "")
    safe_current_index = max(0, min(len(safe_text), int(current_index or 0)))
    next_index = max(0, min(len(safe_text), int(index or 0)))
    if safe_current_index >= len(safe_text) or safe_text[safe_current_index] not in TYPEWRITER_LEADING_OPENERS:
        return next_index

    while next_index < len(safe_text) and safe_text[next_index] in TYPEWRITER_LEADING_OPENERS:
        next_index = get_next_typewriter_cluster_index(safe_text, next_index)

    return get_next_typewriter_cluster_index(safe_text, next_index) if next_index < len(safe_text) else next_index


def include_typewriter_trailing_closers(text: str, index: int) -> int:
    safe_text = str(text or "")
    next_index = max(0, min(len(safe_text), int(index or 0)))
    while next_index < len(safe_text) and safe_text[next_index] in TYPEWRITER_TRAILING_CLOSERS:
        next_index += 1
    return next_index


def get_typewriter_punctuation_pause_ms(text: str, full_text: str = "") -> int:
    anchor_text = get_typewriter_pause_anchor_text(text)
    anchor_char = get_typewriter_pause_anchor_char(text)
    if re.search(r"(?:\.{3,}|…+)$", anchor_text):
        return TYPEWRITER_ELLIPSIS_PAUSE_MS
    if anchor_char == "." and is_typewriter_inline_period(anchor_text, full_text):
        return 0
    if anchor_char == "." and is_typewriter_abbreviation_period(anchor_text, full_text):
        return 0
    if anchor_char in "。！？!?.":
        return TYPEWRITER_SENTENCE_PAUSE_MS
    if anchor_char in "…—-":
        return TYPEWRITER_ELLIPSIS_PAUSE_MS
    if anchor_char in "，、；;：:,":
        return TYPEWRITER_CLAUSE_PAUSE_MS
    return 0


def get_typewriter_pause_anchor_text(text: str) -> str:
    chars = list(str(text or "").rstrip())
    while len(chars) > 1 and chars[-1] in TYPEWRITER_TRAILING_CLOSERS:
        chars.pop()
    return "".join(chars)


def get_typewriter_pause_anchor_char(text: str) -> str:
    chars = list(get_typewriter_pause_anchor_text(text))
    return chars[-1] if chars else ""


def is_typewriter_inline_period(anchor_text: str, full_text: str = "") -> bool:
    safe_anchor_text = str(anchor_text or "")
    safe_full_text = str(full_text or "")
    previous_char = safe_anchor_text[-2] if len(safe_anchor_text) >= 2 else ""
    next_char = safe_full_text[len(safe_anchor_text) : len(safe_anchor_text) + 1]
    return bool(re.match(r"[A-Za-z0-9]", previous_char) and re.match(r"[A-Za-z0-9]", next_char))


def is_typewriter_abbreviation_period(anchor_text: str, full_text: str = "") -> bool:
    safe_anchor_text = str(anchor_text or "")
    safe_full_text = str(full_text or "")
    token_match = re.search(r"([A-Za-z](?:[A-Za-z]|\.)*)\.$", safe_anchor_text)
    token = token_match.group(1).lower() if token_match else ""
    next_char = safe_full_text[len(safe_anchor_text) : len(safe_anchor_text) + 1]
    return token in TYPEWRITER_PERIOD_ABBREVIATIONS and bool(next_char and next_char.isspace())


def get_native_typewriter_step_delay_ms(speed: str, visible_text: str = "", full_text: str = "") -> int:
    safe_speed = get_safe_text_speed(speed)
    chars_per_second = TEXT_SPEED_PRESETS.get(safe_speed, TEXT_SPEED_PRESETS["normal"])
    if chars_per_second >= TEXT_SPEED_PRESETS["instant"]:
        return 0
    base_delay = max(1, int(round(1000 / max(1, chars_per_second))))
    return base_delay + get_typewriter_punctuation_pause_ms(visible_text, full_text)


def load_project_runtime_settings(project_id: str) -> dict:
    settings_path = get_project_settings_file_path(project_id)
    if not settings_path.is_file():
        return dict(DEFAULT_RUNTIME_PLAYER_SETTINGS)
    try:
        payload = json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception:
        return dict(DEFAULT_RUNTIME_PLAYER_SETTINGS)
    return sanitize_runtime_player_settings(payload)


def write_project_runtime_settings(project_id: str, settings: dict) -> Path:
    settings_dir = get_runtime_settings_dir()
    settings_dir.mkdir(parents=True, exist_ok=True)
    settings_path = get_project_settings_file_path(project_id)
    safe_settings = sanitize_runtime_player_settings(settings)
    settings_path.write_text(json.dumps(safe_settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return settings_path


def format_snapshot_saved_at(saved_at: str | None) -> str:
    if not saved_at:
        return "尚未保存"
    try:
        parsed = datetime.fromisoformat(str(saved_at))
    except Exception:
        return str(saved_at)
    return parsed.strftime("%m-%d %H:%M")


def format_play_duration(milliseconds: int | float | None) -> str:
    try:
        total_seconds = max(0, int(float(milliseconds or 0) // 1000))
    except Exception:
        total_seconds = 0
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    if hours:
        return f"{hours} 小时 {minutes} 分钟"
    if minutes:
        return f"{minutes} 分钟 {seconds} 秒"
    return f"{seconds} 秒"


def format_runtime_variable_value(variable: dict | None, value: object) -> str:
    coerced_value = coerce_runtime_variable_value(variable, value)
    if isinstance(coerced_value, bool):
        return "开" if coerced_value else "关"
    if isinstance(coerced_value, float) and int(coerced_value) == coerced_value:
        return str(int(coerced_value))
    return str(coerced_value)


def build_variable_summary_text(
    variables: list[dict] | None,
    variable_state: dict | None,
    *,
    limit: int = 3,
) -> str:
    if not variables or not isinstance(variable_state, dict):
        return ""
    parts: list[str] = []
    for variable in variables:
        if not isinstance(variable, dict):
            continue
        variable_id = str(variable.get("id") or "").strip()
        if not variable_id or variable_id not in variable_state:
            continue
        variable_name = str(variable.get("name") or variable_id).strip() or variable_id
        parts.append(f"{variable_name}:{format_runtime_variable_value(variable, variable_state.get(variable_id))}")
        if len(parts) >= limit:
            break
    if not parts:
        return ""
    remaining_count = max(0, len([variable for variable in variables if isinstance(variable, dict) and variable.get("id")]) - len(parts))
    suffix = f" 等 {remaining_count + len(parts)} 项" if remaining_count > 0 else ""
    return " / ".join(parts) + suffix


def build_save_dialog_page_data(
    project: dict | None,
    save_store: dict | None,
    page: int = 0,
    page_size: int = SAVE_DIALOG_PAGE_SIZE,
    variables: list[dict] | None = None,
) -> dict:
    slot_count = get_project_formal_save_slot_count(project)
    safe_page_size = max(1, int(page_size or SAVE_DIALOG_PAGE_SIZE))
    page_count = max(1, (slot_count + safe_page_size - 1) // safe_page_size)
    current_page = max(0, min(page_count - 1, int(page or 0)))
    start = current_page * safe_page_size
    end = min(slot_count, start + safe_page_size)
    formal_slots = (save_store or {}).get("formalSlots") or [None] * slot_count
    formal_slots = list(formal_slots[:slot_count])
    while len(formal_slots) < slot_count:
        formal_slots.append(None)

    visible_slots = []
    for slot_index in range(start, end):
        snapshot = formal_slots[slot_index]
        scene_name = ""
        summary_text = "空位"
        saved_at = "尚未保存"
        if snapshot:
            scene_name = str(snapshot.get("sceneName") or snapshot.get("sceneId") or f"存档 {slot_index + 1}")
            summary_text = str(snapshot.get("summaryText") or "").strip() or "当前没有摘要。"
            saved_at = format_snapshot_saved_at(snapshot.get("savedAt"))
            variable_summary_text = str(snapshot.get("variableSummaryText") or "").strip() or build_variable_summary_text(
                variables,
                snapshot.get("variableState") if isinstance(snapshot, dict) else None,
            )
        else:
            variable_summary_text = ""
        visible_slots.append(
            {
                "slotIndex": slot_index,
                "label": f"正式存档 {slot_index + 1}",
                "isEmpty": snapshot is None,
                "sceneName": scene_name,
                "summaryText": summary_text,
                "variableSummaryText": variable_summary_text,
                "savedAt": saved_at,
                "finished": bool(snapshot.get("finished")) if snapshot else False,
            }
        )

    quick_save = (save_store or {}).get("quickSave")
    quick_variable_summary = ""
    if quick_save:
        quick_variable_summary = str(quick_save.get("variableSummaryText") or "").strip() or build_variable_summary_text(
            variables,
            quick_save.get("variableState") if isinstance(quick_save, dict) else None,
        )
    quick_summary = {
        "isEmpty": quick_save is None,
        "sceneName": str((quick_save or {}).get("sceneName") or (quick_save or {}).get("sceneId") or ""),
        "summaryText": str((quick_save or {}).get("summaryText") or "").strip() or ("空" if quick_save is None else "当前没有摘要。"),
        "variableSummaryText": quick_variable_summary,
        "savedAt": format_snapshot_saved_at((quick_save or {}).get("savedAt")),
    }
    return {
        "slotCount": slot_count,
        "pageSize": safe_page_size,
        "pageCount": page_count,
        "page": current_page,
        "startIndex": start,
        "endIndex": end,
        "quickSave": quick_summary,
        "visibleSlots": visible_slots,
    }


def write_project_save_store(project_id: str, save_store: dict) -> Path:
    save_dir = get_runtime_save_dir()
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = get_project_save_file_path(project_id)
    save_path.write_text(json.dumps(save_store, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return save_path


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def get_safe_character_stage(source: dict | None) -> dict:
    raw = source if isinstance(source, dict) else {}

    def read_number(key: str, fallback: float, minimum: float, maximum: float) -> float:
        try:
            value = float(raw.get(key, fallback))
        except (TypeError, ValueError):
            value = fallback
        return clamp(value, minimum, maximum)

    def read_bool(key: str, fallback: bool = False) -> bool:
        value = raw.get(key, fallback)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "on"}:
                return True
            if normalized in {"false", "0", "no", "off", ""}:
                return False
        return fallback

    return {
        "offsetX": round(read_number("offsetX", 0, -60, 60)),
        "offsetY": round(read_number("offsetY", 0, -45, 45)),
        "scale": round(read_number("scale", 100, 45, 220)),
        "opacity": round(read_number("opacity", 100, 0, 100)),
        "layer": round(read_number("layer", 0, -10, 10)),
        "flipX": read_bool("flipX"),
    }


def get_block_label(block_type: str) -> str:
    return {
        "dialogue": "台词",
        "narration": "旁白",
        "choice": "选项",
        "jump": "跳转",
        "condition": "条件判断",
        "background": "背景",
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
        "screen_filter": "画面滤镜",
        "depth_blur": "景深模糊",
    }.get(block_type, block_type or "未知")


def get_asset_runtime_path(bundle_dir: Path, asset: dict | None) -> Path | None:
    if not asset or asset.get("isMissing"):
        return None
    export_url = str(asset.get("exportUrl") or "").strip()
    if not export_url:
        return None
    candidate = bundle_dir / export_url
    return candidate if candidate.is_file() else None


def split_wrap_tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9]+(?:[._:/@+-][A-Za-z0-9]+)*|\s+|.", str(text or ""), flags=re.DOTALL)


def append_wrapped_token(font, lines: list[str], current: str, token: str, max_width: int) -> str:
    if token.isspace():
        return current + " " if current and not current.endswith(" ") else current

    if not current and font.size(token)[0] <= max_width:
        return token
    if not current:
        for char in token:
            char_candidate = current + char
            if current and font.size(char_candidate)[0] > max_width:
                lines.append(current.rstrip())
                current = char
            else:
                current = char_candidate
        return current

    candidate = current + token
    if font.size(candidate)[0] <= max_width:
        return candidate

    lines.append(current.rstrip())
    current = ""
    if font.size(token)[0] <= max_width:
        return token

    for char in token:
        char_candidate = current + char
        if current and font.size(char_candidate)[0] > max_width:
            lines.append(current.rstrip())
            current = char
        else:
            current = char_candidate
    return current


def wrap_text(font, text: str, max_width: int) -> list[str]:
    if not text:
        return [""]
    if max_width <= 0:
        return [str(text or "")]

    lines: list[str] = []
    raw_lines = str(text or "").splitlines()
    for raw_line in raw_lines or [""]:
        if raw_line == "":
            lines.append("")
            continue
        current = ""
        for token in split_wrap_tokens(raw_line):
            current = append_wrapped_token(font, lines, current, token, max_width)
        if current or not lines:
            lines.append(current.rstrip())
    return lines or [str(text or "")]


def ellipsize_text(font, text: str, max_width: int, suffix: str = "…") -> str:
    safe_text = str(text or "")
    if font.size(safe_text)[0] <= max_width:
        return safe_text
    if font.size(suffix)[0] > max_width:
        return ""
    while safe_text and font.size(safe_text.rstrip() + suffix)[0] > max_width:
        safe_text = safe_text[:-1]
    return safe_text.rstrip() + suffix


class NativeRuntimePlayer:
    def __init__(self, pygame, game_data_path: Path) -> None:
        self.pygame = pygame
        self.bundle_dir = game_data_path.parent
        self.data = load_game_data(game_data_path)
        self.project = self.data.get("project") or {}
        self.assets = (self.data.get("assets") or {}).get("assets") or []
        self.characters = (self.data.get("characters") or {}).get("characters") or []
        self.variables = (self.data.get("variables") or {}).get("variables") or []
        self.variables_by_id = {str(variable.get("id")): variable for variable in self.variables if variable.get("id")}
        self.chapters = self.data.get("chapters") or []
        self.build_info = self.data.get("buildInfo") or {}
        self.i18n = self.data.get("i18n") if isinstance(self.data.get("i18n"), dict) else {}
        self.default_language = normalize_language_code(
            self.i18n.get("defaultLanguage") or self.project.get("language"),
            DEFAULT_PROJECT_LANGUAGE,
        )
        self.fallback_language = normalize_language_code(self.i18n.get("fallbackLanguage"), self.default_language)
        self.supported_languages = normalize_supported_languages(
            self.i18n.get("supportedLanguages") or self.project.get("supportedLanguages"),
            self.default_language,
        )
        self.language_labels = {
            **RUNTIME_LANGUAGE_LABELS,
            **(self.i18n.get("languageLabels") if isinstance(self.i18n.get("languageLabels"), dict) else {}),
        }
        self.current_language = self.default_language
        self.dialog_box_config = get_project_dialog_box_config(self.project)
        self.game_ui_config = get_project_game_ui_config(self.project)

        self.assets_by_id = {asset.get("id"): asset for asset in self.assets if asset.get("id")}
        self.characters_by_id = {character.get("id"): character for character in self.characters if character.get("id")}
        self.scenes_by_id = {}
        self.scene_order = []
        for chapter in self.chapters:
            for scene in chapter.get("scenes", []) or []:
                scene_id = scene.get("id")
                if scene_id:
                    self.scenes_by_id[scene_id] = scene
                    self.scene_order.append(scene_id)

        if not self.scenes_by_id:
            raise NativeRuntimeError("游戏数据里没有任何场景。")

        resolution = self.project.get("resolution") or {}
        self.width = int(resolution.get("width") or 1280)
        self.height = int(resolution.get("height") or 720)
        self.formal_save_slot_count = get_project_formal_save_slot_count(self.project)
        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.active_display_mode = "windowed"
        pygame.display.set_caption(f"{self.project.get('title') or 'Canvasia Engine'} · 原生 Runtime")

        self.font_source_status = "系统字体"
        self.font_small = self._create_font(22)
        self.font_body = self._create_font(30)
        self.font_title = self._create_font(36, bold=True)
        self.font_ui = self._create_font(18)
        self.active_text_scale_percent = 100
        self.image_cache: dict[str, object] = {}
        self.image_file_cache: dict[str, object] = {}
        self.sound_cache: dict[str, object] = {}
        self.current_bgm_asset_id: str | None = None
        self.current_bgm_volume_percent = 100
        self.current_bgm_scope: dict | None = None
        self.current_voice_channel = None
        self.current_voice_volume_percent = 100
        self.project_id = str(self.project.get("projectId") or "untitled_project")
        self.save_store = load_project_save_store(self.project_id, self.formal_save_slot_count)
        self.save_file_path = get_project_save_file_path(self.project_id)
        self.runtime_settings = load_project_runtime_settings(self.project_id)
        self.apply_runtime_language_setting()
        self.settings_file_path = get_project_settings_file_path(self.project_id)
        self.archive_progress = load_project_archive_progress(self.project_id)
        self.progress_file_path = get_project_progress_file_path(self.project_id)
        loaded_read_text_keys = list(self.archive_progress.get("readTextKeys") or [])
        self.player_profile = load_project_player_profile(self.project_id)
        self.profile_file_path = get_project_profile_file_path(self.project_id)
        self.auto_resume_snapshot = load_project_auto_resume(self.project_id)
        self.auto_resume_file_path = get_project_auto_resume_file_path(self.project_id)
        self.auto_resume_write_enabled = self.auto_resume_snapshot is None
        self.profile_session_started_at_ms = 0
        self.overlay_mode: str | None = None
        self.overlay_page = 0
        self.overlay_focus_index = 0
        self.overlay_hotspots: list[dict] = []
        self.video_hotspots: list[dict] = []
        self.video_preview_frame_cache: dict[str, dict] = {}
        self.embedded_video_playback: PyAvSynchronizedVideoPlayback | OpenCvEmbeddedVideoPlayback | None = None
        self.text_history: list[dict] = []
        self.text_history_seen_keys: set[str] = set()
        self.read_text_key_order: list[str] = loaded_read_text_keys[-READ_TEXT_KEY_LIMIT:]
        self.read_text_keys: set[str] = set(self.read_text_key_order)
        self.history_scroll_index = 0
        self.auto_play_enabled = False
        self.auto_play_deadline_ms = 0
        self.skip_read_enabled = False
        self.skip_deadline_ms = 0
        self.ui_hidden = False
        self.system_menu_index = 0
        self.title_menu_index = 0
        self.settings_menu_index = 0
        self.archive_selection_index = 0
        self.current_archive_key = "chapters"
        self.archive_detail_key: str | None = None
        self.archive_detail_entry: dict | None = None
        self.current_line_started_at_ms = 0
        self.current_line_next_reveal_at_ms = 0
        self.current_line_full_text = ""
        self.current_line_revealed_chars = 0
        self.runtime_elapsed_seconds = 0.0
        self.scene3d_preview_yaw = float(DEFAULT_SCENE3D_PREVIEW["yaw"])
        self.scene3d_preview_pitch = float(DEFAULT_SCENE3D_PREVIEW["pitch"])
        self.scene3d_preview_zoom = float(DEFAULT_SCENE3D_PREVIEW["zoom"])
        self.scene3d_preview_interaction_enabled = bool(DEFAULT_SCENE3D_PREVIEW["interactionEnabled"])
        self.active_particle_effect: dict | None = None
        self.particle_items: list[dict] = []
        self.screen_shake_effect: dict | None = None
        self.screen_flash_effect: dict | None = None
        self.screen_fade_effect: dict | None = None
        self.camera_zoom_effect: dict | None = None
        self.camera_pan_effect: dict | None = None
        self.screen_filter_effect: dict | None = None
        self.depth_blur_effect: dict | None = None

        self.variable_state = self.build_initial_variable_state()
        self.stage_background_asset_id: str | None = None
        self.visible_characters: dict[str, dict] = {}
        self.background_transition: dict | None = None
        self.leaving_characters: dict[str, dict] = {}
        self.current_scene_id = self.project.get("entrySceneId") or self.scene_order[0]
        if self.current_scene_id not in self.scenes_by_id:
            self.current_scene_id = self.scene_order[0]
        self.unlock_current_chapter_replay()
        self.current_block_index = 0
        self.current_line: dict | None = None
        self.current_choices: list[dict] | None = None
        self.current_choice_index = 0
        self.title_screen_active = False
        self.finished = False
        self.finished_message = ""
        self.status_message = "正在初始化原生 Runtime…"

        self._initialize_audio()
        self.apply_runtime_settings()
        self.record_player_session_start()
        self.open_title_screen()

    def get_project_font_asset_path(self) -> Path | None:
        font_asset_id = str(self.game_ui_config.get("fontAssetId") or "").strip()
        if not font_asset_id:
            return None
        asset = self.assets_by_id.get(font_asset_id)
        asset_path = get_asset_runtime_path(self.bundle_dir, asset)
        if not asset_path or asset_path.suffix.lower() not in SUPPORTED_FONT_EXTENSIONS:
            return None
        return asset_path

    def get_font_candidate_names(self) -> list[str]:
        explicit_family = str(self.game_ui_config.get("fontFamily") or "").strip()
        font_style = str(self.game_ui_config.get("fontStyle") or "modern")
        style_candidates = {
            "serif": ["Noto Serif CJK SC", "Source Han Serif SC", "Songti SC", "SimSun", "STSong"],
            "rounded": ["PingFang SC", "Microsoft YaHei UI", "Noto Sans CJK SC", "Arial Rounded MT Bold"],
            "modern": ["PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans CJK SC", "Source Han Sans SC"],
        }.get(font_style, [])
        fallback_candidates = ["WenQuanYi Zen Hei", "SimHei", "Arial Unicode MS", "Arial"]
        candidates = []
        for name in [explicit_family, *style_candidates, *fallback_candidates]:
            if name and name not in candidates:
                candidates.append(name)
        return candidates

    def _create_font(self, size: int, bold: bool = False):
        font_asset_path = self.get_project_font_asset_path()
        if font_asset_path:
            try:
                font = self.pygame.font.Font(str(font_asset_path), size)
                if bold and hasattr(font, "set_bold"):
                    font.set_bold(True)
                self.font_source_status = f"项目字体：{font_asset_path.name}"
                return font
            except Exception:
                self.font_source_status = "项目字体加载失败，已回退系统字体"

        candidates = self.get_font_candidate_names()
        for name in candidates:
            try:
                font = self.pygame.font.SysFont(name, size, bold=bold)
                if font:
                    if not self.font_source_status.startswith("项目字体加载失败"):
                        self.font_source_status = f"系统字体：{name}"
                    return font
            except Exception:
                continue
        self.font_source_status = "Pygame 默认字体"
        return self.pygame.font.Font(None, size)

    def get_runtime_text_scale_percent(self) -> int:
        return clamp_int(
            self.runtime_settings.get("textScalePercent"),
            min(TEXT_SCALE_PRESETS),
            max(TEXT_SCALE_PRESETS),
            DEFAULT_RUNTIME_PLAYER_SETTINGS["textScalePercent"],
        )

    def apply_text_scale(self) -> None:
        scale_percent = self.get_runtime_text_scale_percent()
        if getattr(self, "active_text_scale_percent", 100) == scale_percent:
            return
        scale = scale_percent / 100
        self.font_small = self._create_font(max(18, int(round(22 * scale))))
        self.font_body = self._create_font(max(24, int(round(30 * scale))))
        self.font_title = self._create_font(max(28, int(round(36 * scale))), bold=True)
        ui_scale = min(1.16, max(0.94, scale))
        self.font_ui = self._create_font(max(16, int(round(18 * ui_scale))))
        self.active_text_scale_percent = scale_percent

    def _initialize_audio(self) -> None:
        try:
            self.pygame.mixer.init()
        except Exception:
            self.status_message = "当前设备没有初始化音频输出，运行时会继续，但音乐和语音不会播放。"

    def get_effective_volume(self, channel_key: str) -> float:
        master = clamp(float(self.runtime_settings.get("masterVolume", 100)) / 100, 0.0, 1.0)
        channel = clamp(float(self.runtime_settings.get(channel_key, 100)) / 100, 0.0, 1.0)
        return master * channel

    def get_effective_bgm_volume(self, volume_percent: object | None = None) -> float:
        safe_volume_percent = (
            self.current_bgm_volume_percent
            if volume_percent is None
            else get_safe_volume_percent(volume_percent, 100)
        )
        return self.get_effective_volume("bgmVolume") * (safe_volume_percent / 100)

    def get_effective_voice_volume(self, volume_percent: object | None = None) -> float:
        safe_volume_percent = (
            self.current_voice_volume_percent
            if volume_percent is None
            else get_safe_volume_percent(volume_percent, 100)
        )
        return self.get_effective_volume("voiceVolume") * (safe_volume_percent / 100)

    def get_safe_runtime_language(self, language: object) -> str:
        normalized = normalize_language_code(language, "")
        if normalized and normalized in self.supported_languages:
            return normalized
        if self.default_language in self.supported_languages:
            return self.default_language
        return self.supported_languages[0] if self.supported_languages else DEFAULT_PROJECT_LANGUAGE

    def get_runtime_language_label(self, language: object) -> str:
        safe_language = self.get_safe_runtime_language(language)
        return str(self.language_labels.get(safe_language) or safe_language)

    def apply_runtime_language_setting(self) -> None:
        self.current_language = self.get_safe_runtime_language(self.runtime_settings.get("language"))
        self.runtime_settings["language"] = self.current_language

    def localize_value(self, source: dict | None, key: str, fallback: str = "") -> str:
        source = source if isinstance(source, dict) else {}
        translations = source.get(f"{key}Translations") if isinstance(source.get(f"{key}Translations"), dict) else {}
        candidates = [
            self.current_language,
            self.fallback_language,
            self.default_language,
            DEFAULT_PROJECT_LANGUAGE,
        ]
        for candidate in candidates:
            language = normalize_language_code(candidate, "")
            text = str(translations.get(language) or "").strip() if language else ""
            if text:
                return text
        return str(source.get(key) or fallback or "").strip()

    def is_voice_playing(self) -> bool:
        if not self.current_voice_channel:
            return False
        try:
            return bool(self.current_voice_channel.get_busy())
        except Exception:
            return False

    def apply_runtime_settings(self) -> None:
        self.apply_text_scale()
        self.apply_display_mode()
        if self.pygame.mixer.get_init():
            try:
                self.pygame.mixer.music.set_volume(self.get_effective_bgm_volume())
            except Exception:
                pass
        if self.current_voice_channel:
            try:
                self.current_voice_channel.set_volume(self.get_effective_voice_volume())
            except Exception:
                pass

    def apply_display_mode(self) -> None:
        display_mode = str(self.runtime_settings.get("displayMode") or "windowed")
        if display_mode == getattr(self, "active_display_mode", "windowed"):
            return
        flags = self.pygame.FULLSCREEN if display_mode == "fullscreen" else 0
        try:
            self.screen = self.pygame.display.set_mode((self.width, self.height), flags)
            self.active_display_mode = display_mode
        except Exception:
            if display_mode == "fullscreen":
                self.runtime_settings["displayMode"] = "windowed"
                self.screen = self.pygame.display.set_mode((self.width, self.height))
                self.active_display_mode = "windowed"
                self.status_message = "全屏切换失败，已回到窗口模式。"

    def toggle_display_mode(self) -> None:
        current = str(self.runtime_settings.get("displayMode") or "windowed")
        self.runtime_settings["displayMode"] = "fullscreen" if current == "windowed" else "windowed"
        self.runtime_settings = sanitize_runtime_player_settings(self.runtime_settings)
        self.apply_display_mode()
        self.persist_runtime_settings()
        label = "全屏" if self.runtime_settings.get("displayMode") == "fullscreen" else "窗口"
        self.status_message = f"显示模式已切换为：{label}"

    def persist_runtime_settings(self) -> None:
        write_project_runtime_settings(self.project_id, self.runtime_settings)

    def persist_archive_progress(self) -> None:
        write_project_archive_progress(self.project_id, self.archive_progress)

    def persist_read_text_progress(self) -> None:
        self.read_text_key_order = [key for key in self.read_text_key_order if key in self.read_text_keys]
        self.read_text_key_order = self.read_text_key_order[-READ_TEXT_KEY_LIMIT:]
        self.archive_progress["readTextKeys"] = list(self.read_text_key_order)
        self.persist_archive_progress()

    def get_snapshot_text_history(self) -> list[dict]:
        return sanitize_text_history_entries(self.text_history)

    def restore_text_history_from_snapshot(self, snapshot: dict) -> None:
        restored_history = sanitize_text_history_entries(snapshot.get("textHistory"))
        self.text_history = restored_history
        self.text_history_seen_keys = {
            str(item.get("key") or "")
            for item in restored_history
            if str(item.get("key") or "")
        }
        self.history_scroll_index = max(0, len(self.text_history) - 1)

    def persist_player_profile(self) -> None:
        self.player_profile = sanitize_player_profile(self.player_profile)
        write_project_player_profile(self.project_id, self.player_profile)

    def record_player_session_start(self) -> None:
        now = now_iso()
        profile = sanitize_player_profile(self.player_profile)
        if not profile.get("firstPlayedAt"):
            profile["firstPlayedAt"] = now
        profile["lastPlayedAt"] = now
        profile["sessionCount"] = int(profile.get("sessionCount") or 0) + 1
        self.player_profile = profile
        self.profile_session_started_at_ms = self.pygame.time.get_ticks()
        self.persist_player_profile()

    def record_player_session_end(self) -> None:
        profile = sanitize_player_profile(self.player_profile)
        if self.profile_session_started_at_ms:
            elapsed_ms = max(0, self.pygame.time.get_ticks() - self.profile_session_started_at_ms)
            profile["totalPlayMs"] = int(profile.get("totalPlayMs") or 0) + elapsed_ms
            self.profile_session_started_at_ms = 0
        profile["lastEndedAt"] = now_iso()
        self.player_profile = profile
        self.persist_player_profile()

    def record_player_resume(self) -> None:
        profile = sanitize_player_profile(self.player_profile)
        profile["resumedCount"] = int(profile.get("resumedCount") or 0) + 1
        profile["lastPlayedAt"] = now_iso()
        self.player_profile = profile
        self.persist_player_profile()

    def record_player_return_to_start(self) -> None:
        profile = sanitize_player_profile(self.player_profile)
        profile["returnToTitleCount"] = int(profile.get("returnToTitleCount") or 0) + 1
        profile["lastPlayedAt"] = now_iso()
        self.player_profile = profile
        self.persist_player_profile()

    def persist_auto_resume_snapshot(self) -> None:
        if not self.auto_resume_write_enabled:
            return
        snapshot = self.build_save_snapshot("auto-resume")
        self.auto_resume_snapshot = sanitize_auto_resume_snapshot(snapshot)
        if self.auto_resume_snapshot:
            write_project_auto_resume(self.project_id, self.auto_resume_snapshot)

    def clear_auto_resume_snapshot(self) -> None:
        clear_project_auto_resume(self.project_id)
        self.auto_resume_snapshot = None
        self.auto_resume_write_enabled = False
        self.status_message = "续玩记录已清除。"

    def load_auto_resume_snapshot(self) -> None:
        snapshot = self.auto_resume_snapshot or load_project_auto_resume(self.project_id)
        if not snapshot:
            self.status_message = "当前还没有续玩记录。"
            return
        self.restore_from_snapshot(snapshot)
        self.record_player_resume()
        self.persist_auto_resume_snapshot()
        self.close_overlay(preserve_status=True)
        self.status_message = f"已续玩：{snapshot.get('sceneName') or '未命名场景'}"

    def get_active_theme_mode(self) -> str:
        selected = str(self.runtime_settings.get("themeMode") or "auto")
        if selected == "auto":
            hour = datetime.now().hour
            return "light" if 7 <= hour < 19 else "dark"
        return selected

    def get_active_palette(self) -> dict:
        if self.get_active_theme_mode() == "light":
            palette = {
                "bgTop": (223, 232, 244),
                "bgBottom": (246, 249, 255),
                "panel": (245, 249, 255),
                "panelAlpha": 236,
                "panelBorder": (120, 156, 214),
                "text": (34, 47, 73),
                "muted": (92, 108, 132),
                "accent": (72, 122, 228),
                "accentAlt": (140, 90, 236),
                "warning": (220, 128, 86),
                "overlay": (220, 228, 242, 172),
                "placeholder": (220, 230, 244),
            }
        else:
            palette = {
                "bgTop": (18, 32, 58),
                "bgBottom": (24, 18, 48),
                "panel": COLOR_PANEL,
                "panelAlpha": 230,
                "panelBorder": COLOR_PANEL_BORDER,
                "text": COLOR_TEXT,
                "muted": COLOR_TEXT_MUTED,
                "accent": COLOR_ACCENT,
                "accentAlt": COLOR_ACCENT_ALT,
                "warning": COLOR_WARNING,
                "overlay": (6, 10, 18, 188),
                "placeholder": (36, 46, 77),
            }

        game_ui = getattr(self, "game_ui_config", None) or {}
        if game_ui:
            bg = game_ui.get("backgroundColor", palette["bgBottom"])
            accent = game_ui.get("backgroundAccentColor", palette["accent"])
            panel = game_ui.get("panelColor", palette["panel"])
            border = game_ui.get("borderColor", palette["panelBorder"])
            palette.update(
                {
                    "bgTop": mix_rgb(bg, accent, 0.18),
                    "bgBottom": mix_rgb(bg, (0, 0, 0), 0.18),
                    "panel": panel,
                    "panelAlpha": int(round(clamp_int(game_ui.get("panelOpacity"), 35, 100, 88) * 2.55)),
                    "panelBorder": border,
                    "text": game_ui.get("textColor", palette["text"]),
                    "muted": game_ui.get("mutedTextColor", palette["muted"]),
                    "accent": game_ui.get("accentColor", palette["accent"]),
                    "accentAlt": game_ui.get("accentAltColor", palette["accentAlt"]),
                    "overlay": (*mix_rgb(bg, (0, 0, 0), 0.22), 188),
                    "placeholder": mix_rgb(panel, accent, 0.12),
                }
            )
        return palette

    def unlock_archive_entry(self, progress_key: str, entry_id: str | None) -> None:
        safe_id = str(entry_id or "").strip()
        if not safe_id:
            return
        entries = self.archive_progress.setdefault(progress_key, [])
        if safe_id in entries:
            return
        entries.append(safe_id)
        self.archive_progress = sanitize_archive_progress(self.archive_progress)
        self.persist_archive_progress()

    def build_scene_preview(self, scene: dict | None) -> dict:
        preview = {
            "backgroundAssetId": "",
            "speakerName": "",
            "dialogueText": "",
        }
        if not scene:
            return preview
        for block in scene.get("blocks", []) or []:
            block_type = str(block.get("type") or "").strip()
            if block_type == "background" and block.get("assetId"):
                preview["backgroundAssetId"] = str(block.get("assetId") or "")
            elif block_type in {"dialogue", "narration"}:
                preview["dialogueText"] = self.localize_value(block, "text")
                speaker_id = str(block.get("speakerId") or "").strip()
                if speaker_id:
                    speaker = self.characters_by_id.get(speaker_id) or {}
                    preview["speakerName"] = self.localize_value(speaker, "displayName", speaker_id)
                elif block_type == "narration":
                    preview["speakerName"] = "旁白"
        return preview

    def collect_scene_encounter_character_ids(self, scene: dict | None, max_block_index: int | None = None) -> list[str]:
        if not scene:
            return []
        seen_ids: set[str] = set()
        ordered_ids: list[str] = []
        limit = max_block_index if max_block_index is not None else 10**9
        for block_index, block in enumerate(scene.get("blocks", []) or []):
            if block_index > limit:
                break
            candidates = []
            speaker_id = str(block.get("speakerId") or "").strip()
            character_id = str(block.get("characterId") or "").strip()
            if speaker_id:
                candidates.append(speaker_id)
            if character_id:
                candidates.append(character_id)
            for candidate in candidates:
                if candidate not in self.characters_by_id or candidate in seen_ids:
                    continue
                seen_ids.add(candidate)
                ordered_ids.append(candidate)
        return ordered_ids

    def get_chapter_archive_entries(self) -> list[dict]:
        unlocked_ids = set(self.archive_progress.get("chapterReplayUnlocked") or [])
        entries = []
        for order, chapter in enumerate(self.chapters, start=1):
            scenes = chapter.get("scenes") or []
            first_scene = scenes[0] if scenes else {}
            preview = self.build_scene_preview(first_scene)
            chapter_id = str(chapter.get("chapterId") or "")
            entries.append(
                {
                    "id": chapter_id,
                    "name": self.localize_value(chapter, "name", f"第 {order} 章"),
                    "subtitle": f"{len(scenes)} 个场景 · 开头：{self.localize_value(first_scene, 'name', '未命名场景')}",
                    "notes": str(chapter.get("summary") or chapter.get("notes") or ""),
                    "actionLabel": "重放这一章",
                    "actionEnabled": chapter_id in unlocked_ids and bool(first_scene.get("id")),
                    "firstSceneId": str(first_scene.get("id") or ""),
                    "previewAssetId": preview["backgroundAssetId"],
                    "previewSpeakerName": preview["speakerName"],
                    "previewText": preview["dialogueText"],
                    "unlocked": chapter_id in unlocked_ids,
                }
            )
        return entries

    def get_music_archive_entries(self) -> list[dict]:
        unlocked_ids = set(self.archive_progress.get("bgmUnlocked") or [])
        entries = []
        for asset in self.assets:
            if asset.get("type") != "bgm" or not asset.get("id"):
                continue
            tags = " / ".join(asset.get("tags") or [])
            entries.append(
                {
                    "id": str(asset["id"]),
                    "name": str(asset.get("name") or asset["id"]),
                    "subtitle": tags or "BGM 曲目",
                    "notes": str(asset.get("notes") or ""),
                    "actionLabel": "播放这首",
                    "actionEnabled": str(asset["id"]) in unlocked_ids,
                    "unlocked": str(asset["id"]) in unlocked_ids,
                    "previewSpeakerName": "音乐鉴赏",
                    "previewText": str(asset.get("notes") or "解锁后可以直接播放这首 BGM。"),
                }
            )
        return entries

    def get_gallery_archive_entries(self) -> list[dict]:
        unlocked_ids = set(self.archive_progress.get("cgUnlocked") or [])
        entries = []
        for asset in self.assets:
            if asset.get("type") != "cg" or not asset.get("id"):
                continue
            tags = " / ".join(asset.get("tags") or [])
            entries.append(
                {
                    "id": str(asset["id"]),
                    "name": str(asset.get("name") or asset["id"]),
                    "subtitle": tags or "CG 条目",
                    "notes": str(asset.get("notes") or ""),
                    "actionLabel": "查看大图",
                    "actionEnabled": str(asset["id"]) in unlocked_ids,
                    "previewAssetId": str(asset["id"]),
                    "previewText": str(asset.get("notes") or "推进到对应演出后，这张 CG 会在这里亮起。"),
                    "unlocked": str(asset["id"]) in unlocked_ids,
                }
            )
        return entries

    def get_location_archive_entries(self) -> list[dict]:
        unlocked_ids = set(self.archive_progress.get("locationUnlocked") or [])
        seen_asset_ids: set[str] = set()
        entries = []
        for chapter in self.chapters:
            chapter_name = self.localize_value(chapter, "name", "未命名章节")
            for scene in chapter.get("scenes") or []:
                for block in scene.get("blocks", []) or []:
                    if str(block.get("type") or "").strip() != "background":
                        continue
                    asset_id = str(block.get("assetId") or "").strip()
                    if not asset_id or asset_id in seen_asset_ids:
                        continue
                    asset = self.assets_by_id.get(asset_id) or {}
                    if asset.get("type") not in {"background", "scene3d"}:
                        continue
                    seen_asset_ids.add(asset_id)
                    tags = " / ".join(asset.get("tags") or [])
                    entries.append(
                        {
                            "id": asset_id,
                            "name": str(asset.get("name") or asset_id),
                            "subtitle": f"{chapter_name} · {self.localize_value(scene, 'name', '未命名场景')}",
                            "notes": tags or ("推进到这个 3D 场景第一次出现的位置后会自动收录。" if asset.get("type") == "scene3d" else "推进到这张背景第一次出现的位置后会自动收录。"),
                            "actionLabel": "查看地点",
                            "actionEnabled": asset_id in unlocked_ids,
                            "previewAssetId": asset_id,
                            "previewText": str(tags or ("这个地点来自剧情里的 3D 场景切换。" if asset.get("type") == "scene3d" else "这个地点来自剧情里的背景切换。")),
                            "assetType": str(asset.get("type") or ""),
                            "unlocked": asset_id in unlocked_ids,
                        }
                    )
        return entries

    def get_character_archive_entries(self) -> list[dict]:
        unlocked_ids = set(self.archive_progress.get("characterUnlocked") or [])
        entries = []
        for character in self.characters:
            character_id = str(character.get("id") or "").strip()
            if not character_id:
                continue
            expressions = character.get("expressions") or []
            presentation = self.get_character_presentation(character)
            mode_label = self.get_character_presentation_mode_label(character)
            entries.append(
                {
                    "id": character_id,
                    "name": self.localize_value(character, "displayName", character_id),
                    "subtitle": f"{mode_label} · {character.get('defaultPosition') or 'center'} · {len(expressions)} 个表情",
                    "notes": str(character.get("bio") or "推进到角色出场或开口后自动收录。"),
                    "actionLabel": "查看角色",
                    "actionEnabled": character_id in unlocked_ids,
                    "previewAssetId": str(presentation.get("fallbackSpriteAssetId") or character.get("defaultSpriteId") or ""),
                    "previewText": str(character.get("bio") or "这个角色会在剧情推进后自动收录进图鉴。"),
                    "unlocked": character_id in unlocked_ids,
                }
            )
        return entries

    def get_narration_archive_entries(self) -> list[dict]:
        unlocked_ids = set(self.archive_progress.get("narrationUnlocked") or [])
        entries = []
        for chapter in self.chapters:
            chapter_name = self.localize_value(chapter, "name", "未命名章节")
            for scene in chapter.get("scenes") or []:
                current_background_asset_id = ""
                for block_index, block in enumerate(scene.get("blocks", []) or []):
                    block_type = str(block.get("type") or "").strip()
                    if block_type == "background" and block.get("assetId"):
                        current_background_asset_id = str(block.get("assetId") or "")
                    if block_type != "narration":
                        continue
                    text = self.localize_value(block, "text")
                    if not text:
                        continue
                    entry_id = build_narration_archive_entry_id(scene.get("id"), block.get("id"), block_index)
                    entries.append(
                        {
                            "id": entry_id,
                            "name": f"{chapter_name} · {self.localize_value(scene, 'name', '未命名场景')}",
                            "subtitle": f"第 {block_index + 1} 条摘录",
                            "notes": text[:80],
                            "actionLabel": "查看摘录",
                            "actionEnabled": entry_id in unlocked_ids,
                            "previewAssetId": current_background_asset_id,
                            "previewSpeakerName": "旁白",
                            "previewText": text,
                            "unlocked": entry_id in unlocked_ids,
                        }
                    )
        return entries

    def get_relation_archive_entries(self) -> list[dict]:
        unlocked_ids = set(self.archive_progress.get("relationUnlocked") or [])
        entries = []
        seen_pair_ids: set[str] = set()
        for chapter in self.chapters:
            chapter_name = self.localize_value(chapter, "name", "未命名章节")
            for scene in chapter.get("scenes") or []:
                scene_character_ids = self.collect_scene_encounter_character_ids(scene)
                if len(scene_character_ids) < 2:
                    continue
                preview = self.build_scene_preview(scene)
                for index, left_character_id in enumerate(scene_character_ids):
                    for right_character_id in scene_character_ids[index + 1 :]:
                        pair_id = build_relationship_archive_id(left_character_id, right_character_id)
                        if not pair_id or pair_id in seen_pair_ids:
                            continue
                        seen_pair_ids.add(pair_id)
                        left_character = self.characters_by_id.get(left_character_id) or {}
                        right_character = self.characters_by_id.get(right_character_id) or {}
                        left_name = self.localize_value(left_character, "displayName", left_character_id)
                        right_name = self.localize_value(right_character, "displayName", right_character_id)
                        entries.append(
                            {
                                "id": pair_id,
                                "name": f"{left_name} × {right_name}",
                                "subtitle": f"{chapter_name} · {self.localize_value(scene, 'name', '未命名场景')}",
                                "notes": preview["dialogueText"] or "推进到这组角色真正同场后会自动收录。",
                                "actionLabel": "查看关系",
                                "actionEnabled": pair_id in unlocked_ids,
                                "previewAssetId": preview["backgroundAssetId"],
                                "previewSpeakerName": preview["speakerName"],
                                "previewText": preview["dialogueText"],
                                "unlocked": pair_id in unlocked_ids,
                            }
                        )
        return entries

    def get_voice_replay_entries(self) -> list[dict]:
        unlocked_ids = set(self.archive_progress.get("voiceReplayUnlocked") or [])
        entries = []
        for chapter in self.chapters:
            chapter_name = self.localize_value(chapter, "name", "未命名章节")
            for scene in chapter.get("scenes") or []:
                scene_name = self.localize_value(scene, "name", "未命名场景")
                current_background_asset_id = ""
                for block_index, block in enumerate(scene.get("blocks", []) or []):
                    block_type = str(block.get("type") or "").strip()
                    if block_type == "background" and block.get("assetId"):
                        current_background_asset_id = str(block.get("assetId") or "")
                    if block_type not in {"dialogue", "narration"} or not block.get("voiceAssetId"):
                        continue
                    text = self.localize_value(block, "text")
                    entry_id = build_voice_replay_entry_id(scene.get("id"), block.get("id"), block_index)
                    speaker_id = str(block.get("speakerId") or "").strip()
                    speaker_name = ""
                    if speaker_id:
                        speaker_name = self.localize_value(self.characters_by_id.get(speaker_id), "displayName", speaker_id)
                    elif block_type == "narration":
                        speaker_name = "旁白"
                    entries.append(
                        {
                            "id": entry_id,
                            "name": speaker_name or f"{chapter_name} · {scene_name}",
                            "subtitle": f"{chapter_name} · {scene_name}",
                            "notes": text[:80] or "这句带语音的台词会在推进后自动收录。",
                            "actionLabel": "回放语音",
                            "actionEnabled": entry_id in unlocked_ids,
                            "voiceAssetId": str(block.get("voiceAssetId") or ""),
                            "voiceVolume": get_safe_volume_percent(block.get("voiceVolume"), 100),
                            "previewAssetId": current_background_asset_id,
                            "previewSpeakerName": speaker_name,
                            "previewText": text,
                            "unlocked": entry_id in unlocked_ids,
                        }
                    )
        return entries

    def get_ending_archive_entries(self) -> list[dict]:
        unlocked_ids = set(self.archive_progress.get("endingUnlocked") or [])
        entries = []
        for chapter in self.chapters:
            chapter_name = self.localize_value(chapter, "name", "未命名章节")
            for scene in chapter.get("scenes") or []:
                scene_id = str(scene.get("id") or "").strip()
                if not scene_id or collect_scene_outgoing_targets(scene):
                    continue
                preview = self.build_scene_preview(scene)
                entries.append(
                    {
                        "id": scene_id,
                        "name": self.localize_value(scene, "name", scene_id),
                        "subtitle": chapter_name,
                        "notes": str(scene.get("notes") or "推进到这条路线收束位置后会自动回收到这里。"),
                        "actionLabel": "回放结局",
                        "actionEnabled": scene_id in unlocked_ids,
                        "previewAssetId": preview["backgroundAssetId"],
                        "previewSpeakerName": preview["speakerName"],
                        "previewText": preview["dialogueText"],
                        "unlocked": scene_id in unlocked_ids,
                    }
                )
        return entries

    def get_achievement_archive_entries(self) -> list[dict]:
        character_entries = self.get_character_archive_entries()
        gallery_entries = self.get_gallery_archive_entries()
        music_entries = self.get_music_archive_entries()
        ending_entries = self.get_ending_archive_entries()

        unlocked_characters = sum(1 for entry in character_entries if entry.get("unlocked"))
        unlocked_cg = sum(1 for entry in gallery_entries if entry.get("unlocked"))
        unlocked_bgm = sum(1 for entry in music_entries if entry.get("unlocked"))
        unlocked_endings = sum(1 for entry in ending_entries if entry.get("unlocked"))

        definitions = [
            {
                "id": "first_start",
                "name": "初次启动",
                "subtitle": "第一次进入原生 Runtime",
                "notes": "启动一次原生 Runtime 即可点亮。",
                "unlocked": bool(self.scene_order),
            },
            {
                "id": "first_character",
                "name": "角色初见",
                "subtitle": f"已收录角色 {unlocked_characters} / {len(character_entries)}",
                "notes": "任意角色完成收录后点亮。",
                "unlocked": unlocked_characters > 0,
            },
            {
                "id": "all_characters",
                "name": "角色全收录",
                "subtitle": f"已收录角色 {unlocked_characters} / {len(character_entries)}",
                "notes": "收录全部角色图鉴后点亮。",
                "unlocked": bool(character_entries) and unlocked_characters >= len(character_entries),
            },
            {
                "id": "first_cg",
                "name": "CG 初见",
                "subtitle": f"已回收 CG {unlocked_cg} / {len(gallery_entries)}",
                "notes": "任意 CG 完成回收后点亮。",
                "unlocked": unlocked_cg > 0,
            },
            {
                "id": "all_cg",
                "name": "CG 全回收",
                "subtitle": f"已回收 CG {unlocked_cg} / {len(gallery_entries)}",
                "notes": "回收全部 CG 后点亮。",
                "unlocked": bool(gallery_entries) and unlocked_cg >= len(gallery_entries),
            },
            {
                "id": "first_bgm",
                "name": "乐曲初见",
                "subtitle": f"已解锁曲目 {unlocked_bgm} / {len(music_entries)}",
                "notes": "任意 BGM 完成解锁后点亮。",
                "unlocked": unlocked_bgm > 0,
            },
            {
                "id": "all_bgm",
                "name": "乐曲全解锁",
                "subtitle": f"已解锁曲目 {unlocked_bgm} / {len(music_entries)}",
                "notes": "解锁全部 BGM 后点亮。",
                "unlocked": bool(music_entries) and unlocked_bgm >= len(music_entries),
            },
            {
                "id": "first_ending",
                "name": "初次通关",
                "subtitle": f"已回收结局 {unlocked_endings} / {len(ending_entries)}",
                "notes": "任意结局完成回收后点亮。",
                "unlocked": unlocked_endings > 0,
            },
            {
                "id": "all_endings",
                "name": "结局全回收",
                "subtitle": f"已回收结局 {unlocked_endings} / {len(ending_entries)}",
                "notes": "回收全部结局后点亮。",
                "unlocked": bool(ending_entries) and unlocked_endings >= len(ending_entries),
            },
        ]

        return [
            {
                **entry,
                "actionLabel": "查看成就",
                "actionEnabled": bool(entry.get("unlocked")),
                "previewText": entry["notes"],
            }
            for entry in definitions
        ]

    def get_archive_entries(self, archive_key: str) -> list[dict]:
        if archive_key == "achievements":
            return self.get_achievement_archive_entries()
        if archive_key == "narrations":
            return self.get_narration_archive_entries()
        if archive_key == "relations":
            return self.get_relation_archive_entries()
        if archive_key == "voices":
            return self.get_voice_replay_entries()
        if archive_key == "locations":
            return self.get_location_archive_entries()
        if archive_key == "characters":
            return self.get_character_archive_entries()
        if archive_key == "endings":
            return self.get_ending_archive_entries()
        if archive_key == "music":
            return self.get_music_archive_entries()
        if archive_key == "gallery":
            return self.get_gallery_archive_entries()
        return self.get_chapter_archive_entries()

    def get_selected_archive_entry(self) -> dict | None:
        entries = self.get_archive_entries(self.current_archive_key)
        if not entries:
            return None
        self.archive_selection_index = max(0, min(len(entries) - 1, self.archive_selection_index))
        return entries[self.archive_selection_index]

    def get_visible_archive_window(self, entries: list[dict], limit: int = 9) -> tuple[int, list[tuple[int, dict]]]:
        if not entries:
            return 0, []
        safe_limit = max(1, int(limit or 9))
        if len(entries) <= safe_limit:
            return 0, list(enumerate(entries))
        current_index = max(0, min(len(entries) - 1, self.archive_selection_index))
        max_start = max(0, len(entries) - safe_limit)
        start = max(0, min(max_start, current_index - safe_limit // 2))
        end = min(len(entries), start + safe_limit)
        start = max(0, end - safe_limit)
        return start, list(enumerate(entries[start:end], start=start))

    def change_archive_tab(self, delta: int) -> None:
        if not ARCHIVE_MENU_SEQUENCE:
            return
        try:
            current_index = ARCHIVE_MENU_SEQUENCE.index(self.current_archive_key)
        except ValueError:
            current_index = 0
        self.current_archive_key = ARCHIVE_MENU_SEQUENCE[(current_index + delta) % len(ARCHIVE_MENU_SEQUENCE)]
        self.archive_selection_index = 0

    def is_ending_scene(self, scene_id: str | None) -> bool:
        safe_scene_id = str(scene_id or "").strip()
        if not safe_scene_id:
            return False
        scene = self.scenes_by_id.get(safe_scene_id)
        return bool(scene) and not collect_scene_outgoing_targets(scene)

    def record_ending_completion(self, scene_id: str | None) -> None:
        safe_scene_id = str(scene_id or "").strip()
        if not self.is_ending_scene(safe_scene_id):
            return
        before_unlocked = set(self.archive_progress.get("endingUnlocked") or [])
        self.unlock_archive_entry("endingUnlocked", safe_scene_id)
        self.archive_progress["endingCompletionCount"] = max(
            0,
            int(self.archive_progress.get("endingCompletionCount") or 0),
        ) + 1
        self.archive_progress["endingLastCompletedAt"] = now_iso()
        self.archive_progress = sanitize_archive_progress(self.archive_progress)
        self.persist_archive_progress()
        if safe_scene_id not in before_unlocked:
            self.status_message = "结局已回收。"

    def start_current_line_display(self, text: str) -> None:
        self.current_line_full_text = str(text or "")
        self.current_line_revealed_chars = 0
        self.current_line_started_at_ms = self.pygame.time.get_ticks()
        self.current_line_next_reveal_at_ms = self.current_line_started_at_ms
        self.auto_play_deadline_ms = 0
        self.skip_deadline_ms = 0
        if self.get_current_line_text_speed() == "instant":
            self.reveal_current_line_immediately()

    def reveal_current_line_immediately(self) -> None:
        self.current_line_revealed_chars = len(self.current_line_full_text)
        self.current_line_next_reveal_at_ms = 0

    def is_current_line_fully_visible(self) -> bool:
        return self.current_line_revealed_chars >= len(self.current_line_full_text)

    def update_current_line_reveal(self) -> None:
        if not self.current_line or self.is_current_line_fully_visible():
            return
        speed = self.get_current_line_text_speed()
        if speed == "instant":
            self.reveal_current_line_immediately()
            return

        now_ms = self.pygame.time.get_ticks()
        if self.current_line_next_reveal_at_ms <= 0:
            self.current_line_next_reveal_at_ms = now_ms

        while not self.is_current_line_fully_visible() and now_ms >= self.current_line_next_reveal_at_ms:
            next_index = get_next_typewriter_index(self.current_line_full_text, self.current_line_revealed_chars)
            if next_index <= self.current_line_revealed_chars:
                self.reveal_current_line_immediately()
                return
            self.current_line_revealed_chars = next_index
            if self.is_current_line_fully_visible():
                self.current_line_next_reveal_at_ms = 0
                return
            visible_text = self.current_line_full_text[: self.current_line_revealed_chars]
            self.current_line_next_reveal_at_ms += get_native_typewriter_step_delay_ms(
                speed,
                visible_text,
                self.current_line_full_text,
            )

    def get_current_line_text_speed(self) -> str:
        return get_safe_text_speed(
            (self.current_line or {}).get("textSpeed"),
            str(self.runtime_settings.get("textSpeed") or "normal"),
        )

    def get_current_line_render_text(self) -> str:
        self.update_current_line_reveal()
        return self.current_line_full_text[: self.current_line_revealed_chars]

    def build_text_history_key(self, scene: dict | None, block_index: int, block_type: str, text: str) -> str:
        scene_id = str((scene or {}).get("id") or self.current_scene_id or "")
        text_digest = hashlib.sha1(str(text or "").encode("utf-8")).hexdigest()[:12]
        return f"{scene_id}:{int(block_index)}:{block_type}:{text_digest}"

    def get_line_speaker_name(self, line: dict) -> str:
        speaker_id = line.get("speakerId")
        if line.get("type") == "dialogue":
            character = self.characters_by_id.get(speaker_id) or {}
            return self.localize_value(character, "displayName", str(speaker_id or "角色"))
        if line.get("speakerName"):
            return str(line.get("speakerName") or "")
        if line.get("blockLabel"):
            return str(line.get("blockLabel") or "")
        return "旁白"

    def record_text_history(self, line: dict, scene: dict | None, block_index: int) -> None:
        text = str(line.get("text") or "").strip()
        if not text:
            return
        block_type = str(line.get("type") or "")
        history_key = self.build_text_history_key(scene, block_index, block_type, text)
        line["historyKey"] = history_key
        if history_key in self.text_history_seen_keys:
            return
        self.text_history_seen_keys.add(history_key)
        self.text_history.append(
            {
                "key": history_key,
                "sceneName": self.localize_value(scene, "name", self.get_current_scene_name()),
                "speakerName": self.get_line_speaker_name(line),
                "text": text,
                "blockType": block_type,
                "voiceAssetId": str(line.get("voiceAssetId") or "").strip(),
                "voiceVolume": get_safe_volume_percent(line.get("voiceVolume"), 100),
            }
        )
        self.text_history = self.text_history[-120:]
        self.history_scroll_index = max(0, len(self.text_history) - 1)

    def get_selected_text_history_item(self) -> dict | None:
        if not self.text_history:
            return None
        safe_index = max(0, min(len(self.text_history) - 1, self.history_scroll_index))
        self.history_scroll_index = safe_index
        return self.text_history[safe_index]

    def play_selected_history_voice(self) -> bool:
        item = self.get_selected_text_history_item()
        if not item:
            self.status_message = "当前还没有可回听的历史文本。"
            return True
        voice_asset_id = str(item.get("voiceAssetId") or "").strip()
        if not voice_asset_id:
            self.status_message = "这条历史文本没有绑定语音。"
            return True
        if self.play_voice(voice_asset_id, volume_percent=item.get("voiceVolume")):
            self.status_message = f"正在回听：{item.get('speakerName') or '历史语音'}"
        else:
            self.status_message = "这条历史文本的语音素材不可用。"
        return True

    def mark_current_line_read(self) -> None:
        if not self.current_line:
            return
        history_key = str(self.current_line.get("historyKey") or "")
        if history_key and history_key not in self.read_text_keys:
            self.read_text_keys.add(history_key)
            self.read_text_key_order.append(history_key)
            self.persist_read_text_progress()

    def open_text_history_overlay(self) -> None:
        self.ui_hidden = False
        self.overlay_mode = "history"
        self.history_scroll_index = max(0, len(self.text_history) - 1)
        self.status_message = "文本历史已打开。"

    def toggle_ui_hidden(self) -> None:
        if self.overlay_mode or self.title_screen_active:
            return
        self.ui_hidden = not self.ui_hidden
        if self.ui_hidden:
            self.stop_flow_assist()
            self.status_message = "界面已隐藏。左键 / 右键 / 中键 / U 可恢复。"
        else:
            self.status_message = "界面已恢复。"

    def restore_ui_hidden(self) -> bool:
        if not self.ui_hidden:
            return False
        self.ui_hidden = False
        self.status_message = "界面已恢复。"
        return True

    def toggle_auto_play(self) -> None:
        self.auto_play_enabled = not self.auto_play_enabled
        if self.auto_play_enabled:
            self.skip_read_enabled = False
            self.auto_play_deadline_ms = 0
            self.status_message = "自动播放已开启。"
        else:
            self.status_message = "自动播放已关闭。"

    def toggle_skip_read(self) -> None:
        self.skip_read_enabled = not self.skip_read_enabled
        if self.skip_read_enabled:
            self.auto_play_enabled = False
            self.skip_deadline_ms = 0
            self.status_message = "已读快进已开启，遇到未读文本或选项会停下。"
        else:
            self.status_message = "已读快进已关闭。"

    def stop_flow_assist(self) -> None:
        self.auto_play_enabled = False
        self.skip_read_enabled = False
        self.auto_play_deadline_ms = 0
        self.skip_deadline_ms = 0

    def update_flow_assist(self) -> None:
        if self.overlay_mode or self.current_choices or self.finished or not self.current_line:
            return
        if self.current_line.get("type") == "video_play":
            return
        now_ms = self.pygame.time.get_ticks()
        if self.skip_read_enabled:
            history_key = str(self.current_line.get("historyKey") or "")
            if history_key not in self.read_text_keys:
                self.skip_read_enabled = False
                self.status_message = "已读快进已停下：这里是未读文本。"
                return
            if not self.is_current_line_fully_visible():
                self.reveal_current_line_immediately()
            if self.skip_deadline_ms <= 0:
                self.skip_deadline_ms = now_ms + 90
                return
            if now_ms >= self.skip_deadline_ms:
                self.advance_current_line_if_allowed()
                self.skip_deadline_ms = 0
            return
        if self.auto_play_enabled and self.is_current_line_fully_visible():
            if self.runtime_settings.get("autoPlayWaitForVoice") == "on" and self.is_voice_playing():
                self.auto_play_deadline_ms = 0
                return
            if self.auto_play_deadline_ms <= 0:
                delay_ms = int(self.runtime_settings.get("autoPlayDelayMs") or DEFAULT_RUNTIME_PLAYER_SETTINGS["autoPlayDelayMs"])
                self.auto_play_deadline_ms = now_ms + max(400, delay_ms)
                return
            if now_ms >= self.auto_play_deadline_ms:
                self.advance_current_line_if_allowed()
                self.auto_play_deadline_ms = 0

    def handle_scene_finished(self, scene: dict | None) -> None:
        self.apply_bgm_scope_for_scene_finished(scene)
        self.unlock_relation_entries_for_scene(scene)
        scene_id = str((scene or {}).get("id") or "").strip()
        if self.is_ending_scene(scene_id):
            self.record_ending_completion(scene_id)
        self.finished = True
        self.finished_message = "剧情已经结束。"

    def unlock_relation_entries_for_scene(self, scene: dict | None, max_block_index: int | None = None) -> None:
        scene_character_ids = self.collect_scene_encounter_character_ids(scene, max_block_index=max_block_index)
        if len(scene_character_ids) < 2:
            return
        for index, left_character_id in enumerate(scene_character_ids):
            for right_character_id in scene_character_ids[index + 1 :]:
                pair_id = build_relationship_archive_id(left_character_id, right_character_id)
                if pair_id:
                    self.unlock_archive_entry("relationUnlocked", pair_id)

    def sync_archive_progress_for_pause(self, scene: dict | None, block: dict, block_index: int) -> None:
        block_type = str(block.get("type") or "").strip()
        if block_type == "narration":
            narration_id = build_narration_archive_entry_id((scene or {}).get("id"), block.get("id"), block_index)
            self.unlock_archive_entry("narrationUnlocked", narration_id)
        if block_type in {"dialogue", "narration"} and block.get("voiceAssetId"):
            voice_id = build_voice_replay_entry_id((scene or {}).get("id"), block.get("id"), block_index)
            self.unlock_archive_entry("voiceReplayUnlocked", voice_id)
        self.unlock_relation_entries_for_scene(scene, max_block_index=block_index)

    def _load_image(self, asset_id: str | None):
        if not asset_id:
            return None
        if asset_id in self.image_cache:
            return self.image_cache[asset_id]
        asset = self.assets_by_id.get(asset_id)
        asset_path = get_asset_runtime_path(self.bundle_dir, asset)
        if not asset_path:
            self.image_cache[asset_id] = None
            return None
        try:
            image = self.pygame.image.load(str(asset_path)).convert_alpha()
        except Exception:
            image = None
        self.image_cache[asset_id] = image
        return image

    def _load_image_file(self, image_path: Path | None):
        if not image_path:
            return None
        cache_key = str(image_path)
        if cache_key in self.image_file_cache:
            return self.image_file_cache[cache_key]
        if not image_path.is_file():
            self.image_file_cache[cache_key] = None
            return None
        try:
            image = self.pygame.image.load(str(image_path)).convert_alpha()
        except Exception:
            image = None
        self.image_file_cache[cache_key] = image
        return image

    def get_engine_brand_logo_path(self) -> Path | None:
        candidates = [
            self.bundle_dir / ENGINE_BRAND_LOGO_RELATIVE_PATH,
            Path(__file__).resolve().parent / ENGINE_BRAND_LOGO_RELATIVE_PATH,
            Path(__file__).resolve().parent.parent / "prototype_editor" / "assets" / "canvasia-brand-logo.png",
        ]
        for candidate in candidates:
            if candidate.is_file():
                return candidate
        return None

    def get_title_logo_image(self):
        title_logo_asset_id = str(self.game_ui_config.get("titleLogoAssetId") or "").strip()
        if title_logo_asset_id:
            title_logo = self._load_image(title_logo_asset_id)
            if title_logo:
                return title_logo
        return self._load_image_file(self.get_engine_brand_logo_path())

    def draw_nine_slice_image(self, source, rect, slice_config: dict | None, opacity_percent: int) -> None:
        if not source or rect.width <= 0 or rect.height <= 0:
            return
        opacity = clamp_int(opacity_percent, 0, 100, 0)
        if opacity <= 0:
            return

        pygame = self.pygame
        source_width, source_height = source.get_size()
        if source_width <= 0 or source_height <= 0:
            return

        slice_source = slice_config if isinstance(slice_config, dict) else {}
        left = clamp_int(slice_source.get("left"), 0, source_width // 2, 0)
        right = clamp_int(slice_source.get("right"), 0, source_width // 2, 0)
        top = clamp_int(slice_source.get("top"), 0, source_height // 2, 0)
        bottom = clamp_int(slice_source.get("bottom"), 0, source_height // 2, 0)
        target_left = min(left, rect.width // 2)
        target_right = min(right, max(0, rect.width - target_left))
        target_top = min(top, rect.height // 2)
        target_bottom = min(bottom, max(0, rect.height - target_top))

        source_columns = [(0, left), (left, source_width - right), (source_width - right, source_width)]
        source_rows = [(0, top), (top, source_height - bottom), (source_height - bottom, source_height)]
        target_columns = [
            (0, target_left),
            (target_left, rect.width - target_right),
            (rect.width - target_right, rect.width),
        ]
        target_rows = [
            (0, target_top),
            (target_top, rect.height - target_bottom),
            (rect.height - target_bottom, rect.height),
        ]
        frame_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)

        for row_index, (source_y1, source_y2) in enumerate(source_rows):
            for column_index, (source_x1, source_x2) in enumerate(source_columns):
                source_rect = pygame.Rect(source_x1, source_y1, source_x2 - source_x1, source_y2 - source_y1)
                target_x1, target_x2 = target_columns[column_index]
                target_y1, target_y2 = target_rows[row_index]
                target_rect = pygame.Rect(target_x1, target_y1, target_x2 - target_x1, target_y2 - target_y1)
                if (
                    source_rect.width <= 0
                    or source_rect.height <= 0
                    or target_rect.width <= 0
                    or target_rect.height <= 0
                ):
                    continue
                segment = source.subsurface(source_rect).copy()
                if segment.get_size() != target_rect.size:
                    segment = pygame.transform.smoothscale(segment, target_rect.size)
                frame_surface.blit(segment, target_rect)

        frame_surface.set_alpha(int(round(opacity * 2.55)))
        self.screen.blit(frame_surface, rect.topleft)

    def get_game_ui_panel_frame_image(self, frame_kind: str = "panel"):
        asset_key = {
            "save": "saveSlotFrameAssetId",
            "system": "systemPanelFrameAssetId",
        }.get(frame_kind, "panelFrameAssetId")
        asset_id = str(self.game_ui_config.get(asset_key) or "").strip()
        image = self._load_image(asset_id) if asset_id else None
        if not image and frame_kind != "panel":
            fallback_asset_id = str(self.game_ui_config.get("panelFrameAssetId") or "").strip()
            image = self._load_image(fallback_asset_id) if fallback_asset_id else None
        return image

    def draw_game_ui_panel_frame(self, rect, frame_kind: str = "panel") -> None:
        self.draw_nine_slice_image(
            self.get_game_ui_panel_frame_image(frame_kind),
            rect,
            self.game_ui_config.get("panelFrameSlice"),
            int(self.game_ui_config.get("panelFrameOpacity") or 0),
        )

    def get_game_ui_button_frame_image(self, state: str = "normal"):
        asset_key = {
            "hover": "buttonHoverFrameAssetId",
            "pressed": "buttonPressedFrameAssetId",
            "disabled": "buttonDisabledFrameAssetId",
        }.get(state, "buttonFrameAssetId")
        asset_id = str(self.game_ui_config.get(asset_key) or "").strip()
        image = self._load_image(asset_id) if asset_id else None
        if not image and state != "normal":
            fallback_asset_id = str(self.game_ui_config.get("buttonFrameAssetId") or "").strip()
            image = self._load_image(fallback_asset_id) if fallback_asset_id else None
        return image

    def get_game_ui_button_state(self, rect, *, active: bool = False, disabled: bool = False) -> str:
        if disabled:
            return "disabled"
        try:
            hovered = bool(rect.collidepoint(self.pygame.mouse.get_pos()))
            pressed = bool(self.pygame.mouse.get_pressed()[0]) if hovered else False
        except Exception:
            hovered = False
            pressed = False
        if pressed:
            return "pressed"
        if hovered or active:
            return "hover"
        return "normal"

    def draw_game_ui_button_frame(self, rect, state: str = "normal") -> None:
        self.draw_nine_slice_image(
            self.get_game_ui_button_frame_image(state),
            rect,
            self.game_ui_config.get("buttonFrameSlice"),
            int(self.game_ui_config.get("buttonFrameOpacity") or 0),
        )

    def _load_sound(self, asset_id: str | None):
        if not asset_id:
            return None
        if asset_id in self.sound_cache:
            return self.sound_cache[asset_id]
        asset = self.assets_by_id.get(asset_id)
        asset_path = get_asset_runtime_path(self.bundle_dir, asset)
        if not asset_path or not self.pygame.mixer.get_init():
            self.sound_cache[asset_id] = None
            return None
        try:
            sound = self.pygame.mixer.Sound(str(asset_path))
        except Exception:
            sound = None
        self.sound_cache[asset_id] = sound
        return sound

    def get_dialog_border_radius(self, height: int) -> int:
        shape = self.dialog_box_config.get("shape")
        if shape == "square":
            return 8
        if shape == "capsule":
            return max(18, height // 2)
        return max(16, min(32, height // 6))

    def get_dialog_opacity_scale(self) -> float:
        opacity_percent = clamp_int(
            self.runtime_settings.get("dialogBoxOpacityPercent"),
            min(DIALOG_BOX_OPACITY_PRESETS),
            max(DIALOG_BOX_OPACITY_PRESETS),
            DEFAULT_RUNTIME_PLAYER_SETTINGS["dialogBoxOpacityPercent"],
        )
        return opacity_percent / 100

    def scale_dialog_opacity(self, opacity: int | float) -> int:
        return clamp_int(int(round(float(opacity or 0) * self.get_dialog_opacity_scale())), 0, 255, 0)

    def get_dialog_panel_rect(self, min_height: int) -> object:
        width_percent = self.dialog_box_config.get("widthPercent", 76) / 100
        width = max(420, min(self.width - 48, int(self.width * width_percent)))
        height = max(int(min_height), int(self.dialog_box_config.get("minHeight", 148)))
        rect = self.pygame.Rect(0, 0, width, height)
        offset_x = int(self.width * int(self.dialog_box_config.get("offsetXPercent", 0)) / 100)
        offset_y = int(self.height * int(self.dialog_box_config.get("offsetYPercent", 0)) / 100)
        anchor = str(self.dialog_box_config.get("anchor") or "bottom")
        if anchor == "top":
            rect.midtop = (self.width // 2 + offset_x, 34 + offset_y)
        elif anchor in {"center", "free"}:
            rect.center = (self.width // 2 + offset_x, self.height // 2 + offset_y)
        else:
            rect.midbottom = (self.width // 2 + offset_x, self.height - 34 + offset_y)
        rect.clamp_ip(self.pygame.Rect(12, 12, self.width - 24, self.height - 24))
        return rect

    def draw_dialog_panel(self, rect) -> None:
        pygame = self.pygame
        config = self.dialog_box_config
        radius = self.get_dialog_border_radius(rect.height)
        shadow_strength = int(config.get("shadowStrength", 0))
        if shadow_strength > 0:
            shadow_alpha = int(70 + shadow_strength * 2.2)
            shadow_surface = pygame.Surface((rect.width + 32, rect.height + 32), pygame.SRCALPHA)
            pygame.draw.rect(
                shadow_surface,
                (0, 0, 0, min(190, shadow_alpha)),
                pygame.Rect(16, 16, rect.width, rect.height),
                border_radius=min(radius + 6, (rect.height + 12) // 2),
            )
            self.screen.blit(shadow_surface, (rect.left - 16, rect.top - 8))

        panel_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        panel_rect = panel_surface.get_rect()

        background_opacity = self.scale_dialog_opacity(int(config.get("backgroundOpacity", 0)))
        if background_opacity > 0:
            pygame.draw.rect(
                panel_surface,
                with_alpha(config.get("backgroundColor", COLOR_PANEL), background_opacity),
                panel_rect,
                border_radius=radius,
            )

        panel_art_id = config.get("panelAssetId")
        panel_art_opacity = self.scale_dialog_opacity(int(config.get("panelAssetOpacity", 0)))
        panel_art = self._load_image(panel_art_id) if panel_art_id and panel_art_opacity > 0 else None
        if panel_art:
            art_width, art_height = panel_art.get_size()
            if art_width > 0 and art_height > 0:
                if config.get("panelAssetFit") == "contain":
                    scale = min(rect.width / art_width, rect.height / art_height)
                else:
                    scale = max(rect.width / art_width, rect.height / art_height)
                scaled = pygame.transform.smoothscale(
                    panel_art,
                    (max(1, int(art_width * scale)), max(1, int(art_height * scale))),
                )
                scaled.set_alpha(int(round(panel_art_opacity * 2.55)))
                art_rect = scaled.get_rect(center=panel_rect.center)
                panel_surface.blit(scaled, art_rect)

        mask_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(mask_surface, (255, 255, 255, 255), mask_surface.get_rect(), border_radius=radius)
        panel_surface.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        self.screen.blit(panel_surface, rect)

        border_width = int(config.get("borderWidth", 0))
        border_opacity = int(config.get("borderOpacity", 0))
        if border_width > 0 and border_opacity > 0:
            border_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(
                border_surface,
                with_alpha(config.get("borderColor", COLOR_PANEL_BORDER), border_opacity),
                border_surface.get_rect(),
                width=border_width,
                border_radius=radius,
            )
            self.screen.blit(border_surface, rect)

    def get_dialogue_speaker_name(self, line: dict) -> str:
        if line.get("type") == "dialogue":
            character = self.characters_by_id.get(line.get("speakerId")) or {}
            return self.localize_value(character, "displayName", str(line.get("speakerId") or ""))
        if line.get("speakerName"):
            return str(line.get("speakerName") or "")
        if line.get("blockLabel"):
            return str(line.get("blockLabel") or "")
        return "旁白"

    def build_dialogue_layout(self, line: dict | None, text_width: int | None = None) -> dict:
        line = line or {}
        padding_x = int(self.dialog_box_config.get("paddingX", 18))
        padding_y = int(self.dialog_box_config.get("paddingY", 14))
        probe_panel = self.get_dialog_panel_rect(176)
        safe_text_width = int(text_width or (probe_panel.width - padding_x * 2))
        speaker_name = self.get_dialogue_speaker_name(line)
        speaker_height = self.font_title.get_height() + 12 if speaker_name else 0
        meta_height = self.font_ui.get_height()
        line_height = self.font_body.get_height() + 8
        full_lines = wrap_text(self.font_body, self.current_line_full_text, safe_text_width)
        max_panel_height = max(176, self.height - 48)
        max_text_height = max(36, max_panel_height - padding_y * 2 - speaker_height - meta_height - 10)
        max_possible_lines = max(1, max_text_height // line_height)
        desired_lines = min(max(1, len(full_lines)), max_possible_lines)
        desired_height = padding_y * 2 + speaker_height + meta_height + 10 + desired_lines * line_height
        return {
            "speakerName": speaker_name,
            "fullLines": full_lines,
            "lineHeight": line_height,
            "minHeight": min(max_panel_height, max(176, desired_height)),
            "textWidth": safe_text_width,
        }

    def blit_dialogue_text(self, font, text: str, position: tuple[int, int], color) -> None:
        shadow_strength = int(self.dialog_box_config.get("shadowStrength", 0))
        if shadow_strength > 0:
            shadow_alpha = clamp_int(shadow_strength * 3, 0, 150, 0)
            shadow_surface = font.render(str(text or ""), True, (0, 0, 0))
            shadow_surface.set_alpha(shadow_alpha)
            self.screen.blit(shadow_surface, (position[0] + 2, position[1] + 2))
        self.screen.blit(font.render(str(text or ""), True, color), position)

    def get_save_dialog_data(self) -> dict:
        return build_save_dialog_page_data(
            self.project,
            self.save_store,
            page=self.overlay_page,
            page_size=SAVE_DIALOG_PAGE_SIZE,
            variables=self.variables,
        )

    def get_save_dialog_slot_count(self) -> int:
        return len(self.get_save_dialog_data().get("visibleSlots") or [])

    def normalize_overlay_focus(self) -> None:
        if self.overlay_mode in {"save", "load"}:
            slot_count = self.get_save_dialog_slot_count()
            if slot_count <= 0:
                self.overlay_focus_index = 0
            else:
                self.overlay_focus_index = max(0, min(slot_count - 1, self.overlay_focus_index))
        elif self.overlay_mode == "title":
            self.title_menu_index = max(0, min(len(TITLE_MENU_ITEMS) - 1, self.title_menu_index))
        elif self.overlay_mode == "system":
            self.system_menu_index = max(0, min(len(SYSTEM_MENU_ITEMS) - 1, self.system_menu_index))

    def get_title_preview_background_asset_id(self) -> str:
        title_background_asset_id = str(self.game_ui_config.get("titleBackgroundAssetId") or "").strip()
        if title_background_asset_id:
            return title_background_asset_id
        for scene in self.scenes_by_id.values():
            for block in scene.get("blocks", []) or []:
                if str(block.get("type") or "") == "background" and block.get("assetId"):
                    return str(block.get("assetId") or "")
        return ""

    def open_title_screen(self) -> None:
        self.stop_embedded_video_playback()
        self.ui_hidden = False
        self.title_screen_active = True
        self.overlay_mode = "title"
        self.title_menu_index = 0
        self.overlay_hotspots = []
        self.current_line = None
        self.current_choices = None
        self.finished = False
        self.finished_message = ""
        self.stage_background_asset_id = self.get_title_preview_background_asset_id() or None
        self.background_transition = None
        self.leaving_characters = {}
        self.status_message = "标题页：选择开始、续玩、读档或设置。"

    def start_story_from_title(self) -> None:
        self.stop_embedded_video_playback()
        self.ui_hidden = False
        self.title_screen_active = False
        self.overlay_mode = None
        self.overlay_hotspots = []
        self.stop_voice()
        self.stop_bgm()
        self.clear_particle_effect()
        self.clear_stage_visual_effects(include_persistent=True)
        self.current_line = None
        self.current_choices = None
        self.current_choice_index = 0
        self.finished = False
        self.finished_message = ""
        self.stage_background_asset_id = None
        self.visible_characters = {}
        self.background_transition = None
        self.leaving_characters = {}
        self.current_bgm_asset_id = None
        self.current_bgm_volume_percent = 100
        self.current_bgm_scope = None
        self.variable_state = self.build_initial_variable_state()
        self.current_scene_id = self.project.get("entrySceneId") or self.scene_order[0]
        if self.current_scene_id not in self.scenes_by_id:
            self.current_scene_id = self.scene_order[0]
        self.current_block_index = 0
        self.auto_resume_write_enabled = True
        self.unlock_current_chapter_replay()
        self.advance_until_pause()
        self.persist_auto_resume_snapshot()
        self.status_message = "已开始游戏。"

    def open_save_dialog(self, mode: str) -> None:
        self.overlay_mode = mode if mode in {"save", "load"} else "save"
        self.overlay_page = 0
        self.overlay_focus_index = 0
        if self.overlay_mode == "load":
            formal_slots = self.save_store.get("formalSlots") or []
            for slot_index, snapshot in enumerate(formal_slots):
                if snapshot:
                    self.overlay_page = slot_index // SAVE_DIALOG_PAGE_SIZE
                    self.overlay_focus_index = slot_index % SAVE_DIALOG_PAGE_SIZE
                    break
        self.normalize_overlay_focus()
        self.status_message = "存档面板已打开。"

    def open_system_menu(self) -> None:
        self.overlay_mode = "system"
        self.system_menu_index = 0
        self.status_message = "系统菜单已打开。"

    def open_help_overlay(self) -> None:
        self.ui_hidden = False
        self.overlay_mode = "help"
        self.status_message = "操作帮助已打开。"

    def open_profile_overlay(self) -> None:
        self.overlay_mode = "profile"
        self.status_message = "玩家档案已打开。"

    def open_auto_resume_overlay(self) -> None:
        self.auto_resume_snapshot = load_project_auto_resume(self.project_id)
        self.overlay_mode = "auto-resume"
        self.status_message = "续玩记录已打开。"

    def close_overlay(self, preserve_status: bool = False) -> None:
        closing_mode = self.overlay_mode
        self.overlay_hotspots = []
        self.archive_detail_entry = None
        self.archive_detail_key = None
        if self.title_screen_active and closing_mode != "title":
            self.overlay_mode = "title"
            if not preserve_status:
                self.status_message = "已返回标题页。"
            return
        self.overlay_mode = None
        if not preserve_status:
            self.status_message = "已返回游戏画面。"

    def change_save_dialog_page(self, delta: int) -> None:
        dialog_data = self.get_save_dialog_data()
        page_count = dialog_data.get("pageCount") or 1
        self.overlay_page = max(0, min(page_count - 1, self.overlay_page + delta))
        self.normalize_overlay_focus()

    def activate_overlay_slot(self, visible_slot_index: int) -> None:
        dialog_data = self.get_save_dialog_data()
        visible_slots = dialog_data.get("visibleSlots") or []
        if visible_slot_index < 0 or visible_slot_index >= len(visible_slots):
            return
        slot_index = int(visible_slots[visible_slot_index]["slotIndex"])
        if self.overlay_mode == "save":
            self.save_formal_slot(slot_index)
            self.close_overlay(preserve_status=True)
        elif self.overlay_mode == "load":
            snapshot = (self.save_store.get("formalSlots") or [None] * self.formal_save_slot_count)[slot_index]
            if not snapshot:
                self.status_message = f"正式存档 {slot_index + 1} 还是空的。"
                return
            self.load_formal_slot(slot_index)
            self.close_overlay(preserve_status=True)

    def restart_story(self) -> None:
        self.record_player_return_to_start()
        self.start_story_from_title()
        self.status_message = "已回到开头。"

    def activate_system_menu_item(self, item_key: str) -> bool:
        if item_key == "continue":
            self.close_overlay()
            return True
        if item_key == "help":
            self.open_help_overlay()
            return True
        if item_key == "history":
            self.open_text_history_overlay()
            return True
        if item_key == "archives":
            self.open_archive_overlay()
            return True
        if item_key == "profile":
            self.open_profile_overlay()
            return True
        if item_key == "auto-resume":
            self.open_auto_resume_overlay()
            return True
        if item_key == "save":
            self.open_save_dialog("save")
            return True
        if item_key == "load":
            self.open_save_dialog("load")
            return True
        if item_key == "settings":
            self.open_settings_overlay()
            return True
        if item_key == "quick-save":
            self.save_quick()
            self.close_overlay(preserve_status=True)
            return True
        if item_key == "quick-load":
            self.load_quick()
            self.close_overlay(preserve_status=True)
            return True
        if item_key == "restart":
            self.restart_story()
            return True
        if item_key == "exit":
            return False
        return True

    def get_title_menu_items(self) -> list[dict]:
        self.auto_resume_snapshot = load_project_auto_resume(self.project_id)
        formal_slots = self.save_store.get("formalSlots") or []
        filled_formal_count = sum(1 for item in formal_slots if item)
        menu_items = []
        for item_key, item_label in TITLE_MENU_ITEMS:
            enabled = True
            subtitle = ""
            if item_key == "start":
                subtitle = "从入口场景开始新的游玩。"
            elif item_key == "resume":
                enabled = self.auto_resume_snapshot is not None
                if self.auto_resume_snapshot:
                    variable_summary = str(self.auto_resume_snapshot.get("variableSummaryText") or "").strip()
                    if not variable_summary:
                        variable_summary = build_variable_summary_text(
                            self.variables,
                            self.auto_resume_snapshot.get("variableState"),
                        )
                    subtitle = f"{self.auto_resume_snapshot.get('sceneName') or '未命名场景'} · {format_snapshot_saved_at(self.auto_resume_snapshot.get('savedAt'))}"
                    if variable_summary:
                        subtitle = f"{subtitle} · {variable_summary}"
                else:
                    subtitle = "推进一次剧情后会自动生成续玩记录。"
            elif item_key == "load":
                subtitle = f"正式存档 {filled_formal_count}/{self.formal_save_slot_count}。"
            elif item_key == "settings":
                subtitle = "主题、全屏、文字速度和音量。"
            elif item_key == "archives":
                subtitle = "章节、音乐、CG、角色、结局和成就。"
            elif item_key == "exit":
                subtitle = "关闭原生 Runtime。"
            menu_items.append({"key": item_key, "label": item_label, "subtitle": subtitle, "enabled": enabled})
        return menu_items

    def activate_title_menu_item(self, item_key: str) -> bool:
        if item_key == "start":
            self.start_story_from_title()
            return True
        if item_key == "resume":
            if not self.auto_resume_snapshot:
                self.status_message = "当前还没有续玩记录。"
                return True
            self.load_auto_resume_snapshot()
            return True
        if item_key == "load":
            self.open_save_dialog("load")
            return True
        if item_key == "settings":
            self.open_settings_overlay()
            return True
        if item_key == "archives":
            self.open_archive_overlay()
            return True
        if item_key == "exit":
            return False
        return True

    def open_archive_overlay(self, archive_key: str | None = None) -> None:
        safe_key = archive_key if archive_key in ARCHIVE_MENU_ITEMS else self.current_archive_key or "chapters"
        self.overlay_mode = "archives"
        self.current_archive_key = safe_key
        self.archive_selection_index = 0
        entries = self.get_archive_entries(safe_key)
        for index, entry in enumerate(entries):
            if entry.get("unlocked"):
                self.archive_selection_index = index
                break
        self.status_message = f"{ARCHIVE_MENU_ITEMS.get(safe_key, '资料馆')} 已打开。"

    def open_settings_overlay(self) -> None:
        self.overlay_mode = "settings"
        self.settings_menu_index = 0
        self.status_message = "体验设置已打开。"

    def adjust_runtime_setting(self, setting_key: str, direction: int) -> None:
        if setting_key == "themeMode":
            current = str(self.runtime_settings.get("themeMode") or "auto")
            options = list(RUNTIME_THEME_MODES)
            current_index = options.index(current) if current in options else 0
            self.runtime_settings["themeMode"] = options[(current_index + direction) % len(options)]
        elif setting_key == "displayMode":
            current = str(self.runtime_settings.get("displayMode") or "windowed")
            options = list(RUNTIME_DISPLAY_MODES)
            current_index = options.index(current) if current in options else 0
            self.runtime_settings["displayMode"] = options[(current_index + direction) % len(options)]
        elif setting_key == "textSpeed":
            current = str(self.runtime_settings.get("textSpeed") or "normal")
            options = list(TEXT_SPEED_PRESETS.keys())
            current_index = options.index(current) if current in options else 0
            self.runtime_settings["textSpeed"] = options[(current_index + direction) % len(options)]
            if self.current_line and not self.is_current_line_fully_visible():
                self.start_current_line_display(self.current_line_full_text)
        elif setting_key == "language":
            options = self.supported_languages or [DEFAULT_PROJECT_LANGUAGE]
            current = self.get_safe_runtime_language(self.runtime_settings.get("language"))
            current_index = options.index(current) if current in options else 0
            self.runtime_settings["language"] = options[(current_index + direction) % len(options)]
        elif setting_key == "textScalePercent":
            current = int(self.runtime_settings.get("textScalePercent") or DEFAULT_RUNTIME_PLAYER_SETTINGS["textScalePercent"])
            options = list(TEXT_SCALE_PRESETS)
            current_index = min(range(len(options)), key=lambda index: abs(options[index] - current))
            self.runtime_settings["textScalePercent"] = options[(current_index + direction) % len(options)]
        elif setting_key == "dialogBoxOpacityPercent":
            current = int(self.runtime_settings.get("dialogBoxOpacityPercent", DEFAULT_RUNTIME_PLAYER_SETTINGS["dialogBoxOpacityPercent"]))
            options = list(DIALOG_BOX_OPACITY_PRESETS)
            current_index = min(range(len(options)), key=lambda index: abs(options[index] - current))
            self.runtime_settings["dialogBoxOpacityPercent"] = options[(current_index + direction) % len(options)]
        elif setting_key == "autoPlayDelayMs":
            current = int(self.runtime_settings.get("autoPlayDelayMs") or DEFAULT_RUNTIME_PLAYER_SETTINGS["autoPlayDelayMs"])
            options = list(AUTO_PLAY_DELAY_PRESETS)
            current_index = min(range(len(options)), key=lambda index: abs(options[index] - current))
            self.runtime_settings["autoPlayDelayMs"] = options[(current_index + direction) % len(options)]
        elif setting_key == "autoPlayWaitForVoice":
            current = str(self.runtime_settings.get("autoPlayWaitForVoice") or DEFAULT_RUNTIME_PLAYER_SETTINGS["autoPlayWaitForVoice"])
            options = list(RUNTIME_TOGGLE_MODES)
            current_index = options.index(current) if current in options else 0
            self.runtime_settings["autoPlayWaitForVoice"] = options[(current_index + direction) % len(options)]
        elif setting_key in {"masterVolume", "bgmVolume", "sfxVolume", "voiceVolume"}:
            current_value = int(self.runtime_settings.get(setting_key) or DEFAULT_RUNTIME_PLAYER_SETTINGS[setting_key])
            self.runtime_settings[setting_key] = clamp_int(current_value + direction * 5, 0, 100, current_value)
        self.runtime_settings = sanitize_runtime_player_settings(self.runtime_settings)
        self.apply_runtime_language_setting()
        if setting_key == "language":
            self.refresh_current_localized_pause()
        self.persist_runtime_settings()
        self.apply_runtime_settings()
        self.status_message = "体验设置已更新。"

    def get_setting_value_label(self, setting_key: str) -> str:
        if setting_key == "themeMode":
            label_map = {"auto": "自动", "light": "浅色", "dark": "深色"}
            selected = str(self.runtime_settings.get("themeMode") or "auto")
            active = self.get_active_theme_mode()
            return f"{label_map.get(selected, selected)}（当前：{label_map.get(active, active)}）"
        if setting_key == "displayMode":
            label_map = {"windowed": "窗口", "fullscreen": "全屏"}
            selected = str(self.runtime_settings.get("displayMode") or "windowed")
            return label_map.get(selected, selected)
        if setting_key == "textSpeed":
            speed_key = str(self.runtime_settings.get("textSpeed") or "normal")
            return TEXT_SPEED_LABELS.get(speed_key, speed_key)
        if setting_key == "language":
            return self.get_runtime_language_label(self.runtime_settings.get("language"))
        if setting_key == "textScalePercent":
            return f"{int(self.runtime_settings.get('textScalePercent') or DEFAULT_RUNTIME_PLAYER_SETTINGS['textScalePercent'])}%"
        if setting_key == "dialogBoxOpacityPercent":
            opacity = int(self.runtime_settings.get("dialogBoxOpacityPercent") or 0)
            return "透明" if opacity == 0 else f"{opacity}%"
        if setting_key == "autoPlayDelayMs":
            return f"{int(self.runtime_settings.get('autoPlayDelayMs') or DEFAULT_RUNTIME_PLAYER_SETTINGS['autoPlayDelayMs']) / 1000:.1f} 秒"
        if setting_key == "autoPlayWaitForVoice":
            return "开启" if self.runtime_settings.get("autoPlayWaitForVoice") == "on" else "关闭"
        return f"{int(self.runtime_settings.get(setting_key) or 0)}%"

    def activate_archive_entry(self, entry: dict | None) -> bool:
        if not entry:
            return True
        if not entry.get("unlocked"):
            self.status_message = "当前条目还没有解锁。"
            return True
        if self.current_archive_key == "chapters":
            first_scene_id = str(entry.get("firstSceneId") or "")
            if not first_scene_id:
                self.status_message = "这章还没有可回放的起点场景。"
                return True
            self.stop_voice()
            self.current_choices = None
            self.current_line = None
            self.finished = False
            self.finished_message = ""
            self.title_screen_active = False
            self.set_scene(first_scene_id)
            self.close_overlay(preserve_status=True)
            self.advance_until_pause()
            self.auto_resume_write_enabled = True
            self.persist_auto_resume_snapshot()
            self.status_message = f"已从章节开头进入：{entry.get('name') or '未命名章节'}"
            return True
        if self.current_archive_key == "music":
            self.play_bgm(str(entry.get("id") or ""), loop=True)
            self.status_message = f"正在试听：{entry.get('name') or '未命名曲目'}"
            return True
        if self.current_archive_key == "gallery":
            self.open_archive_detail(entry)
            return True
        if self.current_archive_key == "locations":
            self.open_archive_detail(entry)
            return True
        if self.current_archive_key == "characters":
            self.open_archive_detail(entry)
            return True
        if self.current_archive_key == "narrations":
            self.open_archive_detail(entry)
            return True
        if self.current_archive_key == "relations":
            self.open_archive_detail(entry)
            return True
        if self.current_archive_key == "voices":
            voice_asset_id = str(entry.get("voiceAssetId") or "")
            if voice_asset_id:
                self.play_voice(voice_asset_id, volume_percent=entry.get("voiceVolume"))
                self.status_message = f"正在回放语音：{entry.get('name') or '未命名条目'}"
            else:
                self.status_message = "这个条目当前没有可回放语音。"
            return True
        if self.current_archive_key == "endings":
            scene_id = str(entry.get("id") or "")
            if not scene_id:
                self.status_message = "这个结局当前没有可回放的场景。"
                return True
            self.stop_voice()
            self.current_choices = None
            self.current_line = None
            self.finished = False
            self.finished_message = ""
            self.title_screen_active = False
            self.set_scene(scene_id)
            self.close_overlay(preserve_status=True)
            self.advance_until_pause()
            self.auto_resume_write_enabled = True
            self.persist_auto_resume_snapshot()
            self.status_message = f"已进入结局回放：{entry.get('name') or '未命名结局'}"
            return True
        if self.current_archive_key == "achievements":
            self.open_archive_detail(entry)
            return True
        return True

    def open_archive_detail(self, entry: dict) -> None:
        self.archive_detail_key = self.current_archive_key
        self.archive_detail_entry = dict(entry)
        self.overlay_mode = "archive-detail"
        self.status_message = f"正在查看：{entry.get('name') or '资料馆条目'}"

    def close_archive_detail(self) -> None:
        self.overlay_mode = "archives"
        self.archive_detail_entry = None
        self.archive_detail_key = None
        self.status_message = "已返回资料馆。"

    def get_chapter_for_scene(self, scene_id: str | None) -> dict | None:
        safe_scene_id = str(scene_id or "").strip()
        if not safe_scene_id:
            return None
        for chapter in self.chapters:
            for scene in chapter.get("scenes") or []:
                if str(scene.get("id") or "") == safe_scene_id:
                    return chapter
        return None

    def unlock_current_chapter_replay(self) -> None:
        chapter = self.get_chapter_for_scene(self.current_scene_id)
        chapter_id = str((chapter or {}).get("chapterId") or "")
        if chapter_id:
            self.unlock_archive_entry("chapterReplayUnlocked", chapter_id)

    def get_current_scene(self) -> dict | None:
        return self.scenes_by_id.get(self.current_scene_id)

    def get_current_scene_name(self) -> str:
        return self.localize_value(self.get_current_scene(), "name", self.current_scene_id or "未命名场景")

    def refresh_current_localized_pause(self) -> None:
        scene = self.get_current_scene()
        blocks = (scene or {}).get("blocks", []) or []
        if self.current_block_index >= len(blocks):
            return
        block = blocks[self.current_block_index]
        block_type = str(block.get("type") or "").strip()
        if block_type not in {"dialogue", "narration"}:
            return
        was_fully_visible = self.is_current_line_fully_visible()
        line_text = self.localize_value(block, "text")
        self.current_line = {
            "type": block_type,
            "speakerId": block.get("speakerId"),
            "text": line_text,
            "textSpeed": block.get("textSpeed"),
            "voiceAssetId": block.get("voiceAssetId"),
            "voiceVolume": block.get("voiceVolume"),
            "blockLabel": get_block_label(block_type),
        }
        self.start_current_line_display(line_text)
        if was_fully_visible:
            self.reveal_current_line_immediately()

    def get_current_line_preview(self) -> str:
        if self.current_line and self.current_line.get("text"):
            return str(self.current_line["text"]).strip()
        if self.current_choices:
            return "当前停在选项卡。"
        if self.finished:
            return self.finished_message or "剧情已经结束。"
        return ""

    def get_snapshot_visible_characters(self, source: dict | None = None) -> dict:
        characters = source if isinstance(source, dict) else self.visible_characters
        snapshot_characters = {}
        for character_id, state in characters.items():
            if not isinstance(state, dict):
                continue
            safe_state = dict(state)
            safe_state.pop("transition", None)
            safe_state.pop("__leaving", None)
            snapshot_characters[character_id] = safe_state
        return snapshot_characters

    def build_save_snapshot(self, kind: str) -> dict:
        return {
            "kind": kind,
            "savedAt": now_iso(),
            "sceneId": self.current_scene_id,
            "sceneName": self.get_current_scene_name(),
            "blockIndex": self.current_block_index,
            "variableState": dict(self.variable_state),
            "stageBackgroundAssetId": self.stage_background_asset_id,
            "scene3dPreview": {
                "yaw": round(float(self.scene3d_preview_yaw), 2),
                "pitch": round(float(self.scene3d_preview_pitch), 2),
                "zoom": round(float(self.scene3d_preview_zoom), 3),
                "interactionEnabled": bool(self.scene3d_preview_interaction_enabled),
            },
            "visibleCharacters": self.get_snapshot_visible_characters(),
            "currentBgmAssetId": self.current_bgm_asset_id,
            "currentBgmVolume": self.current_bgm_volume_percent,
            "currentBgmScope": dict(self.current_bgm_scope) if isinstance(self.current_bgm_scope, dict) else None,
            "finished": self.finished,
            "finishedMessage": self.finished_message,
            "summaryText": self.get_current_line_preview()[:96],
            "variableSummaryText": build_variable_summary_text(self.variables, self.variable_state),
            "textHistory": self.get_snapshot_text_history(),
            "particleEffect": dict(self.active_particle_effect) if self.active_particle_effect else None,
            "visualEffects": {
                "screenFade": dict(self.screen_fade_effect) if self.screen_fade_effect else None,
                "cameraZoom": dict(self.camera_zoom_effect) if self.camera_zoom_effect else None,
                "cameraPan": dict(self.camera_pan_effect) if self.camera_pan_effect else None,
                "screenFilter": dict(self.screen_filter_effect) if self.screen_filter_effect else None,
                "depthBlur": dict(self.depth_blur_effect) if self.depth_blur_effect else None,
            },
        }

    def persist_save_store(self) -> None:
        write_project_save_store(self.project_id, self.save_store)

    def save_quick(self) -> None:
        self.save_store["quickSave"] = self.build_save_snapshot("quick")
        self.persist_save_store()
        self.status_message = f"快速存档已写入：{self.save_file_path.name}"

    def load_quick(self) -> None:
        snapshot = self.save_store.get("quickSave")
        if not snapshot:
            self.status_message = "当前还没有快速存档。"
            return
        self.restore_from_snapshot(snapshot)
        self.persist_auto_resume_snapshot()
        self.status_message = f"已读入快速存档：{snapshot.get('sceneName') or '未命名场景'}"

    def save_formal_slot(self, slot_index: int) -> None:
        if slot_index < 0 or slot_index >= self.formal_save_slot_count:
            return
        self.save_store["formalSlots"][slot_index] = self.build_save_snapshot("formal")
        self.persist_save_store()
        self.status_message = f"正式存档 {slot_index + 1} 已写入：{self.save_file_path.name}"

    def load_formal_slot(self, slot_index: int) -> None:
        if slot_index < 0 or slot_index >= self.formal_save_slot_count:
            return
        snapshot = (self.save_store.get("formalSlots") or [None] * self.formal_save_slot_count)[slot_index]
        if not snapshot:
            self.status_message = f"正式存档 {slot_index + 1} 还是空的。"
            return
        self.restore_from_snapshot(snapshot)
        self.persist_auto_resume_snapshot()
        self.status_message = f"已读入正式存档 {slot_index + 1}：{snapshot.get('sceneName') or '未命名场景'}"

    def restore_from_snapshot(self, snapshot: dict) -> None:
        self.stop_embedded_video_playback()
        self.ui_hidden = False
        self.title_screen_active = False
        self.overlay_mode = None
        self.auto_resume_write_enabled = True
        self.stop_voice()
        self.current_line = None
        self.current_choices = None
        self.current_choice_index = 0
        self.restore_text_history_from_snapshot(snapshot)
        self.finished = bool(snapshot.get("finished"))
        self.finished_message = str(snapshot.get("finishedMessage") or "")
        scene_id = str(snapshot.get("sceneId") or self.project.get("entrySceneId") or self.scene_order[0])
        self.current_scene_id = scene_id if scene_id in self.scenes_by_id else self.scene_order[0]
        self.unlock_current_chapter_replay()
        self.current_block_index = int(snapshot.get("blockIndex") or 0)
        self.variable_state = self.merge_variable_state(snapshot.get("variableState") or {})
        self.stage_background_asset_id = snapshot.get("stageBackgroundAssetId")
        self.apply_scene3d_preview_config(snapshot.get("scene3dPreview") if isinstance(snapshot.get("scene3dPreview"), dict) else None)
        self.visible_characters = self.get_snapshot_visible_characters(snapshot.get("visibleCharacters") or {})
        self.background_transition = None
        self.leaving_characters = {}
        self.current_bgm_asset_id = None
        self.current_bgm_volume_percent = get_safe_volume_percent(snapshot.get("currentBgmVolume"), 100)
        self.current_bgm_scope = snapshot.get("currentBgmScope") if isinstance(snapshot.get("currentBgmScope"), dict) else None
        self.clear_particle_effect()
        self.clear_stage_visual_effects(include_persistent=True)

        bgm_asset_id = snapshot.get("currentBgmAssetId")
        if bgm_asset_id:
            self.play_bgm(bgm_asset_id, loop=True, volume_percent=self.current_bgm_volume_percent)
        else:
            self.stop_bgm()

        particle_effect = snapshot.get("particleEffect")
        if particle_effect:
            self.set_particle_effect(particle_effect)

        visual_effects = snapshot.get("visualEffects") or {}
        self.screen_fade_effect = visual_effects.get("screenFade")
        self.camera_zoom_effect = visual_effects.get("cameraZoom")
        self.camera_pan_effect = visual_effects.get("cameraPan")
        self.screen_filter_effect = visual_effects.get("screenFilter")
        self.depth_blur_effect = visual_effects.get("depthBlur")

        if self.finished:
            self.persist_auto_resume_snapshot()
            return
        self.hydrate_pause_from_current_block()
        self.persist_auto_resume_snapshot()

    def set_scene(self, scene_id: str | None) -> None:
        if scene_id and scene_id in self.scenes_by_id:
            self.current_scene_id = scene_id
            self.current_block_index = 0
            self.unlock_current_chapter_replay()
            return
        self.finished = True
        self.finished_message = "剧情已经结束。"

    def clear_particle_effect(self) -> None:
        self.active_particle_effect = None
        self.particle_items = []

    def stop_bgm_for_scope_end(self, fade_out_ms: int = 0) -> None:
        self.stop_bgm(fade_out_ms=fade_out_ms)
        self.current_bgm_scope = None

    def apply_bgm_scope_before_block(self, scene: dict | None, block_index: int) -> None:
        scope = self.current_bgm_scope if isinstance(self.current_bgm_scope, dict) else None
        if not scope:
            return
        end_mode = get_safe_music_end_mode(scope.get("endMode"))
        if end_mode == "until_next_music":
            return
        scene_id = str((scene or {}).get("id") or "")
        scope_scene_id = str(scope.get("sceneId") or "")
        if scope_scene_id and scene_id and scope_scene_id != scene_id:
            self.stop_bgm_for_scope_end(get_safe_audio_fade_ms(scope.get("fadeOutMs"), 600))
            return
        if end_mode != "after_block":
            return
        end_block_id = str(scope.get("endBlockId") or "")
        blocks = (scene or {}).get("blocks", []) or []
        end_index = next((index for index, item in enumerate(blocks) if item.get("id") == end_block_id), -1)
        if end_index >= 0 and block_index > end_index:
            self.stop_bgm_for_scope_end(get_safe_audio_fade_ms(scope.get("fadeOutMs"), 600))

    def apply_bgm_scope_for_scene_finished(self, scene: dict | None) -> None:
        scope = self.current_bgm_scope if isinstance(self.current_bgm_scope, dict) else None
        if not scope or get_safe_music_end_mode(scope.get("endMode")) == "until_next_music":
            return
        scene_id = str((scene or {}).get("id") or "")
        scope_scene_id = str(scope.get("sceneId") or "")
        if not scope_scene_id or scope_scene_id == scene_id:
            self.stop_bgm_for_scope_end(get_safe_audio_fade_ms(scope.get("fadeOutMs"), 600))

    def clear_stage_visual_effects(self, include_persistent: bool = False) -> None:
        self.screen_shake_effect = None
        self.screen_flash_effect = None
        if include_persistent:
            self.screen_fade_effect = None
            self.camera_zoom_effect = None
            self.camera_pan_effect = None
            self.screen_filter_effect = None
            self.depth_blur_effect = None

    def apply_stage_visual_effect_block(self, block: dict) -> None:
        config = normalize_native_visual_effect_block(block)
        block_type = config.get("type")
        if block_type == "screen_shake":
            self.screen_shake_effect = {
                **config,
                "remaining": get_effect_duration_seconds(config.get("duration")),
                "durationSeconds": get_effect_duration_seconds(config.get("duration")),
            }
        elif block_type == "screen_flash":
            self.screen_flash_effect = {
                **config,
                "remaining": get_effect_duration_seconds(config.get("duration")),
                "durationSeconds": get_effect_duration_seconds(config.get("duration")),
            }
        elif block_type == "screen_fade":
            self.screen_fade_effect = None if config.get("action") == "fade_in" else config
        elif block_type == "camera_zoom":
            self.camera_zoom_effect = None if config.get("action") == "reset" else config
        elif block_type == "camera_pan":
            self.camera_pan_effect = None if config.get("target") == "center" else config
        elif block_type == "screen_filter":
            self.screen_filter_effect = None if config.get("action") == "clear" else config
        elif block_type == "depth_blur":
            self.depth_blur_effect = None if config.get("action") == "clear" else config
        self.status_message = f"演出已应用：{get_block_label(str(block_type or ''))}"

    def get_runtime_ticks_ms(self) -> int:
        return int(self.pygame.time.get_ticks())

    def start_background_transition(self, previous_asset_id: str | None, block: dict) -> None:
        previous_id = str(previous_asset_id or "").strip()
        next_id = str(self.stage_background_asset_id or "").strip()
        transition = get_safe_basic_transition(block.get("transition"))
        duration_ms = get_safe_transition_duration_ms(block.get("transitionDurationMs"))
        if not previous_id or previous_id == next_id or transition == "none" or duration_ms <= 0:
            self.background_transition = None
            return
        self.background_transition = {
            "previousAssetId": previous_id,
            "nextAssetId": next_id,
            "transition": transition,
            "durationMs": duration_ms,
            "startedAtMs": self.get_runtime_ticks_ms(),
        }

    def get_character_transition_state(self, block: dict, direction: str = "in") -> dict | None:
        return build_native_transition_state(
            block.get("transition"),
            block.get("transitionDurationMs"),
            self.get_runtime_ticks_ms(),
            direction,
        )

    def prune_finished_native_transitions(self) -> None:
        now_ms = self.get_runtime_ticks_ms()
        if self.background_transition and get_native_transition_progress(self.background_transition, now_ms) >= 1.0:
            self.background_transition = None

        for character_id in list(self.leaving_characters):
            transition = (self.leaving_characters.get(character_id) or {}).get("transition")
            if get_native_transition_progress(transition, now_ms) >= 1.0:
                self.leaving_characters.pop(character_id, None)

        for state in self.visible_characters.values():
            if not isinstance(state, dict):
                continue
            transition = state.get("transition")
            if transition and get_native_transition_progress(transition, now_ms) >= 1.0:
                state.pop("transition", None)

    def set_particle_effect(self, effect: dict | None) -> None:
        config = normalize_native_particle_effect_config(effect)
        if config["action"] == "stop":
            self.clear_particle_effect()
            return
        self.active_particle_effect = config
        self.particle_items = build_native_particle_items(config, self.width, self.height)

    def update_particle_effect(self, dt_seconds: float) -> None:
        if not self.active_particle_effect or not self.particle_items:
            return
        config = self.active_particle_effect
        preset = str(config.get("preset") or "snow")
        upward = preset in {"bubbles", "smoke", "flame", "stardust", "glyphs"}
        padding = max(32.0, float(config.get("sizeMax") or 20) * 2.0)
        for index, item in enumerate(self.particle_items):
            item["life"] = max(0.0, float(item.get("life") or 0.0) - dt_seconds)
            item["rotation"] = float(item.get("rotation") or 0.0) + float(item.get("spin") or 0.0) * dt_seconds
            wobble = math.sin(self.runtime_elapsed_seconds * 1.8 + float(item.get("wobblePhase") or 0.0)) * float(item.get("wobble") or 0.0)
            item["x"] = float(item.get("x") or 0.0) + float(item.get("vx") or 0.0) * dt_seconds + wobble * dt_seconds
            item["y"] = float(item.get("y") or 0.0) + float(item.get("vy") or 0.0) * dt_seconds
            out_of_bounds = (
                item["x"] < -padding
                or item["x"] > self.width + padding
                or item["y"] < -padding
                or item["y"] > self.height + padding
            )
            if item["life"] <= 0 or out_of_bounds:
                replacement = build_native_particle_item(config, self.width, self.height)
                if upward:
                    replacement["y"] = random.uniform(self.height * 0.5, self.height + padding * 0.5)
                else:
                    replacement["y"] = random.uniform(-self.height * 0.2, 0.0)
                self.particle_items[index] = replacement

    def update_stage_visual_effects(self, dt_seconds: float) -> None:
        for attr_name in ("screen_shake_effect", "screen_flash_effect"):
            effect = getattr(self, attr_name)
            if not effect:
                continue
            remaining = max(0.0, float(effect.get("remaining") or 0.0) - dt_seconds)
            effect["remaining"] = remaining
            if remaining <= 0:
                setattr(self, attr_name, None)
        self.prune_finished_native_transitions()

    def render_particle_shape(self, surface, shape: str, color: tuple[int, int, int], alpha: int, size: int) -> None:
        draw_color = (*color, max(0, min(255, alpha)))
        center = size // 2
        radius = max(1, size // 2 - 1)
        if shape == "rain":
            self.pygame.draw.line(surface, draw_color, (center, 1), (center + max(1, size // 4), size - 2), max(1, size // 6))
        elif shape == "petal":
            self.pygame.draw.ellipse(surface, draw_color, (1, center // 2, max(2, size - 2), max(2, size // 2)))
        elif shape == "bubble":
            self.pygame.draw.circle(surface, draw_color, (center, center), radius, max(1, size // 8))
            self.pygame.draw.circle(surface, (*color, max(0, min(255, alpha // 2))), (max(1, center - radius // 3), max(1, center - radius // 3)), max(1, radius // 5))
        elif shape == "confetti":
            self.pygame.draw.rect(surface, draw_color, (1, 1, max(2, size - 2), max(2, size // 2)), border_radius=max(1, size // 8))
        elif shape == "smoke":
            self.pygame.draw.circle(surface, draw_color, (center, center), radius)
        elif shape == "flame":
            points = [(center, 1), (size - 2, size - 3), (center, size - 2), (2, size - 3)]
            self.pygame.draw.polygon(surface, draw_color, points)
        elif shape == "ember":
            self.pygame.draw.circle(surface, draw_color, (center, center), radius)
        elif shape == "spark":
            self.pygame.draw.line(surface, draw_color, (center, 0), (center, size), max(1, size // 7))
            self.pygame.draw.line(surface, draw_color, (0, center), (size, center), max(1, size // 7))
        elif shape == "star":
            self.pygame.draw.line(surface, draw_color, (center, 0), (center, size), max(1, size // 8))
            self.pygame.draw.line(surface, draw_color, (0, center), (size, center), max(1, size // 8))
            self.pygame.draw.line(surface, draw_color, (2, 2), (size - 2, size - 2), max(1, size // 9))
            self.pygame.draw.line(surface, draw_color, (size - 2, 2), (2, size - 2), max(1, size // 9))
        elif shape == "glyph":
            rect = self.pygame.Rect(2, 2, max(2, size - 4), max(2, size - 4))
            self.pygame.draw.rect(surface, draw_color, rect, max(1, size // 8), border_radius=max(1, size // 6))
            self.pygame.draw.line(surface, draw_color, (rect.left + 3, rect.centery), (rect.right - 3, rect.centery), max(1, size // 10))
        else:
            self.pygame.draw.circle(surface, draw_color, (center, center), radius)

    def render_particle_effect(self, target=None) -> None:
        if not self.active_particle_effect or not self.particle_items:
            return
        target = target or self.screen
        config = self.active_particle_effect
        asset_id = str(config.get("assetId") or "")
        particle_image = self._load_image(asset_id) if asset_id else None
        for item in self.particle_items:
            progress = 1.0 - (float(item.get("life") or 0.0) / max(0.001, float(item.get("maxLife") or 1.0)))
            size = max(2, int(round(float(item.get("size") or 4.0))))
            alpha = int(round(255 * (0.15 + (1.0 - progress) * 0.85)))
            color = mix_rgb(
                tuple(config.get("color") or (255, 255, 255)),
                tuple(config.get("accentColor") or (214, 238, 255)),
                float(item.get("colorMix") or 0.0) * (0.5 + progress * 0.5),
            )
            if particle_image:
                image = self.pygame.transform.smoothscale(particle_image, (size, size))
                if image.get_flags() & self.pygame.SRCALPHA:
                    image = image.copy()
                image.set_alpha(alpha)
            else:
                image = self.pygame.Surface((size, size), self.pygame.SRCALPHA)
                self.render_particle_shape(image, str(config.get("shape") or "glow"), color, alpha, size)
            rotation = float(item.get("rotation") or 0.0)
            if abs(rotation) > 0.01:
                image = self.pygame.transform.rotozoom(image, -rotation, 1.0)
            rect = image.get_rect(center=(int(item.get("x") or 0), int(item.get("y") or 0)))
            target.blit(image, rect)

    def hydrate_pause_from_current_block(self) -> None:
        scene = self.get_current_scene()
        blocks = (scene or {}).get("blocks", []) or []
        if self.current_block_index >= len(blocks):
            self.handle_scene_finished(scene)
            return

        block = blocks[self.current_block_index]
        block_type = str(block.get("type") or "").strip()
        if block_type == "choice":
            self.current_choices = block.get("options", []) or []
            self.current_choice_index = 0
            self.stop_flow_assist()
            return
        if block_type in {"dialogue", "narration"}:
            line_text = self.localize_value(block, "text")
            self.current_line = {
                "type": block_type,
                "speakerId": block.get("speakerId"),
                "text": line_text,
                "textSpeed": block.get("textSpeed"),
                "voiceAssetId": block.get("voiceAssetId"),
                "voiceVolume": block.get("voiceVolume"),
                "blockLabel": get_block_label(block_type),
            }
            self.sync_archive_progress_for_pause(scene, block, self.current_block_index)
            self.record_text_history(self.current_line, scene, self.current_block_index)
            self.start_current_line_display(line_text)
            if block_type == "dialogue":
                self.sync_expression_for_dialogue(block)
            if block.get("voiceAssetId"):
                self.play_voice(block.get("voiceAssetId"), volume_percent=block.get("voiceVolume"))
            else:
                self.stop_voice()
            return
        self.advance_until_pause()

    def advance_until_pause(self) -> None:
        self.current_line = None
        self.current_choices = None

        while not self.finished:
            scene = self.get_current_scene()
            if not scene:
                self.finished = True
                self.finished_message = "当前路线没有有效场景。"
                return

            blocks = scene.get("blocks", []) or []
            if self.current_block_index >= len(blocks):
                self.handle_scene_finished(scene)
                return

            self.apply_bgm_scope_before_block(scene, self.current_block_index)

            block = blocks[self.current_block_index]
            block_type = str(block.get("type") or "").strip()

            if block_type == "background":
                previous_background_asset_id = self.stage_background_asset_id
                self.stage_background_asset_id = block.get("assetId")
                background_asset = self.assets_by_id.get(self.stage_background_asset_id) or {}
                if background_asset.get("type") == "scene3d":
                    self.apply_scene3d_preview_config(block.get("scene3dPreview") if isinstance(block.get("scene3dPreview"), dict) else None)
                self.start_background_transition(previous_background_asset_id, block)
                if background_asset.get("type") == "cg":
                    self.unlock_archive_entry("cgUnlocked", self.stage_background_asset_id)
                elif background_asset.get("type") in {"background", "scene3d"}:
                    self.unlock_archive_entry("locationUnlocked", self.stage_background_asset_id)
                self.current_block_index += 1
                continue

            if block_type == "character_show":
                character_id = block.get("characterId")
                if character_id:
                    self.unlock_archive_entry("characterUnlocked", character_id)
                    self.visible_characters[character_id] = {
                        "expressionId": block.get("expressionId"),
                        "position": block.get("position"),
                        "stage": get_safe_character_stage(block.get("stage")),
                        "transition": self.get_character_transition_state(block, "in"),
                    }
                    self.leaving_characters.pop(character_id, None)
                self.current_block_index += 1
                continue

            if block_type == "character_hide":
                character_id = block.get("characterId")
                if character_id:
                    previous_state = self.visible_characters.pop(character_id, None)
                    transition = self.get_character_transition_state(block, "out")
                    if previous_state and transition:
                        previous_state["transition"] = transition
                        self.leaving_characters[character_id] = previous_state
                self.current_block_index += 1
                continue

            if block_type == "music_play":
                self.current_bgm_scope = get_music_scope_from_block(block, self.current_scene_id)
                self.play_bgm(
                    block.get("assetId"),
                    loop=bool(block.get("loop", True)),
                    fade_in_ms=get_safe_audio_fade_ms(block.get("fadeInMs"), 600),
                    volume_percent=block.get("volume"),
                )
                self.current_block_index += 1
                continue

            if block_type == "music_stop":
                self.current_bgm_scope = None
                self.stop_bgm(fade_out_ms=get_safe_audio_fade_ms(block.get("fadeOutMs"), 600))
                self.current_block_index += 1
                continue

            if block_type == "particle_effect":
                if str(block.get("action") or "start").strip() == "stop":
                    self.clear_particle_effect()
                    self.status_message = "粒子特效已停止。"
                else:
                    self.set_particle_effect(block)
                    self.status_message = f"粒子特效已启动：{self.active_particle_effect.get('preset') if self.active_particle_effect else 'snow'}"
                self.current_block_index += 1
                continue

            if block_type in {"screen_shake", "screen_flash", "screen_fade", "camera_zoom", "camera_pan", "screen_filter", "depth_blur"}:
                self.apply_stage_visual_effect_block(block)
                self.current_block_index += 1
                continue

            if block_type == "sfx_play":
                self.play_sfx(block.get("assetId"), volume_percent=block.get("volume"))
                self.current_block_index += 1
                continue

            if block_type == "video_play":
                self.stop_embedded_video_playback()
                asset_id = str(block.get("assetId") or "")
                asset = self.assets_by_id.get(asset_id) or {}
                asset_path = get_asset_runtime_path(self.bundle_dir, asset)
                start_time = normalize_video_time_seconds(block.get("startTimeSeconds"))
                end_time = normalize_video_time_seconds(block.get("endTimeSeconds"))
                if end_time <= start_time:
                    end_time = 0.0
                text = self.build_native_video_prompt(block, asset, asset_path)
                self.current_line = {
                    "type": block_type,
                    "speakerId": None,
                    "speakerName": "视频",
                    "text": text,
                    "voiceAssetId": None,
                    "videoAssetId": asset_id,
                    "videoAssetPath": str(asset_path) if asset_path else "",
                    "videoTitle": str(block.get("title") or asset.get("name") or "视频播放"),
                    "videoFileName": asset_path.name if asset_path else "",
                    "videoStartTimeSeconds": start_time,
                    "videoEndTimeSeconds": end_time,
                    "videoClipLabel": build_video_clip_label(start_time, end_time),
                    "videoFit": str(block.get("fit") or "contain"),
                    "videoVolume": clamp_int(block.get("volume"), 0, 100, 100),
                    "videoSkippable": bool(block.get("skippable", True)),
                    "videoPreviewMode": NATIVE_VIDEO_PREVIEW_MODE,
                    "videoOpened": False,
                    "videoPlaybackFinished": False,
                    "videoPlaybackMode": "",
                    "blockLabel": get_block_label(block_type),
                }
                self.stop_voice()
                self.record_text_history(self.current_line, scene, self.current_block_index)
                self.start_current_line_display(text)
                self.reveal_current_line_immediately()
                self.status_message = "视频卡片：按 V 内嵌播放，按 O 使用系统播放器，Enter 继续"
                return

            if block_type == "credits_roll":
                lines = block.get("lines") if isinstance(block.get("lines"), list) else []
                credits_text = "\n".join(str(line) for line in lines[:12] if str(line).strip())
                text = (
                    f"{str(block.get('title') or 'STAFF')}\n"
                    f"{str(block.get('subtitle') or '').strip()}\n\n"
                    f"{credits_text or '感谢游玩。'}"
                ).strip()
                self.current_line = {
                    "type": block_type,
                    "speakerId": None,
                    "speakerName": "片尾字幕",
                    "text": text,
                    "voiceAssetId": None,
                    "blockLabel": get_block_label(block_type),
                }
                self.stop_voice()
                self.record_text_history(self.current_line, scene, self.current_block_index)
                self.start_current_line_display(text)
                self.reveal_current_line_immediately()
                self.status_message = "片尾字幕：按继续推进"
                return

            if block_type == "variable_set":
                self.apply_variable_set(block)
                self.current_block_index += 1
                continue

            if block_type == "variable_add":
                self.apply_variable_add(block)
                self.current_block_index += 1
                continue

            if block_type == "jump":
                self.set_scene(block.get("targetSceneId"))
                continue

            if block_type == "condition":
                self.resolve_condition(block)
                continue

            if block_type == "choice":
                options = block.get("options", []) or []
                self.current_choices = options
                self.current_choice_index = 0
                self.stop_flow_assist()
                self.status_message = f"当前为选项卡：{len(options)} 个分支"
                return

            if block_type in {"dialogue", "narration"}:
                line_text = self.localize_value(block, "text")
                self.current_line = {
                    "type": block_type,
                    "speakerId": block.get("speakerId"),
                    "text": line_text,
                    "textSpeed": block.get("textSpeed"),
                    "voiceAssetId": block.get("voiceAssetId"),
                    "voiceVolume": block.get("voiceVolume"),
                    "blockLabel": get_block_label(block_type),
                }
                self.sync_archive_progress_for_pause(scene, block, self.current_block_index)
                self.record_text_history(self.current_line, scene, self.current_block_index)
                self.start_current_line_display(line_text)
                if block_type == "dialogue":
                    self.sync_expression_for_dialogue(block)
                if block.get("voiceAssetId"):
                    self.play_voice(block.get("voiceAssetId"), volume_percent=block.get("voiceVolume"))
                else:
                    self.stop_voice()
                self.status_message = f"当前卡片：{get_block_label(block_type)}"
                return

            self.current_block_index += 1

    def sync_expression_for_dialogue(self, block: dict) -> None:
        speaker_id = block.get("speakerId")
        if not speaker_id:
            return
        self.unlock_archive_entry("characterUnlocked", speaker_id)
        character = self.characters_by_id.get(speaker_id)
        if not character:
            return
        existing = self.visible_characters.get(speaker_id, {})
        self.visible_characters[speaker_id] = {
            "expressionId": block.get("expressionId") or existing.get("expressionId") or "expr_default",
            "position": existing.get("position") or character.get("defaultPosition") or "center",
            "stage": get_safe_character_stage(existing.get("stage")),
            "transition": existing.get("transition"),
        }

    def play_bgm(
        self,
        asset_id: str | None,
        loop: bool = True,
        fade_in_ms: int = 0,
        volume_percent: object | None = None,
    ) -> None:
        if not self.pygame.mixer.get_init():
            return
        safe_volume_percent = get_safe_volume_percent(volume_percent, 100)
        if asset_id == self.current_bgm_asset_id:
            self.current_bgm_volume_percent = safe_volume_percent
            self.pygame.mixer.music.set_volume(self.get_effective_bgm_volume())
            return
        asset = self.assets_by_id.get(asset_id)
        asset_path = get_asset_runtime_path(self.bundle_dir, asset)
        if not asset_path:
            self.current_bgm_asset_id = None
            self.current_bgm_volume_percent = 100
            self.current_bgm_scope = None
            return
        if asset and asset.get("type") == "bgm":
            self.unlock_archive_entry("bgmUnlocked", asset_id)
        try:
            self.pygame.mixer.music.load(str(asset_path))
            self.current_bgm_volume_percent = safe_volume_percent
            self.pygame.mixer.music.set_volume(self.get_effective_bgm_volume())
            safe_fade_in_ms = get_safe_audio_fade_ms(fade_in_ms)
            try:
                self.pygame.mixer.music.play(-1 if loop else 0, fade_ms=safe_fade_in_ms)
            except TypeError:
                self.pygame.mixer.music.play(-1 if loop else 0)
            self.current_bgm_asset_id = asset_id
        except Exception:
            self.current_bgm_asset_id = None
            self.current_bgm_volume_percent = 100
            self.current_bgm_scope = None

    def stop_bgm(self, fade_out_ms: int = 0) -> None:
        if self.pygame.mixer.get_init():
            safe_fade_out_ms = get_safe_audio_fade_ms(fade_out_ms)
            if safe_fade_out_ms > 0:
                self.pygame.mixer.music.fadeout(safe_fade_out_ms)
            else:
                self.pygame.mixer.music.stop()
        self.current_bgm_asset_id = None
        self.current_bgm_volume_percent = 100
        self.current_bgm_scope = None

    def play_sfx(self, asset_id: str | None, volume_percent: object | None = None) -> None:
        sound = self._load_sound(asset_id)
        if sound:
            try:
                sound_volume = get_safe_volume_percent(volume_percent, 100) / 100
                sound.set_volume(self.get_effective_volume("sfxVolume") * sound_volume)
                sound.play()
            except Exception:
                return

    def play_voice(self, asset_id: str | None, volume_percent: object | None = None) -> bool:
        self.stop_voice()
        sound = self._load_sound(asset_id)
        if not sound:
            return False
        try:
            self.current_voice_volume_percent = get_safe_volume_percent(volume_percent, 100)
            sound.set_volume(self.get_effective_voice_volume())
            self.current_voice_channel = sound.play()
            return True
        except Exception:
            self.current_voice_channel = None
            self.current_voice_volume_percent = 100
            return False

    def stop_voice(self) -> None:
        if self.current_voice_channel:
            try:
                self.current_voice_channel.stop()
            except Exception:
                pass
        self.current_voice_channel = None
        self.current_voice_volume_percent = 100

    def stop_embedded_video_playback(self) -> None:
        if self.embedded_video_playback:
            self.embedded_video_playback.release()
        self.embedded_video_playback = None

    def build_native_video_prompt(self, block: dict, asset: dict, asset_path: Path | None) -> str:
        title = str(block.get("title") or asset.get("name") or "视频播放")
        start_time = normalize_video_time_seconds(block.get("startTimeSeconds"))
        end_time = normalize_video_time_seconds(block.get("endTimeSeconds"))
        if end_time <= start_time:
            end_time = 0.0
        lines = [
            title,
            "",
            "原生 Runtime Preview 会优先尝试 PyAV/FFmpeg 音画同步内嵌播放；依赖或编码不匹配时，会自动回落到 OpenCV 画面播放或系统播放器桥接。",
        ]
        if asset_path:
            lines.extend(
                [
                    f"文件：{asset_path.name}",
                    "操作：按 V 播放/暂停内嵌视频；按 O 调用系统播放器；播放结束后按 Enter 继续。",
                ]
            )
        else:
            lines.extend(
                [
                    "视频文件没有被找到，可能是素材缺失或导出包不完整。",
                    "建议回到编辑器重新导出，或改用网页包 / NW.js 桌面包验证视频。",
                ]
            )

        has_clip_range = start_time > 0 or end_time > 0
        if has_clip_range:
            lines.append(
                f"剪辑提示：编辑器设置了 {build_video_clip_label(start_time, end_time)}；"
                "内嵌播放会按该区间停下；系统播放器桥接不会强制裁切。"
            )
        if not bool(block.get("skippable", True)):
            lines.append("不可跳过提示：需要先播放视频；如果使用内嵌播放，需要播放结束后才能继续。")
        lines.append("音画提示：安装可选视频依赖后会走 PyAV 同步播放；若当前机器不支持该编码，仍可按 O 使用系统播放器兜底。")
        return "\n".join(lines)

    def get_video_preview_cache_key(self, line: dict) -> str:
        video_path_value = str(line.get("videoAssetPath") or "").strip()
        if not video_path_value:
            return ""
        start_time = normalize_video_time_seconds(line.get("videoStartTimeSeconds"))
        return f"{Path(video_path_value).resolve()}::{start_time:.3f}"

    def get_video_preview_frame_result(self, line: dict) -> dict:
        cache_key = self.get_video_preview_cache_key(line)
        if not cache_key:
            return {"surface": None, "status": "视频文件缺失"}
        if cache_key not in self.video_preview_frame_cache:
            video_path_value = str(line.get("videoAssetPath") or "").strip()
            start_time = normalize_video_time_seconds(line.get("videoStartTimeSeconds"))
            surface, status = load_opencv_video_frame_surface(self.pygame, Path(video_path_value), start_time)
            self.video_preview_frame_cache[cache_key] = {"surface": surface, "status": status}
        return self.video_preview_frame_cache[cache_key]

    def get_current_embedded_video_surface(self):
        if self.embedded_video_playback:
            self.embedded_video_playback.update(self.pygame.time.get_ticks())
            if self.embedded_video_playback.finished and self.current_line and self.current_line.get("type") == "video_play":
                self.current_line["videoOpened"] = True
                self.current_line["videoPlaybackFinished"] = True
                self.current_line["videoPlaybackMode"] = getattr(
                    self.embedded_video_playback,
                    "backend_id",
                    NATIVE_VIDEO_EMBEDDED_BACKEND_ID,
                )
                self.status_message = self.embedded_video_playback.status_message
            return self.embedded_video_playback.current_surface
        return None

    def get_current_embedded_video_status(self) -> str:
        if not self.embedded_video_playback:
            return ""
        return str(self.embedded_video_playback.status or "")

    def create_embedded_video_playback(
        self,
        video_path: Path,
        start_time_seconds: float,
        end_time_seconds: float,
        fit_mode: str,
        volume: int,
    ) -> tuple[PyAvSynchronizedVideoPlayback | OpenCvEmbeddedVideoPlayback | None, str]:
        attempts: list[PyAvSynchronizedVideoPlayback | OpenCvEmbeddedVideoPlayback] = [
            PyAvSynchronizedVideoPlayback(
                self.pygame,
                video_path,
                start_time_seconds=start_time_seconds,
                end_time_seconds=end_time_seconds,
                fit_mode=fit_mode,
                volume=volume,
            ),
            OpenCvEmbeddedVideoPlayback(
                self.pygame,
                video_path,
                start_time_seconds=start_time_seconds,
                end_time_seconds=end_time_seconds,
                fit_mode=fit_mode,
            ),
        ]
        failure_messages = []
        for playback in attempts:
            opened, message = playback.open()
            if opened:
                if failure_messages:
                    return playback, f"{message}；此前尝试：{' / '.join(failure_messages)}"
                return playback, message
            failure_messages.append(message)
            playback.release()
        return None, "；".join(failure_messages) or "没有可用的内嵌视频后端"

    def start_or_toggle_embedded_video(self) -> bool:
        if not self.current_line or self.current_line.get("type") != "video_play":
            return False
        video_path_value = str(self.current_line.get("videoAssetPath") or "").strip()
        if not video_path_value:
            self.status_message = "当前视频文件不存在，无法打开。"
            return False
        now_ms = self.pygame.time.get_ticks()
        if self.embedded_video_playback and self.embedded_video_playback.status in {"playing", "paused"}:
            self.embedded_video_playback.toggle_pause(now_ms)
            self.status_message = self.embedded_video_playback.status_message
            return True
        self.stop_embedded_video_playback()
        start_time_seconds = normalize_video_time_seconds(self.current_line.get("videoStartTimeSeconds"))
        end_time_seconds = normalize_video_time_seconds(self.current_line.get("videoEndTimeSeconds"))
        fit_mode = str(self.current_line.get("videoFit") or "contain")
        volume = clamp_int(self.current_line.get("videoVolume"), 0, 100, 100)
        playback, message = self.create_embedded_video_playback(
            Path(video_path_value),
            start_time_seconds,
            end_time_seconds,
            fit_mode,
            volume,
        )
        if playback is None:
            self.status_message = f"{message}；已回落到系统播放器桥接。"
            return False
        playback.play(now_ms)
        playback.update(now_ms)
        self.embedded_video_playback = playback
        self.current_line["videoOpened"] = True
        self.current_line["videoPlaybackFinished"] = bool(playback.finished)
        self.current_line["videoPlaybackMode"] = playback.backend_id
        if playback.backend_id == NATIVE_VIDEO_SYNC_BACKEND_ID and getattr(playback, "audio_channel", None):
            self.status_message = "PyAV 音画同步播放中；按 Space 暂停，O 可用系统播放器兜底。"
        elif playback.backend_id == NATIVE_VIDEO_SYNC_BACKEND_ID:
            self.status_message = "PyAV 画面播放中（音频不可用）；按 Space 暂停，O 可用系统播放器兜底。"
        else:
            self.status_message = "OpenCV 内嵌画面播放中（无音频）；按 Space 暂停，O 可用系统播放器播放。"
        self.reveal_current_line_immediately()
        return True

    def open_current_video_external(self) -> None:
        if not self.current_line or self.current_line.get("type") != "video_play":
            return
        self.stop_embedded_video_playback()
        video_path_value = str(self.current_line.get("videoAssetPath") or "").strip()
        if not video_path_value:
            self.status_message = "当前视频文件不存在，无法打开。"
            return
        success, message = open_external_video(Path(video_path_value))
        self.current_line["videoOpened"] = bool(success)
        if success:
            self.current_line["videoPlaybackMode"] = "system_player_bridge"
            self.current_line["videoPlaybackFinished"] = True
        self.status_message = message
        self.reveal_current_line_immediately()

    def open_current_video(self) -> None:
        if not self.start_or_toggle_embedded_video():
            self.open_current_video_external()

    def can_advance_current_line(self) -> bool:
        if not self.current_line or self.current_line.get("type") != "video_play":
            return True
        if (
            self.embedded_video_playback
            and self.embedded_video_playback.status in {"playing", "paused"}
            and self.current_line.get("videoSkippable") is False
        ):
            self.status_message = "这段视频标记为不可跳过，请等待内嵌播放结束后再确认。"
            return False
        requires_confirmation = (
            self.current_line.get("videoSkippable") is False
            and bool(self.current_line.get("videoAssetPath"))
            and not bool(self.current_line.get("videoOpened"))
        )
        if not requires_confirmation:
            return True
        self.status_message = "这段视频标记为不可跳过，请先按 V 播放，再回到窗口确认继续。"
        return False

    def advance_current_line_if_allowed(self) -> None:
        if self.can_advance_current_line():
            self.stop_embedded_video_playback()
            self.advance_dialogue()

    def handle_video_card_mouse_event(self, event) -> bool:
        for target in self.video_hotspots:
            if not target["rect"].collidepoint(event.pos):
                continue
            if target.get("disabled"):
                self.can_advance_current_line()
                return True
            if target.get("kind") == "play-video":
                self.open_current_video()
                return True
            if target.get("kind") == "external-video":
                self.open_current_video_external()
                return True
            if target.get("kind") == "continue-video":
                self.advance_current_line_if_allowed()
                return True
        return True

    def build_initial_variable_state(self) -> dict:
        return {
            variable_id: coerce_runtime_variable_value(variable, variable.get("defaultValue"))
            for variable_id, variable in self.variables_by_id.items()
        }

    def normalize_runtime_variable_value(self, variable_id: str | None, value: object) -> object:
        variable = self.variables_by_id.get(str(variable_id or ""))
        if not variable:
            return None
        return coerce_runtime_variable_value(variable, value)

    def merge_variable_state(self, variable_state: dict | None) -> dict:
        merged_state = self.build_initial_variable_state()
        if not isinstance(variable_state, dict):
            return merged_state
        for variable_id, value in variable_state.items():
            safe_variable_id = str(variable_id or "")
            if safe_variable_id in self.variables_by_id:
                merged_state[safe_variable_id] = self.normalize_runtime_variable_value(safe_variable_id, value)
        return merged_state

    def get_runtime_variable_value(self, variable_id: str | None) -> object:
        safe_variable_id = str(variable_id or "")
        if safe_variable_id not in self.variables_by_id:
            return None
        if safe_variable_id not in self.variable_state:
            self.variable_state[safe_variable_id] = self.normalize_runtime_variable_value(
                safe_variable_id,
                self.variables_by_id[safe_variable_id].get("defaultValue"),
            )
        return self.variable_state.get(safe_variable_id)

    def apply_variable_set(self, block: dict) -> None:
        variable_id = str(block.get("variableId") or "")
        if variable_id not in self.variables_by_id:
            return
        self.variable_state[variable_id] = self.normalize_runtime_variable_value(variable_id, block.get("value"))

    def apply_variable_add(self, block: dict) -> None:
        variable_id = str(block.get("variableId") or "")
        variable = self.variables_by_id.get(variable_id)
        if normalize_variable_type((variable or {}).get("type")) != "number":
            return
        current = self.get_runtime_variable_value(variable_id)
        try:
            current_number = float(current)
        except (TypeError, ValueError):
            current_number = 0.0
        try:
            delta = float(block.get("value", 0))
        except (TypeError, ValueError):
            delta = 0.0
        next_value = current_number + delta
        if int(next_value) == next_value:
            next_value = int(next_value)
        self.variable_state[variable_id] = self.normalize_runtime_variable_value(variable_id, next_value)

    def evaluate_operator(self, current_value, operator: str, target_value) -> bool:
        if operator in {"==", "="}:
            return current_value == target_value
        if operator == "!=":
            return current_value != target_value
        try:
            left = float(current_value)
            right = float(target_value)
        except (TypeError, ValueError):
            left = str(current_value)
            right = str(target_value)
        if operator == ">":
            return left > right
        if operator == ">=":
            return left >= right
        if operator == "<":
            return left < right
        if operator == "<=":
            return left <= right
        return False

    def evaluate_when(self, conditions: list[dict]) -> bool:
        if not conditions:
            return False
        for condition in conditions:
            variable_id = str(condition.get("variableId") or "")
            operator = str(condition.get("operator") or "==")
            expected_value = self.normalize_runtime_variable_value(variable_id, condition.get("value"))
            current_value = self.get_runtime_variable_value(variable_id)
            if not self.evaluate_operator(current_value, operator, expected_value):
                return False
        return True

    def resolve_condition(self, block: dict) -> None:
        for branch in block.get("branches", []) or []:
            if self.evaluate_when(branch.get("when", []) or []):
                self.set_scene(branch.get("gotoSceneId"))
                return
        self.set_scene(block.get("elseGotoSceneId"))

    def apply_choice_effect(self, effect: dict) -> None:
        effect_type = effect.get("type")
        if effect_type == "variable_set":
            self.apply_variable_set(effect)
        elif effect_type == "variable_add":
            self.apply_variable_add(effect)

    def choose_current_option(self, option_index: int) -> None:
        if not self.current_choices:
            return
        option = self.current_choices[option_index]
        for effect in option.get("effects", []) or []:
            self.apply_choice_effect(effect)
        self.current_block_index += 1
        target_scene_id = option.get("gotoSceneId") or option.get("targetSceneId")
        self.current_choices = None
        if target_scene_id:
            self.set_scene(target_scene_id)
        self.advance_until_pause()
        self.auto_resume_write_enabled = True
        self.persist_auto_resume_snapshot()

    def advance_dialogue(self) -> None:
        if self.current_line:
            if not self.is_current_line_fully_visible():
                self.reveal_current_line_immediately()
                return
            self.mark_current_line_read()
            self.current_line = None
            self.current_block_index += 1
            self.advance_until_pause()
            self.auto_resume_write_enabled = True
            self.persist_auto_resume_snapshot()

    def get_character_sprite_asset_id(self, character_id: str, expression_id: str | None) -> str | None:
        character = self.characters_by_id.get(character_id) or {}
        expressions = character.get("expressions", []) or []
        expression_map = {item.get("id"): item for item in expressions if item.get("id")}
        selected = expression_map.get(expression_id) or expression_map.get("expr_default")
        if selected and selected.get("spriteAssetId"):
            return selected["spriteAssetId"]
        presentation = self.get_character_presentation(character)
        return presentation.get("fallbackSpriteAssetId") or character.get("defaultSpriteId")

    def get_character_presentation(self, character: dict | None) -> dict:
        character = character or {}
        source = character.get("presentation") if isinstance(character.get("presentation"), dict) else {}
        mode = str(source.get("mode") or "sprite")
        if mode not in CHARACTER_PRESENTATION_MODE_LABELS:
            mode = "sprite"
        live2d = source.get("live2d") if isinstance(source.get("live2d"), dict) else {}
        model3d = source.get("model3d") if isinstance(source.get("model3d"), dict) else {}
        return {
            "mode": mode,
            "fallbackSpriteAssetId": str(source.get("fallbackSpriteAssetId") or character.get("defaultSpriteId") or ""),
            "live2d": {
                "modelAssetId": str(live2d.get("modelAssetId") or ""),
                "idleMotion": str(live2d.get("idleMotion") or ""),
            },
            "model3d": {
                "modelAssetId": str(model3d.get("modelAssetId") or ""),
                "idleAnimation": str(model3d.get("idleAnimation") or ""),
            },
        }

    def get_character_presentation_mode_label(self, character: dict | None) -> str:
        return CHARACTER_PRESENTATION_MODE_LABELS.get(
            str(self.get_character_presentation(character).get("mode") or "sprite"),
            CHARACTER_PRESENTATION_MODE_LABELS["sprite"],
        )

    def get_character_model_asset_label(self, character: dict | None) -> str:
        presentation = self.get_character_presentation(character)
        mode = str(presentation.get("mode") or "sprite")
        model_asset_id = ""
        if mode == "live2d":
            model_asset_id = str((presentation.get("live2d") or {}).get("modelAssetId") or "")
        elif mode == "model3d":
            model_asset_id = str((presentation.get("model3d") or {}).get("modelAssetId") or "")
        if not model_asset_id:
            return "模型未绑定"
        asset = self.assets_by_id.get(model_asset_id) or {}
        return str(asset.get("name") or model_asset_id)

    def get_character_expression_binding_label(self, character: dict | None, expression_id: str | None) -> str:
        character = character or {}
        expressions = character.get("expressions", []) or []
        expression_map = {item.get("id"): item for item in expressions if item.get("id")}
        selected = expression_map.get(expression_id) or expression_map.get("expr_default")
        if not selected:
            return "表情映射：未配置"
        labels = []
        layer_count = len(selected.get("layerAssetIds") or [])
        if layer_count:
            labels.append(f"差分 {layer_count}")
        live2d_binding = " / ".join(
            item
            for item in [
                str(selected.get("live2dExpression") or "").strip(),
                str(selected.get("live2dMotion") or "").strip(),
            ]
            if item
        )
        if live2d_binding:
            labels.append(f"Live2D {live2d_binding}")
        model3d_binding = " / ".join(
            item
            for item in [
                str(selected.get("model3dExpression") or "").strip(),
                str(selected.get("model3dAnimation") or "").strip(),
            ]
            if item
        )
        if model3d_binding:
            labels.append(f"3D {model3d_binding}")
        return "表情映射：" + (" · ".join(labels) if labels else "沿用默认")

    def get_character_model_asset_id(self, character: dict | None) -> str:
        presentation = self.get_character_presentation(character)
        mode = str(presentation.get("mode") or "sprite")
        if mode == "live2d":
            return str((presentation.get("live2d") or {}).get("modelAssetId") or "").strip()
        if mode == "model3d":
            return str((presentation.get("model3d") or {}).get("modelAssetId") or "").strip()
        return ""

    def summarize_model_dependency_health(self, mode: str, model_path: Path | None) -> dict:
        if not model_path:
            return {"total": 0, "missing": [], "unsafe": [], "status": "unknown", "label": "依赖：待检测"}

        lower_name = model_path.name.lower()
        references: list[str] = []
        missing: list[str] = []
        unsafe: list[str] = []
        status = "ready"

        if mode == "live2d" and lower_name.endswith(".model3.json"):
            try:
                references = collect_live2d_model3_references(json.loads(model_path.read_text(encoding="utf-8")))
            except Exception:
                return {"total": 0, "missing": [], "unsafe": [], "status": "invalid", "label": "依赖：入口 JSON 异常"}
            for reference in references:
                dependency_path = resolve_live2d_dependency_path(model_path, reference, self.bundle_dir)
                if dependency_path is None:
                    unsafe.append(reference)
                elif not dependency_path.is_file():
                    missing.append(reference)
        elif mode == "model3d" and model_path.suffix.lower() == ".gltf":
            try:
                references = collect_gltf_references(json.loads(model_path.read_text(encoding="utf-8")))
            except Exception:
                return {"total": 0, "missing": [], "unsafe": [], "status": "invalid", "label": "依赖：gltf JSON 异常"}
            for reference in references:
                dependency_path = resolve_model3d_dependency_path(model_path, reference, self.bundle_dir)
                if dependency_path is None:
                    unsafe.append(reference)
                elif not dependency_path.is_file():
                    missing.append(reference)
        elif mode == "model3d" and model_path.suffix.lower() in {".glb", ".vrm"}:
            return {"total": 0, "missing": [], "unsafe": [], "status": "ready", "label": f"依赖：{model_path.suffix.upper()[1:]} 单文件"}
        elif mode == "model3d" and model_path.suffix.lower() in {".fbx", ".obj"}:
            return {"total": 0, "missing": [], "unsafe": [], "status": "partial", "label": "依赖：需转换/材质复核"}
        elif mode == "live2d":
            return {"total": 0, "missing": [], "unsafe": [], "status": "partial", "label": "依赖：建议绑定 model3.json"}

        if unsafe or missing:
            status = "partial"
        if not references:
            return {"total": 0, "missing": missing, "unsafe": unsafe, "status": status, "label": "依赖：无外部引用"}
        ready_count = max(0, len(references) - len(missing) - len(unsafe))
        if status == "ready":
            label = f"依赖：{ready_count}/{len(references)} 已就绪"
        else:
            label = f"依赖：缺 {len(missing) + len(unsafe)}/{len(references)} 项"
        return {"total": len(references), "missing": missing, "unsafe": unsafe, "status": status, "label": label}

    def get_character_model_preview_report(self, character: dict | None, expression_id: str | None = None) -> dict:
        character = character or {}
        presentation = self.get_character_presentation(character)
        mode = str(presentation.get("mode") or "sprite")
        mode_label = self.get_character_presentation_mode_label(character)
        fallback_asset_id = str(presentation.get("fallbackSpriteAssetId") or character.get("defaultSpriteId") or "").strip()
        fallback_asset = self.assets_by_id.get(fallback_asset_id) if fallback_asset_id else None
        fallback_path = get_asset_runtime_path(self.bundle_dir, fallback_asset)
        fallback_status = "ready" if fallback_path else ("missing" if fallback_asset_id else "none")
        model_asset_id = self.get_character_model_asset_id(character)
        model_asset = self.assets_by_id.get(model_asset_id) if model_asset_id else None
        model_path = get_asset_runtime_path(self.bundle_dir, model_asset)
        dependency_health = self.summarize_model_dependency_health(mode, model_path)

        if mode not in {"live2d", "model3d"}:
            status = "sprite"
        elif not model_asset_id:
            status = "unbound"
        elif not model_asset:
            status = "missing_asset"
        elif not model_path:
            status = "missing_file"
        elif dependency_health.get("status") == "invalid":
            status = "invalid"
        elif dependency_health.get("status") == "partial":
            status = "partial"
        else:
            status = "ready"

        status_label = {
            "sprite": "普通立绘",
            "unbound": "模型未绑定",
            "missing_asset": "素材记录缺失",
            "missing_file": "模型文件缺失",
            "invalid": "入口异常",
            "partial": "需要补强",
            "ready": "资源完整",
        }.get(status, "待检查")

        return {
            "isAdvanced": mode in {"live2d", "model3d"},
            "mode": mode,
            "modeLabel": mode_label,
            "status": status,
            "statusLabel": status_label,
            "modelAssetId": model_asset_id,
            "modelAssetName": str((model_asset or {}).get("name") or model_asset_id or "未绑定"),
            "modelExportUrl": str((model_asset or {}).get("exportUrl") or ""),
            "modelPath": model_path,
            "dependencyHealth": dependency_health,
            "fallbackStatus": fallback_status,
            "fallbackAssetName": str((fallback_asset or {}).get("name") or fallback_asset_id or "未绑定"),
            "bindingLabel": self.get_character_expression_binding_label(character, expression_id),
        }

    def get_character_model_preview_lines(self, character: dict | None, expression_id: str | None = None) -> list[str]:
        report = self.get_character_model_preview_report(character, expression_id)
        if not report.get("isAdvanced"):
            return []
        fallback_label = {
            "ready": f"兜底：{report['fallbackAssetName']}",
            "missing": "兜底：素材文件缺失",
            "none": "兜底：未绑定",
        }.get(str(report.get("fallbackStatus") or ""), "兜底：待检查")
        binding_label = str(report.get("bindingLabel") or "表情映射：沿用默认").replace("表情映射：", "映射：", 1)
        return [
            f"{report['modeLabel']} 预览桥：{report['statusLabel']}",
            f"入口：{report['modelAssetName']}",
            str((report.get("dependencyHealth") or {}).get("label") or "依赖：待检测"),
            binding_label,
            fallback_label,
        ]

    def get_scene3d_asset(self, asset_id: str | None = None) -> dict | None:
        safe_asset_id = str(asset_id or self.stage_background_asset_id or "").strip()
        if not safe_asset_id:
            return None
        asset = self.assets_by_id.get(safe_asset_id)
        return asset if asset and asset.get("type") == "scene3d" else None

    def get_scene3d_preview_config(self, source: dict | None = None) -> dict:
        return normalize_scene3d_preview_config(source)

    def apply_scene3d_preview_config(self, source: dict | None = None) -> None:
        config = self.get_scene3d_preview_config(source)
        self.scene3d_preview_yaw = config["yaw"]
        self.scene3d_preview_pitch = config["pitch"]
        self.scene3d_preview_zoom = config["zoom"]
        self.scene3d_preview_interaction_enabled = bool(config["interactionEnabled"])

    def get_scene3d_preview_report(self, asset_id: str | None = None) -> dict:
        asset = self.get_scene3d_asset(asset_id)
        if not asset:
            return {
                "isScene3d": False,
                "status": "none",
                "statusLabel": "未使用 3D 场景",
                "dependencyHealth": {"status": "unknown", "label": "依赖：待检测"},
                "structureSummary": {"status": "unknown", "label": "结构：待检测"},
            }
        asset_path = get_asset_runtime_path(self.bundle_dir, asset)
        dependency_health = self.summarize_model_dependency_health("model3d", asset_path)
        structure_summary = summarize_gltf_structure(asset_path)
        if asset.get("isMissing") or not asset_path:
            status = "missing_file"
        elif dependency_health.get("status") == "invalid" or structure_summary.get("status") == "invalid":
            status = "invalid"
        elif dependency_health.get("status") == "partial" or structure_summary.get("status") == "empty":
            status = "partial"
        else:
            status = "ready"
        return {
            "isScene3d": True,
            "assetId": str(asset.get("id") or ""),
            "name": str(asset.get("name") or asset.get("id") or "未命名 3D 场景"),
            "exportUrl": str(asset.get("exportUrl") or ""),
            "status": status,
            "statusLabel": {
                "missing_file": "场景文件缺失",
                "invalid": "入口异常",
                "partial": "需要补强",
                "ready": "资源完整",
            }.get(status, "待检查"),
            "dependencyHealth": dependency_health,
            "structureSummary": structure_summary,
            "preview": {
                "yaw": round(float(self.scene3d_preview_yaw), 1),
                "pitch": round(float(self.scene3d_preview_pitch), 1),
                "zoom": round(float(self.scene3d_preview_zoom), 2),
                "interactionEnabled": bool(self.scene3d_preview_interaction_enabled),
            },
        }

    def get_scene3d_preview_lines(self, asset_id: str | None = None) -> list[str]:
        report = self.get_scene3d_preview_report(asset_id)
        if not report.get("isScene3d"):
            return []
        preview = report.get("preview") or {}
        return [
            f"3D 场景预览桥：{report.get('statusLabel') or '待检查'}",
            f"入口：{report.get('name') or '未绑定'}",
            str((report.get("dependencyHealth") or {}).get("label") or "依赖：待检测"),
            str((report.get("structureSummary") or {}).get("label") or "结构：待检测"),
            f"视角：yaw {preview.get('yaw')}° / pitch {preview.get('pitch')}° / zoom {preview.get('zoom')}x",
            "交互：←→旋转 · ↑↓俯仰 · +/-缩放 · 0复位" if report.get("preview", {}).get("interactionEnabled") else "交互：本卡片已锁定视角",
        ]

    def adjust_scene3d_preview(self, *, yaw_delta: float = 0.0, pitch_delta: float = 0.0, zoom_delta: float = 0.0, reset: bool = False) -> None:
        if reset:
            self.scene3d_preview_yaw = 32.0
            self.scene3d_preview_pitch = 34.0
            self.scene3d_preview_zoom = 1.0
        else:
            self.scene3d_preview_yaw = (float(self.scene3d_preview_yaw) + yaw_delta) % 360
            self.scene3d_preview_pitch = clamp(float(self.scene3d_preview_pitch) + pitch_delta, 12.0, 72.0)
            self.scene3d_preview_zoom = clamp(float(self.scene3d_preview_zoom) + zoom_delta, 0.55, 1.9)
        report = self.get_scene3d_preview_report()
        preview = report.get("preview") or {}
        self.status_message = (
            f"3D 场景预览：yaw {preview.get('yaw')}° / pitch {preview.get('pitch')}° / zoom {preview.get('zoom')}x"
        )

    def handle_scene3d_preview_key(self, event) -> bool:
        if not self.get_scene3d_asset() or not self.scene3d_preview_interaction_enabled:
            return False
        key = event.key
        if key == self.pygame.K_LEFT:
            self.adjust_scene3d_preview(yaw_delta=-8)
            return True
        if key == self.pygame.K_RIGHT:
            self.adjust_scene3d_preview(yaw_delta=8)
            return True
        if key == self.pygame.K_UP:
            self.adjust_scene3d_preview(pitch_delta=4)
            return True
        if key == self.pygame.K_DOWN:
            self.adjust_scene3d_preview(pitch_delta=-4)
            return True
        plus_keys = {self.pygame.K_EQUALS, getattr(self.pygame, "K_PLUS", self.pygame.K_EQUALS), self.pygame.K_KP_PLUS}
        minus_keys = {self.pygame.K_MINUS, self.pygame.K_KP_MINUS}
        zero_keys = {self.pygame.K_0, self.pygame.K_KP0}
        if key in plus_keys:
            self.adjust_scene3d_preview(zoom_delta=0.08)
            return True
        if key in minus_keys:
            self.adjust_scene3d_preview(zoom_delta=-0.08)
            return True
        if key in zero_keys:
            self.adjust_scene3d_preview(reset=True)
            return True
        return False

    def get_stage_zoom_scale(self) -> float:
        if not self.camera_zoom_effect:
            return 1.0
        action = str(self.camera_zoom_effect.get("action") or "zoom_in")
        strength = str(self.camera_zoom_effect.get("strength") or "medium")
        return CAMERA_ZOOM_SCALE.get((action, strength), 1.0)

    def get_stage_pan_offset(self) -> int:
        if not self.camera_pan_effect:
            return 0
        target = str(self.camera_pan_effect.get("target") or "center")
        strength = str(self.camera_pan_effect.get("strength") or "medium")
        base = CAMERA_PAN_OFFSET.get(target, 0.0)
        multiplier = CAMERA_PAN_STRENGTH_MULTIPLIER.get(strength, 1.0)
        return int(round(self.width * base * multiplier))

    def get_stage_shake_offset(self) -> tuple[int, int]:
        if not self.screen_shake_effect:
            return (0, 0)
        intensity = str(self.screen_shake_effect.get("intensity") or "medium")
        distance = SHAKE_DISTANCE.get(intensity, SHAKE_DISTANCE["medium"])
        phase = self.runtime_elapsed_seconds * 74.0
        return (int(math.sin(phase) * distance), int(math.cos(phase * 1.31) * distance * 0.55))

    def render_stage_surface(self, stage_surface) -> None:
        scale = self.get_stage_zoom_scale()
        offset_x = self.get_stage_pan_offset()
        shake_x, shake_y = self.get_stage_shake_offset()
        if abs(scale - 1.0) > 0.01:
            scaled_size = (max(1, int(self.width * scale)), max(1, int(self.height * scale)))
            stage_surface = self.pygame.transform.smoothscale(stage_surface, scaled_size)
        rect = stage_surface.get_rect(center=(self.width // 2 + offset_x + shake_x, self.height // 2 + shake_y))
        self.screen.blit(stage_surface, rect)

    def render_stage_effect_overlays(self) -> None:
        if self.screen_filter_effect:
            preset = str(self.screen_filter_effect.get("preset") or "memory")
            strength = str(self.screen_filter_effect.get("strength") or "medium")
            grade = get_safe_screen_color_grade(self.screen_filter_effect.get("grade"))
            wash_color, base_alpha = SCREEN_FILTER_WASH.get(preset, SCREEN_FILTER_WASH["memory"])
            alpha = int(base_alpha * SCREEN_FILTER_STRENGTH_MULTIPLIER.get(strength, 1.0))
            wash = self.pygame.Surface((self.width, self.height), self.pygame.SRCALPHA)
            wash.fill((*wash_color, max(0, min(160, alpha))))
            self.screen.blit(wash, (0, 0))

            temperature = int(grade.get("temperature") or 0)
            if temperature:
                temp_color = (255, 184, 102) if temperature > 0 else (108, 172, 255)
                temp_alpha = int(min(54, abs(temperature) / 100 * 54))
                temp_wash = self.pygame.Surface((self.width, self.height), self.pygame.SRCALPHA)
                temp_wash.fill((*temp_color, temp_alpha))
                self.screen.blit(temp_wash, (0, 0))

            brightness_delta = int(grade.get("brightness") or 100) - 100
            if brightness_delta:
                tone = 255 if brightness_delta > 0 else 0
                tone_alpha = int(min(72, abs(brightness_delta) / 80 * 72))
                tone_wash = self.pygame.Surface((self.width, self.height), self.pygame.SRCALPHA)
                tone_wash.fill((tone, tone, tone, tone_alpha))
                self.screen.blit(tone_wash, (0, 0))

            contrast_delta = int(grade.get("contrast") or 100) - 100
            if contrast_delta > 0:
                multiplier = 255 - int(min(42, contrast_delta / 80 * 42))
                contrast_wash = self.pygame.Surface((self.width, self.height), self.pygame.SRCALPHA)
                contrast_wash.fill((multiplier, multiplier, multiplier, 255))
                self.screen.blit(contrast_wash, (0, 0), special_flags=self.pygame.BLEND_RGBA_MULT)
            elif contrast_delta < 0:
                flat_alpha = int(min(42, abs(contrast_delta) / 80 * 42))
                flat_wash = self.pygame.Surface((self.width, self.height), self.pygame.SRCALPHA)
                flat_wash.fill((140, 148, 160, flat_alpha))
                self.screen.blit(flat_wash, (0, 0))

            saturation_delta = int(grade.get("saturation") or 100) - 100
            if saturation_delta < 0:
                gray_alpha = int(min(58, abs(saturation_delta) / 100 * 58))
                gray_wash = self.pygame.Surface((self.width, self.height), self.pygame.SRCALPHA)
                gray_wash.fill((184, 192, 206, gray_alpha))
                self.screen.blit(gray_wash, (0, 0))

            hue_shift = int(grade.get("hue") or 0)
            if hue_shift:
                hue_color = (142, 106, 255) if hue_shift > 0 else (94, 222, 184)
                hue_alpha = int(min(34, abs(hue_shift) / 180 * 34))
                hue_wash = self.pygame.Surface((self.width, self.height), self.pygame.SRCALPHA)
                hue_wash.fill((*hue_color, hue_alpha))
                self.screen.blit(hue_wash, (0, 0))

            vignette = int(grade.get("vignette") or 0)
            if vignette > 0:
                vignette_surface = self.pygame.Surface((self.width, self.height), self.pygame.SRCALPHA)
                max_alpha = int(min(122, vignette / 100 * 122))
                band = max(1, int(min(self.width, self.height) * 0.16))
                for index in range(6):
                    ratio = (index + 1) / 6
                    alpha_step = int(max_alpha * ratio)
                    inset = int(band * (1 - ratio))
                    self.pygame.draw.rect(vignette_surface, (2, 6, 12, alpha_step), self.pygame.Rect(0, 0, self.width, max(1, band - inset)))
                    self.pygame.draw.rect(vignette_surface, (2, 6, 12, alpha_step), self.pygame.Rect(0, self.height - max(1, band - inset), self.width, max(1, band - inset)))
                    self.pygame.draw.rect(vignette_surface, (2, 6, 12, alpha_step), self.pygame.Rect(0, 0, max(1, band - inset), self.height))
                    self.pygame.draw.rect(vignette_surface, (2, 6, 12, alpha_step), self.pygame.Rect(self.width - max(1, band - inset), 0, max(1, band - inset), self.height))
                self.screen.blit(vignette_surface, (0, 0))

        if self.depth_blur_effect:
            strength = str(self.depth_blur_effect.get("strength") or "medium")
            focus = str(self.depth_blur_effect.get("focus") or "full")
            alpha = DEPTH_BLUR_ALPHA.get(strength, DEPTH_BLUR_ALPHA["medium"])
            shade = self.pygame.Surface((self.width, self.height), self.pygame.SRCALPHA)
            if focus == "left":
                shade.fill((0, 0, 0, 0))
                self.pygame.draw.rect(shade, (0, 0, 0, alpha), self.pygame.Rect(int(self.width * 0.42), 0, int(self.width * 0.58), self.height))
            elif focus == "right":
                shade.fill((0, 0, 0, 0))
                self.pygame.draw.rect(shade, (0, 0, 0, alpha), self.pygame.Rect(0, 0, int(self.width * 0.58), self.height))
            elif focus == "center":
                shade.fill((0, 0, 0, 0))
                self.pygame.draw.rect(shade, (0, 0, 0, alpha), self.pygame.Rect(0, 0, int(self.width * 0.26), self.height))
                self.pygame.draw.rect(shade, (0, 0, 0, alpha), self.pygame.Rect(int(self.width * 0.74), 0, int(self.width * 0.26), self.height))
            else:
                shade.fill((0, 0, 0, alpha))
            self.screen.blit(shade, (0, 0))

    def project_scene3d_grid_point(self, x: float, z: float, center_x: int, center_y: int, scale: float) -> tuple[int, int]:
        yaw = math.radians(float(self.scene3d_preview_yaw))
        pitch_ratio = math.sin(math.radians(float(self.scene3d_preview_pitch)))
        rotated_x = x * math.cos(yaw) - z * math.sin(yaw)
        rotated_z = x * math.sin(yaw) + z * math.cos(yaw)
        screen_x = center_x + rotated_x * scale
        screen_y = center_y + rotated_z * scale * (0.20 + 0.48 * pitch_ratio)
        return int(round(screen_x)), int(round(screen_y))

    def render_scene3d_background_preview(self, target, asset: dict) -> None:
        palette = self.get_active_palette()
        target.fill(mix_rgb(palette["bgTop"], (0, 0, 0), 0.16))
        glow = self.pygame.Surface((self.width, self.height), self.pygame.SRCALPHA)
        for index, radius in enumerate([520, 360, 220]):
            alpha = max(18, 58 - index * 16)
            self.pygame.draw.circle(
                glow,
                (*palette["accent"], alpha),
                (self.width // 2, int(self.height * 0.38)),
                radius,
            )
        target.blit(glow, (0, 0))

        center_x = self.width // 2
        center_y = int(self.height * 0.58)
        scale = 42 * float(self.scene3d_preview_zoom)
        grid_range = range(-9, 10)
        line_color = with_alpha(palette["accent"], 34)
        axis_color = with_alpha(palette["accentAlt"], 70)
        for value in grid_range:
            start = self.project_scene3d_grid_point(value, -9, center_x, center_y, scale)
            end = self.project_scene3d_grid_point(value, 9, center_x, center_y, scale)
            self.pygame.draw.line(target, axis_color if value == 0 else line_color, start, end, 2 if value == 0 else 1)
            start = self.project_scene3d_grid_point(-9, value, center_x, center_y, scale)
            end = self.project_scene3d_grid_point(9, value, center_x, center_y, scale)
            self.pygame.draw.line(target, axis_color if value == 0 else line_color, start, end, 2 if value == 0 else 1)

        report = self.get_scene3d_preview_report(str(asset.get("id") or ""))
        panel_rect = self.pygame.Rect(0, 0, min(520, self.width - 96), 178)
        panel_rect.center = (self.width // 2, int(self.height * 0.28))
        self.pygame.draw.rect(target, (*palette["panel"], 224), panel_rect, border_radius=24)
        self.pygame.draw.rect(target, with_alpha(palette["accent"], 62), panel_rect, 2, border_radius=24)
        target.blit(self.font_title.render("3D 场景交互预览桥", True, palette["text"]), (panel_rect.left + 24, panel_rect.top + 18))
        status_surface = self.font_ui.render(str(report.get("statusLabel") or "待检查"), True, palette["accent"] if report.get("status") == "ready" else palette["warning"])
        target.blit(status_surface, (panel_rect.right - status_surface.get_width() - 24, panel_rect.top + 26))
        y = panel_rect.top + 66
        for line in self.get_scene3d_preview_lines(str(asset.get("id") or ""))[1:]:
            clipped = ellipsize_text(self.font_ui, line, panel_rect.width - 48)
            target.blit(self.font_ui.render(clipped, True, palette["muted"]), (panel_rect.left + 24, y))
            y += 24

    def render_screen_effect_overlays(self) -> None:
        if self.screen_fade_effect:
            color = FADE_COLORS.get(str(self.screen_fade_effect.get("color") or "black"), FADE_COLORS["black"])
            fade_surface = self.pygame.Surface((self.width, self.height), self.pygame.SRCALPHA)
            fade_surface.fill((*color, 220))
            self.screen.blit(fade_surface, (0, 0))

        if self.screen_flash_effect:
            color = FLASH_COLORS.get(str(self.screen_flash_effect.get("color") or "white"), FLASH_COLORS["white"])
            intensity = str(self.screen_flash_effect.get("intensity") or "medium")
            remaining = float(self.screen_flash_effect.get("remaining") or 0.0)
            duration = max(0.001, float(self.screen_flash_effect.get("durationSeconds") or 0.72))
            alpha = int(FLASH_ALPHA.get(intensity, FLASH_ALPHA["medium"]) * clamp(remaining / duration, 0.0, 1.0))
            flash_surface = self.pygame.Surface((self.width, self.height), self.pygame.SRCALPHA)
            flash_surface.fill((*color, max(0, min(255, alpha))))
            self.screen.blit(flash_surface, (0, 0))

    def render(self) -> None:
        pygame = self.pygame
        self.screen.fill(self.get_active_palette()["bgBottom"])
        stage_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.render_background(stage_surface)
        self.render_characters(stage_surface)
        self.render_particle_effect(stage_surface)
        self.render_stage_surface(stage_surface)
        self.render_stage_effect_overlays()
        if not self.ui_hidden or self.overlay_mode:
            self.render_status_bar()
        if not self.ui_hidden:
            if self.current_choices:
                self.render_choices()
            elif self.current_line and self.current_line.get("type") == "video_play":
                self.render_video_card()
            elif self.current_line:
                self.render_dialogue()
            elif self.finished:
                self.render_finished()
        self.render_screen_effect_overlays()
        self.render_overlay()
        pygame.display.flip()

    def render_background_asset(self, target, asset_id: str | None, alpha: int = 255) -> None:
        target = target or self.screen
        palette = self.get_active_palette()
        safe_asset_id = str(asset_id or "").strip()
        safe_alpha = clamp_int(alpha, 0, 255, 255)
        render_target = target
        if safe_alpha < 255:
            render_target = self.pygame.Surface((self.width, self.height), self.pygame.SRCALPHA)

        background_asset = self.assets_by_id.get(safe_asset_id) or {}
        if background_asset.get("type") == "scene3d":
            self.render_scene3d_background_preview(render_target, background_asset)
            if safe_alpha < 255:
                render_target.set_alpha(safe_alpha)
                target.blit(render_target, (0, 0))
            return
        background = self._load_image(safe_asset_id)
        if background:
            bg_width, bg_height = background.get_size()
            scale = max(self.width / bg_width, self.height / bg_height)
            scaled = self.pygame.transform.smoothscale(
                background,
                (max(1, int(bg_width * scale)), max(1, int(bg_height * scale))),
            )
            rect = scaled.get_rect(center=(self.width // 2, self.height // 2))
            render_target.blit(scaled, rect)
        else:
            top = self.pygame.Surface((self.width, self.height // 2))
            bottom = self.pygame.Surface((self.width, self.height - self.height // 2))
            top.fill(palette["bgTop"])
            bottom.fill(palette["bgBottom"])
            render_target.blit(top, (0, 0))
            render_target.blit(bottom, (0, self.height // 2))
            label = "背景未加载" if safe_asset_id else "当前场景没有背景"
            self.blit_text_center(self.font_title, label, self.width // 2, self.height // 2 - 20, palette["muted"], target=render_target)

        if safe_alpha < 255 and background_asset.get("type") != "scene3d":
            render_target.set_alpha(safe_alpha)
            target.blit(render_target, (0, 0))

    def render_background(self, target=None) -> None:
        target = target or self.screen
        self.render_background_asset(target, self.stage_background_asset_id)
        transition = self.background_transition
        if not transition:
            return
        now_ms = self.get_runtime_ticks_ms()
        progress = get_native_transition_progress(transition, now_ms)
        if progress >= 1.0:
            self.background_transition = None
            return
        previous_alpha = int(round(255 * (1.0 - ease_out_cubic(progress))))
        if previous_alpha > 0:
            self.render_background_asset(target, transition.get("previousAssetId"), previous_alpha)

    def render_character_model_preview_card(self, target, anchor_rect, character: dict, expression_id: str | None) -> None:
        report = self.get_character_model_preview_report(character, expression_id)
        if not report.get("isAdvanced"):
            return

        palette = self.get_active_palette()
        status = str(report.get("status") or "")
        accent = palette["accent"] if status == "ready" else palette["warning"]
        if status in {"missing_asset", "missing_file", "invalid", "unbound"}:
            accent = mix_rgb(palette["warning"], (255, 64, 64), 0.34)

        card_width = min(300, max(238, int(self.width * 0.22)))
        card_height = 128
        card_x = int(anchor_rect.centerx - card_width / 2)
        card_x = max(18, min(self.width - card_width - 18, card_x))
        if anchor_rect.top > 156:
            card_y = anchor_rect.top - card_height - 14
        else:
            card_y = anchor_rect.bottom - card_height - 18
        card_y = max(92, min(self.height - card_height - 150, card_y))
        card_rect = self.pygame.Rect(card_x, card_y, card_width, card_height)

        self.pygame.draw.rect(target, (*palette["panel"], 226), card_rect, border_radius=18)
        self.pygame.draw.rect(target, with_alpha(accent, 68), card_rect, 2, border_radius=18)
        self.pygame.draw.line(
            target,
            (*accent, 190),
            (card_rect.left + 18, card_rect.top + 34),
            (card_rect.right - 18, card_rect.top + 34),
            2,
        )

        title = f"{report['modeLabel']} 预览桥"
        status_label = str(report.get("statusLabel") or "待检查")
        target.blit(self.font_ui.render(title, True, palette["text"]), (card_rect.left + 16, card_rect.top + 10))
        status_surface = self.font_ui.render(status_label, True, accent)
        target.blit(status_surface, (card_rect.right - status_surface.get_width() - 16, card_rect.top + 10))

        lines = self.get_character_model_preview_lines(character, expression_id)[1:5]
        y = card_rect.top + 44
        for line in lines:
            clipped = ellipsize_text(self.font_ui, line, card_rect.width - 30)
            target.blit(self.font_ui.render(clipped, True, palette["muted"]), (card_rect.left + 16, y))
            y += 20

    def get_character_render_transition_adjustment(
        self,
        state: dict,
        width: int,
        height: int,
        is_leaving: bool,
    ) -> dict:
        transition = state.get("transition") if isinstance(state, dict) else None
        if not transition:
            return {"opacityMultiplier": 1.0, "offsetX": 0, "offsetY": 0, "scaleMultiplier": 1.0}

        progress = get_native_transition_progress(transition, self.get_runtime_ticks_ms())
        eased = ease_out_cubic(progress)
        transition_name = get_safe_character_transition(transition.get("transition"))
        visible_ratio = 1.0 - eased if is_leaving else eased
        offset_ratio = eased if is_leaving else (1.0 - eased)
        offset_x = 0
        offset_y = 0
        scale_multiplier = 1.0

        if transition_name == "slide_left":
            offset_x = -int(width * 0.18 * offset_ratio)
        elif transition_name == "slide_right":
            offset_x = int(width * 0.18 * offset_ratio)
        elif transition_name == "rise":
            offset_y = int(height * 0.10 * offset_ratio)
        elif transition_name == "pop":
            scale_multiplier = (1.0 - 0.06 * eased) if is_leaving else (0.92 + 0.08 * eased)

        return {
            "opacityMultiplier": clamp(visible_ratio, 0.0, 1.0),
            "offsetX": offset_x,
            "offsetY": offset_y,
            "scaleMultiplier": clamp(scale_multiplier, 0.25, 2.0),
        }

    def get_renderable_character_items(self) -> list[tuple[str, dict]]:
        items: list[tuple[str, dict]] = []
        for character_id, state in self.visible_characters.items():
            items.append((character_id, dict(state or {})))
        for character_id, state in self.leaving_characters.items():
            leaving_state = dict(state or {})
            leaving_state["__leaving"] = True
            items.append((character_id, leaving_state))
        return items

    def render_characters(self, target=None) -> None:
        target = target or self.screen
        palette = self.get_active_palette()
        position_x = {
            "left": int(self.width * 0.24),
            "center": int(self.width * 0.50),
            "right": int(self.width * 0.76),
        }
        def character_sort_key(item):
            character_state = item[1] if isinstance(item[1], dict) else {}
            stage = get_safe_character_stage(character_state.get("stage"))
            return (
                stage["layer"],
                position_x.get(character_state.get("position") or "center", 0),
            )

        for character_id, state in sorted(self.get_renderable_character_items(), key=character_sort_key):
            stage = get_safe_character_stage(state.get("stage"))
            sprite_asset_id = self.get_character_sprite_asset_id(character_id, state.get("expressionId"))
            sprite = self._load_image(sprite_asset_id)
            x = position_x.get(state.get("position") or "center", self.width // 2) + int(self.width * stage["offsetX"] / 100)
            bottom_y = int(self.height * 0.88) + int(self.height * stage["offsetY"] / 100)
            is_leaving = bool(state.get("__leaving"))
            if sprite:
                sprite_width, sprite_height = sprite.get_size()
                max_height = int(self.height * 0.74)
                scale = min(max_height / max(sprite_height, 1), 1.6) * (stage["scale"] / 100)
                transition_adjustment = self.get_character_render_transition_adjustment(
                    state,
                    max(1, int(sprite_width * scale)),
                    max(1, int(sprite_height * scale)),
                    is_leaving,
                )
                scale *= transition_adjustment["scaleMultiplier"]
                scaled = self.pygame.transform.smoothscale(
                    sprite,
                    (max(1, int(sprite_width * scale)), max(1, int(sprite_height * scale))),
                )
                if stage["flipX"]:
                    scaled = self.pygame.transform.flip(scaled, True, False)
                effective_opacity = clamp(stage["opacity"] * transition_adjustment["opacityMultiplier"], 0, 100)
                if effective_opacity < 100:
                    scaled = scaled.copy()
                    scaled.set_alpha(int(255 * effective_opacity / 100))
                rect = scaled.get_rect(
                    midbottom=(
                        x + int(transition_adjustment["offsetX"]),
                        bottom_y + int(transition_adjustment["offsetY"]),
                    )
                )
                target.blit(scaled, rect)
                character = self.characters_by_id.get(character_id) or {}
                if effective_opacity > 15 and not is_leaving:
                    self.render_character_model_preview_card(target, rect, character, state.get("expressionId"))
            else:
                transition_adjustment = self.get_character_render_transition_adjustment(state, 220, 420, is_leaving)
                placeholder_rect = self.pygame.Rect(0, 0, 220, 420)
                placeholder_scale = stage["scale"] / 100 * transition_adjustment["scaleMultiplier"]
                placeholder_rect.width = max(1, int(placeholder_rect.width * placeholder_scale))
                placeholder_rect.height = max(1, int(placeholder_rect.height * placeholder_scale))
                placeholder_rect.midbottom = (
                    x + int(transition_adjustment["offsetX"]),
                    bottom_y + int(transition_adjustment["offsetY"]),
                )
                effective_opacity = clamp(stage["opacity"] * transition_adjustment["opacityMultiplier"], 0, 100)
                placeholder_surface = self.pygame.Surface(placeholder_rect.size, self.pygame.SRCALPHA)
                self.pygame.draw.rect(
                    placeholder_surface,
                    with_alpha(palette["placeholder"], effective_opacity),
                    placeholder_surface.get_rect(),
                    border_radius=28,
                )
                self.pygame.draw.rect(
                    placeholder_surface,
                    with_alpha(palette["panelBorder"], effective_opacity),
                    placeholder_surface.get_rect(),
                    2,
                    border_radius=28,
                )
                target.blit(placeholder_surface, placeholder_rect)
                character = self.characters_by_id.get(character_id) or {}
                character_name = self.localize_value(character, "displayName", character_id)
                presentation_label = self.get_character_presentation_mode_label(character)
                model_asset_label = self.get_character_model_asset_label(character)
                binding_label = self.get_character_expression_binding_label(character, state.get("expressionId"))
                if effective_opacity > 15:
                    self.blit_text_center(
                        self.font_body,
                        character_name,
                        placeholder_rect.centerx,
                        placeholder_rect.centery - 16,
                        palette["text"],
                        target=target,
                    )
                    self.blit_text_center(
                        self.font_ui,
                        presentation_label,
                        placeholder_rect.centerx,
                        placeholder_rect.centery + 22,
                        palette["accent"],
                        target=target,
                    )
                    self.blit_text_center(
                        self.font_ui,
                        model_asset_label,
                        placeholder_rect.centerx,
                        placeholder_rect.centery + 52,
                        palette["muted"],
                        target=target,
                    )
                    self.blit_text_center(
                        self.font_ui,
                        binding_label[:32],
                        placeholder_rect.centerx,
                        placeholder_rect.centery + 80,
                        palette["muted"],
                        target=target,
                    )
                if not is_leaving:
                    self.render_character_model_preview_card(target, placeholder_rect, character, state.get("expressionId"))

    def render_status_bar(self) -> None:
        palette = self.get_active_palette()
        panel = self.pygame.Rect(20, 18, self.width - 40, 64)
        self.pygame.draw.rect(self.screen, (*palette["panel"], palette["panelAlpha"]), panel, border_radius=18)
        self.pygame.draw.rect(self.screen, palette["panelBorder"], panel, 1, border_radius=18)
        self.draw_game_ui_panel_frame(panel)
        project_title = self.project.get("title") or "Canvasia Engine"
        target_label = self.build_info.get("exportTargetLabel") or "原生 Runtime"
        status_text = f"{project_title} · {target_label}"
        self.screen.blit(self.font_ui.render(status_text, True, palette["text"]), (36, 30))
        self.screen.blit(self.font_ui.render(self.status_message, True, palette["muted"]), (36, 52))
        controls = (
            "↑↓：选择 · Enter：确认 · F11：全屏 · Esc：退出"
            if self.overlay_mode == "title"
            else "左键：推进 · 右键/F1：系统 · 中键/U：隐藏界面 · F12/P：截图"
        )
        control_surface = self.font_ui.render(controls, True, palette["muted"])
        self.screen.blit(control_surface, (self.width - control_surface.get_width() - 36, 30))
        mode_labels = []
        if self.auto_play_enabled:
            mode_labels.append("AUTO")
        if self.skip_read_enabled:
            mode_labels.append("SKIP READ")
        if mode_labels:
            mode_surface = self.font_ui.render(" · ".join(mode_labels), True, palette["accent"])
            self.screen.blit(mode_surface, (self.width - mode_surface.get_width() - 36, 52))

    def render_dialogue(self) -> None:
        line = self.current_line or {}
        layout = self.build_dialogue_layout(line)
        panel = self.get_dialog_panel_rect(layout["minHeight"])
        self.draw_dialog_panel(panel)
        padding_x = int(self.dialog_box_config.get("paddingX", 18))
        padding_y = int(self.dialog_box_config.get("paddingY", 14))
        text_left = panel.left + padding_x
        text_width = panel.width - padding_x * 2

        if text_width != layout["textWidth"]:
            layout = self.build_dialogue_layout(line, text_width)
        speaker_name = layout["speakerName"]

        current_top = panel.top + padding_y
        if speaker_name:
            self.blit_dialogue_text(
                self.font_title,
                speaker_name,
                (text_left, current_top),
                self.dialog_box_config.get("speakerColor", COLOR_TEXT),
            )
            current_top += self.font_title.get_height() + 12

        text = self.get_current_line_render_text()
        full_lines = layout["fullLines"]
        line_height = layout["lineHeight"]
        meta_text = self.build_save_summary_line()
        meta_height = self.font_ui.get_height()
        meta_top = panel.bottom - padding_y - meta_height
        max_text_height = max(36, meta_top - current_top - 10)
        max_lines = max(1, max_text_height // line_height)
        has_overflow = len(full_lines) > max_lines
        if has_overflow:
            meta_text += " · 长文本：H 查看历史"
        meta_surface = self.font_ui.render(meta_text, True, self.dialog_box_config.get("hintColor", COLOR_TEXT_MUTED))
        meta_top = panel.bottom - padding_y - meta_surface.get_height()
        max_text_height = max(36, meta_top - current_top - 10)
        max_lines = max(1, max_text_height // line_height)
        lines = wrap_text(self.font_body, text, text_width)
        visible_lines = list(lines[:max_lines])
        if has_overflow and self.is_current_line_fully_visible() and visible_lines:
            visible_lines[-1] = ellipsize_text(self.font_body, visible_lines[-1], text_width, " …")
        for index, text_line in enumerate(visible_lines):
            self.blit_dialogue_text(
                self.font_body,
                text_line,
                (text_left, current_top + index * line_height),
                self.dialog_box_config.get("textColor", COLOR_TEXT),
            )

        self.screen.blit(meta_surface, (text_left, meta_top))

    def render_video_card(self) -> None:
        line = self.current_line or {}
        palette = self.get_active_palette()
        panel = self.pygame.Rect(0, 0, min(self.width - 88, 1040), min(self.height - 118, 610))
        panel.center = (self.width // 2, self.height // 2 + 18)
        self.pygame.draw.rect(self.screen, (*palette["panel"], 244), panel, border_radius=30)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 76), panel, 2, border_radius=30)
        self.draw_game_ui_panel_frame(panel, "system")

        embedded_frame = self.get_current_embedded_video_surface()
        embedded_status = self.get_current_embedded_video_status()
        playback_mode = str(line.get("videoPlaybackMode") or "")
        if self.embedded_video_playback:
            playback_mode = str(getattr(self.embedded_video_playback, "backend_id", playback_mode) or playback_mode)
        is_sync_backend = playback_mode == NATIVE_VIDEO_SYNC_BACKEND_ID
        is_opencv_backend = playback_mode == NATIVE_VIDEO_EMBEDDED_BACKEND_ID
        backend_label = "PyAV 音画同步" if is_sync_backend else ("OpenCV 画面" if is_opencv_backend else "自动检测")
        kicker_label = "NATIVE SYNC VIDEO" if is_sync_backend else "NATIVE VIDEO CARD"
        kicker = self.font_ui.render(kicker_label, True, palette["accent"])
        self.screen.blit(kicker, (panel.left + 30, panel.top + 24))
        title = str(line.get("videoTitle") or "视频播放")
        self.screen.blit(self.font_title.render(title[:34], True, palette["text"]), (panel.left + 30, panel.top + 52))

        preview_result = self.get_video_preview_frame_result(line)
        preview_frame = preview_result.get("surface")
        preview_status = str(preview_result.get("status") or "")
        display_frame = embedded_frame or preview_frame
        status_labels = [
            (
                ("音画同步中" if is_sync_backend else "内嵌播放中")
                if embedded_status == "playing"
                else (
                    ("同步暂停" if is_sync_backend else "内嵌暂停")
                    if embedded_status == "paused"
                    else ("已播放" if line.get("videoOpened") else "等待播放")
                )
            ),
            "不可跳过" if line.get("videoSkippable") is False else "可跳过",
            backend_label if playback_mode else ("窗口内画面" if display_frame else "桥接卡预览"),
        ]
        pill_right = panel.right - 30
        for label in reversed(status_labels):
            label_surface = self.font_ui.render(label, True, palette["text"])
            pill_width = label_surface.get_width() + 22
            pill_rect = self.pygame.Rect(pill_right - pill_width, panel.top + 28, pill_width, 28)
            fill_color = palette["accent"] if label in {"音画同步中", "同步暂停", "内嵌播放中", "内嵌暂停", "已播放"} else palette["panel"]
            self.pygame.draw.rect(self.screen, with_alpha(fill_color, 62), pill_rect, border_radius=14)
            self.pygame.draw.rect(self.screen, with_alpha(palette["accentAlt"], 42), pill_rect, 1, border_radius=14)
            self.screen.blit(label_surface, (pill_rect.left + 11, pill_rect.top + 5))
            pill_right = pill_rect.left - 8

        preview_rect = self.pygame.Rect(panel.left + 30, panel.top + 96, panel.width - 60, max(170, panel.height - 274))
        self.pygame.draw.rect(self.screen, (5, 8, 16), preview_rect, border_radius=24)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 36), preview_rect, 1, border_radius=24)
        self.draw_game_ui_panel_frame(preview_rect)

        if display_frame:
            image_width, image_height = display_frame.get_size()
            image_area = preview_rect.inflate(-6, -6)
            fit_mode = str(line.get("videoFit") or "contain")
            if fit_mode == "cover":
                scale = max(image_area.width / max(1, image_width), image_area.height / max(1, image_height))
            else:
                scale = min(image_area.width / max(1, image_width), image_area.height / max(1, image_height))
            scaled = self.pygame.transform.smoothscale(
                display_frame,
                (max(1, int(image_width * scale)), max(1, int(image_height * scale))),
            )
            previous_clip = self.screen.get_clip()
            self.screen.set_clip(preview_rect)
            self.screen.blit(scaled, scaled.get_rect(center=preview_rect.center))
            self.screen.set_clip(previous_clip)
            if embedded_status not in {"playing", "paused"}:
                overlay = self.pygame.Surface((preview_rect.width, preview_rect.height), self.pygame.SRCALPHA)
                overlay.fill((5, 8, 16, 72))
                self.screen.blit(overlay, preview_rect.topleft)
        else:
            glow_surface = self.pygame.Surface((preview_rect.width, preview_rect.height), self.pygame.SRCALPHA)
            self.pygame.draw.circle(
                glow_surface,
                with_alpha(palette["accent"], 24),
                (int(preview_rect.width * 0.28), int(preview_rect.height * 0.35)),
                max(80, preview_rect.height // 2),
            )
            self.pygame.draw.circle(
                glow_surface,
                with_alpha(palette["accentAlt"], 20),
                (int(preview_rect.width * 0.78), int(preview_rect.height * 0.18)),
                max(70, preview_rect.height // 3),
            )
            self.screen.blit(glow_surface, preview_rect.topleft)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 42), preview_rect, 1, border_radius=24)
        self.draw_game_ui_panel_frame(preview_rect)

        if embedded_status != "playing":
            play_radius = max(34, min(62, preview_rect.height // 5))
            self.pygame.draw.circle(self.screen, with_alpha(palette["accent"], 58), preview_rect.center, play_radius)
            self.pygame.draw.circle(self.screen, with_alpha(palette["accentAlt"], 82), preview_rect.center, play_radius, 2)
            if embedded_status == "paused":
                bar_width = max(8, play_radius // 4)
                bar_height = int(play_radius * 0.9)
                for offset in (-bar_width, bar_width):
                    bar_rect = self.pygame.Rect(0, 0, bar_width, bar_height)
                    bar_rect.center = (preview_rect.centerx + offset, preview_rect.centery)
                    self.pygame.draw.rect(self.screen, palette["text"], bar_rect, border_radius=4)
            else:
                triangle_size = play_radius * 0.72
                triangle = [
                    (int(preview_rect.centerx - triangle_size * 0.28), int(preview_rect.centery - triangle_size * 0.48)),
                    (int(preview_rect.centerx - triangle_size * 0.28), int(preview_rect.centery + triangle_size * 0.48)),
                    (int(preview_rect.centerx + triangle_size * 0.52), preview_rect.centery),
                ]
                self.pygame.draw.polygon(self.screen, palette["text"], triangle)

        file_label = str(line.get("videoFileName") or "视频文件未找到")
        bridge_hint = "按 V 优先尝试 PyAV 音画同步；按 O 使用系统播放器兜底。"
        if embedded_status == "playing":
            if is_sync_backend:
                bridge_hint = "PyAV 音画同步播放中；按 Space / V 暂停，O 可打开系统播放器。"
            else:
                bridge_hint = "OpenCV 画面播放中（无音频）；按 Space / V 暂停，O 可打开系统播放器。"
        elif embedded_status == "paused":
            bridge_hint = "内嵌视频已暂停；按 Space / V 继续播放。"
        elif line.get("videoPlaybackFinished"):
            bridge_hint = "内嵌视频已播放结束；按 Enter 继续剧情。"
        elif preview_frame:
            bridge_hint = "已读取视频画面帧；按 V 尝试窗口内音画同步播放。"
        elif preview_status:
            bridge_hint = f"{preview_status}；按 O 唤起系统播放器。"
        if not line.get("videoAssetPath"):
            bridge_hint = "视频文件缺失。可以继续剧情，但正式发布前需要重新导出素材。"
        self.blit_text_center(self.font_body, file_label[:42], preview_rect.centerx, preview_rect.bottom - 72, palette["text"])
        self.blit_text_center(self.font_ui, bridge_hint[:58], preview_rect.centerx, preview_rect.bottom - 40, palette["muted"])

        meta_top = preview_rect.bottom + 18
        clip_label = str(line.get("videoClipLabel") or "整段播放")
        meta_rows = [
            ("剪辑范围", clip_label),
            ("画面适配", str(line.get("videoFit") or "contain")),
            ("播放后端", backend_label),
            ("音量", f"{int(line.get('videoVolume') or 100)}%"),
        ]
        meta_left = panel.left + 34
        meta_width = max(130, (panel.width - 68) // len(meta_rows))
        for index, (label, value) in enumerate(meta_rows):
            row_rect = self.pygame.Rect(meta_left + index * meta_width, meta_top, meta_width - 12, 42)
            self.pygame.draw.rect(self.screen, with_alpha(palette["panel"], 42), row_rect, border_radius=14)
            self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 20), row_rect, 1, border_radius=14)
            self.screen.blit(self.font_ui.render(label, True, palette["muted"]), (row_rect.left + 12, row_rect.top + 6))
            value_surface = self.font_ui.render(value, True, palette["text"])
            self.screen.blit(value_surface, (row_rect.right - value_surface.get_width() - 12, row_rect.top + 22))

        timeline_rect = self.pygame.Rect(panel.left + 34, meta_top + 56, panel.width - 68, 8)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 26), timeline_rect, border_radius=4)
        start_time = float(line.get("videoStartTimeSeconds") or 0)
        end_time = float(line.get("videoEndTimeSeconds") or 0)
        playback_progress = self.embedded_video_playback.get_progress_ratio() if self.embedded_video_playback else None
        if playback_progress is not None and playback_progress > 0:
            progress_rect = self.pygame.Rect(timeline_rect.left, timeline_rect.top, max(8, int(timeline_rect.width * playback_progress)), timeline_rect.height)
            self.pygame.draw.rect(self.screen, with_alpha(palette["accent"], 88), progress_rect, border_radius=4)
        elif start_time > 0 or end_time > 0:
            virtual_duration = max(end_time, start_time + 12, 30)
            start_x = timeline_rect.left + int(timeline_rect.width * min(start_time / virtual_duration, 1))
            end_ratio = min((end_time or virtual_duration) / virtual_duration, 1)
            end_x = timeline_rect.left + int(timeline_rect.width * end_ratio)
            selected_rect = self.pygame.Rect(start_x, timeline_rect.top, max(8, end_x - start_x), timeline_rect.height)
            self.pygame.draw.rect(self.screen, with_alpha(palette["accent"], 82), selected_rect, border_radius=4)
        else:
            self.pygame.draw.rect(self.screen, with_alpha(palette["accent"], 58), timeline_rect, border_radius=4)

        self.video_hotspots = []
        button_y = panel.bottom - 54
        play_label = "Space 暂停" if embedded_status == "playing" else ("Space 继续" if embedded_status == "paused" else "V 音画播放")
        continue_disabled = line.get("videoSkippable") is False and bool(line.get("videoAssetPath")) and not bool(line.get("videoOpened"))
        buttons = [
            ("play-video", play_label, panel.left + 34, 140, False),
            ("external-video", "O 系统播放器", panel.left + 186, 148, False),
            (
                "continue-video",
                "Enter 继续",
                panel.right - 154,
                120,
                continue_disabled,
            ),
        ]
        for action, label, left, width, disabled in buttons:
            button_rect = self.pygame.Rect(left, button_y, width, 36)
            active = action == "play-video" and embedded_status in {"playing", "paused"} and not disabled
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accent"] if active else palette["panel"], 72 if active else 48),
                button_rect,
                border_radius=15,
            )
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accentAlt"] if active else palette["panelBorder"], 80 if active else 32),
                button_rect,
                1,
                border_radius=15,
            )
            self.draw_game_ui_button_frame(
                button_rect,
                self.get_game_ui_button_state(button_rect, active=active, disabled=disabled),
            )
            self.blit_text_center(self.font_ui, label, button_rect.centerx, button_rect.top + 9, palette["muted"] if disabled else palette["text"])
            self.video_hotspots.append({"kind": action, "rect": button_rect, "disabled": disabled})

        if continue_disabled:
            hint = "不可跳过视频需要先播放一次，再确认继续。"
        elif embedded_status in {"playing", "paused"} and line.get("videoSkippable") is False:
            hint = "不可跳过视频需要等待内嵌播放结束。"
        else:
            hint = "Space/V 播放或暂停 · O 系统播放器 · Enter 继续。"
        self.screen.blit(self.font_ui.render(hint, True, palette["muted"]), (panel.left + 34, panel.bottom - 86))

    def render_choices(self) -> None:
        option_count = len(self.current_choices or [])
        panel = self.get_dialog_panel_rect(max(212, 86 + option_count * 54))
        self.draw_dialog_panel(panel)
        padding_x = int(self.dialog_box_config.get("paddingX", 18))
        padding_y = int(self.dialog_box_config.get("paddingY", 14))
        title = self.font_title.render("请选择下一步", True, self.dialog_box_config.get("speakerColor", COLOR_TEXT))
        self.screen.blit(title, (panel.left + padding_x, panel.top + padding_y))
        button_top = panel.top + padding_y + title.get_height() + 18
        button_left = panel.left + padding_x
        button_width = panel.width - padding_x * 2
        active_fill = with_alpha(self.dialog_box_config.get("borderColor", COLOR_ACCENT), 88)
        idle_fill = with_alpha(
            self.dialog_box_config.get("backgroundColor", COLOR_PANEL),
            max(0, self.scale_dialog_opacity(self.dialog_box_config.get("backgroundOpacity", 0))),
        )
        border_color = with_alpha(self.dialog_box_config.get("borderColor", COLOR_PANEL_BORDER), max(24, self.dialog_box_config.get("borderOpacity", 0)))

        for index, option in enumerate(self.current_choices or []):
            row_rect = self.pygame.Rect(button_left, button_top + index * 52, button_width, 40)
            is_active = index == self.current_choice_index
            fill = active_fill if is_active else idle_fill
            border = with_alpha(self.dialog_box_config.get("speakerColor", COLOR_ACCENT_ALT), 88) if is_active else border_color
            self.pygame.draw.rect(self.screen, fill, row_rect, border_radius=16)
            self.pygame.draw.rect(self.screen, border, row_rect, 2, border_radius=16)
            self.draw_game_ui_button_frame(row_rect, self.get_game_ui_button_state(row_rect, active=is_active))
            label = str(option.get("text") or f"选项 {index + 1}")
            label = self.localize_value(option, "text", label)
            self.screen.blit(
                self.font_body.render(label, True, self.dialog_box_config.get("textColor", COLOR_TEXT)),
                (row_rect.left + 18, row_rect.top + 5),
            )

    def render_finished(self) -> None:
        panel = self.get_dialog_panel_rect(220)
        panel.centery = self.height // 2
        self.draw_dialog_panel(panel)
        self.blit_text_center(self.font_title, "本条路线已经结束", panel.centerx, panel.top + 48, self.dialog_box_config.get("speakerColor", COLOR_TEXT))
        self.blit_text_center(self.font_body, self.finished_message or "剧情结束。", panel.centerx, panel.top + 104, self.dialog_box_config.get("textColor", COLOR_TEXT_MUTED))
        self.blit_text_center(self.font_ui, "按 Esc 退出原生 Runtime", panel.centerx, panel.top + 158, self.dialog_box_config.get("hintColor", COLOR_TEXT_MUTED))

    def render_overlay(self) -> None:
        if not self.overlay_mode:
            self.overlay_hotspots = []
            return
        palette = self.get_active_palette()
        backdrop = self.pygame.Surface((self.width, self.height), self.pygame.SRCALPHA)
        backdrop.fill(palette["overlay"])
        self.screen.blit(backdrop, (0, 0))
        self.overlay_hotspots = []
        if self.overlay_mode == "title":
            self.render_title_overlay()
        elif self.overlay_mode in {"save", "load"}:
            self.render_save_dialog_overlay()
        elif self.overlay_mode == "system":
            self.render_system_menu_overlay()
        elif self.overlay_mode == "help":
            self.render_help_overlay()
        elif self.overlay_mode == "history":
            self.render_text_history_overlay()
        elif self.overlay_mode == "profile":
            self.render_profile_overlay()
        elif self.overlay_mode == "auto-resume":
            self.render_auto_resume_overlay()
        elif self.overlay_mode == "settings":
            self.render_settings_overlay()
        elif self.overlay_mode == "archives":
            self.render_archive_overlay()
        elif self.overlay_mode == "archive-detail":
            self.render_archive_detail_overlay()

    def render_title_overlay(self) -> None:
        palette = self.get_active_palette()
        menu_items = self.get_title_menu_items()
        panel = self.pygame.Rect(0, 0, min(self.width - 84, 1060), min(self.height - 92, 610))
        panel.center = (self.width // 2, self.height // 2)
        self.pygame.draw.rect(self.screen, (*palette["panel"], 242), panel, border_radius=32)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 78), panel, 2, border_radius=32)
        self.draw_game_ui_panel_frame(panel, "system")

        glow = self.pygame.Surface((panel.width, panel.height), self.pygame.SRCALPHA)
        self.pygame.draw.circle(glow, with_alpha(palette["accent"], 34), (int(panel.width * 0.28), int(panel.height * 0.24)), 190)
        self.pygame.draw.circle(glow, with_alpha(palette["accentAlt"], 30), (int(panel.width * 0.88), int(panel.height * 0.14)), 170)
        self.screen.blit(glow, panel.topleft)

        logo_rect = self.pygame.Rect(panel.left + 46, panel.top + 70, 300, 250)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panel"], 68), logo_rect, border_radius=28)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 36), logo_rect, 1, border_radius=28)
        self.draw_game_ui_panel_frame(logo_rect)
        logo = self.get_title_logo_image()
        if logo:
            logo_width, logo_height = logo.get_size()
            scale = min(logo_rect.width * 0.86 / max(1, logo_width), logo_rect.height * 0.86 / max(1, logo_height))
            scaled = self.pygame.transform.smoothscale(
                logo,
                (max(1, int(logo_width * scale)), max(1, int(logo_height * scale))),
            )
            self.screen.blit(scaled, scaled.get_rect(center=logo_rect.center))
        else:
            self.blit_text_center(self.font_title, "CE", logo_rect.centerx, logo_rect.centery - 18, palette["text"])
            self.blit_text_center(self.font_ui, "Canvasia Engine", logo_rect.centerx, logo_rect.centery + 26, palette["muted"])

        title_left = logo_rect.right + 42
        title_top = panel.top + 78
        project_title = str(self.project.get("title") or self.project.get("name") or "Canvasia Engine")
        self.screen.blit(self.font_ui.render("NATIVE RUNTIME PREVIEW", True, palette["accent"]), (title_left, title_top))
        self.screen.blit(self.font_title.render(project_title[:28], True, palette["text"]), (title_left, title_top + 34))
        summary = f"{len(self.chapters)} 章 · {len(self.scenes_by_id)} 场景 · 正式存档 {self.formal_save_slot_count} 格"
        self.screen.blit(self.font_ui.render(summary, True, palette["muted"]), (title_left, title_top + 82))
        self.screen.blit(
            self.font_ui.render("标题页支持续玩、读档、设置和资料馆，适合作为独立 App 的第一屏。", True, palette["muted"]),
            (title_left, title_top + 112),
        )

        menu_left = title_left
        menu_top = title_top + 160
        menu_width = panel.right - menu_left - 46
        row_height = 56
        for index, item in enumerate(menu_items):
            row_rect = self.pygame.Rect(menu_left, menu_top + index * row_height, menu_width, 46)
            is_active = index == self.title_menu_index
            enabled = bool(item.get("enabled", True))
            fill_color = palette["accent"] if is_active else palette["panel"]
            fill_alpha = 78 if is_active else 36
            border_color = palette["accentAlt"] if is_active else palette["panelBorder"]
            self.pygame.draw.rect(self.screen, with_alpha(fill_color, fill_alpha if enabled else 20), row_rect, border_radius=18)
            self.pygame.draw.rect(self.screen, with_alpha(border_color, 86 if is_active else 24), row_rect, 1, border_radius=18)
            self.draw_game_ui_button_frame(
                row_rect,
                self.get_game_ui_button_state(row_rect, active=is_active, disabled=not enabled),
            )
            label_color = palette["text"] if enabled else palette["muted"]
            self.screen.blit(self.font_body.render(str(item["label"]), True, label_color), (row_rect.left + 18, row_rect.top + 6))
            subtitle = str(item.get("subtitle") or "")
            subtitle_surface = self.font_ui.render(subtitle[:46], True, palette["muted"])
            self.screen.blit(subtitle_surface, (row_rect.right - subtitle_surface.get_width() - 18, row_rect.top + 15))
            self.overlay_hotspots.append({"kind": "title-item", "value": item["key"], "rect": row_rect})

        footer = "↑↓ 选择 · Enter 确认 · F11 全屏 · Esc 退出"
        self.screen.blit(self.font_ui.render(footer, True, palette["muted"]), (panel.left + 46, panel.bottom - 48))

    def render_save_dialog_overlay(self) -> None:
        dialog_data = self.get_save_dialog_data()
        panel = self.pygame.Rect(0, 0, min(self.width - 88, 1040), min(self.height - 112, 620))
        panel.center = (self.width // 2, self.height // 2)
        self.pygame.draw.rect(self.screen, with_alpha(self.dialog_box_config.get("backgroundColor", COLOR_PANEL), 96), panel, border_radius=28)
        self.pygame.draw.rect(
            self.screen,
            with_alpha(self.dialog_box_config.get("borderColor", COLOR_PANEL_BORDER), 72),
            panel,
            2,
            border_radius=28,
        )
        self.draw_game_ui_panel_frame(panel, "system")

        title = "正式存档" if self.overlay_mode == "save" else "读取存档"
        title_surface = self.font_title.render(title, True, self.dialog_box_config.get("speakerColor", COLOR_TEXT))
        subtitle = f"第 {dialog_data['page'] + 1} / {dialog_data['pageCount']} 页 · 共 {dialog_data['slotCount']} 格"
        subtitle_surface = self.font_ui.render(subtitle, True, self.dialog_box_config.get("hintColor", COLOR_TEXT_MUTED))
        self.screen.blit(title_surface, (panel.left + 28, panel.top + 24))
        self.screen.blit(subtitle_surface, (panel.left + 28, panel.top + 58))

        quick_save = dialog_data.get("quickSave") or {}
        quick_rect = self.pygame.Rect(panel.left + 28, panel.top + 92, panel.width - 56, 72)
        self.pygame.draw.rect(self.screen, with_alpha(self.dialog_box_config.get("backgroundColor", COLOR_PANEL), 42), quick_rect, border_radius=18)
        self.pygame.draw.rect(
            self.screen,
            with_alpha(self.dialog_box_config.get("borderColor", COLOR_PANEL_BORDER), 26),
            quick_rect,
            1,
            border_radius=18,
        )
        self.draw_game_ui_panel_frame(quick_rect, "save")
        quick_title = "快速存档" if not quick_save.get("isEmpty") else "快速存档（空）"
        self.screen.blit(
            self.font_ui.render(quick_title, True, self.dialog_box_config.get("speakerColor", COLOR_TEXT)),
            (quick_rect.left + 16, quick_rect.top + 10),
        )
        quick_variable_summary = str(quick_save.get("variableSummaryText") or "")
        quick_meta = f"{quick_save.get('savedAt')} · {quick_save.get('sceneName') or '尚未创建'}"
        if quick_variable_summary:
            quick_meta = f"{quick_meta} · {quick_variable_summary}"
        self.screen.blit(
            self.font_ui.render(quick_meta[:92], True, self.dialog_box_config.get("hintColor", COLOR_TEXT_MUTED)),
            (quick_rect.left + 16, quick_rect.top + 34),
        )
        quick_summary = str(quick_save.get("summaryText") or "空")
        self.screen.blit(
            self.font_ui.render(quick_summary[:78], True, self.dialog_box_config.get("textColor", COLOR_TEXT)),
            (quick_rect.left + 16, quick_rect.top + 52),
        )

        slots = dialog_data.get("visibleSlots") or []
        card_gap = 16
        card_width = (panel.width - 56 - card_gap) // 2
        card_height = 116
        cards_top = quick_rect.bottom + 22
        for visible_index, slot in enumerate(slots):
            row = visible_index // 2
            column = visible_index % 2
            card_rect = self.pygame.Rect(
                panel.left + 28 + column * (card_width + card_gap),
                cards_top + row * (card_height + 14),
                card_width,
                card_height,
            )
            is_active = visible_index == self.overlay_focus_index
            fill_opacity = 78 if is_active else 34
            border_opacity = 92 if is_active else 24
            self.pygame.draw.rect(
                self.screen,
                with_alpha(
                    self.dialog_box_config.get("borderColor", COLOR_ACCENT) if is_active else self.dialog_box_config.get("backgroundColor", COLOR_PANEL),
                    fill_opacity,
                ),
                card_rect,
                border_radius=22,
            )
            self.pygame.draw.rect(
                self.screen,
                with_alpha(
                    self.dialog_box_config.get("speakerColor", COLOR_ACCENT_ALT) if is_active else self.dialog_box_config.get("borderColor", COLOR_PANEL_BORDER),
                    border_opacity,
                ),
                card_rect,
                2,
                border_radius=22,
            )
            self.draw_game_ui_panel_frame(card_rect, "save")
            label = str(slot.get("label") or "")
            scene_name = str(slot.get("sceneName") or ("空位" if slot.get("isEmpty") else "未命名场景"))
            summary_text = str(slot.get("summaryText") or "")
            if slot.get("finished"):
                summary_text = "路线结束 · " + summary_text
            saved_at = str(slot.get("savedAt") or "尚未保存")
            variable_summary = str(slot.get("variableSummaryText") or "")
            meta_text = f"{saved_at} · {variable_summary}" if variable_summary else saved_at
            self.screen.blit(
                self.font_ui.render(label, True, self.dialog_box_config.get("speakerColor", COLOR_TEXT)),
                (card_rect.left + 16, card_rect.top + 12),
            )
            self.screen.blit(
                self.font_body.render(scene_name[:22], True, self.dialog_box_config.get("textColor", COLOR_TEXT)),
                (card_rect.left + 16, card_rect.top + 34),
            )
            self.screen.blit(
                self.font_ui.render(meta_text[:42], True, self.dialog_box_config.get("hintColor", COLOR_TEXT_MUTED)),
                (card_rect.left + 16, card_rect.top + 72),
            )
            self.screen.blit(
                self.font_ui.render(summary_text[:40], True, self.dialog_box_config.get("textColor", COLOR_TEXT)),
                (card_rect.left + 16, card_rect.top + 92),
            )
            self.overlay_hotspots.append({"kind": "slot", "value": visible_index, "rect": card_rect})

        button_y = panel.bottom - 58
        controls = [
            ("prev", "上一页", panel.left + 28),
            ("next", "下一页", panel.left + 168),
            ("switch", "切换存/读", panel.left + 308),
            ("close", "关闭", panel.right - 124),
        ]
        for action, label, left in controls:
            button_rect = self.pygame.Rect(left, button_y, 108 if action != "switch" else 132, 34)
            self.pygame.draw.rect(self.screen, with_alpha(self.dialog_box_config.get("backgroundColor", COLOR_PANEL), 58), button_rect, border_radius=14)
            self.pygame.draw.rect(
                self.screen,
                with_alpha(self.dialog_box_config.get("borderColor", COLOR_PANEL_BORDER), 42),
                button_rect,
                1,
                border_radius=14,
            )
            self.draw_game_ui_button_frame(button_rect, self.get_game_ui_button_state(button_rect))
            self.blit_text_center(
                self.font_ui,
                label,
                button_rect.centerx,
                button_rect.top + 8,
                self.dialog_box_config.get("textColor", COLOR_TEXT),
            )
            self.overlay_hotspots.append({"kind": action, "rect": button_rect})

        hint = "数字键 1-6 选槽位 · ←→ 切页 · Enter 执行 · Esc 关闭"
        self.screen.blit(
            self.font_ui.render(hint, True, self.dialog_box_config.get("hintColor", COLOR_TEXT_MUTED)),
            (panel.left + 28, panel.bottom - 88),
        )

    def get_profile_total_play_ms(self) -> int:
        profile = sanitize_player_profile(self.player_profile)
        total_ms = int(profile.get("totalPlayMs") or 0)
        if self.profile_session_started_at_ms:
            total_ms += max(0, self.pygame.time.get_ticks() - self.profile_session_started_at_ms)
        return total_ms

    def render_profile_overlay(self) -> None:
        palette = self.get_active_palette()
        profile = sanitize_player_profile(self.player_profile)
        panel = self.pygame.Rect(0, 0, min(self.width - 96, 700), min(self.height - 112, 500))
        panel.center = (self.width // 2, self.height // 2)
        self.pygame.draw.rect(self.screen, (*palette["panel"], 246), panel, border_radius=28)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 72), panel, 2, border_radius=28)
        self.draw_game_ui_panel_frame(panel, "system")
        self.screen.blit(self.font_title.render("玩家档案", True, palette["text"]), (panel.left + 30, panel.top + 26))
        self.screen.blit(
            self.font_ui.render("本地记录，不会上传；用于统计游玩和续玩入口。", True, palette["muted"]),
            (panel.left + 30, panel.top + 62),
        )

        rows = [
            ("累计游玩", format_play_duration(self.get_profile_total_play_ms())),
            ("启动次数", f"{int(profile.get('sessionCount') or 0)} 次"),
            ("续玩次数", f"{int(profile.get('resumedCount') or 0)} 次"),
            ("回到开头", f"{int(profile.get('returnToTitleCount') or 0)} 次"),
            ("首次游玩", format_snapshot_saved_at(profile.get("firstPlayedAt"))),
            ("最近启动", format_snapshot_saved_at(profile.get("lastPlayedAt"))),
            ("最近退出", format_snapshot_saved_at(profile.get("lastEndedAt"))),
        ]
        auto_resume_label = "无"
        if self.auto_resume_snapshot:
            auto_resume_label = f"{self.auto_resume_snapshot.get('sceneName') or '未命名场景'} · {format_snapshot_saved_at(self.auto_resume_snapshot.get('savedAt'))}"
        rows.append(("续玩记录", auto_resume_label))

        row_top = panel.top + 108
        for index, (label, value) in enumerate(rows):
            row_rect = self.pygame.Rect(panel.left + 30, row_top + index * 38, panel.width - 60, 30)
            if index % 2 == 0:
                self.pygame.draw.rect(self.screen, with_alpha(palette["accent"], 18), row_rect, border_radius=12)
            self.screen.blit(self.font_ui.render(label, True, palette["muted"]), (row_rect.left + 12, row_rect.top + 6))
            value_surface = self.font_ui.render(value, True, palette["text"])
            self.screen.blit(value_surface, (row_rect.right - value_surface.get_width() - 12, row_rect.top + 6))

        close_rect = self.pygame.Rect(panel.right - 138, panel.bottom - 58, 108, 34)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panel"], 58), close_rect, border_radius=14)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 42), close_rect, 1, border_radius=14)
        self.draw_game_ui_button_frame(close_rect, self.get_game_ui_button_state(close_rect))
        self.blit_text_center(self.font_ui, "关闭", close_rect.centerx, close_rect.top + 8, palette["text"])
        self.overlay_hotspots.append({"kind": "close", "rect": close_rect})
        self.screen.blit(self.font_ui.render("Enter / Esc 关闭", True, palette["muted"]), (panel.left + 30, panel.bottom - 48))

    def render_auto_resume_overlay(self) -> None:
        palette = self.get_active_palette()
        snapshot = self.auto_resume_snapshot or load_project_auto_resume(self.project_id)
        panel = self.pygame.Rect(0, 0, min(self.width - 96, 720), min(self.height - 112, 420))
        panel.center = (self.width // 2, self.height // 2)
        self.pygame.draw.rect(self.screen, (*palette["panel"], 246), panel, border_radius=28)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 72), panel, 2, border_radius=28)
        self.draw_game_ui_panel_frame(panel, "system")
        self.screen.blit(self.font_title.render("续玩记录", True, palette["text"]), (panel.left + 30, panel.top + 26))
        self.screen.blit(
            self.font_ui.render("每次停在台词、选项或结束页时，原生 Runtime 会自动更新这里。", True, palette["muted"]),
            (panel.left + 30, panel.top + 62),
        )

        card_rect = self.pygame.Rect(panel.left + 30, panel.top + 108, panel.width - 60, 150)
        self.pygame.draw.rect(self.screen, with_alpha(palette["accent"], 26), card_rect, border_radius=20)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 36), card_rect, 1, border_radius=20)
        self.draw_game_ui_panel_frame(card_rect, "save")
        if snapshot:
            scene_name = str(snapshot.get("sceneName") or snapshot.get("sceneId") or "未命名场景")
            summary = str(snapshot.get("summaryText") or snapshot.get("finishedMessage") or "当前没有摘要。")
            variable_summary = str(snapshot.get("variableSummaryText") or "").strip()
            if not variable_summary:
                variable_summary = build_variable_summary_text(self.variables, snapshot.get("variableState"))
            meta = f"{format_snapshot_saved_at(snapshot.get('savedAt'))} · 第 {int(snapshot.get('blockIndex') or 0) + 1} 张卡"
            if snapshot.get("finished"):
                meta += " · 已结束"
            self.screen.blit(self.font_body.render(scene_name[:28], True, palette["text"]), (card_rect.left + 18, card_rect.top + 20))
            self.screen.blit(self.font_ui.render(meta, True, palette["muted"]), (card_rect.left + 18, card_rect.top + 58))
            if variable_summary:
                self.screen.blit(self.font_ui.render(variable_summary[:74], True, palette["accent"]), (card_rect.left + 18, card_rect.top + 82))
            self.screen.blit(self.font_ui.render(summary[:72], True, palette["text"]), (card_rect.left + 18, card_rect.top + 110))
        else:
            self.blit_text_center(self.font_body, "当前没有续玩记录", card_rect.centerx, card_rect.top + 42, palette["muted"])
            self.blit_text_center(self.font_ui, "推进一次剧情或读入存档后会自动生成。", card_rect.centerx, card_rect.top + 88, palette["muted"])

        controls = []
        if snapshot:
            controls.extend([("auto-resume-load", "读取续玩"), ("auto-resume-clear", "清除记录")])
        controls.append(("close", "关闭"))
        button_width = 118
        gap = 14
        start_left = panel.right - 30 - len(controls) * button_width - (len(controls) - 1) * gap
        button_y = panel.bottom - 62
        for index, (kind, label) in enumerate(controls):
            button_rect = self.pygame.Rect(start_left + index * (button_width + gap), button_y, button_width, 36)
            is_primary = kind == "auto-resume-load"
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accent"] if is_primary else palette["panel"], 72 if is_primary else 58),
                button_rect,
                border_radius=14,
            )
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accentAlt"] if is_primary else palette["panelBorder"], 84 if is_primary else 42),
                button_rect,
                1,
                border_radius=14,
            )
            self.draw_game_ui_button_frame(button_rect, self.get_game_ui_button_state(button_rect, active=is_primary))
            self.blit_text_center(self.font_ui, label, button_rect.centerx, button_rect.top + 9, palette["text"])
            self.overlay_hotspots.append({"kind": kind, "rect": button_rect})

        hint = "Enter 读取续玩 · C 清除记录 · Esc 关闭" if snapshot else "Esc 关闭"
        self.screen.blit(self.font_ui.render(hint, True, palette["muted"]), (panel.left + 30, panel.bottom - 50))

    def get_system_menu_item_description(self, item_key: str) -> str:
        if item_key == "continue":
            return "关闭菜单，返回当前剧情画面。"
        if item_key == "help":
            return "打开原生操作中心，查看当前状态、快捷键和常用入口。"
        if item_key == "history":
            return f"查看最近文本和语音回听；当前记录 {len(self.text_history)} 条。"
        if item_key == "archives":
            return "进入章节、CG、音乐、角色、结局和成就等资料馆。"
        if item_key == "profile":
            return "查看本地玩家档案、游玩时长和续玩统计。"
        if item_key == "auto-resume":
            state = "已有续玩记录" if self.auto_resume_snapshot else "暂无续玩记录"
            return f"管理自动续玩快照；当前：{state}。"
        if item_key == "save":
            return f"打开正式存档面板；{self.build_save_summary_line()}。"
        if item_key == "load":
            return f"读取正式存档槽位；{self.build_save_summary_line()}。"
        if item_key == "settings":
            return "调整主题、全屏、语言、文字速度、文本框透明度和各类音量。"
        if item_key == "quick-save":
            return "立即覆盖快速存档，适合临时保留当前进度。"
        if item_key == "quick-load":
            return "立即读入快速存档；若没有快存会给出提示。"
        if item_key == "restart":
            return "回到入口场景重新开始，并记录一次返回开头。"
        if item_key == "exit":
            return "关闭原生 Runtime 预览窗口。"
        return "执行当前系统操作。"

    def render_system_menu_overlay(self) -> None:
        palette = self.get_active_palette()
        panel_height = min(self.height - 72, max(548, 150 + len(SYSTEM_MENU_ITEMS) * 38))
        panel = self.pygame.Rect(0, 0, min(self.width - 96, 760), panel_height)
        panel.center = (self.width // 2, self.height // 2)
        self.pygame.draw.rect(self.screen, (*palette["panel"], 244), panel, border_radius=28)
        self.pygame.draw.rect(
            self.screen,
            with_alpha(palette["panelBorder"], 72),
            panel,
            2,
            border_radius=28,
        )
        self.draw_game_ui_panel_frame(panel, "system")
        title_surface = self.font_title.render("系统菜单", True, palette["text"])
        self.screen.blit(title_surface, (panel.left + 26, panel.top + 24))
        self.screen.blit(
            self.font_ui.render("原生 Runtime 控制台", True, palette["muted"]),
            (panel.left + 26, panel.top + 58),
        )

        button_top = panel.top + 96
        list_width = min(310, max(260, panel.width // 2 - 52))
        for index, (item_key, item_label) in enumerate(SYSTEM_MENU_ITEMS):
            row_rect = self.pygame.Rect(panel.left + 26, button_top + index * 38, list_width, 32)
            is_active = index == self.system_menu_index
            self.pygame.draw.rect(
                self.screen,
                with_alpha(
                    palette["accent"] if is_active else palette["panel"],
                    72 if is_active else 36,
                ),
                row_rect,
                border_radius=16,
            )
            self.pygame.draw.rect(
                self.screen,
                with_alpha(
                    palette["accentAlt"] if is_active else palette["panelBorder"],
                    84 if is_active else 22,
                ),
                row_rect,
                1,
                border_radius=16,
            )
            self.draw_game_ui_button_frame(row_rect, self.get_game_ui_button_state(row_rect, active=is_active))
            self.screen.blit(
                self.font_ui.render(item_label, True, palette["text"]),
                (row_rect.left + 14, row_rect.top + 6),
            )
            self.overlay_hotspots.append({"kind": "system-item", "value": item_key, "rect": row_rect})

        selected_key, selected_label = SYSTEM_MENU_ITEMS[self.system_menu_index]
        detail_rect = self.pygame.Rect(
            panel.left + 26 + list_width + 18,
            button_top,
            panel.right - (panel.left + 26 + list_width + 18) - 26,
            panel.bottom - button_top - 78,
        )
        self.pygame.draw.rect(self.screen, with_alpha(palette["accent"], 16), detail_rect, border_radius=22)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 32), detail_rect, 1, border_radius=22)
        self.screen.blit(self.font_body.render(selected_label, True, palette["accent"]), (detail_rect.left + 18, detail_rect.top + 18))
        description_rect = self.pygame.Rect(detail_rect.left + 18, detail_rect.top + 62, detail_rect.width - 36, 96)
        self.blit_wrapped_text(
            self.font_ui,
            self.get_system_menu_item_description(selected_key),
            description_rect,
            palette["text"],
            line_gap=6,
            max_lines=4,
        )
        status_lines = [
            f"主题：{self.get_setting_value_label('themeMode')}",
            f"显示：{self.get_setting_value_label('displayMode')}",
            f"语言：{self.get_setting_value_label('language')}",
            f"文本：{self.get_setting_value_label('textSpeed')} / {self.get_setting_value_label('textScalePercent')}",
        ]
        status_top = detail_rect.bottom - 94
        for offset, line in enumerate(status_lines):
            self.screen.blit(
                self.font_ui.render(line, True, palette["muted"]),
                (detail_rect.left + 18, status_top + offset * (self.font_ui.get_height() + 6)),
            )

        hint = "↑↓ 切换 · Enter 执行 · Esc 关闭"
        self.screen.blit(
            self.font_ui.render(hint, True, palette["muted"]),
            (panel.left + 26, panel.bottom - 44),
        )

    def get_help_overlay_sections(self) -> list[dict]:
        scene = self.scenes_by_id.get(str(self.current_scene_id or "")) or {}
        scene_label = "标题页" if self.title_screen_active else self.localize_value(scene, "name", self.current_scene_id or "未命名场景")
        if self.current_choices:
            reading_state = f"选项中：{self.current_choice_index + 1}/{len(self.current_choices)}"
        elif self.current_line:
            line_type = str(self.current_line.get("type") or "dialogue")
            reading_state = {
                "dialogue": "台词播放",
                "narration": "旁白播放",
                "video_play": "视频段落",
            }.get(line_type, line_type)
        elif self.finished:
            reading_state = "路线结束"
        else:
            reading_state = "待推进"

        flow_labels = [
            f"自动播放：{'开' if self.auto_play_enabled else '关'}",
            f"已读快进：{'开' if self.skip_read_enabled else '关'}",
            f"UI：{'隐藏' if self.ui_hidden else '显示'}",
        ]
        video_state = "播放中" if self.embedded_video_playback and self.embedded_video_playback.status in {"playing", "paused"} else "待机"
        return [
            {
                "title": "当前状态",
                "lines": [
                    f"场景：{scene_label}",
                    f"阅读：{reading_state} · 历史 {len(self.text_history)} 条",
                    " · ".join(flow_labels),
                    f"视频：{video_state} · 字体：{self.font_source_status}",
                ],
            },
            {
                "title": "体验设置",
                "lines": [
                    f"主题：{self.get_setting_value_label('themeMode')} · 显示：{self.get_setting_value_label('displayMode')}",
                    f"语言：{self.get_setting_value_label('language')} · 文字：{self.get_setting_value_label('textSpeed')}",
                    f"大小：{self.get_setting_value_label('textScalePercent')} · 自动：{self.get_setting_value_label('autoPlayDelayMs')}",
                    f"文本框：{self.get_setting_value_label('dialogBoxOpacityPercent')} · 等语音：{self.get_setting_value_label('autoPlayWaitForVoice')}",
                    f"音量：总 {self.get_setting_value_label('masterVolume')} / BGM {self.get_setting_value_label('bgmVolume')} / 语音 {self.get_setting_value_label('voiceVolume')}",
                ],
            },
            {
                "title": "阅读推进",
                "lines": [
                    "Enter / Space / 左键 / 滚轮下：推进文本",
                    "A：自动播放 · S：已读快进",
                    "H / 滚轮上：文本历史 · R / V：语音回听",
                    "U / 鼠标中键：隐藏或恢复 UI",
                ],
            },
            {
                "title": "系统与存档",
                "lines": [
                    "F1 / Tab / 右键：系统菜单 · F2 / ?：操作帮助",
                    "F5：快存 · F8/F9：快读",
                    "F6：正式存档 · F7：读取存档",
                    "F11：窗口 / 全屏 · F12 / P：截图",
                ],
            },
        ]

    def get_help_quick_actions(self) -> list[dict]:
        return [
            {"key": "settings", "label": "体验设置", "shortcut": "S"},
            {"key": "save", "label": "正式存档", "shortcut": "F6"},
            {"key": "load", "label": "读取存档", "shortcut": "F7"},
            {"key": "history", "label": "文本历史", "shortcut": "H"},
            {"key": "archives", "label": "资料馆", "shortcut": "A"},
            {"key": "profile", "label": "玩家档案", "shortcut": "P"},
        ]

    def activate_help_action(self, action_key: str) -> bool:
        if action_key == "settings":
            self.open_settings_overlay()
        elif action_key == "save":
            self.open_save_dialog("save")
        elif action_key == "load":
            self.open_save_dialog("load")
        elif action_key == "history":
            self.open_text_history_overlay()
        elif action_key == "archives":
            self.open_archive_overlay()
        elif action_key == "profile":
            self.open_profile_overlay()
        elif action_key == "system":
            self.open_system_menu()
        else:
            self.close_overlay()
        return True

    def render_help_overlay(self) -> None:
        palette = self.get_active_palette()
        panel = self.pygame.Rect(0, 0, min(self.width - 72, 1020), min(self.height - 64, 660))
        panel.center = (self.width // 2, self.height // 2)
        self.pygame.draw.rect(self.screen, (*palette["panel"], 246), panel, border_radius=28)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 72), panel, 2, border_radius=28)
        self.draw_game_ui_panel_frame(panel, "system")
        self.screen.blit(self.font_title.render("原生操作中心", True, palette["text"]), (panel.left + 26, panel.top + 18))
        self.screen.blit(
            self.font_ui.render("F2 / ? 随时打开 · 查看当前状态 · 直接跳转常用面板", True, palette["muted"]),
            (panel.left + 26, panel.top + 54),
        )

        grid_left = panel.left + 26
        grid_top = panel.top + 88
        grid_gap = 14
        action_area_height = 110
        card_width = max(190, (panel.width - 52 - grid_gap) // 2)
        card_height = max(90, (panel.bottom - action_area_height - grid_top - grid_gap) // 2)
        for index, section in enumerate(self.get_help_overlay_sections()):
            column = index % 2
            row = index // 2
            card_rect = self.pygame.Rect(
                grid_left + column * (card_width + grid_gap),
                grid_top + row * (card_height + grid_gap),
                card_width,
                card_height,
            )
            self.pygame.draw.rect(self.screen, with_alpha(palette["accent"], 16), card_rect, border_radius=20)
            self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 28), card_rect, 1, border_radius=20)
            self.screen.blit(self.font_body.render(str(section["title"]), True, palette["accent"]), (card_rect.left + 14, card_rect.top + 10))
            line_y = card_rect.top + 38
            for line in section["lines"]:
                line_rect = self.pygame.Rect(card_rect.left + 14, line_y, card_rect.width - 28, self.font_ui.get_height() + 4)
                line_y = self.blit_wrapped_text(self.font_ui, str(line), line_rect, palette["text"], line_gap=2, max_lines=1) + 2

        action_items = self.get_help_quick_actions()
        action_top = panel.bottom - 102
        action_gap = 10
        action_width = max(96, (panel.width - 52 - action_gap * (len(action_items) - 1)) // len(action_items))
        for index, action in enumerate(action_items):
            action_rect = self.pygame.Rect(
                panel.left + 26 + index * (action_width + action_gap),
                action_top,
                action_width,
                38,
            )
            self.pygame.draw.rect(self.screen, with_alpha(palette["accentAlt"], 26), action_rect, border_radius=16)
            self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 42), action_rect, 1, border_radius=16)
            self.draw_game_ui_button_frame(action_rect, self.get_game_ui_button_state(action_rect))
            label = f"{action['label']} · {action['shortcut']}"
            self.blit_text_center(self.font_ui, label, action_rect.centerx, action_rect.top + 9, palette["text"])
            self.overlay_hotspots.append({"kind": "help-action", "value": action["key"], "rect": action_rect})

        close_rect = self.pygame.Rect(panel.right - 134, panel.bottom - 48, 104, 32)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panel"], 58), close_rect, border_radius=14)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 42), close_rect, 1, border_radius=14)
        self.draw_game_ui_button_frame(close_rect, self.get_game_ui_button_state(close_rect))
        self.blit_text_center(self.font_ui, "关闭", close_rect.centerx, close_rect.top + 7, palette["text"])
        self.overlay_hotspots.append({"kind": "close", "rect": close_rect})
        self.screen.blit(self.font_ui.render("点击上方入口或按 S/H/A/P 快速跳转 · Enter / Esc / 右键关闭", True, palette["muted"]), (panel.left + 26, panel.bottom - 38))

    def render_text_history_overlay(self) -> None:
        palette = self.get_active_palette()
        panel = self.pygame.Rect(0, 0, min(self.width - 88, 860), min(self.height - 96, 620))
        panel.center = (self.width // 2, self.height // 2)
        self.pygame.draw.rect(self.screen, (*palette["panel"], 246), panel, border_radius=28)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 72), panel, 2, border_radius=28)
        self.draw_game_ui_panel_frame(panel, "system")
        self.screen.blit(self.font_title.render("文本历史", True, palette["text"]), (panel.left + 28, panel.top + 24))
        subtitle = f"已记录 {len(self.text_history)} 条 · 字体：{self.font_source_status}"
        self.screen.blit(self.font_ui.render(subtitle[:72], True, palette["muted"]), (panel.left + 28, panel.top + 60))

        list_rect = self.pygame.Rect(panel.left + 28, panel.top + 98, panel.width - 56, panel.height - 164)
        self.pygame.draw.rect(self.screen, with_alpha(palette["accent"], 16), list_rect, border_radius=20)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 24), list_rect, 1, border_radius=20)
        if not self.text_history:
            self.blit_text_center(self.font_body, "还没有历史文本", list_rect.centerx, list_rect.centery - 18, palette["muted"])
        else:
            visible_count = max(1, list_rect.height // 104)
            max_start = max(0, len(self.text_history) - visible_count)
            start = max(0, min(max_start, self.history_scroll_index - visible_count + 1))
            y = list_rect.top + 16
            for offset, item in enumerate(self.text_history[start : start + visible_count]):
                item_index = start + offset
                item_rect = self.pygame.Rect(list_rect.left + 10, y - 8, list_rect.width - 20, 96)
                is_active = item_index == self.history_scroll_index
                if is_active:
                    self.pygame.draw.rect(self.screen, with_alpha(palette["accent"], 28), item_rect, border_radius=16)
                    self.pygame.draw.rect(self.screen, with_alpha(palette["accentAlt"], 64), item_rect, 1, border_radius=16)
                speaker = str(item.get("speakerName") or "旁白")
                scene_name = str(item.get("sceneName") or "")
                has_voice = bool(str(item.get("voiceAssetId") or "").strip())
                header = f"{speaker} · {scene_name}" if scene_name else speaker
                self.screen.blit(self.font_ui.render(header[:56], True, palette["accent"]), (list_rect.left + 18, y))
                if has_voice:
                    voice_surface = self.font_ui.render("VOICE", True, palette["accentAlt"])
                    self.screen.blit(voice_surface, (list_rect.right - voice_surface.get_width() - 18, y))
                text_rect = self.pygame.Rect(list_rect.left + 18, y + 24, list_rect.width - 36, 62)
                self.blit_wrapped_text(self.font_ui, str(item.get("text") or ""), text_rect, palette["text"], line_gap=4, max_lines=3)
                self.overlay_hotspots.append({"kind": "history-item", "value": item_index, "rect": item_rect})
                y += 104

        close_rect = self.pygame.Rect(panel.right - 138, panel.bottom - 56, 108, 34)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panel"], 58), close_rect, border_radius=14)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 42), close_rect, 1, border_radius=14)
        self.draw_game_ui_button_frame(close_rect, self.get_game_ui_button_state(close_rect))
        self.blit_text_center(self.font_ui, "关闭", close_rect.centerx, close_rect.top + 8, palette["text"])
        self.overlay_hotspots.append({"kind": "close", "rect": close_rect})
        hint = "↑↓ 选择 · R/V 重听语音 · PageUp/PageDown 快速滚动 · Esc 关闭"
        self.screen.blit(self.font_ui.render(hint, True, palette["muted"]), (panel.left + 28, panel.bottom - 44))

    def render_settings_overlay(self) -> None:
        palette = self.get_active_palette()
        panel = self.pygame.Rect(0, 0, min(self.width - 72, 600), min(self.height - 48, 500))
        panel.center = (self.width // 2, self.height // 2)
        self.pygame.draw.rect(self.screen, (*palette["panel"], 246), panel, border_radius=28)
        self.pygame.draw.rect(
            self.screen,
            with_alpha(palette["panelBorder"], 72),
            panel,
            2,
            border_radius=28,
        )
        self.draw_game_ui_panel_frame(panel, "system")
        self.screen.blit(self.font_title.render("体验设置", True, palette["text"]), (panel.left + 28, panel.top + 24))
        self.screen.blit(
            self.font_ui.render("主题 / 显示 / 语言 / 阅读辅助 / 文本框 / 自动播放 / 四路音量", True, palette["muted"]),
            (panel.left + 28, panel.top + 58),
        )

        button_top = panel.top + 96
        row_height = 44
        available_height = max(row_height, panel.bottom - 70 - button_top)
        visible_count = max(1, min(len(SETTINGS_MENU_ITEMS), available_height // row_height))
        max_start = max(0, len(SETTINGS_MENU_ITEMS) - visible_count)
        visible_start = max(0, min(max_start, self.settings_menu_index - visible_count + 1))
        visible_items = SETTINGS_MENU_ITEMS[visible_start : visible_start + visible_count]
        for offset, (setting_key, setting_label) in enumerate(visible_items):
            index = visible_start + offset
            row_rect = self.pygame.Rect(panel.left + 24, button_top + offset * row_height, panel.width - 48, 36)
            is_active = index == self.settings_menu_index
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accent"] if is_active else palette["panel"], 70 if is_active else 34),
                row_rect,
                border_radius=16,
            )
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accentAlt"] if is_active else palette["panelBorder"], 82 if is_active else 22),
                row_rect,
                1,
                border_radius=16,
            )
            self.draw_game_ui_button_frame(row_rect, self.get_game_ui_button_state(row_rect, active=is_active))
            self.screen.blit(self.font_ui.render(setting_label, True, palette["text"]), (row_rect.left + 14, row_rect.top + 10))
            value_label = self.get_setting_value_label(setting_key)
            value_surface = self.font_ui.render(value_label, True, palette["muted"])
            self.screen.blit(value_surface, (row_rect.right - value_surface.get_width() - 48, row_rect.top + 10))
            self.screen.blit(self.font_ui.render("◀", True, palette["text"]), (row_rect.right - 32, row_rect.top + 9))
            self.screen.blit(self.font_ui.render("▶", True, palette["text"]), (row_rect.right - 16, row_rect.top + 9))
            self.overlay_hotspots.append({"kind": "settings-item", "value": setting_key, "index": index, "rect": row_rect})

        range_label = f"{visible_start + 1}-{visible_start + len(visible_items)}/{len(SETTINGS_MENU_ITEMS)}"
        self.screen.blit(self.font_ui.render(range_label, True, palette["muted"]), (panel.right - 96, panel.top + 62))
        hint = "↑↓ 切换 · ←→ 调整 · Enter 切换 · Esc 返回"
        self.screen.blit(self.font_ui.render(hint, True, palette["muted"]), (panel.left + 28, panel.bottom - 44))

    def render_archive_overlay(self) -> None:
        palette = self.get_active_palette()
        entries = self.get_archive_entries(self.current_archive_key)
        selected_entry = self.get_selected_archive_entry()
        visible_start, visible_entries = self.get_visible_archive_window(entries)
        panel = self.pygame.Rect(0, 0, min(self.width - 72, 1120), min(self.height - 92, 660))
        panel.center = (self.width // 2, self.height // 2)
        self.pygame.draw.rect(self.screen, (*palette["panel"], 246), panel, border_radius=28)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 72), panel, 2, border_radius=28)
        self.draw_game_ui_panel_frame(panel, "system")
        title = ARCHIVE_MENU_ITEMS.get(self.current_archive_key, "资料馆")
        self.screen.blit(self.font_title.render("资料馆", True, palette["text"]), (panel.left + 26, panel.top + 24))
        unlocked_count = sum(1 for entry in entries if entry.get("unlocked"))
        completion_suffix = ""
        if self.current_archive_key == "endings":
            completion_suffix = f" · 累计通关 {int(self.archive_progress.get('endingCompletionCount') or 0)} 次"
        summary = f"{title} · 已解锁 {unlocked_count} / {len(entries)}{completion_suffix}"
        self.screen.blit(self.font_ui.render(summary, True, palette["muted"]), (panel.left + 26, panel.top + 58))

        tabs_top = panel.top + 92
        tab_left = panel.left + 24
        tab_gap = 10
        tab_count = max(1, len(ARCHIVE_MENU_SEQUENCE))
        available_tab_width = panel.width - 48 - tab_gap * (tab_count - 1)
        tab_width = max(88, available_tab_width // tab_count)
        tab_height = 34
        for index, archive_key in enumerate(ARCHIVE_MENU_SEQUENCE):
            tab_rect = self.pygame.Rect(tab_left + index * (tab_width + tab_gap), tabs_top, tab_width, tab_height)
            is_active = archive_key == self.current_archive_key
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accent"] if is_active else palette["panel"], 74 if is_active else 34),
                tab_rect,
                border_radius=16,
            )
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accentAlt"] if is_active else palette["panelBorder"], 84 if is_active else 20),
                tab_rect,
                1,
                border_radius=16,
            )
            self.draw_game_ui_button_frame(tab_rect, self.get_game_ui_button_state(tab_rect, active=is_active))
            self.blit_text_center(self.font_ui, ARCHIVE_MENU_ITEMS[archive_key], tab_rect.centerx, tab_rect.top + 8, palette["text"])
            self.overlay_hotspots.append({"kind": "archive-tab", "value": archive_key, "rect": tab_rect})

        list_rect = self.pygame.Rect(panel.left + 24, panel.top + 138, 360, panel.height - 190)
        hero_rect = self.pygame.Rect(list_rect.right + 20, panel.top + 138, panel.right - list_rect.right - 44, panel.height - 190)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panel"], 42), list_rect, border_radius=20)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 24), list_rect, 1, border_radius=20)
        self.draw_game_ui_panel_frame(list_rect)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panel"], 42), hero_rect, border_radius=20)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 24), hero_rect, 1, border_radius=20)
        self.draw_game_ui_panel_frame(hero_rect)

        row_top = list_rect.top + 14
        row_height = 54
        for row_index, (entry_index, entry) in enumerate(visible_entries):
            row_rect = self.pygame.Rect(list_rect.left + 12, row_top + row_index * row_height, list_rect.width - 24, 44)
            is_active = entry_index == self.archive_selection_index
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accent"] if is_active else palette["panel"], 68 if is_active else 26),
                row_rect,
                border_radius=16,
            )
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accentAlt"] if is_active else palette["panelBorder"], 82 if is_active else 20),
                row_rect,
                1,
                border_radius=16,
            )
            self.draw_game_ui_button_frame(row_rect, self.get_game_ui_button_state(row_rect, active=is_active))
            title_text = entry["name"] if entry.get("unlocked") else "未解锁"
            self.screen.blit(self.font_ui.render(title_text[:22], True, palette["text"]), (row_rect.left + 14, row_rect.top + 8))
            subtitle = entry.get("subtitle") or ""
            if not entry.get("unlocked"):
                subtitle = "推进剧情后解锁"
            self.screen.blit(self.font_ui.render(subtitle[:28], True, palette["muted"]), (row_rect.left + 14, row_rect.top + 24))
            self.overlay_hotspots.append({"kind": "archive-item", "value": entry_index, "rect": row_rect})

        if len(entries) > len(visible_entries):
            scroll_label = f"显示 {visible_start + 1}-{visible_start + len(visible_entries)} / {len(entries)}"
            self.screen.blit(self.font_ui.render(scroll_label, True, palette["muted"]), (list_rect.left + 14, list_rect.bottom - 26))

        if not selected_entry:
            self.blit_text_center(self.font_title, "当前没有可显示条目", hero_rect.centerx, hero_rect.top + 90, palette["muted"])
        else:
            hero_title = selected_entry["name"] if selected_entry.get("unlocked") else "？？？"
            self.screen.blit(self.font_title.render(hero_title, True, palette["text"]), (hero_rect.left + 22, hero_rect.top + 22))
            self.screen.blit(
                self.font_ui.render(
                    selected_entry.get("subtitle") if selected_entry.get("unlocked") else "推进剧情后解锁",
                    True,
                    palette["muted"],
                ),
                (hero_rect.left + 22, hero_rect.top + 62),
            )
            preview_rect = self.pygame.Rect(hero_rect.left + 22, hero_rect.top + 96, hero_rect.width - 44, hero_rect.height - 190)
            self.pygame.draw.rect(self.screen, with_alpha(palette["panel"], 22), preview_rect, border_radius=18)
            self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 16), preview_rect, 1, border_radius=18)
            self.draw_game_ui_panel_frame(preview_rect)

            preview_asset_id = str(selected_entry.get("previewAssetId") or "")
            if self.current_archive_key == "gallery" and selected_entry.get("unlocked"):
                image = self._load_image(str(selected_entry.get("id") or ""))
                if image:
                    image_width, image_height = image.get_size()
                    scale = min(preview_rect.width / max(1, image_width), preview_rect.height / max(1, image_height))
                    scaled = self.pygame.transform.smoothscale(
                        image,
                        (max(1, int(image_width * scale)), max(1, int(image_height * scale))),
                    )
                    image_rect = scaled.get_rect(center=preview_rect.center)
                    self.screen.blit(scaled, image_rect)
                else:
                    self.blit_text_center(self.font_body, "CG 预览未加载", preview_rect.centerx, preview_rect.centery - 16, palette["muted"])
            elif self.current_archive_key in {"chapters", "locations", "characters", "endings"} and selected_entry.get("unlocked") and preview_asset_id:
                image = self._load_image(preview_asset_id)
                if image:
                    image_width, image_height = image.get_size()
                    scale = min(preview_rect.width / max(1, image_width), preview_rect.height / max(1, image_height))
                    scaled = self.pygame.transform.smoothscale(
                        image,
                        (max(1, int(image_width * scale)), max(1, int(image_height * scale))),
                    )
                    image_rect = scaled.get_rect(center=preview_rect.center)
                    self.screen.blit(scaled, image_rect)
                else:
                    self.blit_text_center(self.font_body, "预览图未加载", preview_rect.centerx, preview_rect.centery - 16, palette["muted"])
            else:
                preview_label = {
                    "chapters": "章节回放预览",
                    "music": "音乐鉴赏预览",
                    "gallery": "CG 回想预览",
                    "locations": "地点图鉴预览",
                    "characters": "角色图鉴预览",
                    "narrations": "旁白摘录预览",
                    "relations": "关系图鉴预览",
                    "voices": "语音回听预览",
                    "endings": "结局回放预览",
                    "achievements": "成就馆预览",
                }.get(self.current_archive_key, "资料馆预览")
                self.blit_text_center(self.font_body, preview_label, preview_rect.centerx, preview_rect.centery - 16, palette["muted"])

            notes = selected_entry.get("notes") or ""
            preview_copy = str(selected_entry.get("previewText") or "")
            speaker_copy = str(selected_entry.get("previewSpeakerName") or "")
            if speaker_copy:
                self.screen.blit(
                    self.font_ui.render(speaker_copy[:28], True, palette["text"]),
                    (hero_rect.left + 22, hero_rect.bottom - 102),
                )
            self.screen.blit(
                self.font_ui.render(
                    (preview_copy if selected_entry.get("unlocked") and preview_copy else notes if selected_entry.get("unlocked") else "推进剧情后，这个条目会自动亮起。")[:72],
                    True,
                    palette["muted"],
                ),
                (hero_rect.left + 22, hero_rect.bottom - 78),
            )
            action_label = selected_entry.get("actionLabel") if selected_entry.get("unlocked") else "未解锁"
            action_rect = self.pygame.Rect(hero_rect.left + 22, hero_rect.bottom - 52, 160, 32)
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accent"] if selected_entry.get("actionEnabled") else palette["panel"], 76 if selected_entry.get("actionEnabled") else 24),
                action_rect,
                border_radius=14,
            )
            self.pygame.draw.rect(
                self.screen,
                with_alpha(palette["accentAlt"] if selected_entry.get("actionEnabled") else palette["panelBorder"], 84 if selected_entry.get("actionEnabled") else 20),
                action_rect,
                1,
                border_radius=14,
            )
            self.draw_game_ui_button_frame(
                action_rect,
                self.get_game_ui_button_state(
                    action_rect,
                    active=bool(selected_entry.get("actionEnabled")),
                    disabled=not bool(selected_entry.get("actionEnabled")),
                ),
            )
            self.blit_text_center(self.font_ui, action_label, action_rect.centerx, action_rect.top + 7, palette["text"])
            self.overlay_hotspots.append({"kind": "archive-action", "rect": action_rect})

        hint = "←→ 切换馆页 · ↑↓ 切换条目 · Enter 执行动作 · Esc 关闭"
        self.screen.blit(self.font_ui.render(hint, True, palette["muted"]), (panel.left + 26, panel.bottom - 30))

    def get_archive_detail_image_asset_id(self, archive_key: str, entry: dict) -> str:
        if archive_key == "gallery":
            return str(entry.get("id") or "")
        return str(entry.get("previewAssetId") or "")

    def get_archive_detail_body(self, archive_key: str, entry: dict) -> str:
        title = str(entry.get("name") or "未命名条目")
        subtitle = str(entry.get("subtitle") or "")
        notes = str(entry.get("notes") or "")
        preview_text = str(entry.get("previewText") or "")
        speaker = str(entry.get("previewSpeakerName") or "")
        if archive_key == "gallery":
            return notes or preview_text or "这张 CG 已经解锁，可以在这里以大图方式查看。"
        if archive_key == "locations":
            return notes or preview_text or "这个地点来自剧情中的背景切换。"
        if archive_key == "characters":
            character = self.characters_by_id.get(str(entry.get("id") or "")) or {}
            base_body = notes or preview_text or f"{title} 已经收录进角色图鉴。"
            preview_lines = self.get_character_model_preview_lines(character)
            if preview_lines:
                return f"{base_body}\n\n" + "；".join(preview_lines)
            return base_body
        if archive_key == "narrations":
            return preview_text or notes or "这段旁白已经收录，可以在这里单独回看。"
        if archive_key == "relations":
            prefix = f"{speaker}：" if speaker else ""
            return f"{prefix}{preview_text or notes or subtitle or '这组关系已经在剧情中出现。'}"
        if archive_key == "achievements":
            return notes or subtitle or "这个成就已经点亮。"
        return preview_text or notes or subtitle or title

    def render_archive_detail_overlay(self) -> None:
        palette = self.get_active_palette()
        archive_key = self.archive_detail_key or self.current_archive_key
        entry = self.archive_detail_entry or self.get_selected_archive_entry() or {}
        panel = self.pygame.Rect(0, 0, min(self.width - 72, 1120), min(self.height - 92, 660))
        panel.center = (self.width // 2, self.height // 2)
        self.pygame.draw.rect(self.screen, (*palette["panel"], 248), panel, border_radius=28)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 76), panel, 2, border_radius=28)
        self.draw_game_ui_panel_frame(panel, "system")

        archive_title = ARCHIVE_MENU_ITEMS.get(archive_key, "资料馆")
        self.screen.blit(self.font_title.render(archive_title, True, palette["text"]), (panel.left + 28, panel.top + 24))
        self.screen.blit(
            self.font_ui.render("详情查看 · 这里展示条目的完整预览和说明", True, palette["muted"]),
            (panel.left + 28, panel.top + 60),
        )

        media_rect = self.pygame.Rect(panel.left + 28, panel.top + 100, int(panel.width * 0.54), panel.height - 172)
        content_rect = self.pygame.Rect(media_rect.right + 26, panel.top + 104, panel.right - media_rect.right - 54, panel.height - 182)
        image_asset_id = self.get_archive_detail_image_asset_id(archive_key, entry)
        empty_label = {
            "gallery": "CG 大图未加载",
            "locations": "地点预览未加载",
            "characters": "角色立绘未加载",
            "relations": "关系预览未加载",
            "narrations": "旁白摘录",
            "achievements": "成就详情",
        }.get(archive_key, "详情预览")
        self.render_contained_image(image_asset_id, media_rect, empty_label, palette)

        name = str(entry.get("name") or "未命名条目")
        subtitle = str(entry.get("subtitle") or "")
        self.screen.blit(self.font_title.render(name[:24], True, palette["text"]), (content_rect.left, content_rect.top))
        subtitle_y = content_rect.top + self.font_title.get_height() + 8
        if subtitle:
            self.blit_wrapped_text(
                self.font_ui,
                subtitle,
                self.pygame.Rect(content_rect.left, subtitle_y, content_rect.width, 44),
                palette["muted"],
                line_gap=4,
                max_lines=2,
            )

        body_top = subtitle_y + 58
        body_rect = self.pygame.Rect(content_rect.left, body_top, content_rect.width, max(80, content_rect.bottom - body_top - 82))
        self.blit_wrapped_text(self.font_body, self.get_archive_detail_body(archive_key, entry), body_rect, palette["text"], line_gap=8)

        meta_rows = []
        if archive_key == "characters":
            character = self.characters_by_id.get(str(entry.get("id") or "")) or {}
            expressions = character.get("expressions") or []
            preview_report = self.get_character_model_preview_report(character)
            meta_rows.append(f"表现类型：{self.get_character_presentation_mode_label(character)}")
            meta_rows.append(f"预览状态：{preview_report.get('statusLabel') or '待检查'}")
            meta_rows.append(f"表情数量：{len(expressions)}")
            meta_rows.append(f"默认站位：{character.get('defaultPosition') or 'center'}")
            meta_rows.append(f"模型素材：{self.get_character_model_asset_label(character)}")
        elif archive_key == "gallery":
            meta_rows.append(f"CG ID：{entry.get('id') or 'unknown'}")
        elif archive_key == "achievements":
            meta_rows.append("状态：已点亮" if entry.get("unlocked") else "状态：未点亮")
        elif archive_key in {"narrations", "relations", "locations"}:
            meta_rows.append(f"来源：{subtitle or '剧情推进'}")

        meta_y = content_rect.bottom - 96
        for row in meta_rows[:4]:
            self.screen.blit(self.font_ui.render(row, True, palette["muted"]), (content_rect.left, meta_y))
            meta_y += 22

        back_rect = self.pygame.Rect(panel.right - 154, panel.bottom - 58, 126, 36)
        self.pygame.draw.rect(self.screen, with_alpha(palette["accent"], 74), back_rect, border_radius=14)
        self.pygame.draw.rect(self.screen, with_alpha(palette["accentAlt"], 84), back_rect, 1, border_radius=14)
        self.draw_game_ui_button_frame(back_rect, self.get_game_ui_button_state(back_rect, active=True))
        self.blit_text_center(self.font_ui, "返回资料馆", back_rect.centerx, back_rect.top + 9, palette["text"])
        self.overlay_hotspots.append({"kind": "archive-detail-back", "rect": back_rect})
        hint = "Enter / Esc 返回资料馆"
        self.screen.blit(self.font_ui.render(hint, True, palette["muted"]), (panel.left + 28, panel.bottom - 44))

    def blit_text_center(self, font, text: str, center_x: int, top_y: int, color, target=None) -> None:
        target = target or self.screen
        surface = font.render(text, True, color)
        rect = surface.get_rect(midtop=(center_x, top_y))
        target.blit(surface, rect)

    def blit_wrapped_text(self, font, text: str, rect, color, line_gap: int = 6, max_lines: int | None = None) -> int:
        lines = wrap_text(font, str(text or ""), max(1, rect.width))
        if max_lines is not None:
            lines = lines[: max(0, max_lines)]
        y = rect.top
        line_height = font.get_height() + line_gap
        for line in lines:
            if y + font.get_height() > rect.bottom:
                break
            self.screen.blit(font.render(line, True, color), (rect.left, y))
            y += line_height
        return y

    def render_contained_image(self, asset_id: str | None, rect, empty_label: str, palette: dict) -> None:
        asset = self.assets_by_id.get(str(asset_id or "")) or {}
        image = self._load_image(asset_id)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panel"], 36), rect, border_radius=22)
        self.pygame.draw.rect(self.screen, with_alpha(palette["panelBorder"], 28), rect, 1, border_radius=22)
        self.draw_game_ui_panel_frame(rect)
        if asset.get("type") == "scene3d":
            center_x = rect.centerx
            center_y = rect.centery + 34
            scale = max(22, min(rect.width, rect.height) * 0.10)
            for value in range(-4, 5):
                start = self.project_scene3d_grid_point(value, -5, center_x, center_y, scale)
                end = self.project_scene3d_grid_point(value, 5, center_x, center_y, scale)
                self.pygame.draw.line(self.screen, with_alpha(palette["accent"], 34), start, end, 1)
                start = self.project_scene3d_grid_point(-5, value, center_x, center_y, scale)
                end = self.project_scene3d_grid_point(5, value, center_x, center_y, scale)
                self.pygame.draw.line(self.screen, with_alpha(palette["accentAlt"], 34), start, end, 1)
            self.blit_text_center(self.font_body, "3D 场景预览桥", rect.centerx, rect.top + 44, palette["text"])
            self.blit_text_center(self.font_ui, str(asset.get("name") or asset_id or "未命名场景"), rect.centerx, rect.top + 84, palette["muted"])
            return
        if not image:
            self.blit_text_center(self.font_body, empty_label, rect.centerx, rect.centery - 18, palette["muted"])
            return
        image_width, image_height = image.get_size()
        scale = min(rect.width / max(1, image_width), rect.height / max(1, image_height))
        scaled = self.pygame.transform.smoothscale(
            image,
            (max(1, int(image_width * scale)), max(1, int(image_height * scale))),
        )
        image_rect = scaled.get_rect(center=rect.center)
        self.screen.blit(scaled, image_rect)

    def build_save_summary_line(self) -> str:
        quick_save = self.save_store.get("quickSave")
        formal_slots = self.save_store.get("formalSlots") or [None] * self.formal_save_slot_count
        filled_formal = sum(1 for item in formal_slots if item)
        quick_label = "已就绪" if quick_save else "空"
        return f"快存：{quick_label} · 正式存档：{filled_formal}/{self.formal_save_slot_count} · 存档文件：{self.save_file_path.name}"

    def capture_screenshot(self) -> Path | None:
        screenshot_dir = get_runtime_screenshot_dir()
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        project_stem = Path(make_project_save_filename(self.project_id)).stem
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        screenshot_path = screenshot_dir / f"{project_stem}-{timestamp}.png"
        try:
            self.pygame.image.save(self.screen, str(screenshot_path))
        except Exception:
            self.status_message = "截图保存失败，请检查写入权限。"
            return None
        self.status_message = f"截图已保存：{screenshot_path.name}"
        return screenshot_path

    def is_help_shortcut_event(self, event) -> bool:
        if event.type != self.pygame.KEYDOWN:
            return False
        if event.key == self.pygame.K_F2:
            return True
        if str(getattr(event, "unicode", "") or "") == "?":
            return True
        slash_key = getattr(self.pygame, "K_SLASH", None)
        if slash_key is None or event.key != slash_key:
            return False
        event_mod = int(getattr(event, "mod", 0) or 0)
        return bool(event_mod & self.pygame.KMOD_SHIFT)

    def handle_event(self, event) -> bool:
        if event.type == self.pygame.QUIT:
            return False
        if event.type == self.pygame.KEYDOWN and event.key == self.pygame.K_ESCAPE:
            if self.overlay_mode:
                if self.overlay_mode == "title":
                    return False
                if self.overlay_mode == "archive-detail":
                    self.close_archive_detail()
                    return True
                self.close_overlay()
                return True
            if self.restore_ui_hidden():
                return True
            return False
        if event.type == self.pygame.KEYDOWN:
            if event.key in (self.pygame.K_F12, self.pygame.K_p):
                self.capture_screenshot()
                return True
            if self.is_help_shortcut_event(event):
                if self.overlay_mode == "help":
                    self.close_overlay()
                else:
                    self.open_help_overlay()
                return True
            if self.ui_hidden and event.key == self.pygame.K_u:
                self.restore_ui_hidden()
                return True
            if self.ui_hidden and event.key not in {self.pygame.K_F11}:
                self.restore_ui_hidden()
                return True
            if self.current_line and self.current_line.get("type") == "video_play":
                if event.key in (self.pygame.K_v, self.pygame.K_SPACE):
                    self.open_current_video()
                    return True
                if event.key == self.pygame.K_o:
                    self.open_current_video_external()
                    return True
            if event.key == self.pygame.K_F11:
                self.toggle_display_mode()
                return True
            if self.overlay_mode == "title":
                return self.handle_overlay_event(event)
            if event.key in (self.pygame.K_F1, self.pygame.K_TAB):
                self.open_system_menu()
                return True
            if event.key == self.pygame.K_F6:
                self.open_save_dialog("save")
                return True
            if event.key == self.pygame.K_F7:
                self.open_save_dialog("load")
                return True
            if self.handle_save_shortcuts(event):
                return True
            if self.overlay_mode:
                return self.handle_overlay_event(event)
            if not self.current_choices and self.handle_scene3d_preview_key(event):
                return True
            if event.key == self.pygame.K_u:
                self.toggle_ui_hidden()
                return True
            if event.key == self.pygame.K_h:
                self.open_text_history_overlay()
                return True
            if event.key == self.pygame.K_a:
                self.toggle_auto_play()
                return True
            if event.key == self.pygame.K_s:
                self.toggle_skip_read()
                return True

        if event.type == self.pygame.MOUSEWHEEL:
            if self.ui_hidden:
                self.restore_ui_hidden()
                return True
            if self.overlay_mode:
                return self.handle_overlay_event(event)
            if event.y > 0:
                self.open_text_history_overlay()
                return True
            if event.y < 0 and self.current_line:
                self.advance_current_line_if_allowed()
                return True

        if event.type == self.pygame.MOUSEBUTTONDOWN and event.button == 3:
            if self.ui_hidden:
                self.restore_ui_hidden()
                return True
            if self.overlay_mode:
                if self.overlay_mode == "title":
                    return True
                if self.overlay_mode == "archive-detail":
                    self.close_archive_detail()
                    return True
                self.close_overlay()
                return True
            self.open_system_menu()
            return True

        if event.type == self.pygame.MOUSEBUTTONDOWN and event.button == 2:
            if self.overlay_mode:
                return self.handle_overlay_event(event)
            self.toggle_ui_hidden()
            return True

        if event.type == self.pygame.MOUSEBUTTONDOWN and event.button == 1 and self.ui_hidden:
            self.restore_ui_hidden()
            return True

        if event.type == self.pygame.MOUSEBUTTONDOWN and event.button in {4, 5}:
            if self.ui_hidden:
                self.restore_ui_hidden()
                return True
            if self.overlay_mode:
                return self.handle_overlay_event(event)
            if event.button == 4:
                self.open_text_history_overlay()
                return True
            if self.current_line:
                self.advance_current_line_if_allowed()
                return True

        if self.overlay_mode and event.type == self.pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.handle_overlay_event(event)

        if self.current_choices:
            return self.handle_choice_event(event)

        if self.current_line and self.current_line.get("type") == "video_play" and event.type == self.pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.handle_video_card_mouse_event(event)

        if self.current_line or self.finished:
            if event.type == self.pygame.KEYDOWN and event.key in (self.pygame.K_RETURN, self.pygame.K_SPACE):
                if self.finished:
                    return False
                self.advance_current_line_if_allowed()
            elif event.type == self.pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.restore_ui_hidden():
                    return True
                if self.finished:
                    return False
                self.advance_current_line_if_allowed()
        return True

    def handle_overlay_event(self, event) -> bool:
        if self.overlay_mode == "title":
            return self.handle_title_overlay_event(event)
        if self.overlay_mode in {"save", "load"}:
            return self.handle_save_dialog_event(event)
        if self.overlay_mode == "system":
            return self.handle_system_menu_event(event)
        if self.overlay_mode == "help":
            return self.handle_help_overlay_event(event)
        if self.overlay_mode == "history":
            return self.handle_text_history_overlay_event(event)
        if self.overlay_mode == "profile":
            return self.handle_profile_overlay_event(event)
        if self.overlay_mode == "auto-resume":
            return self.handle_auto_resume_overlay_event(event)
        if self.overlay_mode == "settings":
            return self.handle_settings_overlay_event(event)
        if self.overlay_mode == "archives":
            return self.handle_archive_overlay_event(event)
        if self.overlay_mode == "archive-detail":
            return self.handle_archive_detail_overlay_event(event)
        return True

    def handle_title_overlay_event(self, event) -> bool:
        pygame = self.pygame
        menu_items = self.get_title_menu_items()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.title_menu_index = (self.title_menu_index - 1) % len(menu_items)
                return True
            if event.key == pygame.K_DOWN:
                self.title_menu_index = (self.title_menu_index + 1) % len(menu_items)
                return True
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.activate_title_menu_item(str(menu_items[self.title_menu_index]["key"]))
            shortcut_map = {
                pygame.K_n: "start",
                pygame.K_r: "resume",
                pygame.K_l: "load",
                pygame.K_s: "settings",
                pygame.K_a: "archives",
            }
            if event.key in shortcut_map:
                return self.activate_title_menu_item(shortcut_map[event.key])
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for target in self.overlay_hotspots:
                if target.get("kind") == "title-item" and target["rect"].collidepoint(event.pos):
                    for index, item in enumerate(menu_items):
                        if item["key"] == target.get("value"):
                            self.title_menu_index = index
                            break
                    return self.activate_title_menu_item(str(target.get("value") or "start"))
        return True

    def handle_save_dialog_event(self, event) -> bool:
        pygame = self.pygame
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.change_save_dialog_page(-1)
                return True
            if event.key == pygame.K_RIGHT:
                self.change_save_dialog_page(1)
                return True
            if event.key == pygame.K_UP:
                self.overlay_focus_index = (self.overlay_focus_index - 2) % max(1, self.get_save_dialog_slot_count())
                self.normalize_overlay_focus()
                return True
            if event.key == pygame.K_DOWN:
                self.overlay_focus_index = (self.overlay_focus_index + 2) % max(1, self.get_save_dialog_slot_count())
                self.normalize_overlay_focus()
                return True
            if event.key == pygame.K_a:
                self.overlay_focus_index = max(0, self.overlay_focus_index - 1)
                return True
            if event.key == pygame.K_d:
                self.overlay_focus_index = min(max(0, self.get_save_dialog_slot_count() - 1), self.overlay_focus_index + 1)
                return True
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.activate_overlay_slot(self.overlay_focus_index)
                return True
            digit_map = {
                pygame.K_1: 0,
                pygame.K_2: 1,
                pygame.K_3: 2,
                pygame.K_4: 3,
                pygame.K_5: 4,
                pygame.K_6: 5,
            }
            if event.key in digit_map:
                self.activate_overlay_slot(digit_map[event.key])
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for target in self.overlay_hotspots:
                if target["rect"].collidepoint(event.pos):
                    kind = target.get("kind")
                    if kind == "slot":
                        self.activate_overlay_slot(int(target.get("value", 0)))
                    elif kind == "prev":
                        self.change_save_dialog_page(-1)
                    elif kind == "next":
                        self.change_save_dialog_page(1)
                    elif kind == "switch":
                        self.open_save_dialog("load" if self.overlay_mode == "save" else "save")
                    elif kind == "close":
                        self.close_overlay()
                    return True
        return True

    def handle_system_menu_event(self, event) -> bool:
        pygame = self.pygame
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.system_menu_index = (self.system_menu_index - 1) % len(SYSTEM_MENU_ITEMS)
                return True
            if event.key == pygame.K_DOWN:
                self.system_menu_index = (self.system_menu_index + 1) % len(SYSTEM_MENU_ITEMS)
                return True
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.activate_system_menu_item(SYSTEM_MENU_ITEMS[self.system_menu_index][0])
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for target in self.overlay_hotspots:
                if target["kind"] == "system-item" and target["rect"].collidepoint(event.pos):
                    return self.activate_system_menu_item(str(target["value"]))
        return True

    def handle_help_overlay_event(self, event) -> bool:
        pygame = self.pygame
        if event.type == pygame.KEYDOWN:
            shortcut_map = {
                pygame.K_s: "settings",
                pygame.K_h: "history",
                pygame.K_a: "archives",
                pygame.K_p: "profile",
                pygame.K_m: "system",
                pygame.K_l: "load",
                pygame.K_F6: "save",
                pygame.K_F7: "load",
            }
            if event.key in shortcut_map:
                return self.activate_help_action(shortcut_map[event.key])
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.close_overlay()
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for target in self.overlay_hotspots:
                if target.get("kind") == "help-action" and target["rect"].collidepoint(event.pos):
                    return self.activate_help_action(str(target.get("value") or ""))
                if target.get("kind") == "close" and target["rect"].collidepoint(event.pos):
                    self.close_overlay()
                    return True
        return True

    def handle_text_history_overlay_event(self, event) -> bool:
        pygame = self.pygame
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.history_scroll_index = max(0, self.history_scroll_index - 1)
                return True
            if event.key == pygame.K_DOWN:
                self.history_scroll_index = min(max(0, len(self.text_history) - 1), self.history_scroll_index + 1)
                return True
            if event.key == pygame.K_PAGEUP:
                self.history_scroll_index = max(0, self.history_scroll_index - 5)
                return True
            if event.key == pygame.K_PAGEDOWN:
                self.history_scroll_index = min(max(0, len(self.text_history) - 1), self.history_scroll_index + 5)
                return True
            if event.key in (pygame.K_r, pygame.K_v):
                return self.play_selected_history_voice()
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.close_overlay()
                return True
        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                self.history_scroll_index = max(0, self.history_scroll_index - 1)
                return True
            if event.y < 0:
                self.history_scroll_index = min(max(0, len(self.text_history) - 1), self.history_scroll_index + 1)
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for target in self.overlay_hotspots:
                if target.get("kind") == "history-item" and target["rect"].collidepoint(event.pos):
                    self.history_scroll_index = int(target.get("value") or 0)
                    if getattr(event, "clicks", 1) >= 2:
                        return self.play_selected_history_voice()
                    return True
                if target.get("kind") == "close" and target["rect"].collidepoint(event.pos):
                    self.close_overlay()
                    return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in {4, 5}:
            if event.button == 4:
                self.history_scroll_index = max(0, self.history_scroll_index - 1)
            else:
                self.history_scroll_index = min(max(0, len(self.text_history) - 1), self.history_scroll_index + 1)
            return True
        return True

    def handle_profile_overlay_event(self, event) -> bool:
        pygame = self.pygame
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.close_overlay()
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for target in self.overlay_hotspots:
                if target.get("kind") == "close" and target["rect"].collidepoint(event.pos):
                    self.close_overlay()
                    return True
        return True

    def handle_auto_resume_overlay_event(self, event) -> bool:
        pygame = self.pygame
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.load_auto_resume_snapshot()
                return True
            if event.key == pygame.K_c:
                self.clear_auto_resume_snapshot()
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for target in self.overlay_hotspots:
                if not target["rect"].collidepoint(event.pos):
                    continue
                kind = target.get("kind")
                if kind == "auto-resume-load":
                    self.load_auto_resume_snapshot()
                    return True
                if kind == "auto-resume-clear":
                    self.clear_auto_resume_snapshot()
                    return True
                if kind == "close":
                    self.close_overlay()
                    return True
        return True

    def handle_settings_overlay_event(self, event) -> bool:
        pygame = self.pygame
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.settings_menu_index = (self.settings_menu_index - 1) % len(SETTINGS_MENU_ITEMS)
                return True
            if event.key == pygame.K_DOWN:
                self.settings_menu_index = (self.settings_menu_index + 1) % len(SETTINGS_MENU_ITEMS)
                return True
            if event.key == pygame.K_LEFT:
                self.adjust_runtime_setting(SETTINGS_MENU_ITEMS[self.settings_menu_index][0], -1)
                return True
            if event.key == pygame.K_RIGHT:
                self.adjust_runtime_setting(SETTINGS_MENU_ITEMS[self.settings_menu_index][0], 1)
                return True
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.adjust_runtime_setting(SETTINGS_MENU_ITEMS[self.settings_menu_index][0], 1)
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, target in enumerate(self.overlay_hotspots):
                if target["kind"] == "settings-item" and target["rect"].collidepoint(event.pos):
                    self.settings_menu_index = int(target.get("index", index))
                    midpoint = target["rect"].centerx
                    self.adjust_runtime_setting(str(target["value"]), -1 if event.pos[0] < midpoint else 1)
                    return True
        return True

    def handle_archive_overlay_event(self, event) -> bool:
        pygame = self.pygame
        entries = self.get_archive_entries(self.current_archive_key)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.change_archive_tab(-1)
                return True
            if event.key == pygame.K_RIGHT:
                self.change_archive_tab(1)
                return True
            if event.key == pygame.K_UP and entries:
                self.archive_selection_index = (self.archive_selection_index - 1) % len(entries)
                return True
            if event.key == pygame.K_DOWN and entries:
                self.archive_selection_index = (self.archive_selection_index + 1) % len(entries)
                return True
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.activate_archive_entry(self.get_selected_archive_entry())
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for target in self.overlay_hotspots:
                if target["rect"].collidepoint(event.pos):
                    if target["kind"] == "archive-tab":
                        self.current_archive_key = str(target.get("value") or "chapters")
                        self.archive_selection_index = 0
                        return True
                    if target["kind"] == "archive-item":
                        self.archive_selection_index = int(target.get("value", 0))
                        return True
                    if target["kind"] == "archive-action":
                        return self.activate_archive_entry(self.get_selected_archive_entry())
        return True

    def handle_archive_detail_overlay_event(self, event) -> bool:
        pygame = self.pygame
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.close_archive_detail()
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for target in self.overlay_hotspots:
                if target.get("kind") == "archive-detail-back" and target["rect"].collidepoint(event.pos):
                    self.close_archive_detail()
                    return True
        return True

    def handle_save_shortcuts(self, event) -> bool:
        pygame = self.pygame
        if event.key == pygame.K_F5:
            self.save_quick()
            return True
        if event.key in (pygame.K_F8, pygame.K_F9):
            self.load_quick()
            return True

        event_mod = int(getattr(event, "mod", 0) or 0)
        is_ctrl = bool(event_mod & pygame.KMOD_CTRL) or bool(event_mod & pygame.KMOD_META)
        if not is_ctrl:
            return False

        slot_keys = {
            pygame.K_1: 0,
            pygame.K_2: 1,
            pygame.K_3: 2,
        }
        if event.key not in slot_keys:
            return False

        slot_index = slot_keys[event.key]
        if event_mod & pygame.KMOD_SHIFT:
            self.load_formal_slot(slot_index)
        else:
            self.save_formal_slot(slot_index)
        return True

    def handle_choice_event(self, event) -> bool:
        if not self.current_choices:
            return True
        if event.type == self.pygame.KEYDOWN:
            if event.key == self.pygame.K_UP:
                self.current_choice_index = (self.current_choice_index - 1) % len(self.current_choices)
            elif event.key == self.pygame.K_DOWN:
                self.current_choice_index = (self.current_choice_index + 1) % len(self.current_choices)
            elif event.key in (self.pygame.K_RETURN, self.pygame.K_SPACE):
                self.choose_current_option(self.current_choice_index)
        elif event.type == self.pygame.MOUSEBUTTONDOWN and event.button == 1:
            panel = self.get_dialog_panel_rect(max(212, 86 + len(self.current_choices) * 54))
            padding_x = int(self.dialog_box_config.get("paddingX", 18))
            padding_y = int(self.dialog_box_config.get("paddingY", 14))
            button_top = panel.top + padding_y + self.font_title.get_height() + 18
            button_width = panel.width - padding_x * 2
            for index, _option in enumerate(self.current_choices):
                row_rect = self.pygame.Rect(panel.left + padding_x, button_top + index * 52, button_width, 40)
                if row_rect.collidepoint(event.pos):
                    self.current_choice_index = index
                    self.choose_current_option(index)
                    break
        return True

    def run(self) -> int:
        running = True
        while running:
            dt_seconds = self.clock.tick(FPS) / 1000
            self.runtime_elapsed_seconds += dt_seconds
            for event in self.pygame.event.get():
                running = self.handle_event(event)
                if not running:
                    break
            self.update_stage_visual_effects(dt_seconds)
            self.update_particle_effect(dt_seconds)
            self.update_flow_assist()
            self.render()

        self.record_player_session_end()
        self.persist_auto_resume_snapshot()
        self.stop_bgm()
        self.stop_voice()
        return 0


def run_player(game_data_path: Path) -> int:
    try:
        import pygame
    except ImportError:
        bundle_dir = game_data_path.resolve().parent
        requirements_name = (
            "requirements-native-runtime.txt"
            if (bundle_dir / "requirements-native-runtime.txt").is_file()
            else "requirements.txt"
        )
        print("缺少依赖：pygame-ce")
        print(f"请先运行：python3 -m pip install -r {requirements_name}")
        return 1

    try:
        pygame.init()
        player = NativeRuntimePlayer(pygame, game_data_path)
        return player.run()
    except NativeRuntimeError as error:
        log_path = write_runtime_crash_log(game_data_path, error, "native_runtime_error")
        print(f"原生 Runtime 包无法启动：{error}")
        print(f"错误日志：{log_path}")
        show_runtime_error_screen(pygame, str(error), log_path)
        return 1
    except Exception as error:
        log_path = write_runtime_crash_log(game_data_path, error, "unexpected_error")
        print(f"原生 Runtime 包发生未处理错误：{error}")
        print(f"错误日志：{log_path}")
        show_runtime_error_screen(pygame, f"{type(error).__name__}: {error}", log_path)
        return 1
    finally:
        try:
            pygame.quit()
        except Exception:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Canvasia Engine 原生 Runtime 播放器")
    parser.add_argument("game_data", nargs="?", default=DEFAULT_GAME_DATA_NAME, help="导出的 game_data.json 路径")
    parser.add_argument("--validate-bundle", dest="validate_bundle", help="只检查导出包结构，不启动窗口")
    parser.add_argument("--release-check", dest="release_check", help="输出发布前自检报告 JSON，不启动窗口")
    parser.add_argument("--doctor", "--release-doctor", dest="doctor", help="一键运行原生 Runtime 发布体检报告 JSON，不启动窗口")
    parser.add_argument("--release-candidate-report", "--rc-report", dest="release_candidate_report", help="输出原生 Runtime 发布候选总报告 JSON，不启动窗口")
    parser.add_argument("--release-control-json", dest="release_control_json", help="输出原生 Runtime 发布总控报告 JSON，不启动窗口")
    parser.add_argument("--release-control-report", "--release-control-md", dest="release_control_report", help="输出原生 Runtime 发布总控 Markdown 报告，不启动窗口")
    parser.add_argument("--write-release-control-reports", dest="write_release_control_reports", help="写入原生 Runtime 发布总控 Markdown / JSON 报告，不启动窗口")
    parser.add_argument("--vn-baseline-quality-json", "--vn-quality-json", dest="vn_baseline_quality_json", help="输出原生 Runtime VN 基础质感报告 JSON，不启动窗口")
    parser.add_argument("--vn-baseline-quality-report", "--vn-quality-report", "--vn-quality-md", dest="vn_baseline_quality_report", help="输出原生 Runtime VN 基础质感 Markdown 报告，不启动窗口")
    parser.add_argument("--write-vn-baseline-quality-reports", "--write-vn-quality-reports", dest="write_vn_baseline_quality_reports", help="写入原生 Runtime VN 基础质感 Markdown / JSON 报告，不启动窗口")
    parser.add_argument("--acceptance-check", "--acceptance-json", dest="acceptance_check", help="输出原生 Runtime 发布验收清单 JSON，不启动窗口")
    parser.add_argument("--acceptance-report", "--acceptance-md", dest="acceptance_report", help="输出原生 Runtime 发布验收清单 Markdown，不启动窗口")
    parser.add_argument("--write-acceptance-reports", dest="write_acceptance_reports", help="写入原生 Runtime 发布验收清单 Markdown / JSON，不启动窗口")
    parser.add_argument("--file-integrity-report", dest="file_integrity_report", help="输出原生 Runtime 文件完整性清单 JSON，不启动窗口")
    parser.add_argument("--file-integrity-markdown", "--file-integrity-md", dest="file_integrity_markdown", help="输出原生 Runtime 文件完整性 Markdown 报告，不启动窗口")
    parser.add_argument("--write-file-integrity-reports", dest="write_file_integrity_reports", help="写入原生 Runtime 文件完整性 Markdown / JSON 报告，不启动窗口")
    parser.add_argument("--verify-file-integrity", dest="verify_file_integrity", help="校验原生 Runtime 文件完整性报告，不启动窗口")
    parser.add_argument("--exercise-save-load", dest="exercise_save_load", help="检查存档文件能否写入和读回")
    parser.add_argument("--exercise-settings", dest="exercise_settings", help="检查原生 Runtime 设置能否写入和读回")
    parser.add_argument("--exercise-archives", dest="exercise_archives", help="检查原生 Runtime 资料馆进度能否写入和读回")
    parser.add_argument("--exercise-particles", dest="exercise_particles", help="检查原生 Runtime 粒子配置能否生成可播放条目")
    parser.add_argument("--exercise-visual-effects", dest="exercise_visual_effects", help="检查原生 Runtime 高级演出配置能否规范化")
    parser.add_argument("--exercise-profile", dest="exercise_profile", help="检查原生 Runtime 玩家档案和续玩记录能否写入和读回")
    parser.add_argument("--describe-title-screen", dest="describe_title_screen", help="输出原生 Runtime 标题页配置摘要，不启动窗口")
    parser.add_argument("--describe-video-bridge", dest="describe_video_bridge", help="输出原生 Runtime 视频桥接摘要，不启动窗口")
    parser.add_argument("--describe-video-backends", dest="describe_video_backends", help="输出原生 Runtime 可选视频后端摘要，不启动窗口")
    parser.add_argument("--probe-video-preview", dest="probe_video_preview", help="输出原生 Runtime 可选视频帧 / 内嵌画面探针，不启动窗口")
    parser.add_argument("--describe-3d-assets", dest="describe_3d_assets", help="输出 3D 模型 / 3D 场景资产结构与依赖清单 JSON，不启动窗口")
    parser.add_argument("--describe-3d-assets-markdown", "--describe-3d-assets-md", dest="describe_3d_assets_markdown", help="输出 3D 模型 / 3D 场景资产清单 Markdown 摘要，不启动窗口")
    parser.add_argument("--describe-model-preview", dest="describe_model_preview", help="输出 Live2D / 3D 角色预览桥摘要，不启动窗口")
    parser.add_argument("--describe-scene3d-preview", dest="describe_scene3d_preview", help="输出 3D 场景交互预览桥摘要，不启动窗口")
    parser.add_argument("--describe-save-dialog", dest="describe_save_dialog", help="输出正式存档面板摘要，不启动窗口")
    parser.add_argument("--page", dest="save_dialog_page", type=int, default=0, help="配合 --describe-save-dialog 使用，指定页码")
    args = parser.parse_args(argv)

    if args.validate_bundle:
        try:
            validate_bundle(Path(args.validate_bundle).resolve())
            print("Native runtime bundle validation passed.")
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime bundle validation failed: {error}")
            return 1

    if args.release_check:
        print_release_check_report(Path(args.release_check).resolve())
        return 0

    if args.doctor:
        try:
            report = print_native_runtime_doctor_report(Path(args.doctor).resolve())
            return 1 if report.get("status") == "fail" else 0
        except NativeRuntimeError as error:
            print(f"Native runtime doctor failed: {error}")
            return 1

    if args.release_candidate_report:
        try:
            report = print_native_runtime_release_candidate_report(Path(args.release_candidate_report).resolve())
            return 1 if report.get("status") == "blocked" else 0
        except NativeRuntimeError as error:
            print(f"Native runtime release candidate report failed: {error}")
            return 1

    if args.release_control_json:
        try:
            print_native_runtime_release_control_json_report(Path(args.release_control_json).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime release control JSON failed: {error}")
            return 1

    if args.release_control_report:
        try:
            print_native_runtime_release_control_markdown_report(Path(args.release_control_report).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime release control report failed: {error}")
            return 1

    if args.write_release_control_reports:
        try:
            payload = write_native_runtime_release_control_reports(Path(args.write_release_control_reports).resolve())
            print(
                json.dumps(
                    {
                        "status": payload.get("qualityGate", {}).get("status"),
                        "label": payload.get("qualityGate", {}).get("label"),
                        "markdown": "native-runtime-release-control-report.md",
                        "json": "native-runtime-release-control-report.json",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime release control report write failed: {error}")
            return 1

    if args.vn_baseline_quality_json:
        try:
            report = print_native_runtime_vn_baseline_quality_json_report(Path(args.vn_baseline_quality_json).resolve())
            return 1 if report.get("status") == "needs_fix" else 0
        except NativeRuntimeError as error:
            print(f"Native runtime VN baseline quality JSON failed: {error}")
            return 1

    if args.vn_baseline_quality_report:
        try:
            report = print_native_runtime_vn_baseline_quality_markdown_report(Path(args.vn_baseline_quality_report).resolve())
            return 1 if report.get("status") == "needs_fix" else 0
        except NativeRuntimeError as error:
            print(f"Native runtime VN baseline quality report failed: {error}")
            return 1

    if args.write_vn_baseline_quality_reports:
        try:
            report = write_native_runtime_vn_baseline_quality_reports(Path(args.write_vn_baseline_quality_reports).resolve())
            print(
                json.dumps(
                    {
                        "status": report.get("status"),
                        "label": report.get("summary", {}).get("statusLabel"),
                        "markdown": VN_BASELINE_QUALITY_MARKDOWN_NAME,
                        "json": VN_BASELINE_QUALITY_REPORT_NAME,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 1 if report.get("status") == "needs_fix" else 0
        except NativeRuntimeError as error:
            print(f"Native runtime VN baseline quality report write failed: {error}")
            return 1

    if args.acceptance_check:
        try:
            report = print_native_runtime_acceptance_json_report(Path(args.acceptance_check).resolve())
            return 1 if report.get("acceptanceGate", {}).get("status") == "blocked" else 0
        except NativeRuntimeError as error:
            print(f"Native runtime acceptance check failed: {error}")
            return 1

    if args.acceptance_report:
        try:
            report = print_native_runtime_acceptance_markdown_report(Path(args.acceptance_report).resolve())
            return 1 if report.get("acceptanceGate", {}).get("status") == "blocked" else 0
        except NativeRuntimeError as error:
            print(f"Native runtime acceptance report failed: {error}")
            return 1

    if args.write_acceptance_reports:
        try:
            payload = write_native_runtime_acceptance_reports(Path(args.write_acceptance_reports).resolve())
            print(
                json.dumps(
                    {
                        "status": payload.get("acceptanceGate", {}).get("status"),
                        "label": payload.get("acceptanceGate", {}).get("label"),
                        "markdown": ACCEPTANCE_REPORT_NAME,
                        "json": ACCEPTANCE_JSON_NAME,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 1 if payload.get("acceptanceGate", {}).get("status") == "blocked" else 0
        except NativeRuntimeError as error:
            print(f"Native runtime acceptance report write failed: {error}")
            return 1

    if args.file_integrity_report:
        try:
            print_native_runtime_file_integrity_report(Path(args.file_integrity_report).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime file integrity report failed: {error}")
            return 1

    if args.file_integrity_markdown:
        try:
            print_native_runtime_file_integrity_markdown_report(Path(args.file_integrity_markdown).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime file integrity markdown failed: {error}")
            return 1

    if args.write_file_integrity_reports:
        try:
            payload = write_native_runtime_file_integrity_reports(Path(args.write_file_integrity_reports).resolve())
            print(
                json.dumps(
                    {
                        "status": "written",
                        "fileCount": payload.get("summary", {}).get("fileCount"),
                        "markdown": FILE_INTEGRITY_MARKDOWN_NAME,
                        "json": FILE_INTEGRITY_REPORT_NAME,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime file integrity report write failed: {error}")
            return 1

    if args.verify_file_integrity:
        try:
            report = print_native_runtime_file_integrity_verification(Path(args.verify_file_integrity).resolve())
            return 1 if report.get("status") == "fail" else 0
        except NativeRuntimeError as error:
            print(f"Native runtime file integrity verification failed: {error}")
            return 1

    if args.exercise_save_load:
        try:
            exercise_save_load(Path(args.exercise_save_load).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime save/load validation failed: {error}")
            return 1

    if args.exercise_settings:
        try:
            exercise_runtime_settings(Path(args.exercise_settings).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime settings validation failed: {error}")
            return 1

    if args.exercise_archives:
        try:
            exercise_archive_progress(Path(args.exercise_archives).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime archive validation failed: {error}")
            return 1

    if args.exercise_particles:
        try:
            exercise_particle_effect(Path(args.exercise_particles).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime particle validation failed: {error}")
            return 1

    if args.exercise_visual_effects:
        try:
            exercise_visual_effects(Path(args.exercise_visual_effects).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime visual effects validation failed: {error}")
            return 1

    if args.exercise_profile:
        try:
            exercise_player_profile(Path(args.exercise_profile).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime profile validation failed: {error}")
            return 1

    if args.describe_title_screen:
        try:
            print_native_title_screen_report(Path(args.describe_title_screen).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime title screen description failed: {error}")
            return 1

    if args.describe_video_bridge:
        try:
            print_native_video_bridge_report(Path(args.describe_video_bridge).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime video bridge description failed: {error}")
            return 1

    if args.describe_video_backends:
        try:
            print_native_video_backend_report(Path(args.describe_video_backends).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime video backend description failed: {error}")
            return 1

    if args.probe_video_preview:
        try:
            print_native_video_preview_probe_report(Path(args.probe_video_preview).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime video preview probe failed: {error}")
            return 1

    if args.describe_3d_assets:
        try:
            print_native_3d_asset_report(Path(args.describe_3d_assets).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime 3D asset report failed: {error}")
            return 1

    if args.describe_3d_assets_markdown:
        try:
            print_native_3d_asset_markdown_report(Path(args.describe_3d_assets_markdown).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime 3D asset markdown report failed: {error}")
            return 1

    if args.describe_model_preview:
        try:
            print_native_character_model_preview_report(Path(args.describe_model_preview).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime model preview description failed: {error}")
            return 1

    if args.describe_scene3d_preview:
        try:
            print_native_scene3d_preview_report(Path(args.describe_scene3d_preview).resolve())
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime 3D scene preview description failed: {error}")
            return 1

    if args.describe_save_dialog:
        try:
            describe_save_dialog(Path(args.describe_save_dialog).resolve(), page=args.save_dialog_page)
            return 0
        except NativeRuntimeError as error:
            print(f"Native runtime save dialog description failed: {error}")
            return 1

    return run_player(resolve_game_data_argument(args.game_data))


if __name__ == "__main__":
    raise SystemExit(main())
