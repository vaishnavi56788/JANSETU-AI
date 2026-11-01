import os, json, uuid, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import fitz
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import base64
from groq import Groq

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_FILE, override=True)
DB_PATH = BASE_DIR / "jansetu.db"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

client = (
    Groq(api_key=GROQ_API_KEY)
    if GROQ_API_KEY and not DEMO_MODE
    else None
)

app = FastAPI(title="JANSETU AI API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS complaints (
            id TEXT PRIMARY KEY, category TEXT, severity TEXT, description TEXT,
            department TEXT, location TEXT, status TEXT, created_at TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS applications (
            id TEXT PRIMARY KEY, service_name TEXT, applicant_summary TEXT,
            guidance TEXT, status TEXT, created_at TEXT
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS verifications (
            id TEXT PRIMARY KEY, claim TEXT, verdict TEXT, explanation TEXT,
            evidence TEXT, created_at TEXT
        )""")
init_db()

def ask_ai(
    prompt: str,
    image_bytes: Optional[bytes] = None,
    mime_type: Optional[str] = None
) -> str:

    if not client:
        raise HTTPException(
            503,
            "Groq API key is not configured. Check backend/.env"
        )

    try:
        if image_bytes:
            encoded_image = base64.b64encode(
                image_bytes
            ).decode("utf-8")

            image_type = mime_type or "image/jpeg"

            user_content = [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{image_type};base64,{encoded_image}"
                    }
                }
            ]
        else:
            user_content = prompt

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are JANSETU AI, a civic assistance "
                        "assistant. Give clear, factual and "
                        "easy-to-understand responses."
                    )
                },
                {
                    "role": "user",
                    "content": user_content
                }
            ],
            temperature=0.3,
            max_completion_tokens=2048
        )

        return response.choices[0].message.content or ""

    except Exception as exc:
        raise HTTPException(
            502,
            f"Groq AI request failed: {str(exc)[:300]}"
        )

def parse_json(text: str):
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start:end+1])
            except json.JSONDecodeError:
                pass
        raise HTTPException(502, "AI returned an unexpected format. Please try again.")

@app.get("/")
def root():
    return {"name": "JANSETU AI", "status": "running", "docs": "/docs"}

@app.get("/api/health")
def health():
    return {"status": "ok", "ai_configured": bool(client), "demo_mode": DEMO_MODE}

@app.post("/api/policy/analyze")
async def analyze_policy(file: UploadFile = File(...), language: str = Form("English")):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Please upload a PDF file.")
    data = await file.read()
    if len(data) > 12 * 1024 * 1024:
        raise HTTPException(413, "PDF must be smaller than 12 MB.")
    try:
        doc = fitz.open(stream=data, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        page_count = len(doc)
    except Exception:
        raise HTTPException(400, "Could not read this PDF.")
    if len(text.strip()) < 80:
        raise HTTPException(400, "Very little text was extracted. This may be a scanned PDF; OCR is not enabled in this MVP.")
    text = text[:12000]
    prompt = f"""
You are PolicyLens, an assistant explaining public policy. Analyze ONLY the supplied document.
Respond in valid JSON with keys: title, summary, eligibility (array), benefits (array),
documents (array), deadlines (array), important_conditions (array), caveats (array).
Use simple {language}. Preserve dates and amounts exactly. If information is absent, say
'Not specified in the provided document'. Do not invent rules. Include page references where
possible in each item. This is informational, not legal advice.
DOCUMENT:
{text}
"""
    if DEMO_MODE:
        result = {"title": file.filename.rsplit(".", 1)[0].replace("_", " ").title(), "summary": "DEMO MODE: PDF text extracted. This is illustrative sample output, not an analysis of the document's actual provisions.", "eligibility": ["Check the eligibility section in the original notification."], "benefits": ["Verify benefits and amounts in the original document."], "documents": ["Use only documents listed in the original notice."], "deadlines": ["Verify the closing date in the original PDF."], "important_conditions": ["Sample output; do not rely on it for an application."], "caveats": ["No AI analysis was performed in Demo Mode.", "Verify all details against the original government notification."]}
    else:
        result = parse_json(ask_ai(prompt))
    result["demo_mode"] = DEMO_MODE
    result["pages_read"] = page_count
    result["source_file"] = file.filename
    return result

@app.post("/api/civic/classify")
async def classify_civic(file: UploadFile = File(...), description: str = Form(""), location: str = Form("")):
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(400, "Upload a JPG, PNG, or WEBP image.")
    data = await file.read()
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(413, "Image must be smaller than 8 MB.")
    prompt = f"""
Analyze this citizen-submitted civic issue image. User description: {description or "None"}.
Approximate location supplied by user: {location or "Not supplied"}.
Return valid JSON with keys category, severity, description, suggested_department,
recommended_next_step, visual_limitations. category should be one of Road damage,
Garbage, Water leakage, Drainage, Streetlight, Pollution, Other. severity should be
Low, Medium, or High. Be cautious: do not claim certainty from an image alone and do not
infer an exact location. This is a triage suggestion, not an official decision.
"""
    if DEMO_MODE:
        hint = (description + " " + file.filename).lower()
        choices = [("garbage", "Garbage", "Municipal sanitation department"), ("kachra", "Garbage", "Municipal sanitation department"), ("water", "Water leakage", "Water supply department"), ("leak", "Water leakage", "Water supply department"), ("drain", "Drainage", "Municipal drainage department"), ("light", "Streetlight", "Municipal electrical department"), ("pothole", "Road damage", "Public works department"), ("road", "Road damage", "Public works department"), ("smoke", "Pollution", "Pollution control authority")]
        category, dept = next(((c, d) for k, c, d in choices if k in hint), ("Other", "Municipal helpdesk (review required)"))
        result = {"category": category, "severity": "Medium", "description": description or "Civic issue submitted for review.", "suggested_department": dept, "recommended_next_step": "Review the details before submitting.", "visual_limitations": ["Demo uses text hints, not image understanding.", "Severity is illustrative and needs human review."]}
    else:
        result = parse_json(ask_ai(prompt, data, file.content_type))
    result["demo_mode"] = DEMO_MODE
    result["status"] = "Ready for citizen review"
    return result

class ComplaintCreate(BaseModel):
    category: str
    severity: str
    description: str
    department: str = "To be reviewed"
    location: str = ""

@app.post("/api/civic/submit")
def submit_complaint(item: ComplaintCreate):
    cid = "JAN-" + uuid.uuid4().hex[:8].upper()
    now = datetime.now(timezone.utc).isoformat()
    with db() as conn:
        conn.execute("INSERT INTO complaints VALUES (?,?,?,?,?,?,?,?)",
            (cid, item.category, item.severity, item.description, item.department,
             item.location, "Submitted", now))
    return {"id": cid, "status": "Submitted", "created_at": now}

@app.get("/api/civic/complaints")
def list_complaints():
    with db() as conn:
        rows = conn.execute("SELECT * FROM complaints ORDER BY created_at DESC LIMIT 100").fetchall()
    return [dict(r) for r in rows]

class EligibilityRequest(BaseModel):
    service_name: str
    official_rules: str = Field(min_length=20)
    applicant_details: str = Field(min_length=2)
    language: str = "English"

@app.post("/api/seva/check-eligibility")
def check_eligibility(item: EligibilityRequest):
    prompt = f"""
You are SevaBot. Compare the applicant details only against the official rules pasted below.
Return valid JSON keys: assessment (Potentially eligible / Not enough information /
Likely not eligible), reasons (array), missing_information (array), required_documents
(array), next_steps (array), disclaimer. Explain in {item.language}. Do not invent criteria.
Never make a final government eligibility decision. If details are incomplete, say so.
SERVICE: {item.service_name}
OFFICIAL RULES:
{item.official_rules[:18000]}
APPLICANT DETAILS:
{item.applicant_details[:5000]}
"""
    if DEMO_MODE:
        rules = item.official_rules.lower(); details = item.applicant_details.lower()
        topics = [w for w in ["income", "age", "student", "resident", "disability", "category", "marks"] if w in rules]
        missing = [w for w in topics if w not in details]
        result = {"assessment": "Not enough information" if missing else "Potentially eligible for further review", "reasons": ["Demo checks only whether some rule topics appear in the applicant details."], "missing_information": ["Please confirm: " + w for w in missing] or ["No obvious missing topic detected; manually compare every condition."], "required_documents": ["Refer to the official scheme notification for required documents."], "next_steps": ["Read the complete official notification.", "Confirm each condition with the issuing department.", "Use the official portal for applications."], "disclaimer": "Illustrative demo only; not an eligibility decision."}
    else:
        result = parse_json(ask_ai(prompt))
    aid = "APP-" + uuid.uuid4().hex[:8].upper()
    now = datetime.now(timezone.utc).isoformat()
    with db() as conn:
        conn.execute("INSERT INTO applications VALUES (?,?,?,?,?,?)",
            (aid, item.service_name, item.applicant_details[:500], json.dumps(result), "Guidance generated", now))
    result["tracking_id"] = aid
    result["demo_mode"] = DEMO_MODE
    return result

class VerifyRequest(BaseModel):
    claim: str = Field(min_length=8)
    evidence: str = ""
    source_urls: list[str] = []

@app.post("/api/truth/verify")
def verify_claim(item: VerifyRequest):
    if not item.evidence.strip() and not item.source_urls:
        result = {
            "verdict": "Unverified",
            "explanation": "No supporting sources or evidence were supplied. This prototype does not independently search the live web, so it cannot confirm this claim.",
            "evidence_assessment": [],
            "limitations": ["A language model cannot establish truth from the claim alone.", "Provide official or trusted source excerpts/URLs for comparison."]
        }
    elif DEMO_MODE:
        result = {"verdict": "Unverified", "explanation": "DEMO MODE: No independent fact-checking or source retrieval was performed. Check the claim against trusted primary sources.", "evidence_assessment": ["Supplied evidence and URLs are recorded for demonstration only."], "missing_evidence": ["A trusted source excerpt directly addressing the claim."], "limitations": ["This demo does not fetch URLs or analyze image/video authenticity."]}
    else:
        prompt = f"""
You are TruthScan, an evidence analysis assistant. Assess the claim ONLY against the evidence
provided below. Do not pretend to have opened URLs or searched the web. URLs are leads, not
evidence unless their contents are pasted. Return valid JSON keys: verdict (Supported /
Contradicted / Misleading or missing context / Unverified), explanation, evidence_assessment
(array), missing_evidence (array), limitations (array). Quote or summarize the supplied evidence
accurately. If evidence is insufficient, use Unverified. Never assert that an image/video is a
deepfake based only on appearance.
CLAIM: {item.claim}
SUPPLIED EVIDENCE EXCERPTS:
{item.evidence[:16000]}
SOURCE URLS (not fetched by this MVP):
{json.dumps(item.source_urls[:10])}
"""
        result = parse_json(ask_ai(prompt))
    vid = "VER-" + uuid.uuid4().hex[:8].upper()
    now = datetime.now(timezone.utc).isoformat()
    with db() as conn:
        conn.execute("INSERT INTO verifications VALUES (?,?,?,?,?,?)",
            (vid, item.claim, result.get("verdict", "Unverified"), result.get("explanation", ""),
             json.dumps(item.source_urls), now))
    result["report_id"] = vid
    result["demo_mode"] = DEMO_MODE
    return result

@app.get("/api/dashboard/stats")
def dashboard_stats():
    with db() as conn:
        complaints = conn.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
        apps = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
        verifications = conn.execute("SELECT COUNT(*) FROM verifications").fetchone()[0]
        recent = conn.execute("SELECT id,category,severity,status,created_at FROM complaints ORDER BY created_at DESC LIMIT 5").fetchall()
    return {"complaints": complaints, "applications": apps, "verifications": verifications,
            "recent_complaints": [dict(r) for r in recent]}
