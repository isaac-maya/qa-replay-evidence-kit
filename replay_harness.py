"""Replay synthetic workflow logs and generate QA evidence."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).parent
LOG_PATH = ROOT / "sample_logs" / "replay_events.json"
DEFECT_PATH = ROOT / "defect_packet.md"
RISK_PATH = ROOT / "risk_summary.md"


def classify(error: str) -> tuple[str, str]:
    if "timeout" in error:
        return "Integration reliability", "Service dependency or retry policy"
    if "schema" in error or "missing field" in error:
        return "API contract violation", "Schema drift or missing response field"
    if "mismatch" in error:
        return "Business logic regression", "Calculation or rule change"
    return "Unknown", "Needs triage"


def load_events() -> list[dict]:
    return json.loads(LOG_PATH.read_text(encoding="utf-8"))


def failures(events: list[dict]) -> list[dict]:
    output = []
    for event in events:
        if event["status"] == "fail":
            failure_class, root_cause = classify(event.get("error", ""))
            output.append({**event, "failure_class": failure_class, "root_cause": root_cause})
    return output


def render_defect_packet(items: list[dict]) -> str:
    lines = [
        "# Defect Packet",
        "",
        "## Sendable Summary",
        "",
        "This sample shows how a QA engineer can turn failing replay output into a compact evidence packet with ownership clues and release implications. It is intentionally small, but the format is meant to look like something a team could use in a real decision.",
        "",
        "## Summary",
        "",
        f"Failures found: {len(items)}",
        "",
        "| Case | Step | Failure class | Evidence | Root-cause bucket |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in items:
        lines.append(f"| {item['case_id']} | {item['step']} | {item['failure_class']} | {item.get('error', '')} | {item['root_cause']} |")
    triage = []
    owners = {
        "Business logic regression": "feature owner",
        "API contract violation": "API/platform owner",
        "Integration reliability": "platform/API owner",
        "Unknown": "triage lead",
    }
    seen_classes: set[str] = set()
    for item in items:
        fc = item["failure_class"]
        if fc not in seen_classes:
            seen_classes.add(fc)
            owner = owners.get(fc, "triage lead")
            triage.append(f"Assign {fc.lower()} ({item['step']}) to {owner} for review.")
    triage.append("Keep evidence packet attached to release decision so failures are reproducible.")
    numbered = [f"{i}. {step}" for i, step in enumerate(triage, start=1)]
    lines.extend(["", "## Recommended Triage", "", *numbered, ""])
    return "\n".join(lines)


def gonogo_note(items: list[dict]) -> str:
    blockers = [i for i in items if i["failure_class"] in ("Business logic regression", "API contract violation")]
    gateable = [i for i in items if i["failure_class"] == "Integration reliability"]
    lines = []
    if blockers:
        cases = ", ".join(sorted({i["case_id"] for i in blockers}))
        steps = " / ".join(sorted({i["step"] for i in blockers}))
        classes = " / ".join(sorted({i["failure_class"] for i in blockers}))
        lines.append(f"Do not release: {classes} in {cases} ({steps}) requires an owner and fix or documented rollback.")
    if gateable:
        cases = ", ".join(sorted({i["case_id"] for i in gateable}))
        steps = " / ".join(sorted({i["step"] for i in gateable}))
        lines.append(f"Conditional ship: integration failure in {cases} ({steps}) may proceed with an explicit compensating control if isolated and retry-safe.")
    if not lines:
        lines.append("No blocking failures. Release may proceed after standard sign-off.")
    return " ".join(lines)


def render_risk_summary(events: list[dict], items: list[dict]) -> str:
    failed_cases = {item["case_id"] for item in items}
    buckets = Counter(item["failure_class"] for item in items)
    risk = "High" if any(item["failure_class"] == "Business logic regression" for item in items) else "Medium"
    return "\n".join([
        "# Release Risk Summary",
        "",
        "This summary is designed for go/no-go discussion: what failed, what kind of failure it is, and whether the release can move with a compensating control.",
        "",
        f"- Events replayed: {len(events)}",
        f"- Failed cases: {len(failed_cases)}",
        f"- Risk level: {risk}",
        "",
        "## Failure Buckets",
        "",
        *[f"- {name}: {count}" for name, count in buckets.items()],
        "",
        "## Go / No-Go Note",
        "",
        gonogo_note(items),
        "",
    ])


def main() -> None:
    events = load_events()
    items = failures(events)
    DEFECT_PATH.write_text(render_defect_packet(items), encoding="utf-8")
    RISK_PATH.write_text(render_risk_summary(events, items), encoding="utf-8")
    print(f"Replayed {len(events)} events; found {len(items)} failures.")


if __name__ == "__main__":
    main()
