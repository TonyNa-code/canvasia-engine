(function attachRecentWorkspaceTools(global) {
  const RECENT_WORKSPACE_LIMIT = 8;

  const RECENT_WORKSPACE_TYPE_LABELS = Object.freeze({
    scene: "剧情场景",
    script: "台本入口",
    asset: "素材资料",
    character: "角色资料",
  });

  function hasOwn(source, key) {
    return Object.prototype.hasOwnProperty.call(source, key);
  }

  function getSafeRecentWorkspaceType(type) {
    return hasOwn(RECENT_WORKSPACE_TYPE_LABELS, type) ? type : "scene";
  }

  function getRecentWorkspaceTypeLabel(type) {
    return RECENT_WORKSPACE_TYPE_LABELS[getSafeRecentWorkspaceType(type)] ?? RECENT_WORKSPACE_TYPE_LABELS.scene;
  }

  function sanitizeRecentWorkspaceText(value, maxLength = 140) {
    const text = String(value ?? "").trim();
    const safeMaxLength = Number.isInteger(Number(maxLength)) && Number(maxLength) >= 0 ? Number(maxLength) : 140;
    return text ? text.slice(0, safeMaxLength) : "";
  }

  function getRecentWorkspaceStorageKey(scope = "default") {
    const safeScope = sanitizeRecentWorkspaceText(scope, 180) || "default";
    return `tony-na-engine:editor-recent-work:${safeScope}`;
  }

  function getRecentWorkspaceItemKey(entry) {
    if (!entry) {
      return "";
    }

    if (entry.type === "script") {
      return `script:${entry.sceneId ?? ""}:${entry.blockId ?? ""}`;
    }

    if (entry.type === "asset") {
      return `asset:${entry.assetId ?? ""}`;
    }

    if (entry.type === "character") {
      return `character:${entry.characterId ?? ""}`;
    }

    return `scene:${entry.sceneId ?? ""}`;
  }

  function getSafeRecentWorkspaceUpdatedAt(value, nowIso = () => new Date().toISOString()) {
    const updatedAt = new Date(value ?? nowIso());
    return Number.isNaN(updatedAt.getTime()) ? nowIso() : updatedAt.toISOString();
  }

  function sanitizeRecentWorkspaceEntry(source = {}, options = {}) {
    if (!source || typeof source !== "object") {
      return null;
    }

    const nowIso = typeof options.nowIso === "function" ? options.nowIso : () => new Date().toISOString();
    const type = getSafeRecentWorkspaceType(source.type);
    const base = {
      type,
      updatedAt: getSafeRecentWorkspaceUpdatedAt(source.updatedAt, nowIso),
      title: sanitizeRecentWorkspaceText(source.title, 160),
      subtitle: sanitizeRecentWorkspaceText(source.subtitle, 180),
      summary: sanitizeRecentWorkspaceText(source.summary, 240),
    };

    if (type === "script") {
      const sceneId = sanitizeRecentWorkspaceText(source.sceneId, 120);
      const blockId = sanitizeRecentWorkspaceText(source.blockId, 120);
      return sceneId && blockId ? { ...base, sceneId, blockId } : null;
    }

    if (type === "asset") {
      const assetId = sanitizeRecentWorkspaceText(source.assetId, 120);
      return assetId ? { ...base, assetId } : null;
    }

    if (type === "character") {
      const characterId = sanitizeRecentWorkspaceText(source.characterId, 120);
      return characterId ? { ...base, characterId } : null;
    }

    const sceneId = sanitizeRecentWorkspaceText(source.sceneId, 120);
    return sceneId ? { ...base, sceneId } : null;
  }

  function capRecentWorkspaceItems(entries, limit = RECENT_WORKSPACE_LIMIT) {
    const safeLimit = Number.isInteger(Number(limit)) && Number(limit) >= 0
      ? Number(limit)
      : RECENT_WORKSPACE_LIMIT;
    return (Array.isArray(entries) ? entries : [])
      .map((entry) => sanitizeRecentWorkspaceEntry(entry))
      .filter(Boolean)
      .slice(0, safeLimit);
  }

  function mergeRecentWorkspaceItem(entries, source, options = {}) {
    const limit = options.limit ?? RECENT_WORKSPACE_LIMIT;
    const entry = sanitizeRecentWorkspaceEntry(source, options);
    if (!entry) {
      return capRecentWorkspaceItems(entries, limit);
    }

    const nextKey = getRecentWorkspaceItemKey(entry);
    return [
      entry,
      ...capRecentWorkspaceItems(entries, limit).filter((item) => getRecentWorkspaceItemKey(item) !== nextKey),
    ].slice(0, Number.isInteger(Number(limit)) && Number(limit) >= 0 ? Number(limit) : RECENT_WORKSPACE_LIMIT);
  }

  function loadStoredRecentWorkspaceItems(storage, key, options = {}) {
    if (!storage || !key) {
      return [];
    }

    try {
      const raw = storage.getItem(key);
      if (!raw) {
        return [];
      }

      const parsed = JSON.parse(raw);
      const entries = Array.isArray(parsed) ? parsed : Array.isArray(parsed?.items) ? parsed.items : [];
      return capRecentWorkspaceItems(entries, options.limit ?? RECENT_WORKSPACE_LIMIT);
    } catch (error) {
      return [];
    }
  }

  function persistRecentWorkspaceItems(storage, key, entries, options = {}) {
    if (!storage || !key) {
      return false;
    }

    try {
      storage.setItem(
        key,
        JSON.stringify(capRecentWorkspaceItems(entries, options.limit ?? RECENT_WORKSPACE_LIMIT))
      );
      return true;
    } catch (error) {
      return false;
    }
  }

  function clearStoredRecentWorkspaceItems(storage, key) {
    if (!storage || !key) {
      return false;
    }

    try {
      storage.removeItem(key);
      return true;
    } catch (error) {
      return false;
    }
  }

  global.TonyNaEditorRecentWorkspace = Object.freeze({
    RECENT_WORKSPACE_LIMIT,
    RECENT_WORKSPACE_TYPE_LABELS,
    getSafeRecentWorkspaceType,
    getRecentWorkspaceTypeLabel,
    sanitizeRecentWorkspaceText,
    getRecentWorkspaceStorageKey,
    getRecentWorkspaceItemKey,
    sanitizeRecentWorkspaceEntry,
    capRecentWorkspaceItems,
    mergeRecentWorkspaceItem,
    loadStoredRecentWorkspaceItems,
    persistRecentWorkspaceItems,
    clearStoredRecentWorkspaceItems,
  });
})(typeof window !== "undefined" ? window : globalThis);
