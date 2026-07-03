(function attachAudioCueSheetTools(global) {
  const BLOCK_LABELS = Object.freeze({
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
    choice: "选项",
    jump: "跳转",
    condition: "条件",
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
    return ["background", "dialogue", "narration", "character_show", "choice", "video_play", "credits_roll"].includes(
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
    let plannedEndIndex = blocks.length - 1;
    let endBlock = null;
    let endLabel = "场景末尾";

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
      spanCount: Math.max(1, plannedEndIndex - startIndex + 1),
    };
  }

  function buildAudioCue(block = {}, context = {}) {
    const issues = [];
    const assetId = cleanText(block.assetId);
    const asset = assetId ? context.assetMap.get(assetId) : null;
    const startIndex = context.blockIndex ?? 0;
    const endInfo = getAudioControlEndIndex(block, context.blocks, startIndex, issues);
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
      issues,
    };
    cue.status = issues.some((issue) => issue.severity === "blocker")
      ? "blocker"
      : issues.some((issue) => issue.severity === "warn")
        ? "warn"
        : issues.length > 0
          ? "tip"
          : "good";
    cue.statusLabel = cue.status === "blocker" ? "需先修" : cue.status === "warn" ? "建议复查" : cue.status === "tip" ? "可润色" : "正常";
    return cue;
  }

  function buildAudioCueSheet(data = {}) {
    const assetMap = buildAssetMap(data);
    const chapterMap = buildChapterMap(data);
    const scenes = getOrderedScenes(data);
    const cues = [];
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

      blocks.forEach((block, blockIndex) => {
        if (block?.type === "music_play") {
          const cue = buildAudioCue(block, { assetMap, blocks, blockIndex, scene, sceneIndex, chapter });
          cues.push(cue);
          sceneCues.push(cue);
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

      if (hasStoryContent && sceneCues.length === 0) {
        scenesWithoutMusic.push({
          sceneId: cleanText(scene?.id),
          sceneName: cleanText(scene?.name ?? scene?.title, `场景 ${sceneIndex + 1}`),
          chapterName: chapter.name,
          blockCount: blocks.length,
        });
      }
    });

    const issues = cues
      .flatMap((cue) =>
        cue.issues.map((issue) => ({
          ...issue,
          cueId: cue.id,
          chapterName: cue.chapterName,
          sceneName: cue.sceneName,
          assetName: cue.assetName,
          startLabel: cue.startLabel,
        }))
      )
      .sort((left, right) => getIssueWeight(right) - getIssueWeight(left) || left.sceneName.localeCompare(right.sceneName, "zh-CN"));

    const summary = {
      cueCount: cues.length,
      explicitRangeCount: cues.filter((cue) => cue.endMode === "after_block").length,
      sceneEndCount: cues.filter((cue) => cue.endMode === "scene_end").length,
      takeoverCount: cues.filter((cue) => cue.issues.some((issue) => issue.code.includes("taken_over"))).length,
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
      stops,
      scenesWithoutMusic,
      issues,
      summary,
    };
  }

  function getAudioCueSheetStatusDigest(sheet = {}) {
    const summary = sheet.summary ?? {};
    if ((summary.cueCount ?? 0) === 0) {
      return {
        status: "empty",
        tone: "soft",
        title: "还没有 BGM 调度",
        detail: "项目里暂时没有播放音乐卡。可以先给入口场景加一首 BGM，再逐步做范围。",
      };
    }
    if ((summary.blockerCount ?? 0) > 0) {
      return {
        status: "blocked",
        tone: "danger",
        title: `有 ${summary.blockerCount} 个 BGM 阻塞问题`,
        detail: "优先修复缺素材、坏范围或真实文件缺失，再做发布前试听。",
      };
    }
    if ((summary.warningCount ?? 0) > 0) {
      return {
        status: "warn",
        tone: "warn",
        title: `有 ${summary.warningCount} 个 BGM 调度提醒`,
        detail: "音乐能继续推进，但建议复查被提前接管或范围不清晰的位置。",
      };
    }
    return {
      status: "ready",
      tone: "good",
      title: "BGM 调度表可用于发布前试听",
      detail: "当前音乐卡都有明确素材和可解释的播放范围。",
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
      `${cue.fadeInMs} / ${cue.fadeOutMs} ms`,
      cue.statusLabel,
    ]);
    const issueRows = toArray(sheet.issues).slice(0, 120).map((issue, index) => [
      `${index + 1}`,
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
      `# ${projectTitle} BGM 调度表`,
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
          ["指定范围", `${summary.explicitRangeCount ?? 0}`],
          ["场景结束范围", `${summary.sceneEndCount ?? 0}`],
          ["停止音乐卡", `${summary.stopCount ?? 0}`],
          ["阻塞问题", `${summary.blockerCount ?? 0}`],
          ["复查提醒", `${summary.warningCount ?? 0}`],
          ["无 BGM 内容场景", `${summary.scenesWithoutMusicCount ?? 0}`],
        ]
      ),
      "",
      "## BGM Cue 列表",
      "",
      buildMarkdownTable(["序号", "章节", "场景", "BGM", "范围", "开始", "结束", "淡入/淡出", "状态"], cueRows) ||
        "当前没有播放音乐卡。",
      "",
      "## 需要复查的问题",
      "",
      buildMarkdownTable(["序号", "级别", "章节", "场景", "问题", "说明"], issueRows) || "当前没有明显 BGM 调度问题。",
      "",
      "## 暂无 BGM 的内容场景",
      "",
      buildMarkdownTable(["序号", "章节", "场景", "卡片数"], sceneRows) || "当前没有需要提示的无 BGM 内容场景。",
      "",
    ].join("\n")}`;
  }

  function buildAudioCueSheetCsv(sheet = {}) {
    const rows = toArray(sheet.cues).map((cue, index) => [
      `${index + 1}`,
      cue.chapterName,
      cue.sceneName,
      cue.blockIndex + 1,
      cue.assetName,
      cue.assetId,
      cue.endModeLabel,
      cue.endLabel,
      cue.spanCount,
      cue.volume,
      cue.loop ? "循环" : "不循环",
      cue.fadeInMs,
      cue.fadeOutMs,
      cue.statusLabel,
      cue.issues.map((issue) => issue.title).join(" / "),
    ]);
    return `\uFEFF${buildCsv(
      ["序号", "章节", "场景", "开始卡片", "BGM", "素材ID", "范围", "结束位置", "覆盖卡片", "音量", "循环", "淡入ms", "淡出ms", "状态", "问题"],
      rows
    )}\n`;
  }

  global.CanvasiaEditorAudioCueSheet = Object.freeze({
    getSafeMusicEndMode,
    getMusicEndModeLabel,
    buildAudioCueSheet,
    getAudioCueSheetStatusDigest,
    buildAudioCueSheetMarkdown,
    buildAudioCueSheetCsv,
  });
})(typeof window !== "undefined" ? window : globalThis);
