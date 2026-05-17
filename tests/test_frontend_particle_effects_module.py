from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "particle_effects.js"


def particlePresetLibrary_expected() -> list[dict]:
    combo_layers = [
        {"enabled": True, "preset": "flame", "densityMultiplier": 1.5, "blend": "add"},
        {"enabled": False, "preset": "dust", "densityMultiplier": 2, "blend": "normal"},
        {"enabled": True, "preset": "smoke", "densityMultiplier": 0.25, "blend": "normal"},
    ]
    return [
        {
            "id": "dream_fx",
            "name": "梦境光",
            "config": {
                "preset": "glyphs",
                "comboPreset": "arcane_stack",
                "customComboLayers": combo_layers,
            },
        },
        {
            "id": "snow_soft",
            "name": "柔雪",
            "config": {"preset": "snow", "comboPreset": "blizzard_stack"},
        },
        {
            "id": "broken",
            "name": "坏预设",
            "config": {"preset": "bad", "comboPreset": "bad"},
        },
    ]


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
            const comboTestLayers = [
              {{ enabled: true, preset: "flame", densityMultiplier: 1.5, blend: "add" }},
              {{ enabled: false, preset: "dust", densityMultiplier: 2, blend: "normal" }},
              {{ enabled: true, preset: "smoke", densityMultiplier: 0.25, blend: "normal" }},
            ];
            const particlePresetLibrary = [
              {{
                id: "dream_fx",
                name: "梦境光",
                config: {{
                  preset: "glyphs",
                  comboPreset: "arcane_stack",
                  customComboLayers: comboTestLayers,
                }},
              }},
              {{
                id: "snow_soft",
                name: "柔雪",
                config: {{ preset: "snow", comboPreset: "blizzard_stack" }},
              }},
              {{
                id: "broken",
                name: "坏预设",
                config: {{ preset: "bad", comboPreset: "bad" }},
              }},
            ];
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
              profileMath: [
                tools.getParticleCurveProfile({{ sizeCurve: "pulse", opacityCurve: "blink", forceField: "orbit" }}).size.mid,
                tools.getParticleCurveProfile({{ sizeCurve: "pulse", opacityCurve: "blink", forceField: "orbit" }}).opacity.mid,
                tools.getParticleCurveProfile({{ sizeCurve: "pulse", opacityCurve: "blink", forceField: "orbit" }}).force.orbit,
                tools.getParticleCurveProfile({{ sizeCurve: "bad", opacityCurve: "bad", forceField: "bad" }}).size.start,
                tools.getParticleCurveProfile({{ sizeCurve: "bad", opacityCurve: "bad", forceField: "bad" }}).opacity.end,
                tools.getParticleCurveProfile({{ sizeCurve: "bad", opacityCurve: "bad", forceField: "bad" }}).force.x,
                tools.getParticleColorCurveProfile({{ colorCurve: "spectral" }}).hue.end,
                tools.getParticleColorCurveProfile({{ colorCurve: "bad" }}).hue.start,
              ],
              emitterAnchors: [
                tools.getParticleEmitterAnchor({{ area: "center", emitterX: 80, emitterY: 140, emitterZ: 130 }}),
                tools.getParticleEmitterAnchor(
                  {{ follow: "character", followAnchor: "feet", emitterZ: 0 }},
                  {{ activeCharacterId: "hero", visibleCharacters: [{{ characterId: "hero", position: "right" }}] }}
                ),
                tools.getParticleEmitterAnchor(
                  {{ follow: "camera", followAnchor: "head", emitterZ: 0 }},
                  {{ cameraPan: {{ target: "left" }}, cameraZoom: {{ focus: "right" }} }}
                ),
              ],
              layerVariants: tools
                .buildParticleLayerVariants({{
                  preset: "snow",
                  layerCount: 3,
                  density: 90,
                  sizeMin: 10,
                  sizeMax: 20,
                  opacityMin: 0.2,
                  opacityMax: 0.8,
                  spreadZ: 30,
                  gravityZ: 0,
                  emitterZ: 0,
                  color: "#000000",
                  colorAccent: "#ffffff",
                  colorEnd: "#ff0000",
                }})
                .map((layer) => ({{
                  index: layer.__layerIndex,
                  density: layer.density,
                  sizeMin: Number(layer.sizeMin.toFixed(2)),
                  opacityMax: Number(layer.opacityMax.toFixed(2)),
                  spreadZ: layer.spreadZ,
                }})),
              customCombo: {{
                defaultLayer: tools.buildDefaultParticleCustomComboLayer("flame"),
                normalizedBad: tools.normalizeParticleCustomComboLayer(
                  {{
                    enabled: true,
                    preset: "bad",
                    densityMultiplier: "9",
                    sizeScale: 0,
                    lifeScale: "2.5",
                    opacityScale: "bad",
                    colorMix: "1.4",
                    blend: "bad",
                  }},
                  "smoke"
                ),
                normalizedLimit: tools.normalizeParticleCustomComboLayers([
                  ...comboTestLayers,
                  ...comboTestLayers,
                  ...comboTestLayers,
                ]).length,
                enabledCount: tools.getEnabledParticleCustomComboLayers(comboTestLayers).length,
                summary: tools.getParticleCustomComboLayerSummary(comboTestLayers),
              }},
              customLayerMarkup: tools.renderParticleCustomLayerEditor(1, {{
                enabled: true,
                preset: "flame",
                emissionMode: "burst",
                follow: "character",
                followAnchor: "feet",
                densityMultiplier: 1.5,
                sizeScale: 1.25,
                lifeScale: 0.75,
                opacityScale: 0.6,
                colorMix: 0.35,
                blend: "add",
              }}),
              customPresetQuickListMarkup: tools.renderParticleCustomPresetQuickList(
                particlePresetLibrary.slice(0, 2),
                {{
                  selectedPresetId: "dream_fx",
                  normalizeParticleEffectConfig: (config) => ({{
                    comboPreset: config.comboPreset || "none",
                    customComboLayers: config.customComboLayers || [],
                  }}),
                }}
              ),
              emptyCustomPresetQuickListMarkup: tools.renderParticleCustomPresetQuickList([]),
              imageAssetOptionsMarkup: tools.renderParticleImageAssetOptions(
                [
                  {{ id: "bg_1", name: "背景 <雨天>", type: "background" }},
                  {{ id: "spark_png", name: "自定义火花图", type: "ui" }},
                ],
                "spark_png",
                {{ getAssetTypeLabel: (type) => ({{ background: "背景", ui: "UI 图层" }}[type] || type) }}
              ),
              particleEditorMarkup: tools.renderParticleEffectEditor(
                {{
                  action: "start",
                  preset: "flame",
                  intensity: "heavy",
                  speed: "fast",
                  wind: "right",
                  area: "center",
                  assetId: "spark_png",
                  density: 88,
                  customComboLayers: comboTestLayers,
                  comboPreset: "arcane_stack",
                  emitterShape: "circle",
                  follow: "character",
                  followAnchor: "feet",
                  layerCount: 3,
                  emitterX: 44,
                  emitterY: 77,
                  emitterZ: 8,
                  attractionX: 10,
                  attractionY: -20,
                  vortex: 33,
                  forceField: "orbit",
                  fieldX: 55,
                  fieldY: 66,
                  sizeMin: 4,
                  sizeMax: 16,
                  lifeMin: 1.5,
                  lifeMax: 4.5,
                  opacityMin: 0.3,
                  opacityMax: 0.9,
                  sizeCurve: "pulse",
                  opacityCurve: "blink",
                  colorCurve: "spectral",
                  gravityX: 0,
                  gravityY: 30,
                  gravityZ: -5,
                  spreadX: 40,
                  spreadY: 20,
                  spreadZ: 10,
                  turbulence: 12,
                  rotationMin: -15,
                  rotationMax: 45,
                  spin: 30,
                  color: "#111111",
                  colorAccent: "#eeeeee",
                  colorEnd: "#ff8844",
                  blend: "add",
                }},
                {{
                  savedParticlePresets: particlePresetLibrary.slice(0, 2),
                  selectedParticleCustomPresetId: "snow_soft",
                  particlePresetSearchQuery: "魔法",
                  filteredParticleCustomPresetCount: 1,
                  customPresetLimit: 24,
                  particleImageAssets: [{{ id: "spark_png", name: "自定义火花图", type: "ui" }}],
                  getAssetTypeLabel: (type) => ({{ ui: "UI 图层" }}[type] || type),
                  normalizeParticleEffectConfig: (config) => config,
                  renderParticleCustomPresetQuickList: () => `<div data-quick-list>quick preset list</div>`,
                  renderParticleCustomLayerEditor: (index, layer) => `<section data-rendered-layer="${{index}}:${{layer.preset}}"></section>`,
                }}
              ),
              comboVariants: {{
                none: tools
                  .buildParticleComboVariants({{ preset: "snow", comboPreset: "none", density: 12 }})
                  .map((variant) => ({{
                    index: variant.__comboIndex,
                    preset: variant.preset,
                    density: variant.density,
                    comboPreset: variant.comboPreset,
                  }})),
                arcane: tools
                  .buildParticleComboVariants({{
                    preset: "glyphs",
                    comboPreset: "arcane_stack",
                    density: 18,
                    color: "#000000",
                    colorAccent: "#ffffff",
                    colorEnd: "#ff0000",
                  }})
                  .map((variant) => ({{
                    index: variant.__comboIndex,
                    preset: variant.preset,
                    density: variant.density,
                    follow: variant.follow,
                    followAnchor: variant.followAnchor,
                    comboPreset: variant.comboPreset,
                    color: variant.color,
                    colorAccent: variant.colorAccent,
                    blend: variant.blend,
                    layerCount: variant.layerCount,
                  }})),
                custom: tools
                  .buildParticleComboVariants({{
                    preset: "snow",
                    comboPreset: "none",
                    customComboLayers: comboTestLayers,
                    density: 20,
                    color: "#000000",
                    colorAccent: "#ffffff",
                    colorEnd: "#ff0000",
                  }})
                  .map((variant) => ({{
                    index: variant.__comboIndex,
                    preset: variant.preset,
                    density: variant.density,
                    blend: variant.blend,
                    comboPreset: variant.comboPreset,
                    color: variant.color,
                    colorAccent: variant.colorAccent,
                  }})),
              }},
              presetLibrary: {{
                primary: [
                  tools.getParticleCustomPresetPrimaryPreset({{ preset: "glyphs" }}),
                  tools.getParticleCustomPresetPrimaryPreset({{ preset: "bad" }}),
                  tools.getParticleCustomPresetPrimaryPreset(null),
                ],
                tokens: tools.getParticleCustomPresetSearchTokens(particlePresetLibrary[0]),
                filteredMagic: tools
                  .getFilteredParticleCustomPresets(particlePresetLibrary, "魔法阵")
                  .map((preset) => preset.id),
                filteredLayer: tools
                  .getFilteredParticleCustomPresets(particlePresetLibrary, "l3:烟雾")
                  .map((preset) => preset.id),
                filteredBlank: tools
                  .getFilteredParticleCustomPresets(particlePresetLibrary, "  ")
                  .map((preset) => preset.id),
                filteredBadInput: tools.getFilteredParticleCustomPresets(null, "anything"),
                groups: tools
                  .groupParticleCustomPresets(particlePresetLibrary)
                  .map(([key, items]) => [key, items.map((item) => item.id)]),
                groupsBadInput: tools.groupParticleCustomPresets(null),
              }},
              presetPersistence: {{
                byId: [
                  tools.getParticleCustomPresetById(particlePresetLibrary, " snow_soft ")?.name,
                  tools.getParticleCustomPresetById(particlePresetLibrary, "none"),
                ],
                saveNew: (() => {{
                  const plan = tools.buildParticleCustomPresetSavePlan({{
                    name: " 新预设 ",
                    currentConfig: {{ preset: "flame" }},
                    currentPresets: particlePresetLibrary.slice(0, 2),
                  }});
                  return {{
                    ok: plan.ok,
                    isUpdate: plan.isUpdate,
                    targetId: plan.targetId,
                    names: plan.nextPresets.map((preset) => preset.name),
                    ids: plan.nextPresets.map((preset) => preset.id),
                  }};
                }})(),
                saveUpdate: (() => {{
                  const plan = tools.buildParticleCustomPresetSavePlan({{
                    name: "改名柔雪",
                    currentConfig: {{ preset: "rain" }},
                    currentPresets: particlePresetLibrary.slice(0, 2),
                    selectedPresetId: "snow_soft",
                  }});
                  return {{
                    ok: plan.ok,
                    isUpdate: plan.isUpdate,
                    targetId: plan.targetId,
                    names: plan.nextPresets.map((preset) => preset.name),
                    presets: plan.nextPresets.map((preset) => preset.config.preset),
                  }};
                }})(),
                saveErrors: [
                  tools.buildParticleCustomPresetSavePlan({{ name: "   " }}).reason,
                  tools.buildParticleCustomPresetSavePlan({{
                    name: "满了",
                    currentConfig: {{ preset: "rain" }},
                    currentPresets: particlePresetLibrary.slice(0, 2),
                    limit: 2,
                  }}).reason,
                  tools.buildParticleCustomPresetSavePlan({{
                    name: "满了",
                    currentConfig: {{ preset: "rain" }},
                    currentPresets: particlePresetLibrary.slice(0, 2),
                    limit: 2,
                  }}).limit,
                ],
                exportOne: tools.buildParticleCustomPresetExportPayload(
                  particlePresetLibrary[0],
                  "2026-01-02T00:00:00.000Z"
                ),
                exportPack: tools.buildParticleCustomPresetPackExportPayload(
                  particlePresetLibrary.slice(0, 2),
                  "测试项目",
                  "2026-01-03T00:00:00.000Z"
                ),
                extract: [
                  tools.extractParticleCustomPresetsFromImportPayload([1, 2]).length,
                  tools.extractParticleCustomPresetsFromImportPayload({{ presets: [1] }}).length,
                  tools.extractParticleCustomPresetsFromImportPayload({{ preset: {{ id: "solo" }} }})[0].id,
                  tools.extractParticleCustomPresetsFromImportPayload({{}}).length,
                ],
                importPlan: (() => {{
                  const plan = tools.buildParticleCustomPresetImportPlan(
                    {{
                      presets: [
                        {{ id: "dream_fx", name: "重复梦境", config: {{ preset: "flame", density: 22 }} }},
                        {{ name: "", config: {{ preset: "rain" }} }},
                        {{ id: "stars", name: "星尘", config: {{ preset: "stardust" }} }},
                      ],
                    }},
                    particlePresetLibrary.slice(0, 2),
                    {{ limit: 4 }}
                  );
                  return {{
                    rawCount: plan.rawCount,
                    importedCount: plan.importedCount,
                    skippedCount: plan.skippedCount,
                    selectedPresetId: plan.selectedPresetId,
                    summary: plan.summary,
                    ids: plan.mergedPresets.map((preset) => preset.id),
                    names: plan.mergedPresets.map((preset) => preset.name),
                    presets: plan.mergedPresets.map((preset) => preset.config.preset),
                  }};
                }})(),
              }},
              particleDescription: {{
                off: tools.describeParticleEffect(null),
                active: tools.describeParticleEffect(
                  {{
                    action: "start",
                    preset: "glyphs",
                    assetId: "snowflake",
                    intensity: "heavy",
                    speed: "fast",
                    wind: "left",
                    area: "center",
                    emissionMode: "burst",
                    emitterShape: "circle",
                    emitterX: 44,
                    emitterY: 77,
                    emitterZ: 8,
                    attractionX: 10,
                    attractionY: -20,
                    vortex: 33,
                    follow: "character",
                    followAnchor: "feet",
                    comboPreset: "arcane_stack",
                    customComboLayers: comboTestLayers,
                    layerCount: 2,
                    sizeCurve: "pulse",
                    opacityCurve: "blink",
                    colorCurve: "spectral",
                    forceField: "orbit",
                    fieldX: 55,
                    fieldY: 66,
                    density: 18,
                    sizeMin: 4,
                    sizeMax: 16,
                    lifeMin: 1.5,
                    lifeMax: 4.5,
                    gravityX: 0,
                    gravityY: 30,
                    gravityZ: -5,
                    spreadX: 40,
                    spreadY: 20,
                    spreadZ: 10,
                    opacityMin: 0.3,
                    opacityMax: 0.9,
                    rotationMin: -15,
                    rotationMax: 45,
                    spin: 30,
                    turbulence: 12,
                    color: "#000000",
                    colorAccent: "#ffffff",
                    colorEnd: "#ff0000",
                    blend: "add",
                  }},
                  {{ getImageName: (assetId) => `Asset:${{assetId}}` }}
                ),
                rows: tools.buildParticleEffectDetailRows(
                  {{
                    action: "start",
                    preset: "glyphs",
                    assetId: "snowflake",
                    intensity: "heavy",
                    speed: "fast",
                    wind: "left",
                    area: "center",
                    emissionMode: "burst",
                    emitterShape: "circle",
                    emitterX: 44,
                    emitterY: 77,
                    emitterZ: 8,
                    attractionX: 10,
                    attractionY: -20,
                    vortex: 33,
                    follow: "character",
                    followAnchor: "feet",
                    comboPreset: "arcane_stack",
                    customComboLayers: comboTestLayers,
                    layerCount: 2,
                    sizeCurve: "pulse",
                    opacityCurve: "blink",
                    colorCurve: "spectral",
                    forceField: "orbit",
                    fieldX: 55,
                    fieldY: 66,
                    density: 18,
                    sizeMin: 4,
                    sizeMax: 16,
                    lifeMin: 1.5,
                    lifeMax: 4.5,
                    gravityX: 0,
                    gravityY: 30,
                    gravityZ: -5,
                    spreadX: 40,
                    spreadY: 20,
                    spreadZ: 10,
                    opacityMin: 0.3,
                    opacityMax: 0.9,
                    rotationMin: -15,
                    rotationMax: 45,
                    spin: 30,
                    turbulence: 12,
                    color: "#000000",
                    colorAccent: "#ffffff",
                    colorEnd: "#ff0000",
                    blend: "add",
                  }},
                  {{ getImageName: (assetId) => `Asset:${{assetId}}` }}
                ),
                stopRows: tools.buildParticleEffectDetailRows({{ action: "stop" }}),
              }},
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
        self.assertIn("buildParticleLayerVariants", payload["keys"])
        self.assertIn("buildParticleComboVariants", payload["keys"])
        self.assertIn("getParticleCustomComboLayerSummary", payload["keys"])
        self.assertIn("getFilteredParticleCustomPresets", payload["keys"])
        self.assertIn("groupParticleCustomPresets", payload["keys"])
        self.assertIn("describeParticleEffect", payload["keys"])
        self.assertIn("buildParticleEffectDetailRows", payload["keys"])
        self.assertIn("buildParticleCustomPresetImportPlan", payload["keys"])
        self.assertIn("buildParticleCustomPresetSavePlan", payload["keys"])
        self.assertIn("getParticleEmitterAnchor", payload["keys"])
        self.assertIn("getParticleCurveProfile", payload["keys"])
        self.assertIn("renderParticleCustomLayerEditor", payload["keys"])
        self.assertIn("renderParticleCustomPresetQuickList", payload["keys"])
        self.assertIn("renderParticleEffectEditor", payload["keys"])
        self.assertIn("renderParticleImageAssetOptions", payload["keys"])
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
        self.assertEqual(payload["profileMath"], [1.28, 1, 0.78, 1, 0.12, 0, 54, 0])
        self.assertEqual(
            payload["emitterAnchors"],
            [
                {"x": 77, "y": 120, "z": 100},
                {"x": 76, "y": 82, "z": 8},
                {"x": 24, "y": 30, "z": 0},
            ],
        )
        self.assertEqual(
            payload["layerVariants"],
            [
                {"index": 0, "density": 22, "sizeMin": 7.8, "opacityMax": 0.58, "spreadZ": 30},
                {"index": 1, "density": 35, "sizeMin": 10.1, "opacityMax": 0.7, "spreadZ": 42},
                {"index": 2, "density": 22, "sizeMin": 12.4, "opacityMax": 0.83, "spreadZ": 54},
            ],
        )
        self.assertEqual(
            payload["customCombo"],
            {
                "defaultLayer": {
                    "enabled": False,
                    "preset": "flame",
                    "emissionMode": "continuous",
                    "follow": "none",
                    "followAnchor": "torso",
                    "densityMultiplier": 1,
                    "sizeScale": 1,
                    "lifeScale": 1,
                    "opacityScale": 1,
                    "colorMix": 0.42,
                    "blend": "add",
                },
                "normalizedBad": {
                    "enabled": True,
                    "preset": "snow",
                    "emissionMode": "continuous",
                    "follow": "none",
                    "followAnchor": "torso",
                    "densityMultiplier": 4,
                    "sizeScale": 0.2,
                    "lifeScale": 2.5,
                    "opacityScale": 1,
                    "colorMix": 1,
                    "blend": "screen",
                },
                "normalizedLimit": 6,
                "enabledCount": 2,
                "summary": "L2:火焰 / ×1.5 / 线性发光 · L3:烟雾 / ×0.3 / 正常叠加",
            },
        )
        self.assertIn("自定义叠层 2", payload["customLayerMarkup"])
        self.assertIn('data-layer-index="1"', payload["customLayerMarkup"])
        self.assertIn('id="editorParticleCustomLayer2Preset"', payload["customLayerMarkup"])
        self.assertIn('value="flame" selected', payload["customLayerMarkup"])
        self.assertIn('value="burst" selected', payload["customLayerMarkup"])
        self.assertIn('value="character" selected', payload["customLayerMarkup"])
        self.assertIn('value="feet" selected', payload["customLayerMarkup"])
        self.assertIn('id="editorParticleCustomLayer2DensityMultiplier"', payload["customLayerMarkup"])
        self.assertIn('value="1.5"', payload["customLayerMarkup"])
        self.assertIn('id="editorParticleCustomLayer2ColorMix"', payload["customLayerMarkup"])
        self.assertIn('value="0.35"', payload["customLayerMarkup"])
        self.assertIn('value="add" selected', payload["customLayerMarkup"])
        self.assertIn("particle-preset-group-title", payload["customPresetQuickListMarkup"])
        self.assertIn("法阵符纹", payload["customPresetQuickListMarkup"])
        self.assertIn("梦境光", payload["customPresetQuickListMarkup"])
        self.assertIn("柔雪", payload["customPresetQuickListMarkup"])
        self.assertIn("is-active", payload["customPresetQuickListMarkup"])
        self.assertIn('data-preset-id="dream_fx"', payload["customPresetQuickListMarkup"])
        self.assertIn("魔法阵叠层 / L2:火焰 / ×1.5 / 线性发光", payload["customPresetQuickListMarkup"])
        self.assertIn("当前筛选下还没有命中的粒子预设", payload["emptyCustomPresetQuickListMarkup"])
        self.assertIn("背景 &lt;雨天&gt; · 背景", payload["imageAssetOptionsMarkup"])
        self.assertIn("自定义火花图 · UI 图层", payload["imageAssetOptionsMarkup"])
        self.assertIn('value="spark_png" selected', payload["imageAssetOptionsMarkup"])
        self.assertIn("编辑粒子特效", payload["particleEditorMarkup"])
        self.assertIn('id="editorParticleAction"', payload["particleEditorMarkup"])
        self.assertIn('value="start" selected', payload["particleEditorMarkup"])
        self.assertIn('id="editorParticlePreset"', payload["particleEditorMarkup"])
        self.assertIn('value="flame" selected', payload["particleEditorMarkup"])
        self.assertIn('data-action="apply-particle-scene-preset"', payload["particleEditorMarkup"])
        self.assertIn("当前已保存 2 / 24 组", payload["particleEditorMarkup"])
        self.assertIn('id="editorParticleCustomPresetSearch"', payload["particleEditorMarkup"])
        self.assertIn('value="魔法"', payload["particleEditorMarkup"])
        self.assertIn('value="snow_soft" selected', payload["particleEditorMarkup"])
        self.assertIn("搜索结果 1 组", payload["particleEditorMarkup"])
        self.assertIn('data-quick-list', payload["particleEditorMarkup"])
        self.assertIn("自定义火花图", payload["particleEditorMarkup"])
        self.assertIn('id="editorParticleDensity"', payload["particleEditorMarkup"])
        self.assertIn('value="88"', payload["particleEditorMarkup"])
        self.assertIn('data-action="add-particle-custom-layer"', payload["particleEditorMarkup"])
        self.assertIn('data-rendered-layer="0:flame"', payload["particleEditorMarkup"])
        self.assertIn('data-rendered-layer="1:dust"', payload["particleEditorMarkup"])
        self.assertIn('id="editorParticleEmitterShape"', payload["particleEditorMarkup"])
        self.assertIn('value="circle" selected', payload["particleEditorMarkup"])
        self.assertIn('id="editorParticleFollowAnchor"', payload["particleEditorMarkup"])
        self.assertIn('value="feet" selected', payload["particleEditorMarkup"])
        self.assertIn('id="editorParticleForceField"', payload["particleEditorMarkup"])
        self.assertIn('value="orbit" selected', payload["particleEditorMarkup"])
        self.assertIn('id="editorParticleColorEnd"', payload["particleEditorMarkup"])
        self.assertIn('value="#ff8844"', payload["particleEditorMarkup"])
        self.assertIn('data-action="save-block"', payload["particleEditorMarkup"])
        self.assertEqual(
            payload["comboVariants"],
            {
                "none": [
                    {"index": 0, "preset": "snow", "density": 12, "comboPreset": "none"},
                ],
                "arcane": [
                    {
                        "index": 0,
                        "preset": "glyphs",
                        "density": 18,
                        "follow": "character",
                        "followAnchor": "torso",
                        "comboPreset": "arcane_stack",
                        "color": "#000000",
                        "colorAccent": "#ffffff",
                        "blend": "add",
                        "layerCount": 1,
                    },
                    {
                        "index": 1,
                        "preset": "glyphs",
                        "density": 13,
                        "follow": "character",
                        "followAnchor": "feet",
                        "comboPreset": "none",
                        "color": "#456e85",
                        "colorAccent": "#fbf0ff",
                        "blend": "add",
                        "layerCount": 2,
                    },
                    {
                        "index": 2,
                        "preset": "stardust",
                        "density": 16,
                        "follow": "camera",
                        "followAnchor": "torso",
                        "comboPreset": "none",
                        "color": "#44697a",
                        "colorAccent": "#fff9ff",
                        "blend": "screen",
                        "layerCount": 1,
                    },
                    {
                        "index": 3,
                        "preset": "sparkles",
                        "density": 6,
                        "follow": "character",
                        "followAnchor": "torso",
                        "comboPreset": "none",
                        "color": "#748185",
                        "colorAccent": "#cef5ff",
                        "blend": "add",
                        "layerCount": 1,
                    },
                ],
                "custom": [
                    {
                        "index": 0,
                        "preset": "snow",
                        "density": 20,
                        "blend": "screen",
                        "comboPreset": "none",
                        "color": "#000000",
                        "colorAccent": "#ffffff",
                    },
                    {
                        "index": 1,
                        "preset": "flame",
                        "density": 39,
                        "blend": "add",
                        "comboPreset": "none",
                        "color": "#945123",
                        "colorAccent": "#fffad3",
                    },
                    {
                        "index": 2,
                        "preset": "smoke",
                        "density": 6,
                        "blend": "normal",
                        "comboPreset": "none",
                        "color": "#656e7b",
                        "colorAccent": "#f8fbff",
                    },
                ],
            },
        )
        self.assertEqual(
            payload["presetLibrary"],
            {
                "primary": ["glyphs", "snow", "snow"],
                "tokens": "梦境光 dream_fx 法阵符纹 魔法阵叠层 l2:火焰 / ×1.5 / 线性发光 · l3:烟雾 / ×0.3 / 正常叠加",
                "filteredMagic": ["dream_fx"],
                "filteredLayer": ["dream_fx"],
                "filteredBlank": ["dream_fx", "snow_soft", "broken"],
                "filteredBadInput": [],
                "groups": [["glyphs", ["dream_fx"]], ["snow", ["snow_soft", "broken"]]],
                "groupsBadInput": [],
            },
        )
        self.assertEqual(
            payload["presetPersistence"],
            {
                "byId": ["柔雪", None],
                "saveNew": {
                    "ok": True,
                    "isUpdate": False,
                    "targetId": "新预设",
                    "names": ["梦境光", "柔雪", "新预设"],
                    "ids": ["dream_fx", "snow_soft", "新预设"],
                },
                "saveUpdate": {
                    "ok": True,
                    "isUpdate": True,
                    "targetId": "snow_soft",
                    "names": ["梦境光", "改名柔雪"],
                    "presets": ["glyphs", "rain"],
                },
                "saveErrors": ["missing_name", "limit_reached", 2],
                "exportOne": {
                    "engine": "Canvasia Engine",
                    "kind": "particle_preset",
                    "exportedAt": "2026-01-02T00:00:00.000Z",
                    "preset": particlePresetLibrary_expected()[0],
                },
                "exportPack": {
                    "engine": "Canvasia Engine",
                    "kind": "particle_preset_pack",
                    "projectTitle": "测试项目",
                    "exportedAt": "2026-01-03T00:00:00.000Z",
                    "presets": particlePresetLibrary_expected()[:2],
                },
                "extract": [2, 1, "solo", 0],
                "importPlan": {
                    "rawCount": 3,
                    "importedCount": 2,
                    "skippedCount": 1,
                    "selectedPresetId": "导入预设_2",
                    "summary": "已导入粒子预设：新增 2 组，另有 1 组因为项目上限被跳过",
                    "ids": ["dream_fx", "snow_soft", "dream_fx_02", "导入预设_2"],
                    "names": ["梦境光", "柔雪", "重复梦境", "导入预设 2"],
                    "presets": ["glyphs", "snow", "flame", "rain"],
                },
            },
        )
        self.assertEqual(payload["particleDescription"]["off"], "已关闭")
        self.assertEqual(
            payload["particleDescription"]["active"],
            "法阵符纹 · 爆发式发射 · 圆形发射器 · 魔法阵叠层 · L2:火焰 / ×1.5 / 线性发光 · L3:烟雾 / ×0.3 / 正常叠加 · 中段放大 · 光谱漂移 · 2 层 · 18 颗 · 4-16 px · G 0/30/-5 · 线性发光 · Asset:snowflake",
        )
        self.assertEqual(
            payload["particleDescription"]["stopRows"],
            [["执行动作", "关闭当前粒子特效"]],
        )
        self.assertEqual(
            payload["particleDescription"]["rows"],
            [
                ["执行动作", "开始粒子特效"],
                ["粒子类型", "法阵符纹"],
                ["自定义图片", "Asset:snowflake"],
                ["特效强度", "浓一点"],
                ["速度 / 风向", "快一点 / 向左吹"],
                ["出现区域", "中间区域"],
                ["发射模式", "爆发式发射"],
                ["组合方案", "魔法阵叠层"],
                ["自定义叠层", "L2:火焰 / ×1.5 / 线性发光 · L3:烟雾 / ×0.3 / 正常叠加"],
                ["发射器", "圆形发射器 / 跟随当前说话角色 / 脚边 / 地面"],
                ["叠加层数", "2 层"],
                ["时间曲线", "中段放大 / 中段更亮 / 光谱漂移"],
                ["中心力场", "环绕中心 / 中心 55 / 66"],
                ["发射器 XYZ", "44 / 77 / 8"],
                ["吸引 / 旋涡", "X 10 / Y -20 / 涡流 33"],
                ["粒子数量", "18 颗"],
                ["尺寸范围", "4 ~ 16 px"],
                ["寿命范围", "1.5 ~ 4.5 秒"],
                ["重力 XYZ", "0 / 30 / -5"],
                ["疏散 XYZ", "40 / 20 / 10"],
                ["透明度范围", "0.3 ~ 0.9"],
                ["旋转 / 扰动", "-15 ~ 45 deg / 自转 30 deg / 乱流 12"],
                ["颜色", "#000000 → #ffffff → #ff0000"],
                ["混合模式", "线性发光"],
            ],
        )


if __name__ == "__main__":
    unittest.main()
