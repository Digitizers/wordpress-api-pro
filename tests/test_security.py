import os, sys, unittest
import urllib.request

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "wordpress-api-pro", "scripts")
sys.path.insert(0, os.path.abspath(SCRIPTS))

import security  # noqa: E402
from security import (  # noqa: E402
    SafetyError, check_wp_url_scheme, require_secure_wp_url, same_origin,
    should_confirm_publish, validate_probe_host,
    validate_probe_url, validate_remote_url,
)
from seo_meta import _map_meta_keys  # noqa: E402


class WpUrlSchemeTest(unittest.TestCase):
    """Plaintext http:// to a public host is refused as of 3.9.0; it used to
    print a warning and continue, which sent the app password in the clear."""

    def _stderr(self, fn, *args, **kwargs):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            result = fn(*args, **kwargs)
        return result, buf.getvalue()

    def test_http_on_a_public_host_is_refused(self):
        with self.assertRaises(SafetyError):
            check_wp_url_scheme("http://example.com", env={})

    def test_wp_allow_http_downgrades_the_refusal_to_a_warning(self):
        result, err = self._stderr(check_wp_url_scheme, "http://example.com",
                                   env={"WP_ALLOW_HTTP": "1"})
        self.assertIn("SECURITY WARNING", err)
        self.assertEqual(result, "http://example.com")  # url returned unchanged

    def test_wp_require_https_still_refuses(self):
        """An environment that pinned WP_REQUIRE_HTTPS=1 keeps its behaviour."""
        with self.assertRaises(SafetyError):
            check_wp_url_scheme("http://example.com", env={"WP_REQUIRE_HTTPS": "1"})

    def test_explicit_strictness_beats_the_escape_hatch(self):
        with self.assertRaises(SafetyError):
            check_wp_url_scheme("http://example.com",
                                env={"WP_ALLOW_HTTP": "1", "WP_REQUIRE_HTTPS": "1"})

    def test_https_is_silent(self):
        result, err = self._stderr(check_wp_url_scheme, "https://example.com", env={})
        self.assertEqual(err, "")
        self.assertEqual(result, "https://example.com")

    def test_local_dev_hosts_stay_exempt(self):
        """localhost and the .local/.test/.localhost suffixes never warn or refuse -
        a local site has no wire for a credential to leak on."""
        for url in ("http://localhost:8080", "http://site.local",
                    "http://mysite.test", "http://app.localhost"):
            result, err = self._stderr(check_wp_url_scheme, url, env={})
            self.assertEqual(err, "", url)
            self.assertEqual(result, url)

    def test_local_is_exempt_even_under_wp_require_https(self):
        _, err = self._stderr(check_wp_url_scheme, "http://localhost",
                              env={"WP_REQUIRE_HTTPS": "1"})
        self.assertEqual(err, "")


class RequireSecureWpUrlTest(unittest.TestCase):
    """The CLI boundary: a refusal must read as a safety error with exit 2,
    not as an uncaught traceback."""

    def test_refusal_exits_two(self):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            with self.assertRaises(SystemExit) as caught:
                require_secure_wp_url("http://example.com", env={})
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("Safety error", buf.getvalue())

    def test_https_passes_through(self):
        self.assertEqual(require_secure_wp_url("https://example.com", env={}),
                         "https://example.com")


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

    def test_raw_key_is_refused_by_default(self):
        """A key outside the allowlist used to be written as raw postmeta with a
        warning, so a typo'd friendly name silently created a junk meta row."""
        with self.assertRaises(ValueError) as ctx:
            _map_meta_keys({"_custom_raw_key": "val"}, "rankmath", env={})
        self.assertIn("_custom_raw_key", str(ctx.exception))
        self.assertIn("WP_ALLOW_RAW_META=1", str(ctx.exception))

    def test_wp_allow_raw_meta_restores_the_write_with_a_warning(self):
        payload, warnings = _map_meta_keys({"_custom_raw_key": "val"}, "rankmath",
                                           env={"WP_ALLOW_RAW_META": "1"})
        self.assertEqual(payload["_custom_raw_key"], "val")
        self.assertEqual(len(warnings), 1)
        _key, msg = warnings[0]
        self.assertIn("_custom_raw_key", msg)
        self.assertIn("not in the rankmath allowlist", msg)

    def test_require_allowlist_env_still_refuses_raw_key(self):
        with self.assertRaises(ValueError):
            _map_meta_keys({"_raw_key": "val"}, "rankmath", env={"WP_REQUIRE_ALLOWLIST": "1"})

    def test_explicit_strictness_beats_the_escape_hatch(self):
        with self.assertRaises(ValueError):
            _map_meta_keys({"_raw_key": "val"}, "yoast",
                           env={"WP_ALLOW_RAW_META": "1", "WP_REQUIRE_ALLOWLIST": "1"})

    def test_require_allowlist_allows_known_keys(self):
        """WP_REQUIRE_ALLOWLIST=1 does NOT block properly allowlisted keys."""
        payload, warnings = _map_meta_keys(
            {"description": "desc"}, "yoast", env={"WP_REQUIRE_ALLOWLIST": "1"}
        )
        self.assertEqual(payload, {"_yoast_wpseo_metadesc": "desc"})
        self.assertEqual(warnings, [])


