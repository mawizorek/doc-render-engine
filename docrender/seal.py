"""The crypto layer shared by the router and its client script.

Split out of `router.py` on 2026-08-04, and the seam is not arbitrary. Two of
the three things in here have a CONTRACT WITH A FILE IN ANOTHER LANGUAGE:
`assets/router.js` re-derives the same key with the same KDF and the same
iteration count, and if these two disagree by one parameter every router on the
site stops working with no error a reader could act on. That contract deserves
its own file rather than a paragraph inside a module about routing.

⚠️ SO: THIS FILE AND `assets/router.js` MOVE IN THE SAME PR. ALWAYS.

=============================================================================
TWO OPERATIONS, AND THEY DO NOT SHARE SALTS
=============================================================================
`check()` -- prove a code without shipping it. Ships a PBKDF2 verifier and
              nothing else, so a page never hands the code to the next person
              who opens it.

`wrap()`  -- actually encrypt something the reader must not have until they
              type a code: a redirect DESTINATION, or the withheld nav manifest.
              AES-256-GCM.

🚫 `check()` USES ONE SALT PER BUILD AND `wrap()` MINTS A FRESH ONE PER CALL.
That asymmetry looks like an inconsistency somebody should tidy, and tidying it
would be a real regression in one direction and a real performance bug in the
other:

  * VERIFIERS want a stable salt, because the derived value has to be CACHEABLE.
    Per-page salts meant a code the reader had already typed was re-derived at
    120,000 iterations on every single page view. See state.ROUTER_SALT.
  * CIPHERTEXT wants fresh material every time, because reusing key material
    across different plaintexts is how AES-GCM stops being safe.

A verifier is public information by design -- it is printed in the page. A
sealed manifest is not. Same primitive, opposite requirements.

=============================================================================
WHAT NONE OF THIS PROTECTS
=============================================================================
A curtain hides a page BODY in the DOM; it does not encrypt it. The markdown is
public in the content repo either way. Nothing in this file changes that, and
the naming is deliberately `seal`, not `encrypt` or `lock`, so nobody reads a
stronger promise into an import. Full reasoning in `router.py`.
"""

from __future__ import annotations

import base64
import hashlib
import secrets

from . import state

#: ⚠️ MIRRORED IN `assets/router.js` as `data-iter` on the form. The client
#: reads it off the markup rather than hardcoding it, so this is the one place
#: it is written -- but a change still ships with the JS, because the JS is what
#: proves the pair still agrees.
ITERATIONS = 120_000


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def derive(key: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac(
        "sha256", key.encode("utf-8"), salt, ITERATIONS, dklen=32
    )


def verifier_salt() -> bytes:
    """One salt for every curtain verifier on this build. See state.ROUTER_SALT.

    Minted lazily rather than at import, because a module-level value survives
    `mkdocs serve`'s in-process rebuilds and would then outlive the build it
    belongs to -- exactly what state.reset() exists to prevent.
    """
    if not state.ROUTER_SALT:
        state.ROUTER_SALT = secrets.token_bytes(16)
    return state.ROUTER_SALT


def check(key: str) -> dict:
    """A verifier for a curtain: prove the code without shipping the code."""
    salt = verifier_salt()
    return {"s": b64(salt), "h": b64(derive(key, salt))}


def wrap(key: str, plaintext: str) -> dict | None:
    """Seal a redirect destination, or a nav manifest, under its key.

    🚫 Random salt AND nonce, per call, never the shared verifier salt. This is
    encryption, not verification -- see the module docstring.

    Returns None when `cryptography` is absent, which every caller must treat as
    a real failure rather than an empty result: the thing being sealed is
    something a reader is not supposed to have yet.
    """
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        state.note(
            "notes",
            "seal: the `cryptography` package is missing, so redirect "
            "destinations and withheld nav entries cannot be sealed. Add it to "
            "requirements.txt.",
        )
        return None
    salt = secrets.token_bytes(16)
    nonce = secrets.token_bytes(12)
    sealed = AESGCM(derive(key, salt)).encrypt(
        nonce, plaintext.encode("utf-8"), None
    )
    return {"s": b64(salt), "n": b64(nonce), "w": b64(sealed)}
