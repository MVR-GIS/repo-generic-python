from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import platform
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


def extract_foundry_threads_chat(
    export_path: Optional[str | Path] = None,
    session_date: Optional[str | dt.date] = None,
    topic: Optional[str] = None,
    sessions_dir: str | Path = "dev/sessions",
    backup: bool = True,
    quiet: bool = False,
    downloads_dir: Optional[str | Path] = None,
) -> Path:
    """
    Extract a Foundry Threads chat export JSON file into a reproducible, human-readable
    markdown transcript with YAML front matter, and preserve the raw export JSON.

    This function is modeled after the behavior of `{reproducibleai}::extract_copilot_chat()`:

    - Minimal required arguments with sensible defaults
    - "Save often" workflow: re-running updates the *same* derived artifact
    - On overwrite, creates timestamped backups (default: enabled)

    Inputs
    ------
    export_path:
        Path to the Foundry Threads export JSON file (typically `threads_export.json`).
        If None (default), uses:
          - Windows: %USERPROFILE%\\Downloads\\threads_export.json
          - Other OS: ~/Downloads/threads_export.json

    session_date:
        Session date used in output naming.
        If None (default), attempts to parse `metadata.createdAt` from the export
        (RFC1123 format like "Sun, 03 May 2026 15:53:07 GMT"). If parsing fails,
        falls back to today's date.

        You may also pass:
          - a datetime.date object, or
          - a string "YYYY-MM-DD"

    topic:
        Optional topic suffix for multi-topic days. Mirrors `{reproducibleai}`:
        if None, the output is date-only (YYYY-MM-DD.md). If provided, the output
        is YYYY-MM-DD_<topic>.md, after sanitization.

    sessions_dir:
        Directory for session artifacts (default: "dev/sessions").

    backup:
        If True (default), when overwriting an existing session transcript,
        copy it to `dev/sessions/.backups/` with a timestamp suffix before
        writing the new transcript.

    quiet:
        If True, suppress informational messages.

    downloads_dir:
        Advanced override for the downloads directory used when export_path is None.

    Outputs (written)
    -----------------
    Committed artifacts (Option A):
      - dev/sessions/YYYY-MM-DD[_topic].md
          Human-readable transcript with YAML front matter.
      - dev/sessions/.raw/YYYY-MM-DD[_topic].threads_export.json
          Raw export preserved for audit and for re-deriving the transcript.

    Gitignored artifacts:
      - dev/sessions/.backups/
          Timestamped backups of the transcript created on overwrite.

    Returns
    -------
    Path
        The path to the written transcript markdown file.

    Usage (typical)
    ---------------
    1) Export Threads chat JSON from Foundry UI to `threads_export.json`
       (OS default Downloads directory).
    2) From repo root, run:

       python -m tools.foundry_threads

    3) Commit:
       - dev/sessions/YYYY-MM-DD*.md
       - dev/sessions/.raw/*.threads_export.json

    Notes
    -----
    - This function assumes offline/no-internet friendly operation.
    - The Foundry export format observed includes a `conversation` list with
      objects like {"SENT": {...}} and {"RECEIVED": {...}}.
    - A known export typo is handled: "diplayName" instead of "displayName".
    """
    sessions_dir = Path(sessions_dir)
    _ensure_dir(sessions_dir, quiet=quiet)

    export_path = _resolve_export_path(export_path=export_path, downloads_dir=downloads_dir)
    if not export_path.exists():
        raise FileNotFoundError(f"Export JSON not found: {export_path}")

    export_text = export_path.read_text(encoding="utf-8")
    export = json.loads(export_text)

    date_str = _resolve_session_date_str(session_date=session_date, export=export)
    topic_clean = _sanitize_topic(topic) if topic else None

    stem = date_str if topic_clean is None else f"{date_str}_{topic_clean}"
    md_path = sessions_dir / f"{stem}.md"

    raw_dir = sessions_dir / ".raw"
    _ensure_dir(raw_dir, quiet=quiet)
    raw_path = raw_dir / f"{stem}.threads_export.json"

    backups_dir = sessions_dir / ".backups"
    if backup:
        _ensure_dir(backups_dir, quiet=quiet)

    # Backup existing markdown (COPY, not move)
    if md_path.exists() and backup:
        backup_path = _make_backup_path(backups_dir, md_path.name)
        shutil.copy2(md_path, backup_path)
        if not quiet:
            print(f"Backed up existing session to: {backup_path}")

    # Write raw export (committed)
    raw_path.write_text(export_text, encoding="utf-8")
    if not quiet:
        print(f"Wrote raw export: {raw_path}")

    export_sha256 = _sha256_text(export_text)

    # Write transcript markdown (committed)
    transcript_md = _render_markdown(export=export, export_sha256=export_sha256)
    md_path.write_text(transcript_md, encoding="utf-8")
    if not quiet:
        print(f"Wrote transcript: {md_path}")

    return md_path


