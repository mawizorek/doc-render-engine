"""The `!!! qr "name"` directive -- a STATIC QR code built at publish time.

    !!! form "incident-report"    embeds the form
    !!! qr "incident-report"      encodes its address

🔴 THE ARGUMENT FOR EVERY DECISION HERE LIVES IN `specs/qr-codes.md` (BUILD 6),
AND THIS DOCSTRING DELIBERATELY DOES NOT REPEAT IT. It held a summary of that
spec until 2026-08-21 and the file reached 28,490 B against a ~22 KB ceiling --
not because it had a seam, but because it was a SECOND CLAIMANT on a document
that already existed. That is this repo's most-retired defect wearing a docstring,
and trimming it was the fix rather than splitting the module.

⚠️ WHAT STAYS HERE IS ONLY WHAT AN EDITOR OF *THIS FILE* CANNOT SAFELY NOT KNOW:
the reason each encoder argument is pinned (they are three lines from the call),
the reason the write happens where it does, and what this module borrows.

STATE: steps 2 and 6 built (a `links:` name; a `forms:` slot on the same page).
NOT BUILT: `@page-id` (step 4), the report inventory (step 3), `display=`/`print=`
(step 5). 🚫 An unbuilt option is REFUSED with its own report line, never ignored.

=============================================================================
🔴 EVERY ENCODER ARGUMENT IS PINNED, AND NONE OF THEM IS SEGNO'S DEFAULT
=============================================================================
Byte-identical GENERATION is not guaranteed by ISO/IEC 18004 -- only scanning is.
So determinism is constructed, and each pin has a failure it prevents:

  boost_error=False  DEFAULT IS `True`. Left on, segno RAISES the error level
                     whenever the version has spare capacity, so one extra
                     character in the payload silently changes the matrix.
                     Verified against segno's API docs 2026-08-21.
  make_qr()          NOT `make()`, whose `micro=None` default may return a MICRO
                     QR -- different symbology, 2-module quiet zone, materially
                     worse reader support. It would scan on the author's phone
                     and fail on somebody else's.
  error=_ECC         segno's default (`None`) is level L, ~7% recovery. Not for
                     paper, so the level is always explicit.
  mode="byte"        alphanumeric is denser but UPPERCASE-ONLY and a URL path is
                     case-sensitive. Pinned so an all-caps payload cannot switch
                     modes and change the matrix.
  encoding="utf-8"   otherwise chosen FROM THE PAYLOAD (8859-1, else UTF-8).
  border=4           the quiet zone is PART OF THE SYMBOL. Baked in, where no
                     stylesheet can crop it. Crop it and the code stops scanning.

⚠️ A MAJOR SEGNO BUMP MAY LEGALLY CHANGE THIS OUTPUT. Hence the upper bound in
`requirements.txt`.

=============================================================================
⭐ THE PNG IS WRITTEN AT `on_post_build`, AND THE TIMING IS THE WHOLE DESIGN
=============================================================================
A `!!! qr` lives in the page BODY, and `on_files` has already run by the time any
body is read -- `assets.py` ruled on exactly this shape for `!!! data`. And a
`data:` URI, which would need no file at all, is DEAD IN A PDF (viewers refuse
non-http(s) targets), which is the medium this feature exists for.

⭐ So the href is DERIVED, not discovered: the filename is a content hash of the
pinned recipe plus the payload, which can be written into the page before the file
exists. Consequences, all of them the point: nothing enters `images.INDEX` (which
refuses duplicate stems and would break a real image's reference); no stray `!`;
and identical inputs give an identical path, so a rebuild produces no diff.

⚠️ These files do NOT carry `assets.py`'s content fingerprint -- the hash IS the
filename. 🚫 Do not "fix" that by routing them through `_stamped()`; it puts them
back into the `on_files` timing problem above.

=============================================================================
⚠️ WHAT THIS MODULE BORROWS, AND THE PRICE
=============================================================================
`urllinks._entry`, `._page_links`, `._site_links`, `._bad_scheme` and
`forms._entry` are called rather than reimplemented, because a second copy of the
two-spellings entry parser or the scheme allow-list is a second claimant on one
truth. 🔴 THE PRICE IS THAT THOSE FIVE PRIVATE NAMES ARE NOW INTERFACE: renaming
one breaks this module. If that becomes uncomfortable, promote them in their own
module -- do not copy them here.

🔴 AND THE LIMIT, WHICH IS WORSE HERE THAN ANYWHERE ELSE IN THE ENGINE: an
external URL is not verifiable at build time (`urllinks` says so first), and a QR
makes that unverifiable thing UNREADABLE BY A HUMAN TOO. Nobody proofreads a QR;
a wrong one renders as a perfect, confident square. The report inventory (step 3)
is the answer and does not exist yet.
"""

