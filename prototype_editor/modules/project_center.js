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

  global.CanvasiaEditorProjectCenter = Object.freeze({
    renderProjectCenterCard,
  });
})(typeof window !== "undefined" ? window : globalThis);
