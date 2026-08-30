"""The lede, the keywords line, the ownership tag and the revision line. What a
page says around the edges of what it argues.

WHY THE LEDE IS A FIELD AND NOT A POSITION (decided 2026-08-03, Michael).

It used to be defined three times, in three languages, and none of the three
knew the others existed:

    stylesheet   `.md-typeset h1 + p` -- the paragraph ELEMENT after the H1
    engine       the first non-blank run of lines after the `# ` line
    search       everything between the H1 and the next heading

Those three agree perfectly on a page that opens with exactly one paragraph,
and diverge on every page that does not. Nothing checked it, so the divergence
was silent and looked like a styling bug: on a page whose H1 is followed
straight by `## Section`, the old code read the HEADING as the lede and planted
the generated spec table underneath it.

Now it is `summary:`, required on `_base`, rendered here into the slot after the
H1. One definition. The stylesheet targets what this emits instead of guessing
at document shape, and search indexes it because it is genuinely on the page.

⚠️ NO POSITIONAL FALLBACK, and that was the explicit call. "Field wins, a body
paragraph stays legal" was on the table and was REJECTED: a sanctioned fallback
is a fourth definition of the lede, which is the defect this module exists to
remove. A page keeping its lede in the body gets REPORTED, never quietly
absorbed.

THE MIGRATION IS LOUD ON PURPOSE. Every page written before this carries its
lede positionally, so the first build after it ships reports the whole tree.
That is a worklist, not a regression -- nothing fails, nothing stops
publishing, and a page with no `summary:` renders exactly as it did the day
before.

THE KEYWORDS LINE is the same argument pointed at search. `keywords: [genie,
personnel lift]` renders as a visible line at the foot, so the words are indexed
because they are ON THE PAGE rather than injected into an index by a mechanism
nobody can see. A HIDDEN meta block was the rejected option: it cannot be
audited, so it rots silently, and the first symptom is a search that quietly
stopped matching.

⚠️ RENAMED FROM `also_known_as` 2026-08-04, Michael. The old key is reported via
objects.py _LEGACY_KEYS. **The visible label moved with the field on purpose:**
the old name could only honestly hold aliases, and the new one also holds search
terms that are not names, so "Also called: electrics" was about to be false.

🔴 THE REVISION LINE, AND THE FIELD THAT HAD NO READER (2026-08-07, Michael).

`revised:` has been declared optional on `_base` since the type system shipped.
It is documented in the engine README and offered in `_template.md`. AND
NOTHING IN THIS ENGINE EVER READ IT. The date that actually reached a reader
was a line authors typed by hand at the bottom of the page -- so the header key
was decoration and the body line was the only real one, which is precisely the
inverse of what every document describing the field says.

Michael: "whatever string I put in the revised metadata should be automatically
italicized and placed as the very last thing on any page during build time.
That way, it isn't being replicated in two places."

⭐ THE INTERESTING PART IS WHAT THE TWO COPIES DID TO THE VALUE. A field has one
spelling; a typed line has as many as there are authors. Live at the time of
writing, on nine pages: `Aug 2026`, `Aug 2026.`, `Aug 26`, `August 2026.`,
`Jun 2026.`, `May 2026.`, a bare `Revised` carrying no date whatsoever, and one
page shipped public still holding the template's literal `Revised Month Year.`
placeholder. Nothing was broken and nothing reported -- every one of those
rendered perfectly. THE DUPLICATION DID NOT CAUSE A CONTRADICTION, IT CAUSED A
DRIFT, and a drift has no failing build to announce it.

⚠️ THE VALUE RENDERS VERBATIM AND IS DELIBERATELY NOT NORMALISED. `Revised` is
the LABEL this engine supplies, exactly as `Keywords:` is; everything after it
is whatever the field holds. So `revised: 2026-08` renders "Revised 2026-08"
and `revised: Aug 2026` renders "Revised Aug 2026" -- and the two content repos
currently disagree about which of those they write. Parsing a date out of the
string was available and was NOT taken: this is provenance typed by a human,
and an engine that reformats it starts owning a calendar it cannot verify. If
one house spelling is wanted, that is a content decision, and the field being
singular is what finally makes the disagreement countable.

⚠️ THE ITALIC IS AN `<em>` IN THE MARKUP RATHER THAN `font-style` IN THE
STYLESHEET. Italic was the REQUEST rather than a styling choice, so it should
survive print.css, a stylesheet that failed to load, and anything that reads
this HTML without our CSS. base.css owns the size, colour and spacing of the
line and nothing else. Do not tidy the `<em>` away into a rule.

=============================================================================
🔴 THE OWNERSHIP TAG (2026-08-30, Michael) -- ONE FOOTER LINE, TWO ENDS
=============================================================================
    Revised Fall 2026                      Posted by Michael A Wizorek
                                        michael.wizorek@rochester.edu

> Michael: *"something more general and global so I don't have to worry about
> adding it to every page ... if someone sees this printed on a desk and is
> curious about it, they need to know where it came from and who to contact."*

And, after v1 stacked it as its own line ABOVE the date and rewrote the revised
rule to match: *"Leave the revised function and position and font and size
exactly the same on the left side of the footer ... No stacking ... don't
fucking move or change revised."* ⚑ *A request to ADD a line was executed as a
redesign of the line already there.*

⭐ TWO LINES, NAME OVER ADDRESS, BOTH FLUSH RIGHT (v3, matched to Michael's own
mock-up rather than inferred). The `·` separator is GONE and a `<br>` replaces
it: with the pair set right, a middot left hanging at the end of the first line
is exactly the fussiness a provenance stamp should not have. `foot.css` carries
the `text-align: right` that keeps the second line flush.

🔴 EMITTED **AFTER** THE REVISION LINE, WHICH IS THE OPPOSITE OF WHAT IT LOOKS
LIKE IT SHOULD BE. It renders ON that line, floated right and pulled up by a
negative margin, and the pull is CONSTANT only when it hangs off revised's own
bottom -- so `objects.py` writes it last. Swapping those two statements makes it
stack again. **STYLING AND THE FULL MEASURED ARGUMENT LIVE IN `assets/foot.css`**
§ THE OWNERSHIP TAG, including why the rule is there rather than in base.css and
which single value to adjust if the browser disagrees with the print engine.
This function only makes the element.

🔴 IT IS DRAWN FROM THE INSTANCE, NOT FROM FRONTMATTER, AND THAT IS THE OTHER
HALF OF THE REQUEST. Every other line this module renders is a per-page field.
This one is authored ONCE in `instances/<slug>/site.yml` and lands on every page
of that site with no page edit anywhere -- which is what "general and global"
means, and it matters more than it looks: the safety content repo is one agents
may never commit to, so a `posted_by:` frontmatter key would have meant Michael
hand-editing every file in the tree, forever. Same polarity as `print:` and
`routes.yml`: **absent means the line does not render**, so five of six sites are
untouched by this landing.

⚠️ SO `owner()` BREAKS THE ONE THING THE FOUR FUNCTIONS ABOVE IT HAVE IN COMMON,
and it is named rather than smuggled. The closing note below says what they share
is being "drawn from frontmatter on EVERY page regardless of type." This one is
drawn from CONFIG. It lives here because it is the same foot-of-page furniture
class and renders into the same block -- and because objects.py had ~280 B of
headroom against the 22,528 B read ceiling, so a function there would have
breached it. 🚩 Its own module needs a hook registration in `mkdocs.yml` (28,158 B,
unwritable whole). Debt, stated.

⚠️ THE LABEL IS ENGINE-SUPPLIED, exactly as `Revised` and `Keywords:` are. The
config holds a name and an address; it does not hold the word "Posted". That is
what keeps the phrasing identical across every sheet in a printed packet, which
was the point of making the tag global rather than typed.

⚠️ THE ADDRESS IS A REAL `mailto:` ANCHOR AND THAT IS A DELIBERATE ASYMMETRY.
On screen it is a live control; on paper it renders as plain text, because
`print-type.css` §5 strips link colour and paper has no click. A contact line
you cannot contact from the screen is the DEAD CONTROL shape this engine kills
on sight. ✅ AND IT IS NOW VERIFIED RATHER THAN ASSUMED: the built HTML on
`gh-pages` carries `<a href="mailto:...">` intact with no decoration, so
`urllinks.py` and `links.py` leave a raw anchor alone. The v2 fallback (drop the
anchor, emit text) is therefore retired, not merely unused.

⚠️ NO HTML-ESCAPING OF THE ADDRESS, AND IT IS A JUDGEMENT NOT AN OVERSIGHT. The
value comes from a config file only Michael writes. If this ever reads from
anything a third party can write, escape it there and not here.

🚩 AND THE TAG CLAIMS MAINTENANCE IT CANNOT PROVE. It renders unconditionally
while `revised:` stays optional, so a page with no date carries a named owner and
no evidence anybody has looked at it since. Raised 2026-08-30 and deferred by
Michael to the revision-log conversation -- **explicitly not this feature's job.**
Recorded so it is not read as solved.

⚠️ THIS MODULE IS NAMED FOR THE LEDE AND NOW HOLDS FOUR FOOT-OF-PAGE LINES.
That mismatch is known and is not worth a rename today: what these functions
share is that they are drawn from frontmatter -- or, in `owner()`'s case, from
config -- on EVERY page regardless of type, which is a real thing to have in
common and is the reason objects.py calls all of them from the same few lines.
Named so the next reader does not file it as an accident.
"""

