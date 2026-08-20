import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

type AppRow = {
  id: string;
  status: string;
  match_score: number | null;
  recommendation: string | null;
  selected_resume_type: string | null;
  human_action: string | null;
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
        SUBMITTED appears only with confirmation evidence. HUMAN_ACTION_REQUIRED means a
        legitimate human-only step (CAPTCHA, login, LinkedIn, ToS).
      </p>
      <table className="table">
        <thead>
          <tr>
            <th>Status</th>
            <th>Score</th>
            <th>Resume</th>
            <th>Recommendation</th>
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
              <td>{row.human_action ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
