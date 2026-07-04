(function attachAudioCueSheetTools(global) {
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
    choice: "选项",
    jump: "跳转",
    condition: "条件",
  });

  const BLOCK_LABELS = Object.freeze({
    ...FALLBACK_BLOCK_LABELS,
    ...(storyBlockCatalogTools.BLOCK_COMPACT_LABELS ?? {}),
  });

  const MUSIC_END_MODE_LABELS = Object.freeze({
    until_next_music: "直到下一首或停止卡",
    scene_end: "覆盖到场景结束",
    after_block: "播放到指定卡片",
  });

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

  function getSafeMusicEndMode(mode) {
    return Object.hasOwn(MUSIC_END_MODE_LABELS, mode) ? mode : "until_next_music";
  }

  function getMusicEndModeLabel(mode) {
    return MUSIC_END_MODE_LABELS[getSafeMusicEndMode(mode)];
  }

  function getBlockLabel(type) {
    return BLOCK_LABELS[type] ?? cleanText(type, "卡片");
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

  function buildChapterMap(data = {}) {
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

  function getCharacterList(data = {}) {
    if (Array.isArray(data.characters)) {
      return data.characters;
    }
    if (data.charactersById instanceof Map) {
      return Array.from(data.charactersById.values());
    }
    if (data.charactersById && typeof data.charactersById === "object") {
      return Object.values(data.charactersById);
    }
    return [];
  }

  function buildCharacterMap(data = {}) {
    const characterMap = new Map();
    getCharacterList(data).forEach((character) => {
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
    } else if (data.charactersById && typeof data.charactersById === "object") {
      Object.entries(data.charactersById).forEach(([id, character]) => {
        if (id) {
          characterMap.set(String(id), character);
        }
      });
    }
    return characterMap;
  }

  function getCharacterName(characterMap = new Map(), characterId = "") {
    const safeId = cleanText(characterId);
    if (!safeId) {
      return "旁白";
    }
    const character = characterMap.get(safeId);
    return cleanText(character?.displayName ?? character?.name, safeId);
  }

  function getOrderedScenes(data = {}) {
    const chapters = toArray(data.chapters);
    const scenes = toArray(data.scenes);
    const chapterOrder = new Map(chapters.map((chapter, index) => [String(chapter?.id ?? ""), index]));
    return scenes
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

  function isStoryContentBlock(block = {}) {
    return ["background", "dialogue", "narration", "character_show", "choice", "video_play", "credits_roll", "wait"].includes(
      block.type
    );
  }

  function summarizeBlock(block = {}, index = 0) {
    const label = getBlockLabel(block.type);
    const text =
      block.text ||
      block.title ||
      block.name ||
      block.assetId ||
      toArray(block.options)
        .map((option) => option?.text)
        .filter(Boolean)
        .join(" / ");
    const summary = cleanText(text);
    return summary ? `第 ${index + 1} 张 · ${label} · ${summary.slice(0, 32)}` : `第 ${index + 1} 张 · ${label}`;
  }

  function pushIssue(target, severity, code, title, detail) {
    target.push({ severity, code, title, detail });
  }

  function getCueStatus(issues = []) {
    const safeIssues = toArray(issues);
    if (safeIssues.some((issue) => issue.severity === "blocker")) {
      return "blocker";
    }
    if (safeIssues.some((issue) => issue.severity === "warn")) {
      return "warn";
    }
    return safeIssues.length > 0 ? "tip" : "good";
  }

  function getCueStatusLabel(status) {
    return status === "blocker" ? "需先修" : status === "warn" ? "建议复查" : status === "tip" ? "可润色" : "正常";
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

  function getAudioControlEndIndex(block = {}, blocks = [], startIndex = 0, issues = []) {
    const endMode = getSafeMusicEndMode(block.endMode);
    const nextAudioControlIndex = blocks.findIndex(
      (candidate, index) => index > startIndex && ["music_play", "music_stop"].includes(candidate?.type)
    );
    const nextAudioControlBlock = nextAudioControlIndex >= 0 ? blocks[nextAudioControlIndex] : null;
    let plannedEndIndex = blocks.length - 1;
    let endBlock = null;
    let endLabel = "场景末尾";
    let validExplicitEnd = false;

    if (endMode === "until_next_music") {
      plannedEndIndex = nextAudioControlIndex >= 0 ? nextAudioControlIndex - 1 : blocks.length - 1;
      endLabel = nextAudioControlIndex >= 0 ? `第 ${nextAudioControlIndex + 1} 张前自动接管` : "后续没有音乐接管";
    } else if (endMode === "scene_end") {
      plannedEndIndex = blocks.length - 1;
      if (nextAudioControlIndex >= 0) {
        pushIssue(
          issues,
          "warn",
          "scene_end_taken_over",
          "场景覆盖被提前接管",
          `这首 BGM 设置为覆盖到场景结束，但第 ${nextAudioControlIndex + 1} 张有新的音乐或停止卡。`
        );
      }
    } else if (endMode === "after_block") {
      const endBlockId = cleanText(block.endBlockId);
      const targetIndex = blocks.findIndex((candidate) => String(candidate?.id ?? "") === endBlockId);
      if (!endBlockId) {
        pushIssue(issues, "warn", "missing_end_block", "缺少结束卡片", "这首 BGM 选择了指定范围，但还没有选择结束卡片。");
      } else if (targetIndex < 0) {
        pushIssue(
          issues,
          "blocker",
          "invalid_end_block",
          "结束卡片不存在",
          `结束卡片 ${endBlockId} 已经找不到，导出前建议重新选择。`
        );
      } else if (targetIndex < startIndex) {
        pushIssue(
          issues,
          "blocker",
          "end_block_before_start",
          "结束卡片在播放卡之前",
          "指定结束卡片排在音乐播放卡之前，范围需要重新选择。"
        );
      } else {
        plannedEndIndex = targetIndex;
        endBlock = blocks[targetIndex];
        endLabel = summarizeBlock(endBlock, targetIndex);
        validExplicitEnd = true;
        if (nextAudioControlIndex >= 0 && nextAudioControlIndex <= targetIndex) {
          pushIssue(
            issues,
            "warn",
            "range_taken_over",
            "指定范围被提前接管",
            `第 ${nextAudioControlIndex + 1} 张音乐或停止卡会在目标结束卡之前接管。`
          );
        }
      }
    }

    return {
      endMode,
      endModeLabel: getMusicEndModeLabel(endMode),
      plannedEndIndex,
      endBlock,
      endLabel,
      nextAudioControlIndex,
      nextAudioControlBlock,
      nextAudioControlLabel: nextAudioControlBlock ? summarizeBlock(nextAudioControlBlock, nextAudioControlIndex) : "",
      validExplicitEnd,
      spanCount: Math.max(1, plannedEndIndex - startIndex + 1),
    };
  }

  function getAudioHandoffInfo(endInfo = {}) {
    const nextIndex = Number.isFinite(endInfo.nextAudioControlIndex) ? endInfo.nextAudioControlIndex : -1;
    const nextBlock = endInfo.nextAudioControlBlock;
    const nextLabel = endInfo.nextAudioControlLabel || (nextBlock ? summarizeBlock(nextBlock, nextIndex) : "");

    if (nextIndex >= 0 && nextIndex <= endInfo.plannedEndIndex) {
      return {
        type: "early_takeover",
        label: `${nextLabel || `第 ${nextIndex + 1} 张`} 会提前接管`,
        needsReview: true,
      };
    }
    if (nextIndex >= 0 && endInfo.endMode === "until_next_music" && nextIndex === endInfo.plannedEndIndex + 1) {
      return {
        type: nextBlock?.type === "music_stop" ? "stop_handoff" : "music_handoff",
        label: nextLabel ? `${nextLabel} 接管` : `第 ${nextIndex + 1} 张接管`,
        needsReview: false,
      };
    }
    if (endInfo.endMode === "after_block") {
      if (!endInfo.validExplicitEnd) {
        return {
          type: "broken_range",
          label: "结束卡片需要重新选择",
          needsReview: true,
        };
      }
      return {
        type: "explicit_end",
        label: `播放到 ${endInfo.endLabel}`,
        needsReview: true,
      };
    }
    if (endInfo.endMode === "scene_end") {
      return {
        type: "scene_end",
        label: "覆盖到场景末尾",
        needsReview: true,
      };
    }
    return {
      type: "open_tail",
      label: "后续没有音乐卡接管",
      needsReview: true,
    };
  }

  function buildAudioCueAuditionHint(cue = {}) {
    if (cue.status === "blocker") {
      return "先修素材或范围，再试听。";
    }
    if (cue.handoffType === "music_handoff") {
      return "从本段开头试听到下一首切入，确认切歌不突兀。";
    }
    if (cue.handoffType === "stop_handoff") {
      return "试听到停止音乐卡，确认淡出长度合适。";
    }
    if (cue.handoffType === "explicit_end") {
      return "重点试听开始卡和结束卡前后。";
    }
    if (cue.handoffType === "scene_end") {
      return "从本段开始试听到场景末尾。";
    }
    return cue.status === "warn" ? "复查提示后再试听一次。" : "抽查这一段的开头和结尾。";
  }

  function finalizeAudioCueStatus(cue = {}) {
    const issues = toArray(cue.issues);
    cue.status = getCueStatus(issues);
    cue.statusLabel = getCueStatusLabel(cue.status);
    cue.needsAudition = cue.status !== "good" || ["music_handoff", "stop_handoff", "explicit_end", "scene_end"].includes(cue.handoffType);
    cue.auditionHint = buildAudioCueAuditionHint(cue);
    return cue;
  }

  function addIssueToCue(cue = {}, severity, code, title, detail) {
    if (!Array.isArray(cue.issues)) {
      cue.issues = [];
    }
    pushIssue(cue.issues, severity, code, title, detail);
    finalizeAudioCueStatus(cue);
  }

  function buildAudioCue(block = {}, context = {}) {
    const issues = [];
    const assetId = cleanText(block.assetId);
    const asset = assetId ? context.assetMap.get(assetId) : null;
    const startIndex = context.blockIndex ?? 0;
    const endInfo = getAudioControlEndIndex(block, context.blocks, startIndex, issues);
    const handoffInfo = getAudioHandoffInfo(endInfo);
    const fadeInMs = Math.round(clampNumber(block.fadeInMs, 0, 30000, 0));
    const fadeOutMs = Math.round(clampNumber(block.fadeOutMs, 0, 30000, 600));
    const volume = Math.round(clampNumber(block.volume, 0, 100, 100));

    if (!assetId) {
      pushIssue(issues, "blocker", "missing_asset", "未选择 BGM 素材", "这张播放音乐卡没有绑定任何 BGM。");
    } else if (!asset) {
      pushIssue(issues, "blocker", "unknown_asset", "BGM 素材不存在", `素材 ${assetId} 不在当前素材库中。`);
    } else if (asset.type && asset.type !== "bgm") {
      pushIssue(issues, "warn", "asset_type_mismatch", "素材类型不是 BGM", `当前素材类型是 ${asset.type}。`);
    } else if (asset.fileExists === false) {
      pushIssue(issues, "blocker", "asset_file_missing", "BGM 文件缺失", "素材条目存在，但真实音频文件暂时不可用。");
    }

    if (fadeInMs <= 0) {
      pushIssue(issues, "tip", "no_fade_in", "未设置淡入", "可以给开场或切歌留 300-1200ms 淡入，听感更自然。");
    }
    if (endInfo.endMode !== "until_next_music" && fadeOutMs <= 0) {
      pushIssue(issues, "tip", "no_fade_out", "未设置范围淡出", "指定范围或场景结束 BGM 建议保留一点淡出时间。");
    }

    const cue = {
      id: cleanText(block.id, `music_${context.blockIndex + 1}`),
      chapterId: context.chapter?.id ?? "",
      chapterName: context.chapter?.name ?? "未分章",
      sceneId: context.scene?.id ?? "",
      sceneName: cleanText(context.scene?.name ?? context.scene?.title, `场景 ${context.sceneIndex + 1}`),
      blockId: cleanText(block.id),
      blockIndex: startIndex,
      startLabel: summarizeBlock(block, startIndex),
      endBlockId: endInfo.endBlock?.id ?? cleanText(block.endBlockId),
      endBlockIndex: endInfo.plannedEndIndex,
      endLabel: endInfo.endLabel,
      spanCount: endInfo.spanCount,
      assetId,
      assetName: cleanText(asset?.name ?? asset?.fileName, assetId || "未选择 BGM"),
      assetReady: Boolean(asset && asset.fileExists !== false),
      volume,
      loop: block.loop !== false,
      fadeInMs,
      fadeOutMs,
      endMode: endInfo.endMode,
      endModeLabel: endInfo.endModeLabel,
      handoffType: handoffInfo.type,
      handoffLabel: handoffInfo.label,
      handoffNeedsReview: handoffInfo.needsReview,
      issues,
    };
    return finalizeAudioCueStatus(cue);
  }

  function auditAudioCueContinuity(cues = []) {
    toArray(cues).forEach((cue, index, orderedCues) => {
      const nextCue = orderedCues[index + 1];
      if (!nextCue || cue.sceneId !== nextCue.sceneId) {
        return;
      }
      if (nextCue.blockIndex > (cue.endBlockIndex ?? cue.blockIndex) + 2) {
        return;
      }
      if (cue.fadeOutMs <= 0 && nextCue.fadeInMs <= 0) {
        addIssueToCue(
          cue,
          "warn",
          "abrupt_music_handoff",
          "切歌没有淡入淡出",
          `下一首 ${nextCue.assetName} 也没有淡入，建议给前后 BGM 留 300-1200ms 过渡。`
        );
      }
      if (cue.assetId && cue.assetId === nextCue.assetId && cue.endMode === "until_next_music") {
        addIssueToCue(
          cue,
          "tip",
          "duplicate_music_restart",
          "同一首 BGM 连续重播",
          "如果只是想让同一首歌继续循环，可以删掉后面重复的播放卡；如果想重头播放，则可以保留。"
        );
      }
    });
  }

  function buildAudioCueRangeRows(cues = []) {
    return toArray(cues).map((cue, index) => ({
      id: cue.id,
      index: index + 1,
      chapterName: cue.chapterName,
      sceneName: cue.sceneName,
      assetName: cue.assetName,
      assetId: cue.assetId,
      coverageLabel: `${cue.startLabel} -> ${cue.endLabel}`,
      handoffLabel: cue.handoffLabel,
      spanLabel: `${cue.spanCount} 张卡`,
      fadeLabel: `${cue.fadeInMs} / ${cue.fadeOutMs} ms`,
      auditionHint: cue.auditionHint,
      status: cue.status,
      statusLabel: cue.statusLabel,
    }));
  }

  function finalizeSfxCueStatus(cue = {}) {
    cue.status = getCueStatus(cue.issues);
    cue.statusLabel = getCueStatusLabel(cue.status);
    cue.reviewHint =
      cue.status === "blocker"
        ? "先补齐音效素材，再做试玩确认。"
        : cue.status === "warn"
          ? "试听这一声的触发点和音量，避免突兀。"
          : cue.status === "tip"
            ? "可以顺手确认音效存在感。"
            : "发布前抽查触发点即可。";
    return cue;
  }

  function addIssueToSfxCue(cue = {}, severity, code, title, detail) {
    if (!Array.isArray(cue.issues)) {
      cue.issues = [];
    }
    pushIssue(cue.issues, severity, code, title, detail);
    finalizeSfxCueStatus(cue);
  }

  function buildSfxCue(block = {}, context = {}) {
    const issues = [];
    const assetId = cleanText(block.assetId);
    const assetHint = cleanText(block.assetHint);
    const asset = assetId ? context.assetMap.get(assetId) : null;
    const volume = Math.round(clampNumber(block.volume, 0, 100, 100));

    if (!assetId) {
      pushIssue(
        issues,
        "blocker",
        "missing_sfx_asset",
        "未选择音效素材",
        assetHint ? `导入脚本提示为 ${assetHint}，但还没有绑定到素材库音效。` : "这张播放音效卡没有绑定任何音效素材。"
      );
    } else if (!asset) {
      pushIssue(issues, "blocker", "unknown_sfx_asset", "音效素材不存在", `素材 ${assetId} 不在当前素材库中。`);
    } else if (asset.type && asset.type !== "sfx") {
      pushIssue(issues, "warn", "sfx_asset_type_mismatch", "素材类型不是音效", `当前素材类型是 ${asset.type}。`);
    } else if (asset.fileExists === false) {
      pushIssue(issues, "blocker", "sfx_file_missing", "音效文件缺失", "素材条目存在，但真实音效文件暂时不可用。");
    }

    if (volume <= 0) {
      pushIssue(issues, "warn", "silent_sfx", "音效音量为 0", "这张音效卡会被触发，但玩家听不到。");
    } else if (volume >= 96) {
      pushIssue(issues, "tip", "very_loud_sfx", "音效音量接近满格", "爆发音效可以保留高音量，但脚步、门铃、环境声建议试听一下。");
    }

    const cue = {
      id: cleanText(block.id, `sfx_${context.blockIndex + 1}`),
      chapterId: context.chapter?.id ?? "",
      chapterName: context.chapter?.name ?? "未分章",
      sceneId: context.scene?.id ?? "",
      sceneName: cleanText(context.scene?.name ?? context.scene?.title, `场景 ${context.sceneIndex + 1}`),
      blockId: cleanText(block.id),
      blockIndex: context.blockIndex ?? 0,
      cueLabel: summarizeBlock(block, context.blockIndex ?? 0),
      assetId,
      assetHint,
      assetName: cleanText(asset?.name ?? asset?.fileName, assetId || assetHint || "未选择音效"),
      assetReady: Boolean(asset && asset.fileExists !== false),
      volume,
      issues,
    };
    return finalizeSfxCueStatus(cue);
  }

  function auditSceneSfxDensity(sceneSfxCues = []) {
    const safeCues = toArray(sceneSfxCues);
    if (safeCues.length <= 6) {
      return;
    }
    addIssueToSfxCue(
      safeCues[0],
      "tip",
      "dense_scene_sfx",
      "当前场景音效较密",
      `这个场景有 ${safeCues.length} 张音效卡。可以保留，但发布前建议从头试玩确认节奏不吵。`
    );
  }

  function buildSfxCueRows(sfxCues = []) {
    return toArray(sfxCues).map((cue, index) => ({
      id: cue.id,
      index: index + 1,
      chapterName: cue.chapterName,
      sceneName: cue.sceneName,
      assetName: cue.assetName,
      assetId: cue.assetId,
      cueLabel: cue.cueLabel,
      volumeLabel: `${cue.volume}%`,
      reviewHint: cue.reviewHint,
      status: cue.status,
      statusLabel: cue.statusLabel,
    }));
  }

  function finalizeVoiceCueStatus(cue = {}) {
    cue.status = getCueStatus(cue.issues);
    cue.statusLabel = getCueStatusLabel(cue.status);
    cue.reviewHint =
      cue.status === "blocker"
        ? "先补齐语音文件，再做试玩确认。"
        : cue.status === "warn"
          ? "试听这一句语音和文字节奏是否贴合。"
          : cue.status === "tip"
            ? "可以顺手确认音量和情绪。"
            : "发布前抽查这一句语音即可。";
    return cue;
  }

  function buildVoiceCue(block = {}, context = {}) {
    const voiceAssetId = cleanText(block.voiceAssetId ?? block.voice?.assetId);
    if (!voiceAssetId) {
      return null;
    }

    const issues = [];
    const asset = context.assetMap.get(voiceAssetId);
    const volume = Math.round(clampNumber(block.voiceVolume, 0, 100, 100));
    const speakerId = cleanText(block.speakerId ?? block.characterId);
    const speakerName = block.type === "narration" ? "旁白" : getCharacterName(context.characterMap, speakerId);

    if (!asset) {
      pushIssue(issues, "blocker", "voice_missing_asset", "语音素材不存在", `素材 ${voiceAssetId} 不在当前素材库中。`);
    } else if (asset.type && asset.type !== "voice") {
      pushIssue(issues, "blocker", "voice_wrong_asset_type", "语音绑定了错误素材类型", `当前素材类型是 ${asset.type}，应改成语音素材。`);
    } else if (asset.fileExists === false) {
      pushIssue(issues, "blocker", "voice_file_missing", "语音文件缺失", "语音条目存在，但真实音频文件暂时不可用。");
    }

    if (volume <= 0) {
      pushIssue(issues, "warn", "silent_voice", "语音音量为 0", "这句语音会被触发，但玩家听不到。");
    }

    const cue = {
      id: cleanText(block.id, `voice_${context.blockIndex + 1}`),
      chapterId: context.chapter?.id ?? "",
      chapterName: context.chapter?.name ?? "未分章",
      sceneId: context.scene?.id ?? "",
      sceneName: cleanText(context.scene?.name ?? context.scene?.title, `场景 ${context.sceneIndex + 1}`),
      blockId: cleanText(block.id),
      blockIndex: context.blockIndex ?? 0,
      cueLabel: summarizeBlock(block, context.blockIndex ?? 0),
      speakerId,
      speakerName,
      textPreview: cleanText(block.text).slice(0, 48),
      assetId: voiceAssetId,
      assetName: cleanText(asset?.name ?? asset?.fileName, voiceAssetId),
      assetReady: Boolean(asset && asset.fileExists !== false),
      volume,
      issues,
    };
    return finalizeVoiceCueStatus(cue);
  }

  function buildVoiceCueRows(voiceCues = []) {
    return toArray(voiceCues).map((cue, index) => ({
      id: cue.id,
      index: index + 1,
      chapterName: cue.chapterName,
      sceneName: cue.sceneName,
      speakerName: cue.speakerName,
      assetName: cue.assetName,
      assetId: cue.assetId,
      cueLabel: cue.cueLabel,
      textPreview: cue.textPreview,
      volumeLabel: `${cue.volume}%`,
      reviewHint: cue.reviewHint,
      status: cue.status,
      statusLabel: cue.statusLabel,
    }));
  }

  function buildAudioCueSheet(data = {}) {
    const assetMap = buildAssetMap(data);
    const chapterMap = buildChapterMap(data);
    const characterMap = buildCharacterMap(data);
    const scenes = getOrderedScenes(data);
    const cues = [];
    const sfxCues = [];
    const voiceCues = [];
    const stops = [];
    const scenesWithoutMusic = [];

    scenes.forEach((scene, sceneIndex) => {
      const blocks = toArray(scene?.blocks);
      const chapter = chapterMap.get(String(scene?.chapterId ?? "")) ?? {
        id: String(scene?.chapterId ?? ""),
        name: "未分章",
      };
      const hasStoryContent = blocks.some(isStoryContentBlock);
      const sceneCues = [];
      const sceneSfxCues = [];

      blocks.forEach((block, blockIndex) => {
        if (block?.type === "music_play") {
          const cue = buildAudioCue(block, { assetMap, blocks, blockIndex, scene, sceneIndex, chapter });
          cues.push(cue);
          sceneCues.push(cue);
        }
        if (block?.type === "sfx_play") {
          const cue = buildSfxCue(block, { assetMap, blockIndex, scene, sceneIndex, chapter });
          sfxCues.push(cue);
          sceneSfxCues.push(cue);
        }
        if (["dialogue", "narration"].includes(block?.type)) {
          const cue = buildVoiceCue(block, { assetMap, characterMap, blockIndex, scene, sceneIndex, chapter });
          if (cue) {
            voiceCues.push(cue);
          }
        }
        if (block?.type === "music_stop") {
          stops.push({
            id: cleanText(block.id, `music_stop_${blockIndex + 1}`),
            chapterName: chapter.name,
            sceneName: cleanText(scene?.name ?? scene?.title, `场景 ${sceneIndex + 1}`),
            blockIndex,
            blockId: cleanText(block.id),
            fadeOutMs: Math.round(clampNumber(block.fadeOutMs, 0, 30000, 600)),
            label: summarizeBlock(block, blockIndex),
          });
        }
      });
      auditSceneSfxDensity(sceneSfxCues);

      if (hasStoryContent && sceneCues.length === 0) {
        scenesWithoutMusic.push({
          sceneId: cleanText(scene?.id),
          sceneName: cleanText(scene?.name ?? scene?.title, `场景 ${sceneIndex + 1}`),
          chapterName: chapter.name,
          blockCount: blocks.length,
        });
      }
    });

    auditAudioCueContinuity(cues);
    const rangeRows = buildAudioCueRangeRows(cues);
    const sfxRows = buildSfxCueRows(sfxCues);
    const voiceRows = buildVoiceCueRows(voiceCues);

    const musicIssues = cues.flatMap((cue) =>
      cue.issues.map((issue) => ({
        ...issue,
        cueType: "bgm",
        cueId: cue.id,
        chapterName: cue.chapterName,
        sceneName: cue.sceneName,
        assetName: cue.assetName,
        startLabel: cue.startLabel,
      }))
    );
    const sfxIssues = sfxCues.flatMap((cue) =>
      cue.issues.map((issue) => ({
        ...issue,
        cueType: "sfx",
        cueId: cue.id,
        chapterName: cue.chapterName,
        sceneName: cue.sceneName,
        assetName: cue.assetName,
        startLabel: cue.cueLabel,
      }))
    );
    const voiceIssues = voiceCues.flatMap((cue) =>
      cue.issues.map((issue) => ({
        ...issue,
        cueType: "voice",
        cueId: cue.id,
        chapterName: cue.chapterName,
        sceneName: cue.sceneName,
        assetName: cue.assetName,
        startLabel: cue.cueLabel,
      }))
    );
    const issues = [...musicIssues, ...sfxIssues, ...voiceIssues]
      .sort((left, right) => getIssueWeight(right) - getIssueWeight(left) || left.sceneName.localeCompare(right.sceneName, "zh-CN"));

    const summary = {
      cueCount: cues.length,
      sfxCueCount: sfxCues.length,
      voiceCueCount: voiceCues.length,
      rangeSegmentCount: rangeRows.length,
      explicitRangeCount: cues.filter((cue) => cue.endMode === "after_block").length,
      sceneEndCount: cues.filter((cue) => cue.endMode === "scene_end").length,
      handoffCount: cues.filter((cue) => ["music_handoff", "stop_handoff"].includes(cue.handoffType)).length,
      openTailCount: cues.filter((cue) => cue.handoffType === "open_tail").length,
      auditionNeededCount: cues.filter((cue) => cue.needsAudition).length,
      takeoverCount: cues.filter((cue) => cue.issues.some((issue) => issue.code.includes("taken_over"))).length,
      abruptHandoffCount: cues.filter((cue) => cue.issues.some((issue) => issue.code === "abrupt_music_handoff")).length,
      sfxIssueCount: sfxIssues.length,
      missingSfxAssetCount: sfxCues.filter((cue) =>
        cue.issues.some((issue) => ["missing_sfx_asset", "unknown_sfx_asset", "sfx_file_missing"].includes(issue.code))
      ).length,
      voiceIssueCount: voiceIssues.length,
      missingVoiceAssetCount: voiceCues.filter((cue) =>
        cue.issues.some((issue) => ["voice_missing_asset", "voice_wrong_asset_type", "voice_file_missing"].includes(issue.code))
      ).length,
      missingAssetCount: cues.filter((cue) =>
        cue.issues.some((issue) => ["missing_asset", "unknown_asset", "asset_file_missing"].includes(issue.code))
      ).length,
      missingEndBlockCount: cues.filter((cue) =>
        cue.issues.some((issue) => ["missing_end_block", "invalid_end_block", "end_block_before_start"].includes(issue.code))
      ).length,
      noFadeCount: cues.filter((cue) => cue.issues.some((issue) => ["no_fade_in", "no_fade_out"].includes(issue.code))).length,
      stopCount: stops.length,
      scenesWithoutMusicCount: scenesWithoutMusic.length,
      blockerCount: issues.filter((issue) => issue.severity === "blocker").length,
      warningCount: issues.filter((issue) => issue.severity === "warn").length,
      tipCount: issues.filter((issue) => issue.severity === "tip").length,
    };

    return {
      projectTitle: cleanText(data.project?.title, "Canvasia Project"),
      cues,
      rangeRows,
      sfxCues,
      sfxRows,
      voiceCues,
      voiceRows,
      stops,
      scenesWithoutMusic,
      issues,
      summary,
    };
  }

  function getAudioCueSheetStatusDigest(sheet = {}) {
    const summary = sheet.summary ?? {};
    if ((summary.cueCount ?? 0) === 0 && (summary.sfxCueCount ?? 0) === 0 && (summary.voiceCueCount ?? 0) === 0) {
      return {
        status: "empty",
        tone: "soft",
        title: "还没有音频调度",
        detail: "项目里暂时没有播放音乐、音效或已绑定语音。可以先给入口场景加一首 BGM，再补关键音效和语音。",
      };
    }
    if ((summary.blockerCount ?? 0) > 0) {
      return {
        status: "blocked",
        tone: "danger",
        title: `有 ${summary.blockerCount} 个音频阻塞问题`,
        detail: "优先修复缺素材、坏范围或真实文件缺失，再做发布前试听。",
      };
    }
    if ((summary.warningCount ?? 0) > 0) {
      return {
        status: "warn",
        tone: "warn",
        title: `有 ${summary.warningCount} 个音频调度提醒`,
        detail: "音频能继续推进，但建议复查被提前接管、范围不清晰或音效异常的位置。",
      };
    }
    return {
      status: "ready",
      tone: "good",
      title: "音频调度表可用于发布前试听",
      detail: `当前 BGM、音效和已绑定语音都有明确素材；其中 ${summary.auditionNeededCount ?? 0} 段 BGM 建议发布前试听确认。`,
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

  function buildAudioCueSheetMarkdown(sheet = {}, context = {}) {
    const digest = getAudioCueSheetStatusDigest(sheet);
    const summary = sheet.summary ?? {};
    const projectTitle = context.projectTitle || sheet.projectTitle || "Canvasia Project";
    const generatedAt = context.generatedAt || new Date().toISOString();
    const cueRows = toArray(sheet.cues).slice(0, 120).map((cue, index) => [
      `${index + 1}`,
      cue.chapterName,
      cue.sceneName,
      cue.assetName,
      cue.endModeLabel,
      cue.startLabel,
      cue.endLabel,
      cue.handoffLabel,
      `${cue.fadeInMs} / ${cue.fadeOutMs} ms`,
      cue.statusLabel,
    ]);
    const rangeRows = toArray(sheet.rangeRows).slice(0, 120).map((row) => [
      `${row.index}`,
      `${row.chapterName} / ${row.sceneName}`,
      row.assetName,
      row.coverageLabel,
      row.handoffLabel,
      row.auditionHint,
      row.statusLabel,
    ]);
    const sfxRows = toArray(sheet.sfxRows).slice(0, 120).map((row) => [
      `${row.index}`,
      `${row.chapterName} / ${row.sceneName}`,
      row.assetName,
      row.cueLabel,
      row.volumeLabel,
      row.reviewHint,
      row.statusLabel,
    ]);
    const voiceRows = toArray(sheet.voiceRows).slice(0, 120).map((row) => [
      `${row.index}`,
      `${row.chapterName} / ${row.sceneName}`,
      row.speakerName,
      row.assetName,
      row.cueLabel,
      row.volumeLabel,
      row.reviewHint,
      row.statusLabel,
    ]);
    const issueRows = toArray(sheet.issues).slice(0, 120).map((issue, index) => [
      `${index + 1}`,
      issue.cueType === "voice" ? "语音" : issue.cueType === "sfx" ? "音效" : "BGM",
      issue.severity === "blocker" ? "阻塞" : issue.severity === "warn" ? "提醒" : "润色",
      issue.chapterName,
      issue.sceneName,
      issue.title,
      issue.detail,
    ]);
    const sceneRows = toArray(sheet.scenesWithoutMusic).slice(0, 80).map((scene, index) => [
      `${index + 1}`,
      scene.chapterName,
      scene.sceneName,
      `${scene.blockCount} 张卡片`,
    ]);

    return `\uFEFF${[
      `# ${projectTitle} 音频调度表`,
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
          ["BGM 播放卡", `${summary.cueCount ?? 0}`],
          ["音效卡", `${summary.sfxCueCount ?? 0}`],
          ["语音卡", `${summary.voiceCueCount ?? 0}`],
          ["覆盖段", `${summary.rangeSegmentCount ?? 0}`],
          ["指定范围", `${summary.explicitRangeCount ?? 0}`],
          ["场景结束范围", `${summary.sceneEndCount ?? 0}`],
          ["自然接管", `${summary.handoffCount ?? 0}`],
          ["建议试听", `${summary.auditionNeededCount ?? 0}`],
          ["停止音乐卡", `${summary.stopCount ?? 0}`],
          ["阻塞问题", `${summary.blockerCount ?? 0}`],
          ["复查提醒", `${summary.warningCount ?? 0}`],
          ["音效缺失", `${summary.missingSfxAssetCount ?? 0}`],
          ["语音缺失", `${summary.missingVoiceAssetCount ?? 0}`],
          ["无 BGM 内容场景", `${summary.scenesWithoutMusicCount ?? 0}`],
        ]
      ),
      "",
      "## BGM 覆盖范围速览",
      "",
      buildMarkdownTable(["序号", "章节 / 场景", "BGM", "覆盖范围", "接管方式", "试听提示", "状态"], rangeRows) ||
        "当前没有可展示的 BGM 覆盖范围。",
      "",
      "## BGM Cue 列表",
      "",
      buildMarkdownTable(["序号", "章节", "场景", "BGM", "范围", "开始", "结束", "接管方式", "淡入/淡出", "状态"], cueRows) ||
        "当前没有播放音乐卡。",
      "",
      "## 音效 Cue 列表",
      "",
      buildMarkdownTable(["序号", "章节 / 场景", "音效", "触发位置", "音量", "试听提示", "状态"], sfxRows) ||
        "当前没有播放音效卡。",
      "",
      "## 语音 Cue 列表",
      "",
      buildMarkdownTable(["序号", "章节 / 场景", "角色", "语音", "触发位置", "音量", "试听提示", "状态"], voiceRows) ||
        "当前没有已绑定语音的台词或旁白。",
      "",
      "## 需要复查的问题",
      "",
      buildMarkdownTable(["序号", "类型", "级别", "章节", "场景", "问题", "说明"], issueRows) || "当前没有明显音频调度问题。",
      "",
      "## 暂无 BGM 的内容场景",
      "",
      buildMarkdownTable(["序号", "章节", "场景", "卡片数"], sceneRows) || "当前没有需要提示的无 BGM 内容场景。",
      "",
    ].join("\n")}`;
  }

  function buildAudioCueSheetCsv(sheet = {}) {
    const musicRows = toArray(sheet.cues).map((cue, index) => [
      "BGM",
      `${index + 1}`,
      cue.chapterName,
      cue.sceneName,
      cue.blockIndex + 1,
      cue.assetName,
      cue.assetId,
      cue.endModeLabel,
      cue.endLabel,
      cue.handoffLabel,
      cue.spanCount,
      cue.volume,
      cue.loop ? "循环" : "不循环",
      cue.fadeInMs,
      cue.fadeOutMs,
      cue.auditionHint,
      cue.statusLabel,
      cue.issues.map((issue) => issue.title).join(" / "),
    ]);
    const sfxRows = toArray(sheet.sfxCues).map((cue, index) => [
      "SFX",
      `${index + 1}`,
      cue.chapterName,
      cue.sceneName,
      cue.blockIndex + 1,
      cue.assetName,
      cue.assetId,
      "播放一次音效",
      cue.cueLabel,
      "",
      "",
      cue.volume,
      "",
      "",
      "",
      cue.reviewHint,
      cue.statusLabel,
      cue.issues.map((issue) => issue.title).join(" / "),
    ]);
    const voiceRows = toArray(sheet.voiceCues).map((cue, index) => [
      "Voice",
      `${index + 1}`,
      cue.chapterName,
      cue.sceneName,
      cue.blockIndex + 1,
      cue.assetName,
      cue.assetId,
      "播放语音",
      cue.cueLabel,
      "",
      "",
      cue.volume,
      "",
      "",
      "",
      cue.reviewHint,
      cue.statusLabel,
      cue.issues.map((issue) => issue.title).join(" / "),
    ]);
    const rows = [...musicRows, ...sfxRows, ...voiceRows];
    return `\uFEFF${buildCsv(
      [
        "类型",
        "序号",
        "章节",
        "场景",
        "开始卡片",
        "素材",
        "素材ID",
        "范围",
        "结束/触发位置",
        "接管方式",
        "覆盖卡片",
        "音量",
        "循环",
        "淡入ms",
        "淡出ms",
        "试听提示",
        "状态",
        "问题",
      ],
      rows
    )}\n`;
  }

  global.CanvasiaEditorAudioCueSheet = Object.freeze({
    getSafeMusicEndMode,
    getMusicEndModeLabel,
    buildAudioCueRangeRows,
    buildSfxCueRows,
    buildVoiceCueRows,
    buildAudioCueSheet,
    getAudioCueSheetStatusDigest,
    buildAudioCueSheetMarkdown,
    buildAudioCueSheetCsv,
  });
})(typeof window !== "undefined" ? window : globalThis);
