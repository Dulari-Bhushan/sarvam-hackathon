import base64, json, os, re
import requests
from flask import Flask, jsonify, request, send_from_directory

HERE = os.path.dirname(os.path.abspath(__file__))
_env = os.path.join(HERE, ".env")
if os.path.exists(_env):
    for line in open(_env, encoding="utf-8"):
        if "=" in line:
            k, v = line.strip().split("=", 1)
            os.environ.setdefault(k, v)
KEY = os.environ["SARVAM_API_KEY"]
H = {"api-subscription-key": KEY}
BASE = "https://api.sarvam.ai"

app = Flask(__name__)

LANGS = {"hi-IN": "Hindi", "en-IN": "English", "ta-IN": "Tamil", "te-IN": "Telugu",
         "bn-IN": "Bengali", "mr-IN": "Marathi", "gu-IN": "Gujarati", "kn-IN": "Kannada",
         "ml-IN": "Malayalam", "pa-IN": "Punjabi", "od-IN": "Odia"}

ROUTER_PROMPT = """You are Sahayak, an assistant helping Indian citizens turn a spoken problem into the right official document.
Input is what the user said (may be Hinglish/code-mixed or any Indian language) and optionally text read from a photo of a document.
Reply with ONLY a JSON object, no markdown, with these keys:
- "intent": one of "grievance" | "rti" | "insurance_claim" | "scheme" | "explain_document"
- "why": one short sentence in English on why this intent
- "facts": list of {"fact": short English statement, "evidence": the exact words from the input that support it}
- "document_title": title of the document you will draft (English)
- "draft": the full formal document in English (letter/application/RTI/claim/appeal) with To/Subject/Body/Date placeholders, citing the relevant law or scheme (e.g. RTI Act 2005 Section 6(1), Consumer Protection Act 2019, IRDAI Policyholders' Protection Regulations, PM-SYM, PMJJBY). Use [placeholders] for unknown details. Never invent names or numbers.
- "draft_native": a short version of the draft body (4-6 sentences) in {lang}
- "summary_native": a 3-sentence plain spoken summary in {lang} for the user: what we understood, what we drafted, what to do next. Simple words, no jargon.
- "next_steps": list of 3 short English steps
- "scam_check": {"risk": "low" | "medium" | "high", "reasons": list of up to 3 short English reasons}. Judge whether the document/message looks fraudulent or a phishing/fee scam (asks for OTP, advance fees, urgent threats, unofficial contact details, mismatched names). Genuine-looking official notices are "low"; say what the user should verify.
"""


def chat(system, user, max_tokens=6000):
    for attempt in range(3):
        r = requests.post(f"{BASE}/v1/chat/completions", headers=H, timeout=120, json={
            "model": "sarvam-105b",
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "max_tokens": max_tokens * (attempt + 1), "temperature": 0.3})
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        if content and content.strip():
            return content
    raise RuntimeError("model returned empty answer")


def extract_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))


def tts(text, lang, speaker="priya"):
    text = text[:480]
    r = requests.post(f"{BASE}/text-to-speech", headers=H, timeout=60, json={
        "text": text, "target_language_code": lang, "model": "bulbul:v3", "speaker": speaker})
    if r.status_code != 200:
        return None, r.text
    return r.json()["audios"][0], None


@app.get("/")
def index():
    return send_from_directory(HERE, "index.html")


@app.post("/api/transcribe")
def transcribe():
    f = request.files["audio"]
    r = requests.post(f"{BASE}/speech-to-text", headers=H, timeout=90,
                      files={"file": (f.filename or "a.webm", f.stream, f.mimetype or "audio/webm")},
                      data={"model": "saaras:v3", "mode": "codemix"})
    if r.status_code != 200:
        return jsonify(error=r.text), 500
    j = r.json()
    return jsonify(text=j.get("transcript", ""), lang=j.get("language_code"))


@app.post("/api/ocr")
def ocr():
    import io, time, zipfile
    f = request.files["photo"]
    mime = f.mimetype or "image/jpeg"
    r = requests.post(f"{BASE}/doc-ai/v1/job/digitise", headers=H, timeout=60,
                      files={"file": (f.filename or "doc.jpg", f.stream, mime)},
                      data={"language": request.form.get("lang", "en-IN"), "output_format": "md"})
    if r.status_code >= 300:
        return jsonify(error=r.text), 500
    job = r.json()["job_id"]
    status = ""
    for _ in range(40):
        time.sleep(1.5)
        s = requests.get(f"{BASE}/doc-ai/v1/job/{job}/status", headers=H, timeout=30).json()
        status = s.get("job_state") or s.get("status")
        if status in ("completed", "partially_completed", "failed", "rejected"):
            break
    if status not in ("completed", "partially_completed"):
        return jsonify(error=f"OCR job ended with status {status}"), 500
    u = requests.get(f"{BASE}/doc-ai/v1/job/{job}/download-url", headers=H, timeout=30).json()
    url = u.get("url") or u.get("download_url") or next(iter(u.get("download_urls", {}).values()), {}).get("file_url")
    z = zipfile.ZipFile(io.BytesIO(requests.get(url, timeout=60).content))
    name = next(n for n in z.namelist() if n.endswith(".md"))
    return jsonify(text=z.read(name).decode("utf-8"))


