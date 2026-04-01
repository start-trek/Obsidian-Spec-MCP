from __future__ import annotations

import re
from typing import Iterable

from .models import Profile, ValidationIssue, ValidationReport
from .registry import normalize_pack_name

CHECKBOX_RE = re.compile(r"^\s*[-*+]\s+\[[^\]]\]\s+")
TASKS_BLOCK_RE = re.compile(r"```tasks\n(?P<body>.*?)\n```", re.DOTALL)
TEMPLATER_TAG_RE = re.compile(r"<%[*_-]?(.*?)%>", re.DOTALL)
QUICKADD_TOKEN_RE = re.compile(r"{{[^{}]+}}")
META_BIND_INLINE_RE = re.compile(r"\b(?:INPUT|VIEW|BUTTON)\[[^\]]+\]")
JS_ENGINE_BLOCK_RE = re.compile(r"```js-engine\n.*?\n```", re.DOTALL)
CALL_OUT_RE = re.compile(r"^> \[![^\]]+\]", re.MULTILINE)
WIKILINK_RE = re.compile(r"(?<!!)\[\[[^\]]+\]\]")
EMBED_RE = re.compile(r"!\[\[[^\]]+\]\]")
INLINE_MD_LINK_RE = re.compile(r"\[[^\]]+\]\((?!https?://|mailto:)[^)]+\)")
YAML_START_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)

PRIORITY_MARKERS = ["🔺", "⏫", "🔼", "🔽", "⏬"]
DATE_MARKERS = ["📅", "⏳", "🛫", "✅", "➕"]


def validate_markdown(markdown: str, packs: Iterable[str], profile: Profile | None = None) -> ValidationReport:
    normalized_packs = [normalize_pack_name(pack) for pack in packs]
    issues: list[ValidationIssue] = []
    profile = profile or Profile(name="runtime")

    for pack in normalized_packs:
        if pack == "core":
            issues.extend(_validate_core(markdown, profile))
        elif pack == "tasks":
            issues.extend(_validate_tasks(markdown, profile))
        elif pack == "templater":
            issues.extend(_validate_templater(markdown, profile))
        elif pack == "quickadd":
            issues.extend(_validate_quickadd(markdown, profile))
        elif pack == "meta_bind":
            issues.extend(_validate_meta_bind(markdown, profile))
        elif pack == "js_engine":
            issues.extend(_validate_js_engine(markdown, profile))
        elif pack == "docxer":
            issues.extend(_validate_docxer(markdown, profile))
        elif pack == "linter":
            issues.extend(_validate_linter(markdown, profile))

    valid = not any(issue.severity == "error" for issue in issues)
    summary = "Validation passed." if valid else "Validation found one or more errors."
    return ValidationReport(
        valid=valid,
        packs_checked=normalized_packs,
        issues=issues,
        summary=summary,
        effective_profile=profile.model_dump(mode="json"),
    )


def _validate_core(markdown: str, profile: Profile) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if "[!" in markdown and not CALL_OUT_RE.search(markdown):
        issues.append(
            ValidationIssue(
                pack="core",
                severity="warning",
                message="Possible callout marker found, but no valid Obsidian callout block was detected.",
                suggestion="Use blockquote syntax like > [!info] Title.",
            )
        )
    if profile.use_wikilinks and INLINE_MD_LINK_RE.search(markdown) and not WIKILINK_RE.search(markdown):
        issues.append(
            ValidationIssue(
                pack="core",
                severity="info",
                message="Profile prefers wikilinks for internal references, but markdown links were detected.",
                suggestion="Prefer [[Note Name]] for vault-internal links.",
            )
        )
    if profile.prefer_properties and not YAML_START_RE.search(markdown) and any(token in markdown for token in ["tags:", "aliases:", "cssclasses:"]):
        issues.append(
            ValidationIssue(
                pack="core",
                severity="info",
                message="Property-like keys were found outside frontmatter while the profile prefers properties.",
                suggestion="Move note metadata into YAML frontmatter or Properties.",
            )
        )
    return issues


