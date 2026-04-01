# Obsidian Core Spec Pack

Sources
- Obsidian Help: https://obsidian.md/help/Home

Purpose
- Provide a compact authoring reference for core Obsidian markdown semantics.

Rules
- Prefer `[[Wikilinks]]` for vault-internal links.
- Use `![[Note]]` or `![[Note#Heading]]` for embeds and transclusion.
- Use callouts with blockquote syntax, for example `> [!info]`.
- Store structured metadata in Properties or YAML frontmatter when your vault profile prefers it.

Examples
- `[[Project Note]]`
- `![[Reference Note#Open Questions]]`
- `> [!warning] Migration risk`
