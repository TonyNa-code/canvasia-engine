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
    const sceneCount = project.sceneCount ?? 0;

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
            class="toolbar-button toolbar-button-primary"
            data-action="open-project"
            data-project-id="${escape(projectId)}"
          >
            ${isActive ? "继续编辑这个项目" : "打开这个项目"}
          </button>
          <button
            type="button"
            class="toolbar-button"
            data-action="${project.isSample ? "duplicate-project" : "rename-project"}"
            data-project-id="${escape(projectId)}"
          >
            ${project.isSample ? "复制成正式项目" : "改项目名"}
          </button>
          ${
            project.isSample
              ? ""
              : `
                <button
                  type="button"
                  class="toolbar-button"
                  data-action="duplicate-project"
                  data-project-id="${escape(projectId)}"
                >
                  复制项目
                </button>
                <button
                  type="button"
                  class="toolbar-button toolbar-button-danger"
                  data-action="delete-project"
                  data-project-id="${escape(projectId)}"
                >
                  删除项目
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
          class="toolbar-button project-center-mode-option ${isActive ? "is-active" : ""}"
          data-action="set-editor-mode"
          data-editor-mode="${safeMode}"
          aria-pressed="${isActive ? "true" : "false"}"
          aria-label="${escape(ariaLabel)}"
          title="${escape(actionLabel)}"
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
              <p>这里不再默认打开测试样板。可先创建一个空白项目，或继续已有作品。</p>
            </div>
            <div class="project-center-pill-row">
              <span class="project-center-pill">默认从空白项目开始</span>
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
              <button type="button" class="toolbar-button toolbar-button-primary" data-action="create-project">
                新建空白项目
              </button>
              <button type="button" class="toolbar-button" data-action="open-beginner-tutorial">
                打开新手教程
              </button>
              <button type="button" class="toolbar-button" data-action="refresh-project-center">
                刷新项目列表
              </button>
            </div>
          </div>
        </article>
        <aside class="project-center-sidecard">
          <h3>当前入口说明</h3>
          <p>空白项目初始不会自动加入章节、台词和角色，可按需要自行新建章节和场景。</p>
          <div class="project-meta-row">
            <span class="project-center-pill">已发现项目 ${localProjectCount} 个</span>
            <span class="project-center-pill">默认模式可在主卡片或顶部切换</span>
            <span class="project-center-pill">${hasSampleProject ? "示例项目可选打开" : "当前没有示例项目"}</span>
            <span class="project-center-pill">${hasActiveProject ? "已经记录过上次打开的项目" : "还没有打开过项目"}</span>
          </div>
        </aside>
      </section>
    `;
  }

  function renderProjectCenterProjectList(projects = [], activeProjectId = "", helpers = {}) {
    const projectList = Array.isArray(projects) ? projects : [];

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
                <p>这正好。先点上面的“新建空白项目”，给作品起个名字，然后我们就从零开始把它搭起来。</p>
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

  global.CanvasiaEditorProjectCenter = Object.freeze({
    renderProjectCenterCard,
    renderProjectCenterHero,
    renderProjectCenterProjectList,
  });
})(typeof window !== "undefined" ? window : globalThis);
