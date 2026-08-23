from __future__ import annotations

import hashlib
import hmac
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Callable

try:
    from .runtime_persistent_variables import (
        build_persistent_runtime_variable_store,
        collect_persistent_runtime_variable_state,
        merge_persistent_runtime_variable_state,
        sanitize_persistent_runtime_variable_state,
    )
    from .runtime_player_settings import sanitize_runtime_player_settings
    from .runtime_save_thumbnails import prune_orphaned_save_thumbnails
    from .runtime_storage import (
        READ_TEXT_KEY_LIMIT,
        clear_project_auto_resume,
        load_project_archive_progress,
        load_project_auto_resume,
        load_project_persistent_variables,
        load_project_player_profile,
        load_project_runtime_settings,
        load_project_save_store,
        now_iso,
        sanitize_archive_progress,
        sanitize_player_profile,
        write_project_archive_progress,
        write_project_auto_resume,
        write_project_persistent_variables,
        write_project_player_profile,
        write_project_runtime_settings,
        write_project_save_store,
    )
except ImportError:  # pragma: no cover - exported native packages import from the same directory.
    from runtime_persistent_variables import (
        build_persistent_runtime_variable_store,
        collect_persistent_runtime_variable_state,
        merge_persistent_runtime_variable_state,
        sanitize_persistent_runtime_variable_state,
    )
    from runtime_player_settings import sanitize_runtime_player_settings
    from runtime_save_thumbnails import prune_orphaned_save_thumbnails
    from runtime_storage import (
        READ_TEXT_KEY_LIMIT,
        clear_project_auto_resume,
        load_project_archive_progress,
        load_project_auto_resume,
        load_project_persistent_variables,
        load_project_player_profile,
        load_project_runtime_settings,
        load_project_save_store,
        now_iso,
        sanitize_archive_progress,
        sanitize_player_profile,
        write_project_archive_progress,
        write_project_auto_resume,
        write_project_persistent_variables,
        write_project_player_profile,
        write_project_runtime_settings,
        write_project_save_store,
    )


SAVE_VAULT_FORMAT = "canvasia-native-save-vault"
SAVE_VAULT_FORMAT_VERSION = 1
SAVE_VAULT_ENGINE = "Canvasia Engine"
SAVE_VAULT_EXTENSION = ".canvasia-save"
SAVE_VAULT_SUBDIR_NAME = "native-runtime-vault"
SAVE_VAULT_MAX_BYTES = 12_000_000
SAVE_VAULT_LIST_LIMIT = 12
SAVE_VAULT_RECORD_NAMES = (
    "saveStore",
    "autoResume",
    "archiveProgress",
    "playerProfile",
    "persistentVariables",
    "runtimeSettings",
)
SAVE_VAULT_TOP_LEVEL_FIELDS = {
    "format",
    "formatVersion",
    "engine",
    "exportedAt",
    "kind",
    "project",
    "records",
    "integrity",
}
SAVE_VAULT_PROJECT_FIELDS = {"projectId", "title", "releaseVersion"}
SAVE_VAULT_MISSING_MTIME = -1.0


def _safe_text(value: object, limit: int = 240) -> str:
    return str(value or "").strip()[: max(0, int(limit))]


def _safe_project_id(value: object) -> str:
    source = _safe_text(value, 160)
    safe = "".join(character if character.isalnum() or character in {"-", "_"} else "_" for character in source)
    return safe.strip("_") or "untitled_project"


def _clone_json(value: object) -> object:
    return json.loads(json.dumps(value, ensure_ascii=False))


def _with_alpha(color: tuple[int, int, int], alpha: int) -> tuple[int, int, int, int]:
    return (*color[:3], max(0, min(255, int(alpha))))


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _normalize_exported_at(value: object | None = None) -> str:
    if isinstance(value, datetime):
        candidate = value
    elif value:
        try:
            candidate = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            candidate = datetime.now().astimezone()
    else:
        candidate = datetime.now().astimezone()
    if candidate.tzinfo is None:
        candidate = candidate.astimezone()
    return candidate.isoformat(timespec="seconds")


def _integrity_source(bundle: dict) -> dict:
    return {
        "format": bundle.get("format"),
        "formatVersion": bundle.get("formatVersion"),
        "engine": bundle.get("engine"),
        "exportedAt": bundle.get("exportedAt"),
        "kind": bundle.get("kind"),
        "project": bundle.get("project"),
        "records": bundle.get("records"),
    }


