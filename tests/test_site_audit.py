import os, sys, unittest

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "wordpress-api-pro", "scripts")
sys.path.insert(0, os.path.abspath(SCRIPTS))

import site_audit as sa  # noqa: E402


class CmsTest(unittest.TestCase):
    def test_detects_wordpress_and_version_from_generator(self):
        html = '<meta name="generator" content="WordPress 6.5.2" />'
        out = sa.parse_cms(html, {})
        self.assertTrue(out["is_wordpress"])
        self.assertEqual(out["wp_version"], "6.5.2")

    def test_detects_wp_from_wp_content_when_no_generator(self):
        html = '<link href="/wp-content/themes/x/style.css">'
        out = sa.parse_cms(html, {})
        self.assertTrue(out["is_wordpress"])

    def test_php_version_from_x_powered_by(self):
        out = sa.parse_cms("", {"X-Powered-By": "PHP/8.1.27"})
        self.assertEqual(out["php_version"], "8.1.27")

    def test_non_wp(self):
        self.assertFalse(sa.parse_cms("<html>nothing</html>", {})["is_wordpress"])


class SeoTest(unittest.TestCase):
    def test_extracts_title_and_description_and_h1_and_canonical(self):
        html = ('<title>Acme — Home</title>'
                '<meta name="description" content="We build things.">'
                '<link rel="canonical" href="https://acme/"><h1>Hi</h1>')
        out = sa.parse_seo(html)
        self.assertEqual(out["title"], "Acme — Home")
        self.assertEqual(out["meta_description"], "We build things.")
        self.assertEqual(out["h1_count"], 1)
        self.assertTrue(out["has_canonical"])

    def test_missing_fields(self):
        out = sa.parse_seo("<html></html>")
        self.assertIsNone(out["title"])
        self.assertIsNone(out["meta_description"])
        self.assertEqual(out["h1_count"], 0)
        self.assertFalse(out["has_canonical"])


class HeadersTest(unittest.TestCase):
    def test_present_and_missing_security_headers(self):
        out = sa.analyze_headers({
            "Strict-Transport-Security": "max-age=63072000",
            "X-Content-Type-Options": "nosniff",
        })
        self.assertIn("Strict-Transport-Security", out["present"])
        self.assertIn("Content-Security-Policy", out["missing"])
        self.assertIn("X-Frame-Options", out["missing"])


class SslTest(unittest.TestCase):
    def test_days_left_positive(self):
        now = sa._parse_cert_time("Jan  1 00:00:00 2026 GMT")
        days = sa.ssl_days_left("Mar  2 00:00:00 2026 GMT", now=now)
        self.assertEqual(days, 60)


class PageSpeedTest(unittest.TestCase):
    def test_grade(self):
        self.assertEqual(sa.grade_pagespeed(0.95), "pass")
        self.assertEqual(sa.grade_pagespeed(0.80), "warn")
        self.assertEqual(sa.grade_pagespeed(0.50), "fail")


if __name__ == "__main__":
    unittest.main()
