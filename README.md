# RecipeBot — Michal's recipe book

A WhatsApp bot that takes an Instagram reel link and saves the recipe to a recipe book website.

## Status
- [x] Reel → recipe extractor (`bot/`)
- [ ] WhatsApp webhook (Meta Cloud API test number)
- [ ] Storage (Supabase)
- [ ] Recipe book website (GitHub Pages, Hebrew RTL, editable notes)

## Try the extractor
```bash
pip install -r requirements.txt
export GEMINI_API_KEY=...        # free key from https://aistudio.google.com/apikey
python bot/cli.py https://www.instagram.com/reel/XXXX/
python bot/cli.py --caption-only https://www.instagram.com/reel/XXXX/   # no key needed
```

How it works: `bot/reel.py` downloads the reel's caption and a small copy of the video with yt-dlp.
`bot/extract.py` sends both to Gemini, which returns a structured Hebrew recipe
(title, servings, time, ingredients with amounts, steps, tags).
