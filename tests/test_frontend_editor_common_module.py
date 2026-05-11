from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "editor_common.js"


class FrontendEditorCommonModuleTests(unittest.TestCase):
    def test_editor_common_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorCommon;
            const result = {{
              keys: Object.keys(tools).sort(),
              fileNames: [
                tools.sanitizeFileName("  chapter 01:雨夜/告白?.txt  "),
                tools.sanitizeFileName("***"),
                tools.sanitizeFileName(null),
              ],
              csvCells: [
                tools.formatCsvCell('她说 "你好"'),
                tools.formatCsvCell(null),
              ],
              truncation: [
                tools.truncateText("  abc  ", 4),
                tools.truncateText("abcdef", 4),
                tools.truncateText("abcdef", 0),
                tools.truncateText(null, 4),
              ],
              dates: [
                tools.formatDate(""),
                tools.formatDate("not-a-date"),
                tools.formatDate("2026-05-06T00:00:00.000Z", {{
                  locale: "en-US",
                  formatOptions: {{ timeZone: "UTC", hour12: false }},
                }}),
              ],
              numbers: [
                tools.getSafeNonNegativeNumber("12px", 7),
                tools.getSafeNonNegativeNumber("-5", 7),
                tools.getSafeNonNegativeNumber("bad", 7),
                tools.getSafeNumber("3.5rem", 9),
                tools.getSafeNumber("", 9),
                tools.getSafeNumber("0", 9),
              ],
              urls: [
                tools.buildTemplateAssetUrl("/背景/scene one.png", "/public/root/"),
                tools.buildTemplateAssetUrl("voices\\\\hero line.ogg", "assets"),
                tools.buildTemplateAssetUrl("", "assets"),
                tools.buildTemplateAssetUrl("bg.png", ""),
              ],
              sizes: [
                tools.formatFileSize(-1),
                tools.formatFileSize(512),
                tools.formatFileSize(1536),
                tools.formatFileSize(15 * 1024),
                tools.formatFileSize(2.5 * 1024 * 1024),
                tools.formatFileSize(18 * 1024 * 1024),
              ],
              clamp: [
                tools.clamp(-1, 0, 10),
                tools.clamp(4, 0, 10),
                tools.clamp(20, 0, 10),
              ],
              html: tools.escapeHtml(`<button data-x="1">'&'</button>`),
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
        self.assertIn("escapeHtml", payload["keys"])
        self.assertIn("buildTemplateAssetUrl", payload["keys"])
        self.assertEqual(payload["fileNames"], ["chapter_01_雨夜_告白_.txt", "", ""])
        self.assertEqual(payload["csvCells"], ['"她说 ""你好"""', '""'])
        self.assertEqual(payload["truncation"], ["abc", "abc…", "a…", ""])
        self.assertEqual(payload["dates"][0], "未知")
        self.assertEqual(payload["dates"][1], "not-a-date")
        self.assertIn("5/6/2026", payload["dates"][2])
        self.assertEqual(payload["numbers"], [12, 0, 7, 3.5, 9, 0])
        self.assertEqual(
            payload["urls"],
            [
                "/public/root/%E8%83%8C%E6%99%AF/scene%20one.png",
                "assets/voices/hero%20line.ogg",
                "",
                "",
            ],
        )
        self.assertEqual(payload["sizes"], ["未知", "512 B", "1.5 KB", "15 KB", "2.5 MB", "18 MB"])
        self.assertEqual(payload["clamp"], [0, 4, 10])
        self.assertEqual(payload["html"], "&lt;button data-x=&quot;1&quot;&gt;&#39;&amp;&#39;&lt;/button&gt;")


if __name__ == "__main__":
    unittest.main()
