export const DEFAULT_RUNTIME_HISTORY_VISIBLE_LIMIT = 24;
export const FILTERED_RUNTIME_HISTORY_VISIBLE_LIMIT = 80;
export const RUNTIME_HISTORY_QUERY_MAX_LENGTH = 80;

function toSafeText(value) {
  return String(value ?? "").trim();
}

function escapeBasicHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export function normalizeRuntimeHistoryQuery(value) {
  return toSafeText(value)
    .slice(0, RUNTIME_HISTORY_QUERY_MAX_LENGTH)
    .normalize("NFKC")
    .toLocaleLowerCase();
}

function normalizeRuntimeHistorySearchText(value) {
  return toSafeText(value).normalize("NFKC").toLocaleLowerCase();
}

export function sanitizeRuntimeHistoryFilters(value = {}) {
  return {
    query: toSafeText(value.query).slice(0, RUNTIME_HISTORY_QUERY_MAX_LENGTH),
    speaker: toSafeText(value.speaker).slice(0, 120),
    voicedOnly: value.voicedOnly === true,
  };
}

export function getRuntimeHistoryStepIndex(session, delta) {
  const offset = Math.trunc(Number(delta) || 0);
  if (!session || !Array.isArray(session.timeline) || !Number.isInteger(session.position) || !offset) {
    return null;
  }
  const nextIndex = session.position + offset;
  return nextIndex >= 0 && nextIndex < session.timeline.length ? nextIndex : null;
}

export function buildRuntimeHistoryRecords(session, options = {}) {
  const timeline = Array.isArray(session?.timeline) ? session.timeline : [];
  const {
    getBlockLabel = (value) => toSafeText(value) || "剧情",
    getVoiceAssetId = () => "",
    stripStoryText = (value) => toSafeText(value),
  } = options;

  return timeline.map((snapshot, index) => {
    const visualState = snapshot?.visualState && typeof snapshot.visualState === "object"
      ? snapshot.visualState
      : {};
    const sceneName = toSafeText(snapshot?.sceneName) || "未命名场景";
    const speakerName = toSafeText(visualState.speakerName) || "系统";
    const text = toSafeText(stripStoryText(visualState.dialogueText));
    const title = snapshot?.completed
      ? "试玩结束"
      : `${getBlockLabel(snapshot?.blockType)} · ${sceneName}`;
    const hasVoice = Boolean(getVoiceAssetId(snapshot));
    const searchText = normalizeRuntimeHistorySearchText(
      [title, sceneName, speakerName, text].filter(Boolean).join("\n")
    );
    return {
      index,
      number: index + 1,
      snapshot,
      title,
      sceneName,
      speakerName,
      text,
      hasVoice,
      searchText,
    };
  });
}

export function collectRuntimeHistorySpeakers(records) {
  const speakers = [];
  const seen = new Set();
  for (const record of Array.isArray(records) ? records : []) {
    const speakerName = toSafeText(record?.speakerName) || "系统";
    if (!seen.has(speakerName)) {
      seen.add(speakerName);
      speakers.push(speakerName);
    }
  }
  return speakers;
}

export function filterRuntimeHistoryRecords(records, filters = {}) {
  const safeFilters = sanitizeRuntimeHistoryFilters(filters);
  const normalizedQuery = normalizeRuntimeHistoryQuery(safeFilters.query);
  return (Array.isArray(records) ? records : []).filter((record) => {
    if (safeFilters.speaker && record?.speakerName !== safeFilters.speaker) {
      return false;
    }
    if (safeFilters.voicedOnly && !record?.hasVoice) {
      return false;
    }
    return !normalizedQuery || normalizeRuntimeHistorySearchText(record?.searchText).includes(normalizedQuery);
  });
}

export function buildRuntimeHistoryView(session, filters = {}, options = {}) {
  const records = buildRuntimeHistoryRecords(session, options);
  const safeFilters = sanitizeRuntimeHistoryFilters(filters);
  const speakers = collectRuntimeHistorySpeakers(records);
  if (safeFilters.speaker && !speakers.includes(safeFilters.speaker)) {
    safeFilters.speaker = "";
  }
  const matchedRecords = filterRuntimeHistoryRecords(records, safeFilters);
  const filterActive = Boolean(safeFilters.query || safeFilters.speaker || safeFilters.voicedOnly);
  const requestedLimit = Number(
    filterActive ? options.filteredLimit : options.defaultLimit
  );
  const fallbackLimit = filterActive
    ? FILTERED_RUNTIME_HISTORY_VISIBLE_LIMIT
    : DEFAULT_RUNTIME_HISTORY_VISIBLE_LIMIT;
  const visibleLimit = Number.isFinite(requestedLimit) && requestedLimit > 0
    ? Math.trunc(requestedLimit)
    : fallbackLimit;
  const visibleRecords = matchedRecords.slice(-visibleLimit);
  return {
    filters: safeFilters,
    records,
    speakers,
    matchedRecords,
    visibleRecords,
    filterActive,
    hiddenMatchCount: Math.max(0, matchedRecords.length - visibleRecords.length),
  };
}

