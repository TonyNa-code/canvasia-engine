(function attachAssetUsageMapTools(global) {
  const storyBlockCatalogTools = global.CanvasiaEditorStoryBlockCatalog || {};

  const FALLBACK_BLOCK_LABELS = Object.freeze({
    background: "切换背景",
    dialogue: "台词",
    narration: "旁白",
    character_show: "显示角色",
    character_move: "角色舞台动作",
    character_hide: "隐藏角色",
    music_play: "播放音乐",
    music_stop: "停止音乐",
    sfx_play: "播放音效",
    video_play: "播放视频",
    credits_roll: "片尾字幕",
    wait: "等待停顿",
    particle_effect: "粒子特效",
    screen_shake: "屏幕震动",
    screen_flash: "闪屏",
    screen_fade: "黑场淡入淡出",
    camera_zoom: "镜头推近拉远",
    camera_pan: "镜头平移",
    screen_filter: "回忆滤镜",
    depth_blur: "景深模糊",
    jump: "跳转",
    variable_set: "设置变量",
    variable_add: "修改变量",
    choice: "选项",
    condition: "条件判断",
  });

  const BLOCK_LABELS = Object.freeze({
    ...FALLBACK_BLOCK_LABELS,
    ...(storyBlockCatalogTools.BLOCK_LABELS ?? {}),
  });

  const PROJECT_UI_ASSET_FIELDS = Object.freeze([
    Object.freeze({ group: "对话框", key: "dialogBoxConfig.panelAssetId", label: "文本框自定义贴图" }),
    Object.freeze({ group: "成品 UI", key: "gameUiConfig.fontAssetId", label: "界面字体" }),
    Object.freeze({ group: "成品 UI", key: "gameUiConfig.titleBackgroundAssetId", label: "标题背景" }),
    Object.freeze({ group: "成品 UI", key: "gameUiConfig.titleLogoAssetId", label: "标题 Logo" }),
    Object.freeze({ group: "成品 UI", key: "gameUiConfig.panelFrameAssetId", label: "通用面板九宫格" }),
    Object.freeze({ group: "成品 UI", key: "gameUiConfig.buttonFrameAssetId", label: "按钮默认九宫格" }),
    Object.freeze({ group: "成品 UI", key: "gameUiConfig.buttonHoverFrameAssetId", label: "按钮悬停九宫格" }),
    Object.freeze({ group: "成品 UI", key: "gameUiConfig.buttonPressedFrameAssetId", label: "按钮按下九宫格" }),
    Object.freeze({ group: "成品 UI", key: "gameUiConfig.buttonDisabledFrameAssetId", label: "按钮禁用九宫格" }),
    Object.freeze({ group: "成品 UI", key: "gameUiConfig.saveSlotFrameAssetId", label: "存档卡片九宫格" }),
    Object.freeze({ group: "成品 UI", key: "gameUiConfig.systemPanelFrameAssetId", label: "系统弹窗九宫格" }),
    Object.freeze({ group: "成品 UI", key: "gameUiConfig.uiOverlayAssetId", label: "全局叠层纹理" }),
  ]);

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

  function getPathValue(source, dottedPath) {
    return String(dottedPath ?? "")
      .split(".")
      .filter(Boolean)
      .reduce((cursor, part) => (cursor && typeof cursor === "object" ? cursor[part] : undefined), source);
  }

  function getCharacterList(data = {}) {
    return Array.isArray(data.characters)
      ? data.characters
      : Array.isArray(data.characters?.characters)
        ? data.characters.characters
        : [];
  }

  function getCharacterDisplayName(character = {}, fallback = "") {
    return cleanText(character.displayName ?? character.name, fallback || character.id || "未命名角色");
  }

  function getCharacterPresentation(character = {}) {
    const presentation = character.presentation && typeof character.presentation === "object" ? character.presentation : {};
    return {
      mode: cleanText(presentation.mode, "sprite"),
      fallbackSpriteAssetId: cleanText(presentation.fallbackSpriteAssetId),
      live2d: presentation.live2d && typeof presentation.live2d === "object" ? presentation.live2d : {},
      model3d: presentation.model3d && typeof presentation.model3d === "object" ? presentation.model3d : {},
    };
  }

  function addUsage(usageMap, assetId, entry) {
    const cleanAssetId = cleanText(assetId);
    if (!cleanAssetId) {
      return;
    }
    const list = usageMap.get(cleanAssetId) ?? [];
    list.push(entry);
    usageMap.set(cleanAssetId, list);
  }

  function addProjectUiUsages(usageMap, project = {}) {
    PROJECT_UI_ASSET_FIELDS.forEach((field) => {
      const assetId = getPathValue(project, field.key);
      addUsage(usageMap, assetId, {
        kind: "project",
        label: `项目 UI：${field.label}`,
        meta: `${field.group} / ${field.key}`,
      });
    });
  }

  function addCharacterExpressionUsages(usageMap, character, expression, context = {}) {
    const characterName = getCharacterDisplayName(character, context.characterId);
    const expressionName = cleanText(expression?.name, expression?.id || "表情");
    addUsage(usageMap, expression?.spriteAssetId, {
      kind: context.kind ?? "character",
      characterId: context.characterId ?? character?.id,
      sceneId: context.sceneId,
      blockId: context.blockId,
      label: `${context.labelPrefix ?? "角色表情"}：${characterName} / ${expressionName}`,
      meta: context.meta ?? "角色资料页 / 表情设置",
    });
    toArray(expression?.layerAssetIds).forEach((layerAssetId, layerIndex) => {
      addUsage(usageMap, layerAssetId, {
        kind: context.kind ?? "character",
        characterId: context.characterId ?? character?.id,
        sceneId: context.sceneId,
        blockId: context.blockId,
        label: `${context.layerLabelPrefix ?? "角色差分图层"}：${characterName} / ${expressionName}`,
        meta: context.meta
          ? `${context.meta} · 差分 ${layerIndex + 1}`
          : `角色资料页 / 表情差分 ${layerIndex + 1}`,
      });
    });
  }

  function addCharacterUsages(usageMap, characters) {
    toArray(characters).forEach((character) => {
      const characterName = getCharacterDisplayName(character);
      addUsage(usageMap, character.defaultSpriteId, {
        kind: "character",
        characterId: character.id,
        label: `角色默认立绘：${characterName}`,
        meta: "角色资料页 / 默认立绘",
      });

      const presentation = getCharacterPresentation(character);
      addUsage(usageMap, presentation.fallbackSpriteAssetId, {
        kind: "character",
        characterId: character.id,
        label: `角色高级表现兜底：${characterName}`,
        meta: "角色资料页 / 高级表现",
      });
      addUsage(usageMap, presentation.live2d.modelAssetId, {
        kind: "character",
        characterId: character.id,
        label: `角色 Live2D 模型：${characterName}`,
        meta: "角色资料页 / 高级表现",
      });
      addUsage(usageMap, presentation.model3d.modelAssetId, {
        kind: "character",
        characterId: character.id,
        label: `角色 3D 模型：${characterName}`,
        meta: "角色资料页 / 高级表现",
      });

      toArray(character.expressions).forEach((expression) => {
        addCharacterExpressionUsages(usageMap, character, expression);
      });
    });
  }

  function addStoryBlockUsages(usageMap, chapters, characterMap) {
    toArray(chapters).forEach((chapter, chapterIndex) => {
      const chapterName = cleanText(chapter?.name ?? chapter?.title, `章节 ${chapterIndex + 1}`);
      toArray(chapter?.scenes).forEach((scene) => {
        const sceneName = cleanText(scene?.name ?? scene?.title, scene?.id || "未命名场景");
        toArray(scene?.blocks).forEach((block, blockIndex) => {
          const blockLabel = BLOCK_LABELS[block?.type] ?? cleanText(block?.type, "卡片");
          const meta = `${chapterName} · 第 ${blockIndex + 1} 张卡片`;
          addUsage(usageMap, block?.assetId, {
            kind: "story",
            sceneId: scene?.id,
            blockId: block?.id,
            label: `场景：${sceneName} / ${blockLabel}`,
            meta,
          });
          addUsage(usageMap, block?.voiceAssetId, {
            kind: "story",
            sceneId: scene?.id,
            blockId: block?.id,
            label: `场景：${sceneName} / ${blockLabel}语音`,
            meta,
          });

          if (["dialogue", "character_show", "character_move"].includes(block?.type)) {
            const characterId = cleanText(block.speakerId ?? block.characterId);
            const character = characterMap.get(characterId);
            const expression = toArray(character?.expressions).find((item) => item?.id === block.expressionId);
            if (expression) {
              addCharacterExpressionUsages(usageMap, character, expression, {
                kind: "story",
                characterId,
                sceneId: scene?.id,
                blockId: block?.id,
                labelPrefix: `场景：${sceneName}`,
                layerLabelPrefix: `场景差分：${sceneName}`,
                meta,
              });
            }
          }
        });
      });
    });
  }

  function buildAssetUsageMap(data = {}) {
    const usageMap = new Map();
    const characters = getCharacterList(data);
    const characterMap = buildCollectionMap(data.charactersById);
    characters.forEach((character) => {
      if (character?.id) {
        characterMap.set(String(character.id), character);
      }
    });

    addProjectUiUsages(usageMap, data.project ?? {});
    addCharacterUsages(usageMap, characters);
    addStoryBlockUsages(usageMap, data.chapters, characterMap);
    return usageMap;
  }

  function getAssetUsageEntries(assetId, data = {}) {
    const cleanAssetId = cleanText(assetId);
    if (!cleanAssetId || !data?.assetUsage) {
      return [];
    }
    if (typeof data.assetUsage.get === "function") {
      return data.assetUsage.get(cleanAssetId) ?? [];
    }
    return Object.prototype.hasOwnProperty.call(data.assetUsage, cleanAssetId)
      ? data.assetUsage[cleanAssetId] ?? []
      : [];
  }

  function getAssetUsageCount(assetId, data = {}) {
    return getAssetUsageEntries(assetId, data).length;
  }

  global.CanvasiaEditorAssetUsageMap = {
    PROJECT_UI_ASSET_FIELDS,
    buildAssetUsageMap,
    getAssetUsageEntries,
    getAssetUsageCount,
  };
})(typeof window !== "undefined" ? window : globalThis);
