from __future__ import annotations

import hashlib
import json
import os
import re
import time
import unicodedata
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import Programme


class TranslationError(RuntimeError):
    pass


def load_json_yaml(path: Path) -> dict:
    """Load config written in JSON syntax, which is valid YAML 1.2."""
    return json.loads(path.read_text(encoding="utf-8"))


class MyMemoryProvider:
    """No-key fallback MT provider. Manual/official mappings always run first."""

    name = "MyMemory"
    endpoint = "https://api.mymemory.translated.net/get"

    def __init__(
        self,
        timeout: int = 30,
        delay: float = 0.8,
        max_attempts: int = 5,
        retry_backoff: float = 3.0,
        max_retry_delay: float = 30.0,
    ):
        self.timeout = timeout
        self.delay = delay
        self.max_attempts = max_attempts
        self.retry_backoff = retry_backoff
        self.max_retry_delay = max_retry_delay

    def translate(self, text: str) -> str:
        params = {"q": text, "langpair": "ja|en"}
        if os.environ.get("MYMEMORY_EMAIL"):
            params["de"] = os.environ["MYMEMORY_EMAIL"]
        request = Request(
            f"{self.endpoint}?{urlencode(params)}",
            headers={"User-Agent": "Japan-EPG/1.0 (+XMLTV generator)"},
        )
        payload = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                break
            except HTTPError as exc:
                if exc.code != 429 or attempt == self.max_attempts:
                    raise TranslationError(f"MyMemory request failed: {exc}") from exc
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                try:
                    wait_seconds = float(retry_after) if retry_after else self.retry_backoff * (2 ** (attempt - 1))
                except ValueError:
                    wait_seconds = self.retry_backoff * (2 ** (attempt - 1))
                time.sleep(min(wait_seconds, self.max_retry_delay))
            except Exception as exc:
                raise TranslationError(f"MyMemory request failed: {exc}") from exc
        if payload is None:
            raise TranslationError("MyMemory request failed without a response")
        if payload.get("responseStatus") != 200 or payload.get("quotaFinished"):
            raise TranslationError(f"MyMemory rejected translation: {payload.get('responseDetails') or payload}")
        result = (payload.get("responseData") or {}).get("translatedText", "").strip()
        if not result or result.upper().startswith("MYMEMORY WARNING"):
            raise TranslationError("MyMemory returned no usable translation")
        time.sleep(self.delay)
        return result


