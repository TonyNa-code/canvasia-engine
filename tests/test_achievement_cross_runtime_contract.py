from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path

from native_runtime.runtime_achievements import (
    get_custom_achievement_storage_id,
    sanitize_achievement_unlock_block,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
WEB_MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_achievements.js"


class AchievementCrossRuntimeContractTests(unittest.TestCase):
    def test_web_and_native_generate_the_same_stable_identity(self) -> None:
        block = {
            "id": "unlock-special",
            "type": "achievement_unlock",
            "achievementId": "  秘密 Route #1  ",
            "title": "秘密路线",
            "hiddenBeforeUnlock": True,
        }
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(WEB_MODULE_PATH))}, "utf8"), context);
            process.stdout.write(JSON.stringify(
              context.window.CanvasiaRuntimeAchievements.sanitizeAchievementUnlockBlock({json.dumps(block, ensure_ascii=False)})
            ));
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
        web = json.loads(completed.stdout)
        native = sanitize_achievement_unlock_block(block)
        self.assertEqual(web["authorId"], native["authorId"])
        self.assertEqual(web["id"], native["id"])
        self.assertEqual(web["hiddenBeforeUnlock"], native["hiddenBeforeUnlock"])
        self.assertEqual(native["id"], get_custom_achievement_storage_id("秘密 route 1"))


if __name__ == "__main__":
    unittest.main()
