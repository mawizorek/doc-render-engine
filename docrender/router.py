"""Stage 04b -- ROUTERS. A pause, or a door to somewhere else.

=============================================================================
THE FRONTMATTER KEYS, and how they relate to `status:`
=============================================================================

    status:          REQUIRED on every page, and NOTHING to do with routers.
                     It decides whether the page is BUILT and whether it is
                     LISTED. There is no default: a page with no status is not
                     built at all. See docrender/visibility.py.

    router:          name of a table in instances/<slug>/routes.yml (REMOTE)
    router_code:     a code, or a list of them, written right here (LOCAL)
    router_prompt:   the label above the field. Optional, and does NOTHING on
                     its own -- decoration for a router, not a router.
    router_inherit:  `false` on a page opts it out of a folder's cascade.

A router does not gate anything and `status:` does not know it exists. They
answer different questions: status decides what REACHES the site, a router
decides what a reader sees FIRST once they are there. A `hidden` page with a
router is still not built; a `public` page with a curtain is still fully public.

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

⚠️ AND IT IS STILL NOT PROTECTION. A direct link to a child page shows the
curtain, but the body is in that page's source either way. Cascading makes the
PAUSE consistent across a folder. It does not make the folder private, and
nothing here ever will -- the content repo is public.

This is deliberately the OPPOSITE emphasis from publication states, which
cascade so that the most PROTECTIVE statement wins. Access should be hard to
weaken by accident; a pause should be easy to reason about. Same direction, very
different stakes.

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

    loadin24: crew-sheet    -> REDIRECT. Names a different page; sends you there.

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
the key to the next person who opens it.

REDIRECT still seals its destination, and the asymmetry is the point: a
plaintext destination is not a router, it is a list of links with an input box
in front of it. A curtain has no such problem -- the destination is the page you
are already standing on.
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
from pathlib import Path

from . import state
from .util import load_yaml

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
    """Seal a redirect destination under its key."""
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
    return bool(meta.get("router") or _as_list(meta.get("router_code")))


def _inherited(src_uri: str) -> tuple[dict, str] | tuple[None, None]:
    """Nearest ancestor folder index that declares a router, if any.

    Walks UP one folder at a time and stops at the first hit, so a subfolder
    that redeclares overrides rather than stacking. Stacking would mean two
    fields on one page, which is not a thing anybody wants.
    """
    parts = Path(src_uri).parts
    # Start above this page's own folder: its own index is a sibling, not an
    # ancestor, and a folder index does not inherit from itself.
    for depth in range(len(parts) - 1, 0, -1):
        candidate = "/".join(parts[:depth - 1] + ("index.md",)) if depth > 1 else "index.md"
        if candidate == src_uri:
            continue
        meta = state.BY_SRC.get(candidate)
        if meta and _declares_router(meta):
            return meta, candidate
    return None, None


def _field(mode: str, payload: list, prompt: str) -> str:
    return (
        '<form class="dr-router" data-mode="' + mode + '"'
        + ' data-iter="' + str(ITERATIONS) + '"'
        + ' data-routes="' + _b64(json.dumps(payload).encode("utf-8")) + '">'
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

    table_name = source_meta.get("router")
    local = _as_list(source_meta.get("router_code"))

    own_id = str(meta.get("id") or "")
    depth = page.file.url.count("/")
    prefix = "../" * depth

    curtain: list[dict] = [_check(code) for code in local]
    redirects: list[dict] = []

    if table_name:
        tables = _routes()
        table = tables.get(str(table_name))
        if table is None:
            state.note(
                "missing_required",
                src + ": declares router '" + str(table_name)
                + "', which is not in instances/"
                + str(state.INSTANCE.get("slug")) + "/routes.yml. Known: "
                + (", ".join(sorted(tables)) or "none"),
            )
            table = {}

        for key, target in (table or {}).items():
            # PORTABLE CURTAIN: no destination means "this page, whichever page
            # is asking". The form that makes a cascade work.
            if target is None or not str(target).strip():
                curtain.append(_check(str(key)))
                continue

            target = str(target).strip()

            # PINNED CURTAIN: names this page explicitly.
            if target == own_id:
                curtain.append(_check(str(key)))
                continue

            hit = state.PAGES.get(target)
            if not hit:
                state.note(
                    "dead_links",
                    src + ": router '" + str(table_name) + "' has a key pointing "
                    + "at '" + target + "', which is not a page on this site. "
                    + "That key will never route anywhere. (Leave the value "
                    + "blank for a curtain on whichever page uses the table.)",
                )
                continue

            wrap = _wrap(str(key), prefix + str(hit["url"]))
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
    if local and table_name:
        origin = "local+remote"
    elif local:
        origin = "local"
    else:
        origin = "remote"
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
        return html + _field("redirect", redirects, prompt)

    # CURTAIN. The body is held behind the `hidden` ATTRIBUTE rather than a CSS
    # class, so it is withheld before any stylesheet loads -- no flash of
    # content on a slow connection.
    #
    # The <noscript> block reveals it and removes the field. Correct rather than
    # a compromise: this is a pause, not a lock, so a reader without JavaScript
    # should get the document instead of an input box that can never work.
    # `!important` in an author sheet beats the `hidden` attribute's user-agent
    # rule, which is the only reason that works.
    return (
        _field("curtain", curtain + redirects, prompt)
        + "<noscript><style>"
        + ".dr-curtain{display:block !important}.dr-router{display:none}"
        + "</style></noscript>"
        + '<div class="dr-curtain" hidden>' + html + "</div>"
    )
