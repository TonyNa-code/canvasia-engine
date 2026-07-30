from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_particle_renderer.js"


class FrontendRuntimeParticleRendererModuleTests(unittest.TestCase):
    def test_renderer_builds_a_budgeted_layer_without_player_globals(self) -> None:
        script = textwrap.dedent(
            f"""
            import {{ renderRuntimeParticleLayer }} from {json.dumps(MODULE_PATH.as_uri())};
            const normalize = (value) => ({{
              action: "start",
              preset: "snow",
              intensity: "heavy",
              speed: "medium",
              wind: "still",
              area: "full",
              comboPreset: "custom",
              emissionMode: "continuous",
              emitterShape: "box",
              follow: "world",
              blend: "screen",
              layerCount: 2,
              assetId: "snow_texture",
              density: 160,
              lifeMin: 2,
              lifeMax: 4,
              sizeMin: 4,
              sizeMax: 8,
              spreadX: 100,
              spreadY: 30,
              spreadZ: 0,
              fieldX: 50,
              fieldY: 50,
              gravityX: 0,
              gravityY: 20,
              gravityZ: 0,
              attractionX: 0,
              attractionY: 0,
              turbulence: 0,
              vortex: 0,
              opacityMin: 0.6,
              opacityMax: 1,
              rotationMin: 0,
              rotationMax: 0,
              spin: 0,
              color: "#ffffff",
              colorAccent: "#d6eeff",
              colorEnd: "#ffffff",
              ...value,
            }});
            const html = renderRuntimeParticleLayer(normalize({{}}), null, {{
              normalizeParticleEffectConfig: normalize,
              buildParticleComboVariants: (value) => [{{ ...value, __comboIndex: 0 }}],
              buildParticleLayerVariants: (value) => [0, 1].map((index) => ({{ ...value, __layerIndex: index }})),
              performanceProfile: "mobile_low",
              qualityStatus: {{ qualityLevelIndex: 0, adaptiveScale: 1, deviceScale: 1 }},
              getPresetDensityMultiplier: () => 1,
              getParticleMotionProfile: () => ({{ aspect: "glow", startBase: 0, endBase: 100 }}),
              getParticleAreaLayout: () => ({{ start: 0, width: 100 }}),
              getParticleEmitterAnchor: () => ({{ x: 50, y: 0, z: 0 }}),
              getSafeParticleEmitterShape: (value) => value,
              getParticleCurveProfile: () => ({{
                force: {{ x: 0, y: 0, orbit: 0 }},
                opacity: {{ mid: 1, end: 0 }},
                size: {{ start: 1, mid: 1, end: 1 }},
              }}),
              getParticleColorCurveProfile: () => ({{
                hue: {{ start: 0, mid: 0, end: 0 }},
                saturation: {{ start: 1, mid: 1, end: 1 }},
                brightness: {{ start: 1, mid: 1, end: 1 }},
              }}),
              getParticleSpeedMultiplier: () => 1,
              getParticleRandom: () => 0.5,
              getParticleWindBias: () => 0,
              mixParticleColors: (left) => left,
              getParticleBlendCssValue: () => "screen",
              resolveParticleImageUrl: () => "assets/particle/snow.png",
              clamp: (value, minimum, maximum) => Math.min(maximum, Math.max(minimum, value)),
              escapeHtml: (value) => String(value),
            }});
            process.stdout.write(JSON.stringify({{
              empty: renderRuntimeParticleLayer(null, null, {{}}),
              itemCount: (html.match(/class="particle-item/g) ?? []).length,
              hasBudget: html.includes('data-particle-rendered="84"'),
              hasProfile: html.includes('data-particle-performance-profile="mobile_low"'),
              hasImage: html.includes('assets/particle/snow.png'),
            }}));
            """
        )
        completed = subprocess.run(
            ["node", "--input-type=module", "-e", script],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["empty"], "")
        self.assertEqual(payload["itemCount"], 84)
        self.assertTrue(payload["hasBudget"])
        self.assertTrue(payload["hasProfile"])
        self.assertTrue(payload["hasImage"])


if __name__ == "__main__":
    unittest.main()
