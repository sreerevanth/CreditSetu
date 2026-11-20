# Deploy CreditSetu (free public link)

The app is a single Streamlit project with no external services, so it deploys in a few minutes.

## Option 1 · Streamlit Community Cloud (recommended, free)

1. Merge the latest code into the `main` branch on GitHub.
2. Go to **https://share.streamlit.io** and sign in with your GitHub account.
3. Click **Create app → Deploy a public app from GitHub**.
4. Fill in:
   - **Repository:** `sreerevanth/CreditSetu`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL:** pick something short, e.g. `creditsetu`
5. *(Optional, for Claude mode)* Open **Advanced settings → Secrets** and add:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
   Without a key, the built-in offline agent runs everything.
6. Click **Deploy**. The first build takes 3–5 minutes (it installs the OCR model).

`packages.txt` installs the two system libraries the OCR engine needs; `requirements.txt` has the Python packages.

**Note:** Streamlit Cloud's disk is temporary. The bank queue resets when the app restarts and is re-seeded with demo files automatically. That's fine for a demo; production would use Postgres.

## Option 2 · Hugging Face Spaces (free)

1. Create a new Space → **Docker** → blank template.
2. Push this repo to the Space (or link it), keeping the `Dockerfile`.
3. In the Space settings, add a variable `PORT=7860`, and optionally a secret `ANTHROPIC_API_KEY`.

## Option 3 · Any Docker host (Render, Railway, Cloud Run)

```bash
docker build -t creditsetu .
docker run -p 8501:8501 creditsetu
```

Set `ANTHROPIC_API_KEY` as an environment variable to enable Claude mode.

## Before the demo: checklist

- [ ] Open the public link once, so the app is warm when judges arrive
- [ ] Click **⚡ See the 60-second demo** on the home page and check it reaches results
- [ ] Switch to **हिन्दी** and send one message
- [ ] Open **Bank officer** and click a file
- [ ] Have `data/sample_statement_sunita.pdf` and `data/sample_quotation_photo.jpg` downloaded, to show uploads live
