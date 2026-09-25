import unittest

from src.playlist import find_channel, parse_m3u


PLAYLIST = """#EXTM3U
#EXTINF:-1 group-title="地上デジタル" tvg-id="NHK東京・総合_jp" tvg-name="NHK G" tvg-logo="https://example/logo.png",NHK G
https://example/nhkg.m3u8
#EXTINF:-1 group-title="地上デジタル" tvg-id="NHK東京・教育_jp" tvg-name="NHK E",NHK E
https://example/nhke.m3u8
#EXTINF:-1 group-title="BS放送" tvg-id="NHK・BS_jp" tvg-name="NHK BS",NHK BS
https://example/nhkbs.m3u8
#EXTINF:-1 tvg-id="other",Other
https://example/other.m3u8
"""


class PlaylistTests(unittest.TestCase):
    def test_parse_playlist(self):
        channels = parse_m3u(PLAYLIST)
        self.assertEqual(4, len(channels))
        self.assertEqual("NHK東京・総合_jp", channels[0].tvg_id)
        self.assertEqual("https://example/nhkg.m3u8", channels[0].url)

    def test_nhk_g_channel_id_match(self):
        channel = find_channel(parse_m3u(PLAYLIST), name="NHK G")
        self.assertEqual("NHK東京・総合_jp", channel.tvg_id)

    def test_additional_nhk_channel_ids_match(self):
        channels = parse_m3u(PLAYLIST)
        self.assertEqual("NHK東京・教育_jp", find_channel(channels, name="NHK E").tvg_id)
        self.assertEqual("NHK・BS_jp", find_channel(channels, name="NHK BS").tvg_id)


if __name__ == "__main__":
    unittest.main()