from __future__ import annotations

import re

_H1 = "# "

#: A list item opening a block. Up to three spaces of indent, which is all
#: Python-Markdown allows before it stops being a list at all.
_LIST_ITEM = re.compile(r"^ {0,3}(?:[-*+][ \t]|\d+[.)][ \t])")

#: A Material callout or collapsible: `!!! danger`, `??? note`.
_CALLOUT = re.compile(r"^ {0,3}(?:!!!|\?\?\?)")

#: A hand-typed revision line at the foot of a page: `*Revised Aug 2026.*`,
#: `_Revised May 2026_`, or the bare word.
#:
#: ⚠️ ANCHORED AT THE START OF THE LINE, WITH ONLY EMPHASIS ALLOWED IN FRONT,
#: and that is the whole of its precision. A sentence that MENTIONS a revision
#: -- "source: PPE Program.docx, last revised 13 August 2025" -- is prose about
#: a different document and is none of this field's business. Matching the word
#: anywhere on a line would have swept that up and told its author to delete a
#: sentence carrying provenance the frontmatter cannot hold.
_REVISED_LINE = re.compile(r"^\s*[*_]{0,2}\s*Revised\b", re.IGNORECASE)


def _find_h1(lines: list[str]) -> int | None:
    return next((i for i, ln in enumerate(lines) if ln.startswith(_H1)), None)