def _validate_tasks(markdown: str, profile: Profile) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    allowed_symbols = {" ", "x", "X"}
    for item in profile.tasks_custom_statuses:
        symbol = str(item.get("symbol", ""))
        if symbol:
            allowed_symbols.add(symbol)
    lines = markdown.splitlines()
    for idx, line in enumerate(lines, start=1):
        if any(marker in line for marker in PRIORITY_MARKERS + DATE_MARKERS + ["🔁"]):
            if not CHECKBOX_RE.match(line):
                issues.append(
                    ValidationIssue(
                        pack="tasks",
                        severity="error",
                        line=idx,
                        message="Tasks metadata markers appear on a line that is not a markdown checklist item.",
                        suggestion="Start Tasks entries like - [ ] My task 📅 2026-04-05.",
                    )
                )
        match = re.match(r"^\s*[-*+]\s+\[([^\]])\]", line)
        if match:
            symbol = match.group(1)
            if symbol not in allowed_symbols:
                issues.append(
                    ValidationIssue(
                        pack="tasks",
                        severity="warning",
                        line=idx,
                        message=f"Checklist status '{symbol}' is not present in the effective Tasks status set.",
                        suggestion="Update the runtime Tasks config or use a configured status symbol.",
                    )
                )
        if line.strip().startswith(("- [", "* [", "+ [")) and "🔁" in line and not re.search(r"🔁\s+every\b", line):
            issues.append(
                ValidationIssue(
                    pack="tasks",
                    severity="warning",
                    line=idx,
                    message="Recurring task marker found without the expected 'every ...' phrase.",
                    suggestion="Use syntax like 🔁 every week.",
                )
            )
    for match in TASKS_BLOCK_RE.finditer(markdown):
        body = match.group("body")
        stripped = [line.strip() for line in body.splitlines() if line.strip()]
        if not stripped:
            issues.append(
                ValidationIssue(
                    pack="tasks",
                    severity="warning",
                    message="Empty tasks query block.",
                    suggestion="Add instructions like not done, due today, sort by due.",
                )
            )
        if profile.tasks_append_global_filter_to_queries and profile.tasks_global_filter:
            if not any(profile.tasks_global_filter in line for line in stripped):
                issues.append(
                    ValidationIssue(
                        pack="tasks",
                        severity="info",
                        message="Profile expects Tasks query blocks to include the global filter.",
                        suggestion=f"Add a line containing {profile.tasks_global_filter!r}.",
                    )
                )
    if "```tasks" in markdown and not TASKS_BLOCK_RE.search(markdown):
        issues.append(
            ValidationIssue(
                pack="tasks",
                severity="error",
                message="Unclosed or malformed tasks fenced block.",
                suggestion="Wrap task queries in a fenced code block with language tasks.",
            )
        )
    return issues


def _validate_templater(markdown: str, profile: Profile) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    open_count = markdown.count("<%")
    close_count = markdown.count("%>")
    if open_count != close_count:
        issues.append(
            ValidationIssue(
                pack="templater",
                severity="error",
                message="Unbalanced Templater tags.",
                suggestion="Make sure each <% or <%* has a matching %>.",
            )
        )
    if "<%" in markdown and not TEMPLATER_TAG_RE.search(markdown):
        issues.append(
            ValidationIssue(
                pack="templater",
                severity="warning",
                message="Templater-like tag detected but no valid command found.",
            )
        )
    if profile.templater_user_scripts:
        found = [name for name in profile.templater_user_scripts if name in markdown]
        if "tp.user." in markdown and not found:
            issues.append(
                ValidationIssue(
                    pack="templater",
                    severity="info",
                    message="Template references tp.user helpers that are not listed in the effective profile.",
                    suggestion="Register known helpers in the Templater runtime config.",
                )
            )
    return issues


