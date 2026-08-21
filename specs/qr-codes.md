# BUILD 6 — STATIC QR CODES, resolved through the `links:` registry

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-21, out of the URITP Safety incident-report print session. Indexed from [`next-build-spec.md`](../next-build-spec.md). Decision history: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

> Michael, 2026-08-21: *"i wnat to qr code out to the incident report fowm, in case i print the page and hsare it - that way peopoel can pull up the form on their phone. could also link back to the smae page via id cos ti's embedded there but would want straight up url codes as well"*
>
> And on placement, which decided the whole shape: *"i like the making it a part of exisitng links: organization"*
>
> On determinism, which is the actual engineering requirement: *"they have to be STATIC qr codes - like if a different engienr we asked to amek the same code, they would make the smae image - type htign?"*

---

## One line

A build-time QR code, **generated from a NAME in the existing `links:` registry** (or from a page `id:`), emitted as **inline SVG** so it survives paper, with the payload and the full encoder recipe printed in the build report so a human can verify a code **before** it goes to print.

---

## §0 — WHY PAPER CHANGES EVERY DECISION IN THIS FILE

The use case is not "a QR on a web page." A reader on the page can already tap the embedded form. **The QR exists for the moment the page stops being a page** — printed, handed out, pinned in a shop.

<p><br/></p>

🔴 **THAT INVERTS THE USUAL COST OF BEING WRONG.** Every other reference in this engine is wrong *recoverably*: a dead `@id` renders a struck-through span, somebody sees it, the next publish fixes it. **A wrong QR renders as a perfect, confident, beautiful square** — and by the time anybody discovers it, it is on forty sheets of paper in a scene shop. There is no next publish for paper.

<p><br/></p>

⭐ **SO THE DESIGN PRIORITY IS NOT ELEGANCE, IT IS VERIFIABILITY BEFORE PRINT.** Every ruling below that looks over-cautious is paying for that one property. `urllinks.py` already states the general form of this limit at the top of its own file — an external URL is not verifiable at build time — and a QR takes that unverifiable thing and makes it **unreadable by a human as well.** Nobody proofreads a QR.

---

## 🔴 §1 — THE BOMB: `base_url` IS OVERRIDDEN BY THE PUBLISHING PATH

**This is the finding that must survive even if the rest of this spec is thrown away.**

<p><br/></p>

`instances/uritp-safety/site.yml` declares `base_url: https://mawizorek.github.io/uritp-safety/`. But `.github/workflows/publish-default.yml` **overrides it per publishing path**, discovering the real address with `configure-pages` rather than trusting config, and its own comment says an unfixed value *"poisons doc-index.json -- the one file other sites depend on."* `docrender/instance.py` records `DOCRENDER_BASE_URL` as *"a fact site.yml owns that the PUBLISHING PATH may override for one build."*

<p><br/></p>

🔴 **A POISONED `doc-index.json` IS REPAIRED BY THE NEXT PUBLISH. A POISONED QR IS REPAIRED BY REPRINTING.** Same root cause, categorically different blast radius, and the existing warning was written by somebody who only had the recoverable case in mind.

<p><br/></p>

**Therefore, two hard rules:**

1. 🚫 **An in-site QR with no `base_url` REFUSES TO RENDER.** Not a guess, not a relative path, not a plausible default. Report to `missing_required` and emit the dead span. A QR is the one reference in this engine where declining is unambiguously cheaper than proceeding.
2. 🔴 **EVERY QR's ABSOLUTE PAYLOAD IS PRINTED AS TEXT IN THE BUILD REPORT.** See §5. This is the whole verification surface and it is not optional — a payload you can only read with a phone is a payload nobody checks.

<p><br/></p>

⚠️ **AND A PREVIEW BUILD IS THE DANGEROUS ONE.** `docindex.py` runs a `dry_run` mode where *"nothing deploys and this report is the entire output."* A preview run can carry a preview `base_url`, so a code copied off a preview render is exactly the wrong code. **The report line must state which `base_url` was in force**, not merely the payload.

---

## ⭐ §2 — THE `links:` FOLD-IN IS THE RIGHT ANSWER, AND IT IS ALSO THE ONLY CHEAP ONE

Michael picked this on instinct. It is also the only option that does not touch a file already over its read ceiling, which he did not know.

