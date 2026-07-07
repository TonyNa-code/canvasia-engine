(function attachProjectRuntimeSettingsPanelTools(global) {
  "use strict";

  function defaultEscapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function getEscapeHtml(helpers = {}) {
    return typeof helpers.escapeHtml === "function" ? helpers.escapeHtml : defaultEscapeHtml;
  }

  function toEntries(value) {
    return Object.entries(value ?? {});
  }

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function getAssetList(assetContext = {}) {
    return Array.isArray(assetContext.assetList) ? assetContext.assetList : [];
  }

  function getAssetById(assetContext = {}, assetId = "") {
    const id = String(assetId ?? "");
    if (!id) {
      return null;
    }
    if (typeof assetContext.assetsById?.get === "function") {
      return assetContext.assetsById.get(id) ?? null;
    }
    if (assetContext.assetsById && Object.prototype.hasOwnProperty.call(assetContext.assetsById, id)) {
      return assetContext.assetsById[id] ?? null;
    }
    return getAssetList(assetContext).find((asset) => asset?.id === id) ?? null;
  }

  function getAssetTypeLabel(assetContext = {}, type = "") {
    if (typeof assetContext.getAssetTypeLabel === "function") {
      return assetContext.getAssetTypeLabel(type);
    }
    return String(type || "素材");
  }

  function getAssetOptionLabel(asset = {}) {
    const fileName = String(asset.path ?? "").split("/").pop();
    return asset.fileExists ? `${asset.name} · ${fileName}` : `${asset.name} · 文件未导入`;
  }

  function renderOptionList(labels = {}, selectedValue = "", helpers = {}) {
    const escapeHtml = getEscapeHtml(helpers);
    return toEntries(labels)
      .map(
        ([value, label]) =>
          `<option value="${escapeHtml(value)}" ${selectedValue === value ? "selected" : ""}>${escapeHtml(label)}</option>`
      )
      .join("");
  }

  function renderPresetButtons(labels = {}, selectedValue = "", action = "", datasetName = "", helpers = {}) {
    const escapeHtml = getEscapeHtml(helpers);
    return toEntries(labels)
      .filter(([preset]) => preset !== "custom")
      .map(
        ([preset, label]) => `
          <button
            class="toolbar-button ${selectedValue === preset ? "toolbar-button-primary" : ""}"
            type="button"
            data-action="${escapeHtml(action)}"
            ${datasetName}="${escapeHtml(preset)}"
          >
            ${escapeHtml(label)}
          </button>
        `
      )
      .join("");
  }

  function renderSelectField({ id, label, optionsHtml }, helpers = {}) {
    const escapeHtml = getEscapeHtml(helpers);
    return `
      <label class="playback-setting">
        <span>${escapeHtml(label)}</span>
        <select id="${escapeHtml(id)}">
          ${optionsHtml}
        </select>
      </label>
    `;
  }

  function renderTextInputField({ id, label, value = "", placeholder = "", maxLength = 80 }, helpers = {}) {
    const escapeHtml = getEscapeHtml(helpers);
    return `
      <label class="playback-setting">
        <span>${escapeHtml(label)}</span>
        <input
          id="${escapeHtml(id)}"
          type="text"
          maxlength="${Number(maxLength) || 80}"
          placeholder="${escapeHtml(placeholder)}"
          value="${escapeHtml(value)}"
        />
      </label>
    `;
  }

  function renderCheckboxButton({ id, label, checked }, helpers = {}) {
    const escapeHtml = getEscapeHtml(helpers);
    return `
      <label class="toolbar-button playback-setting-inline">
        <input id="${escapeHtml(id)}" type="checkbox" ${checked ? "checked" : ""} />
        ${escapeHtml(label)}
      </label>
    `;
  }

  function renderColorField({ id, label, value }, helpers = {}) {
    const escapeHtml = getEscapeHtml(helpers);
    return `
      <label class="playback-setting">
        <span>${escapeHtml(label)}</span>
        <input id="${escapeHtml(id)}" type="color" value="${escapeHtml(value)}" />
      </label>
    `;
  }

  function renderRangeField({ id, label, value, min, max, step = 1, suffix = "" }, helpers = {}) {
    const escapeHtml = getEscapeHtml(helpers);
    return `
      <label class="playback-setting">
        <span>${escapeHtml(label)}</span>
        <input id="${escapeHtml(id)}" type="range" min="${min}" max="${max}" step="${step}" value="${escapeHtml(value)}" />
        <strong class="playback-volume-value">${escapeHtml(value)}${escapeHtml(suffix)}</strong>
      </label>
    `;
  }

  function buildDialogBoxAssetSelectOptions(assetContext = {}, selectedAssetId = "", helpers = {}) {
    const escapeHtml = getEscapeHtml(helpers);
    const uiAssets = getAssetList(assetContext).filter((asset) => asset?.type === "ui");
    if (!uiAssets.length) {
      return `<option value="">当前还没有可用的 UI 素材</option>`;
    }
    return [
      `<option value="" ${!selectedAssetId ? "selected" : ""}>不叠图片图层</option>`,
      ...uiAssets.map(
        (asset) =>
          `<option value="${escapeHtml(asset.id)}" ${selectedAssetId === asset.id ? "selected" : ""}>${escapeHtml(
            getAssetOptionLabel(asset)
          )}</option>`
      ),
    ].join("");
  }

  function buildGameUiAssetSelectOptions(
    assetContext = {},
    selectedAssetId = "",
    allowedTypes = ["ui"],
    emptyLabel = "不绑定素材",
    helpers = {}
  ) {
    const escapeHtml = getEscapeHtml(helpers);
    const allowedSet = new Set(allowedTypes);
    const assets = getAssetList(assetContext).filter((asset) => allowedSet.has(asset?.type));
    const selectedAsset = getAssetById(assetContext, selectedAssetId);
    const options = [`<option value="" ${!selectedAssetId ? "selected" : ""}>${escapeHtml(emptyLabel)}</option>`];

    if (selectedAssetId && selectedAsset && !allowedSet.has(selectedAsset.type)) {
      options.push(
        `<option value="${escapeHtml(selectedAsset.id)}" selected>${escapeHtml(`${selectedAsset.name} · 当前绑定`)}</option>`
      );
    }

    if (!assets.length) {
      const typeHint = allowedTypes.map((type) => getAssetTypeLabel(assetContext, type)).join(" / ") || "素材";
      options.push(`<option value="" disabled>当前还没有可用${escapeHtml(typeHint)}，可先去素材库导入</option>`);
      return options.join("");
    }

    options.push(
      ...assets.map(
        (asset) =>
          `<option value="${escapeHtml(asset.id)}" ${selectedAssetId === asset.id ? "selected" : ""}>${escapeHtml(
            getAssetOptionLabel(asset)
          )}</option>`
      )
    );
    return options.join("");
  }

  function renderGameUiFrameSliceControls(idPrefix, title, slice = {}, helpers = {}) {
    const escapeHtml = getEscapeHtml(helpers);
    const fields = [
      ["top", "上"],
      ["right", "右"],
      ["bottom", "下"],
      ["left", "左"],
    ];
    return `
      <div class="detail-card ui-frame-slice-card">
        <strong>${escapeHtml(title)}</strong>
        <p class="helper-text">九宫格边距会决定 UI 贴图四角不被拉伸，中间区域自动延展；适合按钮框、科幻边框、纸张卷轴等资源。</p>
        <div class="playback-setting-grid dialog-config-grid">
          ${fields
            .map(
              ([key, label]) => `
                <label class="playback-setting">
                  <span>${label}边距</span>
                  <input
                    id="${escapeHtml(idPrefix)}${key[0].toUpperCase()}${key.slice(1)}Input"
                    type="number"
                    min="0"
                    max="96"
                    step="1"
                    value="${escapeHtml(slice[key])}"
                  />
                </label>
              `
            )
            .join("")}
        </div>
      </div>
    `;
  }

  function renderDialogBoxReadabilityCard(report, plan, digest, helpers = {}) {
    if (!report || !plan || !digest) {
      return "";
    }

    const escapeHtml = getEscapeHtml(helpers);
    const metrics = report.metrics ?? {};
    const issueItems = toArray(report.issues).slice(0, 3);
    const issueListMarkup = issueItems.length > 0
      ? `
        <ul class="dialog-readability-issue-list">
          ${issueItems
            .map((issue) => `<li>${escapeHtml(issue.title)}：${escapeHtml(issue.detail)}</li>`)
            .join("")}
        </ul>
      `
      : `<p class="dialog-readability-ok">当前文本框读起来比较稳，暂时不需要自动修复。</p>`;
    const operationSummary = plan.changed
      ? `将调整 ${toArray(plan.operations).length} 项：${toArray(plan.operations)
          .map((operation) => operation.label)
          .slice(0, 4)
          .join("、")}`
      : "不会修改你的自定义贴图、锚点、偏移或剧情内容。";

    return `
      <div class="dialog-readability-card" data-readability-level="${escapeHtml(digest.level)}">
        <div class="dialog-readability-head">
          <div>
            <strong>文本框可读性安全网</strong>
            <p class="helper-text">${escapeHtml(digest.helperText)}</p>
          </div>
          <span class="dialog-readability-badge" data-readability-level="${escapeHtml(digest.level)}">
            ${escapeHtml(digest.badgeLabel)}
          </span>
        </div>
        <div class="dialog-readability-metrics">
          <span>正文 ${metrics.textBlockCount ?? 0} 段</span>
          <span>长文本 ${metrics.longTextCount ?? 0} 段</span>
          <span>多行 ${metrics.multilineCount ?? 0} 段</span>
          <span>对比度 ${metrics.textContrastRatio ?? "-"}:1</span>
        </div>
        ${issueListMarkup}
        <div class="dialog-readability-actions">
          <button
            class="toolbar-button ${plan.changed ? "toolbar-button-primary" : ""}"
            type="button"
            data-action="apply-dialog-box-readability-fix"
            ${plan.changed && !helpers.dialogBoxReadabilityFixInFlight ? "" : "disabled"}
          >
            ${escapeHtml(helpers.dialogBoxReadabilityFixInFlight ? "增强中..." : digest.actionLabel)}
          </button>
          <span>${escapeHtml(operationSummary)}</span>
        </div>
      </div>
    `;
  }

  function renderLocalizationSection(model, helpers = {}) {
    const escapeHtml = getEscapeHtml(helpers);
    const labels = model.labels?.languageLabels ?? {};
    return `
      <section class="detail-card dialog-config-card">
        <strong>多语言与国际化</strong>
        <p class="helper-text">先选择默认语言，再勾选成品包里允许玩家切换的语言。剧情卡片可逐步补充 textTranslations / displayNameTranslations，缺失翻译会自动回退到默认文本。</p>
        <div class="playback-setting-grid dialog-config-grid">
          ${renderSelectField(
            {
              id: "projectDefaultLanguageSelect",
              label: "默认语言",
              optionsHtml: renderOptionList(labels, model.projectLanguage, helpers),
            },
            helpers
          )}
          <div class="playback-setting">
            <span>成品可切换语言</span>
            <div class="detail-actions">
              ${toEntries(labels)
                .map(
                  ([language, label]) => `
                    <label class="toolbar-button">
                      <input
                        type="checkbox"
                        data-project-supported-language
                        value="${escapeHtml(language)}"
                        ${toArray(model.projectSupportedLanguages).includes(language) ? "checked" : ""}
                      />
                      ${escapeHtml(label)}
                    </label>
                  `
                )
                .join("")}
            </div>
          </div>
        </div>
        <div class="detail-actions">
          <button class="toolbar-button toolbar-button-primary" data-action="save-project-localization">
            保存多语言设置
          </button>
        </div>
        <div class="detail-meta">当前默认语言：${escapeHtml(labels[model.projectLanguage] ?? model.projectLanguage)}；导出 Runtime 会提供 ${toArray(model.projectSupportedLanguages).length} 种语言。</div>
      </section>
    `;
  }

  function renderSaveSlotSection(model, helpers = {}) {
    const runtimeSettings = model.runtimeSettings ?? {};
    const limits = model.saveSlotLimits ?? {};
    return `
      <section class="detail-card dialog-config-card">
        <strong>正式存档位数量</strong>
        <p class="helper-text">手动存档位不再固定。大项目可直接扩到 50、100 或更多，读档分页会自动跟着变化。</p>
        <div class="asset-search-row story-tree-filter-row">
          <label class="asset-search-field">
            <span class="sr-only">正式存档位数量</span>
            <input
              id="projectFormalSaveSlotCountInput"
              type="number"
              min="${limits.min}"
              max="${limits.max}"
              step="1"
              value="${runtimeSettings.formalSaveSlotCount}"
            />
          </label>
          <button class="toolbar-button toolbar-button-primary" data-action="save-project-save-slot-count">
            保存存档位
          </button>
        </div>
        <div class="detail-meta">当前项目已配置 ${runtimeSettings.formalSaveSlotCount} 个正式存档位，正式读档会自动分页展示。</div>
      </section>
    `;
  }

  function renderPlaybackDefaultsSection(model, helpers = {}) {
    const escapeHtml = getEscapeHtml(helpers);
    const runtimeSettings = model.runtimeSettings ?? {};
    const labels = model.labels ?? {};
    return `
      <section class="detail-card dialog-config-card">
        <strong>成品默认播放体验</strong>
        <p class="helper-text">这里控制玩家第一次打开导出游戏时的阅读节奏、主题和音量。玩家在游戏里手动调整后，会优先使用玩家自己的本地设置。</p>
        <div class="playback-setting-grid dialog-config-grid">
          ${renderSelectField(
            {
              id: "projectRuntimeDefaultTextSpeedSelect",
              label: "默认文字速度",
              optionsHtml: renderOptionList(labels.textSpeedLabels, runtimeSettings.defaultTextSpeed, helpers),
            },
            helpers
          )}
          ${renderSelectField(
            {
              id: "projectRuntimeDefaultDialogThemeSelect",
              label: "默认对话框主题",
              optionsHtml: renderOptionList(labels.dialogThemeLabels, runtimeSettings.defaultDialogTheme, helpers),
            },
            helpers
          )}
          ${renderSelectField(
            {
              id: "projectRuntimeDefaultUiThemeModeSelect",
              label: "默认界面深浅",
              optionsHtml: renderOptionList(labels.uiThemeModeLabels, runtimeSettings.defaultUiThemeMode, helpers),
            },
            helpers
          )}
          ${renderSelectField(
            {
              id: "projectRuntimePerformanceProfileSelect",
              label: "性能目标",
              optionsHtml: renderOptionList(labels.performanceProfileLabels, runtimeSettings.performanceProfile, helpers),
            },
            helpers
          )}
          ${renderCheckboxButton(
            {
              id: "projectRuntimeDefaultVoiceEnabledInput",
              label: "默认开启语音",
              checked: runtimeSettings.defaultVoiceEnabled,
            },
            helpers
          )}
          ${renderCheckboxButton(
            {
              id: "projectRuntimeDefaultVoiceDuckingEnabledInput",
              label: "语音时压低 BGM",
              checked: runtimeSettings.defaultVoiceDuckingEnabled,
            },
            helpers
          )}
        </div>
        <div class="playback-volume-grid dialog-config-ranges">
          ${renderRangeField({ id: "projectRuntimeDefaultBgmVolumeInput", label: "默认 BGM 音量", min: 0, max: 100, value: runtimeSettings.defaultBgmVolume, suffix: "%" }, helpers)}
          ${renderRangeField({ id: "projectRuntimeDefaultSfxVolumeInput", label: "默认音效音量", min: 0, max: 100, value: runtimeSettings.defaultSfxVolume, suffix: "%" }, helpers)}
          ${renderRangeField({ id: "projectRuntimeDefaultVoiceVolumeInput", label: "默认语音音量", min: 0, max: 100, value: runtimeSettings.defaultVoiceVolume, suffix: "%" }, helpers)}
          ${renderRangeField({ id: "projectRuntimeDefaultVoiceDuckingRatioInput", label: "语音时 BGM 保留", min: 15, max: 100, value: runtimeSettings.defaultVoiceDuckingRatio, suffix: "%" }, helpers)}
        </div>
        <div class="detail-actions">
          <button class="toolbar-button toolbar-button-primary" data-action="save-project-runtime-playback-defaults">
            保存默认播放体验
          </button>
        </div>
        <div class="detail-meta">当前默认：${escapeHtml(labels.textSpeedLabels?.[runtimeSettings.defaultTextSpeed] ?? runtimeSettings.defaultTextSpeed)} · ${escapeHtml(
          labels.dialogThemeLabels?.[runtimeSettings.defaultDialogTheme] ?? runtimeSettings.defaultDialogTheme
        )} · ${escapeHtml(labels.uiThemeModeLabels?.[runtimeSettings.defaultUiThemeMode] ?? runtimeSettings.defaultUiThemeMode)} · ${escapeHtml(
          labels.performanceProfileLabels?.[runtimeSettings.performanceProfile] ?? runtimeSettings.performanceProfile
        )} · BGM ${runtimeSettings.defaultBgmVolume}% / 音效 ${runtimeSettings.defaultSfxVolume}% / 语音 ${runtimeSettings.defaultVoiceVolume}% · 语音焦点${runtimeSettings.defaultVoiceDuckingEnabled ? "开" : "关"} / BGM 保留 ${runtimeSettings.defaultVoiceDuckingRatio}%</div>
      </section>
    `;
  }

  function renderDialogBoxSection(model, helpers = {}) {
    const dialogBoxConfig = model.dialogBoxConfig ?? {};
    const labels = model.labels ?? {};
    return `
      <section class="detail-card dialog-config-card">
        <strong>对话文本框样式</strong>
        <p class="helper-text">先选一个基础预设，再用颜色、透明度、尺寸和 UI 图层继续微调。没有特殊需求时也可以直接用透明无框。</p>
        <div class="detail-actions">
          ${renderPresetButtons(
            labels.dialogBoxPresetLabels,
            dialogBoxConfig.preset,
            "apply-project-dialog-box-preset",
            "data-dialog-preset",
            helpers
          )}
        </div>
        ${renderDialogBoxReadabilityCard(model.dialogBoxReadabilityReport, model.dialogBoxReadabilityPlan, model.dialogBoxReadabilityDigest, helpers)}
        <div class="playback-setting-grid dialog-config-grid">
          ${renderSelectField({ id: "projectDialogBoxPresetSelect", label: "当前预设", optionsHtml: renderOptionList(labels.dialogBoxPresetLabels, dialogBoxConfig.preset, helpers) }, helpers)}
          ${renderSelectField({ id: "projectDialogBoxShapeSelect", label: "框体形状", optionsHtml: renderOptionList(labels.dialogBoxShapeLabels, dialogBoxConfig.shape, helpers) }, helpers)}
          ${renderSelectField({ id: "projectDialogBoxAnchorSelect", label: "文本框位置", optionsHtml: renderOptionList(labels.dialogBoxAnchorLabels, dialogBoxConfig.anchor, helpers) }, helpers)}
          ${renderSelectField({ id: "projectDialogBoxAssetSelect", label: "图片图层", optionsHtml: buildDialogBoxAssetSelectOptions(model.assetContext, dialogBoxConfig.panelAssetId, helpers) }, helpers)}
          ${renderSelectField(
            {
              id: "projectDialogBoxAssetFitSelect",
              label: "图层铺法",
              optionsHtml: `
                <option value="cover" ${dialogBoxConfig.panelAssetFit === "cover" ? "selected" : ""}>铺满裁切</option>
                <option value="contain" ${dialogBoxConfig.panelAssetFit === "contain" ? "selected" : ""}>完整显示</option>
              `,
            },
            helpers
          )}
        </div>
        <div class="playback-setting-grid dialog-config-grid dialog-config-colors">
          ${renderColorField({ id: "projectDialogBoxBackgroundColorInput", label: "底色", value: dialogBoxConfig.backgroundColor }, helpers)}
          ${renderColorField({ id: "projectDialogBoxBorderColorInput", label: "边框色", value: dialogBoxConfig.borderColor }, helpers)}
          ${renderColorField({ id: "projectDialogBoxTextColorInput", label: "正文色", value: dialogBoxConfig.textColor }, helpers)}
          ${renderColorField({ id: "projectDialogBoxSpeakerColorInput", label: "名字色", value: dialogBoxConfig.speakerColor }, helpers)}
        </div>
        <div class="playback-volume-grid dialog-config-ranges">
          ${renderRangeField({ id: "projectDialogBoxBackgroundOpacityInput", label: "底色透明度", min: 0, max: 100, value: dialogBoxConfig.backgroundOpacity, suffix: "%" }, helpers)}
          ${renderRangeField({ id: "projectDialogBoxBorderOpacityInput", label: "边框透明度", min: 0, max: 100, value: dialogBoxConfig.borderOpacity, suffix: "%" }, helpers)}
          ${renderRangeField({ id: "projectDialogBoxAssetOpacityInput", label: "图层透明度", min: 0, max: 100, value: dialogBoxConfig.panelAssetOpacity, suffix: "%" }, helpers)}
          ${renderRangeField({ id: "projectDialogBoxBlurInput", label: "模糊", min: 0, max: 24, value: dialogBoxConfig.blurStrength, suffix: "px" }, helpers)}
          ${renderRangeField({ id: "projectDialogBoxWidthInput", label: "宽度", min: 55, max: 100, value: dialogBoxConfig.widthPercent, suffix: "%" }, helpers)}
          ${renderRangeField({ id: "projectDialogBoxHeightInput", label: "高度", min: 96, max: 320, step: 4, value: dialogBoxConfig.minHeight, suffix: "px" }, helpers)}
          ${renderRangeField({ id: "projectDialogBoxOffsetXInput", label: "水平偏移", min: -35, max: 35, value: dialogBoxConfig.offsetXPercent, suffix: "%" }, helpers)}
          ${renderRangeField({ id: "projectDialogBoxOffsetYInput", label: "垂直偏移", min: -35, max: 35, value: dialogBoxConfig.offsetYPercent, suffix: "%" }, helpers)}
        </div>
        <div class="detail-actions">
          <button class="toolbar-button toolbar-button-primary" data-action="save-project-dialog-box-config">
            保存文本框样式
          </button>
          <button class="toolbar-button" data-action="set-preview-dialog-theme-project">
            试玩里切到项目样式
          </button>
        </div>
        <div class="detail-meta">当前支持预设、透明无框、自定义颜色/尺寸，以及叠加一张 UI 素材图层；复杂版式可以先通过 UI 素材图层完成。</div>
      </section>
    `;
  }

  function renderGameUiAssetSelect(model, id, label, configKey, allowedTypes, emptyLabel, helpers = {}) {
    return renderSelectField(
      {
        id,
        label,
        optionsHtml: buildGameUiAssetSelectOptions(
          model.assetContext,
          model.gameUiConfig?.[configKey],
          allowedTypes,
          emptyLabel,
          helpers
        ),
      },
      helpers
    );
  }

  function renderGameUiSection(model, helpers = {}) {
    const gameUiConfig = model.gameUiConfig ?? {};
    const labels = model.labels ?? {};
    return `
      <section class="detail-card dialog-config-card">
        <strong>成品 UI 皮肤</strong>
        <p class="helper-text">这一层控制玩家真正看到的标题页、顶部栏、按钮、系统菜单、存档/图鉴弹窗和侧栏外观；文本框仍然由上面的“对话文本框样式”单独控制。</p>
        <div class="detail-actions">
          ${renderPresetButtons(labels.gameUiPresetLabels, gameUiConfig.preset, "apply-project-game-ui-preset", "data-game-ui-preset", helpers)}
        </div>
        <div class="playback-setting-grid dialog-config-grid">
          ${renderSelectField({ id: "projectGameUiPresetSelect", label: "皮肤预设", optionsHtml: renderOptionList(labels.gameUiPresetLabels, gameUiConfig.preset, helpers) }, helpers)}
          ${renderSelectField({ id: "projectGameUiLayoutPresetSelect", label: "运行时布局", optionsHtml: renderOptionList(labels.gameUiLayoutLabels, gameUiConfig.layoutPreset, helpers) }, helpers)}
          ${renderSelectField({ id: "projectGameUiTitleLayoutSelect", label: "标题页布局", optionsHtml: renderOptionList(labels.gameUiTitleLayoutLabels, gameUiConfig.titleLayout, helpers) }, helpers)}
          ${renderSelectField({ id: "projectGameUiFontStyleSelect", label: "字体气质", optionsHtml: renderOptionList(labels.gameUiFontLabels, gameUiConfig.fontStyle, helpers) }, helpers)}
          ${renderTextInputField({ id: "projectGameUiFontFamilyInput", label: "系统字体族", value: gameUiConfig.fontFamily, placeholder: "例如 Noto Serif CJK SC" }, helpers)}
          ${renderGameUiAssetSelect(model, "projectGameUiFontAssetSelect", "字体素材", "fontAssetId", ["font"], "使用系统字体族 / 默认字体", helpers)}
          ${renderSelectField({ id: "projectGameUiSurfaceStyleSelect", label: "面板质感", optionsHtml: renderOptionList(labels.gameUiSurfaceLabels, gameUiConfig.surfaceStyle, helpers) }, helpers)}
          ${renderSelectField({ id: "projectGameUiBrandModeSelect", label: "品牌露出", optionsHtml: renderOptionList(labels.gameUiBrandLabels, gameUiConfig.brandMode, helpers) }, helpers)}
          ${renderSelectField({ id: "projectGameUiSidePanelModeSelect", label: "侧栏显示", optionsHtml: renderOptionList(labels.gameUiSidePanelLabels, gameUiConfig.sidePanelMode, helpers) }, helpers)}
          ${renderSelectField({ id: "projectGameUiSidePanelPositionSelect", label: "侧栏位置", optionsHtml: renderOptionList(labels.gameUiSidePositionLabels, gameUiConfig.sidePanelPosition, helpers) }, helpers)}
          ${renderSelectField({ id: "projectGameUiTopbarPositionSelect", label: "顶部栏位置", optionsHtml: renderOptionList(labels.gameUiTopbarPositionLabels, gameUiConfig.topbarPosition, helpers) }, helpers)}
          ${renderSelectField({ id: "projectGameUiHudPositionSelect", label: "舞台 HUD", optionsHtml: renderOptionList(labels.gameUiHudPositionLabels, gameUiConfig.hudPosition, helpers) }, helpers)}
          ${renderSelectField({ id: "projectGameUiTitleCardAnchorSelect", label: "标题卡片位置", optionsHtml: renderOptionList(labels.gameUiTitleCardAnchorLabels, gameUiConfig.titleCardAnchor, helpers) }, helpers)}
          ${renderSelectField(
            {
              id: "projectGameUiTitleBackgroundFitSelect",
              label: "标题背景铺法",
              optionsHtml: `
                <option value="cover" ${gameUiConfig.titleBackgroundFit === "cover" ? "selected" : ""}>铺满裁切</option>
                <option value="contain" ${gameUiConfig.titleBackgroundFit === "contain" ? "selected" : ""}>完整显示</option>
              `,
            },
            helpers
          )}
        </div>
        <div class="playback-setting-grid dialog-config-grid">
          ${renderGameUiAssetSelect(model, "projectGameUiTitleBackgroundAssetSelect", "标题背景图", "titleBackgroundAssetId", ["background", "cg", "ui"], "不使用标题背景图", helpers)}
          ${renderGameUiAssetSelect(model, "projectGameUiTitleLogoAssetSelect", "标题 Logo 图", "titleLogoAssetId", ["ui", "sprite", "cg"], "使用默认 Logo", helpers)}
          ${renderGameUiAssetSelect(model, "projectGameUiPanelFrameAssetSelect", "通用面板贴图", "panelFrameAssetId", ["ui"], "不使用面板贴图", helpers)}
          ${renderGameUiAssetSelect(model, "projectGameUiButtonFrameAssetSelect", "按钮默认贴图", "buttonFrameAssetId", ["ui"], "不使用按钮贴图", helpers)}
          ${renderGameUiAssetSelect(model, "projectGameUiButtonHoverFrameAssetSelect", "按钮悬停贴图", "buttonHoverFrameAssetId", ["ui"], "沿用默认按钮贴图", helpers)}
          ${renderGameUiAssetSelect(model, "projectGameUiButtonPressedFrameAssetSelect", "按钮按下贴图", "buttonPressedFrameAssetId", ["ui"], "沿用默认按钮贴图", helpers)}
          ${renderGameUiAssetSelect(model, "projectGameUiButtonDisabledFrameAssetSelect", "按钮禁用贴图", "buttonDisabledFrameAssetId", ["ui"], "沿用默认按钮贴图", helpers)}
          ${renderGameUiAssetSelect(model, "projectGameUiSaveSlotFrameAssetSelect", "存档卡片贴图", "saveSlotFrameAssetId", ["ui"], "不使用存档贴图", helpers)}
          ${renderGameUiAssetSelect(model, "projectGameUiSystemPanelFrameAssetSelect", "系统弹窗贴图", "systemPanelFrameAssetId", ["ui"], "沿用通用面板", helpers)}
          ${renderGameUiAssetSelect(model, "projectGameUiOverlayAssetSelect", "全局叠层纹理", "uiOverlayAssetId", ["ui"], "不使用叠层纹理", helpers)}
        </div>
        ${renderGameUiFrameSliceControls("projectGameUiPanelFrameSlice", "面板 / 存档 / 弹窗九宫格", gameUiConfig.panelFrameSlice, helpers)}
        ${renderGameUiFrameSliceControls("projectGameUiButtonFrameSlice", "按钮九宫格", gameUiConfig.buttonFrameSlice, helpers)}
        <div class="playback-setting-grid dialog-config-grid dialog-config-colors">
          ${renderColorField({ id: "projectGameUiBackgroundColorInput", label: "背景色", value: gameUiConfig.backgroundColor }, helpers)}
          ${renderColorField({ id: "projectGameUiBackgroundAccentColorInput", label: "氛围色", value: gameUiConfig.backgroundAccentColor }, helpers)}
          ${renderColorField({ id: "projectGameUiPanelColorInput", label: "面板色", value: gameUiConfig.panelColor }, helpers)}
          ${renderColorField({ id: "projectGameUiTextColorInput", label: "正文色", value: gameUiConfig.textColor }, helpers)}
          ${renderColorField({ id: "projectGameUiMutedTextColorInput", label: "弱文字", value: gameUiConfig.mutedTextColor }, helpers)}
          ${renderColorField({ id: "projectGameUiAccentColorInput", label: "主强调", value: gameUiConfig.accentColor }, helpers)}
          ${renderColorField({ id: "projectGameUiAccentAltColorInput", label: "副强调", value: gameUiConfig.accentAltColor }, helpers)}
          ${renderColorField({ id: "projectGameUiButtonTextColorInput", label: "按钮文字", value: gameUiConfig.buttonTextColor }, helpers)}
          ${renderColorField({ id: "projectGameUiBorderColorInput", label: "描边色", value: gameUiConfig.borderColor }, helpers)}
        </div>
        <div class="playback-volume-grid dialog-config-ranges">
          ${renderRangeField({ id: "projectGameUiPanelOpacityInput", label: "面板透明度", min: 35, max: 100, value: gameUiConfig.panelOpacity, suffix: "%" }, helpers)}
          ${renderRangeField({ id: "projectGameUiBorderOpacityInput", label: "描边透明度", min: 0, max: 100, value: gameUiConfig.borderOpacity, suffix: "%" }, helpers)}
          ${renderRangeField({ id: "projectGameUiCornerRadiusInput", label: "圆角", min: 4, max: 42, value: gameUiConfig.cornerRadius, suffix: "px" }, helpers)}
          ${renderRangeField({ id: "projectGameUiBackdropBlurInput", label: "背景模糊", min: 0, max: 28, value: gameUiConfig.backdropBlur, suffix: "px" }, helpers)}
          ${renderRangeField({ id: "projectGameUiStageVignetteInput", label: "舞台暗角", min: 0, max: 80, value: gameUiConfig.stageVignette, suffix: "%" }, helpers)}
          ${renderRangeField({ id: "projectGameUiMotionIntensityInput", label: "动态强度", min: 0, max: 100, value: gameUiConfig.motionIntensity, suffix: "%" }, helpers)}
          ${renderRangeField({ id: "projectGameUiTitleBackgroundOpacityInput", label: "标题背景透明度", min: 0, max: 100, value: gameUiConfig.titleBackgroundOpacity, suffix: "%" }, helpers)}
          ${renderRangeField({ id: "projectGameUiPanelFrameOpacityInput", label: "面板贴图透明度", min: 0, max: 100, value: gameUiConfig.panelFrameOpacity, suffix: "%" }, helpers)}
          ${renderRangeField({ id: "projectGameUiButtonFrameOpacityInput", label: "按钮贴图透明度", min: 0, max: 100, value: gameUiConfig.buttonFrameOpacity, suffix: "%" }, helpers)}
          ${renderRangeField({ id: "projectGameUiOverlayOpacityInput", label: "全局纹理透明度", min: 0, max: 100, value: gameUiConfig.uiOverlayOpacity, suffix: "%" }, helpers)}
          ${renderRangeField({ id: "projectGameUiTitleCardOffsetXInput", label: "标题水平偏移", min: -35, max: 35, value: gameUiConfig.titleCardOffsetXPercent, suffix: "%" }, helpers)}
          ${renderRangeField({ id: "projectGameUiTitleCardOffsetYInput", label: "标题垂直偏移", min: -35, max: 35, value: gameUiConfig.titleCardOffsetYPercent, suffix: "%" }, helpers)}
          ${renderRangeField({ id: "projectGameUiLayoutGapInput", label: "主布局间距", min: 8, max: 48, value: gameUiConfig.layoutGap, suffix: "px" }, helpers)}
          ${renderRangeField({ id: "projectGameUiSidePanelWidthInput", label: "侧栏宽度", min: 240, max: 460, step: 4, value: gameUiConfig.sidePanelWidth, suffix: "px" }, helpers)}
        </div>
        <div class="detail-actions">
          <button class="toolbar-button toolbar-button-primary" data-action="save-project-game-ui-config">
            保存成品 UI 皮肤
          </button>
          <button class="toolbar-button" data-action="export-build" data-export-target="web">
            导出网页包检查外观
          </button>
        </div>
        <div class="detail-meta">当前覆盖标题页、系统菜单、存档/读档、EXTRA/图鉴弹窗、侧栏、按钮、HUD、布局位置、UI 贴图绑定、九宫格拉伸和按钮多状态贴图。</div>
      </section>
    `;
  }

  function renderProjectRuntimeSettingsPanel(model = {}, helpers = {}) {
    return `
      <article class="detail-card">
        <strong>成品体验设置</strong>
        <p class="helper-text">这里会直接写进项目文件，网页试玩包和桌面版都会吃这套配置。适合先把“存档规模”“对话框风格”和“成品 UI 皮肤”定下来。</p>
        <div class="detail-stack">
          ${renderLocalizationSection(model, helpers)}
          ${renderSaveSlotSection(model, helpers)}
          ${renderPlaybackDefaultsSection(model, helpers)}
          <div id="projectVariableLibraryPanelHost">
            ${model.variableLibraryPanelHtml ?? ""}
          </div>
          ${renderDialogBoxSection(model, helpers)}
          ${renderGameUiSection(model, helpers)}
        </div>
      </article>
    `;
  }

  function readInputValue(doc, id) {
    return doc?.getElementById?.(id)?.value;
  }

  function readInputChecked(doc, id, fallback = true) {
    const input = doc?.getElementById?.(id);
    return input ? input.checked : fallback;
  }

  function readGameUiFrameSliceFromDocument(doc, idPrefix, fallbackSlice, getSafeGameUiFrameSlice) {
    return getSafeGameUiFrameSlice(
      {
        top: readInputValue(doc, `${idPrefix}TopInput`),
        right: readInputValue(doc, `${idPrefix}RightInput`),
        bottom: readInputValue(doc, `${idPrefix}BottomInput`),
        left: readInputValue(doc, `${idPrefix}LeftInput`),
      },
      fallbackSlice
    );
  }

  function readProjectDialogBoxConfigFromDocument(currentConfig, doc, getProjectDialogBoxConfig) {
    return getProjectDialogBoxConfig({
      dialogBoxConfig: {
        ...currentConfig,
        preset: readInputValue(doc, "projectDialogBoxPresetSelect"),
        shape: readInputValue(doc, "projectDialogBoxShapeSelect"),
        anchor: readInputValue(doc, "projectDialogBoxAnchorSelect"),
        widthPercent: readInputValue(doc, "projectDialogBoxWidthInput"),
        minHeight: readInputValue(doc, "projectDialogBoxHeightInput"),
        offsetXPercent: readInputValue(doc, "projectDialogBoxOffsetXInput"),
        offsetYPercent: readInputValue(doc, "projectDialogBoxOffsetYInput"),
        backgroundColor: readInputValue(doc, "projectDialogBoxBackgroundColorInput"),
        backgroundOpacity: readInputValue(doc, "projectDialogBoxBackgroundOpacityInput"),
        borderColor: readInputValue(doc, "projectDialogBoxBorderColorInput"),
        borderOpacity: readInputValue(doc, "projectDialogBoxBorderOpacityInput"),
        textColor: readInputValue(doc, "projectDialogBoxTextColorInput"),
        speakerColor: readInputValue(doc, "projectDialogBoxSpeakerColorInput"),
        blurStrength: readInputValue(doc, "projectDialogBoxBlurInput"),
        panelAssetId: readInputValue(doc, "projectDialogBoxAssetSelect"),
        panelAssetOpacity: readInputValue(doc, "projectDialogBoxAssetOpacityInput"),
        panelAssetFit: readInputValue(doc, "projectDialogBoxAssetFitSelect"),
      },
    });
  }

  function readProjectGameUiConfigFromDocument(
    currentConfig,
    doc,
    getProjectGameUiConfig,
    getSafeGameUiFrameSlice
  ) {
    return getProjectGameUiConfig({
      gameUiConfig: {
        ...currentConfig,
        preset: readInputValue(doc, "projectGameUiPresetSelect"),
        layoutPreset: readInputValue(doc, "projectGameUiLayoutPresetSelect"),
        titleLayout: readInputValue(doc, "projectGameUiTitleLayoutSelect"),
        fontStyle: readInputValue(doc, "projectGameUiFontStyleSelect"),
        fontFamily: readInputValue(doc, "projectGameUiFontFamilyInput"),
        fontAssetId: readInputValue(doc, "projectGameUiFontAssetSelect"),
        surfaceStyle: readInputValue(doc, "projectGameUiSurfaceStyleSelect"),
        brandMode: readInputValue(doc, "projectGameUiBrandModeSelect"),
        sidePanelMode: readInputValue(doc, "projectGameUiSidePanelModeSelect"),
        sidePanelPosition: readInputValue(doc, "projectGameUiSidePanelPositionSelect"),
        topbarPosition: readInputValue(doc, "projectGameUiTopbarPositionSelect"),
        hudPosition: readInputValue(doc, "projectGameUiHudPositionSelect"),
        titleCardAnchor: readInputValue(doc, "projectGameUiTitleCardAnchorSelect"),
        titleCardOffsetXPercent: readInputValue(doc, "projectGameUiTitleCardOffsetXInput"),
        titleCardOffsetYPercent: readInputValue(doc, "projectGameUiTitleCardOffsetYInput"),
        layoutGap: readInputValue(doc, "projectGameUiLayoutGapInput"),
        sidePanelWidth: readInputValue(doc, "projectGameUiSidePanelWidthInput"),
        titleBackgroundAssetId: readInputValue(doc, "projectGameUiTitleBackgroundAssetSelect"),
        titleBackgroundFit: readInputValue(doc, "projectGameUiTitleBackgroundFitSelect"),
        titleBackgroundOpacity: readInputValue(doc, "projectGameUiTitleBackgroundOpacityInput"),
        titleLogoAssetId: readInputValue(doc, "projectGameUiTitleLogoAssetSelect"),
        panelFrameAssetId: readInputValue(doc, "projectGameUiPanelFrameAssetSelect"),
        panelFrameOpacity: readInputValue(doc, "projectGameUiPanelFrameOpacityInput"),
        panelFrameSlice: readGameUiFrameSliceFromDocument(
          doc,
          "projectGameUiPanelFrameSlice",
          currentConfig.panelFrameSlice,
          getSafeGameUiFrameSlice
        ),
        buttonFrameAssetId: readInputValue(doc, "projectGameUiButtonFrameAssetSelect"),
        buttonHoverFrameAssetId: readInputValue(doc, "projectGameUiButtonHoverFrameAssetSelect"),
        buttonPressedFrameAssetId: readInputValue(doc, "projectGameUiButtonPressedFrameAssetSelect"),
        buttonDisabledFrameAssetId: readInputValue(doc, "projectGameUiButtonDisabledFrameAssetSelect"),
        buttonFrameOpacity: readInputValue(doc, "projectGameUiButtonFrameOpacityInput"),
        buttonFrameSlice: readGameUiFrameSliceFromDocument(
          doc,
          "projectGameUiButtonFrameSlice",
          currentConfig.buttonFrameSlice,
          getSafeGameUiFrameSlice
        ),
        saveSlotFrameAssetId: readInputValue(doc, "projectGameUiSaveSlotFrameAssetSelect"),
        systemPanelFrameAssetId: readInputValue(doc, "projectGameUiSystemPanelFrameAssetSelect"),
        uiOverlayAssetId: readInputValue(doc, "projectGameUiOverlayAssetSelect"),
        uiOverlayOpacity: readInputValue(doc, "projectGameUiOverlayOpacityInput"),
        backgroundColor: readInputValue(doc, "projectGameUiBackgroundColorInput"),
        backgroundAccentColor: readInputValue(doc, "projectGameUiBackgroundAccentColorInput"),
        panelColor: readInputValue(doc, "projectGameUiPanelColorInput"),
        panelOpacity: readInputValue(doc, "projectGameUiPanelOpacityInput"),
        textColor: readInputValue(doc, "projectGameUiTextColorInput"),
        mutedTextColor: readInputValue(doc, "projectGameUiMutedTextColorInput"),
        accentColor: readInputValue(doc, "projectGameUiAccentColorInput"),
        accentAltColor: readInputValue(doc, "projectGameUiAccentAltColorInput"),
        buttonTextColor: readInputValue(doc, "projectGameUiButtonTextColorInput"),
        borderColor: readInputValue(doc, "projectGameUiBorderColorInput"),
        borderOpacity: readInputValue(doc, "projectGameUiBorderOpacityInput"),
        cornerRadius: readInputValue(doc, "projectGameUiCornerRadiusInput"),
        backdropBlur: readInputValue(doc, "projectGameUiBackdropBlurInput"),
        stageVignette: readInputValue(doc, "projectGameUiStageVignetteInput"),
        motionIntensity: readInputValue(doc, "projectGameUiMotionIntensityInput"),
      },
    });
  }

  function readProjectRuntimePlaybackDefaultsFromDocument(currentSettings, doc, getProjectRuntimeSettings) {
    return getProjectRuntimeSettings({
      runtimeSettings: {
        ...currentSettings,
        defaultTextSpeed: readInputValue(doc, "projectRuntimeDefaultTextSpeedSelect"),
        defaultDialogTheme: readInputValue(doc, "projectRuntimeDefaultDialogThemeSelect"),
        defaultUiThemeMode: readInputValue(doc, "projectRuntimeDefaultUiThemeModeSelect"),
        performanceProfile: readInputValue(doc, "projectRuntimePerformanceProfileSelect"),
        defaultBgmVolume: readInputValue(doc, "projectRuntimeDefaultBgmVolumeInput"),
        defaultSfxVolume: readInputValue(doc, "projectRuntimeDefaultSfxVolumeInput"),
        defaultVoiceVolume: readInputValue(doc, "projectRuntimeDefaultVoiceVolumeInput"),
        defaultVoiceDuckingRatio: readInputValue(doc, "projectRuntimeDefaultVoiceDuckingRatioInput"),
        defaultVoiceEnabled: readInputChecked(doc, "projectRuntimeDefaultVoiceEnabledInput", true),
        defaultVoiceDuckingEnabled: readInputChecked(doc, "projectRuntimeDefaultVoiceDuckingEnabledInput", true),
      },
    });
  }

  global.CanvasiaEditorProjectRuntimeSettingsPanel = Object.freeze({
    buildGameUiAssetSelectOptions,
    readGameUiFrameSliceFromDocument,
    readProjectDialogBoxConfigFromDocument,
    readProjectGameUiConfigFromDocument,
    readProjectRuntimePlaybackDefaultsFromDocument,
    renderDialogBoxReadabilityCard,
    renderGameUiFrameSliceControls,
    renderProjectRuntimeSettingsPanel,
  });
})(typeof window !== "undefined" ? window : globalThis);
