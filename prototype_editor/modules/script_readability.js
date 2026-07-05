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

  function normalizeReadableSceneBlocks(sceneOrBlocks) {
    if (Array.isArray(sceneOrBlocks)) {
      return sceneOrBlocks;
    }

    return Array.isArray(sceneOrBlocks?.blocks) ? sceneOrBlocks.blocks : [];
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
  });
})(typeof window !== "undefined" ? window : globalThis);
