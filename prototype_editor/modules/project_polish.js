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
      scenePlans,
      nextActions: [
        "打开项目巡检，确认没有新增错误。",
        "进入试玩页，从第一处整理过的场景开始快速过一遍。",
        "如果效果不满意，可在项目历史里恢复到整理前自动检查点。",
      ],
    };
    return receipt;
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
    const nextActions = toArray(receipt.nextActions).length
      ? receipt.nextActions.map((action, index) => `${index + 1}. ${action}`)
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
      ...sceneLines,
      toArray(receipt.nextActions)[0] ? `下一步：${receipt.nextActions[0]}` : "",
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
    buildProjectOneClickPolishReceipt,
    buildProjectOneClickPolishReceiptFileName,
    buildProjectOneClickPolishReceiptMarkdown,
    buildProjectOneClickPolishReceiptClipboardSummary,
  });
})(typeof window !== "undefined" ? window : globalThis);
