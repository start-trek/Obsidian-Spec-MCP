# JS Engine Spec Pack

Sources
- JS Engine Docs: https://www.moritzjung.dev/obsidian-js-engine-plugin-docs/
- JS Engine GitHub: https://github.com/mProjectsCode/obsidian-js-engine-plugin

Purpose
- Describe executable `js-engine` blocks for dynamic rendering inside notes.

Rules
- JS Engine code belongs in fenced code blocks with language `js-engine`.
- The block should return a renderable value.
- Keep code examples minimal unless the user explicitly asks for plugin-side logic.

Examples
- ```js-engine
  return engine.markdown.create('*test*');
  ```
