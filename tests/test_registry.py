"""Tests for obsidian_spec_mcp.registry"""
from __future__ import annotations

import pytest

from obsidian_spec_mcp.registry import (
    available_packs,
    get_pack,
    load_doc_text,
    load_profile,
    make_snippet,
    normalize_pack_name,
    search_docs,
)


class TestNormalizePackName:
    def test_identity(self):
        assert normalize_pack_name("core") == "core"
        assert normalize_pack_name("tasks") == "tasks"

    def test_alias_doxcer(self):
        assert normalize_pack_name("doxcer") == "docxer"

    def test_alias_metabind(self):
        assert normalize_pack_name("metabind") == "meta_bind"

    def test_alias_jsengine(self):
        assert normalize_pack_name("jsengine") == "js_engine"

    def test_alias_obsidian(self):
        assert normalize_pack_name("obsidian") == "core"
        assert normalize_pack_name("core_obsidian") == "core"

    def test_strips_whitespace(self):
        assert normalize_pack_name("  tasks  ") == "tasks"

    def test_case_insensitive(self):
        assert normalize_pack_name("Tasks") == "tasks"
        assert normalize_pack_name("DOXCER") == "docxer"

    def test_hyphens_to_underscores(self):
        assert normalize_pack_name("meta-bind") == "meta_bind"
        assert normalize_pack_name("js-engine") == "js_engine"


class TestAvailablePacks:
    def test_returns_all_eight(self):
        packs = available_packs()
        assert len(packs) == 8

    def test_pack_names(self):
        names = {p.name for p in available_packs()}
        assert names == {"core", "tasks", "templater", "quickadd", "meta_bind", "js_engine", "docxer", "linter"}

    def test_enabled_only(self):
        enabled = available_packs(enabled_only=True)
        assert len(enabled) >= 1
        assert all(p.enabled_by_default for p in enabled)


class TestGetPack:
    def test_known_pack(self):
        pack = get_pack("tasks")
        assert pack.name == "tasks"
        assert pack.title == "Tasks"

    def test_alias_resolution(self):
        pack = get_pack("doxcer")
        assert pack.name == "docxer"

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown pack"):
            get_pack("nonexistent_plugin")


class TestLoadProfile:
    def test_default_profile(self):
        profile = load_profile("default")
        assert profile.name == "default"
        assert isinstance(profile.default_packs, list)
        assert "core" in profile.default_packs

    def test_missing_profile_raises(self):
        with pytest.raises(Exception):
            load_profile("does_not_exist_xyz")


class TestLoadDocText:
    def test_core_doc(self):
        text = load_doc_text("core")
        assert len(text) > 0
        assert isinstance(text, str)

    def test_tasks_doc(self):
        text = load_doc_text("tasks")
        assert len(text) > 0

    def test_all_packs_have_docs(self):
        for name in ["core", "tasks", "templater", "quickadd", "meta_bind", "js_engine", "docxer", "linter"]:
            text = load_doc_text(name)
            assert len(text) > 0, f"Doc for {name} should not be empty"

    def test_alias_doc(self):
        text = load_doc_text("doxcer")
        assert len(text) > 0


class TestSearchDocs:
    def test_keyword_hit(self):
        hits = search_docs("checklist")
        assert len(hits) >= 1
        assert hits[0].score > 0

    def test_empty_query(self):
        hits = search_docs("")
        assert len(hits) == 8

    def test_filter_by_pack(self):
        hits = search_docs("syntax", packs=["tasks"])
        for hit in hits:
            assert hit.pack == "tasks"

    def test_no_match(self):
        hits = search_docs("zzzznonexistenttermzzzz")
        assert len(hits) == 0

    def test_results_sorted_by_score(self):
        hits = search_docs("markdown")
        scores = [h.score for h in hits]
        assert scores == sorted(scores, reverse=True)


class TestMakeSnippet:
    def test_basic(self):
        result = make_snippet("Hello world foo bar", ["hello"])
        assert "Hello" in result

    def test_empty_text(self):
        assert make_snippet("", ["foo"]) == ""

    def test_no_terms(self):
        result = make_snippet("Some text here", [])
        assert result.startswith("Some")
