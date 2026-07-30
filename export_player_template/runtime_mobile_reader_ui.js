import {
  createMobileReaderController,
  getSafeMobileReaderMode,
} from "./runtime_mobile_reader.js";

function replaceStrongText(button, value) {
  button?.querySelector("strong")?.replaceChildren(value);
}

export function createMobileReaderUiController(options = {}) {
  const {
    documentRef = globalThis.document,
    globalObject = globalThis,
    refs = {},
    state,
    getSnapshot = () => null,
    getOverlayRoot = () => null,
    isBlockingMediaSnapshot = () => false,
    renderHistory = () => "",
    renderEmpty = () => "",
    handleHistoryPanelClick = () => {},
    stopAutoAdvance = () => {},
    toggleDialogVisibility = () => {},
    persistPlaybackSettings = () => {},
    renderPlaybackControls = () => {},
    setInputMode = () => {},
  } = options;

  if (!state) {
    throw new TypeError("Mobile reader UI requires shared player state.");
  }

  function renderHistorySheet() {
    const active = Boolean(state.mobileReaderStatus?.active);
    const visible = active && state.mobileHistoryOpen && state.started && state.session;
    if (refs.mobileHistorySheet) {
      refs.mobileHistorySheet.hidden = !visible;
      refs.mobileHistorySheet.classList.toggle("is-visible", visible);
    }
    if (refs.mobileHistoryList) {
      refs.mobileHistoryList.innerHTML = state.session
        ? renderHistory(state.session)
        : renderEmpty("开始游戏后，这里会显示最近经过的剧情。");
    }
  }

  function render(snapshot = getSnapshot()) {
    const status = state.mobileReaderStatus ?? gestureController.getStatus();
    const active = Boolean(status?.active);
    const started = Boolean(state.started && state.session && refs.startOverlay?.hidden);
    const overlayRoot = getOverlayRoot();
    const blockedByOverlay = Boolean(overlayRoot && overlayRoot !== refs.mobileHistorySheet);
    const blockedByMedia = Boolean(snapshot && isBlockingMediaSnapshot(snapshot));

    if (refs.mobileReaderDock) {
      refs.mobileReaderDock.hidden =
        !active || !started || blockedByOverlay || blockedByMedia || state.mobileHistoryOpen;
    }
    if (refs.mobileAutoButton) {
      refs.mobileAutoButton.disabled = !started;
      refs.mobileAutoButton.setAttribute("aria-pressed", state.playback.autoPlay ? "true" : "false");
      replaceStrongText(refs.mobileAutoButton, state.playback.autoPlay ? "自动中" : "自动");
    }
    if (refs.mobileDialogButton) {
      refs.mobileDialogButton.disabled = !started;
      refs.mobileDialogButton.setAttribute("aria-pressed", state.dialogHidden ? "true" : "false");
      replaceStrongText(refs.mobileDialogButton, state.dialogHidden ? "显框" : "隐框");
    }
    if (refs.mobileHistoryButton) {
      refs.mobileHistoryButton.disabled = !started;
    }
    if (refs.mobileSystemButton) {
      refs.mobileSystemButton.disabled = !started;
    }
    if (refs.menuMobileReaderModeSelect) {
      refs.menuMobileReaderModeSelect.value = getSafeMobileReaderMode(state.playback.mobileReaderMode);
    }
    renderHistorySheet();
  }

  function closeHistory() {
    if (!state.mobileHistoryOpen) {
      return false;
    }
    state.mobileHistoryOpen = false;
    render();
    return true;
  }

  function openHistory() {
    if (!state.mobileReaderStatus?.active || !state.started || !state.session) {
      return false;
    }
    state.mobileHistoryOpen = true;
    stopAutoAdvance();
    render();
    refs.mobileHistoryCloseButton?.focus?.({ preventScroll: true });
    return true;
  }

  function handleGesture(action) {
    setInputMode("touch");
    if (action === "dialog" && state.mobileHistoryOpen) {
      closeHistory();
      return;
    }
    if (!state.started || !state.session || getOverlayRoot()) {
      return;
    }
    if (action === "history") {
      openHistory();
    } else if (action === "dialog") {
      toggleDialogVisibility();
    }
  }

  function handleStatus(status) {
    state.mobileReaderStatus = status;
    documentRef.documentElement.dataset.runtimeMobileReader = status?.active ? "active" : "inactive";
    if (!status?.active) {
      state.mobileHistoryOpen = false;
    }
    render();
  }

  function handleModeChange(event) {
    state.playback.mobileReaderMode = getSafeMobileReaderMode(event?.target?.value);
    persistPlaybackSettings();
    state.mobileHistoryOpen = false;
    gestureController.refresh("setting");
    renderPlaybackControls();
  }

  function handleHistorySheetClick(event) {
    if (event.target === refs.mobileHistorySheet) {
      closeHistory();
      return;
    }
    const ElementConstructor = globalObject.HTMLElement;
    if (!ElementConstructor || !(event.target instanceof ElementConstructor)) {
      return;
    }
    const shouldCloseAfterJump = Boolean(event.target.closest("[data-history-index]"));
    handleHistoryPanelClick(event);
    if (shouldCloseAfterJump) {
      closeHistory();
    }
  }

  const gestureController = createMobileReaderController({
    root: documentRef.documentElement,
    gestureTarget: refs.stageFrame,
    globalObject,
    documentRef,
    getMode: () => state.playback?.mobileReaderMode ?? "auto",
    onModeChange: handleStatus,
    onGesture: handleGesture,
  });

  return Object.freeze({
    start: gestureController.start,
    stop: gestureController.stop,
    refresh: gestureController.refresh,
    getStatus: gestureController.getStatus,
    render,
    openHistory,
    closeHistory,
    handleModeChange,
    handleHistorySheetClick,
  });
}