from __future__ import annotations

import hashlib
import html
import re
from pathlib import Path

from . import forms, state, urllinks
from .util import relative_url, sub_outside_code

#: `!!! qr "name"` plus optional trailing `key=value` pairs, alone on its line.
#:
#: Deliberately the same shape as `!!! form "slot"` (docrender/forms.py) so the
#: body vocabulary stays one pattern rather than two spellings of one idea -- and
#: since step 6 the resemblance is more than cosmetic: both directives can name
#: the SAME slot on one page. The difference is the trailing group: forms.py
#: anchors straight to end-of-line, and that anchor is where options go.
#:
#: 🚫 OPTIONS ARE BARE `key=value`, NOT an attr_list brace block. `markers.py`
#: hands an unrecognised brace block back untouched while `cells.plain()` strips
#: EVERY brace block -- BUILD 1's spec names that disagreement as a live defect --
#: and BUILD 1's `clean.py` is built to remove our own declared vocabulary, so a
#: QR option in braces is a QR option a future stripper deletes.
_QR = re.compile(r'(?m)^[ \t]*!!![ \t]+qr[ \t]+"([^"\n]+)"(?P<opts>[^\n]*)$')

_OPT = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=(\S+)")

#: Exactly two keys are legal, so anything else is an ERROR rather than a
#: judgement call. Both are REFUSED in `_html_for` until step 5 -- and
#: recognised-but-unbuilt is a different report line from mistyped, which is the
#: whole reason this tuple exists before the feature does.
_KEYS = ("display", "print")

#: 🔴 ONE ENGINE CONSTANT, NOT CONFIG AND NOT A LINE OPTION (Michael: "globally
#: for all builds in all renderer apps" -- `site.yml` would be per site).
#:
#: ⚠️ `Q` (~25%) IS A STARTING POINT AWAITING ONE MEASUREMENT, and it cannot be
#: reasoned to because EC IS NOT MONOTONIC AT A FIXED PHYSICAL SIZE: more
#: correction -> more codewords -> higher version -> each module physically
#: SMALLER on the same square, and module size is what a camera resolves. `H` in a
#: 25mm square can scan WORSE than `Q`.
#: ⭐ Safe to change at any time: the PAYLOAD is unchanged, so every code already
#: printed keeps scanning. The reverse of `base_url`, which is unforgiving.
#: 🔴 The legibility floor for safety-critical print is Hazard Hawthorne's call
#: (specs/print-identity.md §3f). A safety QR that will not scan is a safety
#: defect, not a styling one.
_ECC = "Q"

#: Pixels per module in the downloaded PNG. ⚠️ It decides whether the download is
#: usable at poster scale, which is the one property a person notices -- and it is
#: part of the determinism contract, since a change moves the bytes, the hash and
#: therefore the filename.
_SCALE = 8

#: The quiet zone, in modules. Part of the symbol. See the docstring.
_BORDER = 4

#: Where the images land in the built site. 🚫 NOT `assets/`, which is
#: `assets.py`'s planned-and-fingerprinted namespace and would invite somebody to
#: route these through `_stamped()`.
_DIR = "qr"

