"""Tests for obsidian_spec_mcp.validators"""
from __future__ import annotations

from obsidian_spec_mcp.models import Profile
from obsidian_spec_mcp.validators import validate_markdown


def _profile(**overrides) -> Profile:
    defaults = dict(name="test", use_wikilinks=True, prefer_properties=True)
    defaults.update(overrides)
    return Profile(**defaults)


class TestCoreValidation:
    def test_valid_callout(self):
        md = "> [!info] Title\n> Body text here"
        report = validate_markdown(md, ["core"], _profile())
        assert report.valid

    def test_broken_callout_marker(self):
        md = "Some text [!info] but not a callout"
        report = validate_markdown(md, ["core"], _profile())
        warnings = [i for i in report.issues if i.pack == "core" and i.severity == "warning"]
        assert len(warnings) >= 1

    def test_wikilink_preferred(self):
        md = "[My Note](My%20Note.md)"
        report = validate_markdown(md, ["core"], _profile(use_wikilinks=True))
        info = [i for i in report.issues if "wikilinks" in i.message.lower()]
        assert len(info) >= 1

    def test_wikilink_not_flagged_when_disabled(self):
        md = "[My Note](My%20Note.md)"
        report = validate_markdown(md, ["core"], _profile(use_wikilinks=False))
        info = [i for i in report.issues if "wikilinks" in i.message.lower()]
        assert len(info) == 0

    def test_properties_outside_frontmatter(self):
        md = "tags: foo\nSome content"
        report = validate_markdown(md, ["core"], _profile(prefer_properties=True))
        info = [i for i in report.issues if "frontmatter" in i.message.lower() or "properties" in i.message.lower()]
        assert len(info) >= 1


class TestTasksValidation:
    def test_valid_task_line(self):
        md = "- [x] Done task ⏫ 📅 2026-04-05"
        report = validate_markdown(md, ["tasks"], _profile())
        assert report.valid

    def test_task_markers_not_on_checklist(self):
        md = "Some text ⏫ 📅 2026-04-05"
        report = validate_markdown(md, ["tasks"], _profile())
        errors = [i for i in report.issues if i.severity == "error"]
        assert len(errors) >= 1

    def test_unknown_status_symbol(self):
        md = "- [?] Mystery task"
        report = validate_markdown(md, ["tasks"], _profile())
        warnings = [i for i in report.issues if "status" in i.message.lower()]
        assert len(warnings) >= 1

    def test_custom_status_accepted(self):
        md = "- [/] In progress task"
        p = _profile(tasks_custom_statuses=[{"symbol": "/", "name": "in-progress", "type": "IN_PROGRESS"}])
        report = validate_markdown(md, ["tasks"], p)
        status_issues = [i for i in report.issues if "status" in i.message.lower() and "/" in i.message]
        assert len(status_issues) == 0

    def test_valid_tasks_query_block(self):
        md = "```tasks\nnot done\ndue before tomorrow\nsort by due\n```"
        report = validate_markdown(md, ["tasks"], _profile())
        assert report.valid

    def test_empty_tasks_query_block(self):
        md = "```tasks\n\n```"
        report = validate_markdown(md, ["tasks"], _profile())
        warnings = [i for i in report.issues if "empty" in i.message.lower()]
        assert len(warnings) >= 1

    def test_unclosed_tasks_block(self):
        md = "```tasks\nnot done"
        report = validate_markdown(md, ["tasks"], _profile())
        errors = [i for i in report.issues if i.severity == "error"]
        assert len(errors) >= 1

    def test_recurrence_without_every(self):
        md = "- [ ] Recurring 🔁 weekly"
        report = validate_markdown(md, ["tasks"], _profile())
        warnings = [i for i in report.issues if "every" in i.message.lower()]
        assert len(warnings) >= 1

    def test_recurrence_valid(self):
        md = "- [ ] Recurring 🔁 every week"
        report = validate_markdown(md, ["tasks"], _profile())
        recurrence_warnings = [i for i in report.issues if "every" in i.message.lower()]
        assert len(recurrence_warnings) == 0

    def test_global_filter_in_query(self):
        p = _profile(tasks_global_filter="#task", tasks_append_global_filter_to_queries=True)
        md = "```tasks\nnot done\nsort by due\n```"
        report = validate_markdown(md, ["tasks"], p)
        info = [i for i in report.issues if "global filter" in i.message.lower()]
        assert len(info) >= 1


