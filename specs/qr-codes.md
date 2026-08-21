# BUILD 6 — STATIC QR CODES, resolved through the `links:` registry

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-21, out of the URITP Safety incident-report print session. Indexed from [`next-build-spec.md`](../next-build-spec.md). Decision history: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

> Michael, 2026-08-21, the use case: *"i wnat to qr code out to the incident report fowm, in case i print the page and hsare it - that way peopoel can pull up the form on their phone."*
>
> Placement: *"i like the making it a part of exisitng links: organization"*
>
> Determinism: *"they have to be STATIC qr codes - like if a different engienr we asked to amek the same code, they would make the smae image."*
>
> ✅ The grammar: *"display = and print = are both optional and the only thing that declares where those qr codes appear"* + *"i don't want to be declaring error level in my line. we will set it glboally for all builds in all renderer apps."*
>
> ✅ **On the printed download link, which closed ruling 9 and produced §4d.3:** *"pdfs currently still work if they have links so this shoudl still apply where the pdf links to a donalod of the qr code jsut like other links do for their links"*

---

## One line

A build-time QR code, **generated from a NAME in the existing `links:` registry** (or from a page `id:`), placed by **two optional boolean options** on the directive line, defaulting to a **download link that stays live in a PDF** — with the payload and encoder recipe printed in the build report so a human can verify a code **before** it goes to print.

---

## §0 — WHY PAPER CHANGES EVERY DECISION IN THIS FILE

A reader on the page can already tap the embedded form. **The QR exists for the moment the page stops being a page** — printed, handed out, pinned in a shop.

<p><br/></p>

🔴 **THAT INVERTS THE USUAL COST OF BEING WRONG.** Every other reference here fails *recoverably*: a dead `@id` renders a struck-through span, somebody sees it, the next publish fixes it. **A wrong QR renders as a perfect, confident square** — and by the time anybody notices it is on forty sheets in a scene shop. There is no next publish for paper.

<p><br/></p>

⭐ **SO THE DESIGN PRIORITY IS VERIFIABILITY BEFORE PRINT, NOT ELEGANCE.** `urllinks.py` already states the general form of this limit — an external URL is not verifiable at build time — and a QR takes that unverifiable thing and makes it **unreadable by a human as well.** Nobody proofreads a QR.

<p><br/></p>

⚠️ **AND SINCE §4d.3, "PRINT" IS TWO DIFFERENT DESTINATIONS.** A **PDF** keeps live hyperlinks; **toner on paper** keeps none. CSS cannot tell them apart — both are `@media print` — so any rule here serves both and must be judged against both.

---

## 🔴 §1 — THE BOMB: `base_url` IS OVERRIDDEN BY THE PUBLISHING PATH

**The finding that must survive even if the rest of this spec is thrown away.**

<p><br/></p>

`instances/uritp-safety/site.yml` declares `base_url: https://mawizorek.github.io/uritp-safety/`. But `.github/workflows/publish-default.yml` **overrides it per publishing path**, discovering the real address with `configure-pages` rather than trusting config, and its own comment says an unfixed value *"poisons doc-index.json -- the one file other sites depend on."* `instance.py` records `DOCRENDER_BASE_URL` as *"a fact site.yml owns that the PUBLISHING PATH may override for one build."*

<p><br/></p>

🔴 **A POISONED `doc-index.json` IS REPAIRED BY THE NEXT PUBLISH. A POISONED QR IS REPAIRED BY REPRINTING.** Same root cause, categorically different blast radius, and the existing warning was written by somebody who only had the recoverable case in mind.

<p><br/></p>

**Two hard rules:**

1. 🚫 **An in-site QR with no `base_url` REFUSES TO RENDER.** Not a guess, not a relative path, not a plausible default. Report to `missing_required`, emit the dead span. This is the one reference in the engine where declining is unambiguously cheaper than proceeding.
2. 🔴 **EVERY QR's ABSOLUTE PAYLOAD IS PRINTED AS TEXT IN THE BUILD REPORT** (§5). Not optional — a payload you can only read with a phone is a payload nobody checks.

<p><br/></p>

⚠️ **AND A PREVIEW BUILD IS THE DANGEROUS ONE.** `docindex.py` has a `dry_run` mode where *"nothing deploys and this report is the entire output."* A preview run can carry a preview `base_url`, so a code copied off a preview render is exactly the wrong code. **The report line states which `base_url` was in force**, not merely the payload.

---

## ⭐ §2 — THE `links:` FOLD-IN IS THE RIGHT ANSWER, AND ALSO THE ONLY CHEAP ONE

Michael picked this on instinct. It is also the only option that does not touch a file already over its read ceiling, which he did not know.

<p><br/></p>

`docrender/urllinks.py` already owns everything a QR needs to know about an address: **two homes with the page winning** (and the override *reported*, *"because a silent override is indistinguishable from a typo"*), a **scheme allow-list**, and an **`on_files` audit of entries nobody has referenced yet** because *"the report is most useful to the person who just typed the entry."* ⭐ **The registry is the feature; the page block is the convenience.**

<p><br/></p>

🔴 **AND THE DECIDING PRACTICAL FACT: `links:` COSTS NOTHING IN `instance.py`.** `urllinks._site_links()` reads `state.INSTANCE.get('links')` **directly**, so the key needs no per-key handling — and `instance.py` is **23,047 B, already past the ~22 KB ceiling**, with `print-identity.md` §4c queued to add a `print:` block to it. **A net-new `qr:` config block would have joined a queue for a file that cannot be safely edited.** ⚠️ Verify the direct read at build; the evidence is `_site_links()`, not an assumption.

