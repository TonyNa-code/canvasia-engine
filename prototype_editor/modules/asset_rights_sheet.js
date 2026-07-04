(function attachAssetRightsSheetTools(global) {
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

  const PLACEHOLDER_RE = /(placeholder|sample|demo|temp|tmp|dummy|占位|示例|测试|临时)/i;
  const NON_COMMERCIAL_RE = /(non[-_\s]?commercial|cc[-_\s]?by[-_\s]?nc|personal only|editorial|不可商用|非商用|个人使用|禁止商用)/i;
  const ATTRIBUTION_RE = /(cc[-_\s]?by|attribution|署名|标注作者|需署名|credit required)/i;
  const PROVENANCE_RE = /(openai|midjourney|stable diffusion|sdxl|novelai|dall|sora|ai|人工智能|生成)/i;

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    return text || fallback;
  }

  function toCount(value, fallback = 0) {
    const numberValue = Number(value);
    if (!Number.isFinite(numberValue)) {
      return fallback;
    }
    return Math.max(0, Math.round(numberValue));
  }

  function getAssetTypeLabel(type = "") {
    return ASSET_TYPE_LABELS[type] ?? cleanText(type, "未知");
  }

  function getAssetList(data = {}) {
    if (Array.isArray(data.assetList)) {
      return data.assetList;
    }
    if (Array.isArray(data.assets?.assets)) {
      return data.assets.assets;
    }
    return Array.isArray(data.assets) ? data.assets : [];
  }

  function getNestedValue(source = {}, key = "") {
    if (!source || typeof source !== "object" || !key) {
      return undefined;
    }
    if (Object.prototype.hasOwnProperty.call(source, key)) {
      return source[key];
    }
    const meta = source.meta && typeof source.meta === "object" ? source.meta : {};
    if (Object.prototype.hasOwnProperty.call(meta, key)) {
      return meta[key];
    }
    const rights = source.rights && typeof source.rights === "object" ? source.rights : {};
    if (Object.prototype.hasOwnProperty.call(rights, key)) {
      return rights[key];
    }
    const provenance = source.provenance && typeof source.provenance === "object" ? source.provenance : {};
    if (Object.prototype.hasOwnProperty.call(provenance, key)) {
      return provenance[key];
    }
    return undefined;
  }

  function firstText(source = {}, keys = [], fallback = "") {
    for (const key of keys) {
      const value = getNestedValue(source, key);
      if (Array.isArray(value)) {
        const joined = value.map((item) => cleanText(item)).filter(Boolean).join(" / ");
        if (joined) {
          return joined;
        }
      }
      const text = cleanText(value);
      if (text) {
        return text;
      }
    }
    return fallback;
  }

  function firstBoolean(source = {}, keys = []) {
    for (const key of keys) {
      const value = getNestedValue(source, key);
      if (typeof value === "boolean") {
        return value;
      }
      const text = cleanText(value).toLowerCase();
      if (["true", "yes", "allowed", "ok", "commercial", "可商用", "允许"].includes(text)) {
        return true;
      }
      if (["false", "no", "forbidden", "not allowed", "noncommercial", "不可商用", "禁止"].includes(text)) {
        return false;
      }
    }
    return null;
  }

  function getAssetUsageEntries(assetId, data = {}, options = {}) {
    const source = options.assetUsage ?? data.assetUsage;
    if (!assetId || !source) {
      return [];
    }
    if (typeof source.get === "function") {
      return toArray(source.get(assetId));
    }
    if (Object.prototype.hasOwnProperty.call(source, assetId)) {
      return toArray(source[assetId]);
    }
    return [];
  }

  function hasAssetMarker(asset = {}, pattern) {
    const tags = toArray(asset.tags).join(" ");
    return pattern.test(
      [
        asset.id,
        asset.name,
        asset.path,
        asset.fileName,
        tags,
        firstText(asset, ["note", "description"]),
      ]
        .map((item) => cleanText(item))
        .join(" ")
    );
  }

  function isPlaceholderAsset(asset = {}) {
    return hasAssetMarker(asset, PLACEHOLDER_RE);
  }

  function isAiGeneratedAsset(asset = {}) {
    if (firstBoolean(asset, ["generatedByAi", "aiGenerated", "isAiGenerated"]) === true) {
      return true;
    }
    const aiProvider = firstText(asset, ["aiProvider", "provider", "generatedBy", "modelProvider"]);
    const prompt = firstText(asset, ["prompt", "generationPrompt", "sourcePrompt"]);
    return Boolean(prompt || hasAssetMarker({ ...asset, name: `${asset.name ?? ""} ${aiProvider}` }, PROVENANCE_RE));
  }

  function getCommercialStatus(asset = {}, licenseLabel = "") {
    const commercialFlag = firstBoolean(asset, ["commercialUse", "commercialAllowed", "allowCommercialUse", "isCommercialUseAllowed"]);
    const commercialText = firstText(asset, ["commercialUse", "commercialAllowed", "usageRights", "rightsStatus", "terms"]);
    const labelSource = `${licenseLabel} ${commercialText}`;
    if (commercialFlag === false || NON_COMMERCIAL_RE.test(labelSource)) {
      return {
        status: "blocked",
        label: commercialText || "不可商用 / 未获商用许可",
      };
    }
    if (commercialFlag === true || /(commercial|royalty[-_\s]?free|可商用|商用可|允许商用)/i.test(labelSource)) {
      return {
        status: "ready",
        label: commercialText || "可商用",
      };
    }
    return {
      status: "unknown",
      label: commercialText || "未登记商用状态",
    };
  }

  function needsAttribution(asset = {}, licenseLabel = "") {
    const flag = firstBoolean(asset, ["attributionRequired", "creditRequired", "requiresCredit"]);
    if (flag !== null) {
      return flag;
    }
    return ATTRIBUTION_RE.test(`${licenseLabel} ${firstText(asset, ["terms", "usageRights"])}`);
  }

  function getIssueWeight(issue = {}) {
    if (issue.severity === "blocker") {
      return 100;
    }
    if (issue.severity === "warn") {
      return 60;
    }
    return 20;
  }

  function makeIssue(record, severity, code, title, detail) {
    return {
      severity,
      code,
      title,
      detail,
      assetId: record.assetId,
      assetName: record.assetName,
      typeLabel: record.typeLabel,
      usageCount: record.usageCount,
    };
  }

  function pushIssue(record, issues, severity, code, title, detail) {
    const issue = makeIssue(record, severity, code, title, detail);
    record.issues.push(issue);
    issues.push(issue);
  }

  function getStatusFromIssues(issues = []) {
    if (issues.some((issue) => issue.severity === "blocker")) {
      return "blocker";
    }
    if (issues.some((issue) => issue.severity === "warn")) {
      return "warn";
    }
    if (issues.length) {
      return "tip";
    }
    return "good";
  }

  function getStatusLabel(status = "good") {
    if (status === "blocker") {
      return "先修";
    }
    if (status === "warn") {
      return "优先";
    }
    if (status === "tip") {
      return "整理";
    }
    return "就绪";
  }

  function createAssetRightsRecord(asset = {}, data = {}, options = {}) {
    const licenseLabel = firstText(asset, ["license", "licenseName", "licenseType", "licenseLabel", "rightsLicense"], "未登记");
    const sourceLabel = firstText(asset, ["sourceUrl", "sourceURL", "source", "origin", "assetSource", "downloadUrl"], "");
    const authorLabel = firstText(asset, ["author", "creator", "artist", "copyrightOwner", "owner"], "");
    const creditLabel = firstText(asset, ["credit", "attribution", "creditLine", "requiredCredit"], "");
    const providerLabel = firstText(asset, ["aiProvider", "provider", "generatedBy", "modelProvider", "model"], "");
    const promptLabel = firstText(asset, ["prompt", "generationPrompt", "sourcePrompt"], "");
    const usageEntries = getAssetUsageEntries(asset.id, data, options);
    const commercial = getCommercialStatus(asset, licenseLabel);
    return {
      asset,
      assetId: cleanText(asset.id),
      assetName: cleanText(asset.name, asset.id || "未命名素材"),
      type: cleanText(asset.type, "unknown"),
      typeLabel: getAssetTypeLabel(asset.type),
      path: cleanText(asset.path),
      fileExists: Boolean(asset.fileExists),
      usageCount: usageEntries.length || toCount(asset.usageCount),
      usageLocations: usageEntries.map((entry) => cleanText(`${entry.label ?? ""} ${entry.meta ? `(${entry.meta})` : ""}`)).filter(Boolean),
      licenseLabel,
      sourceLabel,
      authorLabel,
      creditLabel,
      commercialLabel: commercial.label,
      commercialStatus: commercial.status,
      providerLabel,
      promptLabel,
      isPlaceholder: isPlaceholderAsset(asset),
      isAiGenerated: isAiGeneratedAsset(asset),
      attributionRequired: needsAttribution(asset, licenseLabel),
      issues: [],
      status: "good",
      statusLabel: "就绪",
    };
  }

  function evaluateRecord(record, issues) {
    const isUsed = record.usageCount > 0;
    const missingLicense = record.licenseLabel === "未登记";
    const missingSource = !record.sourceLabel && !record.authorLabel;
    const missingCredit = record.attributionRequired && !record.creditLabel && !record.authorLabel;

    if (isUsed && record.commercialStatus === "blocked") {
      pushIssue(
        record,
        issues,
        "blocker",
        "asset_rights_noncommercial",
        "已使用素材不可商用",
        `${record.assetName} 标记为 ${record.commercialLabel}，发布前需要替换或重新取得授权。`
      );
    } else if (isUsed && record.commercialStatus === "unknown") {
      pushIssue(
        record,
        issues,
        "warn",
        "asset_rights_commercial_unknown",
        "商用状态未确认",
        `${record.assetName} 已被项目使用，但没有登记是否允许商用。`
      );
    }

    if (isUsed && missingLicense) {
      pushIssue(
        record,
        issues,
        "warn",
        "asset_rights_license_missing",
        "缺少授权协议",
        `${record.assetName} 已被使用，建议登记许可证、购买凭证或自制说明。`
      );
    } else if (!isUsed && missingLicense) {
      pushIssue(
        record,
        issues,
        "tip",
        "asset_rights_unused_license_missing",
        "未使用素材缺授权记录",
        `${record.assetName} 暂未使用，但如果之后要进成品，最好先补授权信息。`
      );
    }

    if (isUsed && missingSource) {
      pushIssue(
        record,
        issues,
        "warn",
        "asset_rights_source_missing",
        "缺少来源或作者",
        `${record.assetName} 没有登记来源链接、作者或自制记录，后续做 Staff / Credits 会很难追。`
      );
    }

    if (isUsed && missingCredit) {
      pushIssue(
        record,
        issues,
        "warn",
        "asset_rights_credit_missing",
        "缺少署名文本",
        `${record.assetName} 的授权看起来需要署名，但还没有准备可直接放入 Staff 的 credit line。`
      );
    }

    if (isUsed && record.isPlaceholder) {
      pushIssue(
        record,
        issues,
        "warn",
        "asset_rights_placeholder_used",
        "占位素材仍在成品中",
        `${record.assetName} 像是占位 / 示例 / 临时素材，发布前建议替换为正式素材。`
      );
    }

    if (isUsed && record.isAiGenerated && (!record.providerLabel || !record.promptLabel)) {
      pushIssue(
        record,
        issues,
        "warn",
        "asset_rights_ai_provenance_missing",
        "AI 生成来源不完整",
        `${record.assetName} 像是 AI 生成素材，建议记录模型 / 服务商 / prompt 关键词，方便之后复查。`
      );
    }

    record.status = getStatusFromIssues(record.issues);
    record.statusLabel = getStatusLabel(record.status);
  }

  function buildAssetRightsSheet(data = {}, options = {}) {
    const records = getAssetList(data).map((asset) => createAssetRightsRecord(asset, data, options));
    const issues = [];
    records.forEach((record) => evaluateRecord(record, issues));
    records.sort((left, right) => {
      const severityDiff =
        Math.max(0, ...right.issues.map(getIssueWeight)) - Math.max(0, ...left.issues.map(getIssueWeight));
      if (severityDiff !== 0) {
        return severityDiff;
      }
      if (right.usageCount !== left.usageCount) {
        return right.usageCount - left.usageCount;
      }
      return left.assetName.localeCompare(right.assetName, "zh-CN");
    });
    issues.sort((left, right) => getIssueWeight(right) - getIssueWeight(left) || left.assetName.localeCompare(right.assetName, "zh-CN"));

    const usedRecords = records.filter((record) => record.usageCount > 0);
    const blockerCount = issues.filter((issue) => issue.severity === "blocker").length;
    const warningCount = issues.filter((issue) => issue.severity === "warn").length;
    const tipCount = issues.filter((issue) => issue.severity === "tip").length;
    const readinessPenalty = Math.min(100, blockerCount * 24 + warningCount * 8 + tipCount);

    return {
      projectTitle: cleanText(data.project?.title, "Canvasia Project"),
      assets: records,
      issues,
      creditRoll: records
        .filter((record) => record.usageCount > 0 && (record.creditLabel || record.authorLabel || record.sourceLabel))
        .map((record) => ({
          assetName: record.assetName,
          typeLabel: record.typeLabel,
          creditLine: cleanText(record.creditLabel, [record.assetName, record.authorLabel, record.sourceLabel].filter(Boolean).join(" / ")),
        })),
      summary: {
        assetCount: records.length,
        usedAssetCount: usedRecords.length,
        unusedAssetCount: records.length - usedRecords.length,
        missingLicenseCount: records.filter((record) => record.licenseLabel === "未登记").length,
        usedMissingLicenseCount: usedRecords.filter((record) => record.licenseLabel === "未登记").length,
        missingSourceCount: usedRecords.filter((record) => !record.sourceLabel && !record.authorLabel).length,
        missingCreditCount: usedRecords.filter((record) => record.attributionRequired && !record.creditLabel && !record.authorLabel).length,
        placeholderCount: records.filter((record) => record.isPlaceholder).length,
        usedPlaceholderCount: usedRecords.filter((record) => record.isPlaceholder).length,
        aiGeneratedCount: records.filter((record) => record.isAiGenerated).length,
        aiProvenanceMissingCount: usedRecords.filter((record) => record.isAiGenerated && (!record.providerLabel || !record.promptLabel)).length,
        nonCommercialCount: usedRecords.filter((record) => record.commercialStatus === "blocked").length,
        commercialUnknownCount: usedRecords.filter((record) => record.commercialStatus === "unknown").length,
        blockerCount,
        warningCount,
        tipCount,
        readinessPercent: Math.max(0, 100 - readinessPenalty),
      },
    };
  }

  function getAssetRightsStatusDigest(sheet = {}) {
    const summary = sheet.summary ?? {};
    if ((summary.assetCount ?? 0) === 0) {
      return {
        status: "soft",
        title: "素材库为空",
        detail: "导入第一批背景、立绘、音乐或 UI 素材后，这里会自动生成授权与署名清单。",
      };
    }
    if ((summary.blockerCount ?? 0) > 0) {
      return {
        status: "blocked",
        title: `${summary.blockerCount} 个授权先修`,
        detail: "有已使用素材明确不可商用或授权冲突，发布前建议先替换或取得许可。",
      };
    }
    if ((summary.warningCount ?? 0) > 0) {
      return {
        status: "warn",
        title: `${summary.warningCount} 个授权待补`,
        detail: "项目可以继续制作，但素材许可证、来源、署名或 AI 生成记录还需要补齐。",
      };
    }
    if ((summary.tipCount ?? 0) > 0) {
      return {
        status: "soft",
        title: `${summary.tipCount} 个素材整理项`,
        detail: "已使用素材没有明显授权阻塞，未使用素材仍可继续补记录。",
      };
    }
    return {
      status: "ready",
      title: "素材授权就绪",
      detail: "已使用素材的授权、来源、商用状态和署名信息看起来比较完整。",
    };
  }

  function escapeMarkdownTableCell(value) {
    return String(value ?? "")
      .replace(/\|/g, "\\|")
      .replace(/\r?\n/g, "<br />")
      .trim();
  }

  function buildMarkdownTable(headers = [], rows = []) {
    const safeRows = toArray(rows);
    if (!safeRows.length) {
      return "";
    }
    return [
      `| ${toArray(headers).map(escapeMarkdownTableCell).join(" | ")} |`,
      `| ${toArray(headers).map(() => "---").join(" | ")} |`,
      ...safeRows.map((row) => `| ${toArray(row).map(escapeMarkdownTableCell).join(" | ")} |`),
    ].join("\n");
  }

  function csvCell(value) {
    return `"${String(value ?? "").replace(/"/g, '""')}"`;
  }

  function buildCsv(headers = [], rows = []) {
    return [headers, ...rows].map((row) => toArray(row).map(csvCell).join(",")).join("\n");
  }

  function buildAssetRightsMarkdown(sheet = {}, options = {}) {
    const summary = sheet.summary ?? {};
    const digest = getAssetRightsStatusDigest(sheet);
    const projectTitle = cleanText(options.projectTitle ?? sheet.projectTitle, "Canvasia Project");
    const generatedAt = cleanText(options.generatedAt);
    const assetRows = toArray(sheet.assets).map((record) => [
      record.statusLabel,
      record.assetName,
      record.typeLabel,
      record.usageCount,
      record.licenseLabel,
      record.commercialLabel,
      record.authorLabel || record.sourceLabel || "未登记",
      record.creditLabel || "未登记",
      record.isAiGenerated ? `${record.providerLabel || "AI"} / ${record.promptLabel ? "有 prompt" : "缺 prompt"}` : "否",
    ]);
    const issueRows = toArray(sheet.issues).map((issue, index) => [
      index + 1,
      getStatusLabel(issue.severity),
      issue.assetName,
      issue.typeLabel,
      issue.title,
      issue.detail,
    ]);
    const creditRows = toArray(sheet.creditRoll).map((entry) => [
      entry.typeLabel,
      entry.assetName,
      entry.creditLine,
    ]);

    return [
      `# ${projectTitle} 素材授权与署名清单`,
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
        ["素材", "已使用", "缺授权", "商用未知", "不可商用", "占位仍使用", "AI 记录缺口", "发布就绪度"],
        [
          [
            summary.assetCount ?? 0,
            summary.usedAssetCount ?? 0,
            summary.usedMissingLicenseCount ?? 0,
            summary.commercialUnknownCount ?? 0,
            summary.nonCommercialCount ?? 0,
            summary.usedPlaceholderCount ?? 0,
            summary.aiProvenanceMissingCount ?? 0,
            `${summary.readinessPercent ?? 0}%`,
          ],
        ]
      ),
      "",
      "## 素材授权表",
      "",
      buildMarkdownTable(["状态", "素材", "类型", "引用", "授权", "商用", "来源 / 作者", "署名", "AI 来源"], assetRows) ||
        "当前没有可列出的素材。",
      "",
      "## 需要处理的问题",
      "",
      buildMarkdownTable(["序号", "级别", "素材", "类型", "问题", "说明"], issueRows) || "当前没有明显授权问题。",
      "",
      "## Staff / Credits 备选署名",
      "",
      buildMarkdownTable(["类型", "素材", "署名文本"], creditRows) || "还没有可直接放入 Staff 的署名记录。",
      "",
    ].join("\n");
  }

  function buildAssetRightsCsv(sheet = {}) {
    const rows = toArray(sheet.assets).map((record, index) => [
      index + 1,
      record.assetName,
      record.assetId,
      record.typeLabel,
      record.usageCount,
      record.statusLabel,
      record.licenseLabel,
      record.commercialLabel,
      record.sourceLabel,
      record.authorLabel,
      record.creditLabel,
      record.isPlaceholder ? "是" : "否",
      record.isAiGenerated ? "是" : "否",
      record.providerLabel,
      record.promptLabel,
      record.issues.map((issue) => issue.title).join(" / "),
    ]);
    return `\uFEFF${buildCsv(
      ["序号", "素材", "ID", "类型", "引用次数", "状态", "授权", "商用", "来源", "作者", "署名", "占位", "AI生成", "AI服务/模型", "Prompt", "问题"],
      rows
    )}\n`;
  }

  function defaultEscapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function getAssetRightsToneClass(status) {
    if (status === "blocked") {
      return "danger-text";
    }
    if (status === "warn") {
      return "warn-text";
    }
    if (status === "ready") {
      return "good-text";
    }
    return "";
  }

  function renderFallbackMetric(title, value, detail, escapeHtml) {
    return `
      <article class="route-metric-card">
        <span>${escapeHtml(title)}</span>
        <strong>${escapeHtml(value)}</strong>
        <small>${escapeHtml(detail)}</small>
      </article>
    `;
  }

  function renderAssetRightsSheetPanel(sheet = {}, options = {}) {
    const escapeHtml = typeof options.escapeHtml === "function" ? options.escapeHtml : defaultEscapeHtml;
    const renderMetric =
      typeof options.renderRouteMetricCard === "function"
        ? options.renderRouteMetricCard
        : (title, value, detail) => renderFallbackMetric(title, value, detail, escapeHtml);
    const digest = getAssetRightsStatusDigest(sheet);
    const summary = sheet.summary ?? {};
    const topIssues = toArray(sheet.issues).slice(0, 4);
    const creditPreview = toArray(sheet.creditRoll).slice(0, 4);

    return `
      <article class="detail-card preview-sprint-panel">
        <div class="panel-heading">
          <h2>素材授权与署名清单</h2>
          <span class="badge badge-soft ${getAssetRightsToneClass(digest.status)}">${escapeHtml(digest.title)}</span>
        </div>
        <p class="helper-text">${escapeHtml(digest.detail)} 它会把已使用素材的许可证、来源、作者、商用状态、占位标记和 AI 生成记录集中列出，方便发布前做最后确认。</p>
        <div class="preview-sprint-metrics">
          ${renderMetric("已使用素材", `${summary.usedAssetCount ?? 0} 个`, "真正进入成品的素材")}
          ${renderMetric("授权 / 来源缺口", `${summary.usedMissingLicenseCount ?? 0} / ${summary.missingSourceCount ?? 0}`, "需要补许可证或来源")}
          ${renderMetric("商用风险", `${summary.nonCommercialCount ?? 0} / ${summary.commercialUnknownCount ?? 0}`, "不可商用 / 未确认")}
          ${renderMetric("发布就绪度", `${summary.readinessPercent ?? 0}%`, "按素材授权风险估算")}
        </div>
        <div class="detail-actions">
          <button class="toolbar-button toolbar-button-primary" data-action="export-asset-rights-markdown">
            导出授权清单
          </button>
          <button class="toolbar-button" data-action="export-asset-rights-csv">
            导出授权 CSV
          </button>
          <button class="toolbar-button" data-action="switch-screen" data-screen="assets">
            去素材库补资料
          </button>
        </div>
        ${
          topIssues.length > 0
            ? `
              <div class="preview-sprint-grid">
                ${topIssues
                  .map(
                    (issue) => `
                      <article class="preview-sprint-card is-${issue.severity === "blocker" ? "danger" : issue.severity === "warn" ? "warn" : "soft"}">
                        <div class="preview-sprint-head">
                          <strong>${escapeHtml(issue.title)}</strong>
                          <span class="issue-tag ${issue.severity === "blocker" ? "danger-text" : issue.severity === "warn" ? "warn-text" : ""}">
                            ${escapeHtml(getStatusLabel(issue.severity))}
                          </span>
                        </div>
                        <p>${escapeHtml(issue.assetName)} · ${escapeHtml(issue.detail)}</p>
                      </article>
                    `
                  )
                  .join("")}
              </div>
            `
            : `
              <div class="assistant-tip">
                <strong>授权清单看起来很干净。</strong>
                <span>如果后续导入外部素材，记得顺手登记来源、作者和署名文本。</span>
              </div>
            `
        }
        ${
          creditPreview.length > 0
            ? `
              <div class="asset-mini-list">
                ${creditPreview
                  .map(
                    (entry) => `
                      <span class="badge badge-soft">${escapeHtml(entry.typeLabel)} · ${escapeHtml(entry.creditLine)}</span>
                    `
                  )
                  .join("")}
              </div>
            `
            : ""
        }
      </article>
    `;
  }

  global.CanvasiaEditorAssetRightsSheet = Object.freeze({
    buildAssetRightsSheet,
    getAssetRightsStatusDigest,
    buildAssetRightsMarkdown,
    buildAssetRightsCsv,
    renderAssetRightsSheetPanel,
    getAssetTypeLabel,
    getAssetRightsToneClass,
  });
})(typeof window !== "undefined" ? window : globalThis);
