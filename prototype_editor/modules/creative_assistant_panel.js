(function attachCreativeAssistantPanel(global) {
  function getSafeFunction(value, fallback) {
    return typeof value === "function" ? value : fallback;
  }

  function normalizeOptions(options = {}) {
    const state = options.state ?? {};
    return {
      state,
      scene: options.scene ?? null,
      selectedBlock: options.selectedBlock ?? null,
      modes: options.modes ?? {},
      providers: options.providers ?? {},
      promptSamples: Array.isArray(options.promptSamples) ? options.promptSamples : [],
      maxHistory: Math.max(1, Number(options.maxHistory) || 1),
      escapeHtml: getSafeFunction(options.escapeHtml, (value) => String(value ?? "")),
      getSafeMode: getSafeFunction(options.getSafeMode, (value) => String(value ?? "")),
      getSafeProvider: getSafeFunction(options.getSafeProvider, (value) => String(value ?? "local")),
      getProviderConfig: getSafeFunction(options.getProviderConfig, () => ({})),
      getSafeModel: getSafeFunction(options.getSafeModel, (value) => String(value ?? "")),
      getResultBlocks: getSafeFunction(options.getResultBlocks, (result) => (Array.isArray(result?.blocks) ? result.blocks : [])),
      getActiveBlockIndexes: getSafeFunction(options.getActiveBlockIndexes, () => []),
      getSelectedBlocks: getSafeFunction(options.getSelectedBlocks, () => []),
      getBlockTypeLabel: getSafeFunction(options.getBlockTypeLabel, (blockType) => String(blockType ?? "旁白")),
      getBlockSummary: getSafeFunction(options.getBlockSummary, () => ({ title: "场景末尾" })),
      filterHistoryRecords: getSafeFunction(options.filterHistoryRecords, (records) => records),
    };
  }

  function formatCreativeAssistantHistoryTime(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return "刚刚";
    }
    return date.toLocaleString("zh-CN", {
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  function renderProviderButtons(context) {
    const { state, providers, getSafeProvider, escapeHtml } = context;
    return Object.entries(providers)
      .map(
        ([provider, label]) => `
          <button
            type="button"
            class="creative-mode-button ${getSafeProvider(state.creativeAssistantProvider) === provider ? "is-active" : ""}"
            data-action="set-creative-assistant-provider"
            data-creative-provider="${escapeHtml(provider)}"
          >
            ${escapeHtml(label)}
          </button>
        `
      )
      .join("");
  }

  function renderModeButtons(context) {
    const { state, modes, getSafeMode, escapeHtml } = context;
    return Object.entries(modes)
      .map(
        ([mode, label]) => `
          <button
            type="button"
            class="creative-mode-button ${getSafeMode(state.creativeAssistantMode) === mode ? "is-active" : ""}"
            data-action="set-creative-assistant-mode"
            data-creative-mode="${escapeHtml(mode)}"
          >
            ${escapeHtml(label)}
          </button>
        `
      )
      .join("");
  }

  function renderCreativeAssistantBlankPanel() {
    return `
      <div class="creative-assistant-shell is-blank">
        <div class="creative-assistant-copy">
          <span class="eyebrow">Canvasia Assistant</span>
          <strong>先创建一个场景，智能创作助手就能帮你搭 Demo。</strong>
          <p>默认使用本地模板，不上传项目、不产生 API 费用；也可以在剧情编辑页切到自带 Key 的真模型模式。</p>
        </div>
      </div>
    `;
  }

  function renderBlockPreview(context, result) {
    const { getResultBlocks, getActiveBlockIndexes, getBlockTypeLabel, escapeHtml } = context;
    const blocks = getResultBlocks(result);
    if (!blocks.length) {
      return "";
    }
    const selectedIndexes = getActiveBlockIndexes(result);
    const selectedSet = new Set(selectedIndexes);
    return `
      <div class="creative-block-preview">
        <div class="creative-block-preview-head">
          <span>剧情卡片预览 · 已选 ${selectedIndexes.length}/${blocks.length}</span>
          <button type="button" class="toolbar-button" data-action="copy-creative-assistant-blocks" ${selectedIndexes.length ? "" : "disabled"}>复制已选卡片</button>
        </div>
        <div class="creative-block-preview-list">
          ${blocks
            .map((block, index) => {
              const blockType = ["dialogue", "narration", "choice"].includes(block?.type) ? block.type : "narration";
              const choiceOptions = Array.isArray(block?.options) ? block.options : [];
              const checked = selectedSet.has(index);
              return `
                <article class="creative-block-preview-card ${checked ? "is-selected" : ""}">
                  <div class="creative-block-preview-card-head">
                    <span>#${index + 1}</span>
                    <strong>${escapeHtml(getBlockTypeLabel(blockType))}</strong>
                    <label class="creative-block-select">
                      <input
                        type="checkbox"
                        data-action="toggle-creative-assistant-block"
                        data-creative-block-index="${index}"
                        ${checked ? "checked" : ""}
                      />
                      <span>插入</span>
                    </label>
                  </div>
                  ${
                    blockType === "choice"
                      ? `
                        <div class="creative-block-options">
                          ${choiceOptions
                            .map(
                              (option, optionIndex) => `
                                <span>${optionIndex + 1}. ${escapeHtml(option?.text || `选项 ${optionIndex + 1}`)}</span>
                              `
                            )
                            .join("")}
                        </div>
                      `
                      : `
                        <p>
                          ${blockType === "dialogue" && block?.speakerId ? `<em>${escapeHtml(block.speakerId)}</em>` : ""}
                          ${escapeHtml(block?.text ?? "")}
                        </p>
                      `
                  }
                </article>
              `;
            })
            .join("")}
        </div>
      </div>
    `;
  }

  function renderResult(context) {
    const { state, providers, getSafeProvider, escapeHtml } = context;
    const result = state.creativeAssistantResult;
    if (state.creativeAssistantLoading) {
      return `
        <div class="creative-assistant-result">
          <strong>正在构思...</strong>
          <p>助手正在把主题拆成剧情节奏、可插入卡片和素材方向。</p>
        </div>
      `;
    }
    if (state.creativeAssistantError) {
      return `
        <div class="creative-assistant-result is-error">
          <strong>生成失败</strong>
          <p>${escapeHtml(state.creativeAssistantError)}</p>
        </div>
      `;
    }
    if (!result) {
      return `
        <div class="creative-assistant-result is-empty">
          <strong>可以从一句话开始。</strong>
          <p>例如“雨夜校园悬疑恋爱”，助手会生成剧情片段、创作建议和可继续扩展的素材提示。</p>
        </div>
      `;
    }

    const guidance = Array.isArray(result.guidance) ? result.guidance : [];
    const assetPrompts = Array.isArray(result.assetPrompts) ? result.assetPrompts : [];
    const blockCount = Number(result.blockCount ?? result.blocks?.length ?? 0);
    const provider = result.provider ?? {};
    const providerLabel = provider.label ?? providers[getSafeProvider(provider.mode)] ?? "兼容模型";
    const providerMeta = provider.model ? `${providerLabel} · ${provider.model}` : providerLabel;
    return `
      <div class="creative-assistant-result">
        <div class="creative-result-head">
          <span class="issue-tag good-text">${escapeHtml(result.modeLabel ?? "本地助手")}</span>
          <span class="issue-tag ${provider.fallback ? "warn-text" : ""}">${escapeHtml(providerMeta)}</span>
          <span class="issue-tag">${blockCount > 0 ? `可插入 ${blockCount} 张卡片` : "仅建议"}</span>
        </div>
        <strong>${escapeHtml(result.title ?? "已生成创作建议")}</strong>
        <p>${escapeHtml(result.summary ?? "")}</p>
        <div class="creative-advice-list">
          ${guidance.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}
        </div>
        ${renderBlockPreview(context, result)}
        ${
          assetPrompts.length > 0
            ? `
              <div class="creative-asset-prompts">
                <span>素材概念提示</span>
                ${assetPrompts.map((item) => `<code>${escapeHtml(item)}</code>`).join("")}
              </div>
            `
            : ""
        }
        <div class="creative-privacy-note">
          ${escapeHtml(result.privacy?.message ?? "当前为本地模板助手，不会上传项目内容。")}
          ${result.fallbackReason ? `<br />回落原因：${escapeHtml(result.fallbackReason)}` : ""}
        </div>
      </div>
    `;
  }

  function renderHistory(context) {
    const {
      state,
      providers,
      modes,
      maxHistory,
      escapeHtml,
      getResultBlocks,
      filterHistoryRecords,
    } = context;
    const records = Array.isArray(state.creativeAssistantHistory) ? state.creativeAssistantHistory : [];
    const recovery = state.creativeAssistantHistoryRecovery;
    const recoveryCount = recovery?.records?.length ?? 0;
    if (!records.length && !recoveryCount) {
      return "";
    }
    const visibleRecords = filterHistoryRecords(records).slice(0, maxHistory);
    const favoriteCount = records.filter((record) => record.favorite).length;
    const query = state.creativeAssistantHistoryQuery ?? "";
    const favoritesOnly = Boolean(state.creativeAssistantHistoryFavoritesOnly);
    const isFiltered = Boolean(query.trim() || favoritesOnly);
    return `
      <div class="creative-assistant-history">
        <div class="creative-history-head">
          <div>
            <span class="eyebrow">Idea Vault</span>
            <strong>灵感盒</strong>
            <span>${visibleRecords.length}/${records.length} 条${favoriteCount ? ` · 收藏 ${favoriteCount}` : ""}</span>
          </div>
          <div class="creative-history-head-actions">
            <button type="button" class="toolbar-button" data-action="copy-creative-assistant-history-markdown">复制档案</button>
            <button type="button" class="toolbar-button" data-action="export-creative-assistant-history-markdown">导出 Markdown</button>
            <button type="button" class="toolbar-button" data-action="export-creative-assistant-history-view" ${visibleRecords.length ? "" : "disabled"}>导出当前视图</button>
            <button type="button" class="toolbar-button" data-action="export-creative-assistant-history-archive">导出全部</button>
            <button type="button" class="toolbar-button" data-action="clear-creative-assistant-nonfavorites" ${favoriteCount && favoriteCount < records.length ? "" : "disabled"}>清理未收藏</button>
            <button type="button" class="toolbar-button" data-action="clear-creative-assistant-history">清空</button>
            ${
              recoveryCount
                ? `<button type="button" class="toolbar-button toolbar-button-primary" data-action="restore-creative-assistant-history-recovery">恢复上次清理</button>`
                : ""
            }
          </div>
        </div>
        ${
          recoveryCount
            ? `<div class="creative-history-recovery">最近一次删除 / 清理前保留了 ${recoveryCount} 条可恢复灵感；恢复前会把当前灵感盒保存成新的恢复点。</div>`
            : ""
        }
        <div class="creative-history-tools">
          <label class="creative-history-search">
            <span class="sr-only">搜索灵感盒</span>
            <input
              id="creativeAssistantHistorySearchInput"
              type="search"
              placeholder="搜索标题、场景、提示词、素材建议..."
              value="${escapeHtml(query)}"
            />
          </label>
          <button
            type="button"
            class="toolbar-button ${favoritesOnly ? "is-active" : ""}"
            data-action="toggle-creative-assistant-history-favorites"
          >
            ${favoritesOnly ? "显示全部" : "只看收藏"}
          </button>
        </div>
        <div class="creative-history-list">
          ${
            visibleRecords.length
              ? visibleRecords
                  .map((record) => {
                    const blockCount = getResultBlocks(record.result).length;
                    const providerLabel = record.result?.provider?.label ?? providers[record.result?.provider?.mode] ?? "本地模板";
                    return `
                      <article class="creative-history-card ${record.favorite ? "is-favorite" : ""}">
                        <div>
                          <strong>${escapeHtml(record.result?.title ?? "未命名灵感")}</strong>
                          <p>${escapeHtml(record.prompt || record.result?.summary || "未填写主题")}</p>
                          <div class="creative-history-meta">
                            <span>${escapeHtml(record.result?.modeLabel ?? modes[record.result?.mode] ?? "灵感")}</span>
                            <span>${blockCount ? `${blockCount} 张卡片` : "仅建议"}</span>
                            <span>${escapeHtml(providerLabel)}</span>
                          </div>
                          <span>${escapeHtml(record.sceneName)} · ${escapeHtml(formatCreativeAssistantHistoryTime(record.createdAt))}</span>
                        </div>
                        <div class="creative-history-actions">
                          <button type="button" class="toolbar-button" data-action="toggle-creative-assistant-history-favorite" data-creative-history-id="${escapeHtml(record.id)}">${record.favorite ? "已收藏" : "收藏"}</button>
                          <button type="button" class="toolbar-button" data-action="copy-creative-assistant-history-blocks" data-creative-history-id="${escapeHtml(record.id)}" ${blockCount ? "" : "disabled"}>复制卡片</button>
                          <button type="button" class="toolbar-button" data-action="copy-creative-assistant-history-record-markdown" data-creative-history-id="${escapeHtml(record.id)}">复制文档</button>
                          <button type="button" class="toolbar-button" data-action="restore-creative-assistant-history" data-creative-history-id="${escapeHtml(record.id)}">恢复</button>
                          <button type="button" class="toolbar-button" data-action="export-creative-assistant-history" data-creative-history-id="${escapeHtml(record.id)}">导出</button>
                          <button type="button" class="toolbar-button danger" data-action="delete-creative-assistant-history" data-creative-history-id="${escapeHtml(record.id)}">删除</button>
                        </div>
                      </article>
                    `;
                  })
                  .join("")
              : `<div class="creative-history-empty">${isFiltered ? "没有匹配的灵感。换个关键词，或者先显示全部。" : "灵感盒暂时为空。"}</div>`
          }
        </div>
        <p class="creative-history-note">灵感盒最多保留 ${maxHistory} 条，收藏会优先保留；内容只保存在当前浏览器 localStorage，不写入项目文件，也不会保存 API Key。</p>
      </div>
    `;
  }

  function renderCreativeAssistantPanel(options = {}) {
    const context = normalizeOptions(options);
    const {
      state,
      scene,
      selectedBlock,
      providers,
      promptSamples,
      escapeHtml,
      getSafeProvider,
      getProviderConfig,
      getSafeModel,
      getSelectedBlocks,
      getBlockSummary,
    } = context;
    const sampleButtons = promptSamples
      .map(
        (sample) => `
          <button
            type="button"
            class="creative-sample-chip"
            data-action="apply-creative-assistant-sample"
            data-creative-prompt="${escapeHtml(sample)}"
          >
            ${escapeHtml(sample)}
          </button>
        `
      )
      .join("");
    const selectedBlockCount = getSelectedBlocks().length;
    const canInsert = Boolean(state.creativeAssistantResult?.insertable && selectedBlockCount > 0 && !state.creativeAssistantLoading);
    const provider = getSafeProvider(state.creativeAssistantProvider);
    const providerConfig = getProviderConfig(provider);
    const isModelProvider = provider !== "local";
    const currentContext = selectedBlock ? getBlockSummary(selectedBlock, scene).title : "场景末尾";
    return `
      <div class="creative-assistant-shell">
        <div class="creative-assistant-copy">
          <span class="eyebrow">Canvasia Assistant · 创作搭子</span>
          <div class="creative-assistant-title-row">
            <strong>智能创作助手</strong>
            <span class="badge badge-soft">${escapeHtml(scene?.name ?? "当前场景")}</span>
          </div>
          <p>本地模板适合零配置试玩；也可以使用 OpenAI、DeepSeek、通义千问、Kimi、智谱或自定义兼容 API Key 生成更自由的剧情、建议和素材提示。</p>
          <div class="creative-current-context">当前插入点：${escapeHtml(currentContext)}</div>
        </div>
        <div class="creative-assistant-workbench">
          <div class="creative-provider-row">
            <span>生成引擎</span>
            <div class="creative-mode-row">${renderProviderButtons(context)}</div>
          </div>
          ${
            isModelProvider
              ? `
                <div class="creative-openai-config">
                  <label>
                    <span>${escapeHtml(providerConfig.label ?? providers[provider] ?? "兼容模型")} API Key</span>
                    <input
                      id="creativeAssistantOpenAiKey"
                      type="password"
                      autocomplete="off"
                      placeholder="${escapeHtml(providerConfig.keyPlaceholder ?? "API Key")}"
                      value="${escapeHtml(state.creativeAssistantOpenAiKey)}"
                    />
                  </label>
                  <label>
                    <span>模型</span>
                    <input
                      id="creativeAssistantModel"
                      type="text"
                      spellcheck="false"
                      placeholder="${escapeHtml(providerConfig.modelPlaceholder ?? providerConfig.defaultModel ?? "")}"
                      value="${escapeHtml(getSafeModel(state.creativeAssistantModel, provider))}"
                    />
                  </label>
                  ${
                    provider === "custom"
                      ? `
                        <label>
                          <span>Base URL</span>
                          <input
                            id="creativeAssistantBaseUrl"
                            type="url"
                            spellcheck="false"
                            placeholder="https://example.com/v1 或 http://127.0.0.1:11434/v1"
                            value="${escapeHtml(state.creativeAssistantBaseUrl ?? "")}"
                          />
                        </label>
                      `
                      : ""
                  }
                  <p class="helper-text">${escapeHtml(providerConfig.endpointNote ?? "Key 只用于本次生成，不会写入项目文件。")}</p>
                  <label class="creative-remember-key">
                    <input
                      id="creativeAssistantRememberKey"
                      type="checkbox"
                      ${state.creativeAssistantRememberKey ? "checked" : ""}
                    />
                    <span>只在本浏览器记住 Key，不写入项目文件</span>
                  </label>
                  <div class="creative-openai-actions">
                    <span>隐私安全</span>
                    <button
                      type="button"
                      class="toolbar-button"
                      data-action="forget-creative-assistant-key"
                      ${state.creativeAssistantOpenAiKey || state.creativeAssistantRememberKey ? "" : "disabled"}
                    >
                      忘记本机 Key
                    </button>
                  </div>
                </div>
              `
              : ""
          }
          <div class="creative-mode-row">${renderModeButtons(context)}</div>
          <textarea
            id="creativeAssistantPrompt"
            class="creative-assistant-prompt"
            placeholder="一句话描述你想做的游戏或场景，比如：雨夜校园悬疑恋爱，女主知道一个不能说的秘密"
          >${escapeHtml(state.creativeAssistantPrompt)}</textarea>
          <div class="creative-sample-row">${sampleButtons}</div>
          <div class="creative-action-row">
            <button
              type="button"
              class="toolbar-button toolbar-button-primary"
              data-action="generate-creative-assistant"
              ${state.creativeAssistantLoading ? "disabled" : ""}
            >
              ${state.creativeAssistantLoading ? "生成中..." : isModelProvider ? "用 API 生成" : "生成建议"}
            </button>
            <button
              type="button"
              class="toolbar-button"
              data-action="insert-creative-assistant-blocks"
              ${canInsert ? "" : "disabled"}
            >
              插入到当前场景
            </button>
            <button
              type="button"
              class="toolbar-button"
              data-action="copy-creative-assistant-summary"
              ${state.creativeAssistantResult ? "" : "disabled"}
            >
              复制建议
            </button>
            <button
              type="button"
              class="toolbar-button"
              data-action="export-creative-assistant-history"
              data-creative-history-id="${escapeHtml(state.creativeAssistantHistory?.[0]?.id ?? "")}"
              ${state.creativeAssistantHistory?.[0] ? "" : "disabled"}
            >
              导出最新灵感
            </button>
            <label class="toolbar-button creative-import-button">
              导入灵感
              <input
                id="creativeAssistantHistoryImportInput"
                class="sr-only"
                type="file"
                accept="application/json,.json,.canvasia-idea.json,.canvasia-idea-vault.json"
              />
            </label>
          </div>
        </div>
        ${renderResult(context)}
        ${renderHistory(context)}
      </div>
    `;
  }

  global.CanvasiaEditorCreativeAssistantPanel = Object.freeze({
    formatCreativeAssistantHistoryTime,
    renderCreativeAssistantBlankPanel,
    renderCreativeAssistantPanel,
  });
})(typeof window !== "undefined" ? window : globalThis);
