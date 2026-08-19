"""The `@url:` namespace -- an EXTERNAL link, named once and referenced by name.

WHY decisions here are the way they are: the doc-render-engine Decision Log.
The reader-facing contract is README section 3. This docstring holds what
somebody EDITING this file has to know, and points at the rest.

    [the standard](@url:osha_mewp)      the label is what you typed
    [](@url:osha_mewp)                  falls back to the entry's `text:`
    [spec](@url:genie#specifications)   an anchor, if the entry has none of its own

TWO HOMES, ONE NAMESPACE, AND THE PAGE WINS.

    instances/<slug>/site.yml   links:   the site-wide registry
    a page's own frontmatter     links:   a local override or a one-off

Michael, 2026-08-18: *"i want something like that but where i can define a
frontmatter... and then in the markdown text i could call it using [](@) but i
know we'd have to be careful not to collide with a page slug."*

=============================================================================
THE COLLISION HE WAS WORRIED ABOUT CANNOT HAPPEN, AND THAT IS WHY THERE IS NO
SECOND SIGIL
=============================================================================

The ask arrived with a proposed workaround attached -- a different character
instead of `@`, to keep a link variable from being mistaken for a page id.
Nothing needed inventing. `links.py` resolves a RESERVED PREFIX at step 1 and a
PAGE ID at step 3, so `@url:osha_mewp` is answered here before page lookup ever
runs. `prefixes.py` exists for precisely this, and its docstring says the
resolution order IS the fix -- written after `@data:inventory_table` once
reported "unknown peer site: data".

⭐ A second sigil would have been a whole parallel syntax bought to solve a
problem the registry already solves. The general form is worth keeping: when a
request arrives carrying its own workaround, price the workaround against the
mechanism that already exists before building it.

=============================================================================
🔴 THE ONE GUARANTEE THIS NAMESPACE CANNOT OFFER, STATED FIRST
=============================================================================

Every other `@` target resolves against something this build KNOWS -- a page id
in `state.PAGES`, a peer's published index, a declared data slot, an indexed
image file. So a broken one renders as the struck-through dead span and lands in
the report.

🔴 AN EXTERNAL URL IS NOT VERIFIABLE AT BUILD TIME. A MISSING NAME is caught
here and gets the dead span for free (this module returns None and links.py does
the rest). A name that resolves to a URL which 404s renders as a perfect,
confident anchor to nothing.

⚠️ That is a REDUCTION in the promise the `@` syntax otherwise makes, and it is
written at the top of this file rather than left for a reader who trusted the
pattern. Link-checking is not unthinkable -- `links._load_peers` already does
network I/O with a timeout and a committed cache -- but the publish routine fires
every 20 minutes, so a naive checker would hit somebody else's server ~72 times a
day per link. That is its own build with its own decisions.

=============================================================================
WHAT THIS IS FOR, AND WHICH HALF OF THE ASK IS THE WEAKER HALF
=============================================================================

A page-local `links:` block is a TYPING SHORTCUT. It does not survive the URL
changing: the same vendor link on twenty pages is twenty edits, which is exactly
the failure the id indirection exists to prevent (README section 1 -- moving or
renaming a page cannot break an inbound link, because none of those things is
what the link points at).

⭐ SO THE SITE-WIDE REGISTRY IS THE FEATURE AND THE PAGE BLOCK IS THE
CONVENIENCE. One edit in `site.yml` fixes every page; a one-off page still gets
its local entry without touching config. Same shape as the `nav:` cascade, and
the same rule `site.yml` already states about `sections:` -- config covers what
the content cannot speak for.

⚠️ AND IT LIVES IN `site.yml` RATHER THAN A NEW `theme/*.tsv`. `theme/` is what a
site LOOKS LIKE; an external address book is not a look. `peers:` is the exact
precedent one block over: a map of names to external base URLs, per site, in
config. A new TSV would also make the registry engine-wide, and OSHA links belong
to the safety site rather than to `hml`.

=============================================================================
NO NEW REPORT BUCKET, ON PURPOSE
=============================================================================

Findings go to `dead_links` (a reference that failed) and `notes` (a declaration
that is wrong or shadowed). Inventing a bucket is TWO edits in two files --
`state.reset()` and sizecheck's `_LABELS` -- and a bucket missing from `_LABELS`
is printed by nothing at all. Both of those files already carry that warning.
This module is not worth a third home for it.
"""