def build_save_vault_integrity(bundle: dict) -> str:
    digest = hashlib.sha256(_canonical_json(_integrity_source(bundle)).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def build_save_vault_summary(bundle: dict) -> dict:
    records = bundle.get("records") if isinstance(bundle.get("records"), dict) else {}
    save_store = records.get("saveStore") if isinstance(records.get("saveStore"), dict) else {}
    formal_slots = save_store.get("formalSlots") if isinstance(save_store.get("formalSlots"), list) else []
    archive = records.get("archiveProgress") if isinstance(records.get("archiveProgress"), dict) else {}
    persistent = records.get("persistentVariables") if isinstance(records.get("persistentVariables"), dict) else {}
    persistent_values = persistent.get("values") if isinstance(persistent.get("values"), dict) else persistent
    unlock_keys = (
        "chapterReplayUnlocked",
        "bgmUnlocked",
        "cgUnlocked",
        "locationUnlocked",
        "characterUnlocked",
        "narrationUnlocked",
        "relationUnlocked",
        "voiceReplayUnlocked",
        "endingUnlocked",
        "achievementUnlocked",
    )
    unlocked_count = sum(
        len(archive.get(key))
        for key in unlock_keys
        if isinstance(archive.get(key), list)
    )
    return {
        "projectId": _safe_text((bundle.get("project") or {}).get("projectId"), 160),
        "projectTitle": _safe_text((bundle.get("project") or {}).get("title"), 240),
        "releaseVersion": _safe_text((bundle.get("project") or {}).get("releaseVersion"), 120),
        "exportedAt": _safe_text(bundle.get("exportedAt"), 80),
        "kind": _safe_text(bundle.get("kind"), 40),
        "formalSaveCount": sum(1 for slot in formal_slots if isinstance(slot, dict)),
        "formalSaveSlotCount": len(formal_slots),
        "hasQuickSave": isinstance(save_store.get("quickSave"), dict),
        "hasAutoResume": isinstance(records.get("autoResume"), dict),
        "unlockedCount": unlocked_count,
        "persistentVariableCount": len(persistent_values),
    }


def _failure(code: str, message: str, **details) -> dict:
    return {"ok": False, "code": code, "message": message, "details": details}


def build_save_vault_bundle(
    project: dict | None,
    records: dict | None,
    *,
    exported_at: object | None = None,
    kind: str = "manual",
) -> dict:
    project_source = project if isinstance(project, dict) else {}
    record_source = records if isinstance(records, dict) else {}
    missing_records = [name for name in SAVE_VAULT_RECORD_NAMES if name not in record_source]
    if missing_records:
        raise ValueError(f"Save vault records are incomplete: {', '.join(missing_records)}")
    safe_kind = str(kind or "manual").strip().lower()
    if safe_kind not in {"manual", "pre-restore"}:
        raise ValueError(f"Unsupported save vault kind: {kind}")
    safe_records = {name: _clone_json(record_source.get(name)) for name in SAVE_VAULT_RECORD_NAMES}
    bundle = {
        "format": SAVE_VAULT_FORMAT,
        "formatVersion": SAVE_VAULT_FORMAT_VERSION,
        "engine": SAVE_VAULT_ENGINE,
        "exportedAt": _normalize_exported_at(exported_at),
        "kind": safe_kind,
        "project": {
            "projectId": _safe_text(project_source.get("projectId"), 160) or "untitled_project",
            "title": _safe_text(project_source.get("title") or "未命名项目", 240),
            "releaseVersion": _safe_text(project_source.get("releaseVersion"), 120),
        },
        "records": safe_records,
    }
    bundle["integrity"] = build_save_vault_integrity(bundle)
    serialized = json.dumps(bundle, ensure_ascii=False)
    if len(serialized.encode("utf-8")) > SAVE_VAULT_MAX_BYTES:
        raise ValueError("玩家数据超过保险箱单文件安全上限。")
    return bundle


def validate_save_vault_bundle(
    source: object,
    *,
    expected_project_id: object | None = None,
    max_bytes: int = SAVE_VAULT_MAX_BYTES,
) -> dict:
    if not isinstance(source, dict) or set(source) != SAVE_VAULT_TOP_LEVEL_FIELDS:
        return _failure("invalid_root", "这不是可识别的 Canvasia 原生存档备份。")
    try:
        serialized = json.dumps(source, ensure_ascii=False)
    except (TypeError, ValueError):
        return _failure("not_serializable", "备份内容无法读取。")
    if len(serialized.encode("utf-8")) > max(1, int(max_bytes)):
        return _failure("too_large", "备份文件超过安全大小限制。")
    if source.get("format") != SAVE_VAULT_FORMAT:
        return _failure("wrong_format", "文件格式不属于 Canvasia 原生玩家数据保险箱。")
    if source.get("formatVersion") != SAVE_VAULT_FORMAT_VERSION:
        return _failure("unsupported_version", "备份版本暂不受当前 Runtime 支持。")
    if source.get("engine") != SAVE_VAULT_ENGINE:
        return _failure("wrong_engine", "备份来源无法确认。")
    if str(source.get("kind") or "") not in {"manual", "pre-restore"}:
        return _failure("invalid_kind", "备份用途标记无法识别。")
    try:
        datetime.fromisoformat(str(source.get("exportedAt") or "").replace("Z", "+00:00"))
    except ValueError:
        return _failure("invalid_export_time", "备份缺少有效的导出时间。")
    project = source.get("project")
    if not isinstance(project, dict) or set(project) != SAVE_VAULT_PROJECT_FIELDS:
        return _failure("invalid_project", "备份中的项目信息不完整。")
    project_id = _safe_text(project.get("projectId"), 160)
    if not project_id:
        return _failure("invalid_project", "备份中没有项目标识。")
    expected_id = _safe_text(expected_project_id, 160)
    if expected_id and project_id != expected_id:
        return _failure(
            "project_mismatch",
            "这个备份属于其他作品，已阻止覆盖当前游戏数据。",
            expectedProjectId=expected_id,
            backupProjectId=project_id,
        )
    records = source.get("records")
    if not isinstance(records, dict) or set(records) != set(SAVE_VAULT_RECORD_NAMES):
        return _failure("record_set_mismatch", "备份记录集合与当前 Runtime 不匹配。")
    try:
        safe_records = {name: _clone_json(records.get(name)) for name in SAVE_VAULT_RECORD_NAMES}
    except (TypeError, ValueError):
        return _failure("invalid_record", "备份记录包含无法读取的数据。")
    normalized = {
        "format": SAVE_VAULT_FORMAT,
        "formatVersion": SAVE_VAULT_FORMAT_VERSION,
        "engine": SAVE_VAULT_ENGINE,
        "exportedAt": _normalize_exported_at(source.get("exportedAt")),
        "kind": str(source.get("kind")),
        "project": {
            "projectId": project_id,
            "title": _safe_text(project.get("title") or "未命名项目", 240),
            "releaseVersion": _safe_text(project.get("releaseVersion"), 120),
        },
        "records": safe_records,
        "integrity": _safe_text(source.get("integrity"), 100),
    }
    if not hmac.compare_digest(normalized["integrity"], build_save_vault_integrity(normalized)):
        return _failure("integrity_mismatch", "备份完整性校验失败，文件可能不完整或已被改写。")
    return {
        "ok": True,
        "code": "ready",
        "message": "备份已通过格式、项目和完整性校验。",
        "bundle": normalized,
        "summary": build_save_vault_summary(normalized),
    }


def get_save_vault_directory(project_id: object, root_dir: Path | None = None) -> Path:
    root = Path(root_dir) if root_dir is not None else Path.home() / ".canvasia-engine"
    return root / SAVE_VAULT_SUBDIR_NAME / _safe_project_id(project_id)


def build_save_vault_filename(project_id: object, exported_at: object | None = None, *, kind: str = "manual") -> str:
    timestamp = _normalize_exported_at(exported_at)
    safe_timestamp = "".join(character for character in timestamp if character.isdigit())[:14]
    kind_suffix = "-before-restore" if kind == "pre-restore" else ""
    return f"{_safe_project_id(project_id)}-{safe_timestamp}{kind_suffix}{SAVE_VAULT_EXTENSION}"


def _write_text_atomically(path: Path, text: str) -> None:
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
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink()
            except FileNotFoundError:
                pass


def write_save_vault_bundle(
    project: dict | None,
    records: dict | None,
    *,
    root_dir: Path | None = None,
    exported_at: object | None = None,
    kind: str = "manual",
) -> tuple[Path, dict]:
    bundle = build_save_vault_bundle(project, records, exported_at=exported_at, kind=kind)
    project_id = bundle["project"]["projectId"]
    target_dir = get_save_vault_directory(project_id, root_dir)
    target_path = target_dir / build_save_vault_filename(project_id, bundle["exportedAt"], kind=kind)
    if target_path.exists():
        suffix = datetime.now().strftime("%f")
        target_path = target_path.with_name(f"{target_path.stem}-{suffix}{target_path.suffix}")
    _write_text_atomically(target_path, json.dumps(bundle, ensure_ascii=False, indent=2) + "\n")
    return target_path, bundle


def read_save_vault_file(path: Path, *, expected_project_id: object | None = None) -> dict:
    target = Path(path)
    try:
        size_bytes = target.stat().st_size
    except OSError as error:
        return _failure("unreadable", f"无法读取备份文件：{error}", path=str(target))
    if size_bytes > SAVE_VAULT_MAX_BYTES:
        return _failure("too_large", "备份文件超过安全大小限制。", path=str(target), sizeBytes=size_bytes)
    try:
        source = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return _failure("invalid_json", "备份文件不是完整的 UTF-8 JSON。", path=str(target), sizeBytes=size_bytes)
    result = validate_save_vault_bundle(source, expected_project_id=expected_project_id)
    result["path"] = target
    result["sizeBytes"] = size_bytes
    return result


def _save_vault_sort_key(path: Path) -> tuple[float, str]:
    try:
        modified_at = path.stat().st_mtime
    except OSError:
        # A backup may be moved by Finder between directory discovery and
        # sorting. Keep refresh non-fatal; the later read reports its state.
        modified_at = SAVE_VAULT_MISSING_MTIME
    return modified_at, path.name


def list_save_vault_entries(
    project_id: object,
    *,
    root_dir: Path | None = None,
    limit: int = SAVE_VAULT_LIST_LIMIT,
) -> list[dict]:
    directory = get_save_vault_directory(project_id, root_dir)
    if not directory.is_dir():
        return []
    paths = [path for path in directory.glob(f"*{SAVE_VAULT_EXTENSION}") if path.is_file()]
    paths.sort(key=_save_vault_sort_key, reverse=True)
    entries = []
    for path in paths[: max(0, int(limit))]:
        result = read_save_vault_file(path, expected_project_id=project_id)
        entries.append(
            {
                "path": path,
                "filename": path.name,
                "ok": bool(result.get("ok")),
                "code": str(result.get("code") or "invalid"),
                "message": str(result.get("message") or "备份状态未知。"),
                "summary": dict(result.get("summary") or {}),
                "sizeBytes": int(result.get("sizeBytes") or 0),
            }
        )
    return entries


def restore_save_vault_records(
    source: object,
    *,
    expected_project_id: object,
    current_records: dict,
    write_record: Callable[[str, object], None],
) -> dict:
    validation = validate_save_vault_bundle(source, expected_project_id=expected_project_id)
    if not validation.get("ok"):
        return validation
    missing_current = [name for name in SAVE_VAULT_RECORD_NAMES if name not in current_records]
    if missing_current:
        return _failure("current_state_incomplete", "当前玩家数据无法形成完整回滚点。", missing=missing_current)
    previous = {name: _clone_json(current_records.get(name)) for name in SAVE_VAULT_RECORD_NAMES}
    target_records = validation["bundle"]["records"]
    applied: list[str] = []
    try:
        for name in SAVE_VAULT_RECORD_NAMES:
            applied.append(name)
            write_record(name, _clone_json(target_records.get(name)))
    except Exception as error:
        rollback_errors = []
        for name in reversed(applied):
            try:
                previous_value = _clone_json(previous.get(name))
                write_record(name, previous_value)
                # Native storage rotates the old primary into `.bak`. Repeating
                # the idempotent write restores both generations to the same
                # pre-transaction value instead of leaving a partial target in
                # the automatic recovery slot.
                write_record(name, _clone_json(previous_value))
            except Exception as rollback_error:
                rollback_errors.append(f"{name}: {type(rollback_error).__name__}")
        return _failure(
            "restore_failed",
            "恢复没有完成，已尝试回滚到操作前状态。",
            failedRecord=applied[-1] if applied else "",
            error=f"{type(error).__name__}: {error}",
            rollbackComplete=not rollback_errors,
            rollbackErrors=rollback_errors,
        )
    return {
        "ok": True,
        "code": "restored",
        "message": "玩家数据已完整恢复。",
        "bundle": validation["bundle"],
        "summary": validation["summary"],
    }


def build_runtime_save_vault_records(runtime) -> dict:
    archive_progress = sanitize_archive_progress(
        {
            **runtime.archive_progress,
            "readTextKeys": list(runtime.read_text_key_order[-READ_TEXT_KEY_LIMIT:]),
        }
    )
    return {
        "saveStore": runtime.save_store,
        "autoResume": runtime.auto_resume_snapshot,
        "archiveProgress": archive_progress,
        "playerProfile": sanitize_player_profile(runtime.player_profile),
        "persistentVariables": build_persistent_runtime_variable_store(
            collect_persistent_runtime_variable_state(runtime.variable_state, runtime.variables),
            runtime.variables,
            updated_at=now_iso(),
        ),
        "runtimeSettings": sanitize_runtime_player_settings(runtime.runtime_settings),
    }


def build_runtime_save_vault_project_identity(runtime) -> dict:
    return {
        "projectId": runtime.project_id,
        "title": str(runtime.project.get("title") or "未命名项目"),
        "releaseVersion": str(runtime.project.get("releaseVersion") or ""),
    }


def cancel_runtime_save_vault_restore_confirmation(runtime) -> None:
    runtime.save_vault_restore_armed_path = ""
    runtime.save_vault_restore_armed_until_ms = 0


def refresh_runtime_save_vault_entries(runtime, *, announce: bool = True) -> None:
    selected_path = ""
    if runtime.save_vault_entries and runtime.save_vault_index < len(runtime.save_vault_entries):
        selected_path = str(runtime.save_vault_entries[runtime.save_vault_index].get("path") or "")
    runtime.save_vault_entries = list_save_vault_entries(runtime.project_id)
    runtime.save_vault_index = 0
    if selected_path:
        for index, entry in enumerate(runtime.save_vault_entries):
            if str(entry.get("path") or "") == selected_path:
                runtime.save_vault_index = index
                break
    cancel_runtime_save_vault_restore_confirmation(runtime)
    if announce:
        runtime.status_message = f"数据保险箱已刷新：{len(runtime.save_vault_entries)} 份备份。"


def open_runtime_save_vault_overlay(runtime) -> None:
    runtime.overlay_mode = "save-vault"
    runtime.save_vault_index = 0
    runtime.save_vault_entries = list_save_vault_entries(runtime.project_id)
    cancel_runtime_save_vault_restore_confirmation(runtime)
    runtime.status_message = f"数据保险箱已打开：{len(runtime.save_vault_entries)} 份备份。"


def create_runtime_save_vault_backup(runtime, *, kind: str = "manual") -> Path | None:
    try:
        path, _bundle = write_save_vault_bundle(
            build_runtime_save_vault_project_identity(runtime),
            build_runtime_save_vault_records(runtime),
            kind=kind,
        )
    except (OSError, TypeError, ValueError) as error:
        runtime.status_message = f"数据备份创建失败，原有存档未受影响：{type(error).__name__}"
        return None
    runtime.save_vault_entries = list_save_vault_entries(runtime.project_id)
    runtime.save_vault_index = next(
        (
            index
            for index, entry in enumerate(runtime.save_vault_entries)
            if str(entry.get("path") or "") == str(path)
        ),
        0,
    )
    cancel_runtime_save_vault_restore_confirmation(runtime)
    label = "恢复前安全点" if kind == "pre-restore" else "玩家数据备份"
    runtime.status_message = f"{label}已创建：{path.name}"
    return path


def write_runtime_save_vault_record(runtime, name: str, value: object) -> None:
    if name not in SAVE_VAULT_RECORD_NAMES:
        raise ValueError(f"Unsupported save vault record: {name}")
    if name == "saveStore":
        write_project_save_store(runtime.project_id, value if isinstance(value, dict) else {})
    elif name == "autoResume":
        if isinstance(value, dict):
            write_project_auto_resume(runtime.project_id, value)
        else:
            clear_project_auto_resume(runtime.project_id)
    elif name == "archiveProgress":
        write_project_archive_progress(runtime.project_id, value if isinstance(value, dict) else {})
    elif name == "playerProfile":
        write_project_player_profile(runtime.project_id, value if isinstance(value, dict) else {})
    elif name == "persistentVariables":
        write_project_persistent_variables(runtime.project_id, value if isinstance(value, dict) else {})
    elif name == "runtimeSettings":
        write_project_runtime_settings(runtime.project_id, value if isinstance(value, dict) else {})
    else:  # pragma: no cover - kept as a guard when the record registry grows.
        raise ValueError(f"Unimplemented save vault record: {name}")


def reload_runtime_save_vault_records(runtime) -> None:
    runtime.save_store = load_project_save_store(runtime.project_id, runtime.formal_save_slot_count)
    runtime.auto_resume_snapshot = load_project_auto_resume(runtime.project_id)
    runtime.archive_progress = load_project_archive_progress(runtime.project_id)
    runtime.read_text_key_order = list(runtime.archive_progress.get("readTextKeys") or [])[-READ_TEXT_KEY_LIMIT:]
    runtime.read_text_keys = set(runtime.read_text_key_order)
    runtime.player_profile = load_project_player_profile(runtime.project_id)
    runtime.persistent_variable_state = sanitize_persistent_runtime_variable_state(
        load_project_persistent_variables(runtime.project_id),
        runtime.variables,
    )
    runtime.variable_state = merge_persistent_runtime_variable_state(
        runtime.variable_state,
        runtime.variables,
        runtime.persistent_variable_state,
    )
    runtime.runtime_settings = load_project_runtime_settings(runtime.project_id, runtime.project)
    runtime.apply_runtime_language_setting()
    runtime.apply_runtime_settings()
    runtime.auto_resume_write_enabled = runtime.auto_resume_snapshot is None
    prune_orphaned_save_thumbnails(runtime.save_store, runtime.project_id)


def restore_selected_runtime_save_vault(runtime) -> bool:
    if not runtime.save_vault_entries:
        runtime.status_message = "当前没有可以恢复的玩家数据备份。"
        return False
    runtime.save_vault_index = max(0, min(len(runtime.save_vault_entries) - 1, runtime.save_vault_index))
    selected = runtime.save_vault_entries[runtime.save_vault_index]
    if not selected.get("ok"):
        runtime.status_message = str(selected.get("message") or "所选备份没有通过完整性校验。")
        return False
    selected_path = Path(selected["path"])
    now_ms = runtime.pygame.time.get_ticks()
    if (
        runtime.save_vault_restore_armed_path != str(selected_path)
        or now_ms > runtime.save_vault_restore_armed_until_ms
    ):
        runtime.save_vault_restore_armed_path = str(selected_path)
        runtime.save_vault_restore_armed_until_ms = now_ms + 5000
        runtime.status_message = "已完成恢复预检；5 秒内再次选择“恢复所选”才会写入。"
        return False

    current_records = build_runtime_save_vault_records(runtime)
    safety_path = create_runtime_save_vault_backup(runtime, kind="pre-restore")
    if safety_path is None:
        runtime.status_message = "无法建立恢复前安全点，已取消恢复。"
        return False
    read_result = read_save_vault_file(selected_path, expected_project_id=runtime.project_id)
    if not read_result.get("ok"):
        runtime.status_message = str(read_result.get("message") or "备份在写入前校验失败，已取消恢复。")
        return False
    restore_result = restore_save_vault_records(
        read_result["bundle"],
        expected_project_id=runtime.project_id,
        current_records=current_records,
        write_record=lambda name, value: write_runtime_save_vault_record(runtime, name, value),
    )
    if not restore_result.get("ok"):
        rollback_label = "已回滚" if restore_result.get("details", {}).get("rollbackComplete") else "回滚不完整"
        runtime.status_message = f"恢复失败（{rollback_label}），当前数据保险箱仍保留安全点。"
        cancel_runtime_save_vault_restore_confirmation(runtime)
        return False
    reload_runtime_save_vault_records(runtime)
    runtime.save_vault_entries = list_save_vault_entries(runtime.project_id)
    runtime.save_vault_index = 0
    cancel_runtime_save_vault_restore_confirmation(runtime)
    runtime.status_message = "玩家数据已恢复；当前画面保持不变，可从续玩或读档进入恢复进度。"
    return True


def render_save_vault_overlay(runtime) -> None:
    pygame = runtime.pygame
    palette = runtime.get_active_palette()
    entries = runtime.save_vault_entries
    panel = pygame.Rect(0, 0, min(runtime.width - 80, 1040), min(runtime.height - 80, 660))
    panel.center = (runtime.width // 2, runtime.height // 2)
    pygame.draw.rect(runtime.screen, (*palette["panel"], 246), panel, border_radius=30)
    pygame.draw.rect(runtime.screen, _with_alpha(palette["panelBorder"], 76), panel, 2, border_radius=30)
    runtime.draw_game_ui_panel_frame(panel, "system")

    runtime.screen.blit(runtime.font_title.render("数据保险箱", True, palette["text"]), (panel.left + 30, panel.top + 24))
    subtitle = "为存档、续玩、解锁、跨周目记忆和体验设置生成完整校验备份"
    runtime.screen.blit(runtime.font_ui.render(subtitle, True, palette["muted"]), (panel.left + 30, panel.top + 62))

    list_rect = pygame.Rect(panel.left + 30, panel.top + 104, min(480, panel.width // 2), panel.height - 190)
    detail_rect = pygame.Rect(list_rect.right + 18, list_rect.top, panel.right - list_rect.right - 48, list_rect.height)
    for rect in (list_rect, detail_rect):
        pygame.draw.rect(runtime.screen, _with_alpha(palette["accent"], 12), rect, border_radius=22)
        pygame.draw.rect(runtime.screen, _with_alpha(palette["panelBorder"], 38), rect, 1, border_radius=22)

    if not entries:
        runtime.blit_wrapped_text(
            runtime.font_body,
            "还没有手动备份。选择下方“创建新备份”，即可得到一份独立于正常存档的安全副本。",
            list_rect.inflate(-34, -34),
            palette["muted"],
            line_gap=8,
            max_lines=5,
        )
    else:
        row_height = 68
        runtime.save_vault_index = max(0, min(len(entries) - 1, runtime.save_vault_index))
        window_start = max(0, min(runtime.save_vault_index, len(entries) - 5))
        visible_entries = entries[window_start : window_start + 5]
        for row_index, entry in enumerate(visible_entries):
            index = window_start + row_index
            row = pygame.Rect(list_rect.left + 14, list_rect.top + 14 + row_index * (row_height + 8), list_rect.width - 28, row_height)
            active = index == runtime.save_vault_index
            tone = palette["accent"] if active else palette["panel"]
            pygame.draw.rect(runtime.screen, _with_alpha(tone, 64 if active else 34), row, border_radius=16)
            pygame.draw.rect(
                runtime.screen,
                _with_alpha(palette["accentAlt"] if active else palette["panelBorder"], 72 if active else 24),
                row,
                1,
                border_radius=16,
            )
            status = "完整" if entry.get("ok") else "不可恢复"
            title = str(entry.get("filename") or "未命名备份")
            runtime.screen.blit(runtime.font_ui.render(title[:45], True, palette["text"]), (row.left + 14, row.top + 10))
            meta_color = palette["accent"] if entry.get("ok") else (255, 150, 150)
            runtime.screen.blit(runtime.font_ui.render(status, True, meta_color), (row.left + 14, row.top + 38))
            runtime.overlay_hotspots.append({"kind": "save-vault-entry", "value": index, "rect": row})

    selected = entries[runtime.save_vault_index] if entries and runtime.save_vault_index < len(entries) else None
    restore_armed = bool(
        selected
        and str(selected.get("path") or "") == runtime.save_vault_restore_armed_path
        and pygame.time.get_ticks() <= runtime.save_vault_restore_armed_until_ms
    )
    if selected:
        summary = selected.get("summary") or {}
        health = "校验通过，可以恢复" if selected.get("ok") else str(selected.get("message") or "备份不可用")
        runtime.screen.blit(runtime.font_body.render(health[:28], True, palette["accent"] if selected.get("ok") else (255, 150, 150)), (detail_rect.left + 20, detail_rect.top + 20))
        lines = [
            f"创建时间：{summary.get('exportedAt') or '未知'}",
            f"正式存档：{summary.get('formalSaveCount', 0)} / {summary.get('formalSaveSlotCount', 0)}",
            f"快速存档：{'有' if summary.get('hasQuickSave') else '无'}",
            f"续玩记录：{'有' if summary.get('hasAutoResume') else '无'}",
            f"解锁记录：{summary.get('unlockedCount', 0)} 项",
            f"跨周目变量：{summary.get('persistentVariableCount', 0)} 项",
        ]
        for index, line in enumerate(lines):
            runtime.screen.blit(runtime.font_ui.render(line, True, palette["muted"]), (detail_rect.left + 20, detail_rect.top + 68 + index * 34))
        note = (
            "请再次确认恢复。写入前仍会自动创建当前状态安全点。"
            if restore_armed
            else "恢复前会自动保存当前状态；首次确认只会进入 5 秒待确认状态。"
        )
        note_color = (255, 203, 117) if restore_armed else palette["text"]
        runtime.blit_wrapped_text(runtime.font_ui, note, pygame.Rect(detail_rect.left + 20, detail_rect.bottom - 104, detail_rect.width - 40, 72), note_color, line_gap=5, max_lines=3)
    else:
        runtime.blit_wrapped_text(runtime.font_body, "备份列表为空。", detail_rect.inflate(-40, -40), palette["muted"], max_lines=2)

    buttons = (
        ("save-vault-create", "创建新备份", panel.left + 30, 150),
        ("save-vault-restore", "再次确认恢复" if restore_armed else "恢复所选", panel.left + 194, 150),
        ("save-vault-refresh", "刷新列表", panel.left + 358, 124),
    )
    for kind, label, left, width in buttons:
        disabled = kind == "save-vault-restore" and (not selected or not selected.get("ok"))
        rect = pygame.Rect(left, panel.bottom - 60, width, 36)
        pygame.draw.rect(runtime.screen, _with_alpha(palette["accent"] if kind == "save-vault-create" else palette["panel"], 70 if not disabled else 24), rect, border_radius=15)
        pygame.draw.rect(runtime.screen, _with_alpha(palette["panelBorder"], 42), rect, 1, border_radius=15)
        runtime.draw_game_ui_button_frame(rect, runtime.get_game_ui_button_state(rect, disabled=disabled))
        runtime.blit_text_center(runtime.font_ui, label, rect.centerx, rect.top + 9, palette["muted"] if disabled else palette["text"])
        runtime.overlay_hotspots.append({"kind": kind, "rect": rect, "disabled": disabled})
    hint = "↑↓ 选择 · B 创建 · Enter / R 恢复 · F 刷新 · Esc 返回"
    runtime.screen.blit(runtime.font_ui.render(hint, True, palette["muted"]), (detail_rect.left, panel.bottom - 49))


def handle_save_vault_event(runtime, event) -> bool:
    pygame = runtime.pygame
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_UP and runtime.save_vault_entries:
            runtime.save_vault_index = (runtime.save_vault_index - 1) % len(runtime.save_vault_entries)
            runtime.cancel_save_vault_restore_confirmation()
            return True
        if event.key == pygame.K_DOWN and runtime.save_vault_entries:
            runtime.save_vault_index = (runtime.save_vault_index + 1) % len(runtime.save_vault_entries)
            runtime.cancel_save_vault_restore_confirmation()
            return True
        if event.key == pygame.K_b:
            runtime.create_save_vault_backup()
            return True
        if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_r):
            runtime.restore_selected_save_vault()
            return True
        if event.key == pygame.K_f:
            runtime.refresh_save_vault_entries()
            return True
    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        for target in runtime.overlay_hotspots:
            if not target["rect"].collidepoint(event.pos):
                continue
            kind = str(target.get("kind") or "")
            if kind == "save-vault-entry":
                runtime.save_vault_index = max(0, int(target.get("value") or 0))
                runtime.cancel_save_vault_restore_confirmation()
                return True
            if kind == "save-vault-create":
                runtime.create_save_vault_backup()
                return True
            if kind == "save-vault-restore" and not target.get("disabled"):
                runtime.restore_selected_save_vault()
                return True
            if kind == "save-vault-refresh":
                runtime.refresh_save_vault_entries()
                return True
    return True


__all__ = [
    "SAVE_VAULT_FORMAT",
    "SAVE_VAULT_FORMAT_VERSION",
    "SAVE_VAULT_RECORD_NAMES",
    "build_runtime_save_vault_project_identity",
    "build_runtime_save_vault_records",
    "build_save_vault_bundle",
    "build_save_vault_filename",
    "build_save_vault_integrity",
    "build_save_vault_summary",
    "cancel_runtime_save_vault_restore_confirmation",
    "create_runtime_save_vault_backup",
    "get_save_vault_directory",
    "handle_save_vault_event",
    "list_save_vault_entries",
    "open_runtime_save_vault_overlay",
    "read_save_vault_file",
    "refresh_runtime_save_vault_entries",
    "reload_runtime_save_vault_records",
    "render_save_vault_overlay",
    "restore_selected_runtime_save_vault",
    "restore_save_vault_records",
    "validate_save_vault_bundle",
    "write_runtime_save_vault_record",
    "write_save_vault_bundle",
]
