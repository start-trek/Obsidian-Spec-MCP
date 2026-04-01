"""Solo gauntlet tests — exercises every tool against every pack with realistic vault content.

Each pack is tested for:
  - get_pack_info: metadata correctness
  - get_doc: substantive documentation returned
  - search_spec: keyword hits within the pack
  - validate (valid): clean markdown passes
  - validate (invalid): broken markdown catches expected issues
  - generate then re-validate: generated snippets pass their own validator
  - get_effective_profile: runtime config merging

Also covers:
  - Cross-pack validation combos
  - Alias resolution
  - Resource access (via registry functions)
  - Prompt exercising
"""
from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

import pytest

from obsidian_spec_mcp.config import load_effective_profile
from obsidian_spec_mcp.models import PluginConfigPaths, Profile
from obsidian_spec_mcp.registry import (
    available_packs,
    get_pack,
    load_doc_text,
    load_profile,
    normalize_pack_name,
    search_docs,
)
from obsidian_spec_mcp.renderers import generate_snippet
from obsidian_spec_mcp.validators import validate_markdown

# ---------------------------------------------------------------------------
# Paths to test vault configs
# ---------------------------------------------------------------------------
CONFIGS_DIR = Path(__file__).resolve().parent.parent / "test_vault_configs"
VAULT_DIR = Path(__file__).resolve().parent / "fixtures" / "vault"

ALL_PACKS = ["core", "tasks", "templater", "quickadd", "meta_bind", "js_engine", "docxer", "linter"]


def _config_paths(**overrides) -> PluginConfigPaths:
    """Build PluginConfigPaths from the test_vault_configs directory."""
    base = {
        "profile_path": str(CONFIGS_DIR / "profile_overlay.json"),
        "tasks_path": str(CONFIGS_DIR / "tasks.json"),
        "linter_path": str(CONFIGS_DIR / "linter.json"),
        "quickadd_path": str(CONFIGS_DIR / "quickadd.json"),
        "templater_path": str(CONFIGS_DIR / "templater.json"),
        "meta_bind_path": str(CONFIGS_DIR / "meta_bind.json"),
        "js_engine_path": str(CONFIGS_DIR / "js_engine.json"),
        "docxer_path": str(CONFIGS_DIR / "docxer.json"),
    }
    base.update(overrides)
    return PluginConfigPaths(**base)


def _load_vault_note(relative_path: str) -> str:
    """Read a seed note from the test vault."""
    return (VAULT_DIR / relative_path).read_text(encoding="utf-8")


def _effective_profile() -> Profile:
    """Load the full effective profile with all test vault configs."""
    return load_effective_profile("default", _config_paths()).profile


# ===================================================================
# Per-pack metadata and docs
# ===================================================================

class TestPackMetadata:
    """get_pack_info returns correct metadata for every pack."""

    @pytest.mark.parametrize("pack_name", ALL_PACKS)
    def test_pack_info_fields(self, pack_name):
        pack = get_pack(pack_name)
        assert pack.name == pack_name
        assert len(pack.title) > 0
        assert len(pack.description) > 20
        assert isinstance(pack.syntax_kinds, list)
        assert len(pack.syntax_kinds) >= 1
        assert isinstance(pack.docs, list)
        assert len(pack.docs) >= 1
        assert pack.docs[0].url.startswith("http")

    @pytest.mark.parametrize("pack_name", ALL_PACKS)
    def test_doc_is_substantive(self, pack_name):
        text = load_doc_text(pack_name)
        assert len(text) > 100, f"Doc for {pack_name} should be substantive (>100 chars), got {len(text)}"
        assert "Rules" in text or "Purpose" in text


