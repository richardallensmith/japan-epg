import tempfile
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.models import Programme, XmltvChannel
from src.normalize import deduplicate
from src.validate import ValidationError, parse_xmltv_timestamp, validate_feed
from src.xmltv import build_xmltv, xmltv_timestamp

CHANNEL = "NHK東京・総合_jp"
CHANNEL_2 = "NHK東京・教育_jp"
JST = timezone(timedelta(hours=9))


def channels(*ids):
    return [
        XmltvChannel(channel_id=value, display_name_en=value, display_name_ja=value)
        for value in (ids or (CHANNEL,))
    ]


def programme(start=None, title="A & B <ニュース>"):
    start = start or datetime(2026, 9, 26, 19, 0, tzinfo=JST)
    return Programme(
        channel_id=CHANNEL,
        start=start,
        stop=start + timedelta(minutes=30),
        title_ja=title,
        title_en="A & B <News>",
        description_ja="説明 & 詳細",
        description_en="Description & details",
    )


class XmltvTests(unittest.TestCase):
    def test_timestamp_has_japan_offset(self):
        value = xmltv_timestamp(datetime(2026, 9, 26, 19, 0, tzinfo=JST))
        self.assertEqual("20260926190000 +0900", value)
        self.assertEqual(timedelta(hours=9), parse_xmltv_timestamp(value).utcoffset())

    def test_xml_escaping_round_trip(self):
        tree = build_xmltv(
            [programme()], channels=channels(CHANNEL)
        )
        raw = ET.tostring(tree.getroot(), encoding="unicode")
        self.assertIn("A &amp; B &lt;ニュース&gt;", raw)
        self.assertEqual("A & B <ニュース>", tree.findtext("programme/title[@lang='ja']"))

    def test_bilingual_titles(self):
        tree = build_xmltv(
            [programme()], channels=channels(CHANNEL)
        )
        titles = {(node.get("lang"), node.text) for node in tree.findall("programme/title")}
        self.assertIn(("en", "A & B <News>"), titles)
        self.assertIn(("ja", "A & B <ニュース>"), titles)

    def test_duplicate_prevention(self):
        first = programme()
        result = deduplicate([first, programme()])
        self.assertEqual(1, len(result))

    def test_validation_passes(self):
        now = datetime(2026, 9, 26, 18, 0, tzinfo=JST)
        tree = build_xmltv(
            [programme()], channels=channels(CHANNEL)
        )
        result = validate_feed(
            tree,
            expected_channel_ids={CHANNEL},
            playlist_channel_ids={CHANNEL},
            now=now,
            min_future_hours=1,
        )
        self.assertEqual(1, result["programmes"])

    def test_validation_rejects_bad_channel_id(self):
        tree = build_xmltv(
            [programme()], channels=channels(CHANNEL)
        )
        with self.assertRaises(ValidationError):
            validate_feed(
                tree,
                expected_channel_ids={CHANNEL},
                playlist_channel_ids={"invented.id"},
                now=datetime(2026, 9, 26, 18, 0, tzinfo=JST),
            )

    def test_validation_rejects_malformed_and_reversed_times(self):
        tree = build_xmltv(
            [programme()], channels=channels(CHANNEL)
        )
        element = tree.find("programme")
        element.set("start", "bad")
        with self.assertRaises(ValidationError):
            validate_feed(
                tree,
                expected_channel_ids={CHANNEL},
                playlist_channel_ids={CHANNEL},
                now=datetime(2026, 9, 26, 18, 0, tzinfo=JST),
            )
        element.set("start", "20260926200000 +0900")
        element.set("stop", "20260926190000 +0900")
        with self.assertRaises(ValidationError):
            validate_feed(
                tree,
                expected_channel_ids={CHANNEL},
                playlist_channel_ids={CHANNEL},
                now=datetime(2026, 9, 26, 18, 0, tzinfo=JST),
            )

    def test_validation_rejects_duplicate_xml(self):
        tree = build_xmltv(
            [programme(), programme()], channels=channels(CHANNEL)
        )
        with self.assertRaises(ValidationError):
            validate_feed(
                tree,
                expected_channel_ids={CHANNEL},
                playlist_channel_ids={CHANNEL},
                now=datetime(2026, 9, 26, 18, 0, tzinfo=JST),
            )

    def test_validation_rejects_stale_feed(self):
        old = programme(start=datetime(2026, 9, 25, 10, 0, tzinfo=JST))
        tree = build_xmltv([old], channels=channels(CHANNEL))
        with self.assertRaises(ValidationError):
            validate_feed(
                tree,
                expected_channel_ids={CHANNEL},
                playlist_channel_ids={CHANNEL},
                now=datetime(2026, 9, 26, 18, 0, tzinfo=JST),
            )

    def test_validation_requires_programmes_for_every_channel(self):
        tree = build_xmltv([programme()], channels=channels(CHANNEL, CHANNEL_2))
        with self.assertRaises(ValidationError):
            validate_feed(
                tree,
                expected_channel_ids={CHANNEL, CHANNEL_2},
                playlist_channel_ids={CHANNEL, CHANNEL_2},
                now=datetime(2026, 9, 26, 18, 0, tzinfo=JST),
            )


if __name__ == "__main__":
    unittest.main()
