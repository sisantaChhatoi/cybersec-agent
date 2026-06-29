import re
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

# A bare bank name ("SBI") has no long digit run; a real account number does.
_ACCOUNT_NUMBER_PATTERN = re.compile(r"\d{6,}")

# A phone number, a bank account, and a UPI handle are distinct identifier
# types -- they must never hold the same value. Extraction returning one value
# for two of them is a misattribution (the model conflated two questions), not
# a coincidence to record twice.
_DISTINCT_IDENTITY_FIELDS = ("caller_number", "mule_account", "mule_upi")


class ScamType(str, Enum):
    DIGITAL_ARREST = "digital_arrest"
    COURIER_PARCEL = "courier_parcel"
    KYC = "kyc"
    UPI = "upi"
    JOB = "job"
    INVESTMENT = "investment"
    LOTTERY = "lottery"
    OTHER = "other"


class IncidentStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    REPORTED = "reported"
    COMPLETED = "completed"


EXTRACTABLE_FIELDS = [
    "caller_number",
    "mule_account",
    "mule_upi",
    "victim_region",
    "scam_type",
    "claimed_authority",
    "amount_demanded",
    "amount_lost",
    "payment_method",
    "remote_app_requested",
]


class Incident(BaseModel):
    incident_id: UUID = Field(default_factory=uuid4)
    session_id: str
    user_id: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    scam_type: ScamType | None = None
    claimed_authority: str | None = None
    caller_number: str | None = None
    mule_account: str | None = None
    mule_account_bank_name: str | None = None
    mule_upi: str | None = None
    amount_demanded: float | None = None
    amount_lost: float | None = None
    victim_region: str | None = None
    payment_method: str | None = None
    remote_app_requested: str | None = None
    status: IncidentStatus = IncidentStatus.IN_PROGRESS

    def merge_extracted(self, updates: dict) -> None:
        """Fill fields from an extraction/tool result. Each field is filled
        once then locked, so a later pass can't overwrite a correct value with
        a hallucinated one. scam_type is the exception -- it can be refined as
        the conversation reveals more."""
        for field in EXTRACTABLE_FIELDS:
            value = updates.get(field)
            if not _is_real_value(value):
                continue
            if field == "scam_type":
                try:
                    self.scam_type = ScamType(value)
                except ValueError:
                    continue
            elif field == "mule_account":
                if not self._resolve_identity_conflict("mule_account", str(value)):
                    self._merge_mule_account(str(value))
            elif field in _DISTINCT_IDENTITY_FIELDS:
                if getattr(self, field) is None and not self._resolve_identity_conflict(
                    field, str(value)
                ):
                    setattr(self, field, value)
            elif getattr(self, field) is None:
                setattr(self, field, value)

    def _resolve_identity_conflict(self, field: str, value: str) -> bool:
        """If `value` is already held by another identity field, it's a
        misattribution. mule_account/mule_upi (what the fraud graph links rings
        through) win over caller_number -- the bug pattern is "asked for the
        number AND the account in one breath," and the user's answer is far
        more often the account they were explicitly asked to name. Returns True
        if `field` should be left unset."""
        value = value.strip()
        priority = {"mule_account": 0, "mule_upi": 0, "caller_number": 1}
        for other in _DISTINCT_IDENTITY_FIELDS:
            if other == field:
                continue
            existing = getattr(self, other)
            if existing is None or str(existing).strip() != value:
                continue
            if priority[other] < priority[field]:
                return True
            setattr(self, other, None)
        return False

    def _merge_mule_account(self, value: str) -> None:
        if _ACCOUNT_NUMBER_PATTERN.search(value):
            self.mule_account = value
        elif self.mule_account is None:
            # Just a bank name so far; keep it aside and let the agent ask for
            # the actual number.
            self.mule_account_bank_name = value


_NULL_PLACEHOLDER_PHRASES = (
    "not explicitly stated",
    "not stated",
    "not mentioned",
    "not provided",
    "not specified",
    "unknown",
    "n/a",
    "none",
    "null",
)


def _is_real_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        stripped = value.strip().lower()
        return bool(stripped) and stripped not in _NULL_PLACEHOLDER_PHRASES
    return True
