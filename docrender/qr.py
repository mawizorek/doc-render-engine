"""The `!!! qr "name"` directive -- a STATIC QR code built at publish time.

WHY decisions here are the way they are: `specs/qr-codes.md` (BUILD 6) and the
doc-render-engine Decision Log. This docstring is the CONTRACT.

    !!! qr "incident_form"

Michael, 2026-08-21: *"i wnat to qr code out to the incident report fowm, in
case i print the page and hsare it - that way peopoel can pull up the form on
their phone"* and, on where the address lives, *"i like the making it a part of
exisitng links: organization."*

=============================================================================
STEP 2 OF SIX. WHAT IS DELIBERATELY NOT HERE YET
=============================================================================
The spec's build order exists because the risky half must land AFTER the surface
that verifies it. So this module ships the SAFE half:

    BUILT      an external `links:` name -> a PNG download link
    NOT YET    `@page-id` targets (needs the base_url refusal, spec §1)
    NOT YET    the report inventory (spec §5, and it is step 3 on purpose)
    NOT YET    `display=` / `print=` (spec §4d -- a rendered code)
    NOT YET    the `forms:` rung (spec ruling 2)

🚫 AN UNBUILT OPTION IS REFUSED, NOT IGNORED. `display=`/`print=` parse and then
report "recognised, not implemented" -- because a key that silently does nothing
is the defect mkdocs.yml's own comment records a dead hook for, and because
somebody will write them from the spec before the spec is built.

=============================================================================
🔴 THE ADDRESS LIVES IN `links:`. NEVER IN THE DIRECTIVE.
=============================================================================
The name is resolved through `urllinks`' registry -- page frontmatter first, then
`site.yml` -- so one edit fixes every page. A raw URL typed into the directive is
REFUSED: *"the same vendor link on twenty pages is twenty edits,"* and on paper it
is twenty edits and forty reprints.

⭐ AND THAT REGISTRY IS READ, NEVER MODIFIED. `urllinks._site_links()` reads
`state.INSTANCE` directly, which is why this whole feature needs no instance
config key and never touches `docrender/instance.py` -- a file already past the
read ceiling with a `print:` block queued behind it.

=============================================================================
🔴 DETERMINISM IS CONSTRUCTED HERE, NOT INHERITED FROM THE LIBRARY
=============================================================================
"Any generator makes the same image" is FALSE by default. Segno's own library
comparison records that `qrcode` does not reproduce the reference symbol in
ISO/IEC 18004:2015 Fig. 1. Scanning interoperability is guaranteed by the
standard; byte-identical GENERATION is not. So every knob is pinned:

🔴 `boost_error=False` -- VERIFIED AGAINST SEGNO'S API DOCS 2026-08-21, AND THE
DEFAULT IS `True`. Left alone, segno silently RAISES the error level whenever the
chosen version has spare capacity, so the same payload at the same declared level
yields a different level -- and therefore a different matrix -- because the
payload changed by one character. The cost of switching it off is real and is
stated so nobody "optimises" it back on: we deliberately leave spare capacity
unused. That is the price of a matrix that cannot change on its own.

🔴 `make_qr()`, NOT `make()` -- AND THIS IS THE ONE THE SPEC MISSED. `segno.make`
takes `micro=None` by default, which means it *may* emit a MICRO QR code for a
short payload. A Micro QR is a different symbology with its own version set, a
2-module quiet zone, and materially worse reader support. It would have scanned
fine on the developer's phone and failed on somebody else's, which is the exact
failure shape this engine keeps logging. `make_qr` can never return one.

`error=` -- segno's default is `None`, documented as level **L** (~7% recovery).
Unacceptable for paper, so the level is always explicit. ONE ENGINE CONSTANT,
never a per-line option (Michael: *"we will set it glboally for all builds in all
renderer apps. let's not overthink it here"*). ⭐ And that is safe in a way worth
knowing: changing `_ECC` never invalidates printed paper, because the PAYLOAD is
unchanged, so every code already on a wall keeps scanning. It is the reverse of
`base_url`, which is unforgiving after print.

`mode="byte"` -- alphanumeric mode is denser but UPPERCASE-ONLY, and a URL path is
case-sensitive, so a URL can never legally use it. Pinned anyway so an all-caps
payload cannot silently switch modes and change the matrix.

`encoding="utf-8"` -- segno otherwise tries ISO/IEC 8859-1 and falls back to
UTF-8, which is a decision made from the payload's contents. Identical output for
any ASCII URL; pinned so it stays identical for one that stops being ASCII.

`border=4` -- the quiet zone, and it is PART OF THE SYMBOL rather than padding.
It is baked into the image, where no stylesheet can crop it. Cropping it stops
the code scanning.

⚠️ A MAJOR SEGNO BUMP MAY LEGALLY CHANGE OUR OUTPUT (serialization defaults, mask
tie-breaking). That is why `requirements.txt` carries an upper bound.

=============================================================================
⭐ WHY THE PNG IS WRITTEN AT `on_post_build` AND NOT AT `on_files`
=============================================================================
Michael, 2026-08-21: *"pdfs currently still work if they have links so this
shoudl still apply where the pdf links to a donalod of the qr code."*

That ruling killed the obvious mechanism. A `data:` URI needs no file at all --
but PDF viewers refuse non-`http(s)` link targets, so a data URI works perfectly
on screen and DIES in a PDF, which is the medium the whole ruling is about, with
no error anywhere.

🔴 AND `on_files` CANNOT HELP, because a `!!! qr` lives in the page BODY and
`on_files` has already run by the time any body is read. `assets.py` ruled on
exactly this shape for `!!! data`: *"a `!!! data` block lives in the BODY of a
page, not in the first 2000 bytes a frontmatter scan reads, so the router's trick
does not transfer."*

⭐ SO THE HREF IS DERIVED RATHER THAN DISCOVERED. The filename is a content hash
of the pinned recipe plus the payload, which means it can be written into the page
before the file exists, and `on_post_build` -- which runs after every body has
been read -- writes the collected images into `site_dir`. `docindex.py` already
publishes a real file from that event.

⭐ THREE CONSEQUENCES, ALL OF THEM THE POINT:

  * NOTHING ENTERS `images.INDEX`. That index refuses duplicate filename stems,
    on the rule that *"two pictures with one name are two different pictures"* --
    so a generated file joining it could break a real image's reference and would
    only be safe through a hook-ordering dependency nobody would know they had.
  * NO STRAY BANG. `images.py` works because its resolver returns link markdown
    and the `!` in `![alt](@img:x)` survives outside the match. A block directive
    never has that problem.
  * IDENTICAL RECIPE + PAYLOAD -> IDENTICAL PATH, so a rebuild produces no diff.

⚠️ WHAT IT COSTS, STATED RATHER THAN DISCOVERED: these files do NOT carry
`assets.py`'s content fingerprint, because they are not planned assets. The hash
IS the filename, so cache behaviour is the same by accident rather than by that
mechanism -- do not "fix" it by routing them through `_stamped()`, which would
put them back into the `on_files` timing problem above.

=============================================================================
⚠️ THE LIMIT, STATED FIRST, BECAUSE IT IS WORSE HERE THAN ANYWHERE
=============================================================================
`urllinks.py` already says an external URL is not verifiable at build time. A QR
takes that unverifiable thing and makes it UNREADABLE BY A HUMAN AS WELL. Nobody
proofreads a QR, and a wrong one renders as a perfect, confident square.

🔴 THE BUILD REPORT INVENTORY (spec §5) IS THE ANSWER TO THAT, AND IT IS STEP 3.
Until it lands, the only verification is scanning the code. Do not add
`@page-id` support before it: a mistyped external name at least fails loudly here,
while a wrong `base_url` produces a beautiful code pointing nowhere.
"""