def _validate_quickadd(markdown: str, profile: Profile) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if markdown.count("{{") != markdown.count("}}"):
        issues.append(
            ValidationIssue(
                pack="quickadd",
                severity="error",
                message="Unbalanced QuickAdd double-brace placeholders.",
                suggestion="Use balanced placeholders like {{DATE}} or {{VALUE:project}}.",
            )
        )
    tokens = QUICKADD_TOKEN_RE.findall(markdown)
    if "{{" in markdown and not tokens:
        issues.append(
            ValidationIssue(
                pack="quickadd",
                severity="warning",
                message="Placeholder braces detected but no valid QuickAdd token matched.",
            )
        )
    known = set(profile.quickadd_known_variables)
    for token in tokens:
        if token.startswith("{{VALUE:"):
            name = token[len("{{VALUE:"):-2]
            if known and name not in known:
                issues.append(
                    ValidationIssue(
                        pack="quickadd",
                        severity="info",
                        message=f"QuickAdd variable '{name}' is not in the effective known-variable set.",
                        suggestion="Add it to the runtime QuickAdd config if it is valid in your vault.",
                    )
                )
    return issues


def _validate_meta_bind(markdown: str, profile: Profile) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if any(token in markdown for token in ["INPUT[", "VIEW[", "BUTTON["]) and not META_BIND_INLINE_RE.search(markdown):
        issues.append(
            ValidationIssue(
                pack="meta_bind",
                severity="warning",
                message="Meta Bind token detected but the inline syntax looks malformed.",
                suggestion="Use patterns like INPUT[text:title] or BUTTON[actionName].",
            )
        )
    if profile.meta_bind_field_types and "INPUT[" in markdown:
        for match in re.finditer(r"INPUT\[([^:\]]+)", markdown):
            field_type = match.group(1).strip()
            if field_type not in profile.meta_bind_field_types:
                issues.append(
                    ValidationIssue(
                        pack="meta_bind",
                        severity="info",
                        message=f"Meta Bind field type '{field_type}' is not listed in the effective profile.",
                    )
                )
    return issues


def _validate_js_engine(markdown: str, profile: Profile) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if "```js-engine" in markdown and not JS_ENGINE_BLOCK_RE.search(markdown):
        issues.append(
            ValidationIssue(
                pack="js_engine",
                severity="error",
                message="JS Engine block is not properly closed.",
                suggestion="Use fenced blocks with language js-engine.",
            )
        )
    if profile.js_engine_helpers and "```js-engine" in markdown:
        if not any(helper in markdown for helper in profile.js_engine_helpers):
            issues.append(
                ValidationIssue(
                    pack="js_engine",
                    severity="info",
                    message="JS Engine block does not reference any configured helper names.",
                )
            )
    return issues


def _validate_docxer(markdown: str, profile: Profile) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if ".docx" in markdown and ".md" not in markdown:
        issues.append(
            ValidationIssue(
                pack="docxer",
                severity="info",
                message="Docxer references usually imply a source .docx and a markdown output note.",
            )
        )
    return issues


def _validate_linter(markdown: str, profile: Profile) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    expectations = profile.linter_expectations or {}
    headings = [line for line in markdown.splitlines() if line.startswith("#")]
    if expectations.get("single_h1", True) and len([line for line in headings if line.startswith("# ")]) > 1:
        issues.append(
            ValidationIssue(
                pack="linter",
                severity="warning",
                message="Multiple H1 headings found.",
                suggestion="Many Linter setups expect a single top-level heading.",
            )
        )
    if expectations.get("collapse_extra_blank_lines", True) and "\n\n\n" in markdown:
        issues.append(
            ValidationIssue(
                pack="linter",
                severity="info",
                message="Triple blank lines found.",
                suggestion="Consider collapsing extra blank lines if your Linter profile enforces spacing.",
            )
        )
    if expectations.get("prefer_yaml_frontmatter") and "tags:" in markdown and not YAML_START_RE.search(markdown):
        issues.append(
            ValidationIssue(
                pack="linter",
                severity="info",
                message="Linter profile prefers YAML frontmatter, but metadata-like keys were found outside it.",
            )
        )
    return issues
