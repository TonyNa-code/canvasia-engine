export const NARRATOR_VOICE_PROFILE_ID = "__canvasia_narrator__";

const DEFAULT_PROFILE = Object.freeze({ volume: 100, muted: false });
const MAX_PROFILE_COUNT = 160;
const MAX_PROFILE_ID_LENGTH = 128;
const BLOCKED_PROFILE_IDS = new Set(["__proto__", "prototype", "constructor"]);

function getSafeVolumePercent(value, fallback = 100) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return fallback;
  }
  return Math.min(100, Math.max(0, Math.round(numeric)));
}

export function getSafeVoiceProfileId(value) {
  const profileId = typeof value === "string" ? value.trim() : "";
  if (
    !profileId ||
    profileId.length > MAX_PROFILE_ID_LENGTH ||
    BLOCKED_PROFILE_IDS.has(profileId) ||
    /[\u0000-\u001f\u007f]/.test(profileId)
  ) {
    return "";
  }
  return profileId;
}

export function sanitizeVoiceMixProfiles(source = {}, options = {}) {
  if (!source || typeof source !== "object" || Array.isArray(source)) {
    return {};
  }

  const allowedIds = options.allowedIds
    ? new Set(Array.from(options.allowedIds, (item) => getSafeVoiceProfileId(item)).filter(Boolean))
    : null;
  const result = {};

  for (const [rawProfileId, rawProfile] of Object.entries(source)) {
    if (Object.keys(result).length >= MAX_PROFILE_COUNT) {
      break;
    }
    const profileId = getSafeVoiceProfileId(rawProfileId);
    if (!profileId || (allowedIds && !allowedIds.has(profileId))) {
      continue;
    }
    const profile =
      typeof rawProfile === "number" || typeof rawProfile === "string"
        ? { volume: rawProfile }
        : rawProfile && typeof rawProfile === "object" && !Array.isArray(rawProfile)
          ? rawProfile
          : {};
    result[profileId] = {
      volume: getSafeVolumePercent(profile.volume, DEFAULT_PROFILE.volume),
      muted: profile.muted === true,
    };
  }

  return result;
}

export function getVoiceMixProfile(profiles = {}, profileId = "") {
  const safeProfileId = getSafeVoiceProfileId(profileId);
  if (!safeProfileId) {
    return { ...DEFAULT_PROFILE };
  }
  const profile = sanitizeVoiceMixProfiles({ [safeProfileId]: profiles?.[safeProfileId] })[safeProfileId];
  return profile ?? { ...DEFAULT_PROFILE };
}

export function getVoiceMixVolumeRatio(profiles = {}, profileId = "") {
  const profile = getVoiceMixProfile(profiles, profileId);
  return profile.muted ? 0 : profile.volume / 100;
}

export function updateVoiceMixProfile(profiles = {}, profileId = "", patch = {}) {
  const safeProfileId = getSafeVoiceProfileId(profileId);
  const nextProfiles = sanitizeVoiceMixProfiles(profiles);
  if (!safeProfileId) {
    return nextProfiles;
  }

  const current = getVoiceMixProfile(nextProfiles, safeProfileId);
  const nextProfile = {
    volume: getSafeVolumePercent(patch.volume, current.volume),
    muted: typeof patch.muted === "boolean" ? patch.muted : current.muted,
  };
  if (nextProfile.volume === DEFAULT_PROFILE.volume && !nextProfile.muted) {
    delete nextProfiles[safeProfileId];
  } else {
    nextProfiles[safeProfileId] = nextProfile;
  }
  return nextProfiles;
}

export function getVoiceProfileIdFromBlock(block = {}) {
  if (block?.type === "narration") {
    return NARRATOR_VOICE_PROFILE_ID;
  }
  if (block?.type === "dialogue") {
    return getSafeVoiceProfileId(block.speakerId);
  }
  return "";
}

export function getVoiceProfileIdFromSnapshot(snapshot = {}) {
  return getVoiceProfileIdFromBlock(snapshot?.block ?? {});
}

function getCharacterFromMap(charactersById, characterId) {
  if (charactersById && typeof charactersById.get === "function") {
    return charactersById.get(characterId);
  }
  return charactersById?.[characterId];
}

export function collectVoiceMixerEntries(options = {}) {
  const scenes = Array.isArray(options.scenes) ? options.scenes : [];
  const entriesById = new Map();

  scenes.forEach((scene) => {
    const sceneId = typeof scene?.id === "string" ? scene.id : "";
    (Array.isArray(scene?.blocks) ? scene.blocks : []).forEach((block) => {
      if (!block?.voiceAssetId || (block.type !== "dialogue" && block.type !== "narration")) {
        return;
      }
      const profileId = getVoiceProfileIdFromBlock(block);
      if (!profileId) {
        return;
      }
      const previous = entriesById.get(profileId) ?? {
        id: profileId,
        label:
          profileId === NARRATOR_VOICE_PROFILE_ID
            ? String(options.narratorLabel ?? "旁白")
            : String(
                options.getCharacterName?.(profileId, getCharacterFromMap(options.charactersById, profileId)) ??
                  getCharacterFromMap(options.charactersById, profileId)?.displayName ??
                  getCharacterFromMap(options.charactersById, profileId)?.name ??
                  profileId
              ),
        lineCount: 0,
        sceneIds: new Set(),
      };
      previous.lineCount += 1;
      if (sceneId) {
        previous.sceneIds.add(sceneId);
      }
      entriesById.set(profileId, previous);
    });
  });

  return Array.from(entriesById.values()).map((entry) => ({
    id: entry.id,
    label: entry.label,
    lineCount: entry.lineCount,
    sceneCount: entry.sceneIds.size,
  }));
}

