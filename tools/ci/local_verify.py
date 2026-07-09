#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


ROOT_DIR = Path(__file__).resolve().parents[2]
EDITOR_INDEX_PATH = ROOT_DIR / "prototype_editor" / "index.html"
SCRIPT_SRC_PATTERN = re.compile(r"<script\b[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>", re.IGNORECASE)

PYTHON_SYNTAX_FILES = [
    "editor_local_security.py",
    "editor_snapshot_cache.py",
    "editor_static_cache.py",
    "export_route_playtest_workbook.py",
    "export_choice_consequence_sheet.py",
    "export_variable_influence_sheet.py",
    "export_asset_rights.py",
    "export_audio_cue_sheet.py",
    "export_stage_direction_sheet.py",
    "export_icon.py",
    "export_provenance_verifier.py",
    "export_presentation_timeline.py",
    "export_voice_production.py",
    "export_localization_audit.py",
    "export_package_guide.py",
    "export_quality_reports.py",
    "export_report_descriptions.py",
    "export_release_control.py",
    "export_release_artifacts.py",
    "export_release_evidence_pack.py",
    "export_release_readiness.py",
    "export_runtime_preload.py",
    "native_runtime_export_commands.py",
    "native_runtime_export_digest.py",
    "export_story_route_map.py",
    "export_unlockable_manifest.py",
    "renpy_export.py",
    "run_editor.py",
    "native_runtime/runtime_player.py",
    "native_runtime/runtime_i18n.py",
    "native_runtime/runtime_player_settings.py",
    "native_runtime/runtime_text_effects.py",
    "native_runtime/runtime_storage.py",
    "native_runtime/runtime_variables.py",
    "native_runtime/runtime_vn_quality.py",
    "native_runtime/runtime_performance.py",
    "native_runtime/runtime_preload.py",
    "native_runtime/runtime_scene_prefetch.py",
    "native_runtime/runtime_diagnostics.py",
    "native_runtime/build_native_runtime_app.py",
    "tools/ci/maintainability_check.py",
    "tools/ci/local_verify.py",
    "tools/ci/project_health.py",
    "tools/release/check_editor_signing_readiness.py",
    "tools/release/prepare_preview_release.py",
    "tools/runtime/run_native_runtime_smoke.py",
    "tests/test_ci_workflow_coverage.py",
    "tests/test_editor_infrastructure.py",
    "tests/test_export_icon.py",
    "tests/test_export_provenance_verifier.py",
    "tests/test_export_release_artifacts.py",
    "tests/test_export_asset_rights.py",
    "tests/test_export_audio_cue_sheet.py",
    "tests/test_export_stage_direction_sheet.py",
    "tests/test_export_presentation_timeline.py",
    "tests/test_export_voice_production.py",
    "tests/test_prepare_preview_release.py",
    "tests/test_release_public_surface.py",
    "tests/test_maintainability_check_tool.py",
    "tests/test_native_runtime_export_commands.py",
    "tests/test_native_runtime_export_digest.py",
    "tests/test_frontend_action_handlers.py",
    "tests/test_run_editor_smoke.py",
    "tests/test_native_runtime_render_smoke.py",
    "tests/test_browser_playwright_smoke.py",
]


@dataclass(frozen=True)
class VerifyStep:
    name: str
    command: list[str]
    category: str
    required: bool = True
    env: dict[str, str] = field(default_factory=dict)
    timeout_seconds: int | None = None


@dataclass
class StepResult:
    name: str
    category: str
    command: list[str]
    status: str
    duration_seconds: float = 0.0
    returncode: int | None = None
    output_tail: str = ""
    skipped_reason: str = ""


ANSI_COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "red": "\033[31m",
    "cyan": "\033[36m",
    "muted": "\033[2m",
}

STATUS_BADGES = {
    "passed": ("[PASS]", "green"),
    "failed": ("[FAIL]", "red"),
    "planned": ("[PLAN]", "cyan"),
    "skipped": ("[SKIP]", "yellow"),
}


def get_python_executable() -> str:
    return sys.executable or "python3"


def discover_editor_module_scripts() -> list[str]:
    html = EDITOR_INDEX_PATH.read_text(encoding="utf-8")
    return [
        script.removeprefix("./")
        for script in SCRIPT_SRC_PATTERN.findall(html)
        if script.startswith("./modules/")
    ]


