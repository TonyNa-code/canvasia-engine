from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "visual_effects.js"


class FrontendVisualEffectsModuleTests(unittest.TestCase):
    def test_visual_effect_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.TonyNaEditorVisualEffects;
            const result = {{
              keys: Object.keys(tools).sort(),
              labels: [
                tools.getShakeIntensityLabel("heavy"),
                tools.getEffectDurationLabel("unknown"),
                tools.getFlashColorLabel("warm"),
                tools.getFadeActionLabel("fade_in"),
                tools.getCameraZoomActionLabel("reset"),
                tools.getCameraPanTargetLabel("left"),
                tools.getScreenFilterPresetLabel("mono"),
                tools.getDepthBlurFocusLabel("full"),
                tools.getVideoFitLabel("cover"),
                tools.getCreditsBackgroundLabel("transparent"),
              ],
              safeValues: [
                tools.getSafeShakeIntensity("x"),
                tools.getSafeEffectDuration("long"),
                tools.getSafeFlashColor("bad"),
                tools.getSafeFlashIntensity("strong"),
                tools.getSafeFadeColor("white"),
                tools.getSafeCameraZoomFocus("right"),
                tools.getSafeCameraPanStrength("bad"),
                tools.getSafeScreenFilterAction("clear"),
                tools.getSafeDepthBlurStrength("bad"),
                tools.getSafeVideoFit("fill"),
              ],
              metrics: [
                tools.getShakeDistance("heavy"),
                tools.getEffectDurationSeconds("short"),
                tools.getFlashOpacity("soft"),
                tools.getFlashColorRgb("red"),
                tools.getFadeColorRgb("white"),
                tools.getCameraZoomScale("zoom_out", "heavy"),
                tools.getCameraZoomScale("reset", "heavy"),
                tools.getCameraZoomOrigin("left"),
                tools.getCameraPanOffset("left", "heavy"),
                tools.getCameraPanOffset("right", "light"),
                tools.getCameraPanOffset("center", "heavy"),
              ],
              screen: [
                tools.getScreenFilterCss({{ preset: "cold", strength: "strong" }}),
                tools.getScreenFilterCss(null),
                tools.getScreenFilterWash({{ preset: "dream", strength: "soft" }}),
                tools.getScreenFilterWash(null),
                tools.getSafeScreenColorGrade({{ brightness: "999", temperature: "-140", vignette: "bad" }}),
                tools.getScreenColorGradeCss({{ brightness: 120, contrast: 80, saturation: 135, hue: 18, temperature: -30 }}),
                tools.getScreenColorGradeSummary({{ brightness: 120, temperature: -30, vignette: 20 }}),
                tools.getScreenFilterVignette({{ grade: {{ vignette: 50 }} }}),
                tools.getScreenFilterWash({{ preset: "memory", strength: "medium", grade: {{ temperature: 80 }} }}),
              ],
              depth: [
                tools.getDepthBlurBackdropPx("strong"),
                tools.getDepthBlurParticlePx("medium"),
                tools.getDepthBlurSpritePx("soft"),
                tools.getDepthBlurSpriteOpacity("bad"),
              ],
              videoAndCredits: [
                tools.getSafeVideoVolume("-20"),
                tools.getSafeVideoVolume("49.5"),
                tools.getSafeVideoVolume("999"),
                tools.getSafeVideoVolume("bad"),
                tools.getSafeCreditsDuration("2"),
                tools.getSafeCreditsDuration("35.6"),
                tools.getSafeCreditsDuration("999"),
                tools.getSafeCreditsDuration("bad"),
                tools.parseCreditsLines("制作：Tony Na\\n\\n 音乐：夜雨 "),
                tools.getCreditsLines([" 导演 ", "", null, "脚本"]),
                tools.getCreditsLinesText(["Staff", " Cast "]),
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
        self.assertIn("getScreenFilterCss", payload["keys"])
        self.assertIn("getCreditsLinesText", payload["keys"])
        self.assertEqual(
            payload["labels"],
            ["很强", "正常", "暖光", "慢慢亮起", "恢复正常", "向左看", "黑白回忆", "只虚化背景", "铺满裁切", "叠在当前画面上"],
        )
        self.assertEqual(
            payload["safeValues"],
            ["medium", "long", "white", "strong", "white", "right", "medium", "clear", "medium", "fill"],
        )
        self.assertEqual(payload["metrics"][0:5], [16, 0.42, 0.36, "255, 120, 120", "255, 252, 247"])
        self.assertEqual(payload["metrics"][5:], [0.88, 1, "28% 52%", 12, -4, 0])
        self.assertIn("hue-rotate(192deg)", payload["screen"][0])
        self.assertEqual(payload["screen"][1], "")
        self.assertEqual(payload["screen"][2]["opacity"], 0.12)
        self.assertIn("rgba(255, 241, 250", payload["screen"][2]["background"])
        self.assertEqual(payload["screen"][3], {"background": "transparent", "opacity": 0})
        self.assertEqual(
            payload["screen"][4],
            {"brightness": 180, "contrast": 100, "saturation": 100, "hue": 0, "temperature": -100, "vignette": 0},
        )
        self.assertIn("brightness(1.200)", payload["screen"][5])
        self.assertIn("hue-rotate(20.40deg)", payload["screen"][5])
        self.assertEqual(payload["screen"][6], "亮度 120 / 冷暖 -30 / 暗角 20")
        self.assertAlmostEqual(payload["screen"][7], 0.34)
        self.assertEqual(payload["screen"][8]["opacity"], 0.328)
        self.assertIn("rgba(255, 220, 166", payload["screen"][8]["background"])
        self.assertEqual(payload["depth"], [10, 2.4, 1.8, 0.58])
        self.assertEqual(payload["videoAndCredits"][0:8], [0, 50, 100, 100, 4, 36, 180, 18])
        self.assertEqual(payload["videoAndCredits"][8], ["制作：Tony Na", "音乐：夜雨"])
        self.assertEqual(payload["videoAndCredits"][9], ["导演", "脚本"])
        self.assertEqual(payload["videoAndCredits"][10], "Staff\nCast")


if __name__ == "__main__":
    unittest.main()
