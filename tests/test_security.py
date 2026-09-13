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

    def test_wp_allow_http_names_the_host_it_permits(self):
        result, err = self._stderr(check_wp_url_scheme, "http://example.com",
                                   env={"WP_ALLOW_HTTP": "example.com"})
        self.assertIn("SECURITY WARNING", err)
        self.assertEqual(result, "http://example.com")  # url returned unchanged

    def test_a_blanket_value_is_refused(self):
        """WP_ALLOW_HTTP=1 used to mean "any host", so one variable set for one
        staging box silently covered every site the agent touched afterwards -
        production included (ClawHub audit of 3.9.4, AIG rated it High)."""
        for blanket in ("1", "true", "yes", "all", "*"):
            with self.assertRaises(SafetyError, msg=blanket) as caught:
                check_wp_url_scheme("http://example.com", env={"WP_ALLOW_HTTP": blanket})
            self.assertIn("name the host", str(caught.exception))

    def test_a_named_host_does_not_cover_a_different_one(self):
        with self.assertRaises(SafetyError):
            check_wp_url_scheme("http://prod.example.com",
                                env={"WP_ALLOW_HTTP": "staging.example.com"})

    def test_several_hosts_can_be_listed(self):
        _, err = self._stderr(check_wp_url_scheme, "http://b.example.com",
                              env={"WP_ALLOW_HTTP": "a.example.com, b.example.com"})
        self.assertIn("SECURITY WARNING", err)

    def test_the_refusal_names_the_host_to_allow(self):
        """The hint has to be actionable for THIS host, not a generic switch."""
        with self.assertRaises(SafetyError) as caught:
            check_wp_url_scheme("http://shop.example.com", env={})
        self.assertIn("WP_ALLOW_HTTP=shop.example.com", str(caught.exception))

    def test_wp_require_https_still_refuses(self):
        """An environment that pinned WP_REQUIRE_HTTPS=1 keeps its behaviour."""
        with self.assertRaises(SafetyError):
            check_wp_url_scheme("http://example.com", env={"WP_REQUIRE_HTTPS": "1"})

    def test_strictness_wins_over_a_legacy_blanket_value_too(self):
        """An upgraded environment may still carry WP_ALLOW_HTTP=1 alongside
        WP_REQUIRE_HTTPS=1. Telling that operator to write a hostname instead
        proposes a change that cannot work (Codex, PR #23)."""
        with self.assertRaises(SafetyError) as caught:
            check_wp_url_scheme("http://example.com",
                                env={"WP_ALLOW_HTTP": "1", "WP_REQUIRE_HTTPS": "1"})
        self.assertIn("WP_REQUIRE_HTTPS=1", str(caught.exception))
        self.assertNotIn("name the host", str(caught.exception))

    def test_explicit_strictness_beats_the_escape_hatch(self):
        with self.assertRaises(SafetyError) as caught:
            check_wp_url_scheme("http://example.com",
                                env={"WP_ALLOW_HTTP": "example.com", "WP_REQUIRE_HTTPS": "1"})
        # and it must not suggest the hatch, which would just fail again
        self.assertIn("WP_REQUIRE_HTTPS=1", str(caught.exception))
        self.assertNotIn("Set WP_ALLOW_HTTP", str(caught.exception))

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
        handler = security._ValidatingRedirectHandler(security.validate_probe_url)
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


