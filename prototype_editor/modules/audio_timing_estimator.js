(function attachAudioTimingEstimatorTools(global) {
  const AUDIO_TIMING_DEFAULTS = Object.freeze({
    textCharactersPerSecond: 8,
    minimumTextSeconds: 1.4,
    maximumTextSeconds: 24,
    choiceDecisionSeconds: 2.4,
    visualBlockSeconds: 0.45,
    audioControlSeconds: 0.35,
    defaultWaitSeconds: 1,
    defaultVideoSeconds: 6,
    defaultCreditsSeconds: 12,
  });

  const EFFECT_DURATION_SECONDS = Object.freeze({
    short: 0.36,
    medium: 0.72,
    long: 1.2,
  });

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function clampNumber(value, minimum, maximum, fallback = minimum) {
    const number = Number(value);
    if (!Number.isFinite(number)) {
      return fallback;
    }
    return Math.min(Math.max(number, minimum), maximum);
  }

  function getTimingOptions(options = {}) {
    return {
      textCharactersPerSecond: clampNumber(
        options.textCharactersPerSecond,
        3,
        40,
        AUDIO_TIMING_DEFAULTS.textCharactersPerSecond
      ),
      minimumTextSeconds: clampNumber(options.minimumTextSeconds, 0.5, 8, AUDIO_TIMING_DEFAULTS.minimumTextSeconds),
      maximumTextSeconds: clampNumber(options.maximumTextSeconds, 3, 90, AUDIO_TIMING_DEFAULTS.maximumTextSeconds),
      choiceDecisionSeconds: clampNumber(options.choiceDecisionSeconds, 0.5, 20, AUDIO_TIMING_DEFAULTS.choiceDecisionSeconds),
      visualBlockSeconds: clampNumber(options.visualBlockSeconds, 0, 5, AUDIO_TIMING_DEFAULTS.visualBlockSeconds),
      audioControlSeconds: clampNumber(options.audioControlSeconds, 0, 5, AUDIO_TIMING_DEFAULTS.audioControlSeconds),
      defaultWaitSeconds: clampNumber(options.defaultWaitSeconds, 0.1, 30, AUDIO_TIMING_DEFAULTS.defaultWaitSeconds),
      defaultVideoSeconds: clampNumber(options.defaultVideoSeconds, 1, 180, AUDIO_TIMING_DEFAULTS.defaultVideoSeconds),
      defaultCreditsSeconds: clampNumber(options.defaultCreditsSeconds, 4, 240, AUDIO_TIMING_DEFAULTS.defaultCreditsSeconds),
    };
  }

  function countReadableCharacters(value) {
    return Array.from(cleanText(value).replace(/\s+/g, "")).length;
  }

  function getChoiceText(block = {}) {
    return toArray(block.options)
      .map((option) => cleanText(option?.text ?? option?.label))
      .filter(Boolean)
      .join(" / ");
  }

  function getCreditsText(block = {}) {
    const lines = toArray(block.lines).length ? block.lines : toArray(block.credits);
    return lines
      .map((line) => cleanText(line?.name ?? line?.role ?? line?.text ?? line))
      .filter(Boolean)
      .join(" / ");
  }

  function getReadableBlockText(block = {}) {
    if (["dialogue", "narration"].includes(block.type)) {
      return cleanText(block.text);
    }
    if (block.type === "choice") {
      return getChoiceText(block);
    }
    if (block.type === "credits_roll") {
      return getCreditsText(block);
    }
    return cleanText(block.text ?? block.title ?? block.caption);
  }

  function getSafeWaitSeconds(block = {}, options = {}) {
    const timingOptions = getTimingOptions(options);
    return clampNumber(block.durationSeconds ?? block.seconds ?? block.waitSeconds, 0.1, 300, timingOptions.defaultWaitSeconds);
  }

  function getSafeVideoSeconds(block = {}, options = {}) {
    const timingOptions = getTimingOptions(options);
    const startTime = clampNumber(block.startTimeSeconds, 0, 24 * 60 * 60, 0);
    const endTime = clampNumber(block.endTimeSeconds, 0, 24 * 60 * 60, 0);
    if (endTime > startTime) {
      return clampNumber(endTime - startTime, 0.5, 600, timingOptions.defaultVideoSeconds);
    }
    return clampNumber(block.durationSeconds, 0.5, 600, timingOptions.defaultVideoSeconds);
  }

  function getEffectSeconds(block = {}) {
    return EFFECT_DURATION_SECONDS[block.duration] ?? EFFECT_DURATION_SECONDS.medium;
  }

  function estimateTextSeconds(characterCount, options = {}) {
    const timingOptions = getTimingOptions(options);
    if (characterCount <= 0) {
      return 0;
    }
    return clampNumber(
      characterCount / timingOptions.textCharactersPerSecond,
      timingOptions.minimumTextSeconds,
      timingOptions.maximumTextSeconds,
      timingOptions.minimumTextSeconds
    );
  }

  function roundSeconds(value) {
    return Math.round(clampNumber(value, 0, 999999, 0) * 10) / 10;
  }

  function formatEstimatedDuration(seconds) {
    const safeSeconds = Math.max(0, Math.round(Number(seconds) || 0));
    if (safeSeconds <= 0) {
      return "约 0 秒";
    }
    if (safeSeconds < 60) {
      return `约 ${safeSeconds} 秒`;
    }
    const minutes = Math.floor(safeSeconds / 60);
    const remainingSeconds = safeSeconds % 60;
    return remainingSeconds > 0 ? `约 ${minutes}分${remainingSeconds}秒` : `约 ${minutes} 分钟`;
  }

  function estimateBlockTiming(block = {}, options = {}) {
    const timingOptions = getTimingOptions(options);
    const type = cleanText(block.type, "unknown");
    const text = getReadableBlockText(block);
    const readableCharacterCount = countReadableCharacters(text);
    let estimatedSeconds = estimateTextSeconds(readableCharacterCount, timingOptions);
    let waitSeconds = 0;
    let textBlockCount = readableCharacterCount > 0 ? 1 : 0;
    let mediaBlockCount = 0;

    if (type === "choice") {
      estimatedSeconds += timingOptions.choiceDecisionSeconds;
    } else if (type === "wait") {
      waitSeconds = getSafeWaitSeconds(block, timingOptions);
      estimatedSeconds += waitSeconds;
    } else if (type === "video_play") {
      const videoSeconds = getSafeVideoSeconds(block, timingOptions);
      estimatedSeconds += videoSeconds;
      mediaBlockCount += 1;
    } else if (type === "credits_roll") {
      const creditsSeconds = clampNumber(block.durationSeconds, 4, 600, timingOptions.defaultCreditsSeconds);
      estimatedSeconds = Math.max(estimatedSeconds, creditsSeconds);
      mediaBlockCount += 1;
    } else if (["background", "character_show", "character_hide", "screen_shake", "screen_flash", "screen_fade"].includes(type)) {
      estimatedSeconds += type.startsWith("screen_") ? getEffectSeconds(block) : timingOptions.visualBlockSeconds;
    } else if (["music_play", "music_stop", "sfx_play"].includes(type)) {
      estimatedSeconds += timingOptions.audioControlSeconds;
    }

    if (!["dialogue", "narration", "choice", "credits_roll"].includes(type)) {
      textBlockCount = 0;
    }

    return {
      type,
      estimatedSeconds: roundSeconds(estimatedSeconds),
      readableCharacterCount,
      waitSeconds: roundSeconds(waitSeconds),
      textBlockCount,
      mediaBlockCount,
      textPreview: text.slice(0, 48),
    };
  }

  function getTimingTone(summary = {}) {
    const seconds = Number(summary.estimatedSeconds) || 0;
    if ((summary.textBlockCount ?? 0) <= 0 && (summary.mediaBlockCount ?? 0) <= 0) {
      return "silent";
    }
    if (seconds > 0 && seconds < 8) {
      return "short";
    }
    if (seconds >= 240) {
      return "long";
    }
    return "balanced";
  }

  function estimateBlockRangeTiming(blocks = [], startIndex = 0, endIndex = startIndex, options = {}) {
    const safeBlocks = toArray(blocks);
    if (!safeBlocks.length) {
      return {
        startIndex: 0,
        endIndex: -1,
        blockCount: 0,
        estimatedSeconds: 0,
        durationLabel: "约 0 秒",
        readableCharacterCount: 0,
        waitSeconds: 0,
        textBlockCount: 0,
        mediaBlockCount: 0,
        tone: "silent",
      };
    }

    const safeStart = Math.max(0, Math.min(safeBlocks.length - 1, Number(startIndex) || 0));
    const safeEnd = Math.max(safeStart, Math.min(safeBlocks.length - 1, Number(endIndex) || safeStart));
    const blockTimings = safeBlocks.slice(safeStart, safeEnd + 1).map((block) => estimateBlockTiming(block, options));
    const estimatedSeconds = roundSeconds(blockTimings.reduce((total, timing) => total + timing.estimatedSeconds, 0));
    const summary = {
      startIndex: safeStart,
      endIndex: safeEnd,
      blockCount: blockTimings.length,
      estimatedSeconds,
      durationLabel: formatEstimatedDuration(estimatedSeconds),
      readableCharacterCount: blockTimings.reduce((total, timing) => total + timing.readableCharacterCount, 0),
      waitSeconds: roundSeconds(blockTimings.reduce((total, timing) => total + timing.waitSeconds, 0)),
      textBlockCount: blockTimings.reduce((total, timing) => total + timing.textBlockCount, 0),
      mediaBlockCount: blockTimings.reduce((total, timing) => total + timing.mediaBlockCount, 0),
      blockTimings,
    };
    summary.tone = getTimingTone(summary);
    return summary;
  }

  function buildAudioSegmentTimingHint(summary = {}) {
    const durationLabel = summary.durationLabel || formatEstimatedDuration(summary.estimatedSeconds);
    const characterCount = summary.readableCharacterCount ?? 0;
    const textBlockCount = summary.textBlockCount ?? 0;
    const waitSeconds = summary.waitSeconds ?? 0;
    const waitLabel = waitSeconds > 0 ? `，含等待 ${formatEstimatedDuration(waitSeconds).replace(/^约 /, "")}` : "";
    if (summary.tone === "silent") {
      return `${durationLabel}，几乎没有正文，建议确认这不是误把 BGM 绑在空段落上。`;
    }
    if (summary.tone === "short") {
      return `${durationLabel}，${textBlockCount} 段正文、约 ${characterCount} 字${waitLabel}，这段偏短，适合短提示或转场。`;
    }
    if (summary.tone === "long") {
      return `${durationLabel}，${textBlockCount} 段正文、约 ${characterCount} 字${waitLabel}，段落较长，建议发布前重点听循环感。`;
    }
    return `${durationLabel}，${textBlockCount} 段正文、约 ${characterCount} 字${waitLabel}。`;
  }

  global.CanvasiaEditorAudioTimingEstimator = Object.freeze({
    AUDIO_TIMING_DEFAULTS,
    countReadableCharacters,
    getReadableBlockText,
    estimateTextSeconds,
    estimateBlockTiming,
    estimateBlockRangeTiming,
    formatEstimatedDuration,
    buildAudioSegmentTimingHint,
  });
})(typeof window !== "undefined" ? window : globalThis);
