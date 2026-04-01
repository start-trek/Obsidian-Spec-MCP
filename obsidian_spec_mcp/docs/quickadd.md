# QuickAdd Spec Pack

Sources
- QuickAdd Docs: https://quickadd.obsidian.guide/docs/
- QuickAdd VALUE docs: https://publish.obsidian.md/quickadd/VALUE
- Format Syntax: https://quickadd.obsidian.guide/docs/FormatSyntax
- Choices: https://quickadd.obsidian.guide/docs/Choices/

Purpose
- Capture the formatting tokens and choice-oriented authoring patterns used by the QuickAdd plugin for rapid note creation, capture, and macro execution.

## Format Placeholders

Rules
- QuickAdd format tokens use double-brace syntax: `{{TOKEN}}`.
- All opening `{{` must have a matching closing `}}`. Unbalanced braces are an error.
- Placeholders are case-sensitive for built-in tokens.

Built-in tokens
- `{{DATE}}` — Current date (uses the format from QuickAdd settings).
- `{{DATE:format}}` — Current date with explicit format, e.g. `{{DATE:YYYY-MM-DD}}`.
- `{{TIME}}` — Current time.
- `{{TITLE}}` — Title of the note being created.
- `{{NAME}}` — Same as TITLE in most contexts.
- `{{VALUE}}` — Prompts the user for a value at capture time.
- `{{VALUE:variableName}}` — Prompts for a named variable.
- `{{SELECTED}}` — Currently selected text in the editor.
- `{{CLIPBOARD}}` — Contents of the system clipboard.

Examples
- `{{DATE:YYYY-MM-DD}}`
- `{{VALUE:project}}`
- `{{VALUE:attendees}}`
- `{{CLIPBOARD}}`

## Variables

Rules
- Named variables use `{{VALUE:name}}` syntax.
- When `quickadd_known_variables` is configured in the profile, referencing an unknown variable triggers an info-level notice.
- Variable names should be descriptive and consistent across templates.

Edge cases
- `{{VALUE:project` (missing `}}`) is an error — unbalanced braces.
- `{{UNKNOWN_TOKEN}}` is not a built-in but may be a macro variable.

## Choices

Types
- **Capture** — Append or prepend text to a note using format syntax.
- **Template** — Create a new note from a template.
- **Macro** — Run a sequence of commands.
- **Multi** — Present a menu of sub-choices.

Rules
- When `quickadd_choice_names` is configured, generated snippets should reference known choices.
- Choice names are user-defined and should match the vault's QuickAdd configuration.

## Full Capture Example

```
# {{VALUE:project}} — Meeting Notes

Date: {{DATE:YYYY-MM-DD}}
Attendees: {{VALUE:attendees}}

## Agenda
{{VALUE:agenda}}

## Action Items
- [ ] {{VALUE:action_item}} — assigned to {{VALUE:assignee}}

## Notes
{{VALUE:notes}}
```

## Cross-pack notes
- QuickAdd templates often generate notes that should pass Linter validation.
- Captured notes can contain Tasks syntax: `- [ ] {{VALUE:task}} 📅 {{DATE:YYYY-MM-DD}}`.
- QuickAdd templates can include Templater commands if both plugins are active, but avoid mixing `{{VALUE:x}}` with `<% tp.system.prompt("x") %>` for the same variable.
