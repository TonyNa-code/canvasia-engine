from __future__ import annotations

from pathlib import Path


NATIVE_RUNTIME_COMMAND_KEYS = frozenset(
    {
        "mac_launcher",
        "linux_launcher",
        "windows_launcher",
        "mac_release_candidate",
        "linux_release_candidate",
        "windows_release_candidate",
        "mac_release_control",
        "linux_release_control",
        "windows_release_control",
        "mac_acceptance",
        "linux_acceptance",
        "windows_acceptance",
        "mac_file_integrity",
        "linux_file_integrity",
        "windows_file_integrity",
        "mac_app_builder",
        "linux_app_builder",
        "windows_app_builder",
    }
)


def _write_posix_script(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines), encoding="utf-8")
    path.chmod(0o755)


def _write_windows_script(path: Path, lines: list[str]) -> None:
    path.write_text("\r\n".join(lines), encoding="utf-8")


def _script_preamble() -> list[str]:
    return [
        "#!/bin/bash",
        "set -e",
        'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"',
        'cd "$SCRIPT_DIR"',
    ]


def _script_preamble_pipefail() -> list[str]:
    return [
        "#!/bin/bash",
        "set -e",
        "set -o pipefail",
        'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"',
        'cd "$SCRIPT_DIR"',
    ]


def write_native_runtime_command_files(
    build_dir: Path,
    *,
    command_names: dict[str, str],
    runtime_player_name: str,
    requirements_name: str,
    build_requirements_name: str,
) -> dict[str, Path]:
    missing = sorted(NATIVE_RUNTIME_COMMAND_KEYS - set(command_names))
    if missing:
        raise ValueError("Missing native runtime command names: " + ", ".join(missing))

    paths = {key: build_dir / command_names[key] for key in NATIVE_RUNTIME_COMMAND_KEYS}

    _write_posix_script(
        paths["mac_launcher"],
        [
            "#!/bin/bash",
            "set -e",
            'SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"',
            'cd "$SCRIPT_DIR"',
            f"python3 {runtime_player_name} game_data.json || {{",
            '  echo ""',
            '  echo "原生 Runtime 包没有启动成功。请先确认 Python 3 和 pygame-ce 已安装。"',
            f'  echo "安装命令：python3 -m pip install -r {requirements_name}"',
            '  echo ""',
            '  read -r -p "按回车关闭..." _',
            "  exit 1",
            "}",
            "",
        ],
    )
    _write_posix_script(
        paths["linux_launcher"],
        _script_preamble() + [f"python3 {runtime_player_name} game_data.json", ""],
    )
    _write_windows_script(
        paths["windows_launcher"],
        [
            "@echo off",
            "cd /d %~dp0",
            f"python {runtime_player_name} game_data.json",
            "if errorlevel 1 (",
            "  echo.",
            "  echo 原生 Runtime 包没有启动成功，请先确认 Python 3 和 pygame-ce 已安装。",
            f"  echo 安装命令：python -m pip install -r {requirements_name}",
            "  pause",
            ")",
            "",
        ],
    )

    _write_posix_script(
        paths["mac_release_candidate"],
        _script_preamble_pipefail()
        + [
            f"python3 {runtime_player_name} --release-candidate-report . | tee native-runtime-release-candidate-report.json || {{",
            '  echo ""',
            '  echo "发布候选检查发现阻塞项，报告已写入 native-runtime-release-candidate-report.json。"',
            '  echo "请先按报告修复，再继续打包或分发。"',
            '  echo ""',
            '  read -r -p "按回车关闭..." _',
            "  exit 1",
            "}",
            'echo ""',
            'echo "发布候选检查完成，报告已写入 native-runtime-release-candidate-report.json。"',
            'read -r -p "按回车关闭..." _',
            "",
        ],
    )
    _write_posix_script(
        paths["linux_release_candidate"],
        _script_preamble_pipefail()
        + [f"python3 {runtime_player_name} --release-candidate-report . | tee native-runtime-release-candidate-report.json", ""],
    )
    _write_windows_script(
        paths["windows_release_candidate"],
        [
            "@echo off",
            "cd /d %~dp0",
            f"python {runtime_player_name} --release-candidate-report . > native-runtime-release-candidate-report.json",
            "if errorlevel 1 (",
            "  echo.",
            "  echo 发布候选检查发现阻塞项，报告已写入 native-runtime-release-candidate-report.json。",
            "  echo 请先按报告修复，再继续打包或分发。",
            "  pause",
            "  exit /b 1",
            ")",
            "echo.",
            "echo 发布候选检查完成，报告已写入 native-runtime-release-candidate-report.json。",
            "pause",
            "",
        ],
    )

    _write_report_writer_scripts(
        paths,
        runtime_player_name=runtime_player_name,
        report_key="release_control",
        cli_flag="--write-release-control-reports",
        success_message="发布总控报告已生成：native-runtime-release-control-report.md / .json",
        failure_message="发布总控报告没有生成成功。请先确认 Python 3 和 pygame-ce 已安装。",
        fallback_hint=f"安装命令：python3 -m pip install -r {requirements_name}",
        windows_fallback_hint=f"安装命令：python -m pip install -r {requirements_name}",
    )
    _write_report_writer_scripts(
        paths,
        runtime_player_name=runtime_player_name,
        report_key="acceptance",
        cli_flag="--write-acceptance-reports",
        success_message="发布验收清单已生成：native-runtime-release-acceptance.md / .json",
        failure_message="发布验收清单没有生成成功。请先运行发布总控报告和文件完整性校验。",
        fallback_hint="可手动执行：python3 runtime_player.py --write-acceptance-reports .",
        windows_fallback_hint="可手动执行：python runtime_player.py --write-acceptance-reports .",
    )

    _write_posix_script(
        paths["mac_file_integrity"],
        _script_preamble()
        + [
            f"python3 {runtime_player_name} --verify-file-integrity . || {{",
            '  echo ""',
            '  echo "文件完整性校验未通过。请重新下载或重新导出原生 Runtime 包。"',
            '  echo ""',
            '  read -r -p "按回车关闭..." _',
            "  exit 1",
            "}",
            'echo ""',
            'echo "文件完整性校验通过。"',
            'read -r -p "按回车关闭..." _',
            "",
        ],
    )
    _write_posix_script(
        paths["linux_file_integrity"],
        _script_preamble() + [f"python3 {runtime_player_name} --verify-file-integrity .", ""],
    )
    _write_windows_script(
        paths["windows_file_integrity"],
        [
            "@echo off",
            "cd /d %~dp0",
            f"python {runtime_player_name} --verify-file-integrity .",
            "if errorlevel 1 (",
            "  echo.",
            "  echo 文件完整性校验未通过，请重新下载或重新导出原生 Runtime 包。",
            "  pause",
            "  exit /b 1",
            ")",
            "echo.",
            "echo 文件完整性校验通过。",
            "pause",
            "",
        ],
    )

    _write_app_builder_scripts(
        paths,
        requirements_name=requirements_name,
        build_requirements_name=build_requirements_name,
    )
    return paths


