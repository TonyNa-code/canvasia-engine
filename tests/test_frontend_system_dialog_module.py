from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "system_dialog.js"
APP_PATH = ROOT_DIR / "prototype_editor" / "app.js"


class FrontendSystemDialogModuleTests(unittest.TestCase):
    def test_system_dialog_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorSystemDialog;
            const normalized = tools.normalizeSystemDialogOptions({{
              title: " 删除项目？ ",
              message: ["第一行", "", "第二行"],
              tone: "danger",
              copyable: true,
              input: {{
                value: "  旧名字  ",
                placeholder: "新名字",
                maxLength: "42",
                requiredMessage: "必须填写",
              }},
            }});
            const result = {{
              keys: Object.keys(tools).sort(),
              normalized,
              failure: tools.inferSystemAlertOptions("导出失败：missing bg.png"),
              softFailure: tools.inferSystemAlertOptions("保存没有成功：网络异常"),
              warning: tools.inferSystemAlertOptions("先选中一个场景"),
              info: tools.inferSystemAlertOptions("保存完成"),
              marks: [
                tools.getSystemDialogToneMark("danger"),
                tools.getSystemDialogToneMark("warning"),
                tools.getSystemDialogToneMark("success"),
                tools.getSystemDialogToneMark("info"),
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
        self.assertIn("createSystemDialogController", payload["keys"])
        self.assertIn("normalizeSystemDialogOptions", payload["keys"])
        self.assertEqual(payload["normalized"]["title"], " 删除项目？ ")
        self.assertEqual(payload["normalized"]["message"], "第一行\n第二行")
        self.assertEqual(payload["normalized"]["tone"], "danger")
        self.assertTrue(payload["normalized"]["copyText"])
        self.assertEqual(payload["normalized"]["input"]["value"], "  旧名字  ")
        self.assertEqual(payload["normalized"]["input"]["maxLength"], 42)
        self.assertEqual(payload["normalized"]["input"]["requiredMessage"], "必须填写")
        self.assertEqual(payload["failure"]["title"], "操作失败")
        self.assertEqual(payload["failure"]["tone"], "danger")
        self.assertTrue(payload["failure"]["copyable"])
        self.assertEqual(payload["softFailure"]["title"], "操作失败")
        self.assertEqual(payload["softFailure"]["tone"], "danger")
        self.assertEqual(payload["warning"]["title"], "需要处理")
        self.assertEqual(payload["warning"]["tone"], "warning")
        self.assertEqual(payload["info"]["title"], "提示")
        self.assertEqual(payload["info"]["tone"], "info")
        self.assertEqual(payload["marks"], ["!", "?", "✓", "i"])

    def test_app_uses_engine_alert_wrapper_for_user_messages(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")

        self.assertIn("function showEngineAlert", source)
        self.assertIn("function showEngineConfirm", source)
        self.assertNotIn("window.alert(", source)
        self.assertNotIn("window.confirm(", source)
        self.assertGreaterEqual(source.count("showEngineAlert("), 30)
        self.assertGreaterEqual(source.count("showEngineConfirm("), 10)


if __name__ == "__main__":
    unittest.main()
