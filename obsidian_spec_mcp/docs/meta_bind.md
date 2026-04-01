# Meta Bind Spec Pack

Sources
- Meta Bind Docs: https://www.moritzjung.dev/obsidian-meta-bind-plugin-docs/
- Meta Bind Input Fields: https://www.moritzjung.dev/obsidian-meta-bind-plugin-docs/guides/inputfields/

Purpose
- Model interactive fields, views, and buttons that bind to note metadata.

Rules
- Inline input fields can use patterns like `INPUT[text:title]`.
- Inline toggles can use patterns like `INPUT[toggle:done]`.
- View fields can use `VIEW[...]`.
- Richer declarations can be placed inside fenced `meta-bind` blocks.

Examples
- `INPUT[toggle:done]`
- `VIEW[title]`
