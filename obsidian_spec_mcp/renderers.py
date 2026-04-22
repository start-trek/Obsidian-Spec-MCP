from __future__ import annotations

from textwrap import dedent

from .models import GeneratedSnippet, Profile
from .registry import normalize_pack_name


def generate_snippet(
    pack: str,
    intent: str,
    title: str | None = None,
    details: dict | None = None,
    profile: Profile | None = None,
) -> GeneratedSnippet:
    normalized = normalize_pack_name(pack)
    details = details or {}
    profile = profile or Profile(name="runtime")
    title = title or "Untitled"

    if normalized == "tasks":
        return _tasks(intent=intent, title=title, details=details, profile=profile)
    if normalized == "templater":
        return _templater(intent=intent, title=title, details=details, profile=profile)
    if normalized == "quickadd":
        return _quickadd(intent=intent, title=title, details=details, profile=profile)
    if normalized == "meta_bind":
        return _meta_bind(intent=intent, title=title, details=details, profile=profile)
    if normalized == "js_engine":
        return _js_engine(intent=intent, title=title, details=details, profile=profile)
    if normalized == "docxer":
        return _docxer(intent=intent, title=title, details=details, profile=profile)
    if normalized == "linter":
        return _linter(intent=intent, title=title, details=details, profile=profile)
    if normalized == "dataview":
        return _dataview(intent=intent, title=title, details=details, profile=profile)
    if normalized == "datacore":
        return _datacore(intent=intent, title=title, details=details, profile=profile)
    if normalized == "mermaid":
        return _mermaid(intent=intent, title=title, details=details, profile=profile)
    if normalized == "styling":
        return _styling(intent=intent, title=title, details=details, profile=profile)
    return _core(intent=intent, title=title, details=details, profile=profile)


def _core(intent: str, title: str, details: dict, profile: Profile) -> GeneratedSnippet:
    related_link = "[[Related Note]]" if profile.use_wikilinks else "[Related Note](Related%20Note.md)"
    related_embed = "![[Reference Note#Key Section]]" if profile.use_wikilinks else "![](Reference%20Note.md#Key%20Section)"
    markdown = dedent(
        f"""
        ---
        title: {title}
        tags:
          - obsidian
        ---

        # {title}

        > [!info] Summary
        > {details.get('summary', 'Add a concise summary here.')}

        ## Related
        - {related_link}
        - {related_embed}
        """
    ).strip()
    return GeneratedSnippet(pack="core", intent=intent, markdown=markdown)


def _tasks(intent: str, title: str, details: dict, profile: Profile) -> GeneratedSnippet:
    profile_hints = []
    custom_symbols = [item.get("symbol") for item in profile.tasks_custom_statuses if item.get("symbol")]
    status_symbol = details.get("status_symbol") or (custom_symbols[0] if custom_symbols else " ")
    if custom_symbols:
        profile_hints.append(f"Configured custom task statuses: {', '.join(custom_symbols)}")
    if intent == "query":
        path_line = f"path includes {details.get('path', 'Projects')}"
        global_filter = profile.tasks_global_filter or details.get("global_filter")
        filter_line = f"filter by function task.description.includes('{global_filter}')" if global_filter and profile.tasks_append_global_filter_to_queries else None
        lines = ["```tasks", "not done", path_line]
        if filter_line:
            lines.append(filter_line)
        lines.extend(["sort by due", "group by folder", "```"])
        markdown = "\n".join(lines)
    else:
        due = details.get("due", "2026-04-08")
        priority = details.get("priority", "⏫")
        recurrence = details.get("recurrence")
        recurring = f" 🔁 every {recurrence}" if recurrence else ""
        global_filter = f" {profile.tasks_global_filter}" if profile.tasks_global_filter else ""
        markdown = f"- [{status_symbol}] {title}{global_filter} {priority} 📅 {due}{recurring}".strip()
    return GeneratedSnippet(
        pack="tasks",
        intent=intent,
        markdown=markdown,
        notes=["Adjust dates, recurrence, and custom statuses to match your vault settings."],
        profile_hints=profile_hints,
    )