def discover_frontend_tests() -> list[str]:
    return sorted(path.name for path in (ROOT_DIR / "tests").glob("test_frontend*.py"))


def discover_python_test_files() -> list[str]:
    return sorted(f"tests/{path.name}" for path in (ROOT_DIR / "tests").glob("test_*.py"))


def build_python_compile_step(python_executable: str) -> VerifyStep:
    compile_files = sorted(dict.fromkeys(PYTHON_SYNTAX_FILES + discover_python_test_files()))
    return VerifyStep(
        name="Python syntax check",
        category="syntax",
        command=[python_executable, "-m", "py_compile", *compile_files],
    )


def build_node_check_steps() -> list[VerifyStep]:
    module_scripts = discover_editor_module_scripts()
    script_paths = [f"prototype_editor/{script}" for script in module_scripts]
    script_paths.extend(
        [
            "prototype_editor/app.js",
            "export_player_template/runtime_conditions.js",
            "export_player_template/player.js",
            "export_player_template/runtime_data.js",
            "export_player_template/runtime_visual_constants.js",
            "export_player_template/runtime_controls.js",
            "export_player_template/runtime_settings.js",
            "export_player_template/runtime_i18n.js",
            "export_player_template/runtime_audio.js",
            "export_player_template/runtime_preload.js",
            "export_player_template/runtime_scene_prefetch.js",
            "export_player_template/runtime_text_effects.js",
        ]
    )
    return [
        VerifyStep(
            name=f"Node syntax: {script_path}",
            category="frontend-syntax",
            command=["node", "--check", script_path],
        )
        for script_path in script_paths
    ]


def build_unittest_step(name: str, pattern: str, category: str, python_executable: str) -> VerifyStep:
    return VerifyStep(
        name=name,
        category=category,
        command=[python_executable, "-m", "unittest", "discover", "-s", "tests", "-p", pattern, "-v"],
    )


def build_frontend_unittest_steps(python_executable: str) -> list[VerifyStep]:
    return [
        build_unittest_step(f"Frontend tests: {test_name}", test_name, "frontend-tests", python_executable)
        for test_name in discover_frontend_tests()
    ]


def build_release_tooling_steps(python_executable: str) -> list[VerifyStep]:
    return [
        build_unittest_step("CI workflow coverage", "test_ci_workflow_coverage.py", "release-tests", python_executable),
        build_unittest_step("GitHub status tooling", "test_github_status_tool.py", "release-tests", python_executable),
        build_unittest_step("Local verify tooling", "test_local_verify_tool.py", "release-tests", python_executable),
        build_unittest_step("Native runtime export command writer", "test_native_runtime_export_commands.py", "release-tests", python_executable),
        build_unittest_step("Native runtime export digest", "test_native_runtime_export_digest.py", "release-tests", python_executable),
        build_unittest_step("Maintainability tooling", "test_maintainability_check_tool.py", "release-tests", python_executable),
        VerifyStep(
            name="Maintainability guardrails",
            category="release-tests",
            command=[
                python_executable,
                "tools/ci/maintainability_check.py",
                "--json-report",
                "verification_reports/maintainability.json",
                "--markdown-report",
                "verification_reports/maintainability.md",
            ],
        ),
        build_unittest_step("Project health tooling", "test_project_health_tool.py", "release-tests", python_executable),
        build_unittest_step("Ren'Py export contract", "test_renpy_export_contract.py", "release-tests", python_executable),
        build_unittest_step("Runtime preload export contract", "test_export_runtime_preload.py", "release-tests", python_executable),
        build_unittest_step("Export report description parity", "test_export_report_description_parity.py", "release-tests", python_executable),
        build_unittest_step("Export performance budget contract", "test_export_performance_budget.py", "release-tests", python_executable),
        build_unittest_step("Export icon contract", "test_export_icon.py", "release-tests", python_executable),
        build_unittest_step("Export provenance verifier contract", "test_export_provenance_verifier.py", "release-tests", python_executable),
        build_unittest_step("Export release artifacts contract", "test_export_release_artifacts.py", "release-tests", python_executable),
        build_unittest_step("Export release evidence pack contract", "test_export_release_evidence_pack.py", "release-tests", python_executable),
        build_unittest_step("Export route playtest workbook contract", "test_export_route_playtest_workbook.py", "release-tests", python_executable),
        build_unittest_step("Export choice consequence contract", "test_export_choice_consequence_sheet.py", "release-tests", python_executable),
        build_unittest_step("Export variable influence contract", "test_export_variable_influence_sheet.py", "release-tests", python_executable),
        build_unittest_step("Export asset rights contract", "test_export_asset_rights.py", "release-tests", python_executable),
        build_unittest_step("Export audio cue sheet contract", "test_export_audio_cue_sheet.py", "release-tests", python_executable),
        build_unittest_step("Export stage direction contract", "test_export_stage_direction_sheet.py", "release-tests", python_executable),
        build_unittest_step("Export presentation timeline contract", "test_export_presentation_timeline.py", "release-tests", python_executable),
        build_unittest_step("Export voice production contract", "test_export_voice_production.py", "release-tests", python_executable),
        build_unittest_step("Native runtime i18n contract", "test_native_runtime_i18n.py", "release-tests", python_executable),
        VerifyStep(
            name="Template project health check",
            category="release-tests",
            command=[
                python_executable,
                "tools/ci/project_health.py",
                "template_project",
                "--json-report",
                "verification_reports/project-health-template.json",
                "--markdown-report",
                "verification_reports/project-health-template.md",
            ],
        ),
        build_unittest_step("Preview release tooling", "test_prepare_preview_release.py", "release-tests", python_executable),
        build_unittest_step("Public release surface guard", "test_release_public_surface.py", "release-tests", python_executable),
    ]


