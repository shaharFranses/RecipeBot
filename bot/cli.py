"""Try the extractor from the command line:

    python bot/cli.py https://www.instagram.com/reel/XXXX/
    python bot/cli.py --caption-only https://www.instagram.com/reel/XXXX/   # no AI key needed
"""
import argparse
import json

from reel import fetch_reel


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("url")
    p.add_argument("--caption-only", action="store_true", help="only download the caption, skip the AI step")
    args = p.parse_args()

    reel = fetch_reel(args.url, download_video=not args.caption_only)
    print(f"Author: {reel.author}\nVideo: {reel.video_path}\nCaption:\n{reel.caption}\n")
    if args.caption_only:
        return

    from extract import extract_recipe

    recipe = extract_recipe(reel)
    print(json.dumps(recipe.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
