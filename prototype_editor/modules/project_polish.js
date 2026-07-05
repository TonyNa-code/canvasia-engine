(function attachProjectPolishTools(global) {
  "use strict";

  const scriptReadabilityTools = global.CanvasiaEditorScriptReadability || {};
  const scenePolishTools = global.CanvasiaEditorScenePolish || {};
  const audioCueSheetTools = global.CanvasiaEditorAudioCueSheet || {};

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
    return `发布前整理完成：${parts.join("；")}`;
  }

  function buildProjectOneClickPolishPlan(data = {}, options = {}) {
    const { sceneStore, sceneOrder } = buildSceneStore(data);
    const sceneEdits = new Map();
    const readableOptions = options.readable ?? options.readability ?? {};
    const presentationOptions = options.presentation ?? {};
    const audioOptions = options.audio ?? {};

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
      changed: scenePlans.length > 0,
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
      firstChangedSceneId: scenePlans[0]?.sceneId ?? "",
      firstChangedBlockId: scenePlans[0]?.firstChangedBlockId ?? "",
      firstChangedIndex: scenePlans[0]?.firstChangedIndex ?? -1,
      componentPlans: {
        readable: readablePlan,
        presentation: presentationPlan,
        audio: audioPlan,
      },
    };
    plan.totalOperationCount =
      plan.readableSplitCount + plan.presentationChangedFieldCount + plan.audioOperationCount;
    plan.summary = buildProjectOneClickPolishSummary(plan);
    return plan;
  }

  function getProjectOneClickPolishDigest(data = {}, options = {}) {
    const plan = buildProjectOneClickPolishPlan(data, options);
    const previewNames = plan.scenePlans
      .slice(0, Math.max(1, Number(options.sceneNameLimit) || 3))
      .map((scenePlan) => scenePlan.sceneName)
      .filter(Boolean);

    return {
      canApply: plan.changed,
      actionLabel: plan.changed ? `一键发布前整理 ${plan.totalOperationCount} 项` : "发布前整理已完成",
      badgeLabel: plan.changed ? `${plan.changedSceneCount} 个场景可整理` : "无需处理",
      helperText: plan.changed
        ? `会依次处理长文本、基础演出和音频范围；涉及 ${previewNames.join("、")}${
            plan.changedSceneCount > previewNames.length ? " 等场景" : ""
          }。`
        : "全项目长文本、基础演出和音频范围已经比较适合发布前检查。",
      plan,
    };
  }

  global.CanvasiaEditorProjectPolish = Object.freeze({
    buildProjectOneClickPolishPlan,
    buildProjectOneClickPolishSummary,
    getProjectOneClickPolishDigest,
  });
})(typeof window !== "undefined" ? window : globalThis);
