const STORAGE_PREFIX = "canvasia-engine";
const RUNTIME_STORAGE_BACKUP_SUFFIX = "backup-v1";
const DEFAULT_BACKUP_CHARACTER_LIMIT = 1_000_000;
const RUNTIME_STORAGE_RECOVERY_EVENT_LIMIT = 32;
const runtimeStorageRecoveryEvents = [];

export const RUNTIME_STORAGE_KEY_SUFFIXES = Object.freeze({
  playback: "player-preview",
  autoResume: "player-autoresume",
  readHistory: "player-read",
  saveSlots: "player-saves",
  quickSave: "player-quicksave",
  playerProfile: "player-profile",
  achievements: "player-achievements",
  chapters: "player-chapters",
  locations: "player-locations",
  narrations: "player-narrations",
  relations: "player-relations",
  voiceReplay: "player-voice-replay",
  characters: "player-characters",
  extraUnlocks: "player-extra",
  endings: "player-endings",
  persistentVariables: "player-persistent-variables",
});

export function getBrowserStorage(windowRef = globalThis.window) {
  try {
    return windowRef?.localStorage ?? null;
  } catch (error) {
    return null;
  }
}

export function getProjectStorageScope(project = {}) {
  const title = String(project?.title ?? "canvasia-project")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9\u4e00-\u9fa5_-]+/g, "-")
    .replace(/-+/g, "-")
    .slice(0, 72);

  return title || "project";
}

export function buildRuntimeStorageKey(scope, suffix) {
  const safeScope = String(scope || "project").trim() || "project";
  const safeSuffix = String(suffix || "player-data").trim() || "player-data";
  return `${STORAGE_PREFIX}:${safeSuffix}:${safeScope}`;
}

export function buildRuntimeStorageBackupKey(key) {
  return `${String(key || "").trim()}:${RUNTIME_STORAGE_BACKUP_SUFFIX}`;
}

export function shouldBackupRuntimeStorageKey(key) {
  return String(key || "").startsWith(`${STORAGE_PREFIX}:`);
}

export function buildRuntimeStorageKeys(project = {}) {
  const scope = getProjectStorageScope(project);
  const keys = { scope };

  Object.entries(RUNTIME_STORAGE_KEY_SUFFIXES).forEach(([name, suffix]) => {
    keys[name] = buildRuntimeStorageKey(scope, suffix);
  });

  return Object.freeze(keys);
}

function parseRuntimeStorageJson(raw) {
  if (typeof raw !== "string") {
    return { valid: false, value: null };
  }

  try {
    return { valid: true, value: JSON.parse(raw) };
  } catch (error) {
    return { valid: false, value: null };
  }
}

function serializeRuntimeStorageBackup(value, characterLimit = DEFAULT_BACKUP_CHARACTER_LIMIT) {
  const safeLimit = Math.max(0, Number(characterLimit) || 0);
  try {
    const serialized = JSON.stringify(value);
    if (typeof serialized !== "string") {
      return null;
    }
    if (serialized.length <= safeLimit) {
      return serialized;
    }

    // Save thumbnails are reproducible presentation data. Dropping them keeps a
    // large slot collection recoverable without exhausting the browser quota.
    const compact = JSON.stringify(value, (name, item) => (name === "thumbnailDataUrl" ? "" : item));
    return typeof compact === "string" && compact.length <= safeLimit ? compact : null;
  } catch (error) {
    return null;
  }
}

function recordRuntimeStorageRecovery(key, backupKey, options = {}) {
  const event = {
    key,
    backupKey,
    recoveredAt: new Date().toISOString(),
  };
  runtimeStorageRecoveryEvents.push(event);
  runtimeStorageRecoveryEvents.splice(
    0,
    Math.max(0, runtimeStorageRecoveryEvents.length - RUNTIME_STORAGE_RECOVERY_EVENT_LIMIT)
  );
  try {
    options.onRecovery?.({ ...event });
  } catch (error) {
    // Recovery must not fail because an optional UI callback failed.
  }
}

export function consumeRuntimeStorageRecoveryEvents() {
  return runtimeStorageRecoveryEvents.splice(0).map((event) => ({ ...event }));
}

export function readRuntimeStorageJson(key, fallback = null, options = {}) {
  const storage = options.storage ?? getBrowserStorage(options.windowRef);
  if (!storage) {
    return fallback;
  }

  let raw = null;
  try {
    raw = storage.getItem(key);
  } catch (error) {
    return fallback;
  }

  const primary = parseRuntimeStorageJson(raw);
  if (primary.valid) {
    return primary.value;
  }

  const backupEnabled = options.backup !== false && shouldBackupRuntimeStorageKey(key);
  if (!backupEnabled) {
    return fallback;
  }

  const backupKey = buildRuntimeStorageBackupKey(key);
  try {
    const backupRaw = storage.getItem(backupKey);
    const backup = parseRuntimeStorageJson(backupRaw);
    if (!backup.valid) {
      return fallback;
    }
    try {
      storage.setItem(key, backupRaw);
    } catch (error) {
      // Returning the valid backup is still safer than discarding it when the
      // browser currently refuses a self-healing write.
    }
    recordRuntimeStorageRecovery(key, backupKey, options);
    return backup.value;
  } catch (error) {
    return fallback;
  }
}

export function writeRuntimeStorageJson(key, value, options = {}) {
  const storage = options.storage ?? getBrowserStorage(options.windowRef);
  if (!storage) {
    return false;
  }

  let serialized = null;
  try {
    serialized = JSON.stringify(value);
  } catch (error) {
    return false;
  }
  if (typeof serialized !== "string") {
    return false;
  }

  const backupEnabled = options.backup !== false && shouldBackupRuntimeStorageKey(key);
  let previous = { valid: false, value: null };
  if (backupEnabled) {
    try {
      previous = parseRuntimeStorageJson(storage.getItem(key));
    } catch (error) {
      previous = { valid: false, value: null };
    }
  }

  try {
    storage.setItem(key, serialized);
  } catch (error) {
    return false;
  }

  if (backupEnabled) {
    const backupValue = previous.valid ? previous.value : value;
    const backupRaw = serializeRuntimeStorageBackup(backupValue, options.backupCharacterLimit);
    if (backupRaw !== null) {
      try {
        storage.setItem(buildRuntimeStorageBackupKey(key), backupRaw);
      } catch (error) {
        // The primary localStorage write is atomic. Quota pressure may prevent
        // the extra recovery copy, but must not report the completed save as lost.
      }
    }
  }
  return true;
}

export function removeRuntimeStorageItem(key, options = {}) {
  const storage = options.storage ?? getBrowserStorage(options.windowRef);
  if (!storage) {
    return false;
  }

  try {
    if (options.backup !== false && shouldBackupRuntimeStorageKey(key)) {
      storage.removeItem(buildRuntimeStorageBackupKey(key));
    }
    storage.removeItem(key);
    return true;
  } catch (error) {
    return false;
  }
}
