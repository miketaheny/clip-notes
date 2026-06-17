import importlib.util
import os
import pathlib
import tempfile
import unittest


SCRIPT_PATH = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "raindrop_api.py"
SPEC = importlib.util.spec_from_file_location("raindrop_api", SCRIPT_PATH)
raindrop_api = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(raindrop_api)


class RaindropApiTests(unittest.TestCase):
    def test_parse_tags_accepts_apple_note_hashtags(self):
        self.assertEqual(
            raindrop_api.parse_tags(["#clip-notes #reference,#ai", "product"]),
            ["clip-notes", "reference", "ai", "product"],
        )

    def test_parse_tags_can_keep_hash_prefix(self):
        self.assertEqual(
            raindrop_api.parse_tags(["#clip-notes #reference"], keep_hash=True),
            ["#clip-notes", "#reference"],
        )

    def test_merge_tags_preserves_existing_and_dedupes_case_insensitively(self):
        self.assertEqual(
            raindrop_api.merge_tags(["AI", "reading"], ["ai", "clip-notes"]),
            ["AI", "reading", "clip-notes"],
        )

    def test_compact_raindrop_extracts_stable_fields(self):
        compact = raindrop_api.compact_raindrop(
            {
                "_id": 123,
                "title": "Example",
                "link": "https://example.com",
                "collection": {"$id": 456},
                "tags": ["clip-notes"],
            }
        )
        self.assertEqual(compact["id"], 123)
        self.assertEqual(compact["collection_id"], 456)
        self.assertEqual(compact["tags"], ["clip-notes"])

    def test_parse_env_line_supports_basic_dotenv_syntax(self):
        self.assertEqual(
            raindrop_api.parse_env_line('export RAINDROP_ACCESS_TOKEN="abc123"'),
            ("RAINDROP_ACCESS_TOKEN", "abc123"),
        )
        self.assertIsNone(raindrop_api.parse_env_line("# comment"))
        self.assertIsNone(raindrop_api.parse_env_line("not a key"))

    def test_load_env_file_does_not_override_existing_values_by_default(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = pathlib.Path(tmpdir) / ".env"
            env_path.write_text(
                "RAINDROP_ACCESS_TOKEN=from-file\n"
                "RAINDROP_INBOX_COLLECTION=Inbox\n",
                encoding="utf-8",
            )
            old_token = os.environ.get("RAINDROP_ACCESS_TOKEN")
            old_inbox = os.environ.get("RAINDROP_INBOX_COLLECTION")
            try:
                os.environ["RAINDROP_ACCESS_TOKEN"] = "existing"
                os.environ.pop("RAINDROP_INBOX_COLLECTION", None)
                loaded = raindrop_api.load_env_file(str(env_path))
                self.assertEqual(os.environ["RAINDROP_ACCESS_TOKEN"], "existing")
                self.assertEqual(os.environ["RAINDROP_INBOX_COLLECTION"], "Inbox")
                self.assertEqual(loaded, ["RAINDROP_INBOX_COLLECTION"])
            finally:
                if old_token is None:
                    os.environ.pop("RAINDROP_ACCESS_TOKEN", None)
                else:
                    os.environ["RAINDROP_ACCESS_TOKEN"] = old_token
                if old_inbox is None:
                    os.environ.pop("RAINDROP_INBOX_COLLECTION", None)
                else:
                    os.environ["RAINDROP_INBOX_COLLECTION"] = old_inbox


if __name__ == "__main__":
    unittest.main()
