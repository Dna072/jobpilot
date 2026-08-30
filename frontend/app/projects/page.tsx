import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

type Payload = {
  inventory: Array<{
    name: string;
    kind: string;
    repository: string | null;
    evidence_strength: string;
    qa_passed: boolean;
    target_roles: string[];
  }>;
  requests: Array<{ name: string; status: string; github_url: string | null }>;
};

function describeProjectStatus(status: string): string {
  switch (status) {
    case "WAITING_FOR_REPOSITORY":
      return "Waiting for you to create the GitHub repository";
    case "REPOSITORY_FOUND":
      return "Repository found — starter code not pushed yet";
    case "PROJECT_BUILDING":
      return "Writing starter code";
    case "PROJECT_COMPLETE":
      return "Starter code is on GitHub";
    default:
      return status;
  }
}

export default async function ProjectsPage() {
  let data: Payload = { inventory: [], requests: [] };
  try {
    data = await api<Payload>("/api/v1/projects");
  } catch {
    /* empty */
  }
  return (
    <div>
      <h1>Portfolio</h1>
      <p className="lede">
        Professional products, NexDev work, and labelled portfolio repos. JobPilot will email
        you to create a GitHub repository when a new project is actually justified.
      </p>
      {data.requests.length ? (
        <>
          <h2>Repository requests</h2>
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Status</th>
                <th>GitHub</th>
              </tr>
            </thead>
            <tbody>
              {data.requests.map((r) => (
                <tr key={r.name}>
                  <td>{r.name}</td>
                  <td>{describeProjectStatus(r.status)}</td>
                  <td>{r.github_url ?? "waiting"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      ) : null}
      <table className="table">
        <thead>
          <tr>
            <th>Project</th>
            <th>Kind</th>
            <th>Evidence</th>
            <th>Roles</th>
          </tr>
        </thead>
        <tbody>
          {data.inventory.map((p) => (
            <tr key={p.name}>
              <td>{p.repository ? <a href={p.repository}>{p.name}</a> : p.name}</td>
              <td>{p.kind}</td>
              <td>{p.evidence_strength}</td>
              <td>{p.target_roles.join(", ")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
