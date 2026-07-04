export const RUNTIME_SHORTCUT_GROUPS = Object.freeze([
  Object.freeze({
    title: "剧情推进",
    description: "最常用的阅读、回看和显示控制。",
    shortcuts: Object.freeze([
      Object.freeze({ keys: Object.freeze(["Space", "Enter", "→"]), label: "继续 / 显示整句", detail: "打字机播放中会先显示整句，之后再推进剧情。" }),
      Object.freeze({ keys: Object.freeze(["PageUp", "PageDown"]), label: "上一句 / 下一句", detail: "在已经走过的剧情历史中前后移动。" }),
      Object.freeze({ keys: Object.freeze(["H", "右键"]), label: "隐藏 / 显示对话框", detail: "适合欣赏背景、CG 或人物立绘。" }),
      Object.freeze({ keys: Object.freeze(["F1", "Shift + ?"]), label: "打开操作指南", detail: "随时查看当前 Runtime 支持的玩家操作。" }),
    ]),
  }),
  Object.freeze({
    title: "存档与系统",
    description: "关键分支前后最容易用到的安全操作。",
    shortcuts: Object.freeze([
      Object.freeze({ keys: Object.freeze(["Q"]), label: "快速存档", detail: "把当前节点保存到快速存档位。" }),
      Object.freeze({ keys: Object.freeze(["L"]), label: "快速读档", detail: "回到最近一次快速存档。" }),
      Object.freeze({ keys: Object.freeze(["Esc"]), label: "关闭当前面板", detail: "优先关闭最上层弹窗，再回到游戏。" }),
      Object.freeze({ keys: Object.freeze(["R"]), label: "重新开始", detail: "从入口场景重新开始本次试玩。" }),
    ]),
  }),
  Object.freeze({
    title: "自动播放",
    description: "适合录屏、演示或连续阅读的操作。",
    shortcuts: Object.freeze([
      Object.freeze({ keys: Object.freeze(["S"]), label: "跳过已读开关", detail: "只跳过已经读过的文本，遇到未读内容会自动停下。" }),
      Object.freeze({ keys: Object.freeze(["自动播放按钮"]), label: "自动播放", detail: "按文字长度、语音和等待卡节奏自动推进。" }),
      Object.freeze({ keys: Object.freeze(["重播语音"]), label: "重播当前语音", detail: "当前台词有语音时可重新播放。" }),
    ]),
  }),
]);

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderShortcutKeys(keys) {
  return (Array.isArray(keys) ? keys : [])
    .map((key) => `<kbd>${escapeHtml(key)}</kbd>`)
    .join("");
}

export function renderOperationGuideGroup(group) {
  return `
    <article class="operation-guide-group">
      <div class="operation-guide-group-head">
        <h3>${escapeHtml(group.title)}</h3>
        <p>${escapeHtml(group.description)}</p>
      </div>
      <div class="operation-shortcut-list">
        ${(group.shortcuts ?? [])
          .map(
            (shortcut) => `
              <div class="operation-shortcut-row">
                <div class="operation-shortcut-keys">${renderShortcutKeys(shortcut.keys)}</div>
                <div>
                  <strong>${escapeHtml(shortcut.label)}</strong>
                  <p>${escapeHtml(shortcut.detail)}</p>
                </div>
              </div>
            `
          )
          .join("")}
      </div>
    </article>
  `;
}

export function renderOperationGuideGroups(groups = RUNTIME_SHORTCUT_GROUPS) {
  return groups.map(renderOperationGuideGroup).join("");
}
