"""Save and look up recipes in Supabase through its REST API."""
from __future__ import annotations

import os

import httpx

from extract import Recipe
from reel import Reel


def _base() -> str:
    return os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1/recipes"


def _headers() -> dict[str, str]:
    key = os.environ["SUPABASE_SERVICE_KEY"]
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def find_by_url(url: str) -> dict | None:
    r = httpx.get(_base(), headers=_headers(), params={"source_url": f"eq.{url}", "select": "id,title"}, timeout=20)
    r.raise_for_status()
    rows = r.json()
    return rows[0] if rows else None


def save_recipe(recipe: Recipe, reel: Reel, added_by: str = "") -> dict:
    row = {
        "source_url": reel.url,
        "author": reel.author,
        "thumbnail": reel.thumbnail,
        "title": recipe.title or "מתכון ללא שם",
        "description": recipe.description,
        "servings": recipe.servings,
        "total_time": recipe.total_time,
        "ingredients": [i.model_dump() for i in recipe.ingredients],
        "steps": recipe.steps,
        "tags": recipe.tags,
        "raw_caption": reel.caption,
        "added_by": added_by,
    }
    r = httpx.post(_base(), headers={**_headers(), "Prefer": "return=representation"}, json=row, timeout=20)
    r.raise_for_status()
    return r.json()[0]
