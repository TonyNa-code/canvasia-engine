(function attachScriptImporterTools(global) {
  const SCRIPT_IMPORT_MAX_LINES = 120;
  const SCRIPT_IMPORT_MAX_BLOCKS = 80;
  const SCRIPT_IMPORT_MAX_OPTIONS = 6;
  const STAGE_DRAFT_TYPES = Object.freeze([
    "background",
    "character_show",
    "character_hide",
    "music_play",
    "music_stop",
    "sfx_play",
    "screen_fade",
  ]);
  const ROUTE_DRAFT_TYPES = Object.freeze(["jump"]);
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

  function stripWrappingQuotes(value) {
    const text = trimImportedText(value, 800);
    const match = text.match(/^["“”'‘’](.+?)["“”'‘’]$/u);
    return trimImportedText(match ? match[1] : text, 800);
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

  function parseInlineTimeMs(text, keyword, fallbackMs = 600) {
    const match = String(text ?? "").match(new RegExp(`\\b${keyword}\\s+([0-9.]+\\s*(?:ms|s)?)`, "i"));
    return match ? parseTimeMs(match[1], fallbackMs) : fallbackMs;
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
    return trimImportedText(
      String(text ?? "")
        .replace(/\bwith\s+[a-zA-Z_-]+(?:\s+duration\s+[0-9.]+\s*(?:ms|s)?)?/iu, "")
        .replace(/\bduration\s+[0-9.]+\s*(?:ms|s)?/iu, "")
        .replace(/\bat\s+(left|center|right|truecenter|middle)\b/iu, "")
        .replace(/\bfade(?:in|out)?\s+[0-9.]+\s*(?:ms|s)?/giu, ""),
      240
    );
  }

  function isIgnoredScriptLine(line) {
    return /^(?:#|\/\/|label\s+\S+\s*:|menu\s*:|return\b|call\s+\S+|pause\b)/i.test(String(line ?? "").trim());
  }

  function parseChoiceLine(line) {
    const quotedChoice = String(line ?? "").match(/^["“](.+?)["”]\s*:$/u);
    if (quotedChoice) {
      return trimImportedText(quotedChoice[1], 160);
    }

    const match = String(line ?? "").match(/^(?:[-*•]|[0-9]+[.)、])\s*(.+)$/u);
    return match ? trimImportedText(match[1], 160) : "";
  }

  function parseChoiceOptionLine(line) {
    const text = parseChoiceLine(line);
    if (!text) {
      return null;
    }

    const targetMatch = text.match(/^(.+?)\s*(?:->|=>)\s*(\S.+)$/u);
    return {
      text: trimImportedText(targetMatch?.[1] ?? text, 160),
      targetHint: trimImportedText(targetMatch?.[2] ?? "", 120),
    };
  }

  function parseDialogueLine(line) {
    const match = String(line ?? "").match(/^([^:：]{1,24})[:：]\s*(.+)$/u);
    if (!match) {
      return null;
    }

    const speakerName = trimImportedText(match[1], 80);
    const text = trimImportedText(match[2], 800);
    if (!speakerName || !text || ["旁白", "narration", "旁述"].includes(speakerName.toLowerCase())) {
      return text ? { type: "narration", text } : null;
    }

    return {
      type: "dialogue",
      speakerName,
      text,
    };
  }

  function parseQuotedDialogueLine(line) {
    const text = String(line ?? "").trim();
    const dialogue = text.match(/^([^"“”]{1,32})\s+["“](.+?)["”]\s*$/u);
    if (dialogue) {
      return {
        type: "dialogue",
        speakerName: trimImportedText(dialogue[1], 80),
        text: trimImportedText(dialogue[2], 800),
      };
    }

    const narration = text.match(/^["“](.+?)["”]\s*$/u);
    return narration ? { type: "narration", text: trimImportedText(narration[1], 800) } : null;
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
      return leading.argument
        ? {
            type: "character_show",
            characterHint: leading.argument,
            expressionHint,
            position: parseDirectivePosition(showText, "center"),
            transition: parseDirectiveTransition(showText, "fade"),
            transitionDurationMs: parseInlineTimeMs(showText, "duration", 600),
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

    function attachPendingVoice(block) {
      if (pendingVoiceHint && (block?.type === "dialogue" || block?.type === "narration")) {
        block.voiceHint = pendingVoiceHint;
        pendingVoiceHint = "";
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

      const stageDirection = parseStageDirectionLine(line);
      if (stageDirection) {
        blocks.push(stageDirection);
        return;
      }

      const dialogue = parseDialogueLine(line);
      if (dialogue) {
        blocks.push(attachPendingVoice(dialogue));
        return;
      }

      const quotedDialogue = parseQuotedDialogueLine(line);
      if (quotedDialogue) {
        blocks.push(attachPendingVoice(quotedDialogue));
        return;
      }

      const narration = trimImportedText(line);
      if (narration) {
        blocks.push(attachPendingVoice({
          type: "narration",
          text: narration,
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
        }
        return summary;
      },
      { dialogue: 0, narration: 0, choice: 0, stage: 0, route: 0 }
    );

    return {
      ...counts,
      total: counts.dialogue + counts.narration + counts.choice + counts.stage + counts.route,
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
    if (block?.type === "character_hide") {
      return `隐藏角色：${block.characterHint || "当前角色"}`;
    }
    if (block?.type === "music_play") {
      return `播放 BGM：${block.assetHint || "待选择音乐"}`;
    }
    if (block?.type === "sfx_play") {
      return `播放音效：${block.assetHint || "待选择音效"}`;
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
    return "路线卡片";
  }

  function buildScriptDraftPreviewLines(blocks = [], limit = 6) {
    return (Array.isArray(blocks) ? blocks : [])
      .slice(0, Math.max(0, Number.parseInt(limit, 10) || 0))
      .map((block, index) => {
        if (block?.type === "dialogue") {
          const voiceSuffix = block.voiceHint ? `（voice: ${block.voiceHint}）` : "";
          return `${index + 1}. ${block.speakerName || "角色"}：${block.text || ""}${voiceSuffix}`;
        }
        if (block?.type === "choice") {
          return `${index + 1}. 选项：${(block.options ?? [])
            .map((option) => (option.targetHint ? `${option.text} -> ${option.targetHint}` : option.text))
            .join(" / ")}`;
        }
        if (STAGE_DRAFT_TYPES.includes(block?.type)) {
          return `${index + 1}. 演出：${buildStagePreviewLine(block)}`;
        }
        if (ROUTE_DRAFT_TYPES.includes(block?.type)) {
          return `${index + 1}. 路线：${buildRoutePreviewLine(block)}`;
        }
        return `${index + 1}. 旁白：${block?.text || ""}${block?.voiceHint ? `（voice: ${block.voiceHint}）` : ""}`;
      });
  }

  global.CanvasiaEditorScriptImporter = Object.freeze({
    SCRIPT_IMPORT_MAX_LINES,
    SCRIPT_IMPORT_MAX_BLOCKS,
    SCRIPT_IMPORT_MAX_OPTIONS,
    STAGE_DRAFT_TYPES,
    ROUTE_DRAFT_TYPES,
    normalizeScriptImportText,
    parseChoiceLine,
    parseChoiceOptionLine,
    parseDialogueLine,
    parseQuotedDialogueLine,
    parseStageDirectionLine,
    parseVoiceLine,
    parseJumpLine,
    parseScriptDraftToBlocks,
    summarizeScriptDraftBlocks,
    buildScriptDraftPreviewLines,
  });
})(typeof window !== "undefined" ? window : globalThis);
