---
globs: '["**/*.py"]'
description: Provides a precise, enforceable standard for Python documentation
  so there is no ambiguity about what must be included when exposing functions,
  classes, or scripts for external use.
alwaysApply: true
---

When creating a function, class, or module in Python, you must add a comprehensive docstring that includes:
• A brief summary of what the API does.
• Detailed description of parameters (including type hints).
• Description of return values (or effects) and any raised exceptions.
• A short usage example shown either in the docstring or in an accompanying `examples/` file.
• Any helper utilities (e.g., wrapper functions, validation helpers) that are required for external callers to successfully invoke the API.
• Clear indication of the public API surface (e.g., mark private helpers with a leading underscore and do not document them as part of the public API).

This rule applies to all newly created or modified Python files (`globs: ["**/*.py"]`) and ensures that any function, class, or script can be called from other modules or external code with full, self‑contained documentation.
