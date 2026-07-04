(function attachScreenplayExporterTools(global) {
  const TEXT_LINE_TYPES = new Set(["dialogue", "narration"]);
  const CHOICE_TYPES = new Set(["choice"]);
  const STAGE_DIRECTION_TYPES = new Set([
    "background",
    "character",
    "character_show",
    "character_hide",
    "music_play",
    "music_stop",
    "sfx_play",
    "video_play",
    "particle_effect",
    "wait",
    "jump",
    "condition",
    "variable_set",
    "variable_add",
  ]);

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function getBlockType(block = {}) {
    return cleanText(block.type, "unknown");
  }

  function getProjectTitle(data = {}, options = {}) {
    return cleanText(options.projectTitle ?? data.project?.title ?? data.title, "Canvasia Project");
  }

  function getAssetList(data = {}) {
    return Array.isArray(data.assetList)
      ? data.assetList
      : Array.isArray(data.assets?.assets)
        ? data.assets.assets
        : [];
  }

  function getCharacterList(data = {}) {
    return Array.isArray(data.characters)
      ? data.characters
      : Array.isArray(data.characters?.characters)
        ? data.characters.characters
        : [];
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

  function buildChapterMap(data = {}) {
    const chapterMap = new Map();
    toArray(data.chapters).forEach((chapter, index) => {
      const chapterId = cleanText(chapter?.id ?? chapter?.chapterId, `chapter_${index + 1}`);
      chapterMap.set(chapterId, {
        id: chapterId,
        name: cleanText(chapter?.name ?? chapter?.title, `章节 ${index + 1}`),
        order: index,
        sceneOrder: toArray(chapter?.sceneOrder).map((sceneId) => cleanText(sceneId)).filter(Boolean),
      });
    });
    return chapterMap;
  }

  function getSceneRecords(data = {}) {
    const sceneMap = buildSceneMap(data);
    const chapterMap = buildChapterMap(data);
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
      const chapter = chapterMap.get(cleanText(scene.chapterId));
      seenSceneIds.add(sceneId);
      records.push({
        scene,
        sceneIndex,
        chapterId: chapter?.id ?? cleanText(scene.chapterId),
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

  function formatMs(value) {
    const ms = Number(value ?? 0);
    return Number.isFinite(ms) && ms > 0 ? `${ms}ms` : "";
  }

  function formatSeconds(value) {
    const seconds = Number(value ?? 0);
    return Number.isFinite(seconds) && seconds > 0 ? `${seconds}s` : "";
  }

  function joinParts(parts, separator = "，") {
    return parts.map((part) => cleanText(part)).filter(Boolean).join(separator);
  }

  function buildChoiceText(block = {}, sceneMap = new Map()) {
    const options = toArray(block.options);
    if (!options.length) {
      return "选项：暂未配置选项";
    }
    return options
      .map((option, index) => {
        const optionText = cleanText(option?.text ?? option?.label, `选项 ${index + 1}`);
        const target = getSceneTargetLabel(sceneMap, option?.targetSceneId ?? option?.target);
        return `${index + 1}. ${optionText} -> ${target}`;
      })
      .join(" / ");
  }

  function buildConditionText(block = {}, sceneMap = new Map()) {
    const branches = toArray(block.branches);
    if (!branches.length) {
      return "条件分支：暂未配置判断分支";
    }
    return branches
      .map((branch, index) => {
        const condition = cleanText(branch?.condition ?? branch?.label, index === 0 ? "如果" : "否则");
        const target = getSceneTargetLabel(sceneMap, branch?.targetSceneId ?? branch?.target);
        return `${condition} -> ${target}`;
      })
      .join(" / ");
  }

  function buildStageDirectionText(block = {}, context = {}) {
    const type = getBlockType(block);
    const assetMap = context.assetMap ?? new Map();
    const characterMap = context.characterMap ?? new Map();
    const sceneMap = context.sceneMap ?? new Map();

    if (type === "background") {
      return joinParts([
        `切换背景：${getAssetName(assetMap, block.assetId, "未选择背景")}`,
        block.transition ? `转场 ${block.transition}` : "",
        formatMs(block.durationMs ?? block.transitionDurationMs),
      ]);
    }
    if (type === "character" || type === "character_show") {
      return joinParts([
        `显示立绘：${getCharacterName(characterMap, block.characterId, "未选择角色")}`,
        block.expressionId ? `表情 ${block.expressionId}` : "",
        block.position ? `位置 ${block.position}` : "",
        block.scale ? `缩放 ${block.scale}` : "",
        block.transition ? `转场 ${block.transition}` : "",
      ]);
    }
    if (type === "character_hide") {
      return joinParts([
        `隐藏立绘：${getCharacterName(characterMap, block.characterId, "未选择角色")}`,
        block.transition ? `转场 ${block.transition}` : "",
      ]);
    }
    if (type === "music_play") {
      return joinParts([
        `播放 BGM：${getAssetName(assetMap, block.assetId, "未选择音乐")}`,
        block.fadeInMs ? `淡入 ${formatMs(block.fadeInMs)}` : "",
        block.volume ? `音量 ${block.volume}` : "",
      ]);
    }
    if (type === "music_stop") {
      return joinParts([`停止 BGM`, block.fadeOutMs ? `淡出 ${formatMs(block.fadeOutMs)}` : ""]);
    }
    if (type === "sfx_play") {
      return joinParts([
        `播放音效：${getAssetName(assetMap, block.assetId, "未选择音效")}`,
        block.volume ? `音量 ${block.volume}` : "",
      ]);
    }
    if (type === "video_play") {
      return joinParts([
        `播放视频：${getAssetName(assetMap, block.assetId, "未选择视频")}`,
        block.skippable === false ? "不可跳过" : "可跳过",
      ]);
    }
    if (type === "particle_effect") {
      return joinParts([
        `粒子效果：${cleanText(block.preset ?? block.effectId, "自定义粒子")}`,
        block.intensity ? `强度 ${block.intensity}` : "",
      ]);
    }
    if (type === "wait") {
      return `等待：${formatSeconds(block.durationSeconds) || formatMs(block.durationMs) || "未设置时长"}`;
    }
    if (type === "jump") {
      return `跳转：${getSceneTargetLabel(sceneMap, block.targetSceneId ?? block.target)}`;
    }
    if (type === "condition") {
      return buildConditionText(block, sceneMap);
    }
    if (type === "variable_set") {
      return `设置变量：${cleanText(block.variableId, "未选择变量")} = ${cleanText(block.value, "空值")}`;
    }
    if (type === "variable_add") {
      return `调整变量：${cleanText(block.variableId, "未选择变量")} + ${cleanText(block.value ?? block.delta, "0")}`;
    }
    return cleanText(block.text ?? block.note ?? block.label, `演出指令：${type}`);
  }

  function getLineKindLabel(kind) {
    if (kind === "dialogue") {
      return "台词";
    }
    if (kind === "narration") {
      return "旁白";
    }
    if (kind === "choice") {
      return "选项";
    }
    if (kind === "stage") {
      return "演出";
    }
    return "其他";
  }

  function createEntry(record, block, blockIndex, order, context) {
    const type = getBlockType(block);
    const assetMap = context.assetMap ?? new Map();
    const characterMap = context.characterMap ?? new Map();
    const sceneMap = context.sceneMap ?? new Map();
    const sceneId = cleanText(record.scene?.id);
    const speakerId = cleanText(block.speakerId);
    let kind = "stage";
    let text = "";
    let speakerName = "";
    let targetLabel = "";
    let assetId = cleanText(block.assetId ?? block.voiceAssetId ?? block.voice?.assetId);
    let assetName = getAssetName(assetMap, assetId);
    let note = "";

    if (TEXT_LINE_TYPES.has(type)) {
      kind = type;
      text = cleanText(block.text, type === "dialogue" ? "（空台词）" : "（空旁白）");
      speakerName = type === "dialogue" ? getCharacterName(characterMap, speakerId, "未指定说话人") : "旁白";
      assetId = cleanText(block.voiceAssetId ?? block.voice?.assetId);
      assetName = getAssetName(assetMap, assetId);
      note = type === "dialogue" ? (assetId ? `语音：${assetName || assetId}` : "待绑定语音") : "";
    } else if (CHOICE_TYPES.has(type)) {
      kind = "choice";
      text = buildChoiceText(block, sceneMap);
      targetLabel = toArray(block.options)
        .map((option) => getSceneTargetLabel(sceneMap, option?.targetSceneId ?? option?.target))
        .join(" / ");
      note = `${toArray(block.options).length} 个选项`;
    } else if (STAGE_DIRECTION_TYPES.has(type)) {
      kind = "stage";
      text = buildStageDirectionText(block, context);
      targetLabel =
        type === "jump"
          ? getSceneTargetLabel(sceneMap, block.targetSceneId ?? block.target)
          : type === "condition"
            ? toArray(block.branches)
                .map((branch) => getSceneTargetLabel(sceneMap, branch?.targetSceneId ?? branch?.target))
                .join(" / ")
            : "";
    } else {
      kind = "stage";
      text = buildStageDirectionText(block, context);
      note = "暂未归类的卡片类型";
    }

    return {
      order,
      chapterId: cleanText(record.chapterId),
      chapterName: cleanText(record.chapterName, "未分章"),
      sceneId,
      sceneName: cleanText(record.scene?.name ?? record.scene?.title, sceneId || "未命名场景"),
      blockId: cleanText(block.id, `block_${blockIndex + 1}`),
      blockIndex,
      blockType: type,
      kind,
      kindLabel: getLineKindLabel(kind),
      speakerId,
      speakerName,
      text,
      textLength: text.length,
      assetId,
      assetName,
      targetLabel,
      note,
      needsVoice: kind === "dialogue",
      hasVoice: kind === "dialogue" && Boolean(assetId),
    };
  }

  function summarizeEntries(entries = [], sceneRecords = []) {
    const dialogueCount = entries.filter((entry) => entry.kind === "dialogue").length;
    const narrationCount = entries.filter((entry) => entry.kind === "narration").length;
    const choiceCount = entries.filter((entry) => entry.kind === "choice").length;
    const stageDirectionCount = entries.filter((entry) => entry.kind === "stage").length;
    const voiceLineCount = entries.filter((entry) => entry.needsVoice).length;
    const missingVoiceCount = entries.filter((entry) => entry.needsVoice && !entry.hasVoice).length;
    const characterIds = new Set(entries.map((entry) => entry.speakerId).filter(Boolean));
    const chapterIds = new Set(sceneRecords.map((record) => cleanText(record.chapterId)).filter(Boolean));
    return {
      chapterCount: chapterIds.size,
      sceneCount: sceneRecords.length,
      blockCount: entries.length,
      lineCount: dialogueCount + narrationCount,
      dialogueCount,
      narrationCount,
      choiceCount,
      stageDirectionCount,
      voiceLineCount,
      missingVoiceCount,
      characterCount: characterIds.size,
      textLength: entries.reduce((sum, entry) => sum + (entry.textLength ?? 0), 0),
    };
  }

  function buildChapterSections(entries = []) {
    const chapterMap = new Map();
    entries.forEach((entry) => {
      const chapterId = entry.chapterId || "unassigned";
      if (!chapterMap.has(chapterId)) {
        chapterMap.set(chapterId, {
          id: chapterId,
          name: entry.chapterName,
          scenes: [],
          sceneMap: new Map(),
        });
      }
      const chapter = chapterMap.get(chapterId);
      const sceneId = entry.sceneId || `scene_${chapter.scenes.length + 1}`;
      if (!chapter.sceneMap.has(sceneId)) {
        const scene = { id: sceneId, name: entry.sceneName, entries: [] };
        chapter.sceneMap.set(sceneId, scene);
        chapter.scenes.push(scene);
      }
      chapter.sceneMap.get(sceneId).entries.push(entry);
    });
    return Array.from(chapterMap.values()).map((chapter) => ({
      id: chapter.id,
      name: chapter.name,
      scenes: chapter.scenes,
    }));
  }

  function buildScreenplayExport(data = {}, options = {}) {
    const assetMap = buildAssetMap(data);
    const characterMap = buildCharacterMap(data);
    const sceneMap = buildSceneMap(data);
    const sceneRecords = getSceneRecords(data);
    const context = { assetMap, characterMap, sceneMap };
    const entries = [];
    let order = 1;

    sceneRecords.forEach((record) => {
      toArray(record.scene?.blocks).forEach((block, blockIndex) => {
        entries.push(createEntry(record, block, blockIndex, order, context));
        order += 1;
      });
    });

    const summary = summarizeEntries(entries, sceneRecords);
    return {
      formatVersion: 1,
      projectTitle: getProjectTitle(data, options),
      summary,
      entries,
      chapters: buildChapterSections(entries),
    };
  }

  function getScreenplayStatusDigest(screenplay = {}) {
    const summary = screenplay.summary ?? {};
    if (!summary.blockCount) {
      return {
        status: "empty",
        title: "还没有剧本内容",
        detail: "添加章节、场景、台词或演出指令后，就能导出完整剧本台本。",
      };
    }
    if ((summary.missingVoiceCount ?? 0) > 0) {
      return {
        status: "review",
        title: "可导出，语音待补",
        detail: `已整理 ${summary.blockCount} 张剧情卡，其中 ${summary.missingVoiceCount} 句台词还没有绑定语音。`,
      };
    }
    return {
      status: "ready",
      title: "剧本台本已就绪",
      detail: `已整理 ${summary.sceneCount ?? 0} 个场景、${summary.lineCount ?? 0} 行正文和 ${summary.stageDirectionCount ?? 0} 条演出指令。`,
    };
  }

  function escapeMarkdownTableCell(value) {
    return String(value ?? "")
      .replace(/\|/g, "\\|")
      .replace(/\r?\n/g, "<br />")
      .trim();
  }

  function buildMarkdownTable(headers, rows) {
    if (!rows.length) {
      return "";
    }
    return [
      `| ${headers.map(escapeMarkdownTableCell).join(" | ")} |`,
      `| ${headers.map(() => "---").join(" | ")} |`,
      ...rows.map((row) => `| ${row.map(escapeMarkdownTableCell).join(" | ")} |`),
    ].join("\n");
  }

  function formatEntryMarkdownLine(entry = {}) {
    if (entry.kind === "dialogue") {
      const voiceSuffix = entry.assetName ? ` （语音：${entry.assetName}）` : " （待绑定语音）";
      return `- ${entry.speakerName || "未指定说话人"}：${entry.text}${voiceSuffix}`;
    }
    if (entry.kind === "narration") {
      return `- [旁白] ${entry.text}`;
    }
    if (entry.kind === "choice") {
      return `- [选项] ${entry.text}`;
    }
    return `- [演出] ${entry.text}`;
  }

  function buildScreenplayMarkdown(screenplay = {}, options = {}) {
    const projectTitle = cleanText(options.projectTitle ?? screenplay.projectTitle, "Canvasia Project");
    const generatedAt = cleanText(options.generatedAt);
    const summary = screenplay.summary ?? {};
    const digest = getScreenplayStatusDigest(screenplay);
    const overviewRows = [
      ["章节", summary.chapterCount ?? 0],
      ["场景", summary.sceneCount ?? 0],
      ["剧情卡", summary.blockCount ?? 0],
      ["正文行", summary.lineCount ?? 0],
      ["台词", summary.dialogueCount ?? 0],
      ["旁白", summary.narrationCount ?? 0],
      ["选项", summary.choiceCount ?? 0],
      ["演出指令", summary.stageDirectionCount ?? 0],
      ["待绑定语音", summary.missingVoiceCount ?? 0],
    ];
    const lines = [
      `# ${projectTitle} 剧本台本`,
      "",
      generatedAt ? `生成时间：${generatedAt}` : "",
      "",
      `状态：${digest.title}`,
      "",
      digest.detail,
      "",
      "## 总览",
      "",
      buildMarkdownTable(["项目", "数量"], overviewRows),
      "",
      "## 正文与演出",
      "",
    ];

    if (!toArray(screenplay.chapters).length) {
      lines.push("当前还没有可导出的剧本内容。");
      return `\uFEFF${lines.join("\n")}\n`;
    }

    toArray(screenplay.chapters).forEach((chapter) => {
      lines.push(`### ${chapter.name}`);
      lines.push("");
      toArray(chapter.scenes).forEach((scene) => {
        lines.push(`#### 场景：${scene.name}`);
        lines.push("");
        toArray(scene.entries).forEach((entry) => {
          lines.push(formatEntryMarkdownLine(entry));
        });
        lines.push("");
      });
    });

    return `\uFEFF${lines.join("\n")}\n`;
  }

  function formatCsvCell(value) {
    return `"${String(value ?? "").replace(/"/g, '""')}"`;
  }

  function buildCsv(headers, rows) {
    return [headers, ...rows].map((row) => row.map(formatCsvCell).join(",")).join("\n");
  }

  function buildScreenplayCsv(screenplay = {}) {
    const rows = toArray(screenplay.entries).map((entry) => [
      screenplay.projectTitle,
      entry.order,
      entry.chapterName,
      entry.sceneName,
      entry.blockIndex + 1,
      entry.kindLabel,
      entry.blockType,
      entry.speakerName,
      entry.text,
      entry.assetName,
      entry.targetLabel,
      entry.note,
    ]);
    return `\uFEFF${buildCsv(
      ["项目", "序号", "章节", "场景", "卡片序号", "分类", "卡片类型", "角色/声部", "内容", "关联素材", "目标场景", "备注"],
      rows
    )}\n`;
  }

  global.CanvasiaEditorScreenplayExporter = Object.freeze({
    TEXT_LINE_TYPES,
    CHOICE_TYPES,
    STAGE_DIRECTION_TYPES,
    buildScreenplayExport,
    getScreenplayStatusDigest,
    buildScreenplayMarkdown,
    buildScreenplayCsv,
    buildStageDirectionText,
    buildChoiceText,
  });
})(typeof window !== "undefined" ? window : globalThis);
