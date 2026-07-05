(function attachValidationCacheTools(global) {
  const EMPTY_VALIDATION = Object.freeze({
    errors: Object.freeze([]),
    warnings: Object.freeze([]),
  });

  function normalizeValidationResult(result) {
    return {
      errors: Array.isArray(result?.errors) ? result.errors : [],
      warnings: Array.isArray(result?.warnings) ? result.warnings : [],
    };
  }

  function getNow(options = {}) {
    if (typeof options.now === "function") {
      return options.now();
    }
    if (global.performance && typeof global.performance.now === "function") {
      return global.performance.now();
    }
    return Date.now();
  }

  function createValidationCache(options = {}) {
    let entry = null;
    let hitCount = 0;
    let missCount = 0;
    let invalidationCount = 0;
    let lastDurationMs = 0;

    function invalidate() {
      entry = null;
      invalidationCount += 1;
    }

    function getOrCompute(key, compute, callOptions = {}) {
      const cacheKey = String(key ?? "");
      if (!callOptions.force && entry && entry.key === cacheKey) {
        hitCount += 1;
        return entry.result;
      }

      missCount += 1;
      const startedAt = getNow(options);
      const result = normalizeValidationResult(typeof compute === "function" ? compute() : EMPTY_VALIDATION);
      lastDurationMs = Math.max(0, getNow(options) - startedAt);
      entry = {
        key: cacheKey,
        result,
      };
      return result;
    }

    function getStats() {
      return {
        hitCount,
        missCount,
        invalidationCount,
        hasEntry: Boolean(entry),
        key: entry?.key ?? "",
        lastDurationMs: Number(lastDurationMs.toFixed(2)),
      };
    }

    return Object.freeze({
      getOrCompute,
      invalidate,
      getStats,
    });
  }

  global.CanvasiaEditorValidationCache = Object.freeze({
    EMPTY_VALIDATION,
    normalizeValidationResult,
    createValidationCache,
  });
})(typeof window !== "undefined" ? window : globalThis);
