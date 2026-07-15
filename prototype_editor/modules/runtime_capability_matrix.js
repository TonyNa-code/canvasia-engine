(function attachRuntimeCapabilityMatrixTools(global) {
  const storyBlockCatalogTools = global.CanvasiaEditorStoryBlockCatalog || {};
  const dialogBoxReadabilityTools = global.CanvasiaEditorDialogBoxReadability || {};
  const projectSettingsTools = global.CanvasiaEditorProjectSettings || {};

  const FALLBACK_CAPABILITY_ROWS = Object.freeze([
    ["background", "画面", "full", "full", "背景 / CG 在 Web 与原生 Runtime 中播放；3D 场景会走原生结构检查与预览兜底。"],
    ["character_show", "角色", "full", "full", "支持角色登场、表情、站位、舞台参数和基础转场。"],
    ["character_move", "角色", "full", "full", "支持角色平滑走位、换表情、缩放、透明度、翻转、图层与缓动。"],
    ["character_hide", "角色", "full", "full", "支持角色离场和基础转场。"],
    ["dialogue", "文本", "full", "full", "支持说话人、表情同步、打字机、语音和文本历史。"],
    ["narration", "文本", "full", "full", "支持旁白文本、打字机、语音和文本历史。"],
    ["choice", "分支", "full", "full", "支持玩家选项、变量效果和目标场景跳转。"],
    ["condition", "分支", "full", "full", "支持条件分支、否则分支和变量判断。"],
    ["jump", "分支", "full", "full", "支持显式场景跳转。"],
    ["variable_set", "变量", "full", "full", "支持变量赋值。"],
    ["variable_add", "变量", "full", "full", "支持数值变量增减。"],
    ["music_play", "音频", "full", "full", "支持 BGM 播放、循环、音量、淡入和范围调度。"],
    ["music_stop", "音频", "full", "full", "支持 BGM 淡出停止。"],
    ["sfx_play", "音频", "full", "full", "支持音效播放与音量控制。"],
    ["video_play", "视频", "full", "partial", "Web Runtime 支持内嵌播放；原生 Runtime 支持 PyAV / OpenCV / 系统播放器兜底，需按目标平台验收。"],
    ["credits_roll", "结尾", "full", "full", "支持片尾字幕与回想 / 发布检查。"],
    ["wait", "演出", "full", "full", "支持等待 / 停顿节奏卡；自动播放会按设定时长等待。"],
    ["particle_effect", "演出", "full", "full", "支持项目粒子预设、图片粒子、密度、速度、重力和颜色等参数。"],
    ["screen_shake", "演出", "full", "full", "支持屏幕震动。"],
    ["screen_flash", "演出", "full", "full", "支持闪屏。"],
    ["screen_fade", "演出", "full", "full", "支持淡入淡出。"],
    ["camera_zoom", "演出", "full", "full", "支持镜头推近、拉远和重置。"],
    ["camera_pan", "演出", "full", "full", "支持镜头平移和回中。"],
    ["screen_filter", "演出", "full", "full", "支持滤镜、色调和清除。"],
    ["depth_blur", "演出", "full", "full", "支持景深模糊和清除。"],
  ]).map(([type, group, webStatus, nativeStatus, note]) =>
    Object.freeze({ type, group, webStatus, nativeStatus, note })
  );

  const CAPABILITY_ROWS = Object.freeze(
    (typeof storyBlockCatalogTools.getRuntimeCapabilityRows === "function"
      ? storyBlockCatalogTools.getRuntimeCapabilityRows()
      : FALLBACK_CAPABILITY_ROWS
    ).map((row) =>
      Object.freeze({
        type: row.type,
        group: row.group,
        webStatus: row.webStatus,
        nativeStatus: row.nativeStatus,
        note: row.note,
      })
    )
  );

  const STATUS_LABELS = Object.freeze({
    full: "完整支持",
    partial: "需要验收",
    planned: "规划中",
    unsupported: "未支持",
    unknown: "未知卡片",
  });

  const STATUS_WEIGHT = Object.freeze({
    full: 0,
    partial: 1,
    planned: 2,
    unsupported: 3,
    unknown: 4,
  });

  const ACCEPTANCE_TARGET_LABELS = Object.freeze({
    web: "Web Runtime",
    native: "原生 Runtime",
    cross: "Web / 原生",
  });

  const ACCEPTANCE_SEVERITY_LABELS = Object.freeze({
    blocker: "先修",
    warn: "重点验收",
    check: "点测",
  });

  const VISUAL_EFFECT_TYPES = new Set(
    typeof storyBlockCatalogTools.getRuntimeVisualEffectBlockTypes === "function"
      ? storyBlockCatalogTools.getRuntimeVisualEffectBlockTypes()
      : ["wait", "screen_shake", "screen_flash", "screen_fade", "camera_zoom", "camera_pan", "screen_filter", "depth_blur"]
  );

  const VN_ESSENTIAL_STATUS_LABELS = Object.freeze({
    ready: "基础稳",
    needs_fix: "先补基础",
    needs_polish: "建议打磨",
    empty: "待开始",
  });

  const VN_ESSENTIAL_SEVERITY_LABELS = Object.freeze({
    warn: "基础缺口",
    soft: "体验打磨",
  });

  const DEFAULT_FORMAL_SAVE_SLOT_COUNT = 24;

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function toNumber(value, fallback = 0) {
    const number = Number(value);
    return Number.isFinite(number) ? number : fallback;
  }

  function clampNumber(value, minimum, maximum, fallback = minimum) {
    return Math.min(Math.max(toNumber(value, fallback), minimum), maximum);
  }

  function buildCollectionMap(source, idField = "id") {
    const result = new Map();
    if (source instanceof Map) {
      source.forEach((value, id) => {
        if (id) {
          result.set(String(id), value);
        }
      });
      return result;
    }
    if (source && typeof source === "object" && !Array.isArray(source)) {
      Object.entries(source).forEach(([id, value]) => {
        if (id) {
          result.set(String(id), value);
        }
      });
      return result;
    }
    toArray(source).forEach((item) => {
      if (item?.[idField]) {
        result.set(String(item[idField]), item);
      }
    });
    return result;
  }

  function getAssetList(data = {}) {
    return Array.isArray(data.assetList)
      ? data.assetList
      : Array.isArray(data.assets?.assets)
        ? data.assets.assets
        : [];
  }

  function buildAssetMap(data = {}) {
    const assetMap = new Map();
    getAssetList(data).forEach((asset) => {
      if (asset?.id) {
        assetMap.set(String(asset.id), asset);
      }
    });
    buildCollectionMap(data.assetsById).forEach((asset, id) => assetMap.set(id, asset));
    return assetMap;
  }

  function buildSceneMap(data = {}) {
    const sceneMap = new Map();
    toArray(data.scenes).forEach((scene) => {
      if (scene?.id) {
        sceneMap.set(String(scene.id), scene);
      }
    });
    buildCollectionMap(data.scenesById).forEach((scene, id) => sceneMap.set(id, scene));
    toArray(data.chapters).forEach((chapter) => {
      toArray(chapter.scenes).forEach((scene) => {
        if (scene?.id) {
          sceneMap.set(String(scene.id), scene);
        }
      });
    });
    return sceneMap;
  }

  function buildChapterMap(data = {}) {
    return new Map(
      toArray(data.chapters).map((chapter, index) => [
        String(chapter?.id ?? chapter?.chapterId ?? ""),
        {
          id: String(chapter?.id ?? chapter?.chapterId ?? ""),
          name: cleanText(chapter?.name ?? chapter?.title, `章节 ${index + 1}`),
          order: index,
          sceneOrder: toArray(chapter?.sceneOrder).map((sceneId) => String(sceneId ?? "")).filter(Boolean),
        },
      ])
    );
  }

  function getSceneRecords(data = {}) {
    const sceneMap = buildSceneMap(data);
    const chapterMap = buildChapterMap(data);
    const records = [];
    const seenSceneIds = new Set();

    toArray(data.chapters).forEach((chapter, chapterIndex) => {
      const chapterId = String(chapter?.id ?? chapter?.chapterId ?? "");
      const chapterName = cleanText(chapter?.name ?? chapter?.title, `章节 ${chapterIndex + 1}`);
      const directScenes = toArray(chapter?.scenes);
      const orderedIds = toArray(chapter?.sceneOrder).map((sceneId) => String(sceneId ?? "")).filter(Boolean);
      const scenes = directScenes.length
        ? directScenes
        : orderedIds.map((sceneId) => sceneMap.get(sceneId)).filter(Boolean);
      scenes.forEach((scene, sceneIndex) => {
        if (!scene?.id || seenSceneIds.has(String(scene.id))) {
          return;
        }
        seenSceneIds.add(String(scene.id));
        records.push({ scene, sceneIndex, chapterId, chapterName, chapterOrder: chapterIndex });
      });
    });

    toArray(data.scenes).forEach((scene, sceneIndex) => {
      if (!scene?.id || seenSceneIds.has(String(scene.id))) {
        return;
      }
      const chapter = chapterMap.get(String(scene.chapterId ?? ""));
      seenSceneIds.add(String(scene.id));
      records.push({
        scene,
        sceneIndex,
        chapterId: String(scene.chapterId ?? ""),
        chapterName: chapter?.name ?? "未分章",
        chapterOrder: chapter?.order ?? 9999,
      });
    });

    return records.sort((left, right) => {
      if (left.chapterOrder !== right.chapterOrder) {
        return left.chapterOrder - right.chapterOrder;
      }
      return left.sceneIndex - right.sceneIndex;
    });
  }

  function getRuntimeStatusLabel(status = "") {
    return STATUS_LABELS[status] ?? cleanText(status, "未知");
  }

  function getRuntimeAcceptanceTargetLabel(target = "") {
    return ACCEPTANCE_TARGET_LABELS[target] ?? cleanText(target, "全 Runtime");
  }

  function getVnEssentialStatusLabel(status = "") {
    return VN_ESSENTIAL_STATUS_LABELS[status] ?? cleanText(status, "未知");
  }

  function getWorstStatus(...statuses) {
    return statuses.reduce((worst, status) => {
      const safeStatus = status || "unknown";
      return (STATUS_WEIGHT[safeStatus] ?? 99) > (STATUS_WEIGHT[worst] ?? 99) ? safeStatus : worst;
    }, "full");
  }

  function getCapabilityMap() {
    return new Map(CAPABILITY_ROWS.map((row) => [row.type, row]));
  }

  function getRowSceneLabel(row = {}) {
    return toArray(row.usedSceneNames).join(" / ") || "当前项目";
  }

  function hasUsedType(typeSet, type) {
    return Boolean(typeSet.get(type)?.usedCount);
  }

  function buildRuntimeAcceptanceChecklist(rows = [], summary = {}) {
    const usedRows = toArray(rows).filter((row) => (row.usedCount ?? 0) > 0);
    const usedTypeMap = new Map(usedRows.map((row) => [row.type, row]));
    const items = [];
    const seenIds = new Set();

    const addItem = (item) => {
      const id = cleanText(item.id);
      if (!id || seenIds.has(id)) {
        return;
      }
      seenIds.add(id);
      items.push({
        id,
        target: item.target ?? "cross",
        targetLabel: getRuntimeAcceptanceTargetLabel(item.target ?? "cross"),
        severity: item.severity ?? "check",
        severityLabel: ACCEPTANCE_SEVERITY_LABELS[item.severity ?? "check"] ?? "点测",
        title: cleanText(item.title, "Runtime 验收项"),
        detail: cleanText(item.detail, "导出后按目标平台实际跑一遍。"),
        relatedBlockTypes: toArray(item.relatedBlockTypes).map((type) => cleanText(type)).filter(Boolean),
        source: cleanText(item.source, "Runtime 覆盖矩阵"),
        done: false,
      });
    };

    if (!usedRows.length) {
      return {
        items: [],
        summary: {
          itemCount: 0,
          blockerCount: 0,
          warningCount: 0,
          checkCount: 0,
          webItemCount: 0,
          nativeItemCount: 0,
          crossRuntimeItemCount: 0,
        },
      };
    }

    addItem({
      id: "web-runtime-first-run",
      target: "web",
      severity: "check",
      title: "Web 试玩包从入口跑到第一处分支",
      detail: "导出 Web 试玩包后，确认开场背景、第一条台词、菜单、存档和至少一个选项都能正常响应。",
      relatedBlockTypes: usedRows.slice(0, 8).map((row) => row.type),
      source: "基础播放链",
    });
    addItem({
      id: "native-runtime-first-run",
      target: "native",
      severity: (summary.nativePartialCount ?? 0) > 0 ? "warn" : "check",
      title: "原生 Runtime 在目标平台启动并完成一轮读档",
      detail: "至少在准备发布的平台跑一次原生包，确认启动、继续游戏、正式存档、读档、系统菜单、历史文本和退出流程。",
      relatedBlockTypes: usedRows.slice(0, 8).map((row) => row.type),
      source: "基础播放链",
    });

    usedRows.forEach((row) => {
      if (row.overallStatus === "unknown" || row.overallStatus === "unsupported") {
        addItem({
          id: `runtime-support-${row.type}`,
          target: "cross",
          severity: "blocker",
          title: `${row.type} 需要先补 Runtime 支持声明`,
          detail: `${row.type} 已在 ${getRowSceneLabel(row)} 使用，但还没有明确 Web / 原生播放策略。发布前应补矩阵、播放器处理或移除该卡片。`,
          relatedBlockTypes: [row.type],
          source: "未登记卡片",
        });
      } else if (row.overallStatus === "planned") {
        addItem({
          id: `runtime-planned-${row.type}`,
          target: "cross",
          severity: "blocker",
          title: `${row.type} 仍处于规划中`,
          detail: `${row.type} 已进入项目内容，但 Runtime 还没有正式可用路径。建议先改用已支持卡片或补完整播放器能力。`,
          relatedBlockTypes: [row.type],
          source: "规划中卡片",
        });
      }

      if (row.webStatus !== "full" && row.webStatus !== "unknown") {
        addItem({
          id: `web-runtime-${row.type}`,
          target: "web",
          severity: "warn",
          title: `Web Runtime 重点验收 ${row.type}`,
          detail: `${row.type} 在 Web Runtime 不是完整覆盖；导出试玩包后需要确认 ${getRowSceneLabel(row)} 的表现和回退逻辑。`,
          relatedBlockTypes: [row.type],
          source: "Web 覆盖差异",
        });
      }
      if (row.nativeStatus !== "full" && row.nativeStatus !== "unknown") {
        addItem({
          id: `native-runtime-${row.type}`,
          target: "native",
          severity: "warn",
          title: `原生 Runtime 重点验收 ${row.type}`,
          detail: `${row.type} 在原生 Runtime 依赖平台兜底或特殊环境；需要在目标系统确认 ${getRowSceneLabel(row)} 能完整播放。`,
          relatedBlockTypes: [row.type],
          source: "原生覆盖差异",
        });
      }
    });

    if (hasUsedType(usedTypeMap, "video_play")) {
      addItem({
        id: "runtime-video-sync",
        target: "native",
        severity: "warn",
        title: "视频播放要验音画同步、跳过和结束回到剧情",
        detail: "带 OP / ED / 插入视频的项目，要检查视频开始、播放中跳过、播放结束、失败兜底，以及回到下一张剧情卡片是否稳定。",
        relatedBlockTypes: ["video_play"],
        source: "视频链路",
      });
    }

    if (["music_play", "music_stop", "sfx_play"].some((type) => hasUsedType(usedTypeMap, type))) {
      addItem({
        id: "runtime-audio-cues",
        target: "cross",
        severity: "check",
        title: "音频调度要验淡入淡出、循环、音量和范围",
        detail: "确认 BGM 不只是机械连播，而是能按指定剧情范围切换；音效不抢占 BGM，停止和淡出不会残留。",
        relatedBlockTypes: ["music_play", "music_stop", "sfx_play"],
        source: "音频链路",
      });
    }

    if (["character_show", "character_move", "character_hide"].some((type) => hasUsedType(usedTypeMap, type))) {
      addItem({
        id: "runtime-character-stage",
        target: "cross",
        severity: "check",
        title: "立绘登退场与舞台动作要验位置、大小和缓动",
        detail: "确认角色自定义位置、缩放、透明度、走位缓动、隐藏和多角色同屏不会被不同 Runtime 解释成错位或残影。",
        relatedBlockTypes: ["character_show", "character_move", "character_hide"],
        source: "角色舞台",
      });
    }

    if (["dialogue", "narration"].some((type) => hasUsedType(usedTypeMap, type))) {
      addItem({
        id: "runtime-textbox-reading",
        target: "cross",
        severity: "check",
        title: "文字体验要验打字机、文本框、历史和语音回听",
        detail: "确认长文本不溢出，打字机速度、点击快进、历史文本、自动播放和项目级文本框皮肤在导出包里一致。",
        relatedBlockTypes: ["dialogue", "narration"],
        source: "文本链路",
      });
    }

    if (["choice", "condition", "jump", "variable_set", "variable_add"].some((type) => hasUsedType(usedTypeMap, type))) {
      addItem({
        id: "runtime-branch-variables",
        target: "cross",
        severity: "check",
        title: "分支变量要验每条可达路线和坏链兜底",
        detail: "至少跑一条主线、一条分支和一个返回路径，确认变量条件、否则分支、跳转目标和结局候选不会卡死。",
        relatedBlockTypes: ["choice", "condition", "jump", "variable_set", "variable_add"],
        source: "分支链路",
      });
    }

    if (usedRows.some((row) => VISUAL_EFFECT_TYPES.has(row.type))) {
      addItem({
        id: "runtime-visual-effects-reset",
        target: "cross",
        severity: "check",
        title: "镜头与滤镜演出要验播放结束后的复位",
        detail: "震动、闪屏、淡入淡出、镜头移动、滤镜和景深要确认不会遮住 UI，也不会在下一场景残留状态。",
        relatedBlockTypes: Array.from(VISUAL_EFFECT_TYPES),
        source: "演出链路",
      });
    }

    if (hasUsedType(usedTypeMap, "particle_effect")) {
      addItem({
        id: "runtime-particle-budget",
        target: "cross",
        severity: "check",
        title: "粒子效果要验密度、图片粒子和帧率",
        detail: "下雨、下雪、花瓣等粒子要确认密度、速度、重力、颜色和自定义贴图都能播放，并且低配设备不明显掉帧。",
        relatedBlockTypes: ["particle_effect"],
        source: "粒子链路",
      });
    }

    if (hasUsedType(usedTypeMap, "credits_roll")) {
      addItem({
        id: "runtime-credits-ending",
        target: "cross",
        severity: "check",
        title: "片尾字幕要验滚动、跳过和结束归档",
        detail: "确认片尾演职员表滚动速度、跳过、结束后回到标题或回想馆登记都符合项目预期。",
        relatedBlockTypes: ["credits_roll"],
        source: "结尾链路",
      });
    }

    if ((summary.scene3dBackgroundCount ?? 0) > 0) {
      addItem({
        id: "native-runtime-scene3d",
        target: "native",
        severity: "warn",
        title: "3D 场景背景要验资产依赖和原生兜底",
        detail: "检查 glTF / GLB / VRM 依赖、贴图路径、材质槽、动画通道和原生 Runtime 报告，避免导出包缺贴图或只显示空场景。",
        relatedBlockTypes: ["background"],
        source: "3D 资产链路",
      });
    }

    const checklistSummary = {
      itemCount: items.length,
      blockerCount: items.filter((item) => item.severity === "blocker").length,
      warningCount: items.filter((item) => item.severity === "warn").length,
      checkCount: items.filter((item) => item.severity === "check").length,
      webItemCount: items.filter((item) => item.target === "web").length,
      nativeItemCount: items.filter((item) => item.target === "native").length,
      crossRuntimeItemCount: items.filter((item) => item.target === "cross").length,
    };

    return { items, summary: checklistSummary };
  }

  function getSceneBlockRecords(data = {}) {
    const records = [];
    getSceneRecords(data).forEach((record) => {
      toArray(record.scene?.blocks).forEach((block, blockIndex) => {
        records.push({ ...record, block, blockIndex });
      });
    });
    return records;
  }

  function getProjectRuntimeSettings(project = {}) {
    if (typeof projectSettingsTools.getProjectRuntimeSettings === "function") {
      return projectSettingsTools.getProjectRuntimeSettings(project);
    }
    const source = project?.runtimeSettings ?? {};
    return {
      formalSaveSlotCount: clampNumber(
        Math.round(toNumber(source.formalSaveSlotCount, DEFAULT_FORMAL_SAVE_SLOT_COUNT)),
        3,
        120,
        DEFAULT_FORMAL_SAVE_SLOT_COUNT
      ),
    };
  }

  function hasAssetReference(block = {}) {
    return Boolean(cleanText(block.assetId) || cleanText(block.backgroundAssetId) || cleanText(block.cgAssetId));
  }

  function hasMeaningfulTransition(block = {}) {
    const transition = cleanText(block.transition, "none").toLowerCase();
    if (!transition || transition === "none") {
      return false;
    }
    if (!Object.hasOwn(block, "transitionDurationMs")) {
      return true;
    }
    return toNumber(block.transitionDurationMs, 0) !== 0;
  }

  function hasCharacterStageAdjustment(block = {}) {
    const stage = block.stage && typeof block.stage === "object" ? block.stage : {};
    return (
      toNumber(stage.scale ?? block.scale, 100) !== 100 ||
      toNumber(stage.opacity ?? block.opacity, 100) !== 100 ||
      toNumber(stage.offsetX ?? block.offsetX, 0) !== 0 ||
      toNumber(stage.offsetY ?? block.offsetY, 0) !== 0 ||
      toNumber(stage.layer ?? block.layer, 0) !== 0 ||
      Boolean(stage.flipX ?? block.flipX)
    );
  }

  function getMusicEndMode(block = {}) {
    if (typeof storyBlockCatalogTools.getSafeMusicEndMode === "function") {
      return storyBlockCatalogTools.getSafeMusicEndMode(block.endMode);
    }
    const mode = cleanText(block.endMode, "until_next_music");
    return Object.hasOwn({ until_next_music: true, scene_end: true, after_block: true }, mode) ? mode : "until_next_music";
  }

  function buildVnEssentialIssue(severity, code, title, detail, suggestion, area = "story") {
    return {
      severity: severity === "warn" ? "warn" : "soft",
      severityLabel: VN_ESSENTIAL_SEVERITY_LABELS[severity === "warn" ? "warn" : "soft"],
      code,
      area,
      title: cleanText(title, "基础能力提示"),
      detail: cleanText(detail, "当前项目还有可打磨的基础项。"),
      suggestion: cleanText(suggestion, "按提示补齐后，再导出试玩包验证一次。"),
    };
  }

  function buildVnEssentialArea(id, label, issueCodes = [], issues = [], summary = "", detail = "") {
    const relatedIssues = toArray(issues).filter((issue) => issueCodes.includes(issue.code));
    const status = relatedIssues.some((issue) => issue.severity === "warn")
      ? "needs_fix"
      : relatedIssues.length > 0
        ? "needs_polish"
        : "ready";
    return {
      id,
      label,
      status,
      statusLabel: getVnEssentialStatusLabel(status),
      issueCount: relatedIssues.length,
      warnCount: relatedIssues.filter((issue) => issue.severity === "warn").length,
      softCount: relatedIssues.filter((issue) => issue.severity === "soft").length,
      summary: cleanText(summary, label),
      detail: cleanText(detail, relatedIssues[0]?.suggestion ?? "这一块基础体验暂时稳定。"),
    };
  }

  function getDialogBoxReadabilityReport(data = {}) {
    if (typeof dialogBoxReadabilityTools.buildDialogBoxReadabilityReport !== "function") {
      return null;
    }
    try {
      return dialogBoxReadabilityTools.buildDialogBoxReadabilityReport(data);
    } catch (_error) {
      return null;
    }
  }

  function buildVnEssentialsAudit(data = {}) {
    const blockRecords = getSceneBlockRecords(data);
    const sceneRecords = getSceneRecords(data);
    const sceneCount = sceneRecords.length;
    const project = data.project ?? {};
    const runtimeSettings = getProjectRuntimeSettings(project);
    const assetMap = buildAssetMap(data);
    const issues = [];
    const sceneIdsWithBackground = new Set();
    const sceneIdsWithMusic = new Set();
    const sceneIdsWithEffects = new Set();
    const characterPositions = new Set();
    const referencedBgAssetIds = new Set();
    const referencedMusicAssetIds = new Set();
    const assetCounts = { bgm: 0, video: 0, ui: 0, font: 0 };

    getAssetList(data).forEach((asset) => {
      const assetType = cleanText(asset?.type);
      if (assetType === "bgm" || assetType === "audio") {
        assetCounts.bgm += 1;
      }
      if (assetType === "video") {
        assetCounts.video += 1;
      }
      if (assetType === "ui") {
        assetCounts.ui += 1;
      }
      if (assetType === "font") {
        assetCounts.font += 1;
      }
    });

    const metrics = {
      sceneCount,
      blockCount: blockRecords.length,
      dialogueCount: 0,
      narrationCount: 0,
      choiceCount: 0,
      conditionCount: 0,
      jumpCount: 0,
      variableMutationCount: 0,
      choiceEffectCount: 0,
      backgroundBlockCount: 0,
      backgroundTransitionCount: 0,
      scenesWithBackground: 0,
      characterShowCount: 0,
      characterMoveCount: 0,
      characterHideCount: 0,
      characterTransitionCount: 0,
      characterPositionVariantCount: 0,
      characterStageAdjustmentCount: 0,
      musicPlayCount: 0,
      musicStopCount: 0,
      musicScopedCount: 0,
      musicFadeInCount: 0,
      musicFadeOutCount: 0,
      sfxPlayCount: 0,
      videoPlayCount: 0,
      scenesWithMusic: 0,
      scenesWithEffects: 0,
      textBoxIssueCount: 0,
      textBoxDangerCount: 0,
      formalSaveSlotCount: runtimeSettings.formalSaveSlotCount,
      bgmAssetCount: assetCounts.bgm,
      videoAssetCount: assetCounts.video,
      uiAssetCount: assetCounts.ui,
      fontAssetCount: assetCounts.font,
      referencedBackgroundAssetCount: 0,
      referencedMusicAssetCount: 0,
    };

    blockRecords.forEach(({ block, scene }) => {
      const type = cleanText(block?.type, "unknown");
      const sceneId = cleanText(scene?.id ?? scene?.sceneId, `scene_${metrics.sceneCount}`);
      if (["screen_shake", "screen_flash", "screen_fade", "camera_zoom", "camera_pan", "screen_filter", "depth_blur", "particle_effect", "wait"].includes(type)) {
        sceneIdsWithEffects.add(sceneId);
      }

      if (type === "dialogue") {
        metrics.dialogueCount += 1;
      } else if (type === "narration") {
        metrics.narrationCount += 1;
      } else if (type === "choice") {
        metrics.choiceCount += 1;
        toArray(block.options).forEach((option) => {
          metrics.choiceEffectCount += toArray(option?.effects).length;
        });
      } else if (type === "condition") {
        metrics.conditionCount += 1;
      } else if (type === "jump") {
        metrics.jumpCount += 1;
      } else if (type === "variable_set" || type === "variable_add") {
        metrics.variableMutationCount += 1;
      } else if (type === "background") {
        metrics.backgroundBlockCount += 1;
        sceneIdsWithBackground.add(sceneId);
        if (hasMeaningfulTransition(block)) {
          metrics.backgroundTransitionCount += 1;
        }
        if (hasAssetReference(block)) {
          referencedBgAssetIds.add(cleanText(block.assetId ?? block.backgroundAssetId ?? block.cgAssetId));
        }
      } else if (type === "character_show") {
        metrics.characterShowCount += 1;
        characterPositions.add(cleanText(block.position, "center"));
        if (hasMeaningfulTransition(block)) {
          metrics.characterTransitionCount += 1;
        }
        if (hasCharacterStageAdjustment(block)) {
          metrics.characterStageAdjustmentCount += 1;
        }
      } else if (type === "character_move") {
        metrics.characterMoveCount += 1;
        characterPositions.add(cleanText(block.position, "center"));
        if (hasCharacterStageAdjustment(block)) {
          metrics.characterStageAdjustmentCount += 1;
        }
      } else if (type === "character_hide") {
        metrics.characterHideCount += 1;
        if (hasMeaningfulTransition(block)) {
          metrics.characterTransitionCount += 1;
        }
      } else if (type === "music_play") {
        metrics.musicPlayCount += 1;
        sceneIdsWithMusic.add(sceneId);
        const endMode = getMusicEndMode(block);
        if (endMode !== "until_next_music") {
          metrics.musicScopedCount += 1;
        }
        if (toNumber(block.fadeInMs, 0) > 0) {
          metrics.musicFadeInCount += 1;
        }
        if (endMode !== "until_next_music" && toNumber(block.fadeOutMs, 0) > 0) {
          metrics.musicFadeOutCount += 1;
        }
        if (cleanText(block.assetId)) {
          referencedMusicAssetIds.add(cleanText(block.assetId));
        }
      } else if (type === "music_stop") {
        metrics.musicStopCount += 1;
        if (toNumber(block.fadeOutMs, 0) > 0) {
          metrics.musicFadeOutCount += 1;
        }
      } else if (type === "sfx_play") {
        metrics.sfxPlayCount += 1;
      } else if (type === "video_play") {
        metrics.videoPlayCount += 1;
      }
    });

    metrics.scenesWithBackground = sceneIdsWithBackground.size;
    metrics.scenesWithMusic = sceneIdsWithMusic.size;
    metrics.scenesWithEffects = sceneIdsWithEffects.size;
    metrics.characterPositionVariantCount = characterPositions.size;
    metrics.referencedBackgroundAssetCount = [...referencedBgAssetIds].filter((id) => assetMap.has(id)).length;
    metrics.referencedMusicAssetCount = [...referencedMusicAssetIds].filter((id) => assetMap.has(id)).length;
    metrics.textBlockCount = metrics.dialogueCount + metrics.narrationCount + metrics.choiceCount;
    metrics.branchBlockCount = metrics.choiceCount + metrics.conditionCount + metrics.jumpCount;

    if (sceneCount > 0 && metrics.textBlockCount === 0) {
      issues.push(buildVnEssentialIssue("warn", "story_text_missing", "缺少可读剧情文本", "当前项目已有场景，但没有台词、旁白或选项卡片。", "先补一段可从入口读到的文本，再做导出试玩。", "story"));
    }
    if (sceneCount > 0 && metrics.scenesWithBackground < sceneCount) {
      issues.push(buildVnEssentialIssue("warn", "background_coverage", "背景覆盖不完整", `${sceneCount - metrics.scenesWithBackground} 个场景还没有背景 / CG / 3D 场景卡片。`, "给每个可试玩场景至少放一张画面素材，避免黑屏式试玩体验。", "visual"));
    }
    if (metrics.backgroundBlockCount >= 2 && metrics.backgroundTransitionCount === 0) {
      issues.push(buildVnEssentialIssue("soft", "background_transition_missing", "背景切换缺少基础转场", "多张背景卡片没有检测到淡入淡出或其他过渡。", "章节开头或场景切换建议设置 400-1000ms 的淡入淡出。", "visual"));
    }
    if (metrics.dialogueCount >= 3 && metrics.characterShowCount === 0) {
      issues.push(buildVnEssentialIssue("soft", "character_stage_missing", "人物登场演出偏弱", "台词已经成段，但没有检测到角色登场卡片。", "给主要角色补显示/隐藏、位置、缩放和淡入淡出，让试玩更像正式 VN。", "character"));
    }
    if (sceneCount >= 2 && metrics.characterShowCount > 0 && metrics.characterHideCount === 0) {
      issues.push(buildVnEssentialIssue("soft", "character_hide_missing", "角色退场节奏未标记", "检测到角色登场，但没有隐藏角色卡片。", "章节切换或角色离场时补隐藏卡片，避免立绘残留。", "character"));
    }
    if (metrics.characterShowCount >= 3 && metrics.characterTransitionCount === 0) {
      issues.push(buildVnEssentialIssue("soft", "character_transition_missing", "人物登场缺少基础转场", `${metrics.characterShowCount} 次角色登场没有使用淡入、滑入、上浮或弹出。`, "关键情绪点给角色登退场加轻量转场，减少硬切。", "character"));
    }
    const characterStageCueCount = metrics.characterShowCount + metrics.characterMoveCount;
    if (characterStageCueCount >= 3 && metrics.characterPositionVariantCount <= 1) {
      issues.push(buildVnEssentialIssue("soft", "character_position_static", "人物站位过于固定", `${characterStageCueCount} 次登场/动作只使用了 ${metrics.characterPositionVariantCount} 种站位。`, "对话双方或重点角色建议使用 left / center / right，并用角色动作卡完成场内调度。", "character"));
    }
    if (characterStageCueCount >= 4 && metrics.characterStageAdjustmentCount === 0) {
      issues.push(buildVnEssentialIssue("soft", "character_stage_static", "人物舞台参数没有变化", "多次角色登场/动作没有检测到缩放、透明度、偏移、翻转或层级调整。", "近景、回忆或压迫感段落可以适当使用缩放/透明度/偏移。", "character"));
    }
    if (sceneCount >= 2 && metrics.musicPlayCount === 0) {
      issues.push(buildVnEssentialIssue("soft", "bgm_plan_missing", "缺少 BGM 进入点", "多场景项目没有检测到播放 BGM 卡片。", "为章节开头、转场或情绪段落设置 BGM，并确认导出包里能按范围切换。", "audio"));
    }
    if (metrics.musicPlayCount >= 2 && metrics.musicScopedCount === 0 && metrics.musicStopCount === 0) {
      issues.push(buildVnEssentialIssue("warn", "bgm_scope_missing", "多首 BGM 缺少明确播放范围", `检测到 ${metrics.musicPlayCount} 个 BGM 播放点，但没有 scene_end / after_block 范围或停止音乐卡片。`, "给每首关键曲目设置结束范围，避免音乐覆盖到不该出现的文本段落。", "audio"));
    }
    if (metrics.musicPlayCount > 0 && metrics.musicFadeInCount < metrics.musicPlayCount) {
      issues.push(buildVnEssentialIssue("soft", "bgm_fade_in_missing", "部分 BGM 没有淡入", `${metrics.musicPlayCount - metrics.musicFadeInCount} 个 BGM 播放点没有设置淡入时间。`, "给 BGM 播放卡片设置 400-1000ms 淡入，减少切歌突兀感。", "audio"));
    }
    if (metrics.musicStopCount > 0 && metrics.musicFadeOutCount < metrics.musicStopCount) {
      issues.push(buildVnEssentialIssue("soft", "bgm_fade_out_missing", "部分停止音乐没有淡出", `${metrics.musicStopCount - metrics.musicFadeOutCount} 个停止音乐卡片没有淡出。`, "给停止音乐卡片设置淡出，让场景切换和静音段落更自然。", "audio"));
    }
    if (sceneCount >= 3 && metrics.sfxPlayCount === 0) {
      issues.push(buildVnEssentialIssue("soft", "sfx_plan_missing", "缺少基础音效点", "多场景项目没有检测到音效卡片。", "给脚步、门铃、短信提示、心跳或关键演出补少量音效点。", "audio"));
    }
    if (metrics.videoAssetCount > 0 && metrics.videoPlayCount === 0) {
      issues.push(buildVnEssentialIssue("soft", "video_asset_unused", "视频素材还没有进入剧情", `检测到 ${metrics.videoAssetCount} 个视频素材，但没有播放视频卡片。`, "如果这些是 OP、ED 或过场动画，建议放入对应章节并跑一次 Runtime 视频验收。", "media"));
    }
    if (sceneCount >= 2 && metrics.choiceCount === 0) {
      issues.push(buildVnEssentialIssue("soft", "choice_node_missing", "缺少可交互选项", "多场景项目没有检测到选项卡片。", "如果目标不是纯电子书，建议至少加入一个选项、分支或可回收差分。", "branch"));
    }
    if (metrics.choiceCount > 0 && metrics.choiceEffectCount === 0 && metrics.variableMutationCount === 0 && metrics.conditionCount === 0) {
      issues.push(buildVnEssentialIssue("soft", "choice_consequence_missing", "选项后果还不明显", "检测到选项，但没有变量效果、变量卡片或条件分支。", "为关键选项补好感度、路线旗标或后续条件读取，避免玩家觉得是假按钮。", "branch"));
    }
    if (sceneCount >= 6 && metrics.formalSaveSlotCount < 12) {
      issues.push(buildVnEssentialIssue("soft", "save_slot_count_low", "正式存档位可能偏少", `当前 ${sceneCount} 个场景配置了 ${metrics.formalSaveSlotCount} 个正式存档位。`, "中长篇 Demo 建议至少 12-24 个正式存档位；多路线作品可提高到 50 个以上。", "system"));
    }

    const dialogBoxReport = getDialogBoxReadabilityReport(data);
    if (dialogBoxReport) {
      metrics.textBoxIssueCount = toArray(dialogBoxReport.issues).length;
      metrics.textBoxDangerCount = toArray(dialogBoxReport.issues).filter((issue) => issue.severity === "danger").length;
      if (metrics.textBoxIssueCount > 0) {
        const firstIssue = dialogBoxReport.issues[0];
        issues.push(
          buildVnEssentialIssue(
            metrics.textBoxDangerCount > 0 ? "warn" : "soft",
            "dialog_box_readability",
            "文本框可读性需要复看",
            `${firstIssue.title}：${firstIssue.detail}`,
            "到项目设置里使用文本框可读性自动优化，或手动调整底色、透明度、宽高、内边距和文字颜色。",
            "textbox"
          )
        );
      }
    }

    const gameUiConfig = project.gameUiConfig ?? {};
    const hasCustomUiAsset = [
      "titleLogoAssetId",
      "titleBackgroundAssetId",
      "panelFrameAssetId",
      "buttonFrameAssetId",
      "saveSlotFrameAssetId",
      "systemPanelFrameAssetId",
      "uiOverlayAssetId",
      "fontAssetId",
    ].some((field) => cleanText(gameUiConfig[field]));
    const hasCustomUiPalette = Boolean(cleanText(gameUiConfig.fontFamily)) || cleanText(gameUiConfig.preset) === "custom";
    if (sceneCount >= 2 && !hasCustomUiAsset && !hasCustomUiPalette) {
      issues.push(buildVnEssentialIssue("soft", "game_ui_skin_default", "游戏 UI 仍接近默认皮肤", "没有检测到标题图、Logo、九宫格按钮/面板、字体或自定义 UI 贴图。", "正式发布前可以保留默认皮肤，但建议至少换标题图、Logo 或按钮状态，让作品更有辨识度。", "ui"));
    }
    if (metrics.fontAssetCount > 0 && !cleanText(gameUiConfig.fontAssetId)) {
      issues.push(buildVnEssentialIssue("soft", "font_asset_unbound", "字体素材尚未绑定到游戏 UI", `素材库里有 ${metrics.fontAssetCount} 个字体素材，但项目 UI 没有绑定字体素材。`, "如果这是作品正式字体，建议在项目设置里绑定，保证导出包和原生 Runtime 字体一致。", "ui"));
    }

    const areas = [
      buildVnEssentialArea("story", "剧情文本", ["story_text_missing"], issues, `${metrics.textBlockCount} 个文本/选项块`, "先保证入口能读到一段完整剧情。"),
      buildVnEssentialArea("visual", "画面背景", ["background_coverage", "background_transition_missing"], issues, `${metrics.scenesWithBackground}/${sceneCount} 个场景有背景`, "每个可试玩场景至少要有画面锚点。"),
      buildVnEssentialArea(
        "character",
        "人物舞台",
        ["character_stage_missing", "character_hide_missing", "character_transition_missing", "character_position_static", "character_stage_static"],
        issues,
        `${metrics.characterShowCount} 次登场 / ${metrics.characterMoveCount} 次动作 / ${metrics.characterPositionVariantCount} 种站位`,
        "检查立绘显示、隐藏、站位、缩放和转场。"
      ),
      buildVnEssentialArea(
        "audio",
        "音频调度",
        ["bgm_plan_missing", "bgm_scope_missing", "bgm_fade_in_missing", "bgm_fade_out_missing", "sfx_plan_missing"],
        issues,
        `${metrics.musicPlayCount} 个 BGM / ${metrics.sfxPlayCount} 个音效`,
        "BGM 应按文本范围、场景或停止卡控制，而不是机械连播。"
      ),
      buildVnEssentialArea("branch", "分支变量", ["choice_node_missing", "choice_consequence_missing"], issues, `${metrics.choiceCount} 个选项 / ${metrics.conditionCount} 个条件`, "至少让关键选项有可解释后果。"),
      buildVnEssentialArea("textbox", "文本框可读性", ["dialog_box_readability"], issues, `${metrics.textBoxIssueCount} 个可读性提示`, "长文本、浅色背景和复杂 CG 下要能看清。"),
      buildVnEssentialArea("system", "存档与系统项", ["save_slot_count_low"], issues, `${metrics.formalSaveSlotCount} 个正式存档位`, "中长篇作品需要足够手动存档空间。"),
      buildVnEssentialArea("ui", "游戏 UI 皮肤", ["game_ui_skin_default", "font_asset_unbound"], issues, hasCustomUiAsset || hasCustomUiPalette ? "已检测到自定义 UI 线索" : "接近默认皮肤", "作品自己的 Logo、字体、按钮和面板会显著提升完成感。"),
      buildVnEssentialArea("media", "视频与额外素材", ["video_asset_unused"], issues, `${metrics.videoPlayCount}/${metrics.videoAssetCount} 个视频已入剧情`, "OP / ED / 过场视频要确认能在导出包播放。"),
    ];

    const warnCount = issues.filter((issue) => issue.severity === "warn").length;
    const softCount = issues.filter((issue) => issue.severity === "soft").length;
    const readyAreaCount = areas.filter((area) => area.status === "ready").length;
    const score = sceneCount === 0
      ? 0
      : Math.max(0, Math.round(100 - warnCount * 14 - softCount * 6 - (areas.length - readyAreaCount) * 2));
    const status = sceneCount === 0 ? "empty" : warnCount > 0 ? "needs_fix" : softCount > 0 ? "needs_polish" : "ready";

    return {
      status,
      statusLabel: getVnEssentialStatusLabel(status),
      summary: {
        score,
        areaCount: areas.length,
        readyAreaCount,
        attentionAreaCount: areas.length - readyAreaCount,
        warnCount,
        softCount,
        issueCount: issues.length,
        recommendation: issues[0]?.suggestion ?? (sceneCount === 0 ? "先创建第一个场景和第一段文本。" : "基础视觉小说体验未发现明显缺口，可以继续做实机点测。"),
      },
      metrics,
      areas,
      issues,
    };
  }

  function addUsage(usageMap, block, record, assetMap) {
    const type = cleanText(block?.type, "unknown");
    const usage =
      usageMap.get(type) ??
      {
        type,
        count: 0,
        sceneNames: new Set(),
        chapterNames: new Set(),
        scene3dCount: 0,
      };
    usage.count += 1;
    usage.sceneNames.add(cleanText(record.scene?.name ?? record.scene?.title, record.scene?.id ?? "未命名场景"));
    usage.chapterNames.add(cleanText(record.chapterName, "未分章"));
    if (type === "background") {
      const asset = assetMap.get(cleanText(block.assetId));
      if (asset?.type === "scene3d") {
        usage.scene3dCount += 1;
      }
    }
    usageMap.set(type, usage);
  }

  function buildRuntimeCapabilityMatrix(data = {}) {
    const assetMap = buildAssetMap(data);
    const capabilityMap = getCapabilityMap();
    const usageMap = new Map();
    let totalBlockCount = 0;

    getSceneRecords(data).forEach((record) => {
      toArray(record.scene?.blocks).forEach((block) => {
        totalBlockCount += 1;
        addUsage(usageMap, block, record, assetMap);
      });
    });

    const rows = CAPABILITY_ROWS.map((capability) => {
      const usage = usageMap.get(capability.type);
      const nativeStatus = usage?.scene3dCount ? getWorstStatus(capability.nativeStatus, "partial") : capability.nativeStatus;
      return {
        ...capability,
        nativeStatus,
        usedCount: usage?.count ?? 0,
        scene3dCount: usage?.scene3dCount ?? 0,
        usedSceneNames: usage ? Array.from(usage.sceneNames).slice(0, 5) : [],
        usedChapterNames: usage ? Array.from(usage.chapterNames).slice(0, 5) : [],
        overallStatus: getWorstStatus(capability.webStatus, nativeStatus),
        webStatusLabel: getRuntimeStatusLabel(capability.webStatus),
        nativeStatusLabel: getRuntimeStatusLabel(nativeStatus),
        overallStatusLabel: getRuntimeStatusLabel(getWorstStatus(capability.webStatus, nativeStatus)),
      };
    });

    const unknownRows = Array.from(usageMap.values())
      .filter((usage) => !capabilityMap.has(usage.type))
      .map((usage) => ({
        type: usage.type,
        group: "未知",
        webStatus: "unknown",
        nativeStatus: "unknown",
        overallStatus: "unknown",
        webStatusLabel: getRuntimeStatusLabel("unknown"),
        nativeStatusLabel: getRuntimeStatusLabel("unknown"),
        overallStatusLabel: getRuntimeStatusLabel("unknown"),
        usedCount: usage.count,
        scene3dCount: usage.scene3dCount,
        usedSceneNames: Array.from(usage.sceneNames).slice(0, 5),
        usedChapterNames: Array.from(usage.chapterNames).slice(0, 5),
        note: "这个卡片类型还没有登记 Runtime 覆盖状态，需要先补矩阵和播放器支持。",
      }));

    const allRows = [...rows, ...unknownRows].sort((left, right) => {
      const leftUsed = left.usedCount > 0 ? 0 : 1;
      const rightUsed = right.usedCount > 0 ? 0 : 1;
      if (leftUsed !== rightUsed) {
        return leftUsed - rightUsed;
      }
      if ((STATUS_WEIGHT[right.overallStatus] ?? 0) !== (STATUS_WEIGHT[left.overallStatus] ?? 0)) {
        return (STATUS_WEIGHT[right.overallStatus] ?? 0) - (STATUS_WEIGHT[left.overallStatus] ?? 0);
      }
      return left.type.localeCompare(right.type, "en-US");
    });

    const usedRows = allRows.filter((row) => row.usedCount > 0);
    const issues = usedRows
      .filter((row) => row.overallStatus !== "full")
      .map((row) => ({
        severity: row.overallStatus === "unknown" || row.overallStatus === "unsupported" ? "blocker" : "warn",
        code: `runtime_${row.overallStatus}`,
        title: `${row.type}：${row.overallStatusLabel}`,
        detail: row.scene3dCount
          ? `${row.note} 当前还有 ${row.scene3dCount} 张 3D 场景背景，建议重点验收原生 Runtime。`
          : row.note,
        blockType: row.type,
        group: row.group,
        usedCount: row.usedCount,
        sceneNames: row.usedSceneNames,
      }));
    const summary = {
      capabilityCount: rows.length,
      totalBlockCount,
      usedTypeCount: usedRows.length,
      fullUsedTypeCount: usedRows.filter((row) => row.overallStatus === "full").length,
      partialUsedTypeCount: usedRows.filter((row) => row.overallStatus === "partial").length,
      unsupportedUsedTypeCount: usedRows.filter((row) => ["planned", "unsupported"].includes(row.overallStatus)).length,
      unknownUsedTypeCount: unknownRows.filter((row) => row.usedCount > 0).length,
      webPartialCount: usedRows.filter((row) => row.webStatus !== "full").length,
      nativePartialCount: usedRows.filter((row) => row.nativeStatus !== "full").length,
      scene3dBackgroundCount: usedRows.reduce((total, row) => total + (row.scene3dCount ?? 0), 0),
      issueCount: issues.length,
    };

    const acceptance = buildRuntimeAcceptanceChecklist(allRows, summary);
    const essentials = buildVnEssentialsAudit(data);

    return {
      projectTitle: cleanText(data.project?.title, "Canvasia Project"),
      rows: allRows,
      usedRows,
      issues,
      summary,
      acceptance,
      essentials,
    };
  }

  function getRuntimeCapabilityStatusDigest(matrix = {}) {
    const summary = matrix.summary ?? {};
    if ((summary.totalBlockCount ?? 0) === 0) {
      return {
        status: "empty",
        title: "还没有可检查的剧情卡片",
        detail: "项目里还没有剧情卡片。开始写第一场后，这里会检查 Web / 原生 Runtime 覆盖状态。",
      };
    }
    if ((summary.unknownUsedTypeCount ?? 0) > 0 || (summary.unsupportedUsedTypeCount ?? 0) > 0) {
      return {
        status: "blocked",
        title: "存在未确认 Runtime 支持",
        detail: "当前项目使用了尚未登记或未支持的卡片类型，建议先补 Runtime 支持再发布。",
      };
    }
    if ((summary.partialUsedTypeCount ?? 0) > 0 || (summary.nativePartialCount ?? 0) > 0 || (summary.webPartialCount ?? 0) > 0) {
      return {
        status: "warn",
        title: `${summary.partialUsedTypeCount ?? 0} 类卡片需要重点验收`,
        detail: "当前卡片可以导出，但部分能力在不同 Runtime 中依赖兜底或目标平台环境，发布前建议跑一遍对应包。",
      };
    }
    return {
      status: "ready",
      title: "Runtime 覆盖稳定",
      detail: "当前项目使用的卡片类型在 Web Runtime 和原生 Runtime 中都有完整覆盖。",
    };
  }

  function escapeMarkdownTableCell(value) {
    return String(value ?? "")
      .replace(/\|/g, "\\|")
      .replace(/\r?\n/g, "<br />")
      .trim();
  }

  function buildMarkdownTable(headers = [], rows = []) {
    const safeRows = toArray(rows);
    if (!safeRows.length) {
      return "";
    }
    return [
      `| ${toArray(headers).map(escapeMarkdownTableCell).join(" | ")} |`,
      `| ${toArray(headers).map(() => "---").join(" | ")} |`,
      ...safeRows.map((row) => `| ${toArray(row).map(escapeMarkdownTableCell).join(" | ")} |`),
    ].join("\n");
  }

  function csvCell(value) {
    return `"${String(value ?? "").replace(/"/g, '""')}"`;
  }

  function buildCsv(headers = [], rows = []) {
    return [headers, ...rows].map((row) => toArray(row).map(csvCell).join(",")).join("\n");
  }

  function buildRuntimeCapabilityMarkdown(matrix = {}, options = {}) {
    const summary = matrix.summary ?? {};
    const digest = getRuntimeCapabilityStatusDigest(matrix);
    const projectTitle = cleanText(options.projectTitle ?? matrix.projectTitle, "Canvasia Project");
    const generatedAt = cleanText(options.generatedAt);
    const usedRows = toArray(matrix.usedRows).map((row) => [
      row.group,
      row.type,
      row.usedCount,
      row.webStatusLabel,
      row.nativeStatusLabel,
      row.overallStatusLabel,
      row.usedSceneNames.join(" / "),
      row.note,
    ]);
    const issueRows = toArray(matrix.issues).map((issue, index) => [
      index + 1,
      issue.severity === "blocker" ? "先修" : "验收",
      issue.blockType,
      issue.usedCount,
      issue.sceneNames.join(" / "),
      issue.detail,
    ]);
    const acceptanceRows = toArray(matrix.acceptance?.items).map((item, index) => [
      index + 1,
      item.targetLabel,
      item.severityLabel,
      item.title,
      item.relatedBlockTypes.join(" / "),
      item.detail,
    ]);
    const essentials = matrix.essentials ?? {};
    const essentialsSummary = essentials.summary ?? {};
    const essentialAreaRows = toArray(essentials.areas).map((area) => [
      area.label,
      area.statusLabel,
      area.summary,
      area.detail,
    ]);
    const essentialIssueRows = toArray(essentials.issues).map((issue, index) => [
      index + 1,
      issue.severityLabel,
      issue.title,
      issue.detail,
      issue.suggestion,
    ]);

    return [
      `# ${projectTitle} Runtime 覆盖矩阵`,
      "",
      generatedAt ? `生成时间：${generatedAt}` : "",
      "",
      `状态：${digest.title}`,
      "",
      digest.detail,
      "",
      "## 总览",
      "",
      buildMarkdownTable(
        ["剧情卡片", "已用类型", "完整类型", "需验收类型", "未知类型", "Web 风险", "原生风险", "3D 场景背景"],
        [
          [
            summary.totalBlockCount ?? 0,
            summary.usedTypeCount ?? 0,
            summary.fullUsedTypeCount ?? 0,
            summary.partialUsedTypeCount ?? 0,
            summary.unknownUsedTypeCount ?? 0,
            summary.webPartialCount ?? 0,
            summary.nativePartialCount ?? 0,
            summary.scene3dBackgroundCount ?? 0,
          ],
        ]
      ),
      "",
      "## 已使用卡片",
      "",
      buildMarkdownTable(["分组", "卡片类型", "使用次数", "Web Runtime", "原生 Runtime", "总体", "使用场景", "说明"], usedRows) ||
        "当前项目还没有剧情卡片。",
      "",
      "## VN 基础能力成熟度",
      "",
      buildMarkdownTable(
        ["基础分", "状态", "稳妥项", "需关注项", "基础缺口", "体验打磨", "建议"],
        [
          [
            `${essentialsSummary.score ?? 0}/100`,
            essentials.statusLabel ?? "待检查",
            essentialsSummary.readyAreaCount ?? 0,
            essentialsSummary.attentionAreaCount ?? 0,
            essentialsSummary.warnCount ?? 0,
            essentialsSummary.softCount ?? 0,
            essentialsSummary.recommendation ?? "",
          ],
        ]
      ),
      "",
      buildMarkdownTable(["领域", "状态", "当前情况", "处理提示"], essentialAreaRows) || "当前项目还没有可分析的 VN 基础能力。",
      "",
      buildMarkdownTable(["序号", "级别", "基础缺口", "说明", "建议"], essentialIssueRows) || "当前没有明显基础能力缺口。",
      "",
      "## 需要重点验收",
      "",
      buildMarkdownTable(["序号", "级别", "卡片类型", "使用次数", "场景", "说明"], issueRows) || "当前没有 Runtime 覆盖风险。",
      "",
      "## Runtime 验收清单",
      "",
      buildMarkdownTable(["序号", "目标", "级别", "验收项", "相关卡片", "说明"], acceptanceRows) ||
        "当前项目还没有可生成验收清单的剧情卡片。",
      "",
    ].join("\n");
  }

  function buildRuntimeCapabilityCsv(matrix = {}) {
    const rows = toArray(matrix.rows).map((row) => [
      row.group,
      row.type,
      row.usedCount,
      row.webStatusLabel,
      row.nativeStatusLabel,
      row.overallStatusLabel,
      row.usedSceneNames.join(" / "),
      row.note,
    ]);
    return `\uFEFF${buildCsv(["分组", "卡片类型", "使用次数", "Web Runtime", "原生 Runtime", "总体", "使用场景", "说明"], rows)}\n`;
  }

  global.CanvasiaEditorRuntimeCapabilityMatrix = Object.freeze({
    CAPABILITY_ROWS,
    FALLBACK_CAPABILITY_ROWS,
    buildRuntimeCapabilityMatrix,
    buildRuntimeAcceptanceChecklist,
    buildVnEssentialsAudit,
    getRuntimeCapabilityStatusDigest,
    buildRuntimeCapabilityMarkdown,
    buildRuntimeCapabilityCsv,
    getRuntimeStatusLabel,
    getRuntimeAcceptanceTargetLabel,
    getVnEssentialStatusLabel,
  });
})(typeof window !== "undefined" ? window : globalThis);
