(function attachStoryTemplateApplicationTools(global) {
  function getHelper(options, key, fallback = () => undefined) {
    return typeof options[key] === "function" ? options[key] : fallback;
  }

  function cloneStoryTemplateFields(fields) {
    if (!fields || typeof fields !== "object") {
      return {};
    }
    return JSON.parse(JSON.stringify(fields));
  }

  function buildStoryTemplateChoiceEffect(effectPlan = {}, options = {}) {
    const getSafeVariableId = getHelper(options, "getSafeVariableId", (value) => String(value ?? ""));
    const getVariableDefaultValue = getHelper(options, "getVariableDefaultValue", () => "");
    const normalizeVariableValue = getHelper(options, "normalizeVariableValue", (_variableId, value) => value);
    const type = String(effectPlan.type ?? "").trim();

    if (type === "variable_add") {
      const variableId = getSafeVariableId(effectPlan.variableId, "number");
      if (!variableId) {
        return null;
      }
      const value = Number(effectPlan.value ?? 1);
      return {
        type: "variable_add",
        variableId,
        value: Number.isFinite(value) ? value : 1,
      };
    }

    if (type === "variable_set") {
      const variableId = getSafeVariableId(effectPlan.variableId);
      if (!variableId) {
        return null;
      }
      const value = Object.prototype.hasOwnProperty.call(effectPlan, "value")
        ? effectPlan.value
        : getVariableDefaultValue(variableId);
      return {
        type: "variable_set",
        variableId,
        value: normalizeVariableValue(variableId, value),
      };
    }

    return null;
  }

  function applyStoryTemplateSpeaker(block, speakerId, options = {}) {
    const getSafeExpressionId = getHelper(options, "getSafeExpressionId", () => "");
    const getDefaultCharacterPosition = getHelper(options, "getDefaultCharacterPosition", () => "");

    if (!block || !speakerId) {
      return;
    }

    if (block.type === "dialogue") {
      block.speakerId = speakerId;
      block.expressionId = getSafeExpressionId(speakerId, null);
    }

    if (block.type === "character_show") {
      block.characterId = speakerId;
      block.expressionId = getSafeExpressionId(speakerId, null);
      if (!String(block.position ?? "").trim()) {
        block.position = getDefaultCharacterPosition(speakerId);
      }
    }

    if (block.type === "character_hide") {
      block.characterId = speakerId;
    }
  }

  function applyStoryTemplateChoiceTexts(block, choiceTexts) {
    if (!Array.isArray(choiceTexts) || !Array.isArray(block?.options)) {
      return;
    }

    block.options = block.options.map((option, index) => ({
      ...option,
      text: choiceTexts[index] ?? option.text,
    }));
  }

  function applyStoryTemplateChoiceOptions(block, recipe = {}, context = {}, options = {}) {
    const createChoiceOptionId = getHelper(options, "createChoiceOptionId", (blockId, index) => `${blockId}_choice_${index}`);
    const optionPlans = Array.isArray(recipe.choiceOptions) ? recipe.choiceOptions : [];
    if (!optionPlans.length || !Array.isArray(block?.options)) {
      applyStoryTemplateChoiceTexts(block, recipe.choiceTexts);
      return;
    }

    block.options = optionPlans.map((optionPlan, index) => {
      const baseOption = block.options[index] ?? {};
      const text = String(optionPlan?.text ?? recipe.choiceTexts?.[index] ?? baseOption.text ?? `选项 ${index + 1}`).trim();
      const effects = (Array.isArray(optionPlan?.effects) ? optionPlan.effects : [])
        .map((effectPlan) => buildStoryTemplateChoiceEffect(effectPlan, options))
        .filter(Boolean);
      return {
        id: baseOption.id ?? createChoiceOptionId(block.id, index),
        text: text || `选项 ${index + 1}`,
        gotoSceneId: String(optionPlan?.gotoSceneId ?? baseOption.gotoSceneId ?? context.scene?.id ?? ""),
        effects,
      };
    });
  }

  function applyStoryTemplateNumberCondition(block, recipe = {}, context = {}, options = {}) {
    const getSafeVariableId = getHelper(options, "getSafeVariableId", (value) => String(value ?? ""));
    const createDefaultConditionBranches = getHelper(options, "createDefaultConditionBranches", () => []);

    if (block?.type !== "condition" || !recipe.numberVariableCondition) {
      return;
    }

    const variableId = getSafeVariableId(recipe.numberVariableCondition.variableId, "number");
    if (!variableId) {
      return;
    }

    const value = Number(recipe.numberVariableCondition.value ?? 1);
    const rule = {
      variableId,
      operator: recipe.numberVariableCondition.operator ?? ">=",
      value: Number.isFinite(value) ? value : 1,
    };
    block.branches =
      Array.isArray(block.branches) && block.branches.length
        ? block.branches
        : createDefaultConditionBranches(block.id, context.scene?.id);
    block.branches[0] = {
      ...block.branches[0],
      when: [rule],
    };
  }

  function applyStoryTemplateRecipe(block, recipe = {}, context = {}, options = {}) {
    const getDefaultJumpTargetSceneId = getHelper(options, "getDefaultJumpTargetSceneId", (sceneId) => sceneId ?? "");
    Object.assign(block, cloneStoryTemplateFields(recipe.fields));

    if (recipe.speaker) {
      applyStoryTemplateSpeaker(block, context.speakerId, options);
    }

    applyStoryTemplateChoiceOptions(block, recipe, context, options);
    applyStoryTemplateNumberCondition(block, recipe, context, options);

    if (recipe.defaultJumpTarget && block.type === "jump") {
      block.targetSceneId = getDefaultJumpTargetSceneId(context.scene?.id);
    }
  }

  function finalizeStoryTemplateBlocks(blocks = [], recipes = []) {
    blocks.forEach((block, index) => {
      const recipe = recipes[index];
      if (block?.type !== "music_play" || !Number.isInteger(recipe?.endAfterRecipeIndex)) {
        return;
      }
      const endBlock = blocks[recipe.endAfterRecipeIndex];
      if (!endBlock?.id) {
        return;
      }
      block.endMode = "after_block";
      block.endBlockId = endBlock.id;
    });
  }

  function createTemplateBlock(sceneDraft, recipe = {}, context = {}, options = {}) {
    const createDefaultBlock = getHelper(options, "createDefaultBlock", () => null);

    if (!recipe?.type) {
      return null;
    }

    const block = createDefaultBlock(sceneDraft, recipe.type);
    if (!block) {
      return null;
    }
    applyStoryTemplateRecipe(block, recipe, context, options);
    sceneDraft.blocks.push(block);
    return block;
  }

  function buildStoryTemplateBlocks(scene, templateId, options = {}) {
    const getStoryTemplatePreset = getHelper(options, "getStoryTemplatePreset", () => null);
    const getStoryTemplateBlockRecipes = getHelper(options, "getStoryTemplateBlockRecipes", () => []);
    const cloneScene = getHelper(options, "cloneScene", (value) => JSON.parse(JSON.stringify(value ?? {})));
    const getSafeCharacterId = getHelper(options, "getSafeCharacterId", (value) => String(value ?? ""));
    const preset = getStoryTemplatePreset(templateId);

    if (!scene || !preset) {
      return [];
    }

    const recipes = getStoryTemplateBlockRecipes(templateId);
    if (!recipes.length) {
      return [];
    }

    const sceneDraft = cloneScene(scene);
    sceneDraft.blocks = [...(scene.blocks ?? [])];
    const blocks = [];
    const speakerId = getSafeCharacterId(options.selectedCharacterId ?? options.firstCharacterId);
    const context = {
      scene,
      speakerId,
    };

    recipes.forEach((recipe) => {
      const block = createTemplateBlock(sceneDraft, recipe, context, options);
      if (block) {
        blocks.push(block);
      }
    });

    finalizeStoryTemplateBlocks(blocks, recipes);
    return blocks;
  }

  function buildStoryTemplateApplicationSummary(preset = {}, blocks = [], options = {}) {
    const getBlockLabel = getHelper(options, "getBlockLabel", (type) => type || "卡片");
    const counts = blocks.reduce((result, block) => {
      const type = block?.type || "unknown";
      result[type] = (result[type] ?? 0) + 1;
      return result;
    }, {});
    const typeDigest = Object.entries(counts)
      .slice(0, 4)
      .map(([type, count]) => `${getBlockLabel(type)} ${count}`)
      .join(" · ");
    const countLabel = `${blocks.length} 张卡片`;
    const title = preset?.title ? `已插入模板：${preset.title}` : "已插入剧情模板";

    return {
      title,
      countLabel,
      typeDigest,
      message: typeDigest ? `${title}（${countLabel}：${typeDigest}）` : `${title}（${countLabel}）`,
    };
  }

  global.CanvasiaEditorStoryTemplateApplication = Object.freeze({
    applyStoryTemplateChoiceOptions,
    applyStoryTemplateChoiceTexts,
    applyStoryTemplateNumberCondition,
    applyStoryTemplateRecipe,
    applyStoryTemplateSpeaker,
    buildStoryTemplateApplicationSummary,
    buildStoryTemplateBlocks,
    buildStoryTemplateChoiceEffect,
    cloneStoryTemplateFields,
    createTemplateBlock,
    finalizeStoryTemplateBlocks,
  });
})(window);
