import { api, type Status } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function Page() {
  let stats: Status | null = null;
  let error: string | null = null;
  try {
    stats = await api<Status>("/api/v1/status");
  } catch (err) {
    error = err instanceof Error ? err.message : "API unavailable";
  }

  const cards = stats
    ? [
        ["Discovered", stats.jobs_discovered],
        ["Analyzed", stats.jobs_analyzed],
        ["Strong matches", stats.strong_matches],
        ["Submitted", stats.applications_submitted],
        ["Human action", stats.human_actions_required],
        ["Failed", stats.failed_applications],
        ["Projects", stats.projects_created],
        ["Upgrades", stats.projects_upgraded],
      ]
    : [];

  return (
    <div>
      <h1>Quality-adjusted pipeline</h1>
      <p className="lede">
        JobPilot scores European (Sweden-first) roles against Derrick Adjei’s documented
        experience and portfolio. It never invents employment, never bypasses CAPTCHA,
        and never marks an application submitted without evidence.
      </p>
      {error ? <p className="bad">Control plane offline: {error}</p> : null}
      <div className="grid">
        {cards.map(([k, v]) => (
          <div className="card" key={String(k)}>
            <div className="k">{k}</div>
            <div className="v">{v}</div>
          </div>
        ))}
      </div>
      {stats ? (
        <pre style={{ marginTop: 28 }}>{stats.text}</pre>
      ) : (
        <pre style={{ marginTop: 28 }}>{`jobpilot status\n(start the API to populate counters)`}</pre>
      )}
    </div>
  );
}
