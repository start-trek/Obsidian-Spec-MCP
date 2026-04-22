"""Tests for the Mermaid pack: registry, validator, and renderer."""
from __future__ import annotations

from pathlib import Path

import pytest

from obsidian_spec_mcp.models import Profile
from obsidian_spec_mcp.registry import (
    PACKS,
    get_pack,
    load_doc_text,
    normalize_pack_name,
)
from obsidian_spec_mcp.renderers import generate_snippet
from obsidian_spec_mcp.validators import validate_markdown


FIXTURES = Path(__file__).parent / "fixtures"


def _profile(**overrides) -> Profile:
    defaults = dict(name="test")
    defaults.update(overrides)
    return Profile(**defaults)


class TestMermaidRegistry:
    def test_mermaid_registered(self):
        assert "mermaid" in PACKS
        pack = PACKS["mermaid"]
        assert pack.name == "mermaid"
        assert pack.enabled_by_default is True

    def test_aliases_resolve(self):
        assert normalize_pack_name("mermaidjs") == "mermaid"
        assert normalize_pack_name("mermaid_js") == "mermaid"
        assert normalize_pack_name("diagram") == "mermaid"
        assert normalize_pack_name("mmd") == "mermaid"

    def test_get_pack(self):
        pack = get_pack("mermaid")
        assert "flowchart" in pack.description.lower()

    def test_doc_text_nonempty(self):
        text = load_doc_text("mermaid")
        assert "flowchart" in text.lower()
        assert "special characters" in text.lower()


class TestMermaidValidatorBasics:
    def test_valid_flowchart_passes(self):
        md = (
            "```mermaid\n"
            "flowchart TD\n"
            "    A[Start] --> B[End]\n"
            "```"
        )
        report = validate_markdown(md, ["mermaid"], _profile())
        assert report.valid, [i.message for i in report.issues]

    def test_valid_sequence_passes(self):
        md = (
            "```mermaid\n"
            "sequenceDiagram\n"
            "    Alice->>Bob: Hello\n"
            "```"
        )
        report = validate_markdown(md, ["mermaid"], _profile())
        assert report.valid

    def test_no_mermaid_blocks_is_noop(self):
        md = "Some plain markdown with no code blocks."
        report = validate_markdown(md, ["mermaid"], _profile())
        assert report.valid
        assert len([i for i in report.issues if i.pack == "mermaid"]) == 0

    def test_unclosed_fence_is_error(self):
        md = "```mermaid\nflowchart TD\n    A --> B"
        report = validate_markdown(md, ["mermaid"], _profile())
        assert not report.valid
        assert any("not properly closed" in i.message for i in report.issues)

    def test_unknown_diagram_keyword_is_error(self):
        md = "```mermaid\nnotADiagram TD\n    A --> B\n```"
        report = validate_markdown(md, ["mermaid"], _profile())
        assert not report.valid
        assert any("Unknown Mermaid diagram keyword" in i.message for i in report.issues)

    def test_empty_block_is_warning(self):
        md = "```mermaid\n\n```"
        report = validate_markdown(md, ["mermaid"], _profile())
        warnings = [i for i in report.issues if i.severity == "warning"]
        assert any("Empty mermaid block" in i.message for i in warnings)


