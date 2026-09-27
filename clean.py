"""
Stage 1: Clean & deduplicate the messy B2C leads.
Pure rule-based (no AI) — fast, deterministic, easy to explain.

Input : skillcase_messy_b2c_leads.csv
Output: leads_clean.json  (list of unique leads with a `data_flags` field)
"""

import csv
import json
import re

INPUT = "skillcase_messy_b2c_leads.csv"
OUTPUT = "leads_clean.json"


def norm_phone(raw: str) -> str:
    """Keep digits only, drop country code, keep last 10 digits."""
    digits = re.sub(r"\D", "", raw or "")
    return digits[-10:] if len(digits) >= 10 else digits


def norm_email(raw: str) -> str:
    return (raw or "").strip().lower()


def norm_experience(raw: str) -> str:
    """'2 yrs', '2 years', '2' -> '2 years'.  '6 months' stays."""
    if not raw:
        return ""
    raw = raw.strip().lower()
    if "month" in raw:
        return raw
    m = re.search(r"\d+", raw)
    return f"{m.group()} years" if m else raw


def norm_text(raw: str) -> str:
    """Fix ALL CAPS / weird casing on names, cities, goals."""
    if not raw:
        return ""
    raw = raw.strip()
    # if it's all caps or all lower, title-case it; otherwise leave as-is
    if raw.isupper() or raw.islower():
        return raw.title()
    return raw


def norm_goal(raw: str) -> str:
    raw = (raw or "").strip().lower()
    if "german" in raw:
        return "Work in Germany"
    if "canada" in raw:
        return "Work in Canada"
    if "uk" in raw:
        return "Work in UK"
    if "abroad" in raw:
        return "Work abroad"
    return norm_text(raw)


def load_rows():
    with open(INPUT, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def clean():
    rows = load_rows()
    seen = {}          # dedupe key -> stored lead
    unique = []

    for row in rows:
        phone = norm_phone(row["phone"])
        email = norm_email(row["email"])
        # dedupe key: phone is the most reliable shared identifier here
        key = phone or email

        flags = []
        if not row.get("email"):
            flags.append("missing_email")
        if not row.get("german_level"):
            flags.append("missing_german_level")
        if not row.get("experience"):
            flags.append("missing_experience")

        lead = {
            "lead_id": row["lead_id"],
            "name": norm_text(row["name"]),
            "phone": phone,
            "email": email,
            "city": norm_text(row["city"]),
            "education": row["education"].strip(),
            "experience": norm_experience(row["experience"]),
            "goal": norm_goal(row["goal"]),
            "german_level": row["german_level"].strip().upper(),
            "source": row["source"].strip(),
            "last_contacted": row["last_contacted"].strip(),
            "conversation": row["conversation"].strip(),
            "notes": row["notes"].strip(),
            "data_flags": flags,
        }

        if key in seen:
            # duplicate — record it against the original, skip from unique list
            seen[key]["duplicate_of"] = seen[key].get("duplicate_of", seen[key]["lead_id"])
            seen[key].setdefault("duplicate_ids", []).append(lead["lead_id"])
            continue

        seen[key] = lead
        unique.append(lead)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)

    # summary for your slides / README
    dupes = sum(len(l.get("duplicate_ids", [])) for l in unique)
    print(f"Total rows read     : {len(rows)}")
    print(f"Unique leads        : {len(unique)}")
    print(f"Duplicates merged   : {dupes}")
    print("Leads with data gaps:",
          sum(1 for l in unique if l["data_flags"]))
    for l in unique:
        if l.get("duplicate_ids"):
            print(f"  {l['lead_id']} ({l['name']}) <- dup: {l['duplicate_ids']}")


if __name__ == "__main__":
    clean()