class TestSearchSpec:
    """search_spec returns relevant hits for each pack."""

    PACK_KEYWORDS = {
        "core": "wikilink",
        "tasks": "checklist",
        "templater": "interpolation",
        "quickadd": "placeholder",
        "meta_bind": "input",
        "js_engine": "engine",
        "docxer": "docx",
        "linter": "heading",
    }

    @pytest.mark.parametrize("pack_name", ALL_PACKS)
    def test_keyword_hits_within_pack(self, pack_name):
        keyword = self.PACK_KEYWORDS[pack_name]
        hits = search_docs(keyword, packs=[pack_name])
        assert len(hits) >= 1, f"Expected at least 1 hit for '{keyword}' in {pack_name}"
        assert hits[0].pack == pack_name
        assert hits[0].score > 0


# ===================================================================
# Core pack validation
# ===================================================================

class TestCoreGauntlet:
    def test_valid_note(self):
        md = _load_vault_note("core/Valid Core Note.md")
        report = validate_markdown(md, ["core"], _effective_profile())
        assert report.valid, f"Expected valid, got issues: {[i.message for i in report.issues]}"

    def test_broken_note(self):
        md = _load_vault_note("core/Broken Core Note.md")
        report = validate_markdown(md, ["core"], _effective_profile())
        messages = [i.message for i in report.issues]
        assert any("callout" in m.lower() for m in messages), f"Expected callout issue, got: {messages}"
        assert any("wikilink" in m.lower() or "markdown link" in m.lower() for m in messages), \
            f"Expected wikilink preference issue, got: {messages}"

    def test_generate_then_validate(self):
        snip = generate_snippet("core", "note", title="Generated Core Note", profile=_effective_profile())
        report = validate_markdown(snip.markdown, ["core"], _effective_profile())
        assert report.valid, f"Generated core snippet failed validation: {[i.message for i in report.issues]}"


# ===================================================================
# Tasks pack validation
# ===================================================================

class TestTasksGauntlet:
    def test_valid_note(self):
        md = _load_vault_note("tasks/Valid Tasks Note.md")
        report = validate_markdown(md, ["tasks"], _effective_profile())
        errors = [i for i in report.issues if i.severity == "error"]
        assert len(errors) == 0, f"Expected no errors, got: {[e.message for e in errors]}"

    def test_broken_note_catches_issues(self):
        md = _load_vault_note("tasks/Broken Tasks Note.md")
        report = validate_markdown(md, ["tasks"], _effective_profile())
        messages = " ".join(i.message for i in report.issues)
        assert "not a markdown checklist" in messages.lower(), f"Expected checklist error, got: {messages}"
        assert "empty tasks query" in messages.lower(), f"Expected empty query warning, got: {messages}"

    def test_broken_note_catches_unknown_status(self):
        md = _load_vault_note("tasks/Broken Tasks Note.md")
        profile = _effective_profile()
        report = validate_markdown(md, ["tasks"], profile)
        status_issues = [i for i in report.issues if "status" in i.message.lower()]
        assert len(status_issues) >= 1, "Expected at least one unknown-status warning"

    def test_broken_note_catches_bad_recurrence(self):
        md = _load_vault_note("tasks/Broken Tasks Note.md")
        report = validate_markdown(md, ["tasks"], _effective_profile())
        recurrence = [i for i in report.issues if "every" in i.message.lower()]
        assert len(recurrence) >= 1, "Expected recurrence warning"

    def test_generate_task_line_then_validate(self):
        profile = _effective_profile()
        snip = generate_snippet("tasks", "task-line", title="Gauntlet Task", profile=profile)
        report = validate_markdown(snip.markdown, ["tasks"], profile)
        errors = [i for i in report.issues if i.severity == "error"]
        assert len(errors) == 0, f"Generated task line failed validation: {[e.message for e in errors]}"

    def test_generate_task_query_then_validate(self):
        profile = _effective_profile()
        snip = generate_snippet("tasks", "query", title="Gauntlet Query", profile=profile)
        report = validate_markdown(snip.markdown, ["tasks"], profile)
        errors = [i for i in report.issues if i.severity == "error"]
        assert len(errors) == 0, f"Generated query failed validation: {[e.message for e in errors]}"


# ===================================================================
# Templater pack validation
# ===================================================================

