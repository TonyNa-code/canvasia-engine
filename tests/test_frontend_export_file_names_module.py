from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "export_file_names.js"


class FrontendExportFileNamesModuleTests(unittest.TestCase):
    def test_export_file_names_build_stable_dated_project_names(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{
              window: {{
                CanvasiaEditorCommon: {{
                  sanitizeFileName(value) {{
                    return String(value ?? "")
                      .trim()
                      .replace(/[\\\\/:*?"<>|]/g, "_")
                      .replace(/\\s+/g, "_")
                      .replace(/_+/g, "_")
                      .replace(/^_+|_+$/g, "");
                  }},
                }},
              }},
            }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorExportFileNames;
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              dateStamp: tools.buildFileNameDateStamp("2026-07-06T10:20:30+08:00"),
              invalidDateStampLength: tools.buildFileNameDateStamp("not-a-date").length,
              baseName: tools.getProjectFileNameBase({{ projectTitle: " Demo:视觉小说 / v1 " }}),
              fallbackBaseName: tools.getProjectFileNameBase({{ projectTitle: "***", fallback: "canvasia-engine" }}),
              extension: tools.normalizeExtension(".markdown"),
              defaultExtension: tools.normalizeExtension(""),
              datedName: tools.buildDatedProjectFileName("release evidence pack", ".md", {{
                projectTitle: " Demo:视觉小说 / v1 ",
                dateValue: "2026-07-06T10:20:30+08:00",
              }}),
              fallbackName: tools.buildDatedProjectFileName("***", "", {{
                projectTitle: "***",
                fallback: "canvasia-engine",
                dateValue: "2026-07-06T10:20:30+08:00",
              }}),
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
        self.assertIn("buildDatedProjectFileName", payload["keys"])
        self.assertEqual(payload["dateStamp"], "20260706")
        self.assertEqual(payload["invalidDateStampLength"], 8)
        self.assertEqual(payload["baseName"], "Demo_视觉小说_v1")
        self.assertEqual(payload["fallbackBaseName"], "canvasia-engine")
        self.assertEqual(payload["extension"], "markdown")
        self.assertEqual(payload["defaultExtension"], "md")
        self.assertEqual(payload["datedName"], "Demo_视觉小说_v1_release_evidence_pack_20260706.md")
        self.assertEqual(payload["fallbackName"], "canvasia-engine_export_20260706.md")


if __name__ == "__main__":
    unittest.main()
