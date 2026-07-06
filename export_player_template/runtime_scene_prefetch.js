const PRELOADABLE_TYPES = new Set(["background", "sprite", "cg", "ui", "bgm", "sfx", "voice", "video"]);
const IMAGE_TYPES = new Set(["background", "sprite", "cg", "ui"]);
const AUDIO_TYPES = new Set(["bgm", "sfx", "voice"]);
const VIDEO_TYPES = new Set(["video"]);
const DIRECT_ASSET_BLOCK_TYPES = new Set([
  "background",
  "music_play",
  "sfx_play",
  "video_play",
  "particle_effect",
]);

function toArray(value) {
  return Array.isArray(value) ? value : [];
}

function cleanText(value) {
  return String(value ?? "").trim();
}

function getFromCollection(collection, id) {
  const key = cleanText(id);
  if (!key || !collection) {
    return null;
  }
  if (collection instanceof Map) {
    return collection.get(key) ?? null;
  }
  if (Array.isArray(collection)) {
    return collection.find((item) => cleanText(item?.id) === key) ?? null;
  }
  if (typeof collection === "object") {
    return collection[key] ?? null;
  }
  return null;
}

function getSceneBlocks(scene) {
  return toArray(scene?.blocks);
}

function getAssetType(asset) {
  const type = cleanText(asset?.type);
  return PRELOADABLE_TYPES.has(type) ? type : "";
}

function getAssetUrl(asset) {
  return cleanText(asset?.exportUrl ?? asset?.publicPath ?? asset?.url);
}

function getAssetSizeBytes(asset) {
  const size = Number(asset?.fileSizeBytes ?? asset?.sizeBytes ?? asset?.byteSize ?? 0);
  return Number.isFinite(size) && size > 0 ? Math.floor(size) : 0;
}

function getPreloadReason(block, fallback = "路线预取") {
  const type = cleanText(block?.type);
  if (type === "background") return "即将切换背景";
  if (type === "character_show") return "即将显示立绘";
  if (type === "dialogue") return "即将显示角色或播放语音";
  if (type === "narration") return "即将播放旁白语音";
  if (type === "music_play") return "即将切换 BGM";
  if (type === "sfx_play") return "即将播放音效";
  if (type === "video_play") return "即将播放视频";
  if (type === "particle_effect") return "即将显示粒子贴图";
  return fallback;
}

function addAssetId(target, assetId, reason) {
  const id = cleanText(assetId);
  if (!id) {
    return;
  }
  target.push({ assetId: id, reason });
}

function collectCharacterSpriteAssetIds(block, context, target) {
  const charactersById = context.charactersById;
  const characterId = cleanText(block?.characterId ?? block?.speakerId);
  if (!characterId) {
    return;
  }
  const character = getFromCollection(charactersById, characterId);
  const expressions = toArray(character?.expressions);
  const expressionId = cleanText(block?.expressionId);
  const expression = expressionId ? expressions.find((item) => cleanText(item?.id) === expressionId) : null;
  const fallbackExpression = expressions[0] ?? null;
  addAssetId(
    target,
    expression?.spriteAssetId ?? fallbackExpression?.spriteAssetId ?? character?.defaultSpriteId,
    getPreloadReason(block)
  );
}

function collectBlockAssetCandidates(block, context) {
  const candidates = [];
  if (!block || typeof block !== "object") {
    return candidates;
  }

  if (DIRECT_ASSET_BLOCK_TYPES.has(block.type)) {
    addAssetId(candidates, block.assetId, getPreloadReason(block));
  }

  if (block.type === "dialogue" || block.type === "narration") {
    addAssetId(candidates, block.voiceAssetId, getPreloadReason(block));
  }

  if (block.type === "character_show" || block.type === "dialogue") {
    collectCharacterSpriteAssetIds(block, context, candidates);
  }

  return candidates;
}

