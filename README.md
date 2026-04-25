# Intelligent Document Verification System with AI Reasoning

A working Flask prototype for document upload, browser camera capture, OCR, OpenCV tamper detection, SQLAlchemy storage, visual highlighting, API verification, and downloadable PDF reports.

## Folder Structure

```text
HACTIVERSE/
  app.py
  requirements.txt
  README.md
  document_verifier/
    __init__.py
    config.py
    models.py
    ocr.py
    detection.py
    reasoning.py
    routes.py
    report.py
    sample_data.py
    static/
      css/styles.css
      js/app.js
    templates/
      index.html
      result.html
  tests/
    test_detection.py
    test_api.py
  instance/
    verifier.sqlite3
  storage/
    uploads/
    processed/
    samples/
```

## Prerequisites

Install Python dependencies:

```powershell
python -m pip install -r requirements-dev.txt
```

Install the native Tesseract OCR binary:

- Windows: install from `https://github.com/UB-Mannheim/tesseract/wiki`
- Add the install folder, often `C:\Program Files\Tesseract-OCR`, to `PATH`
- Verify with:

```powershell
tesseract --version
```

If Tesseract is not installed, the app still runs and stores a clear OCR setup error, but OCR text extraction requires the native binary.

Optional Groq reasoning:

```powershell
$env:GROQ_API_KEY="your_groq_key"
$env:GROQ_MODEL="llama-3.3-70b-versatile"
python app.py
```

The app uses Groq's OpenAI-compatible chat completions endpoint (`https://api.groq.com/openai/v1/chat/completions`) to turn OCR and computer-vision evidence into a clearer reviewer explanation. If no key is configured, or Groq is unavailable, it falls back to deterministic local reasoning.

## Dataset Context

The verifier presents public document-analysis datasets as useful domain references for evaluation and future extension:

- DocTamper: tampered text detection in document images, https://github.com/qcf-568/DocTamper
- MIDV-500: identity document recognition from mobile video, https://huggingface.co/papers/1807.05786
- RVL-CDIP: document image classification/layout reference, https://huggingface.co/datasets/aharley/rvl_cdip

Confirm each dataset's license and access terms for your use case.

## Train A Real Model

The app can use a trained classifier artifact at:

```text
models/document_tamper_model.joblib
```

Train from a labeled real dataset folder:

```powershell
python scripts/train_document_model.py --dataset-dir data/document_tamper --output models/document_tamper_model.joblib
```

Expected folder format:

```text
data/document_tamper/
  authentic/
    image_001.png
  tampered/
    image_002.png
```

Or train from a CSV manifest:

```powershell
python scripts/train_document_model.py --manifest data/document_tamper/manifest.csv --output models/document_tamper_model.joblib
```

Manifest format:

```csv
image_path,label
authentic/image_001.png,authentic
tampered/image_002.png,tampered
```

Once the model file exists, uploads automatically include a trained-model document-level tamper signal in addition to localized OpenCV findings.

## Run Locally

```powershell
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Deploy To Railway

This repository is now Railway-ready for Python deployment:

- `Procfile` starts the app with Gunicorn using Railway's `$PORT`.
- `requirements.txt` includes `gunicorn` for production serving.
- `requirements.txt` includes `psycopg[binary]` for managed Postgres support.
- `document_verifier/config.py` normalizes `postgres://...` to `postgresql://...` for SQLAlchemy compatibility.

Deploy steps:

1. Push this repo to GitHub.
2. In Railway, create a new project from the GitHub repo.
3. Add environment variables:

```text
SECRET_KEY=replace-with-a-long-random-value
GROQ_API_KEY=your_groq_key_optional
GROQ_MODEL=llama-3.3-70b-versatile
```

4. Optional but recommended: add a Railway PostgreSQL service and set `DATABASE_URL` to that connection string.

Important Railway notes:

- If no `DATABASE_URL` is provided, the app falls back to SQLite.
- Local storage on Railway containers is ephemeral. For persistent uploads/reports, use object storage.
- OCR requires native Tesseract at runtime; without it, the app still runs and returns an OCR setup warning.

## Deploy To Vercel

This repository is ready for Vercel's Python/Flask runtime:

- `api/index.py` exports the Flask `app` object used by Vercel.
- `vercel.json` rewrites all routes to that Flask function.
- `.python-version` pins Python 3.12.
- `vercel.json` gives the image-processing function more time and memory.
- `.vercelignore` keeps local uploads, test outputs, SQLite files, and model artifacts out of the serverless bundle.
- On Vercel, generated uploads, processed images, reports, and the fallback SQLite database are written to `/tmp/hactiverse`.

Install the Vercel CLI and test locally:

```powershell
npm i -g vercel
python -m pip install -r requirements.txt
vercel dev
```

Deploy:

```powershell
vercel
vercel --prod
```

Set these environment variables in the Vercel project dashboard:

```text
SECRET_KEY=replace-with-a-long-random-value
GROQ_API_KEY=your_groq_key_optional
GROQ_MODEL=llama-3.3-70b-versatile
```

Important Vercel notes:

- The local `.env` file is ignored. Use Vercel environment variables for secrets.
- Vercel serverless storage is temporary. Upload history, generated images, reports, and SQLite records can disappear between cold starts. For production persistence, set `DATABASE_URL` to a managed database and move generated files to object storage such as Vercel Blob.
- OCR requires the native Tesseract binary. The app still deploys without it and returns an OCR setup message, but full OCR extraction needs a deployment environment where Tesseract is available.
- Large trained model files are ignored by default, and `scikit-learn` is kept in `requirements-dev.txt` to keep the Vercel bundle smaller. If you need the classifier in production, add `scikit-learn` back to production dependencies, store the model externally, or explicitly configure `DOCUMENT_TAMPER_MODEL_PATH` and include the artifact intentionally.

## Test the Demo

Generate a sample tampered document:

```powershell
python -m document_verifier.sample_data
```

Then upload:

```text
storage/samples/sample_tampered_document.png
```

Camera testing:

1. Start the server.
2. Open the UI.
3. Click the camera button.
4. Allow browser camera permission.
5. Capture and verify.

Run automated tests:

```powershell
pytest
```

## API

Verify a file:

```powershell
curl.exe -F "document=@storage/samples/sample_tampered_document.png" http://127.0.0.1:5000/api/verify
```

Fetch a stored result:

```text
GET /api/documents/<document_id>
```

Download a PDF report:

```text
GET /documents/<document_id>/report
```
