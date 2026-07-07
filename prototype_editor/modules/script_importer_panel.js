(function attachScriptImporterPanelTools(global) {
  const DEFAULT_SCRIPT_IMPORTER_TOOLS = global.CanvasiaEditorScriptImporter || {};
  const SCRIPT_IMPORT_PLACEHOLDER = [
    "scene classroom with fade",
    'play video opening_movie title "Opening" volume 80 from 0 to 18 cover',
    "play music school_theme fadein 1.2",
    "show 悠奈 smile at center with dissolve",
    "filter memory soft",
    "blur right strong",
    "particle snow heavy fast",
    "shake heavy short",
    "flash white soft short",
    "zoom in medium center",
    "play sound door_knock",
    "voice yuina_001",
    "speed fast",
    "wait 0.8",
    '悠奈 "你终于来了。"',
    "set route = common",
    "add affection +1",
    "- 问她为什么在这里 -> rooftop [affection +1]",
    "- 先沉默陪她一会儿 [affection -1]",
    "if affection >= 2 -> rooftop else -> ending",
    "jump ending",
  ].join("\n");

  function escapeHtmlFallback(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function getScriptImporterTools(options = {}) {
    return options.scriptImporterTools || DEFAULT_SCRIPT_IMPORTER_TOOLS;
  }

  function getScriptImporterSampleDraft(characterName = "女主角") {
    const safeCharacterName = String(characterName ?? "").trim() || "女主角";
    return [
      "scene classroom with fade",
      "play music school_theme fadein 1.2",
      `show ${safeCharacterName} smile at center with dissolve`,
      "play sound door_knock",
      "voice yuina_001",
      "wait 0.8",
      `${safeCharacterName} "你终于来了。"`,
      "旁白：雨声贴着窗沿落下。",
      "set route = common",
      "add affection +1",
      "我把伞往她那边递过去。",
      "- 问她为什么在这里",
      "- 先沉默陪她一会儿",
      `hide ${safeCharacterName} with fade`,
    ].join("\n");
  }

  function buildScriptImportSummaryParts(blocks = [], options = {}) {
    const scriptImporterTools = getScriptImporterTools(options);
    const summary =
      typeof scriptImporterTools.summarizeScriptDraftBlocks === "function"
        ? scriptImporterTools.summarizeScriptDraftBlocks(blocks)
        : { total: 0 };

    if (!summary.total) {
      return { total: 0, detail: "" };
    }

    const stagePart = summary.stage ? ` / 演出 ${summary.stage}` : "";
    const logicPart = summary.logic ? ` / 逻辑 ${summary.logic}` : "";
    const routePart = summary.route ? ` / 跳转 ${summary.route}` : "";
    return {
      total: summary.total,
      detail: `台词 ${summary.dialogue ?? 0} / 旁白 ${summary.narration ?? 0} / 选项 ${
        summary.choice ?? 0
      }${stagePart}${logicPart}${routePart}`,
    };
  }

  function getScriptImportSummaryText(blocks = [], options = {}) {
    const summary = buildScriptImportSummaryParts(blocks, options);
    return summary.total ? `将插入 ${summary.total} 张卡片：${summary.detail}` : "还没有预览结果";
  }

  function getScriptImportInsertedSummaryText(blocks = [], options = {}) {
    const summary = buildScriptImportSummaryParts(blocks, options);
    return summary.total ? `已插入 ${summary.total} 张剧情卡片：${summary.detail}` : "没有可插入的剧情卡片";
  }

  function getScriptImporterCapabilityGroups() {
    return Object.freeze([
      Object.freeze({ title: "正文", items: Object.freeze(["角色：台词", '角色 "台词"', "旁白"]) }),
      Object.freeze({ title: "分支", items: Object.freeze(["- 选项", "-> 场景", "[变量 +1]"]) }),
      Object.freeze({ title: "演出", items: Object.freeze(["scene / show / hide", "music / sound / video", "shake / flash / camera"]) }),
      Object.freeze({ title: "逻辑", items: Object.freeze(["set / add", "if 条件", "jump"]) }),
    ]);
  }

  function renderScriptImporterCapabilityGrid(options = {}) {
    const escapeHtml = typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtmlFallback;
    return `
      <div class="script-importer-capability-grid" aria-label="台本导入支持的写法">
        ${getScriptImporterCapabilityGroups()
          .map(
            (group) => `
              <div class="script-importer-capability-card">
                <strong>${escapeHtml(group.title)}</strong>
                <span>${group.items.map((item) => escapeHtml(item)).join(" / ")}</span>
              </div>
            `
          )
          .join("")}
      </div>
    `;
  }

  function renderScriptImporterPanel(scene, _selectedBlock = null, options = {}) {
    if (!scene) {
      return "";
    }

    const escapeHtml = typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtmlFallback;
    const scriptImporterTools = getScriptImporterTools(options);
    const draft = String(options.draft ?? "");
    const blocks = Array.isArray(options.blocks) ? options.blocks : [];
    const previewLines =
      typeof scriptImporterTools.buildScriptDraftPreviewLines === "function"
        ? scriptImporterTools.buildScriptDraftPreviewLines(blocks, 5)
        : [];
    const hasBlocks = blocks.length > 0;
    const insertionTarget = String(options.insertionTarget ?? "当前会插入到场景末尾");
    const error = String(options.error ?? "");

    return `
      <div class="script-importer-shell">
        <div class="script-importer-copy">
          <span class="eyebrow">Text To Cards</span>
          <strong>手写剧本转剧情卡片</strong>
          <p>从文档或备忘录粘贴文本，先预览再插入。角色台词、普通旁白、连续选项、变量后果、变量卡、条件分支、音频、视频、镜头、粒子、文字速度和路线跳转都会转成可编辑剧情卡片。</p>
          <span class="helper-text">${escapeHtml(insertionTarget)}</span>
          ${renderScriptImporterCapabilityGrid({ escapeHtml })}
        </div>
        <div class="script-importer-workbench">
          <textarea
            id="scriptImporterDraft"
            class="script-importer-textarea"
            spellcheck="false"
            placeholder="${escapeHtml(SCRIPT_IMPORT_PLACEHOLDER)}"
          >${escapeHtml(draft)}</textarea>
          <div class="script-importer-actions">
            <button type="button" class="toolbar-button" data-action="apply-script-import-sample">填入示例</button>
            <button type="button" class="toolbar-button" data-action="preview-script-import">预览识别</button>
            <button type="button" class="toolbar-button toolbar-button-primary" data-action="insert-script-import-blocks" ${
              hasBlocks ? "" : "disabled"
            }>
              插入识别结果
            </button>
          </div>
        </div>
        <div class="script-importer-preview">
          <span class="issue-tag ${hasBlocks ? "good-text" : "warn-text"}">${escapeHtml(
            getScriptImportSummaryText(blocks, { scriptImporterTools })
          )}</span>
          ${error ? `<p class="helper-text warn-text">${escapeHtml(error)}</p>` : ""}
          ${
            previewLines.length
              ? `<div class="script-importer-preview-lines">${previewLines
                  .map((line) => `<code>${escapeHtml(line)}</code>`)
                  .join("")}</div>`
              : `<p class="helper-text">先粘贴一小段文本并点击“预览识别”。</p>`
          }
        </div>
      </div>
    `;
  }

  global.CanvasiaEditorScriptImporterPanel = Object.freeze({
    getScriptImportInsertedSummaryText,
    getScriptImportSummaryText,
    getScriptImporterCapabilityGroups,
    getScriptImporterSampleDraft,
    renderScriptImporterCapabilityGrid,
    renderScriptImporterPanel,
  });
})(window);
