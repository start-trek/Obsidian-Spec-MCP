# Templater Spec Pack

Sources
- Templater Introduction: https://silentvoid13.github.io/Templater/introduction.html
- Templater Commands: https://silentvoid13.github.io/Templater/commands/overview.html

Purpose
- Generate Templater-aware note templates.

Rules
- Interpolation commands use `<% ... %>`.
- JavaScript execution commands use `<%* ... %>`.
- Keep opening and closing tags balanced.
- Use `tp.*` helpers only where they make the template clearer.

Examples
- `<% tp.file.title %>`
- `<%* const today = tp.date.now("YYYY-MM-DD") %>`