class GoogleTranslateProvider:
    """Secondary no-key MT provider for uncached variable text."""

    name = "Google Translate"
    endpoint = "https://translate.googleapis.com/translate_a/single"

    def __init__(self, timeout: int = 30, delay: float = 0.35):
        self.timeout = timeout
        self.delay = delay

    def translate(self, text: str) -> str:
        params = {"client": "gtx", "sl": "ja", "tl": "en", "dt": "t", "q": text}
        request = Request(
            f"{self.endpoint}?{urlencode(params)}",
            headers={"User-Agent": "Japan-EPG/1.0 (+XMLTV generator)"},
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            result = "".join(part[0] for part in payload[0] if part and part[0]).strip()
        except Exception as exc:
            raise TranslationError(f"Google Translate request failed: {exc}") from exc
        if not result:
            raise TranslationError("Google Translate returned no usable translation")
        time.sleep(self.delay)
        return result


class ProviderChain:
    """Try replaceable MT providers in order and stop retrying one that fails."""

    def __init__(self, providers):
        self.providers = list(providers)
        self.disabled: set[int] = set()
        self._last_name = "provider chain"

    @property
    def name(self) -> str:
        return self._last_name

    def translate(self, text: str) -> str:
        errors = []
        for index, provider in enumerate(self.providers):
            if index in self.disabled:
                continue
            try:
                result = provider.translate(text)
                self._last_name = provider.name
                return result
            except TranslationError as exc:
                self.disabled.add(index)
                errors.append(str(exc))
        raise TranslationError("All machine-translation providers failed: " + "; ".join(errors))


class TranslationCache:
    def __init__(self, path: Path):
        self.path = path
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
        else:
            payload = {"version": 1, "entries": {}}
        self.entries: dict[str, dict] = payload.setdefault("entries", {})
        self.dirty = False

    @staticmethod
    def key(kind: str, text: str) -> str:
        return hashlib.sha256(f"{kind}\0ja\0en\0{text}".encode()).hexdigest()

    def get(self, kind: str, text: str) -> str | None:
        item = self.entries.get(self.key(kind, text))
        return item.get("translation") if item else None

    def put(self, kind: str, text: str, translation: str, provider: str) -> None:
        self.entries[self.key(kind, text)] = {
            "kind": kind,
            "source": text,
            "translation": translation,
            "provider": provider,
        }
        self.dirty = True

    def save(self) -> None:
        if self.dirty:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp = self.path.with_suffix(".tmp")
            temp.write_text(
                json.dumps({"version": 1, "entries": self.entries}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            temp.replace(self.path)
            self.dirty = False


class TranslationEngine:
    def __init__(
        self,
        *,
        title_overrides_path: Path,
        translation_overrides_path: Path,
        cache_path: Path,
        provider: MyMemoryProvider | None = None,
        description_limit: int = 48,
    ):
        title_data = load_json_yaml(title_overrides_path)
        manual_data = load_json_yaml(translation_overrides_path)
        self.exact_titles = title_data.get("exact", {})
        self.prefix_titles = title_data.get("prefix", {})
        self.manual_titles = manual_data.get("title", {})
        self.manual_descriptions = manual_data.get("description", {})
        self.genre_overrides = manual_data.get("genre", {})
        self.cache = TranslationCache(cache_path)
        self.provider = provider or ProviderChain([GoogleTranslateProvider(), MyMemoryProvider(max_attempts=2)])
        self.description_limit = description_limit

    @staticmethod
    def _clean_english(text: str) -> str:
        text = unicodedata.normalize("NFKC", text)
        for incorrect, preferred in {
            "Blatham": "Blossom",
            "Sandwich Man": "Sandwichman",
            "Inside the Shogunate": "Makuuchi division",
            "the Shogunate": "the Makuuchi division",
        }.items():
            text = text.replace(incorrect, preferred)
        return re.sub(r"\s+", " ", text).strip(" 　-–")

    @staticmethod
    def _kanji_number(text: str) -> int | None:
        normalized = unicodedata.normalize("NFKC", text)
        if normalized.isdigit():
            return int(normalized)
        digits = {"〇": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
        if not normalized or any(char not in digits and char not in "十百" for char in normalized):
            return None
        total = 0
        current = 0
        for char in normalized:
            if char in digits:
                current = digits[char]
            elif char == "十":
                total += (current or 1) * 10
                current = 0
            elif char == "百":
                total += (current or 1) * 100
                current = 0
        return total + current

    def _rule_title(self, text: str) -> str | None:
        normalized = unicodedata.normalize("NFKC", text)
        sumo = re.match(
            r"^大相撲(?:\((\d{4})年\))?\s*(幕内の全取組\s*)?(初場所|春場所|夏場所|名古屋場所|秋場所|九州場所)\s*([一二三四五六七八九十百\d]+)日目\s*(.*)$",
            normalized,
        )
        if sumo:
            _year, all_bouts, basho_ja, day_ja, remainder = sumo.groups()
            basho = {
                "初場所": "Hatsu Basho",
                "春場所": "Haru Basho",
                "夏場所": "Natsu Basho",
                "名古屋場所": "Nagoya Basho",
                "秋場所": "Aki Basho",
                "九州場所": "Kyushu Basho",
            }[basho_ja]
            day = self._kanji_number(day_ja)
            result = f"Grand Sumo: {basho}, Day {day if day is not None else day_ja}"
            if all_bouts:
                result += " — All Makuuchi Bouts"
            known_remainders = {
                "各段優勝力士インタビュー": "Divisional Champions Interviews",
                "優勝争いの行方は": "The Championship Race",
            }
            if remainder:
                result += " — " + known_remainders.get(remainder, self._machine("title-fragment", remainder))
            return result

        serial = re.match(r"^【連続テレビ小説】([^（(\s]+)(.*)$", text)
        if serial:
            series, remainder = serial.groups()
            series_en = self.exact_titles.get(series) or self._machine("proper-name", series)
            digest = re.search(r"土曜ダイジェスト版\s*第([0-9０-９]+)週", remainder)
            if digest:
                week = unicodedata.normalize("NFKC", digest.group(1))
                finale = "Final " if "🈡" in remainder or "最終" in remainder else ""
                return f"Serial TV Novel: {series_en} — {finale}Saturday Digest, Week {week}"
            final_week = re.search(
                r"[（(]([0-9０-９]+)[）)]最終週「道標(?:（みちしるべ）)?」",
                remainder.replace("　", ""),
            )
            if final_week:
                episode = unicodedata.normalize("NFKC", final_week.group(1))
                finale = " — Finale" if "🈡" in remainder else ""
                return f'Serial TV Novel: {series_en} — Episode {episode}{finale} — Final Week: "Signpost"'
            return self._clean_english(
                f"Serial TV Novel: {series_en}" + (f" — {self._title_fragment(remainder)}" if remainder else "")
            )
        serial_pr = re.match(r'^連続テレビ小説「([^」]+)」\s*ＰＲ$', text)
        if serial_pr:
            series = serial_pr.group(1)
            return f"Serial TV Novel: {self.exact_titles.get(series) or self._machine('proper-name', series)} — Preview"

        regional_news = re.match(r"^ニュース(?:・気象情報)?[（(]([^）)]+)[）)]$", text)
        if regional_news:
            base = "News and Weather" if "気象" in text else "News"
            return f"{base} ({self._machine('title-fragment', regional_news.group(1))})"
        return None

    def _machine(self, kind: str, text: str) -> str:
        cached = self.cache.get(kind, text)
        if cached:
            return self._clean_english(cached)
        try:
            result = self._clean_english(self.provider.translate(text))
        except TranslationError as exc:
            excerpt = text if len(text) <= 80 else text[:77] + "..."
            raise TranslationError(f"Unable to translate {kind} text {excerpt!r}: {exc}") from exc
        self.cache.put(kind, text, result, self.provider.name)
        self.cache.save()  # retain progress if a later request fails
        return result

    def _title_fragment(self, text: str) -> str:
        markers = []
        for symbol, label in (("🈡", "Finale"), ("🈞", "Repeat"), ("🈢", "Live")):
            if symbol in text:
                markers.append(label)
                text = text.replace(symbol, "")
        translated = self._machine("title-fragment", text.strip()) if text.strip() else ""
        if markers:
            marker_text = ", ".join(markers)
            return f"{marker_text} — {translated}" if translated else marker_text
        return translated

    def _title_without_broadcast_markers(self, text: str) -> str:
        if text in self.manual_titles:
            return self.manual_titles[text]
        if text in self.exact_titles:
            return self.exact_titles[text]
        rule_result = self._rule_title(text)
        if rule_result:
            return rule_result
        for prefix in sorted(self.prefix_titles, key=len, reverse=True):
            if text.startswith(prefix):
                remainder = text[len(prefix) :].strip(" 　:：")
                known = self.prefix_titles[prefix]
                if not remainder:
                    return known
                translated_remainder = self._title_fragment(remainder)
                separator = "" if known.endswith((" ", ": ")) else ": "
                result = self._clean_english(known + separator + translated_remainder)
                self.cache.put("title", text, result, "mapping+" + self.provider.name)
                self.cache.save()
                return result
        cached = self.cache.get("title", text)
        if cached:
            return self._clean_english(cached)
        return self._machine("title", text)

    def title(self, text: str) -> str:
        marker_labels = []
        markers = {
            "🈞": "Repeat",
            "🈢": "Live",
            "🈡": "Finale",
            "🈕": "New",
        }
        cleaned = text
        for symbol, label in markers.items():
            if symbol in cleaned:
                marker_labels.append(label)
            cleaned = cleaned.replace(symbol, "")
        for symbol in ("🈀", "🈑", "🈓", "🈖", "🈐", "🈔", "🈙", "🈚", "🈒", "🅂"):
            cleaned = cleaned.replace(symbol, "")
        result = self._title_without_broadcast_markers(cleaned.strip())
        if marker_labels:
            result += " — " + ", ".join(marker_labels)
        return result

    def _description_excerpt(self, text: str) -> str:
        if len(text) <= self.description_limit:
            return text
        segment = text[: self.description_limit]
        for punctuation in ("。", "！", "？"):
            pos = segment.rfind(punctuation)
            if pos >= max(12, self.description_limit // 2):
                return segment[: pos + 1]
        return segment.rstrip("、， ") + "…"

    def description(self, text: str) -> str:
        if not text:
            return ""
        if text in self.manual_descriptions:
            return self.manual_descriptions[text]
        cached = self.cache.get("description", text)
        if cached:
            return self._clean_english(cached)
        excerpt = self._description_excerpt(text)
        result = self._machine("description-excerpt", excerpt)
        self.cache.put("description", text, result, self.provider.name + " (summary excerpt)")
        self.cache.save()
        return result

    def genre(self, text: str) -> str:
        if text in self.genre_overrides:
            return self.genre_overrides[text]
        cached = self.cache.get("genre", text)
        if cached:
            return self._clean_english(cached)
        return self._machine("genre", text)

    def enrich(self, programmes: list[Programme]) -> list[Programme]:
        for programme in programmes:
            programme.title_en = self.title(programme.title_ja)
            programme.description_en = self.description(programme.description_ja)
            programme.categories_en = [self.genre(category) for category in programme.categories_ja]
        self.cache.save()
        return programmes
