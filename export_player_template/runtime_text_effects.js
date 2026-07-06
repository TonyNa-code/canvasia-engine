const typewriterGraphemeSegmenter =
  typeof Intl !== "undefined" && typeof Intl.Segmenter === "function"
    ? new Intl.Segmenter(undefined, { granularity: "grapheme" })
    : null;
const TYPEWRITER_LEADING_OPENERS = "“‘\"'（([{【〔〈《「『";
const TYPEWRITER_TRAILING_CLOSERS = "”’\"'）)]}】〕〉》」』";
const TYPEWRITER_PERIOD_ABBREVIATIONS = new Set([
  "mr",
  "mrs",
  "ms",
  "dr",
  "prof",
  "sr",
  "jr",
  "st",
  "vs",
  "etc",
  "e.g",
  "i.e",
  "u.s",
  "u.k",
  "no",
  "fig",
  "vol",
  "ch",
  "dept",
  "inc",
  "ltd",
  "co",
]);
const TYPEWRITER_STEP_DELAYS = Object.freeze({
  slow: 42,
  normal: 28,
  fast: 18,
  instant: 0,
});

export function getSafeRuntimeTextSpeed(speed) {
  return Object.hasOwn(TYPEWRITER_STEP_DELAYS, speed) ? speed : "normal";
}

export function getNextTypewriterIndex(text, currentIndex) {
  const safeText = String(text ?? "");
  const safeIndex = Math.max(0, Math.min(Number(currentIndex) || 0, safeText.length));

  if (safeIndex >= safeText.length) {
    return safeText.length;
  }

  let nextIndex = getNextCodePointIndex(safeText, safeIndex);
  const currentChar = getCodePointAtIndex(safeText, safeIndex);
  nextIndex = includeTypewriterLeadingFollower(safeText, safeIndex, nextIndex);

  if (/[A-Za-z0-9]/.test(currentChar)) {
    let grouped = 1;
    while (nextIndex < safeText.length && grouped < 3) {
      const nextChar = getCodePointAtIndex(safeText, nextIndex);
      if (!/[A-Za-z0-9]/.test(nextChar)) {
        break;
      }
      nextIndex = getNextCodePointIndex(safeText, nextIndex);
      grouped += 1;
    }
  }

  nextIndex = includeTypewriterTrailingClosers(safeText, nextIndex);

  while (nextIndex < safeText.length && /\s/.test(getCodePointAtIndex(safeText, nextIndex))) {
    nextIndex = getNextCodePointIndex(safeText, nextIndex);
  }

  return nextIndex;
}

export function includeTypewriterLeadingFollower(text, currentIndex, index) {
  const safeText = String(text ?? "");
  const currentChar = getCodePointAtIndex(safeText, currentIndex);
  let nextIndex = Math.max(0, Math.min(Number(index) || 0, safeText.length));

  if (!TYPEWRITER_LEADING_OPENERS.includes(currentChar)) {
    return nextIndex;
  }

  while (nextIndex < safeText.length && TYPEWRITER_LEADING_OPENERS.includes(getCodePointAtIndex(safeText, nextIndex))) {
    nextIndex = getNextCodePointIndex(safeText, nextIndex);
  }

  return nextIndex < safeText.length ? getNextCodePointIndex(safeText, nextIndex) : nextIndex;
}

export function includeTypewriterTrailingClosers(text, index) {
  const safeText = String(text ?? "");
  let nextIndex = Math.max(0, Math.min(Number(index) || 0, safeText.length));
  while (nextIndex < safeText.length && TYPEWRITER_TRAILING_CLOSERS.includes(getCodePointAtIndex(safeText, nextIndex))) {
    nextIndex = getNextUnicodeScalarIndex(safeText, nextIndex);
  }
  return nextIndex;
}

export function getNextCodePointIndex(text, index) {
  const safeText = String(text ?? "");
  const safeIndex = Math.max(0, Math.min(Number(index) || 0, safeText.length));
  if (safeIndex >= safeText.length) {
    return safeText.length;
  }
  if (typewriterGraphemeSegmenter) {
    for (const segment of typewriterGraphemeSegmenter.segment(safeText)) {
      const segmentEnd = segment.index + segment.segment.length;
      if (safeIndex >= segment.index && safeIndex < segmentEnd) {
        return segmentEnd;
      }
    }
  }
  return getNextTypewriterClusterIndex(safeText, safeIndex);
}

export function getNextUnicodeScalarIndex(text, index) {
  const safeText = String(text ?? "");
  const safeIndex = Math.max(0, Math.min(Number(index) || 0, safeText.length));
  if (safeIndex >= safeText.length) {
    return safeText.length;
  }
  const codePoint = safeText.codePointAt(safeIndex);
  return safeIndex + (codePoint && codePoint > 0xffff ? 2 : 1);
}

export function getCodePointAtIndex(text, index) {
  const safeText = String(text ?? "");
  const safeIndex = Math.max(0, Math.min(Number(index) || 0, safeText.length));
  return safeText.slice(safeIndex, getNextUnicodeScalarIndex(safeText, safeIndex));
}

