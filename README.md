# Sahayak (सहायक)

**Speak your problem in any Indian language, or photograph the letter. Get the right official document back, explained aloud.**

Built for a 20-minute Sarvam AI hackathon.

## The problem

Hundreds of millions of people in India are entitled to schemes, claims, refunds and legal remedies but can't use them. The paperwork is in English or formal Hindi, and notices are written in legal language. Someone whose insurance claim was rejected can describe the problem easily in their own language. Turning it into the right appeal, with the right law cited, is the hard part.

## What it does

1. **Listens:** the user speaks in Hindi, Hinglish or another Indian language (Saaras v3, code-mix mode).
2. **Reads:** the user can also upload a photo of a notice, bill or rejection letter (Sarvam Vision).
3. **Routes:** one LLM call decides what is needed: a grievance, an RTI application, an insurance claim appeal, a scheme application, or a plain-language explanation of a document (Sarvam-105B).
4. **Drafts:** it writes the formal document with the relevant law or scheme cited and `[placeholders]` for details it doesn't know. It never invents names or numbers.
5. **Shows its evidence:** every fact is displayed next to the exact words or photo text it came from, so the user can check the draft.
6. **Speaks:** a short summary and next steps are read aloud in the user's language (Bulbul v3).
7. **Family Forward:** one click makes a voice message of the summary to send to a relative who can't read.

## Pipeline

```
 voice ──► Saaras v3 (speech to text) ──┐
                                        ├─► Sarvam-105B router + extractor (JSON: intent, facts, evidence)
 photo ──► Sarvam Vision (OCR) ─────────┘                │
                                                         ▼
                                           Sarvam-105B drafter (document, summary, next steps)
                                                         │
                                                         ▼
                                       Bulbul v3 (text to speech) ──► spoken summary / Family Forward
```

## Run it

Requires Python 3.10+.

```bash
pip install flask requests
echo SARVAM_API_KEY=your_key_here > .env
python app.py
```

Open http://localhost:5000. Use Chrome so the microphone works.

## Files

- `app.py`: Flask backend, with `/api/transcribe`, `/api/ocr`, `/api/process` and `/api/speak`
- `index.html`: the single-page UI

## Limitations

- Family Forward uses a different Bulbul speaker. True voice cloning (Sarvam's beta feature) is not wired in yet.
- Photos must be PNG or JPEG.
- Drafts are for guidance only and are not legal advice.
- The API key lives only in `.env`, which is git-ignored.

## Ideas for next

- Real voice cloning for Family Forward
- Offline or missed-call entry for people without smartphones
- Auto-filling government forms, not just drafting letters