<p><br/></p>

`docrender/urllinks.py` already owns everything a QR needs to know about an address:

- **Two homes, one namespace, the page wins.** `site.yml` `links:` is the site-wide registry; a page's own frontmatter `links:` block overrides it, **and the override is reported out loud** *"because a silent override is indistinguishable from a typo."*
- **A scheme allow-list**, `_SCHEMES`, including `mailto:` and `tel:`.
- **An `on_files` audit that checks entries nobody has referenced yet**, because *"the report is most useful to the person who just typed the entry."*
- ⭐ **The registry is the feature; the page block is the convenience.** One edit in `site.yml` fixes every page.

<p><br/></p>

🔴 **AND THE DECIDING PRACTICAL FACT: `links:` COSTS NOTHING IN `instance.py`.** `urllinks._site_links()` reads `state.INSTANCE.get('links')` **directly**, so the key needs no per-key handling. That matters because `docrender/instance.py` is **23,047 B — already past the ~22 KB ceiling** before anything is added, and `specs/print-identity.md` §4c is *already* queued to add a `print:` block to it. **A net-new `qr:` config block would have joined a queue for a file that cannot be safely edited. Folding into `links:` skips the queue entirely.** ⚠️ Verify the direct read at build; the evidence is `_site_links()`, not an assumption.

### §2a — the syntax, and the one namespace collision that matters

```
!!! qr "incident_form"        a declared external address
!!! qr "@form-incident-report" a page in THIS site, by id
```

**Resolution ladder, deliberately the same shape `urllinks._resolve` already walks:** page `links:` block → site.yml `links:` → (with a leading `@`) a page `id:` in `state.PAGES`.

<p><br/></p>

⏳ **RULING 1 — does a bare name ever mean a page id?** Recommend **NO: a page id requires the explicit `@` sigil.** A bare name is always a `links:` entry. Otherwise a link name and a page id can collide, and `prefixes.py`'s founding lesson is that a namespace where two things can mean one token gets resolved by whichever table was searched first. **Making the two forms visually different is free; adjudicating a collision is not.**

### 🔴 §2b — `@qr:` IS THE ONE PLACE AN IN-SITE ABSOLUTE URL IS LEGAL, AND THAT IS A DELIBERATE EXCEPTION

`urllinks._bad_scheme` **actively refuses** a URL pointing back into the site:

> *"points back into THIS site. Use @&lt;id&gt; instead: an id follows the page when it moves, and a hardcoded URL to your own site is a link that breaks silently on the next reorganisation."*

⭐ **So Michael's "straight up url codes" ask is HALF ALREADY ILLEGAL, and the engine is right.** A QR payload must be absolute — a phone camera has no page to be relative to — so `@qr:` is the single place in this engine that constructs `base_url` + a page url on purpose. **Stated as an exception with a reason, because an undocumented exception reads as a contradiction to the next person, and this one contradicts a refusal written in prose one module over.**

<p><br/></p>

🚫 **A raw absolute URL typed into the directive is REFUSED.** The address goes in `links:` or it does not exist. Same argument `urllinks.py` makes: *"the same vendor link on twenty pages is twenty edits."* On paper it is twenty edits and forty reprints.

### ⚠️ §2c — THE THIRD CLAIMANT, on the exact page that prompted this

`uritp-safety/40-forms/incident-report.md` **already declares that ClickUp form URL**, in its `forms:` block. Putting the same address in a `links:` entry for the QR makes **two declarations of one address on one page** — the defect this repo retired `roster.json`, `registry.json` and `app-index.md` over.

<p><br/></p>

⏳ **RULING 2 — may `@qr:` read a `forms:` slot?** Recommend **YES, as the last rung**: page `links:` → site `links:` → `@`page-id → **`forms:` slot name**. A form embedded on a page is an address that page already owns, and re-typing it to put it in a square is how the two drift.

<p><br/></p>

⭐ **BUT THE BETTER ANSWER FOR THIS PAGE IS NEITHER: point the QR at the PAGE.** A scanner then lands on the 48-hour rule, the near-miss definition, and the form embedded and open (`collapsed: false`) — instead of a naked form with no instructions. It also survives ClickUp reissuing the form URL, because the address stays in exactly one place. **Recommend `@form-incident-report` as the payload for the founding use case**, with the raw-URL path built and available for genuinely external targets (OSHA, a vendor manual).