class TestTemplaterGauntlet:
    def test_valid_template(self):
        md = _load_vault_note("templater/Valid Template.md")
        report = validate_markdown(md, ["templater"], _effective_profile())
        assert report.valid, f"Expected valid, got: {[i.message for i in report.issues]}"

    def test_broken_template(self):
        md = _load_vault_note("templater/Broken Template.md")
        report = validate_markdown(md, ["templater"], _effective_profile())
        errors = [i for i in report.issues if i.severity == "error"]
        assert len(errors) >= 1, "Expected unbalanced tag error"
        assert any("unbalanced" in e.message.lower() for e in errors)

    def test_broken_template_unknown_user_script(self):
        md = _load_vault_note("templater/Broken Template.md")
        profile = _effective_profile()
        report = validate_markdown(md, ["templater"], profile)
        user_issues = [i for i in report.issues if "tp.user" in i.message.lower()]
        assert len(user_issues) >= 1, "Expected unknown user script warning"

    def test_generate_then_validate(self):
        profile = _effective_profile()
        snip = generate_snippet("templater", "project-template", title="Gauntlet Template", profile=profile)
        report = validate_markdown(snip.markdown, ["templater"], profile)
        assert report.valid, f"Generated template failed validation: {[i.message for i in report.issues]}"


# ===================================================================
# QuickAdd pack validation
# ===================================================================

class TestQuickAddGauntlet:
    def test_valid_format(self):
        md = _load_vault_note("quickadd/Valid QuickAdd Format.md")
        report = validate_markdown(md, ["quickadd"], _effective_profile())
        assert report.valid, f"Expected valid, got: {[i.message for i in report.issues]}"

    def test_broken_format(self):
        md = _load_vault_note("quickadd/Broken QuickAdd Format.md")
        report = validate_markdown(md, ["quickadd"], _effective_profile())
        errors = [i for i in report.issues if i.severity == "error"]
        assert len(errors) >= 1, "Expected unbalanced brace error"

    def test_unknown_variable(self):
        md = _load_vault_note("quickadd/Broken QuickAdd Format.md")
        profile = _effective_profile()
        report = validate_markdown(md, ["quickadd"], profile)
        var_issues = [i for i in report.issues if "unknown_var_xyz" in i.message or "another_missing_var" in i.message]
        assert len(var_issues) >= 1, "Expected unknown variable info"

    def test_generate_then_validate(self):
        profile = _effective_profile()
        snip = generate_snippet("quickadd", "capture", title="Gauntlet Capture", profile=profile)
        report = validate_markdown(snip.markdown, ["quickadd"], profile)
        assert report.valid, f"Generated QuickAdd failed validation: {[i.message for i in report.issues]}"


# ===================================================================
# Meta Bind pack validation
# ===================================================================

class TestMetaBindGauntlet:
    def test_valid_note(self):
        md = _load_vault_note("meta_bind/Valid Meta Bind Note.md")
        report = validate_markdown(md, ["meta_bind"], _effective_profile())
        assert report.valid, f"Expected valid, got: {[i.message for i in report.issues]}"

    def test_unknown_field_type(self):
        md = "INPUT[colorpicker:theme_color]"
        profile = _effective_profile()
        report = validate_markdown(md, ["meta_bind"], profile)
        type_issues = [i for i in report.issues if "colorpicker" in i.message]
        assert len(type_issues) >= 1, "Expected unknown field type info"

    def test_generate_then_validate(self):
        profile = _effective_profile()
        snip = generate_snippet("meta_bind", "form", title="Gauntlet Form", profile=profile)
        report = validate_markdown(snip.markdown, ["meta_bind"], profile)
        assert report.valid, f"Generated Meta Bind failed validation: {[i.message for i in report.issues]}"


# ===================================================================
# JS Engine pack validation
# ===================================================================

