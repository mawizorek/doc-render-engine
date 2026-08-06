"""Stage 04b -- ROUTERS. A pause, or a door to somewhere else.

WHY decisions here are the way they are: the doc-render-engine Decision Log.
This docstring is the CONTRACT and is deliberately kept under the warn line.
The crypto lives in `docrender/seal.py`, which pairs with `assets/router.js`.

=============================================================================
THE FRONTMATTER KEYS, and how they relate to `status:`
=============================================================================

    status:          REQUIRED on every page, and NOTHING to do with routers.
                     It decides whether the page is BUILT and whether it is
                     LISTED. See docrender/visibility.py.

    router:          name of a table in instances/<slug>/routes.yml, or a LIST
                     of table names (REMOTE)
    router_code:     a code, or a list of them, written right here (LOCAL)
    router_prompt:   the label above the field. Optional, and does NOTHING on
                     its own -- decoration for a router, not a router.
    router_inherit:  `false` on a page opts it out of a folder's cascade.

A router does not gate anything and `status:` does not know it exists. Status
decides what REACHES the site; a router decides what a reader sees FIRST once
they are there. A `hidden` page with a router is still not built; a `public`
page with a curtain is still fully public.

=============================================================================
EVERY SOURCE OF KEYS POOLS. REPEATING A FRONTMATTER KEY DOES NOT.
=============================================================================
    router: [pm, staff, guests]      # three REMOTE tables
    router_code: [tryme, temp26]     # plus two LOCAL codes -- all five pool

⚠️ WHAT DOES NOT WORK IS WRITING THE SAME KEY TWICE. `router:` on two lines is
YAML keeping the LAST value, silently. Use a list. objects.py reports duplicate
frontmatter keys FIRST because the symptom ("only one of my tables works")
looks nothing like the cause.

A key defined in two different tables is reported and the FIRST table wins.
Letting dict order decide would make the winner depend on the order somebody
happened to type two unrelated files in.

=============================================================================
LOCAL VS REMOTE
=============================================================================
LOCAL -- `router_code:` in the page. Throwaway, no engine deploy.
REMOTE -- a table in `instances/<slug>/routes.yml`. Durable, one place to edit,
and the only form that can send somebody to a DIFFERENT page.

⚠️ A LOCAL CODE IS IN THE CONTENT REPO. Fine for a pause, wrong for anything you
would mind a stranger typing. Local is for trash; remote is for real.

=============================================================================
THREE KINDS OF ENTRY, and the DESTINATION decides which -- never a mode flag
=============================================================================

    maw:                    -> PORTABLE CURTAIN. No destination, so it means
                               "curtain on whatever page declares this table."
                               One entry, reusable on any number of pages,
                               never needs to know their ids. The form that
                               makes a cascade useful.

    staff26: staff          -> PINNED CURTAIN. Names the id of the page it is
                               used on. Same behaviour, tied to one page.

    loadin24: crew-sheet    -> REDIRECT. Names a different page; sends you
                               there.

⚠️ A PINNED curtain does NOT cascade usefully: inherited by a child, its id no
longer matches, so it is read as a redirect BACK to the folder index. Coherent,
rarely wanted. Use the portable form on any table you expect to inherit.

=============================================================================
A ROUTER ON A FOLDER'S index.md CASCADES TO EVERYTHING UNDER IT
=============================================================================
    production/staff/index.md      router: pm     <- declared once
    production/staff/props.md                     <- inherits it

The NEAREST ancestor wins, so a subfolder redeclaring OVERRIDES rather than
stacks. A page opts out with `router_inherit: false`. A folder is the unit
people think in, and a pause that only covers the folder's front page is one a
reader steps around by clicking any child.

🔴 THIS DID NOT WORK FOR A DIRECT CHILD UNTIL 2026-08-03, and the example above
is the case it got wrong: `_inherited` began its walk at the GRANDPARENT, so it
never read the one folder index the feature exists for. `parts[:depth - 1]`
where `parts[:depth]` was meant, guarded by a comment confidently explaining a
different off-by-one. Now an explicit list of ancestor paths, because index
arithmetic is what made a wrong answer look deliberate.

=============================================================================
THE CASCADE TAKES THE SIDEBAR WITH IT (DL J14, 2026-08-04)
=============================================================================
visibility.py strips a routed folder's subtree out of the nav at stage 00b and
stashes it in `state.NAV_SEALED`. This file seals that manifest with `seal.wrap`,
under EVERY code that opens the curtain and no others, and ships it as
`data-subtree`. A correct code decrypts it and router.js injects the entries.

⚠️ A REDIRECT CODE NEVER UNSEALS THE NAV. It does not reveal this page, so it
has no business revealing this page's children -- which is why curtain codes
are collected separately below rather than read back off the verifiers.

⭐ AND SINCE 2026-08-06 THE FOLDER'S OWN ROW CAN BE IN THAT MANIFEST TOO.
`nav: routed` takes the whole folder out of the sidebar, not just its children,
so there is no row for the client to hang a list under -- the row is entry ZERO
instead. This file carries the difference as `place`, alongside `anchor`:

    in    the folder still has a row. Find it, append. Every router before
          2026-08-06 does this, and it is what an unset value means.
    end   there is no row. The client builds one and appends it to the top
          level.

⚠️ AND `place` IS A SEPARATE ATTRIBUTE RATHER THAN AN INFERENCE FROM AN EMPTY
`anchor`, which is one line shorter and wrong for a reason this repo keeps
relearning: an empty anchor would then mean BOTH "put it at the end" and "the
seal produced no anchor", which is one flag answering two questions.

=============================================================================
A HELD CODE OPENS THE PAGE BEFORE FIRST PAINT (DL J17, 2026-08-04)
=============================================================================
Michael: "the lock menu kinda flashes on top of any page that's potentially
locked... it's still like loading the menu each time and passing it immediately
which seems like bad architecture." Correct on both counts, and they were two
separate defects with one shared fix.

🔴 THE FLASH. `router.js` is `extra_javascript`, which Material puts at the END
of the body, so the browser had already painted the form before any script ran.
Hiding it from JS is by definition too late. Fixed with `_BOOT`, a tiny inline
script emitted immediately after the form: it runs DURING PARSE, before the
first paint, and sets a class on <html> that router.css acts on.

🔴 THE RE-DERIVATION, which is the architectural half. `seal.check()` used to
mint a FRESH RANDOM SALT PER PAGE, so a code the reader had already typed could
not be cached -- every navigation re-ran PBKDF2 at 120,000 iterations against a
brand-new salt, per held key, sequentially, before the body appeared. Nothing
was being loaded; it was being recomputed. One salt per BUILD makes the derived
verifier reusable, so page two costs a string comparison. See state.ROUTER_SALT
and seal.py on why verifiers and ciphertext do not share salts.

=============================================================================
A CURTAIN IS A PAUSE. THE PAGE SOURCE PROVES IT.
=============================================================================
The body is hidden in the DOM. It is NOT encrypted. View source, open devtools,
or read the markdown in the content repo and it is all there. That is the
design: *"just a screen before landing on content, a brief pause. not real
encryption."* v1 encrypted page bodies and paid for it with a cipher shared
across two files, a keyring and its own authoring document -- to protect content
that was readable in the repo the whole time.

What IS withheld is the CODE (only a verifier ships) and, since J14, the NAV
MANIFEST. Not a contradiction: a manifest in the clear would defeat the only
thing that feature does, while a body in the clear defeats nothing ever claimed.

=============================================================================
⭐ THE FIELD IS MASKED, AND THAT IS NOT A CONTRADICTION OF THE LINE ABOVE
=============================================================================
Michael, 2026-08-05: *"add a privacy screen [to] our router gate input field so
that when i type a code it's not visible on my screen. the black dots should
appear instead."*

`type="password"`. One attribute, and it sits directly against this feature's
own design note -- *no padlock, no red, no "restricted"* -- so the distinction
has to be written down or somebody will correctly delete it later.

A PADLOCK CLAIMS THE CONTENT IS PROTECTED. That claim is false here and the
section above says so at length: the body is in the DOM.

THE MASK CLAIMS THE CODE IS WORTH NOT SHOWING THE ROOM. That claim is TRUE, and
it is the only true one available: the code is the single thing this feature
genuinely withholds, since only a PBKDF2 verifier is ever printed. The input is
therefore the one surface where a real secret is handled, and the only place a
privacy affordance is honest rather than decorative.

The threat is mundane rather than cryptographic and it is the reason it matters:
these pages are opened in a booth, a shop, or backstage with somebody standing
behind you. Shoulder surfing does not care that the body is unencrypted.

⚠️ WHAT IT COSTS. A masked field cannot be proof-read, so a TYPO and a genuinely
wrong code are now indistinguishable to the reader -- both get "that code does
not go anywhere." The error path already clears and refocuses, which is the
right recovery, but on a phone this is a real usability cost paid for a real
privacy gain. A reveal toggle is the standard answer and is deliberately NOT
built: it is new UI and new JS on a feature whose entire argument is restraint.

⚠️ NO `name` ATTRIBUTE, AND IT MATTERS MORE NOW THAN IT DID. A password input
WITH a name is what browsers and password managers offer to save. This field has
never had one -- the form is intercepted in JS and never serialised -- so the
mask adds no save prompt and nothing lands in a keychain. Do not add one.

=============================================================================
🔴 AND THE SEAL IS WHY A WRONG DESTINATION WAS INVISIBLE FOR TWO DAYS. This file
built redirect URLs with `"../" * page.file.url.count("/")`, the separator-
counting math `util.relative_url` exists to replace -- and util.py's docstring
named THIS file as the dangerous copy while this file kept it. A curtain's
mistakes are visible immediately; a redirect's destination is encrypted, so a
wrong URL only surfaces when somebody types a correct code and lands on a 404.
**A docstring describing a fix is not the fix.** Every url the seal touches,
now including the nav manifest, goes through `relative_url`.
"""

