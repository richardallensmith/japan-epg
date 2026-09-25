import unittest

from src.playlist import find_channel, parse_m3u


PLAYLIST = """#EXTM3U
#EXTINF:-1 group-title="地上デジタル" tvg-id="NHK東京・総合_jp" tvg-name="NHK G" tvg-logo="https://example/logo.png",NHK G
https://example/nhkg.m3u8
#EXTINF:-1 tvg-id="other",Other
https://example/other.m3u8
"""


class PlaylistTests(unittest.TestCase):
    def test_parse_playlist(self):
        channels = parse_m3u(PLAYLIST)
        self.assertEqual(2, len(channels))
        self.assertEqual("NHK東京・総合_jp", channels[0].tvg_id)
        self.assertEqual("https://example/nhkg.m3u8", channels[0].url)

    def test_nhk_g_channel_id_match(self):
        channel = find_channel(parse_m3u(PLAYLIST), name="NHK G")
        self.assertEqual("NHK東京・総合_jp", channel.tvg_id)


if __name__ == "__main__":
    unittest.main()
