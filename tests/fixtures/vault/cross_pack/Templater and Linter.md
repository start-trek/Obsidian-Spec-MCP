---
created: <% tp.file.creation_date("YYYY-MM-DD") %>
title: Templater and Linter Cross-Pack Test
tags:
  - test
  - cross-pack
---

# <% tp.file.title %>

<%* const today = tp.date.now("YYYY-MM-DD") %>

## Summary

Created on: <% today %>

This template should pass both Templater and Linter validation:
- Balanced Templater tags
- Single H1
- Clean spacing
- Proper frontmatter