def _templater(intent: str, title: str, details: dict, profile: Profile) -> GeneratedSnippet:
    helper_note = ""
    profile_hints = []
    if profile.templater_user_scripts:
        helper = profile.templater_user_scripts[0]
        helper_note = f'\nHelper: <% tp.user.{helper}() %>'
        profile_hints.append(f"Known tp.user helpers: {', '.join(profile.templater_user_scripts)}")
    lines = [
        '---',
        f'created: <% tp.file.creation_date("YYYY-MM-DD") %>',
        f'title: {title}',
        '---',
        '',
        '# <% tp.file.title %>',
        '',
        '<%* const today = tp.date.now("YYYY-MM-DD") %>',
        f'Date: <% today %>{helper_note}',
    ]
    markdown = '\n'.join(lines)
    return GeneratedSnippet(pack="templater", intent=intent, markdown=markdown, profile_hints=profile_hints)


def _quickadd(intent: str, title: str, details: dict, profile: Profile) -> GeneratedSnippet:
    project_var = profile.quickadd_known_variables[0] if profile.quickadd_known_variables else "project"
    summary_var = profile.quickadd_known_variables[1] if len(profile.quickadd_known_variables) > 1 else "summary"
    lines = [
        f'# {title}',
        '',
        f'Date: {{{{DATE}}}}',
        f'Project: {{{{VALUE:{project_var}}}}}',
        f'Summary: {{{{VALUE:{summary_var}}}}}',
    ]
    markdown = '\n'.join(lines)
    hints = []
    if profile.quickadd_choice_names:
        hints.append(f"Known QuickAdd choices: {', '.join(profile.quickadd_choice_names)}")
    return GeneratedSnippet(pack="quickadd", intent=intent, markdown=markdown, profile_hints=hints)


def _meta_bind(intent: str, title: str, details: dict, profile: Profile) -> GeneratedSnippet:
    toggle_type = profile.meta_bind_field_types[0] if profile.meta_bind_field_types else "toggle"
    text_type = profile.meta_bind_field_types[1] if len(profile.meta_bind_field_types) > 1 else "text"
    markdown = dedent(
        f"""
        # {title}

        Done: `INPUT[{toggle_type}:done]`
        Title: `INPUT[{text_type}:title]`
        Current value: `VIEW[title]`
        """
    ).strip()
    return GeneratedSnippet(pack="meta_bind", intent=intent, markdown=markdown)


def _js_engine(intent: str, title: str, details: dict, profile: Profile) -> GeneratedSnippet:
    helper_line = ""
    hints = []
    if profile.js_engine_helpers:
        helper_line = f"\n// available helper: {profile.js_engine_helpers[0]}"
        hints.append(f"Known JS Engine helpers: {', '.join(profile.js_engine_helpers)}")
    body = f"return engine.markdown.create('*Hello from JS Engine*');{helper_line}"
    markdown = f"```js-engine\n{body}\n```"
    return GeneratedSnippet(pack="js_engine", intent=intent, markdown=markdown, profile_hints=hints)


def _docxer(intent: str, title: str, details: dict, profile: Profile) -> GeneratedSnippet:
    source_docx = details.get("source_docx", profile.docxer_defaults.get("source_docx", "document.docx"))
    output_note = details.get("output_note", profile.docxer_defaults.get("output_note", "document.md"))
    markdown = dedent(
        f"""
        # {title}

        Source file: {source_docx}
        Output note: {output_note}

        1. Add the .docx file to the vault.
        2. Open the file in Obsidian.
        3. Convert it to markdown with Docxer.
        """
    ).strip()
    return GeneratedSnippet(pack="docxer", intent=intent, markdown=markdown)


def _linter(intent: str, title: str, details: dict, profile: Profile) -> GeneratedSnippet:
    expectations = profile.linter_expectations or {}
    goals = [
        "One top-level heading" if expectations.get("single_h1", True) else "Multiple top-level headings allowed",
        "Clean frontmatter spacing" if expectations.get("prefer_yaml_frontmatter", True) else "Flexible metadata layout",
        "Normalized blank lines" if expectations.get("collapse_extra_blank_lines", True) else "Blank line style left open",
        "Consistent list markers",
    ]
    markdown = dedent(
        f"""
        # {title}

        ## Linter goals
        - {goals[0]}
        - {goals[1]}
        - {goals[2]}
        - {goals[3]}
        """
    ).strip()
    return GeneratedSnippet(pack="linter", intent=intent, markdown=markdown)


