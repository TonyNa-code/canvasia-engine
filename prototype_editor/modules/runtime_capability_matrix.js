(function attachRuntimeCapabilityMatrixTools(global) {
  const CAPABILITY_ROWS = Object.freeze([
    ["background", "画面", "full", "full", "背景 / CG 在 Web 与原生 Runtime 中播放；3D 场景会走原生结构检查与预览兜底。"],
    ["character_show", "角色", "full", "full", "支持角色登场、表情、站位、舞台参数和基础转场。"],
    ["character_hide", "角色", "full", "full", "支持角色离场和基础转场。"],
    ["dialogue", "文本", "full", "full", "支持说话人、表情同步、打字机、语音和文本历史。"],
    ["narration", "文本", "full", "full", "支持旁白文本、打字机、语音和文本历史。"],
    ["choice", "分支", "full", "full", "支持玩家选项、变量效果和目标场景跳转。"],
    ["condition", "分支", "full", "full", "支持条件分支、否则分支和变量判断。"],
    ["jump", "分支", "full", "full", "支持显式场景跳转。"],
    ["variable_set", "变量", "full", "full", "支持变量赋值。"],
    ["variable_add", "变量", "full", "full", "支持数值变量增减。"],
    ["music_play", "音频", "full", "full", "支持 BGM 播放、循环、音量、淡入和范围调度。"],
    ["music_stop", "音频", "full", "full", "支持 BGM 淡出停止。"],
    ["sfx_play", "音频", "full", "full", "支持音效播放与音量控制。"],
    ["video_play", "视频", "full", "partial", "Web Runtime 支持内嵌播放；原生 Runtime 支持 PyAV / OpenCV / 系统播放器兜底，需按目标平台验收。"],
    ["credits_roll", "结尾", "full", "full", "支持片尾字幕与回想 / 发布检查。"],
    ["particle_effect", "演出", "full", "full", "支持项目粒子预设、图片粒子、密度、速度、重力和颜色等参数。"],
    ["screen_shake", "演出", "full", "full", "支持屏幕震动。"],
    ["screen_flash", "演出", "full", "full", "支持闪屏。"],
    ["screen_fade", "演出", "full", "full", "支持淡入淡出。"],
    ["camera_zoom", "演出", "full", "full", "支持镜头推近、拉远和重置。"],
    ["camera_pan", "演出", "full", "full", "支持镜头平移和回中。"],
    ["screen_filter", "演出", "full", "full", "支持滤镜、色调和清除。"],
    ["depth_blur", "演出", "full", "full", "支持景深模糊和清除。"],
  ]).map(([type, group, webStatus, nativeStatus, note]) =>
    Object.freeze({ type, group, webStatus, nativeStatus, note })
  );

  const STATUS_LABELS = Object.freeze({
    full: "完整支持",
    partial: "需要验收",
    planned: "规划中",
    unsupported: "未支持",
    unknown: "未知卡片",
  });

  const STATUS_WEIGHT = Object.freeze({
    full: 0,
    partial: 1,
    planned: 2,
    unsupported: 3,
    unknown: 4,
  });

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function buildCollectionMap(source, idField = "id") {
    const result = new Map();
    if (source instanceof Map) {
      source.forEach((value, id) => {
        if (id) {
          result.set(String(id), value);
        }
      });
      return result;
    }
    if (source && typeof source === "object" && !Array.isArray(source)) {
      Object.entries(source).forEach(([id, value]) => {
        if (id) {
          result.set(String(id), value);
        }
      });
      return result;
    }
    toArray(source).forEach((item) => {
      if (item?.[idField]) {
        result.set(String(item[idField]), item);
      }
    });
    return result;
  }

  function getAssetList(data = {}) {
    return Array.isArray(data.assetList)
      ? data.assetList
      : Array.isArray(data.assets?.assets)
        ? data.assets.assets
        : [];
  }

  function buildAssetMap(data = {}) {
    const assetMap = new Map();
    getAssetList(data).forEach((asset) => {
      if (asset?.id) {
        assetMap.set(String(asset.id), asset);
      }
    });
    buildCollectionMap(data.assetsById).forEach((asset, id) => assetMap.set(id, asset));
    return assetMap;
  }

  function buildSceneMap(data = {}) {
    const sceneMap = new Map();
    toArray(data.scenes).forEach((scene) => {
      if (scene?.id) {
        sceneMap.set(String(scene.id), scene);
      }
    });
    buildCollectionMap(data.scenesById).forEach((scene, id) => sceneMap.set(id, scene));
    toArray(data.chapters).forEach((chapter) => {
      toArray(chapter.scenes).forEach((scene) => {
        if (scene?.id) {
          sceneMap.set(String(scene.id), scene);
        }
      });
    });
    return sceneMap;
  }

  function buildChapterMap(data = {}) {
    return new Map(
      toArray(data.chapters).map((chapter, index) => [
        String(chapter?.id ?? chapter?.chapterId ?? ""),
        {
          id: String(chapter?.id ?? chapter?.chapterId ?? ""),
          name: cleanText(chapter?.name ?? chapter?.title, `章节 ${index + 1}`),
          order: index,
          sceneOrder: toArray(chapter?.sceneOrder).map((sceneId) => String(sceneId ?? "")).filter(Boolean),
        },
      ])
    );
  }

  function getSceneRecords(data = {}) {
    const sceneMap = buildSceneMap(data);
    const chapterMap = buildChapterMap(data);
    const records = [];
    const seenSceneIds = new Set();

    toArray(data.chapters).forEach((chapter, chapterIndex) => {
      const chapterId = String(chapter?.id ?? chapter?.chapterId ?? "");
      const chapterName = cleanText(chapter?.name ?? chapter?.title, `章节 ${chapterIndex + 1}`);
      const directScenes = toArray(chapter?.scenes);
      const orderedIds = toArray(chapter?.sceneOrder).map((sceneId) => String(sceneId ?? "")).filter(Boolean);
      const scenes = directScenes.length
        ? directScenes
        : orderedIds.map((sceneId) => sceneMap.get(sceneId)).filter(Boolean);
      scenes.forEach((scene, sceneIndex) => {
        if (!scene?.id || seenSceneIds.has(String(scene.id))) {
          return;
        }
        seenSceneIds.add(String(scene.id));
        records.push({ scene, sceneIndex, chapterId, chapterName, chapterOrder: chapterIndex });
      });
    });

    toArray(data.scenes).forEach((scene, sceneIndex) => {
      if (!scene?.id || seenSceneIds.has(String(scene.id))) {
        return;
      }
      const chapter = chapterMap.get(String(scene.chapterId ?? ""));
      seenSceneIds.add(String(scene.id));
      records.push({
        scene,
        sceneIndex,
        chapterId: String(scene.chapterId ?? ""),
        chapterName: chapter?.name ?? "未分章",
        chapterOrder: chapter?.order ?? 9999,
      });
    });

    return records.sort((left, right) => {
      if (left.chapterOrder !== right.chapterOrder) {
        return left.chapterOrder - right.chapterOrder;
      }
      return left.sceneIndex - right.sceneIndex;
    });
  }

  function getRuntimeStatusLabel(status = "") {
    return STATUS_LABELS[status] ?? cleanText(status, "未知");
  }

  function getWorstStatus(...statuses) {
    return statuses.reduce((worst, status) => {
      const safeStatus = status || "unknown";
      return (STATUS_WEIGHT[safeStatus] ?? 99) > (STATUS_WEIGHT[worst] ?? 99) ? safeStatus : worst;
    }, "full");
  }

  function getCapabilityMap() {
    return new Map(CAPABILITY_ROWS.map((row) => [row.type, row]));
  }

  function addUsage(usageMap, block, record, assetMap) {
    const type = cleanText(block?.type, "unknown");
    const usage =
      usageMap.get(type) ??
      {
        type,
        count: 0,
        sceneNames: new Set(),
        chapterNames: new Set(),
        scene3dCount: 0,
      };
    usage.count += 1;
    usage.sceneNames.add(cleanText(record.scene?.name ?? record.scene?.title, record.scene?.id ?? "未命名场景"));
    usage.chapterNames.add(cleanText(record.chapterName, "未分章"));
    if (type === "background") {
      const asset = assetMap.get(cleanText(block.assetId));
      if (asset?.type === "scene3d") {
        usage.scene3dCount += 1;
      }
    }
    usageMap.set(type, usage);
  }

  function buildRuntimeCapabilityMatrix(data = {}) {
    const assetMap = buildAssetMap(data);
    const capabilityMap = getCapabilityMap();
    const usageMap = new Map();
    let totalBlockCount = 0;

    getSceneRecords(data).forEach((record) => {
      toArray(record.scene?.blocks).forEach((block) => {
        totalBlockCount += 1;
        addUsage(usageMap, block, record, assetMap);
      });
    });

    const rows = CAPABILITY_ROWS.map((capability) => {
      const usage = usageMap.get(capability.type);
      const nativeStatus = usage?.scene3dCount ? getWorstStatus(capability.nativeStatus, "partial") : capability.nativeStatus;
      return {
        ...capability,
        nativeStatus,
        usedCount: usage?.count ?? 0,
        scene3dCount: usage?.scene3dCount ?? 0,
        usedSceneNames: usage ? Array.from(usage.sceneNames).slice(0, 5) : [],
        usedChapterNames: usage ? Array.from(usage.chapterNames).slice(0, 5) : [],
        overallStatus: getWorstStatus(capability.webStatus, nativeStatus),
        webStatusLabel: getRuntimeStatusLabel(capability.webStatus),
        nativeStatusLabel: getRuntimeStatusLabel(nativeStatus),
        overallStatusLabel: getRuntimeStatusLabel(getWorstStatus(capability.webStatus, nativeStatus)),
      };
    });

    const unknownRows = Array.from(usageMap.values())
      .filter((usage) => !capabilityMap.has(usage.type))
      .map((usage) => ({
        type: usage.type,
        group: "未知",
        webStatus: "unknown",
        nativeStatus: "unknown",
        overallStatus: "unknown",
        webStatusLabel: getRuntimeStatusLabel("unknown"),
        nativeStatusLabel: getRuntimeStatusLabel("unknown"),
        overallStatusLabel: getRuntimeStatusLabel("unknown"),
        usedCount: usage.count,
        scene3dCount: usage.scene3dCount,
        usedSceneNames: Array.from(usage.sceneNames).slice(0, 5),
        usedChapterNames: Array.from(usage.chapterNames).slice(0, 5),
        note: "这个卡片类型还没有登记 Runtime 覆盖状态，需要先补矩阵和播放器支持。",
      }));

    const allRows = [...rows, ...unknownRows].sort((left, right) => {
      const leftUsed = left.usedCount > 0 ? 0 : 1;
      const rightUsed = right.usedCount > 0 ? 0 : 1;
      if (leftUsed !== rightUsed) {
        return leftUsed - rightUsed;
      }
      if ((STATUS_WEIGHT[right.overallStatus] ?? 0) !== (STATUS_WEIGHT[left.overallStatus] ?? 0)) {
        return (STATUS_WEIGHT[right.overallStatus] ?? 0) - (STATUS_WEIGHT[left.overallStatus] ?? 0);
      }
      return left.type.localeCompare(right.type, "en-US");
    });

    const usedRows = allRows.filter((row) => row.usedCount > 0);
    const issues = usedRows
      .filter((row) => row.overallStatus !== "full")
      .map((row) => ({
        severity: row.overallStatus === "unknown" || row.overallStatus === "unsupported" ? "blocker" : "warn",
        code: `runtime_${row.overallStatus}`,
        title: `${row.type}：${row.overallStatusLabel}`,
        detail: row.scene3dCount
          ? `${row.note} 当前还有 ${row.scene3dCount} 张 3D 场景背景，建议重点验收原生 Runtime。`
          : row.note,
        blockType: row.type,
        group: row.group,
        usedCount: row.usedCount,
        sceneNames: row.usedSceneNames,
      }));
    const summary = {
      capabilityCount: rows.length,
      totalBlockCount,
      usedTypeCount: usedRows.length,
      fullUsedTypeCount: usedRows.filter((row) => row.overallStatus === "full").length,
      partialUsedTypeCount: usedRows.filter((row) => row.overallStatus === "partial").length,
      unsupportedUsedTypeCount: usedRows.filter((row) => ["planned", "unsupported"].includes(row.overallStatus)).length,
      unknownUsedTypeCount: unknownRows.filter((row) => row.usedCount > 0).length,
      webPartialCount: usedRows.filter((row) => row.webStatus !== "full").length,
      nativePartialCount: usedRows.filter((row) => row.nativeStatus !== "full").length,
      scene3dBackgroundCount: usedRows.reduce((total, row) => total + (row.scene3dCount ?? 0), 0),
      issueCount: issues.length,
    };

    return {
      projectTitle: cleanText(data.project?.title, "Canvasia Project"),
      rows: allRows,
      usedRows,
      issues,
      summary,
    };
  }

  function getRuntimeCapabilityStatusDigest(matrix = {}) {
    const summary = matrix.summary ?? {};
    if ((summary.totalBlockCount ?? 0) === 0) {
      return {
        status: "empty",
        title: "还没有可检查的剧情卡片",
        detail: "项目里还没有剧情卡片。开始写第一场后，这里会检查 Web / 原生 Runtime 覆盖状态。",
      };
    }
    if ((summary.unknownUsedTypeCount ?? 0) > 0 || (summary.unsupportedUsedTypeCount ?? 0) > 0) {
      return {
        status: "blocked",
        title: "存在未确认 Runtime 支持",
        detail: "当前项目使用了尚未登记或未支持的卡片类型，建议先补 Runtime 支持再发布。",
      };
    }
    if ((summary.partialUsedTypeCount ?? 0) > 0 || (summary.nativePartialCount ?? 0) > 0 || (summary.webPartialCount ?? 0) > 0) {
      return {
        status: "warn",
        title: `${summary.partialUsedTypeCount ?? 0} 类卡片需要重点验收`,
        detail: "当前卡片可以导出，但部分能力在不同 Runtime 中依赖兜底或目标平台环境，发布前建议跑一遍对应包。",
      };
    }
    return {
      status: "ready",
      title: "Runtime 覆盖稳定",
      detail: "当前项目使用的卡片类型在 Web Runtime 和原生 Runtime 中都有完整覆盖。",
    };
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

  function csvCell(value) {
    return `"${String(value ?? "").replace(/"/g, '""')}"`;
  }

  function buildCsv(headers = [], rows = []) {
    return [headers, ...rows].map((row) => toArray(row).map(csvCell).join(",")).join("\n");
  }

  function buildRuntimeCapabilityMarkdown(matrix = {}, options = {}) {
    const summary = matrix.summary ?? {};
    const digest = getRuntimeCapabilityStatusDigest(matrix);
    const projectTitle = cleanText(options.projectTitle ?? matrix.projectTitle, "Canvasia Project");
    const generatedAt = cleanText(options.generatedAt);
    const usedRows = toArray(matrix.usedRows).map((row) => [
      row.group,
      row.type,
      row.usedCount,
      row.webStatusLabel,
      row.nativeStatusLabel,
      row.overallStatusLabel,
      row.usedSceneNames.join(" / "),
      row.note,
    ]);
    const issueRows = toArray(matrix.issues).map((issue, index) => [
      index + 1,
      issue.severity === "blocker" ? "先修" : "验收",
      issue.blockType,
      issue.usedCount,
      issue.sceneNames.join(" / "),
      issue.detail,
    ]);

    return [
      `# ${projectTitle} Runtime 覆盖矩阵`,
      "",
      generatedAt ? `生成时间：${generatedAt}` : "",
      "",
      `状态：${digest.title}`,
      "",
      digest.detail,
      "",
      "## 总览",
      "",
      buildMarkdownTable(
        ["剧情卡片", "已用类型", "完整类型", "需验收类型", "未知类型", "Web 风险", "原生风险", "3D 场景背景"],
        [
          [
            summary.totalBlockCount ?? 0,
            summary.usedTypeCount ?? 0,
            summary.fullUsedTypeCount ?? 0,
            summary.partialUsedTypeCount ?? 0,
            summary.unknownUsedTypeCount ?? 0,
            summary.webPartialCount ?? 0,
            summary.nativePartialCount ?? 0,
            summary.scene3dBackgroundCount ?? 0,
          ],
        ]
      ),
      "",
      "## 已使用卡片",
      "",
      buildMarkdownTable(["分组", "卡片类型", "使用次数", "Web Runtime", "原生 Runtime", "总体", "使用场景", "说明"], usedRows) ||
        "当前项目还没有剧情卡片。",
      "",
      "## 需要重点验收",
      "",
      buildMarkdownTable(["序号", "级别", "卡片类型", "使用次数", "场景", "说明"], issueRows) || "当前没有 Runtime 覆盖风险。",
      "",
    ].join("\n");
  }

  function buildRuntimeCapabilityCsv(matrix = {}) {
    const rows = toArray(matrix.rows).map((row) => [
      row.group,
      row.type,
      row.usedCount,
      row.webStatusLabel,
      row.nativeStatusLabel,
      row.overallStatusLabel,
      row.usedSceneNames.join(" / "),
      row.note,
    ]);
    return `\uFEFF${buildCsv(["分组", "卡片类型", "使用次数", "Web Runtime", "原生 Runtime", "总体", "使用场景", "说明"], rows)}\n`;
  }

  global.CanvasiaEditorRuntimeCapabilityMatrix = Object.freeze({
    CAPABILITY_ROWS,
    buildRuntimeCapabilityMatrix,
    getRuntimeCapabilityStatusDigest,
    buildRuntimeCapabilityMarkdown,
    buildRuntimeCapabilityCsv,
    getRuntimeStatusLabel,
  });
})(typeof window !== "undefined" ? window : globalThis);
