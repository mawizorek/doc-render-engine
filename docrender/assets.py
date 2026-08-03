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

About fifty lines, and the content repo stays pure permanently. A content repo
can be zipped with the green button and contain nothing but documents, which
was the entire origin of this redesign.

SCRIPTS ARE ONLY PUBLISHED WHEN A PAGE ACTUALLY USES THEM. `router.js` ships
only if some page on this site declares a router. A site with no routers
should not carry the crypto for one, and a reader should not download it.
"""

from __future__ import annotations

from pathlib import Path

from mkdocs.structure.files import File

from . import state, theme


def _uses_router() -> bool:
    return any(meta.get("router") for meta in state.BY_SRC.values())


def on_config(config):
    """Register the URLs. The files themselves arrive in on_files.

    Order is deliberate: base, then generated tokens, then the instance sheet
    last, so a site always has the final word on its own look.
    """
    for name in ("assets/base.css", "assets/_tokens.css"):
        if name not in config.extra_css:
            config.extra_css.append(name)
    if (Path(state.INSTANCE.get("dir", ".")) / "theme.css").is_file():
        if "assets/site.css" not in config.extra_css:
            config.extra_css.append("assets/site.css")

    if _uses_router() and "assets/router.js" not in config.extra_javascript:
        config.extra_javascript.append("assets/router.js")

    return config


def _adopt(files, config, source: Path, dest_uri: str) -> None:
    """Publish a file from outside docs_dir at a chosen site path."""
    if not source.is_file():
        return
    files.append(File.generated(config, dest_uri, content=source.read_bytes()))


def on_files(files, config):
    _adopt(files, config, state.ENGINE_ROOT / "assets" / "base.css",
           "assets/base.css")

    files.append(File.generated(
        config, "assets/_tokens.css", content=theme.build_css()
    ))

    _adopt(files, config,
           Path(state.INSTANCE.get("dir", ".")) / "theme.css",
           "assets/site.css")

    if _uses_router():
        _adopt(files, config, state.ENGINE_ROOT / "assets" / "router.js",
               "assets/router.js")

    return files