function shouldSkipAsset(assetId, asset, excludeAssetIds) {
  if (!assetId || !asset || asset.isMissing) {
    return true;
  }
  if (excludeAssetIds?.has?.(assetId)) {
    return true;
  }
  return !getAssetType(asset) || !getAssetUrl(asset);
}

function upsertPrefetchEntry(entriesById, assetId, asset, metadata) {
  const existing = entriesById.get(assetId);
  const type = getAssetType(asset);
  const url = getAssetUrl(asset);
  const priority = Number.isFinite(Number(metadata.priority)) ? Number(metadata.priority) : 0;
  const phase = cleanText(metadata.phase) || "deferred";
  const phaseRank = { critical: 0, early: 1, deferred: 2, library: 3 };

  if (
    existing &&
    existing.priority >= priority &&
    (phaseRank[existing.phase] ?? 9) <= (phaseRank[phase] ?? 9)
  ) {
    return;
  }

  entriesById.set(assetId, {
    assetId,
    url,
    type,
    name: cleanText(asset.name) || assetId,
    phase,
    priority,
    sizeBytes: getAssetSizeBytes(asset),
    reason: metadata.reason,
    sceneId: metadata.sceneId,
    blockId: metadata.blockId,
  });
}

function addBlockAssets(entriesById, block, context, metadata) {
  const assetsById = context.assetsById;
  collectBlockAssetCandidates(block, context).forEach((candidate) => {
    const assetId = cleanText(candidate.assetId);
    const asset = getFromCollection(assetsById, assetId);
    if (shouldSkipAsset(assetId, asset, context.excludeAssetIds)) {
      return;
    }
    upsertPrefetchEntry(entriesById, assetId, asset, {
      ...metadata,
      reason: candidate.reason || metadata.reason,
      blockId: cleanText(block?.id),
    });
  });
}

function collectSceneRange(entriesById, scene, context, options) {
  const blocks = getSceneBlocks(scene);
  const startIndex = Math.max(0, Number(options.startIndex) || 0);
  const limit = Math.max(0, Number(options.limit) || 0);
  blocks.slice(startIndex, startIndex + limit).forEach((block, offset) => {
    addBlockAssets(entriesById, block, context, {
      sceneId: cleanText(scene?.id),
      phase: options.phase,
      priority: Math.max(0, Number(options.priority) || 0) - offset,
      reason: options.reason,
    });
  });
}

function isContinueTarget(value, continueTarget = "__continue__") {
  return cleanText(value) === continueTarget;
}

function collectChoiceTargetSceneIds(snapshot, continueTarget) {
  return toArray(snapshot?.choiceOptions)
    .map((option) => cleanText(option?.gotoSceneId ?? option?.targetSceneId))
    .filter((sceneId) => sceneId && !isContinueTarget(sceneId, continueTarget));
}

function collectBlockTargetSceneIds(block, continueTarget = "__continue__") {
  const targets = [];
  if (block?.type === "jump") {
    targets.push(cleanText(block.targetSceneId));
  }
  if (block?.type === "condition") {
    toArray(block.branches).forEach((branch) => targets.push(cleanText(branch?.gotoSceneId)));
    targets.push(cleanText(block.elseGotoSceneId));
  }
  if (block?.type === "choice") {
    toArray(block.options).forEach((option) => {
      const target = cleanText(option?.gotoSceneId ?? option?.targetSceneId);
      if (!isContinueTarget(target, continueTarget)) {
        targets.push(target);
      }
    });
  }
  return targets.filter(Boolean);
}

function getUniqueSceneIds(sceneIds) {
  return Array.from(new Set(sceneIds.map(cleanText).filter(Boolean)));
}

function getPrefetchSignature(snapshot, sceneIds, entries) {
  const current = [snapshot?.sceneId, snapshot?.blockId, snapshot?.blockIndex].map((value) => cleanText(value)).join(":");
  const targetKey = getUniqueSceneIds(sceneIds).join(",");
  const assetKey = entries.map((entry) => entry.assetId).join(",");
  return [current, targetKey, assetKey].join("|");
}

