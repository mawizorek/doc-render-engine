# doc-render-engine

The renderer for a family of documentation sites. One app, many instances.

**Status:** v1. Builds. Deployment needs the manual setup in §6.
**Instances:** `template` (live gold standard). Others are added deliberately.

---

## 1. The idea in one paragraph

A content repo holds markdown and nothing else, so its green **Download ZIP**
button hands you exactly the documents and no machinery. Everything that turns
those documents into a website lives here instead: hooks, object schema, theme
tables, and one small config file per site under `instances/`. The engine is
instantiated once per site, each instance points at a different content repo,
and every site gets the same behaviour without anybody copying code.

That button is not a footnote. It is the requirement the whole architecture was
reverse-engineered from.

---

## 2. Repo shape

```
mkdocs.yml              base config. Almost no identity in it, deliberately.
pyproject.toml          the engine is a real installable package.
requirements.txt        pinned build deps, and notes on what is NOT here.

docrender/              THE APP. Knows nothing about any particular site.
  state.py              one shared namespace per build.
  util.py               frontmatter + table parsing. No mkdocs import.
  instance.py           stage 00: become this site. Nav ordering.
  objects.py            stage 01: validate frontmatter, draw the type.
  visibility.py         stage 02: the publication gate.
  links.py              stage 03: @id and @peer:id resolution.
  theme.py              stage 04: tokens from TSV to CSS properties.
  assets.py             stage 05: publish files from OUTSIDE the doc tree.
  pagefoot.py           stage 06: the edit link.
  buildstamp.py         stage 07: is this page the latest push?
  sizecheck.py          stage 08: size budget, LEAK SCAN, build report.
  docindex.py           stage 09: /doc-index.json, the cross-site contract.

hooks/NN_*.py           thin shims. They hold the ORDER; the package holds the
                        logic. The order is load-bearing, see hooks/README.md.

objects/*.yml           WHAT A KIND OF PAGE IS. The schema layer.
theme/*.tsv             WHAT IT LOOKS LIKE. Data, not code.
assets/base.css         the shared style layer.

instances/<slug>/
  site.yml              WHICH SITE. Name, URL, content repo, palette, sections.
  theme.css             that site's own look. Loaded last, has the final word.
  xref-cache.json       last known good peer indexes. COMMITTED on purpose.

.github/workflows/build.yml   the app matrix.
```

---

## 3. The frontmatter contract

The only interface between a content repo and this engine. A page declares
itself; the renderer obeys.

```markdown
---
id: main-stage          # IDENTITY. Permanent. Set once, never change.
title: Main Stage       # what humans see
type: space             # picks the rules in objects/space.yml
status: public          # hidden | unlisted | gated | public
parent: example-house   # an id, never a path
order: 10               # sidebar weight. Absent sorts alphabetically.
revised: 2026-08
---
```

`id`, `title` and `status` are required on every page. **A page with no status
does not build**, which is how nothing reaches the public web because someone
forgot a line.

---

## 4. Adding a site

1. Create the content repo, **under the same account as this one** (§6a says
   why that is not a style preference). Markdown only.
2. `cp -r instances/template instances/<slug>` and edit `site.yml`.
3. Add one row to the matrix in `.github/workflows/build.yml`.
4. **Add the new repo to the `DOCRENDER_TOKEN` PAT's repository list.** Easy to
   forget, and the failure is a 403 at the very last step of an otherwise green
   build.
5. Enable Pages on the content repo: **deploy from branch → `gh-pages`**.

That this is five steps rather than a fork is the point.

**Pin by tag, never by branch, once other sites are consuming this repo.** The
reason these are separate repos is that they fail separately; a floating
reference re-couples them and one bad engine commit breaks every site at once.
Run the lowest-stakes site as the canary on the moving tag and pin the rest.

---

## 5. Rules this engine enforces on itself

- **No site name in the engine.** `sizecheck.py` scans for the active
  instance's proper nouns and **fails the build** if it finds one. It is the
  only hard failure in the pipeline, because a portable engine otherwise stops
  being portable silently.
- **22KB per source file**, 18KB warn. A file that cannot be read whole cannot
  be safely edited.
- **Warn, never die**, for everything else. v1 built with `--strict` and one
  typo froze the entire live site twice in forty minutes while Pages kept
  serving a stale commit. Broken things render as visible markers and appear in
  the report; the deploy continues.

---

## 6. Setup that a human has to do

None of this can be done from inside a workflow.

### a. The `DOCRENDER_TOKEN` secret, on THIS repo

A fine-grained PAT with **Contents: Read and write**. It goes on the engine,
not on a content repo, because **the secret belongs where the workflow runs** —
and every workflow in this family runs here. A content repo holds no workflow
at all; that is the purity rule.

⚠️ **A fine-grained PAT is scoped to ONE resource owner**, which is why every
repo in this family has to live under the same account. A split namespace is
not untidy, it is unbuildable: no single token can both read the engine and
write the site.

⚠️ **A repo TRANSFERRED into the account after the token was created is NOT
added to it automatically.** The token's repository list is a fixed set chosen
at creation. The build then goes green all the way through rendering and dies
with a 403 on the final push, which reads like a broken deploy rather than a
missing checkbox. Check the list at
[Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens?type=beta)
and add the repo.

### b. Pages on each content repo

**Settings → Pages → Deploy from a branch → `gh-pages` / `(root)`.**

Order matters: the first successful build CREATES that branch, so the setting
cannot be flipped until after the first run. Run the workflow, set Pages, run
it once more.

---

## 7. Known limits, stated rather than discovered later

- **`status: gated` is NOT implemented.** A page declaring it is published as
  `unlisted` with a loud warning. Shipping a gate that looks like access
  control but is not is worse than shipping none, because people put things
  behind it. See `docrender/visibility.py`.
- **Cross-site links resolve at BUILD time.** If a peer renames a page, links
  to it are wrong until the next build. The nightly cron closes that to a day;
  a `repository_dispatch` from a peer's deploy closes it to minutes. Closing it
  further means adding a server, which is a bad trade for a doc archive.
- **A Pages site is public even from a private repo.** Privately published
  Pages requires GitHub Enterprise Cloud. Publication states control what
  reaches the SITE, never what is readable in the repo. If it would matter that
  a stranger read it, it does not belong in a doc repo at all.
- **Content repos cannot trigger their own rebuild**, because they hold no
  workflow. That is the cost of purity and it is paid on purpose. Cron plus
  manual dispatch covers it.

---

*v1, 2026-08-03. Built from the v1 sandbox at `maw-agents/uritp-docs`, which
proved the mechanics and is the reason several decisions here are phrased as
reversals.*
