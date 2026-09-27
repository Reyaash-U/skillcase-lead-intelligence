"""
Stage 5: Generate personalized outreach for each RELEVANT lead
using Gemini (single batched request).

Reads : leads_prioritized.json
Writes: leads_outreach.json  (adds outreach)

The message must use the lead's SPECIFIC situation (german level,
experience, their stated concern), not a generic template.
"""

import os
import json
import time
from google import genai
from google.genai import errors

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-3.8-flash"

INPUT = "leads_prioritized.json"
OUTPUT = "leads_outreach.json"

BUSINESS = """
Skillcase helps INDIAN NURSES move to GERMANY to work as nurses
(German language training A1->B2 + placement in a German hospital).
Tone for outreach: warm, professional, WhatsApp-style, concise.
Indian nurse audience. No false promises (never guarantee a job).
"""

PROMPT = """{business}

Below is a JSON list of leads with their situation and main concern.
Write a PERSONALIZED outreach message for EACH lead.

Rules for every message:
  - 2 to 4 sentences, WhatsApp-friendly, warm and professional.
  - Reference their SPECIFIC situation (German level, experience) and
    directly address their stated objection/need if any.
  - End with a clear, low-pressure next step (e.g. a quick call).
  - Do NOT guarantee a job. Do NOT use a generic template.
  - Start with "Hi {{first name}},"

For each lead return an object with:
  - "lead_id": the lead's id
  - "outreach": the message text

Return a STRICT JSON array only, no markdown, no extra text.

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
        except errors.ServerError as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                print(f"    server busy, waiting 15s (attempt {attempt+1})...")
                time.sleep(15)
                continue
            raise
    raise RuntimeError("Failed after retries")


def main():
    with open(INPUT, encoding="utf-8") as f:
        leads = json.load(f)

    relevant = [l for l in leads if l.get("relevant") == "Yes"]

    slim = [{
        "lead_id": l["lead_id"],
        "name": l["name"],
        "german_level": l["german_level"],
        "experience": l["experience"],
        "intent": l.get("intent", ""),
        "need": l.get("need", ""),
        "objection": l.get("objection", ""),
        "priority": l.get("priority", ""),
    } for l in relevant]

    prompt = PROMPT.format(
        business=BUSINESS,
        leads_json=json.dumps(slim, ensure_ascii=False, indent=2),
    )

    print(f"Writing outreach for {len(relevant)} leads in ONE request...")
    text = call_gemini(prompt)
    text = text.replace("```json", "").replace("```", "").strip()
    results = json.loads(text)
    by_id = {r["lead_id"]: r for r in results}

    for lead in leads:
        r = by_id.get(lead["lead_id"])
        lead["outreach"] = r.get("outreach", "") if r else ""

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)

    # show a couple of examples
    print("\n--- sample messages ---")
    for lead in leads:
        if lead.get("outreach"):
            print(f"\n[{lead['priority']}] {lead['lead_id']} {lead['name']}:")
            print(lead["outreach"])
            break
    for lead in reversed(leads):
        if lead.get("outreach"):
            print(f"\n[{lead['priority']}] {lead['lead_id']} {lead['name']}:")
            print(lead["outreach"])
            break

    print(f"\nDone. Saved -> {OUTPUT}")


if __name__ == "__main__":
    main()
