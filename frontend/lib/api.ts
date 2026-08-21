const API =
  process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function api<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  return res.json() as Promise<T>;
}

export type Status = {
  jobs_discovered: number;
  jobs_analyzed: number;
  strong_matches: number;
  applications_submitted: number;
  human_actions_required: number;
  projects_created: number;
  projects_upgraded: number;
  failed_applications: number;
  text: string;
};

export type JobRow = {
  id: string;
  title: string;
  company: string | null;
  location: string;
  country: string | null;
  url: string;
  status: string | null;
  match_score: number | null;
};
