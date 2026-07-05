# Frontend — Underwriter Cockpit (Next.js)

The visual layer: applicant list, Health Card (RAG gauge, pillar radar, reason codes,
suggested limit, confidence, ML PD), the **traditional-vs-alternate-data** comparison,
the **what-if consent simulator**, mocked rails, and the **portfolio impact** dashboard.

## Run locally (personal laptop)
```bash
cd frontend
cp .env.local.example .env.local     # points at http://localhost:8000 by default
npm install
npm run dev                          # http://localhost:3000
```
(Make sure the backend is running — see ../backend/README.md.)

## Deploy — Vercel (free)
1. Push the repo to GitHub.
2. On vercel.com → New Project → import the repo → set **Root Directory = `frontend`**.
3. Add env var `NEXT_PUBLIC_API_BASE = https://<your-space>.hf.space`.
4. Deploy. Vercel auto-builds on every push.

## Stack
Next.js 14 (App Router) · TypeScript · Tailwind CSS · Recharts · lucide-react.
