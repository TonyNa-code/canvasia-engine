from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "creative_assistant_panel.js"
APP_PATH = ROOT_DIR / "prototype_editor" / "app.js"


class FrontendCreativeAssistantPanelModuleTests(unittest.TestCase):
    def test_panel_renders_provider_result_selection_and_history_without_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorCreativeAssistantPanel;
            const escapeHtml = (value) => String(value ?? "")
              .replaceAll("&", "&amp;")
              .replaceAll("<", "&lt;")
              .replaceAll(">", "&gt;")
              .replaceAll('"', "&quot;")
              .replaceAll("'", "&#039;");
            const state = {{
              creativeAssistantProvider: "custom",
              creativeAssistantModel: "model-x",
              creativeAssistantBaseUrl: "http://127.0.0.1:11434/v1",
              creativeAssistantOpenAiKey: "<secret-key>",
              creativeAssistantRememberKey: true,
              creativeAssistantMode: "script",
              creativeAssistantPrompt: "雨夜 <script>alert(1)</script>",
              creativeAssistantLoading: false,
              creativeAssistantError: "",
              creativeAssistantSelectedBlockIndexes: [0],
              creativeAssistantResult: {{
                insertable: true,
                mode: "script",
                modeLabel: "剧情片段",
                title: "雨夜秘密",
                summary: "先听见脚步声",
                guidance: ["保持悬念"],
                assetPrompts: ["rainy hallway"],
                blockCount: 2,
                blocks: [
                  {{ type: "dialogue", speakerId: "heroine", text: "你听见了吗？" }},
                  {{ type: "choice", options: [{{ text: "追上去" }}, {{ text: "留下" }}] }},
                ],
                provider: {{ mode: "custom", label: "本地兼容服务", model: "model-x", fallback: false }},
                privacy: {{ message: "只发送当前提示词" }},
              }},
              creativeAssistantHistoryQuery: "雨夜",
              creativeAssistantHistoryFavoritesOnly: true,
              creativeAssistantHistoryRecovery: {{ records: [{{ id: "backup" }}] }},
              creativeAssistantHistory: [
                {{
                  id: "idea-1",
                  favorite: true,
                  prompt: "雨夜开场",
                  sceneName: "序章",
                  createdAt: "2026-05-04T12:30:00.000Z",
                  result: {{
                    mode: "script",
                    title: "雨夜秘密",
                    summary: "走廊灯忽明忽暗",
                    blocks: [{{ type: "dialogue", text: "有人吗？" }}],
                    provider: {{ mode: "custom", label: "本地兼容服务" }},
                  }},
                }},
              ],
            }};
            const options = {{
              state,
              scene: {{ id: "scene-1", name: "序章" }},
              selectedBlock: {{ id: "block-1" }},
              modes: {{ starter_demo: "试玩 Demo", script: "剧情片段" }},
              providers: {{ local: "本地模板", custom: "自定义兼容 API" }},
              promptSamples: ["雨夜校园"],
              maxHistory: 30,
              escapeHtml,
              getSafeMode: (value) => value,
              getSafeProvider: (value) => value,
              getProviderConfig: () => ({{
                label: "自定义兼容 API",
                keyPlaceholder: "API Key",
                modelPlaceholder: "model-name",
                endpointNote: "只连接你填写的地址。",
              }}),
              getSafeModel: (value) => value,
              getResultBlocks: (result) => Array.isArray(result?.blocks) ? result.blocks : [],
              getActiveBlockIndexes: () => [0],
              getSelectedBlocks: () => [state.creativeAssistantResult.blocks[0]],
              getBlockTypeLabel: (type) => ({{ dialogue: "台词", narration: "旁白", choice: "选项" }}[type] ?? "旁白"),
              getBlockSummary: () => ({{ title: "第 1 张台词卡" }}),
              filterHistoryRecords: (records) => records.filter((record) => record.favorite),
            }};
            process.stdout.write(JSON.stringify({{
              html: tools.renderCreativeAssistantPanel(options),
              blank: tools.renderCreativeAssistantBlankPanel(),
              invalidTime: tools.formatCreativeAssistantHistoryTime("not-a-date"),
            }}));
            """
        )
        completed = subprocess.run(
            ["node", "-e", script],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        html = payload["html"]
        self.assertIn("Canvasia Assistant · 创作搭子", html)
        self.assertIn("第 1 张台词卡", html)
        self.assertIn("自定义兼容 API", html)
        self.assertIn("creativeAssistantBaseUrl", html)
        self.assertIn("雨夜秘密", html)
        self.assertIn("剧情卡片预览 · 已选 1/2", html)
        self.assertIn("data-creative-block-index=\"0\"", html)
        self.assertIn("creative-history-card is-favorite", html)
        self.assertIn("恢复上次清理", html)
        self.assertIn("雨夜 &lt;script&gt;alert(1)&lt;/script&gt;", html)
        self.assertIn("&lt;secret-key&gt;", html)
        self.assertNotIn("<secret-key>", html)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("先创建一个场景", payload["blank"])
        self.assertEqual(payload["invalidTime"], "刚刚")

    def test_editor_delegates_panel_rendering_and_uses_scoped_refreshes(self) -> None:
        app_source = APP_PATH.read_text(encoding="utf-8")

        self.assertIn("const creativeAssistantPanelTools = window.CanvasiaEditorCreativeAssistantPanel;", app_source)
        self.assertIn("creativeAssistantPanelTools.renderCreativeAssistantPanel(", app_source)
        self.assertIn("creativeAssistantPanelTools.renderCreativeAssistantBlankPanel()", app_source)
        self.assertNotIn("function renderCreativeAssistantHistory()", app_source)
        self.assertNotIn("function renderCreativeAssistantResult()", app_source)
        self.assertNotIn("function renderCreativeAssistantBlockPreview(result)", app_source)
        self.assertIn("function refreshCreativeAssistantPanel(options = {})", app_source)
        self.assertIn("state.creativeAssistantSelectedBlockIndexes = [...selected].sort", app_source)
        self.assertIn("refreshCreativeAssistantPanel();\n  setSaveStatus(`智能助手已选", app_source)
        self.assertIn("refreshCreativeAssistantPanel();\n  setSaveStatus(nextFavorite", app_source)


if __name__ == "__main__":
    unittest.main()
