"""Tests for obsidian_spec_mcp.config"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from obsidian_spec_mcp.config import load_effective_profile
from obsidian_spec_mcp.models import PluginConfigPaths


class TestLoadEffectiveProfile:
    def test_default_no_configs(self):
        report = load_effective_profile("default", PluginConfigPaths())
        assert report.profile.name == "default"
        assert len(report.sources) >= 1
        assert report.sources[0].kind == "bundled-profile"
        assert report.sources[0].loaded is True

    def test_missing_config_file(self):
        paths = PluginConfigPaths(tasks_path="/nonexistent/tasks.json")
        report = load_effective_profile("default", paths)
        not_found = [s for s in report.sources if not s.loaded and "not found" in (s.details or "").lower()]
        assert len(not_found) >= 1


class TestTasksConfigMerge:
    def test_custom_statuses_loaded(self):
        cfg = {
            "customStatuses": [
                {"symbol": "/", "name": "in-progress", "type": "IN_PROGRESS"},
                {"symbol": "?", "name": "question", "type": "NON_TASK"},
            ],
            "globalFilter": "#task",
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(cfg, f)
            f.flush()
            paths = PluginConfigPaths(tasks_path=f.name)
            report = load_effective_profile("default", paths)
        os.unlink(f.name)
        symbols = [s["symbol"] for s in report.profile.tasks_custom_statuses]
        assert "/" in symbols
        assert "?" in symbols
        assert report.profile.tasks_global_filter == "#task"

    def test_append_global_filter(self):
        cfg = {"appendGlobalFilterToQueries": True, "globalFilter": "#task"}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(cfg, f)
            f.flush()
            paths = PluginConfigPaths(tasks_path=f.name)
            report = load_effective_profile("default", paths)
        os.unlink(f.name)
        assert report.profile.tasks_append_global_filter_to_queries is True


class TestLinterConfigMerge:
    def test_linter_rules_loaded(self):
        cfg = {"rules": {"single_h1": False, "collapse_extra_blank_lines": True}}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(cfg, f)
            f.flush()
            paths = PluginConfigPaths(linter_path=f.name)
            report = load_effective_profile("default", paths)
        os.unlink(f.name)
        assert report.profile.linter_expectations.get("single_h1") is False


class TestTemplaterConfigMerge:
    def test_user_scripts_loaded(self):
        cfg = {"userScripts": [{"name": "myHelper"}, "anotherHelper"]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(cfg, f)
            f.flush()
            paths = PluginConfigPaths(templater_path=f.name)
            report = load_effective_profile("default", paths)
        os.unlink(f.name)
        assert "myHelper" in report.profile.templater_user_scripts
        assert "anotherHelper" in report.profile.templater_user_scripts


class TestQuickAddConfigMerge:
    def test_variables_and_choices(self):
        cfg = {
            "variables": [{"name": "project"}, "status"],
            "choices": [{"name": "Daily Note"}, {"name": "Meeting Note"}],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(cfg, f)
            f.flush()
            paths = PluginConfigPaths(quickadd_path=f.name)
            report = load_effective_profile("default", paths)
        os.unlink(f.name)
        assert "project" in report.profile.quickadd_known_variables
        assert "status" in report.profile.quickadd_known_variables
        assert "Daily Note" in report.profile.quickadd_choice_names


class TestProfileOverlay:
    def test_overlay_merges(self):
        overlay = {"use_wikilinks": False, "default_packs": ["core", "tasks", "linter"]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(overlay, f)
            f.flush()
            paths = PluginConfigPaths(profile_path=f.name)
            report = load_effective_profile("default", paths)
        os.unlink(f.name)
        assert report.profile.use_wikilinks is False
        assert "linter" in report.profile.default_packs


class TestEnvVarResolution:
    def test_env_tasks_path(self, monkeypatch, tmp_path):
        cfg_file = tmp_path / "tasks.json"
        cfg_file.write_text(json.dumps({"globalFilter": "#envtest"}))
        monkeypatch.setenv("OBS_SPEC_TASKS_CONFIG_PATH", str(cfg_file))
        report = load_effective_profile("default", PluginConfigPaths())
        assert report.profile.tasks_global_filter == "#envtest"


class TestYamlConfig:
    def test_yaml_file_loads(self, tmp_path):
        cfg_file = tmp_path / "linter.yaml"
        cfg_file.write_text("rules:\n  single_h1: false\n  collapse_extra_blank_lines: true\n")
        paths = PluginConfigPaths(linter_path=str(cfg_file))
        report = load_effective_profile("default", paths)
        assert report.profile.linter_expectations.get("single_h1") is False


class TestExampleRuntimeConfigs:
    """Smoke tests using the bundled example config files."""

    EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples" / "runtime_configs"

    @pytest.mark.skipif(
        not (Path(__file__).resolve().parent.parent / "examples" / "runtime_configs").exists(),
        reason="examples/runtime_configs not present",
    )
    def test_all_example_configs_load(self):
        paths = PluginConfigPaths(
            tasks_path=str(self.EXAMPLES_DIR / "tasks.json"),
            linter_path=str(self.EXAMPLES_DIR / "linter.json"),
            quickadd_path=str(self.EXAMPLES_DIR / "quickadd.json"),
            templater_path=str(self.EXAMPLES_DIR / "templater.json"),
            meta_bind_path=str(self.EXAMPLES_DIR / "meta_bind.json"),
            js_engine_path=str(self.EXAMPLES_DIR / "js_engine.json"),
            docxer_path=str(self.EXAMPLES_DIR / "docxer.json"),
            profile_path=str(self.EXAMPLES_DIR / "profile_overlay.json"),
        )
        report = load_effective_profile("default", paths)
        loaded_kinds = [s.kind for s in report.sources if s.loaded]
        assert "bundled-profile" in loaded_kinds
        assert "tasks-config" in loaded_kinds
        assert "linter-config" in loaded_kinds
