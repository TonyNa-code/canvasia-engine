(function attachPlaytestHandoffReportTools(global) {
  const regressionDiagnosticTools = global.CanvasiaEditorRegressionDiagnostics;

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function toCount(value, fallback = 0) {
    const numberValue = Number(value);
    return Number.isFinite(numberValue) ? Math.max(0, Math.round(numberValue)) : fallback;
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

  function parseCsvRows(text = "") {
    const rows = [];
    let row = [];
    let cell = "";
    let inQuotes = false;
    const source = String(text ?? "").replace(/^\uFEFF/, "");

    for (let index = 0; index < source.length; index += 1) {
      const char = source[index];
      const nextChar = source[index + 1];
      if (char === '"' && inQuotes && nextChar === '"') {
        cell += '"';
        index += 1;
        continue;
      }
      if (char === '"') {
        inQuotes = !inQuotes;
        continue;
      }
      if (char === "," && !inQuotes) {
        row.push(cell);
        cell = "";
        continue;
      }
      if ((char === "\n" || char === "\r") && !inQuotes) {
        if (char === "\r" && nextChar === "\n") {
          index += 1;
        }
        row.push(cell);
        if (row.some((item) => String(item ?? "").trim())) {
          rows.push(row);
        }
        row = [];
        cell = "";
        continue;
      }
      cell += char;
    }

    row.push(cell);
    if (row.some((item) => String(item ?? "").trim())) {
      rows.push(row);
    }
    return rows;
  }

  function normalizeHeader(value) {
    return String(value ?? "").trim().toLowerCase().replace(/\s+/g, "");
  }

  function getCsvCell(row = [], headerIndex = {}, names = []) {
    for (const name of names) {
      const index = headerIndex.get(normalizeHeader(name));
      if (Number.isInteger(index)) {
        return String(row[index] ?? "").trim();
      }
    }
    return "";
  }

  function getPlaytestFeedbackSeverityWeight(severity = "") {
    const value = String(severity ?? "").toLowerCase();
    if (/阻塞|blocker|critical|fatal|卡死|无法继续/.test(value)) {
      return 100;
    }
    if (/明显|严重|major|high|important/.test(value)) {
      return 70;
    }
    if (/轻微|minor|low|small/.test(value)) {
      return 35;
    }
    if (/建议|suggest|idea|优化/.test(value)) {
      return 15;
    }
    return value.trim() ? 30 : 20;
  }

  function getPlaytestFeedbackSeverityLabel(severity = "") {
    const value = String(severity ?? "").trim();
    if (!value) {
      return "未分级";
    }
    if (getPlaytestFeedbackSeverityWeight(value) >= 100) {
      return "阻塞";
    }
    if (getPlaytestFeedbackSeverityWeight(value) >= 70) {
      return "明显问题";
    }
    if (getPlaytestFeedbackSeverityWeight(value) >= 35) {
      return "轻微问题";
    }
    return "建议";
  }

  function normalizePlaytestFeedbackIssue(row = [], headerIndex = {}, index = 0) {
    const type = getCsvCell(row, headerIndex, ["类型", "type"]);
    const chapterName = getCsvCell(row, headerIndex, ["章节", "chapter"]);
    const sceneName = getCsvCell(row, headerIndex, ["场景", "scene"]);
    const routeTarget = getCsvCell(row, headerIndex, ["路线/目标", "路线", "目标", "route/target", "target"]);
    const severity = getCsvCell(row, headerIndex, ["严重程度", "severity"]);
    const category = getCsvCell(row, headerIndex, ["问题分类", "分类", "category"]);
    const steps = getCsvCell(row, headerIndex, ["复现步骤", "steps"]);
    const expected = getCsvCell(row, headerIndex, ["期望表现", "expected"]);
    const actual = getCsvCell(row, headerIndex, ["实际表现", "actual"]);
    const evidence = getCsvCell(row, headerIndex, ["截图/录屏", "截图", "录屏", "evidence"]);
    const note = getCsvCell(row, headerIndex, ["备注", "note"]);
    const hasIssueText = [severity, category, steps, expected, actual, evidence, note].some(Boolean);

    if (!hasIssueText || type === "项目") {
      return null;
    }

    const severityWeight = getPlaytestFeedbackSeverityWeight(severity || category || actual);
    return {
      id: `feedback-${index + 1}`,
      order: index + 1,
      type,
      chapterName,
      sceneName,
      routeTarget,
      severity,
      severityLabel: getPlaytestFeedbackSeverityLabel(severity || category || actual),
      severityWeight,
      category: category || "未分类",
      steps,
      expected,
      actual,
      evidence,
      note,
      summary: actual || note || steps || routeTarget || sceneName || "测试反馈",
    };
  }

  function parsePlaytestFeedbackCsv(text = "") {
    const rows = parseCsvRows(text);
    if (rows.length < 2) {
      return {
        issues: [],
        skippedRows: rows.length,
        headers: rows[0] ?? [],
      };
    }
    const headers = rows[0].map((item) => String(item ?? "").trim());
    const headerIndex = new Map(headers.map((header, index) => [normalizeHeader(header), index]));
    const issues = [];
    let skippedRows = 0;

    rows.slice(1).forEach((row, index) => {
      const issue = normalizePlaytestFeedbackIssue(row, headerIndex, index);
      if (issue) {
        issues.push(issue);
      } else {
        skippedRows += 1;
      }
    });

    issues.sort((left, right) => {
      if (right.severityWeight !== left.severityWeight) {
        return right.severityWeight - left.severityWeight;
      }
      return left.order - right.order;
    });

    return {
      issues,
      skippedRows,
      headers,
    };
  }

  function buildPlaytestFeedbackIntake(text = "", context = {}) {
    const parsed = parsePlaytestFeedbackCsv(text);
    const categoryCounts = new Map();
    parsed.issues.forEach((issue) => {
      categoryCounts.set(issue.category, (categoryCounts.get(issue.category) ?? 0) + 1);
    });
    const blockerCount = parsed.issues.filter((issue) => issue.severityWeight >= 100).length;
    const majorCount = parsed.issues.filter((issue) => issue.severityWeight >= 70 && issue.severityWeight < 100).length;
    const minorCount = parsed.issues.filter((issue) => issue.severityWeight >= 35 && issue.severityWeight < 70).length;
    const suggestionCount = Math.max(0, parsed.issues.length - blockerCount - majorCount - minorCount);

    return {
      projectTitle: context.projectTitle || "Canvasia Project",
      importedAt: context.importedAt || new Date().toISOString(),
      sourceName: context.sourceName || "",
      skippedRows: parsed.skippedRows,
      issues: parsed.issues,
      summary: {
        totalCount: parsed.issues.length,
        blockerCount,
        majorCount,
        minorCount,
        suggestionCount,
        categoryCounts: Array.from(categoryCounts.entries())
          .map(([category, count]) => ({ category, count }))
          .sort((left, right) => right.count - left.count || left.category.localeCompare(right.category, "zh-CN")),
      },
    };
  }

  function buildPlaytestFeedbackIntakeMarkdown(intake = {}) {
    const summary = intake.summary ?? {};
    const issues = toArray(intake.issues);
    const categoryTable = buildMarkdownTable(
      ["问题分类", "数量"],
      toArray(summary.categoryCounts).map((item) => [item.category, `${item.count}`])
    );
    const issueTable = buildMarkdownTable(
      ["优先级", "严重程度", "分类", "章节", "场景", "路线/目标", "实际表现", "复现步骤", "截图/录屏"],
      issues.slice(0, 80).map((issue, index) => [
        `${index + 1}`,
        issue.severityLabel,
        issue.category,
        issue.chapterName,
        issue.sceneName,
        issue.routeTarget,
        issue.actual || issue.summary,
        issue.steps,
        issue.evidence,
      ])
    );

    return `\uFEFF${[
      `# ${intake.projectTitle || "Canvasia Project"} 测试反馈回收摘要`,
      "",
      `导入时间：${intake.importedAt || ""}`,
      intake.sourceName ? `来源文件：${intake.sourceName}` : "",
      "",
      "## 总览",
      "",
      buildMarkdownTable(
        ["项目", "数量"],
        [
          ["反馈总数", `${summary.totalCount ?? 0}`],
          ["阻塞", `${summary.blockerCount ?? 0}`],
          ["明显问题", `${summary.majorCount ?? 0}`],
          ["轻微问题", `${summary.minorCount ?? 0}`],
          ["建议", `${summary.suggestionCount ?? 0}`],
          ["未采用空行", `${intake.skippedRows ?? 0}`],
        ]
      ),
      "",
      "## 分类统计",
      "",
      categoryTable || "暂时没有可统计的问题分类。",
      "",
      "## 优先修复列表",
      "",
      issueTable || "暂时没有可列出的测试反馈。",
      "",
    ].filter(Boolean).join("\n")}`;
  }

  function buildPlaytestFeedbackIntakeCsv(intake = {}) {
    const issues = toArray(intake.issues);
    return `\uFEFF${buildCsv(
      ["优先级", "严重程度", "问题分类", "章节", "场景", "路线/目标", "实际表现", "复现步骤", "期望表现", "截图/录屏", "备注"],
      issues.map((issue, index) => [
        `${index + 1}`,
        issue.severityLabel,
        issue.category,
        issue.chapterName,
        issue.sceneName,
        issue.routeTarget,
        issue.actual || issue.summary,
        issue.steps,
        issue.expected,
        issue.evidence,
        issue.note,
      ])
    )}\n`;
  }

  function serializeRegressionCase(caseResult = {}, index = 0) {
    return {
      order: index + 1,
      sceneId: caseResult.sceneId ?? "",
      sceneName: caseResult.sceneName ?? "",
      chapterName: caseResult.chapterName ?? "",
      sourceLabel: caseResult.sourceLabel ?? "",
      status: caseResult.status ?? "",
      statusLabel: caseResult.statusLabel ?? caseResult.status ?? "未记录",
      reason: caseResult.reason ?? "",
      detail: caseResult.detail ?? "",
      steps: toCount(caseResult.steps),
      visitedSceneCount: toCount(caseResult.visitedSceneCount),
      choiceCount: toCount(caseResult.choiceCount),
      selectedOptionTexts: toArray(caseResult.selectedOptionTexts).filter(Boolean),
      variableOverrideSummary: caseResult.variableOverrideSummary ?? "",
      conditionTraceSummaries: toArray(caseResult.conditionTraceSummaries).filter(Boolean),
      priorityScore: toCount(caseResult.priorityScore),
      recommendation: caseResult.recommendation ?? "",
    };
  }

  function getRegressionCaseDiagnostic(caseResult = {}) {
    if (regressionDiagnosticTools?.formatRegressionDiagnosticLine) {
      return regressionDiagnosticTools.formatRegressionDiagnosticLine(caseResult);
    }

    return [
      caseResult.variableOverrideSummary ? `测试预设：${caseResult.variableOverrideSummary}` : "",
      ...toArray(caseResult.conditionTraceSummaries),
    ].filter(Boolean).join(" / ");
  }

  function serializeRegressionResult(regressionResult = null, fixQueue = []) {
    if (!regressionResult) {
      return null;
    }
    return {
      ranAt: regressionResult.ranAt ?? "",
      summary: {
        total: toCount(regressionResult.summary?.total),
        passCount: toCount(regressionResult.summary?.passCount),
        warnCount: toCount(regressionResult.summary?.warnCount),
        failCount: toCount(regressionResult.summary?.failCount),
      },
      cases: toArray(regressionResult.cases).map(serializeRegressionCase),
      fixQueue: toArray(fixQueue).map(serializeRegressionCase),
    };
  }

  function flattenRouteTestingCases(routeTestingPlan = {}) {
    const rows = [];
    toArray(routeTestingPlan.decisionPoints).forEach((point, pointIndex) => {
      toArray(point.routeCases).forEach((routeCase, routeIndex) => {
        rows.push({
          type: "分支路线",
          order: `${pointIndex + 1}.${routeIndex + 1}`,
          chapterName: point.chapterName ?? "",
          sceneName: point.sceneName ?? "",
          pathLabel: point.entryPathLabel || "入口未接通",
          targetLabel: `${routeCase.label ?? "路线"} -> ${routeCase.targetSceneName ?? "未设置"}`,
          statusLabel: routeCase.statusLabel ?? routeCase.status ?? "未记录",
          testingHint: routeCase.targetExists
            ? "进入目标场景后确认文本、演出、变量和存档都正常。"
            : "先修复目标场景缺失或重命名造成的坏链。",
        });
      });
    });
    toArray(routeTestingPlan.endingTestCases).forEach((testCase, index) => {
      rows.push({
        type: "结局路径",
        order: `${index + 1}`,
        chapterName: testCase.chapterName ?? "",
        sceneName: testCase.sceneName ?? "",
        pathLabel: testCase.pathLabel || "暂未接通",
        targetLabel: testCase.sceneName ?? "",
        statusLabel: testCase.statusLabel ?? testCase.status ?? "未记录",
        testingHint: testCase.testingHint ?? "完整跑到这个结局并确认回想、存档和收尾文本。",
      });
    });
    return rows;
  }

  function getRouteTestingSummary(routeTestingPlan = {}) {
    const summary = routeTestingPlan.summary ?? {};
    const flattened = flattenRouteTestingCases(routeTestingPlan);
    return {
      decisionPointCount: toCount(summary.decisionPointCount, toArray(routeTestingPlan.decisionPoints).length),
      routeCaseCount: toCount(summary.routeCaseCount, flattened.filter((row) => row.type === "分支路线").length),
      endingTestCaseCount: toCount(summary.endingTestCaseCount, flattened.filter((row) => row.type === "结局路径").length),
      blockedRouteCaseCount: toCount(summary.brokenRouteCaseCount) + toCount(summary.unreachableRouteCaseCount),
      reachableEndingTestCaseCount: toCount(
        summary.reachableEndingTestCaseCount,
        flattened.filter((row) => row.type === "结局路径" && row.statusLabel === "可打到").length
      ),
    };
  }

  function buildPlaytestHandoffDigest(context = {}) {
    const regression = serializeRegressionResult(context.regressionResult, context.regressionFixQueue);
    const routeSummary = getRouteTestingSummary(context.routeTestingPlan);
    const routeCaseCount = routeSummary.routeCaseCount + routeSummary.endingTestCaseCount;
    const failCount = regression?.summary.failCount ?? 0;
    const warnCount = regression?.summary.warnCount ?? 0;
    const blockerCount = failCount + routeSummary.blockedRouteCaseCount;

    if (blockerCount > 0) {
      return {
        status: "blocked",
        title: `先修 ${blockerCount} 个试玩阻塞点`,
        detail: "当前更适合给内部测试员做断点验证，先不要按公开发布口径发。",
      };
    }
    if (!regression) {
      return {
        status: "needs_regression",
        title: "建议先跑一次自动回归试玩",
        detail: "路线清单已可导出，但缺少最新自动回归结果，测试员会少一层参考。",
      };
    }
    if (warnCount > 0) {
      return {
        status: "preview",
        title: `可发 Preview，但有 ${warnCount} 条路线建议复看`,
        detail: "可以交给测试员试玩，同时把复看路线作为重点反馈项。",
      };
    }
    return {
      status: routeCaseCount > 0 ? "ready" : "empty",
      title: routeCaseCount > 0 ? "测试员工单已准备好" : "还没有可列出的试玩用例",
      detail: routeCaseCount > 0 ? "路线用例和自动回归结果都比较干净，可以交给测试员按清单试玩。" : "先补分支或结局路线，再导出测试工单。",
    };
  }

  function buildPlaytestHandoffMarkdown(context = {}) {
    const projectTitle = context.projectTitle || "Canvasia Project";
    const generatedAt = context.generatedAt || new Date().toISOString();
    const routeRows = flattenRouteTestingCases(context.routeTestingPlan);
    const regression = serializeRegressionResult(context.regressionResult, context.regressionFixQueue);
    const digest = buildPlaytestHandoffDigest(context);
    const routeSummary = getRouteTestingSummary(context.routeTestingPlan);
    const routeTable = buildMarkdownTable(
      ["类型", "序号", "章节", "场景", "入口/路径", "路线/目标", "状态", "测试提示"],
      routeRows.slice(0, 80).map((row) => [
        row.type,
        row.order,
        row.chapterName,
        row.sceneName,
        row.pathLabel,
        row.targetLabel,
        row.statusLabel,
        row.testingHint,
      ])
    );
    const regressionTable = regression
      ? buildMarkdownTable(
          ["顺序", "路线", "状态", "来源", "步数", "默认选择", "条件/变量诊断", "说明"],
          regression.cases.map((caseResult) => [
            `${caseResult.order}`,
            caseResult.sceneName,
            caseResult.statusLabel,
            `${caseResult.chapterName} · ${caseResult.sourceLabel}`,
            `${caseResult.steps}`,
            caseResult.selectedOptionTexts.join(" / "),
            getRegressionCaseDiagnostic(caseResult),
            caseResult.detail || caseResult.reason,
          ])
        )
      : "";
    const fixQueueTable = regression?.fixQueue?.length
      ? buildMarkdownTable(
          ["优先级", "路线", "状态", "分数", "条件/变量诊断", "建议"],
          regression.fixQueue.map((caseResult, index) => [
            `${index + 1}`,
            caseResult.sceneName,
            caseResult.statusLabel,
            `${caseResult.priorityScore}`,
            getRegressionCaseDiagnostic(caseResult),
            caseResult.recommendation || caseResult.reason,
          ])
        )
      : "";

    return `\uFEFF${[
      `# ${projectTitle} 测试员试玩工单`,
      "",
      `导出时间：${generatedAt}`,
      `当前判断：${digest.title}`,
      `说明：${digest.detail}`,
      "",
      "## 给测试员的试玩顺序",
      "",
      "1. 先按“重点修复 / 复看路线”确认是否还会卡住。",
      "2. 再按“路线试玩清单”逐条走分支和结局。",
      "3. 遇到黑屏、无法继续、音乐/语音异常、存档读档不一致时，记录场景名和触发步骤。",
      "",
      "## 总览",
      "",
      buildMarkdownTable(
        ["项目", "数量"],
        [
          ["分支检查点", `${routeSummary.decisionPointCount}`],
          ["路线用例", `${routeSummary.routeCaseCount}`],
          ["结局用例", `${routeSummary.endingTestCaseCount}`],
          ["阻塞路线用例", `${routeSummary.blockedRouteCaseCount}`],
          ["可打到结局", `${routeSummary.reachableEndingTestCaseCount}`],
          ["自动回归通过 / 复看 / 失败", regression ? `${regression.summary.passCount} / ${regression.summary.warnCount} / ${regression.summary.failCount}` : "未执行"],
        ]
      ),
      "",
      "## 重点修复 / 复看路线",
      "",
      fixQueueTable || "当前没有自动回归修复队列。若还未跑自动回归，建议先在编辑器里执行一次。",
      "",
      "## 自动回归结果",
      "",
      regressionTable || "还没有自动回归结果。",
      "",
      "## 路线试玩清单",
      "",
      routeTable || "当前没有可列出的路线试玩用例。",
      "",
    ].join("\n")}`;
  }

  function buildPlaytestHandoffCsv(context = {}) {
    const projectTitle = context.projectTitle || "Canvasia Project";
    const routeRows = flattenRouteTestingCases(context.routeTestingPlan);
    const regression = serializeRegressionResult(context.regressionResult, context.regressionFixQueue);
    const rows = [
      ["项目", "", projectTitle, "", "", "", "", "", ""],
      ...toArray(regression?.fixQueue).map((caseResult, index) => [
        "优先复看",
        `${index + 1}`,
        caseResult.chapterName,
        caseResult.sceneName,
        caseResult.sourceLabel,
        caseResult.reason,
        caseResult.statusLabel,
        getRegressionCaseDiagnostic(caseResult),
        caseResult.recommendation || caseResult.detail,
      ]),
      ...routeRows.map((row) => [
        row.type,
        row.order,
        row.chapterName,
        row.sceneName,
        row.pathLabel,
        row.targetLabel,
        row.statusLabel,
        "",
        row.testingHint,
      ]),
    ];

    return `\uFEFF${buildCsv(["类型", "序号", "章节", "场景", "入口/路径", "路线/目标", "状态", "条件/变量诊断", "测试提示"], rows)}\n`;
  }

  function buildPlaytestFeedbackRows(context = {}) {
    const routeRows = flattenRouteTestingCases(context.routeTestingPlan);
    const regression = serializeRegressionResult(context.regressionResult, context.regressionFixQueue);
    const focusRows = toArray(regression?.fixQueue).map((caseResult, index) => ({
      type: "优先复看",
      order: `${index + 1}`,
      chapterName: caseResult.chapterName,
      sceneName: caseResult.sceneName,
      pathLabel: caseResult.sourceLabel,
      targetLabel: caseResult.reason,
      suggestedCategory: caseResult.status === "fail" ? "卡死/断线" : "体验复看",
    }));
    const plannedRows = routeRows.map((row) => ({
      type: row.type,
      order: row.order,
      chapterName: row.chapterName,
      sceneName: row.sceneName,
      pathLabel: row.pathLabel,
      targetLabel: row.targetLabel,
      suggestedCategory: row.type === "结局路径" ? "结局/回想" : "分支/剧情",
    }));

    return [...focusRows, ...plannedRows, {
      type: "自由反馈",
      order: "",
      chapterName: "",
      sceneName: "",
      pathLabel: "",
      targetLabel: "",
      suggestedCategory: "其他",
    }];
  }

  function buildPlaytestFeedbackTemplateMarkdown(context = {}) {
    const projectTitle = context.projectTitle || "Canvasia Project";
    const generatedAt = context.generatedAt || new Date().toISOString();
    const rows = buildPlaytestFeedbackRows(context);
    const table = buildMarkdownTable(
      ["类型", "章节", "场景", "路线/目标", "严重程度", "问题分类", "复现步骤", "期望表现", "实际表现", "截图/录屏", "备注"],
      rows.slice(0, 100).map((row) => [
        row.type,
        row.chapterName,
        row.sceneName,
        row.targetLabel || row.pathLabel,
        "",
        row.suggestedCategory,
        "",
        "",
        "",
        "",
        "",
      ])
    );

    return `\uFEFF${[
      `# ${projectTitle} 测试反馈模板`,
      "",
      `导出时间：${generatedAt}`,
      "",
      "## 填写说明",
      "",
      "- 严重程度建议写：阻塞 / 明显问题 / 轻微问题 / 建议。",
      "- 问题分类建议写：卡死/断线、文本、演出、音频、UI、存档、性能、错别字、其他。",
      "- 复现步骤请尽量写成“从哪个场景开始，点了哪些选项，发生了什么”。",
      "- 如果有截图或录屏，把文件名或链接填在“截图/录屏”列。",
      "",
      "## 反馈表",
      "",
      table || "当前没有路线用例。可以直接在下面新增自由反馈。",
      "",
    ].join("\n")}`;
  }

  function buildPlaytestFeedbackTemplateCsv(context = {}) {
    const projectTitle = context.projectTitle || "Canvasia Project";
    const rows = [
      ["项目", projectTitle, "", "", "", "", "", "", "", "", ""],
      ...buildPlaytestFeedbackRows(context).map((row) => [
        row.type,
        row.chapterName,
        row.sceneName,
        row.targetLabel || row.pathLabel,
        "",
        row.suggestedCategory,
        "",
        "",
        "",
        "",
        "",
      ]),
    ];

    return `\uFEFF${buildCsv(["类型", "章节", "场景", "路线/目标", "严重程度", "问题分类", "复现步骤", "期望表现", "实际表现", "截图/录屏", "备注"], rows)}\n`;
  }

  global.CanvasiaEditorPlaytestHandoffReport = Object.freeze({
    serializeRegressionResult,
    flattenRouteTestingCases,
    getRouteTestingSummary,
    buildPlaytestHandoffDigest,
    buildPlaytestHandoffMarkdown,
    buildPlaytestHandoffCsv,
    buildPlaytestFeedbackRows,
    buildPlaytestFeedbackTemplateMarkdown,
    buildPlaytestFeedbackTemplateCsv,
    parseCsvRows,
    parsePlaytestFeedbackCsv,
    buildPlaytestFeedbackIntake,
    buildPlaytestFeedbackIntakeMarkdown,
    buildPlaytestFeedbackIntakeCsv,
  });
})(typeof window !== "undefined" ? window : globalThis);
