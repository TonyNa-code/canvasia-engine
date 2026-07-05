(function attachRouteTestingReportTools(global) {
  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function toCount(value, fallback = 0) {
    const numberValue = Number(value);
    return Number.isFinite(numberValue)
      ? Math.max(0, Math.round(numberValue))
      : fallback;
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
      `| ${toArray(headers)
        .map(() => "---")
        .join(" | ")} |`,
      ...safeRows.map(
        (row) => `| ${toArray(row).map(escapeMarkdownTableCell).join(" | ")} |`,
      ),
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
          order: routeCase.order,
          routeId: routeCase.routeId,
          routeKind: routeCase.routeKind,
          sourceSceneId: routeCase.sourceSceneId ?? point.sceneId,
          sourceSceneName: routeCase.sourceSceneName ?? point.sceneName,
          targetSceneId: routeCase.targetSceneId,
          targetSceneName: routeCase.targetSceneName,
          targetPathLabel: routeCase.targetPathLabel,
          targetExists: routeCase.targetExists,
          status: routeCase.status,
          statusLabel: routeCase.statusLabel,
          blockIndex: Number.isInteger(routeCase.blockIndex)
            ? routeCase.blockIndex
            : null,
          optionIndex: Number.isInteger(routeCase.optionIndex)
            ? routeCase.optionIndex
            : null,
          branchIndex: Number.isInteger(routeCase.branchIndex)
            ? routeCase.branchIndex
            : null,
        })),
      })),
      endingTestCases: toArray(plan.endingTestCases).map((testCase) => ({
        order: testCase.order,
        sceneId: testCase.sceneId,
        sceneName: testCase.sceneName,
        chapterId: testCase.chapterId,
        chapterName: testCase.chapterName,
        routeDepth: testCase.routeDepth,
        pathLabel: testCase.pathLabel,
        pathRouteLabels: toArray(testCase.pathRouteLabels),
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
    const routeCaseCount = decisionPoints.reduce(
      (sum, point) => sum + toArray(point.routeCases).length,
      0,
    );
    const brokenRouteCaseCount = decisionPoints.reduce(
      (sum, point) => sum + toCount(point.brokenRouteCount),
      0,
    );
    const unreachableRouteCaseCount = decisionPoints.reduce(
      (sum, point) => sum + toCount(point.unreachableTargetCount),
      0,
    );

    return {
      decisionPointCount: toCount(
        summary.decisionPointCount,
        decisionPoints.length,
      ),
      reachableDecisionPointCount: toCount(
        summary.reachableDecisionPointCount,
        decisionPoints.filter((point) => point.isReachable).length,
      ),
      routeCaseCount: toCount(summary.routeCaseCount, routeCaseCount),
      brokenRouteCaseCount: toCount(
        summary.brokenRouteCaseCount,
        brokenRouteCaseCount,
      ),
      unreachableRouteCaseCount: toCount(
        summary.unreachableRouteCaseCount,
        unreachableRouteCaseCount,
      ),
      endingTestCaseCount: toCount(
        summary.endingTestCaseCount,
        endingTestCases.length,
      ),
      reachableEndingTestCaseCount: toCount(
        summary.reachableEndingTestCaseCount,
        endingTestCases.filter((testCase) => testCase.status === "ready")
          .length,
      ),
    };
  }

  function getRouteTestingStatusDigest(plan = {}) {
    const summary = getRouteTestingSummary(plan);
    const blockedCount =
      summary.brokenRouteCaseCount + summary.unreachableRouteCaseCount;
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
    const severityWeight =
      item.severity === "blocker" ? 1000 : item.severity === "warn" ? 700 : 260;
    const kindWeight = item.kind === "ending" ? 60 : 90;
    const depth = Number.isFinite(Number(item.routeDepth))
      ? Number(item.routeDepth)
      : 999;
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
          sourceSceneId: routeCase.sourceSceneId ?? point.sceneId,
          sourceSceneName: routeCase.sourceSceneName ?? point.sceneName,
          targetSceneId: routeCase.targetSceneId,
          routeDepth: point.routeDepth,
          entryPathLabel: point.entryPathLabel || "入口未接通",
          routeLabel: routeCase.label,
          routeKind: routeCase.routeKind ?? "",
          routeCaseId: routeCase.routeId ?? "",
          blockIndex: Number.isInteger(routeCase.blockIndex)
            ? routeCase.blockIndex
            : null,
          optionIndex: Number.isInteger(routeCase.optionIndex)
            ? routeCase.optionIndex
            : null,
          branchIndex: Number.isInteger(routeCase.branchIndex)
            ? routeCase.branchIndex
            : null,
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
        sourceSceneId: testCase.sceneId,
        sourceSceneName: testCase.sceneName,
        targetSceneId: testCase.sceneId,
        routeDepth: testCase.routeDepth,
        entryPathLabel: testCase.pathLabel || "暂未接通",
        routeLabel: "结局路径",
        routeKind: "ending",
        routeCaseId: `ending:${testCase.sceneId || index}`,
        blockIndex: null,
        optionIndex: null,
        branchIndex: null,
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
        const weightDelta =
          getExecutionWeight(right) - getExecutionWeight(left);
        if (weightDelta !== 0) {
          return weightDelta;
        }
        return String(left.sceneName ?? "").localeCompare(
          String(right.sceneName ?? ""),
          "zh-CN",
        );
      })
      .map((item, index) => ({
        ...item,
        rank: index + 1,
      }));
  }

  function buildRouteTestingAcceptanceChecklist(plan = {}) {
    const summary = getRouteTestingSummary(plan);
    const queue = buildRouteTestingExecutionQueue(plan);
    const blockedCount = queue.filter(
      (item) => item.severity !== "test",
    ).length;
    const readyBranchCount = queue.filter(
      (item) => item.kind === "branch" && item.status === "ready",
    ).length;
    const readyEndingCount = queue.filter(
      (item) => item.kind === "ending" && item.status === "ready",
    ).length;

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
        done:
          summary.routeCaseCount > 0 &&
          readyBranchCount === summary.routeCaseCount,
        detail:
          summary.routeCaseCount > 0
            ? `可试玩分支 ${readyBranchCount}/${summary.routeCaseCount} 条。`
            : "当前没有分支用例；如果游戏有选择肢，建议先补分支点。",
      },
      {
        id: "ending_cases_played",
        label: "结局路径完整跑通",
        done:
          summary.endingTestCaseCount > 0 &&
          readyEndingCount === summary.endingTestCaseCount,
        detail:
          summary.endingTestCaseCount > 0
            ? `可打到结局 ${readyEndingCount}/${summary.endingTestCaseCount} 个。`
            : "当前没有结局候选；建议至少做一个明确收束场景。",
      },
      {
        id: "save_and_archive_checked",
        label: "存档与回想联动确认",
        done: blockedCount === 0 && readyEndingCount > 0,
        detail:
          "跑结局时顺手确认保存、读档、文本历史、CG/BGM/语音回想和返回标题。",
      },
    ];
  }

  function getRouteKindLabel(routeKind = "") {
    if (routeKind === "choice") {
      return "选项分支";
    }
    if (routeKind === "condition") {
      return "条件分支";
    }
    if (routeKind === "fallback") {
      return "否则分支";
    }
    if (routeKind === "jump") {
      return "直接跳转";
    }
    if (routeKind === "ending") {
      return "结局路径";
    }
    return "路线";
  }

  function getRouteTestingVariablePresetHint(item = {}) {
    if (item.routeKind === "condition") {
      return "自动回归会尝试把条件变量调到命中此分支；人工试玩时确认玩家能在前文自然获得这些变量。";
    }
    if (item.routeKind === "fallback") {
      return "自动回归会尝试让上方条件都不满足；人工试玩时确认失败线、普通线或保底线不会卡死。";
    }
    if (item.routeKind === "choice") {
      return "按玩家视角选择对应选项即可；若该选项会改变量，后续需要确认变量真的影响分支或回想。";
    }
    if (item.kind === "ending") {
      return "按路径完整跑到结局，顺手确认结局回想、CG/BGM/语音解锁和返回标题。";
    }
    return "不需要额外变量预设，按路径进入并确认跳转结果。";
  }

  function buildRouteTestingManualSteps(item = {}) {
    if (item.severity === "blocker") {
      return [
        `打开「${item.sceneName || "分支场景"}」并定位到 ${getRouteKindLabel(item.routeKind)}。`,
        `重新选择或创建目标场景「${item.targetLabel || "未设置目标"}」。`,
        "重新生成路线试玩手册，确认这条用例不再显示坏链。",
      ];
    }
    if (item.severity === "warn") {
      return [
        `从项目入口检查到「${item.sceneName || "分支场景"}」的上游路径。`,
        `补一个跳转、选项或条件结果，让玩家能自然抵达「${item.targetLabel || "目标场景"}」。`,
        "重新进入试玩或自动回归，确认目标已经变成可达。",
      ];
    }
    if (item.kind === "ending") {
      return [
        `从新游戏开始，按路径「${item.entryPathLabel || "项目入口"}」完整跑到结局。`,
        "确认结尾文本、演出、BGM淡出、存档/读档和回想解锁都正常。",
        "返回标题页后再读一次关键存档，确认没有断档或状态丢失。",
      ];
    }
    return [
      `从入口按路径「${item.entryPathLabel || "项目入口"}」进入「${item.sceneName || "分支场景"}」。`,
      `触发 ${getRouteKindLabel(item.routeKind)}「${item.routeLabel || "路线"}」，确认进入「${item.targetLabel || "目标场景"}」。`,
      "检查该分支后的文本、立绘、BGM、存档和变量后果是否符合预期。",
    ];
  }

  function getRouteTestingLaneDetail(laneId, items = []) {
    if (laneId === "repair") {
      return items.length > 0
        ? "先把这些断点接上，否则玩家或自动回归跑不到完整路线。"
        : "坏链和不可达路线已经清空。";
    }
    if (laneId === "branch") {
      return items.length > 0
        ? "每条可达分支都应该至少人工点一次，避免默认路线掩盖问题。"
        : "当前没有可单独执行的分支用例。";
    }
    if (laneId === "ending") {
      return items.length > 0
        ? "每个可打到结局都需要完整跑一遍，确认收束和解锁。"
        : "还没有可打到的结局路径。";
    }
    return items.length > 0
      ? "这些用例适合交给自动回归优先执行。"
      : "暂无自动回归优先种子。";
  }

  function buildRouteTestingWorkbook(plan = {}) {
    const serialized = serializeRouteTestingPlan(plan);
    const executionQueue = buildRouteTestingExecutionQueue(serialized);
    const cards = executionQueue.map((item) => ({
      ...item,
      kindLabel: item.kind === "ending" ? "结局" : "分支",
      routeKindLabel: getRouteKindLabel(item.routeKind),
      variablePresetHint: getRouteTestingVariablePresetHint(item),
      manualSteps: buildRouteTestingManualSteps(item),
      canAutoSmoke: item.status === "ready" && item.kind === "branch",
    }));
    const repairItems = cards.filter((item) => item.severity !== "test");
    const branchItems = cards.filter(
      (item) => item.kind === "branch" && item.status === "ready",
    );
    const endingItems = cards.filter(
      (item) => item.kind === "ending" && item.status === "ready",
    );
    const autoSmokeItems = cards
      .filter((item) => item.canAutoSmoke)
      .slice(0, 8);
    const lanes = [
      {
        id: "repair",
        label: "先修路线断点",
        tone: repairItems.length > 0 ? "warn" : "good",
        itemCount: repairItems.length,
        detail: getRouteTestingLaneDetail("repair", repairItems),
        items: repairItems,
      },
      {
        id: "branch",
        label: "逐条覆盖分支",
        tone: branchItems.length > 0 ? "test" : "soft",
        itemCount: branchItems.length,
        detail: getRouteTestingLaneDetail("branch", branchItems),
        items: branchItems,
      },
      {
        id: "ending",
        label: "完整跑通结局",
        tone: endingItems.length > 0 ? "test" : "soft",
        itemCount: endingItems.length,
        detail: getRouteTestingLaneDetail("ending", endingItems),
        items: endingItems,
      },
      {
        id: "auto_smoke",
        label: "自动回归优先种子",
        tone: autoSmokeItems.length > 0 ? "good" : "soft",
        itemCount: autoSmokeItems.length,
        detail: getRouteTestingLaneDetail("auto_smoke", autoSmokeItems),
        items: autoSmokeItems,
      },
    ];

    return {
      summary: getRouteTestingSummary(serialized),
      digest: getRouteTestingStatusDigest(serialized),
      readinessPercent: getRouteTestingReadinessPercent(serialized),
      lanes,
      cards,
      topCards: cards.slice(0, 8),
      nextBestAction: cards[0] ?? null,
    };
  }

  function buildRouteTestingWorkbookTable(plan = {}) {
    const workbook = buildRouteTestingWorkbook(plan);
    return buildMarkdownTable(
      [
        "序号",
        "阶段",
        "对象",
        "位置",
        "执行步骤",
        "变量 / 状态提示",
        "验收口径",
      ],
      workbook.topCards.map((item) => [
        `${item.rank}`,
        item.phase,
        `${item.kindLabel} / ${item.routeKindLabel}`,
        `${item.chapterName} · ${item.sceneName}`,
        item.manualSteps.join("<br />"),
        item.variablePresetHint,
        item.acceptanceCriteria,
      ]),
    );
  }

  function getRouteTestingReadinessPercent(plan = {}) {
    const summary = getRouteTestingSummary(plan);
    const total = summary.routeCaseCount + summary.endingTestCaseCount;
    if (total <= 0) {
      return 0;
    }
    const blocked =
      summary.brokenRouteCaseCount + summary.unreachableRouteCaseCount;
    const unreachableEndings = Math.max(
      0,
      summary.endingTestCaseCount - summary.reachableEndingTestCaseCount,
    );
    const ready = Math.max(0, total - blocked - unreachableEndings);
    return Math.max(0, Math.min(100, Math.round((ready / total) * 100)));
  }

  function buildRouteTestingReportTables(plan = {}) {
    const serialized = serializeRouteTestingPlan(plan);
    const summary = getRouteTestingSummary(serialized);
    const executionQueue = buildRouteTestingExecutionQueue(serialized);
    const acceptanceChecklist =
      buildRouteTestingAcceptanceChecklist(serialized);
    const workbookTable = buildRouteTestingWorkbookTable(serialized);
    const summaryTable = buildMarkdownTable(
      ["项目", "数量"],
      [
        ["分支检查点", `${summary.decisionPointCount}`],
        ["从入口可到的分支点", `${summary.reachableDecisionPointCount}`],
        ["路线用例", `${summary.routeCaseCount}`],
        [
          "阻塞路线用例",
          `${summary.brokenRouteCaseCount + summary.unreachableRouteCaseCount}`,
        ],
        ["结局用例", `${summary.endingTestCaseCount}`],
        ["可打到结局用例", `${summary.reachableEndingTestCaseCount}`],
        ["执行队列", `${executionQueue.length}`],
        ["路线就绪度", `${getRouteTestingReadinessPercent(serialized)}%`],
      ],
    );
    const executionTable = buildMarkdownTable(
      ["序号", "阶段", "类型", "任务", "位置", "路线/目标", "动作", "通过标准"],
      executionQueue
        .slice(0, 80)
        .map((item) => [
          `${item.rank}`,
          item.phase,
          item.kind === "ending" ? "结局" : "分支",
          item.title,
          `${item.chapterName} · ${item.sceneName}`,
          `${item.routeLabel} -> ${item.targetLabel}`,
          item.actionLabel,
          item.acceptanceCriteria,
        ]),
    );
    const acceptanceTable = buildMarkdownTable(
      ["项目", "状态", "说明"],
      acceptanceChecklist.map((item) => [
        item.label,
        item.done ? "完成" : "待处理",
        item.detail,
      ]),
    );
    const decisionTable = buildMarkdownTable(
      ["分支点", "入口路径", "路线用例", "阻塞"],
      serialized.decisionPoints.slice(0, 40).map((point) => [
        `${point.chapterName} · ${point.sceneName}`,
        point.entryPathLabel || "入口未接通",
        toArray(point.routeCases)
          .slice(0, 8)
          .map(
            (routeCase) =>
              `${routeCase.label} -> ${routeCase.targetSceneName}（${routeCase.statusLabel}）`,
          )
          .join(" / "),
        `${toCount(point.brokenRouteCount) + toCount(point.unreachableTargetCount)}`,
      ]),
    );
    const endingTable = buildMarkdownTable(
      ["结局", "状态", "路径", "测试提示"],
      serialized.endingTestCases
        .slice(0, 40)
        .map((testCase) => [
          `${testCase.chapterName} · ${testCase.sceneName}`,
          testCase.statusLabel,
          testCase.pathLabel || "暂未接通",
          testCase.testingHint,
        ]),
    );

    return {
      summaryTable,
      executionTable,
      acceptanceTable,
      workbookTable,
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
      "## 发布前路线工作簿",
      "",
      tables.workbookTable || "当前没有可列出的路线执行步骤。",
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

    buildRouteTestingWorkbook(serialized).topCards.forEach((item) => {
      rows.push([
        "路线工作簿",
        `${item.rank}`,
        item.chapterName,
        item.sceneName,
        item.entryPathLabel,
        `${item.routeKindLabel}：${item.routeLabel} -> ${item.targetLabel}`,
        item.statusLabel,
        `${item.manualSteps.join(" / ")} / ${item.variablePresetHint} / ${item.acceptanceCriteria}`,
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
          routeCase.targetExists
            ? "按此分支进入目标场景并确认演出正常。"
            : "先修复目标场景缺失或名称变更。",
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
      [
        "类型",
        "序号",
        "章节",
        "场景",
        "入口/路径",
        "路线/目标",
        "状态",
        "测试提示",
      ],
      [["项目", "", projectTitle, "", "", "", "", ""], ...rows],
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
    getRouteKindLabel,
    getRouteTestingVariablePresetHint,
    buildRouteTestingManualSteps,
    buildRouteTestingWorkbook,
    buildRouteTestingWorkbookTable,
    getRouteTestingReadinessPercent,
    buildRouteTestingReportTables,
    buildRouteTestingPlanMarkdown,
    buildRouteTestingPlanCsv,
  });
})(typeof window !== "undefined" ? window : globalThis);
