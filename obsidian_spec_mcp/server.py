from __future__ import annotations

import json
import re
from typing import Annotated

from mcp.server.fastmcp import FastMCP

from .config import load_effective_profile
from .models import PluginConfigPaths
from .registry import available_packs, get_pack, load_doc_text, load_profile, normalize_pack_name, search_docs
from .renderers import generate_snippet
from .validators import validate_markdown

# Error pattern library for mapping error messages to validation tools
# Note: More specific patterns must come before general ones
ERROR_PATTERNS = {
    "Error parsing Mermaid diagram": {
        "tool": "debug_mermaid",
        "packs": ["mermaid"],
        "message": "Mermaid parsing error detected - running debug analysis...",
        "suggestion": "Use debug_mermaid for detailed analysis and fixes"
    },
    "Lexical error on line": {
        "tool": "validate_obsidian_markdown",
        "packs": ["mermaid"],
        "message": "Mermaid syntax error detected - running validation...",
        "suggestion": "Common causes: unquoted special characters (/ # : ()) in node labels"
    },
    "Unbalanced Templater tags": {
        "tool": "validate_obsidian_markdown", 
        "packs": ["templater"],
        "message": "Templater syntax error detected - running validation...",
        "suggestion": "Check for missing <% or %> tags"
    },
    "Tasks metadata markers": {
        "tool": "validate_obsidian_markdown",
        "packs": ["tasks"],
        "message": "Tasks syntax error detected - running validation...",
        "suggestion": "Ensure task metadata markers are on valid checklist items"
    }
}

INSTRUCTIONS = (
    "Obsidian Spec MCP provides authoritative syntax references, validation, "
    "and snippet generation for Obsidian markdown and popular community plugins. "
    "\n\n"
    "## Recommended workflow\n"
    "1. **Lookup** — call `get_doc` or `search_spec` to understand correct syntax for the target pack(s).\n"
    "2. **Generate** — call `generate_obsidian_snippet` to produce a starter snippet tailored to the user's profile.\n"
    "3. **Validate** — call `validate_obsidian_markdown` on the draft before delivering it to the user.\n"
    "4. **Write** — use a separate vault-write server (e.g. mcp-obsidian) to persist the validated note.\n"
    "\n"
    "## Debugging workflow\n"
    "When encountering Obsidian rendering errors:\n"
    "- **Mermaid errors**: Use `debug_mermaid` for lexical errors, parsing failures, or rendering issues\n"
    "- **Syntax errors**: Use `validate_obsidian_markdown` with appropriate packs\n"
    "- **Unknown errors**: Use `detect_error_pattern` to map error messages to validation tools\n"
    "\n"
    "## Important guidelines\n"
    "- This server is **read-only**. It cannot write to an Obsidian vault. Use mcp-obsidian for writes.\n"
    "- Always validate before writing. Generated snippets should pass their own pack's validator.\n"
    "- When runtime plugin config paths are provided, they override the bundled defaults "
    "so that validation and generation match the user's actual vault settings.\n"
    "- Only use plugin-specific syntax (Tasks, Templater, etc.) when the corresponding pack is enabled.\n"
    "- Bundled packs: core, tasks, templater, quickadd, meta_bind, js_engine, docxer, linter, dataview, datacore, mermaid, styling.\n"
    "\n"
    "## When to Use This Tool\n"
    "- When encountering Obsidian rendering errors\n"
    "- When syntax validation is needed\n"
    "- When unsure about plugin-specific syntax\n"
    "- When debugging existing markdown\n"
    "- When Mermaid diagrams fail to parse or render\n"
)

mcp = FastMCP(
    name="Obsidian Spec MCP",
    instructions=INSTRUCTIONS,
    stateless_http=True,
    json_response=True,
)


def _runtime_paths(
    profile_path: str | None = None,
    tasks_path: str | None = None,
    linter_path: str | None = None,
    quickadd_path: str | None = None,
    templater_path: str | None = None,
    meta_bind_path: str | None = None,
    js_engine_path: str | None = None,
    docxer_path: str | None = None,
    dataview_path: str | None = None,
    datacore_path: str | None = None,
    mermaid_path: str | None = None,
) -> PluginConfigPaths:
    return PluginConfigPaths(
        profile_path=profile_path,
        tasks_path=tasks_path,
        linter_path=linter_path,
        quickadd_path=quickadd_path,
        templater_path=templater_path,
        meta_bind_path=meta_bind_path,
        js_engine_path=js_engine_path,
        docxer_path=docxer_path,
        dataview_path=dataview_path,
        datacore_path=datacore_path,
        mermaid_path=mermaid_path,
    )


