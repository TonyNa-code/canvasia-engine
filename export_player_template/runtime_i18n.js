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
