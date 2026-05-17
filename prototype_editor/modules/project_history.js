(function attachProjectHistoryTools(global) {
  const HISTORY_KIND_LABELS = Object.freeze({
    manual: "手动检查点",
    baseline: "项目基线",
    auto: "自动快照",
  });

  const HISTORY_KIND_TONES = Object.freeze({
    manual: "good",
    baseline: "soft",
    auto: "warn",
  });

  const HISTORY_FILTER_LABELS = Object.freeze({
    all: "全部版本",
    manual: "只看检查点",
    auto: "只看自动快照",
    baseline: "只看基线",
    current: "只看当前版本",
  });

  const HISTORY_CHANGE_KIND_LABELS = Object.freeze({
    created: "新增",
    removed: "移除",
    changed: "改动",
  });

  function hasOwn(source, key) {
    return Object.prototype.hasOwnProperty.call(source, key);
  }

  function trimHistoryText(value, maxLength = 160) {
    const text = String(value ?? "").trim();
    if (!Number.isFinite(Number(maxLength)) || Number(maxLength) <= 0) {
      return text;
    }
    return text.slice(0, Number(maxLength));
  }

  function getSafeNumber(value, fallback = 0) {
    const numericValue = Number(value);
    return Number.isFinite(numericValue) ? numericValue : fallback;
  }

  function getSafeHistoryKind(kind) {
    return hasOwn(HISTORY_KIND_LABELS, kind) ? kind : "auto";
  }

  function getHistoryKindLabel(kind) {
    return HISTORY_KIND_LABELS[getSafeHistoryKind(kind)] ?? HISTORY_KIND_LABELS.auto;
  }

  function getHistoryKindTone(kind) {
    return HISTORY_KIND_TONES[getSafeHistoryKind(kind)] ?? HISTORY_KIND_TONES.auto;
  }

  function getSafeHistoryFilterMode(value) {
    return hasOwn(HISTORY_FILTER_LABELS, value) ? value : "all";
  }

  function getHistoryFilterLabel(value) {
    return HISTORY_FILTER_LABELS[getSafeHistoryFilterMode(value)] ?? HISTORY_FILTER_LABELS.all;
  }

  function getHistoryChangeKindLabel(kind) {
    return hasOwn(HISTORY_CHANGE_KIND_LABELS, kind) ? HISTORY_CHANGE_KIND_LABELS[kind] : HISTORY_CHANGE_KIND_LABELS.changed;
  }

  function getSafeProjectSessionRecovery(recovery) {
    if (!recovery || typeof recovery !== "object") {
      return {
        noticeActive: false,
        lastUnexpectedExitAt: "",
        lastUnexpectedExitStartedAt: "",
        lastEndedReason: "",
        message: "",
      };
    }

    return {
      noticeActive: Boolean(recovery.noticeActive),
      lastUnexpectedExitAt: trimHistoryText(recovery.lastUnexpectedExitAt, 80),
      lastUnexpectedExitStartedAt: trimHistoryText(recovery.lastUnexpectedExitStartedAt, 80),
      lastEndedReason: trimHistoryText(recovery.lastEndedReason, 80),
      message: trimHistoryText(recovery.message, 240),
    };
  }

  function sanitizeHistorySnapshot(snapshot) {
    if (!snapshot || typeof snapshot !== "object") {
      return null;
    }

    const index = getSafeNumber(snapshot.index, -1);
    const label = trimHistoryText(snapshot.label, 120) || "未命名快照";
    return {
      ...snapshot,
      index,
      kind: getSafeHistoryKind(snapshot.kind),
      label,
      createdAt: trimHistoryText(snapshot.createdAt, 80),
      isCurrent: Boolean(snapshot.isCurrent),
    };
  }

  function sanitizeHistorySnapshots(snapshots) {
    return (Array.isArray(snapshots) ? snapshots : [])
      .map((snapshot) => sanitizeHistorySnapshot(snapshot))
      .filter(Boolean);
  }

  function getSafeProjectHistory(history) {
    if (!history || typeof history !== "object") {
      return {
        totalSnapshots: 0,
        currentIndex: -1,
        canUndo: false,
        canRedo: false,
        currentSnapshot: null,
        previousSnapshot: null,
        nextSnapshot: null,
        recentSnapshots: [],
        timelineSnapshots: [],
      };
    }

    const recentSnapshots = sanitizeHistorySnapshots(history.recentSnapshots);
    const timelineSnapshots = sanitizeHistorySnapshots(history.timelineSnapshots);
    const totalFallback = timelineSnapshots.length || recentSnapshots.length;
    const totalSnapshots = Math.max(0, getSafeNumber(history.totalSnapshots, totalFallback));
    const currentIndex = getSafeNumber(history.currentIndex, -1);

    return {
      totalSnapshots,
      currentIndex,
      canUndo: Boolean(history.canUndo),
      canRedo: Boolean(history.canRedo),
      currentSnapshot:
        sanitizeHistorySnapshot(history.currentSnapshot) ??
        timelineSnapshots.find((snapshot) => snapshot.isCurrent) ??
        null,
      previousSnapshot: sanitizeHistorySnapshot(history.previousSnapshot),
      nextSnapshot: sanitizeHistorySnapshot(history.nextSnapshot),
      recentSnapshots,
      timelineSnapshots,
    };
  }

  function getHistorySnapshotByIndex(targetIndex, history) {
    const safeHistory = getSafeProjectHistory(history);
    const numericIndex = Number(targetIndex);
    if (!Number.isFinite(numericIndex)) {
      return null;
    }
    return safeHistory.timelineSnapshots.find((snapshot) => Number(snapshot.index) === numericIndex) ?? null;
  }

  function getPreviousHistorySnapshot(history) {
    const safeHistory = getSafeProjectHistory(history);
    return safeHistory.previousSnapshot ?? getHistorySnapshotByIndex(Number(safeHistory.currentIndex) - 1, safeHistory);
  }

  function normalizeHistorySearchQuery(query) {
    return trimHistoryText(query, 240).toLowerCase();
  }

  function formatHistorySnapshotDate(snapshot, formatDate) {
    if (typeof formatDate !== "function") {
      return trimHistoryText(snapshot?.createdAt, 80);
    }

    try {
      return formatDate(snapshot?.createdAt);
    } catch (error) {
      return trimHistoryText(snapshot?.createdAt, 80);
    }
  }

  function buildHistorySnapshotSearchText(snapshot, options = {}) {
    const safeSnapshot = sanitizeHistorySnapshot(snapshot);
    if (!safeSnapshot) {
      return "";
    }

    return [
      safeSnapshot.label,
      getHistoryKindLabel(safeSnapshot.kind),
      formatHistorySnapshotDate(safeSnapshot, options.formatDate),
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
  }

  function doesHistorySnapshotMatchFilter(snapshot, filterMode = "all") {
    const safeSnapshot = sanitizeHistorySnapshot(snapshot);
    if (!safeSnapshot) {
      return false;
    }

    const safeFilter = getSafeHistoryFilterMode(filterMode);
    if (safeFilter === "all") {
      return true;
    }
    if (safeFilter === "current") {
      return safeSnapshot.isCurrent;
    }
    return safeSnapshot.kind === safeFilter;
  }

  function doesHistorySnapshotMatchSearch(snapshot, query = "", options = {}) {
    const safeQuery = normalizeHistorySearchQuery(query);
    if (!safeQuery) {
      return true;
    }
    return buildHistorySnapshotSearchText(snapshot, options).includes(safeQuery);
  }

  function getFilteredHistorySnapshots(history, options = {}) {
    const safeHistory = getSafeProjectHistory(history);
    const filterMode = getSafeHistoryFilterMode(options.filterMode);
    const query = normalizeHistorySearchQuery(options.searchQuery);

    return safeHistory.timelineSnapshots.filter(
      (snapshot) =>
        doesHistorySnapshotMatchFilter(snapshot, filterMode) &&
        doesHistorySnapshotMatchSearch(snapshot, query, { formatDate: options.formatDate })
    );
  }

  function formatHistoryRestorePreview(preview, options = {}) {
    if (!preview || typeof preview !== "object") {
      return "恢复后会把项目回到你选中的那个时间点。";
    }

    const changedFileCount = getSafeNumber(preview.changedFileCount, 0);
    if (changedFileCount <= 0) {
      return "当前版本和目标版本没有差异。";
    }

    const itemLimit = Math.max(0, getSafeNumber(options.itemLimit, 6));
    const changedItems = Array.isArray(preview.changedItems) ? preview.changedItems : [];
    const detailLines = changedItems
      .slice(0, itemLimit)
      .map((item) => `- ${trimHistoryText(item?.label ?? item?.path ?? "未知内容", 140)}（${getHistoryChangeKindLabel(item?.kind)}）`);
    const hiddenCount = Math.max(changedItems.length - detailLines.length, 0);
    return [
      `恢复后会影响 ${changedFileCount} 处内容。`,
      detailLines.length > 0 ? "" : null,
      ...detailLines,
      hiddenCount > 0 ? `- 另外还有 ${hiddenCount} 处变化` : null,
    ]
      .filter(Boolean)
      .join("\n");
  }

  function buildProjectRecoveryPromptKey(projectId, recovery) {
    const safeRecovery = getSafeProjectSessionRecovery(recovery);
    return `${trimHistoryText(projectId || "unknown", 120)}:${
      safeRecovery.lastUnexpectedExitAt || safeRecovery.lastUnexpectedExitStartedAt || "none"
    }`;
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function formatDate(value) {
    if (!value) {
      return "未知";
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return String(value);
    }

    return date.toLocaleString("zh-CN");
  }

  function getDashboardTaskToneClass(tone) {
    if (tone === "danger") {
      return "danger-text";
    }
    if (tone === "warn") {
      return "warn-text";
    }
    if (tone === "good") {
      return "good-text";
    }
    return "";
  }

  function renderHistorySnapshotCard(snapshot, options = {}) {
    const safeSnapshot = sanitizeHistorySnapshot(snapshot);
    if (!safeSnapshot) {
      return "";
    }

    const escape = typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtml;
    const format = typeof options.formatDate === "function" ? options.formatDate : formatDate;
    const getToneClass =
      typeof options.getDashboardTaskToneClass === "function"
        ? options.getDashboardTaskToneClass
        : getDashboardTaskToneClass;
    const isCompact = options.compact === true;
    const isCurrent = Boolean(safeSnapshot.isCurrent);
    const canRestore = options.allowRestore !== false && !isCurrent;
    const canRelabel = options.allowRelabel !== false;
    const title = safeSnapshot.label || "未命名快照";
    const metaLabel = `${getHistoryKindLabel(safeSnapshot.kind)} · 第 ${Number(safeSnapshot.index ?? 0) + 1} 份`;

    return `
    <article class="history-card ${isCurrent ? "is-current" : ""} ${safeSnapshot.kind === "manual" ? "is-manual" : ""} ${
      safeSnapshot.kind === "baseline" ? "is-baseline" : ""
    }">
      <div class="history-card-top">
        <div class="history-card-title">
          <div class="pill-row">
            <span class="issue-tag ${getToneClass(getHistoryKindTone(safeSnapshot.kind))}">${escape(
              getHistoryKindLabel(safeSnapshot.kind)
            )}</span>
            ${isCurrent ? '<span class="issue-tag is-good">当前版本</span>' : ""}
          </div>
          <strong>${escape(title)}</strong>
        </div>
        <span class="history-card-time">${escape(format(safeSnapshot.createdAt))}</span>
      </div>
      <div class="history-card-meta">${escape(metaLabel)}</div>
      <div class="history-card-actions">
        ${
          canRestore
            ? `<button class="toolbar-button ${isCompact ? "" : "toolbar-button-primary"}" data-action="restore-project-history" data-history-index="${Number(
                safeSnapshot.index ?? -1
              )}">
                恢复到这里
              </button>`
            : '<button class="toolbar-button" type="button" disabled>当前就在这里</button>'
        }
        ${
          canRelabel
            ? `<button class="toolbar-button" data-action="rename-project-history-snapshot" data-history-index="${Number(
                safeSnapshot.index ?? -1
              )}">
                改备注
              </button>`
            : ""
        }
      </div>
    </article>
  `;
  }

  function renderHistoryTimeline(history, options = {}) {
    const safeHistory = getSafeProjectHistory(history);
    const snapshots = Array.isArray(options.filteredSnapshots)
      ? sanitizeHistorySnapshots(options.filteredSnapshots)
      : getFilteredHistorySnapshots(safeHistory, options);

    if (snapshots.length === 0) {
      return safeHistory.totalSnapshots > 0
        ? '<div class="history-empty">当前筛选下还没有命中的快照，可以换个关键词或切回“全部版本”。</div>'
        : '<div class="history-empty">这个项目还没有可显示的快照时间线。</div>';
    }

    return snapshots.map((snapshot) => renderHistorySnapshotCard(snapshot, options)).join("");
  }

  global.CanvasiaEditorProjectHistory = Object.freeze({
    HISTORY_KIND_LABELS,
    HISTORY_KIND_TONES,
    HISTORY_FILTER_LABELS,
    HISTORY_CHANGE_KIND_LABELS,
    trimHistoryText,
    getSafeHistoryKind,
    getHistoryKindLabel,
    getHistoryKindTone,
    getSafeHistoryFilterMode,
    getHistoryFilterLabel,
    getHistoryChangeKindLabel,
    getSafeProjectSessionRecovery,
    sanitizeHistorySnapshot,
    sanitizeHistorySnapshots,
    getSafeProjectHistory,
    getHistorySnapshotByIndex,
    getPreviousHistorySnapshot,
    normalizeHistorySearchQuery,
    buildHistorySnapshotSearchText,
    doesHistorySnapshotMatchFilter,
    doesHistorySnapshotMatchSearch,
    getFilteredHistorySnapshots,
    formatHistoryRestorePreview,
    buildProjectRecoveryPromptKey,
    renderHistorySnapshotCard,
    renderHistoryTimeline,
  });
})(typeof window !== "undefined" ? window : globalThis);
