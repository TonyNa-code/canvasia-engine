from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "visual_effects.js"
APP_PATH = ROOT_DIR / "prototype_editor" / "app.js"


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
            const tools = context.window.CanvasiaEditorVisualEffects;
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
                tools.getPositionLabel("right"),
                tools.getTransitionLabel("slide_left"),
                tools.getTextSpeedLabel("instant"),
                tools.getDialogThemeLabel("paper"),
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
                tools.getSafePosition("bad"),
                tools.getSafeTransition("bad"),
                tools.getSafeTextSpeed("bad"),
                tools.getSafeDialogTheme("bad"),
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
                tools.getSafeTransitionDurationMs("1250"),
                tools.getSafeTransitionDurationMs("-20"),
                tools.getSafeTransitionDurationMs("9000"),
                tools.getSafeTransitionDurationMs("bad"),
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
                tools.parseCreditsLines("制作：Creator\\n\\n 音乐：夜雨 "),
                tools.getCreditsLines([" 导演 ", "", null, "脚本"]),
                tools.getCreditsLinesText(["Staff", " Cast "]),
              ],
              characterStage: [
                tools.getSafeCharacterStage({{ offsetX: "90", offsetY: "-90", scale: "15", opacity: "0", layer: "20", flipX: "true" }}),
                tools.getSafeCharacterStage({{ offsetX: "", offsetY: "12px", scale: "", opacity: "", layer: "", flipX: "off" }}),
                tools.getSafeCharacterStage(null),
                tools.getCharacterStagePreset("foreground"),
                tools.getCharacterStagePreset("missing").id,
                tools.getCharacterStagePreset("right_focus").position,
                tools.getCharacterStagePreset("right_focus").stage,
                tools.getCharacterStagePresetEntries().map((preset) => preset.id),
                tools.getMatchingCharacterStagePresetId(tools.getCharacterStagePreset("foreground").stage, "center"),
                tools.getMatchingCharacterStagePresetId(tools.getCharacterStagePreset("right_focus").stage, "right"),
                tools.getMatchingCharacterStagePresetId(tools.getCharacterStagePreset("right_focus").stage, "left"),
                tools.applyCharacterStageDelta({{ offsetX: 59, offsetY: -44, scale: 219, layer: 9 }}, {{ offsetX: 8, offsetY: -8, scale: 8, layer: 4 }}),
                tools.getCharacterStageAdjustment("move_left"),
                tools.applyCharacterStageAdjustment({{ offsetX: 58, scale: 218, opacity: 5, layer: 9, flipX: false }}, "move_right"),
                tools.applyCharacterStageAdjustment({{ flipX: false }}, "flip_toggle").flipX,
                tools.applyCharacterStageAdjustment({{ offsetX: 12 }}, "reset"),
                tools.getCharacterStageAdjustmentEntries().map((adjustment) => adjustment.id).slice(-2),
                tools.getCharacterStageStyle({{ offsetX: 12, offsetY: -8, scale: 125, opacity: 70, layer: 3, flipX: true }}),
                tools.getCharacterStageSummary({{ offsetX: 12, offsetY: -8, scale: 125, opacity: 70, layer: 3, flipX: true }}),
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
        self.assertIn("getMatchingCharacterStagePresetId", payload["keys"])
        self.assertEqual(
            payload["labels"],
            [
                "很强",
                "正常",
                "暖光",
                "慢慢亮起",
                "恢复正常",
                "向左看",
                "黑白回忆",
                "只虚化背景",
                "铺满裁切",
                "叠在当前画面上",
                "右侧",
                "从左侧滑入 / 滑出",
                "立刻显示",
                "纸页回忆",
            ],
        )
        self.assertEqual(
            payload["safeValues"],
            ["medium", "long", "white", "strong", "white", "right", "medium", "clear", "medium", "fill", "center", "fade", "normal", "project"],
        )
        self.assertEqual(payload["metrics"][0:5], [16, 0.42, 0.36, "255, 120, 120", "255, 252, 247"])
        self.assertEqual(payload["metrics"][5:11], [0.88, 1, "28% 52%", 12, -4, 0])
        self.assertEqual(payload["metrics"][11:], [1250, 0, 5000, 360])
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
        self.assertEqual(payload["videoAndCredits"][8], ["制作：Creator", "音乐：夜雨"])
        self.assertEqual(payload["videoAndCredits"][9], ["导演", "脚本"])
        self.assertEqual(payload["videoAndCredits"][10], "Staff\nCast")
        self.assertEqual(
            payload["characterStage"][0],
            {"offsetX": 60, "offsetY": -45, "scale": 45, "opacity": 0, "layer": 10, "flipX": True},
        )
        self.assertEqual(
            payload["characterStage"][1],
            {"offsetX": 0, "offsetY": 12, "scale": 100, "opacity": 100, "layer": 0, "flipX": False},
        )
        self.assertEqual(
            payload["characterStage"][2],
            {"offsetX": 0, "offsetY": 0, "scale": 100, "opacity": 100, "layer": 0, "flipX": False},
        )
        self.assertEqual(payload["characterStage"][3]["id"], "foreground")
        self.assertEqual(payload["characterStage"][3]["stage"]["scale"], 152)
        self.assertEqual(payload["characterStage"][3]["stage"]["layer"], 5)
        self.assertEqual(payload["characterStage"][4], "default")
        self.assertEqual(payload["characterStage"][5], "right")
        self.assertEqual(
            payload["characterStage"][6],
            {"offsetX": -4, "offsetY": 0, "scale": 106, "opacity": 100, "layer": 0, "flipX": True},
        )
        self.assertEqual(
            payload["characterStage"][7],
            ["default", "close", "distant", "foreground", "memory", "left_focus", "right_focus"],
        )
        self.assertEqual(payload["characterStage"][8], "foreground")
        self.assertEqual(payload["characterStage"][9], "right_focus")
        self.assertEqual(payload["characterStage"][10], "")
        self.assertEqual(
            payload["characterStage"][11],
            {"offsetX": 60, "offsetY": -45, "scale": 220, "opacity": 100, "layer": 10, "flipX": False},
        )
        self.assertEqual(payload["characterStage"][12]["id"], "move_left")
        self.assertEqual(payload["characterStage"][12]["delta"], {"offsetX": -4})
        self.assertEqual(
            payload["characterStage"][13],
            {"offsetX": 60, "offsetY": 0, "scale": 218, "opacity": 5, "layer": 9, "flipX": False},
        )
        self.assertTrue(payload["characterStage"][14])
        self.assertEqual(
            payload["characterStage"][15],
            {"offsetX": 0, "offsetY": 0, "scale": 100, "opacity": 100, "layer": 0, "flipX": False},
        )
        self.assertEqual(payload["characterStage"][16], ["flip_toggle", "reset"])
        self.assertEqual(
            payload["characterStage"][17],
            "--sprite-position-x:50%;--sprite-offset-x:12%;--sprite-offset-y:-8%;--sprite-scale:1.250;--sprite-opacity:0.70;--sprite-layer:3;--sprite-flip-x:-1;z-index:23;",
        )
        self.assertEqual(payload["characterStage"][18], "X 12% / Y -8% / 125% / 透明 70% / 层级 3 / 镜像")

    def test_editor_app_uses_visual_effect_module_constants(self) -> None:
        app_source = APP_PATH.read_text(encoding="utf-8")

        self.assertIn("} = visualEffectTools;", app_source)
        self.assertNotIn("const SHAKE_INTENSITY_LABELS = visualEffectTools?.SHAKE_INTENSITY_LABELS", app_source)
        self.assertNotIn("const SCREEN_COLOR_GRADE_DEFAULTS = visualEffectTools?.SCREEN_COLOR_GRADE_DEFAULTS", app_source)
        self.assertNotIn("const DIALOG_THEME_LABELS = visualEffectTools?.DIALOG_THEME_LABELS", app_source)
        self.assertIn("TEXT_SPEED_LABELS,", app_source)
        self.assertIn("DIALOG_THEME_LABELS,", app_source)


if __name__ == "__main__":
    unittest.main()
