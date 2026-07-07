(function attachProjectPolishTools(global) {
  "use strict";

  const scriptReadabilityTools = global.CanvasiaEditorScriptReadability || {};
  const scenePolishTools = global.CanvasiaEditorScenePolish || {};
  const scenePacingAdvisorTools = global.CanvasiaEditorScenePacingAdvisor || {};
  const audioCueSheetTools = global.CanvasiaEditorAudioCueSheet || {};
  const projectSettingsTools = global.CanvasiaEditorProjectSettings || {};
  const dialogBoxReadabilityTools = global.CanvasiaEditorDialogBoxReadability || {};

  const PROJECT_POLISH_SAVE_SLOT_TARGETS = Object.freeze({
    medium: 24,
    large: 50,
  });

  const GAME_UI_IDENTITY_FIELDS = Object.freeze([
    "titleLogoAssetId",
    "titleBackgroundAssetId",
    "panelFrameAssetId",
    "buttonFrameAssetId",
    "saveSlotFrameAssetId",
    "systemPanelFrameAssetId",
    "uiOverlayAssetId",
    "fontAssetId",
  ]);

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").trim();
    return text || fallback;
  }

  function cloneValue(value) {
    return JSON.parse(JSON.stringify(value ?? null));
  }

  function toCount(value) {
    const count = Number(value);
    return Number.isFinite(count) ? Math.max(0, Math.round(count)) : 0;
  }

  function getSceneId(scene = {}, fallback = "") {
    return cleanText(scene.id, fallback);
  }

  function getSceneName(scene = {}, fallback = "") {
    return cleanText(scene.name ?? scene.title, fallback || getSceneId(scene));
  }

  function getSceneList(data = {}) {
    if (typeof scriptReadabilityTools.getProjectReadableSceneList === "function") {
      return scriptReadabilityTools.getProjectReadableSceneList(data);
    }
    if (typeof scenePolishTools.getProjectSceneList === "function") {
      return scenePolishTools.getProjectSceneList(data);
    }
    return toArray(data.scenes);
  }

  function getChapterSceneMap(chapters = []) {
    const chapterSceneMap = new Map();
    toArray(chapters).forEach((chapter) => {
      toArray(chapter.scenes).forEach((scene) => {
        const sceneId = getSceneId(scene);
        if (sceneId) {
          chapterSceneMap.set(sceneId, scene);
        }
      });
    });
    return chapterSceneMap;
  }

  function buildSceneStore(data = {}) {
    const sceneStore = new Map();
    const sceneOrder = [];
    const pushScene = (scene, fallback = {}) => {
      const sceneId = getSceneId(scene, getSceneId(fallback));
      if (!sceneId || sceneStore.has(sceneId)) {
        return;
      }

      const nextScene = {
        ...(cloneValue(fallback) ?? {}),
        ...(cloneValue(scene) ?? {}),
        id: sceneId,
      };
      sceneStore.set(sceneId, nextScene);
      sceneOrder.push(sceneId);
    };

    const chapterSceneMap = getChapterSceneMap(data.chapters);
    getSceneList(data).forEach((scene) => pushScene(scene, chapterSceneMap.get(getSceneId(scene))));
    toArray(data.scenes).forEach((scene) => pushScene(scene, chapterSceneMap.get(getSceneId(scene))));
    if (data.scenesById && typeof data.scenesById.forEach === "function") {
      data.scenesById.forEach((scene, id) => pushScene(scene, { id }));
    } else if (data.scenesById && typeof data.scenesById === "object") {
      Object.entries(data.scenesById).forEach(([id, scene]) => pushScene(scene, { id }));
    }

    return { sceneStore, sceneOrder };
  }

  function getScenesFromStore(sceneStore, sceneOrder) {
    const pushed = new Set();
    const scenes = [];
    toArray(sceneOrder).forEach((sceneId) => {
      const scene = sceneStore.get(sceneId);
      if (scene) {
        pushed.add(sceneId);
        scenes.push(cloneValue(scene));
      }
    });
    sceneStore.forEach((scene, sceneId) => {
      if (!pushed.has(sceneId)) {
        scenes.push(cloneValue(scene));
      }
    });
    return scenes;
  }

  function getProjectSceneCount(data = {}) {
    return getSceneList(data).length;
  }

  function getAssetList(data = {}) {
    return toArray(data.assetList ?? data.assets);
  }

  function getFirstAssetIdByTypes(data = {}, types = []) {
    const acceptedTypes = new Set(toArray(types).map((type) => cleanText(type)));
    const asset = getAssetList(data).find((item) => {
      const assetId = cleanText(item?.id);
      const assetType = cleanText(item?.type);
      return assetId && acceptedTypes.has(assetType) && item?.fileExists !== false;
    });
    return cleanText(asset?.id);
  }

  function buildDataWithScenes(data, sceneStore, sceneOrder) {
    const scenes = getScenesFromStore(sceneStore, sceneOrder);
    const scenesById = new Map(scenes.map((scene) => [getSceneId(scene), scene]));
    const chapters = toArray(data.chapters).map((chapter) => {
      const nextChapter = {
        ...(cloneValue(chapter) ?? {}),
      };
      if (Array.isArray(chapter.scenes)) {
        nextChapter.scenes = chapter.scenes.map((scene) => {
          const sceneId = getSceneId(scene);
          return cloneValue(scenesById.get(sceneId) ?? scene);
        });
      }
      return nextChapter;
    });

    return {
      ...data,
      chapters,
      scenes,
      scenesById,
    };
  }

  function ensureSceneEdit(sceneEdits, sceneId, scenePlan = {}, scene = {}) {
    if (!sceneEdits.has(sceneId)) {
      sceneEdits.set(sceneId, {
        sceneId,
        sceneName: cleanText(scenePlan.sceneName, getSceneName(scene, sceneId)),
        chapterId: cleanText(scenePlan.chapterId, cleanText(scene.chapterId)),
        chapterName: cleanText(scenePlan.chapterName, cleanText(scene.chapterName)),
        firstChangedBlockId: "",
        firstChangedIndex: -1,
        readableSplitCount: 0,
        readableAddedBlockCount: 0,
        presentationChangedBlockCount: 0,
        presentationChangedFieldCount: 0,
        audioChangedBlockCount: 0,
        audioOperationCount: 0,
      });
    }
    return sceneEdits.get(sceneId);
  }

  function setFirstChange(edit, blockId, index) {
    if (edit.firstChangedBlockId) {
      return;
    }
    edit.firstChangedBlockId = cleanText(blockId);
    edit.firstChangedIndex = Number.isFinite(Number(index)) ? Number(index) : -1;
  }

  function mergeScenePlan(sceneStore, scenePlan = {}) {
    const sourceScene = scenePlan.scene ?? {};
    const sceneId = cleanText(scenePlan.sceneId, getSceneId(sourceScene));
    if (!sceneId) {
      return null;
    }

    const previousScene = sceneStore.get(sceneId) ?? {};
    const nextScene = {
      ...(cloneValue(previousScene) ?? {}),
      ...(cloneValue(sourceScene) ?? {}),
      id: sceneId,
    };
    if (!cleanText(nextScene.chapterId)) {
      nextScene.chapterId = cleanText(scenePlan.chapterId, cleanText(previousScene.chapterId));
    }
    if (!cleanText(nextScene.chapterName)) {
      nextScene.chapterName = cleanText(scenePlan.chapterName, cleanText(previousScene.chapterName));
    }
    sceneStore.set(sceneId, nextScene);
    return { sceneId, scene: nextScene };
  }

  function applyReadablePlan(sceneStore, sceneEdits, plan = {}) {
    toArray(plan.scenePlans).forEach((scenePlan) => {
      const merged = mergeScenePlan(sceneStore, scenePlan);
      if (!merged) {
        return;
      }
      const edit = ensureSceneEdit(sceneEdits, merged.sceneId, scenePlan, merged.scene);
      edit.readableSplitCount += Math.max(0, Number(scenePlan.splitCount) || 0);
      edit.readableAddedBlockCount += Math.max(0, Number(scenePlan.addedBlockCount) || 0);
      setFirstChange(edit, scenePlan.firstSplitBlockId, scenePlan.firstSplitIndex);
    });
  }

  function applyPresentationPlan(sceneStore, sceneEdits, plan = {}) {
    toArray(plan.scenePlans).forEach((scenePlan) => {
      const merged = mergeScenePlan(sceneStore, scenePlan);
      if (!merged) {
        return;
      }
      const edit = ensureSceneEdit(sceneEdits, merged.sceneId, scenePlan, merged.scene);
      edit.presentationChangedBlockCount += Math.max(0, Number(scenePlan.changedBlockCount) || 0);
      edit.presentationChangedFieldCount += Math.max(0, Number(scenePlan.changedFieldCount) || 0);
      setFirstChange(edit, scenePlan.firstChangedBlockId, scenePlan.firstChangedIndex);
    });
  }

  function applyAudioPlan(sceneStore, sceneEdits, plan = {}) {
    toArray(plan.scenePlans).forEach((scenePlan) => {
      const merged = mergeScenePlan(sceneStore, scenePlan);
      if (!merged) {
        return;
      }
      const edit = ensureSceneEdit(sceneEdits, merged.sceneId, scenePlan, merged.scene);
      edit.audioChangedBlockCount += Math.max(0, Number(scenePlan.changedBlockCount) || 0);
      edit.audioOperationCount += Math.max(0, Number(scenePlan.operationCount) || 0);
      setFirstChange(edit, scenePlan.firstChangedBlockId, scenePlan.firstChangedIndex);
    });
  }

  function buildProjectOneClickPolishSummary(plan = {}) {
    if (!plan.changed) {
      return "项目基础内容已经比较适合发布前检查";
    }

    const parts = [];
    if (plan.readableSplitCount > 0) {
      parts.push(`拆分 ${plan.readableSplitCount} 张长文本，新增 ${plan.readableAddedBlockCount} 张卡片`);
    }
    if (plan.presentationChangedFieldCount > 0) {
      parts.push(`补齐 ${plan.presentationChangedFieldCount} 个演出参数`);
    }
    if (plan.audioOperationCount > 0) {
      parts.push(`修复 ${plan.audioOperationCount} 个音频参数`);
    }
    if (plan.projectOperationCount > 0) {
      parts.push(`补齐 ${plan.projectOperationCount} 个项目体验设置`);
    }
    return `发布前整理完成：${parts.join("；")}`;
  }

  function buildProjectPacingSnapshot(data = {}, options = {}) {
    if (
      typeof scenePacingAdvisorTools.analyzeScenePacing !== "function" ||
      typeof scenePacingAdvisorTools.aggregateScenePacingAnalyses !== "function"
    ) {
      return null;
    }

    const analyses = getSceneList(data).map((scene, index) => {
      const analysis = scenePacingAdvisorTools.analyzeScenePacing(scene, options);
      return {
        ...analysis,
        sceneId: getSceneId(scene, `scene_${index + 1}`),
        sceneName: getSceneName(scene, `场景 ${index + 1}`),
        chapterName: cleanText(scene.chapterName),
      };
    });
    const aggregate = scenePacingAdvisorTools.aggregateScenePacingAnalyses(analyses);
    const sceneHighlights = analyses
      .filter((analysis) => ["rough", "needs_polish"].includes(analysis.grade?.id))
      .sort((left, right) => (left.score ?? 0) - (right.score ?? 0))
      .slice(0, Math.max(1, Number(options.sceneLimit) || 4))
      .map((analysis) => ({
        sceneId: analysis.sceneId,
        sceneName: compactText(analysis.sceneName, analysis.sceneId, 120),
        chapterName: compactText(analysis.chapterName, "", 120),
        score: Math.max(0, Number(analysis.score) || 0),
        gradeLabel: cleanText(analysis.grade?.label, "待打磨"),
        headline: compactText(analysis.headline, "这一场建议试玩复看。", 160),
        issueSummary: toArray(analysis.issues)
          .slice(0, 3)
          .map((issue) => cleanText(issue.title))
          .filter(Boolean)
          .join(" / "),
        actionSummary: toArray(analysis.actions).slice(0, 3).join(" / ") || "试玩确认",
      }));

    return {
      sceneCount: aggregate.sceneCount,
      averageScore: aggregate.averageScore,
      roughSceneCount: aggregate.roughSceneCount,
      readySceneCount: aggregate.readySceneCount,
      topIssues: toArray(aggregate.topIssues)
        .slice(0, Math.max(1, Number(options.issueLimit) || 4))
        .map((issue) => ({
          code: cleanText(issue.code),
          title: compactText(issue.title, "节奏问题", 120),
          count: Math.max(0, Number(issue.count) || 0),
        })),
      sceneHighlights,
    };
  }

  function getProjectRuntimeSettings(project = {}) {
    if (typeof projectSettingsTools.getProjectRuntimeSettings === "function") {
      return projectSettingsTools.getProjectRuntimeSettings(project);
    }
    return {
      ...(project.runtimeSettings ?? {}),
      formalSaveSlotCount: toCount(project.runtimeSettings?.formalSaveSlotCount) || PROJECT_POLISH_SAVE_SLOT_TARGETS.medium,
    };
  }

  function getProjectGameUiConfig(project = {}) {
    if (typeof projectSettingsTools.getProjectGameUiConfig === "function") {
      return projectSettingsTools.getProjectGameUiConfig(project);
    }
    return {
      preset: "stellar",
      fontFamily: "",
      fontAssetId: "",
      ...(project.gameUiConfig ?? {}),
    };
  }

  function hasGameUiIdentity(config = {}) {
    const hasAssetIdentity = GAME_UI_IDENTITY_FIELDS.some((field) => cleanText(config[field]));
    const hasPaletteIdentity = cleanText(config.fontFamily) || cleanText(config.preset) === "custom";
    return Boolean(hasAssetIdentity || hasPaletteIdentity);
  }

  function getSaveSlotTarget(sceneCount, options = {}) {
    const explicitTarget = toCount(options.saveSlotTarget ?? options.formalSaveSlotCount);
    if (explicitTarget > 0) {
      return explicitTarget;
    }
    return sceneCount >= 20 ? PROJECT_POLISH_SAVE_SLOT_TARGETS.large : PROJECT_POLISH_SAVE_SLOT_TARGETS.medium;
  }

  function addProjectOperation(operations, area, field, fromValue, toValue, label, detail = "") {
    if (JSON.stringify(fromValue ?? null) === JSON.stringify(toValue ?? null)) {
      return false;
    }
    operations.push({
      area,
      field,
      fromValue,
      toValue,
      label: cleanText(label, "补齐项目设置"),
      detail: cleanText(detail, "发布前自动补齐一项安全默认设置。"),
    });
    return true;
  }

  function buildProjectSettingsPolishPlan(data = {}, options = {}) {
    const project = data.project ?? {};
    const sceneCount = getProjectSceneCount(data);
    const operations = [];
    const projectPatch = {};

    const runtimeSettings = getProjectRuntimeSettings(project);
    const nextRuntimeSettings = { ...runtimeSettings };
    if (sceneCount >= 6) {
      const target = getSaveSlotTarget(sceneCount, options);
      if (toCount(nextRuntimeSettings.formalSaveSlotCount) < target) {
        addProjectOperation(
          operations,
          "runtime",
          "formalSaveSlotCount",
          nextRuntimeSettings.formalSaveSlotCount,
          target,
          "提高正式存档位数量",
          sceneCount >= 20
            ? "长篇或多路线作品会自动给更多手动存档空间。"
            : "中篇 Demo 至少保留 24 个正式存档位，方便玩家回看分支。"
        );
        nextRuntimeSettings.formalSaveSlotCount = target;
      }
    }
    if (JSON.stringify(nextRuntimeSettings) !== JSON.stringify(runtimeSettings)) {
      projectPatch.runtimeSettings = nextRuntimeSettings;
    }

    if (typeof dialogBoxReadabilityTools.buildDialogBoxReadabilityAutoFixPlan === "function") {
      const dialogPlan = dialogBoxReadabilityTools.buildDialogBoxReadabilityAutoFixPlan(data);
      if (dialogPlan.changed) {
        toArray(dialogPlan.operations).forEach((operation) => {
          addProjectOperation(
            operations,
            "dialogBox",
            operation.field,
            operation.fromValue,
            operation.toValue,
            operation.label,
            "增强文本框可读性，避免浅色背景或长文本下看不清。"
          );
        });
        projectPatch.dialogBoxConfig = dialogPlan.dialogBoxConfig;
      }
    }

    const gameUiConfig = getProjectGameUiConfig(project);
    const nextGameUiConfig = { ...gameUiConfig };
    const firstFontAssetId = getFirstAssetIdByTypes(data, ["font"]);
    if (firstFontAssetId && !cleanText(nextGameUiConfig.fontAssetId)) {
      addProjectOperation(
        operations,
        "gameUi",
        "fontAssetId",
        "",
        firstFontAssetId,
        "绑定项目字体素材",
        "素材库已有字体时，优先让成品 UI 和 Runtime 使用同一套字体。"
      );
      nextGameUiConfig.fontAssetId = firstFontAssetId;
    }
    if (sceneCount >= 2 && !hasGameUiIdentity(nextGameUiConfig)) {
      addProjectOperation(
        operations,
        "gameUi",
        "preset",
        nextGameUiConfig.preset,
        "custom",
        "锁定一套项目专属 UI 基底",
        "不会替换用户素材，只把默认皮肤固定成可继续自定义的项目皮肤。"
      );
      nextGameUiConfig.preset = "custom";
      if (!cleanText(nextGameUiConfig.fontFamily) && !cleanText(nextGameUiConfig.fontAssetId)) {
        nextGameUiConfig.fontFamily = "Noto Sans SC, ui-sans-serif, sans-serif";
      }
      if (toCount(nextGameUiConfig.panelOpacity) < 82) {
        nextGameUiConfig.panelOpacity = 88;
      }
    }
    if (JSON.stringify(nextGameUiConfig) !== JSON.stringify(gameUiConfig)) {
      projectPatch.gameUiConfig = nextGameUiConfig;
    }

    const runtimeOperationCount = operations.filter((operation) => operation.area === "runtime").length;
    const dialogBoxOperationCount = operations.filter((operation) => operation.area === "dialogBox").length;
    const gameUiOperationCount = operations.filter((operation) => operation.area === "gameUi").length;

    return {
      changed: operations.length > 0,
      sceneCount,
      operations,
      operationCount: operations.length,
      runtimeOperationCount,
      dialogBoxOperationCount,
      gameUiOperationCount,
      projectPatch,
      summary:
        operations.length > 0
          ? `已准备 ${operations.length} 项项目级基础体验补全`
          : "项目级基础体验设置已经比较稳",
    };
  }

  function compactText(value, fallback = "", maxLength = 120) {
    const text = cleanText(value, fallback).replace(/\s+/g, " ");
    const safeMaxLength = Math.max(1, Number(maxLength) || 120);
    return text.length > safeMaxLength ? `${text.slice(0, safeMaxLength - 1)}…` : text;
  }

  function getReceiptTimestamp(value = "") {
    const date = value ? new Date(value) : new Date();
    if (Number.isNaN(date.getTime())) {
      return new Date().toISOString();
    }
    return date.toISOString();
  }

  function buildReceiptId(generatedAt = "") {
    return `polish-${getReceiptTimestamp(generatedAt).replace(/[-:T.Z]/g, "").slice(0, 14)}`;
  }

  function sanitizeFilePart(value, fallback = "canvasia-project") {
    return cleanText(value, fallback)
      .toLowerCase()
      .replace(/[^a-z0-9\u4e00-\u9fa5_-]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 48) || fallback;
  }

  function escapeMarkdownCell(value) {
    return String(value ?? "")
      .replace(/\|/g, "\\|")
      .replace(/\r?\n/g, "<br>")
      .trim();
  }

  function buildMarkdownTable(headers = [], rows = []) {
    const safeHeaders = toArray(headers).map(escapeMarkdownCell);
    const safeRows = toArray(rows).map((row) => toArray(row).map(escapeMarkdownCell));
    if (!safeHeaders.length || !safeRows.length) {
      return "";
    }

    return [
      `| ${safeHeaders.join(" | ")} |`,
      `| ${safeHeaders.map(() => "---").join(" | ")} |`,
      ...safeRows.map((row) => `| ${safeHeaders.map((_header, index) => row[index] ?? "").join(" | ")} |`),
    ].join("\n");
  }

  function buildProjectOneClickPolishPlan(data = {}, options = {}) {
    const { sceneStore, sceneOrder } = buildSceneStore(data);
    const sceneEdits = new Map();
    const readableOptions = options.readable ?? options.readability ?? {};
    const presentationOptions = options.presentation ?? {};
    const audioOptions = options.audio ?? {};
    const projectSettingsOptions = options.projectSettings ?? options.project ?? {};

    const readablePlan =
      typeof scriptReadabilityTools.buildReadableProjectSplitPlan === "function"
        ? scriptReadabilityTools.buildReadableProjectSplitPlan(
            buildDataWithScenes(data, sceneStore, sceneOrder),
            readableOptions
          )
        : { changed: false, scenePlans: [] };
    applyReadablePlan(sceneStore, sceneEdits, readablePlan);

    const presentationPlan =
      typeof scenePolishTools.buildProjectPresentationPolishPlan === "function"
        ? scenePolishTools.buildProjectPresentationPolishPlan(
            buildDataWithScenes(data, sceneStore, sceneOrder),
            presentationOptions
          )
        : { changed: false, scenePlans: [] };
    applyPresentationPlan(sceneStore, sceneEdits, presentationPlan);

    const audioPlan =
      typeof audioCueSheetTools.buildAudioCueAutoFixPlan === "function"
        ? audioCueSheetTools.buildAudioCueAutoFixPlan(buildDataWithScenes(data, sceneStore, sceneOrder), audioOptions)
        : { changed: false, scenePlans: [] };
    applyAudioPlan(sceneStore, sceneEdits, audioPlan);

    const projectSettingsPlan = buildProjectSettingsPolishPlan(
      buildDataWithScenes(data, sceneStore, sceneOrder),
      projectSettingsOptions
    );
    const pacingSnapshot = buildProjectPacingSnapshot(
      buildDataWithScenes(data, sceneStore, sceneOrder),
      options.pacing ?? {}
    );

    const orderedSceneIds = sceneOrder.filter((sceneId) => sceneEdits.has(sceneId));
    sceneEdits.forEach((_edit, sceneId) => {
      if (!orderedSceneIds.includes(sceneId)) {
        orderedSceneIds.push(sceneId);
      }
    });
    const scenePlans = orderedSceneIds.map((sceneId) => {
      const edit = sceneEdits.get(sceneId);
      const scene = sceneStore.get(sceneId);
      return {
        ...edit,
        scene: cloneValue(scene),
      };
    });

    const plan = {
      changed: scenePlans.length > 0 || projectSettingsPlan.changed,
      scenePlans,
      changedSceneCount: scenePlans.length,
      readableSplitCount: scenePlans.reduce((total, scenePlan) => total + scenePlan.readableSplitCount, 0),
      readableAddedBlockCount: scenePlans.reduce((total, scenePlan) => total + scenePlan.readableAddedBlockCount, 0),
      presentationChangedBlockCount: scenePlans.reduce(
        (total, scenePlan) => total + scenePlan.presentationChangedBlockCount,
        0
      ),
      presentationChangedFieldCount: scenePlans.reduce(
        (total, scenePlan) => total + scenePlan.presentationChangedFieldCount,
        0
      ),
      audioChangedBlockCount: scenePlans.reduce((total, scenePlan) => total + scenePlan.audioChangedBlockCount, 0),
      audioOperationCount: scenePlans.reduce((total, scenePlan) => total + scenePlan.audioOperationCount, 0),
      projectOperationCount: projectSettingsPlan.operationCount,
      projectOperations: projectSettingsPlan.operations,
      projectPatch: projectSettingsPlan.projectPatch,
      pacingSnapshot,
      pacingAverageScore: pacingSnapshot?.averageScore ?? null,
      pacingRoughSceneCount: pacingSnapshot?.roughSceneCount ?? 0,
      pacingReadySceneCount: pacingSnapshot?.readySceneCount ?? 0,
      runtimeSettingOperationCount: projectSettingsPlan.runtimeOperationCount,
      dialogBoxOperationCount: projectSettingsPlan.dialogBoxOperationCount,
      gameUiOperationCount: projectSettingsPlan.gameUiOperationCount,
      firstChangedSceneId: scenePlans[0]?.sceneId ?? "",
      firstChangedBlockId: scenePlans[0]?.firstChangedBlockId ?? "",
      firstChangedIndex: scenePlans[0]?.firstChangedIndex ?? -1,
      componentPlans: {
        readable: readablePlan,
        presentation: presentationPlan,
        audio: audioPlan,
        projectSettings: projectSettingsPlan,
        pacing: pacingSnapshot,
      },
    };
    plan.totalOperationCount =
      plan.readableSplitCount + plan.presentationChangedFieldCount + plan.audioOperationCount + plan.projectOperationCount;
    plan.summary = buildProjectOneClickPolishSummary(plan);
    return plan;
  }

  function buildProjectOneClickPolishReceipt(plan = {}, context = {}) {
    const generatedAt = getReceiptTimestamp(context.generatedAt);
    const scenePlans = toArray(plan.scenePlans).map((scenePlan) => ({
      sceneId: cleanText(scenePlan.sceneId),
      sceneName: compactText(scenePlan.sceneName, cleanText(scenePlan.sceneId, "未命名场景"), 120),
      firstChangedBlockId: cleanText(scenePlan.firstChangedBlockId),
      readableSplitCount: Math.max(0, Number(scenePlan.readableSplitCount) || 0),
      readableAddedBlockCount: Math.max(0, Number(scenePlan.readableAddedBlockCount) || 0),
      presentationChangedFieldCount: Math.max(0, Number(scenePlan.presentationChangedFieldCount) || 0),
      audioOperationCount: Math.max(0, Number(scenePlan.audioOperationCount) || 0),
    }));
    const projectOperations = toArray(plan.projectOperations).map((operation) => ({
      area: cleanText(operation.area, "project"),
      field: cleanText(operation.field),
      label: compactText(operation.label, "补齐项目设置", 120),
      detail: compactText(operation.detail, "发布前自动补齐一项安全默认设置。", 180),
      fromValue: operation.fromValue,
      toValue: operation.toValue,
    }));
    const projectOperationCount = Math.max(0, Number(plan.projectOperationCount) || projectOperations.length);
    const nextActions = [
      {
        label: "重新巡检确认",
        action: "run-project-inspection",
        detail: "确认一键整理没有新增错误。",
      },
      ...(projectOperationCount > 0
        ? [
            {
              label: "复看项目设置",
              action: "switch-screen",
              screen: "project",
              detail: "确认存档位、文本框、成品 UI 和字体绑定符合你的作品气质。",
            },
          ]
        : []),
      {
        label: "去试玩页确认",
        action: "switch-screen",
        screen: "preview",
        detail: "从第一处整理过的场景或入口场景开始快速过一遍。",
      },
      {
        label: "导出整理回执",
        action: "export-project-one-click-polish-receipt",
        detail: "把本次处理内容留给测试或发布记录。",
      },
    ];
    const receipt = {
      receiptId: cleanText(context.receiptId, buildReceiptId(generatedAt)),
      generatedAt,
      projectTitle: compactText(context.projectTitle, "Canvasia Engine Project", 160),
      safetySnapshotLabel: compactText(context.safetySnapshotLabel, "", 160),
      summary: compactText(plan.summary, buildProjectOneClickPolishSummary(plan), 240),
      changedSceneCount: Math.max(0, Number(plan.changedSceneCount) || scenePlans.length),
      totalOperationCount: Math.max(0, Number(plan.totalOperationCount) || 0),
      readableSplitCount: Math.max(0, Number(plan.readableSplitCount) || 0),
      readableAddedBlockCount: Math.max(0, Number(plan.readableAddedBlockCount) || 0),
      presentationChangedFieldCount: Math.max(0, Number(plan.presentationChangedFieldCount) || 0),
      audioOperationCount: Math.max(0, Number(plan.audioOperationCount) || 0),
      projectOperationCount,
      runtimeSettingOperationCount: Math.max(0, Number(plan.runtimeSettingOperationCount) || 0),
      dialogBoxOperationCount: Math.max(0, Number(plan.dialogBoxOperationCount) || 0),
      gameUiOperationCount: Math.max(0, Number(plan.gameUiOperationCount) || 0),
      pacingSnapshot: plan.pacingSnapshot ?? null,
      pacingAverageScore:
        plan.pacingAverageScore === null || typeof plan.pacingAverageScore === "undefined"
          ? null
          : Math.max(0, Number(plan.pacingAverageScore) || 0),
      pacingRoughSceneCount: Math.max(0, Number(plan.pacingRoughSceneCount) || 0),
      pacingReadySceneCount: Math.max(0, Number(plan.pacingReadySceneCount) || 0),
      scenePlans,
      projectOperations,
      nextActions:
        Math.max(0, Number(plan.pacingRoughSceneCount) || 0) > 0
          ? [
              ...nextActions.slice(0, 2),
              {
                label: "复看节奏问题",
                action: "switch-screen",
                screen: "preview",
                detail: `还有 ${Math.max(0, Number(plan.pacingRoughSceneCount) || 0)} 个场景建议试玩复看。`,
              },
              ...nextActions.slice(2),
            ]
          : nextActions,
    };
    return receipt;
  }

  function getReceiptNextActionLabel(action, fallback = "打开项目巡检并重新试玩。") {
    if (typeof action === "string") {
      return compactText(action, fallback, 140);
    }
    if (!action || typeof action !== "object") {
      return fallback;
    }
    const label = compactText(action.label, "", 80);
    const detail = compactText(action.detail, "", 120);
    return [label, detail].filter(Boolean).join("：") || fallback;
  }

  function buildProjectOneClickPolishReceiptFileName(receipt = {}) {
    const projectSlug = sanitizeFilePart(receipt.projectTitle);
    const receiptId = sanitizeFilePart(receipt.receiptId, buildReceiptId(receipt.generatedAt));
    return `${projectSlug}-${receiptId}.md`;
  }

  function buildProjectOneClickPolishReceiptMarkdown(receipt = {}) {
    if (!receipt || typeof receipt !== "object") {
      return "";
    }

    const summaryTable = buildMarkdownTable(
      ["项目", "内容"],
      [
        ["回执编号", receipt.receiptId],
        ["项目", receipt.projectTitle],
        ["整理时间", receipt.generatedAt],
        ["安全检查点", receipt.safetySnapshotLabel || "未记录"],
        ["涉及场景", `${receipt.changedSceneCount ?? 0} 个`],
        ["总处理项", `${receipt.totalOperationCount ?? 0} 项`],
        ["长文本", `${receipt.readableSplitCount ?? 0} 张，新增 ${receipt.readableAddedBlockCount ?? 0} 张卡片`],
        ["演出参数", `${receipt.presentationChangedFieldCount ?? 0} 项`],
        ["音频参数", `${receipt.audioOperationCount ?? 0} 项`],
        ["项目级设置", `${receipt.projectOperationCount ?? 0} 项`],
        [
          "节奏体检",
          receipt.pacingAverageScore === null || typeof receipt.pacingAverageScore === "undefined"
            ? "未启用"
            : `平均 ${receipt.pacingAverageScore} 分；待打磨 ${receipt.pacingRoughSceneCount ?? 0} 个；可试玩 ${
                receipt.pacingReadySceneCount ?? 0
              } 个`,
        ],
      ]
    );
    const sceneRows = toArray(receipt.scenePlans).map((scenePlan) => [
      scenePlan.sceneName || scenePlan.sceneId || "未命名场景",
      scenePlan.sceneId || "-",
      `${scenePlan.readableSplitCount ?? 0} / +${scenePlan.readableAddedBlockCount ?? 0}`,
      `${scenePlan.presentationChangedFieldCount ?? 0}`,
      `${scenePlan.audioOperationCount ?? 0}`,
      scenePlan.firstChangedBlockId || "-",
    ]);
    const sceneTable = buildMarkdownTable(["场景", "ID", "长文本 / 新增卡", "演出参数", "音频参数", "首处定位"], sceneRows);
    const projectRows = toArray(receipt.projectOperations).map((operation) => [
      operation.label || operation.field || "项目设置",
      operation.area || "project",
      operation.field || "-",
      operation.detail || "-",
    ]);
    const projectTable = buildMarkdownTable(["项目级补全", "领域", "字段", "说明"], projectRows);
    const pacingSnapshot = receipt.pacingSnapshot && typeof receipt.pacingSnapshot === "object" ? receipt.pacingSnapshot : null;
    const pacingRows = toArray(pacingSnapshot?.sceneHighlights).map((scene) => [
      scene.sceneName || scene.sceneId || "未命名场景",
      scene.score ?? 0,
      scene.gradeLabel || "待打磨",
      scene.issueSummary || scene.headline || "-",
      scene.actionSummary || "试玩确认",
    ]);
    const pacingIssueRows = toArray(pacingSnapshot?.topIssues).map((issue) => [
      issue.title || issue.code || "节奏问题",
      issue.count ?? 0,
    ]);
    const pacingTable = buildMarkdownTable(["场景", "分数", "阶段", "主要问题", "建议动作"], pacingRows);
    const pacingIssueTable = buildMarkdownTable(["高频节奏问题", "出现次数"], pacingIssueRows);
    const nextActions = toArray(receipt.nextActions).length
      ? receipt.nextActions.map((action, index) => `${index + 1}. ${getReceiptNextActionLabel(action)}`)
      : ["1. 打开项目巡检并重新试玩。"];

    return [
      "# 发布前整理回执",
      "",
      `- 回执编号：${receipt.receiptId || "未记录"}`,
      `- 项目：${receipt.projectTitle || "Canvasia Engine Project"}`,
      `- 摘要：${receipt.summary || "发布前整理完成"}`,
      "",
      "## 汇总",
      "",
      summaryTable,
      "",
      "## 场景明细",
      "",
      sceneTable || "本次没有可列出的场景明细。",
      "",
      "## 项目级补全",
      "",
      projectTable || "本次没有项目级设置补全。",
      "",
      "## 节奏体检",
      "",
      receipt.pacingAverageScore === null || typeof receipt.pacingAverageScore === "undefined"
        ? "本次没有启用节奏体检。"
        : `平均节奏分：${receipt.pacingAverageScore}；待打磨场景：${receipt.pacingRoughSceneCount ?? 0}；可试玩场景：${
            receipt.pacingReadySceneCount ?? 0
          }。`,
      "",
      pacingTable || "没有需要优先复看的节奏场景。",
      "",
      pacingIssueTable || "没有明显高频节奏问题。",
      "",
      "## 后续建议",
      "",
      ...nextActions,
      "",
    ].join("\n");
  }

  function buildProjectOneClickPolishReceiptClipboardSummary(receipt = {}) {
    if (!receipt || typeof receipt !== "object") {
      return "";
    }

    const sceneLines = toArray(receipt.scenePlans)
      .slice(0, 4)
      .map(
        (scenePlan) =>
          `- ${scenePlan.sceneName || scenePlan.sceneId || "未命名场景"}：长文本 ${scenePlan.readableSplitCount ?? 0}，演出 ${
            scenePlan.presentationChangedFieldCount ?? 0
          }，音频 ${scenePlan.audioOperationCount ?? 0}`
      );
    const overflowCount = Math.max(0, toArray(receipt.scenePlans).length - sceneLines.length);
    if (overflowCount > 0) {
      sceneLines.push(`- 另有 ${overflowCount} 个场景，请导出完整回执查看。`);
    }

    return [
      `发布前整理回执：${receipt.summary || "发布前整理完成"}`,
      `回执编号：${receipt.receiptId || "未记录"}`,
      `项目：${receipt.projectTitle || "Canvasia Engine Project"}`,
      `整理时间：${receipt.generatedAt || "未记录"}`,
      receipt.safetySnapshotLabel ? `安全检查点：${receipt.safetySnapshotLabel}` : "",
      `涉及场景：${receipt.changedSceneCount ?? 0} 个；处理项：${receipt.totalOperationCount ?? 0} 项`,
      (receipt.projectOperationCount ?? 0) > 0 ? `项目级补全：${receipt.projectOperationCount} 项` : "",
      receipt.pacingAverageScore === null || typeof receipt.pacingAverageScore === "undefined"
        ? ""
        : `节奏体检：平均 ${receipt.pacingAverageScore} 分，待打磨 ${receipt.pacingRoughSceneCount ?? 0} 个，可试玩 ${
            receipt.pacingReadySceneCount ?? 0
          } 个`,
      ...sceneLines,
      ...toArray(receipt.pacingSnapshot?.sceneHighlights)
        .slice(0, 3)
        .map((scene) => `- 节奏复看：${scene.sceneName || scene.sceneId}：${scene.issueSummary || scene.headline || "试玩确认"}`),
      ...toArray(receipt.projectOperations)
        .slice(0, 4)
        .map((operation) => `- ${operation.label || "项目设置"}：${operation.detail || "已补齐安全默认值。"}`),
      toArray(receipt.nextActions)[0] ? `下一步：${getReceiptNextActionLabel(receipt.nextActions[0])}` : "",
    ]
      .filter(Boolean)
      .join("\n");
  }

  function getProjectOneClickPolishDigest(data = {}, options = {}) {
    const plan = buildProjectOneClickPolishPlan(data, options);
    const previewNames = plan.scenePlans
      .slice(0, Math.max(1, Number(options.sceneNameLimit) || 3))
      .map((scenePlan) => scenePlan.sceneName)
      .filter(Boolean);

    return {
      canApply: plan.changed,
      actionLabel: plan.changed
        ? `一键发布前整理 ${plan.totalOperationCount} 项`
        : plan.pacingRoughSceneCount > 0
          ? "发布前整理已完成，建议复看节奏"
          : "发布前整理已完成",
      badgeLabel: plan.changed
        ? `${plan.changedSceneCount} 个场景 / ${plan.projectOperationCount} 项设置`
        : plan.pacingRoughSceneCount > 0
          ? `${plan.pacingRoughSceneCount} 个场景待试玩`
        : "无需处理",
      helperText: plan.changed
        ? `会依次处理长文本、基础演出、音频范围和项目级基础体验；涉及 ${
            previewNames.length ? previewNames.join("、") : "项目设置"
          }${plan.changedSceneCount > previewNames.length ? " 等场景" : ""}。`
        : plan.pacingRoughSceneCount > 0
          ? `自动整理项已完成；节奏体检平均 ${plan.pacingAverageScore} 分，还有 ${plan.pacingRoughSceneCount} 个场景建议试玩复看。`
        : "全项目长文本、基础演出、音频范围和项目级基础体验已经比较适合发布前检查。",
      plan,
    };
  }

  global.CanvasiaEditorProjectPolish = Object.freeze({
    buildProjectSettingsPolishPlan,
    buildProjectPacingSnapshot,
    buildProjectOneClickPolishPlan,
    buildProjectOneClickPolishSummary,
    getProjectOneClickPolishDigest,
    buildProjectOneClickPolishReceipt,
    buildProjectOneClickPolishReceiptFileName,
    buildProjectOneClickPolishReceiptMarkdown,
    buildProjectOneClickPolishReceiptClipboardSummary,
  });
})(typeof window !== "undefined" ? window : globalThis);
