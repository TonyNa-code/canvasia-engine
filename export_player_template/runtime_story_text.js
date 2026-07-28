import {
  parseRuntimeTextPacing,
} from "./runtime_text_pacing.js";
import {
  mapRuntimeRichTextSourceIndex,
  parseRuntimeRichText,
  renderRuntimeRichText,
} from "./runtime_rich_text.js";

function freezeCue(cue) {
  return Object.freeze({ ...cue });
}

export function parseRuntimeStoryText(value) {
  const sourceText = String(value ?? "");
  const pacingPlan = parseRuntimeTextPacing(sourceText);
  const richPlan = parseRuntimeRichText(pacingPlan.plainText);
  const cues = pacingPlan.cues.map((cue) => freezeCue({
    ...cue,
    index: mapRuntimeRichTextSourceIndex(richPlan, cue.index),
  }));
  return Object.freeze({
    sourceText,
    plainText: richPlan.plainText,
    cues: Object.freeze(cues),
    segments: richPlan.segments,
    hasCues: cues.length > 0,
    hasMarkup: richPlan.hasMarkup,
  });
}

export function stripRuntimeStoryText(value) {
  return parseRuntimeStoryText(value).plainText;
}

export function renderRuntimeStoryText(planOrValue, options = {}) {
  const plan = typeof planOrValue === "string" || planOrValue == null
    ? parseRuntimeStoryText(planOrValue)
    : planOrValue;
  return renderRuntimeRichText(plan, options);
}

const runtimeStoryTextApi = Object.freeze({
  parseRuntimeStoryText,
  stripRuntimeStoryText,
  renderRuntimeStoryText,
});

globalThis.CanvasiaRuntimeStoryText = runtimeStoryTextApi;
