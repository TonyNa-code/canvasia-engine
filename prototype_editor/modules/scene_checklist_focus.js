(function attachSceneChecklistFocusTools(global) {
  function cleanText(value) {
    return String(value ?? "").trim();
  }

  function getAddBlockOptionsFromDataset(dataset = {}) {
    const source = dataset && typeof dataset === "object" ? dataset : {};
    return {
      checklistCompleteItem: cleanText(source.sceneChecklistComplete),
    };
  }

  function shouldCompleteFocus(focus, checklistItem) {
    const safeItem = cleanText(checklistItem);
    return Boolean(safeItem && focus && typeof focus === "object" && cleanText(focus.item) === safeItem);
  }

  function getFocusTitle(focus) {
    return cleanText(focus?.title) || cleanText(focus?.label) || "当前清单项";
  }

  function buildCompletionFeedback(focus, blockLabel) {
    const title = getFocusTitle(focus);
    const safeBlockLabel = cleanText(blockLabel) || "剧情卡片";
    return {
      title,
      statusMessage: `已新增${safeBlockLabel}，${title}已处理；可试玩清单会重新计算。`,
      toastMessage: `${title}已处理`,
    };
  }

  global.CanvasiaEditorSceneChecklistFocus = Object.freeze({
    getAddBlockOptionsFromDataset,
    shouldCompleteFocus,
    buildCompletionFeedback,
  });
})(typeof window !== "undefined" ? window : globalThis);
