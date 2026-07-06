from __future__ import annotations

import json
import platform
import sys
import traceback
from datetime import datetime
from pathlib import Path

try:
    from .runtime_player_settings import (
        build_project_default_runtime_player_settings,
        sanitize_runtime_player_settings,
    )
except ImportError:  # pragma: no cover - exported native packages import from the same directory.
    from runtime_player_settings import (
        build_project_default_runtime_player_settings,
        sanitize_runtime_player_settings,
    )


SAVE_ROOT_DIR_NAME = ".canvasia-engine"
SAVE_SUBDIR_NAME = "native-runtime-saves"
SETTINGS_SUBDIR_NAME = "native-runtime-settings"
PROGRESS_SUBDIR_NAME = "native-runtime-progress"
PROFILE_SUBDIR_NAME = "native-runtime-profiles"
AUTO_RESUME_SUBDIR_NAME = "native-runtime-autoresume"
LOG_SUBDIR_NAME = "native-runtime-logs"
SCREENSHOT_SUBDIR_NAME = "native-runtime-screenshots"
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


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


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


def write_project_save_store(project_id: str, save_store: dict) -> Path:
    save_dir = get_runtime_save_dir()
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = get_project_save_file_path(project_id)
    save_path.write_text(json.dumps(save_store, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return save_path


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
        safe_snapshot = {
            "kind": "auto-resume",
            "savedAt": now_iso(),
            "sceneId": "",
            "sceneName": "未命名场景",
            "blockIndex": 0,
        }
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

    def clean_count(raw_value) -> int:
        try:
            return max(0, int(raw_value or 0))
        except Exception:
            return 0

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
        "endingCompletionCount": clean_count(source.get("endingCompletionCount")),
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


def load_project_runtime_settings(project_id: str, project: dict | None = None) -> dict:
    project_defaults = build_project_default_runtime_player_settings(project)
    settings_path = get_project_settings_file_path(project_id)
    if not settings_path.is_file():
        return project_defaults
    try:
        payload = json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception:
        return project_defaults
    return sanitize_runtime_player_settings({**project_defaults, **payload})


def write_project_runtime_settings(project_id: str, settings: dict) -> Path:
    settings_dir = get_runtime_settings_dir()
    settings_dir.mkdir(parents=True, exist_ok=True)
    settings_path = get_project_settings_file_path(project_id)
    safe_settings = sanitize_runtime_player_settings(settings)
    settings_path.write_text(json.dumps(safe_settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return settings_path