#: `site-relative path -> png bytes`, filled during page rendering and drained at
#: `on_post_build`. A module-level collector on the `images.INDEX` precedent.
#:
#: ⚠️ CLEARED AT THE START OF EVERY BUILD, not at import: `mkdocs serve` rebuilds
#: IN-PROCESS, so a dict that only grows would carry a deleted page's code into
#: the next build and write a file nothing references.
PENDING: dict[str, bytes] = {}


def _dead(label: str, reason: str) -> str:
    """The same struck-through span `links.py` uses, so a broken QR looks like
    every other broken reference. 🚫 Deliberately not an anchor: a QR that failed
    to resolve must not offer a control."""
    return (
        '<span class="docrender-dead" title="'
        + html.escape(reason, quote=True) + '">' + html.escape(label) + "</span>"
    )


def _slug(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "-", name).strip("-").lower() or "code"


def _options(raw: str, src: str, name: str) -> dict:
    """Parse the trailing `key=value` pairs, reporting anything unknown.

    ⚠️ AN UNKNOWN KEY IS REPORTED, NEVER IGNORED. A mistyped `dispay=true` would
    otherwise fall through to the default and emit a download link where a
    rendered code was wanted: wrong output, no signal.
    """
    tail = (raw or "").strip()
    if not tail:
        return {}

    found = {}
    for key, value in _OPT.findall(tail):
        if key not in _KEYS:
            state.note(
                "notes",
                src + ': `!!! qr "' + name + '"` carries unknown option `' + key
                + "=" + value + "`. Legal options: " + ", ".join(_KEYS)
                + ". Ignored -- nothing was hidden or shown because of it.",
            )
            continue
        found[key] = value.lower() in ("true", "yes", "1")

    leftover = _OPT.sub("", tail).strip()
    if leftover:
        state.note(
            "notes",
            src + ': `!!! qr "' + name + '"` has trailing text that is not a '
            + "`key=value` option: '" + leftover + "'. Ignored.",
        )
    return found


def _from_form(name: str, src: str):
    """The `src:` of a `forms:` slot on this page. None = no such slot, "" = unusable.

    ⚠️ RETURNS THE URL ONLY. `forms._entry` hands back `(src, text, collapsed)` and
    the other two belong to the EMBED: a QR has no caption to render (the engine
    emits none, by ruling) and cannot be collapsed.

    ⚠️ A MALFORMED SLOT GETS ITS OWN MESSAGE RATHER THAN `_bad_scheme`'s, which
    would say *"has no `url:`"* about a block whose key is `src:`. An accurate
    sentence naming the wrong key is worse than a vague one.
    """
    entry = forms._entry(src, name)
    if entry is None:
        return None
    url = (entry[0] or "").strip()
    if not url:
        state.note(
            "dead_links",
            src + ': `!!! qr "' + name + '"` found a `forms:` slot of that name '
            "with no `src:` value. Nothing was rendered.",
        )
        return ""
    return url


