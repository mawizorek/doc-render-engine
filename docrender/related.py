"""`related:` -- the fourth foot-of-page field, and the THIRD one that was
declared and read by nothing.

Michael, 2026-08-19: *"does `related: [page-id]` render anywhere on a page if
used in the frontmatter?"* It did not. `objects/_base.yml` has offered it since
the type system shipped, with the note *"ids, not paths"*, and no module in this
engine ever looked at it.

🔴 THIS IS THE SAME BUG AS `revised:`, TWELVE DAYS LATER, AND lede.py ALREADY
WROTE THE POST-MORTEM. From its own docstring: *"`revised:` has been declared
optional on `_base` since the type system shipped. It is documented in the engine
README and offered in `_template.md`. AND NOTHING IN THIS ENGINE EVER READ IT."*
Fixed 08-07. ⚑ A field is only as live as its READER, and a declaration is not a
reader -- `objects.py` validates `requires` and never once looks at `optional`,
which its own comment says out loud. So every key in that list is a promise
nobody checks, and the only way to know which ones are real is to grep for a
consumer.

⚠️ AND THE COST WAS ALREADY VISIBLE, WHICH IS THE PART WORTH RECORDING. Every
policy page in `uritp-safety` hand-types a `## Related` block -- *"Part of
General Safety for All"*, *"Reporting Incidents"* -- exactly as nine pages
hand-typed their revision date into seven different spellings. The duplication
did not produce a contradiction, it produced a DRIFT, and a drift has no failing
build to announce it.

=============================================================================
WHERE IT LANDS, AND WHY THAT IS A RULING RATHER THAN A DEFAULT
=============================================================================
Michael: *"should land above 'revised' line tho."*

The foot of a page now reads, top to bottom:

    the document
    ## In this section     a contents list, if the type draws one
    Related                THIS
    Keywords:              search terms
    <em>Revised ...</em>   the last thing the DOCUMENT says
    ---                    hook 06's rule
    Edit this page         scaffolding

⭐ THE ORDERING IS A GRADIENT FROM CONTENT TO METADATA and every boundary in it
was argued somewhere else: `objects.py` put the contents list at the foot because
a list of links above the prose turns a hub into a menu; `lede.py` made `revised`
last because Michael called it *"the very last thing on any page"*; hook 06's
rule is the seam where the document stops and the scaffolding starts. **Related
links are the most CONTENT-like of the three foot fields** -- they are places to
go next, which is a reader's business -- so they sit highest.

=============================================================================
🔴 IT EMITS `@id` TOKENS AND MUST BE CALLED FROM HOOK 01, NOT LATER
=============================================================================
The list is rendered as `[Title](@some-id)` and handed to stage 03 to resolve,
which is not a convenience -- it is the only correct choice, and it buys three
things no local resolution could:

  1. **links.py records the edge in `state.REFS`**, so a `related:` entry becomes
     a real edge in `/doc-refs.json` rather than a link that merely works.
     Hand-typed `## Related` blocks already did this; a locally-resolved URL
     would have SILENTLY REMOVED that graph edge while looking like an upgrade.
  2. **a dead id renders as the struck broken-reference marker** and lands in the
     report, by the same path as every other reference on the site.
  3. **relative-URL arithmetic stays in exactly one place.** `util.relative_url`
     exists because counting separators was wrong on precisely one page per site
     -- the landing page, the most-linked-from page there is.

⚠️ SO THE TITLE COMES FROM `state.BY_SRC`, NOT FROM `state.PAGES`. BY_SRC is
populated in this same hook, before visibility prunes anything, while PAGES is
filled at stage 03 and does not exist yet when this runs. 🚫 Do not "fix" this by
checking PAGES for publication -- it is empty here, every id would look dead, and
the whole list would vanish. Publication is links.py's call and it already makes
it loudly.

=============================================================================
⚠️ WHAT IT DELIBERATELY DOES NOT DO
=============================================================================
🚫 **NOT SYMMETRIC.** `A related: [B]` does not put A on B's page. Inverting the
graph is exactly what `/doc-refs.json` already publishes (`referenced_by`), and
rendering the inverse would mean a page's foot changing because somebody edited a
different file -- which no author could predict and no diff would show.

🚫 **NO DEDUPE AGAINST THE BODY.** `_child_list` skips children the prose already
links, and that is right for a generated INVENTORY: the list is whatever is left
over. `related:` is not an inventory, it is an ASSERTION -- the author said these
things are related -- so it renders what it was given. If a page links something
in prose AND lists it here, that is two statements, not a duplicate.

🚫 **NO CSS.** `.dr-related` is emitted and styled by nothing, matching `dr-aka`'s
shape so it inherits the same foot-of-page typography. Registering a stylesheet
means editing `assets.py`, which is 22,426 B and OVER the ~22KB read ceiling --
rewriting a file that cannot be read whole is how `util.py` lost `relative_url`
and every build died on ImportError. ⚠️ Named as a real limit rather than a
choice: this line cannot be restyled until that file is split.

⚠️ **ONE STRING IS ACCEPTED AS WELL AS A LIST**, matching `keywords()` one
function over. `related: policy-fire` is what somebody types for a single entry,
and refusing it buys nothing but a support question.
"""

