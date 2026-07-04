(function attachPresentationTimelineTools(global) {
  const storyBlockCatalogTools = global.CanvasiaEditorStoryBlockCatalog || {};

  const FALLBACK_BLOCK_LABELS = Object.freeze({
    background: "背景",
    dialogue: "台词",
    narration: "旁白",
    character_show: "角色登场",
    character_hide: "角色退场",
    music_play: "播放 BGM",
    music_stop: "停止 BGM",
    sfx_play: "音效",
    video_play: "视频",
    credits_roll: "片尾字幕",
    wait: "等待停顿",
    particle_effect: "粒子",
    screen_shake: "震动",
    screen_flash: "闪屏",
    screen_fade: "淡入淡出",
    camera_zoom: "镜头缩放",
    camera_pan: "镜头平移",
    screen_filter: "滤镜",
    depth_blur: "景深",
    choice: "选项",
    condition: "条件",
    jump: "跳转",
  });

  const BLOCK_LABELS = Object.freeze({
    ...FALLBACK_BLOCK_LABELS,
    ...(storyBlockCatalogTools.BLOCK_COMPACT_LABELS ?? {}),
  });

  const TEXT_SPEED_CHARS_PER_SECOND = Object.freeze({
    slow: 12,
    normal: 18,
    fast: 28,
    instant: 80,
  });

  const STORY_TEXT_TYPES = new Set(
    typeof storyBlockCatalogTools.getTimelineTextBlockTypes === "function"
      ? storyBlockCatalogTools.getTimelineTextBlockTypes()
      : ["dialogue", "narration", "choice"]
  );
  const VISUAL_BEAT_TYPES = new Set(
    typeof storyBlockCatalogTools.getTimelineVisualBeatBlockTypes === "function"
      ? storyBlockCatalogTools.getTimelineVisualBeatBlockTypes()
      : [
          "background",
          "character_show",
          "character_hide",
          "particle_effect",
          "wait",
          "screen_shake",
          "screen_flash",
          "screen_fade",
          "camera_zoom",
          "camera_pan",
          "screen_filter",
          "depth_blur",
          "video_play",
          "credits_roll",
        ]
  );
  const AUDIO_BEAT_TYPES = new Set(
    typeof storyBlockCatalogTools.getTimelineAudioBeatBlockTypes === "function"
      ? storyBlockCatalogTools.getTimelineAudioBeatBlockTypes()
      : ["music_play", "music_stop", "sfx_play", "video_play"]
  );
  const TIMELINE_TYPES = new Set([...STORY_TEXT_TYPES, ...VISUAL_BEAT_TYPES, ...AUDIO_BEAT_TYPES, "condition", "jump"]);

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function clampNumber(value, minimum, maximum, fallback = minimum) {
    const number = Number(value);
    if (!Number.isFinite(number)) {
      return fallback;
    }
    return Math.min(Math.max(number, minimum), maximum);
  }

  function getBlockLabel(type) {
    return BLOCK_LABELS[type] ?? cleanText(type, "卡片");
  }

  function getChapterMap(data = {}) {
    return new Map(
      toArray(data.chapters).map((chapter, index) => [
        String(chapter?.id ?? ""),
        {
          id: String(chapter?.id ?? ""),
          name: cleanText(chapter?.name ?? chapter?.title, `章节 ${index + 1}`),
          order: index,
        },
      ])
    );
  }

  function getOrderedScenes(data = {}) {
    const chapterOrder = new Map(toArray(data.chapters).map((chapter, index) => [String(chapter?.id ?? ""), index]));
    return toArray(data.scenes)
      .map((scene, index) => ({ scene, index }))
      .sort((left, right) => {
        const leftChapterOrder = chapterOrder.get(String(left.scene?.chapterId ?? "")) ?? 9999;
        const rightChapterOrder = chapterOrder.get(String(right.scene?.chapterId ?? "")) ?? 9999;
        if (leftChapterOrder !== rightChapterOrder) {
          return leftChapterOrder - rightChapterOrder;
        }
        return left.index - right.index;
      })
      .map((item) => item.scene);
  }

  function getAssetList(data = {}) {
    if (Array.isArray(data.assetList)) {
      return data.assetList;
    }
    if (Array.isArray(data.assets)) {
      return data.assets;
    }
    if (data.assetsById instanceof Map) {
      return Array.from(data.assetsById.values());
    }
    if (data.assetsById && typeof data.assetsById === "object") {
      return Object.values(data.assetsById);
    }
    return [];
  }

  function buildAssetMap(data = {}) {
    const assetMap = new Map();
    getAssetList(data).forEach((asset) => {
      if (asset?.id) {
        assetMap.set(String(asset.id), asset);
      }
    });
    if (data.assetsById instanceof Map) {
      data.assetsById.forEach((asset, id) => {
        if (id) {
          assetMap.set(String(id), asset);
        }
      });
    } else if (data.assetsById && typeof data.assetsById === "object") {
      Object.entries(data.assetsById).forEach(([id, asset]) => {
        if (id) {
          assetMap.set(String(id), asset);
        }
      });
    }
    return assetMap;
  }

  function getCharacterMap(data = {}) {
    const characterMap = new Map();
    toArray(data.characters).forEach((character) => {
      if (character?.id) {
        characterMap.set(String(character.id), character);
      }
    });
    if (data.charactersById instanceof Map) {
      data.charactersById.forEach((character, id) => {
        if (id) {
          characterMap.set(String(id), character);
        }
      });
    }
    return characterMap;
  }

  function getCharacterName(characterMap, characterId = "") {
    const id = cleanText(characterId);
    const character = characterMap.get(id);
    return cleanText(character?.displayName ?? character?.name, id || "未选择角色");
  }

  function getBlockText(block = {}) {
    if (block.type === "choice") {
      return toArray(block.options)
        .map((option) => cleanText(option?.text))
        .filter(Boolean)
        .join(" / ");
    }
    if (block.type === "credits_roll") {
      return toArray(block.lines).map(cleanText).filter(Boolean).join(" / ");
    }
    return cleanText(block.text ?? block.title ?? block.name ?? block.assetId ?? block.characterId ?? block.speakerId);
  }

  function summarizeBlock(block = {}, index = 0) {
    const label = getBlockLabel(block.type);
    const text = getBlockText(block);
    return text ? `第 ${index + 1} 张 · ${label} · ${text.slice(0, 32)}` : `第 ${index + 1} 张 · ${label}`;
  }

  function estimateTextDurationMs(block = {}) {
    const text = getBlockText(block);
    if (!text) {
      return 0;
    }
    const chars = Array.from(text).length;
    const speed = Object.hasOwn(TEXT_SPEED_CHARS_PER_SECOND, block.textSpeed) ? block.textSpeed : "normal";
    const punctuationPauseMs = (text.match(/[，。！？、,.!?]/g) ?? []).length * 90;
    const baseMs = (chars / TEXT_SPEED_CHARS_PER_SECOND[speed]) * 1000 + punctuationPauseMs;
    return Math.round(clampNumber(baseMs, 650, 22000, 1200));
  }

  function getTransitionDurationMs(block = {}) {
    return Math.round(clampNumber(block.transitionDurationMs, 0, 8000, 600));
  }

  function getEffectDurationMs(block = {}) {
    const duration = cleanText(block.duration, "medium");
    if (duration === "short") {
      return 420;
    }
    if (duration === "long") {
      return 1400;
    }
    return 820;
  }

  function getEventDurationMs(block = {}) {
    if (STORY_TEXT_TYPES.has(block.type)) {
      return estimateTextDurationMs(block);
    }
    if (["background", "character_show", "character_hide"].includes(block.type)) {
      return getTransitionDurationMs(block);
    }
    if (["screen_shake", "screen_flash", "screen_fade", "camera_zoom", "camera_pan", "screen_filter", "depth_blur"].includes(block.type)) {
      return getEffectDurationMs(block);
    }
    if (block.type === "credits_roll") {
      return Math.round(clampNumber(block.durationSeconds, 4, 180, 18) * 1000);
    }
    if (block.type === "wait") {
      return Math.round(clampNumber(block.durationSeconds, 0.1, 30, 1) * 1000);
    }
    if (block.type === "video_play") {
      return Math.round(clampNumber(block.durationSeconds, 1, 600, 12) * 1000);
    }
    return 0;
  }

  function pushIssue(issues, severity, code, title, detail, context = {}) {
    issues.push({ severity, code, title, detail, ...context });
  }

  function getIssueWeight(issue = {}) {
    if (issue.severity === "blocker") {
      return 100;
    }
    if (issue.severity === "warn") {
      return 60;
    }
    return 20;
  }

  function getStatusFromIssues(issues = []) {
    if (issues.some((issue) => issue.severity === "blocker")) {
      return "blocker";
    }
    if (issues.some((issue) => issue.severity === "warn")) {
      return "warn";
    }
    if (issues.length) {
      return "tip";
    }
    return "good";
  }

  function getStatusLabel(status) {
    if (status === "blocker") {
      return "先修";
    }
    if (status === "warn") {
      return "复查";
    }
    if (status === "tip") {
      return "润色";
    }
    return "正常";
  }

  function getAssetStatus(assetId, assetMap) {
    const id = cleanText(assetId);
    if (!id) {
      return { label: "未选择素材", ready: false, name: "" };
    }
    const asset = assetMap.get(id);
    if (!asset) {
      return { label: "素材不存在", ready: false, name: id };
    }
    if (asset.fileExists === false) {
      return { label: "文件缺失", ready: false, name: cleanText(asset.name ?? asset.fileName, id) };
    }
    return { label: "素材可用", ready: true, name: cleanText(asset.name ?? asset.fileName, id) };
  }

  function inspectBlock(block = {}, context = {}) {
    const issues = [];
    const baseContext = {
      chapterName: context.chapterName,
      sceneName: context.sceneName,
      sceneId: context.sceneId,
      blockId: cleanText(block.id),
      blockIndex: context.blockIndex,
      blockLabel: summarizeBlock(block, context.blockIndex),
    };
    const type = cleanText(block.type, "unknown");
    const typeLabel = getBlockLabel(type);
    const durationMs = getEventDurationMs(block);
    let detail = getBlockText(block);

    if (type === "background") {
      const asset = getAssetStatus(block.assetId, context.assetMap);
      detail = asset.name || asset.label;
      if (!cleanText(block.assetId)) {
        pushIssue(issues, "blocker", "background_missing_asset", "背景卡未选择素材", "这张背景卡没有绑定背景素材。", baseContext);
      } else if (!asset.ready) {
        pushIssue(issues, "blocker", "background_asset_not_ready", "背景素材不可用", asset.label, baseContext);
      }
      if (cleanText(block.transition, "fade") === "none") {
        pushIssue(issues, "tip", "background_hard_cut", "背景是硬切", "如果不是故意制造突兀感，建议给背景切换加淡入淡出。", baseContext);
      }
    }

    if (type === "music_play") {
      const asset = getAssetStatus(block.assetId, context.assetMap);
      detail = asset.name || asset.label;
      const fadeInMs = Math.round(clampNumber(block.fadeInMs, 0, 30000, 0));
      if (!cleanText(block.assetId)) {
        pushIssue(issues, "blocker", "music_missing_asset", "BGM 卡未选择素材", "这张播放音乐卡没有绑定 BGM。", baseContext);
      } else if (!asset.ready) {
        pushIssue(issues, "blocker", "music_asset_not_ready", "BGM 素材不可用", asset.label, baseContext);
      }
      if (fadeInMs < 250) {
        pushIssue(issues, context.musicActive ? "warn" : "tip", "music_hard_start", "BGM 进入过快", "建议设置 500-1500ms 淡入，让音乐更自然接入文本。", baseContext);
      }
    }

    if (type === "music_stop") {
      const fadeOutMs = Math.round(clampNumber(block.fadeOutMs, 0, 30000, 0));
      detail = `${fadeOutMs}ms 淡出`;
      if (fadeOutMs < 250) {
        pushIssue(issues, "tip", "music_hard_stop", "BGM 停止过硬", "建议给停止音乐卡设置淡出，避免像播放器突然切断。", baseContext);
      }
    }

    if (type === "sfx_play") {
      const asset = getAssetStatus(block.assetId, context.assetMap);
      detail = asset.name || asset.label;
      if (!cleanText(block.assetId)) {
        pushIssue(issues, "blocker", "sfx_missing_asset", "音效卡未选择素材", "这张音效卡没有绑定音效素材。", baseContext);
      } else if (!asset.ready) {
        pushIssue(issues, "blocker", "sfx_asset_not_ready", "音效素材不可用", asset.label, baseContext);
      }
    }

    if (type === "video_play") {
      const asset = getAssetStatus(block.assetId, context.assetMap);
      detail = asset.name || cleanText(block.title, asset.label);
      if (!cleanText(block.assetId) && !cleanText(block.title)) {
        pushIssue(issues, "warn", "video_missing_identity", "视频卡缺少素材或标题", "OP / ED 视频建议至少绑定素材或写清标题，便于导出前复核。", baseContext);
      } else if (cleanText(block.assetId) && !asset.ready) {
        pushIssue(issues, "blocker", "video_asset_not_ready", "视频素材不可用", asset.label, baseContext);
      }
    }

    if (type === "character_show") {
      detail = getCharacterName(context.characterMap, block.characterId);
      const stage = block.stage ?? block.characterStage ?? {};
      const scale = Math.round(clampNumber(stage.scale, 45, 220, 100));
      const opacity = Math.round(clampNumber(stage.opacity, 0, 100, 100));
      if (!cleanText(block.characterId)) {
        pushIssue(issues, "blocker", "character_show_missing_character", "角色登场卡未选择角色", "这张卡没有绑定角色。", baseContext);
      }
      if (cleanText(block.transition, "fade") === "none") {
        pushIssue(issues, "tip", "character_show_hard_cut", "角色登场是硬切", "建议用淡入、滑入或弹出，让立绘出现更像正式演出。", baseContext);
      }
      if (scale <= 55 || scale >= 185) {
        pushIssue(issues, "tip", "character_scale_extreme", "立绘缩放较极端", `当前缩放约 ${scale}%，建议确认构图没有遮挡文本框或出画。`, baseContext);
      }
      if (opacity < 45) {
        pushIssue(issues, "warn", "character_opacity_too_low", "立绘透明度过低", `当前透明度约 ${opacity}%，玩家可能看不清角色。`, baseContext);
      }
    }

    if (type === "character_hide") {
      detail = getCharacterName(context.characterMap, block.characterId);
      if (!cleanText(block.characterId)) {
        pushIssue(issues, "blocker", "character_hide_missing_character", "角色退场卡未选择角色", "这张卡没有绑定要隐藏的角色。", baseContext);
      }
      if (cleanText(block.transition, "fade") === "none") {
        pushIssue(issues, "tip", "character_hide_hard_cut", "角色退场是硬切", "如果不是故意制造突兀感，建议给退场加淡出或滑出。", baseContext);
      }
    }

    if ((type === "dialogue" || type === "narration") && !cleanText(block.text)) {
      pushIssue(issues, "warn", "empty_text_block", "正文卡没有文本", "这张台词/旁白卡是空的，发布前建议补正文或删除。", baseContext);
    }

    if (type === "choice" && toArray(block.options).length === 0) {
      pushIssue(issues, "blocker", "choice_without_options", "选项卡没有选项", "玩家走到这里会没有可点内容。", baseContext);
    }

    if (type === "credits_roll" && !toArray(block.lines).some((line) => cleanText(line))) {
      pushIssue(issues, "warn", "credits_without_lines", "片尾字幕为空", "片尾卡已经存在，但还没有演职人员文本。", baseContext);
    }

    if (type === "wait" && clampNumber(block.durationSeconds, 0.1, 30, 1) >= 8) {
      pushIssue(issues, "warn", "long_wait_block", "等待停顿偏长", "超过 8 秒的停顿可能会让玩家误以为卡住，建议只在强演出时使用。", baseContext);
    }

    const status = getStatusFromIssues(issues);
    return {
      ...baseContext,
      type,
      typeLabel,
      detail,
      durationMs,
      status,
      statusLabel: getStatusLabel(status),
      issues,
    };
  }

  function inspectScene(scene = {}, context = {}) {
    const blocks = toArray(scene.blocks);
    const chapterName = context.chapter?.name ?? "未分章";
    const sceneName = cleanText(scene.name ?? scene.title, `场景 ${context.sceneIndex + 1}`);
    const sceneId = cleanText(scene.id);
    const events = [];
    const issues = [];
    let hasStoryContent = false;
    let hasVisualBeat = false;
    let hasAudioBeat = false;
    let hasBackground = false;
    let firstStoryContentIndex = -1;
    let firstBackgroundIndex = -1;
    let lastVisualBeatIndex = -1;
    let textRunCount = 0;
    let staticTextWarned = false;
    let musicActive = false;

    blocks.forEach((block, blockIndex) => {
      const type = cleanText(block?.type);
      if (!TIMELINE_TYPES.has(type)) {
        return;
      }

      const event = inspectBlock(block, {
        ...context,
        chapterName,
        sceneName,
        sceneId,
        blockIndex,
        musicActive,
      });
      events.push(event);
      issues.push(...event.issues);

      if (STORY_TEXT_TYPES.has(type)) {
        hasStoryContent = true;
        textRunCount += 1;
        if (firstStoryContentIndex < 0) {
          firstStoryContentIndex = blockIndex;
        }
        if (!staticTextWarned && textRunCount >= 7 && blockIndex - lastVisualBeatIndex >= 7) {
          pushIssue(
            issues,
            "warn",
            "long_static_text_run",
            "长对白段缺少演出变化",
            "连续多张正文/选项之间没有背景、立绘、镜头、滤镜或粒子变化，建议补一个表情、镜头或环境变化。",
            {
              chapterName,
              sceneName,
              sceneId,
              blockId: cleanText(block.id),
              blockIndex,
              blockLabel: summarizeBlock(block, blockIndex),
            }
          );
          staticTextWarned = true;
        }
      } else if (VISUAL_BEAT_TYPES.has(type)) {
        hasVisualBeat = true;
        lastVisualBeatIndex = blockIndex;
        textRunCount = 0;
      }

      if (type === "background") {
        hasBackground = true;
        if (firstBackgroundIndex < 0) {
          firstBackgroundIndex = blockIndex;
        }
      }
      if (AUDIO_BEAT_TYPES.has(type)) {
        hasAudioBeat = true;
      }
      if (type === "music_play") {
        musicActive = true;
      }
      if (type === "music_stop") {
        musicActive = false;
      }
    });

    if (hasStoryContent && (!hasBackground || (firstBackgroundIndex >= 0 && firstStoryContentIndex >= 0 && firstStoryContentIndex < firstBackgroundIndex))) {
      pushIssue(issues, "warn", "scene_opening_without_background", "场景开头缺少明确背景", "建议让内容出现前先切背景，避免玩家不知道当前地点。", {
        chapterName,
        sceneName,
        sceneId,
        blockId: "",
        blockIndex: -1,
        blockLabel: sceneName,
      });
    }

    if (hasStoryContent && !hasAudioBeat) {
      pushIssue(issues, "tip", "scene_without_audio_anchor", "内容场景没有音频锚点", "不一定必须有 BGM，但发布前建议确认这一段是故意留白，而不是忘了配乐或音效。", {
        chapterName,
        sceneName,
        sceneId,
        blockId: "",
        blockIndex: -1,
        blockLabel: sceneName,
      });
    }

    if (hasStoryContent && !hasVisualBeat) {
      pushIssue(issues, "warn", "scene_without_visual_anchor", "内容场景缺少视觉锚点", "整场只有文本或逻辑卡，建议至少补背景、立绘或一个镜头变化。", {
        chapterName,
        sceneName,
        sceneId,
        blockId: "",
        blockIndex: -1,
        blockLabel: sceneName,
      });
    }

    const estimatedDurationMs = events.reduce((total, event) => total + Math.max(0, Number(event.durationMs) || 0), 0);
    const status = getStatusFromIssues(issues);

    return {
      sceneId,
      sceneName,
      chapterName,
      eventCount: events.length,
      estimatedDurationMs,
      estimatedDurationLabel: formatDuration(estimatedDurationMs),
      hasStoryContent,
      hasVisualBeat,
      hasAudioBeat,
      status,
      statusLabel: getStatusLabel(status),
      issues,
      events,
    };
  }

  function formatDuration(ms) {
    const safeMs = Math.max(0, Number(ms) || 0);
    if (safeMs < 1000) {
      return "不到 1 秒";
    }
    const seconds = Math.round(safeMs / 1000);
    if (seconds < 60) {
      return `${seconds} 秒`;
    }
    const minutes = Math.floor(seconds / 60);
    const restSeconds = seconds % 60;
    return restSeconds ? `${minutes} 分 ${restSeconds} 秒` : `${minutes} 分`;
  }

  function buildPresentationTimeline(data = {}) {
    const assetMap = buildAssetMap(data);
    const characterMap = getCharacterMap(data);
    const chapterMap = getChapterMap(data);
    const sceneReports = getOrderedScenes(data).map((scene, sceneIndex) =>
      inspectScene(scene, {
        sceneIndex,
        assetMap,
        characterMap,
        chapter: chapterMap.get(String(scene?.chapterId ?? "")) ?? { name: "未分章" },
      })
    );
    const events = sceneReports.flatMap((scene) => scene.events);
    const issues = sceneReports
      .flatMap((scene) => scene.issues)
      .sort((left, right) => getIssueWeight(right) - getIssueWeight(left) || left.sceneName.localeCompare(right.sceneName, "zh-CN"));
    const estimatedDurationMs = sceneReports.reduce((total, scene) => total + scene.estimatedDurationMs, 0);
    const summary = {
      sceneCount: sceneReports.length,
      eventCount: events.length,
      storySceneCount: sceneReports.filter((scene) => scene.hasStoryContent).length,
      estimatedDurationMs,
      estimatedDurationLabel: formatDuration(estimatedDurationMs),
      longStaticTextRunCount: issues.filter((issue) => issue.code === "long_static_text_run").length,
      abruptAudioCount: issues.filter((issue) => ["music_hard_start", "music_hard_stop"].includes(issue.code)).length,
      missingVisualAnchorCount: issues.filter((issue) => issue.code === "scene_without_visual_anchor").length,
      missingAudioAnchorCount: issues.filter((issue) => issue.code === "scene_without_audio_anchor").length,
      blockerCount: issues.filter((issue) => issue.severity === "blocker").length,
      warningCount: issues.filter((issue) => issue.severity === "warn").length,
      tipCount: issues.filter((issue) => issue.severity === "tip").length,
    };

    return {
      projectTitle: cleanText(data.project?.title, "Canvasia Project"),
      sceneReports,
      events,
      issues,
      summary,
    };
  }

  function getPresentationTimelineStatusDigest(timeline = {}) {
    const summary = timeline.summary ?? {};
    if ((summary.eventCount ?? 0) === 0) {
      return {
        status: "empty",
        tone: "soft",
        title: "还没有可分析的演出时间轴",
        detail: "项目里暂时没有正文、背景、角色、音乐、视频或演出卡。",
      };
    }
    if ((summary.blockerCount ?? 0) > 0) {
      return {
        status: "blocked",
        tone: "danger",
        title: `有 ${summary.blockerCount} 个演出阻塞问题`,
        detail: "优先修复缺素材、空选项、空角色或不可用媒体，再做节奏润色。",
      };
    }
    if ((summary.warningCount ?? 0) > 0) {
      return {
        status: "warn",
        tone: "warn",
        title: `有 ${summary.warningCount} 个演出节奏提醒`,
        detail: "项目可以继续推进，但建议复查开场背景、长静态对白、硬切音乐和视觉锚点。",
      };
    }
    return {
      status: "ready",
      tone: "good",
      title: "演出时间轴看起来比较稳",
      detail: "当前正文、视觉和音频锚点没有明显发布前结构问题。",
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

  function formatCsvCell(value) {
    const text = String(value ?? "");
    return `"${text.replaceAll('"', '""')}"`;
  }

  function buildCsv(headers = [], rows = []) {
    return [
      toArray(headers).map(formatCsvCell).join(","),
      ...toArray(rows).map((row) => toArray(row).map(formatCsvCell).join(",")),
    ].join("\n");
  }

  function buildPresentationTimelineMarkdown(timeline = {}, context = {}) {
    const digest = getPresentationTimelineStatusDigest(timeline);
    const summary = timeline.summary ?? {};
    const projectTitle = context.projectTitle || timeline.projectTitle || "Canvasia Project";
    const generatedAt = context.generatedAt || new Date().toISOString();
    const sceneRows = toArray(timeline.sceneReports).slice(0, 120).map((scene, index) => [
      `${index + 1}`,
      scene.chapterName,
      scene.sceneName,
      `${scene.eventCount}`,
      scene.estimatedDurationLabel,
      scene.statusLabel,
    ]);
    const eventRows = toArray(timeline.events).slice(0, 160).map((event, index) => [
      `${index + 1}`,
      event.chapterName,
      event.sceneName,
      event.blockIndex + 1,
      event.typeLabel,
      event.detail,
      formatDuration(event.durationMs),
      event.statusLabel,
    ]);
    const issueRows = toArray(timeline.issues).slice(0, 140).map((issue, index) => [
      `${index + 1}`,
      issue.severity === "blocker" ? "阻塞" : issue.severity === "warn" ? "提醒" : "润色",
      issue.chapterName,
      issue.sceneName,
      issue.title,
      issue.detail,
    ]);

    return `\uFEFF${[
      `# ${projectTitle} 演出时间轴`,
      "",
      `导出时间：${generatedAt}`,
      `状态：${digest.title}`,
      `说明：${digest.detail}`,
      "",
      "## 总览",
      "",
      buildMarkdownTable(
        ["项目", "数量"],
        [
          ["场景", `${summary.sceneCount ?? 0}`],
          ["内容场景", `${summary.storySceneCount ?? 0}`],
          ["演出事件", `${summary.eventCount ?? 0}`],
          ["预计阅读/演出时长", summary.estimatedDurationLabel ?? "0 秒"],
          ["阻塞问题", `${summary.blockerCount ?? 0}`],
          ["复查提醒", `${summary.warningCount ?? 0}`],
          ["润色建议", `${summary.tipCount ?? 0}`],
        ]
      ),
      "",
      "## 场景节奏",
      "",
      buildMarkdownTable(["序号", "章节", "场景", "事件", "预计时长", "状态"], sceneRows) || "当前没有可列出的场景。",
      "",
      "## 演出事件",
      "",
      buildMarkdownTable(["序号", "章节", "场景", "卡片", "类型", "内容", "预计时长", "状态"], eventRows) ||
        "当前没有可列出的演出事件。",
      "",
      "## 需要复查的问题",
      "",
      buildMarkdownTable(["序号", "级别", "章节", "场景", "问题", "说明"], issueRows) || "当前没有明显演出节奏问题。",
      "",
    ].join("\n")}`;
  }

  function buildPresentationTimelineCsv(timeline = {}) {
    const rows = toArray(timeline.events).map((event, index) => [
      `${index + 1}`,
      event.chapterName,
      event.sceneName,
      event.blockIndex + 1,
      event.typeLabel,
      event.detail,
      event.durationMs,
      formatDuration(event.durationMs),
      event.statusLabel,
      toArray(event.issues).map((issue) => issue.title).join(" / "),
    ]);
    return `\uFEFF${buildCsv(
      ["序号", "章节", "场景", "卡片", "类型", "内容", "预计毫秒", "预计时长", "状态", "问题"],
      rows
    )}\n`;
  }

  global.CanvasiaEditorPresentationTimeline = Object.freeze({
    buildPresentationTimeline,
    getPresentationTimelineStatusDigest,
    buildPresentationTimelineMarkdown,
    buildPresentationTimelineCsv,
    estimateTextDurationMs,
    formatDuration,
  });
})(typeof window !== "undefined" ? window : globalThis);
