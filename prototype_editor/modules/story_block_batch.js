(function attachStoryBlockBatchTools(global) {
  "use strict";

  const REORDER_ACTIONS = new Set(["up", "down", "start", "end"]);

  function asList(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanId(value) {
    return String(value ?? "").trim();
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function getBlockIds(blocks = []) {
    return asList(blocks).map((block) => cleanId(block?.id)).filter(Boolean);
  }

  function normalizeStoryBlockSelection(blocks = [], selectedIds = []) {
    const requested = new Set(asList(selectedIds).map(cleanId).filter(Boolean));
    return getBlockIds(blocks).filter((blockId) => requested.has(blockId));
  }

  function normalizeStoryBlockSelectionAnchor(blocks = [], anchorId = "", selectedIds = []) {
    const safeAnchorId = cleanId(anchorId);
    const blockIds = new Set(getBlockIds(blocks));
    if (safeAnchorId && blockIds.has(safeAnchorId)) {
      return safeAnchorId;
    }
    const normalized = normalizeStoryBlockSelection(blocks, selectedIds);
    return normalized[normalized.length - 1] ?? "";
  }

  function updateStoryBlockSelection(blocks = [], selectedIds = [], blockId = "", options = {}) {
    const blockIds = getBlockIds(blocks);
    const targetId = cleanId(blockId);
    const targetIndex = blockIds.indexOf(targetId);
    const normalized = normalizeStoryBlockSelection(blocks, selectedIds);

    if (targetIndex < 0) {
      return {
        selectedIds: normalized,
        anchorId: normalizeStoryBlockSelectionAnchor(blocks, options.anchorId, normalized),
        changed: false,
      };
    }

    const selected = new Set(normalized);
    const shouldSelect =
      typeof options.checked === "boolean" ? options.checked : !selected.has(targetId);
    const anchorId = normalizeStoryBlockSelectionAnchor(blocks, options.anchorId, normalized);
    const anchorIndex = blockIds.indexOf(anchorId);

    if (options.range === true && anchorIndex >= 0) {
      const firstIndex = Math.min(anchorIndex, targetIndex);
      const lastIndex = Math.max(anchorIndex, targetIndex);
      blockIds.slice(firstIndex, lastIndex + 1).forEach((id) => {
        if (shouldSelect) {
          selected.add(id);
        } else {
          selected.delete(id);
        }
      });
    } else if (shouldSelect) {
      selected.add(targetId);
    } else {
      selected.delete(targetId);
    }

    const nextSelectedIds = blockIds.filter((id) => selected.has(id));
    return {
      selectedIds: nextSelectedIds,
      anchorId: options.range === true && anchorIndex >= 0 ? anchorId : targetId,
      changed: nextSelectedIds.join("|") !== normalized.join("|"),
    };
  }

  function selectVisibleStoryBlocks(blocks = [], selectedIds = [], visibleBlockIds = []) {
    const visible = new Set(asList(visibleBlockIds).map(cleanId).filter(Boolean));
    const selected = new Set(normalizeStoryBlockSelection(blocks, selectedIds));
    getBlockIds(blocks).forEach((blockId) => {
      if (visible.has(blockId)) {
        selected.add(blockId);
      }
    });
    return normalizeStoryBlockSelection(blocks, [...selected]);
  }

  function canMoveSelection(blockIds, selected, direction) {
    if (direction === "up") {
      return blockIds.some((blockId, index) => index > 0 && selected.has(blockId) && !selected.has(blockIds[index - 1]));
    }
    return blockIds.some(
      (blockId, index) =>
        index < blockIds.length - 1 && selected.has(blockId) && !selected.has(blockIds[index + 1])
    );
  }

  function getStoryBlockSelectionModel(blocks = [], selectedIds = [], visibleBlockIds = []) {
    const blockIds = getBlockIds(blocks);
    const orderedIds = normalizeStoryBlockSelection(blocks, selectedIds);
    const selected = new Set(orderedIds);
    const requestedVisibleIds = new Set(asList(visibleBlockIds).map(cleanId).filter(Boolean));
    const visibleIds = blockIds.filter((blockId) => requestedVisibleIds.has(blockId));
    const visibleSelectedCount = visibleIds.filter((blockId) => selected.has(blockId)).length;
    const selectedIndexes = orderedIds.map((blockId) => blockIds.indexOf(blockId)).filter((index) => index >= 0);
    const contiguous = selectedIndexes.every((index, itemIndex) => itemIndex === 0 || index === selectedIndexes[itemIndex - 1] + 1);
    const startsAtBeginning = orderedIds.length > 0 && orderedIds.every((blockId, index) => blockIds[index] === blockId);
    const endOffset = blockIds.length - orderedIds.length;
    const endsAtEnd = orderedIds.length > 0 && orderedIds.every((blockId, index) => blockIds[endOffset + index] === blockId);

    return {
      blockCount: blockIds.length,
      selectedCount: orderedIds.length,
      orderedIds,
      selectedIndexes,
      visibleCount: visibleIds.length,
      visibleSelectedCount,
      hiddenSelectedCount: Math.max(orderedIds.length - visibleSelectedCount, 0),
      allVisibleSelected: visibleIds.length > 0 && visibleSelectedCount === visibleIds.length,
      canSelectVisible: visibleIds.length > 0 && visibleSelectedCount < visibleIds.length,
      canClear: orderedIds.length > 0,
      canMoveUp: canMoveSelection(blockIds, selected, "up"),
      canMoveDown: canMoveSelection(blockIds, selected, "down"),
      canMoveStart: orderedIds.length > 0 && !startsAtBeginning,
      canMoveEnd: orderedIds.length > 0 && !endsAtEnd,
      contiguous,
      firstIndex: selectedIndexes[0] ?? -1,
      lastIndex: selectedIndexes[selectedIndexes.length - 1] ?? -1,
    };
  }

  function repairInvalidMusicRanges(blocks = []) {
    const safeBlocks = asList(blocks);
    const indexById = new Map(getBlockIds(safeBlocks).map((blockId, index) => [blockId, index]));
    let repairCount = 0;
    const repairedBlocks = safeBlocks.map((block, index) => {
      if (block?.type !== "music_play" || block?.endMode !== "after_block") {
        return block;
      }
      const targetIndex = indexById.get(cleanId(block.endBlockId));
      if (Number.isInteger(targetIndex) && targetIndex > index) {
        return block;
      }
      repairCount += 1;
      return {
        ...block,
        endMode: "until_next_music",
        endBlockId: "",
      };
    });
    return { blocks: repairedBlocks, repairCount };
  }

  function buildStoryBlockReorderPlan(blocks = [], selectedIds = [], action = "") {
    const safeBlocks = [...asList(blocks)];
    const operation = cleanId(action);
    const orderedIds = normalizeStoryBlockSelection(safeBlocks, selectedIds);
    if (!orderedIds.length) {
      return { changed: false, reason: "先勾选要移动的剧情卡片", blocks: safeBlocks, selectedIds: [] };
    }
    if (!REORDER_ACTIONS.has(operation)) {
      return { changed: false, reason: "不支持这项批量排序操作", blocks: safeBlocks, selectedIds: orderedIds };
    }

    const selected = new Set(orderedIds);
    let nextBlocks = [...safeBlocks];
    if (operation === "up") {
      for (let index = 1; index < nextBlocks.length; index += 1) {
        if (selected.has(cleanId(nextBlocks[index]?.id)) && !selected.has(cleanId(nextBlocks[index - 1]?.id))) {
          [nextBlocks[index - 1], nextBlocks[index]] = [nextBlocks[index], nextBlocks[index - 1]];
        }
      }
    } else if (operation === "down") {
      for (let index = nextBlocks.length - 2; index >= 0; index -= 1) {
        if (selected.has(cleanId(nextBlocks[index]?.id)) && !selected.has(cleanId(nextBlocks[index + 1]?.id))) {
          [nextBlocks[index], nextBlocks[index + 1]] = [nextBlocks[index + 1], nextBlocks[index]];
        }
      }
    } else {
      const selectedBlocks = nextBlocks.filter((block) => selected.has(cleanId(block?.id)));
      const remainingBlocks = nextBlocks.filter((block) => !selected.has(cleanId(block?.id)));
      nextBlocks = operation === "start" ? [...selectedBlocks, ...remainingBlocks] : [...remainingBlocks, ...selectedBlocks];
    }

    const changed = getBlockIds(nextBlocks).join("|") !== getBlockIds(safeBlocks).join("|");
    if (!changed) {
      const edgeLabel = operation === "up" || operation === "start" ? "最前面" : "最后面";
      return {
        changed: false,
        reason: `选中的卡片已经在${edgeLabel}了`,
        blocks: safeBlocks,
        selectedIds: orderedIds,
      };
    }

    const repairResult = repairInvalidMusicRanges(nextBlocks);
    const firstSelectedId = orderedIds[0];
    const previewIndex = Math.max(repairResult.blocks.findIndex((block) => cleanId(block?.id) === firstSelectedId), 0);
    const actionLabels = {
      up: "上移一格",
      down: "下移一格",
      start: "移到场景开头",
      end: "移到场景末尾",
    };
    return {
      changed: true,
      blocks: repairResult.blocks,
      selectedIds: orderedIds,
      selectedBlockId: firstSelectedId,
      previewIndex,
      repairCount: repairResult.repairCount,
      message: `已将 ${orderedIds.length} 张卡片${actionLabels[operation]}`,
    };
  }

  function buildStoryBlockDuplicatePlan(blocks = [], selectedIds = [], options = {}) {
    const safeBlocks = [...asList(blocks)];
    const orderedIds = normalizeStoryBlockSelection(safeBlocks, selectedIds);
    const duplicateBlock = typeof options.duplicateBlock === "function" ? options.duplicateBlock : null;
    if (!orderedIds.length) {
      return { changed: false, reason: "先勾选要复制的剧情卡片", blocks: safeBlocks, selectedIds: [] };
    }
    if (!duplicateBlock) {
      return { changed: false, reason: "剧情卡片复制器没有准备好", blocks: safeBlocks, selectedIds: orderedIds };
    }

    const selected = new Set(orderedIds);
    const sourceBlocks = safeBlocks.filter((block) => selected.has(cleanId(block?.id)));
    const duplicates = [];
    const sourceToDuplicateId = new Map();
    const existingIds = new Set(getBlockIds(safeBlocks));

    for (const sourceBlock of sourceBlocks) {
      const duplicate = duplicateBlock(sourceBlock, {
        existingBlocks: [...safeBlocks, ...duplicates],
        sourceBlocks,
        duplicateBlocks: [...duplicates],
      });
      const duplicateId = cleanId(duplicate?.id);
      if (!duplicate || !duplicateId || existingIds.has(duplicateId)) {
        return {
          changed: false,
          reason: "复制卡片时没有生成唯一编号，本次没有修改场景",
          blocks: safeBlocks,
          selectedIds: orderedIds,
        };
      }
      existingIds.add(duplicateId);
      sourceToDuplicateId.set(cleanId(sourceBlock?.id), duplicateId);
      duplicates.push(duplicate);
    }

    const remappedDuplicates = duplicates.map((block) => {
      const mappedEndBlockId = sourceToDuplicateId.get(cleanId(block?.endBlockId));
      return mappedEndBlockId ? { ...block, endBlockId: mappedEndBlockId } : block;
    });
    const lastSelectedIndex = Math.max(...orderedIds.map((blockId) => getBlockIds(safeBlocks).indexOf(blockId)));
    const insertIndex = lastSelectedIndex + 1;
    const nextBlocks = [
      ...safeBlocks.slice(0, insertIndex),
      ...remappedDuplicates,
      ...safeBlocks.slice(insertIndex),
    ];
    const repairResult = repairInvalidMusicRanges(nextBlocks);
    const duplicateIds = remappedDuplicates.map((block) => cleanId(block?.id));
    return {
      changed: true,
      blocks: repairResult.blocks,
      selectedIds: duplicateIds,
      selectedBlockId: duplicateIds[0],
      previewIndex: insertIndex,
      repairCount: repairResult.repairCount,
      message: `已复制 ${duplicateIds.length} 张卡片，新副本已放在选区后面`,
    };
  }

  function buildStoryBlockDeletePlan(blocks = [], selectedIds = []) {
    const safeBlocks = [...asList(blocks)];
    const orderedIds = normalizeStoryBlockSelection(safeBlocks, selectedIds);
    if (!orderedIds.length) {
      return { changed: false, reason: "先勾选要删除的剧情卡片", blocks: safeBlocks, selectedIds: [] };
    }

    const selected = new Set(orderedIds);
    const firstSelectedIndex = getBlockIds(safeBlocks).indexOf(orderedIds[0]);
    const remainingBlocks = safeBlocks.filter((block) => !selected.has(cleanId(block?.id)));
    const repairResult = repairInvalidMusicRanges(remainingBlocks);
    const previewIndex = repairResult.blocks.length
      ? Math.min(Math.max(firstSelectedIndex, 0), repairResult.blocks.length - 1)
      : 0;
    const selectedBlockId = cleanId(repairResult.blocks[previewIndex]?.id);

    return {
      changed: true,
      blocks: repairResult.blocks,
      selectedIds: [],
      selectedBlockId,
      previewIndex,
      repairCount: repairResult.repairCount,
      message: `已删除 ${orderedIds.length} 张卡片`,
    };
  }

  function renderStoryBlockBatchToolbar(scene = {}, visibleBlocks = [], selectedIds = [], options = {}) {
    const blocks = asList(scene?.blocks);
    if (!blocks.length) {
      return "";
    }
    const visibleIds = getBlockIds(visibleBlocks);
    const model = getStoryBlockSelectionModel(blocks, selectedIds, visibleIds);
    const busy = options.busy === true;
    const disabled = (condition) => (busy || condition ? "disabled" : "");
    const selectionLabel = model.selectedCount
      ? `已选 ${model.selectedCount} 张${model.hiddenSelectedCount ? `，其中 ${model.hiddenSelectedCount} 张在筛选外` : ""}`
      : "还没有建立选区";
    const rangeHint = model.selectedCount
      ? model.contiguous
        ? "这是连续选区，可整段移动、复制或删除。"
        : "这是分散选区，移动时会保持卡片之间的相对顺序。"
      : "点卡片左上角的“多选”，按住 Shift 再点可连续勾选。";
    const repairHint = "调整顺序后若 BGM 的自定义结束点失效，会自动退回到“下一首音乐接管”。";

    return `
      <section class="story-batch-toolbar ${model.selectedCount ? "has-selection" : ""}" data-slot="story-block-batch-toolbar" aria-label="剧情卡片剪辑选区">
        <div class="story-batch-copy">
          <span class="story-batch-kicker">剪辑选区</span>
          <strong>${escapeHtml(selectionLabel)}</strong>
          <small>${escapeHtml(rangeHint)}</small>
        </div>
        <div class="story-batch-select-actions" aria-label="选区范围">
          <button type="button" class="toolbar-button" data-action="select-all-visible-story-blocks" ${disabled(!model.canSelectVisible)}>
            ${model.visibleCount === model.blockCount ? "全选本场" : `全选当前 ${model.visibleCount} 张`}
          </button>
          <button type="button" class="toolbar-button" data-action="clear-story-block-selection" ${disabled(!model.canClear)}>清空选区</button>
        </div>
        <div class="story-batch-operation-rail" ${model.selectedCount ? "" : "hidden"} aria-label="批量编排操作">
          <button type="button" class="story-batch-operation" data-action="move-story-block-selection-start" ${disabled(!model.canMoveStart)}>移到开头</button>
          <button type="button" class="story-batch-operation" data-action="move-story-block-selection-up" ${disabled(!model.canMoveUp)}>上移一格</button>
          <button type="button" class="story-batch-operation" data-action="move-story-block-selection-down" ${disabled(!model.canMoveDown)}>下移一格</button>
          <button type="button" class="story-batch-operation" data-action="move-story-block-selection-end" ${disabled(!model.canMoveEnd)}>移到末尾</button>
          <button type="button" class="story-batch-operation is-copy" data-action="duplicate-story-block-selection" ${disabled(false)}>复制选区</button>
          <button type="button" class="story-batch-operation is-danger" data-action="delete-story-block-selection" ${disabled(false)}>删除选区</button>
        </div>
        <span class="story-batch-safety" ${model.selectedCount ? "" : "hidden"}>${escapeHtml(repairHint)}</span>
      </section>
    `;
  }

  function createStoryBlockBatchController(options = {}) {
    const getScene = typeof options.getScene === "function" ? options.getScene : () => null;
    const getVisibleBlocks =
      typeof options.getVisibleBlocks === "function" ? options.getVisibleBlocks : (scene) => asList(scene?.blocks);
    const getSelectedIds = typeof options.getSelectedIds === "function" ? options.getSelectedIds : () => [];
    const getAnchorId = typeof options.getAnchorId === "function" ? options.getAnchorId : () => "";
    const getFocusedBlockId =
      typeof options.getFocusedBlockId === "function" ? options.getFocusedBlockId : () => "";
    const setSelection = typeof options.setSelection === "function" ? options.setSelection : () => {};
    const getBusy = typeof options.getBusy === "function" ? options.getBusy : () => false;
    const setBusy = typeof options.setBusy === "function" ? options.setBusy : () => {};
    const onUiChange = typeof options.onUiChange === "function" ? options.onUiChange : () => {};
    const onToolbarChange =
      typeof options.onToolbarChange === "function" ? options.onToolbarChange : onUiChange;
    const setStatus = typeof options.setStatus === "function" ? options.setStatus : () => {};
    const showToast = typeof options.showToast === "function" ? options.showToast : () => {};
    const flushPendingChanges =
      typeof options.flushPendingChanges === "function" ? options.flushPendingChanges : async () => true;
    const cloneScene =
      typeof options.cloneScene === "function"
        ? options.cloneScene
        : (scene) => JSON.parse(JSON.stringify(scene));
    const persistScene = typeof options.persistScene === "function" ? options.persistScene : async () => false;
    const duplicateBlockForScene =
      typeof options.duplicateBlockForScene === "function" ? options.duplicateBlockForScene : null;
    const showConfirm = typeof options.showConfirm === "function" ? options.showConfirm : async () => false;
    const getBlockSummary =
      typeof options.getBlockSummary === "function"
        ? options.getBlockSummary
        : (block) => ({ title: block?.text || block?.id || "剧情卡片" });

    function getCheckedIds(scene = getScene()) {
      return normalizeStoryBlockSelection(scene?.blocks ?? [], getSelectedIds());
    }

    function normalizeSelection(scene = getScene()) {
      const selectedIds = getCheckedIds(scene);
      const anchorId = normalizeStoryBlockSelectionAnchor(
        scene?.blocks ?? [],
        getAnchorId(),
        selectedIds
      );
      setSelection(selectedIds, anchorId);
      return selectedIds;
    }

    function toggle(blockId, toggleOptions = {}) {
      const scene = getScene();
      if (!scene || getBusy()) {
        return false;
      }
      const safeBlockId = cleanId(blockId);
      const checkedIds = getCheckedIds(scene);
      const result = updateStoryBlockSelection(scene.blocks, checkedIds, safeBlockId, {
        anchorId: getAnchorId(),
        checked: !checkedIds.includes(safeBlockId),
        range: toggleOptions.range === true,
      });
      setSelection(result.selectedIds, result.anchorId);
      onUiChange();
      setStatus(`${toggleOptions.range === true ? "连续选区" : "剪辑选区"}现在有 ${result.selectedIds.length} 张卡片`);
      return result.changed;
    }

    function selectVisible() {
      const scene = getScene();
      if (!scene || getBusy()) {
        return false;
      }
      const visibleBlocks = getVisibleBlocks(scene);
      const selectedIds = selectVisibleStoryBlocks(
        scene.blocks,
        getCheckedIds(scene),
        visibleBlocks.map((block) => block.id)
      );
      const anchorId = getAnchorId() || selectedIds[selectedIds.length - 1] || "";
      setSelection(selectedIds, anchorId);
      onUiChange();
      setStatus(`已将当前可见的 ${visibleBlocks.length} 张卡片加入剪辑选区`);
      showToast(`剪辑选区现在有 ${selectedIds.length} 张卡片`);
      return true;
    }

    function clear() {
      if (getBusy()) {
        return false;
      }
      setSelection([], "");
      onUiChange();
      setStatus("剧情卡片剪辑选区已清空");
      return true;
    }

    function getSuccessMessage(plan = {}) {
      const repairCount = Number(plan.repairCount ?? 0);
      if (repairCount <= 0) {
        return plan.message ?? "剧情卡片批量操作完成";
      }
      return `${plan.message ?? "剧情卡片批量操作完成"}；同时修复了 ${repairCount} 处失效的 BGM 结束范围`;
    }

    async function applyPlan(buildPlan, applyOptions = {}) {
      if (getBusy()) {
        setStatus("上一项批量编排仍在保存，请稍等...");
        return false;
      }

      setBusy(true);
      onToolbarChange();
      try {
        if (!(await flushPendingChanges())) {
          return false;
        }
        const scene = getScene();
        if (!scene) {
          return false;
        }
        const checkedIds = getCheckedIds(scene);
        const updatedScene = cloneScene(scene);
        const plan = buildPlan(updatedScene, checkedIds);
        if (!plan?.changed) {
          const reason = plan?.reason ?? "这次没有需要修改的卡片顺序";
          setStatus(reason);
          showToast(reason);
          return false;
        }

        updatedScene.blocks = plan.blocks;
        const focusedBlockId = cleanId(getFocusedBlockId());
        const currentFocusExists = updatedScene.blocks.some((block) => cleanId(block?.id) === focusedBlockId);
        const selectedBlockId =
          applyOptions.focusNewSelection === true
            ? cleanId(plan.selectedBlockId)
            : currentFocusExists
              ? focusedBlockId
              : cleanId(plan.selectedBlockId);
        const previewBlockIndex = Math.max(
          updatedScene.blocks.findIndex((block) => cleanId(block?.id) === selectedBlockId),
          0
        );
        const nextSelectedIds = normalizeStoryBlockSelection(updatedScene.blocks, plan.selectedIds);
        const nextAnchorId = nextSelectedIds[nextSelectedIds.length - 1] ?? "";
        const successMessage = getSuccessMessage(plan);
        const success = await persistScene(updatedScene, {
          selectedSceneId: updatedScene.id,
          selectedBlockId: selectedBlockId || null,
          previewSceneId: updatedScene.id,
          previewBlockIndex,
          storyBlockCheckedIds: nextSelectedIds,
          storyBlockSelectionAnchorId: nextAnchorId,
          successMessage,
        });
        if (success) {
          setSelection(nextSelectedIds, nextAnchorId);
          showToast(successMessage);
        }
        return Boolean(success);
      } finally {
        setBusy(false);
        onUiChange();
      }
    }

    function reorder(action) {
      return applyPlan(
        (updatedScene, checkedIds) =>
          buildStoryBlockReorderPlan(updatedScene.blocks, checkedIds, action)
      );
    }

    function duplicate() {
      return applyPlan(
        (updatedScene, checkedIds) =>
          buildStoryBlockDuplicatePlan(updatedScene.blocks, checkedIds, {
            duplicateBlock: duplicateBlockForScene
              ? (sourceBlock, context) =>
                  duplicateBlockForScene(
                    { ...updatedScene, blocks: context.existingBlocks },
                    sourceBlock
                  )
              : null,
          }),
        { focusNewSelection: true }
      );
    }

    async function remove() {
      const scene = getScene();
      const checkedIds = getCheckedIds(scene);
      if (!scene || !checkedIds.length || getBusy()) {
        return false;
      }
      const checked = new Set(checkedIds);
      const previewTitles = asList(scene.blocks)
        .filter((block) => checked.has(cleanId(block?.id)))
        .slice(0, 3)
        .map((block) => `“${getBlockSummary(block, scene).title}”`)
        .join("、");
      const hiddenCount = Math.max(checkedIds.length - 3, 0);
      const shouldDelete = await showConfirm({
        title: `删除选中的 ${checkedIds.length} 张卡片？`,
        message: `将删除 ${previewTitles}${hiddenCount ? ` 等 ${checkedIds.length} 张卡片` : ""}。这会作为一次操作写入项目安全网，可用撤销恢复。`,
        tone: "danger",
        confirmLabel: `删除 ${checkedIds.length} 张`,
        cancelLabel: "保留这些卡片",
      });
      if (!shouldDelete) {
        return false;
      }
      return applyPlan(
        (updatedScene, selectedIds) =>
          buildStoryBlockDeletePlan(updatedScene.blocks, selectedIds)
      );
    }

    async function applyFocusedPlan(buildPlan) {
      if (getBusy()) {
        setStatus("上一项卡片操作仍在保存，请稍等...");
        return false;
      }
      setBusy(true);
      onToolbarChange();
      try {
        if (!(await flushPendingChanges())) {
          return false;
        }
        const scene = getScene();
        const focusedBlockId = cleanId(getFocusedBlockId());
        if (!scene || !focusedBlockId) {
          return false;
        }
        const updatedScene = cloneScene(scene);
        const plan = buildPlan(updatedScene, focusedBlockId);
        if (!plan?.changed) {
          if (plan?.reason) {
            setStatus(plan.reason);
          }
          return false;
        }
        if (plan.confirm && !(await showConfirm(plan.confirm))) {
          return false;
        }
        updatedScene.blocks = plan.blocks;
        const successMessage = getSuccessMessage(plan);
        const success = await persistScene(updatedScene, {
          selectedSceneId: updatedScene.id,
          selectedBlockId: plan.selectedBlockId || null,
          previewSceneId: updatedScene.id,
          previewBlockIndex: Math.max(Number(plan.previewIndex ?? 0), 0),
          successMessage,
        });
        if (success && plan.toast !== false) {
          showToast(successMessage);
        }
        return Boolean(success);
      } finally {
        setBusy(false);
        onUiChange();
      }
    }

    function duplicateFocused() {
      return applyFocusedPlan((updatedScene, focusedBlockId) => {
        const currentIndex = asList(updatedScene.blocks).findIndex(
          (block) => cleanId(block?.id) === focusedBlockId
        );
        if (currentIndex < 0 || !duplicateBlockForScene) {
          return { changed: false };
        }
        const blocks = [...updatedScene.blocks];
        const duplicatedBlock = duplicateBlockForScene(
          { ...updatedScene, blocks },
          blocks[currentIndex]
        );
        blocks.splice(currentIndex + 1, 0, duplicatedBlock);
        return {
          changed: true,
          blocks,
          selectedBlockId: cleanId(duplicatedBlock?.id),
          previewIndex: currentIndex + 1,
          message: "这张卡片已经复制",
          toast: false,
        };
      });
    }

    function reorderFocused(blockId, targetBlockId, position = "before") {
      return applyFocusedPlan((updatedScene) => {
        const blocks = [...asList(updatedScene.blocks)];
        const originalOrder = getBlockIds(blocks).join("|");
        const currentIndex = blocks.findIndex((block) => cleanId(block?.id) === cleanId(blockId));
        if (currentIndex < 0) {
          return { changed: false };
        }
        const [movedBlock] = blocks.splice(currentIndex, 1);
        const targetIndex = blocks.findIndex((block) => cleanId(block?.id) === cleanId(targetBlockId));
        if (targetIndex < 0) {
          return { changed: false };
        }
        const rawInsertIndex = position === "after" ? targetIndex + 1 : targetIndex;
        const insertIndex = Math.max(0, Math.min(rawInsertIndex, blocks.length));
        blocks.splice(insertIndex, 0, movedBlock);
        if (getBlockIds(blocks).join("|") === originalOrder) {
          return { changed: false, reason: "卡片顺序没有变化" };
        }
        const repaired = repairInvalidMusicRanges(blocks);
        return {
          changed: true,
          blocks: repaired.blocks,
          selectedBlockId: cleanId(movedBlock?.id),
          previewIndex: repaired.blocks.findIndex((block) => cleanId(block?.id) === cleanId(movedBlock?.id)),
          repairCount: repaired.repairCount,
          message: "卡片顺序已更新",
        };
      });
    }

    function moveFocused(direction) {
      return applyFocusedPlan((updatedScene, focusedBlockId) => {
        const blocks = [...asList(updatedScene.blocks)];
        const currentIndex = blocks.findIndex((block) => cleanId(block?.id) === focusedBlockId);
        const targetIndex = currentIndex + Number(direction);
        if (currentIndex < 0) {
          return { changed: false };
        }
        if (targetIndex < 0 || targetIndex >= blocks.length) {
          return {
            changed: false,
            reason: Number(direction) < 0 ? "这张卡片已经在最上面了" : "这张卡片已经在最下面了",
          };
        }
        [blocks[currentIndex], blocks[targetIndex]] = [blocks[targetIndex], blocks[currentIndex]];
        const repaired = repairInvalidMusicRanges(blocks);
        return {
          changed: true,
          blocks: repaired.blocks,
          selectedBlockId: focusedBlockId,
          previewIndex: targetIndex,
          repairCount: repaired.repairCount,
          message: Number(direction) < 0 ? "卡片已上移一格" : "卡片已下移一格",
          toast: false,
        };
      });
    }

    function deleteFocused() {
      return applyFocusedPlan((updatedScene, focusedBlockId) => {
        const blocks = [...asList(updatedScene.blocks)];
        const blockIndex = blocks.findIndex((block) => cleanId(block?.id) === focusedBlockId);
        if (blockIndex < 0) {
          return { changed: false };
        }
        const block = blocks[blockIndex];
        const summary = getBlockSummary(block, updatedScene);
        blocks.splice(blockIndex, 1);
        const repaired = repairInvalidMusicRanges(blocks);
        const previewIndex = repaired.blocks.length
          ? Math.min(blockIndex, repaired.blocks.length - 1)
          : 0;
        return {
          changed: true,
          blocks: repaired.blocks,
          selectedBlockId: cleanId(repaired.blocks[previewIndex]?.id),
          previewIndex,
          repairCount: repaired.repairCount,
          message: "这张卡片已经删除",
          toast: false,
          confirm: {
            title: "删除这张剧情卡片？",
            message: `要删除这张“${summary.title}”卡片吗？删除后会立刻写回项目文件。`,
            tone: "danger",
            confirmLabel: "删除卡片",
            cancelLabel: "保留卡片",
          },
        };
      });
    }

    return Object.freeze({
      getCheckedIds,
      normalizeSelection,
      toggle,
      selectVisible,
      clear,
      applyPlan,
      reorder,
      duplicate,
      remove,
      duplicateFocused,
      reorderFocused,
      moveFocused,
      deleteFocused,
    });
  }

  global.CanvasiaEditorStoryBlockBatch = Object.freeze({
    normalizeStoryBlockSelection,
    normalizeStoryBlockSelectionAnchor,
    updateStoryBlockSelection,
    selectVisibleStoryBlocks,
    getStoryBlockSelectionModel,
    repairInvalidMusicRanges,
    buildStoryBlockReorderPlan,
    buildStoryBlockDuplicatePlan,
    buildStoryBlockDeletePlan,
    renderStoryBlockBatchToolbar,
    createStoryBlockBatchController,
  });
})(typeof window !== "undefined" ? window : globalThis);
