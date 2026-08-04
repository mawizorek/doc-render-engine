"""Stage 04b -- ROUTERS. A pause, or a door to somewhere else.

=============================================================================
THE FRONTMATTER KEYS, and how they relate to `status:`
=============================================================================

    status:          REQUIRED on every page, and NOTHING to do with routers.
                     It decides whether the page is BUILT and whether it is
                     LISTED. There is no default: a page with no status is not
                     built at all. See docrender/visibility.py.

    router:          name of a table in instances/<slug>/routes.yml, or a LIST
                     of table names (REMOTE)
    router_code:     a code, or a list of them, written right here (LOCAL)
    router_prompt:   the label above the field. Optional, and does NOTHING on
                     its own -- decoration for a router, not a router.
    router_inherit:  `false` on a page opts it out of a folder's cascade.

A router does not gate anything and `status:` does not know it exists. They
answer different questions: status decides what REACHES the site, a router
decides what a reader sees FIRST once they are there. A `hidden` page with a
router is still not built; a `public` page with a curtain is still fully public.

=============================================================================
EVERY SOURCE OF KEYS POOLS. REPEATING A FRONTMATTER KEY DOES NOT.
=============================================================================
One page may draw keys from any number of places, and they all end up in the
same field:

    ---
    id: staff
    status: public
    router: [pm, staff, guests]      # three REMOTE tables
    router_code: [tryme, temp26]     # plus two LOCAL codes
    ---

⚠️ WHAT DOES NOT WORK IS WRITING THE SAME KEY TWICE:

    router: pm
    router: staff        # <- the first line is GONE

That is YAML, not this engine: a duplicate key silently keeps the LAST value.
Use a list. objects.py reports duplicate frontmatter keys FIRST for exactly
this reason -- the symptom ("only one of my tables works") looks nothing like
the cause.

A key defined in two different tables is reported and the first table wins.
Resolving that by dict iteration order would make the winner depend on the
order somebody happened to type two files in.

=============================================================================
A ROUTER ON A FOLDER'S index.md CASCADES TO EVERYTHING UNDER IT
=============================================================================
    production/staff/index.md      router: pm     <- declared once
    production/staff/props.md                     <- inherits it
    production/staff/notes/x.md                   <- inherits it too

The NEAREST ancestor wins, so a subfolder can redeclare and override rather
than stack. A page opts out with `router_inherit: false`.

Why cascade at all: a folder is the unit people actually think in -- "the staff
notes" -- and a pause that only applies to the folder's front page is a pause a
reader steps around by clicking any child in the sidebar. It also costs the
reader nothing extra, because an unlock is remembered for the session: one code
at the index and the whole folder opens as they navigate.

🔴 THIS DID NOT WORK FOR A DIRECT CHILD UNTIL 2026-08-03, AND THE EXAMPLE
ABOVE IS THE CASE IT GOT WRONG. `_inherited` began its walk at the page's
GRANDPARENT folder: for `production/staff/props.md` it looked at
`production/index.md` and then the site root, and never at
`production/staff/index.md` -- the one folder index the whole feature exists to
read. `parts[:depth - 1]` where `parts[:depth]` was meant, guarded by a comment
confidently explaining a different off-by-one. It is now an explicit list of
ancestor paths, because index arithmetic is what made a wrong answer look
deliberate.

⚠️ AND IT IS STILL NOT PROTECTION. A direct link to a child page shows the
curtain, but the body is in that page's source either way. Cascading makes the
PAUSE consistent across a folder. It does not make the folder private, and
nothing here ever will -- the content repo is public.

A pause should be easy to reason about, so the nearest statement wins and a page
can opt out. That is deliberately the opposite instinct from access control,
where the most protective statement should win -- but note that publication
states do not actually cascade at all. See visibility.py, which used to claim
they did.

=============================================================================
THE CASCADE NOW TAKES THE SIDEBAR WITH IT (DL Q10 -> J14, 2026-08-04)
=============================================================================
A routed folder index has its whole subtree removed from the nav by
visibility.py at stage 00b, which stashes what it took in `state.NAV_SEALED`.
This file seals that manifest with `_wrap`, under EVERY code that opens the
curtain and no others, and ships it on the form as `data-subtree`. A correct
code decrypts it and router.js injects the entries under the section's own
sidebar link.

Sealed rather than shipped as text because a plaintext manifest would put every
withheld title in the source of the page withholding it. The full argument, and
the one that lost, are in the Decision Log -- not repeated here, because this
docstring is already at the warn line.

⚠️ A REDIRECT CODE NEVER UNSEALS THE NAV. It does not reveal this page, so it
has no business revealing this page's children. Only curtain codes are used,
which is why they are collected separately below rather than read back off the
hashes.

=============================================================================
LOCAL VS REMOTE
=============================================================================
LOCAL -- in the page. Throwaway, no engine edit, no engine deploy:

    ---
    id: staff
    status: public
    router_code: staff26
    router_prompt: Got a code?
    ---

REMOTE -- in the engine. Durable, one place to edit, and the only form that can
send somebody to a DIFFERENT page:

    # instances/<slug>/routes.yml
    staff:
      staff26: staff                # curtain on the staff page (by id)
      loadin24: crew-call-sheet     # redirect to another page
    pm:
      maw:                          # PORTABLE curtain -- see below

Both may be present on one page; the keys pool. A code you are trying for an
afternoon should not require touching the engine, and a code people are actually
given should not sit in a public content repo.

⚠️ A LOCAL CODE IS IN A PUBLIC REPO. Fine for a pause, wrong for anything you
would mind a stranger typing. Local is for trash; remote is for real.

=============================================================================
THREE KINDS OF ENTRY, and the destination decides which -- never a mode flag
=============================================================================

    maw:                    -> PORTABLE CURTAIN. No destination at all, so it
                               means "curtain on whatever page declares this
                               table." One entry, reusable on any number of
                               pages, and it never needs to know their ids.
                               This is the form that makes a cascade useful.

    staff26: staff          -> PINNED CURTAIN. Names the id of the page it is
                               used on. Identical behaviour, tied to that one
                               page -- what you want when one table mixes
                               curtains for several different pages.

    loadin24: crew-sheet    -> REDIRECT. Names a different page; sends you
                               there.

⚠️ A PINNED curtain does NOT cascade usefully: inherited by a child page, its
id no longer matches, so it is read as a redirect BACK to the folder index.
That is coherent but rarely wanted. Use the portable form on any table you
expect to inherit.

=============================================================================
A CURTAIN IS A PAUSE. THE PAGE SOURCE PROVES IT.
=============================================================================
The body is hidden in the DOM. It is NOT encrypted. View source, open devtools,
or read the markdown in the public repo and it is all there.

That is the design: *"just a screen before landing on content, a brief pause.
not real encryption."* v1 encrypted page bodies and paid for it with a cipher
shared across two files, a keyring and its own authoring document -- to protect
content that was public in the repo the whole time.

What IS withheld is the code: only a PBKDF2 hash ships, so a page does not hand
the key to the next person who opens it. As of J14 the withheld NAV MANIFEST is
sealed too -- which is not a contradiction of the paragraph above, because a
manifest that shipped in the clear would defeat the feature that asked for it,
while a body that ships in the clear defeats nothing that was ever claimed.

REDIRECT still seals its destination, and the asymmetry is the point: a
plaintext destination is not a router, it is a list of links with an input box
in front of it. A curtain has no such problem -- the destination is the page you
are already standing on.

🔴 AND THE SEAL IS WHY A WRONG DESTINATION WAS INVISIBLE FOR TWO DAYS. This file
built redirect URLs with `"../" * page.file.url.count("/")`, the separator-
counting math that `util.relative_url` was written to replace. util.py's own
docstring says it was lifted into util because TWO hooks had copied that math,
and names this one as the worse copy for precisely the reason it then stayed
broken: a curtain's mistakes are visible immediately, while a redirect's
destination is encrypted, so a wrong URL surfaces only when a reader types a
correct code and lands on a 404. links.py was converted; this file was not.
**A docstring describing a fix is not the fix.** Every url the seal touches --
now including the nav manifest -- goes through `relative_url` for that reason.
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
from pathlib import Path

from . import state
from .util import load_yaml, relative_url

ITERATIONS = 120_000


def _b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _routes() -> dict:
    return load_yaml(Path(state.INSTANCE.get("dir", ".")) / "routes.yml")


def _derive(key: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha256", key.encode("utf-8"), salt, ITERATIONS, dklen=32
    )


def _check(key: str) -> dict:
    """A verifier for a curtain: prove the code without shipping the code."""
    salt = secrets.token_bytes(16)
    return {"s": _b64(salt), "h": _b64(_derive(key, salt))}


def _wrap(key: str, destination: str) -> dict | None:
    """Seal a redirect destination, or a nav manifest, under its key."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        state.note(
            "notes",
            "router: the `cryptography` package is missing, so redirect "
            "destinations cannot be sealed. Add it to requirements.txt.",
        )
        return None
    salt = secrets.token_bytes(16)
    nonce = secrets.token_bytes(12)
    sealed = AESGCM(_derive(key, salt)).encrypt(
        nonce, destination.encode("utf-8"), None
    )
    return {"s": _b64(salt), "n": _b64(nonce), "w": _b64(sealed)}


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
    intentional: it carried a comment explaining, correctly, that a page's own
    index is not its ancestor -- while actually skipping its PARENT's index too.

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