class TestTemplaterValidation:
    def test_balanced_tags(self):
        md = "<% tp.file.title %>"
        report = validate_markdown(md, ["templater"], _profile())
        assert report.valid

    def test_unbalanced_tags(self):
        md = "<% tp.file.title"
        report = validate_markdown(md, ["templater"], _profile())
        errors = [i for i in report.issues if i.severity == "error"]
        assert len(errors) >= 1

    def test_exec_tag(self):
        md = "<%* const today = tp.date.now('YYYY-MM-DD') %>"
        report = validate_markdown(md, ["templater"], _profile())
        assert report.valid

    def test_unknown_user_script(self):
        p = _profile(templater_user_scripts=["myHelper"])
        md = "<% tp.user.unknownHelper() %>"
        report = validate_markdown(md, ["templater"], p)
        info = [i for i in report.issues if "tp.user" in i.message.lower()]
        assert len(info) >= 1


class TestQuickAddValidation:
    def test_balanced_placeholders(self):
        md = "{{DATE}} and {{VALUE:project}}"
        report = validate_markdown(md, ["quickadd"], _profile())
        assert report.valid

    def test_unbalanced_braces(self):
        md = "{{DATE}} and {{VALUE:project"
        report = validate_markdown(md, ["quickadd"], _profile())
        errors = [i for i in report.issues if i.severity == "error"]
        assert len(errors) >= 1

    def test_unknown_variable(self):
        p = _profile(quickadd_known_variables=["project"])
        md = "{{VALUE:unknown_var}}"
        report = validate_markdown(md, ["quickadd"], p)
        info = [i for i in report.issues if "unknown_var" in i.message]
        assert len(info) >= 1


class TestMetaBindValidation:
    def test_valid_inline(self):
        md = "INPUT[toggle:done]"
        report = validate_markdown(md, ["meta_bind"], _profile())
        assert report.valid

    def test_unknown_field_type(self):
        p = _profile(meta_bind_field_types=["toggle", "text"])
        md = "INPUT[slider:volume]"
        report = validate_markdown(md, ["meta_bind"], p)
        info = [i for i in report.issues if "slider" in i.message]
        assert len(info) >= 1


class TestJsEngineValidation:
    def test_valid_block(self):
        md = "```js-engine\nreturn engine.markdown.create('*test*');\n```"
        report = validate_markdown(md, ["js_engine"], _profile())
        assert report.valid

    def test_unclosed_block(self):
        md = "```js-engine\nreturn engine.markdown.create('*test*');"
        report = validate_markdown(md, ["js_engine"], _profile())
        errors = [i for i in report.issues if i.severity == "error"]
        assert len(errors) >= 1


class TestDocxerValidation:
    def test_docx_without_md(self):
        md = "Convert document.docx to notes."
        report = validate_markdown(md, ["docxer"], _profile())
        info = [i for i in report.issues if i.pack == "docxer"]
        assert len(info) >= 1

    def test_docx_with_md(self):
        md = "Convert document.docx to document.md"
        report = validate_markdown(md, ["docxer"], _profile())
        assert report.valid


class TestLinterValidation:
    def test_single_h1_ok(self):
        md = "# Title\n\n## Section\n\nContent"
        report = validate_markdown(md, ["linter"], _profile())
        h1_warnings = [i for i in report.issues if "H1" in i.message]
        assert len(h1_warnings) == 0

    def test_multiple_h1(self):
        md = "# Title One\n\n# Title Two\n\nContent"
        report = validate_markdown(md, ["linter"], _profile())
        h1_warnings = [i for i in report.issues if "H1" in i.message]
        assert len(h1_warnings) >= 1

    def test_triple_blank_lines(self):
        md = "Some text\n\n\n\nMore text"
        report = validate_markdown(md, ["linter"], _profile())
        blank_issues = [i for i in report.issues if "blank" in i.message.lower()]
        assert len(blank_issues) >= 1

    def test_clean_spacing(self):
        md = "Some text\n\nMore text"
        report = validate_markdown(md, ["linter"], _profile())
        assert report.valid


class TestMultiPackValidation:
    def test_tasks_and_linter(self):
        md = "- [x] Done task ⏫ 📅 2026-04-05\n\n# Title\n\nContent"
        report = validate_markdown(md, ["tasks", "linter"], _profile())
        assert "tasks" in report.packs_checked
        assert "linter" in report.packs_checked

    def test_valid_means_no_errors(self):
        md = "- [x] Done task"
        report = validate_markdown(md, ["tasks"], _profile())
        assert report.valid
        assert not any(i.severity == "error" for i in report.issues)

    def test_summary_on_error(self):
        md = "Task markers ⏫ not on checklist"
        report = validate_markdown(md, ["tasks"], _profile())
        assert not report.valid
        assert "error" in report.summary.lower()