def _dataview(intent: str, title: str, details: dict, profile: Profile) -> GeneratedSnippet:
    if intent == "inline":
        field = details.get("field", "this.title")
        markdown = f"`= {field}`"
        return GeneratedSnippet(
            pack="dataview",
            intent=intent,
            markdown=markdown,
            notes=["Inline Dataview queries update in real-time when viewing the note."],
        )
    if intent == "dataviewjs":
        custom_views = profile.dataview_views if profile.dataview_views else []
        view_note = f"\n// Available views: {', '.join(custom_views)}" if custom_views else ""
        markdown = dedent(
            f"""\
            ```dataviewjs
            // Query all pages matching a tag{view_note}
            dv.table(
              ["File", "Modified"],
              dv.pages("#tag").map(p => [p.file.link, p.file.mtime])
            )
            ```
            """
        ).strip()
        return GeneratedSnippet(
            pack="dataview",
            intent=intent,
            markdown=markdown,
            notes=["DataviewJS provides full JavaScript access to the Dataview API."],
            profile_hints=custom_views,
        )
    # Default: dataview query block
    tag = details.get("tag", "project")
    sort_by = details.get("sort_by", "file.name")
    custom_views = profile.dataview_views if profile.dataview_views else []
    view_note = f"\n// Available saved views: {', '.join(custom_views)}" if custom_views else ""
    markdown = dedent(
        f"""\
        ```dataview{view_note}
        LIST FROM #{tag}
        WHERE completed = false
        SORT {sort_by} ASC
        ```
        """
    ).strip()
    return GeneratedSnippet(
        pack="dataview",
        intent=intent,
        markdown=markdown,
        notes=["Dataview queries update automatically when underlying data changes."],
        profile_hints=custom_views,
    )


def _datacore(intent: str, title: str, details: dict, profile: Profile) -> GeneratedSnippet:
    view_type = details.get("view", "table")
    from_source = details.get("from", "#project")
    custom_components = profile.datacore_components if profile.datacore_components else []
    component_note = f"\n# Custom components available: {', '.join(custom_components)}" if custom_components else ""
    markdown = dedent(
        f"""\
        ```datacore
        view: {view_type}
        from: {from_source}
        select:
          - file.link
          - status
          - due_date
        where: status != "completed"
        sort: due_date ASC
        ```{component_note}
        """
    ).strip()
    notes = [
        "Datacore is experimental and syntax may change.",
        "Views are reactive and update automatically.",
    ]
    return GeneratedSnippet(
        pack="datacore",
        intent=intent,
        markdown=markdown,
        notes=notes,
        profile_hints=custom_components,
    )


