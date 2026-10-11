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
    ### In this section     a contents list, if the type draws one
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
PER-EDGE LOCAL TEXT: `- id: text`, AND WHY NOT THE DESTINATION'S `gloss:`
=============================================================================
Michael, 2026-10-11: *"this is why I want the feature to do custom local related
text but you were skimping on that feature for built in details."*

⭐ THE MIGRATION IS WHAT PROVED IT, AND IT WAS NOT A PREFERENCE. Sweeping the
thirteen `## Related` blocks in `template-docs` found 38 entries, and 25 OF THEM
CARRIED A TRAILING NOTE. Moving the ids into a bare list would have deleted two
thirds of the content of the blocks it replaced, and called it a migration.

🔴 `linklabels.py` ALREADY OFFERS `gloss:` AND `gloss_from_summary:`, AND
REACHING FOR THOSE FIRST WAS THE WRONG INSTINCT -- it answered "what is already
built" instead of "what is being said." A gloss belongs to the DESTINATION and
says one thing on every page that links it. These notes belong to the SOURCE and
say why THIS page is pointing THERE. The repo's own content proves the two are
not the same field:

  * `markers.md` describes Routers as *"the other inline tool, for routing rather
    than confidence"*. `routers.md` describes Markers as *"the other inline tool,
    for confidence rather than routing"*. ⚑ THE SAME EDGE, WRITTEN IN OPPOSITE
    DIRECTIONS. No single gloss on either destination can say both, and a gloss
    that tried would be wrong on one of the two pages.
  * `frontmatter` is pointed at by four pages and described four ways: *"the
    header contract, and the away-from-the-page rule"*, *"the block at the top,
    and what may go in it"*, *"where required fields are declared"*, *"where
    `status:` lives"*. Each is correct for its own page. Flattening them to one
    destination gloss loses four true statements to keep one.

⚠️ AND THIS DOES NOT RE-OPEN hoverspan.py R2, WHICH REFUSES `{hover=}` ON A PAGE
LINK AS *"a second copy free to drift"*. That refusal is sound because a hover on
a page link restates the destination's `summary:` -- two copies of one fact, and
the copy rots. There is no first copy here. The destination's `summary:`
describes the page; this describes the RELATION, which no other field in the
engine holds. ⚑ Drift needs two statements of the same fact, and a relation
asserted by one page is not a fact the destination ever stated.

THE SHAPE. A single-key mapping per entry, because YAML already has one:

    related:
      - frontmatter: the header contract, and the away-from-the-page rule
      - writing: the inline syntax in full
      - audit

⭐ BARE STRINGS STILL PARSE, MIXED LISTS PARSE, and a list with no notes renders
BYTE-IDENTICAL output to what it rendered before this change. That is the whole
reason for choosing the mapping over an `- id:` / `- text:` pair or an inline
`id | text` separator: 23 pages in `uritp-docs` are already on the bare form and
none of them had to be touched. ⚠️ Quote the text if it contains a colon --
`- links: "`@data:` mentions, and every other reference form"` -- which is YAML's
rule, not ours, and the one real sharp edge in the syntax.

IT RENDERS AS A PARENTHETICAL, STILL ONE `<p>`, STILL ONE ELEMENT. 🚫 The
obvious alternative -- switch to a bulleted list once any entry carries text --
was considered and refused twice over. It would rebuild the `## Related` SECTION
this field exists to retire, three lines below the end of the document; and a
nested `<ul>` inside a `markdown="1"` block needs its own per-child attributes
under `md_in_html`, which this engine has never shipped and would be discovered
broken in a published build rather than here. ⚠️ Named as a known cost: a long
note on six entries makes a long line, and it cannot be given its own
typography until `assets.py` is split -- same limit as the next paragraph.

=============================================================================
⚠️ WHAT IT DELIBERATELY DOES NOT DO
=============================================================================
🚫 **NOT SYMMETRIC.** `A related: [B]` does not put A on B's page. Inverting the
graph is exactly what `/doc-refs.json` already publishes (`referenced_by`), and
rendering the inverse would mean a page's foot changing because somebody edited a
different file -- which no author could predict and no diff would show. ⭐ The
per-edge text above is the second argument for this, arriving seven weeks later:
the note is written FROM one side, so an inverted edge would print a sentence
about the wrong page.

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


