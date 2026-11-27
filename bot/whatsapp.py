"""Send WhatsApp messages and check webhook signatures (Meta WhatsApp Cloud API)."""
from __future__ import annotations

import hashlib
import hmac
import os

import httpx

GRAPH_VERSION = os.environ.get("GRAPH_API_VERSION", "v21.0")


def verify_signature(body: bytes, header: str | None) -> bool:
    """Meta signs every webhook call with the app secret. Reject anything unsigned."""
    secret = os.environ.get("WHATSAPP_APP_SECRET", "")
    if not secret or not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header.removeprefix("sha256="))


def send_text(to: str, text: str) -> None:
    phone_id = os.environ["WHATSAPP_PHONE_NUMBER_ID"]
    r = httpx.post(
        f"https://graph.facebook.com/{GRAPH_VERSION}/{phone_id}/messages",
        headers={"Authorization": f"Bearer {os.environ['WHATSAPP_TOKEN']}"},
        json={
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text[:4096], "preview_url": True},
        },
        timeout=20,
    )
    r.raise_for_status()
