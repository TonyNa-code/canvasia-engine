(function attachExportReportDescriptionTools(global) {
  "use strict";

  const REPORT_DESCRIPTION_BY_NAME = Object.freeze({
    "README_试玩验收先看这里.md": "试玩验收入口：告诉作者和测试员导出后先打开什么、按什么顺序检查。",
    "release-evidence-pack.md": "发布证据包：把关键验收报告汇总成一份交接清单。",
    "release_readiness_summary.md": "发布试玩就绪摘要：综合剧情、素材、本地化、性能预算和 Runtime 覆盖，判断是否适合交给测试员。",
    "release_readiness_summary.json": "机器可读发布试玩就绪摘要：适合 CI、二次工具或自动化验收读取。",
    "performance-budget.md": "发布性能预算：复查包体、已引用素材、首屏预加载、早期路线加载和超大素材。",
    "performance-budget.json": "机器可读发布性能预算：适合自动化检查包体、首屏压力和素材体积风险。",
    "performance-budget.csv": "可导入表格的发布性能预算：方便按素材和问题分配优化任务。",
    "release-fix-order.md": "发布前修复顺序：把阻塞、复核和体验问题按优先级排好，告诉作者先修什么。",
    "release-fix-order.json": "机器可读发布前修复顺序：适合自动化读取修复任务。",
    "release-fix-order.csv": "可导入表格的发布前修复顺序：方便多人协作跟进修复状态。",
    "story_route_map.md": "剧情路线图：检查坏跳转、不可达场景、结局候选和路线覆盖。",
    "route-playtest-workbook.md": "路线试玩工作簿：把分支和结局整理成可手动点测的执行路线。",
    "route-playtest-workbook.csv": "可导入表格的路线试玩工作簿：方便测试员逐条记录结果。",
    "runtime-capability-matrix.md": "Runtime 覆盖矩阵：检查剧情卡片、VN 基础体验和 Web / 原生支持状态。",
    "localization_audit.md": "本地化覆盖报告：检查中日英等语言的漏译和覆盖率。",
    "asset-rights-report.md": "素材授权与署名报告：复查商用状态、来源、AI 生成记录和 Staff 草稿。",
    "audio-cue-report.md": "音频调度报告：复查 BGM 范围、淡入淡出、音效、语音缺口和人声混音风险。",
    "stage-direction-report.md": "角色舞台调度报告：复查背景、立绘、表情、位置、透明度和登退场。",
    "presentation-timeline-report.md": "演出时间轴报告：复查阅读时长、静态长文本、画面 / 音频锚点和硬切风险。",
    "choice-consequence-report.md": "选项后果表：复查选项文本、跳转目标、变量效果和无后果按钮。",
    "variable-influence-report.md": "变量影响表：复查变量定义、读写位置、条件引用和未使用路线旗标。",
    "voice-production-report.md": "语音制作清单：给录音、回听和长台词复核使用。",
    "unlockable_content_report.md": "可解锁内容报告：复查 CG、音乐、语音回听、图鉴、成就、章节和结局覆盖。",
    "runtime_preload_manifest.json": "Runtime 预加载清单：记录首屏和早期路线会预热的资源。",
    "RUNTIME_PRELOAD_REPORT.md": "Runtime 预加载报告：复查首屏和切场景加载压力。",
    "native-runtime-performance-budget.md": "原生 Runtime 性能预算：复查原生包体、素材体积和剧情规模。",
    "native-runtime-release-control-report.md": "原生 Runtime 发布总控：汇总发布候选、性能、文件完整性和验收状态。",
  });

  const PLAYABLE_EXPORT_RESULT_TARGETS = Object.freeze(["web", "native_runtime", "windows_nwjs", "macos_nwjs", "linux_nwjs"]);

  const PLAYABLE_EXPORT_REPORT_LINKS = Object.freeze([
    Object.freeze({ urlKey: "playtestGuidePublicUrl", label: "试玩验收 README", reportName: "README_试玩验收先看这里.md", primary: true }),
    Object.freeze({ urlKey: "releaseEvidencePackPublicUrl", label: "发布证据包", reportName: "release-evidence-pack.md", primary: true }),
    Object.freeze({ urlKey: "releaseReadinessReportPublicUrl", label: "发布就绪报告", reportName: "release_readiness_summary.md", primary: true }),
    Object.freeze({ urlKey: "routePlaytestWorkbookReportPublicUrl", label: "路线试玩工作簿", reportName: "route-playtest-workbook.md", primary: true }),
    Object.freeze({ urlKey: "routePlaytestWorkbookCsvPublicUrl", label: "路线试玩 CSV", reportName: "route-playtest-workbook.csv" }),
    Object.freeze({ urlKey: "storyRouteMapReportPublicUrl", label: "剧情路线图", reportName: "story_route_map.md" }),
    Object.freeze({ urlKey: "choiceConsequenceReportPublicUrl", label: "选项后果表", reportName: "choice-consequence-report.md" }),
    Object.freeze({ urlKey: "variableInfluenceReportPublicUrl", label: "变量影响表", reportName: "variable-influence-report.md" }),
    Object.freeze({ urlKey: "presentationTimelineReportPublicUrl", label: "演出时间轴", reportName: "presentation-timeline-report.md" }),
    Object.freeze({ urlKey: "audioCueSheetReportPublicUrl", label: "音频调度表", reportName: "audio-cue-report.md" }),
    Object.freeze({ urlKey: "stageDirectionReportPublicUrl", label: "角色舞台调度", reportName: "stage-direction-report.md" }),
    Object.freeze({ urlKey: "assetRightsReportPublicUrl", label: "素材授权报告", reportName: "asset-rights-report.md" }),
    Object.freeze({ urlKey: "voiceProductionReportPublicUrl", label: "语音制作清单", reportName: "voice-production-report.md" }),
    Object.freeze({ urlKey: "localizationAuditReportPublicUrl", label: "多语言覆盖报告", reportName: "localization_audit.md" }),
    Object.freeze({ urlKey: "runtimePreloadReportPublicUrl", label: "Runtime 预热报告", reportName: "RUNTIME_PRELOAD_REPORT.md" }),
  ]);

  function cleanText(value, fallback = "") {
    return String(value ?? fallback).replace(/\s+/g, " ").trim();
  }

  function normalizeReportLookupName(reportName) {
    const normalized = cleanText(reportName).replace(/\\/g, "/");
    return normalized.split("/").pop() || "";
  }

  function describeExportReportFile(reportName) {
    const lookupName = normalizeReportLookupName(reportName);
    if (REPORT_DESCRIPTION_BY_NAME[lookupName]) {
      return REPORT_DESCRIPTION_BY_NAME[lookupName];
    }
    if (lookupName.endsWith(".csv")) {
      return "可导入表格的补充检查报告。";
    }
    if (lookupName.endsWith(".json")) {
      return "机器可读补充检查报告。";
    }
    return "补充发布检查报告。";
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function renderDetailRowsFallback(rows = []) {
    return `<div class="detail-rows">${rows
      .map(([label, value]) => `<div><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`)
      .join("")}</div>`;
  }

  function isPlayableExportResult(exportResult) {
    return PLAYABLE_EXPORT_RESULT_TARGETS.includes(exportResult?.target);
  }

  function getLatestExportReportLinks(exportResult) {
    if (!isPlayableExportResult(exportResult)) {
      return [];
    }
    return PLAYABLE_EXPORT_REPORT_LINKS.filter((item) => exportResult?.[item.urlKey]).map((item) => ({
      ...item,
      href: exportResult[item.urlKey],
      description: describeExportReportFile(item.reportName),
    }));
  }

  function renderExportReportLink(link, options = {}) {
    const escape = typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtml;
    const description = link.description || "导出报告";
    return `
      <a
        class="toolbar-button${link.primary ? " toolbar-button-primary" : ""}"
        href="${escape(link.href)}"
        target="_blank"
        rel="noreferrer"
        title="${escape(description)}"
        aria-label="${escape(`${link.label}：${description}`)}"
      >
        ${escape(link.label)}
      </a>
    `;
  }

  function renderLatestExportReportPanel(exportResult, options = {}) {
    const links = getLatestExportReportLinks(exportResult);
    if (!links.length) {
      return "";
    }
    const renderRows = typeof options.renderDetailRows === "function" ? options.renderDetailRows : renderDetailRowsFallback;
    const routeReadiness = Number.isFinite(Number(exportResult.routePlaytestReadinessPercent))
      ? `${Math.max(0, Math.min(100, Number(exportResult.routePlaytestReadinessPercent)))}%`
      : "未记录";
    const routeCaseLine = [
      `${Number(exportResult.routePlaytestRouteCaseCount ?? 0)} 条分支`,
      `${Number(exportResult.routePlaytestEndingCaseCount ?? 0)} 个结局`,
      `${Number(exportResult.routePlaytestBlockedCaseCount ?? 0)} 个阻塞`,
    ].join(" / ");
    const releaseReadinessLine = [
      exportResult.releaseReadinessStatus || "未记录",
      Number.isFinite(Number(exportResult.releaseReadinessScore)) ? `${Number(exportResult.releaseReadinessScore)} 分` : "",
    ].filter(Boolean).join(" · ");

    return `
      <article class="detail-card">
        <strong>最近导出的验收报告</strong>
        <p class="helper-text">导出成功后，先打开这些报告就能按路线、素材、音频、演出和发布门禁逐项验收，不用再去导出文件夹里翻文件。</p>
        ${renderRows([
          ["导出目标", exportResult.targetLabel ?? exportResult.target ?? "未记录"],
          ["路线试玩就绪度", routeReadiness],
          ["路线用例", routeCaseLine],
          ["发布就绪", releaseReadinessLine || "未记录"],
        ])}
        <div class="detail-actions">
          ${links.map((link) => renderExportReportLink(link, options)).join("")}
        </div>
      </article>
    `;
  }

  global.CanvasiaEditorExportReportDescriptions = Object.freeze({
    REPORT_DESCRIPTION_BY_NAME,
    PLAYABLE_EXPORT_RESULT_TARGETS,
    PLAYABLE_EXPORT_REPORT_LINKS,
    describeExportReportFile,
    isPlayableExportResult,
    getLatestExportReportLinks,
    renderLatestExportReportPanel,
    normalizeReportLookupName,
  });
})(typeof window !== "undefined" ? window : globalThis);