def _clip(text: str, limit: int = 60) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "..."


def classify(body: str) -> tuple[str, str]:
    """What the first block after the H1 IS, and what it says.

    Returns one of `no_h1` `empty` `paragraph` `heading` `callout` `list`
    `table` `html`, plus that block's text where there is any.

    It classifies rather than answering yes/no because 'no lede found' is the
    same sentence for a page that opens with a table and a page with no body,
    and those are different jobs for whoever has to fix it.
    """
    lines = body.splitlines()
    h1 = _find_h1(lines)
    if h1 is None:
        return "no_h1", ""

    i = h1 + 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines):
        return "empty", ""

    first = lines[i]
    stripped = first.lstrip()
    if stripped.startswith("#"):
        return "heading", stripped
    if _CALLOUT.match(first):
        return "callout", stripped
    if _LIST_ITEM.match(first):
        return "list", stripped
    if stripped.startswith("|"):
        return "table", stripped
    if stripped.startswith("<"):
        return "html", stripped

    run = []
    while i < len(lines) and lines[i].strip():
        run.append(lines[i].strip())
        i += 1
    return "paragraph", " ".join(run)


def check(src: str, meta: dict, body: str, note) -> None:
    """Report a page whose lede is not where the field says it is.

    Runs in hook 01, on EVERY page including hidden ones, for the same reason
    the rest of that hook does: a page is broken or not regardless of whether
    it happens to be published today.

    A missing `summary:` is already reported by the required-field check. What
    is added here is WHERE THE TEXT IS -- the difference between a lede that
    needs moving and a lede that has to be written.
    """
    summary = str(meta.get("summary") or "").strip()
    kind, text = classify(body)

    if kind == "no_h1":
        note(
            "body_lede",
            src + ": no `# ` heading. There is nowhere to render the lede, so "
            + "`summary:` is dropped even if it is set, and the page has no "
            + "title in its own body.",
        )
        return

    if summary and kind == "paragraph":
        note(
            "body_lede",
            src + ": has BOTH `summary:` and a paragraph under the H1. The "
            + "field is the lede; that paragraph now renders as ordinary body "
            + 'text directly beneath it, usually saying the same thing twice '
            + '-- "' + _clip(text) + '"',
        )
        return

    if kind == "paragraph":
        note(
            "body_lede",
            src + ": lede is still in the BODY. Move it into `summary:` and "
            + 'delete the paragraph -- "' + _clip(text) + '"',
        )
        return

    if not summary:
        note(
            "body_lede",
            src + ": no `summary:`, and no paragraph under the H1 to migrate "
            + "(found " + kind + "). This lede has to be WRITTEN, not moved. "
            + "Until it is, the page's search result shows no text at all.",
        )