@mcp.resource("obsidian://packs/index")
def pack_index() -> str:
    payload = [pack.model_dump(mode="json") for pack in available_packs()]
    return json.dumps(payload, indent=2)


@mcp.resource("obsidian://packs/{name}")
def pack_resource(name: str) -> str:
    pack = get_pack(name)
    return json.dumps(pack.model_dump(mode="json"), indent=2)


@mcp.resource("obsidian://docs/{name}")
def pack_doc(name: str) -> str:
    return load_doc_text(name)


@mcp.resource("obsidian://profiles/{name}")
def profile_resource(name: str) -> str:
    profile = load_profile(name)
    return json.dumps(profile.model_dump(mode="json"), indent=2)


@mcp.tool()
def list_packs(enabled_only: bool = False) -> list[dict]:
    """List all registered Obsidian spec packs. Returns a JSON array of objects with fields: name, title, description, syntax_kinds, enabled_by_default. Set enabled_only=true to filter to packs that are active by default."""
    return [pack.model_dump(mode="json") for pack in available_packs(enabled_only=enabled_only)]


@mcp.tool()
def get_pack_info(name: str) -> dict:
    """Return metadata and source links for a spec pack. Accepts pack name or alias (e.g. 'doxcer' resolves to 'docxer'). Returns a JSON object with name, title, description, syntax_kinds, docs (array of {label, url}), examples, validator_notes, and enabled_by_default."""
    try:
        return get_pack(name).model_dump(mode="json")
    except (KeyError, ValueError) as exc:
        return {"error": True, "message": f"Unknown pack: {name}", "suggestion": "Call list_packs to see available packs."}


@mcp.tool()
def search_spec(query: str, packs: list[str] | None = None) -> list[dict]:
    """Search bundled spec docs by keyword across one or more packs. Returns a JSON array of {pack, line, text, score} sorted by relevance. Omit packs to search all. Use this before generating markdown to find the correct syntax."""
    return [hit.model_dump(mode="json") for hit in search_docs(query=query, packs=packs)]


@mcp.tool()
def get_doc(name: str) -> str:
    """Return the bundled markdown guidance for a specific pack. Accepts pack name or alias. Returns the full spec document as markdown text including rules, examples, and edge cases. Use this to understand a pack's syntax before generating or validating."""
    try:
        return load_doc_text(name)
    except (KeyError, ValueError) as exc:
        return f"Error: Unknown pack '{name}'. Call list_packs to see available packs."


@mcp.tool()
def get_effective_profile(
    profile_name: str = "default",
    profile_path: str | None = None,
    tasks_path: str | None = None,
    linter_path: str | None = None,
    quickadd_path: str | None = None,
    templater_path: str | None = None,
    meta_bind_path: str | None = None,
    js_engine_path: str | None = None,
    docxer_path: str | None = None,
    dataview_path: str | None = None,
    datacore_path: str | None = None,
    mermaid_path: str | None = None,
) -> dict:
    """Load the bundled profile plus any runtime plugin config files or overlays. Returns {profile: {...}, sources: [{kind, path, loaded, error}]}. Pass file paths to plugin JSON configs (e.g. tasks_path pointing to the Tasks plugin data.json) to tailor validation and generation to the user's actual vault settings."""
    report = load_effective_profile(
        profile_name=profile_name,
        config_paths=_runtime_paths(
            profile_path=profile_path,
            tasks_path=tasks_path,
            linter_path=linter_path,
            quickadd_path=quickadd_path,
            templater_path=templater_path,
            meta_bind_path=meta_bind_path,
            js_engine_path=js_engine_path,
            docxer_path=docxer_path,
            dataview_path=dataview_path,
            datacore_path=datacore_path,
            mermaid_path=mermaid_path,
        ),
    )
    return report.model_dump(mode="json")