---

## 🔴 §3 — DETERMINISM IS REAL BUT IT IS NOT AUTOMATIC

Michael's question — *would a different engineer make the same image* — has a precise answer: **yes, if and only if six things are pinned.** Leave any of them on a library default and two conformant encoders diverge.

<p><br/></p>

| # | Pinned | Why it moves the matrix |
|---|---|---|
| **1** | the **payload bytes**, exactly | one trailing slash is a different symbol |
| **2** | the **encoding mode** | a URL with lowercase forces byte mode; an all-caps one could go alphanumeric, which is a *different matrix for the same text* |
| **3** | the **version** (module count) | derived from payload + EC; deterministic once 1 and 4 are fixed, but it must be RECORDED |
| **4** | the **error-correction level** | see the boost trap below |
| **5** | the **mask** | ISO/IEC 18004 selects it by lowest penalty score, so it is deterministic **for an encoder that implements the standard scoring** — which is an assumption about the library, not a property of the spec |
| **6** | the **SVG serialization** | fixed scale, fixed quiet zone, no XML declaration, no metadata, no varying attribute order — or identical matrices produce different bytes and churn every build |

<p><br/></p>

🔴 **THE BOOST TRAP, AND IT IS THE ONE THAT WOULD ACTUALLY BITE US.** `segno` raises the error-correction level automatically when the chosen version has spare capacity. So *the same payload with the same declared EC level can yield a different EC level, therefore a different matrix,* purely because the payload length changed by a character. **`boost_error` must be explicitly OFF**, and that is not the default.

<p><br/></p>

⚠️ **"ANY GENERATOR PRODUCES THE SAME CODE" IS A CLAIM THE EVIDENCE DOES NOT SUPPORT.** Segno's own library comparison records that the widely-used `qrcode` package **does not reproduce the reference symbol printed in ISO/IEC 18004:2015 Fig. 1**. Interoperability of *scanning* is guaranteed by the standard; **byte-identical generation is not.** Reproducibility here is a property we construct and record, never one we inherit.

<p><br/></p>

⭐ **THEREFORE THE RECIPE IS PART OF THE ARTIFACT.** The build report records encoder **name and version** beside version/EC/mask (§5). A reproducibility claim against an unnamed encoder is not a claim.

### §3a — the dependency

`requirements.txt` is the file whose own header records that *"an unpinned transitive dependency is an unpinned build"* after MkDocs 2.0 broke a live publish. **Pin narrowly:** `segno>=1.6,<2`. Pure Python, zero dependencies, BSD — it adds no transitive surface, which is the only reason a new dependency is defensible in a file that argues this hard about them.

<p><br/></p>

⚠️ **A MAJOR BUMP MAY LEGALLY CHANGE OUR OUTPUT** (serialization defaults, mask tie-breaking). That is not a bug in segno; it is why the upper bound exists and why the version is recorded per code.

<p><br/></p>

⏳ **RULING 3 — error-correction level.** Higher EC survives scuffing and photocopying; it also adds modules, so at a fixed physical size each module gets *smaller*, which cuts the other way. There is a real optimum and it is not a taste question. 🔴 **`specs/print-identity.md` §3f already put the legibility floor for safety-critical print in Hazard Hawthorne's lane, not the engine's. Same ruling, same owner.** Recommend **Q** as the starting point, to be measured, not asserted.

---

## 🔴 §4 — INLINE SVG, AND THE REVERSAL THAT GOT THERE

The first instinct was a generated `.svg` file published through `assets.py` and referenced with the bang-image form, reusing `images.py`. **Three findings killed it.**

<p><br/></p>

🔴 **1. THE STRAY BANG.** `images.py` works because its resolver returns **link markdown** — `[alt](url)` — and `links._LINK` starts matching at the opening bracket, so the `!` in `![alt](@img:x)` sits outside the match and survives to form an image. **A resolver that returns raw `<svg>` leaves the `!` behind as a literal exclamation mark on the page.** Cosmetic, trivially missed in review, and it forces the syntax decision rather than following from it.

<p><br/></p>