### §2a — the syntax, and the one namespace collision that matters

```
!!! qr "incident_form"          a declared external address
!!! qr "@form-incident-report"  a page in THIS site, by id
```

**Ladder, deliberately the shape `urllinks._resolve` already walks:** page `links:` → site.yml `links:` → (with a leading `@`) a page `id:` in `state.PAGES`.

<p><br/></p>

⏳ **RULING 1 — does a bare name ever mean a page id?** Recommend **NO: a page id requires the explicit `@`.** Otherwise a link name and a page id can collide, and `prefixes.py`'s founding lesson is that a namespace where two things mean one token gets resolved by whichever table was searched first. **Making the forms visually different is free; adjudicating a collision is not.**

### 🔴 §2b — `@qr:` IS THE ONE PLACE AN IN-SITE ABSOLUTE URL IS LEGAL, AND THAT IS A DELIBERATE EXCEPTION

`urllinks._bad_scheme` **actively refuses** a URL pointing back into the site: *"points back into THIS site. Use @&lt;id&gt; instead: an id follows the page when it moves, and a hardcoded URL to your own site is a link that breaks silently on the next reorganisation."*

<p><br/></p>

⭐ **So the "straight up url codes" ask is HALF ALREADY ILLEGAL, and the engine is right.** A QR payload must be absolute — a phone camera has no page to be relative to — so `@qr:` is the single place in this engine that constructs `base_url` + a page url on purpose. **Written down as an exception with a reason, because an undocumented exception reads as a contradiction to the next person, and this one contradicts a refusal in prose one module over.**

<p><br/></p>

🚫 **A raw absolute URL typed into the directive is REFUSED.** The address goes in `links:` or it does not exist — *"the same vendor link on twenty pages is twenty edits,"* and on paper it is twenty edits and forty reprints.

### ⚠️ §2c — THE THIRD CLAIMANT, on the exact page that prompted this

`uritp-safety/40-forms/incident-report.md` **already declares that ClickUp form URL** in its `forms:` block. A `links:` entry for the QR makes **two declarations of one address on one page** — the defect this repo retired three manifests over.

<p><br/></p>

⏳ **RULING 2 — may `@qr:` read a `forms:` slot?** Recommend **YES, as the last rung.** A form embedded on a page is an address that page already owns, and re-typing it to put it in a square is how the two drift.

<p><br/></p>

⭐ **BUT THE BETTER ANSWER FOR THIS PAGE IS NEITHER: point the QR at the PAGE.** A scanner then lands on the 48-hour rule, the near-miss definition, and the form embedded and open — instead of a naked form with no instructions. It also survives ClickUp reissuing the form URL. **Recommend `@form-incident-report` for the founding use case.**

---

## 🔴 §3 — DETERMINISM IS REAL BUT IT IS NOT AUTOMATIC

*Would a different engineer make the same image* has a precise answer: **yes, if and only if six things are pinned.**

<p><br/></p>

| # | Pinned | Why it moves the matrix |
|---|---|---|
| **1** | the **payload bytes** | one trailing slash is a different symbol |
| **2** | **byte mode, always** | alphanumeric is denser but **uppercase-only**, and a URL path is case-sensitive, so a URL can never legally take it. Pinned so an all-caps payload cannot silently switch modes. |
| **3** | the **version** | derived from payload + EC; deterministic once 1 and 4 are fixed, but it must be RECORDED |
| **4** | the **error-correction level** | ✅ an ENGINE CONSTANT — §3b |
| **5** | the **mask** | ISO/IEC 18004 picks it by lowest penalty score, deterministic **for an encoder implementing the standard scoring** — an assumption about the library, not a property of the spec |
| **6** | the **serialization** | fixed scale, fixed quiet zone, no XML declaration, no metadata, no varying attribute order |

<p><br/></p>

🔴 **THE BOOST TRAP.** `segno` raises the EC level automatically when the chosen version has spare capacity — so *the same payload at the same declared level can yield a different level, therefore a different matrix,* purely because the payload changed by one character. **`boost_error` must be explicitly OFF**, and that is not the default. ⭐ **The cost is real and is stated here rather than discovered by whoever "optimises" it back on: we deliberately leave spare capacity unused.** That is the price of reproducibility, and it is right — a code whose recovery level silently improves is a code whose matrix silently changed.

<p><br/></p>

⚠️ **"ANY GENERATOR PRODUCES THE SAME CODE" IS NOT SUPPORTED BY THE EVIDENCE.** Segno's own library comparison records that the widely-used `qrcode` package **does not reproduce the reference symbol in ISO/IEC 18004:2015 Fig. 1**. Interoperability of *scanning* is guaranteed by the standard; **byte-identical generation is not.** ⭐ So the recipe is part of the artifact and the report records encoder name and version (§5) — a reproducibility claim against an unnamed encoder is not a claim.

<p><br/></p>

⭐ **AND MICHAEL'S TWO-LINE EXAMPLE IS THE PROOF THIS PAYS FOR ITSELF.** `display=true` on one line and a bare directive on the next encodes **the same payload twice on one page.** Under a pinned recipe those matrices are necessarily identical; under library defaults with boost on they could differ, same page, same build.

### §3a — the dependency

**Pin narrowly: `segno>=1.6,<2`.** Pure Python, zero dependencies, BSD — no transitive surface, which is the only reason a new dependency is defensible in a file whose header records that *"an unpinned transitive dependency is an unpinned build"* after MkDocs 2.0 broke a live publish. ⚠️ **A major bump may legally change our output** (serialization defaults, mask tie-breaking); that is why the upper bound exists and why the version is recorded per code.

