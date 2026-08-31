"""Hook 03 -- links point at IDS, never at paths.

    [Main Stage](@main-stage)              a page in this site
    [the notes](@main-stage#venue-notes)   a heading on it
    [rep plot](@oph:rep-plot)              a page in a SIBLING site
    [the schedule](@data:circuit_schedule) a data table on THIS page
    [ETC](@term:etc)                       a defined term, styled as terminology
    [fkCal](@rel:table-events)             a relationship, styled as schema
    [the TD](@role:technical-director)     a production role, glossed on hover
    [the front panel](@img:h5-front)       an image anywhere in this site

Moving the file, renaming its folder, or retitling the page cannot break an inbound
link, because none of those things is what the link points at. Set `id:` once and never
change it; that promise is the whole mechanism.


RESOLUTION ORDER (rewritten 2026-08-04, DL J8)
==============================================

0. A TOKEN CARRYING A FILE EXTENSION is refused, with the reason said out loud.
1. RESERVED PREFIX. `@<prefix>:<rest>` claimed by a handler in docrender/prefixes.py.
   `data` is claimed by datatable.py, `img` by images.py, and every marker prefix by
   markerlinks.py -- which derives them from the `prefix` column of theme/markers.tsv,
   so that set GROWS WITH A DATA EDIT and is not a list anybody maintains. Read that
   module for why the registry is DERIVED from its handlers rather than typed here.
2. PEER SITE. `@<slug>:<id>` against the peer's published index.
3. PAGE ID. `@<id>` in this site.

THE ORDER IS THE FIX, NOT A PREFERENCE. This file used to run `token.partition(":")`
first and treat everything left of the colon as a peer slug -- so `@data:inventory_table`
reported "unknown peer site: data", naming the wrong subsystem on a page that was
perfectly correct. Two namespaces built the same week by different hands is how the
second merge silently reopens the first hole.

And the extension refusal matters because the token charset accepts dots, so
`[x](@circuits-and-dimmers.tsv)` matched this regex and resolved as a page id -- the
wrong error, on a page one edit from right. Data files are reached by SLOT, never by
filename; that is the entire point of a slot.

⚠️ THE REFUSAL LIST HAD A HOLE FOR IMAGES UNTIL 2026-08-07, and it was the same bug
wearing the same clothes: no image suffix was listed, so `[fig](@rep-plot.png)` walked
straight past step 0 and came back as "no page yet with id: rep-plot.png". The list
now covers both families and the message BRANCHES -- a data file is sent to
`@data:<slot>`, an image to `@img:<name>` -- because a reader chasing a broken picture
should not be told about frontmatter data slots.


AN `#anchor` IS NOW PASSED TO HANDLERS THAT ASKED FOR IT (2026-08-09)
=====================================================================

~~⚠️ A RESERVED PREFIX TAKES NO `#anchor`, AND THAT WAS SILENT UNTIL 2026-08-04. A
handler's signature is `(rest, page, label)` -- no anchor -- so `@data:x#totals` or
`@term:etc#history` parsed fine, resolved fine, and lost the anchor on the way out.
The reader got a correct-looking link to the top of the wrong place. It is now
REPORTED and still dropped, which is the honest minimum: passing it through would
mean changing the signature every handler already implements, and datatable.py is
over the read ceiling tonight, so that is a deliberate later change and not a thing
to sneak into a feature branch.~~

STRUCK 2026-08-09, and left struck because "still dropped" was true for four days.
That later change is here, and it did NOT need the signature edit it was waiting on.

⭐ THE OPT-IN IS ON THE CLAIM. `prefixes.claim(..., anchors=True)` says a handler
accepts a fourth positional argument; this file asks `prefixes.takes_anchor()` and
picks the call shape. `@data:` and `@img:` never opted in, are called exactly as
before, and keep the complaint below -- correctly, because `@data:` addresses a whole
TABLE and `@img:` a whole PICTURE, and neither has anywhere for a fragment to point.
So the parked fix turned out not to require touching datatable.py at all.

⚑ Worth keeping: a change blocked on "we would have to edit that file too" is worth
re-examining for a version that does not. The blocker was assumed to be the signature
and it was actually the ASSUMPTION THAT ONE ANSWER FITS EVERY HANDLER.

What forced it was the calc marker: a calculation has no page of its own, it lives at
a HEADING on its table's page, so `@calc:table-workdays#calc-fkCalendar` is the whole
address and the fragment is the half that carries the meaning.


AND SO IS THE AUTHOR'S TRAILING `{...}` (2026-08-30, BUILD 9)
=============================================================

    Ask the [Theatre Administrator](@role:theatre-administrator){.no-print}

The same mechanism one rung further up the ladder in prefixes.py: a handler that
claimed `opts=True` receives the block as a FIFTH argument and OWNS it, and every
other branch of `replace()` re-emits it verbatim.

🔴 RE-EMITTING IS NOT A COURTESY, IT IS THE WHOLE SAFETY ARGUMENT. Before this
change the regex stopped at the closing paren, so an author's brace was never
consumed and simply survived into the output -- which is why `[x](@page-id){.foo}`
puts a class on a plain page link TODAY and has always worked. Widening the pattern
without re-emitting in every branch would have broken that silently, on live content,
with no report line. Every branch below therefore ends `+ opts`, and the ONE that
does not is the one whose handler was handed the value instead.

✅ AND THE REGRESSION SURFACE WAS MEASURED BEFORE THE PATTERN CHANGED, not reasoned
about: every `.md` under `user:mawizorek` was searched for `](@` and NOTHING anywhere
writes a brace after an @-link. So "identical to today" is a verified claim about real
content rather than a hopeful one about the code.

⚠️ A HANDLER THAT OPTS IN AND IGNORES THE VALUE EATS IT. That is stated in
prefixes.claim's docstring too, because the failure is invisible from here: this file
cannot tell a handler that merged the block from one that dropped it.

⭐ IT CLOSED A GAP RATHER THAN ONLY SERVING ONE FLAG. No marker link could carry an
author class on any site before today, and nothing anywhere said so -- the brace
landed next to the one markerlinks emits, and attr_list takes one block. The feature
that forced the fix was a print opt-out; what shipped is every marker link becoming
decoratable.


EVERY RESOLUTION IS RECORDED (added 2026-08-06)
===============================================

Each branch of `replace()` calls `state.ref(...)` before it returns. docindex.py
inverts the result and publishes /doc-refs.json.

⭐ NOTHING NEW IS COMPUTED. This file already had to resolve every reference to
rewrite it, and it discarded the answer the instant the string was built -- the
reference graph existed once per link, for the length of one function call, and was
never written down. The recording sits INSIDE the branch that produces the href,
which is the only placement where the report cannot drift from the page: there is no
second pass to disagree with the first.

⭐ AND THAT IS WHAT MAKES A MARKER LINK WORTH TYPING. `[fkCal](@rel:table-events)`
records a real edge here, so "every relationship in this doc set" is a graph rather
than a count. The span form `{.rel}` can only record a mention.

⚠️ A DEAD REFERENCE IS RECORDED TOO, with `ok: false`. A report of only the working
links would describe a site that does not exist, and the broken ones are the reason
anybody opens the file.


THE PAGE MAP CARRIES WHAT OTHER PAGES NEED (extended 2026-08-30, BUILD 9)
=========================================================================

`on_files` builds `state.PAGES` -- the published map, keyed by page id. It holds
exactly the facts a DIFFERENT page has to know about this one, which is why `gloss`
and `print_gloss` are in it as of BUILD 9.

⭐ AND THE ABSENCE OF THAT ROUTE WAS THE WHOLE BUILD. markerlinks resolves an
`@role:` reference against this map; the frontmatter lives in `state.BY_SRC`, which
is keyed by `src_uri` and not by page id. So a resolver holding an id had NO path to
its target's frontmatter at all -- not a slow path, none. Two keys here, at the one
site where `meta` is already in hand, and the feature exists.

⚠️ SO THE ADMISSION TEST FOR A NEW KEY IS NARROW: does a page OTHER THAN THIS ONE
need the value? `type` and `status` passed it, `gloss` passes it, and a phone number
does not -- see objects/role.yml, which refuses exactly that on space.yml's ruling.
This is not a general-purpose frontmatter cache and must not become one.

🔴 AND READING IT OFF `PAGES` RATHER THAN `BY_SRC` IS LOAD-BEARING. PAGES is built
AFTER visibility prunes, so a link can never resolve to a page that was not built.
A consumer reaching into BY_SRC for the same value would reintroduce exactly that
hole -- a gloss arriving from a page nobody can open.


CROSS-SITE, with the honest limit up front. Every site in the family publishes
/doc-index.json at its root on every build. `@peer:id` resolves against the peer's
index, fetched at BUILD time and cached to disk in the instance folder. If a sibling
renames a page, our links stay wrong until we rebuild.

The cache is COMMITTED, not ignored. An unreachable peer then degrades to 'last known
good, marked stale' instead of taking our build down over somebody else's outage.

⚠️ A PEER'S GLOSS IS NOT AVAILABLE, and that is a real limit rather than an
oversight: the peer branch resolves against `/doc-index.json`, which docindex.py
publishes, and that file does not carry frontmatter. So `@oph:some-role` would link
correctly and carry no hover text. Not fixed here -- it needs a decision about what
the cross-site index promises, which is a bigger question than one field.

WHAT A BROKEN REFERENCE LOOKS LIKE. A `<span>`: red, struck through, carrying a
`[broken link]` badge and a tooltip naming what was not found. **It is NOT an anchor**
-- no href, no navigation, nothing to click. The link does not ACT, and the failure is
not hidden. A marked-but-dead reference is useful information on a site being written:
it says a document is coming.

Code is skipped via util.sub_outside_code -- see that function for why. Same-site paths
are resolved by util.relative_url -- see THAT function for the root-index bug this file
shipped with, and do not reintroduce a `../` count.
"""

