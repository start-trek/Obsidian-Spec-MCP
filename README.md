# Obsidian Spec MCP

A spec-centric MCP server for Obsidian authoring.

This server is designed to complement a write-capable vault MCP such as `mcp-obsidian`.

Use this server when you want the model to:
- look up Obsidian-flavored authoring rules,
- generate syntax-aware snippets,
- validate markdown before writing it to the vault,
- switch between plugin-specific syntax packs,
- tailor generation and validation to your real plugin settings.

Bundled packs:
- Core Obsidian
- Tasks
- Templater
- QuickAdd
- Meta Bind
- JS Engine
- Docxer
- Linter

## Why split spec from vault writes?

A vault MCP is good at file access and patching content.
A spec MCP is good at answering questions like:
- "What syntax should I use here?"
- "Is this valid Tasks markdown for my custom statuses?"
- "Give me a Templater template that also survives my Linter rules."

This server is intentionally read-only and generation-oriented.
Pair it with a separate MCP that can read and write your vault.

## What is included

- MCP resources for pack metadata, bundled docs, and starter profiles
- MCP tools for listing packs, reading docs, searching specs, validating markdown, and generating starter snippets
- MCP prompts for authoring Obsidian markdown, Tasks snippets, and Templater templates
- Built-in normalization for common aliases, including `doxcer` -> `docxer`
- A runtime config layer that can ingest local plugin config files and profile overlays

## Install

We recommend `uv`, in line with the MCP Python SDK docs.

```bash
uv sync
```

## Run over stdio

```bash
uv run obsidian-spec-mcp
```

## Run over streamable HTTP

```bash
uv run python -c "from obsidian_spec_mcp.server import mcp; mcp.run(transport='streamable-http')"
```

## Example tools

- `list_packs`
- `get_pack_info`
- `search_spec`
- `get_doc`
- `get_effective_profile`
- `validate_obsidian_markdown`
- `generate_obsidian_snippet`
- `normalized_pack_name`

## Example resources

- `obsidian://packs/index`
- `obsidian://packs/tasks`
- `obsidian://docs/templater`
- `obsidian://profiles/default`

## Runtime config layer

This version can merge the bundled profile with local plugin config files.
That lets the server validate and generate against your actual vault conventions instead of generic defaults.

Supported runtime inputs:
- profile overlay JSON or YAML
- Tasks config
- Linter config
- QuickAdd config
- Templater config
- Meta Bind config
- JS Engine config
- Docxer config

You can pass paths directly into the tools, or set environment variables:

```bash
export OBS_SPEC_PROFILE_PATH=/path/to/profile_overlay.json
export OBS_SPEC_TASKS_CONFIG_PATH=/path/to/tasks.json
export OBS_SPEC_LINTER_CONFIG_PATH=/path/to/linter.json
export OBS_SPEC_QUICKADD_CONFIG_PATH=/path/to/quickadd.json
export OBS_SPEC_TEMPLATER_CONFIG_PATH=/path/to/templater.json
export OBS_SPEC_META_BIND_CONFIG_PATH=/path/to/meta_bind.json
export OBS_SPEC_JS_ENGINE_CONFIG_PATH=/path/to/js_engine.json
export OBS_SPEC_DOCXER_CONFIG_PATH=/path/to/docxer.json
```

Then call `get_effective_profile` to confirm what was loaded.

## Example workflow with mcp-obsidian

1. Ask this server for the right syntax and pattern.
2. Load the effective profile from your local config files.
3. Generate or validate markdown against the relevant packs.
4. Send the validated content to `mcp-obsidian` for insertion into the vault.

## Runtime examples

Starter runtime config files are included in `examples/runtime_configs/`.

Typical validation call pattern:

```json
{
  "markdown": "- [/] Draft proposal #task ⏫ 📅 2026-04-05",
  "packs": ["tasks", "linter"],
  "tasks_path": "examples/runtime_configs/tasks.json",
  "linter_path": "examples/runtime_configs/linter.json"
}
```

Typical generation call pattern:

```json
{
  "pack": "templater",
  "intent": "project-template",
  "title": "Project Alpha",
  "templater_path": "examples/runtime_configs/templater.json"
}
```

## Notes on pack scope

### Tasks
This pack validates markdown checklist lines and fenced `tasks` query blocks, and can honor custom status symbols and global filters from runtime config.

### Templater
This pack focuses on command delimiters and starter patterns, and can incorporate known `tp.user` helper names.

### QuickAdd
This pack focuses on format tokens and starter placeholder patterns, and can incorporate known variable and choice names.

### Meta Bind
This pack focuses on inline `INPUT[...]`, `VIEW[...]`, and related patterns, and can incorporate field-type conventions.

### JS Engine
This pack focuses on fenced `js-engine` blocks and can surface configured helper names.

### Docxer
This pack is workflow-oriented rather than a custom markdown grammar, but can carry local defaults for input and output paths.

### Linter
This pack expresses hygiene rules that help generated notes survive local linting and can honor local style policy.

## Extend it

Useful next steps:
- replace the bundled docs with fuller local mirrors of the official plugin docs,
- read actual Obsidian plugin data files directly from a vault path,
- add stricter validators for each plugin pack,
- add prompt variants for your most common note patterns,
- add downstream orchestration so a client can validate here and write through `mcp-obsidian` in one flow.
