---
title: Broken JS Engine Note
tags:
  - test
  - js-engine-broken
---

# Broken JS Engine Note

## Unclosed block

```js-engine
return engine.markdown.create('*This block is never closed*');
