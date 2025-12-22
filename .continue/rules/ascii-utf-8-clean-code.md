---
globs: '["**/*.py", "**/*.md", "**/*.yaml", "**/*.yml", "**/*.json", "**/*.toml"]'
regex: |-
  [\x00-\x1F\x7F]   # control characters
  |[\x80-\uFFFF]    # any code point above U+007F (non‑ASCII)
description: Ensures that all files that are intended for cross‑platform
  consumption avoid characters that can be mishandled by terminals, logs, or
  version‑control diffs. This rule applies to source code, configuration, and
  documentation files.
alwaysApply: true
---

Do not include non‑printable or non‑UTF‑8 characters (such as emoji, control codes, or any characters outside the printable ASCII range U+0020–U+007E) in source code, comments, docstrings, configuration files, or any documentation that will be consumed by external systems. If a character is required for technical reasons (e.g., a Unicode identifier), it must be explicitly escaped or documented, but the default stance is to stay within standard printable UTF‑8 (space through tilde).