export function createRuntimeHistoryController(options = {}) {
  const {
    escapeHtml = escapeBasicHtml,
    renderEmpty = (value) => `<p>${escapeHtml(value)}</p>`,
  } = options;
  let filters = sanitizeRuntimeHistoryFilters(options.initialFilters);

  function getFilters() {
    return { ...filters };
  }

  function resetFilters() {
    filters = sanitizeRuntimeHistoryFilters();
    return getFilters();
  }

  function updateFromTarget(target) {
    if (!target || typeof target.matches !== "function") {
      return false;
    }
    if (target.matches("[data-history-search]")) {
      filters.query = toSafeText(target.value).slice(0, RUNTIME_HISTORY_QUERY_MAX_LENGTH);
      return true;
    }
    if (target.matches("[data-history-speaker]")) {
      filters.speaker = toSafeText(target.value).slice(0, 120);
      return true;
    }
    if (target.matches("[data-history-voiced]")) {
      filters.voicedOnly = !filters.voicedOnly;
      return true;
    }
    if (target.matches("[data-history-clear]")) {
      resetFilters();
      return true;
    }
    return false;
  }

  function renderToolbar(view) {
    const speakerOptions = [
      `<option value="">全部角色</option>`,
      ...view.speakers.map((speaker) => (
        `<option value="${escapeHtml(speaker)}"${speaker === view.filters.speaker ? " selected" : ""}>${escapeHtml(speaker)}</option>`
      )),
    ].join("");
    const resultText = view.filterActive
      ? `找到 ${view.matchedRecords.length} / ${view.records.length} 条`
      : view.hiddenMatchCount > 0
        ? `显示最近 ${view.visibleRecords.length} 条，共 ${view.records.length} 条`
        : `共 ${view.records.length} 条`;
    const hiddenText = view.hiddenMatchCount > 0
      ? ` · 另有 ${view.hiddenMatchCount} 条较早结果，可继续缩小范围`
      : "";
    return `
      <section class="history-toolbar" aria-label="历史记录筛选">
        <label class="history-search-field">
          <span>搜索台词</span>
          <input
            type="search"
            value="${escapeHtml(view.filters.query)}"
            maxlength="${RUNTIME_HISTORY_QUERY_MAX_LENGTH}"
            placeholder="台词、角色或场景"
            autocomplete="off"
            data-history-search
          />
        </label>
        <label class="history-speaker-field">
          <span>角色</span>
          <select data-history-speaker>${speakerOptions}</select>
        </label>
        <button
          class="history-filter-button${view.filters.voicedOnly ? " is-active" : ""}"
          type="button"
          data-history-voiced
          aria-pressed="${view.filters.voicedOnly ? "true" : "false"}"
        >有语音</button>
        <button
          class="history-filter-button"
          type="button"
          data-history-clear
          ${view.filterActive ? "" : "disabled"}
        >清除</button>
        <p class="history-filter-summary" role="status">${escapeHtml(resultText + hiddenText)}</p>
      </section>
    `;
  }

  function render(session) {
    if (!session || !Array.isArray(session.timeline) || session.timeline.length === 0) {
      return renderEmpty("还没有历史记录。");
    }
    const view = buildRuntimeHistoryView(session, filters, options);
    filters = view.filters;
    const rows = view.visibleRecords.map((record) => `
      <article class="history-row ${record.index === session.position ? "is-selected" : ""}">
        <button class="history-main-button" type="button" data-history-index="${record.index}">
          <strong>${record.number}. ${escapeHtml(record.title)}</strong>
          <p>${escapeHtml(record.text)}</p>
          <div class="meta">${escapeHtml(record.speakerName)}</div>
        </button>
        <div class="history-actions">
          <button
            class="history-voice-button"
            type="button"
            data-history-voice-index="${record.index}"
            ${record.hasVoice ? "" : "disabled"}
          >重播语音</button>
        </div>
      </article>
    `).join("");
    const emptyMessage = view.records.length === 0
      ? "还没有历史记录。"
      : "没有符合当前筛选条件的历史记录。";
    return `${renderToolbar(view)}${rows || renderEmpty(emptyMessage)}`;
  }

  return Object.freeze({
    getFilters,
    resetFilters,
    updateFromTarget,
    render,
  });
}