🔴 **2. `on_files` RUNS BEFORE ANY PAGE BODY IS READ, AND THE QR LIVES IN THE BODY.** A generated file must be appended at `on_files`; a `!!! qr` directive is discovered at `on_page_markdown`, much later. `assets.py` has already ruled on this exact shape for `!!! data`: *"a `!!! data` block lives in the BODY of a page, not in the first 2000 bytes a frontmatter scan reads, so the router's trick does not transfer,"* and it chose to publish unconditionally rather than to scan bodies. **A file-based QR would need either a body scan or a second frontmatter declaration listing which codes to build — i.e. declaring every QR twice.**

<p><br/></p>

🔴 **3. IT WOULD ENTER `images.INDEX` AND COULD COLLIDE.** `images.on_files` (01f) indexes **every image in the file set** by lowercased filename stem and **refuses duplicates**, on the rule that *"two pictures with one name are two different pictures."* A generated `qr-incident-form.svg` colliding with a real image stem breaks **both** references. Survivable today only because a later hook stage appends after 01f has indexed — **which is a hook-ordering dependency nobody would know they had.** `visibility.py` had to ship a literal stage-order regression detector for exactly this class of silent break.

<p><br/></p>

⭐ **INLINE SVG DISSOLVES ALL THREE AT ONCE.** No file, so no `on_files`, no double declaration, no index entry, no ordering law. `prefixes.py` already permits it: a resolver returns *"a replacement markdown/HTML string."*

<p><br/></p>

⭐ **AND INLINE IS THE SAFER FORMAT ON PAPER, WHICH IS THE WHOLE USE CASE.** `specs/print-identity.md` §4d warns that browsers *"can flatten images at print"* — that a logo can print as an empty box — and explicitly **refuses to assert SVG print behaviour from a read**, requiring a real print preview. An inline SVG's modules are **filled vector paths in the document's own box tree**, not an external image resource a print pipeline can drop. Fewer moving parts in the one medium that cannot be re-published.

<p><br/></p>

**What inline costs, stated rather than discovered:** page weight (a v3 symbol as one path is small, but it is per-page and not cached), no dedup across pages, and **no fingerprinted URL.** ⚠️ That last one is a genuine loss: `assets.py`'s content fingerprint would have made byte-identical output visible as eight hex characters in a diff. **§5 replaces it with something better for this feature — the report prints the payload as READABLE TEXT, which is what somebody about to print actually needs.** A hash proves two builds agree; the text proves the code is *correct*.

<p><br/></p>

⏳ **RULING 4 — inline or file?** Recommend **inline for v1**, on the three findings above. If a print preview later shows inline SVG failing where an `<img>` succeeds, the file path is a rebuild, not a patch — so **the print preview in §6 step 1 is blocking, not confirmatory.**

### §4a — the directive shape follows from ruling 4

**`!!! qr "name"`, block-level, on the `!!! form` precedent** in `docrender/forms.py` — the same *page NAMES a thing, engine BUILDS the element* split, and deliberately the same body vocabulary rather than a third spelling. It dodges the stray bang entirely.

<p><br/></p>

⚠️ **COST: NO `figure.py` REUSE.** Stage 01e wraps captioned **images**; an inline SVG block is not one, so a caption is this module's own job. ⏳ **RULING 5:** caption via a second directive argument, or reuse the entry's `text:` (the ladder `urllinks` already walks: typed label → entry `text:` → the name)? **Recommend the existing ladder.** A third caption mechanism is a third thing to keep in step.

### 🔴 §4b — PHYSICAL SIZE AND THE QUIET ZONE ARE FUNCTIONAL, NOT STYLING

- **The quiet zone is 4 modules and it is load-bearantly part of the symbol.** Crop it with CSS and the code stops scanning. It must be *inside* the SVG viewBox, where no stylesheet can reach it.
- **A minimum size in `mm`, not `px`.** `print-identity.md` §4d already established that this is the one place a physical unit is correct rather than trapped: *"the sheet is a physical object and `px` at print resolution is a fiction."* 🔴 **Not `em`** — §3b of that spec is the whole finding.
- 🔴 **`print-color-adjust: exact`, MANDATORY.** Non-negotiable for a QR: a code printed with adjusted contrast is a code that does not scan. `print.css` already applies this narrowly to elements *whose meaning is carried by a colour*, and a QR is the purest example in the engine.
- 🚫 **NO THEME COLOURS. Black on white, always.** Every other surface here consumes `--dr-*` tokens; a QR must not. Scanners need luminance contrast, `database` is an unproven theme on this very site, and a paper palette correction lives inside generated `tokens.css`. **A themed QR is a dead control that looks like a feature.**

