"""Compatibility wrapper for Strands tool decorator."""

from __future__ import annotations


try:  # pragma: no cover - depends on strands runtime
    from strands import tool as _strands_tool
except ImportError:  # pragma: no cover - used in local tests without strands
    def strands_tool(*decorator_args, **decorator_kwargs):
        if decorator_args and callable(decorator_args[0]) and len(decorator_args) == 1 and not decorator_kwargs:
            return decorator_args[0]

        def decorate(fn):
            return fn

        return decorate
else:  # pragma: no cover
    def strands_tool(*decorator_args, **decorator_kwargs):
        return _strands_tool(*decorator_args, **decorator_kwargs)
