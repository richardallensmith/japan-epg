from __future__ import annotations

import unittest

from src.stream_health import (
    ProbeResult,
    apply_results,
    parse_playlist,
    publishable_keys,
    reconcile_inventory,
    render_playlist,
    reviewed_display_names,
    should_suppress_mass_failure,
)


PLAYLIST = """#EXTM3U url-tvg="https://example.invalid/epg.xml"

#EXTINF:-1 group-title="News" tvg-id="one.jp" tvg-name="One" tvg-logo="https://example/1.png",One
https://example.invalid/one.m3u8

#EXTINF:-1 group-title="Music" tvg-id="two.jp" tvg-name="Two" tvg-logo="https://example/2.png",Two
https://example.invalid/two.m3u8
"""


class StreamHealthTests(unittest.TestCase):
    def test_parse_and_render_preserve_channel_metadata_and_order(self):
        header, entries = parse_playlist(PLAYLIST)
        self.assertEqual("#EXTM3U url-tvg=\"https://example.invalid/epg.xml\"", header)
        self.assertEqual(["One", "Two"], [entry.name for entry in entries])
        self.assertEqual(["tvg:one.jp", "tvg:two.jp"], [entry.key for entry in entries])

        rendered = render_playlist(header, entries, {entries[1].key})
        self.assertNotIn(",One\n", rendered)
        self.assertIn(entries[1].extinf, rendered)
        self.assertIn(entries[1].url, rendered)

    def test_render_playlist_uses_english_first_visible_name_without_changing_metadata(self):
        header, entries = parse_playlist(PLAYLIST)
        rendered = render_playlist(
            header,
            entries,
            {entries[1].key},
            {"two.jp": "Two English (二番)"},
        )
        self.assertIn('tvg-id="two.jp" tvg-name="Two"', rendered)
        self.assertIn(',Two English (二番)\n', rendered)
        self.assertNotIn(',Two\n', rendered)

    def test_bootstrap_channels_are_grandfathered_and_publishable(self):
        _, entries = parse_playlist(PLAYLIST)
        state = {"channels": {}}
        reconcile_inventory(state, entries, "2026-10-21T00:00:00+00:00", bootstrap=True)

        self.assertEqual({"healthy"}, {record["state"] for record in state["channels"].values()})
        self.assertTrue(all(record["grandfathered"] for record in state["channels"].values()))
        self.assertEqual({entry.key for entry in entries}, publishable_keys(state))

    def test_healthy_channel_becomes_suspect_then_removed(self):
        _, entries = parse_playlist(PLAYLIST)
        entry = entries[0]
        state = {"channels": {}}
        reconcile_inventory(state, [entry], "t0", bootstrap=True)

        fail = {entry.key: ProbeResult(entry.key, False, (), 0.2, "404")}
        for n in range(1, 7):
            apply_results(
                state,
                fail,
                now=f"t{n}",
                suspect_after=2,
                remove_after=6,
                restore_after=2,
                new_successes_required=1,
                suppress_failures=False,
            )

        record = state["channels"][entry.key]
        self.assertEqual("removed", record["state"])
        self.assertEqual(6, record["consecutive_failures"])
        self.assertNotIn(entry.key, publishable_keys(state))

    def test_removed_channel_requires_two_successes_to_restore(self):
        _, entries = parse_playlist(PLAYLIST)
        entry = entries[0]
        state = {"channels": {}}
        reconcile_inventory(state, [entry], "t0", bootstrap=True)
        record = state["channels"][entry.key]
        record["state"] = "removed"
        record["consecutive_failures"] = 6

        success = {entry.key: ProbeResult(entry.key, True, ("video",), 1.0, "")}
        apply_results(
            state,
            success,
            now="t1",
            suspect_after=2,
            remove_after=6,
            restore_after=2,
            new_successes_required=1,
            suppress_failures=False,
        )
        self.assertEqual("removed", record["state"])

        apply_results(
            state,
            success,
            now="t2",
            suspect_after=2,
            remove_after=6,
            restore_after=2,
            new_successes_required=1,
            suppress_failures=False,
        )
        self.assertEqual("healthy", record["state"])

    def test_new_channel_requires_success_before_publication(self):
        _, entries = parse_playlist(PLAYLIST)
        entry = entries[0]
        state = {"channels": {}}
        reconcile_inventory(state, [entry], "t0", bootstrap=False)

        self.assertEqual("new", state["channels"][entry.key]["state"])
        self.assertNotIn(entry.key, publishable_keys(state))

        apply_results(
            state,
            {entry.key: ProbeResult(entry.key, True, ("audio",), 1.0, "")},
            now="t1",
            suspect_after=2,
            remove_after=6,
            restore_after=2,
            new_successes_required=1,
            suppress_failures=False,
        )
        self.assertEqual("healthy", state["channels"][entry.key]["state"])
        self.assertIn(entry.key, publishable_keys(state))

    def test_suppressed_failure_does_not_increment_counter(self):
        _, entries = parse_playlist(PLAYLIST)
        entry = entries[0]
        state = {"channels": {}}
        reconcile_inventory(state, [entry], "t0", bootstrap=True)

        apply_results(
            state,
            {entry.key: ProbeResult(entry.key, False, (), 0.2, "404")},
            now="t1",
            suspect_after=2,
            remove_after=6,
            restore_after=2,
            new_successes_required=1,
            suppress_failures=True,
        )
        self.assertEqual(0, state["channels"][entry.key]["consecutive_failures"])
        self.assertEqual("healthy", state["channels"][entry.key]["state"])

    def test_mass_failure_uses_only_proven_good_active_channels(self):
        _, entries = parse_playlist(PLAYLIST)
        state = {"channels": {}}
        reconcile_inventory(state, entries, "t0", bootstrap=True)

        for entry in entries:
            state["channels"][entry.key]["ever_succeeded"] = True

        results = {
            entries[0].key: ProbeResult(entries[0].key, False, (), 0.2, "404"),
            entries[1].key: ProbeResult(entries[1].key, True, ("video",), 1.0, ""),
        }
        suppressed, size, failures, ratio = should_suppress_mass_failure(
            state, results, threshold=0.30, minimum_baseline=2
        )
        self.assertTrue(suppressed)
        self.assertEqual(2, size)
        self.assertEqual(1, failures)
        self.assertEqual(0.5, ratio)

    def test_upstream_removed_channel_is_not_publishable(self):
        _, entries = parse_playlist(PLAYLIST)
        state = {"channels": {}}
        reconcile_inventory(state, entries, "t0", bootstrap=True)
        reconcile_inventory(state, [entries[0]], "t1", bootstrap=False)

        missing = state["channels"][entries[1].key]
        self.assertEqual("upstream_removed", missing["state"])
        self.assertFalse(missing["present_upstream"])
        self.assertNotIn(entries[1].key, publishable_keys(state))


if __name__ == "__main__":
    unittest.main()