### ⚠️ §4c — IT CONSUMES SHEET-ONE SPACE, WHICH TWO OTHER BUILDS ARE ALSO SPENDING

`print-identity.md` §3g: re-typesetting *"invalidates every manual break, immediately"*, and the letterhead *"consumes vertical space at the top of sheet one, so it moves every break on a one-sheet document too."* **A QR block does the same.** BUILD 5's leading change, BUILD 5's letterhead and this code are three claimants on the same sheet. **Whichever lands last re-previews the others.**

---

## §5 — THE REPORT IS THE VERIFICATION SURFACE

Every build lists **every QR on the site**, in plain text:

```
qr · 40-forms/incident-report.md · "@form-incident-report"
     payload  https://mawizorek.github.io/uritp-safety/40-forms/incident-report/
     base_url https://mawizorek.github.io/uritp-safety/  (site.yml)
     recipe   segno 1.6.6 · byte · v3 · ecc Q · mask 2 · boost off · quiet 4
```

⭐ **THIS IS THE FEATURE, NOT THE PAPERWORK.** It is the only way a human confirms a code before committing it to paper, and it directly answers Michael's determinism question in a form he can read.

<p><br/></p>

⏳ **RULING 6 — a new report bucket, or reuse?** `urllinks.py` explicitly refused its own bucket: *"Inventing a bucket is TWO edits in two files -- `state.reset()` and sizecheck's `_LABELS` -- and a bucket missing from `_LABELS` is printed by nothing at all."* **Recommend paying it anyway, once, for a `qr` INVENTORY bucket.** Failures still go to `dead_links`/`notes`; the inventory is a listing, and `sizecheck._INVENTORY` exists precisely so a worklist is not counted as a defect. **This is the one feature whose listing is a safety control rather than a nicety.**

<p><br/></p>

⚠️ **AND IT INTERACTS WITH TWO QUEUED BUILDS.** `next-build-spec.md` **BUILD 2 Piece C moves `_LABELS` into a new `docrender/report.py`** — so if QR ships second the bucket edit lands there, not in `sizecheck.py`. ⭐ **Piece A's 10-annotations-per-step cap is NOT affected**: inventory buckets are deliberately not annotated, *"because annotating them trains everyone to ignore annotations."*

---

## ⏳ Rulings needed (summary)

