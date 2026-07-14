"""Link safety checker — GSB + VirusTotal + Tier-1 heuristics + Tier-2 domain age + Tier-4 page/ML."""

import asyncio

from fastapi import APIRouter, Depends

from server.chatbot.link_safety import (
    analyze_url,
    check_domain_age,
    check_gsb,
    check_ml_classifier,
    check_page_content,
    check_vt,
    domain_changed,
    unshorten,
)
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

    resolved = await unshorten(url)
    heuristics = analyze_url(resolved)
    ml = check_ml_classifier(resolved)

    gsb_r, vt_r, age_r, page_r = await asyncio.gather(
        check_gsb(resolved),
        check_vt(resolved),
        check_domain_age(resolved),
        check_page_content(resolved),
        return_exceptions=True,
    )
    gsb: dict = gsb_r if isinstance(gsb_r, dict) else {"safe": True, "threat": None}
    vt: dict = (
        vt_r
        if isinstance(vt_r, dict)
        else {"safe": None, "malicious": 0, "suspicious": 0, "note": "unavailable"}
    )
    domain_age: dict = (
        age_r
        if isinstance(age_r, dict)
        else {"age_days": None, "created": None, "domain": ""}
    )
    page: dict = (
        page_r
        if isinstance(page_r, dict)
        else {"available": False, "flags": [], "score": 0}
    )

    score = heuristics["score"]

    if not gsb["safe"]:
        score += 40
    if isinstance(vt.get("malicious"), int) and vt["malicious"] > 0:
        score += 40
    elif isinstance(vt.get("suspicious"), int) and vt["suspicious"] > 0:
        score += 20

    age_days = domain_age.get("age_days")
    if age_days is not None:
        if age_days < 30:
            score += 25
        elif age_days < 90:
            score += 10

    score += page.get("score", 0)

    if ml.get("available") and ml.get("label") in ("phishing", "malware"):
        confidence = ml.get("confidence") or 0
        if confidence >= 0.80:
            score += int(confidence * 30)

    combined_score = min(score, 100)
    risk_level = (
        "high"
        if combined_score >= 60
        else "suspicious"
        if combined_score >= 20
        else "low"
    )
    verdict = (
        "unsafe"
        if risk_level == "high"
        else "suspicious"
        if risk_level == "suspicious"
        else "safe"
    )

    return {
        "url": url,
        "resolved_url": resolved if domain_changed(url, resolved) else None,
        "verdict": verdict,
        "risk_score": combined_score,
        "risk_level": risk_level,
        "flags": heuristics["flags"],
        "domain_age": domain_age,
        "ml_classifier": ml,
        "page_analysis": page,
        "google_safe_browsing": gsb,
        "virustotal": vt,
    }
