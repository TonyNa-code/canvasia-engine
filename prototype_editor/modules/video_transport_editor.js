(function attachVideoTransportEditor(global) {
  "use strict";

  const VIDEO_TRANSPORT_PRESETS = Object.freeze({
    op_ed: Object.freeze({
      label: "OP / ED",
      description: "自动完整播放一次，保留黑边，不裁掉字幕或片尾名单。",
      values: Object.freeze({ autoplay: true, loop: false, resumeMode: "restart", startTimeSeconds: 0, endTimeSeconds: 0, fit: "contain", volume: 100, skippable: true }),
    }),
    cutscene: Object.freeze({
      label: "剧情过场",
      description: "自动播放一次并铺满舞台，适合短演出或转场动画。",
      values: Object.freeze({ autoplay: true, loop: false, resumeMode: "resume", startTimeSeconds: 0, endTimeSeconds: 0, fit: "cover", volume: 100, skippable: true }),
    }),
    atmosphere_loop: Object.freeze({
      label: "循环氛围",
      description: "静音循环并铺满舞台，玩家确认后结束循环继续剧情。",
      values: Object.freeze({ autoplay: true, loop: true, resumeMode: "resume", startTimeSeconds: 0, endTimeSeconds: 0, fit: "cover", volume: 0, skippable: true }),
    }),
    manual_clip: Object.freeze({
      label: "手动播放",
      description: "先停在视频卡片，由玩家决定何时开始；读档后从保存位置继续。",
      values: Object.freeze({ autoplay: false, loop: false, resumeMode: "resume", startTimeSeconds: 0, endTimeSeconds: 0, fit: "contain", volume: 100, skippable: true }),
    }),
  });

  function getRuntimeTools(options = {}) {
    return options.runtimeTools ?? global.CanvasiaRuntimeVideoTransport;
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function renderLabelOptions(labels = {}, selectedValue = "") {
    return Object.entries(labels)
      .map(([value, label]) => `<option value="${escapeHtml(value)}" ${value === selectedValue ? "selected" : ""}>${escapeHtml(label)}</option>`)
      .join("");
  }

  function renderVideoTransportEditor(block = {}, options = {}) {
    const runtimeTools = getRuntimeTools(options);
    const transport = runtimeTools.sanitizeVideoTransport(block);
    const diagnostics = runtimeTools.getVideoTransportDiagnostics(block);
    const fitLabels = options.videoFitLabels ?? { contain: "完整显示（可能留黑边）", cover: "铺满画面（可能裁边）", fill: "拉伸铺满" };
    const presetButtons = Object.entries(VIDEO_TRANSPORT_PRESETS)
      .map(([id, preset]) => `
        <button type="button" class="toolbar-button" data-action="apply-video-transport-preset" data-video-transport-preset="${id}" title="${escapeHtml(preset.description)}">
          ${escapeHtml(preset.label)}
        </button>`)
      .join("");

    return `
      <section class="video-transport-editor" data-video-transport-editor>
        <div class="video-transport-heading">
          <div>
            <strong>视频播放导演</strong>
            <span>起播方式、片段范围、循环与读档行为</span>
          </div>
          <span class="video-transport-status is-${diagnostics.level}" data-video-transport-status>${escapeHtml(diagnostics.label)}</span>
        </div>
        <div class="detail-actions video-transport-presets">${presetButtons}</div>
        <div class="field-grid compact-grid video-transport-fields">
          <div class="detail-row">
            <label for="editorVideoAutoplay">进入这张卡片时</label>
            <select id="editorVideoAutoplay">
              <option value="true" ${transport.autoplay ? "selected" : ""}>自动开始播放</option>
              <option value="false" ${!transport.autoplay ? "selected" : ""}>等待玩家手动播放</option>
            </select>
          </div>
          <div class="detail-row">
            <label for="editorVideoLoop">播放到片段结尾后</label>
            <select id="editorVideoLoop">
              <option value="false" ${!transport.loop ? "selected" : ""}>继续后面的剧情</option>
              <option value="true" ${transport.loop ? "selected" : ""}>回到片段开头循环</option>
            </select>
          </div>
          <div class="detail-row">
            <label for="editorVideoResumeMode">读档回到这段视频时</label>
            <select id="editorVideoResumeMode">
              <option value="restart" ${transport.resumeMode === "restart" ? "selected" : ""}>从片段开头重播</option>
              <option value="resume" ${transport.resumeMode === "resume" ? "selected" : ""}>从存档位置继续</option>
            </select>
          </div>
          <div class="detail-row">
            <label for="editorVideoFit">画面适配</label>
            <select id="editorVideoFit">${renderLabelOptions(fitLabels, transport.fit)}</select>
          </div>
          <div class="detail-row">
            <label for="editorVideoVolume">视频音量</label>
            <input id="editorVideoVolume" type="number" min="0" max="100" step="1" value="${transport.volume}" />
            <p class="helper-text">可输入 0–100；0 为静音，预设也会自动填写。</p>
          </div>
          <div class="detail-row">
            <label for="editorVideoStartTime">从第几秒开始</label>
            <input id="editorVideoStartTime" type="number" min="0" max="21600" step="0.1" value="${transport.startTimeSeconds}" />
          </div>
          <div class="detail-row">
            <label for="editorVideoEndTime">到第几秒结束</label>
            <input id="editorVideoEndTime" type="number" min="0" max="21600" step="0.1" value="${transport.endTimeSeconds}" />
            <p class="helper-text">填 0 表示播放到视频自然结尾。</p>
          </div>
          <div class="detail-row">
            <label for="editorVideoSkippable">玩家能否提前结束</label>
            <select id="editorVideoSkippable" ${transport.loop ? "disabled" : ""}>
              <option value="true" ${transport.skippable ? "selected" : ""}>允许跳过</option>
              <option value="false" ${!transport.skippable ? "selected" : ""}>必须播放完</option>
            </select>
            <p class="helper-text">循环视频会始终保留“结束循环”，避免玩家被困住。</p>
          </div>
        </div>
        <div class="video-transport-summary" data-video-transport-summary>${escapeHtml(runtimeTools.getVideoTransportSummary(transport))}</div>
      </section>`;
  }

  function readVideoTransportEditor(block = {}, documentRef = global.document, options = {}) {
    const runtimeTools = getRuntimeTools(options);
    return runtimeTools.sanitizeVideoTransport({
      ...block,
      autoplay: documentRef?.getElementById("editorVideoAutoplay")?.value !== "false",
      loop: documentRef?.getElementById("editorVideoLoop")?.value === "true",
      resumeMode: documentRef?.getElementById("editorVideoResumeMode")?.value,
      fit: documentRef?.getElementById("editorVideoFit")?.value,
      volume: documentRef?.getElementById("editorVideoVolume")?.value,
      startTimeSeconds: documentRef?.getElementById("editorVideoStartTime")?.value,
      endTimeSeconds: documentRef?.getElementById("editorVideoEndTime")?.value,
      skippable: documentRef?.getElementById("editorVideoSkippable")?.value !== "false",
    });
  }

  function updateVideoTransportPreview(documentRef = global.document, options = {}) {
    const runtimeTools = getRuntimeTools(options);
    const rawSource = {
      autoplay: documentRef?.getElementById?.("editorVideoAutoplay")?.value !== "false",
      loop: documentRef?.getElementById?.("editorVideoLoop")?.value === "true",
      resumeMode: documentRef?.getElementById?.("editorVideoResumeMode")?.value,
      fit: documentRef?.getElementById?.("editorVideoFit")?.value,
      volume: documentRef?.getElementById?.("editorVideoVolume")?.value,
      startTimeSeconds: documentRef?.getElementById?.("editorVideoStartTime")?.value,
      endTimeSeconds: documentRef?.getElementById?.("editorVideoEndTime")?.value,
      skippable: documentRef?.getElementById?.("editorVideoSkippable")?.value !== "false",
    };
    const transport = runtimeTools.sanitizeVideoTransport(rawSource);
    const diagnostics = runtimeTools.getVideoTransportDiagnostics(rawSource);
    const summary = documentRef?.querySelector?.("[data-video-transport-summary]");
    const status = documentRef?.querySelector?.("[data-video-transport-status]");
    const skippable = documentRef?.getElementById?.("editorVideoSkippable");
    if (summary) {
      summary.textContent = runtimeTools.getVideoTransportSummary(transport);
    }
    if (status) {
      status.textContent = diagnostics.label;
      status.className = `video-transport-status is-${diagnostics.level}`;
    }
    if (skippable) {
      skippable.disabled = transport.loop;
      if (transport.loop) {
        skippable.value = "true";
      }
    }
    return transport;
  }

  function applyVideoTransportPreset(presetId, documentRef = global.document, options = {}) {
    const preset = VIDEO_TRANSPORT_PRESETS[presetId];
    if (!preset) {
      return Object.freeze({ ok: false, label: "没有找到这组视频播放预设。" });
    }
    const fieldMap = {
      autoplay: "editorVideoAutoplay",
      loop: "editorVideoLoop",
      resumeMode: "editorVideoResumeMode",
      startTimeSeconds: "editorVideoStartTime",
      endTimeSeconds: "editorVideoEndTime",
      fit: "editorVideoFit",
      volume: "editorVideoVolume",
      skippable: "editorVideoSkippable",
    };
    Object.entries(fieldMap).forEach(([key, id]) => {
      const control = documentRef?.getElementById?.(id);
      if (control) {
        control.value = String(preset.values[key]);
      }
    });
    updateVideoTransportPreview(documentRef, options);
    return Object.freeze({ ok: true, label: `已套用视频预设：${preset.label}` });
  }

  function createPreviewVideoController(options = {}) {
    const runtimeTools = getRuntimeTools(options);
    let active = null;

    function stop() {
      if (!active) {
        return;
      }
      active.cleanup?.();
      if (active.timer) {
        global.clearTimeout?.(active.timer);
      }
      active.video?.pause?.();
      active.video?.removeAttribute?.("src");
      active.video?.load?.();
      active.overlay?.remove?.();
      active = null;
    }

    function capture(snapshot) {
      if (!active || active.snapshot !== snapshot) {
        return 0;
      }
      const position = runtimeTools.getVideoPlaybackPosition(
        active.video,
        snapshot?.videoPlaybackPositionSeconds ?? active.transport.startTimeSeconds
      );
      snapshot.videoPlaybackPositionSeconds = position;
      return position;
    }

    function sync(snapshot, syncOptions = {}) {
      const root = syncOptions.root;
      if (!snapshot || snapshot.blockType !== "video_play" || !root) {
        stop();
        return false;
      }
      const stepKey = String(syncOptions.stepKey ?? "");
      if (active?.stepKey === stepKey && root.contains?.(active.overlay)) {
        return true;
      }

      stop();
      const documentRef = root.ownerDocument ?? global.document;
      const transport = runtimeTools.sanitizeVideoTransport(snapshot.block);
      const overlay = documentRef.createElement("div");
      const video = documentRef.createElement("video");
      const chrome = documentRef.createElement("div");
      const title = documentRef.createElement("span");
      const skipButton = documentRef.createElement("button");
      overlay.className = "preview-video-overlay";
      overlay.dataset.fit = transport.fit;
      overlay.setAttribute("data-preview-video-overlay", "");
      video.className = "preview-runtime-video";
      video.controls = true;
      video.playsInline = true;
      video.preload = "metadata";
      chrome.className = "preview-video-overlay-ui";
      title.textContent = String(syncOptions.title || "视频播放");
      skipButton.type = "button";
      skipButton.className = "toolbar-button";
      skipButton.textContent = transport.loop ? "结束循环" : "跳过视频";
      skipButton.hidden = !transport.skippable;
      chrome.append(title, skipButton);
      overlay.append(video, chrome);
      overlay.addEventListener("click", (event) => event.stopPropagation());
      overlay.addEventListener("contextmenu", (event) => event.stopPropagation());
      root.append(overlay);

      const finish = (detail = {}) => {
        if (!active || active.stepKey !== stepKey) {
          return;
        }
        const completedSnapshot = active.snapshot;
        stop();
        syncOptions.onFinished?.(completedSnapshot, detail);
      };
      const cleanup = runtimeTools.bindVideoTransportToVideo(video, transport, {
        initialPositionSeconds: snapshot.videoPlaybackPositionSeconds,
        onFinished: (reason) => finish({ reason }),
        onLoop: () => {
          title.textContent = `${String(syncOptions.title || "视频播放")} · 循环中`;
        },
        onError: () => {
          title.textContent = `${String(syncOptions.title || "视频播放")} · 文件无法播放`;
          if (active) {
            active.timer = global.setTimeout?.(() => finish({ reason: "error" }), 1600);
          }
        },
      });
      active = { stepKey, snapshot, overlay, video, transport, cleanup, timer: null };
      skipButton.addEventListener("click", (event) => {
        event.stopPropagation();
        finish({ reason: transport.loop ? "loop-exit" : "skipped", skipped: true });
      });

      const videoUrl = String(syncOptions.videoUrl || "").trim();
      if (!videoUrl) {
        title.textContent = `${String(syncOptions.title || "视频播放")} · 素材缺失`;
        active.timer = global.setTimeout?.(() => finish({ reason: "missing" }), 1600);
        return true;
      }
      video.src = encodeURI(videoUrl);
      video.load?.();
      if (transport.autoplay) {
        video.play?.().catch?.(() => {
          title.textContent = `${String(syncOptions.title || "视频播放")} · 点击画面开始`;
        });
      } else {
        title.textContent = `${String(syncOptions.title || "视频播放")} · 等待手动播放`;
      }
      return true;
    }

    return Object.freeze({ sync, capture, stop });
  }

  global.CanvasiaEditorVideoTransport = Object.freeze({
    VIDEO_TRANSPORT_PRESETS,
    renderVideoTransportEditor,
    readVideoTransportEditor,
    updateVideoTransportPreview,
    applyVideoTransportPreset,
    createPreviewVideoController,
  });
})(typeof window !== "undefined" ? window : globalThis);
