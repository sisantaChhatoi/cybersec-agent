"""Link safety checker — GSB + VirusTotal + Tier-1 heuristics."""

import asyncio

from fastapi import APIRouter, Depends

from server.chatbot.link_safety import analyze_url, check_gsb, check_vt, unshorten
from server.deps import get_current_user

router = APIRouter(prefix="/link-check", tags=["link-check"])


@router.post("")
async def check_link(
    payload: dict,
    _: str = Depends(get_current_user),
) -> dict:
    url: str = payload.get("url", "").strip()
    if not url:
        return {"error": "url is required"}

    # Unshorten first so GSB/VT and heuristics see the real destination
    resolved = await unshorten(url)
    heuristics = analyze_url(resolved)

    gsb, vt = await asyncio.gather(
        check_gsb(resolved),
        check_vt(resolved),
        return_exceptions=True,
    )
    if isinstance(gsb, Exception):
        gsb = {"safe": True, "threat": None}
    if isinstance(vt, Exception):
        vt = {"safe": None, "malicious": 0, "suspicious": 0, "note": "unavailable"}

    # Layer reputation hits on top of heuristic score
    rep_score = 0
    if not gsb["safe"]:
        rep_score += 40
    if isinstance(vt.get("malicious"), int) and vt["malicious"] > 0:
        rep_score += 40
    elif isinstance(vt.get("suspicious"), int) and vt["suspicious"] > 0:
        rep_score += 20

    combined_score = min(heuristics["score"] + rep_score, 100)
    risk_level = "high" if combined_score >= 60 else "suspicious" if combined_score >= 25 else "low"
    verdict = "unsafe" if risk_level == "high" else "suspicious" if risk_level == "suspicious" else "safe"

    return {
        "url": url,
        "resolved_url": resolved if resolved != url else None,
        "verdict": verdict,
        "risk_score": combined_score,
        "risk_level": risk_level,
        "flags": heuristics["flags"],
        "google_safe_browsing": gsb,
        "virustotal": vt,
    }
