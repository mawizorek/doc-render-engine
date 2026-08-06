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
visibility.py strips a routed folder's subtree out of the nav at stage 00bc and
stashes it in `state.NAV_SEALED`. This file seals each manifest with `seal.wrap`,
under EVERY code that opens that curtain and no others.

⚠️ A REDIRECT CODE NEVER UNSEALS THE NAV. It does not reveal the page, so it has
no business revealing that page's children -- which is why curtain codes are
collected separately rather than read back off the verifiers.

⭐ AND SINCE 2026-08-06 THE FOLDER'S OWN ROW CAN BE IN THAT MANIFEST TOO.
`nav: routed` takes the whole folder out of the sidebar, not just its children,
so there is no row for the client to hang a list under -- the row is entry ZERO
instead, and `place` says which case applies:

    in    the folder still has a row. Find it, append underneath.
    at    there is no row. The client builds one and places it, using `before`
          (the next surviving top-level sibling) and `idx` as a fallback.

=============================================================================
🔴 THE MANIFEST SHIPS ON EVERY PAGE, AND IT USED TO SHIP ON THE FORM
=============================================================================
Michael, 2026-08-06: *"it should NOT disappear after i enter the code the first
time."*

It did, and the cause was structural: the payload was an attribute of the router
FORM, which renders only where a router is declared or inherited. Navigate out
of the folder and the ciphertext is simply not on the page. visibility.py
carried that as a known limit and called fixing it "more machinery for a
cosmetic consistency."

⚑ IT WAS NOT COSMETIC. A folder that vanishes the moment you click into it is a
flicker rather than a menu, and navigating from that menu is the entire feature.

So `_nav_boot` emits ONE hidden element on EVERY page, carrying every withheld
folder on the site.

⭐ WHY ONE BLOB CAN SERVE EVERY PAGE: the urls inside it are BUILD urls, exactly
as MkDocs made them, rather than resolved against the asking page. Resolving
them per page is what made the old ciphertext page-specific. The one per-page
value left is `data-root`, a `../..` prefix that rides OUTSIDE the seal where it
costs nothing, and the client joins the two. Sealing once per build rather than
once per page falls out of that for free.

⭐ AND IT REPLACED the form-borne version rather than joining it. Two mechanisms
doing one job is the duplication this repo keeps killing -- so the ORDINARY
`router:` case persists across pages now as well.

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
brand-new salt, per held key, sequentially, before the body appeared. One salt
per BUILD makes the derived verifier reusable, so page two costs a string
comparison. See state.ROUTER_SALT and seal.py on why verifiers and ciphertext do
not share salts.

⚠️ THE SAME ARGUMENT NOW APPLIES TO THE NAV, and router.js caches the DECRYPTED
manifest in sessionStorage for it. Without that, every page load would re-derive
every held key against every sealed folder before it could draw a sidebar entry.

=============================================================================
A CURTAIN IS A PAUSE. THE PAGE SOURCE PROVES IT.
=============================================================================
The body is hidden in the DOM. It is NOT encrypted. View source, open devtools,
or read the markdown and it is all there. That is the design: *"just a screen
before landing on content, a brief pause. not real encryption."*

What IS withheld is the CODE (only a verifier ships) and the NAV MANIFEST. Not a
contradiction: a manifest in the clear would defeat the only thing that feature
does, while a body in the clear defeats nothing ever claimed.

=============================================================================
⭐ THE FIELD IS MASKED, AND THAT IS NOT A CONTRADICTION OF THE LINE ABOVE
=============================================================================
Michael, 2026-08-05: *"add a privacy screen [to] our router gate input field so
that when i type a code it's not visible on my screen."*

`type="password"`. One attribute, and it sits directly against this feature's
own design note -- *no padlock, no red, no "restricted"* -- so the distinction
has to be written down or somebody will correctly delete it later.

A PADLOCK CLAIMS THE CONTENT IS PROTECTED. False here, at length, above.

THE MASK CLAIMS THE CODE IS WORTH NOT SHOWING THE ROOM. True, and the only true
claim available: the code is the single thing this feature genuinely withholds,
since only a PBKDF2 verifier is ever printed. The threat is mundane rather than
cryptographic and that is why it matters -- these pages are opened in a booth or
backstage with somebody standing behind you.

⚠️ WHAT IT COSTS. A masked field cannot be proof-read, so a TYPO and a genuinely
wrong code are indistinguishable to the reader. A reveal toggle is the standard
answer and is deliberately NOT built: new UI and new JS on a feature whose whole
argument is restraint.

⚠️ NO `name` ATTRIBUTE. A password input WITH a name is what browsers offer to
save. This field has never had one, so the mask adds no save prompt and nothing
lands in a keychain. Do not add one.

