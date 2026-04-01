# Meta Bind Spec Pack

Sources
- Meta Bind Docs: https://www.moritzjung.dev/obsidian-meta-bind-plugin-docs/
- Meta Bind Input Fields: https://www.moritzjung.dev/obsidian-meta-bind-plugin-docs/guides/inputfields/
- Meta Bind View Fields: https://www.moritzjung.dev/obsidian-meta-bind-plugin-docs/guides/viewfields/
- Meta Bind Buttons: https://www.moritzjung.dev/obsidian-meta-bind-plugin-docs/guides/buttons/

Purpose
- Model interactive input fields, view fields, and buttons that bind to note metadata (frontmatter properties), enabling live-editing forms directly inside notes.

## Input Fields (INPUT)

Rules
- Inline syntax: `INPUT[fieldType:propertyName]`.
- The field type determines the widget rendered (toggle, text, slider, select, date, etc.).
- The property name must match a frontmatter property in the same note.
- When `meta_bind_field_types` is configured in the profile, using an unconfigured type triggers an info notice.

Built-in field types
- `toggle` — Boolean checkbox bound to a property.
- `text` — Single-line text input.
- `textarea` — Multi-line text input.
- `slider` — Numeric slider.
- `select` — Dropdown selection.
- `date` — Date picker.
- `date_picker` — Alternative date picker.
- `number` — Numeric input.
- `suggester` — Autocomplete suggester.
- `editor` — Rich text editor.
- `list` — List/array editor.
- `imageSuggester` — Image selection from vault.

Examples
- `INPUT[toggle:done]` — Toggle bound to `done` property.
- `INPUT[text:title]` — Text input bound to `title`.
- `INPUT[slider(minValue(0), maxValue(10)):rating]` — Slider with constraints.
- `INPUT[select(option(low), option(medium), option(high)):priority]` — Select dropdown.

## View Fields (VIEW)

Rules
- Inline syntax: `VIEW[propertyName]`.
- Displays the current value of a frontmatter property as read-only text.
- Supports JavaScript expressions: `VIEW[{done} ? "Complete" : "Pending"]`.

Examples
- `VIEW[title]` — Display the title property.
- `VIEW[{rating} * 10]` — Computed view.

## Buttons (BUTTON)

Rules
- Inline syntax: `BUTTON[buttonId]`.
- Buttons are defined in meta-bind code blocks with actions.
- Actions include: command, open, js, input, sleep, templaterCreateNote.

## Block Syntax

Rules
- Fenced code blocks with language `meta-bind` can contain multiple declarations.
- Each line in the block is an INPUT, VIEW, or BUTTON declaration.

Example
````
```meta-bind
INPUT[text:title]
INPUT[toggle:done]
INPUT[slider(minValue(0), maxValue(5)):rating]
```
````

Edge cases
- `INPUT[` without closing `]` is malformed syntax.
- Field types not in the configured `meta_bind_field_types` list trigger an info notice, not an error.
- Properties referenced by INPUT fields should exist in the note's frontmatter.

## Cross-pack notes
- Meta Bind fields read/write frontmatter properties, so notes should follow Core properties rules.
- Linter may reformat frontmatter that Meta Bind modifies — ensure compatible settings.
- Meta Bind forms work well alongside Tasks for interactive task management dashboards.
