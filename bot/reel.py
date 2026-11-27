"""Download an Instagram reel's caption and video with yt-dlp."""
from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yt_dlp

INSTAGRAM_URL = re.compile(r"https?://(?:www\.)?instagram\.com/(?:reel|reels|p|tv)/[\w-]+", re.I)


class ReelError(Exception):
    """The reel could not be fetched (private, removed, or blocked by Instagram)."""


@dataclass
class Reel:
    url: str
    caption: str
    author: str
    thumbnail: str | None
    video_path: Path | None


def find_instagram_url(text: str) -> str | None:
    match = INSTAGRAM_URL.search(text or "")
    return match.group(0) if match else None


def fetch_reel(url: str, workdir: Path | None = None, download_video: bool = True) -> Reel:
    workdir = Path(workdir or tempfile.mkdtemp(prefix="reel-"))
    opts = {
        "quiet": True,
        "no_warnings": True,
        "outtmpl": str(workdir / "%(id)s.%(ext)s"),
        # Small mp4 is plenty for the AI to watch and keeps uploads fast.
        "format": "worst[ext=mp4]/worst",
        "skip_download": not download_video,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=download_video)
    except yt_dlp.utils.DownloadError as e:
        raise ReelError(str(e)) from e

    video_path = None
    if download_video:
        files = sorted(workdir.glob(f"{info['id']}.*"))
        video_path = files[0] if files else None

    return Reel(
        url=url,
        caption=info.get("description") or "",
        author=info.get("uploader") or info.get("channel") or "",
        thumbnail=info.get("thumbnail"),
        video_path=video_path,
    )
