(function attachVariableInfluenceSheetTools(global) {
  const VARIABLE_TYPE_LABELS = Object.freeze({
    number: "数字",
    boolean: "开关",
    string: "文本",
  });

  const USAGE_LABELS = Object.freeze({
    set: "直接设置",
    add: "数值增减",
    choice: "选项后果",
    condition: "条件读取",
    choice_gate: "选项门控",
  });

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function getVariableTypeLabel(type = "") {
    return VARIABLE_TYPE_LABELS[type] ?? cleanText(type, "未知");
  }

  function getUsageLabel(kind = "") {
    return USAGE_LABELS[kind] ?? cleanText(kind, "引用");
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

  function buildVariableMap(data = {}) {
    const variableMap = new Map();
    [
      ...toArray(data.variables),
      ...toArray(data.project?.variables),
      ...toArray(data.projectSettings?.variables),
    ].forEach((variable) => {
      if (variable?.id) {
        variableMap.set(String(variable.id), variable);
      }
    });
    buildCollectionMap(data.variablesById).forEach((variable, id) => variableMap.set(id, variable));
    return variableMap;
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
    return new Map(
      toArray(data.chapters).map((chapter, index) => [
        String(chapter?.id ?? chapter?.chapterId ?? ""),
        {
          id: String(chapter?.id ?? chapter?.chapterId ?? ""),
          name: cleanText(chapter?.name ?? chapter?.title, `章节 ${index + 1}`),
          order: index,
          sceneOrder: toArray(chapter?.sceneOrder).map((sceneId) => String(sceneId ?? "")).filter(Boolean),
        },
      ])
    );
  }

  function getSceneRecords(data = {}) {
    const sceneMap = buildSceneMap(data);
    const chapterMap = buildChapterMap(data);
    const records = [];
    const seenSceneIds = new Set();

    toArray(data.chapters).forEach((chapter, chapterIndex) => {
      const chapterId = String(chapter?.id ?? chapter?.chapterId ?? "");
      const chapterName = cleanText(chapter?.name ?? chapter?.title, `章节 ${chapterIndex + 1}`);
      const directScenes = toArray(chapter?.scenes);
      const orderedIds = toArray(chapter?.sceneOrder).map((sceneId) => String(sceneId ?? "")).filter(Boolean);
      const scenes = directScenes.length
        ? directScenes
        : orderedIds.map((sceneId) => sceneMap.get(sceneId)).filter(Boolean);
      scenes.forEach((scene, sceneIndex) => {
        if (!scene?.id || seenSceneIds.has(String(scene.id))) {
          return;
        }
        seenSceneIds.add(String(scene.id));
        records.push({ scene, sceneIndex, chapterId, chapterName, chapterOrder: chapterIndex });
      });
    });

    toArray(data.scenes).forEach((scene, sceneIndex) => {
      if (!scene?.id || seenSceneIds.has(String(scene.id))) {
        return;
      }
      const chapter = chapterMap.get(String(scene.chapterId ?? ""));
      seenSceneIds.add(String(scene.id));
      records.push({
        scene,
        sceneIndex,
        chapterId: String(scene.chapterId ?? ""),
        chapterName: chapter?.name ?? "未分章",
        chapterOrder: chapter?.order ?? 9999,
      });
    });

    sceneMap.forEach((scene, id) => {
      if (!scene?.id || seenSceneIds.has(id)) {
        return;
      }
      seenSceneIds.add(id);
      records.push({
        scene,
        sceneIndex: records.length,
        chapterId: String(scene.chapterId ?? ""),
        chapterName: chapterMap.get(String(scene.chapterId ?? ""))?.name ?? "未分章",
        chapterOrder: chapterMap.get(String(scene.chapterId ?? ""))?.order ?? 9999,
      });
    });

    return records.sort((left, right) => {
      if (left.chapterOrder !== right.chapterOrder) {
        return left.chapterOrder - right.chapterOrder;
      }
      return left.sceneIndex - right.sceneIndex;
    });
  }

  function parseNumberBound(value) {
    if (value === null || value === undefined || typeof value === "boolean") {
      return null;
    }
    const number = Number.parseFloat(value);
    return Number.isFinite(number) ? number : null;
  }

  function isValueMatchingType(variable = {}, value) {
    if (!variable?.id) {
      return true;
    }
    if (variable.type === "number") {
      return typeof value === "number" && Number.isFinite(value);
    }
    if (variable.type === "boolean") {
      return typeof value === "boolean";
    }
    return typeof value === "string";
  }

  function formatValue(value) {
    if (typeof value === "boolean") {
      return value ? "true" : "false";
    }
    if (value === null || value === undefined) {
      return "";
    }
    return String(value);
  }

  function getVariableName(variableMap, variableId = "") {
    const id = cleanText(variableId);
    const variable = variableMap.get(id);
    return cleanText(variable?.name ?? variable?.label, id || "未选择变量");
  }

  function createVariableRecord(variable = {}) {
    return {
      variable,
      variableId: cleanText(variable.id),
      variableName: cleanText(variable.name ?? variable.label, variable.id),
      type: cleanText(variable.type, "string"),
      typeLabel: getVariableTypeLabel(variable.type),
      readCount: 0,
      writeCount: 0,
      setCount: 0,
      addCount: 0,
      choiceEffectCount: 0,
      conditionCount: 0,
      locations: [],
      references: [],
      issues: [],
      status: "good",
      statusLabel: "正常",
    };
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

  function pushIssue(target, severity, code, title, detail, context = {}) {
    target.push({ severity, code, title, detail, ...context });
  }

  function getStatusFromIssues(issues = []) {
    if (issues.some((issue) => issue.severity === "blocker")) {
      return "blocker";
    }
    if (issues.some((issue) => issue.severity === "warn")) {
      return "warn";
    }
    if (issues.length) {
      return "tip";
    }
    return "good";
  }

  function getStatusLabel(status) {
    if (status === "blocker") {
      return "先修";
    }
    if (status === "warn") {
      return "复查";
    }
    if (status === "tip") {
      return "整理";
    }
    return "正常";
  }

  function recordReference(records, unknownReferences, variableMap, reference = {}) {
    const variableId = cleanText(reference.variableId);
    const base = {
      chapterName: reference.chapterName,
      sceneName: reference.sceneName,
      sceneId: reference.sceneId,
      blockId: reference.blockId,
      blockIndex: reference.blockIndex,
      kind: reference.kind,
      kindLabel: getUsageLabel(reference.kind),
      label: reference.label,
      value: reference.value,
      valueLabel: formatValue(reference.value),
      optionText: reference.optionText,
      branchIndex: reference.branchIndex,
      ruleIndex: reference.ruleIndex,
    };

    if (!variableId || !variableMap.has(variableId)) {
      unknownReferences.push({
        ...base,
        variableId,
        variableName: variableId || "未选择变量",
      });
      return;
    }

    const record = records.get(variableId);
    if (!record) {
      return;
    }
    const variable = variableMap.get(variableId);
    const nextReference = {
      ...base,
      variableId,
      variableName: getVariableName(variableMap, variableId),
    };
    record.references.push(nextReference);
    if (record.locations.length < 5) {
      record.locations.push(base.label);
    }

    if (reference.kind === "condition" || reference.kind === "choice_gate") {
      record.readCount += 1;
      record.conditionCount += 1;
      if (!isValueMatchingType(variable, reference.value)) {
        pushIssue(
          record.issues,
          "blocker",
          "condition_value_type_mismatch",
          "条件比较值类型不对",
          `${record.variableName} 是 ${record.typeLabel}，但条件值是 ${formatValue(reference.value) || "空"}`,
          nextReference
        );
      }
      return;
    }

    record.writeCount += 1;
    if (reference.kind === "set") {
      record.setCount += 1;
      if (!isValueMatchingType(variable, reference.value)) {
        pushIssue(
          record.issues,
          "blocker",
          "variable_set_type_mismatch",
          "变量设置值类型不对",
          `${record.variableName} 是 ${record.typeLabel}，但设置值是 ${formatValue(reference.value) || "空"}`,
          nextReference
        );
      }
    } else if (reference.kind === "add") {
      record.addCount += 1;
      if (variable.type !== "number" || typeof reference.value !== "number" || !Number.isFinite(reference.value)) {
        pushIssue(
          record.issues,
          "blocker",
          "variable_add_type_mismatch",
          "变量加减只能用于数字变量",
          `${record.variableName} 是 ${record.typeLabel}，不能用作数字加减。`,
          nextReference
        );
      }
    } else if (reference.kind === "choice") {
      record.choiceEffectCount += 1;
      if (reference.effectType === "variable_add") {
        record.addCount += 1;
        if (variable.type !== "number" || typeof reference.value !== "number" || !Number.isFinite(reference.value)) {
          pushIssue(
            record.issues,
            "blocker",
            "choice_add_type_mismatch",
            "选项变量加减不合法",
            `${record.variableName} 是 ${record.typeLabel}，不能在选项里使用“变量增加”。`,
            nextReference
          );
        }
      } else if (!isValueMatchingType(variable, reference.value)) {
        record.setCount += 1;
        pushIssue(
          record.issues,
          "blocker",
          "choice_set_type_mismatch",
          "选项变量设置值类型不对",
          `${record.variableName} 是 ${record.typeLabel}，但选项设置值是 ${formatValue(reference.value) || "空"}`,
          nextReference
        );
      } else {
        record.setCount += 1;
      }
    }
  }

  function inspectVariableDefinition(record) {
    const variable = record.variable ?? {};
    const defaultValue = variable.defaultValue;

    if (!cleanText(variable.id)) {
      pushIssue(record.issues, "blocker", "variable_missing_id", "变量缺少 ID", "变量 ID 不能为空，否则剧情卡无法稳定引用。", {
        variableId: record.variableId,
        variableName: record.variableName,
      });
    }
    if (!["number", "boolean", "string"].includes(variable.type)) {
      pushIssue(record.issues, "warn", "variable_unknown_type", "变量类型不认识", `当前类型：${variable.type || "空"}，运行时会倾向按文本处理。`, {
        variableId: record.variableId,
        variableName: record.variableName,
      });
    }
    if (!isValueMatchingType(variable, defaultValue)) {
      pushIssue(record.issues, "blocker", "variable_default_type_mismatch", "变量默认值类型不对", "默认值类型需要和变量类型一致。", {
        variableId: record.variableId,
        variableName: record.variableName,
      });
    }
    if (variable.type === "number") {
      const minValue = parseNumberBound(variable.min ?? variable.minValue);
      const maxValue = parseNumberBound(variable.max ?? variable.maxValue);
      if ((variable.min ?? variable.minValue) != null && minValue === null) {
        pushIssue(record.issues, "warn", "variable_min_invalid", "数字变量最小值无效", "最小值不是有效数字。", {
          variableId: record.variableId,
          variableName: record.variableName,
        });
      }
      if ((variable.max ?? variable.maxValue) != null && maxValue === null) {
        pushIssue(record.issues, "warn", "variable_max_invalid", "数字变量最大值无效", "最大值不是有效数字。", {
          variableId: record.variableId,
          variableName: record.variableName,
        });
      }
      if (minValue !== null && maxValue !== null && minValue > maxValue) {
        pushIssue(record.issues, "blocker", "variable_range_reversed", "数字变量范围上下限反了", "最小值不能大于最大值。", {
          variableId: record.variableId,
          variableName: record.variableName,
        });
      }
      if (
        typeof defaultValue === "number" &&
        ((minValue !== null && defaultValue < minValue) || (maxValue !== null && defaultValue > maxValue))
      ) {
        pushIssue(record.issues, "warn", "variable_default_out_of_range", "默认值超出数字范围", "默认值会被运行时限制或造成判断偏差。", {
          variableId: record.variableId,
          variableName: record.variableName,
        });
      }
    }
  }

  function addRecordLevelUsageIssues(record) {
    if (record.references.length === 0) {
      pushIssue(record.issues, "tip", "variable_unused", "变量未被剧情引用", "如果不是预留变量，发布前可以考虑删除或改为备用分组。", {
        variableId: record.variableId,
        variableName: record.variableName,
      });
    } else if (record.writeCount > 0 && record.readCount === 0) {
      pushIssue(record.issues, "warn", "variable_written_never_read", "变量被写入但没有条件读取", "这个变量会变化，但暂时不会影响任何分支；如果它是路线标记，建议补条件或说明用途。", {
        variableId: record.variableId,
        variableName: record.variableName,
      });
    } else if (record.readCount > 0 && record.writeCount === 0) {
      pushIssue(record.issues, "tip", "variable_read_default_only", "条件只读取默认值", "这个变量被条件判断读取，但没有剧情卡或选项修改它，分支可能永远固定。", {
        variableId: record.variableId,
        variableName: record.variableName,
      });
    }
  }

  function collectReferences(data = {}, variableMap = new Map()) {
    const records = new Map(Array.from(variableMap.values()).map((variable) => [String(variable.id ?? ""), createVariableRecord(variable)]));
    const unknownReferences = [];

    getSceneRecords(data).forEach(({ scene, chapterName }) => {
      const sceneName = cleanText(scene?.name ?? scene?.title, scene?.id ?? "未命名场景");
      const sceneId = cleanText(scene?.id);
      toArray(scene?.blocks).forEach((block, blockIndex) => {
        const blockId = cleanText(block?.id, `block_${blockIndex + 1}`);
        const base = {
          chapterName,
          sceneName,
          sceneId,
          blockId,
          blockIndex,
          label: `${chapterName} / ${sceneName} / 第 ${blockIndex + 1} 张`,
        };
        if (block?.type === "variable_set") {
          recordReference(records, unknownReferences, variableMap, {
            ...base,
            kind: "set",
            variableId: block.variableId,
            value: block.value,
          });
        }
        if (block?.type === "variable_add") {
          recordReference(records, unknownReferences, variableMap, {
            ...base,
            kind: "add",
            variableId: block.variableId,
            value: block.value,
          });
        }
        if (block?.type === "choice") {
          toArray(block.options).forEach((option, optionIndex) => {
            toArray(option.choiceAvailabilityWhen).forEach((rule, ruleIndex) => {
              recordReference(records, unknownReferences, variableMap, {
                ...base,
                kind: "choice_gate",
                variableId: rule.variableId,
                value: rule.value,
                optionText: cleanText(option.text, `选项 ${optionIndex + 1}`),
                optionIndex,
                ruleIndex,
              });
            });
            toArray(option.effects).forEach((effect, effectIndex) => {
              recordReference(records, unknownReferences, variableMap, {
                ...base,
                kind: "choice",
                variableId: effect.variableId,
                value: effect.value,
                effectType: effect.type,
                optionText: cleanText(option.text, `选项 ${optionIndex + 1}`),
                optionIndex,
                effectIndex,
              });
            });
          });
        }
        if (block?.type === "condition") {
          toArray(block.branches).forEach((branch, branchIndex) => {
            toArray(branch.when).forEach((rule, ruleIndex) => {
              recordReference(records, unknownReferences, variableMap, {
                ...base,
                kind: "condition",
                variableId: rule.variableId,
                value: rule.value,
                branchIndex,
                ruleIndex,
              });
            });
          });
        }
      });
    });

    return { records, unknownReferences };
  }

  function buildVariableInfluenceSheet(data = {}) {
    const variableMap = buildVariableMap(data);
    const { records, unknownReferences } = collectReferences(data, variableMap);
    const issues = [];
    const variableRecords = Array.from(records.values());

    variableRecords.forEach((record) => {
      inspectVariableDefinition(record);
      addRecordLevelUsageIssues(record);
      record.status = getStatusFromIssues(record.issues);
      record.statusLabel = getStatusLabel(record.status);
      issues.push(...record.issues);
    });

    unknownReferences.forEach((reference) => {
      issues.push({
        severity: "blocker",
        code: reference.variableId ? "variable_reference_unknown" : "variable_reference_missing",
        title: reference.variableId ? "引用了不存在的变量" : "变量引用为空",
        detail: reference.variableId ? `变量 ${reference.variableId} 不在变量库中。` : "剧情逻辑卡没有选择变量。",
        ...reference,
      });
    });

    issues.sort((left, right) => getIssueWeight(right) - getIssueWeight(left) || cleanText(left.variableName).localeCompare(cleanText(right.variableName), "zh-CN"));

    const references = variableRecords.flatMap((record) => record.references);
    const summary = {
      variableCount: variableRecords.length,
      referencedVariableCount: variableRecords.filter((record) => record.references.length > 0).length,
      unusedVariableCount: variableRecords.filter((record) => record.references.length === 0).length,
      readCount: variableRecords.reduce((total, record) => total + record.readCount, 0),
      writeCount: variableRecords.reduce((total, record) => total + record.writeCount, 0),
      choiceEffectCount: variableRecords.reduce((total, record) => total + record.choiceEffectCount, 0),
      conditionCount: variableRecords.reduce((total, record) => total + record.conditionCount, 0),
      unknownReferenceCount: unknownReferences.length,
      writtenNeverReadCount: issues.filter((issue) => issue.code === "variable_written_never_read").length,
      readDefaultOnlyCount: issues.filter((issue) => issue.code === "variable_read_default_only").length,
      blockerCount: issues.filter((issue) => issue.severity === "blocker").length,
      warningCount: issues.filter((issue) => issue.severity === "warn").length,
      tipCount: issues.filter((issue) => issue.severity === "tip").length,
    };

    return {
      projectTitle: cleanText(data.project?.title, "Canvasia Project"),
      variables: variableRecords,
      references,
      unknownReferences,
      issues,
      summary,
    };
  }

  function getVariableInfluenceStatusDigest(sheet = {}) {
    const summary = sheet.summary ?? {};
    if ((summary.variableCount ?? 0) === 0) {
      return {
        status: "empty",
        tone: "soft",
        title: "还没有变量影响表",
        detail: "项目里暂时没有变量。需要好感度、路线旗标或开关时，可以先补基础变量包。",
      };
    }
    if ((summary.blockerCount ?? 0) > 0) {
      return {
        status: "blocked",
        tone: "danger",
        title: `有 ${summary.blockerCount} 个变量逻辑阻塞`,
        detail: "优先修复坏变量引用、类型不匹配、数字范围错误和不合法加减。",
      };
    }
    if ((summary.warningCount ?? 0) > 0) {
      return {
        status: "warn",
        tone: "warn",
        title: `有 ${summary.warningCount} 个变量逻辑提醒`,
        detail: "项目可以继续制作，但建议复查写入后未读取、默认值范围和可读性。",
      };
    }
    return {
      status: "ready",
      tone: "good",
      title: "变量影响关系比较清晰",
      detail: "当前变量定义、写入和条件读取没有明显结构风险。",
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

  function buildVariableInfluenceMarkdown(sheet = {}, context = {}) {
    const digest = getVariableInfluenceStatusDigest(sheet);
    const summary = sheet.summary ?? {};
    const projectTitle = context.projectTitle || sheet.projectTitle || "Canvasia Project";
    const generatedAt = context.generatedAt || new Date().toISOString();
    const variableRows = toArray(sheet.variables).slice(0, 160).map((record, index) => [
      `${index + 1}`,
      record.variableName,
      record.variableId,
      record.typeLabel,
      `${record.writeCount}`,
      `${record.readCount}`,
      `${record.choiceEffectCount}`,
      `${record.conditionCount}`,
      record.statusLabel,
      record.locations.join(" / "),
    ]);
    const issueRows = toArray(sheet.issues).slice(0, 160).map((issue, index) => [
      `${index + 1}`,
      issue.severity === "blocker" ? "阻塞" : issue.severity === "warn" ? "提醒" : "整理",
      issue.variableName ?? issue.variableId,
      issue.kindLabel ?? "",
      issue.chapterName ?? "",
      issue.sceneName ?? "",
      issue.title,
      issue.detail,
    ]);

    return `\uFEFF${[
      `# ${projectTitle} 变量影响表`,
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
          ["变量", `${summary.variableCount ?? 0}`],
          ["被引用变量", `${summary.referencedVariableCount ?? 0}`],
          ["未引用变量", `${summary.unusedVariableCount ?? 0}`],
          ["写入次数", `${summary.writeCount ?? 0}`],
          ["条件读取", `${summary.readCount ?? 0}`],
          ["未知引用", `${summary.unknownReferenceCount ?? 0}`],
          ["阻塞问题", `${summary.blockerCount ?? 0}`],
          ["复查提醒", `${summary.warningCount ?? 0}`],
        ]
      ),
      "",
      "## 变量影响清单",
      "",
      buildMarkdownTable(["序号", "变量", "ID", "类型", "写入", "读取", "选项效果", "条件", "状态", "位置示例"], variableRows) ||
        "当前没有可列出的变量。",
      "",
      "## 需要复查的问题",
      "",
      buildMarkdownTable(["序号", "级别", "变量", "用途", "章节", "场景", "问题", "说明"], issueRows) || "当前没有明显变量逻辑问题。",
      "",
    ].join("\n")}`;
  }

  function buildVariableInfluenceCsv(sheet = {}) {
    const rows = toArray(sheet.variables).map((record, index) => [
      `${index + 1}`,
      record.variableName,
      record.variableId,
      record.typeLabel,
      record.writeCount,
      record.readCount,
      record.setCount,
      record.addCount,
      record.choiceEffectCount,
      record.conditionCount,
      record.statusLabel,
      record.locations.join(" / "),
      record.issues.map((issue) => issue.title).join(" / "),
    ]);
    return `\uFEFF${buildCsv(
      ["序号", "变量", "ID", "类型", "写入", "读取", "直接设置", "数值增减", "选项效果", "条件读取", "状态", "位置示例", "问题"],
      rows
    )}\n`;
  }

  global.CanvasiaEditorVariableInfluenceSheet = Object.freeze({
    buildVariableInfluenceSheet,
    getVariableInfluenceStatusDigest,
    buildVariableInfluenceMarkdown,
    buildVariableInfluenceCsv,
    getVariableTypeLabel,
    getUsageLabel,
  });
})(typeof window !== "undefined" ? window : globalThis);
