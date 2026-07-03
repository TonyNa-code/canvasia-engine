(function attachEditorModeTools(global) {
  const EDITOR_MODE_LABELS = Object.freeze({
    beginner: "新手模式",
    advanced: "高级模式",
  });

  const NAV_SCREEN_LABELS = Object.freeze({
    dashboard: Object.freeze({
      beginner: "开工首页",
      advanced: "首页",
    }),
    story: Object.freeze({
      beginner: "写剧情",
      advanced: "写剧情",
    }),
    assets: Object.freeze({
      beginner: "补素材",
      advanced: "管素材",
    }),
    characters: Object.freeze({
      beginner: "看角色",
      advanced: "管角色",
    }),
    script: Object.freeze({
      beginner: "台词台本",
      advanced: "台词台本",
    }),
    inspection: Object.freeze({
      beginner: "查问题",
      advanced: "项目巡检",
    }),
    preview: Object.freeze({
      beginner: "试玩收尾",
      advanced: "预览导出",
    }),
  });

  const BEGINNER_STORY_TOOLBAR_ACTIONS = new Set([
    "create-scene",
    "create-chapter",
    "rename-scene",
    "add-dialogue",
    "add-narration",
    "add-choice",
    "add-background",
    "add-character-show",
    "add-music-play",
    "add-video-play",
    "add-wait",
    "add-jump",
  ]);

  const BEGINNER_ASSET_TOOLBAR_ACTIONS = new Set(["pick-assets", "replace-asset-file"]);
  const STORY_CONTENT_BLOCK_TYPES = Object.freeze(["dialogue", "narration"]);
  const STORY_ROUTE_BLOCK_TYPES = Object.freeze(["choice", "jump"]);
  const STORY_POLISH_BLOCK_TYPES = Object.freeze([
    "particle_effect",
    "wait",
    "screen_shake",
    "screen_flash",
    "screen_fade",
    "camera_zoom",
    "camera_pan",
    "screen_filter",
    "depth_blur",
  ]);

  function getSafeEditorMode(mode) {
    return String(mode ?? "").trim().toLowerCase() === "advanced" ? "advanced" : "beginner";
  }

  function getProjectEditorMode(project) {
    return getSafeEditorMode(project?.editorMode);
  }

  function isAdvancedEditorMode(project) {
    return getProjectEditorMode(project) === "advanced";
  }

  function getEditorModeLabel(mode) {
    return EDITOR_MODE_LABELS[getSafeEditorMode(mode)] ?? EDITOR_MODE_LABELS.beginner;
  }

  function getNavScreenLabel(screenName, mode = "beginner") {
    const safeMode = getSafeEditorMode(mode);
    return NAV_SCREEN_LABELS[screenName]?.[safeMode] ?? NAV_SCREEN_LABELS[screenName]?.advanced ?? screenName;
  }

  function getEditorModeDescription(mode, context = "dashboard") {
    const safeMode = getSafeEditorMode(mode);

    if (safeMode === "advanced") {
      if (context === "preview") {
        return "显示完整的发布检查、导出诊断和修复入口，适合收尾与发布前巡检。";
      }
      if (context === "inspection") {
        return "显示完整的项目巡检、问题过滤、发布检查和修复入口，适合集中 QA 与收尾。";
      }
      if (context === "story") {
        return "显示完整剧情工具栏，包括变量、条件、复杂演出和结构整理入口。";
      }
      return "显示完整编辑能力，适合处理分支逻辑和复杂演出。";
    }

    if (context === "preview") {
      return "当前只保留导出阶段最常用的信息和按钮。";
    }
    if (context === "inspection") {
      return "当前只显示关键错误、缺口和巡检入口。";
    }
    if (context === "story") {
      return "当前只保留常用剧情骨架按钮，优先处理台词、旁白、选项、背景和音乐。";
    }
    return "当前优先保留常用入口，适合处理基础剧情流程。";
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function getEscapeHtml(options = {}) {
    return typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtml;
  }

  function renderFallbackQuickActionButton(action = {}, primary = false, options = {}) {
    const escape = getEscapeHtml(options);
    const datasetEntries = Object.entries(action.dataset ?? {})
      .map(([key, value]) => ` data-${escape(key)}="${escape(value)}"`)
      .join("");
    const sceneIdAttr = action.sceneId ? ` data-scene-id="${escape(action.sceneId)}"` : "";
    return `
      <button
        type="button"
        class="toolbar-button ${primary ? "toolbar-button-primary" : ""}"
        data-action="${escape(action.action ?? "")}"
        ${sceneIdAttr}
        ${datasetEntries}
      >
        ${escape(action.label ?? "执行")}
      </button>
    `;
  }

  function getQuickActionRenderer(options = {}) {
    return typeof options.renderQuickActionButton === "function"
      ? options.renderQuickActionButton
      : (action, primary = false) => renderFallbackQuickActionButton(action, primary, options);
  }

  function normalizeWorkflowTemplateSummary(summary) {
    if (!summary || typeof summary !== "object") {
      return null;
    }

    const blockCount = Math.max(Number.parseInt(summary.blockCount ?? 0, 10) || 0, 0);
    const labels = Array.isArray(summary.labels)
      ? summary.labels.map((label) => String(label ?? "").trim()).filter(Boolean)
      : [];
    if (blockCount <= 0 || !labels.length) {
      return null;
    }

    return {
      title: String(summary.title ?? "剧情模板").trim() || "剧情模板",
      blockCount,
      labels: labels.slice(0, 8),
    };
  }

  function renderWorkflowTemplateSummary(summary, options = {}) {
    const safeSummary = normalizeWorkflowTemplateSummary(summary);
    if (!safeSummary) {
      return "";
    }

    const escape = getEscapeHtml(options);
    return `
      <div class="workflow-template-summary" aria-label="${escape(safeSummary.title)}模板预览">
        <span class="workflow-template-summary-title">${escape(safeSummary.title)} · 将插入 ${safeSummary.blockCount} 张卡片</span>
        <div class="story-filter-chip-row">
          ${safeSummary.labels.map((label) => `<span class="issue-tag">${escape(label)}</span>`).join("")}
        </div>
      </div>
    `;
  }

  function renderEditorModeSwitchButtons(mode = "beginner", options = {}) {
    const escape = getEscapeHtml(options);
    const safeMode = getSafeEditorMode(mode);
    const compact = options.compact === true;
    return ["beginner", "advanced"]
      .map(
        (itemMode) => `
          <button
            type="button"
            class="toolbar-button editor-mode-chip ${safeMode === itemMode ? "is-active" : ""} ${compact ? "is-compact" : ""}"
            data-action="set-editor-mode"
            data-editor-mode="${itemMode}"
          >
            ${escape(getEditorModeLabel(itemMode))}
          </button>
        `
      )
      .join("");
  }

  function getEditorModeGuideTitle(context = "dashboard") {
    if (context === "preview") {
      return "导出界面分层";
    }
    if (context === "inspection") {
      return "巡检界面分层";
    }
    if (context === "story") {
      return "剧情工具栏分层";
    }
    return "编辑器模式";
  }

  function getEditorModeGuideNote(mode) {
    return getSafeEditorMode(mode) === "advanced"
      ? "如需快速返回基础流程，可切回新手模式。"
      : "需要处理变量、条件分支、镜头和复杂演出时，可切换到高级模式。";
  }

  function renderEditorModeGuideCard(context = "dashboard", options = {}) {
    const escape = getEscapeHtml(options);
    const mode = getSafeEditorMode(options.mode);
    const title = getEditorModeGuideTitle(context);
    const description = getEditorModeDescription(mode, context);
    const note = getEditorModeGuideNote(mode);

    return `
      <article class="detail-card editor-mode-card">
        <strong>${escape(title)}</strong>
        <p>${escape(description)}</p>
        <div class="detail-actions">
          ${renderEditorModeSwitchButtons(mode, options)}
          <button type="button" class="toolbar-button" data-action="open-beginner-tutorial">
            打开新手教程
          </button>
        </div>
        <div class="detail-meta">${escape(note)}</div>
      </article>
    `;
  }

  function buildBeginnerStoryWorkflow(scene, options = {}) {
    if (!scene) {
      return null;
    }

    const blocks = Array.isArray(scene.blocks) ? scene.blocks : [];
    const storyCount = blocks.filter((block) => STORY_CONTENT_BLOCK_TYPES.includes(block.type)).length;
    const hasBackground = blocks.some((block) => block.type === "background");
    const hasCharacterShow = blocks.some((block) => block.type === "character_show");
    const hasMusic = blocks.some((block) => block.type === "music_play");
    const hasBranchOrJump = blocks.some((block) => STORY_ROUTE_BLOCK_TYPES.includes(block.type));
    const hasPolish = blocks.some((block) => STORY_POLISH_BLOCK_TYPES.includes(block.type));
    const playableTemplateSummary = normalizeWorkflowTemplateSummary(options.playableTemplateSummary);

    const steps = [
      {
        step: "第一步",
        title: storyCount > 0 ? "写入这一场的基础正文" : "先生成一段可试玩剧情",
        done: storyCount > 0,
        description:
          storyCount > 0
            ? `这一场已经有 ${storyCount} 张正文卡片了，可以继续往下补氛围和去向。`
            : "一键放入背景、音乐、角色登场、对白、选择项和淡出收束，先让这一场跑起来。",
        ...(storyCount <= 0 && playableTemplateSummary ? { templateSummary: playableTemplateSummary } : {}),
        actions:
          storyCount > 0
            ? [
                { label: "继续加台词", action: "add-dialogue" },
                { label: "加一张旁白", action: "add-narration" },
              ]
            : [
                { label: "生成可试玩段落", action: "apply-story-template", dataset: { "template-id": "playable_scene" } },
                { label: "先加一句台词", action: "add-dialogue" },
              ],
      },
      {
        step: "第二步",
        title: "补齐基础演出氛围",
        done: hasBackground && (hasCharacterShow || hasMusic),
        description:
          hasBackground && (hasCharacterShow || hasMusic)
            ? "这一场已经有基础空间感了，人物和音乐至少有一项进来了。"
            : "背景、人物亮相和音乐至少补两项后，这一场的预览会更完整。",
        actions: [
          { label: hasBackground ? "再显一个角色" : "先切背景", action: hasBackground ? "add-character-show" : "add-background" },
          { label: hasMusic ? "补人物亮相" : "播一首音乐", action: hasMusic ? "add-character-show" : "add-music-play" },
        ],
      },
      {
        step: "第三步",
        title: "补齐这一场的去向",
        done: hasBranchOrJump,
        description:
          hasBranchOrJump
            ? "这场已经有下一步去向了，后面就可以开始试玩路线。"
            : "补一个选项分支，或者至少连接到下一场，避免流程在这里中断。",
        actions: [
          { label: "加选项分支", action: "add-choice" },
          { label: "直接跳下一场", action: "add-jump" },
        ],
      },
      {
        step: "第四步",
        title: "补充强化演出",
        done: hasPolish,
        description:
          hasPolish
            ? "这一场已经有至少一种强化演出，记忆点开始出来了。"
            : "剧情顺畅后，可再补粒子、镜头、闪屏等强化演出。",
        actions: [
          { label: "加粒子特效", action: "add-particle-effect" },
          { label: "去试玩这场", action: "preview-scene-from-map", sceneId: scene.id },
        ],
      },
    ];

    const nextStep = steps.find((item) => !item.done) ?? steps[steps.length - 1];
    return { nextStep, steps };
  }

  function renderBeginnerStoryWorkflow(scene, options = {}) {
    const escape = getEscapeHtml(options);
    const renderQuickActionButton = getQuickActionRenderer(options);
    const workflow = buildBeginnerStoryWorkflow(scene, options);
    if (!workflow) {
      return "";
    }

    return `
      <article class="detail-card beginner-workflow-panel">
        <div class="panel-heading">
          <div>
            <h2>新手上手顺序</h2>
            <span class="panel-note">按当前场景状态显示处理顺序</span>
          </div>
            <span class="issue-tag good-text">当前进行项：${escape(workflow.nextStep.step)}</span>
        </div>
        <article class="beginner-workflow-focus">
          <span class="workflow-step-label">${escape(workflow.nextStep.step)}</span>
          <strong>${escape(workflow.nextStep.title)}</strong>
          <p>${escape(workflow.nextStep.description)}</p>
          ${renderWorkflowTemplateSummary(workflow.nextStep.templateSummary, options)}
          <div class="detail-actions">
            ${workflow.nextStep.actions.map((action, index) => renderQuickActionButton(action, index === 0)).join("")}
          </div>
        </article>
        <div class="beginner-workflow-grid">
          ${workflow.steps
            .map(
              (step) => `
                <article class="beginner-workflow-card ${step.done ? "is-done" : "is-current"}">
                  <span class="workflow-step-label">${escape(step.step)}</span>
                  <strong>${escape(step.title)}</strong>
                  <p>${escape(step.description)}</p>
                  ${renderWorkflowTemplateSummary(step.templateSummary, options)}
                  <div class="story-filter-chip-row">
                    <span class="issue-tag ${step.done ? "good-text" : "warn-text"}">${step.done ? "当前已完成" : "进行中"}</span>
                  </div>
                </article>
              `
            )
            .join("")}
        </div>
      </article>
    `;
  }

  function renderStoryEditorModeBanner(scene = null, options = {}) {
    const escape = getEscapeHtml(options);
    const mode = getSafeEditorMode(options.mode);
    const hiddenCount = Math.max(Number.parseInt(options.hiddenCount ?? 0, 10) || 0, 0);

    return `
      <article class="detail-card editor-mode-banner-card">
        <div class="story-mode-banner-head">
          <div class="text-stack">
            <strong>${escape(getEditorModeLabel(mode))}</strong>
            <p>${escape(getEditorModeDescription(mode, "story"))}</p>
          </div>
          <div class="detail-actions">
            ${renderEditorModeSwitchButtons(mode, { ...options, compact: true })}
          </div>
        </div>
        <div class="story-filter-chip-row">
          ${
            mode === "advanced"
              ? '<span class="issue-tag good-text">完整工具栏已展开</span><span class="issue-tag">适合处理变量、条件和复杂演出</span>'
              : `<span class="issue-tag good-text">当前显示常用骨架按钮</span><span class="issue-tag">已收起 ${hiddenCount} 个高级按钮</span>`
          }
        </div>
      </article>
    ${mode === "beginner" ? renderBeginnerStoryWorkflow(scene, options) : ""}
    `;
  }

  global.CanvasiaEditorMode = Object.freeze({
    EDITOR_MODE_LABELS,
    NAV_SCREEN_LABELS,
    BEGINNER_STORY_TOOLBAR_ACTIONS,
    BEGINNER_ASSET_TOOLBAR_ACTIONS,
    STORY_CONTENT_BLOCK_TYPES,
    STORY_ROUTE_BLOCK_TYPES,
    STORY_POLISH_BLOCK_TYPES,
    getSafeEditorMode,
    getProjectEditorMode,
    isAdvancedEditorMode,
    getEditorModeLabel,
    getNavScreenLabel,
    getEditorModeDescription,
    renderEditorModeSwitchButtons,
    getEditorModeGuideTitle,
    getEditorModeGuideNote,
    renderEditorModeGuideCard,
    normalizeWorkflowTemplateSummary,
    renderWorkflowTemplateSummary,
    buildBeginnerStoryWorkflow,
    renderBeginnerStoryWorkflow,
    renderStoryEditorModeBanner,
  });
})(typeof window !== "undefined" ? window : globalThis);