class MediaRedirectTest(unittest.TestCase):
    """fetch_https_media validated the URL the caller supplied and then let
    urllib follow redirects unchecked, so a public HTTPS host could redirect to
    http://127.0.0.1/ and the download would follow - the SSRF that validator
    exists to prevent (ClawHub audit of 3.9.1: AIG and ClawScan both found it)."""

    def _redirect(self, to_url):
        handler = security._ValidatingRedirectHandler(security.validate_remote_url)
        req = urllib.request.Request("https://93.184.216.34/logo.png")
        return handler.redirect_request(req, None, 302, "Found", None, to_url)

    def test_redirect_to_loopback_is_refused(self):
        with self.assertRaises(SafetyError):
            self._redirect("https://127.0.0.1/secret.png")

    def test_redirect_to_link_local_metadata_is_refused(self):
        with self.assertRaises(SafetyError):
            self._redirect("https://169.254.169.254/latest/meta-data/")

    def test_redirect_downgrading_to_http_is_refused(self):
        """The media path is HTTPS-only, and a redirect must not launder that."""
        with self.assertRaises(SafetyError):
            self._redirect("http://93.184.216.34/logo.png")

    def test_redirect_to_another_public_https_host_is_followed(self):
        """A CDN handing off to another public host is ordinary and must work."""
        self.assertEqual(self._redirect("https://8.8.8.8/logo.png").full_url,
                         "https://8.8.8.8/logo.png")

    def test_fetch_https_media_uses_the_validating_opener(self):
        source = open(os.path.join(SCRIPTS, "security.py"), encoding="utf-8").read()
        body = source[source.index("def fetch_https_media"):]
        body = body[:body.index("return response, body")]
        self.assertIn("_MEDIA_OPENER.open(", body)
        self.assertNotIn("urllib.request.urlopen(", body)

    def test_security_itself_keeps_no_bare_urlopen(self):
        """The module that owns the redirect rules must not bypass them."""
        source = open(os.path.join(SCRIPTS, "security.py"), encoding="utf-8").read()
        code = [ln for ln in source.splitlines()
                if "urllib.request.urlopen(" in ln and not ln.strip().startswith("#")]
        self.assertEqual(code, [])


class RequestTimeoutTest(unittest.TestCase):
    """An unset timeout meant urllib's default: no timeout at all, so a hung or
    black-holed connection stalled the agent for ever (ClawHub audit of 3.9.1,
    [EA4] - availability hardening, not a vulnerability)."""

    def _timeout_passed(self, fn, opener_name):
        from unittest import mock as _mock
        seen = {}

        class FakeOpener:
            def open(self, req, timeout=None):
                seen["timeout"] = timeout
                return "response"

        with _mock.patch.object(security, opener_name, FakeOpener()):
            fn()
        return seen["timeout"]

    def test_authenticated_calls_are_bounded_by_default(self):
        req = urllib.request.Request("https://example.com/wp-json")
        self.assertEqual(
            self._timeout_passed(lambda: security.urlopen_authenticated(req), "_AUTH_SAFE_OPENER"),
            security.DEFAULT_REQUEST_TIMEOUT)

    def test_an_explicit_timeout_still_wins(self):
        req = urllib.request.Request("https://example.com/wp-json")
        self.assertEqual(
            self._timeout_passed(lambda: security.urlopen_authenticated(req, timeout=7),
                                 "_AUTH_SAFE_OPENER"),
            7)

    def test_probe_calls_are_bounded_by_default(self):
        req = urllib.request.Request("https://8.8.8.8/")
        self.assertEqual(
            self._timeout_passed(lambda: security.urlopen_probe(req), "_PROBE_OPENER"),
            security.DEFAULT_REQUEST_TIMEOUT)