def build_backend_smoke_step(python_executable: str) -> VerifyStep:
    return build_unittest_step("Backend smoke tests", "test_run_editor_smoke.py", "backend-smoke", python_executable)


def build_native_runtime_smoke_step(python_executable: str) -> VerifyStep:
    return VerifyStep(
        name="Native runtime render smoke tests",
        category="native-smoke",
        command=[
            python_executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-p",
            "test_native_runtime_render_smoke.py",
            "-v",
        ],
        env={
            "SDL_AUDIODRIVER": "dummy",
            "SDL_VIDEODRIVER": "dummy",
        },
    )


def build_browser_smoke_step(python_executable: str) -> VerifyStep:
    return build_unittest_step("Browser Playwright smoke tests", "test_browser_playwright_smoke.py", "browser-smoke", python_executable)


def build_verify_steps(profile: str, python_executable: str | None = None) -> list[VerifyStep]:
    safe_profile = profile.strip().lower()
    python_bin = python_executable or get_python_executable()
    base_steps = [build_python_compile_step(python_bin), *build_node_check_steps()]
    release_steps = [*build_release_tooling_steps(python_bin), *build_frontend_unittest_steps(python_bin)]

    if safe_profile == "syntax":
        return base_steps
    if safe_profile == "quick":
        return [*base_steps, *release_steps]
    if safe_profile == "standard":
        return [*base_steps, *release_steps, build_backend_smoke_step(python_bin)]
    if safe_profile == "full":
        return [
            *base_steps,
            *release_steps,
            build_backend_smoke_step(python_bin),
            build_native_runtime_smoke_step(python_bin),
            build_browser_smoke_step(python_bin),
        ]
    if safe_profile == "browser":
        return [build_browser_smoke_step(python_bin)]
    if safe_profile == "github":
        return [
            *base_steps,
            *release_steps,
            build_backend_smoke_step(python_bin),
            build_native_runtime_smoke_step(python_bin),
            build_browser_smoke_step(python_bin),
        ]

    raise ValueError(f"Unknown verify profile: {profile}")


def check_required_tools(steps: Sequence[VerifyStep]) -> list[str]:
    missing: list[str] = []
    for step in steps:
        executable = step.command[0]
        if executable == sys.executable:
            continue
        if shutil.which(executable) is None and not Path(executable).exists():
            missing.append(executable)
    return sorted(set(missing))


