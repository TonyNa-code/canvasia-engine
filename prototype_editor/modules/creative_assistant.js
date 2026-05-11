(function attachCreativeAssistantTools(global) {
  const CREATIVE_ASSISTANT_MODES = Object.freeze({
    starter_demo: "试玩 Demo",
    script: "剧情片段",
    advice: "创作建议",
    polish: "场景润色",
  });

  const CREATIVE_ASSISTANT_PROVIDERS = Object.freeze({
    local: "本地模板",
    openai: "OpenAI 真模型",
  });

  const CREATIVE_ASSISTANT_PROVIDER_STORAGE_KEY = "canvasia-engine:creative-assistant-provider";
  const CREATIVE_ASSISTANT_OPENAI_KEY_STORAGE_KEY = "canvasia-engine:creative-assistant-openai-key";
  const CREATIVE_ASSISTANT_OPENAI_MODEL_STORAGE_KEY = "canvasia-engine:creative-assistant-openai-model";
  const CREATIVE_ASSISTANT_REMEMBER_KEY_STORAGE_KEY = "canvasia-engine:creative-assistant-remember-key";
  const CREATIVE_ASSISTANT_HISTORY_STORAGE_KEY = "canvasia-engine:creative-assistant-history";
  const CREATIVE_ASSISTANT_HISTORY_RECOVERY_STORAGE_KEY = "canvasia-engine:creative-assistant-history-recovery";
  const CREATIVE_ASSISTANT_DEFAULT_OPENAI_MODEL = "gpt-5.5";
  const CREATIVE_ASSISTANT_MAX_HISTORY = 8;

  const CREATIVE_ASSISTANT_PROMPT_SAMPLES = Object.freeze([
    "雨夜校园悬疑恋爱，女主知道一个不能说的秘密",
    "近未来城市里，AI 少女第一次学会撒谎",
    "黄昏天台，青梅竹马终于谈起三年前的误会",
  ]);

  function hasOwn(source, key) {
    return Object.prototype.hasOwnProperty.call(source, key);
  }

  function getSafeCreativeAssistantMode(mode) {
    const safeMode = String(mode ?? "").trim();
    return hasOwn(CREATIVE_ASSISTANT_MODES, safeMode) ? safeMode : "starter_demo";
  }

  function getSafeCreativeAssistantProvider(provider) {
    const safeProvider = String(provider ?? "").trim();
    return hasOwn(CREATIVE_ASSISTANT_PROVIDERS, safeProvider) ? safeProvider : "local";
  }

  function getSafeCreativeAssistantModel(model) {
    const cleanModel = String(model ?? "").trim();
    return cleanModel || CREATIVE_ASSISTANT_DEFAULT_OPENAI_MODEL;
  }

  function getDefaultCreativeAssistantSettings() {
    return {
      provider: "local",
      rememberKey: false,
      openAiKey: "",
      model: CREATIVE_ASSISTANT_DEFAULT_OPENAI_MODEL,
    };
  }

  function trimCreativeAssistantText(value, maxLength = 600) {
    return String(value ?? "").trim().slice(0, maxLength);
  }

  function cloneCreativeAssistantBlocksForHistory(blocks) {
    if (!Array.isArray(blocks)) {
      return [];
    }
    return blocks.slice(0, 12).map((block) => {
      const blockType = ["dialogue", "narration", "choice"].includes(block?.type) ? block.type : "narration";
      if (blockType === "choice") {
        return {
          type: "choice",
          options: (Array.isArray(block.options) ? block.options : []).slice(0, 4).map((option, index) => ({
            text: trimCreativeAssistantText(option?.text || `选项 ${index + 1}`, 120),
            gotoSceneId: trimCreativeAssistantText(option?.gotoSceneId, 120),
            effects: [],
          })),
        };
      }
      const clonedBlock = {
        type: blockType,
        text: trimCreativeAssistantText(block?.text, 800),
      };
      if (blockType === "dialogue") {
        clonedBlock.speakerId = trimCreativeAssistantText(block?.speakerId, 120);
        clonedBlock.expressionId = trimCreativeAssistantText(block?.expressionId, 120);
      }
      return clonedBlock;
    });
  }

  function sanitizeCreativeAssistantHistoryResult(result) {
    if (!result || typeof result !== "object") {
      return null;
    }
    const blocks = cloneCreativeAssistantBlocksForHistory(result.blocks);
    const provider = result.provider && typeof result.provider === "object" ? result.provider : {};
    return {
      mode: getSafeCreativeAssistantMode(result.mode),
      modeLabel: trimCreativeAssistantText(result.modeLabel || CREATIVE_ASSISTANT_MODES[getSafeCreativeAssistantMode(result.mode)], 80),
      title: trimCreativeAssistantText(result.title || "未命名灵感", 120),
      summary: trimCreativeAssistantText(result.summary, 700),
      guidance: (Array.isArray(result.guidance) ? result.guidance : [])
        .map((item) => trimCreativeAssistantText(item, 280))
        .filter(Boolean)
        .slice(0, 8),
      assetPrompts: (Array.isArray(result.assetPrompts) ? result.assetPrompts : [])
        .map((item) => trimCreativeAssistantText(item, 280))
        .filter(Boolean)
        .slice(0, 6),
      blocks,
      insertable: Boolean(blocks.length),
      blockCount: blocks.length,
      provider: {
        mode: getSafeCreativeAssistantProvider(provider.mode),
        label: trimCreativeAssistantText(
          provider.label || CREATIVE_ASSISTANT_PROVIDERS[getSafeCreativeAssistantProvider(provider.mode)],
          80
        ),
        status: trimCreativeAssistantText(provider.status, 60),
        model: trimCreativeAssistantText(provider.model, 80),
        fallback: Boolean(provider.fallback),
      },
      privacy: {
        mode: trimCreativeAssistantText(result.privacy?.mode, 80),
        sentToExternalService: Boolean(result.privacy?.sentToExternalService),
        message: trimCreativeAssistantText(result.privacy?.message, 260),
      },
      fallbackReason: trimCreativeAssistantText(result.fallbackReason, 260),
    };
  }

  function sanitizeCreativeAssistantGenerationResponse(response) {
    const rawResult =
      response && typeof response === "object" && hasOwn(response, "result")
        ? response.result
        : response;
    return sanitizeCreativeAssistantHistoryResult(rawResult);
  }

  function sanitizeCreativeAssistantHistoryRecord(record, options = {}) {
    if (!record || typeof record !== "object") {
      return null;
    }
    const result = sanitizeCreativeAssistantHistoryResult(record.result);
    if (!result) {
      return null;
    }
    const createId =
      typeof options.createId === "function"
        ? options.createId
        : () => `creative_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    const nowIso = typeof options.nowIso === "function" ? options.nowIso : () => new Date().toISOString();
    return {
      id: trimCreativeAssistantText(record.id, 80) || createId(),
      createdAt: trimCreativeAssistantText(record.createdAt, 40) || nowIso(),
      prompt: trimCreativeAssistantText(record.prompt, 800),
      sceneId: trimCreativeAssistantText(record.sceneId, 160),
      sceneName: trimCreativeAssistantText(record.sceneName || "当前场景", 160),
      favorite: Boolean(record.favorite),
      result,
    };
  }

  function getCreativeAssistantHistorySignature(record) {
    return `${record?.result?.title ?? ""}|${record?.prompt ?? ""}`;
  }

  function getCreativeAssistantHistoryLimit(limit = CREATIVE_ASSISTANT_MAX_HISTORY) {
    const numericLimit = Number(limit);
    return Math.max(0, Number.isFinite(numericLimit) ? numericLimit : CREATIVE_ASSISTANT_MAX_HISTORY);
  }

  function capCreativeAssistantHistoryRecords(records, limit = CREATIVE_ASSISTANT_MAX_HISTORY) {
    const safeLimit = getCreativeAssistantHistoryLimit(limit);
    const sourceRecords = (Array.isArray(records) ? records : []).filter(Boolean);
    if (safeLimit <= 0) {
      return [];
    }
    if (sourceRecords.length <= safeLimit) {
      return sourceRecords.slice(0, safeLimit);
    }
    const selected = [];
    const selectedRecords = new Set();
    sourceRecords.forEach((record, index) => {
      if (record?.favorite && selected.length < safeLimit) {
        selected.push({ index, record });
        selectedRecords.add(record);
      }
    });
    sourceRecords.forEach((record, index) => {
      if (!selectedRecords.has(record) && selected.length < safeLimit) {
        selected.push({ index, record });
        selectedRecords.add(record);
      }
    });
    return selected
      .sort((left, right) => left.index - right.index)
      .map((item) => item.record);
  }

  function mergeCreativeAssistantHistoryRecord(records, record, limit = CREATIVE_ASSISTANT_MAX_HISTORY) {
    const sourceRecords = Array.isArray(records) ? records : [];
    const safeLimit = getCreativeAssistantHistoryLimit(limit);
    if (!record) {
      return capCreativeAssistantHistoryRecords(sourceRecords, safeLimit);
    }
    const recordSignature = getCreativeAssistantHistorySignature(record);
    const duplicateRecord = sourceRecords.find(
      (item) => item?.id === record.id || getCreativeAssistantHistorySignature(item) === recordSignature
    );
    const mergedRecord = duplicateRecord?.favorite && !record.favorite
      ? { ...record, favorite: true }
      : record;
    return capCreativeAssistantHistoryRecords([
      mergedRecord,
      ...sourceRecords.filter(
        (item) => item?.id !== record.id && getCreativeAssistantHistorySignature(item) !== recordSignature
      ),
    ], safeLimit);
  }

  function loadCreativeAssistantSettings(storage) {
    try {
      return {
        provider: getSafeCreativeAssistantProvider(storage.getItem(CREATIVE_ASSISTANT_PROVIDER_STORAGE_KEY)),
        rememberKey: storage.getItem(CREATIVE_ASSISTANT_REMEMBER_KEY_STORAGE_KEY) === "true",
        openAiKey: storage.getItem(CREATIVE_ASSISTANT_OPENAI_KEY_STORAGE_KEY) ?? "",
        model: getSafeCreativeAssistantModel(storage.getItem(CREATIVE_ASSISTANT_OPENAI_MODEL_STORAGE_KEY)),
      };
    } catch (error) {
      return {
        provider: "local",
        rememberKey: false,
        openAiKey: "",
        model: CREATIVE_ASSISTANT_DEFAULT_OPENAI_MODEL,
      };
    }
  }

  function persistCreativeAssistantSettings(storage, settings) {
    try {
      storage.setItem(CREATIVE_ASSISTANT_PROVIDER_STORAGE_KEY, getSafeCreativeAssistantProvider(settings?.provider));
      storage.setItem(CREATIVE_ASSISTANT_OPENAI_MODEL_STORAGE_KEY, getSafeCreativeAssistantModel(settings?.model));
      storage.setItem(CREATIVE_ASSISTANT_REMEMBER_KEY_STORAGE_KEY, settings?.rememberKey ? "true" : "false");
      if (settings?.rememberKey && settings?.openAiKey) {
        storage.setItem(CREATIVE_ASSISTANT_OPENAI_KEY_STORAGE_KEY, settings.openAiKey);
      } else {
        storage.removeItem(CREATIVE_ASSISTANT_OPENAI_KEY_STORAGE_KEY);
      }
      return true;
    } catch (error) {
      return false;
    }
  }

  function loadCreativeAssistantHistory(storage, options = {}) {
    try {
      const parsed = JSON.parse(storage.getItem(CREATIVE_ASSISTANT_HISTORY_STORAGE_KEY) || "[]");
      return (Array.isArray(parsed) ? parsed : [])
        .map((record) => sanitizeCreativeAssistantHistoryRecord(record, options))
        .filter(Boolean)
        .slice(0, CREATIVE_ASSISTANT_MAX_HISTORY);
    } catch (error) {
      return [];
    }
  }

  function persistCreativeAssistantHistory(storage, records, limit = CREATIVE_ASSISTANT_MAX_HISTORY) {
    try {
      storage.setItem(
        CREATIVE_ASSISTANT_HISTORY_STORAGE_KEY,
        JSON.stringify(capCreativeAssistantHistoryRecords(records, limit))
      );
      return true;
    } catch (error) {
      return false;
    }
  }

  function buildCreativeAssistantHistoryRecoverySnapshot(records, options = {}) {
    const sanitizedRecords = capCreativeAssistantHistoryRecords(
      (Array.isArray(records) ? records : [])
        .map((record) =>
          sanitizeCreativeAssistantHistoryRecord(record, {
            createId: options.createId,
            nowIso: options.nowIso,
          })
        )
        .filter(Boolean),
      options.limit
    );
    return {
      engine: "Canvasia Engine",
      kind: "creative_assistant_history_recovery",
      formatVersion: 1,
      createdAt: trimCreativeAssistantText(options.createdAt, 40) || new Date().toISOString(),
      reason: trimCreativeAssistantText(options.reason || "history_cleanup", 80),
      recordCount: sanitizedRecords.length,
      records: sanitizedRecords,
      privacy: {
        containsApiKey: false,
        storage: "browser_localStorage",
      },
    };
  }

  function sanitizeCreativeAssistantHistoryRecoverySnapshot(snapshot, options = {}) {
    if (!snapshot || typeof snapshot !== "object") {
      return null;
    }
    const records = capCreativeAssistantHistoryRecords(
      (Array.isArray(snapshot.records) ? snapshot.records : [])
        .map((record) =>
          sanitizeCreativeAssistantHistoryRecord(record, {
            createId: options.createId,
            nowIso: options.nowIso,
          })
        )
        .filter(Boolean),
      options.limit
    );
    if (!records.length) {
      return null;
    }
    return {
      engine: "Canvasia Engine",
      kind: "creative_assistant_history_recovery",
      formatVersion: 1,
      createdAt: trimCreativeAssistantText(snapshot.createdAt, 40) || new Date().toISOString(),
      reason: trimCreativeAssistantText(snapshot.reason || "history_cleanup", 80),
      recordCount: records.length,
      records,
      privacy: {
        containsApiKey: false,
        storage: "browser_localStorage",
      },
    };
  }

  function buildCreativeAssistantHistoryRecoverySwap(currentRecords, recoverySnapshot, options = {}) {
    const currentSafeRecords = capCreativeAssistantHistoryRecords(
      (Array.isArray(currentRecords) ? currentRecords : [])
        .map((record) =>
          sanitizeCreativeAssistantHistoryRecord(record, {
            createId: options.createId,
            nowIso: options.nowIso,
          })
        )
        .filter(Boolean),
      options.limit
    );
    const safeRecoverySnapshot = sanitizeCreativeAssistantHistoryRecoverySnapshot(recoverySnapshot, {
      createId: options.createId,
      nowIso: options.nowIso,
      limit: options.limit,
    });
    if (!safeRecoverySnapshot?.records?.length) {
      return {
        canRestore: false,
        currentRecordCount: currentSafeRecords.length,
        restoredRecordCount: 0,
        restoredRecords: [],
        nextRecoverySnapshot: null,
      };
    }
    const nextRecoverySnapshot = currentSafeRecords.length
      ? buildCreativeAssistantHistoryRecoverySnapshot(currentSafeRecords, {
          createdAt: options.createdAt,
          reason: options.reason || "before_restore",
          limit: options.limit,
          createId: options.createId,
          nowIso: options.nowIso,
        })
      : null;
    return {
      canRestore: true,
      currentRecordCount: currentSafeRecords.length,
      restoredRecordCount: safeRecoverySnapshot.records.length,
      restoredRecords: safeRecoverySnapshot.records,
      nextRecoverySnapshot,
    };
  }

  function loadCreativeAssistantHistoryRecovery(storage, options = {}) {
    try {
      return sanitizeCreativeAssistantHistoryRecoverySnapshot(
        JSON.parse(storage.getItem(CREATIVE_ASSISTANT_HISTORY_RECOVERY_STORAGE_KEY) || "null"),
        options
      );
    } catch (error) {
      return null;
    }
  }

  function persistCreativeAssistantHistoryRecovery(storage, snapshot) {
    try {
      const sanitizedSnapshot = sanitizeCreativeAssistantHistoryRecoverySnapshot(snapshot);
      if (!sanitizedSnapshot) {
        storage.removeItem(CREATIVE_ASSISTANT_HISTORY_RECOVERY_STORAGE_KEY);
        return false;
      }
      storage.setItem(CREATIVE_ASSISTANT_HISTORY_RECOVERY_STORAGE_KEY, JSON.stringify(sanitizedSnapshot));
      return true;
    } catch (error) {
      return false;
    }
  }

  function clearCreativeAssistantHistoryRecovery(storage) {
    try {
      storage.removeItem(CREATIVE_ASSISTANT_HISTORY_RECOVERY_STORAGE_KEY);
      return true;
    } catch (error) {
      return false;
    }
  }

  function buildCreativeAssistantHistoryArchive(records, options = {}) {
    const numericLimit = Number(options.limit);
    const safeLimit = Math.max(0, Number.isFinite(numericLimit) ? numericLimit : CREATIVE_ASSISTANT_MAX_HISTORY);
    const sanitizedRecords = (Array.isArray(records) ? records : [])
      .map((record) =>
        sanitizeCreativeAssistantHistoryRecord(record, {
          createId: options.createId,
          nowIso: options.nowIso,
        })
      )
      .filter(Boolean)
      .slice(0, safeLimit);
    return {
      engine: "Canvasia Engine",
      kind: "creative_assistant_history_archive",
      formatVersion: 1,
      exportedAt: trimCreativeAssistantText(options.exportedAt, 40) || new Date().toISOString(),
      projectTitle: trimCreativeAssistantText(options.projectTitle, 160),
      recordCount: sanitizedRecords.length,
      records: sanitizedRecords,
      privacy: {
        containsApiKey: false,
        storage: "browser_localStorage",
        note: "Archive contains prompts and generated ideas only; API keys are never included.",
      },
    };
  }

  function getCreativeAssistantHistoryArchiveRecords(payload, options = {}) {
    const numericLimit = Number(options.limit);
    const safeLimit = Math.max(0, Number.isFinite(numericLimit) ? numericLimit : CREATIVE_ASSISTANT_MAX_HISTORY);
    const sourceRecords = Array.isArray(payload)
      ? payload
      : Array.isArray(payload?.records)
        ? payload.records
        : payload?.record
          ? [payload.record]
          : [];
    return sourceRecords
      .map((record) =>
        sanitizeCreativeAssistantHistoryRecord(record, {
          createId: options.createId,
          nowIso: options.nowIso,
        })
      )
      .filter(Boolean)
      .slice(0, safeLimit);
  }

  function getCreativeAssistantHistorySearchText(record) {
    const result = record?.result ?? {};
    return [
      record?.prompt,
      record?.sceneName,
      result.title,
      result.summary,
      ...(Array.isArray(result.guidance) ? result.guidance : []),
      ...(Array.isArray(result.assetPrompts) ? result.assetPrompts : []),
      ...(Array.isArray(result.blocks) ? result.blocks : []).flatMap((block) => [
        block?.text,
        block?.speakerId,
        ...(Array.isArray(block?.options) ? block.options.map((option) => option?.text) : []),
      ]),
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
  }

  function filterCreativeAssistantHistoryRecords(records, options = {}) {
    const sourceRecords = Array.isArray(records) ? records : [];
    const query = trimCreativeAssistantText(options.query, 160).toLowerCase();
    const favoritesOnly = Boolean(options.favoritesOnly);
    return sourceRecords.filter((record) => {
      if (favoritesOnly && !record?.favorite) {
        return false;
      }
      if (!query) {
        return true;
      }
      return getCreativeAssistantHistorySearchText(record).includes(query);
    });
  }

  function formatCreativeAssistantMarkdownList(items, prefix = "- ") {
    return (Array.isArray(items) ? items : [])
      .map((item) => trimCreativeAssistantText(item, 360))
      .filter(Boolean)
      .map((item) => `${prefix}${item}`)
      .join("\n");
  }

  function buildCreativeAssistantRecordMarkdown(record, index = 0) {
    const safeRecord = sanitizeCreativeAssistantHistoryRecord(record, {
      createId: () => trimCreativeAssistantText(record?.id, 80) || `idea_${index + 1}`,
      nowIso: () => trimCreativeAssistantText(record?.createdAt, 40) || "",
    });
    if (!safeRecord) {
      return "";
    }
    const result = safeRecord.result;
    const guidance = formatCreativeAssistantMarkdownList(result.guidance);
    const assetPrompts = formatCreativeAssistantMarkdownList(result.assetPrompts);
    const blocksText = buildCreativeAssistantBlocksText(result, getDefaultCreativeAssistantBlockSelection(result));
    return [
      `## ${index + 1}. ${result.title}${safeRecord.favorite ? " ★" : ""}`,
      "",
      `- 场景：${safeRecord.sceneName || "当前场景"}`,
      `- 时间：${safeRecord.createdAt || "未记录"}`,
      `- 模式：${result.modeLabel || CREATIVE_ASSISTANT_MODES[result.mode]}`,
      safeRecord.prompt ? `- 提示词：${safeRecord.prompt}` : "",
      "",
      result.summary ? `**概述**\n\n${result.summary}` : "",
      guidance ? `**创作建议**\n\n${guidance}` : "",
      assetPrompts ? `**素材提示**\n\n${assetPrompts}` : "",
      blocksText ? `**可插入剧情卡片**\n\n${blocksText}` : "",
    ]
      .filter(Boolean)
      .join("\n\n");
  }

  function buildCreativeAssistantHistoryMarkdown(records, options = {}) {
    const sourceRecords = Array.isArray(records) ? records : [];
    const sanitizedRecords = filterCreativeAssistantHistoryRecords(sourceRecords, {
      query: options.query,
      favoritesOnly: options.favoritesOnly,
    }).slice(0, Number.isFinite(Number(options.limit)) ? Math.max(0, Number(options.limit)) : CREATIVE_ASSISTANT_MAX_HISTORY);
    const projectTitle = trimCreativeAssistantText(options.projectTitle, 160) || "Canvasia Engine Project";
    const exportedAt = trimCreativeAssistantText(options.exportedAt, 40) || new Date().toISOString();
    const filterNote = [
      trimCreativeAssistantText(options.query, 160) ? `关键词：${trimCreativeAssistantText(options.query, 160)}` : "",
      options.favoritesOnly ? "范围：仅收藏" : "",
    ].filter(Boolean).join("；") || "范围：全部灵感";
    return [
      `# ${projectTitle} · Canvasia Assistant 灵感档案`,
      "",
      `- 导出时间：${exportedAt}`,
      `- 记录数量：${sanitizedRecords.length}`,
      `- ${filterNote}`,
      "- 隐私说明：此 Markdown 不包含 API Key，仅包含提示词和生成内容。",
      "",
      sanitizedRecords.length
        ? sanitizedRecords.map((record, index) => buildCreativeAssistantRecordMarkdown(record, index)).join("\n\n---\n\n")
        : "_当前筛选下没有可导出的灵感。_",
    ].join("\n");
  }

  function getCreativeAssistantBlockTypeLabel(blockType) {
    return (
      {
        dialogue: "台词",
        narration: "旁白",
        choice: "选项",
      }[blockType] ?? "剧情"
    );
  }

  function getCreativeAssistantBlockPreviewText(block, index) {
    const blockType = ["dialogue", "narration", "choice"].includes(block?.type) ? block.type : "narration";
    if (blockType === "choice") {
      const options = Array.isArray(block.options) ? block.options : [];
      const optionText = options
        .map((option, optionIndex) => `${optionIndex + 1}. ${trimCreativeAssistantText(option?.text || `选项 ${optionIndex + 1}`, 120)}`)
        .join("\n");
      return `#${index + 1} ${getCreativeAssistantBlockTypeLabel(blockType)}\n${optionText || "1. 继续"}`;
    }
    const speaker = blockType === "dialogue" && block?.speakerId ? `【${block.speakerId}】` : "";
    return `#${index + 1} ${getCreativeAssistantBlockTypeLabel(blockType)}\n${speaker}${trimCreativeAssistantText(block?.text, 900)}`;
  }

  function getCreativeAssistantResultBlocks(result) {
    return Array.isArray(result?.blocks) ? result.blocks : [];
  }

  function getDefaultCreativeAssistantBlockSelection(result) {
    return getCreativeAssistantResultBlocks(result).map((_block, index) => index);
  }

  function getActiveCreativeAssistantBlockIndexes(result, selectedIndexes) {
    const blocks = getCreativeAssistantResultBlocks(result);
    if (!blocks.length) {
      return [];
    }
    const validIndexes = new Set(blocks.map((_block, index) => index));
    if (!Array.isArray(selectedIndexes)) {
      return getDefaultCreativeAssistantBlockSelection(result);
    }
    const selected = selectedIndexes.filter((index) => validIndexes.has(Number(index))).map(Number);
    return [...new Set(selected)].sort((left, right) => left - right);
  }

  function getSelectedCreativeAssistantBlocks(result, selectedIndexes) {
    const blocks = getCreativeAssistantResultBlocks(result);
    return getActiveCreativeAssistantBlockIndexes(result, selectedIndexes)
      .map((index) => blocks[index])
      .filter(Boolean);
  }

  function buildCreativeAssistantBlocksText(result, selectedIndexes) {
    const blocks = getSelectedCreativeAssistantBlocks(result, selectedIndexes);
    if (!blocks.length) {
      return "";
    }
    return [
      result?.title ? `《${result.title}》` : "Canvasia Assistant 剧情卡片",
      result?.summary ?? "",
      "",
      ...blocks.map((block, index) => getCreativeAssistantBlockPreviewText(block, index)),
    ]
      .filter((line) => line !== null && line !== undefined)
      .join("\n\n");
  }

  global.CanvasiaEditorCreativeAssistant = Object.freeze({
    CREATIVE_ASSISTANT_MODES,
    CREATIVE_ASSISTANT_PROVIDERS,
    CREATIVE_ASSISTANT_PROVIDER_STORAGE_KEY,
    CREATIVE_ASSISTANT_OPENAI_KEY_STORAGE_KEY,
    CREATIVE_ASSISTANT_OPENAI_MODEL_STORAGE_KEY,
    CREATIVE_ASSISTANT_REMEMBER_KEY_STORAGE_KEY,
    CREATIVE_ASSISTANT_HISTORY_STORAGE_KEY,
    CREATIVE_ASSISTANT_HISTORY_RECOVERY_STORAGE_KEY,
    CREATIVE_ASSISTANT_DEFAULT_OPENAI_MODEL,
    CREATIVE_ASSISTANT_MAX_HISTORY,
    CREATIVE_ASSISTANT_PROMPT_SAMPLES,
    getSafeCreativeAssistantMode,
    getSafeCreativeAssistantProvider,
    getSafeCreativeAssistantModel,
    getDefaultCreativeAssistantSettings,
    trimCreativeAssistantText,
    cloneCreativeAssistantBlocksForHistory,
    sanitizeCreativeAssistantHistoryResult,
    sanitizeCreativeAssistantGenerationResponse,
    sanitizeCreativeAssistantHistoryRecord,
    capCreativeAssistantHistoryRecords,
    mergeCreativeAssistantHistoryRecord,
    loadCreativeAssistantSettings,
    persistCreativeAssistantSettings,
    loadCreativeAssistantHistory,
    persistCreativeAssistantHistory,
    buildCreativeAssistantHistoryRecoverySnapshot,
    sanitizeCreativeAssistantHistoryRecoverySnapshot,
    buildCreativeAssistantHistoryRecoverySwap,
    loadCreativeAssistantHistoryRecovery,
    persistCreativeAssistantHistoryRecovery,
    clearCreativeAssistantHistoryRecovery,
    buildCreativeAssistantHistoryArchive,
    getCreativeAssistantHistoryArchiveRecords,
    getCreativeAssistantHistorySearchText,
    filterCreativeAssistantHistoryRecords,
    buildCreativeAssistantRecordMarkdown,
    buildCreativeAssistantHistoryMarkdown,
    getCreativeAssistantBlockTypeLabel,
    getCreativeAssistantBlockPreviewText,
    getCreativeAssistantResultBlocks,
    getDefaultCreativeAssistantBlockSelection,
    getActiveCreativeAssistantBlockIndexes,
    getSelectedCreativeAssistantBlocks,
    buildCreativeAssistantBlocksText,
  });
})(typeof window !== "undefined" ? window : globalThis);
