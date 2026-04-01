# Linter Spec Pack

Sources
- Linter Docs: https://platers.github.io/obsidian-linter/
- Linter GitHub: https://github.com/platers/obsidian-linter
- Linter Rules Reference: https://platers.github.io/obsidian-linter/settings/

Purpose
- Express style rules that help generated notes survive local Obsidian Linter runs. Linter is configuration-driven, so vault-local policy always takes precedence over generic markdown preferences.

## Heading Rules

single_h1
- When `single_h1` is true (default), the note should have exactly one `# H1` heading.
- Multiple H1 headings trigger a warning.
- When `single_h1` is false, multiple H1 headings are allowed.

Rules
- Heading levels should be sequential (no skipping from H1 to H3).
- Headings should have a blank line before and after them.
- Heading style should be consistent (ATX `#` style preferred).

## Blank Line Rules

collapse_extra_blank_lines
- When true (default), consecutive blank lines are collapsed to a single blank line.
- Three or more consecutive blank lines trigger an info notice.
- Files should not end with multiple trailing blank lines.

Rules
- One blank line between paragraphs.
- One blank line before and after headings, code blocks, and lists.
- No trailing whitespace on lines.

## Frontmatter Rules

prefer_yaml_frontmatter
- When true (default), metadata should be in YAML frontmatter at the top of the file.
- Inline metadata (e.g. `tags: value` in body text) triggers a warning.
- Frontmatter should be consistently formatted (consistent indentation, no trailing spaces).

Rules
- Frontmatter is delimited by `---` at the start and end.
- YAML keys should use lowercase with hyphens or underscores.
- List values should use array syntax (not comma-separated strings).

## List Rules

Rules
- List markers should be consistent within a list (all `-` or all `*` or all `1.`).
- Nested lists should use consistent indentation.
- Blank lines between list items are optional but should be consistent.

## Other Common Rules

- **Trailing spaces**: No trailing whitespace on any line.
- **Final newline**: Files should end with exactly one newline character.
- **Consecutive headings**: Avoid two headings with no content between them.
- **Empty lines around code blocks**: One blank line before and after fenced code blocks.

## Runtime Configuration

The `linter_expectations` profile setting controls which rules are active:

```json
{
  "single_h1": true,
  "collapse_extra_blank_lines": true,
  "prefer_yaml_frontmatter": true
}
```

When loaded from the vault's actual Linter config, these settings are extracted from the plugin's `data.json` file to match the user's real linting rules.

## Examples

Clean note (passes all rules)
```
---
title: Clean Note
tags:
  - example
---

# Clean Note

## Section One

Content here.

## Section Two

More content here.
```

Dirty note (multiple violations)
```
# First H1

# Second H1



Triple blank lines above.

tags: inline-metadata
```

## Cross-pack notes
- All generated notes from any pack should survive Linter rules.
- Tasks lines, Templater output, QuickAdd captures, and Meta Bind forms should all produce Linter-compliant notes.
- When generating multi-pack content, always validate against Linter as one of the selected packs.
- Fenced code blocks (Tasks queries, JS Engine, meta-bind) are exempt from most Linter content rules but their surrounding context must be clean.
