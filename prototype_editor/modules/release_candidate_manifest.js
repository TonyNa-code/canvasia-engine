(function attachReleaseCandidateManifestTools(global) {
  const DELIVERABLE_DEFINITIONS = Object.freeze([
    {
      id: "playable_export",
      label: "Playable build",
      owner: "Release",
      description: "Web / desktop / native Runtime export that a tester can actually open.",
    },
    {
      id: "release_control",
      label: "Release control report",
      owner: "Producer",
      description: "Release gate, fix order, validation summary, and latest export status.",
    },
    {
      id: "production_backlog",
      label: "Production backlog",
      owner: "Producer",
      description: "Cross-module task queue for the remaining release work.",
    },
    {
      id: "runtime_matrix",
      label: "Runtime acceptance matrix",
      owner: "Runtime",
      description: "Web and native Runtime coverage for the story blocks used by the project.",
    },
    {
      id: "screenplay",
      label: "Screenplay / script",
      owner: "Writing",
      description: "Full readable script for proofreading, translation, and voice handoff.",
    },
    {
      id: "director_cues",
      label: "Director cue sheet",
      owner: "Direction",
      description: "Scene-by-scene visual, audio, route, pacing, and effect beats.",
    },
    {
      id: "voice_sheet",
      label: "Voice production sheet",
      owner: "Audio",
      description: "Voice line readiness, missing files, long lines, and speaker coverage.",
    },
    {
      id: "localization_pack",
      label: "Localization pack",
      owner: "Localization",
      description: "Language coverage and translator CSV handoff when the project has multiple languages.",
    },
    {
      id: "unlockable_manifest",
      label: "Unlockable content manifest",
      owner: "Content",
      description: "Gallery, replay, archive, ending, and achievement coverage for public-preview release.",
    },
    {
      id: "artifact_integrity",
      label: "Artifact integrity",
      owner: "Release",
      description: "Archive, checksum, and verifier files for public distribution.",
    },
  ]);

  const BLOCK_LABELS = Object.freeze({
    background: "Background",
    dialogue: "Dialogue",
    narration: "Narration",
    choice: "Choice",
    condition: "Condition",
    jump: "Jump",
    character_show: "Character show",
    character_move: "Character motion",
    character_hide: "Character hide",
    music_play: "BGM",
    music_stop: "BGM stop",
    sfx_play: "SFX",
    video_play: "Video",
    particle_effect: "Particle",
    wait: "Wait",
    screen_shake: "Shake",
    screen_flash: "Flash",
    screen_fade: "Fade",
    camera_zoom: "Camera zoom",
    camera_pan: "Camera pan",
    screen_filter: "Filter",
    depth_blur: "Depth blur",
    credits_roll: "Credits",
    variable_set: "Variable set",
    variable_add: "Variable add",
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

  function clamp(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  function normalizeSeverity(severity = "") {
    if (["blocker", "danger", "error", "fail", "failed", "blocked"].includes(severity)) {
      return "blocker";
    }
    if (["warn", "warning", "review", "preview", "needs_review"].includes(severity)) {
      return "warn";
    }
    if (["good", "ready", "ok", "pass", "passed"].includes(severity)) {
      return "good";
    }
    return "tip";
  }

  function getSeverityLabel(severity = "") {
    const normalized = normalizeSeverity(severity);
    if (normalized === "blocker") {
      return "Blocker";
    }
    if (normalized === "warn") {
      return "Needs review";
    }
    if (normalized === "good") {
      return "Ready";
    }
    return "Polish";
  }

  function getSeverityWeight(severity = "") {
    const normalized = normalizeSeverity(severity);
    if (normalized === "blocker") {
      return 100;
    }
    if (normalized === "warn") {
      return 60;
    }
    if (normalized === "tip") {
      return 25;
    }
    return 0;
  }

  function formatEstimatedDuration(seconds) {
    const safeSeconds = Math.max(0, Math.round(Number(seconds) || 0));
    if (safeSeconds < 60) {
      return `about ${safeSeconds}s`;
    }
    const minutes = Math.floor(safeSeconds / 60);
    const remainingSeconds = safeSeconds % 60;
    return remainingSeconds > 0 ? `about ${minutes}m ${remainingSeconds}s` : `about ${minutes}m`;
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
        : Array.isArray(data.assets)
          ? data.assets
          : [];
  }

  function getCharacterList(data = {}) {
    return Array.isArray(data.characters)
      ? data.characters
      : Array.isArray(data.characters?.characters)
        ? data.characters.characters
        : [];
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

  function getSceneRecords(data = {}) {
    const sceneMap = buildSceneMap(data);
    const records = [];
    const seenSceneIds = new Set();

    toArray(data.chapters).forEach((chapter, chapterIndex) => {
      const chapterId = cleanText(chapter?.id ?? chapter?.chapterId, `chapter_${chapterIndex + 1}`);
      const chapterName = cleanText(chapter?.name ?? chapter?.title, `Chapter ${chapterIndex + 1}`);
      const directScenes = toArray(chapter?.scenes);
      const orderedIds = toArray(chapter?.sceneOrder).map((sceneId) => cleanText(sceneId)).filter(Boolean);
      const scenes = directScenes.length
        ? directScenes
        : orderedIds.map((sceneId) => sceneMap.get(sceneId)).filter(Boolean);

      scenes.forEach((scene, sceneIndex) => {
        const sceneId = cleanText(scene?.id);
        if (!sceneId || seenSceneIds.has(sceneId)) {
          return;
        }
        seenSceneIds.add(sceneId);
        records.push({ scene, sceneIndex, chapterId, chapterName, chapterOrder: chapterIndex });
      });
    });

    toArray(data.scenes).forEach((scene, sceneIndex) => {
      const sceneId = cleanText(scene?.id);
      if (!sceneId || seenSceneIds.has(sceneId)) {
        return;
      }
      seenSceneIds.add(sceneId);
      records.push({
        scene,
        sceneIndex,
        chapterId: cleanText(scene.chapterId),
        chapterName: "Unchaptered",
        chapterOrder: 9999,
      });
    });

    return records.sort((left, right) => {
      if (left.chapterOrder !== right.chapterOrder) {
        return left.chapterOrder - right.chapterOrder;
      }
      return left.sceneIndex - right.sceneIndex;
    });
  }

  function getBlockLabel(type) {
    return BLOCK_LABELS[type] ?? cleanText(type, "Custom block");
  }

  function getResolution(data = {}, context = {}) {
    const resolution = context.resolution ?? data.project?.resolution ?? data.resolution ?? {};
    return {
      width: toCount(resolution.width, 1920),
      height: toCount(resolution.height, 1080),
    };
  }

  function getDefaultLanguage(data = {}) {
    return cleanText(data.i18n?.defaultLanguage ?? data.project?.language ?? data.project?.defaultLanguage, "zh-CN");
  }

  function getSupportedLanguages(data = {}, localizationCoverage = null) {
    const languages = [];
    const addLanguage = (language) => {
      const value = cleanText(language?.code ?? language?.id ?? language?.language ?? language?.locale ?? language);
      if (value && !languages.includes(value)) {
        languages.push(value);
      }
    };

    toArray(localizationCoverage?.supportedLanguages).forEach(addLanguage);
    [
      data.i18n?.supportedLanguages,
      data.i18n?.languages,
      data.i18n?.locales,
      data.project?.supportedLanguages,
      data.project?.languages,
      data.project?.locales,
    ].forEach((list) => toArray(list).forEach(addLanguage));
    addLanguage(getDefaultLanguage(data));
    return languages.length ? languages : [getDefaultLanguage(data)];
  }

  function buildContentInventory(data = {}, context = {}) {
    const sceneRecords = getSceneRecords(data);
    const blockCounts = new Map();
    let totalBlockCount = 0;
    sceneRecords.forEach((record) => {
      toArray(record.scene?.blocks).forEach((block) => {
        const type = cleanText(block?.type, "unknown");
        totalBlockCount += 1;
        blockCounts.set(type, (blockCounts.get(type) ?? 0) + 1);
      });
    });

    const topBlockTypes = Array.from(blockCounts.entries())
      .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0], "en-US"))
      .slice(0, 8)
      .map(([type, count]) => ({ type, label: getBlockLabel(type), count }));

    const languages = getSupportedLanguages(data, context.localizationCoverage);
    return {
      chapterCount: toArray(data.chapters).length,
      sceneCount: sceneRecords.length,
      blockCount: totalBlockCount,
      characterCount: getCharacterList(data).length,
      assetCount: getAssetList(data).length,
      dialogueCount: blockCounts.get("dialogue") ?? 0,
      narrationCount: blockCounts.get("narration") ?? 0,
      choiceCount: blockCounts.get("choice") ?? 0,
      endingCount: toCount(context.routeOverview?.metrics?.endingScenes),
      languageCount: languages.length,
      defaultLanguage: getDefaultLanguage(data),
      supportedLanguages: languages,
      topBlockTypes,
      hasAudio: ["music_play", "sfx_play"].some((type) => blockCounts.has(type)),
      hasVideo: blockCounts.has("video_play"),
      hasCharacterStaging: ["character_show", "character_move", "character_hide"].some((type) => blockCounts.has(type)),
      hasParticlesOrEffects: ["particle_effect", "screen_shake", "screen_flash", "screen_fade", "camera_zoom", "camera_pan"].some((type) =>
        blockCounts.has(type)
      ),
      hasChoices: blockCounts.has("choice"),
    };
  }

  function buildProductionTimingSummary(context = {}) {
    const directorSummary = context.directorCueSheet?.summary ?? {};
    const sceneCount = toCount(directorSummary.sceneCount);
    const totalEstimatedSeconds = toCount(directorSummary.totalEstimatedSeconds);
    const averageSceneSeconds =
      directorSummary.averageSceneSeconds !== undefined
        ? toCount(directorSummary.averageSceneSeconds)
        : sceneCount
          ? Math.round(totalEstimatedSeconds / sceneCount)
          : 0;
    const shortSceneCount = toCount(directorSummary.shortSceneCount);
    const longSceneCount = toCount(directorSummary.longSceneCount);
    const silentSceneCount = toCount(directorSummary.silentSceneCount);
    const hasTimingData =
      totalEstimatedSeconds > 0 ||
      shortSceneCount > 0 ||
      longSceneCount > 0 ||
      silentSceneCount > 0 ||
      directorSummary.averageSceneSeconds !== undefined;
    return {
      available: hasTimingData,
      sceneCount,
      totalEstimatedSeconds,
      totalEstimatedLabel: hasTimingData ? formatEstimatedDuration(totalEstimatedSeconds) : "not estimated",
      averageSceneSeconds,
      averageSceneLabel: hasTimingData ? formatEstimatedDuration(averageSceneSeconds) : "not estimated",
      shortSceneCount,
      longSceneCount,
      silentSceneCount,
      reviewSceneCount: shortSceneCount + longSceneCount + silentSceneCount,
      timingRiskLabel: `${shortSceneCount} short / ${longSceneCount} long / ${silentSceneCount} empty`,
    };
  }

  function getAssetSize(asset = {}) {
    return toCount(asset.fileSizeBytes ?? asset.sizeBytes ?? asset.bytes ?? asset.fileSize);
  }

  function buildAssetInventory(data = {}) {
    const assets = getAssetList(data);
    const byType = new Map();
    let missingCount = 0;
    let totalBytes = 0;
    let placeholderCount = 0;

    assets.forEach((asset) => {
      const type = cleanText(asset?.type, "other");
      byType.set(type, (byType.get(type) ?? 0) + 1);
      totalBytes += getAssetSize(asset);
      if (asset?.fileExists === false) {
        missingCount += 1;
      }
      const tags = toArray(asset?.tags).map((tag) => cleanText(tag).toLowerCase());
      const marker = [asset?.name, asset?.fileName, asset?.path, ...tags].join(" ").toLowerCase();
      if (marker.includes("placeholder") || marker.includes("占位")) {
        placeholderCount += 1;
      }
    });

    return {
      totalCount: assets.length,
      missingCount,
      placeholderCount,
      totalBytes,
      totalSizeLabel: formatBytes(totalBytes),
      byType: Array.from(byType.entries())
        .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0], "en-US"))
        .map(([type, count]) => ({ type, count })),
    };
  }

  function formatBytes(bytes = 0) {
    const safeBytes = Math.max(0, Number(bytes) || 0);
    if (safeBytes >= 1024 * 1024 * 1024) {
      return `${(safeBytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
    }
    if (safeBytes >= 1024 * 1024) {
      return `${(safeBytes / (1024 * 1024)).toFixed(1)} MB`;
    }
    if (safeBytes >= 1024) {
      return `${(safeBytes / 1024).toFixed(1)} KB`;
    }
    return `${safeBytes} B`;
  }

  function summarizeChecklist(items = []) {
    const safeItems = toArray(items);
    return {
      totalCount: safeItems.length,
      blockerCount: safeItems.filter((item) => normalizeSeverity(item?.severity) === "blocker").length,
      warningCount: safeItems.filter((item) => normalizeSeverity(item?.severity) === "warn").length,
      readyCount: safeItems.filter((item) => normalizeSeverity(item?.severity) === "good").length,
    };
  }

  function buildDeliverableStatus(id, context = {}) {
    const productionBacklog = context.productionBacklog ?? {};
    const runtimeCapabilityMatrix = context.runtimeCapabilityMatrix ?? {};
    const screenplay = context.screenplay ?? {};
    const directorCueSheet = context.directorCueSheet ?? {};
    const voiceSheet = context.voiceSheet ?? {};
    const localizationCoverage = context.localizationCoverage ?? {};
    const unlockableContentManifest = context.unlockableContentManifest ?? {};
    const exportResult = context.exportResult ?? null;
    const releaseChecklistItems = toArray(context.releaseChecklistItems);

    if (id === "playable_export") {
      if (!exportResult) {
        return { status: "missing", severity: "warn", detail: "No export has been recorded in this editor session." };
      }
      if (toCount(exportResult.missingAssets) > 0) {
        return {
          status: "blocked",
          severity: "blocker",
          detail: `${toCount(exportResult.missingAssets)} missing asset(s) in the latest export.`,
        };
      }
      return {
        status: "ready",
        severity: "good",
        detail: cleanText(exportResult.targetLabel ?? exportResult.target, "Latest playable export is available."),
        href: cleanText(exportResult.publicIndexUrl ?? exportResult.archivePublicUrl ?? exportResult.manifestPublicUrl),
      };
    }

    if (id === "release_control") {
      if (releaseChecklistItems.length || context.finalPublishGate || context.releaseFixOrder) {
        const summary = summarizeChecklist(releaseChecklistItems);
        const severity = summary.blockerCount ? "blocker" : summary.warningCount ? "warn" : "good";
        return {
          status: severity === "good" ? "ready" : "review",
          severity,
          detail: `${summary.blockerCount} blocker / ${summary.warningCount} review / ${summary.readyCount} ready checks.`,
        };
      }
      return { status: "missing", severity: "warn", detail: "Release control data has not been generated." };
    }

    if (id === "production_backlog") {
      const summary = productionBacklog.summary ?? {};
      if (summary.taskCount === undefined) {
        return { status: "missing", severity: "warn", detail: "Production backlog is not available." };
      }
      const severity = summary.blockerCount ? "blocker" : summary.warningCount ? "warn" : "good";
      return {
        status: severity === "good" ? "ready" : "review",
        severity,
        detail: `${summary.taskCount ?? 0} task(s), readiness ${summary.readinessPercent ?? 0}%.`,
      };
    }

    if (id === "runtime_matrix") {
      const summary = runtimeCapabilityMatrix.summary ?? {};
      if (summary.totalBlockCount === undefined) {
        return { status: "missing", severity: "warn", detail: "Runtime matrix is not available." };
      }
      const severity = summary.unknownUsedTypeCount || summary.unsupportedUsedTypeCount ? "blocker" : summary.partialUsedTypeCount ? "warn" : "good";
      return {
        status: severity === "good" ? "ready" : "review",
        severity,
        detail: `${summary.usedTypeCount ?? 0} used block type(s), ${summary.issueCount ?? 0} runtime issue(s).`,
      };
    }

    if (id === "screenplay") {
      const summary = screenplay.summary ?? {};
      if ((summary.lineCount ?? 0) > 0 || (summary.entryCount ?? 0) > 0) {
        return {
          status: "ready",
          severity: "good",
          detail: `${summary.lineCount ?? summary.entryCount ?? 0} script line(s), ${summary.choiceCount ?? 0} choice(s).`,
        };
      }
      return { status: "missing", severity: "warn", detail: "No screenplay lines are available yet." };
    }

    if (id === "director_cues") {
      const summary = directorCueSheet.summary ?? {};
      if (summary.sceneCount === undefined) {
        return { status: "missing", severity: "warn", detail: "Director cue sheet is not available." };
      }
      const severity = summary.blockerCount ? "blocker" : summary.warningCount ? "warn" : "good";
      const timing = buildProductionTimingSummary(context);
      const timingDetail = timing.available ? ` Estimated runtime ${timing.totalEstimatedLabel}; ${timing.timingRiskLabel}.` : "";
      return {
        status: severity === "good" ? "ready" : "review",
        severity,
        detail: `${summary.sceneCount ?? 0} scene(s), ${summary.cueCount ?? 0} cue(s), ${summary.issueCount ?? 0} cue issue(s).${timingDetail}`,
      };
    }

    if (id === "voice_sheet") {
      const summary = voiceSheet.summary ?? {};
      if (summary.lineCount === undefined) {
        return { status: "missing", severity: "warn", detail: "Voice sheet is not available." };
      }
      const severity = summary.missingFileCount || summary.missingAssetCount ? "blocker" : summary.missingVoiceCount ? "warn" : "good";
      return {
        status: severity === "good" ? "ready" : "review",
        severity,
        detail: `${summary.readyLineCount ?? 0}/${summary.lineCount ?? 0} voice line(s) ready.`,
      };
    }

    if (id === "localization_pack") {
      const summary = localizationCoverage.summary ?? {};
      if ((summary.supportedLanguageCount ?? 0) <= 1) {
        return { status: "not_needed", severity: "good", detail: "Single-language project; localization pack is optional." };
      }
      const severity = (summary.missingCount ?? 0) > 0 ? "warn" : "good";
      return {
        status: severity === "good" ? "ready" : "review",
        severity,
        detail: `${summary.readyPercent ?? 0}% localized, ${summary.missingCount ?? 0} missing translation(s).`,
      };
    }

    if (id === "unlockable_manifest") {
      const summary = unlockableContentManifest.summary ?? {};
      if (summary.totalEntryCount === undefined) {
        return { status: "missing", severity: "warn", detail: "Unlockable content manifest is not available." };
      }
      if ((summary.totalEntryCount ?? 0) === 0) {
        return { status: "not_needed", severity: "good", detail: "No EXTRA / replay / archive content is configured yet." };
      }
      const severity = (summary.warningCount ?? 0) > 0 || (summary.missingEntryCount ?? 0) > 0 ? "warn" : "good";
      return {
        status: severity === "good" ? "ready" : "review",
        severity,
        detail: `${summary.readyEntryCount ?? 0}/${summary.totalEntryCount ?? 0} unlockable entries ready, ${summary.reachableEndingCount ?? 0}/${summary.endingCount ?? 0} endings reachable.`,
      };
    }

    if (id === "artifact_integrity") {
      if (!exportResult) {
        return { status: "missing", severity: "warn", detail: "Export first to generate archive and integrity artifacts." };
      }
      if (exportResult.archiveSha256 || exportResult.fileIntegrityStatus || exportResult.archiveChecksumPublicUrl) {
        return {
          status: "ready",
          severity: "good",
          detail: cleanText(exportResult.archiveSizeLabel, "Integrity metadata is available."),
          href: cleanText(exportResult.archiveChecksumPublicUrl ?? exportResult.fileIntegrityReportPublicUrl),
        };
      }
      return { status: "review", severity: "warn", detail: "Latest export exists, but checksum or integrity report is missing." };
    }

    return { status: "unknown", severity: "tip", detail: "No status rule is registered for this deliverable." };
  }

  function buildDeliverables(context = {}) {
    return DELIVERABLE_DEFINITIONS.map((definition) => ({
      ...definition,
      ...buildDeliverableStatus(definition.id, context),
    }));
  }

  function pushRisk(risks, risk = {}) {
    const severity = normalizeSeverity(risk.severity);
    const title = cleanText(risk.title);
    if (!title) {
      return;
    }
    const nextRisk = {
      severity,
      severityLabel: getSeverityLabel(severity),
      area: cleanText(risk.area, "Release"),
      title,
      detail: cleanText(risk.detail ?? risk.description ?? risk.status, "Review this item before distribution."),
      source: cleanText(risk.source ?? risk.location ?? risk.targetLabel, "Project"),
      actionLabel: cleanText(risk.actionLabel ?? risk.action?.label),
    };
    const key = [nextRisk.severity, nextRisk.area, nextRisk.title, nextRisk.source].join("|").toLowerCase();
    if (!risks.some((item) => item.key === key)) {
      risks.push({ ...nextRisk, key });
    }
  }

  function buildRiskRegister(context = {}) {
    const risks = [];
    const validation = context.validation ?? {};
    const errorCount = toCount(validation.errorCount);
    const warningCount = toCount(validation.warningCount);
    if (errorCount > 0) {
      pushRisk(risks, {
        severity: "blocker",
        area: "Validation",
        title: `${errorCount} validation error(s)`,
        detail: "Project validation still has errors that can break preview or export.",
      });
    }
    if (warningCount > 0) {
      pushRisk(risks, {
        severity: "warn",
        area: "Validation",
        title: `${warningCount} validation warning(s)`,
        detail: "Warnings are not always blocking, but should be checked before sharing a release candidate.",
      });
    }

    toArray(context.releaseChecklistItems)
      .filter((item) => normalizeSeverity(item?.severity) !== "good")
      .slice(0, 8)
      .forEach((item) =>
        pushRisk(risks, {
          severity: item.severity,
          area: "Release gate",
          title: item.title,
          detail: item.description ?? item.status,
          source: item.status,
          actionLabel: item.action?.label,
        })
      );

    toArray(context.productionBacklog?.tasks)
      .filter((task) => normalizeSeverity(task?.severity) !== "good")
      .slice(0, 8)
      .forEach((task) =>
        pushRisk(risks, {
          severity: task.severity,
          area: task.areaLabel,
          title: task.title,
          detail: task.detail,
          source: task.source,
          actionLabel: task.action?.label,
        })
      );

    toArray(context.runtimeCapabilityMatrix?.issues)
      .slice(0, 6)
      .forEach((issue) =>
        pushRisk(risks, {
          severity: issue.severity,
          area: "Runtime",
          title: issue.title,
          detail: issue.detail,
          source: toArray(issue.sceneNames).join(" / ") || issue.group,
        })
      );

    toArray(context.localizationCoverage?.issues)
      .slice(0, 4)
      .forEach((issue) =>
        pushRisk(risks, {
          severity: issue.severity,
          area: "Localization",
          title: issue.title,
          detail: issue.detail,
          source: issue.languageLabel,
        })
      );

    toArray(context.unlockableContentManifest?.issues)
      .filter((issue) => normalizeSeverity(issue?.severity) !== "good")
      .slice(0, 4)
      .forEach((issue) =>
        pushRisk(risks, {
          severity: issue.severity,
          area: "Unlockables",
          title: issue.title,
          detail: issue.detail,
          source: issue.groupId ?? issue.assetId ?? issue.sceneId,
        })
      );

    toArray(context.directorCueSheet?.issues)
      .filter((issue) => normalizeSeverity(issue?.severity) === "blocker")
      .slice(0, 4)
      .forEach((issue) =>
        pushRisk(risks, {
          severity: issue.severity,
          area: "Director cues",
          title: issue.title,
          detail: issue.detail,
          source: [issue.chapterName, issue.sceneName].filter(Boolean).join(" / "),
        })
      );

    if (!context.exportResult) {
      pushRisk(risks, {
        severity: "warn",
        area: "Export",
        title: "No latest export record",
        detail: "Export a playable build before calling this a release candidate.",
      });
    } else if (toCount(context.exportResult.missingAssets) > 0) {
      pushRisk(risks, {
        severity: "blocker",
        area: "Export",
        title: "Latest export has missing assets",
        detail: `${toCount(context.exportResult.missingAssets)} missing asset(s): ${toArray(context.exportResult.missingAssetNames).slice(0, 5).join(" / ")}`,
      });
    }

    risks.sort((left, right) => {
      const weight = { blocker: 100, warn: 60, tip: 25, good: 0 };
      return (weight[right.severity] ?? 0) - (weight[left.severity] ?? 0) || left.area.localeCompare(right.area, "en-US");
    });
    return risks.map((risk, index) => ({ ...risk, id: `risk_${index + 1}` }));
  }

  function buildSignoffChecklist(content = {}, context = {}) {
    const productionTiming = buildProductionTimingSummary(context);
    const items = [
      {
        id: "open_build",
        target: "All builds",
        title: "Open the exported build from a clean folder",
        detail: "Confirm the launch path does not depend on the editor workspace.",
        required: true,
      },
      {
        id: "first_scene",
        target: "Story",
        title: "Start from the configured entry scene",
        detail: "The first background, first text line, and first player input should appear correctly.",
        required: content.sceneCount > 0,
      },
      {
        id: "route_smoke",
        target: "Routes",
        title: "Reach at least one ending or stable stop point",
        detail: `${content.endingCount || "No"} ending scene(s) detected; run the shortest route smoke before publishing.`,
        required: content.hasChoices || content.endingCount > 0,
      },
      {
        id: "save_load",
        target: "System",
        title: "Manual save, load, quick-save, and auto-resume smoke",
        detail: "Make sure a player can leave and resume without losing the current line.",
        required: true,
      },
      {
        id: "audio_mix",
        target: "Audio",
        title: "BGM, SFX, voice, and fade timing check",
        detail: "Listen through at least one scene transition that changes music or voice.",
        required: Boolean(content.hasAudio || context.voiceSheet?.summary?.lineCount),
      },
      {
        id: "pacing_runtime",
        target: "Pacing",
        title: "Estimated scene duration and pacing pass",
        detail: productionTiming.available
          ? `Estimated total runtime ${productionTiming.totalEstimatedLabel}; review ${productionTiming.timingRiskLabel}.`
          : "Run the director cue sheet first so the release handoff can include scene duration estimates.",
        required: Boolean(content.sceneCount > 0),
      },
      {
        id: "stage_motion",
        target: "Presentation",
        title: "Character staging, transitions, and camera effects check",
        detail: "Confirm sprites do not jump unexpectedly and transition timing feels intentional.",
        required: Boolean(content.hasCharacterStaging || content.hasParticlesOrEffects),
      },
      {
        id: "video_op_ed",
        target: "Video",
        title: "OP / ED / embedded video playback check",
        detail: "Verify video starts, stops, and returns to story playback on each target platform.",
        required: Boolean(content.hasVideo),
      },
      {
        id: "language_switch",
        target: "Localization",
        title: "Language switch and fallback check",
        detail: `${content.languageCount} language(s) configured; verify fallback text is readable.`,
        required: content.languageCount > 1,
      },
      {
        id: "extras_unlockables",
        target: "EXTRA / Replay",
        title: "Gallery, replay, archive, ending, and achievement smoke",
        detail: "Open the EXTRA / replay surfaces and verify unlocked items, thumbnails, audio replay, and ending entries are readable.",
        required: toCount(context.unlockableContentManifest?.summary?.totalEntryCount) > 0,
      },
      {
        id: "native_runtime",
        target: "Native Runtime",
        title: "Native Runtime smoke on the intended desktop platform",
        detail: "Run the exported native package and verify assets load outside the browser.",
        required: Boolean(context.runtimeCapabilityMatrix?.summary?.nativePartialCount || context.exportResult?.target === "native_runtime"),
      },
    ];

    return items.map((item) => ({
      ...item,
      status: item.required ? "required" : "optional",
      statusLabel: item.required ? "Required" : "Optional",
    }));
  }

  function buildNextActions(risks = [], deliverables = []) {
    const riskActions = risks
      .filter((risk) => risk.severity !== "good")
      .slice(0, 4)
      .map((risk) => ({
        type: "risk",
        title: risk.title,
        detail: `${risk.area} · ${risk.detail}`,
        priority: risk.severity,
      }));
    const missingDeliverables = deliverables
      .filter((item) => ["missing", "blocked", "review"].includes(item.status) && item.severity !== "good")
      .slice(0, 4)
      .map((item) => ({
        type: "deliverable",
        title: `Prepare ${item.label}`,
        detail: item.detail,
        priority: item.severity,
      }));
    return [...riskActions, ...missingDeliverables].slice(0, 6);
  }

  function calculateReadiness(content = {}, assetInventory = {}, risks = [], deliverables = [], context = {}) {
    const blockerCount = risks.filter((risk) => risk.severity === "blocker").length;
    const warningCount = risks.filter((risk) => risk.severity === "warn").length;
    const missingDeliverableCount = deliverables.filter((item) => ["missing", "blocked"].includes(item.status)).length;
    const reviewDeliverableCount = deliverables.filter((item) => item.status === "review").length;
    const regressionPenalty = context.regressionResult ? 0 : 5;
    const contentPenalty = content.sceneCount === 0 || content.blockCount === 0 ? 32 : 0;
    const assetPenalty = assetInventory.missingCount * 8 + assetInventory.placeholderCount * 2;
    return clamp(
      100 -
        blockerCount * 14 -
        warningCount * 5 -
        missingDeliverableCount * 7 -
        reviewDeliverableCount * 3 -
        regressionPenalty -
        contentPenalty -
        assetPenalty,
      0,
      100
    );
  }

  function getReleaseStatus(readinessPercent, risks = [], content = {}) {
    if (content.sceneCount === 0 || content.blockCount === 0 || risks.some((risk) => risk.severity === "blocker")) {
      return "blocked";
    }
    if (readinessPercent >= 92 && !risks.some((risk) => risk.severity === "warn")) {
      return "ready";
    }
    if (readinessPercent >= 72) {
      return "candidate";
    }
    return "review";
  }

  function buildReleaseCandidateManifest(context = {}) {
    const data = context.data ?? {};
    const project = data.project ?? {};
    const resolution = getResolution(data, context);
    const content = buildContentInventory(data, context);
    const assets = buildAssetInventory(data);
    const productionTiming = buildProductionTimingSummary(context);
    const deliverables = buildDeliverables(context);
    const risks = buildRiskRegister(context);
    const signoffChecklist = buildSignoffChecklist(content, context);
    const readinessPercent = calculateReadiness(content, assets, risks, deliverables, context);
    const status = getReleaseStatus(readinessPercent, risks, content);
    const nextActions = buildNextActions(risks, deliverables);
    const releaseChecklist = summarizeChecklist(context.releaseChecklistItems);

    return {
      formatVersion: 1,
      generatedAt: context.generatedAt ?? new Date().toISOString(),
      project: {
        title: cleanText(project.title, "Canvasia Project"),
        releaseVersion: cleanText(context.releaseVersion ?? project.releaseVersion, "1.0.0-preview"),
        editorMode: cleanText(context.editorMode),
        editorModeLabel: cleanText(context.editorModeLabel, "Editor"),
        resolution,
      },
      status,
      statusLabel: getReleaseCandidateStatusDigest({ status, readinessPercent, risks, content }).title,
      readinessPercent,
      content,
      assets,
      releaseChecklist,
      production: {
        taskCount: toCount(context.productionBacklog?.summary?.taskCount),
        blockerCount: toCount(context.productionBacklog?.summary?.blockerCount),
        warningCount: toCount(context.productionBacklog?.summary?.warningCount),
        readinessPercent: toCount(context.productionBacklog?.summary?.readinessPercent),
      },
      productionTiming,
      runtime: {
        usedTypeCount: toCount(context.runtimeCapabilityMatrix?.summary?.usedTypeCount),
        issueCount: toCount(context.runtimeCapabilityMatrix?.summary?.issueCount),
        acceptanceItemCount: toCount(context.runtimeCapabilityMatrix?.acceptance?.summary?.itemCount),
      },
      unlockables: {
        totalEntryCount: toCount(context.unlockableContentManifest?.summary?.totalEntryCount),
        readyEntryCount: toCount(context.unlockableContentManifest?.summary?.readyEntryCount),
        missingEntryCount: toCount(context.unlockableContentManifest?.summary?.missingEntryCount),
        achievementCount: toCount(context.unlockableContentManifest?.summary?.achievementCount),
        endingCount: toCount(context.unlockableContentManifest?.summary?.endingCount),
        reachableEndingCount: toCount(context.unlockableContentManifest?.summary?.reachableEndingCount),
        readinessPercent: toCount(context.unlockableContentManifest?.summary?.readinessPercent),
      },
      latestExport: context.exportResult
        ? {
            target: cleanText(context.exportResult.target),
            targetLabel: cleanText(context.exportResult.targetLabel ?? context.exportResult.target, "Latest export"),
            buildPath: cleanText(context.exportResult.buildPath),
            archiveSizeLabel: cleanText(context.exportResult.archiveSizeLabel),
            missingAssets: toCount(context.exportResult.missingAssets),
            publicUrl: cleanText(context.exportResult.publicIndexUrl ?? context.exportResult.archivePublicUrl ?? context.exportResult.manifestPublicUrl),
          }
        : null,
      deliverables,
      risks,
      signoffChecklist,
      nextActions,
    };
  }

  function getReleaseCandidateStatusDigest(manifest = {}) {
    const status = manifest.status ?? "review";
    const readinessPercent = toCount(manifest.readinessPercent);
    const risks = toArray(manifest.risks);
    const content = manifest.content ?? {};
    const blockerCount = risks.filter((risk) => risk.severity === "blocker").length;
    const warningCount = risks.filter((risk) => risk.severity === "warn").length;

    if (status === "blocked") {
      return {
        status,
        title: content.sceneCount === 0 || content.blockCount === 0 ? "Content not release-ready" : `${blockerCount} blocker(s) before RC`,
        detail: "This project should not be shared as a release candidate until the blocker list is cleared.",
      };
    }
    if (status === "ready") {
      return {
        status,
        title: "Release candidate package is ready",
        detail: "Core checks, deliverables, and signoff items look ready for public preview distribution.",
      };
    }
    if (status === "candidate") {
      return {
        status,
        title: `RC candidate · ${readinessPercent}%`,
        detail: warningCount
          ? "No hard blockers were found, but the release still has review items worth checking before posting."
          : "The package is close to public-preview quality; run the manual signoff checklist before posting.",
      };
    }
    return {
      status,
      title: `Needs release review · ${readinessPercent}%`,
      detail: "The project has enough structure to review, but still needs release-polish work before sharing widely.",
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

  function buildReleaseCandidateMarkdown(manifest = {}, options = {}) {
    const digest = getReleaseCandidateStatusDigest(manifest);
    const projectTitle = cleanText(options.projectTitle ?? manifest.project?.title, "Canvasia Project");
    const generatedAt = cleanText(options.generatedAt ?? manifest.generatedAt);
    const deliverableRows = toArray(manifest.deliverables).map((item) => [
      item.label,
      item.owner,
      item.status,
      getSeverityLabel(item.severity),
      item.detail,
    ]);
    const riskRows = toArray(manifest.risks).map((risk, index) => [
      index + 1,
      risk.severityLabel,
      risk.area,
      risk.title,
      risk.source,
      risk.detail,
      risk.actionLabel,
    ]);
    const signoffRows = toArray(manifest.signoffChecklist).map((item, index) => [
      index + 1,
      item.statusLabel,
      item.target,
      item.title,
      item.detail,
    ]);
    const nextActionRows = toArray(manifest.nextActions).map((item, index) => [
      index + 1,
      getSeverityLabel(item.priority),
      item.title,
      item.detail,
    ]);

    return [
      `# ${projectTitle} Release Candidate Manifest`,
      "",
      generatedAt ? `Generated: ${generatedAt}` : "",
      "",
      `Status: ${digest.title}`,
      "",
      digest.detail,
      "",
      "## Snapshot",
      "",
      buildMarkdownTable(
        [
          "Version",
          "Readiness",
          "Estimated Runtime",
          "Pacing Review",
          "Resolution",
          "Chapters",
          "Scenes",
          "Blocks",
          "Characters",
          "Assets",
          "Languages",
          "Unlockables",
        ],
        [
          [
            manifest.project?.releaseVersion,
            `${manifest.readinessPercent ?? 0}%`,
            manifest.productionTiming?.totalEstimatedLabel ?? "not estimated",
            manifest.productionTiming?.timingRiskLabel ?? "0 short / 0 long / 0 empty",
            `${manifest.project?.resolution?.width ?? 0} x ${manifest.project?.resolution?.height ?? 0}`,
            manifest.content?.chapterCount ?? 0,
            manifest.content?.sceneCount ?? 0,
            manifest.content?.blockCount ?? 0,
            manifest.content?.characterCount ?? 0,
            manifest.assets?.totalCount ?? 0,
            toArray(manifest.content?.supportedLanguages).join(" / "),
            `${manifest.unlockables?.readyEntryCount ?? 0}/${manifest.unlockables?.totalEntryCount ?? 0}`,
          ],
        ]
      ),
      "",
      "## Deliverables",
      "",
      buildMarkdownTable(["Deliverable", "Owner", "Status", "Severity", "Detail"], deliverableRows) || "No deliverables were generated.",
      "",
      "## Risk Register",
      "",
      buildMarkdownTable(["#", "Severity", "Area", "Risk", "Source", "Detail", "Action"], riskRows) || "No release risks were detected.",
      "",
      "## Manual Signoff",
      "",
      buildMarkdownTable(["#", "Required", "Target", "Check", "Detail"], signoffRows),
      "",
      "## Next Actions",
      "",
      buildMarkdownTable(["#", "Priority", "Action", "Detail"], nextActionRows) || "No next action is required.",
      "",
    ].join("\n");
  }

  function buildReleaseCandidateCsv(manifest = {}) {
    const timingRows = manifest.productionTiming
      ? [
          [
            "timing",
            "estimated_runtime",
            "Estimated runtime",
            "Pacing",
            manifest.productionTiming.available ? "ready" : "missing",
            manifest.productionTiming.totalEstimatedLabel,
            manifest.productionTiming.timingRiskLabel,
          ],
          [
            "timing",
            "average_scene",
            "Average scene duration",
            "Pacing",
            manifest.productionTiming.available ? "ready" : "missing",
            manifest.productionTiming.averageSceneLabel,
            `${manifest.productionTiming.reviewSceneCount ?? 0} scene(s) should be reviewed for pacing.`,
          ],
        ]
      : [];
    const deliverableRows = toArray(manifest.deliverables).map((item) => [
      "deliverable",
      item.id,
      item.label,
      item.owner,
      item.status,
      getSeverityLabel(item.severity),
      item.detail,
    ]);
    const riskRows = toArray(manifest.risks).map((risk) => [
      "risk",
      risk.id,
      risk.title,
      risk.area,
      risk.severity,
      risk.severityLabel,
      risk.detail,
    ]);
    const signoffRows = toArray(manifest.signoffChecklist).map((item) => [
      "signoff",
      item.id,
      item.title,
      item.target,
      item.status,
      item.statusLabel,
      item.detail,
    ]);
    return `\uFEFF${buildCsv(["kind", "id", "title", "owner_or_target", "status", "label", "detail"], [
      ...timingRows,
      ...deliverableRows,
      ...riskRows,
      ...signoffRows,
    ])}\n`;
  }

  function fallbackEscapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderReleaseCandidateManifestPanel(manifest = {}, options = {}) {
    const escapeHtml = typeof options.escapeHtml === "function" ? options.escapeHtml : fallbackEscapeHtml;
    const renderMetric =
      typeof options.renderRouteMetricCard === "function"
        ? options.renderRouteMetricCard
        : (label, value, hint) => `<div class="route-metric-card"><b>${escapeHtml(value)}</b><span>${escapeHtml(label)}</span><small>${escapeHtml(hint)}</small></div>`;
    const renderEmpty =
      typeof options.renderEmpty === "function"
        ? options.renderEmpty
        : (message) => `<p class="helper-text">${escapeHtml(message)}</p>`;
    const getToneClass = typeof options.getToneClass === "function" ? options.getToneClass : () => "";
    const digest = getReleaseCandidateStatusDigest(manifest);
    const topRisks = toArray(manifest.risks).slice(0, 4);
    const allDeliverables = toArray(manifest.deliverables);
    const deliverables = allDeliverables
      .slice()
      .sort((left, right) => getSeverityWeight(right.severity) - getSeverityWeight(left.severity))
      .slice(0, 5);
    const signoffItems = toArray(manifest.signoffChecklist).filter((item) => item.required).slice(0, 5);

    return `
      <article class="detail-card preview-sprint-panel" data-inspection-section="release-candidate">
        <div class="panel-heading">
          <h2>Release Candidate Manifest</h2>
          <span class="badge badge-soft ${getToneClass(digest.status)}">${escapeHtml(digest.title)}</span>
        </div>
        <p class="helper-text">${escapeHtml(digest.detail)} This manifest turns the current editor state into a handoff sheet for testers, translators, runtime checks, and public-preview packaging.</p>
        <div class="preview-sprint-metrics">
          ${renderMetric("Readiness", `${manifest.readinessPercent ?? 0}%`, "release candidate estimate")}
          ${renderMetric(
            "Estimated Runtime",
            manifest.productionTiming?.totalEstimatedLabel ?? "not estimated",
            manifest.productionTiming?.timingRiskLabel ?? "run director cues first"
          )}
          ${renderMetric("Scenes / Blocks", `${manifest.content?.sceneCount ?? 0} / ${manifest.content?.blockCount ?? 0}`, "playable content inventory")}
          ${renderMetric("Deliverables", `${allDeliverables.filter((item) => item.severity === "good").length}/${allDeliverables.length}`, "ready release artifacts")}
          ${renderMetric("Risks", `${topRisks.length ? manifest.risks.length : 0}`, "blockers and review items")}
        </div>
        <div class="detail-actions">
          <button class="toolbar-button toolbar-button-primary" data-action="export-release-candidate-manifest-markdown">
            Export RC manifest
          </button>
          <button class="toolbar-button" data-action="export-release-candidate-manifest-csv">
            Export RC CSV
          </button>
          <button class="toolbar-button" data-action="run-project-inspection">
            Refresh inspection
          </button>
        </div>
        ${
          topRisks.length > 0
            ? `
              <div class="preview-sprint-grid">
                ${topRisks
                  .map(
                    (risk) => `
                      <article class="preview-sprint-card is-${risk.severity === "blocker" ? "danger" : risk.severity === "warn" ? "warn" : "soft"}">
                        <div class="preview-sprint-head">
                          <strong>${escapeHtml(risk.title)}</strong>
                          <span class="issue-tag ${risk.severity === "blocker" ? "danger-text" : risk.severity === "warn" ? "warn-text" : ""}">
                            ${escapeHtml(`${risk.severityLabel} · ${risk.area}`)}
                          </span>
                        </div>
                        <p>${escapeHtml(risk.source)}</p>
                        <div class="helper-text">${escapeHtml(risk.detail)}</div>
                      </article>
                    `
                  )
                  .join("")}
              </div>
            `
            : deliverables.length > 0
              ? `
                <div class="list-stack compact-stack">
                  ${deliverables
                    .map(
                      (item) => `
                        <div class="route-testing-item">
                          <div>
                            <b>${escapeHtml(item.label)}</b>
                            <span>${escapeHtml(`${item.owner} · ${item.detail}`)}</span>
                          </div>
                          <span>${escapeHtml(item.status)}</span>
                        </div>
                      `
                    )
                    .join("")}
                </div>
              `
              : renderEmpty("No release candidate information is available yet.")
        }
        ${
          signoffItems.length > 0
            ? `
              <div class="section-subhead">
                <div>
                  <h3>Manual signoff checklist</h3>
                  <p>These are the human checks that should happen after export, even when automated checks pass.</p>
                </div>
                <span class="issue-tag">${escapeHtml(`${signoffItems.length} required`)}</span>
              </div>
              <div class="list-stack compact-stack">
                ${signoffItems
                  .map(
                    (item) => `
                      <div class="route-testing-item">
                        <div>
                          <b>${escapeHtml(item.title)}</b>
                          <span>${escapeHtml(`${item.target} · ${item.detail}`)}</span>
                        </div>
                        <span>${escapeHtml(item.statusLabel)}</span>
                      </div>
                    `
                  )
                  .join("")}
              </div>
            `
            : ""
        }
      </article>
    `;
  }

  global.CanvasiaEditorReleaseCandidateManifest = Object.freeze({
    buildReleaseCandidateManifest,
    getReleaseCandidateStatusDigest,
    buildReleaseCandidateMarkdown,
    buildReleaseCandidateCsv,
    renderReleaseCandidateManifestPanel,
  });
})(typeof window !== "undefined" ? window : globalThis);
