from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import yaml

from .models import ConfigSourceReport, EffectiveProfileReport, PluginConfigPaths, Profile
from .registry import load_profile


ENV_MAP = {
    "profile_path": "OBS_SPEC_PROFILE_PATH",
    "tasks_path": "OBS_SPEC_TASKS_CONFIG_PATH",
    "linter_path": "OBS_SPEC_LINTER_CONFIG_PATH",
    "quickadd_path": "OBS_SPEC_QUICKADD_CONFIG_PATH",
    "templater_path": "OBS_SPEC_TEMPLATER_CONFIG_PATH",
    "meta_bind_path": "OBS_SPEC_META_BIND_CONFIG_PATH",
    "js_engine_path": "OBS_SPEC_JS_ENGINE_CONFIG_PATH",
    "docxer_path": "OBS_SPEC_DOCXER_CONFIG_PATH",
    "dataview_path": "OBS_SPEC_DATAVIEW_CONFIG_PATH",
    "datacore_path": "OBS_SPEC_DATACORE_CONFIG_PATH",
}


def load_effective_profile(profile_name: str = "default", config_paths: PluginConfigPaths | None = None) -> EffectiveProfileReport:
    profile = load_profile(profile_name)
    sources: list[ConfigSourceReport] = [
        ConfigSourceReport(kind="bundled-profile", path=f"{profile_name}_profile.json", loaded=True, details="Loaded bundled default profile")
    ]

    paths = _resolve_paths(config_paths)

    base_overlay = _load_mapping(paths.profile_path, "profile-overlay", sources)
    if base_overlay:
        _merge_profile(profile, base_overlay, source_label=str(paths.profile_path))

    tasks_cfg = _load_mapping(paths.tasks_path, "tasks-config", sources)
    if tasks_cfg:
        _merge_profile(profile, _extract_tasks(tasks_cfg), source_label=str(paths.tasks_path))

    linter_cfg = _load_mapping(paths.linter_path, "linter-config", sources)
    if linter_cfg:
        _merge_profile(profile, _extract_linter(linter_cfg), source_label=str(paths.linter_path))

    quickadd_cfg = _load_mapping(paths.quickadd_path, "quickadd-config", sources)
    if quickadd_cfg:
        _merge_profile(profile, _extract_quickadd(quickadd_cfg), source_label=str(paths.quickadd_path))

    templater_cfg = _load_mapping(paths.templater_path, "templater-config", sources)
    if templater_cfg:
        _merge_profile(profile, _extract_templater(templater_cfg), source_label=str(paths.templater_path))

    meta_bind_cfg = _load_mapping(paths.meta_bind_path, "meta-bind-config", sources)
    if meta_bind_cfg:
        _merge_profile(profile, _extract_meta_bind(meta_bind_cfg), source_label=str(paths.meta_bind_path))

    js_engine_cfg = _load_mapping(paths.js_engine_path, "js-engine-config", sources)
    if js_engine_cfg:
        _merge_profile(profile, _extract_js_engine(js_engine_cfg), source_label=str(paths.js_engine_path))

    docxer_cfg = _load_mapping(paths.docxer_path, "docxer-config", sources)
    if docxer_cfg:
        _merge_profile(profile, _extract_docxer(docxer_cfg), source_label=str(paths.docxer_path))

    dataview_cfg = _load_mapping(paths.dataview_path, "dataview-config", sources)
    if dataview_cfg:
        _merge_profile(profile, _extract_dataview(dataview_cfg), source_label=str(paths.dataview_path))

    datacore_cfg = _load_mapping(paths.datacore_path, "datacore-config", sources)
    if datacore_cfg:
        _merge_profile(profile, _extract_datacore(datacore_cfg), source_label=str(paths.datacore_path))

    profile.config_sources = [src.path for src in sources if src.loaded]
    return EffectiveProfileReport(profile=profile, sources=sources)


def _resolve_paths(config_paths: PluginConfigPaths | None) -> PluginConfigPaths:
    data = config_paths.model_dump() if config_paths else {}
    for field, env_name in ENV_MAP.items():
        if not data.get(field):
            env_value = os.getenv(env_name)
            if env_value:
                data[field] = env_value
    return PluginConfigPaths.model_validate(data)


def _load_mapping(path_str: str | None, kind: str, sources: list[ConfigSourceReport]) -> dict[str, Any] | None:
    if not path_str:
        return None
    path = Path(path_str).expanduser()
    if not path.exists():
        sources.append(ConfigSourceReport(kind=kind, path=str(path), loaded=False, details="File not found"))
        return None
    try:
        if path.suffix.lower() in {".yaml", ".yml"}:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        else:
            data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            sources.append(ConfigSourceReport(kind=kind, path=str(path), loaded=False, details="Expected a JSON or YAML object"))
            return None
        sources.append(ConfigSourceReport(kind=kind, path=str(path), loaded=True, details=f"Loaded {kind}"))
        return data
    except Exception as exc:  # pragma: no cover - defensive path
        sources.append(ConfigSourceReport(kind=kind, path=str(path), loaded=False, details=str(exc)))
        return None


