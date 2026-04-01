---
title: Broken Template
tags:
  - test
  - templater-broken
---

# Broken Template

## Unbalanced tags

This has an opening tag with no closing: <% tp.file.title

And another one: <%* const x = 1

## Unknown user script reference

<% tp.user.unknownHelper() %>
<% tp.user.anotherMissing("arg") %>
