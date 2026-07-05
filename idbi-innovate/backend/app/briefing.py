"""
OPTIONAL underwriter-briefing narration.

IMPORTANT: the LLM is used ONLY to rephrase the already-computed, deterministic
Health Card into a readable paragraph. It NEVER makes or alters the credit decision
— the score, RAG, reasons and limit are all fixed before this is called. If
GEMINI_API_KEY is not set, we return the deterministic rule-based summary verbatim,
so the product is fully functional with zero LLM dependency.

Uses only stdlib (urllib) to call the Gemini API, so no extra backend deps.
"""
import json
import os
import urllib.request

_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"


def _prompt(card):
    ex = card["explanation"]
    facts = {
        "segment": card["segment"], "new_to_credit": card["is_ntc"],
        "rag": card["rag"], "score": card["unified_score"],
        "recommendation": card["recommendation"], "suggested_limit": card["suggested_limit"],
        "estimated_monthly_revenue": card["estimated_monthly_revenue"],
        "data_confidence": card["data_confidence"],
        "strengths": [s["text"] for s in ex["strengths"]],
        "concerns": [c["text"] for c in ex["concerns"]],
        "data_quality_flags": ex["data_quality"],
    }
    return (
        "You are assisting a bank underwriter. Using ONLY the facts below, write a "
        "concise 3-4 sentence briefing in plain professional English. Do NOT invent "
        "numbers, do NOT change the recommendation, and end by reminding that the final "
        "decision rests with the underwriter.\n\nFACTS:\n" + json.dumps(facts, indent=2)
    )


def generate(card):
    """Return {'briefing': str, 'source': 'gemini'|'deterministic'}."""
    deterministic = card["explanation"]["summary"]
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return {"briefing": deterministic, "source": "deterministic",
                "note": "Set GEMINI_API_KEY to enable LLM narration (rephrasing only; "
                        "decision remains deterministic)."}
    try:
        body = json.dumps({"contents": [{"parts": [{"text": _prompt(card)}]}]}).encode()
        url = _ENDPOINT.format(model=_MODEL, key=key)
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        return {"briefing": text, "source": "gemini"}
    except Exception as e:
        # never let LLM issues break the flow — fall back to deterministic
        return {"briefing": deterministic, "source": "deterministic", "error": str(e)}