from __future__ import annotations

import json
import secrets
from pathlib import Path

from . import seal, state
from .util import load_yaml, relative_url

# Runs during parse, BEFORE the first paint, which is the only moment that can
# stop the form flashing. Deliberately dumb: it compares a cached verifier
# against the ones on this page and sets a class. No crypto, no await, no
# reflow -- if it needed any of the three it would be too slow to be worth it.
#
#   dr-open      a cached verifier MATCHES an entry on this page, which is the
#                same proof router.js computes, just precomputed. Body shown and
#                form hidden at paint time.
#   dr-checking  keys are held but none has a cached verifier (first unlock of
#                the session, or the first page after a redeploy moved the
#                salt). The outcome is unknown, so the form is held back while
#                the async trial runs and router.js puts it back if all fail.
#
# ⚠️ NEITHER CLASS HIDES THE BODY. A reader whose JS dies mid-flight must never
# end up staring at a blank page, so `hidden` on the curtain stays the only
# thing withholding content and the <noscript> block still overrides it.
_BOOT = (
    "<script>(function(){var f=document.querySelector('.dr-router');"
    "if(!f)return;var h=document.documentElement,k=[];"
    "try{k=JSON.parse(sessionStorage.getItem('docrender.keys'))||[]}"
    "catch(e){}if(!k.length)return;var r=[];"
    "try{r=JSON.parse(atob(f.dataset.routes))||[]}catch(e){}"
    "for(var i=0;i<k.length;i++){var c=k[i];if(!c||!c.h)continue;"
    "for(var j=0;j<r.length;j++){if(r[j].h&&r[j].s===c.s&&r[j].h===c.h){"
    "h.className+=' dr-open';return}}}"
    "h.className+=' dr-checking'})();</script>"
)


