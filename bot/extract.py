"""Turn a reel (caption + video) into a structured Hebrew recipe with Gemini."""
from __future__ import annotations

import logging
import os
import re
import time

from google import genai
from google.genai import types
from pydantic import BaseModel

from reel import Reel

log = logging.getLogger("recipebot")

# Google retires model names often. Unless GEMINI_MODEL is set, pick the newest
# plain "flash" model this API key can use, so the bot doesn't break when one is retired.
FALLBACK_MODEL = "gemini-3.8-flash"
_SKIP = ("lite", "preview", "exp", "tts", "image", "live", "audio", "thinking", "embedding", "8b")
_model_cache: str | None = None


def _version(name: str) -> tuple:
    m = re.search(r"gemini-(\d+(?:\.\d+)?)", name)
    return tuple(int(x) for x in m.group(1).split(".")) if m else (0,)


def pick_model(client: genai.Client) -> str:
    global _model_cache
    if os.environ.get("GEMINI_MODEL"):
        return os.environ["GEMINI_MODEL"]
    if _model_cache:
        return _model_cache
    try:
        names = []
        for m in client.models.list():
            name = (m.name or "").removeprefix("models/")
            actions = getattr(m, "supported_actions", None) or []
            if "flash" in name and not any(x in name for x in _SKIP) and (not actions or "generateContent" in actions):
                names.append(name)
        if names:
            _model_cache = max(names, key=lambda n: (_version(n), -len(n)))
    except Exception:
        log.exception("could not list Gemini models")
    _model_cache = _model_cache or FALLBACK_MODEL
    log.info("using Gemini model %s", _model_cache)
    return _model_cache


class Ingredient(BaseModel):
    item: str
    amount: str  # e.g. "2 כוסות", "לפי הטעם"


class Recipe(BaseModel):
    is_recipe: bool  # False when the reel has no recipe in it
    title: str
    description: str
    servings: str
    total_time: str
    ingredients: list[Ingredient]
    steps: list[str]
    tags: list[str]


PROMPT = """אתה עוזר שמחלץ מתכונים מסרטוני אינסטגרם.
קיבלת את הכיתוב של הפוסט ואת הסרטון עצמו (אם יש).
חלץ את המתכון המלא: שם, תיאור קצר, מספר מנות, זמן כולל, רשימת מצרכים עם כמויות, ושלבי הכנה מסודרים.
- כתוב הכל בעברית, גם אם המקור באנגלית או בשפה אחרת.
- השתמש גם במה שנאמר ומוצג בסרטון, לא רק בכיתוב.
- אם פרט לא ידוע, השאר מחרוזת ריקה. אל תמציא כמויות.
- tags: 2-5 תגיות קצרות (למשל: קינוח, טבעוני, ארוחת ערב, אפייה).
- אם אין בסרטון מתכון בכלל, החזר is_recipe=false.

כיתוב הפוסט:
---
{caption}
---
"""


def _client() -> genai.Client:
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def _upload_video(client: genai.Client, path) -> types.File:
    f = client.files.upload(file=str(path))
    while f.state and f.state.name == "PROCESSING":
        time.sleep(2)
        f = client.files.get(name=f.name)
    if f.state and f.state.name == "FAILED":
        raise RuntimeError("Gemini could not process the video")
    return f


def extract_recipe(reel: Reel) -> Recipe:
    client = _client()
    contents: list = []
    uploaded = None
    if reel.video_path:
        uploaded = _upload_video(client, reel.video_path)
        contents.append(uploaded)
    contents.append(PROMPT.format(caption=reel.caption or "(אין כיתוב)"))
    try:
        resp = client.models.generate_content(
            model=pick_model(client),
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Recipe,
                temperature=0.2,
            ),
        )
    finally:
        if uploaded:
            try:
                client.files.delete(name=uploaded.name)
            except Exception:
                pass
    return Recipe.model_validate_json(resp.text)
