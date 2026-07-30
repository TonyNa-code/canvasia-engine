from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_particle_quality.js"


class FrontendRuntimeParticleQualityModuleTests(unittest.TestCase):
    def test_runtime_budget_adapts_to_device_and_sustained_frame_pressure(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};
            const layers = Array.from({{ length: 4 }}, () => ({{
              preset: "snow",
              intensity: "heavy",
              area: "full",
              density: 180,
            }}));
            const standard = tools.buildParticleRenderPlan(layers, {{ performanceProfile: "standard" }});
            const mobile = tools.buildParticleRenderPlan(layers, {{ performanceProfile: "mobile_low" }});
            const controller = tools.createAdaptiveParticleQualityController({{
              performanceProfile: "standard",
              capabilities: {{ hardwareConcurrency: 8, deviceMemory: 8, reducedMotion: false }},
            }});
            const initial = controller.getSnapshot();
            for (let index = 0; index < 55; index += 1) controller.observeFrame(40);
            const pressured = controller.getSnapshot();
            for (let index = 0; index < 280; index += 1) controller.observeFrame(10);
            const recovered = controller.getSnapshot();
            const constrained = tools.createAdaptiveParticleQualityController({{
              performanceProfile: "standard",
              capabilities: {{ hardwareConcurrency: 2, deviceMemory: 2, reducedMotion: true }},
            }}).getSnapshot();
            const accessibleHighQualityScale = tools.getParticleDeviceScale(
              {{ hardwareConcurrency: 12, deviceMemory: 16, reducedMotion: true }},
              "high_quality_pc"
            );
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              standard,
              mobile,
              initial,
              pressured,
              recovered,
              constrained,
              accessibleHighQualityScale,
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
        self.assertIn("createAdaptiveParticleQualityController", payload["keys"])
        self.assertEqual(payload["standard"]["renderedTotal"], 260)
        self.assertEqual(payload["mobile"]["renderedTotal"], 84)
        self.assertEqual(payload["initial"]["qualityLevel"], "full")
        self.assertEqual(payload["pressured"]["qualityLevel"], "balanced")
        self.assertEqual(payload["recovered"]["qualityLevel"], "full")
        self.assertEqual(payload["constrained"]["qualityLevel"], "recovery")
        self.assertLess(payload["constrained"]["deviceScale"], 0.6)
        self.assertEqual(payload["accessibleHighQualityScale"], 0.72)


if __name__ == "__main__":
    unittest.main()