class TestJsEngineGauntlet:
    def test_valid_note(self):
        md = _load_vault_note("js_engine/Valid JS Engine Note.md")
        report = validate_markdown(md, ["js_engine"], _effective_profile())
        assert report.valid, f"Expected valid, got: {[i.message for i in report.issues]}"

    def test_broken_note(self):
        md = _load_vault_note("js_engine/Broken JS Engine Note.md")
        report = validate_markdown(md, ["js_engine"], _effective_profile())
        errors = [i for i in report.issues if i.severity == "error"]
        assert len(errors) >= 1, "Expected unclosed block error"

    def test_generate_then_validate(self):
        profile = _effective_profile()
        snip = generate_snippet("js_engine", "script", title="Gauntlet Script", profile=profile)
        report = validate_markdown(snip.markdown, ["js_engine"], profile)
        assert report.valid, f"Generated JS Engine failed validation: {[i.message for i in report.issues]}"


# ===================================================================
# Docxer pack validation
# ===================================================================

class TestDocxerGauntlet:
    def test_valid_note(self):
        md = _load_vault_note("docxer/Valid Docxer Note.md")
        report = validate_markdown(md, ["docxer"], _effective_profile())
        assert report.valid, f"Expected valid, got: {[i.message for i in report.issues]}"

    def test_broken_note(self):
        md = _load_vault_note("docxer/Broken Docxer Note.md")
        report = validate_markdown(md, ["docxer"], _effective_profile())
        docxer_issues = [i for i in report.issues if i.pack == "docxer"]
        assert len(docxer_issues) >= 1, "Expected docxer info about missing .md reference"

    def test_generate_then_validate(self):
        profile = _effective_profile()
        snip = generate_snippet("docxer", "convert", title="Gauntlet Import", profile=profile)
        report = validate_markdown(snip.markdown, ["docxer"], profile)
        assert report.valid, f"Generated Docxer failed validation: {[i.message for i in report.issues]}"


# ===================================================================
# Linter pack validation
# ===================================================================

class TestLinterGauntlet:
    def test_valid_note(self):
        md = _load_vault_note("linter/Valid Linter Note.md")
        report = validate_markdown(md, ["linter"], _effective_profile())
        errors = [i for i in report.issues if i.severity in ("error", "warning")]
        assert len(errors) == 0, f"Expected no errors/warnings, got: {[e.message for e in errors]}"

    def test_broken_note_multiple_h1(self):
        md = _load_vault_note("linter/Broken Linter Note.md")
        report = validate_markdown(md, ["linter"], _effective_profile())
        h1_issues = [i for i in report.issues if "H1" in i.message]
        assert len(h1_issues) >= 1, "Expected multiple H1 warning"

    def test_broken_note_triple_blank_lines(self):
        md = _load_vault_note("linter/Broken Linter Note.md")
        report = validate_markdown(md, ["linter"], _effective_profile())
        blank_issues = [i for i in report.issues if "blank" in i.message.lower()]
        assert len(blank_issues) >= 1, "Expected triple blank line info"

    def test_generate_then_validate(self):
        profile = _effective_profile()
        snip = generate_snippet("linter", "hygiene", title="Gauntlet Hygiene", profile=profile)
        report = validate_markdown(snip.markdown, ["linter"], profile)
        errors = [i for i in report.issues if i.severity in ("error", "warning")]
        assert len(errors) == 0, f"Generated Linter note has issues: {[e.message for e in errors]}"


# ===================================================================
# Cross-pack validation
# ===================================================================

class TestCrossPackGauntlet:
    def test_tasks_and_linter(self):
        md = _load_vault_note("cross_pack/Tasks and Linter.md")
        profile = _effective_profile()
        report = validate_markdown(md, ["tasks", "linter"], profile)
        errors = [i for i in report.issues if i.severity == "error"]
        assert len(errors) == 0, f"Expected no errors, got: {[e.message for e in errors]}"
        assert "tasks" in report.packs_checked
        assert "linter" in report.packs_checked

    def test_templater_and_linter(self):
        md = _load_vault_note("cross_pack/Templater and Linter.md")
        profile = _effective_profile()
        report = validate_markdown(md, ["templater", "linter"], profile)
        assert report.valid, f"Expected valid, got: {[i.message for i in report.issues]}"

    def test_core_tasks_linter(self):
        md = _load_vault_note("cross_pack/Core Tasks Linter.md")
        profile = _effective_profile()
        report = validate_markdown(md, ["core", "tasks", "linter"], profile)
        errors = [i for i in report.issues if i.severity == "error"]
        assert len(errors) == 0, f"Expected no errors, got: {[e.message for e in errors]}"
        assert set(report.packs_checked) == {"core", "tasks", "linter"}


