"""agent-lint -- Estimate costs and lint agent workflow YAML files."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("agentlinter")
except PackageNotFoundError:  # pragma: no cover - source tree without an installed package
    __version__ = "0+unknown"

__all__ = ["__version__"]
