(function attachEditorTypewriterAdapter(global) {
  "use strict";

  function delegate(runtimeName) {
    return (...args) => {
      const runtimeTools = global.CanvasiaRuntimeTextEffects;
      const runtimeFunction = runtimeTools?.[runtimeName];
      if (typeof runtimeFunction !== "function") {
        throw new Error("共享打字机模块尚未加载，请刷新编辑器后重试。");
      }
      return runtimeFunction(...args);
    };
  }

  global.CanvasiaEditorTypewriter = Object.freeze({
    getCodePointAtIndex: delegate("getCodePointAtIndex"),
    getNextCodePointIndex: delegate("getNextCodePointIndex"),
    getNextTypewriterClusterIndex: delegate("getNextTypewriterClusterIndex"),
    getNextTypewriterIndex: delegate("getNextTypewriterIndex"),
    getNextUnicodeScalarIndex: delegate("getNextUnicodeScalarIndex"),
    getSafeTypewriterTextSpeed: delegate("getSafeRuntimeTextSpeed"),
    getTypewriterCodePointAtIndex: delegate("getTypewriterCodePointAtIndex"),
    getTypewriterPauseAnchorChar: delegate("getTypewriterPauseAnchorChar"),
    getTypewriterPauseAnchorText: delegate("getTypewriterPauseAnchorText"),
    getTypewriterPunctuationPause: delegate("getTypewriterPunctuationPause"),
    getTypewriterStepDelay: delegate("getTypewriterStepDelay"),
    includeTypewriterLeadingFollower: delegate("includeTypewriterLeadingFollower"),
    includeTypewriterTrailingClosers: delegate("includeTypewriterTrailingClosers"),
    isRegionalIndicatorSymbol: delegate("isRegionalIndicatorSymbol"),
    isTypewriterAbbreviationPeriod: delegate("isTypewriterAbbreviationPeriod"),
    isTypewriterGraphemeExtension: delegate("isTypewriterGraphemeExtension"),
    isTypewriterInlinePeriod: delegate("isTypewriterInlinePeriod"),
  });
})(typeof window !== "undefined" ? window : globalThis);