class DnsPinningTest(unittest.TestCase):
    """The validator resolved the name and urlopen resolved it again, so an
    attacker controlling the name could answer a public address for the check
    and a private one for the connection (ClawHub audit of 3.9.2: AIG and
    ClawScan). Everything that enforces the rule now DIALS a validated address."""

    def _serve(self):
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer

        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"payload")
            def log_message(self, *a):
                pass

        srv = HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.shutdown)
        return f"http://127.0.0.1:{srv.server_address[1]}/", srv.server_address[1]

    def test_a_loopback_target_is_refused_at_connect_time(self):
        url, _ = self._serve()
        with self.assertRaises(SafetyError):
            security._PROBE_OPENER.open(url, timeout=5)

    def test_the_pinned_opener_still_transports_a_request(self):
        """The refusal above must come from the rule, not from a broken opener."""
        from unittest import mock as _mock
        url, _ = self._serve()
        with _mock.patch.object(security, "_assert_public_host", return_value=["127.0.0.1"]):
            response = security._PROBE_OPENER.open(url, timeout=5)
        self.assertEqual(response.status, 200)
        self.assertEqual(response.read(), b"payload")

    def test_the_connection_dials_the_validated_address(self):
        from unittest import mock as _mock
        _, port = self._serve()
        with _mock.patch.object(security, "_assert_public_host", return_value=["127.0.0.1"]):
            sock = security._connect_to_public_host("any.example", port, 5)
        self.addCleanup(sock.close)
        self.assertEqual(sock.getpeername()[0], "127.0.0.1")

    def test_a_refused_address_is_never_dialled(self):
        with self.assertRaises(SafetyError):
            security._connect_to_public_host("127.0.0.1", 9, 5)

    def test_validation_returns_the_addresses_it_approved(self):
        """Returning them is what lets the caller pin one instead of re-resolving."""
        self.assertEqual(security._public_addresses("8.8.8.8"), ["8.8.8.8"])

    def test_the_audit_no_longer_opens_its_own_socket(self):
        source = open(os.path.join(SCRIPTS, "site_audit.py"), encoding="utf-8").read()
        self.assertNotIn("socket.create_connection", source)
        self.assertIn("connect_public_tls(", source)

    def test_tls_verification_still_uses_the_hostname(self):
        """Pinning the address must not weaken certificate checking."""
        source = open(os.path.join(SCRIPTS, "security.py"), encoding="utf-8").read()
        body = source[source.index("class _PinnedHTTPSConnection"):]
        body = body[:body.index("class _PinnedHTTPHandler")]
        self.assertIn("server_hostname=self._tunnel_host or self.host", body)


class AuditBodyLimitTest(unittest.TestCase):
    """site_audit read response bodies with a bare read(), so any server it
    visited decided how much memory this process used."""

    def test_both_read_paths_are_bounded(self):
        source = open(os.path.join(SCRIPTS, "site_audit.py"), encoding="utf-8").read()
        self.assertNotIn("r.read().decode", source)
        self.assertNotIn("e.read().decode", source)
        self.assertIn("r.read(MAX_BODY_BYTES)", source)
        self.assertIn("e.read(MAX_BODY_BYTES)", source)

    def test_the_cap_is_applied_to_a_real_oversized_body(self):
        import io, site_audit as sa
        class Huge(io.RawIOBase):
            def read(self, n=-1):
                return b"x" * (n if n and n > 0 else 1024)
        capped = Huge().read(sa.MAX_BODY_BYTES)
        self.assertEqual(len(capped), sa.MAX_BODY_BYTES)


