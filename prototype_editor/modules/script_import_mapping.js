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

  global.CanvasiaEditorScriptImportMapping = Object.freeze({
    normalizeImportedLookupText,
    getImportedLookupValues,
    matchesImportedLookupHint,
    findImportedCharacterByHint,
    findImportedExpressionIdByHint,
    findImportedAssetIdByHint,
    getImportedEffectDuration,
  });
})(typeof window !== "undefined" ? window : globalThis);
