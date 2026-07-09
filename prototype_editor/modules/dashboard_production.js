(function attachDashboardProductionTools(global) {
  const SCENE_PRIORITY_LABELS = Object.freeze({
    parked: "先放一放",
    normal: "正常推进",
    focus: "优先处理",
    rush: "马上处理",
  });

  const SCENE_STATUS_LABELS = Object.freeze({
    outline: "待开写",
    drafting: "写作中",
    polishing: "润色中",
    ready: "可试玩",
  });

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function toCount(value, fallback = 0) {
    const numberValue = Number(value);
    if (!Number.isFinite(numberValue)) {
      return fallback;
    }
    return Math.max(0, Math.round(numberValue));
  }

  function getMetrics(routeOverview = {}) {
    return routeOverview.metrics ?? {};
  }

  function getSafeScenePriority(priority, helpers = {}) {
    if (typeof helpers.getSafeScenePriority === "function") {
      return helpers.getSafeScenePriority(priority);
    }
    const safePriority = String(priority ?? "normal").trim();
    return Object.hasOwn(SCENE_PRIORITY_LABELS, safePriority) ? safePriority : "normal";
  }

  function getSafeSceneStatus(status, helpers = {}) {
    if (typeof helpers.getSafeSceneStatus === "function") {
      return helpers.getSafeSceneStatus(status);
    }
    const safeStatus = String(status ?? "outline").trim();
    return Object.hasOwn(SCENE_STATUS_LABELS, safeStatus) ? safeStatus : "outline";
  }

  function getScenePriorityLabel(priority, helpers = {}) {
    if (typeof helpers.getScenePriorityLabel === "function") {
      return helpers.getScenePriorityLabel(priority);
    }
    return SCENE_PRIORITY_LABELS[getSafeScenePriority(priority, helpers)] ?? SCENE_PRIORITY_LABELS.normal;
  }

  function getSceneStatusLabel(status, helpers = {}) {
    if (typeof helpers.getSceneStatusLabel === "function") {
      return helpers.getSceneStatusLabel(status);
    }
    return SCENE_STATUS_LABELS[getSafeSceneStatus(status, helpers)] ?? SCENE_STATUS_LABELS.outline;
  }

  function buildRouteSceneProductionNotes(scene, helpers = {}) {
    if (typeof helpers.buildRouteSceneProductionNotes === "function") {
      return helpers.buildRouteSceneProductionNotes(scene);
    }
    return [];
  }

  function buildDashboardProductionSummary({
    readinessScore,
    routeOverview = {},
    issueEntryCount,
    missingVoiceCount,
    directionIdeaCount,
  }) {
    const metrics = getMetrics(routeOverview);
    if ((metrics.brokenRoutes ?? 0) > 0) {
      return "目前最先该修的是路线断线，不然试玩时很容易直接卡住。";
    }

    if ((metrics.unreachableScenes ?? 0) > 0) {
      return `有 ${metrics.unreachableScenes} 个场景从入口暂时走不到，先接通主路线会更稳。`;
    }

    if (issueEntryCount > 0) {
      return `台本里还有 ${issueEntryCount} 条需要体检的正文，先补这些会让后面统稿轻松很多。`;
    }

    if (missingVoiceCount > 0) {
      return `台词主体已经能看了，下一步最适合继续补语音，现在还差 ${missingVoiceCount} 句。`;
    }

    if (directionIdeaCount > 0) {
      return "剧情骨架已经立住了，接下来最值的是挑几句高光台词补镜头和特效。";
    }

    if (readinessScore >= 75) {
      return "整体已经有成品味道了，现在更适合回去抛光演出和试玩手感。";
    }

    return "现在最适合继续往前填内容，把空场景、背景和音乐慢慢补齐。";
  }

  function getDashboardProgressPercent(done, total) {
    if (!total || total <= 0) {
      return 100;
    }

    return Math.max(0, Math.min(100, Math.round((done / total) * 100)));
  }

  function getScenePlanningPriorityRank(priority, helpers = {}) {
    const safePriority = getSafeScenePriority(priority, helpers);
    if (safePriority === "rush") {
      return 4;
    }
    if (safePriority === "focus") {
      return 3;
    }
    if (safePriority === "normal") {
      return 2;
    }
    return 0;
  }

  function getScenePlanningStatusRank(status, helpers = {}) {
    const safeStatus = getSafeSceneStatus(status, helpers);
    if (safeStatus === "ready") {
      return 4;
    }
    if (safeStatus === "polishing") {
      return 3;
    }
    if (safeStatus === "drafting") {
      return 2;
    }
    return 1;
  }

  function getScenePlanningTone(scene = {}, helpers = {}) {
    const safePriority = getSafeScenePriority(scene.priority, helpers);
    const safeStatus = getSafeSceneStatus(scene.status, helpers);

    if (safePriority === "rush") {
      return "danger";
    }
    if (safePriority === "focus" || safeStatus === "polishing") {
      return "warn";
    }
    if (safeStatus === "ready") {
      return "good";
    }
    return "soft";
  }

  function buildDashboardScenePlanningSummary(scene = {}, helpers = {}) {
    const productionNotes = buildRouteSceneProductionNotes(scene, helpers);
    const pieces = [
      `${getSceneStatusLabel(scene.status, helpers)} / ${getScenePriorityLabel(scene.priority, helpers)}`,
      `正文 ${(scene.dialogueCount ?? 0) + (scene.narrationCount ?? 0) + (scene.choiceCount ?? 0)} 张`,
    ];

    if (!scene.hasBackground) {
      pieces.push("还没放背景");
    } else if (!scene.hasMusic && scene.hasStoryContent) {
      pieces.push("可以再补 BGM");
    } else if ((scene.missingVoiceCount ?? 0) > 0) {
      pieces.push(`还差 ${scene.missingVoiceCount} 句语音`);
    } else if (!scene.hasEffects && scene.hasStoryContent) {
      pieces.push("适合加一点演出");
    } else {
      pieces.push(productionNotes[0] ?? "可以继续抛光");
    }

    return pieces.join(" · ");
  }

  function buildDashboardScenePlanningNextStep(scene = {}) {
    return buildDashboardScenePlayableChecklist(scene).nextStep;
  }

  function getSceneChecklistFocusHint(checklistItem, checklistLabel = "") {
    const safeItem = cleanText(checklistItem);
    const safeLabel = cleanText(checklistLabel);
    const hints = {
      story: {
        title: "先补正文",
        description: "先加一两张对白、旁白或选项卡，让这个场景至少能从头读到尾。",
        toast: "先补正文，让这段先跑起来",
        actions: [
          {
            label: "加台词卡",
            action: "add-dialogue",
            primary: true,
            dataset: { "scene-checklist-complete": "story" },
          },
          {
            label: "加旁白卡",
            action: "add-narration",
            dataset: { "scene-checklist-complete": "story" },
          },
          {
            label: "加选项卡",
            action: "add-choice",
            dataset: { "scene-checklist-complete": "story" },
          },
        ],
      },
      background: {
        title: "补背景",
        description: "先给这段切一张背景图，再继续补台词，画面完成感会立刻上来。",
        toast: "先补背景，画面会更完整",
        actions: [
          {
            label: "加背景卡",
            action: "add-background",
            primary: true,
            dataset: { "scene-checklist-complete": "background" },
          },
        ],
      },
      music: {
        title: "补 BGM",
        description: "给这一段加一张 BGM 或音乐范围卡，先把氛围托住，再继续细修台词。",
        toast: "先补 BGM，把氛围托起来",
        actions: [
          {
            label: "加 BGM 卡",
            action: "add-music-play",
            primary: true,
            dataset: { "scene-checklist-complete": "music" },
          },
        ],
      },
      voice: {
        title: "补语音",
        description: "优先给主要角色台词绑定语音或占位语音，之后试玩时更容易检查节奏。",
        toast: "先补语音，检查台词节奏",
        actions: [
          {
            label: "只看待绑语音",
            action: "focus-story-block-filters",
            primary: true,
            dataset: { "story-block-type": "dialogue", "story-block-issue": "missing_voice" },
          },
        ],
      },
      presentation: {
        title: "加镜头 / 特效",
        description: "给关键句补淡入淡出、镜头、粒子或滤镜，让这一段更像正式演出。",
        toast: "先加演出，让这段更有完成度",
        actions: [
          {
            label: "加镜头缩放",
            action: "add-camera-zoom",
            primary: true,
            dataset: { "scene-checklist-complete": "presentation" },
          },
          {
            label: "加粒子特效",
            action: "add-particle-effect",
            dataset: { "scene-checklist-complete": "presentation" },
          },
          {
            label: "加淡入淡出",
            action: "add-screen-fade",
            dataset: { "scene-checklist-complete": "presentation" },
          },
        ],
      },
    };
    const hint = hints[safeItem];
    if (hint) {
      return { ...hint, item: safeItem, label: safeLabel || hint.title };
    }
    if (!safeLabel) {
      return null;
    }
    return {
      item: safeItem || "custom",
      label: safeLabel,
      title: safeLabel,
      description: "已打开对应场景，可以先按这个缺口继续补内容。",
      toast: safeLabel,
      actions: [],
    };
  }

  function makeSceneChecklistAction(scene, label) {
    return {
      label,
      action: "open-scene-from-map",
      sceneId: cleanText(scene.id),
    };
  }

  function makeSceneChecklistItem({ id, label, ready, pending = false, essential = false, readyText, missingText, pendingText, action }) {
    const status = ready ? "ready" : pending ? "pending" : "missing";
    return {
      id,
      label,
      essential,
      status,
      tone: status === "ready" ? "good" : essential ? "warn" : "soft",
      text: status === "ready" ? readyText : status === "pending" ? pendingText : missingText,
      action: status === "ready" ? null : action,
    };
  }

  function buildDashboardScenePlayableChecklist(scene = {}) {
    const dialogueCount = toCount(scene.dialogueCount);
    const narrationCount = toCount(scene.narrationCount);
    const choiceCount = toCount(scene.choiceCount);
    const textBlockCount = dialogueCount + narrationCount + choiceCount;
    const hasStoryContent = Boolean(scene.hasStoryContent) || textBlockCount > 0;
    const hasBackground = Boolean(scene.hasBackground);
    const hasMusic = Boolean(scene.hasMusic);
    const hasEffects = Boolean(scene.hasEffects);
    const missingVoiceCount = toCount(scene.missingVoiceCount);
    const checklist = [
      makeSceneChecklistItem({
        id: "story",
        label: "正文",
        essential: true,
        ready: hasStoryContent,
        readyText: textBlockCount > 0 ? `正文 ${textBlockCount} 张` : "已有正文骨架",
        missingText: "先补正文",
        action: makeSceneChecklistAction(scene, "补正文"),
      }),
      makeSceneChecklistItem({
        id: "background",
        label: "背景",
        essential: true,
        ready: hasBackground,
        pending: !hasStoryContent,
        readyText: "已有背景",
        missingText: "补背景",
        pendingText: "等正文后补背景",
        action: makeSceneChecklistAction(scene, "补背景"),
      }),
      makeSceneChecklistItem({
        id: "music",
        label: "BGM",
        essential: true,
        ready: hasMusic,
        pending: !hasStoryContent,
        readyText: "已有 BGM",
        missingText: "补 BGM",
        pendingText: "等正文后配 BGM",
        action: makeSceneChecklistAction(scene, "补 BGM"),
      }),
      makeSceneChecklistItem({
        id: "voice",
        label: "语音",
        ready: missingVoiceCount === 0,
        pending: !hasStoryContent,
        readyText: "语音已齐",
        missingText: `缺语音 ${missingVoiceCount} 句`,
        pendingText: "等台词后配语音",
        action: makeSceneChecklistAction(scene, "补语音"),
      }),
      makeSceneChecklistItem({
        id: "presentation",
        label: "演出",
        ready: hasEffects,
        pending: !hasStoryContent,
        readyText: "已有演出",
        missingText: "加镜头 / 特效",
        pendingText: "等正文后补演出",
        action: makeSceneChecklistAction(scene, "补演出"),
      }),
    ];
    const readyCount = checklist.filter((item) => item.status === "ready").length;
    const missingItems = checklist.filter((item) => item.status !== "ready");
    const essentialMissingCount = checklist.filter((item) => item.essential && item.status !== "ready").length;
    const firstMissing = missingItems.find((item) => item.status === "missing") ?? missingItems[0] ?? null;
    const score = getDashboardProgressPercent(readyCount, checklist.length);
    const status = essentialMissingCount > 0 ? "needs_core" : missingItems.length > 0 ? "needs_polish" : "ready";
    return {
      status,
      score,
      readyCount,
      totalCount: checklist.length,
      missingCount: missingItems.length,
      essentialMissingCount,
      label: status === "ready" ? "可试玩" : status === "needs_polish" ? "可试玩，待打磨" : "还差基础项",
      nextStep: firstMissing
        ? firstMissing.status === "pending"
          ? firstMissing.text
          : `${firstMissing.text}，让这段更接近可试玩。`
        : "这段已经有试玩味道了，可以回去跑一遍手感。",
      firstMissing,
      items: checklist,
    };
  }

  function buildSceneOpenFocusAction(scene = {}, item = {}, options = {}) {
    const sceneId = cleanText(scene.id);
    if (!sceneId) {
      return null;
    }
    const label = cleanText(options.label, item.action?.label ?? item.text ?? "打开场景");
    return {
      label,
      action: "open-scene-from-map",
      sceneId,
      dataset: {
        "scene-checklist-item": cleanText(item.id, "custom"),
        "scene-checklist-label": label,
      },
    };
  }

  function buildDashboardScenePlayableActionPlan(scene = {}, checklist = null) {
    const sceneId = cleanText(scene.id);
    if (!sceneId) {
      return [];
    }

    const safeChecklist = checklist ?? buildDashboardScenePlayableChecklist(scene);
    const firstMissing = safeChecklist.firstMissing;
    if (!firstMissing) {
      return [
        {
          label: "从这里试玩",
          action: "preview-scene-from-map",
          sceneId,
        },
      ];
    }

    const actions = [];
    if (firstMissing.id === "story" && firstMissing.status === "missing") {
      actions.push({
        label: "生成可试玩段落",
        action: "apply-story-template-to-scene",
        dataset: {
          "scene-id": sceneId,
          "template-id": "playable_scene",
          "scene-checklist-complete": "story",
        },
      });
      actions.push(buildSceneOpenFocusAction(scene, firstMissing, { label: "打开这里继续写" }));
      return actions.filter(Boolean);
    }

    const focusHint = getSceneChecklistFocusHint(firstMissing.id, firstMissing.action?.label ?? firstMissing.text);
    actions.push(buildSceneOpenFocusAction(scene, firstMissing, { label: focusHint?.title ?? firstMissing.action?.label }));

    if (safeChecklist.status !== "needs_core") {
      actions.push({
        label: "试玩这一段",
        action: "preview-scene-from-map",
        sceneId,
      });
    }

    return actions.filter(Boolean).slice(0, 2);
  }

  function buildDashboardScenePlanningQueue(routeOverview = {}, helpers = {}) {
    return toArray(routeOverview.nodes)
      .filter((scene) => {
        const safePriority = getSafeScenePriority(scene.priority, helpers);
        const safeStatus = getSafeSceneStatus(scene.status, helpers);
        return safePriority !== "parked" && (safePriority !== "normal" || safeStatus !== "drafting" || Boolean(scene.notes));
      })
      .map((scene) => {
        const playableChecklist = buildDashboardScenePlayableChecklist(scene);
        return {
          ...scene,
          tone: getScenePlanningTone(scene, helpers),
          summary: buildDashboardScenePlanningSummary(scene, helpers),
          playableChecklist,
          playableActionPlan: buildDashboardScenePlayableActionPlan(scene, playableChecklist),
          nextStep: buildDashboardScenePlanningNextStep(scene),
          planningScore:
            getScenePlanningPriorityRank(scene.priority, helpers) * 100 +
            getScenePlanningStatusRank(scene.status, helpers) * 20 +
            (scene.completionScore ?? 0),
        };
      })
      .sort((left, right) => right.planningScore - left.planningScore);
  }

  function buildDashboardProductionTasks(routeOverview = {}, overview = {}, options = {}) {
    const helpers = options.helpers ?? {};
    const validationErrors = toArray(options.validationErrors);
    const tasks = [];
    const pushTask = (task) => tasks.push(task);
    const alerts = toArray(routeOverview.alerts);
    const metrics = getMetrics(routeOverview);
    const primaryDangerAlert = alerts.find((alert) => alert.tone === "danger");
    const primaryReachabilityAlert = alerts.find((alert) => alert.label === "不可达");
    const structuralError = validationErrors.find(
      (issue) => !/目标场景不存在|章节顺序里引用了不存在的场景/.test(issue.message)
    );
    const plannedFocusScene = toArray(overview.plannedScenes).find((scene) =>
      ["rush", "focus"].includes(getSafeScenePriority(scene.priority, helpers))
    );
    const emptyScene = toArray(overview.emptyScenes)[0] ?? null;
    const missingBackgroundScene = toArray(overview.scenesMissingBackground)[0] ?? null;
    const missingMusicScene = toArray(overview.scenesMissingMusic)[0] ?? null;
    const flatScene = toArray(overview.flatScenes)[0] ?? null;
    const topIssueEntry = toArray(overview.issueEntries)[0] ?? null;

    if (primaryDangerAlert) {
      pushTask({
        priority: 120,
        tone: "danger",
        badge: `坏链 ${metrics.brokenRoutes ?? 0} 处`,
        title: "先修路线断线",
        description: `${primaryDangerAlert.sceneName} 里有一条跳转还没接到真实场景，试玩时最容易在这里断掉。`,
        meta: primaryDangerAlert.meta,
        actions: [
          {
            label: "打开场景",
            action: "open-scene-from-map",
            sceneId: primaryDangerAlert.sceneId,
          },
        ],
      });
    }

    if (structuralError) {
      pushTask({
        priority: 112,
        tone: "danger",
        badge: `结构错误 ${validationErrors.length} 项`,
        title: "先处理结构问题",
        description: structuralError.message,
        meta: structuralError.location,
        actions: [
          {
            label: "去预览导出页看检查",
            action: "switch-screen",
            screen: "preview",
          },
        ],
      });
    }

    if (primaryReachabilityAlert) {
      pushTask({
        priority: 108,
        tone: "warn",
        badge: `不可达 ${metrics.unreachableScenes ?? 0} 个`,
        title: "接通入口走不到的场景",
        description: `${primaryReachabilityAlert.sceneName} 已经有内容或入口线，但从项目入口试玩时暂时走不到。`,
        meta: primaryReachabilityAlert.meta,
        actions: [
          {
            label: "打开场景",
            action: "open-scene-from-map",
            sceneId: primaryReachabilityAlert.sceneId,
          },
          {
            label: "只看不可达",
            action: "set-route-map-filter",
            dataset: { "route-filter": "unreachable" },
          },
        ],
      });
    }

    if (plannedFocusScene) {
      const safePriority = getSafeScenePriority(plannedFocusScene.priority, helpers);
      pushTask({
        priority: safePriority === "rush" ? 106 : 90,
        tone: safePriority === "rush" ? "danger" : "warn",
        badge: `${getScenePriorityLabel(plannedFocusScene.priority, helpers)} · ${getSceneStatusLabel(
          plannedFocusScene.status,
          helpers
        )}`,
        title: "跟进你手动标记的重点场景",
        description: `${plannedFocusScene.chapterName} / ${plannedFocusScene.name} 已经被你标成“${getScenePriorityLabel(
          plannedFocusScene.priority,
          helpers
        )}”，现在最适合回去把这一段继续往前推。`,
        meta: plannedFocusScene.notes || plannedFocusScene.nextStep,
        actions: [
          {
            label: "继续写这里",
            action: "open-scene-from-map",
            sceneId: plannedFocusScene.id,
          },
          {
            label: getSafeSceneStatus(plannedFocusScene.status, helpers) === "ready" ? "直接试玩" : "先试玩这段",
            action: "preview-scene-from-map",
            sceneId: plannedFocusScene.id,
          },
        ],
      });
    }

    if (emptyScene) {
      pushTask({
        priority: 100,
        tone: "warn",
        badge: `空场景 ${toArray(overview.emptyScenes).length} 个`,
        title: "补可试玩正文",
        description: `还有 ${toArray(overview.emptyScenes).length} 个场景几乎还没有正文内容，补出基础台词、旁白或选项后，试玩链会更完整。`,
        meta: `${emptyScene.name} 目前还没有可试玩内容`,
        actions: [
          {
            label: "打开这个空场景",
            action: "open-scene-from-map",
            sceneId: emptyScene.id,
          },
        ],
      });
    }

    if (missingBackgroundScene) {
      pushTask({
        priority: 92,
        tone: "warn",
        badge: `缺背景 ${toArray(overview.scenesMissingBackground).length} 场`,
        title: "给场景补舞台感",
        description: `还有 ${toArray(overview.scenesMissingBackground).length} 个有正文的场景没切背景，补上背景后，画面完成度会明显提升。`,
        meta: `${missingBackgroundScene.name} 现在还没放背景卡片`,
        actions: [
          {
            label: "打开这个场景",
            action: "open-scene-from-map",
            sceneId: missingBackgroundScene.id,
          },
          {
            label: "去素材页找背景",
            action: "switch-screen",
            screen: "assets",
          },
        ],
      });
    }

    if ((overview.missingVoiceCount ?? 0) > 0) {
      pushTask({
        priority: 88,
        tone: "warn",
        badge: `待配音 ${overview.missingVoiceCount} 句`,
        title: "继续补语音覆盖",
        description: `主台词里还有 ${overview.missingVoiceCount} 句没绑语音。现在去补，会让试玩手感一下子更像正式 galgame。`,
        meta: `当前整体语音覆盖率 ${overview.voiceProgress}%`,
        actions: [
          {
            label: "只看待绑语音",
            action: "focus-script-missing-voice",
          },
          {
            label: "打开角色页",
            action: "switch-screen",
            screen: "characters",
          },
        ],
      });
    }

    if (topIssueEntry) {
      const issueEntries = toArray(overview.issueEntries);
      const placeholderCount = issueEntries.filter((entry) => toArray(entry.issues).includes("placeholder")).length;
      const longCount = issueEntries.filter((entry) => toArray(entry.issues).includes("too_long")).length;
      const duplicateCount = issueEntries.filter((entry) => toArray(entry.issues).includes("duplicate")).length;
      const issuePieces = [
        placeholderCount > 0 ? `待补正文 ${placeholderCount}` : "",
        longCount > 0 ? `偏长 ${longCount}` : "",
        duplicateCount > 0 ? `疑似重复 ${duplicateCount}` : "",
      ].filter(Boolean);

      pushTask({
        priority: 82,
        tone: "warn",
        badge: `文本体检 ${overview.issueEntryCount} 条`,
        title: "先清一轮台本文本问题",
        description: `台本里已经自动查出了 ${overview.issueEntryCount} 条更值得优先处理的正文。`,
        meta: issuePieces.join(" / ") || topIssueEntry.title,
        actions: [
          {
            label: "只看有问题台本",
            action: "focus-script-issues",
          },
          {
            label: "打开第一条",
            action: "open-character-line",
            sceneId: topIssueEntry.sceneId,
            blockId: topIssueEntry.blockId,
          },
        ],
      });
    }

    if (missingMusicScene) {
      pushTask({
        priority: 70,
        tone: "soft",
        badge: `缺音乐 ${toArray(overview.scenesMissingMusic).length} 场`,
        title: "给关键场景补 BGM",
        description: `还有 ${toArray(overview.scenesMissingMusic).length} 个有正文的场景没有背景音乐，补上后氛围会更完整。`,
        meta: `${missingMusicScene.name} 现在还没放音乐卡片`,
        actions: [
          {
            label: "打开这个场景",
            action: "open-scene-from-map",
            sceneId: missingMusicScene.id,
          },
          {
            label: "去素材页找 BGM",
            action: "switch-screen",
            screen: "assets",
          },
        ],
      });
    }

    if (toArray(overview.unusedAssets).length > 0) {
      pushTask({
        priority: 64,
        tone: "soft",
        badge: `闲置素材 ${toArray(overview.unusedAssets).length} 个`,
        title: "清一轮无用素材",
        description: `素材库里还有 ${toArray(overview.unusedAssets).length} 个文件暂时没被剧情引用，整理一下会让工程更干净。`,
        meta: `${overview.unusedAssets[0].name} 等素材还没用上`,
        actions: [
          {
            label: "去素材页定位",
            action: "focus-unused-assets",
          },
        ],
      });
    }

    if (flatScene && (overview.directionIdeaCount ?? 0) > 0) {
      pushTask({
        priority: 56,
        tone: "good",
        badge: `演出灵感 ${overview.directionIdeaCount} 句`,
        title: "给高光句补镜头和特效",
        description: `台本里已经有 ${overview.directionIdeaCount} 句很适合加滤镜、镜头、粒子或震动。现在去补，成品味会提升得特别快。`,
        meta: `${flatScene.name} 这种正文已成型但演出还偏素的场景最适合先下手`,
        actions: [
          {
            label: "去台本页找灵感",
            action: "switch-screen",
            screen: "script",
          },
          {
            label: "打开这个场景",
            action: "open-scene-from-map",
            sceneId: flatScene.id,
          },
        ],
      });
    }

    return tasks.sort((left, right) => right.priority - left.priority);
  }

  function buildDashboardSceneStatusColumns(routeOverview = {}, helpers = {}) {
    const columns = [
      {
        status: "outline",
        title: "待开写",
        hint: "先把这一列补成可试玩骨架。",
        emptyText: "目前没有待开写的场景。",
      },
      {
        status: "drafting",
        title: "写作中",
        hint: "正文正在长出来，最适合继续往前推。",
        emptyText: "目前没有正在写的场景。",
      },
      {
        status: "polishing",
        title: "润色中",
        hint: "主体已站住，适合补演出、语音和气氛。",
        emptyText: "目前没有正在润色的场景。",
      },
      {
        status: "ready",
        title: "可试玩",
        hint: "已经值得拿去跑手感或给朋友试了。",
        emptyText: "目前还没有标成可试玩的场景。",
      },
    ];

    return columns.map((column) => {
      const scenes = toArray(routeOverview.nodes)
        .filter((scene) => getSafeSceneStatus(scene.status, helpers) === column.status)
        .map((scene) => {
          const playableChecklist = buildDashboardScenePlayableChecklist(scene);
          return {
            ...scene,
            tone: getScenePlanningTone(scene, helpers),
            summary: buildDashboardScenePlanningSummary(scene, helpers),
            playableChecklist,
            playableActionPlan: buildDashboardScenePlayableActionPlan(scene, playableChecklist),
            nextStep: buildDashboardScenePlanningNextStep(scene),
          };
        })
        .sort((left, right) => {
          const priorityDiff =
            getScenePlanningPriorityRank(right.priority, helpers) - getScenePlanningPriorityRank(left.priority, helpers);
          if (priorityDiff !== 0) {
            return priorityDiff;
          }
          return (right.completionScore ?? 0) - (left.completionScore ?? 0);
        });

      return {
        ...column,
        scenes,
      };
    });
  }

  function getDashboardTaskToneClass(tone) {
    if (tone === "danger") {
      return "danger-text";
    }
    if (tone === "warn") {
      return "warn-text";
    }
    if (tone === "good") {
      return "good-text";
    }
    return "";
  }

  global.CanvasiaEditorDashboardProduction = Object.freeze({
    buildDashboardProductionSummary,
    buildDashboardProductionTasks,
    buildDashboardScenePlanningNextStep,
    buildDashboardScenePlanningQueue,
    buildDashboardScenePlanningSummary,
    buildDashboardSceneStatusColumns,
    buildDashboardScenePlayableActionPlan,
    buildDashboardScenePlayableChecklist,
    getSceneChecklistFocusHint,
    getDashboardProgressPercent,
    getDashboardTaskToneClass,
    getScenePlanningPriorityRank,
    getScenePlanningStatusRank,
    getScenePlanningTone,
  });
})(typeof window !== "undefined" ? window : globalThis);
