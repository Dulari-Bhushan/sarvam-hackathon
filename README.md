# Dadi Desk (दादी डेस्क)

**One voice agent for Indian citizens. Speak your problem in your language, or photograph the letter. Dadi Desk works out what you need, drafts the right official document, checks it isn't a scam, and explains it aloud, even in a family member's voice.**

Built in a 20-minute Sarvam AI hackathon.

---

## ⭐ What is new here (not in the hackathon idea sheet)

The sheet lists 49 separate products. Dadi Desk is **one agent that decides which of them you need**, plus five things the sheet does not describe:

| New | What it does | Why it matters |
|---|---|---|
| **1. Intent Router** | A single LLM call reads your speech and photo, then picks the right path: grievance, RTI, insurance appeal, scheme application, or plain explanation. | The sheet treats these as 6+ different products (#28, #40, #45, #46, #47…). Real citizens don't know which form they need. They only know the problem. |
| **2. Scam Shield** | Every document or message gets a low / medium / high fraud badge with reasons (OTP requests, advance fees, urgent threats). | Fake KYC and "pay a fee to release your claim" messages are common in India. The tool checks the notice before it helps you act on it. |
| **3. Evidence Trail** | Each fact in the draft is shown next to the exact words you said or the exact line in your photo it came from. | The user can verify the AI's draft instead of trusting it blindly. The AI never invents names or numbers. It uses `[placeholders]`. |
| **4. Family Forward (cloned voice)** | The summary becomes a voice message in a relative's cloned voice (with consent) to send to someone who can't read. | It solves the last-mile problem. The person who needs the information is often not the person at the phone. |
| **5. Persona Mode (fun)** | One click re-explains the result as **Dadi** (warm, proverb-filled), **Fauji Uncle** (crisp numbered steps) or **Chhota Bachcha** (explained to a 10-year-old), each in its own voice. | The same facts, delivered in the tone the listener trusts. Elders, kids and busy people all take information differently. |
| **6. Voice follow-ups** | After the draft, ask "how many days until I get a reply?" by voice and hear the answer in your language. | It makes the output a conversation, not a one-shot document. |

*Closest sheet items, for transparency: #10 Elder Companion (scam warnings), #19 Voice Time Capsule (voice cloning), #39 Sunniye Samjhiye (evidence linked to audio). Dadi Desk differs by joining them into one routed pipeline.*

---

## The problem

Hundreds of millions of people in India are entitled to schemes, claims, refunds and legal remedies but can't use them. The paperwork is in English or formal Hindi, and notices are written in legal language. Someone whose insurance claim was rejected can describe the problem easily in their own language. Turning it into the right appeal, with the right law cited, is the hard part.

## Pipeline

```
 voice ──► Saaras v3 (speech to text, code-mix) ──┐
                                                  ├─► Sarvam-105B ROUTER + EXTRACTOR
 photo ──► Sarvam Vision (OCR) ───────────────────┘      intent · facts · evidence · scam_check
                                                         │
                                                         ▼
                                           Sarvam-105B DRAFTER
                                           document · spoken summary · next steps
                                                         │
                                  ┌──────────────────────┼───────────────────────┐
                                  ▼                      ▼                       ▼
                       Bulbul v3 (TTS)         Voice cloning (consent)     Voice follow-up Q&A
                       spoken summary          Family Forward              (Saaras → LLM → Bulbul)
```

### Sarvam APIs used

| API | Used for |
|---|---|
| Saaras v3 | Speech to text, including Hinglish (code-mix mode) |
| Sarvam Vision (Document Intelligence) | Reading photos of letters, bills and notices |
| Sarvam-105B | Routing, fact extraction, drafting, scam check, personas, follow-up answers |
| Bulbul v3 | Spoken summaries and answers in 10+ Indian languages |
| Instant Voice Cloning (beta) | Family Forward in a relative's voice |

## Demo scenarios

Sample documents are in `demo_images/`. Upload one, then speak (or type) the matching line.

| Image | Say |
|---|---|
| `1_insurance_claim_rejection.png` | "Mera claim reject ho gaya, maine to saare bill jama kiye the." |
| `2_bank_loan_notice.png` | "Bank ne notice bheja hai, meri fasal kharab hui thi, ab penalty kyun?" |
| `3_electricity_bill_wrong.png` | "Mera bijli ka bill bahut zyada aaya hai, hum to kam use karte hain." |
| `4_hospital_discharge_summary.png` | "Maa ko hospital se chhutti mili hai, ye papers samajh nahi aa rahe." |
| `5_scheme_application_rejected.png` | "Mera pension scheme ka form reject ho gaya, ab kya karun?" |

| `6_FAKE_claim_approved_scam.png` | "Mujhe ye message aaya hai, mera claim approve ho gaya, kya ye sach hai?" (Scam Shield: HIGH risk) |

**Scam Shield demo (type this):** "Mujhe SMS aaya ki mera KYC expire ho gaya, abhi 500 rupay fees bhejo aur OTP batao warna account band." The result shows a **red HIGH risk** badge.

## Run it

Requires Python 3.10+ and a Chrome browser (for the microphone).

```bash
pip install -r requirements.txt
echo SARVAM_API_KEY=your_key_here > .env
python app.py
```

Open http://localhost:5000.

## Deploy (Render)

1. Push this repo to GitHub, then on https://render.com choose **New > Blueprint** and pick the repo (`render.yaml` is included).
2. Set the `SARVAM_API_KEY` environment variable.
3. Open the generated URL. The microphone needs HTTPS, which Render provides.

## Files

- `app.py`: Flask backend with `/api/transcribe`, `/api/ocr`, `/api/process`, `/api/ask`, `/api/voice/create` and `/api/speak`
- `index.html`: the single-page UI
- `demo_images/`: sample letters for the demo

## Limitations and responsible use

- Drafts are for guidance only and are not legal advice. Cited laws are well-known ones, and unknown details stay as `[placeholders]`.
- Scam Shield is an LLM judgement, not a guarantee. It tells users what to verify.
- Voice cloning is Sarvam's beta feature. It needs a clean 10-second clip and the speaker's consent (the UI asks for it). If cloning fails, Family Forward falls back to a standard Bulbul voice.
- Photos must be PNG or JPEG.
- The API key lives only in `.env`, which is git-ignored.

## Ideas for next

- Offline or missed-call entry for people without smartphones
- Auto-filling government forms, not just drafting letters
- Tracking the filed grievance and reminding the user by voice when a reply is due
