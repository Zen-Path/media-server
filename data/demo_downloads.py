import random
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional

from scripts.media_server.src.constants import DownloadStatus, MediaType

DEFAULT_OPTIONS = {
    "end_time_probability": 0.9,
    "max_days_offset": 200,
    "max_duration_seconds": 3600,
    "min_duration_seconds": 5,
    "status_success_probability": 0.6,
    "status_failure_probability": 0.1,
    "status_mixed_probability": 0.15,
    "status_in_progress_probability": 0.05,
    "seed": 42,
}


def resolve_status(
    item: Dict[str, Any], rng: random.Random, config: Dict[str, Any], now: datetime
) -> int:
    """
    Enforces logical consistency between status and timestamps.
    Ensures end_time is never in the future relative to 'now'.
    """
    # Ensure end_time <= now
    if item.get("end_time") and item["end_time"] > now:
        item["end_time"] = now

    has_end_time = item.get("end_time") is not None
    current_status = item.get("status")

    # If it has an end_time, it MUST be a terminal state.
    if has_end_time:
        if current_status in [
            DownloadStatus.DONE,
            DownloadStatus.FAILED,
            DownloadStatus.MIXED,
        ]:
            return current_status

        # If it was PENDING/IN_PROGRESS but has an end_time, we force a terminal state
        p = rng.random()
        success_limit = config["status_success_probability"]
        failure_limit = success_limit + config["status_failure_probability"]

        if p < success_limit:
            return DownloadStatus.DONE
        if p < failure_limit:
            return DownloadStatus.FAILED
        return DownloadStatus.MIXED

    # If it has NO end_time, it MUST be an active state.
    if not has_end_time:
        if current_status in [DownloadStatus.PENDING, DownloadStatus.IN_PROGRESS]:
            return current_status

        # Fallback for missing/terminal status on an item with no end_time
        return (
            DownloadStatus.IN_PROGRESS if rng.random() < 0.3 else DownloadStatus.PENDING
        )

    return current_status or DownloadStatus.PENDING


