import { buildSpeakerFocusPresentation } from "./runtime_speaker_focus.js";


export function collectRenderableCharacterCards(visibleCharacters, characterTransitionEvent = null) {
  const cards = [...(visibleCharacters ?? [])];
  if (characterTransitionEvent?.mode === "hide" && characterTransitionEvent.characterState) {
    cards.push({
      ...characterTransitionEvent.characterState,
      __ghostMode: "hide",
    });
  }
  return cards;
}


export function buildCharacterCardPresentation(characterState, options = {}) {
  const classes = ["sprite-card"];
  const activeCharacterId = options.activeCharacterId ?? null;
  const characterTransitionEvent = options.characterTransitionEvent ?? null;
  const characterEmphasisEvent = options.characterEmphasisEvent ?? null;
  const visualComfortMode = options.visualComfortMode ?? "standard";
  const isGhostHide = characterState?.__ghostMode === "hide";
  const speakerFocusPresentation = buildSpeakerFocusPresentation({
    characterId: characterState?.characterId,
    activeCharacterId,
    visibleCharacterIds: options.visibleCharacterIds ?? [],
    gameUiConfig: options.gameUiConfig ?? {},
    visualComfortMode,
    isLeaving: isGhostHide,
  });
  const transition = characterTransitionEvent
    ? options.getSafeTransition(characterTransitionEvent.transition)
    : "none";
  const transitionDurationMs = characterTransitionEvent
    ? options.scaleVisualTransitionMs(
        options.getSafeTransitionDurationMs(characterTransitionEvent.durationMs),
        visualComfortMode
      )
    : options.scaleVisualTransitionMs(options.getSafeTransitionDurationMs(), visualComfortMode);
  const isMoving =
    characterTransitionEvent?.mode === "move" &&
    characterTransitionEvent.characterId === characterState?.characterId;
  const stageStyle = `${options.getCharacterStageStyle(characterState?.stage, characterState?.position)}${
    isMoving ? options.getCharacterMotionStyle(characterTransitionEvent) : ""
  }--sprite-transition-ms:${transitionDurationMs}ms;${speakerFocusPresentation.style}`;

  classes.push(...speakerFocusPresentation.classNames);
  if (options.shouldBlurCharacter?.(characterState?.position, options.depthBlur)) {
    classes.push("is-depth-muted");
    classes.push(`depth-strength-${options.getSafeDepthBlurStrength(options.depthBlur?.strength)}`);
  } else if (options.depthBlur) {
    classes.push("is-depth-focus");
  }
  if (characterTransitionEvent?.mode === "show" && characterTransitionEvent.characterId === characterState?.characterId) {
    classes.push("is-entering");
  }
  if (isMoving) classes.push("is-moving");
  if (isGhostHide) classes.push("is-leaving");
  classes.push("is-breathing");
  if (activeCharacterId === characterState?.characterId) classes.push("is-speaking");
  if (characterEmphasisEvent?.characterId === characterState?.characterId) classes.push("is-emphasis");

  return Object.freeze({
    classes: Object.freeze(classes),
    transition,
    transitionDurationMs,
    stageStyle,
    speakerFocusPresentation,
    isGhostHide,
    isMoving,
  });
}


export function renderCharacterCards(model = {}, options = {}) {
  const cards = collectRenderableCharacterCards(model.visibleCharacters, model.characterTransitionEvent);
  if (cards.length === 0) return options.emptyMarkup ?? "";
  const visibleCharacterIds = cards
    .filter((item) => item?.__ghostMode !== "hide")
    .map((item) => item?.characterId)
    .filter(Boolean);
  return cards
    .sort((left, right) => options.getPositionOrder(left?.position) - options.getPositionOrder(right?.position))
    .map((characterState) => {
      const presentation = buildCharacterCardPresentation(characterState, {
        ...options,
        ...model,
        visibleCharacterIds,
      });
      return options.renderCard(characterState, presentation);
    })
    .join("");
}


const runtimeCharacterCardsApi = Object.freeze({
  collectRenderableCharacterCards,
  buildCharacterCardPresentation,
  renderCharacterCards,
});

globalThis.CanvasiaRuntimeCharacterCards = runtimeCharacterCardsApi;
