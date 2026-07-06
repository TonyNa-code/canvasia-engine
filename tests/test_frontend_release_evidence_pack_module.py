from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "release_evidence_pack.js"


class FrontendReleaseEvidencePackModuleTests(unittest.TestCase):
    def test_release_evidence_pack_builds_single_handoff_markdown(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorReleaseEvidencePack;
            const markdown = tools.buildReleaseEvidencePackMarkdown({{
              projectTitle: "Demo VN",
              generatedAt: "2026-07-06 10:00:00",
              releaseVersion: "1.0.0-preview",
              editorModeLabel: "新手模式",
              validation: {{ errorCount: 1, warningCount: 2 }},
              regressionSummary: {{ total: 3, passCount: 2, warnCount: 0, failCount: 1 }},
              exportSummary: {{ label: "原生 Runtime 包 · demo.zip" }},
              sections: [
                {{
                  id: "release_control",
                  title: "发布总控报告",
                  fileName: "demo_release_control.md",
                  description: "发布状态和修复顺序。",
                  content: "\\uFEFF# 发布总控\\n\\n先修阻塞项。",
                }},
                {{
                  id: "regression",
                  title: "自动回归诊断包",
                  fileName: "demo_regression.md",
                  description: "失败路线。",
                  content: "",
                  emptyMessage: "还没有跑自动回归。",
                }},
              ],
            }});
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              indexTable: tools.buildSectionIndexTable([
                {{ title: "A", fileName: "a.md", required: true, description: "alpha" }},
              ]),
              markdown,
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
        markdown = payload["markdown"]
        self.assertIn("buildReleaseEvidencePackMarkdown", payload["keys"])
        self.assertIn("| # | 证据 | 建议文件名 | 优先级 | 用途 |", payload["indexTable"])
        self.assertIn("# Demo VN 发布证据包", markdown)
        self.assertIn("发布版本：1.0.0-preview", markdown)
        self.assertIn("编辑模式：新手模式", markdown)
        self.assertIn("- 项目巡检：1 个错误 / 2 个提醒", markdown)
        self.assertIn("- 自动回归：已测 3 条，通过 2 条，失败 1 条，需要复看 0 条", markdown)
        self.assertIn("- 最近导出：原生 Runtime 包 · demo.zip", markdown)
        self.assertIn("| 1 | 发布总控报告 | demo_release_control.md | 必看 | 发布状态和修复顺序。 |", markdown)
        self.assertIn("## 1. 发布总控报告", markdown)
        self.assertIn("先修阻塞项。", markdown)
        self.assertIn("## 2. 自动回归诊断包", markdown)
        self.assertIn("还没有跑自动回归。", markdown)


if __name__ == "__main__":
    unittest.main()
