import unittest

from src.playlist import find_channel, parse_m3u


PLAYLIST = """#EXTM3U
#EXTINF:-1 group-title="地上デジタル" tvg-id="NHK東京・総合_jp" tvg-name="NHK G" tvg-logo="https://example/logo.png",NHK G
https://example/nhkg.m3u8
#EXTINF:-1 group-title="地上デジタル" tvg-id="NHK東京・教育_jp" tvg-name="NHK E",NHK E
https://example/nhke.m3u8
#EXTINF:-1 group-title="BS放送" tvg-id="NHK・BS_jp" tvg-name="NHK BS",NHK BS
https://example/nhkbs.m3u8
#EXTINF:-1 tvg-id="日本テレビ_jp" tvg-name="NTV",NTV
https://example/ntv.m3u8
#EXTINF:-1 tvg-id="テレビ朝日_jp" tvg-name="TV Asahi",TV Asahi
https://example/asahi.m3u8
#EXTINF:-1 tvg-id="TBS_jp" tvg-name="TBS",TBS
https://example/tbs.m3u8
#EXTINF:-1 tvg-id="テレ東_jp" tvg-name="TV Tokyo",TV Tokyo
https://example/tvtokyo.m3u8
#EXTINF:-1 tvg-id="フジテレビ_jp" tvg-name="Fuji TV",Fuji TV
https://example/fuji.m3u8
#EXTINF:-1 tvg-id="other",Other
https://example/other.m3u8
"""


class PlaylistTests(unittest.TestCase):
    def test_parse_playlist(self):
        channels = parse_m3u(PLAYLIST)
        self.assertEqual(9, len(channels))
        self.assertEqual("NHK東京・総合_jp", channels[0].tvg_id)
        self.assertEqual("https://example/nhkg.m3u8", channels[0].url)

    def test_nhk_g_channel_id_match(self):
        channel = find_channel(parse_m3u(PLAYLIST), name="NHK G")
        self.assertEqual("NHK東京・総合_jp", channel.tvg_id)

    def test_additional_nhk_channel_ids_match(self):
        channels = parse_m3u(PLAYLIST)
        self.assertEqual("NHK東京・教育_jp", find_channel(channels, name="NHK E").tvg_id)
        self.assertEqual("NHK・BS_jp", find_channel(channels, name="NHK BS").tvg_id)

    def test_commercial_channel_ids_match(self):
        channels = parse_m3u(PLAYLIST)
        expected = {
            "NTV": "日本テレビ_jp",
            "TV Asahi": "テレビ朝日_jp",
            "TBS": "TBS_jp",
            "TV Tokyo": "テレ東_jp",
            "Fuji TV": "フジテレビ_jp",
        }
        for name, tvg_id in expected.items():
            self.assertEqual(tvg_id, find_channel(channels, name=name).tvg_id)


if __name__ == "__main__":
    unittest.main()