from __future__ import annotations

import hashlib
import html
import re
from pathlib import Path

from . import state, urllinks
from .util import relative_url, sub_outside_code

#: `!!! qr "name"` plus optional trailing `key=value` pairs, alone on its line.
#:
#: Deliberately the same shape as `!!! form "slot"` (docrender/forms.py) so the
#: body vocabulary stays one pattern rather than two spellings of one idea. The
#: difference is the trailing group: forms.py anchors straight to end-of-line,
#: and that anchor is exactly where options have to go.
#:
#: 🚫 OPTIONS ARE BARE `key=value`, NOT AN attr_list BRACE BLOCK, and that is a
#: refusal rather than an oversight. `markers.py` hands an unrecognised brace
#: block back untouched *"rather than eating syntax that belongs to somebody
#: else"*, while `cells.plain()` strips EVERY brace block -- BUILD 1's spec names
#: that disagreement as a live defect. Worse, BUILD 1's `clean.py` is built to
#: remove our own declared vocabulary, so a QR option in braces is a QR option a
#: future stripper deletes.
_QR = re.compile(r'(?m)^[ \t]*!!![ \t]+qr[ \t]+"([^"\n]+)"(?P<opts>[^\n]*)$')

_OPT = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=(\S+)")

#: Exactly two keys are legal, so anything else is an ERROR rather than a
#: judgement call. Both are declared here and REFUSED in `_html` until spec §4d
#: is built -- recognised-but-unbuilt is a different report line from mistyped,
#: and telling them apart is the whole reason this tuple exists this early.
_KEYS = ("display", "print")

