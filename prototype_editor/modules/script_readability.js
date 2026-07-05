(function attachScriptReadabilityTools(global) {
  const VN_TEXT_LONG_WARNING_LENGTH = 260;
  const VN_TEXT_LONG_WARNING_LINES = 5;
  const VN_TEXT_SPLIT_TARGET_LENGTH = 180;
  const VN_CHOICE_LONG_WARNING_LENGTH = 42;
  const VN_CHOICE_MANY_OPTIONS = 6;

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function getEscapeHtml(options = {}) {
    return typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtml;
  }

  function getReadableTextMetrics(text) {
    const safeText = String(text ?? "").trim();
    return {
      length: safeText.length,
      lineCount: safeText ? safeText.split(/\r?\n/).length : 0,
    };
  }

  function buildReadableTextSummary(metrics) {
    const safeMetrics =
      metrics && typeof metrics === "object"
        ? metrics
        : {
            length: 0,
            lineCount: 0,
          };
    return `当前 ${safeMetrics.length} 字 / ${safeMetrics.lineCount} 行，超过 ${VN_TEXT_SPLIT_TARGET_LENGTH} 字会启用拆分；超过 ${VN_TEXT_LONG_WARNING_LENGTH} 字或 ${VN_TEXT_LONG_WARNING_LINES} 行时建议拆卡。`;
  }

  function getChoiceTextQualityState(text) {
    const length = String(text ?? "").trim().length;
    const isLong = length > VN_CHOICE_LONG_WARNING_LENGTH;

    return {
      length,
      isLong,
      statusText: isLong ? "文案偏长" : "按钮舒适",
      toneClass: isLong ? "warn-text" : "good-text",
    };
  }

  function buildChoiceTextSummary(length) {
    return `当前 ${length} 字，建议不超过 ${VN_CHOICE_LONG_WARNING_LENGTH} 字；解释性内容最好放到前一句台词或旁白里。`;
  }

  function renderChoiceTextQualityTools(text, options = {}) {
    const escape = getEscapeHtml(options);
    const toolState = getChoiceTextQualityState(text);

    return `
      <div class="choice-text-tools ${toolState.isLong ? "is-warning" : ""}" data-choice-text-tools>
        <span class="helper-text" data-choice-text-summary>${escape(buildChoiceTextSummary(toolState.length))}</span>
        <span class="issue-tag ${toolState.toneClass}" data-choice-text-status>${toolState.statusText}</span>
      </div>
    `;
  }

  function buildChoiceCountSummary(optionCount) {
    return `当前 ${optionCount} 个选项，超过 ${VN_CHOICE_MANY_OPTIONS} 个时按钮区可能拥挤；复杂分支建议拆成二级选择。`;
  }

  function isReadableTextLong(text) {
    const metrics = getReadableTextMetrics(text);
    return metrics.length > VN_TEXT_LONG_WARNING_LENGTH || metrics.lineCount > VN_TEXT_LONG_WARNING_LINES;
  }

  function findReadableSplitIndex(text, limit) {
    const safeLimit = Math.max(1, Number(limit) || VN_TEXT_SPLIT_TARGET_LENGTH);
    const searchWindow = String(text ?? "").slice(0, safeLimit + 1);
    const minUsefulIndex = Math.floor(safeLimit * 0.45);
    const punctuationPattern = /[。！？!?；;，,、：:]/g;
    let match = null;
    let splitIndex = -1;

    while ((match = punctuationPattern.exec(searchWindow)) !== null) {
      const candidateIndex = match.index + 1;
      if (candidateIndex >= minUsefulIndex) {
        splitIndex = candidateIndex;
      }
    }

    if (splitIndex > 0) {
      return splitIndex;
    }

    const spaceIndex = searchWindow.lastIndexOf(" ");
    if (spaceIndex >= minUsefulIndex) {
      return spaceIndex + 1;
    }

    return safeLimit;
  }

  function splitLongReadableSegment(segment, limit) {
    const chunks = [];
    let remaining = String(segment ?? "").trim();

    while (remaining.length > limit) {
      const splitIndex = findReadableSplitIndex(remaining, limit);
      const head = remaining.slice(0, splitIndex).trim();
      if (head) {
        chunks.push(head);
      }
      remaining = remaining.slice(splitIndex).trim();
    }

    if (remaining) {
      chunks.push(remaining);
    }

    return chunks;
  }

  function shouldJoinReadableSegmentsWithSpace(left, right) {
    return /[A-Za-z0-9)]$/.test(left) && /^[A-Za-z0-9(]/.test(right);
  }

  function splitReadableTextIntoChunks(text, limit = VN_TEXT_SPLIT_TARGET_LENGTH) {
    const safeLimit = Math.max(20, Number(limit) || VN_TEXT_SPLIT_TARGET_LENGTH);
    const normalizedText = String(text ?? "").replace(/\r\n/g, "\n").trim();
    if (!normalizedText) {
      return [];
    }

    const rawSegments = normalizedText
      .split(/\n+/)
      .flatMap((line) => line.match(/[^。！？!?；;…]+[。！？!?；;…]*/g) ?? [line])
      .map((segment) => segment.trim())
      .filter(Boolean);
    const sentenceSegments = rawSegments.flatMap((segment) =>
      segment.length > safeLimit ? splitLongReadableSegment(segment, safeLimit) : [segment]
    );
    const chunks = [];
    let currentChunk = "";

    sentenceSegments.forEach((segment) => {
      if (!currentChunk) {
        currentChunk = segment;
        return;
      }

      const separator = shouldJoinReadableSegmentsWithSpace(currentChunk, segment) ? " " : "";
      const merged = `${currentChunk}${separator}${segment}`;
      if (merged.length <= safeLimit) {
        currentChunk = merged;
        return;
      }

      chunks.push(currentChunk);
      currentChunk = segment;
    });

    if (currentChunk) {
      chunks.push(currentChunk);
    }

    return chunks;
  }

  function cloneReadableValue(value) {
    return JSON.parse(JSON.stringify(value ?? null));
  }

  function toReadableArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function normalizeReadableSceneBlocks(sceneOrBlocks) {
    if (Array.isArray(sceneOrBlocks)) {
      return sceneOrBlocks;
    }

    return Array.isArray(sceneOrBlocks?.blocks) ? sceneOrBlocks.blocks : [];
  }

  function cleanReadableText(value, fallback = "") {
    const text = String(value ?? "").trim();
    return text || fallback;
  }

  function addReadableSceneToLookup(lookup, scene, fallbackId = "") {
    const sceneId = cleanReadableText(scene?.id, cleanReadableText(fallbackId));
    if (sceneId && !lookup.has(sceneId)) {
      lookup.set(sceneId, scene);
    }
  }

  function buildReadableSceneLookup(data = {}) {
    const lookup = new Map();
    if (data.scenesById && typeof data.scenesById.forEach === "function") {
      data.scenesById.forEach((scene, id) => addReadableSceneToLookup(lookup, scene, id));
    } else if (data.scenesById && typeof data.scenesById === "object") {
      Object.entries(data.scenesById).forEach(([id, scene]) => addReadableSceneToLookup(lookup, scene, id));
    }
    toReadableArray(data.scenes).forEach((scene) => addReadableSceneToLookup(lookup, scene));
    toReadableArray(data.chapters).forEach((chapter) => {
      toReadableArray(chapter.scenes).forEach((scene) => addReadableSceneToLookup(lookup, scene));
    });
    return lookup;
  }

  function getReadableSceneFromLookup(lookup, sceneId) {
    const safeId = cleanReadableText(sceneId);
    return safeId ? lookup.get(safeId) ?? null : null;
  }

  function getProjectReadableSceneList(data = {}) {
    const lookup = buildReadableSceneLookup(data);
    const scenes = [];
    const seen = new Set();
    const pushScene = (scene, chapter = {}) => {
      const sceneId = cleanReadableText(scene?.id);
      if (!sceneId || seen.has(sceneId)) {
        return;
      }
      seen.add(sceneId);
      scenes.push({
        ...(scene ?? {}),
        id: sceneId,
        chapterId: cleanReadableText(scene?.chapterId) || cleanReadableText(chapter.chapterId ?? chapter.id),
        chapterName: cleanReadableText(scene?.chapterName) || cleanReadableText(chapter.name ?? chapter.title),
      });
    };

    toReadableArray(data.chapters).forEach((chapter) => {
      const sceneIds = toReadableArray(chapter.sceneOrder).map((sceneId) => cleanReadableText(sceneId)).filter(Boolean);
      if (sceneIds.length) {
        sceneIds.forEach((sceneId) => pushScene(getReadableSceneFromLookup(lookup, sceneId), chapter));
        return;
      }
      toReadableArray(chapter.scenes).forEach((scene) => pushScene(scene, chapter));
    });

    toReadableArray(data.scenes).forEach((scene) => pushScene(scene));
    if (data.scenesById && typeof data.scenesById.forEach === "function") {
      data.scenesById.forEach((scene) => pushScene(scene));
    }
    return scenes;
  }

  function isReadableTextBlock(block) {
    return block?.type === "dialogue" || block?.type === "narration";
  }

  function createReadableBlockIdAllocator(sceneOrBlocks = []) {
    const existing = new Set(
      normalizeReadableSceneBlocks(sceneOrBlocks)
        .map((block) => String(block?.id ?? "").trim())
        .filter(Boolean)
    );
    let number = 1;

    return () => {
      let blockId = "";
      do {
        blockId = `block_${String(number).padStart(3, "0")}`;
        number += 1;
      } while (existing.has(blockId));
      existing.add(blockId);
      return blockId;
    };
  }

  function clearReadableSplitVoiceBinding(block) {
    delete block.voiceAssetId;
    delete block.voiceVolume;
    delete block.voice;
    return block;
  }

  function buildReadableBlockSplitPlan(block, options = {}) {
    const safeBlock = block && typeof block === "object" ? block : null;
    if (!isReadableTextBlock(safeBlock)) {
      return {
        canSplit: false,
        reason: "unsupported_block",
        originalBlockId: String(safeBlock?.id ?? ""),
        chunkCount: 0,
        chunks: [],
        blocks: [],
      };
    }

    const chunks = splitReadableTextIntoChunks(safeBlock.text, options.limit);
    if (chunks.length < 2) {
      return {
        canSplit: false,
        reason: "short_text",
        originalBlockId: String(safeBlock.id ?? ""),
        chunkCount: chunks.length,
        chunks,
        blocks: [],
      };
    }

    const allocateBlockId =
      typeof options.allocateBlockId === "function"
        ? options.allocateBlockId
        : createReadableBlockIdAllocator(options.scene ?? options.blocks ?? []);
    const splitBlocks = chunks.map((chunk, index) => {
      const nextBlock = cloneReadableValue(safeBlock) ?? {};
      nextBlock.id = index === 0 ? safeBlock.id : allocateBlockId();
      nextBlock.text = chunk;

      if (index > 0) {
        clearReadableSplitVoiceBinding(nextBlock);
      }

      return nextBlock;
    });

    return {
      canSplit: true,
      reason: "split",
      originalBlockId: String(safeBlock.id ?? ""),
      firstBlockId: String(splitBlocks[0]?.id ?? ""),
      chunkCount: splitBlocks.length,
      chunks,
      blocks: splitBlocks,
    };
  }

  function buildReadableSceneSplitPlan(scene, options = {}) {
    const sourceBlocks = normalizeReadableSceneBlocks(scene);
    const nextScene = cloneReadableValue(scene) ?? {};
    const allocateBlockId = createReadableBlockIdAllocator(sourceBlocks);
    const splitEntries = [];
    const nextBlocks = [];

    sourceBlocks.forEach((block, index) => {
      const plan = buildReadableBlockSplitPlan(block, {
        ...options,
        allocateBlockId,
      });

      if (!plan.canSplit) {
        nextBlocks.push(cloneReadableValue(block));
        return;
      }

      nextBlocks.push(...plan.blocks);
      splitEntries.push({
        blockId: plan.originalBlockId,
        firstBlockId: plan.firstBlockId,
        index,
        chunkCount: plan.chunkCount,
        addedBlockCount: Math.max(0, plan.chunkCount - 1),
      });
    });

    nextScene.blocks = nextBlocks;

    return {
      changed: splitEntries.length > 0,
      scene: nextScene,
      splitEntries,
      splitCount: splitEntries.length,
      addedBlockCount: nextBlocks.length - sourceBlocks.length,
      firstSplitBlockId: splitEntries[0]?.firstBlockId ?? "",
      firstSplitIndex: splitEntries[0]?.index ?? -1,
    };
  }

  function buildReadableProjectSplitSummary(scenePlans = []) {
    const safePlans = toReadableArray(scenePlans);
    const splitCount = safePlans.reduce((total, plan) => total + (plan.splitCount ?? 0), 0);
    const addedBlockCount = safePlans.reduce((total, plan) => total + (plan.addedBlockCount ?? 0), 0);
    if (!safePlans.length) {
      return "全项目台词和旁白长度已经比较舒适";
    }
    return `已准备整理 ${safePlans.length} 个场景、${splitCount} 张长文本，预计新增 ${addedBlockCount} 张卡片`;
  }

  function buildReadableProjectSplitPlan(data = {}, options = {}) {
    const scenePlans = getProjectReadableSceneList(data)
      .map((scene) => {
        const plan = buildReadableSceneSplitPlan(scene, options);
        return plan.changed
          ? {
              ...plan,
              sceneId: cleanReadableText(scene.id),
              sceneName: cleanReadableText(scene.name ?? scene.title, scene.id),
              chapterId: cleanReadableText(scene.chapterId),
              chapterName: cleanReadableText(scene.chapterName),
            }
          : null;
      })
      .filter(Boolean);

    return {
      changed: scenePlans.length > 0,
      scenePlans,
      changedSceneCount: scenePlans.length,
      splitCount: scenePlans.reduce((total, plan) => total + (plan.splitCount ?? 0), 0),
      addedBlockCount: scenePlans.reduce((total, plan) => total + (plan.addedBlockCount ?? 0), 0),
      firstChangedSceneId: scenePlans[0]?.sceneId ?? "",
      firstSplitBlockId: scenePlans[0]?.firstSplitBlockId ?? "",
      firstSplitIndex: scenePlans[0]?.firstSplitIndex ?? -1,
      summary: buildReadableProjectSplitSummary(scenePlans),
    };
  }

  function getReadableProjectSplitDigest(data = {}, options = {}) {
    const plan = buildReadableProjectSplitPlan(data, options);
    const previewNames = plan.scenePlans
      .slice(0, Math.max(1, Number(options.sceneNameLimit) || 3))
      .map((scenePlan) => scenePlan.sceneName)
      .filter(Boolean);

    return {
      canApply: plan.changed,
      actionLabel: plan.changed ? `整理全项目长文本 ${plan.splitCount} 张` : "全项目文本长度舒适",
      badgeLabel: plan.changed ? `${plan.changedSceneCount} 个场景可整理` : "无需拆卡",
      helperText: plan.changed
        ? `会处理 ${previewNames.join("、")}${plan.changedSceneCount > previewNames.length ? " 等场景" : ""}；只拆台词和旁白，不改文字内容。`
        : "全项目台词和旁白长度已经比较舒适。",
      plan,
    };
  }

  function getReadableTextToolState(text) {
    const metrics = getReadableTextMetrics(text);
    const isLong = isReadableTextLong(text);
    const canSplit = splitReadableTextIntoChunks(text).length > 1;

    return {
      metrics,
      isLong,
      canSplit,
      statusText: isLong ? "建议拆卡" : canSplit ? "可拆卡" : "长度舒适",
      toneClass: isLong ? "warn-text" : "good-text",
    };
  }

  global.CanvasiaEditorScriptReadability = Object.freeze({
    VN_TEXT_LONG_WARNING_LENGTH,
    VN_TEXT_LONG_WARNING_LINES,
    VN_TEXT_SPLIT_TARGET_LENGTH,
    VN_CHOICE_LONG_WARNING_LENGTH,
    VN_CHOICE_MANY_OPTIONS,
    getReadableTextMetrics,
    buildReadableTextSummary,
    getChoiceTextQualityState,
    buildChoiceTextSummary,
    renderChoiceTextQualityTools,
    buildChoiceCountSummary,
    isReadableTextLong,
    getReadableTextToolState,
    findReadableSplitIndex,
    splitLongReadableSegment,
    shouldJoinReadableSegmentsWithSpace,
    splitReadableTextIntoChunks,
    isReadableTextBlock,
    createReadableBlockIdAllocator,
    buildReadableBlockSplitPlan,
    buildReadableSceneSplitPlan,
    getProjectReadableSceneList,
    buildReadableProjectSplitSummary,
    buildReadableProjectSplitPlan,
    getReadableProjectSplitDigest,
  });
})(typeof window !== "undefined" ? window : globalThis);