def parse_porcelain_status(status_text: str) -> dict[str, int]:
    counts = {"staged": 0, "unstaged": 0, "untracked": 0, "total": 0}
    for line in str(status_text or "").splitlines():
        if not line:
            continue
        if line.startswith("??"):
            counts["untracked"] += 1
            counts["total"] += 1
            continue
        index_status = line[0] if len(line) > 0 else " "
        worktree_status = line[1] if len(line) > 1 else " "
        if index_status != " ":
            counts["staged"] += 1
        if worktree_status != " ":
            counts["unstaged"] += 1
        if index_status != " " or worktree_status != " ":
            counts["total"] += 1
    return counts


def run_git_command(args: Sequence[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout).strip())
    return completed.stdout.rstrip("\n")


def get_git_snapshot() -> dict[str, object]:
    try:
        sha = run_git_command(["rev-parse", "HEAD"])
        branch = run_git_command(["branch", "--show-current"]) or "(detached)"
        dirty = parse_porcelain_status(run_git_command(["status", "--porcelain"]))
    except RuntimeError as error:
        return {
            "available": False,
            "error": compact_report_text(error, 220),
        }
    return {
        "available": True,
        "branch": branch,
        "sha": sha,
        "shortSha": sha[:7],
        "dirty": dirty,
        "hasUncommittedChanges": dirty["total"] > 0,
    }


def build_git_clean_result(git_snapshot: dict[str, object]) -> StepResult:
    if not git_snapshot.get("available"):
        return StepResult(
            name="Git clean working tree",
            category="git",
            command=["git", "status", "--porcelain"],
            status="failed",
            returncode=None,
            output_tail=f"Git status could not be checked: {git_snapshot.get('error', 'unknown error')}",
        )

    dirty = git_snapshot.get("dirty") if isinstance(git_snapshot.get("dirty"), dict) else {}
    total = int(dirty.get("total") or 0)
    if total == 0:
        return StepResult(
            name="Git clean working tree",
            category="git",
            command=["git", "status", "--porcelain"],
            status="passed",
            returncode=0,
            output_tail="Git working tree is clean.",
        )

    output = (
        f"Git working tree has {total} local change(s).\n"
        f"Staged / unstaged / untracked: {dirty.get('staged', 0)} / {dirty.get('unstaged', 0)} / {dirty.get('untracked', 0)}.\n"
        "Commit, stash, or intentionally keep these changes before making a final release."
    )
    return StepResult(
        name="Git clean working tree",
        category="git",
        command=["git", "status", "--porcelain"],
        status="failed",
        returncode=1,
        output_tail=output,
    )


def build_missing_tool_results(steps: Sequence[VerifyStep], missing_tools: Sequence[str]) -> list[StepResult]:
    results: list[StepResult] = []
    for tool in sorted(set(missing_tools)):
        affected_steps = [step.name for step in steps if step.command and step.command[0] == tool]
        affected_preview = ", ".join(affected_steps[:5])
        if len(affected_steps) > 5:
            affected_preview += f", ... (+{len(affected_steps) - 5} more)"
        output = (
            f"Missing required tool: {tool}.\n"
            f"Affected checks: {affected_preview or 'unknown'}.\n"
            "Install the tool, add it to PATH, or choose a verification profile that does not require it."
        )
        results.append(
            StepResult(
                name=f"Missing required tool: {tool}",
                category="environment",
                command=[tool],
                status="failed",
                returncode=None,
                output_tail=output,
                skipped_reason="required tool missing",
            )
        )
    return results


def run_step(step: VerifyStep, dry_run: bool = False) -> StepResult:
    if dry_run:
        return StepResult(name=step.name, category=step.category, command=step.command, status="planned")

    env = os.environ.copy()
    env.update(step.env)
    start = time.perf_counter()
    try:
        completed = subprocess.run(
            step.command,
            cwd=ROOT_DIR,
            env=env,
            capture_output=True,
            text=True,
            check=False,
            timeout=step.timeout_seconds,
        )
    except subprocess.TimeoutExpired as error:
        duration = time.perf_counter() - start
        captured_output = "".join(
            part.decode("utf-8", errors="replace") if isinstance(part, bytes) else str(part or "")
            for part in (error.stdout, error.stderr)
        )
        timeout_note = f"Command timed out after {error.timeout}s."
        output = f"{captured_output}\n{timeout_note}".strip()
        return StepResult(
            name=step.name,
            category=step.category,
            command=step.command,
            status="failed",
            duration_seconds=duration,
            returncode=None,
            output_tail=output[-4000:],
        )
    duration = time.perf_counter() - start
    output = f"{completed.stdout}{completed.stderr}"
    return StepResult(
        name=step.name,
        category=step.category,
        command=step.command,
        status="passed" if completed.returncode == 0 else "failed",
        duration_seconds=duration,
        returncode=completed.returncode,
        output_tail=output[-4000:],
    )