def check_revised(src: str, meta: dict, body: str, note) -> None:
    """Report a page still typing its revision date into the body.

    ONLY THE LAST THREE NON-BLANK LINES ARE EXAMINED. The thing being hunted is
    a FOOTER, and the cost of widening the search is not a false positive in
    the abstract -- it is telling somebody to delete a real sentence. See
    _REVISED_LINE.

    The two cases are reported separately because they are different jobs. A
    page carrying BOTH now prints its date twice and the fix is a deletion; a
    page carrying only the body line has nothing in the field yet and the fix
    is a move. One message for both would have sent half the tree looking for
    a duplicate that is not there.

    Same posture as `check` above: runs on hidden pages too, nothing fails,
    nothing stops publishing, and a page that has already moved says nothing.
    """
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    found = next(
        (ln for ln in reversed(lines[-3:]) if _REVISED_LINE.match(ln)), ""
    )
    if not found:
        return

    field = str(meta.get("revised") or "").strip()
    if field:
        note(
            "body_revised",
            src + ": has BOTH `revised: " + field + "` and a hand-typed "
            + '"' + _clip(found) + '" at the foot. The field is drawn at the '
            + "bottom of the page now, so this one prints the revision date "
            + "twice. Delete the body line.",
        )
        return

    note(
        "body_revised",
        src + ": revision date is still in the BODY -- "
        + '"' + _clip(found) + '". Move it into `revised:` and delete the '
        + "line. The engine draws it at the foot, in italic, from the field.",
    )


def render(markdown: str, summary) -> str:
    """Put the summary in the slot immediately after the H1.

    Emitted as a real element with a class rather than as a bare paragraph, so
    the stylesheet can target what the engine MADE instead of inferring the
    lede from document shape a third time.
    """
    text = " ".join(str(summary).split())
    if not text:
        return markdown

    lines = markdown.splitlines()
    h1 = _find_h1(lines)
    if h1 is None:
        # Nothing to anchor to. `check` reports it; nothing is invented here.
        # Guessing a position for generated content is exactly how a spec
        # table ended up inside somebody's first section.
        return markdown

    block = '<p class="dr-lede" markdown="1">' + text + "</p>"
    return "\n".join(lines[: h1 + 1] + ["", block] + lines[h1 + 1 :])


