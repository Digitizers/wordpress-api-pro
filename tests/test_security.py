import os, sys, unittest

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "wordpress-api-pro", "scripts")
sys.path.insert(0, os.path.abspath(SCRIPTS))

from security import SafetyError, warn_insecure_wp_url  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
