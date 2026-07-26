(function attachRuntimeAchievementTools(global) {
  const CUSTOM_ACHIEVEMENT_PREFIX = "custom:";
  const MAX_ACHIEVEMENT_ID_LENGTH = 64;

  function cleanText(value, fallback = "", maxLength = 240) {
    const text = String(value ?? "").trim();
    return (text || String(fallback ?? "").trim()).slice(0, maxLength);
  }

  function getSafeAchievementAuthorId(value, fallback = "achievement") {
    const normalize = (candidate) =>
      String(candidate ?? "")
        .normalize("NFKC")
        .trim()
        .toLowerCase()
        .replace(/\s+/g, "-")
        .replace(/[^0-9a-z_\-\u4e00-\u9fff]/g, "")
        .replace(/^[-_]+|[-_]+$/g, "")
        .slice(0, MAX_ACHIEVEMENT_ID_LENGTH);
    return normalize(value) || normalize(fallback) || "achievement";
  }

  function getCustomAchievementStorageId(authorId, fallback = "achievement") {
    return `${CUSTOM_ACHIEVEMENT_PREFIX}${getSafeAchievementAuthorId(authorId, fallback)}`;
  }

  function getLocalizedBlockValue(block, key, fallback, options = {}) {
    if (typeof options.getLocalizedValue === "function") {
      return options.getLocalizedValue(block, key, fallback);
    }
    return block?.[key] ?? fallback;
  }

  function sanitizeAchievementUnlockBlock(block = {}, options = {}) {
    const fallbackId = cleanText(block.id, "achievement", MAX_ACHIEVEMENT_ID_LENGTH);
    const authorId = getSafeAchievementAuthorId(block.achievementId, fallbackId);
    const name = cleanText(
      getLocalizedBlockValue(block, "title", block.title, options),
      "新的成就",
      80
    );
    return {
      id: getCustomAchievementStorageId(authorId),
      authorId,
      name,
      title: name,
      description: cleanText(
        getLocalizedBlockValue(block, "description", block.description, options),
        "完成这段剧情时解锁。",
        240
      ),
      category: cleanText(
        getLocalizedBlockValue(block, "category", block.category, options),
        "剧情里程碑",
        48
      ),
      requirement: cleanText(
        getLocalizedBlockValue(block, "requirement", block.requirement, options),
        "推进到指定剧情",
        120
      ),
      hiddenBeforeUnlock: block.hiddenBeforeUnlock === true,
      iconAssetId: cleanText(block.iconAssetId, "", 128),
      kind: "custom",
      progressTarget: 1,
    };
  }

  function collectCustomAchievementDefinitions(scenes = [], options = {}) {
    const definitions = [];
    const byId = new Map();

    (Array.isArray(scenes) ? scenes : []).forEach((scene) => {
      (Array.isArray(scene?.blocks) ? scene.blocks : []).forEach((block, blockIndex) => {
        if (block?.type !== "achievement_unlock") {
          return;
        }
        const definition = {
          ...sanitizeAchievementUnlockBlock(block, options),
          sceneId: cleanText(scene?.id, "", 128),
          blockId: cleanText(block?.id, "", 128),
          blockIndex,
          duplicateCount: 0,
        };
        const existing = byId.get(definition.id);
        if (existing) {
          existing.duplicateCount += 1;
          return;
        }
        byId.set(definition.id, definition);
        definitions.push(definition);
      });
    });

    return definitions.map((definition) => ({ ...definition }));
  }

  function toIdSet(value) {
    if (value instanceof Set) {
      return new Set(value);
    }
    if (Array.isArray(value)) {
      return new Set(value);
    }
    if (value && typeof value.keys === "function") {
      return new Set(value.keys());
    }
    return new Set();
  }

  function buildAutomaticAchievementDefinitions(metrics = {}, unlockedAchievementIds = []) {
    const unlocked = toIdSet(unlockedAchievementIds);
    const definitions = [];
    const sceneCount = Math.max(0, Number(metrics.sceneCount) || 0);
    const choiceBlockCount = Math.max(0, Number(metrics.choiceBlockCount) || 0);
    const characterCount = Math.max(0, Number(metrics.characterCount) || 0);
    const unlockedCharacterCount = Math.max(0, Number(metrics.unlockedCharacterCount) || 0);
    const galleryCount = Math.max(0, Number(metrics.galleryCount) || 0);
    const unlockedCgCount = Math.max(0, Number(metrics.unlockedCgCount) || 0);
    const musicCount = Math.max(0, Number(metrics.musicCount) || 0);
    const unlockedBgmCount = Math.max(0, Number(metrics.unlockedBgmCount) || 0);
    const endingCount = Math.max(0, Number(metrics.endingCount) || 0);
    const unlockedEndingCount = Math.max(0, Number(metrics.unlockedEndingCount) || 0);
    const add = (definition) => definitions.push({ kind: "automatic", hiddenBeforeUnlock: false, ...definition });

    if (sceneCount > 0) {
      add({
        id: "first_start",
        name: "初次启程",
        category: "剧情里程碑",
        description: "第一次正式开始试玩这个项目。",
        requirement: "点击开始试玩 1 次",
        progressCurrent: unlocked.has("first_start") ? 1 : 0,
        progressTarget: 1,
      });
    }
    if (choiceBlockCount > 0) {
      add({
        id: "first_choice",
        name: "分岔路口",
        category: "剧情里程碑",
        description: "第一次在剧情里做出一个选项分支。",
        requirement: "做出 1 次选项选择",
        progressCurrent: unlocked.has("first_choice") ? 1 : 0,
        progressTarget: 1,
      });
    }
    if (characterCount > 0) {
      add({
        id: "first_character",
        name: "初次相遇",
        category: "人物收集",
        description: "第一次在剧情里见到角色，人物档案馆开始亮起。",
        requirement: "解锁 1 位角色",
        progressCurrent: Math.min(unlockedCharacterCount, 1),
        progressTarget: 1,
      });
      add({
        id: "all_characters",
        name: "全员到齐",
        category: "人物收集",
        description: "把这个项目里的所有角色都收录进图鉴里。",
        requirement: `收录全部 ${characterCount} 位角色`,
        progressCurrent: Math.min(unlockedCharacterCount, characterCount),
        progressTarget: characterCount,
      });
    }
    if (galleryCount > 0) {
      add({
        id: "first_cg",
        name: "回想开幕",
        category: "EXTRA 收集",
        description: "第一次在剧情里解锁一张 CG。",
        requirement: "解锁 1 张 CG",
        progressCurrent: Math.min(unlockedCgCount, 1),
        progressTarget: 1,
      });
      add({
        id: "all_cg",
        name: "回想收藏家",
        category: "EXTRA 收集",
        description: "把这个项目里的所有 CG 都解锁进回想馆。",
        requirement: `解锁全部 ${galleryCount} 张 CG`,
        progressCurrent: Math.min(unlockedCgCount, galleryCount),
        progressTarget: galleryCount,
      });
    }
    if (musicCount > 0) {
      add({
        id: "first_bgm",
        name: "旋律初响",
        category: "EXTRA 收集",
        description: "第一次在剧情里听到并解锁一首 BGM。",
        requirement: "解锁 1 首 BGM",
        progressCurrent: Math.min(unlockedBgmCount, 1),
        progressTarget: 1,
      });
      add({
        id: "all_bgm",
        name: "全曲收藏",
        category: "EXTRA 收集",
        description: "把这个项目里的所有 BGM 都收录进音乐鉴赏。",
        requirement: `解锁全部 ${musicCount} 首 BGM`,
        progressCurrent: Math.min(unlockedBgmCount, musicCount),
        progressTarget: musicCount,
      });
    }
    if (endingCount > 0) {
      add({
        id: "first_ending",
        name: "终幕初见",
        category: "路线回收",
        description: "第一次真正抵达某条路线的结局。",
        requirement: "回收 1 个结局",
        progressCurrent: Math.min(unlockedEndingCount, 1),
        progressTarget: 1,
      });
      add({
        id: "all_endings",
        name: "全结局制霸",
        category: "路线回收",
        description: "把所有可回收结局都点亮进结局回收馆。",
        requirement: `回收全部 ${endingCount} 个结局`,
        progressCurrent: Math.min(unlockedEndingCount, endingCount),
        progressTarget: endingCount,
      });
    }
    return definitions;
  }

  function buildAchievementDefinitions(options = {}) {
    const unlocked = toIdSet(options.unlockedAchievementIds);
    const automatic = buildAutomaticAchievementDefinitions(options.metrics, unlocked);
    const custom = collectCustomAchievementDefinitions(options.scenes, options).map((definition) => ({
      ...definition,
      iconUrl:
        definition.iconAssetId && typeof options.getAssetUrl === "function"
          ? options.getAssetUrl(definition.iconAssetId)
          : "",
      progressCurrent: unlocked.has(definition.id) ? 1 : 0,
      progressTarget: 1,
    }));
    return [...custom, ...automatic];
  }

  function sanitizeAchievementProgressEntries(source, definitions = []) {
    const validIds = new Set((Array.isArray(definitions) ? definitions : []).map((item) => item?.id).filter(Boolean));
    return (source && typeof source === "object" ? Object.entries(source) : []).filter(
      ([achievementId, unlockedAt]) =>
        validIds.has(achievementId) && typeof unlockedAt === "string" && unlockedAt.trim()
    );
  }

  function getAchievementPresentation(definition = {}, unlocked = false) {
    const hidden = definition.hiddenBeforeUnlock === true && !unlocked;
    return {
      name: hidden ? "隐藏成就" : cleanText(definition.name, "未命名成就", 80),
      description: hidden ? "继续探索后才能揭晓这个成就。" : cleanText(definition.description, "尚未填写说明。", 240),
      category: hidden ? "隐藏收集" : cleanText(definition.category, "剧情里程碑", 48),
      requirement: hidden ? "条件尚未公开" : cleanText(definition.requirement, "推进剧情后解锁", 120),
      iconUrl: hidden ? "" : cleanText(definition.iconUrl, "", 1000),
      hidden,
    };
  }

  global.CanvasiaRuntimeAchievements = Object.freeze({
    CUSTOM_ACHIEVEMENT_PREFIX,
    MAX_ACHIEVEMENT_ID_LENGTH,
    getSafeAchievementAuthorId,
    getCustomAchievementStorageId,
    sanitizeAchievementUnlockBlock,
    collectCustomAchievementDefinitions,
    buildAutomaticAchievementDefinitions,
    buildAchievementDefinitions,
    sanitizeAchievementProgressEntries,
    getAchievementPresentation,
  });
})(typeof window !== "undefined" ? window : globalThis);
