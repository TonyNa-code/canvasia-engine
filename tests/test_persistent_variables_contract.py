from __future__ import annotations

import json
import subprocess
import textwrap
import unittest
from pathlib import Path

from native_runtime.runtime_persistent_variables import (
    build_persistent_runtime_variable_store,
    get_persistent_runtime_variable_summary,
    merge_persistent_runtime_variable_state,
    sanitize_persistent_runtime_variable_state,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_MODULE_PATH = ROOT_DIR / "export_player_template" / "runtime_persistent_variables.js"


VARIABLES = [
    {"id": "chapter_score", "type": "number", "scope": "save", "defaultValue": 0},
    {
        "id": "route_clear_count",
        "type": "number",
        "scope": "persistent",
        "defaultValue": 0,
        "min": 0,
        "max": 9,
    },
    {"id": "second_loop", "type": "boolean", "scope": "persistent", "defaultValue": False},
    {"id": "last_ending", "type": " String ", "scope": " PERSISTENT ", "defaultValue": "none"},
]


def run_frontend_contract() -> dict:
    script = textwrap.dedent(
        f"""
        import * as tools from {json.dumps(FRONTEND_MODULE_PATH.as_uri())};
        const variables = {json.dumps(VARIABLES, ensure_ascii=False)};
        const stored = {{ formatVersion: 1, values: {{
          route_clear_count: 99,
          second_loop: "true",
          last_ending: 7,
          removed_variable: "ignored",
        }} }};
        const sanitized = tools.sanitizePersistentRuntimeVariableState(stored, variables);
        const merged = tools.mergePersistentRuntimeVariableState(
          {{ chapter_score: 18, route_clear_count: 1, second_loop: false, last_ending: "old" }},
          variables,
          sanitized
        );
        const summary = tools.getPersistentRuntimeVariableSummary(merged, variables);
        const store = tools.buildPersistentRuntimeVariableStore(merged, variables, {{
          now: () => "2026-07-26T12:00:00+08:00",
        }});
        process.stdout.write(JSON.stringify({{
          scopes: variables.map((variable) => tools.getSafeRuntimeVariableScope(variable.scope)),
          persistentIds: tools.getPersistentRuntimeVariables(variables).map((variable) => variable.id),
          sanitized,
          merged,
          summary,
          store,
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
    if completed.returncode != 0:
        raise AssertionError(completed.stderr)
    return json.loads(completed.stdout)


class PersistentVariablesContractTests(unittest.TestCase):
    def test_web_and_native_helpers_share_the_same_semantics(self) -> None:
        frontend = run_frontend_contract()
        stored = {
            "formatVersion": 1,
            "values": {
                "route_clear_count": 99,
                "second_loop": "true",
                "last_ending": 7,
                "removed_variable": "ignored",
            },
        }
        sanitized = sanitize_persistent_runtime_variable_state(stored, VARIABLES)
        merged = merge_persistent_runtime_variable_state(
            {
                "chapter_score": 18,
                "route_clear_count": 1,
                "second_loop": False,
                "last_ending": "old",
            },
            VARIABLES,
            sanitized,
        )
        summary = get_persistent_runtime_variable_summary(merged, VARIABLES)
        store = build_persistent_runtime_variable_store(
            merged,
            VARIABLES,
            updated_at="2026-07-26T12:00:00+08:00",
        )

        self.assertEqual(frontend["scopes"], ["save", "persistent", "persistent", "persistent"])
        self.assertEqual(
            frontend["persistentIds"],
            ["route_clear_count", "second_loop", "last_ending"],
        )
        self.assertEqual(frontend["sanitized"], sanitized)
        self.assertEqual(frontend["merged"], merged)
        self.assertEqual(frontend["summary"], summary)
        self.assertEqual(frontend["store"], store)
        self.assertEqual(merged["chapter_score"], 18)
        self.assertEqual(merged["route_clear_count"], 9)
        self.assertTrue(merged["second_loop"])
        self.assertEqual(merged["last_ending"], "7")
        self.assertNotIn("removed_variable", merged)
        self.assertEqual(summary["count"], 3)
        self.assertEqual(summary["changedCount"], 3)

    def test_missing_persistent_store_uses_creator_defaults(self) -> None:
        sanitized = sanitize_persistent_runtime_variable_state(None, VARIABLES)

        self.assertEqual(
            sanitized,
            {
                "route_clear_count": 0,
                "second_loop": False,
                "last_ending": "none",
            },
        )


if __name__ == "__main__":
    unittest.main()
