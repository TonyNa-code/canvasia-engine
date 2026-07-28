const MUSIC_TRANSPORT_MAX_SECONDS = 6 * 60 * 60;
const MUSIC_TRANSPORT_EPSILON_SECONDS = 0.035;
const MUSIC_RESTART_MODES = Object.freeze(["continue", "restart"]);

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function normalizeSeconds(value, fallback = 0) {
  const parsed = Number(value);
  const safeValue = Number.isFinite(parsed) ? parsed : Number(fallback) || 0;
  return Number(clamp(safeValue, 0, MUSIC_TRANSPORT_MAX_SECONDS).toFixed(3));
}

export function sanitizeMusicTransport(source = {}) {
  const loop = source?.loop !== false;
  const startTimeSeconds = normalizeSeconds(source?.startTimeSeconds);
  const hasExplicitLoopStart = source?.loopStartSeconds !== undefined
    && source?.loopStartSeconds !== null
    && source?.loopStartSeconds !== "";
  const loopStartSeconds = normalizeSeconds(
    hasExplicitLoopStart ? source.loopStartSeconds : startTimeSeconds,
    startTimeSeconds
  );
  const rawLoopEndSeconds = normalizeSeconds(source?.loopEndSeconds);
  const loopEndSeconds = rawLoopEndSeconds > loopStartSeconds ? rawLoopEndSeconds : 0;
  const restartMode = MUSIC_RESTART_MODES.includes(source?.restartMode)
    ? source.restartMode
    : "continue";

  return Object.freeze({
    loop,
    startTimeSeconds,
    loopStartSeconds,
    loopEndSeconds,
    restartMode,
  });
}

export function isSimpleMusicLoop(source = {}) {
  const transport = sanitizeMusicTransport(source);
  return transport.loop
    && transport.startTimeSeconds === 0
    && transport.loopStartSeconds === 0
    && transport.loopEndSeconds === 0;
}

export function buildMusicPlaybackKey(assetId, source = {}, cueId = "") {
  const transport = sanitizeMusicTransport(source);
  const parts = [
    String(assetId ?? ""),
    transport.loop ? "loop" : "once",
    transport.startTimeSeconds,
    transport.loopStartSeconds,
    transport.loopEndSeconds,
  ];
  if (transport.restartMode === "restart") {
    parts.push(String(cueId ?? "cue"));
  }
  return parts.join(":");
}

export function getMusicInitialPosition(source = {}, resumeTimeSeconds = null) {
  const transport = sanitizeMusicTransport(source);
  if (resumeTimeSeconds === null || resumeTimeSeconds === undefined || resumeTimeSeconds === "") {
    return transport.startTimeSeconds;
  }
  const resume = normalizeSeconds(resumeTimeSeconds, transport.startTimeSeconds);
  if (transport.loop && transport.loopEndSeconds > 0 && resume >= transport.loopEndSeconds) {
    return transport.loopStartSeconds;
  }
  return resume;
}

export function getMusicTransportSummary(source = {}) {
  const transport = sanitizeMusicTransport(source);
  if (!transport.loop) {
    return transport.startTimeSeconds > 0
      ? `从 ${transport.startTimeSeconds} 秒开始，只播放一次`
      : "从头播放一次，结束后保持静音";
  }
  if (isSimpleMusicLoop(transport)) {
    return transport.restartMode === "restart" ? "整首循环，同曲音乐卡也会重新播放" : "整首循环，同曲音乐卡会自然续播";
  }
  const endLabel = transport.loopEndSeconds > 0 ? `${transport.loopEndSeconds} 秒` : "歌曲结尾";
  return `先从 ${transport.startTimeSeconds} 秒播放，再循环 ${transport.loopStartSeconds} 秒到${endLabel}`;
}

