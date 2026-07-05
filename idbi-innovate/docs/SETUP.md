# Personal-laptop setup & run guide

Everything needed to run + deploy the MSME Financial Health Card. Author on the
office laptop; do all of this on your **personal** laptop.

---

## 1. Runtimes to install (do this now, in parallel)

| Tool | Version | Get it | Verify |
|---|---|---|---|
| **Python** | 3.10–3.12 (3.11 ideal) | python.org, or `brew install python@3.11` (Mac) | `python3 --version` |
| **Node.js** | 20 LTS (18+ ok) | nodejs.org (includes npm) | `node -v` && `npm -v` |
| **Git** | any recent | git-scm.com, or `brew install git` | `git --version` |

**Windows note:** during the Python installer, tick **"Add Python to PATH"**. Use
**PowerShell** for the commands below (`python` instead of `python3` on Windows).

Optional (not required — Hugging Face builds the container for you):
- **Docker Desktop** — only if you want to test the backend container locally.

---

## 2. Accounts to create (all free)

- **GitHub** — code hosting + the transfer target. github.com
- **Vercel** — frontend hosting; sign in **with GitHub**. vercel.com
- **Hugging Face** — backend hosting (Docker Space). huggingface.co
- **Google AI Studio API key** *(optional)* — for the Gemini "briefing" narration.
  aistudio.google.com → "Get API key" (free tier). The app works fully without it.

---

## 3. Transfer the files

Zip `idbi-innovate/` on the office laptop → move via personal cloud/USB → unzip on
personal laptop. Then:
```bash
cd idbi-innovate
git init && git add . && git commit -m "MSME Financial Health Card"
# create a repo on github.com, then:
git remote add origin https://github.com/<you>/idbi-innovate.git
git push -u origin main
```

---

## 4. Run the whole thing locally

### Backend (terminal 1)
```bash
cd idbi-innovate
python3 -m pip install -r backend/requirements.txt
python3 data/generate.py                 # creates data/output/
python3 -m ml.train_logreg               # portable PD model (runs anywhere)
uvicorn backend.app.main:app --reload --port 8000
# check: http://localhost:8000/docs
```

### (Optional) the stronger XGBoost model
```bash
python3 -m pip install -r ml/requirements.txt
python3 -m ml.train_sklearn              # writes model.joblib (backend auto-uses it)
python3 -m ml.shap_explain               # SHAP explainability artifacts
```
> To serve the XGBoost model, also uncomment sklearn/xgboost/joblib/numpy in
> `backend/requirements.txt` and reinstall.

### Frontend (terminal 2)
```bash
cd idbi-innovate/frontend
cp .env.local.example .env.local         # already points at localhost:8000
npm install
npm run dev
# open http://localhost:3000
```

---

## 5. Deploy (free)

### Backend → Hugging Face Space (Docker)
1. huggingface.co → New → **Space** → SDK **Docker** → blank.
2. Push this repo to the Space (or connect the GitHub repo).
3. Ensure the Space uses `backend/Dockerfile` (or copy it to repo root as `Dockerfile`).
4. It serves on port 7860 → your API base is `https://<user>-<space>.hf.space`.
5. *(Optional)* add `GEMINI_API_KEY` in Space **Settings → Secrets** for AI narration.

### Frontend → Vercel
1. vercel.com → New Project → import the GitHub repo.
2. **Root Directory = `frontend`**.
3. Env var: `NEXT_PUBLIC_API_BASE = https://<user>-<space>.hf.space`.
4. Deploy. Auto-rebuilds on every `git push`.

---

## 6. Demo-day tips
- **Warm the backend** (open the HF URL) a minute before presenting — free tiers sleep.
- **Record a backup demo video** regardless — never risk a live cold-start on stage.
- Set `FRONTEND_ORIGIN` on the backend to your Vercel URL to lock CORS in production.

---

## Quick reference — package lists
- **Data engine:** none (pure Python stdlib).
- **Backend:** `fastapi`, `uvicorn[standard]`, `pydantic`  → `backend/requirements.txt`
- **ML (full):** `scikit-learn`, `xgboost`, `numpy`, `joblib`, `shap`  → `ml/requirements.txt`
- **Frontend:** `next`, `react`, `react-dom`, `recharts`, `lucide-react` (+ dev: `typescript`, `tailwindcss`, `postcss`, `autoprefixer`)  → `npm install` reads `package.json`
