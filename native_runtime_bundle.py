from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path, PurePosixPath


def build_native_runtime_required_module_files(
    template_dir: Path,
    module_names: Iterable[str],
) -> tuple[tuple[Path, str], ...]:
    """Build a validated source/name registry for exported native modules."""
    root = Path(template_dir)
    result: list[tuple[Path, str]] = []
    seen: set[str] = set()
    for value in module_names:
        name = str(value or "").strip()
        pure_name = PurePosixPath(name)
        if not name or "/" in name or "\\" in name or pure_name.name != name or not name.endswith(".py"):
            raise ValueError(f"Invalid native Runtime module name: {value!r}")
        if name in seen:
            raise ValueError(f"Duplicate native Runtime module name: {name}")
        seen.add(name)
        result.append((root / name, name))
    return tuple(result)
