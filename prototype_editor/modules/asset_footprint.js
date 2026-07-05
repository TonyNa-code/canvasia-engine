(function attachAssetFootprintTools(global) {
  const MIB = 1024 * 1024;

  const CATEGORY_DEFINITIONS = Object.freeze({
    image: Object.freeze({
      label: "图片",
      types: Object.freeze(["background", "sprite", "cg", "ui"]),
      warnBytes: 10 * MIB,
      dangerBytes: 32 * MIB,
      suggestion: "背景、CG 和 UI 图层优先导出 WebP/JPEG 预览版，透明图再用 PNGQuant 或 WebP 压缩。",
    }),
    audio: Object.freeze({
      label: "音频",
      types: Object.freeze(["bgm", "sfx", "voice"]),
      warnBytes: 25 * MIB,
      dangerBytes: 80 * MIB,
      suggestion: "BGM、语音和音效建议转成 OGG/MP3，并按章节或角色分组，减少首次加载压力。",
    }),
    video: Object.freeze({
      label: "视频",
      types: Object.freeze(["video"]),
      warnBytes: 150 * MIB,
      dangerBytes: 500 * MIB,
      suggestion: "OP、ED 和过场视频建议重新编码 H.264/H.265，并控制码率、分辨率和时长。",
    }),
    live2d: Object.freeze({
      label: "Live2D",
      types: Object.freeze(["live2d"]),
      warnBytes: 50 * MIB,
      dangerBytes: 180 * MIB,
      suggestion: "Live2D 模型可以清理未用动作和贴图，并保留源工程在项目外归档。",
    }),
    model3d: Object.freeze({
      label: "3D 资产",
      types: Object.freeze(["model3d", "scene3d"]),
      warnBytes: 120 * MIB,
      dangerBytes: 500 * MIB,
      suggestion: "3D 模型和场景建议压缩贴图、减少内嵌大纹理，并单独做低配版本。",
    }),
    font: Object.freeze({
      label: "字体",
      types: Object.freeze(["font"]),
      warnBytes: 20 * MIB,
      dangerBytes: 60 * MIB,
      suggestion: "字体建议确认授权后做子集化，只保留项目实际需要的字重和字符范围。",
    }),
    other: Object.freeze({
      label: "其他",
      types: Object.freeze([]),
      warnBytes: 50 * MIB,
      dangerBytes: 200 * MIB,
      suggestion: "其他素材建议确认是否真的进入成品包，不需要的先移到项目外归档。",
    }),
  });

  const ASSET_TYPE_LABELS = Object.freeze({
    background: "背景",
    sprite: "立绘",
    cg: "CG",
    bgm: "音乐",
    sfx: "音效",
    voice: "语音",
    video: "视频",
    ui: "界面素材",
    font: "字体",
    live2d: "Live2D",
    model3d: "3D 模型",
    scene3d: "3D 场景",
  });

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function toFiniteBytes(value) {
    if (typeof value === "string") {
      const cleanValue = value.replace(/,/g, "").trim();
      if (!cleanValue) {
        return 0;
      }
      const unitMatch = cleanValue.match(/^([0-9]+(?:\.[0-9]+)?)\s*(b|kb|kib|mb|mib|gb|gib)$/i);
      if (unitMatch) {
        const amount = Number(unitMatch[1]);
        const unit = unitMatch[2].toLowerCase();
        const multiplier =
          unit === "gb" || unit === "gib"
            ? 1024 * MIB
            : unit === "mb" || unit === "mib"
              ? MIB
              : unit === "kb" || unit === "kib"
                ? 1024
                : 1;
        return Number.isFinite(amount) && amount > 0 ? Math.round(amount * multiplier) : 0;
      }
      const parsed = Number(cleanValue);
      return Number.isFinite(parsed) && parsed > 0 ? Math.round(parsed) : 0;
    }
    const parsed = Number(value);
    return Number.isFinite(parsed) && parsed > 0 ? Math.round(parsed) : 0;
  }

  function getAssetList(data = {}) {
    if (Array.isArray(data.assetList)) {
      return data.assetList;
    }
    if (Array.isArray(data.assets?.assets)) {
      return data.assets.assets;
    }
    if (Array.isArray(data.assets)) {
      return data.assets;
    }
    return [];
  }

  function formatBytes(bytes) {
    const size = Number(bytes);
    if (!Number.isFinite(size) || size < 0) {
      return "未知";
    }
    if (size < 1024) {
      return `${Math.round(size)} B`;
    }
    if (size < MIB) {
      return `${(size / 1024).toFixed(size < 10 * 1024 ? 1 : 0)} KB`;
    }
    if (size < 1024 * MIB) {
      return `${(size / MIB).toFixed(size < 10 * MIB ? 1 : 0)} MB`;
    }
    return `${(size / (1024 * MIB)).toFixed(2)} GB`;
  }

  function getAssetTypeLabel(type) {
    const cleanType = String(type ?? "").trim();
    return ASSET_TYPE_LABELS[cleanType] ?? cleanText(cleanType, "素材");
  }

  function normalizeAssetSizeBytes(asset = {}) {
    return [
      asset.fileSizeBytes,
      asset.sizeBytes,
      asset.byteSize,
      asset.fileSize,
      asset.size,
    ].reduce((current, candidate) => current || toFiniteBytes(candidate), 0);
  }

  function getAssetFootprintCategory(asset = {}) {
    const type = String(asset.type ?? "").trim();
    const match = Object.entries(CATEGORY_DEFINITIONS).find(([, definition]) => definition.types.includes(type));
    return match ? match[0] : "other";
  }

  function getUnusedAssetIdSet(options = {}) {
    if (options.unusedAssetIds && typeof options.unusedAssetIds.has === "function") {
      return new Set(Array.from(options.unusedAssetIds).map((id) => String(id)));
    }
    if (Array.isArray(options.unusedAssetIds)) {
      return new Set(options.unusedAssetIds.map((id) => String(id)));
    }
    return new Set();
  }

  function isPlaceholderAsset(asset = {}) {
    const text = [
      asset.name,
      asset.path,
      asset.description,
      ...toArray(asset.tags),
    ]
      .map((value) => String(value ?? "").toLowerCase())
      .join(" ");
    return /(placeholder|占位|临时|待替换|sample)/i.test(text);
  }

  function normalizeAssetRecord(asset, options = {}) {
    const id = cleanText(asset.id, "");
    const category = getAssetFootprintCategory(asset);
    const definition = CATEGORY_DEFINITIONS[category] ?? CATEGORY_DEFINITIONS.other;
    const sizeBytes = normalizeAssetSizeBytes(asset);
    const fileExists = asset.fileExists !== false;
    const missingSize = fileExists && sizeBytes <= 0;
    const unusedAssetIds = options.unusedAssetIds ?? new Set();
    const unused = id ? unusedAssetIds.has(id) : false;
    const risk =
      sizeBytes >= definition.dangerBytes
        ? "danger"
        : sizeBytes >= definition.warnBytes
          ? "warn"
          : "ready";

    return {
      id,
      name: cleanText(asset.name, id || "未命名素材"),
      path: cleanText(asset.path || asset.relativePath || asset.publicUrl, ""),
      type: cleanText(asset.type, "other"),
      typeLabel: getAssetTypeLabel(asset.type),
      category,
      categoryLabel: definition.label,
      sizeBytes,
      sizeLabel: formatBytes(sizeBytes),
      fileExists,
      missingSize,
      unused,
      placeholder: isPlaceholderAsset(asset),
      risk,
      suggestion: definition.suggestion,
      warnBytes: definition.warnBytes,
      dangerBytes: definition.dangerBytes,
    };
  }

  function buildCategorySummary(records) {
    return Object.entries(CATEGORY_DEFINITIONS)
      .map(([category, definition]) => {
        const assets = records.filter((record) => record.category === category);
        const totalBytes = assets.reduce((sum, record) => sum + record.sizeBytes, 0);
        const riskCount = assets.filter((record) => record.risk !== "ready").length;
        return {
          category,
          label: definition.label,
          count: assets.length,
          totalBytes,
          totalLabel: formatBytes(totalBytes),
          riskCount,
          largest: assets.slice().sort((left, right) => right.sizeBytes - left.sizeBytes)[0] ?? null,
        };
      })
      .filter((entry) => entry.count > 0)
      .sort((left, right) => right.totalBytes - left.totalBytes || right.riskCount - left.riskCount);
  }

  function pushWarning(warnings, warning) {
    warnings.push({
      code: warning.code,
      severity: warning.severity ?? "tip",
      title: warning.title,
      detail: warning.detail,
      assetId: warning.assetId ?? "",
      assetName: warning.assetName ?? "",
      actionHint: warning.actionHint ?? "",
    });
  }

  function buildAssetFootprintReport(data = {}, options = {}) {
    const unusedAssetIds = getUnusedAssetIdSet(options);
    const totalWarnBytes = toFiniteBytes(options.totalWarnBytes) || 600 * MIB;
    const totalDangerBytes = toFiniteBytes(options.totalDangerBytes) || 1536 * MIB;
    const records = getAssetList(data)
      .map((asset) => normalizeAssetRecord(asset, { unusedAssetIds }))
      .sort((left, right) => right.sizeBytes - left.sizeBytes || left.name.localeCompare(right.name, "zh-Hans-CN"));
    const totalBytes = records.reduce((sum, record) => sum + record.sizeBytes, 0);
    const topAssets = records.slice(0, 12);
    const categories = buildCategorySummary(records);
    const warnings = [];

    if (totalBytes >= totalDangerBytes) {
      pushWarning(warnings, {
        code: "total_footprint_danger",
        severity: "danger",
        title: "发布包体积已经明显偏大",
        detail: `当前已记录素材合计 ${formatBytes(totalBytes)}，建议先压缩大视频、大音频和超大图片再正式发包。`,
        actionHint: "先处理排行前 5 的素材，通常收益最大。",
      });
    } else if (totalBytes >= totalWarnBytes) {
      pushWarning(warnings, {
        code: "total_footprint_warn",
        severity: "warn",
        title: "发布包体积接近需要控制的区间",
        detail: `当前已记录素材合计 ${formatBytes(totalBytes)}，正式发布前建议做一轮压缩体检。`,
        actionHint: "优先压缩视频、BGM 和高分辨率 CG。",
      });
    }

    records
      .filter((record) => record.risk !== "ready")
      .slice(0, 8)
      .forEach((record) => {
        pushWarning(warnings, {
          code: `large_${record.category}`,
          severity: record.risk === "danger" ? "danger" : "warn",
          title: `${record.categoryLabel}素材体积偏大`,
          detail: `${record.name} 当前 ${record.sizeLabel}，${record.suggestion}`,
          assetId: record.id,
          assetName: record.name,
          actionHint: "可以先保留源文件归档，再导入一份发布用压缩版。",
        });
      });

    const missingSizeCount = records.filter((record) => record.missingSize).length;
    if (missingSizeCount > 0) {
      pushWarning(warnings, {
        code: "missing_size_metadata",
        severity: "warn",
        title: "部分素材缺少体积记录",
        detail: `有 ${missingSizeCount} 个已导入素材没有记录文件大小，体积报告会低估真实包体。`,
        actionHint: "重新导入或替换这些素材后，编辑器会补齐文件大小。",
      });
    }

    const largeUnused = records.filter((record) => record.unused && record.sizeBytes >= 10 * MIB);
    if (largeUnused.length > 0) {
      pushWarning(warnings, {
        code: "large_unused_assets",
        severity: "warn",
        title: "有大体积闲置素材",
        detail: `${largeUnused.length} 个未使用素材合计 ${formatBytes(
          largeUnused.reduce((sum, record) => sum + record.sizeBytes, 0)
        )}，如果只是备份建议移出项目目录。`,
        actionHint: "先确认是否真的不会进入成品，再删除或外部归档。",
      });
    }

    const placeholderCount = records.filter((record) => record.placeholder).length;
    if (placeholderCount > 0) {
      pushWarning(warnings, {
        code: "placeholder_assets",
        severity: "tip",
        title: "仍有占位或临时素材",
        detail: `检测到 ${placeholderCount} 个名字或标签像占位素材的条目，发布前建议确认是否要替换。`,
        actionHint: "如果它们就是正式素材，可以改名或移除占位标签。",
      });
    }

    const dangerCount = warnings.filter((warning) => warning.severity === "danger").length;
    const warnCount = warnings.filter((warning) => warning.severity === "warn").length;
    const releaseRiskLevel = dangerCount > 0 ? "danger" : warnCount > 0 ? "warn" : "ready";

    return {
      assets: records,
      categories,
      warnings,
      topAssets,
      totals: {
        assetCount: records.length,
        totalBytes,
        totalLabel: formatBytes(totalBytes),
        totalWarnBytes,
        totalWarnLabel: formatBytes(totalWarnBytes),
        totalDangerBytes,
        totalDangerLabel: formatBytes(totalDangerBytes),
        missingSizeCount,
        unusedCount: records.filter((record) => record.unused).length,
        placeholderCount,
        riskAssetCount: records.filter((record) => record.risk !== "ready").length,
        dangerCount,
        warnCount,
      },
      releaseRiskLevel,
    };
  }

  function getAssetFootprintDigest(report = {}) {
    const totals = report.totals ?? {};
    const warningCount = (report.warnings ?? []).filter((warning) => ["danger", "warn"].includes(warning.severity)).length;
    const largest = (report.topAssets ?? [])[0] ?? null;
    const level = report.releaseRiskLevel ?? "ready";
    const title =
      level === "danger"
        ? "包体风险偏高"
        : level === "warn"
          ? "建议压缩一轮"
          : "素材体积健康";
    const detail =
      level === "danger"
        ? "正式发布前建议先处理最大素材，否则下载包、加载峰值和低配体验都会被拖累。"
        : level === "warn"
          ? "当前没有硬阻塞，但已经值得做一轮图片、音频或视频压缩。"
          : "当前登记素材没有明显体积风险，可以继续把精力放在剧情和演出上。";

    return {
      level,
      title,
      detail,
      actionLabel: level === "ready" ? "导出体积清单" : "导出压缩清单",
      badges: [
        `${totals.assetCount ?? 0} 个素材`,
        `合计 ${totals.totalLabel ?? "0 B"}`,
        warningCount > 0 ? `${warningCount} 项提醒` : "无明显体积风险",
        largest ? `最大：${largest.name} · ${largest.sizeLabel}` : "暂无素材",
      ],
    };
  }

  function buildMarkdownTable(headers, rows) {
    if (!rows.length) {
      return "";
    }
    const escapeCell = (value) => String(value ?? "").replace(/\|/g, "\\|").replace(/\n+/g, " ");
    return [
      `| ${headers.map(escapeCell).join(" | ")} |`,
      `| ${headers.map(() => "---").join(" | ")} |`,
      ...rows.map((row) => `| ${row.map(escapeCell).join(" | ")} |`),
    ].join("\n");
  }

  function buildAssetFootprintMarkdown(report = {}, options = {}) {
    const projectTitle = cleanText(options.projectTitle, "Canvasia Project");
    const generatedAt = cleanText(options.generatedAt, "");
    const digest = getAssetFootprintDigest(report);
    const totals = report.totals ?? {};
    const categoryRows = toArray(report.categories).map((category) => [
      category.label,
      category.count,
      category.totalLabel,
      category.riskCount,
      category.largest ? `${category.largest.name} · ${category.largest.sizeLabel}` : "",
    ]);
    const assetRows = toArray(report.topAssets).map((asset, index) => [
      index + 1,
      asset.name,
      asset.typeLabel,
      asset.categoryLabel,
      asset.sizeLabel,
      asset.risk === "danger" ? "明显偏大" : asset.risk === "warn" ? "建议压缩" : "正常",
      asset.unused ? "未使用" : "已使用或未统计",
    ]);
    const warningRows = toArray(report.warnings).map((warning, index) => [
      index + 1,
      warning.severity === "danger" ? "高风险" : warning.severity === "warn" ? "提醒" : "提示",
      warning.title,
      warning.assetName,
      warning.detail,
      warning.actionHint,
    ]);

    return [
      `# ${projectTitle} 素材体积雷达`,
      "",
      generatedAt ? `生成时间：${generatedAt}` : "",
      "",
      `状态：${digest.title}`,
      "",
      digest.detail,
      "",
      "## 总览",
      "",
      buildMarkdownTable(
        ["素材数", "已记录体积", "风险素材", "未知体积", "未使用", "占位/临时"],
        [[
          totals.assetCount ?? 0,
          totals.totalLabel ?? "0 B",
          totals.riskAssetCount ?? 0,
          totals.missingSizeCount ?? 0,
          totals.unusedCount ?? 0,
          totals.placeholderCount ?? 0,
        ]]
      ),
      "",
      "## 分类体积",
      "",
      buildMarkdownTable(["分类", "数量", "合计", "风险素材", "最大项"], categoryRows) || "当前没有可统计的素材分类。",
      "",
      "## 体积排行",
      "",
      buildMarkdownTable(["排名", "素材", "类型", "分类", "大小", "状态", "使用情况"], assetRows) || "当前没有素材体积记录。",
      "",
      "## 发布前建议",
      "",
      buildMarkdownTable(["序号", "级别", "问题", "素材", "说明", "建议动作"], warningRows) || "当前没有明显体积问题。",
      "",
    ].join("\n");
  }

  function formatCsvCell(value) {
    const text = String(value ?? "");
    if (/[",\n\r]/.test(text)) {
      return `"${text.replace(/"/g, '""')}"`;
    }
    return text;
  }

  function buildCsv(headers, rows) {
    return [headers, ...rows].map((row) => row.map(formatCsvCell).join(",")).join("\n");
  }

  function buildAssetFootprintCsv(report = {}) {
    const rows = toArray(report.assets).map((asset, index) => [
      index + 1,
      asset.name,
      asset.id,
      asset.typeLabel,
      asset.categoryLabel,
      asset.sizeBytes,
      asset.sizeLabel,
      asset.risk === "danger" ? "明显偏大" : asset.risk === "warn" ? "建议压缩" : "正常",
      asset.fileExists ? "已导入" : "缺文件",
      asset.unused ? "未使用" : "已使用或未统计",
      asset.placeholder ? "可能是占位" : "",
      asset.path,
    ]);
    return `\uFEFF${buildCsv(
      ["序号", "素材", "ID", "类型", "分类", "字节", "大小", "体积状态", "文件状态", "使用情况", "占位提示", "路径"],
      rows
    )}\n`;
  }

  global.CanvasiaEditorAssetFootprint = Object.freeze({
    CATEGORY_DEFINITIONS,
    getAssetList,
    formatBytes,
    normalizeAssetSizeBytes,
    getAssetFootprintCategory,
    buildAssetFootprintReport,
    getAssetFootprintDigest,
    buildAssetFootprintMarkdown,
    buildAssetFootprintCsv,
  });
})(typeof window !== "undefined" ? window : globalThis);
