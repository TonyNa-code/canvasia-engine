(function attachStoryBlockEditorTools(global) {
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

  function getRenderer(options, key, fallback = () => "") {
    return typeof options[key] === "function" ? options[key] : fallback;
  }

  function getEditableChoiceEffects(effectList, options = {}) {
    const reader = getRenderer(options, "getEditableChoiceEffects", (effects = []) => effects ?? []);
    const result = reader(effectList ?? []);
    return Array.isArray(result) ? result : [];
  }

  function renderLabelOptions(labelMap, selectedValue, options = {}) {
    const escape = getEscapeHtml(options);
    return Object.entries(labelMap ?? {})
      .map(
        ([value, label]) => `
                <option value="${escape(value)}" ${value === selectedValue ? "selected" : ""}>
                  ${escape(label)}
                </option>
              `
      )
      .join("");
  }

  function renderAssetOptions(assets, selectedAssetId, options = {}) {
    const escape = getEscapeHtml(options);
    return (assets ?? [])
      .map(
        (asset) => `
                <option value="${escape(asset.id ?? "")}" ${asset.id === selectedAssetId ? "selected" : ""}>
                  ${escape(asset.name ?? "")}
                </option>
              `
      )
      .join("");
  }

  function renderVideoVolumeOptions(labelMap, selectedVolume, options = {}) {
    const escape = getEscapeHtml(options);
    return Object.entries(labelMap ?? {})
      .map(
        ([value, label]) => `
                <option value="${escape(value)}" ${Number(value) === selectedVolume ? "selected" : ""}>
                  ${escape(label)}
                </option>
              `
      )
      .join("");
  }

  function renderSelectRow(id, label, labelMap, selectedValue, options = {}) {
    const escape = getEscapeHtml(options);
    return `
      <div class="detail-row">
        <label for="${escape(id)}">${escape(label)}</label>
        <select id="${escape(id)}">
          ${renderLabelOptions(labelMap, selectedValue, options)}
        </select>
      </div>
    `;
  }

  function renderTransitionDurationInput(block, options = {}) {
    const escape = getEscapeHtml(options);
    const getSafeTransitionDurationMs = getRenderer(options, "getSafeTransitionDurationMs", (value, fallback = 360) => {
      const number = Number.parseFloat(value ?? "");
      const safeFallback = Number.isFinite(Number(fallback)) ? Math.min(Math.max(Number(fallback), 0), 5000) : 360;
      return Math.round(Math.min(Math.max(Number.isFinite(number) ? number : safeFallback, 0), 5000));
    });
    const durationMs = getSafeTransitionDurationMs(block?.transitionDurationMs);

    return `
      <div class="detail-row">
        <label for="editorTransitionDurationMs">转场时长（毫秒）</label>
        <input
          id="editorTransitionDurationMs"
          type="number"
          min="0"
          max="5000"
          step="50"
          value="${escape(String(durationMs))}"
        />
        <p class="helper-text">0 是直接切换；数值越大，淡入、滑入或退场越慢。旧项目不填时会自动使用默认节奏。</p>
      </div>
    `;
  }

  function renderTextSpeedOverrideRow(block, options = {}) {
    const escape = getEscapeHtml(options);
    const labelMap = {
      follow: "跟随全局文字速度",
      ...(options.textSpeedLabels ?? {}),
    };
    const selectedValue = Object.hasOwn(options.textSpeedLabels ?? {}, block?.textSpeed)
      ? block.textSpeed
      : "follow";

    return `
      <div class="detail-row">
        <label for="editorTextSpeed">这句文字速度</label>
        <select id="editorTextSpeed">
          ${renderLabelOptions(labelMap, selectedValue, options)}
        </select>
        <p class="helper-text">用于单独控制这一句的打字机节奏。默认跟随试玩 / 玩家设置。</p>
      </div>
    `;
  }

  function renderSaveBlockActions() {
    return `
    <div class="detail-actions">
      <button class="toolbar-button toolbar-button-primary" data-action="save-block">保存这张卡片</button>
    </div>
  `;
  }

  function renderBlockManagementCard(scene, selectedIndex, options = {}) {
    const renderDetailRows = getRenderer(options, "renderDetailRows");
    const blockCount = scene?.blocks?.length ?? 0;
    const safeIndex = Number.isFinite(Number(selectedIndex)) ? Number(selectedIndex) : 0;

    return `
    <article class="editor-card">
      <h3>管理这张卡片</h3>
      <p>如果顺序不对，可以先上移、下移，确认无误后再继续编辑内容。</p>
      ${renderDetailRows([
        ["所在场景", scene?.name ?? "未选择"],
        ["当前顺序", `第 ${safeIndex + 1} 张 / 共 ${blockCount} 张`],
      ])}
      <div class="detail-actions">
        <button class="toolbar-button" data-action="move-block-up" ${safeIndex <= 0 ? "disabled" : ""}>
          上移一格
        </button>
        <button class="toolbar-button" data-action="duplicate-block">复制这张卡片</button>
        <button
          class="toolbar-button"
          data-action="move-block-down"
          ${safeIndex >= blockCount - 1 ? "disabled" : ""}
        >
          下移一格
        </button>
        <button class="toolbar-button toolbar-button-danger" data-action="delete-block">删除这张卡片</button>
      </div>
    </article>
  `;
  }

  function renderReadonlyBlockPanel(block, options = {}) {
    const renderDetailRows = getRenderer(options, "renderDetailRows");
    const buildBlockDetails = getRenderer(options, "buildBlockDetails", () => []);

    return `
    ${renderDetailRows(buildBlockDetails(block))}
    <article class="editor-card">
      <h3>高级兼容卡片</h3>
      <p>这张卡片会完整保留在项目数据和导出流程中。当前界面先显示结构详情，适合检查从旧版本或自定义扩展导入的高级内容。</p>
    </article>
  `;
  }

  function renderScreenShakeEditor(block, options = {}) {
    const getSafeShakeIntensity = getRenderer(options, "getSafeShakeIntensity", (value) => value ?? "medium");
    const getSafeEffectDuration = getRenderer(options, "getSafeEffectDuration", (value) => value ?? "medium");
    const intensity = getSafeShakeIntensity(block?.intensity);
    const duration = getSafeEffectDuration(block?.duration);

    return `
    <article class="editor-card">
      <h3>编辑屏幕震动</h3>
      <p>适合撞门、跌倒、心跳、爆点台词这类需要“震一下”来加强情绪的时刻。</p>
    </article>
    <div class="field-grid">
      ${renderSelectRow("editorShakeIntensity", "震动强度", options.shakeIntensityLabels, intensity, options)}
      ${renderSelectRow("editorShakeDuration", "持续多久", options.effectDurationLabels, duration, options)}
      <div class="helper-text">屏幕震动是一次性的演出卡片，只会影响当前这一步，不会一直抖下去。</div>
    </div>
    ${renderSaveBlockActions()}
  `;
  }

  function renderScreenFlashEditor(block, options = {}) {
    const getSafeFlashColor = getRenderer(options, "getSafeFlashColor", (value) => value ?? "white");
    const getSafeFlashIntensity = getRenderer(options, "getSafeFlashIntensity", (value) => value ?? "medium");
    const getSafeEffectDuration = getRenderer(options, "getSafeEffectDuration", (value) => value ?? "medium");
    const color = getSafeFlashColor(block?.color);
    const intensity = getSafeFlashIntensity(block?.intensity);
    const duration = getSafeEffectDuration(block?.duration);

    return `
    <article class="editor-card">
      <h3>编辑闪屏</h3>
      <p>适合回忆切入、强光、冲击、情绪爆点这类需要画面瞬间闪一下的过场演出。</p>
    </article>
    <div class="field-grid">
      ${renderSelectRow("editorFlashColor", "闪屏颜色", options.flashColorLabels, color, options)}
      ${renderSelectRow("editorFlashIntensity", "闪屏强度", options.flashIntensityLabels, intensity, options)}
      ${renderSelectRow("editorFlashDuration", "持续多久", options.effectDurationLabels, duration, options)}
      <div class="helper-text">闪屏也是一次性的演出卡片，适合穿插在关键台词和转场前后。</div>
    </div>
    ${renderSaveBlockActions()}
  `;
  }

  function renderScreenFadeEditor(block, options = {}) {
    const getSafeFadeAction = getRenderer(options, "getSafeFadeAction", (value) => value ?? "fade_out");
    const getSafeFadeColor = getRenderer(options, "getSafeFadeColor", (value) => value ?? "black");
    const getSafeEffectDuration = getRenderer(options, "getSafeEffectDuration", (value) => value ?? "medium");
    const action = getSafeFadeAction(block?.action);
    const color = getSafeFadeColor(block?.color);
    const duration = getSafeEffectDuration(block?.duration);

    return `
    <article class="editor-card">
      <h3>编辑黑场淡入淡出</h3>
      <p>适合章节切换、视角切换、告白前停顿、回忆开场这类需要慢慢暗下去或亮起来的过场。</p>
    </article>
    <div class="field-grid">
      ${renderSelectRow("editorFadeAction", "这张卡片要做什么", options.fadeActionLabels, action, options)}
      ${renderSelectRow("editorFadeColor", "淡到什么颜色", options.fadeColorLabels, color, options)}
      ${renderSelectRow("editorFadeDuration", "持续多久", options.effectDurationLabels, duration, options)}
      <div class="helper-text">需要做“先黑场，再切背景，再亮起”时，通常会按“淡出 -> 切背景 -> 淡入”的顺序摆卡片。</div>
    </div>
    ${renderSaveBlockActions()}
  `;
  }

  function renderCameraZoomEditor(block, options = {}) {
    const getSafeCameraZoomAction = getRenderer(options, "getSafeCameraZoomAction", (value) => value ?? "zoom_in");
    const getSafeCameraZoomStrength = getRenderer(options, "getSafeCameraZoomStrength", (value) => value ?? "medium");
    const getSafeCameraZoomFocus = getRenderer(options, "getSafeCameraZoomFocus", (value) => value ?? "center");
    const action = getSafeCameraZoomAction(block?.action);
    const strength = getSafeCameraZoomStrength(block?.strength);
    const focus = getSafeCameraZoomFocus(block?.focus);

    return `
    <article class="editor-card">
      <h3>编辑镜头推近拉远</h3>
      <p>适合心动特写、视线聚焦、危险逼近或突然拉远制造距离感的时刻。</p>
    </article>
    <div class="field-grid">
      ${renderSelectRow("editorCameraZoomAction", "镜头动作", options.cameraZoomActionLabels, action, options)}
      ${renderSelectRow("editorCameraZoomStrength", "镜头强度", options.cameraZoomStrengthLabels, strength, options)}
      ${renderSelectRow("editorCameraZoomFocus", "重点看哪里", options.cameraZoomFocusLabels, focus, options)}
      <div class="helper-text">镜头缩放会持续保留，直到后面再插一张新的镜头卡片，或者选“恢复正常”为止。</div>
    </div>
    ${renderSaveBlockActions()}
  `;
  }

  function renderCameraPanEditor(block, options = {}) {
    const getSafeCameraPanTarget = getRenderer(options, "getSafeCameraPanTarget", (value) => value ?? "center");
    const getSafeCameraPanStrength = getRenderer(options, "getSafeCameraPanStrength", (value) => value ?? "medium");
    const target = getSafeCameraPanTarget(block?.target);
    const strength = getSafeCameraPanStrength(block?.strength);

    return `
    <article class="editor-card">
      <h3>编辑镜头平移</h3>
      <p>适合视线移动、角色从一侧出场、慢慢把注意力移到另一边，或者拉回画面中心。</p>
    </article>
    <div class="field-grid">
      ${renderSelectRow("editorCameraPanTarget", "镜头看向哪里", options.cameraPanTargetLabels, target, options)}
      ${renderSelectRow("editorCameraPanStrength", "平移幅度", options.cameraPanStrengthLabels, strength, options)}
      <div class="helper-text">镜头平移会持续保留，直到后面再插一张新的平移卡片，或者选“回到中间”为止。</div>
    </div>
    ${renderSaveBlockActions()}
  `;
  }

  function renderColorGradeNumberInput(id, label, key, grade, options = {}) {
    const escape = getEscapeHtml(options);
    const [minimum, maximum] = options.screenColorGradeLimits?.[key] ?? [0, 100];
    const defaultValue = options.screenColorGradeDefaults?.[key] ?? 0;
    const hint = options.hint ?? `范围 ${minimum} 到 ${maximum}，默认 ${defaultValue}`;

    return `
    <div class="detail-row">
      <label for="${escape(id)}">${escape(label)}</label>
      <input
        id="${escape(id)}"
        type="number"
        min="${escape(String(minimum))}"
        max="${escape(String(maximum))}"
        step="1"
        value="${escape(String(grade?.[key] ?? defaultValue))}"
        aria-describedby="${escape(id)}Hint"
      />
      <div id="${escape(id)}Hint" class="helper-text">${escape(hint)}</div>
    </div>
  `;
  }

  function renderScreenFilterEditor(block, options = {}) {
    const getSafeScreenFilterAction = getRenderer(options, "getSafeScreenFilterAction", (value) => value ?? "apply");
    const getSafeScreenFilterPreset = getRenderer(options, "getSafeScreenFilterPreset", (value) => value ?? "memory");
    const getSafeScreenFilterStrength = getRenderer(options, "getSafeScreenFilterStrength", (value) => value ?? "medium");
    const getSafeScreenColorGrade = getRenderer(options, "getSafeScreenColorGrade", (value) => value ?? {});
    const action = getSafeScreenFilterAction(block?.action);
    const preset = getSafeScreenFilterPreset(block?.preset);
    const strength = getSafeScreenFilterStrength(block?.strength);
    const grade = getSafeScreenColorGrade(block?.grade);
    const colorGradeOptions = {
      ...options,
      screenColorGradeDefaults: options.screenColorGradeDefaults,
      screenColorGradeLimits: options.screenColorGradeLimits,
    };

    return `
    <article class="editor-card">
      <h3>编辑画面调色</h3>
      <p>先选一个气氛预设，再像调色板一样微调亮度、对比度、色相、冷暖和暗角。</p>
    </article>
    <div class="field-grid">
      ${renderSelectRow("editorScreenFilterAction", "这张卡片要做什么", options.screenFilterActionLabels, action, options)}
      ${renderSelectRow("editorScreenFilterPreset", "滤镜风格", options.screenFilterPresetLabels, preset, options)}
      ${renderSelectRow("editorScreenFilterStrength", "滤镜强度", options.screenFilterStrengthLabels, strength, options)}
      <div class="helper-text">滤镜会持续保留，直到后面插入一张“关闭滤镜”的卡片为止。</div>
    </div>
    <article class="editor-card">
      <h3>基础调色板</h3>
      <p>默认值不会改变画面。小白可以只改预设，高级用户可以用这些参数做统一色调。</p>
    </article>
    <div class="field-grid">
      ${renderColorGradeNumberInput("editorColorGradeBrightness", "亮度", "brightness", grade, colorGradeOptions)}
      ${renderColorGradeNumberInput("editorColorGradeContrast", "对比度", "contrast", grade, colorGradeOptions)}
      ${renderColorGradeNumberInput("editorColorGradeSaturation", "饱和度", "saturation", grade, colorGradeOptions)}
      ${renderColorGradeNumberInput("editorColorGradeHue", "色相旋转", "hue", grade, { ...colorGradeOptions, hint: "负数偏向前一段色相，正数偏向后一段色相，默认 0" })}
      ${renderColorGradeNumberInput("editorColorGradeTemperature", "冷暖色温", "temperature", grade, { ...colorGradeOptions, hint: "负数更冷，正数更暖，默认 0" })}
      ${renderColorGradeNumberInput("editorColorGradeVignette", "暗角强度", "vignette", grade, { ...colorGradeOptions, hint: "0 是关闭，100 是最明显" })}
    </div>
    ${renderSaveBlockActions()}
  `;
  }

  function renderDepthBlurEditor(block, options = {}) {
    const getSafeDepthBlurAction = getRenderer(options, "getSafeDepthBlurAction", (value) => value ?? "apply");
    const getSafeDepthBlurFocus = getRenderer(options, "getSafeDepthBlurFocus", (value) => value ?? "center");
    const getSafeDepthBlurStrength = getRenderer(options, "getSafeDepthBlurStrength", (value) => value ?? "medium");
    const action = getSafeDepthBlurAction(block?.action);
    const focus = getSafeDepthBlurFocus(block?.focus);
    const strength = getSafeDepthBlurStrength(block?.strength);

    return `
    <article class="editor-card">
      <h3>编辑景深模糊</h3>
      <p>适合回忆、心动特写、旁人退到背景、镜头只想强调某一位角色的时候。</p>
    </article>
    <div class="field-grid">
      ${renderSelectRow("editorDepthBlurAction", "这张卡片要做什么", options.depthBlurActionLabels, action, options)}
      ${renderSelectRow("editorDepthBlurFocus", "重点突出哪里", options.depthBlurFocusLabels, focus, options)}
      ${renderSelectRow("editorDepthBlurStrength", "模糊强度", options.depthBlurStrengthLabels, strength, options)}
      <div class="helper-text">景深会持续保留，直到你再插一张“关闭景深”的卡片为止。</div>
    </div>
    ${renderSaveBlockActions()}
  `;
  }

  function renderReadableTextQualityTools(text, label, options = {}) {
    const escape = getEscapeHtml(options);
    const getReadableTextToolState = getRenderer(options, "getReadableTextToolState", () => ({
      canSplit: false,
      isLong: false,
      metrics: {},
      statusText: "正常",
      toneClass: "good-text",
    }));
    const buildReadableTextSummary = getRenderer(options, "buildReadableTextSummary", () => "");
    const toolState = getReadableTextToolState(text);

    return `
    <div class="readable-text-tools ${toolState.isLong ? "is-warning" : ""}" data-readable-text-tools>
      <div>
        <strong>${escape(label)}可读性</strong>
        <p class="helper-text" data-readable-summary>
          ${escape(buildReadableTextSummary(toolState.metrics))}
        </p>
      </div>
      <span class="issue-tag ${escape(toolState.toneClass)}" data-readable-status>${escape(toolState.statusText)}</span>
      <button
        type="button"
        class="toolbar-button"
        data-action="split-readable-block"
        data-readable-split-button
        ${toolState.canSplit ? "" : "disabled"}
      >
        拆成长文本卡片
      </button>
    </div>
  `;
  }

  function getCollectionEntry(collection, key) {
    if (!key || !collection) {
      return null;
    }
    if (typeof collection.get === "function") {
      return collection.get(key) ?? null;
    }
    return collection[key] ?? null;
  }

  function renderDialogueEditor(block, options = {}) {
    const escape = getEscapeHtml(options);
    const getSafeCharacterId = getRenderer(options, "getSafeCharacterId", (characterId) => characterId ?? "");
    const getSafeExpressionId = getRenderer(options, "getSafeExpressionId", (_characterId, expressionId) => expressionId ?? "");
    const renderExpressionOptions = getRenderer(options, "renderExpressionOptions");
    const renderReadableTextTools = getRenderer(options, "renderReadableTextQualityTools", renderReadableTextQualityTools);
    const characters = Array.isArray(options.characters) ? options.characters : [];
    const voiceAssets = Array.isArray(options.voiceAssets) ? options.voiceAssets : [];
    const speakerId = getSafeCharacterId(block?.speakerId);
    const expressionId = getSafeExpressionId(speakerId, block?.expressionId);
    const boundVoiceAsset = block?.voiceAssetId ? getCollectionEntry(options.assetsById, block.voiceAssetId) : null;
    const blockId = String(block?.id ?? "");
    const voiceAssetId = String(block?.voiceAssetId ?? "");
    const voiceHelperCard = voiceAssetId
      ? `
        <article class="editor-card">
          <h3>这句已经绑好语音</h3>
          <p>当前绑定的是“${escape(boundVoiceAsset?.name ?? voiceAssetId)}”。如果还没上传真实音频，后面去素材页替换这个语音条目就行。</p>
        </article>
      `
      : `
        <article class="editor-card">
          <h3>这句还没有语音</h3>
          <p>如需先搭起配音工作流，可直接生成一个语音占位条目；系统会自动绑定到这句台词，后续再上传真实文件即可。</p>
          <div class="detail-actions">
            <button
              class="toolbar-button"
              data-action="create-voice-placeholder"
              data-scene-id="${escape(options.selectedSceneId ?? "")}"
              data-block-id="${escape(blockId)}"
            >
              一键生成语音条目并绑定
            </button>
          </div>
        </article>
      `;

    return `
    <article class="editor-card">
      <h3>编辑这句台词</h3>
      <p>改完以后点“保存这张卡片”，内容就会写回示例项目 JSON。</p>
    </article>
    ${voiceHelperCard}
    <div class="field-grid">
      <div class="detail-row">
        <label for="editorSpeakerId">说话角色</label>
        <select id="editorSpeakerId">
          ${characters
            .map(
              (character) => `
                <option value="${escape(character.id ?? "")}" ${character.id === speakerId ? "selected" : ""}>
                  ${escape(character.displayName ?? character.name ?? "")}
                </option>
              `
            )
            .join("")}
        </select>
      </div>
      <div class="detail-row">
        <label for="editorExpressionId">角色表情</label>
        <select id="editorExpressionId">
          ${renderExpressionOptions(speakerId, expressionId)}
        </select>
      </div>
      <div class="detail-row">
        <label for="editorVoiceAssetId">绑定语音</label>
        <select id="editorVoiceAssetId">
          <option value="">暂时不绑定语音</option>
          ${voiceAssets
            .map(
              (asset) => `
                <option value="${escape(asset.id ?? "")}" ${asset.id === voiceAssetId ? "selected" : ""}>
                  ${escape(asset.name ?? "")}
                </option>
              `
            )
            .join("")}
        </select>
      </div>
      <div class="detail-row">
        <label for="editorVoiceVolume">这句语音音量（%）</label>
        <input id="editorVoiceVolume" type="number" min="0" max="100" step="1" value="${escape(
          String(block?.voiceVolume ?? 100)
        )}" />
        <p class="helper-text">用于单独控制这一句配音的强弱，会和玩家自己的语音音量设置叠加。</p>
      </div>
      <div class="detail-row">
        <label for="editorDialogueText">台词内容</label>
        <textarea id="editorDialogueText">${escape(block?.text ?? "")}</textarea>
        ${renderReadableTextTools(block?.text, "台词")}
      </div>
      ${renderTextSpeedOverrideRow(block, options)}
    </div>
    ${renderSaveBlockActions()}
  `;
  }

  function renderChoiceEditor(block, options = {}) {
    const createDefaultChoiceOptions = getRenderer(options, "createDefaultChoiceOptions", () => []);
    const renderDetailRows = getRenderer(options, "renderDetailRows");
    const renderChoiceCountQualityTools = getRenderer(options, "renderChoiceCountQualityTools");
    const renderChoiceOptionEditorRow = getRenderer(options, "renderChoiceOptionEditorRow");
    const choiceOptions = Array.isArray(block?.options) && block.options.length
      ? block.options
      : createDefaultChoiceOptions(block?.id);
    const optionMarkup = choiceOptions.map(
      (option, index) => renderChoiceOptionEditorRow(option, index, choiceOptions.length)
    );

    return `
    <article class="editor-card">
      <h3>编辑这个选项分支</h3>
      <p>每个选项都能设置文案、跳转场景，还能追加好感度变化、开关变化和路线记录这类附加效果。</p>
    </article>
    ${renderDetailRows([
      ["卡片类型", options.blockLabels?.[block?.type] ?? block?.type],
      ["当前选项数", choiceOptions.length],
    ])}
    ${renderChoiceCountQualityTools(choiceOptions.length)}
    <div id="choiceOptionsEditor" class="option-editor-list">
      ${optionMarkup.join("")}
    </div>
    <div class="detail-actions">
      <button class="toolbar-button" data-action="add-choice-option">再加一个选项</button>
      <button class="toolbar-button toolbar-button-primary" data-action="save-block">保存这张卡片</button>
    </div>
  `;
  }

  function renderNarrationEditor(block, options = {}) {
    const escape = getEscapeHtml(options);
    const renderReadableTextTools = getRenderer(options, "renderReadableTextQualityTools", renderReadableTextQualityTools);
    const voiceAssets = Array.isArray(options.voiceAssets) ? options.voiceAssets : [];
    const voiceAssetId = String(block?.voiceAssetId ?? "");
    const boundVoiceAsset = voiceAssetId ? getCollectionEntry(options.assetsById, voiceAssetId) : null;

    return `
    <article class="editor-card">
      <h3>编辑这段旁白</h3>
      <p>旁白不会显示角色名，适合推进气氛、内心独白或 VO 叙述；需要时也可以绑定语音。</p>
    </article>
    <div class="field-grid">
      <div class="detail-row">
        <label for="editorNarrationText">旁白内容</label>
        <textarea id="editorNarrationText">${escape(block?.text ?? "")}</textarea>
        ${renderReadableTextTools(block?.text, "旁白")}
      </div>
      <div class="detail-row">
        <label for="editorNarrationVoiceAssetId">旁白语音</label>
        <select id="editorNarrationVoiceAssetId">
          <option value="">暂时不绑定语音</option>
          ${voiceAssets
            .map(
              (asset) => `
                <option value="${escape(asset.id ?? "")}" ${asset.id === voiceAssetId ? "selected" : ""}>
                  ${escape(asset.name ?? "")}
                </option>
              `
            )
            .join("")}
        </select>
        <p class="helper-text">
          ${voiceAssetId ? `当前绑定的是“${escape(boundVoiceAsset?.name ?? voiceAssetId)}”。` : "如果想做旁白朗读、内心独白或剧情 VO，可以在这里绑定语音。"}
        </p>
      </div>
      <div class="detail-row">
        <label for="editorNarrationVoiceVolume">旁白语音音量（%）</label>
        <input id="editorNarrationVoiceVolume" type="number" min="0" max="100" step="1" value="${escape(
          String(block?.voiceVolume ?? 100)
        )}" />
        <p class="helper-text">用于单独控制这段旁白语音的强弱，会和玩家自己的语音音量设置叠加。</p>
      </div>
      ${renderTextSpeedOverrideRow(block, options)}
    </div>
    ${renderSaveBlockActions()}
  `;
  }

  function renderChoiceCountQualityTools(optionCount, options = {}) {
    const escape = getEscapeHtml(options);
    const buildChoiceCountSummary = getRenderer(options, "buildChoiceCountSummary", (count) => `当前 ${count} 个选项`);
    const safeCount = Math.max(Number(optionCount) || 0, 0);
    const isCrowded = safeCount > Number(options.choiceManyOptionsThreshold ?? 4);

    return `
    <div class="choice-count-tools ${isCrowded ? "is-warning" : ""}" data-choice-count-tools>
      <div>
        <strong>选项按钮区</strong>
        <p class="helper-text" data-choice-count-summary>${escape(buildChoiceCountSummary(safeCount))}</p>
      </div>
      <span class="issue-tag ${isCrowded ? "warn-text" : "good-text"}" data-choice-count-status>
        ${isCrowded ? "按钮偏多" : "数量舒适"}
      </span>
    </div>
  `;
  }

  function renderBackgroundAssetOptions(assets, selectedAssetId, options = {}) {
    const escape = getEscapeHtml(options);
    return (assets ?? [])
      .map(
        (asset) => `
                <option value="${escape(asset.id ?? "")}" ${asset.id === selectedAssetId ? "selected" : ""}>
                  ${escape(asset.name ?? "")}${asset.type === "scene3d" ? " · 3D 场景" : ""}
                </option>
              `
      )
      .join("");
  }

  function renderBackgroundEditor(block, options = {}) {
    const escape = getEscapeHtml(options);
    const getSafeTransition = getRenderer(options, "getSafeTransition", (value) => value ?? "fade");
    const getSafeScene3dPreviewConfig = getRenderer(options, "getSafeScene3dPreviewConfig", () => ({
      interactionEnabled: true,
      pitch: 35,
      yaw: 0,
      zoom: 1,
    }));
    const renderTransitionOptions = getRenderer(options, "renderTransitionOptions");
    const transition = getSafeTransition(block?.transition);
    const scene3dPreview = getSafeScene3dPreviewConfig(block?.scene3dPreview);

    return `
    <article class="editor-card">
      <h3>编辑背景切换</h3>
      <p>这里决定这一张卡片出现时，画面切到哪张背景；也可以选择 3D 场景资产，原生 Runtime 会进入交互预览桥。</p>
    </article>
    <div class="field-grid">
      <div class="detail-row">
        <label for="editorBackgroundAssetId">背景 / 3D 场景</label>
        <select id="editorBackgroundAssetId">
          ${renderBackgroundAssetOptions(options.backgroundAssets, block?.assetId, options)}
        </select>
      </div>
      <div class="detail-row">
        <label for="editorTransition">切换方式</label>
        <select id="editorTransition">
          ${renderTransitionOptions(transition, { basic: true })}
        </select>
      </div>
      ${renderTransitionDurationInput(block, options)}
      <div class="detail-row">
        <label>3D 场景默认视角</label>
        <div class="field-grid compact-grid">
          <label>
            <span>Yaw 旋转</span>
            <input id="editorScene3dYaw" type="number" min="0" max="359" step="1" value="${escape(String(scene3dPreview.yaw))}" />
          </label>
          <label>
            <span>Pitch 俯仰</span>
            <input id="editorScene3dPitch" type="number" min="12" max="72" step="1" value="${escape(String(scene3dPreview.pitch))}" />
          </label>
          <label>
            <span>Zoom 缩放</span>
            <input id="editorScene3dZoom" type="number" min="0.55" max="1.9" step="0.05" value="${escape(String(scene3dPreview.zoom))}" />
          </label>
        </div>
        <p class="helper-text">当这里选择的是 3D 场景素材时，原生 Runtime 会用这组参数初始化空间预览桥。</p>
      </div>
      <label class="toggle-row">
        <input id="editorScene3dInteractionEnabled" type="checkbox" ${scene3dPreview.interactionEnabled ? "checked" : ""} />
        <span>允许玩家在原生 Runtime 中用方向键和 +/- 微调 3D 场景视角</span>
      </label>
    </div>
    ${renderSaveBlockActions()}
  `;
  }

  function renderCharacterShowEditor(block, options = {}) {
    const getSafeCharacterId = getRenderer(options, "getSafeCharacterId", (characterId) => characterId ?? "");
    const getSafeExpressionId = getRenderer(options, "getSafeExpressionId", (_characterId, expressionId) => expressionId ?? "");
    const getSafePosition = getRenderer(options, "getSafePosition", (position) => position ?? "center");
    const getSafeTransition = getRenderer(options, "getSafeTransition", (transition) => transition ?? "fade");
    const getCharacterStageFromBlock = getRenderer(options, "getCharacterStageFromBlock", () => ({}));
    const renderCharacterOptions = getRenderer(options, "renderCharacterOptions");
    const renderExpressionOptions = getRenderer(options, "renderExpressionOptions");
    const renderPositionOptions = getRenderer(options, "renderPositionOptions");
    const renderTransitionOptions = getRenderer(options, "renderTransitionOptions");
    const renderCharacterStageControls = getRenderer(options, "renderCharacterStageControls");
    const characterId = getSafeCharacterId(block?.characterId);
    const expressionId = getSafeExpressionId(characterId, block?.expressionId);
    const position = getSafePosition(block?.position);
    const transition = getSafeTransition(block?.transition);
    const stage = getCharacterStageFromBlock(block);

    return `
    <article class="editor-card">
      <h3>编辑角色出场</h3>
      <p>这里决定是谁出场、用什么表情、站在画面哪里，以及如何出现。需要更细的舞台调度时，可以继续微调立绘位置、大小和层级。</p>
    </article>
    <div class="field-grid">
      <div class="detail-row">
        <label for="editorCharacterId">显示哪个角色</label>
        <select id="editorCharacterId">
          ${renderCharacterOptions(characterId)}
        </select>
      </div>
      <div class="detail-row">
        <label for="editorExpressionId">角色表情</label>
        <select id="editorExpressionId">
          ${renderExpressionOptions(characterId, expressionId)}
        </select>
      </div>
      <div class="detail-row">
        <label for="editorCharacterPosition">显示位置</label>
        <select id="editorCharacterPosition">
          ${renderPositionOptions(position)}
        </select>
      </div>
      <div class="detail-row">
        <label for="editorTransition">出场方式</label>
        <select id="editorTransition">
          ${renderTransitionOptions(transition)}
        </select>
      </div>
      ${renderTransitionDurationInput(block, options)}
      ${renderCharacterStageControls(stage, { position })}
    </div>
    ${renderSaveBlockActions()}
  `;
  }

  function renderCharacterHideEditor(block, options = {}) {
    const getSafeCharacterId = getRenderer(options, "getSafeCharacterId", (characterId) => characterId ?? "");
    const getSafeTransition = getRenderer(options, "getSafeTransition", (transition) => transition ?? "fade");
    const renderCharacterOptions = getRenderer(options, "renderCharacterOptions");
    const renderTransitionOptions = getRenderer(options, "renderTransitionOptions");
    const characterId = getSafeCharacterId(block?.characterId);
    const transition = getSafeTransition(block?.transition);

    return `
    <article class="editor-card">
      <h3>编辑角色退场</h3>
      <p>这里决定哪位角色离开画面，以及退场方式。</p>
    </article>
    <div class="field-grid">
      <div class="detail-row">
        <label for="editorCharacterId">隐藏哪个角色</label>
        <select id="editorCharacterId">
          ${renderCharacterOptions(characterId)}
        </select>
      </div>
      <div class="detail-row">
        <label for="editorTransition">退场方式</label>
        <select id="editorTransition">
          ${renderTransitionOptions(transition)}
        </select>
      </div>
      ${renderTransitionDurationInput(block, options)}
    </div>
    ${renderSaveBlockActions()}
  `;
  }

  function renderMusicPlayEditor(block, options = {}) {
    const escape = getEscapeHtml(options);
    const getSafeAssetIdByType = getRenderer(options, "getSafeAssetIdByType", (_type, assetId) => assetId ?? "");
    const getSafeMusicEndMode = getRenderer(options, "getSafeMusicEndMode", (mode) => mode ?? "until_next_music");
    const getMusicRangeSummary = getRenderer(
      options,
      "getMusicRangeSummary",
      () => "这首 BGM 会按播放范围设置自动覆盖剧情。"
    );
    const getMusicRangeTimeline = getRenderer(options, "getMusicRangeTimeline", () => ({
      startLabel: "当前音乐卡",
      modeLabel: "自动范围",
      endLabel: "后续剧情",
      countLabel: "按设置覆盖",
    }));
    const renderMusicEndModeOptions = getRenderer(options, "renderMusicEndModeOptions");
    const renderMusicRangeEndBlockOptions = getRenderer(options, "renderMusicRangeEndBlockOptions");
    const assetId = getSafeAssetIdByType("bgm", block?.assetId);
    const endMode = getSafeMusicEndMode(block?.endMode);
    const hasRangeCandidates = Boolean(options.hasRangeCandidates);
    const isCustomRange = endMode === "after_block";
    const rangeTimeline = getMusicRangeTimeline(block);

    return `
    <article class="editor-card">
      <h3>编辑背景音乐</h3>
      <p>这里决定播哪首 BGM、是否循环、淡入多久，以及这首歌覆盖哪一段剧情。</p>
    </article>
    <div class="field-grid">
      <div class="detail-row">
        <label for="editorMusicAssetId">音乐素材</label>
        <select id="editorMusicAssetId">
          ${renderAssetOptions(options.musicAssets, assetId, options)}
        </select>
      </div>
      <div class="detail-row">
        <label for="editorMusicLoop">是否循环</label>
        <select id="editorMusicLoop">
          <option value="true" ${block?.loop !== false ? "selected" : ""}>循环播放</option>
          <option value="false" ${block?.loop === false ? "selected" : ""}>只播放一次</option>
        </select>
      </div>
      <div class="detail-row">
        <label for="editorMusicVolume">本段音量（%）</label>
        <input id="editorMusicVolume" type="number" min="0" max="100" step="1" value="${escape(
          String(block?.volume ?? 100)
        )}" />
        <p class="helper-text">这里只控制这张音乐卡的混音倍率，会和玩家自己的 BGM 音量设置叠加。</p>
      </div>
      <div class="detail-row">
        <label for="editorMusicEndMode">播放范围</label>
        <select id="editorMusicEndMode">
          ${renderMusicEndModeOptions(endMode)}
        </select>
        <p class="helper-text">可以让这首 BGM 自动覆盖一段文本，而不是只能机械地靠下一张音乐卡切换。</p>
      </div>
      <div class="detail-row">
        <label for="editorMusicEndBlockId">范围结束卡片</label>
        <select id="editorMusicEndBlockId" data-has-range-candidates="${hasRangeCandidates ? "true" : "false"}" ${
          hasRangeCandidates && isCustomRange ? "" : "disabled"
        }>
          ${renderMusicRangeEndBlockOptions(block)}
        </select>
        <p class="helper-text">当播放范围选“播到指定卡片后”时，会在玩家看完这张卡片后自动淡出停止。</p>
      </div>
      <div class="music-range-preview" data-music-range-preview>
        <strong>当前覆盖范围</strong>
        <div class="music-range-timeline" aria-label="BGM 覆盖范围时间轴">
          <span data-music-range-start>${escape(rangeTimeline.startLabel)}</span>
          <i aria-hidden="true"></i>
          <span data-music-range-mode>${escape(rangeTimeline.modeLabel)}</span>
          <i aria-hidden="true"></i>
          <span data-music-range-end>${escape(rangeTimeline.endLabel)}</span>
          <em data-music-range-count>${escape(rangeTimeline.countLabel)}</em>
        </div>
        <span>${escape(getMusicRangeSummary(block))}</span>
      </div>
      <div class="detail-row">
        <label for="editorFadeInMs">淡入时间（毫秒）</label>
        <input id="editorFadeInMs" type="number" min="0" step="100" value="${escape(
          String(block?.fadeInMs ?? 0)
        )}" />
      </div>
      <div class="detail-row">
        <label for="editorMusicRangeFadeOutMs">范围结束淡出（毫秒）</label>
        <input id="editorMusicRangeFadeOutMs" type="number" min="0" step="100" value="${escape(
          String(block?.fadeOutMs ?? 600)
        )}" />
      </div>
    </div>
    ${renderSaveBlockActions()}
  `;
  }

  function renderMusicStopEditor(block, options = {}) {
    const escape = getEscapeHtml(options);

    return `
    <article class="editor-card">
      <h3>编辑停止音乐</h3>
      <p>这里决定当前 BGM 什么时候停，以及淡出多久。</p>
    </article>
    <div class="field-grid">
      <div class="detail-row">
        <label for="editorFadeOutMs">淡出时间（毫秒）</label>
        <input id="editorFadeOutMs" type="number" min="0" step="100" value="${escape(
          String(block?.fadeOutMs ?? 0)
        )}" />
      </div>
    </div>
    ${renderSaveBlockActions()}
  `;
  }

  function renderSfxPlayEditor(block, options = {}) {
    const escape = getEscapeHtml(options);
    const getSafeAssetIdByType = getRenderer(options, "getSafeAssetIdByType", (_type, assetId) => assetId ?? "");
    const assetId = getSafeAssetIdByType("sfx", block?.assetId);

    return `
    <article class="editor-card">
      <h3>编辑音效播放</h3>
      <p>这里决定当前卡片触发时播放哪一个音效。</p>
    </article>
    <div class="field-grid">
      <div class="detail-row">
        <label for="editorSfxAssetId">音效素材</label>
        <select id="editorSfxAssetId">
          ${renderAssetOptions(options.sfxAssets, assetId, options)}
        </select>
      </div>
      <div class="detail-row">
        <label for="editorSfxVolume">本次音效音量（%）</label>
        <input id="editorSfxVolume" type="number" min="0" max="100" step="1" value="${escape(
          String(block?.volume ?? 100)
        )}" />
        <p class="helper-text">用于调整这一声门铃、脚步、心跳或爆发音效的存在感，会和玩家音效音量叠加。</p>
      </div>
    </div>
    ${renderSaveBlockActions()}
  `;
  }

  function renderVideoPlayEditor(block, options = {}) {
    const escape = getEscapeHtml(options);
    const getSafeAssetIdByType = getRenderer(options, "getSafeAssetIdByType", (_type, assetId) => assetId ?? "");
    const getSafeNonNegativeNumber = getRenderer(options, "getSafeNonNegativeNumber", (value, fallback = 0) => {
      const parsed = Number.parseFloat(value ?? "");
      return Number.isFinite(parsed) && parsed >= 0 ? parsed : fallback;
    });
    const getSafeVideoVolume = getRenderer(options, "getSafeVideoVolume", (value) => Number(value ?? 100));
    const getSafeVideoFit = getRenderer(options, "getSafeVideoFit", (value) => value ?? "contain");
    const assetId = getSafeAssetIdByType("video", block?.assetId);
    const startTimeSeconds = getSafeNonNegativeNumber(block?.startTimeSeconds, 0);
    const endTimeSeconds = getSafeNonNegativeNumber(block?.endTimeSeconds, 0);
    const volume = getSafeVideoVolume(block?.volume);
    const fit = getSafeVideoFit(block?.fit);

    return `
    <article class="editor-card">
      <h3>编辑视频播放</h3>
      <p>适合 OP、ED、PV、过场动画。这里也提供最基础的裁段能力：设置开始秒数和结束秒数，就能只播放素材中的一小段。</p>
    </article>
    <div class="field-grid">
      <div class="detail-row">
        <label for="editorVideoAssetId">视频素材</label>
        <select id="editorVideoAssetId">
          <option value="">暂时不选择视频</option>
          ${renderAssetOptions(options.videoAssets, assetId, options)}
        </select>
      </div>
      <div class="detail-row">
        <label for="editorVideoTitle">播放标题</label>
        <input
          id="editorVideoTitle"
          type="text"
          maxlength="48"
          value="${escape(block?.title ?? "")}"
          placeholder="例如：Opening Movie / Ending Movie"
        />
      </div>
      <div class="detail-row">
        <label for="editorVideoFit">画面适配</label>
        <select id="editorVideoFit">
          ${renderLabelOptions(options.videoFitLabels, fit, options)}
        </select>
      </div>
      <div class="detail-row">
        <label for="editorVideoVolume">视频音量</label>
        <select id="editorVideoVolume">
          ${renderVideoVolumeOptions(options.videoVolumeLabels, volume, options)}
        </select>
      </div>
      <div class="detail-row">
        <label for="editorVideoStartTime">从第几秒开始</label>
        <input id="editorVideoStartTime" type="number" min="0" step="0.1" value="${escape(String(startTimeSeconds))}" />
      </div>
      <div class="detail-row">
        <label for="editorVideoEndTime">到第几秒结束</label>
        <input id="editorVideoEndTime" type="number" min="0" step="0.1" value="${escape(String(endTimeSeconds))}" />
      </div>
      <div class="detail-row">
        <label for="editorVideoSkippable">是否允许跳过</label>
        <select id="editorVideoSkippable">
          <option value="true" ${block?.skippable !== false ? "selected" : ""}>允许玩家跳过</option>
          <option value="false" ${block?.skippable === false ? "selected" : ""}>必须播放完</option>
        </select>
      </div>
      <div class="helper-text">结束秒数填 0 表示播放到视频文件自然结束。网页包和 NW.js 桌面包会直接播放视频；原生 Runtime Preview 会优先尝试窗口内 PyAV/FFmpeg 音画同步播放，失败时再回落到 OpenCV 画面兜底或系统播放器桥接。</div>
    </div>
    <div class="detail-actions">
      <button class="toolbar-button toolbar-button-primary" data-action="save-block">保存这张卡片</button>
      <button class="toolbar-button" data-action="focus-asset-gap" data-asset-filter-mode="all" data-asset-type="video">去视频素材库</button>
    </div>
  `;
  }

  function renderCreditsRollEditor(block, options = {}) {
    const escape = getEscapeHtml(options);
    const getCreditsLinesText = getRenderer(options, "getCreditsLinesText", (lines) => Array.isArray(lines) ? lines.join("\n") : "");
    const getSafeCreditsDuration = getRenderer(options, "getSafeCreditsDuration", (value) => value ?? 18);
    const getSafeCreditsBackground = getRenderer(options, "getSafeCreditsBackground", (value) => value ?? "dark");
    const lines = getCreditsLinesText(block?.lines);
    const durationSeconds = getSafeCreditsDuration(block?.durationSeconds);
    const background = getSafeCreditsBackground(block?.background);

    return `
    <article class="editor-card">
      <h3>编辑片尾演职人员表</h3>
      <p>这是一张轻量“片尾字幕”卡片，不需要外部剪辑软件也能做基础滚动片尾。后面如果要做更复杂的片尾动画，可以再导出视频替换。</p>
    </article>
    <div class="field-grid">
      <div class="detail-row">
        <label for="editorCreditsTitle">片尾标题</label>
        <input
          id="editorCreditsTitle"
          type="text"
          maxlength="48"
          value="${escape(block?.title ?? "STAFF")}"
        />
      </div>
      <div class="detail-row">
        <label for="editorCreditsSubtitle">副标题</label>
        <input
          id="editorCreditsSubtitle"
          type="text"
          maxlength="72"
          value="${escape(block?.subtitle ?? "")}"
          placeholder="例如：Thank you for playing"
        />
      </div>
      <div class="detail-row">
        <label for="editorCreditsLines">字幕内容</label>
        <textarea id="editorCreditsLines" placeholder="企划：Creator&#10;剧本：Writer&#10;美术：Your Artist&#10;音乐：Your Composer">${escape(lines)}</textarea>
      </div>
      <div class="detail-row">
        <label for="editorCreditsDuration">滚动时长（秒）</label>
        <input id="editorCreditsDuration" type="number" min="4" max="180" step="1" value="${escape(String(durationSeconds))}" />
      </div>
      <div class="detail-row">
        <label for="editorCreditsBackground">片尾背景</label>
        <select id="editorCreditsBackground">
          ${renderLabelOptions(options.creditsBackgroundLabels, background, options)}
        </select>
      </div>
      <div class="detail-row">
        <label for="editorCreditsSkippable">是否允许跳过</label>
        <select id="editorCreditsSkippable">
          <option value="true" ${block?.skippable !== false ? "selected" : ""}>允许玩家跳过</option>
          <option value="false" ${block?.skippable === false ? "selected" : ""}>必须滚完</option>
        </select>
      </div>
    </div>
    ${renderSaveBlockActions()}
  `;
  }

  function renderJumpEditor(block, options = {}) {
    const getSafeSceneId = getRenderer(options, "getSafeSceneId", (sceneId) => sceneId ?? "");
    const renderSceneOptions = getRenderer(options, "renderSceneOptions");
    const targetSceneId = getSafeSceneId(block?.targetSceneId);

    return `
    <article class="editor-card">
      <h3>编辑场景跳转</h3>
      <p>这里决定这张卡片执行完以后，直接跳到哪个场景。</p>
    </article>
    <div class="field-grid">
      <div class="detail-row">
        <label for="editorJumpTargetSceneId">跳到哪个场景</label>
        <select id="editorJumpTargetSceneId">
          ${renderSceneOptions(targetSceneId)}
        </select>
      </div>
    </div>
    <div class="detail-actions">
      <button class="toolbar-button toolbar-button-primary" data-action="save-block">保存这张卡片</button>
    </div>
  `;
  }

  function renderVariableStarterPrompt(title, description, options = {}) {
    const escape = getEscapeHtml(options);

    return `
    <article class="editor-card">
      <h3>${escape(title)}</h3>
      <p>${escape(description)}</p>
      <div class="detail-actions">
        <button class="toolbar-button toolbar-button-primary" data-action="create-starter-variables">
          一键创建基础变量库
        </button>
      </div>
    </article>
    <article class="editor-card">
      <h3>会创建什么</h3>
      <p>基础变量库会加入“好感度”（数字）、“路线标记”（文本）和“剧情开关”（是/否），足够支撑常见分支、数值变化和条件判断。</p>
    </article>
  `;
  }

  function renderVariableSetEditor(block, options = {}) {
    const escape = getEscapeHtml(options);
    const getSafeVariableId = getRenderer(options, "getSafeVariableId", (variableId) => variableId ?? "");
    const getVariableType = getRenderer(options, "getVariableType", () => "string");
    const getVariableTypeLabel = getRenderer(options, "getVariableTypeLabel", (type) => type ?? "");
    const renderVariableOptions = getRenderer(options, "renderVariableOptions");
    const renderVariableSetValueFields = getRenderer(options, "renderVariableSetValueFields");
    const variableId = getSafeVariableId(block?.variableId);

    return `
    <article class="editor-card">
      <h3>编辑变量设置</h3>
      <p>这里会把某个变量直接改成指定值，适合开关、路线名或固定状态。</p>
    </article>
    <div class="field-grid">
      <div class="detail-row">
        <label for="editorVariableId">要设置哪个变量</label>
        <select id="editorVariableId">
          ${renderVariableOptions(variableId)}
        </select>
      </div>
      <div class="detail-row">
        <label>变量类型</label>
        <div id="editorVariableTypeValue" class="value">${escape(
          getVariableTypeLabel(getVariableType(variableId))
        )}</div>
      </div>
      <div id="editorVariableValueFields" class="field-grid">
        ${renderVariableSetValueFields(variableId, block?.value)}
      </div>
    </div>
    <div class="detail-actions">
      <button class="toolbar-button toolbar-button-primary" data-action="save-block">保存这张卡片</button>
    </div>
  `;
  }

  function renderVariableAddEditor(block, options = {}) {
    const escape = getEscapeHtml(options);
    const getSafeVariableId = getRenderer(options, "getSafeVariableId", (variableId) => variableId ?? "");
    const getSafeNumber = getRenderer(options, "getSafeNumber", (value, fallback = 0) => {
      const parsed = Number.parseFloat(value ?? "");
      return Number.isFinite(parsed) ? parsed : fallback;
    });
    const renderVariableOptions = getRenderer(options, "renderVariableOptions");
    const variableId = getSafeVariableId(block?.variableId, "number");

    return `
    <article class="editor-card">
      <h3>编辑数字变量变化</h3>
      <p>这里会给数字变量加减数值，最适合好感度、分数和进度条。</p>
    </article>
    <div class="field-grid">
      <div class="detail-row">
        <label for="editorVariableAddId">要修改哪个数字变量</label>
        <select id="editorVariableAddId">
          ${renderVariableOptions(variableId, "number")}
        </select>
      </div>
      <div class="detail-row">
        <label for="editorVariableAddValue">变化值</label>
        <input
          id="editorVariableAddValue"
          type="number"
          step="1"
          value="${escape(String(getSafeNumber(block?.value, 1)))}"
        />
      </div>
      <div class="helper-text">正数表示增加，负数表示减少。这里只会列出数字类型的变量。</div>
    </div>
    <div class="detail-actions">
      <button class="toolbar-button toolbar-button-primary" data-action="save-block">保存这张卡片</button>
    </div>
  `;
  }

  function renderConditionEditor(block, options = {}) {
    const createDefaultConditionBranches = getRenderer(options, "createDefaultConditionBranches", () => []);
    const getSafeSceneId = getRenderer(options, "getSafeSceneId", (sceneId) => sceneId ?? "");
    const getDefaultJumpTargetSceneId = getRenderer(options, "getDefaultJumpTargetSceneId", () => "");
    const getSceneLabelById = getRenderer(options, "getSceneLabelById", (sceneId) => sceneId);
    const renderDetailRows = getRenderer(options, "renderDetailRows");
    const renderSceneOptions = getRenderer(options, "renderSceneOptions");
    const renderBranchRow = getRenderer(options, "renderConditionBranchEditorRow", renderConditionBranchEditorRow);
    const branches = Array.isArray(block?.branches) && block.branches.length > 0
      ? block.branches
      : createDefaultConditionBranches(block?.id, options.selectedSceneId);
    const elseGotoSceneId = getSafeSceneId(
      block?.elseGotoSceneId,
      getDefaultJumpTargetSceneId(options.selectedSceneId)
    );

    return `
    <article class="editor-card">
      <h3>编辑条件判断</h3>
      <p>这里会先检查变量，再根据结果跳到不同场景。每条分支都可以继续加判断。</p>
    </article>
    ${renderDetailRows([
      ["当前分支数", branches.length],
      ["没命中时去哪里", getSceneLabelById(elseGotoSceneId)],
    ])}
    <div id="conditionBranchesEditor" class="option-editor-list">
      ${branches.map((branch, index) => renderBranchRow(branch, index, branches.length)).join("")}
    </div>
    <div class="detail-row">
      <label for="editorConditionElseSceneId">如果都不满足，跳到哪个场景</label>
      <select id="editorConditionElseSceneId">
        ${renderSceneOptions(elseGotoSceneId)}
      </select>
    </div>
    <div class="detail-actions">
      <button class="toolbar-button" data-action="add-condition-branch">再加一条分支</button>
      <button class="toolbar-button toolbar-button-primary" data-action="save-block">保存这张卡片</button>
    </div>
  `;
  }

  function renderChoiceEffectEditorRow(effect, index, effectCount = 1, options = {}) {
    const normalizeChoiceEffect = getRenderer(options, "normalizeChoiceEffect", (value) => value ?? {});
    const renderChoiceEffectTypeOptions = getRenderer(options, "renderChoiceEffectTypeOptions");
    const renderVariableOptions = getRenderer(options, "renderVariableOptions");
    const renderChoiceEffectValueFields = getRenderer(options, "renderChoiceEffectValueFields");
    const safeEffect = normalizeChoiceEffect(effect);
    const safeIndex = Number.isFinite(Number(index)) ? Number(index) : 0;
    const safeEffectCount = Math.max(Number.isFinite(Number(effectCount)) ? Number(effectCount) : 1, 1);
    const variableFilter = safeEffect.type === "variable_add" ? "number" : null;

    return `
    <div class="effect-editor" data-choice-effect>
      <strong data-choice-effect-title>附加效果 ${safeIndex + 1}</strong>
      <div class="field-grid">
        <div class="detail-row">
          <label>效果类型</label>
          <select data-field="choice-effect-type">
            ${renderChoiceEffectTypeOptions(safeEffect.type)}
          </select>
        </div>
        <div class="detail-row">
          <label>作用到哪个变量</label>
          <select data-field="choice-effect-variable">
            ${renderVariableOptions(safeEffect.variableId, variableFilter)}
          </select>
        </div>
        <div class="field-grid" data-choice-effect-value-fields>
          ${renderChoiceEffectValueFields(safeEffect.type, safeEffect.variableId, safeEffect.value)}
        </div>
      </div>
      <div class="detail-actions">
        <button class="toolbar-button" data-action="move-choice-effect-up" ${safeIndex <= 0 ? "disabled" : ""}>上移效果</button>
        <button class="toolbar-button" data-action="move-choice-effect-down" ${safeIndex >= safeEffectCount - 1 ? "disabled" : ""}>下移效果</button>
        <button class="toolbar-button" data-action="remove-choice-effect">删除这条效果</button>
      </div>
    </div>
  `;
  }

  function renderChoiceEffectEmptyState() {
    return `<div class="helper-text" data-choice-effects-empty>这个选项暂时没有附加效果。需要的话，点下面按钮就能继续加。</div>`;
  }

  function renderConditionRuleEditorRow(rule, index, ruleCount = 1, options = {}) {
    const getSafeVariableId = getRenderer(options, "getSafeVariableId", (variableId) => variableId ?? "");
    const getSafeConditionOperator = getRenderer(options, "getSafeConditionOperator", (_variableId, operator) => operator ?? "==");
    const renderVariableOptions = getRenderer(options, "renderVariableOptions");
    const renderConditionOperatorOptions = getRenderer(options, "renderConditionOperatorOptions");
    const renderConditionValueFields = getRenderer(options, "renderConditionValueFields");
    const safeRule = rule ?? {};
    const safeIndex = Number.isFinite(Number(index)) ? Number(index) : 0;
    const safeRuleCount = Math.max(Number.isFinite(Number(ruleCount)) ? Number(ruleCount) : 1, 1);
    const variableId = getSafeVariableId(safeRule.variableId);
    const operator = getSafeConditionOperator(variableId, safeRule.operator);

    return `
    <div class="option-editor" data-condition-rule>
      <strong data-condition-rule-title>判断 ${safeIndex + 1}</strong>
      <div class="field-grid">
        <div class="detail-row">
          <label>检查哪个变量</label>
          <select data-field="condition-variable">
            ${renderVariableOptions(variableId)}
          </select>
        </div>
        <div class="detail-row">
          <label>比较方式</label>
          <select data-field="condition-operator">
            ${renderConditionOperatorOptions(variableId, operator)}
          </select>
        </div>
        <div class="field-grid" data-condition-value-fields>
          ${renderConditionValueFields(variableId, safeRule.value)}
        </div>
      </div>
      <div class="detail-actions">
        <button class="toolbar-button" data-action="move-condition-rule-up" ${safeIndex <= 0 ? "disabled" : ""}>上移判断</button>
        <button class="toolbar-button" data-action="move-condition-rule-down" ${safeIndex >= safeRuleCount - 1 ? "disabled" : ""}>下移判断</button>
        <button class="toolbar-button" data-action="remove-condition-rule">删除这个判断</button>
      </div>
    </div>
  `;
  }

  function renderConditionBranchEditorRow(branch, index, branchCount = 1, options = {}) {
    const escape = getEscapeHtml(options);
    const createConditionBranchId = getRenderer(
      options,
      "createConditionBranchId",
      (_blockId, branchIndex) => `condition_branch_${Number(branchIndex) + 1}`
    );
    const createDefaultConditionRule = getRenderer(options, "createDefaultConditionRule", () => ({}));
    const getSafeSceneId = getRenderer(options, "getSafeSceneId", (sceneId) => sceneId ?? "");
    const getDefaultJumpTargetSceneId = getRenderer(options, "getDefaultJumpTargetSceneId", () => "");
    const renderSceneOptions = getRenderer(options, "renderSceneOptions");
    const renderRuleRow = getRenderer(options, "renderConditionRuleEditorRow", renderConditionRuleEditorRow);
    const safeBranch = branch ?? {};
    const safeIndex = Number.isFinite(Number(index)) ? Number(index) : 0;
    const safeBranchCount = Math.max(Number.isFinite(Number(branchCount)) ? Number(branchCount) : 1, 1);
    const branchId = String(safeBranch.id ?? createConditionBranchId("condition", safeIndex));
    const rules = Array.isArray(safeBranch.when) && safeBranch.when.length > 0
      ? safeBranch.when
      : [createDefaultConditionRule()];
    const gotoSceneId = getSafeSceneId(
      safeBranch.gotoSceneId,
      getDefaultJumpTargetSceneId(options.selectedSceneId)
    );

    return `
    <div class="option-editor" data-condition-branch data-branch-id="${escape(branchId)}">
      <strong data-condition-branch-title>条件分支 ${safeIndex + 1}</strong>
      <div class="field-grid">
        <div class="detail-row">
          <label>满足这条分支后跳到哪里</label>
          <select data-field="condition-goto">
            ${renderSceneOptions(gotoSceneId)}
          </select>
        </div>
      </div>
      <div class="option-editor-list" data-condition-rules>
        ${rules.map((item, ruleIndex) => renderRuleRow(item, ruleIndex, rules.length)).join("")}
      </div>
      <div class="detail-actions">
        <button class="toolbar-button" data-action="move-condition-branch-up" ${safeIndex <= 0 ? "disabled" : ""}>上移分支</button>
        <button class="toolbar-button" data-action="move-condition-branch-down" ${safeIndex >= safeBranchCount - 1 ? "disabled" : ""}>下移分支</button>
        <button class="toolbar-button" data-action="add-condition-rule" data-branch-id="${escape(branchId)}">再加一个判断</button>
        <button class="toolbar-button" data-action="remove-condition-branch" data-branch-id="${escape(branchId)}">删除这条分支</button>
      </div>
    </div>
  `;
  }

  function renderChoiceOptionEditorRow(option, index, optionCount = 1, options = {}) {
    const escape = getEscapeHtml(options);
    const safeOption = option ?? {};
    const scenes = Array.isArray(options.scenes) ? options.scenes : [];
    const renderChoiceTextQualityTools = getRenderer(options, "renderChoiceTextQualityTools");
    const renderEffectRow = getRenderer(options, "renderChoiceEffectEditorRow", renderChoiceEffectEditorRow);
    const renderEmptyState = getRenderer(options, "renderChoiceEffectEmptyState", renderChoiceEffectEmptyState);
    const editableEffects = getEditableChoiceEffects(safeOption.effects, options);
    const effectCount = Array.isArray(safeOption.effects) ? safeOption.effects.length : 0;
    const unsupportedEffectCount = Math.max(effectCount - editableEffects.length, 0);
    const safeIndex = Number.isFinite(Number(index)) ? Number(index) : 0;
    const safeOptionCount = Math.max(Number.isFinite(Number(optionCount)) ? Number(optionCount) : 1, 1);
    const optionId = String(safeOption.id ?? "");

    return `
    <div class="option-editor" data-choice-option data-option-id="${escape(optionId)}">
      <strong data-choice-option-title>选项 ${safeIndex + 1}</strong>
      <div class="field-grid">
        <div class="detail-row">
          <label>选项文案</label>
          <input
            type="text"
            data-field="choice-text"
            value="${escape(safeOption.text ?? "")}"
            placeholder="例如：一起回家吧"
          />
          ${renderChoiceTextQualityTools(safeOption.text)}
        </div>
        <div class="detail-row">
          <label>跳转到哪个场景</label>
          <select data-field="choice-goto">
            ${scenes
              .map(
                (scene) => `
                  <option value="${escape(scene.id ?? "")}" ${scene.id === safeOption.gotoSceneId ? "selected" : ""}>
                    ${escape(scene.name ?? "")}
                  </option>
                `
              )
              .join("")}
          </select>
        </div>
        <div class="detail-row">
          <label>这个选项触发时还要做什么</label>
          <div class="value">当前共有 ${effectCount} 条附加效果</div>
        </div>
        <div class="effect-editor-list" data-choice-effects>
          ${
            editableEffects.length > 0
              ? editableEffects
                  .map((effect, effectIndex) => renderEffectRow(effect, effectIndex, editableEffects.length))
                  .join("")
              : renderEmptyState()
          }
        </div>
        ${
          unsupportedEffectCount > 0
            ? `<div class="helper-text">这个选项里还有 ${unsupportedEffectCount} 条暂时不支持可视化编辑的旧效果，保存时会继续保留。</div>`
            : ""
        }
        <div class="detail-actions">
          <button
            class="toolbar-button"
            data-action="move-choice-option-up"
            data-option-id="${escape(optionId)}"
            ${safeIndex <= 0 ? "disabled" : ""}
          >
            上移选项
          </button>
          <button
            class="toolbar-button"
            data-action="move-choice-option-down"
            data-option-id="${escape(optionId)}"
            ${safeIndex >= safeOptionCount - 1 ? "disabled" : ""}
          >
            下移选项
          </button>
          <button class="toolbar-button" data-action="add-choice-effect" data-option-id="${escape(optionId)}">给这个选项加效果</button>
          <button class="toolbar-button" data-action="remove-choice-option" data-option-id="${escape(optionId)}">删除这个选项</button>
        </div>
      </div>
    </div>
  `;
  }

  global.CanvasiaEditorStoryBlockEditors = Object.freeze({
    renderBlockManagementCard,
    renderReadonlyBlockPanel,
    renderScreenShakeEditor,
    renderScreenFlashEditor,
    renderScreenFadeEditor,
    renderCameraZoomEditor,
    renderCameraPanEditor,
    renderColorGradeNumberInput,
    renderScreenFilterEditor,
    renderDepthBlurEditor,
    renderReadableTextQualityTools,
    renderDialogueEditor,
    renderChoiceEditor,
    renderNarrationEditor,
    renderChoiceCountQualityTools,
    renderBackgroundEditor,
    renderCharacterShowEditor,
    renderCharacterHideEditor,
    renderMusicPlayEditor,
    renderMusicStopEditor,
    renderSfxPlayEditor,
    renderVideoPlayEditor,
    renderCreditsRollEditor,
    renderJumpEditor,
    renderVariableStarterPrompt,
    renderVariableSetEditor,
    renderVariableAddEditor,
    renderConditionEditor,
    renderConditionBranchEditorRow,
    renderConditionRuleEditorRow,
    renderChoiceEffectEditorRow,
    renderChoiceEffectEmptyState,
    renderChoiceOptionEditorRow,
  });
})(typeof window !== "undefined" ? window : globalThis);
