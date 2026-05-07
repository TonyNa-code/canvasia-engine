(function attachPreviewSaveTools(global) {
  const PREVIEW_SAVE_SHORTCUT_COUNT = 3;
  const PREVIEW_SAVE_DIALOG_PAGE_SIZE = 6;

  function clampNumber(value, min, max) {
    return Math.min(Math.max(value, min), max);
  }

  function getSafeSlotCount(slotCount, fallback = PREVIEW_SAVE_SHORTCUT_COUNT) {
    const numeric = Number(slotCount);
    return Number.isInteger(numeric) && numeric > 0 ? numeric : fallback;
  }

  function getSafePreviewSaveSlotIndex(rawIndex, slotCount) {
    const numeric = Number(rawIndex);
    const safeSlotCount = getSafeSlotCount(slotCount);
    if (!Number.isInteger(numeric)) {
      return null;
    }
    const nextIndex = numeric - 1;
    return nextIndex >= 0 && nextIndex < safeSlotCount ? nextIndex : null;
  }

  function getPreviewSaveDialogPageCount(slotCount, pageSize = PREVIEW_SAVE_DIALOG_PAGE_SIZE) {
    const safeSlotCount = getSafeSlotCount(slotCount);
    const safePageSize = getSafeSlotCount(pageSize, PREVIEW_SAVE_DIALOG_PAGE_SIZE);
    return Math.max(1, Math.ceil(safeSlotCount / safePageSize));
  }

  function getSafePreviewSaveDialogPage(rawPage, options = {}) {
    const pageCount = getPreviewSaveDialogPageCount(options.slotCount, options.pageSize);
    const maxPageIndex = pageCount - 1;
    const numeric = Number(rawPage);
    if (!Number.isInteger(numeric)) {
      return clampNumber(Number(options.currentPage) || 0, 0, maxPageIndex);
    }
    return clampNumber(numeric, 0, maxPageIndex);
  }

  function getSafePreviewSaveDialogMode(rawMode) {
    return rawMode === "load" ? "load" : "save";
  }

  function createEmptyPreviewSaveSlots(slotCount) {
    return Array.from({ length: getSafeSlotCount(slotCount) }, () => null);
  }

  function deepClonePreviewData(value) {
    try {
      return JSON.parse(JSON.stringify(value ?? null));
    } catch (error) {
      return null;
    }
  }

  function sanitizeStoredPreviewSnapshot(source, options = {}) {
    if (!source || typeof source !== "object") {
      return null;
    }

    const sceneId = typeof source.sceneId === "string" ? source.sceneId : null;
    const scene = sceneId && typeof options.getSceneById === "function" ? options.getSceneById(sceneId) : null;
    const cloneVisualState = typeof options.cloneVisualState === "function"
      ? options.cloneVisualState
      : deepClonePreviewData;
    const cloneVariables = typeof options.cloneVariables === "function"
      ? options.cloneVariables
      : deepClonePreviewData;
    const choiceOptions = Array.isArray(source.choiceOptions)
      ? source.choiceOptions.map((option) => deepClonePreviewData(option)).filter(Boolean)
      : [];

    return {
      sceneId,
      sceneName: String(source.sceneName ?? scene?.name ?? sceneId ?? "试玩记录"),
      blockIndex: Number.isFinite(Number(source.blockIndex)) ? Number(source.blockIndex) : -1,
      blockId: source.blockId == null ? null : String(source.blockId),
      blockType: source.completed ? "complete" : String(source.blockType ?? "dialogue"),
      block: source.block && typeof source.block === "object" ? deepClonePreviewData(source.block) : null,
      visualState: cloneVisualState(source.visualState),
      variables: cloneVariables(source.variables),
      choiceOptions,
      transitionTargetSceneId:
        source.transitionTargetSceneId == null ? null : String(source.transitionTargetSceneId),
      selectedOptionId: source.selectedOptionId == null ? null : String(source.selectedOptionId),
      resolvedBranchId: source.resolvedBranchId == null ? null : String(source.resolvedBranchId),
      completed: Boolean(source.completed),
    };
  }

  function sanitizeStoredPreviewSession(source, options = {}) {
    if (!source || typeof source !== "object") {
      return null;
    }

    const sanitizeSnapshot = typeof options.sanitizeSnapshot === "function"
      ? options.sanitizeSnapshot
      : (snapshot) => sanitizeStoredPreviewSnapshot(snapshot, options);
    const getSafeSceneId = typeof options.getSafeSceneId === "function"
      ? options.getSafeSceneId
      : (sceneId) => (sceneId == null ? null : String(sceneId));
    const fallbackSceneId = getSafeSceneId(source.startSceneId ?? options.fallbackSceneId);
    const timeline = Array.isArray(source.timeline)
      ? source.timeline.map((snapshot) => sanitizeSnapshot(snapshot)).filter(Boolean)
      : [];

    if (timeline.length === 0) {
      return null;
    }

    return {
      startSceneId: getSafeSceneId(source.startSceneId ?? timeline[0]?.sceneId ?? fallbackSceneId),
      timeline,
      position: clampNumber(Number(source.position) || 0, 0, timeline.length - 1),
    };
  }

  function sanitizeStoredPreviewSaveSlot(source, options = {}) {
    if (!source || typeof source !== "object") {
      return null;
    }

    const sanitizeSession = typeof options.sanitizeSession === "function"
      ? options.sanitizeSession
      : (session) => sanitizeStoredPreviewSession(session, options);
    const session = sanitizeSession(source.session);

    if (!session) {
      return null;
    }

    const nowIso = typeof options.nowIso === "function" ? options.nowIso() : new Date().toISOString();
    return {
      savedAt: source.savedAt ? String(source.savedAt) : nowIso,
      session,
      thumbnailDataUrl: typeof source.thumbnailDataUrl === "string" ? source.thumbnailDataUrl : "",
    };
  }

  global.TonyNaEditorPreviewSave = Object.freeze({
    PREVIEW_SAVE_SHORTCUT_COUNT,
    PREVIEW_SAVE_DIALOG_PAGE_SIZE,
    getSafePreviewSaveSlotIndex,
    getPreviewSaveDialogPageCount,
    getSafePreviewSaveDialogPage,
    getSafePreviewSaveDialogMode,
    createEmptyPreviewSaveSlots,
    deepClonePreviewData,
    sanitizeStoredPreviewSnapshot,
    sanitizeStoredPreviewSession,
    sanitizeStoredPreviewSaveSlot,
  });
})(typeof window !== "undefined" ? window : globalThis);
