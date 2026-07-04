from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "asset_rights_sheet.js"


class FrontendAssetRightsSheetModuleTests(unittest.TestCase):
    def test_asset_rights_sheet_detects_license_credit_and_ai_provenance_risks(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorAssetRightsSheet;
            const data = {{
              project: {{ title: "Rights Demo" }},
              assetList: [
                {{
                  id: "bg_ok",
                  type: "background",
                  name: "黄昏教室",
                  path: "assets/bg_ok.png",
                  fileExists: true,
                  license: "CC-BY 4.0",
                  sourceUrl: "https://example.com/bg",
                  author: "Studio A",
                  credit: "Background by Studio A",
                  commercialUse: true,
                }},
                {{
                  id: "bgm_missing",
                  type: "bgm",
                  name: "放课后钢琴",
                  path: "assets/bgm.ogg",
                  fileExists: true,
                }},
                {{
                  id: "sprite_placeholder",
                  type: "sprite",
                  name: "placeholder heroine",
                  path: "assets/tmp_heroine.png",
                  fileExists: true,
                  license: "Royalty-free commercial",
                  source: "internal draft",
                  author: "Canvasia Team",
                  commercialUse: true,
                }},
                {{
                  id: "ai_cg",
                  type: "cg",
                  name: "AI 生成回忆 CG",
                  path: "assets/ai_cg.png",
                  fileExists: true,
                  license: "Creator-owned commercial",
                  source: "self-generated",
                  generatedByAi: true,
                  aiProvider: "OpenAI",
                  commercialUse: true,
                }},
                {{
                  id: "font_nc",
                  type: "font",
                  name: "不可商用字体",
                  path: "assets/font.ttf",
                  fileExists: true,
                  license: "CC-BY-NC",
                  source: "https://example.com/font",
                  author: "Font Maker",
                }},
                {{
                  id: "unused_missing",
                  type: "cg",
                  name: "备用 CG",
                  path: "assets/unused.png",
                  fileExists: true,
                }},
              ],
              assetUsage: {{
                bg_ok: [{{ label: "场景：教室", meta: "背景" }}],
                bgm_missing: [{{ label: "场景：放学", meta: "BGM" }}],
                sprite_placeholder: [{{ label: "角色：女主", meta: "默认立绘" }}],
                ai_cg: [{{ label: "回想馆", meta: "CG" }}],
                font_nc: [{{ label: "成品 UI", meta: "字体" }}],
              }},
            }};
            const sheet = tools.buildAssetRightsSheet(data);
            const digest = tools.getAssetRightsStatusDigest(sheet);
            const markdown = tools.buildAssetRightsMarkdown(sheet, {{
              projectTitle: "Rights Demo",
              generatedAt: "2026-07-04 04:00:00",
            }});
            const csv = tools.buildAssetRightsCsv(sheet);
            const panel = tools.renderAssetRightsSheetPanel(sheet);
            const creditsDraft = tools.buildAssetCreditsRollDraft(sheet, {{ projectTitle: "Rights Demo" }});
            const creditsScript = tools.buildAssetCreditsScript(sheet, {{ projectTitle: "Rights Demo" }});
            const editor = tools.renderAssetRightsEditor(data.assetList[0]);
            const fakeDocument = {{
              getElementById(id) {{
                const values = {{
                  assetRightsLicenseInput: {{ value: "自制授权" }},
                  assetRightsCommercialInput: {{ value: "allowed" }},
                  assetRightsSourceInput: {{ value: "本人绘制" }},
                  assetRightsAuthorInput: {{ value: "Canvasia Team" }},
                  assetRightsCreditInput: {{ value: "Art by Canvasia Team" }},
                  assetRightsAiProviderInput: {{ value: "OpenAI" }},
                  assetRightsPromptInput: {{ value: "visual novel classroom" }},
                  assetRightsGeneratedByAiInput: {{ checked: true }},
                  assetRightsAttributionRequiredInput: {{ checked: true }},
                }};
                return values[id] ?? {{ value: "", checked: false }};
              }},
            }};
            const collected = tools.collectAssetRightsFormValues(fakeDocument);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              sheet,
              digest,
              markdown,
              csv,
              panel,
              creditsDraft,
              creditsScript,
              editor,
              collected,
              bgLabel: tools.getAssetTypeLabel("background"),
              commercialFormValue: tools.getAssetCommercialUseFormValue(data.assetList[0]),
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
        self.assertIn("buildAssetRightsSheet", payload["keys"])
        self.assertIn("buildAssetRightsMarkdown", payload["keys"])
        self.assertIn("buildAssetRightsCsv", payload["keys"])
        self.assertIn("buildAssetCreditsRollDraft", payload["keys"])
        self.assertIn("buildAssetCreditsScript", payload["keys"])
        self.assertIn("collectAssetRightsFormValues", payload["keys"])
        self.assertIn("renderAssetRightsEditor", payload["keys"])
        self.assertIn("renderAssetRightsSheetPanel", payload["keys"])
        self.assertEqual(payload["sheet"]["summary"]["assetCount"], 6)
        self.assertEqual(payload["sheet"]["summary"]["usedAssetCount"], 5)
        self.assertEqual(payload["sheet"]["summary"]["usedMissingLicenseCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["missingSourceCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["usedPlaceholderCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["aiGeneratedCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["aiProvenanceMissingCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["nonCommercialCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["commercialUnknownCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["blockerCount"], 1)
        self.assertEqual(payload["sheet"]["summary"]["warningCount"], 5)
        self.assertEqual(payload["sheet"]["summary"]["tipCount"], 1)
        self.assertEqual(payload["digest"]["status"], "blocked")
        issue_codes = [issue["code"] for issue in payload["sheet"]["issues"]]
        self.assertIn("asset_rights_noncommercial", issue_codes)
        self.assertIn("asset_rights_license_missing", issue_codes)
        self.assertIn("asset_rights_source_missing", issue_codes)
        self.assertIn("asset_rights_placeholder_used", issue_codes)
        self.assertIn("asset_rights_ai_provenance_missing", issue_codes)
        self.assertIn("asset_rights_unused_license_missing", issue_codes)
        self.assertIn("# Rights Demo 素材授权与署名清单", payload["markdown"])
        self.assertIn("Background by Studio A", payload["markdown"])
        self.assertIn('"不可商用字体"', payload["csv"])
        self.assertIn('data-action="export-asset-rights-markdown"', payload["panel"])
        self.assertIn('data-action="copy-asset-rights-credits-script"', payload["panel"])
        self.assertIn('data-action="add-asset-rights-credits-roll"', payload["panel"])
        self.assertTrue(payload["creditsDraft"]["hasCredits"])
        self.assertEqual(payload["creditsDraft"]["type"], "credits_roll")
        self.assertIn("黄昏教室：Background by Studio A", payload["creditsDraft"]["lines"])
        self.assertIn('credits title "STAFF"', payload["creditsScript"])
        self.assertIn("Background by Studio A", payload["creditsScript"])
        self.assertIn("assetRightsLicenseInput", payload["editor"])
        self.assertEqual(payload["collected"]["license"], "自制授权")
        self.assertEqual(payload["collected"]["commercialUse"], "可商用")
        self.assertEqual(payload["collected"]["sourceUrl"], "本人绘制")
        self.assertTrue(payload["collected"]["generatedByAi"])
        self.assertEqual(payload["commercialFormValue"], "allowed")
        self.assertEqual(payload["bgLabel"], "背景")


if __name__ == "__main__":
    unittest.main()
