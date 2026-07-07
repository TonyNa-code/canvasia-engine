(function attachCharacterPresentationPanelTools(global) {
  function fallbackEscapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function fallbackAssetSelectOptions(selectedValue, _types, emptyLabel = "暂不绑定") {
    const safeSelectedValue = String(selectedValue ?? "");
    return `<option value="${fallbackEscapeHtml(safeSelectedValue)}">${fallbackEscapeHtml(emptyLabel)}</option>`;
  }

  function fallbackStatCard(label, value) {
    return `
      <article class="stat-card">
        <span>${fallbackEscapeHtml(label)}</span>
        <strong>${fallbackEscapeHtml(value)}</strong>
      </article>
    `;
  }

  function fallbackExpressionBindingStatus(expression = {}) {
    const hasBinding = Boolean(
      (expression.layerAssetIds ?? []).length ||
        expression.live2dExpression ||
        expression.live2dMotion ||
        expression.model3dExpression ||
        expression.model3dAnimation
    );
    return hasBinding
      ? { tone: "good-text", label: "已绑定" }
      : { tone: "warn-text", label: "未绑定" };
  }

  function getHelper(helpers, key, fallback) {
    return typeof helpers?.[key] === "function" ? helpers[key] : fallback;
  }

  function renderCharacterPresentationPanel(model = {}, helpers = {}) {
    const character = model.character ?? {};
    const presentation = model.presentation ?? {};
    const live2d = presentation.live2d ?? {};
    const model3d = presentation.model3d ?? {};
    const status = model.status ?? { tone: "", label: "未配置", detail: "" };
    const readiness = model.readiness ?? {};
    const modeLabels = model.modeLabels ?? {};
    const boundAssetNames = model.boundAssetNames ?? "";
    const escapeHtml = getHelper(helpers, "escapeHtml", fallbackEscapeHtml);
    const buildGameUiAssetSelectOptions = getHelper(
      helpers,
      "buildGameUiAssetSelectOptions",
      fallbackAssetSelectOptions
    );
    const getCharacterPresentationModeLabel = getHelper(
      helpers,
      "getCharacterPresentationModeLabel",
      () => modeLabels[presentation.mode] ?? presentation.mode ?? "普通立绘"
    );

    return `
    <article class="detail-card character-presentation-panel">
      <div class="character-scene-panel-head">
        <div>
          <strong>高级角色表现</strong>
          <p class="helper-text">这里统一管理普通立绘、差分立绘、Live2D 和 3D 模型。现在先保存配置和兜底关系，后续渲染层会直接读取这套结构。</p>
        </div>
        <div class="scene-card-tags">
          <span class="issue-tag ${status.tone}">${escapeHtml(status.label)}</span>
          <span class="issue-tag">${escapeHtml(getCharacterPresentationModeLabel(character))}</span>
        </div>
      </div>
      <div class="playback-setting-grid dialog-config-grid">
        <label class="playback-setting">
          <span>表现类型</span>
          <select id="characterPresentationModeSelect">
            ${Object.entries(modeLabels)
              .map(
                ([mode, label]) => `
                  <option value="${escapeHtml(mode)}" ${presentation.mode === mode ? "selected" : ""}>${escapeHtml(label)}</option>
                `
              )
              .join("")}
          </select>
        </label>
        <label class="playback-setting">
          <span>兜底立绘</span>
          <select id="characterPresentationFallbackSpriteSelect">
            ${buildGameUiAssetSelectOptions(presentation.fallbackSpriteAssetId, ["sprite", "cg", "ui"], "沿用角色默认立绘")}
          </select>
        </label>
        <label class="playback-setting">
          <span>Live2D 模型入口</span>
          <select id="characterPresentationLive2dAssetSelect">
            ${buildGameUiAssetSelectOptions(live2d.modelAssetId, ["live2d"], "暂不绑定 Live2D")}
          </select>
        </label>
        <label class="playback-setting">
          <span>3D 模型入口</span>
          <select id="characterPresentationModel3dAssetSelect">
            ${buildGameUiAssetSelectOptions(model3d.modelAssetId, ["model3d"], "暂不绑定 3D 模型")}
          </select>
        </label>
        <label class="playback-setting">
          <span>Live2D 待机动作</span>
          <input id="characterPresentationLive2dIdleInput" type="text" value="${escapeHtml(live2d.idleMotion)}" placeholder="Idle / idle_01" />
        </label>
        <label class="playback-setting">
          <span>3D 待机动画</span>
          <input id="characterPresentationModel3dIdleInput" type="text" value="${escapeHtml(model3d.idleAnimation)}" placeholder="Idle / Stand / Breathing" />
        </label>
      </div>
      <div class="scene-card-tags">
        <label class="issue-tag">
          <input id="characterPresentationLive2dBlinkInput" type="checkbox" ${live2d.blink ? "checked" : ""} />
          自动眨眼
        </label>
        <label class="issue-tag">
          <input id="characterPresentationLive2dBreathInput" type="checkbox" ${live2d.breath ? "checked" : ""} />
          呼吸
        </label>
        <label class="issue-tag">
          <input id="characterPresentationLive2dLipSyncInput" type="checkbox" ${live2d.lipSync ? "checked" : ""} />
          口型同步
        </label>
        <label class="issue-tag">
          <input id="characterPresentationLive2dCursorInput" type="checkbox" ${live2d.cursorTracking ? "checked" : ""} />
          视线跟随
        </label>
      </div>
      <p class="helper-text">${escapeHtml(status.detail)}</p>
      <p class="helper-text">已纳入引用保护：${boundAssetNames ? escapeHtml(boundAssetNames) : "当前还没有额外模型素材绑定"}。</p>
      ${renderCharacterPresentationReadinessPanel(character, readiness, helpers)}
      ${renderCharacterExpressionBindingPanel(character, helpers)}
      <div class="detail-actions">
        <button
          type="button"
          class="toolbar-button toolbar-button-primary"
          data-action="save-character-presentation"
          data-character-id="${escapeHtml(character.id)}"
        >
          保存角色表现配置
        </button>
        <button type="button" class="toolbar-button" data-action="focus-asset-gap" data-asset-filter-mode="all" data-asset-type="live2d">
          去导入 Live2D
        </button>
        <button type="button" class="toolbar-button" data-action="focus-asset-gap" data-asset-filter-mode="all" data-asset-type="model3d">
          去导入 3D 模型
        </button>
      </div>
    </article>
  `;
  }

  function renderCharacterPresentationReadinessPanel(character = {}, readiness = {}, helpers = {}) {
    const escapeHtml = getHelper(helpers, "escapeHtml", fallbackEscapeHtml);
    const renderStatCard = getHelper(helpers, "renderStatCard", fallbackStatCard);
    const getCharacterPresentationModeLabel = getHelper(helpers, "getCharacterPresentationModeLabel", () => "普通立绘");
    const issueItems = Array.isArray(readiness.issues) && readiness.issues.length
      ? readiness.issues
      : [
          {
            tone: "good-text",
            title: "角色表现链路已经比较稳",
            detail: "模型入口、兜底素材和表情映射都已经达到当前阶段的可迁移标准。",
          },
        ];

    return `
    <div class="character-presentation-readiness">
      <div class="character-progress-card">
        <div class="character-progress-head">
          <strong>角色表现体检 ${readiness.score ?? 0}%</strong>
          <span class="${readiness.tone ?? ""}">${escapeHtml(getCharacterPresentationModeLabel(character))}</span>
        </div>
        <div class="character-progress-track">
          <span class="character-progress-fill" style="width:${Number(readiness.score ?? 0)}%;"></span>
        </div>
        <div class="character-progress-meta">
          <span>主素材：${escapeHtml(readiness.primaryHealth?.label ?? "未绑定")}</span>
          <span>兜底：${escapeHtml(readiness.fallbackHealth?.label ?? "未绑定")}</span>
          <span>映射：${Number(readiness.mappedExpressionCount ?? 0)}/${Number(readiness.expressionCount ?? 0) || 0}</span>
        </div>
      </div>
      <div class="summary-grid character-summary-grid">
        ${renderStatCard("体检分", `${readiness.score ?? 0}%`)}
        ${renderStatCard("主素材", readiness.primaryHealth?.ok ? "可用" : readiness.primaryHealth?.asset ? "待补文件" : "未绑定")}
        ${renderStatCard("兜底素材", readiness.fallbackHealth?.ok ? "安全" : readiness.fallbackHealth?.asset ? "待补文件" : "未绑定")}
        ${renderStatCard("表情映射", `${Number(readiness.mappedExpressionCount ?? 0)}/${Number(readiness.expressionCount ?? 0) || 0}`)}
      </div>
      <div class="character-presentation-issue-list">
        ${issueItems
          .map(
            (issue) => `
              <article class="character-presentation-issue">
                <span class="issue-tag ${issue.tone}">${escapeHtml(issue.title)}</span>
                <p class="helper-text">${escapeHtml(issue.detail)}</p>
              </article>
            `
          )
          .join("")}
      </div>
    </div>
  `;
  }

  function renderCharacterExpressionBindingPanel(character = {}, helpers = {}) {
    const escapeHtml = getHelper(helpers, "escapeHtml", fallbackEscapeHtml);
    const getCharacterExpressionBindingStatus = getHelper(
      helpers,
      "getCharacterExpressionBindingStatus",
      fallbackExpressionBindingStatus
    );
    const expressions = Array.isArray(character?.expressions) ? character.expressions : [];
    if (!expressions.length) {
      return `
      <div class="character-expression-binding-shell">
        <strong>表情映射</strong>
        <p class="helper-text">这个角色还没有表情条目。先保留兜底立绘配置，后续补表情后可以逐个绑定 Live2D 表情、动作或 3D 动画。</p>
      </div>
    `;
    }

    return `
    <div class="character-expression-binding-shell">
      <div class="character-expression-binding-head">
        <strong>表情级映射</strong>
        <span class="helper-text">可选项：不给新手增加负担，但高级项目可以逐个表情绑定 Live2D/3D 动作。</span>
      </div>
      <div class="character-expression-binding-grid">
        ${expressions
          .map((expression) => {
            const bindingStatus = getCharacterExpressionBindingStatus(expression);
            return `
              <article class="character-expression-binding-card" data-expression-id="${escapeHtml(expression.id)}">
                <div class="character-expression-binding-title">
                  <strong>${escapeHtml(expression.name || expression.id)}</strong>
                  <span class="issue-tag ${bindingStatus.tone}">${escapeHtml(bindingStatus.label)}</span>
                </div>
                <label class="playback-setting">
                  <span>差分图层素材 ID</span>
                  <input
                    class="characterExpressionLayerAssetsInput"
                    type="text"
                    value="${escapeHtml((expression.layerAssetIds ?? []).join(", "))}"
                    placeholder="sprite_hair, sprite_eye, sprite_mouth"
                  />
                </label>
                <div class="character-expression-binding-fields">
                  <label class="playback-setting">
                    <span>Live2D 表情</span>
                    <input class="characterExpressionLive2dExpressionInput" type="text" value="${escapeHtml(expression.live2dExpression ?? "")}" placeholder="smile.exp3.json / smile" />
                  </label>
                  <label class="playback-setting">
                    <span>Live2D 动作</span>
                    <input class="characterExpressionLive2dMotionInput" type="text" value="${escapeHtml(expression.live2dMotion ?? "")}" placeholder="tap_body.motion3.json / idle_01" />
                  </label>
                  <label class="playback-setting">
                    <span>3D 表情</span>
                    <input class="characterExpressionModel3dExpressionInput" type="text" value="${escapeHtml(expression.model3dExpression ?? "")}" placeholder="joy / blink / aa" />
                  </label>
                  <label class="playback-setting">
                    <span>3D 动画</span>
                    <input class="characterExpressionModel3dAnimationInput" type="text" value="${escapeHtml(expression.model3dAnimation ?? "")}" placeholder="Wave / IdleHappy / Talk" />
                  </label>
                </div>
              </article>
            `;
          })
          .join("")}
      </div>
    </div>
  `;
  }

  global.CanvasiaEditorCharacterPresentationPanel = Object.freeze({
    renderCharacterPresentationPanel,
    renderCharacterPresentationReadinessPanel,
    renderCharacterExpressionBindingPanel,
  });
})(typeof window !== "undefined" ? window : globalThis);
