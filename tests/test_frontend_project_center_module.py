from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "project_center.js"


class FrontendProjectCenterModuleTests(unittest.TestCase):
    def test_project_center_card_renders_actions_and_escapes_labels(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorProjectCenter;
            const escapeHtml = (value) => String(value ?? "")
              .replace(/&/g, "&amp;")
              .replace(/</g, "&lt;")
              .replace(/>/g, "&gt;")
              .replace(/"/g, "&quot;")
              .replace(/'/g, "&#39;");
            const helpers = {{
              escapeHtml,
              formatDate: (value) => `日期:${{value}}`,
              getTemplateLabel: () => "校园恋爱 <模板>",
              getSafeEditorMode: (mode) => mode === "advanced" ? "advanced" : "beginner",
              getEditorModeLabel: (mode) => mode === "advanced" ? "高级模式" : "新手模式",
            }};
            const formalHtml = tools.renderProjectCenterCard({{
              projectId: "project-<1>",
              title: "我的 <企划>",
              template: "school",
              language: "zh-CN",
              updatedAt: "2026-05-18",
              editorMode: "advanced",
              chapterCount: 2,
              sceneCount: 3,
              resolution: {{ width: 2560, height: 1440 }},
            }}, "project-<1>", helpers);
            const sampleHtml = tools.renderProjectCenterCard({{
              projectId: "sample-1",
              title: "示例项目",
              template: "sample",
              isSample: true,
              chapterCount: 1,
              sceneCount: 6,
            }}, "", helpers);
            const fallbackHtml = tools.renderProjectCenterCard({{
              title: "无 helper",
              sceneCount: 0,
            }});
            const heroHtml = tools.renderProjectCenterHero({{
              localProjectCount: 2,
              projectCenterMode: "advanced",
              projectCenterModeLabel: "高级 <模式>",
              hasSampleProject: true,
              activeProjectId: "project-1",
            }}, {{ escapeHtml }});
            const emptyListHtml = tools.renderProjectCenterProjectList([], "", helpers);
            const listHtml = tools.renderProjectCenterProjectList([
              {{
                projectId: "project-<1>",
                title: "我的 <企划>",
                template: "school",
                sceneCount: 3,
              }},
              {{
                projectId: "sample-1",
                title: "示例项目",
                isSample: true,
                sceneCount: 6,
              }},
            ], "project-<1>", helpers);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              formalHtml,
              sampleHtml,
              fallbackHtml,
              heroHtml,
              emptyListHtml,
              listHtml,
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

        self.assertIn("renderProjectCenterCard", payload["keys"])
        self.assertIn("我的 &lt;企划&gt;", payload["formalHtml"])
        self.assertIn("校园恋爱 &lt;模板&gt;", payload["formalHtml"])
        self.assertIn("data-project-id=\"project-&lt;1&gt;\"", payload["formalHtml"])
        self.assertIn("上次打开", payload["formalHtml"])
        self.assertIn("继续编辑这个项目", payload["formalHtml"])
        self.assertIn("data-action=\"rename-project\"", payload["formalHtml"])
        self.assertIn("data-action=\"delete-project\"", payload["formalHtml"])
        self.assertIn("日期:2026-05-18", payload["formalHtml"])
        self.assertIn("分辨率 2560 × 1440", payload["formalHtml"])
        self.assertIn("高级模式", payload["formalHtml"])
        self.assertIn("data-action=\"duplicate-project\"", payload["sampleHtml"])
        self.assertNotIn("data-action=\"delete-project\"", payload["sampleHtml"])
        self.assertIn("复制成正式项目", payload["sampleHtml"])
        self.assertIn("真正的空白项目", payload["fallbackHtml"])
        self.assertIn("新手模式", payload["fallbackHtml"])
        self.assertIn("renderProjectCenterHero", payload["keys"])
        self.assertIn("renderProjectCenterProjectList", payload["keys"])
        self.assertIn("新建默认：高级 &lt;模式&gt;", payload["heroHtml"])
        self.assertIn("新建项目默认模式", payload["heroHtml"])
        self.assertIn("只影响之后创建的空白项目", payload["heroHtml"])
        self.assertIn('data-action="set-editor-mode"', payload["heroHtml"])
        self.assertIn('data-editor-mode="beginner"', payload["heroHtml"])
        self.assertIn('data-editor-mode="advanced"', payload["heroHtml"])
        self.assertIn("设为新手模式", payload["heroHtml"])
        self.assertIn('aria-label="项目中心主卡片：设为新建项目默认新手模式"', payload["heroHtml"])
        self.assertIn("默认：高级模式", payload["heroHtml"])
        self.assertIn('title="新建项目已经默认使用高级模式"', payload["heroHtml"])
        self.assertIn('aria-pressed="true"', payload["heroHtml"])
        self.assertIn("默认模式可在主卡片或顶部切换", payload["heroHtml"])
        self.assertIn("已发现项目 2 个", payload["heroHtml"])
        self.assertIn("示例项目可选打开", payload["heroHtml"])
        self.assertIn("已经记录过上次打开的项目", payload["heroHtml"])
        self.assertIn('data-action="create-project"', payload["heroHtml"])
        self.assertIn('data-action="refresh-project-center"', payload["heroHtml"])
        self.assertIn("现在还是一张白纸", payload["emptyListHtml"])
        self.assertIn("project-card-grid", payload["listHtml"])
        self.assertEqual(payload["listHtml"].count("project-card "), 2)
        self.assertIn("我的 &lt;企划&gt;", payload["listHtml"])
        self.assertIn("复制成正式项目", payload["listHtml"])


if __name__ == "__main__":
    unittest.main()
