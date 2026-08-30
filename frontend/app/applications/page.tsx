import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

type AppRow = {
  id: string;
  status: string;
  match_score: number | null;
  recommendation: string | null;
  selected_resume_type: string | null;
  human_action: string | null;
  preview_url: string | null;
};

export default async function ApplicationsPage() {
  let rows: AppRow[] = [];
  try {
    rows = await api<AppRow[]>("/api/v1/applications");
  } catch {
    rows = [];
  }
  return (
    <div>
      <h1>Applications</h1>
      <p className="lede">
        Nothing is sent to a company until you open the review email and choose Send this
        application or submit it yourself. SUBMITTED only appears with confirmation from
        the company site.
      </p>
      <table className="table">
        <thead>
          <tr>
            <th>Status</th>
            <th>Score</th>
            <th>Resume</th>
            <th>Recommendation</th>
            <th>Review</th>
            <th>Human action</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id}>
              <td>
                <span className={`badge ${row.status === "SUBMITTED" ? "good" : row.status === "FAILED" ? "bad" : "warn"}`}>
                  {row.status}
                </span>
              </td>
              <td>{row.match_score ?? "—"}</td>
              <td>{row.selected_resume_type ?? "—"}</td>
              <td>{row.recommendation ?? "—"}</td>
              <td>{row.preview_url ? <a href={row.preview_url}>Review draft</a> : "—"}</td>
              <td>{row.human_action ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
