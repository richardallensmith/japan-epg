import unittest

from src.fetch.base import SourceError
from src.fetch.bangumi import BangumiSource, _BangumiParser


HTML = """
<div id="ch_area"><ul>
  <li><p>4 日テレ1</p></li><li><p>5 テレビ朝日</p></li>
</ul></div>
<div id="program_area">
<ul id="program_line_1">
  <li s="202609260500" e="202609260530" pid="123" se-id="event-1">
    <div class="program_time gc-anime">00</div>
    <a class="title_link" href="/tv_events/example">
      <p class="program_title">アニメ番組（12）🈞</p>
      <p class="program_detail">説明 &amp; 詳細</p>
    </a>
  </li>
  <li s="202609260530" e="202609260600" pid="124"><div class="program_time no_genre">30</div><p class="program_title">ニュース</p><p class="program_detail"></p></li>
  <li s="202609260600" e="202609260630" pid="125"><div class="program_time gc-sports">00</div><p class="program_title">スポーツ</p><p class="program_detail">試合</p></li>
</ul>
<ul id="program_line_2">
  <li s="202609260500" e="202609260600" pid="200"><div class="program_time no_genre">00</div><p class="program_title">朝番組</p><p class="program_detail">紹介</p></li>
  <li s="202609260600" e="202609260700" pid="201"><div class="program_time no_genre">00</div><p class="program_title">情報番組</p><p class="program_detail">紹介</p></li>
  <li s="202609260700" e="202609260800" pid="202"><div class="program_time no_genre">00</div><p class="program_title">ドラマ</p><p class="program_detail">紹介</p></li>
</ul>
</div>
"""


class BangumiSourceTests(unittest.TestCase):
    def test_parser_maps_station_times_metadata_and_markers(self):
        parser = _BangumiParser()
        parser.feed(HTML)
        source = BangumiSource(station="日テレ1")
        programmes = source._parse(parser, "日本テレビ_jp", "20260926")
        self.assertEqual(3, len(programmes))
        first = programmes[0]
        self.assertEqual("アニメ番組（12）🈞", first.title_ja)
        self.assertEqual("説明 & 詳細", first.description_ja)
        self.assertEqual("12", first.episode_number)
        self.assertEqual(["アニメ／特撮"], first.categories_ja)
        self.assertEqual({"repeat"}, first.markers)
        self.assertEqual("2026-09-26T05:00:00+09:00", first.start.isoformat())

    def test_guarded_station_line_selects_ambiguous_channel(self):
        parser = _BangumiParser()
        parser.feed(HTML)
        source = BangumiSource(station="テレビ朝日", lineup="tokyo", station_line=2)
        programmes = source._parse(parser, "テレビ朝日_jp", "20260926")
        self.assertEqual(3, len(programmes))
        self.assertEqual("朝番組", programmes[0].title_ja)

    def test_guarded_station_line_rejects_lineup_change(self):
        parser = _BangumiParser()
        parser.feed(HTML)
        source = BangumiSource(station="TOKYO", lineup="tokyo", station_line=2)
        with self.assertRaises(SourceError):
            source._parse(parser, "TOKYO・MX2_jp", "20260926")

    def test_new_marker_is_preserved(self):
        self.assertIn("new", BangumiSource._markers("🈟新番組"))

class ServiceIdentityTests(unittest.TestCase):
    def test_service_id_rejects_station_rename_collision(self):
        parser = _BangumiParser()
        parser.feed(HTML)
        source = BangumiSource(station='日テレ1', station_line=1, station_id='191')
        with self.assertRaisesRegex(SourceError, 'service ID changed'):
            source._parse(parser, 'CH.621', '20260926')

    def test_service_id_and_display_name_both_required(self):
        html = HTML.replace('event-1', '191-1').replace('pid="124"', 'pid="124" se-id="191-2"').replace('pid="125"', 'pid="125" se-id="191-3"')
        parser = _BangumiParser()
        parser.feed(html)
        source = BangumiSource(station='日テレ1', station_line=1, station_id='191')
        self.assertEqual(3, len(source._parse(parser, 'CH.621', '20260926')))
        source.station = 'WOWOW'
        with self.assertRaises(SourceError):
            source._parse(parser, 'CH.621', '20260926')


if __name__ == "__main__":
    unittest.main()
