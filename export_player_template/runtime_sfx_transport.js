const SFX_FADE_MAX_MS = 60 * 1000;
const SFX_CHANNEL_IDS = Object.freeze(["effect", "ambience", "ui"]);
const SFX_STOP_CHANNEL_IDS = Object.freeze(["all", ...SFX_CHANNEL_IDS]);
const SFX_RESTART_MODES = Object.freeze(["continue", "restart"]);

function clamp(value, minimum, maximum) {
  return Math.min(maximum, Math.max(minimum, value));
}

function normalizeNumber(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : Number(fallback) || 0;
}

function normalizeVolume(value, fallback = 100) {
  if (value === null || value === undefined || value === "") {
    return clamp(Math.round(normalizeNumber(fallback, 100)), 0, 100);
  }
  return clamp(Math.round(normalizeNumber(value, fallback)), 0, 100);
}

function normalizeFadeMs(value, fallback = 0) {
  return clamp(Math.round(normalizeNumber(value, fallback)), 0, SFX_FADE_MAX_MS);
}

export function sanitizeSfxChannelId(value, { allowAll = false, fallback = "effect" } = {}) {
  const supported = allowAll ? SFX_STOP_CHANNEL_IDS : SFX_CHANNEL_IDS;
  const safeFallback = supported.includes(fallback) ? fallback : allowAll ? "all" : "effect";
  const candidate = String(value ?? "").trim().toLowerCase();
  return supported.includes(candidate) ? candidate : safeFallback;
}

export function sanitizeSfxTransport(source = {}) {
  const loop = source?.loop === true;
  const restartMode = loop && SFX_RESTART_MODES.includes(source?.restartMode)
    ? source.restartMode
    : loop
      ? "continue"
      : "restart";
  return Object.freeze({
    channelId: sanitizeSfxChannelId(source?.channelId),
    loop,
    restartMode,
    volume: normalizeVolume(source?.volume),
    fadeInMs: normalizeFadeMs(source?.fadeInMs),
    replaceFadeOutMs: normalizeFadeMs(source?.replaceFadeOutMs),
  });
}

export function sanitizeSfxStop(source = {}) {
  return Object.freeze({
    channelId: sanitizeSfxChannelId(source?.channelId, { allowAll: true, fallback: "all" }),
    fadeOutMs: normalizeFadeMs(source?.fadeOutMs, 600),
  });
}

export function buildSfxPlaybackKey(assetId, source = {}, cueId = "") {
  const transport = sanitizeSfxTransport(source);
  const parts = [String(assetId ?? ""), transport.channelId, transport.loop ? "loop" : "once"];
  if (transport.restartMode === "restart" || !transport.loop) {
    parts.push(String(cueId || "cue"));
  }
  return parts.join(":");
}

export function getSfxChannelLabel(channelId = "effect") {
  return {
    effect: "效果声道",
    ambience: "环境声道",
    ui: "界面声道",
    all: "全部音效声道",
  }[sanitizeSfxChannelId(channelId, { allowAll: true, fallback: "all" })];
}

export function getSfxTransportSummary(source = {}) {
  const transport = sanitizeSfxTransport(source);
  const channelLabel = getSfxChannelLabel(transport.channelId);
  if (!transport.loop) {
    return `${channelLabel}叠加播放一次 / 音量 ${transport.volume}%${
      transport.fadeInMs ? ` / ${transport.fadeInMs}ms 淡入` : ""
    }`;
  }
  const restartLabel = transport.restartMode === "continue" ? "同声道同素材自然续播" : "每次重新开始";
  return `${channelLabel}持续循环 / ${restartLabel} / 音量 ${transport.volume}%${
    transport.replaceFadeOutMs ? ` / 替换时 ${transport.replaceFadeOutMs}ms 淡出` : ""
  }`;
}

export function getSfxStopSummary(source = {}) {
  const stop = sanitizeSfxStop(source);
  return `停止${getSfxChannelLabel(stop.channelId)}${stop.fadeOutMs ? ` / ${stop.fadeOutMs}ms 淡出` : " / 立即停止"}`;
}

export function getSfxTransportDiagnostics(source = {}) {
  const transport = sanitizeSfxTransport(source);
  if (transport.loop && transport.channelId === "effect") {
    return Object.freeze({
      level: "warning",
      code: "loop_on_effect_channel",
      label: "循环音效建议放到环境声道，避免与门铃、脚步等短音效互相挤占。",
    });
  }
  if (!transport.loop && source?.restartMode === "continue") {
    return Object.freeze({
      level: "warning",
      code: "continue_requires_loop",
      label: "一次性音效不需要续播规则，当前会按每次重新播放处理。",
    });
  }
  return Object.freeze({
    level: "good",
    code: "ready",
    label: "声音轨道规则有效，可在试玩和导出成品中保持一致。",
  });
}

