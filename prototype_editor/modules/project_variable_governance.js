(function attachProjectVariableGovernanceTools(global) {
  const DEFAULT_USAGE = Object.freeze({
    total: 0,
    setCount: 0,
    addCount: 0,
    inputCount: 0,
    textReferenceCount: 0,
    conditionCount: 0,
    choiceEffectCount: 0,
    locations: [],
    references: [],
  });

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function getCallback(options, name, fallback) {
    return typeof options?.[name] === "function" ? options[name] : fallback;
  }

  function getUsage(usageMap, variableId) {
    return usageMap?.get?.(variableId) ?? DEFAULT_USAGE;
  }

  function buildGovernanceItems(variables = [], usageMap = new Map(), options = {}) {
    const getDraft = getCallback(options, "getDraft", () => null);
    const buildDraftModel = getCallback(options, "buildDraftModel", (variable) => variable);
    const getRangeIssues = getCallback(options, "getRangeIssues", () => []);
    const getIdIssue = getCallback(options, "getIdIssue", () => "");
    const getSafeStatus = getCallback(options, "getSafeStatus", (status) => status || "active");

    return variables.map((variable) => {
      const draft = getDraft(variable.id);
      const renderVariable = buildDraftModel(variable);
      const usage = getUsage(usageMap, variable.id);
      const rangeIssues = getRangeIssues(renderVariable);
      const idIssue = getIdIssue(renderVariable.id, variable.id);
      const status = getSafeStatus(renderVariable.status);
      const issues = [...rangeIssues];
      if (idIssue) {
        issues.push(idIssue);
      }
      if (status === "deprecated" && usage.total > 0) {
        issues.push("废弃变量仍被引用");
      }
      return {
        variable,
        renderVariable,
        usage,
        issues,
        status,
        hasDraft: Boolean(draft),
      };
    });
  }

  function isMatchingFilter(item, filterMode, options = {}) {
    if (filterMode === "referenced") return item.usage.total > 0;
    if (filterMode === "unused") return item.usage.total === 0;
    if (filterMode === "risky") return item.issues.length > 0;
    if (filterMode === "draft") return item.hasDraft;
    if (["active", "reserved", "deprecated"].includes(filterMode)) return item.status === filterMode;
    if (["number", "boolean", "string"].includes(filterMode)) return item.renderVariable.type === filterMode;
    if (["save", "persistent"].includes(filterMode)) {
      const getSafeScope = getCallback(options, "getSafeScope", (scope) => scope || "save");
      return getSafeScope(item.renderVariable.scope) === filterMode;
    }
    return true;
  }

  function getGovernanceScore(items = []) {
    if (items.length === 0) {
      return 100;
    }
    const riskCount = items.filter((item) => item.issues.length > 0).length;
    const unusedCount = items.filter((item) => item.usage.total === 0 && item.status !== "reserved").length;
    const draftCount = items.filter((item) => item.hasDraft).length;
    return Math.max(0, Math.min(100, 100 - riskCount * 18 - unusedCount * 4 - draftCount * 2));
  }

  function renderGovernancePanel(items = [], options = {}) {
    const escape = getCallback(options, "escapeHtml", escapeHtml);
    const renderMetricCard = getCallback(options, "renderMetricCard", () => "");
    const renderEmpty = getCallback(options, "renderEmpty", () => "");
    const getVariableTypeLabel = getCallback(options, "getVariableTypeLabel", (type) => type);
    const isPersistentVariable = getCallback(
      options,
      "isPersistentVariable",
      (variable) => variable?.scope === "persistent"
    );
    const totalCount = items.length;
    const referencedCount = items.filter((item) => item.usage.total > 0).length;
    const unusedCount = items.filter((item) => item.usage.total === 0).length;
    const riskItems = items.filter((item) => item.issues.length > 0);
    const draftCount = items.filter((item) => item.hasDraft).length;
    const reservedCount = items.filter((item) => item.status === "reserved").length;
    const deprecatedCount = items.filter((item) => item.status === "deprecated").length;
    const persistentCount = items.filter((item) => isPersistentVariable(item.renderVariable)).length;
    const score = getGovernanceScore(items);
    const hotItems = items
      .filter((item) => item.usage.total > 0)
      .sort((left, right) => right.usage.total - left.usage.total)
      .slice(0, 3);
    const unusedPreview = items.filter((item) => item.usage.total === 0).slice(0, 4);

    return `
      <section class="detail-card">
        <div class="panel-heading">
          <div>
            <strong>变量治理雷达</strong>
            <p class="helper-text">用项目级视角看变量健康度：风险越少、废弃变量越少，后期做分支和导出就越稳。</p>
          </div>
          <span class="badge badge-soft">Health ${score}</span>
        </div>
        <div class="route-summary-strip beginner-guide-metrics">
          ${renderMetricCard("健康分", score, "范围风险、草稿和未引用变量越少越高")}
          ${renderMetricCard("引用覆盖", `${referencedCount} / ${totalCount}`, "至少被一张剧情卡片使用")}
          ${renderMetricCard("未引用", unusedCount, "可清理，也可能是预留变量")}
          ${renderMetricCard("风险变量", riskItems.length, "ID、范围或默认值需要处理")}
          ${renderMetricCard("草稿中", draftCount, "已修改但还没保存")}
          ${renderMetricCard("跨周目", persistentCount, "新游戏、旧存档和回退都不会让它倒退")}
          ${renderMetricCard("预留 / 废弃", `${reservedCount} / ${deprecatedCount}`, "预留不会被自动清理；废弃仍引用会报风险")}
        </div>
        <div class="playback-setting-grid dialog-config-grid">
          <article class="detail-card">
            <strong>热点变量</strong>
            <div class="detail-stack">
              ${hotItems.length > 0
                ? hotItems.map((item) => `
                    <div class="detail-row">
                      <label>${escape(item.renderVariable.name || item.variable.id)}</label>
                      <div class="value">${item.usage.total} 处引用</div>
                    </div>`).join("")
                : renderEmpty("还没有变量被剧情卡片引用。")}
            </div>
          </article>
          <article class="detail-card">
            <strong>优先处理</strong>
            <div class="detail-stack">
              ${riskItems.length > 0
                ? riskItems.slice(0, 4).map((item) => `
                    <div class="detail-row">
                      <label>${escape(item.renderVariable.name || item.variable.id)}</label>
                      <div class="value">${escape(item.issues.join("、"))}</div>
                    </div>`).join("")
                : renderEmpty("变量 ID、默认值和范围目前没有明显风险。")}
            </div>
          </article>
          <article class="detail-card">
            <strong>未引用预览</strong>
            <div class="detail-stack">
              ${unusedPreview.length > 0
                ? unusedPreview.map((item) => `
                    <div class="detail-row">
                      <label>${escape(item.renderVariable.name || item.variable.id)}</label>
                      <div class="value">${escape(getVariableTypeLabel(item.renderVariable.type))}</div>
                    </div>`).join("")
                : renderEmpty("没有未引用变量，逻辑库很干净。")}
            </div>
          </article>
        </div>
      </section>
    `;
  }

  function renderFilterButtons(items, filterMode, options = {}) {
    const escape = getCallback(options, "escapeHtml", escapeHtml);
    const filterLabels = options.filterLabels ?? {};
    return Object.entries(filterLabels)
      .map(([mode, label]) => {
        const count = items.filter((item) => isMatchingFilter(item, mode, options)).length;
        return `
          <button
            type="button"
            class="toolbar-button ${filterMode === mode ? "toolbar-button-primary" : ""}"
            data-action="set-project-variable-filter"
            data-variable-filter-mode="${mode}"
          >
            ${escape(label)} · ${count}
          </button>
        `;
      })
      .join("");
  }

  function renderLibraryPanel(context = {}, options = {}) {
    const escape = getCallback(options, "escapeHtml", escapeHtml);
    const renderMetricCard = getCallback(options, "renderMetricCard", () => "");
    const renderEmpty = getCallback(options, "renderEmpty", () => "");
    const renderEditorRow = getCallback(options, "renderEditorRow", () => "");
    const getVariableTypeLabel = getCallback(options, "getVariableTypeLabel", (type) => type);
    const getSafeScope = getCallback(options, "getSafeScope", (scope) => scope || "save");
    const getSafeStatus = getCallback(options, "getSafeStatus", (status) => status || "active");
    const isPersistentVariable = getCallback(
      options,
      "isPersistentVariable",
      (variable) => variable?.scope === "persistent"
    );
    const getRangeIssues = getCallback(options, "getRangeIssues", () => []);
    const variables = Array.isArray(context.variables) ? context.variables : [];
    const query = String(context.searchQuery ?? "").trim().toLowerCase();
    const filterMode = String(context.filterMode ?? "all");
    const usageMap = context.usageMap ?? new Map();
    const governanceItems = Array.isArray(context.governanceItems) ? context.governanceItems : [];
    const filterLabels = options.filterLabels ?? {};
    const scopeLabels = options.scopeLabels ?? {};
    const statusLabels = options.statusLabels ?? {};
    const filteredItems = governanceItems.filter((item) => {
      const { variable, renderVariable } = item;
      if (!isMatchingFilter(item, filterMode, options)) {
        return false;
      }
      if (!query) {
        return true;
      }
      return [
        renderVariable.id,
        renderVariable.name,
        renderVariable.group,
        renderVariable.description,
        variable.id,
        variable.name,
        getVariableTypeLabel(renderVariable.type),
        scopeLabels[getSafeScope(renderVariable.scope)],
        statusLabels[getSafeStatus(renderVariable.status)],
      ].some((value) => String(value ?? "").toLowerCase().includes(query));
    });
    const referencedCount = variables.filter((variable) => getUsage(usageMap, variable.id).total > 0).length;
    const unusedCount = Math.max(variables.length - referencedCount, 0);
    const riskCount = variables.filter((variable) => getRangeIssues(variable).length > 0).length;
    const persistentCount = variables.filter((variable) => isPersistentVariable(variable)).length;
    const typeCount = (type) => variables.filter((variable) => variable.type === type).length;

    return `
      <section class="detail-card dialog-config-card" id="projectVariableLibraryPanel">
        <div class="panel-heading">
          <div>
            <strong>变量库管理台</strong>
            <p class="helper-text">集中管理好感度、路线标记、开关和计数器。这里保存后，剧情条件、选项效果、网页包和原生 Runtime 会一起使用同一套变量定义。</p>
          </div>
          <span class="badge badge-soft">Logic Core</span>
        </div>
        <div class="route-summary-strip beginner-guide-metrics">
          ${renderMetricCard("变量总数", variables.length, "项目可用的逻辑状态")}
          ${renderMetricCard("数字变量", typeCount("number"), "好感度、分数和进度")}
          ${renderMetricCard("跨周目记忆", persistentCount, "通关标记、周目继承和隐藏路线")}
          ${renderMetricCard("已引用", referencedCount, "被剧情卡片实际使用")}
          ${renderMetricCard("未引用", unusedCount, "可能是废弃变量或预留变量")}
          ${renderMetricCard("待整理", riskCount, "范围或默认值需要注意")}
        </div>
        ${renderGovernancePanel(governanceItems, options)}
        <div class="asset-search-row story-tree-filter-row">
          <label class="asset-search-field">
            <span class="sr-only">搜索变量</span>
            <input
              id="projectVariableSearchInput"
              type="search"
              value="${escape(context.searchQuery ?? "")}"
              placeholder="搜变量名、ID 或类型"
            />
          </label>
          <button class="toolbar-button" data-action="add-project-variable" data-variable-type="number">新增数字</button>
          <button class="toolbar-button" data-action="add-project-variable" data-variable-type="boolean">新增开关</button>
          <button class="toolbar-button" data-action="add-project-variable" data-variable-type="string">新增文本</button>
          <button class="toolbar-button" data-action="repair-project-variable-ranges">一键整理范围</button>
          <button class="toolbar-button" data-action="delete-unused-project-variables">清理未引用</button>
          <button class="toolbar-button" data-action="export-project-variable-report">导出治理报告</button>
          <button class="toolbar-button" data-action="create-starter-variables">补齐基础变量包</button>
        </div>
        <div class="story-filter-chip-row">
          ${renderFilterButtons(governanceItems, filterMode, options)}
        </div>
        <div class="detail-stack">
          ${filteredItems.length > 0
            ? filteredItems.map(({ variable }) => renderEditorRow(variable, getUsage(usageMap, variable.id))).join("")
            : renderEmpty(
                variables.length > 0
                  ? `当前「${filterLabels[filterMode] ?? filterMode}」视图没有命中变量。`
                  : "这个项目还没有变量，可以先新增一个数字变量或补齐基础变量包。"
              )}
        </div>
      </section>
    `;
  }

  function buildAuditReport(items = [], context = {}, options = {}) {
    const getVariableTypeLabel = getCallback(options, "getVariableTypeLabel", (type) => type);
    const getSafeScope = getCallback(options, "getSafeScope", (scope) => scope || "save");
    const getDefaultInputValue = getCallback(options, "getDefaultInputValue", () => "");
    const isPersistentVariable = getCallback(
      options,
      "isPersistentVariable",
      (variable) => variable?.scope === "persistent"
    );
    const scopeLabels = options.scopeLabels ?? {};
    const statusLabels = options.statusLabels ?? {};
    const projectTitle = context.projectTitle ?? "未命名项目";
    const generatedAt = context.generatedAt ?? new Date().toLocaleString();
    const score = getGovernanceScore(items);
    const referencedCount = items.filter((item) => item.usage.total > 0).length;
    const unusedItems = items.filter((item) => item.usage.total === 0);
    const riskItems = items.filter((item) => item.issues.length > 0);
    const draftItems = items.filter((item) => item.hasDraft);
    const persistentItems = items.filter((item) => isPersistentVariable(item.renderVariable));
    const hotItems = [...items]
      .filter((item) => item.usage.total > 0)
      .sort((left, right) => right.usage.total - left.usage.total);
    const lines = [
      "Canvasia Engine 变量治理报告",
      `项目：${projectTitle}`,
      `生成时间：${generatedAt}`,
      "",
      "一、总体概览",
      `- 健康分：${score}`,
      `- 变量总数：${items.length}`,
      `- 已引用变量：${referencedCount}`,
      `- 未引用变量：${unusedItems.length}`,
      `- 风险变量：${riskItems.length}`,
      `- 草稿变量：${draftItems.length}`,
      `- 跨周目记忆：${persistentItems.length}`,
      "",
      "二、热点变量",
    ];

    if (hotItems.length > 0) {
      hotItems.slice(0, 12).forEach((item, index) => {
        lines.push(`${index + 1}. ${item.renderVariable.name || item.variable.id} (${item.variable.id})：${item.usage.total} 处引用`);
      });
    } else {
      lines.push("暂无变量被剧情卡片引用。");
    }

    lines.push("", "三、优先处理风险");
    if (riskItems.length > 0) {
      riskItems.forEach((item, index) => {
        lines.push(`${index + 1}. ${item.renderVariable.name || item.variable.id} (${item.variable.id})：${item.issues.join("、")}`);
      });
    } else {
      lines.push("未发现变量 ID、默认值或范围风险。");
    }

    lines.push("", "四、未引用变量");
    if (unusedItems.length > 0) {
      unusedItems.forEach((item, index) => {
        lines.push(`${index + 1}. ${item.renderVariable.name || item.variable.id} (${item.variable.id}) · ${getVariableTypeLabel(item.renderVariable.type)}`);
      });
    } else {
      lines.push("没有未引用变量。");
    }

    lines.push("", "五、变量明细");
    items.forEach((item, index) => {
      lines.push(
        `${index + 1}. ${item.renderVariable.name || item.variable.id}`,
        `   ID：${item.variable.id}`,
        `   类型：${getVariableTypeLabel(item.renderVariable.type)}`,
        `   保存范围：${scopeLabels[getSafeScope(item.renderVariable.scope)] ?? item.renderVariable.scope}`,
        `   分组：${item.renderVariable.group || "未分组"}`,
        `   状态：${statusLabels[item.status] ?? item.status}`,
        `   说明：${item.renderVariable.description || "未填写"}`,
        `   默认值：${getDefaultInputValue(item.renderVariable)}`,
        `   引用数：${item.usage.total}`,
        `   风险：${item.issues.length > 0 ? item.issues.join("、") : "无"}`
      );
      const references = Array.isArray(item.usage.references) ? item.usage.references : [];
      references.slice(0, 8).forEach((reference) => lines.push(`   - ${reference.label}`));
      if (references.length > 8) {
        lines.push(`   - 另有 ${references.length - 8} 处引用`);
      }
    });

    return `\uFEFF${lines.join("\n")}`;
  }

  global.CanvasiaEditorProjectVariableGovernance = Object.freeze({
    DEFAULT_USAGE,
    buildGovernanceItems,
    isMatchingFilter,
    getGovernanceScore,
    renderGovernancePanel,
    renderFilterButtons,
    renderLibraryPanel,
    buildAuditReport,
  });
})(typeof window !== "undefined" ? window : globalThis);
