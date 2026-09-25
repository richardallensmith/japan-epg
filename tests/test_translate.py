import json
import tempfile
import unittest
from pathlib import Path

from src.translate import TranslationEngine


class FakeProvider:
    name = "fake"

    def translate(self, text):
        return "Translated " + text


class TranslateTests(unittest.TestCase):
    def make_engine(self, root):
        (root / "titles").write_text(
            json.dumps(
                {
                    "exact": {"ニュース７": "NHK News 7", "風、薫る": "Kaze, Kaoru"},
                    "prefix": {},
                }
            ),
            encoding="utf-8",
        )
        (root / "manual").write_text(
            json.dumps({"title": {}, "description": {}, "genre": {}}), encoding="utf-8"
        )
        return TranslationEngine(
            title_overrides_path=root / "titles",
            translation_overrides_path=root / "manual",
            cache_path=root / "cache.json",
            provider=FakeProvider(),
        )

    def test_bilingual_known_title(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            engine = self.make_engine(root)
            self.assertEqual("NHK News 7", engine.title("ニュース７"))

    def test_grand_sumo_rule(self):
        with tempfile.TemporaryDirectory() as temp:
            engine = self.make_engine(Path(temp))
            self.assertEqual(
                "Grand Sumo: Aki Basho, Day 14",
                engine.title("大相撲（２０２６年）秋場所　十四日目"),
            )

    def test_serial_drama_digest_rule(self):
        with tempfile.TemporaryDirectory() as temp:
            engine = self.make_engine(Path(temp))
            self.assertEqual(
                "Serial TV Novel: Kaze, Kaoru — Final Saturday Digest, Week 26",
                engine.title("【連続テレビ小説】風、薫る　🈡土曜ダイジェスト版　第２６週"),
            )


if __name__ == "__main__":
    unittest.main()
