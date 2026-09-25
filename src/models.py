from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class PlaylistChannel:
    name: str
    url: str
    tvg_id: str
    tvg_name: str = ""
    tvg_logo: str = ""
    group_title: str = ""


@dataclass(frozen=True)
class XmltvChannel:
    channel_id: str
    display_name_en: str
    display_name_ja: str
    icon_url: str = ""


@dataclass
class Programme:
    channel_id: str
    start: datetime
    stop: datetime
    title_ja: str
    description_ja: str = ""
    title_en: str = ""
    description_en: str = ""
    episode_number: str = ""
    categories_ja: list[str] = field(default_factory=list)
    categories_en: list[str] = field(default_factory=list)
    markers: set[str] = field(default_factory=set)
    source_id: str = ""
    source_url: str = ""

    def identity(self) -> tuple[str, datetime, datetime, str]:
        return (self.channel_id, self.start, self.stop, self.title_ja)