export function getVoiceMixerSummary(entries = [], profiles = {}) {
  const safeEntries = Array.isArray(entries) ? entries : [];
  const customizedCount = safeEntries.filter((entry) => {
    const profile = getVoiceMixProfile(profiles, entry?.id);
    return profile.muted || profile.volume !== DEFAULT_PROFILE.volume;
  }).length;
  const mutedCount = safeEntries.filter((entry) => getVoiceMixProfile(profiles, entry?.id).muted).length;
  return {
    characterCount: safeEntries.length,
    customizedCount,
    mutedCount,
  };
}

export function renderVoiceMixerRows(entries = [], profiles = {}, options = {}) {
  const escapeHtml = typeof options.escapeHtml === "function" ? options.escapeHtml : (value) => String(value ?? "");
  if (!Array.isArray(entries) || entries.length === 0) {
    return '<div class="voice-mixer-empty">项目中还没有绑定语音的角色或旁白。</div>';
  }

  return entries
    .map((entry) => {
      const profile = getVoiceMixProfile(profiles, entry.id);
      const safeId = escapeHtml(entry.id);
      const stateLabel = profile.muted ? "已静音" : profile.volume === 100 ? "跟随总音量" : `角色音量 ${profile.volume}%`;
      return `
        <article class="voice-mixer-row ${profile.muted ? "is-muted" : ""}" data-voice-mixer-row="${safeId}">
          <div class="voice-mixer-copy">
            <strong>${escapeHtml(entry.label)}</strong>
            <span>${escapeHtml(`${entry.lineCount} 句语音 · ${entry.sceneCount} 个场景 · ${stateLabel}`)}</span>
          </div>
          <label class="voice-mixer-volume">
            <span class="sr-only">${escapeHtml(`${entry.label}音量`)}</span>
            <input
              type="range"
              min="0"
              max="100"
              step="1"
              value="${profile.volume}"
              data-voice-mixer-volume="${safeId}"
              ${profile.muted ? "disabled" : ""}
            />
            <strong data-voice-mixer-value="${safeId}">${profile.volume}%</strong>
          </label>
          <button class="pill-button is-secondary" type="button" data-voice-mixer-mute="${safeId}">
            ${profile.muted ? "恢复" : "静音"}
          </button>
        </article>
      `;
    })
    .join("");
}

export function createVoiceMixerController(options = {}) {
  const refs = options.refs ?? {};
  const getEntries = typeof options.getEntries === "function" ? options.getEntries : () => [];
  const getProfiles = typeof options.getProfiles === "function" ? options.getProfiles : () => ({});
  const setProfiles = typeof options.setProfiles === "function" ? options.setProfiles : () => {};
  const persist = typeof options.persist === "function" ? options.persist : () => {};
  const updateAudio = typeof options.updateAudio === "function" ? options.updateAudio : () => {};
  const escapeHtml = typeof options.escapeHtml === "function" ? options.escapeHtml : (value) => String(value ?? "");

  function renderSummary(entries = getEntries()) {
    if (!refs.summary) {
      return;
    }
    const summary = getVoiceMixerSummary(entries, getProfiles());
    refs.summary.textContent = summary.characterCount
      ? `${summary.characterCount} 个语音通道 · 已单独调整 ${summary.customizedCount} 个 · 已静音 ${summary.mutedCount} 个`
      : "项目中还没有绑定语音的角色或旁白。";
  }

  function render() {
    if (!refs.list) {
      return;
    }
    const entries = getEntries();
    const profiles = getProfiles();
    const summary = getVoiceMixerSummary(entries, profiles);
    refs.list.innerHTML = renderVoiceMixerRows(entries, profiles, { escapeHtml });
    if (refs.resetButton) {
      refs.resetButton.disabled = summary.customizedCount === 0;
    }
    renderSummary(entries);
  }

  function commitProfiles(nextProfiles, { rerender = true } = {}) {
    setProfiles(nextProfiles);
    persist();
    updateAudio();
    if (rerender) {
      render();
    }
  }

  function handleInput(event) {
    const input = event.target?.closest?.("[data-voice-mixer-volume]");
    if (!input) {
      return;
    }
    const profileId = input.dataset.voiceMixerVolume;
    const nextProfiles = updateVoiceMixProfile(getProfiles(), profileId, { volume: input.value });
    commitProfiles(nextProfiles, { rerender: false });

    const profile = getVoiceMixProfile(nextProfiles, profileId);
    const valueNode = Array.from(refs.list?.querySelectorAll("[data-voice-mixer-value]") ?? []).find(
      (node) => node.dataset.voiceMixerValue === profileId
    );
    if (valueNode) {
      valueNode.textContent = `${profile.volume}%`;
    }
    const summary = getVoiceMixerSummary(getEntries(), nextProfiles);
    if (refs.resetButton) {
      refs.resetButton.disabled = summary.customizedCount === 0;
    }
    renderSummary();
  }

  function handleClick(event) {
    const muteButton = event.target?.closest?.("[data-voice-mixer-mute]");
    if (!muteButton) {
      return;
    }
    const profileId = muteButton.dataset.voiceMixerMute;
    const current = getVoiceMixProfile(getProfiles(), profileId);
    commitProfiles(updateVoiceMixProfile(getProfiles(), profileId, { muted: !current.muted }));
  }

  function reset() {
    commitProfiles({});
  }

  function attach() {
    refs.list?.addEventListener("input", handleInput);
    refs.list?.addEventListener("click", handleClick);
    refs.resetButton?.addEventListener("click", reset);
  }

  return Object.freeze({ attach, render, reset });
}
