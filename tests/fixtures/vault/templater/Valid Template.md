---
created: <% tp.file.creation_date("YYYY-MM-DD") %>
title: <% tp.file.title %>
tags:
  - test
  - templater
---

# <% tp.file.title %>

<%* const today = tp.date.now("YYYY-MM-DD") %>
<%* const tomorrow = tp.date.now("YYYY-MM-DD", 1) %>

## Dates

- Created: <% tp.file.creation_date("YYYY-MM-DD") %>
- Today: <% today %>
- Tomorrow: <% tomorrow %>

## File Info

- Path: <% tp.file.path() %>
- Folder: <% tp.file.folder() %>

## Cursor Position

Content before cursor
<% tp.file.cursor() %>
Content after cursor
