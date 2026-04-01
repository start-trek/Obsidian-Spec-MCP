"""Integration tests — full round-trip through obsidian-spec-mcp and Obsidian REST API.

Exercises the recommended workflow:
  1. Generate a snippet via obsidian-spec-mcp
  2. Validate it
  3. Write it to the vault via Obsidian Local REST API
  4. Read it back
  5. Verify content matches

Requirements:
  - Obsidian running with the Local REST API plugin enabled
  - OBSIDIAN_API_KEY set in environment (or .env file)
  - Network access to https://127.0.0.1:27124

Run with:
  uv run pytest tests/test_integration.py -v -m integration
"""
from __future__ import annotations

import os
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path
from textwrap import dedent

import pytest

from obsidian_spec_mcp.config import load_effective_profile
from obsidian_spec_mcp.models import PluginConfigPaths
from obsidian_spec_mcp.renderers import generate_snippet
from obsidian_spec_mcp.validators import validate_markdown

# ---------------------------------------------------------------------------
# Obsidian REST API helpers
# ---------------------------------------------------------------------------
OBSIDIAN_BASE = "https://127.0.0.1:27124"
OBSIDIAN_API_KEY = os.environ.get("OBSIDIAN_API_KEY", "")
TEST_FOLDER = "_spec_mcp_integration_test"

# Allow self-signed certs from the Obsidian Local REST API
_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE


def _obsidian_available() -> bool:
    """Return True if Obsidian REST API is reachable and key is set."""
    if not OBSIDIAN_API_KEY:
        return False
    try:
        req = urllib.request.Request(
            f"{OBSIDIAN_BASE}/",
            headers={"Authorization": f"Bearer {OBSIDIAN_API_KEY}"},
        )
        urllib.request.urlopen(req, timeout=3, context=_SSL_CTX)
        return True
    except Exception:
        return False


def _put_note(vault_path: str, content: str) -> int:
    """Write (create or overwrite) a note via Obsidian REST API. Returns HTTP status."""
    url = f"{OBSIDIAN_BASE}/vault/{vault_path}"
    data = content.encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="PUT",
        headers={
            "Authorization": f"Bearer {OBSIDIAN_API_KEY}",
            "Content-Type": "text/markdown",
        },
    )
    resp = urllib.request.urlopen(req, timeout=10, context=_SSL_CTX)
    return resp.status


def _get_note(vault_path: str) -> str:
    """Read a note from the vault via Obsidian REST API."""
    url = f"{OBSIDIAN_BASE}/vault/{vault_path}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {OBSIDIAN_API_KEY}",
            "Accept": "text/markdown",
        },
    )
    resp = urllib.request.urlopen(req, timeout=10, context=_SSL_CTX)
    return resp.read().decode("utf-8")


def _delete_note(vault_path: str) -> None:
    """Delete a note from the vault via Obsidian REST API. Ignores 404."""
    url = f"{OBSIDIAN_BASE}/vault/{vault_path}"
    req = urllib.request.Request(
        url,
        method="DELETE",
        headers={"Authorization": f"Bearer {OBSIDIAN_API_KEY}"},
    )
    try:
        urllib.request.urlopen(req, timeout=10, context=_SSL_CTX)
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
SKIP_REASON = "Obsidian REST API not available (set OBSIDIAN_API_KEY and run Obsidian)"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not _obsidian_available(), reason=SKIP_REASON),
]


@pytest.fixture(autouse=True)
def _cleanup_test_folder():
    """Delete all notes created during the test."""
    created: list[str] = []
    yield created
    for path in created:
        _delete_note(path)


def _test_path(name: str) -> str:
    """Return a vault-relative path under the integration test folder."""
    return f"{TEST_FOLDER}/{name}"


# ---------------------------------------------------------------------------
# Pack intents for round-trip generation
# ---------------------------------------------------------------------------
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


# ===================================================================
# Per-pack round-trip: generate → validate → write → read → verify
# ===================================================================

