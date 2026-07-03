(function attachScriptImportMappingTools(global) {
  function normalizeImportedLookupText(value) {
    return String(value ?? "")
      .trim()
      .toLowerCase()
      .replace(/\.[a-z0-9]+$/i, "")
      .replace(/[\s_-]+/g, "");
  }

  function getImportedLookupValues(item, extraValues = []) {
    const tags = Array.isArray(item?.tags) ? item.tags : [];
    return [
      item?.id,
      item?.name,
      item?.displayName,
      item?.fileName,
      item?.filename,
      item?.path,
      item?.src,
      item?.url,
      ...tags,
      ...extraValues,
    ].filter(Boolean);
  }

  function matchesImportedLookupHint(hint, values, { partial = false } = {}) {
    const normalizedHint = normalizeImportedLookupText(hint);
    if (!normalizedHint) {
      return false;
    }

    return values.some((value) => {
      const normalizedValue = normalizeImportedLookupText(value);
      if (!normalizedValue) {
        return false;
      }

      return (
        normalizedValue === normalizedHint ||
        (partial && (normalizedValue.includes(normalizedHint) || normalizedHint.includes(normalizedValue)))
      );
    });
  }

  function findImportedCharacterByHint(data, characterHint) {
    const characters = Array.isArray(data?.characters) ? data.characters : [];
    const exact = characters.find((character) => matchesImportedLookupHint(characterHint, getImportedLookupValues(character)));
    return (
      exact ??
      characters.find((character) =>
        matchesImportedLookupHint(characterHint, getImportedLookupValues(character), { partial: true })
      ) ??
      null
    );
  }

  function findImportedExpressionIdByHint(data, characterId, expressionHint) {
    const character = data?.charactersById instanceof Map
      ? data.charactersById.get(characterId)
      : (data?.characters ?? []).find((item) => item?.id === characterId);
    const expressions = Array.isArray(character?.expressions) ? character.expressions : [];
    const exact = expressions.find((expression) => matchesImportedLookupHint(expressionHint, getImportedLookupValues(expression)));
    const partial =
      exact ??
      expressions.find((expression) =>
        matchesImportedLookupHint(expressionHint, getImportedLookupValues(expression), { partial: true })
      );
    return partial?.id ?? "";
  }

  function findImportedAssetIdByHint(data, assetHint, assetTypes = []) {
    const allowedTypes = new Set(assetTypes.filter(Boolean));
    const assets = Array.isArray(data?.assetList) ? data.assetList : [];
    const candidates = allowedTypes.size ? assets.filter((asset) => allowedTypes.has(asset.type)) : assets;
    const exact = candidates.find((asset) => matchesImportedLookupHint(assetHint, getImportedLookupValues(asset)));
    const partial =
      exact ??
      candidates.find((asset) =>
        matchesImportedLookupHint(assetHint, getImportedLookupValues(asset), { partial: true })
      );
    return partial?.id ?? "";
  }

  function findImportedSceneByHint(data, sceneHint) {
    const scenes = Array.isArray(data?.scenes) ? data.scenes : [];
    const exact = scenes.find((scene) => matchesImportedLookupHint(sceneHint, getImportedLookupValues(scene)));
    return (
      exact ??
      scenes.find((scene) => matchesImportedLookupHint(sceneHint, getImportedLookupValues(scene), { partial: true })) ??
      null
    );
  }

  function findImportedSceneIdByHint(data, sceneHint) {
    return findImportedSceneByHint(data, sceneHint)?.id ?? "";
  }

  function findImportedVariableByHint(data, variableHint, typeFilter = "") {
    const variables = Array.isArray(data?.variables) ? data.variables : [];
    const candidates = typeFilter ? variables.filter((variable) => variable?.type === typeFilter) : variables;
    const exact = candidates.find((variable) => matchesImportedLookupHint(variableHint, getImportedLookupValues(variable)));
    return (
      exact ??
      candidates.find((variable) =>
        matchesImportedLookupHint(variableHint, getImportedLookupValues(variable), { partial: true })
      ) ??
      null
    );
  }

  function findImportedVariableIdByHint(data, variableHint, typeFilter = "") {
    return findImportedVariableByHint(data, variableHint, typeFilter)?.id ?? "";
  }

  function getImportedEffectDuration(durationMs) {
    const ms = Number.parseFloat(durationMs ?? "");
    if (!Number.isFinite(ms)) {
      return "medium";
    }
    if (ms <= 450) {
      return "short";
    }
    if (ms >= 1000) {
      return "long";
    }
    return "medium";
  }

  function callScriptImportResolver(resolvers, name, args = [], fallback = "") {
    const resolver = resolvers?.[name];
    return typeof resolver === "function" ? resolver(...args) : fallback;
  }

  function cloneScriptImportStageDefaults(value) {
    return value && typeof value === "object" && !Array.isArray(value) ? { ...value } : {};
  }

  function normalizeImportedDraftBlockForScene(draftBlock, scene = null, resolvers = {}) {
    if (!draftBlock || typeof draftBlock !== "object") {
      return null;
    }

    const getAssetId = (hint, types) => callScriptImportResolver(resolvers, "findAssetIdByHint", [hint, types], "");
    const getSceneId = (hint) => callScriptImportResolver(resolvers, "findSceneIdByHint", [hint], "");
    const getVariableId = (hint, typeFilter = "") =>
      callScriptImportResolver(resolvers, "findVariableIdByHint", [hint, typeFilter], "");
    const getTransition = (value) => callScriptImportResolver(resolvers, "getSafeTransition", [value], value || "fade");
    const getTransitionDurationMs = (value, fallback) =>
      callScriptImportResolver(resolvers, "getSafeTransitionDurationMs", [value, fallback], fallback ?? 600);
    const getNonNegativeNumber = (value, fallback) =>
      callScriptImportResolver(resolvers, "getSafeNonNegativeNumber", [value, fallback], fallback ?? 0);
    const getVolumePercent = (value, fallback) =>
      callScriptImportResolver(resolvers, "getSafeVolumePercent", [value, fallback], fallback ?? 100);
    const getTextSpeed = (value) => callScriptImportResolver(resolvers, "getSafeTextSpeed", [value], value || "normal");
    const getVideoFit = (value) => callScriptImportResolver(resolvers, "getSafeVideoFit", [value], value || "contain");
    const getVideoVolume = (value) => callScriptImportResolver(resolvers, "getSafeVideoVolume", [value], 100);
    const getShakeIntensity = (value) =>
      callScriptImportResolver(resolvers, "getSafeShakeIntensity", [value], value || "medium");
    const getEffectDurationLabel = (value) =>
      callScriptImportResolver(resolvers, "getSafeEffectDuration", [value], value || "medium");
    const getFlashColor = (value) => callScriptImportResolver(resolvers, "getSafeFlashColor", [value], value || "white");
    const getFlashIntensity = (value) =>
      callScriptImportResolver(resolvers, "getSafeFlashIntensity", [value], value || "medium");
    const getCameraZoomAction = (value) =>
      callScriptImportResolver(resolvers, "getSafeCameraZoomAction", [value], value || "zoom_in");
    const getCameraZoomStrength = (value) =>
      callScriptImportResolver(resolvers, "getSafeCameraZoomStrength", [value], value || "medium");
    const getCameraZoomFocus = (value) =>
      callScriptImportResolver(resolvers, "getSafeCameraZoomFocus", [value], value || "center");
    const getCameraPanTarget = (value) =>
      callScriptImportResolver(resolvers, "getSafeCameraPanTarget", [value], value || "center");
    const getCameraPanStrength = (value) =>
      callScriptImportResolver(resolvers, "getSafeCameraPanStrength", [value], value || "medium");
    const getCharacterStage = (value) => {
      const mergedStage = {
        ...cloneScriptImportStageDefaults(resolvers?.defaultCharacterStage),
        ...cloneScriptImportStageDefaults(value),
      };
      return callScriptImportResolver(resolvers, "getSafeCharacterStage", [mergedStage], mergedStage);
    };
    const getCreditsDuration = (value) => callScriptImportResolver(resolvers, "getSafeCreditsDuration", [value], 18);
    const getCreditsBackground = (value) =>
      callScriptImportResolver(resolvers, "getSafeCreditsBackground", [value], value || "dark");
    const getFadeAction = (value) => callScriptImportResolver(resolvers, "getSafeFadeAction", [value], value || "fade_out");
    const getEffectDuration = (value) =>
      callScriptImportResolver(resolvers, "getEffectDuration", [value], getImportedEffectDuration(value));
    const getConditionOperator = (variableId, value) =>
      callScriptImportResolver(resolvers, "getSafeConditionOperator", [variableId, value], value || "==");
    const normalizeImportedVariableValue = (variableId, value) =>
      callScriptImportResolver(resolvers, "normalizeVariableValue", [variableId, value], value);
    const getScreenFilterAction = (value) =>
      callScriptImportResolver(resolvers, "getSafeScreenFilterAction", [value], value || "apply");
    const getScreenFilterPreset = (value) =>
      callScriptImportResolver(resolvers, "getSafeScreenFilterPreset", [value], value || "memory");
    const getScreenFilterStrength = (value) =>
      callScriptImportResolver(resolvers, "getSafeScreenFilterStrength", [value], value || "medium");
    const getScreenColorGrade = (value) => callScriptImportResolver(resolvers, "getSafeScreenColorGrade", [value], {});
    const getDepthBlurAction = (value) =>
      callScriptImportResolver(resolvers, "getSafeDepthBlurAction", [value], value || "apply");
    const getDepthBlurFocus = (value) =>
      callScriptImportResolver(resolvers, "getSafeDepthBlurFocus", [value], value || "center");
    const getDepthBlurStrength = (value) =>
      callScriptImportResolver(resolvers, "getSafeDepthBlurStrength", [value], value || "medium");
    const getParticleAction = (value) =>
      callScriptImportResolver(resolvers, "getSafeParticleAction", [value], value || "start");
    const getParticlePreset = (value) =>
      callScriptImportResolver(resolvers, "getSafeParticlePreset", [value], value || "snow");
    const getParticleIntensity = (value) =>
      callScriptImportResolver(resolvers, "getSafeParticleIntensity", [value], value || "medium");
    const getParticleSpeed = (value) =>
      callScriptImportResolver(resolvers, "getSafeParticleSpeed", [value], value || "medium");
    const buildParticleDefaults = (preset) =>
      callScriptImportResolver(resolvers, "buildDefaultParticleEffectConfig", [preset], {
        type: "particle_effect",
        action: "start",
        preset,
        intensity: "medium",
        speed: "medium",
      });
    const normalizeParticleConfig = (config) =>
      callScriptImportResolver(resolvers, "normalizeParticleEffectConfig", [config], config);
    const normalizeChoiceEffectConfig = (effect) =>
      callScriptImportResolver(resolvers, "normalizeChoiceEffect", [effect], effect);
    const getChoiceContinueTarget = () => resolvers?.choiceContinueTarget ?? "__continue__";

    const normalizeChoiceEffects = (effects = []) =>
      (Array.isArray(effects) ? effects : [])
        .map((effect) => {
          const type = effect?.type === "variable_add" ? "variable_add" : "variable_set";
          const variableId = getVariableId(effect?.variableHint ?? effect?.variableId, type === "variable_add" ? "number" : "");
          if (!variableId) {
            return null;
          }
          return normalizeChoiceEffectConfig({
            type,
            variableId,
            value: effect?.value,
          });
        })
        .filter(Boolean);
    const normalizeConditionRules = (rules = []) =>
      (Array.isArray(rules) ? rules : [])
        .map((rule) => {
          const rawOperator = rule?.operator === "=" ? "==" : String(rule?.operator ?? "==").trim();
          const numericOperator = [">", ">=", "<", "<="].includes(rawOperator);
          const variableId = getVariableId(rule?.variableHint ?? rule?.variableId, numericOperator ? "number" : "");
          if (!variableId) {
            return null;
          }
          const operator = getConditionOperator(variableId, rawOperator);
          return {
            variableId,
            operator,
            value: normalizeImportedVariableValue(variableId, rule?.value),
          };
        })
        .filter(Boolean);
    const getDefaultConditionTarget = () =>
      callScriptImportResolver(resolvers, "getDefaultJumpTargetSceneId", [scene?.id], "");

    if (draftBlock.type === "dialogue") {
      const voiceAssetId = getAssetId(draftBlock.voiceHint, ["voice"]);
      const textSpeed = draftBlock.textSpeed ? getTextSpeed(draftBlock.textSpeed) : "";
      return {
        type: "dialogue",
        speakerId: callScriptImportResolver(resolvers, "getSpeakerCharacterId", [draftBlock.speakerName], ""),
        text: String(draftBlock.text ?? "").trim(),
        ...(textSpeed ? { textSpeed } : {}),
        ...(voiceAssetId ? { voiceAssetId, voiceVolume: 100 } : {}),
      };
    }

    if (draftBlock.type === "narration") {
      const voiceAssetId = getAssetId(draftBlock.voiceHint, ["voice"]);
      const textSpeed = draftBlock.textSpeed ? getTextSpeed(draftBlock.textSpeed) : "";
      return {
        type: "narration",
        text: String(draftBlock.text ?? "").trim(),
        ...(textSpeed ? { textSpeed } : {}),
        ...(voiceAssetId ? { voiceAssetId, voiceVolume: 100 } : {}),
      };
    }

    if (draftBlock.type === "choice") {
      return {
        type: "choice",
        options: (Array.isArray(draftBlock.options) ? draftBlock.options : [])
          .map((option) => ({
            text: String(option?.text ?? "").trim(),
            gotoSceneId: getSceneId(option?.targetHint) || getChoiceContinueTarget(),
            effects: normalizeChoiceEffects(option?.effects),
          }))
          .filter((option) => option.text),
      };
    }

    if (draftBlock.type === "variable_set") {
      const variableId = getVariableId(draftBlock.variableHint ?? draftBlock.variableId);
      if (!variableId) {
        return null;
      }
      return {
        type: "variable_set",
        variableId,
        value: normalizeImportedVariableValue(variableId, draftBlock.value),
      };
    }

    if (draftBlock.type === "variable_add") {
      const variableId = getVariableId(draftBlock.variableHint ?? draftBlock.variableId, "number");
      const value = Number.parseFloat(draftBlock.value ?? "");
      if (!variableId || !Number.isFinite(value)) {
        return null;
      }
      return {
        type: "variable_add",
        variableId,
        value: normalizeImportedVariableValue(variableId, value),
      };
    }

    if (draftBlock.type === "background") {
      return {
        type: "background",
        assetId: getAssetId(draftBlock.assetHint, ["background", "cg"]),
        transition: getTransition(draftBlock.transition ?? "fade"),
        transitionDurationMs: getTransitionDurationMs(draftBlock.transitionDurationMs, 600),
      };
    }

    if (draftBlock.type === "character_show") {
      const characterId = callScriptImportResolver(resolvers, "findCharacterIdByHint", [draftBlock.characterHint], "");
      const defaultPosition = callScriptImportResolver(
        resolvers,
        "getDefaultCharacterPosition",
        [characterId],
        "center"
      );
      return {
        type: "character_show",
        characterId,
        expressionId: callScriptImportResolver(
          resolvers,
          "findExpressionIdByHint",
          [characterId, draftBlock.expressionHint],
          ""
        ),
        position: callScriptImportResolver(
          resolvers,
          "getSafePosition",
          [draftBlock.position ?? defaultPosition],
          draftBlock.position ?? defaultPosition
        ),
        transition: getTransition(draftBlock.transition ?? "fade"),
        transitionDurationMs: getTransitionDurationMs(draftBlock.transitionDurationMs, 600),
        stage: getCharacterStage(draftBlock.stage),
      };
    }

    if (draftBlock.type === "character_hide") {
      return {
        type: "character_hide",
        characterId: callScriptImportResolver(resolvers, "findCharacterIdByHint", [draftBlock.characterHint], ""),
        transition: getTransition(draftBlock.transition ?? "fade"),
        transitionDurationMs: getTransitionDurationMs(draftBlock.transitionDurationMs, 600),
      };
    }

    if (draftBlock.type === "music_play") {
      return {
        type: "music_play",
        assetId: getAssetId(draftBlock.assetHint, ["bgm"]),
        loop: true,
        volume: 100,
        fadeInMs: getNonNegativeNumber(draftBlock.fadeInMs, 600),
        fadeOutMs: getNonNegativeNumber(draftBlock.fadeOutMs, 600),
        endMode: "until_next_music",
        endBlockId: "",
      };
    }

    if (draftBlock.type === "music_stop") {
      return {
        type: "music_stop",
        fadeOutMs: getNonNegativeNumber(draftBlock.fadeOutMs, 600),
      };
    }

    if (draftBlock.type === "sfx_play") {
      return {
        type: "sfx_play",
        assetId: getAssetId(draftBlock.assetHint, ["sfx"]),
        volume: getVolumePercent(draftBlock.volume, 100),
      };
    }

    if (draftBlock.type === "video_play") {
      const startTimeSeconds = getNonNegativeNumber(draftBlock.startTimeSeconds, 0);
      const endTimeSeconds = getNonNegativeNumber(draftBlock.endTimeSeconds, 0);
      return {
        type: "video_play",
        assetId: getAssetId(draftBlock.assetHint, ["video"]),
        title: String(draftBlock.title || draftBlock.assetHint || "").trim().slice(0, 80),
        fit: getVideoFit(draftBlock.fit),
        volume: getVideoVolume(draftBlock.volume),
        startTimeSeconds,
        endTimeSeconds: endTimeSeconds > startTimeSeconds ? endTimeSeconds : 0,
        skippable: draftBlock.skippable !== false,
      };
    }

    if (draftBlock.type === "credits_roll") {
      const lines = Array.isArray(draftBlock.lines)
        ? draftBlock.lines.map((line) => String(line ?? "").trim()).filter(Boolean)
        : [];
      return {
        type: "credits_roll",
        title: String(draftBlock.title || "STAFF").trim().slice(0, 80) || "STAFF",
        subtitle: String(draftBlock.subtitle ?? "").trim().slice(0, 120),
        lines: lines.length ? lines : ["企划：Creator", "剧本：Writer", "美术：", "音乐：", "特别感谢：所有玩家"],
        durationSeconds: getCreditsDuration(draftBlock.durationSeconds),
        background: getCreditsBackground(draftBlock.background),
        skippable: draftBlock.skippable !== false,
      };
    }

    if (draftBlock.type === "screen_shake") {
      return {
        type: "screen_shake",
        intensity: getShakeIntensity(draftBlock.intensity),
        duration: getEffectDurationLabel(draftBlock.duration),
      };
    }

    if (draftBlock.type === "screen_flash") {
      return {
        type: "screen_flash",
        color: getFlashColor(draftBlock.color),
        intensity: getFlashIntensity(draftBlock.intensity),
        duration: getEffectDurationLabel(draftBlock.duration),
      };
    }

    if (draftBlock.type === "camera_zoom") {
      return {
        type: "camera_zoom",
        action: getCameraZoomAction(draftBlock.action),
        strength: getCameraZoomStrength(draftBlock.strength),
        focus: getCameraZoomFocus(draftBlock.focus),
      };
    }

    if (draftBlock.type === "camera_pan") {
      return {
        type: "camera_pan",
        target: getCameraPanTarget(draftBlock.target),
        strength: getCameraPanStrength(draftBlock.strength),
      };
    }

    if (draftBlock.type === "screen_fade") {
      return {
        type: "screen_fade",
        action: getFadeAction(draftBlock.action ?? "fade_out"),
        color: "black",
        duration: getEffectDuration(draftBlock.durationMs),
      };
    }

    if (draftBlock.type === "condition") {
      const branches = (Array.isArray(draftBlock.branches) ? draftBlock.branches : [])
        .map((branch) => {
          const when = normalizeConditionRules(branch?.when);
          if (!when.length) {
            return null;
          }
          return {
            when,
            gotoSceneId: getSceneId(branch?.targetHint ?? branch?.gotoSceneId) || getDefaultConditionTarget(),
          };
        })
        .filter(Boolean);
      if (!branches.length) {
        return null;
      }
      return {
        type: "condition",
        branches,
        elseGotoSceneId: getSceneId(draftBlock.elseTargetHint) || getDefaultConditionTarget(),
      };
    }

    if (draftBlock.type === "screen_filter") {
      const action = getScreenFilterAction(draftBlock.action);
      return {
        type: "screen_filter",
        action,
        preset: getScreenFilterPreset(draftBlock.preset),
        strength: getScreenFilterStrength(draftBlock.strength),
        grade: getScreenColorGrade(draftBlock.grade),
      };
    }

    if (draftBlock.type === "depth_blur") {
      return {
        type: "depth_blur",
        action: getDepthBlurAction(draftBlock.action),
        focus: getDepthBlurFocus(draftBlock.focus),
        strength: getDepthBlurStrength(draftBlock.strength),
      };
    }

    if (draftBlock.type === "particle_effect") {
      const preset = getParticlePreset(draftBlock.preset);
      return normalizeParticleConfig({
        ...buildParticleDefaults(preset),
        type: "particle_effect",
        action: getParticleAction(draftBlock.action),
        preset,
        intensity: getParticleIntensity(draftBlock.intensity),
        speed: getParticleSpeed(draftBlock.speed),
      });
    }

    if (draftBlock.type === "jump") {
      return {
        type: "jump",
        targetSceneId:
          getSceneId(draftBlock.targetHint) ||
          callScriptImportResolver(resolvers, "getDefaultJumpTargetSceneId", [scene?.id], ""),
      };
    }

    return {
      type: "narration",
      text: String(draftBlock.text ?? "").trim(),
    };
  }

  global.CanvasiaEditorScriptImportMapping = Object.freeze({
    normalizeImportedLookupText,
    getImportedLookupValues,
    matchesImportedLookupHint,
    findImportedCharacterByHint,
    findImportedExpressionIdByHint,
    findImportedAssetIdByHint,
    findImportedSceneByHint,
    findImportedSceneIdByHint,
    findImportedVariableByHint,
    findImportedVariableIdByHint,
    getImportedEffectDuration,
    normalizeImportedDraftBlockForScene,
  });
})(typeof window !== "undefined" ? window : globalThis);