def summarize_results(results: Sequence[StepResult]) -> dict[str, object]:
    passed = sum(1 for result in results if result.status == "passed")
    failed = sum(1 for result in results if result.status == "failed")
    planned = sum(1 for result in results if result.status == "planned")
    skipped = sum(1 for result in results if result.status == "skipped")
    duration = sum(result.duration_seconds for result in results)
    categories: dict[str, dict[str, object]] = {}
    for result in results:
        category = result.category or "uncategorized"
        category_summary = categories.setdefault(
            category,
            {"passed": 0, "failed": 0, "planned": 0, "skipped": 0, "total": 0, "durationSeconds": 0.0},
        )
        category_summary["total"] = int(category_summary["total"]) + 1
        category_summary["durationSeconds"] = float(category_summary["durationSeconds"]) + result.duration_seconds
        if result.status in {"passed", "failed", "planned", "skipped"}:
            category_summary[result.status] = int(category_summary[result.status]) + 1
    for category_summary in categories.values():
        category_summary["durationSeconds"] = round(float(category_summary["durationSeconds"]), 2)
    failed_results = [result for result in results if result.status == "failed"]
    first_failed = failed_results[0] if failed_results else None
    return {
        "status": "failed" if failed else "planned" if planned and not passed else "passed",
        "passed": passed,
        "failed": failed,
        "planned": planned,
        "skipped": skipped,
        "total": len(results),
        "durationSeconds": round(duration, 2),
        "categories": categories,
        "failedCategories": sorted({result.category for result in failed_results}),
        "firstFailedStep": (
            {
                "name": first_failed.name,
                "category": first_failed.category,
                "command": first_failed.command,
                "returncode": first_failed.returncode,
            }
            if first_failed
            else None
        ),
    }


def format_command(command: Sequence[str]) -> str:
    return shlex.join([str(part) for part in command])


def should_use_terminal_color(stream: object = sys.stdout) -> bool:
    is_tty = bool(getattr(stream, "isatty", lambda: False)())
    return is_tty and not os.environ.get("NO_COLOR") and os.environ.get("TERM", "") != "dumb"


def colorize_terminal(text: object, color: str, enabled: bool = False) -> str:
    safe_text = str(text)
    if not enabled:
        return safe_text
    prefix = ANSI_COLORS.get(color, "")
    reset = ANSI_COLORS["reset"] if prefix else ""
    return f"{prefix}{safe_text}{reset}"


def get_terminal_status_badge(status: str, use_color: bool = False) -> str:
    label, color = STATUS_BADGES.get(status, (f"[{status.upper()}]", "muted"))
    return colorize_terminal(label, color, use_color)


def format_terminal_step_header(index: int, total: int, step: VerifyStep) -> str:
    return f"[{index:02d}/{total:02d}] {step.name} ({step.category})"


def format_terminal_step_result(result: StepResult, use_color: bool = False) -> str:
    badge = get_terminal_status_badge(result.status, use_color)
    suffix = f"{result.duration_seconds:.2f}s"
    if result.returncode not in (None, 0):
        suffix += f", exit {result.returncode}"
    return f"  {badge} {result.status} in {suffix}"


def build_terminal_header_lines(
    profile: str,
    steps: Sequence[VerifyStep],
    git_snapshot: dict[str, object] | None = None,
    use_color: bool = False,
) -> list[str]:
    git = git_snapshot or {}
    lines = [
        colorize_terminal("Canvasia Engine Verify", "bold", use_color),
        f"Profile: {profile} | Checks: {len(steps)}",
    ]
    if git.get("available"):
        dirty = git.get("dirty") if isinstance(git.get("dirty"), dict) else {}
        lines.append(
            "Git: "
            f"{git.get('branch', '(unknown)')} @ {git.get('shortSha', '')} | "
            f"local changes: {dirty.get('total', 0)}"
        )
    else:
        lines.append(f"Git: unavailable ({compact_report_text(git.get('error', 'unknown'), 120)})")
    return lines


