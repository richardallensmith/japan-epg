from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from .models import Programme, XmltvChannel


def xmltv_timestamp(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("XMLTV timestamps must be timezone-aware")
    return value.strftime("%Y%m%d%H%M%S %z")


def build_xmltv(
    programmes: list[Programme],
    *,
    channels: list[XmltvChannel],
) -> ET.ElementTree:
    root = ET.Element("tv", {"generator-info-name": "Japan EPG"})
    for info in channels:
        channel = ET.SubElement(root, "channel", {"id": info.channel_id})
        ET.SubElement(channel, "display-name", {"lang": "en"}).text = info.display_name_en
        ET.SubElement(channel, "display-name", {"lang": "ja"}).text = info.display_name_ja
        if info.icon_url:
            ET.SubElement(channel, "icon", {"src": info.icon_url})

    for item in programmes:
        programme = ET.SubElement(
            root,
            "programme",
            {"start": xmltv_timestamp(item.start), "stop": xmltv_timestamp(item.stop), "channel": item.channel_id},
        )
        ET.SubElement(programme, "title", {"lang": "en"}).text = item.title_en
        ET.SubElement(programme, "title", {"lang": "ja"}).text = item.title_ja
        if item.description_en:
            ET.SubElement(programme, "desc", {"lang": "en"}).text = item.description_en
        if item.description_ja:
            ET.SubElement(programme, "desc", {"lang": "ja"}).text = item.description_ja
        if item.episode_number:
            ET.SubElement(programme, "episode-num", {"system": "onscreen"}).text = item.episode_number
        for category in item.categories_en:
            ET.SubElement(programme, "category", {"lang": "en"}).text = category
        for category in item.categories_ja:
            ET.SubElement(programme, "category", {"lang": "ja"}).text = category
        for marker in sorted(item.markers):
            ET.SubElement(programme, "category", {"lang": "en"}).text = marker.title()
        if "repeat" in item.markers:
            ET.SubElement(programme, "previously-shown")
    return ET.ElementTree(root)


def write_xmltv(tree: ET.ElementTree, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(tree, space="  ")
    temp = path.with_suffix(".tmp")
    tree.write(temp, encoding="utf-8", xml_declaration=True, short_empty_elements=True)
    temp.replace(path)