class TestMermaidFlowchartLabelEscaping:
    def test_unquoted_slash_in_diamond_is_error(self):
        """This reproduces the exact user-reported bug: {/route"""
        md = (
            "```mermaid\n"
            "flowchart TD\n"
            "    A[context, text, links, rationale] --> C\n"
            "    C --> D{/route}\n"
            "```"
        )
        report = validate_markdown(md, ["mermaid"], _profile())
        assert not report.valid
        errors = [i for i in report.issues if i.severity == "error"]
        assert any("/" in i.message and "special character" in i.message.lower() for i in errors)

    def test_quoted_slash_in_diamond_passes(self):
        md = (
            "```mermaid\n"
            "flowchart TD\n"
            "    C --> D{\"/route\"}\n"
            "```"
        )
        report = validate_markdown(md, ["mermaid"], _profile())
        assert report.valid, [i.message for i in report.issues]

    def test_unquoted_hash_in_label_is_error(self):
        md = (
            "```mermaid\n"
            "flowchart TD\n"
            "    A[tag: #project] --> B\n"
            "```"
        )
        report = validate_markdown(md, ["mermaid"], _profile())
        assert not report.valid

    def test_unquoted_paren_in_label_is_error(self):
        md = (
            "```mermaid\n"
            "flowchart TD\n"
            "    A[foo (bar)] --> B\n"
            "```"
        )
        report = validate_markdown(md, ["mermaid"], _profile())
        assert not report.valid

    def test_class_line_is_not_validated_as_label(self):
        """`class A internal-link;` is a Mermaid directive, not a label."""
        md = (
            "```mermaid\n"
            "flowchart LR\n"
            "    A[Project Note] --> B[Reference]\n"
            "    class A,B internal-link;\n"
            "```"
        )
        report = validate_markdown(md, ["mermaid"], _profile())
        assert report.valid, [i.message for i in report.issues]


class TestMermaidBracketBalance:
    def test_unbalanced_square_brackets(self):
        md = (
            "```mermaid\n"
            "flowchart TD\n"
            "    A[Start --> B\n"
            "```"
        )
        report = validate_markdown(md, ["mermaid"], _profile())
        assert not report.valid
        assert any("Unbalanced" in i.message for i in report.issues)


class TestMermaidProfileAllowedDiagrams:
    def test_disallowed_diagram_is_warning(self):
        profile = _profile(mermaid_allowed_diagrams=["flowchart", "sequenceDiagram"])
        md = "```mermaid\npie title x\n    \"a\" : 10\n```"
        report = validate_markdown(md, ["mermaid"], profile)
        warnings = [i for i in report.issues if i.severity == "warning"]
        assert any("not in the profile" in i.message for i in warnings)

    def test_allowed_diagram_no_warning(self):
        profile = _profile(mermaid_allowed_diagrams=["flowchart", "pie"])
        md = "```mermaid\npie title x\n    \"a\" : 10\n```"
        report = validate_markdown(md, ["mermaid"], profile)
        allowed_warnings = [i for i in report.issues if "not in the profile" in i.message]
        assert len(allowed_warnings) == 0


class TestMermaidFixture:
    def test_bad_flowchart_fixture_line_4_error(self):
        md = (FIXTURES / "mermaid_bad_flowchart.md").read_text(encoding="utf-8")
        report = validate_markdown(md, ["mermaid"], _profile())
        assert not report.valid
        errors = [i for i in report.issues if i.severity == "error"]
        assert len(errors) >= 1


class TestMermaidRenderer:
    @pytest.mark.parametrize(
        "intent",
        [
            "mermaid/flowchart",
            "mermaid/sequence",
            "mermaid/class",
            "mermaid/state",
            "mermaid/er",
            "mermaid/gantt",
            "mermaid/pie",
            "mermaid/mindmap",
            "mermaid/timeline",
            "mermaid/quadrant",
            "mermaid/gitgraph",
            "mermaid/journey",
            "mermaid/obsidian-linked",
        ],
    )
    def test_snippet_generates_and_validates(self, intent):
        snippet = generate_snippet(pack="mermaid", intent=intent, profile=_profile())
        assert snippet.markdown.startswith("```mermaid")
        assert snippet.markdown.rstrip().endswith("```")
        report = validate_markdown(snippet.markdown, ["mermaid"], _profile())
        assert report.valid, f"Intent {intent!r} produced invalid markdown: {[i.message for i in report.issues]}"

    def test_unknown_intent_falls_back_to_flowchart(self):
        snippet = generate_snippet(pack="mermaid", intent="mermaid/unknown-xyz", profile=_profile())
        assert "flowchart" in snippet.markdown

    def test_notes_mention_quoting(self):
        snippet = generate_snippet(pack="mermaid", intent="mermaid/flowchart", profile=_profile())
        assert any("special characters" in note.lower() or "quote" in note.lower() for note in snippet.notes)
