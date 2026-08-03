"""Stage 04b -- ROUTERS. A pause, or a door to somewhere else.

=============================================================================
TWO PLACES TO PUT A CODE, and they answer different needs
=============================================================================

LOCAL -- in the page itself. Throwaway, no engine edit, no deploy of anything
but the content repo:

    ---
    id: staff
    router_code: staff26
    router_prompt: Got a code?
    ---

REMOTE -- in `instances/<slug>/routes.yml` in the engine. Durable, one place to
edit, and the only form that can send somebody to a DIFFERENT page:

    staff:
      staff26: staff                # curtain on the staff page
      loadin24: crew-call-sheet      # redirect to another page

    ---
    id: staff
    router: staff
    ---

Both may be present; the keys are simply pooled. The split is deliberate
(Michael, 2026-08-03): a code you are trying out for an afternoon should not
require touching the engine, and a code that people are actually given should
not live in a file anyone can grep out of a public content repo.

⚠️ A LOCAL CODE IS IN THE CONTENT REPO, WHICH IS PUBLIC. That is fine for the
thing it is for -- a pause -- and it is the wrong choice for anything you would
mind a stranger typing. Local is for trash; remote is for real.

=============================================================================
CURTAIN OR REDIRECT: the destination decides, not a mode flag
=============================================================================
**A key pointing at the id of the page carrying the router is a CURTAIN**: the
page's own body is held back, the field sits where the content would be, and a
correct code reveals it in place. `router_code` is always a curtain, since it
names no destination at all.

Anything else is a REDIRECT.

Inferred rather than declared because "send me to the page I am on" has exactly
one sensible meaning. Michael hit the other reading first: the browser navigated
to the same URL and nothing appeared to happen.

=============================================================================
A CURTAIN IS A PAUSE. THE PAGE SOURCE PROVES IT.
=============================================================================
The body is hidden in the DOM. It is NOT encrypted. View source, open devtools,
or read the markdown in the public repo and it is all there.

That is the design, not an oversight: *"just a screen before landing on content,
a brief pause. not real encryption."* v1 encrypted page bodies and paid for it
with a cipher shared across two files, a keyring and its own authoring document
-- to protect content that was public in the repo the whole time.

What IS withheld is the code: only a PBKDF2 hash ships, so a page does not hand
the key to the next person who opens it. Weak effort in the right place, none
wasted in the wrong one.

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
    meta = state.BY_SRC.get(page.file.src_uri, {})
    table_name = meta.get("router")
    local = _as_list(meta.get("router_code"))
    if not table_name and not local:
        return html

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
                page.file.src_uri + ": declares router '" + str(table_name)
                + "', which is not in instances/"
                + str(state.INSTANCE.get("slug")) + "/routes.yml. Known: "
                + (", ".join(sorted(tables)) or "none"),
            )
            table = {}
        for key, target in (table or {}).items():
            target = str(target)
            if target == own_id:
                curtain.append(_check(str(key)))
                continue
            hit = state.PAGES.get(target)
            if not hit:
                state.note(
                    "dead_links",
                    page.file.src_uri + ": router '" + str(table_name) + "' has a "
                    + "key pointing at '" + target + "', which is not a page on "
                    + "this site. That key will never route anywhere.",
                )
                continue
            wrap = _wrap(str(key), prefix + str(hit["url"]))
            if wrap:
                redirects.append(wrap)

    if not curtain and not redirects:
        state.note(
            "notes",
            page.file.src_uri + ": a router is declared but produced no working "
            + "keys, so no field is rendered.",
        )
        return html

    prompt = str(meta.get("router_prompt") or "Enter your code")
    mode = "curtain" if curtain else "redirect"
    source = "local" if local and not table_name else (
        "remote" if table_name and not local else "local+remote"
    )
    state.note(
        "routers",
        page.file.src_uri + " · " + mode + " · " + source + " · "
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