class SameOriginTest(unittest.TestCase):
    def test_identical_origin(self):
        self.assertTrue(same_origin("https://site.com/a", "https://site.com/b"))

    def test_explicit_default_port_is_the_same_origin(self):
        """https://site.com and https://site.com:443 are one origin."""
        self.assertTrue(same_origin("https://site.com/a", "https://site.com:443/b"))

    def test_host_scheme_and_port_each_break_the_origin(self):
        self.assertFalse(same_origin("https://site.com/a", "https://evil.com/a"))
        self.assertFalse(same_origin("https://site.com/a", "http://site.com/a"))
        self.assertFalse(same_origin("https://site.com/a", "https://site.com:8443/a"))

    def test_host_comparison_is_case_insensitive(self):
        self.assertTrue(same_origin("https://SITE.com/a", "https://site.COM/b"))


class AuthStrippingRedirectTest(unittest.TestCase):
    """CPython's HTTPRedirectHandler copies every header except
    content-length/content-type onto the redirected request, so a redirect to
    another host carries Authorization with it. The handler must drop it."""

    def _redirect(self, from_url, to_url):
        handler = security._AuthStrippingRedirectHandler()
        req = urllib.request.Request(from_url, headers={"Authorization": "Basic c2VjcmV0"})
        return handler.redirect_request(req, None, 302, "Found", None, to_url)

    def test_credentials_are_dropped_when_the_host_changes(self):
        new = self._redirect("https://site.com/wp-json", "https://evil.com/collect")
        self.assertIsNone(new.get_header("Authorization"))

    def test_credentials_survive_a_same_origin_redirect(self):
        """WordPress canonical-URL redirects are same-origin and must keep working."""
        new = self._redirect("https://site.com/wp-json", "https://site.com/wp-json/")
        self.assertEqual(new.get_header("Authorization"), "Basic c2VjcmV0")

    def test_credentials_are_dropped_on_an_https_to_http_downgrade(self):
        new = self._redirect("https://site.com/wp-json", "http://site.com/wp-json")
        self.assertIsNone(new.get_header("Authorization"))

    def test_header_name_casing_does_not_hide_the_credential(self):
        handler = security._AuthStrippingRedirectHandler()
        req = urllib.request.Request("https://site.com/x")
        req.add_unredirected_header("authorization", "Basic c2VjcmV0")
        new = handler.redirect_request(req, None, 302, "Found", None, "https://evil.com/y")
        self.assertNotIn("authorization",
                         [k.lower() for k in list(new.headers) + list(new.unredirected_hdrs)])


class ValidateProbeUrlTest(unittest.TestCase):
    """The site audit must reach http:// (detecting a missing HTTPS redirect is
    one of its own checks) without becoming an SSRF primitive. Every case uses
    an IP literal, so no test resolves a name over the network."""

    def test_http_is_permitted_for_a_public_address(self):
        self.assertEqual(validate_probe_url("http://93.184.216.34/"), "http://93.184.216.34/")

    def test_loopback_is_refused(self):
        with self.assertRaises(SafetyError):
            validate_probe_url("http://127.0.0.1/wp-admin")

    def test_link_local_metadata_address_is_refused(self):
        with self.assertRaises(SafetyError):
            validate_probe_url("http://169.254.169.254/latest/meta-data/")

    def test_private_address_is_refused(self):
        with self.assertRaises(SafetyError):
            validate_probe_url("http://192.168.1.1/")

    def test_non_http_scheme_is_refused(self):
        with self.assertRaises(SafetyError):
            validate_probe_url("file:///etc/passwd")

    def test_missing_hostname_is_refused(self):
        with self.assertRaises(SafetyError):
            validate_probe_url("http:///wp-json")


