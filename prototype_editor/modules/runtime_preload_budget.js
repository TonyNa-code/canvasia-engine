(function attachRuntimePreloadBudgetTools(global) {
  const MIB = 1024 * 1024;

  const IMAGE_ASSET_TYPES = Object.freeze(["background", "sprite", "cg", "ui"]);
  const AUDIO_ASSET_TYPES = Object.freeze(["bgm", "sfx", "voice"]);
  const VIDEO_ASSET_TYPES = Object.freeze(["video"]);
  const PRELOADABLE_ASSET_TYPES = Object.freeze([...IMAGE_ASSET_TYPES, ...AUDIO_ASSET_TYPES, ...VIDEO_ASSET_TYPES]);

  const DEFAULT_BUDGETS = Object.freeze({
    criticalBudgetBytes: 96 * MIB,
    earlyBudgetBytes: 256 * MIB,
    totalPreloadBudgetBytes: 512 * MIB,
    sceneHotspotBudgetBytes: 128 * MIB,
    maxCriticalEntries: 18,
    maxEarlyEntries: 48,
    singleImageWarnBytes: 18 * MIB,
    singleAudioWarnBytes: 30 * MIB,
    singleVideoWarnBytes: 240 * MIB,
  });

  const PHASE_DEFINITIONS = Object.freeze({
    critical: Object.freeze({
      label: "首屏必备",
      detail: "入口场景前 12 张卡片会优先进入启动预热。",
      priority: 100,
    }),
    early: Object.freeze({
      label: "早期路线",
      detail: "前三个场景会在开局附近继续预热。",
      priority: 72,
    }),
    deferred: Object.freeze({
      label: "后续再加载",
      detail: "中后段素材不应拖慢第一次打开。",
      priority: 38,
    }),
    library: Object.freeze({
      label: "素材库保底",
      detail: "收藏的常用背景、CG、BGM 和 UI 会低优先级准备。",
      priority: 18,
    }),
  });

  const ASSET_TYPE_LABELS = Object.freeze({
    background: "背景",
    sprite: "立绘",
    cg: "CG",
    bgm: "音乐",
    sfx: "音效",
    voice: "语音",
    video: "视频",
    ui: "界面素材",
    unknown: "缺失素材",
  });

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function toFiniteBytes(value) {
    if (typeof value === "string") {
      const cleanValue = value.replace(/,/g, "").trim();
      if (!cleanValue) {
        return 0;
      }
      const unitMatch = cleanValue.match(/^([0-9]+(?:\.[0-9]+)?)\s*(b|kb|kib|mb|mib|gb|gib)$/i);
      if (unitMatch) {
        const amount = Number(unitMatch[1]);
        const unit = unitMatch[2].toLowerCase();
        const multiplier =
          unit === "gb" || unit === "gib"
            ? 1024 * MIB
            : unit === "mb" || unit === "mib"
              ? MIB
              : unit === "kb" || unit === "kib"
                ? 1024
                : 1;
        return Number.isFinite(amount) && amount > 0 ? Math.round(amount * multiplier) : 0;
      }
      const parsed = Number(cleanValue);
      return Number.isFinite(parsed) && parsed > 0 ? Math.round(parsed) : 0;
    }
    const parsed = Number(value);
    return Number.isFinite(parsed) && parsed > 0 ? Math.round(parsed) : 0;
  }

  function normalizeAssetSizeBytes(asset = {}) {
    return [
      asset.fileSizeBytes,
      asset.sizeBytes,
      asset.byteSize,
      asset.fileSize,
      asset.size,
    ].reduce((current, candidate) => current || toFiniteBytes(candidate), 0);
  }

  function formatBytes(bytes) {
    const size = Number(bytes);
    if (!Number.isFinite(size) || size < 0) {
      return "未知";
    }
    if (size < 1024) {
      return `${Math.round(size)} B`;
    }
    if (size < MIB) {
      return `${(size / 1024).toFixed(size < 10 * 1024 ? 1 : 0)} KB`;
    }
    if (size < 1024 * MIB) {
      return `${(size / MIB).toFixed(size < 10 * MIB ? 1 : 0)} MB`;
    }
    return `${(size / (1024 * MIB)).toFixed(2)} GB`;
  }

  function getAssetTypeLabel(type) {
    const cleanType = cleanText(type, "unknown");
    return ASSET_TYPE_LABELS[cleanType] ?? cleanType;
  }

  function getAssetList(data = {}) {
    if (Array.isArray(data.assetList)) {
      return data.assetList;
    }
    if (Array.isArray(data.assets?.assets)) {
      return data.assets.assets;
    }
    if (Array.isArray(data.assets)) {
      return data.assets;
    }
    return [];
  }

  function getAssetMap(data = {}) {
    const map = new Map();
    getAssetList(data).forEach((asset) => {
      const id = cleanText(asset?.id);
      if (id) {
        map.set(id, asset);
      }
    });
    return map;
  }

  function getCharacterList(data = {}) {
    if (Array.isArray(data.characters)) {
      return data.characters;
    }
    if (Array.isArray(data.characters?.characters)) {
      return data.characters.characters;
    }
    return [];
  }

  function getCharactersById(data = {}) {
    const map = new Map();
    getCharacterList(data).forEach((character) => {
      const id = cleanText(character?.id);
      if (id) {
        map.set(id, character);
      }
    });
    return map;
  }

  function normalizeAssetRecord(asset = {}, fallbackId = "") {
    const id = cleanText(asset.id, fallbackId);
    const type = cleanText(asset.type, "unknown");
    const sizeBytes = normalizeAssetSizeBytes(asset);
    const fileExists = asset.fileExists !== false && asset.isMissing !== true && asset.missing !== true;
    return {
      id,
      name: cleanText(asset.name, id || "未命名素材"),
      path: cleanText(asset.path || asset.relativePath || asset.publicUrl || asset.exportUrl),
      type,
      typeLabel: getAssetTypeLabel(type),
      sizeBytes,
      sizeLabel: sizeBytes > 0 ? formatBytes(sizeBytes) : "未知",
      fileExists,
      missingSize: fileExists && sizeBytes <= 0,
      missingReference: false,
    };
  }

  function normalizeMissingAssetRecord(assetId) {
    return {
      id: cleanText(assetId),
      name: cleanText(assetId, "缺失素材"),
      path: "",
      type: "unknown",
      typeLabel: ASSET_TYPE_LABELS.unknown,
      sizeBytes: 0,
      sizeLabel: "未知",
      fileExists: false,
      missingSize: true,
      missingReference: true,
    };
  }

  function getChapterId(chapter = {}) {
    return cleanText(chapter.chapterId || chapter.id);
  }

  function getSceneId(scene = {}) {
    return cleanText(scene.id || scene.sceneId);
  }

  function getOrderedChapters(data = {}) {
    const project = data.project && typeof data.project === "object" ? data.project : {};
    const chapters = toArray(data.chapters).filter((chapter) => chapter && typeof chapter === "object");
    const chapterOrder = toArray(project.chapterOrder).map((id) => cleanText(id)).filter(Boolean);
    const chapterMap = new Map(chapters.map((chapter) => [getChapterId(chapter), chapter]));
    const ordered = chapterOrder.filter((id) => chapterMap.has(id)).map((id) => chapterMap.get(id));
    chapters.forEach((chapter) => {
      if (!chapterOrder.includes(getChapterId(chapter))) {
        ordered.push(chapter);
      }
    });
    return ordered;
  }

  function getOrderedScenes(data = {}) {
    const chapters = getOrderedChapters(data);
    if (!chapters.length && Array.isArray(data.scenes)) {
      return data.scenes
        .filter((scene) => scene && typeof scene === "object")
        .map((scene, sceneIndex) => ({
          ...scene,
          __chapterId: "",
          __chapterName: "",
          __chapterIndex: 0,
          __sceneIndex: sceneIndex,
          __sceneIndexInChapter: sceneIndex,
        }));
    }

    const orderedScenes = [];
    chapters.forEach((chapter, chapterIndex) => {
      const scenes = toArray(chapter.scenes).filter((scene) => scene && typeof scene === "object");
      const sceneOrder = toArray(chapter.sceneOrder).map((id) => cleanText(id)).filter(Boolean);
      const sceneMap = new Map(scenes.map((scene) => [getSceneId(scene), scene]));
      const chapterScenes = sceneOrder.filter((id) => sceneMap.has(id)).map((id) => sceneMap.get(id));
      scenes.forEach((scene) => {
        if (!sceneOrder.includes(getSceneId(scene))) {
          chapterScenes.push(scene);
        }
      });
      chapterScenes.forEach((scene, sceneIndexInChapter) => {
        orderedScenes.push({
          ...scene,
          __chapterId: getChapterId(chapter),
          __chapterName: cleanText(chapter.name || chapter.title),
          __chapterIndex: chapterIndex,
          __sceneIndex: orderedScenes.length,
          __sceneIndexInChapter: sceneIndexInChapter,
        });
      });
    });
    return orderedScenes;
  }

  function getEntrySceneId(data = {}, orderedScenes = []) {
    const project = data.project && typeof data.project === "object" ? data.project : {};
    return cleanText(project.entrySceneId || project.startSceneId || project.firstSceneId) || getSceneId(orderedScenes[0] ?? {});
  }

  function getPreloadPhase(sceneIndex, blockIndex, sceneId, entrySceneId) {
    if (sceneId && sceneId === entrySceneId && blockIndex <= 12) {
      return "critical";
    }
    if (sceneIndex <= 2) {
      return "early";
    }
    return "deferred";
  }

  function getPhasePriority(phase) {
    return PHASE_DEFINITIONS[phase]?.priority ?? 10;
  }

  function getCharacterSpriteAssetId(charactersById, characterId, expressionId) {
    const character = charactersById.get(cleanText(characterId));
    if (!character || typeof character !== "object") {
      return "";
    }

    const expressionKey = cleanText(expressionId);
    const expression = toArray(character.expressions).find((item) => cleanText(item?.id) === expressionKey);
    const presentation = character.presentation && typeof character.presentation === "object" ? character.presentation : {};
    return (
      cleanText(expression?.spriteAssetId || expression?.assetId) ||
      cleanText(character.defaultSpriteId) ||
      cleanText(presentation.fallbackSpriteAssetId) ||
      cleanText(presentation.defaultSpriteId)
    );
  }

  function createPhaseSummary(phase, budgets) {
    const definition = PHASE_DEFINITIONS[phase] ?? {};
    const budgetKey =
      phase === "critical" ? "criticalBudgetBytes" : phase === "early" ? "earlyBudgetBytes" : "totalPreloadBudgetBytes";
    return {
      phase,
      label: definition.label ?? phase,
      detail: definition.detail ?? "",
      count: 0,
      bytes: 0,
      bytesLabel: "0 B",
      missingFileCount: 0,
      missingSizeCount: 0,
      budgetBytes: budgets[budgetKey],
      budgetLabel: formatBytes(budgets[budgetKey]),
      overBudget: false,
    };
  }

  function pushWarning(warnings, warning) {
    warnings.push({
      code: warning.code,
      severity: warning.severity ?? "tip",
      title: warning.title,
      detail: warning.detail,
      actionHint: warning.actionHint ?? "",
      assetId: warning.assetId ?? "",
      assetName: warning.assetName ?? "",
      sceneId: warning.sceneId ?? "",
      sceneName: warning.sceneName ?? "",
    });
  }

  function buildRuntimePreloadBudgetReport(data = {}, options = {}) {
    const budgets = { ...DEFAULT_BUDGETS, ...options };
    const assetsById = getAssetMap(data);
    const charactersById = getCharactersById(data);
    const orderedScenes = getOrderedScenes(data);
    const entrySceneId = getEntrySceneId(data, orderedScenes);
    const candidates = new Map();
    let order = 0;

    function addAsset(assetId, context = {}) {
      const safeAssetId = cleanText(assetId);
      if (!safeAssetId) {
        return;
      }
      const rawAsset = assetsById.get(safeAssetId);
      const isMissingReference = !rawAsset;
      if (rawAsset && !PRELOADABLE_ASSET_TYPES.includes(cleanText(rawAsset.type))) {
        return;
      }

      const assetRecord = rawAsset ? normalizeAssetRecord(rawAsset, safeAssetId) : normalizeMissingAssetRecord(safeAssetId);
      const phase = cleanText(context.phase, "deferred");
      const priority = getPhasePriority(phase) + Number(context.bonus ?? 0);
      const sceneId = getSceneId(context.scene ?? {});
      const sceneName = cleanText(context.scene?.name || context.scene?.title || sceneId);
      const occurrence = {
        phase,
        reason: cleanText(context.reason),
        sceneId,
        sceneName,
        blockId: cleanText(context.block?.id),
        blockType: cleanText(context.block?.type),
      };
      const existing = candidates.get(safeAssetId);

      if (existing) {
        if (occurrence.reason && !existing.reasons.includes(occurrence.reason)) {
          existing.reasons.push(occurrence.reason);
        }
        existing.occurrences.push(occurrence);
        if (priority <= existing.priority) {
          return;
        }
      }

      candidates.set(safeAssetId, {
        ...assetRecord,
        missingReference: isMissingReference,
        phase,
        priority,
        order: existing?.order ?? order++,
        sceneId,
        sceneName,
        blockId: occurrence.blockId,
        reason: occurrence.reason,
        reasons: existing?.reasons?.length ? existing.reasons : occurrence.reason ? [occurrence.reason] : [],
        occurrences: existing?.occurrences?.length ? existing.occurrences : [occurrence],
      });
    }

    orderedScenes.forEach((scene) => {
      const sceneIndex = Number(scene.__sceneIndex ?? 0);
      const sceneId = getSceneId(scene);
      toArray(scene.blocks).forEach((block, blockIndex) => {
        if (!block || typeof block !== "object") {
          return;
        }
        const blockType = cleanText(block.type);
        const phase = getPreloadPhase(sceneIndex, blockIndex, sceneId, entrySceneId);
        const bonus = phase === "critical" ? Math.max(0, 12 - blockIndex) : Math.max(0, 4 - sceneIndex);
        const sceneLabel = cleanText(scene.name || scene.title || sceneId);

        if (["background", "music_play", "sfx_play", "video_play"].includes(blockType)) {
          addAsset(block.assetId, {
            phase,
            reason: `${sceneLabel} / ${blockType}`,
            scene,
            block,
            bonus,
          });
        }

        if (["dialogue", "narration"].includes(blockType)) {
          addAsset(block.voiceAssetId, {
            phase,
            reason: `${sceneLabel} / voice`,
            scene,
            block,
            bonus,
          });
        }

        if (["character_show", "dialogue"].includes(blockType)) {
          addAsset(getCharacterSpriteAssetId(charactersById, block.characterId || block.speakerId, block.expressionId), {
            phase,
            reason: `${sceneLabel} / sprite`,
            scene,
            block,
            bonus,
          });
        }
      });
    });

    getAssetList(data).forEach((asset) => {
      const assetType = cleanText(asset?.type);
      if (["background", "cg", "bgm", "ui"].includes(assetType) && asset?.favorite) {
        addAsset(asset.id, {
          phase: "library",
          reason: "favorite asset",
          bonus: 8,
        });
      }
    });

    const entries = Array.from(candidates.values())
      .sort((left, right) => right.priority - left.priority || left.order - right.order || left.name.localeCompare(right.name, "zh-Hans-CN"))
      .map((entry, index) => ({ ...entry, preloadIndex: index + 1 }));
    const phaseOrder = ["critical", "early", "deferred", "library"];
    const phases = Object.fromEntries(phaseOrder.map((phase) => [phase, createPhaseSummary(phase, budgets)]));
    const sceneMap = new Map();

    entries.forEach((entry) => {
      const summary = phases[entry.phase] ?? phases.deferred;
      summary.count += 1;
      summary.bytes += entry.sizeBytes;
      summary.missingFileCount += entry.fileExists ? 0 : 1;
      summary.missingSizeCount += entry.missingSize ? 1 : 0;

      if (entry.sceneId) {
        const key = entry.sceneId;
        const sceneSummary =
          sceneMap.get(key) ??
          {
            sceneId: entry.sceneId,
            sceneName: entry.sceneName || entry.sceneId,
            criticalBytes: 0,
            earlyBytes: 0,
            totalBytes: 0,
            count: 0,
            missingFileCount: 0,
            topAssets: [],
          };
        if (entry.phase === "critical") {
          sceneSummary.criticalBytes += entry.sizeBytes;
        }
        if (entry.phase === "critical" || entry.phase === "early") {
          sceneSummary.earlyBytes += entry.sizeBytes;
        }
        sceneSummary.totalBytes += entry.sizeBytes;
        sceneSummary.count += 1;
        sceneSummary.missingFileCount += entry.fileExists ? 0 : 1;
        sceneSummary.topAssets.push(entry);
        sceneMap.set(key, sceneSummary);
      }
    });

    Object.values(phases).forEach((summary) => {
      summary.bytesLabel = formatBytes(summary.bytes);
      summary.overBudget =
        summary.phase === "critical"
          ? summary.bytes > budgets.criticalBudgetBytes
          : summary.phase === "early"
            ? summary.bytes > budgets.earlyBudgetBytes
            : false;
    });

    const scenes = Array.from(sceneMap.values())
      .map((scene) => ({
        ...scene,
        criticalLabel: formatBytes(scene.criticalBytes),
        earlyLabel: formatBytes(scene.earlyBytes),
        totalLabel: formatBytes(scene.totalBytes),
        topAssets: scene.topAssets.sort((left, right) => right.sizeBytes - left.sizeBytes).slice(0, 4),
        overHotspotBudget: scene.earlyBytes > budgets.sceneHotspotBudgetBytes,
      }))
      .sort((left, right) => right.earlyBytes - left.earlyBytes || right.count - left.count);

    const warnings = [];
    const criticalAndEarlyEntries = entries.filter((entry) => entry.phase === "critical" || entry.phase === "early");
    const totalPreloadBytes = entries.reduce((sum, entry) => sum + entry.sizeBytes, 0);

    if (phases.critical.bytes > budgets.criticalBudgetBytes) {
      pushWarning(warnings, {
        code: "critical_over_budget",
        severity: "danger",
        title: "首屏必备素材过重",
        detail: `首屏阶段已经达到 ${phases.critical.bytesLabel}，超过建议预算 ${formatBytes(budgets.criticalBudgetBytes)}。`,
        actionHint: "优先压缩入口场景背景、立绘、语音，OP 视频尽量延后播放或降低码率。",
      });
    }

    if (phases.early.bytes > budgets.earlyBudgetBytes) {
      pushWarning(warnings, {
        code: "early_over_budget",
        severity: "warn",
        title: "开局早期路线加载压力偏高",
        detail: `前三个场景早期预热素材达到 ${phases.early.bytesLabel}，建议控制在 ${formatBytes(budgets.earlyBudgetBytes)} 以内。`,
        actionHint: "把后面才会用到的 CG、BGM 或视频移到更靠后的场景，减少开局预热。",
      });
    }

    if (totalPreloadBytes > budgets.totalPreloadBudgetBytes) {
      pushWarning(warnings, {
        code: "total_preload_over_budget",
        severity: "warn",
        title: "预热清单整体偏重",
        detail: `当前预热候选合计 ${formatBytes(totalPreloadBytes)}，后续低配设备可能会持续后台加载。`,
        actionHint: "减少收藏素材、压缩大素材，避免把整部作品都变成开局预热任务。",
      });
    }

    const missingEarlyAssets = criticalAndEarlyEntries.filter((entry) => !entry.fileExists);
    if (missingEarlyAssets.length > 0) {
      pushWarning(warnings, {
        code: "critical_missing_assets",
        severity: "danger",
        title: "首屏或早期路线有缺失素材",
        detail: `${missingEarlyAssets.length} 个首屏 / 早期素材缺文件或缺登记，导出后可能直接黑屏、静音或跳过演出。`,
        actionHint: "先补齐缺失素材，再做性能压缩。",
      });
    }

    const missingSizeCount = criticalAndEarlyEntries.filter((entry) => entry.missingSize && entry.fileExists).length;
    if (missingSizeCount > 0) {
      pushWarning(warnings, {
        code: "critical_missing_size",
        severity: "warn",
        title: "部分首屏素材缺少体积记录",
        detail: `${missingSizeCount} 个首屏 / 早期素材没有文件大小，报告会低估真实加载压力。`,
        actionHint: "重新导入或替换素材，让编辑器补齐大小信息。",
      });
    }

    if (phases.critical.count > budgets.maxCriticalEntries) {
      pushWarning(warnings, {
        code: "too_many_critical_entries",
        severity: "warn",
        title: "首屏素材条目太多",
        detail: `首屏阶段需要准备 ${phases.critical.count} 个素材，超过建议上限 ${budgets.maxCriticalEntries} 个。`,
        actionHint: "入口场景尽量用少量高质量素材，复杂演出可以放到点击开始之后。",
      });
    }

    if (phases.critical.count + phases.early.count > budgets.maxEarlyEntries) {
      pushWarning(warnings, {
        code: "too_many_early_entries",
        severity: "warn",
        title: "开局预热素材数量偏多",
        detail: `首屏和早期路线合计 ${phases.critical.count + phases.early.count} 个素材，建议控制在 ${budgets.maxEarlyEntries} 个以内。`,
        actionHint: "删掉未真正需要的收藏项，或把支线专用素材移到对应支线后段。",
      });
    }

    entries
      .filter((entry) => {
        if (IMAGE_ASSET_TYPES.includes(entry.type)) {
          return entry.sizeBytes > budgets.singleImageWarnBytes;
        }
        if (AUDIO_ASSET_TYPES.includes(entry.type)) {
          return entry.sizeBytes > budgets.singleAudioWarnBytes;
        }
        if (VIDEO_ASSET_TYPES.includes(entry.type)) {
          return entry.sizeBytes > budgets.singleVideoWarnBytes;
        }
        return false;
      })
      .slice(0, 6)
      .forEach((entry) => {
        pushWarning(warnings, {
          code: "single_asset_over_budget",
          severity: entry.phase === "critical" ? "danger" : "warn",
          title: "单个预热素材偏大",
          detail: `${entry.name} 是 ${entry.typeLabel}，当前 ${entry.sizeLabel}，会拖慢 ${PHASE_DEFINITIONS[entry.phase]?.label ?? entry.phase}。`,
          actionHint: "保留源文件，另存发布用压缩版或降低分辨率 / 码率。",
          assetId: entry.id,
          assetName: entry.name,
          sceneId: entry.sceneId,
          sceneName: entry.sceneName,
        });
      });

    scenes
      .filter((scene) => scene.overHotspotBudget)
      .slice(0, 3)
      .forEach((scene) => {
        pushWarning(warnings, {
          code: "scene_hotspot",
          severity: "warn",
          title: "单场景加载热点偏重",
          detail: `${scene.sceneName} 的首屏 / 早期素材合计 ${scene.earlyLabel}，可能成为开局卡顿点。`,
          actionHint: "优先压缩这个场景里的背景、立绘、视频和长 BGM。",
          sceneId: scene.sceneId,
          sceneName: scene.sceneName,
        });
      });

    const dangerCount = warnings.filter((warning) => warning.severity === "danger").length;
    const warnCount = warnings.filter((warning) => warning.severity === "warn").length;
    const releaseRiskLevel = dangerCount > 0 ? "danger" : warnCount > 0 ? "warn" : "ready";

    return {
      budgets: {
        ...budgets,
        criticalBudgetLabel: formatBytes(budgets.criticalBudgetBytes),
        earlyBudgetLabel: formatBytes(budgets.earlyBudgetBytes),
        totalPreloadBudgetLabel: formatBytes(budgets.totalPreloadBudgetBytes),
      },
      entrySceneId,
      entries,
      topEntries: entries.slice().sort((left, right) => right.sizeBytes - left.sizeBytes).slice(0, 12),
      phases,
      phaseList: phaseOrder.map((phase) => phases[phase]),
      scenes,
      warnings,
      totals: {
        totalEntries: entries.length,
        totalBytes: totalPreloadBytes,
        totalLabel: formatBytes(totalPreloadBytes),
        criticalAndEarlyEntries: criticalAndEarlyEntries.length,
        criticalAndEarlyBytes: phases.critical.bytes + phases.early.bytes,
        criticalAndEarlyLabel: formatBytes(phases.critical.bytes + phases.early.bytes),
        missingFileCount: entries.filter((entry) => !entry.fileExists).length,
        missingSizeCount: entries.filter((entry) => entry.missingSize && entry.fileExists).length,
        dangerCount,
        warnCount,
      },
      releaseRiskLevel,
    };
  }

  function getRuntimePreloadBudgetDigest(report = {}) {
    const totals = report.totals ?? {};
    const critical = report.phases?.critical ?? {};
    const early = report.phases?.early ?? {};
    const level = report.releaseRiskLevel ?? "ready";
    const title =
      level === "danger"
        ? "首屏压力偏高"
        : level === "warn"
          ? "开局建议瘦身"
          : "首屏加载健康";
    const detail =
      level === "danger"
        ? "正式发包前建议先处理入口场景的大素材和缺文件，否则玩家第一次打开时最容易卡住。"
        : level === "warn"
          ? "目前没有硬阻塞，但开局路线已经值得做一轮压缩或延后加载。"
          : "首屏和早期路线没有明显预热压力，可以继续打磨内容演出。";

    return {
      level,
      title,
      detail,
      actionLabel: level === "ready" ? "导出预热清单" : "导出瘦身建议",
      badges: [
        `首屏 ${critical.bytesLabel ?? "0 B"}`,
        `早期 ${early.bytesLabel ?? "0 B"}`,
        `${totals.totalEntries ?? 0} 个候选素材`,
        (totals.missingFileCount ?? 0) > 0 ? `缺文件 ${totals.missingFileCount} 个` : "无首屏缺文件",
      ],
    };
  }

  function buildMarkdownTable(headers, rows) {
    if (!rows.length) {
      return "";
    }
    const escapeCell = (value) => String(value ?? "").replace(/\|/g, "\\|").replace(/\n+/g, " ");
    return [
      `| ${headers.map(escapeCell).join(" | ")} |`,
      `| ${headers.map(() => "---").join(" | ")} |`,
      ...rows.map((row) => `| ${row.map(escapeCell).join(" | ")} |`),
    ].join("\n");
  }

  function buildRuntimePreloadBudgetMarkdown(report = {}, options = {}) {
    const projectTitle = cleanText(options.projectTitle, "Canvasia Project");
    const generatedAt = cleanText(options.generatedAt);
    const digest = getRuntimePreloadBudgetDigest(report);
    const totals = report.totals ?? {};
    const phaseRows = toArray(report.phaseList).map((phase) => [
      phase.label,
      phase.count,
      phase.bytesLabel,
      phase.budgetLabel,
      phase.missingFileCount,
      phase.missingSizeCount,
      phase.overBudget ? "超过建议预算" : "正常",
    ]);
    const assetRows = toArray(report.topEntries).map((entry, index) => [
      index + 1,
      entry.name,
      entry.typeLabel,
      PHASE_DEFINITIONS[entry.phase]?.label ?? entry.phase,
      entry.sizeLabel,
      entry.fileExists ? "已导入" : "缺文件",
      entry.reason,
    ]);
    const sceneRows = toArray(report.scenes).slice(0, 8).map((scene, index) => [
      index + 1,
      scene.sceneName,
      scene.earlyLabel,
      scene.count,
      scene.missingFileCount,
      scene.overHotspotBudget ? "热点偏重" : "正常",
    ]);
    const warningRows = toArray(report.warnings).map((warning, index) => [
      index + 1,
      warning.severity === "danger" ? "高风险" : warning.severity === "warn" ? "提醒" : "提示",
      warning.title,
      warning.assetName || warning.sceneName,
      warning.detail,
      warning.actionHint,
    ]);

    return [
      `# ${projectTitle} Runtime 首屏加载预算`,
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
        ["预热素材", "首屏+早期体积", "总预热体积", "缺文件", "缺体积记录", "提醒数"],
        [[
          totals.totalEntries ?? 0,
          totals.criticalAndEarlyLabel ?? "0 B",
          totals.totalLabel ?? "0 B",
          totals.missingFileCount ?? 0,
          totals.missingSizeCount ?? 0,
          (totals.dangerCount ?? 0) + (totals.warnCount ?? 0),
        ]]
      ),
      "",
      "## 阶段预算",
      "",
      buildMarkdownTable(["阶段", "数量", "体积", "建议预算", "缺文件", "缺体积", "状态"], phaseRows) || "当前没有可统计的预热素材。",
      "",
      "## 首屏 / 早期素材排行",
      "",
      buildMarkdownTable(["排名", "素材", "类型", "阶段", "大小", "文件状态", "来源"], assetRows) || "当前没有预热候选素材。",
      "",
      "## 场景热点",
      "",
      buildMarkdownTable(["排名", "场景", "首屏/早期体积", "素材数", "缺文件", "状态"], sceneRows) || "当前没有明显场景热点。",
      "",
      "## 发布前建议",
      "",
      buildMarkdownTable(["序号", "级别", "问题", "对象", "说明", "建议动作"], warningRows) || "当前没有明显首屏加载问题。",
      "",
    ].join("\n");
  }

  function formatCsvCell(value) {
    const text = String(value ?? "");
    if (/[",\n\r]/.test(text)) {
      return `"${text.replace(/"/g, '""')}"`;
    }
    return text;
  }

  function buildCsv(headers, rows) {
    return [headers, ...rows].map((row) => row.map(formatCsvCell).join(",")).join("\n");
  }

  function buildRuntimePreloadBudgetCsv(report = {}) {
    const rows = toArray(report.entries).map((entry, index) => [
      index + 1,
      entry.name,
      entry.id,
      entry.typeLabel,
      PHASE_DEFINITIONS[entry.phase]?.label ?? entry.phase,
      entry.sizeBytes,
      entry.sizeLabel,
      entry.fileExists ? "已导入" : "缺文件",
      entry.missingSize ? "缺体积记录" : "",
      entry.sceneName,
      entry.reason,
      entry.path,
    ]);
    return `\uFEFF${buildCsv(
      ["序号", "素材", "ID", "类型", "预热阶段", "字节", "大小", "文件状态", "体积状态", "场景", "来源", "路径"],
      rows
    )}\n`;
  }

  global.CanvasiaEditorRuntimePreloadBudget = Object.freeze({
    DEFAULT_BUDGETS,
    PHASE_DEFINITIONS,
    IMAGE_ASSET_TYPES,
    AUDIO_ASSET_TYPES,
    VIDEO_ASSET_TYPES,
    PRELOADABLE_ASSET_TYPES,
    getAssetList,
    getAssetMap,
    getCharacterList,
    getOrderedScenes,
    getEntrySceneId,
    getPreloadPhase,
    getPhasePriority,
    getCharacterSpriteAssetId,
    normalizeAssetSizeBytes,
    formatBytes,
    buildRuntimePreloadBudgetReport,
    getRuntimePreloadBudgetDigest,
    buildRuntimePreloadBudgetMarkdown,
    buildRuntimePreloadBudgetCsv,
  });
})(typeof window !== "undefined" ? window : globalThis);
