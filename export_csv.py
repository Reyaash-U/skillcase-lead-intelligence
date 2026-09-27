"""
Stage 7: Export the final processed leads to CSV (the dataset deliverable).
No AI. Reads leads_final.json, writes leads_final.csv with a clean schema.

Note: leads_final.json holds the 27 UNIQUE leads. The 3 duplicates
(L008, L028 -> L001;  L021 -> L004) are recorded on their originals via
`duplicate_ids`. We add explicit duplicate rows at the end so the CSV
accounts for all 30 original lead_ids transparently.
"""

import csv
import json

INPUT = "leads_final.json"
OUTPUT = "leads_final.csv"

COLUMNS = [
    "lead_id", "name", "phone", "email", "city",
    "education", "experience", "german_level", "goal", "source",
    "relevant", "relevance_reason", "relevance_confidence",
    "intent", "profile", "need", "objection",
    "missing_info", "next_action",
    "priority", "priority_score",
    "outreach",
    "qc_status", "qc_flags",
    "duplicate_of",
]


def row_from_lead(lead, override=None):
    override = override or {}
    row = {}
    for col in COLUMNS:
        if col in override:
            row[col] = override[col]
        elif col == "qc_flags":
            row[col] = " | ".join(lead.get("qc_flags", []))
        elif col == "duplicate_of":
            row[col] = ""  # originals aren't duplicates
        else:
            row[col] = lead.get(col, "")
    return row


def main():
    with open(INPUT, encoding="utf-8") as f:
        leads = json.load(f)

    rows = []

    # 1. the unique, processed leads
    for lead in leads:
        rows.append(row_from_lead(lead))

    # 2. explicit rows for the merged duplicates, pointing to their original
    for lead in leads:
        for dup_id in lead.get("duplicate_ids", []):
            rows.append(row_from_lead(lead, override={
                "lead_id": dup_id,
                "relevant": "Duplicate",
                "relevance_reason": f"Duplicate of {lead['lead_id']} "
                                    f"(same phone/email)",
                "relevance_confidence": "",
                "intent": "", "profile": "", "need": "", "objection": "",
                "missing_info": "", "next_action": "",
                "priority": "Excluded", "priority_score": "",
                "outreach": "",
                "qc_status": "Duplicate", "qc_flags": "",
                "duplicate_of": lead["lead_id"],
            }))

    # sort by lead_id so it reads like the original sheet
    rows.sort(key=lambda r: r["lead_id"])

    with open(OUTPUT, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows -> {OUTPUT}")
    print(f"  Unique processed leads : {len(leads)}")
    print(f"  Duplicate rows added   : {len(rows) - len(leads)}")
    print(f"  Total (should be 30)   : {len(rows)}")


if __name__ == "__main__":
    main()