def build_terminal_summary_lines(
    summary: dict[str, object],
    results: Sequence[StepResult],
    git_snapshot: dict[str, object] | None = None,
    report_paths: Sequence[Path] = (),
    use_color: bool = False,
) -> list[str]:
    badge = get_terminal_status_badge(str(summary.get("status", "unknown")), use_color)
    lines = [
        "",
        colorize_terminal("Verification Summary", "bold", use_color),
        (
            f"{badge} {summary.get('passed', 0)} passed / {summary.get('failed', 0)} failed / "
            f"{summary.get('planned', 0)} planned / {summary.get('skipped', 0)} skipped "
            f"in {summary.get('durationSeconds', 0)}s"
        ),
    ]

    categories = summary.get("categories") if isinstance(summary.get("categories"), dict) else {}
    if categories:
        lines.append("Category breakdown:")
        for category, category_summary in sorted(categories.items()):
            if not isinstance(category_summary, dict):
                continue
            status_text = (
                f"{category_summary.get('passed', 0)} pass, "
                f"{category_summary.get('failed', 0)} fail, "
                f"{category_summary.get('planned', 0)} plan"
            )
            lines.append(f"  - {category}: {status_text}, {category_summary.get('durationSeconds', 0)}s")

    failed_results = [result for result in results if result.status == "failed"]
    if failed_results:
        first_failed = failed_results[0]
        lines.extend(
            [
                "First failure:",
                f"  - {first_failed.name} ({first_failed.category})",
                f"  - Re-run: {format_command(first_failed.command)}",
            ]
        )
    else:
        git = git_snapshot or {}
        dirty = git.get("dirty") if isinstance(git.get("dirty"), dict) else {}
        if int(dirty.get("total") or 0) > 0:
            lines.append("Next: checks passed; review local changes, then commit when ready.")
        else:
            lines.append("Next: checks passed and the working tree is clean.")

    if report_paths:
        lines.append("Reports:")
        for path in report_paths:
            lines.append(f"  - {path}")

    return lines


def print_terminal_lines(lines: Sequence[str]) -> None:
    for line in lines:
        print(line)


def compact_report_text(value: object, limit: int = 500) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    safe_limit = max(int(limit or 0), 20)
    if len(text) <= safe_limit:
        return text
    return f"{text[: safe_limit - 3].rstrip()}..."


def format_markdown_inline_code(value: object) -> str:
    return compact_report_text(value).replace("`", "'")


def format_markdown_table_cell(value: object, limit: int = 160) -> str:
    return compact_report_text(value, limit).replace("|", r"\|")


def choose_markdown_code_fence(value: object) -> str:
    text = str(value or "")
    fence = "```"
    while fence in text:
        fence += "`"
    return fence


