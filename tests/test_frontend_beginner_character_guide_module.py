from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "beginner_character_guide.js"


class FrontendBeginnerCharacterGuideModuleTests(unittest.TestCase):
    def test_beginner_character_guide_prioritizes_next_character_step_without_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorBeginnerCharacterGuide;
            const helpers = {{
              escapeHtml(value) {{
                return String(value ?? "")
                  .replaceAll("&", "&amp;")
                  .replaceAll("<", "&lt;")
                  .replaceAll(">", "&gt;")
                  .replaceAll('"', "&quot;")
                  .replaceAll("'", "&#39;");
              }},
              renderQuickActionButton(action, emphasized = false) {{
                const datasetMarkup = Object.entries(action.dataset ?? {{}})
                  .map(([key, value]) => ` data-${{key}}="${{value}}"`)
                  .join("");
                const directAttrs = [
                  action.sceneId ? `data-scene-id="${{action.sceneId}}"` : "",
                  action.blockId ? `data-block-id="${{action.blockId}}"` : "",
                ].filter(Boolean).join(" ");
                return `<button class="${{emphasized ? "primary" : "secondary"}}" data-action="${{action.action}}"${{datasetMarkup}}${{directAttrs ? ` ${{directAttrs}}` : ""}}>${{action.label}}</button>`;
              }},
              renderRouteMetricCard(label, value, hint) {{
                const escape = (input) => String(input ?? "")
                  .replaceAll("&", "&amp;")
                  .replaceAll("<", "&lt;")
                  .replaceAll(">", "&gt;")
                  .replaceAll('"', "&quot;")
                  .replaceAll("'", "&#39;");
                return `<metric data-label="${{escape(label)}}" data-value="${{escape(value)}}" data-hint="${{escape(hint)}}"></metric>`;
              }},
            }};
            const character = {{ displayName: "悠奈 <tag>" }};
            const emptyModel = tools.buildBeginnerCharacterGuideModel(null, null);
            const noLineModel = tools.buildBeginnerCharacterGuideModel(character, {{
              totalLines: 0,
              missingVoiceCount: 0,
              scenesCount: 0,
              missingVoiceLines: [],
            }});
            const missingVoiceModel = tools.buildBeginnerCharacterGuideModel(character, {{
              totalLines: 4,
              missingVoiceCount: 2,
              scenesCount: 1,
              missingVoiceLines: [{{ sceneId: "scene_1", blockId: "block_1" }}],
            }});
            const readyModel = tools.buildBeginnerCharacterGuideModel(character, {{
              totalLines: 5,
              missingVoiceCount: 0,
              scenesCount: 3,
              missingVoiceLines: [],
            }});
            const defaultModel = tools.buildBeginnerCharacterGuideModel(character, {{
              totalLines: 3,
              missingVoiceCount: 0,
              scenesCount: 0,
              missingVoiceLines: [],
            }});
            const summaryModel = tools.buildBeginnerCharacterSummaryModel(
              {{ totalCount: 5, visibleCount: 2 }},
              character,
              {{ totalLines: 7, missingVoiceCount: 1 }}
            );
            const emptySummaryModel = tools.buildBeginnerCharacterSummaryModel({{ totalCount: 5, visibleCount: 5 }}, null, null);
            const guideHtml = tools.renderBeginnerCharacterGuidePanel(missingVoiceModel, helpers);
            const summaryHtml = tools.renderBeginnerCharacterSummaryPanel(summaryModel, helpers);
            const emptyGuideHtml = tools.renderBeginnerCharacterGuidePanel(emptyModel, helpers);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              emptyModel,
              noLineModel,
              missingVoiceModel,
              readyModel,
              defaultModel,
              summaryModel,
              emptySummaryModel,
              guideHtml,
              summaryHtml,
              emptyGuideHtml,
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

        self.assertIn("buildBeginnerCharacterGuideModel", payload["keys"])
        self.assertIn("renderBeginnerCharacterGuidePanel", payload["keys"])
        self.assertTrue(payload["emptyModel"]["empty"])
        self.assertEqual(payload["emptyModel"]["actions"][0]["action"], "create-starter-kit")
        self.assertEqual(payload["noLineModel"]["title"], "为 悠奈 <tag> 添加第一句台词")
        self.assertEqual(payload["noLineModel"]["actions"][1]["dataset"]["screen"], "assets")
        self.assertEqual(payload["missingVoiceModel"]["title"], "补齐 悠奈 <tag> 的首个待绑语音")
        self.assertEqual(payload["missingVoiceModel"]["actions"][0]["action"], "open-character-line")
        self.assertEqual(payload["missingVoiceModel"]["actions"][0]["sceneId"], "scene_1")
        self.assertEqual(payload["readyModel"]["title"], "悠奈 <tag> 的基础内容已具备")
        self.assertEqual(payload["readyModel"]["actions"][0]["dataset"]["screen"], "preview")
        self.assertEqual(payload["defaultModel"]["title"], "让 悠奈 <tag> 进入剧情流程")
        self.assertEqual(payload["summaryModel"]["metrics"]["totalLines"], 7)
        self.assertEqual(payload["emptySummaryModel"]["title"], "先从列表里挑一个角色")
        self.assertIn("新手角色顺序", payload["guideHtml"])
        self.assertIn("悠奈 &lt;tag&gt;", payload["guideHtml"])
        self.assertIn('data-action="open-character-line"', payload["guideHtml"])
        self.assertIn('data-scene-id="scene_1"', payload["guideHtml"])
        self.assertIn('data-label="待绑语音"', payload["summaryHtml"])
        self.assertIn("补齐第一个角色骨架", payload["emptyGuideHtml"])


if __name__ == "__main__":
    unittest.main()