### ✅ §3b — ERROR CORRECTION IS ONE GLOBAL CONSTANT (RULINGS 3 AND 8 CLOSED)

> *"i don't want to be declaring error level in my line. we will set it glboally for all builds in all renderer apps. let's not overthink it here."*

✅ **`ecc=` IS NOT A DIRECTIVE OPTION. It is a constant in `docrender/qr.py`** — not `site.yml`, not instance config, because *"all renderer apps"* means the engine rather than a site. **Ruling 8 is withdrawn: there is nothing to override.**

<p><br/></p>

⭐ **AND THE GLOBAL IS SAFER THAN IT SOUNDS, WHICH IS WHY "DON'T OVERTHINK IT" IS CORRECT HERE: CHANGING IT NEVER INVALIDATES PRINTED PAPER.** The payload is unchanged by an EC change, so **every code already on a wall keeps scanning**; only newly generated codes differ. 🔴 **The exact reverse of §1**, and worth holding side by side: `base_url` is unforgiving after print, EC is freely reversible. **The reversible decision came off the per-line surface and the unforgiving one stayed on it, which is the right way round.**

<p><br/></p>

**Since it was asked — ISO/IEC 18004 defines exactly four levels and there are no others:**

<p><br/></p>

| Level | Recovers | For |
|---|---|---|
| **L** | ~7% | screen-only, pristine conditions. 🚫 Not for paper. |
| **M** | ~15% | the de facto default in most libraries and web generators |
| **Q** | ~25% | print that gets handled — the safety case |
| **H** | ~30% | print that gets abused, or a logo overlaid on the code |

<p><br/></p>

🔴 **THE ONE NON-OBVIOUS FACT, AND THE ONLY REASON THIS NEEDS A MEASUREMENT: EC IS NOT MONOTONIC AT A FIXED PHYSICAL SIZE.** Correction is stored as extra codewords, extra codewords need a bigger symbol, and a bigger symbol at the same printed size means **each module is physically smaller** — and module size is what a camera has to resolve. **So `H` in a 25 mm square can scan WORSE than `Q` in the same square.** The instinct that more correction is safer is wrong in exactly the case we care about.

<p><br/></p>

⏳ **RULING 3 (NARROWED) — what is the constant?** Recommend **Q**, measured once at §6 step 1 and then left alone. 🔴 **`print-identity.md` §3f already put the legibility floor for safety-critical print in Hazard Hawthorne's lane, not the engine's. Same ruling, same owner.** ⭐ One free lever if the measurement is tight: **byte-mode capacity falls off as EC rises, so a shorter PAGE PATH buys a higher level at the same module count.** Not a shortener — this build is static by definition.

---

## 🔴 §4 — THE RENDERED CODE IS INLINE SVG, NOT A PUBLISHED FILE

The first instinct was a generated `.svg` published through `assets.py` and referenced with the bang-image form, reusing `images.py`. **Three findings killed it, and all three are about the RENDERED code specifically** (§4d.3 revisits them for the DOWNLOAD, which is a different job):

<p><br/></p>

1. 🔴 **THE STRAY BANG.** `images.py` works because its resolver returns **link markdown**, and `links._LINK` starts matching at the opening bracket — so the `!` in `![alt](@img:x)` survives outside the match to form an image. **A resolver returning raw `<svg>` leaves the `!` behind as a literal exclamation mark.**
2. 🔴 **`on_files` RUNS BEFORE ANY PAGE BODY IS READ, AND THE QR LIVES IN THE BODY.** `assets.py` already ruled on this exact shape for `!!! data`: *"a `!!! data` block lives in the BODY of a page, not in the first 2000 bytes a frontmatter scan reads, so the router's trick does not transfer."*
3. 🔴 **IT WOULD ENTER `images.INDEX` AND COULD COLLIDE.** That index keys every image by lowercased filename stem and **refuses duplicates**, because *"two pictures with one name are two different pictures"* — so a generated stem clashing with a real one breaks **both** references, survivable only through a hook-ordering dependency nobody would know they had.

<p><br/></p>

⭐ **INLINE DISSOLVES ALL THREE.** No file, no `on_files`, no index entry, no ordering law. `prefixes.py` already permits it: a resolver returns *"a replacement markdown/HTML string."*

<p><br/></p>

⭐ **AND INLINE SVG IS THE SAFER FORMAT ON PAPER, WHICH IS THE WHOLE USE CASE.** `print-identity.md` §4d warns browsers *"can flatten images at print"* — that a logo can print as an empty box — and **refuses to assert SVG print behaviour from a read.** An inline SVG's modules are **filled vector paths in the document's own box tree**, not an external resource a print pipeline can drop.

<p><br/></p>

**What inline costs:** page weight (per-page, not cached), no dedup across pages, and **no fingerprinted URL** — `assets.py`'s content fingerprint would have made byte-identical output visible as eight hex characters in a diff. **§5 replaces it with something better here: the report prints the payload as READABLE TEXT.** A hash proves two builds agree; the text proves the code is *correct*.

<p><br/></p>

⏳ **RULING 4 — inline or file, for the RENDERED code?** Recommend **inline for v1.** If a print preview shows inline SVG failing where an `<img>` succeeds, the file path is a rebuild rather than a patch — so **§6 step 1 is blocking, not confirmatory.**

### §4a — the directive shape

**`!!! qr "name"`, block-level, on the `!!! form` precedent** in `docrender/forms.py` — the same *page NAMES a thing, engine BUILDS the element* split, and deliberately the same body vocabulary rather than a third spelling. It dodges the stray bang entirely.

