const VIDEO_TRANSPORT_MAX_SECONDS = 6 * 60 * 60;
const VIDEO_TRANSPORT_EPSILON_SECONDS = 0.035;
const VIDEO_RESUME_MODES = Object.freeze(["restart", "resume"]);
const VIDEO_FIT_MODES = Object.freeze(["contain", "cover", "fill"]);

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

export function normalizeVideoSeconds(value, fallback = 0) {
  const parsed = Number(value);
  const safeValue = Number.isFinite(parsed) ? parsed : Number(fallback) || 0;
  return Number(clamp(safeValue, 0, VIDEO_TRANSPORT_MAX_SECONDS).toFixed(3));
}

export function getSafeVideoFit(value) {
  return VIDEO_FIT_MODES.includes(value) ? value : "contain";
}

export function getSafeVideoVolume(value, fallback = 100) {
  const parsed = value === null || value === undefined || value === "" ? Number.NaN : Number(value);
  const parsedFallback = Number(fallback);
  const safeFallback = Number.isFinite(parsedFallback) ? parsedFallback : 100;
  const safeValue = Number.isFinite(parsed) ? parsed : safeFallback;
  return Math.round(clamp(safeValue, 0, 100));
}

export function sanitizeVideoTransport(source = {}) {
  const loop = source?.loop === true;
  const startTimeSeconds = normalizeVideoSeconds(source?.startTimeSeconds);
  const rawEndTimeSeconds = normalizeVideoSeconds(source?.endTimeSeconds);
  const endTimeSeconds = rawEndTimeSeconds > startTimeSeconds ? rawEndTimeSeconds : 0;
  const resumeMode = VIDEO_RESUME_MODES.includes(source?.resumeMode)
    ? source.resumeMode
    : "restart";

  return Object.freeze({
    autoplay: source?.autoplay !== false,
    loop,
    resumeMode,
    startTimeSeconds,
    endTimeSeconds,
    fit: getSafeVideoFit(source?.fit),
    volume: getSafeVideoVolume(source?.volume),
    // A permanently looping, non-skippable clip would trap the player.
    skippable: loop ? true : source?.skippable !== false,
  });
}

export function getVideoInitialPosition(source = {}, resumeTimeSeconds = null) {
  const transport = sanitizeVideoTransport(source);
  if (
    transport.resumeMode !== "resume" ||
    resumeTimeSeconds === null ||
    resumeTimeSeconds === undefined ||
    resumeTimeSeconds === ""
  ) {
    return transport.startTimeSeconds;
  }

  const resume = normalizeVideoSeconds(resumeTimeSeconds, transport.startTimeSeconds);
  if (resume < transport.startTimeSeconds) {
    return transport.startTimeSeconds;
  }
  if (transport.endTimeSeconds > 0 && resume >= transport.endTimeSeconds) {
    return transport.startTimeSeconds;
  }
  return resume;
}

export function getVideoPlaybackPosition(video, fallback = 0) {
  return normalizeVideoSeconds(video?.currentTime, fallback);
}

export function getVideoTransportSummary(source = {}) {
  const transport = sanitizeVideoTransport(source);
  const startLabel = transport.startTimeSeconds > 0
    ? `从 ${transport.startTimeSeconds} 秒开始`
    : "从头开始";
  const endLabel = transport.endTimeSeconds > 0
    ? `到 ${transport.endTimeSeconds} 秒`
    : "播放到自然结尾";
  const playLabel = transport.loop ? "循环播放，玩家可随时继续" : "播放一次后继续剧情";
  const startModeLabel = transport.autoplay ? "进入卡片时自动播放" : "等待玩家手动播放";
  const resumeLabel = transport.resumeMode === "resume" ? "读档后接着播放" : "读档后重新播放";
  return `${startModeLabel}；${startLabel}，${endLabel}；${playLabel}；${resumeLabel}`;
}