1. **Bare name = `links:` only; page id needs an explicit `@`?** Recommend yes.
2. **May `@qr:` read a `forms:` slot as its last rung?** Recommend yes.
3. **Error-correction level.** Recommend Q, **measured**. 🔴 Hawthorne owns the print legibility floor.
4. **Inline SVG or generated file?** Recommend inline. **Blocking print preview first.**
5. **Caption source.** Recommend the existing label → `text:` → name ladder.
6. **A `qr` inventory bucket?** Recommend yes, cost stated.
7. **Does a QR ever render on SCREEN?** It is useless to a reader who can tap the link. Recommend **print-only by default** (`display: none` outside `@media print`, the letterhead's polarity), with an opt-in for signage pages that exist to be photographed. **Not decided — it changes what an author sees while writing.**

---

## Files and sizes (measured at HEAD 2026-08-21 — RE-MEASURE AT BUILD)

| File | Now | Change |
|---|---|---|
| **NEW** `docrender/qr.py` | — | ~7-9 KB. Resolver, recipe, SVG emit, report lines. |
| **NEW** `hooks/03e_qr.py` | — | ~150 B shim. 🔴 **LOAD-BEARING**: `urllinks.py` records that dropping its equivalent means nothing claims the namespace and every reference renders *"unknown peer site"* — correct behaviour, and a mystery to the author. |
| `requirements.txt` | 2,023 B | +1 line, `segno>=1.6,<2`. |
| `mkdocs.yml` | **13,632 B** | one hook registration. ⚠️ Its own comment records a hook that has been dead exactly this way. |
| `docrender/urllinks.py` | 14,403 B | ⭐ **ideally untouched** — the `links:` registry is READ, not modified. Verify `_entry()` is importable without a circular import. |
| `docrender/images.py` | 9,451 B | ⭐ **untouched, and §4 is why.** No generated file enters `images.INDEX`. |
| `docrender/instance.py` | **23,047 B** | ⭐ **UNTOUCHED — §2 is the whole point.** Already over the ceiling with a `print:` block queued behind it. |
| `docrender/sizecheck.py` | 14,859 B | +small (ruling 6). ⚠️ Or `report.py`, if BUILD 2 lands first. |
| `docrender/state.py` | 15,918 B | +1 bucket in `reset()` (ruling 6). |
| **NEW** `assets/print-qr.css` *or* rules in an existing print sheet | — | ⏳ ruling 4/7. 🔴 If a new sheet: it **must** join `_PRINT_ASSETS` in `assets.py`, and `hand_written_css()` picks it up for the token audit automatically. 🪦 `print-scheme.css` is the tombstone proving *"a file in assets/ absent from these tuples is never published and does nothing."* |

<p><br/></p>

🔴 **THIS TABLE WILL BE WRONG WITHIN TWO DAYS. IT IS THE HOUSE SCAR.** `print-identity.md` recorded `mkdocs.yml` at 7,685 B and then at 13,632 B — a 77% drift that moved an *instruction*, not just a figure. **Measure at the moment you act; never quote this table.**

---

## Sequence

1. 🔴 **A PRINT PREVIEW FIRST, BEFORE ANY CODE.** Hand-place one inline SVG QR and one `<img>` SVG QR on a printed sheet and **scan both with a phone.** Ruling 4 rests on it, and `print-identity.md` §4d already refuses to assert SVG print behaviour from a read. One preview, no build.
2. **The resolver, external targets only** (`links:` names). No `base_url`, no page ids, no absolute construction — the half with no §1 exposure.
3. **The report inventory** (§5). Before in-site targets, so the verification surface exists **before** the risky payload does.
4. **In-site page-id targets** (§2b), with the `base_url` refusal (§1).
5. **Print CSS** — size floor, quiet zone, `print-color-adjust`, ruling 7's screen polarity.
6. **The `forms:` rung** (ruling 2), last, because it is a convenience on a mechanism that must already be trustworthy.

---

## What this build is NOT

- 🚫 **Not a dynamic QR.** No redirect service, no shortener, no third party between a safety page and a reader. The payload is baked into the modules. A code telling somebody how to report an injury must not depend on a vendor's uptime.
- 🚫 **Not a raw URL typed into the directive.** The address lives in `links:`, once (§2b).
- 🚫 **Not a themed QR.** Black on white (§4b).
- 🚫 **Not a QR of anything but an address.** No vCards, no wifi payloads, no EPC. Those are real segno features and each is its own decision.
- 🚫 **Not a link checker.** `urllinks.py`'s limit carries over unchanged and gets worse: a code can encode a URL that 404s and will look perfect. ⚠️ **The report prints the payload so a human can catch what the build cannot.**
- 🚫 **Not `@img:` and not a change to `images.py`** (§4).
- 🚫 **Not a new instance config block** (§2).

---

## ⚠️ Declared gaps in this spec

- **`specs/print-identity.md` (BUILD 5) IS PARTLY STALE, AND IT MATTERS HERE.** It lists `print-flow.css` and `print-type.css` as NEW, but `assets.py`'s `_PRINT_ASSETS` at HEAD already registers **five** print sheets (`print.css`, `print-flow.css`, `print-type.css`, `print-space.css`, `print-callout.css`). **So the split shipped, and it shipped with a different seam than the spec proposed** — `print-space.css` and `print-callout.css` exist; the specced `print-identity.css` does **not**, so the letterhead never landed. Read `assets.py` for what exists, never that spec's file table. **Reported, not fixed: it is another build's document.**
- **`next-build-spec.md`'s index said FOUR builds and BUILD 5 already existed.** Corrected in the same PR as this file.
- **Nothing here has been tested against a scanner.** Every claim about scannability is a reading of the standard and of segno's documentation, not a measurement. §6 step 1 exists because of that.
- **`docrender/links.py` (16,596 B) was NOT read whole this session.** The resolution order is quoted from `prefixes.py`'s docstring, which is authoritative about the contract but is not the implementation. **Read `links.py` before writing the resolver.**
