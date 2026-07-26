(function attachPreviewStoryDebuggerTools(global) {
  "use strict";

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function getCollectionItem(collection, key) {
    if (!collection || !key) {
      return null;
    }
    if (typeof collection.get === "function") {
      return collection.get(key) ?? null;
    }
    return collection[key] ?? null;
  }

  function getActivePreviewTimeline(session) {
    const timeline = toArray(session?.timeline);
    if (timeline.length === 0) {
      return [];
    }
    const requestedPosition = Number.parseInt(session?.position, 10);
    const safePosition = Number.isFinite(requestedPosition)
      ? Math.min(Math.max(requestedPosition, 0), timeline.length - 1)
      : timeline.length - 1;
    return timeline.slice(0, safePosition + 1);
  }

  function getCurrentSnapshot(session) {
    const activeTimeline = getActivePreviewTimeline(session);
    return activeTimeline[activeTimeline.length - 1] ?? null;
  }

  function buildPreviewRouteSummary(session, options = {}) {
    const timeline = getActivePreviewTimeline(session);
    const getRouteDecisionSummary =
      typeof options.getRouteDecisionSummary === "function" ? options.getRouteDecisionSummary : () => null;
    const sceneIds = new Set();
    const items = [];
    let choiceCount = 0;
    let conditionCount = 0;
    let pendingChoiceCount = 0;

    timeline.forEach((snapshot, index) => {
      if (snapshot?.sceneId) {
        sceneIds.add(snapshot.sceneId);
      }

      const decision = getRouteDecisionSummary(snapshot);
      if (!decision) {
        return;
      }

      if (snapshot.blockType === "choice") {
        if (decision.pending) {
          pendingChoiceCount += 1;
        } else {
          choiceCount += 1;
        }
      } else if (snapshot.blockType === "condition") {
        conditionCount += 1;
      }

      items.push({
        index,
        sceneId: snapshot.sceneId,
        blockId: snapshot.blockId,
        blockType: snapshot.blockType,
        sceneName: snapshot.sceneName,
        title: decision.title,
        meta: decision.meta,
        pending: Boolean(decision.pending),
        isCurrent: index === timeline.length - 1,
      });
    });

    return {
      visitedSceneCount: sceneIds.size,
      choiceCount,
      conditionCount,
      pendingChoiceCount,
      items,
    };
  }

  function buildPreviewBranchCoverage(session, projectData = {}, options = {}) {
    const timeline = getActivePreviewTimeline(session);
    const visitedPointKeys = new Set();
    const coveredOutcomeKeys = new Set();
    const getConditionBranchKey =
      typeof options.getConditionBranchKey === "function"
        ? options.getConditionBranchKey
        : (branch, index) => cleanText(branch?.id, `branch-${index + 1}`);
    const formatConditionRule =
      typeof options.formatConditionRule === "function"
        ? options.formatConditionRule
        : (rule) => `${cleanText(rule?.variableId, "变量")} ${cleanText(rule?.operator, "==")} ${cleanText(rule?.value)}`;
    const getChoiceTargetLabel =
      typeof options.getChoiceTargetLabel === "function"
        ? options.getChoiceTargetLabel
        : (sceneId) => cleanText(getCollectionItem(projectData.scenesById, sceneId)?.name, sceneId);

    timeline.forEach((snapshot) => {
      if (!snapshot || snapshot.completed || !snapshot.blockId) {
        return;
      }

      if (snapshot.blockType === "choice") {
        const pointKey = `choice:${snapshot.sceneId}:${snapshot.blockId}`;
        visitedPointKeys.add(pointKey);
        const selectedOptionId = cleanText(snapshot.selectedOptionId);
        if (selectedOptionId) {
          coveredOutcomeKeys.add(`${pointKey}:${selectedOptionId}`);
        }
        return;
      }

      if (snapshot.blockType === "condition") {
        const pointKey = `condition:${snapshot.sceneId}:${snapshot.blockId}`;
        visitedPointKeys.add(pointKey);
        const resolvedBranchId = cleanText(snapshot.resolvedBranchId);
        if (resolvedBranchId) {
          coveredOutcomeKeys.add(`${pointKey}:${resolvedBranchId}`);
        }
      }
    });

    const points = [];
    toArray(projectData.chapters).forEach((chapter) => {
      toArray(chapter?.scenes).forEach((scene) => {
        toArray(scene?.blocks).forEach((block, blockIndex) => {
          if (block?.type === "choice") {
            const pointKey = `choice:${scene.id}:${block.id}`;
            const outcomes = toArray(block.options).map((option, index) => {
              const optionKey = cleanText(option?.id, `option-${index + 1}`);
              const outcomeKey = `${pointKey}:${optionKey}`;
              const effectsCount = toArray(option?.effects).length;
              const targetSceneName = getChoiceTargetLabel(option?.gotoSceneId) || "未设置目标";
              return {
                key: outcomeKey,
                label: cleanText(option?.text, `选项 ${index + 1}`),
                meta: `${targetSceneName}${effectsCount > 0 ? ` · ${effectsCount} 条效果` : ""}`,
                covered: coveredOutcomeKeys.has(outcomeKey),
              };
            });

            points.push({
              key: pointKey,
              sceneId: scene.id,
              blockId: block.id,
              blockType: block.type,
              title: `${cleanText(scene.name, scene.id)} / 选项分支`,
              meta: `${cleanText(scene.chapterName, chapter?.name)} · 第 ${blockIndex + 1} 张卡片`,
              visited: visitedPointKeys.has(pointKey),
              outcomes,
            });
            return;
          }

          if (block?.type !== "condition") {
            return;
          }

          const pointKey = `condition:${scene.id}:${block.id}`;
          const branchOutcomes = toArray(block.branches).map((branch, index) => {
            const branchKey = getConditionBranchKey(branch, index);
            const outcomeKey = `${pointKey}:${branchKey}`;
            const targetSceneName =
              cleanText(getCollectionItem(projectData.scenesById, branch?.gotoSceneId)?.name, branch?.gotoSceneId) ||
              "未设置目标";
            const rules = toArray(branch?.when).map((rule) => formatConditionRule(rule)).filter(Boolean);
            return {
              key: outcomeKey,
              label: rules.join(" 且 ") || `条件分支 ${index + 1}`,
              meta: `命中后去：${targetSceneName}`,
              covered: coveredOutcomeKeys.has(outcomeKey),
            };
          });
          const elseOutcomeKey = `${pointKey}:else`;
          const elseTargetSceneName =
            cleanText(
              getCollectionItem(projectData.scenesById, block.elseGotoSceneId)?.name,
              block.elseGotoSceneId
            ) || "未设置目标";

          points.push({
            key: pointKey,
            sceneId: scene.id,
            blockId: block.id,
            blockType: block.type,
            title: `${cleanText(scene.name, scene.id)} / 条件判断`,
            meta: `${cleanText(scene.chapterName, chapter?.name)} · 第 ${blockIndex + 1} 张卡片`,
            visited: visitedPointKeys.has(pointKey),
            outcomes: [
              ...branchOutcomes,
              {
                key: elseOutcomeKey,
                label: "否则",
                meta: `都不满足时去：${elseTargetSceneName}`,
                covered: coveredOutcomeKeys.has(elseOutcomeKey),
              },
            ],
          });
        });
      });
    });

    const currentSnapshot = getCurrentSnapshot(session);
    const pointsWithCoverage = points.map((point) => {
      const coveredCount = point.outcomes.filter((outcome) => outcome.covered).length;
      return {
        ...point,
        coveredCount,
        remainingCount: Math.max(point.outcomes.length - coveredCount, 0),
        isCurrent:
          currentSnapshot?.sceneId === point.sceneId &&
          currentSnapshot?.blockId === point.blockId &&
          ["choice", "condition"].includes(currentSnapshot?.blockType),
      };
    });
    const unvisitedPoints = pointsWithCoverage.filter((point) => !point.visited);
    const partialPoints = pointsWithCoverage.filter((point) => point.visited && point.remainingCount > 0);
    const fullyCoveredPoints = pointsWithCoverage.filter((point) => point.remainingCount === 0);
    const totalOutcomeCount = pointsWithCoverage.reduce((total, point) => total + point.outcomes.length, 0);
    const coveredOutcomeCount = pointsWithCoverage.reduce((total, point) => total + point.coveredCount, 0);

    return {
      totalPoints: pointsWithCoverage.length,
      visitedPointCount: pointsWithCoverage.length - unvisitedPoints.length,
      fullyCoveredPointCount: fullyCoveredPoints.length,
      totalOutcomeCount,
      coveredOutcomeCount,
      remainingOutcomeCount: Math.max(totalOutcomeCount - coveredOutcomeCount, 0),
      unvisitedPoints,
      partialPoints,
      points: pointsWithCoverage,
      currentPendingChoice:
        currentSnapshot?.blockType === "choice" && toArray(currentSnapshot.choiceOptions).length > 0
          ? currentSnapshot
          : null,
    };
  }

  function stableSerialize(value) {
    if (Array.isArray(value)) {
      return `[${value.map(stableSerialize).join(",")}]`;
    }
    if (value && typeof value === "object") {
      return `{${Object.keys(value)
        .sort()
        .map((key) => `${JSON.stringify(key)}:${stableSerialize(value[key])}`)
        .join(",")}}`;
    }
    return JSON.stringify(value);
  }

  function valuesEqual(left, right) {
    return stableSerialize(left) === stableSerialize(right);
  }

  function getVariableDefinitions(options = {}) {
    return toArray(options.variableDefinitions).filter((variable) => cleanText(variable?.id));
  }

  function getVariableLabel(variableId, options = {}) {
    const definition = getVariableDefinitions(options).find((variable) => variable.id === variableId);
    return cleanText(definition?.name, variableId);
  }

  function getVariableDefault(variableId, options = {}) {
    const definition = getVariableDefinitions(options).find((variable) => variable.id === variableId);
    if (typeof options.getVariableDefaultValue === "function") {
      return options.getVariableDefaultValue(variableId);
    }
    return definition?.defaultValue;
  }

  function formatVariableValue(variableId, value, options = {}) {
    if (typeof options.formatVariableValue === "function") {
      return cleanText(options.formatVariableValue(variableId, value), String(value ?? ""));
    }
    if (typeof value === "boolean") {
      return value ? "是" : "否";
    }
    if (value && typeof value === "object") {
      return JSON.stringify(value);
    }
    return String(value ?? "");
  }

  function buildVariableChanges(previousVariables = {}, currentVariables = {}, options = {}) {
    const variableIds = new Set([
      ...getVariableDefinitions(options).map((variable) => variable.id),
      ...Object.keys(previousVariables ?? {}),
      ...Object.keys(currentVariables ?? {}),
    ]);
    return Array.from(variableIds)
      .sort()
      .flatMap((variableId) => {
        const beforeValue = Object.hasOwn(previousVariables ?? {}, variableId)
          ? previousVariables[variableId]
          : getVariableDefault(variableId, options);
        const afterValue = Object.hasOwn(currentVariables ?? {}, variableId)
          ? currentVariables[variableId]
          : getVariableDefault(variableId, options);
        if (valuesEqual(beforeValue, afterValue)) {
          return [];
        }
        return [
          {
            variableId,
            name: getVariableLabel(variableId, options),
            beforeValue,
            afterValue,
            beforeLabel: formatVariableValue(variableId, beforeValue, options),
            afterLabel: formatVariableValue(variableId, afterValue, options),
          },
        ];
      });
  }

  function getCharacterLabel(characterId, options = {}) {
    if (typeof options.getCharacterName === "function") {
      return cleanText(options.getCharacterName(characterId), characterId);
    }
    return cleanText(characterId, "未命名角色");
  }

  function getAssetLabel(assetId, options = {}) {
    if (typeof options.getAssetName === "function") {
      return cleanText(options.getAssetName(assetId), assetId);
    }
    return cleanText(assetId, "未命名素材");
  }

  function getPositionLabel(position) {
    return { left: "左侧", center: "中央", right: "右侧" }[cleanText(position)] ?? cleanText(position, "舞台");
  }

  function buildCharacterCues(previousVisual = {}, currentVisual = {}, options = {}) {
    const previousMap = new Map(toArray(previousVisual.visibleCharacters).map((item) => [item.characterId, item]));
    const currentMap = new Map(toArray(currentVisual.visibleCharacters).map((item) => [item.characterId, item]));
    const cues = [];

    currentMap.forEach((currentState, characterId) => {
      const previousState = previousMap.get(characterId);
      const name = getCharacterLabel(characterId, options);
      if (!previousState) {
        cues.push({ kind: "character", label: "角色登场", detail: `${name} · ${getPositionLabel(currentState.position)}` });
        return;
      }
      if (!valuesEqual(previousState, currentState)) {
        const expression = cleanText(currentState.expressionName, currentState.expressionId);
        cues.push({
          kind: "character",
          label: "角色变化",
          detail: `${name} · ${getPositionLabel(currentState.position)}${expression ? ` · ${expression}` : ""}`,
        });
      }
    });
    previousMap.forEach((previousState, characterId) => {
      if (!currentMap.has(characterId)) {
        cues.push({ kind: "character", label: "角色退场", detail: getCharacterLabel(characterId, options) });
      }
    });
    return cues;
  }

  function buildStageImageCues(previousVisual = {}, currentVisual = {}, options = {}) {
    const previousMap = new Map(toArray(previousVisual.visibleStageImages).map((item) => [item.layerId, item]));
    const currentMap = new Map(toArray(currentVisual.visibleStageImages).map((item) => [item.layerId, item]));
    const cues = [];
    currentMap.forEach((currentState, layerId) => {
      const previousState = previousMap.get(layerId);
      const assetName = getAssetLabel(currentState.assetId, options);
      if (!previousState) {
        cues.push({ kind: "stage-image", label: "舞台贴图出现", detail: `${assetName} · ${cleanText(layerId, "图层")}` });
      } else if (!valuesEqual(previousState, currentState)) {
        cues.push({ kind: "stage-image", label: "舞台贴图变化", detail: `${assetName} · ${cleanText(layerId, "图层")}` });
      }
    });
    previousMap.forEach((previousState, layerId) => {
      if (!currentMap.has(layerId)) {
        cues.push({
          kind: "stage-image",
          label: "舞台贴图隐藏",
          detail: `${getAssetLabel(previousState.assetId, options)} · ${cleanText(layerId, "图层")}`,
        });
      }
    });
    return cues;
  }

  function buildVisualCues(previousVisual = {}, currentVisual = {}, snapshot = {}, options = {}) {
    const cues = [];
    const previousBackground = cleanText(previousVisual.backgroundAssetId);
    const currentBackground = cleanText(currentVisual.backgroundAssetId);
    if (previousBackground !== currentBackground) {
      cues.push({
        kind: "background",
        label: currentBackground ? "背景切换" : "背景清空",
        detail: currentBackground
          ? cleanText(currentVisual.backgroundName, getAssetLabel(currentBackground, options))
          : cleanText(previousVisual.backgroundName, getAssetLabel(previousBackground, options)),
      });
    }

    const previousMusic = cleanText(previousVisual.musicAssetId);
    const currentMusic = cleanText(currentVisual.musicAssetId);
    if (previousMusic !== currentMusic) {
      cues.push({
        kind: "music",
        label: currentMusic ? "BGM 开始" : "BGM 停止",
        detail: currentMusic
          ? `${cleanText(currentVisual.musicName, getAssetLabel(currentMusic, options))} · ${Number(currentVisual.musicVolume ?? 100)}%`
          : cleanText(previousVisual.musicName, getAssetLabel(previousMusic, options)),
      });
    } else if (currentMusic && Number(previousVisual.musicVolume ?? 100) !== Number(currentVisual.musicVolume ?? 100)) {
      cues.push({
        kind: "music",
        label: "BGM 音量",
        detail: `${cleanText(currentVisual.musicName, getAssetLabel(currentMusic, options))} · ${Number(currentVisual.musicVolume ?? 100)}%`,
      });
    }

    cues.push(...buildCharacterCues(previousVisual, currentVisual, options));
    cues.push(...buildStageImageCues(previousVisual, currentVisual, options));

    const effectFields = [
      ["particleEffect", "粒子演出"],
      ["screenShake", "屏幕震动"],
      ["screenFlash", "屏幕闪光"],
      ["screenFade", "画面淡入淡出"],
      ["cameraZoom", "镜头缩放"],
      ["cameraPan", "镜头移动"],
      ["screenFilter", "画面滤镜"],
      ["depthBlur", "景深模糊"],
    ];
    effectFields.forEach(([field, label]) => {
      if (currentVisual[field] && !valuesEqual(previousVisual[field], currentVisual[field])) {
        cues.push({ kind: "effect", label, detail: "这一卡触发" });
      }
    });

    if (snapshot?.blockType === "sfx_play" && snapshot.block?.assetId) {
      cues.push({ kind: "audio", label: "音效播放", detail: getAssetLabel(snapshot.block.assetId, options) });
    }
    const voiceAssetId = cleanText(snapshot?.block?.voiceAssetId);
    if (voiceAssetId) {
      cues.push({ kind: "audio", label: "语音播放", detail: getAssetLabel(voiceAssetId, options) });
    }
    return cues;
  }

  function getSnapshotSummary(snapshot, options = {}) {
    if (snapshot?.completed) {
      return {
        title: cleanText(snapshot?.visualState?.dialogueText, "试玩结束"),
        meta: "路线结束",
      };
    }
    if (typeof options.getBlockSummary === "function") {
      const summary = options.getBlockSummary(snapshot) ?? {};
      return {
        title: cleanText(summary.title, snapshot?.visualState?.dialogueText),
        meta: cleanText(summary.meta),
      };
    }
    return {
      title: cleanText(snapshot?.visualState?.dialogueText, snapshot?.blockType),
      meta: cleanText(snapshot?.visualState?.speakerName),
    };
  }

  function buildPreviewFlightRecorder(session, options = {}) {
    const timeline = getActivePreviewTimeline(session);
    const defaultVariables = Object.fromEntries(
      getVariableDefinitions(options).map((variable) => [variable.id, getVariableDefault(variable.id, options)])
    );
    const entries = timeline.map((snapshot, index) => {
      const previousSnapshot = timeline[index - 1] ?? null;
      const previousVariables = previousSnapshot?.variables ?? defaultVariables;
      const previousVisualState = previousSnapshot?.visualState ?? {};
      const summary = getSnapshotSummary(snapshot, options);
      const variableChanges = buildVariableChanges(previousVariables, snapshot?.variables ?? {}, options);
      const stageCues = buildVisualCues(previousVisualState, snapshot?.visualState ?? {}, snapshot, options);
      const routeDecision =
        typeof options.getRouteDecisionSummary === "function"
          ? options.getRouteDecisionSummary(snapshot)
          : null;
      const blockLabel = snapshot?.completed
        ? "试玩结束"
        : cleanText(options.blockLabels?.[snapshot?.blockType], snapshot?.blockType || "未知卡片");
      const significant = Boolean(variableChanges.length || stageCues.length || routeDecision || snapshot?.completed);
      return {
        index,
        isCurrent: index === timeline.length - 1,
        sceneId: snapshot?.sceneId ?? "",
        sceneName: cleanText(snapshot?.sceneName, snapshot?.sceneId || "未知场景"),
        blockId: snapshot?.blockId ?? "",
        blockIndex: Number.isInteger(snapshot?.blockIndex) ? snapshot.blockIndex : -1,
        blockType: snapshot?.blockType ?? "",
        blockLabel,
        title: summary.title,
        meta: summary.meta,
        completed: Boolean(snapshot?.completed),
        variableChanges,
        stageCues,
        routeDecision: routeDecision
          ? {
              title: cleanText(routeDecision.title, "路线结果"),
              meta: cleanText(routeDecision.meta),
              pending: Boolean(routeDecision.pending),
            }
          : null,
        significant,
      };
    });
    const sceneIds = new Set(entries.map((entry) => entry.sceneId).filter(Boolean));
    const variableChangeCount = entries.reduce((total, entry) => total + entry.variableChanges.length, 0);
    const stageCueCount = entries.reduce((total, entry) => total + entry.stageCues.length, 0);
    const routeDecisionCount = entries.filter((entry) => entry.routeDecision && !entry.routeDecision.pending).length;
    const currentEntry = entries[entries.length - 1] ?? null;
    const significantEntries = entries.filter((entry) => entry.significant);

    return {
      schemaVersion: 1,
      projectTitle: cleanText(options.projectTitle, "未命名项目"),
      generatedAt: cleanText(options.generatedAt, new Date().toISOString()),
      startSceneId: cleanText(session?.startSceneId),
      currentPosition: entries.length > 0 ? entries.length - 1 : -1,
      summary: {
        stepCount: entries.length,
        visitedSceneCount: sceneIds.size,
        variableChangeCount,
        routeDecisionCount,
        stageCueCount,
        significantStepCount: significantEntries.length,
        completed: Boolean(currentEntry?.completed),
        currentSceneName: currentEntry?.sceneName ?? "未开始",
        currentBlockLabel: currentEntry?.blockLabel ?? "未开始",
      },
      entries,
      significantEntries,
    };
  }

  function escapeMarkdown(value) {
    return String(value ?? "").replace(/\\/g, "\\\\").replace(/\|/g, "\\|").replace(/\r?\n/g, "<br />");
  }

  function buildPreviewFlightRecorderMarkdown(report = {}) {
    const summary = report.summary ?? {};
    const lines = [
      `# ${cleanText(report.projectTitle, "未命名项目")} 试玩飞行记录`,
      "",
      `- 生成时间：${cleanText(report.generatedAt, "未知")}`,
      `- 当前进度：${Number(summary.stepCount ?? 0)} 步 / ${Number(summary.visitedSceneCount ?? 0)} 个场景`,
      `- 变量变化：${Number(summary.variableChangeCount ?? 0)} 项`,
      `- 路线结果：${Number(summary.routeDecisionCount ?? 0)} 项`,
      `- 音画调度：${Number(summary.stageCueCount ?? 0)} 项`,
      `- 当前落点：${cleanText(summary.currentSceneName, "未开始")} / ${cleanText(summary.currentBlockLabel, "未开始")}`,
      "",
      "## 有效轨迹",
      "",
    ];

    if (toArray(report.entries).length === 0) {
      lines.push("尚未开始试玩。", "");
      return lines.join("\n");
    }

    lines.push("| 步骤 | 场景 / 卡片 | 内容 | 变量变化 | 路线结果 | 音画调度 |", "| --- | --- | --- | --- | --- | --- |");
    toArray(report.entries).forEach((entry) => {
      const variableText = toArray(entry.variableChanges)
        .map((change) => `${change.name}: ${change.beforeLabel} -> ${change.afterLabel}`)
        .join("；");
      const routeText = entry.routeDecision
        ? `${entry.routeDecision.title}${entry.routeDecision.meta ? ` · ${entry.routeDecision.meta}` : ""}`
        : "";
      const cueText = toArray(entry.stageCues).map((cue) => `${cue.label}: ${cue.detail}`).join("；");
      lines.push(
        `| ${entry.index + 1} | ${escapeMarkdown(`${entry.sceneName} / ${entry.blockLabel}`)} | ${escapeMarkdown(entry.title)} | ${escapeMarkdown(variableText || "-")} | ${escapeMarkdown(routeText || "-")} | ${escapeMarkdown(cueText || "-")} |`
      );
    });
    lines.push("", "> 本记录只包含当前时间线位置之前的有效轨迹；回退后被放弃的未来路线不会混入统计。", "");
    return lines.join("\n");
  }

  global.CanvasiaEditorPreviewStoryDebugger = Object.freeze({
    getActivePreviewTimeline,
    buildPreviewRouteSummary,
    buildPreviewBranchCoverage,
    buildPreviewFlightRecorder,
    buildPreviewFlightRecorderMarkdown,
  });
})(typeof window !== "undefined" ? window : globalThis);
