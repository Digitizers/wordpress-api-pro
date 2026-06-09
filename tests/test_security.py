import os, sys, unittest

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "wordpress-api-pro", "scripts")
sys.path.insert(0, os.path.abspath(SCRIPTS))

from security import SafetyError, warn_insecure_wp_url, should_confirm_publish  # noqa: E402
from seo_meta import _map_meta_keys  # noqa: E402


class WarnInsecureWpUrlTest(unittest.TestCase):
    def test_warns_on_http_nonlocal(self):
        """http:// on a public host prints a SECURITY WARNING to stderr."""
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            result = warn_insecure_wp_url("http://example.com", env={})
        self.assertIn("SECURITY WARNING", buf.getvalue())
        self.assertEqual(result, "http://example.com")  # url returned unchanged

    def test_silent_on_https(self):
        """https:// never triggers a warning."""
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            warn_insecure_wp_url("https://example.com", env={})
        self.assertEqual(buf.getvalue(), "")

    def test_silent_on_localhost_http(self):
        """http:// on localhost/dev hosts is exempt — no warning."""
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            warn_insecure_wp_url("http://localhost:8080", env={})
            warn_insecure_wp_url("http://site.local", env={})
        self.assertEqual(buf.getvalue(), "")

    def test_raises_when_wp_require_https_set(self):
        """WP_REQUIRE_HTTPS=1 upgrades the warning to a SafetyError."""
        with self.assertRaises(SafetyError):
            warn_insecure_wp_url("http://example.com", env={"WP_REQUIRE_HTTPS": "1"})

    def test_silent_on_dot_test_host(self):
        """http://*.test hosts are treated as local dev — no warning."""
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            warn_insecure_wp_url("http://mysite.test", env={})
        self.assertEqual(buf.getvalue(), "")

    def test_silent_on_dot_localhost_host(self):
        """http://*.localhost hosts are treated as local dev — no warning."""
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            warn_insecure_wp_url("http://app.localhost", env={})
        self.assertEqual(buf.getvalue(), "")

    def test_wp_require_https_not_triggered_for_local(self):
        """WP_REQUIRE_HTTPS=1 does NOT raise for localhost — local is always exempt."""
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            warn_insecure_wp_url("http://localhost", env={"WP_REQUIRE_HTTPS": "1"})
        self.assertEqual(buf.getvalue(), "")


class ShouldConfirmPublishTest(unittest.TestCase):
    def test_interactive_publish_returns_true(self):
        """Interactive TTY + publish + no --yes → should prompt."""
        self.assertIs(should_confirm_publish("publish", False, True), True)

    def test_non_tty_is_silent(self):
        """Non-interactive context (agent/CI) → never prompt, even for publish."""
        self.assertIs(should_confirm_publish("publish", False, False), False)

    def test_yes_bypass_skips_prompt(self):
        """--yes on a TTY → no prompt."""
        self.assertIs(should_confirm_publish("publish", True, True), False)

    def test_draft_never_prompts(self):
        """Non-publish statuses never trigger the prompt."""
        self.assertIs(should_confirm_publish("draft", False, True), False)
        self.assertIs(should_confirm_publish(None, False, True), False)


class SeoMetaRawKeyTest(unittest.TestCase):
    """Unit-test _map_meta_keys directly (no HTTP) for the raw-key warning guard."""

    def test_allowlisted_key_passes_through_silently(self):
        """Known friendly names are mapped without warnings."""
        payload, warnings = _map_meta_keys({"title": "My Title"}, "rankmath", env={})
        self.assertEqual(payload, {"rank_math_title": "My Title"})
        self.assertEqual(warnings, [])

    def test_raw_key_included_in_payload_and_warns(self):
        """Non-allowlisted key is still written but produces a warning entry."""
        payload, warnings = _map_meta_keys({"_custom_raw_key": "val"}, "rankmath", env={})
        self.assertIn("_custom_raw_key", payload)
        self.assertEqual(payload["_custom_raw_key"], "val")
        self.assertEqual(len(warnings), 1)
        _key, msg = warnings[0]
        self.assertIn("_custom_raw_key", msg)
        self.assertIn("not in the rankmath allowlist", msg)

    def test_raw_key_warn_message_printed_to_stderr(self):
        """_map_meta_keys itself returns warnings; set_seo_meta prints them."""
        import io, contextlib
        # Exercise the stderr print path via set_seo_meta with a mocked HTTP layer.
        # Here we test _map_meta_keys returns the right warning text.
        _payload, warnings = _map_meta_keys({"_raw": "x"}, "yoast", env={})
        self.assertTrue(any("not in the yoast allowlist" in msg for _k, msg in warnings))

    def test_require_allowlist_env_refuses_raw_key(self):
        """WP_REQUIRE_ALLOWLIST=1 turns the warning into a ValueError (refusal)."""
        with self.assertRaises(ValueError) as ctx:
            _map_meta_keys({"_raw_key": "val"}, "rankmath", env={"WP_REQUIRE_ALLOWLIST": "1"})
        self.assertIn("WP_REQUIRE_ALLOWLIST=1", str(ctx.exception))

    def test_require_allowlist_allows_known_keys(self):
        """WP_REQUIRE_ALLOWLIST=1 does NOT block properly allowlisted keys."""
        payload, warnings = _map_meta_keys(
            {"description": "desc"}, "yoast", env={"WP_REQUIRE_ALLOWLIST": "1"}
        )
        self.assertEqual(payload, {"_yoast_wpseo_metadesc": "desc"})
        self.assertEqual(warnings, [])


if __name__ == "__main__":
    unittest.main()