function sanitizePersistentChannelState(source = {}, fallbackChannelId = "effect") {
  const transport = sanitizeSfxTransport({ ...source, channelId: source?.channelId ?? fallbackChannelId, loop: true });
  const assetId = String(source?.assetId ?? "").trim();
  if (!assetId) {
    return null;
  }
  return Object.freeze({
    assetId,
    cueId: String(source?.cueId ?? ""),
    ...transport,
    loop: true,
  });
}

export function sanitizeSfxChannelStateMap(source = {}) {
  const result = {};
  if (!source || typeof source !== "object" || Array.isArray(source)) {
    return result;
  }
  SFX_CHANNEL_IDS.forEach((channelId) => {
    const state = sanitizePersistentChannelState(source[channelId], channelId);
    if (state) {
      result[channelId] = state;
    }
  });
  return result;
}

export function applySfxBlockToChannelState(source = {}, block = {}, options = {}) {
  const result = sanitizeSfxChannelStateMap(source);
  if (block?.type === "sfx_stop") {
    const stop = sanitizeSfxStop(block);
    if (stop.channelId === "all") {
      return {};
    }
    delete result[stop.channelId];
    return result;
  }
  if (block?.type !== "sfx_play") {
    return result;
  }
  const transport = sanitizeSfxTransport(block);
  if (!transport.loop || !String(block.assetId ?? "").trim()) {
    return result;
  }
  result[transport.channelId] = {
    assetId: String(block.assetId),
    cueId: String(options.cueId ?? block.id ?? ""),
    ...transport,
  };
  return result;
}

function defaultDisposeAudio(audio) {
  try {
    audio.pause?.();
    audio.removeAttribute?.("src");
    audio.src = "";
    audio.load?.();
  } catch (_error) {
    // Audio teardown is best-effort on browser and test doubles.
  }
}

function safePlay(audio) {
  try {
    const result = audio?.play?.();
    result?.catch?.(() => {});
  } catch (_error) {
    // Browser autoplay policy failures are retried by a later user gesture.
  }
}

function defaultFadeAudio(audio, detail = {}) {
  const durationMs = normalizeFadeMs(detail.durationMs);
  const from = clamp(normalizeNumber(detail.from, audio?.volume ?? 0), 0, 1);
  const to = clamp(normalizeNumber(detail.to, 0), 0, 1);
  const requestFrame = globalThis.requestAnimationFrame?.bind(globalThis);
  if (!audio || durationMs <= 0 || !requestFrame) {
    if (audio) {
      audio.volume = to;
    }
    detail.onComplete?.();
    return;
  }
  const startedAt = globalThis.performance?.now?.() ?? Date.now();
  audio.volume = from;
  const tick = (now) => {
    const progress = clamp((normalizeNumber(now, Date.now()) - startedAt) / durationMs, 0, 1);
    audio.volume = from + (to - from) * progress;
    if (progress < 1) {
      requestFrame(tick);
    } else {
      detail.onComplete?.();
    }
  };
  requestFrame(tick);
}