def _write_report_writer_scripts(
    paths: dict[str, Path],
    *,
    runtime_player_name: str,
    report_key: str,
    cli_flag: str,
    success_message: str,
    failure_message: str,
    fallback_hint: str,
    windows_fallback_hint: str,
) -> None:
    _write_posix_script(
        paths[f"mac_{report_key}"],
        _script_preamble()
        + [
            f"python3 {runtime_player_name} {cli_flag} . || {{",
            '  echo ""',
            f'  echo "{failure_message}"',
            f'  echo "{fallback_hint}"',
            '  echo ""',
            '  read -r -p "按回车关闭..." _',
            "  exit 1",
            "}",
            'echo ""',
            f'echo "{success_message}"',
            'read -r -p "按回车关闭..." _',
            "",
        ],
    )
    _write_posix_script(
        paths[f"linux_{report_key}"],
        _script_preamble() + [f"python3 {runtime_player_name} {cli_flag} .", ""],
    )
    _write_windows_script(
        paths[f"windows_{report_key}"],
        [
            "@echo off",
            "cd /d %~dp0",
            f"python {runtime_player_name} {cli_flag} .",
            "if errorlevel 1 (",
            "  echo.",
            f"  echo {failure_message}",
            f"  echo {windows_fallback_hint}",
            "  pause",
            "  exit /b 1",
            ")",
            "echo.",
            f"echo {success_message}",
            "pause",
            "",
        ],
    )


def _write_app_builder_scripts(
    paths: dict[str, Path],
    *,
    requirements_name: str,
    build_requirements_name: str,
) -> None:
    _write_posix_script(
        paths["mac_app_builder"],
        _script_preamble()
        + [
            f"python3 -m pip install -r {requirements_name} -r {build_requirements_name}",
            "python3 build_native_runtime_app.py --mode onedir . || {",
            '  echo ""',
            '  echo "原生 Runtime 应用打包没有完成。请确认 Python 3、pygame-ce 和 PyInstaller 已安装。"',
            '  echo "可手动执行：python3 build_native_runtime_app.py --mode onedir ."',
            '  echo ""',
            '  read -r -p "按回车关闭..." _',
            "  exit 1",
            "}",
            'echo ""',
            'echo "打包完成，输出目录：native_app_dist/"',
            'echo "同时会生成 native_app_package_manifest.json 和平台 Preview zip。"',
            'read -r -p "按回车关闭..." _',
            "",
        ],
    )
    _write_posix_script(
        paths["linux_app_builder"],
        _script_preamble()
        + [
            f"python3 -m pip install -r {requirements_name} -r {build_requirements_name}",
            "python3 build_native_runtime_app.py --mode onedir .",
            "",
        ],
    )
    _write_windows_script(
        paths["windows_app_builder"],
        [
            "@echo off",
            "cd /d %~dp0",
            f"python -m pip install -r {requirements_name} -r {build_requirements_name}",
            "python build_native_runtime_app.py --mode onedir .",
            "if errorlevel 1 (",
            "  echo.",
            "  echo 原生 Runtime 应用打包没有完成，请确认 Python 3、pygame-ce 和 PyInstaller 已安装。",
            "  echo 可手动执行：python build_native_runtime_app.py --mode onedir .",
            "  pause",
            "  exit /b 1",
            ")",
            "echo.",
            "echo 打包完成，输出目录：native_app_dist\\",
            "echo 同时会生成 native_app_package_manifest.json 和平台 Preview zip。",
            "pause",
            "",
        ],
    )
