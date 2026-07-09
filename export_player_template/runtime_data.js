import {
  DEFAULT_RUNTIME_LANGUAGE,
  buildRuntimeLanguageLabels,
  normalizeLanguageCode,
  normalizeSupportedLanguages,
} from "./runtime_i18n.js";

export const CHOICE_CONTINUE_TARGET = "__continue__";

export function isChoiceContinueTarget(value) {
  return String(value ?? "").trim() === CHOICE_CONTINUE_TARGET;
}

export function orderChapters(chapters, chapterOrder) {
  if (!chapterOrder?.length) {
    return chapters;
  }

  const chapterMap = new Map(chapters.map((chapter) => [chapter.chapterId, chapter]));
  return [
    ...chapterOrder.map((chapterId) => chapterMap.get(chapterId)).filter(Boolean),
    ...chapters.filter((chapter) => !chapterOrder.includes(chapter.chapterId)),
  ];
}

export function collectSceneOutgoingTargets(scene) {
  const targets = [];

  (scene?.blocks ?? []).forEach((block) => {
    if (block.type === "jump" && block.targetSceneId) {
      targets.push(block.targetSceneId);
      return;
    }

    if (block.type === "choice") {
      (block.options ?? []).forEach((option) => {
        if (option.gotoSceneId && !isChoiceContinueTarget(option.gotoSceneId)) {
          targets.push(option.gotoSceneId);
        }
      });
      return;
    }

    if (block.type === "condition") {
      (block.branches ?? []).forEach((branch) => {
        if (branch.gotoSceneId) {
          targets.push(branch.gotoSceneId);
        }
      });
      if (block.elseGotoSceneId) {
        targets.push(block.elseGotoSceneId);
      }
    }
  });

  return Array.from(new Set(targets.filter((target) => typeof target === "string" && target.trim())));
}

export function normalizeGameData(source = {}) {
  const project = source.project ?? {};
  const defaultLanguage = normalizeLanguageCode(
    source.i18n?.defaultLanguage ?? project.language,
    DEFAULT_RUNTIME_LANGUAGE
  );
  const supportedLanguages = normalizeSupportedLanguages(
    source.i18n?.supportedLanguages ?? project.supportedLanguages,
    defaultLanguage
  );
  const i18n = {
    defaultLanguage,
    fallbackLanguage: normalizeLanguageCode(source.i18n?.fallbackLanguage, defaultLanguage),
    supportedLanguages,
    languageLabels: buildRuntimeLanguageLabels(source.i18n?.languageLabels),
  };
  const assets = source.assets?.assets ?? [];
  const characters = source.characters?.characters ?? [];
  const variables = source.variables?.variables ?? [];
  const orderedChapters = orderChapters(source.chapters ?? [], project.chapterOrder ?? []);
  const assetsById = new Map(assets.map((asset) => [asset.id, asset]));
  const charactersById = new Map(characters.map((character) => [character.id, character]));
  const variablesById = new Map(variables.map((variable) => [variable.id, variable]));
  const scenesById = new Map();
  const scenes = [];

  orderedChapters.forEach((chapter) => {
    (chapter.scenes ?? []).forEach((scene) => {
      const fullScene = {
        ...scene,
        chapterId: chapter.chapterId,
        chapterName: chapter.name,
      };
      scenes.push(fullScene);
      scenesById.set(scene.id, fullScene);
    });
  });

  const endingScenes = scenes.filter((scene) => collectSceneOutgoingTargets(scene).length === 0);

  return {
    project,
    assets,
    assetsById,
    characters,
    charactersById,
    variables,
    variablesById,
    chapters: orderedChapters,
    scenes,
    scenesById,
    endingScenes,
    i18n,
    buildInfo: source.buildInfo ?? { copiedAssets: 0, missingAssets: [] },
  };
}
