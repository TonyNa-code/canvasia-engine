// Voice-driven character motion shared by the editor preview and Web Runtime.
// Static sprites receive restrained body motion while model adapters can consume mouthOpen.

export const VOICE_REACTIVE_MOTION_MODE_LABELS = Object.freeze({
  off: "关闭语音演技",
  soft: "自然语音起伏",
  cinematic: "鲜明舞台演技",
});

export const DEFAULT_VOICE_REACTIVE_MOTION_CONFIG = Object.freeze({
  voiceReactiveMotionMode: "soft",
  voiceReactiveMotionIntensity: 58,
  voiceReactiveMotionSensitivity: 62,
});

export const VOICE_REACTIVE_MOTION_PROFILES = Object.freeze({
  off: Object.freeze({ scaleBoost: 0, liftPercent: 0 }),
  soft: Object.freeze({ scaleBoost: 0.006, liftPercent: 0.24 }),
  cinematic: Object.freeze({ scaleBoost: 0.014, liftPercent: 0.55 }),
});

const ACTIVE_CLASS = "is-voice-reactive";
const STYLE_PROPERTIES = Object.freeze([
  "--voice-reactive-level",
  "--voice-reactive-mouth",
  "--voice-reactive-scale",
  "--voice-reactive-lift",
]);

function clamp(value, minimum, maximum) {
  return Math.min(Math.max(value, minimum), maximum);
}

function getSafeNumber(value, fallback) {
  const numeric = Number.parseFloat(value ?? "");
  return Number.isFinite(numeric) ? numeric : fallback;
}

function roundPoseValue(value) {
  return Math.round(Number(value) * 1000) / 1000;
}

function getConfigSource(value) {
  if (value?.gameUiConfig && typeof value.gameUiConfig === "object") {
    return value.gameUiConfig;
  }
  return value && typeof value === "object" ? value : {};
}

function getVisualComfortMotionScale(value) {
  if (value === "static") return 0;
  if (value === "gentle") return 0.35;
  return 1;
}

export function getSafeVoiceReactiveMotionMode(value) {
  const mode = String(value ?? DEFAULT_VOICE_REACTIVE_MOTION_CONFIG.voiceReactiveMotionMode)
    .trim()
    .toLowerCase();
  return Object.hasOwn(VOICE_REACTIVE_MOTION_PROFILES, mode)
    ? mode
    : DEFAULT_VOICE_REACTIVE_MOTION_CONFIG.voiceReactiveMotionMode;
}

export function getVoiceReactiveMotionConfig(value = {}) {
  const source = getConfigSource(value);
  return Object.freeze({
    voiceReactiveMotionMode: getSafeVoiceReactiveMotionMode(source.voiceReactiveMotionMode),
    voiceReactiveMotionIntensity: Math.round(
      clamp(
        getSafeNumber(
          source.voiceReactiveMotionIntensity,
          DEFAULT_VOICE_REACTIVE_MOTION_CONFIG.voiceReactiveMotionIntensity
        ),
        0,
        100
      )
    ),
    voiceReactiveMotionSensitivity: Math.round(
      clamp(
        getSafeNumber(
          source.voiceReactiveMotionSensitivity,
          DEFAULT_VOICE_REACTIVE_MOTION_CONFIG.voiceReactiveMotionSensitivity
        ),
        0,
        100
      )
    ),
  });
}

export function normalizeVoiceReactiveLevel(rawLevel, sensitivity = 62, previousLevel = 0) {
  const safeRawLevel = clamp(getSafeNumber(rawLevel, 0), 0, 1);
  const safeSensitivity = clamp(getSafeNumber(sensitivity, 62), 0, 100) / 100;
  const threshold = 0.07 - safeSensitivity * 0.052;
  const gain = 3.2 + safeSensitivity * 4.4;
  const target = clamp((safeRawLevel - threshold) * gain, 0, 1);
  const previous = clamp(getSafeNumber(previousLevel, 0), 0, 1);
  const smoothing = target >= previous ? 0.58 : 0.2;
  return roundPoseValue(previous + (target - previous) * smoothing);
}

