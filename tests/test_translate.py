import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from src.translate import MyMemoryProvider, ProviderChain, TranslationCache, TranslationEngine, TranslationError


class FakeProvider:
    name = "fake"

    def translate(self, text):
        return "Translated " + text


class FailingProvider:
    name = "failing"

    def __init__(self):
        self.calls = 0

    def translate(self, _text):
        self.calls += 1
        raise TranslationError("quota exhausted")


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return b'{"responseStatus": 200, "responseData": {"translatedText": "News"}}'


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
                "Serial TV Novel: Kaze, Kaoru — Saturday Digest, Week 26 — Finale",
                engine.title("【連続テレビ小説】風、薫る　🈡土曜ダイジェスト版　第２６週"),
            )

    def test_machine_translation_retries_rate_limit(self):
        provider = MyMemoryProvider(delay=0, retry_backoff=0, max_attempts=2)
        rate_limit = HTTPError(provider.endpoint, 429, "Too Many Requests", {"Retry-After": "0"}, None)
        with patch("src.translate.urlopen", side_effect=[rate_limit, FakeResponse()]) as request, patch(
            "src.translate.time.sleep"
        ):
            self.assertEqual("News", provider.translate("ニュース"))
        self.assertEqual(2, request.call_count)

    def test_provider_chain_disables_failed_provider(self):
        failing = FailingProvider()
        chain = ProviderChain([failing, FakeProvider()])
        self.assertEqual("Translated 一", chain.translate("一"))
        self.assertEqual("Translated 二", chain.translate("二"))
        self.assertEqual(1, failing.calls)
        self.assertEqual("fake", chain.name)

    def test_broadcast_metadata_symbols_are_not_machine_translated(self):
        with tempfile.TemporaryDirectory() as temp:
            engine = self.make_engine(Path(temp))
            self.assertEqual("Translated 番組", engine.title("番組🈀🈑🈓🈖"))

    def test_new_and_secret_markers_are_rendered_in_english(self):
        with tempfile.TemporaryDirectory() as temp:
            engine = self.make_engine(Path(temp))
            self.assertEqual("Translated 番組 — New, Secret", engine.title("🈟㊙番組"))

    def test_concurrent_cache_snapshots_merge_without_losing_entries(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "translations.json"
            first = TranslationCache(path)
            second = TranslationCache(path)
            first.put("title", "一", "One", "first")
            second.put("title", "二", "Two", "second")
            first.save()
            second.save()
            merged = TranslationCache(path)
            self.assertEqual("One", merged.get("title", "一"))
            self.assertEqual("Two", merged.get("title", "二"))

class EmptyTranslationTests(unittest.TestCase):
    def test_null_response_is_a_translation_error(self):
        class NullResponse(FakeResponse):
            def read(self):
                return b'{"responseStatus":200,"responseData":{"translatedText":null}}'
        with patch('src.translate.urlopen', return_value=NullResponse()):
            with self.assertRaises(TranslationError):
                MyMemoryProvider(delay=0).translate('ニュース')

class GoogleRetryTests(unittest.TestCase):
    def test_transient_server_error_retries_before_fallback(self):
        from src.translate import GoogleTranslateProvider
        class GoogleResponse(FakeResponse):
            def read(self):
                return '[[["News","ニュース"]]]'.encode()
        provider = GoogleTranslateProvider(delay=0)
        failure = HTTPError(provider.endpoint, 503, 'Unavailable', {}, None)
        with patch('src.translate.urlopen', side_effect=[failure, GoogleResponse()]) as request, patch('src.translate.time.sleep'):
            self.assertEqual('News', provider.translate('ニュース'))
        self.assertEqual(2, request.call_count)

    def test_rate_limit_is_not_retried(self):
        from src.translate import GoogleTranslateProvider
        provider = GoogleTranslateProvider(delay=0)
        failure = HTTPError(provider.endpoint, 429, 'Rate limited', {}, None)
        with patch('src.translate.urlopen', side_effect=failure) as request:
            with self.assertRaises(TranslationError):
                provider.translate('ニュース')
        self.assertEqual(1, request.call_count)

class SatelliteMappingTests(unittest.TestCase):
    def test_reviewed_recurring_titles_override_machine_cache(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp:
            engine = TranslationEngine(title_overrides_path=root / 'config/title_overrides.yaml',
                translation_overrides_path=root / 'config/translation_overrides.yaml',
                cache_path=Path(temp) / 'cache.json', provider=FailingProvider())
            self.assertEqual('Off Air', engine.title('休止'))
            self.assertEqual('Information', engine.title('インフォメーション'))
            self.assertEqual('Programme Guide', engine.title('番組案内'))


if __name__ == "__main__":
    unittest.main()
