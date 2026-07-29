from __future__ import annotations

import importlib
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path


VIDEO_TRANSPORT_MAX_SECONDS = 6 * 60 * 60
VIDEO_RESUME_MODES = frozenset({"restart", "resume"})
VIDEO_FIT_MODES = frozenset({"contain", "cover", "fill"})
NATIVE_VIDEO_OPTIONAL_REQUIREMENTS_NAME = "requirements-native-runtime-video.txt"
NATIVE_VIDEO_OPTIONAL_REQUIREMENTS_CANDIDATES = (
    NATIVE_VIDEO_OPTIONAL_REQUIREMENTS_NAME,
    "requirements-video.txt",
)
NATIVE_VIDEO_SYNC_BACKEND_ID = "pyav_audio_video_sync"
NATIVE_VIDEO_EMBEDDED_BACKEND_ID = "opencv_embedded_playback"

NATIVE_VIDEO_BACKEND_OPTIONS = (
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
        "notes": "优先使用音频播放时钟驱动画面，支持剪辑区间、循环、结束检测与读档续播；编码兼容性仍需目标系统实机验收。",
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
        "notes": "PyAV 不可用时的画面播放兜底：可识别剪辑结尾和循环，但不解音频。",
    },
)


def normalize_video_time_seconds(value: object, fallback: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = float(fallback)
    if number != number:
        number = float(fallback)
    return round(max(0.0, min(float(VIDEO_TRANSPORT_MAX_SECONDS), number)), 3)


def get_safe_video_volume(value: object, fallback: int = 100) -> int:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = float(fallback)
    if number != number:
        number = float(fallback)
    return int(max(0.0, min(100.0, number)) + 0.5)


def sanitize_video_transport(source: dict | None = None) -> dict:
    source = source if isinstance(source, dict) else {}
    loop = source.get("loop") is True
    start_time = normalize_video_time_seconds(source.get("startTimeSeconds"))
    raw_end_time = normalize_video_time_seconds(source.get("endTimeSeconds"))
    end_time = raw_end_time if raw_end_time > start_time else 0.0
    resume_mode = str(source.get("resumeMode") or "restart")
    if resume_mode not in VIDEO_RESUME_MODES:
        resume_mode = "restart"
    fit = str(source.get("fit") or "contain")
    if fit not in VIDEO_FIT_MODES:
        fit = "contain"
    return {
        "autoplay": source.get("autoplay") is not False,
        "loop": loop,
        "resumeMode": resume_mode,
        "startTimeSeconds": start_time,
        "endTimeSeconds": end_time,
        "fit": fit,
        "volume": get_safe_video_volume(source.get("volume")),
        "skippable": True if loop else source.get("skippable") is not False,
    }


def get_video_initial_position(
    source: dict | None = None,
    resume_time_seconds: object | None = None,
) -> float:
    transport = sanitize_video_transport(source)
    if (
        transport["resumeMode"] != "resume"
        or resume_time_seconds is None
        or resume_time_seconds == ""
    ):
        return float(transport["startTimeSeconds"])
    resume = normalize_video_time_seconds(resume_time_seconds, transport["startTimeSeconds"])
    if resume < transport["startTimeSeconds"]:
        return float(transport["startTimeSeconds"])
    if transport["endTimeSeconds"] > 0 and resume >= transport["endTimeSeconds"]:
        return float(transport["startTimeSeconds"])
    return resume


def get_video_playback_position(playback: object | None, fallback: object = 0.0) -> float:
    elapsed_ms = getattr(playback, "elapsed_ms", None) if playback is not None else None
    if elapsed_ms is None:
        return normalize_video_time_seconds(fallback)
    try:
        return normalize_video_time_seconds(float(elapsed_ms) / 1000.0, fallback)
    except (TypeError, ValueError):
        return normalize_video_time_seconds(fallback)


def build_video_clip_label(start_time_seconds: object, end_time_seconds: object) -> str:
    start = normalize_video_time_seconds(start_time_seconds)
    end = normalize_video_time_seconds(end_time_seconds)
    start_label = f"{start:g} 秒" if start > 0 else "开头"
    end_label = f"{end:g} 秒" if end > start else "自然结尾"
    return f"{start_label} → {end_label}"


def build_native_video_prompt(block: dict, asset: dict, asset_path: Path | None) -> str:
    transport = sanitize_video_transport(block)
    title = str(block.get("title") or asset.get("name") or "视频播放")
    lines = [
        title,
        "",
        "原生 Runtime 会优先在窗口内自动播放视频；PyAV 不可用或编码不兼容时，可改用 OpenCV 画面或系统播放器。",
    ]
    if asset_path:
        start_label = "自动开始" if transport["autoplay"] else "等待手动播放"
        loop_label = "循环播放" if transport["loop"] else "播放一次"
        lines.extend(
            [
                f"文件：{asset_path.name}",
                f"规则：{start_label} · {loop_label} · {build_video_clip_label(transport['startTimeSeconds'], transport['endTimeSeconds'])}",
                "操作：Space 播放/暂停；O 使用系统播放器；Enter 跳过或结束循环。",
            ]
        )
    else:
        lines.extend(
            [
                "视频文件没有被找到，可能是素材缺失或导出包不完整。",
                "建议回到编辑器重新导出，或改用网页包 / NW.js 桌面包验证视频。",
            ]
        )
    if transport["resumeMode"] == "resume":
        lines.append("存档提示：读档回到这里时会从保存的播放位置继续。")
    if not transport["skippable"]:
        lines.append("不可跳过：需要等待内嵌视频播放结束后才能继续。")
    lines.append("兼容提示：系统播放器桥接无法读取真实结束时间，播放后需回到游戏窗口确认继续。")
    return "\n".join(lines)


def build_native_video_line(
    block: dict,
    asset: dict,
    asset_path: Path | None,
    *,
    preview_mode: str,
    block_label: str,
    resume_time_seconds: object | None = None,
) -> dict:
    transport = sanitize_video_transport(block)
    initial_position = get_video_initial_position(transport, resume_time_seconds)
    return {
        "type": "video_play",
        "speakerId": None,
        "speakerName": "视频",
        "text": build_native_video_prompt(block, asset, asset_path),
        "voiceAssetId": None,
        "videoAssetId": str(block.get("assetId") or ""),
        "videoAssetPath": str(asset_path) if asset_path else "",
        "videoTitle": str(block.get("title") or asset.get("name") or "视频播放"),
        "videoFileName": asset_path.name if asset_path else "",
        "videoStartTimeSeconds": transport["startTimeSeconds"],
        "videoEndTimeSeconds": transport["endTimeSeconds"],
        "videoPlaybackPositionSeconds": initial_position,
        "videoClipLabel": build_video_clip_label(
            transport["startTimeSeconds"],
            transport["endTimeSeconds"],
        ),
        "videoFit": transport["fit"],
        "videoVolume": transport["volume"],
        "videoSkippable": transport["skippable"],
        "videoAutoplay": transport["autoplay"],
        "videoLoop": transport["loop"],
        "videoResumeMode": transport["resumeMode"],
        "videoPreviewMode": preview_mode,
        "videoOpened": False,
        "videoPlaybackFinished": False,
        "videoPlaybackMode": "",
        "blockLabel": block_label,
    }


def get_video_preview_cache_key(line: dict) -> str:
    video_path_value = str(line.get("videoAssetPath") or "").strip()
    if not video_path_value:
        return ""
    start_time = normalize_video_time_seconds(line.get("videoPlaybackPositionSeconds"))
    return f"{Path(video_path_value).resolve()}::{start_time:.3f}"


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
