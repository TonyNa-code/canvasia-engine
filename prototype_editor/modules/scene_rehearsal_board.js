(function attachSceneRehearsalBoardTools(global) {
  const commonTools = global.CanvasiaEditorCommon || {};
  const storyBlockCatalogTools = global.CanvasiaEditorStoryBlockCatalog || {};

  const REHEARSAL_LANES = Object.freeze([
    Object.freeze({ id: "story", label: "对白", shortLabel: "文", note: "台词、旁白、选项与玩家输入" }),
    Object.freeze({ id: "stage", label: "舞台", shortLabel: "景", note: "背景、角色、道具、视频与片尾" }),
    Object.freeze({ id: "audio", label: "声音", shortLabel: "声", note: "BGM、环境声、音效与语音" }),
    Object.freeze({ id: "motion", label: "演出", shortLabel: "演", note: "镜头、滤镜、粒子、转场与停顿" }),
    Object.freeze({ id: "logic", label: "路线", shortLabel: "路", note: "分支、跳转、变量、调用与成就" }),
  ]);

  const BLOCK_LANES = Object.freeze({
    dialogue: ["story"],
    narration: ["story"],
    choice: ["story", "logic"],
    text_input: ["story", "logic"],
    background: ["stage"],
    stage_image: ["stage"],
    character_show: ["stage"],
    character_move: ["stage", "motion"],
    character_hide: ["stage"],
    video_play: ["stage", "audio"],
    credits_roll: ["stage", "motion"],
    music_play: ["audio"],
    music_stop: ["audio"],
    sfx_play: ["audio"],
    sfx_stop: ["audio"],
    wait: ["motion"],
    particle_effect: ["motion"],
    screen_shake: ["motion"],
    screen_flash: ["motion"],
    screen_fade: ["motion"],
    camera_zoom: ["motion"],
    camera_pan: ["motion"],
    screen_filter: ["motion"],
    depth_blur: ["motion"],
    jump: ["logic"],
    condition: ["logic"],
    scene_call: ["logic"],
    scene_return: ["logic"],
    variable_set: ["logic"],
    variable_add: ["logic"],
    achievement_unlock: ["logic"],
  });

  function fallbackEscapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  const escapeHtml = commonTools.escapeHtml || fallbackEscapeHtml;

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

  function getBlockLanes(block = {}) {
    const lanes = [...(BLOCK_LANES[block.type] ?? ["motion"])];
    if (["dialogue", "narration"].includes(block.type) && cleanText(block.voiceAssetId)) {
      lanes.push("audio");
    }
    return [...new Set(lanes)];
  }

  function getBlockLabel(block = {}, options = {}) {
    const catalogLabel = storyBlockCatalogTools.getBlockLabel?.(block.type);
    return cleanText(options.blockLabels?.[block.type], cleanText(catalogLabel ?? block.type, "卡片"));
  }

  function getBlockSummary(block = {}, scene = {}, options = {}) {
    if (typeof options.getBlockSummary === "function") {
      const summary = options.getBlockSummary(block, scene) ?? {};
      return {
        title: cleanText(summary.title, getBlockLabel(block, options)),
        detail: cleanText(summary.meta ?? summary.detail, "点击定位并继续编辑"),
      };
    }
    const text = cleanText(block.text ?? block.title ?? block.name ?? block.assetId ?? block.characterId);
    return {
      title: text || getBlockLabel(block, options),
      detail: text ? getBlockLabel(block, options) : "点击定位并继续编辑",
    };
  }

  function formatTimecode(milliseconds) {
    const safeMs = Math.max(0, Number(milliseconds) || 0);
    const totalTenths = Math.round(safeMs / 100);
    const minutes = Math.floor(totalTenths / 600);
    const seconds = Math.floor((totalTenths % 600) / 10);
    const tenths = totalTenths % 10;
    return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}.${tenths}`;
  }

  function buildReportEventMap(sceneReport = {}) {
    const byBlockId = new Map();
    const byBlockIndex = new Map();
    toArray(sceneReport.events).forEach((event) => {
      const blockId = cleanText(event?.blockId);
      if (blockId) {
        byBlockId.set(blockId, event);
      }
      if (Number.isInteger(event?.blockIndex)) {
        byBlockIndex.set(event.blockIndex, event);
      }
    });
    return { byBlockId, byBlockIndex };
  }

  function buildReportIssueMap(sceneReport = {}) {
    const byBlockId = new Map();
    const byBlockIndex = new Map();
    toArray(sceneReport.issues).forEach((issue) => {
      const blockId = cleanText(issue?.blockId);
      if (blockId) {
        byBlockId.set(blockId, [...(byBlockId.get(blockId) ?? []), issue]);
      }
      if (Number.isInteger(issue?.blockIndex) && issue.blockIndex >= 0) {
        byBlockIndex.set(issue.blockIndex, [...(byBlockIndex.get(issue.blockIndex) ?? []), issue]);
      }
    });
    return { byBlockId, byBlockIndex };
  }

  function getBeatWindow(beatCount, selectedIndex, maximum = 48) {
    const safeCount = Math.max(0, Number(beatCount) || 0);
    const safeMaximum = Math.round(clampNumber(maximum, 8, 96, 48));
    if (safeCount <= safeMaximum) {
      return { start: 0, end: safeCount, truncated: false };
    }
    const safeSelected = Math.round(clampNumber(selectedIndex, 0, safeCount - 1, 0));
    const preferredBefore = Math.floor(safeMaximum * 0.38);
    const start = Math.min(Math.max(safeSelected - preferredBefore, 0), safeCount - safeMaximum);
    return { start, end: start + safeMaximum, truncated: true };
  }

  function getBeatStatus(issues = []) {
    if (issues.some((issue) => issue.severity === "blocker")) {
      return "blocker";
    }
    if (issues.some((issue) => issue.severity === "warn")) {
      return "warn";
    }
    if (issues.length > 0) {
      return "tip";
    }
    return "ready";
  }

  function buildSceneRehearsalModel(scene = {}, sceneReport = {}, options = {}) {
    const blocks = toArray(scene.blocks);
    const selectedBlockId = cleanText(options.selectedBlockId);
    const eventMap = buildReportEventMap(sceneReport);
    const issueMap = buildReportIssueMap(sceneReport);
    let elapsedMs = 0;
    const beats = blocks.map((block, blockIndex) => {
      const blockId = cleanText(block?.id, `block_${blockIndex + 1}`);
      const event = eventMap.byBlockId.get(blockId) ?? eventMap.byBlockIndex.get(blockIndex) ?? null;
      const issues = issueMap.byBlockId.get(blockId) ?? issueMap.byBlockIndex.get(blockIndex) ?? [];
      const summary = getBlockSummary(block, scene, options);
      const durationMs = Math.max(0, Number(event?.durationMs) || 0);
      const beat = {
        blockId,
        blockIndex,
        number: blockIndex + 1,
        type: cleanText(block?.type, "unknown"),
        label: getBlockLabel(block, options),
        title: summary.title,
        detail: summary.detail,
        lanes: getBlockLanes(block),
        durationMs,
        startMs: elapsedMs,
        endMs: elapsedMs + durationMs,
        startTimecode: formatTimecode(elapsedMs),
        durationLabel: durationMs > 0 ? (options.formatDuration?.(durationMs) ?? formatTimecode(durationMs)) : "瞬时",
        hasVoice: Boolean(cleanText(block?.voiceAssetId)),
        issues,
        status: getBeatStatus(issues),
        selected: blockId === selectedBlockId,
      };
      elapsedMs += durationMs;
      return beat;
    });

    let selectedIndex = beats.findIndex((beat) => beat.selected);
    if (selectedIndex < 0 && beats.length > 0) {
      selectedIndex = 0;
      beats[0].selected = true;
    }
    const windowRange = getBeatWindow(beats.length, selectedIndex, options.maxVisibleBeats ?? 48);
    const visibleBeats = beats.slice(windowRange.start, windowRange.end);
    const laneRows = REHEARSAL_LANES.map((lane) => ({
      ...lane,
      markerCount: beats.filter((beat) => beat.lanes.includes(lane.id)).length,
      beats: visibleBeats.filter((beat) => beat.lanes.includes(lane.id)),
    }));
    const reportIssues = toArray(sceneReport.issues);

    return {
      sceneId: cleanText(scene.id),
      sceneName: cleanText(scene.name ?? scene.title, "未命名场景"),
      chapterName: cleanText(scene.chapterName, "未分章"),
      beats,
      visibleBeats,
      laneRows,
      selectedBeat: selectedIndex >= 0 ? beats[selectedIndex] : null,
      previousBeat: selectedIndex > 0 ? beats[selectedIndex - 1] : null,
      nextBeat: selectedIndex >= 0 && selectedIndex < beats.length - 1 ? beats[selectedIndex + 1] : null,
      window: {
        ...windowRange,
        firstNumber: visibleBeats[0]?.number ?? 0,
        lastNumber: visibleBeats.at(-1)?.number ?? 0,
      },
      issues: reportIssues,
      summary: {
        beatCount: beats.length,
        estimatedDurationMs: elapsedMs,
        estimatedDurationLabel: options.formatDuration?.(elapsedMs) ?? formatTimecode(elapsedMs),
        activeLaneCount: laneRows.filter((lane) => lane.markerCount > 0).length,
        voicedBeatCount: beats.filter((beat) => beat.hasVoice).length,
        issueCount: reportIssues.length,
        blockerCount: reportIssues.filter((issue) => issue.severity === "blocker").length,
        warningCount: reportIssues.filter((issue) => issue.severity === "warn").length,
      },
    };
  }

  function getBeatToneLabel(beat = {}) {
    if (beat.status === "blocker") {
      return "先修";
    }
    if (beat.status === "warn") {
      return "复查";
    }
    if (beat.status === "tip") {
      return "润色";
    }
    return beat.durationLabel ?? "瞬时";
  }

  function renderBeatButton(beat = {}, laneId = "story", visibleIndex = 0) {
    const currentMarkup = beat.selected ? ' aria-current="true"' : "";
    const ariaLabel = `第 ${beat.number} 张，${beat.label}，${beat.title}，${beat.startTimecode}`;
    return `
      <button
        type="button"
        class="scene-rehearsal-beat is-${escapeHtml(laneId)} is-${escapeHtml(beat.status)}${beat.selected ? " is-selected" : ""}"
        data-slot="scene-rehearsal-beat"
        data-state="${beat.selected ? "selected" : "idle"}"
        data-action="select-block"
        data-block-id="${escapeHtml(beat.blockId)}"
        style="--rehearsal-column: ${visibleIndex + 1}"
        aria-label="${escapeHtml(ariaLabel)}"${currentMarkup}
        title="${escapeHtml(`${beat.startTimecode} · ${beat.detail}`)}"
      >
        <span class="scene-rehearsal-beat-index">${beat.number}</span>
        <strong>${escapeHtml(beat.label)}</strong>
        <small>${escapeHtml(beat.title)}</small>
        <em>${escapeHtml(getBeatToneLabel(beat))}</em>
      </button>
    `;
  }

  function renderCompactBeatStrip(model = {}) {
    const selectedIndex = Math.max(0, model.visibleBeats.findIndex((beat) => beat.selected));
    const start = Math.max(0, selectedIndex - 3);
    const end = Math.min(model.visibleBeats.length, start + 7);
    const compactBeats = model.visibleBeats.slice(Math.max(0, end - 7), end);
    return `
      <div class="scene-rehearsal-compact-strip" role="group" aria-label="当前场景节拍速览">
        ${compactBeats
          .map(
            (beat) => `
              <button
                type="button"
                class="scene-rehearsal-compact-beat is-${escapeHtml(beat.lanes[0] ?? "motion")}${beat.selected ? " is-selected" : ""}"
                data-slot="scene-rehearsal-compact-beat"
                data-state="${beat.selected ? "selected" : "idle"}"
                data-action="select-block"
                data-block-id="${escapeHtml(beat.blockId)}"
                aria-label="第 ${beat.number} 张，${escapeHtml(beat.label)}，${escapeHtml(beat.title)}"
                ${beat.selected ? 'aria-current="true"' : ""}
              >
                <span>${String(beat.number).padStart(2, "0")}</span>
                <strong>${escapeHtml(beat.label)}</strong>
              </button>
            `
          )
          .join("")}
      </div>
    `;
  }

  function renderTimeRuler(model = {}) {
    return `
      <div class="scene-rehearsal-ruler" style="--rehearsal-column-count: ${model.visibleBeats.length}">
        <div class="scene-rehearsal-lane-label is-ruler">
          <span>TIME</span>
          <strong>节拍</strong>
        </div>
        <div class="scene-rehearsal-track is-ruler" aria-hidden="true">
          ${model.visibleBeats
            .map(
              (beat, index) => `
                <span class="scene-rehearsal-timecode" style="--rehearsal-column: ${index + 1}">
                  ${escapeHtml(beat.startTimecode)}
                </span>
              `
            )
            .join("")}
        </div>
      </div>
    `;
  }

  function renderLaneRow(lane = {}, model = {}) {
    const visibleIndexByBlockId = new Map(model.visibleBeats.map((beat, index) => [beat.blockId, index]));
    return `
      <div class="scene-rehearsal-lane" data-slot="scene-rehearsal-lane" data-lane="${escapeHtml(lane.id)}">
        <div class="scene-rehearsal-lane-label">
          <span>${escapeHtml(lane.shortLabel)}</span>
          <strong>${escapeHtml(lane.label)}</strong>
          <small>${lane.markerCount}</small>
        </div>
        <div
          class="scene-rehearsal-track"
          role="group"
          aria-label="${escapeHtml(`${lane.label}轨道：${lane.note}`)}"
          style="--rehearsal-column-count: ${model.visibleBeats.length}"
        >
          ${lane.beats
            .map((beat) => renderBeatButton(beat, lane.id, visibleIndexByBlockId.get(beat.blockId) ?? 0))
            .join("")}
        </div>
      </div>
    `;
  }

  function renderSelectedBeatInspector(model = {}) {
    const beat = model.selectedBeat;
    if (!beat) {
      return "";
    }
    return `
      <div class="scene-rehearsal-selection" data-slot="scene-rehearsal-selection">
        <div class="scene-rehearsal-selection-copy">
          <span class="scene-rehearsal-kicker">SELECTED BEAT · ${escapeHtml(beat.startTimecode)}</span>
          <strong>第 ${beat.number} 张 · ${escapeHtml(beat.label)} · ${escapeHtml(beat.title)}</strong>
          <small>${escapeHtml(beat.detail)} · ${escapeHtml(beat.durationLabel)}</small>
        </div>
        <div class="scene-rehearsal-selection-actions">
          <button type="button" class="toolbar-button" data-action="select-block" data-block-id="${escapeHtml(
            model.previousBeat?.blockId ?? ""
          )}" ${model.previousBeat ? "" : "disabled"}>上一拍</button>
          <button type="button" class="toolbar-button" data-action="select-block" data-block-id="${escapeHtml(
            model.nextBeat?.blockId ?? ""
          )}" ${model.nextBeat ? "" : "disabled"}>下一拍</button>
          <button
            type="button"
            class="toolbar-button toolbar-button-primary"
            data-action="preview-story-location"
            data-scene-id="${escapeHtml(model.sceneId)}"
            data-block-id="${escapeHtml(beat.blockId)}"
          >从这一拍试演</button>
        </div>
      </div>
    `;
  }

  function renderIssueQueue(model = {}) {
    const issues = model.issues.slice(0, 4);
    if (!issues.length) {
      return `
        <div class="scene-rehearsal-clear-state">
          <span>排练记录</span>
          <strong>没有发现明显的演出结构问题</strong>
          <small>仍建议从高光段完整试玩一次，确认真实节奏。</small>
        </div>
      `;
    }
    return `
      <div class="scene-rehearsal-issue-queue" aria-label="当前场景演出问题">
        ${issues
          .map((issue) => {
            const blockId = cleanText(issue.blockId);
            const content = `
              <span>${issue.severity === "blocker" ? "先修" : issue.severity === "warn" ? "复查" : "润色"}</span>
              <strong>${escapeHtml(issue.title ?? "演出问题")}</strong>
              <small>${escapeHtml(issue.detail ?? "定位后复查这一拍。")}</small>
            `;
            return blockId
              ? `<button type="button" class="scene-rehearsal-issue is-${escapeHtml(
                  issue.severity ?? "tip"
                )}" data-action="select-block" data-block-id="${escapeHtml(blockId)}">${content}</button>`
              : `<article class="scene-rehearsal-issue is-${escapeHtml(issue.severity ?? "tip")}">${content}</article>`;
          })
          .join("")}
      </div>
    `;
  }

  function handleSceneRehearsalKeyboardNavigation(event, root = null) {
    if (!event || !["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) {
      return false;
    }
    const target = event.target?.closest?.(
      '[data-slot="scene-rehearsal-beat"], [data-slot="scene-rehearsal-compact-beat"]'
    );
    if (!target || (root && !root.contains?.(target))) {
      return false;
    }
    const group = target.closest?.('[role="group"]');
    if (!group) {
      return false;
    }
    const selector = target.matches?.('[data-slot="scene-rehearsal-beat"]')
      ? '[data-slot="scene-rehearsal-beat"]'
      : '[data-slot="scene-rehearsal-compact-beat"]';
    const buttons = Array.from(group.querySelectorAll?.(selector) ?? []).filter((button) => !button.disabled);
    const currentIndex = buttons.indexOf(target);
    if (currentIndex < 0 || buttons.length < 2) {
      return false;
    }
    let nextIndex = currentIndex;
    if (event.key === "Home") {
      nextIndex = 0;
    } else if (event.key === "End") {
      nextIndex = buttons.length - 1;
    } else if (event.key === "ArrowLeft") {
      nextIndex = currentIndex > 0 ? currentIndex - 1 : buttons.length - 1;
    } else if (event.key === "ArrowRight") {
      nextIndex = currentIndex < buttons.length - 1 ? currentIndex + 1 : 0;
    }
    event.preventDefault?.();
    buttons[nextIndex]?.focus?.({ preventScroll: false });
    return true;
  }

  function renderSceneRehearsalBoard(scene = {}, sceneReport = {}, options = {}) {
    const model = buildSceneRehearsalModel(scene, sceneReport, options);
    const expanded = Boolean(options.expanded);
    if (!model.beats.length) {
      return `
        <section class="scene-rehearsal-board is-empty" data-slot="scene-rehearsal-board" data-state="empty">
          <div>
            <span class="scene-rehearsal-kicker">SCENE REHEARSAL</span>
            <strong>导演排练台会在场景有卡片后出现</strong>
            <small>先加一张台词、背景或音乐卡，再回来查看整场节拍。</small>
          </div>
        </section>
      `;
    }

    const windowLabel = model.window.truncated
      ? `当前显示第 ${model.window.firstNumber}-${model.window.lastNumber} 张，共 ${model.summary.beatCount} 张`
      : `完整显示 ${model.summary.beatCount} 张卡片`;
    const statusTone = model.summary.blockerCount > 0 ? "blocker" : model.summary.warningCount > 0 ? "warn" : "ready";
    const trackMinWidth = Math.max(760, model.visibleBeats.length * 118);

    return `
      <section
        class="scene-rehearsal-board is-${statusTone}${expanded ? " is-expanded" : ""}"
        data-slot="scene-rehearsal-board"
        data-state="${expanded ? "expanded" : "collapsed"}"
        aria-labelledby="sceneRehearsalTitle"
      >
        <div class="scene-rehearsal-head">
          <div class="scene-rehearsal-title-lockup">
            <span class="scene-rehearsal-kicker">SCENE REHEARSAL · ${escapeHtml(model.chapterName)}</span>
            <div>
              <h2 id="sceneRehearsalTitle">导演排练台</h2>
              <strong>${escapeHtml(model.sceneName)}</strong>
            </div>
            <p>把对白、舞台、声音、演出和路线摊在同一张分镜条上。点任意节拍即可回到卡片，也能从那一拍直接试玩。</p>
          </div>
          <div class="scene-rehearsal-head-actions">
            <button
              type="button"
              class="toolbar-button ${expanded ? "" : "toolbar-button-primary"}"
              data-action="toggle-scene-rehearsal"
              aria-expanded="${expanded ? "true" : "false"}"
              aria-controls="sceneRehearsalTracks"
            >${expanded ? "收起轨道" : "展开排练轨道"}</button>
            <button
              type="button"
              class="toolbar-button ${expanded ? "toolbar-button-primary" : ""}"
              data-action="preview-story-location"
              data-scene-id="${escapeHtml(model.sceneId)}"
              data-block-id="${escapeHtml(model.selectedBeat?.blockId ?? model.beats[0].blockId)}"
            >从当前节拍试演</button>
          </div>
        </div>
        <div class="scene-rehearsal-metrics" aria-label="场景排练摘要">
          <span><b>${model.summary.beatCount}</b> 个节拍</span>
          <span><b>${escapeHtml(model.summary.estimatedDurationLabel)}</b> 预计时长</span>
          <span><b>${model.summary.activeLaneCount}/5</b> 条轨道已使用</span>
          <span><b>${model.summary.voicedBeatCount}</b> 句已绑语音</span>
          <span class="is-${statusTone}"><b>${model.summary.issueCount}</b> 个排练提醒</span>
          <small>${escapeHtml(windowLabel)}</small>
        </div>
        ${renderCompactBeatStrip(model)}
        <div
          id="sceneRehearsalTracks"
          class="scene-rehearsal-expanded-content"
          ${expanded ? "" : "hidden"}
        >
          <div class="scene-rehearsal-scroll" style="--rehearsal-track-min-width: ${trackMinWidth}px">
            ${renderTimeRuler(model)}
            ${model.laneRows.map((lane) => renderLaneRow(lane, model)).join("")}
          </div>
          ${renderSelectedBeatInspector(model)}
          ${renderIssueQueue(model)}
        </div>
      </section>
    `;
  }

  global.CanvasiaEditorSceneRehearsalBoard = Object.freeze({
    REHEARSAL_LANES,
    BLOCK_LANES,
    getBlockLanes,
    formatTimecode,
    getBeatWindow,
    buildSceneRehearsalModel,
    renderCompactBeatStrip,
    renderTimeRuler,
    renderLaneRow,
    renderSelectedBeatInspector,
    renderIssueQueue,
    handleSceneRehearsalKeyboardNavigation,
    renderSceneRehearsalBoard,
  });
})(typeof window !== "undefined" ? window : globalThis);