@app.post("/api/process")
def process():
    d = request.json
    text, lang = d.get("text", "").strip(), d.get("lang", "hi-IN")
    ocr = d.get("ocr", "").strip()
    lname = LANGS.get(lang, "Hindi")
    user = f"User said: {text}"
    if ocr:
        user += f"\n\nText from photo of their document:\n{ocr}"
    try:
        raw = chat(ROUTER_PROMPT.replace("{lang}", lname), user)
        data = extract_json(raw)
    except Exception as e:
        return jsonify(error=f"LLM step failed: {e}"), 500
    audio, err = tts(data.get("summary_native", ""), lang, d.get("speaker", "priya"))
    data["audio"] = audio
    data["tts_error"] = err
    return jsonify(data)


@app.post("/api/ask")
def ask():
    d = request.json
    lang = d.get("lang", "hi-IN")
    hist = "".join(f"User: {h['q']}\nSahayak: {h['a']}\n" for h in d.get("history", [])[-6:])
    sys_p = (f"You are Sahayak. The user got this document draft and summary:\n{d.get('context','')[:5000]}\n"
             + (f"Conversation so far:\n{hist}\n" if hist else "")
             + f"Answer their follow-up question in simple spoken {LANGS.get(lang,'Hindi')}, in at most 3 short sentences. "
             + "If unsure, say what to verify with the official office. No legal guarantees.")
    try:
        ans = chat(sys_p, d["question"], 3000).strip()
    except Exception as e:
        return jsonify(error=str(e)), 500
    audio, err = tts(ans, lang, "priya")
    return jsonify(answer=ans, audio=audio, error=err)


PERSONAS = {
    "dadi": ("a loving grandmother (Dadi). Warm, reassuring, uses one short folksy proverb or 'beta' naturally, never scary", "roopa"),
    "fauji": ("a retired army officer uncle. Crisp, disciplined, numbered action steps, calm confidence", "ratan"),
    "bachcha": ("a kind teacher talking to a 10-year-old. Very simple words, one fun comparison from daily life", "kavya"),
}


@app.post("/api/persona")
def persona():
    d = request.json
    lang = d.get("lang", "hi-IN")
    desc, speaker = PERSONAS.get(d.get("persona"), PERSONAS["dadi"])
    sys_p = (f"Explain the following official document situation as {desc}. "
             f"Speak in {LANGS.get(lang,'Hindi')}, 4 short sentences max, covering what happened and what to do next. "
             "Stay accurate; do not invent facts, names or numbers. Output only the spoken words.\n\n" + d.get("context", "")[:4000])
    try:
        text = chat(sys_p, "Please explain.", 3000).strip()
    except Exception as e:
        return jsonify(error=str(e)), 500
    audio, err = tts(text, lang, speaker)
    return jsonify(text=text, audio=audio, error=err)


@app.post("/api/voice/create")
def voice_create():
    f = request.files["audio"]
    r = requests.post(f"{BASE}/voices/create", headers=H, timeout=90,
                      files={"file": (f.filename or "ref.wav", f.stream, f.mimetype or "audio/wav")},
                      data={"name": "family-" + os.urandom(3).hex(), "language": request.form.get("lang", "hi-IN")})
    if r.status_code >= 300:
        return jsonify(error=r.text), 500
    j = r.json()
    vid = (j.get("data") or j).get("voice_id")
    return jsonify(voice_id=vid)


@app.post("/api/speak")
def speak():
    d = request.json
    if d.get("voice_id"):
        r = requests.post(f"{BASE}/voices/clone", headers=H, timeout=90,
                          files={"text": (None, d["text"][:950]), "language_code": (None, d.get("lang", "hi-IN")),
                                 "voice_id": (None, d["voice_id"])})
        if r.status_code >= 300:
            return jsonify(audio=None, error=r.text)
        j = r.json()
        return jsonify(audio=j.get("audio_b64") or j.get("audio"), error=None)
    audio, err = tts(d["text"], d.get("lang", "hi-IN"), d.get("speaker", "rahul"))
    return jsonify(audio=audio, error=err)


if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 5000)), debug=False)
