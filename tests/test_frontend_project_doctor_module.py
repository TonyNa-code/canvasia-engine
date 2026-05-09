from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "project_doctor.js"
APP_PATH = ROOT_DIR / "prototype_editor" / "app.js"


class FrontendProjectDoctorModuleTests(unittest.TestCase):
    def run_project_doctor_script(self, body: str) -> dict:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.TonyNaEditorProjectDoctor;
            {body}
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
        return json.loads(completed.stdout)

    def test_project_doctor_prioritizes_beginner_repair_queue(self) -> None:
        payload = self.run_project_doctor_script(
            """
            const queue = tools.buildProjectDoctorQueue({
              issueItems: [
                {
                  kind: "warnings",
                  title: "这句台词还没有绑定语音。",
                  meta: "第一章 / 第 3 张卡",
                  action: { label: "打开台词", action: "open-character-line", sceneId: "s1", blockId: "b3" },
                },
                {
                  kind: "media_budget",
                  title: "opening.mp4 体积偏大",
                  meta: "680 MB",
                  action: { label: "打开素材", action: "open-asset-from-issue", assetId: "video_op" },
                },
                {
                  kind: "errors",
                  title: "入口场景不存在。",
                  meta: "project.json -> missing_scene",
                },
              ],
              routeOverview: {
                alerts: [
                  { tone: "warn", sceneId: "secret", sceneName: "隐藏线", message: "目前没有入口", meta: "孤立场景" },
                  { tone: "danger", sceneId: "s2", sceneName: "分支", message: "选项指向了不存在的场景。", meta: "第 2 张卡" },
                  { tone: "soft", sceneId: "ending", sceneName: "结局", message: "收束场景", meta: "正常结局" },
                ],
              },
              regressionResult: {
                cases: [
                  { id: "pass", status: "pass", sceneName: "开场", reason: "已走通" },
                  {
                    id: "loop",
                    status: "fail",
                    sceneName: "循环测试",
                    chapterName: "第一章",
                    reason: "疑似死循环",
                    detail: "重复命中同一位置",
                    steps: 20,
                    anchorSceneId: "loop_scene",
                  },
                ],
              },
              limit: 6,
            });
            const summary = tools.buildProjectDoctorSummary(queue);
            process.stdout.write(JSON.stringify({ queue, summary }));
            """
        )

        queue = payload["queue"]
        self.assertEqual(
            [step["kind"] for step in queue],
            ["errors", "regression_fail", "route_danger", "warnings", "media_budget", "route_warn"],
        )
        self.assertEqual(queue[0]["badge"], "先修")
        self.assertIn("项目入口", queue[0]["recovery"])
        self.assertIn("第一幕", queue[0]["doneWhen"])
        self.assertEqual(queue[0]["repairCodes"], ["entry_scene"])
        self.assertEqual(queue[0]["actions"][0]["action"], "set-inspection-filter")
        self.assertEqual(queue[2]["actions"][0]["sceneId"], "s2")
        self.assertIn("坏链数量减少", queue[2]["doneWhen"])
        self.assertEqual(queue[3]["actions"][0]["blockId"], "b3")
        self.assertIn("待配音", queue[3]["doneWhen"])
        self.assertEqual(payload["summary"]["status"], "danger")
        self.assertEqual(payload["summary"]["dangerCount"], 3)
        self.assertEqual(payload["summary"]["warnCount"], 3)
        self.assertEqual(payload["summary"]["autoRepairableCount"], 1)
        self.assertIn("可一键安全修复 1 项", payload["summary"]["autoRepairLabel"])
        self.assertIn("硬阻塞", payload["summary"]["title"])

    def test_project_doctor_clean_summary_is_encouraging(self) -> None:
        payload = self.run_project_doctor_script(
            """
            const queue = tools.buildProjectDoctorQueue({
              issueItems: [],
              routeOverview: { alerts: [{ tone: "soft", sceneId: "ending", message: "结局收束" }] },
              regressionResult: { cases: [{ id: "ok", status: "pass", sceneName: "开场" }] },
            });
            const summary = tools.buildProjectDoctorSummary(queue);
            process.stdout.write(JSON.stringify({ queue, summary }));
            """
        )

        self.assertEqual(payload["queue"], [])
        self.assertEqual(payload["summary"]["status"], "clean")
        self.assertEqual(payload["summary"]["badge"], "很干净")
        self.assertEqual(payload["summary"]["autoRepairableCount"], 0)
        self.assertEqual(payload["summary"]["autoRepairLabel"], "暂无可一键修复项")
        self.assertIn("继续试玩", payload["summary"]["description"])

    def test_project_doctor_respects_zero_limit(self) -> None:
        payload = self.run_project_doctor_script(
            """
            const queue = tools.buildProjectDoctorQueue({
              issueItems: [
                { kind: "errors", title: "入口场景不存在。", meta: "project.json" },
              ],
              limit: 0,
            });
            const fallbackQueue = tools.buildProjectDoctorQueue({
              issueItems: [
                { kind: "errors", title: "入口场景不存在。", meta: "project.json" },
              ],
              limit: "not-a-number",
            });
            process.stdout.write(JSON.stringify({ queue, fallbackLength: fallbackQueue.length }));
            """
        )

        self.assertEqual(payload["queue"], [])
        self.assertEqual(payload["fallbackLength"], 1)

    def test_project_doctor_infers_order_repair_codes(self) -> None:
        payload = self.run_project_doctor_script(
            """
            process.stdout.write(JSON.stringify({
              scene: tools.inferRepairCodes({ title: "场景排序引用不存在", meta: "sceneOrder -> ghost" }),
              chapter: tools.inferRepairCodes({ title: "章节排序引用不存在", meta: "chapterOrder -> ghost" }),
              sceneDuplicate: tools.inferRepairCodes({ title: "场景排序重复。", meta: "sceneOrder[2]" }),
              chapterDuplicate: tools.inferRepairCodes({ title: "章节排序重复。", meta: "chapterOrder[2]" }),
              sceneOmitted: tools.inferRepairCodes({ title: "场景没有进入排序。", meta: "sceneOrder 缺少 scene_02" }),
              chapterOmitted: tools.inferRepairCodes({ title: "章节没有进入排序。", meta: "chapterOrder 缺少 chapter_02" }),
              sceneRecoveryMentioningChapter: tools.inferRepairCodes({
                title: "场景没有进入排序。",
                meta: "sceneOrder 缺少 scene_02",
                recovery: "把遗漏场景补回当前章节排序表。",
              }),
              fallbackRecovery: tools.inferRepairCodes({ title: "需要整理", recovery: "项目医生会整理章节排序。" }),
              none: tools.inferRepairCodes({ title: "这句台词还没有绑定语音。" }),
            }));
            """
        )

        self.assertEqual(payload["scene"], ["scene_order"])
        self.assertEqual(payload["chapter"], ["chapter_order"])
        self.assertEqual(payload["sceneDuplicate"], ["scene_order"])
        self.assertEqual(payload["chapterDuplicate"], ["chapter_order"])
        self.assertEqual(payload["sceneOmitted"], ["scene_order"])
        self.assertEqual(payload["chapterOmitted"], ["chapter_order"])
        self.assertEqual(payload["sceneRecoveryMentioningChapter"], ["scene_order"])
        self.assertEqual(payload["fallbackRecovery"], ["chapter_order"])
        self.assertEqual(payload["none"], [])

    def test_project_doctor_explains_order_repair_success(self) -> None:
        payload = self.run_project_doctor_script(
            """
            const queue = tools.buildProjectDoctorQueue({
              issueItems: [
                { kind: "warnings", title: "章节没有进入排序。", meta: "project.json.chapterOrder -> 缺少 chapter_02" },
                { kind: "warnings", title: "场景排序重复。", meta: "第一章 -> sceneOrder[2] -> scene_start" },
              ],
              limit: 2,
            });
            process.stdout.write(JSON.stringify({ queue }));
            """
        )

        queue = payload["queue"]
        by_title = {item["title"]: item for item in queue}
        chapter_step = by_title["章节没有进入排序。"]
        scene_step = by_title["场景排序重复。"]
        self.assertEqual(chapter_step["repairCodes"], ["chapter_order"])
        self.assertEqual(scene_step["repairCodes"], ["scene_order"])
        self.assertIn("遗漏章节补回排序表", chapter_step["recovery"])
        self.assertIn("章节排序的重复", chapter_step["doneWhen"])
        self.assertIn("遗漏场景补回本章顺序表", scene_step["recovery"])
        self.assertIn("本章场景能按正确顺序浏览", scene_step["doneWhen"])

    def test_editor_validation_surfaces_safe_order_repairs(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")

        self.assertIn('"章节排序重复。"', source)
        self.assertIn('"章节排序里引用了不存在的章节。"', source)
        self.assertIn('"场景排序重复。"', source)
        self.assertIn('"场景排序里引用了不存在的场景。"', source)
        self.assertIn('"章节没有进入排序。"', source)
        self.assertIn('"场景没有进入排序。"', source)
        self.assertIn("data.project.chapterOrder ?? []", source)
        self.assertIn("localSceneIds.has(safeSceneId)", source)
        self.assertIn("项目医生的一键安全修复会清理无效或重复章节排序", source)
        self.assertIn("项目医生的一键安全修复会清理无效或重复场景排序", source)
        self.assertIn("autoRepairableCount", source)
        self.assertIn("可一键修复", source)

    def test_project_doctor_builds_repair_receipt(self) -> None:
        payload = self.run_project_doctor_script(
            """
            const repaired = tools.buildProjectDoctorRepairReceipt({
              changed: true,
              savedAt: "2026-05-09T06:38:12+08:00",
              repairs: [
                { code: "entry_scene", title: "已修复入口场景", detail: "入口场景已改为 scene_001。" },
                { code: "scene_order", title: "已整理场景顺序：第一章", detail: "补回未进入排序的场景 1 个。" },
              ],
              skipped: [
                { code: "chapter_order", title: "章节顺序无需修复" },
              ],
            });
            const clean = tools.buildProjectDoctorRepairReceipt({
              changed: false,
              repairs: [],
              skipped: [{ code: "entry_scene", title: "入口场景无需修复" }],
            });
            process.stdout.write(JSON.stringify({ repaired, clean }));
            """
        )

        self.assertEqual(payload["repaired"]["status"], "repaired")
        self.assertEqual(payload["repaired"]["repairCount"], 2)
        self.assertEqual(payload["repaired"]["skippedCount"], 1)
        self.assertEqual(payload["repaired"]["repairs"][0]["code"], "entry_scene")
        self.assertEqual(payload["repaired"]["nextActions"][0]["action"], "run-project-inspection")
        self.assertEqual(payload["repaired"]["nextActions"][1]["action"], "run-preview-regression")
        self.assertEqual(payload["repaired"]["nextActions"][2]["action"], "export-inspection-report")
        self.assertIn("自动快照", payload["repaired"]["description"])
        self.assertEqual(payload["clean"]["status"], "clean")
        self.assertEqual(payload["clean"]["nextActions"][1]["action"], "switch-screen")
        self.assertEqual(payload["clean"]["nextActions"][1]["screen"], "preview")
        self.assertIn("没有发现", payload["clean"]["title"])


if __name__ == "__main__":
    unittest.main()
