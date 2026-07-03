import json, os, sys, unittest
from unittest import mock

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "wordpress-api-pro", "scripts")
sys.path.insert(0, os.path.abspath(SCRIPTS))

import create_post  # noqa: E402
import upload_media  # noqa: E402


class FakeResp:
    def __init__(self, payload, code=200):
        self._b = json.dumps(payload).encode()
        self.status = code
    def read(self): return self._b
    def __enter__(self): return self
    def __exit__(self, *a): return False


class ResolveRestBaseTest(unittest.TestCase):
    def test_uses_rest_base_from_types(self):
        with mock.patch.object(create_post.urllib.request, "urlopen",
                               return_value=FakeResp({"rest_base": "projects"})):
            self.assertEqual(
                create_post.resolve_rest_base("http://x", "a", "projects"), "projects")

    def test_falls_back_to_slug_on_error(self):
        with mock.patch.object(create_post.urllib.request, "urlopen",
                               side_effect=Exception("404")):
            self.assertEqual(
                create_post.resolve_rest_base("http://x", "a", "team"), "team")


class ResolveTaxonomyRestBaseTest(unittest.TestCase):
    def test_hits_taxonomies_endpoint_not_types(self):
        """A taxonomy's rest_base must be read from /wp/v2/taxonomies/{tax},
        NOT the post-type /wp/v2/types/{...} endpoint (which 404s for a tax)."""
        seen = {}

        def fake_get(url, auth):
            seen["url"] = url
            return {"rest_base": "project_category"}

        with mock.patch.object(create_post, "_get", side_effect=fake_get):
            rb = create_post.resolve_taxonomy_rest_base("http://x", "a", "project_cat")
        self.assertEqual(rb, "project_category")
        self.assertIn("/wp-json/wp/v2/taxonomies/project_cat", seen["url"])
        self.assertNotIn("/types/", seen["url"])

    def test_falls_back_to_slug_on_error(self):
        with mock.patch.object(create_post, "_get", side_effect=Exception("404")):
            self.assertEqual(
                create_post.resolve_taxonomy_rest_base("http://x", "a", "genre"), "genre")


class ResolveTermsTest(unittest.TestCase):
    def test_existing_term_resolves_to_id(self):
        responses = [
            FakeResp({"rest_base": "project_category"}),   # taxonomy rest base
            FakeResp([{"id": 5, "name": "Branding"}]),     # term search hit
        ]
        with mock.patch.object(create_post.urllib.request, "urlopen",
                               side_effect=responses):
            out = create_post.resolve_terms("http://x", "a",
                                             {"project_category": ["Branding"]},
                                             create_missing=False)
            self.assertEqual(out, {"project_category": [5]})

    def test_term_resolution_queries_taxonomy_rest_base(self):
        """The term search + create must use the taxonomy's rest_base in the URL."""
        seen = []

        def fake_urlopen(req, *a, **k):
            seen.append(req.full_url)
            if "/taxonomies/" in req.full_url:
                return FakeResp({"rest_base": "genre"})
            return FakeResp([{"id": 9, "name": "Jazz"}])

        with mock.patch.object(create_post.urllib.request, "urlopen",
                               side_effect=fake_urlopen):
            out = create_post.resolve_terms("http://x", "a",
                                             {"music_genre": ["Jazz"]},
                                             create_missing=False)
        self.assertEqual(out, {"music_genre": [9]})
        self.assertTrue(any("/wp-json/wp/v2/genre?search=" in u for u in seen))


class SetFeaturedImageTest(unittest.TestCase):
    def test_failure_raises_recoverable_exception_not_systemexit(self):
        """A featured-image failure must raise a normal Exception so a batching
        caller (seed_content.seed) can record a per-entry failure — never
        SystemExit, which its `except Exception` would not catch."""
        with mock.patch.object(upload_media.urllib.request, "urlopen",
                               side_effect=Exception("boom")):
            try:
                upload_media.set_featured_image("http://x", "u", "p", 1, 2)
            except SystemExit:
                self.fail("set_featured_image raised SystemExit — would abort the whole seed batch")
            except Exception:
                pass  # expected: a recoverable exception
            else:
                self.fail("set_featured_image did not raise on failure")

    def test_failure_raises_runtimeerror(self):
        with mock.patch.object(upload_media.urllib.request, "urlopen",
                               side_effect=Exception("boom")):
            with self.assertRaises(RuntimeError):
                upload_media.set_featured_image("http://x", "u", "p", 1, 2)

    def test_routes_through_rest_base(self):
        """CPT entries must set featured media on /wp/v2/{rest_base}/{id}."""
        seen = {}

        def fake_urlopen(req, *a, **k):
            seen["url"] = req.full_url
            return FakeResp({"id": 7, "featured_media": 2})

        with mock.patch.object(upload_media.urllib.request, "urlopen",
                               side_effect=fake_urlopen):
            upload_media.set_featured_image("http://x", "u", "p", 7, 2, rest_base="projects")
        self.assertIn("/wp-json/wp/v2/projects/7", seen["url"])


import seed_content  # noqa: E402


class SeedDryRunTest(unittest.TestCase):
    def test_dry_run_plans_every_entry_without_network(self):
        fixture = os.path.join(os.path.dirname(__file__), "fixtures", "seed.json")
        with open(fixture) as f:
            dataset = json.load(f)
        plan = seed_content.plan_seed(dataset)
        self.assertEqual(len(plan), 2)
        self.assertEqual(plan[0]["post_type"], "projects")
        self.assertIn("acf", plan[0]["will_set"])
        self.assertIn("terms", plan[0]["will_set"])
        self.assertEqual(plan[1]["featured_image_kind"], "url")
        self.assertEqual(plan[0]["featured_image_kind"], "media_id")


if __name__ == "__main__":
    unittest.main()
