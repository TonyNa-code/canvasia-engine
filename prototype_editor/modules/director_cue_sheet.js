(function attachDirectorCueSheetTools(global) {
  const CUE_GROUP_LABELS = Object.freeze({
    story: "剧情",
    visual: "画面",
    audio: "声音",
    effect: "演出",
    route: "路线",
    pacing: "节奏",
    system: "系统",
  });

  const BLOCK_LABELS = Object.freeze({
    background: "背景",
    dialogue: "台词",
    narration: "旁白",
    choice: "选项",
    condition: "条件分支",
    jump: "跳转",
    character_show: "角色登场",
    character_hide: "角色退场",
    music_play: "播放 BGM",
    music_stop: "停止 BGM",
    sfx_play: "音效",
    video_play: "视频",
    particle_effect: "粒子",
    wait: "等待",
    screen_shake: "震动",
    screen_flash: "闪屏",
    screen_fade: "淡入淡出",
    camera_zoom: "镜头缩放",
    camera_pan: "镜头平移",
    screen_filter: "滤镜",
    depth_blur: "景深",
    credits_roll: "片尾字幕",
    variable_set: "设置变量",
    variable_add: "调整变量",
  });

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function truncateText(value, maxLength = 72) {
    const text = cleanText(value);
    if (text.length <= maxLength) {
      return text;
    }
    return `${text.slice(0, Math.max(0, maxLength - 1))}…`;
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
        : Array.isArray(data.assets)
          ? data.assets
          : [];
  }

  function getCharacterList(data = {}) {
    return Array.isArray(data.characters)
      ? data.characters
      : Array.isArray(data.characters?.characters)
        ? data.characters.characters
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

  function buildCharacterMap(data = {}) {
    const characterMap = new Map();
    getCharacterList(data).forEach((character) => {
      if (character?.id) {
        characterMap.set(String(character.id), character);
      }
    });
    buildCollectionMap(data.charactersById).forEach((character, id) => characterMap.set(id, character));
    return characterMap;
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

  function getSceneRecords(data = {}) {
    const sceneMap = buildSceneMap(data);
    const records = [];
    const seenSceneIds = new Set();

    toArray(data.chapters).forEach((chapter, chapterIndex) => {
      const chapterId = cleanText(chapter?.id ?? chapter?.chapterId, `chapter_${chapterIndex + 1}`);
      const chapterName = cleanText(chapter?.name ?? chapter?.title, `章节 ${chapterIndex + 1}`);
      const directScenes = toArray(chapter?.scenes);
      const orderedIds = toArray(chapter?.sceneOrder).map((sceneId) => cleanText(sceneId)).filter(Boolean);
      const scenes = directScenes.length
        ? directScenes
        : orderedIds.map((sceneId) => sceneMap.get(sceneId)).filter(Boolean);

      scenes.forEach((scene, sceneIndex) => {
        const sceneId = cleanText(scene?.id);
        if (!sceneId || seenSceneIds.has(sceneId)) {
          return;
        }
        seenSceneIds.add(sceneId);
        records.push({ scene, sceneIndex, chapterId, chapterName, chapterOrder: chapterIndex });
      });
    });

    toArray(data.scenes).forEach((scene, sceneIndex) => {
      const sceneId = cleanText(scene?.id);
      if (!sceneId || seenSceneIds.has(sceneId)) {
        return;
      }
      seenSceneIds.add(sceneId);
      records.push({
        scene,
        sceneIndex,
        chapterId: cleanText(scene.chapterId),
        chapterName: "未分章",
        chapterOrder: 9999,
      });
    });

    return records.sort((left, right) => {
      if (left.chapterOrder !== right.chapterOrder) {
        return left.chapterOrder - right.chapterOrder;
      }
      return left.sceneIndex - right.sceneIndex;
    });
  }

  function getBlockLabel(type) {
    return BLOCK_LABELS[type] ?? cleanText(type, "卡片");
  }

  function getAssetName(assetMap, assetId, fallback = "") {
    const cleanId = cleanText(assetId);
    if (!cleanId) {
      return fallback;
    }
    const asset = assetMap.get(cleanId);
    return cleanText(asset?.name ?? asset?.fileName ?? asset?.path, cleanId);
  }

  function getCharacterName(characterMap, characterId, fallback = "") {
    const cleanId = cleanText(characterId);
    if (!cleanId) {
      return fallback;
    }
    const character = characterMap.get(cleanId);
    return cleanText(character?.displayName ?? character?.name, cleanId);
  }

  function getSceneTargetLabel(sceneMap, targetSceneId) {
    const cleanId = cleanText(targetSceneId);
    if (!cleanId) {
      return "继续下一张卡";
    }
    const scene = sceneMap.get(cleanId);
    return cleanText(scene?.name, cleanId);
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

  function pushIssue(sheetIssues, sceneCue, severity, code, title, detail, context = {}) {
    const issue = {
      severity,
      code,
      title,
      detail,
      chapterName: sceneCue.chapterName,
      sceneName: sceneCue.sceneName,
      sceneId: sceneCue.sceneId,
      ...context,
    };
    sceneCue.issues.push(issue);
    sheetIssues.push(issue);
  }

  function addRequiredAsset(sceneCue, sheetIssues, assetMap, assetId, roleLabel, context = {}) {
    const cleanId = cleanText(assetId);
    if (!cleanId) {
      return "";
    }
    const asset = assetMap.get(cleanId);
    const assetName = cleanText(asset?.name ?? asset?.fileName ?? asset?.path, cleanId);
    if (!sceneCue.requiredAssets.some((item) => item.assetId === cleanId && item.roleLabel === roleLabel)) {
      sceneCue.requiredAssets.push({
        assetId: cleanId,
        assetName,
        roleLabel,
        fileExists: asset ? asset.fileExists !== false : false,
      });
    }
    if (!asset) {
      pushIssue(
        sheetIssues,
        sceneCue,
        "blocker",
        "director_asset_unknown",
        `${roleLabel}素材不存在`,
        `剧情卡引用了「${cleanId}」，但素材库里找不到这个条目。`,
        { assetId: cleanId, assetName, ...context }
      );
    } else if (asset.fileExists === false) {
      pushIssue(
        sheetIssues,
        sceneCue,
        "blocker",
        "director_asset_missing_file",
        `${roleLabel}文件缺失`,
        `素材「${assetName}」已经被场景使用，但真实文件还没有导入。`,
        { assetId: cleanId, assetName, ...context }
      );
    }
    return assetName;
  }

  function addCue(sceneCue, group, block, blockIndex, text, context = {}) {
    const cue = {
      order: sceneCue.cues.length + 1,
      blockIndex,
      blockId: cleanText(block?.id, `block_${blockIndex + 1}`),
      blockType: cleanText(block?.type, "unknown"),
      blockLabel: getBlockLabel(block?.type),
      group,
      groupLabel: CUE_GROUP_LABELS[group] ?? cleanText(group, "制作"),
      text: truncateText(text, 120),
      assetNames: toArray(context.assetNames).filter(Boolean),
      characterName: cleanText(context.characterName),
      targetLabel: cleanText(context.targetLabel),
    };
    sceneCue.cues.push(cue);
    sceneCue.groupCounts[group] = (sceneCue.groupCounts[group] ?? 0) + 1;
    return cue;
  }

  function formatChoiceText(block = {}, sceneMap = new Map()) {
    const options = toArray(block.options);
    if (!options.length) {
      return "选项未配置";
    }
    return options
      .map((option, index) => {
        const label = cleanText(option?.text ?? option?.label, `选项 ${index + 1}`);
        const target = getSceneTargetLabel(sceneMap, option?.targetSceneId ?? option?.target);
        return `${index + 1}. ${label} -> ${target}`;
      })
      .join(" / ");
  }

  function formatConditionText(block = {}, sceneMap = new Map()) {
    const branches = toArray(block.branches);
    if (!branches.length) {
      return "条件分支未配置";
    }
    return branches
      .map((branch, index) => {
        const label = cleanText(branch?.condition ?? branch?.label, index === 0 ? "如果" : "否则");
        return `${label} -> ${getSceneTargetLabel(sceneMap, branch?.targetSceneId ?? branch?.target)}`;
      })
      .join(" / ");
  }

  function collectDialogueSpeaker(sceneCue, speakerId) {
    const cleanId = cleanText(speakerId);
    if (cleanId) {
      sceneCue.dialogueSpeakerIds.add(cleanId);
    }
  }

  function buildCueForBlock(sceneCue, sheetIssues, block = {}, blockIndex = 0, context = {}) {
    const type = cleanText(block.type, "unknown");
    const assetMap = context.assetMap ?? new Map();
    const characterMap = context.characterMap ?? new Map();
    const sceneMap = context.sceneMap ?? new Map();

    if (type === "dialogue") {
      const speakerId = cleanText(block.speakerId);
      const speakerName = getCharacterName(characterMap, speakerId, "未指定说话人");
      collectDialogueSpeaker(sceneCue, speakerId);
      if (!speakerId || !characterMap.has(speakerId)) {
        pushIssue(sheetIssues, sceneCue, "warn", "director_dialogue_unknown_speaker", "台词说话人待确认", "这句台词没有匹配到角色库里的角色。", {
          blockIndex,
          speakerId,
        });
      }
      const voiceName = addRequiredAsset(sceneCue, sheetIssues, assetMap, block.voiceAssetId ?? block.voice?.assetId, "语音", { blockIndex });
      if (!voiceName) {
        pushIssue(sheetIssues, sceneCue, "tip", "director_dialogue_missing_voice", "台词待配音", `「${speakerName}」这句台词还没有绑定语音。`, {
          blockIndex,
          speakerId,
        });
      }
      addCue(sceneCue, "story", block, blockIndex, `${speakerName}：${cleanText(block.text, "（空台词）")}`, {
        characterName: speakerName,
        assetNames: voiceName ? [voiceName] : [],
      });
      return;
    }

    if (type === "narration") {
      addCue(sceneCue, "story", block, blockIndex, `旁白：${cleanText(block.text, "（空旁白）")}`);
      return;
    }

    if (type === "choice") {
      sceneCue.hasRouteCue = true;
      addCue(sceneCue, "route", block, blockIndex, formatChoiceText(block, sceneMap));
      if (!toArray(block.options).length) {
        pushIssue(sheetIssues, sceneCue, "warn", "director_choice_empty", "选项没有内容", "这个选项卡还没有可供玩家选择的分支。", { blockIndex });
      }
      return;
    }

    if (type === "condition") {
      sceneCue.hasRouteCue = true;
      addCue(sceneCue, "route", block, blockIndex, formatConditionText(block, sceneMap));
      if (!toArray(block.branches).length) {
        pushIssue(sheetIssues, sceneCue, "warn", "director_condition_empty", "条件分支为空", "这个条件卡还没有配置任何判断结果。", { blockIndex });
      }
      return;
    }

    if (type === "jump") {
      sceneCue.hasRouteCue = true;
      const targetLabel = getSceneTargetLabel(sceneMap, block.targetSceneId ?? block.target);
      addCue(sceneCue, "route", block, blockIndex, `跳转到：${targetLabel}`, { targetLabel });
      return;
    }

    if (type === "background") {
      sceneCue.hasBackground = true;
      const assetName = addRequiredAsset(sceneCue, sheetIssues, assetMap, block.assetId, "背景", { blockIndex });
      addCue(sceneCue, "visual", block, blockIndex, `切换背景：${assetName || "未选择背景"}${block.transition ? ` / ${block.transition}` : ""}`, {
        assetNames: assetName ? [assetName] : [],
      });
      if (!block.assetId) {
        pushIssue(sheetIssues, sceneCue, "warn", "director_background_unset", "背景未选择", "背景卡已经加入场景，但还没有绑定背景素材。", {
          blockIndex,
        });
      }
      return;
    }

    if (type === "character_show") {
      const characterId = cleanText(block.characterId);
      const characterName = getCharacterName(characterMap, characterId, "未选择角色");
      if (characterId) {
        sceneCue.visibleCharacterIds.add(characterId);
        sceneCue.stagedCharacterIds.add(characterId);
      } else {
        pushIssue(sheetIssues, sceneCue, "warn", "director_character_show_unset", "角色登场未选择角色", "角色登场卡还没有绑定角色。", { blockIndex });
      }
      addCue(
        sceneCue,
        "visual",
        block,
        blockIndex,
        `显示立绘：${characterName}${block.expressionId ? ` / 表情 ${block.expressionId}` : ""}${block.position ? ` / ${block.position}` : ""}`,
        { characterName }
      );
      return;
    }

    if (type === "character_hide") {
      const characterId = cleanText(block.characterId);
      const characterName = getCharacterName(characterMap, characterId, "未选择角色");
      if (characterId) {
        sceneCue.visibleCharacterIds.delete(characterId);
      }
      addCue(sceneCue, "visual", block, blockIndex, `隐藏立绘：${characterName}`, { characterName });
      return;
    }

    if (type === "music_play") {
      sceneCue.hasMusicCue = true;
      const assetName = addRequiredAsset(sceneCue, sheetIssues, assetMap, block.assetId, "BGM", { blockIndex });
      addCue(sceneCue, "audio", block, blockIndex, `播放 BGM：${assetName || "未选择音乐"}${block.fadeInMs ? ` / 淡入 ${block.fadeInMs}ms` : ""}`, {
        assetNames: assetName ? [assetName] : [],
      });
      return;
    }

    if (type === "music_stop") {
      sceneCue.hasMusicCue = true;
      addCue(sceneCue, "audio", block, blockIndex, `停止 BGM${block.fadeOutMs ? ` / 淡出 ${block.fadeOutMs}ms` : ""}`);
      return;
    }

    if (type === "sfx_play") {
      const assetName = addRequiredAsset(sceneCue, sheetIssues, assetMap, block.assetId, "音效", { blockIndex });
      addCue(sceneCue, "audio", block, blockIndex, `播放音效：${assetName || "未选择音效"}`, { assetNames: assetName ? [assetName] : [] });
      return;
    }

    if (type === "video_play") {
      const assetName = addRequiredAsset(sceneCue, sheetIssues, assetMap, block.assetId, "视频", { blockIndex });
      addCue(sceneCue, "visual", block, blockIndex, `播放视频：${assetName || "未选择视频"}`, { assetNames: assetName ? [assetName] : [] });
      return;
    }

    if (["particle_effect", "screen_shake", "screen_flash", "screen_fade", "camera_zoom", "camera_pan", "screen_filter", "depth_blur"].includes(type)) {
      sceneCue.hasEffectCue = true;
      addCue(sceneCue, "effect", block, blockIndex, `${getBlockLabel(type)}：${cleanText(block.preset ?? block.action ?? block.target ?? block.duration, "默认")}`);
      return;
    }

    if (type === "wait") {
      addCue(sceneCue, "pacing", block, blockIndex, `停顿：${cleanText(block.durationSeconds ?? block.durationMs, "未设置时长")}`);
      return;
    }

    if (type === "credits_roll") {
      addCue(sceneCue, "system", block, blockIndex, `片尾字幕：${toArray(block.lines).map(cleanText).filter(Boolean).join(" / ") || "未填写字幕"}`);
      return;
    }

    if (type === "variable_set" || type === "variable_add") {
      addCue(sceneCue, "route", block, blockIndex, `${getBlockLabel(type)}：${cleanText(block.variableId, "未选择变量")}`);
      return;
    }

    addCue(sceneCue, "system", block, blockIndex, `${getBlockLabel(type)}：${cleanText(block.text ?? block.note ?? block.assetId ?? block.characterId, "待补说明")}`);
  }

  function buildSceneCue(record, sheetIssues, context) {
    const scene = record.scene ?? {};
    const sceneCue = {
      sceneId: cleanText(scene.id),
      sceneName: cleanText(scene.name ?? scene.title, "未命名场景"),
      chapterId: cleanText(record.chapterId),
      chapterName: cleanText(record.chapterName, "未分章"),
      cues: [],
      issues: [],
      requiredAssets: [],
      groupCounts: {},
      visibleCharacterIds: new Set(),
      stagedCharacterIds: new Set(),
      dialogueSpeakerIds: new Set(),
      hasBackground: false,
      hasMusicCue: false,
      hasRouteCue: false,
      hasEffectCue: false,
    };

    toArray(scene.blocks).forEach((block, blockIndex) => buildCueForBlock(sceneCue, sheetIssues, block, blockIndex, context));
    finalizeSceneCue(sceneCue, sheetIssues);
    return serializeSceneCue(sceneCue);
  }

  function finalizeSceneCue(sceneCue, sheetIssues) {
    const storyCount = (sceneCue.groupCounts.story ?? 0) + (sceneCue.groupCounts.route ?? 0);
    const visualCount = sceneCue.groupCounts.visual ?? 0;
    const effectCount = sceneCue.groupCounts.effect ?? 0;

    if (!sceneCue.cues.length) {
      pushIssue(sheetIssues, sceneCue, "warn", "director_scene_empty", "空场景", "这个场景没有任何剧情卡，试玩时会直接空过去。");
    }
    if (storyCount > 0 && !sceneCue.hasBackground) {
      pushIssue(sheetIssues, sceneCue, "warn", "director_scene_missing_background", "场景缺少背景", "这个场景有正文或分支，但没有明确背景卡。");
    }
    if ((sceneCue.groupCounts.story ?? 0) >= 3 && visualCount <= 1 && effectCount === 0) {
      pushIssue(sheetIssues, sceneCue, "tip", "director_scene_too_static", "画面节奏偏静", "这一场正文较多但画面变化很少，可以考虑补立绘、镜头、粒子或转场。");
    }
    if ((sceneCue.groupCounts.story ?? 0) >= 2 && !sceneCue.hasMusicCue) {
      pushIssue(sheetIssues, sceneCue, "tip", "director_scene_no_audio_anchor", "缺少声音锚点", "这一场已有正文内容，可以考虑配置 BGM、环境音或关键音效。");
    }
    sceneCue.dialogueSpeakerIds.forEach((speakerId) => {
      if (!sceneCue.stagedCharacterIds.has(speakerId)) {
        pushIssue(sheetIssues, sceneCue, "tip", "director_speaker_not_staged", "说话人可能未登场", "该角色有台词，但本场没有检测到对应角色登场卡。", {
          speakerId,
        });
      }
    });
  }

  function getSceneReadiness(issues = [], cueCount = 0) {
    if (!cueCount) {
      return { status: "empty", label: "空场景", score: 0 };
    }
    const blockerCount = issues.filter((issue) => issue.severity === "blocker").length;
    const warnCount = issues.filter((issue) => issue.severity === "warn").length;
    const tipCount = issues.filter((issue) => issue.severity === "tip").length;
    const score = Math.max(0, 100 - blockerCount * 35 - warnCount * 18 - tipCount * 6);
    if (blockerCount > 0) {
      return { status: "blocked", label: "先修", score };
    }
    if (warnCount > 0) {
      return { status: "warn", label: "优先", score };
    }
    if (tipCount > 0) {
      return { status: "soft", label: "润色", score };
    }
    return { status: "ready", label: "可制作", score };
  }

  function serializeSceneCue(sceneCue) {
    const cueCount = sceneCue.cues.length;
    const readiness = getSceneReadiness(sceneCue.issues, cueCount);
    const groupCounts = { ...sceneCue.groupCounts };
    return {
      sceneId: sceneCue.sceneId,
      sceneName: sceneCue.sceneName,
      chapterId: sceneCue.chapterId,
      chapterName: sceneCue.chapterName,
      cues: sceneCue.cues,
      issues: sceneCue.issues,
      requiredAssets: sceneCue.requiredAssets,
      groupCounts,
      cueCount,
      requiredAssetCount: sceneCue.requiredAssets.length,
      missingAssetCount: sceneCue.requiredAssets.filter((asset) => !asset.fileExists).length,
      storyCueCount: groupCounts.story ?? 0,
      visualCueCount: groupCounts.visual ?? 0,
      audioCueCount: groupCounts.audio ?? 0,
      effectCueCount: groupCounts.effect ?? 0,
      routeCueCount: groupCounts.route ?? 0,
      readiness,
    };
  }

  function summarizeSheet(scenes = [], issues = []) {
    const blockerCount = issues.filter((issue) => issue.severity === "blocker").length;
    const warningCount = issues.filter((issue) => issue.severity === "warn").length;
    const tipCount = issues.filter((issue) => issue.severity === "tip").length;
    const totalScore = scenes.reduce((sum, scene) => sum + (scene.readiness?.score ?? 0), 0);
    return {
      sceneCount: scenes.length,
      cueCount: scenes.reduce((sum, scene) => sum + scene.cueCount, 0),
      storyCueCount: scenes.reduce((sum, scene) => sum + scene.storyCueCount, 0),
      visualCueCount: scenes.reduce((sum, scene) => sum + scene.visualCueCount, 0),
      audioCueCount: scenes.reduce((sum, scene) => sum + scene.audioCueCount, 0),
      effectCueCount: scenes.reduce((sum, scene) => sum + scene.effectCueCount, 0),
      routeCueCount: scenes.reduce((sum, scene) => sum + scene.routeCueCount, 0),
      requiredAssetCount: scenes.reduce((sum, scene) => sum + scene.requiredAssetCount, 0),
      missingAssetCount: scenes.reduce((sum, scene) => sum + scene.missingAssetCount, 0),
      blockerCount,
      warningCount,
      tipCount,
      readinessPercent: scenes.length ? Math.round(totalScore / scenes.length) : 0,
    };
  }

  function buildProductionQueue(issues = []) {
    return toArray(issues)
      .slice()
      .sort((left, right) => getIssueWeight(right) - getIssueWeight(left))
      .slice(0, 16)
      .map((issue, index) => ({
        id: `director_task_${index + 1}`,
        severity: issue.severity,
        title: issue.title,
        detail: issue.detail,
        chapterName: issue.chapterName,
        sceneName: issue.sceneName,
        targetLabel: [issue.chapterName, issue.sceneName].filter(Boolean).join(" / ") || "导演分镜清单",
        actionLabel: issue.severity === "blocker" ? "先修复素材或空场景" : issue.severity === "warn" ? "补齐基础演出" : "做演出润色",
      }));
  }

  function buildDirectorCueSheet(data = {}, options = {}) {
    const assetMap = buildAssetMap(data);
    const characterMap = buildCharacterMap(data);
    const sceneMap = buildSceneMap(data);
    const issues = [];
    const context = { assetMap, characterMap, sceneMap };
    const scenes = getSceneRecords(data).map((record) => buildSceneCue(record, issues, context));
    const sortedIssues = issues.sort((left, right) => getIssueWeight(right) - getIssueWeight(left));
    return {
      formatVersion: 1,
      projectTitle: cleanText(options.projectTitle ?? data.project?.title, "Canvasia Project"),
      summary: summarizeSheet(scenes, sortedIssues),
      scenes,
      issues: sortedIssues,
      productionQueue: buildProductionQueue(sortedIssues),
    };
  }

  function getDirectorCueStatusDigest(sheet = {}) {
    const summary = sheet.summary ?? {};
    if (!(summary.sceneCount ?? 0)) {
      return {
        status: "empty",
        title: "还没有场景分镜",
        detail: "创建场景并加入剧情卡后，就能生成导演分镜清单。",
      };
    }
    if ((summary.blockerCount ?? 0) > 0) {
      return {
        status: "blocked",
        title: `${summary.blockerCount} 个分镜先修`,
        detail: "先处理缺文件、空场景或坏引用，避免试玩和导出时断掉。",
      };
    }
    if ((summary.warningCount ?? 0) > 0) {
      return {
        status: "warn",
        title: `${summary.warningCount} 个分镜优先项`,
        detail: "场景可以继续制作，但建议补齐背景、选项、条件或基础演出。",
      };
    }
    return {
      status: "ready",
      title: "导演分镜可用",
      detail: `已整理 ${summary.sceneCount} 个场景、${summary.cueCount} 条制作节拍，平均就绪度 ${summary.readinessPercent ?? 0}%。`,
    };
  }

  function escapeMarkdownTableCell(value) {
    return String(value ?? "")
      .replace(/\|/g, "\\|")
      .replace(/\r?\n/g, "<br />")
      .trim();
  }

  function buildMarkdownTable(headers = [], rows = []) {
    if (!toArray(rows).length) {
      return "";
    }
    return [
      `| ${toArray(headers).map(escapeMarkdownTableCell).join(" | ")} |`,
      `| ${toArray(headers).map(() => "---").join(" | ")} |`,
      ...toArray(rows).map((row) => `| ${toArray(row).map(escapeMarkdownTableCell).join(" | ")} |`),
    ].join("\n");
  }

  function buildDirectorCueMarkdown(sheet = {}, options = {}) {
    const projectTitle = cleanText(options.projectTitle ?? sheet.projectTitle, "Canvasia Project");
    const generatedAt = cleanText(options.generatedAt);
    const summary = sheet.summary ?? {};
    const digest = getDirectorCueStatusDigest(sheet);
    const sceneRows = toArray(sheet.scenes).map((scene) => [
      scene.chapterName,
      scene.sceneName,
      scene.cueCount,
      scene.requiredAssetCount,
      scene.missingAssetCount,
      scene.readiness?.label,
      `${scene.readiness?.score ?? 0}%`,
    ]);
    const issueRows = toArray(sheet.issues)
      .slice(0, 30)
      .map((issue, index) => [index + 1, issue.severity, issue.chapterName, issue.sceneName, issue.title, issue.detail]);
    const lines = [
      `# ${projectTitle} 导演分镜清单`,
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
        ["场景", "节拍", "剧情", "画面", "声音", "演出", "路线", "缺素材", "平均就绪度"],
        [
          [
            summary.sceneCount ?? 0,
            summary.cueCount ?? 0,
            summary.storyCueCount ?? 0,
            summary.visualCueCount ?? 0,
            summary.audioCueCount ?? 0,
            summary.effectCueCount ?? 0,
            summary.routeCueCount ?? 0,
            summary.missingAssetCount ?? 0,
            `${summary.readinessPercent ?? 0}%`,
          ],
        ]
      ),
      "",
      "## 场景分布",
      "",
      buildMarkdownTable(["章节", "场景", "节拍", "资产", "缺素材", "状态", "就绪度"], sceneRows) || "当前没有场景。",
      "",
      "## 场景 cue cards",
      "",
    ];

    toArray(sheet.scenes).forEach((scene) => {
      lines.push(`### ${scene.chapterName} / ${scene.sceneName}`);
      lines.push("");
      lines.push(`状态：${scene.readiness?.label ?? "未知"} / ${scene.readiness?.score ?? 0}%`);
      lines.push("");
      toArray(scene.cues).slice(0, 18).forEach((cue) => {
        lines.push(`- [${cue.groupLabel}] 第 ${cue.blockIndex + 1} 张：${cue.text}`);
      });
      if (scene.requiredAssets.length) {
        lines.push("");
        lines.push(`资产：${scene.requiredAssets.map((asset) => `${asset.roleLabel}:${asset.assetName}`).join(" / ")}`);
      }
      if (scene.issues.length) {
        lines.push("");
        lines.push(`问题：${scene.issues.map((issue) => issue.title).join(" / ")}`);
      }
      lines.push("");
    });

    lines.push("## 优先问题");
    lines.push("");
    lines.push(buildMarkdownTable(["序号", "级别", "章节", "场景", "问题", "说明"], issueRows) || "当前没有明显分镜问题。");
    lines.push("");
    return `\uFEFF${lines.join("\n")}`;
  }

  function csvCell(value) {
    return `"${String(value ?? "").replace(/"/g, '""')}"`;
  }

  function buildCsv(headers = [], rows = []) {
    return [headers, ...rows].map((row) => toArray(row).map(csvCell).join(",")).join("\n");
  }

  function buildDirectorCueCsv(sheet = {}) {
    const rows = [];
    toArray(sheet.scenes).forEach((scene) => {
      toArray(scene.cues).forEach((cue) => {
        rows.push([
          sheet.projectTitle,
          scene.chapterName,
          scene.sceneName,
          cue.blockIndex + 1,
          cue.groupLabel,
          cue.blockLabel,
          cue.text,
          cue.characterName,
          cue.assetNames.join(" / "),
          cue.targetLabel,
          scene.readiness?.label,
          scene.issues.map((issue) => issue.title).join(" / "),
        ]);
      });
    });
    return `\uFEFF${buildCsv(
      ["项目", "章节", "场景", "卡片序号", "节拍", "卡片类型", "说明", "角色", "关联资产", "目标", "场景状态", "场景问题"],
      rows
    )}\n`;
  }

  function defaultEscapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function getDefaultToneClass(status) {
    if (status === "blocked") {
      return "danger-text";
    }
    if (status === "warn") {
      return "warn-text";
    }
    if (status === "ready") {
      return "good-text";
    }
    return "";
  }

  function renderDirectorCueSheetPanel(sheet = {}, options = {}) {
    const escape = typeof options.escapeHtml === "function" ? options.escapeHtml : defaultEscapeHtml;
    const metric =
      typeof options.renderRouteMetricCard === "function"
        ? options.renderRouteMetricCard
        : (label, value, hint) => `<div><strong>${escape(label)}</strong><b>${escape(value)}</b><span>${escape(hint)}</span></div>`;
    const empty =
      typeof options.renderEmpty === "function"
        ? options.renderEmpty
        : (message) => `<p class="empty-state">${escape(message)}</p>`;
    const toneClass = typeof options.getToneClass === "function" ? options.getToneClass : getDefaultToneClass;
    const digest = getDirectorCueStatusDigest(sheet);
    const summary = sheet.summary ?? {};
    const topIssues = toArray(sheet.issues).slice(0, 4);
    const scenePreview = toArray(sheet.scenes).slice(0, 4);

    return `
      <article class="detail-card preview-sprint-panel">
        <div class="panel-heading">
          <h2>导演分镜清单</h2>
          <span class="badge badge-soft ${toneClass(digest.status)}">${escape(digest.title)}</span>
        </div>
        <p class="helper-text">${escape(digest.detail)} 它会把每个场景拆成剧情、画面、声音、演出、路线节拍，方便像真正制作表一样检查“这一场到底还缺什么”。</p>
        <div class="preview-sprint-metrics">
          ${metric("场景 / 节拍", `${summary.sceneCount ?? 0} / ${summary.cueCount ?? 0}`, "导演视角下的制作 cue")}
          ${metric("画面 / 声音", `${summary.visualCueCount ?? 0} / ${summary.audioCueCount ?? 0}`, "背景、立绘、视频、BGM、音效")}
          ${metric("演出 / 路线", `${summary.effectCueCount ?? 0} / ${summary.routeCueCount ?? 0}`, "镜头、粒子、滤镜、选项和跳转")}
          ${metric("缺素材 / 就绪度", `${summary.missingAssetCount ?? 0} / ${summary.readinessPercent ?? 0}%`, "导出前最该先补的制作缺口")}
        </div>
        <div class="detail-actions">
          <button class="toolbar-button toolbar-button-primary" data-action="export-director-cue-sheet-markdown">
            导出导演分镜清单
          </button>
          <button class="toolbar-button" data-action="export-director-cue-sheet-csv">
            导出分镜 CSV
          </button>
          <button class="toolbar-button" data-action="switch-screen" data-screen="story">
            去剧情页补演出
          </button>
        </div>
        ${
          topIssues.length > 0
            ? `
              <div class="preview-sprint-grid">
                ${topIssues
                  .map(
                    (issue) => `
                      <article class="preview-sprint-card is-${issue.severity === "blocker" ? "danger" : issue.severity === "warn" ? "warn" : "soft"}">
                        <div class="preview-sprint-head">
                          <strong>${escape(issue.title)}</strong>
                          <span class="issue-tag ${issue.severity === "blocker" ? "danger-text" : issue.severity === "warn" ? "warn-text" : ""}">
                            ${escape(issue.severity === "blocker" ? "先修" : issue.severity === "warn" ? "优先" : "润色")}
                          </span>
                        </div>
                        <p>${escape([issue.chapterName, issue.sceneName].filter(Boolean).join(" · "))}</p>
                        <div class="helper-text">${escape(issue.detail)}</div>
                      </article>
                    `
                  )
                  .join("")}
              </div>
            `
            : scenePreview.length > 0
              ? `
                <div class="list-stack compact-stack">
                  ${scenePreview
                    .map(
                      (scene) => `
                        <div class="route-testing-item">
                          <div>
                            <b>${escape(`${scene.chapterName} · ${scene.sceneName}`)}</b>
                            <span>${escape(`节拍 ${scene.cueCount} · 资产 ${scene.requiredAssetCount} · 缺口 ${scene.missingAssetCount}`)}</span>
                          </div>
                          <span>${escape(`${scene.readiness?.label ?? "未知"} · ${scene.readiness?.score ?? 0}%`)}</span>
                        </div>
                      `
                    )
                    .join("")}
                </div>
              `
              : empty("当前项目还没有可生成分镜的场景。先在剧情页加入第一段正文、背景或演出卡。")
        }
      </article>
    `;
  }

  global.CanvasiaEditorDirectorCueSheet = Object.freeze({
    CUE_GROUP_LABELS,
    buildDirectorCueSheet,
    getDirectorCueStatusDigest,
    buildDirectorCueMarkdown,
    buildDirectorCueCsv,
    renderDirectorCueSheetPanel,
  });
})(typeof window !== "undefined" ? window : globalThis);
