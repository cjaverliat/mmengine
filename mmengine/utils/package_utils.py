# Copyright (c) OpenMMLab. All rights reserved.
import os.path as osp
import subprocess
from importlib.metadata import PackageNotFoundError, distribution
from typing import Any
import importlib.util
import importlib.metadata
from pathlib import Path

def is_installed(package: str) -> bool:
    """Check package whether installed.

    Args:
        package (str): Name of package to be checked.
    """
    import importlib.util

    # First check if it's an importable module
    spec = importlib.util.find_spec(package)
    if spec is not None and spec.origin is not None:
        return True

    # If not found as module, check if it's a distribution package
    try:
        distribution(package)
        return True
    except PackageNotFoundError:
        return False


def get_installed_path(package: str) -> Path:
    """Return the installed directory of a package.

    Handles cases where the package name differs from the module name
    (e.g. 'mmcv-full' → 'mmcv').

    Raises:
        importlib.metadata.PackageNotFoundError: package not installed
        RuntimeError: package is a namespace package with no concrete location
    """
    # 1. Try importlib.metadata first — works for any installed distribution
    try:
        dist = importlib.metadata.distribution(package)
        module_name = _dist_top_level_module(dist) or package
        location = Path(str(dist.locate_file("")))
        candidate = location / module_name
        if candidate.is_dir():
            return candidate
    except importlib.metadata.PackageNotFoundError:
        pass

    # 2. Fall back to importlib.util for editable installs / oddball layouts
    spec = importlib.util.find_spec(package)
    if spec is None:
        raise importlib.metadata.PackageNotFoundError(
            f"Package {package!r} is not installed"
        )
    if spec.origin is not None:
        return Path(spec.origin).parent
    if spec.submodule_search_locations:
        return Path(next(iter(spec.submodule_search_locations)))
    raise RuntimeError(
        f"{package!r} is a namespace package with no concrete location"
    )


def _dist_top_level_module(dist: importlib.metadata.Distribution) -> str | None:
    """Infer the top-level module name from distribution metadata."""
    top_level = dist.read_text("top_level.txt")
    if top_level:
        first = top_level.strip().splitlines()[0].strip()
        if first:
            return first
    return None


def call_command(cmd: list) -> None:
    try:
        subprocess.check_call(cmd)
    except Exception as e:
        raise e  # type: ignore


def install_package(package: str):
    if not is_installed(package):
        call_command(['python', '-m', 'pip', 'install', package])
