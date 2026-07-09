#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


ROOT_DIR = Path(__file__).resolve().parents[2]
EDITOR_INDEX_PATH = ROOT_DIR / "prototype_editor" / "index.html"
EDITOR_APP_PATH = ROOT_DIR / "prototype_editor" / "app.js"
EDITOR_MODULES_DIR = ROOT_DIR / "prototype_editor" / "modules"
MODULE_GUARD_PATH = EDITOR_MODULES_DIR / "module_guard.js"
TESTS_DIR = ROOT_DIR / "tests"
SCRIPT_SRC_PATTERN = re.compile(r"<script\b[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>", re.IGNORECASE)
MODULE_GUARD_REQUIREMENT_PATTERN = re.compile(
    r"\{\s*globalName:\s*\"([^\"]+)\"\s*,\s*script:\s*\"([^\"]+)\"\s*,\s*label:\s*\"([^\"]+)\"\s*\}",
    re.MULTILINE,
)
APP_WINDOW_GLOBAL_PATTERN = re.compile(r"window\.(Canvasia[A-Za-z0-9_]+)")
MODULE_GUARD_SCRIPT = "./modules/module_guard.js"
EDITOR_APP_SCRIPT = "./app.js"
ALLOWED_UNGUARDED_APP_GLOBALS = frozenset(
    {
        "CanvasiaEditorModuleGuard",
        # Legacy alias exported by project_milestones.js for older panels.
        "CanvasiaProjectMilestones",
    }
)

KNOWN_MODULE_TEST_DEBT = frozenset()


@dataclass(frozen=True)
class FileBudget:
    path: str
    warning_lines: int
    max_lines: int
    owner: str
    next_action: str


