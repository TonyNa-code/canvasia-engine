(function attachCommandPaletteTools(global) {
  const SCREEN_COMMANDS = [
    { id: "screen-dashboard", title: "回到制作首页", screen: "dashboard", section: "导航", keywords: ["首页", "路线", "dashboard"] },
    { id: "screen-story", title: "写剧情 / 编排场景", screen: "story", section: "导航", keywords: ["剧情", "台词", "场景", "story"] },
    { id: "screen-assets", title: "管理素材", screen: "assets", section: "导航", keywords: ["素材", "背景", "音乐", "assets"] },
    { id: "screen-characters", title: "管理角色", screen: "characters", section: "导航", keywords: ["角色", "立绘", "人物"] },
    { id: "screen-script", title: "打开台词台本", screen: "script", section: "导航", keywords: ["台本", "语音", "script"] },
    { id: "screen-inspection", title: "打开项目巡检", screen: "inspection", section: "质量", keywords: ["检查", "错误", "doctor"] },
    { id: "screen-preview", title: "试玩与导出", screen: "preview", section: "发布", keywords: ["预览", "导出", "试玩"] },
  ];

  function normalizeSearchText(value) {
    return String(value ?? "").trim().toLowerCase();
  }

  function buildCommandSearchText(command) {
    return [
      command.title,
      command.subtitle,
      command.section,
      ...(command.keywords ?? []),
    ]
      .map((item) => normalizeSearchText(item))
      .filter(Boolean)
      .join(" ");
  }

  function buildCommandPaletteCommands(context = {}) {
    const hasProject = Boolean(context.hasProject);
    const hasStructure = Number(context.chapterCount ?? 0) > 0 && Number(context.sceneCount ?? 0) > 0;
    const needsStarterKit = Boolean(context.needsStarterKit);
    const hasValidationErrors = Number(context.errorCount ?? 0) > 0;
    const canExport = hasProject && !hasValidationErrors;
    const disabledProjectTitle = "先新建或打开项目后可用";
    const commands = [
      {
        id: "open-project-center",
        title: "打开项目中心",
        subtitle: hasProject ? "切换、复制或新建作品" : "从 Demo 或空白项目开始",
        section: "项目",
        action: "open-project-center",
        keywords: ["项目", "打开", "新建"],
      },
      {
        id: "create-playable-demo",
        title: "新建可试玩 Demo",
        subtitle: "先拿一条完整链路跑起来",
        section: "项目",
        action: "create-playable-demo-project",
        disabled: hasProject,
        disabledReason: hasProject ? "当前已有打开项目，回到项目中心后再创建 Demo" : "",
        keywords: ["demo", "新手", "示例"],
      },
      {
        id: "open-beginner-tutorial",
        title: "打开新手教程",
        subtitle: "按第一次开工顺序完成作品",
        section: "学习",
        action: "open-beginner-tutorial",
        keywords: ["教程", "帮助", "新手"],
      },
      {
        id: "mode-beginner",
        title: "切到新手模式",
        subtitle: "收起高阶入口，先完成可试玩闭环",
        section: "模式",
        action: "set-editor-mode",
        dataset: { "editor-mode": "beginner" },
        keywords: ["beginner", "新手"],
      },
      {
        id: "mode-advanced",
        title: "切到高级模式",
        subtitle: "显示变量、分支、演出和高级整理入口",
        section: "模式",
        action: "set-editor-mode",
        dataset: { "editor-mode": "advanced" },
        keywords: ["advanced", "高级"],
      },
      {
        id: "theme-auto",
        title: "界面外观：自动",
        subtitle: "按时间在浅色和深色之间切换",
        section: "外观",
        action: "set-ui-theme-mode",
        dataset: { "ui-theme-mode": "auto" },
        keywords: ["外观", "主题", "auto"],
      },
      {
        id: "theme-dark",
        title: "界面外观：深色",
        subtitle: "适合夜间写作和沉浸式编辑",
        section: "外观",
        action: "set-ui-theme-mode",
        dataset: { "ui-theme-mode": "dark" },
        keywords: ["外观", "主题", "dark"],
      },
      {
        id: "theme-light",
        title: "界面外观：浅色",
        subtitle: "适合白天整理素材和阅读台本",
        section: "外观",
        action: "set-ui-theme-mode",
        dataset: { "ui-theme-mode": "light" },
        keywords: ["外观", "主题", "light"],
      },
      ...SCREEN_COMMANDS.map((command) => ({
        ...command,
        subtitle: hasProject ? `跳到${command.title}` : disabledProjectTitle,
        action: "switch-screen",
        dataset: { screen: command.screen },
        disabled: !hasProject,
        disabledReason: hasProject ? "" : disabledProjectTitle,
      })),
      {
        id: "create-first-chapter",
        title: "一键创建第一章和第一场景",
        subtitle: hasStructure ? "项目已经有基础结构" : "空白项目最快开工入口",
        section: "开工",
        action: "create-first-chapter",
        disabled: !hasProject || hasStructure,
        disabledReason: !hasProject ? disabledProjectTitle : hasStructure ? "当前项目已有章节和场景" : "",
        keywords: ["章节", "场景", "空白"],
      },
      {
        id: "create-starter-kit",
        title: "补齐起步骨架",
        subtitle: needsStarterKit ? "生成第一位角色、第一张背景和第一首 BGM" : "角色、背景和 BGM 骨架已经够用",
        section: "开工",
        action: "create-starter-kit",
        disabled: !hasProject || !needsStarterKit,
        disabledReason: !hasProject ? disabledProjectTitle : !needsStarterKit ? "当前项目暂不需要起步骨架" : "",
        keywords: ["角色", "背景", "bgm", "起步"],
      },
      {
        id: "export-web",
        title: "导出 Web 试玩包",
        subtitle: canExport ? "生成最容易分享的一版" : hasProject ? "先处理项目巡检错误" : disabledProjectTitle,
        section: "发布",
        action: "export-build",
        dataset: { "export-target": "web" },
        disabled: !canExport,
        disabledReason: !hasProject ? disabledProjectTitle : "项目仍有结构错误，先打开项目巡检",
        keywords: ["导出", "web", "试玩"],
      },
    ];

    return commands;
  }

  function filterCommandPaletteCommands(commands = [], query = "") {
    const normalizedQuery = normalizeSearchText(query);
    if (!normalizedQuery) {
      return commands;
    }
    const terms = normalizedQuery.split(/\s+/).filter(Boolean);
    return commands.filter((command) => {
      const haystack = buildCommandSearchText(command);
      return terms.every((term) => haystack.includes(term));
    });
  }

  function clampCommandPaletteIndex(index, commands = []) {
    if (!commands.length) {
      return 0;
    }
    const numericIndex = Number.parseInt(index ?? 0, 10);
    if (!Number.isFinite(numericIndex)) {
      return 0;
    }
    return Math.max(0, Math.min(commands.length - 1, numericIndex));
  }

  function renderCommandPaletteList(commands = [], selectedIndex = 0, helpers = {}) {
    const escapeHtml = helpers.escapeHtml ?? ((value) => String(value ?? ""));
    if (!commands.length) {
      return `
        <div class="command-palette-empty">
          <strong>没有找到匹配的指令</strong>
          <span>换个关键词试试，比如“剧情”“导出”“素材”。</span>
        </div>
      `;
    }
    return commands
      .map((command, index) => {
        const disabled = Boolean(command.disabled);
        const selectedClass = index === selectedIndex ? " is-selected" : "";
        const disabledClass = disabled ? " is-disabled" : "";
        const reason = disabled && command.disabledReason ? ` · ${command.disabledReason}` : "";
        return `
          <button
            type="button"
            class="command-palette-item${selectedClass}${disabledClass}"
            data-action="run-command-palette-command"
            data-command-id="${escapeHtml(command.id)}"
            role="option"
            aria-selected="${index === selectedIndex ? "true" : "false"}"
            ${disabled ? 'aria-disabled="true"' : ""}
          >
            <span class="command-palette-section">${escapeHtml(command.section ?? "指令")}</span>
            <strong>${escapeHtml(command.title)}</strong>
            <small>${escapeHtml(`${command.subtitle ?? ""}${reason}`)}</small>
          </button>
        `;
      })
      .join("");
  }

  global.CanvasiaEditorCommandPalette = {
    buildCommandPaletteCommands,
    filterCommandPaletteCommands,
    clampCommandPaletteIndex,
    renderCommandPaletteList,
  };
})(window);
