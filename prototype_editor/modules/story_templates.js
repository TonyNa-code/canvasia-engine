(function attachStoryTemplateTools(global) {
  const STORY_TEMPLATE_PRESETS = Object.freeze({
    opening_intro: Object.freeze({
      title: "开场铺垫",
    }),
    memory_entry: Object.freeze({
      title: "进入回忆",
    }),
    emotion_burst: Object.freeze({
      title: "情绪爆点",
    }),
    branch_choice: Object.freeze({
      title: "选项分支",
    }),
    scene_outro: Object.freeze({
      title: "场景收尾",
    }),
  });

  const PROJECT_TEMPLATE_LABELS = Object.freeze({
    blank: "空白项目",
    campus_romance: "校园恋爱模板",
  });

  function getStoryTemplatePreset(templateId) {
    return STORY_TEMPLATE_PRESETS[templateId] ?? null;
  }

  function getTemplateLabel(template) {
    return PROJECT_TEMPLATE_LABELS[template] ?? template;
  }

  global.CanvasiaEditorStoryTemplates = Object.freeze({
    STORY_TEMPLATE_PRESETS,
    PROJECT_TEMPLATE_LABELS,
    getStoryTemplatePreset,
    getTemplateLabel,
  });
})(typeof window !== "undefined" ? window : globalThis);