class TestPerPackRoundTrip:
    """Generate a snippet, validate, write to vault, read back, and verify."""

    @pytest.mark.parametrize("pack_name", list(PACK_INTENTS.keys()))
    def test_generate_validate_write_read(self, pack_name, _cleanup_test_folder):
        intent = PACK_INTENTS[pack_name]
        title = f"Integration {pack_name}"
        snip = generate_snippet(pack_name, intent, title=title)

        # Validate
        report = validate_markdown(snip.markdown, [pack_name])
        errors = [i for i in report.issues if i.severity == "error"]
        assert len(errors) == 0, f"Generated {pack_name} snippet has errors: {errors}"

        # Write
        note_path = _test_path(f"{pack_name}_{intent}.md")
        _cleanup_test_folder.append(note_path)
        status = _put_note(note_path, snip.markdown)
        assert status in (200, 204), f"Write failed with status {status}"

        # Read back
        content = _get_note(note_path)
        assert len(content) > 0, "Read-back returned empty content"

        # Verify key content survived round-trip
        # (Obsidian REST API may normalize whitespace slightly)
        for key_fragment in _key_fragments(pack_name, title):
            assert key_fragment in content, \
                f"Expected '{key_fragment}' in read-back content for {pack_name}"


def _key_fragments(pack_name: str, title: str) -> list[str]:
    """Return pack-specific strings that must appear in the round-tripped note."""
    fragments = [title]
    if pack_name == "tasks":
        fragments.append("📅")
    elif pack_name == "templater":
        fragments.append("tp.")
    elif pack_name == "quickadd":
        fragments.append("{{")
    elif pack_name == "meta_bind":
        fragments.append("INPUT[")
    elif pack_name == "js_engine":
        fragments.append("js-engine")
    elif pack_name == "docxer":
        fragments.append(".docx")
    elif pack_name == "linter":
        fragments.append("Linter")
    return fragments


# ===================================================================
# Cross-pack round-trip
# ===================================================================

class TestCrossPackRoundTrip:
    def test_core_tasks_linter_round_trip(self, _cleanup_test_folder):
        """Generate core snippet, validate with multiple packs, write, read back."""
        snip = generate_snippet("core", "note", title="Cross-Pack Integration")
        report = validate_markdown(snip.markdown, ["core", "linter"])
        errors = [i for i in report.issues if i.severity == "error"]
        assert len(errors) == 0, f"Cross-pack validation errors: {errors}"

        note_path = _test_path("cross_pack_round_trip.md")
        _cleanup_test_folder.append(note_path)
        _put_note(note_path, snip.markdown)
        content = _get_note(note_path)
        assert "Cross-Pack Integration" in content


# ===================================================================
# Runtime-config round-trip (with effective profile)
# ===================================================================

CONFIGS_DIR = Path(__file__).resolve().parent.parent / "test_vault_configs"


class TestRuntimeConfigRoundTrip:
    @pytest.mark.skipif(not CONFIGS_DIR.exists(), reason="test_vault_configs not present")
    def test_profile_aware_generation(self, _cleanup_test_folder):
        """Load effective profile with configs, generate with it, validate, write, read."""
        paths = PluginConfigPaths(
            tasks_path=str(CONFIGS_DIR / "tasks.json"),
        )
        runtime = load_effective_profile("default", paths)
        profile = runtime.profile

        snip = generate_snippet("tasks", "task-line", title="Profile Round-Trip", profile=profile)
        report = validate_markdown(snip.markdown, ["tasks"], profile)
        errors = [i for i in report.issues if i.severity == "error"]
        assert len(errors) == 0, f"Profile-aware validation errors: {errors}"

        note_path = _test_path("profile_round_trip.md")
        _cleanup_test_folder.append(note_path)
        _put_note(note_path, snip.markdown)
        content = _get_note(note_path)
        assert "Profile Round-Trip" in content