_MERMAID_TEMPLATES: dict[str, str] = {
    "flowchart": (
        "```mermaid\n"
        "flowchart TD\n"
        "    A[Start] --> B{\"Decision\"}\n"
        "    B -->|yes| C[Continue]\n"
        "    B -->|no| D[Stop]\n"
        "```"
    ),
    "sequence": (
        "```mermaid\n"
        "sequenceDiagram\n"
        "    participant Alice\n"
        "    participant Bob\n"
        "    Alice->>Bob: Hello\n"
        "    Bob-->>Alice: Hi\n"
        "```"
    ),
    "class": (
        "```mermaid\n"
        "classDiagram\n"
        "    class Animal {\n"
        "        +String name\n"
        "        +move() void\n"
        "    }\n"
        "    Animal <|-- Dog\n"
        "```"
    ),
    "state": (
        "```mermaid\n"
        "stateDiagram-v2\n"
        "    [*] --> Idle\n"
        "    Idle --> Running: start\n"
        "    Running --> Idle: stop\n"
        "    Running --> [*]\n"
        "```"
    ),
    "er": (
        "```mermaid\n"
        "erDiagram\n"
        "    CUSTOMER ||--o{ ORDER : places\n"
        "    ORDER ||--|{ LINE-ITEM : contains\n"
        "```"
    ),
    "gantt": (
        "```mermaid\n"
        "gantt\n"
        "    title Project Timeline\n"
        "    dateFormat YYYY-MM-DD\n"
        "    section Phase 1\n"
        "    Task A :a1, 2026-01-01, 30d\n"
        "    Task B :after a1, 20d\n"
        "```"
    ),
    "pie": (
        "```mermaid\n"
        "pie title Allocation\n"
        "    \"Work\" : 40\n"
        "    \"Sleep\" : 33\n"
        "    \"Other\" : 27\n"
        "```"
    ),
    "mindmap": (
        "```mermaid\n"
        "mindmap\n"
        "    root((Topic))\n"
        "        Branch A\n"
        "            Leaf A1\n"
        "        Branch B\n"
        "```"
    ),
    "timeline": (
        "```mermaid\n"
        "timeline\n"
        "    title History\n"
        "    2024 : Kickoff\n"
        "    2025 : Launch\n"
        "    2026 : Expansion\n"
        "```"
    ),
    "quadrant": (
        "```mermaid\n"
        "quadrantChart\n"
        "    title Effort vs Impact\n"
        "    x-axis Low Effort --> High Effort\n"
        "    y-axis Low Impact --> High Impact\n"
        "    Quick Wins: [0.2, 0.8]\n"
        "    Big Bets: [0.8, 0.8]\n"
        "```"
    ),
    "gitgraph": (
        "```mermaid\n"
        "gitGraph\n"
        "    commit\n"
        "    branch feature\n"
        "    commit\n"
        "    checkout main\n"
        "    merge feature\n"
        "```"
    ),
    "journey": (
        "```mermaid\n"
        "journey\n"
        "    title User onboarding\n"
        "    section Sign up\n"
        "      Visit site: 5: User\n"
        "      Create account: 4: User\n"
        "```"
    ),
    "obsidian-linked": (
        "```mermaid\n"
        "flowchart LR\n"
        "    A[Project Note] --> B[Reference]\n"
        "    class A,B internal-link;\n"
        "```"
    ),
}


def _mermaid(intent: str, title: str, details: dict, profile: Profile) -> GeneratedSnippet:
    key = intent.split("/")[-1] if "/" in intent else intent
    template = _MERMAID_TEMPLATES.get(key) or _MERMAID_TEMPLATES["flowchart"]
    notes = [
        "Quote labels that contain special characters like /, #, :, or parentheses.",
        "Obsidian bundles Mermaid v10.x; some v11 shapes and beta diagrams may not render.",
    ]
    hints: list[str] = []
    if profile.mermaid_allowed_diagrams:
        hints.append("Profile-allowed diagram types: " + ", ".join(profile.mermaid_allowed_diagrams))
    if key == "obsidian-linked":
        notes.append("Node IDs must match target note filenames for internal-link routing.")
    return GeneratedSnippet(
        pack="mermaid",
        intent=intent,
        markdown=template,
        notes=notes,
        profile_hints=hints,
    )


_STYLING_COMMON_NOTES = [
    "Use `cssclasses` (plural list) in frontmatter; `cssclass` is deprecated.",
    "CSS snippets live at <vault>/.obsidian/snippets/<name>.css and are toggled under Settings -> Appearance -> CSS snippets.",
    "Overrides to --file-line-width require Settings -> Editor -> Readable line length to be ENABLED.",
    "After editing a snippet, toggle it off/on or reload Obsidian for changes to apply.",
]


def _styling_cssclasses_frontmatter(details: dict) -> str:
    raw = details.get("cssclasses") or details.get("classes") or details.get("class_name") or "wide-page"
    if isinstance(raw, str):
        classes = [item.strip() for item in raw.split(",") if item.strip()]
    elif isinstance(raw, list):
        classes = [str(item).strip() for item in raw if str(item).strip()]
    else:
        classes = ["wide-page"]
    if not classes:
        classes = ["wide-page"]
    lines = ["---", "cssclasses:"]
    for cls in classes:
        lines.append(f"  - {cls}")
    lines.append("---")
    return "\n".join(lines)


def _styling_file_line_width_override(details: dict) -> str:
    class_name = str(details.get("class_name") or details.get("cssclass") or "wide-page")
    value = str(details.get("value") or details.get("width") or "100%")
    return (
        f"/* Widen notes tagged with `cssclasses: {class_name}`.\n"
        " * Requires Readable line length to be enabled in Settings. */\n"
        f".{class_name} {{\n"
        f"  --file-line-width: {value};\n"
        f"}}\n"
        "\n"
        "/* Minimal theme uses its own line-width variable. */\n"
        f"body.minimal-theme.minimal-theme .{class_name} {{\n"
        f"  --line-width: {value};\n"
        f"}}\n"
    )


