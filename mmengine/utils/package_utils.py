# Copyright (c) OpenMMLab. All rights reserved.
import importlib.metadata
import importlib.util
import os.path as osp
import re
import subprocess


def _normalize_package_name(name: str) -> str:
    """Normalize package name per PEP 503."""
    return re.sub(r'[-_.]+', '_', name).lower()


def is_installed(package: str) -> bool:
    """Check package whether installed.

    Args:
        package (str): Name of package to be checked.
    """
    try:
        importlib.metadata.distribution(package)
        return True
    except importlib.metadata.PackageNotFoundError:
        spec = importlib.util.find_spec(package)
        if spec is None:
            return False
        elif spec.origin is not None:
            return True
        else:
            return False


def get_installed_path(package: str) -> str:
    """Get installed path of package.

    Args:
        package (str): Name of package.

    Example:
        >>> get_installed_path('mmcls')
        >>> '.../lib/python3.7/site-packages/mmcls'
    """
    try:
        dist = importlib.metadata.distribution(package)
    except importlib.metadata.PackageNotFoundError as e:
        # If the package is not installed, a path set in PYTHONPATH
        # can still be detected by `find_spec`.
        spec = importlib.util.find_spec(package)
        if spec is not None:
            if spec.origin is not None:
                return osp.dirname(spec.origin)
            else:
                raise RuntimeError(
                    f'{package} is a namespace package, which is invalid '
                    'for `get_installed_path`')
        else:
            raise e

    # locate_file('') returns the site-packages root as a Path
    location = dist.locate_file('')

    # Try the package name as-is, then normalized, then inferred from metadata
    for candidate in (package, _normalize_package_name(package)):
        possible_path = location / candidate
        if possible_path.exists():
            return str(possible_path)

    return str(location / package2module(package))


def package2module(package: str) -> str:
    """Infer module name from package.

    Args:
        package (str): Package to infer module name.
    """
    dist = importlib.metadata.distribution(package)

    # Try legacy top_level.txt first (setuptools-generated)
    top_level = dist.read_text('top_level.txt')
    if top_level and top_level.strip():
        return top_level.split('\n')[0]

    # Fall back to inferring from RECORD entries (PEP 627)
    files = dist.files
    if files:
        candidates = {
            f.parts[0]
            for f in files
            if len(f.parts) > 1
            and not f.parts[0].endswith(('.dist-info', '.data'))
        }
        if len(candidates) == 1:
            return next(iter(candidates)).removesuffix('.py')

    raise ValueError(f'cannot infer the module name of {package}')


def call_command(cmd: list) -> None:
    try:
        subprocess.check_call(cmd)
    except Exception as e:
        raise e  # type: ignore


def install_package(package: str) -> None:
    if not is_installed(package):
        call_command(['python', '-m', 'pip', 'install', package])
