"""Tests for obsidian_spec_mcp.server — exercises the MCP tool/resource/prompt layer."""
from __future__ import annotations

import json

import pytest

from obsidian_spec_mcp.server import (
    generate_obsidian_snippet,
    get_doc,
    get_effective_profile,
    get_pack_info,
    list_packs,
    normalized_pack_name,
    search_spec,
    validate_obsidian_markdown,
)


class TestListPacks:
    def test_returns_list(self):
        result = list_packs()
        assert isinstance(result, list)
        assert len(result) == 8

    def test_enabled_only(self):
        result = list_packs(enabled_only=True)
        assert len(result) >= 1
        assert all(p["enabled_by_default"] for p in result)


class TestGetPackInfo:
    def test_known_pack(self):
        result = get_pack_info("tasks")
        assert result["name"] == "tasks"
        assert "title" in result

    def test_alias(self):
        result = get_pack_info("doxcer")
        assert result["name"] == "docxer"


class TestSearchSpec:
    def test_returns_hits(self):
        result = search_spec("checklist")
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_pack_filter(self):
        result = search_spec("syntax", packs=["linter"])
        for hit in result:
            assert hit["pack"] == "linter"


class TestGetDoc:
    def test_returns_text(self):
        result = get_doc("core")
        assert isinstance(result, str)
        assert len(result) > 0


class TestGetEffectiveProfile:
    def test_default(self):
        result = get_effective_profile()
        assert "profile" in result
        assert result["profile"]["name"] == "default"
        assert "sources" in result

    def test_with_example_configs(self):
        result = get_effective_profile(
            tasks_path="examples/runtime_configs/tasks.json",
            linter_path="examples/runtime_configs/linter.json",
        )
        loaded_kinds = [s["kind"] for s in result["sources"] if s["loaded"]]
        assert "tasks-config" in loaded_kinds
        assert "linter-config" in loaded_kinds


class TestValidateObsidianMarkdown:
    def test_valid_task(self):
        result = validate_obsidian_markdown(
            markdown="- [x] Done task ⏫ 📅 2026-04-05",
            packs=["tasks"],
        )
        assert result["valid"] is True

    def test_invalid_task(self):
        result = validate_obsidian_markdown(
            markdown="Some text ⏫ 📅 2026-04-05",
            packs=["tasks"],
        )
        assert result["valid"] is False

    def test_multi_pack(self):
        result = validate_obsidian_markdown(
            markdown="- [x] Done\n\n# Title\n\nContent",
            packs=["tasks", "linter"],
        )
        assert "tasks" in result["packs_checked"]
        assert "linter" in result["packs_checked"]

    def test_with_runtime_config(self):
        result = validate_obsidian_markdown(
            markdown="- [/] In progress task",
            packs=["tasks"],
            tasks_path="examples/runtime_configs/tasks.json",
        )
        assert isinstance(result, dict)


class TestGenerateObsidianSnippet:
    def test_task_line(self):
        result = generate_obsidian_snippet(pack="tasks", intent="task-line", title="Buy milk")
        assert result["pack"] == "tasks"
        assert "Buy milk" in result["markdown"]

    def test_templater(self):
        result = generate_obsidian_snippet(pack="templater", intent="template", title="Daily")
        assert result["pack"] == "templater"
        assert "<%" in result["markdown"]

    def test_alias_pack(self):
        result = generate_obsidian_snippet(pack="doxcer", intent="convert", title="Import")
        assert result["pack"] == "docxer"


class TestNormalizedPackName:
    def test_returns_dict(self):
        result = normalized_pack_name("doxcer")
        assert result == {"input": "doxcer", "normalized": "docxer"}

    def test_identity(self):
        result = normalized_pack_name("tasks")
        assert result["normalized"] == "tasks"