def _styling_wide_page_snippet(details: dict) -> str:
    class_name = str(details.get("class_name") or "wide-page")
    buffer_px = str(details.get("sidebar_buffer") or "400px")
    return (
        f"/* {class_name}.css -- per-note mermaid breakout.\n"
        f" * Activate with frontmatter `cssclasses: [{class_name}]`.\n"
        " * Requires Readable line length enabled. */\n"
        "\n"
        "/* Reading mode: mermaid containers (wrapper + inner). */\n"
        f".{class_name} .markdown-preview-view .block-language-mermaid,\n"
        f".{class_name} .markdown-preview-view .mermaid,\n"
        f".{class_name} .markdown-preview-section > div:has(> .mermaid),\n"
        f".{class_name} .markdown-preview-section > div:has(> .block-language-mermaid),\n"
        "/* Live Preview: mermaid inside CodeMirror 6 embed blocks. */\n"
        f".{class_name} .cm-preview-code-block.cm-lang-mermaid,\n"
        f".{class_name} .cm-embed-block .mermaid {{\n"
        f"  width: calc(100vw - {buffer_px}) !important;\n"
        f"  max-width: calc(100vw - {buffer_px}) !important;\n"
        "  position: relative !important;\n"
        "  left: 50% !important;\n"
        "  transform: translateX(-50%) !important;\n"
        "}\n"
        "\n"
        "/* Scale the rendered SVG up to fill the widened container. */\n"
        f".{class_name} .block-language-mermaid svg,\n"
        f".{class_name} .mermaid svg,\n"
        f".{class_name} .cm-preview-code-block.cm-lang-mermaid svg {{\n"
        "  max-width: 100% !important;\n"
        "  width: 100% !important;\n"
        "  height: auto !important;\n"
        "}\n"
    )


def _styling_container_breakout(details: dict) -> str:
    class_name = str(details.get("class_name") or "wide-page")
    target = str(details.get("target_selector") or ".block-language-mermaid")
    buffer_px = str(details.get("sidebar_buffer") or "400px")
    return (
        f"/* Break `{target}` out of the readable-line-width container\n"
        f" * when its note has `cssclasses: [{class_name}]`. Generic pattern\n"
        " * applicable to mermaid, callouts, tables, code blocks, etc. */\n"
        f".{class_name} {target} {{\n"
        f"  width: calc(100vw - {buffer_px}) !important;\n"
        f"  max-width: calc(100vw - {buffer_px}) !important;\n"
        "  position: relative !important;\n"
        "  left: 50% !important;\n"
        "  transform: translateX(-50%) !important;\n"
        "}\n"
    )


def _styling(intent: str, title: str, details: dict, profile: Profile) -> GeneratedSnippet:
    key = intent.split("/")[-1] if "/" in intent else intent
    notes = list(_STYLING_COMMON_NOTES)
    hints: list[str] = []

    if key in {"cssclasses-frontmatter", "cssclasses", "frontmatter"}:
        markdown = _styling_cssclasses_frontmatter(details)
    elif key in {"file-line-width-override", "file-line-width", "line-width"}:
        markdown = _styling_file_line_width_override(details)
        notes.append("Minimal theme uses --line-width; this snippet sets both.")
    elif key in {"wide-page-snippet", "wide-page", "mermaid-breakout"}:
        markdown = _styling_wide_page_snippet(details)
        notes.append("Tune the sidebar buffer (default 400px) to taste: larger = more margin.")
    elif key in {"container-breakout", "breakout"}:
        markdown = _styling_container_breakout(details)
        notes.append("Works for any block-level wrapper, not just mermaid.")
    else:
        markdown = _styling_wide_page_snippet(details)
        notes.append(f"Unknown styling intent '{intent}'; defaulting to wide-page-snippet.")

    return GeneratedSnippet(
        pack="styling",
        intent=intent,
        markdown=markdown,
        notes=notes,
        profile_hints=hints,
    )
