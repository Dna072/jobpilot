import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function ReportsPage() {
  let text = "No weekly report yet.";
  try {
    const data = await api<{ text?: string; report?: unknown }>("/api/v1/reports/weekly");
    text = data.text || JSON.stringify(data.report, null, 2);
  } catch {
    /* empty */
  }
  return (
    <div>
      <h1>Weekly report</h1>
      <p className="lede">Funnel, skill demand, gaps, and strategy — emailed when SMTP is configured.</p>
      <pre>{text}</pre>
    </div>
  );
}
