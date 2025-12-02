# Collections module for ResSimPlotter
# Contains container/grouping classes that manage components

from .operation import Operation
# Note: System not imported here to avoid circular imports with components

__all__ = ['Operation']