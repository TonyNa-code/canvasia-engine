(function attachChoiceConsequenceSheetTools(global) {
  const CHOICE_EFFECT_LABELS = Object.freeze({
    variable_add: "变量增加",
    variable_set: "变量设为",
  });

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function buildSceneMap(data = {}) {
    const sceneMap = new Map();
    toArray(data.scenes).forEach((scene) => {
      if (scene?.id) {
        sceneMap.set(String(scene.id), scene);
      }
    });
    if (data.scenesById instanceof Map) {
      data.scenesById.forEach((scene, id) => {
        if (id) {
          sceneMap.set(String(id), scene);
        }
      });
    } else if (data.scenesById && typeof data.scenesById === "object") {
      Object.entries(data.scenesById).forEach(([id, scene]) => {
        if (id) {
          sceneMap.set(String(id), scene);
        }
      });
    }
    return sceneMap;
  }

  function getOrderedScenes(data = {}) {
    const sceneMap = buildSceneMap(data);
    if (Array.isArray(data.scenes) && data.scenes.length) {
      const chapterOrder = new Map(toArray(data.chapters).map((chapter, index) => [String(chapter?.id ?? chapter?.chapterId ?? ""), index]));
      return data.scenes
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
    return Array.from(sceneMap.values());
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

  function buildVariableMap(data = {}) {
    const variableMap = new Map();
    const variables = [
      ...toArray(data.variables),
      ...toArray(data.project?.variables),
      ...toArray(data.projectSettings?.variables),
    ];
    variables.forEach((variable) => {
      if (variable?.id) {
        variableMap.set(String(variable.id), variable);
      }
    });
    if (data.variablesById instanceof Map) {
      data.variablesById.forEach((variable, id) => {
        if (id) {
          variableMap.set(String(id), variable);
        }
      });
    } else if (data.variablesById && typeof data.variablesById === "object") {
      Object.entries(data.variablesById).forEach(([id, variable]) => {
        if (id) {
          variableMap.set(String(id), variable);
        }
      });
    }
    return variableMap;
  }

  function getSceneName(sceneMap, sceneId = "") {
    const id = cleanText(sceneId);
    const scene = sceneMap.get(id);
    return cleanText(scene?.name ?? scene?.title, id || "继续当前场景");
  }

  function getVariableName(variableMap, variableId = "") {
    const id = cleanText(variableId);
    const variable = variableMap.get(id);
    return cleanText(variable?.name ?? variable?.label, id || "未选择变量");
  }

  function getVariableType(variableMap, variableId = "") {
    const variable = variableMap.get(cleanText(variableId));
    return cleanText(variable?.type, "");
  }

  function getEffectTypeLabel(type = "") {
    return CHOICE_EFFECT_LABELS[type] ?? cleanText(type, "未知效果");
  }

  function formatEffectValue(value) {
    if (typeof value === "boolean") {
      return value ? "true" : "false";
    }
    if (value == null) {
      return "";
    }
    return String(value);
  }

  function summarizeChoiceEffect(effect = {}, variableMap = new Map()) {
    const type = cleanText(effect.type);
    const variableId = cleanText(effect.variableId);
    const variableName = getVariableName(variableMap, variableId);
    const value = formatEffectValue(effect.value);
    if (type === "variable_add") {
      return `${variableName} + ${value || "1"}`;
    }
    if (type === "variable_set") {
      return `${variableName} = ${value}`;
    }
    return `${getEffectTypeLabel(type)} ${variableName}${value ? ` ${value}` : ""}`.trim();
  }

  function getEffectKey(effect = {}) {
    return [cleanText(effect.type), cleanText(effect.variableId), formatEffectValue(effect.value)].join(":");
  }

  function getOptionOutcomeKey(option = {}) {
    const effects = toArray(option.effects).map(getEffectKey).sort().join("|");
    return [cleanText(option.gotoSceneId), effects].join("=>");
  }

  function pushIssue(issues, severity, code, title, detail, context = {}) {
    issues.push({ severity, code, title, detail, ...context });
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
      return "润色";
    }
    return "正常";
  }

  function getOptionIssueContext(option = {}) {
    return {
      chapterName: option.chapterName,
      sceneName: option.sceneName,
      sceneId: option.sceneId,
      blockId: option.blockId,
      blockIndex: option.blockIndex,
      optionIndex: option.optionIndex,
      optionText: option.optionText,
    };
  }

  function inspectChoiceEffect(effect = {}, context = {}) {
    const issues = [];
    const type = cleanText(effect.type);
    const variableId = cleanText(effect.variableId);
    const variableType = getVariableType(context.variableMap, variableId);
    const baseContext = context.baseContext ?? {};

    if (!["variable_add", "variable_set"].includes(type)) {
      pushIssue(issues, "warn", "choice_effect_unknown_type", "选项效果类型未知", `当前效果类型：${type || "空"}`, baseContext);
    }
    if (!variableId) {
      pushIssue(issues, "blocker", "choice_effect_missing_variable", "选项效果缺少变量", "这个选项效果没有选择要修改的变量。", baseContext);
    } else if (!context.variableMap.has(variableId)) {
      pushIssue(issues, "blocker", "choice_effect_unknown_variable", "选项效果变量不存在", `变量 ${variableId} 不在当前变量库里。`, baseContext);
    } else if (type === "variable_add" && variableType && variableType !== "number") {
      pushIssue(
        issues,
        "blocker",
        "choice_effect_add_non_number",
        "非数字变量不能增加",
        `${getVariableName(context.variableMap, variableId)} 是 ${variableType} 类型，不能使用“变量增加”。`,
        baseContext
      );
    }
    return issues;
  }

  function buildChoiceOptionEntry(option = {}, context = {}) {
    const optionText = cleanText(option.text);
    const targetSceneId = cleanText(option.gotoSceneId);
    const effects = toArray(option.effects);
    const baseContext = {
      chapterName: context.chapterName,
      sceneName: context.sceneName,
      sceneId: context.sceneId,
      blockId: context.blockId,
      blockIndex: context.blockIndex,
      optionIndex: context.optionIndex,
      optionText: optionText || `选项 ${context.optionIndex + 1}`,
    };
    const issues = [];

    if (!optionText) {
      pushIssue(issues, "blocker", "choice_option_empty_text", "选项文案为空", "玩家会看到空按钮或难以理解的选项。", baseContext);
    }
    if (targetSceneId && !context.sceneMap.has(targetSceneId)) {
      pushIssue(issues, "blocker", "choice_option_unknown_target", "选项目标场景不存在", `目标场景 ${targetSceneId} 已经找不到。`, baseContext);
    }
    if (!targetSceneId && effects.length === 0) {
      pushIssue(
        issues,
        "warn",
        "choice_option_no_consequence",
        "选项没有路线或变量后果",
        "这个选项既不跳转，也不修改变量，玩家容易觉得是假按钮。",
        baseContext
      );
    }

    effects.forEach((effect) => {
      issues.push(...inspectChoiceEffect(effect, { variableMap: context.variableMap, baseContext }));
    });

    const status = getStatusFromIssues(issues);
    return {
      ...baseContext,
      optionId: cleanText(option.id, `${context.blockId}_option_${context.optionIndex + 1}`),
      targetSceneId,
      targetSceneName: getSceneName(context.sceneMap, targetSceneId),
      hasTarget: Boolean(targetSceneId),
      effectCount: effects.length,
      effectSummary: effects.length
        ? effects.map((effect) => summarizeChoiceEffect(effect, context.variableMap)).join(" / ")
        : "无变量后果",
      outcomeKey: getOptionOutcomeKey(option),
      status,
      statusLabel: getStatusLabel(status),
      issues,
    };
  }

  function inspectChoiceBlock(block = {}, context = {}) {
    const options = toArray(block.options);
    const blockContext = {
      chapterName: context.chapterName,
      sceneName: context.sceneName,
      sceneId: context.sceneId,
      blockId: cleanText(block.id, `choice_${context.blockIndex + 1}`),
      blockIndex: context.blockIndex,
    };
    const issues = [];
    if (options.length === 0) {
      pushIssue(issues, "blocker", "choice_block_without_options", "选项卡没有选项", "玩家走到这里会没有可点内容。", blockContext);
    }
    if (options.length > 5) {
      pushIssue(issues, "tip", "choice_block_crowded", "选项数量偏多", `当前有 ${options.length} 个选项，建议确认按钮区不会拥挤。`, blockContext);
    }

    const optionEntries = options.map((option, optionIndex) =>
      buildChoiceOptionEntry(option, {
        ...context,
        ...blockContext,
        optionIndex,
      })
    );

    const textGroups = new Map();
    optionEntries.forEach((option) => {
      const key = cleanText(option.optionText);
      if (!key) {
        return;
      }
      textGroups.set(key, [...(textGroups.get(key) ?? []), option]);
    });
    textGroups.forEach((group) => {
      if (group.length > 1) {
        group.forEach((option) => {
          pushIssue(
            option.issues,
            "warn",
            "choice_duplicate_text",
            "选项文案重复",
            `同一组选项中有 ${group.length} 个“${option.optionText}”。`,
            getOptionIssueContext(option)
          );
        });
      }
    });

    const actionableOptions = optionEntries.filter((option) => option.hasTarget || option.effectCount > 0);
    const outcomeGroups = new Map();
    actionableOptions.forEach((option) => {
      outcomeGroups.set(option.outcomeKey, [...(outcomeGroups.get(option.outcomeKey) ?? []), option]);
    });
    outcomeGroups.forEach((group) => {
      if (group.length > 1 && group.length === actionableOptions.length) {
        group.forEach((option) => {
          pushIssue(
            option.issues,
            "warn",
            "choice_same_consequence",
            "所有选项后果相同",
            "这组选项的跳转和变量效果完全一致；如果是故意伪装路线，建议至少记录一个变量或改文案说明差异。",
            getOptionIssueContext(option)
          );
        });
      }
    });

    optionEntries.forEach((option) => {
      option.status = getStatusFromIssues(option.issues);
      option.statusLabel = getStatusLabel(option.status);
    });

    issues.push(...optionEntries.flatMap((option) => option.issues));
    const status = getStatusFromIssues(issues);
    return {
      ...blockContext,
      optionCount: optionEntries.length,
      actionableOptionCount: actionableOptions.length,
      sameOutcomeGroupCount: [...outcomeGroups.values()].filter((group) => group.length > 1).length,
      status,
      statusLabel: getStatusLabel(status),
      issues,
      options: optionEntries,
    };
  }

  function buildChoiceConsequenceSheet(data = {}) {
    const sceneMap = buildSceneMap(data);
    const variableMap = buildVariableMap(data);
    const chapterMap = buildChapterMap(data);
    const choiceBlocks = [];

    getOrderedScenes(data).forEach((scene, sceneIndex) => {
      const chapter = chapterMap.get(String(scene?.chapterId ?? "")) ?? { name: "未分章" };
      const sceneName = cleanText(scene?.name ?? scene?.title, `场景 ${sceneIndex + 1}`);
      const sceneId = cleanText(scene?.id);
      toArray(scene?.blocks).forEach((block, blockIndex) => {
        if (block?.type !== "choice") {
          return;
        }
        choiceBlocks.push(
          inspectChoiceBlock(block, {
            chapterName: chapter.name,
            sceneName,
            sceneId,
            blockIndex,
            sceneMap,
            variableMap,
          })
        );
      });
    });

    const options = choiceBlocks.flatMap((block) => block.options);
    const issues = choiceBlocks
      .flatMap((block) => block.issues)
      .sort((left, right) => getIssueWeight(right) - getIssueWeight(left) || left.sceneName.localeCompare(right.sceneName, "zh-CN"));
    const summary = {
      choiceBlockCount: choiceBlocks.length,
      optionCount: options.length,
      actionableOptionCount: options.filter((option) => option.hasTarget || option.effectCount > 0).length,
      variableEffectCount: options.reduce((total, option) => total + option.effectCount, 0),
      noConsequenceCount: issues.filter((issue) => issue.code === "choice_option_no_consequence").length,
      sameConsequenceCount: issues.filter((issue) => issue.code === "choice_same_consequence").length,
      brokenTargetCount: issues.filter((issue) => issue.code === "choice_option_unknown_target").length,
      brokenVariableCount: issues.filter((issue) =>
        ["choice_effect_missing_variable", "choice_effect_unknown_variable", "choice_effect_add_non_number"].includes(issue.code)
      ).length,
      blockerCount: issues.filter((issue) => issue.severity === "blocker").length,
      warningCount: issues.filter((issue) => issue.severity === "warn").length,
      tipCount: issues.filter((issue) => issue.severity === "tip").length,
    };

    return {
      projectTitle: cleanText(data.project?.title, "Canvasia Project"),
      choiceBlocks,
      options,
      issues,
      summary,
    };
  }

  function getChoiceConsequenceStatusDigest(sheet = {}) {
    const summary = sheet.summary ?? {};
    if ((summary.choiceBlockCount ?? 0) === 0) {
      return {
        status: "empty",
        tone: "soft",
        title: "还没有选项后果表",
        detail: "项目里暂时没有选项卡。需要分支路线时，可以先在剧情页插入选项。",
      };
    }
    if ((summary.blockerCount ?? 0) > 0) {
      return {
        status: "blocked",
        tone: "danger",
        title: `有 ${summary.blockerCount} 个选项阻塞问题`,
        detail: "优先修复空选项、坏跳转、坏变量或不合法的变量增加效果。",
      };
    }
    if ((summary.warningCount ?? 0) > 0) {
      return {
        status: "warn",
        tone: "warn",
        title: `有 ${summary.warningCount} 个选项后果提醒`,
        detail: "项目可以继续制作，但建议复查无后果选项、重复选项和后果完全相同的分支。",
      };
    }
    return {
      status: "ready",
      tone: "good",
      title: "选项后果比较清晰",
      detail: "当前选项都有可解释的路线或变量后果，适合进入试玩复核。",
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

  function buildChoiceConsequenceMarkdown(sheet = {}, context = {}) {
    const digest = getChoiceConsequenceStatusDigest(sheet);
    const summary = sheet.summary ?? {};
    const projectTitle = context.projectTitle || sheet.projectTitle || "Canvasia Project";
    const generatedAt = context.generatedAt || new Date().toISOString();
    const optionRows = toArray(sheet.options).slice(0, 180).map((option, index) => [
      `${index + 1}`,
      option.chapterName,
      option.sceneName,
      option.blockIndex + 1,
      option.optionText,
      option.targetSceneName,
      option.effectSummary,
      option.statusLabel,
    ]);
    const issueRows = toArray(sheet.issues).slice(0, 160).map((issue, index) => [
      `${index + 1}`,
      issue.severity === "blocker" ? "阻塞" : issue.severity === "warn" ? "提醒" : "润色",
      issue.chapterName,
      issue.sceneName,
      issue.optionText ?? issue.blockId,
      issue.title,
      issue.detail,
    ]);

    return `\uFEFF${[
      `# ${projectTitle} 选项后果表`,
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
          ["选项卡", `${summary.choiceBlockCount ?? 0}`],
          ["选项按钮", `${summary.optionCount ?? 0}`],
          ["有路线或变量后果", `${summary.actionableOptionCount ?? 0}`],
          ["变量效果", `${summary.variableEffectCount ?? 0}`],
          ["无后果选项", `${summary.noConsequenceCount ?? 0}`],
          ["同后果提醒", `${summary.sameConsequenceCount ?? 0}`],
          ["阻塞问题", `${summary.blockerCount ?? 0}`],
          ["复查提醒", `${summary.warningCount ?? 0}`],
        ]
      ),
      "",
      "## 选项后果",
      "",
      buildMarkdownTable(["序号", "章节", "场景", "卡片", "选项", "目标场景", "变量效果", "状态"], optionRows) ||
        "当前没有可列出的选项。",
      "",
      "## 需要复查的问题",
      "",
      buildMarkdownTable(["序号", "级别", "章节", "场景", "选项", "问题", "说明"], issueRows) || "当前没有明显选项后果问题。",
      "",
    ].join("\n")}`;
  }

  function buildChoiceConsequenceCsv(sheet = {}) {
    const rows = toArray(sheet.options).map((option, index) => [
      `${index + 1}`,
      option.chapterName,
      option.sceneName,
      option.blockIndex + 1,
      option.optionIndex + 1,
      option.optionText,
      option.targetSceneId,
      option.targetSceneName,
      option.effectCount,
      option.effectSummary,
      option.statusLabel,
      toArray(option.issues).map((issue) => issue.title).join(" / "),
    ]);
    return `\uFEFF${buildCsv(
      ["序号", "章节", "场景", "卡片", "选项序号", "选项文案", "目标场景ID", "目标场景", "变量效果数", "变量效果", "状态", "问题"],
      rows
    )}\n`;
  }

  global.CanvasiaEditorChoiceConsequenceSheet = Object.freeze({
    buildChoiceConsequenceSheet,
    getChoiceConsequenceStatusDigest,
    buildChoiceConsequenceMarkdown,
    buildChoiceConsequenceCsv,
    summarizeChoiceEffect,
    getEffectTypeLabel,
  });
})(typeof window !== "undefined" ? window : globalThis);