def _payload(name: str, src: str, page):
    """The absolute URL this code will encode, or None to decline.

    THREE RUNGS: this page's `links:` block, then `site.yml`'s registry, then this
    page's `forms:` block. Rungs 1 and 2 are `urllinks`' own ladder and precedence,
    reused rather than re-derived, because two resolution orders for one registry
    is how they drift.

    ⭐ WHY THE `forms:` RUNG IS LAST, AND IT IS LOAD-BEARING RATHER THAN
    ARBITRARY: a `links:` entry is an ADDRESS BOOK whose purpose is to be pointed
    at, while a `forms:` slot's URL is an implementation detail of an embed. So an
    explicit `links:` entry must be able to override it -- a page whose QR should
    point somewhere other than the form it embeds says so, and is believed.

    ⭐ WHY THE RUNG EXISTS AT ALL: without it, a page that embeds a form and wants
    a QR of it must declare that URL TWICE, and no build can detect a mismatch --
    both entries would be valid while the QR pointed at the dead one and the embed
    kept working.

    🔴 ONE NARROWING: `forms.py` enforces an allow-list of exactly one host, so
    this rung can only ever yield a ClickUp form address. **It is not a
    general-purpose address book and must not be grown into one.** A vendor
    manual, a standard, a phone number -- all `links:`.

    ⚠️ `_page_links` TAKES THE PAGE OBJECT, not `src`, which is why `page` is
    threaded down here rather than the path alone.

    🚫 A LEADING `@` IS AN IN-SITE PAGE ID AND IS STILL REFUSED. It is the half
    that constructs `base_url`, the publishing path can override `base_url` for one
    build, and a wrong one bakes a dead address into paper that no later publish
    repairs. It does not ship before the report inventory that would catch it.
    """
    if name.startswith("@"):
        state.note(
            "missing_required",
            src + ': `!!! qr "' + name + '"` targets an in-site page id, which is '
            "NOT BUILT YET (specs/qr-codes.md step 4). Nothing was rendered. An "
            "in-site payload has to be absolute, so it depends on `base_url` -- "
            "and the publishing path may override that for one build, which would "
            "bake a dead address into anything printed. Name an entry in `links:` "
            "or a `forms:` slot on this page instead, or wait for step 4.",
        )
        return None

    entry = urllinks._entry(urllinks._page_links(page), name)
    where = "this page's `links:` block"
    if entry is None:
        entry = urllinks._entry(urllinks._site_links(), name)
        where = "site.yml"

    if entry is None:
        # RUNG 3, reached only when no `links:` entry of this name exists anywhere
        # -- which is what makes an explicit entry an override.
        url = _from_form(name, src)
        if url is None:
            state.note(
                "dead_links",
                src + ': `!!! qr "' + name + '"` names no entry in this page\'s '
                "`links:` block, none in site.yml, and no `forms:` slot on this "
                "page. Nothing was rendered.",
            )
            return None
        if not url:
            return None  # slot found, unusable; `_from_form` reported why
        # ⚠️ STILL SCHEME-CHECKED even though forms.py has a one-host allow-list,
        # because that check runs in forms.py's RENDER path -- so a slot declared
        # and never embedded has never been validated at all, and this rung can
        # reach exactly such a slot.
        problem = urllinks._bad_scheme(url)
        if problem:
            state.note(
                "dead_links",
                src + ': `!!! qr "' + name + '"` resolves to the `forms:` slot of '
                "that name, whose `src:` " + problem,
            )
            return None
        return url

    # ⚠️ A NAME IN BOTH IS REPORTED, NEVER SILENTLY RESOLVED -- same polarity
    # `urllinks` sets for a page overriding the site registry: a silent override is
    # indistinguishable from a typo.
    if forms._entry(src, name) is not None:
        state.note(
            "notes",
            src + ': `!!! qr "' + name + '"` matches BOTH a `links:` entry (in '
            + where + ") and a `forms:` slot of the same name on this page. The "
            "`links:` entry wins, which is the design -- said out loud because a "
            "silent override is indistinguishable from a typo. Delete the "
            "`links:` entry if the QR should follow the embedded form.",
        )

    url = entry[0]
    problem = urllinks._bad_scheme(url)
    if problem:
        # ⭐ REUSED RATHER THAN REIMPLEMENTED, and it earns its keep immediately:
        # this is the function that refuses a URL pointing back into this site,
        # with the reason already written -- so the wrong answer a QR author is
        # most likely to reach for is covered by somebody else's rule.
        state.note(
            "dead_links",
            src + ': `!!! qr "' + name + '"` resolves to an entry in ' + where
            + " that " + problem,
        )
        return None
    return url


def _png(payload: str) -> bytes:
    """The pinned encoder recipe. Every argument is load-bearing; see the docstring.

    ⚠️ `segno` IS IMPORTED HERE, NOT AT MODULE LEVEL. A top-level import makes a
    missing dependency an ImportError at hook load, which takes the WHOLE BUILD
    down -- the shape that killed all four sites on 2026-08-05. Inside the call it
    degrades to one reported, declined code.
    """
    import io

    import segno

    code = segno.make_qr(
        payload,
        error=_ECC,
        mode="byte",
        encoding="utf-8",
        boost_error=False,
    )
    buffer = io.BytesIO()
    code.save(
        buffer, kind="png", scale=_SCALE, border=_BORDER, dark="black", light="white"
    )
    return buffer.getvalue()


