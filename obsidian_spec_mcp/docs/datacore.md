# Datacore Spec Pack

Sources
- Datacore GitHub: https://github.com/blacksmithgu/obsidian-datacore
- Datacore is currently experimental and in active development.

Purpose
- Validate and generate Datacore reactive component blocks for live-updating data views.

## Datacore Blocks

Rules
- Datacore uses fenced code blocks with language `datacore`.
- Declarative YAML-like syntax with view definitions.
- Views are reactive and update automatically when underlying data changes.
- Component structure defines view type, data source, and rendering options.

View types
- `view: table` — tabular display of data.
- `view: list` — simple list view.
- `view: card` — card-based grid layout.
- `view: calendar` — calendar view for date-based data.

Core fields
- `from` — data source (similar to Dataview: `#tag`, `"folder"`, `[[link]]`).
- `where` — filter conditions on fields.
- `select` — fields to display (column names or expressions).
- `group` — grouping key for aggregation.
- `sort` — sort order specification.

Examples
```datacore
view: table
from: #project
select:
  - name: file.link
  - status
  - due_date
where: status != "completed"
sort: due_date ASC
```

```datacore
view: list
from: #task
where: priority == "high"
group: file.folder
```

```datacore
view: calendar
from: #meeting
select: date
where: date >= today
```

Edge cases
- Datacore syntax is evolving; refer to latest GitHub documentation.
- Invalid view types fall back to default table view.
- Missing `from` clause may error rather than defaulting to all files.

## Reactivity

Rules
- Datacore views update automatically when source data changes.
- Frontmatter edits trigger view refresh.
- File moves/renames update references automatically.
- Component state persists across Obsidian restarts.

Performance notes
- Large vaults may experience brief delays on initial load.
- Consider `limit` clause for expensive queries.
- Views cache results intelligently to minimize recomputation.

## Comparison with Dataview

Migration notes
- Datacore is intended as a successor to Dataview with improved reactivity.
- Syntax is similar but not identical; some Dataview queries need adaptation.
- DataviewJS functionality may be replaced by future Datacore scripting features.
- Both plugins can coexist; migrate views incrementally.

Feature parity gaps
- Datacore does not yet support all DataviewJS APIs.
- Inline queries (`` `= expr` ``) may use different syntax in Datacore.
- Task-specific features may differ from Dataview task queries.

## Configuration

Runtime profile fields
- `datacore_components` — list of registered custom component names.

Cross-pack notes
- Datacore can query notes using Tasks plugin metadata if indexed.
- Meta Bind fields are accessible as frontmatter properties.
- Templater-created notes are picked up by Datacore after creation.

## Development Status

Warning
- Datacore is experimental and subject to breaking changes.
- API and syntax may change between releases.
- Not recommended for critical production workflows yet.
- Monitor GitHub releases for updates and migration guides.

Validator notes
- Datacore validation is conservative due to evolving syntax.
- Focus on structural validation (valid YAML, required fields present).
- Semantic validation (valid field names) is limited.
