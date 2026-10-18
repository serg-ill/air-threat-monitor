"""Build reproducible archives for HACS and manual installation."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
INTEGRATION = ROOT / "custom_components" / "air_threat_monitor"
DIST = ROOT / "dist"
HACS_ARCHIVE = DIST / "air-threat-monitor.zip"


def _version() -> str:
    manifest = json.loads((INTEGRATION / "manifest.json").read_text(encoding="utf-8"))
    version = manifest["version"]
    constants = (INTEGRATION / "const.py").read_text(encoding="utf-8")
    match = re.search(r'^VERSION: Final = "([^"]+)"$', constants, re.MULTILINE)
    if match is None or match.group(1) != version:
        raise RuntimeError("manifest.json and const.py versions do not match")
    return version


def _files(section: str = "integration") -> list[Path]:
    """Package only explicitly reviewed public files, never directory contents."""

    manifest = json.loads(
        (ROOT / "scripts" / "release-files.json").read_text(encoding="utf-8")
    )
    names = manifest[section]
    if not isinstance(names, list) or not names:
        raise RuntimeError(f"Empty or invalid release allowlist: {section}")
    base = INTEGRATION if section == "integration" else ROOT
    sources = []
    for name in names:
        if not isinstance(name, str):
            raise RuntimeError("Release paths must be strings")
        relative = Path(name)
        if (
            relative.is_absolute()
            or relative.as_posix() != name
            or any(part.startswith(".") for part in relative.parts)
        ):
            raise RuntimeError(f"Invalid release path: {name}")
        source = base / relative
        ancestors = (
            base.joinpath(*relative.parts[:i]) for i in range(len(relative.parts) + 1)
        )
        if any(path.is_symlink() for path in ancestors):
            raise RuntimeError(f"Symlinks are not allowed in releases: {name}")
        if not source.is_file():
            raise RuntimeError(f"Missing allowlisted release file: {name}")
        sources.append(source)
    if len(set(sources)) != len(sources):
        raise RuntimeError(f"Duplicate release paths: {section}")
    return sorted(sources)


def _write_file(archive: ZipFile, source: Path, target: Path) -> None:
    info = ZipInfo(target.as_posix(), date_time=(2026, 1, 1, 0, 0, 0))
    info.compress_type = ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, source.read_bytes())


def _build(archive_path: Path, *, manual: bool) -> None:
    with ZipFile(archive_path, "w") as archive:
        for source in _files():
            relative = source.relative_to(INTEGRATION)
            target = (
                Path("custom_components") / "air_threat_monitor" / relative
                if manual
                else relative
            )
            _write_file(archive, source, target)
        if manual:
            for source in _files("manual"):
                _write_file(archive, source, source.relative_to(ROOT))


def _validate_repository() -> None:
    hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
    if hacs.get("country") != "UA":
        raise RuntimeError("hacs.json must identify the supported country")
    if hacs.get("zip_release") is not True:
        raise RuntimeError("hacs.json must enable zip_release")
    if hacs.get("filename") != HACS_ARCHIVE.name:
        raise RuntimeError("hacs.json filename does not match the release archive")

    required = (
        ROOT / "README.md",
        ROOT / "NOTICE.md",
        ROOT / "brand" / "logo.png",
        ROOT / "brand" / "icon.png",
        INTEGRATION / "brand" / "icon.png",
        INTEGRATION / "brand" / "icon@2x.png",
        INTEGRATION / "brand" / "logo.png",
        INTEGRATION / "brand" / "logo@2x.png",
        INTEGRATION / "manifest.json",
        INTEGRATION / "assets" / "air-threat-radar-card.js",
        ROOT / "docs" / "images" / "demo-safe-signal.png",
        ROOT / "docs" / "images" / "demo-alert-signal.png",
        ROOT / "docs" / "images" / "demo-safe-theme-dark.png",
        ROOT / "docs" / "images" / "demo-safe-theme-light.png",
        ROOT / "docs" / "images" / "card-editor.png",
    )
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing release files: {', '.join(missing)}")


def main() -> None:
    """Validate source metadata and build both archive layouts."""

    version = _version()
    _validate_repository()
    _files()
    _files("manual")
    DIST.mkdir(exist_ok=True)
    for old_file in DIST.iterdir():
        if old_file.is_file():
            old_file.unlink()
        elif old_file.is_dir():
            shutil.rmtree(old_file)

    manual_archive = DIST / f"air-threat-monitor-{version}-manual.zip"
    _build(HACS_ARCHIVE, manual=False)
    _build(manual_archive, manual=True)

    checksums = []
    for archive in (HACS_ARCHIVE, manual_archive):
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        checksums.append(f"{digest}  {archive.name}")
    (DIST / "SHA256SUMS.txt").write_text("\n".join(checksums) + "\n", encoding="utf-8")

    print(f"Built Air Threat Monitor {version}")
    for archive in (HACS_ARCHIVE, manual_archive):
        print(f"- {archive.relative_to(ROOT)} ({archive.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