@dataclass(frozen=True)
class Message:
    """
    A normalized message extracted from a Foundry Threads export.

    Attributes
    ----------
    role:
        "user" for SENT messages, "assistant" for RECEIVED messages.
    display_name:
        Display name for user or model (if present).
    content:
        Message content as plain text (verbatim from export).
    """

    role: str
    display_name: str
    content: str


def _render_markdown(export: Dict[str, Any], export_sha256: str) -> str:
    """
    Render a Foundry Threads export as markdown with YAML front matter.

    Parameters
    ----------
    export:
        Parsed JSON export (dict).
    export_sha256:
        SHA256 hash of the raw JSON text (for integrity tracking).

    Returns
    -------
    str
        Markdown document text ending in a newline.
    """
    meta = export.get("metadata", {}) if isinstance(export, dict) else {}

    title = _as_str(meta.get("title"))
    created_at = _as_str(meta.get("createdAt"))
    last_updated_at = _as_str(meta.get("lastUpdatedAt"))
    user_id = _as_str(meta.get("userId"))

    messages = _extract_messages(export)

    user_display = _first_nonempty([m.display_name for m in messages if m.role == "user"])
    model_display = _first_nonempty([m.display_name for m in messages if m.role == "assistant"])

    counts_total = len(messages)
    counts_user = sum(1 for m in messages if m.role == "user")
    counts_assistant = sum(1 for m in messages if m.role == "assistant")

    front_matter = {
        "title": title,
        "created_at": created_at,
        "last_updated_at": last_updated_at,
        "foundry_user_id": user_id,
        "user_display_name": user_display,
        "model_display_name": model_display,
        "export_sha256": export_sha256,
        "messages_total": counts_total,
        "messages_sent": counts_user,
        "messages_received": counts_assistant,
        "source": {
            "platform": "foundry",
            "export_file": "threads_export.json",
            "format": "foundry_threads_export",
        },
    }

    yaml_text = yaml.safe_dump(front_matter, sort_keys=False, allow_unicode=True).strip()

    lines: List[str] = []
    lines.append("---")
    lines.append(yaml_text)
    lines.append("---")
    lines.append("")
    lines.append("# Threads session transcript")
    lines.append("")

    if title:
        lines.append("## Title")
        lines.append("")
        lines.append(title)
        lines.append("")

    lines.append("## Conversation")
    lines.append("")

    for i, m in enumerate(messages, start=1):
        role_label = "User" if m.role == "user" else "Assistant"
        name_part = f" — {m.display_name}" if m.display_name else ""
        lines.append(f"### {i}. {role_label}{name_part}")
        lines.append("")
        lines.append(m.content.strip() if m.content else "")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _extract_messages(export: Dict[str, Any]) -> List[Message]:
    """
    Extract normalized messages from the Foundry Threads export structure.

    Handles:
    - {"SENT": {...}} -> role="user"
    - {"RECEIVED": {...}} -> role="assistant"

    Also handles a known typo in some exports:
    - "diplayName" instead of "displayName" for SENT messages.
    """
    conv = export.get("conversation", [])
    if not isinstance(conv, list):
        return []

    out: List[Message] = []

    for item in conv:
        if not isinstance(item, dict) or len(item) != 1:
            continue

        key = next(iter(item.keys()))
        payload = item.get(key)
        if not isinstance(payload, dict):
            continue

        if key == "SENT":
            display = _as_str(payload.get("displayName")) or _as_str(payload.get("diplayName"))
            content = _as_str(payload.get("content"))
            out.append(Message(role="user", display_name=display, content=content))

        elif key == "RECEIVED":
            display = _as_str(payload.get("displayName"))
            content = _as_str(payload.get("content"))
            out.append(Message(role="assistant", display_name=display, content=content))

    return out


def _resolve_export_path(
    export_path: Optional[str | Path],
    downloads_dir: Optional[str | Path],
) -> Path:
    """
    Resolve the export JSON path.

    If export_path is provided, returns it as a Path.
    Otherwise returns <Downloads>/threads_export.json using OS defaults
    (Windows-first).
    """
    if export_path is not None:
        return Path(export_path)

    downloads = Path(downloads_dir) if downloads_dir is not None else _default_downloads_dir()
    return downloads / "threads_export.json"


