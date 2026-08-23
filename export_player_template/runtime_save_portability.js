import {
  RUNTIME_STORAGE_KEY_SUFFIXES,
  buildRuntimeStorageBackupKey,
  getBrowserStorage,
  readRuntimeStorageJson,
  removeRuntimeStorageItem,
  writeRuntimeStorageJson,
} from "./runtime_storage.js";

export const RUNTIME_SAVE_BACKUP_FORMAT = "canvasia-runtime-save-backup";
export const RUNTIME_SAVE_BACKUP_VERSION = 1;
export const DEFAULT_RUNTIME_SAVE_BACKUP_CHARACTER_LIMIT = 12_000_000;

const RUNTIME_SAVE_BACKUP_ENGINE = "Canvasia Engine";
const RUNTIME_SAVE_RECORD_NAMES = Object.freeze(Object.keys(RUNTIME_STORAGE_KEY_SUFFIXES));
const TOP_LEVEL_FIELDS = Object.freeze([
  "format",
  "formatVersion",
  "engine",
  "exportedAt",
  "project",
  "compaction",
  "records",
  "integrity",
]);
const PROJECT_FIELDS = Object.freeze(["projectId", "scope", "title", "releaseVersion"]);
const COMPACTION_FIELDS = Object.freeze(["thumbnailCountRemoved"]);
const RECORD_FIELDS = Object.freeze(["present", "value"]);

function isPlainRecord(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function getSafeText(value, maxLength = 240) {
  return String(value ?? "").trim().slice(0, Math.max(0, maxLength));
}

function hasOnlyFields(value, allowedFields) {
  return isPlainRecord(value) && Object.keys(value).every((key) => allowedFields.includes(key));
}

function stableSerialize(value) {
  if (value === null || typeof value !== "object") {
    const serialized = JSON.stringify(value);
    if (typeof serialized !== "string") {
      throw new TypeError("Save backup contains a value that cannot be serialized.");
    }
    return serialized;
  }
  if (Array.isArray(value)) {
    return `[${value.map((item) => stableSerialize(item)).join(",")}]`;
  }
  return `{${Object.keys(value)
    .sort()
    .map((key) => `${JSON.stringify(key)}:${stableSerialize(value[key])}`)
    .join(",")}}`;
}

function getFnv1a32(value) {
  let hash = 0x811c9dc5;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193) >>> 0;
  }
  return hash.toString(16).padStart(8, "0");
}

function getBackupIntegritySource(backup) {
  return {
    format: backup.format,
    formatVersion: backup.formatVersion,
    engine: backup.engine,
    exportedAt: backup.exportedAt,
    project: backup.project,
    compaction: backup.compaction,
    records: backup.records,
  };
}

function buildBackupIntegrity(backup) {
  return `fnv1a32:${getFnv1a32(stableSerialize(getBackupIntegritySource(backup)))}`;
}

function getSafeNowIso(now = new Date()) {
  const candidate = typeof now === "function" ? now() : now;
  const date = candidate instanceof Date ? candidate : new Date(candidate);
  return Number.isFinite(date.getTime()) ? date.toISOString() : new Date().toISOString();
}

function buildProjectIdentity(project = {}, storageKeys = {}) {
  return {
    projectId: getSafeText(project?.projectId, 160),
    scope: getSafeText(storageKeys?.scope, 160),
    title: getSafeText(project?.title || "未命名项目", 240),
    releaseVersion: getSafeText(project?.releaseVersion, 120),
  };
}

function hasValidStorageKeys(storageKeys = {}) {
  return RUNTIME_SAVE_RECORD_NAMES.every(
    (name) => typeof storageKeys?.[name] === "string" && Boolean(storageKeys[name])
  );
}

function cloneJsonValue(value) {
  return JSON.parse(JSON.stringify(value));
}

