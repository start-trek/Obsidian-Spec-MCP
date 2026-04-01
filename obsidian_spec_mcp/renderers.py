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