### 🔴 §4b — PHYSICAL SIZE AND THE QUIET ZONE ARE FUNCTIONAL, NOT STYLING

- **The quiet zone is 4 modules and it is part of the symbol.** Crop it with CSS and the code stops scanning. It lives *inside* the SVG viewBox where no stylesheet can reach it.
- **A minimum size in `mm`, not `px`.** `print-identity.md` §4d established this is the one place a physical unit is correct rather than trapped: *"the sheet is a physical object and `px` at print resolution is a fiction."* 🔴 **Not `em`.**
- 🔴 **`print-color-adjust: exact`, MANDATORY.** A code printed with adjusted contrast is a code that does not scan. ⭐ **And this is a one-selector edit, not a new decision:** `print.css` already carries a narrow list of elements *"whose MEANING is carried by a colour"* and its own comment reasons exactly this way about a `!!! danger` border. A QR is the purest example in the engine. ⚠️ Read that list's own warning first — *"a rule that forces one colour to print forces all of them on that element"* — which is harmless here (black on white is the whole design) but is the reason the list is narrow.
- 🚫 **NO THEME COLOURS. Black on white, always.** ⭐ **`print.css` supplies an independent argument for this that outranks mine:** paper's ground is declared `transparent`, *"the ABSENCE of a decision rather than a substitute for one,"* because no vector owns paper — and 16 of 19 canonical palettes carry semantic colours authored against a DARK ground straight into their light row. **A themed QR would inherit that defect on the one surface that cannot be re-published.**

### ⚠️ §4c — IT CONSUMES SHEET-ONE SPACE, WHICH TWO OTHER BUILDS ARE ALSO SPENDING

`print-identity.md` §3g: re-typesetting *"invalidates every manual break, immediately"*, and the letterhead *"consumes vertical space at the top of sheet one, so it moves every break on a one-sheet document too."* **A QR block does the same.** BUILD 5's leading change, BUILD 5's letterhead and this code are three claimants on one sheet. **Whichever lands last re-previews the others.**

### ✅ §4d — THE GRAMMAR: TWO BOOLEANS, AND A DEFAULT THAT IS A DOWNLOAD (RULINGS 5, 7, 7b CLOSED)

> *"display = and print = are both optional **and the only thing that declares where those qr codes appear**... if either is provided, then nothing besides the rectangle prints, and any headers or footers would be defined inline with the markdown text or in frontmatter."*

<p><br/></p>

| Written | Renders |
|---|---|
| `!!! qr "@x"` | **a download link**, text *"QR Code"*, delivering a PNG. Nothing else. |
| `!!! qr "@x" display=true` | the code on screen. **No download link.** |
| `!!! qr "@x" print=true` | the code on paper. **No download link.** |
| `!!! qr "@x" display=true print=true` | the code in both media. **No download link.** |

<p><br/></p>

**Two lines give both behaviours** — Michael's own example, needing no new syntax:

```
!!! qr "@form-incident-report" display=true
!!! qr "@form-incident-report"
```

<p><br/></p>

⭐ **THE ORGANISING LINE: AN ADDRESS BELONGS TO THE REGISTRY; A PLACEMENT BELONGS TO THE LINE.** 🔴 **And "the only thing that declares where those qr codes appear" is a HARD RULE with teeth: no site.yml default, no frontmatter placement key, no theme opinion.** One surface decides placement; a second surface that could override it is the drift this repo has retired three manifests over.

<p><br/></p>

✅ **RULING 5 (caption) IS CLOSED BY THE SAME SENTENCE: THE ENGINE EMITS NO CAPTION, EVER.** Headers and footers are the author's prose, above and below the directive. **Strictly better than the label ladder I recommended**, because a caption is content and content belongs to the content repo — and it **deletes** the `figure.py` problem rather than solving it. There is nothing to wrap.

<p><br/></p>

⚠️ **BUT A BARE RECTANGLE NEEDS AN ACCESSIBLE NAME, AND THAT IS NOT A CAPTION.** A QR with no visible text and no `<title>` is silence to a screen reader, and on a safety page that is a compliance surface. **Recommend an SVG `<title>` carrying the resolved payload** — invisible in both media, so it never becomes the caption just ruled out.

#### 🔴 §4d.1 — THE DEFAULT NEEDS AN ARTIFACT, WHICH REOPENS §4's FILE PROBLEM

**A download needs something to download**, and §4 killed generated files because `on_files` runs before any body is read.

<p><br/></p>

🪦 <s>**Resolved with a `data:image/png;base64,…` href plus the `download` attribute** — no file, so §4's three findings stay dissolved and the download still hands over a real PNG.</s> **SUPERSEDED BY §4d.3 THE SAME DAY, and struck rather than deleted because the reasoning was right about the mechanism and wrong about the destination.** A `data:` URI is dead in a PDF, which is precisely where Michael needs it live.

<p><br/></p>

⭐ **PNG IS STILL THE RIGHT FORMAT FOR THE DOWNLOAD, WHICH CONTRADICTS §4's SVG PREFERENCE ON PURPOSE.** §4 chose SVG for the *rendered* code because vector survives print. A *download* is destined elsewhere — a poster, a slide, an email, a call-board — and consumer tools handle PNG reliably and SVG badly. **Two jobs, two correct answers.** 🔴 `segno` writes PNG with no third-party imaging dependency, which is the only reason this does not drag Pillow into `requirements.txt`. ⚠️ **Verify in the pinned version.**

<p><br/></p>

