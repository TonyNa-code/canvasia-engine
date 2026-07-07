(function attachBeginnerCharacterGuideTools(global) {
  function fallbackEscapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function fallbackActionButton(action, emphasized = false) {
    const datasetMarkup = Object.entries(action?.dataset ?? {})
      .map(([key, value]) => ` data-${key}="${fallbackEscapeHtml(value)}"`)
      .join("");
    const directAttrs = [
      action?.sceneId ? `data-scene-id="${fallbackEscapeHtml(action.sceneId)}"` : "",
      action?.blockId ? `data-block-id="${fallbackEscapeHtml(action.blockId)}"` : "",
    ]
      .filter(Boolean)
      .join(" ");
    const attrs = [datasetMarkup.trim(), directAttrs].filter(Boolean).join(" ");
    return `<button type="button" class="${emphasized ? "primary" : "secondary"}" data-action="${fallbackEscapeHtml(
      action?.action ?? ""
    )}"${attrs ? ` ${attrs}` : ""}>${fallbackEscapeHtml(action?.label ?? "继续")}</button>`;
  }

  function fallbackMetricCard(label, value, hint) {
    return `
      <article class="route-metric-card">
        <span>${fallbackEscapeHtml(label)}</span>
        <strong>${fallbackEscapeHtml(value)}</strong>
        <small>${fallbackEscapeHtml(hint)}</small>
      </article>
    `;
  }

  function getHelper(helpers, key, fallback) {
    return typeof helpers?.[key] === "function" ? helpers[key] : fallback;
  }

  function getSafeCount(value) {
    const count = Number(value ?? 0);
    return Number.isFinite(count) ? Math.max(0, count) : 0;
  }

  function buildBeginnerCharacterSummaryModel(rosterOverview = {}, character = null, stats = null) {
    const characterName = character?.displayName ?? "";
    return {
      title: character ? `${characterName} 已经选中` : "先从列表里挑一个角色",
      subtitle: character
        ? "新手模式下先关注：这个角色有没有台词、有没有待绑语音、常不常出现。"
        : "角色页先不用做复杂筛选，先从左边点一个角色看整体状态就好。",
      metrics: {
        totalCount: getSafeCount(rosterOverview.totalCount),
        visibleCount: getSafeCount(rosterOverview.visibleCount),
        totalLines: getSafeCount(stats?.totalLines),
        missingVoiceCount: getSafeCount(stats?.missingVoiceCount),
      },
    };
  }

  function buildBeginnerCharacterGuideModel(character = null, stats = null) {
    if (!character || !stats) {
      return {
        empty: true,
        title: "补齐第一个角色骨架",
        description: "角色页会先检查当前项目是否已有角色条目；如当前为空，可直接生成一个角色骨架。",
        actions: [
          { label: "一键生成起步骨架", action: "create-starter-kit" },
          { label: "自定义名字再生成", action: "create-starter-kit-custom" },
        ],
      };
    }

    const characterName = String(character.displayName ?? "当前角色");
    const totalLines = getSafeCount(stats.totalLines);
    const scenesCount = getSafeCount(stats.scenesCount);
    const missingVoiceCount = getSafeCount(stats.missingVoiceCount);
    const firstMissingVoice = Array.isArray(stats.missingVoiceLines) ? stats.missingVoiceLines[0] ?? null : null;

    let title = `让 ${characterName} 进入剧情流程`;
    let description = `${characterName} 适合先在剧情页完成出场和台词，再补充语音与细节。`;
    let actions = [
      { label: "去剧情页继续写", action: "switch-screen", dataset: { screen: "story" } },
      { label: "去试玩页看看", action: "switch-screen", dataset: { screen: "preview" } },
    ];

    if (totalLines === 0) {
      title = `为 ${characterName} 添加第一句台词`;
      description = "当前角色已有资料，但尚未参与台词，可在剧情页补入一句台词。";
      actions = [
        { label: "去剧情页加台词", action: "switch-screen", dataset: { screen: "story" } },
        { label: "去素材页补立绘", action: "switch-screen", dataset: { screen: "assets" } },
      ];
    } else if (firstMissingVoice) {
      title = `补齐 ${characterName} 的首个待绑语音`;
      description = `当前角色还有 ${missingVoiceCount} 句待绑语音，可先处理列表中靠前的一句。`;
      actions = [
        {
          label: "定位到这句台词",
          action: "open-character-line",
          sceneId: firstMissingVoice.sceneId,
          blockId: firstMissingVoice.blockId,
        },
        { label: "去试玩里听节奏", action: "switch-screen", dataset: { screen: "preview" } },
      ];
    } else if (scenesCount > 0) {
      title = `${characterName} 的基础内容已具备`;
      description = `当前角色已在 ${scenesCount} 个场景里出现，适合继续试玩或补充互动内容。`;
      actions = [
        { label: "去试玩页看看", action: "switch-screen", dataset: { screen: "preview" } },
        { label: "回剧情页继续补互动", action: "switch-screen", dataset: { screen: "story" } },
      ];
    }

    return {
      empty: false,
      characterName,
      title,
      description,
      actions,
    };
  }

  function renderBeginnerCharacterSummaryPanel(model = {}, helpers = {}) {
    const escapeHtml = getHelper(helpers, "escapeHtml", fallbackEscapeHtml);
    const renderRouteMetricCard = getHelper(helpers, "renderRouteMetricCard", fallbackMetricCard);
    const metrics = model.metrics ?? {};

    return `
    <article class="detail-card beginner-guide-panel">
      <strong>${escapeHtml(model.title ?? "先从列表里挑一个角色")}</strong>
      <p>${escapeHtml(model.subtitle ?? "")}</p>
      <div class="route-summary-strip beginner-guide-metrics">
        ${renderRouteMetricCard("角色总数", metrics.totalCount ?? 0, "项目里当前登记了多少位角色")}
        ${renderRouteMetricCard("当前命中", metrics.visibleCount ?? 0, "搜索或筛选后现在能看到多少位")}
        ${renderRouteMetricCard("当前台词", metrics.totalLines ?? 0, "这位角色已经开口多少句")}
        ${renderRouteMetricCard("待绑语音", metrics.missingVoiceCount ?? 0, "后面回头补也完全来得及")}
      </div>
    </article>
  `;
  }

  function renderBeginnerCharacterGuidePanel(model = {}, helpers = {}) {
    const escapeHtml = getHelper(helpers, "escapeHtml", fallbackEscapeHtml);
    const renderQuickActionButton = getHelper(helpers, "renderQuickActionButton", fallbackActionButton);
    const actions = Array.isArray(model.actions) ? model.actions : [];

    if (model.empty) {
      return `
      <section class="detail-card beginner-guide-panel">
        <strong>${escapeHtml(model.title ?? "补齐第一个角色骨架")}</strong>
        <p>${escapeHtml(model.description ?? "")}</p>
        <div class="detail-actions">
          ${actions.map((action, index) => renderQuickActionButton(action, index === 0)).join("")}
        </div>
      </section>
    `;
    }

    return `
    <section class="detail-card beginner-guide-panel">
      <div class="panel-heading">
        <div>
          <h3>新手角色顺序</h3>
          <span class="panel-note">优先查看台词、待绑语音和出场情况</span>
        </div>
        <span class="badge badge-soft">${escapeHtml(model.characterName ?? "当前角色")}</span>
      </div>
      <article class="beginner-guide-card beginner-guide-focus-card">
        <strong>${escapeHtml(model.title ?? "")}</strong>
        <p>${escapeHtml(model.description ?? "")}</p>
        <div class="detail-actions">
          ${actions.map((action, index) => renderQuickActionButton(action, index === 0)).join("")}
        </div>
      </article>
    </section>
  `;
  }

  global.CanvasiaEditorBeginnerCharacterGuide = Object.freeze({
    buildBeginnerCharacterSummaryModel,
    buildBeginnerCharacterGuideModel,
    renderBeginnerCharacterSummaryPanel,
    renderBeginnerCharacterGuidePanel,
  });
})(typeof window !== "undefined" ? window : globalThis);
