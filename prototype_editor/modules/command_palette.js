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

  const STORY_BLOCK_COMMANDS = [
    {
      id: "insert-dialogue",
      title: "插入台词卡",
      subtitle: "在当前选中卡片后加一句角色对白",
      action: "add-dialogue",
      section: "插卡",
      keywords: ["台词", "对白", "dialogue", "角色"],
    },
    {
      id: "insert-narration",
      title: "插入旁白卡",
      subtitle: "补叙述、心理描写或场景说明",
      action: "add-narration",
      section: "插卡",
      keywords: ["旁白", "叙述", "narration", "文字"],
    },
    {
      id: "insert-choice",
      title: "插入选项卡",
      subtitle: "创建可跳转分支的选择项",
      action: "add-choice",
      section: "分支",
      keywords: ["选项", "分支", "choice", "路线"],
    },
    {
      id: "insert-background",
      title: "插入切背景卡",
      subtitle: "切换背景或 3D 场景预览",
      action: "add-background",
      section: "演出",
      keywords: ["背景", "场景", "background", "bg"],
    },
    {
      id: "insert-character-show",
      title: "插入显示角色卡",
      subtitle: "让立绘淡入、定位并调整大小姿态",
      action: "add-character-show",
      section: "演出",
      keywords: ["立绘", "角色", "显示", "show", "淡入"],
    },
    {
      id: "insert-character-hide",
      title: "插入隐藏角色卡",
      subtitle: "让角色退场或淡出",
      action: "add-character-hide",
      section: "演出",
      keywords: ["立绘", "角色", "隐藏", "hide", "淡出"],
    },
    {
      id: "insert-music-play",
      title: "插入播放 BGM 卡",
      subtitle: "指定音乐、循环、音量和淡入淡出",
      action: "add-music-play",
      section: "音频",
      keywords: ["bgm", "音乐", "播放", "music", "淡入"],
    },
    {
      id: "insert-music-stop",
      title: "插入停止 BGM 卡",
      subtitle: "在剧情节点淡出当前音乐",
      action: "add-music-stop",
      section: "音频",
      keywords: ["bgm", "音乐", "停止", "stop", "淡出"],
    },
    {
      id: "insert-sfx",
      title: "插入音效卡",
      subtitle: "播放按钮音、环境音或演出音效",
      action: "add-sfx-play",
      section: "音频",
      keywords: ["音效", "sfx", "sound", "效果音"],
    },
    {
      id: "insert-video",
      title: "插入视频 / OP 卡",
      subtitle: "用于 OP、ED、过场动画或片段播放",
      action: "add-video-play",
      section: "视频",
      keywords: ["视频", "op", "ed", "movie", "video"],
    },
    {
      id: "insert-credits",
      title: "插入片尾字幕卡",
      subtitle: "快速生成 STAFF 滚动字幕",
      action: "add-credits-roll",
      section: "视频",
      keywords: ["片尾", "字幕", "staff", "credits", "ed"],
    },
    {
      id: "insert-particle",
      title: "插入粒子特效卡",
      subtitle: "添加雪、雨、花瓣或项目粒子预设",
      action: "add-particle-effect",
      section: "演出",
      keywords: ["粒子", "下雪", "下雨", "particle", "特效"],
    },
    {
      id: "insert-shake",
      title: "插入屏幕震动卡",
      subtitle: "表现冲击、惊吓或爆点",
      action: "add-screen-shake",
      section: "镜头",
      keywords: ["震动", "shake", "冲击", "镜头"],
    },
    {
      id: "insert-flash",
      title: "插入闪屏卡",
      subtitle: "白闪、红闪或冲击瞬间",
      action: "add-screen-flash",
      section: "镜头",
      keywords: ["闪屏", "flash", "白闪", "红闪"],
    },
    {
      id: "insert-fade",
      title: "插入黑场淡入淡出卡",
      subtitle: "转场、回忆进入或段落收束",
      action: "add-screen-fade",
      section: "镜头",
      keywords: ["黑场", "淡入", "淡出", "fade", "转场"],
    },
    {
      id: "insert-camera-zoom",
      title: "插入镜头推近 / 拉远卡",
      subtitle: "把注意力压到角色或关键画面上",
      action: "add-camera-zoom",
      section: "镜头",
      keywords: ["镜头", "推近", "拉远", "zoom", "camera"],
    },
    {
      id: "insert-camera-pan",
      title: "插入镜头平移卡",
      subtitle: "做视线移动、场景巡视或慢镜头",
      action: "add-camera-pan",
      section: "镜头",
      keywords: ["镜头", "平移", "pan", "camera"],
    },
    {
      id: "insert-filter",
      title: "插入回忆滤镜卡",
      subtitle: "快速进入回忆、梦境或特殊氛围",
      action: "add-screen-filter",
      section: "调色",
      keywords: ["滤镜", "回忆", "调色", "filter", "color"],
    },
    {
      id: "insert-depth-blur",
      title: "插入景深模糊卡",
      subtitle: "突出主体或制造朦胧感",
      action: "add-depth-blur",
      section: "调色",
      keywords: ["景深", "模糊", "blur", "焦点"],
    },
    {
      id: "insert-jump",
      title: "插入跳转场景卡",
      subtitle: "把剧情接到另一个场景",
      action: "add-jump",
      section: "分支",
      keywords: ["跳转", "场景", "jump", "goto"],
    },
    {
      id: "insert-variable-set",
      title: "插入设变量卡",
      subtitle: "记录好感度、Flag 或章节状态",
      action: "add-variable-set",
      section: "逻辑",
      keywords: ["变量", "flag", "好感度", "set"],
    },
    {
      id: "insert-variable-add",
      title: "插入数值变化卡",
      subtitle: "给数值变量加减分",
      action: "add-variable-add",
      section: "逻辑",
      keywords: ["变量", "数值", "加分", "add"],
    },
    {
      id: "insert-condition",
      title: "插入条件判断卡",
      subtitle: "按变量决定下一段剧情",
      action: "add-condition",
      section: "逻辑",
      keywords: ["条件", "判断", "if", "condition", "分支"],
    },
  ];

  const STORY_TEMPLATE_COMMANDS = [
    {
      id: "template-opening-intro",
      title: "套用：开场铺垫",
      subtitle: "背景、BGM、旁白、角色登场和第一句对白",
      templateId: "opening_intro",
      keywords: ["模板", "开场", "opening", "intro"],
    },
    {
      id: "template-memory-entry",
      title: "套用：进入回忆",
      subtitle: "黑场、回忆滤镜、旁白和回忆对白",
      templateId: "memory_entry",
      keywords: ["模板", "回忆", "memory", "filter"],
    },
    {
      id: "template-emotion-burst",
      title: "套用：情绪爆点",
      subtitle: "镜头、震动、闪屏和情绪台词",
      templateId: "emotion_burst",
      keywords: ["模板", "爆点", "情绪", "演出"],
    },
    {
      id: "template-branch-choice",
      title: "套用：选项分支",
      subtitle: "旁白、选择项和分支提示",
      templateId: "branch_choice",
      keywords: ["模板", "选项", "分支", "choice"],
    },
    {
      id: "template-scene-outro",
      title: "套用：场景收尾",
      subtitle: "收束旁白、淡出、跳转或段落结束",
      templateId: "scene_outro",
      keywords: ["模板", "收尾", "outro", "结尾"],
    },
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
    const hasSelectedScene = Boolean(context.hasSelectedScene);
    const hasStructure = Number(context.chapterCount ?? 0) > 0 && Number(context.sceneCount ?? 0) > 0;
    const needsStarterKit = Boolean(context.needsStarterKit);
    const hasValidationErrors = Number(context.errorCount ?? 0) > 0;
    const canExport = hasProject && !hasValidationErrors;
    const disabledProjectTitle = "先新建或打开项目后可用";
    const disabledSceneTitle = hasProject ? "先创建或选择一个场景后可用" : disabledProjectTitle;
    const sceneSubtitle = context.selectedSceneTitle
      ? `插入到当前场景：${context.selectedSceneTitle}`
      : "插入到当前选中的场景";
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
      ...STORY_BLOCK_COMMANDS.map((command) => ({
        ...command,
        subtitle: hasSelectedScene ? `${command.subtitle} · ${sceneSubtitle}` : disabledSceneTitle,
        disabled: !hasSelectedScene,
        disabledReason: hasSelectedScene ? "" : disabledSceneTitle,
      })),
      ...STORY_TEMPLATE_COMMANDS.map((command) => ({
        ...command,
        section: "模板",
        action: "apply-story-template",
        dataset: { "template-id": command.templateId },
        subtitle: hasSelectedScene ? `${command.subtitle} · ${sceneSubtitle}` : disabledSceneTitle,
        disabled: !hasSelectedScene,
        disabledReason: hasSelectedScene ? "" : disabledSceneTitle,
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