⚠️ **PNG DETERMINISM IS A SEPARATE, SMALLER PROBLEM THAN §3's.** A PNG carries compression settings and optional metadata chunks, so two runs can differ in bytes while encoding an identical matrix. ⭐ **Now that §4d.3 makes it a real published file, that matters more than it did under a data URI: a fingerprinted asset URL changes when the bytes change, so nondeterministic PNG output would churn the URL on every build.** 🔴 **Pin the scale and suppress optional metadata**, and record the scale — a downloaded PNG's pixel size is what decides whether it is usable at poster scale, and that is the one property a person notices.

#### 🔴 §4d.2 — TWO HOLES IN THE GRAMMAR, BOTH SILENT, BOTH CHEAP TO CLOSE

**A. `display=false` / `print=false` renders NOTHING AT ALL.** The rule is *"if either is provided"* — so `print=false` is provided, which suppresses the download link, and then declines to print. **A declared QR that appears in no medium and reports nothing.** 🚫 **Refuse it loudly:** an explicit `false` is legal to write (it reads naturally and somebody will), but **a directive whose every declared medium is false is reported to `missing_required` and renders the dead span.** A no-op that looks like a declaration is the defect `mkdocs.yml`'s own comment records a dead hook for.

<p><br/></p>

**B. A `print=true`-only code is INVISIBLE TO ITS OWN AUTHOR.** On screen, *"failed to resolve"* and *"resolved and correctly hidden"* are **the same blank space.** This engine kills invisible controls on sight, so the mitigation is mandatory: **the §5 report line states the media flags for every code**, and it is the only surface that can tell those two states apart. ⚠️ **Verification for a print-only code is print preview or the report — never the rendered page.** ⭐ **The default case is exempt, and that is a real virtue of Michael's design:** a bare directive renders a visible link, so the commonest usage is self-evidencing.

#### ✅ §4d.3 — THE DOWNLOAD LINK STAYS LIVE IN A PDF (RULING 9 CLOSED)

> Michael, 2026-08-21: *"pdfs currently still work if they have links so this shoudl still apply where the pdf links to a donalod of the qr code jsut like other links do for their links"*

✅ **RULING 9 CLOSED AGAINST MY RECOMMENDATION, AND HE IS RIGHT.** I proposed hiding the default link in `@media print` on the grounds that *"QR Code"* is dead text on paper. **That reasoning silently assumed print means TONER.** A PDF is the artifact he actually shares, it keeps live hyperlinks, and every other link on the page already survives into it. **Hiding the QR link would have made it the ONE link in the engine that vanishes from a PDF** — a special case with no justification, which is exactly the shape this repo kills.

<p><br/></p>

⭐ **AND `print.css` SETTLES IT INDEPENDENTLY, IN A BLOCK WHOSE WHOLE POINT IS *DO NOT WRITE A RULE HERE*.** Its dead-reference section carries no CSS at all and explains why: the signal *"is now a dotted underline declared once in assets/base.css, unscoped to any medium, so it reaches paper on its own,"* plus 🚫 *"DO NOT RE-DECLARE IT HERE. A second copy of a decoration is a second claimant on one truth."* **A link that reaches paper by default is the documented, verified-on-paper behaviour of this engine. Ruling 9's answer was already written; I just had not read the file.**

<p><br/></p>

🔴 **BUT IT KILLS §4d.1's MECHANISM, AND THAT IS THE REAL FINDING: A `data:` URI IS DEAD IN A PDF.** PDF viewers refuse non-`http(s)` link targets as a security matter, and print-to-PDF generally drops the annotation rather than carrying a megabyte of base64 into the file. ⚠️ **So the data URI is the one artifact shape that works perfectly on screen and fails in exactly the medium this ruling is about — with no error anywhere.** Michael's ruling and §4d.1's mechanism cannot both stand.

<p><br/></p>

⭐ **THE RESOLUTION, AND IT DISSOLVES §4's TIMING OBJECTION RATHER THAN ARGUING WITH IT: WRITE THE PNG AT `on_post_build`, NOT AT `on_files`.**

<p><br/></p>

§4's problem was never "files are bad" — it was that a **body-discovered** directive cannot append to the `files` collection, because `on_files` has already run. **`on_post_build` runs LAST, after every page body has been read**, and `docindex.py` already writes a real published file there (`doc-index.json`, the file sibling sites resolve cross-site links against). So:

- the resolver computes the payload at page-render time and emits `<a href="assets/qr/<hash>.png" download="qr-<name>.png">QR Code</a>`
- the href is **derived, not discovered** — a content hash of the pinned recipe plus payload — so it can be written confidently before the file exists
- `on_post_build` writes every collected PNG into `site_dir` at those paths

<p><br/></p>

⭐ **AND §4's THREE FINDINGS STAY DEAD:** no `on_files` participation, so **nothing enters `images.INDEX`** and there is no stem collision and no hook-ordering law; and the resolver still returns markdown, so **no stray bang.** ⭐ **A content-hash filename also satisfies §3 for free** — identical recipe plus identical payload means an identical path, so a rebuild produces no diff.

<p><br/></p>

⚠️ **THREE THINGS TO VERIFY, ALL REASONED NOT MEASURED.** That MkDocs `on_post_build` can write into `site_dir` at an arbitrary path (**strongly implied by `docindex.py` doing it, but its exact write mechanism was NOT read**); that a `download` attribute on a same-origin `http(s)` URL saves rather than navigates; and that a relative `href` resolves correctly from every depth in the tree — 🔴 **use `util.relative_url`, never a `../` count.** `images.py` names that arithmetic as the bug this house *"shipped wrong three separate times"* and `print-identity.md` §4c repeats it: **a letterhead, or a QR, renders at every depth and is maximally exposed.**

