# JANSETU AI — Hackathon MVP

A single React + FastAPI civic-governance prototype with four AI modules:
- PolicyLens: upload a PDF and explain it in plain language.
- CivicWatch: classify a civic-issue image and save a complaint.
- SevaBot: compare a citizen's answers with eligibility rules supplied by the user.
- TruthScan: analyze a claim against evidence/source URLs supplied by the user. Without evidence, it deliberately returns **Unverified** rather than pretending to fact-check the internet.

## Requirements
- Python 3.10+
- Node.js 18+
- A Gemini API key (Google AI Studio). The app has a demo fallback if no key is configured, but real AI requires a key.

## 1. Start the backend

Open a terminal in `JANSETU-AI/backend`:

### Windows PowerShell
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and add your Gemini key:
```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
```

Then run:
```powershell
uvicorn app.main:app --reload
```

Backend: http://127.0.0.1:8000  
API docs: http://127.0.0.1:8000/docs

### macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env, then:
uvicorn app.main:app --reload
```

## 2. Start the frontend

Open a second terminal in `JANSETU-AI/frontend`:
```bash
npm install
npm run dev
```

Open the URL printed by Vite (usually http://localhost:5173).

## 3. How to demo
1. PolicyLens: upload a text-based government PDF. Scanned PDFs may need OCR; this MVP reports when no text is extracted.
2. CivicWatch: upload a civic issue image, review the AI classification, then save it as a complaint.
3. SevaBot: enter a service name, paste the official eligibility rules, and enter applicant details. It provides guidance, not a binding eligibility decision.
4. TruthScan: enter a claim and paste official/trusted source URLs or excerpts. The app will distinguish supported, contradicted, mixed/misleading, and unverified. Do not treat model output as definitive proof.

## 4. Notes
- This is a hackathon prototype, not an official government service.
- It does not submit real government applications or contact authorities.
- Use fictional/sample citizen data in demos. Do not upload Aadhaar, bank details, passwords, or other sensitive personal information.
- Gemini API key is only read by the backend; never put it in frontend code.
- SQLite database is created automatically at `backend/jansetu.db`.


## Demo Mode (no API key required)

Set `DEMO_MODE=true` and leave `GEMINI_API_KEY` empty in `backend/.env`. Restart the backend. All four workflows return illustrative sample results. CivicWatch uses text hints (not image understanding), PolicyLens extracts PDF text but returns sample explanations, SevaBot uses a simple topic-presence check, and TruthScan always returns Unverified. Do not use demo results for real government decisions.
