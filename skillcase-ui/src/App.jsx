import { useState, useMemo } from "react";
import "./App.css";
import LEADS from "./leads_final.json";

const ORD = { High: 0, Medium: 1, Low: 2, Excluded: 3 };

export default function App() {
  const [filter, setFilter] = useState("All");
  const [sel, setSel] = useState(null);

  const counts = useMemo(() => ({
    All: LEADS.length,
    Relevant: LEADS.filter((l) => l.relevant === "Yes").length,
    "Not relevant": LEADS.filter((l) => l.relevant === "No").length,
    "Needs review": LEADS.filter((l) => l.qc_status === "Needs review").length,
  }), []);

  const rows = useMemo(() => {
    let r = [...LEADS];
    if (filter === "Relevant") r = r.filter((l) => l.relevant === "Yes");
    else if (filter === "Not relevant") r = r.filter((l) => l.relevant === "No");
    else if (filter === "Needs review") r = r.filter((l) => l.qc_status === "Needs review");
    return r.sort(
      (a, b) => ORD[a.priority] - ORD[b.priority] || (b.priority_score || 0) - (a.priority_score || 0)
    );
  }, [filter]);

  const highCount = LEADS.filter((l) => l.priority === "High").length;

  return (
    <div className="app">
      <header className="hd">
        <h1>Skillcase — Lead Intelligence</h1>
        <p>30 raw leads → cleaned, classified, enriched, prioritized &amp; outreach-ready</p>
      </header>

      <div className="stats">
        <Stat n={highCount} label="High priority" cls="green" />
        <Stat n={counts.Relevant} label="Relevant" cls="blue" />
        <Stat n={counts["Not relevant"]} label="Excluded" cls="grey" />
        <Stat n={counts["Needs review"]} label="Flagged by QC" cls="red" />
      </div>

      <div className="tabs">
        {["All", "Relevant", "Not relevant", "Needs review"].map((f) => (
          <button key={f} className={"tab" + (filter === f ? " on" : "")} onClick={() => setFilter(f)}>
            {f} <span className="ct">{counts[f]}</span>
          </button>
        ))}
      </div>

      <div className="grid">
        <div className="tablewrap">
          <table>
            <thead>
              <tr>
                <th>ID</th><th>Name</th><th>Profile</th><th>Priority</th><th>Relevant</th><th>QC</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((l) => (
                <tr key={l.lead_id} onClick={() => setSel(l)} className={sel?.lead_id === l.lead_id ? "sel" : ""}>
                  <td className="mono">{l.lead_id}</td>
                  <td className="nm">{l.name}<div className="sub">{l.city}</div></td>
                  <td className="sub">{l.education}, {l.experience || "—"}, {l.german_level || "—"}</td>
                  <td>
                    <span className={"pill " + l.priority.toLowerCase()}>
                      {l.priority}{l.priority_score != null ? ` · ${l.priority_score}` : ""}
                    </span>
                  </td>
                  <td className="sub">
                    {l.relevant === "Yes"
                      ? <span className="ok">Yes · {l.relevance_confidence}%</span>
                      : <span className="grey">No</span>}
                  </td>
                  <td>
                    {l.qc_status === "Needs review"
                      ? <span className="flag">⚑ {l.qc_flags.length}</span>
                      : <span className="sub">OK</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <aside className="detail">
          {!sel ? (
            <div className="empty">Select a lead to see full detail →</div>
          ) : (
            <>
              <div className="dhd">
                <div>
                  <h2>{sel.name} <span className="mono sub">{sel.lead_id}</span></h2>
                  <p className="sub">
                    {sel.education} · {sel.experience || "exp ?"} · German {sel.german_level || "?"} · {sel.city}
                  </p>
                </div>
                <span className={"pill " + sel.priority.toLowerCase()}>{sel.priority}</span>
              </div>

              {sel.relevant === "No" ? (
                <Field label="Not relevant" val={sel.relevance_reason} />
              ) : (
                <>
                  <Field label="Intent" val={sel.intent} />
                  <Field label="Need" val={sel.need} />
                  <Field label="Objection" val={sel.objection} />
                  <Field label="Missing info" val={sel.missing_info} />
                  <Field label="Next action" val={sel.next_action} />
                  {sel.duplicate_ids?.length > 0 && (
                    <Field label="Duplicates merged" val={sel.duplicate_ids.join(", ")} />
                  )}
                  {sel.outreach && (
                    <div className="msg">
                      <div className="mlabel blue">Personalized outreach</div>
                      <p>{sel.outreach}</p>
                    </div>
                  )}
                </>
              )}

              {sel.qc_flags?.length > 0 && (
                <div className="qc">
                  <div className="mlabel red">⚑ Quality-control flags</div>
                  {sel.qc_flags.map((f, i) => (
                    <div key={i} className="qcf">{f}</div>
                  ))}
                </div>
              )}
            </>
          )}
        </aside>
      </div>
    </div>
  );
}

function Stat({ n, label, cls }) {
  return (
    <div className="stat">
      <div className={"num " + cls}>{n}</div>
      <div className="slabel">{label}</div>
    </div>
  );
}

function Field({ label, val }) {
  return (
    <div className="field">
      <div className="flabel">{label}</div>
      <div className="fval">{val || "—"}</div>
    </div>
  );
}