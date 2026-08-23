from __future__ import annotations

import json
import os
import platform
import sys
import tempfile
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

try:
    from .runtime_voice_mixer import get_safe_voice_profile_id
except ImportError:  # pragma: no cover - exported native packages import from the same directory.
    from runtime_voice_mixer import get_safe_voice_profile_id

try:
    from .runtime_save_slots import normalize_formal_save_slots
except ImportError:  # pragma: no cover - exported native packages import from the same directory.
    from runtime_save_slots import normalize_formal_save_slots


SAVE_ROOT_DIR_NAME = ".canvasia-engine"
SAVE_SUBDIR_NAME = "native-runtime-saves"
SETTINGS_SUBDIR_NAME = "native-runtime-settings"
PROGRESS_SUBDIR_NAME = "native-runtime-progress"
PROFILE_SUBDIR_NAME = "native-runtime-profiles"
PERSISTENT_VARIABLES_SUBDIR_NAME = "native-runtime-persistent-variables"
AUTO_RESUME_SUBDIR_NAME = "native-runtime-autoresume"
LOG_SUBDIR_NAME = "native-runtime-logs"
SCREENSHOT_SUBDIR_NAME = "native-runtime-screenshots"
READ_TEXT_KEY_LIMIT = 20000
SNAPSHOT_TEXT_HISTORY_LIMIT = 120
CRASH_LOG_FILE_PREFIX = "runtime-crash-"
CRASH_FEEDBACK_LOG_LIMIT = 8
RUNTIME_JSON_BACKUP_SUFFIX = ".bak"
RUNTIME_STORAGE_RECOVERY_EVENT_LIMIT = 32
_runtime_storage_recovery_events: list[dict] = []
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


def get_runtime_persistent_variables_dir() -> Path:
    return Path.home() / SAVE_ROOT_DIR_NAME / PERSISTENT_VARIABLES_SUBDIR_NAME


def get_runtime_auto_resume_dir() -> Path:
    return Path.home() / SAVE_ROOT_DIR_NAME / AUTO_RESUME_SUBDIR_NAME


def get_runtime_log_dir() -> Path:
    return Path.home() / SAVE_ROOT_DIR_NAME / LOG_SUBDIR_NAME


def get_runtime_screenshot_dir() -> Path:
    return Path.home() / SAVE_ROOT_DIR_NAME / SCREENSHOT_SUBDIR_NAME


def get_runtime_json_backup_path(path: Path) -> Path:
    return path.with_name(f"{path.name}{RUNTIME_JSON_BACKUP_SUFFIX}")


def _sync_runtime_storage_dir(path: Path) -> None:
    try:
        directory_fd = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(directory_fd)
    except OSError:
        pass
    finally:
        os.close(directory_fd)


