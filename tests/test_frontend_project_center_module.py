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
            const openingHtml = tools.renderProjectCenterCard({{
              projectId: "project-opening",
              title: "正在打开的企划",
              template: "school",
              sceneCount: 1,
            }}, "", {{ ...helpers, projectOpenInFlightId: "project-opening" }});
            const renamingHtml = tools.renderProjectCenterCard({{
              projectId: "project-renaming",
              title: "正在改名的企划",
              template: "school",
              sceneCount: 1,
            }}, "", {{ ...helpers, projectRenameInFlightId: "project-renaming" }});
            const duplicatingFormalHtml = tools.renderProjectCenterCard({{
              projectId: "project-duplicating",
              title: "正在复制的企划",
              template: "school",
              sceneCount: 1,
            }}, "", {{ ...helpers, projectDuplicateInFlightId: "project-duplicating" }});
            const duplicatingSampleHtml = tools.renderProjectCenterCard({{
              projectId: "sample-duplicating",
              title: "正在复制的示例",
              template: "sample",
              isSample: true,
              sceneCount: 1,
            }}, "", {{ ...helpers, projectDuplicateInFlightId: "sample-duplicating" }});
            const deletingHtml = tools.renderProjectCenterCard({{
              projectId: "project-deleting",
              title: "正在删除的企划",
              template: "school",
              sceneCount: 1,
            }}, "", {{ ...helpers, projectDeleteInFlightId: "project-deleting" }});
            const lockedCardHtml = tools.renderProjectCenterCard({{
              projectId: "project-locked",
              title: "被其它操作锁住的企划",
              template: "school",
              sceneCount: 2,
            }}, "", {{
              ...helpers,
              projectCenterOperationInFlightMessage: "正在打开项目，请稍等...",
            }});
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
            const busyHeroHtml = tools.renderProjectCenterHero({{
              localProjectCount: 2,
              projectCenterMode: "beginner",
              projectCenterModeLabel: "新手模式",
            }}, {{
              escapeHtml,
              projectCreateInFlight: true,
              projectCenterRefreshInFlight: true,
            }});
            const lockedHeroHtml = tools.renderProjectCenterHero({{
              localProjectCount: 2,
              projectCenterMode: "advanced",
              projectCenterModeLabel: "高级模式",
            }}, {{
              escapeHtml,
              projectCenterOperationInFlightMessage: "正在打开项目，请稍等...",
            }});
            const emptyListHtml = tools.renderProjectCenterProjectList([], "", helpers);
            const busyEmptyListHtml = tools.renderProjectCenterProjectList([], "", {{
              ...helpers,
              projectCreateInFlight: true,
            }});
            const lockedEmptyListHtml = tools.renderProjectCenterProjectList([], "", {{
              ...helpers,
              projectCenterOperationInFlightMessage: "正在打开项目，请稍等...",
            }});
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
              openingHtml,
              renamingHtml,
              duplicatingFormalHtml,
              duplicatingSampleHtml,
              deletingHtml,
              lockedCardHtml,
              fallbackHtml,
              heroHtml,
              busyHeroHtml,
              lockedHeroHtml,
              emptyListHtml,
              busyEmptyListHtml,
              lockedEmptyListHtml,
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
        self.assertIn("打开中...", payload["openingHtml"])
        self.assertIn('aria-busy="true"', payload["openingHtml"])
        self.assertIn('disabled aria-disabled="true"', payload["openingHtml"])
        self.assertIn("is-busy", payload["openingHtml"])
        self.assertIn("改名中...", payload["renamingHtml"])
        self.assertIn('aria-busy="true"', payload["renamingHtml"])
        self.assertIn('disabled aria-disabled="true"', payload["renamingHtml"])
        self.assertIn("is-busy", payload["renamingHtml"])
        self.assertIn("复制中...", payload["duplicatingFormalHtml"])
        self.assertIn('aria-busy="true"', payload["duplicatingFormalHtml"])
        self.assertIn('data-action="duplicate-project"', payload["duplicatingFormalHtml"])
        self.assertIn("复制中...", payload["duplicatingSampleHtml"])
        self.assertIn('aria-busy="true"', payload["duplicatingSampleHtml"])
        self.assertIn("is-busy", payload["duplicatingSampleHtml"])
        self.assertIn("删除中...", payload["deletingHtml"])
        self.assertIn('aria-busy="true"', payload["deletingHtml"])
        self.assertIn('disabled aria-disabled="true"', payload["deletingHtml"])
        self.assertIn("is-busy", payload["deletingHtml"])
        self.assertIn("被其它操作锁住的企划", payload["lockedCardHtml"])
        self.assertIn("is-locked", payload["lockedCardHtml"])
        self.assertIn('disabled aria-disabled="true"', payload["lockedCardHtml"])
        self.assertIn('title="正在打开项目，请稍等..."', payload["lockedCardHtml"])
        self.assertNotIn('aria-busy="true"', payload["lockedCardHtml"])
        self.assertNotIn("打开中...", payload["lockedCardHtml"])
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
        self.assertIn("第一次建议先生成可试玩 Demo", payload["heroHtml"])
        self.assertIn("推荐从可试玩 Demo 开始", payload["heroHtml"])
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
        self.assertIn('data-action="create-playable-demo-project"', payload["heroHtml"])
        self.assertIn("新建可试玩 Demo", payload["heroHtml"])
        self.assertIn("想马上试玩就选 Demo 项目", payload["heroHtml"])
        self.assertIn('data-action="refresh-project-center"', payload["heroHtml"])
        self.assertIn("准备中...", payload["busyHeroHtml"])
        self.assertIn("刷新中...", payload["busyHeroHtml"])
        self.assertIn('data-action="create-project"', payload["busyHeroHtml"])
        self.assertIn('data-action="create-playable-demo-project"', payload["busyHeroHtml"])
        self.assertIn('data-action="refresh-project-center"', payload["busyHeroHtml"])
        self.assertIn('aria-busy="true"', payload["busyHeroHtml"])
        self.assertIn('disabled aria-disabled="true"', payload["busyHeroHtml"])
        self.assertIn("is-busy", payload["busyHeroHtml"])
        self.assertIn("is-locked", payload["lockedHeroHtml"])
        self.assertIn('disabled aria-disabled="true"', payload["lockedHeroHtml"])
        self.assertIn('title="正在打开项目，请稍等..."', payload["lockedHeroHtml"])
        self.assertIn('data-action="open-beginner-tutorial"', payload["lockedHeroHtml"])
        self.assertNotIn('aria-busy="true"', payload["lockedHeroHtml"])
        self.assertNotIn("准备中...", payload["lockedHeroHtml"])
        self.assertNotIn("刷新中...", payload["lockedHeroHtml"])
        self.assertIn("现在还是一张白纸", payload["emptyListHtml"])
        self.assertIn("第一次建议先生成一个可试玩 Demo", payload["emptyListHtml"])
        self.assertIn('data-action="create-playable-demo-project"', payload["emptyListHtml"])
        self.assertIn('data-action="create-project"', payload["emptyListHtml"])
        self.assertIn("新建可试玩 Demo", payload["emptyListHtml"])
        self.assertIn("准备中...", payload["busyEmptyListHtml"])
        self.assertIn('aria-busy="true"', payload["busyEmptyListHtml"])
        self.assertIn('disabled aria-disabled="true"', payload["busyEmptyListHtml"])
        self.assertIn("is-busy", payload["busyEmptyListHtml"])
        self.assertIn("is-locked", payload["lockedEmptyListHtml"])
        self.assertIn('disabled aria-disabled="true"', payload["lockedEmptyListHtml"])
        self.assertIn('title="正在打开项目，请稍等..."', payload["lockedEmptyListHtml"])
        self.assertNotIn('aria-busy="true"', payload["lockedEmptyListHtml"])
        self.assertIn("project-card-grid", payload["listHtml"])
        self.assertEqual(payload["listHtml"].count("project-card "), 2)
        self.assertIn("我的 &lt;企划&gt;", payload["listHtml"])
        self.assertIn("复制成正式项目", payload["listHtml"])


if __name__ == "__main__":
    unittest.main()
