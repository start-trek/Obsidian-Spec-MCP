# Linter Spec Pack

Sources
- Linter Docs: https://platers.github.io/obsidian-linter/
- Linter GitHub: https://github.com/platers/obsidian-linter

Purpose
- Express style rules that help generated notes survive local linting.

Rules
- Assume one top-level heading unless the local linter profile says otherwise.
- Keep frontmatter consistently formatted.
- Normalize blank lines and list spacing.
- Treat Linter as configuration-driven, so vault-local policy wins over generic markdown preferences.

Examples
- Single H1 at the top.
- No triple blank lines.