export function buildVoiceReactiveMotionPose({
  characterId,
  activeCharacterId,
  voiceActive = false,
  voiceLevel = 0,
  gameUiConfig = {},
  visualComfortMode = "standard",
  isLeaving = false,
} = {}) {
  const config = getVoiceReactiveMotionConfig(gameUiConfig);
  const safeCharacterId = String(characterId ?? "").trim();
  const safeActiveCharacterId = String(activeCharacterId ?? "").trim();
  const motionScale = getVisualComfortMotionScale(visualComfortMode);
  const active = Boolean(
    config.voiceReactiveMotionMode !== "off" &&
      voiceActive &&
      !isLeaving &&
      safeCharacterId &&
      safeCharacterId === safeActiveCharacterId &&
      motionScale > 0
  );
  const level = active ? clamp(getSafeNumber(voiceLevel, 0), 0, 1) : 0;
  const intensity = config.voiceReactiveMotionIntensity / 100;
  const activity = level * intensity * motionScale;
  const profile = VOICE_REACTIVE_MOTION_PROFILES[config.voiceReactiveMotionMode];

  return Object.freeze({
    mode: config.voiceReactiveMotionMode,
    active,
    level: roundPoseValue(level),
    mouthOpen: roundPoseValue(activity),
    scaleMultiplier: roundPoseValue(1 + profile.scaleBoost * activity),
    offsetYPercent: roundPoseValue(-profile.liftPercent * activity),
  });
}

export function buildVoiceReactiveMotionPresentation(options = {}) {
  const pose = buildVoiceReactiveMotionPose(options);
  return Object.freeze({
    ...pose,
    classNames: Object.freeze(pose.active ? [ACTIVE_CLASS] : []),
    style: [
      `--voice-reactive-level:${pose.level.toFixed(3)}`,
      `--voice-reactive-mouth:${pose.mouthOpen.toFixed(3)}`,
      `--voice-reactive-scale:${pose.scaleMultiplier.toFixed(3)}`,
      `--voice-reactive-lift:${pose.offsetYPercent.toFixed(3)}%`,
    ].join(";"),
  });
}

function getRmsLevel(analyser, data) {
  if (!analyser || !data) return null;
  analyser.getByteTimeDomainData(data);
  let sum = 0;
  for (let index = 0; index < data.length; index += 1) {
    const sample = (data[index] - 128) / 128;
    sum += sample * sample;
  }
  return clamp(Math.sqrt(sum / Math.max(data.length, 1)), 0, 1);
}

function getFallbackVoiceLevel(audio, nowMs) {
  if (!audio || audio.paused || audio.ended) return 0;
  const time = Number.isFinite(audio.currentTime) ? audio.currentTime : nowMs / 1000;
  const pulse = Math.abs(Math.sin(time * 11.7)) * 0.55 + Math.abs(Math.sin(time * 4.3 + 0.8)) * 0.45;
  return 0.035 + pulse * 0.095;
}

function resetMotionNode(node) {
  if (!node) return;
  node.classList?.remove?.(ACTIVE_CLASS);
  STYLE_PROPERTIES.forEach((property) => node.style?.removeProperty?.(property));
  if (node.dataset) {
    delete node.dataset.voiceReactiveLevel;
    delete node.dataset.mouthOpen;
  }
}

