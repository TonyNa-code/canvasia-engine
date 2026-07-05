(function attachDialogBoxReadabilityTools(global) {
  const DEFAULT_DIALOG_BOX_CONFIG = Object.freeze({
    preset: "moonlight",
    shape: "rounded",
    widthPercent: 76,
    minHeight: 148,
    paddingX: 18,
    paddingY: 14,
    backgroundColor: "#0c1422",
    backgroundOpacity: 92,
    borderColor: "#79dcff",
    borderOpacity: 18,
    textColor: "#f3f6ff",
    speakerColor: "#ffffff",
    hintColor: "#c8d6ea",
    blurStrength: 10,
    borderWidth: 1,
    shadowStrength: 30,
    panelAssetId: "",
    panelAssetOpacity: 0,
    panelAssetFit: "cover",
    anchor: "bottom",
    offsetXPercent: 0,
    offsetYPercent: 0,
  });
  const CONTRAST_LIMITS = Object.freeze({
    body: 4.5,
    supporting: 3.8,
  });
  const TEXT_DENSITY_LIMITS = Object.freeze({
    longLineLength: 42,
    heavyLineLength: 64,
    denseAverageLength: 32,
  });

  function getProjectSettingsTools() {
    return global.CanvasiaEditorProjectSettings || {};
  }

  function clamp(value, min, max) {
    const parsed = Number.parseFloat(value ?? "");
    const safeValue = Number.isFinite(parsed) ? parsed : min;
    return Math.min(Math.max(safeValue, min), max);
  }

  function normalizeHexColor(value, fallback = "#ffffff") {
    const text = String(value ?? "").trim();
    if (/^#[0-9a-fA-F]{6}$/.test(text)) {
      return text.toLowerCase();
    }
    return /^#[0-9a-fA-F]{6}$/.test(String(fallback ?? "").trim())
      ? String(fallback).trim().toLowerCase()
      : "#ffffff";
  }

  function normalizeDialogBoxConfig(projectOrData) {
    const project = projectOrData?.project ?? projectOrData ?? {};
    const projectSettingsTools = getProjectSettingsTools();
    if (typeof projectSettingsTools.getProjectDialogBoxConfig === "function") {
      return projectSettingsTools.getProjectDialogBoxConfig(project);
    }

    const source = project.dialogBoxConfig ?? {};
    return {
      ...DEFAULT_DIALOG_BOX_CONFIG,
      ...source,
      widthPercent: clamp(source.widthPercent ?? DEFAULT_DIALOG_BOX_CONFIG.widthPercent, 55, 100),
      minHeight: clamp(source.minHeight ?? DEFAULT_DIALOG_BOX_CONFIG.minHeight, 96, 320),
      paddingX: clamp(source.paddingX ?? DEFAULT_DIALOG_BOX_CONFIG.paddingX, 8, 72),
      paddingY: clamp(source.paddingY ?? DEFAULT_DIALOG_BOX_CONFIG.paddingY, 6, 48),
      backgroundColor: normalizeHexColor(source.backgroundColor, DEFAULT_DIALOG_BOX_CONFIG.backgroundColor),
      backgroundOpacity: clamp(source.backgroundOpacity ?? DEFAULT_DIALOG_BOX_CONFIG.backgroundOpacity, 0, 100),
      textColor: normalizeHexColor(source.textColor, DEFAULT_DIALOG_BOX_CONFIG.textColor),
      speakerColor: normalizeHexColor(source.speakerColor, DEFAULT_DIALOG_BOX_CONFIG.speakerColor),
      hintColor: normalizeHexColor(source.hintColor, DEFAULT_DIALOG_BOX_CONFIG.hintColor),
      blurStrength: clamp(source.blurStrength ?? DEFAULT_DIALOG_BOX_CONFIG.blurStrength, 0, 24),
      panelAssetId: String(source.panelAssetId ?? "").trim(),
      panelAssetOpacity: clamp(source.panelAssetOpacity ?? DEFAULT_DIALOG_BOX_CONFIG.panelAssetOpacity, 0, 100),
      panelAssetFit: source.panelAssetFit === "contain" ? "contain" : "cover",
      anchor: String(source.anchor ?? DEFAULT_DIALOG_BOX_CONFIG.anchor).trim() || DEFAULT_DIALOG_BOX_CONFIG.anchor,
      offsetXPercent: clamp(source.offsetXPercent ?? DEFAULT_DIALOG_BOX_CONFIG.offsetXPercent, -35, 35),
      offsetYPercent: clamp(source.offsetYPercent ?? DEFAULT_DIALOG_BOX_CONFIG.offsetYPercent, -35, 35),
    };
  }

  function getProjectSceneList(data) {
    const scenesById = new Map();
    const addScene = (scene) => {
      if (!scene || typeof scene !== "object") {
        return;
      }
      const sceneId = String(scene.id ?? scene.sceneId ?? "").trim();
      if (sceneId && scenesById.has(sceneId)) {
        return;
      }
      scenesById.set(sceneId || `scene_${scenesById.size + 1}`, scene);
    };

    (Array.isArray(data?.scenes) ? data.scenes : []).forEach(addScene);
    (Array.isArray(data?.chapters) ? data.chapters : []).forEach((chapter) => {
      (Array.isArray(chapter?.scenes) ? chapter.scenes : []).forEach(addScene);
    });
    return Array.from(scenesById.values());
  }

  function normalizeText(value) {
    return String(value ?? "")
      .replace(/\r\n/g, "\n")
      .replace(/[ \t]+/g, " ")
      .trim();
  }

  function collectBlockTextEntries(block) {
    const entries = [];
    const blockType = String(block?.type ?? "").trim();
    if (["dialogue", "narration", "text"].includes(blockType)) {
      const text = normalizeText(block.text ?? block.content ?? block.line);
      if (text) {
        entries.push({
          type: blockType,
          text,
          lineCount: text.split("\n").length,
        });
      }
    }

    if (blockType === "choice" && Array.isArray(block?.choices)) {
      block.choices.forEach((choice) => {
        const text = normalizeText(choice.text ?? choice.label ?? choice.title);
        if (text) {
          entries.push({
            type: "choice",
            text,
            lineCount: text.split("\n").length,
          });
        }
      });
    }
    return entries;
  }

  function analyzeTextDensity(data) {
    const entries = [];
    getProjectSceneList(data).forEach((scene) => {
      (Array.isArray(scene?.blocks) ? scene.blocks : []).forEach((block) => {
        entries.push(...collectBlockTextEntries(block));
      });
    });

    const lengths = entries.map((entry) => entry.text.length);
    const maxLength = lengths.length > 0 ? Math.max(...lengths) : 0;
    const totalLength = lengths.reduce((sum, value) => sum + value, 0);
    const averageLength = lengths.length > 0 ? totalLength / lengths.length : 0;
    const longTextCount = lengths.filter((length) => length >= TEXT_DENSITY_LIMITS.longLineLength).length;
    const heavyTextCount = lengths.filter((length) => length >= TEXT_DENSITY_LIMITS.heavyLineLength).length;
    const multilineCount = entries.filter((entry) => entry.lineCount > 1).length;

    return {
      textBlockCount: entries.length,
      averageLength,
      maxLength,
      longTextCount,
      heavyTextCount,
      multilineCount,
      isDense:
        heavyTextCount > 0 ||
        multilineCount > 0 ||
        averageLength >= TEXT_DENSITY_LIMITS.denseAverageLength,
    };
  }

  function hexToRgb(hexColor) {
    const safeColor = normalizeHexColor(hexColor);
    return {
      red: Number.parseInt(safeColor.slice(1, 3), 16),
      green: Number.parseInt(safeColor.slice(3, 5), 16),
      blue: Number.parseInt(safeColor.slice(5, 7), 16),
    };
  }

  function srgbToLinear(channel) {
    const value = channel / 255;
    return value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  }

  function getRelativeLuminance(hexColor) {
    const rgb = hexToRgb(hexColor);
    return (
      0.2126 * srgbToLinear(rgb.red) +
      0.7152 * srgbToLinear(rgb.green) +
      0.0722 * srgbToLinear(rgb.blue)
    );
  }

  function getContrastRatio(foreground, background) {
    const first = getRelativeLuminance(foreground);
    const second = getRelativeLuminance(background);
    const lighter = Math.max(first, second);
    const darker = Math.min(first, second);
    return (lighter + 0.05) / (darker + 0.05);
  }

  function getReadablePalette(backgroundColor) {
    const isDarkSurface = getRelativeLuminance(backgroundColor) < 0.42;
    return isDarkSurface
      ? {
          textColor: "#f5f7ff",
          speakerColor: "#ffffff",
          hintColor: "#d8e2f2",
        }
      : {
          textColor: "#2f2218",
          speakerColor: "#5f3d2a",
          hintColor: "#6d5d53",
        };
  }

  function getReadabilityTargets(textStats, config) {
    const isDense = textStats.isDense;
    const hasText = textStats.textBlockCount > 0;
    return {
      opacity: hasText ? (isDense ? 86 : 72) : 0,
      widthPercent: isDense ? 78 : 72,
      minHeight: isDense ? 168 : 140,
      paddingX: isDense ? 18 : 16,
      paddingY: isDense ? 14 : 12,
      blurStrength: config.backgroundOpacity > 0 || hasText ? 6 : 0,
    };
  }

  function buildIssue(id, severity, title, detail) {
    return { id, severity, title, detail };
  }

  function buildDialogBoxReadabilityReport(data = {}) {
    const config = normalizeDialogBoxConfig(data);
    const textStats = analyzeTextDensity(data);
    const targets = getReadabilityTargets(textStats, config);
    const hasPanelAsset = Boolean(config.panelAssetId) && config.panelAssetOpacity >= 35;
    const needsOpaqueSurface =
      !hasPanelAsset && textStats.textBlockCount > 0 && config.backgroundOpacity < targets.opacity;
    const textContrastRatio = getContrastRatio(config.textColor, config.backgroundColor);
    const speakerContrastRatio = getContrastRatio(config.speakerColor, config.backgroundColor);
    const issues = [];

    if (needsOpaqueSurface) {
      issues.push(
        buildIssue(
          "background-opacity",
          config.backgroundOpacity < 35 ? "danger" : "warning",
          "文本框底色太透明",
          `当前底色透明度 ${Math.round(config.backgroundOpacity)}%，长文本和复杂背景下可能看不清。`
        )
      );
    }

    if ((config.backgroundOpacity >= 35 || hasPanelAsset || needsOpaqueSurface) && textContrastRatio < CONTRAST_LIMITS.body) {
      issues.push(
        buildIssue(
          "text-contrast",
          "danger",
          "正文和底色对比不足",
          `当前对比度约 ${textContrastRatio.toFixed(1)}:1，建议至少 ${CONTRAST_LIMITS.body}:1。`
        )
      );
    }

    if ((config.backgroundOpacity >= 35 || hasPanelAsset || needsOpaqueSurface) && speakerContrastRatio < CONTRAST_LIMITS.supporting) {
      issues.push(
        buildIssue(
          "speaker-contrast",
          "warning",
          "角色名颜色偏弱",
          `名字颜色对比度约 ${speakerContrastRatio.toFixed(1)}:1，深浅模式切换时可能发虚。`
        )
      );
    }

    if (textStats.textBlockCount > 0 && config.widthPercent < targets.widthPercent) {
      issues.push(
        buildIssue(
          "width",
          "warning",
          "文本框宽度偏窄",
          `当前宽度 ${Math.round(config.widthPercent)}%，长句会更容易换行或挤压。`
        )
      );
    }

    if (textStats.isDense && config.minHeight < targets.minHeight) {
      issues.push(
        buildIssue(
          "height",
          "warning",
          "文本框高度偏矮",
          `当前高度 ${Math.round(config.minHeight)}px，项目里已有较长或多行文本。`
        )
      );
    }

    if (textStats.textBlockCount > 0 && (config.paddingX < targets.paddingX || config.paddingY < targets.paddingY)) {
      issues.push(
        buildIssue(
          "padding",
          "warning",
          "文本内边距偏紧",
          `当前内边距 ${Math.round(config.paddingX)}px / ${Math.round(config.paddingY)}px，阅读时会显得拥挤。`
        )
      );
    }

    const level = issues.some((issue) => issue.severity === "danger")
      ? "danger"
      : issues.length > 0
        ? "warning"
        : "ready";

    return {
      level,
      config,
      issues,
      hasPanelAsset,
      targets,
      metrics: {
        textBlockCount: textStats.textBlockCount,
        averageLength: Number(textStats.averageLength.toFixed(1)),
        maxLength: textStats.maxLength,
        longTextCount: textStats.longTextCount,
        heavyTextCount: textStats.heavyTextCount,
        multilineCount: textStats.multilineCount,
        textContrastRatio: Number(textContrastRatio.toFixed(2)),
        speakerContrastRatio: Number(speakerContrastRatio.toFixed(2)),
      },
    };
  }

  function addOperation(operations, field, fromValue, toValue, label) {
    if (fromValue === toValue) {
      return false;
    }
    operations.push({ field, fromValue, toValue, label });
    return true;
  }

  function buildDialogBoxReadabilityAutoFixPlan(data = {}) {
    const report = buildDialogBoxReadabilityReport(data);
    const nextConfig = { ...report.config };
    const operations = [];
    const targets = report.targets;

    if (!report.hasPanelAsset && report.metrics.textBlockCount > 0 && nextConfig.backgroundOpacity < targets.opacity) {
      addOperation(
        operations,
        "backgroundOpacity",
        nextConfig.backgroundOpacity,
        targets.opacity,
        "提高文本框底色透明度"
      );
      nextConfig.backgroundOpacity = targets.opacity;
    }

    if (nextConfig.widthPercent < targets.widthPercent) {
      addOperation(operations, "widthPercent", nextConfig.widthPercent, targets.widthPercent, "放宽文本框宽度");
      nextConfig.widthPercent = targets.widthPercent;
    }

    if (nextConfig.minHeight < targets.minHeight) {
      addOperation(operations, "minHeight", nextConfig.minHeight, targets.minHeight, "增加文本框高度");
      nextConfig.minHeight = targets.minHeight;
    }

    if (nextConfig.paddingX < targets.paddingX) {
      addOperation(operations, "paddingX", nextConfig.paddingX, targets.paddingX, "补水平内边距");
      nextConfig.paddingX = targets.paddingX;
    }

    if (nextConfig.paddingY < targets.paddingY) {
      addOperation(operations, "paddingY", nextConfig.paddingY, targets.paddingY, "补垂直内边距");
      nextConfig.paddingY = targets.paddingY;
    }

    if (!report.hasPanelAsset && nextConfig.backgroundOpacity > 0 && nextConfig.blurStrength < targets.blurStrength) {
      addOperation(operations, "blurStrength", nextConfig.blurStrength, targets.blurStrength, "补轻微背景模糊");
      nextConfig.blurStrength = targets.blurStrength;
    }

    const palette = getReadablePalette(nextConfig.backgroundColor);
    const nextTextContrastRatio = getContrastRatio(nextConfig.textColor, nextConfig.backgroundColor);
    const nextSpeakerContrastRatio = getContrastRatio(nextConfig.speakerColor, nextConfig.backgroundColor);
    if ((nextConfig.backgroundOpacity >= 35 || report.hasPanelAsset) && nextTextContrastRatio < CONTRAST_LIMITS.body) {
      addOperation(operations, "textColor", nextConfig.textColor, palette.textColor, "提高正文对比度");
      nextConfig.textColor = palette.textColor;
    }
    if ((nextConfig.backgroundOpacity >= 35 || report.hasPanelAsset) && nextSpeakerContrastRatio < CONTRAST_LIMITS.supporting) {
      addOperation(operations, "speakerColor", nextConfig.speakerColor, palette.speakerColor, "提高名字对比度");
      nextConfig.speakerColor = palette.speakerColor;
    }
    if ((nextConfig.backgroundOpacity >= 35 || report.hasPanelAsset) && getContrastRatio(nextConfig.hintColor, nextConfig.backgroundColor) < 3) {
      addOperation(operations, "hintColor", nextConfig.hintColor, palette.hintColor, "提高提示文字对比度");
      nextConfig.hintColor = palette.hintColor;
    }

    if (operations.length > 0) {
      nextConfig.preset = "custom";
    }

    return {
      changed: operations.length > 0,
      dialogBoxConfig: nextConfig,
      operations,
      report,
      summary:
        operations.length > 0
          ? `已准备 ${operations.length} 项文本框可读性增强`
          : "文本框可读性已经比较稳",
    };
  }

  function applyDialogBoxReadabilityPatch(projectOrData, plan = buildDialogBoxReadabilityAutoFixPlan(projectOrData)) {
    const project = projectOrData?.project ?? projectOrData ?? {};
    return {
      ...project,
      dialogBoxConfig: {
        ...(project.dialogBoxConfig ?? {}),
        ...plan.dialogBoxConfig,
      },
    };
  }

  function getDialogBoxReadabilityDigest(reportOrData) {
    const report = reportOrData?.metrics && Array.isArray(reportOrData?.issues)
      ? reportOrData
      : buildDialogBoxReadabilityReport(reportOrData);
    const issueCount = report.issues.length;
    const actionLabel = issueCount > 0 ? "一键增强文本框可读性" : "文本框可读性已达标";
    const badgeLabel =
      report.level === "danger"
        ? `${issueCount} 项高风险`
        : report.level === "warning"
          ? `${issueCount} 项建议优化`
          : "可读性稳";
    const helperText =
      issueCount > 0
        ? "只会补透明度、宽高、内边距和文字对比，不会改贴图、锚点、偏移或剧情。"
        : "当前文本框对长句、多行文本和浅深色背景都比较安全。";

    return {
      level: report.level,
      canApply: issueCount > 0,
      issueCount,
      actionLabel,
      badgeLabel,
      helperText,
      primaryIssue: report.issues[0]?.title ?? "文本框可读性已达标",
      metrics: report.metrics,
    };
  }

  global.CanvasiaEditorDialogBoxReadability = Object.freeze({
    CONTRAST_LIMITS,
    TEXT_DENSITY_LIMITS,
    normalizeDialogBoxConfig,
    analyzeTextDensity,
    getContrastRatio,
    buildDialogBoxReadabilityReport,
    buildDialogBoxReadabilityAutoFixPlan,
    applyDialogBoxReadabilityPatch,
    getDialogBoxReadabilityDigest,
  });
})(typeof window !== "undefined" ? window : globalThis);