<p><br/></p>

⚠️ **AND THE HONEST REMAINING GAP: ON TONER, THE LINK IS STILL DEAD TEXT.** Nothing fixes that — paper has no clicks. The ruling is that **the PDF case wins the tie**, because it is the shared artifact and because a link that prints as text is the engine's existing, verified behaviour for every other link. 🚫 **Not solved by printing the URL beside it** (`print.css` deliberately has no such rule, and the URL of a hashed PNG is unreadable anyway). ⭐ **If a toner reader needs the code, that is what `print=true` is for** — which is the whole reason placement is per-line.

### 🔴 §4e — THE OPTIONS ARE BARE `key=value`, NOT BRACES

The obvious spelling is the attr_list-style block used for captions: `{ display=true }`. 🚫 **Refused, on three things already written down here.**

<p><br/></p>

1. **Braces are CONTESTED TERRITORY and two of our own modules disagree about them.** `markers.on_page_markdown` hands an unrecognised brace block back untouched, *"rather than eating syntax that belongs to somebody else"*; `cells.plain()` strips **every** brace block. **BUILD 1's spec names that disagreement as a live defect.**
2. 🔴 **BUILD 1's `clean.py` WOULD EAT THEM.** Its job is to strip *our declared vocabulary* and leave foreign attr_list alone — and a brace block that is genuinely ours is exactly what it removes. **A QR option in braces is a QR option a future stripper deletes.**
3. **Bare `key=value` after the quoted name cannot collide with anything.** `forms.py`'s pattern is anchored to end-of-line, so this needs its own pattern regardless — the anchor is where the trailing options go.

<p><br/></p>

⚠️ **An unknown key is REPORTED, never ignored.** A mistyped `dispay=true` would silently fall through to the default and emit a download link where a rendered code was wanted — wrong output, no signal. ⭐ **Exactly two keys are legal, so anything else is an error rather than a judgement call.**

---

## §5 — THE REPORT IS THE VERIFICATION SURFACE

Every build lists **every QR on the site**, in plain text:

```
qr · 40-forms/incident-report.md · "@form-incident-report" · print
     payload  https://mawizorek.github.io/uritp-safety/40-forms/incident-report/
     base_url https://mawizorek.github.io/uritp-safety/  (site.yml)
     recipe   segno 1.6.6 · byte · v3 · ecc Q · mask 2 · boost off · quiet 4 · 25mm

qr · 40-forms/incident-report.md · "@form-incident-report" · download
     payload  https://mawizorek.github.io/uritp-safety/40-forms/incident-report/
     file     assets/qr/8f3ab12c.png  (png, 600px)
```

⭐ **THIS IS THE FEATURE, NOT THE PAPERWORK.** It is the only way a human confirms a code before committing it to paper, it answers the determinism question in a form he can read, **and since §4d.2 it is the only way to tell a correctly hidden print-only code from one that failed to resolve.** ⚠️ **The two-line pattern produces TWO report lines for one address, and that is correct** — they are two placements. ⭐ **And since §4d.3 the download line names a real file**, which is checkable in the built site rather than only believable.

<p><br/></p>

⏳ **RULING 6 — a new report bucket, or reuse?** `urllinks.py` refused its own: *"Inventing a bucket is TWO edits in two files -- `state.reset()` and sizecheck's `_LABELS` -- and a bucket missing from `_LABELS` is printed by nothing at all."* **Recommend paying it once, for a `qr` INVENTORY bucket.** Failures still go to `dead_links`/`notes`; the inventory is a listing, and `sizecheck._INVENTORY` exists precisely so a worklist is not counted as a defect. **This is the one feature whose listing is a safety control rather than a nicety.**

<p><br/></p>

⚠️ **AND IT INTERACTS WITH A QUEUED BUILD.** **BUILD 2 Piece C moves `_LABELS` into `docrender/report.py`** — if QR ships second the bucket edit lands there, not in `sizecheck.py`. ⭐ Piece A's 10-annotation cap is unaffected: inventory buckets are deliberately not annotated, *"because annotating them trains everyone to ignore annotations."*

---

## ⏳ Rulings (five open, five closed)

1. **Bare name = `links:` only; page id needs an explicit `@`?** Recommend yes.
2. **May `@qr:` read a `forms:` slot as its last rung?** Recommend yes.
3. **NARROWED — what is the global EC constant?** Recommend **Q**, measured once. 🔴 Hawthorne owns the print legibility floor.
4. **Inline or a published file, for the RENDERED code?** Recommend inline. **Blocking print preview first.** ⚠️ The DOWNLOAD is a published file either way (§4d.3).
5. ✅ **CLOSED — the engine emits NO caption.** Author's prose.
6. **A `qr` inventory bucket?** Recommend yes, cost stated.
7. ✅ **CLOSED — placement is per-line**, via `display=` / `print=`, and nothing else may declare it.
7b. ✅ **CLOSED — no "default medium" exists.** The default is a *download link*, a third behaviour.
8. ✅ **WITHDRAWN — `ecc=` is not a line option.**
9. ✅ **CLOSED — the default link PRINTS and stays live in a PDF**, like every other link. Which retires the `data:` URI in favour of a post-build PNG (§4d.3).
10. **Is `display=false` legal to write?** Recommend yes-but-refused-when-total: an all-false directive reports and renders the dead span (§4d.2 A).
11. **(NEW) Where do the PNGs live in `site_dir`, and does anything clean them?** `assets/qr/<hash>.png` is the proposal. A stale file cannot accumulate in a rebuilt `site_dir`, but **a hashed path means an old code stays reachable by URL for anyone holding the link** — harmless, and worth deciding rather than discovering.

