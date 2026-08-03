"""Stage 04b -- ROUTERS. Type a key, get sent somewhere.

    ---
    id: crew-start
    title: Crew start
    type: page
    status: public
    router: crew
    ---

That page renders a text field. Type a key from the `crew` route table and you
are sent to the page that key names. Type the wrong thing and the router does
not know what to do with you, so nothing happens.

=============================================================================
THIS IS NOT A SECURITY FEATURE AND IS NOT NAMED LIKE ONE
=============================================================================
Deliberately called a ROUTER, with KEYS, not a gate with passwords. The word
choice is the design (Michael, 2026-08-03): a gate implies a wall and invites
trust nobody should extend to it. A router just does not know where to send
someone who types the wrong thing.

What it is genuinely good for: keeping a casual reader out of the developer's
way, and handing one person a code that drops them somewhere specific.

What it is not for: anything that would matter if a stranger read it. The
content repo is public, the markdown is one click away, and a destination page
is reachable by URL whether or not anybody typed a key. Said once, here, in the
file -- not repeated at every call site.

=============================================================================
WHY THE DESTINATION IS ENCRYPTED ANYWAY
=============================================================================
The destination could be a plain string in the page and the router would still
work. It is encrypted with the key instead, and that is worth the twenty lines
for one reason: **a plaintext destination is not a router, it is a list of
links with an input box in front of it.** Anyone reading source would see every
destination and skip the field, which defeats the only thing the feature does.

So: PBKDF2 over the key, AES-GCM over the destination. A wrong key decrypts
nothing rather than failing a comparison. Same envelope shape v1 used for page
bodies, pointed at a URL instead -- which is why that mechanism was worth
keeping even when the premise around it was not.

The wraps are UNLABELLED and shuffled at build time. The page never learns
which key belongs to which route; it tries each wrap until one decrypts.

=============================================================================
WHERE THE KEYS LIVE: instances/<slug>/routes.yml
=============================================================================
One file per site, in the ENGINE, which is the single editable source. Never in
the content repo -- that repo is public and has a Download ZIP button, so a key
committed there ships with the documents.

    # instances/uritp/routes.yml
    crew:
      loadin24: crew-call-sheet
      grid: spac-main-stage

The ROUTE TABLE NAME (`crew`) is shared vocabulary and lives in the page's
frontmatter; the KEYS are local and live here. Same split as object types and
palettes: names shared, values per instance. So `crew` can exist on two sites
with different keys, correctly, because they are different people.

PAIR A ROUTER WITH `status: unlisted` ON ITS DESTINATIONS. Not enforced,
because a destination is sometimes deliberately public, but a router pointing
at a page already sitting in the sidebar is a router with nothing to do.
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


def _encrypt(key: str, destination: str) -> dict | None:
    """Wrap one destination under one key."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        state.note(
            "notes",
            "router: the `cryptography` package is missing, so destinations "
            "cannot be encrypted and routers will not work. Add it to "
            "requirements.txt.",
        )
        return None

    salt = secrets.token_bytes(16)
    nonce = secrets.token_bytes(12)
    derived = hashlib.pbkdf2_hmac(
        "sha256", key.encode("utf-8"), salt, ITERATIONS, dklen=32
    )
    sealed = AESGCM(derived).encrypt(nonce, destination.encode("utf-8"), None)
    return {"s": _b64(salt), "n": _b64(nonce), "w": _b64(sealed)}


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

    depth = page.file.url.count("/")
    prefix = "../" * depth

    wraps = []
    for key, target in table.items():
        hit = state.PAGES.get(str(target))
        if not hit:
            state.note(
                "dead_links",
                page.file.src_uri + ": router '" + str(table_name) + "' has a key "
                + "pointing at '" + str(target) + "', which is not a page on this "
                + "site. That key will never route anywhere.",
            )
            continue
        wrap = _encrypt(str(key), prefix + str(hit["url"]))
        if wrap:
            wraps.append(wrap)

    if not wraps:
        state.note(
            "notes",
            page.file.src_uri + ": router '" + str(table_name) + "' produced no "
            + "working routes, so the field is not rendered.",
        )
        return html

    # Shuffled so source order says nothing about which route is which.
    secrets.SystemRandom().shuffle(wraps)
    state.note(
        "routers",
        page.file.src_uri + " · " + str(table_name) + " · "
        + str(len(wraps)) + " routes",
    )

    prompt = meta.get("router_prompt") or "Enter your code"

    return html + (
        '<form class="dr-router" data-iter="' + str(ITERATIONS) + '"'
        + ' data-routes="' + _b64(json.dumps(wraps).encode("utf-8")) + '">'
        + '<label class="dr-router__label" for="dr-router-key">'
        + str(prompt) + "</label>"
        + '<div class="dr-router__row">'
        + '<input class="dr-router__input" id="dr-router-key" type="text"'
        + ' autocomplete="off" autocapitalize="off" spellcheck="false">'
        + '<button class="dr-router__btn" type="submit">Go</button>'
        + "</div>"
        + '<p class="dr-router__error" role="alert" hidden>'
        + "That code does not go anywhere.</p>"
        + "</form>"
    )