from __future__ import annotations

import html
import json
import re
import urllib.request
from pathlib import Path

from . import prefixes, state
from .util import relative_url, sub_outside_code

#: ⚠️ THE `opts` GROUP IS OPTIONAL AND MUST STAY OPTIONAL. It captures the author's
#: trailing attr_list block, braces included, so a handler can merge it into its own.
#: Every branch that does not hand it to a handler re-emits it verbatim -- see the
#: docstring: not re-emitting is a silent regression on content that works today.
_LINK = re.compile(
    r"\[(?P<label>[^\]]*)\]\(@(?P<token>[A-Za-z0-9_.:-]+)(?P<anchor>#[A-Za-z0-9_-]+)?\)"
    r"(?P<opts>\{[ \t]*[^}\n]*\})?"
)

#: Suffixes that mean somebody named a FILE where a SLOT belongs. Not a security
#: check, a legibility one: the error has to name the right subsystem.
_DATA_SUFFIXES = (".tsv", ".csv", ".json", ".yml", ".yaml", ".md", ".txt", ".xlsx")

#: The same mistake, made about a picture. Kept as its OWN tuple rather than
#: appended above, because a name is a promise: seven image extensions inside a
#: constant called `_DATA_SUFFIXES` would be a lie the next reader has to discover.
#:
#: ⚠️ Mirrors `images.SUFFIXES` and must stay in step with it. `.pdf` is absent from
#: both for the same reason -- a PDF is a document you LINK to, not a picture you
#: place, and naming it here would invite `![alt](@img:some-plan)`.
_IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif")

