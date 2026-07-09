const STORAGE_PREFIX = "canvasia-engine";

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

export function buildRuntimeStorageKeys(project = {}) {
  const scope = getProjectStorageScope(project);
  const keys = { scope };

  Object.entries(RUNTIME_STORAGE_KEY_SUFFIXES).forEach(([name, suffix]) => {
    keys[name] = buildRuntimeStorageKey(scope, suffix);
  });

  return Object.freeze(keys);
}

export function readRuntimeStorageJson(key, fallback = null, options = {}) {
  const storage = options.storage ?? getBrowserStorage(options.windowRef);
  if (!storage) {
    return fallback;
  }

  try {
    const raw = storage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch (error) {
    return fallback;
  }
}

export function writeRuntimeStorageJson(key, value, options = {}) {
  const storage = options.storage ?? getBrowserStorage(options.windowRef);
  if (!storage) {
    return false;
  }

  try {
    storage.setItem(key, JSON.stringify(value));
    return true;
  } catch (error) {
    return false;
  }
}

export function removeRuntimeStorageItem(key, options = {}) {
  const storage = options.storage ?? getBrowserStorage(options.windowRef);
  if (!storage) {
    return false;
  }

  try {
    storage.removeItem(key);
    return true;
  } catch (error) {
    return false;
  }
}
