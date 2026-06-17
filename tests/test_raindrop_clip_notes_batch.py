import datetime as dt
import importlib.util
import pathlib
import unittest


SCRIPT_PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "raindrop_clip_notes_batch.py"
SPEC = importlib.util.spec_from_file_location("raindrop_clip_notes_batch", SCRIPT_PATH)
batch = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(batch)


class RaindropClipNotesBatchTests(unittest.TestCase):
    def test_short_note_title_starts_with_raindrop_id_and_truncates(self):
        title = batch.short_note_title(
            {
                "id": 123,
                "title": "A very long title " * 10,
            },
            max_base_length=20,
        )
        self.assertTrue(title.startswith("RD 123 - A very long title..."))
        self.assertTrue(title.endswith(" - Clip Notes"))

    def test_classify_news_item_adds_revisit_and_tags(self):
        classification = batch.classify_raindrop(
            {
                "id": 123,
                "title": "Trump on Iran deal",
                "domain": "apple.news",
                "excerpt": "Breaking news about a ceasefire.",
                "link": "https://apple.news/example",
            },
            today=dt.date(2026, 6, 17),
        )
        self.assertEqual(classification["lifecycle"], "short-lived")
        self.assertEqual(classification["category"], "news")
        self.assertEqual(classification["revisit"], "2026-06-24")
        self.assertIn("#apple-news", classification["tags"])

    def test_classify_unknown_social_item_uses_personal_category(self):
        classification = batch.classify_raindrop(
            {
                "id": 123,
                "title": "https://x.com/user/status/123",
                "domain": "x.com",
                "excerpt": "",
                "link": "https://x.com/user/status/123",
            },
            today=dt.date(2026, 6, 17),
        )
        self.assertEqual(classification["category"], "personal")
        self.assertIn("#reference", classification["tags"])
        self.assertIn("#personal", classification["tags"])

    def test_parse_found_note(self):
        self.assertEqual(batch.parse_found_note("FOUND: RD 123 - Example"), "RD 123 - Example")
        self.assertIsNone(batch.parse_found_note("MISSING: 123"))


if __name__ == "__main__":
    unittest.main()
