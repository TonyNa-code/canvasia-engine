(function attachSceneMoodRecipeTools(global) {
  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function getEscapeHtml(options = {}) {
    return typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtml;
  }

  function clone(value) {
    return JSON.parse(JSON.stringify(value ?? null));
  }

  function toBlocks(scene = {}) {
    return Array.isArray(scene.blocks) ? scene.blocks : [];
  }

  function hasBlockType(scene, type) {
    return toBlocks(scene).some((block) => block?.type === type);
  }

  function countBlockTypes(scene, types = []) {
    const typeSet = new Set(types);
    return toBlocks(scene).filter((block) => typeSet.has(block?.type)).length;
  }

  const EFFECT_TYPES = Object.freeze([
    "wait",
    "particle_effect",
    "screen_shake",
    "screen_flash",
    "screen_fade",
    "camera_zoom",
    "camera_pan",
    "screen_filter",
    "depth_blur",
  ]);

  const SCENE_MOOD_RECIPES = Object.freeze([
    Object.freeze({
      id: "warm-confession",
      title: "心动特写",
      subtitle: "适合告白、暧昧、角色靠近的情绪段",
      tone: "good",
      tags: Object.freeze(["柔光", "景深", "轻推镜头"]),
      priority: 90,
      buildBlocks: () => [
        {
          type: "screen_filter",
          action: "apply",
          preset: "dream",
          strength: "soft",
          grade: { brightness: 108, contrast: 96, saturation: 112, hue: 0, temperature: 18, vignette: 8 },
        },
        { type: "depth_blur", action: "apply", focus: "center", strength: "soft" },
        { type: "camera_zoom", action: "zoom_in", strength: "light", focus: "center" },
        { type: "wait", durationSeconds: 0.6 },
      ],
      score: (scene) => (hasBlockType(scene, "dialogue") ? 24 : 4) + (hasBlockType(scene, "character_show") ? 14 : 0),
    }),
    Object.freeze({
      id: "mystery-pressure",
      title: "悬疑压迫",
      subtitle: "适合秘密揭露、危险临近、夜晚调查",
      tone: "warn",
      tags: Object.freeze(["冷色", "黑闪", "侧向镜头"]),
      priority: 84,
      buildBlocks: () => [
        {
          type: "screen_filter",
          action: "apply",
          preset: "cold",
          strength: "medium",
          grade: { brightness: 92, contrast: 118, saturation: 76, hue: -8, temperature: -22, vignette: 24 },
        },
        { type: "camera_pan", target: "left", strength: "light" },
        { type: "screen_flash", color: "black", intensity: "soft", duration: "short" },
        { type: "wait", durationSeconds: 0.45 },
      ],
      score: (scene) => (hasBlockType(scene, "screen_filter") ? 4 : 22) + (hasBlockType(scene, "dialogue") ? 10 : 0),
    }),
    Object.freeze({
      id: "rain-memory",
      title: "雨夜回忆",
      subtitle: "适合雨天、独白、回忆切入和低声叙述",
      tone: "soft",
      tags: Object.freeze(["雨丝", "冷色回忆", "可带 BGM"]),
      priority: 78,
      buildBlocks: (context = {}) => [
        {
          type: "particle_effect",
          action: "start",
          preset: "rain",
          intensity: "light",
          speed: "slow",
          wind: "right",
          area: "full",
          density: 36,
          sizeMin: 2,
          sizeMax: 8,
          gravityY: 0.8,
          spreadX: 0.28,
          spreadY: 0.45,
          opacityMin: 0.22,
          opacityMax: 0.62,
          color: "#d8ecff",
          colorAccent: "#a9c7ff",
          blend: "screen",
        },
        {
          type: "screen_filter",
          action: "apply",
          preset: "cold",
          strength: "soft",
          grade: { brightness: 96, contrast: 104, saturation: 86, hue: -4, temperature: -12, vignette: 12 },
        },
        ...(context.bgmAssetId
          ? [
              {
                type: "music_play",
                assetId: context.bgmAssetId,
                loop: true,
                volume: 72,
                fadeInMs: 1200,
                fadeOutMs: 1200,
                endMode: "until_next_music",
                endBlockId: "",
              },
            ]
          : []),
        { type: "wait", durationSeconds: 0.7 },
      ],
      score: (scene, context = {}) => (hasBlockType(scene, "background") ? 10 : 0) + (context.bgmAssetId ? 12 : 0) + 16,
    }),
    Object.freeze({
      id: "climax-pulse",
      title: "爆点冲击",
      subtitle: "适合强台词、真相揭开、战斗或情绪爆发",
      tone: "danger",
      tags: Object.freeze(["强推镜头", "震动", "白闪"]),
      priority: 76,
      buildBlocks: () => [
        { type: "camera_zoom", action: "zoom_in", strength: "heavy", focus: "center" },
        { type: "screen_shake", intensity: "medium", duration: "short" },
        { type: "screen_flash", color: "white", intensity: "soft", duration: "short" },
        { type: "wait", durationSeconds: 0.3 },
      ],
      score: (scene) => (hasBlockType(scene, "choice") ? 14 : 0) + (hasBlockType(scene, "dialogue") ? 18 : 0),
    }),
    Object.freeze({
      id: "quiet-ending",
      title: "收束留白",
      subtitle: "适合章节结束、分别、转入黑场或 ED 前",
      tone: "good",
      tags: Object.freeze(["黑场", "BGM 淡出", "停顿"]),
      priority: 72,
      buildBlocks: () => [
        { type: "screen_fade", action: "fade_out", color: "black", duration: "medium" },
        { type: "music_stop", fadeOutMs: 1400 },
        { type: "wait", durationSeconds: 0.9 },
      ],
      score: (scene) => (hasBlockType(scene, "music_play") ? 18 : 0) + (hasBlockType(scene, "jump") ? 8 : 0) + 10,
    }),
  ]);

  const RECIPE_MAP = Object.freeze(Object.fromEntries(SCENE_MOOD_RECIPES.map((recipe) => [recipe.id, recipe])));

  function getSceneMoodRecipe(recipeId) {
    return RECIPE_MAP[String(recipeId ?? "")] ?? null;
  }

  function createSceneMoodBlockIdFactory(scene = {}) {
    const used = new Set(toBlocks(scene).map((block) => String(block?.id ?? "")).filter(Boolean));
    let number = 1;

    return function createSceneMoodBlockId() {
      while (used.has(`block_${String(number).padStart(3, "0")}`)) {
        number += 1;
      }
      const blockId = `block_${String(number).padStart(3, "0")}`;
      used.add(blockId);
      number += 1;
      return blockId;
    };
  }

  function buildRecipeBlocks(recipe, scene, context = {}) {
    const rawBlocks = typeof recipe.buildBlocks === "function" ? recipe.buildBlocks(context, scene) : [];
    const createId =
      typeof context.createBlockId === "function" ? context.createBlockId : createSceneMoodBlockIdFactory(scene);

    return rawBlocks
      .filter((block) => block && typeof block === "object" && block.type)
      .map((block) => ({
        ...clone(block),
        id: createId(),
      }));
  }

  function applySceneMoodRecipe(scene = {}, recipeId = "", options = {}) {
    const recipe = getSceneMoodRecipe(recipeId);
    if (!recipe) {
      return {
        applied: false,
        reason: "unknown_recipe",
        scene,
        blocks: [],
        insertIndex: -1,
        recipe: null,
        summary: "没有找到这组演出配方",
      };
    }

    const nextScene = clone({ ...scene, blocks: toBlocks(scene) }) ?? { ...scene, blocks: [] };
    nextScene.blocks = Array.isArray(nextScene.blocks) ? nextScene.blocks : [];
    const blocks = buildRecipeBlocks(recipe, nextScene, options);

    if (!blocks.length) {
      return {
        applied: false,
        reason: "empty_recipe",
        scene: nextScene,
        blocks: [],
        insertIndex: -1,
        recipe,
        summary: `${recipe.title} 暂时没有可插入的演出卡片`,
      };
    }

    const selectedBlockId = String(options.insertAfterBlockId ?? "");
    const selectedIndex = nextScene.blocks.findIndex((block) => String(block?.id ?? "") === selectedBlockId);
    const insertIndex = selectedIndex >= 0 ? selectedIndex + 1 : nextScene.blocks.length;
    nextScene.blocks.splice(insertIndex, 0, ...blocks);

    return {
      applied: true,
      scene: nextScene,
      blocks,
      insertIndex,
      recipe,
      summary: `已套用“${recipe.title}”：新增 ${blocks.length} 张演出卡片`,
    };
  }

  function analyzeSceneMoodReadiness(scene = {}, context = {}) {
    const storyCount = countBlockTypes(scene, ["dialogue", "narration", "choice"]);
    const effectCount = countBlockTypes(scene, EFFECT_TYPES);
    const hasBackground = hasBlockType(scene, "background");
    const hasMusic = hasBlockType(scene, "music_play");
    const canApply = storyCount > 0 || hasBackground || hasMusic;

    return {
      storyCount,
      effectCount,
      hasBackground,
      hasMusic,
      hasBgmCandidate: Boolean(context.bgmAssetId),
      canApply,
      emptyReason: canApply ? "" : "先写一两句正文或补背景，再套演出配方会更自然。",
    };
  }

  function getSceneMoodRecipeSuggestions(scene = {}, context = {}, options = {}) {
    const limit = Math.max(1, Number(options.limit ?? 4) || 4);
    const readiness = analyzeSceneMoodReadiness(scene, context);

    return SCENE_MOOD_RECIPES.map((recipe) => ({
      ...recipe,
      tags: [...(recipe.tags ?? [])],
      score: (typeof recipe.score === "function" ? recipe.score(scene, context, readiness) : 0) + recipe.priority / 10,
      disabled: !readiness.canApply,
      disabledReason: readiness.emptyReason,
    }))
      .sort((left, right) => right.score - left.score || right.priority - left.priority)
      .slice(0, limit);
  }

  function renderSceneMoodRecipePanel(scene = {}, context = {}, options = {}) {
    const escape = getEscapeHtml(options);
    const suggestions = getSceneMoodRecipeSuggestions(scene, context, { limit: options.limit ?? 4 });
    const readiness = analyzeSceneMoodReadiness(scene, context);
    const toneLabels = {
      danger: "爆点",
      warn: "悬疑",
      good: "常用",
      soft: "氛围",
    };
    const toneClass = (tone) => {
      if (tone === "danger") return "danger-text";
      if (tone === "warn") return "warn-text";
      return "good-text";
    };

    return `
      <article class="production-task-card story-structure-section story-optimizer-panel story-mood-recipe-panel">
        <div class="production-task-top">
          <strong>演出配方</strong>
          <span class="issue-tag good-text">一键插入可调卡片</span>
        </div>
        <p class="helper-text">
          这些配方会把滤镜、镜头、停顿、粒子和音频范围组合成可见的剧情卡片；套用后仍可逐张修改或删除。
        </p>
        ${
          readiness.canApply
            ? `<div class="story-optimizer-grid">
                ${suggestions
                  .map(
                    (recipe) => `
                      <article class="story-optimizer-card is-${escape(recipe.tone)}">
                        <div class="story-optimizer-head">
                          <strong>${escape(recipe.title)}</strong>
                          <span class="issue-tag ${toneClass(recipe.tone)}">${escape(toneLabels[recipe.tone] ?? "配方")}</span>
                        </div>
                        <p>${escape(recipe.subtitle)}</p>
                        <div class="story-optimizer-tag-row">
                          ${recipe.tags.map((tag) => `<span class="issue-tag">${escape(tag)}</span>`).join("")}
                        </div>
                        <div class="story-optimizer-action-row">
                          <button
                            type="button"
                            class="toolbar-button toolbar-button-primary"
                            data-action="apply-scene-mood-recipe"
                            data-recipe-id="${escape(recipe.id)}"
                          >
                            套用这组配方
                          </button>
                        </div>
                      </article>
                    `
                  )
                  .join("")}
              </div>`
            : `<div class="story-structure-step"><strong>${escape(readiness.emptyReason)}</strong></div>`
        }
      </article>
    `;
  }

  global.CanvasiaEditorSceneMoodRecipes = {
    EFFECT_TYPES,
    SCENE_MOOD_RECIPES,
    getSceneMoodRecipe,
    createSceneMoodBlockIdFactory,
    buildRecipeBlocks,
    applySceneMoodRecipe,
    analyzeSceneMoodReadiness,
    getSceneMoodRecipeSuggestions,
    renderSceneMoodRecipePanel,
  };
})(typeof window !== "undefined" ? window : globalThis);