def _routes() -> dict:
    return load_yaml(Path(state.INSTANCE.get("dir", ".")) / "routes.yml")


def _as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value if str(v).strip()]
    return [str(value)] if str(value).strip() else []


def _declares_router(meta: dict) -> bool:
    return bool(_as_list(meta.get("router")) or _as_list(meta.get("router_code")))


def _ancestor_indexes(src_uri: str) -> list[str]:
    """Every folder index above this page, nearest first, excluding itself.

    Written as an explicit list rather than arithmetic on path indices, because
    the arithmetic version was wrong by one level for two days and read as
    intentional. See the red note in the module docstring.

    For `production/staff/props.md`:
        production/staff/index.md, production/index.md, index.md

    For `production/staff/index.md` the first candidate IS the page, so it is
    dropped and the walk starts at `production/index.md`. A folder index does
    not inherit from itself.
    """
    parts = list(Path(src_uri).parts[:-1])
    out = []
    while True:
        candidate = "/".join(parts + ["index.md"])
        if candidate != src_uri:
            out.append(candidate)
        if not parts:
            return out
        parts.pop()


def _inherited(src_uri: str) -> tuple[dict, str] | tuple[None, None]:
    """Nearest ancestor folder index that declares a router, if any.

    Stops at the first hit, so a subfolder that redeclares overrides rather than
    stacking. Stacking ACROSS folders would mean a reader's code depending on
    how deep they happened to be, which is not something anybody can reason
    about. Stacking on ONE page is what a list is for.
    """
    for candidate in _ancestor_indexes(src_uri):
        meta = state.BY_SRC.get(candidate)
        if meta and _declares_router(meta):
            return meta, candidate
    return None, None


