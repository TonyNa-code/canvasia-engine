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

  function getSafeOpenAiAssetGenerationType(type) {
    return OPENAI_ASSET_GENERATION_TYPES.includes(type) ? type : "background";
  }

  function getSafeOpenAiAssetGenerationOption(value, options, fallback) {
    return options.includes(value) ? value : fallback;
  }

  function getOpenAiAssetPromptSample(assetType) {
    return OPENAI_ASSET_GENERATION_TYPE_PROMPTS[getSafeOpenAiAssetGenerationType(assetType)];
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
      </section>
    `;
  }

  function buildOpenAiAssetGenerationPayload(state) {
    return {
      assetType: getSafeOpenAiAssetGenerationType(state.openAiAssetType),
      prompt: String(state.openAiAssetPrompt ?? "").trim(),
      assetName: String(state.openAiAssetName ?? "").trim(),
      apiKey: String(state.openAiAssetApiKey ?? "").trim(),
      model: String(state.openAiAssetModel ?? "").trim() || "gpt-image-1.5",
      size: getSafeOpenAiAssetGenerationOption(state.openAiAssetSize, OPENAI_ASSET_GENERATION_SIZES, "1536x1024"),
      quality: getSafeOpenAiAssetGenerationOption(state.openAiAssetQuality, OPENAI_ASSET_GENERATION_QUALITIES, "medium"),
      background: getSafeOpenAiAssetGenerationOption(state.openAiAssetBackground, OPENAI_ASSET_GENERATION_BACKGROUNDS, "auto"),
      outputFormat: getSafeOpenAiAssetGenerationOption(state.openAiAssetOutputFormat, OPENAI_ASSET_GENERATION_FORMATS, "png"),
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
    getSafeOpenAiAssetGenerationType,
    getSafeOpenAiAssetGenerationOption,
    getOpenAiAssetPromptSample,
    getOpenAiAssetPromptLengthInfo,
    getOpenAiAssetPromptLengthLabel,
    getOpenAiAssetPromptLengthWarning,
    getOpenAiAssetModelWarning,
    getOpenAiAssetGenerationCompatibilityWarning,
    getDefaultOpenAiAssetGenerationState,
    renderOpenAiAssetGeneratorPanel,
    buildOpenAiAssetGenerationPayload,
  });
})(typeof window !== "undefined" ? window : globalThis);