_TIMEOUT = 10


def _cache_path() -> Path:
    return Path(state.INSTANCE.get("dir", ".")) / "xref-cache.json"


def _dead(label: str, reason: str) -> str:
    """A span, deliberately. Marked as broken, impossible to click."""
    return (
        '<span class="docrender-dead" title="' + html.escape(reason, quote=True) + '">'
        + html.escape(label) + "</span>"
    )


def on_files(files, config):
    for f in files.documentation_pages():
        meta = state.BY_SRC.get(f.src_uri, {})
        page_id = meta.get("id")
        if not page_id:
            continue
        state.PAGES[page_id] = {
            "id": page_id,
            "type": meta.get("_type", "page"),
            "title": meta.get("title") or f.name,
            "url": f.url,
            "status": meta.get("status", "public"),
            # BUILD 9. The hover gloss and its paper override, read by
            # markerlinks on any page that REFERENCES this one. See the module
            # docstring: the admission test is whether another page needs it.
            #
            # ⚠️ `.get()` WITH NO DEFAULT, SO A MISSING KEY IS None AND AN EMPTY
            # ONE IS "". Those are different states downstream and collapsing
            # them here would make one unreachable: absent print_gloss means
            # "print the gloss", empty means "print nothing". Do not add `or ""`.
            "gloss": meta.get("gloss"),
            "print_gloss": meta.get("print_gloss"),
        }

    _load_peers()
    # Every hook has been imported by now, so the registry is complete. A peer slugged
    # with a reserved word would otherwise stop resolving and say nothing at all.
    #
    # ⚠️ THE RESERVED SET IS NO LONGER FIXED AT DEVELOPMENT TIME. markerlinks derives
    # its claims from theme/markers.tsv, so adding a marker row can newly collide with
    # a peer slug that has been fine for months. This call is what turns that into a
    # line in the report rather than a peer that quietly stops resolving.
    prefixes.audit_peers((state.INSTANCE.get("peers") or {}).keys(), state.note)
    return files


