from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


PackName = Literal[
    "core",
    "tasks",
    "templater",
    "quickadd",
    "meta_bind",
    "js_engine",
    "docxer",
    "linter",
]


class DocSource(BaseModel):
    label: str
    url: str
    notes: str | None = None


class PackInfo(BaseModel):
    name: PackName
    title: str
    description: str
    syntax_kinds: list[str] = Field(default_factory=list)
    docs: list[DocSource] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    validator_notes: list[str] = Field(default_factory=list)
    enabled_by_default: bool = True


class SearchHit(BaseModel):
    pack: PackName
    title: str
    score: int
    snippet: str
    source_url: str | None = None


class ValidationIssue(BaseModel):
    pack: str
    severity: Literal["error", "warning", "info"]
    message: str
    line: int | None = None
    suggestion: str | None = None


class ValidationReport(BaseModel):
    valid: bool
    packs_checked: list[str]
    issues: list[ValidationIssue] = Field(default_factory=list)
    summary: str
    effective_profile: dict[str, Any] | None = None


class GeneratedSnippet(BaseModel):
    pack: str
    intent: str
    markdown: str
    notes: list[str] = Field(default_factory=list)
    profile_hints: list[str] = Field(default_factory=list)


class Profile(BaseModel):
    name: str
    use_wikilinks: bool = True
    prefer_properties: bool = True
    default_packs: list[str] = Field(default_factory=lambda: ["core", "tasks"])
    tasks_global_filter: str | None = None
    tasks_custom_statuses: list[dict[str, str]] = Field(default_factory=list)
    tasks_date_priority: list[str] = Field(default_factory=lambda: ["scheduled", "due"])
    tasks_append_global_filter_to_queries: bool = False
    linter_expectations: dict[str, Any] = Field(default_factory=dict)
    quickadd_known_variables: list[str] = Field(default_factory=list)
    quickadd_choice_names: list[str] = Field(default_factory=list)
    templater_user_scripts: list[str] = Field(default_factory=list)
    templater_folder_templates: dict[str, str] = Field(default_factory=dict)
    meta_bind_field_types: list[str] = Field(default_factory=list)
    js_engine_helpers: list[str] = Field(default_factory=list)
    docxer_defaults: dict[str, Any] = Field(default_factory=dict)
    config_sources: list[str] = Field(default_factory=list)


class ConfigSourceReport(BaseModel):
    kind: str
    path: str
    loaded: bool
    details: str | None = None


class EffectiveProfileReport(BaseModel):
    profile: Profile
    sources: list[ConfigSourceReport] = Field(default_factory=list)


class PluginConfigPaths(BaseModel):
    profile_path: str | None = None
    tasks_path: str | None = None
    linter_path: str | None = None
    quickadd_path: str | None = None
    templater_path: str | None = None
    meta_bind_path: str | None = None
    js_engine_path: str | None = None
    docxer_path: str | None = None


class RuntimeOptions(BaseModel):
    profile_name: str = "default"
    config_paths: PluginConfigPaths = Field(default_factory=PluginConfigPaths)
