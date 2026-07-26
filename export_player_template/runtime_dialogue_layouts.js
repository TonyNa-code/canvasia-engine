export const DIALOGUE_LAYOUT_IDS = Object.freeze(["adv", "nvl", "cinematic"]);

export const DIALOGUE_LAYOUT_LABELS = Object.freeze({
  adv: "经典 ADV 对话框",
  nvl: "NVL 满页叙事",
  cinematic: "电影字幕",
});

export const DIALOGUE_LAYOUT_DESCRIPTIONS = Object.freeze({
  adv: "角色名与正文显示在常规对话框中，适合大多数对白。",
  nvl: "同页保留前文并逐句累积，适合书信、回忆、长旁白和密集叙事。",
  cinematic: "把当前一句压成画面下方的电影字幕，适合短句、转场和演出高光。",
});

const DIALOGUE_BLOCK_TYPES = new Set(["dialogue", "narration"]);
const NVL_BOUNDARY_BLOCK_TYPES = new Set([
  "choice",
  "condition",
  "jump",
  "video_play",
  "credits_roll",
  "achievement_unlock",
]);
const DEFAULT_NVL_ENTRY_LIMIT = 8;
const MAX_NVL_ENTRY_LIMIT = 20;

function clampInteger(value, minimum, maximum, fallback) {
  const numeric = Number(value);
  const safeValue = Number.isFinite(numeric) ? Math.round(numeric) : fallback;
  return Math.min(maximum, Math.max(minimum, safeValue));
}

function getSafeBlockType(block) {
  return String(block?.type ?? "").trim().toLowerCase();
}

function defaultResolveDialogueEntry(block, index) {
  return {
    id: String(block?.id ?? `dialogue_${index + 1}`),
    blockIndex: index,
    type: getSafeBlockType(block),
    speakerName: String(block?.speakerName ?? block?.speakerId ?? (block?.type === "narration" ? "旁白" : "")),
    text: String(block?.text ?? ""),
  };
}

function sanitizeDialoguePageEntry(entry, block, index) {
  const source = entry && typeof entry === "object" ? entry : {};
  const sourceType = String(source.type ?? block?.type ?? "").trim().toLowerCase();
  return {
    id: String(source.id ?? block?.id ?? `dialogue_${index + 1}`),
    blockIndex: Number.isFinite(Number(source.blockIndex)) ? Number(source.blockIndex) : index,
    type: DIALOGUE_BLOCK_TYPES.has(sourceType) ? sourceType : "narration",
    speakerName: String(source.speakerName ?? ""),
    text: String(source.text ?? block?.text ?? ""),
  };
}

export function getSafeDialogueLayout(value, fallback = "adv") {
  const safeFallback = DIALOGUE_LAYOUT_IDS.includes(fallback) ? fallback : "adv";
  const layout = String(value ?? safeFallback).trim().toLowerCase();
  return DIALOGUE_LAYOUT_IDS.includes(layout) ? layout : safeFallback;
}

export function getDialogueLayoutLabel(value) {
  return DIALOGUE_LAYOUT_LABELS[getSafeDialogueLayout(value)];
}

export function getDialogueLayoutDescription(value) {
  return DIALOGUE_LAYOUT_DESCRIPTIONS[getSafeDialogueLayout(value)];
}

export function getDialogueLayoutFromBlock(block, fallback = "adv") {
  if (!DIALOGUE_BLOCK_TYPES.has(getSafeBlockType(block))) {
    return "adv";
  }
  return getSafeDialogueLayout(block?.dialogueLayout, fallback);
}

export function shouldStartNewNvlPage(block) {
  return getDialogueLayoutFromBlock(block) === "nvl" && block?.nvlPageBreak === true;
}

export function collectNvlPageEntries(blocks, currentIndex, options = {}) {
  const sourceBlocks = Array.isArray(blocks) ? blocks : [];
  const safeIndex = clampInteger(currentIndex, 0, Math.max(0, sourceBlocks.length - 1), 0);
  const currentBlock = sourceBlocks[safeIndex];
  if (!currentBlock || getDialogueLayoutFromBlock(currentBlock) !== "nvl") {
    return [];
  }

  const entryLimit = clampInteger(
    options.limit,
    1,
    MAX_NVL_ENTRY_LIMIT,
    DEFAULT_NVL_ENTRY_LIMIT
  );
  const resolveEntry =
    typeof options.resolveEntry === "function" ? options.resolveEntry : defaultResolveDialogueEntry;
  const entries = [];

  for (let index = safeIndex; index >= 0; index -= 1) {
    const block = sourceBlocks[index];
    const blockType = getSafeBlockType(block);
    if (DIALOGUE_BLOCK_TYPES.has(blockType)) {
      if (getDialogueLayoutFromBlock(block) !== "nvl") {
        break;
      }
      entries.unshift(sanitizeDialoguePageEntry(resolveEntry(block, index), block, index));
      if (shouldStartNewNvlPage(block) || entries.length >= entryLimit) {
        break;
      }
      continue;
    }
    if (NVL_BOUNDARY_BLOCK_TYPES.has(blockType)) {
      break;
    }
  }

  return entries;
}

export function buildDialogueLayoutPresentation(block, options = {}) {
  const layout = getDialogueLayoutFromBlock(block, options.fallbackLayout);
  const entries =
    layout === "nvl"
      ? collectNvlPageEntries(options.blocks, options.currentIndex, {
          limit: options.limit,
          resolveEntry: options.resolveEntry,
        })
      : [];
  return {
    layout,
    label: getDialogueLayoutLabel(layout),
    description: getDialogueLayoutDescription(layout),
    startsNewPage: shouldStartNewNvlPage(block),
    entries,
  };
}

const runtimeDialogueLayoutsApi = Object.freeze({
  DIALOGUE_LAYOUT_IDS,
  DIALOGUE_LAYOUT_LABELS,
  DIALOGUE_LAYOUT_DESCRIPTIONS,
  getSafeDialogueLayout,
  getDialogueLayoutLabel,
  getDialogueLayoutDescription,
  getDialogueLayoutFromBlock,
  shouldStartNewNvlPage,
  collectNvlPageEntries,
  buildDialogueLayoutPresentation,
});

globalThis.CanvasiaRuntimeDialogueLayouts = runtimeDialogueLayoutsApi;
