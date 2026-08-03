"""docrender -- the doc-site renderer.

This package is an APP. It knows how to turn a folder of markdown into a site.
It does not know, and must never know, anything about any particular site.

Everything site-specific lives in `instances/<slug>/site.yml`, loaded at build
time by the first hook. If you find yourself typing the name of a venue, a
theatre, a company or a person into this package, that is a bug in the design
and not a shortcut.

There is a test for exactly that: docrender/sizecheck.py scans the engine
source for the active instance's own name and fails the build if it finds one.
A seam nobody tests is a seam that closes.
"""

__version__ = "0.1.0"
