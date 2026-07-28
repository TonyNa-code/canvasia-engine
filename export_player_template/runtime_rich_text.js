// Safe inline text presentation shared by the editor preview and exported Web Runtime.

export const RUNTIME_RICH_TEXT_KINDS = Object.freeze(["emphasis", "whisper", "color", "ruby"]);

const RICH_TEXT_MARKER_PATTERN = /\[\[\s*(em|whisper|color|ruby)\s*=\s*([^\[\]]*?)\s*\]\]/gi;
const SAFE_COLOR_PATTERN = /^#[0-9a-f]{6}$/i;

function freezeSegment(segment) {
  return Object.freeze({ ...segment });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function normalizeColor(value) {
  const color = String(value ?? "").trim();
  return SAFE_COLOR_PATTERN.test(color) ? color.toLowerCase() : "";
}

function parseMarker(command, payload) {
  const safeCommand = String(command ?? "").trim().toLowerCase();
  const safePayload = String(payload ?? "");

  if (safeCommand === "em" || safeCommand === "whisper") {
    if (!safePayload) return null;
    return {
      type: safeCommand === "em" ? "emphasis" : "whisper",
      text: safePayload,
    };
  }

  const separatorIndex = safePayload.indexOf("|");
  if (separatorIndex <= 0 || separatorIndex >= safePayload.length - 1) {
    return null;
  }
  const left = safePayload.slice(0, separatorIndex).trim();
  const right = safePayload.slice(separatorIndex + 1);

  if (safeCommand === "color") {
    const color = normalizeColor(left);
    return color && right ? { type: "color", color, text: right } : null;
  }
  if (safeCommand === "ruby") {
    return left && right.trim()
      ? { type: "ruby", text: left, annotation: right.trim().slice(0, 48) }
      : null;
  }
  return null;
}

function appendLiteral(sourceText, sourceStart, sourceEnd, plainParts, sourceToPlain, plainLength) {
  const literal = sourceText.slice(sourceStart, sourceEnd);
  plainParts.push(literal);
  for (let offset = 0; offset <= literal.length; offset += 1) {
    sourceToPlain[sourceStart + offset] = plainLength + offset;
  }
  return plainLength + literal.length;
}

export function parseRuntimeRichText(value) {
  const sourceText = String(value ?? "");
  const plainParts = [];
  const segments = [];
  const sourceToPlain = new Array(sourceText.length + 1).fill(0);
  let sourceIndex = 0;
  let plainLength = 0;
  let match;
  RICH_TEXT_MARKER_PATTERN.lastIndex = 0;

  while ((match = RICH_TEXT_MARKER_PATTERN.exec(sourceText)) !== null) {
    plainLength = appendLiteral(
      sourceText,
      sourceIndex,
      match.index,
      plainParts,
      sourceToPlain,
      plainLength
    );
    const marker = parseMarker(match[1], match[2]);
    if (!marker) {
      plainLength = appendLiteral(
        sourceText,
        match.index,
        RICH_TEXT_MARKER_PATTERN.lastIndex,
        plainParts,
        sourceToPlain,
        plainLength
      );
      sourceIndex = RICH_TEXT_MARKER_PATTERN.lastIndex;
      continue;
    }

    const markerStart = match.index;
    const markerEnd = RICH_TEXT_MARKER_PATTERN.lastIndex;
    for (let index = markerStart; index < markerEnd; index += 1) {
      sourceToPlain[index] = plainLength;
    }
    const segmentStart = plainLength;
    plainParts.push(marker.text);
    plainLength += marker.text.length;
    sourceToPlain[markerEnd] = plainLength;
    segments.push(freezeSegment({
      ...marker,
      start: segmentStart,
      end: plainLength,
    }));
    sourceIndex = markerEnd;
  }

  plainLength = appendLiteral(
    sourceText,
    sourceIndex,
    sourceText.length,
    plainParts,
    sourceToPlain,
    plainLength
  );
  sourceToPlain[sourceText.length] = plainLength;

  return Object.freeze({
    sourceText,
    plainText: plainParts.join(""),
    segments: Object.freeze(segments),
    sourceToPlain: Object.freeze(sourceToPlain),
    hasMarkup: segments.length > 0,
  });
}

export function stripRuntimeRichText(value) {
  return parseRuntimeRichText(value).plainText;
}

export function mapRuntimeRichTextSourceIndex(plan, sourceIndex) {
  const mapping = plan?.sourceToPlain ?? [];
  const safeIndex = Math.max(0, Math.min(Number(sourceIndex) || 0, Math.max(0, mapping.length - 1)));
  return Number(mapping[safeIndex]) || 0;
}

function renderSegment(segment, visibleText) {
  const escapedText = escapeHtml(visibleText);
  if (segment.type === "emphasis") {
    return `<strong class="runtime-rich-text runtime-rich-text-emphasis">${escapedText}</strong>`;
  }
  if (segment.type === "whisper") {
    return `<span class="runtime-rich-text runtime-rich-text-whisper">${escapedText}</span>`;
  }
  if (segment.type === "color") {
    return `<span class="runtime-rich-text runtime-rich-text-color" style="--runtime-rich-color:${segment.color}">${escapedText}</span>`;
  }
  if (segment.type === "ruby" && visibleText.length >= segment.end - segment.start) {
    return `<ruby class="runtime-rich-text runtime-rich-text-ruby"><rb>${escapedText}</rb><rt>${escapeHtml(segment.annotation)}</rt></ruby>`;
  }
  return escapedText;
}

export function renderRuntimeRichText(planOrValue, options = {}) {
  const plan = typeof planOrValue === "string" || planOrValue == null
    ? parseRuntimeRichText(planOrValue)
    : planOrValue;
  const plainText = String(plan?.plainText ?? "");
  const visibleEnd = Math.max(
    0,
    Math.min(
      plainText.length,
      options.visibleEnd == null ? plainText.length : Number(options.visibleEnd) || 0
    )
  );
  const parts = [];
  let cursor = 0;

  for (const segment of plan?.segments ?? []) {
    if (segment.start >= visibleEnd) break;
    if (segment.start > cursor) {
      parts.push(escapeHtml(plainText.slice(cursor, Math.min(segment.start, visibleEnd))));
    }
    const segmentEnd = Math.min(segment.end, visibleEnd);
    if (segmentEnd > segment.start) {
      parts.push(renderSegment(segment, plainText.slice(segment.start, segmentEnd)));
    }
    cursor = Math.max(cursor, segmentEnd);
    if (cursor >= visibleEnd) break;
  }

  if (cursor < visibleEnd) {
    parts.push(escapeHtml(plainText.slice(cursor, visibleEnd)));
  }
  return parts.join("");
}

export function buildRuntimeRichTextSummary(value) {
  const plan = parseRuntimeRichText(value);
  const counts = Object.fromEntries(RUNTIME_RICH_TEXT_KINDS.map((kind) => [kind, 0]));
  plan.segments.forEach((segment) => {
    counts[segment.type] += 1;
  });
  const labels = [
    ["emphasis", "处强调"],
    ["whisper", "处低声"],
    ["color", "处变色"],
    ["ruby", "处注音"],
  ]
    .filter(([kind]) => counts[kind] > 0)
    .map(([kind, label]) => `${counts[kind]} ${label}`);
  return Object.freeze({
    ...counts,
    hasMarkup: plan.hasMarkup,
    label: labels.join(" · ") || "使用普通文字",
  });
}

const runtimeRichTextApi = Object.freeze({
  RUNTIME_RICH_TEXT_KINDS,
  parseRuntimeRichText,
  stripRuntimeRichText,
  mapRuntimeRichTextSourceIndex,
  renderRuntimeRichText,
  buildRuntimeRichTextSummary,
});

globalThis.CanvasiaRuntimeRichText = runtimeRichTextApi;
