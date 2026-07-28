(function attachMusicTransportEditor(global) {
  "use strict";

  const MUSIC_TRANSPORT_PRESETS = Object.freeze({
    full_loop: Object.freeze({
      label: "整首循环",
      description: "常规 BGM，从头播放并循环；同曲卡片自然续播。",
      values: Object.freeze({ loop: true, startTimeSeconds: 0, loopStartSeconds: 0, loopEndSeconds: 0, restartMode: "continue" }),
    }),
    intro_loop: Object.freeze({
      label: "片头后循环",
      description: "先播放一次片头，再从指定位置循环，适合有前奏的主题曲。",
      values: Object.freeze({ loop: true, startTimeSeconds: 0, loopStartSeconds: 8, loopEndSeconds: 0, restartMode: "continue" }),
    }),
    play_once: Object.freeze({
      label: "只播一次",
      description: "播放到结尾后不重来，适合短过场和提示音乐。",
      values: Object.freeze({ loop: false, startTimeSeconds: 0, loopStartSeconds: 0, loopEndSeconds: 0, restartMode: "continue" }),
    }),
    restart_cue: Object.freeze({
      label: "同曲也重播",
      description: "每次走到这张音乐卡都从起播点重来。",
      values: Object.freeze({ loop: true, startTimeSeconds: 0, loopStartSeconds: 0, loopEndSeconds: 0, restartMode: "restart" }),
    }),
  });

  function getRuntimeTools(options = {}) {
    return options.runtimeTools ?? global.CanvasiaRuntimeMusicTransport;
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function renderMusicTransportEditor(block = {}, options = {}) {
    const runtimeTools = getRuntimeTools(options);
    const transport = runtimeTools.sanitizeMusicTransport(block);
    const diagnostics = runtimeTools.getMusicTransportDiagnostics(block);
    const presetButtons = Object.entries(MUSIC_TRANSPORT_PRESETS)
      .map(([id, preset]) => `
        <button type="button" class="toolbar-button" data-action="apply-music-transport-preset" data-music-transport-preset="${id}" title="${escapeHtml(preset.description)}">
          ${escapeHtml(preset.label)}
        </button>`)
      .join("");

    return `
      <section class="music-transport-editor" data-music-transport-editor>
        <div class="music-transport-heading">
          <div>
            <strong>精确播放</strong>
            <span>片头、循环段与同曲续播规则</span>
          </div>
          <span class="music-transport-status is-${diagnostics.level}" data-music-transport-status>${escapeHtml(diagnostics.label)}</span>
        </div>
        <div class="detail-actions music-transport-presets">${presetButtons}</div>
        <div class="field-grid compact-grid music-transport-fields">
          <div class="detail-row">
            <label for="editorMusicStartTime">第一次从这里开始（秒）</label>
            <input id="editorMusicStartTime" type="number" min="0" max="21600" step="0.1" value="${transport.startTimeSeconds}" />
          </div>
          <div class="detail-row">
            <label for="editorMusicLoopStart">循环回到这里（秒）</label>
            <input id="editorMusicLoopStart" type="number" min="0" max="21600" step="0.1" value="${transport.loopStartSeconds}" ${transport.loop ? "" : "disabled"} />
          </div>
          <div class="detail-row">
            <label for="editorMusicLoopEnd">循环到这里（秒）</label>
            <input id="editorMusicLoopEnd" type="number" min="0" max="21600" step="0.1" value="${transport.loopEndSeconds}" ${transport.loop ? "" : "disabled"} />
            <p class="helper-text">填 0 表示播放到歌曲自然结尾。</p>
          </div>
          <div class="detail-row">
            <label for="editorMusicRestartMode">再次遇到同一首歌</label>
            <select id="editorMusicRestartMode">
              <option value="continue" ${transport.restartMode === "continue" ? "selected" : ""}>保持当前位置继续</option>
              <option value="restart" ${transport.restartMode === "restart" ? "selected" : ""}>从起播点重新开始</option>
            </select>
          </div>
        </div>
        <div class="music-transport-summary" data-music-transport-summary>${escapeHtml(runtimeTools.getMusicTransportSummary(transport))}</div>
      </section>`;
  }

  function readMusicTransportEditor(block = {}, documentRef = global.document, options = {}) {
    const runtimeTools = getRuntimeTools(options);
    return runtimeTools.sanitizeMusicTransport({
      ...block,
      loop: documentRef?.getElementById("editorMusicLoop")?.value !== "false",
      startTimeSeconds: documentRef?.getElementById("editorMusicStartTime")?.value,
      loopStartSeconds: documentRef?.getElementById("editorMusicLoopStart")?.value,
      loopEndSeconds: documentRef?.getElementById("editorMusicLoopEnd")?.value,
      restartMode: documentRef?.getElementById("editorMusicRestartMode")?.value,
    });
  }

  function updateMusicTransportPreview(documentRef = global.document, options = {}) {
    const runtimeTools = getRuntimeTools(options);
    const source = readMusicTransportEditor({}, documentRef, options);
    const summary = documentRef?.querySelector?.("[data-music-transport-summary]");
    const status = documentRef?.querySelector?.("[data-music-transport-status]");
    const loopStart = documentRef?.getElementById?.("editorMusicLoopStart");
    const loopEnd = documentRef?.getElementById?.("editorMusicLoopEnd");
    const diagnostics = runtimeTools.getMusicTransportDiagnostics({
      ...source,
      loopStartSeconds: documentRef?.getElementById?.("editorMusicLoopStart")?.value,
      loopEndSeconds: documentRef?.getElementById?.("editorMusicLoopEnd")?.value,
    });
    if (summary) {
      summary.textContent = runtimeTools.getMusicTransportSummary(source);
    }
    if (status) {
      status.textContent = diagnostics.label;
      status.className = `music-transport-status is-${diagnostics.level}`;
    }
    if (loopStart) {
      loopStart.disabled = !source.loop;
    }
    if (loopEnd) {
      loopEnd.disabled = !source.loop;
    }
    return source;
  }

  function applyMusicTransportPreset(presetId, documentRef = global.document, options = {}) {
    const preset = MUSIC_TRANSPORT_PRESETS[presetId];
    if (!preset) {
      return Object.freeze({ ok: false, label: "没有找到这组音乐播放预设。" });
    }
    const values = preset.values;
    const setValue = (id, value) => {
      const control = documentRef?.getElementById?.(id);
      if (control) {
        control.value = String(value);
      }
    };
    setValue("editorMusicLoop", values.loop);
    setValue("editorMusicStartTime", values.startTimeSeconds);
    setValue("editorMusicLoopStart", values.loopStartSeconds);
    setValue("editorMusicLoopEnd", values.loopEndSeconds);
    setValue("editorMusicRestartMode", values.restartMode);
    updateMusicTransportPreview(documentRef, options);
    return Object.freeze({ ok: true, label: `已套用：${preset.label}` });
  }

  global.CanvasiaEditorMusicTransport = Object.freeze({
    MUSIC_TRANSPORT_PRESETS,
    renderMusicTransportEditor,
    readMusicTransportEditor,
    updateMusicTransportPreview,
    applyMusicTransportPreset,
  });
})(typeof window !== "undefined" ? window : globalThis);