#: 🔴 ONE ENGINE CONSTANT, NOT CONFIG AND NOT A LINE OPTION. Michael's ruling was
#: "globally for all builds in all renderer apps", and an engine constant is the
#: only thing that spans apps -- `site.yml` would be per site.
#:
#: ⚠️ `Q` (~25% recovery) IS A STARTING POINT AWAITING ONE MEASUREMENT, and the
#: measurement is not optional because EC IS NOT MONOTONIC AT A FIXED PHYSICAL
#: SIZE: more correction means more codewords means a higher version means each
#: module is physically SMALLER on the same square of paper -- and module size is
#: what a camera has to resolve. `H` in a 25mm square can scan WORSE than `Q`.
#: 🔴 The legibility floor for safety-critical print is Hazard Hawthorne's call,
#: per specs/print-identity.md §3f. A safety QR that will not scan is a safety
#: defect, not a styling one.
_ECC = "Q"

#: Pixels per module in the downloaded PNG. ⚠️ RECORDED BECAUSE IT IS THE ONE
#: PROPERTY A PERSON NOTICES: it decides whether the download is usable at poster
#: scale. Also part of the determinism contract -- a scale change changes the
#: bytes, therefore the hash, therefore the filename.
_SCALE = 8

#: The quiet zone, in modules. Part of the symbol. See the docstring.
_BORDER = 4

#: Where the images land in the built site. Not `assets/`, which is
#: `assets.py`'s planned-and-fingerprinted namespace and would invite somebody to
#: route these through `_stamped()` -- see the docstring for why that reopens the
#: timing bug.
_DIR = "qr"

#: `site-relative path -> png bytes`, filled during page rendering and drained at
#: `on_post_build`. A module-level collector on the `images.INDEX` precedent.
#:
#: ⚠️ CLEARED AT THE START OF EVERY BUILD, not at import: `mkdocs serve` rebuilds
#: IN-PROCESS, so a dict that only ever grows would carry a deleted page's code
#: into the next build and write a file nothing references.
PENDING: dict[str, bytes] = {}


def _dead(label: str, reason: str) -> str:
    """The same struck-through span `links.py` uses. Never an anchor.

    Borrowed rather than reinvented so a broken QR looks like every other broken
    reference on the site. 🚫 It is deliberately not clickable: a QR that failed
    to resolve must not offer a control.
    """
    return (
        '<span class="docrender-dead" title="'
        + html.escape(reason, quote=True) + '">' + html.escape(label) + "</span>"
    )


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