=============================================================================
🔴 AND THE SEAL IS WHY A WRONG DESTINATION WAS INVISIBLE FOR TWO DAYS. This file
built redirect URLs with `"../" * page.file.url.count("/")`, the separator-
counting math `util.relative_url` exists to replace -- and util.py's docstring
named THIS file as the dangerous copy while this file kept it. A curtain's
mistakes are visible immediately; a redirect's destination is encrypted, so a
wrong URL only surfaces when somebody types a correct code and lands on a 404.
**A docstring describing a fix is not the fix.**
"""

from __future__ import annotations

import hashlib
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

#: The sealed site-wide nav payload, cached for the life of one build.
#:
#: ⚠️ IT LIVES HERE RATHER THAN IN state.py BECAUSE ONLY THIS MODULE TOUCHES IT,
#: which is that module's own stated admission rule. The cost is that `mkdocs
#: serve` rebuilds in-process and a module global outlives a build -- so the key
#: is a DIGEST OF THE MANIFEST rather than a build counter. A page retitle
#: changes the manifest without changing which folders are sealed, so anything
#: coarser would keep serving a stale reveal until somebody restarted the server.
_NAV_CACHE: dict = {}


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


def _keys_for(
    source_meta: dict,
    own_id: str,
    src: str,
    report: bool = True,
) -> tuple[list[str], list[tuple[str, str]]]:
    """Which keys open a CURTAIN here, and which are REDIRECTS to elsewhere.

    Returns (curtain codes in plaintext, [(key, destination BUILD url)]).

    ⭐ EXTRACTED, NOT COPIED, AND THAT IS THE POINT. Two callers need this now --
    the page renderer, and `_nav_payload`, which has to seal each manifest under
    the same codes that open the curtain. Stating "which entries are curtains"
    twice is how the two would drift the first time somebody adds a fourth entry
    shape.

    ⚠️ `report=False` FOR THE SECOND CALLER. Every collision and dead link here
    is already printed by the page pass; printing them again would look like a
    second, separate problem.

    Destinations come back as BUILD urls and are resolved against the asking
    page by the caller. Resolving them in here would make the result
    page-specific, which is exactly what stopped the nav payload being shareable.
    """
    local = _as_list(source_meta.get("router_code"))
    table_names = _as_list(source_meta.get("router"))

    codes: list[str] = list(local)
    dests: list[tuple[str, str]] = []

    # WHERE EACH KEY CAME FROM, so a collision can be reported with both sources
    # named. Two tables claiming one key is a real editing mistake, and letting
    # dict order decide the winner would make it depend on the order somebody
    # typed two unrelated files in.
    origin_of: dict[str, str] = {code: "router_code" for code in local}

    tables = _routes() if table_names else {}
    for table_name in table_names:
        table = tables.get(table_name)
        if table is None:
            if report:
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
                if report:
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
                codes.append(key)
                continue

            target = str(target).strip()

            # PINNED CURTAIN: names this page explicitly.
            if target == own_id:
                codes.append(key)
                continue

            hit = state.PAGES.get(target)
            if not hit:
                if report:
                    state.note(
                        "dead_links",
                        src + ": router '" + table_name + "' has a key pointing "
                        + "at '" + target + "', which is not a page on this "
                        + "site. That key will never route anywhere. (Leave the "
                        + "value blank for a curtain on whichever page uses the "
                        + "table.)",
                    )
                continue

            dests.append((key, str(hit["url"])))

    return codes, dests


def _nav_payload() -> tuple[str, str]:
    """(base64 blob, build id) describing every withheld folder on this site.

    ONE payload for the whole build, emitted unchanged on every page. See the
    module docstring for why that is possible at all -- the short version is
    that the urls inside are build urls, so nothing in here is page-specific.

    Each entry is one sealed folder:

        p   place: 'in' (hang under the folder's own row) or 'at' (build one)
        a   anchor url, 'in' only
        b   the row to insert ahead of, 'at' only
        i   fallback index in the top-level list, 'at' only
        w   the manifest, wrapped once per curtain code

    ⚠️ WRAPPED PER CODE AND THEN SHUFFLED, unchanged from the per-page version:
    which code opens which folder is itself information, and in frontmatter
    order the wraps would leak it.
    """
    if not state.NAV_SEALED:
        return "", ""

    signature = json.dumps(state.NAV_SEALED, sort_keys=True, default=str)
    if _NAV_CACHE.get("sig") == signature:
        return _NAV_CACHE["blob"], _NAV_CACHE["build"]

    entries = []
    for src, sealed in state.NAV_SEALED.items():
        meta = state.BY_SRC.get(src, {})
        codes, _dests = _keys_for(
            meta, str(meta.get("id") or ""), src, report=False
        )
        if not codes:
            continue

        manifest = json.dumps(sealed["items"], separators=(",", ":"))
        wraps = [w for w in (seal.wrap(code, manifest) for code in codes) if w]
        if not wraps:
            # The seal failed, so the subtree stays out of the sidebar and no
            # code brings it back. Fail-safe in the right direction and useless
            # to a reader, so it is a real defect rather than a note.
            state.note(
                "missing_required",
                src + ": the withheld nav subtree could not be sealed, so no "
                + "code will reveal it. The section is unopenable until "
                + "`cryptography` is installed.",
            )
            continue

        secrets.SystemRandom().shuffle(wraps)

        entry = {"p": str(sealed.get("place") or "in"), "w": wraps}
        if sealed.get("anchor"):
            entry["a"] = sealed["anchor"]
        if sealed.get("before"):
            entry["b"] = sealed["before"]
        if isinstance(sealed.get("idx"), int) and sealed["idx"] >= 0:
            entry["i"] = sealed["idx"]
        entries.append(entry)

    blob = (
        seal.b64(json.dumps(entries, separators=(",", ":")).encode("utf-8"))
        if entries else ""
    )
    # ⚠️ THE BUILD ID IS WHAT EXPIRES A READER'S CACHED SIDEBAR. router.js keeps
    # the DECRYPTED manifest in sessionStorage so page two costs no crypto, and
    # a reader can be mid-session when a deploy lands. Keying that cache on a
    # digest of the payload means a changed manifest is a different cache, and a
    # renamed page cannot keep showing its old title.
    build = hashlib.sha256(blob.encode("utf-8")).hexdigest()[:8] if blob else ""

    _NAV_CACHE.update(sig=signature, blob=blob, build=build)
    return blob, build


def _nav_boot(page) -> str:
    """The hidden element carrying the sealed nav, for THIS page.

    ⚠️ EMITTED ON EVERY PAGE, INCLUDING PAGES WITH NO ROUTER AT ALL. Those are
    the pages a reader navigates to after unlocking, so they are exactly where
    this matters -- putting it only on routed pages would reproduce the bug it
    exists to fix, two clicks in.

    `data-root` is the only page-specific value: how far up to the site root, so
    the client can resolve build urls without the seal having to know which page
    is asking. `data-iter` rides along because a page outside the folder has no
    form to read the KDF iteration count off.
    """
    blob, build = _nav_payload()
    if not blob:
        return ""
    return (
        '<div class="dr-nav-boot" hidden'
        + ' data-nav="' + blob + '"'
        + ' data-root="' + relative_url("", page.file.url) + '"'
        + ' data-build="' + build + '"'
        + ' data-iter="' + str(seal.ITERATIONS) + '"'
        + "></div>"
    )


def _field(mode: str, payload: list, prompt: str) -> str:
    return (
        '<form class="dr-router" data-mode="' + mode + '"'
        + ' data-iter="' + str(seal.ITERATIONS) + '"'
        + ' data-routes="' + seal.b64(json.dumps(payload).encode("utf-8")) + '"'
        + ">"
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

    # ⚠️ FIRST, AND ON EVERY PATH OUT OF THIS FUNCTION. Three of the four early
    # returns below are pages with no router, which is precisely where the
    # sealed nav has to be present -- they are what a reader clicks INTO after
    # unlocking. Appending this only on routed pages is the bug this element was
    # added to fix.
    boot = _nav_boot(page)

    inherited_from = None
    if _declares_router(meta):
        source_meta = meta
    elif meta.get("router_inherit") is False:
        return html + boot
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
            return html + boot

    own_id = str(meta.get("id") or "")
    codes, dests = _keys_for(source_meta, own_id, src)

    curtain: list[dict] = [seal.check(code) for code in codes]
    redirects: list[dict] = []
    for key, target_url in dests:
        # Resolved against THIS page, never from a separator count. See the red
        # note in the module docstring, and util.relative_url.
        wrap = seal.wrap(key, relative_url(target_url, page.file.url))
        if wrap:
            redirects.append(wrap)

    if not curtain and not redirects:
        state.note(
            "notes",
            src + ": a router is declared but produced no working keys, so no "
            + "field is rendered.",
        )
        return html + boot

    prompt = str(
        meta.get("router_prompt")
        or source_meta.get("router_prompt")
        or "Enter your code"
    )
    mode = "curtain" if curtain else "redirect"

    table_names = _as_list(source_meta.get("router"))
    local = _as_list(source_meta.get("router_code"))
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
        + str(len(curtain) + len(redirects)) + " keys",
    )

    rng = secrets.SystemRandom()
    rng.shuffle(curtain)
    rng.shuffle(redirects)

    if not curtain:
        # No boot script on a redirect: there is nothing on this page to reveal
        # early, and a held code must never navigate somebody who just arrived.
        return html + _field("redirect", redirects, prompt) + boot

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
    # work.
    #
    # ⚠️ THE NAV ELEMENT SITS OUTSIDE THE CURTAIN, deliberately. It carries no
    # readable content and hiding it would change nothing -- but a payload that
    # only exists inside a hidden container is one refactor away from being
    # removed with it.
    return (
        _field("curtain", curtain + redirects, prompt)
        + _BOOT
        + "<noscript><style>"
        + ".dr-curtain{display:block !important}.dr-router{display:none}"
        + "</style></noscript>"
        + '<div class="dr-curtain" hidden>' + html + "</div>"
        + boot
    )