def keywords(value) -> str:
    """The keywords line. VISIBLE, which is the whole point of it.

    Accepts a list or a comma-separated string, because both are what people
    actually type and refusing one of them buys nothing.

    ⚠️ The emitted class is `dr-aka`, not `dr-keywords`. See the module
    docstring: the stylesheet that would have to change sits near the read-clip
    line, and that is a worse risk than one stale internal name.
    """
    if value in (None, "", [], {}):
        return ""
    if isinstance(value, str):
        names = value.split(",")
    else:
        names = [str(v) for v in value]
    names = [" ".join(n.split()) for n in names]
    names = [n for n in names if n]
    if not names:
        return ""
    return '<p class="dr-aka">Keywords: ' + ", ".join(names) + "</p>"


def owner(value) -> str:
    """The ownership tag: name over address, flush right of `revised`.

    Takes the `owner:` mapping off the INSTANCE -- `{name, email}` -- and not a
    frontmatter field. The caller reads `state.INSTANCE`; this function stays
    pure, same bargain as `keywords` and `revised`, so it can be reasoned about
    without a build. Layout is `assets/foot.css`; the emit-order rule it depends
    on is in the module docstring and in objects.py beside the call.

    ⭐ THE `<br>` IS THE SHAPE, NOT A FALLBACK FOR WRAPPING. Two deliberate lines
    (v3, from Michael's mock-up), so the break does not move with the viewport
    and the address always starts a line of its own. A `·` separator was v1/v2
    and is retired: set flush right, it left a middot dangling at a line end.

    THE NAME IS THE ONLY REQUIRED HALF. A site declaring an address and no name
    renders nothing rather than `Posted by · someone@x` -- a label with no
    subject is worse than an absent line, and the absent line is already the
    documented default for five of six sites.

    ⚠️ A STRING IS ACCEPTED AS THE NAME. `owner: Michael A Wizorek` is what
    somebody will type on the first site that copies this, and refusing it buys
    nothing -- it renders the tag with no address, which is exactly what was
    written. Same posture as `keywords` taking a bare string.
    """
    if value in (None, "", [], {}):
        return ""
    if isinstance(value, str):
        name, email = " ".join(value.split()), ""
    else:
        name = " ".join(str(value.get("name") or "").split())
        email = " ".join(str(value.get("email") or "").split())
    if not name:
        return ""

    line = "Posted by " + name
    if email:
        line += (
            "<br>" + '<a href="mailto:' + email + '">' + email + "</a>"
        )
    return '<p class="dr-owner">' + line + "</p>"


def revised(value) -> str:
    """The revision line. The last thing the DOCUMENT says, and italic.

    Same bargain as `keywords` above: the field is the only copy, the engine
    draws it, and an author never types it. The module docstring carries why
    the value is passed through verbatim and why the italic is markup rather
    than a stylesheet rule.

    🔴 UNCHANGED BY THE OWNERSHIP TAG, BY RULING (Michael, 2026-08-30: *"don't
    fucking move or change revised"*). This function, its label, its `<em>` and
    its base.css rule are byte-identical to what they were before the tag
    existed. The tag renders beside it and touches none of this.

    ⚠️ `str(value)` RATHER THAN AN ISINSTANCE LADDER, and it is load-bearing.
    YAML resolves `revised: 2026-08` to a string and `revised: 2026-08-07` to a
    `datetime.date`, silently, on a difference of three characters. Both have
    to render, so both get stringified -- a type check here would have made a
    fully-specified date the one value that vanished.
    """
    text = " ".join(str(value or "").split())
    if not text:
        return ""
    return '<p class="dr-revised"><em>Revised ' + text + "</em></p>"


def insert_after(markdown: str, block: str) -> str:
    """Place generated content after the H1 and the lede.

    Moved here from objects.py unchanged: it is a function about the lede, and
    it was the biggest thing in that file that was not about types.

    Anything it cannot parse confidently goes at the TOP rather than being
    placed on a guess, because a wrong guess splits a sentence in half.
    """
    lines = markdown.splitlines()
    h1 = _find_h1(lines)
    if h1 is None:
        return block + "\n" + markdown
    i = h1 + 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    while i < len(lines) and lines[i].strip():
        i += 1
    return "\n".join(lines[:i] + ["", block] + lines[i:])