def _seal_nav(owner_src: str, codes: list[str], page) -> tuple[str, str, str]:
    """Seal the nav entries visibility.py withheld, once per curtain code.

    Returns (base64 payload, anchor url, place), all empty when there is nothing
    to reveal -- the normal case for a page whose folder had no children.

    ⚠️ EVERY url is resolved against the page ASKING, not against the page that
    owns the manifest. An inherited router puts this form on a child three
    folders down, where the index page's own urls are wrong. Sealed, so wrong
    means invisible until somebody types a real code. See the module docstring.
    """
    sealed = state.NAV_SEALED.get(owner_src)
    if not sealed or not codes:
        return "", "", ""

    items = []
    for entry in sealed["items"]:
        row = {"t": entry["t"], "d": entry.get("d", 1)}
        if entry.get("u"):
            row["u"] = relative_url(entry["u"], page.file.url)
        items.append(row)

    manifest = json.dumps(items, separators=(",", ":"))
    wraps = [w for w in (seal.wrap(code, manifest) for code in codes) if w]
    if not wraps:
        # The seal failed, so the subtree stays out of the sidebar and no code
        # brings it back. Fail-safe in the right direction and useless to a
        # reader, so it is reported as a real defect rather than a note.
        state.note(
            "missing_required",
            page.file.src_uri + ": the withheld nav subtree could not be "
            + "sealed, so no code will reveal it. The section is unopenable "
            + "until `cryptography` is installed.",
        )
        return "", "", ""

    # Which code opens which is itself information, and with one manifest per
    # code the wraps are otherwise in frontmatter order.
    secrets.SystemRandom().shuffle(wraps)

    # ⚠️ AN EMPTY ANCHOR STAYS EMPTY. `relative_url("", ...)` returns a path
    # back up the tree, not "" -- a perfectly valid-looking href for a place
    # that does not exist. router.js guards with `if (!href)`, so passing the
    # transformed value would sail straight past the one check written for this.
    # A falsy value has to survive a transformation as falsy or the guard
    # downstream is decoration.
    raw_anchor = sealed.get("anchor") or ""
    anchor = relative_url(raw_anchor, page.file.url) if raw_anchor else ""

    return (
        seal.b64(json.dumps(wraps, separators=(",", ":")).encode("utf-8")),
        anchor,
        str(sealed.get("place") or "in"),
    )


