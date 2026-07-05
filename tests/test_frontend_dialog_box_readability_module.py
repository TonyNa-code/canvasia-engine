from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_SETTINGS_PATH = ROOT_DIR / "prototype_editor" / "modules" / "project_settings.js"
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "dialog_box_readability.js"


class FrontendDialogBoxReadabilityModuleTests(unittest.TestCase):
    def test_dialog_box_readability_report_and_autofix_are_pure(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(PROJECT_SETTINGS_PATH))}, "utf8"), context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorDialogBoxReadability;
            const riskyProject = {{
              project: {{
                title: "雨夜测试",
                dialogBoxConfig: {{
                  preset: "transparent",
                  shape: "rounded",
                  anchor: "free",
                  offsetXPercent: 12,
                  offsetYPercent: -8,
                  widthPercent: 58,
                  minHeight: 96,
                  paddingX: 8,
                  paddingY: 6,
                  backgroundColor: "#ffffff",
                  backgroundOpacity: 8,
                  textColor: "#f8f8f8",
                  speakerColor: "#eeeeee",
                  hintColor: "#f0f0f0",
                  blurStrength: 0,
                  panelAssetId: " custom_panel ",
                  panelAssetOpacity: 20,
                  panelAssetFit: "contain",
                }},
              }},
              scenes: [
                {{
                  id: "scene_1",
                  blocks: [
                    {{
                      id: "line_1",
                      type: "dialogue",
                      text: "这是一段非常长的测试台词，用来模拟正式 galgame 里面常见的长句展示，确保文本框不要太透明也不要太窄。",
                    }},
                    {{
                      id: "line_2",
                      type: "narration",
                      text: "第一行\\n第二行",
                    }},
                    {{
                      id: "choice_1",
                      type: "choice",
                      choices: [
                        {{ text: "认真回应她" }},
                        {{ label: "先观察一下" }},
                      ],
                    }},
                  ],
                }},
              ],
            }};
            const report = tools.buildDialogBoxReadabilityReport(riskyProject);
            const plan = tools.buildDialogBoxReadabilityAutoFixPlan(riskyProject);
            const patchedProject = tools.applyDialogBoxReadabilityPatch(riskyProject.project, plan);
            const digest = tools.getDialogBoxReadabilityDigest(report);
            const cleanProject = {{
              project: {{
                dialogBoxConfig: {{
                  preset: "moonlight",
                  widthPercent: 80,
                  minHeight: 176,
                  paddingX: 20,
                  paddingY: 16,
                  backgroundColor: "#0c1422",
                  backgroundOpacity: 92,
                  textColor: "#f3f6ff",
                  speakerColor: "#ffffff",
                  hintColor: "#d8e2f2",
                  blurStrength: 10,
                }},
              }},
              scenes: [
                {{ id: "scene_ok", blocks: [{{ type: "dialogue", text: "短句也很清楚。" }}] }},
              ],
            }};
            const cleanPlan = tools.buildDialogBoxReadabilityAutoFixPlan(cleanProject);
            const cleanDigest = tools.getDialogBoxReadabilityDigest(cleanProject);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              report: {{
                level: report.level,
                issueIds: report.issues.map((issue) => issue.id),
                issueCount: report.issues.length,
                hasPanelAsset: report.hasPanelAsset,
                metrics: report.metrics,
              }},
              plan: {{
                changed: plan.changed,
                fields: plan.operations.map((operation) => operation.field),
                summary: plan.summary,
                config: plan.dialogBoxConfig,
              }},
              patchedProject,
              digest,
              cleanPlan: {{
                changed: cleanPlan.changed,
                summary: cleanPlan.summary,
              }},
              cleanDigest,
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
        self.assertIn("buildDialogBoxReadabilityReport", payload["keys"])
        self.assertIn("buildDialogBoxReadabilityAutoFixPlan", payload["keys"])
        self.assertEqual(payload["report"]["level"], "danger")
        self.assertFalse(payload["report"]["hasPanelAsset"])
        self.assertGreaterEqual(payload["report"]["issueCount"], 5)
        self.assertIn("background-opacity", payload["report"]["issueIds"])
        self.assertIn("text-contrast", payload["report"]["issueIds"])
        self.assertIn("width", payload["report"]["issueIds"])
        self.assertEqual(payload["report"]["metrics"]["textBlockCount"], 4)
        self.assertEqual(payload["report"]["metrics"]["longTextCount"], 1)
        self.assertEqual(payload["report"]["metrics"]["multilineCount"], 1)
        self.assertTrue(payload["plan"]["changed"])
        self.assertIn("backgroundOpacity", payload["plan"]["fields"])
        self.assertIn("widthPercent", payload["plan"]["fields"])
        self.assertIn("minHeight", payload["plan"]["fields"])
        self.assertIn("paddingX", payload["plan"]["fields"])
        self.assertIn("paddingY", payload["plan"]["fields"])
        self.assertIn("blurStrength", payload["plan"]["fields"])
        self.assertIn("textColor", payload["plan"]["fields"])
        self.assertEqual(payload["plan"]["config"]["preset"], "custom")
        self.assertEqual(payload["plan"]["config"]["panelAssetId"], "custom_panel")
        self.assertEqual(payload["plan"]["config"]["panelAssetFit"], "contain")
        self.assertEqual(payload["patchedProject"]["title"], "雨夜测试")
        self.assertEqual(payload["patchedProject"]["dialogBoxConfig"]["anchor"], "free")
        self.assertEqual(payload["patchedProject"]["dialogBoxConfig"]["offsetXPercent"], 12)
        self.assertEqual(payload["patchedProject"]["dialogBoxConfig"]["offsetYPercent"], -8)
        self.assertEqual(payload["digest"]["level"], "danger")
        self.assertTrue(payload["digest"]["canApply"])
        self.assertIn("一键增强", payload["digest"]["actionLabel"])
        self.assertFalse(payload["cleanPlan"]["changed"])
        self.assertEqual(payload["cleanPlan"]["summary"], "文本框可读性已经比较稳")
        self.assertEqual(payload["cleanDigest"]["level"], "ready")
        self.assertFalse(payload["cleanDigest"]["canApply"])


if __name__ == "__main__":
    unittest.main()