function stripThumbnailData(value, counter) {
  if (Array.isArray(value)) {
    return value.map((item) => stripThumbnailData(item, counter));
  }
  if (!isPlainRecord(value)) {
    return value;
  }
  const result = {};
  Object.entries(value).forEach(([key, item]) => {
    if (key === "thumbnailDataUrl" && typeof item === "string" && item) {
      result[key] = "";
      counter.count += 1;
      return;
    }
    result[key] = stripThumbnailData(item, counter);
  });
  return result;
}

function compactBackupThumbnails(backup) {
  const counter = { count: 0 };
  const records = {};
  RUNTIME_SAVE_RECORD_NAMES.forEach((name) => {
    const entry = backup.records[name];
    records[name] = entry.present
      ? { present: true, value: stripThumbnailData(entry.value, counter) }
      : { present: false, value: null };
  });
  return {
    ...backup,
    compaction: { thumbnailCountRemoved: counter.count },
    records,
  };
}

function getStorageSnapshot(storage, storageKeys) {
  const snapshot = new Map();
  RUNTIME_SAVE_RECORD_NAMES.forEach((name) => {
    const key = storageKeys[name];
    const backupKey = buildRuntimeStorageBackupKey(key);
    snapshot.set(key, storage.getItem(key));
    snapshot.set(backupKey, storage.getItem(backupKey));
  });
  return snapshot;
}

function restoreStorageSnapshot(storage, snapshot) {
  let restored = true;
  snapshot.forEach((rawValue, key) => {
    try {
      if (rawValue === null) {
        storage.removeItem(key);
      } else {
        storage.setItem(key, rawValue);
      }
    } catch (error) {
      restored = false;
    }
  });
  return restored;
}

function buildFailure(code, message, details = {}) {
  return { ok: false, code, message, details };
}

function buildSummary(backup) {
  const storedRecordCount = RUNTIME_SAVE_RECORD_NAMES.reduce(
    (count, name) => count + (backup.records[name]?.present ? 1 : 0),
    0
  );
  return {
    projectId: backup.project.projectId,
    projectTitle: backup.project.title,
    releaseVersion: backup.project.releaseVersion,
    exportedAt: backup.exportedAt,
    recordCount: RUNTIME_SAVE_RECORD_NAMES.length,
    storedRecordCount,
    emptyRecordCount: RUNTIME_SAVE_RECORD_NAMES.length - storedRecordCount,
    thumbnailCountRemoved: backup.compaction.thumbnailCountRemoved,
  };
}

export function createRuntimeSaveBackup(project = {}, storageKeys = {}, options = {}) {
  const storage = options.storage ?? getBrowserStorage(options.windowRef);
  if (!storage) {
    throw new Error("当前环境无法读取浏览器存档。");
  }
  const characterLimit = Math.max(
    1,
    Number(options.characterLimit) || DEFAULT_RUNTIME_SAVE_BACKUP_CHARACTER_LIMIT
  );
  const missing = Symbol("missing-runtime-save-record");
  const records = {};

  RUNTIME_SAVE_RECORD_NAMES.forEach((name) => {
    const key = storageKeys[name];
    if (typeof key !== "string" || !key) {
      throw new TypeError(`Runtime storage key is missing: ${name}`);
    }
    const value = readRuntimeStorageJson(key, missing, { storage });
    records[name] = value === missing
      ? { present: false, value: null }
      : { present: true, value: cloneJsonValue(value) };
  });

  let backup = {
    format: RUNTIME_SAVE_BACKUP_FORMAT,
    formatVersion: RUNTIME_SAVE_BACKUP_VERSION,
    engine: RUNTIME_SAVE_BACKUP_ENGINE,
    exportedAt: getSafeNowIso(options.now),
    project: buildProjectIdentity(project, storageKeys),
    compaction: { thumbnailCountRemoved: 0 },
    records,
  };
  backup.integrity = buildBackupIntegrity(backup);

  if (JSON.stringify(backup).length > characterLimit) {
    backup = compactBackupThumbnails(backup);
    backup.integrity = buildBackupIntegrity(backup);
  }
  if (JSON.stringify(backup).length > characterLimit) {
    throw new RangeError("存档内容过大，移除可重建缩略图后仍无法生成安全备份。");
  }
  return backup;
}