@mcp.tool()
def validate_obsidian_markdown(
    markdown: str,
    packs: list[str] | None = None,
    profile_name: str = "default",
    profile_path: str | None = None,
    tasks_path: str | None = None,
    linter_path: str | None = None,
    quickadd_path: str | None = None,
    templater_path: str | None = None,
    meta_bind_path: str | None = None,
    js_engine_path: str | None = None,
    docxer_path: str | None = None,
    dataview_path: str | None = None,
    datacore_path: str | None = None,
    mermaid_path: str | None = None,
) -> dict:
    """Validate markdown against one or more Obsidian spec packs. Returns {valid: bool, packs_checked: [...], issues: [{pack, severity, message, line, suggestion}], summary: str, suggested_fixes: [...]}. Omit packs to use the profile's default_packs. Always call this before writing markdown to a vault. Does NOT write files — use mcp-obsidian for that."""
    runtime = load_effective_profile(
        profile_name=profile_name,
        config_paths=_runtime_paths(
            profile_path=profile_path,
            tasks_path=tasks_path,
            linter_path=linter_path,
            quickadd_path=quickadd_path,
            templater_path=templater_path,
            meta_bind_path=meta_bind_path,
            js_engine_path=js_engine_path,
            docxer_path=docxer_path,
            dataview_path=dataview_path,
            datacore_path=datacore_path,
            mermaid_path=mermaid_path,
        ),
    )
    selected = packs or runtime.profile.default_packs
    report = validate_markdown(markdown=markdown, packs=selected, profile=runtime.profile)
    
    # Generate suggested fixes for common issues
    suggested_fixes = []
    for issue in report.issues:
        if issue.pack == "mermaid" and "special character" in issue.message.lower():
            # Extract the problematic line and suggest fixes
            if issue.line:
                lines = markdown.split('\n')
                if 0 < issue.line <= len(lines):
                    original_line = lines[issue.line - 1]
                    # Fix unquoted special characters in node labels
                    fixed_line = re.sub(
                        r'(\{|\[|\()([^{}[\]()"]*[/#:()][^{}[\]()"]*)(\}|\]|\))',
                        lambda m: f'{m.group(1)}"{m.group(2)}"{m.group(3)}',
                        original_line
                    )
                    if fixed_line != original_line:
                        suggested_fixes.append({
                            "line": issue.line,
                            "original": original_line.strip(),
                            "fixed": fixed_line.strip(),
                            "explanation": "Unquoted special characters in node label - wrap in double quotes"
                        })
    
    result = report.model_dump(mode="json")
    result["suggested_fixes"] = suggested_fixes
    return result


@mcp.tool()
def generate_obsidian_snippet(
    pack: str,
    intent: str,
    title: str | None = None,
    details_json: str | None = None,
    profile_name: str = "default",
    profile_path: str | None = None,
    tasks_path: str | None = None,
    linter_path: str | None = None,
    quickadd_path: str | None = None,
    templater_path: str | None = None,
    meta_bind_path: str | None = None,
    js_engine_path: str | None = None,
    docxer_path: str | None = None,
    dataview_path: str | None = None,
    datacore_path: str | None = None,
    mermaid_path: str | None = None,
) -> dict:
    """Generate a starter markdown snippet for a specific pack and intent. Returns {pack, intent, markdown, notes, profile_hints}. Common intents: core/note, tasks/task-line, tasks/query, templater/project-template, quickadd/capture, meta_bind/form, js_engine/script, docxer/convert, linter/hygiene, dataview/query, dataview/inline, dataview/dataviewjs, datacore/view, mermaid/flowchart, mermaid/sequence, mermaid/class, mermaid/state, mermaid/er, mermaid/gantt, mermaid/pie, mermaid/mindmap, mermaid/timeline, mermaid/quadrant, mermaid/gitgraph, mermaid/journey, mermaid/obsidian-linked. Validate the returned markdown before writing it to a vault."""
    details = json.loads(details_json) if details_json else {}
    runtime = load_effective_profile(
        profile_name=profile_name,
        config_paths=_runtime_paths(
            profile_path=profile_path,
            tasks_path=tasks_path,
            linter_path=linter_path,
            quickadd_path=quickadd_path,
            templater_path=templater_path,
            meta_bind_path=meta_bind_path,
            js_engine_path=js_engine_path,
            docxer_path=docxer_path,
            dataview_path=dataview_path,
            datacore_path=datacore_path,
            mermaid_path=mermaid_path,
        ),
    )
    snippet = generate_snippet(pack=pack, intent=intent, title=title, details=details, profile=runtime.profile)
    return snippet.model_dump(mode="json")


@mcp.tool()
def detect_error_pattern(error_message: str) -> dict:
    """Detect error patterns and map them to appropriate validation tools. Returns {pattern_found, tool, packs, message, suggestion}. Use when encountering Obsidian rendering errors to determine which validation tool to use."""
    for pattern, config in ERROR_PATTERNS.items():
        if pattern in error_message:
            return {
                "pattern_found": True,
                "matched_pattern": pattern,
                "tool": config["tool"],
                "packs": config["packs"],
                "message": config["message"],
                "suggestion": config["suggestion"]
            }
    
    return {
        "pattern_found": False,
        "tool": "validate_obsidian_markdown",
        "packs": ["core", "mermaid"],
        "message": "No specific error pattern detected - running general validation...",
        "suggestion": "Consider checking syntax for all active plugins"
    }


