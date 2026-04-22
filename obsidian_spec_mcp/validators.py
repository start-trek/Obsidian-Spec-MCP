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
DATAVIEW_BLOCK_RE = re.compile(r"```dataview\n.*?```", re.DOTALL)
DATAVIEWJS_BLOCK_RE = re.compile(r"```dataviewjs\n.*?```", re.DOTALL)
DATACORE_BLOCK_RE = re.compile(r"```datacore\n.*?```", re.DOTALL)
INLINE_DATAVIEW_RE = re.compile(r"`=[^`]+`")
CALL_OUT_RE = re.compile(r"^> \[![^\]]+\]", re.MULTILINE)
WIKILINK_RE = re.compile(r"(?<!!)\[\[[^\]]+\]\]")
EMBED_RE = re.compile(r"!\[\[[^\]]+\]\]")
INLINE_MD_LINK_RE = re.compile(r"\[[^\]]+\]\((?!https?://|mailto:)[^)]+\)")
YAML_START_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
MERMAID_BLOCK_RE = re.compile(r"^(?P<indent>[ \t]*)```mermaid[ \t]*\n(?P<body>.*?)\n(?P=indent)```", re.DOTALL | re.MULTILINE)
MERMAID_OPEN_FENCE_RE = re.compile(r"^[ \t]*```mermaid\b", re.MULTILINE)

MERMAID_DIAGRAM_KEYWORDS = {
    "flowchart",
    "graph",
    "sequenceDiagram",
    "classDiagram",
    "classDiagram-v2",
    "stateDiagram",
    "stateDiagram-v2",
    "erDiagram",
    "journey",
    "gantt",
    "pie",
    "gitGraph",
    "mindmap",
    "timeline",
    "quadrantChart",
    "requirementDiagram",
    "C4Context",
    "C4Container",
    "C4Component",
    "C4Dynamic",
    "C4Deployment",
    "sankey-beta",
    "xychart-beta",
    "block-beta",
    "packet-beta",
    "architecture-beta",
}
MERMAID_SPECIAL_IN_LABEL_RE = re.compile(r"[/#:()]")
CSSCLASS_SINGULAR_RE = re.compile(r"^cssclass\s*:\s*", re.MULTILINE)
CSSCLASSES_PLURAL_RE = re.compile(r"^cssclasses\s*:\s*", re.MULTILINE)

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
        elif pack == "dataview":
            issues.extend(_validate_dataview(markdown, profile))
        elif pack == "datacore":
            issues.extend(_validate_datacore(markdown, profile))
        elif pack == "mermaid":
            issues.extend(_validate_mermaid(markdown, profile))
        elif pack == "styling":
            issues.extend(_validate_styling(markdown, profile))

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


def _validate_dataview(markdown: str, profile: Profile) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    # Check for unclosed dataview blocks (not dataviewjs)
    if "```dataview\n" in markdown and not DATAVIEW_BLOCK_RE.search(markdown):
        issues.append(
            ValidationIssue(
                pack="dataview",
                severity="error",
                message="Dataview block is not properly closed.",
                suggestion="Use fenced blocks with language dataview.",
            )
        )
    if "```dataviewjs\n" in markdown and not DATAVIEWJS_BLOCK_RE.search(markdown):
        issues.append(
            ValidationIssue(
                pack="dataview",
                severity="error",
                message="DataviewJS block is not properly closed.",
                suggestion="Use fenced blocks with language dataviewjs.",
            )
        )
    if "`= " in markdown or "`=" in markdown:
        if not INLINE_DATAVIEW_RE.search(markdown):
            issues.append(
                ValidationIssue(
                    pack="dataview",
                    severity="warning",
                    message="Possible inline Dataview expression found but syntax appears malformed.",
                    suggestion="Use backtick-equals syntax like `= this.title`.",
                )
            )
    for match in DATAVIEW_BLOCK_RE.finditer(markdown):
        body = match.group(0)
        if "FROM" not in body.upper() and "TABLE" in body.upper():
            issues.append(
                ValidationIssue(
                    pack="dataview",
                    severity="info",
                    message="Dataview query without FROM clause will scan all files (may be slow).",
                    suggestion="Add a FROM clause to limit the query scope.",
                )
            )
    return issues