def _default_downloads_dir() -> Path:
    """
    Determine the OS default Downloads directory (Windows-first).

    Windows:
      - %USERPROFILE%\\Downloads

    Other:
      - ~/Downloads
    """
    if platform.system().lower().startswith("win"):
        userprofile = os.environ.get("USERPROFILE")
        if userprofile:
            return Path(userprofile) / "Downloads"
    return Path.home() / "Downloads"


def _resolve_session_date_str(session_date: Optional[str | dt.date], export: Dict[str, Any]) -> str:
    """
    Resolve session date string used in output file naming.

    If session_date is None:
      - parse export.metadata.createdAt as RFC1123
      - else fallback to today's date

    If session_date is a date:
      - format YYYY-MM-DD

    If session_date is a string:
      - must match YYYY-MM-DD
    """
    if session_date is None:
        meta = export.get("metadata", {}) if isinstance(export, dict) else {}
        created = _as_str(meta.get("createdAt"))
        parsed = _try_parse_rfc1123(created) if created else None
        d = parsed.date() if parsed else dt.date.today()
        return d.strftime("%Y-%m-%d")

    if isinstance(session_date, dt.date):
        return session_date.strftime("%Y-%m-%d")

    s = str(session_date).strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        raise ValueError("session_date must be a date or 'YYYY-MM-DD'")
    return s


def _try_parse_rfc1123(s: str) -> Optional[dt.datetime]:
    """
    Try parsing Foundry's createdAt/lastUpdatedAt format:
      "Sun, 03 May 2026 15:53:07 GMT"

    Returns None if parsing fails.
    """
    try:
        return dt.datetime.strptime(s, "%a, %d %b %Y %H:%M:%S GMT")
    except Exception:
        return None


def _sanitize_topic(topic: str) -> str:
    """
    Sanitize a topic suffix for use in filenames.

    Mirrors `{reproducibleai}` behavior:
      - replace non [a-zA-Z0-9_-] with underscore
      - collapse multiple underscores
      - trim underscores
    """
    topic = topic.strip()
    if not topic:
        return ""
    topic_clean = re.sub(r"[^a-zA-Z0-9_-]", "_", topic)
    topic_clean = re.sub(r"_+", "_", topic_clean).strip("_")
    return topic_clean


def _sha256_text(text: str) -> str:
    """Return sha256 hex digest for the provided text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _ensure_dir(path: Path, quiet: bool = False) -> None:
    """Create directory (recursive) if missing."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        if not quiet:
            print(f"Created directory: {path}")


def _make_backup_path(backups_dir: Path, original_name: str) -> Path:
    """Create a timestamped backup path for an existing transcript."""
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = Path(original_name).stem
    return backups_dir / f"{stem}_backup_{timestamp}.md"


def _as_str(x: Any) -> str:
    """Coerce value to string; return empty string for None."""
    return "" if x is None else str(x)


def _first_nonempty(items: List[str]) -> str:
    """Return the first non-empty string; otherwise empty string."""
    for x in items:
        if x and str(x).strip():
            return str(x).strip()
    return ""


def _build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser for module execution."""
    p = argparse.ArgumentParser(
        description="Extract Foundry Threads chat export JSON into dev/sessions markdown + raw json (with backups)."
    )
    p.add_argument(
        "--export-path",
        default=None,
        help="Path to threads_export.json. Default: Downloads/threads_export.json",
    )
    p.add_argument(
        "--session-date",
        default=None,
        help="Session date YYYY-MM-DD. Default: parsed from export metadata.createdAt, else today.",
    )
    p.add_argument(
        "--topic",
        default=None,
        help="Optional topic suffix (sanitized). Default: none (date-only filename).",
    )
    p.add_argument(
        "--sessions-dir",
        default="dev/sessions",
        help="Sessions directory. Default: dev/sessions",
    )
    p.add_argument(
        "--no-backup",
        action="store_true",
        help="Disable backups (not recommended).",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress informational messages.",
    )
    p.add_argument(
        "--downloads-dir",
        default=None,
        help="Override downloads directory (advanced). Default: OS default.",
    )
    return p


def main(argv: Optional[List[str]] = None) -> None:
    """
    CLI entrypoint.

    Run from repo root:

      python -m tools.foundry_threads

    Or with options:

      python -m tools.foundry_threads --topic my_topic
    """
    p = _build_arg_parser()
    args = p.parse_args(argv)

    extract_foundry_threads_chat(
        export_path=args.export_path,
        session_date=args.session_date,
        topic=args.topic,
        sessions_dir=args.sessions_dir,
        backup=(not args.no_backup),
        quiet=args.quiet,
        downloads_dir=args.downloads_dir,
    )


if __name__ == "__main__":
    main()
