"""Notifications to family: the trusted-contact alert and the "Is this you?" check.

One small interface so more channels (SMS, WhatsApp, push) can be added later without touching the
call session. Email first, over any SMTP (Gmail app password by default), ported from Resolve's
mailer.ts, including its demo rule: @example.com addresses have no inbox, so their mail goes to
EMAIL_DEMO_REDIRECT_TO when it is set.
"""

import asyncio
import logging
import smtplib
from email.message import EmailMessage
from typing import Protocol

from app.config import settings

log = logging.getLogger("ringproof.notify")


class NotSent(Exception):
    """The message could not be sent; the reason is shown on screen as-is."""


class Notifier(Protocol):
    name: str

    async def send(self, to: str, subject: str, body: str) -> None:
        """Deliver or raise NotSent with a short, user-facing reason."""
        ...


def delivery_address(email: str) -> str:
    redirect = settings.email_demo_redirect_to
    return redirect if redirect and email.lower().endswith("@example.com") else email


def is_allowed(address: str) -> bool:
    """Only the demo redirect and EMAIL_ALLOWED_TO may receive email. Addresses come from the
    browser, so without this a public server would email anyone from this account. (With user
    accounts, contacts who confirmed their address would replace this list: VISION §6.)"""
    allowed = {a.strip().lower() for a in settings.email_allowed_to.split(",") if a.strip()}
    if settings.email_demo_redirect_to:
        allowed.add(settings.email_demo_redirect_to.strip().lower())
    return address.strip().lower() in allowed


class EmailNotifier:
    name = "email"

    async def send(self, to: str, subject: str, body: str) -> None:
        if not to:
            raise NotSent("no email address saved")
        msg = EmailMessage()
        try:
            msg["From"] = f"Ringproof <{settings.smtp_user}>"
            msg["To"] = delivery_address(to)
            msg["Subject"] = subject
        except ValueError as err:  # e.g. a line break in the address or subject
            raise NotSent("the email address is not valid") from err
        if not is_allowed(msg["To"]):
            raise NotSent("this address is not on Ringproof's approved list")
        msg.set_content(body)
        try:
            await asyncio.to_thread(self._send, msg)
        except (smtplib.SMTPException, OSError) as err:
            log.warning("email to %s failed: %s", msg["To"], err)
            raise NotSent("the email server refused it") from err

    @staticmethod
    def _send(msg: EmailMessage) -> None:
        port = settings.smtp_port
        smtp = smtplib.SMTP_SSL if port == 465 else smtplib.SMTP
        with smtp(settings.smtp_host, port, timeout=20) as server:
            if port != 465:
                server.starttls()
            server.login(settings.smtp_user, settings.smtp_pass)
            server.send_message(msg)


class NoNotifier:
    name = "off"

    async def send(self, to: str, subject: str, body: str) -> None:
        raise NotSent("email is not set up")


def get_notifier() -> Notifier:
    return EmailNotifier() if settings.smtp_user and settings.smtp_pass else NoNotifier()


# --- Messages ---------------------------------------------------------------------------------
# Plain words, no transcript: the alert says who the caller claimed to be and why it looks wrong.


def alert_message(user: str, claim: str, why: str) -> tuple[str, str]:
    subject = f"Ringproof: possible scam call to {user}"
    body = (
        f"Ringproof thinks {user} is on a scam call right now.\n\n"
        f"The caller says they are: {claim}\n"
        f"Why it looks wrong: {why}\n\n"
        f"Ringproof is showing {user} a warning not to send money or share any OTP. "
        f"Please call {user} on their usual number.\n\n"
        "If you are worried, the National Cyber Crime Helpline is 1930 (cybercrime.gov.in)."
    )
    return subject, body


def is_this_you_message(user: str, name: str, link: str) -> tuple[str, str]:
    subject = f"Ringproof: are you calling {user} right now?"
    body = (
        f"Hi {name},\n\n"
        f"Someone is on the phone with {user} right now saying they are you.\n"
        f"Please tell Ringproof if it is really you:\n\n{link}\n\n"
        f"If it is not you, please call {user} on their usual number."
    )
    return subject, body