def _load_peers() -> None:
    cache = {}
    path = _cache_path()
    if path.is_file():
        try:
            cache = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            cache = {}

    for slug, base in (state.INSTANCE.get("peers") or {}).items():
        url = str(base).rstrip("/") + "/doc-index.json"
        try:
            with urllib.request.urlopen(url, timeout=_TIMEOUT) as response:
                data = json.loads(response.read().decode("utf-8"))
            cache[slug] = data
            state.PEERS[slug] = data
        except Exception as exc:
            if slug in cache:
                state.PEERS[slug] = cache[slug]
                state.note(
                    "stale_xref",
                    "peer '" + slug + "' unreachable (" + str(exc)
                    + "); using cached index built "
                    + str(cache[slug].get("built", "unknown")),
                )
            else:
                state.note(
                    "stale_xref",
                    "peer '" + slug + "' unreachable (" + str(exc)
                    + ") and no cache exists. Every @" + slug
                    + ": reference will render as broken.",
                )

    if state.PEERS:
        try:
            path.write_text(
                json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        except OSError:
            pass


def on_page_markdown(markdown, page, config, files):
    src = page.file.src_uri

    # The source of every edge recorded below. A page with no `id` cannot be linked
    # TO, but it still links OUT, so its edges are kept under its path rather than
    # dropped -- the missing id is already reported by objects.py, and losing its
    # outbound references here would hide the second problem behind the first.
    src_id = state.BY_SRC.get(src, {}).get("id") or ("path:" + src)

    def replace(match):
        label = match.group("label")
        token = match.group("token")
        anchor = match.group("anchor") or ""
        # Re-emitted by every branch that does not hand it to a handler. See the
        # docstring -- dropping it is a silent regression, not a cosmetic one.
        opts = match.group("opts") or ""

        lowered = token.lower()
        if lowered.endswith(_DATA_SUFFIXES) or lowered.endswith(_IMAGE_SUFFIXES):
            # One mistake, two subsystems. The advice branches because sending
            # somebody chasing a broken picture into the frontmatter `data:` block
            # is the same class of wrong error this refusal exists to prevent.
            if lowered.endswith(_IMAGE_SUFFIXES):
                advice = (
                    "names an IMAGE FILE. Images are reached by NAME, never by "
                    "path: write @img:" + token.rsplit(".", 1)[0] + " instead. The "
                    "name is the filename without its extension, which is what "
                    "lets a png become a webp without touching a single page."
                )
            else:
                advice = (
                    "names a FILE. References point at ids and data slots, never "
                    "at filenames -- that is what makes renaming a file safe. For "
                    "a table use @data:<slot> and declare the filename once in "
                    "`data:` frontmatter."
                )
            state.note("dead_links", src + ": '@" + token + "' " + advice)
            state.ref(src_id, token, "filename", token, False)
            return _dead(
                label, "references point at names, not filenames: " + token
            ) + opts

        if ":" in token:
            prefix, _, rest = token.partition(":")

            handler = prefixes.resolver(prefix)
            if handler:
                # THE CALL SHAPE IS THE HANDLER'S CHOICE, NOT A GUESS MADE HERE.
                # A handler that never opted in is called with three arguments,
                # byte-identically to before 2026-08-09 -- calling it with four
                # would be a TypeError inside a page render, which is a dead site.
                takes = prefixes.takes_anchor(prefix)
                wants_opts = prefixes.takes_opts(prefix)
                if anchor and not takes:
                    # Still dropped for these, and still said out loud. This is now
                    # a genuine statement about the NAMESPACE rather than a blanket
                    # limitation: @data: addresses a whole table and @img: a whole
                    # picture, so a fragment has nowhere to point.
                    state.note(
                        "dead_links",
                        src + ": '@" + token + anchor + "' carries a heading anchor, "
                        + "and the @" + prefix + ": namespace resolves whole targets "
                        + "-- it takes no anchor, so '" + anchor + "' was ignored. "
                        + "The link itself is fine; it lands at the top.",
                    )
                if wants_opts:
                    resolved = handler(rest, page, label, anchor, opts)
                elif takes:
                    resolved = handler(rest, page, label, anchor)
                else:
                    resolved = handler(rest, page, label)
                if resolved is None:
                    state.note(
                        "dead_links",
                        src + ": '@" + token + "' did not resolve. "
                        + prefixes.owner(prefix) + " owns the @" + prefix
                        + ": namespace and does not know '" + rest + "'.",
                    )
                    state.ref(src_id, token, prefix, rest, False)
                    return _dead(label, "unknown " + prefix + ": " + rest) + opts
                state.ref(src_id, token, prefix, rest, True)
                # A handler that took the block OWNS it -- re-emitting here would
                # put a second brace beside the one it just merged, which is the
                # exact two-block collision this argument exists to end.
                return resolved if wants_opts else resolved + opts

            peer = state.PEERS.get(prefix)
            if not peer:
                state.note(
                    "dead_links",
                    src + ": unknown peer site '" + prefix + "'. Reserved prefixes on "
                    + "this build: "
                    + (", ".join(sorted(prefixes.reserved())) or "none") + ".",
                )
                state.ref(src_id, token, "peer", rest, False)
                return _dead(label, "unknown peer site: " + prefix) + opts
            hit = next(
                (c for c in peer.get("pages", []) if c.get("id") == rest), None
            )
            if not hit:
                state.note(
                    "dead_links",
                    src + ": '" + rest + "' not found in peer '" + prefix + "'",
                )
                state.ref(src_id, token, "peer", rest, False)
                return _dead(label, "not found in " + prefix + ": " + rest) + opts
            state.ref(src_id, token, "peer", rest, True)
            base = str(peer.get("base_url", "")).rstrip("/")
            return (
                "[" + label + "](" + base + "/" + str(hit.get("url", "")) + anchor
                + "){ .docrender-xref }" + opts
            )

        hit = state.PAGES.get(token)
        if not hit:
            state.note("dead_links", src + ": no page with id '" + token + "'")
            state.ref(src_id, token, "page", token, False)
            return _dead(label, "no page yet with id: " + token) + opts

        state.ref(src_id, token, "page", token, True)
        # Resolved against THIS page, never from a separator count. The root index
        # page reports its url as `./` and broke that arithmetic.
        target = relative_url(str(hit.get("url", "")), page.file.url)
        return "[" + label + "](" + target + anchor + ")" + opts

    return sub_outside_code(_LINK, replace, markdown)
