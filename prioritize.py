"""
Stage 4: Prioritize leads with a transparent rule-based score (NO AI).
Rule-based here is a deliberate choice: prioritization should be
explainable and consistent, not a black box.

Reads : leads_enriched.json
Writes: leads_prioritized.json  (adds priority_score, priority)
"""

import json

INPUT = "leads_enriched.json"
OUTPUT = "leads_prioritized.json"

# words in the conversation that signal buying intent
BUY_SIGNALS = ["call", "ready to start", "ready", "documents", "vacancies",
               "jobs", "openings", "interview", "tomorrow", "start"]

# words that signal an objection / hesitation
OBJECTION_SIGNALS = ["afford", "cost", "installment", "later", "nervous",
                     "difficult", "unsure", "worried", "expensive"]


def german_points(level):
    return {"B2": 3, "B1": 2, "A2": 1, "A1": 0}.get(level.upper(), 0)


def experience_points(exp):
    exp = exp.lower()
    if "month" in exp:
        return 0
    num = "".join(c for c in exp if c.isdigit())
    years = int(num) if num else 0
    if years >= 3:
        return 2
    if years >= 1:
        return 1
    return 0


def score_lead(lead):
    text = (lead["conversation"] + " " + lead["notes"]).lower()
    score = 0
    score += german_points(lead["german_level"])
    score += experience_points(lead["experience"])
    if any(sig in text for sig in BUY_SIGNALS):
        score += 2
    if any(sig in text for sig in OBJECTION_SIGNALS):
        score -= 1
    return score


def band(score):
    if score >= 5:
        return "High"
    if score >= 3:
        return "Medium"
    return "Low"


def main():
    with open(INPUT, encoding="utf-8") as f:
        leads = json.load(f)

    for lead in leads:
        if lead.get("relevant") != "Yes":
            lead["priority_score"] = None
            lead["priority"] = "Excluded"
            continue
        s = score_lead(lead)
        lead["priority_score"] = s
        lead["priority"] = band(s)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)

    # print sorted, highest priority first
    ranked = sorted(
        [l for l in leads if l["priority"] != "Excluded"],
        key=lambda l: l["priority_score"], reverse=True,
    )
    print("RANKED LEADS (highest first):\n")
    for l in ranked:
        print(f"{l['priority']:7} score={l['priority_score']:>2}  "
              f"{l['lead_id']:5} {l['name']:18} "
              f"[{l['german_level']}, {l['experience']}]")

    highs = sum(1 for l in leads if l["priority"] == "High")
    meds = sum(1 for l in leads if l["priority"] == "Medium")
    lows = sum(1 for l in leads if l["priority"] == "Low")
    print(f"\nHigh: {highs}   Medium: {meds}   Low: {lows}")
    print(f"Saved -> {OUTPUT}")


if __name__ == "__main__":
    main()
