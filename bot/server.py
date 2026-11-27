"""WhatsApp webhook: Michal sends a reel link, the bot saves the recipe and replies with it."""
from __future__ import annotations

import logging
import os
from collections import deque

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse

import storage
import whatsapp
from extract import Recipe, extract_recipe
from reel import Reel, ReelError, fetch_reel, find_instagram_url

log = logging.getLogger("recipebot")
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Only these numbers may use the bot (comma-separated, international format, no +).
ALLOWED = {n.strip().lstrip("+") for n in os.environ.get("ALLOWED_NUMBERS", "").split(",") if n.strip()}
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")

# Meta retries webhooks; remember recent message ids so a recipe isn't processed twice.
_seen: deque[str] = deque(maxlen=500)

HELP = (
    "היי! 👩‍🍳 שלחי לי קישור לרילס מאינסטגרם עם מתכון, "
    "ואני אשמור אותו בספר המתכונים."
)


def recipe_link(recipe_id: str) -> str:
    return f"{SITE_URL}/#/recipe/{recipe_id}" if SITE_URL else ""


def format_recipe(recipe: Recipe, recipe_id: str) -> str:
    lines = [f"✅ נשמר: *{recipe.title}*"]
    meta = " · ".join(x for x in [recipe.servings and f"{recipe.servings} מנות", recipe.total_time] if x)
    if meta:
        lines.append(meta)
    lines.append("\n*מצרכים:*")
    lines += [f"• {i.amount} {i.item}".replace("•  ", "• ") for i in recipe.ingredients]
    lines.append("\n*אופן ההכנה:*")
    lines += [f"{n}. {s}" for n, s in enumerate(recipe.steps, 1)]
    link = recipe_link(recipe_id)
    if link:
        lines.append(f"\n📖 בספר המתכונים: {link}")
    return "\n".join(lines)


def handle_message(sender: str, text: str) -> None:
    url = find_instagram_url(text)
    if not url:
        if len(text) < 80:
            whatsapp.send_text(sender, HELP)
            return
        # A pasted recipe text (e.g. when the reel couldn't be opened).
        whatsapp.send_text(sender, "⏳ מסדרת את המתכון...")
        save_and_reply(sender, Reel(url=None, caption=text, author="", thumbnail=None, video_path=None))
        return

    existing = storage.find_by_url(url)
    if existing:
        whatsapp.send_text(sender, f"המתכון הזה כבר בספר: *{existing['title']}*\n{recipe_link(existing['id'])}".strip())
        return

    whatsapp.send_text(sender, "⏳ קיבלתי! מחלצת את המתכון, זה לוקח בערך דקה...")
    try:
        reel = fetch_reel(url)
    except ReelError as e:
        log.warning("reel fetch failed for %s: %s", url, e)
        whatsapp.send_text(
            sender,
            "😕 לא הצלחתי לפתוח את הרילס (אולי החשבון פרטי או שאינסטגרם חסם). "
            "אפשר להעתיק לי את טקסט המתכון ואני אשמור אותו.",
        )
        return

    save_and_reply(sender, reel)


def save_and_reply(sender: str, reel: Reel) -> None:
    recipe = extract_recipe(reel)
    if not recipe.is_recipe or not recipe.ingredients:
        whatsapp.send_text(sender, "🤔 לא מצאתי פה מתכון.")
        return

    row = storage.save_recipe(recipe, reel, added_by=sender)
    whatsapp.send_text(sender, format_recipe(recipe, row["id"]))


def safe_handle(sender: str, text: str) -> None:
    try:
        handle_message(sender, text)
    except Exception:
        log.exception("failed handling message from %s", sender)
        try:
            whatsapp.send_text(sender, "❌ משהו השתבש. נסי שוב עוד מעט.")
        except Exception:
            log.exception("could not send error message")


@app.get("/")
def health() -> dict:
    return {"ok": True}


@app.get("/webhook")
def verify(request: Request):
    """Meta calls this once when you register the webhook URL."""
    q = request.query_params
    if q.get("hub.mode") == "subscribe" and q.get("hub.verify_token") == os.environ.get("WHATSAPP_VERIFY_TOKEN"):
        return PlainTextResponse(q.get("hub.challenge", ""))
    raise HTTPException(403)


@app.post("/webhook")
async def incoming(request: Request, background: BackgroundTasks):
    body = await request.body()
    if not whatsapp.verify_signature(body, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(401)
    data = await request.json()
    for entry in data.get("entry", []):
        for change in entry.get("changes", []):
            for msg in change.get("value", {}).get("messages", []):
                if msg.get("id") in _seen:
                    continue
                _seen.append(msg.get("id"))
                sender = msg.get("from", "")
                if ALLOWED and sender not in ALLOWED:
                    log.info("ignoring message from unknown number %s", sender)
                    continue
                text = (msg.get("text") or {}).get("body", "")
                # Reply right away so Meta doesn't retry; do the slow work in the background.
                background.add_task(safe_handle, sender, text)
    return {"ok": True}
