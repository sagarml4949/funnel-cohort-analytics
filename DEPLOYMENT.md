# Deployment Guide

This project is a **Streamlit** app that reads its data from the committed
`data/processed/*.csv` files — no database or external services required. It is
already configured for the free tiers of the three most popular hosts:

| File | Purpose |
|---|---|
| `requirements.txt` | Python dependencies (root — auto-detected by every host) |
| `.streamlit/config.toml` | Headless server mode, disable usage stats |
| `Procfile` | Used by Render/Heroku: `streamlit run dashboard/app.py` |
| `render.yaml` | Render Blueprint for one-click deploy from GitHub |
| `deploy/deploy_github.py` | Publishes the project to GitHub via the REST API (no Git install needed) |

> The dashboard entry point is `dashboard/app.py`. The working directory on every
> host is the repo root, which is exactly what `app.py` expects
> (`BASE = parent-of-dashboard/`, data lives in `data/processed/`).

---

## Option A0 — One-command GitHub publish (no Git required)

If `git` is not installed on your machine, use the bundled script. It publishes
the whole project through the GitHub REST API (blobs → tree → commit → ref):

```bash
# 1. Create a token at https://github.com/settings/tokens
#    (classic with `repo`, or fine-grained with Contents + Administration: r/w)
# 2. Preview what will be uploaded (no network calls):
python deploy/deploy_github.py --repo funnel-cohort-analytics --dry-run
# 3. Publish:
python deploy/deploy_github.py --repo funnel-cohort-analytics --token ghp_xxxxxxxx
#    add --private for a private repo, or --owner <org> to publish to an org
```

It creates the repo (or updates an existing one with a new commit), uploads all
20 files (~2.5 MB) in a single commit, and prints the exact next clicks for
Streamlit Community Cloud. Options A and C below then take over.

---

## Option A — Streamlit Community Cloud (easiest, recommended)

1. Create a repo at **github.com/new** (public or private, no README needed).
2. Upload the project files:
   - Click **"uploading an existing file"** on the new repo page (works for
     folders too: drag the `dashboard/`, `data/`, `etl/`, `insights/`,
     `.streamlit/` folders and the root files into the browser).
   - Or install Git and run:
     ```bash
     git init
     git add .
     git commit -m "Funnel & cohort analytics dashboard"
     git branch -M main
     git remote add origin https://github.com/<YOUR_USERNAME>/<REPO_NAME>.git
     git push -u origin main
     ```
3. Go to **share.streamlit.io** → sign in with GitHub → **New app**.
4. Pick the repo, set **Main file path** to `dashboard/app.py`, and click **Deploy**.
5. Done — you get a free URL like `https://<app>.streamlit.app`.

Note: processed data is already committed, so no build steps run the ETL.
If you ever regenerate the CSVs, just commit them and Streamlit redeploys.

---

## Option B — Hugging Face Spaces (free, no Git required)

1. Create an account at **huggingface.co**, then click **New Space**:
   - Name: `funnel-cohort-analytics`
   - SDK: **Streamlit** (Space type: Docker)
   - (Optional) Public or private.
2. In the Space, click the **Files** tab → **Upload files** → drag and drop:
   - Everything **except** the existing `README.md` files (drop the folders
     `dashboard/`, `data/`, `etl/`, `insights/`, `.streamlit/` and the root files
     `requirements.txt`, `Procfile`, `render.yaml`, `.gitignore`).
3. Open/commit the Space `README.md` and put this at the very top (the Space
   needs this metadata; keep your project description below it):
   ```markdown
   ---
   title: Funnel & Cohort Analytics
   sdk: streamlit
   app_file: dashboard/app.py
   sdk_version: 1.63.0
   python_version: '3.11'
   ---
   ```
4. Commit. The Space builds in ~1–2 minutes and serves the app at
   `https://<your-username>-funnel-cohort-analytics.hf.space`.

---

## Option C — Render (free)

1. Push this folder to a GitHub repo (same steps as Option A).
2. At **render.com** → **New +** → **Blueprint** → connect the repo.
3. Render reads `render.yaml`, creates the web service automatically and deploys.
4. Alternative manual route: **New +** → **Web Service** → repo → set:
   - Build command: `pip install -r requirements.txt`
   - Start command: `streamlit run dashboard/app.py --server.port $PORT --server.address 0.0.0.0`
   - Instance type: Free.
5. You get a URL like `https://funnel-cohort-analytics.onrender.com`.

---

## Option D — Quick local / LAN preview (no cloud account)

```bash
pip install -r requirements.txt
streamlit run dashboard/app.py --server.address 0.0.0.0
```

Then open `http://localhost:8501` on this machine, or
`http://<LOCAL-IP>:8501` from any device on the same network.

---

## Troubleshooting

- **Blank page / "Please wait..." forever** — check the host's build logs; the
  most common cause is a missing dependency or the app file path being wrong.
- **`ModuleNotFoundError` in build logs** — confirm `requirements.txt` is at the
  repo root (not inside a subfolder).
- **App starts but shows the "Processed data not found" error** — the
  `data/processed/` CSVs were not committed. Upload `data/processed/*.csv`
  (5 files) to the repo root tree.
- **Python version** — the app works on any supported Python ≥ 3.9; cloud
  defaults (3.10–3.12) are fine. No `runtime.txt` is needed.