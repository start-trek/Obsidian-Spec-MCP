# Dataview Spec Pack

Sources
- Dataview Documentation: https://blacksmithgu.github.io/obsidian-dataview/
- Dataview GitHub: https://github.com/blacksmithgu/obsidian-dataview
- Query Language: https://blacksmithgu.github.io/obsidian-dataview/queries/structure/
- DataviewJS: https://blacksmithgu.github.io/obsidian-dataview/api/intro/
- Inline Queries: https://blacksmithgu.github.io/obsidian-dataview/queries/dql-embeds/

Purpose
- Validate and generate Dataview query blocks, DataviewJS code blocks, and inline Dataview expressions for dynamic vault views.

## Dataview Query Blocks

Rules
- Dataview queries use fenced code blocks with language `dataview`.
- Query structure: `QUERY_TYPE` (LIST, TABLE, TASK, CALENDAR) followed by `FROM` and optional `WHERE` clauses.
- `FROM` sources: `#tag`, `"folder"`, `[[link]]`, or combinations.
- `WHERE` conditions filter results based on file metadata or frontmatter fields.
- Sorting: `SORT field ASC/DESC` at the end of the query.
- Grouping: `GROUP BY field` to group results.
- Limiting: `LIMIT n` to restrict result count.

Query types
- `LIST` — simple list of matching files or values.
- `TABLE field1, field2` — table with specified columns.
- `TASK` — task-specific query that understands task metadata.
- `CALENDAR date_field` — calendar view by date.

Examples
```dataview
LIST FROM #project
WHERE completed = false
SORT file.name ASC
```

```dataview
TABLE file.name, due_date, priority
FROM #task
WHERE due_date >= date(today)
SORT priority DESC
```

```dataview
TASK
FROM #project
WHERE !completed
GROUP BY file.folder
```

Edge cases
- Missing `FROM` clause defaults to all files (can be slow in large vaults).
- Invalid field names in `TABLE` or `WHERE` return empty results (not errors).
- Date comparisons require `date()` wrapper: `WHERE due_date > date(today)`.

## DataviewJS Blocks

Rules
- DataviewJS uses fenced code blocks with language `dataviewjs`.
- JavaScript code executes with `dv` object providing Dataview API.
- Common patterns: `dv.pages()`, `dv.table()`, `dv.list()`, `dv.taskList()`.
- Access file metadata via `page.file.name`, `page.frontmatter.field`, etc.

API reference
- `dv.pages(source)` — get all pages matching source pattern.
- `dv.table(headers, rows)` — render table with given headers and data.
- `dv.list(items)` — render bulleted list.
- `dv.taskList(tasks, groupByFile)` — render task list.
- `dv.current()` — get metadata of current file.

Examples
```dataviewjs
dv.table(
  ["File", "Modified", "Tags"],
  dv.pages("#project").map(p => [
    p.file.link,
    p.file.mtime,
    p.file.tags
  ])
)
```

```dataviewjs
const tasks = dv.pages("#task")
  .where(p => !p.completed)
  .map(p => p.file.tasks)
  .flat();
dv.taskList(tasks);
```

Edge cases
- JavaScript errors in DataviewJS blocks fail silently in preview (check console).
- `dv.pages()` without arguments queries all files — expensive in large vaults.
- Missing closing fence or syntax errors break block rendering.

## Inline Dataview

Rules
- Inline queries use backtick-equals syntax: `` `= expression` ``.
- Evaluated in real-time when viewing the note.
- Can reference `this` for current file metadata.
- Useful for dynamic values: current date, file properties, calculations.

Examples
- `` `= this.title` `` — current file's title from frontmatter.
- `` `= date(today)` `` — today's date.
- `` `= this.file.mtime` `` — last modified time.
- `` `= this.file.tasks.length` `` — count of tasks in current file.

Edge cases
- Inline queries in code blocks or callouts may not render.
- Invalid expressions show literal backtick text, not errors.
- Recursive inline queries (query referencing itself) can cause issues.

## Metadata Fields

Rules
- Dataview automatically indexes file metadata: `file.name`, `file.path`, `file.size`, `file.ctime`, `file.mtime`, `file.tags`, `file.etags`, `file.outlinks`, `file.inlinks`.
- Frontmatter fields become accessible: `field_name` or `this.field_name`.
- Field names are case-insensitive.

Common field types
- Text: compared directly or with `contains()`.
- Dates: use `date()` wrapper for comparisons.
- Lists: use `contains(list, value)` for membership checks.
- Links: compare with `[[link]]` syntax or `contains()`.

## Configuration

Runtime profile fields
- `dataview_views` — list of saved view names for validation.
- `dataview_custom_prefix` — custom prefix for inline queries (rarely changed).

Cross-pack notes
- Dataview queries work well with Tasks plugin for task-specific views.
- Task metadata (priority, dates) from Tasks is accessible in Dataview.
- DataviewJS can access helper scripts defined in JS Engine config.
