"""A page that changes on every request teaches its reader to ignore the feed.

`sources.json` records why the VDI entry hashes the schema FILE and not the
page that links it: the page carries a per-request token. That is true of every
page on that host, so the guideline programme page -- the one place a draft
(Entwurf) would first appear -- could not be watched at all.

Measured before this existed: three fetches of
`vdi.de/richtlinien/programme-zu-vdi-richtlinien/vdi-2770` gave three hashes.
The bodies differed in 16 lines out of 456,524 bytes, and every one of them was
a TYPO3 form-state input or the whitespace around it -- machinery, not content.

So the hash is taken over the page with that machinery removed. What must not
happen is that the removal also hides a change worth reporting, which is what
the second test here is for.
"""
from __future__ import annotations

import importlib.util
import pathlib

_spec = importlib.util.spec_from_file_location(
    "watch", pathlib.Path(__file__).resolve().parents[1] / "watch.py")
watch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(watch)


#: The shape the token arrives in, taken from the page itself.
STATE = (b'<div><input type="hidden" name="tx_form_formframework[faq][__state]" '
         b'value="%s" /></div>')

PAGE = (b"<html><body><h1>VDI 2770</h1>\n"
        b"<p>Blatt 1 Richtlinie 01.04.2020</p>\n" + STATE + b"\n</body></html>")


def test_a_per_request_token_does_not_count_as_a_change():
    first = PAGE % b"TzozOToiVFlQTzNcQ01TXEZvcm1cRG9tYWluXFJ1bnRpbWVcRm9ybVN0YXRlIjoy"
    second = PAGE % b"TzozOToiVFlQTzNcQ01TXEZvcm1cRG9tYWluXFJ1bnRpbWVcRm9ybVN0YXRlIjox"
    assert first != second, "the fixture must actually differ, or this proves nothing"
    assert watch.stable_html(first) == watch.stable_html(second)


def test_a_change_in_what_the_page_says_is_still_a_change():
    """The whole point of the tower. A draft appearing is a line appearing."""
    before = PAGE % b"AAAA"
    after = before.replace(b"<p>Blatt 1 Richtlinie 01.04.2020</p>",
                           b"<p>Blatt 1 Richtlinie 01.04.2020</p>\n"
                           b"<p>Blatt 2 Entwurf 09.2026</p>")
    assert watch.stable_html(before) != watch.stable_html(after)


def test_the_honeypot_field_is_machinery_too():
    """The same form renders a decoy input whose id and name are randomised."""
    decoy = (b'<input autocomplete="%s" aria-hidden="true" id="faq-%s" '
             b'type="text" name="tx_form_formframework[faq][decoy]" />')
    a = PAGE % b"AAAA" + decoy % (b"xs6Qj4ktbl1GM", b"xs6Qj4ktbl1GM")
    b = PAGE % b"AAAA" + decoy % (b"zzzzzzzzzzzzz", b"zzzzzzzzzzzzz")
    assert a != b
    assert watch.stable_html(a) == watch.stable_html(b)


def test_what_a_page_says_survives_the_normalisation():
    """Collapsing whitespace must not collapse words into each other."""
    spaced = b"<html><body><p>Blatt 1</p>\n\n<p>Blatt 2</p></body></html>"
    assert b"Blatt 1" in watch.stable_html(spaced)
    assert b"Blatt 2" in watch.stable_html(spaced)
    assert watch.stable_html(spaced) != watch.stable_html(
        spaced.replace(b"Blatt 2", b"Blatt 3"))
