"""Stage 04b -- ROUTERS. Type a key, get somewhere.

Two modes, and the route table decides which one without any extra syntax.

    # instances/<slug>/routes.yml
    crew:
      loadin24: crew-call-sheet     # REDIRECT: sends you to another page
      staff26: staff                # CURTAIN:  reveals THIS page's own body

**If a key points at the id of the page carrying the router, it is a CURTAIN.**
The page's body is held back, the field sits where the content would be, and a
correct code reveals it in place. Pointing anywhere else is a REDIRECT.

That inference is deliberate rather than a `mode:` field: "send me to the page I
am on" has exactly one sensible meaning, and a redirect to your own URL is
never what anybody wanted. Michael hit that literally -- typed the code, the
browser navigated to the same address, and nothing appeared to happen.

=============================================================================
CURTAIN MODE IS A PAUSE, NOT A LOCK, AND THE PAGE SOURCE PROVES IT
=============================================================================
The body is hidden in the DOM. It is NOT encrypted. Anyone who views source,
opens devtools, or reads the markdown in the public content repo sees
everything.

That is the explicit design (Michael, 2026-08-03): *"just a screen before
landing on content, a brief pause. not real encryption."* Encrypting the body
is what v1 did; it cost a shared cipher across two files, a keyring, and a
whole authoring document, to protect content that was public in the repo the
whole time.

What IS withheld is the code itself: only a PBKDF2 hash of it ships, so the
page does not hand out the key to the next person. Weak effort in the right
place, none wasted in the wrong one.

If something genuinely must not be read, it does not belong in a public doc
repo at all, and no amount of front-end work changes that.

=============================================================================
WHY REDIRECT MODE STILL ENCRYPTS
=============================================================================
Because a plaintext destination is not a router, it is a list of links with an
input box in front of it. Anyone reading source would see every destination and
skip the field, which defeats the only thing that mode does. A curtain has no
such problem: the destination is the page you are already on.

So the asymmetry is on purpose. Curtain hides content it cannot protect and
says so; redirect protects a destination it genuinely can.

=============================================================================
WHERE THE KEYS LIVE: instances/<slug>/routes.yml
=============================================================================
In the ENGINE, one file per site, the single editable source. Never in a content
repo -- that repo is public and has a Download ZIP button, so a key committed
there ships with the documents.

The table NAME is shared vocabulary and lives in the page's frontmatter; the
KEYS are local and live with the site. Same split as object types and palettes.

UNLOCKING IS REMEMBERED FOR THE SESSION. A code that opens one curtain opens
every curtain it fits, and closing the tab re-locks everything --
sessionStorage, not localStorage, because a shared shop machine is the normal
case here.
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
    if not table_name:
        return html

    tables = _routes()
    table = tables.get(str(table_name))
    if not table:
        state.note(
            "missing_required",
            page.file.src_uri + ": declares router '" + str(table_name)
            + "', which is not in instances/" + str(state.INSTANCE.get("slug"))
            + "/routes.yml. Known: " + (", ".join(sorted(tables)) or "none"),
        )
        return html

    own_id = str(meta.get("id") or "")
    depth = page.file.url.count("/")
    prefix = "../" * depth

    curtain: list[dict] = []
    redirects: list[dict] = []

    for key, target in table.items():
        target = str(target)
        # Points at this very page -> curtain. See the module docstring.
        if target == own_id:
            curtain.append(_check(str(key)))
            continue
        hit = state.PAGES.get(target)
        if not hit:
            state.note(
                "dead_links",
                page.file.src_uri + ": router '" + str(table_name) + "' has a key "
                + "pointing at '" + target + "', which is not a page on this "
                + "site. That key will never route anywhere.",
            )
            continue
        wrap = _wrap(str(key), prefix + str(hit["url"]))
        if wrap:
            redirects.append(wrap)

    if not curtain and not redirects:
        state.note(
            "notes",
            page.file.src_uri + ": router '" + str(table_name) + "' produced no "
            + "working routes, so no field is rendered.",
        )
        return html

    prompt = str(meta.get("router_prompt") or "Enter your code")
    mode = "curtain" if curtain else "redirect"
    state.note(
        "routers",
        page.file.src_uri + " · " + str(table_name) + " · " + mode
        + " · " + str(len(curtain) + len(redirects)) + " keys",
    )

    # Shuffled so source order says nothing about which key is which.
    rng = secrets.SystemRandom()
    rng.shuffle(curtain)
    rng.shuffle(redirects)

    if not curtain:
        return html + _field("redirect", redirects, prompt)

    # CURTAIN. The body is held behind the `hidden` attribute rather than a CSS
    # class, so it is withheld even before any stylesheet loads -- no flash of
    # content on a slow connection.
    #
    # The <noscript> block REVEALS it and removes the field. That is correct
    # rather than a compromise: this is a pause, not a lock, so a reader with
    # no JavaScript should get the document instead of an input box that can
    # never work. `!important` in an author sheet beats the `hidden` attribute's
    # user-agent rule, which is the only reason this works at all.
    return (
        _field("curtain", curtain + redirects, prompt)
        + "<noscript><style>"
        + ".dr-curtain{display:block !important}.dr-router{display:none}"
        + "</style></noscript>"
        + '<div class="dr-curtain" hidden>' + html + "</div>"
    )
