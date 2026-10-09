"""Shared data shapes for the risk engine and the API."""

from typing import Literal

from pydantic import BaseModel, Field

RiskLevel = Literal["low", "medium", "high"]
SignalType = Literal[
    "urgency", "secrecy", "transfer_ask", "impersonation", "isolation", "out_of_character"
]


class Turn(BaseModel):
    t: float
    speaker: Literal["caller", "user"]
    text: str


class Contact(BaseModel):
    """What the engine may know about every trusted contact: no profile details."""

    id: str
    name: str
    relation: str


class Profile(BaseModel):
    """One contact's memory, sent only once they are the claimed caller. Never the code word."""

    id: str
    name: str
    relation: str
    addresses_user_as: str
    usual_topics: list[str] = []
    never: list[str] = []
    past_requests: list[str] = []
    # Whether the browser holds a code word for this contact. The word itself never leaves it.
    has_code_word: bool = False
    # Used only to send this contact the "Is this you?" check.
    email: str = ""


class AssessRequest(BaseModel):
    turns: list[Turn]
    contacts: list[Contact] = []
    profile: Profile | None = None
    household_rules: list[str] = []


class Signal(BaseModel):
    type: SignalType
    quote: str = Field(description="The caller's words that triggered it")


class RiskResult(BaseModel):
    score: RiskLevel
    signals: list[Signal] = []
    rationale: str
    claimed_contact: str | None = Field(None, description="Contact id, family only")
    claimed_org: str | None = None
    # Set by the brain chain, not the model: which brain answered, and whether it was a backup.
    checked_by: str = ""
    backup: bool = False


ActionKind = Literal[
    "watch", "code_word_challenge", "is_this_you_check", "hang_up_helpline", "alert_guardian"
]


class Action(BaseModel):
    kind: ActionKind
    message: str = Field(description="One plain instruction shown to the user")
    target: str | None = Field(None, description="Contact id the action involves, if any")
    helpline: dict[str, str] | None = None
