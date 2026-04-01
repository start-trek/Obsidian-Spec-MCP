from __future__ import annotations

import json
from importlib import resources
from typing import Iterable

from .models import DocSource, PackInfo, Profile, SearchHit


PACKS: dict[str, PackInfo] = {
    "core": PackInfo(
        name="core",
        title="Obsidian Core",
        description="Core Obsidian authoring rules for wikilinks, embeds, callouts, and properties.",
        syntax_kinds=["wikilinks", "embeds", "callouts", "properties"],
        docs=[
            DocSource(label="Obsidian Help", url="https://obsidian.md/help/Home"),
        ],
        examples=[
            "[[Project Note]]",
            "![[Design Spec#Open Questions]]",
            "> [!info] Summary",
        ],
        validator_notes=[
            "Prefer wikilinks for vault-internal references when the profile says so.",
            "Callouts use blockquote syntax and a [!type] marker.",
        ],
    ),
    "tasks": PackInfo(
        name="tasks",
        title="Tasks",
        description="Obsidian Tasks plugin syntax for task lines, date emojis, recurrence, and tasks query blocks.",
        syntax_kinds=["task-line", "tasks-query"],
        docs=[
            DocSource(label="Tasks User Guide", url="https://publish.obsidian.md/tasks/Introduction"),
            DocSource(label="Tasks Getting Started", url="https://publish.obsidian.md/tasks/Getting%2BStarted/Getting%2BStarted"),
        ],
        examples=[
            "- [ ] Draft proposal ⏫ 📅 2026-04-05",
            "```tasks\nnot done\ndue before tomorrow\nsort by due\n```",
        ],
        validator_notes=[
            "A Tasks task line starts as a markdown checklist item.",
            "Tasks queries belong inside fenced code blocks with language tasks.",
        ],
    ),
    "templater": PackInfo(
        name="templater",
        title="Templater",
        description="Templater command syntax and template conventions.",
        syntax_kinds=["templater-inline", "templater-exec"],
        docs=[
            DocSource(label="Templater Introduction", url="https://silentvoid13.github.io/Templater/introduction.html"),
            DocSource(label="Templater Commands", url="https://silentvoid13.github.io/Templater/commands/overview.html"),
        ],
        examples=[
            "<% tp.file.title %>",
            "<%* const today = tp.date.now('YYYY-MM-DD') %>",
        ],
        validator_notes=[
            "Interpolation tags start with <% and end with %>.",
            "Execution tags start with <%* and end with %>.",
        ],
    ),
    "quickadd": PackInfo(
        name="quickadd",
        title="QuickAdd",
        description="QuickAdd format syntax, choices, variables, and packaging conventions.",
        syntax_kinds=["quickadd-format", "quickadd-choice"],
        docs=[
            DocSource(label="QuickAdd Getting Started", url="https://quickadd.obsidian.guide/docs/"),
            DocSource(label="QuickAdd VALUE", url="https://publish.obsidian.md/quickadd/VALUE"),
        ],
        examples=[
            "{{DATE}}",
            "{{VALUE:project}}",
        ],
        validator_notes=[
            "QuickAdd commonly uses double-brace format placeholders.",
            "Keep placeholders balanced and uppercase built-in variables unless your local package says otherwise.",
        ],
    ),
    "meta_bind": PackInfo(
        name="meta_bind",
        title="Meta Bind",
        description="Meta Bind inline fields, meta-bind code blocks, and button patterns.",
        syntax_kinds=["meta-bind-input", "meta-bind-block", "meta-bind-button"],
        docs=[
            DocSource(label="Meta Bind Docs", url="https://www.moritzjung.dev/obsidian-meta-bind-plugin-docs/"),
            DocSource(label="Meta Bind Input Fields", url="https://www.moritzjung.dev/obsidian-meta-bind-plugin-docs/guides/inputfields/"),
        ],
        examples=[
            "INPUT[toggle:done]",
            "```meta-bind\nINPUT[text:title]\n```",
        ],
        validator_notes=[
            "Inline input fields use INPUT[...] syntax.",
            "Block declarations can use fenced code blocks with language meta-bind.",
        ],
    ),
    "js_engine": PackInfo(
        name="js_engine",
        title="JS Engine",
        description="JS Engine executable code blocks and rendering patterns.",
        syntax_kinds=["js-engine-block"],
        docs=[
            DocSource(label="JS Engine Docs", url="https://www.moritzjung.dev/obsidian-js-engine-plugin-docs/"),
            DocSource(label="JS Engine GitHub", url="https://github.com/mProjectsCode/obsidian-js-engine-plugin"),
        ],
        examples=[
            "```js-engine\nreturn engine.markdown.create('*test*');\n```",
        ],
        validator_notes=[
            "JS Engine executes code from fenced code blocks with language js-engine.",
        ],
    ),
    "docxer": PackInfo(
        name="docxer",
        title="Docxer",
        description="Docxer conversion workflow and docx-to-markdown considerations.",
        syntax_kinds=["docxer-workflow"],
        docs=[
            DocSource(label="Docxer GitHub", url="https://github.com/Developer-Mike/obsidian-docxer"),
        ],
        examples=[
            "1. Add a .docx file to your vault.\n2. Open it in Obsidian.\n3. Convert to markdown.",
        ],
        validator_notes=[
            "Docxer is workflow-oriented rather than a bespoke markdown grammar.",
        ],
    ),
    "linter": PackInfo(
        name="linter",
        title="Linter",
        description="Linter rule-aware note hygiene for headings, frontmatter, spacing, and markdown cleanup.",
        syntax_kinds=["linter-profile", "lint-style"],
        docs=[
            DocSource(label="Linter Docs", url="https://platers.github.io/obsidian-linter/"),
            DocSource(label="Linter GitHub", url="https://github.com/platers/obsidian-linter"),
        ],
        examples=[
            "Keep one H1 at the top of the note.",
            "Normalize blank lines and frontmatter spacing.",
        ],
        validator_notes=[
            "Linter is configuration-driven, so local vault policy matters more than generic markdown style.",
        ],
    ),
    "dataview": PackInfo(
        name="dataview",
        title="Dataview",
        description="Dataview query language for creating dynamic views and tables from vault metadata.",
        syntax_kinds=["dataview-query", "dataviewjs", "inline-dataview"],
        docs=[
            DocSource(label="Dataview Docs", url="https://blacksmithgu.github.io/obsidian-dataview/"),
            DocSource(label="Dataview GitHub", url="https://github.com/blacksmithgu/obsidian-dataview"),
        ],
        examples=[
            "```dataview\nLIST FROM #project\nWHERE completed = false\n```",
            "`= this.title`",
            "```dataviewjs\ndv.table(['File', 'Modified'], dv.pages().map(p => [p.file.link, p.file.mtime]))\n```",
        ],
        validator_notes=[
            "Dataview queries belong in fenced code blocks with language dataview.",
            "DataviewJS uses dataviewjs language for JavaScript execution.",
            "Inline queries use backtick-equals syntax.",
        ],
        enabled_by_default=True,
    ),
    "datacore": PackInfo(
        name="datacore",
        title="Datacore",
        description="Datacore reactive components for live-updating data views in Obsidian.",
        syntax_kinds=["datacore-component", "datacore-block"],
        docs=[
            DocSource(label="Datacore GitHub", url="https://github.com/blacksmithgu/obsidian-datacore"),
        ],
        examples=[
            "```datacore\nview: table\nfrom: #project\n```",
        ],
        validator_notes=[
            "Datacore is an experimental successor to Dataview.",
        ],
        enabled_by_default=False,
    ),
}