def _seal_nav(owner_src: str, codes: list[str], page) -> tuple[str, str]:
    """Seal the nav entries visibility.py withheld, once per curtain code.

    Returns (base64 payload, anchor url), both empty when there is nothing to
    reveal -- which is the normal case for a page whose folder had no children.

    ⚠️ EVERY url is resolved against the page ASKING, not against the page that
    owns the manifest. An inherited router puts this form on a child three
    folders down, and a url that was correct for the index page is wrong there.
    Sealed, so wrong would have meant invisible until somebody typed a real
    code. See the red note in the module docstring.
    """
    sealed = state.NAV_SEALED.get(owner_src)
    if not sealed or not codes:
        return "", ""

    items = []
    for entry in sealed["items"]:
        row = {"t": entry["t"], "d": entry.get("d", 1)}
        if entry.get("u"):
            row["u"] = relative_url(entry["u"], page.file.url)
        items.append(row)

    manifest = json.dumps(items, separators=(",", ":"))
    wraps = [w for w in (_wrap(code, manifest) for code in codes) if w]
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
        return "", ""

    # Which code opens which is itself information, and with one manifest per
    # code the wraps are otherwise in frontmatter order.
    secrets.SystemRandom().shuffle(wraps)
    return (
        _b64(json.dumps(wraps, separators=(",", ":")).encode("utf-8")),
        relative_url(sealed["anchor"], page.file.url),
    )


