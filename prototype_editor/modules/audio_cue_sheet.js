(function attachAudioCueSheetTools(global) {
  const storyBlockCatalogTools = global.CanvasiaEditorStoryBlockCatalog || {};
  const audioTimingTools = global.CanvasiaEditorAudioTimingEstimator || {};

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
  const AUDIO_CUE_AUTO_FIX_DEFAULTS = Object.freeze({
    musicFadeInMs: 700,
    musicFadeOutMs: 900,
    stopFadeOutMs: 700,
  });
  const VOICE_MIX_DEFAULTS = Object.freeze({
    duckingRatio: 45,
    minimumDuckingRatio: 15,
    maximumDuckingRatio: 100,
    safeEffectiveBgmVolume: 55,
    voiceMaskingMargin: 8,
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

  function getProjectRuntimeSettings(data = {}) {
    if (data.project?.runtimeSettings && typeof data.project.runtimeSettings === "object") {
      return data.project.runtimeSettings;
    }
    if (data.runtimeSettings && typeof data.runtimeSettings === "object") {
      return data.runtimeSettings;
    }
    return {};
  }

  function getProjectVoiceDuckingProfile(data = {}) {
    const runtimeSettings = getProjectRuntimeSettings(data);
    const enabled = runtimeSettings.defaultVoiceDuckingEnabled !== false;
    const ratio = Math.round(
      clampNumber(
        runtimeSettings.defaultVoiceDuckingRatio,
        VOICE_MIX_DEFAULTS.minimumDuckingRatio,
        VOICE_MIX_DEFAULTS.maximumDuckingRatio,
        VOICE_MIX_DEFAULTS.duckingRatio
      )
    );
    return {
      enabled,
      ratio,
      label: enabled ? `语音时 BGM 保留 ${ratio}%` : "语音焦点关闭",
    };
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
        String(chapter?.id ?? chapter?.chapterId ?? ""),
        {
          id: String(chapter?.id ?? chapter?.chapterId ?? ""),
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
    const chapterOrder = new Map(chapters.map((chapter, index) => [String(chapter?.id ?? chapter?.chapterId ?? ""), index]));
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

  function cloneSceneForAudioFix(scene = {}) {
    return {
      ...scene,
      blocks: toArray(scene.blocks).map((block) => ({ ...block })),
    };
  }

  function getBlockId(block = {}) {
    return cleanText(block.id);
  }

  function formatAudioSegmentDuration(seconds) {
    if (typeof audioTimingTools.formatEstimatedDuration === "function") {
      return audioTimingTools.formatEstimatedDuration(seconds);
    }
    const safeSeconds = Math.max(0, Math.round(Number(seconds) || 0));
    if (safeSeconds < 60) {
      return `约 ${safeSeconds} 秒`;
    }
    const minutes = Math.floor(safeSeconds / 60);
    const remainingSeconds = safeSeconds % 60;
    return remainingSeconds > 0 ? `约 ${minutes}分${remainingSeconds}秒` : `约 ${minutes} 分钟`;
  }

  function estimateAudioCueTiming(blocks = [], startIndex = 0, endIndex = startIndex) {
    if (typeof audioTimingTools.estimateBlockRangeTiming === "function") {
      return audioTimingTools.estimateBlockRangeTiming(blocks, startIndex, endIndex);
    }
    const safeBlocks = toArray(blocks);
    const safeStart = Math.max(0, Math.min(safeBlocks.length - 1, Number(startIndex) || 0));
    const safeEnd = Math.max(safeStart, Math.min(safeBlocks.length - 1, Number(endIndex) || safeStart));
    const blockCount = safeBlocks.length ? safeEnd - safeStart + 1 : 0;
    return {
      startIndex: safeStart,
      endIndex: safeEnd,
      blockCount,
      estimatedSeconds: 0,
      durationLabel: "约 0 秒",
      readableCharacterCount: 0,
      waitSeconds: 0,
      textBlockCount: 0,
      mediaBlockCount: 0,
      tone: "silent",
    };
  }

  function buildAudioCueTimingHint(timing = {}) {
    if (typeof audioTimingTools.buildAudioSegmentTimingHint === "function") {
      return audioTimingTools.buildAudioSegmentTimingHint(timing);
    }
    return `${timing.durationLabel || formatAudioSegmentDuration(timing.estimatedSeconds)}，约 ${timing.readableCharacterCount ?? 0} 字。`;
  }

  function getRecommendedAudioRangeEndBlockId(blocks = [], startIndex = 0) {
    const safeBlocks = toArray(blocks);
    const nextAudioControlIndex = safeBlocks.findIndex(
      (candidate, index) => index > startIndex && ["music_play", "music_stop"].includes(candidate?.type)
    );
    const lastCandidateIndex = nextAudioControlIndex >= 0 ? nextAudioControlIndex - 1 : safeBlocks.length - 1;

    for (let index = lastCandidateIndex; index >= startIndex; index -= 1) {
      const block = safeBlocks[index];
      if (isStoryContentBlock(block) && getBlockId(block)) {
        return getBlockId(block);
      }
    }
    for (let index = lastCandidateIndex; index >= startIndex; index -= 1) {
      const blockId = getBlockId(safeBlocks[index]);
      if (blockId) {
        return blockId;
      }
    }
    return "";
  }

  function buildAudioCueAutoFixSummary(scenePlans = []) {
    const safePlans = toArray(scenePlans);
    const blockCount = safePlans.reduce((total, plan) => total + (plan.changedBlockCount ?? 0), 0);
    const operationCount = safePlans.reduce((total, plan) => total + (plan.operationCount ?? 0), 0);
    if (!safePlans.length) {
      return "音频基础参数已经比较完整";
    }
    return `已准备修复 ${safePlans.length} 个场景、${blockCount} 张音频卡、${operationCount} 个基础参数`;
  }

  function getAudioAutoFixDefaults(options = {}) {
    return {
      musicFadeInMs: Math.round(clampNumber(options.musicFadeInMs, 100, 30000, AUDIO_CUE_AUTO_FIX_DEFAULTS.musicFadeInMs)),
      musicFadeOutMs: Math.round(clampNumber(options.musicFadeOutMs, 100, 30000, AUDIO_CUE_AUTO_FIX_DEFAULTS.musicFadeOutMs)),
      stopFadeOutMs: Math.round(clampNumber(options.stopFadeOutMs, 100, 30000, AUDIO_CUE_AUTO_FIX_DEFAULTS.stopFadeOutMs)),
    };
  }

  function buildAudioCueAutoFixPlan(data = {}, options = {}) {
    const defaults = getAudioAutoFixDefaults(options);
    const chapterMap = buildChapterMap(data);
    const scenePlans = [];

    getOrderedScenes(data).forEach((scene, sceneIndex) => {
      const updatedScene = cloneSceneForAudioFix(scene);
      const operations = [];
      const changedBlockIds = new Set();

      updatedScene.blocks.forEach((block, blockIndex, blocks) => {
        if (block?.type === "music_play") {
          const rawEndMode = block.endMode;
          let endMode = getSafeMusicEndMode(rawEndMode);
          if (rawEndMode !== endMode) {
            block.endMode = endMode;
            changedBlockIds.add(getBlockId(block) || `block_${blockIndex + 1}`);
            operations.push({
              blockId: getBlockId(block),
              blockIndex,
              label: "修正 BGM 范围模式",
              detail: `无法识别的范围模式已改为 ${getMusicEndModeLabel(endMode)}。`,
            });
          }

          const fadeInMs = Math.round(clampNumber(block.fadeInMs, 0, 30000, 0));
          if (fadeInMs <= 0) {
            block.fadeInMs = defaults.musicFadeInMs;
            changedBlockIds.add(getBlockId(block) || `block_${blockIndex + 1}`);
            operations.push({
              blockId: getBlockId(block),
              blockIndex,
              label: "补 BGM 淡入",
              detail: `淡入已设为 ${defaults.musicFadeInMs}ms。`,
            });
          }

          if (endMode === "after_block") {
            const endBlockId = cleanText(block.endBlockId);
            const endBlockIndex = blocks.findIndex((candidate) => getBlockId(candidate) === endBlockId);
            if (!endBlockId || endBlockIndex < blockIndex) {
              const recommendedEndBlockId = getRecommendedAudioRangeEndBlockId(blocks, blockIndex);
              if (recommendedEndBlockId) {
                block.endBlockId = recommendedEndBlockId;
                changedBlockIds.add(getBlockId(block) || `block_${blockIndex + 1}`);
                operations.push({
                  blockId: getBlockId(block),
                  blockIndex,
                  label: "补 BGM 结束卡片",
                  detail: `结束卡片已改为 ${recommendedEndBlockId}。`,
                });
              } else {
                endMode = "scene_end";
                block.endMode = endMode;
                block.endBlockId = "";
                changedBlockIds.add(getBlockId(block) || `block_${blockIndex + 1}`);
                operations.push({
                  blockId: getBlockId(block),
                  blockIndex,
                  label: "改为覆盖到场景结束",
                  detail: "当前场景没有可用结束卡片，已改为覆盖到场景结束。",
                });
              }
            }
          }

          const fadeOutMs = Math.round(clampNumber(block.fadeOutMs, 0, 30000, 0));
          if (endMode !== "until_next_music" && fadeOutMs <= 0) {
            block.fadeOutMs = defaults.musicFadeOutMs;
            changedBlockIds.add(getBlockId(block) || `block_${blockIndex + 1}`);
            operations.push({
              blockId: getBlockId(block),
              blockIndex,
              label: "补 BGM 范围淡出",
              detail: `范围淡出已设为 ${defaults.musicFadeOutMs}ms。`,
            });
          }
        }

        if (block?.type === "music_stop") {
          const fadeOutMs = Math.round(clampNumber(block.fadeOutMs, 0, 30000, 0));
          if (fadeOutMs <= 0) {
            block.fadeOutMs = defaults.stopFadeOutMs;
            changedBlockIds.add(getBlockId(block) || `block_${blockIndex + 1}`);
            operations.push({
              blockId: getBlockId(block),
              blockIndex,
              label: "补停止音乐淡出",
              detail: `停止音乐淡出已设为 ${defaults.stopFadeOutMs}ms。`,
            });
          }
        }
      });

      if (operations.length > 0) {
        const chapter = chapterMap.get(String(scene?.chapterId ?? "")) ?? {
          id: String(scene?.chapterId ?? ""),
          name: "未分章",
        };
        scenePlans.push({
          scene: updatedScene,
          sceneId: cleanText(scene?.id),
          sceneName: cleanText(scene?.name ?? scene?.title, `场景 ${sceneIndex + 1}`),
          chapterId: chapter.id,
          chapterName: chapter.name,
          operations,
          operationCount: operations.length,
          changedBlockCount: changedBlockIds.size,
          firstChangedBlockId: operations[0]?.blockId ?? "",
          firstChangedIndex: operations[0]?.blockIndex ?? 0,
        });
      }
    });

    return {
      changed: scenePlans.length > 0,
      scenePlans,
      changedSceneCount: scenePlans.length,
      changedBlockCount: scenePlans.reduce((total, plan) => total + (plan.changedBlockCount ?? 0), 0),
      operationCount: scenePlans.reduce((total, plan) => total + (plan.operationCount ?? 0), 0),
      firstChangedSceneId: scenePlans[0]?.sceneId ?? "",
      firstChangedBlockId: scenePlans[0]?.firstChangedBlockId ?? "",
      firstChangedIndex: scenePlans[0]?.firstChangedIndex ?? 0,
      summary: buildAudioCueAutoFixSummary(scenePlans),
    };
  }

  function getAudioCueAutoFixDigest(data = {}, options = {}) {
    const plan = buildAudioCueAutoFixPlan(data, options);
    return {
      canApply: plan.changed,
      actionLabel: plan.changed ? `一键补齐 ${plan.operationCount} 个音频参数` : "音频基础参数已完整",
      badgeLabel: plan.changed ? `${plan.changedSceneCount} 个场景可自动修` : "无需自动修",
      helperText: plan.changed
        ? "只会补淡入淡出和坏掉的 BGM 范围，不会替你乱选或删除素材。"
        : "当前项目的 BGM 淡入淡出、停止淡出和基础范围参数已经比较完整。",
      plan,
    };
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
    const timingPrefix = cue.timingHint ? `${cue.timingHint} ` : "";
    if (cue.status === "blocker") {
      return `${timingPrefix}先修素材或范围，再试听。`;
    }
    if (cue.handoffType === "music_handoff") {
      return `${timingPrefix}从本段开头试听到下一首切入，确认切歌不突兀。`;
    }
    if (cue.handoffType === "stop_handoff") {
      return `${timingPrefix}试听到停止音乐卡，确认淡出长度合适。`;
    }
    if (cue.handoffType === "explicit_end") {
      return `${timingPrefix}重点试听开始卡和结束卡前后。`;
    }
    if (cue.handoffType === "scene_end") {
      return `${timingPrefix}从本段开始试听到场景末尾。`;
    }
    return cue.status === "warn" ? `${timingPrefix}复查提示后再试听一次。` : `${timingPrefix}抽查这一段的开头和结尾。`;
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
    const timing = estimateAudioCueTiming(context.blocks, startIndex, endInfo.plannedEndIndex);
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
    if (timing.tone === "silent") {
      pushIssue(issues, "tip", "bgm_range_without_text", "BGM 范围几乎没有正文", "这段音乐覆盖的正文很少，建议确认是否只是短转场。");
    } else if (timing.tone === "short" && endInfo.endMode === "after_block") {
      pushIssue(issues, "tip", "short_bgm_segment", "BGM 覆盖段偏短", "这段指定范围预计时长较短，适合短提示或转场；如果是主旋律可以放宽结束点。");
    } else if (timing.tone === "long") {
      pushIssue(issues, "tip", "long_bgm_segment", "BGM 覆盖段较长", "这段预计播放时间较长，建议发布前重点试听循环和情绪是否疲劳。");
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
      timing,
      durationSeconds: timing.estimatedSeconds,
      durationLabel: timing.durationLabel,
      readableCharacterCount: timing.readableCharacterCount,
      waitSeconds: timing.waitSeconds,
      textBlockCount: timing.textBlockCount,
      timingTone: timing.tone,
      timingHint: buildAudioCueTimingHint(timing),
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

  function getVoiceCuesCoveredByMusicCue(cue = {}, voiceCues = []) {
    return toArray(voiceCues).filter(
      (voiceCue) =>
        voiceCue.sceneId === cue.sceneId &&
        (voiceCue.blockIndex ?? -1) >= (cue.blockIndex ?? 0) &&
        (voiceCue.blockIndex ?? -1) <= (cue.endBlockIndex ?? cue.blockIndex ?? 0)
    );
  }

  function getAverageCueVolume(cues = []) {
    const volumes = toArray(cues)
      .map((cue) => Number(cue.volume))
      .filter((volume) => Number.isFinite(volume));
    if (!volumes.length) {
      return 100;
    }
    return Math.round(volumes.reduce((total, volume) => total + volume, 0) / volumes.length);
  }

  function getVoiceMixRiskLabel(risk = "") {
    if (risk === "warn") {
      return "建议先调";
    }
    if (risk === "tip") {
      return "建议试听";
    }
    return "安全";
  }

  function buildVoiceMusicMixRow(cue = {}, coveredVoices = [], profile = getProjectVoiceDuckingProfile()) {
    const averageVoiceVolume = getAverageCueVolume(coveredVoices);
    const effectiveBgmVolume = profile.enabled ? Math.round((cue.volume ?? 100) * profile.ratio / 100) : cue.volume ?? 100;
    let risk = "good";
    let code = "voice_mix_safe";
    let title = "人声混音安全";
    let detail = `语音时 BGM 约 ${effectiveBgmVolume}%，平均语音 ${averageVoiceVolume}%，当前不容易盖住台词。`;
    let reviewHint = "发布前抽查这一段的人声清晰度即可。";

    if (!profile.enabled && (cue.volume ?? 100) >= 65) {
      risk = "warn";
      code = "voice_mix_ducking_disabled";
      title = "语音焦点关闭且 BGM 偏高";
      detail = `这段有 ${coveredVoices.length} 句语音，但语音焦点关闭，BGM 原始音量 ${cue.volume}% 可能盖过台词。`;
      reviewHint = "建议开启语音焦点，或把这段 BGM 音量降到 55-65% 后试听。";
    } else if (
      effectiveBgmVolume >= VOICE_MIX_DEFAULTS.safeEffectiveBgmVolume &&
      effectiveBgmVolume >= averageVoiceVolume - VOICE_MIX_DEFAULTS.voiceMaskingMargin
    ) {
      risk = "warn";
      code = "voice_mix_bgm_may_mask_voice";
      title = "BGM 可能盖过语音";
      detail = `语音时 BGM 约 ${effectiveBgmVolume}%，平均语音 ${averageVoiceVolume}%，对白清晰度可能不足。`;
      reviewHint = "建议降低 BGM 音量或语音时 BGM 保留比例，再从第一句语音开始试听。";
    } else if (profile.enabled && profile.ratio >= 75 && coveredVoices.length >= 2) {
      risk = "tip";
      code = "voice_mix_high_ducking_ratio";
      title = "语音时 BGM 保留比例偏高";
      detail = `这段有 ${coveredVoices.length} 句语音，当前语音时 BGM 仍保留 ${profile.ratio}%。`;
      reviewHint = "如果对白不够清楚，可以把语音时 BGM 保留降到 35-55%。";
    } else if ((cue.volume ?? 100) >= 92 && coveredVoices.length >= 2) {
      risk = "tip";
      code = "voice_mix_loud_music_source";
      title = "BGM 原始音量接近满格";
      detail = `这段 BGM 原始音量 ${cue.volume}%，虽然有语音压低，仍建议确认切入和对白开头。`;
      reviewHint = "重点试听第一句语音开头，确认音乐没有突然顶上来。";
    }

    return {
      id: `voice_mix_${cue.id}`,
      cueId: cue.id,
      sceneId: cue.sceneId,
      sceneName: cue.sceneName,
      chapterName: cue.chapterName,
      assetName: cue.assetName,
      assetId: cue.assetId,
      startLabel: cue.startLabel,
      endLabel: cue.endLabel,
      voiceCount: coveredVoices.length,
      speakerNames: Array.from(new Set(coveredVoices.map((voiceCue) => voiceCue.speakerName).filter(Boolean))).join(" / "),
      bgmVolume: cue.volume,
      averageVoiceVolume,
      effectiveBgmVolume,
      duckingLabel: profile.label,
      risk,
      riskLabel: getVoiceMixRiskLabel(risk),
      code,
      title,
      detail,
      reviewHint,
    };
  }

  function auditVoiceMusicMix(cues = [], voiceCues = [], profile = getProjectVoiceDuckingProfile()) {
    return toArray(cues)
      .map((cue) => {
        const coveredVoices = getVoiceCuesCoveredByMusicCue(cue, voiceCues);
        if (!coveredVoices.length) {
          return null;
        }
        const row = buildVoiceMusicMixRow(cue, coveredVoices, profile);
        if (row.risk !== "good") {
          addIssueToCue(cue, row.risk === "warn" ? "warn" : "tip", row.code, row.title, row.detail);
        }
        return row;
      })
      .filter(Boolean);
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
      durationLabel: cue.durationLabel,
      textLoadLabel: `${cue.readableCharacterCount ?? 0} 字 / ${cue.textBlockCount ?? cue.timing?.textBlockCount ?? 0} 段正文`,
      timingHint: cue.timingHint,
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

  function getAudioRangeSuggestionTone(code = "") {
    if (["invalid_explicit_range", "missing_explicit_range", "backward_explicit_range"].includes(code)) {
      return "warn";
    }
    return "soft";
  }

  function buildAudioRangeSuggestion(block = {}, context = {}, cue = {}) {
    const blocks = toArray(context.blocks);
    const startIndex = context.blockIndex ?? 0;
    const blockId = getBlockId(block);
    const recommendedEndBlockId = getRecommendedAudioRangeEndBlockId(blocks, startIndex);
    const recommendedEndIndex = blocks.findIndex((candidate) => getBlockId(candidate) === recommendedEndBlockId);
    if (!blockId || !recommendedEndBlockId || recommendedEndIndex < startIndex) {
      return null;
    }

    const endMode = getSafeMusicEndMode(block.endMode);
    const currentEndBlockId = cleanText(block.endBlockId);
    const currentEndIndex = blocks.findIndex((candidate) => getBlockId(candidate) === currentEndBlockId);
    const isAlreadyRecommendedExplicitRange =
      endMode === "after_block" && currentEndBlockId === recommendedEndBlockId && Math.round(clampNumber(block.fadeOutMs, 0, 30000, 0)) > 0;
    if (isAlreadyRecommendedExplicitRange) {
      return null;
    }

    let code = "make_explicit_range";
    let reason = "当前 BGM 依赖自动接管；显式绑定到一段文本后，后期替换音乐、插入演出或导出审听表会更清楚。";
    if (endMode === "after_block" && !currentEndBlockId) {
      code = "missing_explicit_range";
      reason = "这首 BGM 已选择“播放到指定卡片”，但还没有结束卡片。";
    } else if (endMode === "after_block" && currentEndIndex < 0) {
      code = "invalid_explicit_range";
      reason = "当前结束卡片已经找不到，可以用系统建议的文本范围重新绑定。";
    } else if (endMode === "after_block" && currentEndIndex < startIndex) {
      code = "backward_explicit_range";
      reason = "当前结束卡片排在播放卡之前，需要重新指定一个正文范围。";
    } else if (endMode === "scene_end") {
      code = "scene_end_to_explicit_range";
      reason = "当前 BGM 覆盖到场景末尾；如果结尾还有等待、片尾或转场，显式结束点更稳。";
    }

    const fadeOutMs = Math.round(clampNumber(block.fadeOutMs, 0, 30000, 0)) || AUDIO_CUE_AUTO_FIX_DEFAULTS.musicFadeOutMs;
    const recommendedEndLabel = summarizeBlock(blocks[recommendedEndIndex], recommendedEndIndex);
    const startLabel = cue.startLabel || summarizeBlock(block, startIndex);
    const assetName = cue.assetName || cleanText(block.assetId, "未选择 BGM");
    const tone = getAudioRangeSuggestionTone(code);

    return {
      id: `${cleanText(context.scene?.id, "scene")}_${blockId}_${recommendedEndBlockId}`,
      code,
      tone,
      confidence: tone === "warn" ? "high" : "medium",
      sceneId: cleanText(context.scene?.id),
      sceneName: cleanText(context.scene?.name ?? context.scene?.title, `场景 ${(context.sceneIndex ?? 0) + 1}`),
      chapterId: context.chapter?.id ?? "",
      chapterName: context.chapter?.name ?? "未分章",
      blockId,
      blockIndex: startIndex,
      endBlockId: recommendedEndBlockId,
      endBlockIndex: recommendedEndIndex,
      endMode: "after_block",
      fadeOutMs,
      assetId: cue.assetId || cleanText(block.assetId),
      assetName,
      title: tone === "warn" ? "修正 BGM 文本范围" : "建议明确 BGM 文本范围",
      detail: `${reason} 建议从 ${startLabel} 播到 ${recommendedEndLabel}。`,
      startLabel,
      endLabel: recommendedEndLabel,
      currentRangeLabel: cue.handoffLabel || getMusicEndModeLabel(endMode),
      actionLabel: "套用这个范围",
    };
  }

  function applyAudioRangeSuggestionToScene(scene = {}, suggestion = {}) {
    const updatedScene = cloneSceneForAudioFix(scene);
    const blocks = toArray(updatedScene.blocks);
    const blockId = cleanText(suggestion.blockId);
    const endBlockId = cleanText(suggestion.endBlockId ?? suggestion.recommendedEndBlockId);
    const blockIndex = blocks.findIndex((block) => getBlockId(block) === blockId);
    const endBlockIndex = blocks.findIndex((block) => getBlockId(block) === endBlockId);

    if (blockIndex < 0) {
      return { ok: false, error: "找不到要调整的 BGM 播放卡。" };
    }
    if (blocks[blockIndex]?.type !== "music_play") {
      return { ok: false, error: "目标卡片不是 BGM 播放卡，无法套用音频范围。" };
    }
    if (endBlockIndex < 0) {
      return { ok: false, error: "找不到建议的结束卡片，可能场景内容已经变化。" };
    }
    if (endBlockIndex < blockIndex) {
      return { ok: false, error: "建议的结束卡片在 BGM 播放卡之前，无法套用。" };
    }

    const block = blocks[blockIndex];
    block.endMode = "after_block";
    block.endBlockId = endBlockId;
    const nextFadeOutMs = Math.round(clampNumber(suggestion.fadeOutMs ?? block.fadeOutMs, 0, 30000, 0));
    block.fadeOutMs = nextFadeOutMs > 0 ? nextFadeOutMs : AUDIO_CUE_AUTO_FIX_DEFAULTS.musicFadeOutMs;

    return {
      ok: true,
      scene: updatedScene,
      blockId,
      endBlockId,
      blockIndex,
      endBlockIndex,
      message: `已把 BGM 范围绑定到第 ${endBlockIndex + 1} 张卡片。`,
    };
  }

  function getAudioProductionSeverityLabel(severity = "") {
    if (severity === "blocker") {
      return "先修";
    }
    if (severity === "warn") {
      return "复查";
    }
    return "润色";
  }

  function getAudioIssueActionLabel(issue = {}) {
    const code = String(issue.code ?? "");
    if (code.includes("voice_mix") || code.includes("ducking")) {
      return "调整 BGM 音量或语音焦点";
    }
    if (code.includes("asset") || code.includes("file_missing")) {
      return "补齐或重新绑定素材";
    }
    if (code.includes("end_block") || code.includes("range")) {
      return "重新选择 BGM 结束范围";
    }
    if (code.includes("handoff") || code.includes("taken_over")) {
      return "试听切歌点并调整淡入淡出";
    }
    if (code.includes("silent")) {
      return "检查音量是否误设为 0";
    }
    if (code.includes("fade")) {
      return "补 300-1200ms 淡入淡出";
    }
    return "打开对应场景复查";
  }

  function getAudioIssueTargetLabel(issue = {}) {
    return cleanText(
      [issue.chapterName, issue.sceneName, issue.startLabel || issue.assetName]
        .filter(Boolean)
        .join(" · "),
      "未定位音频问题"
    );
  }

  function getProductionTaskWeight(task = {}) {
    const severityWeight = task.severity === "blocker" ? 1000 : task.severity === "warn" ? 600 : 220;
    const code = String(task.code ?? "");
    const codeWeight =
      code.includes("file_missing") || code.includes("unknown") || code.includes("missing_asset")
        ? 80
        : code.includes("end_block") || code.includes("range")
          ? 70
          : code.includes("voice_mix") || code.includes("ducking")
            ? 55
            : code.includes("handoff") || code.includes("taken_over")
            ? 45
            : code.includes("scene_without_music")
              ? 25
              : code.includes("audition")
                ? 10
                : 0;
    return severityWeight + codeWeight;
  }

  function buildAudioCueProductionQueue(sheet = {}) {
    const tasks = [];

    toArray(sheet.rangeSuggestions).forEach((suggestion, index) => {
      tasks.push({
        id: `range_suggestion_${suggestion.id || index}`,
        code: suggestion.code ?? "bgm_range_suggestion",
        severity: suggestion.tone === "warn" ? "warn" : "tip",
        phase: suggestion.tone === "warn" ? "修范围" : "范围",
        title: suggestion.title ?? "明确 BGM 覆盖范围",
        detail: suggestion.detail ?? "",
        targetLabel: cleanText(`${suggestion.chapterName ?? "未分章"} · ${suggestion.sceneName ?? "未命名场景"} · ${suggestion.assetName ?? "BGM"}`),
        actionLabel: suggestion.actionLabel ?? "套用建议范围",
        cueType: "bgm",
      });
    });

    toArray(sheet.issues).forEach((issue, index) => {
      tasks.push({
        id: `issue_${issue.cueId ?? index}_${issue.code ?? index}`,
        code: issue.code ?? "audio_issue",
        severity: issue.severity ?? "tip",
        phase: getAudioProductionSeverityLabel(issue.severity),
        title: issue.title ?? "音频问题",
        detail: issue.detail ?? "",
        targetLabel: getAudioIssueTargetLabel(issue),
        actionLabel: getAudioIssueActionLabel(issue),
        cueType: issue.cueType ?? "audio",
      });
    });

    toArray(sheet.scenesWithoutMusic).forEach((scene, index) => {
      tasks.push({
        id: `scene_without_music_${scene.sceneId || index}`,
        code: "scene_without_music",
        severity: "tip",
        phase: "氛围",
        title: "内容场景暂无 BGM",
        detail: `这个场景有 ${scene.blockCount ?? 0} 张剧情卡，但还没有主动播放 BGM。`,
        targetLabel: cleanText(`${scene.chapterName ?? "未分章"} · ${scene.sceneName ?? "未命名场景"}`),
        actionLabel: "给场景开头补一张 BGM 播放卡",
        cueType: "bgm",
      });
    });

    toArray(sheet.cues)
      .filter((cue) => cue.needsAudition)
      .forEach((cue, index) => {
        tasks.push({
          id: `audition_bgm_${cue.id || index}`,
          code: "audition_bgm_segment",
          severity: cue.status === "blocker" ? "blocker" : cue.status === "warn" ? "warn" : "tip",
          phase: cue.status === "blocker" ? "修完再听" : "试听",
          title: "试听 BGM 覆盖段",
          detail: cue.auditionHint,
          targetLabel: `${cue.chapterName} · ${cue.sceneName} · ${cue.assetName}`,
          actionLabel: cue.handoffLabel,
          cueType: "bgm",
        });
      });

    return tasks
      .sort((left, right) => {
        const weightDelta = getProductionTaskWeight(right) - getProductionTaskWeight(left);
        if (weightDelta !== 0) {
          return weightDelta;
        }
        return String(left.targetLabel ?? "").localeCompare(String(right.targetLabel ?? ""), "zh-CN");
      })
      .slice(0, 160)
      .map((task, index) => ({
        ...task,
        rank: index + 1,
      }));
  }

  function buildAudioCueAuditionChecklist(sheet = {}) {
    const rows = [];

    toArray(sheet.cues)
      .filter((cue) => cue.needsAudition)
      .forEach((cue, index) => {
        rows.push({
          id: `bgm_${cue.id || index}`,
          type: "BGM",
          priority: cue.status === "blocker" ? "修完再听" : cue.status === "warn" ? "重点试听" : "抽查",
          targetLabel: `${cue.chapterName} · ${cue.sceneName}`,
          assetName: cue.assetName,
          cueLabel: `${cue.startLabel} -> ${cue.endLabel}`,
          actionLabel: cue.auditionHint,
          statusLabel: cue.statusLabel,
        });
      });

    toArray(sheet.voiceMixRows)
      .filter((row) => row.risk !== "good")
      .forEach((row, index) => {
        rows.push({
          id: `mix_${row.id || index}`,
          type: "Mix",
          priority: row.risk === "warn" ? "重点试听" : "抽查",
          targetLabel: `${row.chapterName} · ${row.sceneName}`,
          assetName: row.assetName,
          cueLabel: `${row.startLabel} -> ${row.endLabel}`,
          actionLabel: row.reviewHint,
          statusLabel: row.riskLabel,
        });
      });

    toArray(sheet.sfxCues)
      .filter((cue, index) => cue.status !== "good" || index < 12)
      .forEach((cue, index) => {
        rows.push({
          id: `sfx_${cue.id || index}`,
          type: "SFX",
          priority: cue.status === "blocker" ? "修完再听" : cue.status === "warn" ? "重点试听" : "抽查",
          targetLabel: `${cue.chapterName} · ${cue.sceneName}`,
          assetName: cue.assetName,
          cueLabel: cue.cueLabel,
          actionLabel: cue.reviewHint,
          statusLabel: cue.statusLabel,
        });
      });

    toArray(sheet.voiceCues)
      .filter((cue, index) => cue.status !== "good" || index < 12)
      .forEach((cue, index) => {
        rows.push({
          id: `voice_${cue.id || index}`,
          type: "Voice",
          priority: cue.status === "blocker" ? "修完再听" : cue.status === "warn" ? "重点试听" : "抽查",
          targetLabel: `${cue.chapterName} · ${cue.sceneName} · ${cue.speakerName}`,
          assetName: cue.assetName,
          cueLabel: cue.textPreview || cue.cueLabel,
          actionLabel: cue.reviewHint,
          statusLabel: cue.statusLabel,
        });
      });

    return rows.slice(0, 160).map((row, index) => ({
      ...row,
      rank: index + 1,
    }));
  }

  function getAudioCueReadinessPercent(summary = {}) {
    const cueTotal = (summary.cueCount ?? 0) + (summary.sfxCueCount ?? 0) + (summary.voiceCueCount ?? 0);
    if (cueTotal <= 0) {
      return 0;
    }
    const penalty =
      (summary.blockerCount ?? 0) * 18 +
      (summary.warningCount ?? 0) * 8 +
      (summary.tipCount ?? 0) * 2 +
      Math.min(24, (summary.scenesWithoutMusicCount ?? 0) * 4);
    return Math.round(clampNumber(100 - penalty, 0, 100, 100));
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
    const rangeSuggestions = [];
    const scenesWithoutMusic = [];
    const voiceMixProfile = getProjectVoiceDuckingProfile(data);

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
          const suggestion = buildAudioRangeSuggestion(block, { blocks, blockIndex, scene, sceneIndex, chapter }, cue);
          if (suggestion) {
            rangeSuggestions.push(suggestion);
          }
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
    const voiceMixRows = auditVoiceMusicMix(cues, voiceCues, voiceMixProfile);
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
      totalEstimatedMusicSeconds: Math.round(cues.reduce((total, cue) => total + (Number(cue.durationSeconds) || 0), 0)),
      shortMusicSegmentCount: cues.filter((cue) => cue.timingTone === "short").length,
      longMusicSegmentCount: cues.filter((cue) => cue.timingTone === "long").length,
      silentMusicSegmentCount: cues.filter((cue) => cue.timingTone === "silent").length,
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
      voiceMusicSegmentCount: voiceMixRows.length,
      voiceMixWarningCount: voiceMixRows.filter((row) => row.risk === "warn").length,
      voiceMixTipCount: voiceMixRows.filter((row) => row.risk === "tip").length,
      stopCount: stops.length,
      scenesWithoutMusicCount: scenesWithoutMusic.length,
      blockerCount: issues.filter((issue) => issue.severity === "blocker").length,
      warningCount: issues.filter((issue) => issue.severity === "warn").length,
      tipCount: issues.filter((issue) => issue.severity === "tip").length,
    };

    const sheet = {
      projectTitle: cleanText(data.project?.title, "Canvasia Project"),
      cues,
      rangeRows,
      sfxCues,
      sfxRows,
      voiceCues,
      voiceRows,
      voiceMixRows,
      voiceMixProfile,
      stops,
      scenesWithoutMusic,
      rangeSuggestions,
      issues,
      summary,
    };
    const productionQueue = buildAudioCueProductionQueue(sheet);
    const auditionChecklist = buildAudioCueAuditionChecklist(sheet);
    summary.productionTaskCount = productionQueue.length;
    summary.auditionChecklistCount = auditionChecklist.length;
    summary.releaseReadinessPercent = getAudioCueReadinessPercent(summary);
    const autoFixPlan = buildAudioCueAutoFixPlan(data);
    summary.autoFixSceneCount = autoFixPlan.changedSceneCount;
    summary.autoFixBlockCount = autoFixPlan.changedBlockCount;
    summary.autoFixOperationCount = autoFixPlan.operationCount;
    summary.rangeSuggestionCount = rangeSuggestions.length;

    return {
      ...sheet,
      productionQueue,
      auditionChecklist,
      autoFixPlan,
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
      cue.durationLabel,
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
      row.durationLabel,
      row.textLoadLabel,
      row.handoffLabel,
      row.auditionHint,
      row.statusLabel,
    ]);
    const rangeSuggestionRows = toArray(sheet.rangeSuggestions).slice(0, 120).map((suggestion, index) => [
      `${index + 1}`,
      suggestion.tone === "warn" ? "建议先修" : "可优化",
      `${suggestion.chapterName} / ${suggestion.sceneName}`,
      suggestion.assetName,
      suggestion.startLabel,
      suggestion.endLabel,
      suggestion.detail,
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
    const voiceMixRows = toArray(sheet.voiceMixRows).slice(0, 120).map((row, index) => [
      `${index + 1}`,
      row.riskLabel,
      `${row.chapterName} / ${row.sceneName}`,
      row.assetName,
      `${row.startLabel} -> ${row.endLabel}`,
      `${row.voiceCount} 句`,
      row.speakerNames || "旁白",
      `${row.bgmVolume}% / ${row.effectiveBgmVolume}%`,
      `${row.averageVoiceVolume}%`,
      row.duckingLabel,
      row.reviewHint,
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
    const productionRows = toArray(sheet.productionQueue).slice(0, 120).map((task) => [
      `${task.rank}`,
      task.phase,
      task.cueType === "voice" ? "语音" : task.cueType === "sfx" ? "音效" : "BGM",
      task.title,
      task.targetLabel,
      task.actionLabel,
      task.detail,
    ]);
    const auditionRows = toArray(sheet.auditionChecklist).slice(0, 120).map((row) => [
      `${row.rank}`,
      row.priority,
      row.type,
      row.targetLabel,
      row.assetName,
      row.cueLabel,
      row.actionLabel,
      row.statusLabel,
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
          ["BGM 预计总时长", formatAudioSegmentDuration(summary.totalEstimatedMusicSeconds ?? 0)],
          ["偏短 / 偏长 / 空段", `${summary.shortMusicSegmentCount ?? 0} / ${summary.longMusicSegmentCount ?? 0} / ${summary.silentMusicSegmentCount ?? 0}`],
          ["指定范围", `${summary.explicitRangeCount ?? 0}`],
          ["范围建议", `${summary.rangeSuggestionCount ?? 0}`],
          ["场景结束范围", `${summary.sceneEndCount ?? 0}`],
          ["自然接管", `${summary.handoffCount ?? 0}`],
          ["建议试听", `${summary.auditionNeededCount ?? 0}`],
          ["停止音乐卡", `${summary.stopCount ?? 0}`],
          ["阻塞问题", `${summary.blockerCount ?? 0}`],
          ["复查提醒", `${summary.warningCount ?? 0}`],
          ["音效缺失", `${summary.missingSfxAssetCount ?? 0}`],
          ["语音缺失", `${summary.missingVoiceAssetCount ?? 0}`],
          ["人声混音段 / 风险", `${summary.voiceMusicSegmentCount ?? 0} / ${summary.voiceMixWarningCount ?? 0}`],
          ["无 BGM 内容场景", `${summary.scenesWithoutMusicCount ?? 0}`],
          ["制作任务", `${summary.productionTaskCount ?? 0}`],
          ["试听清单", `${summary.auditionChecklistCount ?? 0}`],
          ["发布就绪度", `${summary.releaseReadinessPercent ?? 0}%`],
        ]
      ),
      "",
      "## 制作优先队列",
      "",
      buildMarkdownTable(["序号", "阶段", "类型", "任务", "定位", "建议动作", "说明"], productionRows) ||
        "当前没有需要排队处理的音频制作任务。",
      "",
      "## 发布前试听清单",
      "",
      buildMarkdownTable(["序号", "优先级", "类型", "位置", "素材", "触发/范围", "试听动作", "状态"], auditionRows) ||
        "当前没有需要特别列出的试听项。",
      "",
      "## BGM 覆盖范围速览",
      "",
      buildMarkdownTable(["序号", "章节 / 场景", "BGM", "覆盖范围", "预计时长", "正文量", "接管方式", "试听提示", "状态"], rangeRows) ||
        "当前没有可展示的 BGM 覆盖范围。",
      "",
      "## 人声混音检查",
      "",
      buildMarkdownTable(
        ["序号", "状态", "章节 / 场景", "BGM", "覆盖范围", "语音数", "角色", "BGM 原始/语音时", "平均语音", "语音焦点", "试听建议"],
        voiceMixRows
      ) || "当前没有 BGM 与语音重叠的段落。",
      "",
      "## BGM 文本范围建议",
      "",
      buildMarkdownTable(["序号", "类型", "章节 / 场景", "BGM", "开始", "建议结束", "说明"], rangeSuggestionRows) ||
        "当前没有需要单独建议的 BGM 文本范围。",
      "",
      "## BGM Cue 列表",
      "",
      buildMarkdownTable(["序号", "章节", "场景", "BGM", "范围", "预计时长", "开始", "结束", "接管方式", "淡入/淡出", "状态"], cueRows) ||
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
      cue.durationLabel,
      cue.readableCharacterCount,
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
      "",
      "",
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
      "",
      "",
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
    const mixRows = toArray(sheet.voiceMixRows).map((row, index) => [
      "Mix",
      `${index + 1}`,
      row.chapterName,
      row.sceneName,
      "",
      row.assetName,
      row.assetId,
      row.duckingLabel,
      "",
      "",
      `${row.startLabel} -> ${row.endLabel}`,
      `${row.voiceCount} 句语音 / ${row.speakerNames || "旁白"}`,
      "",
      row.effectiveBgmVolume,
      "",
      "",
      "",
      row.reviewHint,
      row.riskLabel,
      row.risk === "good" ? "" : row.title,
    ]);
    const rows = [...musicRows, ...mixRows, ...sfxRows, ...voiceRows];
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
        "预计时长",
        "正文字符",
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
    AUDIO_CUE_AUTO_FIX_DEFAULTS,
    getSafeMusicEndMode,
    getMusicEndModeLabel,
    buildAudioCueRangeRows,
    buildSfxCueRows,
    buildVoiceCueRows,
    getProjectVoiceDuckingProfile,
    buildVoiceMusicMixRow,
    auditVoiceMusicMix,
    buildAudioRangeSuggestion,
    applyAudioRangeSuggestionToScene,
    buildAudioCueProductionQueue,
    buildAudioCueAuditionChecklist,
    buildAudioCueAutoFixSummary,
    buildAudioCueAutoFixPlan,
    getAudioCueAutoFixDigest,
    formatAudioSegmentDuration,
    buildAudioCueSheet,
    getAudioCueSheetStatusDigest,
    buildAudioCueSheetMarkdown,
    buildAudioCueSheetCsv,
  });
})(typeof window !== "undefined" ? window : globalThis);
