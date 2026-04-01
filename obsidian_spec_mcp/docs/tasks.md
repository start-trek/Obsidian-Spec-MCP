# Tasks Spec Pack

Sources
- Tasks User Guide: https://publish.obsidian.md/tasks/Introduction
- Tasks Getting Started: https://publish.obsidian.md/tasks/Getting%2BStarted/Getting%2BStarted
- Dates: https://publish.obsidian.md/tasks/Getting%2BStarted/Dates
- Statuses: https://publish.obsidian.md/tasks/Getting%2BStarted/Statuses
- Recurring Tasks: https://publish.obsidian.md/tasks/Getting%2BStarted/Recurring%2BTasks
- Queries: https://publish.obsidian.md/tasks/Queries/About%2BQueries

Purpose
- Validate and generate markdown checklist lines and fenced `tasks` query blocks compatible with the Obsidian Tasks plugin.

## Task Lines

Rules
- A Tasks item **must** start as a markdown checklist entry: `- [ ] Description`.
- The checkbox status character determines the task state (e.g. ` ` = todo, `x` = done).
- Custom statuses can be configured via runtime config (e.g. `/` = in-progress, `-` = cancelled).
- Task metadata (priority, dates, recurrence) follows the description on the same line.
- Tasks emoji markers are placed after the description text, before any tags.

Status symbols
- `- [ ]` — Todo (default)
- `- [x]` — Done (default)
- `- [/]` — In Progress (custom, must be configured)
- `- [-]` — Cancelled (custom, must be configured)

## Priority

Rules
- Priority is indicated by emoji markers on the task line.
- `⏫` — Highest priority
- `🔼` — High priority
- `🔽` — Low priority
- `⏬` — Lowest priority
- Only one priority marker per task line.

## Dates

Rules
- Dates use emoji markers followed by `YYYY-MM-DD` format.
- `📅 2026-04-05` — Due date
- `⏳ 2026-04-03` — Scheduled date
- `� 2026-04-01` — Start date
- `✅ 2026-04-05` — Done date (set when task is completed)
- `➕ 2026-04-01` — Created date
- Date priority order is configurable via `tasks_date_priority` in the profile.

## Recurrence

Rules
- Recurrence uses the `🔁` marker followed by `every ...` phrase.
- The word `every` is required after the marker.
- Common patterns: `every day`, `every week`, `every month`, `every year`.
- Advanced: `every weekday`, `every 2 weeks`, `every month on the 15th`.

Examples
- `- [ ] Weekly standup 🔁 every week 📅 2026-04-07`
- `- [ ] Monthly review 🔁 every month on the 1st 📅 2026-05-01`

Edge cases
- `🔁 weekly` is invalid — must include `every` (e.g. `🔁 every week`).
- `🔁 monthly on the 1st` is invalid — must include `every`.

## Global Filter

Rules
- When `tasks_global_filter` is set (e.g. `#task`), task lines should include that tag.
- When `tasks_append_global_filter_to_queries` is true, query blocks should also include the filter.
- The global filter helps Tasks distinguish task-managed lines from regular checklists.

## Query Blocks

Rules
- Query blocks use fenced code blocks with language `tasks`.
- Each line in the block is a filter, sort, group, or limit instruction.
- Common filters: `not done`, `done`, `due before YYYY-MM-DD`, `path includes folder`.
- Common sorts: `sort by due`, `sort by priority`, `sort by done reverse`.
- Common groups: `group by folder`, `group by status`.
- An empty query block is a warning (likely a mistake).
- Unclosed query blocks (missing closing ```) are errors.

Examples
```
- [ ] Draft proposal ⏫ 📅 2026-04-05
- [x] Ship v1.0 ✅ 2026-04-01
- [ ] Weekly standup 🔁 every week 📅 2026-04-07
```

````
```tasks
not done
due before 2026-05-01
sort by due
group by folder
```
````

## Cross-pack notes
- Task lines must survive Linter rules (single H1, blank line normalization).
- Tasks inside callouts are valid: `> - [ ] Task inside callout`.
- Wikilinks in task descriptions are valid: `- [ ] Review [[Design Doc]] ⏫`.