from __future__ import annotations

from . import prefixes, state

#: Schemes an entry may use. `mailto:` and `tel:` are here because a safety page
#: naming a vendor's support line is the same job as naming their manual, and
#: refusing them would push somebody back to a raw markdown link -- which is the
#: thing this namespace exists to replace.
#:
#: ⚠️ A RELATIVE PATH IS REFUSED RATHER THAN PASSED THROUGH. `@url:` means
#: OUTSIDE; an in-site target is `@<id>`, which survives the file moving. Letting
#: a path through here would quietly hand somebody a link that breaks on the next
#: reorganisation, with no report -- the whole defect the id syntax fixes.
_SCHEMES = ('https://', 'http://', 'mailto:', 'tel:')


def _entry(block, name: str):
    """One entry out of a `links:` mapping, normalised to (url, text).

    Two spellings, both legal, because the short one is what somebody writes for a
    link with an obvious label and the long one is what they need the moment they
    want a bare `[](@url:x)` to say something:

        genie_manual: https://example.com/manual
        osha_mewp:
          url: https://example.com/standard
          text: OSHA aerial lift standard

    Returns None when the name is absent, so a caller can fall through from the
    page block to the site registry without asking twice.
    """
    if not isinstance(block, dict):
        return None
    raw = block.get(name)
    if raw is None:
        return None
    if isinstance(raw, str):
        return (raw.strip(), '')
    if isinstance(raw, dict):
        return (str(raw.get('url', '')).strip(), str(raw.get('text', '')).strip())
    return ('', '')


def _site_links() -> dict:
    """The site-wide registry from `site.yml`, or an empty mapping."""
    block = state.INSTANCE.get('links')
    return block if isinstance(block, dict) else {}


def _page_links(page) -> dict:
    """This page's own `links:` block, or an empty mapping.

    Read out of `state.BY_SRC` rather than `page.meta`, for the same reason
    navstate does: `BY_SRC` is what the frontmatter parser filled and is populated
    long before any page renders, so one lookup answers both the resolve-time call
    and the on_files audit below.
    """
    block = state.BY_SRC.get(page.file.src_uri, {}).get('links')
    return block if isinstance(block, dict) else {}


def _bad_scheme(url: str) -> str:
    """Why this URL is not usable, or "" if it is fine.

    ⚠️ A SCHEME CHECK, NOT A VALIDITY CHECK, AND THE DIFFERENCE IS THE WHOLE LIMIT
    AT THE TOP OF THIS FILE. It proves the string is shaped like an external
    address. It proves nothing whatsoever about whether anything is there.
    """
    if not url:
        return 'has no `url:`'
    if not url.lower().startswith(_SCHEMES):
        if '//' not in url and ':' not in url:
            return (
                "looks like a path ('" + url + "'), and @url: is for EXTERNAL "
                'addresses only. An in-site target is @<id>, which survives the '
                'page being moved or renamed -- that is the point of an id.'
            )
        return (
            "uses a scheme this engine does not accept ('" + url + "'). Allowed: "
            + ', '.join(_SCHEMES) + '.'
        )
    base = str(state.INSTANCE.get('base_url', '')).rstrip('/')
    if base and url.startswith(base):
        return (
            'points back into THIS site (' + base + '). Use @<id> instead: an id '
            'follows the page when it moves, and a hardcoded URL to your own site '
            'is a link that breaks silently on the next reorganisation.'
        )
    return ''


