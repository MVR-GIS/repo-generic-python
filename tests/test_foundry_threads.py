import json
from pathlib import Path

import yaml

from tools.foundry_threads import extract_foundry_threads_chat


def _read_front_matter(md_text: str) -> dict:
    if not md_text.startswith("---\n"):
        raise AssertionError("Missing YAML front matter start")

    parts = md_text.split("---\n", 2)
    if len(parts) < 3:
        raise AssertionError("Malformed YAML front matter")

    yaml_text = parts[1].strip()
    return yaml.safe_load(yaml_text)


def test_extract_creates_expected_files(tmp_path: Path):
    fixture = Path("tests/fixtures/threads_export.json")
    export = json.loads(fixture.read_text(encoding="utf-8"))

    downloads_dir = tmp_path / "Downloads"
    downloads_dir.mkdir(parents=True)
    export_path = downloads_dir / "threads_export.json"
    export_path.write_text(json.dumps(export, indent=2), encoding="utf-8")

    sessions_dir = tmp_path / "dev" / "sessions"

    md_path = extract_foundry_threads_chat(
        export_path=None,
        session_date=None,
        topic=None,
        sessions_dir=sessions_dir,
        backup=True,
        quiet=True,
        downloads_dir=downloads_dir,
    )

    assert md_path.exists()
    assert md_path.name == "2026-05-03.md"

    raw_path = sessions_dir / ".raw" / "2026-05-03.threads_export.json"
    assert raw_path.exists()

    md_text = md_path.read_text(encoding="utf-8")
    fm = _read_front_matter(md_text)

    assert fm["title"] == export["metadata"]["title"]
    assert fm["created_at"] == export["metadata"]["createdAt"]
    assert fm["last_updated_at"] == export["metadata"]["lastUpdatedAt"]
    assert fm["foundry_user_id"] == export["metadata"]["userId"]

    assert fm["user_display_name"]  # non-empty
    assert fm["model_display_name"]  # non-empty

    assert fm["messages_total"] == 2
    assert fm["messages_sent"] == 1
    assert fm["messages_received"] == 1

    assert "## Conversation" in md_text


def test_extract_creates_backup_on_overwrite(tmp_path: Path):
    fixture = Path("tests/fixtures/threads_export.json")
    export = json.loads(fixture.read_text(encoding="utf-8"))

    downloads_dir = tmp_path / "Downloads"
    downloads_dir.mkdir(parents=True)
    export_path = downloads_dir / "threads_export.json"
    export_path.write_text(json.dumps(export, indent=2), encoding="utf-8")

    sessions_dir = tmp_path / "dev" / "sessions"

    md_path_1 = extract_foundry_threads_chat(
        sessions_dir=sessions_dir,
        quiet=True,
        downloads_dir=downloads_dir,
    )
    assert md_path_1.exists()

    export["conversation"][0]["SENT"]["content"] = "Hello again"
    export_path.write_text(json.dumps(export, indent=2), encoding="utf-8")

    md_path_2 = extract_foundry_threads_chat(
        sessions_dir=sessions_dir,
        quiet=True,
        downloads_dir=downloads_dir,
    )
    assert md_path_2.exists()

    backups_dir = sessions_dir / ".backups"
    assert backups_dir.exists()

    backups = list(backups_dir.glob("2026-05-03_backup_*.md"))
    assert len(backups) == 1

    md_text = md_path_2.read_text(encoding="utf-8")
    assert "Hello again" in md_text