def load_profile(profile_name: str = "default") -> Profile:
    with resources.files("obsidian_spec_mcp.profiles").joinpath(f"{profile_name}_profile.json").open("r", encoding="utf-8") as fh:
        return Profile.model_validate(json.load(fh))


def available_packs(enabled_only: bool = False) -> list[PackInfo]:
    packs = list(PACKS.values())
    if enabled_only:
        packs = [pack for pack in packs if pack.enabled_by_default]
    return packs


def get_pack(name: str) -> PackInfo:
    normalized = normalize_pack_name(name)
    try:
        return PACKS[normalized]
    except KeyError as exc:
        raise ValueError(f"Unknown pack: {name}") from exc


def normalize_pack_name(name: str) -> str:
    token = name.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "metabind": "meta_bind",
        "meta_bind_plugin": "meta_bind",
        "jsengine": "js_engine",
        "docxer": "docxer",
        "doxcer": "docxer",
        "core_obsidian": "core",
        "obsidian": "core",
        "dv": "dataview",
        "dvjs": "dataview",
        "data_view": "dataview",
        "data_core": "datacore",
    }
    return aliases.get(token, token)


def load_doc_text(pack_name: str) -> str:
    normalized = normalize_pack_name(pack_name)
    with resources.files("obsidian_spec_mcp.docs").joinpath(f"{normalized}.md").open("r", encoding="utf-8") as fh:
        return fh.read()


def search_docs(query: str, packs: Iterable[str] | None = None) -> list[SearchHit]:
    terms = [term.casefold() for term in query.split() if term.strip()]
    target_names = [normalize_pack_name(p) for p in packs] if packs else list(PACKS.keys())
    hits: list[SearchHit] = []
    for pack_name in target_names:
        text = load_doc_text(pack_name)
        haystack = text.casefold()
        score = sum(haystack.count(term) for term in terms)
        if not terms:
            score = 1
        if score <= 0:
            continue
        snippet = make_snippet(text, terms)
        pack = PACKS[pack_name]
        source_url = pack.docs[0].url if pack.docs else None
        hits.append(
            SearchHit(
                pack=pack.name,
                title=pack.title,
                score=score,
                snippet=snippet,
                source_url=source_url,
            )
        )
    return sorted(hits, key=lambda hit: hit.score, reverse=True)


def make_snippet(text: str, terms: list[str], width: int = 260) -> str:
    if not text:
        return ""
    if not terms:
        return text[:width].strip()

    lower = text.casefold()
    positions = [lower.find(term) for term in terms if lower.find(term) >= 0]
    start = max(min(positions) - 40, 0) if positions else 0
    end = min(start + width, len(text))
    return text[start:end].strip().replace("\n", " ")
