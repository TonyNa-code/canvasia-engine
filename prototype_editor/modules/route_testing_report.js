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

  function getExecutionSeverity(status = "") {
    if (status === "broken") {
      return "blocker";
    }
    if (status === "unreachable") {
      return "warn";
    }
    return "test";
  }

  function getExecutionPhase(status = "") {
    if (status === "broken") {
      return "先修坏链";
    }
    if (status === "unreachable") {
      return "先接入口";
    }
    return "人工试玩";
  }

  function getExecutionWeight(item = {}) {
    const severityWeight = item.severity === "blocker" ? 1000 : item.severity === "warn" ? 700 : 260;
    const kindWeight = item.kind === "ending" ? 60 : 90;
    const depth = Number.isFinite(Number(item.routeDepth)) ? Number(item.routeDepth) : 999;
    return severityWeight + kindWeight - Math.min(depth, 20);
  }

  function buildRouteTestingExecutionQueue(plan = {}) {
    const serialized = serializeRouteTestingPlan(plan);
    const queue = [];

    serialized.decisionPoints.forEach((point, pointIndex) => {
      toArray(point.routeCases).forEach((routeCase, routeIndex) => {
        const severity = getExecutionSeverity(routeCase.status);
        queue.push({
          id: `route_${point.sceneId || pointIndex}_${routeIndex + 1}`,
          kind: "branch",
          severity,
          phase: getExecutionPhase(routeCase.status),
          title:
            routeCase.status === "broken"
              ? "修复分支坏链"
              : routeCase.status === "unreachable"
                ? "接通不可达目标"
                : "覆盖分支用例",
          chapterName: point.chapterName,
          sceneName: point.sceneName,
          routeDepth: point.routeDepth,
          entryPathLabel: point.entryPathLabel || "入口未接通",
          routeLabel: routeCase.label,
          targetLabel: routeCase.targetSceneName,
          status: routeCase.status,
          statusLabel: routeCase.statusLabel,
          actionLabel:
            routeCase.status === "broken"
              ? "重新选择目标场景"
              : routeCase.status === "unreachable"
                ? "检查上游入口是否接回主路线"
                : "从入口跑到这里并点击该分支",
          acceptanceCriteria:
            routeCase.status === "ready"
              ? "能按入口路径抵达分支点，选择该分支后进入目标场景，文本、演出、存档和回收状态正常。"
              : "修复后重新生成路线试玩手册，确认状态变为可试玩。",
        });
      });
    });

    serialized.endingTestCases.forEach((testCase, index) => {
      const severity = getExecutionSeverity(testCase.status);
      queue.push({
        id: `ending_${testCase.sceneId || index}`,
        kind: "ending",
        severity,
        phase: getExecutionPhase(testCase.status),
        title: testCase.status === "ready" ? "完整跑通结局" : "接通结局入口",
        chapterName: testCase.chapterName,
        sceneName: testCase.sceneName,
        routeDepth: testCase.routeDepth,
        entryPathLabel: testCase.pathLabel || "暂未接通",
        routeLabel: "结局路径",
        targetLabel: testCase.sceneName,
        status: testCase.status,
        statusLabel: testCase.statusLabel,
        actionLabel: testCase.testingHint,
        acceptanceCriteria:
          testCase.status === "ready"
            ? "从新游戏开始按路径完整跑到该结局，确认结尾、解锁、回想、存档和返回标题都正常。"
            : "补齐入口后重新检查，确认玩家能自然打到该结局。",
      });
    });

    return queue
      .sort((left, right) => {
        const weightDelta = getExecutionWeight(right) - getExecutionWeight(left);
        if (weightDelta !== 0) {
          return weightDelta;
        }
        return String(left.sceneName ?? "").localeCompare(String(right.sceneName ?? ""), "zh-CN");
      })
      .map((item, index) => ({
        ...item,
        rank: index + 1,
      }));
  }

  function buildRouteTestingAcceptanceChecklist(plan = {}) {
    const summary = getRouteTestingSummary(plan);
    const queue = buildRouteTestingExecutionQueue(plan);
    const blockedCount = queue.filter((item) => item.severity !== "test").length;
    const readyBranchCount = queue.filter((item) => item.kind === "branch" && item.status === "ready").length;
    const readyEndingCount = queue.filter((item) => item.kind === "ending" && item.status === "ready").length;

    return [
      {
        id: "route_blockers_clear",
        label: "路线阻塞清零",
        done: blockedCount === 0,
        detail:
          blockedCount === 0
            ? "坏链和入口不可达用例已经清掉。"
            : `还有 ${blockedCount} 条路线用例需要先接通。`,
      },
      {
        id: "branch_cases_played",
        label: "分支用例逐条试玩",
        done: summary.routeCaseCount > 0 && readyBranchCount === summary.routeCaseCount,
        detail:
          summary.routeCaseCount > 0
            ? `可试玩分支 ${readyBranchCount}/${summary.routeCaseCount} 条。`
            : "当前没有分支用例；如果游戏有选择肢，建议先补分支点。",
      },
      {
        id: "ending_cases_played",
        label: "结局路径完整跑通",
        done: summary.endingTestCaseCount > 0 && readyEndingCount === summary.endingTestCaseCount,
        detail:
          summary.endingTestCaseCount > 0
            ? `可打到结局 ${readyEndingCount}/${summary.endingTestCaseCount} 个。`
            : "当前没有结局候选；建议至少做一个明确收束场景。",
      },
      {
        id: "save_and_archive_checked",
        label: "存档与回想联动确认",
        done: blockedCount === 0 && readyEndingCount > 0,
        detail: "跑结局时顺手确认保存、读档、文本历史、CG/BGM/语音回想和返回标题。",
      },
    ];
  }

  function getRouteTestingReadinessPercent(plan = {}) {
    const summary = getRouteTestingSummary(plan);
    const total = summary.routeCaseCount + summary.endingTestCaseCount;
    if (total <= 0) {
      return 0;
    }
    const blocked = summary.brokenRouteCaseCount + summary.unreachableRouteCaseCount;
    const unreachableEndings = Math.max(0, summary.endingTestCaseCount - summary.reachableEndingTestCaseCount);
    const ready = Math.max(0, total - blocked - unreachableEndings);
    return Math.max(0, Math.min(100, Math.round((ready / total) * 100)));
  }

  function buildRouteTestingReportTables(plan = {}) {
    const serialized = serializeRouteTestingPlan(plan);
    const summary = getRouteTestingSummary(serialized);
    const executionQueue = buildRouteTestingExecutionQueue(serialized);
    const acceptanceChecklist = buildRouteTestingAcceptanceChecklist(serialized);
    const summaryTable = buildMarkdownTable(
      ["项目", "数量"],
      [
        ["分支检查点", `${summary.decisionPointCount}`],
        ["从入口可到的分支点", `${summary.reachableDecisionPointCount}`],
        ["路线用例", `${summary.routeCaseCount}`],
        ["阻塞路线用例", `${summary.brokenRouteCaseCount + summary.unreachableRouteCaseCount}`],
        ["结局用例", `${summary.endingTestCaseCount}`],
        ["可打到结局用例", `${summary.reachableEndingTestCaseCount}`],
        ["执行队列", `${executionQueue.length}`],
        ["路线就绪度", `${getRouteTestingReadinessPercent(serialized)}%`],
      ]
    );
    const executionTable = buildMarkdownTable(
      ["序号", "阶段", "类型", "任务", "位置", "路线/目标", "动作", "通过标准"],
      executionQueue.slice(0, 80).map((item) => [
        `${item.rank}`,
        item.phase,
        item.kind === "ending" ? "结局" : "分支",
        item.title,
        `${item.chapterName} · ${item.sceneName}`,
        `${item.routeLabel} -> ${item.targetLabel}`,
        item.actionLabel,
        item.acceptanceCriteria,
      ])
    );
    const acceptanceTable = buildMarkdownTable(
      ["项目", "状态", "说明"],
      acceptanceChecklist.map((item) => [item.label, item.done ? "完成" : "待处理", item.detail])
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
      executionTable,
      acceptanceTable,
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
      "## 执行优先队列",
      "",
      tables.executionTable || "当前没有可执行的路线试玩队列。",
      "",
      "## 验收标准",
      "",
      tables.acceptanceTable || "当前没有可列出的路线验收标准。",
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
    const executionQueue = buildRouteTestingExecutionQueue(serialized);

    executionQueue.forEach((item) => {
      rows.push([
        "执行队列",
        `${item.rank}`,
        item.chapterName,
        item.sceneName,
        item.entryPathLabel,
        `${item.routeLabel} -> ${item.targetLabel}`,
        item.statusLabel,
        `${item.actionLabel} / ${item.acceptanceCriteria}`,
      ]);
    });

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
    buildRouteTestingExecutionQueue,
    buildRouteTestingAcceptanceChecklist,
    getRouteTestingReadinessPercent,
    buildRouteTestingReportTables,
    buildRouteTestingPlanMarkdown,
    buildRouteTestingPlanCsv,
  });
})(typeof window !== "undefined" ? window : globalThis);
