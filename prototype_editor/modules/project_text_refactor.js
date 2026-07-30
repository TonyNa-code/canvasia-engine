(function attachProjectTextRefactorTools(global) {
  const PROJECT_TEXT_REFACTOR_SCOPE_OPTIONS = Object.freeze([
    Object.freeze({ id: "dialogue", label: "角色台词", hint: "角色说出的正文" }),
    Object.freeze({ id: "narration", label: "旁白", hint: "叙述与环境文字" }),
    Object.freeze({ id: "choice", label: "选项文案", hint: "玩家看到的选项" }),
    Object.freeze({ id: "input", label: "输入提示", hint: "命名等输入引导" }),
    Object.freeze({ id: "scene_name", label: "场景名", hint: "场景树与标题" }),
    Object.freeze({ id: "chapter_name", label: "章节名", hint: "章节标题" }),
  ]);
  const DEFAULT_PROJECT_TEXT_REFACTOR_SCOPES = Object.freeze(["dialogue", "narration", "choice"]);

  function fallbackEscapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function fallbackTruncateText(value, maxLength = 120) {
    const text = String(value ?? "");
    return text.length > maxLength ? `${text.slice(0, Math.max(0, maxLength - 1))}…` : text;
  }

  function getHelper(helpers, key, fallback) {
    return typeof helpers?.[key] === "function" ? helpers[key] : fallback;
  }

  function createProjectTextRefactorState(overrides = {}) {
    const state = {
      findText: "",
      replaceText: "",
      scopes: [...DEFAULT_PROJECT_TEXT_REFACTOR_SCOPES],
      caseSensitive: true,
      includeTranslations: false,
      loading: false,
      error: "",
      report: null,
      lastAppliedReport: null,
      ...overrides,
    };
    state.scopes = normalizeProjectTextRefactorScopes(state.scopes);
    return state;
  }

  function normalizeProjectTextRefactorScopes(value) {
    const allowed = new Set(PROJECT_TEXT_REFACTOR_SCOPE_OPTIONS.map((option) => option.id));
    const scopes = [];
    (Array.isArray(value) ? value : DEFAULT_PROJECT_TEXT_REFACTOR_SCOPES).forEach((scope) => {
      const safeScope = String(scope ?? "").trim();
      if (allowed.has(safeScope) && !scopes.includes(safeScope)) {
        scopes.push(safeScope);
      }
    });
    return scopes;
  }

  function buildProjectTextRefactorPayload(state = {}) {
    return {
      findText: String(state.findText ?? ""),
      replaceText: String(state.replaceText ?? ""),
      scopes: normalizeProjectTextRefactorScopes(state.scopes),
      caseSensitive: state.caseSensitive !== false,
      includeTranslations: Boolean(state.includeTranslations),
    };
  }

  function getProjectTextRefactorValidationError(state = {}) {
    const payload = buildProjectTextRefactorPayload(state);
    if (!payload.findText.trim()) {
      return "先填写要查找的文字。";
    }
    if (!payload.scopes.length) {
      return "至少选择一种要处理的文字范围。";
    }
    const sameText = payload.caseSensitive
      ? payload.findText === payload.replaceText
      : payload.findText.toLocaleLowerCase() === payload.replaceText.toLocaleLowerCase();
    if (sameText) {
      return "查找文字和替换文字相同。";
    }
    return "";
  }

  function renderProjectTextRefactorPanel(state = {}, helpers = {}) {
    const escapeHtml = getHelper(helpers, "escapeHtml", fallbackEscapeHtml);
    const payload = buildProjectTextRefactorPayload(state);
    return `
      <section class="text-refactor-workbench" aria-labelledby="projectTextRefactorTitle">
        <div class="text-refactor-heading">
          <div>
            <span class="eyebrow">SCRIPT REFACTOR</span>
            <h3 id="projectTextRefactorTitle">剧情重构台</h3>
            <p>跨章节改术语、称呼和选项文案。先预览，再一次写入；每次执行都会进入可撤销的项目历史。</p>
          </div>
          <span class="text-refactor-safety-mark">纯文字 · 不改 ID</span>
        </div>

        <div class="text-refactor-layout">
          <div class="text-refactor-form">
            <div class="text-refactor-input-grid">
              <label>
                <span>查找</span>
                <input id="projectTextRefactorFindInput" type="text" maxlength="240" value="${escapeHtml(payload.findText)}" placeholder="例如：旧校舍" autocomplete="off" />
              </label>
              <label>
                <span>替换为</span>
                <input id="projectTextRefactorReplaceInput" type="text" maxlength="2000" value="${escapeHtml(payload.replaceText)}" placeholder="留空表示删除匹配文字" autocomplete="off" />
              </label>
            </div>

            <fieldset class="text-refactor-scope-fieldset">
              <legend>处理范围</legend>
              <div class="text-refactor-scope-grid">
                ${PROJECT_TEXT_REFACTOR_SCOPE_OPTIONS.map((option) => `
                  <label class="text-refactor-scope-option ${payload.scopes.includes(option.id) ? "is-active" : ""}">
                    <input
                      type="checkbox"
                      data-text-refactor-scope="${escapeHtml(option.id)}"
                      ${payload.scopes.includes(option.id) ? "checked" : ""}
                    />
                    <span><strong>${escapeHtml(option.label)}</strong><small>${escapeHtml(option.hint)}</small></span>
                  </label>
                `).join("")}
              </div>
            </fieldset>

            <div class="text-refactor-options">
              <label>
                <input id="projectTextRefactorCaseSensitiveInput" type="checkbox" ${payload.caseSensitive ? "checked" : ""} />
                <span>区分大小写</span>
              </label>
              <label>
                <input id="projectTextRefactorTranslationsInput" type="checkbox" ${payload.includeTranslations ? "checked" : ""} />
                <span>同时处理已有译文</span>
              </label>
            </div>

            <div class="action-row text-refactor-actions">
              <button type="button" class="toolbar-button toolbar-button-primary" data-action="preview-project-text-refactor" ${state.loading ? "disabled" : ""}>
                ${state.loading ? "正在检查..." : "预览全部命中"}
              </button>
              <button
                id="projectTextRefactorApplyButton"
                type="button"
                class="toolbar-button"
                data-action="apply-project-text-refactor"
                ${state.loading || !state.report?.totalReplacements ? "disabled" : ""}
              >
                ${state.report?.totalReplacements ? `确认替换 ${Number(state.report.totalReplacements)} 处` : "确认后再替换"}
              </button>
              <button type="button" class="toolbar-button" data-action="reset-project-text-refactor" ${state.loading ? "disabled" : ""}>清空</button>
            </div>
          </div>

          <div id="projectTextRefactorFeedback" class="text-refactor-feedback" aria-live="polite">
            ${renderProjectTextRefactorFeedback(state, helpers)}
          </div>
        </div>
      </section>
    `;
  }

  function renderProjectTextRefactorFeedback(state = {}, helpers = {}) {
    const escapeHtml = getHelper(helpers, "escapeHtml", fallbackEscapeHtml);
    if (state.loading) {
      return `
        <div class="text-refactor-empty is-loading">
          <span class="text-refactor-pulse" aria-hidden="true"></span>
          <strong>正在逐章核对</strong>
          <p>只读取当前项目文字，不会在预览阶段写入文件。</p>
        </div>
      `;
    }
    if (state.error) {
      return `
        <div class="text-refactor-empty is-error">
          <strong>这次还不能继续</strong>
          <p>${escapeHtml(state.error)}</p>
        </div>
      `;
    }
    if (state.report) {
      return renderProjectTextRefactorReport(state.report, helpers);
    }
    if (state.lastAppliedReport) {
      const report = state.lastAppliedReport;
      return `
        <div class="text-refactor-receipt">
          <span class="issue-tag good-text">已写入项目历史</span>
          <strong>${escapeHtml(`已替换 ${Number(report.totalReplacements ?? 0)} 处文字`)}</strong>
          <p>${escapeHtml(`影响 ${Number(report.changedChapterCount ?? 0)} 个章节、${Number(report.changedSceneCount ?? 0)} 个场景；如需反悔，可直接使用顶部“撤销”。`)}</p>
        </div>
      `;
    }
    return `
      <div class="text-refactor-empty">
        <strong>预览区</strong>
        <p>这里会逐条列出修改前后。没有预览结果时，执行按钮不会开放。</p>
      </div>
    `;
  }

  function renderProjectTextRefactorReport(report = {}, helpers = {}) {
    const escapeHtml = getHelper(helpers, "escapeHtml", fallbackEscapeHtml);
    const truncateText = getHelper(helpers, "truncateText", fallbackTruncateText);
    const matches = Array.isArray(report.matches) ? report.matches : [];
    const visibleMatches = matches.slice(0, 28);
    const hiddenCount = Math.max(
      0,
      Number(report.truncatedMatchCount ?? 0) + Math.max(0, matches.length - visibleMatches.length)
    );
    if (!Number(report.totalReplacements ?? 0)) {
      return `
        <div class="text-refactor-empty">
          <strong>没有命中</strong>
          <p>当前范围里没有找到这段文字。可以检查大小写，或勾选更多处理范围。</p>
        </div>
      `;
    }

    return `
      <div class="text-refactor-report">
        <div class="text-refactor-metrics">
          <span><strong>${Number(report.totalReplacements ?? 0)}</strong><small>替换处数</small></span>
          <span><strong>${Number(report.changedChapterCount ?? 0)}</strong><small>涉及章节</small></span>
          <span><strong>${Number(report.changedSceneCount ?? 0)}</strong><small>涉及场景</small></span>
        </div>
        <div class="text-refactor-match-list">
          ${visibleMatches.map((match) => `
            <article class="text-refactor-match-card">
              <div class="text-refactor-match-meta">
                <span>${escapeHtml(match.fieldLabel ?? match.scopeLabel ?? "文字")}${match.language ? ` · ${escapeHtml(match.language)}` : ""}</span>
                <small>${escapeHtml([match.chapterName, match.sceneName].filter(Boolean).join(" / "))}</small>
              </div>
              <div class="text-refactor-diff">
                <del>${escapeHtml(truncateText(match.before, 150))}</del>
                <ins>${escapeHtml(truncateText(match.after, 150)) || "（空）"}</ins>
              </div>
              ${match.sceneId ? `
                <button
                  type="button"
                  class="text-link"
                  data-action="${match.blockId ? "open-character-line" : "open-scene-from-map"}"
                  data-scene-id="${escapeHtml(match.sceneId)}"
                  ${match.blockId ? `data-block-id="${escapeHtml(match.blockId)}"` : ""}
                >定位原文</button>
              ` : ""}
            </article>
          `).join("")}
        </div>
        ${hiddenCount > 0 ? `<p class="helper-text">另外还有 ${hiddenCount} 条命中未展开，但会按同一规则处理。</p>` : ""}
      </div>
    `;
  }

  global.CanvasiaEditorProjectTextRefactor = Object.freeze({
    PROJECT_TEXT_REFACTOR_SCOPE_OPTIONS,
    DEFAULT_PROJECT_TEXT_REFACTOR_SCOPES,
    createProjectTextRefactorState,
    normalizeProjectTextRefactorScopes,
    buildProjectTextRefactorPayload,
    getProjectTextRefactorValidationError,
    renderProjectTextRefactorPanel,
    renderProjectTextRefactorFeedback,
    renderProjectTextRefactorReport,
  });
})(typeof window !== "undefined" ? window : globalThis);