---

## Files and sizes (measured at HEAD 2026-08-21 — RE-MEASURE AT BUILD)

| File | Now | Change |
|---|---|---|
| **NEW** `docrender/qr.py` | — | ~9-11 KB. Resolver, two-key option parser, recipe, inline SVG, PNG collection, `on_post_build` writer, report lines. ⚠️ **Up again from §4d.3** — a post-build writer is more than a data URI was. |
| **NEW** `hooks/03e_qr.py` | — | ~150 B shim. 🔴 **LOAD-BEARING**: `urllinks.py` records that dropping its equivalent means nothing claims the namespace and every reference renders *"unknown peer site"* — correct behaviour, and a mystery to the author. |
| `requirements.txt` | 2,023 B | +1 line, `segno>=1.6,<2`. ⭐ **No Pillow** — verify segno's native PNG writer (§4d.1). |
| `mkdocs.yml` | **13,632 B** | one hook registration. ⚠️ Its own comment records a hook that has been dead exactly this way. |
| `docrender/urllinks.py` | 14,403 B | ⭐ **ideally untouched** — the registry is READ. Verify `_entry()` imports without a circular import. |
| `docrender/images.py` | 9,451 B | ⭐ **untouched** — §4 and §4d.3 both keep everything out of `images.INDEX`. |
| `docrender/instance.py` | **23,047 B** | ⭐ **UNTOUCHED** — §2 is the point, and §3b's engine-constant ruling keeps it that way. |
| `docrender/sizecheck.py` | 14,859 B | +small (ruling 6). ⚠️ Or `report.py`, if BUILD 2 lands first. |
| `docrender/state.py` | 15,918 B | +1 bucket in `reset()` (ruling 6). |
| `assets/print.css` | **16,693 B** | ⭐ **probably +1 selector only** — the QR joins the existing `print-color-adjust` list (§4b). 🔴 **No link rule** — ruling 9 needs none, and that file's dead-reference block forbids a second claimant on link decoration. |
| **NEW** `assets/print-qr.css` *or* rules in an existing print sheet | — | ⏳ ruling 4. Size floor, quiet zone, the two visibility states. 🔴 If a new sheet it **must** join `_PRINT_ASSETS` in `assets.py` — **and see the live defect below, which is that exact mistake already shipped.** |

<p><br/></p>

🔴 **THIS TABLE WILL BE WRONG WITHIN TWO DAYS. IT IS THE HOUSE SCAR.** `print-identity.md` recorded `mkdocs.yml` at 7,685 B and then at 13,632 B — a 77% drift that moved an *instruction*, not just a figure. **Measure at the moment you act; never quote this table.**

---

## Sequence

1. 🔴 **A PRINT PREVIEW FIRST, BEFORE ANY CODE.** Hand-place one inline SVG QR and one `<img>` SVG QR, print, **scan both with a phone.** ⭐ Same preview answers ruling 3 for free: same payload at Q and at H, same physical size, scan both. ⭐ **And since §4d.3, a third free question: export a PDF with a normal link in it and confirm the annotation survives** — the ruling rests on it.
2. **The resolver plus the DEFAULT download link** (`links:` names only — no `base_url`, no page ids). ⭐ The right first build: no §1 exposure, and visible on screen, so it proves the resolver before anything can hide.
3. **The report inventory** (§5). Before in-site targets, so the verification surface exists **before** the risky payload does.
4. **In-site page-id targets** (§2b), with the `base_url` refusal (§1).
5. **`display=` / `print=` and the print CSS** (§4d, §4e) — the two booleans, the all-false refusal, size floor, quiet zone, `print-color-adjust`.
6. **The `forms:` rung** (ruling 2), last — a convenience on a mechanism that must already be trustworthy.

---

## What this build is NOT

- 🚫 **Not a dynamic QR.** No redirect service, no shortener, no third party between a safety page and a reader. ⚠️ **This is also why §3b's "shorten the payload" lever means the PAGE PATH and never a short link.**
- 🚫 **Not a raw URL typed into the directive** (§2b).
- 🚫 **Not an error-correction option on the line** (§3b). One engine constant.
- 🚫 **Not an engine-emitted caption** (§4d). Author's prose.
- 🚫 **Not a themed QR.** Black on white (§4b).
- 🚫 **Not options in braces** (§4e).
- 🚫 **Not a link rule in `print.css`** (§4d.3). The default link reaches paper and PDF by the engine's existing behaviour; a second claimant on link decoration is forbidden by that file.
- 🚫 **Not a `data:` URI** (§4d.3). Dead in a PDF.
- 🚫 **Not a QR of anything but an address.** No vCards, no wifi payloads, no EPC — real segno features, each its own decision.
- 🚫 **Not a link checker.** `urllinks.py`'s limit carries over and gets worse: a code can encode a URL that 404s and will look perfect. ⚠️ **The report prints the payload so a human can catch what the build cannot.**
- 🚫 **Not `@img:` and not a change to `images.py`** (§4).
- 🚫 **Not a new instance config block** (§2).

---

## 🔴 LIVE DEFECT FOUND WHILE VERIFYING THIS SPEC — NOT THIS BUILD'S, AND IT SHOULD NOT WAIT FOR IT