# ===================================================================
# Effective profile with runtime configs
# ===================================================================

class TestEffectiveProfileGauntlet:
    @pytest.mark.skipif(not CONFIGS_DIR.exists(), reason="test_vault_configs not present")
    def test_all_configs_load(self):
        report = load_effective_profile("default", _config_paths())
        loaded_kinds = [s.kind for s in report.sources if s.loaded]
        assert "bundled-profile" in loaded_kinds
        assert "tasks-config" in loaded_kinds
        assert "linter-config" in loaded_kinds
        assert "quickadd-config" in loaded_kinds
        assert "templater-config" in loaded_kinds
        assert "meta-bind-config" in loaded_kinds
        assert "js-engine-config" in loaded_kinds
        assert "docxer-config" in loaded_kinds
        assert "profile-overlay" in loaded_kinds

    @pytest.mark.skipif(not CONFIGS_DIR.exists(), reason="test_vault_configs not present")
    def test_tasks_config_applied(self):
        report = load_effective_profile("default", _config_paths())
        p = report.profile
        assert p.tasks_global_filter == "#task"
        assert p.tasks_append_global_filter_to_queries is True
        symbols = [s["symbol"] for s in p.tasks_custom_statuses]
        assert "/" in symbols
        assert "-" in symbols

    @pytest.mark.skipif(not CONFIGS_DIR.exists(), reason="test_vault_configs not present")
    def test_templater_config_applied(self):
        report = load_effective_profile("default", _config_paths())
        p = report.profile
        assert "formatDate" in p.templater_user_scripts
        assert "slugify" in p.templater_user_scripts

    @pytest.mark.skipif(not CONFIGS_DIR.exists(), reason="test_vault_configs not present")
    def test_quickadd_config_applied(self):
        report = load_effective_profile("default", _config_paths())
        p = report.profile
        assert "project" in p.quickadd_known_variables
        assert "Daily Note" in p.quickadd_choice_names

    @pytest.mark.skipif(not CONFIGS_DIR.exists(), reason="test_vault_configs not present")
    def test_meta_bind_config_applied(self):
        report = load_effective_profile("default", _config_paths())
        p = report.profile
        assert "slider" in p.meta_bind_field_types

    @pytest.mark.skipif(not CONFIGS_DIR.exists(), reason="test_vault_configs not present")
    def test_js_engine_config_applied(self):
        report = load_effective_profile("default", _config_paths())
        p = report.profile
        assert "formatDate" in p.js_engine_helpers

    @pytest.mark.skipif(not CONFIGS_DIR.exists(), reason="test_vault_configs not present")
    def test_linter_config_applied(self):
        report = load_effective_profile("default", _config_paths())
        p = report.profile
        assert p.linter_expectations.get("single_h1") is True

    @pytest.mark.skipif(not CONFIGS_DIR.exists(), reason="test_vault_configs not present")
    def test_docxer_config_applied(self):
        report = load_effective_profile("default", _config_paths())
        p = report.profile
        assert "source_docx" in p.docxer_defaults


# ===================================================================
# Alias resolution
# ===================================================================

