# Source resumes (do not overwrite)

These PDFs are the official visual reference. Tailored output goes to `cv/generated/`. JobPilot must not modify these files.

| File | Role |
|---|---|
| `Derrick_Adjei_Data_Engineer.pdf` | Data Engineer (current) |
| `Derrick_Adjei_Backend_Engineer.pdf` | Backend Engineer (current) |
| `Derrick_Adjei_Resume.pdf` | Earlier one-page Data Engineer PDF from discovery |

Editable LaTeX that produces the same look (Leslie Cheng / Fira Sans / navy bars):

- `cv/data-engineer/master.tex`
- `cv/backend-engineer/master.tex`
- `cv/frontend-engineer/master.tex` (same template; no official source PDF was provided)

Compile:

```bash
./scripts/compile-resumes.sh
```