def _payload(name: str, src: str):
    """The absolute URL this code will encode, or None to decline.

    Reads the `links:` registry through `urllinks`, page block first, then
    `site.yml` -- the same ladder and the same precedence a `@url:` reference
    already walks, because two resolution orders for one registry is how they
    drift.

    🚫 A LEADING `@` IS AN IN-SITE PAGE ID AND IS REFUSED IN STEP 2, LOUDLY. It is
    the half that has to construct `base_url`, and the publishing path can
    override `base_url` for one build -- so a wrong one bakes a dead address into
    paper, which no later publish can repair. It does not ship before the report
    inventory that would catch it.
    """
    if name.startswith("@"):
        state.note(
            "missing_required",
            src + ': `!!! qr "' + name + '"` targets an in-site page id, which is '
            "NOT BUILT YET (specs/qr-codes.md step 4). Nothing was rendered. An "
            "in-site payload has to be absolute, so it depends on `base_url` -- "
            "and the publishing path may override that for one build, which would "
            "bake a dead address into anything printed. Name an external entry in "
            "`links:` instead, or wait for step 4.",
        )
        return None

    entry = urllinks._entry(urllinks._page_links_for(src), name)
    where = "page"
    if entry is None:
        entry = urllinks._entry(urllinks._site_links(), name)
        where = "site.yml"
    if entry is None:
        state.note(
            "dead_links",
            src + ': `!!! qr "' + name + '"` names no entry in this page\'s '
            "`links:` block or in site.yml. Nothing was rendered.",
        )
        return None

    url = entry[0]
    problem = urllinks._bad_scheme(url)
    if problem:
        # ⭐ REUSED RATHER THAN REIMPLEMENTED, and it earns its keep immediately:
        # that function is what refuses a URL pointing back into this site, with
        # the reason already written -- "use @<id> instead". So the one wrong
        # answer a QR author is most likely to reach for is already covered by
        # somebody else's rule.
        state.note(
            "dead_links",
            src + ': `!!! qr "' + name + '"` resolves to an entry in ' + where
            + " that " + problem,
        )
        return None
    return url


def _png(payload: str) -> bytes:
    """The pinned encoder recipe. Every argument is load-bearing; see docstring."""
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
    code.save(buffer, kind="png", scale=_SCALE, border=_BORDER, dark="black",
              light="white")
    return buffer.getvalue()


def _html_for(src: str, name: str, opts: dict, page) -> str:
    payload = _payload(name, src)
    if payload is None:
        return _dead("QR Code", "qr: " + name)

    for key in _KEYS:
        if key in opts:
            # 🚫 RECOGNISED, NOT IMPLEMENTED -- a distinct report line from a
            # mistyped key, on purpose. Somebody will write these straight out of
            # the spec before the spec is built, and silently emitting a download
            # link for a line that asked for a rendered code is the wrong output
            # with no signal.
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
        # A payload too large, or a segno version that no longer accepts one of
        # the pinned arguments. Reported and declined -- never a partial image.
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
    # arithmetic as the bug this house "shipped wrong three separate times", and
    # a QR renders at every depth in the tree, so it is maximally exposed.
    href = relative_url(target, page.file.url)
    return (
        '<p class="dr-qr__download"><a href="' + html.escape(href, quote=True)
        + '" download="qr-' + html.escape(_slug(name), quote=True)
        + '.png">QR Code</a></p>'
    )


def _slug(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "-", name).strip("-").lower() or "code"


def on_config(config):
    """Start every build with an empty collector. See `PENDING`."""
    PENDING.clear()
    return config


def on_page_markdown(markdown, page, config, files):
    """Replace each `!!! qr "name"` with its download link.

    ⚠️ `sub_outside_code` IS NOT OPTIONAL. The page that documents this directive
    contains this directive, and util's own docstring records the first time that
    bit this engine: the page teaching `[Main Stage](@main-stage)` shipped with
    the resolved URL inside its own code fence.
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

    Runs after every page body has been read, which is the whole reason the file
    is written here rather than planned at `on_files`. See the docstring.

    ⚠️ A FAILED WRITE IS REPORTED, NOT RAISED. A publish must not die over an
    image; the page already carries the link, so the failure is a 404 on one
    download rather than a lost site -- and the report is where it belongs.
    """
    if not PENDING:
        return

    root = Path(str(config["site_dir"])) / _DIR
    try:
        root.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        state.note("missing_required", "qr: could not create " + str(root)
                   + " (" + str(exc) + "). No QR download will resolve.")
        return

    for target, raw in sorted(PENDING.items()):
        path = Path(str(config["site_dir"])) / target
        try:
            path.write_bytes(raw)
        except OSError as exc:
            state.note("missing_required", "qr: could not write " + target
                       + " (" + str(exc) + "). That download will 404.")