export function buildRuntimeScenePrefetchManifest(snapshot, context = {}, options = {}) {
  const scenesById = context.scenesById;
  const continueTarget = cleanText(options.choiceContinueTarget) || "__continue__";
  const currentScene = getFromCollection(scenesById, snapshot?.sceneId);
  const blockLookahead = Math.max(1, Number(options.blockLookahead) || 8);
  const targetBlockLookahead = Math.max(1, Number(options.targetBlockLookahead) || 10);
  const maxEntries = Math.max(1, Number(options.maxEntries) || 24);
  const entriesById = new Map();
  const targetSceneIds = [];

  if (!snapshot || snapshot.completed || !currentScene) {
    return {
      formatVersion: 1,
      entrySceneId: cleanText(snapshot?.sceneId),
      generatedBy: "runtime_scene_prefetch",
      prefetchKey: getPrefetchSignature(snapshot, [], []),
      targetSceneIds: [],
      entries: [],
    };
  }

  collectSceneRange(entriesById, currentScene, context, {
    startIndex: Math.max(0, Number(snapshot.blockIndex) + 1),
    limit: blockLookahead,
    phase: "early",
    priority: 84,
    reason: "当前场景即将播放",
  });

  const transitionTarget = cleanText(snapshot.transitionTargetSceneId);
  if (transitionTarget && !isContinueTarget(transitionTarget, continueTarget)) {
    targetSceneIds.push(transitionTarget);
  }
  targetSceneIds.push(...collectChoiceTargetSceneIds(snapshot, continueTarget));

  getSceneBlocks(currentScene)
    .slice(Math.max(0, Number(snapshot.blockIndex) + 1), Math.max(0, Number(snapshot.blockIndex) + 1) + blockLookahead)
    .forEach((block) => {
      targetSceneIds.push(...collectBlockTargetSceneIds(block, continueTarget));
    });

  getUniqueSceneIds(targetSceneIds).forEach((sceneId, index) => {
    const scene = getFromCollection(scenesById, sceneId);
    if (!scene) {
      return;
    }
    collectSceneRange(entriesById, scene, context, {
      startIndex: 0,
      limit: targetBlockLookahead,
      phase: index < 4 ? "early" : "deferred",
      priority: Math.max(32, 76 - index * 4),
      reason: "即将进入的分支场景",
    });
  });

  const entries = Array.from(entriesById.values())
    .sort((left, right) => {
      if (right.priority !== left.priority) {
        return right.priority - left.priority;
      }
      return left.assetId.localeCompare(right.assetId);
    })
    .slice(0, maxEntries)
    .map((entry, index) => ({
      ...entry,
      preloadIndex: index + 1,
    }));

  return {
    formatVersion: 1,
    entrySceneId: cleanText(snapshot.sceneId),
    generatedBy: "runtime_scene_prefetch",
    prefetchKey: getPrefetchSignature(snapshot, targetSceneIds, entries),
    targetSceneIds: getUniqueSceneIds(targetSceneIds),
    entries,
  };
}

export function getRuntimeScenePrefetchSummary(manifest) {
  const entries = toArray(manifest?.entries);
  return entries.reduce(
    (summary, entry) => {
      summary.totalCount += 1;
      summary.totalSizeBytes += getAssetSizeBytes(entry);
      if (IMAGE_TYPES.has(entry.type)) summary.imageCount += 1;
      if (AUDIO_TYPES.has(entry.type)) summary.audioCount += 1;
      if (VIDEO_TYPES.has(entry.type)) summary.videoCount += 1;
      return summary;
    },
    {
      totalCount: 0,
      imageCount: 0,
      audioCount: 0,
      videoCount: 0,
      totalSizeBytes: 0,
    }
  );
}
