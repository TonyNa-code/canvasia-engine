#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence


ROOT_DIR = Path(__file__).resolve().parents[2]
EDITOR_INDEX_PATH = ROOT_DIR / "prototype_editor" / "index.html"
SCRIPT_SRC_PATTERN = re.compile(r"<script\b[^>]*\bsrc=[\"']([^\"']+)[\"'][^>]*>", re.IGNORECASE)

PYTHON_SYNTAX_FILES = [
    "run_editor.py",
    "native_runtime/runtime_player.py",
    "native_runtime/build_native_runtime_app.py",
    "tools/release/check_editor_signing_readiness.py",
    "tools/release/prepare_preview_release.py",
    "tools/runtime/run_native_runtime_smoke.py",
    "tools/ci/local_verify.py",
    "tests/test_ci_workflow_coverage.py",
    "tests/test_prepare_preview_release.py",
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
    script_paths.extend(["prototype_editor/app.js", "export_player_template/player.js"])
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
        build_unittest_step("Preview release tooling", "test_prepare_preview_release.py", "release-tests", python_executable),
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


def run_step(step: VerifyStep, dry_run: bool = False) -> StepResult:
    if dry_run:
        return StepResult(name=step.name, category=step.category, command=step.command, status="planned")

    env = os.environ.copy()
    env.update(step.env)
    start = time.perf_counter()
    completed = subprocess.run(
        step.command,
        cwd=ROOT_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=step.timeout_seconds,
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
    return {
        "status": "failed" if failed else "planned" if planned and not passed else "passed",
        "passed": passed,
        "failed": failed,
        "planned": planned,
        "skipped": skipped,
        "total": len(results),
        "durationSeconds": round(duration, 2),
    }


def format_command(command: Sequence[str]) -> str:
    return " ".join(command)


def write_json_report(path: Path, profile: str, results: Sequence[StepResult]) -> None:
    payload = {
        "profile": profile,
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


def write_markdown_report(path: Path, profile: str, results: Sequence[StepResult]) -> None:
    summary = summarize_results(results)
    lines = [
        "# Tony Na Engine Local Verify Report",
        "",
        f"- Profile: `{profile}`",
        f"- Status: `{summary['status']}`",
        f"- Passed: {summary['passed']}",
        f"- Failed: {summary['failed']}",
        f"- Planned: {summary['planned']}",
        f"- Duration: {summary['durationSeconds']}s",
        "",
        "| Step | Category | Status | Seconds |",
        "| --- | --- | --- | --- |",
    ]
    for result in results:
        lines.append(
            f"| {result.name} | {result.category} | {result.status} | {round(result.duration_seconds, 2)} |"
        )
    failed_results = [result for result in results if result.status == "failed"]
    if failed_results:
        lines.extend(["", "## Failed Output"])
        for result in failed_results:
            lines.extend(
                [
                    "",
                    f"### {result.name}",
                    "",
                    f"Command: `{format_command(result.command)}`",
                    "",
                    "```text",
                    result.output_tail.strip(),
                    "```",
                ]
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_plan(steps: Sequence[VerifyStep]) -> None:
    print("Local verify plan:")
    for index, step in enumerate(steps, start=1):
        print(f"{index:02d}. [{step.category}] {format_command(step.command)}")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Tony Na Engine local CI-style verification.")
    parser.add_argument(
        "--profile",
        choices=["syntax", "quick", "standard", "full", "browser", "github"],
        default="standard",
        help="Verification profile to run. Use full/github before important pushes.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print the planned checks without executing them.")
    parser.add_argument("--json-report", type=Path, help="Write a machine-readable JSON report.")
    parser.add_argument("--markdown-report", type=Path, help="Write a human-readable Markdown report.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    steps = build_verify_steps(args.profile)
    missing_tools = check_required_tools(steps)
    if missing_tools:
        print(f"Missing required tools: {', '.join(missing_tools)}", file=sys.stderr)
        return 2

    if args.dry_run:
        print_plan(steps)
        results = [run_step(step, dry_run=True) for step in steps]
    else:
        results = []
        for index, step in enumerate(steps, start=1):
            print(f"[{index}/{len(steps)}] {step.name}")
            result = run_step(step)
            results.append(result)
            print(f"  -> {result.status} ({result.duration_seconds:.2f}s)")
            if result.status == "failed":
                print(result.output_tail, file=sys.stderr)
                break

    if args.json_report:
        write_json_report(args.json_report, args.profile, results)
    if args.markdown_report:
        write_markdown_report(args.markdown_report, args.profile, results)

    summary = summarize_results(results)
    print(
        f"Local verify {summary['status']}: "
        f"{summary['passed']} passed, {summary['failed']} failed, {summary['planned']} planned."
    )
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
