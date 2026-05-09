from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "tools" / "ci" / "project_health.py"


def load_project_health_module():
    spec = importlib.util.spec_from_file_location("project_health", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def create_minimal_project(project_dir: Path, broken: bool = False) -> None:
    (project_dir / "assets" / "backgrounds").mkdir(parents=True, exist_ok=True)
    (project_dir / "assets" / "backgrounds" / "room.png").write_bytes(b"fake-png")
    write_json(
        project_dir / "project.json",
        {
            "formatVersion": 3,
            "title": "Health Test",
            "chapterOrder": ["chapter_01"] if not broken else ["chapter_missing", "chapter_01"],
            "entrySceneId": "scene_start" if not broken else "scene_missing_entry",
        },
    )
    write_json(
        project_dir / "data" / "assets.json",
        {
            "formatVersion": 3,
            "assets": [
                {
                    "id": "bg_room",
                    "type": "background",
                    "name": "Room",
                    "path": "assets/backgrounds/room.png" if not broken else "assets/backgrounds/missing.png",
                }
            ],
        },
    )
    write_json(
        project_dir / "data" / "characters.json",
        {
            "formatVersion": 3,
            "characters": [{"id": "char_hero", "displayName": "Hero"}],
        },
    )
    write_json(
        project_dir / "data" / "variables.json",
        {
            "formatVersion": 3,
            "variables": [{"id": "flag_ready", "type": "boolean", "defaultValue": False}],
        },
    )
    write_json(
        project_dir / "data" / "chapters" / "chapter_01.json",
        {
            "formatVersion": 3,
            "chapterId": "chapter_01",
            "sceneOrder": ["scene_start"] if not broken else ["scene_missing_order", "scene_start"],
            "scenes": [
                {
                    "id": "scene_start",
                    "name": "Start",
                    "blocks": [
                        {"id": "bg", "type": "background", "assetId": "bg_room" if not broken else "bg_missing"},
                        {
                            "id": "line",
                            "type": "dialogue",
                            "speakerId": "char_hero" if not broken else "char_missing",
                            "text": "Hello",
                        },
                        {
                            "id": "choice",
                            "type": "choice",
                            "options": [
                                {
                                    "text": "Go",
                                    "gotoSceneId": "scene_start" if not broken else "scene_missing",
                                    "effects": [
                                        {
                                            "type": "variable_set",
                                            "variableId": "flag_ready" if not broken else "flag_missing",
                                            "value": True,
                                        }
                                    ],
                                }
                            ],
                        },
                    ],
                }
            ],
        },
    )


class ProjectHealthToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.project_health = load_project_health_module()

    def test_minimal_project_passes_without_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir) / "project"
            create_minimal_project(project_dir)

            report = self.project_health.analyze_project(project_dir)

        self.assertEqual(report["summary"]["status"], "passed")
        self.assertEqual(report["summary"]["errors"], 0)
        self.assertEqual(
            report["metrics"],
            {
                "chapterCount": 1,
                "sceneCount": 1,
                "blockCount": 3,
                "dialogueBlockCount": 1,
                "choiceBlockCount": 1,
                "assetCount": 1,
                "readyAssetCount": 1,
                "assetReferenceCount": 1,
                "uniqueAssetReferenceCount": 1,
                "characterCount": 1,
                "variableCount": 1,
            },
        )
        self.assertEqual(report["roadmap"]["completedCount"], 2)
        self.assertEqual(report["roadmap"]["totalCount"], 3)
        self.assertEqual(report["roadmap"]["nextStage"]["id"], "release_candidate")
        self.assertEqual(report["roadmap"]["nextStage"]["primaryGap"]["id"], "content_volume")
        self.assertEqual(report["roadmap"]["nextStage"]["primaryGap"]["action"]["label"], "去写正文")
        self.assertEqual(report["roadmap"]["nextStage"]["primaryGap"]["action"]["screen"], "story")

    def test_broken_project_reports_beginner_facing_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir) / "project"
            create_minimal_project(project_dir, broken=True)

            report = self.project_health.analyze_project(project_dir)

        codes = {issue["code"] for issue in report["issues"]}
        recoveries = [issue["recovery"] for issue in report["issues"]]
        repair_codes = {
            issue["code"]: issue.get("repairCode")
            for issue in report["issues"]
            if issue.get("repairCode")
        }
        self.assertEqual(report["summary"]["status"], "failed")
        self.assertEqual(report["summary"]["autoFixableCount"], 3)
        self.assertEqual(report["roadmap"]["completedCount"], 0)
        self.assertEqual(report["roadmap"]["nextStage"]["id"], "first_playable")
        self.assertEqual(report["roadmap"]["nextStage"]["primaryGap"]["id"], "no_blocking_errors")
        self.assertEqual(report["roadmap"]["nextStage"]["primaryGap"]["action"]["label"], "打开项目巡检")
        self.assertEqual(
            report["summary"]["autoFixableByRepairCode"],
            {"chapter_order": 1, "entry_scene": 1, "scene_order": 1},
        )
        self.assertIn("asset_file_missing", codes)
        self.assertIn("asset_reference_missing", codes)
        self.assertIn("chapter_order_missing", codes)
        self.assertIn("entry_scene_missing", codes)
        self.assertIn("scene_order_missing", codes)
        self.assertIn("scene_reference_missing", codes)
        self.assertIn("character_reference_missing", codes)
        self.assertIn("variable_reference_missing", codes)
        self.assertTrue(any("重新导入" in recovery for recovery in recoveries))
        self.assertTrue(any("章节排序" in recovery for recovery in recoveries))
        self.assertTrue(any("场景排序" in recovery for recovery in recoveries))
        self.assertTrue(any("现有场景" in recovery for recovery in recoveries))
        self.assertEqual(repair_codes["entry_scene_missing"], "entry_scene")
        self.assertEqual(repair_codes["chapter_order_missing"], "chapter_order")
        self.assertEqual(repair_codes["scene_order_missing"], "scene_order")

    def test_duplicate_story_order_reports_safe_repair_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir) / "project"
            create_minimal_project(project_dir)
            project_payload = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
            project_payload["chapterOrder"] = ["chapter_01", "chapter_01"]
            write_json(project_dir / "project.json", project_payload)
            chapter_path = project_dir / "data" / "chapters" / "chapter_01.json"
            chapter_payload = json.loads(chapter_path.read_text(encoding="utf-8"))
            chapter_payload["sceneOrder"] = ["scene_start", "scene_start"]
            write_json(chapter_path, chapter_payload)

            report = self.project_health.analyze_project(project_dir)

        issues = {issue["code"]: issue for issue in report["issues"]}
        self.assertEqual(report["summary"]["status"], "passed_with_warnings")
        self.assertEqual(report["summary"]["errors"], 0)
        self.assertEqual(report["summary"]["autoFixableCount"], 2)
        self.assertIn("chapter_order_duplicate", issues)
        self.assertIn("scene_order_duplicate", issues)
        self.assertEqual(issues["chapter_order_duplicate"]["repairCode"], "chapter_order")
        self.assertEqual(issues["scene_order_duplicate"]["repairCode"], "scene_order")
        self.assertTrue(issues["chapter_order_duplicate"]["autoFixable"])
        self.assertIn("一键安全修复", issues["scene_order_duplicate"]["recovery"])

    def test_omitted_story_order_reports_safe_repair_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir) / "project"
            create_minimal_project(project_dir)
            project_payload = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
            project_payload["chapterOrder"] = []
            write_json(project_dir / "project.json", project_payload)
            chapter_path = project_dir / "data" / "chapters" / "chapter_01.json"
            chapter_payload = json.loads(chapter_path.read_text(encoding="utf-8"))
            chapter_payload["sceneOrder"] = []
            write_json(chapter_path, chapter_payload)

            report = self.project_health.analyze_project(project_dir)

        issues = {issue["code"]: issue for issue in report["issues"]}
        self.assertEqual(report["summary"]["status"], "passed_with_warnings")
        self.assertEqual(report["summary"]["errors"], 0)
        self.assertEqual(report["summary"]["autoFixableCount"], 2)
        self.assertEqual(issues["chapter_order_omitted"]["repairCode"], "chapter_order")
        self.assertEqual(issues["scene_order_omitted"]["repairCode"], "scene_order")
        self.assertIn("遗漏章节", issues["chapter_order_omitted"]["recovery"])
        self.assertIn("遗漏场景", issues["scene_order_omitted"]["recovery"])

    def test_safe_repair_fixes_low_risk_story_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir) / "project"
            create_minimal_project(project_dir, broken=True)
            before = self.project_health.analyze_project(project_dir)

            result = self.project_health.repair_safe_project_issues(project_dir, report=before)
            after = self.project_health.analyze_project(project_dir)
            project_payload = json.loads((project_dir / "project.json").read_text(encoding="utf-8"))
            chapter_payload = json.loads((project_dir / "data" / "chapters" / "chapter_01.json").read_text(encoding="utf-8"))

        repair_codes = {repair["code"] for repair in result["repairs"]}
        self.assertTrue(result["changed"])
        self.assertEqual(repair_codes, {"entry_scene", "chapter_order", "scene_order"})
        self.assertEqual(project_payload["entrySceneId"], "scene_start")
        self.assertEqual(project_payload["chapterOrder"], ["chapter_01"])
        self.assertEqual(chapter_payload["sceneOrder"], ["scene_start"])
        self.assertEqual(after["summary"]["autoFixableCount"], 0)
        self.assertGreater(after["summary"]["errors"], 0)

    def test_template_project_has_no_health_errors(self) -> None:
        report = self.project_health.analyze_project(ROOT_DIR / "template_project")

        self.assertEqual(report["summary"]["errors"], 0, report["issues"])

    def test_cli_can_apply_opt_in_safe_repairs_before_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir) / "project"
            create_minimal_project(project_dir, broken=True)
            json_report = Path(tmp_dir) / "project-health.json"
            markdown_report = Path(tmp_dir) / "project-health.md"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    str(project_dir),
                    "--repair-safe",
                    "--json-report",
                    str(json_report),
                    "--markdown-report",
                    str(markdown_report),
                ],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 1)
            self.assertIn("Safe repair result: repaired 3 / skipped 0", completed.stdout)
            payload = json.loads(json_report.read_text(encoding="utf-8"))
            markdown = markdown_report.read_text(encoding="utf-8")
            self.assertEqual(payload["summary"]["autoFixableCount"], 0)
            self.assertTrue(payload["repairResult"]["changed"])
            self.assertEqual(len(payload["repairResult"]["repairs"]), 3)
            self.assertIn("## Safe Repair Result", markdown)
            self.assertIn("已修复入口场景", markdown)

    def test_cli_writes_json_and_markdown_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir) / "project"
            create_minimal_project(project_dir, broken=True)
            json_report = Path(tmp_dir) / "project-health.json"
            markdown_report = Path(tmp_dir) / "project-health.md"

            completed = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    str(project_dir),
                    "--json-report",
                    str(json_report),
                    "--markdown-report",
                    str(markdown_report),
                ],
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 1)
            self.assertIn("Tony Na Engine Project Health", completed.stdout)
            self.assertIn("Status: failed (需要先处理)", completed.stdout)
            self.assertIn("safe repairs 3", completed.stdout)
            self.assertIn("Roadmap:", completed.stdout)
            self.assertIn("First issues:", completed.stdout)
            self.assertIn("Next actions:", completed.stdout)
            self.assertIn("Reports:", completed.stdout)
            payload = json.loads(json_report.read_text(encoding="utf-8"))
            markdown = markdown_report.read_text(encoding="utf-8")
            self.assertGreater(payload["summary"]["errors"], 0)
            self.assertIn("metrics", payload)
            self.assertIn("roadmap", payload)
            self.assertEqual(payload["roadmap"]["nextStage"]["id"], "first_playable")
            self.assertEqual(payload["metrics"]["chapterCount"], 1)
            self.assertEqual(payload["metrics"]["readyAssetCount"], 0)
            self.assertEqual(payload["metrics"]["assetCount"], 1)
            self.assertEqual(payload["summary"]["autoFixableCount"], 3)
            self.assertIn("# Tony Na Engine Project Health Report", markdown)
            self.assertIn("Status label: 需要先处理", markdown)
            self.assertIn("## Triage Summary", markdown)
            self.assertIn("First blocking issue", markdown)
            self.assertIn("Frequent issue codes", markdown)
            self.assertIn("## Creation Roadmap", markdown)
            self.assertIn("Current target: 第一版可试玩 Demo", markdown)
            self.assertIn("Next gap: 先处理项目健康检查里的错误。", markdown)
            self.assertIn("Suggested button: 打开项目巡检", markdown)
            self.assertIn("| Stage | Status | Progress | Primary gap | Suggested button |", markdown)
            self.assertIn("## Project Snapshot", markdown)
            self.assertLess(markdown.index("## Project Snapshot"), markdown.index("## Suggested Next Actions"))
            self.assertIn("| Chapters | 1 |", markdown)
            self.assertIn("| Scenes | 1 |", markdown)
            self.assertIn("| Assets ready | 0 / 1 |", markdown)
            self.assertIn("## Suggested Next Actions", markdown)
            self.assertIn("Safe repairs: 3", markdown)
            self.assertIn("Safe repair groups", markdown)
            self.assertIn("引用的素材不存在", markdown)
            self.assertIn("Safe Repair", markdown)
            self.assertIn("entry_scene", markdown)
            self.assertIn("chapter_order", markdown)
            self.assertIn("scene_order", markdown)
            self.assertIn("Recovery", markdown)
            self.assertIn("重新导入", markdown)

    def test_terminal_summary_gives_clear_clean_next_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir) / "project"
            create_minimal_project(project_dir)

            report = self.project_health.analyze_project(project_dir)
            lines = self.project_health.build_terminal_summary_lines(report)

        self.assertIn("Tony Na Engine Project Health", lines[0])
        self.assertTrue(any("Status: passed (基础健康)" in line for line in lines))
        self.assertIn("Project size: 1 chapters / 1 scenes / 3 blocks | assets 1/1 ready", lines)
        self.assertTrue(any("Roadmap: 2/3 stages" in line for line in lines))
        self.assertIn("Roadmap next gap: 至少扩到几段台词、几个场景或一小段完整分支。", lines)
        self.assertIn("Roadmap next button: 去写正文", lines)
        self.assertIn("First issues: none", lines)
        self.assertIn("  - 按成品目标路线先补「发布候选版」：至少扩到几段台词、几个场景或一小段完整分支。建议按钮：去写正文。", lines)
        self.assertIn("  - 项目基础健康检查通过，可以继续试玩、导出或进入发布前检查。", lines)

    def test_markdown_report_includes_project_health_triage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_dir = Path(tmp_dir) / "project"
            create_minimal_project(project_dir, broken=True)
            report = self.project_health.analyze_project(project_dir)
            report_path = Path(tmp_dir) / "health.md"

            self.project_health.write_markdown_report(report_path, report)
            markdown = report_path.read_text(encoding="utf-8")

        self.assertIn("## Triage Summary", markdown)
        self.assertIn("## Creation Roadmap", markdown)
        self.assertIn("| Stage | Status | Progress | Primary gap | Suggested button |", markdown)
        self.assertIn("## Project Snapshot", markdown)
        self.assertIn("| Asset references | 1 unique / 1 total |", markdown)
        self.assertIn("## Suggested Next Actions", markdown)
        self.assertIn("先在编辑器的项目巡检页运行", markdown)
        self.assertIn("重新导入缺失素材", markdown)


if __name__ == "__main__":
    unittest.main()
