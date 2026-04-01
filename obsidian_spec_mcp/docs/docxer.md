# Docxer Spec Pack

Sources
- Docxer GitHub: https://github.com/Developer-Mike/obsidian-docxer

Purpose
- Model the workflow for converting `.docx` files into markdown inside Obsidian, and validate that conversion notes track both source and output.

## Overview

Docxer is a workflow-oriented plugin rather than a standalone markdown grammar. It converts Microsoft Word `.docx` files into Obsidian-compatible markdown. The validator checks that notes referencing `.docx` files also mention a `.md` output to ensure the conversion workflow is complete.

## Conversion Workflow

Steps
1. Add a `.docx` file to the vault (e.g. `imports/report.docx`).
2. Open the file in Obsidian — Docxer intercepts the open action.
3. Convert it to markdown — produces a `.md` note in the vault.
4. Review and clean up the generated markdown.

Rules
- Notes that reference a `.docx` file should also reference the `.md` output note.
- A `.docx` reference without a corresponding `.md` reference triggers an info-level notice.
- Post-conversion, the generated markdown should be linter-friendly (proper headings, spacing, frontmatter).

## Runtime Configuration

The `docxer_defaults` profile setting can specify:
- `source_docx` — Default source path pattern (e.g. `imports/document.docx`).
- `output_note` — Default output path pattern (e.g. `converted/document.md`).

When configured, generated snippets use these defaults instead of generic placeholders.

## Generated Snippet Example

```
# Q2 Report Import

Source file: imports/q2_report.docx
Output note: converted/q2_report.md

1. Add the .docx file to the vault.
2. Open the file in Obsidian.
3. Convert it to markdown with Docxer.

## Post-conversion Cleanup
- Review headings for correct hierarchy
- Fix any broken image references
- Normalize list formatting
- Add frontmatter properties
```

## Post-conversion Checklist

- Verify heading hierarchy (H1, H2, etc.) matches the original document structure.
- Replace any broken image references with vault-relative paths.
- Normalize list formatting (consistent markers, indentation).
- Add YAML frontmatter with title, tags, and source reference.
- Run Linter to clean up spacing and formatting.

Edge cases
- `.docx` files with complex tables may produce malformed markdown tables.
- Embedded images are extracted to the vault but paths may need adjustment.
- Footnotes and endnotes may not convert perfectly.

## Cross-pack notes
- Post-conversion notes should pass Linter validation (single H1, clean spacing, frontmatter).
- Add Core properties (frontmatter) to converted notes for vault consistency.
- If the converted document contains task-like content, consider adding Tasks syntax.
