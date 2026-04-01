---
title: Valid JS Engine Note
tags:
  - test
  - js-engine
---

# Valid JS Engine Note

## Basic Block

```js-engine
return engine.markdown.create('*Hello from JS Engine*');
```

## Multi-line Block

```js-engine
const today = new Date().toISOString().slice(0, 10);
const greeting = `Today is ${today}`;
return engine.markdown.create(greeting);
```
