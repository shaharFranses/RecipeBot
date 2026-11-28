"""Turn a reel (caption + video) into a structured Hebrew recipe with Gemini."""
from __future__ import annotations

import os
import time

from google import genai
from google.genai import types
from pydantic import BaseModel

from reel import Reel

# "gemini-flash-latest" always points at Google's current Flash model, so it doesn't go stale.
MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")


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
            model=MODEL,
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
