(function attachRouteTestingReportTools(global) {
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

  function serializeRouteTestingPlan(plan = {}) {
    return {
      summary: plan.summary ?? {},
      decisionPoints: toArray(plan.decisionPoints).map((point) => ({
        sceneId: point.sceneId,
        sceneName: point.sceneName,
        chapterName: point.chapterName,
        routeDepth: point.routeDepth,
        entryPathLabel: point.entryPathLabel,
        isReachable: point.isReachable,
        routeCount: point.routeCount,
        brokenRouteCount: point.brokenRouteCount,
        unreachableTargetCount: point.unreachableTargetCount,
        routeCases: toArray(point.routeCases).map((routeCase) => ({
          label: routeCase.label,
          targetSceneName: routeCase.targetSceneName,
          targetExists: routeCase.targetExists,
          status: routeCase.status,
          statusLabel: routeCase.statusLabel,
        })),
      })),
      endingTestCases: toArray(plan.endingTestCases).map((testCase) => ({
        sceneId: testCase.sceneId,
        sceneName: testCase.sceneName,
        chapterName: testCase.chapterName,
        routeDepth: testCase.routeDepth,
        pathLabel: testCase.pathLabel,
        status: testCase.status,
        statusLabel: testCase.statusLabel,
        testingHint: testCase.testingHint,
      })),
    };
  }

  function getRouteTestingSummary(plan = {}) {
    const serialized = serializeRouteTestingPlan(plan);
    const decisionPoints = serialized.decisionPoints;
    const endingTestCases = serialized.endingTestCases;
    const summary = serialized.summary ?? {};
    const routeCaseCount = decisionPoints.reduce((sum, point) => sum + toArray(point.routeCases).length, 0);
    const brokenRouteCaseCount = decisionPoints.reduce((sum, point) => sum + toCount(point.brokenRouteCount), 0);
    const unreachableRouteCaseCount = decisionPoints.reduce(
      (sum, point) => sum + toCount(point.unreachableTargetCount),
      0
    );

    return {
      decisionPointCount: toCount(summary.decisionPointCount, decisionPoints.length),
      reachableDecisionPointCount: toCount(
        summary.reachableDecisionPointCount,
        decisionPoints.filter((point) => point.isReachable).length
      ),
      routeCaseCount: toCount(summary.routeCaseCount, routeCaseCount),
      brokenRouteCaseCount: toCount(summary.brokenRouteCaseCount, brokenRouteCaseCount),
      unreachableRouteCaseCount: toCount(summary.unreachableRouteCaseCount, unreachableRouteCaseCount),
      endingTestCaseCount: toCount(summary.endingTestCaseCount, endingTestCases.length),
      reachableEndingTestCaseCount: toCount(
        summary.reachableEndingTestCaseCount,
        endingTestCases.filter((testCase) => testCase.status === "ready").length
      ),
    };
  }

  function getRouteTestingStatusDigest(plan = {}) {
    const summary = getRouteTestingSummary(plan);
    const blockedCount = summary.brokenRouteCaseCount + summary.unreachableRouteCaseCount;
    const totalCaseCount = summary.routeCaseCount + summary.endingTestCaseCount;

    if (totalCaseCount === 0) {
      return {
        status: "empty",
        tone: "soft",
        title: "还没有路线试玩用例",
        detail: "项目里暂时没有可独立覆盖的分支或结局路径。",
      };
    }

    if (blockedCount > 0) {
      return {
        status: "blocked",
        tone: "warn",
        title: `还有 ${blockedCount} 条路线用例需要先接通`,
        detail: "优先处理坏链或入口不可达的分支，再开始完整试玩。",
      };
    }

    return {
      status: "ready",
      tone: "good",
      title: "路线试玩手册已可执行",
      detail: "当前分支和结局用例都能进入发布前人工试玩。",
    };
  }

  function buildRouteTestingReportTables(plan = {}) {
    const serialized = serializeRouteTestingPlan(plan);
    const summary = getRouteTestingSummary(serialized);
    const summaryTable = buildMarkdownTable(
      ["项目", "数量"],
      [
        ["分支检查点", `${summary.decisionPointCount}`],
        ["从入口可到的分支点", `${summary.reachableDecisionPointCount}`],
        ["路线用例", `${summary.routeCaseCount}`],
        ["阻塞路线用例", `${summary.brokenRouteCaseCount + summary.unreachableRouteCaseCount}`],
        ["结局用例", `${summary.endingTestCaseCount}`],
        ["可打到结局用例", `${summary.reachableEndingTestCaseCount}`],
      ]
    );
    const decisionTable = buildMarkdownTable(
      ["分支点", "入口路径", "路线用例", "阻塞"],
      serialized.decisionPoints.slice(0, 40).map((point) => [
        `${point.chapterName} · ${point.sceneName}`,
        point.entryPathLabel || "入口未接通",
        toArray(point.routeCases)
          .slice(0, 8)
          .map((routeCase) => `${routeCase.label} -> ${routeCase.targetSceneName}（${routeCase.statusLabel}）`)
          .join(" / "),
        `${toCount(point.brokenRouteCount) + toCount(point.unreachableTargetCount)}`,
      ])
    );
    const endingTable = buildMarkdownTable(
      ["结局", "状态", "路径", "测试提示"],
      serialized.endingTestCases.slice(0, 40).map((testCase) => [
        `${testCase.chapterName} · ${testCase.sceneName}`,
        testCase.statusLabel,
        testCase.pathLabel || "暂未接通",
        testCase.testingHint,
      ])
    );

    return {
      summaryTable,
      decisionTable,
      endingTable,
    };
  }

  function buildRouteTestingPlanMarkdown(plan = {}, context = {}) {
    const projectTitle = context.projectTitle || "Canvasia Project";
    const generatedAt = context.generatedAt || new Date().toISOString();
    const digest = getRouteTestingStatusDigest(plan);
    const tables = buildRouteTestingReportTables(plan);

    return `\uFEFF${[
      `# ${projectTitle} 路线试玩手册`,
      "",
      `导出时间：${generatedAt}`,
      `状态：${digest.title}`,
      `说明：${digest.detail}`,
      "",
      "## 总览",
      "",
      tables.summaryTable || "当前没有可列出的路线试玩摘要。",
      "",
      "## 分支检查点",
      "",
      tables.decisionTable || "当前没有需要单独覆盖的分支点。",
      "",
      "## 结局试玩路径",
      "",
      tables.endingTable || "当前没有可列出的结局试玩路径。",
      "",
      "## 使用建议",
      "",
      "1. 先处理状态为坏链或未接通的路线用例。",
      "2. 每个分支检查点至少试玩一次所有选项或条件结果。",
      "3. 每个可打到结局都完整跑一遍，确认文本、演出、存档和回想解锁正常。",
      "",
    ].join("\n")}`;
  }

  function buildRouteTestingPlanCsv(plan = {}, context = {}) {
    const projectTitle = context.projectTitle || "Canvasia Project";
    const rows = [];
    const serialized = serializeRouteTestingPlan(plan);

    serialized.decisionPoints.forEach((point, pointIndex) => {
      toArray(point.routeCases).forEach((routeCase, routeIndex) => {
        rows.push([
          "分支路线",
          `${pointIndex + 1}.${routeIndex + 1}`,
          point.chapterName,
          point.sceneName,
          point.entryPathLabel || "入口未接通",
          `${routeCase.label} -> ${routeCase.targetSceneName}`,
          routeCase.statusLabel,
          routeCase.targetExists ? "按此分支进入目标场景并确认演出正常。" : "先修复目标场景缺失或名称变更。",
        ]);
      });
    });

    serialized.endingTestCases.forEach((testCase, index) => {
      rows.push([
        "结局路径",
        `${index + 1}`,
        testCase.chapterName,
        testCase.sceneName,
        testCase.pathLabel || "暂未接通",
        testCase.sceneName,
        testCase.statusLabel,
        testCase.testingHint,
      ]);
    });

    return `\uFEFF${buildCsv(
      ["类型", "序号", "章节", "场景", "入口/路径", "路线/目标", "状态", "测试提示"],
      [["项目", "", projectTitle, "", "", "", "", ""], ...rows]
    )}\n`;
  }

  global.CanvasiaEditorRouteTestingReport = Object.freeze({
    escapeMarkdownTableCell,
    buildMarkdownTable,
    serializeRouteTestingPlan,
    getRouteTestingSummary,
    getRouteTestingStatusDigest,
    buildRouteTestingReportTables,
    buildRouteTestingPlanMarkdown,
    buildRouteTestingPlanCsv,
  });
})(typeof window !== "undefined" ? window : globalThis);
