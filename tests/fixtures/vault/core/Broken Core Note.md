This note has no frontmatter but uses property-like keys.

tags: should-be-in-frontmatter
aliases: broken-example

Some text with a possible callout marker [!info] but not in blockquote syntax.

Here is an internal link using markdown syntax instead of wikilinks:
[My Note](My%20Note.md)
[Another](Another.md)

This should trigger core validation warnings about:
1. Properties outside frontmatter
2. Broken callout marker
3. Markdown links when wikilinks are preferred
