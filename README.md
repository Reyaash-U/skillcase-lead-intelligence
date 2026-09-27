# Skillcase — AI Lead Intelligence Pipeline

Turns a messy spreadsheet of 30 B2C leads into a clean, enriched, prioritized,
and outreach-ready lead list — for **Skillcase**, which helps Indian nurses
move to Germany to work as nurses.

Built for the Product & GTM Associate — AI Builder assignment.

## What it does

Raw CSV → **Clean** → **AI Classify** → **AI Enrich** → **Prioritize** →
**AI Outreach** → **Quality Control** → Final dataset + interactive dashboard.

- **Clean** (rule-based): removes 3 duplicates, normalizes formatting, flags missing fields.
- **Classify** (Gemini): Relevant / Not Relevant + reason + confidence. Filters out
  non-nurses (BBA, pharmacist, engineer) and wrong markets (Canada, UK).
- **Enrich** (Gemini): intent, profile, need, objection, missing info, next action.
- **Prioritize** (rule-based, transparent scoring): High / Medium / Low.
- **Outreach** (Gemini): a personalized message per relevant lead — never a template,
  never guarantees a job.
- **Quality control** (rule-based): flags missing data, low AI confidence,
  priority/profile mismatches, and unverified claims in outreach for human review.

## Results

- 30 raw leads → 27 unique → 22 relevant.
- 5 correctly excluded (wrong profession / wrong country).
- 12 leads flagged by QC for human review.

## Tech

- **Pipeline:** Python + Google Gemini API (batched — the whole pipeline uses ~3 API calls).
- **UI:** React + Vite (interactive dashboard with filtering and per-lead detail).

## Run the pipeline

```bash
pip install google-genai
set GEMINI_API_KEY=your_key_here      # Windows
python clean.py
python classify.py
python enrich.py
python prioritize.py
python outreach.py
python qc.py
python export_csv.py
```

Output: `leads_final.json` and `leads_final.csv`.

## Run the dashboard

```bash
cd skillcase-ui
npm install
npm run dev
```

## Files

| File | Purpose |
|------|---------|
| `clean.py` | Dedupe + normalize |
| `classify.py` | AI relevance classification |
| `enrich.py` | AI lead enrichment |
| `prioritize.py` | Rule-based scoring |
| `outreach.py` | AI personalized messages |
| `qc.py` | Quality-control layer |
| `export_csv.py` | Final CSV export |
| `leads_final.csv` | Processed dataset (deliverable) |
| `skillcase-ui/` | React dashboard (prototype) |

## Design notes

- **AI where judgment is needed; rules where transparency matters.** Classification,
  enrichment, and outreach use AI; deduplication, prioritization, and QC are
  deterministic and explainable.
- **On "public information":** these are anonymous leads with only a name + city,
  which cannot be reliably looked up online. Enrichment therefore uses the
  conversation text — the reliable source — rather than guessing from a common name.
- **Batched API calls** keep the pipeline within the Gemini free tier and are how
  this would scale in production.