class ValidateRemoteUrlStillHttpsOnlyTest(unittest.TestCase):
    """validate_probe_url is a separate function precisely so the media
    download path keeps its HTTPS-only guarantee."""

    def test_http_media_url_is_still_refused(self):
        with self.assertRaises(SafetyError):
            validate_remote_url("http://93.184.216.34/logo.png")


class ProbeHostTest(unittest.TestCase):
    def test_public_literal_passes(self):
        self.assertEqual(validate_probe_host("93.184.216.34"), "93.184.216.34")

    def test_loopback_is_refused(self):
        with self.assertRaises(SafetyError):
            validate_probe_host("127.0.0.1")

    def test_empty_host_is_refused(self):
        with self.assertRaises(SafetyError):
            validate_probe_host("")


class ProbeRedirectTest(unittest.TestCase):
    """Validating only the caller's URL is not enough: a public site is free to
    answer 302 http://169.254.169.254/, and urlopen would follow it."""

    def _redirect(self, to_url):
        handler = security._PublicHostRedirectHandler()
        req = urllib.request.Request("http://93.184.216.34/")
        return handler.redirect_request(req, None, 302, "Found", None, to_url)

    def test_redirect_to_an_internal_address_is_refused(self):
        with self.assertRaises(SafetyError):
            self._redirect("http://169.254.169.254/latest/meta-data/")

    def test_redirect_to_a_public_address_is_followed(self):
        self.assertEqual(self._redirect("https://93.184.216.34/x").full_url,
                         "https://93.184.216.34/x")

    def test_an_unresolvable_name_is_not_reported_as_a_refusal(self):
        """A typo'd domain is unreachable, not an attempt to reach internal
        infrastructure - site_audit has to keep reporting it as a site that did
        not respond, so it gets its own SafetyError subclass."""
        import socket as _socket
        from unittest import mock as _mock
        with _mock.patch.object(security, "_hostname_addresses",
                                side_effect=_socket.gaierror("nodename nor servname provided")):
            with self.assertRaises(security.HostResolutionError):
                validate_probe_url("https://nonexistent.invalid/")

    def test_urlopen_probe_validates_before_opening(self):
        """No socket is created: the refusal happens before the opener runs."""
        with self.assertRaises(SafetyError):
            security.urlopen_probe(urllib.request.Request("http://127.0.0.1/"))


class NoBareAuthenticatedUrlopenTest(unittest.TestCase):
    """Static invariant. A script that sends an Authorization header must open
    it through urlopen_authenticated; a bare urllib.request.urlopen there is
    the redirect credential leak this release fixed."""

    def _authenticated_scripts(self):
        for name in sorted(os.listdir(SCRIPTS)):
            if not name.endswith(".py") or name == "security.py":
                continue
            source = open(os.path.join(SCRIPTS, name), encoding="utf-8").read()
            if "Authorization" in source:
                yield name, source

    def test_every_authenticated_cli_checks_the_url_scheme(self):
        """describe_cpt sent Basic credentials over plaintext http:// because its
        main() never called the guard, so the 3.9.0 default did not apply to it
        (Codex, PR #17). Nothing else may be added with that shape."""
        offenders = [name for name, source in self._authenticated_scripts()
                     if "require_secure_wp_url(" not in source]
        self.assertEqual(offenders, [])

    def test_no_authenticated_script_calls_urlopen_directly(self):
        offenders = [name for name, source in self._authenticated_scripts()
                     if "urllib.request.urlopen(" in source]
        self.assertEqual(offenders, [])


