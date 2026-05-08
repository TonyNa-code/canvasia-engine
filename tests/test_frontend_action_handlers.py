from __future__ import annotations

import re
import unittest
from collections import Counter
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EDITOR_DIR = ROOT_DIR / "prototype_editor"
INDEX_PATH = EDITOR_DIR / "index.html"
APP_PATH = EDITOR_DIR / "app.js"
MODULE_PATHS = tuple(sorted((EDITOR_DIR / "modules").glob("*.js")))
ACTION_ATTRIBUTE_PATHS = (INDEX_PATH, APP_PATH)
ACTION_CONFIG_PATHS = (APP_PATH, *MODULE_PATHS)

ACTION_ATTRIBUTE_PATTERN = re.compile(
    r"(?<!\[)\bdata-action\s*=\s*([\"'])([^\"'${}]+)\1"
)
ACTION_HANDLER_PATTERN = re.compile(r"\baction\s*===\s*([\"'])([^\"']+)\1")
ACTION_CASE_HANDLER_PATTERN = re.compile(r"\bcase\s+([\"'])([^\"']+)\1\s*:")
ACTION_CONFIG_VALUE_PATTERN = re.compile(r"\baction\s*:\s*([\"'])([^\"']+)\1")

DYNAMIC_DATA_ACTION_MARKERS = Counter(
    {
        'data-action="${project.isSample ? "duplicate-project" : "rename-project"}"': 1,
        'data-action="${actionName}"': 2,
        'data-action="${mode === "save" ? "quick-save-preview" : "quick-load-preview"}"': 1,
        'data-action="${action.action}"': 1,
        'data-action="${escapeHtml(action.action ?? "")}"': 1,
        'data-action="${button.action}"': 1,
        'data-action="${action.action}"${': 1,
        'data-action="${escapeHtml(button.action)}"': 1,
    }
)

NON_CLICK_ACTION_VALUES = {
    "apply",
    "fade_out",
    "start",
    "stop",
    "zoom_in",
}


def _line_number(source: str, offset: int) -> int:
    return source.count("\n", 0, offset) + 1


def _get_handled_actions() -> set[str]:
    app_source = APP_PATH.read_text(encoding="utf-8")
    click_handler = _extract_function_source(app_source, "handleClick")
    handled_actions = {
        match.group(2)
        for match in ACTION_HANDLER_PATTERN.finditer(click_handler)
    }
    handled_actions.update(
        match.group(2)
        for match in ACTION_CASE_HANDLER_PATTERN.finditer(click_handler)
    )
    return handled_actions


def _extract_function_source(source: str, function_name: str) -> str:
    marker_match = re.search(
        rf"(?:async\s+)?function\s+{re.escape(function_name)}\s*\(",
        source,
    )
    if not marker_match:
        raise AssertionError(f"Missing function {function_name}")
    body_start = source.find("{", marker_match.end())
    if body_start < 0:
        raise AssertionError(f"Missing function body for {function_name}")

    depth = 0
    for index in range(body_start, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[body_start : index + 1]
    raise AssertionError(f"Unclosed function body for {function_name}")


class FrontendActionHandlerTests(unittest.TestCase):
    def test_literal_data_actions_have_click_handlers(self) -> None:
        action_locations: dict[str, list[str]] = {}
        for path in ACTION_ATTRIBUTE_PATHS:
            source = path.read_text(encoding="utf-8")
            for match in ACTION_ATTRIBUTE_PATTERN.finditer(source):
                action = match.group(2).strip()
                if not action:
                    continue
                relative_path = path.relative_to(ROOT_DIR).as_posix()
                action_locations.setdefault(action, []).append(
                    f"{relative_path}:{_line_number(source, match.start())}"
                )

        handled_actions = _get_handled_actions()

        missing_actions = {
            action: locations
            for action, locations in sorted(action_locations.items())
            if action not in handled_actions
        }

        self.assertGreaterEqual(len(action_locations), 200)
        self.assertFalse(
            missing_actions,
            "Literal data-action values without handleClick coverage:\n"
            + "\n".join(
                f"- {action}: {', '.join(locations[:4])}"
                for action, locations in missing_actions.items()
            ),
        )

    def test_dynamic_data_action_sites_are_audited(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        dynamic_markers = Counter()
        for line in source.splitlines():
            if 'data-action="${' not in line:
                continue
            marker = line.strip()
            marker = marker[marker.index("data-action=") :]
            if 'data-action="${action.action}"${' in marker:
                marker = 'data-action="${action.action}"${'
            if 'data-action="${escapeHtml(button.action)}"' in marker:
                marker = 'data-action="${escapeHtml(button.action)}"'
            dynamic_markers[marker] += 1

        self.assertEqual(dynamic_markers, DYNAMIC_DATA_ACTION_MARKERS)

    def test_action_config_values_have_click_handlers(self) -> None:
        handled_actions = _get_handled_actions()
        action_locations: dict[str, list[str]] = {}
        for path in ACTION_CONFIG_PATHS:
            source = path.read_text(encoding="utf-8")
            relative_path = path.relative_to(ROOT_DIR).as_posix()
            for match in ACTION_CONFIG_VALUE_PATTERN.finditer(source):
                action = match.group(2)
                if action in NON_CLICK_ACTION_VALUES:
                    continue
                action_locations.setdefault(action, []).append(
                    f"{relative_path}:{_line_number(source, match.start())}"
                )

        missing_actions = {
            action: locations
            for action, locations in sorted(action_locations.items())
            if action not in handled_actions
        }

        self.assertGreaterEqual(len(action_locations), 45)
        self.assertFalse(
            missing_actions,
            "Action config values without handleClick coverage:\n"
            + "\n".join(
                f"- {action}: {', '.join(locations[:4])}"
                for action, locations in missing_actions.items()
            ),
        )

    def test_handle_click_has_runtime_fallback_for_unwired_buttons(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        click_handler = _extract_function_source(source, "handleClick")

        self.assertIn("function handleMissingProjectAction", source)
        self.assertIn("function handleUnhandledEditorAction", source)
        self.assertIn("handleMissingProjectAction(actionTarget);", click_handler)
        self.assertIn("handleUnhandledEditorAction(action, actionTarget);", click_handler)
        self.assertLess(
            click_handler.rfind('action === "reset-preview-debug-defaults"'),
            click_handler.rfind("handleUnhandledEditorAction(action, actionTarget);"),
        )
        self.assertIn("[Tony Na Engine] Unhandled editor action", source)


if __name__ == "__main__":
    unittest.main()
