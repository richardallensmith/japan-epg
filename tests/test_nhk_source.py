import unittest

from src.fetch.nhk import NHKTimetableSource, SourceError


class NHKSourceTests(unittest.TestCase):
    def test_structurally_empty_schedule_is_rejected(self):
        source = NHKTimetableSource()
        with self.assertRaises(SourceError):
            source._parse({"g1": {"publication": []}}, "NHK東京・総合_jp", "2026-09-26")


if __name__ == "__main__":
    unittest.main()
