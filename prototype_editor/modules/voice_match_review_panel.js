(function attachVoiceMatchReviewPanelTools(global) {
  function fallbackEscapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function fallbackSelectId(reviewKind, reviewIndex) {
    return `voiceMatchReview-${reviewKind}-${reviewIndex}`;
  }

  function fallbackDefaultTargetId(item, availableTargets = []) {
    const candidateIds = (Array.isArray(item?.candidates) ? item.candidates : [])
      .map((candidate) => candidate.assetId)
      .filter((assetId) => availableTargets.some((asset) => asset.id === assetId));
    return candidateIds[0] ?? availableTargets[0]?.id ?? "";
  }

  function getHelper(helpers, key, fallback) {
    return typeof helpers?.[key] === "function" ? helpers[key] : fallback;
  }

  function renderVoiceMatchReviewItem(item = {}, reviewKind = "unmatched", reviewIndex = 0, availableTargets = [], helpers = {}) {
    const escapeHtml = getHelper(helpers, "escapeHtml", fallbackEscapeHtml);
    const getDefaultVoiceMatchTargetId = getHelper(helpers, "getDefaultVoiceMatchTargetId", fallbackDefaultTargetId);
    const getVoiceMatchReviewSelectId = getHelper(helpers, "getVoiceMatchReviewSelectId", fallbackSelectId);
    const safeTargets = Array.isArray(availableTargets) ? availableTargets : [];
    const defaultTargetId = getDefaultVoiceMatchTargetId(item, safeTargets);
    const selectId = getVoiceMatchReviewSelectId(reviewKind, reviewIndex);

    return `
    <article class="asset-usage-item voice-match-review-item">
      <div class="asset-usage-copy">
        <strong>${escapeHtml(item.fileName)}</strong>
        <div class="detail-meta">${escapeHtml(item.reason || "这份文件仍需手动指定一个语音条目。")}</div>
        ${
          item.candidates?.length
            ? `<div class="scene-card-tags">${item.candidates
                .map(
                  (candidate) =>
                    `<span class="issue-tag warn-text">${escapeHtml(candidate.assetName)}</span>`
                )
                .join("")}</div>`
            : ""
        }
      </div>
      <div class="voice-match-review-controls">
        <label class="detail-row voice-match-review-picker" for="${escapeHtml(selectId)}">
          <span>手动绑到</span>
          <select id="${escapeHtml(selectId)}" class="voice-match-review-select">
            ${
              safeTargets.length > 0
                ? safeTargets
                    .map(
                      (asset) => `
                        <option value="${escapeHtml(asset.id)}" ${asset.id === defaultTargetId ? "selected" : ""}>
                          ${escapeHtml(asset.name)} · ${escapeHtml(asset.path)}
                        </option>
                      `
                    )
                    .join("")
                : `<option value="">当前没有待导入语音条目</option>`
            }
          </select>
        </label>
        <div class="script-entry-actions">
          <button
            type="button"
            class="toolbar-button toolbar-button-primary"
            data-action="bind-voice-match-review-file"
            data-review-kind="${escapeHtml(reviewKind)}"
            data-review-index="${escapeHtml(reviewIndex)}"
            ${safeTargets.length > 0 ? "" : "disabled"}
          >
            绑定到所选条目
          </button>
        </div>
      </div>
    </article>
  `;
  }

  function renderVoiceMatchReviewPanel(review = null, availableTargets = [], helpers = {}) {
    if (!review) {
      return "";
    }

    const ambiguousFiles = Array.isArray(review.ambiguousFiles) ? review.ambiguousFiles : [];
    const unmatchedFiles = Array.isArray(review.unmatchedFiles) ? review.unmatchedFiles : [];
    const unresolvedCount = unmatchedFiles.length + ambiguousFiles.length;
    if (unresolvedCount === 0) {
      return "";
    }

    const matchedCount = Number(review.matchedCount ?? 0);
    return `
    <article class="detail-card voice-match-review-panel">
      <div class="panel-heading">
        <div>
          <h3>这批语音还有 ${unresolvedCount} 个待补最后一步</h3>
          <span class="panel-note">自动匹配已处理可识别部分，下面这些可直接手动指定到对应语音占位条目。</span>
        </div>
        <span class="badge badge-soft">本次自动匹配成功 ${Number.isFinite(matchedCount) ? matchedCount : 0} 个</span>
      </div>
      <div class="detail-actions">
        <button class="toolbar-button" type="button" data-action="dismiss-voice-match-review">
          收起这次匹配结果
        </button>
      </div>
      ${
        ambiguousFiles.length
          ? `
            <div class="asset-usage-list">
              <strong>多个候选太像，系统先没敢乱绑</strong>
              ${ambiguousFiles
                .map((item, index) => renderVoiceMatchReviewItem(item, "ambiguous", index, availableTargets, helpers))
                .join("")}
            </div>
          `
          : ""
      }
      ${
        unmatchedFiles.length
          ? `
            <div class="asset-usage-list">
              <strong>没找到足够像的占位条目</strong>
              ${unmatchedFiles
                .map((item, index) => renderVoiceMatchReviewItem(item, "unmatched", index, availableTargets, helpers))
                .join("")}
            </div>
          `
          : ""
      }
    </article>
  `;
  }

  global.CanvasiaEditorVoiceMatchReviewPanel = Object.freeze({
    renderVoiceMatchReviewItem,
    renderVoiceMatchReviewPanel,
  });
})(typeof window !== "undefined" ? window : globalThis);
