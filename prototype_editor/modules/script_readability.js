(function attachScriptReadabilityTools(global) {
  const VN_TEXT_LONG_WARNING_LENGTH = 260;
  const VN_TEXT_LONG_WARNING_LINES = 5;
  const VN_TEXT_SPLIT_TARGET_LENGTH = 180;
  const VN_CHOICE_LONG_WARNING_LENGTH = 42;
  const VN_CHOICE_MANY_OPTIONS = 6;
  const VN_SCRIPT_DUPLICATE_WINDOW = 6;
  const TERMINAL_PUNCTUATION_PATTERN = /[。！？!?…」』”’"')）】\]]$/;

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

  function getReadableBlockText(block = {}) {
    return String(block?.text ?? block?.fields?.text ?? "");
  }

  function getReadableChoiceOptions(block = {}) {
    return toReadableArray(block?.options);
  }

  function normalizeScriptQualityText(text) {
    return String(text ?? "")
      .replace(/\s+/g, "")
      .toLowerCase();
  }

  function hasTerminalPunctuation(text) {
    const safeText = String(text ?? "").trim();
    return !safeText || TERMINAL_PUNCTUATION_PATTERN.test(safeText);
  }

  function getScriptIssueWeight(issue = {}) {
    if (issue.severity === "blocker") {
      return 100;
    }
    if (issue.severity === "warn") {
      return 60;
    }
    return 20;
  }

  function buildScriptQualityIssue(severity, code, title, detail, suggestion, context = {}) {
    return {
      severity,
      code,
      title,
      detail,
      suggestion,
      ...context,
    };
  }

  function getScriptQualityStatus(issues = []) {
    if (issues.some((issue) => issue.severity === "blocker")) {
      return "blocked";
    }
    if (issues.some((issue) => issue.severity === "warn")) {
      return "review";
    }
    if (issues.length) {
      return "polish";
    }
    return "ready";
  }

  function buildScriptQualitySceneReport(sceneOrBlocks, options = {}) {
    const blocks = normalizeReadableSceneBlocks(sceneOrBlocks);
    const sceneId = cleanReadableText(sceneOrBlocks?.id, cleanReadableText(options.sceneId));
    const sceneName = cleanReadableText(sceneOrBlocks?.name ?? sceneOrBlocks?.title, cleanReadableText(options.sceneName, sceneId || "未命名场景"));
    const chapterName = cleanReadableText(sceneOrBlocks?.chapterName, cleanReadableText(options.chapterName));
    const issues = [];
    const recentText = [];
    let textBlockCount = 0;
    let dialogueCount = 0;
    let narrationCount = 0;
    let choiceCount = 0;

    blocks.forEach((block, blockIndex) => {
      const blockType = cleanReadableText(block?.type, "block");
      const context = {
        sceneId,
        sceneName,
        chapterName,
        blockId: cleanReadableText(block?.id, `block_${blockIndex + 1}`),
        blockIndex,
        blockType,
      };

      if (isReadableTextBlock(block)) {
        textBlockCount += 1;
        if (blockType === "dialogue") {
          dialogueCount += 1;
        } else {
          narrationCount += 1;
        }

        const text = cleanReadableText(getReadableBlockText(block));
        const metrics = getReadableTextMetrics(text);
        if (!text) {
          issues.push(
            buildScriptQualityIssue("blocker", "script_empty_text", "空台词 / 空旁白", "这张文本卡没有可读内容，试玩时会像卡住或空跳。", "补正文或删除这张卡", context)
          );
          return;
        }
        if (isReadableTextLong(text)) {
          issues.push(
            buildScriptQualityIssue("warn", "script_long_text", "文本卡过长", `当前 ${metrics.length} 字 / ${metrics.lineCount} 行，建议拆成多张卡。`, "拆成长文本卡片", context)
          );
        }
        if (metrics.length >= 12 && !hasTerminalPunctuation(text)) {
          issues.push(
            buildScriptQualityIssue("tip", "script_missing_terminal_punctuation", "句尾标点不完整", "这句文本没有明显收束标点，打字机效果读起来可能像没说完。", "补句号、问号、感叹号或省略号", context)
          );
        }
        const normalizedText = normalizeScriptQualityText(text);
        const duplicate = recentText.find((item) => item.text === normalizedText && blockIndex - item.blockIndex <= VN_SCRIPT_DUPLICATE_WINDOW);
        if (normalizedText && duplicate) {
          issues.push(
            buildScriptQualityIssue("warn", "script_duplicate_nearby_text", "附近出现重复文本", `和第 ${duplicate.blockIndex + 1} 张文本几乎相同，可能是误复制。`, "确认是否需要改写或删除重复卡", context)
          );
        }
        recentText.push({ text: normalizedText, blockIndex });
        if (recentText.length > VN_SCRIPT_DUPLICATE_WINDOW + 1) {
          recentText.shift();
        }
        if (blockType === "dialogue" && !cleanReadableText(block.speakerId)) {
          issues.push(
            buildScriptQualityIssue("warn", "script_dialogue_missing_speaker", "台词缺少说话人", "没有绑定说话角色时，角色名、立绘表情和语音回听都更难整理。", "绑定说话角色", context)
          );
        }
        if (blockType === "dialogue" && cleanReadableText(block.speakerId) && !cleanReadableText(block.expressionId)) {
          issues.push(
            buildScriptQualityIssue("tip", "script_dialogue_missing_expression", "台词缺少表情", "这句台词有说话人但没有指定表情，角色情绪可能显得平。", "选择表情或保留默认表情", context)
          );
        }
        return;
      }

      if (blockType === "choice") {
        choiceCount += 1;
        const optionsList = getReadableChoiceOptions(block);
        if (!optionsList.length) {
          issues.push(
            buildScriptQualityIssue("warn", "script_choice_empty_options", "选项卡没有按钮", "玩家会看到选择入口但没有可点选项。", "添加至少一个选项或删除选择卡", context)
          );
          return;
        }
        optionsList.forEach((option, optionIndex) => {
          const optionText = cleanReadableText(option?.text);
          const optionContext = { ...context, optionIndex };
          if (!optionText) {
            issues.push(
              buildScriptQualityIssue("warn", "script_choice_empty_text", "选项按钮为空", `第 ${optionIndex + 1} 个选项没有文字。`, "补选项文字", optionContext)
            );
          } else if (getChoiceTextQualityState(optionText).isLong) {
            issues.push(
              buildScriptQualityIssue("warn", "script_choice_text_too_long", "选项文字过长", `第 ${optionIndex + 1} 个选项有 ${optionText.length} 字，按钮区可能拥挤。`, "缩短按钮文字，把解释放进前一句台词", optionContext)
            );
          }
        });
      }
    });

    const summary = {
      blockCount: blocks.length,
      textBlockCount,
      dialogueCount,
      narrationCount,
      choiceCount,
      issueCount: issues.length,
      blockerCount: issues.filter((issue) => issue.severity === "blocker").length,
      warningCount: issues.filter((issue) => issue.severity === "warn").length,
      tipCount: issues.filter((issue) => issue.severity === "tip").length,
      emptyTextCount: issues.filter((issue) => issue.code === "script_empty_text").length,
      longTextCount: issues.filter((issue) => issue.code === "script_long_text").length,
      duplicateTextCount: issues.filter((issue) => issue.code === "script_duplicate_nearby_text").length,
      missingPunctuationCount: issues.filter((issue) => issue.code === "script_missing_terminal_punctuation").length,
      missingSpeakerCount: issues.filter((issue) => issue.code === "script_dialogue_missing_speaker").length,
      missingExpressionCount: issues.filter((issue) => issue.code === "script_dialogue_missing_expression").length,
      choiceIssueCount: issues.filter((issue) => issue.code.startsWith("script_choice_")).length,
    };

    return {
      sceneId,
      sceneName,
      chapterName,
      status: getScriptQualityStatus(issues),
      summary,
      issues,
    };
  }

  function buildScriptQualityAudit(data = {}, options = {}) {
    const sceneReports = getProjectReadableSceneList(data).map((scene) => buildScriptQualitySceneReport(scene, options));
    const issues = sceneReports
      .flatMap((scene) => scene.issues)
      .sort((left, right) => getScriptIssueWeight(right) - getScriptIssueWeight(left) || left.sceneName.localeCompare(right.sceneName, "zh-CN") || left.blockIndex - right.blockIndex);
    const summary = {
      sceneCount: sceneReports.length,
      textBlockCount: sceneReports.reduce((total, scene) => total + scene.summary.textBlockCount, 0),
      dialogueCount: sceneReports.reduce((total, scene) => total + scene.summary.dialogueCount, 0),
      narrationCount: sceneReports.reduce((total, scene) => total + scene.summary.narrationCount, 0),
      choiceCount: sceneReports.reduce((total, scene) => total + scene.summary.choiceCount, 0),
      issueCount: issues.length,
      blockerCount: issues.filter((issue) => issue.severity === "blocker").length,
      warningCount: issues.filter((issue) => issue.severity === "warn").length,
      tipCount: issues.filter((issue) => issue.severity === "tip").length,
      emptyTextCount: issues.filter((issue) => issue.code === "script_empty_text").length,
      longTextCount: issues.filter((issue) => issue.code === "script_long_text").length,
      duplicateTextCount: issues.filter((issue) => issue.code === "script_duplicate_nearby_text").length,
      missingPunctuationCount: issues.filter((issue) => issue.code === "script_missing_terminal_punctuation").length,
      missingSpeakerCount: issues.filter((issue) => issue.code === "script_dialogue_missing_speaker").length,
      missingExpressionCount: issues.filter((issue) => issue.code === "script_dialogue_missing_expression").length,
      choiceIssueCount: issues.filter((issue) => issue.code.startsWith("script_choice_")).length,
    };
    return {
      status: getScriptQualityStatus(issues),
      summary,
      sceneReports,
      issues,
    };
  }

  function getScriptQualityDigest(data = {}, options = {}) {
    const audit = buildScriptQualityAudit(data, options);
    const summary = audit.summary;
    const majorCount = summary.blockerCount + summary.warningCount;
    return {
      status: audit.status,
      canReview: summary.issueCount > 0,
      badgeLabel: summary.issueCount > 0 ? `${summary.issueCount} 个台词问题` : "台词体感稳定",
      headline:
        summary.issueCount > 0
          ? `台词体检：${majorCount} 个需要优先处理，${summary.tipCount} 个可润色。`
          : "台词体检：文本长度、重复和选项文案暂时稳定。",
      helperText:
        summary.issueCount > 0
          ? `重点关注空文本 ${summary.emptyTextCount}、重复 ${summary.duplicateTextCount}、长文本 ${summary.longTextCount}、选项问题 ${summary.choiceIssueCount}。`
          : "当前没有明显空文本、重复台词、过长台词或选项文案问题。",
      audit,
    };
  }

  function buildScriptQualityAuditMarkdown(audit = {}, context = {}) {
    const projectTitle = cleanReadableText(context.projectTitle ?? audit.projectTitle, "Canvasia Project");
    const generatedAt = cleanReadableText(context.generatedAt, new Date().toISOString());
    const summary = audit.summary ?? {};
    const issueRows = toReadableArray(audit.issues).slice(0, 160).map((issue, index) => [
      `${index + 1}`,
      issue.severity === "blocker" ? "阻塞" : issue.severity === "warn" ? "复查" : "润色",
      issue.chapterName,
      issue.sceneName,
      `${Number(issue.blockIndex ?? 0) + 1}`,
      issue.title,
      issue.detail,
      issue.suggestion,
    ]);
    const table = (headers, rows) => {
      if (!rows.length) {
        return "";
      }
      const escapeCell = (value) =>
        String(value ?? "")
          .replace(/\|/g, "\\|")
          .replace(/\r?\n/g, "<br />")
          .trim();
      return [
        `| ${headers.map(escapeCell).join(" | ")} |`,
        `| ${headers.map(() => "---").join(" | ")} |`,
        ...rows.map((row) => `| ${row.map(escapeCell).join(" | ")} |`),
      ].join("\n");
    };
    return `\uFEFF${[
      `# ${projectTitle} 台词质量体检`,
      "",
      `导出时间：${generatedAt}`,
      `状态：${audit.status ?? "ready"}`,
      "",
      "## 总览",
      "",
      table(
        ["项目", "数量"],
        [
          ["场景", summary.sceneCount ?? 0],
          ["文本卡", summary.textBlockCount ?? 0],
          ["台词", summary.dialogueCount ?? 0],
          ["旁白", summary.narrationCount ?? 0],
          ["空文本", summary.emptyTextCount ?? 0],
          ["长文本", summary.longTextCount ?? 0],
          ["重复文本", summary.duplicateTextCount ?? 0],
          ["选项文案问题", summary.choiceIssueCount ?? 0],
          ["缺说话人", summary.missingSpeakerCount ?? 0],
          ["缺表情", summary.missingExpressionCount ?? 0],
        ]
      ),
      "",
      "## 需要复查的台词",
      "",
      table(["序号", "级别", "章节", "场景", "卡片", "问题", "说明", "建议"], issueRows) || "当前没有明显台词质量问题。",
      "",
    ].join("\n")}`;
  }

  function buildScriptQualityAuditCsv(audit = {}) {
    const formatCell = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
    const rows = toReadableArray(audit.issues).map((issue, index) => [
      index + 1,
      issue.severity,
      issue.code,
      issue.chapterName,
      issue.sceneName,
      Number(issue.blockIndex ?? 0) + 1,
      issue.blockType,
      issue.title,
      issue.detail,
      issue.suggestion,
    ]);
    return `\uFEFF${[
      ["index", "severity", "code", "chapter", "scene", "blockIndex", "blockType", "title", "detail", "suggestion"].map(formatCell).join(","),
      ...rows.map((row) => row.map(formatCell).join(",")),
    ].join("\n")}\n`;
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
    getReadableBlockText,
    hasTerminalPunctuation,
    normalizeScriptQualityText,
    buildScriptQualitySceneReport,
    buildScriptQualityAudit,
    getScriptQualityDigest,
    buildScriptQualityAuditMarkdown,
    buildScriptQualityAuditCsv,
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
