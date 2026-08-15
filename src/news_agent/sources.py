from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    kind: str = "rss"


# Keep this list conservative: public feeds/endpoints only. Add or remove feeds as their availability is verified.
DEFAULT_SOURCES = [
    Source("Gazeta.uz", "https://www.gazeta.uz/ru/rss/", "rss"),
    Source("Kun.uz", "https://kun.uz/ru/rss", "rss"),
    Source("Daryo", "https://daryo.uz/feed", "rss"),
    Source("UzA", "https://uza.uz/ru/rss", "rss"),
]
