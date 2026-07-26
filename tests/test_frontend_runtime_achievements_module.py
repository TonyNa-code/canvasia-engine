from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_achievements.js"


class FrontendRuntimeAchievementsModuleTests(unittest.TestCase):
    def test_custom_achievement_contract_and_hidden_presentation(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaRuntimeAchievements;
            const scenes = [{{
              id: "scene-a",
              blocks: [
                {{
                  id: "unlock-1", type: "achievement_unlock", achievementId: " First Meet! ",
                  title: "初次相遇", titleTranslations: {{ en: "First Encounter" }},
                  description: "见到她。", category: "隐藏路线", requirement: "进入秘密房间",
                  hiddenBeforeUnlock: true, iconAssetId: "icon-1",
                }},
                {{
                  id: "unlock-2", type: "achievement_unlock", achievementId: "first meet",
                  title: "重复定义",
                }},
              ],
            }}];
            const definitions = tools.buildAchievementDefinitions({{
              scenes,
              unlockedAchievementIds: ["custom:first-meet"],
              metrics: {{ sceneCount: 1, choiceBlockCount: 1 }},
              getLocalizedValue: (source, key, fallback) => source?.[`${{key}}Translations`]?.en ?? fallback,
              getAssetUrl: (assetId) => `assets/${{assetId}}.png`,
            }});
            const custom = definitions.find((item) => item.kind === "custom");
            const locked = tools.getAchievementPresentation(custom, false);
            const unlocked = tools.getAchievementPresentation(custom, true);
            const progressEntries = tools.sanitizeAchievementProgressEntries({{
              "custom:first-meet": "2026-07-26T00:00:00Z",
              unknown: "2026-07-26T00:00:00Z",
              first_start: "",
            }}, definitions);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              ids: definitions.map((item) => item.id),
              custom, locked, unlocked, progressEntries,
              safeIds: [
                tools.getSafeAchievementAuthorId("  First Meet!  "),
                tools.getCustomAchievementStorageId("秘密 成就"),
              ],
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
        self.assertIn("buildAchievementDefinitions", payload["keys"])
        self.assertEqual(payload["safeIds"], ["first-meet", "custom:秘密-成就"])
        self.assertEqual(payload["ids"], ["custom:first-meet", "first_start", "first_choice"])
        self.assertEqual(payload["custom"]["name"], "First Encounter")
        self.assertEqual(payload["custom"]["duplicateCount"], 1)
        self.assertEqual(payload["custom"]["iconUrl"], "assets/icon-1.png")
        self.assertEqual(payload["custom"]["progressCurrent"], 1)
        self.assertTrue(payload["locked"]["hidden"])
        self.assertEqual(payload["locked"]["name"], "隐藏成就")
        self.assertFalse(payload["unlocked"]["hidden"])
        self.assertEqual(payload["unlocked"]["name"], "First Encounter")
        self.assertEqual(payload["progressEntries"], [["custom:first-meet", "2026-07-26T00:00:00Z"]])


if __name__ == "__main__":
    unittest.main()