class DatasetPathTest(unittest.TestCase):
    """seed_content read its --dataset with a bare open(), so it would read any
    path the agent could name. It goes through validate_local_file now."""

    def test_seed_content_validates_its_dataset_path(self):
        source = open(os.path.join(SCRIPTS, "seed_content.py"), encoding="utf-8").read()
        self.assertIn("validate_local_file(a.dataset", source)
        self.assertNotIn("open(a.dataset)", source)

    def test_validate_local_file_refuses_a_path_outside_the_allowed_roots(self):
        import tempfile
        with tempfile.TemporaryDirectory() as inside, tempfile.TemporaryDirectory() as outside:
            good = os.path.join(inside, "data.json")
            bad = os.path.join(outside, "data.json")
            for path in (good, bad):
                open(path, "w", encoding="utf-8").write("[]")
            env_root = inside
            old = os.environ.get("WP_ALLOWED_FILE_ROOTS")
            os.environ["WP_ALLOWED_FILE_ROOTS"] = env_root
            try:
                self.assertEqual(str(security.validate_local_file(good)),
                                 str(os.path.realpath(good)))
                with self.assertRaises(SafetyError):
                    security.validate_local_file(bad)
            finally:
                if old is None:
                    os.environ.pop("WP_ALLOWED_FILE_ROOTS")
                else:
                    os.environ["WP_ALLOWED_FILE_ROOTS"] = old


if __name__ == "__main__":
    unittest.main()


class AuditUnreachableVsRefusedTest(unittest.TestCase):
    """audit() must keep its two outcomes distinct: a site that did not respond,
    and an address the safety rule refused."""

    def _audit(self, error):
        from unittest import mock as _mock
        import site_audit as sa
        with _mock.patch.object(sa, "_get", side_effect=error):
            return sa.audit("https://example.com")

    def test_unresolvable_host_reports_unreachable(self):
        result = self._audit(security.HostResolutionError("Could not resolve host"))
        self.assertFalse(result["reachable"])
        checks = [f["check"] for f in result["findings"]]
        self.assertIn("reachable", checks)
        self.assertNotIn("blocked", checks)

    def test_refused_address_reports_blocked(self):
        result = self._audit(SafetyError("Refusing host; resolved to unsafe address"))
        self.assertFalse(result["reachable"])
        self.assertEqual([f["check"] for f in result["findings"]], ["blocked"])


class NonGlobalAddressTest(unittest.TestCase):
    """Enumerating non-public categories misses whatever the enumeration forgot.
    It forgot RFC 6598 shared address space: 100.64.0.1 is none of
    private/loopback/link-local/multicast/reserved/unspecified to Python, and is
    routable on every network that runs CGNAT (Codex, PR #17)."""

    def test_cgnat_shared_address_space_is_refused(self):
        with self.assertRaises(SafetyError):
            validate_probe_url("http://100.64.0.1/")

    def test_benchmarking_range_is_refused(self):
        with self.assertRaises(SafetyError):
            validate_probe_url("http://198.18.0.1/")

    def test_nat64_prefix_is_refused_despite_being_global(self):
        """64:ff9b::/96 reports is_global True, so the named flags stay as the
        deny half rather than being replaced by the allowlist."""
        with self.assertRaises(SafetyError):
            validate_probe_url("http://[64:ff9b::1]/")

    def test_an_ordinary_public_address_still_passes(self):
        self.assertEqual(validate_probe_url("http://8.8.8.8/"), "http://8.8.8.8/")
        self.assertEqual(validate_probe_host("93.184.216.34"), "93.184.216.34")


class BatchPreflightTest(unittest.TestCase):
    """Turning the http warning into a refusal made it abort mid-loop: a batch
    with an https site followed by an http one modified the first site, exited
    on the second, and printed no summary (Codex, PR #17)."""

    TARGETS = [("good", "https://a.example.com"), ("bad", "http://b.example.com"),
               ("also-bad", "http://c.example.com"), ("local", "http://site.test")]

    def test_every_offender_is_reported_not_just_the_first(self):
        problems = security.check_wp_url_schemes(self.TARGETS, env={})
        self.assertEqual([label for label, _ in problems], ["bad", "also-bad"])

    def test_a_clean_batch_has_no_problems(self):
        self.assertEqual(
            security.check_wp_url_schemes([("a", "https://a.example.com"),
                                           ("b", "http://localhost:8080")], env={}),
            [])

    def test_require_exits_two_and_names_each_site(self):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            with self.assertRaises(SystemExit) as caught:
                security.require_secure_wp_urls(self.TARGETS, env={})
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("bad:", buf.getvalue())
        self.assertIn("also-bad:", buf.getvalue())

    def test_batch_update_preflights_before_the_write_loop(self):
        source = open(os.path.join(SCRIPTS, "batch_update.py"), encoding="utf-8").read()
        preflight = source.index("require_secure_wp_urls(selected)")
        loop = source.index("for site_name in site_names:")
        self.assertLess(preflight, loop)

    def test_wp_cli_preflights_the_whole_group(self):
        source = open(os.path.join(SCRIPTS, "wp_cli.py"), encoding="utf-8").read()
        preflight = source.index("require_secure_wp_urls(")
        loop = source.index("for site_name in site_data:")
        self.assertLess(preflight, loop)


