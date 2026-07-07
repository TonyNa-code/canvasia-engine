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
EDITOR_MODULES_DIR = ROOT_DIR / "prototype_editor" / "modules"
TESTS_DIR = ROOT_DIR / "tests"
SCRIPT_SRC_PATTERN = re.compile(r"<script\b[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>", re.IGNORECASE)

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


def discover_entrypoint_modules() -> list[str]:
    html = EDITOR_INDEX_PATH.read_text(encoding="utf-8")
    modules = []
    for script in SCRIPT_SRC_PATTERN.findall(html):
        if script.startswith("./modules/"):
            modules.append(Path(script.removeprefix("./modules/")).stem)
    return sorted(dict.fromkeys(modules))


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


def build_report() -> dict[str, object]:
    file_budgets = evaluate_file_budgets()
    modules = evaluate_modules()
    failed_files = [item for item in file_budgets if item["status"] == "failed"]
    warning_files = [item for item in file_budgets if item["status"] == "warning"]
    hard_module_failures = (
        modules["missingEntrypoint"]
        or modules["staleEntrypoint"]
        or modules["newMissingTests"]
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
        },
        "fileBudgets": file_budgets,
        "modules": modules,
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
    ]
    if modules.get("newMissingTests"):
        lines.append("New modules missing tests: " + ", ".join(modules["newMissingTests"]))
    for item in report.get("fileBudgets", []):
        if isinstance(item, dict) and item.get("status") != "passed":
            lines.append(f"- {item.get('path')}: {item.get('lines')} lines, {item.get('note')}")
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