def _write_runtime_text_atomically(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
            temporary_path = Path(handle.name)
        os.replace(temporary_path, path)
        temporary_path = None
        _sync_runtime_storage_dir(path.parent)
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def _read_runtime_json_candidate(path: Path, expected_type=None) -> tuple[bool, object | None]:
    if not path.is_file():
        return False, None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return False, None
    if expected_type is not None and not isinstance(payload, expected_type):
        return False, None
    return True, payload


def _record_runtime_storage_recovery(path: Path, label: str) -> None:
    _runtime_storage_recovery_events.append(
        {
            "label": str(label or "运行数据"),
            "filename": path.name,
            "recoveredAt": now_iso(),
        }
    )
    del _runtime_storage_recovery_events[:-RUNTIME_STORAGE_RECOVERY_EVENT_LIMIT]


def consume_runtime_storage_recovery_events() -> list[dict]:
    events = [dict(event) for event in _runtime_storage_recovery_events]
    _runtime_storage_recovery_events.clear()
    return events


def write_runtime_json_file(path: Path, payload: object) -> Path:
    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    expected_type = type(payload)
    previous_is_valid, previous_payload = _read_runtime_json_candidate(path, expected_type)
    backup_path = get_runtime_json_backup_path(path)
    backup_is_valid, _backup_payload = _read_runtime_json_candidate(backup_path, expected_type)

    _write_runtime_text_atomically(path, serialized)

    backup_payload = previous_payload if previous_is_valid else payload
    if previous_is_valid or not backup_is_valid:
        try:
            backup_text = json.dumps(backup_payload, ensure_ascii=False, indent=2) + "\n"
            _write_runtime_text_atomically(backup_path, backup_text)
        except (OSError, TypeError, ValueError):
            # The primary replacement already completed atomically. A backup failure
            # must not turn a successful save into an apparent data-loss failure.
            pass
    return path


def read_runtime_json_file(
    path: Path,
    fallback: object = None,
    *,
    expected_type=None,
    recovery_label: str = "运行数据",
):
    primary_is_valid, primary_payload = _read_runtime_json_candidate(path, expected_type)
    if primary_is_valid:
        return primary_payload

    backup_path = get_runtime_json_backup_path(path)
    backup_is_valid, backup_payload = _read_runtime_json_candidate(backup_path, expected_type)
    if not backup_is_valid:
        return fallback

    try:
        write_runtime_json_file(path, backup_payload)
    except (OSError, TypeError, ValueError):
        pass
    _record_runtime_storage_recovery(path, recovery_label)
    return backup_payload


def remove_runtime_json_file(path: Path) -> Path:
    # Remove the backup first so a partially failed clear cannot resurrect data.
    for target_path in (get_runtime_json_backup_path(path), path):
        try:
            target_path.unlink()
        except FileNotFoundError:
            pass
    return path


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


def redact_local_home_path(value: object) -> str:
    text = str(value or "").strip()
    home_path = str(Path.home())
    if home_path and home_path != "/":
        text = text.replace(home_path, "~")
    return text


def list_runtime_crash_logs(limit: int = CRASH_FEEDBACK_LOG_LIMIT) -> list[Path]:
    log_dir = get_runtime_log_dir()
    if not log_dir.is_dir():
        return []
    logs = [path for path in log_dir.glob(f"{CRASH_LOG_FILE_PREFIX}*.log") if path.is_file()]
    logs.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return logs[: max(0, int(limit or 0))]


def read_runtime_crash_log_summary(log_path: Path) -> dict:
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
    except Exception as error:
        return {
            "path": redact_local_home_path(log_path),
            "status": "unreadable",
            "message": f"日志无法读取：{type(error).__name__}: {error}",
        }
    lines = text.splitlines()

    def get_prefixed(prefix: str) -> str:
        for line in lines:
            if line.startswith(prefix):
                return redact_local_home_path(line[len(prefix) :].strip())
        return ""

    error_line = ""
    for index, line in enumerate(lines):
        if line.strip() == "Error:":
            for candidate in lines[index + 1 :]:
                candidate = candidate.strip()
                if candidate:
                    error_line = redact_local_home_path(candidate)
                    break
            break
    try:
        stat = log_path.stat()
        size_bytes = stat.st_size
        modified_at = datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds")
    except OSError:
        size_bytes = 0
        modified_at = ""
    return {
        "path": redact_local_home_path(log_path),
        "status": "readable",
        "time": get_prefixed("Time:"),
        "context": get_prefixed("Context:"),
        "gameData": get_prefixed("Game data:"),
        "python": get_prefixed("Python:"),
        "platform": get_prefixed("Platform:"),
        "frozen": get_prefixed("Frozen:"),
        "error": error_line,
        "sizeBytes": size_bytes,
        "modifiedAt": modified_at,
    }


def build_runtime_crash_feedback_report(
    game_data_path: Path | None = None,
    *,
    include_logs: bool = True,
    limit: int = CRASH_FEEDBACK_LOG_LIMIT,
) -> dict:
    if game_data_path is not None and include_logs:
        target_game_data = redact_local_home_path(game_data_path)
    elif game_data_path is not None:
        target_game_data = Path(game_data_path).name
    else:
        target_game_data = ""
    logs = [read_runtime_crash_log_summary(path) for path in list_runtime_crash_logs(limit) if include_logs]
    latest_log = logs[0] if logs else None
    if include_logs and logs:
        status = "has_recent_crashes"
        headline = "检测到本机最近的原生 Runtime 崩溃日志。"
    elif include_logs:
        status = "no_crash_logs"
        headline = "本机还没有记录到原生 Runtime 崩溃日志。"
    else:
        status = "template"
        headline = "这是随导出包提供的崩溃反馈模板，不包含作者本机日志。"
    recommendations = [
        "如果 Runtime 打不开，先把这个反馈报告发给作者或维护者。",
        "默认反馈报告只包含摘要；需要深度排查时，再从日志目录中选择对应原始 .log 文件发送。",
        "分享原始日志前建议确认其中没有不想公开的本机路径或环境信息。",
    ]
    return {
        "formatVersion": 1,
        "generatedAt": now_iso(),
        "status": status,
        "headline": headline,
        "gameData": target_game_data,
        "logDir": redact_local_home_path(get_runtime_log_dir()),
        "summary": {
            "logCount": len(logs),
            "latestTime": latest_log.get("time") if isinstance(latest_log, dict) else "",
            "latestContext": latest_log.get("context") if isinstance(latest_log, dict) else "",
            "latestError": latest_log.get("error") if isinstance(latest_log, dict) else "",
            "includesLocalLogs": bool(include_logs),
        },
        "logs": logs,
        "recommendations": recommendations,
    }


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


def get_project_persistent_variables_file_path(project_id: str) -> Path:
    return get_runtime_persistent_variables_dir() / make_project_save_filename(project_id)


def get_project_auto_resume_file_path(project_id: str) -> Path:
    return get_runtime_auto_resume_dir() / make_project_save_filename(project_id)


def load_project_save_store(project_id: str, slot_count: int) -> dict:
    save_path = get_project_save_file_path(project_id)
    empty_store = {"quickSave": None, "formalSlots": [None] * slot_count}
    payload = read_runtime_json_file(
        save_path,
        empty_store,
        expected_type=dict,
        recovery_label="正式存档",
    )

    formal_slots = normalize_formal_save_slots(payload.get("formalSlots"), slot_count)
    return {
        "quickSave": payload.get("quickSave"),
        "formalSlots": formal_slots,
    }


def write_project_save_store(project_id: str, save_store: dict) -> Path:
    save_path = get_project_save_file_path(project_id)
    return write_runtime_json_file(save_path, save_store)


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
    payload = read_runtime_json_file(
        profile_path,
        DEFAULT_PLAYER_PROFILE,
        expected_type=dict,
        recovery_label="玩家档案",
    )
    return sanitize_player_profile(payload)


def write_project_player_profile(project_id: str, profile: dict) -> Path:
    profile_path = get_project_profile_file_path(project_id)
    safe_profile = sanitize_player_profile(profile)
    return write_runtime_json_file(profile_path, safe_profile)


def load_project_persistent_variables(project_id: str) -> dict:
    persistent_path = get_project_persistent_variables_file_path(project_id)
    return read_runtime_json_file(
        persistent_path,
        {},
        expected_type=dict,
        recovery_label="跨周目记忆",
    )


def write_project_persistent_variables(project_id: str, payload: dict) -> Path:
    persistent_path = get_project_persistent_variables_file_path(project_id)
    safe_payload = payload if isinstance(payload, dict) else {}
    return write_runtime_json_file(persistent_path, safe_payload)


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
        try:
            voice_volume = max(0, min(100, int(round(float(item.get("voiceVolume", 100))))))
        except Exception:
            voice_volume = 100
        key = str(item.get("key") or "").strip()[:180]
        result.append(
            {
                "key": key,
                "sceneName": str(item.get("sceneName") or "").strip()[:80],
                "speakerName": str(item.get("speakerName") or "旁白").strip()[:80],
                "text": text[:2000],
                "blockType": str(item.get("blockType") or "").strip()[:40],
                "voiceAssetId": str(item.get("voiceAssetId") or "").strip()[:120],
                "voiceVolume": voice_volume,
                "voiceProfileId": get_safe_voice_profile_id(item.get("voiceProfileId")),
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
    payload = read_runtime_json_file(
        auto_resume_path,
        None,
        expected_type=dict,
        recovery_label="续玩记录",
    )
    return sanitize_auto_resume_snapshot(payload)


def write_project_auto_resume(project_id: str, snapshot: dict) -> Path:
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
    return write_runtime_json_file(auto_resume_path, safe_snapshot)


def clear_project_auto_resume(project_id: str) -> Path:
    auto_resume_path = get_project_auto_resume_file_path(project_id)
    return remove_runtime_json_file(auto_resume_path)


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
        "achievementUnlocked": clean_id_list(source.get("achievementUnlocked")),
        "readTextKeys": clean_id_list(source.get("readTextKeys"), READ_TEXT_KEY_LIMIT),
        "endingCompletionCount": clean_count(source.get("endingCompletionCount")),
        "endingLastCompletedAt": str(source.get("endingLastCompletedAt") or "").strip() or None,
    }


def load_project_archive_progress(project_id: str) -> dict:
    progress_path = get_project_progress_file_path(project_id)
    payload = read_runtime_json_file(
        progress_path,
        {},
        expected_type=dict,
        recovery_label="收藏与已读进度",
    )
    return sanitize_archive_progress(payload)


def write_project_archive_progress(project_id: str, progress: dict) -> Path:
    progress_path = get_project_progress_file_path(project_id)
    safe_payload = sanitize_archive_progress(progress)
    return write_runtime_json_file(progress_path, safe_payload)


def load_project_runtime_settings(project_id: str, project: dict | None = None) -> dict:
    project_defaults = build_project_default_runtime_player_settings(project)
    settings_path = get_project_settings_file_path(project_id)
    payload = read_runtime_json_file(
        settings_path,
        {},
        expected_type=dict,
        recovery_label="体验设置",
    )
    return sanitize_runtime_player_settings({**project_defaults, **payload})


def write_project_runtime_settings(project_id: str, settings: dict) -> Path:
    settings_path = get_project_settings_file_path(project_id)
    safe_settings = sanitize_runtime_player_settings(settings)
    return write_runtime_json_file(settings_path, safe_settings)