class ProxyBypassTest(unittest.TestCase):
    """urllib's default ProxyHandler rewrites the connection host to the proxy
    before the pinned handlers run, so the pin validated and dialled the PROXY
    while the real target travelled on in the absolute request URI - and the
    proxy resolved that target itself, with none of these rules applied. The
    pin was enforcing the address of the wrong host (Codex, PR #20)."""

    def _server(self, tag, body):
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer

        hits = []

        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                hits.append(self.path)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(body)
            def log_message(self, *a):
                pass

        srv = HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.addCleanup(srv.shutdown)
        return srv.server_address[1], hits

    def test_a_configured_proxy_is_ignored_by_default(self):
        from unittest import mock as _mock
        pport, proxy_hits = self._server("proxy", b"from-proxy")
        tport, target_hits = self._server("target", b"from-target")
        env = {"HTTP_PROXY": f"http://127.0.0.1:{pport}"}
        with _mock.patch.object(security, "_assert_public_host", return_value=["127.0.0.1"]):
            opener = security._address_enforcing_opener(security.validate_probe_url, env=env)
            body = opener.open(f"http://127.0.0.1:{tport}/x", timeout=5).read()
        self.assertEqual(body, b"from-target")
        self.assertEqual(proxy_hits, [])
        self.assertEqual(len(target_hits), 1)

    def test_wp_allow_proxy_restores_it(self):
        """urllib reads the proxy from the real environment (getproxies), so the
        opt-in has to be exercised against os.environ, not just the env mapping
        this function is handed - and no_proxy has to be cleared, or a host that
        exempts 127.0.0.1 (common in dev and CI) would bypass the local proxy and
        make this pass for the wrong reason."""
        from unittest import mock as _mock
        pport, proxy_hits = self._server("proxy", b"from-proxy")
        tport, _ = self._server("target", b"from-target")
        # Clear EVERY proxy variable before setting ours: urllib prefers the
        # lowercase http_proxy over the uppercase one, and no_proxy exempting
        # 127.0.0.1 would bypass the local proxy - either would make this test
        # pass for the wrong reason on a developer's machine or in CI.
        env = {name: "" for name in security.PROXY_ENV_VARS}
        env.update({"no_proxy": "", "NO_PROXY": "", "WP_ALLOW_PROXY": "1",
                    "http_proxy": f"http://127.0.0.1:{pport}",
                    "HTTP_PROXY": f"http://127.0.0.1:{pport}"})
        with _mock.patch.dict(os.environ, env, clear=False):
            with _mock.patch.object(security, "_assert_public_host", return_value=["127.0.0.1"]):
                opener = security._address_enforcing_opener(security.validate_probe_url, env=env)
                body = opener.open(f"http://127.0.0.1:{tport}/x", timeout=5).read()
        self.assertEqual(body, b"from-proxy")
        self.assertEqual(len(proxy_hits), 1)

    def test_the_opt_in_does_not_pin_the_proxy_itself(self):
        """An enterprise proxy is normally on a private address - the exact kind
        the pinned classes reject - so leaving them in place made the documented
        escape hatch fail for the only case it exists for (Codex, PR #20)."""
        names = [type(h).__name__ for h in
                 security._address_enforcing_opener(
                     security.validate_probe_url, env={"WP_ALLOW_PROXY": "1"}).handlers]
        self.assertNotIn("_PinnedHTTPConnection", names)
        self.assertNotIn("_PinnedHTTPHandler", names)
        self.assertNotIn("_PinnedHTTPSHandler", names)
        self.assertIn("_ValidatingRedirectHandler", names)

    def test_a_private_proxy_is_reachable_under_the_opt_in(self):
        """127.0.0.1 stands in for the private address a real proxy sits on."""
        from unittest import mock as _mock
        pport, proxy_hits = self._server("proxy", b"from-proxy")
        tport, _ = self._server("target", b"from-target")
        env = {name: "" for name in security.PROXY_ENV_VARS}
        env.update({"no_proxy": "", "NO_PROXY": "", "WP_ALLOW_PROXY": "1",
                    "http_proxy": f"http://127.0.0.1:{pport}",
                    "HTTP_PROXY": f"http://127.0.0.1:{pport}"})
        with _mock.patch.dict(os.environ, env, clear=False):
            opener = security._address_enforcing_opener(security.validate_probe_url, env=env)
            body = opener.open(f"http://93.184.216.34/x", timeout=5).read()
        self.assertEqual(body, b"from-proxy")
        self.assertEqual(len(proxy_hits), 1)

    def test_the_default_opener_registers_no_proxy_handler(self):
        """Passing an empty ProxyHandler is what stops build_opener installing the
        default one; an empty handler registers no proxy_open methods, so the
        absence of any ProxyHandler here IS the mechanism."""
        names = [type(h).__name__ for h in
                 security._address_enforcing_opener(security.validate_probe_url, env={}).handlers]
        self.assertNotIn("ProxyHandler", names)
        self.assertIn("_PinnedHTTPHandler", names)
        self.assertIn("_PinnedHTTPSHandler", names)

    def test_no_warning_when_allowed_but_no_proxy_is_configured(self):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            security._warn_proxy_in_use(env={"WP_ALLOW_PROXY": "1"})
        self.assertEqual(buf.getvalue(), "")