**`assets/print-chrome.css` EXISTS ON DISK (9,672 B) AND IS ABSENT FROM `_PRINT_ASSETS`. IT IS THEREFORE NEVER PUBLISHED AND DOES NOTHING.** Verified at HEAD `68b192f` by a fresh read of both files.

<p><br/></p>

🔴 **`print.css`'s own header says that file holds "the chrome-off list and the corner stamp"** and that the print group *"is six files as of 2026-08-19"*. **`_PRINT_ASSETS` lists five and its own comment says "FIVE FILES, FIVE JOBS."** So the sheet that suppresses the nav drawer, the table of contents and the site header on paper — the entire reason `print.css` was written, described in its opening paragraph as *"bad in ways that are obvious the moment you look"* — **is not reaching any site.**

<p><br/></p>

⭐ **AND IT ANSWERS ANOTHER SPEC'S OPEN QUESTION.** `print-identity.md` §5 says *"THE BUILD STAMP IS PROBABLY NOT PRINTING TODAY. VERIFY FIRST"* and theorises a `display: none` ancestor problem in Material's footer. **The likely answer is far simpler: the corner stamp moved into a file that is not published.** ⚠️ Both causes could be true at once; this one is verified, that one is not.

<p><br/></p>

🔴 **IT IS THE EXACT FAILURE `assets.py` DOCUMENTS ON THE LINE ABOVE THE TUPLE:** *"`print-scheme.css` IS UNREGISTERED, a comment-only tombstone on disk. **A file in assets/ absent from these tuples is never published and does nothing.**"* One file in that folder is unregistered **on purpose** and one is unregistered **by accident**, and they are indistinguishable from the tuple. ⭐ **`hand_written_css()` compounds it: the token audit derives from the same tuples, so `print-chrome.css` is invisible to the audit too** — no rule in it has ever been checked.

<p><br/></p>

**The fix is one line in `_PRINT_ASSETS`.** 🚫 **Not done here: this spec adds no code, and a live print regression deserves its own PR rather than riding in on a QR document.** ⚠️ **Whoever registers it must then re-preview**, because publishing a 9.6 KB chrome-off sheet for the first time changes every printed page on all six sites at once — and BUILD 5's typography work is measured against the current, wrong output.

---

## ⚠️ Declared gaps in this spec

- 🔴 **SIZE, THIRD TIME, AND I AM DONE ARGUING WITH IT.** Revision 2 claimed "26 KB" while the file was 37,199 B. Revision 3 was written to CUT — per-line `ecc=`, ruling 8, the caption ladder, the three-value media table all deleted — and it **grew to 40,006 B.** ⭐ **The mechanism is now clear and it is not carelessness: every ruling Michael closes is replaced by the ARGUMENT for closing it, and the argument is always longer than the question was.** `assets.py`: *"a file at its size limit is usually a file with a seam in it; trimming prose is what you do instead of finding the seam."* **Trimming has been tried twice and failed twice.** 🔴 **The seam is §3 + §3a + §3b — a self-contained determinism contract, roughly a third of the bytes, referenced by the rest but not depended on line-by-line. It becomes `specs/qr-determinism.md` on the NEXT revision unless Michael says otherwise**; asked twice, answered with design both times, so the default is inverted rather than asked a third time. ⚠️ **Read the real number off the commit, never off this bullet.**
- ✅ **RESOLVED: `print.css` HAS NO LINK POLICY.** The previous revision declared this an unread gap on which ruling 9 depended. It is read now, and the answer is better than expected: **there is no link rule in that file at all**, and its dead-reference block is a deliberate argument for *not writing one*, because `base.css` declares link decoration unscoped to any medium and it reaches paper on its own — **confirmed on paper 2026-08-19.** ⚠️ Minor rot found in passing: `assets.py`'s five-job table credits `print.css` with *"link policy"* and `print-type.css` with *"link decoration"*; **`print.css` contains neither.** Reported, not fixed.
- **NOTHING HERE HAS BEEN TESTED AGAINST A SCANNER, A PRINTER, A PDF EXPORT OR A BROWSER.** Every claim about scannability is a reading of the standard and of segno's docs. ⚠️ That includes §3b's central claim (H can scan worse than Q at fixed size — the mechanism is arithmetic and not in doubt, the crossover point is unknown) and **all three §4d.3 claims: that a `data:` URI dies in a PDF, that a normal link survives one, and that `on_post_build` can write an arbitrary path into `site_dir`.** 🔴 The last is strongly implied by `docindex.py` writing `doc-index.json`, **but its write mechanism was not read.**
- **THREE THINGS TO VERIFY IN SEGNO'S PINNED VERSION**, all read from documentation rather than source: `boost_error`'s default (§3's whole argument rests on turning it off explicitly), the default `error=` value, and **whether the native PNG writer needs no third-party imaging dependency** (§4d.1 — if it does, `requirements.txt` grows and the transitive-surface argument weakens).
- **`docrender/links.py` (16,596 B) was NOT read whole this session.** The resolution order is quoted from `prefixes.py`'s docstring, authoritative about the contract but not the implementation. **Read `links.py` before writing the resolver.**
- **`specs/print-identity.md` (BUILD 5) IS PARTLY STALE.** It lists `print-flow.css` and `print-type.css` as NEW, but `_PRINT_ASSETS` registers five print sheets and **`print.css`'s header describes six.** The split shipped with a different seam than specced — `print-space.css`, `print-callout.css` and `print-chrome.css` exist and none was in the plan; the specced `print-identity.css` does not, so the letterhead never landed. 🔴 **Read `assets.py` AND the sheet headers for what exists — and note they disagree with each other, which is the live defect above.**
