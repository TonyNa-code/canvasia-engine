(function attachStorySceneStructurePanelTools(global) {
  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function getEscapeHtml(options = {}) {
    return typeof options.escapeHtml === "function" ? options.escapeHtml : escapeHtml;
  }

  function getRenderer(options, key, fallback = () => "") {
    return typeof options[key] === "function" ? options[key] : fallback;
  }

  function getToneClass(tone, options = {}) {
    if (typeof options.getDashboardTaskToneClass === "function") {
      return options.getDashboardTaskToneClass(tone);
    }
    if (tone === "danger") {
      return "danger-text";
    }
    if (tone === "warn") {
      return "warn-text";
    }
    if (tone === "good") {
      return "good-text";
    }
    return "";
  }

  function getProductionNoteToneClass(note = "") {
    if (/错误|坏链/.test(note)) {
      return "danger-text";
    }
    if (/缺|提醒|偏素/.test(note)) {
      return "warn-text";
    }
    return "good-text";
  }

  function buildStoryScenePlayableGate(overview = {}) {
    const issueCounts = overview.issueCounts ?? {};
    const routes = Array.isArray(overview.routes) ? overview.routes : [];
    const checks = [];
    const pushCheck = (label, ok, hint) => checks.push({ label, ok: Boolean(ok), hint });

    pushCheck("正文", overview.hasStoryContent, overview.hasStoryContent ? "已经能读" : "先补台词或旁白");
    pushCheck("背景", overview.hasBackground, overview.hasBackground ? "画面已落地" : "先补背景卡");
    pushCheck("BGM", overview.hasMusic, overview.hasMusic ? "氛围已开始" : "建议补一段 BGM");
    pushCheck(
      "去向",
      routes.length > 0 || !overview.hasStoryContent,
      routes.length > 0 ? "已接后续" : "补 jump、选项或条件"
    );

    if ((issueCounts.broken_target ?? 0) > 0 || (overview.brokenRouteCount ?? 0) > 0) {
      return {
        tone: "danger",
        label: "先修坏链再试玩",
        detail: "这一场存在不可达或不存在的跳转目标，先修掉会比继续堆内容更稳。",
        checks,
      };
    }

    if (!overview.hasStoryContent) {
      return {
        tone: "warn",
        label: "还不是可试玩段落",
        detail: "先放一张台词或旁白，把空场景推到可以读的状态。",
        checks,
      };
    }

    if (!overview.hasBackground) {
      return {
        tone: "warn",
        label: "缺少第一眼画面",
        detail: "补一张背景后，这一场会更像真实游戏，而不是只停留在文本草稿。",
        checks,
      };
    }

    if (routes.length === 0 && overview.storyCount > 0) {
      return {
        tone: "warn",
        label: "可读但还没接后续",
        detail: "已经能从这里试玩一段，但发布前最好补上跳转、选项或条件分支。",
        checks,
      };
    }

    return {
      tone: overview.hasMusic ? "good" : "soft",
      label: overview.hasMusic ? "这一场已具备试玩骨架" : "已可试玩，建议补 BGM",
      detail: overview.hasMusic
        ? "正文、画面和去向已经站住了，可以从高光段跑一遍节奏。"
        : "基础可试玩已经成立，再补一段 BGM 会更接近正式视觉小说体验。",
      checks,
    };
  }

  function buildStoryScenePlayableActionPlan(scene = {}, overview = {}) {
    const issueCounts = overview.issueCounts ?? {};
    const routes = Array.isArray(overview.routes) ? overview.routes : [];
    const actions = [];
    const pushAction = (action) => {
      if (action) {
        actions.push(action);
      }
    };

    if ((issueCounts.broken_target ?? 0) > 0 || (overview.brokenRouteCount ?? 0) > 0) {
      pushAction({
        label: "先定位跳转坏链",
        action: "focus-story-block-filters",
        primary: true,
        dataset: { "story-block-type": "logic", "story-block-issue": "broken_target" },
      });
      return actions;
    }

    if (!overview.hasStoryContent) {
      pushAction({
        label: "生成可试玩段落",
        action: "apply-story-template",
        primary: true,
        dataset: { "template-id": "playable_scene" },
      });
      pushAction({ label: "加一张台词", action: "add-dialogue" });
      pushAction({ label: "加一张旁白", action: "add-narration" });
      return actions;
    }

    if (!overview.hasBackground) {
      pushAction({ label: "补背景卡", action: "add-background", primary: true });
    }

    if (!overview.hasMusic) {
      pushAction({ label: "补 BGM 卡", action: "add-music-play", primary: actions.length === 0 });
    }

    if (routes.length === 0 && overview.storyCount > 0) {
      pushAction({ label: "接一张跳转卡", action: "add-jump", primary: actions.length === 0 });
      pushAction({ label: "做一个选项分支", action: "add-choice" });
    }

    if (scene?.id && actions.length < 3) {
      pushAction({
        label: "从这里试玩",
        action: "preview-scene-from-map",
        primary: actions.length === 0,
        dataset: { "scene-id": scene.id },
      });
    }

    return actions.slice(0, 4);
  }

  function renderStoryScenePlayableGate(overview = {}, options = {}) {
    const escape = getEscapeHtml(options);
    const gate = buildStoryScenePlayableGate(overview);
    const scene = options.scene ?? {};
    const actionPlan = buildStoryScenePlayableActionPlan(scene, overview);

    return `
      <article class="production-task-card story-structure-section story-playable-gate is-${escape(gate.tone)}">
        <div class="production-task-top">
          <strong>可试玩闸门</strong>
          <span class="issue-tag ${getToneClass(gate.tone, options)}">${escape(gate.label)}</span>
        </div>
        <p>${escape(gate.detail)}</p>
        <div class="story-optimizer-tag-row">
          ${gate.checks
            .map(
              (check) => `
                <span class="issue-tag ${check.ok ? "good-text" : "warn-text"}">
                  ${escape(check.label)}：${escape(check.hint)}
                </span>
              `
            )
            .join("")}
        </div>
        ${
          actionPlan.length > 0
            ? `
              <div class="story-playable-action-plan">
                <span class="panel-note">推荐顺序</span>
                <div class="story-optimizer-action-row">
                  ${actionPlan.map((button) => renderStorySceneOptimizerButton(button, options)).join("")}
                </div>
              </div>
            `
            : ""
        }
      </article>
    `;
  }

  function renderStorySceneOptimizerButton(button = {}, options = {}) {
    const escape = getEscapeHtml(options);
    const className = button.primary ? "toolbar-button toolbar-button-primary" : "toolbar-button";
    const dataset = Object.entries(button.dataset ?? {})
      .map(([key, value]) => ` data-${key}="${escape(String(value))}"`)
      .join("");
    const disabled = button.disabled ? " disabled" : "";

    return `
      <button type="button" class="${className}" data-action="${escape(button.action)}"${dataset}${disabled}>
        ${escape(button.label)}
      </button>
    `;
  }

  function buildStorySceneOptimizerCards(scene = {}, overview = {}, options = {}) {
    const cards = [];
    const issueCounts = overview.issueCounts ?? {};
    const pushCard = (card) => {
      if (card && (card.actions?.length ?? 0) > 0) {
        cards.push(card);
      }
    };

    if (!overview.hasStoryContent) {
      pushCard({
        tone: "warn",
        title: "先把这一场写起来",
        description: "这一场现在还是空壳，先补 1 到 2 张正文卡片，马上就能进到可试玩状态。",
        tags: ["正文还没开始", "先补骨架最划算"],
        actions: [
          { label: "加一张台词", action: "add-dialogue", primary: true },
          { label: "加一张旁白", action: "add-narration" },
          { label: "从这里试玩", action: "preview-scene-from-map", dataset: { "scene-id": scene.id } },
        ],
      });
    }

    const foundationActions = [];
    const foundationTags = [];
    if (!overview.hasBackground) {
      foundationActions.push({ label: "补背景卡", action: "add-background", primary: true });
      foundationTags.push("还没放背景");
    }
    if (!overview.hasMusic) {
      foundationActions.push({ label: "补 BGM 卡", action: "add-music-play", primary: foundationActions.length === 0 });
      foundationTags.push("还没播 BGM");
    }
    if ((issueCounts.missing_asset ?? 0) > 0) {
      foundationActions.push({
        label: `只看待补素材（${issueCounts.missing_asset}）`,
        action: "focus-story-block-filters",
        dataset: { "story-block-issue": "missing_asset" },
      });
      foundationTags.push(`待补素材 ${issueCounts.missing_asset} 张`);
    }
    pushCard({
      tone: foundationActions.length > 1 ? "warn" : "soft",
      title: "先补基础氛围",
      description: "把背景、BGM 和缺文件素材补起来，这一场的画面和气氛会立刻完整很多。",
      tags: foundationTags,
      actions: foundationActions,
    });

    const repairActions = [];
    const repairTags = [];
    if ((issueCounts.missing_voice ?? 0) > 0) {
      repairActions.push({
        label: `只看待绑语音（${issueCounts.missing_voice}）`,
        action: "focus-story-block-filters",
        primary: true,
        dataset: { "story-block-type": "dialogue", "story-block-issue": "missing_voice" },
      });
      repairTags.push(`缺语音 ${issueCounts.missing_voice} 张`);
    }
    if ((issueCounts.too_long ?? 0) > 0) {
      repairActions.push({
        label: `只看偏长正文（${issueCounts.too_long}）`,
        action: "focus-story-block-filters",
        dataset: { "story-block-issue": "too_long" },
      });
      repairTags.push(`偏长文本 ${issueCounts.too_long} 张`);
    }
    if ((issueCounts.any ?? 0) > 0) {
      repairActions.push({
        label: `只看有问题卡片（${issueCounts.any}）`,
        action: "focus-story-block-filters",
        dataset: { "story-block-issue": "any" },
      });
    }
    pushCard({
      tone: (issueCounts.broken_target ?? 0) > 0 ? "danger" : "warn",
      title: "先把正文和问题修稳",
      description: "先把缺语音、偏长文本和问题卡片筛出来处理，后面继续写会更稳。",
      tags: repairTags,
      actions: repairActions,
    });

    const logicActions = [];
    const logicTags = [];
    if ((issueCounts.broken_target ?? 0) > 0) {
      logicActions.push({
        label: `只看跳转待修（${issueCounts.broken_target}）`,
        action: "focus-story-block-filters",
        primary: true,
        dataset: { "story-block-type": "logic", "story-block-issue": "broken_target" },
      });
      logicTags.push(`坏链 ${issueCounts.broken_target} 处`);
    }
    if ((overview.routes ?? []).length === 0 && overview.storyCount > 0) {
      logicActions.push({ label: "加一张跳转卡", action: "add-jump", primary: logicActions.length === 0 });
      logicActions.push({ label: "加一个选项", action: "add-choice" });
      logicTags.push("后续去向还没接上");
    } else if ((overview.choiceCount ?? 0) + (overview.conditionCount ?? 0) === 0 && overview.storyCount >= 4) {
      logicActions.push({ label: "加一个选项", action: "add-choice", primary: logicActions.length === 0 });
      logicActions.push({ label: "加条件判断", action: "add-condition" });
      logicTags.push("这场还没有分支口");
    }
    if (logicActions.length > 0) {
      logicActions.push({
        label: "只看逻辑卡片",
        action: "focus-story-block-filters",
        dataset: { "story-block-type": "logic" },
      });
    }
    pushCard({
      tone: (issueCounts.broken_target ?? 0) > 0 ? "danger" : "soft",
      title: "把分支和去向接起来",
      description: "路线入口、条件判断和跳转都在这里补，会比读完整场以后再回头找更省事。",
      tags: logicTags,
      actions: logicActions,
    });

    const effectActions = [];
    const effectTags = [];
    const polishDigest = options.polishDigest ?? null;
    if (overview.hasStoryContent) {
      effectActions.push({
        label: polishDigest?.actionLabel ?? "一键润色本场演出",
        action: "polish-scene-presentation",
        primary: true,
        disabled: polishDigest ? !polishDigest.canApply : false,
      });
      effectTags.push(...(polishDigest?.tags?.length ? polishDigest.tags : ["自动补基础转场和淡入淡出"]));
    }
    if (overview.hasStoryContent && !overview.hasEffects) {
      effectActions.push({ label: "加粒子特效", action: "add-particle-effect" });
      effectActions.push({ label: "加镜头推近", action: "add-camera-zoom" });
      effectTags.push("演出还没开始点缀");
    } else if (overview.effectCount > 0 && overview.effectCount < 2 && overview.storyCount >= 3) {
      effectActions.push({ label: "再补一张镜头卡", action: "add-camera-pan" });
      effectActions.push({ label: "加闪屏或震动", action: "add-screen-flash" });
      effectTags.push("演出还可以再抬一点");
    }
    if (overview.storyCount >= 2) {
      effectActions.push({
        label: "只看演出卡片",
        action: "focus-story-block-filters",
        dataset: { "story-block-type": "effect" },
      });
    }
    pushCard({
      tone: effectActions.length > 0 ? "good" : "soft",
      title: "把记忆点做出来",
      description:
        polishDigest?.helperText ||
        "正文已经能读的时候，先补镜头、粒子或闪屏，会比单纯继续堆字更容易出感觉。",
      tags: effectTags,
      actions: effectActions,
    });

    return cards.slice(0, 4);
  }

  function renderStorySceneOptimizerSection(scene = {}, overview = {}, options = {}) {
    const escape = getEscapeHtml(options);
    const renderEmpty = getRenderer(options, "renderEmpty", (text) => `<p class="empty-state">${escape(text)}</p>`);
    const cards = buildStorySceneOptimizerCards(scene, overview, options);
    const toneLabels = {
      danger: "优先修",
      warn: "先处理",
      good: "值得做",
      soft: "顺手补",
    };

    return `
      <article class="production-task-card story-structure-section story-optimizer-panel">
        <div class="production-task-top">
          <strong>场景优化助手</strong>
          <span class="issue-tag good-text">看见缺口就直接动手</span>
        </div>
        <p class="helper-text">这里会把这一场当前最值得做的动作，直接整理成能点的按钮。你不用先记问题，再回工具栏里找。</p>
        ${
          cards.length > 0
            ? `<div class="story-optimizer-grid">
                ${cards
                  .map(
                    (card) => `
                      <article class="story-optimizer-card is-${escape(card.tone)}">
                        <div class="story-optimizer-head">
                          <strong>${escape(card.title)}</strong>
                          <span class="issue-tag ${getToneClass(card.tone, options)}">${escape(
                            toneLabels[card.tone] ?? "可处理"
                          )}</span>
                        </div>
                        <p>${escape(card.description)}</p>
                        ${
                          card.tags?.length
                            ? `<div class="story-optimizer-tag-row">
                                ${card.tags.map((tag) => `<span class="issue-tag">${escape(tag)}</span>`).join("")}
                              </div>`
                            : ""
                        }
                        <div class="story-optimizer-action-row">
                          ${card.actions.map((button) => renderStorySceneOptimizerButton(button, options)).join("")}
                        </div>
                      </article>
                    `
                  )
                  .join("")}
              </div>`
            : renderEmpty("这一场的基础骨架已经比较完整了。可先从这里试玩一遍，确认节奏和演出手感。")
        }
      </article>
    `;
  }

  function renderStorySceneStructurePanel(scene = {}, overview = {}, options = {}) {
    const escape = getEscapeHtml(options);
    const renderRouteMetricCard = getRenderer(options, "renderRouteMetricCard");
    const renderEmpty = getRenderer(options, "renderEmpty", (text) => `<p class="empty-state">${escape(text)}</p>`);
    const tone = options.tone ?? "soft";
    const sceneStatusLabel = options.sceneStatusLabel ?? scene.status ?? "未标记";
    const scenePriorityLabel = options.scenePriorityLabel ?? scene.priority ?? "普通";
    const moodRecipePanelHtml = options.moodRecipePanelHtml ?? "";

    return `
      <article class="editor-card story-structure-card">
        <div class="story-structure-head">
          <div>
            <h3>场景结构总览</h3>
            <p>这里会汇总这场的骨架、分支口、演出密度和当前最值得先补的部分。</p>
          </div>
          <span class="issue-tag ${getToneClass(tone, options)}">完成度 ${escape(overview.completionScore ?? 0)}%</span>
        </div>
        <div class="route-summary-strip story-structure-metrics">
          ${renderRouteMetricCard(
            "正文",
            overview.storyCount ?? 0,
            `台词 ${overview.dialogueCount ?? 0} · 旁白 ${overview.narrationCount ?? 0} · 选项 ${overview.choiceCount ?? 0}`
          )}
          ${renderRouteMetricCard(
            "演出",
            overview.effectCount ?? 0,
            overview.effectCount > 0 ? "画面和听觉已经开始发力" : "还没开始点缀镜头和气氛"
          )}
          ${renderRouteMetricCard(
            "逻辑",
            overview.logicCount ?? 0,
            (overview.choiceCount ?? 0) + (overview.conditionCount ?? 0) > 0
              ? `分支 ${(overview.choiceCount ?? 0) + (overview.conditionCount ?? 0)} 处 · 去向 ${
                  overview.branchTargetCount || 1
                } 条`
              : "当前还是单线推进"
          )}
          ${renderRouteMetricCard(
            "问题卡片",
            overview.issueBlockCount ?? 0,
            overview.issueBlockCount > 0 ? "先修这里会更稳" : "这一场目前比较干净"
          )}
        </div>
        ${renderStoryScenePlayableGate(overview, { ...options, scene })}
        <div class="story-scene-planner-tags">
          <span class="issue-tag good-text">${escape(overview.phaseLabel ?? "短桥段")}</span>
          ${(overview.productionNotes ?? [])
            .map((note) => `<span class="issue-tag ${getProductionNoteToneClass(note)}">${escape(note)}</span>`)
            .join("")}
        </div>
        <div class="story-structure-grid">
          <article class="production-task-card story-structure-section is-${escape(tone)}">
            <div class="production-task-top">
              <strong>这场现在像什么</strong>
              <span class="issue-tag ${getToneClass(tone, options)}">${escape(`${sceneStatusLabel} / ${scenePriorityLabel}`)}</span>
            </div>
            <p>${escape(overview.sceneSummary ?? "")}</p>
            <div class="story-structure-note-list">
              ${(overview.structureNotes ?? [])
                .map(
                  (note) => `
                    <article class="story-structure-note">
                      <strong>${escape(note)}</strong>
                    </article>
                  `
                )
                .join("")}
            </div>
          </article>
          <article class="production-task-card story-structure-section">
            <div class="production-task-top">
              <strong>高光和分支口</strong>
              <span class="issue-tag">${
                (overview.highlightCandidates ?? []).length > 0
                  ? `优先看 ${(overview.highlightCandidates ?? []).length} 处`
                  : "自动分析中"
              }</span>
            </div>
            ${
              (overview.highlightCandidates ?? []).length > 0
                ? `<div class="story-structure-highlight-list">
                    ${overview.highlightCandidates
                      .map(
                        (item) => `
                          <article class="story-structure-highlight-card is-${escape(item.tone)}">
                            <div class="story-structure-highlight-top">
                              <span class="issue-tag ${getToneClass(item.tone, options)}">${escape(item.blockLabel)}</span>
                              <span class="panel-note">第 ${escape((item.index ?? 0) + 1)} 张</span>
                            </div>
                            <strong>${escape(item.title)}</strong>
                            <p>${escape(item.reason)}</p>
                            <div class="detail-meta">${escape(item.meta)}</div>
                            <div class="detail-actions">
                              <button type="button" class="toolbar-button toolbar-button-primary" data-action="select-block" data-block-id="${escape(
                                item.blockId
                              )}">
                                定位这张卡片
                              </button>
                            </div>
                          </article>
                        `
                      )
                      .join("")}
                  </div>`
                : renderEmpty("这场还没出现特别明显的高光点。可先补正文，再用镜头或粒子强化重点。")
            }
          </article>
        </div>
        ${renderStorySceneOptimizerSection(scene, overview, options)}
        ${moodRecipePanelHtml}
        <article class="production-task-card story-structure-section story-structure-next-card is-good">
          <div class="production-task-top">
            <strong>下一步最值钱的优化</strong>
            <span class="issue-tag good-text">先做这几件最划算</span>
          </div>
          <div class="story-structure-step-list">
            ${(overview.nextSteps ?? [])
              .map(
                (step) => `
                  <article class="story-structure-step">
                    <strong>${escape(step)}</strong>
                  </article>
                `
              )
              .join("")}
          </div>
        </article>
      </article>
    `;
  }

  global.CanvasiaEditorStorySceneStructurePanel = Object.freeze({
    buildStorySceneOptimizerCards,
    buildStoryScenePlayableActionPlan,
    buildStoryScenePlayableGate,
    renderStorySceneOptimizerButton,
    renderStorySceneOptimizerSection,
    renderStoryScenePlayableGate,
    renderStorySceneStructurePanel,
  });
})(window);