def _validate_datacore(markdown: str, profile: Profile) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if "```datacore" in markdown and not DATACORE_BLOCK_RE.search(markdown):
        issues.append(
            ValidationIssue(
                pack="datacore",
                severity="error",
                message="Datacore block is not properly closed.",
                suggestion="Use fenced blocks with language datacore.",
            )
        )
    for match in DATACORE_BLOCK_RE.finditer(markdown):
        body = match.group(0)
        if "view:" not in body.lower():
            issues.append(
                ValidationIssue(
                    pack="datacore",
                    severity="warning",
                    message="Datacore block missing 'view' declaration.",
                    suggestion="Specify view type like 'view: table' or 'view: list'.",
                )
            )
        if "from:" not in body.lower():
            issues.append(
                ValidationIssue(
                    pack="datacore",
                    severity="info",
                    message="Datacore block without 'from' clause may scan all files.",
                    suggestion="Add 'from: #tag' or 'from: folder' to limit scope.",
                )
            )
    return issues


def _validate_mermaid(markdown: str, profile: Profile) -> list[ValidationIssue]:
    """Validate Mermaid diagram blocks.

    Heuristic checks only; not a full Mermaid grammar parser. Targets the most
    common breakages observed in Obsidian: unclosed fences, unknown diagram
    keywords, unbalanced brackets, and unquoted special characters in flowchart
    node labels (which produce 'Lexical error on line N. Unrecognized text.').
    """
    issues: list[ValidationIssue] = []

    open_fences = len(MERMAID_OPEN_FENCE_RE.findall(markdown))
    closed_blocks = len(MERMAID_BLOCK_RE.findall(markdown))
    if open_fences > closed_blocks:
        issues.append(
            ValidationIssue(
                pack="mermaid",
                severity="error",
                message="Mermaid block is not properly closed.",
                suggestion="Close the fenced block with a matching ``` on its own line.",
            )
        )
        return issues
    if open_fences == 0:
        return issues
    allowed = set(profile.mermaid_allowed_diagrams) if profile.mermaid_allowed_diagrams else None
    for match in MERMAID_BLOCK_RE.finditer(markdown):
        body = match.group("body")
        block_start_line = markdown[: match.start()].count("\n") + 1
        issues.extend(_validate_mermaid_block(body, block_start_line, profile, allowed))
    return issues