export function createSfxTransportController(options = {}) {
  const AudioClass = options.AudioClass ?? globalThis.Audio;
  const resolveAssetUrl = options.resolveAssetUrl ?? (() => "");
  const getMasterVolume = options.getMasterVolume ?? (() => 1);
  const disposeAudio = options.disposeAudio ?? defaultDisposeAudio;
  const fadeAudio = options.fadeAudio ?? defaultFadeAudio;
  const persistentChannels = new Map();
  const oneShots = new Set();
  let lastOneShotStepKey = "";

  const targetVolume = (transport) => clamp(
    normalizeNumber(getMasterVolume(), 1) * (sanitizeSfxTransport(transport).volume / 100),
    0,
    1
  );

  const stopEntry = (entry, fadeOutMs = 0) => {
    if (!entry?.audio) {
      return;
    }
    const finish = () => disposeAudio(entry.audio);
    if (normalizeFadeMs(fadeOutMs) > 0 && Number(entry.audio.volume) > 0) {
      fadeAudio(entry.audio, { from: entry.audio.volume, to: 0, durationMs: normalizeFadeMs(fadeOutMs), onComplete: finish });
    } else {
      finish();
    }
  };

  const createEntry = (state, { persistent = false } = {}) => {
    if (typeof AudioClass !== "function") {
      return null;
    }
    const url = resolveAssetUrl(state.assetId);
    if (!url) {
      return null;
    }
    const transport = sanitizeSfxTransport(state);
    const audio = new AudioClass(encodeURI(url));
    audio.loop = persistent && transport.loop;
    audio._canvasiaSfxVolumePercent = transport.volume;
    audio._canvasiaSfxChannelId = transport.channelId;
    const volume = targetVolume(transport);
    audio.volume = transport.fadeInMs > 0 ? 0 : volume;
    const entry = {
      assetId: String(state.assetId),
      cueId: String(state.cueId ?? ""),
      playbackKey: buildSfxPlaybackKey(state.assetId, transport, state.cueId),
      transport,
      audio,
    };
    if (transport.fadeInMs > 0) {
      fadeAudio(audio, { from: 0, to: volume, durationMs: transport.fadeInMs });
    }
    safePlay(audio);
    return entry;
  };

  const syncPersistentChannels = (source = {}) => {
    const desired = sanitizeSfxChannelStateMap(source);
    Array.from(persistentChannels.entries()).forEach(([channelId, entry]) => {
      if (!desired[channelId]) {
        stopEntry(entry, 0);
        persistentChannels.delete(channelId);
      }
    });
    Object.entries(desired).forEach(([channelId, state]) => {
      const current = persistentChannels.get(channelId);
      const playbackKey = buildSfxPlaybackKey(state.assetId, state, state.cueId);
      if (current?.playbackKey === playbackKey) {
        current.transport = sanitizeSfxTransport(state);
        current.audio.volume = targetVolume(current.transport);
        if (current.audio.paused && !current.audio.ended) {
          safePlay(current.audio);
        }
        return;
      }
      if (current) {
        stopEntry(current, state.replaceFadeOutMs);
      }
      const next = createEntry(state, { persistent: true });
      if (next) {
        persistentChannels.set(channelId, next);
      } else {
        persistentChannels.delete(channelId);
      }
    });
    return desired;
  };

  const triggerOneShot = (block = {}, stepKey = "") => {
    const safeStepKey = String(stepKey ?? "");
    if (!safeStepKey || safeStepKey === lastOneShotStepKey) {
      return false;
    }
    const transport = sanitizeSfxTransport(block);
    if (transport.loop || !String(block.assetId ?? "").trim()) {
      return false;
    }
    const entry = createEntry({ ...block, ...transport, cueId: safeStepKey });
    if (!entry) {
      return false;
    }
    lastOneShotStepKey = safeStepKey;
    oneShots.add(entry);
    const cleanup = () => {
      oneShots.delete(entry);
      disposeAudio(entry.audio);
    };
    entry.audio.addEventListener?.("ended", cleanup, { once: true });
    entry.audio.addEventListener?.("error", cleanup, { once: true });
    return true;
  };

  return Object.freeze({
    sync(snapshot, detail = {}) {
      if (snapshot?.blockType === "sfx_stop") {
        const stopConfig = sanitizeSfxStop(snapshot.block);
        this.stop(stopConfig.channelId, stopConfig.fadeOutMs);
      }
      const desired = syncPersistentChannels(snapshot?.visualState?.sfxChannels);
      if (snapshot?.blockType === "sfx_play") {
        triggerOneShot(snapshot.block, detail.stepKey);
      } else {
        lastOneShotStepKey = "";
      }
      return desired;
    },
    syncPersistentChannels,
    triggerOneShot,
    updateVolumes() {
      persistentChannels.forEach((entry) => {
        entry.audio.volume = targetVolume(entry.transport);
      });
      oneShots.forEach((entry) => {
        entry.audio.volume = targetVolume(entry.transport);
      });
    },
    stop(channelId = "all", fadeOutMs = 0) {
      const stop = sanitizeSfxStop({ channelId, fadeOutMs });
      Array.from(persistentChannels.entries()).forEach(([activeChannelId, entry]) => {
        if (stop.channelId === "all" || stop.channelId === activeChannelId) {
          stopEntry(entry, stop.fadeOutMs);
          persistentChannels.delete(activeChannelId);
        }
      });
      Array.from(oneShots).forEach((entry) => {
        if (stop.channelId === "all" || stop.channelId === entry.transport.channelId) {
          stopEntry(entry, stop.fadeOutMs);
          oneShots.delete(entry);
        }
      });
    },
    resetOneShotStepKey() {
      lastOneShotStepKey = "";
    },
    getDebugState() {
      return Object.freeze({
        persistentChannels: Object.fromEntries(
          Array.from(persistentChannels.entries()).map(([channelId, entry]) => [channelId, {
            assetId: entry.assetId,
            playbackKey: entry.playbackKey,
            volume: entry.audio.volume,
          }])
        ),
        oneShotCount: oneShots.size,
        lastOneShotStepKey,
      });
    },
  });
}

const runtimeSfxTransportApi = Object.freeze({
  SFX_CHANNEL_IDS,
  SFX_STOP_CHANNEL_IDS,
  SFX_RESTART_MODES,
  sanitizeSfxChannelId,
  sanitizeSfxTransport,
  sanitizeSfxStop,
  buildSfxPlaybackKey,
  getSfxChannelLabel,
  getSfxTransportSummary,
  getSfxStopSummary,
  getSfxTransportDiagnostics,
  sanitizeSfxChannelStateMap,
  applySfxBlockToChannelState,
  createSfxTransportController,
});

globalThis.CanvasiaRuntimeSfxTransport = runtimeSfxTransportApi;