export function getTypewriterCodePointAtIndex(text, index) {
  return String(text ?? "").codePointAt(index) ?? 0;
}

export function isRegionalIndicatorSymbol(text, index) {
  const codePoint = getTypewriterCodePointAtIndex(text, index);
  return codePoint >= 0x1f1e6 && codePoint <= 0x1f1ff;
}

export function isTypewriterGraphemeExtension(text, index) {
  const codePoint = getTypewriterCodePointAtIndex(text, index);
  return (
    (codePoint >= 0x0300 && codePoint <= 0x036f) ||
    (codePoint >= 0x1ab0 && codePoint <= 0x1aff) ||
    (codePoint >= 0x1dc0 && codePoint <= 0x1dff) ||
    (codePoint >= 0x20d0 && codePoint <= 0x20ff) ||
    (codePoint >= 0xfe00 && codePoint <= 0xfe0f) ||
    (codePoint >= 0xe0100 && codePoint <= 0xe01ef) ||
    (codePoint >= 0x1f3fb && codePoint <= 0x1f3ff)
  );
}

export function getNextTypewriterClusterIndex(text, index) {
  const safeText = String(text ?? "");
  const safeIndex = Math.max(0, Math.min(Number(index) || 0, safeText.length));
  if (safeIndex >= safeText.length) {
    return safeText.length;
  }

  let nextIndex = getNextUnicodeScalarIndex(safeText, safeIndex);

  if (isRegionalIndicatorSymbol(safeText, safeIndex) && isRegionalIndicatorSymbol(safeText, nextIndex)) {
    return getNextUnicodeScalarIndex(safeText, nextIndex);
  }

  while (nextIndex < safeText.length) {
    const previousChar = getCodePointAtIndex(safeText, Math.max(0, nextIndex - 1));
    const currentChar = getCodePointAtIndex(safeText, nextIndex);

    if (isTypewriterGraphemeExtension(safeText, nextIndex) || previousChar === "\u200d") {
      nextIndex = getNextUnicodeScalarIndex(safeText, nextIndex);
      continue;
    }

    if (currentChar === "\u200d") {
      nextIndex = getNextUnicodeScalarIndex(safeText, getNextUnicodeScalarIndex(safeText, nextIndex));
      continue;
    }

    break;
  }

  return nextIndex;
}

export function getTypewriterPunctuationPause(text, fullText = "") {
  const anchorText = getTypewriterPauseAnchorText(text);
  const anchorChar = Array.from(anchorText).at(-1) ?? "";
  if (/(\.{3,}|…+)$/.test(anchorText)) {
    return 220;
  }
  if (anchorChar === "." && isTypewriterInlinePeriod(anchorText, fullText)) {
    return 0;
  }
  if (anchorChar === "." && isTypewriterAbbreviationPeriod(anchorText, fullText)) {
    return 0;
  }
  if (/[。！？!?.]/.test(anchorChar)) {
    return 260;
  }
  if (/[………。—-]/.test(anchorChar)) {
    return 220;
  }
  if (/[，、；;：:,]/.test(anchorChar)) {
    return 140;
  }
  return 0;
}

export function getTypewriterPauseAnchorText(text) {
  const chars = Array.from(String(text ?? "").trimEnd());
  while (chars.length > 1 && TYPEWRITER_TRAILING_CLOSERS.includes(chars.at(-1))) {
    chars.pop();
  }
  return chars.join("");
}

export function getTypewriterPauseAnchorChar(text) {
  return Array.from(getTypewriterPauseAnchorText(text)).at(-1) ?? "";
}

export function isTypewriterInlinePeriod(anchorText, fullText = "") {
  const safeAnchorText = String(anchorText ?? "");
  const safeFullText = String(fullText ?? "");
  const previousChar = Array.from(safeAnchorText).at(-2) ?? "";
  const nextChar = safeFullText.slice(safeAnchorText.length, safeAnchorText.length + 1);
  return /[A-Za-z0-9]/.test(previousChar) && /[A-Za-z0-9]/.test(nextChar);
}

export function isTypewriterAbbreviationPeriod(anchorText, fullText = "") {
  const safeAnchorText = String(anchorText ?? "");
  const safeFullText = String(fullText ?? "");
  const token = (safeAnchorText.match(/([A-Za-z](?:[A-Za-z]|\.)*)\.$/)?.[1] ?? "").toLowerCase();
  const nextChar = safeFullText.slice(safeAnchorText.length, safeAnchorText.length + 1);
  return TYPEWRITER_PERIOD_ABBREVIATIONS.has(token) && /\s/.test(nextChar);
}

export function getTypewriterStepDelay(speed, visibleText = "", fullText = "") {
  const safeSpeed = getSafeRuntimeTextSpeed(speed);
  if (safeSpeed === "instant") {
    return 0;
  }
  return TYPEWRITER_STEP_DELAYS[safeSpeed] + getTypewriterPunctuationPause(visibleText, fullText);
}
