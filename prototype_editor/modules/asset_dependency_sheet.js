(function attachAssetDependencySheetTools(global) {
  const ASSET_TYPE_LABELS = Object.freeze({
    background: "背景",
    sprite: "立绘",
    cg: "CG",
    bgm: "音乐",
    sfx: "音效",
    voice: "语音",
    video: "视频",
    ui: "界面素材",
    font: "字体",
    live2d: "Live2D",
    model3d: "3D 模型",
    scene3d: "3D 场景",
  });

  const BLOCK_LABELS = Object.freeze({
    background: "切换背景",
    dialogue: "台词",
    narration: "旁白",
    character_show: "显示角色",
    character_hide: "隐藏角色",
    music_play: "播放音乐",
    music_stop: "停止音乐",
    sfx_play: "播放音效",
    video_play: "播放视频",
    credits_roll: "片尾字幕",
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

  const REFERENCE_SCOPE_LABELS = Object.freeze({
    story: "剧情卡片",
    character: "角色资料",
    ui: "项目 UI",
  });

  const STORY_BLOCK_ASSET_TYPES = Object.freeze({
    background: Object.freeze(["background", "cg", "scene3d"]),
    music_play: Object.freeze(["bgm"]),
    sfx_play: Object.freeze(["sfx"]),
    video_play: Object.freeze(["video"]),
    particle_effect: Object.freeze(["background", "sprite", "cg", "ui"]),
  });

  const GAME_UI_ASSET_FIELDS = Object.freeze([
    Object.freeze({ key: "fontAssetId", label: "成品 UI 字体素材", expectedTypes: Object.freeze(["font"]) }),
    Object.freeze({ key: "titleBackgroundAssetId", label: "标题背景图", expectedTypes: Object.freeze(["background", "cg", "ui"]) }),
    Object.freeze({ key: "titleLogoAssetId", label: "标题 Logo 图", expectedTypes: Object.freeze(["ui", "sprite", "cg"]) }),
    Object.freeze({ key: "panelFrameAssetId", label: "通用面板贴图", expectedTypes: Object.freeze(["ui"]) }),
    Object.freeze({ key: "buttonFrameAssetId", label: "按钮默认贴图", expectedTypes: Object.freeze(["ui"]) }),
    Object.freeze({ key: "buttonHoverFrameAssetId", label: "按钮悬停贴图", expectedTypes: Object.freeze(["ui"]) }),
    Object.freeze({ key: "buttonPressedFrameAssetId", label: "按钮按下贴图", expectedTypes: Object.freeze(["ui"]) }),
    Object.freeze({ key: "buttonDisabledFrameAssetId", label: "按钮禁用贴图", expectedTypes: Object.freeze(["ui"]) }),
    Object.freeze({ key: "saveSlotFrameAssetId", label: "存档卡片贴图", expectedTypes: Object.freeze(["ui"]) }),
    Object.freeze({ key: "systemPanelFrameAssetId", label: "系统弹窗贴图", expectedTypes: Object.freeze(["ui"]) }),
    Object.freeze({ key: "uiOverlayAssetId", label: "全局叠层纹理", expectedTypes: Object.freeze(["ui"]) }),
  ]);

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function getAssetTypeLabel(type = "") {
    return ASSET_TYPE_LABELS[type] ?? cleanText(type, "未知");
  }

  function getReferenceScopeLabel(scope = "") {
    return REFERENCE_SCOPE_LABELS[scope] ?? cleanText(scope, "引用");
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

  function getCharacterList(data = {}) {
    return Array.isArray(data.characters)
      ? data.characters
      : Array.isArray(data.characters?.characters)
        ? data.characters.characters
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

  function buildCharacterMap(data = {}) {
    const characterMap = new Map();
    getCharacterList(data).forEach((character) => {
      if (character?.id) {
        characterMap.set(String(character.id), character);
      }
    });
    buildCollectionMap(data.charactersById).forEach((character, id) => characterMap.set(id, character));
    return characterMap;
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

  function getBlockLabel(type = "") {
    return BLOCK_LABELS[type] ?? cleanText(type, "卡片");
  }

  function getCharacterDisplayName(character = {}, fallback = "") {
    return cleanText(character.displayName ?? character.name, fallback || character.id || "未命名角色");
  }

  function getCharacterPresentation(character = {}) {
    const presentation = character.presentation && typeof character.presentation === "object" ? character.presentation : {};
    return {
      fallbackSpriteAssetId: cleanText(presentation.fallbackSpriteAssetId),
      live2d: presentation.live2d && typeof presentation.live2d === "object" ? presentation.live2d : {},
      model3d: presentation.model3d && typeof presentation.model3d === "object" ? presentation.model3d : {},
    };
  }

  function createAssetRecord(asset = {}) {
    const record = {
      asset,
      assetId: cleanText(asset.id),
      assetName: cleanText(asset.name, asset.id),
      type: cleanText(asset.type, "unknown"),
      typeLabel: getAssetTypeLabel(asset.type),
      path: cleanText(asset.path),
      fileExists: Boolean(asset.fileExists),
      storyReferenceCount: 0,
      characterReferenceCount: 0,
      uiReferenceCount: 0,
      referenceCount: 0,
      references: [],
      locations: [],
      issues: [],
      status: "good",
      statusLabel: "正常",
    };
    Object.defineProperty(record, "_issueKeys", { value: new Set(), enumerable: false });
    return record;
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

  function pushRecordIssue(record, severity, code, title, detail, context = {}) {
    const issueKey = `${code}:${context.assetId ?? record.assetId}:${context.location ?? context.label ?? ""}`;
    if (record._issueKeys.has(issueKey)) {
      return;
    }
    record._issueKeys.add(issueKey);
    record.issues.push({
      severity,
      code,
      title,
      detail,
      assetId: record.assetId,
      assetName: record.assetName,
      typeLabel: record.typeLabel,
      ...context,
    });
  }

  function getStatusFromIssues(issues = []) {
    if (issues.some((issue) => issue.severity === "blocker")) {
      return "blocker";
    }
    if (issues.some((issue) => issue.severity === "warn")) {
      return "warn";
    }
    if (issues.length) {
      return "tip";
    }
    return "good";
  }

  function getStatusLabel(status = "good") {
    if (status === "blocker") {
      return "先修";
    }
    if (status === "warn") {
      return "复查";
    }
    if (status === "tip") {
      return "整理";
    }
    return "正常";
  }

  function getStatusWeight(status = "good") {
    if (status === "blocker") {
      return 100;
    }
    if (status === "warn") {
      return 60;
    }
    if (status === "tip") {
      return 20;
    }
    return 0;
  }

  function getReferenceTypeMismatchDetail(asset, expectedTypes = []) {
    const expectedLabels = expectedTypes.map(getAssetTypeLabel).join(" / ");
    return `${asset.name ?? asset.id} 是 ${getAssetTypeLabel(asset.type)}，但这里期望 ${expectedLabels || "指定类型"}。`;
  }

  function addAssetReference(records, unknownReferences, assetMap, rawAssetId, reference = {}) {
    const assetId = cleanText(rawAssetId);
    if (!assetId) {
      return;
    }

    const base = {
      scope: reference.scope ?? "story",
      scopeLabel: getReferenceScopeLabel(reference.scope ?? "story"),
      expectedTypes: toArray(reference.expectedTypes),
      label: cleanText(reference.label, assetId),
      location: cleanText(reference.location, reference.label),
      chapterName: reference.chapterName,
      sceneName: reference.sceneName,
      sceneId: reference.sceneId,
      blockId: reference.blockId,
      blockIndex: reference.blockIndex,
      field: reference.field,
      characterId: reference.characterId,
      characterName: reference.characterName,
    };

    if (!assetMap.has(assetId)) {
      unknownReferences.push({
        ...base,
        assetId,
        assetName: assetId,
        severity: "blocker",
        code: "asset_reference_unknown",
        title: "引用了不存在的素材",
        detail: `素材 ${assetId} 不在素材库中。`,
      });
      return;
    }

    const asset = assetMap.get(assetId);
    const record = records.get(assetId);
    if (!record) {
      return;
    }

    const nextReference = {
      ...base,
      assetId,
      assetName: cleanText(asset.name, assetId),
      type: asset.type,
      typeLabel: getAssetTypeLabel(asset.type),
    };
    record.references.push(nextReference);
    record.referenceCount += 1;
    if (nextReference.scope === "character") {
      record.characterReferenceCount += 1;
    } else if (nextReference.scope === "ui") {
      record.uiReferenceCount += 1;
    } else {
      record.storyReferenceCount += 1;
    }
    if (record.locations.length < 6 && nextReference.location && !record.locations.includes(nextReference.location)) {
      record.locations.push(nextReference.location);
    }

    if (!record.fileExists) {
      pushRecordIssue(
        record,
        "blocker",
        "asset_file_missing",
        "已引用素材还没有文件",
        "这个素材已经被项目使用，但真实文件还没导入，发布包里会缺画面或声音。",
        nextReference
      );
    }
    if (
      nextReference.expectedTypes.length > 0 &&
      !nextReference.expectedTypes.includes(asset.type)
    ) {
      pushRecordIssue(
        record,
        "blocker",
        "asset_reference_type_mismatch",
        "素材类型和使用位置不匹配",
        getReferenceTypeMismatchDetail(asset, nextReference.expectedTypes),
        nextReference
      );
    }
  }

  function scanCharacterReferences(data, records, unknownReferences, assetMap, characterMap) {
    characterMap.forEach((character) => {
      const characterName = getCharacterDisplayName(character);
      const base = {
        scope: "character",
        characterId: character.id,
        characterName,
      };

      addAssetReference(records, unknownReferences, assetMap, character.defaultSpriteId, {
        ...base,
        expectedTypes: ["sprite"],
        label: `角色默认立绘：${characterName}`,
        location: `角色资料 / ${characterName} / 默认立绘`,
        field: "defaultSpriteId",
      });

      const presentation = getCharacterPresentation(character);
      addAssetReference(records, unknownReferences, assetMap, presentation.fallbackSpriteAssetId, {
        ...base,
        expectedTypes: ["sprite"],
        label: `角色高级表现兜底：${characterName}`,
        location: `角色资料 / ${characterName} / 高级表现兜底`,
        field: "presentation.fallbackSpriteAssetId",
      });
      addAssetReference(records, unknownReferences, assetMap, presentation.live2d.modelAssetId, {
        ...base,
        expectedTypes: ["live2d"],
        label: `角色 Live2D 模型：${characterName}`,
        location: `角色资料 / ${characterName} / Live2D`,
        field: "presentation.live2d.modelAssetId",
      });
      addAssetReference(records, unknownReferences, assetMap, presentation.model3d.modelAssetId, {
        ...base,
        expectedTypes: ["model3d"],
        label: `角色 3D 模型：${characterName}`,
        location: `角色资料 / ${characterName} / 3D 模型`,
        field: "presentation.model3d.modelAssetId",
      });

      toArray(character.expressions).forEach((expression) => {
        const expressionName = cleanText(expression?.name, expression?.id || "表情");
        addAssetReference(records, unknownReferences, assetMap, expression?.spriteAssetId, {
          ...base,
          expectedTypes: ["sprite"],
          label: `角色表情：${characterName} / ${expressionName}`,
          location: `角色资料 / ${characterName} / 表情 ${expressionName}`,
          field: "expressions.spriteAssetId",
        });
        toArray(expression?.layerAssetIds).forEach((layerAssetId, layerIndex) => {
          addAssetReference(records, unknownReferences, assetMap, layerAssetId, {
            ...base,
            expectedTypes: ["sprite", "ui"],
            label: `角色差分图层：${characterName} / ${expressionName}`,
            location: `角色资料 / ${characterName} / 表情 ${expressionName} / 图层 ${layerIndex + 1}`,
            field: "expressions.layerAssetIds",
          });
        });
      });
    });
  }

  function scanProjectUiReferences(data, records, unknownReferences, assetMap) {
    const project = data.project ?? {};
    const dialogBoxConfig = project.dialogBoxConfig ?? {};
    const gameUiConfig = project.gameUiConfig ?? {};

    addAssetReference(records, unknownReferences, assetMap, dialogBoxConfig.panelAssetId, {
      scope: "ui",
      expectedTypes: ["ui"],
      label: "对话文本框图片图层",
      location: "项目设置 / 对话文本框 / 图片图层",
      field: "dialogBoxConfig.panelAssetId",
    });

    GAME_UI_ASSET_FIELDS.forEach((field) => {
      addAssetReference(records, unknownReferences, assetMap, gameUiConfig[field.key], {
        scope: "ui",
        expectedTypes: field.expectedTypes,
        label: field.label,
        location: `项目设置 / 成品 UI 皮肤 / ${field.label}`,
        field: `gameUiConfig.${field.key}`,
      });
    });
  }

  function scanStoryReferences(data, records, unknownReferences, assetMap, characterMap) {
    getSceneRecords(data).forEach(({ scene, chapterName }) => {
      const sceneName = cleanText(scene?.name ?? scene?.title, scene?.id ?? "未命名场景");
      const sceneId = cleanText(scene?.id);
      toArray(scene?.blocks).forEach((block, blockIndex) => {
        const blockLabel = getBlockLabel(block?.type);
        const base = {
          scope: "story",
          chapterName,
          sceneName,
          sceneId,
          blockId: cleanText(block?.id, `block_${blockIndex + 1}`),
          blockIndex,
          label: `${sceneName} / ${blockLabel}`,
          location: `${chapterName} / ${sceneName} / 第 ${blockIndex + 1} 张 · ${blockLabel}`,
        };

        addAssetReference(records, unknownReferences, assetMap, block?.assetId, {
          ...base,
          expectedTypes: STORY_BLOCK_ASSET_TYPES[block?.type] ?? [],
          field: "block.assetId",
        });

        addAssetReference(records, unknownReferences, assetMap, block?.voiceAssetId, {
          ...base,
          expectedTypes: ["voice"],
          label: `${sceneName} / ${blockLabel}语音`,
          field: "block.voiceAssetId",
        });

        if (block?.type === "dialogue" || block?.type === "character_show") {
          const characterId = cleanText(block.speakerId ?? block.characterId);
          const character = characterMap.get(characterId);
          const expression = toArray(character?.expressions).find((item) => item?.id === block.expressionId);
          const characterName = getCharacterDisplayName(character ?? {}, characterId);
          const expressionName = cleanText(expression?.name, block.expressionId || "默认");

          addAssetReference(records, unknownReferences, assetMap, expression?.spriteAssetId, {
            ...base,
            expectedTypes: ["sprite"],
            label: `${sceneName} / ${characterName} / ${expressionName}`,
            field: "character.expression.spriteAssetId",
            characterId,
            characterName,
          });
          toArray(expression?.layerAssetIds).forEach((layerAssetId, layerIndex) => {
            addAssetReference(records, unknownReferences, assetMap, layerAssetId, {
              ...base,
              expectedTypes: ["sprite", "ui"],
              label: `${sceneName} / ${characterName} / ${expressionName} 图层`,
              field: "character.expression.layerAssetIds",
              characterId,
              characterName,
              location: `${base.location} / ${characterName} ${expressionName} 图层 ${layerIndex + 1}`,
            });
          });
        }
      });
    });
  }

  function addRecordLevelIssues(record) {
    if (record.referenceCount === 0) {
      pushRecordIssue(
        record,
        "tip",
        "asset_unused",
        "素材暂时没有被项目引用",
        "如果它不是备用素材，发布前可以考虑移出项目或归档到素材库外。",
        {
          assetId: record.assetId,
          assetName: record.assetName,
          scope: "asset",
          scopeLabel: "素材库",
          location: "素材库",
        }
      );
      if (!record.fileExists) {
        pushRecordIssue(
          record,
          "tip",
          "asset_missing_but_unused",
          "素材未导入且未使用",
          "这类条目通常可以先删除占位或补文件，避免素材库看起来像半成品。",
          {
            assetId: record.assetId,
            assetName: record.assetName,
            scope: "asset",
            scopeLabel: "素材库",
            location: "素材库",
          }
        );
      }
    }
  }

  function buildAssetDependencySheet(data = {}) {
    const assetMap = buildAssetMap(data);
    const characterMap = buildCharacterMap(data);
    const records = new Map(Array.from(assetMap.values()).map((asset) => [String(asset.id ?? ""), createAssetRecord(asset)]));
    const unknownReferences = [];

    scanCharacterReferences(data, records, unknownReferences, assetMap, characterMap);
    scanProjectUiReferences(data, records, unknownReferences, assetMap);
    scanStoryReferences(data, records, unknownReferences, assetMap, characterMap);

    const assetRecords = Array.from(records.values());
    const issues = [];
    assetRecords.forEach((record) => {
      addRecordLevelIssues(record);
      record.status = getStatusFromIssues(record.issues);
      record.statusLabel = getStatusLabel(record.status);
      issues.push(...record.issues);
    });
    issues.push(...unknownReferences);

    const referencedRecords = assetRecords.filter((record) => record.referenceCount > 0);
    const summary = {
      assetCount: assetRecords.length,
      referencedAssetCount: referencedRecords.length,
      unusedAssetCount: assetRecords.filter((record) => record.referenceCount === 0).length,
      missingFileCount: assetRecords.filter((record) => !record.fileExists).length,
      urgentMissingCount: assetRecords.filter((record) => !record.fileExists && record.referenceCount > 0).length,
      unknownReferenceCount: unknownReferences.length,
      typeMismatchCount: issues.filter((issue) => issue.code === "asset_reference_type_mismatch").length,
      storyReferenceCount: assetRecords.reduce((total, record) => total + record.storyReferenceCount, 0),
      characterReferenceCount: assetRecords.reduce((total, record) => total + record.characterReferenceCount, 0),
      uiReferenceCount: assetRecords.reduce((total, record) => total + record.uiReferenceCount, 0),
      blockerCount: issues.filter((issue) => issue.severity === "blocker").length,
      warningCount: issues.filter((issue) => issue.severity === "warn").length,
      tipCount: issues.filter((issue) => issue.severity === "tip").length,
    };

    issues.sort((left, right) => getIssueWeight(right) - getIssueWeight(left) || cleanText(left.assetName).localeCompare(cleanText(right.assetName), "zh-CN"));
    assetRecords.sort((left, right) => {
      const statusDiff = getStatusWeight(right.status) - getStatusWeight(left.status);
      if (statusDiff !== 0) {
        return statusDiff;
      }
      if (right.referenceCount !== left.referenceCount) {
        return right.referenceCount - left.referenceCount;
      }
      return left.assetName.localeCompare(right.assetName, "zh-CN");
    });

    return {
      projectTitle: cleanText(data.project?.title, "Canvasia Project"),
      assets: assetRecords,
      references: assetRecords.flatMap((record) => record.references),
      unknownReferences,
      issues,
      summary,
    };
  }

  function getAssetDependencyStatusDigest(sheet = {}) {
    const summary = sheet.summary ?? {};
    if ((summary.assetCount ?? 0) === 0) {
      return {
        status: "empty",
        title: "还没有素材依赖表",
        detail: "项目里暂时没有素材。先导入背景、立绘、BGM 或 UI 素材后，这里会显示依赖关系。",
      };
    }
    if ((summary.blockerCount ?? 0) > 0) {
      return {
        status: "blocked",
        title: `有 ${summary.blockerCount} 个素材依赖阻塞`,
        detail: "优先处理已引用缺文件、坏素材 ID 和类型不匹配，否则发布包会缺画面或声音。",
      };
    }
    if ((summary.warningCount ?? 0) > 0) {
      return {
        status: "warn",
        title: `有 ${summary.warningCount} 个素材依赖提醒`,
        detail: "项目可以继续制作，但建议复查素材绑定是否符合类型预期。",
      };
    }
    return {
      status: "ready",
      title: "素材依赖关系比较清晰",
      detail: "当前素材引用、真实文件和类型匹配没有明显结构风险。",
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

  function buildAssetDependencyMarkdown(sheet = {}, options = {}) {
    const summary = sheet.summary ?? {};
    const digest = getAssetDependencyStatusDigest(sheet);
    const generatedAt = cleanText(options.generatedAt);
    const projectTitle = cleanText(options.projectTitle ?? sheet.projectTitle, "Canvasia Project");
    const assetRows = toArray(sheet.assets).map((record) => [
      record.statusLabel,
      record.assetName,
      record.typeLabel,
      record.fileExists ? "已导入" : "缺文件",
      record.referenceCount,
      record.storyReferenceCount,
      record.characterReferenceCount,
      record.uiReferenceCount,
      record.locations.join(" / "),
    ]);
    const issueRows = toArray(sheet.issues).map((issue, index) => [
      index + 1,
      issue.severity === "blocker" ? "先修" : issue.severity === "warn" ? "复查" : "整理",
      issue.assetName,
      issue.scopeLabel,
      issue.location,
      issue.title,
      issue.detail,
    ]);

    return [
      `# ${projectTitle} 素材依赖表`,
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
        ["素材", "已引用", "未使用", "缺文件", "已引用缺文件", "未知引用", "类型不匹配", "剧情 / 角色 / UI 引用"],
        [
          [
            summary.assetCount ?? 0,
            summary.referencedAssetCount ?? 0,
            summary.unusedAssetCount ?? 0,
            summary.missingFileCount ?? 0,
            summary.urgentMissingCount ?? 0,
            summary.unknownReferenceCount ?? 0,
            summary.typeMismatchCount ?? 0,
            `${summary.storyReferenceCount ?? 0} / ${summary.characterReferenceCount ?? 0} / ${summary.uiReferenceCount ?? 0}`,
          ],
        ]
      ),
      "",
      "## 素材清单",
      "",
      buildMarkdownTable(["状态", "素材", "类型", "文件", "总引用", "剧情", "角色", "UI", "位置示例"], assetRows) || "当前没有可列出的素材。",
      "",
      "## 需要复查的问题",
      "",
      buildMarkdownTable(["序号", "级别", "素材", "范围", "位置", "问题", "说明"], issueRows) || "当前没有明显素材依赖问题。",
      "",
    ].join("\n");
  }

  function buildAssetDependencyCsv(sheet = {}) {
    const rows = toArray(sheet.assets).map((record, index) => [
      index + 1,
      record.assetName,
      record.assetId,
      record.typeLabel,
      record.fileExists ? "已导入" : "缺文件",
      record.referenceCount,
      record.storyReferenceCount,
      record.characterReferenceCount,
      record.uiReferenceCount,
      record.statusLabel,
      record.locations.join(" / "),
      record.issues.map((issue) => issue.title).join(" / "),
    ]);
    return `\uFEFF${buildCsv(
      ["序号", "素材", "ID", "类型", "文件", "总引用", "剧情引用", "角色引用", "UI引用", "状态", "位置示例", "问题"],
      rows
    )}\n`;
  }

  global.CanvasiaEditorAssetDependencySheet = Object.freeze({
    buildAssetDependencySheet,
    getAssetDependencyStatusDigest,
    buildAssetDependencyMarkdown,
    buildAssetDependencyCsv,
    getAssetTypeLabel,
    getReferenceScopeLabel,
  });
})(typeof window !== "undefined" ? window : globalThis);