def _field(
    mode: str,
    payload: list,
    prompt: str,
    subtree: str,
    anchor: str,
    place: str,
) -> str:
    extra = ""
    if subtree:
        # `place` rides with the payload rather than being inferred from an
        # empty anchor -- see the module docstring on why that shortcut is the
        # one-flag-two-questions defect.
        extra = (
            ' data-subtree="' + subtree + '"'
            + ' data-subtree-anchor="' + anchor + '"'
            + ' data-subtree-place="' + (place or "in") + '"'
        )
    return (
        '<form class="dr-router" data-mode="' + mode + '"'
        + ' data-iter="' + str(seal.ITERATIONS) + '"'
        + ' data-routes="' + seal.b64(json.dumps(payload).encode("utf-8")) + '"'
        + extra + ">"
        + '<label class="dr-router__label" for="dr-router-key">'
        + prompt + "</label>"
        + '<div class="dr-router__row">'
        # ⭐ MASKED. See THE FIELD IS MASKED in the module docstring for why this
        # is not the padlock the design note forbids -- and note there is still
        # no `name` attribute, which is what keeps password managers out of it.
        + '<input class="dr-router__input" id="dr-router-key" type="password"'
        + ' autocomplete="off" autocapitalize="off" spellcheck="false">'
        + '<button class="dr-router__btn" type="submit">Go</button>'
        + "</div>"
        + '<p class="dr-router__error" role="alert" hidden>'
        + "That code does not go anywhere.</p>"
        + "</form>"
    )


