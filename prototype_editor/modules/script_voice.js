(function attachScriptVoiceTools(global) {
  function getArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function sanitizeFileName(value, options = {}) {
    if (typeof options.sanitizeFileName === "function") {
      return options.sanitizeFileName(value);
    }
    return String(value ?? "")
      .trim()
      .replace(/[\\/:*?"<>|]/g, "_")
      .replace(/\s+/g, "_")
      .replace(/_+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  function formatCsvCell(value, options = {}) {
    if (typeof options.formatCsvCell === "function") {
      return options.formatCsvCell(value);
    }
    const text = String(value ?? "");
    return `"${text.replaceAll('"', '""')}"`;
  }

  function formatDate(value, options = {}) {
    if (typeof options.formatDate === "function") {
      return options.formatDate(value);
    }
    if (!value) {
      return "未知";
    }
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString("zh-CN");
  }

  function getDateStamp(options = {}) {
    const source = options.now instanceof Date ? options.now : options.now ? new Date(options.now) : new Date();
    const date = Number.isNaN(source.getTime()) ? new Date() : source;
    return [
      date.getFullYear(),
      String(date.getMonth() + 1).padStart(2, "0"),
      String(date.getDate()).padStart(2, "0"),
    ].join("");
  }

  function getProjectTitle(options = {}) {
    return String(options.projectTitle || "tony-na-engine");
  }

  function getExportedAt(options = {}) {
    if (options.exportedAt) {
      return options.exportedAt;
    }
    const source = options.now instanceof Date ? options.now : options.now ? new Date(options.now) : new Date();
    return Number.isNaN(source.getTime()) ? new Date().toISOString() : source.toISOString();
  }

  function getScriptFilterSummaryText(options = {}) {
    if (typeof options.getScriptFilterSummaryText === "function") {
      return options.getScriptFilterSummaryText();
    }
    return options.filterSummaryText || "全项目全部内容";
  }

  function getScriptTypeLabel(type, options = {}) {
    if (typeof options.getScriptTypeLabel === "function") {
      return options.getScriptTypeLabel(type);
    }
    if (type === "dialogue") {
      return "台词";
    }
    if (type === "narration") {
      return "旁白";
    }
    if (type === "choice") {
      return "选项";
    }
    return "全部内容";
  }

  function getScriptChapterFilterLabel(chapterId, options = {}) {
    if (typeof options.getScriptChapterFilterLabel === "function") {
      return options.getScriptChapterFilterLabel(chapterId);
    }
    return chapterId === "all" ? "全部章节" : String(chapterId ?? "全部章节");
  }

  function getScriptCharacterFilterLabel(characterId, options = {}) {
    if (typeof options.getScriptCharacterFilterLabel === "function") {
      return options.getScriptCharacterFilterLabel(characterId);
    }
    return characterId === "all" ? "全部角色" : String(characterId ?? "全部角色");
  }

  function getScriptIssueFilterLabel(issue, options = {}) {
    if (typeof options.getScriptIssueFilterLabel === "function") {
      return options.getScriptIssueFilterLabel(issue);
    }
    return {
      placeholder: "待补正文",
      too_long: "偏长内容",
      duplicate: "疑似重复",
      missing_voice: "待绑语音",
      variable_logic: "变量待修",
      missing_asset: "待补素材",
      broken_target: "跳转待修",
    }[issue] ?? "全部问题状态";
  }

  function entryToVoicePlaceholderItem(entry) {
    if (!entry?.sceneId || !entry?.blockId) {
      return null;
    }

    return {
      sceneId: entry.sceneId,
      blockId: entry.blockId,
    };
  }

  function getScriptVoiceWorkflowState(entry) {
    if (entry?.type !== "dialogue") {
      return "not_required";
    }
    if (!entry.voiceAssetId) {
      return "missing_binding";
    }
    if (entry.voiceFileExists) {
      return "ready";
    }
    return "placeholder";
  }

  function getScriptVoiceWorkflowLabel(entry) {
    const workflow = getScriptVoiceWorkflowState(entry);
    if (workflow === "missing_binding") {
      return "还没建语音条目";
    }
    if (workflow === "placeholder") {
      return "已建占位，待上传真实文件";
    }
    if (workflow === "ready") {
      return "语音文件已就绪";
    }
    return "不需要语音";
  }

  function buildSuggestedVoiceBaseName(entry = {}) {
    if (entry.voiceName) {
      return entry.voiceName;
    }
    const speaker = String(entry.speakerName || "角色").trim();
    const chapter = String(entry.chapterName || "章节").trim();
    const scene = String(entry.sceneName || "场景").trim();
    return `${speaker}_${chapter}_${scene}_${String((entry.blockIndex ?? 0) + 1).padStart(3, "0")}`;
  }

  function buildSuggestedVoiceFileName(entry = {}, options = {}) {
    const existingPathName = entry.voiceAssetPath ? entry.voiceAssetPath.split("/").pop() ?? "" : "";
    if (existingPathName) {
      return existingPathName;
    }
    return `${sanitizeFileName(buildSuggestedVoiceBaseName(entry), options) || "voice_line"}.wav`;
  }

  function getScriptVoiceStatusText(status) {
    if (status === "missing") {
      return "待绑语音";
    }

    if (status === "voiced") {
      return "已绑语音";
    }

    return "不需要语音";
  }

  function buildVoiceFileMatchAlertMessage(result) {
    const lines = [];
    const matchedCount = Number(result?.matchedCount ?? 0);
    const unmatchedFiles = getArray(result?.unmatchedFiles);
    const ambiguousFiles = getArray(result?.ambiguousFiles);

    if (matchedCount > 0) {
      lines.push(`已成功匹配 ${matchedCount} 个语音文件。`);
    }

    if (unmatchedFiles.length > 0) {
      lines.push("");
      lines.push(`这些文件暂时没有自动匹配成功（${unmatchedFiles.length} 个）：`);
      unmatchedFiles.slice(0, 6).forEach((item) => {
        lines.push(`- ${item.fileName}：${item.reason}`);
      });
      if (unmatchedFiles.length > 6) {
        lines.push(`- 另外还有 ${unmatchedFiles.length - 6} 个文件没有展开`);
      }
    }

    if (ambiguousFiles.length > 0) {
      lines.push("");
      lines.push(`这些文件有多个疑似目标，暂时没有自动乱绑（${ambiguousFiles.length} 个）：`);
      ambiguousFiles.slice(0, 4).forEach((item) => {
        const candidateText = getArray(item.candidates)
          .map((candidate) => candidate.assetName)
          .filter(Boolean)
          .join(" / ");
        lines.push(`- ${item.fileName}：${candidateText || item.reason}`);
      });
      if (ambiguousFiles.length > 4) {
        lines.push(`- 另外还有 ${ambiguousFiles.length - 4} 个文件没有展开`);
      }
    }

    return lines.join("\n").trim();
  }

  function buildVoiceMatchReviewSession(uploadFiles, result, options = {}) {
    const payloadBuckets = new Map();
    getArray(uploadFiles).forEach((filePayload) => {
      const name = String(filePayload?.name ?? "").trim();
      if (!name) {
        return;
      }
      const bucket = payloadBuckets.get(name) ?? [];
      bucket.push(filePayload);
      payloadBuckets.set(name, bucket);
    });

    const takePayloadByName = (fileName) => {
      const bucket = payloadBuckets.get(fileName) ?? [];
      if (!bucket.length) {
        return null;
      }
      const payload = bucket.shift() ?? null;
      if (bucket.length > 0) {
        payloadBuckets.set(fileName, bucket);
      } else {
        payloadBuckets.delete(fileName);
      }
      return payload;
    };

    const mapReviewItem = (item) => {
      const fileName = String(item?.fileName ?? "").trim();
      const payload = takePayloadByName(fileName);
      if (!fileName || !payload) {
        return null;
      }
      return {
        fileName,
        file: payload,
        reason: item?.reason ?? "",
        candidates: item?.candidates ?? [],
      };
    };

    const unmatchedFiles = getArray(result?.unmatchedFiles).map(mapReviewItem).filter(Boolean);
    const ambiguousFiles = getArray(result?.ambiguousFiles).map(mapReviewItem).filter(Boolean);

    if (!unmatchedFiles.length && !ambiguousFiles.length) {
      return null;
    }

    return {
      createdAt: typeof options.nowIso === "function" ? options.nowIso() : new Date().toISOString(),
      matchedCount: Number(result?.matchedCount ?? 0),
      unmatchedFiles,
      ambiguousFiles,
    };
  }

  function getVoiceMatchReviewSelectId(reviewKind, reviewIndex) {
    return `voiceMatchReview-${reviewKind}-${reviewIndex}`;
  }

  function getAvailableManualVoiceMatchTargets(data) {
    if (!data) {
      return [];
    }
    return getArray(data.assetList).filter((asset) => asset.type === "voice" && !asset.fileExists);
  }

  function getDefaultVoiceMatchTargetId(item, availableTargets) {
    const safeTargets = getArray(availableTargets);
    const candidateIds = getArray(item?.candidates)
      .map((candidate) => candidate.assetId)
      .filter((assetId) => safeTargets.some((asset) => asset.id === assetId));
    if (candidateIds.length > 0) {
      return candidateIds[0];
    }
    return safeTargets[0]?.id ?? "";
  }

  function buildScriptEntryCopyText(entry, options = {}) {
    const projectTitle = options.projectTitle ?? "Tony Na Engine Project";
    const lines = [
      `项目：${projectTitle}`,
      `章节：${entry.chapterName}`,
      `场景：${entry.sceneName}`,
      `位置：第 ${Number(entry.blockIndex ?? 0) + 1} 张`,
      `类型：${getScriptTypeLabel(entry.type, options)}`,
    ];

    if (entry.type === "dialogue") {
      lines.push(`角色：${entry.speakerName}`);
    }

    if (entry.expressionName) {
      lines.push(`表情：${entry.expressionName}`);
    }

    lines.push(`语音状态：${getScriptVoiceStatusText(entry.voiceStatus)}`);

    if (entry.voiceName) {
      lines.push(`语音名：${entry.voiceName}`);
    }

    if (getArray(entry.issues).length > 0) {
      lines.push(`问题标签：${entry.issues.map((issue) => getScriptIssueFilterLabel(issue, options)).join(" / ")}`);
    }

    lines.push("", "正文：", entry.text || "这句还没有正文。");

    if (entry.previousContext) {
      lines.push("", `上一句：${entry.previousContext.label}：${entry.previousContext.text}`);
    }

    if (entry.nextContext) {
      lines.push(`下一句：${entry.nextContext.label}：${entry.nextContext.text}`);
    }

    return lines.join("\n");
  }

  function buildScriptTxtContent(filteredEntries, totalEntryCount, options = {}) {
    const lines = [];
    const scopeText = getScriptFilterSummaryText(options);
    const groupedByChapter = new Map();

    getArray(filteredEntries).forEach((entry) => {
      const chapterBucket = groupedByChapter.get(entry.chapterName) ?? new Map();
      const sceneBucket = chapterBucket.get(entry.sceneName) ?? [];
      sceneBucket.push(entry);
      chapterBucket.set(entry.sceneName, sceneBucket);
      groupedByChapter.set(entry.chapterName, chapterBucket);
    });

    lines.push(`${getProjectTitle(options)} · Tony Na Engine 台本导出`);
    lines.push(`导出时间：${formatDate(getExportedAt(options), options)}`);
    lines.push(`当前筛选：${scopeText}`);
    lines.push(`导出条数：${getArray(filteredEntries).length} / 全项目 ${totalEntryCount}`);
    lines.push("");

    groupedByChapter.forEach((sceneMap, chapterName) => {
      lines.push(`【章节】${chapterName}`);
      sceneMap.forEach((entries, sceneName) => {
        lines.push(`  [场景] ${sceneName}`);
        entries.forEach((entry) => {
          const issueText =
            getArray(entry.issues).length > 0
              ? ` [问题：${entry.issues.map((issue) => getScriptIssueFilterLabel(issue, options)).join(" / ")}]`
              : "";
          const previousText = entry.previousContext
            ? ` [上一句：${entry.previousContext.label}：${entry.previousContext.text}]`
            : "";
          const nextText = entry.nextContext
            ? ` [下一句：${entry.nextContext.label}：${entry.nextContext.text}]`
            : "";
          if (entry.type === "dialogue") {
            lines.push(
              `  - ${entry.speakerName}：${entry.text} ${
                entry.voiceStatus === "missing"
                  ? "（待绑语音）"
                  : entry.voiceStatus === "voiced"
                    ? `（语音：${entry.voiceName || "已绑定"}）`
                    : ""
              }${issueText}${previousText}${nextText}`
            );
          } else if (entry.type === "narration") {
            lines.push(`  - [旁白] ${entry.text}${issueText}${previousText}${nextText}`);
          } else {
            lines.push(`  - [选项] ${entry.text}${issueText}${previousText}${nextText}`);
          }
        });
        lines.push("");
      });
    });

    return `\uFEFF${lines.join("\n")}`;
  }

  function buildScriptCsvContent(filteredEntries, totalEntryCount, options = {}) {
    const rows = [
      ["项目名", getProjectTitle(options)],
      ["导出时间", formatDate(getExportedAt(options), options)],
      ["当前筛选", getScriptFilterSummaryText(options)],
      ["导出条数", `${getArray(filteredEntries).length} / 全项目 ${totalEntryCount}`],
      [],
      ["章节", "场景", "卡片序号", "内容类型", "角色", "表情", "上一句", "正文", "下一句", "语音状态", "语音名", "问题标签"],
      ...getArray(filteredEntries).map((entry) => [
        entry.chapterName,
        entry.sceneName,
        Number(entry.blockIndex ?? 0) + 1,
        getScriptTypeLabel(entry.type, options),
        entry.speakerName,
        entry.expressionName,
        entry.previousContext ? `${entry.previousContext.label}：${entry.previousContext.text}` : "",
        entry.text,
        entry.nextContext ? `${entry.nextContext.label}：${entry.nextContext.text}` : "",
        getScriptVoiceStatusText(entry.voiceStatus),
        entry.voiceName,
        getArray(entry.issues).map((issue) => getScriptIssueFilterLabel(issue, options)).join(" / "),
      ]),
    ];

    return `\uFEFF${rows.map((row) => row.map((cell) => formatCsvCell(cell, options)).join(",")).join("\n")}`;
  }

  function getVoiceSheetEntries(sourceEntries, filters = {}, options = {}) {
    const safeCharacterId = filters.characterId
      ? typeof options.getSafeScriptCharacterFilter === "function"
        ? options.getSafeScriptCharacterFilter(filters.characterId)
        : filters.characterId
      : "all";
    const safeChapterId = filters.chapterId
      ? typeof options.getSafeScriptChapterFilter === "function"
        ? options.getSafeScriptChapterFilter(filters.chapterId)
        : filters.chapterId
      : "all";

    return getArray(sourceEntries).filter((entry) => {
      if (entry.type !== "dialogue") {
        return false;
      }
      if (safeCharacterId !== "all" && entry.characterId !== safeCharacterId) {
        return false;
      }
      if (safeChapterId !== "all" && entry.chapterId !== safeChapterId) {
        return false;
      }
      return getScriptVoiceWorkflowState(entry) !== "ready";
    });
  }

  function buildScriptVoiceSheetContent(filteredEntries, totalEntryCount, filters = {}, options = {}) {
    const scopeText =
      filters.characterId || filters.chapterId
        ? [
            filters.characterId ? `角色=${getScriptCharacterFilterLabel(filters.characterId, options)}` : "",
            filters.chapterId ? `章节=${getScriptChapterFilterLabel(filters.chapterId, options)}` : "",
          ]
            .filter(Boolean)
            .join(" / ")
        : getScriptFilterSummaryText(options);

    const rows = [
      ["项目名", getProjectTitle(options)],
      ["导出时间", formatDate(getExportedAt(options), options)],
      ["当前范围", scopeText || "全项目待录语音"],
      ["导出条数", `${getArray(filteredEntries).length} / 全项目待录 ${totalEntryCount}`],
      [],
      [
        "角色",
        "章节",
        "场景",
        "卡片序号",
        "当前状态",
        "当前语音条目",
        "当前语音路径",
        "目标语音条目名",
        "目标录音文件名",
        "表情",
        "正文",
        "上一句",
        "下一句",
      ],
      ...getArray(filteredEntries).map((entry) => [
        entry.speakerName,
        entry.chapterName,
        entry.sceneName,
        Number(entry.blockIndex ?? 0) + 1,
        getScriptVoiceWorkflowLabel(entry),
        entry.voiceName,
        entry.voiceAssetPath,
        buildSuggestedVoiceBaseName(entry),
        buildSuggestedVoiceFileName(entry, options),
        entry.expressionName,
        entry.text,
        entry.previousContext ? `${entry.previousContext.label}：${entry.previousContext.text}` : "",
        entry.nextContext ? `${entry.nextContext.label}：${entry.nextContext.text}` : "",
      ]),
    ];

    return `\uFEFF${rows.map((row) => row.map((cell) => formatCsvCell(cell, options)).join(",")).join("\n")}`;
  }

  function buildScriptExportFileName(format, options = {}) {
    const extension = format === "csv" ? "csv" : "txt";
    const title = sanitizeFileName(getProjectTitle(options), options) || "tony-na-engine";
    const scope = sanitizeFileName(getScriptFilterSummaryText(options), options).slice(0, 28) || "full-script";
    return `${title}_script_${scope}_${getDateStamp(options)}.${extension}`;
  }

  function buildScriptVoiceSheetFileName(filters = {}, options = {}) {
    const title = sanitizeFileName(getProjectTitle(options), options) || "tony-na-engine";
    const scopeText =
      filters.characterId || filters.chapterId
        ? [
            filters.characterId ? getScriptCharacterFilterLabel(filters.characterId, options) : "",
            filters.chapterId ? getScriptChapterFilterLabel(filters.chapterId, options) : "",
          ]
            .filter(Boolean)
            .join("_")
        : getScriptFilterSummaryText(options);
    const scope = sanitizeFileName(scopeText, options).slice(0, 28) || "voice_sheet";
    return `${title}_voice_sheet_${scope}_${getDateStamp(options)}.csv`;
  }

  function buildCharacterVoiceBriefFileName(character, options = {}) {
    const title = sanitizeFileName(getProjectTitle(options), options) || "tony-na-engine";
    const characterName = sanitizeFileName(character?.displayName || character?.id || "character", options);
    return `${title}_voice_delivery_${characterName}_${getDateStamp(options)}.txt`;
  }

  function buildChapterVoiceBriefFileName(chapter, options = {}) {
    const title = sanitizeFileName(getProjectTitle(options), options) || "tony-na-engine";
    const chapterName = sanitizeFileName(chapter?.name || chapter?.chapterId || "chapter", options);
    return `${title}_voice_delivery_${chapterName}_${getDateStamp(options)}.txt`;
  }

  function buildProjectVoiceBriefFileName(options = {}) {
    const title = sanitizeFileName(getProjectTitle(options), options) || "tony-na-engine";
    return `${title}_voice_delivery_project_${getDateStamp(options)}.txt`;
  }

  global.TonyNaEditorScriptVoice = Object.freeze({
    entryToVoicePlaceholderItem,
    getScriptVoiceWorkflowState,
    getScriptVoiceWorkflowLabel,
    buildSuggestedVoiceBaseName,
    buildSuggestedVoiceFileName,
    getScriptVoiceStatusText,
    buildVoiceFileMatchAlertMessage,
    buildVoiceMatchReviewSession,
    getVoiceMatchReviewSelectId,
    getAvailableManualVoiceMatchTargets,
    getDefaultVoiceMatchTargetId,
    buildScriptEntryCopyText,
    buildScriptTxtContent,
    buildScriptCsvContent,
    getVoiceSheetEntries,
    buildScriptVoiceSheetContent,
    buildScriptExportFileName,
    buildScriptVoiceSheetFileName,
    buildCharacterVoiceBriefFileName,
    buildChapterVoiceBriefFileName,
    buildProjectVoiceBriefFileName,
  });
})(typeof window !== "undefined" ? window : globalThis);
