from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "prototype_editor" / "modules" / "particle_performance.js"


class FrontendParticlePerformanceModuleTests(unittest.TestCase):
    def test_editor_particle_budget_limits_full_combinations_fairly(self) -> None:
        script = textwrap.dedent(
            f"""
            const fs = require("fs");
            const vm = require("vm");
            const context = {{ window: {{}} }};
            context.globalThis = context;
            vm.createContext(context);
            vm.runInContext(fs.readFileSync({json.dumps(str(MODULE_PATH))}, "utf8"), context);
            const tools = context.window.CanvasiaEditorParticlePerformance;
            const layers = Array.from({{ length: 5 }}, (_, index) => ({{
              preset: index % 2 ? "rain" : "snow",
              intensity: "heavy",
              area: "full",
              density: 160,
            }}));
            const standard = tools.buildParticleRenderPlan(layers, {{ performanceProfile: "standard" }});
            const mobile = tools.buildParticleRenderPlan(layers, {{ performanceProfile: "mobile_low" }});
            const report = tools.buildParticlePerformanceReport({{ density: 160 }}, {{
              performanceProfile: "web",
              normalizeParticleEffectConfig: (value) => value,
              buildParticleComboVariants: (value) => [{{ ...value, __comboIndex: 0 }}],
              buildParticleLayerVariants: (value) => layers.map((layer, index) => ({{ ...layer, __layerIndex: index }})),
            }});
            const card = tools.renderParticlePerformanceCard(report);
            process.stdout.write(JSON.stringify({{
              keys: Object.keys(tools).sort(),
              standard,
              mobile,
              report,
              card,
              frozen: Object.isFrozen(tools),
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
        self.assertTrue(payload["frozen"])
        self.assertIn("buildParticlePerformanceReport", payload["keys"])
        self.assertEqual(payload["standard"]["renderedTotal"], 260)
        self.assertEqual(payload["mobile"]["renderedTotal"], 84)
        self.assertTrue(payload["standard"]["wasLimited"])
        self.assertTrue(all(entry["count"] > 0 for entry in payload["standard"]["entries"]))
        self.assertLessEqual(
            max(entry["count"] for entry in payload["standard"]["entries"])
            - min(entry["count"] for entry in payload["standard"]["entries"]),
            1,
        )
        self.assertEqual(payload["report"]["performanceProfile"], "web")
        self.assertIn("实时性能预算", payload["card"])
        self.assertIn("particle-performance-meter", payload["card"])


if __name__ == "__main__":
    unittest.main()