@mcp.tool()
def debug_mermaid(
    markdown: str,
    profile_name: str = "default",
    profile_path: str | None = None,
    tasks_path: str | None = None,
    linter_path: str | None = None,
    quickadd_path: str | None = None,
    templater_path: str | None = None,
    meta_bind_path: str | None = None,
    js_engine_path: str | None = None,
    docxer_path: str | None = None,
    dataview_path: str | None = None,
    datacore_path: str | None = None,
    mermaid_path: str | None = None,
) -> dict:
    """Debug a Mermaid diagram that's not rendering. Returns detailed error analysis with line numbers, suggested fixes, and corrected code. Use when encountering Mermaid parsing errors or rendering failures."""
    runtime = load_effective_profile(
        profile_name=profile_name,
        config_paths=_runtime_paths(
            profile_path=profile_path,
            tasks_path=tasks_path,
            linter_path=linter_path,
            quickadd_path=quickadd_path,
            templater_path=templater_path,
            meta_bind_path=meta_bind_path,
            js_engine_path=js_engine_path,
            docxer_path=docxer_path,
            dataview_path=dataview_path,
            datacore_path=datacore_path,
            mermaid_path=mermaid_path,
        ),
    )
    
    # Run validation with enhanced error reporting
    report = validate_markdown(markdown=markdown, packs=["mermaid"], profile=runtime.profile)
    
    # Generate comprehensive debugging analysis
    analysis = {
        "valid": report.valid,
        "issues": [issue.model_dump(mode="json") for issue in report.issues],
        "suggested_fixes": [],
        "corrected_code": markdown,
        "debug_steps": []
    }
    
    # Analyze each issue and generate fixes
    for issue in report.issues:
        if issue.line and issue.line > 0:
            lines = markdown.split('\n')
            if 0 < issue.line <= len(lines):
                original_line = lines[issue.line - 1]
                fixed_line = original_line
                
                if "special character" in issue.message.lower():
                    # Fix unquoted special characters
                    fixed_line = re.sub(
                        r'(\{|\[|\()([^{}[\]()"]*[/#:()][^{}[\]()"]*)(\}|\]|\))',
                        lambda m: f'{m.group(1)}"{m.group(2)}"{m.group(3)}',
                        original_line
                    )
                    analysis["debug_steps"].append(f"Line {issue.line}: Fixed unquoted special characters in node label")
                
                # Update the corrected code
                if fixed_line != original_line:
                    analysis["corrected_code"] = analysis["corrected_code"].replace(original_line, fixed_line)
                    analysis["suggested_fixes"].append({
                        "line": issue.line,
                        "original": original_line.strip(),
                        "fixed": fixed_line.strip(),
                        "issue": issue.message,
                        "suggestion": issue.suggestion
                    })
    
    # Add debugging summary
    if analysis["suggested_fixes"]:
        analysis["summary"] = f"Found {len(analysis['suggested_fixes'])} fixable issues in Mermaid diagram"
    else:
        analysis["summary"] = "No syntax errors detected, but diagram may still have rendering issues"
    
    return analysis


@mcp.tool()
def normalized_pack_name(name: str) -> dict:
    """Normalize aliases such as doxcer -> docxer or metabind -> meta_bind. Returns {input, normalized}. Use this when unsure of the canonical pack name."""
    normalized = normalize_pack_name(name)
    return {"input": name, "normalized": normalized}


@mcp.prompt(title="Create Obsidian Markdown")
def create_obsidian_markdown(
    goal: str,
    packs_csv: str = "core,tasks",
    strict: bool = True,
) -> str:
    packs = [normalize_pack_name(part) for part in packs_csv.split(",") if part.strip()]
    strict_line = "Validate the draft against the selected packs before returning it." if strict else "Return a best-effort draft."
    return (
        "You are authoring Obsidian markdown. "
        f"Goal: {goal}. "
        f"Selected packs: {', '.join(packs)}. "
        "Fetch pack resources first, then use only syntax documented in those packs. "
        f"{strict_line}"
    )


@mcp.prompt(title="Create Tasks Snippet")
def create_tasks_snippet(
    goal: str,
    mode: Annotated[str, "task-line or query"] = "task-line",
) -> str:
    return (
        "Create Obsidian Tasks syntax for the following goal: "
        f"{goal}. "
        f"Return a {mode} using the Tasks pack. "
        "Keep the output strictly compatible with a markdown checklist item or a fenced tasks query block."
    )


@mcp.prompt(title="Create Templater Template")
def create_templater_template(goal: str) -> str:
    return (
        "Create a Templater-compatible template for the following goal: "
        f"{goal}. Use valid <% ... %> and <%* ... %> syntax only when needed."
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