def on_page_content(html, page, config, files):
    src = page.file.src_uri
    meta = state.BY_SRC.get(src, {})

    inherited_from = None
    if _declares_router(meta):
        source_meta = meta
    elif meta.get("router_inherit") is False:
        return html
    else:
        source_meta, inherited_from = _inherited(src)
        if source_meta is None:
            # `router_prompt` alone used to fail silently: the page renders
            # normally and the author is left wondering where the field went.
            if meta.get("router_prompt"):
                state.note(
                    "missing_required",
                    src + ": has `router_prompt` but no `router:` or "
                    + "`router_code:`, so there is no field for it to label.",
                )
            return html

    table_names = _as_list(source_meta.get("router"))
    local = _as_list(source_meta.get("router_code"))

    own_id = str(meta.get("id") or "")

    curtain: list[dict] = [seal.check(code) for code in local]
    redirects: list[dict] = []

    # THE PLAINTEXT CURTAIN CODES, kept alongside their verifiers because the
    # nav manifest has to be SEALED under them and a verifier cannot be reversed
    # to do it. Never rendered, never leaves this function.
    curtain_codes: list[str] = list(local)

    # WHERE EACH KEY CAME FROM, so a collision can be reported with both
    # sources named. Two tables claiming one key is a real editing mistake and
    # letting dict order decide the winner would make it depend on the order
    # somebody typed two unrelated files in.
    origin_of: dict[str, str] = {code: "router_code" for code in local}

    tables = _routes() if table_names else {}
    for table_name in table_names:
        table = tables.get(table_name)
        if table is None:
            state.note(
                "missing_required",
                src + ": declares router '" + table_name
                + "', which is not in instances/"
                + str(state.INSTANCE.get("slug")) + "/routes.yml. Known: "
                + (", ".join(sorted(tables)) or "none"),
            )
            continue

        for key, target in (table or {}).items():
            key = str(key)
            if key in origin_of:
                state.note(
                    "routers",
                    src + ": key '" + key + "' is defined in both '"
                    + origin_of[key] + "' and '" + table_name + "'. Using '"
                    + origin_of[key] + "'; the other is ignored.",
                )
                continue
            origin_of[key] = table_name

            # PORTABLE CURTAIN: no destination means "this page, whichever page
            # is asking". The form that makes a cascade work.
            if target is None or not str(target).strip():
                curtain.append(seal.check(key))
                curtain_codes.append(key)
                continue

            target = str(target).strip()

            # PINNED CURTAIN: names this page explicitly.
            if target == own_id:
                curtain.append(seal.check(key))
                curtain_codes.append(key)
                continue

            hit = state.PAGES.get(target)
            if not hit:
                state.note(
                    "dead_links",
                    src + ": router '" + table_name + "' has a key pointing "
                    + "at '" + target + "', which is not a page on this site. "
                    + "That key will never route anywhere. (Leave the value "
                    + "blank for a curtain on whichever page uses the table.)",
                )
                continue

            # Resolved against THIS page, never from a separator count. See the
            # red note in the module docstring, and util.relative_url.
            wrap = seal.wrap(key, relative_url(str(hit["url"]), page.file.url))
            if wrap:
                redirects.append(wrap)

    if not curtain and not redirects:
        state.note(
            "notes",
            src + ": a router is declared but produced no working keys, so no "
            + "field is rendered.",
        )
        return html

    prompt = str(
        meta.get("router_prompt")
        or source_meta.get("router_prompt")
        or "Enter your code"
    )
    mode = "curtain" if curtain else "redirect"

    # The manifest belongs to the page that DECLARED the router, which on an
    # inherited form is an ancestor rather than this page.
    subtree, anchor, place = _seal_nav(inherited_from or src, curtain_codes, page)

    if local and table_names:
        origin = "local+remote(" + ", ".join(table_names) + ")"
    elif local:
        origin = "local"
    else:
        origin = "remote(" + ", ".join(table_names) + ")"
    if inherited_from:
        origin += " (inherited from " + inherited_from + ")"
    state.note(
        "routers",
        src + " · " + mode + " · " + origin + " · "
        + str(len(curtain) + len(redirects)) + " keys"
        + (" · nav reveal armed" if subtree else "")
        + (" (whole folder)" if place == "end" else ""),
    )

    rng = secrets.SystemRandom()
    rng.shuffle(curtain)
    rng.shuffle(redirects)

    if not curtain:
        # No boot script on a redirect: there is nothing on this page to reveal
        # early, and a held code must never navigate somebody who just arrived.
        return html + _field("redirect", redirects, prompt, "", "", "")

    # CURTAIN. The body ships behind the `hidden` ATTRIBUTE rather than a CSS
    # class, so it is withheld before any stylesheet loads -- no flash of
    # content on a slow connection.
    #
    # `_BOOT` sits between the form and the body so it can hide the form before
    # the first paint. It has to be INLINE and it has to be HERE: an external
    # script is fetched too late, and the same code inside router.js runs after
    # Material's own scripts at the end of the body, which is after paint.
    #
    # The <noscript> block reveals the body and removes the field. Correct
    # rather than a compromise: this is a pause, not a lock, so a reader without
    # JavaScript should get the document instead of an input box that can never
    # work. `!important` in an author sheet beats the `hidden` attribute's
    # user-agent rule, which is the only reason that works.
    #
    # ⚠️ A no-JS reader gets the BODY and not the sidebar entries, the one place
    # the two halves of this feature genuinely disagree. Injecting nav needs a
    # decryption and there is no non-JS way to do one. Stated rather than
    # papered over: the content is reachable, the menu is not.
    return (
        _field("curtain", curtain + redirects, prompt, subtree, anchor, place)
        + _BOOT
        + "<noscript><style>"
        + ".dr-curtain{display:block !important}.dr-router{display:none}"
        + "</style></noscript>"
        + '<div class="dr-curtain" hidden>' + html + "</div>"
    )
