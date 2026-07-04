import { getSafeVolumePercent, getVolumeRatio } from "./runtime_settings.js";

const DEFAULT_BGM_VOLUME = 72;
const DEFAULT_SFX_VOLUME = 85;
const DEFAULT_VOICE_VOLUME = 92;
const MAX_AUDIO_FADE_MS = 30000;
const AUDIO_FADE_FRAME_KEY = "_tnEngineFadeFrame";

function clamp(value, min, max) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return min;
  }
  return Math.min(max, Math.max(min, numeric));
}

function getSafeNumber(value, fallback = 0) {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : fallback;
}

function getRuntimeAnimationApi(animationApi = globalThis) {
  return animationApi ?? globalThis;
}

export function getSafeAudioFadeMs(value, fallback = 0) {
  return Math.round(clamp(getSafeNumber(value, fallback), 0, MAX_AUDIO_FADE_MS));
}

export function getRuntimeMusicTargetVolume(playback = {}, snapshot = {}) {
  return (
    getVolumeRatio(playback?.bgmVolume, DEFAULT_BGM_VOLUME) *
    getVolumeRatio(snapshot?.visualState?.musicVolume ?? snapshot?.block?.volume, 100)
  );
}

export function getRuntimeSfxTargetVolume(playback = {}, volumePercent = 100) {
  return getVolumeRatio(playback?.sfxVolume, DEFAULT_SFX_VOLUME) * getVolumeRatio(volumePercent, 100);
}

export function getRuntimeVoiceTargetVolume(playback = {}, snapshot = {}) {
  return (
    getVolumeRatio(playback?.voiceVolume, DEFAULT_VOICE_VOLUME) *
    getVolumeRatio(snapshot?.block?.voiceVolume, 100)
  );
}

export function cancelAudioFade(audio, animationApi = globalThis) {
  const runtimeApi = getRuntimeAnimationApi(animationApi);
  const frameId = audio?.[AUDIO_FADE_FRAME_KEY];
  if (frameId == null || typeof runtimeApi.cancelAnimationFrame !== "function") {
    if (audio) {
      audio[AUDIO_FADE_FRAME_KEY] = null;
    }
    return;
  }
  runtimeApi.cancelAnimationFrame(frameId);
  audio[AUDIO_FADE_FRAME_KEY] = null;
}

export function disposeAudio(audio, animationApi = globalThis) {
  if (!audio) {
    return;
  }
  cancelAudioFade(audio, animationApi);
  if (typeof audio.pause === "function") {
    audio.pause();
  }
  audio.src = "";
}

export function fadeAudioVolume(
  audio,
  { from = audio?.volume ?? 0, to = 0, durationMs = 0, onComplete = null, animationApi = globalThis } = {}
) {
  if (!audio) {
    return;
  }

  const runtimeApi = getRuntimeAnimationApi(animationApi);
  const requestFrame =
    typeof runtimeApi.requestAnimationFrame === "function" ? runtimeApi.requestAnimationFrame.bind(runtimeApi) : null;
  const now =
    typeof runtimeApi.performance?.now === "function"
      ? () => runtimeApi.performance.now()
      : () => Date.now();

  cancelAudioFade(audio, runtimeApi);
  const safeFrom = clamp(getSafeNumber(from, audio.volume || 0), 0, 1);
  const safeTo = clamp(getSafeNumber(to, 0), 0, 1);
  const safeDuration = getSafeAudioFadeMs(durationMs);

  if (safeDuration <= 0 || !requestFrame) {
    audio.volume = safeTo;
    if (typeof onComplete === "function") {
      onComplete();
    }
    return;
  }

  const startedAt = now();
  const tick = (timestamp) => {
    const progress = clamp((timestamp - startedAt) / safeDuration, 0, 1);
    const eased = progress * progress * (3 - 2 * progress);
    audio.volume = safeFrom + (safeTo - safeFrom) * eased;
    if (progress >= 1) {
      audio[AUDIO_FADE_FRAME_KEY] = null;
      if (typeof onComplete === "function") {
        onComplete();
      }
      return;
    }
    audio[AUDIO_FADE_FRAME_KEY] = requestFrame(tick);
  };

  audio.volume = safeFrom;
  audio[AUDIO_FADE_FRAME_KEY] = requestFrame(tick);
}

export function stopTrackedAudios(audioSet, animationApi = globalThis) {
  if (!audioSet || typeof audioSet.forEach !== "function") {
    return;
  }
  audioSet.forEach((audio) => disposeAudio(audio, animationApi));
  if (typeof audioSet.clear === "function") {
    audioSet.clear();
  }
}

export function getSafeCueVolumePercent(value, fallback = 100) {
  return getSafeVolumePercent(value, fallback);
}
