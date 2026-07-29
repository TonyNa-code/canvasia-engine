(function attachSfxTransportEditor(global) {
  "use strict";

  const SFX_TRANSPORT_PRESETS = Object.freeze({
    impact: Object.freeze({
      label: "短促效果",
      description: "门铃、脚步、碰撞等一次性声音，可与其他声音自然叠加。",
      values: Object.freeze({ channelId: "effect", loop: false, restartMode: "restart", volume: 100, fadeInMs: 0, replaceFadeOutMs: 0 }),
    }),
    ambience: Object.freeze({
      label: "环境循环",
      description: "雨声、风声、人群声等持续氛围，同素材再次出现时自然续播。",
      values: Object.freeze({ channelId: "ambience", loop: true, restartMode: "continue", volume: 65, fadeInMs: 1200, replaceFadeOutMs: 800 }),
    }),
    ui: Object.freeze({
      label: "界面提示",
      description: "确认、提示、解锁等 UI 声音，使用独立逻辑声道。",
      values: Object.freeze({ channelId: "ui", loop: false, restartMode: "restart", volume: 75, fadeInMs: 0, replaceFadeOutMs: 0 }),
    }),
    heartbeat: Object.freeze({
      label: "持续心跳",
      description: "按剧情卡重新触发的循环演出，适合紧张段落和节奏变化。",
      values: Object.freeze({ channelId: "ambience", loop: true, restartMode: "restart", volume: 80, fadeInMs: 250, replaceFadeOutMs: 400 }),
    }),
  });

  function getRuntimeTools(options = {}) {
    return options.runtimeTools ?? global.CanvasiaRuntimeSfxTransport;
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function renderSfxTransportEditor(block = {}, options = {}) {
    const runtimeTools = getRuntimeTools(options);
    const transport = runtimeTools.sanitizeSfxTransport(block);
    const diagnostics = runtimeTools.getSfxTransportDiagnostics(block);
    const presetButtons = Object.entries(SFX_TRANSPORT_PRESETS)
      .map(([id, preset]) => `
        <button type="button" class="toolbar-button" data-action="apply-sfx-transport-preset" data-sfx-transport-preset="${id}" title="${escapeHtml(preset.description)}">
          ${escapeHtml(preset.label)}
        </button>`)
      .join("");

    return `
      <section class="sfx-transport-editor" data-sfx-transport-editor>
        <div class="sfx-transport-heading">
          <div>
            <strong>音效与环境声导演</strong>
            <span>叠加短音效，或让环境声跨卡片持续播放</span>
          </div>
          <span class="sfx-transport-status is-${diagnostics.level}" data-sfx-transport-status>${escapeHtml(diagnostics.label)}</span>
        </div>
        <div class="detail-actions sfx-transport-presets">${presetButtons}</div>
        <div class="field-grid compact-grid sfx-transport-fields">
          <div class="detail-row">
            <label for="editorSfxChannelId">声音用途</label>
            <select id="editorSfxChannelId">
              <option value="effect" ${transport.channelId === "effect" ? "selected" : ""}>效果声道（脚步、碰撞）</option>
              <option value="ambience" ${transport.channelId === "ambience" ? "selected" : ""}>环境声道（雨声、风声）</option>
              <option value="ui" ${transport.channelId === "ui" ? "selected" : ""}>界面声道（确认、提示）</option>
            </select>
          </div>
          <div class="detail-row">
            <label for="editorSfxLoop">播放方式</label>
            <select id="editorSfxLoop">
              <option value="false" ${!transport.loop ? "selected" : ""}>播放一次，可与其他声音叠加</option>
              <option value="true" ${transport.loop ? "selected" : ""}>持续循环，直到停止或被替换</option>
            </select>
          </div>
          <div class="detail-row">
            <label for="editorSfxRestartMode">再次遇到同一循环音时</label>
            <select id="editorSfxRestartMode" ${transport.loop ? "" : "disabled"}>
              <option value="continue" ${transport.restartMode === "continue" ? "selected" : ""}>保持当前进度，自然续播</option>
              <option value="restart" ${transport.restartMode === "restart" ? "selected" : ""}>从头重新播放</option>
            </select>
          </div>
          <div class="detail-row">
            <label for="editorSfxVolume">这张卡片的音量</label>
            <input id="editorSfxVolume" type="number" min="0" max="100" step="1" value="${transport.volume}" />
            <p class="helper-text">会和玩家设置里的总音量、音效音量叠加。</p>
          </div>
          <div class="detail-row">
            <label for="editorSfxFadeInMs">淡入时间（毫秒）</label>
            <input id="editorSfxFadeInMs" type="number" min="0" max="60000" step="100" value="${transport.fadeInMs}" />
          </div>
          <div class="detail-row">
            <label for="editorSfxReplaceFadeOutMs">替换旧循环时淡出（毫秒）</label>
            <input id="editorSfxReplaceFadeOutMs" type="number" min="0" max="60000" step="100" value="${transport.replaceFadeOutMs}" ${transport.loop ? "" : "disabled"} />
          </div>
        </div>
        <div class="sfx-transport-summary" data-sfx-transport-summary>${escapeHtml(runtimeTools.getSfxTransportSummary(transport))}</div>
      </section>`;
  }

  function readSfxTransportEditor(block = {}, documentRef = global.document, options = {}) {
    return getRuntimeTools(options).sanitizeSfxTransport({
      ...block,
      channelId: documentRef?.getElementById("editorSfxChannelId")?.value,
      loop: documentRef?.getElementById("editorSfxLoop")?.value === "true",
      restartMode: documentRef?.getElementById("editorSfxRestartMode")?.value,
      volume: documentRef?.getElementById("editorSfxVolume")?.value,
      fadeInMs: documentRef?.getElementById("editorSfxFadeInMs")?.value,
      replaceFadeOutMs: documentRef?.getElementById("editorSfxReplaceFadeOutMs")?.value,
    });
  }

  function updateSfxTransportPreview(documentRef = global.document, options = {}) {
    const runtimeTools = getRuntimeTools(options);
    const rawSource = {
      channelId: documentRef?.getElementById?.("editorSfxChannelId")?.value,
      loop: documentRef?.getElementById?.("editorSfxLoop")?.value === "true",
      restartMode: documentRef?.getElementById?.("editorSfxRestartMode")?.value,
      volume: documentRef?.getElementById?.("editorSfxVolume")?.value,
      fadeInMs: documentRef?.getElementById?.("editorSfxFadeInMs")?.value,
      replaceFadeOutMs: documentRef?.getElementById?.("editorSfxReplaceFadeOutMs")?.value,
    };
    const transport = runtimeTools.sanitizeSfxTransport(rawSource);
    const diagnostics = runtimeTools.getSfxTransportDiagnostics(rawSource);
    const summary = documentRef?.querySelector?.("[data-sfx-transport-summary]");
    const status = documentRef?.querySelector?.("[data-sfx-transport-status]");
    const restartMode = documentRef?.getElementById?.("editorSfxRestartMode");
    const replaceFade = documentRef?.getElementById?.("editorSfxReplaceFadeOutMs");
    if (summary) {
      summary.textContent = runtimeTools.getSfxTransportSummary(transport);
    }
    if (status) {
      status.textContent = diagnostics.label;
      status.className = `sfx-transport-status is-${diagnostics.level}`;
    }
    if (restartMode) {
      restartMode.disabled = !transport.loop;
    }
    if (replaceFade) {
      replaceFade.disabled = !transport.loop;
    }
    return transport;
  }

  function applySfxTransportPreset(presetId, documentRef = global.document, options = {}) {
    const preset = SFX_TRANSPORT_PRESETS[presetId];
    if (!preset) {
      return Object.freeze({ ok: false, label: "没有找到这组声音预设。" });
    }
    const fieldMap = {
      channelId: "editorSfxChannelId",
      loop: "editorSfxLoop",
      restartMode: "editorSfxRestartMode",
      volume: "editorSfxVolume",
      fadeInMs: "editorSfxFadeInMs",
      replaceFadeOutMs: "editorSfxReplaceFadeOutMs",
    };
    Object.entries(fieldMap).forEach(([key, id]) => {
      const control = documentRef?.getElementById?.(id);
      if (control) {
        control.value = String(preset.values[key]);
      }
    });
    updateSfxTransportPreview(documentRef, options);
    return Object.freeze({ ok: true, label: `已套用声音预设：${preset.label}` });
  }

  function renderSfxStopEditor(block = {}, options = {}) {
    const runtimeTools = getRuntimeTools(options);
    const stop = runtimeTools.sanitizeSfxStop(block);
    return `
      <article class="editor-card">
        <h3>停止环境声或音效</h3>
        <p>通常用于结束雨声、风声、持续心跳等循环声音，也可以一键清空所有音效声道。</p>
      </article>
      <div class="field-grid">
        <div class="detail-row">
          <label for="editorSfxStopChannelId">停止哪个声音用途</label>
          <select id="editorSfxStopChannelId">
            <option value="all" ${stop.channelId === "all" ? "selected" : ""}>全部音效声道</option>
            <option value="effect" ${stop.channelId === "effect" ? "selected" : ""}>效果声道</option>
            <option value="ambience" ${stop.channelId === "ambience" ? "selected" : ""}>环境声道</option>
            <option value="ui" ${stop.channelId === "ui" ? "selected" : ""}>界面声道</option>
          </select>
        </div>
        <div class="detail-row">
          <label for="editorSfxStopFadeOutMs">淡出时间（毫秒）</label>
          <input id="editorSfxStopFadeOutMs" type="number" min="0" max="60000" step="100" value="${stop.fadeOutMs}" />
        </div>
      </div>
      <div class="sfx-transport-summary">${escapeHtml(runtimeTools.getSfxStopSummary(stop))}</div>
      <div class="detail-actions">
        <button class="toolbar-button toolbar-button-primary" data-action="save-block">保存这张卡片</button>
      </div>`;
  }

  function readSfxStopEditor(block = {}, documentRef = global.document, options = {}) {
    return getRuntimeTools(options).sanitizeSfxStop({
      ...block,
      channelId: documentRef?.getElementById("editorSfxStopChannelId")?.value,
      fadeOutMs: documentRef?.getElementById("editorSfxStopFadeOutMs")?.value,
    });
  }

  global.CanvasiaEditorSfxTransport = Object.freeze({
    SFX_TRANSPORT_PRESETS,
    renderSfxTransportEditor,
    readSfxTransportEditor,
    updateSfxTransportPreview,
    applySfxTransportPreset,
    renderSfxStopEditor,
    readSfxStopEditor,
  });
})(typeof window !== "undefined" ? window : globalThis);