export function validateRuntimeSaveBackup(source, options = {}) {
  const characterLimit = Math.max(
    1,
    Number(options.characterLimit) || DEFAULT_RUNTIME_SAVE_BACKUP_CHARACTER_LIMIT
  );
  if (!isPlainRecord(source) || !hasOnlyFields(source, TOP_LEVEL_FIELDS)) {
    return buildFailure("invalid_root", "这不是可识别的 Canvasia 存档备份。");
  }
  let serialized = "";
  try {
    serialized = JSON.stringify(source);
  } catch (error) {
    return buildFailure("not_serializable", "备份内容无法读取。");
  }
  if (serialized.length > characterLimit) {
    return buildFailure("too_large", "备份文件超过安全大小限制。");
  }
  if (source.format !== RUNTIME_SAVE_BACKUP_FORMAT) {
    return buildFailure("wrong_format", "文件格式不属于 Canvasia 玩家存档备份。");
  }
  if (source.formatVersion !== RUNTIME_SAVE_BACKUP_VERSION) {
    return buildFailure("unsupported_version", "备份版本暂不受当前 Runtime 支持。");
  }
  if (source.engine !== RUNTIME_SAVE_BACKUP_ENGINE) {
    return buildFailure("wrong_engine", "备份来源无法确认。");
  }
  if (!Number.isFinite(Date.parse(source.exportedAt))) {
    return buildFailure("invalid_export_time", "备份缺少有效的导出时间。");
  }
  if (!hasOnlyFields(source.project, PROJECT_FIELDS)) {
    return buildFailure("invalid_project", "备份中的项目信息不完整。");
  }
  if (!hasOnlyFields(source.compaction, COMPACTION_FIELDS)) {
    return buildFailure("invalid_compaction", "备份压缩信息无法识别。");
  }
  const thumbnailCountRemoved = Number(source.compaction.thumbnailCountRemoved);
  if (!Number.isInteger(thumbnailCountRemoved) || thumbnailCountRemoved < 0) {
    return buildFailure("invalid_compaction", "备份压缩信息无法识别。");
  }
  if (!isPlainRecord(source.records)) {
    return buildFailure("invalid_records", "备份中没有可恢复的存档记录。");
  }
  const recordNames = Object.keys(source.records);
  if (
    recordNames.length !== RUNTIME_SAVE_RECORD_NAMES.length ||
    recordNames.some((name) => !RUNTIME_SAVE_RECORD_NAMES.includes(name)) ||
    RUNTIME_SAVE_RECORD_NAMES.some((name) => !recordNames.includes(name))
  ) {
    return buildFailure("record_set_mismatch", "备份记录集合与当前 Runtime 不匹配。");
  }

  const normalizedRecords = {};
  for (const name of RUNTIME_SAVE_RECORD_NAMES) {
    const entry = source.records[name];
    if (!hasOnlyFields(entry, RECORD_FIELDS) || typeof entry.present !== "boolean") {
      return buildFailure("invalid_record", `备份记录无法识别：${name}`);
    }
    try {
      normalizedRecords[name] = entry.present
        ? { present: true, value: cloneJsonValue(entry.value) }
        : { present: false, value: null };
    } catch (error) {
      return buildFailure("invalid_record_value", `备份记录无法读取：${name}`);
    }
  }

  const backup = {
    format: source.format,
    formatVersion: source.formatVersion,
    engine: source.engine,
    exportedAt: new Date(source.exportedAt).toISOString(),
    project: {
      projectId: getSafeText(source.project.projectId, 160),
      scope: getSafeText(source.project.scope, 160),
      title: getSafeText(source.project.title, 240),
      releaseVersion: getSafeText(source.project.releaseVersion, 120),
    },
    compaction: { thumbnailCountRemoved },
    records: normalizedRecords,
  };
  backup.integrity = getSafeText(source.integrity, 120);
  if (!backup.integrity || backup.integrity !== buildBackupIntegrity(backup)) {
    return buildFailure("integrity_mismatch", "备份完整性校验失败，文件可能不完整或已被改写。");
  }

  const expected = buildProjectIdentity(options.project, options.storageKeys);
  if (expected.projectId) {
    if (!backup.project.projectId || backup.project.projectId !== expected.projectId) {
      return buildFailure("project_mismatch", "这个备份属于另一个游戏项目。", {
        expectedTitle: expected.title,
        actualTitle: backup.project.title,
      });
    }
  } else if (!backup.project.scope || backup.project.scope !== expected.scope) {
    return buildFailure("project_mismatch", "这个备份属于另一个游戏项目。", {
      expectedTitle: expected.title,
      actualTitle: backup.project.title,
    });
  }

  const summary = buildSummary(backup);
  return {
    ok: true,
    code: "valid",
    backup,
    summary: {
      ...summary,
      releaseVersionMismatch: Boolean(
        expected.releaseVersion &&
        backup.project.releaseVersion &&
        expected.releaseVersion !== backup.project.releaseVersion
      ),
    },
  };
}