def get_report_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json_report(
    path: Path,
    profile: str,
    results: Sequence[StepResult],
    generated_at: str | None = None,
    git_snapshot: dict[str, object] | None = None,
) -> None:
    payload = {
        "profile": profile,
        "generatedAt": generated_at or get_report_timestamp(),
        "git": git_snapshot if git_snapshot is not None else get_git_snapshot(),
        "summary": summarize_results(results),
        "steps": [
            {
                "name": result.name,
                "category": result.category,
                "command": result.command,
                "status": result.status,
                "durationSeconds": round(result.duration_seconds, 2),
                "returncode": result.returncode,
                "outputTail": result.output_tail,
                "skippedReason": result.skipped_reason,
            }
            for result in results
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n", encoding="utf-8")


def write_markdown_report(
    path: Path,
    profile: str,
    results: Sequence[StepResult],
    generated_at: str | None = None,
    git_snapshot: dict[str, object] | None = None,
) -> None:
    summary = summarize_results(results)
    git = git_snapshot if git_snapshot is not None else get_git_snapshot()
    lines = [
        "# Canvasia Engine Local Verify Report",
        "",
        f"- Profile: `{profile}`",
        f"- Generated: `{generated_at or get_report_timestamp()}`",
        f"- Status: `{summary['status']}`",
        f"- Passed: {summary['passed']}",
        f"- Failed: {summary['failed']}",
        f"- Planned: {summary['planned']}",
        f"- Duration: {summary['durationSeconds']}s",
    ]
    if git.get("available"):
        dirty = git.get("dirty") if isinstance(git.get("dirty"), dict) else {}
        lines.extend(
            [
                "",
                "## Git Snapshot",
                "",
                f"- Branch: `{format_markdown_inline_code(git.get('branch', ''))}`",
                f"- Commit: `{format_markdown_inline_code(git.get('shortSha', ''))}`",
                f"- Local changes: `{dirty.get('total', 0)}`",
                f"- Staged / unstaged / untracked: `{dirty.get('staged', 0)} / {dirty.get('unstaged', 0)} / {dirty.get('untracked', 0)}`",
            ]
        )
    else:
        lines.extend(["", "## Git Snapshot", "", f"- Git unavailable: `{format_markdown_inline_code(git.get('error', 'unknown'))}`"])
    categories = summary.get("categories") or {}
    if categories:
        lines.extend(["", "## Category Summary", "", "| Category | Passed | Failed | Planned | Seconds |", "| --- | --- | --- | --- | --- |"])
        for category, category_summary in sorted(categories.items()):
            if not isinstance(category_summary, dict):
                continue
            lines.append(
                "| "
                + " | ".join(
                    [
                        format_markdown_table_cell(category),
                        str(category_summary.get("passed", 0)),
                        str(category_summary.get("failed", 0)),
                        str(category_summary.get("planned", 0)),
                        str(category_summary.get("durationSeconds", 0)),
                    ]
                )
                + " |"
            )
    failed_results = [result for result in results if result.status == "failed"]
    if failed_results:
        failed_categories = ", ".join(sorted({result.category for result in failed_results}))
        first_failed = failed_results[0]
        lines.extend(
            [
                "",
                "## Release Triage",
                "",
                f"- Failed categories: `{format_markdown_inline_code(failed_categories)}`",
                f"- First failed step: `{format_markdown_inline_code(first_failed.name)}`",
                f"- Re-run command: `{format_markdown_inline_code(format_command(first_failed.command))}`",
            ]
        )
    lines.extend(
        [
        "",
        "## Step Details",
        "",
        "| Step | Category | Status | Seconds |",
        "| --- | --- | --- | --- |",
        ]
    )
    for result in results:
        lines.append(
            "| "
            + " | ".join(
                [
                    format_markdown_table_cell(result.name),
                    format_markdown_table_cell(result.category),
                    format_markdown_table_cell(result.status),
                    str(round(result.duration_seconds, 2)),
                ]
            )
            + " |"
        )
    if failed_results:
        lines.extend(["", "## Failed Output"])
        for result in failed_results:
            output = result.output_tail.strip()
            fence = choose_markdown_code_fence(output)
            lines.extend(
                [
                    "",
                    f"### {compact_report_text(result.name)}",
                    "",
                    f"Command: `{format_markdown_inline_code(format_command(result.command))}`",
                    "",
                    f"{fence}text",
                    output,
                    fence,
                ]
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report_directory(
    path: Path,
    profile: str,
    results: Sequence[StepResult],
    git_snapshot: dict[str, object] | None = None,
) -> tuple[Path, Path]:
    safe_profile = re.sub(r"[^a-z0-9_-]+", "-", profile.strip().lower()).strip("-") or "verify"
    json_path = path / f"local-verify-{safe_profile}.json"
    markdown_path = path / f"local-verify-{safe_profile}.md"
    generated_at = get_report_timestamp()
    git_snapshot = git_snapshot if git_snapshot is not None else get_git_snapshot()
    write_json_report(json_path, profile, results, generated_at=generated_at, git_snapshot=git_snapshot)
    write_markdown_report(markdown_path, profile, results, generated_at=generated_at, git_snapshot=git_snapshot)
    write_json_report(path / "local-verify-latest.json", profile, results, generated_at=generated_at, git_snapshot=git_snapshot)
    write_markdown_report(path / "local-verify-latest.md", profile, results, generated_at=generated_at, git_snapshot=git_snapshot)
    return json_path, markdown_path


def print_plan(steps: Sequence[VerifyStep]) -> None:
    print("Local verify plan:")
    for index, step in enumerate(steps, start=1):
        print(f"{index:02d}. {step.name} [{step.category}]")
        print(f"    {format_command(step.command)}")


def run_verify_steps(
    steps: Sequence[VerifyStep],
    dry_run: bool = False,
    fail_fast: bool = True,
    emit_progress: bool = True,
    use_color: bool = False,
) -> list[StepResult]:
    if dry_run:
        if emit_progress:
            print_plan(steps)
        return [run_step(step, dry_run=True) for step in steps]

    results: list[StepResult] = []
    for index, step in enumerate(steps, start=1):
        if emit_progress:
            print(format_terminal_step_header(index, len(steps), step))
        result = run_step(step)
        results.append(result)
        if emit_progress:
            print(format_terminal_step_result(result, use_color=use_color))
        if result.status == "failed":
            if emit_progress:
                print(result.output_tail, file=sys.stderr)
            if fail_fast:
                break
    return results


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Canvasia Engine local CI-style verification.")
    parser.add_argument(
        "--profile",
        choices=["syntax", "quick", "standard", "full", "browser", "github"],
        default="standard",
        help="Verification profile to run. Use full/github before important pushes.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print the planned checks without executing them.")
    parser.add_argument(
        "--no-fail-fast",
        action="store_true",
        help="Continue running later checks after a failure so the report shows every broken area.",
    )
    parser.add_argument(
        "--strict-clean",
        action="store_true",
        help="Fail the verification if the Git working tree has uncommitted changes.",
    )
    parser.add_argument("--json-report", type=Path, help="Write a machine-readable JSON report.")
    parser.add_argument("--markdown-report", type=Path, help="Write a human-readable Markdown report.")
    parser.add_argument(
        "--report-dir",
        type=Path,
        help="Write both JSON and Markdown reports into a directory using stable profile-based filenames.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    steps = build_verify_steps(args.profile)
    git_snapshot = get_git_snapshot()
    use_color = should_use_terminal_color(sys.stdout)
    print_terminal_lines(build_terminal_header_lines(args.profile, steps, git_snapshot, use_color=use_color))
    missing_tools = [] if args.dry_run else check_required_tools(steps)
    if missing_tools:
        print(f"Missing required tools: {', '.join(missing_tools)}", file=sys.stderr)
        results = build_missing_tool_results(steps, missing_tools)
    else:
        results = run_verify_steps(
            steps,
            dry_run=args.dry_run,
            fail_fast=not args.no_fail_fast,
            emit_progress=True,
            use_color=use_color,
        )

    if args.strict_clean:
        git_clean_result = build_git_clean_result(git_snapshot)
        results.append(git_clean_result)
        if git_clean_result.status == "failed":
            print(git_clean_result.output_tail, file=sys.stderr)

    standalone_generated_at = get_report_timestamp() if args.json_report or args.markdown_report else None
    if args.json_report:
        write_json_report(
            args.json_report,
            args.profile,
            results,
            generated_at=standalone_generated_at,
            git_snapshot=git_snapshot,
        )
    if args.markdown_report:
        write_markdown_report(
            args.markdown_report,
            args.profile,
            results,
            generated_at=standalone_generated_at,
            git_snapshot=git_snapshot,
        )
    if args.report_dir:
        json_path, markdown_path = write_report_directory(args.report_dir, args.profile, results, git_snapshot=git_snapshot)
        print(f"Reports written: {json_path} and {markdown_path}")

    summary = summarize_results(results)
    report_paths = [
        path
        for path in [
            args.json_report,
            args.markdown_report,
            args.report_dir / f"local-verify-{re.sub(r'[^a-z0-9_-]+', '-', args.profile.strip().lower()).strip('-') or 'verify'}.json"
            if args.report_dir
            else None,
            args.report_dir / f"local-verify-{re.sub(r'[^a-z0-9_-]+', '-', args.profile.strip().lower()).strip('-') or 'verify'}.md"
            if args.report_dir
            else None,
        ]
        if path
    ]
    print_terminal_lines(
        build_terminal_summary_lines(
            summary,
            results,
            git_snapshot=git_snapshot,
            report_paths=report_paths,
            use_color=use_color,
        )
    )
    if missing_tools:
        return 2
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