def _entries(value) -> list[tuple[str, str]]:
    """Normalise the field to `(id, local_text)` pairs, in declared order.

    ORDER IS PRESERVED AND NOT SORTED. `keywords:` is a bag of search terms and
    `_child_list` sorts to agree with the sidebar, but this is a sequence an
    author chose -- the first entry is usually the parent program or the page you
    actually want next. Sorting it alphabetically would throw that away silently.

    A leading `@` is stripped so both `policy-fire` and `@policy-fire` work; the
    field's own note says *ids, not paths*, and somebody pasting from a link is
    the obvious way the sigil arrives.

    ⭐ FOUR SHAPES PARSE, AND THE PAIR IS THE POINT: a bare string, a list of
    bare strings, a list of single-key mappings, and any mix of the last two.
    Every entry comes back as a pair, with `""` for the ones that carry no text,
    so one code path serves both forms and the old form cannot take a different
    route through `render`.

    ⚠️ A MULTI-KEY MAPPING IS READ AS SEVERAL ENTRIES RATHER THAN REFUSED. The
    only way to type one is to forget a dash, and the forgiving reading loses
    nothing while refusing it would silently drop a real link. Same posture as
    accepting the bare string: strictness here buys a support question.
    """
    if value in (None, "", [], {}):
        return []
    if isinstance(value, str):
        raw: list = value.split(",")
    elif isinstance(value, dict):
        raw = [value]
    else:
        raw = list(value)

    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for item in raw:
        pairs = list(item.items()) if isinstance(item, dict) else [(item, "")]
        for key, text in pairs:
            pid = str(key).strip().lstrip("@")
            if not pid or pid in seen:
                continue
            seen.add(pid)
            # Collapse whitespace: YAML folds a wrapped value onto one line with
            # a newline, and these notes wrap in the source blocks they came from.
            out.append((pid, " ".join(str(text or "").split())))
    return out


def _ids(value) -> list[str]:
    """Just the ids, for the places that only need to know WHICH pages.

    `check()` reports a page carrying both the field and a body heading and names
    the ids it found; the local text is not its business. Kept as a named wrapper
    rather than inlined so the report's phrasing cannot drift from the renderer's
    parse.
    """
    return [pid for pid, _ in _entries(value)]


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

    ⭐ LOCAL TEXT IS A PARENTHETICAL INSIDE THAT SAME LINE, and the parentheses
    are load-bearing rather than decorative: the separator between entries is a
    comma, several of these notes contain commas, and without a bracket the
    reader cannot tell where one entry stops. 🚫 Do not "tidy" them into an
    em dash or a colon for the same reason.

    ⚠️ `markdown="1"` IS LOAD-BEARING. Without it Python-Markdown treats the
    contents of a raw HTML block as literal text, and every `[Title](@id)` inside
    would ship to the reader as source. Same reason `lede.render` carries it, and
    it only works because `md_in_html` is enabled in mkdocs.yml -- which
    figure.py's comment already flags as load-bearing rather than convenience.
    ⭐ It now also carries the notes themselves, so inline code and emphasis
    inside a note render as markdown and not as source.
    """
    entries = _entries(value)
    if not entries:
        return ""
    parts = []
    for pid, text in entries:
        part = "[" + _title(pid) + "](@" + pid + ")"
        if text:
            part += " (" + text + ")"
        parts.append(part)
    return (
        '<p class="dr-related" markdown="1">' + _LABEL + ": "
        + ", ".join(parts) + "</p>"
    )


def check(src: str, meta: dict, body: str, note) -> None:
    """Report a page still hand-typing a `## Related` heading.

    Same posture and same purpose as `lede.check_revised`: the field is now the
    only copy, so a page carrying both prints its related links twice. Reported,
    never rewritten -- the body block may hold prose the field cannot ('Part of
    X' is a sentence, not a link list), so deleting it is the author's call.

    ⚠️ THE 'PROSE THE FIELD CANNOT HOLD' ESCAPE NARROWED ON 2026-10-11. A
    trailing note per entry now moves into the field with its link, so a block of
    `- [Title](@id) -- why` bullets no longer has anything the field cannot take.
    What is left is genuinely only full sentences and paragraphs. ⚑ The report
    still does not rewrite, because telling the two apart is reading, not matching.

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
        "the foot, resolved by id, so a link cannot rot when a page moves. A "
        "trailing note per bullet comes too, as `- id: why this page points "
        "there`.",
    )
