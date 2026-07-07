from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "voice_match_review_panel.js"


class FrontendVoiceMatchReviewPanelModuleTests(unittest.TestCase):
    def test_voice_match_review_panel_renders_manual_binding_without_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorVoiceMatchReviewPanel;
            const helpers = {{
              escapeHtml(value) {{
                return String(value ?? "")
                  .replaceAll("&", "&amp;")
                  .replaceAll("<", "&lt;")
                  .replaceAll(">", "&gt;")
                  .replaceAll('"', "&quot;")
                  .replaceAll("'", "&#39;");
              }},
              getVoiceMatchReviewSelectId(reviewKind, reviewIndex) {{
                return `review-${{reviewKind}}-${{reviewIndex}}`;
              }},
              getDefaultVoiceMatchTargetId(item, availableTargets) {{
                const candidate = (item.candidates ?? []).find((entry) => availableTargets.some((asset) => asset.id === entry.assetId));
                return candidate?.assetId ?? availableTargets[0]?.id ?? "";
              }},
            }};
            const review = {{
              matchedCount: 3,
              ambiguousFiles: [
                {{
                  fileName: "yuna_001.wav",
                  reason: "多个名字太像",
                  candidates: [
                    {{ assetId: "voice_2", assetName: "悠奈 002 <候选>" }},
                    {{ assetId: "voice_1", assetName: "悠奈 001" }},
                  ],
                }},
              ],
              unmatchedFiles: [
                {{
                  fileName: "unknown.wav",
                  reason: "",
                  candidates: [],
                }},
              ],
            }};
            const targets = [
              {{ id: "voice_1", name: "悠奈 001", path: "assets/voice/yuna_001.wav" }},
              {{ id: "voice_2", name: "悠奈 002", path: "assets/voice/yuna_002.wav" }},
            ];
            const panelHtml = tools.renderVoiceMatchReviewPanel(review, targets, helpers);
            const noTargetHtml = tools.renderVoiceMatchReviewItem(review.unmatchedFiles[0], "unmatched", 0, [], helpers);
            const emptyHtml = tools.renderVoiceMatchReviewPanel({{ matchedCount: 2, ambiguousFiles: [], unmatchedFiles: [] }}, targets, helpers);
            const nullHtml = tools.renderVoiceMatchReviewPanel(null, targets, helpers);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              panelHtml,
              noTargetHtml,
              emptyHtml,
              nullHtml,
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
        panel_html = payload["panelHtml"]
        no_target_html = payload["noTargetHtml"]

        self.assertIn("renderVoiceMatchReviewItem", payload["keys"])
        self.assertIn("renderVoiceMatchReviewPanel", payload["keys"])
        self.assertIn("这批语音还有 2 个待补最后一步", panel_html)
        self.assertIn("本次自动匹配成功 3 个", panel_html)
        self.assertIn("多个候选太像，系统先没敢乱绑", panel_html)
        self.assertIn("没找到足够像的占位条目", panel_html)
        self.assertIn("yuna_001.wav", panel_html)
        self.assertIn("悠奈 002 &lt;候选&gt;", panel_html)
        self.assertIn('id="review-ambiguous-0"', panel_html)
        self.assertIn('value="voice_2" selected', panel_html)
        self.assertIn('data-action="bind-voice-match-review-file"', panel_html)
        self.assertIn('data-review-kind="ambiguous"', panel_html)
        self.assertIn('data-review-index="0"', panel_html)
        self.assertIn("收起这次匹配结果", panel_html)
        self.assertIn("当前没有待导入语音条目", no_target_html)
        self.assertIn("disabled", no_target_html)
        self.assertEqual(payload["emptyHtml"], "")
        self.assertEqual(payload["nullHtml"], "")


if __name__ == "__main__":
    unittest.main()
