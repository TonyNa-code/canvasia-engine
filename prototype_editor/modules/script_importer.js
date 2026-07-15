(function attachScriptImporterTools(global) {
  const SCRIPT_IMPORT_MAX_LINES = 120;
  const SCRIPT_IMPORT_MAX_BLOCKS = 80;
  const SCRIPT_IMPORT_MAX_OPTIONS = 6;
  const STAGE_DRAFT_TYPES = Object.freeze([
    "background",
    "character_show",
    "character_move",
    "character_hide",
    "music_play",
    "music_stop",
    "sfx_play",
    "video_play",
    "credits_roll",
    "wait",
    "screen_shake",
    "screen_flash",
    "screen_fade",
    "camera_zoom",
    "camera_pan",
    "screen_filter",
    "depth_blur",
    "particle_effect",
  ]);
  const ROUTE_DRAFT_TYPES = Object.freeze(["jump", "condition"]);
  const VARIABLE_DRAFT_TYPES = Object.freeze(["variable_set", "variable_add"]);
  const TEXT_SPEED_ALIASES = Object.freeze({
    slow: "slow",
    slower: "slow",
    low: "slow",
    normal: "normal",
    standard: "normal",
    default: "normal",
    fast: "fast",
    quick: "fast",
    rapid: "fast",
    instant: "instant",
    immediate: "instant",
    instantly: "instant",
    now: "instant",
    慢: "slow",
    慢速: "slow",
    正常: "normal",
    标准: "normal",
    默认: "normal",
    快: "fast",
    快速: "fast",
    立刻: "instant",
    立即: "instant",
    瞬间: "instant",
  });
  const TRANSITION_ALIASES = Object.freeze({
    dissolve: "fade",
    fade: "fade",
    fadein: "fade",
    fadeout: "fade",
    moveinleft: "slide_left",
    moveoutleft: "slide_left",
    slide_left: "slide_left",
    left: "slide_left",
    moveinright: "slide_right",
    moveoutright: "slide_right",
    slide_right: "slide_right",
    right: "slide_right",
    rise: "rise",
    moveinbottom: "rise",
    pop: "pop",
    zoomin: "pop",
    none: "none",
  });

  function normalizeScriptImportText(value) {
    return String(value ?? "")
      .replace(/\r\n?/g, "\n")
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
  }

  function trimImportedText(value, maxLength = 800) {
    return String(value ?? "").trim().slice(0, maxLength).trim();
  }

  function normalizeDirectiveToken(value) {
    return String(value ?? "")
      .trim()
      .toLowerCase()
      .replace(/[-\s]+/g, "_");
  }

  function escapeRegExp(value) {
    return String(value ?? "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  function stripWrappingQuotes(value) {
    const text = trimImportedText(value, 800);
    const match = text.match(/^["“”'‘’](.+?)["“”'‘’]$/u);
    return trimImportedText(match ? match[1] : text, 800);
  }

  function getSafeImportedTextSpeed(value) {
    const token = normalizeDirectiveToken(value).replace(/^text_speed_?/u, "");
    return TEXT_SPEED_ALIASES[token] ?? "";
  }

  function parseTextSpeedLine(line) {
    const match = String(line ?? "").trim().match(/^(?:text\s+speed|text_speed|speed|文字速度|文本速度|速度)\s*[:=]?\s*(\S+)$/iu);
    const textSpeed = getSafeImportedTextSpeed(match?.[1] ?? "");
    return textSpeed ? { textSpeed } : null;
  }

  function extractInlineTextSpeed(value) {
    let text = trimImportedText(value, 800);
    const speedPattern =
      /(?:\s*(?:[\[（(]\s*(?:text\s+speed|text_speed|speed|文字速度|文本速度|速度)\s*[:=]?\s*(\S+?)\s*[\]）)]|(?:text\s+speed|text_speed|speed|文字速度|文本速度|速度)\s*[:=]?\s*(\S+)))\s*$/iu;
    const match = text.match(speedPattern);
    const textSpeed = getSafeImportedTextSpeed(match?.[1] ?? match?.[2] ?? "");
    if (!textSpeed) {
      return { text, textSpeed: "" };
    }

    text = trimImportedText(text.replace(speedPattern, ""), 800);
    return { text, textSpeed };
  }

  function readLeadingArgument(value) {
    const text = trimImportedText(value, 240);
    const quoted = text.match(/^["“'‘](.+?)["”'’](?:\s+|$)(.*)$/u);
    if (quoted) {
      return {
        argument: trimImportedText(quoted[1], 120),
        rest: trimImportedText(quoted[2], 240),
      };
    }

    const match = text.match(/^(\S+)(?:\s+(.*))?$/u);
    return {
      argument: trimImportedText(match?.[1] ?? text, 120),
      rest: trimImportedText(match?.[2] ?? "", 240),
    };
  }

  function parseTimeMs(value, fallbackMs = 600) {
    const raw = String(value ?? "").trim().toLowerCase();
    const number = Number.parseFloat(raw);
    if (!Number.isFinite(number)) {
      return fallbackMs;
    }

    const ms = raw.endsWith("ms") ? number : number * 1000;
    return Math.round(Math.max(0, Math.min(ms, 30000)));
  }

  function parseTimeSeconds(value, fallbackSeconds = 0) {
    const raw = String(value ?? "").trim().toLowerCase();
    const number = Number.parseFloat(raw);
    if (!Number.isFinite(number)) {
      return fallbackSeconds;
    }

    const seconds = raw.endsWith("ms") ? number / 1000 : number;
    return Math.round(Math.max(0, Math.min(seconds, 21600)) * 10) / 10;
  }

  function parseWaitDurationSeconds(value, fallbackSeconds = 1) {
    const raw = String(value ?? "").trim().toLowerCase();
    const match = raw.match(/^([0-9.]+)\s*(ms|毫秒|s|sec|secs|second|seconds|秒)?$/iu);
    if (!match) {
      return fallbackSeconds;
    }

    const number = Number.parseFloat(match[1]);
    if (!Number.isFinite(number)) {
      return fallbackSeconds;
    }

    const unit = normalizeDirectiveToken(match[2] ?? "s");
    const seconds = unit === "ms" || unit === "毫秒" ? number / 1000 : number;
    return Math.round(Math.min(Math.max(seconds, 0.1), 30) * 10) / 10;
  }

  function parseInlineTimeMs(text, keyword, fallbackMs = 600) {
    const match = String(text ?? "").match(new RegExp(`\\b${keyword}\\s+([0-9.]+\\s*(?:ms|s)?)`, "i"));
    return match ? parseTimeMs(match[1], fallbackMs) : fallbackMs;
  }

  function parseInlineTimeSeconds(text, keywords, fallbackSeconds = 0) {
    const keywordPattern = Array.isArray(keywords) ? keywords.join("|") : keywords;
    const match = String(text ?? "").match(new RegExp(`\\b(?:${keywordPattern})\\s+([0-9.]+\\s*(?:ms|s)?)`, "i"));
    return match ? parseTimeSeconds(match[1], fallbackSeconds) : fallbackSeconds;
  }

  function parseInlineVolumePercent(text, fallback = 100) {
    const match = String(text ?? "").match(/\b(?:volume|vol)\s+([0-9.]+)%?/i);
    if (!match) {
      return fallback;
    }

    const number = Number.parseFloat(match[1]);
    return Number.isFinite(number) ? Math.round(Math.max(0, Math.min(number, 100))) : fallback;
  }

  function parseInlineTitle(text, fallback = "") {
    const quoted = String(text ?? "").match(/\b(?:title|name|as)\s+["“'‘](.+?)["”'’]/iu);
    if (quoted) {
      return trimImportedText(quoted[1], 80);
    }

    const titleStopWords =
      "volume|vol|from|start|to|end|duration|subtitle|sub|lines|staff|dark|light|transparent|contain|cover|fill|skip|skippable|no-?skip|unskippable";
    const plain = String(text ?? "").match(
      new RegExp(`\\b(?:title|name|as)\\s+([^,;]+?)(?=\\s+\\b(?:${titleStopWords})\\b|$)`, "iu")
    );
    return trimImportedText(plain?.[1] ?? fallback, 80);
  }

  function parseInlineSubtitle(text, fallback = "") {
    const quoted = String(text ?? "").match(/\b(?:subtitle|sub)\s+["“'‘](.+?)["”'’]/iu);
    return trimImportedText(quoted?.[1] ?? fallback, 120);
  }

  function parseInlineCreditsLines(text) {
    const quoted = String(text ?? "").match(/\b(?:lines|staff)\s+["“'‘](.+?)["”'’]/iu);
    return quoted
      ? quoted[1]
          .split(/\s*(?:\||\/|；|;)\s*/u)
          .map((line) => trimImportedText(line, 80))
          .filter(Boolean)
      : [];
  }

  function parseInlineVideoFit(text, fallback = "contain") {
    const token = String(text ?? "").match(/\b(contain|cover|fill)\b/i)?.[1]?.toLowerCase();
    return ["contain", "cover", "fill"].includes(token) ? token : fallback;
  }

  function parseInlineVideoSkippable(text, fallback = true) {
    const source = String(text ?? "");
    if (/(?:不可跳过|不能跳过|强制播放)|\b(?:no-?skip|unskippable|required|must\s+watch)\b/i.test(source)) {
      return false;
    }
    if (/(?:可跳过)|\b(?:skip|skippable|can\s+skip)\b/i.test(source)) {
      return true;
    }
    return fallback;
  }

  function parseInlineEnumToken(text, allowedValues, fallback, aliases = {}) {
    const tokens = String(text ?? "")
      .toLowerCase()
      .match(/[a-z_][a-z0-9_-]*/g) ?? [];
    const allowedSet = new Set(allowedValues);
    for (const token of tokens) {
      const normalized = aliases[token] ?? token;
      if (allowedSet.has(normalized)) {
        return normalized;
      }
    }
    return fallback;
  }

  function parseInlineEffectDurationToken(text, fallback = "medium") {
    return parseInlineEnumToken(text, ["short", "medium", "long"], fallback, {
      fast: "short",
      quick: "short",
      brief: "short",
      normal: "medium",
      slow: "long",
      linger: "long",
    });
  }

  function parseInlineCreditsBackground(text, fallback = "dark") {
    return parseInlineEnumToken(text, ["dark", "light", "transparent"], fallback, {
      clear: "transparent",
      overlay: "transparent",
    });
  }

  function parseInlineScreenFilterPreset(text, fallback = "memory") {
    return parseInlineEnumToken(text, ["memory", "mono", "dream", "cold"], fallback, {
      sepia: "memory",
      nostalgic: "memory",
      warm: "memory",
      monochrome: "mono",
      blackwhite: "mono",
      grayscale: "mono",
      bw: "mono",
      dreamy: "dream",
      softlight: "dream",
      cool: "cold",
      blue: "cold",
    });
  }

  function parseInlineScreenFilterStrength(text, fallback = "medium") {
    return parseInlineEnumToken(text, ["soft", "medium", "strong"], fallback, {
      light: "soft",
      weak: "soft",
      normal: "medium",
      heavy: "strong",
      hard: "strong",
    });
  }

  function parseInlineDepthBlurFocus(text, fallback = "center") {
    return parseInlineEnumToken(text, ["left", "center", "right", "full"], fallback, {
      middle: "center",
      bg: "full",
      background: "full",
      all: "full",
    });
  }

  function parseInlineParticlePreset(text, fallback = "snow") {
    return parseInlineEnumToken(
      text,
      ["snow", "rain", "petals", "dust", "embers", "sparkles", "bubbles", "confetti", "smoke", "flame", "stardust", "glyphs"],
      fallback,
      {
        snowfall: "snow",
        sakura: "petals",
        flower: "petals",
        flowers: "petals",
        sparkle: "sparkles",
        sparks: "embers",
        fire: "flame",
        star: "stardust",
        stars: "stardust",
        magic: "glyphs",
        rune: "glyphs",
        runes: "glyphs",
      }
    );
  }

  function parseInlineParticleIntensity(text, fallback = "medium") {
    return parseInlineEnumToken(text, ["light", "medium", "heavy"], fallback, {
      soft: "light",
      weak: "light",
      normal: "medium",
      strong: "heavy",
      dense: "heavy",
    });
  }

  function parseInlineParticleSpeed(text, fallback = "medium") {
    return parseInlineEnumToken(text, ["slow", "medium", "fast"], fallback, {
      normal: "medium",
      quick: "fast",
      rapid: "fast",
    });
  }

  function parseInlineStageNumber(text, keywords) {
    const keywordPattern = (Array.isArray(keywords) ? keywords : [keywords]).map(escapeRegExp).join("|");
    const match = String(text ?? "").match(
      new RegExp(`(?:^|\\s)(?:${keywordPattern})\\s*[:=]?\\s*(-?[0-9.]+)\\s*%?`, "iu")
    );
    if (!match) {
      return null;
    }
    const value = Number.parseFloat(match[1]);
    return Number.isFinite(value) ? value : null;
  }

  function parseInlineCharacterStage(text) {
    const source = String(text ?? "");
    const stage = {};
    const stageEntries = [
      ["offsetX", ["x", "offsetx", "offset_x", "offset-x", "dx", "横向", "水平"]],
      ["offsetY", ["y", "offsety", "offset_y", "offset-y", "dy", "纵向", "垂直"]],
      ["scale", ["scale", "size", "zoom", "大小", "缩放"]],
      ["opacity", ["opacity", "alpha", "透明", "透明度"]],
      ["layer", ["layer", "z", "zindex", "z_index", "层级"]],
    ];

    stageEntries.forEach(([key, keywords]) => {
      const value = parseInlineStageNumber(source, keywords);
      if (value !== null) {
        stage[key] = value;
      }
    });

    if (/\b(?:no[-_\s]?flip|flipx?\s*(?:false|off|no|0))\b/iu.test(source)) {
      stage.flipX = false;
    } else if (/(?:镜像|反向)|\b(?:flip|flipx|mirror|mirrored)\b/iu.test(source)) {
      stage.flipX = true;
    }

    return Object.keys(stage).length ? stage : null;
  }

  function parseInlineCharacterMotionEasing(text, fallback = "ease_out") {
    const match = String(text ?? "").match(
      /\b(?:easing|ease|warp)\s+([a-z_-]+)\b/iu
    );
    const token = normalizeDirectiveToken(match?.[1] ?? fallback);
    const aliases = {
      easein: "ease_in",
      easeout: "ease_out",
      easeinout: "ease_in_out",
      smooth: "ease_in_out",
      bounce: "spring",
    };
    const easing = aliases[token] ?? token;
    return ["linear", "ease_in", "ease_out", "ease_in_out", "spring"].includes(easing)
      ? easing
      : fallback;
  }

  function parseDirectiveTransition(text, fallback = "fade") {
    const match = String(text ?? "").match(/\bwith\s+([a-zA-Z_-]+)/u);
    const raw = normalizeDirectiveToken(match?.[1] ?? fallback).replace(/_+$/g, "");
    return TRANSITION_ALIASES[raw] ?? fallback;
  }

  function parseDirectivePosition(text, fallback = "center") {
    const match = String(text ?? "").match(/\bat\s+(left|center|right|truecenter|middle)\b/i);
    const token = normalizeDirectiveToken(match?.[1] ?? fallback);
    if (token === "truecenter" || token === "middle") {
      return "center";
    }
    return ["left", "center", "right"].includes(token) ? token : fallback;
  }

  function removeDirectiveClauses(text) {
    let cleaned = trimImportedText(
      String(text ?? "")
        .replace(/\bwith\s+[a-zA-Z_-]+(?:\s+duration\s+[0-9.]+\s*(?:ms|s)?)?/iu, " ")
        .replace(/\bduration\s+[0-9.]+\s*(?:ms|s)?/iu, " ")
        .replace(/\bat\s+(left|center|right|truecenter|middle)\b/iu, " ")
        .replace(/\bfade(?:in|out)?\s+[0-9.]+\s*(?:ms|s)?/giu, " "),
      240
    );

    for (let index = 0; index < 3; index += 1) {
      cleaned = cleaned
        .replace(
        /(?:^|\s)(?:x|offsetx|offset_x|offset-x|dx|横向|水平|y|offsety|offset_y|offset-y|dy|纵向|垂直|scale|size|zoom|大小|缩放|opacity|alpha|透明|透明度|layer|z|zindex|z_index|层级)\s*[:=]?\s*-?[0-9.]+\s*%?/giu,
        " "
      )
        .replace(/(?:^|\s)(?:no[-_\s]?flip|flipx?\s*(?:false|off|no|0)|flipx?|mirror|mirrored|镜像|反向)\b/giu, " ");
    }

    return trimImportedText(cleaned.replace(/\s+/g, " "), 240);
  }

  function removeCharacterMotionClauses(text) {
    return trimImportedText(
      removeDirectiveClauses(text).replace(/\b(?:easing|ease|warp)\s+[a-z_-]+\b/giu, " ").replace(/\s+/g, " "),
      240
    );
  }

  function isIgnoredScriptLine(line) {
    return /^(?:#|\/\/|label\s+\S+\s*:|menu\s*:|return\b|call\s+\S+)/i.test(String(line ?? "").trim());
  }

  function parseChoiceLine(line) {
    const quotedChoice = String(line ?? "").match(/^["“](.+?)["”]\s*:$/u);
    if (quotedChoice) {
      return trimImportedText(quotedChoice[1], 160);
    }

    const match = String(line ?? "").match(/^(?:[-*•]|[0-9]+[.)、])\s*(.+)$/u);
    return match ? trimImportedText(match[1], 160) : "";
  }

  function parseChoiceEffectValue(value) {
    const text = stripWrappingQuotes(value);
    const normalized = normalizeDirectiveToken(text);
    if (["true", "yes", "on", "是", "开启"].includes(normalized)) {
      return true;
    }
    if (["false", "no", "off", "否", "关闭"].includes(normalized)) {
      return false;
    }
    const number = Number.parseFloat(text);
    if (Number.isFinite(number) && String(text).match(/^[+-]?[0-9.]+$/u)) {
      return number;
    }
    return trimImportedText(text, 120);
  }

  function parseChoiceEffectClause(clause) {
    const text = trimImportedText(clause, 180);
    if (!text) {
      return null;
    }

    const addMatch = text.match(/^([0-9A-Za-z_\-\u4e00-\u9fff]{1,64})\s*(\+=|-=|\+|-)\s*([+-]?[0-9.]+)$/u);
    if (addMatch) {
      const operator = addMatch[2];
      const amount = Number.parseFloat(addMatch[3]);
      const delta =
        operator === "+="
          ? amount
          : operator === "-="
            ? -amount
            : operator === "-"
              ? -Math.abs(amount)
              : Math.abs(amount);
      return Number.isFinite(amount)
        ? {
            type: "variable_add",
            variableHint: addMatch[1],
            value: delta,
          }
        : null;
    }

    const setMatch = text.match(/^([0-9A-Za-z_\-\u4e00-\u9fff]{1,64})\s*(?:=|:|is|to|为)\s*(.+)$/iu);
    if (setMatch) {
      return {
        type: "variable_set",
        variableHint: setMatch[1],
        value: parseChoiceEffectValue(setMatch[2]),
      };
    }

    return null;
  }

  function parseVariableActionLine(line) {
    const text = trimImportedText(line, 220);
    if (!text) {
      return null;
    }

    const addKeywordMatch = text.match(
      /^(?:add|increase|inc|增加|加)\s+([0-9A-Za-z_\-\u4e00-\u9fff]{1,64})(?:\s+(?:by|为|=))?\s*([+-]?[0-9.]+)$/iu
    );
    if (addKeywordMatch) {
      const value = Number.parseFloat(addKeywordMatch[2]);
      return Number.isFinite(value)
        ? {
            type: "variable_add",
            variableHint: addKeywordMatch[1],
            value,
          }
        : null;
    }

    const setKeywordMatch = text.match(/^(?:set|let|var|variable|设置|设定|变量)\s+(.+)$/iu);
    if (setKeywordMatch) {
      return parseChoiceEffectClause(setKeywordMatch[1]);
    }

    if (/^[0-9A-Za-z_\-\u4e00-\u9fff]{1,64}\s*(?:\+=|-=|=)\s*.+$/u.test(text)) {
      return parseChoiceEffectClause(text);
    }

    return null;
  }

  function parseConditionRuleClause(clause) {
    const text = trimImportedText(clause, 180);
    const match = text.match(
      /^([0-9A-Za-z_\-\u4e00-\u9fff]{1,64})\s*(>=|<=|==|!=|>|<|=|not[_\s-]?contains|contains|starts[_\s-]?with|ends[_\s-]?with)\s*(.+)$/iu
    );
    if (!match) {
      return null;
    }
    const operator = match[2].toLowerCase().replace(/[\s-]+/g, "_");
    return {
      variableHint: match[1],
      operator: operator === "=" ? "==" : operator,
      value: parseChoiceEffectValue(match[3]),
    };
  }

  function parseConditionLine(line) {
    const text = trimImportedText(line, 320);
    const match = text.match(/^(?:if|when|如果)\s+(.+?)\s*(?:->|=>)\s*(.+)$/iu);
    if (!match) {
      return null;
    }

    const targetParts = match[2].match(/^(.*?)(?:\s+(?:else|otherwise|否则)\s*(?:->|=>)?\s*(.+))?$/iu);
    const ruleText = trimImportedText(match[1], 180);
    const rules = ruleText
      .split(/\s*(?:&&|\band\b|且|并且)\s*/iu)
      .map(parseConditionRuleClause)
      .filter(Boolean);
    const targetHint = trimImportedText(targetParts?.[1] ?? "", 120);
    const elseTargetHint = trimImportedText(targetParts?.[2] ?? "", 120);

    if (!rules.length || !targetHint) {
      return null;
    }

    return {
      type: "condition",
      branches: [
        {
          when: rules,
          targetHint,
        },
      ],
      ...(elseTargetHint ? { elseTargetHint } : {}),
    };
  }

  function extractChoiceEffects(text) {
    const source = trimImportedText(text, 260);
    const match = source.match(/^(.*?)\s*[\[【(（]\s*(.+?)\s*[\]】)）]\s*$/u);
    if (!match) {
      return { text: source, effects: [] };
    }

    const effects = match[2]
      .split(/\s*(?:;|；|,|，)\s*/u)
      .map(parseChoiceEffectClause)
      .filter(Boolean);
    if (!effects.length) {
      return { text: source, effects: [] };
    }

    return {
      text: trimImportedText(match[1], 220),
      effects,
    };
  }

  function parseChoiceOptionLine(line) {
    const choiceText = parseChoiceLine(line);
    if (!choiceText) {
      return null;
    }

    const extracted = extractChoiceEffects(choiceText);
    const targetMatch = extracted.text.match(/^(.+?)\s*(?:->|=>)\s*(\S.+)$/u);
    return {
      text: trimImportedText(targetMatch?.[1] ?? extracted.text, 160),
      targetHint: trimImportedText(targetMatch?.[2] ?? "", 120),
      ...(extracted.effects.length ? { effects: extracted.effects } : {}),
    };
  }

  function parseDialogueLine(line) {
    const match = String(line ?? "").match(/^([^:：]{1,24})[:：]\s*(.+)$/u);
    if (!match) {
      return null;
    }

    const speakerName = trimImportedText(match[1], 80);
    const inlineOptions = extractInlineTextSpeed(match[2]);
    const text = inlineOptions.text;
    if (!speakerName || !text || ["旁白", "narration", "旁述"].includes(speakerName.toLowerCase())) {
      return text ? { type: "narration", text, ...(inlineOptions.textSpeed ? { textSpeed: inlineOptions.textSpeed } : {}) } : null;
    }

    return {
      type: "dialogue",
      speakerName,
      text,
      ...(inlineOptions.textSpeed ? { textSpeed: inlineOptions.textSpeed } : {}),
    };
  }

  function parseQuotedDialogueLine(line) {
    const text = String(line ?? "").trim();
    const dialogue = text.match(/^([^"“”]{1,32})\s+["“](.+?)["”](.*)$/u);
    if (dialogue) {
      const trailingOptions = extractInlineTextSpeed(dialogue[3]);
      const inlineOptions = extractInlineTextSpeed(dialogue[2]);
      return {
        type: "dialogue",
        speakerName: trimImportedText(dialogue[1], 80),
        text: inlineOptions.text,
        ...(trailingOptions.textSpeed || inlineOptions.textSpeed
          ? { textSpeed: trailingOptions.textSpeed || inlineOptions.textSpeed }
          : {}),
      };
    }

    const narration = text.match(/^["“](.+?)["”](.*)$/u);
    if (!narration) {
      return null;
    }

    const trailingOptions = extractInlineTextSpeed(narration[2]);
    const inlineOptions = extractInlineTextSpeed(narration[1]);
    return {
      type: "narration",
      text: inlineOptions.text,
      ...(trailingOptions.textSpeed || inlineOptions.textSpeed
        ? { textSpeed: trailingOptions.textSpeed || inlineOptions.textSpeed }
        : {}),
    };
  }

  function parseStageDirectionLine(line) {
    const text = trimImportedText(line, 320);
    if (!text) {
      return null;
    }

    const backgroundMatch = text.match(/^(?:scene|bg|background)\s+(.+)$/i);
    if (backgroundMatch) {
      const assetHint = stripWrappingQuotes(removeDirectiveClauses(backgroundMatch[1]));
      return assetHint
        ? {
            type: "background",
            assetHint,
            transition: parseDirectiveTransition(backgroundMatch[1], "fade"),
            transitionDurationMs: parseInlineTimeMs(backgroundMatch[1], "duration", 600),
          }
        : null;
    }

    const showMatch = text.match(/^show\s+(.+)$/i);
    if (showMatch) {
      const showText = showMatch[1];
      const leading = readLeadingArgument(showText);
      const expressionHint = stripWrappingQuotes(removeDirectiveClauses(leading.rest));
      const stage = parseInlineCharacterStage(showText);
      return leading.argument
        ? {
            type: "character_show",
            characterHint: leading.argument,
            expressionHint,
            position: parseDirectivePosition(showText, "center"),
            transition: parseDirectiveTransition(showText, "fade"),
            transitionDurationMs: parseInlineTimeMs(showText, "duration", 600),
            ...(stage ? { stage } : {}),
          }
        : null;
    }

    const moveMatch = text.match(/^(?:move|animate|移动角色|移动)\s+(.+)$/iu);
    if (moveMatch) {
      const moveText = moveMatch[1];
      const leading = readLeadingArgument(moveText);
      const expressionHint = stripWrappingQuotes(removeCharacterMotionClauses(leading.rest));
      const stage = parseInlineCharacterStage(moveText);
      return leading.argument
        ? {
            type: "character_move",
            characterHint: leading.argument,
            expressionHint,
            position: parseDirectivePosition(moveText, "center"),
            durationMs: parseInlineTimeMs(moveText, "duration", 600),
            easing: parseInlineCharacterMotionEasing(moveText),
            ...(stage ? { stage } : {}),
          }
        : null;
    }

    const hideMatch = text.match(/^hide\s+(.+)$/i);
    if (hideMatch) {
      const hideText = hideMatch[1];
      const leading = readLeadingArgument(hideText);
      return leading.argument
        ? {
            type: "character_hide",
            characterHint: leading.argument,
            transition: parseDirectiveTransition(hideText, "fade"),
            transitionDurationMs: parseInlineTimeMs(hideText, "duration", 600),
          }
        : null;
    }

    const playMusicMatch = text.match(/^(?:play\s+)?(?:music|bgm)\s+(.+)$/i);
    if (playMusicMatch) {
      const musicText = playMusicMatch[1];
      const leading = readLeadingArgument(musicText);
      return leading.argument
        ? {
            type: "music_play",
            assetHint: leading.argument,
            fadeInMs: parseInlineTimeMs(musicText, "fadein", 600),
            fadeOutMs: parseInlineTimeMs(musicText, "fadeout", 600),
          }
        : null;
    }

    const playSfxMatch = text.match(/^(?:play\s+)?(?:sound|sfx|se)\s+(.+)$/i);
    if (playSfxMatch) {
      const sfxText = playSfxMatch[1];
      const leading = readLeadingArgument(sfxText);
      return leading.argument
        ? {
            type: "sfx_play",
            assetHint: leading.argument,
            volume: 100,
          }
        : null;
    }

    const playVideoMatch = text.match(/^(?:play\s+)?(?:video|movie|op|ed|pv)\s+(.+)$/i);
    if (playVideoMatch) {
      const videoText = playVideoMatch[1];
      const leading = readLeadingArgument(videoText);
      const startTimeSeconds = parseInlineTimeSeconds(videoText, ["from", "start"], 0);
      const rawEndTimeSeconds = parseInlineTimeSeconds(videoText, ["to", "end"], 0);
      const endTimeSeconds = rawEndTimeSeconds > startTimeSeconds ? rawEndTimeSeconds : 0;
      return leading.argument
        ? {
            type: "video_play",
            assetHint: leading.argument,
            title: parseInlineTitle(leading.rest),
            fit: parseInlineVideoFit(videoText),
            volume: parseInlineVolumePercent(videoText, 100),
            startTimeSeconds,
            endTimeSeconds,
            skippable: parseInlineVideoSkippable(videoText, true),
          }
        : null;
    }

    const creditsMatch = text.match(/^(?:credits|staff|roll\s+credits)\b(.*)$/i);
    if (creditsMatch) {
      const creditsText = creditsMatch[1] ?? "";
      return {
        type: "credits_roll",
        title: parseInlineTitle(creditsText, "STAFF") || "STAFF",
        subtitle: parseInlineSubtitle(creditsText),
        lines: parseInlineCreditsLines(creditsText),
        durationSeconds: parseInlineTimeSeconds(creditsText, ["duration"], 18),
        background: parseInlineCreditsBackground(creditsText, "dark"),
        skippable: parseInlineVideoSkippable(creditsText, true),
      };
    }

    const shakeMatch = text.match(/^(?:screen\s+)?shake\b(.*)$/i);
    if (shakeMatch) {
      const shakeText = shakeMatch[1] ?? "";
      return {
        type: "screen_shake",
        intensity: parseInlineEnumToken(shakeText, ["light", "medium", "heavy"], "medium", {
          soft: "light",
          weak: "light",
          strong: "heavy",
        }),
        duration: parseInlineEffectDurationToken(shakeText, "short"),
      };
    }

    const flashMatch = text.match(/^(?:screen\s+)?flash\b(.*)$/i);
    if (flashMatch) {
      const flashText = flashMatch[1] ?? "";
      return {
        type: "screen_flash",
        color: parseInlineEnumToken(flashText, ["white", "warm", "red", "black"], "white"),
        intensity: parseInlineEnumToken(flashText, ["soft", "medium", "strong"], "medium", {
          light: "soft",
          heavy: "strong",
        }),
        duration: parseInlineEffectDurationToken(flashText, "short"),
      };
    }

    const zoomMatch = text.match(/^(?:camera\s+)?zoom\b(.*)$/i);
    if (zoomMatch) {
      const zoomText = zoomMatch[1] ?? "";
      return {
        type: "camera_zoom",
        action: parseInlineEnumToken(zoomText, ["zoom_in", "zoom_out", "reset"], "zoom_in", {
          in: "zoom_in",
          out: "zoom_out",
          normal: "reset",
        }),
        strength: parseInlineEnumToken(zoomText, ["light", "medium", "heavy"], "medium", {
          soft: "light",
          strong: "heavy",
        }),
        focus: parseInlineEnumToken(zoomText, ["left", "center", "right"], "center", {
          middle: "center",
        }),
      };
    }

    const panMatch = text.match(/^(?:camera\s+)?pan\b(.*)$/i);
    if (panMatch) {
      const panText = panMatch[1] ?? "";
      return {
        type: "camera_pan",
        target: parseInlineEnumToken(panText, ["left", "center", "right"], "center", {
          middle: "center",
          reset: "center",
        }),
        strength: parseInlineEnumToken(panText, ["light", "medium", "heavy"], "medium", {
          soft: "light",
          strong: "heavy",
        }),
      };
    }

    const clearFilterMatch =
      text.match(/^(?:clear|remove|stop)\s+(?:screen\s+)?filter\b(.*)$/i) ??
      text.match(/^(?:screen\s+)?filter\s+(?:clear|off|stop)\b(.*)$/i);
    if (clearFilterMatch) {
      return {
        type: "screen_filter",
        action: "clear",
        preset: "memory",
        strength: "medium",
      };
    }

    const filterMatch = text.match(/^(?:screen\s+)?filter\b(.*)$/i);
    if (filterMatch) {
      const filterText = filterMatch[1] ?? "";
      return {
        type: "screen_filter",
        action: "apply",
        preset: parseInlineScreenFilterPreset(filterText, "memory"),
        strength: parseInlineScreenFilterStrength(filterText, "medium"),
      };
    }

    const clearDepthBlurMatch =
      text.match(/^(?:clear|remove|stop)\s+(?:depth\s+)?blur\b(.*)$/i) ??
      text.match(/^(?:depth\s+)?blur\s+(?:clear|off|stop)\b(.*)$/i);
    if (clearDepthBlurMatch) {
      return {
        type: "depth_blur",
        action: "clear",
        focus: "center",
        strength: "medium",
      };
    }

    const depthBlurMatch = text.match(/^(?:depth\s+)?blur\b(.*)$/i);
    if (depthBlurMatch) {
      const blurText = depthBlurMatch[1] ?? "";
      return {
        type: "depth_blur",
        action: "apply",
        focus: parseInlineDepthBlurFocus(blurText, "center"),
        strength: parseInlineScreenFilterStrength(blurText, "medium"),
      };
    }

    const stopParticleMatch =
      text.match(/^(?:particle|particles|fx)\s+(?:stop|off|clear)\b(.*)$/i) ??
      text.match(/^(?:stop|clear|remove)\s+(?:particle|particles|fx)\b(.*)$/i);
    if (stopParticleMatch) {
      return {
        type: "particle_effect",
        action: "stop",
        preset: "snow",
        intensity: "medium",
        speed: "medium",
      };
    }

    const particleMatch = text.match(/^(?:particle|particles|fx)\b(.*)$/i);
    if (particleMatch) {
      const particleText = particleMatch[1] ?? "";
      return {
        type: "particle_effect",
        action: "start",
        preset: parseInlineParticlePreset(particleText, "snow"),
        intensity: parseInlineParticleIntensity(particleText, "medium"),
        speed: parseInlineParticleSpeed(particleText, "medium"),
      };
    }

    const stopMusicMatch = text.match(/^stop\s+(?:music|bgm)\b(.*)$/i) ?? text.match(/^(?:music|bgm)\s+stop\b(.*)$/i);
    if (stopMusicMatch) {
      return {
        type: "music_stop",
        fadeOutMs: parseInlineTimeMs(stopMusicMatch[1], "fadeout", 600),
      };
    }

    const fadeMatch = text.match(/^(?:with\s+)?fade(?:\s+(in|out))?(?:\s+([0-9.]+\s*(?:ms|s)?))?$/i);
    if (fadeMatch) {
      return {
        type: "screen_fade",
        action: normalizeDirectiveToken(fadeMatch[1]) === "in" ? "fade_in" : "fade_out",
        durationMs: parseTimeMs(fadeMatch[2], 600),
      };
    }

    return null;
  }

  function parseWaitLine(line) {
    const text = trimImportedText(line, 120);
    const match = text.match(/^(?:wait|pause|等待|停顿)(?:\s+(.+?))?$/iu);
    if (!match) {
      return null;
    }

    return {
      type: "wait",
      durationSeconds: parseWaitDurationSeconds(match[1] ?? "1", 1),
    };
  }

  function parseVoiceLine(line) {
    const match = String(line ?? "").trim().match(/^voice\s+(.+)$/i);
    const voiceHint = stripWrappingQuotes(trimImportedText(match?.[1] ?? "", 160));
    return voiceHint ? { voiceHint } : null;
  }

  function parseJumpLine(line) {
    const match = String(line ?? "").trim().match(/^(?:jump|goto)\s+(.+)$/i);
    const targetHint = trimImportedText(match?.[1] ?? "", 120);
    return targetHint ? { type: "jump", targetHint } : null;
  }

  function flushChoiceOptions(blocks, choiceOptions) {
    if (!choiceOptions.length) {
      return;
    }

    blocks.push({
      type: "choice",
      options: choiceOptions.slice(0, SCRIPT_IMPORT_MAX_OPTIONS).map((option) => {
        const targetHint = trimImportedText(option?.targetHint ?? "", 120);
        const normalizedOption = {
          text: trimImportedText(option?.text ?? option, 160),
        };
        if (targetHint) {
          normalizedOption.targetHint = targetHint;
        }
        if (Array.isArray(option?.effects) && option.effects.length) {
          normalizedOption.effects = option.effects.map((effect) => ({ ...effect }));
        }
        return normalizedOption;
      }),
    });
    choiceOptions.length = 0;
  }

  function parseScriptDraftToBlocks(text, options = {}) {
    const maxLines = Math.max(1, Number.parseInt(options.maxLines ?? SCRIPT_IMPORT_MAX_LINES, 10) || SCRIPT_IMPORT_MAX_LINES);
    const maxBlocks = Math.max(1, Number.parseInt(options.maxBlocks ?? SCRIPT_IMPORT_MAX_BLOCKS, 10) || SCRIPT_IMPORT_MAX_BLOCKS);
    const lines = normalizeScriptImportText(text).slice(0, maxLines);
    const blocks = [];
    const choiceOptions = [];
    let pendingVoiceHint = "";
    let pendingTextSpeed = "";

    function attachPendingLineOptions(block) {
      if (pendingVoiceHint && (block?.type === "dialogue" || block?.type === "narration")) {
        block.voiceHint = pendingVoiceHint;
        pendingVoiceHint = "";
      }
      if (pendingTextSpeed && (block?.type === "dialogue" || block?.type === "narration") && !block.textSpeed) {
        block.textSpeed = pendingTextSpeed;
        pendingTextSpeed = "";
      }
      return block;
    }

    lines.forEach((line) => {
      if (blocks.length >= maxBlocks) {
        return;
      }

      if (isIgnoredScriptLine(line)) {
        return;
      }

      const voiceLine = parseVoiceLine(line);
      if (voiceLine) {
        pendingVoiceHint = voiceLine.voiceHint;
        return;
      }

      const textSpeedLine = parseTextSpeedLine(line);
      if (textSpeedLine) {
        pendingTextSpeed = textSpeedLine.textSpeed;
        return;
      }

      const choiceOption = parseChoiceOptionLine(line);
      if (choiceOption?.text) {
        choiceOptions.push(choiceOption);
        if (choiceOptions.length >= SCRIPT_IMPORT_MAX_OPTIONS) {
          flushChoiceOptions(blocks, choiceOptions);
        }
        return;
      }

      const jump = parseJumpLine(line);
      if (jump) {
        if (choiceOptions.length) {
          const latestOption = choiceOptions[choiceOptions.length - 1];
          latestOption.targetHint = latestOption.targetHint || jump.targetHint;
          return;
        }

        flushChoiceOptions(blocks, choiceOptions);
        blocks.push(jump);
        return;
      }

      flushChoiceOptions(blocks, choiceOptions);

      const condition = parseConditionLine(line);
      if (condition) {
        blocks.push(condition);
        return;
      }

      const variableAction = parseVariableActionLine(line);
      if (variableAction) {
        blocks.push(variableAction);
        return;
      }

      const wait = parseWaitLine(line);
      if (wait) {
        blocks.push(wait);
        return;
      }

      const stageDirection = parseStageDirectionLine(line);
      if (stageDirection) {
        blocks.push(stageDirection);
        return;
      }

      const dialogue = parseDialogueLine(line);
      if (dialogue) {
        blocks.push(attachPendingLineOptions(dialogue));
        return;
      }

      const quotedDialogue = parseQuotedDialogueLine(line);
      if (quotedDialogue) {
        blocks.push(attachPendingLineOptions(quotedDialogue));
        return;
      }

      const narration = trimImportedText(line);
      if (narration) {
        const inlineOptions = extractInlineTextSpeed(narration);
        blocks.push(attachPendingLineOptions({
          type: "narration",
          text: inlineOptions.text,
          ...(inlineOptions.textSpeed ? { textSpeed: inlineOptions.textSpeed } : {}),
        }));
      }
    });

    flushChoiceOptions(blocks, choiceOptions);
    return blocks.slice(0, maxBlocks);
  }

  function summarizeScriptDraftBlocks(blocks = []) {
    const counts = (Array.isArray(blocks) ? blocks : []).reduce(
      (summary, block) => {
        if (block?.type === "dialogue") {
          summary.dialogue += 1;
        } else if (block?.type === "choice") {
          summary.choice += 1;
        } else if (block?.type === "narration") {
          summary.narration += 1;
        } else if (STAGE_DRAFT_TYPES.includes(block?.type)) {
          summary.stage += 1;
        } else if (ROUTE_DRAFT_TYPES.includes(block?.type)) {
          summary.route += 1;
        } else if (VARIABLE_DRAFT_TYPES.includes(block?.type)) {
          summary.logic += 1;
        }
        return summary;
      },
      { dialogue: 0, narration: 0, choice: 0, stage: 0, route: 0, logic: 0 }
    );

    return {
      ...counts,
      total: counts.dialogue + counts.narration + counts.choice + counts.stage + counts.route + counts.logic,
    };
  }

  function buildStagePreviewLine(block) {
    if (block?.type === "background") {
      return `切背景：${block.assetHint || "待选择背景"}`;
    }
    if (block?.type === "character_show") {
      return `显示角色：${[block.characterHint, block.expressionHint, block.position ? `@${block.position}` : ""]
        .filter(Boolean)
        .join(" ")}`;
    }
    if (block?.type === "character_move") {
      return `角色动作：${[
        block.characterHint,
        block.expressionHint,
        block.position ? `→${block.position}` : "",
        `${block.durationMs ?? 600}ms`,
        block.easing,
      ]
        .filter(Boolean)
        .join(" ")}`;
    }
    if (block?.type === "character_hide") {
      return `隐藏角色：${block.characterHint || "当前角色"}`;
    }
    if (block?.type === "music_play") {
      return `播放 BGM：${block.assetHint || "待选择音乐"}`;
    }
    if (block?.type === "sfx_play") {
      return `播放音效：${block.assetHint || "待选择音效"}`;
    }
    if (block?.type === "video_play") {
      return `播放视频：${block.title || block.assetHint || "待选择视频"}`;
    }
    if (block?.type === "credits_roll") {
      return `片尾字幕：${block.title || "STAFF"}`;
    }
    if (block?.type === "wait") {
      return `等待：${parseWaitDurationSeconds(block.durationSeconds, 1)}s`;
    }
    if (block?.type === "screen_shake") {
      return `震屏：${block.intensity || "medium"} / ${block.duration || "short"}`;
    }
    if (block?.type === "screen_flash") {
      return `闪屏：${block.color || "white"} / ${block.intensity || "medium"}`;
    }
    if (block?.type === "camera_zoom") {
      return `镜头缩放：${block.action || "zoom_in"} / ${block.focus || "center"}`;
    }
    if (block?.type === "camera_pan") {
      return `镜头平移：${block.target || "center"} / ${block.strength || "medium"}`;
    }
    if (block?.type === "screen_filter") {
      return block.action === "clear"
        ? "关闭滤镜"
        : `滤镜：${block.preset || "memory"} / ${block.strength || "medium"}`;
    }
    if (block?.type === "depth_blur") {
      return block.action === "clear"
        ? "关闭景深"
        : `景深：${block.focus || "center"} / ${block.strength || "medium"}`;
    }
    if (block?.type === "particle_effect") {
      return block.action === "stop"
        ? "停止粒子"
        : `粒子：${block.preset || "snow"} / ${block.intensity || "medium"} / ${block.speed || "medium"}`;
    }
    if (block?.type === "music_stop") {
      return "停止 BGM";
    }
    if (block?.type === "screen_fade") {
      return block.action === "fade_in" ? "画面淡入" : "画面淡出";
    }
    return "演出卡片";
  }

  function buildRoutePreviewLine(block) {
    if (block?.type === "jump") {
      return `跳转：${block.targetHint || "待选择场景"}`;
    }
    if (block?.type === "condition") {
      const firstBranch = block.branches?.[0] ?? {};
      const whenText = (firstBranch.when ?? [])
        .map((rule) => `${rule.variableHint || rule.variableId} ${rule.operator || "=="} ${String(rule.value ?? "")}`)
        .join(" 且 ");
      const elseText = block.elseTargetHint ? ` / 否则：${block.elseTargetHint}` : "";
      return `条件：${whenText || "变量条件"} -> ${firstBranch.targetHint || "待选择场景"}${elseText}`;
    }
    return "路线卡片";
  }

  function buildVariablePreviewLine(block) {
    const variableHint = trimImportedText(block?.variableHint ?? block?.variableId ?? "", 64) || "变量";
    if (block?.type === "variable_add") {
      const value = Number(block.value);
      const amount = Number.isFinite(value) ? value : 0;
      return `变量变化：${variableHint} ${amount >= 0 ? "+" : ""}${amount}`;
    }
    return `变量赋值：${variableHint} = ${String(block?.value ?? "")}`;
  }

  function buildChoiceEffectPreview(effect) {
    const variableHint = trimImportedText(effect?.variableHint ?? effect?.variableId ?? "", 64);
    if (!variableHint) {
      return "";
    }
    if (effect?.type === "variable_add") {
      const value = Number(effect.value);
      const amount = Number.isFinite(value) ? value : 0;
      return `${variableHint} ${amount >= 0 ? "+" : ""}${amount}`;
    }
    return `${variableHint}=${String(effect?.value ?? "")}`;
  }

  function buildScriptDraftPreviewLines(blocks = [], limit = 6) {
    return (Array.isArray(blocks) ? blocks : [])
      .slice(0, Math.max(0, Number.parseInt(limit, 10) || 0))
      .map((block, index) => {
        if (block?.type === "dialogue") {
          const voiceSuffix = block.voiceHint ? `（voice: ${block.voiceHint}）` : "";
          const speedSuffix = block.textSpeed ? `（speed: ${block.textSpeed}）` : "";
          return `${index + 1}. ${block.speakerName || "角色"}：${block.text || ""}${voiceSuffix}${speedSuffix}`;
        }
        if (block?.type === "choice") {
          return `${index + 1}. 选项：${(block.options ?? [])
            .map((option) => {
              const routePart = option.targetHint ? `${option.text} -> ${option.targetHint}` : option.text;
              const effectText = (option.effects ?? []).map(buildChoiceEffectPreview).filter(Boolean).join("; ");
              return effectText ? `${routePart} [${effectText}]` : routePart;
            })
            .join(" / ")}`;
        }
        if (STAGE_DRAFT_TYPES.includes(block?.type)) {
          return `${index + 1}. 演出：${buildStagePreviewLine(block)}`;
        }
        if (ROUTE_DRAFT_TYPES.includes(block?.type)) {
          return `${index + 1}. 路线：${buildRoutePreviewLine(block)}`;
        }
        if (VARIABLE_DRAFT_TYPES.includes(block?.type)) {
          return `${index + 1}. 逻辑：${buildVariablePreviewLine(block)}`;
        }
        const voiceSuffix = block?.voiceHint ? `（voice: ${block.voiceHint}）` : "";
        const speedSuffix = block?.textSpeed ? `（speed: ${block.textSpeed}）` : "";
        return `${index + 1}. 旁白：${block?.text || ""}${voiceSuffix}${speedSuffix}`;
      });
  }

  global.CanvasiaEditorScriptImporter = Object.freeze({
    SCRIPT_IMPORT_MAX_LINES,
    SCRIPT_IMPORT_MAX_BLOCKS,
    SCRIPT_IMPORT_MAX_OPTIONS,
    STAGE_DRAFT_TYPES,
    ROUTE_DRAFT_TYPES,
    VARIABLE_DRAFT_TYPES,
    normalizeScriptImportText,
    parseChoiceLine,
    parseChoiceEffectClause,
    parseChoiceOptionLine,
    parseVariableActionLine,
    parseDialogueLine,
    parseQuotedDialogueLine,
    parseStageDirectionLine,
    parseWaitLine,
    parseVoiceLine,
    parseTextSpeedLine,
    parseConditionRuleClause,
    parseConditionLine,
    parseJumpLine,
    parseScriptDraftToBlocks,
    summarizeScriptDraftBlocks,
    buildScriptDraftPreviewLines,
  });
})(typeof window !== "undefined" ? window : globalThis);
