"""Streamlit app for the QA Replay Evidence Kit.

Replays synthetic workflow event logs, classifies failures into three classes
(integration reliability / API contract / business logic), and produces a
go / no-go release decision with attached defect packet and risk summary.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import streamlit as st

from replay_harness import (
    classify,
    failures,
    gonogo_note,
    load_events,
    render_defect_packet,
    render_risk_summary,
)

ROOT = Path(__file__).parent
LOG_DIR = ROOT / "sample_logs"

st.set_page_config(
    page_title="QA Replay Evidence Kit — Isaac Maya",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 QA Replay Evidence Kit")
st.markdown(
    "**Replay the workflow. Catch the bugs your tests didn't.**  \n"
    "_Built to demonstrate: QA Lead · Release Engineer · SRE_"
)

with st.expander("📖 Why this exists", expanded=True):
    st.markdown(
        """
Test suites catch what you predicted. **Replay harnesses catch what you didn't.**

This kit replays synthetic workflow logs event-by-event, classifies any failures into three
actionable buckets (Integration reliability / API contract violation / Business logic regression),
and outputs a release decision a manager can sign — not just a pile of red logs.

The classification matters more than the count: an integration timeout is a different release
decision than a calculation mismatch. The kit makes that distinction visible.
"""
    )

with st.expander("🎯 What you're looking at"):
    st.markdown(
        """
- ✅ Event-by-event replay in stream style
- ✅ Three failure classes, each mapped to an ownership bucket and recommended action
- ✅ Defect packet ready to file (manager-readable, copy-pasteable)
- ✅ Go / No-Go release decision derived from failure mix, not severity vibes
- ✅ Pluggable — drop a new JSON log into `sample_logs/` and the harness handles it
"""
    )

st.divider()
st.header("🧪 Try it")

available_logs = sorted(LOG_DIR.glob("*.json"))
log_pick = st.selectbox("Pick a replay log", options=[p.name for p in available_logs])
log_path = LOG_DIR / log_pick

events = json.loads(log_path.read_text())

speed = st.slider("Replay speed (seconds per event)", min_value=0.0, max_value=1.0, value=0.15, step=0.05)

if st.button("▶️ Replay events", type="primary", use_container_width=True):
    stream_placeholder = st.empty()
    lines = []
    failed_so_far = 0
    for evt in events:
        icon = "✅" if evt["status"] == "pass" else "❌"
        suffix = ""
        if evt["status"] == "fail":
            fc, _ = classify(evt.get("error", ""))
            suffix = f"  \n   ↪ **{fc}** — `{evt.get('error', '')}`"
            failed_so_far += 1
        line = f"{icon} `{evt['case_id']}` · `{evt['step']}` — {evt['duration_ms']}ms{suffix}"
        lines.append(line)
        stream_placeholder.markdown("\n\n".join(lines))
        time.sleep(speed)

    items = failures(events)

    st.divider()
    # Go/No-Go banner
    has_blockers = any(i["failure_class"] in ("Business logic regression", "API contract violation") for i in items)
    has_gateable = any(i["failure_class"] == "Integration reliability" for i in items)
    if has_blockers:
        st.error("🛑 **NO-GO** — blocking failures detected. See defect packet below.")
    elif has_gateable:
        st.warning("🟡 **CONDITIONAL GO** — integration failure(s) may proceed with compensating control.")
    elif failed_so_far == 0:
        st.success("✅ **GO** — no failures. Standard sign-off only.")
    else:
        st.info(f"ℹ️ {failed_so_far} failure(s) detected; see breakdown below.")

    col_d, col_r = st.columns(2)
    with col_d:
        st.subheader("📋 Defect Packet")
        st.markdown(render_defect_packet(items))
    with col_r:
        st.subheader("📊 Risk Summary")
        st.markdown(render_risk_summary(events, items))

st.divider()
with st.expander("🧪 How to test it (guided tour)", expanded=True):
    st.markdown(
        """
**Step 1 — Replay the default log.** Hit ▶️. Watch the event stream — most pass (✅), some fail (❌).
Each failure carries its classification in real time.

**Step 2 — Read the verdict.** The default log has both a business-logic mismatch *and* an API contract
violation. That mix produces a 🛑 **NO-GO** — neither failure class can ship without a fix.

**Step 3 — Read the defect packet.** Each failure has a recommended owner (feature owner / platform owner /
triage lead) based on its class. That's the routing logic a release manager needs.

**Step 4 — Break it on purpose.** Edit `sample_logs/replay_events.json`, remove the mismatch and schema
failures, leave only the timeout. Re-run. Verdict should flip to 🟡 **CONDITIONAL GO** — integration
failures alone don't block release.

**Step 5 — Tune replay speed.** Slow it down to 1s/event to talk through the trace with a stakeholder, or
zero it to get instant verdict.
"""
    )

with st.expander("💼 What this proves about me"):
    st.markdown(
        """
**For QA Lead roles:** I classify failures by what they imply, not what they say. A timeout and a
calculation mismatch are different release decisions, and the kit makes that visible.

**For Release Engineer roles:** I produce one-line release decisions backed by evidence. The Go/No-Go
banner is derived from the failure mix, not from a severity field someone forgot to set.

**For SRE roles:** Replay is a tool, not a ritual. The kit produces ownership routing and
compensating-control framing — exactly the artifacts an on-call hand-off needs.

---

**Isaac Maya** — QA · Agentic AI · Data Quality  \n
📧 theisaacmaya@icloud.com · 💼 [LinkedIn](https://linkedin.com/in/isaac-maya) · 🔗 [Source](https://github.com/isaac-maya/qa-replay-evidence-kit) · 📝 [Essays](https://isaac-maya.github.io/essays/)
"""
    )
