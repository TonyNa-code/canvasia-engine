from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_VENV_DIR = ROOT_DIR / ".native_runtime_smoke_venv"
NATIVE_REQUIREMENTS = ROOT_DIR / "native_runtime" / "requirements.txt"
NATIVE_VIDEO_REQUIREMENTS = ROOT_DIR / "native_runtime" / "requirements-video.txt"


def get_venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def run_command(command: list[str], *, env: dict[str, str] | None = None) -> int:
    print("+ " + " ".join(command))
    return subprocess.run(command, cwd=ROOT_DIR, env=env, check=False).returncode


def ensure_venv(venv_dir: Path, *, fresh: bool) -> Path:
    if fresh and venv_dir.exists():
        shutil.rmtree(venv_dir)
    python_path = get_venv_python(venv_dir)
    if not python_path.exists():
        print(f"Creating native runtime smoke venv: {venv_dir}")
        venv.EnvBuilder(with_pip=True, clear=False).create(venv_dir)
    return python_path


def install_requirements(python_path: Path, *, include_video: bool) -> int:
    install_commands = [
        [str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
        [str(python_path), "-m", "pip", "install", "-r", str(NATIVE_REQUIREMENTS)],
    ]
    if include_video:
        install_commands.append([str(python_path), "-m", "pip", "install", "-r", str(NATIVE_VIDEO_REQUIREMENTS)])
    for command in install_commands:
        exit_code = run_command(command)
        if exit_code != 0:
            return exit_code
    return 0


def run_native_smoke(python_path: Path) -> int:
    env = os.environ.copy()
    env.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    env.setdefault("SDL_AUDIODRIVER", "dummy")
    env.setdefault("SDL_VIDEODRIVER", "dummy")
    return run_command(
        [
            str(python_path),
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-p",
            "test_native_runtime*.py",
            "-v",
        ],
        env=env,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run native Runtime render smoke tests in an isolated pygame-ce virtual environment."
    )
    parser.add_argument(
        "--venv",
        type=Path,
        default=DEFAULT_VENV_DIR,
        help="Virtual environment path. Defaults to .native_runtime_smoke_venv in the repo root.",
    )
    parser.add_argument("--fresh", action="store_true", help="Recreate the virtual environment before running.")
    parser.add_argument("--skip-install", action="store_true", help="Use the existing virtual environment as-is.")
    parser.add_argument(
        "--with-video",
        action="store_true",
        help="Also install optional PyAV/OpenCV video requirements before running the smoke suite.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    venv_dir = args.venv.resolve() if args.venv.is_absolute() else (ROOT_DIR / args.venv).resolve()
    python_path = ensure_venv(venv_dir, fresh=args.fresh)
    if not args.skip_install:
        install_exit = install_requirements(python_path, include_video=args.with_video)
        if install_exit != 0:
            return install_exit
    return run_native_smoke(python_path)


if __name__ == "__main__":
    raise SystemExit(main())