FILE_BUDGETS = (
    FileBudget(
        "prototype_editor/app.js",
        warning_lines=45_000,
        max_lines=50_000,
        owner="editor frontend",
        next_action="继续把纯渲染面板、摘要文案和状态计算抽到 prototype_editor/modules/。",
    ),
    FileBudget(
        "run_editor.py",
        warning_lines=15_000,
        max_lines=18_000,
        owner="editor backend",
        next_action="优先抽出无副作用的项目读写、导出和诊断 helper。",
    ),
    FileBudget(
        "native_runtime/runtime_player.py",
        warning_lines=16_000,
        max_lines=19_000,
        owner="native runtime",
        next_action="把菜单、资源预载和文本演出拆到 runtime_* sibling modules。",
    ),
    FileBudget(
        "export_player_template/player.js",
        warning_lines=11_000,
        max_lines=14_000,
        owner="web runtime",
        next_action="继续抽 runtime_audio / runtime_controls / runtime_text_effects 这类独立模块。",
    ),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    return len(path.read_text(encoding="utf-8").splitlines())


def discover_module_files() -> list[str]:
    return sorted(path.stem for path in EDITOR_MODULES_DIR.glob("*.js"))


def discover_entrypoint_scripts() -> list[str]:
    html = EDITOR_INDEX_PATH.read_text(encoding="utf-8")
    return SCRIPT_SRC_PATTERN.findall(html)


def discover_entrypoint_modules() -> list[str]:
    modules = []
    for script in discover_entrypoint_scripts():
        if script.startswith("./modules/"):
            modules.append(Path(script.removeprefix("./modules/")).stem)
    return sorted(dict.fromkeys(modules))


def discover_module_guard_requirements() -> list[dict[str, str]]:
    if not MODULE_GUARD_PATH.exists():
        return []
    source = MODULE_GUARD_PATH.read_text(encoding="utf-8")
    return [
        {"globalName": global_name, "script": script, "label": label}
        for global_name, script, label in MODULE_GUARD_REQUIREMENT_PATTERN.findall(source)
    ]


def discover_app_window_globals() -> list[str]:
    if not EDITOR_APP_PATH.exists():
        return []
    source = EDITOR_APP_PATH.read_text(encoding="utf-8")
    return sorted(set(APP_WINDOW_GLOBAL_PATTERN.findall(source)))


def discover_frontend_module_tests() -> set[str]:
    names: set[str] = set()
    for path in TESTS_DIR.glob("test_frontend*_module.py"):
        match = re.match(r"test_frontend_(.+)_module\.py$", path.name)
        if match:
            names.add(match.group(1))
    return names


def evaluate_file_budgets() -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for budget in FILE_BUDGETS:
        path = ROOT_DIR / budget.path
        line_count = count_lines(path)
        if not path.exists():
            status = "failed"
            note = "File is missing."
        elif line_count > budget.max_lines:
            status = "failed"
            note = f"Line count exceeds hard budget {budget.max_lines}."
        elif line_count > budget.warning_lines:
            status = "warning"
            note = f"Line count exceeds warning budget {budget.warning_lines}; keep extracting modules."
        else:
            status = "passed"
            note = "Within budget."
        results.append(
            {
                "path": budget.path,
                "owner": budget.owner,
                "lines": line_count,
                "warningLines": budget.warning_lines,
                "maxLines": budget.max_lines,
                "status": status,
                "note": note,
                "nextAction": budget.next_action,
            }
        )
    return results


def find_duplicates(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def evaluate_modules() -> dict[str, object]:
    module_files = discover_module_files()
    entrypoint_modules = discover_entrypoint_modules()
    module_file_set = set(module_files)
    entrypoint_set = set(entrypoint_modules)
    test_modules = discover_frontend_module_tests()
    missing_entrypoint = sorted(module_file_set - entrypoint_set)
    stale_entrypoint = sorted(entrypoint_set - module_file_set)
    missing_tests = sorted(module_file_set - test_modules)
    new_missing_tests = sorted(set(missing_tests) - KNOWN_MODULE_TEST_DEBT)
    known_debt = sorted(set(missing_tests) & KNOWN_MODULE_TEST_DEBT)

    return {
        "moduleCount": len(module_files),
        "entrypointModuleCount": len(entrypoint_modules),
        "testedModuleCount": len(module_file_set & test_modules),
        "missingEntrypoint": missing_entrypoint,
        "staleEntrypoint": stale_entrypoint,
        "missingTests": missing_tests,
        "newMissingTests": new_missing_tests,
        "knownTestDebt": known_debt,
        "knownTestDebtCount": len(known_debt),
    }


def evaluate_module_guard() -> dict[str, object]:
    entrypoint_scripts = discover_entrypoint_scripts()
    requirements = discover_module_guard_requirements()
    requirement_scripts = [requirement["script"] for requirement in requirements]
    requirement_globals = [requirement["globalName"] for requirement in requirements]
    requirement_global_set = set(requirement_globals)
    app_window_globals = discover_app_window_globals()
    guarded_app_globals = [
        global_name
        for global_name in app_window_globals
        if global_name not in ALLOWED_UNGUARDED_APP_GLOBALS
    ]
    app_globals_missing_from_guard = sorted(set(guarded_app_globals) - requirement_global_set)
    guard_globals_not_used_by_app = sorted(requirement_global_set - set(app_window_globals))
    startup_order_issues: list[str] = []

    guard_index = entrypoint_scripts.index(MODULE_GUARD_SCRIPT) if MODULE_GUARD_SCRIPT in entrypoint_scripts else None
    app_index = entrypoint_scripts.index(EDITOR_APP_SCRIPT) if EDITOR_APP_SCRIPT in entrypoint_scripts else None

    if guard_index is None:
        startup_order_issues.append(f"{MODULE_GUARD_SCRIPT} is missing from the editor entrypoint.")
    if app_index is None:
        startup_order_issues.append(f"{EDITOR_APP_SCRIPT} is missing from the editor entrypoint.")
    if guard_index is not None and app_index is not None:
        if guard_index > app_index:
            startup_order_issues.append(f"{MODULE_GUARD_SCRIPT} must run before {EDITOR_APP_SCRIPT}.")
        elif app_index != guard_index + 1:
            startup_order_issues.append(f"{MODULE_GUARD_SCRIPT} should run immediately before {EDITOR_APP_SCRIPT}.")

    if guard_index is not None:
        expected_guard_scripts = entrypoint_scripts[:guard_index]
    else:
        expected_guard_scripts = [
            script
            for script in entrypoint_scripts
            if script not in {MODULE_GUARD_SCRIPT, EDITOR_APP_SCRIPT}
        ]

    missing_from_guard = [script for script in expected_guard_scripts if script not in requirement_scripts]
    stale_guard_scripts = [script for script in requirement_scripts if script not in expected_guard_scripts]
    order_matches = requirement_scripts == expected_guard_scripts
    duplicate_globals = find_duplicates(requirement_globals)
    duplicate_scripts = find_duplicates(requirement_scripts)
    order_mismatch_preview = []
    if not order_matches:
        max_preview = min(max(len(expected_guard_scripts), len(requirement_scripts)), 6)
        for index in range(max_preview):
            expected = expected_guard_scripts[index] if index < len(expected_guard_scripts) else "<missing>"
            actual = requirement_scripts[index] if index < len(requirement_scripts) else "<missing>"
            if expected != actual:
                order_mismatch_preview.append(
                    {
                        "index": index,
                        "expected": expected,
                        "actual": actual,
                    }
                )
            if len(order_mismatch_preview) >= 4:
                break

    status = "passed"
    if (
        not MODULE_GUARD_PATH.exists()
        or not requirements
        or startup_order_issues
        or missing_from_guard
        or stale_guard_scripts
        or not order_matches
        or duplicate_globals
        or duplicate_scripts
        or app_globals_missing_from_guard
    ):
        status = "failed"

    return {
        "status": status,
        "requirementCount": len(requirements),
        "entrypointGuardedScriptCount": len(expected_guard_scripts),
        "missingFromGuard": missing_from_guard,
        "staleGuardScripts": stale_guard_scripts,
        "orderMatches": order_matches,
        "orderMismatchPreview": order_mismatch_preview,
        "duplicateGlobals": duplicate_globals,
        "duplicateScripts": duplicate_scripts,
        "startupOrderIssues": startup_order_issues,
        "appWindowGlobalCount": len(app_window_globals),
        "guardedAppGlobalCount": len(guarded_app_globals),
        "allowedUnguardedAppGlobals": sorted(ALLOWED_UNGUARDED_APP_GLOBALS & set(app_window_globals)),
        "appGlobalsMissingFromGuard": app_globals_missing_from_guard,
        "guardGlobalsNotUsedByApp": guard_globals_not_used_by_app,
        "firstRequirement": requirements[0] if requirements else None,
        "lastRequirement": requirements[-1] if requirements else None,
    }


def priority_rank(priority: str) -> int:
    ranks = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    return ranks.get(priority, 9)


def build_maintenance_action(
    priority: str,
    area: str,
    title: str,
    detail: str,
    evidence: str,
    next_step: str,
) -> dict[str, str]:
    return {
        "priority": priority,
        "area": area,
        "title": title,
        "detail": detail,
        "evidence": evidence,
        "nextStep": next_step,
    }


def build_maintenance_plan(
    file_budgets: Sequence[dict[str, object]],
    modules: dict[str, object],
    module_guard: dict[str, object],
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []

    if modules.get("missingEntrypoint") or modules.get("staleEntrypoint"):
        actions.append(
            build_maintenance_action(
                "P0",
                "frontend modules",
                "Sync editor module entrypoints",
                "A module exists without being loaded, or the entrypoint references a stale module.",
                (
                    f"missing={len(modules.get('missingEntrypoint') or [])}; "
                    f"stale={len(modules.get('staleEntrypoint') or [])}"
                ),
                "Update prototype_editor/index.html and the module guard in the same change.",
            )
        )

    if modules.get("newMissingTests"):
        missing_tests = ", ".join(str(name) for name in modules.get("newMissingTests", []))
        actions.append(
            build_maintenance_action(
                "P0",
                "frontend tests",
                "Add direct tests for new editor modules",
                "Every new frontend module should have a small focused Python contract test.",
                f"newMissingTests={missing_tests}",
                "Add tests/test_frontend_<module>_module.py before expanding the module surface.",
            )
        )

    if module_guard.get("status") != "passed":
        actions.append(
            build_maintenance_action(
                "P0",
                "startup guard",
                "Repair startup guard drift",
                "The editor startup guard no longer matches the actual module order or exported globals.",
                f"status={module_guard.get('status', 'unknown')}",
                "Regenerate or update prototype_editor/modules/module_guard.js alongside index.html.",
            )
        )

    for item in file_budgets:
        path = str(item.get("path", ""))
        lines = int(item.get("lines") or 0)
        warning_lines = int(item.get("warningLines") or 0)
        max_lines = int(item.get("maxLines") or 0)
        status = str(item.get("status", "unknown"))
        next_action = str(item.get("nextAction", "Split cohesive pure helpers into owned modules."))
        pressure = (lines / warning_lines) if warning_lines else 0.0

        if status == "failed":
            priority = "P0"
            title = "Reduce file size below the hard maintainability budget"
            detail = "This file is over the hard line-count limit and should be split before adding features."
        elif status == "warning":
            priority = "P1"
            title = "Bring file size back under the warning budget"
            detail = "This file is already large enough to slow future feature work."
        elif pressure >= 0.9:
            priority = "P2"
            title = "Extract the next cohesive module before this file crosses the warning budget"
            detail = "The file still passes, but it is close enough to the warning budget that new features should not land here by default."
        elif pressure >= 0.75:
            priority = "P3"
            title = "Plan the next extraction candidate"
            detail = "The file is healthy today, but it is a known growth area."
        else:
            continue

        actions.append(
            build_maintenance_action(
                priority,
                path,
                title,
                detail,
                f"{lines}/{warning_lines} warning lines, {max_lines} max lines",
                next_action,
            )
        )

    return sorted(actions, key=lambda action: (priority_rank(action["priority"]), action["area"], action["title"]))


def build_report() -> dict[str, object]:
    file_budgets = evaluate_file_budgets()
    modules = evaluate_modules()
    module_guard = evaluate_module_guard()
    maintenance_plan = build_maintenance_plan(file_budgets, modules, module_guard)
    failed_files = [item for item in file_budgets if item["status"] == "failed"]
    warning_files = [item for item in file_budgets if item["status"] == "warning"]
    hard_module_failures = (
        modules["missingEntrypoint"]
        or modules["staleEntrypoint"]
        or modules["newMissingTests"]
        or module_guard["status"] != "passed"
    )
    status = "failed" if failed_files or hard_module_failures else "passed"

    return {
        "generatedAt": utc_now(),
        "status": status,
        "summary": {
            "fileBudgetFailures": len(failed_files),
            "fileBudgetWarnings": len(warning_files),
            "moduleCount": modules["moduleCount"],
            "entrypointModuleCount": modules["entrypointModuleCount"],
            "testedModuleCount": modules["testedModuleCount"],
            "knownTestDebtCount": modules["knownTestDebtCount"],
            "newMissingTestCount": len(modules["newMissingTests"]),
            "moduleGuardStatus": module_guard["status"],
            "moduleGuardRequirementCount": module_guard["requirementCount"],
            "maintenanceActionCount": len(maintenance_plan),
            "topMaintenancePriority": maintenance_plan[0]["priority"] if maintenance_plan else "",
        },
        "fileBudgets": file_budgets,
        "modules": modules,
        "moduleGuard": module_guard,
        "maintenancePlan": maintenance_plan,
    }


def write_json_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_markdown_report(path: Path, report: dict[str, object]) -> None:
    summary = report["summary"] if isinstance(report["summary"], dict) else {}
    modules = report["modules"] if isinstance(report["modules"], dict) else {}
    lines = [
        "# Canvasia Engine Maintainability Report",
        "",
        f"- Generated: `{report.get('generatedAt', '')}`",
        f"- Status: `{report.get('status', 'unknown')}`",
        f"- Modules loaded by editor: `{summary.get('entrypointModuleCount', 0)}`",
        f"- Modules with direct tests: `{summary.get('testedModuleCount', 0)}`",
        f"- Known module test debt: `{summary.get('knownTestDebtCount', 0)}`",
        "",
        "## File Budgets",
        "",
        "| File | Lines | Warning | Max | Status |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for item in report.get("fileBudgets", []):
        if not isinstance(item, dict):
            continue
        lines.append(
            f"| `{item.get('path', '')}` | {item.get('lines', 0)} | {item.get('warningLines', 0)} | "
            f"{item.get('maxLines', 0)} | `{item.get('status', '')}` |"
        )
    if modules.get("knownTestDebt"):
        lines.extend(
            [
                "",
                "## Known Module Test Debt",
                "",
                ", ".join(f"`{name}`" for name in modules.get("knownTestDebt", [])),
            ]
        )
    if modules.get("newMissingTests"):
        lines.extend(
            [
                "",
                "## New Missing Module Tests",
                "",
                ", ".join(f"`{name}`" for name in modules.get("newMissingTests", [])),
            ]
        )
    maintenance_plan = report.get("maintenancePlan")
    if isinstance(maintenance_plan, list) and maintenance_plan:
        lines.extend(
            [
                "",
                "## Maintenance Roadmap",
                "",
                "| Priority | Area | Action | Evidence | Next step |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for action in maintenance_plan[:8]:
            if not isinstance(action, dict):
                continue
            lines.append(
                f"| `{action.get('priority', '')}` | `{action.get('area', '')}` | "
                f"{action.get('title', '')} | {action.get('evidence', '')} | {action.get('nextStep', '')} |"
            )
    module_guard = report.get("moduleGuard")
    if isinstance(module_guard, dict):
        lines.extend(
            [
                "",
                "## Startup Guard Consistency",
                "",
                f"- Status: `{module_guard.get('status', 'unknown')}`",
                f"- Guarded scripts: `{module_guard.get('entrypointGuardedScriptCount', 0)}`",
                f"- Guard requirements: `{module_guard.get('requirementCount', 0)}`",
                f"- Order matches entrypoint: `{module_guard.get('orderMatches', False)}`",
                f"- App globals covered: `{module_guard.get('guardedAppGlobalCount', 0)}`",
            ]
        )
        for key, title in (
            ("startupOrderIssues", "Startup order issues"),
            ("missingFromGuard", "Missing from guard"),
            ("staleGuardScripts", "Stale guard scripts"),
            ("duplicateGlobals", "Duplicate globals"),
            ("duplicateScripts", "Duplicate scripts"),
            ("appGlobalsMissingFromGuard", "App globals missing from guard"),
        ):
            values = module_guard.get(key)
            if values:
                lines.extend(["", f"### {title}", "", ", ".join(f"`{value}`" for value in values)])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def format_terminal_report(report: dict[str, object]) -> str:
    summary = report["summary"] if isinstance(report["summary"], dict) else {}
    modules = report["modules"] if isinstance(report["modules"], dict) else {}
    lines = [
        f"Canvasia maintainability: {report.get('status', 'unknown')}",
        (
            f"Files: {summary.get('fileBudgetFailures', 0)} failure(s), "
            f"{summary.get('fileBudgetWarnings', 0)} warning(s)"
        ),
        (
            f"Modules: {summary.get('entrypointModuleCount', 0)} loaded, "
            f"{summary.get('testedModuleCount', 0)} directly tested, "
            f"{summary.get('knownTestDebtCount', 0)} known debt"
        ),
        (
            f"Startup guard: {summary.get('moduleGuardStatus', 'unknown')} "
            f"({summary.get('moduleGuardRequirementCount', 0)} required globals)"
        ),
        (
            f"Maintenance roadmap: {summary.get('maintenanceActionCount', 0)} action(s), "
            f"top priority {summary.get('topMaintenancePriority', 'none') or 'none'}"
        ),
    ]
    if modules.get("newMissingTests"):
        lines.append("New modules missing tests: " + ", ".join(modules["newMissingTests"]))
    module_guard = report.get("moduleGuard")
    if isinstance(module_guard, dict) and module_guard.get("status") != "passed":
        for key in ("startupOrderIssues", "missingFromGuard", "staleGuardScripts", "duplicateGlobals", "duplicateScripts"):
            values = module_guard.get(key)
            if values:
                lines.append(f"Startup guard {key}: " + ", ".join(values))
        if module_guard.get("appGlobalsMissingFromGuard"):
            lines.append(
                "App globals missing from startup guard: "
                + ", ".join(module_guard["appGlobalsMissingFromGuard"])
            )
        if not module_guard.get("orderMatches", True):
            lines.append("Startup guard order does not match the editor entrypoint.")
    for item in report.get("fileBudgets", []):
        if isinstance(item, dict) and item.get("status") != "passed":
            lines.append(f"- {item.get('path')}: {item.get('lines')} lines, {item.get('note')}")
    maintenance_plan = report.get("maintenancePlan")
    if isinstance(maintenance_plan, list) and maintenance_plan:
        lines.append("Next maintenance actions:")
        for action in maintenance_plan[:3]:
            if isinstance(action, dict):
                lines.append(
                    f"- {action.get('priority')} {action.get('area')}: "
                    f"{action.get('title')} ({action.get('evidence')})"
                )
    return "\n".join(lines)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Canvasia Engine maintainability guardrails.")
    parser.add_argument("--json-report", type=Path, help="Write a machine-readable JSON report.")
    parser.add_argument("--markdown-report", type=Path, help="Write a human-readable Markdown report.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    report = build_report()
    if args.json_report:
        write_json_report(args.json_report, report)
    if args.markdown_report:
        write_markdown_report(args.markdown_report, report)
    print(format_terminal_report(report))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
