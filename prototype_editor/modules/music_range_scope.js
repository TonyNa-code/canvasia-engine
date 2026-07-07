(function attachMusicRangeScopeTools(global) {
  const VALID_MUSIC_END_MODES = new Set(["until_next_music", "scene_end", "after_block"]);

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function getEscapeHtml(options = {}) {
    return typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtml;
  }

  function getSceneBlocks(scene = {}) {
    return Array.isArray(scene?.blocks) ? scene.blocks : [];
  }

  function getSafeMusicEndMode(mode, options = {}) {
    if (typeof options.getSafeMusicEndMode === "function") {
      return options.getSafeMusicEndMode(mode);
    }
    const value = String(mode ?? "").trim();
    return VALID_MUSIC_END_MODES.has(value) ? value : "until_next_music";
  }

  function getBlockLabel(type, options = {}) {
    if (typeof options.getBlockLabel === "function") {
      return options.getBlockLabel(type);
    }
    return type || "步骤";
  }

  function truncateText(value, maxLength = 28, options = {}) {
    if (typeof options.truncateText === "function") {
      return options.truncateText(value, maxLength);
    }
    const text = String(value ?? "");
    return text.length > maxLength ? `${text.slice(0, Math.max(0, maxLength - 1))}…` : text;
  }

  function getMusicRangeCandidateBlocks(scene = {}, musicBlock = {}) {
    const blocks = getSceneBlocks(scene);
    const currentIndex = blocks.findIndex((item) => item.id === musicBlock?.id);
    const candidateBlocks = blocks.filter(
      (item, index) => item?.id && (currentIndex < 0 || index > currentIndex)
    );

    if (musicBlock?.endBlockId && !candidateBlocks.some((item) => item.id === musicBlock.endBlockId)) {
      const preservedBlock = blocks.find((item) => item.id === musicBlock.endBlockId);
      if (preservedBlock) {
        candidateBlocks.unshift(preservedBlock);
      }
    }

    return candidateBlocks;
  }

  function getMusicRangeEffectiveEndBlockId(scene = {}, musicBlock = {}) {
    const candidates = getMusicRangeCandidateBlocks(scene, musicBlock);
    const selectedId = String(musicBlock?.endBlockId ?? "");
    if (selectedId && candidates.some((item) => item.id === selectedId)) {
      return selectedId;
    }
    return candidates[0]?.id ?? "";
  }

  function getMusicRangeBlockLabel(scene = {}, block = {}, index = 0, options = {}) {
    const sceneBlocks = getSceneBlocks(scene);
    const label = getBlockLabel(block?.type, options);
    const text = block?.text || block?.title || block?.name || block?.assetId || "";
    const suffix = text ? ` · ${truncateText(text, 28, options)}` : "";
    const sceneIndex = sceneBlocks.findIndex((item) => item.id === block?.id);
    const displayIndex = sceneIndex >= 0 ? sceneIndex + 1 : index + 1;
    return `第 ${displayIndex} 张 · ${label}${suffix}`;
  }

  function renderMusicRangeEndBlockOptions(scene = {}, musicBlock = {}, options = {}) {
    const escape = getEscapeHtml(options);
    const candidates = getMusicRangeCandidateBlocks(scene, musicBlock);
    if (!candidates.length) {
      return `<option value="">当前卡片后面还没有可选结束点</option>`;
    }
    const selectedId = getMusicRangeEffectiveEndBlockId(scene, musicBlock);
    return candidates
      .map((candidate, index) => {
        const selected = candidate.id === selectedId ? "selected" : "";
        return `
        <option value="${escape(candidate.id)}" ${selected}>
          ${escape(getMusicRangeBlockLabel(scene, candidate, index, options))}
        </option>
      `;
      })
      .join("");
  }

  function getMusicRangeSummaryFromValues(scene = {}, endMode, endBlockId = "", options = {}) {
    const safeEndMode = getSafeMusicEndMode(endMode, options);
    const sceneBlocks = getSceneBlocks(scene);
    const currentBlockIndex = sceneBlocks.findIndex((item) => item.id === options.currentBlockId);

    if (safeEndMode === "scene_end") {
      if (currentBlockIndex >= 0) {
        return `这首 BGM 会从第 ${currentBlockIndex + 1} 张开始覆盖当前场景，离开场景时自动结束。`;
      }
      return "这首 BGM 会覆盖当前场景，离开场景时自动结束。";
    }

    if (safeEndMode === "after_block") {
      if (options.hasRangeCandidates === false) {
        return "当前音乐卡后面还没有可选结束点，先在后面新增台词、旁白或演出卡片。";
      }
      const targetBlock = sceneBlocks.find((item) => item.id === endBlockId);
      if (!targetBlock) {
        return "先选择一张结束卡片，音乐会在玩家看完那张卡片后淡出。";
      }
      const blockIndex = sceneBlocks.findIndex((item) => item.id === targetBlock.id);
      if (currentBlockIndex >= 0 && blockIndex >= currentBlockIndex) {
        const spanCount = blockIndex - currentBlockIndex + 1;
        return `这首 BGM 会从第 ${currentBlockIndex + 1} 张播放到第 ${blockIndex + 1} 张「${getBlockLabel(
          targetBlock.type,
          options
        )}」看完后淡出，共覆盖 ${spanCount} 张卡片。`;
      }
      return `这首 BGM 会播放到第 ${blockIndex + 1} 张「${getBlockLabel(targetBlock.type, options)}」看完后淡出。`;
    }

    return "这首 BGM 会一直播放，直到下一张音乐卡或停止音乐卡接管。";
  }

  function getMusicRangeTimelineFromValues(scene = {}, endMode, endBlockId = "", options = {}) {
    const safeEndMode = getSafeMusicEndMode(endMode, options);
    const sceneBlocks = getSceneBlocks(scene);
    const currentBlockIndex = sceneBlocks.findIndex((item) => item.id === options.currentBlockId);
    const targetBlock = sceneBlocks.find((item) => item.id === endBlockId);
    const targetBlockIndex = targetBlock ? sceneBlocks.findIndex((item) => item.id === targetBlock.id) : -1;
    const startLabel = currentBlockIndex >= 0 ? `第 ${currentBlockIndex + 1} 张` : "当前音乐卡";

    if (safeEndMode === "scene_end") {
      return {
        startLabel,
        modeLabel: "覆盖当前场景",
        endLabel: "场景结束",
        countLabel: currentBlockIndex >= 0 ? "从这里开始" : "自动覆盖",
      };
    }

    if (safeEndMode === "after_block") {
      if (options.hasRangeCandidates === false) {
        return {
          startLabel,
          modeLabel: "指定结束卡",
          endLabel: "暂无后续卡",
          countLabel: "先添加卡片",
        };
      }
      if (!targetBlock) {
        return {
          startLabel,
          modeLabel: "指定结束卡",
          endLabel: "未选择",
          countLabel: "等待选择",
        };
      }
      const spanCount =
        currentBlockIndex >= 0 && targetBlockIndex >= currentBlockIndex ? targetBlockIndex - currentBlockIndex + 1 : 1;
      return {
        startLabel,
        modeLabel: "指定结束卡",
        endLabel: targetBlockIndex >= 0 ? `第 ${targetBlockIndex + 1} 张` : "已选卡片",
        countLabel: `覆盖 ${spanCount} 张`,
      };
    }

    return {
      startLabel,
      modeLabel: "持续到接管",
      endLabel: "下一张音乐/停止卡",
      countLabel: "自动接管",
    };
  }

  function getMusicRangeSummary(scene = {}, musicBlock = {}, options = {}) {
    return getMusicRangeSummaryFromValues(
      scene,
      musicBlock?.endMode,
      getMusicRangeEffectiveEndBlockId(scene, musicBlock),
      {
        ...options,
        hasRangeCandidates: getMusicRangeCandidateBlocks(scene, musicBlock).length > 0,
        currentBlockId: musicBlock?.id,
      }
    );
  }

  function getMusicRangeTimeline(scene = {}, musicBlock = {}, options = {}) {
    return getMusicRangeTimelineFromValues(
      scene,
      musicBlock?.endMode,
      getMusicRangeEffectiveEndBlockId(scene, musicBlock),
      {
        ...options,
        hasRangeCandidates: getMusicRangeCandidateBlocks(scene, musicBlock).length > 0,
        currentBlockId: musicBlock?.id,
      }
    );
  }

  function buildMusicRangeDiagnostics(scene = {}, musicBlock = {}, options = {}) {
    const sceneBlocks = getSceneBlocks(scene);
    const mode = getSafeMusicEndMode(musicBlock?.endMode, options);
    const candidates = getMusicRangeCandidateBlocks(scene, musicBlock);
    const selectedEndBlockId = getMusicRangeEffectiveEndBlockId(scene, musicBlock);
    const currentBlockIndex = sceneBlocks.findIndex((item) => item.id === musicBlock?.id);
    const targetBlockIndex = sceneBlocks.findIndex((item) => item.id === selectedEndBlockId);
    const hasRangeCandidates = candidates.length > 0;
    const spanCount =
      currentBlockIndex >= 0 && targetBlockIndex >= currentBlockIndex ? targetBlockIndex - currentBlockIndex + 1 : 0;

    if (mode === "scene_end") {
      return {
        mode,
        selectedEndBlockId,
        hasRangeCandidates,
        currentBlockIndex,
        targetBlockIndex,
        spanCount: currentBlockIndex >= 0 ? Math.max(1, sceneBlocks.length - currentBlockIndex) : 0,
        tone: "good",
        label: "覆盖到场景结束",
        hint: "适合章节开头、整场氛围或长段落背景音乐。",
      };
    }

    if (mode !== "after_block") {
      return {
        mode,
        selectedEndBlockId: "",
        hasRangeCandidates,
        currentBlockIndex,
        targetBlockIndex: -1,
        spanCount: 0,
        tone: "soft",
        label: "持续到下一次接管",
        hint: "适合普通循环 BGM；遇到下一张音乐或停止音乐卡时自动切换。",
      };
    }

    if (!hasRangeCandidates) {
      return {
        mode,
        selectedEndBlockId: "",
        hasRangeCandidates,
        currentBlockIndex,
        targetBlockIndex: -1,
        spanCount: 0,
        tone: "warn",
        label: "还没有可选结束点",
        hint: "先在这张音乐卡后面补台词、旁白或演出卡片，再设置自定义范围。",
      };
    }

    if (!selectedEndBlockId || targetBlockIndex < 0) {
      return {
        mode,
        selectedEndBlockId,
        hasRangeCandidates,
        currentBlockIndex,
        targetBlockIndex,
        spanCount: 0,
        tone: "warn",
        label: "等待选择结束卡",
        hint: "选择一张后续卡片，BGM 会在那张卡看完后淡出。",
      };
    }

    if (currentBlockIndex >= 0 && targetBlockIndex < currentBlockIndex) {
      return {
        mode,
        selectedEndBlockId,
        hasRangeCandidates,
        currentBlockIndex,
        targetBlockIndex,
        spanCount: 0,
        tone: "danger",
        label: "结束点早于播放点",
        hint: "请改成当前音乐卡后面的卡片，否则自定义范围不会符合预期。",
      };
    }

    return {
      mode,
      selectedEndBlockId,
      hasRangeCandidates,
      currentBlockIndex,
      targetBlockIndex,
      spanCount,
      tone: spanCount >= 6 ? "good" : "soft",
      label: "自定义范围有效",
      hint: spanCount > 0 ? `会覆盖 ${spanCount} 张卡片，结束后按设置淡出。` : "结束点已选中。",
    };
  }

  function renderMusicRangeHealthChips(diagnostics = {}, options = {}) {
    const escape = getEscapeHtml(options);
    const tone = diagnostics?.tone || "soft";
    const labels = [
      diagnostics?.label || "范围待确认",
      diagnostics?.spanCount ? `覆盖 ${diagnostics.spanCount} 张` : "",
      diagnostics?.hint || "",
    ].filter(Boolean);

    return `
      <div class="music-range-health is-${escape(tone)}" data-music-range-health>
        ${labels.map((label) => `<span class="issue-tag">${escape(label)}</span>`).join("")}
      </div>
    `;
  }

  global.CanvasiaEditorMusicRangeScope = Object.freeze({
    buildMusicRangeDiagnostics,
    getMusicRangeBlockLabel,
    getMusicRangeCandidateBlocks,
    getMusicRangeEffectiveEndBlockId,
    getMusicRangeSummary,
    getMusicRangeSummaryFromValues,
    getMusicRangeTimeline,
    getMusicRangeTimelineFromValues,
    renderMusicRangeEndBlockOptions,
    renderMusicRangeHealthChips,
  });
})(window);
