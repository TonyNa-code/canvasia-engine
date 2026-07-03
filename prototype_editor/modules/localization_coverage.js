(function attachLocalizationCoverageTools(global) {
  const DEFAULT_LANGUAGE = "zh-CN";

  const LANGUAGE_LABELS = Object.freeze({
    "zh-CN": "简体中文",
    "zh-TW": "繁体中文",
    "ja-JP": "日本語",
    "en-US": "English",
    "ko-KR": "한국어",
  });

  const BLOCK_LABELS = Object.freeze({
    dialogue: "台词",
    narration: "旁白",
    choice: "选项",
    video_play: "视频标题",
    credits_roll: "片尾字幕",
  });

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function normalizeLanguageCode(value, fallback = "") {
    return cleanText(value, fallback);
  }

  function getLanguageCode(value) {
    if (typeof value === "string") {
      return normalizeLanguageCode(value);
    }
    if (value && typeof value === "object") {
      return normalizeLanguageCode(value.code ?? value.id ?? value.language ?? value.locale ?? value.value);
    }
    return "";
  }

  function addLanguage(target, value) {
    const language = getLanguageCode(value);
    if (language && !target.includes(language)) {
      target.push(language);
    }
  }

  function getTranslationMap(source = {}, key = "") {
    if (!source || typeof source !== "object" || !key) {
      return {};
    }
    const translations = source[`${key}Translations`];
    return translations && typeof translations === "object" && !Array.isArray(translations) ? translations : {};
  }

  function addLanguagesFromTranslationMap(target, source = {}, key = "") {
    Object.keys(getTranslationMap(source, key)).forEach((language) => addLanguage(target, language));
  }

  function getProjectDefaultLanguage(data = {}) {
    const project = data.project ?? {};
    const i18n = data.i18n ?? {};
    return normalizeLanguageCode(i18n.defaultLanguage ?? project.language ?? project.defaultLanguage, DEFAULT_LANGUAGE);
  }

  function getSupportedLanguages(data = {}) {
    const project = data.project ?? {};
    const i18n = data.i18n ?? {};
    const defaultLanguage = getProjectDefaultLanguage(data);
    const languages = [];
    addLanguage(languages, defaultLanguage);

    [
      i18n.supportedLanguages,
      i18n.languages,
      i18n.locales,
      project.supportedLanguages,
      project.languages,
      project.locales,
      project.targetLanguages,
    ].forEach((languageList) => toArray(languageList).forEach((language) => addLanguage(languages, language)));

    addLanguage(languages, i18n.fallbackLanguage);
    collectTranslationLanguages(data, languages);
    return languages.length ? languages : [DEFAULT_LANGUAGE];
  }

  function getLanguageLabel(language) {
    return LANGUAGE_LABELS[language] ?? language;
  }

  function buildChapterMap(data = {}) {
    return new Map(
      toArray(data.chapters).map((chapter, index) => [
        cleanText(chapter?.id),
        {
          id: cleanText(chapter?.id),
          name: cleanText(chapter?.name ?? chapter?.title, `章节 ${index + 1}`),
          order: index,
        },
      ])
    );
  }

  function getOrderedScenes(data = {}) {
    const chapterMap = buildChapterMap(data);
    const scenes = toArray(data.scenes);
    if (scenes.length) {
      return scenes.map((scene, index) => ({ scene, index }));
    }
    return toArray(data.chapters).flatMap((chapter, chapterIndex) =>
      toArray(chapter?.scenes).map((scene, sceneIndex) => ({
        scene: { ...scene, chapterId: scene?.chapterId ?? chapter?.id },
        index: chapterIndex * 10000 + sceneIndex,
      }))
    ).sort((left, right) => {
      const leftOrder = chapterMap.get(cleanText(left.scene?.chapterId))?.order ?? 9999;
      const rightOrder = chapterMap.get(cleanText(right.scene?.chapterId))?.order ?? 9999;
      return leftOrder - rightOrder || left.index - right.index;
    });
  }

  function collectTranslationLanguages(data = {}, languages = []) {
    toArray(data.characters).forEach((character) => {
      addLanguagesFromTranslationMap(languages, character, "displayName");
      addLanguagesFromTranslationMap(languages, character, "name");
    });
    toArray(data.chapters).forEach((chapter) => addLanguagesFromTranslationMap(languages, chapter, "name"));
    getOrderedScenes(data).forEach(({ scene }) => {
      addLanguagesFromTranslationMap(languages, scene, "name");
      toArray(scene?.blocks).forEach((block) => {
        addLanguagesFromTranslationMap(languages, block, "text");
        addLanguagesFromTranslationMap(languages, block, "title");
        toArray(block?.options).forEach((option) => addLanguagesFromTranslationMap(languages, option, "text"));
      });
    });
    return languages;
  }

  function buildCharacterMap(data = {}) {
    return new Map(toArray(data.characters).map((character) => [cleanText(character?.id), character]));
  }

  function getCharacterName(character, fallback = "未命名角色") {
    return cleanText(character?.displayName ?? character?.name, fallback);
  }

  function getBlockLabel(block = {}) {
    return BLOCK_LABELS[block.type] ?? cleanText(block.type, "文本");
  }

  function summarizeBlock(block = {}, index = 0, characterMap = new Map()) {
    if (block.type === "dialogue") {
      const speaker = characterMap.get(cleanText(block.speakerId));
      const speakerName = getCharacterName(speaker, cleanText(block.speakerName, "角色"));
      return `第 ${index + 1} 张 · ${speakerName}台词`;
    }
    if (block.type === "choice") {
      return `第 ${index + 1} 张 · 选项`;
    }
    return `第 ${index + 1} 张 · ${getBlockLabel(block)}`;
  }

  function getFieldLabel(kind, key, index = null) {
    if (kind === "chapter") {
      return "章节名";
    }
    if (kind === "scene") {
      return "场景名";
    }
    if (kind === "character") {
      return "角色名";
    }
    if (kind === "choice_option") {
      return index === null ? "选项文本" : `选项 ${index + 1}`;
    }
    if (key === "title") {
      return "标题";
    }
    return "正文";
  }

  function getEntryStatus(sourceText, localizedText, language, defaultLanguage) {
    if (!sourceText) {
      return "empty_source";
    }
    if (!localizedText) {
      return "missing";
    }
    if (language !== defaultLanguage && localizedText === sourceText) {
      return "same_as_source";
    }
    return "ready";
  }

  function getEntryStatusLabel(status) {
    if (status === "ready") {
      return "已翻译";
    }
    if (status === "missing") {
      return "缺翻译";
    }
    if (status === "same_as_source") {
      return "疑似未翻译";
    }
    return "原文为空";
  }

  function addCoverageEntries(entries, source = {}, descriptor = {}, context = {}) {
    const sourceText = cleanText(source?.[descriptor.key]);
    const translations = getTranslationMap(source, descriptor.key);
    context.targetLanguages.forEach((language) => {
      const localizedText = cleanText(translations[language]);
      const status = getEntryStatus(sourceText, localizedText, language, context.defaultLanguage);
      entries.push({
        id: `${descriptor.id}:${descriptor.key}:${language}`,
        sourceId: descriptor.id,
        targetId: descriptor.targetId ?? descriptor.id,
        kind: descriptor.kind,
        language,
        languageLabel: getLanguageLabel(language),
        key: descriptor.key,
        optionIndex: descriptor.optionIndex ?? null,
        fieldLabel: getFieldLabel(descriptor.kind, descriptor.key, descriptor.optionIndex),
        chapterName: descriptor.chapterName ?? "",
        sceneName: descriptor.sceneName ?? "",
        locationLabel: descriptor.locationLabel ?? "",
        sourceText,
        localizedText,
        status,
        statusLabel: getEntryStatusLabel(status),
      });
    });
  }

  function addBlockEntries(entries, block = {}, context = {}) {
    const blockLabel = summarizeBlock(block, context.blockIndex, context.characterMap);
    const baseDescriptor = {
      id: cleanText(block.id, `block_${context.blockIndex + 1}`),
      kind: "block",
      chapterName: context.chapterName,
      sceneName: context.sceneName,
      locationLabel: blockLabel,
    };

    if (["dialogue", "narration"].includes(block.type)) {
      addCoverageEntries(entries, block, { ...baseDescriptor, key: "text" }, context);
    }
    if (block.type === "video_play" || block.type === "credits_roll") {
      addCoverageEntries(entries, block, { ...baseDescriptor, key: "title" }, context);
      if (cleanText(block.text) || Object.keys(getTranslationMap(block, "text")).length) {
        addCoverageEntries(entries, block, { ...baseDescriptor, key: "text" }, context);
      }
    }
    if (block.type === "choice") {
      toArray(block.options).forEach((option, optionIndex) => {
        addCoverageEntries(
          entries,
          option,
          {
            id: `${baseDescriptor.id}:option_${optionIndex + 1}`,
            targetId: baseDescriptor.id,
            kind: "choice_option",
            key: "text",
            optionIndex,
            chapterName: context.chapterName,
            sceneName: context.sceneName,
            locationLabel: `${blockLabel} · 选项 ${optionIndex + 1}`,
          },
          context
        );
      });
    }
  }

  function buildLocalizationEntries(data = {}, options = {}) {
    const defaultLanguage = normalizeLanguageCode(options.defaultLanguage, getProjectDefaultLanguage(data));
    const supportedLanguages = toArray(options.supportedLanguages).length
      ? toArray(options.supportedLanguages).map(getLanguageCode).filter(Boolean)
      : getSupportedLanguages(data);
    const targetLanguages = supportedLanguages.filter((language) => language && language !== defaultLanguage);
    const chapterMap = buildChapterMap(data);
    const characterMap = buildCharacterMap(data);
    const context = { defaultLanguage, targetLanguages, characterMap };
    const entries = [];

    toArray(data.characters).forEach((character, index) => {
      const key = cleanText(character?.displayName) ? "displayName" : "name";
      addCoverageEntries(
        entries,
        character,
        {
          id: cleanText(character?.id, `character_${index + 1}`),
          kind: "character",
          key,
          locationLabel: getCharacterName(character, `角色 ${index + 1}`),
        },
        context
      );
    });

    toArray(data.chapters).forEach((chapter, index) => {
      const chapterName = cleanText(chapter?.name ?? chapter?.title, `章节 ${index + 1}`);
      addCoverageEntries(
        entries,
        chapter,
        {
          id: cleanText(chapter?.id, `chapter_${index + 1}`),
          kind: "chapter",
          key: "name",
          chapterName,
          locationLabel: chapterName,
        },
        context
      );
    });

    getOrderedScenes(data).forEach(({ scene, index }) => {
      const chapter = chapterMap.get(cleanText(scene?.chapterId));
      const chapterName = chapter?.name ?? "未分章";
      const sceneName = cleanText(scene?.name ?? scene?.title, `场景 ${index + 1}`);
      addCoverageEntries(
        entries,
        scene,
        {
          id: cleanText(scene?.id, `scene_${index + 1}`),
          kind: "scene",
          key: "name",
          chapterName,
          sceneName,
          locationLabel: sceneName,
        },
        context
      );
      toArray(scene?.blocks).forEach((block, blockIndex) => {
        addBlockEntries(entries, block, {
          ...context,
          blockIndex,
          chapterName,
          sceneName,
        });
      });
    });

    return {
      defaultLanguage,
      supportedLanguages,
      targetLanguages,
      entries,
    };
  }

  function buildLanguageBreakdown(entries = [], targetLanguages = []) {
    return targetLanguages.map((language) => {
      const languageEntries = entries.filter((entry) => entry.language === language && entry.status !== "empty_source");
      const readyCount = languageEntries.filter((entry) => entry.status === "ready").length;
      const missingCount = languageEntries.filter((entry) => entry.status === "missing").length;
      const sameAsSourceCount = languageEntries.filter((entry) => entry.status === "same_as_source").length;
      const totalCount = languageEntries.length;
      const completionPercent = totalCount ? Math.round((readyCount / totalCount) * 1000) / 10 : 100;
      return {
        language,
        languageLabel: getLanguageLabel(language),
        totalCount,
        readyCount,
        missingCount,
        sameAsSourceCount,
        completionPercent,
      };
    });
  }

  function buildLocalizationCoverage(data = {}, options = {}) {
    const coverage = buildLocalizationEntries(data, options);
    const sourceEntries = coverage.entries.filter((entry) => entry.status !== "empty_source");
    const readyCount = sourceEntries.filter((entry) => entry.status === "ready").length;
    const missingCount = sourceEntries.filter((entry) => entry.status === "missing").length;
    const sameAsSourceCount = sourceEntries.filter((entry) => entry.status === "same_as_source").length;
    const emptySourceCount = coverage.entries.length - sourceEntries.length;
    const expectedTranslationCount = sourceEntries.length;
    const completionPercent = expectedTranslationCount
      ? Math.round((readyCount / expectedTranslationCount) * 1000) / 10
      : coverage.targetLanguages.length
        ? 0
        : 100;
    const sourceTextCount = new Set(sourceEntries.map((entry) => `${entry.sourceId}:${entry.key}`)).size;
    const issues = sourceEntries
      .filter((entry) => entry.status === "missing" || entry.status === "same_as_source")
      .map((entry) => ({
        severity: entry.status === "missing" ? "warn" : "tip",
        code: entry.status,
        title: entry.status === "missing" ? "缺少目标语言翻译" : "目标语言与原文相同",
        detail: `${entry.languageLabel} · ${entry.locationLabel} · ${entry.fieldLabel}`,
        ...entry,
      }));

    return {
      defaultLanguage: coverage.defaultLanguage,
      defaultLanguageLabel: getLanguageLabel(coverage.defaultLanguage),
      supportedLanguages: coverage.supportedLanguages,
      targetLanguages: coverage.targetLanguages,
      entries: coverage.entries,
      issues,
      languageBreakdown: buildLanguageBreakdown(coverage.entries, coverage.targetLanguages),
      summary: {
        sourceTextCount,
        supportedLanguageCount: coverage.supportedLanguages.length,
        targetLanguageCount: coverage.targetLanguages.length,
        expectedTranslationCount,
        readyCount,
        missingCount,
        sameAsSourceCount,
        emptySourceCount,
        issueCount: issues.length,
        completionPercent,
      },
    };
  }

  function getLocalizationCoverageStatusDigest(coverage = {}) {
    const summary = coverage.summary ?? {};
    if ((summary.targetLanguageCount ?? 0) <= 0) {
      return {
        status: "single",
        title: "单语言项目",
        detail: "当前只启用默认语言；如果要面向中日英等多语言玩家，可以先在项目设置里勾选目标语言。",
      };
    }
    if ((summary.sourceTextCount ?? 0) <= 0) {
      return {
        status: "empty",
        title: "暂无可翻译文本",
        detail: "还没有检测到章节名、场景名、角色名、台词、旁白或选项文本。",
      };
    }
    if ((summary.missingCount ?? 0) > 0) {
      return {
        status: "warn",
        title: `缺翻译 ${summary.missingCount} 项`,
        detail: `多语言覆盖率约 ${summary.completionPercent ?? 0}%，建议发布前先处理缺翻译条目。`,
      };
    }
    if ((summary.sameAsSourceCount ?? 0) > 0) {
      return {
        status: "warn",
        title: `疑似未翻译 ${summary.sameAsSourceCount} 项`,
        detail: `所有目标语言都有文本，但有内容与默认语言完全相同，建议复核是否只是占位。`,
      };
    }
    return {
      status: "ready",
      title: "多语言覆盖完整",
      detail: `已覆盖 ${summary.targetLanguageCount ?? 0} 个目标语言，可进入校对和试玩确认。`,
    };
  }

  function buildMarkdownTable(headers, rows) {
    if (!rows.length) {
      return "";
    }
    const escapeCell = (value) => String(value ?? "").replace(/\|/g, "\\|").replace(/\n/g, " ");
    return [
      `| ${headers.map(escapeCell).join(" | ")} |`,
      `| ${headers.map(() => "---").join(" | ")} |`,
      ...rows.map((row) => `| ${row.map(escapeCell).join(" | ")} |`),
    ].join("\n");
  }

  function escapeCsvCell(value) {
    return `"${String(value ?? "").replace(/"/g, '""')}"`;
  }

  function buildCsv(headers, rows) {
    return [headers, ...rows].map((row) => row.map(escapeCsvCell).join(",")).join("\n");
  }

  function buildLocalizationCoverageMarkdown(coverage = {}, options = {}) {
    const projectTitle = cleanText(options.projectTitle, "Canvasia Project");
    const generatedAt = cleanText(options.generatedAt, new Date().toISOString());
    const digest = getLocalizationCoverageStatusDigest(coverage);
    const summary = coverage.summary ?? {};
    const languageRows = toArray(coverage.languageBreakdown).map((item) => [
      item.languageLabel,
      item.language,
      `${item.completionPercent}%`,
      `${item.readyCount}/${item.totalCount}`,
      `${item.missingCount}`,
      `${item.sameAsSourceCount}`,
    ]);
    const issueRows = toArray(coverage.issues).slice(0, 160).map((issue, index) => [
      `${index + 1}`,
      issue.statusLabel,
      issue.languageLabel,
      issue.chapterName || "-",
      issue.sceneName || "-",
      issue.locationLabel,
      issue.fieldLabel,
      issue.sourceText,
      issue.localizedText || "(空)",
    ]);

    return `\uFEFF${[
      `# ${projectTitle} 多语言覆盖报告`,
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
          ["默认语言", `${coverage.defaultLanguageLabel ?? coverage.defaultLanguage} (${coverage.defaultLanguage})`],
          ["成品支持语言", `${summary.supportedLanguageCount ?? 0}`],
          ["目标翻译语言", `${summary.targetLanguageCount ?? 0}`],
          ["可翻译文本", `${summary.sourceTextCount ?? 0}`],
          ["应填翻译", `${summary.expectedTranslationCount ?? 0}`],
          ["已完成", `${summary.readyCount ?? 0}`],
          ["缺翻译", `${summary.missingCount ?? 0}`],
          ["疑似未翻译", `${summary.sameAsSourceCount ?? 0}`],
          ["覆盖率", `${summary.completionPercent ?? 0}%`],
        ]
      ),
      "",
      "## 按语言统计",
      "",
      buildMarkdownTable(["语言", "代码", "覆盖率", "完成", "缺翻译", "疑似未翻译"], languageRows) ||
        "当前没有目标语言。",
      "",
      "## 待处理条目",
      "",
      buildMarkdownTable(["序号", "状态", "语言", "章节", "场景", "位置", "字段", "原文", "译文"], issueRows) ||
        "当前没有明显多语言缺口。",
      "",
    ].join("\n")}`;
  }

  function buildLocalizationCoverageCsv(coverage = {}) {
    const rows = toArray(coverage.entries).map((entry, index) => [
      `${index + 1}`,
      entry.statusLabel,
      entry.languageLabel,
      entry.language,
      entry.kind,
      entry.targetId,
      entry.key,
      entry.optionIndex === null || entry.optionIndex === undefined ? "" : entry.optionIndex + 1,
      entry.chapterName,
      entry.sceneName,
      entry.locationLabel,
      entry.fieldLabel,
      entry.sourceText,
      entry.localizedText,
    ]);
    return `\uFEFF${buildCsv(
      ["序号", "状态", "语言", "语言代码", "类型", "目标ID", "字段键", "选项序号", "章节", "场景", "位置", "字段", "原文", "译文"],
      rows
    )}\n`;
  }

  function parseCsv(text = "") {
    const source = String(text ?? "").replace(/^\uFEFF/, "");
    const rows = [];
    let row = [];
    let cell = "";
    let inQuotes = false;

    for (let index = 0; index < source.length; index += 1) {
      const char = source[index];
      const nextChar = source[index + 1];
      if (inQuotes) {
        if (char === '"' && nextChar === '"') {
          cell += '"';
          index += 1;
        } else if (char === '"') {
          inQuotes = false;
        } else {
          cell += char;
        }
        continue;
      }
      if (char === '"') {
        inQuotes = true;
        continue;
      }
      if (char === ",") {
        row.push(cell);
        cell = "";
        continue;
      }
      if (char === "\n") {
        row.push(cell);
        rows.push(row);
        row = [];
        cell = "";
        continue;
      }
      if (char === "\r") {
        continue;
      }
      cell += char;
    }
    row.push(cell);
    rows.push(row);
    return rows.filter((candidate) => candidate.some((value) => cleanText(value)));
  }

  function getCsvValue(row = {}, ...headers) {
    for (const header of headers) {
      if (Object.hasOwn(row, header)) {
        return row[header];
      }
    }
    return "";
  }

  function parseLocalizationCoverageCsv(text = "") {
    const rows = parseCsv(text);
    const headers = toArray(rows[0]).map((header) => cleanText(header));
    return rows.slice(1).map((row, rowIndex) => {
      const mapped = {};
      headers.forEach((header, index) => {
        if (header) {
          mapped[header] = row[index] ?? "";
        }
      });
      return {
        rowNumber: rowIndex + 2,
        statusLabel: cleanText(getCsvValue(mapped, "状态", "Status")),
        languageLabel: cleanText(getCsvValue(mapped, "语言", "Language")),
        language: cleanText(getCsvValue(mapped, "语言代码", "Language Code", "language")),
        kind: cleanText(getCsvValue(mapped, "类型", "Kind", "kind")),
        targetId: cleanText(getCsvValue(mapped, "目标ID", "Target ID", "targetId")),
        key: cleanText(getCsvValue(mapped, "字段键", "Key", "key")),
        optionNumber: cleanText(getCsvValue(mapped, "选项序号", "Option", "optionNumber")),
        chapterName: cleanText(getCsvValue(mapped, "章节", "Chapter")),
        sceneName: cleanText(getCsvValue(mapped, "场景", "Scene")),
        locationLabel: cleanText(getCsvValue(mapped, "位置", "Location")),
        fieldLabel: cleanText(getCsvValue(mapped, "字段", "Field")),
        sourceText: cleanText(getCsvValue(mapped, "原文", "Source")),
        localizedText: cleanText(getCsvValue(mapped, "译文", "Translation", "localizedText")),
      };
    });
  }

  function findSceneById(data = {}, sceneId = "") {
    const cleanSceneId = cleanText(sceneId);
    if (!cleanSceneId) {
      return null;
    }
    const sceneEntry = getOrderedScenes(data).find(({ scene }) => cleanText(scene?.id) === cleanSceneId);
    return sceneEntry?.scene ?? null;
  }

  function findBlockInScenes(data = {}, blockId = "") {
    const cleanBlockId = cleanText(blockId);
    if (!cleanBlockId) {
      return null;
    }
    for (const { scene } of getOrderedScenes(data)) {
      const block = toArray(scene?.blocks).find((candidate) => cleanText(candidate?.id) === cleanBlockId);
      if (block) {
        return { scene, block };
      }
    }
    return null;
  }

  function getCurrentTranslation(source = {}, key = "", language = "") {
    return cleanText(getTranslationMap(source, key)[language]);
  }

  function pushImportSkip(skipped, row, reason) {
    skipped.push({
      rowNumber: row.rowNumber,
      reason,
      kind: row.kind,
      targetId: row.targetId,
      language: row.language,
      fieldLabel: row.fieldLabel,
      locationLabel: row.locationLabel,
    });
  }

  function buildLocalizationImportPlan(data = {}, csvText = "") {
    const rows = parseLocalizationCoverageCsv(csvText);
    const patches = [];
    const skipped = [];
    const supportedKinds = new Set(["scene", "block", "choice_option"]);
    const seenPatchKeys = new Set();

    rows.forEach((row) => {
      const language = normalizeLanguageCode(row.language);
      const key = cleanText(row.key);
      const text = cleanText(row.localizedText);
      const kind = cleanText(row.kind);
      const targetId = cleanText(row.targetId);

      if (!text) {
        pushImportSkip(skipped, row, "译文为空，已跳过。");
        return;
      }
      if (!language) {
        pushImportSkip(skipped, row, "语言代码为空，已跳过。");
        return;
      }
      if (!supportedKinds.has(kind)) {
        pushImportSkip(skipped, row, "当前安全导入只自动写入场景名、场景卡片和选项翻译。");
        return;
      }
      if (!targetId || !key) {
        pushImportSkip(skipped, row, "缺少目标ID或字段键，请使用编辑器导出的新版 CSV。");
        return;
      }

      if (kind === "scene") {
        const scene = findSceneById(data, targetId);
        if (!scene) {
          pushImportSkip(skipped, row, "找不到目标场景。");
          return;
        }
        if (key !== "name") {
          pushImportSkip(skipped, row, "场景翻译只支持 name 字段。");
          return;
        }
        if (getCurrentTranslation(scene, key, language) === text) {
          pushImportSkip(skipped, row, "译文与项目内现有内容相同。");
          return;
        }
        const patchKey = `scene:${targetId}:${key}:${language}`;
        if (seenPatchKeys.has(patchKey)) {
          pushImportSkip(skipped, row, "同一个目标在 CSV 中重复出现，已保留第一条。");
          return;
        }
        seenPatchKeys.add(patchKey);
        patches.push({ rowNumber: row.rowNumber, kind, sceneId: scene.id, chapterId: scene.chapterId, targetId, key, language, text });
        return;
      }

      const match = findBlockInScenes(data, targetId);
      if (!match) {
        pushImportSkip(skipped, row, "找不到目标卡片。");
        return;
      }

      if (kind === "block") {
        if (!["text", "title"].includes(key)) {
          pushImportSkip(skipped, row, "卡片翻译只支持 text 或 title 字段。");
          return;
        }
        if (getCurrentTranslation(match.block, key, language) === text) {
          pushImportSkip(skipped, row, "译文与项目内现有内容相同。");
          return;
        }
        const patchKey = `block:${targetId}:${key}:${language}`;
        if (seenPatchKeys.has(patchKey)) {
          pushImportSkip(skipped, row, "同一个目标在 CSV 中重复出现，已保留第一条。");
          return;
        }
        seenPatchKeys.add(patchKey);
        patches.push({
          rowNumber: row.rowNumber,
          kind,
          sceneId: match.scene.id,
          chapterId: match.scene.chapterId,
          targetId,
          key,
          language,
          text,
        });
        return;
      }

      const optionIndex = Number.parseInt(row.optionNumber, 10) - 1;
      const option = Number.isInteger(optionIndex) ? toArray(match.block?.options)[optionIndex] : null;
      if (!option) {
        pushImportSkip(skipped, row, "找不到目标选项。");
        return;
      }
      if (key !== "text") {
        pushImportSkip(skipped, row, "选项翻译只支持 text 字段。");
        return;
      }
      if (getCurrentTranslation(option, key, language) === text) {
        pushImportSkip(skipped, row, "译文与项目内现有内容相同。");
        return;
      }
      const patchKey = `choice_option:${targetId}:${optionIndex}:${key}:${language}`;
      if (seenPatchKeys.has(patchKey)) {
        pushImportSkip(skipped, row, "同一个目标在 CSV 中重复出现，已保留第一条。");
        return;
      }
      seenPatchKeys.add(patchKey);
      patches.push({
        rowNumber: row.rowNumber,
        kind,
        sceneId: match.scene.id,
        chapterId: match.scene.chapterId,
        targetId,
        key,
        optionIndex,
        language,
        text,
      });
    });

    return {
      rows,
      patches,
      skipped,
      summary: {
        rowCount: rows.length,
        patchCount: patches.length,
        skippedCount: skipped.length,
        sceneCount: new Set(patches.map((patch) => patch.sceneId)).size,
        languageCount: new Set(patches.map((patch) => patch.language)).size,
      },
    };
  }

  global.CanvasiaEditorLocalizationCoverage = Object.freeze({
    getSupportedLanguages,
    getLanguageLabel,
    buildLocalizationCoverage,
    getLocalizationCoverageStatusDigest,
    buildLocalizationCoverageMarkdown,
    buildLocalizationCoverageCsv,
    parseLocalizationCoverageCsv,
    buildLocalizationImportPlan,
  });
})(typeof window !== "undefined" ? window : globalThis);
