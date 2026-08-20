import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "JobPilot",
  description: "Career-engineering control plane",
};

const links = [
  ["Overview", "/"],
  ["Jobs", "/jobs"],
  ["Applications", "/applications"],
  ["Projects", "/projects"],
  ["Reports", "/reports"],
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <aside className="side">
            <div className="brand">
              Job<span>Pilot</span>
            </div>
            <nav className="nav">
              {links.map(([label, href]) => (
                <Link key={href} href={href}>
                  {label}
                </Link>
              ))}
            </nav>
          </aside>
          <main className="main">{children}</main>
        </div>
      </body>
    </html>
  );
}
