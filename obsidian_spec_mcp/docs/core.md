# Obsidian Core Spec Pack

Sources
- Obsidian Help: https://obsidian.md/help/Home
- Format your notes: https://help.obsidian.md/Editing+and+formatting/Basic+formatting+syntax
- Properties: https://help.obsidian.md/Editing+and+formatting/Properties
- Callouts: https://help.obsidian.md/Editing+and+formatting/Callouts
- Linking: https://help.obsidian.md/Linking+notes+and+files/Internal+links

Purpose
- Provide an authoritative authoring reference for core Obsidian markdown semantics including wikilinks, embeds, callouts, properties, and standard formatting.

## Wikilinks

Rules
- Prefer `[[Wikilinks]]` for vault-internal references when the profile's `use_wikilinks` is true.
- Display text: `[[Target Note|display text]]`.
- Link to heading: `[[Note#Heading]]`.
- Link to block: `[[Note#^block-id]]`.
- When `use_wikilinks` is false, use standard markdown links: `[display](Note.md)`.

Examples
- `[[Project Note]]`
- `[[Meeting Notes|today's meeting]]`
- `[[Design Doc#Architecture]]`
- `[[Spec#^summary-block]]`

Edge cases
- Wikilinks with pipe characters in display text must be escaped in tables.
- Aliases defined in frontmatter allow linking via any alias.

## Embeds and Transclusion

Rules
- Embed a full note: `![[Note]]`.
- Embed a heading section: `![[Note#Heading]]`.
- Embed a block: `![[Note#^block-id]]`.
- Embed images: `![[image.png]]` or `![[image.png|400]]` for width.
- Embed PDFs: `![[document.pdf]]` or `![[document.pdf#page=3]]`.

Examples
- `![[Reference Doc]]`
- `![[Design Spec#Open Questions]]`
- `![[photo.jpg|600]]`

## Callouts

Rules
- Callouts use blockquote syntax with a type marker: `> [!type]`.
- Optional custom title: `> [!type] Custom Title`.
- Foldable callouts: `> [!type]+` (expanded) or `> [!type]-` (collapsed).
- Built-in types: `note`, `abstract`, `info`, `tip`, `success`, `question`, `warning`, `failure`, `danger`, `bug`, `example`, `quote`.
- Callout content follows on subsequent blockquote lines.

Examples
- `> [!info] Summary`
- `> [!warning] Migration risk`
- `> [!tip]+ Pro Tip` (foldable, expanded by default)
- `> [!note]-` (foldable, collapsed, no title)

Edge cases
- The `[!type]` marker must be the first line of the blockquote.
- A plain blockquote line like `> [!info]` outside blockquote syntax is invalid.
- Nested callouts are supported: indent with additional `>` characters.

## Properties (YAML Frontmatter)

Rules
- Properties are stored in YAML frontmatter delimited by `---` at the top of the file.
- When `prefer_properties` is true, metadata like tags, aliases, and custom fields should live in frontmatter, not inline.
- Common fields: `title`, `tags`, `aliases`, `cssclass`, `date`, `created`.
- Tags in frontmatter use array syntax without the `#` prefix.

Examples
```yaml
---
title: My Note
tags:
  - project
  - draft
aliases:
  - My Project Note
---
```

Edge cases
- Properties outside of frontmatter (e.g. `tags: value` in body text) trigger a warning when `prefer_properties` is true.
- Frontmatter must be the very first content in the file (no blank lines before `---`).

## Cross-pack notes
- Callout content can contain Tasks checklist items.
- Embeds can reference notes that use any plugin syntax.
- Linter rules (single H1, blank line normalization) apply on top of core formatting.