def _merge_profile(profile: Profile, overlay: dict[str, Any], source_label: str) -> None:
    for key, value in overlay.items():
        if value is None or not hasattr(profile, key):
            continue
        current = getattr(profile, key)
        if isinstance(current, list) and isinstance(value, list):
            merged = []
            for item in current + value:
                if item not in merged:
                    merged.append(item)
            setattr(profile, key, merged)
        elif isinstance(current, dict) and isinstance(value, dict):
            merged = dict(current)
            merged.update(value)
            setattr(profile, key, merged)
        else:
            setattr(profile, key, value)
    if source_label not in profile.config_sources:
        profile.config_sources.append(source_label)


def _extract_tasks(data: dict[str, Any]) -> dict[str, Any]:
    statuses = []
    raw_statuses = data.get("customStatuses") or data.get("statuses") or []
    for item in raw_statuses:
        if isinstance(item, dict):
            statuses.append(
                {
                    "symbol": str(item.get("symbol", "")).strip(),
                    "name": str(item.get("name", item.get("id", ""))).strip(),
                    "type": str(item.get("type", item.get("statusType", ""))).strip(),
                }
            )
    overlay: dict[str, Any] = {"tasks_custom_statuses": [s for s in statuses if s.get("symbol") or s.get("name")]}
    global_filter = data.get("globalFilter") or data.get("global_filter")
    if global_filter:
        overlay["tasks_global_filter"] = str(global_filter)
    date_priority = data.get("datePriority") or data.get("date_priority")
    if isinstance(date_priority, list):
        overlay["tasks_date_priority"] = [str(x) for x in date_priority]
    append = data.get("appendGlobalFilterToQueries")
    if isinstance(append, bool):
        overlay["tasks_append_global_filter_to_queries"] = append
    return overlay


def _extract_linter(data: dict[str, Any]) -> dict[str, Any]:
    expectations = data.get("rules") if isinstance(data.get("rules"), dict) else data
    return {"linter_expectations": expectations}


def _extract_quickadd(data: dict[str, Any]) -> dict[str, Any]:
    variables = []
    choices = []
    for item in data.get("variables", []):
        if isinstance(item, dict) and item.get("name"):
            variables.append(str(item["name"]))
        elif isinstance(item, str):
            variables.append(item)
    for choice in data.get("choices", []):
        if isinstance(choice, dict) and choice.get("name"):
            choices.append(str(choice["name"]))
    return {
        "quickadd_known_variables": variables,
        "quickadd_choice_names": choices,
    }


def _extract_templater(data: dict[str, Any]) -> dict[str, Any]:
    scripts = []
    for item in data.get("userScripts") or data.get("user_scripts") or []:
        if isinstance(item, dict) and item.get("name"):
            scripts.append(str(item["name"]))
        elif isinstance(item, str):
            scripts.append(item)
    folder_templates = data.get("folderTemplates") or data.get("folder_templates") or {}
    if not isinstance(folder_templates, dict):
        folder_templates = {}
    return {
        "templater_user_scripts": scripts,
        "templater_folder_templates": {str(k): str(v) for k, v in folder_templates.items()},
    }


def _extract_meta_bind(data: dict[str, Any]) -> dict[str, Any]:
    field_types = data.get("fieldTypes") or data.get("field_types") or []
    return {"meta_bind_field_types": [str(x) for x in field_types]}


def _extract_js_engine(data: dict[str, Any]) -> dict[str, Any]:
    helpers = data.get("helpers") or data.get("globals") or []
    return {"js_engine_helpers": [str(x) for x in helpers]}


def _extract_docxer(data: dict[str, Any]) -> dict[str, Any]:
    defaults = data.get("defaults") if isinstance(data.get("defaults"), dict) else data
    return {"docxer_defaults": defaults}


def _extract_dataview(data: dict[str, Any]) -> dict[str, Any]:
    overlay: dict[str, Any] = {}
    views = data.get("views") or data.get("customViews") or []
    if views:
        overlay["dataview_views"] = [str(x) for x in views]
    prefix = data.get("customPrefix") or data.get("prefix")
    if prefix:
        overlay["dataview_custom_prefix"] = str(prefix)
    return overlay


def _extract_datacore(data: dict[str, Any]) -> dict[str, Any]:
    overlay: dict[str, Any] = {}
    components = data.get("components") or data.get("customComponents") or []
    if components:
        overlay["datacore_components"] = [str(x) for x in components]
    return overlay
