(function attachReleaseEvidencePackTools(global) {
  "use strict";

  function toArray(value) {
    return Array.isArray(value) ? value : [];
  }

  function cleanText(value, fallback = "") {
    return String(value ?? fallback).trim();
  }

  function stripBom(value) {
    return String(value ?? "").replace(/^\uFEFF/, "");
  }

  function normalizeSection(section = {}, index = 0) {
    const title = cleanText(section.title, `证据 ${index + 1}`);
    const content = stripBom(section.content).trim();
    return {
      id: cleanText(section.id, `section_${index + 1}`),
      title,
      fileName: cleanText(section.fileName, `${title}.md`),
      description: cleanText(section.description, "发布前证据"),
      required: section.required !== false,
      content,
      emptyMessage: cleanText(section.emptyMessage, "当前暂无可用内容。"),
    };
  }

  function buildSectionIndexTable(sections = []) {
    const rows = sections.map((section, index) =>
      `| ${index + 1} | ${section.title} | ${section.fileName} | ${section.required ? "必看" : "可选"} | ${section.description} |`
    );
    return [
      "| # | 证据 | 建议文件名 | 优先级 | 用途 |",
      "| --- | --- | --- | --- | --- |",
      ...rows,
    ].join("\n");
  }

  function buildReleaseEvidencePackMarkdown(context = {}) {
    const projectTitle = cleanText(context.projectTitle, "Canvasia Project");
    const generatedAt = cleanText(context.generatedAt, new Date().toISOString());
    const sections = toArray(context.sections).map(normalizeSection);
    const validation = context.validation ?? {};
    const regressionSummary = context.regressionSummary ?? {};
    const exportSummary = context.exportSummary ?? {};
    const releaseVersion = cleanText(context.releaseVersion, "未设置");
    const editorModeLabel = cleanText(context.editorModeLabel, "未记录");
    const readyCount = sections.filter((section) => section.content).length;

    const lines = [
      `# ${projectTitle} 发布证据包`,
      "",
      `生成时间：${generatedAt}`,
      `发布版本：${releaseVersion}`,
      `编辑模式：${editorModeLabel}`,
      "",
      "## 快速状态",
      "",
      `- 项目巡检：${validation.errorCount ?? 0} 个错误 / ${validation.warningCount ?? 0} 个提醒`,
      `- 自动回归：已测 ${regressionSummary.total ?? 0} 条，通过 ${regressionSummary.passCount ?? 0} 条，失败 ${regressionSummary.failCount ?? 0} 条，需要复看 ${regressionSummary.warnCount ?? 0} 条`,
      `- 最近导出：${cleanText(exportSummary.label, "还没有记录最近一次导出")}`,
      `- 已汇总证据：${readyCount}/${sections.length} 份`,
      "",
      "## 建议使用顺序",
      "",
      "1. 先看发布总控报告，确认当前最该修什么。",
      "2. 再看 Release Candidate Manifest，确认内容、Runtime、翻译和交付物是否成形。",
      "3. 如果自动回归里有失败或复看路线，先按诊断包逐条处理。",
      "4. 最后把测试员工单发给群友或测试员，收反馈后再导入反馈表复核。",
      "",
      "## 证据目录",
      "",
      sections.length ? buildSectionIndexTable(sections) : "当前没有可汇总的证据。",
      "",
      ...sections.flatMap((section, index) => [
        `## ${index + 1}. ${section.title}`,
        "",
        `建议文件名：\`${section.fileName}\``,
        `用途：${section.description}`,
        "",
        section.content || section.emptyMessage,
        "",
      ]),
    ];

    return `\uFEFF${lines.join("\n")}`;
  }

  global.CanvasiaEditorReleaseEvidencePack = Object.freeze({
    buildReleaseEvidencePackMarkdown,
    buildSectionIndexTable,
  });
})(typeof window !== "undefined" ? window : globalThis);