def _html_for(src: str, name: str, opts: dict, page) -> str:
    payload = _payload(name, src, page)
    if payload is None:
        return _dead("QR Code", "qr: " + name)

    for key in _KEYS:
        if key in opts:
            # 🚫 RECOGNISED, NOT IMPLEMENTED -- a distinct report line from a
            # mistyped key. Somebody will write these straight out of the spec
            # before the spec is built, and silently emitting a download link for a
            # line that asked for a rendered code is wrong output with no signal.
            state.note(
                "missing_required",
                src + ': `!!! qr "' + name + '" ' + key + "=...` is a recognised "
                "option that is NOT BUILT YET (specs/qr-codes.md step 5). A "
                "download link was rendered instead of a QR image. Remove the "
                "option to silence this.",
            )

    try:
        raw = _png(payload)
    except Exception as exc:
        # Payload too large, `segno` missing, or a version that no longer accepts
        # one of the pinned arguments. Reported and declined -- never a partial
        # image, never a build failure.
        state.note(
            "missing_required",
            src + ': `!!! qr "' + name + '"` could not be encoded (' + str(exc)
            + "). Nothing was rendered.",
        )
        return _dead("QR Code", "qr could not be encoded: " + name)

    digest = hashlib.sha256(
        ("|".join([payload, _ECC, "byte", "utf-8", str(_SCALE), str(_BORDER)]))
        .encode("utf-8")
    ).hexdigest()[:12]
    target = _DIR + "/" + digest + ".png"
    PENDING[target] = raw

    # 🔴 THROUGH THE SHARED HELPER, NEVER A `../` COUNT. images.py names that
    # arithmetic as the bug this house "shipped wrong three separate times", and a
    # QR renders at every depth in the tree, so it is maximally exposed.
    href = relative_url(target, page.file.url)
    return (
        '<p class="dr-qr__download"><a href="' + html.escape(href, quote=True)
        + '" download="qr-' + html.escape(_slug(name), quote=True)
        + '.png">QR Code</a></p>'
    )


def on_config(config):
    """Start every build with an empty collector. See `PENDING`."""
    PENDING.clear()
    return config


def on_page_markdown(markdown, page, config, files):
    """Replace each `!!! qr "name"` with its download link.

    ⚠️ `sub_outside_code` IS NOT OPTIONAL. The page that documents this directive
    contains this directive, and util's own docstring records the first time that
    bit this engine: the page teaching `[Main Stage](@main-stage)` shipped with the
    resolved URL inside its own code fence.
    """
    if "!!!" not in markdown:
        return markdown

    src = getattr(page.file, "src_uri", "")

    def swap(match):
        name = match.group(1).strip()
        opts = _options(match.group("opts"), src, name)
        return "\n\n" + _html_for(src, name, opts, page) + "\n\n"

    return sub_outside_code(_QR, swap, markdown)


def on_post_build(config):
    """Write every collected PNG into `site_dir`.

    Runs after every page body has been read, which is why the file is written
    here rather than planned at `on_files`. See the docstring.

    ⚠️ A FAILED WRITE IS REPORTED, NOT RAISED. A publish must not die over an
    image: the page already carries the link, so the failure is a 404 on one
    download rather than a lost site.
    """
    if not PENDING:
        return

    site = Path(str(config["site_dir"]))
    try:
        (site / _DIR).mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        state.note(
            "missing_required",
            "qr: could not create " + str(site / _DIR) + " (" + str(exc)
            + "). No QR download will resolve.",
        )
        return

    for target, raw in sorted(PENDING.items()):
        try:
            (site / target).write_bytes(raw)
        except OSError as exc:
            state.note(
                "missing_required",
                "qr: could not write " + target + " (" + str(exc)
                + "). That download will 404.",
            )
