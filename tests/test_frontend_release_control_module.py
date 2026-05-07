from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "release_control.js"


class FrontendReleaseControlModuleTests(unittest.TestCase):
    def test_release_control_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.TonyNaEditorReleaseControl;
            const action = {{
              label: "打开素材",
              action: "open-asset-from-issue",
              assetId: "asset_big_video",
              dataset: {{ "asset-filter-mode": "media_budget" }},
              privateValue: "should not leak",
            }};
            const result = {{
              labels: [
                tools.getReleaseSeverityLabel("blocker"),
                tools.getReleaseSeverityLabel("warn"),
                tools.getReleaseSeverityLabel("good"),
                tools.getReleaseSeverityLabel("custom"),
                tools.getReleaseStepToneLabel("danger"),
                tools.getReleaseStepToneLabel("warn"),
                tools.getReleaseStepToneLabel("good"),
                tools.getReleaseStepToneLabel("soft"),
              ],
              serializedAction: tools.serializeReleaseReportAction(action),
              nullAction: tools.serializeReleaseReportAction(null),
              blockerSummary: tools.buildReleaseChecklistSummary([
                {{ severity: "blocker" }},
                {{ severity: "warn" }},
                {{ severity: "good" }},
              ]),
              warnSummary: tools.buildReleaseChecklistSummary([
                {{ severity: "warn" }},
                {{ severity: "good" }},
                {{ severity: "good" }},
              ]),
              goodSummary: tools.buildReleaseChecklistSummary([
                {{ severity: "good" }},
                {{ severity: "good" }},
              ]),
              splitWarnings: tools.splitReleaseWarnings([
                {{ message: tools.MISSING_VOICE_WARNING_MESSAGE }},
                {{ message: "文本偏长。" }},
              ]),
              desktopReady: [
                tools.isDesktopExportReady({{ target: "windows_nwjs", runtimeMode: "nwjs", missingAssets: 0 }}),
                tools.isDesktopExportReady({{ target: "windows_nwjs", runtimeMode: "fallback", missingAssets: 0 }}),
                tools.isDesktopExportReady({{ target: "web", runtimeMode: "nwjs", missingAssets: 0 }}),
                tools.isDesktopExportReady({{ target: "linux_nwjs", runtimeMode: "nwjs", missingAssets: 2 }}),
              ],
            }};
            process.stdout.write(JSON.stringify(result));
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
        self.assertEqual(
            payload["labels"],
            ["阻塞", "提醒", "通过", "custom", "先修", "优先", "确认", "收尾"],
        )
        self.assertEqual(payload["serializedAction"]["label"], "打开素材")
        self.assertEqual(payload["serializedAction"]["assetId"], "asset_big_video")
        self.assertEqual(payload["serializedAction"]["dataset"], {"asset-filter-mode": "media_budget"})
        self.assertNotIn("privateValue", payload["serializedAction"])
        self.assertIsNone(payload["nullAction"])
        self.assertEqual(payload["blockerSummary"]["badge"], "先补阻塞项")
        self.assertEqual(payload["blockerSummary"]["metrics"], [["阻塞项", "1 个"], ["提醒项", "1 个"], ["已就绪", "1 项"]])
        self.assertEqual(payload["warnSummary"]["badge"], "基本可发")
        self.assertEqual(payload["goodSummary"]["badge"], "可以交付")
        self.assertEqual(len(payload["splitWarnings"]["missingVoiceWarnings"]), 1)
        self.assertEqual(len(payload["splitWarnings"]["nonVoiceWarnings"]), 1)
        self.assertEqual(payload["desktopReady"], [True, False, False, False])

    def test_release_fix_order_prioritizes_blockers_before_polish(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.TonyNaEditorReleaseControl;
            const plan = tools.buildReleaseFixOrder({{
              resolution: {{ width: 1280, height: 720 }},
              releaseVersion: "1.2.0-preview",
              hasStoredReleaseVersion: false,
              errorCount: 2,
              warningIssues: [
                {{ message: tools.MISSING_VOICE_WARNING_MESSAGE }},
                {{ message: "台词偏长。" }},
              ],
              firstErrorAction: {{ action: "switch-screen", screen: "story", sceneId: "scene_1" }},
              firstVoiceAction: {{ action: "preview-story-location", sceneId: "scene_1", blockId: "line_1" }},
              firstWarningAction: {{ action: "preview-story-location", sceneId: "scene_2", blockId: "line_9" }},
              routeMetrics: {{ orphanScenes: 1 }},
              urgentMissingAssetsCount: 3,
              mediaBudgetReport: {{
                count: 2,
                blockerCount: 1,
                totalLabel: "680 MB",
                largest: {{ name: "opening.mp4", assetId: "video_op" }},
              }},
              unusedAssetCount: 4,
              exportResult: {{ target: "web", runtimeMode: "web", missingAssets: 0 }},
            }});
            const readyPlan = tools.buildReleaseFixOrder({{
              resolution: {{ width: 1920, height: 1080 }},
              releaseVersion: "1.2.0",
              hasStoredReleaseVersion: true,
              errorCount: 0,
              warningIssues: [],
              routeMetrics: {{ orphanScenes: 0 }},
              urgentMissingAssetsCount: 0,
              mediaBudgetReport: {{ count: 0, blockerCount: 0 }},
              unusedAssetCount: 0,
              exportResult: {{ target: "macos_nwjs", runtimeMode: "nwjs", missingAssets: 0 }},
            }});
            process.stdout.write(JSON.stringify({{
              blockerPlan: plan,
              readyPlan,
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
        blocker_plan = payload["blockerPlan"]
        titles = [step["title"] for step in blocker_plan["steps"]]
        self.assertEqual(
            titles,
            [
                "先清结构错误",
                "检查孤立场景和路线入口",
                "补齐已引用缺口素材",
                "压缩超预算素材",
                "集中补待绑语音",
                "确认发布版本和分辨率",
                "顺手处理补充提醒",
                "清一轮闲置素材",
                "再导一版正式桌面包",
            ],
        )
        self.assertEqual(blocker_plan["blockerCount"], 1)
        self.assertEqual(blocker_plan["urgentCount"], 5)
        self.assertEqual(blocker_plan["steps"][0]["actions"][1]["label"], "打开第一条错误")
        self.assertEqual(blocker_plan["steps"][3]["actions"][1]["assetId"], "video_op")
        self.assertEqual(blocker_plan["steps"][5]["actions"][0]["action"], "save-release-version")

        ready_plan = payload["readyPlan"]
        self.assertEqual(len(ready_plan["steps"]), 1)
        self.assertEqual(ready_plan["steps"][0]["title"], "最后导出正式桌面包确认")
        self.assertEqual(ready_plan["steps"][0]["tone"], "good")
        self.assertEqual(ready_plan["blockerCount"], 0)
        self.assertEqual(ready_plan["urgentCount"], 0)


if __name__ == "__main__":
    unittest.main()
