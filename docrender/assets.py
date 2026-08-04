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

=============================================================================
🐛 ON_CONFIG CANNOT SEE THE PAGES. THIS BROKE THE ROUTER COMPLETELY.
=============================================================================
MkDocs runs EVERY hook's `on_config` before ANY hook's `on_files`. So at
`on_config` time `state.BY_SRC` is empty -- nothing has read a frontmatter block
yet -- and the old `_uses_router()` check therefore answered False on every
single build.

Consequence: `router.js` and `router.css` were PUBLISHED (that happens in
`on_files`, by which point BY_SRC is populated) but never LINKED from any page.
The form rendered, looked completely correct, had no JavaScript attached, and so
submitting it did what an unhandled form does: reloaded the page. Which is
precisely the symptom -- "the page reloads so my guess is the unlock just
doesn't hold." The unlock was never running.

The fix is to decide from something that EXISTS at on_config time. Two sources,
both cheap: the instance's `routes.yml`, and a scan of the content tree for the
frontmatter keys. The scan is one pass over small text files, done once and
cached, which is a fair price for a check that cannot silently answer wrong.

⭐ FEATURE ASSETS ARE STILL PUBLISHED ONLY WHERE THE FEATURE IS USED. The
principle was right; the implementation asked a question too early.

⚠️ AND THAT IS WHY THE GENERATED SHEETS ARE UNCONDITIONAL. `tokens.css` and
`marks.css` are built from theme/*.tsv, which is read straight off disk and does
not care which event is running. Nothing about them can answer wrong early, so
they are never gated on a usage check -- the trap above only bites a decision
that needs the page map.

=============================================================================
⚠️ EVERY ASSET URL CARRIES A CONTENT FINGERPRINT
=============================================================================
    assets/base.a41f7c92.css

First eight hex of the file's own SHA-256, so the URL CHANGES when the bytes
change and stays identical when they do not. Not a micro-optimisation: a stable
asset URL on GitHub Pages meant a browser kept the old stylesheet after a
correct deploy, and every symptom pointed at the build. A fingerprint makes
"I published and do not see my change" impossible for assets.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from mkdocs.structure.files import File

from . import markers, state, theme
from .util import load_yaml

_ROUTER_KEYS = ("router:", "router_code:")


def _uses_router(config) -> bool:
    """Does this site have a router anywhere? Answerable at on_config time.

    Cached in state because both events ask, and the answer must not differ
    between them -- a link with no file, or a file with no link, are both worse
    than either problem alone.
    """
    cached = state.REPORT.get("_router")
    if cached is not None:
        return bool(cached)

    found = bool(load_yaml(Path(state.INSTANCE.get("dir", ".")) / "routes.yml"))

    if not found:
        # A page can carry its own codes with no entry in routes.yml, so the
        # route table alone is not enough to answer this.
        docs = Path(str(config.docs_dir))
        if docs.is_dir():
            for path in docs.rglob("*.md"):
                try:
                    head = path.read_text(encoding="utf-8")[:2000]
                except (OSError, UnicodeDecodeError):
                    continue
                if any(key in head for key in _ROUTER_KEYS):
                    found = True
                    break

    state.REPORT["_router"] = found
    return found


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


def _plan(config) -> list[tuple[str, bytes]]:
    """Every asset this build publishes, in load order, with its bytes.

    Built by both events -- `on_config` needs the URLs, `on_files` needs the
    content -- and they must never disagree. Order is deliberate: base, then the
    generated token sheet, then the generated marker-class sheet, then any
    feature sheet, then the instance sheet LAST so a site always has the final
    word on its own look.

    `marks.css` sits after `tokens.css` because it CONSUMES those tokens, and it
    is separate from them because they answer different questions: tokens.css
    says what a colour IS, marks.css says which family USES it.
    """
    plan: list[tuple[str, bytes]] = []

    base = _read(state.ENGINE_ROOT / "assets" / "base.css")
    if base is not None:
        plan.append(("base.css", base))

    plan.append(("tokens.css", theme.build_css().encode("utf-8")))
    plan.append(("marks.css", markers.build_css().encode("utf-8")))

    if _uses_router(config):
        for name in ("router.css", "router.js"):
            raw = _read(state.ENGINE_ROOT / "assets" / name)
            if raw is not None:
                plan.append((name, raw))

    site_css = _read(Path(state.INSTANCE.get("dir", ".")) / "theme.css")
    if site_css is not None:
        plan.append(("site.css", site_css))

    return plan


def on_config(config):
    for name, raw in _plan(config):
        url = _stamped(name, raw)
        target = config.extra_javascript if name.endswith(".js") else config.extra_css
        if url not in target:
            target.append(url)
    return config


def on_files(files, config):
    for name, raw in _plan(config):
        files.append(File.generated(config, _stamped(name, raw), content=raw))
    return files