class TestAliasGauntlet:
    ALIASES = {
        "doxcer": "docxer",
        "metabind": "meta_bind",
        "meta-bind": "meta_bind",
        "jsengine": "js_engine",
        "js-engine": "js_engine",
        "obsidian": "core",
        "core_obsidian": "core",
        "meta_bind_plugin": "meta_bind",
    }

    @pytest.mark.parametrize("alias,expected", list(ALIASES.items()))
    def test_normalize(self, alias, expected):
        assert normalize_pack_name(alias) == expected

    @pytest.mark.parametrize("alias,expected", list(ALIASES.items()))
    def test_get_pack_via_alias(self, alias, expected):
        pack = get_pack(alias)
        assert pack.name == expected

    @pytest.mark.parametrize("alias,expected", list(ALIASES.items()))
    def test_load_doc_via_alias(self, alias, expected):
        text = load_doc_text(alias)
        assert len(text) > 0


# ===================================================================
# Generate-then-validate for ALL packs (parametrized)
# ===================================================================

class TestGenerateThenValidateAll:
    """Ensures every pack's generated snippet passes its own validator."""

    PACK_INTENTS = {
        "core": "note",
        "tasks": "task-line",
        "templater": "project-template",
        "quickadd": "capture",
        "meta_bind": "form",
        "js_engine": "script",
        "docxer": "convert",
        "linter": "hygiene",
    }

    @pytest.mark.parametrize("pack_name", ALL_PACKS)
    def test_snippet_passes_own_validator(self, pack_name):
        profile = _effective_profile()
        intent = self.PACK_INTENTS[pack_name]
        snip = generate_snippet(pack_name, intent, title=f"Gauntlet {pack_name}", profile=profile)
        assert snip.pack == pack_name
        assert len(snip.markdown) > 10
        report = validate_markdown(snip.markdown, [pack_name], profile)
        errors = [i for i in report.issues if i.severity == "error"]
        assert len(errors) == 0, \
            f"Generated {pack_name}/{intent} snippet failed validation: {[e.message for e in errors]}"


# ===================================================================
# Server-layer tool functions
# ===================================================================

class TestServerToolFunctions:
    """Exercise the server.py tool functions directly."""

    def test_list_packs(self):
        from obsidian_spec_mcp.server import list_packs
        result = list_packs()
        assert len(result) == 8
        names = {p["name"] for p in result}
        assert names == set(ALL_PACKS)

    def test_list_packs_enabled_only(self):
        from obsidian_spec_mcp.server import list_packs
        result = list_packs(enabled_only=True)
        assert all(p["enabled_by_default"] for p in result)

    def test_get_pack_info(self):
        from obsidian_spec_mcp.server import get_pack_info
        result = get_pack_info("tasks")
        assert result["name"] == "tasks"

    def test_search_spec(self):
        from obsidian_spec_mcp.server import search_spec
        result = search_spec("checklist")
        assert len(result) >= 1

    def test_get_doc(self):
        from obsidian_spec_mcp.server import get_doc
        result = get_doc("core")
        assert "wikilink" in result.lower() or "Wikilink" in result

    def test_normalized_pack_name(self):
        from obsidian_spec_mcp.server import normalized_pack_name
        result = normalized_pack_name("doxcer")
        assert result == {"input": "doxcer", "normalized": "docxer"}

    def test_validate_obsidian_markdown(self):
        from obsidian_spec_mcp.server import validate_obsidian_markdown
        result = validate_obsidian_markdown(
            markdown="- [x] Done ⏫ 📅 2026-04-05",
            packs=["tasks"],
        )
        assert result["valid"] is True

    def test_generate_obsidian_snippet(self):
        from obsidian_spec_mcp.server import generate_obsidian_snippet
        result = generate_obsidian_snippet(pack="tasks", intent="task-line", title="Test")
        assert result["pack"] == "tasks"
        assert "Test" in result["markdown"]

    @pytest.mark.skipif(not CONFIGS_DIR.exists(), reason="test_vault_configs not present")
    def test_get_effective_profile_with_configs(self):
        from obsidian_spec_mcp.server import get_effective_profile
        result = get_effective_profile(
            tasks_path=str(CONFIGS_DIR / "tasks.json"),
            linter_path=str(CONFIGS_DIR / "linter.json"),
        )
        loaded = [s["kind"] for s in result["sources"] if s["loaded"]]
        assert "tasks-config" in loaded
        assert "linter-config" in loaded
