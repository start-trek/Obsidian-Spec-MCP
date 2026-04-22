# Styling & CSS snippets

Per-note styling in Obsidian combines two small primitives: the `cssclasses` frontmatter property and CSS snippets under `<vault>/.obsidian/snippets/*.css`. This pack documents how those two pieces interact, the DOM surfaces Obsidian exposes, and the most common recipes (readable line width overrides, container breakout, variable overrides). Scope is small authored snippets — not full-theme development.

## 1. `cssclasses` frontmatter

`cssclasses` is one of Obsidian's three built-in default properties (alongside `tags` and `aliases`). Its values are applied as HTML classes on the containers that render a note. Use the plural list form:

```yaml
---
cssclasses:
  - wide-page
  - redacted
---
```

The singular form `cssclass:` still works but is **deprecated**. Prefer `cssclasses:` with a YAML list, even for a single value.

Each value in the list becomes a class on **both** rendering containers:

- Reading mode: `.markdown-preview-view.wide-page`
- Live Preview / Edit mode: `.markdown-source-view.mod-cm6.wide-page`

That symmetry is why one snippet can style both surfaces from a single `.wide-page` root selector.

## 2. CSS snippet authoring

Snippets live under the vault:

```
<vault>/.obsidian/snippets/<name>.css
```

Enablement flow:

1. Create the file.
2. **Settings → Appearance → CSS snippets** — each file appears here with a toggle.
3. Toggle it on. Obsidian injects the CSS into the app window.
4. After editing the file, Obsidian usually hot-reloads; if it doesn't, toggle off/on or reload the app (`Ctrl/Cmd + P → "Reload app without saving"`).

Scope the snippet's selectors with a `cssclasses` value when you only want it to affect specific notes. An unscoped snippet applies vault-wide.

## 3. Obsidian's CSS variable taxonomy

Obsidian's developer docs organize CSS variables into categories. When writing a snippet, prefer overriding a documented variable over hacking layout classes directly — variables are the intended extension point.

| Category | Purpose |
|---|---|
| Foundations | Abstracted colors, spacing, typography, radii |
| Components | Buttons, inputs, dropdowns, modals, etc. |
| Editor | File container, block, blockquote, callout, code, embed, headings, link, list, properties, table, tag |
| Plugins | Interface for core plugins (graph, search, backlinks, etc.) |
| Window | App chrome (title bar, sidebars, status bar) |
| Publish | Obsidian Publish site variables |

The Editor / File variables are the ones styling-pack recipes touch most often:

| Variable | Description |
|---|---|
| `--file-line-width` | Width of a line when Readable line length is enabled |
| `--file-folding-offset` | Width of the line offset for fold indicators |
| `--file-margins` | File margins |
| `--file-header-font-size` | File header font size |
| `--file-header-font-weight` | File header font weight |
| `--file-header-border` | File header `border-bottom` |
| `--file-header-justify` | File header text alignment |

See the Dev Docs references at the bottom of this page for the complete list.

## 4. Readable line width

When **Settings → Editor → Readable line length** is enabled, Obsidian adds the modifier class `readable-line-width` to the view containers. The canonical selectors that apply the max-width are:

```css
.markdown-source-view.mod-cm6.readable-line-width .cm-sizer,
.markdown-source-view.mod-cm6.readable-line-width .cm-content,
.markdown-source-view.mod-cm6.readable-line-width .cm-line,
.markdown-preview-view.readable-line-width .markdown-preview-sizer {
  max-width: var(--file-line-width);
  margin-left: auto;
  margin-right: auto;
}
```

### Override via the variable (preferred)

```css
/* Wider than default for a specific note class. */
.wideish {
  --file-line-width: 70rem;
}

/* Or go full width. */
.wide-page {
  --file-line-width: 100%;
}
```

### Minimal theme caveat

Minimal uses its own `--line-width` variable. For theme-agnostic snippets, override both:

```css
.wide-page {
  --file-line-width: 100%;
}
body.minimal-theme.minimal-theme .wide-page {
  --line-width: 100%;
}
```

Minimal also ships built-in helper classes (`wide`, `max`). Don't combine them with a custom `wide-page` class or effects compound.

## 5. Reading mode DOM