@lru_cache(maxsize=1)
def get_demo_downloads(
    now: Optional[datetime] = None, row_count: Optional[int] = None, **options: Any
) -> List[Dict[str, Any]]:
    config = {**DEFAULT_OPTIONS, **options}

    # Avoid side effects on global random
    rng = random.Random(config["seed"])

    now = now or datetime.now()

    raw_data: List[Dict[str, Any]] = [
        {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "title": "Rick Astley - Never Gonna Give You Up (Official Video) - YouTube",
            "media_type": MediaType.VIDEO,
            "start_time": now - timedelta(seconds=2),
            "end_time": now,
            "status": DownloadStatus.DONE,
        },
        {
            "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
            "title": "Me at the zoo - YouTube",
            "media_type": MediaType.VIDEO,
            "start_time": now - timedelta(seconds=30),
            "end_time": now - timedelta(seconds=25),
        },
        # Long title
        {
            "url": "https://very-long-url-website.com/long-title-test",
            "title": "This is an extremely long title to test if the CSS truncation"
            "works correctly in the dashboard table row and does not break the layout"
            "of the cell",
            "media_type": MediaType.TEXT,
            "start_time": now - timedelta(minutes=1, seconds=10),
            "end_time": now - timedelta(minutes=1, seconds=5),
            "status": DownloadStatus.FAILED,
        },
        {
            "url": "https://x.com/updates/status/12345",
            "title": "Breaking News: Python 3.14 Released 🚀",
            "media_type": MediaType.IMAGE,
            "start_time": now - timedelta(minutes=5, seconds=25),
            "end_time": None,
            "status": DownloadStatus.IN_PROGRESS,
        },
        # Missing title
        {
            "url": "https://cdn.example.com/assets/logo.png",
            "title": None,
            "media_type": MediaType.IMAGE,
            "start_time": now - timedelta(hours=1, minutes=1, seconds=10),
            "end_time": now - timedelta(hours=1, minutes=1, seconds=5),
        },
        # Gallery media
        {
            "url": "https://imgur.com/gallery/cats",
            "title": "Best Cat Memes 2025",
            "media_type": MediaType.GALLERY,
            "start_time": now - timedelta(hours=1, minutes=45, seconds=10),
            "end_time": now - timedelta(hours=1, minutes=45, seconds=5),
        },
        # Double quotes in title
        {
            "url": "https://vimeo.com/12345678",
            "title": 'Documentary: "The Life of a Software Engineer"',
            "media_type": MediaType.VIDEO,
            "start_time": now - timedelta(hours=2, minutes=5, seconds=40),
            "end_time": now - timedelta(hours=2, minutes=5, seconds=35),
        },
        {
            "url": "https://unsplash.com/photos/mountain-view",
            "title": "High resolution mountain landscape [4K]",
            "media_type": MediaType.IMAGE,
            "start_time": now - timedelta(hours=3, minutes=10, seconds=10),
            "end_time": now - timedelta(hours=3, minutes=10, seconds=5),
        },
        # Direct zip link
        {
            "url": "https://github.com/torvalds/linux/archive/master.zip",
            "title": "linux-master.zip",
            "media_type": MediaType.TEXT,
            "start_time": now - timedelta(hours=3, minutes=20, seconds=20),
            "end_time": now - timedelta(hours=3, minutes=20, seconds=10),
        },
        {
            "url": "https://www.tiktok.com/@user/video/987654",
            "title": "Viral Dance Challenge #2025",
            "media_type": MediaType.VIDEO,
            "start_time": now - timedelta(hours=4, minutes=20, seconds=30),
            "end_time": now - timedelta(hours=4, minutes=20, seconds=25),
        },
        {
            "url": "https://example.com/missing-title-2",
            "title": None,
            "media_type": MediaType.GALLERY,
            "start_time": now - timedelta(hours=4, minutes=30, seconds=35),
            "end_time": now - timedelta(hours=4, minutes=30, seconds=25),
        },
        # Start time = end time
        {
            "url": "https://www.nasa.gov/image-of-the-day",
            "title": "Nebula Cluster from James Webb Telescope",
            "media_type": MediaType.IMAGE,
            "start_time": now - timedelta(hours=5, minutes=1, seconds=1),
            "end_time": now - timedelta(hours=5, minutes=1, seconds=1),
        },
        # Same start time for the next 2
        {
            "url": "https://stackoverflow.com/questions/12345",
            "title": "How to exit vim? - Stack Overflow",
            "media_type": MediaType.TEXT,
            "start_time": now - timedelta(hours=6, minutes=1, seconds=10),
            "end_time": now - timedelta(hours=6, minutes=1, seconds=5),
        },
        {
            "url": "https://www.ted.com/talks/future_of_ai",
            "title": "The Future of AI and Humanity",
            "media_type": MediaType.VIDEO,
            "start_time": now - timedelta(hours=6, minutes=1, seconds=10),
            "end_time": now - timedelta(hours=6, minutes=1, seconds=1),
        },
        # Long running
        {
            "url": "https://www.reddit.com/r/funny/top",
            "title": "Top posts from r/funny this week",
            "media_type": MediaType.GALLERY,
            "start_time": now - timedelta(hours=6, minutes=5, seconds=1),
            "end_time": now - timedelta(hours=5, minutes=1, seconds=10),
            "status": DownloadStatus.MIXED,
        },
        # Emoji in title
        {
            "url": "https://jp.wikipedia.org/wiki/Python",
            "title": "Python (🐍) - Wikipedia",
            "media_type": MediaType.TEXT,
            "start_time": now - timedelta(hours=7, minutes=1, seconds=10),
            "end_time": now - timedelta(hours=7, minutes=1, seconds=1),
        },
        # Right-to-left title
        {
            "url": "https://ar.wikipedia.org/wiki/Python",
            "title": "بايثون (لغة برمجة) - ويكيبيديا",
            "media_type": MediaType.TEXT,
            "start_time": now - timedelta(hours=7, minutes=5, seconds=10),
            "end_time": now - timedelta(hours=7, minutes=5, seconds=1),
        },
        # Yesterday
        {
            "url": "https://spotify.com/track/123",
            "title": "lofi hip hop radio - beats to relax/study to",
            "media_type": MediaType.VIDEO,
            "start_time": now - timedelta(days=1, hours=1, minutes=5, seconds=10),
            "end_time": now - timedelta(days=1, hours=1, minutes=5, seconds=5),
        },
        {
            "url": "https://www.bbc.com/news/technology",
            "title": "Technology News - BBC News",
            "media_type": MediaType.TEXT,
            "start_time": now - timedelta(days=1, hours=2, minutes=5, seconds=15),
            "end_time": now - timedelta(days=1, hours=2, minutes=5, seconds=10),
        },
        {
            "url": "https://www.deviantart.com/art/digital-painting",
            "title": "Cyberpunk Cityscape Concept Art",
            "media_type": MediaType.IMAGE,
            "start_time": now - timedelta(days=1, hours=15, minutes=55, seconds=10),
            "end_time": now - timedelta(days=1, hours=15, minutes=50, seconds=5),
        },
        # This week
        {
            "url": "https://www.twitch.tv/videos/111222333",
            "title": "Grand Finals - EVO 2025",
            "media_type": MediaType.VIDEO,
            "start_time": now - timedelta(days=2, hours=1, minutes=5, seconds=10),
            "end_time": now - timedelta(days=2, hours=1, minutes=5, seconds=5),
        },
        {
            "url": "https://archive.org/details/old-movie",
            "title": "'Metropolis (1927)' - Full Movie",
            "media_type": MediaType.VIDEO,
            "start_time": now - timedelta(days=2, hours=5, minutes=25, seconds=10),
            "end_time": now - timedelta(days=2, hours=5, minutes=25, seconds=5),
        },
        {
            "url": "https://www.pinterest.com/pin/12345",
            "title": "DIY Home Decor Ideas",
            "media_type": MediaType.GALLERY,
            "start_time": now - timedelta(days=4, hours=1, minutes=5, seconds=10),
            "end_time": now - timedelta(days=4, hours=1, minutes=5, seconds=5),
        },
        # Last week
        {
            "url": "https://www.behance.net/gallery/ui-kit",
            "title": "Mobile App UI Kit Freebie",
            "media_type": MediaType.GALLERY,
            "start_time": now - timedelta(days=7, hours=1, minutes=5, seconds=10),
            "end_time": now - timedelta(days=7, hours=1, minutes=5, seconds=5),
        },
        {
            "url": "https://www.coursera.org/learn/machine-learning",
            "title": "Machine Learning Specialization",
            "media_type": MediaType.VIDEO,
            "start_time": now - timedelta(days=8, hours=1, minutes=5, seconds=10),
            "end_time": now - timedelta(days=8, hours=1, minutes=5, seconds=5),
        },
        {
            "url": "https://192.168.1.1/config.backup",
            "title": "Router Configuration Backup",
            "media_type": MediaType.TEXT,
            "start_time": now - timedelta(days=9, hours=1, minutes=5, seconds=10),
            "end_time": now - timedelta(days=9, hours=1, minutes=5, seconds=5),
        },
        {
            "url": "https://example.com/very/deeply/nested/url/structure/that/goes/on/forever/and/ever/to/test/wrapping",
            "title": "Deeply Nested URL Test",
            "media_type": MediaType.TEXT,
            "start_time": now - timedelta(days=10, hours=1, minutes=5, seconds=10),
            "end_time": now - timedelta(days=10, hours=1, minutes=5, seconds=5),
        },
        # Last month
        {
            "url": "https://wallhaven.cc/w/123",
            "title": "Abstract Geometric Wallpaper",
            "media_type": MediaType.IMAGE,
            "start_time": now - timedelta(days=32, hours=1, minutes=5, seconds=10),
            "end_time": now - timedelta(days=32, hours=1, minutes=5, seconds=5),
        },
        {
            "url": "https://www.instagram.com/p/Cxyz123",
            "title": "Sunset at the beach 🏖️",
            "media_type": MediaType.IMAGE,
            "start_time": now - timedelta(days=35, hours=1, seconds=10),
            "end_time": now - timedelta(days=35, hours=1, seconds=5),
        },
        {
            "url": "https://www.soundcloud.com/artist/song",
            "title": "New Single - Summer Vibes",
            "media_type": MediaType.TEXT,
            "start_time": now - timedelta(days=40, hours=5, seconds=10),
            "end_time": now - timedelta(days=40, hours=5, seconds=5),
        },
        # Very old entries
        {
            "url": "https://www.dropbox.com/s/shared/project.pdf",
            "title": "Final_Project_Report_v2_FINAL_REAL.pdf",
            "media_type": MediaType.TEXT,
            "start_time": now - timedelta(days=90, hours=1, seconds=10),
            "end_time": now - timedelta(days=90, hours=1, seconds=5),
        },
        {
            "url": "https://www.youtube.com/watch?v=intro",
            "title": "Channel Intro",
            "media_type": MediaType.VIDEO,
            "start_time": now - timedelta(days=195, hours=10, seconds=10),
            "end_time": now - timedelta(days=195, hours=10, seconds=5),
        },
    ]

    if row_count and row_count > len(raw_data):
        meta_pool = [
            {"u": d["url"], "t": d["title"], "m": d["media_type"]} for d in raw_data
        ]
        for _ in range(row_count - len(raw_data)):
            source = rng.choice(meta_pool)

            is_finished = rng.random() < config["end_time_probability"]
            start_time = now - timedelta(
                days=rng.randint(0, config["max_days_offset"]),
                seconds=rng.randint(0, 86400),
            )

            end_time = None
            if is_finished:
                end_time = start_time + timedelta(
                    seconds=rng.randint(
                        config["min_duration_seconds"], config["max_duration_seconds"]
                    )
                )

            raw_data.append(
                {
                    "url": source["u"],
                    "title": source["t"],
                    "media_type": source["m"],
                    "start_time": start_time,
                    "end_time": end_time,
                    "status": None,  # Leave it for the resolver
                }
            )

    processed_data = []
    for item in raw_data:
        item["status"] = resolve_status(item, rng, config, now)
        processed_data.append(item)

    if row_count:
        processed_data = processed_data[:row_count]

    processed_data.sort(key=lambda x: x["start_time"], reverse=True)

    return processed_data
