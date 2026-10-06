#!/usr/bin/env python3
"""Safe local state helper for P2P ATLAS, CAPSULE, feedback, and metrics."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


CAPSULE_PROFILES = {
    "task": ["Objective", "Progress", "Decisions", "Constraints", "Verified evidence", "Artifacts", "Blockers", "Next action"],
    "brainstorm": ["Original seed", "Promising options", "Valuable wording or voice", "Rejected options and why", "Unresolved tensions", "Next experiment"],
    "research": ["Research question", "Source and claim IDs", "Confirmed facts", "Inferences", "Disputes", "Unknowns", "Retrieval gaps", "Next query"],
    "incident": ["Impact", "Timeline", "Current state", "Evidence", "Hypotheses (not facts)", "Actions and owners", "Rollback state", "Next checkpoint"],
}


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def root_for(project: str) -> Path:
    root = Path(project).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Project directory does not exist: {root}")
    return root / ".p2p" / "state"


def read_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default.copy()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"Expected a JSON object in {path}")
    return value


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def atlas_default() -> dict:
    return {"goal": "", "steps": [], "current": "", "next": "", "blockers": [], "updated_at": now()}


def metrics_default() -> dict:
    return {"tasks": 0, "completed_steps": 0, "corrections": 0, "ratings": [], "notes": [], "updated_at": now()}


def cmd_init(args: argparse.Namespace) -> None:
    root = root_for(args.project)
    write_json(root / "atlas.json", read_json(root / "atlas.json", atlas_default()))
    write_json(root / "metrics.json", read_json(root / "metrics.json", metrics_default()))
    (root / "capsules").mkdir(parents=True, exist_ok=True)
    print(root)


def cmd_atlas_show(args: argparse.Namespace) -> None:
    path = root_for(args.project) / "atlas.json"
    print(json.dumps(read_json(path, atlas_default()), ensure_ascii=False, indent=2))


def cmd_atlas_set(args: argparse.Namespace) -> None:
    path = root_for(args.project) / "atlas.json"
    data = read_json(path, atlas_default())
    if args.goal is not None:
        data["goal"] = args.goal
    if args.current is not None:
        data["current"] = args.current
    if args.next is not None:
        data["next"] = args.next
    if args.add_step:
        data.setdefault("steps", []).append({"name": args.add_step, "status": "pending", "check": args.check or ""})
    data["updated_at"] = now()
    write_json(path, data)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_atlas_blocker(args: argparse.Namespace) -> None:
    path = root_for(args.project) / "atlas.json"
    data = read_json(path, atlas_default())
    blockers = data.setdefault("blockers", [])
    if args.clear:
        blockers.clear()
    elif args.text and args.text not in blockers:
        blockers.append(args.text)
    data["updated_at"] = now()
    write_json(path, data)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_atlas_complete(args: argparse.Namespace) -> None:
    atlas_path = root_for(args.project) / "atlas.json"
    metrics_path = root_for(args.project) / "metrics.json"
    data = read_json(atlas_path, atlas_default())
    steps = data.setdefault("steps", [])
    target = None
    if args.index is not None:
        if args.index < 1 or args.index > len(steps):
            raise SystemExit(f"Step index must be between 1 and {len(steps)}")
        target = steps[args.index - 1]
    else:
        target = next((s for s in steps if s.get("status") != "completed"), None)
    if target is None:
        raise SystemExit("No incomplete step found")
    target["status"] = "completed"
    data["current"] = ""
    pending = next((s for s in steps if s.get("status") != "completed"), None)
    data["next"] = pending.get("name", "") if pending else ""
    data["updated_at"] = now()
    write_json(atlas_path, data)
    metrics = read_json(metrics_path, metrics_default())
    metrics["completed_steps"] = int(metrics.get("completed_steps", 0)) + 1
    metrics["updated_at"] = now()
    write_json(metrics_path, metrics)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def safe_name(name: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", name.strip()).strip(".-")
    if not value:
        raise SystemExit("Capsule name must contain a letter or number")
    return value[:80]


def cmd_capsule_save(args: argparse.Namespace) -> None:
    root = root_for(args.project)
    atlas = read_json(root / "atlas.json", atlas_default())
    if args.body and args.body_file:
        raise SystemExit("Use either --body or --body-file, not both")
    if args.body_file:
        body_path = Path(args.body_file).expanduser().resolve()
        if not body_path.is_file():
            raise SystemExit(f"Capsule body file not found: {body_path}")
        body = body_path.read_text(encoding="utf-8")
    else:
        body = args.body or ""
    prompts = "\n".join(f"- {field}:" for field in CAPSULE_PROFILES[args.profile])
    text = (
        f"# P2P CAPSULE — {args.name}\n\n"
        "- Schema: p2p-capsule/2\n"
        f"- Profile: {args.profile}\n"
        f"- Saved: {now()}\n"
        f"- Goal: {atlas.get('goal', '')}\n"
        f"- Current: {atlas.get('current', '')}\n"
        f"- Next: {atlas.get('next', '')}\n"
        f"- Blockers: {', '.join(atlas.get('blockers', [])) or 'none'}\n\n"
        f"## {args.profile.title()} continuation fields\n\n"
        f"{prompts}\n\n"
        "## Captured session material\n\n"
        f"{body.strip()}\n"
    )
    path = root / "capsules" / f"{safe_name(args.name)}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(path)


def cmd_capsule_load(args: argparse.Namespace) -> None:
    path = root_for(args.project) / "capsules" / f"{safe_name(args.name)}.md"
    if not path.exists():
        raise SystemExit(f"Capsule not found: {path}")
    print(path.read_text(encoding="utf-8"))


def cmd_feedback(args: argparse.Namespace) -> None:
    path = root_for(args.project) / "metrics.json"
    data = read_json(path, metrics_default())
    data["ratings"].append({"rating": args.rating, "target": args.target or "p2p", "note": args.note or "", "at": now()})
    if args.rating == "bad":
        data["corrections"] = int(data.get("corrections", 0)) + 1
    data["updated_at"] = now()
    write_json(path, data)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_metrics(args: argparse.Namespace) -> None:
    path = root_for(args.project) / "metrics.json"
    print(json.dumps(read_json(path, metrics_default()), ensure_ascii=False, indent=2))


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project", default=".", help="Project directory; defaults to current directory")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("init").set_defaults(func=cmd_init)
    atlas = sub.add_parser("atlas")
    atlas_sub = atlas.add_subparsers(dest="atlas_command", required=True)
    atlas_sub.add_parser("show").set_defaults(func=cmd_atlas_show)
    aset = atlas_sub.add_parser("set")
    aset.add_argument("--goal")
    aset.add_argument("--current")
    aset.add_argument("--next")
    aset.add_argument("--add-step")
    aset.add_argument("--check")
    aset.set_defaults(func=cmd_atlas_set)
    blocker = atlas_sub.add_parser("blocker")
    blocker.add_argument("text", nargs="?")
    blocker.add_argument("--clear", action="store_true")
    blocker.set_defaults(func=cmd_atlas_blocker)
    complete = atlas_sub.add_parser("complete")
    complete.add_argument("--index", type=int)
    complete.set_defaults(func=cmd_atlas_complete)
    capsule = sub.add_parser("capsule")
    capsule_sub = capsule.add_subparsers(dest="capsule_command", required=True)
    save = capsule_sub.add_parser("save")
    save.add_argument("name")
    save.add_argument("--profile", choices=tuple(CAPSULE_PROFILES), default="task")
    save.add_argument("--body")
    save.add_argument("--body-file")
    save.set_defaults(func=cmd_capsule_save)
    load = capsule_sub.add_parser("load")
    load.add_argument("name")
    load.set_defaults(func=cmd_capsule_load)
    feedback = sub.add_parser("feedback")
    feedback.add_argument("rating", choices=("good", "ok", "bad"))
    feedback.add_argument("--target")
    feedback.add_argument("--note")
    feedback.set_defaults(func=cmd_feedback)
    sub.add_parser("metrics").set_defaults(func=cmd_metrics)
    return p


if __name__ == "__main__":
    args = parser().parse_args()
    args.func(args)