export function parseRuntimeSaveBackupText(text, options = {}) {
  if (typeof text !== "string" || !text.trim()) {
    return buildFailure("empty_file", "备份文件是空的。");
  }
  const characterLimit = Math.max(
    1,
    Number(options.characterLimit) || DEFAULT_RUNTIME_SAVE_BACKUP_CHARACTER_LIMIT
  );
  if (text.length > characterLimit) {
    return buildFailure("too_large", "备份文件超过安全大小限制。");
  }
  try {
    return validateRuntimeSaveBackup(JSON.parse(text), options);
  } catch (error) {
    return buildFailure("invalid_json", "备份文件不是有效的 JSON 数据。");
  }
}

export function restoreRuntimeSaveBackup(source, options = {}) {
  const validation = validateRuntimeSaveBackup(source, options);
  if (!validation.ok) {
    return validation;
  }
  const storage = options.storage ?? getBrowserStorage(options.windowRef);
  if (!storage) {
    return buildFailure("storage_unavailable", "当前环境无法写入浏览器存档。");
  }
  if (!hasValidStorageKeys(options.storageKeys)) {
    return buildFailure("storage_keys_missing", "当前 Runtime 的存档键不完整，恢复操作已取消。");
  }

  let previousSnapshot = null;
  try {
    previousSnapshot = getStorageSnapshot(storage, options.storageKeys);
  } catch (error) {
    return buildFailure("snapshot_failed", "恢复前无法安全备份当前存档，操作已取消。");
  }

  let failedRecord = "";
  for (const name of RUNTIME_SAVE_RECORD_NAMES) {
    const key = options.storageKeys[name];
    const entry = validation.backup.records[name];
    const changed = entry.present
      ? writeRuntimeStorageJson(key, entry.value, { storage })
      : removeRuntimeStorageItem(key, { storage });
    if (!changed) {
      failedRecord = name;
      break;
    }
  }

  if (failedRecord) {
    const rolledBack = restoreStorageSnapshot(storage, previousSnapshot);
    return buildFailure(
      rolledBack ? "restore_failed" : "restore_failed_rollback_incomplete",
      rolledBack
        ? "恢复未完成，原有存档已经安全回滚。"
        : "恢复失败且浏览器拒绝完整回滚，请先不要关闭页面并重新导出当前存档。",
      { failedRecord }
    );
  }

  return {
    ok: true,
    code: "restored",
    message: "存档已经恢复，Runtime 将重新载入。",
    summary: validation.summary,
  };
}

export function serializeRuntimeSaveBackup(backup) {
  return `${JSON.stringify(backup, null, 2)}\n`;
}

