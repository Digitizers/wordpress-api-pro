import json, os, sys, unittest
from unittest import mock

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "wordpress-api-pro", "scripts")
sys.path.insert(0, os.path.abspath(SCRIPTS))

import create_post  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
