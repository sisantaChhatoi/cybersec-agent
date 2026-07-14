from typing import Literal

from langchain_core.tools import BaseTool, tool

from server.chatbot.link_safety import assess_url
from server.chatbot.retrieval import retrieve
from server.models.incident import Incident
from server.repositories.incident_repo import IncidentRepository

_REPORT_FIELDS = [
    "caller_number",
    "mule_account",
    "mule_upi",
    "victim_region",
    "scam_type",
]


_VERDICT_PHRASE = {
    "unsafe": "unsafe — this link is a scam/malicious site",
    "suspicious": "suspicious — this link shows warning signs of a scam site",
    "safe": "safe — no threats found for this link",
}


@tool
async def check_link_safety(url: str) -> str:
    """Check whether a URL shared by the user is safe or malicious.
    Call this whenever the user pastes or mentions any link/URL.
    Returns a safe/suspicious/unsafe verdict and why, if flagged."""
    result = await assess_url(url)
    if not result["checked"]:
        return "Could not check the link right now; try again shortly."

    # Bare prose only. The chat model parrots any structure it is handed — labels,
    # scores, vendor names — straight into its reply. Structure belongs in the API.
    phrase = _VERDICT_PHRASE[result["verdict"]]
    if result["verdict"] == "safe" or not result["reasons"]:
        return phrase
    return f"{phrase}; {', '.join(result['reasons'])}"


@tool
def search_fraud_knowledge(query: str) -> str:
    """Look up fraud-advisory guidance relevant to the user's situation: scam
    patterns, red flags, what to do, and how/where to report. Call this before
    giving safety advice so the reply is grounded in real guidance, not guessed."""
    hits = retrieve(query)
    return "\n\n".join(hits) if hits else "(no relevant guidance found)"


def build_chat_tools(
    incidents: IncidentRepository, *, session_id: str, user_id: str | None
) -> list[BaseTool]:
    @tool
    async def save_incident(
        scam_type: Literal[
            "digital_arrest",
            "courier_parcel",
            "kyc",
            "upi",
            "job",
            "investment",
            "lottery",
            "other",
        ]
        | None = None,
        caller_number: str | None = None,
        mule_account: str | None = None,
        mule_upi: str | None = None,
        victim_region: str | None = None,
        claimed_authority: str | None = None,
        amount_demanded: float | None = None,
        amount_lost: float | None = None,
        payment_method: str | None = None,
        remote_app_requested: str | None = None,
    ) -> str:
        """Record scam details the user has given. Call this as soon as the user
        reveals any field, and again as more details come out. Pass only fields
        actually stated; leave the rest null. Never put the same value in two of
        caller_number / mule_account / mule_upi.

        - caller_number: phone number the scammer called from
        - mule_account: bank account the user was told to pay (the number, or the bank name if that's all)
        - mule_upi: UPI handle the user was told to pay
        - victim_region: the user's city / area
        - claimed_authority: who the caller claimed to be (CBI, bank, police, courier...)
        - amount_demanded / amount_lost: rupee amounts
        - payment_method, remote_app_requested: e.g. UPI / "AnyDesk"
        """
        incident = await incidents.get(session_id) or Incident(
            session_id=session_id, user_id=user_id
        )
        incident.merge_extracted(
            {
                "scam_type": scam_type,
                "caller_number": caller_number,
                "mule_account": mule_account,
                "mule_upi": mule_upi,
                "victim_region": victim_region,
                "claimed_authority": claimed_authority,
                "amount_demanded": amount_demanded,
                "amount_lost": amount_lost,
                "payment_method": payment_method,
                "remote_app_requested": remote_app_requested,
            }
        )
        await incidents.upsert(incident)
        missing = [f for f in _REPORT_FIELDS if getattr(incident, f) is None]
        return f"saved; still missing: {', '.join(missing) or 'nothing key'}"

    @tool
    async def update_incident(
        scam_type: Literal[
            "digital_arrest",
            "courier_parcel",
            "kyc",
            "upi",
            "job",
            "investment",
            "lottery",
            "other",
        ]
        | None = None,
        caller_number: str | None = None,
        mule_account: str | None = None,
        mule_upi: str | None = None,
        victim_region: str | None = None,
        claimed_authority: str | None = None,
        amount_demanded: float | None = None,
        amount_lost: float | None = None,
        payment_method: str | None = None,
        remote_app_requested: str | None = None,
    ) -> str:
        """Correct a detail already recorded, when the user explicitly changes
        it ("the account was actually X, not Y"). Use ONLY for such corrections,
        not for adding new details — use save_incident for new details. Pass
        only the field(s) being corrected."""
        incident = await incidents.get(session_id)
        if incident is None:
            return "nothing recorded yet; use save_incident"
        incident.overwrite(
            {
                "scam_type": scam_type,
                "caller_number": caller_number,
                "mule_account": mule_account,
                "mule_upi": mule_upi,
                "victim_region": victim_region,
                "claimed_authority": claimed_authority,
                "amount_demanded": amount_demanded,
                "amount_lost": amount_lost,
                "payment_method": payment_method,
                "remote_app_requested": remote_app_requested,
            }
        )
        await incidents.upsert(incident)
        return "updated"

    @tool
    async def lookup_fraud_network(value: str) -> str:
        """Check whether a phone number, bank account, or UPI id has shown up in
        OTHER reported scams. Call this when the user names a specific number /
        account / UPI, so you can warn them if it's already known. Returns how
        many prior reports mention it and what it's linked to."""
        try:
            info = await incidents.lookup_entity(value, exclude_session=session_id)
        except Exception:
            return (
                f"Lookup unavailable for {value}. Do NOT mention this check to the user; "
                "just continue with your normal advice."
            )
        if info["report_count"] == 0:
            return (
                f"No prior report matches {value}. Our data is sparse, so this is NOT evidence "
                "of safety — do NOT tell the user it looks safe and do NOT mention this check; "
                "continue with your normal advice. Only cite this tool when it finds real reports."
            )
        return (
            f"{value}: appears in {info['report_count']} other report(s); "
            f"seen as {info['seen_as']}; scam types {info['scam_types']}; "
            f"linked to {info['linked_entities']}"
        )

    return [
        check_link_safety,
        search_fraud_knowledge,
        save_incident,
        update_incident,
        lookup_fraud_network,
    ]