def _validate_mermaid_block(
    body: str,
    block_start_line: int,
    profile: Profile,
    allowed: set[str] | None,
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    body_lines = body.splitlines()
    fence_line = block_start_line
    first_nonblank_idx = next(
        (i for i, line in enumerate(body_lines) if line.strip() and not line.strip().startswith("%%")),
        None,
    )
    if first_nonblank_idx is None:
        issues.append(
            ValidationIssue(
                pack="mermaid",
                severity="warning",
                line=fence_line,
                message="Empty mermaid block.",
                suggestion="Add a diagram type line such as 'flowchart TD'.",
            )
        )
        return issues

    first_line = body_lines[first_nonblank_idx].strip()
    first_token = first_line.split()[0] if first_line else ""
    diagram_line = fence_line + 1 + first_nonblank_idx
    if first_token not in MERMAID_DIAGRAM_KEYWORDS:
        issues.append(
            ValidationIssue(
                pack="mermaid",
                severity="error",
                line=diagram_line,
                message=f"Unknown Mermaid diagram keyword: {first_token!r}.",
                suggestion=(
                    "Start the block with one of: flowchart, graph, sequenceDiagram, "
                    "classDiagram, stateDiagram-v2, erDiagram, gantt, pie, gitGraph, "
                    "mindmap, timeline, quadrantChart, requirementDiagram, C4Context."
                ),
            )
        )
        return issues

    if allowed is not None and first_token not in allowed:
        issues.append(
            ValidationIssue(
                pack="mermaid",
                severity="warning",
                line=diagram_line,
                message=f"Diagram type {first_token!r} is not in the profile's mermaid_allowed_diagrams list.",
                suggestion="Add the diagram type to the profile or switch to an allowed one.",
            )
        )

    diagram_type = first_token
    diagram_body_lines = body_lines[first_nonblank_idx + 1 :]
    diagram_body_offset = fence_line + 1 + first_nonblank_idx + 1

    if diagram_type in {"flowchart", "graph"}:
        issues.extend(
            _validate_mermaid_flowchart(
                diagram_body_lines,
                start_line=diagram_body_offset,
                profile=profile,
            )
        )
        issues.extend(_check_bracket_balance(diagram_body_lines, start_line=diagram_body_offset))
    return issues


def _validate_mermaid_flowchart(
    body_lines: list[str],
    start_line: int,
    profile: Profile,
) -> list[ValidationIssue]:
    """Flowchart-specific checks: unquoted special chars in shape labels."""
    issues: list[ValidationIssue] = []
    shape_label_re = re.compile(
        r"(?P<open>\{\{|\[\[|\[\(|\(\(|\[|\(|\{)(?P<label>[^\]\)\}\n]*?)(?P<close>\}\}|\]\]|\)\]|\)\)|\]|\)|\})"
    )
    for offset, line in enumerate(body_lines):
        line_no = start_line + offset
        stripped = line.strip()
        if not stripped or stripped.startswith("%%"):
            continue
        if stripped.startswith("class ") or stripped.startswith("classDef ") or stripped.startswith("style ") or stripped.startswith("linkStyle ") or stripped.startswith("click "):
            continue
        if stripped.startswith("subgraph ") or stripped == "end" or stripped.startswith("direction "):
            continue
        for m in shape_label_re.finditer(line):
            label = m.group("label")
            if not label:
                continue
            stripped_label = label.strip()
            if stripped_label.startswith('"') and stripped_label.endswith('"'):
                continue
            if MERMAID_SPECIAL_IN_LABEL_RE.search(stripped_label):
                offending = MERMAID_SPECIAL_IN_LABEL_RE.search(stripped_label).group(0)
                issues.append(
                    ValidationIssue(
                        pack="mermaid",
                        severity="error",
                        line=line_no,
                        message=(
                            f"Unquoted special character {offending!r} inside flowchart node label "
                            f"{m.group(0)!r}. Mermaid's lexer will reject this."
                        ),
                        suggestion=(
                            f'Wrap the label in double quotes, e.g. {m.group("open")}"{stripped_label}"{m.group("close")}.'
                        ),
                    )
                )
    return issues


def _check_bracket_balance(body_lines: list[str], start_line: int) -> list[ValidationIssue]:
    """Approximate balance check for the diagram body, ignoring quoted strings and comments."""
    issues: list[ValidationIssue] = []
    counts = {"[": 0, "]": 0, "(": 0, ")": 0, "{": 0, "}": 0}
    for offset, raw_line in enumerate(body_lines):
        stripped = raw_line.strip()
        if stripped.startswith("%%"):
            continue
        scrubbed: list[str] = []
        in_quote = False
        for ch in raw_line:
            if ch == '"':
                in_quote = not in_quote
                continue
            if not in_quote:
                scrubbed.append(ch)
        line_text = "".join(scrubbed)
        for ch in line_text:
            if ch in counts:
                counts[ch] += 1
    pairs = [("[", "]"), ("(", ")"), ("{", "}")]
    names = {"[": "square brackets", "(": "parentheses", "{": "curly braces"}
    for opener, closer in pairs:
        if counts[opener] != counts[closer]:
            issues.append(
                ValidationIssue(
                    pack="mermaid",
                    severity="error",
                    line=start_line,
                    message=(
                        f"Unbalanced {names[opener]} in mermaid block "
                        f"({counts[opener]} '{opener}' vs {counts[closer]} '{closer}')."
                    ),
                    suggestion=f"Ensure every '{opener}' has a matching '{closer}'.",
                )
            )
    return issues


def _validate_styling(markdown: str, profile: Profile) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    # Only check frontmatter content, not snippet docs that may discuss the deprecated key.
    frontmatter_match = YAML_START_RE.match(markdown)
    if not frontmatter_match:
        return issues
    frontmatter = frontmatter_match.group(0)
    # Match `cssclass:` exactly (not `cssclasses:`) at the start of a frontmatter line.
    for match in CSSCLASS_SINGULAR_RE.finditer(frontmatter):
        # Skip if the match is actually part of `cssclasses:` (handled by the negative below).
        line_start = frontmatter.rfind("\n", 0, match.start()) + 1
        line_text = frontmatter[line_start : frontmatter.find("\n", match.end())]
        if line_text.lstrip().startswith("cssclasses"):
            continue
        line_no = frontmatter.count("\n", 0, match.start()) + 1
        issues.append(
            ValidationIssue(
                pack="styling",
                severity="info",
                line=line_no,
                message="`cssclass:` (singular) is deprecated in Obsidian frontmatter.",
                suggestion="Use the plural list form: `cssclasses:` with a YAML list of values.",
            )
        )
    return issues