def _resolve(name: str, page, label: str, anchor: str):
    """Resolve `@url:<name>`. Returns markdown, or None to decline.

    Declining is how a missing name gets the struck-through dead span: links.py
    reports it and renders the span itself. 🚫 Never return a plausible-looking
    link for a name that is not declared.

    ⚠️ NOTHING IS RECORDED TO THE REFERENCE GRAPH HERE. links.py calls
    `state.ref(...)` on both sides of this -- once when a handler declines, once
    when it returns -- so recording here would double-count every external link in
    /doc-refs.json. The rule this repo keeps re-learning: the recording lives in
    the branch that produces the href, and there is exactly one of those.
    """
    src = page.file.src_uri
    local = _page_links(page)
    site = _site_links()

    found = _entry(local, name)
    where = 'page'
    if found is None:
        found = _entry(site, name)
        where = 'site.yml'
    elif _entry(site, name) is not None:
        # ⭐ THE OVERRIDE IS THE FEATURE, AND IT IS STILL WORTH SAYING OUT LOUD. A
        # page quietly disagreeing with the registry is how two readers of the
        # same site end up at two different vendor pages and nobody can tell why.
        state.note(
            'notes',
            src + ': `links: ' + name + '` overrides the site-wide entry of the '
            + 'same name. The page wins, which is the design -- said out loud '
            + 'because a silent override is indistinguishable from a typo.',
        )

    if found is None:
        return None

    url, text = found

    problem = _bad_scheme(url)
    if problem:
        state.note(
            'dead_links',
            src + ': `@url:' + name + '` resolves to an entry in ' + where + ' that '
            + problem,
        )
        return None

    if anchor:
        if '#' in url:
            # The declared address already names a fragment. Two fragments is not a
            # URL, so one has to lose, and it is the call site's: the entry is the
            # address of record and a page cannot know it was already deep.
            state.note(
                'dead_links',
                src + ": '@url:" + name + anchor + "' adds an anchor to an entry "
                + 'whose URL already carries one (' + url + '). The declared '
                + "fragment is kept and '" + anchor + "' was ignored -- point the "
                + 'entry at the page root, or declare a second entry.',
            )
        else:
            url = url + anchor

    # The label the author typed, then the entry's `text:`, then the name itself.
    # ⭐ THE SAME LADDER A BARE MARKER USES (its row's `label`, then its name), and
    # it is why the ask arrived carrying a name AND a url: `[](@url:x)` matches the
    # link pattern perfectly and would otherwise render an anchor with no text at
    # all -- clickable, invisible, and impossible to catch in a review.
    shown = label or text or name

    # 🚫 NO CLASS ON THE ANCHOR, DELIBERATELY. A peer link wears `.docrender-xref`
    # because a rule paints it. There is no rule for an external link, and a class
    # with no rule is a dead control -- the thing this engine kills on sight. If
    # external links should look different, that is one row of CSS and one word
    # here, in that order.
    return '[' + shown + '](' + url + ')'


# ⚠️ CLAIMED AT MODULE IMPORT, WHICH IS WHY hooks/03d_urllinks.py EXISTS AND IS
# LOAD-BEARING. Drop that shim from the `hooks:` list and this module is never
# imported, nothing claims the namespace, and every `@url:` on every site renders
# as "unknown peer site: url" -- correct behaviour from links.py, and a mystery to
# the author. Same shape as 03c, and as hooks/04_theme.py, which sits unregistered
# in that folder doing nothing.
#
# ⭐ `anchors=True` because an external page has headings like any other, and
# prefixes.py's default is False precisely so that forgetting this flag drops a
# fragment with a report rather than raising a TypeError mid-render.
prefixes.claim('url', __name__, _resolve, anchors=True)


def on_files(files, config):
    """Audit every declared entry, whether or not a page references one.

    ⭐ THE POINT IS THE ENTRY NOBODY HAS USED YET. `_resolve` only ever sees a name
    somebody wrote in prose, so a malformed registry entry would sit unreported
    until the first reference -- and the report is most useful to the person who
    just typed the entry, not to whoever links it next month.

    ⚠️ It cannot check that a URL WORKS. See the limit at the top of the file.
    """
    site = _site_links()
    for name in sorted(site):
        entry = _entry(site, name)
        problem = _bad_scheme(entry[0] if entry else '')
        if problem:
            state.note('notes', 'site.yml: `links: ' + name + '` ' + problem)

    for src, meta in sorted(state.BY_SRC.items()):
        block = meta.get('links')
        if block is None:
            continue
        if not isinstance(block, dict):
            # A list or a bare string here parses as valid YAML and resolves to
            # nothing, which is the silent shape this engine reports rather than
            # ignores.
            state.note(
                'notes',
                src + ': `links:` must be a mapping of name to URL (or to a '
                + '`url:`/`text:` pair). Found ' + type(block).__name__
                + ', so no local link names are available on this page.',
            )
            continue
        for name in sorted(block):
            entry = _entry(block, name)
            problem = _bad_scheme(entry[0] if entry else '')
            if problem:
                state.note('notes', src + ': `links: ' + name + '` ' + problem)

    return files