```
.markdown-preview-view[.readable-line-width][.wide-page]
  > .markdown-preview-sizer
    > .markdown-preview-section
      > div (per rendered block)
        > .block-language-mermaid         ← mermaid wrapper
        > .callout                         ← callouts
        > table                            ← tables
        > pre > code                       ← code blocks
        > p, h1..h6, ul, ol, blockquote    ← prose
```

## 6. Live Preview DOM (CodeMirror 6)

```
.markdown-source-view.mod-cm6[.readable-line-width][.wide-page]
  > .cm-editor
    > .cm-scroller
      > .cm-sizer
        > .cm-contentContainer
          > .cm-content
            > .cm-preview-code-block.cm-lang-mermaid   ← mermaid embed wrapper
              > .mermaid > svg
            > .cm-embed-block                          ← generic embed wrapper
            > .cm-line                                 ← prose lines
            > .HyperMD-codeblock                       ← code block lines
```

Many selectors that look right in Reading mode miss in Live Preview because Live Preview renders through CodeMirror, not the preview renderer. Always provide both chains when styling in-note content.

## 7. Container breakout

To make a specific child exceed the parent's max-width while staying centered in the viewport, use:

```css
.wide-page .block-language-mermaid,
.wide-page .cm-preview-code-block.cm-lang-mermaid {
  width: calc(100vw - 400px);
  max-width: calc(100vw - 400px);
  position: relative;
  left: 50%;
  transform: translateX(-50%);
}
```

The `400px` buffer accounts for the left and right sidebars on a typical desktop layout. Tune it:

- Larger buffer → more whitespace margin, narrower child.
- Smaller buffer → child reaches closer to the window edges.
- When both sidebars are collapsed, a fixed buffer will look slightly over-margined; that's an accepted trade-off of a pure-CSS, viewport-based approach.

The pattern applies to any wrapper element, not just mermaid: tables, callouts, code blocks, and custom plugin blocks can all be broken out with the same technique.

## 8. Prerequisites

- **Readable line length enabled.** Most per-note width overrides drive `--file-line-width`. If the global setting is off, those classes exist but have no width constraint to override.
- **Snippet enabled.** `cssclasses` adds classes regardless, but nothing happens until a matching snippet is loaded.
- **Class spelling matches.** `cssclasses: [wide-page]` produces `.wide-page`. Case and hyphenation are significant.

## 9. Gotchas

- **Hot-reload misses.** Some snippet edits don't hot-reload; toggle off/on.
- **Plural vs singular.** `cssclass:` (singular string) is deprecated. `cssclasses:` (plural list) is current.
- **Theme variable precedence.** Some themes define `--file-line-width` on `body`, which beats a bare `.wide-page { --file-line-width: 100%; }` specificity-wise. Use `body .wide-page { --file-line-width: 100% !important; }` when a theme shadows the variable.
- **`%` vs `px`/`rem` for line width.** `%` sometimes shifts prose left instead of centering; prefer `rem` or `px` for fixed values, and `100%` only when you want full fill.
- **Minimal helper classes.** `wide`, `max`, and similar are already themed; don't layer custom width overrides on top.
- **Reading vs editing mismatch.** Selector works in one mode but not the other — usually because the selector targets preview classes in Live Preview or CodeMirror classes in Reading mode. Write both.

## 10. References

- [Obsidian Help — CSS snippets](https://help.obsidian.md/Extending+Obsidian/CSS+snippets)
- [Obsidian Help — Properties (cssclasses)](https://help.obsidian.md/Editing+and+formatting/Properties)
- [Developer Docs — CSS variables index](https://docs.obsidian.md/Reference/CSS+variables/CSS+variables)
- [Developer Docs — Editor / File variables](https://docs.obsidian.md/Reference/CSS+variables/Editor/File)
- [Developer Docs — About styling](https://docs.obsidian.md/Themes/App+themes/About+styling+Obsidian)
- [Forum: How to: cssclass and readable line length](https://forum.obsidian.md/t/how-to-cssclass-and-readable-line-length/74901)
- [Forum: Disable readable line length on single note](https://forum.obsidian.md/t/disable-readable-line-length-on-single-note/104655)
- [Forum: Optional full-width note (CSS)](https://forum.obsidian.md/t/optional-full-width-note-css/15444)
