from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "particle_effects.js"


class FrontendParticleEffectsModuleTests(unittest.TestCase):
    def test_particle_effect_helpers_work_without_browser_dom(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorParticleEffects;
            const result = {{
              keys: Object.keys(tools).sort(),
              labels: [
                tools.getParticleActionLabel("stop"),
                tools.getParticlePresetLabel("glyphs"),
                tools.getParticleIntensityLabel("bad"),
                tools.getParticleSpeedLabel("fast"),
                tools.getParticleWindLabel("left"),
                tools.getParticleAreaLabel("center"),
                tools.getParticleBlendModeLabel("add"),
                tools.getParticleEmissionModeLabel("burst"),
                tools.getParticleEmitterShapeLabel("circle"),
                tools.getParticleFollowTargetLabel("character"),
                tools.getParticleFollowAnchorLabel("feet"),
                tools.getParticleSizeCurveLabel("pulse"),
                tools.getParticleOpacityCurveLabel("pop"),
                tools.getParticleColorCurveLabel("spectral"),
                tools.getParticleForceFieldLabel("orbit"),
                tools.getParticleComboPresetLabel("arcane_stack"),
              ],
              safeValues: [
                tools.getSafeParticleAction("bad"),
                tools.getSafeParticlePreset("bad"),
                tools.getSafeParticleIntensity("heavy"),
                tools.getSafeParticleSpeed("bad"),
                tools.getSafeParticleWind("bad"),
                tools.getSafeParticleArea("bad"),
                tools.getSafeParticleBlendMode("bad"),
                tools.getSafeParticleEmissionMode("bad"),
                tools.getSafeParticleEmitterShape("bad"),
                tools.getSafeParticleFollowTarget("bad"),
                tools.getSafeParticleFollowAnchor("bad"),
                tools.getSafeParticleSizeCurve("bad"),
                tools.getSafeParticleOpacityCurve("bad"),
                tools.getSafeParticleColorCurve("bad"),
                tools.getSafeParticleForceField("bad"),
                tools.getSafeParticleComboPreset("bad"),
              ],
              metrics: [
                tools.getParticleBlendCssValue("add"),
                tools.getParticleBlendCssValue("normal"),
                tools.getParticleDefaultColorCurve("flame"),
                tools.getParticleDefaultColorCurve("unknown"),
                tools.getSafeParticleLayerCount(0),
                tools.getSafeParticleLayerCount(9),
                tools.getSafeParticleClampedNumber("", 70, -160, 280),
                tools.getSafeParticleClampedNumber(null, 70, -160, 280),
                tools.getSafeParticleClampedNumber(0, 9, -5, 5),
                tools.getSafeParticleClampedNumber("bad", 4, 0, 10),
                tools.getSafeParticleColor("#ABCDEF"),
                tools.getSafeParticleColor("bad", "#00aaFF"),
                tools.getSafeParticleColor("bad", "bad"),
                tools.mixParticleColors("#000000", "#ffffff", 0.5),
                tools.mixParticleColors("#ff0000", "#0000ff", 0.25),
                tools.mixParticleColors("#000000", "#ffffff", 1.5),
                tools.makeParticleCustomPresetId("  梦境 粒子!! ", []),
                tools.makeParticleCustomPresetId("Spark FX", ["spark_fx"]),
              ],
              constants: [
                tools.PARTICLE_CUSTOM_COMBO_LAYER_LIMIT,
                tools.PARTICLE_CUSTOM_PRESET_LIMIT,
                tools.PARTICLE_IMAGE_ASSET_TYPES.includes("ui"),
                tools.PARTICLE_SCENE_PRESET_LABELS.magic_circle,
              ],
              configs: [
                tools.PARTICLE_PRESET_DEFAULTS.snow.density,
                tools.getParticlePresetDefaults("bad").density,
                tools.getParticleAdvancedDefaults("rain").emitterY,
                tools.getParticleScenePresetConfig("blizzard").comboPreset,
                tools.getParticleScenePresetConfig("bad"),
                tools.PARTICLE_COMBO_PRESET_CONFIGS.none.length,
                tools.getParticleComboPresetConfig("blizzard_stack")[0].preset,
                tools.getParticleComboPresetConfig("bad").length,
                tools.buildDefaultParticleEffectConfig("flame").colorCurve,
                tools.buildDefaultParticleEffectConfig("bad").preset,
              ],
              particleMath: [
                tools.getParticleSpeedMultiplier("slow"),
                tools.getParticleSpeedMultiplier("bad"),
                Number(tools.getParticleWindBias("left", "rain").toFixed(3)),
                tools.getParticleWindBias("right", "bubbles"),
                tools.getParticleAreaLayout("center", 50),
                tools.getParticlePresetDensityMultiplier("rain"),
                tools.getParticlePresetDensityMultiplier("flame"),
                tools.getParticleMotionProfile("embers").aspect,
                Number(tools.getParticleRandom(2, 3).toFixed(6)),
                tools.formatParticleNumber(12.340, 2),
                tools.formatParticleNumber(10, 1),
                tools.getParticleAnchorPercent("right"),
                tools.getParticleAnchorPercent("bad"),
                tools.getParticleCameraAnchorPercent({{ cameraPan: {{ target: "right" }}, cameraZoom: {{ focus: "left" }} }}),
                tools.getParticleCameraAnchorPercent({{ cameraPan: {{ target: "center" }}, cameraZoom: {{ focus: "left" }} }}),
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
        self.assertIn("getParticlePresetLabel", payload["keys"])
        self.assertIn("mixParticleColors", payload["keys"])
        self.assertEqual(
            payload["labels"],
            [
                "关闭当前粒子特效",
                "法阵符纹",
                "中等",
                "快一点",
                "向左吹",
                "中间区域",
                "线性发光",
                "爆发式发射",
                "圆形发射器",
                "跟随当前说话角色",
                "脚边 / 地面",
                "中段放大",
                "先亮后淡",
                "光谱漂移",
                "环绕中心",
                "魔法阵叠层",
            ],
        )
        self.assertEqual(
            payload["safeValues"],
            [
                "start",
                "snow",
                "heavy",
                "medium",
                "still",
                "full",
                "screen",
                "continuous",
                "line",
                "none",
                "torso",
                "steady",
                "fade",
                "steady",
                "none",
                "none",
            ],
        )
        self.assertEqual(
            payload["metrics"],
            [
                "plus-lighter",
                "normal",
                "warm_shift",
                "cool_shift",
                1,
                3,
                70,
                70,
                0,
                4,
                "#abcdef",
                "#00aaff",
                "bad",
                "#808080",
                "#bf0040",
                "#ffffff",
                "梦境_粒子",
                "spark_fx_02",
            ],
        )
        self.assertEqual(payload["constants"], [6, 24, True, "魔法阵环"])
        self.assertEqual(
            payload["configs"],
            [40, 40, -8, "blizzard_stack", None, 0, "snow", 0, "warm_shift", "snow"],
        )
        self.assertEqual(
            payload["particleMath"],
            [1.28, 1, -22.1, 13, {"start": 36.5, "width": 27}, 1.15, None, "ember", 0.903288, "12.34", "10", 76, 50, 76, 24],
        )


if __name__ == "__main__":
    unittest.main()
