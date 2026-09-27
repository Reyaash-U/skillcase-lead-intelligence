"""
Stage 6: Quality Control (NO AI) — validate the pipeline's output and
flag records that a human should review before acting on them.

Reads : leads_outreach.json
Writes: leads_final.json  (adds qc_flags, qc_status)

This is the safety net: AI output is NOT trusted blindly.
It produces the "problems caught" examples required by the assignment.
"""

import json

INPUT = "leads_outreach.json"
OUTPUT = "leads_final.json"

# claims in outreach that must be human-verified before sending
UNVERIFIED_CLAIM_WORDS = ["vacanc", "opening", "openings", "employers",
                          "hospitals actively", "actively interviewing",
                          "guarantee"]


def qc_one(lead):
    flags = []

    if lead.get("relevant") != "Yes":
        return flags  # not-relevant leads need no outreach QC

    # 1. Missing critical contact / profile data
    if not lead.get("email"):
        flags.append("MISSING_EMAIL: no email on file — cannot send email outreach")
    if not lead.get("german_level"):
        flags.append("MISSING_GERMAN_LEVEL: language level unknown — job-readiness uncertain")
    if not lead.get("experience"):
        flags.append("MISSING_EXPERIENCE: experience not provided — verify before ranking")

    # 2. Low classifier confidence
    if lead.get("relevance_confidence", 100) < 85:
        flags.append(
            f"LOW_CONFIDENCE: classifier only {lead['relevance_confidence']}% sure — human check")

    # 3. Priority vs profile mismatch (senior B2 nurse ranked below High)
    is_senior_b2 = (lead.get("german_level", "").upper() == "B2")
    exp = lead.get("experience", "")
    years = int("".join(c for c in exp if c.isdigit()) or 0) if "month" not in exp.lower() else 0
    if is_senior_b2 and years >= 5 and lead.get("priority") != "High":
        flags.append(
            f"PRIORITY_MISMATCH: B2 + {years}yrs but ranked {lead['priority']} "
            f"— likely under-scored, human review")

    # 4. Unverified factual claims in the outreach message
    msg = lead.get("outreach", "").lower()
    for w in UNVERIFIED_CLAIM_WORDS:
        if w in msg:
            flags.append(
                "UNVERIFIED_CLAIM: outreach mentions specific jobs/employers/guarantee "
                "— verify facts before sending")
            break

    return flags


def main():
    with open(INPUT, encoding="utf-8") as f:
        leads = json.load(f)

    flagged = []
    for lead in leads:
        flags = qc_one(lead)
        lead["qc_flags"] = flags
        lead["qc_status"] = "Needs review" if flags else "OK"
        if flags:
            flagged.append(lead)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)

    print(f"QC complete. {len(flagged)} leads flagged for review.\n")
    for lead in flagged:
        print(f"--- {lead['lead_id']} {lead['name']} ({lead['priority']}) ---")
        for fl in lead["qc_flags"]:
            print(f"    - {fl}")
    print(f"\nSaved -> {OUTPUT}")


if __name__ == "__main__":
    main()
