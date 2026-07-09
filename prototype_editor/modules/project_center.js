(function attachProjectCenterTools(global) {
  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function getEscapeHtml(helpers = {}) {
    return typeof helpers.escapeHtml === "function" ? helpers.escapeHtml : escapeHtml;
  }

  function getFallbackTemplateLabel(template) {
    if (!template) {
      return "自定义项目";
    }
    return String(template);
  }

  function getFallbackEditorMode(mode) {
    return String(mode ?? "").trim().toLowerCase() === "advanced" ? "advanced" : "beginner";
  }

  function getFallbackEditorModeLabel(mode) {
    return getFallbackEditorMode(mode) === "advanced" ? "高级模式" : "新手模式";
  }

  function getFallbackDateLabel(value) {
    return value ? String(value) : "刚创建";
  }

  function toProjectList(projects) {
    return Array.isArray(projects) ? projects : [];
  }

  function buildProjectCenterSummary(projects = [], activeProjectId = "", options = {}) {
    const projectList = toProjectList(projects);
    const localProjects = projectList.filter((project) => !project.isSample);
    const sampleProjects = projectList.filter((project) => project.isSample);
    const projectCenterMode = getFallbackEditorMode(options.projectCenterMode);
    const projectCenterModeLabel =
      options.projectCenterModeLabel ?? getFallbackEditorModeLabel(projectCenterMode);
    const playableProjects = localProjects.filter((project) => Number(project.sceneCount ?? 0) > 0);
    const blankProjects = localProjects.filter((project) => Number(project.sceneCount ?? 0) <= 0);
    const activeProject = projectList.find((project) => project.projectId === activeProjectId) ?? null;
    const totalSceneCount = localProjects.reduce(
      (total, project) => total + Math.max(Number(project.sceneCount ?? 0) || 0, 0),
      0
    );

    return {
      activeProject,
      activeProjectId,
      blankProjectCount: blankProjects.length,
      hasActiveProject: Boolean(activeProject),
      hasBlankProjects: blankProjects.length > 0,
      hasLocalProjects: localProjects.length > 0,
      hasPlayableProject: playableProjects.length > 0,
      hasSampleProject: sampleProjects.length > 0,
      localProjectCount: localProjects.length,
      playableProjectCount: playableProjects.length,
      projectCenterMode,
      projectCenterModeLabel,
      sampleProjectCount: sampleProjects.length,
      sampleProject: sampleProjects[0] ?? null,
      totalProjectCount: projectList.length,
      totalSceneCount,
    };
  }

  function getProjectCenterNextStep(summary = {}) {
    if (!summary.hasLocalProjects) {
      return {
        title: "建议先生成可试玩 Demo",
        detail: "它会自动带上首章、场景、基础素材和可试玩链路，适合第一次确认整个引擎能跑通。",
        actionLabel: "新建可试玩 Demo",
        intent: "create-playable-demo-project",
      };
    }
    if (summary.hasBlankProjects && !summary.hasPlayableProject) {
      return {
        title: "先给空白项目补第一章",
        detail: summary.hasActiveProject
          ? "当前已有项目还没有可试玩场景。打开项目后创建第一章，再加入背景、立绘、BGM 和第一句台词。"
          : "当前已有项目还没有可试玩场景。请从下方项目列表打开一个项目，再创建第一章和第一段内容。",
        actionLabel: summary.hasActiveProject ? "打开项目继续编辑" : "从下方打开空白项目",
        intent: summary.hasActiveProject ? "open-active-project" : "project-list-hint",
      };
    }
    if (summary.hasActiveProject) {
      return {
        title: "继续上次项目",
        detail: "已经有可编辑项目记录。可以直接回到上次项目，继续补剧情、素材和发布前检查。",
        actionLabel: "继续编辑上次项目",
        intent: "open-active-project",
      };
    }
    return {
      title: "选择一个项目继续",
      detail: "项目列表里已有可试玩内容。先打开一个项目，再进入剧情编辑、试玩和导出流程。",
      actionLabel: "从下方项目打开",
      intent: "project-list-hint",
    };
  }

  function renderProjectCenterNextStep(summary = {}, helpers = {}) {
    const escape = getEscapeHtml(helpers);
    const nextStep = getProjectCenterNextStep(summary);
    const operationInFlightMessage = String(helpers.projectCenterOperationInFlightMessage ?? "").trim();
    const isCreatingProject = Boolean(helpers.projectCreateInFlight);
    const isOpeningProject = Boolean(helpers.projectOpenInFlightId);
    const isBusy =
      (nextStep.intent === "create-playable-demo-project" && isCreatingProject) ||
      (nextStep.intent === "open-active-project" && isOpeningProject);
    const isLocked = Boolean(operationInFlightMessage) && !isBusy;
    const isClickable = nextStep.intent !== "project-list-hint";
    const dataAttrs =
      nextStep.intent === "open-active-project"
        ? `data-action="open-project" data-project-id="${escape(summary.activeProjectId ?? "")}"`
        : nextStep.intent === "create-playable-demo-project"
          ? 'data-action="create-playable-demo-project"'
          : "";
    const stateAttrs = isBusy
      ? 'disabled aria-disabled="true" aria-busy="true"'
      : isLocked
        ? `disabled aria-disabled="true" title="${escape(operationInFlightMessage)}"`
        : "";

    return `
      <div class="project-center-next-step">
        <span class="eyebrow">推荐下一步</span>
        <h3>${escape(nextStep.title)}</h3>
        <p>${escape(nextStep.detail)}</p>
        ${
          isClickable
            ? `
              <button
                type="button"
                class="toolbar-button toolbar-button-primary ${isBusy ? "is-busy" : ""} ${isLocked ? "is-locked" : ""}"
                ${dataAttrs}
                ${stateAttrs}
              >
                ${escape(isBusy ? "处理中..." : nextStep.actionLabel)}
              </button>
            `
            : `<span class="project-center-pill">${escape(nextStep.actionLabel)}</span>`
        }
      </div>
    `;
  }

  function renderProjectCenterCard(project = {}, activeProjectId = "", helpers = {}) {
    const escape = getEscapeHtml(helpers);
    const formatDate = typeof helpers.formatDate === "function" ? helpers.formatDate : getFallbackDateLabel;
    const getTemplateLabel =
      typeof helpers.getTemplateLabel === "function" ? helpers.getTemplateLabel : getFallbackTemplateLabel;
    const getSafeEditorMode =
      typeof helpers.getSafeEditorMode === "function" ? helpers.getSafeEditorMode : getFallbackEditorMode;
    const getEditorModeLabel =
      typeof helpers.getEditorModeLabel === "function" ? helpers.getEditorModeLabel : getFallbackEditorModeLabel;

    const isActive = project.projectId === activeProjectId;
    const templateLabel = getTemplateLabel(project.template);
    const resolution = project.resolution ?? {};
    const updatedAt = project.updatedAt ? formatDate(project.updatedAt) : "刚创建";
    const editorMode = getSafeEditorMode(project.editorMode);
    const editorModeLabel = getEditorModeLabel(editorMode);
    const projectId = project.projectId ?? "";
    const isOpening = Boolean(helpers.projectOpenInFlightId) && helpers.projectOpenInFlightId === projectId;
    const isRenaming = Boolean(helpers.projectRenameInFlightId) && helpers.projectRenameInFlightId === projectId;
    const isDuplicating = Boolean(helpers.projectDuplicateInFlightId) && helpers.projectDuplicateInFlightId === projectId;
    const isDeleting = Boolean(helpers.projectDeleteInFlightId) && helpers.projectDeleteInFlightId === projectId;
    const operationInFlightMessage = String(helpers.projectCenterOperationInFlightMessage ?? "").trim();
    const isProjectActionLocked = Boolean(operationInFlightMessage);
    const sceneCount = project.sceneCount ?? 0;
    const getActionButtonClass = (isBusy) =>
      `${isBusy ? "is-busy" : ""} ${!isBusy && isProjectActionLocked ? "is-locked" : ""}`.trim();
    const getActionButtonAttrs = (isBusy) => {
      if (isBusy) {
        return 'disabled aria-disabled="true" aria-busy="true"';
      }
      if (isProjectActionLocked) {
        return `disabled aria-disabled="true" title="${escape(operationInFlightMessage)}"`;
      }
      return "";
    };

    const description = project.isSample
      ? "这是保留下来的示例项目，只在你需要参考时再打开。"
      : sceneCount === 0
        ? `这是一个真正的空白项目，还没有章节和场景，当前默认用${editorModeLabel}开工。`
        : `这个项目已经有基础内容，可继续写入；当前会按${editorModeLabel}打开。`;

    return `
      <article class="project-card ${project.isSample ? "is-sample" : ""} ${isActive ? "is-active" : ""}">
        <div class="project-card-head">
          <div class="text-stack">
            <div class="project-meta-row">
              <span class="issue-tag ${project.isSample ? "" : "good-text"}">${escape(
                project.isSample ? "示例项目" : "空白项目 / 正式项目"
              )}</span>
              ${isActive ? '<span class="issue-tag good-text">上次打开</span>' : ""}
            </div>
            <h3>${escape(project.title ?? "未命名项目")}</h3>
            <p>${escape(templateLabel)} / ${escape(project.language ?? "zh-CN")}</p>
          </div>
        </div>
        <div class="project-card-body">
          <div class="project-meta-row">
            <span class="project-center-pill">章节 ${project.chapterCount ?? 0}</span>
            <span class="project-center-pill">场景 ${sceneCount}</span>
            <span class="project-center-pill">分辨率 ${resolution.width ?? 1920} × ${resolution.height ?? 1080}</span>
            <span class="project-center-pill">${escape(editorModeLabel)}</span>
          </div>
          <p class="project-card-meta">${escape(description)}</p>
          <p class="project-card-meta">最近更新：${escape(updatedAt)}</p>
        </div>
        <div class="project-card-actions">
          <button
            type="button"
            class="toolbar-button toolbar-button-primary ${getActionButtonClass(isOpening)}"
            data-action="open-project"
            data-project-id="${escape(projectId)}"
            ${getActionButtonAttrs(isOpening)}
          >
            ${isOpening ? "打开中..." : isActive ? "继续编辑这个项目" : "打开这个项目"}
          </button>
          <button
            type="button"
            class="toolbar-button ${getActionButtonClass(project.isSample ? isDuplicating : isRenaming)}"
            data-action="${project.isSample ? "duplicate-project" : "rename-project"}"
            data-project-id="${escape(projectId)}"
            ${getActionButtonAttrs(project.isSample ? isDuplicating : isRenaming)}
          >
            ${project.isSample ? (isDuplicating ? "复制中..." : "复制成正式项目") : isRenaming ? "改名中..." : "改项目名"}
          </button>
          ${
            project.isSample
              ? ""
              : `
                <button
                  type="button"
                  class="toolbar-button ${getActionButtonClass(isDuplicating)}"
                  data-action="duplicate-project"
                  data-project-id="${escape(projectId)}"
                  ${getActionButtonAttrs(isDuplicating)}
                >
                  ${isDuplicating ? "复制中..." : "复制项目"}
                </button>
                <button
                  type="button"
                  class="toolbar-button toolbar-button-danger ${getActionButtonClass(isDeleting)}"
                  data-action="delete-project"
                  data-project-id="${escape(projectId)}"
                  ${getActionButtonAttrs(isDeleting)}
                >
                  ${isDeleting ? "删除中..." : "删除项目"}
                </button>
              `
          }
        </div>
      </article>
    `;
  }

  function renderProjectCenterHero(summary = {}, helpers = {}) {
    const escape = getEscapeHtml(helpers);
    const localProjectCount = Math.max(Number.parseInt(summary.localProjectCount ?? 0, 10) || 0, 0);
    const projectCenterMode = getFallbackEditorMode(summary.projectCenterMode);
    const modeLabel = summary.projectCenterModeLabel ?? getFallbackEditorModeLabel(summary.projectCenterMode);
    const hasSampleProject = Boolean(summary.hasSampleProject ?? summary.sampleProject);
    const hasActiveProject = Boolean(summary.activeProjectId);
    const isCreatingProject = Boolean(helpers.projectCreateInFlight);
    const isRefreshingProjects = Boolean(helpers.projectCenterRefreshInFlight);
    const operationInFlightMessage = String(helpers.projectCenterOperationInFlightMessage ?? "").trim();
    const isProjectCenterLocked = Boolean(operationInFlightMessage);
    const getHeroButtonClass = (isBusy) =>
      `${isBusy ? "is-busy" : ""} ${!isBusy && isProjectCenterLocked ? "is-locked" : ""}`.trim();
    const getHeroButtonAttrs = (isBusy) => {
      if (isBusy) {
        return 'disabled aria-disabled="true" aria-busy="true"';
      }
      if (isProjectCenterLocked) {
        return 'disabled aria-disabled="true"';
      }
      return "";
    };
    const renderModeOption = (mode) => {
      const safeMode = getFallbackEditorMode(mode);
      const isActive = projectCenterMode === safeMode;
      const label = getFallbackEditorModeLabel(safeMode);
      const buttonLabel = isActive ? `默认：${label}` : `设为${label}`;
      const actionLabel = isActive ? `新建项目已经默认使用${label}` : `设为新建项目默认${label}`;
      const ariaLabel = `项目中心主卡片：${actionLabel}`;
      return `
        <button
          type="button"
          class="toolbar-button project-center-mode-option ${isActive ? "is-active" : ""} ${getHeroButtonClass(false)}"
          data-action="set-editor-mode"
          data-editor-mode="${safeMode}"
          aria-pressed="${isActive ? "true" : "false"}"
          aria-label="${escape(ariaLabel)}"
          title="${escape(isProjectCenterLocked ? operationInFlightMessage : actionLabel)}"
          ${getHeroButtonAttrs(false)}
        >
          ${escape(buttonLabel)}
        </button>
      `;
    };

    return `
      <section class="project-center-hero">
        <article class="project-center-banner">
          <div class="project-center-copy">
            <span class="eyebrow">像真正的游戏引擎一样开始</span>
            <div>
              <h2>先选项目，再进入编辑器</h2>
              <p>这里不再默认打开测试样板。第一次建议先生成可试玩 Demo；想从零开始时，也可以创建空白项目。</p>
            </div>
            <div class="project-center-pill-row">
              <span class="project-center-pill">推荐从可试玩 Demo 开始</span>
              <span class="project-center-pill">默认分辨率 1920 × 1080</span>
              <span class="project-center-pill">新建默认：${escape(modeLabel)}</span>
              <span class="project-center-pill">示例项目会单独列在下方，不会默认打开</span>
            </div>
            <div class="project-center-mode-panel">
              <div>
                <strong>新建项目默认模式</strong>
                <span>只影响之后创建的空白项目；已有项目会保留自己的模式。</span>
              </div>
              <div class="project-center-mode-options" role="group" aria-label="新建项目默认编辑模式">
                ${renderModeOption("beginner")}
                ${renderModeOption("advanced")}
              </div>
            </div>
            <div class="project-center-actions">
              <button
                type="button"
                class="toolbar-button toolbar-button-primary ${getHeroButtonClass(isCreatingProject)}"
                data-action="create-playable-demo-project"
                ${getHeroButtonAttrs(isCreatingProject)}
                ${isProjectCenterLocked && !isCreatingProject ? `title="${escape(operationInFlightMessage)}"` : ""}
              >
                ${isCreatingProject ? "准备中..." : "新建可试玩 Demo"}
              </button>
              <button
                type="button"
                class="toolbar-button ${getHeroButtonClass(isCreatingProject)}"
                data-action="create-project"
                ${getHeroButtonAttrs(isCreatingProject)}
                ${isProjectCenterLocked && !isCreatingProject ? `title="${escape(operationInFlightMessage)}"` : ""}
              >
                ${isCreatingProject ? "准备中..." : "新建空白项目"}
              </button>
              <button
                type="button"
                class="toolbar-button ${getHeroButtonClass(false)}"
                data-action="open-beginner-tutorial"
                ${getHeroButtonAttrs(false)}
                ${isProjectCenterLocked ? `title="${escape(operationInFlightMessage)}"` : ""}
              >
                打开新手教程
              </button>
              <button
                type="button"
                class="toolbar-button ${getHeroButtonClass(isRefreshingProjects)}"
                data-action="refresh-project-center"
                ${getHeroButtonAttrs(isRefreshingProjects)}
                ${isProjectCenterLocked && !isRefreshingProjects ? `title="${escape(operationInFlightMessage)}"` : ""}
              >
                ${isRefreshingProjects ? "刷新中..." : "刷新项目列表"}
              </button>
            </div>
          </div>
        </article>
        <aside class="project-center-sidecard">
          <h3>当前入口说明</h3>
          <p>想马上试玩就选 Demo 项目；想完全从零搭建，就选空白项目后自行新建章节和场景。</p>
          <div class="project-meta-row">
            <span class="project-center-pill">已发现项目 ${localProjectCount} 个</span>
            <span class="project-center-pill">默认模式可在主卡片或顶部切换</span>
            <span class="project-center-pill">${hasSampleProject ? "示例项目可选打开" : "当前没有示例项目"}</span>
            <span class="project-center-pill">${hasActiveProject ? "已经记录过上次打开的项目" : "还没有打开过项目"}</span>
          </div>
          ${renderProjectCenterNextStep(summary, helpers)}
        </aside>
      </section>
    `;
  }

  function renderProjectCenterProjectList(projects = [], activeProjectId = "", helpers = {}) {
    const escape = getEscapeHtml(helpers);
    const projectList = Array.isArray(projects) ? projects : [];
    const operationInFlightMessage = String(helpers.projectCenterOperationInFlightMessage ?? "").trim();
    const isProjectCenterLocked = Boolean(operationInFlightMessage);
    const isCreatingProject = Boolean(helpers.projectCreateInFlight);
    const getEmptyCreateButtonClass = () =>
      `${isCreatingProject ? "is-busy" : ""} ${!isCreatingProject && isProjectCenterLocked ? "is-locked" : ""}`.trim();
    const getEmptyCreateButtonAttrs = () => {
      if (isCreatingProject) {
        return 'disabled aria-disabled="true" aria-busy="true"';
      }
      if (isProjectCenterLocked) {
        return `disabled aria-disabled="true" title="${escape(operationInFlightMessage)}"`;
      }
      return "";
    };

    return `
      <section class="panel">
        <div class="panel-heading">
          <h2>项目列表</h2>
          <span class="badge badge-soft">从这里打开</span>
        </div>
        ${
          projectList.length === 0
            ? `
              <div class="project-card-empty">
                <h3>现在还是一张白纸</h3>
                <p>第一次建议先生成一个可试玩 Demo，确认项目、章节、素材和试玩链路都能跑通；想完全从零搭建时，再选择空白项目。</p>
                <div class="project-card-empty-actions">
                  <button
                    type="button"
                    class="toolbar-button toolbar-button-primary ${getEmptyCreateButtonClass()}"
                    data-action="create-playable-demo-project"
                    ${getEmptyCreateButtonAttrs()}
                  >
                    ${isCreatingProject ? "准备中..." : "新建可试玩 Demo"}
                  </button>
                  <button
                    type="button"
                    class="toolbar-button ${getEmptyCreateButtonClass()}"
                    data-action="create-project"
                    ${getEmptyCreateButtonAttrs()}
                  >
                    ${isCreatingProject ? "准备中..." : "新建空白项目"}
                  </button>
                </div>
              </div>
            `
            : `
              <div class="project-card-grid">
                ${projectList.map((project) => renderProjectCenterCard(project, activeProjectId, helpers)).join("")}
              </div>
            `
        }
      </section>
    `;
  }

  function renderProjectCenterShell(projects = [], activeProjectId = "", options = {}, helpers = {}) {
    const summary = buildProjectCenterSummary(projects, activeProjectId, options);
    return `
      <div class="project-center-shell">
        ${renderProjectCenterHero(summary, helpers)}
        ${renderProjectCenterProjectList(projects, activeProjectId, helpers)}
      </div>
    `;
  }

  global.CanvasiaEditorProjectCenter = Object.freeze({
    buildProjectCenterSummary,
    getProjectCenterNextStep,
    renderProjectCenterCard,
    renderProjectCenterHero,
    renderProjectCenterNextStep,
    renderProjectCenterProjectList,
    renderProjectCenterShell,
  });
})(typeof window !== "undefined" ? window : globalThis);
