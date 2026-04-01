"""Tests for obsidian_spec_mcp.renderers"""
from __future__ import annotations

from obsidian_spec_mcp.models import Profile
from obsidian_spec_mcp.renderers import generate_snippet


def _profile(**overrides) -> Profile:
    defaults = dict(name="test", use_wikilinks=True, prefer_properties=True)
    defaults.update(overrides)
    return Profile(**defaults)


class TestCoreSnippet:
    def test_generates_frontmatter(self):
        snip = generate_snippet("core", "note", title="My Note", profile=_profile())
        assert "---" in snip.markdown
        assert "My Note" in snip.markdown
        assert snip.pack == "core"

    def test_wikilinks_used(self):
        snip = generate_snippet("core", "note", title="Test", profile=_profile(use_wikilinks=True))
        assert "[[" in snip.markdown

    def test_markdown_links_when_wikilinks_off(self):
        snip = generate_snippet("core", "note", title="Test", profile=_profile(use_wikilinks=False))
        assert "[[" not in snip.markdown
        assert "](" in snip.markdown

    def test_callout_present(self):
        snip = generate_snippet("core", "note", title="Test", profile=_profile())
        assert "[!info]" in snip.markdown


class TestTasksSnippet:
    def test_task_line(self):
        snip = generate_snippet("tasks", "task-line", title="Buy groceries", profile=_profile())
        assert snip.pack == "tasks"
        assert "Buy groceries" in snip.markdown
        assert snip.markdown.startswith("- [")

    def test_task_query(self):
        snip = generate_snippet("tasks", "query", title="Query", profile=_profile())
        assert "```tasks" in snip.markdown
        assert "not done" in snip.markdown
        assert "```" in snip.markdown

    def test_custom_status_in_task(self):
        p = _profile(tasks_custom_statuses=[{"symbol": "/", "name": "in-progress"}])
        snip = generate_snippet("tasks", "task-line", title="WIP", profile=p)
        assert "- [/]" in snip.markdown

    def test_global_filter_in_task_line(self):
        p = _profile(tasks_global_filter="#task")
        snip = generate_snippet("tasks", "task-line", title="Tagged", profile=p)
        assert "#task" in snip.markdown

    def test_global_filter_in_query(self):
        p = _profile(tasks_global_filter="#task", tasks_append_global_filter_to_queries=True)
        snip = generate_snippet("tasks", "query", title="Filtered", profile=p)
        assert "#task" in snip.markdown

    def test_recurrence(self):
        snip = generate_snippet("tasks", "task-line", title="Recurring", details={"recurrence": "week"}, profile=_profile())
        assert "🔁 every week" in snip.markdown


class TestTemplaterSnippet:
    def test_basic_template(self):
        snip = generate_snippet("templater", "project-template", title="Project Alpha", profile=_profile())
        assert snip.pack == "templater"
        assert "<%" in snip.markdown
        assert "%>" in snip.markdown
        assert "Project Alpha" in snip.markdown

    def test_user_script_hint(self):
        p = _profile(templater_user_scripts=["myHelper"])
        snip = generate_snippet("templater", "template", title="Test", profile=p)
        assert "tp.user.myHelper" in snip.markdown
        assert "myHelper" in snip.profile_hints[0]


class TestQuickAddSnippet:
    def test_basic(self):
        snip = generate_snippet("quickadd", "capture", title="Quick Note", profile=_profile())
        assert snip.pack == "quickadd"
        assert "Quick Note" in snip.markdown

    def test_known_variables(self):
        p = _profile(quickadd_known_variables=["team", "sprint"])
        snip = generate_snippet("quickadd", "capture", title="Sprint", profile=p)
        assert "team" in snip.markdown

    def test_choice_hints(self):
        p = _profile(quickadd_choice_names=["Daily Note"])
        snip = generate_snippet("quickadd", "capture", title="Test", profile=p)
        assert "Daily Note" in snip.profile_hints[0]


class TestMetaBindSnippet:
    def test_basic(self):
        snip = generate_snippet("meta_bind", "form", title="Status Form", profile=_profile())
        assert snip.pack == "meta_bind"
        assert "INPUT[" in snip.markdown

    def test_custom_field_types(self):
        p = _profile(meta_bind_field_types=["slider", "date"])
        snip = generate_snippet("meta_bind", "form", title="Custom", profile=p)
        assert "slider" in snip.markdown


class TestJsEngineSnippet:
    def test_basic(self):
        snip = generate_snippet("js_engine", "script", title="Script", profile=_profile())
        assert snip.pack == "js_engine"
        assert "```js-engine" in snip.markdown

    def test_helper_hint(self):
        p = _profile(js_engine_helpers=["formatDate"])
        snip = generate_snippet("js_engine", "script", title="Helper", profile=p)
        assert "formatDate" in snip.markdown


class TestDocxerSnippet:
    def test_basic(self):
        snip = generate_snippet("docxer", "convert", title="Import Doc", profile=_profile())
        assert snip.pack == "docxer"
        assert ".docx" in snip.markdown

    def test_custom_paths(self):
        snip = generate_snippet("docxer", "convert", title="Custom", details={"source_docx": "report.docx"}, profile=_profile())
        assert "report.docx" in snip.markdown


class TestLinterSnippet:
    def test_basic(self):
        snip = generate_snippet("linter", "hygiene", title="Clean Note", profile=_profile())
        assert snip.pack == "linter"
        assert "Clean Note" in snip.markdown

    def test_expectations_reflected(self):
        p = _profile(linter_expectations={"single_h1": False})
        snip = generate_snippet("linter", "hygiene", title="Flex", profile=p)
        assert "Multiple" in snip.markdown


class TestAliasResolution:
    def test_doxcer_resolves(self):
        snip = generate_snippet("doxcer", "convert", title="Alias Test", profile=_profile())
        assert snip.pack == "docxer"

    def test_metabind_resolves(self):
        snip = generate_snippet("metabind", "form", title="Alias Test", profile=_profile())
        assert snip.pack == "meta_bind"
