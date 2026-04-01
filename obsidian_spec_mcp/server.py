from __future__ import annotations

import json
from typing import Annotated

from mcp.server.fastmcp import FastMCP

from .config import load_effective_profile
from .models import PluginConfigPaths
from .registry import available_packs, get_pack, load_doc_text, load_profile, normalize_pack_name, search_docs
from .renderers import generate_snippet
from .validators import validate_markdown

INSTRUCTIONS = (
    "Obsidian Spec MCP is a spec-centric MCP server for Obsidian authoring. "
    "Use resources and search tools to fetch authoritative pack guidance before generating markdown. "
    "Prefer Tasks, Templater, QuickAdd, Meta Bind, JS Engine, Docxer, and Linter syntax only when the corresponding pack is enabled. "
    "Validate generated markdown before writing it to a vault through a separate write-capable MCP server such as mcp-obsidian. "
    "When runtime plugin config files are available, load them to tailor generation and validation to the actual vault."
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
    """List available spec packs and their primary syntax domains."""
    return [pack.model_dump(mode="json") for pack in available_packs(enabled_only=enabled_only)]


@mcp.tool()
def get_pack_info(name: str) -> dict:
    """Return metadata and source links for a spec pack."""
    return get_pack(name).model_dump(mode="json")


@mcp.tool()
def search_spec(query: str, packs: list[str] | None = None) -> list[dict]:
    """Search bundled spec docs by keyword across one or more packs."""
    return [hit.model_dump(mode="json") for hit in search_docs(query=query, packs=packs)]


@mcp.tool()
def get_doc(name: str) -> str:
    """Return the bundled markdown guidance for a specific pack."""
    return load_doc_text(name)


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
) -> dict:
    """Load the bundled profile plus any runtime plugin config files or overlays."""
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
) -> dict:
    """Validate markdown against one or more Obsidian spec packs, tailored to runtime plugin config files when provided."""
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
        ),
    )
    selected = packs or runtime.profile.default_packs
    report = validate_markdown(markdown=markdown, packs=selected, profile=runtime.profile)
    return report.model_dump(mode="json")


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
) -> dict:
    """Generate a starter snippet for a specific pack and intent, using runtime plugin config when available."""
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
        ),
    )
    snippet = generate_snippet(pack=pack, intent=intent, title=title, details=details, profile=runtime.profile)
    return snippet.model_dump(mode="json")


@mcp.tool()
def normalized_pack_name(name: str) -> dict:
    """Normalize aliases such as doxcer -> docxer or metabind -> meta_bind."""
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
