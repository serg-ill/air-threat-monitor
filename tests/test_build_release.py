"""Prevent private local files from being included in release archives."""

from __future__ import annotations

import json
from zipfile import ZipFile

import pytest

from scripts import build_release


@pytest.fixture
def release_tree(tmp_path, monkeypatch):
    integration = tmp_path / "custom_components" / "air_threat_monitor"
    integration.mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    (integration / "public.py").write_text("PUBLIC = True\n")
    (tmp_path / "README.md").write_text("Public documentation\n")
    manifest = tmp_path / "scripts" / "release-files.json"
    manifest.write_text(
        json.dumps(
            {
                "integration": ["public.py"],
                "manual": ["README.md"],
            }
        )
    )
    monkeypatch.setattr(build_release, "ROOT", tmp_path)
    monkeypatch.setattr(build_release, "INTEGRATION", integration)
    return tmp_path, integration, manifest


def test_archives_exclude_private_files_even_inside_integration(release_tree):
    root, integration, _ = release_tree
    for name in (
        "secrets.yaml",
        ".env",
        "custom-private.py",
        ".DS_Store",
        "backup.json",
        "private-photo.png",
        "assets/images/safe-private.png",
        ".storage/core.config_entries",
        "__pycache__/private.pyc",
    ):
        path = integration / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"PRIVATE-MARKER-DO-NOT-PUBLISH")
    for name in ("private-artwork/image.png", "docs/images/private.png"):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"PRIVATE-MARKER-DO-NOT-PUBLISH")

    for manual in (False, True):
        archive_path = root / f"test-{manual}.zip"
        build_release._build(archive_path, manual=manual)
        with ZipFile(archive_path) as archive:
            assert set(archive.namelist()) == (
                {"custom_components/air_threat_monitor/public.py", "README.md"}
                if manual
                else {"public.py"}
            )
            assert all(
                b"PRIVATE-MARKER" not in archive.read(name)
                for name in archive.namelist()
            )


@pytest.mark.parametrize(
    "name",
    [
        "../secret.py",
        "/tmp/secret.py",
        ".env",
        "assets/../secret.py",
        "assets//secret.py",
        "./public.py",
        "",
    ],
)
def test_allowlist_rejects_unsafe_paths(release_tree, name):
    _, _, manifest = release_tree
    manifest.write_text(json.dumps({"integration": [name]}))
    with pytest.raises(RuntimeError, match="Invalid release path"):
        build_release._files()


def test_allowlist_rejects_symlinks(release_tree):
    root, integration, manifest = release_tree
    (integration / "link.py").symlink_to(root / "README.md")
    manifest.write_text(json.dumps({"integration": ["link.py"]}))
    with pytest.raises(RuntimeError, match="Symlinks"):
        build_release._files()


def test_allowlist_rejects_symlink_directories(release_tree):
    root, integration, manifest = release_tree
    (integration / "linked").symlink_to(root, target_is_directory=True)
    manifest.write_text(json.dumps({"integration": ["linked/README.md"]}))
    with pytest.raises(RuntimeError, match="Symlinks"):
        build_release._files()


def test_allowlist_rejects_missing_files_and_duplicates(release_tree):
    _, _, manifest = release_tree
    manifest.write_text(json.dumps({"integration": ["missing.py"]}))
    with pytest.raises(RuntimeError, match="Missing allowlisted"):
        build_release._files()
    manifest.write_text(json.dumps({"integration": ["public.py", "public.py"]}))
    with pytest.raises(RuntimeError, match="Duplicate"):
        build_release._files()


def test_public_allowlist_covers_expected_integration_modules():
    paths = build_release._files()
    assert build_release.INTEGRATION / "provider.py" in paths
    assert build_release.INTEGRATION / "manifest.json" in paths
    assert len(paths) == len(set(paths))
    assert not any(
        "private" in str(path.relative_to(build_release.ROOT))
        for path in paths + build_release._files("manual")
    )
