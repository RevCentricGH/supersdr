"""DigestBuilder - assemble the weekly per-client digest sections.

``build`` joins the master-tracker call rows (read from the sheet, keyed by rep tab) with the
SmartLead campaign stats (keyed by campaign id) into one section dict per client, in config
order. Each section carries the client's call count, a disposition breakdown, and one entry per
configured campaign. An empty week yields zero counts, never an error.

The disposition column name is imported from ``sheet_reader`` so the two stay in lockstep: if the
sheet's column name changes, this join breaks loudly in the tests rather than silently counting
nothing.
"""
from weeklycheckin.sheet_reader import DISPOSITION_COLUMN


class DigestBuilder:
    def build(self, clients, sheet_rows, smartlead_stats, week):
        sections = []
        for client in clients:
            rows = []
            for tab in client.get("rep_tabs", []):
                rows.extend(sheet_rows.get(tab, []))
            dispositions = {}
            for row in rows:
                label = (row.get(DISPOSITION_COLUMN) or "").strip()
                if not label:
                    continue
                dispositions[label] = dispositions.get(label, 0) + 1
            campaigns = [
                {"campaign_id": cid, "stats": smartlead_stats.get(cid)}
                for cid in client.get("smartlead_campaign_ids", [])
            ]
            sections.append(
                {
                    "client": client.get("name", ""),
                    "week": week,
                    "calls": len(rows),
                    "dispositions": dispositions,
                    "campaigns": campaigns,
                }
            )
        return sections


def digest_has_activity(sections):
    """True if any client had calls or any campaign returned stats this week. An all-zero week
    has no activity; the caller still delivers, prefixed with a no-activity notice, so the
    recipient knows the run happened."""
    for s in sections:
        if s.get("calls"):
            return True
        for c in s.get("campaigns", []):
            if c.get("stats"):
                return True
    return False


def render_digest(sections):
    """Render the digest sections to plain text for printing to stdout."""
    lines = []
    for s in sections:
        lines.append(f"## {s['client']} - week {s['week']}")
        lines.append(f"Calls: {s['calls']}")
        if s["dispositions"]:
            lines.append("Dispositions:")
            for label, count in sorted(s["dispositions"].items()):
                lines.append(f"  - {label}: {count}")
        else:
            lines.append("Dispositions: none")
        lines.append("SmartLead campaigns:")
        if not s["campaigns"]:
            lines.append("  - (no campaigns configured)")
        for c in s["campaigns"]:
            st = c["stats"]
            if st is None:
                lines.append(f"  - campaign {c['campaign_id']}: no stats returned")
            else:
                lines.append(
                    f"  - campaign {c['campaign_id']}: sent {st['sent']}, "
                    f"opens {st['opens']} ({st['open_rate']:.1%}), "
                    f"replies {st['replies']} ({st['reply_rate']:.1%}), "
                    f"bounces {st['bounces']}"
                )
        lines.append("")
    return "\n".join(lines)