export function createVoiceReactiveMotionController(options = {}) {
  const scope = options.scope ?? globalThis;
  const animationApi = options.animationApi ?? scope;
  const resolveRoot = typeof options.resolveRoot === "function"
    ? options.resolveRoot
    : () => options.root ?? scope.document ?? null;
  const audioGraphs = new WeakMap();
  let audioContext = null;
  let activeAudio = null;
  let activeCharacterId = "";
  let gameUiConfig = {};
  let visualComfortMode = "standard";
  let currentLevel = 0;
  let frameHandle = null;
  let boundAudio = null;

  function cancelFrame() {
    if (frameHandle == null) return;
    if (typeof animationApi.cancelAnimationFrame === "function") {
      animationApi.cancelAnimationFrame(frameHandle);
    } else if (typeof animationApi.clearTimeout === "function") {
      animationApi.clearTimeout(frameHandle);
    }
    frameHandle = null;
  }

  function scheduleFrame(callback) {
    if (typeof animationApi.requestAnimationFrame === "function") {
      frameHandle = animationApi.requestAnimationFrame(callback);
      return;
    }
    if (typeof animationApi.setTimeout === "function") {
      frameHandle = animationApi.setTimeout(() => callback(Date.now()), 33);
    }
  }

  function connectAudioGraph(graph) {
    if (!graph || graph.connected) return graph;
    try {
      graph.sourceNode.connect(graph.analyser);
      graph.analyser.connect(audioContext.destination);
      graph.connected = true;
      return graph;
    } catch (_error) {
      try {
        graph.sourceNode.disconnect();
        graph.analyser.disconnect();
      } catch (_disconnectError) {
        // A partially connected graph is still safe to abandon.
      }
      return null;
    }
  }

  function disconnectAudioGraph(audio) {
    const graph = audio ? audioGraphs.get(audio) : null;
    if (!graph?.connected) return;
    try {
      graph.sourceNode.disconnect();
    } catch (_error) {
      // Already disconnected by the browser.
    }
    try {
      graph.analyser.disconnect();
    } catch (_error) {
      // Already disconnected by the browser.
    }
    graph.connected = false;
  }

  function getAudioGraph(audio) {
    if (!audio) return null;
    const cached = audioGraphs.get(audio);
    if (cached) return connectAudioGraph(cached);
    try {
      if (!audioContext) {
        const AudioContextConstructor = options.AudioContext ?? scope.AudioContext ?? scope.webkitAudioContext;
        audioContext = typeof options.audioContextFactory === "function"
          ? options.audioContextFactory()
          : AudioContextConstructor
            ? new AudioContextConstructor()
            : null;
      }
      if (!audioContext?.createMediaElementSource || !audioContext?.createAnalyser) return null;
      const sourceNode = audioContext.createMediaElementSource(audio);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.42;
      const graph = {
        sourceNode,
        analyser,
        data: new Uint8Array(analyser.fftSize),
        connected: false,
      };
      audioGraphs.set(audio, graph);
      return connectAudioGraph(graph);
    } catch (_error) {
      return null;
    }
  }

  function resetAllNodes() {
    const root = resolveRoot();
    root?.querySelectorAll?.(`.sprite-card.${ACTIVE_CLASS}`)?.forEach?.(resetMotionNode);
  }

  function applyCurrentPose() {
    const root = resolveRoot();
    if (!root?.querySelectorAll) return;
    const config = getVoiceReactiveMotionConfig(gameUiConfig);
    root.querySelectorAll(".sprite-card[data-character-id]").forEach((node) => {
      const characterId = String(node.dataset?.characterId ?? "");
      const presentation = buildVoiceReactiveMotionPresentation({
        characterId,
        activeCharacterId,
        voiceActive: Boolean(activeAudio && !activeAudio.paused && !activeAudio.ended),
        voiceLevel: currentLevel,
        gameUiConfig: config,
        visualComfortMode,
        isLeaving: node.classList?.contains?.("is-leaving"),
      });
      if (!presentation.active) {
        resetMotionNode(node);
        return;
      }
      node.classList.add(...presentation.classNames);
      presentation.style.split(";").filter(Boolean).forEach((declaration) => {
        const separator = declaration.indexOf(":");
        node.style.setProperty(declaration.slice(0, separator), declaration.slice(separator + 1));
      });
      node.dataset.voiceReactiveLevel = presentation.level.toFixed(3);
      node.dataset.mouthOpen = presentation.mouthOpen.toFixed(3);
    });
  }

  function finishAudio(audio) {
    if (!audio || audio !== activeAudio) return;
    cancelFrame();
    if (boundAudio === audio) unbindAudioEvents();
    disconnectAudioGraph(audio);
    activeAudio = null;
    activeCharacterId = "";
    currentLevel = 0;
    resetAllNodes();
  }

  function handleAudioPlaying() {
    if (!activeAudio) return;
    getAudioGraph(activeAudio);
    cancelFrame();
    scheduleFrame(tick);
  }

  function handleAudioPause() {
    if (!activeAudio || activeAudio.ended) return;
    cancelFrame();
    currentLevel = 0;
    resetAllNodes();
  }

  function handleAudioEnded() {
    finishAudio(boundAudio);
  }

  function unbindAudioEvents() {
    if (!boundAudio?.removeEventListener) {
      boundAudio = null;
      return;
    }
    boundAudio.removeEventListener("play", handleAudioPlaying);
    boundAudio.removeEventListener("playing", handleAudioPlaying);
    boundAudio.removeEventListener("pause", handleAudioPause);
    boundAudio.removeEventListener("ended", handleAudioEnded);
    boundAudio = null;
  }

  function bindAudioEvents(audio) {
    if (audio === boundAudio) return;
    unbindAudioEvents();
    boundAudio = audio ?? null;
    if (!boundAudio?.addEventListener) return;
    boundAudio.addEventListener("play", handleAudioPlaying);
    boundAudio.addEventListener("playing", handleAudioPlaying);
    boundAudio.addEventListener("pause", handleAudioPause);
    boundAudio.addEventListener("ended", handleAudioEnded);
  }

  function tick(timestamp) {
    frameHandle = null;
    if (!activeAudio) {
      resetAllNodes();
      return;
    }
    if (activeAudio.ended) {
      finishAudio(activeAudio);
      return;
    }
    if (activeAudio.paused) {
      currentLevel = 0;
      resetAllNodes();
      return;
    }
    const config = getVoiceReactiveMotionConfig(gameUiConfig);
    const graph = getAudioGraph(activeAudio);
    const rawLevel = getRmsLevel(graph?.analyser, graph?.data) ?? getFallbackVoiceLevel(activeAudio, timestamp);
    currentLevel = normalizeVoiceReactiveLevel(
      rawLevel,
      config.voiceReactiveMotionSensitivity,
      currentLevel
    );
    applyCurrentPose();
    scheduleFrame(tick);
  }

  function start({ audio, characterId, gameUiConfig: nextConfig = {}, visualComfortMode: nextComfort = "standard" } = {}) {
    const config = getVoiceReactiveMotionConfig(nextConfig);
    const nextCharacterId = String(characterId ?? "").trim();
    if (audio !== activeAudio) {
      disconnectAudioGraph(activeAudio);
      currentLevel = 0;
    }
    activeAudio = audio ?? null;
    activeCharacterId = nextCharacterId;
    gameUiConfig = config;
    visualComfortMode = nextComfort;
    cancelFrame();
    if (!activeAudio || !activeCharacterId || config.voiceReactiveMotionMode === "off" || nextComfort === "static") {
      unbindAudioEvents();
      disconnectAudioGraph(activeAudio);
      activeAudio = null;
      activeCharacterId = "";
      resetAllNodes();
      return false;
    }
    bindAudioEvents(activeAudio);
    getAudioGraph(activeAudio);
    audioContext?.resume?.().catch?.(() => {});
    scheduleFrame(tick);
    return true;
  }

  function stop() {
    cancelFrame();
    unbindAudioEvents();
    disconnectAudioGraph(activeAudio);
    activeAudio = null;
    activeCharacterId = "";
    currentLevel = 0;
    resetAllNodes();
  }

  return Object.freeze({ start, stop, applyCurrentPose });
}

const runtimeVoiceReactiveMotionApi = Object.freeze({
  VOICE_REACTIVE_MOTION_MODE_LABELS,
  DEFAULT_VOICE_REACTIVE_MOTION_CONFIG,
  VOICE_REACTIVE_MOTION_PROFILES,
  getSafeVoiceReactiveMotionMode,
  getVoiceReactiveMotionConfig,
  normalizeVoiceReactiveLevel,
  buildVoiceReactiveMotionPose,
  buildVoiceReactiveMotionPresentation,
  createVoiceReactiveMotionController,
});

globalThis.CanvasiaRuntimeVoiceReactiveMotion = runtimeVoiceReactiveMotionApi;
