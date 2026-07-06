(function attachStageDirectionSheetTools(global) {
  const storyBlockCatalogTools = global.CanvasiaEditorStoryBlockCatalog || {};

  const POSITION_LABELS = Object.freeze({
    left: "左侧",
    center: "中间",
    right: "右侧",
  });

  const FALLBACK_BLOCK_LABELS = Object.freeze({
    background: "背景",
    dialogue: "台词",
    narration: "旁白",
    character_show: "角色登场",
    character_hide: "角色退场",
    video_play: "视频",
    credits_roll: "片尾字幕",
    wait: "等待停顿",
    choice: "选项",
    jump: "跳转",
  });

  const BLOCK_LABELS = Object.freeze({
    ...FALLBACK_BLOCK_LABELS,
    ...(storyBlockCatalogTools.BLOCK_COMPACT_LABELS ?? {}),
  });

  const STAGE_DIRECTION_AUTO_FIX_DEFAULTS = Object.freeze({
    characterShowTransition: "fade",
    characterHideTransition: "fade",
    characterShowDurationMs: 600,
    characterHideDurationMs: 420,
  });

  const CHARACTER_STAGE_DEFAULTS = Object.freeze({
    offsetX: 0,
    offsetY: 0,
    scale: 100,
    opacity: 100,
    layer: 0,
    flipX: false,
  });

  const VALID_POSITIONS = Object.freeze(["left", "center", "right"]);
  const VALID_CHARACTER_TRANSITIONS = Object.freeze(["fade", "slide_left", "slide_right", "rise", "pop", "none"]);
  const STAGE_POSITION_X = Object.freeze({ left: -36, center: 0, right: 36 });

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function clampNumber(value, minimum, maximum, fallback = minimum) {
    const number = Number(value);
    if (!Number.isFinite(number)) {
      return fallback;
    }
    return Math.min(Math.max(number, minimum), maximum);
  }

  function getSafePositionValue(position, fallback = "center") {
    const safePosition = cleanText(position);
    return VALID_POSITIONS.includes(safePosition) ? safePosition : fallback;
  }

  function getSafeCharacterTransitionValue(transition, fallback = "fade") {
    const safeTransition = cleanText(transition);
    return VALID_CHARACTER_TRANSITIONS.includes(safeTransition) ? safeTransition : fallback;
  }

  function getSafeTransitionDurationMs(value, fallback = 600) {
    return Math.round(clampNumber(value, 0, 5000, fallback));
  }

  function normalizeCharacterStage(stageSource = {}) {
    const source = stageSource && typeof stageSource === "object" ? stageSource : {};
    return {
      offsetX: Math.round(clampNumber(source.offsetX, -100, 100, CHARACTER_STAGE_DEFAULTS.offsetX)),
      offsetY: Math.round(clampNumber(source.offsetY, -100, 100, CHARACTER_STAGE_DEFAULTS.offsetY)),
      scale: Math.round(clampNumber(source.scale, 45, 220, CHARACTER_STAGE_DEFAULTS.scale)),
      opacity: Math.round(clampNumber(source.opacity, 0, 100, CHARACTER_STAGE_DEFAULTS.opacity)),
      layer: Math.round(clampNumber(source.layer, -10, 10, CHARACTER_STAGE_DEFAULTS.layer)),
      flipX: Boolean(source.flipX),
    };
  }

  function getStageCompositionX(item = {}) {
    const stage = normalizeCharacterStage(item.stage);
    return (STAGE_POSITION_X[item.position] ?? STAGE_POSITION_X.center) + stage.offsetX * 0.45;
  }

  function getStageCompositionRadius(item = {}) {
    const stage = normalizeCharacterStage(item.stage);
    return Math.max(12, stage.scale * 0.18);
  }

  function buildStageCompositionSnapshot(visibleCharacters = new Map(), context = {}) {
    const characters = [...visibleCharacters.values()].map((item) => {
      const stage = normalizeCharacterStage(item.stage);
      return {
        characterId: item.characterId,
        characterName: item.characterName,
        expressionName: item.expressionName,
        position: item.position,
        positionLabel: getPositionLabel(item.position),
        stage,
        centerX: Math.round(getStageCompositionX(item)),
        radius: Math.round(getStageCompositionRadius(item)),
      };
    });
    return {
      chapterName: context.chapterName,
      sceneName: context.sceneName,
      sceneId: context.sceneId,
      blockId: context.blockId,
      blockIndex: context.blockIndex,
      blockLabel: context.blockLabel,
      visibleCount: characters.length,
      characters,
      characterNames: characters.map((item) => item.characterName).filter(Boolean).join(" / "),
    };
  }

  function findStageOverlapPairs(characters = []) {
    const pairs = [];
    for (let leftIndex = 0; leftIndex < characters.length; leftIndex += 1) {
      for (let rightIndex = leftIndex + 1; rightIndex < characters.length; rightIndex += 1) {
        const left = characters[leftIndex];
        const right = characters[rightIndex];
        const distance = Math.abs(left.centerX - right.centerX);
        const overlapThreshold = Math.min(34, (left.radius + right.radius) * 0.72);
        if (distance < overlapThreshold) {
          pairs.push(`${left.characterName || left.characterId} / ${right.characterName || right.characterId}`);
        }
      }
    }
    return pairs;
  }

  function inspectStageComposition(visibleCharacters = new Map(), issues = [], context = {}, options = {}) {
    const issueStartIndex = issues.length;
    const snapshot = buildStageCompositionSnapshot(visibleCharacters, context);
    const risks = [];
    const positionCounts = new Map();
    const layerCounts = new Map();
    snapshot.characters.forEach((item) => {
      positionCounts.set(item.position, (positionCounts.get(item.position) ?? 0) + 1);
      layerCounts.set(item.stage.layer, (layerCounts.get(item.stage.layer) ?? 0) + 1);
    });
    if ([...positionCounts.values()].some((count) => count > 1)) {
      pushIssue(issues, "tip", "stage_position_overlap", "角色站位可能重叠", "当前舞台有多个角色使用同一站位，建议确认画面是否拥挤。", context);
      risks.push("同站位");
    }
    const overlapPairs = findStageOverlapPairs(snapshot.characters);
    if (overlapPairs.length > 0) {
      pushIssue(issues, "warn", "stage_geometry_overlap", "立绘可能互相遮挡", `请复查：${overlapPairs.join("、")} 的站位、偏移或缩放。`, context);
      risks.push("遮挡");
    }
    if ([...layerCounts.values()].some((count) => count > 1) && snapshot.characters.length > 1) {
      pushIssue(issues, "tip", "stage_layer_overlap", "角色图层可能冲突", "同屏多个角色使用相同图层，复杂遮挡时建议显式区分图层。", context);
      risks.push("图层");
    }
    if (snapshot.visibleCount > 3) {
      pushIssue(issues, "tip", "stage_too_many_characters", "同屏角色较多", "视觉小说常规画面建议控制在 1-3 人，更多角色建议拆镜头或缩放。", context);
      risks.push("拥挤");
    }
    if (snapshot.visibleCount > 1 && snapshot.characters.some((item) => item.stage.scale >= 155)) {
      pushIssue(issues, "tip", "stage_large_sprite_crowding", "大比例立绘可能压迫画面", "同屏多人时，超过 155% 的立绘建议配合偏移、图层或拆镜头使用。", context);
      risks.push("大比例");
    }
    const speaker = cleanText(options.speakerId)
      ? snapshot.characters.find((item) => item.characterId === cleanText(options.speakerId))
      : null;
    if (speaker && speaker.stage.opacity < 35) {
      pushIssue(issues, "warn", "stage_speaker_low_opacity", "说话人透明度过低", "当前说话人的透明度低于 35%，玩家可能看不清是谁在说话。", context);
      risks.push("说话人过淡");
    }
    const compositionIssues = issues.slice(issueStartIndex);
    const status = compositionIssues.some((issue) => issue.severity === "blocker")
      ? "blocker"
      : compositionIssues.some((issue) => issue.severity === "warn")
        ? "warn"
        : risks.length
          ? "tip"
          : "good";
    return {
      ...snapshot,
      status,
      risks,
      issues: compositionIssues,
      riskLabel: risks.length ? risks.join(" / ") : "构图正常",
    };
  }

  function isSameStage(left = {}, right = {}) {
    return ["offsetX", "offsetY", "scale", "opacity", "layer", "flipX"].every((key) => left[key] === right[key]);
  }

  function cloneSceneForStageFix(scene = {}) {
    return {
      ...scene,
      blocks: toArray(scene.blocks).map((block) => ({
        ...block,
        ...(block?.stage && typeof block.stage === "object" ? { stage: { ...block.stage } } : {}),
      })),
    };
  }

  function getPositionLabel(position) {
    return POSITION_LABELS[position] ?? cleanText(position, "未设置");
  }

  function getBlockLabel(type) {
    return BLOCK_LABELS[type] ?? cleanText(type, "卡片");
  }

  function buildAssetMap(data = {}) {
    const assetMap = new Map();
    const assets = Array.isArray(data.assetList) ? data.assetList : Array.isArray(data.assets) ? data.assets : [];
    assets.forEach((asset) => {
      if (asset?.id) {
        assetMap.set(String(asset.id), asset);
      }
    });
    if (data.assetsById instanceof Map) {
      data.assetsById.forEach((asset, id) => {
        if (id) {
          assetMap.set(String(id), asset);
        }
      });
    } else if (data.assetsById && typeof data.assetsById === "object") {
      Object.entries(data.assetsById).forEach(([id, asset]) => {
        if (id) {
          assetMap.set(String(id), asset);
        }
      });
    }
    return assetMap;
  }

  function buildCharacterMap(data = {}) {
    const characters = Array.isArray(data.characters) ? data.characters : [];
    const characterMap = new Map();
    characters.forEach((character) => {
      if (character?.id) {
        characterMap.set(String(character.id), character);
      }
    });
    if (data.charactersById instanceof Map) {
      data.charactersById.forEach((character, id) => {
        if (id) {
          characterMap.set(String(id), character);
        }
      });
    }
    return characterMap;
  }

  function buildChapterMap(data = {}) {
    return new Map(
      toArray(data.chapters).map((chapter, index) => [
        String(chapter?.id ?? ""),
        {
          id: String(chapter?.id ?? ""),
          name: cleanText(chapter?.name ?? chapter?.title, `章节 ${index + 1}`),
          order: index,
        },
      ])
    );
  }

  function getOrderedScenes(data = {}) {
    const chapterOrder = new Map(toArray(data.chapters).map((chapter, index) => [String(chapter?.id ?? ""), index]));
    return toArray(data.scenes)
      .map((scene, index) => ({ scene, index }))
      .sort((left, right) => {
        const leftChapterOrder = chapterOrder.get(String(left.scene?.chapterId ?? "")) ?? 9999;
        const rightChapterOrder = chapterOrder.get(String(right.scene?.chapterId ?? "")) ?? 9999;
        if (leftChapterOrder !== rightChapterOrder) {
          return leftChapterOrder - rightChapterOrder;
        }
        return left.index - right.index;
      })
      .map((item) => item.scene);
  }

  function getCharacterDisplayName(character, characterId = "") {
    return cleanText(character?.displayName ?? character?.name, characterId || "未选择角色");
  }

  function getExpression(character, expressionId = "") {
    const expressions = toArray(character?.expressions);
    return expressions.find((expression) => String(expression?.id ?? "") === String(expressionId ?? "")) ?? null;
  }

  function getExpressionName(character, expressionId = "") {
    const expression = getExpression(character, expressionId);
    return cleanText(expression?.name, cleanText(expressionId, "默认表情"));
  }

  function getPresentationMode(character = {}) {
    const mode = cleanText(character?.presentation?.mode, "sprite");
    return ["sprite", "layered_sprite", "live2d", "model3d"].includes(mode) ? mode : "sprite";
  }

  function collectCharacterVisualAssetIds(character = {}, expressionId = "") {
    const expression = getExpression(character, expressionId);
    const presentation = character?.presentation ?? {};
    const mode = getPresentationMode(character);
    const ids = [];

    if (mode === "live2d") {
      ids.push(presentation.live2d?.modelAssetId);
    } else if (mode === "model3d") {
      ids.push(presentation.model3d?.modelAssetId);
    }

    ids.push(expression?.spriteAssetId);
    toArray(expression?.layerAssetIds).forEach((assetId) => ids.push(assetId));
    ids.push(presentation.fallbackSpriteAssetId);
    ids.push(character.defaultSpriteId);
    return Array.from(new Set(ids.map((assetId) => cleanText(assetId)).filter(Boolean)));
  }

  function getCharacterVisualStatus(character = {}, expressionId = "", assetMap = new Map()) {
    const assetIds = collectCharacterVisualAssetIds(character, expressionId);
    if (!assetIds.length) {
      return {
        status: "missing",
        label: "没有可用立绘",
        assetNames: [],
      };
    }
    const knownAssets = assetIds.map((assetId) => assetMap.get(assetId)).filter(Boolean);
    if (!knownAssets.length) {
      return {
        status: "unknown",
        label: "立绘素材不存在",
        assetNames: assetIds,
      };
    }
    const missingFiles = knownAssets.filter((asset) => asset.fileExists === false);
    return {
      status: missingFiles.length ? "file_missing" : "ready",
      label: missingFiles.length ? "立绘文件缺失" : "立绘可用",
      assetNames: knownAssets.map((asset) => cleanText(asset.name ?? asset.fileName, asset.id)),
    };
  }

  function summarizeBlock(block = {}, index = 0) {
    const label = getBlockLabel(block.type);
    const text =
      block.text ||
      block.title ||
      block.name ||
      block.assetId ||
      toArray(block.options)
        .map((option) => option?.text)
        .filter(Boolean)
        .join(" / ");
    const summary = cleanText(text);
    return summary ? `第 ${index + 1} 张 · ${label} · ${summary.slice(0, 32)}` : `第 ${index + 1} 张 · ${label}`;
  }

  function isStoryContentBlock(block = {}) {
    return ["background", "dialogue", "narration", "character_show", "choice", "video_play", "credits_roll", "wait"].includes(
      block.type
    );
  }

  function pushIssue(issues, severity, code, title, detail, context = {}) {
    issues.push({ severity, code, title, detail, ...context });
  }

  function getIssueWeight(issue = {}) {
    if (issue.severity === "blocker") {
      return 100;
    }
    if (issue.severity === "warn") {
      return 60;
    }
    return 20;
  }

  function getStageIssueToneLabel(status = "") {
    if (status === "blocker") {
      return "阻塞";
    }
    if (status === "warn") {
      return "复查";
    }
    if (status === "tip") {
      return "润色";
    }
    return "正常";
  }

  function addStageEvent(events, event) {
    events.push({
      status: event.issues?.some((issue) => issue.severity === "blocker")
        ? "blocker"
        : event.issues?.some((issue) => issue.severity === "warn")
          ? "warn"
          : event.issues?.length
            ? "tip"
            : "good",
      ...event,
    });
  }

  function inspectCharacterVisual(block, character, assetMap, issues, context) {
    const visual = getCharacterVisualStatus(character, block.expressionId, assetMap);
    if (visual.status === "missing") {
      pushIssue(issues, "blocker", "character_visual_missing", "角色没有可用立绘", "角色没有默认立绘、表情立绘、差分图层或高级模型兜底。", context);
    } else if (visual.status === "unknown") {
      pushIssue(issues, "blocker", "character_visual_unknown_asset", "角色立绘素材不存在", `当前引用：${visual.assetNames.join(" / ")}`, context);
    } else if (visual.status === "file_missing") {
      pushIssue(issues, "blocker", "character_visual_file_missing", "角色立绘文件缺失", `请补齐：${visual.assetNames.join(" / ")}`, context);
    }
    return visual;
  }

  function formatVisualStatusLabel(visual = null) {
    if (!visual) {
      return "未检查立绘";
    }
    return [visual.label, toArray(visual.assetNames).join(" / ")].filter(Boolean).join("：");
  }

  function inspectSceneStage(scene = {}, context = {}) {
    const blocks = toArray(scene.blocks);
    const sceneName = cleanText(scene.name ?? scene.title, `场景 ${context.sceneIndex + 1}`);
    const chapterName = context.chapter?.name ?? "未分章";
    const events = [];
    const compositionRows = [];
    const sceneIssues = [];
    const visibleCharacters = new Map();
    let hasBackground = false;
    let hasStoryContent = false;
    let firstStoryBlockHadBackground = true;
    let firstStageBlock = null;
    let firstDialogueLikeBlock = null;
    let firstBackgroundBlockIndex = -1;
    let firstCharacterShowBlockIndex = -1;

    blocks.forEach((block, blockIndex) => {
      const baseContext = {
        chapterName,
        sceneName,
        sceneId: cleanText(scene.id),
        blockId: cleanText(block.id),
        blockIndex,
        blockLabel: summarizeBlock(block, blockIndex),
      };

      if (isStoryContentBlock(block) && !firstStageBlock) {
        firstStageBlock = {
          type: cleanText(block.type),
          typeLabel: getBlockLabel(block.type),
          blockId: baseContext.blockId,
          blockIndex,
          blockLabel: baseContext.blockLabel,
        };
      }
      if (["dialogue", "narration", "choice"].includes(block.type) && !firstDialogueLikeBlock) {
        firstDialogueLikeBlock = {
          type: cleanText(block.type),
          typeLabel: getBlockLabel(block.type),
          blockId: baseContext.blockId,
          blockIndex,
          blockLabel: baseContext.blockLabel,
        };
      }
      if (block.type === "background" && firstBackgroundBlockIndex < 0) {
        firstBackgroundBlockIndex = blockIndex;
      }
      if (block.type === "character_show" && firstCharacterShowBlockIndex < 0) {
        firstCharacterShowBlockIndex = blockIndex;
      }

      if (isStoryContentBlock(block) && block.type !== "background") {
        hasStoryContent = true;
        if (!hasBackground && firstStoryBlockHadBackground) {
          firstStoryBlockHadBackground = false;
        }
      }

      if (block.type === "background") {
        const assetId = cleanText(block.assetId);
        const asset = context.assetMap.get(assetId);
        const issues = [];
        if (!assetId) {
          pushIssue(issues, "blocker", "background_missing_asset", "背景卡未选择素材", "这张背景卡没有绑定背景素材。", baseContext);
        } else if (!asset) {
          pushIssue(issues, "blocker", "background_unknown_asset", "背景素材不存在", `素材 ${assetId} 不在当前素材库中。`, baseContext);
        } else if (asset.fileExists === false) {
          pushIssue(issues, "blocker", "background_file_missing", "背景文件缺失", "素材条目存在，但真实背景文件暂时不可用。", baseContext);
        }
        hasBackground = true;
        sceneIssues.push(...issues);
        addStageEvent(events, {
          type: "background",
          typeLabel: "背景",
          characterName: "",
          expressionName: "",
          positionLabel: "",
          assetStatusLabel: asset ? cleanText(asset.name, assetId) : assetId || "未选择背景",
          cue: summarizeBlock(block, blockIndex),
          issues,
          ...baseContext,
        });
        return;
      }

      if (block.type === "character_show") {
        const characterId = cleanText(block.characterId);
        const character = context.characterMap.get(characterId);
        const issues = [];
        if (!characterId) {
          pushIssue(issues, "blocker", "character_show_missing_character", "登场卡未选择角色", "这张角色登场卡没有绑定角色。", baseContext);
        } else if (!character) {
          pushIssue(issues, "blocker", "character_show_unknown_character", "登场角色不存在", `角色 ${characterId} 不在当前角色表中。`, baseContext);
        }
        if (character && block.expressionId && !getExpression(character, block.expressionId)) {
          pushIssue(issues, "blocker", "character_expression_missing", "角色表情不存在", `表情 ${block.expressionId} 不在角色表情列表中。`, baseContext);
        }
        const visual = character ? inspectCharacterVisual(block, character, context.assetMap, issues, baseContext) : null;
        const stage = normalizeCharacterStage(block.stage);
        const position = getSafePositionValue(block.position, cleanText(character?.defaultPosition, "center"));
        if (characterId) {
          visibleCharacters.set(characterId, {
            characterId,
            characterName: getCharacterDisplayName(character, characterId),
            expressionName: character ? getExpressionName(character, block.expressionId) : cleanText(block.expressionId),
            position,
            stage,
          });
        }
        const composition = inspectStageComposition(visibleCharacters, issues, baseContext);
        compositionRows.push(composition);
        sceneIssues.push(...issues);
        addStageEvent(events, {
          type: "character_show",
          typeLabel: "登场",
          characterName: getCharacterDisplayName(character, characterId),
          expressionName: character ? getExpressionName(character, block.expressionId) : cleanText(block.expressionId, "未设置表情"),
          positionLabel: getPositionLabel(position),
          stage,
          composition,
          assetStatusLabel: formatVisualStatusLabel(visual),
          cue: summarizeBlock(block, blockIndex),
          issues,
          ...baseContext,
        });
        return;
      }

      if (block.type === "character_hide") {
        const characterId = cleanText(block.characterId);
        const character = context.characterMap.get(characterId);
        const issues = [];
        if (!characterId) {
          pushIssue(issues, "blocker", "character_hide_missing_character", "退场卡未选择角色", "这张角色退场卡没有绑定角色。", baseContext);
        } else if (!character) {
          pushIssue(issues, "blocker", "character_hide_unknown_character", "退场角色不存在", `角色 ${characterId} 不在当前角色表中。`, baseContext);
        } else if (!visibleCharacters.has(characterId)) {
          pushIssue(issues, "tip", "character_hide_not_visible", "退场角色当前不在舞台", "运行时会尝试退场，但这通常说明前面缺少登场卡或顺序需要复查。", baseContext);
        }
        visibleCharacters.delete(characterId);
        sceneIssues.push(...issues);
        addStageEvent(events, {
          type: "character_hide",
          typeLabel: "退场",
          characterName: getCharacterDisplayName(character, characterId),
          expressionName: "",
          positionLabel: "",
          assetStatusLabel: "",
          cue: summarizeBlock(block, blockIndex),
          issues,
          ...baseContext,
        });
        return;
      }

      if (block.type === "dialogue") {
        const characterId = cleanText(block.speakerId);
        const character = context.characterMap.get(characterId);
        const issues = [];
        if (!characterId) {
          pushIssue(issues, "blocker", "dialogue_missing_speaker", "台词卡未选择说话人", "这句台词没有绑定角色。", baseContext);
        } else if (!character) {
          pushIssue(issues, "blocker", "dialogue_unknown_speaker", "说话角色不存在", `角色 ${characterId} 不在当前角色表中。`, baseContext);
        } else if (!visibleCharacters.has(characterId)) {
          pushIssue(
            issues,
            "warn",
            "dialogue_speaker_not_visible",
            "说话人未提前登场",
            "预览会自动把说话人补到默认位置，但正式演出建议先放一张角色登场卡来控制站位和转场。",
            baseContext
          );
        }
        if (character && block.expressionId && !getExpression(character, block.expressionId)) {
          pushIssue(issues, "blocker", "dialogue_expression_missing", "台词表情不存在", `表情 ${block.expressionId} 不在角色表情列表中。`, baseContext);
        }
        const visual = character ? inspectCharacterVisual(block, character, context.assetMap, issues, baseContext) : null;
        if (characterId && character) {
          const previousVisible = visibleCharacters.get(characterId);
          visibleCharacters.set(characterId, {
            characterId,
            characterName: getCharacterDisplayName(character, characterId),
            expressionName: getExpressionName(character, block.expressionId),
            position: previousVisible?.position ?? getSafePositionValue(character.defaultPosition, "center"),
            stage: previousVisible?.stage ?? normalizeCharacterStage({}),
          });
        }
        const composition = inspectStageComposition(visibleCharacters, issues, baseContext, { speakerId: characterId });
        compositionRows.push(composition);
        sceneIssues.push(...issues);
        const visibleSpeaker = visibleCharacters.get(characterId);
        addStageEvent(events, {
          type: "dialogue",
          typeLabel: "说话",
          characterName: getCharacterDisplayName(character, characterId),
          expressionName: character ? getExpressionName(character, block.expressionId) : cleanText(block.expressionId, "未设置表情"),
          positionLabel: getPositionLabel(visibleSpeaker?.position ?? character?.defaultPosition ?? "center"),
          stage: visibleSpeaker?.stage ?? normalizeCharacterStage({}),
          composition,
          assetStatusLabel: formatVisualStatusLabel(visual),
          cue: summarizeBlock(block, blockIndex),
          issues,
          ...baseContext,
        });
      }
    });

    if (hasStoryContent && !blocks.some((block) => block.type === "background" && cleanText(block.assetId))) {
      pushIssue(sceneIssues, "warn", "scene_without_background", "内容场景没有背景卡", "这个场景有正文或角色演出，但没有明确切背景。", {
        chapterName,
        sceneName,
        sceneId: cleanText(scene.id),
        blockId: "",
        blockIndex: -1,
        blockLabel: sceneName,
      });
    } else if (hasStoryContent && !firstStoryBlockHadBackground) {
      pushIssue(sceneIssues, "tip", "scene_content_before_background", "内容出现在背景之前", "场景开头先出现正文/角色，再切背景；建议确认这是不是有意为之。", {
        chapterName,
        sceneName,
        sceneId: cleanText(scene.id),
        blockId: "",
        blockIndex: -1,
        blockLabel: sceneName,
      });
    }

    const visibleCharactersAtEnd = [...visibleCharacters.values()].map((item) => {
      const stage = normalizeCharacterStage(item.stage);
      return {
        characterId: item.characterId,
        characterName: item.characterName,
        expressionName: item.expressionName,
        position: item.position,
        positionLabel: getPositionLabel(item.position),
        stage,
      };
    });
    const openingProfile = {
      firstStageBlock,
      firstDialogueLikeBlock,
      firstBackgroundBlockIndex,
      firstCharacterShowBlockIndex,
      dialogueBeforeBackground: Boolean(
        firstDialogueLikeBlock && (firstBackgroundBlockIndex < 0 || firstDialogueLikeBlock.blockIndex < firstBackgroundBlockIndex)
      ),
      dialogueBeforeCharacterShow: Boolean(
        firstDialogueLikeBlock && (firstCharacterShowBlockIndex < 0 || firstDialogueLikeBlock.blockIndex < firstCharacterShowBlockIndex)
      ),
    };

    return {
      sceneId: cleanText(scene.id),
      sceneName,
      chapterName,
      eventCount: events.length,
      visibleCharacterCountAtEnd: visibleCharacters.size,
      visibleCharactersAtEnd,
      endingCastLabel: visibleCharactersAtEnd.map((item) => item.characterName || item.characterId).filter(Boolean).join(" / "),
      hasStoryContent,
      hasBackground,
      openingProfile,
      issues: sceneIssues,
      events,
      compositionRows,
      status: sceneIssues.some((issue) => issue.severity === "blocker")
        ? "blocker"
        : sceneIssues.some((issue) => issue.severity === "warn")
          ? "warn"
          : sceneIssues.length
            ? "tip"
          : "good",
    };
  }

  const STAGE_CONTINUITY_OPENING_CODES = Object.freeze([
    "scene_without_background",
    "scene_content_before_background",
    "dialogue_speaker_not_visible",
    "dialogue_missing_speaker",
    "dialogue_unknown_speaker",
  ]);

  function getStageContinuityStatus(row = {}) {
    if (row.blockerCount > 0) {
      return "blocker";
    }
    if (row.openingIssueCount > 0 || row.dialogueBeforeStage || row.speakerAutoPlaceCount > 0) {
      return "warn";
    }
    if (row.endingCastCount > 0) {
      return "tip";
    }
    return "good";
  }

  function getStageContinuityNextAction(row = {}) {
    if (row.openingIssueCodes?.includes("scene_without_background")) {
      return "先补背景卡";
    }
    if (row.openingIssueCodes?.includes("dialogue_missing_speaker") || row.openingIssueCodes?.includes("dialogue_unknown_speaker")) {
      return "修说话人";
    }
    if (row.openingIssueCodes?.includes("dialogue_speaker_not_visible") || row.dialogueBeforeStage) {
      return "补登场卡";
    }
    if (row.openingIssueCodes?.includes("scene_content_before_background")) {
      return "调整开场顺序";
    }
    if (row.endingCastCount > 0) {
      return "确认是否退场";
    }
    return row.hasStoryContent ? "可继续制作" : "继续补正文";
  }

  function buildStageContinuityReasons(row = {}) {
    const reasons = [];
    if (row.openingIssueCodes?.includes("scene_without_background")) {
      reasons.push("缺开场背景");
    }
    if (row.openingIssueCodes?.includes("scene_content_before_background")) {
      reasons.push("正文早于背景");
    }
    if (row.openingIssueCodes?.includes("dialogue_speaker_not_visible")) {
      reasons.push("说话人未登场");
    }
    if (row.openingIssueCodes?.some((code) => code === "dialogue_missing_speaker" || code === "dialogue_unknown_speaker")) {
      reasons.push("说话人配置异常");
    }
    if (row.dialogueBeforeStage && !reasons.includes("正文早于背景")) {
      reasons.push("开头先出现正文");
    }
    if (row.endingCastCount > 0) {
      reasons.push(`结尾仍有 ${row.endingCastCount} 名角色在场`);
    }
    return reasons.length ? reasons.join(" / ") : "连续性清晰";
  }

  function buildStageContinuityAudit(sheet = {}) {
    const sceneReports = toArray(sheet.sceneReports);
    const rows = sceneReports.map((scene, index) => {
      const openingIssues = toArray(scene.issues).filter((issue) => STAGE_CONTINUITY_OPENING_CODES.includes(issue.code));
      const openingIssueCodes = Array.from(new Set(openingIssues.map((issue) => issue.code)));
      const blockerCount = openingIssues.filter((issue) => issue.severity === "blocker").length;
      const speakerAutoPlaceCount = openingIssues.filter((issue) => issue.code === "dialogue_speaker_not_visible").length;
      const openingProfile = scene.openingProfile ?? {};
      const dialogueBeforeStage = Boolean(openingProfile.dialogueBeforeBackground || openingProfile.dialogueBeforeCharacterShow);
      const endingCast = toArray(scene.visibleCharactersAtEnd);
      const row = {
        sceneId: scene.sceneId,
        sceneName: scene.sceneName,
        chapterName: scene.chapterName,
        sceneIndex: index,
        hasStoryContent: Boolean(scene.hasStoryContent),
        openingCue: openingProfile.firstStageBlock?.blockLabel ?? "未开始演出",
        firstDialogueCue: openingProfile.firstDialogueLikeBlock?.blockLabel ?? "",
        openingIssueCount: openingIssues.length,
        openingIssueCodes,
        blockerCount,
        speakerAutoPlaceCount,
        dialogueBeforeStage,
        endingCastCount: endingCast.length,
        endingCast,
        endingCastLabel: endingCast.map((item) => item.characterName || item.characterId).filter(Boolean).join(" / "),
      };
      row.status = getStageContinuityStatus(row);
      row.statusLabel = getStageIssueToneLabel(row.status);
      row.reason = buildStageContinuityReasons(row);
      row.nextAction = getStageContinuityNextAction(row);
      return row;
    });
    const reviewRows = rows.filter((row) => row.status !== "good");
    return {
      rows,
      reviewRows,
      summary: {
        sceneCount: rows.length,
        reviewSceneCount: reviewRows.length,
        blockedSceneCount: rows.filter((row) => row.status === "blocker").length,
        warningSceneCount: rows.filter((row) => row.status === "warn").length,
        tipSceneCount: rows.filter((row) => row.status === "tip").length,
        openingRiskSceneCount: rows.filter((row) => row.openingIssueCount > 0 || row.dialogueBeforeStage).length,
        dialogueBeforeStageSceneCount: rows.filter((row) => row.dialogueBeforeStage).length,
        speakerAutoPlaceSceneCount: rows.filter((row) => row.speakerAutoPlaceCount > 0).length,
        endingCastSceneCount: rows.filter((row) => row.endingCastCount > 0).length,
        endingCastCharacterCount: rows.reduce((total, row) => total + row.endingCastCount, 0),
      },
    };
  }

  function buildStageDirectionSheet(data = {}) {
    const assetMap = buildAssetMap(data);
    const characterMap = buildCharacterMap(data);
    const chapterMap = buildChapterMap(data);
    const scenes = getOrderedScenes(data);
    const sceneReports = scenes.map((scene, sceneIndex) =>
      inspectSceneStage(scene, {
        sceneIndex,
        assetMap,
        characterMap,
        chapter: chapterMap.get(String(scene?.chapterId ?? "")) ?? { name: "未分章" },
      })
    );
    const events = sceneReports.flatMap((scene) => scene.events);
    const compositionRows = sceneReports.flatMap((scene) => scene.compositionRows ?? []);
    const issues = sceneReports
      .flatMap((scene) => scene.issues)
      .sort((left, right) => getIssueWeight(right) - getIssueWeight(left) || left.sceneName.localeCompare(right.sceneName, "zh-CN"));
    const summary = {
      sceneCount: sceneReports.length,
      eventCount: events.length,
      stagedSceneCount: sceneReports.filter((scene) => scene.eventCount > 0).length,
      missingBackgroundSceneCount: sceneReports.filter((scene) => scene.issues.some((issue) => issue.code === "scene_without_background")).length,
      speakerAutoPlaceCount: issues.filter((issue) => issue.code === "dialogue_speaker_not_visible").length,
      missingVisualCount: issues.filter((issue) => issue.code.includes("visual") || issue.code.includes("expression")).length,
      compositionCheckpointCount: compositionRows.length,
      compositionRiskCount: compositionRows.filter((row) => row.status !== "good").length,
      overlapRiskCount: issues.filter((issue) => issue.code === "stage_geometry_overlap" || issue.code === "stage_position_overlap").length,
      crowdedStageCount: issues.filter((issue) => issue.code === "stage_too_many_characters" || issue.code === "stage_large_sprite_crowding").length,
      lowOpacitySpeakerCount: issues.filter((issue) => issue.code === "stage_speaker_low_opacity").length,
      layerConflictCount: issues.filter((issue) => issue.code === "stage_layer_overlap").length,
      blockerCount: issues.filter((issue) => issue.severity === "blocker").length,
      warningCount: issues.filter((issue) => issue.severity === "warn").length,
      tipCount: issues.filter((issue) => issue.severity === "tip").length,
    };
    const autoFixPlan = buildStageDirectionAutoFixPlan(data);
    summary.autoFixSceneCount = autoFixPlan.changedSceneCount;
    summary.autoFixBlockCount = autoFixPlan.changedBlockCount;
    summary.autoFixOperationCount = autoFixPlan.operationCount;
    const continuityAudit = buildStageContinuityAudit({ sceneReports, events, compositionRows, issues, summary });
    summary.continuityReviewSceneCount = continuityAudit.summary.reviewSceneCount;
    summary.continuityOpeningRiskSceneCount = continuityAudit.summary.openingRiskSceneCount;
    summary.continuityEndingCastSceneCount = continuityAudit.summary.endingCastSceneCount;
    summary.continuityEndingCastCharacterCount = continuityAudit.summary.endingCastCharacterCount;

    return {
      projectTitle: cleanText(data.project?.title, "Canvasia Project"),
      sceneReports,
      events,
      compositionRows,
      issues,
      summary,
      autoFixPlan,
      continuityAudit,
    };
  }

  function buildStageDirectionAutoFixSummary(scenePlans = []) {
    const safePlans = toArray(scenePlans);
    const blockCount = safePlans.reduce((total, plan) => total + (plan.changedBlockCount ?? 0), 0);
    const operationCount = safePlans.reduce((total, plan) => total + (plan.operationCount ?? 0), 0);
    if (!safePlans.length) {
      return "角色舞台基础参数已经比较完整";
    }
    return `已准备修复 ${safePlans.length} 个场景、${blockCount} 张角色卡、${operationCount} 个舞台参数`;
  }

  function getStageDirectionAutoFixDefaults(options = {}) {
    return {
      characterShowTransition: getSafeCharacterTransitionValue(
        options.characterShowTransition,
        STAGE_DIRECTION_AUTO_FIX_DEFAULTS.characterShowTransition
      ),
      characterHideTransition: getSafeCharacterTransitionValue(
        options.characterHideTransition,
        STAGE_DIRECTION_AUTO_FIX_DEFAULTS.characterHideTransition
      ),
      characterShowDurationMs: getSafeTransitionDurationMs(
        options.characterShowDurationMs,
        STAGE_DIRECTION_AUTO_FIX_DEFAULTS.characterShowDurationMs
      ),
      characterHideDurationMs: getSafeTransitionDurationMs(
        options.characterHideDurationMs,
        STAGE_DIRECTION_AUTO_FIX_DEFAULTS.characterHideDurationMs
      ),
    };
  }

  function pushStageAutoFixOperation(operations, changedBlockIds, block, blockIndex, label, detail) {
    changedBlockIds.add(cleanText(block?.id) || `block_${blockIndex + 1}`);
    operations.push({
      blockId: cleanText(block?.id),
      blockIndex,
      label,
      detail,
    });
  }

  function applyCharacterShowAutoFix(block, blockIndex, context = {}) {
    const operations = context.operations;
    const changedBlockIds = context.changedBlockIds;
    const defaults = context.defaults;
    const character = context.characterMap.get(cleanText(block.characterId));
    const fallbackPosition = getSafePositionValue(character?.defaultPosition, "center");
    const nextPosition = getSafePositionValue(block.position, fallbackPosition);
    if (cleanText(block.position) !== nextPosition) {
      block.position = nextPosition;
      pushStageAutoFixOperation(
        operations,
        changedBlockIds,
        block,
        blockIndex,
        "补角色站位",
        `站位已设为 ${getPositionLabel(nextPosition)}。`
      );
    }

    const transition = getSafeCharacterTransitionValue(block.transition, defaults.characterShowTransition);
    if (!cleanText(block.transition) || transition === "none") {
      block.transition = defaults.characterShowTransition;
      pushStageAutoFixOperation(
        operations,
        changedBlockIds,
        block,
        blockIndex,
        "补登场转场",
        `角色登场已改为 ${defaults.characterShowTransition === "fade" ? "淡入" : defaults.characterShowTransition}。`
      );
    } else if (block.transition !== transition) {
      block.transition = transition;
      pushStageAutoFixOperation(operations, changedBlockIds, block, blockIndex, "修正登场转场", "无法识别的转场已改为安全值。");
    }

    const durationMs = getSafeTransitionDurationMs(block.transitionDurationMs, defaults.characterShowDurationMs);
    if (durationMs <= 0 || Number(block.transitionDurationMs) !== durationMs) {
      block.transitionDurationMs = durationMs > 0 ? durationMs : defaults.characterShowDurationMs;
      pushStageAutoFixOperation(
        operations,
        changedBlockIds,
        block,
        blockIndex,
        "补登场时长",
        `登场转场时长已设为 ${block.transitionDurationMs}ms。`
      );
    }

    const normalizedStage = normalizeCharacterStage(block.stage);
    const hadStage = block.stage && typeof block.stage === "object";
    if (!hadStage || !isSameStage(normalizedStage, block.stage)) {
      block.stage = normalizedStage;
      pushStageAutoFixOperation(
        operations,
        changedBlockIds,
        block,
        blockIndex,
        hadStage ? "修正立绘舞台参数" : "补立绘舞台参数",
        "已补齐缩放、透明度、层级和偏移参数。"
      );
    }
  }

  function applyCharacterHideAutoFix(block, blockIndex, context = {}) {
    const operations = context.operations;
    const changedBlockIds = context.changedBlockIds;
    const defaults = context.defaults;
    const transition = getSafeCharacterTransitionValue(block.transition, defaults.characterHideTransition);
    if (!cleanText(block.transition) || transition === "none") {
      block.transition = defaults.characterHideTransition;
      pushStageAutoFixOperation(
        operations,
        changedBlockIds,
        block,
        blockIndex,
        "补退场转场",
        `角色退场已改为 ${defaults.characterHideTransition === "fade" ? "淡出" : defaults.characterHideTransition}。`
      );
    } else if (block.transition !== transition) {
      block.transition = transition;
      pushStageAutoFixOperation(operations, changedBlockIds, block, blockIndex, "修正退场转场", "无法识别的转场已改为安全值。");
    }

    const durationMs = getSafeTransitionDurationMs(block.transitionDurationMs, defaults.characterHideDurationMs);
    if (durationMs <= 0 || Number(block.transitionDurationMs) !== durationMs) {
      block.transitionDurationMs = durationMs > 0 ? durationMs : defaults.characterHideDurationMs;
      pushStageAutoFixOperation(
        operations,
        changedBlockIds,
        block,
        blockIndex,
        "补退场时长",
        `退场转场时长已设为 ${block.transitionDurationMs}ms。`
      );
    }
  }

  function buildStageDirectionAutoFixPlan(data = {}, options = {}) {
    const defaults = getStageDirectionAutoFixDefaults(options);
    const characterMap = buildCharacterMap(data);
    const chapterMap = buildChapterMap(data);
    const scenePlans = [];

    getOrderedScenes(data).forEach((scene, sceneIndex) => {
      const updatedScene = cloneSceneForStageFix(scene);
      const operations = [];
      const changedBlockIds = new Set();

      toArray(updatedScene.blocks).forEach((block, blockIndex) => {
        const context = { characterMap, defaults, operations, changedBlockIds };
        if (block?.type === "character_show") {
          applyCharacterShowAutoFix(block, blockIndex, context);
        } else if (block?.type === "character_hide") {
          applyCharacterHideAutoFix(block, blockIndex, context);
        }
      });

      if (operations.length > 0) {
        const chapter = chapterMap.get(String(scene?.chapterId ?? "")) ?? {
          id: String(scene?.chapterId ?? ""),
          name: "未分章",
        };
        scenePlans.push({
          scene: updatedScene,
          sceneId: cleanText(scene?.id),
          sceneName: cleanText(scene?.name ?? scene?.title, `场景 ${sceneIndex + 1}`),
          chapterId: chapter.id,
          chapterName: chapter.name,
          operations,
          operationCount: operations.length,
          changedBlockCount: changedBlockIds.size,
          firstChangedBlockId: operations[0]?.blockId ?? "",
          firstChangedIndex: operations[0]?.blockIndex ?? 0,
        });
      }
    });

    return {
      changed: scenePlans.length > 0,
      scenePlans,
      changedSceneCount: scenePlans.length,
      changedBlockCount: scenePlans.reduce((total, plan) => total + (plan.changedBlockCount ?? 0), 0),
      operationCount: scenePlans.reduce((total, plan) => total + (plan.operationCount ?? 0), 0),
      firstChangedSceneId: scenePlans[0]?.sceneId ?? "",
      firstChangedBlockId: scenePlans[0]?.firstChangedBlockId ?? "",
      firstChangedIndex: scenePlans[0]?.firstChangedIndex ?? 0,
      summary: buildStageDirectionAutoFixSummary(scenePlans),
    };
  }

  function getStageDirectionStatusDigest(sheet = {}) {
    const summary = sheet.summary ?? {};
    if ((summary.eventCount ?? 0) === 0) {
      return {
        status: "empty",
        tone: "soft",
        title: "还没有角色舞台调度",
        detail: "项目里暂时没有背景、角色登场、退场或角色台词事件。",
      };
    }
    if ((summary.blockerCount ?? 0) > 0) {
      return {
        status: "blocked",
        tone: "danger",
        title: `有 ${summary.blockerCount} 个舞台阻塞问题`,
        detail: "优先修复缺角色、缺立绘、坏表情或缺背景素材。",
      };
    }
    if ((summary.warningCount ?? 0) > 0) {
      return {
        status: "warn",
        tone: "warn",
        title: `有 ${summary.warningCount} 个舞台连续性提醒`,
        detail: "作品可以继续推进，但建议复查说话人登场、场景背景和站位节奏。",
      };
    }
    return {
      status: "ready",
      tone: "good",
      title: "角色舞台调度可用于发布前检查",
      detail: "当前角色登场、退场、说话和背景调度没有明显结构问题。",
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

  function formatCsvCell(value) {
    const text = String(value ?? "");
    return `"${text.replaceAll('"', '""')}"`;
  }

  function buildCsv(headers = [], rows = []) {
    return [
      toArray(headers).map(formatCsvCell).join(","),
      ...toArray(rows).map((row) => toArray(row).map(formatCsvCell).join(",")),
    ].join("\n");
  }

  function buildStageDirectionSheetMarkdown(sheet = {}, context = {}) {
    const digest = getStageDirectionStatusDigest(sheet);
    const summary = sheet.summary ?? {};
    const continuityAudit = sheet.continuityAudit ?? buildStageContinuityAudit(sheet);
    const projectTitle = context.projectTitle || sheet.projectTitle || "Canvasia Project";
    const generatedAt = context.generatedAt || new Date().toISOString();
    const eventRows = toArray(sheet.events).slice(0, 140).map((event, index) => [
      `${index + 1}`,
      event.chapterName,
      event.sceneName,
      event.typeLabel,
      event.characterName,
      event.expressionName,
      event.positionLabel,
      event.assetStatusLabel,
      event.cue,
      event.composition?.riskLabel ?? "",
      event.status === "blocker" ? "阻塞" : event.status === "warn" ? "复查" : event.status === "tip" ? "润色" : "正常",
    ]);
    const compositionRows = toArray(sheet.compositionRows)
      .filter((row) => row.status !== "good")
      .slice(0, 100)
      .map((row, index) => [
        `${index + 1}`,
        row.status === "blocker" ? "阻塞" : row.status === "warn" ? "复查" : "润色",
        row.chapterName,
        row.sceneName,
        row.blockLabel,
        `${row.visibleCount ?? 0}`,
        row.characterNames,
        row.riskLabel,
      ]);
    const continuityRows = toArray(continuityAudit.reviewRows)
      .slice(0, 100)
      .map((row, index) => [
        `${index + 1}`,
        row.statusLabel,
        row.chapterName,
        row.sceneName,
        row.openingCue,
        row.endingCastLabel || "无",
        row.reason,
        row.nextAction,
      ]);
    const issueRows = toArray(sheet.issues).slice(0, 140).map((issue, index) => [
      `${index + 1}`,
      issue.severity === "blocker" ? "阻塞" : issue.severity === "warn" ? "提醒" : "润色",
      issue.chapterName,
      issue.sceneName,
      issue.title,
      issue.detail,
    ]);

    return `\uFEFF${[
      `# ${projectTitle} 角色舞台调度表`,
      "",
      `导出时间：${generatedAt}`,
      `状态：${digest.title}`,
      `说明：${digest.detail}`,
      "",
      "## 总览",
      "",
      buildMarkdownTable(
        ["项目", "数量"],
        [
          ["场景", `${summary.sceneCount ?? 0}`],
          ["舞台事件", `${summary.eventCount ?? 0}`],
          ["有调度场景", `${summary.stagedSceneCount ?? 0}`],
          ["无背景内容场景", `${summary.missingBackgroundSceneCount ?? 0}`],
          ["说话人自动补位", `${summary.speakerAutoPlaceCount ?? 0}`],
          ["立绘/表情缺口", `${summary.missingVisualCount ?? 0}`],
          ["构图检查点", `${summary.compositionCheckpointCount ?? 0}`],
          ["构图风险", `${summary.compositionRiskCount ?? 0}`],
          ["遮挡/重叠风险", `${summary.overlapRiskCount ?? 0}`],
          ["拥挤/大比例风险", `${summary.crowdedStageCount ?? 0}`],
          ["说话人过淡", `${summary.lowOpacitySpeakerCount ?? 0}`],
          ["连续性复查场景", `${summary.continuityReviewSceneCount ?? 0}`],
          ["开场调度风险", `${summary.continuityOpeningRiskSceneCount ?? 0}`],
          ["结尾仍有角色", `${summary.continuityEndingCastSceneCount ?? 0}`],
          ["可自动补齐场景", `${summary.autoFixSceneCount ?? 0}`],
          ["可自动补齐参数", `${summary.autoFixOperationCount ?? 0}`],
          ["阻塞问题", `${summary.blockerCount ?? 0}`],
          ["复查提醒", `${summary.warningCount ?? 0}`],
        ]
      ),
      "",
      "## 舞台事件列表",
      "",
      buildMarkdownTable(["序号", "章节", "场景", "类型", "角色", "表情", "站位", "素材", "位置", "构图", "状态"], eventRows) ||
        "当前没有可列出的舞台事件。",
      "",
      "## 舞台构图检查",
      "",
      buildMarkdownTable(["序号", "级别", "章节", "场景", "检查点", "同屏人数", "角色", "风险"], compositionRows) ||
        "当前没有明显站位、遮挡、图层或透明度构图风险。",
      "",
      "## 场景连续性审计",
      "",
      buildMarkdownTable(["序号", "级别", "章节", "场景", "开场", "结尾在场", "原因", "下一步"], continuityRows) ||
        "当前没有明显开场调度或结尾留场风险。",
      "",
      "## 需要复查的问题",
      "",
      buildMarkdownTable(["序号", "级别", "章节", "场景", "问题", "说明"], issueRows) ||
        "当前没有明显角色舞台连续性问题。",
      "",
    ].join("\n")}`;
  }

  function buildStageDirectionSheetCsv(sheet = {}) {
    const continuityBySceneId = new Map(toArray(sheet.continuityAudit?.rows).map((row) => [row.sceneId, row]));
    const rows = toArray(sheet.events).map((event, index) => [
      `${index + 1}`,
      event.chapterName,
      event.sceneName,
      event.blockIndex + 1,
      event.typeLabel,
      event.characterName,
      event.expressionName,
      event.positionLabel,
      event.assetStatusLabel,
      event.cue,
      event.composition?.visibleCount ?? "",
      event.composition?.riskLabel ?? "",
      continuityBySceneId.get(event.sceneId)?.statusLabel ?? "",
      continuityBySceneId.get(event.sceneId)?.endingCastLabel ?? "",
      continuityBySceneId.get(event.sceneId)?.nextAction ?? "",
      event.status,
      toArray(event.issues).map((issue) => issue.title).join(" / "),
    ]);
    return `\uFEFF${buildCsv(
      [
        "序号",
        "章节",
        "场景",
        "卡片",
        "类型",
        "角色",
        "表情",
        "站位",
        "素材状态",
        "位置",
        "同屏人数",
        "构图风险",
        "连续性状态",
        "结尾在场",
        "连续性下一步",
        "状态",
        "问题",
      ],
      rows
    )}\n`;
  }

  global.CanvasiaEditorStageDirectionSheet = Object.freeze({
    STAGE_DIRECTION_AUTO_FIX_DEFAULTS,
    buildStageDirectionSheet,
    buildStageDirectionAutoFixPlan,
    buildStageDirectionAutoFixSummary,
    buildStageContinuityAudit,
    getStageDirectionStatusDigest,
    buildStageDirectionSheetMarkdown,
    buildStageDirectionSheetCsv,
    getCharacterVisualStatus,
  });
})(typeof window !== "undefined" ? window : globalThis);