export function getVideoTransportDiagnostics(source = {}) {
  const start = normalizeVideoSeconds(source?.startTimeSeconds);
  const end = normalizeVideoSeconds(source?.endTimeSeconds);
  if (end > 0 && end <= start) {
    return Object.freeze({
      level: "warning",
      code: "end_not_after_start",
      label: "结束秒数必须晚于开始秒数，当前会播放到视频自然结尾。",
    });
  }
  if (source?.loop === true && source?.skippable === false) {
    return Object.freeze({
      level: "warning",
      code: "loop_requires_exit",
      label: "循环视频必须能退出，运行时已自动保留“结束循环”按钮。",
    });
  }
  return Object.freeze({
    level: "good",
    code: "ready",
    label: "播放规则有效，编辑器试玩、网页成品与原生 Runtime 会使用同一组参数。",
  });
}

function seekVideo(video, seconds) {
  if (!video) {
    return;
  }
  const duration = Number(video.duration);
  const upperBound = Number.isFinite(duration) && duration > 0
    ? Math.max(0, duration - VIDEO_TRANSPORT_EPSILON_SECONDS)
    : VIDEO_TRANSPORT_MAX_SECONDS;
  try {
    video.currentTime = clamp(normalizeVideoSeconds(seconds), 0, upperBound);
  } catch (_error) {
    // Metadata may not be ready yet; loadedmetadata retries the seek.
  }
}

function playVideo(video) {
  try {
    const result = video?.play?.();
    result?.catch?.(() => {});
  } catch (_error) {
    // Browser autoplay policies are surfaced by the caller's UI.
  }
}

export function bindVideoTransportToVideo(video, source = {}, options = {}) {
  const transport = sanitizeVideoTransport(source);
  const initialPosition = getVideoInitialPosition(transport, options.initialPositionSeconds);
  let disposed = false;
  let initialSeekApplied = false;
  let completionReported = false;

  const applyInitialSeek = () => {
    if (disposed || initialSeekApplied) {
      return;
    }
    initialSeekApplied = true;
    seekVideo(video, initialPosition);
  };
  const reportFinished = (reason) => {
    if (disposed || completionReported) {
      return;
    }
    completionReported = true;
    options.onFinished?.(reason);
  };
  const restartLoop = () => {
    if (disposed) {
      return;
    }
    if (!transport.loop) {
      reportFinished("ended");
      return;
    }
    seekVideo(video, transport.startTimeSeconds);
    playVideo(video);
    options.onLoop?.(transport.startTimeSeconds);
  };
  const handleTimeUpdate = () => {
    if (
      !disposed &&
      transport.endTimeSeconds > 0 &&
      Number(video?.currentTime) >= transport.endTimeSeconds - VIDEO_TRANSPORT_EPSILON_SECONDS
    ) {
      if (transport.loop) {
        restartLoop();
      } else {
        reportFinished("segment-end");
      }
    }
  };
  const handleEnded = () => restartLoop();
  const handleError = () => {
    if (!disposed) {
      options.onError?.();
    }
  };

  if (video) {
    video.loop = false;
    video.volume = transport.volume / 100;
    video.addEventListener?.("loadedmetadata", applyInitialSeek);
    video.addEventListener?.("timeupdate", handleTimeUpdate);
    video.addEventListener?.("ended", handleEnded);
    video.addEventListener?.("error", handleError);
    if (Number(video.readyState) >= 1 || initialPosition === 0) {
      applyInitialSeek();
    }
  }

  return () => {
    disposed = true;
    video?.removeEventListener?.("loadedmetadata", applyInitialSeek);
    video?.removeEventListener?.("timeupdate", handleTimeUpdate);
    video?.removeEventListener?.("ended", handleEnded);
    video?.removeEventListener?.("error", handleError);
  };
}

const runtimeVideoTransportApi = Object.freeze({
  VIDEO_RESUME_MODES,
  VIDEO_FIT_MODES,
  normalizeVideoSeconds,
  getSafeVideoFit,
  getSafeVideoVolume,
  sanitizeVideoTransport,
  getVideoInitialPosition,
  getVideoPlaybackPosition,
  getVideoTransportSummary,
  getVideoTransportDiagnostics,
  bindVideoTransportToVideo,
});

globalThis.CanvasiaRuntimeVideoTransport = runtimeVideoTransportApi;
