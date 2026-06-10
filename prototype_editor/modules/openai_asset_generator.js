(function attachOpenAiAssetGeneratorTools(global) {
  const API_GENERATE_OPENAI_ASSET = "/api/generate-openai-asset";
  const OPENAI_ASSET_GENERATION_TYPES = Object.freeze(["background", "sprite", "cg", "ui"]);
  const OPENAI_ASSET_GENERATION_TYPE_PROMPTS = Object.freeze({
    background: "雨后黄昏的校园走廊，窗外有浅蓝色天光，适合作为视觉小说背景",
    sprite: "原创女主角半身立绘，校服，温柔但带一点神秘感，透明背景",
    cg: "两人在天台晚风中对视的事件 CG，青春恋爱视觉小说氛围",
    ui: "半透明蓝白科技感视觉小说对话框素材，干净边缘，无文字",
  });
  const OPENAI_ASSET_GENERATION_SIZES = Object.freeze(["1024x1024", "1536x1024", "1024x1536", "auto"]);
  const OPENAI_ASSET_GENERATION_QUALITIES = Object.freeze(["medium", "high", "low", "auto"]);
  const OPENAI_ASSET_GENERATION_BACKGROUNDS = Object.freeze(["auto", "transparent", "opaque"]);
  const OPENAI_ASSET_GENERATION_FORMATS = Object.freeze(["png", "webp", "jpeg"]);
  const OPENAI_ASSET_GENERATION_MAX_PROMPT_CHARS = 1400;
  const OPENAI_ASSET_GENERATION_MAX_STYLE_HINT_CHARS = 260;
  const OPENAI_ASSET_GENERATION_STYLE_HINT_PRESETS = Object.freeze([
    Object.freeze({
      id: "clear-school",
      label: "清透校园",
      value: "清透蓝白、柔和光线、校园恋爱氛围",
    }),
    Object.freeze({
      id: "cinematic-night",
      label: "电影夜景",
      value: "深蓝夜景、电影感光影、轻微胶片颗粒",
    }),
    Object.freeze({
      id: "warm-watercolor",
      label: "暖色水彩",
      value: "暖色水彩、柔和轮廓、日常治愈氛围",
    }),
    Object.freeze({
      id: "clean-ui",
      label: "简洁 UI",
      value: "简洁科技感、干净边缘、低饱和蓝白配色",
    }),
  ]);
  const OPENAI_ASSET_EXPRESSION_BIND_PRESETS = Object.freeze([
    Object.freeze({ id: "expr_default", label: "默认", name: "默认" }),
    Object.freeze({ id: "expr_smile", label: "微笑", name: "微笑" }),
    Object.freeze({ id: "expr_shy", label: "害羞", name: "害羞" }),
  ]);

  function getSafeOpenAiAssetGenerationType(type) {
    return OPENAI_ASSET_GENERATION_TYPES.includes(type) ? type : "background";
  }

  function getSafeOpenAiAssetGenerationOption(value, options, fallback) {
    return options.includes(value) ? value : fallback;
  }

  function getOpenAiAssetPromptSample(assetType) {
    return OPENAI_ASSET_GENERATION_TYPE_PROMPTS[getSafeOpenAiAssetGenerationType(assetType)];
  }

  function getOpenAiAssetStyleHintPreset(presetId) {
    return (
      OPENAI_ASSET_GENERATION_STYLE_HINT_PRESETS.find((preset) => preset.id === String(presetId ?? "")) ?? null
    );
  }

  function getOpenAiAssetExpressionBindPreset(presetId) {
    return (
      OPENAI_ASSET_EXPRESSION_BIND_PRESETS.find((preset) => preset.id === String(presetId ?? "")) ?? null
    );
  }

  function getOpenAiAssetPromptLengthInfo(prompt) {
    const length = Array.from(String(prompt ?? "")).length;
    return {
      length,
      max: OPENAI_ASSET_GENERATION_MAX_PROMPT_CHARS,
      remaining: Math.max(0, OPENAI_ASSET_GENERATION_MAX_PROMPT_CHARS - length),
      overLimit: length > OPENAI_ASSET_GENERATION_MAX_PROMPT_CHARS,
    };
  }

  function getOpenAiAssetPromptLengthLabel(prompt) {
    const info = getOpenAiAssetPromptLengthInfo(prompt);
    return `提示词 ${info.length} / ${info.max} 字`;
  }

  function getOpenAiAssetPromptLengthWarning(prompt) {
    const info = getOpenAiAssetPromptLengthInfo(prompt);
    return info.overLimit ? `提示词超过 ${info.max} 字，请缩短后再生成。` : "";
  }

  function getOpenAiAssetStyleHintLengthInfo(styleHint) {
    const length = Array.from(String(styleHint ?? "")).length;
    return {
      length,
      max: OPENAI_ASSET_GENERATION_MAX_STYLE_HINT_CHARS,
      remaining: Math.max(0, OPENAI_ASSET_GENERATION_MAX_STYLE_HINT_CHARS - length),
      overLimit: length > OPENAI_ASSET_GENERATION_MAX_STYLE_HINT_CHARS,
    };
  }

  function getOpenAiAssetStyleHintLengthLabel(styleHint) {
    const info = getOpenAiAssetStyleHintLengthInfo(styleHint);
    return `画风补充 ${info.length} / ${info.max} 字`;
  }

  function getOpenAiAssetStyleHintLengthWarning(styleHint) {
    const info = getOpenAiAssetStyleHintLengthInfo(styleHint);
    return info.overLimit ? `画风补充超过 ${info.max} 字，请缩短后再生成。` : "";
  }

  function getOpenAiAssetModelWarning(model) {
    const value = String(model ?? "").trim();
    if (!value) {
      return "";
    }
    if (value.length > 80 || !/^[A-Za-z0-9._:-]+$/.test(value)) {
      return "模型名只能包含英文字母、数字、点、下划线、冒号或短横线，且不超过 80 个字符。";
    }
    return "";
  }

  function getOpenAiAssetGenerationCompatibilityWarning(state = {}) {
    const background = getSafeOpenAiAssetGenerationOption(
      state.openAiAssetBackground,
      OPENAI_ASSET_GENERATION_BACKGROUNDS,
      "auto"
    );
    const outputFormat = getSafeOpenAiAssetGenerationOption(
      state.openAiAssetOutputFormat,
      OPENAI_ASSET_GENERATION_FORMATS,
      "png"
    );
    if (background === "transparent" && outputFormat === "jpeg") {
      return "JPEG 不支持透明背景。请改用 PNG / WebP，或把背景改为自动 / 不透明。";
    }
    return "";
  }

  function getDefaultOpenAiAssetGenerationState() {
    return {
      openAiAssetType: "background",
      openAiAssetPrompt: OPENAI_ASSET_GENERATION_TYPE_PROMPTS.background,
      openAiAssetName: "",
      openAiAssetApiKey: "",
      openAiAssetModel: "gpt-image-1.5",
      openAiAssetStyleHint: "",
      openAiAssetBindCharacterId: "",
      openAiAssetBindExpressionId: "expr_default",
      openAiAssetBindExpressionName: "默认",
      openAiAssetBindAsDefaultSprite: true,
      openAiAssetSize: "1536x1024",
      openAiAssetQuality: "medium",
      openAiAssetBackground: "auto",
      openAiAssetOutputFormat: "png",
      openAiAssetLoading: false,
      openAiAssetError: "",
      openAiAssetLastResult: null,
    };
  }

  function renderOpenAiAssetSelectOptions(options, selectedValue, labels = {}, escapeHtml = String) {
    return options
      .map((option) => {
        const label = labels[option] ?? option;
        return `<option value="${escapeHtml(option)}" ${option === selectedValue ? "selected" : ""}>${escapeHtml(label)}</option>`;
      })
      .join("");
  }

  function renderOpenAiAssetGeneratorPanel({
    state,
    selectedAssetType = "background",
    characters = [],
    escapeHtml = String,
    getAssetTypeLabel = (type) => type,
  }) {
    const assetType = getSafeOpenAiAssetGenerationType(state.openAiAssetType || selectedAssetType);
    const typeLabels = Object.fromEntries(
      OPENAI_ASSET_GENERATION_TYPES.map((type) => [type, getAssetTypeLabel(type)])
    );
    const sizeLabels = {
      "1536x1024": "横图 1536 x 1024",
      "1024x1536": "竖图 1024 x 1536",
      "1024x1024": "方图 1024 x 1024",
      auto: "自动",
    };
    const qualityLabels = {
      low: "低成本草稿",
      medium: "标准",
      high: "高质量",
      auto: "自动",
    };
    const backgroundLabels = {
      auto: "自动",
      transparent: "透明背景",
      opaque: "不透明背景",
    };
    const formatLabels = {
      png: "PNG",
      webp: "WebP",
      jpeg: "JPEG",
    };
    const samplePrompt = getOpenAiAssetPromptSample(assetType);
    const isLoading = Boolean(state.openAiAssetLoading);
    const fieldLockAttrs = isLoading ? 'disabled aria-disabled="true" title="AI 素材正在生成，请稍等..."' : "";
    const modelWarning = getOpenAiAssetModelWarning(state.openAiAssetModel);
    const promptLengthWarning = getOpenAiAssetPromptLengthWarning(state.openAiAssetPrompt);
    const styleHintLengthWarning = getOpenAiAssetStyleHintLengthWarning(state.openAiAssetStyleHint);
    const safeCharacters = Array.isArray(characters) ? characters.filter((character) => character?.id) : [];
    const selectedBindCharacterId = String(state.openAiAssetBindCharacterId ?? "").trim();
    const lastResult = state.openAiAssetLastResult ?? {};
    const lastAsset = lastResult.asset ?? null;
    const lastAssetPath = typeof lastAsset?.path === "string" ? lastAsset.path : "";
    const lastPrivacyMessage =
      typeof lastResult.privacy?.message === "string"
        ? lastResult.privacy.message
        : lastResult.privacy?.apiKeyStored === false
          ? "API Key 未写入项目文件或素材元数据。"
          : "";
    const compatibilityWarning = getOpenAiAssetGenerationCompatibilityWarning(state);

    return `
      <section class="detail-card openai-asset-generator-panel">
        <div class="panel-heading">
          <div>
            <h3>AI 生成素材</h3>
            <span class="panel-note">填一句需求，生成结果会自动进入当前项目素材库</span>
          </div>
          <span class="badge badge-soft">OpenAI Image</span>
        </div>
        <form id="openAiAssetGeneratorForm" class="openai-asset-generator-form" autocomplete="off" novalidate onsubmit="return false">
          <div class="openai-asset-generator-grid">
          <label>
            <span>素材类型</span>
            <select id="openAiAssetType" ${fieldLockAttrs}>
              ${renderOpenAiAssetSelectOptions(OPENAI_ASSET_GENERATION_TYPES, assetType, typeLabels, escapeHtml)}
            </select>
          </label>
          <label>
            <span>素材名称</span>
            <input id="openAiAssetName" type="text" maxlength="80" placeholder="比如：雨夜教室背景" value="${escapeHtml(state.openAiAssetName)}" ${fieldLockAttrs} />
          </label>
          <label>
            <span>OpenAI API Key</span>
            <input id="openAiAssetApiKey" type="password" autocomplete="off" placeholder="sk-..." value="${escapeHtml(state.openAiAssetApiKey)}" ${fieldLockAttrs} />
          </label>
          <label>
            <span>模型</span>
            <input id="openAiAssetModel" type="text" spellcheck="false" value="${escapeHtml(state.openAiAssetModel)}" placeholder="gpt-image-1.5" ${fieldLockAttrs} />
            ${
              modelWarning
                ? `<span class="helper-text danger-text" role="alert">${escapeHtml(modelWarning)}</span>`
                : '<span class="helper-text">留空会使用默认模型；自定义模型名不要包含空格。</span>'
            }
          </label>
          <label>
            <span>画风补充</span>
            <input
              id="openAiAssetStyleHint"
              type="text"
              maxlength="${OPENAI_ASSET_GENERATION_MAX_STYLE_HINT_CHARS}"
              placeholder="比如：清透蓝白、柔和光线、校园恋爱氛围"
              value="${escapeHtml(state.openAiAssetStyleHint)}"
              ${fieldLockAttrs}
            />
            <span
              id="openAiAssetStyleHintLengthStatus"
              class="helper-text ${styleHintLengthWarning ? "danger-text" : ""}"
              role="status"
              aria-live="polite"
            >${escapeHtml(styleHintLengthWarning || getOpenAiAssetStyleHintLengthLabel(state.openAiAssetStyleHint))}</span>
            <div class="openai-asset-style-preset-row" aria-label="画风补充预设">
              ${OPENAI_ASSET_GENERATION_STYLE_HINT_PRESETS.map((preset) => {
                const isActive = String(state.openAiAssetStyleHint ?? "").trim() === preset.value;
                return `
                  <button
                    type="button"
                    class="asset-tag-chip openai-asset-style-preset ${isActive ? "is-active" : ""} ${isLoading ? "is-locked" : ""}"
                    data-action="apply-openai-asset-style-preset"
                    data-style-preset="${escapeHtml(preset.id)}"
                    ${isLoading ? 'disabled aria-disabled="true" title="AI 素材正在生成，请稍等..."' : ""}
                  >
                    ${escapeHtml(preset.label)}
                  </button>
                `;
              }).join("")}
            </div>
          </label>
          ${
            assetType === "sprite"
              ? `
                <div class="openai-asset-bind-panel">
                  <div>
                    <strong>生成后绑定角色</strong>
                    <span class="helper-text">可选。生成立绘后自动绑定为角色默认立绘或某个表情，方便马上进入剧情预览。</span>
                  </div>
                  ${
                    safeCharacters.length
                      ? `
                        <div class="openai-asset-bind-grid">
                          <label>
                            <span>绑定到角色</span>
                            <select id="openAiAssetBindCharacterId" ${fieldLockAttrs}>
                              <option value="">不绑定，只加入素材库</option>
                              ${safeCharacters
                                .map((character) => {
                                  const characterId = String(character.id ?? "");
                                  const characterName = String(character.displayName ?? character.name ?? characterId);
                                  return `<option value="${escapeHtml(characterId)}" ${characterId === selectedBindCharacterId ? "selected" : ""}>${escapeHtml(characterName)}</option>`;
                                })
                                .join("")}
                            </select>
                          </label>
                          <label>
                            <span>表情 ID</span>
                            <input
                              id="openAiAssetBindExpressionId"
                              type="text"
                              maxlength="80"
                              value="${escapeHtml(state.openAiAssetBindExpressionId)}"
                              placeholder="expr_default"
                              ${fieldLockAttrs}
                            />
                          </label>
                          <label>
                            <span>表情名称</span>
                            <input
                              id="openAiAssetBindExpressionName"
                              type="text"
                              maxlength="40"
                              value="${escapeHtml(state.openAiAssetBindExpressionName)}"
                              placeholder="默认"
                              ${fieldLockAttrs}
                            />
                          </label>
                        </div>
                        <div class="openai-asset-style-preset-row" aria-label="角色表情快捷预设">
                          ${OPENAI_ASSET_EXPRESSION_BIND_PRESETS.map((preset) => {
                            const isActive = String(state.openAiAssetBindExpressionId ?? "").trim() === preset.id;
                            return `
                              <button
                                type="button"
                                class="asset-tag-chip openai-asset-style-preset ${isActive ? "is-active" : ""} ${isLoading ? "is-locked" : ""}"
                                data-action="apply-openai-asset-expression-preset"
                                data-expression-preset="${escapeHtml(preset.id)}"
                                ${isLoading ? 'disabled aria-disabled="true" title="AI 素材正在生成，请稍等..."' : ""}
                              >
                                ${escapeHtml(preset.label)}
                              </button>
                            `;
                          }).join("")}
                        </div>
                        <label class="openai-asset-bind-default">
                          <input
                            id="openAiAssetBindAsDefaultSprite"
                            type="checkbox"
                            ${state.openAiAssetBindAsDefaultSprite ? "checked" : ""}
                            ${fieldLockAttrs}
                          />
                          <span>同时设为角色默认立绘 / 表现兜底图</span>
                        </label>
                      `
                      : '<span class="helper-text">项目里还没有角色。可以先去角色页创建角色，或只把生成结果加入素材库。</span>'
                  }
                </div>
              `
              : ""
          }
          <label>
            <span>尺寸</span>
            <select id="openAiAssetSize" ${fieldLockAttrs}>
              ${renderOpenAiAssetSelectOptions(OPENAI_ASSET_GENERATION_SIZES, state.openAiAssetSize, sizeLabels, escapeHtml)}
            </select>
          </label>
          <label>
            <span>质量</span>
            <select id="openAiAssetQuality" ${fieldLockAttrs}>
              ${renderOpenAiAssetSelectOptions(OPENAI_ASSET_GENERATION_QUALITIES, state.openAiAssetQuality, qualityLabels, escapeHtml)}
            </select>
          </label>
          <label>
            <span>背景</span>
            <select id="openAiAssetBackground" ${fieldLockAttrs}>
              ${renderOpenAiAssetSelectOptions(OPENAI_ASSET_GENERATION_BACKGROUNDS, state.openAiAssetBackground, backgroundLabels, escapeHtml)}
            </select>
          </label>
          <label>
            <span>格式</span>
            <select id="openAiAssetOutputFormat" ${fieldLockAttrs}>
              ${renderOpenAiAssetSelectOptions(OPENAI_ASSET_GENERATION_FORMATS, state.openAiAssetOutputFormat, formatLabels, escapeHtml)}
            </select>
          </label>
          <label class="openai-asset-prompt-field">
            <span>提示词</span>
            <textarea id="openAiAssetPrompt" maxlength="${OPENAI_ASSET_GENERATION_MAX_PROMPT_CHARS}" placeholder="${escapeHtml(samplePrompt)}" ${fieldLockAttrs}>${escapeHtml(state.openAiAssetPrompt)}</textarea>
            <span
              id="openAiAssetPromptLengthStatus"
              class="helper-text ${promptLengthWarning ? "danger-text" : ""}"
              role="status"
              aria-live="polite"
            >${escapeHtml(promptLengthWarning || getOpenAiAssetPromptLengthLabel(state.openAiAssetPrompt))}</span>
          </label>
          </div>
          <div class="creative-current-context">
            Key 只随本次请求发送，不会写入项目文件；生成出来的图片会保存到 ${escapeHtml(getAssetTypeLabel(assetType))} 素材库。
          </div>
          ${
            compatibilityWarning
              ? `<p class="helper-text warn-text" role="note">${escapeHtml(compatibilityWarning)}</p>`
              : ""
          }
          ${
            isLoading
              ? '<p class="helper-text" role="status" aria-live="polite">正在生成素材，完成后会自动导入素材库，请暂时不要关闭页面。</p>'
              : ""
          }
          ${
            state.openAiAssetError
              ? `<p class="helper-text danger-text" role="alert">${escapeHtml(state.openAiAssetError)}</p>`
              : ""
          }
          ${
            lastAsset
              ? `<p class="helper-text good-text" role="status" aria-live="polite">刚刚已生成：${escapeHtml(lastAsset.name)} · ${escapeHtml(getAssetTypeLabel(lastAsset.type))}</p>`
              : ""
          }
          ${
            lastAsset && (lastAssetPath || lastPrivacyMessage)
              ? `
                <div class="creative-current-context" role="note">
                  ${lastAssetPath ? `<span>保存位置：${escapeHtml(lastAssetPath)}</span>` : ""}
                  ${lastPrivacyMessage ? `<span>隐私确认：${escapeHtml(lastPrivacyMessage)}</span>` : ""}
                </div>
              `
              : ""
          }
          <div class="creative-action-row">
            <button
              type="button"
              class="toolbar-button toolbar-button-primary ${isLoading ? "is-busy" : ""}"
              data-action="generate-openai-asset"
              ${isLoading ? 'disabled aria-disabled="true" aria-busy="true"' : ""}
            >
              ${isLoading ? "正在生成..." : "生成并导入素材库"}
            </button>
            <button
              type="button"
              class="toolbar-button ${isLoading ? "is-locked" : ""}"
              data-action="apply-openai-asset-prompt-sample"
              data-asset-type="${escapeHtml(assetType)}"
              ${isLoading ? 'disabled aria-disabled="true" title="AI 素材正在生成，请稍等..."' : ""}
            >
              填入示例提示词
            </button>
            <button
              type="button"
              class="toolbar-button ${isLoading ? "is-locked" : ""}"
              data-action="forget-openai-asset-key"
              ${isLoading || !state.openAiAssetApiKey ? 'disabled aria-disabled="true"' : ""}
              title="只清空当前页面里的生图 Key，不影响项目文件"
            >
              清空本次 Key
            </button>
          </div>
        </form>
      </section>
    `;
  }

  function buildOpenAiAssetGenerationPayload(state) {
    const assetType = getSafeOpenAiAssetGenerationType(state.openAiAssetType);
    const bindCharacterId = String(state.openAiAssetBindCharacterId ?? "").trim();
    return {
      assetType,
      prompt: String(state.openAiAssetPrompt ?? "").trim(),
      assetName: String(state.openAiAssetName ?? "").trim(),
      apiKey: String(state.openAiAssetApiKey ?? "").trim(),
      model: String(state.openAiAssetModel ?? "").trim() || "gpt-image-1.5",
      styleHint: String(state.openAiAssetStyleHint ?? "").trim(),
      size: getSafeOpenAiAssetGenerationOption(state.openAiAssetSize, OPENAI_ASSET_GENERATION_SIZES, "1536x1024"),
      quality: getSafeOpenAiAssetGenerationOption(state.openAiAssetQuality, OPENAI_ASSET_GENERATION_QUALITIES, "medium"),
      background: getSafeOpenAiAssetGenerationOption(state.openAiAssetBackground, OPENAI_ASSET_GENERATION_BACKGROUNDS, "auto"),
      outputFormat: getSafeOpenAiAssetGenerationOption(state.openAiAssetOutputFormat, OPENAI_ASSET_GENERATION_FORMATS, "png"),
      characterBinding:
        assetType === "sprite" && bindCharacterId
          ? {
              characterId: bindCharacterId,
              expressionId: String(state.openAiAssetBindExpressionId ?? "").trim(),
              expressionName: String(state.openAiAssetBindExpressionName ?? "").trim(),
              setAsDefaultSprite: Boolean(state.openAiAssetBindAsDefaultSprite),
            }
          : null,
    };
  }

  global.CanvasiaEditorOpenAiAssetGenerator = Object.freeze({
    API_GENERATE_OPENAI_ASSET,
    OPENAI_ASSET_GENERATION_TYPES,
    OPENAI_ASSET_GENERATION_TYPE_PROMPTS,
    OPENAI_ASSET_GENERATION_SIZES,
    OPENAI_ASSET_GENERATION_QUALITIES,
    OPENAI_ASSET_GENERATION_BACKGROUNDS,
    OPENAI_ASSET_GENERATION_FORMATS,
    OPENAI_ASSET_GENERATION_MAX_PROMPT_CHARS,
    OPENAI_ASSET_GENERATION_MAX_STYLE_HINT_CHARS,
    OPENAI_ASSET_GENERATION_STYLE_HINT_PRESETS,
    OPENAI_ASSET_EXPRESSION_BIND_PRESETS,
    getSafeOpenAiAssetGenerationType,
    getSafeOpenAiAssetGenerationOption,
    getOpenAiAssetPromptSample,
    getOpenAiAssetStyleHintPreset,
    getOpenAiAssetExpressionBindPreset,
    getOpenAiAssetPromptLengthInfo,
    getOpenAiAssetPromptLengthLabel,
    getOpenAiAssetPromptLengthWarning,
    getOpenAiAssetStyleHintLengthInfo,
    getOpenAiAssetStyleHintLengthLabel,
    getOpenAiAssetStyleHintLengthWarning,
    getOpenAiAssetModelWarning,
    getOpenAiAssetGenerationCompatibilityWarning,
    getDefaultOpenAiAssetGenerationState,
    renderOpenAiAssetGeneratorPanel,
    buildOpenAiAssetGenerationPayload,
  });
})(typeof window !== "undefined" ? window : globalThis);
