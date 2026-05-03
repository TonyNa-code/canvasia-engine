(function attachAssetCatalogTools(global) {
  const ASSET_TYPE_LABELS = Object.freeze({
    background: "背景",
    sprite: "立绘",
    cg: "CG",
    bgm: "音乐",
    sfx: "音效",
    voice: "语音",
    video: "视频",
    ui: "界面素材",
    font: "字体",
    live2d: "Live2D",
    model3d: "3D 模型",
    scene3d: "3D 场景",
  });

  const ASSET_PRESET_TAGS = Object.freeze({
    background: Object.freeze(["校园", "教室", "走廊", "屋顶", "黄昏", "夜晚", "日常"]),
    sprite: Object.freeze(["默认", "微笑", "害羞", "生气", "悲伤", "女主", "主角"]),
    cg: Object.freeze(["主线", "回忆", "约会", "告白", "高潮", "甜蜜"]),
    bgm: Object.freeze(["日常", "温柔", "紧张", "恋爱", "悲伤", "高潮"]),
    sfx: Object.freeze(["学校", "脚步", "环境", "提示", "门", "点击"]),
    voice: Object.freeze(["女主", "主角", "日常", "情绪", "告白", "独白"]),
    video: Object.freeze(["OP", "ED", "PV", "过场"]),
    ui: Object.freeze(["按钮", "对话框", "名字框", "图标", "菜单"]),
    font: Object.freeze(["正文", "标题", "圆体", "宋体", "手写", "授权确认"]),
    live2d: Object.freeze(["角色", "模型", "表情", "呼吸", "口型"]),
    model3d: Object.freeze(["角色", "GLB", "VRM", "待机", "动作"]),
    scene3d: Object.freeze(["场景", "地图", "房间", "GLB", "交互"]),
  });

  const CHARACTER_PRESENTATION_MODE_LABELS = Object.freeze({
    sprite: "普通立绘",
    layered_sprite: "差分立绘",
    live2d: "Live2D",
    model3d: "3D 模型",
  });

  const ASSET_FILTER_MODE_LABELS = Object.freeze({
    all: "显示全部",
    unused: "仅看未使用",
    missing_file: "仅看待导入",
    urgent_missing: "仅看已引用缺口",
    duplicate: "仅看疑似重复",
    asset3d_risk: "仅看 3D 发布风险",
    media_budget: "仅看素材预算风险",
  });

  const ASSET_FILTER_MODE_STATUS_LABELS = Object.freeze({
    all: "全部素材",
    unused: "未使用素材",
    missing_file: "待导入素材",
    urgent_missing: "已被项目引用但缺文件的素材",
    duplicate: "疑似重复素材",
    asset3d_risk: "最近一次 3D 发布体检标记的风险素材",
    media_budget: "体积偏大、建议发布前压缩的素材",
  });

  const ASSET_MEDIA_BUDGET_LIMITS = Object.freeze({
    background: Object.freeze({ warnBytes: 8 * 1024 * 1024, blockerBytes: 24 * 1024 * 1024, label: "背景图" }),
    sprite: Object.freeze({ warnBytes: 6 * 1024 * 1024, blockerBytes: 18 * 1024 * 1024, label: "立绘" }),
    cg: Object.freeze({ warnBytes: 10 * 1024 * 1024, blockerBytes: 32 * 1024 * 1024, label: "CG" }),
    ui: Object.freeze({ warnBytes: 4 * 1024 * 1024, blockerBytes: 16 * 1024 * 1024, label: "界面素材" }),
    bgm: Object.freeze({ warnBytes: 18 * 1024 * 1024, blockerBytes: 60 * 1024 * 1024, label: "音乐" }),
    sfx: Object.freeze({ warnBytes: 6 * 1024 * 1024, blockerBytes: 18 * 1024 * 1024, label: "音效" }),
    voice: Object.freeze({ warnBytes: 8 * 1024 * 1024, blockerBytes: 24 * 1024 * 1024, label: "语音" }),
    video: Object.freeze({ warnBytes: 120 * 1024 * 1024, blockerBytes: 500 * 1024 * 1024, label: "视频" }),
    font: Object.freeze({ warnBytes: 20 * 1024 * 1024, blockerBytes: 60 * 1024 * 1024, label: "字体" }),
    live2d: Object.freeze({ warnBytes: 40 * 1024 * 1024, blockerBytes: 120 * 1024 * 1024, label: "Live2D" }),
    model3d: Object.freeze({ warnBytes: 80 * 1024 * 1024, blockerBytes: 300 * 1024 * 1024, label: "3D 模型" }),
    scene3d: Object.freeze({ warnBytes: 120 * 1024 * 1024, blockerBytes: 500 * 1024 * 1024, label: "3D 场景" }),
  });

  function hasOwn(source, key) {
    return Object.prototype.hasOwnProperty.call(source, key);
  }

  function getSafeCharacterPresentationMode(mode) {
    return hasOwn(CHARACTER_PRESENTATION_MODE_LABELS, mode) ? mode : "sprite";
  }

  function getCharacterPresentationModeLabel(mode) {
    return CHARACTER_PRESENTATION_MODE_LABELS[getSafeCharacterPresentationMode(mode)] ?? CHARACTER_PRESENTATION_MODE_LABELS.sprite;
  }

  function getSafeAssetFilterMode(filterMode) {
    const safeMode = String(filterMode ?? "").trim();
    return hasOwn(ASSET_FILTER_MODE_LABELS, safeMode) ? safeMode : "all";
  }

  function getAssetFilterModeLabel(filterMode) {
    return ASSET_FILTER_MODE_LABELS[getSafeAssetFilterMode(filterMode)] ?? ASSET_FILTER_MODE_LABELS.all;
  }

  function getAssetFilterModeStatusLabel(filterMode) {
    return ASSET_FILTER_MODE_STATUS_LABELS[getSafeAssetFilterMode(filterMode)] ?? ASSET_FILTER_MODE_STATUS_LABELS.all;
  }

  function getAssetMediaBudgetLimit(asset) {
    if (!asset) {
      return null;
    }
    return ASSET_MEDIA_BUDGET_LIMITS[asset.type] ?? null;
  }

  function getAssetPresetTags(assetType) {
    return ASSET_PRESET_TAGS[assetType] ?? [];
  }

  function getAssetTypeLabel(type) {
    return ASSET_TYPE_LABELS[type] ?? type;
  }

  global.TonyNaEditorAssetCatalog = Object.freeze({
    ASSET_TYPE_LABELS,
    ASSET_PRESET_TAGS,
    CHARACTER_PRESENTATION_MODE_LABELS,
    ASSET_FILTER_MODE_LABELS,
    ASSET_FILTER_MODE_STATUS_LABELS,
    ASSET_MEDIA_BUDGET_LIMITS,
    getSafeCharacterPresentationMode,
    getCharacterPresentationModeLabel,
    getSafeAssetFilterMode,
    getAssetFilterModeLabel,
    getAssetFilterModeStatusLabel,
    getAssetMediaBudgetLimit,
    getAssetPresetTags,
    getAssetTypeLabel,
  });
})(typeof window !== "undefined" ? window : globalThis);