export function getMusicTransportDiagnostics(source = {}) {
  const inputLoopStart = normalizeSeconds(source?.loopStartSeconds, normalizeSeconds(source?.startTimeSeconds));
  const inputLoopEnd = normalizeSeconds(source?.loopEndSeconds);
  if (source?.loop !== false && inputLoopEnd > 0 && inputLoopEnd <= inputLoopStart) {
    return Object.freeze({
      level: "warning",
      code: "loop_end_not_after_start",
      label: "循环终点必须晚于循环起点，当前会按歌曲结尾处理。",
    });
  }
  return Object.freeze({ level: "good", code: "ready", label: "播放规则有效，可在试玩和导出成品中保持一致。" });
}

function seekAudio(audio, seconds) {
  if (!audio) {
    return;
  }
  const duration = Number(audio.duration);
  const upperBound = Number.isFinite(duration) && duration > 0
    ? Math.max(0, duration - MUSIC_TRANSPORT_EPSILON_SECONDS)
    : MUSIC_TRANSPORT_MAX_SECONDS;
  try {
    audio.currentTime = clamp(normalizeSeconds(seconds), 0, upperBound);
  } catch (_error) {
    // Browsers can reject an early seek before metadata is available; loadedmetadata retries it.
  }
}

function playAudio(audio) {
  try {
    const result = audio?.play?.();
    result?.catch?.(() => {});
  } catch (_error) {
    // Autoplay policy failures are handled by the runtime's next user gesture.
  }
}

export function bindMusicTransportToAudio(audio, source = {}, options = {}) {
  const transport = sanitizeMusicTransport(source);
  const initialPosition = getMusicInitialPosition(transport, options.initialPositionSeconds);
  let disposed = false;
  let initialSeekApplied = false;

  const applyInitialSeek = () => {
    if (disposed || initialSeekApplied) {
      return;
    }
    initialSeekApplied = true;
    seekAudio(audio, initialPosition);
  };
  const restartLoopSegment = () => {
    if (disposed || !transport.loop) {
      options.onStopped?.();
      return;
    }
    seekAudio(audio, transport.loopStartSeconds);
    playAudio(audio);
  };
  const handleTimeUpdate = () => {
    if (
      !disposed
      && transport.loop
      && transport.loopEndSeconds > 0
      && Number(audio?.currentTime) >= transport.loopEndSeconds - MUSIC_TRANSPORT_EPSILON_SECONDS
    ) {
      restartLoopSegment();
    }
  };
  const handleEnded = () => restartLoopSegment();

  audio.loop = isSimpleMusicLoop(transport);
  audio.addEventListener?.("loadedmetadata", applyInitialSeek);
  audio.addEventListener?.("timeupdate", handleTimeUpdate);
  audio.addEventListener?.("ended", handleEnded);
  if (Number(audio.readyState) >= 1 || initialPosition === 0) {
    applyInitialSeek();
  }

  return () => {
    disposed = true;
    audio.removeEventListener?.("loadedmetadata", applyInitialSeek);
    audio.removeEventListener?.("timeupdate", handleTimeUpdate);
    audio.removeEventListener?.("ended", handleEnded);
  };
}

export function getMusicPlaybackPosition(audio, fallback = 0) {
  return normalizeSeconds(audio?.currentTime, fallback);
}

export function keepExistingMusicPlaybackAlive(audio) {
  if (!audio || audio.ended === true) {
    return false;
  }
  if (audio.paused === true) {
    playAudio(audio);
  }
  return true;
}

const runtimeMusicTransportApi = Object.freeze({
  MUSIC_RESTART_MODES,
  sanitizeMusicTransport,
  isSimpleMusicLoop,
  buildMusicPlaybackKey,
  getMusicInitialPosition,
  getMusicTransportSummary,
  getMusicTransportDiagnostics,
  bindMusicTransportToAudio,
  getMusicPlaybackPosition,
  keepExistingMusicPlaybackAlive,
});

globalThis.CanvasiaRuntimeMusicTransport = runtimeMusicTransportApi;
