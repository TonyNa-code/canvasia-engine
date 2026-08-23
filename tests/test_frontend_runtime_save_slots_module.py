from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_save_slots.js"


class FrontendRuntimeSaveSlotsModuleTests(unittest.TestCase):
    def test_protection_is_backward_compatible_and_blocks_mutation(self) -> None:
        script = textwrap.dedent(
            f"""
            import * as tools from {json.dumps(MODULE_PATH.as_uri())};

            const oldSlot = {{ savedAt: "2026-08-23", session: {{ position: 3 }}, thumbnailDataUrl: "data:image/png;base64,a" }};
            const slots = [oldSlot, null];
            const oldMetadata = tools.sanitizeFormalSaveSlotMetadata(oldSlot);
            const protectedState = tools.toggleFormalSaveSlotProtection(slots, 0);
            const serialized = tools.serializeFormalSaveSlot(slots[0], (session) => JSON.parse(JSON.stringify(session)));
            serialized.session.position = 99;
            const copy = tools.getFormalSaveProtectionCopy(slots[0], false);
            const unprotectedState = tools.setFormalSaveSlotProtection(slots, 0, false);

            process.stdout.write(JSON.stringify({{
              exportedKeys: Object.keys(tools).sort(),
              oldMetadata,
              oldCanMutate: tools.canMutateFormalSaveSlot(oldSlot),
              protectedState,
              protectedCanMutate: tools.canMutateFormalSaveSlot({{ protected: true }}),
              serialized,
              originalPosition: slots[0].session.position,
              copy,
              unprotectedState,
              invalidToggle: tools.toggleFormalSaveSlotProtection(slots, 8),
              emptyToggle: tools.toggleFormalSaveSlotProtection(slots, 1),
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
        self.assertIn("toggleFormalSaveSlotProtection", payload["exportedKeys"])
        self.assertEqual(payload["oldMetadata"], {"protected": False})
        self.assertTrue(payload["oldCanMutate"])
        self.assertTrue(payload["protectedState"])
        self.assertFalse(payload["protectedCanMutate"])
        self.assertTrue(payload["serialized"]["protected"])
        self.assertEqual(payload["originalPosition"], 3)
        self.assertFalse(payload["copy"]["protected"])
        self.assertFalse(payload["unprotectedState"])
        self.assertIsNone(payload["invalidToggle"])
        self.assertIsNone(payload["emptyToggle"])

    def test_player_routes_all_formal_slot_mutations_through_protection_guards(self) -> None:
        player = (ROOT_DIR / "export_player_template" / "player.js").read_text(encoding="utf-8")
        registry = (ROOT_DIR / "export_runtime_module_registry.py").read_text(encoding="utf-8")

        self.assertIn('from "./runtime_save_slots.js"', player)
        self.assertGreaterEqual(player.count("canMutateFormalSaveSlot("), 4)
        self.assertIn("data-toggle-save-protection", player)
        self.assertIn('("SaveSlots", "runtime_save_slots.js")', registry)


if __name__ == "__main__":
    unittest.main()
