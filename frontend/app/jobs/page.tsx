import { api, type JobRow } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function JobsPage() {
  let jobs: JobRow[] = [];
  try {
    jobs = await api<JobRow[]>("/api/v1/jobs");
  } catch {
    jobs = [];
  }
  return (
    <div>
      <h1>Jobs</h1>
      <p className="lede">Deduplicated postings from permitted sources. Match scores are transparent, not LLM vibes.</p>
      <table className="table">
        <thead>
          <tr>
            <th>Role</th>
            <th>Company</th>
            <th>Location</th>
            <th>Score</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => (
            <tr key={job.id}>
              <td>
                <a href={job.url} target="_blank" rel="noreferrer">
                  {job.title}
                </a>
              </td>
              <td>{job.company}</td>
              <td>{job.location}</td>
              <td>{job.match_score ?? "—"}</td>
              <td>
                <span className="badge">{job.status ?? "new"}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {jobs.length === 0 ? <p className="lede">No jobs ingested yet. A cycle runs every 15 minutes (Sweden first: Uppsala, Stockholm, Gothenburg, Malmö).</p> : null}
    </div>
  );
}