def _field(mode: str, payload: list, prompt: str, subtree: str, anchor: str) -> str:
    extra = ""
    if subtree:
        extra = (
            ' data-subtree="' + subtree + '"'
            + ' data-subtree-anchor="' + anchor + '"'
        )
    return (
        '<form class="dr-router" data-mode="' + mode + '"'
        + ' data-iter="' + str(ITERATIONS) + '"'
        + ' data-routes="' + _b64(json.dumps(payload).encode("utf-8")) + '"'
        + extra + ">"
        + '<label class="dr-router__label" for="dr-router-key">'
        + prompt + "</label>"
        + '<div class="dr-router__row">'
        + '<input class="dr-router__input" id="dr-router-key" type="text"'
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

    curtain: list[dict] = [_check(code) for code in local]
    redirects: list[dict] = []

    # THE PLAINTEXT CURTAIN CODES, kept alongside their hashes because the nav
    # manifest has to be SEALED under them and a hash cannot be reversed to do
    # it. Never rendered, never leaves this function.
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
                curtain.append(_check(key))
                curtain_codes.append(key)
                continue

            target = str(target).strip()

            # PINNED CURTAIN: names this page explicitly.
            if target == own_id:
                curtain.append(_check(key))
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
            wrap = _wrap(key, relative_url(str(hit["url"]), page.file.url))
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
    subtree, anchor = _seal_nav(inherited_from or src, curtain_codes, page)

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
        + (" · nav reveal armed" if subtree else ""),
    )

    rng = secrets.SystemRandom()
    rng.shuffle(curtain)
    rng.shuffle(redirects)

    if not curtain:
        return html + _field("redirect", redirects, prompt, "", "")

    # CURTAIN. The body is held behind the `hidden` ATTRIBUTE rather than a CSS
    # class, so it is withheld before any stylesheet loads -- no flash of
    # content on a slow connection.
    #
    # The <noscript> block reveals it and removes the field. Correct rather than
    # a compromise: this is a pause, not a lock, so a reader without JavaScript
    # should get the document instead of an input box that can never work.
    # `!important` in an author sheet beats the `hidden` attribute's user-agent
    # rule, which is the only reason that works.
    #
    # ⚠️ A no-JS reader gets the BODY and not the sidebar entries, which is the
    # one place the two halves of this feature genuinely disagree. Injecting nav
    # needs a decryption, and there is no non-JS way to do one. Stated rather
    # than papered over: the content is reachable, the menu is not.
    return (
        _field("curtain", curtain + redirects, prompt, subtree, anchor)
        + "<noscript><style>"
        + ".dr-curtain{display:block !important}.dr-router{display:none}"
        + "</style></noscript>"
        + '<div class="dr-curtain" hidden>' + html + "</div>"
    )
