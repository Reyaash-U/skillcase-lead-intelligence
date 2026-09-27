"""
Stage 3: Enrich each RELEVANT lead using Gemini (single batched request).

Reads : leads_classified.json
Writes: leads_enriched.json  (adds intent, profile, need, objection,
                              missing_info, next_action)

Note on 'public information': these are anonymous B2C leads with only a
name + city, which cannot be reliably looked up online. So we enrich from
the CONVERSATION TEXT itself, which is the reliable source here. (We state
this clearly in the presentation as a product-thinking decision.)
"""

import os
import json
import time
from google import genai
from google.genai import errors

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-3.8-flash"

INPUT = "leads_classified.json"
OUTPUT = "leads_enriched.json"

BUSINESS = """
Skillcase helps INDIAN NURSES move to GERMANY to work as nurses.
Path: learn German (A1 -> B1/B2) -> get placed in a German hospital.
Key facts that matter for sales:
  - B2 German is usually required to work as a nurse in Germany.
  - Nurses with B2 + experience are the most job-ready (hottest leads).
  - Common concerns: cost, timeline, eligibility of GNM vs BSc, confidence in German.
"""

PROMPT = """{business}

Below is a JSON list of relevant leads. For EACH lead, read the
conversation and notes, then extract useful sales context.

For each lead return an object with:
  - "lead_id": the lead's id
  - "intent": what the lead is trying to achieve (short)
  - "profile": one-line background (education, experience, german level)
  - "need": what they most need help with right now
  - "objection": their main concern/objection, or "None stated"
  - "missing_info": the most important info the salesperson should still collect
  - "next_action": the single best next step for the salesperson

Base everything ONLY on the data given. Do not invent facts.
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
        "education": l["education"],
        "experience": l["experience"],
        "german_level": l["german_level"],
        "goal": l["goal"],
        "conversation": l["conversation"],
        "notes": l["notes"],
    } for l in relevant]

    prompt = PROMPT.format(
        business=BUSINESS,
        leads_json=json.dumps(slim, ensure_ascii=False, indent=2),
    )

    print(f"Enriching {len(relevant)} relevant leads in ONE request...")
    text = call_gemini(prompt)
    text = text.replace("```json", "").replace("```", "").strip()
    results = json.loads(text)
    by_id = {r["lead_id"]: r for r in results}

    for lead in leads:
        r = by_id.get(lead["lead_id"])
        if r:
            lead["intent"] = r.get("intent", "")
            lead["profile"] = r.get("profile", "")
            lead["need"] = r.get("need", "")
            lead["objection"] = r.get("objection", "None stated")
            lead["missing_info"] = r.get("missing_info", "")
            lead["next_action"] = r.get("next_action", "")
            print(f"{lead['lead_id']:5} {lead['name']:18} | {lead['intent'][:45]}")
        else:
            # not-relevant leads get blank enrichment fields
            for k in ["intent", "profile", "need", "objection",
                      "missing_info", "next_action"]:
                lead.setdefault(k, "")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)

    print(f"\nDone. Enriched {len(results)} leads.")
    print(f"Saved -> {OUTPUT}")


if __name__ == "__main__":
    main()
