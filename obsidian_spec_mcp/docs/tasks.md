# Tasks Spec Pack

Sources
- Tasks User Guide: https://publish.obsidian.md/tasks/Introduction
- Tasks Getting Started: https://publish.obsidian.md/tasks/Getting%2BStarted/Getting%2BStarted

Purpose
- Validate and generate markdown checklist lines and fenced `tasks` query blocks.

Rules
- A Tasks item starts as a markdown checklist entry, for example `- [ ] Draft proposal`.
- Date and priority fields are commonly represented with emoji markers, for example `📅 2026-04-05` and `⏫`.
- Recurrence uses the recurrence marker followed by an `every ...` phrase.
- Query blocks must be fenced code blocks with language `tasks`.

Examples
- `- [ ] Draft proposal ⏫ 📅 2026-04-05`
- ```tasks
  not done
  due before tomorrow
  sort by due
  ```