class ProxyWarningTest(unittest.TestCase):
    """The warning belongs to a fetch that claims address enforcement, not to
    importing the module: at import it fired twice (one opener each) in every
    CLI that imports security, including the ones that never use these openers
    (Codex, PR #20)."""

    def setUp(self):
        security._proxy_warning_emitted = False
        self.addCleanup(setattr, security, "_proxy_warning_emitted", False)

    def _stderr_of(self, fn):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            fn()
        return buf.getvalue()

    def test_building_an_opener_is_silent(self):
        env = {"WP_ALLOW_PROXY": "1", "HTTP_PROXY": "http://proxy.internal:3128"}
        out = self._stderr_of(
            lambda: security._address_enforcing_opener(security.validate_probe_url, env=env))
        self.assertEqual(out, "")

    def test_the_warning_fires_once_for_a_protected_fetch(self):
        env = {"WP_ALLOW_PROXY": "1", "HTTP_PROXY": "http://proxy.internal:3128"}
        first = self._stderr_of(lambda: security._warn_proxy_in_use(env=env))
        second = self._stderr_of(lambda: security._warn_proxy_in_use(env=env))
        self.assertIn("not enforced end to end", first)
        self.assertEqual(second, "")

    def test_silent_without_the_opt_in(self):
        self.assertEqual(
            self._stderr_of(lambda: security._warn_proxy_in_use(
                env={"HTTP_PROXY": "http://proxy.internal:3128"})),
            "")

    def test_the_fetch_paths_call_it(self):
        source = open(os.path.join(SCRIPTS, "security.py"), encoding="utf-8").read()
        for fn in ("def urlopen_probe", "def fetch_https_media"):
            body = source[source.index(fn):]
            body = body[:body.index("\n\n\n")]
            self.assertIn("_warn_proxy_in_use()", body, fn)


class WooProductSafetyTest(unittest.TestCase):
    """WooCommerce publishes a product whose status is omitted, so
    "woo_products --action create" put a priced, purchasable, indexable product
    straight onto a live storefront - with no draft default and no confirmation,
    while SKILL.md says to prefer drafts and confirm live writes (ClawHub audit
    of 3.9.3: AIG and ClawScan)."""

    def setUp(self):
        import woo_products
        self.woo = woo_products

    def _created(self, **kwargs):
        from unittest import mock as _mock
        with _mock.patch.object(self.woo, "make_wc_request",
                                side_effect=lambda *a, **k: k.get("data")):
            return self.woo.create_product("https://shop.example", "k", "s", "T", "9.99", **kwargs)

    def test_a_created_product_defaults_to_draft(self):
        self.assertEqual(self._created()["status"], "draft")

    def test_an_explicit_status_still_wins(self):
        self.assertEqual(self._created(status="publish")["status"], "publish")

    def test_an_explicit_draft_is_honoured(self):
        self.assertEqual(self._created(status="draft")["status"], "draft")

    def test_price_and_name_are_unchanged_by_the_default(self):
        data = self._created()
        self.assertEqual((data["name"], data["regular_price"], data["type"]),
                         ("T", "9.99", "simple"))

    def test_a_live_product_prompts_at_a_terminal(self):
        from unittest import mock as _mock
        with _mock.patch("builtins.input", return_value="PUBLISH"):
            self.woo.confirm_live_product("https://shop.example", "publish", False, "CREATE",
                                          is_tty=True)

    def test_a_refused_prompt_aborts(self):
        from unittest import mock as _mock
        with _mock.patch("builtins.input", return_value="no"):
            with self.assertRaises(SystemExit) as caught:
                self.woo.confirm_live_product("https://shop.example", "publish", False, "CREATE",
                                              is_tty=True)
        self.assertEqual(caught.exception.code, 1)

    def test_an_agent_or_ci_run_is_never_prompted(self):
        """No TTY means no prompt - this is a guard for a human at a terminal,
        not a gate an automation has to work around."""
        from unittest import mock as _mock
        with _mock.patch("builtins.input", side_effect=AssertionError("must not prompt")):
            self.woo.confirm_live_product("https://shop.example", "publish", False, "CREATE",
                                          is_tty=False)

    def test_a_draft_is_never_prompted(self):
        from unittest import mock as _mock
        with _mock.patch("builtins.input", side_effect=AssertionError("must not prompt")):
            self.woo.confirm_live_product("https://shop.example", "draft", False, "CREATE",
                                          is_tty=True)

    def test_the_cli_confirms_before_creating_and_before_publishing(self):
        source = open(os.path.join(SCRIPTS, "woo_products.py"), encoding="utf-8").read()
        self.assertIn('confirm_live_product(args.url, status, args.yes, "CREATE")', source)
        self.assertIn('confirm_live_product(args.url, args.status, args.yes, "PUBLISH")', source)


if __name__ == "__main__":
    unittest.main()