from __future__ import annotations

from . import state
from .util import slug_title

#: The visible label. `Related` rather than `Related pages` or `See also`, to
#: match the `## Related` heading the content repos already hand-type -- the
#: migration reads as a promotion rather than as a rename.
_LABEL = "Related"


def _ids(value) -> list[str]:
    """Normalise the field to a list of ids, in declared order.

    ORDER IS PRESERVED AND NOT SORTED. `keywords:` is a bag of search terms and
    `_child_list` sorts to agree with the sidebar, but this is a sequence an
    author chose -- the first entry is usually the parent program or the page you
    actually want next. Sorting it alphabetically would throw that away silently.

    A leading `@` is stripped so both `policy-fire` and `@policy-fire` work; the
    field's own note says *ids, not paths*, and somebody pasting from a link is
    the obvious way the sigil arrives.
    """
    if value in (None, "", [], {}):
        return []
    raw = value.split(",") if isinstance(value, str) else list(value)
    out, seen = [], set()
    for item in raw:
        pid = str(item).strip().lstrip("@")
        if pid and pid not in seen:
            seen.add(pid)
            out.append(pid)
    return out


def _title(page_id: str) -> str:
    """The title to show for an id, from frontmatter read in this same hook.

    Falls back to a prettified slug rather than to the bare id, matching
    `_child_list`. ⚠️ AND IT DOES NOT DECLINE ON AN UNKNOWN ID: the link is still
    emitted as `@id`, so links.py reports it dead and renders the struck marker.
    Skipping it here would remove the evidence and leave the author with a
    shorter list and no explanation.
    """
    for src, meta in state.BY_SRC.items():
        if str((meta or {}).get("id") or "").strip() == page_id:
            return str((meta or {}).get("title") or slug_title(page_id))
    return slug_title(page_id)


def render(value) -> str:
    """The Related line, as markdown for stage 03 to resolve. "" if empty.

    A `<p>` of comma-separated links rather than a bulleted list, deliberately:
    this sits in a stack of three quiet foot-of-page lines beside `Keywords:` and
    `Revised`, and a bulleted list there reads as new CONTENT after the document
    has ended. The hand-typed blocks it replaces were `## Related` headings with
    bullets, which is precisely why they looked like a section.

    ⚠️ `markdown="1"` IS LOAD-BEARING. Without it Python-Markdown treats the
    contents of a raw HTML block as literal text, and every `[Title](@id)` inside
    would ship to the reader as source. Same reason `lede.render` carries it, and
    it only works because `md_in_html` is enabled in mkdocs.yml -- which
    figure.py's comment already flags as load-bearing rather than convenience.
    """
    ids = _ids(value)
    if not ids:
        return ""
    links = ["[" + _title(pid) + "](@" + pid + ")" for pid in ids]
    return (
        '<p class="dr-related" markdown="1">' + _LABEL + ": "
        + ", ".join(links) + "</p>"
    )


def check(src: str, meta: dict, body: str, note) -> None:
    """Report a page still hand-typing a `## Related` heading.

    Same posture and same purpose as `lede.check_revised`: the field is now the
    only copy, so a page carrying both prints its related links twice. Reported,
    never rewritten -- the body block may hold prose the field cannot ('Part of
    X' is a sentence, not a link list), so deleting it is the author's call.

    ⚠️ A HEADING IS THE SIGNAL, NOT THE WORD. `_REVISED_LINE` next door is
    anchored for exactly this reason: matching "related" anywhere on a line would
    sweep up ordinary prose about a related production and tell somebody to
    delete a real sentence.
    """
    heading = ""
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        text = stripped.lstrip("#").strip().lower().rstrip(":")
        if text in ("related", "see also", "related pages"):
            heading = stripped
            break
    if not heading:
        return

    field = _ids(meta.get("related"))
    if field:
        note(
            "body_related",
            src + ': has BOTH `related:` (' + ", ".join(field) + ') and a '
            + 'hand-typed "' + heading + '" heading. The field is drawn at the '
            "foot now, above the Keywords and Revised lines, so this page "
            "lists its related pages twice. Delete the body block, or keep it "
            "if it carries prose the field cannot.",
        )
        return

    note(
        "body_related",
        src + ': related pages are still in the BODY -- "' + heading + '". Move '
        "the ids into `related:` and delete the block. The engine draws them at "
        "the foot, resolved by id, so a link cannot rot when a page moves.",
    )
