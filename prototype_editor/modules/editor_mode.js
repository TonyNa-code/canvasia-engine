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
    "add-jump",
  ]);

  const BEGINNER_ASSET_TOOLBAR_ACTIONS = new Set(["pick-assets", "replace-asset-file"]);

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

  global.CanvasiaEditorMode = Object.freeze({
    EDITOR_MODE_LABELS,
    NAV_SCREEN_LABELS,
    BEGINNER_STORY_TOOLBAR_ACTIONS,
    BEGINNER_ASSET_TOOLBAR_ACTIONS,
    getSafeEditorMode,
    getProjectEditorMode,
    isAdvancedEditorMode,
    getEditorModeLabel,
    getNavScreenLabel,
    getEditorModeDescription,
  });
})(typeof window !== "undefined" ? window : globalThis);