class AuditSummaryTest(unittest.TestCase):
    """--summary discarded every finding when reachable was false, so a refused
    address was reported as a flat "Site unreachable." - a deliberate safety
    refusal misreported as a connectivity failure, with the address hidden
    (Codex, PR #17)."""

    def _summary(self, error):
        from unittest import mock as _mock
        import site_audit as sa
        with _mock.patch.object(sa, "_get", side_effect=error):
            return sa._summary(sa.audit("https://example.com"))

    def test_a_blocked_address_is_named_in_the_summary(self):
        text = self._summary(SafetyError("Refusing host; resolved to unsafe address 10.0.0.5"))
        self.assertIn("blocked", text)
        self.assertIn("10.0.0.5", text)
        self.assertNotIn("Site unreachable.", text)

    def test_an_unresolvable_host_still_reads_as_unreachable(self):
        text = self._summary(security.HostResolutionError("Could not resolve host 'nope.invalid'"))
        self.assertIn("site did not respond", text)

    def test_a_result_with_no_findings_keeps_the_old_line(self):
        import site_audit as sa
        self.assertIn("Site unreachable.",
                      sa._summary({"url": "https://x.example", "reachable": False, "findings": []}))


class ErrorResultExitTest(unittest.TestCase):
    """acf_fields, jetengine_fields and seo_meta report a failed write as
    {"error": ...} rather than by raising, so the CLI printed the error and
    still exited 0 - read as success by CI and by an agent. 3.9.0 fixed
    seo_meta only; the other two carried the same shape."""

    def test_an_error_result_exits_one(self):
        with self.assertRaises(SystemExit) as caught:
            security.exit_on_error_result(security.error_result("HTTP 403", details={}))
        self.assertEqual(caught.exception.code, 1)

    def test_a_successful_result_does_not_exit(self):
        self.assertIsNone(security.exit_on_error_result({"id": 12, "status": "draft"}))

    def test_a_site_field_named_error_is_data_not_a_failure(self):
        """The ACF and JetEngine getters return the SITE's own field dictionary,
        so a custom field named "error" - or an explicit --field error lookup -
        is ordinary data. Key presence cannot identify a failure (Codex, PR #18)."""
        self.assertIsNone(security.exit_on_error_result({"error": "yes, a real field value"}))
        self.assertIsNone(security.exit_on_error_result({"error": {"nested": True}}))

    def test_a_non_dict_result_is_ignored(self):
        self.assertIsNone(security.exit_on_error_result(["a", "list"]))

    def test_the_envelope_serialises_like_a_plain_dict(self):
        """It is a dict subclass so the CLI's JSON output is unchanged."""
        import json as _json
        self.assertEqual(_json.loads(_json.dumps(security.error_result("boom", details={"a": 1}))),
                         {"error": "boom", "details": {"a": 1}})

    def test_no_script_builds_a_bare_error_dict(self):
        """A bare {"error": ...} return is indistinguishable from site data;
        failures go through error_result so the type carries the meaning."""
        offenders = []
        for name in sorted(os.listdir(SCRIPTS)):
            if not name.endswith(".py") or name == "security.py":
                continue
            source = open(os.path.join(SCRIPTS, name), encoding="utf-8").read()
            if 'return {"error"' in source:
                offenders.append(name)
        self.assertEqual(offenders, [])

    def test_every_script_returning_a_failure_checks_it(self):
        offenders = []
        for name in sorted(os.listdir(SCRIPTS)):
            if not name.endswith(".py") or name == "security.py":
                continue
            source = open(os.path.join(SCRIPTS, name), encoding="utf-8").read()
            if "error_result(" not in source:
                continue
            if "exit_on_error_result(" not in source:
                offenders.append(name)
        self.assertEqual(offenders, [])
