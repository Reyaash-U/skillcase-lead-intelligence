"""
Stage 2: Classify ALL leads in a SINGLE Gemini request (batched).
This uses only 1 API call instead of 27 — stays well within the
free-tier daily quota (20 requests/day).

Reads : leads_clean.json
Writes: leads_classified.json  (adds relevant, reason, confidence)
"""

import os
import json
import time
from google import genai
from google.genai import errors

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-3.8-flash"

INPUT = "leads_clean.json"
OUTPUT = "leads_classified.json"

BUSINESS = """
Skillcase helps INDIAN NURSES move to GERMANY to work as nurses.
The path: learn German (A1 -> B1/B2) -> get placed in a German hospital.
A lead is only a good fit if BOTH are true:
  1. They are a nurse (BSc Nursing or GNM qualification).
  2. They want to work in GERMANY specifically.
Not a fit if: non-nursing profession (BBA, pharmacist, engineer, etc.)
              or they want a different country (Canada, UK, etc.).
"""

PROMPT = """{business}

Below is a JSON list of leads. Classify EVERY lead.

For each lead return an object with:
  - "lead_id": the lead's id
  - "relevant": "Yes" or "No"
  - "reason": one short sentence
  - "confidence": integer 0-100

Return a STRICT JSON array only, no extra text, no markdown.
Example: [{{"lead_id":"L001","relevant":"Yes","reason":"...","confidence":90}}]

LEADS:
{leads_json}
"""


def call_gemini(prompt, max_retries=5):
    for attempt in range(max_retries):
        try:
            resp = client.models.generate_content(model=MODEL, contents=prompt)
            return resp.text.strip()
        except errors.ClientError as e:
            if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                print(f"    rate limited, waiting 30s (attempt {attempt+1})...")
                time.sleep(30)
                continue
            raise
    raise RuntimeError("Still rate limited after retries")


def main():
    with open(INPUT, encoding="utf-8") as f:
        leads = json.load(f)

    # send only the fields the model needs to judge relevance
    slim = [{
        "lead_id": l["lead_id"],
        "name": l["name"],
        "education": l["education"],
        "experience": l["experience"],
        "goal": l["goal"],
        "german_level": l["german_level"],
        "conversation": l["conversation"],
        "notes": l["notes"],
    } for l in leads]

    prompt = PROMPT.format(
        business=BUSINESS,
        leads_json=json.dumps(slim, ensure_ascii=False, indent=2),
    )

    print(f"Sending all {len(leads)} leads in ONE request...")
    text = call_gemini(prompt)
    text = text.replace("```json", "").replace("```", "").strip()
    results = json.loads(text)

    # map results back onto the leads by lead_id
    by_id = {r["lead_id"]: r for r in results}
    for lead in leads:
        r = by_id.get(lead["lead_id"])
        if r:
            lead["relevant"] = r.get("relevant", "Unknown")
            lead["relevance_reason"] = r.get("reason", "")
            lead["relevance_confidence"] = r.get("confidence", 0)
        else:
            lead["relevant"] = "Missing"
            lead["relevance_reason"] = "not returned by model"
            lead["relevance_confidence"] = 0
        print(f"{lead['lead_id']:5} {lead['name']:18} "
              f"-> {lead['relevant']:3} ({lead['relevance_confidence']}%) "
              f"{lead['relevance_reason']}")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)

    relevant = sum(1 for l in leads if l["relevant"] == "Yes")
    print(f"\nDone. {relevant} relevant / {len(leads)} total.")
    print(f"Saved -> {OUTPUT}   (used just 1 API request)")


if __name__ == "__main__":
    main()
