(function attachDashboardPrimaryActionTools(global) {
  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function toDatasetEntries(action = {}) {
    return Object.entries({
      ...(action.dataset ?? {}),
      ...(action.screen ? { screen: action.screen } : {}),
      ...(action.stepIndex ? { stepIndex: action.stepIndex } : {}),
    }).filter(([, value]) => value !== undefined && value !== null && value !== "");
  }

  function buildDashboardPrimaryActionModel(options = {}) {
    if (options.isBlankProject) {
      const disabled = Boolean(options.chapterCreateInFlight);
      return [
        {
          label: "创建第一章和第一场",
          action: "create-first-chapter",
          primary: true,
          disabled,
          busy: disabled,
        },
        {
          label: "自定义名字再创建",
          action: "create-first-chapter-custom",
          disabled,
          busy: disabled,
        },
        {
          label: "看 6 步教程",
          action: "open-beginner-tutorial",
          dataset: { stepIndex: "1" },
        },
      ];
    }

    const oneClickPolishDigest = options.oneClickPolishDigest ?? null;
    const projectPolishDigest = options.projectPolishDigest ?? null;
    const projectReadableDigest = options.projectReadableDigest ?? null;
    const oneClickPolishDisabled = Boolean(
      options.projectOneClickPolishInFlight || (oneClickPolishDigest ? !oneClickPolishDigest.canApply : false)
    );
    const projectPolishDisabled = Boolean(
      options.projectPresentationPolishInFlight || (projectPolishDigest ? !projectPolishDigest.canApply : false)
    );
    const projectReadableDisabled = Boolean(
      options.projectReadableSplitInFlight || (projectReadableDigest ? !projectReadableDigest.canApply : false)
    );
    const actions = [
      {
        label: "进入剧情编辑",
        action: "switch-screen",
        screen: "story",
        primary: true,
      },
      {
        label: options.projectOneClickPolishInFlight
          ? "发布前整理中..."
          : oneClickPolishDigest?.actionLabel ?? "一键发布前整理",
        action: "run-project-one-click-polish",
        primary: true,
        disabled: oneClickPolishDisabled,
        title: oneClickPolishDigest?.helperText ?? "依次整理长文本、基础演出和音频范围，适合发布前快速补齐。",
      },
    ];

    if (options.hasOneClickPolishReceipt) {
      actions.push(
        {
          label: "复制整理回执",
          action: "copy-project-one-click-polish-receipt-summary",
        },
        {
          label: "导出整理回执",
          action: "export-project-one-click-polish-receipt",
        }
      );
    }

    actions.push(
      {
        label: options.projectPresentationPolishInFlight ? "全项目润色中..." : projectPolishDigest?.actionLabel ?? "润色全项目演出",
        action: "polish-project-presentation",
        disabled: projectPolishDisabled,
        title: projectPolishDigest?.helperText ?? "批量补齐全项目基础转场、淡入淡出、音量和文字速度。",
      },
      {
        label: options.projectReadableSplitInFlight ? "长文本整理中..." : projectReadableDigest?.actionLabel ?? "整理全项目长文本",
        action: "split-readable-project",
        disabled: projectReadableDisabled,
        title: projectReadableDigest?.helperText ?? "批量把过长台词和旁白拆成更适合阅读的卡片。",
      },
      {
        label: "查看试玩页",
        action: "switch-screen",
        screen: "preview",
      },
      {
        label: "打开素材页",
        action: "switch-screen",
        screen: "assets",
      },
      {
        label: "打开新手教程",
        action: "open-beginner-tutorial",
      }
    );

    return actions;
  }

  function renderDashboardPrimaryActionButton(action = {}, helpers = {}) {
    const html = typeof helpers.escapeHtml === "function" ? helpers.escapeHtml : escapeHtml;
    const className = `toolbar-button${action.primary ? " toolbar-button-primary" : ""}`;
    const datasetMarkup = toDatasetEntries(action)
      .map(([key, value]) => ` data-${key.replace(/[A-Z]/g, (char) => `-${char.toLowerCase()}`)}="${html(value)}"`)
      .join("");
    const disabledMarkup = action.disabled ? ' disabled aria-disabled="true"' : "";
    const busyMarkup = action.busy ? ' aria-busy="true"' : "";
    const titleMarkup = action.title ? ` title="${html(action.title)}"` : "";

    return `
      <button class="${className}" data-action="${html(action.action ?? "")}"${datasetMarkup}${disabledMarkup}${busyMarkup}${titleMarkup}>
        ${html(action.label ?? "继续")}
      </button>
    `;
  }

  function renderDashboardPrimaryActions(options = {}, helpers = {}) {
    return buildDashboardPrimaryActionModel(options)
      .map((action) => renderDashboardPrimaryActionButton(action, helpers))
      .join("");
  }

  global.CanvasiaEditorDashboardPrimaryActions = Object.freeze({
    buildDashboardPrimaryActionModel,
    renderDashboardPrimaryActionButton,
    renderDashboardPrimaryActions,
  });
})(typeof window !== "undefined" ? window : globalThis);
