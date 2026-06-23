(function attachProjectMilestoneTools(global) {
  function toCount(value) {
    const numberValue = Number(value);
    return Number.isFinite(numberValue) && numberValue > 0 ? Math.floor(numberValue) : 0;
  }

  function clampPercent(value) {
    const numberValue = Number(value);
    if (!Number.isFinite(numberValue)) {
      return 0;
    }
    return Math.max(0, Math.min(100, Math.round(numberValue)));
  }

  function getPercent(done, total) {
    const safeTotal = toCount(total);
    if (safeTotal <= 0) {
      return 0;
    }
    return clampPercent((toCount(done) / safeTotal) * 100);
  }

  function createAction(label, action, extra = {}) {
    return {
      label,
      action,
      ...extra,
    };
  }

  function createCheck({ id, label, done, detail, missing, weight = 1, action = null }) {
    return {
      id,
      label,
      done: Boolean(done),
      detail: String(detail ?? ""),
      missing: String(missing ?? ""),
      weight: Math.max(1, Number(weight) || 1),
      action,
    };
  }

  function scoreChecks(checks) {
    const totalWeight = checks.reduce((total, check) => total + check.weight, 0);
    if (totalWeight <= 0) {
      return 0;
    }
    const doneWeight = checks
      .filter((check) => check.done)
      .reduce((total, check) => total + check.weight, 0);
    return clampPercent((doneWeight / totalWeight) * 100);
  }

  function getMilestoneTone(percent, blockerCount) {
    if (percent >= 100) {
      return "good";
    }
    if (blockerCount >= 3) {
      return "danger";
    }
    if (percent >= 60 || blockerCount <= 2) {
      return "warn";
    }
    return "soft";
  }

  function getUniqueActions(checks, fallbackActions = []) {
    const actions = [];
    const seen = new Set();
    [...checks, ...fallbackActions.map((action) => ({ action }))]
      .map((entry) => entry.action)
      .filter(Boolean)
      .forEach((action) => {
        const key = [
          action.action,
          action.screen ?? action.dataset?.screen ?? "",
          action.sceneId ?? "",
          action.exportTarget ?? action.dataset?.exportTarget ?? action.dataset?.["export-target"] ?? "",
        ].join(":");
        if (seen.has(key)) {
          return;
        }
        seen.add(key);
        actions.push(action);
      });
    return actions.slice(0, 2);
  }

  function createMilestone({ id, title, label, summaryWhenDone, summaryWhenOpen, checks, fallbackActions = [] }) {
    const blockers = checks.filter((check) => !check.done);
    const wins = checks.filter((check) => check.done);
    const percent = scoreChecks(checks);
    const done = blockers.length === 0;
    const primaryBlocker = blockers[0] ?? null;
    return {
      id,
      title,
      label,
      percent,
      done,
      tone: getMilestoneTone(percent, blockers.length),
      blockers,
      wins,
      checks,
      summary: done
        ? summaryWhenDone
        : primaryBlocker
          ? `${summaryWhenOpen} 下一步：${primaryBlocker.missing}`
          : summaryWhenOpen,
      actions: getUniqueActions(blockers, fallbackActions),
    };
  }

  function buildProjectMilestonePlan(context = {}) {
    const totalChapters = toCount(context.totalChapters);
    const totalScenes = toCount(context.totalScenes);
    const scenesWithContent = toCount(context.scenesWithContent);
    const scenesWithBackground = toCount(context.scenesWithBackground);
    const scenesWithMusic = toCount(context.scenesWithMusic);
    const scenesWithEffects = toCount(context.scenesWithEffects);
    const totalDialogueCount = toCount(context.totalDialogueCount);
    const voicedDialogueCount = toCount(context.voicedDialogueCount);
    const readyAssetCount = toCount(context.readyAssetCount);
    const totalAssetCount = toCount(context.totalAssetCount);
    const validationErrorCount = toCount(context.validationErrorCount);
    const validationWarningCount = toCount(context.validationWarningCount);
    const brokenRoutes = toCount(context.brokenRoutes);
    const orphanScenes = toCount(context.orphanScenes);
    const placeholderAssetCount = toCount(context.placeholderAssetCount);
    const placeholderScriptCount = toCount(context.placeholderScriptCount);
    const placeholderContentCount = placeholderAssetCount + placeholderScriptCount;
    const hasStarterKit = context.hasStarterKit === true;
    const hasExport = context.hasExport === true;
    const regressionPass = context.regressionPass === true;
    const contentCoverage = getPercent(scenesWithContent, totalScenes);
    const backgroundCoverage = getPercent(scenesWithBackground, totalScenes);
    const musicCoverage = getPercent(scenesWithMusic, totalScenes);
    const effectCoverage = getPercent(scenesWithEffects, totalScenes);
    const voiceCoverage = totalDialogueCount > 0 ? getPercent(voicedDialogueCount, totalDialogueCount) : 100;
    const assetCoverage = totalAssetCount > 0 ? getPercent(readyAssetCount, totalAssetCount) : 0;

    const actions = {
      createChapter: createAction("创建第一章", "create-first-chapter"),
      writeStory: createAction("去写正文", "switch-screen", { screen: "story" }),
      assets: createAction("打开素材页", "switch-screen", { screen: "assets" }),
      starterKit: createAction("生成起步骨架", "create-starter-kit"),
      replacePlaceholders: createAction(
        placeholderScriptCount > 0 ? "替换待补正文" : "替换占位素材",
        "switch-screen",
        { screen: placeholderScriptCount > 0 ? "story" : "assets" }
      ),
      inspection: createAction("打开项目巡检", "switch-screen", { screen: "inspection" }),
      preview: createAction("去试玩导出", "switch-screen", { screen: "preview" }),
      regression: createAction("运行回归试玩", "run-preview-regression"),
      exportWeb: createAction("导出网页包", "export-build", { dataset: { "export-target": "web" } }),
    };

    const milestones = [
      createMilestone({
        id: "first_playable",
        title: "第一版可试玩 Demo",
        label: "先让它跑起来",
        summaryWhenDone: "已经具备第一版可试玩骨架，可以开始提升氛围和流程完整度。",
        summaryWhenOpen: "目标是让小白用户先做出一段能打开、能阅读、能试玩的内容。",
        checks: [
          createCheck({
            id: "structure",
            label: "章节和场景骨架",
            done: totalChapters > 0 && totalScenes > 0,
            detail: `${totalChapters} 章 / ${totalScenes} 场`,
            missing: "先创建第一章和第一场。",
            weight: 2,
            action: actions.createChapter,
          }),
          createCheck({
            id: "story",
            label: "第一段正文",
            done: scenesWithContent > 0,
            detail: `${scenesWithContent} 个场景已有正文`,
            missing: "写入第一句旁白、台词或选项。",
            weight: 2,
            action: actions.writeStory,
          }),
          createCheck({
            id: "route",
            label: "试玩路线不断线",
            done: brokenRoutes === 0,
            detail: brokenRoutes === 0 ? "未发现坏链" : `${brokenRoutes} 条坏链`,
            missing: "先清掉跳转坏链。",
            weight: 2,
            action: actions.inspection,
          }),
          createCheck({
            id: "stage_seed",
            label: "基础舞台感",
            done: scenesWithBackground > 0 || hasStarterKit,
            detail: scenesWithBackground > 0 ? `${scenesWithBackground} 个场景已有背景` : hasStarterKit ? "已有起步素材骨架" : "还没有背景骨架",
            missing: "补第一张背景或生成起步骨架。",
            action: hasStarterKit ? actions.assets : actions.starterKit,
          }),
          createCheck({
            id: "no_blocking_errors",
            label: "没有阻塞错误",
            done: validationErrorCount === 0,
            detail: validationErrorCount === 0 ? "结构错误为 0" : `${validationErrorCount} 项错误`,
            missing: "先处理项目检查里的错误。",
            weight: 2,
            action: actions.inspection,
          }),
        ],
        fallbackActions: [actions.preview, actions.writeStory],
      }),
      createMilestone({
        id: "vertical_slice",
        title: "体验版打磨",
        label: "像一段正式作品",
        summaryWhenDone: "核心体验已经比较完整，适合开始做发布候选前的稳定性检查。",
        summaryWhenOpen: "目标是让 Demo 不只是能跑，而是有画面、音乐、节奏和一点演出味道。",
        checks: [
          createCheck({
            id: "content_coverage",
            label: "正文覆盖过半",
            done: totalScenes > 0 && contentCoverage >= 60,
            detail: `${contentCoverage}% 场景已有正文`,
            missing: "优先补空场景正文。",
            weight: 2,
            action: actions.writeStory,
          }),
          createCheck({
            id: "background_coverage",
            label: "多数场景有背景",
            done: totalScenes > 0 && backgroundCoverage >= 60,
            detail: `${backgroundCoverage}% 场景已有背景`,
            missing: "给主要场景补背景卡片。",
            action: actions.assets,
          }),
          createCheck({
            id: "music_coverage",
            label: "关键场景有 BGM",
            done: totalScenes > 0 && musicCoverage >= 40,
            detail: `${musicCoverage}% 场景已有 BGM`,
            missing: "给开场或重点场景补音乐。",
            action: actions.assets,
          }),
          createCheck({
            id: "effect_texture",
            label: "至少有演出点缀",
            done: scenesWithEffects > 0 || effectCoverage >= 25,
            detail: `${scenesWithEffects} 个场景已有演出卡片`,
            missing: "加一点镜头、粒子、滤镜或闪屏。",
            action: actions.writeStory,
          }),
          createCheck({
            id: "asset_ready",
            label: "核心素材就绪",
            done: totalAssetCount > 0 && assetCoverage >= 70,
            detail: totalAssetCount > 0 ? `${assetCoverage}% 素材已有真实文件` : "还没有素材条目",
            missing: "补齐被引用素材的真实文件。",
            weight: 2,
            action: actions.assets,
          }),
          createCheck({
            id: "demo_placeholders_replaced",
            label: "Demo 占位内容已替换",
            done: placeholderContentCount === 0,
            detail:
              placeholderContentCount === 0
                ? "没有明显占位素材或待补正文"
                : `占位素材 ${placeholderAssetCount} 个 / 待补正文 ${placeholderScriptCount} 条`,
            missing:
              placeholderScriptCount > 0
                ? "先把待补正文替换成正式台词。"
                : "先把可试玩 Demo 的占位素材换成正式素材。",
            weight: 2,
            action: actions.replacePlaceholders,
          }),
          createCheck({
            id: "warning_budget",
            label: "提醒项可控",
            done: validationWarningCount <= 5,
            detail: `${validationWarningCount} 项提醒`,
            missing: "把明显提醒项降到 5 项以内。",
            action: actions.inspection,
          }),
        ],
        fallbackActions: [actions.preview, actions.inspection],
      }),
      createMilestone({
        id: "release_candidate",
        title: "发布候选版",
        label: "准备给别人下载",
        summaryWhenDone: "发布候选核心条件已经达标，可以进入人工长流程试玩和附件整理。",
        summaryWhenOpen: "目标是把明显会被吐槽的断线、缺素材、未导出、未回归这些风险压下去。",
        checks: [
          createCheck({
            id: "zero_errors",
            label: "结构错误清零",
            done: validationErrorCount === 0,
            detail: `${validationErrorCount} 项错误`,
            missing: "先清零项目错误。",
            weight: 3,
            action: actions.inspection,
          }),
          createCheck({
            id: "zero_broken_routes",
            label: "路线坏链清零",
            done: brokenRoutes === 0,
            detail: `${brokenRoutes} 条坏链`,
            missing: "修复所有坏链。",
            weight: 3,
            action: actions.inspection,
          }),
          createCheck({
            id: "reachable_scenes",
            label: "重要场景可抵达",
            done: totalScenes <= 1 || orphanScenes === 0,
            detail: `${orphanScenes} 个孤立场景`,
            missing: "检查孤立场景是否需要接回主线。",
            action: actions.inspection,
          }),
          createCheck({
            id: "release_assets",
            label: "发布素材基本齐",
            done: totalAssetCount > 0 && assetCoverage >= 90,
            detail: totalAssetCount > 0 ? `${assetCoverage}% 素材就绪` : "还没有素材条目",
            missing: "把素材真实文件补到 90% 以上。",
            weight: 2,
            action: actions.assets,
          }),
          createCheck({
            id: "no_demo_placeholders",
            label: "无明显 Demo 占位内容",
            done: placeholderContentCount === 0,
            detail:
              placeholderContentCount === 0
                ? "没有明显占位内容"
                : `占位素材 ${placeholderAssetCount} 个 / 待补正文 ${placeholderScriptCount} 条`,
            missing: "发布前把 Demo 占位素材和待补正文替换掉。",
            weight: 2,
            action: actions.replacePlaceholders,
          }),
          createCheck({
            id: "voice_optional_polish",
            label: "语音覆盖可说明",
            done: totalDialogueCount === 0 || voiceCoverage >= 60,
            detail: totalDialogueCount === 0 ? "无台词语音需求" : `${voiceCoverage}% 台词已绑语音`,
            missing: "如定位为有声作品，先把重点台词语音补到 60% 以上。",
            action: actions.assets,
          }),
          createCheck({
            id: "regression",
            label: "自动回归试玩通过",
            done: regressionPass,
            detail: regressionPass ? "最近一次回归通过" : "还没有通过记录",
            missing: "运行一次自动回归试玩。",
            weight: 2,
            action: actions.regression,
          }),
          createCheck({
            id: "exported",
            label: "已经导出过一版",
            done: hasExport,
            detail: hasExport ? "已有导出记录" : "尚未导出",
            missing: "先导出一版网页包或桌面包。",
            weight: 2,
            action: actions.exportWeb,
          }),
        ],
        fallbackActions: [actions.inspection, actions.preview],
      }),
    ];

    const nextMilestone = milestones.find((milestone) => !milestone.done) ?? milestones[milestones.length - 1];
    const completedCount = milestones.filter((milestone) => milestone.done).length;
    const overallScore = clampPercent(
      milestones.reduce((total, milestone) => total + milestone.percent, 0) / Math.max(milestones.length, 1)
    );

    return {
      overallScore,
      completedCount,
      totalCount: milestones.length,
      nextMilestone,
      milestones,
      headline:
        completedCount === milestones.length
          ? "三阶段目标都已达标，接下来适合做人工长流程试玩和发布素材整理。"
          : `当前优先推进：${nextMilestone.title}。`,
    };
  }

  function buildProjectMilestoneGapDigest(plan = {}) {
    const milestones = Array.isArray(plan?.milestones) ? plan.milestones : [];
    const releaseMilestone =
      milestones.find((milestone) => milestone?.id === "release_candidate") ?? milestones[milestones.length - 1] ?? null;
    const nextMilestone = plan?.nextMilestone ?? milestones.find((milestone) => !milestone?.done) ?? releaseMilestone;
    const isReleasePhase = nextMilestone?.id === "release_candidate" || Boolean(releaseMilestone?.done);
    const releaseBlockers = Array.isArray(releaseMilestone?.blockers) ? releaseMilestone.blockers : [];
    const nextBlockers = Array.isArray(nextMilestone?.blockers) ? nextMilestone.blockers : [];
    const activeBlockers = isReleasePhase ? releaseBlockers : nextBlockers;
    const primaryGap = activeBlockers[0] ?? nextBlockers[0] ?? releaseBlockers[0] ?? null;
    const releaseDone = Boolean(releaseMilestone?.done);
    const overallScore = clampPercent(plan?.overallScore ?? 0);
    const completedCount = toCount(plan?.completedCount);
    const totalCount = toCount(plan?.totalCount || milestones.length);
    const activePercent = clampPercent(nextMilestone?.percent ?? releaseMilestone?.percent ?? 0);
    const status = releaseDone ? "ready" : activeBlockers.length <= 2 && (activePercent >= 70 || overallScore >= 70) ? "close" : "open";
    const nextAction =
      (Array.isArray(nextMilestone?.actions) && nextMilestone.actions[0]) ||
      (Array.isArray(releaseMilestone?.actions) && releaseMilestone.actions[0]) ||
      null;

    return {
      status,
      eyebrow: releaseDone || isReleasePhase ? "发布候选差距" : "当前阶段缺口",
      title: releaseDone
        ? "发布候选核心条件已达标"
        : activeBlockers.length > 0
          ? `${nextMilestone?.title ?? "当前阶段"}还差 ${activeBlockers.length} 项`
          : `继续确认${nextMilestone?.title ?? "当前阶段"}状态`,
      description: releaseDone
        ? "核心发布门槛已经通过，接下来适合人工长流程试玩、整理附件和准备 Release notes。"
        : primaryGap
          ? `先处理「${primaryGap.missing || primaryGap.label}」，然后重新跑一次巡检和试玩。`
          : "继续按当前阶段推进，完成后再做发布候选确认。",
      overallScore,
      completedCount,
      totalCount,
      activePercent,
      releasePercent: clampPercent(releaseMilestone?.percent ?? 0),
      activeBlockerCount: activeBlockers.length,
      releaseBlockerCount: releaseBlockers.length,
      gapMetricLabel: releaseDone || isReleasePhase ? "候选缺口" : "阶段缺口",
      gapMetricHint: releaseDone || isReleasePhase ? "发布前建议清零" : "先清掉这一阶段",
      nextMilestoneTitle: nextMilestone?.title ?? "继续推进当前项目",
      primaryGap,
      topGaps: activeBlockers.slice(0, 4),
      nextAction,
    };
  }

  function getActionKey(action = {}) {
    return [
      action.action ?? "",
      action.screen ?? action.dataset?.screen ?? "",
      action.sceneId ?? "",
      action.blockId ?? "",
      action.characterId ?? "",
      action.chapterId ?? "",
      action.assetId ?? "",
      action.dataset?.["export-target"] ?? action.dataset?.exportTarget ?? "",
    ].join(":");
  }

  function normalizeBriefAction(action, fallback = null) {
    const base = action && typeof action === "object" ? action : fallback;
    if (!base || typeof base !== "object") {
      return null;
    }
    const normalized = {
      label: String(base.label ?? "去处理"),
      action: String(base.action ?? "switch-screen"),
    };
    ["href", "screen", "sceneId", "blockId", "characterId", "chapterId", "assetId"].forEach((key) => {
      if (base[key]) {
        normalized[key] = String(base[key]);
      }
    });
    if (base.dataset && typeof base.dataset === "object") {
      normalized.dataset = { ...base.dataset };
    }
    return normalized;
  }

  function dedupeBriefActions(actions = []) {
    const seen = new Set();
    const normalizedActions = [];
    actions
      .map((action) => normalizeBriefAction(action))
      .filter(Boolean)
      .forEach((action) => {
        const key = getActionKey(action);
        if (seen.has(key)) {
          return;
        }
        seen.add(key);
        normalizedActions.push(action);
      });
    return normalizedActions;
  }

  function buildProjectMilestoneActionBrief(plan = {}) {
    const digest = buildProjectMilestoneGapDigest(plan);
    const focusMilestone = plan.nextMilestone ?? (Array.isArray(plan.milestones) ? plan.milestones[0] : null);
    const primaryGap = digest.primaryGap ?? null;
    const isReady = digest.status === "ready";
    const primaryAction = normalizeBriefAction(
      isReady
        ? { label: "去试玩验收", action: "switch-screen", screen: "preview" }
        : digest.nextAction,
      { label: "打开项目巡检", action: "switch-screen", screen: "inspection" }
    );
    const secondarySeedActions = isReady
      ? [
          { label: "重新导出网页包", action: "export-build", dataset: { "export-target": "web" } },
          { label: "打开项目巡检", action: "switch-screen", screen: "inspection" },
          { label: "查看成品路线", action: "switch-screen", screen: "dashboard" },
        ]
      : [
          { label: "打开项目巡检", action: "switch-screen", screen: "inspection" },
          { label: "查看成品路线", action: "switch-screen", screen: "dashboard" },
          { label: "去试玩确认", action: "switch-screen", screen: "preview" },
        ];
    const secondaryActions = dedupeBriefActions([
      primaryAction,
      ...secondarySeedActions,
    ]).filter((action) => getActionKey(action) !== getActionKey(primaryAction));

    const checklist = isReady
      ? [
          {
            label: "人工长流程试玩",
            detail: "从头到尾跑一次主要路线，记录卡顿、错字和演出节奏问题。",
            done: false,
          },
          {
            label: "整理发布附件",
            detail: "确认下载包、校验文件、说明文档和截图都已准备好。",
            done: false,
          },
          {
            label: "撰写 Release notes",
            detail: "用玩家能看懂的话说明当前版本能做什么、已知限制是什么。",
            done: false,
          },
        ]
      : (digest.topGaps ?? []).slice(0, 3).map((gap) => ({
          label: gap.label ?? "待处理项",
          detail: gap.missing || gap.detail || "继续补齐这个条件。",
          done: Boolean(gap.done),
        }));

    return {
      status: digest.status,
      tone: isReady ? "good" : digest.status === "close" ? "warn" : "danger",
      eyebrow: isReady ? "今日工作台" : digest.eyebrow,
      badge: isReady ? "准备验收" : digest.status === "close" ? "快到发布" : "优先推进",
      title: isReady
        ? "进入人工验收和发布附件整理"
        : primaryGap
          ? `先做：${primaryGap.missing || primaryGap.label}`
          : digest.title,
      description: isReady
        ? "核心发布门槛已经达标，现在最值钱的是人工试玩、附件整理和版本说明。"
        : `这是通往「${digest.nextMilestoneTitle || focusMilestone?.title || "当前阶段"}」的最短路径；做完后再跑一次巡检和试玩确认。`,
      primaryAction,
      secondaryActions: secondaryActions.slice(0, 2),
      metrics: [
        { label: "总进度", value: `${digest.overallScore}%`, hint: `${digest.completedCount}/${digest.totalCount} 个阶段达标` },
        {
          label: digest.gapMetricLabel ?? "阶段缺口",
          value: `${digest.activeBlockerCount ?? digest.releaseBlockerCount ?? 0} 项`,
          hint: digest.gapMetricHint ?? "先清掉这一阶段",
        },
        { label: "当前阶段", value: digest.nextMilestoneTitle, hint: focusMilestone?.label ?? "按按钮继续推进" },
      ],
      checklist,
    };
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function renderProjectMilestoneGapList(gaps = [], options = {}) {
    const escape = typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtml;
    const safeGaps = Array.isArray(gaps) ? gaps : [];

    if (!safeGaps.length) {
      return `
      <div class="project-milestone-gap-list">
        <article class="project-milestone-gap-item is-done">
          <strong>核心发布门槛已达标</strong>
          <span>可以进入人工长流程试玩、附件整理和 Release notes 准备。</span>
        </article>
      </div>
    `;
    }

    return `
    <div class="project-milestone-gap-list">
      ${safeGaps
        .map(
          (gap) => `
            <article class="project-milestone-gap-item">
              <strong>${escape(gap.label ?? "待处理项")}</strong>
              <span>${escape(gap.missing || gap.detail || "继续补齐这个发布候选条件。")}</span>
            </article>
          `
        )
        .join("")}
    </div>
  `;
  }

  function renderProjectMilestoneChecklist(checks = [], options = {}) {
    const escape = typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtml;
    const safeChecks = Array.isArray(checks) ? checks : [];
    const orderedChecks = [...safeChecks.filter((check) => !check.done), ...safeChecks.filter((check) => check.done)];
    const visibleChecks = orderedChecks.slice(0, 5);
    const hiddenCount = Math.max(orderedChecks.length - visibleChecks.length, 0);

    return `
    <div class="project-milestone-checklist">
      ${visibleChecks
        .map(
          (check) => `
            <div class="project-milestone-check ${check.done ? "is-done" : "is-open"}">
              <span class="project-milestone-check-dot" aria-hidden="true"></span>
              <div>
                <strong>${escape(check.label)}</strong>
                <span>${escape(check.done ? check.detail : check.missing)}</span>
              </div>
            </div>
          `
        )
        .join("")}
      ${
        hiddenCount > 0
          ? `<div class="project-milestone-more">还有 ${hiddenCount} 项细节已收起，进入项目巡检可继续查看。</div>`
          : ""
      }
    </div>
  `;
  }

  function renderProjectMilestoneActions(actions = [], options = {}) {
    const safeActions = Array.isArray(actions) ? actions : [];
    const renderQuickActionButton =
      typeof options.renderQuickActionButton === "function"
        ? options.renderQuickActionButton
        : (action, emphasized = false) => {
            const escape = typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtml;
            const className = `toolbar-button${emphasized ? " toolbar-button-primary" : ""}`;
            return `<button type="button" class="${className}" data-action="${escape(action.action ?? "")}">${escape(
              action.label ?? "去处理"
            )}</button>`;
          };

    if (safeActions.length === 0) {
      return `
      <button type="button" class="toolbar-button toolbar-button-primary" data-action="switch-screen" data-screen="preview">
        去试玩确认
      </button>
    `;
    }

    return safeActions.map((action, index) => renderQuickActionButton(action, index === 0)).join("");
  }

  const projectMilestonesApi = Object.freeze({
    buildProjectMilestoneActionBrief,
    buildProjectMilestonePlan,
    buildProjectMilestoneGapDigest,
    clampPercent,
    getPercent,
    renderProjectMilestoneGapList,
    renderProjectMilestoneChecklist,
    renderProjectMilestoneActions,
  });
  global.CanvasiaProjectMilestones = projectMilestonesApi;
  global.CanvasiaEditorProjectMilestones = projectMilestonesApi;
})(typeof window !== "undefined" ? window : globalThis);
