"""Hook 05 -- serve stylesheets and scripts that live OUTSIDE the content tree.

This is the hook that makes the purity rule physically possible, so read this
before anyone 'fixes' it by moving the CSS back where it looks like it belongs.

MkDocs publishes files it finds inside `docs_dir` and resolves `extra_css`
relative to `docs_dir`. Read literally, that means stylesheets and scripts must
live inside the doc tree. v1 did exactly that, and it is the single largest
reason its content folder was full of machinery.

The way out is the `on_files` event: append File objects whose source is
somewhere else entirely -- here the engine's own assets/ and the instance's
folder. MkDocs treats them as ordinary site files from that point on.

⭐ FEATURE ASSETS ARE PUBLISHED ONLY WHERE THE FEATURE IS USED. The router's
CSS and JS ship only if some page on this site declares a router. A site with
no routers should not carry the crypto for one, a reader should not download
it, and base.css should not grow a section that most sites scroll past.

=============================================================================
⚠️ EVERY ASSET URL CARRIES A CONTENT FINGERPRINT (added 2026-08-03)
=============================================================================
    assets/base.a41f7c92.css

The hash is the first eight hex of the file's own SHA-256, so the URL CHANGES
whenever the bytes change and stays identical when they do not.

This is not a micro-optimisation, it is a correctness fix for the most
expensive failure mode this project has had. `assets/base.css` was a stable URL
served by GitHub Pages, so a browser -- and any CDN in front of it -- kept the
old copy after a deploy. The site said it had updated, the deploy WAS correct,
the markup WAS new, and the styling was hours old. Every symptom pointed at the
build, and the build was innocent.

It cost a full diagnostic round on 2026-08-03 chasing a stale engine that was
real but was not the whole story, and it is the reason "I published and do not
see your change" kept being true. A fingerprint makes that class of report
impossible: if the bytes changed, the URL changed, and nothing can serve the
old one by accident.

Side effect worth knowing: old fingerprinted files are simply absent from the
next deploy, so nothing accumulates.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from mkdocs.structure.files import File

from . import state, theme


def _uses_router() -> bool:
    return any(meta.get("router") for meta in state.BY_SRC.values())


def _fingerprint(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()[:8]


def _stamped(name: str, raw: bytes) -> str:
    """`base.css` + bytes -> `assets/base.a41f7c92.css`."""
    stem, _, suffix = name.rpartition(".")
    return "assets/" + stem + "." + _fingerprint(raw) + "." + suffix


def _read(path: Path) -> bytes | None:
    try:
        return path.read_bytes()
    except OSError:
        return None


def _plan() -> list[tuple[str, bytes]]:
    """Every asset this build publishes, in load order, with its bytes.

    Built once and used by both events: `on_config` needs the URLs and
    `on_files` needs the content, and they must not disagree about either.
    Order is deliberate -- base, then generated tokens, then any feature sheet,
    then the instance sheet LAST, so a site always has the final word on its
    own look.
    """
    plan: list[tuple[str, bytes]] = []

    base = _read(state.ENGINE_ROOT / "assets" / "base.css")
    if base is not None:
        plan.append(("base.css", base))

    plan.append(("tokens.css", theme.build_css().encode("utf-8")))

    if _uses_router():
        for name in ("router.css", "router.js"):
            raw = _read(state.ENGINE_ROOT / "assets" / name)
            if raw is not None:
                plan.append((name, raw))

    site_css = _read(Path(state.INSTANCE.get("dir", ".")) / "theme.css")
    if site_css is not None:
        plan.append(("site.css", site_css))

    return plan


def on_config(config):
    for name, raw in _plan():
        url = _stamped(name, raw)
        target = config.extra_javascript if name.endswith(".js") else config.extra_css
        if url not in target:
            target.append(url)
    return config


def on_files(files, config):
    for name, raw in _plan():
        files.append(File.generated(config, _stamped(name, raw), content=raw))
    return files
