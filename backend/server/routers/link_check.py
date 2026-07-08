"""Link safety checker — Google Safe Browsing + VirusTotal."""

import httpx
from fastapi import APIRouter, Depends

from server.deps import get_current_user
from shared.config import settings

router = APIRouter(prefix="/link-check", tags=["link-check"])

_GSB_URL = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
_VT_URL = "https://www.virustotal.com/api/v3/urls"


async def _check_gsb(url: str) -> dict:
    body = {
        "client": {"clientId": "digital-arrest-shield", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": [
                "MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE",
                "POTENTIALLY_HARMFUL_APPLICATION",
            ],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            _GSB_URL, params={"key": settings.google_safe_browsing_key}, json=body
        )
        r.raise_for_status()
        data = r.json()
        matches = data.get("matches", [])
        if matches:
            threat = matches[0].get("threatType", "UNKNOWN")
            return {"safe": False, "threat": threat}
        return {"safe": True, "threat": None}


async def _check_vt(url: str) -> dict:
    import base64
    url_id = base64.urlsafe_b64encode(url.encode()).rstrip(b"=").decode()
    headers = {"x-apikey": settings.virustotal_key}
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{_VT_URL}/{url_id}", headers=headers)
        if r.status_code == 404:
            # URL not in VT database yet — submit it
            submit = await client.post(
                _VT_URL, headers=headers, data={"url": url}
            )
            submit.raise_for_status()
            return {"safe": None, "malicious": 0, "suspicious": 0, "note": "queued"}
        r.raise_for_status()
        stats = r.json()["data"]["attributes"]["last_analysis_stats"]
        malicious = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)
        return {
            "safe": malicious == 0 and suspicious == 0,
            "malicious": malicious,
            "suspicious": suspicious,
            "note": None,
        }


@router.post("")
async def check_link(
    payload: dict,
    _: str = Depends(get_current_user),
) -> dict:
    url: str = payload.get("url", "").strip()
    if not url:
        return {"error": "url is required"}

    gsb, vt = await _check_gsb(url), await _check_vt(url)

    overall_safe = gsb["safe"] and (vt["safe"] is not False)
    verdict = "safe" if overall_safe else "unsafe"

    return {
        "url": url,
        "verdict": verdict,
        "google_safe_browsing": gsb,
        "virustotal": vt,
    }
