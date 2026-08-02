(function attachCharacterBlockingWorkspaceTools(global) {
  const commonTools = global.CanvasiaEditorCommon || {};

  const CHARACTER_POSITION_PERCENT = Object.freeze({ left: 24, center: 50, right: 76 });
  const CHARACTER_BLOCKING_FORMATIONS = Object.freeze({
    balanced: Object.freeze({
      id: "balanced",
      label: "自动排开",
      description: "按当前左右顺序均匀排开，适合先得到不会挤在一起的基础画面。",
      minimumCast: 1,
      maximumCast: 5,
    }),
    dialogue_duo: Object.freeze({
      id: "dialogue_duo",
      label: "双人对谈",
      description: "两位角色分居左右并略微推近，适合连续对白。",
      minimumCast: 2,
      maximumCast: 2,
    }),
    focus_selected: Object.freeze({
      id: "focus_selected",
      label: "突出当前角色",
      description: "当前角色居中靠前，其余角色退到两侧作为陪衬。",
      minimumCast: 2,
      maximumCast: 5,
      requiresSelected: true,
    }),
    wide_cast: Object.freeze({
      id: "wide_cast",
      label: "多人全景",
      description: "缩小并拉开多人站位，适合三到五人的同屏段落。",
      minimumCast: 2,
      maximumCast: 5,
    }),
  });

  function fallbackEscapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  const escapeHtml = commonTools.escapeHtml || fallbackEscapeHtml;

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function clampNumber(value, minimum, maximum, fallback = minimum) {
    const number = Number(value);
    if (!Number.isFinite(number)) return fallback;
    return Math.min(Math.max(number, minimum), maximum);
  }

  function getToolOptions(options = {}) {
    return {
      getSafeCharacterStage:
        options.getSafeCharacterStage ||
        ((value = {}) => ({
          offsetX: Math.round(clampNumber(value.offsetX, -60, 60, 0)),
          offsetY: Math.round(clampNumber(value.offsetY, -45, 45, 0)),
          scale: Math.round(clampNumber(value.scale, 45, 220, 100)),
          opacity: Math.round(clampNumber(value.opacity, 0, 100, 100)),
          layer: Math.round(clampNumber(value.layer, -10, 10, 0)),
          flipX: Boolean(value.flipX),
        })),
      getSafePosition:
        options.getSafePosition || ((value) => (["left", "center", "right"].includes(value) ? value : "center")),
      getCharacterVisual:
        options.getCharacterVisual ||
        ((characterId, expressionId) => ({
          characterId,
          expressionId,
          characterName: characterId || "未选择角色",
          spriteUrl: "",
          defaultPosition: "center",
        })),
    };
  }

  function getCharacterCenterPercent(item = {}) {
    const stage = item.stage ?? {};
    const widthPercent = Math.max(12, Math.min(60, 28 * ((Number(stage.scale) || 100) / 100)));
    const base = CHARACTER_POSITION_PERCENT[item.position] ?? CHARACTER_POSITION_PERCENT.center;
    return base + ((Number(stage.offsetX) || 0) / 100) * widthPercent;
  }

  function getCharacterWidthPercent(item = {}) {
    return Math.max(12, Math.min(60, 28 * ((Number(item.stage?.scale) || 100) / 100)));
  }

  function buildBlockingGeometry(characters = []) {
    const rows = toArray(characters).map((character) => {
      const widthPercent = getCharacterWidthPercent(character);
      const centerPercent = getCharacterCenterPercent(character);
      return {
        ...character,
        centerPercent,
        widthPercent,
        leftPercent: centerPercent - widthPercent / 2,
        rightPercent: centerPercent + widthPercent / 2,
      };
    });
    const overlapPairs = [];
    for (let leftIndex = 0; leftIndex < rows.length; leftIndex += 1) {
      for (let rightIndex = leftIndex + 1; rightIndex < rows.length; rightIndex += 1) {
        const left = rows[leftIndex];
        const right = rows[rightIndex];
        const distance = Math.abs(left.centerPercent - right.centerPercent);
        const overlapThreshold = (left.widthPercent + right.widthPercent) * 0.34;
        if (distance < overlapThreshold) {
          overlapPairs.push({
            leftCharacterId: left.characterId,
            rightCharacterId: right.characterId,
            label: `${left.characterName} / ${right.characterName}`,
          });
        }
      }
    }
    const offscreenCharacters = rows.filter((row) => row.leftPercent < 1 || row.rightPercent > 99);
    return { rows, overlapPairs, offscreenCharacters };
  }

  function buildCharacterBlockingModel(scene = {}, selectedBlockId = "", options = {}) {
    const tools = getToolOptions(options);
    const blocks = toArray(scene.blocks);
    const requestedBlockId = cleanText(selectedBlockId);
    const matchedIndex = blocks.findIndex((block) => cleanText(block?.id) === requestedBlockId);
    const selectedIndex = matchedIndex >= 0 ? matchedIndex : Math.max(0, blocks.length - 1);
    const selectedBlock = blocks[selectedIndex] ?? null;
    const selectedCharacterId = cleanText(selectedBlock?.characterId ?? selectedBlock?.speakerId);
    const visibleCharacters = new Map();

    blocks.slice(0, selectedIndex + 1).forEach((block, blockIndex) => {
      const characterId = cleanText(block?.characterId ?? block?.speakerId);
      if (["character_show", "character_move"].includes(block?.type) && characterId) {
        const previous = visibleCharacters.get(characterId);
        const visual = tools.getCharacterVisual(characterId, cleanText(block.expressionId, previous?.expressionId ?? ""));
        visibleCharacters.set(characterId, {
          characterId,
          characterName: cleanText(visual?.characterName, characterId),
          expressionId: cleanText(block.expressionId, previous?.expressionId ?? ""),
          expressionName: cleanText(visual?.expressionName, cleanText(block.expressionId, "默认表情")),
          spriteUrl: cleanText(visual?.spriteUrl),
          position: tools.getSafePosition(block.position ?? previous?.position ?? visual?.defaultPosition),
          stage: tools.getSafeCharacterStage(block.stage ?? previous?.stage),
          controlBlockId: cleanText(block.id),
          controlBlockIndex: blockIndex,
          implicit: false,
          order: previous?.order ?? visibleCharacters.size,
        });
        return;
      }

      if (block?.type === "character_hide" && characterId) {
        visibleCharacters.delete(characterId);
        return;
      }

      if (block?.type === "dialogue" && characterId) {
        const previous = visibleCharacters.get(characterId);
        const expressionId = cleanText(block.expressionId, previous?.expressionId ?? "");
        const visual = tools.getCharacterVisual(characterId, expressionId);
        visibleCharacters.set(characterId, {
          characterId,
          characterName: cleanText(visual?.characterName, characterId),
          expressionId,
          expressionName: cleanText(visual?.expressionName, expressionId || "默认表情"),
          spriteUrl: cleanText(visual?.spriteUrl, previous?.spriteUrl ?? ""),
          position: tools.getSafePosition(previous?.position ?? visual?.defaultPosition),
          stage: tools.getSafeCharacterStage(previous?.stage),
          controlBlockId: cleanText(previous?.controlBlockId),
          controlBlockIndex: Number.isInteger(previous?.controlBlockIndex) ? previous.controlBlockIndex : -1,
          implicit: !previous?.controlBlockId,
          order: previous?.order ?? visibleCharacters.size,
        });
      }
    });

    const characters = [...visibleCharacters.values()]
      .map((character) => ({ ...character, selected: character.characterId === selectedCharacterId }))
      .sort((left, right) => left.order - right.order);
    const geometry = buildBlockingGeometry(characters);
    const issues = [];
    if (geometry.overlapPairs.length) {
      issues.push({
        code: "cast_overlap",
        severity: "warn",
        title: "立绘可能互相遮挡",
        detail: `建议复查：${geometry.overlapPairs.map((pair) => pair.label).join("、")}`,
      });
    }
    if (geometry.offscreenCharacters.length) {
      issues.push({
        code: "cast_offscreen",
        severity: "warn",
        title: "部分立绘接近画面外",
        detail: geometry.offscreenCharacters.map((item) => item.characterName).join("、"),
      });
    }
    const implicitCharacters = characters.filter((character) => character.implicit);
    if (implicitCharacters.length) {
      issues.push({
        code: "cast_implicit",
        severity: "tip",
        title: "有角色依赖运行时自动补位",
        detail: `${implicitCharacters.map((item) => item.characterName).join("、")} 还没有明确的登场或动作卡。`,
      });
    }
    if (characters.length > 4) {
      issues.push({
        code: "cast_crowded",
        severity: "tip",
        title: "同屏角色较多",
        detail: "建议用多人全景，或把镜头拆成两个节拍。",
      });
    }

    return {
      sceneId: cleanText(scene.id),
      sceneName: cleanText(scene.name ?? scene.title, "未命名场景"),
      selectedBlockId: cleanText(selectedBlock?.id),
      selectedBlockIndex: selectedIndex,
      selectedCharacterId,
      characters,
      geometry,
      issues,
      summary: {
        visibleCount: characters.length,
        controllableCount: characters.filter((character) => character.controlBlockId).length,
        overlapCount: geometry.overlapPairs.length,
        offscreenCount: geometry.offscreenCharacters.length,
        implicitCount: implicitCharacters.length,
      },
    };
  }

  function getFormationAvailability(formation = {}, model = {}) {
    const count = model.summary?.controllableCount ?? 0;
    if (count < (formation.minimumCast ?? 1)) return { enabled: false, reason: "在场角色还不够" };
    if (count > (formation.maximumCast ?? 5)) return { enabled: false, reason: "当前同屏人数超过此编队范围" };
    if (
      formation.requiresSelected &&
      !model.characters?.some(
        (character) => character.characterId === model.selectedCharacterId && character.controlBlockId
      )
    ) {
      return { enabled: false, reason: "先选中一位有明确走位卡的角色" };
    }
    return { enabled: true, reason: "" };
  }

  function getFormationEntries(model = {}) {
    return Object.values(CHARACTER_BLOCKING_FORMATIONS).map((formation) => ({
      ...formation,
      ...getFormationAvailability(formation, model),
    }));
  }

  function makeStageTarget(character = {}, target = {}) {
    return {
      position: target.position ?? character.position,
      stage: {
        ...character.stage,
        offsetX: target.offsetX ?? character.stage.offsetX,
        offsetY: target.offsetY ?? character.stage.offsetY,
        scale: target.scale ?? character.stage.scale,
        opacity: target.opacity ?? character.stage.opacity,
        layer: target.layer ?? character.stage.layer,
      },
    };
  }

  function getBalancedSlots(count) {
    const layouts = {
      1: [{ position: "center", offsetX: 0, offsetY: 0, scale: 110, opacity: 100, layer: 2 }],
      2: [
        { position: "left", offsetX: 4, offsetY: 0, scale: 106, opacity: 100, layer: 1 },
        { position: "right", offsetX: -4, offsetY: 0, scale: 106, opacity: 100, layer: 2 },
      ],
      3: [
        { position: "left", offsetX: 0, offsetY: 4, scale: 92, opacity: 100, layer: 1 },
        { position: "center", offsetX: 0, offsetY: 0, scale: 98, opacity: 100, layer: 2 },
        { position: "right", offsetX: 0, offsetY: 4, scale: 92, opacity: 100, layer: 3 },
      ],
      4: [
        { position: "left", offsetX: -24, offsetY: 7, scale: 82, opacity: 100, layer: 0 },
        { position: "left", offsetX: 30, offsetY: 3, scale: 86, opacity: 100, layer: 1 },
        { position: "right", offsetX: -30, offsetY: 3, scale: 86, opacity: 100, layer: 2 },
        { position: "right", offsetX: 24, offsetY: 7, scale: 82, opacity: 100, layer: 3 },
      ],
      5: [
        { position: "left", offsetX: -30, offsetY: 10, scale: 74, opacity: 100, layer: -1 },
        { position: "left", offsetX: 24, offsetY: 6, scale: 78, opacity: 100, layer: 0 },
        { position: "center", offsetX: 0, offsetY: 1, scale: 84, opacity: 100, layer: 2 },
        { position: "right", offsetX: -24, offsetY: 6, scale: 78, opacity: 100, layer: 1 },
        { position: "right", offsetX: 30, offsetY: 10, scale: 74, opacity: 100, layer: 3 },
      ],
    };
    return layouts[count] ?? [];
  }

  function getWideSlots(count) {
    return getBalancedSlots(count).map((slot, index) => ({
      ...slot,
      scale: Math.max(68, slot.scale - (count <= 2 ? 14 : 8)),
      offsetY: slot.offsetY + 8,
      layer: index - Math.floor(count / 2),
    }));
  }

  function getFocusSlots(characters = [], selectedCharacterId = "") {
    const selected = characters.find((character) => character.characterId === selectedCharacterId);
    if (!selected) return [];
    const supporting = characters
      .filter((character) => character.characterId !== selectedCharacterId)
      .sort((left, right) => getCharacterCenterPercent(left) - getCharacterCenterPercent(right));
    const supportingSlots = getWideSlots(Math.max(2, supporting.length + 1)).filter((_, index) => index !== Math.floor((supporting.length + 1) / 2));
    const targetByCharacterId = new Map([
      [
        selectedCharacterId,
        { position: "center", offsetX: 0, offsetY: -2, scale: 126, opacity: 100, layer: 5 },
      ],
    ]);
    supporting.forEach((character, index) => {
      targetByCharacterId.set(character.characterId, {
        ...(supportingSlots[index] ?? getWideSlots(supporting.length)[index]),
        opacity: 84,
        layer: Math.min(index, 1),
      });
    });
    return characters.map((character) => targetByCharacterId.get(character.characterId));
  }

  function buildFormationTargets(model = {}, formationId = "") {
    const characters = model.characters
      .filter((character) => character.controlBlockId)
      .sort((left, right) => getCharacterCenterPercent(left) - getCharacterCenterPercent(right));
    let slots = [];
    if (formationId === "dialogue_duo" && characters.length === 2) {
      slots = [
        { position: "left", offsetX: 7, offsetY: -1, scale: 112, opacity: 100, layer: 2 },
        { position: "right", offsetX: -7, offsetY: -1, scale: 112, opacity: 100, layer: 3 },
      ];
    } else if (formationId === "focus_selected") {
      slots = getFocusSlots(characters, model.selectedCharacterId);
    } else if (formationId === "wide_cast") {
      slots = getWideSlots(characters.length);
    } else {
      slots = getBalancedSlots(characters.length);
    }
    return characters.map((character, index) => ({
      character,
      target: makeStageTarget(character, slots[index] ?? {}),
    }));
  }

  function isSameStage(left = {}, right = {}) {
    return ["offsetX", "offsetY", "scale", "opacity", "layer", "flipX"].every(
      (key) => left[key] === right[key]
    );
  }

  function buildCharacterBlockingFormationPlan(scene = {}, selectedBlockId = "", formationId = "", options = {}) {
    const tools = getToolOptions(options);
    const model = buildCharacterBlockingModel(scene, selectedBlockId, options);
    const formation = CHARACTER_BLOCKING_FORMATIONS[cleanText(formationId)];
    if (!formation) {
      return { ok: false, reason: "unknown_formation", model, formation: null, scene, patches: [] };
    }
    const availability = getFormationAvailability(formation, model);
    if (!availability.enabled) {
      return { ok: false, reason: "unavailable", detail: availability.reason, model, formation, scene, patches: [] };
    }

    const nextScene = {
      ...scene,
      blocks: toArray(scene.blocks).map((block) => ({
        ...block,
        ...(block?.stage && typeof block.stage === "object" ? { stage: { ...block.stage } } : {}),
      })),
    };
    const patchByBlockId = new Map();
    buildFormationTargets(model, formation.id).forEach(({ character, target }) => {
      const blockIndex = nextScene.blocks.findIndex((block) => cleanText(block?.id) === character.controlBlockId);
      if (blockIndex < 0) return;
      const block = nextScene.blocks[blockIndex];
      const before = {
        position: tools.getSafePosition(block.position ?? character.position),
        stage: tools.getSafeCharacterStage(block.stage ?? character.stage),
      };
      const after = {
        position: tools.getSafePosition(target.position),
        stage: tools.getSafeCharacterStage(target.stage),
      };
      if (before.position === after.position && isSameStage(before.stage, after.stage)) return;
      nextScene.blocks[blockIndex] = { ...block, position: after.position, stage: after.stage };
      patchByBlockId.set(character.controlBlockId, {
        blockId: character.controlBlockId,
        blockIndex,
        characterId: character.characterId,
        characterName: character.characterName,
        before,
        after,
      });
    });
    const patches = [...patchByBlockId.values()].sort((left, right) => left.blockIndex - right.blockIndex);
    if (!patches.length) {
      return { ok: false, reason: "no_changes", model, formation, scene: nextScene, patches: [] };
    }
    return {
      ok: true,
      reason: "",
      model,
      formation,
      scene: nextScene,
      patches,
      skippedCount: model.summary.visibleCount - model.summary.controllableCount,
      summary: `${formation.label} · 调整 ${patches.length} 张角色卡`,
    };
  }

  function renderCharacterBlockingSprites(model = {}, options = {}) {
    const getCharacterStageStyle = options.getCharacterStageStyle || (() => "");
    return toArray(model.characters)
      .filter((character) => !character.selected)
      .map((character) => {
        const style = getCharacterStageStyle(character.stage, character.position);
        const visual = character.spriteUrl
          ? `<img src="${escapeHtml(character.spriteUrl)}" alt="" draggable="false" />`
          : `<span class="stage-blocking-fallback-head"></span><span class="stage-blocking-fallback-body"></span>`;
        const content = `${visual}<span class="stage-blocking-sprite-label">${escapeHtml(character.characterName)}</span>`;
        return character.controlBlockId
          ? `<button type="button" class="stage-blocking-sprite${character.spriteUrl ? " has-image" : " is-fallback"}" data-position="${escapeHtml(
              character.position
            )}" style="${escapeHtml(style)}" data-action="select-block" data-block-id="${escapeHtml(
              character.controlBlockId
            )}" aria-label="定位到 ${escapeHtml(character.characterName)} 的走位卡">${content}</button>`
          : `<span class="stage-blocking-sprite is-fallback is-implicit" data-position="${escapeHtml(
              character.position
            )}" style="${escapeHtml(style)}" aria-label="${escapeHtml(
              `${character.characterName} 尚无明确登场卡`
            )}">${content}</span>`;
      })
      .join("");
  }

  function renderCharacterBlockingWorkspace(model = {}) {
    if (!model.characters?.length) return "";
    const entries = getFormationEntries(model);
    const tone = model.summary.overlapCount || model.summary.offscreenCount ? "warn" : model.issues.length ? "tip" : "ready";
    const castButtons = model.characters
      .map((character) => {
        const content = `
          <span>${character.selected ? "当前" : character.implicit ? "待补登场" : "在场"}</span>
          <strong>${escapeHtml(character.characterName)}</strong>
          <small>${escapeHtml(character.position === "left" ? "左侧" : character.position === "right" ? "右侧" : "中央")} · ${character.stage.scale}%</small>
        `;
        return character.controlBlockId
          ? `<button type="button" class="stage-blocking-cast-chip${character.selected ? " is-selected" : ""}" data-action="select-block" data-block-id="${escapeHtml(
              character.controlBlockId
            )}">${content}</button>`
          : `<article class="stage-blocking-cast-chip is-implicit">${content}</article>`;
      })
      .join("");
    const issue = model.issues[0];
    return `
      <section class="stage-blocking-workspace is-${tone}" data-character-blocking-workspace>
        <div class="stage-blocking-head">
          <div>
            <span>CAST BLOCKING</span>
            <strong>多人走位台</strong>
          </div>
          <p><b>${model.summary.visibleCount}</b> 人在场 · <b>${model.summary.controllableCount}</b> 人有明确走位卡</p>
        </div>
        <div class="stage-blocking-cast" aria-label="当前节拍在场角色">${castButtons}</div>
        <div class="stage-blocking-formations" aria-label="多人编队预设">
          ${entries
            .map(
              (entry) => `
                <button
                  type="button"
                  class="stage-blocking-formation"
                  data-action="apply-character-blocking-formation"
                  data-character-blocking-formation="${escapeHtml(entry.id)}"
                  title="${escapeHtml(entry.enabled ? entry.description : entry.reason)}"
                  ${entry.enabled ? "" : "disabled"}
                >
                  <strong>${escapeHtml(entry.label)}</strong>
                  <span>${escapeHtml(entry.enabled ? entry.description : entry.reason)}</span>
                </button>
              `
            )
            .join("")}
        </div>
        <div class="stage-blocking-status is-${tone}">
          <span>${tone === "warn" ? "需要复查" : tone === "tip" ? "走位提示" : "构图清晰"}</span>
          <strong>${escapeHtml(issue?.title ?? "当前角色之间没有明显遮挡")}</strong>
          <small>${escapeHtml(issue?.detail ?? "可直接点画面里的其他角色，回到它最近的登场或动作卡。")}</small>
        </div>
      </section>
    `;
  }

  function createCharacterBlockingController(options = {}) {
    let formationInFlight = false;

    function getModel() {
      return buildCharacterBlockingModel(options.getScene?.() ?? {}, options.getSelectedBlockId?.() ?? "", options);
    }

    async function applyFormation(formationId) {
      if (formationInFlight) {
        options.showToast?.("多人走位正在保存，请稍等。", "info");
        return false;
      }
      formationInFlight = true;
      try {
        const flushed = await options.flushPendingChanges?.();
        if (flushed === false) return false;
        const scene = options.getScene?.() ?? {};
        const selectedBlockId = options.getSelectedBlockId?.() ?? "";
        const plan = buildCharacterBlockingFormationPlan(scene, selectedBlockId, formationId, options);
        if (!plan.ok) {
          const message =
            plan.reason === "no_changes"
              ? "当前角色已经是这套编队。"
              : plan.detail || "这套编队暂时不适合当前在场角色。";
          options.showToast?.(message, plan.reason === "no_changes" ? "info" : "error");
          return false;
        }

        if (plan.patches.length > 1) {
          const accepted = await options.confirm?.({
            title: `套用“${plan.formation.label}”？`,
            message: `将同时调整 ${plan.patches.length} 张角色登场/动作卡。${
              plan.skippedCount ? `另有 ${plan.skippedCount} 位角色没有明确走位卡，会保持原样。` : ""
            }保存后仍可从项目历史恢复。`,
            confirmLabel: "套用编队",
            cancelLabel: "先不调整",
          });
          if (!accepted) return false;
        }

        options.setStatus?.(`正在套用${plan.formation.label}...`);
        const saved = await options.persistScene?.(plan.scene, {
          selectedSceneId: plan.scene.id,
          selectedBlockId,
          previewSceneId: plan.scene.id,
          previewBlockIndex: plan.model.selectedBlockIndex,
          successMessage: `${plan.formation.label}已应用到 ${plan.patches.length} 张角色卡`,
        });
        if (saved) {
          options.showToast?.(`${plan.formation.label}已完成 · ${plan.patches.length} 张角色卡`);
        }
        return Boolean(saved);
      } finally {
        formationInFlight = false;
      }
    }

    return Object.freeze({ getModel, applyFormation });
  }

  global.CanvasiaEditorCharacterBlockingWorkspace = Object.freeze({
    CHARACTER_POSITION_PERCENT,
    CHARACTER_BLOCKING_FORMATIONS,
    getCharacterCenterPercent,
    getCharacterWidthPercent,
    buildBlockingGeometry,
    buildCharacterBlockingModel,
    getFormationAvailability,
    getFormationEntries,
    buildFormationTargets,
    buildCharacterBlockingFormationPlan,
    renderCharacterBlockingSprites,
    renderCharacterBlockingWorkspace,
    createCharacterBlockingController,
  });
})(typeof window !== "undefined" ? window : globalThis);
