(function attachUnlockableContentManifestTools(global) {
  const GROUP_DEFINITIONS = Object.freeze([
    {
      id: "extra_cg",
      label: "CG 图鉴",
      unlockRule: "CG 素材被展示或打包后进入图鉴。",
      detail: "会出现在 EXTRA / 回想馆里的 CG 图片。",
    },
    {
      id: "music_room",
      label: "音乐回想",
      unlockRule: "BGM 被播放或打包后进入音乐回想。",
      detail: "玩家通关或发现后可回听的背景音乐。",
    },
    {
      id: "voice_replay",
      label: "语音回听",
      unlockRule: "绑定语音的台词或旁白可进入回听。",
      detail: "与剧情文本绑定的语音片段。",
    },
    {
      id: "character_archive",
      label: "角色图鉴",
      unlockRule: "角色在剧情中登场后进入图鉴。",
      detail: "角色资料与可展示立绘素材。",
    },
    {
      id: "location_archive",
      label: "地点图鉴",
      unlockRule: "背景或 3D 场景被访问后进入图鉴。",
      detail: "剧情中到访过的背景、房间和 3D 场景。",
    },
    {
      id: "narration_archive",
      label: "旁白档案",
      unlockRule: "重要旁白可作为剧情记忆解锁。",
      detail: "可回顾的旁白与故事记忆条目。",
    },
    {
      id: "relationship_archive",
      label: "关系图鉴",
      unlockRule: "两个角色同场出现后生成关系条目。",
      detail: "从同场剧情推断出的角色关系组合。",
    },
    {
      id: "chapter_replay",
      label: "章节回放",
      unlockRule: "章节开始或通关后可进入回放。",
      detail: "按章节整理的回放入口。",
    },
    {
      id: "ending_collection",
      label: "结局收集",
      unlockRule: "抵达结局路线后解锁。",
      detail: "可达与暂不可达的结局路线。",
    },
    {
      id: "achievements",
      label: "成就集合",
      unlockRule: "由路线、图鉴、音频、角色和结局里程碑解锁。",
      detail: "根据当前项目自动生成的成就覆盖。",
    },
  ]);

  const ASSET_TYPE_LABELS = Object.freeze({
    background: "背景",
    sprite: "立绘",
    cg: "CG",
    bgm: "BGM",
    sfx: "音效",
    voice: "语音",
    video: "视频",
    ui: "UI",
    font: "字体",
    live2d: "Live2D",
    model3d: "3D 模型",
    scene3d: "3D 场景",
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

  function percentage(done, total) {
    if (!total) {
      return 0;
    }
    return Math.round((done / total) * 100);
  }

  function formatCsvCell(value) {
    return `"${String(value ?? "").replace(/"/g, '""')}"`;
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
      const id = cleanText(item?.[idField]);
      if (id) {
        result.set(id, item);
      }
    });
    return result;
  }

  function getAssetList(data = {}) {
    if (Array.isArray(data.assetList)) {
      return data.assetList;
    }
    if (Array.isArray(data.assets?.assets)) {
      return data.assets.assets;
    }
    return Array.isArray(data.assets) ? data.assets : [];
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

  function getChapterList(data = {}) {
    return Array.isArray(data.chapters) ? data.chapters : [];
  }

  function buildAssetMap(data = {}) {
    const map = buildCollectionMap(data.assetsById);
    getAssetList(data).forEach((asset) => {
      const id = cleanText(asset?.id);
      if (id) {
        map.set(id, asset);
      }
    });
    return map;
  }

  function buildCharacterMap(data = {}) {
    const map = buildCollectionMap(data.charactersById);
    getCharacterList(data).forEach((character) => {
      const id = cleanText(character?.id);
      if (id) {
        map.set(id, character);
      }
    });
    return map;
  }

  function buildSceneMap(data = {}) {
    const map = buildCollectionMap(data.scenesById);
    toArray(data.scenes).forEach((scene) => {
      const id = cleanText(scene?.id);
      if (id) {
        map.set(id, scene);
      }
    });
    getChapterList(data).forEach((chapter) => {
      toArray(chapter?.scenes).forEach((scene) => {
        const id = cleanText(scene?.id);
        if (id) {
          map.set(id, scene);
        }
      });
    });
    return map;
  }

  function getSceneRecords(data = {}) {
    const sceneMap = buildSceneMap(data);
    const records = [];
    const seen = new Set();

    getChapterList(data).forEach((chapter, chapterIndex) => {
      const chapterId = cleanText(chapter?.id ?? chapter?.chapterId, `chapter_${chapterIndex + 1}`);
      const chapterName = cleanText(chapter?.name ?? chapter?.title, `Chapter ${chapterIndex + 1}`);
      const directScenes = toArray(chapter?.scenes);
      const orderedScenes = toArray(chapter?.sceneOrder)
        .map((sceneId) => sceneMap.get(cleanText(sceneId)))
        .filter(Boolean);
      const scenes = directScenes.length ? directScenes : orderedScenes;
      scenes.forEach((scene, sceneIndex) => {
        const sceneId = cleanText(scene?.id);
        if (!sceneId || seen.has(sceneId)) {
          return;
        }
        seen.add(sceneId);
        records.push({ scene, sceneId, sceneIndex, chapterId, chapterName, chapterIndex });
      });
    });

    toArray(data.scenes).forEach((scene, sceneIndex) => {
      const sceneId = cleanText(scene?.id);
      if (!sceneId || seen.has(sceneId)) {
        return;
      }
      seen.add(sceneId);
      records.push({
        scene,
        sceneId,
        sceneIndex,
        chapterId: cleanText(scene?.chapterId),
        chapterName: "Unchaptered",
        chapterIndex: 9999,
      });
    });

    return records.sort((left, right) => {
      if (left.chapterIndex !== right.chapterIndex) {
        return left.chapterIndex - right.chapterIndex;
      }
      return left.sceneIndex - right.sceneIndex;
    });
  }

  function collectBlocks(data = {}) {
    const records = [];
    getSceneRecords(data).forEach((record) => {
      toArray(record.scene?.blocks).forEach((block, blockIndex) => {
        records.push({ ...record, block, blockIndex });
      });
    });
    return records;
  }

  function assetReady(asset = {}) {
    if (!asset || typeof asset !== "object") {
      return false;
    }
    if (asset.fileExists === false || asset.missing === true) {
      return false;
    }
    if (asset.fileExists === true || asset.ready === true) {
      return true;
    }
    return Boolean(asset.path || asset.url || asset.fileName || asset.relativePath || asset.src);
  }

  function getAssetName(asset = {}, fallback = "Untitled asset") {
    return cleanText(asset.name ?? asset.title ?? asset.fileName ?? asset.id, fallback);
  }

  function getAssetTypeLabel(type = "") {
    return ASSET_TYPE_LABELS[type] ?? cleanText(type, "Asset");
  }

  function getAssetUsageCount(assetId, data = {}) {
    if (!assetId) {
      return 0;
    }
    const usage = data.assetUsage;
    if (!usage) {
      return 0;
    }
    if (typeof usage.get === "function") {
      return toArray(usage.get(assetId)).length;
    }
    return toArray(usage[assetId]).length;
  }

  function getCharacterName(character = {}, fallback = "Unnamed character") {
    return cleanText(character.name ?? character.displayName ?? character.label ?? character.id, fallback);
  }

  function getCharacterPrimaryAssetIds(character = {}) {
    return [
      character.defaultSpriteId,
      character.defaultAssetId,
      character.spriteAssetId,
      character.avatarAssetId,
      character.presentation?.defaultSpriteId,
      character.presentation?.defaultAssetId,
      character.presentation?.avatarAssetId,
      ...toArray(character.expressions).map((expression) => expression?.assetId ?? expression?.spriteAssetId),
      ...toArray(character.presentation?.expressions).map((expression) => expression?.assetId ?? expression?.spriteAssetId),
    ]
      .map((assetId) => cleanText(assetId))
      .filter(Boolean);
  }

  function getBlockAssetId(block = {}) {
    return cleanText(
      block.assetId ??
        block.backgroundAssetId ??
        block.imageAssetId ??
        block.cgAssetId ??
        block.musicAssetId ??
        block.bgmAssetId ??
        block.voiceAssetId ??
        block.videoAssetId ??
        block.scene3dAssetId
    );
  }

  function getBlockSpeakerId(block = {}) {
    return cleanText(block.characterId ?? block.speakerId ?? block.character ?? block.speaker);
  }

  function makeIssue(severity, code, title, detail, context = {}) {
    return { severity, code, title, detail, ...context };
  }

  function makeEntry({ id, title, status = "ready", detail = "", source = "", meta = {}, issues = [] }) {
    return {
      id: cleanText(id, title),
      title: cleanText(title, "Untitled"),
      status,
      detail: cleanText(detail),
      source: cleanText(source),
      meta,
      issues,
    };
  }

  function buildGroup(id, entries = [], issues = []) {
    const definition = GROUP_DEFINITIONS.find((item) => item.id === id) ?? {
      id,
      label: id,
      unlockRule: "Project-defined unlock rule.",
      detail: "",
    };
    const totalCount = entries.length;
    const readyCount = entries.filter((entry) => entry.status === "ready").length;
    const missingCount = entries.filter((entry) => entry.status === "missing" || entry.status === "warn").length;
    return {
      ...definition,
      totalCount,
      readyCount,
      missingCount,
      readinessPercent: percentage(readyCount, totalCount),
      status: totalCount === 0 ? "empty" : missingCount > 0 ? "warn" : "ready",
      entries,
      issues,
    };
  }

  function collectAssetGroup(data = {}, type, groupId, issues) {
    const entries = getAssetList(data)
      .filter((asset) => cleanText(asset?.type) === type)
      .map((asset) => {
        const id = cleanText(asset?.id);
        const ready = assetReady(asset);
        const usageCount = getAssetUsageCount(id, data);
        const entryIssues = [];
        if (!ready) {
          const issue = makeIssue(
            "warn",
            "unlockable_asset_missing",
          `${getAssetTypeLabel(type)} 文件缺失`,
          `${getAssetName(asset)} 已进入可解锁内容清单，但当前没有可用文件。`,
            { groupId, assetId: id }
          );
          entryIssues.push(issue);
          issues.push(issue);
        }
        return makeEntry({
          id,
          title: getAssetName(asset),
          status: ready ? "ready" : "missing",
          detail: `${getAssetTypeLabel(type)} · 引用 ${usageCount} 次`,
          source: cleanText(asset.path ?? asset.fileName ?? asset.url),
          meta: { type, usageCount },
          issues: entryIssues,
        });
      });
    return buildGroup(groupId, entries, entries.flatMap((entry) => entry.issues));
  }

  function collectVoiceReplayEntries(data = {}, issues) {
    const assetMap = buildAssetMap(data);
    const entries = [];
    collectBlocks(data).forEach((record) => {
      const voiceAssetId = cleanText(record.block?.voiceAssetId ?? record.block?.voiceId ?? record.block?.voice);
      if (!voiceAssetId) {
        return;
      }
      const asset = assetMap.get(voiceAssetId);
      const ready = assetReady(asset);
      const text = cleanText(record.block?.text ?? record.block?.line ?? record.block?.content, "Voice line");
      const entryIssues = [];
      if (!ready) {
        const issue = makeIssue(
          "warn",
          "unlockable_voice_missing",
          "语音回听文件缺失",
          `${record.chapterName} / ${cleanText(record.scene?.name, record.sceneId)} 有语音回听条目，但语音文件不可用。`,
          { groupId: "voice_replay", sceneId: record.sceneId, blockId: record.block?.id, assetId: voiceAssetId }
        );
        entryIssues.push(issue);
        issues.push(issue);
      }
      entries.push(
        makeEntry({
          id: `${record.sceneId}:${record.block?.id ?? record.blockIndex}:voice`,
          title: text.length > 42 ? `${text.slice(0, 42)}...` : text,
          status: ready ? "ready" : "missing",
          detail: `${record.chapterName} · ${cleanText(record.scene?.name, record.sceneId)}`,
          source: getAssetName(asset ?? {}, voiceAssetId),
          meta: { voiceAssetId, sceneId: record.sceneId, blockId: record.block?.id },
          issues: entryIssues,
        })
      );
    });
    return buildGroup("voice_replay", entries, entries.flatMap((entry) => entry.issues));
  }

  function collectCharacterArchiveEntries(data = {}, issues) {
    const assetMap = buildAssetMap(data);
    const characterSeenInStory = new Set();
    collectBlocks(data).forEach(({ block }) => {
      const speakerId = getBlockSpeakerId(block);
      if (speakerId) {
        characterSeenInStory.add(speakerId);
      }
    });
    const entries = getCharacterList(data).map((character) => {
      const characterId = cleanText(character?.id);
      const assetIds = getCharacterPrimaryAssetIds(character);
      const readyAssetCount = assetIds.filter((assetId) => assetReady(assetMap.get(assetId))).length;
      const ready = assetIds.length ? readyAssetCount > 0 : false;
      const used = characterSeenInStory.has(characterId) || toArray(character?.sceneIds).length > 0;
      const entryIssues = [];
      if (!ready) {
        const issue = makeIssue(
          "warn",
          "unlockable_character_visual_missing",
          "角色图鉴视觉素材缺失",
          `${getCharacterName(character)} 没有可用于图鉴展示的立绘或头像素材。`,
          { groupId: "character_archive", characterId }
        );
        entryIssues.push(issue);
        issues.push(issue);
      }
      return makeEntry({
        id: characterId,
        title: getCharacterName(character),
        status: ready ? "ready" : "missing",
        detail: `${used ? "已在剧情中登场" : "暂未使用"} · 视觉素材 ${readyAssetCount}/${Math.max(assetIds.length, 1)} 可用`,
        source: assetIds.join(", "),
        meta: { characterId, used, readyAssetCount, visualAssetCount: assetIds.length },
        issues: entryIssues,
      });
    });
    return buildGroup("character_archive", entries, entries.flatMap((entry) => entry.issues));
  }

  function collectLocationEntries(data = {}, issues) {
    const assetMap = buildAssetMap(data);
    const byAssetId = new Map();
    collectBlocks(data).forEach((record) => {
      const type = cleanText(record.block?.type);
      if (!["background", "scene3d", "video_play"].includes(type)) {
        return;
      }
      const assetId = getBlockAssetId(record.block);
      if (!assetId) {
        return;
      }
      const existing = byAssetId.get(assetId) ?? {
        assetId,
        scenes: new Set(),
        firstRecord: record,
      };
      existing.scenes.add(cleanText(record.scene?.name, record.sceneId));
      byAssetId.set(assetId, existing);
    });

    const entries = Array.from(byAssetId.values()).map((record) => {
      const asset = assetMap.get(record.assetId);
      const ready = assetReady(asset);
      const entryIssues = [];
      if (!ready) {
        const issue = makeIssue(
          "warn",
          "unlockable_location_asset_missing",
          "地点图鉴素材缺失",
          `${getAssetName(asset ?? {}, record.assetId)} 已作为地点使用，但当前没有可用文件。`,
          { groupId: "location_archive", assetId: record.assetId }
        );
        entryIssues.push(issue);
        issues.push(issue);
      }
      return makeEntry({
        id: record.assetId,
        title: getAssetName(asset ?? {}, record.assetId),
        status: ready ? "ready" : "missing",
        detail: `${record.scenes.size} 个场景 · ${getAssetTypeLabel(asset?.type)}`,
        source: Array.from(record.scenes).slice(0, 3).join(" / "),
        meta: { assetId: record.assetId, sceneCount: record.scenes.size },
        issues: entryIssues,
      });
    });
    return buildGroup("location_archive", entries, entries.flatMap((entry) => entry.issues));
  }

  function collectNarrationEntries(data = {}) {
    const entries = collectBlocks(data)
      .filter((record) => cleanText(record.block?.type) === "narration" && cleanText(record.block?.text ?? record.block?.content))
      .map((record) => {
        const text = cleanText(record.block?.text ?? record.block?.content);
        return makeEntry({
          id: `${record.sceneId}:${record.block?.id ?? record.blockIndex}:narration`,
          title: text.length > 46 ? `${text.slice(0, 46)}...` : text,
          status: "ready",
          detail: `${record.chapterName} · ${cleanText(record.scene?.name, record.sceneId)}`,
          source: text,
          meta: { sceneId: record.sceneId, blockId: record.block?.id },
        });
      });
    return buildGroup("narration_archive", entries);
  }

  function collectRelationshipEntries(data = {}) {
    const characterMap = buildCharacterMap(data);
    const pairs = new Map();
    getSceneRecords(data).forEach((record) => {
      const speakers = new Set();
      toArray(record.scene?.blocks).forEach((block) => {
        const speakerId = getBlockSpeakerId(block);
        if (speakerId) {
          speakers.add(speakerId);
        }
      });
      const ids = Array.from(speakers).sort();
      ids.forEach((leftId, leftIndex) => {
        ids.slice(leftIndex + 1).forEach((rightId) => {
          const pairId = `${leftId}__${rightId}`;
          const pair = pairs.get(pairId) ?? { leftId, rightId, scenes: new Set() };
          pair.scenes.add(cleanText(record.scene?.name, record.sceneId));
          pairs.set(pairId, pair);
        });
      });
    });
    const entries = Array.from(pairs.values()).map((pair) => {
      const left = characterMap.get(pair.leftId);
      const right = characterMap.get(pair.rightId);
      return makeEntry({
        id: `${pair.leftId}:${pair.rightId}`,
        title: `${getCharacterName(left ?? {}, pair.leftId)} / ${getCharacterName(right ?? {}, pair.rightId)}`,
        status: "ready",
        detail: `同场 ${pair.scenes.size} 次`,
        source: Array.from(pair.scenes).slice(0, 3).join(" / "),
        meta: { leftId: pair.leftId, rightId: pair.rightId, sceneCount: pair.scenes.size },
      });
    });
    return buildGroup("relationship_archive", entries);
  }

  function collectChapterReplayEntries(data = {}) {
    const entries = getChapterList(data).map((chapter, index) => {
      const sceneCount = toArray(chapter?.scenes).length || toArray(chapter?.sceneOrder).length;
      return makeEntry({
        id: cleanText(chapter?.id, `chapter_${index + 1}`),
        title: cleanText(chapter?.name ?? chapter?.title, `第 ${index + 1} 章`),
        status: sceneCount > 0 ? "ready" : "warn",
        detail: `${sceneCount} 个场景`,
        source: cleanText(chapter?.description ?? chapter?.summary),
        meta: { sceneCount },
      });
    });
    return buildGroup("chapter_replay", entries);
  }

  function collectEndingEntries(routeOverview = {}, issues) {
    const endingPaths = toArray(routeOverview?.endingPaths);
    const candidateEndings = endingPaths.length
      ? endingPaths
      : toArray(routeOverview?.endings).map((ending) => ({ ...ending, reachable: ending.reachable ?? true }));
    const entries = candidateEndings.map((ending, index) => {
      const reachable = ending.reachable !== false && ending.status !== "unreachable";
      const title = cleanText(ending.label ?? ending.name ?? ending.sceneName ?? ending.endingName, `Ending ${index + 1}`);
      const entryIssues = [];
      if (!reachable) {
        const issue = makeIssue(
          "warn",
          "unlockable_ending_unreachable",
          "结局当前不可达",
          `${title} 已列为结局，但路线分析暂时无法从入口场景抵达。`,
          { groupId: "ending_collection", sceneId: ending.sceneId ?? ending.id }
        );
        entryIssues.push(issue);
        issues.push(issue);
      }
      return makeEntry({
        id: cleanText(ending.id ?? ending.sceneId, `ending_${index + 1}`),
        title,
        status: reachable ? "ready" : "warn",
        detail: reachable ? "路线图可抵达" : "入口场景暂不可达",
        source: cleanText(ending.pathLabel ?? ending.routeLabel ?? ending.chapterName),
        meta: { reachable },
        issues: entryIssues,
      });
    });
    return buildGroup("ending_collection", entries, entries.flatMap((entry) => entry.issues));
  }

  function buildAchievementEntries(data = {}, routeOverview = {}, groups = []) {
    const metrics = routeOverview?.metrics ?? {};
    const activeGroups = groups.filter((group) => group.id !== "achievements" && group.totalCount > 0);
    const entries = [
      makeEntry({
        id: "story_start",
        title: "首次进入剧情",
        status: toCount(metrics.sceneCount ?? metrics.totalScenes ?? getSceneRecords(data).length) > 0 ? "ready" : "warn",
        detail: "玩家开始阅读项目。",
      }),
      makeEntry({
        id: "first_choice",
        title: "首次做出选择",
        status: collectBlocks(data).some((record) => cleanText(record.block?.type) === "choice") ? "ready" : "warn",
        detail: "玩家遇到至少一个选项分支。",
      }),
      ...activeGroups.map((group) =>
        makeEntry({
          id: `complete_${group.id}`,
          title: `完成${group.label}`,
          status: group.status === "ready" ? "ready" : "warn",
          detail: `${group.readyCount}/${group.totalCount} 个条目可用。`,
          meta: { groupId: group.id },
        })
      ),
    ];
    return buildGroup("achievements", entries);
  }

  function buildUnlockableContentManifest(data = {}, options = {}) {
    const routeOverview = options.routeOverview ?? {};
    const issues = [];
    const groups = [
      collectAssetGroup(data, "cg", "extra_cg", issues),
      collectAssetGroup(data, "bgm", "music_room", issues),
      collectVoiceReplayEntries(data, issues),
      collectCharacterArchiveEntries(data, issues),
      collectLocationEntries(data, issues),
      collectNarrationEntries(data),
      collectRelationshipEntries(data),
      collectChapterReplayEntries(data),
      collectEndingEntries(routeOverview, issues),
    ];
    groups.push(buildAchievementEntries(data, routeOverview, groups));

    if (!groups.some((group) => group.totalCount > 0)) {
      issues.push(
        makeIssue(
          "tip",
          "unlockable_content_empty",
          "No unlockable content yet",
          "当前还没有足够的图鉴、回想或成就内容。建议先补 CG、BGM、角色、旁白、结局或语音台词。",
          { groupId: "overview" }
        )
      );
    }

    const totalEntryCount = groups.reduce((sum, group) => sum + group.totalCount, 0);
    const readyEntryCount = groups.reduce((sum, group) => sum + group.readyCount, 0);
    const missingEntryCount = groups.reduce((sum, group) => sum + group.missingCount, 0);
    const warningCount = issues.filter((issue) => issue.severity === "warn").length;
    const tipCount = issues.filter((issue) => issue.severity === "tip").length;
    const endingGroup = groups.find((group) => group.id === "ending_collection");

    return {
      projectTitle: cleanText(data.project?.title ?? data.projectTitle, "Canvasia Project"),
      generatedAt: new Date().toISOString(),
      groups,
      issues,
      summary: {
        groupCount: groups.length,
        activeGroupCount: groups.filter((group) => group.totalCount > 0).length,
        totalEntryCount,
        readyEntryCount,
        missingEntryCount,
        achievementCount: groups.find((group) => group.id === "achievements")?.totalCount ?? 0,
        endingCount: endingGroup?.totalCount ?? 0,
        reachableEndingCount: endingGroup?.readyCount ?? 0,
        warningCount,
        tipCount,
        readinessPercent: percentage(readyEntryCount, totalEntryCount),
      },
    };
  }

  function getUnlockableContentStatusDigest(manifest = {}) {
    const summary = manifest.summary ?? {};
    if (!summary.totalEntryCount) {
      return {
        status: "soft",
        title: "可解锁内容尚未成型",
        detail: "当前项目还没有生成图鉴、回想、档案或成就内容。",
      };
    }
    if (summary.warningCount > 0 || summary.missingEntryCount > 0) {
      return {
        status: "warn",
        title: `${summary.warningCount || summary.missingEntryCount} 个可解锁内容缺口`,
        detail: "部分图鉴、档案、回听或结局条目需要补文件或修路线后再发布。",
      };
    }
    return {
      status: "ready",
      title: "可解锁内容已就绪",
      detail: "图鉴、回想、档案、结局和成就覆盖看起来已经可以发布。",
    };
  }

  function buildUnlockableContentMarkdown(manifest = {}, options = {}) {
    const generatedAt = options.generatedAt || manifest.generatedAt || new Date().toISOString();
    const summary = manifest.summary ?? {};
    const lines = [
      `# ${manifest.projectTitle || "Canvasia Project"} 可解锁内容清单`,
      "",
      `Generated: ${generatedAt}`,
      "",
      "## 总览",
      "",
      `- 已启用分组：${summary.activeGroupCount ?? 0}/${summary.groupCount ?? 0}`,
      `- 条目就绪：${summary.readyEntryCount ?? 0}/${summary.totalEntryCount ?? 0}`,
      `- 缺失或需复查条目：${summary.missingEntryCount ?? 0}`,
      `- 成就数量：${summary.achievementCount ?? 0}`,
      `- 可达结局：${summary.reachableEndingCount ?? 0}/${summary.endingCount ?? 0}`,
      `- 就绪度：${summary.readinessPercent ?? 0}%`,
      "",
      "## 分组",
      "",
      "| 分组 | 条目 | 就绪 | 状态 | 解锁规则 |",
      "| --- | ---: | ---: | --- | --- |",
      ...toArray(manifest.groups).map(
        (group) =>
          `| ${group.label} | ${group.totalCount} | ${group.readyCount} | ${group.status} | ${group.unlockRule} |`
      ),
      "",
    ];

    if (toArray(manifest.issues).length) {
      lines.push("## 问题", "");
      toArray(manifest.issues).forEach((issue) => {
        lines.push(`- [${issue.severity}] ${issue.title}: ${issue.detail}`);
      });
      lines.push("");
    }

    toArray(manifest.groups)
      .filter((group) => group.totalCount > 0)
      .forEach((group) => {
        lines.push(`## ${group.label}`, "", group.detail, "", "| Entry | Status | Detail | Source |", "| --- | --- | --- | --- |");
        group.entries.slice(0, 80).forEach((entry) => {
          lines.push(`| ${entry.title} | ${entry.status} | ${entry.detail} | ${entry.source || "-"} |`);
        });
        if (group.entries.length > 80) {
        lines.push(`| ... | ... | 还有 ${group.entries.length - 80} 个条目 | - |`);
        }
        lines.push("");
      });

    return lines.join("\n");
  }

  function buildUnlockableContentCsv(manifest = {}) {
    const rows = [["group_id", "group_label", "entry_id", "entry_title", "status", "detail", "source"]];
    toArray(manifest.groups).forEach((group) => {
      if (!group.entries?.length) {
        rows.push([group.id, group.label, "", "", "empty", group.detail, ""]);
        return;
      }
      group.entries.forEach((entry) => {
        rows.push([group.id, group.label, entry.id, entry.title, entry.status, entry.detail, entry.source]);
      });
    });
    return `\ufeff${rows.map((row) => row.map(formatCsvCell).join(",")).join("\n")}`;
  }

  function getToneClass(status = "") {
    if (status === "warn") {
      return "warn-text";
    }
    if (status === "ready") {
      return "good-text";
    }
    return "";
  }

  function renderUnlockableContentManifestPanel(manifest = {}, options = {}) {
    const escapeHtml = options.escapeHtml ?? ((value) => cleanText(value));
    const renderRouteMetricCard =
      options.renderRouteMetricCard ??
      ((label, value, detail) => `
        <div class="route-metric-card">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
          <small>${escapeHtml(detail)}</small>
        </div>
      `);
    const digest = getUnlockableContentStatusDigest(manifest);
    const summary = manifest.summary ?? {};
    const topIssues = toArray(manifest.issues).slice(0, 4);
    const activeGroups = toArray(manifest.groups)
      .filter((group) => group.totalCount > 0)
      .sort((left, right) => right.missingCount - left.missingCount || right.totalCount - left.totalCount)
      .slice(0, 6);

    return `
      <article class="detail-card preview-sprint-panel">
        <div class="panel-heading">
          <h2>可解锁内容清单</h2>
          <span class="badge badge-soft ${getToneClass(digest.status)}">${escapeHtml(digest.title)}</span>
        </div>
        <p class="helper-text">${escapeHtml(digest.detail)} 它会把 CG 图鉴、音乐回想、语音回听、资料馆、结局和成就汇总成一张发布前检查表。</p>
        <div class="preview-sprint-metrics">
          ${renderRouteMetricCard("条目就绪", `${summary.readyEntryCount ?? 0}/${summary.totalEntryCount ?? 0}`, "图鉴 / 回想 / 档案条目")}
          ${renderRouteMetricCard("分组启用", `${summary.activeGroupCount ?? 0}/${summary.groupCount ?? 0}`, "图库、回听、资料馆等")}
          ${renderRouteMetricCard("可达结局", `${summary.reachableEndingCount ?? 0}/${summary.endingCount ?? 0}`, "路线图可抵达")}
          ${renderRouteMetricCard("就绪度", `${summary.readinessPercent ?? 0}%`, `${summary.warningCount ?? 0} 个提醒`)}
        </div>
        <div class="detail-actions">
          <button class="toolbar-button toolbar-button-primary" data-action="export-unlockable-content-manifest-markdown">
            导出可解锁清单
          </button>
          <button class="toolbar-button" data-action="export-unlockable-content-manifest-csv">
            导出 CSV
          </button>
          <button class="toolbar-button" data-action="switch-screen" data-screen="preview">
            去试玩确认
          </button>
        </div>
        ${
          topIssues.length > 0
            ? `
              <div class="preview-sprint-grid">
                ${topIssues
                  .map(
                    (issue) => `
                      <article class="preview-sprint-card is-${issue.severity === "warn" ? "warn" : "soft"}">
                        <div class="preview-sprint-head">
                          <strong>${escapeHtml(issue.title)}</strong>
                          <span class="issue-tag ${issue.severity === "warn" ? "warn-text" : ""}">
                            ${escapeHtml(issue.code)}
                          </span>
                        </div>
                        <p>${escapeHtml(issue.detail)}</p>
                      </article>
                    `
                  )
                  .join("")}
              </div>
            `
            : activeGroups.length > 0
              ? `
                <div class="list-stack compact-stack">
                  ${activeGroups
                    .map(
                      (group) => `
                        <div class="route-testing-item">
                          <div>
                            <b>${escapeHtml(group.label)}</b>
                            <span>${escapeHtml(group.detail)}</span>
                          </div>
                          <span>${escapeHtml(`${group.readyCount}/${group.totalCount}`)}</span>
                        </div>
                      `
                    )
                    .join("")}
                </div>
              `
              : `
                <div class="assistant-tip">
                  <strong>暂时还没有可解锁内容。</strong>
                  <span>先添加 CG、BGM、角色、旁白、结局或配音台词，再重新导出这份清单。</span>
                </div>
              `
        }
      </article>
    `;
  }

  global.CanvasiaEditorUnlockableContentManifest = Object.freeze({
    buildUnlockableContentManifest,
    getUnlockableContentStatusDigest,
    buildUnlockableContentMarkdown,
    buildUnlockableContentCsv,
    renderUnlockableContentManifestPanel,
  });
})(typeof window !== "undefined" ? window : globalThis);
