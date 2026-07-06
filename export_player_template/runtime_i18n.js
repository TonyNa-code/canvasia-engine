export const DEFAULT_RUNTIME_LANGUAGE = "zh-CN";

export const RUNTIME_LANGUAGE_LABELS = Object.freeze({
  "zh-CN": "简体中文",
  "ja-JP": "日本語",
  "en-US": "English",
});

export function normalizeLanguageCode(value, fallback = DEFAULT_RUNTIME_LANGUAGE) {
  const rawValue = String(value ?? "").trim();
  if (!rawValue || !/^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8}){0,2}$/.test(rawValue)) {
    return fallback;
  }
  const parts = rawValue.split("-");
  return [
    parts[0].toLowerCase(),
    ...parts.slice(1).map((part, index) => (index === 0 && [2, 3].includes(part.length) ? part.toUpperCase() : part)),
  ].join("-");
}

export function normalizeSupportedLanguages(rawLanguages, defaultLanguage = DEFAULT_RUNTIME_LANGUAGE) {
  const safeDefaultLanguage = normalizeLanguageCode(defaultLanguage, DEFAULT_RUNTIME_LANGUAGE);
  const languages = [];
  (Array.isArray(rawLanguages) ? rawLanguages : []).forEach((rawLanguage) => {
    const language = normalizeLanguageCode(rawLanguage, "");
    if (language && !languages.includes(language)) {
      languages.push(language);
    }
  });
  if (!languages.includes(safeDefaultLanguage)) {
    languages.unshift(safeDefaultLanguage);
  }
  return languages.length ? languages : [DEFAULT_RUNTIME_LANGUAGE];
}

export function buildRuntimeLanguageLabels(customLabels = {}) {
  return Object.freeze({
    ...RUNTIME_LANGUAGE_LABELS,
    ...(customLabels && typeof customLabels === "object" ? customLabels : {}),
  });
}

export function buildRuntimeLanguageFallbackChain({
  language = "",
  fallbackLanguage = "",
  defaultLanguage = DEFAULT_RUNTIME_LANGUAGE,
  defaultRuntimeLanguage = DEFAULT_RUNTIME_LANGUAGE,
} = {}) {
  const chain = [];
  [language, fallbackLanguage, defaultLanguage, defaultRuntimeLanguage].forEach((candidate) => {
    const safeLanguage = normalizeLanguageCode(candidate, "");
    if (safeLanguage && !chain.includes(safeLanguage)) {
      chain.push(safeLanguage);
    }
  });
  return chain.length ? chain : [DEFAULT_RUNTIME_LANGUAGE];
}

export function resolveLocalizedRuntimeValue(source, key, {
  language = "",
  fallbackLanguage = "",
  defaultLanguage = DEFAULT_RUNTIME_LANGUAGE,
  fallback = "",
} = {}) {
  const safeSource = source && typeof source === "object" ? source : {};
  const translations = safeSource[`${key}Translations`];
  const fallbackChain = buildRuntimeLanguageFallbackChain({ language, fallbackLanguage, defaultLanguage });
  const requestedLanguage = normalizeLanguageCode(language, "");
  const safeDefaultLanguage = normalizeLanguageCode(defaultLanguage, DEFAULT_RUNTIME_LANGUAGE);

  if (translations && typeof translations === "object") {
    for (const candidate of fallbackChain) {
      const text = String(translations[candidate] ?? "").trim();
      if (text) {
        return {
          value: text,
          requestedLanguage,
          usedLanguage: candidate,
          fallbackChain,
          fallbackUsed: Boolean(requestedLanguage && candidate !== requestedLanguage),
          missingRequestedLanguage: Boolean(
            requestedLanguage && requestedLanguage !== safeDefaultLanguage && !String(translations[requestedLanguage] ?? "").trim()
          ),
        };
      }
    }
  }

  const value = String(safeSource[key] ?? fallback ?? "");
  return {
    value,
    requestedLanguage,
    usedLanguage: "",
    fallbackChain,
    fallbackUsed: Boolean(requestedLanguage && requestedLanguage !== safeDefaultLanguage),
    missingRequestedLanguage: Boolean(requestedLanguage && requestedLanguage !== safeDefaultLanguage),
  };
}

export function getLocalizedRuntimeValue(source, key, options = {}) {
  return resolveLocalizedRuntimeValue(source, key, options).value;
}

function normalizeFallbackEvent(event = {}) {
  const requestedLanguage = normalizeLanguageCode(event.requestedLanguage, "");
  const usedLanguage = normalizeLanguageCode(event.usedLanguage, "");
  const key = String(event.key ?? "").trim() || "text";
  return {
    key,
    sourceId: String(event.sourceId ?? "").trim(),
    requestedLanguage,
    usedLanguage,
    fallbackChain: Array.isArray(event.fallbackChain)
      ? event.fallbackChain.map((language) => normalizeLanguageCode(language, "")).filter(Boolean)
      : [],
    valuePreview: String(event.valuePreview ?? "").trim().slice(0, 80),
    recordedAt: String(event.recordedAt ?? "").trim(),
  };
}

function countBy(events, key) {
  return events.reduce((counts, event) => {
    const value = String(event[key] ?? "").trim() || "unknown";
    counts[value] = (counts[value] ?? 0) + 1;
    return counts;
  }, {});
}

export function buildRuntimeLocalizationFallbackReport(events = []) {
  const normalizedEvents = (Array.isArray(events) ? events : [])
    .map((event) => normalizeFallbackEvent(event))
    .filter((event) => event.requestedLanguage || event.usedLanguage || event.sourceId || event.valuePreview);
  return Object.freeze({
    count: normalizedEvents.length,
    latest: normalizedEvents.at(-1) ?? null,
    byRequestedLanguage: countBy(normalizedEvents, "requestedLanguage"),
    byUsedLanguage: countBy(normalizedEvents, "usedLanguage"),
    byKey: countBy(normalizedEvents, "key"),
    events: Object.freeze(normalizedEvents),
  });
}

export function formatRuntimeLocalizationFallbackSummary(events = []) {
  const report = buildRuntimeLocalizationFallbackReport(events);
  if (!report.count) {
    return "当前游玩路径暂未发现缺译回退";
  }
  const latest = report.latest;
  const usedText = latest.usedLanguage ? `，已回退到 ${latest.usedLanguage}` : "，已使用原文";
  const targetText = latest.sourceId ? `${latest.key}:${latest.sourceId}` : latest.key;
  return `${report.count} 处${usedText} · 最近 ${targetText}`;
}