export function getRuntimeSaveBackupFileName(project = {}, exportedAt = new Date().toISOString()) {
  const title = getSafeText(project?.title || "canvasia-game", 72)
    .replace(/[\\/:*?"<>|\u0000-\u001f]+/g, "-")
    .replace(/\s+/g, " ")
    .replace(/-+/g, "-")
    .trim() || "canvasia-game";
  const date = Number.isFinite(Date.parse(exportedAt))
    ? new Date(exportedAt).toISOString().slice(0, 10).replaceAll("-", "")
    : "backup";
  return `${title}_存档备份_${date}.canvasia-save.json`;
}

function triggerBackupDownload(backup, options = {}) {
  const documentRef = options.documentRef ?? globalThis.document;
  const urlApi = options.urlApi ?? globalThis.URL;
  const BlobCtor = options.BlobCtor ?? globalThis.Blob;
  if (!documentRef?.createElement || !urlApi?.createObjectURL || typeof BlobCtor !== "function") {
    throw new Error("当前环境不支持下载存档备份。");
  }
  const blob = new BlobCtor([serializeRuntimeSaveBackup(backup)], {
    type: "application/json;charset=utf-8",
  });
  const url = urlApi.createObjectURL(blob);
  const anchor = documentRef.createElement("a");
  anchor.href = url;
  anchor.download = getRuntimeSaveBackupFileName(backup.project, backup.exportedAt);
  anchor.hidden = true;
  documentRef.body?.appendChild(anchor);
  anchor.click();
  anchor.remove?.();
  const release = () => urlApi.revokeObjectURL?.(url);
  (options.setTimeout ?? globalThis.setTimeout)?.(release, 0) ?? release();
  return anchor.download;
}

async function readBackupFile(file, options = {}) {
  if (typeof file?.text === "function") {
    return file.text();
  }
  const FileReaderCtor = options.FileReaderCtor ?? globalThis.FileReader;
  if (typeof FileReaderCtor !== "function") {
    throw new Error("当前环境无法读取所选文件。");
  }
  return new Promise((resolve, reject) => {
    const reader = new FileReaderCtor();
    reader.addEventListener("load", () => resolve(String(reader.result ?? "")), { once: true });
    reader.addEventListener("error", () => reject(reader.error ?? new Error("文件读取失败。")), { once: true });
    reader.readAsText(file, "utf-8");
  });
}

export function createRuntimeSavePortabilityController(options = {}) {
  const refs = options.refs ?? {};
  const project = options.project ?? {};
  const storageKeys = options.storageKeys ?? {};
  const windowRef = options.windowRef ?? globalThis.window;
  const storage = options.storage ?? getBrowserStorage(windowRef);
  const characterLimit = Math.max(
    1,
    Number(options.characterLimit) || DEFAULT_RUNTIME_SAVE_BACKUP_CHARACTER_LIMIT
  );
  const listeners = [];
  let attached = false;
  let pendingBackup = null;
  let pendingSummary = null;
  let busy = false;
  let selectionToken = 0;

  function setStatus(message, tone = "neutral") {
    if (!refs.status) {
      return;
    }
    refs.status.textContent = message;
    refs.status.dataset.tone = tone;
  }

  function render() {
    const unavailable = !storage;
    if (refs.exportButton) {
      refs.exportButton.disabled = unavailable || busy;
    }
    if (refs.importButton) {
      refs.importButton.disabled = unavailable || busy;
    }
    if (refs.restoreButton) {
      refs.restoreButton.hidden = !pendingBackup;
      refs.restoreButton.disabled = unavailable || busy || !pendingBackup;
    }
    if (refs.root) {
      refs.root.dataset.busy = busy ? "true" : "false";
    }
    if (unavailable) {
      setStatus("当前浏览器没有开放本地存档权限，暂时无法备份或恢复。", "error");
    }
  }

  function addListener(target, eventName, callback) {
    if (typeof target?.addEventListener !== "function") {
      return;
    }
    target.addEventListener(eventName, callback);
    listeners.push([target, eventName, callback]);
  }

  function exportCurrentSave() {
    if (busy || !storage) {
      return false;
    }
    busy = true;
    render();
    try {
      const backup = createRuntimeSaveBackup(project, storageKeys, {
        storage,
        characterLimit,
        now: options.now,
      });
      const fileName = triggerBackupDownload(backup, options);
      const summary = buildSummary(backup);
      const compactNote = summary.thumbnailCountRemoved > 0
        ? `；为控制体积已省略 ${summary.thumbnailCountRemoved} 张可重建缩略图`
        : "";
      setStatus(`已导出 ${summary.storedRecordCount} 组玩家记录：${fileName}${compactNote}。`, "success");
      options.onExported?.({ backup, fileName, summary });
      return true;
    } catch (error) {
      setStatus(error?.message || "存档备份导出失败。", "error");
      return false;
    } finally {
      busy = false;
      render();
    }
  }

  function chooseBackupFile() {
    if (busy || !storage) {
      return false;
    }
    refs.fileInput?.click?.();
    return true;
  }

  async function handleBackupFileChange(event) {
    const token = selectionToken + 1;
    selectionToken = token;
    pendingBackup = null;
    pendingSummary = null;
    const file = event?.target?.files?.[0] ?? null;
    if (!file) {
      render();
      return false;
    }
    if (Number(file.size) > characterLimit * 4) {
      setStatus("所选备份文件超过安全大小限制。", "error");
      event.target.value = "";
      render();
      return false;
    }
    busy = true;
    setStatus("正在核对备份内容，不会在确认前改动当前存档。", "neutral");
    render();
    try {
      const text = await readBackupFile(file, options);
      if (token !== selectionToken) {
        return false;
      }
      const validation = parseRuntimeSaveBackupText(text, {
        project,
        storageKeys,
        characterLimit,
      });
      if (!validation.ok) {
        setStatus(validation.message, "error");
        return false;
      }
      pendingBackup = validation.backup;
      pendingSummary = validation.summary;
      const versionNote = pendingSummary.releaseVersionMismatch
        ? "；游戏版本不同，将通过当前兼容层读取"
        : "";
      setStatus(
        `已核对 ${pendingSummary.projectTitle} 的备份：${pendingSummary.storedRecordCount} 组记录，导出于 ${new Date(
          pendingSummary.exportedAt
        ).toLocaleString()}${versionNote}。再次确认后才会覆盖当前玩家数据。`,
        "ready"
      );
      options.onValidated?.({ backup: pendingBackup, summary: pendingSummary });
      return true;
    } catch (error) {
      setStatus(error?.message || "备份文件读取失败。", "error");
      return false;
    } finally {
      busy = false;
      if (event?.target) {
        event.target.value = "";
      }
      render();
    }
  }

  function restorePendingSave() {
    if (busy || !pendingBackup || !storage) {
      return false;
    }
    busy = true;
    render();
    options.onBeforeRestore?.({ backup: pendingBackup, summary: pendingSummary });
    const result = restoreRuntimeSaveBackup(pendingBackup, {
      project,
      storageKeys,
      storage,
      characterLimit,
    });
    if (!result.ok) {
      busy = false;
      options.onRestoreFailed?.(result);
      setStatus(result.message, "error");
      render();
      return false;
    }
    pendingBackup = null;
    pendingSummary = null;
    setStatus(result.message, "success");
    options.onRestored?.(result);
    return true;
  }

  function attach() {
    if (attached) {
      return;
    }
    attached = true;
    addListener(refs.exportButton, "click", exportCurrentSave);
    addListener(refs.importButton, "click", chooseBackupFile);
    addListener(refs.fileInput, "change", handleBackupFileChange);
    addListener(refs.restoreButton, "click", restorePendingSave);
    render();
  }

  function detach() {
    listeners.splice(0).forEach(([target, eventName, callback]) => {
      target.removeEventListener?.(eventName, callback);
    });
    attached = false;
    selectionToken += 1;
  }

  function getSnapshot() {
    return Object.freeze({
      attached,
      busy,
      pending: Boolean(pendingBackup),
      summary: pendingSummary ? { ...pendingSummary } : null,
    });
  }

  return Object.freeze({
    attach,
    detach,
    render,
    exportCurrentSave,
    chooseBackupFile,
    handleBackupFileChange,
    restorePendingSave,
    getSnapshot,
  });
}
