(function attachBeginnerTutorialTools(global) {
  function hasBeginnerTutorialStoryContent(data) {
    const scenes = data?.scenes ?? [];
    return scenes.some((scene) =>
      (scene.blocks ?? []).some((block) => ["dialogue", "narration", "choice"].includes(block.type))
    );
  }

  function hasBeginnerTutorialPreviewProgress(context = {}, sanitizeStoredPreviewSession = (session) => session) {
    const autoResume = sanitizeStoredPreviewSession(context.previewAutoResume?.session);
    const quickSave = sanitizeStoredPreviewSession(context.previewQuickSave?.session);
    const slotSession = (context.previewSaveSlots ?? []).find((slot) => sanitizeStoredPreviewSession(slot?.session));
    const sessionTimelineLength = context.previewSession?.timeline?.length ?? 0;
    return Boolean(autoResume || quickSave || slotSession || sessionTimelineLength > 1);
  }

  function getRuntimeExportSupportSummary() {
    return {
      windows: "游戏成品现在支持网页试玩包和 Windows 桌面包，Windows 这边可以走可运行桌面包链路。",
      macLinux: "macOS 和 Linux 现在也已经能导出原生桌面包，三端都走同一套 NW.js 原生桌面壳链路。",
      editor:
        "编辑器本体已经能导出三系统桌面套装，所以创作工具和游戏成品的支持范围现在不是完全一样的。",
    };
  }

  function buildBeginnerTutorialSteps(context = {}) {
    const data = context.data ?? null;
    const hasProject = Boolean(data?.project);
    const hasScenes = (data?.scenes?.length ?? 0) > 0;
    const hasStoryContent = hasProject && hasBeginnerTutorialStoryContent(data);
    const starterKitOverview = hasProject ? context.starterKitOverview ?? null : null;
    const starterKitReady = hasProject && starterKitOverview ? !starterKitOverview.needsStarterKit : false;
    const previewReady = hasProject && hasScenes;
    const previewDone = previewReady && Boolean(context.previewProgress);
    const exportDone = Boolean(context.lastExportResult);
    const exportSupport = getRuntimeExportSupportSummary();

    return [
      {
        id: "project",
        step: "第 1 步",
        title: hasProject ? "先确认当前项目入口" : "先创建或打开项目",
        done: hasProject,
        summary: hasProject
          ? `当前已经打开《${data.project.title}》，后续步骤会按项目进度排列。`
          : "第一次建议先生成可试玩 Demo；想完全从零搭建时，再新建空白项目。",
        notes: [
          hasProject ? "页面切换和保存操作都会基于当前项目进行。" : "Demo 会自动创建项目、第一章、基础素材和可预览入口。",
          hasProject ? "可随时回项目中心切换作品或复制示例项目。" : "空白项目仍然保留，适合已经想好结构的作品。",
          "示例项目会单独显示在项目中心下方。",
        ],
        actions: hasProject
          ? [
              { label: "回项目中心看看", action: "open-project-center" },
              { label: "继续留在当前项目", action: "switch-screen", dataset: { screen: "dashboard" } },
            ]
          : [
              { label: "新建可试玩 Demo", action: "create-playable-demo-project" },
              { label: "新建空白项目", action: "create-project" },
            ],
      },
      {
        id: "chapter",
        step: "第 2 步",
        title: hasScenes ? "第一章和第一场已经有了" : "先建第一章和第一场",
        done: hasScenes,
        summary: hasScenes
          ? "剧情骨架已经建立，可直接继续写入正文。"
          : "空白项目需要先创建第一章和第一场，后续内容才能挂载。",
        notes: [
          "没有场景时，剧情块和试玩入口都不会出现。",
          "如需自定义命名，可使用“自定义名字再创建”。",
        ],
        actions: hasScenes
          ? [
              { label: "去剧情页继续写", action: "switch-screen", dataset: { screen: "story" } },
              { label: "查看首页路线", action: "switch-screen", dataset: { screen: "dashboard" } },
            ]
          : [
              { label: "一键创建第一章", action: "create-first-chapter" },
              { label: "自定义名字再创建", action: "create-first-chapter-custom" },
            ],
      },
      {
        id: "story",
        step: "第 3 步",
        title: hasStoryContent ? "正文已经开始成形" : "先写第一段正文",
        done: hasStoryContent,
        summary: hasStoryContent
          ? "当前项目里已经有正文卡片，后续可以继续补齐角色、背景、音乐和分支。"
          : "先写一句台词或旁白，让项目从空场景进入可阅读状态。",
        notes: [
          "新手模式下，剧情页优先显示正文相关入口。",
          "变量、条件和镜头演出可在后续切换到高级模式时再补充。",
        ],
        actions: [
          { label: hasStoryContent ? "继续写剧情" : "打开剧情页", action: "switch-screen", dataset: { screen: "story" } },
          { label: "看新手工作流", action: "switch-screen", dataset: { screen: "story" } },
        ],
      },
      {
        id: "starter-kit",
        step: "第 4 步",
        title: starterKitReady ? "角色和基础素材已经补上" : "再补角色、背景和 BGM",
        done: starterKitReady,
        summary: starterKitReady
          ? "项目已经具备角色、基础素材和首场景演出骨架。"
          : "补上第一个角色、一张背景和一首 BGM 后，会自动尝试接入首场景，让预览更快跑起来。",
        notes: [
          starterKitOverview?.needsStarterKit
            ? `当前还缺：${starterKitOverview.missingLabels.join("、")}。`
            : "如已自行导入素材，可继续进入试玩与导出流程。",
          "这里会生成可试玩的占位素材和首场景基础演出，后续仍可在素材页替换成正式图片和音频文件。",
        ],
        actions: starterKitOverview?.needsStarterKit
          ? [
              { label: "一键生成起步骨架", action: "create-starter-kit" },
              { label: "自定义名字再生成", action: "create-starter-kit-custom" },
            ]
          : [
              { label: "打开角色页", action: "switch-screen", dataset: { screen: "characters" } },
              { label: "去素材页继续补", action: "switch-screen", dataset: { screen: "assets" } },
            ],
      },
      {
        id: "preview",
        step: "第 5 步",
        title: previewDone ? "试玩链已经跑过" : "进入试玩流程",
        done: previewDone,
        summary: previewReady
          ? previewDone
            ? "当前版本已经完成试玩记录，可继续使用正式存档、快速存档和系统菜单做自测。"
            : "当前已经有可运行场景，适合先到试玩页检查节奏和基础链路。"
          : "当前还没有可试玩场景，需要先完成前面步骤。",
        notes: [
          "试玩页已经接通正式存档、快速存档、系统菜单和标题页读档等核心能力。",
          "当前内容可先完成一轮试玩，再继续补充细节。",
        ],
        actions: previewReady
          ? [
              { label: "进入试玩收尾", action: "switch-screen", dataset: { screen: "preview" } },
              { label: "回剧情页继续补", action: "switch-screen", dataset: { screen: "story" } },
            ]
          : [
              { label: "创建第一章", action: "create-first-chapter" },
              { label: "回首页看看进度", action: "switch-screen", dataset: { screen: "dashboard" } },
            ],
      },
      {
        id: "export",
        step: "第 6 步",
        title: exportDone ? "已经导出过一版" : "最后再看导出目标",
        done: exportDone,
        summary: exportDone
          ? "导出链已经实际跑过了，后面就可以继续收尾、修问题、再导下一版。"
          : "导出前可先确认平台支持范围：当前游戏成品可导出网页试玩包，也可走 Windows / macOS / Linux 原生桌面包链路。",
        notes: [
          exportSupport.windows,
          exportSupport.macLinux,
          exportSupport.editor,
        ],
        actions: [
          { label: "打开预览导出页", action: "switch-screen", dataset: { screen: "preview" } },
          { label: "打开项目巡检", action: "switch-screen", dataset: { screen: "inspection" } },
        ],
      },
    ];
  }

  function clampBeginnerTutorialStepIndex(stepIndex, steps) {
    const maxIndex = Math.max((steps?.length ?? 0) - 1, 0);
    return Math.min(Math.max(Number.parseInt(stepIndex ?? "0", 10) || 0, 0), maxIndex);
  }

  function getBeginnerTutorialDefaultStepIndex(steps) {
    return Math.max(
      (steps ?? []).findIndex((step) => !step.done),
      0
    );
  }

  function getBeginnerTutorialSummary(context = {}) {
    if (context.data?.project) {
      return `当前项目：${context.activeProjectTitle}。教程会按这个项目的真实进度排列当前流程。`;
    }
    if (context.activeProjectTitle) {
      return `上次打开的项目是《${context.activeProjectTitle}》。如需继续处理，可先从项目中心打开。`;
    }
    return "还没有打开项目也没关系。第一次建议先新建可试玩 Demo，再按下面 6 步往下走。";
  }

  function renderBeginnerTutorialStepList(steps, stepIndex, escapeHtml = String) {
    return (steps ?? [])
      .map(
        (step, index) => `
          <button
            type="button"
            class="beginner-tutorial-step-button ${index === stepIndex ? "is-active" : ""} ${step.done ? "is-done" : ""}"
            data-action="set-beginner-tutorial-step"
            data-step-index="${index}"
          >
            <span class="beginner-tutorial-step-meta">${escapeHtml(step.step)}</span>
            <strong>${escapeHtml(step.title)}</strong>
            <span class="beginner-tutorial-step-state">${step.done ? "当前已完成" : "进行中"}</span>
          </button>
        `
      )
      .join("");
  }

  function renderBeginnerTutorialContent(currentStep, helpers = {}) {
    const escapeHtml = helpers.escapeHtml ?? String;
    const renderQuickActionButton = helpers.renderQuickActionButton ?? (() => "");
    return `
      <article class="beginner-tutorial-focus">
        <span class="issue-tag ${currentStep.done ? "good-text" : "warn-text"}">${escapeHtml(currentStep.step)}</span>
        <h3>${escapeHtml(currentStep.title)}</h3>
        <p>${escapeHtml(currentStep.summary)}</p>
        <div class="detail-actions">
          ${currentStep.actions.map((action, index) => renderQuickActionButton(action, index === 0)).join("")}
        </div>
      </article>
      <section class="beginner-tutorial-note-stack">
        ${currentStep.notes
          .map(
            (note) => `
              <article class="detail-card beginner-tutorial-note-card">
                <strong>这一条为什么重要</strong>
                <p>${escapeHtml(note)}</p>
              </article>
            `
          )
          .join("")}
      </section>
      <article class="detail-card beginner-tutorial-footer-card">
        <strong>最简单的记忆方式</strong>
        <p>先建项目和第一场，再写正文，补角色和素材，进入试玩，最后再看导出目标。先完成一段可运行内容，再继续扩展会更清晰。</p>
      </article>
    `;
  }

  function getBeginnerWorkflowStepStatusLabel(step) {
    if (step?.statusLabel) {
      return step.statusLabel;
    }
    return step?.done ? "当前已完成" : "进行中";
  }

  function getBeginnerWorkflowStepToneClass(step) {
    if (step?.done || step?.statusTone === "good") {
      return "good-text";
    }
    if (step?.statusTone === "danger") {
      return "danger-text";
    }
    if (step?.statusTone === "soft") {
      return "soft-text";
    }
    return "warn-text";
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function renderBeginnerDashboardWorkflow(workflow, helpers = {}) {
    const escape = helpers.escapeHtml ?? escapeHtml;
    const renderQuickActionButton = helpers.renderQuickActionButton ?? (() => "");
    const safeWorkflow = workflow && typeof workflow === "object" ? workflow : { steps: [], nextStep: null };
    const steps = Array.isArray(safeWorkflow.steps) ? safeWorkflow.steps : [];
    const nextStep = safeWorkflow.nextStep ?? steps.find((item) => !item.done) ?? steps[0] ?? {
      step: "第 1 步",
      title: "先创建或打开项目",
      description: "第一次建议从项目中心新建可试玩 Demo；想从零开始时，再新建空白项目。",
      actions: [{ label: "回项目中心", action: "open-project-center" }],
    };

    return `
    <section class="panel beginner-dashboard-panel">
      <div class="panel-heading">
        <div>
          <h2>新手开工顺序</h2>
          <span class="panel-note">按当前项目进度显示 4 个主要步骤</span>
        </div>
        <span class="badge badge-soft">当前进行项：${escape(nextStep.step)}</span>
      </div>
      <div class="beginner-dashboard-grid">
        <article class="beginner-dashboard-card beginner-dashboard-focus-card">
          <span class="eyebrow">${escape(nextStep.step)}</span>
          <strong>${escape(nextStep.title)}</strong>
          <p>${escape(nextStep.description)}</p>
          <div class="detail-actions">
            ${(nextStep.actions ?? []).map((action, index) => renderQuickActionButton(action, index === 0)).join("")}
          </div>
        </article>
        <div class="beginner-dashboard-step-stack">
          ${steps
            .map(
              (step) => `
                <article class="beginner-dashboard-card ${step.done ? "is-done" : ""}">
                  <span class="workflow-step-label">${escape(step.step)}</span>
                  <strong>${escape(step.title)}</strong>
                  <p>${escape(step.description)}</p>
                  <div class="story-filter-chip-row">
                    <span class="issue-tag ${getBeginnerWorkflowStepToneClass(step)}">
                      ${escape(getBeginnerWorkflowStepStatusLabel(step))}
                    </span>
                  </div>
                </article>
              `
            )
            .join("")}
        </div>
      </div>
    </section>
  `;
  }

  function renderBeginnerAdvancedToolsPanel(helpers = {}) {
    const renderQuickActionButton = helpers.renderQuickActionButton ?? (() => "");

    return `
    <section class="panel beginner-advanced-tools-panel">
      <div class="panel-heading">
        <div>
          <h2>更多高级工具</h2>
          <span class="panel-note">需要分支、校对和发布收尾时可切换到高级模式</span>
        </div>
        <span class="badge badge-soft">新手模式默认收起</span>
      </div>
      <div class="story-filter-chip-row">
        <span class="issue-tag">台词台本页</span>
        <span class="issue-tag">全局检索台</span>
        <span class="issue-tag">项目安全网时间线</span>
        <span class="issue-tag">剧情路线图</span>
        <span class="issue-tag">场景状态看板</span>
      </div>
      <article class="detail-card beginner-dashboard-card">
        <strong>适用阶段</strong>
        <p>完成基础剧情后，可切换到高级模式处理变量分支、系统校对、历史恢复和正式导出。</p>
        <div class="detail-actions">
          ${renderQuickActionButton(
            { label: "切到高级模式", action: "set-editor-mode", dataset: { "editor-mode": "advanced" } },
            true
          )}
          ${renderQuickActionButton({ label: "先继续写剧情", action: "switch-screen", dataset: { screen: "story" } })}
        </div>
      </article>
    </section>
  `;
  }

  function renderStarterKitPanel(overview, defaults, context = "dashboard", helpers = {}) {
    const escape = helpers.escapeHtml ?? escapeHtml;
    const safeOverview = overview && typeof overview === "object" ? overview : {};
    if (!safeOverview.needsStarterKit) {
      return "";
    }

    const safeDefaults = defaults && typeof defaults === "object" ? defaults : {};
    const contextCopy = {
      dashboard: "当前项目已经有章节骨架，下一步适合补齐角色、背景和 BGM 的基础条目。",
      story: "当前剧情已经可以继续写入，补齐角色、背景和 BGM 后，预览和演出会更完整。",
      assets: "这里可以生成“背景 / 立绘 / BGM”的起步条目，后续再替换成正式素材文件。",
      characters: "先补齐第一个角色骨架后，台词归属、立绘表情和语音整理会更完整。",
    };

    return `
    <section class="detail-card starter-kit-panel">
      <div class="panel-heading">
        <h3>第二步起步骨架</h3>
        <span class="badge badge-soft">补齐基础条目</span>
      </div>
      <div class="starter-kit-grid">
        <article class="starter-kit-card is-primary">
          <span class="eyebrow">当前进度</span>
          <strong>补齐角色与基础素材</strong>
          <p>${escape(contextCopy[context] ?? contextCopy.dashboard)}</p>
          <div class="scene-card-tags">
            ${(safeOverview.missingLabels ?? [])
              .map((label) => `<span class="issue-tag warn-text">待补：${escape(label)}</span>`)
              .join("")}
          </div>
          <div class="pill-row">
            ${safeOverview.missingCharacter ? `<span class="pill">角色默认名：${escape(safeDefaults.characterName ?? "女主角")}</span>` : ""}
            ${safeOverview.missingBackground ? `<span class="pill">背景默认名：${escape(safeDefaults.backgroundName ?? "第一场背景")}</span>` : ""}
            ${safeOverview.missingBgm ? `<span class="pill">BGM 默认名：${escape(safeDefaults.bgmName ?? "开场 BGM")}</span>` : ""}
          </div>
          <div class="action-row">
            <button class="toolbar-button toolbar-button-primary" type="button" data-action="create-starter-kit">
              一键生成起步骨架
            </button>
            <button class="toolbar-button" type="button" data-action="create-starter-kit-custom">
              自定义名字再生成
            </button>
          </div>
        </article>
        <article class="starter-kit-card">
          <span class="eyebrow">生成内容</span>
          <ul class="blank-project-step-list">
            ${safeOverview.missingCharacter ? "<li>生成一个角色骨架，并自动带一张默认立绘条目。</li>" : ""}
            ${safeOverview.missingBackground ? "<li>生成第一张可替换背景占位图，方便你先试玩再换正式图片。</li>" : ""}
            ${safeOverview.missingBgm ? "<li>生成第一首可替换静音 BGM，占住演出位置，后面可直接替换。</li>" : ""}
          </ul>
          <div class="detail-meta">此操作只会补齐条目骨架，不会改动现有剧情内容。</div>
        </article>
      </div>
    </section>
  `;
  }

  function renderBlankProjectStarterPanel(defaults, context = "dashboard", helpers = {}) {
    const escape = helpers.escapeHtml ?? escapeHtml;
    const safeDefaults = defaults && typeof defaults === "object" ? defaults : {};
    const contextCopy =
      context === "story"
        ? "当前位于剧情页，先创建第一章和第一场景后，这里就会切换成可编辑的剧情工作台。"
        : "当前项目还是空白状态，创建第一章和第一场景后即可继续填充台词、角色和素材。";

    return `
    <section class="panel blank-project-panel">
      <div class="panel-heading">
        <h2>空白项目首次引导</h2>
        <span class="badge badge-soft">初始步骤</span>
      </div>
      <div class="blank-project-grid">
        <article class="blank-project-card is-primary">
          <span class="eyebrow">当前进度</span>
          <h3>创建第一章和第一场景</h3>
          <p>${escape(contextCopy)}</p>
          <div class="pill-row">
            <span class="pill">默认章节：${escape(safeDefaults.chapterName ?? "第一章")}</span>
            <span class="pill">默认场景：${escape(safeDefaults.firstSceneName ?? "开场")}</span>
          </div>
          <div class="action-row">
            <button class="toolbar-button toolbar-button-primary" type="button" data-action="create-first-chapter">
              一键创建第一章
            </button>
            <button class="toolbar-button" type="button" data-action="create-first-chapter-custom">
              自定义名字再创建
            </button>
          </div>
          <div class="detail-meta">章节名和场景名后续仍可修改。</div>
        </article>
        <article class="blank-project-card">
          <span class="eyebrow">后续顺序</span>
          <h3>开工顺序</h3>
          <ol class="blank-project-step-list">
            <li>先写出第一段旁白和第一句台词。</li>
            <li>再去素材页导入第一张背景和一首 BGM。</li>
            <li>然后回角色页补角色名、表情和立绘。</li>
          </ol>
          <div class="action-row">
            <button class="toolbar-button" type="button" data-action="switch-screen" data-screen="assets">
              打开素材页
            </button>
            <button class="toolbar-button" type="button" data-action="switch-screen" data-screen="characters">
              打开角色页
            </button>
          </div>
        </article>
      </div>
    </section>
  `;
  }

  function renderBlankStoryWorkspacePanel() {
    return `
    <div class="blank-story-workspace">
      <div class="blank-story-workspace-copy">
        <strong>剧情工作台还没有章节和场景</strong>
        <p>创建第一章和第一场景后，这里会切换成可编辑状态。</p>
      </div>
      <div class="action-row">
        <button class="toolbar-button toolbar-button-primary" type="button" data-action="create-first-chapter">
          一键创建第一章
        </button>
        <button class="toolbar-button" type="button" data-action="create-first-chapter-custom">
          自定义名字再创建
        </button>
      </div>
    </div>
  `;
  }

  global.CanvasiaEditorBeginnerTutorial = Object.freeze({
    hasBeginnerTutorialStoryContent,
    hasBeginnerTutorialPreviewProgress,
    getRuntimeExportSupportSummary,
    buildBeginnerTutorialSteps,
    clampBeginnerTutorialStepIndex,
    getBeginnerTutorialDefaultStepIndex,
    getBeginnerTutorialSummary,
    renderBeginnerTutorialStepList,
    renderBeginnerTutorialContent,
    getBeginnerWorkflowStepStatusLabel,
    getBeginnerWorkflowStepToneClass,
    renderBeginnerDashboardWorkflow,
    renderBeginnerAdvancedToolsPanel,
    renderStarterKitPanel,
    renderBlankProjectStarterPanel,
    renderBlankStoryWorkspacePanel,
  });
})(typeof window !== "undefined" ? window : globalThis);
