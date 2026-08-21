# BUILD 6 — STATIC QR CODES, resolved through the `links:` registry

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-21, out of the URITP Safety incident-report print session. Indexed from [`next-build-spec.md`](../next-build-spec.md). Decision history: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

> Michael, 2026-08-21, the use case: *"i wnat to qr code out to the incident report fowm, in case i print the page and hsare it - that way peopoel can pull up the form on their phone."*
>
> On placement, which decided the whole shape: *"i like the making it a part of exisitng links: organization"*
>
> On determinism, the actual engineering requirement: *"they have to be STATIC qr codes - like if a different engienr we asked to amek the same code, they would make the smae image - type htign?"*
>
> ✅ **The grammar ruling, which closed four open questions and shrank the build:** *"i don't want to be declaring error level in my line. we will set it glboally for all builds in all renderer apps... display = and print = are both optional and the only thing that declares where those qr codes appear."*

---

## One line

A build-time QR code, **generated from a NAME in the existing `links:` registry** (or from a page `id:`), placed by **two optional boolean options** on the directive line, defaulting to a **PNG download link** when neither is given — with the payload and encoder recipe printed in the build report so a human can verify a code **before** it goes to print.

---

## §0 — WHY PAPER CHANGES EVERY DECISION IN THIS FILE

The use case is not "a QR on a web page." A reader on the page can already tap the embedded form. **The QR exists for the moment the page stops being a page** — printed, handed out, pinned in a shop.

<p><br/></p>

🔴 **THAT INVERTS THE USUAL COST OF BEING WRONG.** Every other reference in this engine is wrong *recoverably*: a dead `@id` renders a struck-through span, somebody sees it, the next publish fixes it. **A wrong QR renders as a perfect, confident, beautiful square** — and by the time anybody discovers it, it is on forty sheets of paper in a scene shop. There is no next publish for paper.

<p><br/></p>

⭐ **SO THE DESIGN PRIORITY IS VERIFIABILITY BEFORE PRINT, NOT ELEGANCE.** Every rule below that looks over-cautious is paying for that one property. `urllinks.py` already states the general form of this limit — an external URL is not verifiable at build time — and a QR takes that unverifiable thing and makes it **unreadable by a human as well.** Nobody proofreads a QR.

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

## ⭐ §2 — THE `links:` FOLD-IN IS THE RIGHT ANSWER, AND ALSO THE ONLY CHEAP ONE

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
!!! qr "incident_form"          a declared external address
!!! qr "@form-incident-report"  a page in THIS site, by id
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

⭐ **BUT THE BETTER ANSWER FOR THIS PAGE IS NEITHER: point the QR at the PAGE.** A scanner then lands on the 48-hour rule, the near-miss definition, and the form embedded and open (`collapsed: false`) — instead of a naked form with no instructions. It also survives ClickUp reissuing the form URL, because the address stays in exactly one place. **Recommend `@form-incident-report` as the payload for the founding use case**, with the raw-URL path available for genuinely external targets (OSHA, a vendor manual).

---

## 🔴 §3 — DETERMINISM IS REAL BUT IT IS NOT AUTOMATIC

Michael's question — *would a different engineer make the same image* — has a precise answer: **yes, if and only if six things are pinned.** Leave any on a library default and two conformant encoders diverge.

<p><br/></p>

| # | Pinned | Why it moves the matrix |
|---|---|---|
| **1** | the **payload bytes**, exactly | one trailing slash is a different symbol |
| **2** | the **encoding mode** — **byte, always** | alphanumeric is denser but **uppercase-only**, and a URL path is case-sensitive, so a URL can never legally take it. Pinned so an all-caps payload cannot silently switch modes and change the matrix. |
| **3** | the **version** (module count) | derived from payload + EC; deterministic once 1 and 4 are fixed, but it must be RECORDED |
| **4** | the **error-correction level** | ✅ **now an ENGINE CONSTANT** — §3b |
| **5** | the **mask** | ISO/IEC 18004 selects it by lowest penalty score, so it is deterministic **for an encoder that implements the standard scoring** — an assumption about the library, not a property of the spec |
| **6** | the **serialization** | fixed scale, fixed quiet zone, no XML declaration, no metadata, no varying attribute order — or identical matrices produce different bytes and churn every build |

<p><br/></p>

🔴 **THE BOOST TRAP, AND IT IS THE ONE THAT WOULD ACTUALLY BITE US.** `segno` raises the error-correction level automatically when the chosen version has spare capacity. So *the same payload at the same declared EC level can yield a different EC level, therefore a different matrix,* purely because the payload changed by one character. **`boost_error` must be explicitly OFF**, and that is not the default.

<p><br/></p>

⭐ **THE COST OF SWITCHING IT OFF IS REAL, SO IT IS STATED HERE RATHER THAN DISCOVERED BY WHOEVER "OPTIMISES" IT BACK ON.** With boost off we **deliberately leave spare capacity unused.** That is the price of reproducibility and it is the right trade: a code whose recovery level silently improves is a code whose matrix silently changed, and a matrix that changes on its own is the one thing §0 says we cannot have.

<p><br/></p>

⚠️ **"ANY GENERATOR PRODUCES THE SAME CODE" IS A CLAIM THE EVIDENCE DOES NOT SUPPORT.** Segno's own library comparison records that the widely-used `qrcode` package **does not reproduce the reference symbol printed in ISO/IEC 18004:2015 Fig. 1**. Interoperability of *scanning* is guaranteed by the standard; **byte-identical generation is not.** Reproducibility here is a property we construct and record, never one we inherit. ⭐ **Therefore the recipe is part of the artifact**, and the report records encoder name and version (§5) — a reproducibility claim against an unnamed encoder is not a claim.

<p><br/></p>

⭐ **AND MICHAEL'S TWO-LINE EXAMPLE IS THE PROOF THIS WORK PAYS FOR ITSELF.** `display=true` on one line and a bare directive on the next means **the same payload is encoded twice on one page.** Under a pinned recipe those two matrices are necessarily identical; under library defaults with boost on they could differ, on the same page, in the same build. **The determinism pin is what makes his own syntax safe.**

### §3a — the dependency

`requirements.txt` is the file whose own header records that *"an unpinned transitive dependency is an unpinned build"* after MkDocs 2.0 broke a live publish. **Pin narrowly:** `segno>=1.6,<2`. Pure Python, zero dependencies, BSD — no transitive surface, which is the only reason a new dependency is defensible in a file that argues this hard about them.

<p><br/></p>

⚠️ **A MAJOR BUMP MAY LEGALLY CHANGE OUR OUTPUT** (serialization defaults, mask tie-breaking). Not a bug in segno; it is why the upper bound exists and why the version is recorded per code.

### ✅ §3b — ERROR CORRECTION IS ONE GLOBAL CONSTANT (RULINGS 3 AND 8 CLOSED)

> Michael, 2026-08-21: *"i don't want to be declaring error level in my line. we will set it glboally for all builds in all renderer apps. let's not overthink it here."*

✅ **`ecc=` IS NOT A DIRECTIVE OPTION. It is a constant in `docrender/qr.py`** — not `site.yml`, not instance config, because *"all renderer apps"* means the engine rather than a site. **Ruling 8 (per-line override) is withdrawn entirely: there is nothing to override.**

<p><br/></p>

⭐ **AND THE GLOBAL IS SAFER THAN IT SOUNDS, WHICH IS WHY HIS INSTINCT TO NOT OVERTHINK IT IS CORRECT: CHANGING IT NEVER INVALIDATES PRINTED PAPER.** The payload is unchanged by an EC change, so **every code already on a wall keeps scanning** — only newly generated codes differ. This is the one decision in the whole build that is freely reversible after print, and it is the one he took off the per-line surface. 🔴 **The reverse of §1**, and worth holding side by side: `base_url` is unforgiving after print, EC is not.

<p><br/></p>

**For the record, since it was asked — ISO/IEC 18004 defines exactly four levels and there are no others:**

<p><br/></p>

| Level | Recovers | For |
|---|---|---|
| **L** | ~7% | screen-only, pristine conditions. 🚫 Not for paper. |
| **M** | ~15% | the de facto default in most libraries and web generators |
| **Q** | ~25% | print that gets handled — the safety case |
| **H** | ~30% | print that gets abused, or a logo overlaid on the code |

<p><br/></p>

🔴 **THE ONE NON-OBVIOUS FACT, AND THE ONLY REASON THIS NEEDS A MEASUREMENT RATHER THAN A PREFERENCE: EC IS NOT MONOTONIC AT A FIXED PHYSICAL SIZE.** Correction is stored as extra codewords, extra codewords need a bigger symbol, and a bigger symbol at the same printed size means **each module is physically smaller** — and module size is what a phone camera has to resolve. **So `H` in a 25 mm square can scan WORSE than `Q` in the same square.** The instinct that more correction is safer is wrong in exactly the case we care about.

<p><br/></p>

⏳ **RULING 3 (NARROWED) — what is the constant?** Recommend **Q**, measured once at §6 step 1 and then left alone. 🔴 **`specs/print-identity.md` §3f already put the legibility floor for safety-critical print in Hazard Hawthorne's lane, not the engine's. Same ruling, same owner.** ⭐ One free lever if the measurement is tight: **byte-mode capacity falls off as EC rises, so a shorter PAGE PATH buys a higher level at the same module count.** Not via a shortener — this build is static by definition.

---

## 🔴 §4 — INLINE, NOT A PUBLISHED FILE, AND THE REVERSAL THAT GOT THERE

The first instinct was a generated `.svg` published through `assets.py` and referenced with the bang-image form, reusing `images.py`. **Three findings killed it.**

<p><br/></p>

🔴 **1. THE STRAY BANG.** `images.py` works because its resolver returns **link markdown** — `[alt](url)` — and `links._LINK` starts matching at the opening bracket, so the `!` in `![alt](@img:x)` sits outside the match and survives to form an image. **A resolver that returns raw `<svg>` leaves the `!` behind as a literal exclamation mark on the page.**

<p><br/></p>

🔴 **2. `on_files` RUNS BEFORE ANY PAGE BODY IS READ, AND THE QR LIVES IN THE BODY.** A generated file must be appended at `on_files`; a `!!! qr` directive is discovered at `on_page_markdown`, much later. `assets.py` has already ruled on this exact shape for `!!! data`: *"a `!!! data` block lives in the BODY of a page, not in the first 2000 bytes a frontmatter scan reads, so the router's trick does not transfer."* **A file-based QR needs either a body scan or a second frontmatter declaration listing which codes to build — i.e. declaring every QR twice.**

<p><br/></p>

🔴 **3. IT WOULD ENTER `images.INDEX` AND COULD COLLIDE.** `images.on_files` (01f) indexes every image in the file set by lowercased filename stem and **refuses duplicates**, on the rule that *"two pictures with one name are two different pictures."* A generated `qr-incident-form.svg` colliding with a real image stem breaks **both** references — survivable only through a hook-ordering dependency nobody would know they had. `visibility.py` had to ship a literal stage-order regression detector for exactly this class of silent break.

<p><br/></p>

⭐ **INLINE DISSOLVES ALL THREE AT ONCE.** No file, so no `on_files`, no double declaration, no index entry, no ordering law. `prefixes.py` already permits it: a resolver returns *"a replacement markdown/HTML string."*

<p><br/></p>

⭐ **AND INLINE SVG IS THE SAFER FORMAT ON PAPER, WHICH IS THE WHOLE USE CASE.** `print-identity.md` §4d warns that browsers *"can flatten images at print"* — that a logo can print as an empty box — and explicitly **refuses to assert SVG print behaviour from a read.** An inline SVG's modules are **filled vector paths in the document's own box tree**, not an external resource a print pipeline can drop.

<p><br/></p>

**What inline costs, stated rather than discovered:** page weight (per-page, not cached), no dedup across pages, and **no fingerprinted URL** — `assets.py`'s content fingerprint would have made byte-identical output visible as eight hex characters in a diff. **§5 replaces it with something better for this feature: the report prints the payload as READABLE TEXT.** A hash proves two builds agree; the text proves the code is *correct*.

<p><br/></p>

⏳ **RULING 4 — inline or file?** Recommend **inline for v1.** If a print preview later shows inline SVG failing where an `<img>` succeeds, the file path is a rebuild rather than a patch — so **§6 step 1 is blocking, not confirmatory.**

### §4a — the directive shape

**`!!! qr "name"`, block-level, on the `!!! form` precedent** in `docrender/forms.py` — the same *page NAMES a thing, engine BUILDS the element* split, and deliberately the same body vocabulary rather than a third spelling. It dodges the stray bang entirely.

### 🔴 §4b — PHYSICAL SIZE AND THE QUIET ZONE ARE FUNCTIONAL, NOT STYLING

- **The quiet zone is 4 modules and it is part of the symbol.** Crop it with CSS and the code stops scanning. It must live *inside* the SVG viewBox, where no stylesheet can reach it.
- **A minimum size in `mm`, not `px`.** `print-identity.md` §4d already established this is the one place a physical unit is correct rather than trapped: *"the sheet is a physical object and `px` at print resolution is a fiction."* 🔴 **Not `em`** — §3b of that spec is the whole finding.
- 🔴 **`print-color-adjust: exact`, MANDATORY.** A code printed with adjusted contrast is a code that does not scan. `print.css` already applies this narrowly to elements *whose meaning is carried by a colour*, and a QR is the purest example in the engine.
- 🚫 **NO THEME COLOURS. Black on white, always.** Scanners need luminance contrast, `database` is an unproven theme on this very site, and a paper palette correction lives inside generated `tokens.css`. **A themed QR is a dead control that looks like a feature.**

### ⚠️ §4c — IT CONSUMES SHEET-ONE SPACE, WHICH TWO OTHER BUILDS ARE ALSO SPENDING

`print-identity.md` §3g: re-typesetting *"invalidates every manual break, immediately"*, and the letterhead *"consumes vertical space at the top of sheet one, so it moves every break on a one-sheet document too."* **A QR block does the same.** BUILD 5's leading change, BUILD 5's letterhead and this code are three claimants on the same sheet. **Whichever lands last re-previews the others.**

### ✅ §4d — THE GRAMMAR: TWO BOOLEANS, AND A DEFAULT THAT IS A DOWNLOAD (RULINGS 5, 7 AND 7b CLOSED)

> Michael, 2026-08-21: *"display = and print = are both optional **and the only thing that declares where those qr codes appear**... if either is provided, then nothing besides the rectangle prints, and any headers or footers would be defined inline with the markdown text or in frontmatter."*

<p><br/></p>

| Written | Renders |
|---|---|
| `!!! qr "@x"` | **a download link**, text *"QR Code"*, delivering a PNG. Nothing else. |
| `!!! qr "@x" display=true` | the code on screen. **No download link.** |
| `!!! qr "@x" print=true` | the code on paper. **No download link.** |
| `!!! qr "@x" display=true print=true` | the code in both media. **No download link.** |

<p><br/></p>

**Two lines give both behaviours**, which is Michael's own example and needs no new syntax:

```
!!! qr "@form-incident-report" display=true
!!! qr "@form-incident-report"
```

<p><br/></p>

⭐ **THE ORGANISING LINE: AN ADDRESS BELONGS TO THE REGISTRY; A PLACEMENT BELONGS TO THE LINE.** `links:` answers *where does this point* — one address of record, one edit fixes every page. The directive answers *where does this instance appear.* 🔴 **And "the only thing that declares where those qr codes appear" is a HARD RULE with teeth: no site.yml default, no frontmatter placement key, no theme opinion.** One surface decides placement, and a second surface that could override it is the drift this repo has retired three manifests over.

<p><br/></p>

✅ **RULING 5 (caption) IS CLOSED BY THE SAME SENTENCE: THE ENGINE EMITS NO CAPTION, EVER.** *"Nothing besides the rectangle"* — headers and footers are the author's prose, written above and below the directive. **That is strictly better than the label ladder I recommended**, because a caption is content and this engine's founding rule is that content belongs to the content repo. It also deletes the `figure.py` problem rather than solving it: there is nothing to wrap.

<p><br/></p>

⚠️ **BUT A BARE RECTANGLE NEEDS AN ACCESSIBLE NAME, AND THAT IS NOT A CAPTION.** A QR with no visible text and no `<title>` in its SVG is silence to a screen reader — and on a safety page that is a compliance surface, not a nicety. **Recommend an SVG `<title>` carrying the resolved payload**, invisible on screen and on paper, so the accessible name is the destination itself. 🚫 **Not visible text** — that would be the caption Michael just ruled out.

#### 🔴 §4d.1 — THE DEFAULT REOPENS §4's FILE PROBLEM, AND `data:` CLOSES IT AGAIN

**A download needs something to download.** §4 killed generated files for three reasons, and *"downloads the qr code as png"* walks straight back into all of them — a published `.png` needs `on_files`, which runs before any body is read.

<p><br/></p>

⭐ **THE RESOLUTION IS A `data:` URI PLUS THE `download` ATTRIBUTE:**

```
<a href="data:image/png;base64,…" download="qr-form-incident-report.png">QR Code</a>
```

**No file, so no `on_files`, no `images.INDEX` entry, no ordering law — §4's three findings stay dissolved, and the download still hands over a real PNG.** ⚠️ **Verify the `download` attribute against a `data:` URI in a real browser before building**; it is standard behaviour but this repo does not assert runtime behaviour from a read, and a download link that opens the image instead of saving it is a broken control that looks fine.

<p><br/></p>

⭐ **AND PNG IS THE RIGHT FORMAT FOR THE DOWNLOAD SPECIFICALLY, WHICH IS WORTH SAYING BECAUSE IT CONTRADICTS §4's SVG PREFERENCE ON PURPOSE.** §4 chose SVG for the *rendered* code because vector survives print. A *download* is destined for somewhere else entirely — a poster, a slide, an email, a call-board — and consumer tools handle PNG reliably and SVG badly. **Two different jobs, two correct answers.** 🔴 Also: `segno` writes PNG with no third-party imaging dependency, which is the only reason this does not drag Pillow into `requirements.txt`. ⚠️ **Verify that in the pinned version.**

<p><br/></p>

⚠️ **PNG DETERMINISM IS A SEPARATE PROBLEM FROM §3's, AND IT IS SMALLER.** A PNG carries compression settings and optional metadata chunks, so two runs can differ in bytes while encoding an identical matrix. **It matters less here because the data URI is regenerated every build and never committed** — nothing diffs it. 🔴 **But the pinned scale must be recorded**, because a downloaded PNG's pixel size is what determines whether it is usable at poster scale, and that is the one property a person notices.

#### 🔴 §4d.2 — TWO HOLES IN THE GRAMMAR, BOTH SILENT, BOTH CHEAP TO CLOSE

**A. `display=false` / `print=false` renders NOTHING AT ALL.** The rule is *"if either is provided"* — so `!!! qr "@x" print=false` is provided, which suppresses the download link, and then declines to print. **Result: a declared QR that appears in no medium and reports nothing.** 🚫 **Refuse it loudly**: an explicit `false` is legal to write (it reads naturally and somebody will), but **a directive whose every declared medium is false is reported to `missing_required` and renders the dead span.** A no-op that looks like a declaration is the defect `mkdocs.yml`'s own comment records a dead hook for.

<p><br/></p>

**B. A `print=true`-only code is INVISIBLE TO ITS OWN AUTHOR.** On screen, *"failed to resolve"* and *"resolved and correctly hidden"* are **the same blank space.** This engine kills invisible controls on sight, so the mitigation is mandatory: **the §5 report line states the media flags for every code**, and it is the only surface that can tell those two states apart. ⚠️ **Verification for a print-only code is print preview or the report — never the rendered page.** ⭐ **The default case is exempt and that is a real virtue of Michael's design**: a bare directive renders a visible link on screen, so the commonest usage is self-evidencing.

<p><br/></p>

⏳ **RULING 9 (NEW) — does the DEFAULT download link print?** On paper, the words *"QR Code"* as a hyperlink are **dead text**: nothing to tap, nothing to scan, no URL shown. **Recommend `display: none` in `@media print` for the default link only**, so a printed sheet shows nothing rather than an instruction it cannot honour. ⚠️ **Check `print.css`'s existing link policy first** — it already has an opinion about how links print, and this must not become a second one.

### 🔴 §4e — THE OPTIONS ARE BARE `key=value`, NOT BRACES, AND THAT IS A DELIBERATE REFUSAL

The obvious spelling is the attr_list-style block this engine already uses for captions: `{ display=true }`. 🚫 **Refused, for three reasons already written down in this repo.**

<p><br/></p>

1. **Braces are CONTESTED TERRITORY and two of our own modules already disagree about them.** `markers.on_page_markdown` checks `_TABLE` and deliberately hands back an unrecognised brace block untouched, *"rather than eating syntax that belongs to somebody else."* `cells.plain()` opens with `re.sub(r"\{[^}\n]*\}", "", text)` and strips **every** brace block. **BUILD 1's spec names that disagreement as a live defect.**
2. 🔴 **BUILD 1's `clean.py` WOULD EAT THEM.** Its job is to strip *our declared vocabulary* and leave foreign attr_list alone — and a brace block that is genuinely ours is exactly what it removes. **A QR option in braces is a QR option a future stripper deletes.**
3. **Bare `key=value` after the quoted name cannot collide with anything.** `forms.py`'s pattern is anchored to end-of-line (`[ \t]*$`), so this needs its own pattern regardless — the anchor is where the trailing options go.

<p><br/></p>

⚠️ **An unknown key is REPORTED, never ignored.** A mistyped `dispay=true` would silently fall through to the default and emit a download link where a rendered code was wanted — wrong output, no signal. ⭐ **And the two-key vocabulary makes this cheap to enforce:** exactly two keys are legal, so anything else is an error rather than a judgement call.

---

## §5 — THE REPORT IS THE VERIFICATION SURFACE

Every build lists **every QR on the site**, in plain text:

```
qr · 40-forms/incident-report.md · "@form-incident-report" · print
     payload  https://mawizorek.github.io/uritp-safety/40-forms/incident-report/
     base_url https://mawizorek.github.io/uritp-safety/  (site.yml)
     recipe   segno 1.6.6 · byte · v3 · ecc Q · mask 2 · boost off · quiet 4 · 25mm

qr · 40-forms/incident-report.md · "@form-incident-report" · download (png, 600px)
     payload  https://mawizorek.github.io/uritp-safety/40-forms/incident-report/
```

⭐ **THIS IS THE FEATURE, NOT THE PAPERWORK.** It is the only way a human confirms a code before committing it to paper, it answers Michael's determinism question in a form he can read, **and since §4d.2 it is the only way to tell a correctly hidden print-only code from one that failed to resolve.** ⚠️ **Michael's two-line pattern produces TWO report lines for one address, and that is correct** — they are two placements, and a reader checking a printed sheet needs to know which one they are looking at.

<p><br/></p>

⏳ **RULING 6 — a new report bucket, or reuse?** `urllinks.py` explicitly refused its own bucket: *"Inventing a bucket is TWO edits in two files -- `state.reset()` and sizecheck's `_LABELS` -- and a bucket missing from `_LABELS` is printed by nothing at all."* **Recommend paying it anyway, once, for a `qr` INVENTORY bucket.** Failures still go to `dead_links`/`notes`; the inventory is a listing, and `sizecheck._INVENTORY` exists precisely so a worklist is not counted as a defect. **This is the one feature whose listing is a safety control rather than a nicety.**

<p><br/></p>

⚠️ **AND IT INTERACTS WITH A QUEUED BUILD.** **BUILD 2 Piece C moves `_LABELS` into a new `docrender/report.py`** — so if QR ships second the bucket edit lands there, not in `sizecheck.py`. ⭐ **Piece A's 10-annotations-per-step cap is NOT affected**: inventory buckets are deliberately not annotated, *"because annotating them trains everyone to ignore annotations."*

---

## ⏳ Rulings (five open, four closed)

1. **Bare name = `links:` only; page id needs an explicit `@`?** Recommend yes.
2. **May `@qr:` read a `forms:` slot as its last rung?** Recommend yes.
3. **NARROWED — what is the global EC constant?** Recommend **Q**, measured once. 🔴 Hawthorne owns the print legibility floor.
4. **Inline or a published file?** Recommend inline. **Blocking print preview first.**
5. ✅ **CLOSED — the engine emits NO caption.** Author's prose, above and below. §4d.
6. **A `qr` inventory bucket?** Recommend yes, cost stated.
7. ✅ **CLOSED — placement is per-line**, via `display=` / `print=`, and nothing else may declare it. §4d.
7b. ✅ **CLOSED — there is no "default medium" any more.** The default is a *download link*, which is a third behaviour rather than a medium. §4d.
8. ✅ **WITHDRAWN — `ecc=` is not a line option**, so there is nothing to override. §3b.
9. **Does the default download link print?** Recommend hidden in `@media print`. ⚠️ Check `print.css`'s existing link policy first (§4d.2).
10. **(NEW) Is `display=false` legal to write?** Recommend yes-but-refused-when-total: an all-false directive reports and renders the dead span (§4d.2 A).

---

## Files and sizes (measured at HEAD 2026-08-21 — RE-MEASURE AT BUILD)

| File | Now | Change |
|---|---|---|
| **NEW** `docrender/qr.py` | — | ~8-10 KB. Resolver, two-key option parser, recipe, SVG emit, PNG data URI, report lines. |
| **NEW** `hooks/03e_qr.py` | — | ~150 B shim. 🔴 **LOAD-BEARING**: `urllinks.py` records that dropping its equivalent means nothing claims the namespace and every reference renders *"unknown peer site"* — correct behaviour, and a mystery to the author. |
| `requirements.txt` | 2,023 B | +1 line, `segno>=1.6,<2`. ⭐ **No Pillow** — verify segno's native PNG writer in the pinned version (§4d.1). |
| `mkdocs.yml` | **13,632 B** | one hook registration. ⚠️ Its own comment records a hook that has been dead exactly this way. |
| `docrender/urllinks.py` | 14,403 B | ⭐ **ideally untouched** — the `links:` registry is READ, not modified. Verify `_entry()` imports without a circular import. |
| `docrender/images.py` | 9,451 B | ⭐ **untouched, and §4 is why.** Nothing generated enters `images.INDEX`. |
| `docrender/instance.py` | **23,047 B** | ⭐ **UNTOUCHED — §2 is the whole point**, and §3b's global-constant ruling keeps it that way: an engine constant is not instance config. |
| `docrender/sizecheck.py` | 14,859 B | +small (ruling 6). ⚠️ Or `report.py`, if BUILD 2 lands first. |
| `docrender/state.py` | 15,918 B | +1 bucket in `reset()` (ruling 6). |
| **NEW** `assets/print-qr.css` *or* rules in an existing print sheet | — | ⏳ rulings 4 and 9. **Three states now: screen-visible, print-visible, and the default link hidden on paper.** 🔴 If a new sheet, it **must** join `_PRINT_ASSETS` in `assets.py`; `hand_written_css()` then picks it up for the token audit automatically. 🪦 `print-scheme.css` is the tombstone proving *"a file in assets/ absent from these tuples is never published and does nothing."* |

<p><br/></p>

🔴 **THIS TABLE WILL BE WRONG WITHIN TWO DAYS. IT IS THE HOUSE SCAR.** `print-identity.md` recorded `mkdocs.yml` at 7,685 B and then at 13,632 B — a 77% drift that moved an *instruction*, not just a figure. **Measure at the moment you act; never quote this table.**

---

## Sequence

1. 🔴 **A PRINT PREVIEW FIRST, BEFORE ANY CODE.** Hand-place one inline SVG QR and one `<img>` SVG QR on a printed sheet and **scan both with a phone.** Ruling 4 rests on it, and `print-identity.md` §4d refuses to assert SVG print behaviour from a read. ⭐ **Same preview answers ruling 3 for free: print the same payload at Q and at H, same physical size, scan both.**
2. **The resolver plus the DEFAULT download link** (`links:` names only — no `base_url`, no page ids). ⭐ **The default is the right first build**: it is the half with no §1 exposure AND the half that is visible on screen, so it proves the resolver before anything can hide.
3. **The report inventory** (§5). Before in-site targets, so the verification surface exists **before** the risky payload does, and before anything can render invisibly.
4. **In-site page-id targets** (§2b), with the `base_url` refusal (§1).
5. **`display=` / `print=` and the print CSS** (§4d, §4e) — the two booleans, the all-false refusal, size floor, quiet zone, `print-color-adjust`, ruling 9.
6. **The `forms:` rung** (ruling 2), last, because it is a convenience on a mechanism that must already be trustworthy.

---

## What this build is NOT

- 🚫 **Not a dynamic QR.** No redirect service, no shortener, no third party between a safety page and a reader. The payload is baked into the modules. A code telling somebody how to report an injury must not depend on a vendor's uptime. ⚠️ **This is also why §3b's "shorten the payload" lever means the PAGE PATH and never a short link.**
- 🚫 **Not a raw URL typed into the directive.** The address lives in `links:`, once (§2b).
- 🚫 **Not an error-correction option on the line** (§3b). One engine constant.
- 🚫 **Not an engine-emitted caption** (§4d). Author's prose.
- 🚫 **Not a themed QR.** Black on white (§4b).
- 🚫 **Not options in braces** (§4e).
- 🚫 **Not a published image file** (§4, §4d.1). Inline SVG, or a `data:` PNG for the download.
- 🚫 **Not a QR of anything but an address.** No vCards, no wifi payloads, no EPC. Real segno features, each its own decision.
- 🚫 **Not a link checker.** `urllinks.py`'s limit carries over and gets worse: a code can encode a URL that 404s and will look perfect. ⚠️ **The report prints the payload so a human can catch what the build cannot.**
- 🚫 **Not `@img:` and not a change to `images.py`** (§4).
- 🚫 **Not a new instance config block** (§2).

---

## ⚠️ Declared gaps in this spec

- 🔴 **THE PREVIOUS REVISION OF THIS BULLET SAID "THIS FILE AT 26 KB" AND REASONED FROM THAT NUMBER. THE FILE WAS 37,199 B WHEN IT SAID SO.** A size claim wrong on arrival, in the bullet whose subject is size — `super-agent-base.md` records three prior passes shipping exactly this defect and `print-identity.md` calls it the house scar. **The lesson is the one already written everywhere here: MEASURE FROM THE WRITE RESPONSE, never from the draft in front of you.** This revision cut §3b's per-line machinery, ruling 8, the caption ladder and the three-value media table; **whatever the resulting number is, read it off the commit rather than this sentence.**
- **THE ~22 KB CEILING AND WHY THIS FILE IS NOT SPLIT YET.** The ceiling's justification is *"a file that cannot be read whole cannot be safely edited"*, which is empirical — and `print-identity.md` at 32,260 B **provably came back whole** through the git blob path on 2026-08-21, so the figure (derived from base64 inflating against a ~30 KB return cap) is not binding for markdown read that way. ⭐ **The seam is pre-identified: §3 is a determinism contract, separable as `specs/qr-determinism.md`.** Michael was asked twice and answered with design instead, which reads as *not yet*. **Split follows the concerns, not the bytes** — but if a read of this file ever comes back clipped, §3 is the cut.
- **NOTHING HERE HAS BEEN TESTED AGAINST A SCANNER, A PRINTER, OR A BROWSER.** Every claim about scannability is a reading of the standard and of segno's docs. ⚠️ That includes §3b's central claim (H can scan worse than Q at fixed size — the mechanism is arithmetic and not in doubt, the crossover point is unknown) and §4d.1's `download`-on-`data:`-URI behaviour.
- **THREE THINGS TO VERIFY IN SEGNO'S PINNED VERSION BEFORE WRITING THE RECIPE**, all read from documentation rather than source: `boost_error`'s default (§3's whole argument rests on turning it off explicitly), the default `error=` value, and **whether the native PNG writer needs no third-party imaging dependency** (§4d.1 — if it does, `requirements.txt` grows and the transitive-surface argument weakens).
- **`docrender/links.py` (16,596 B) was NOT read whole this session.** The resolution order is quoted from `prefixes.py`'s docstring, authoritative about the contract but not the implementation. **Read `links.py` before writing the resolver.**
- **`print.css`'s LINK POLICY WAS NOT READ.** Ruling 9 depends on it and `print-identity.md` names it as an existing concern of that sheet. **Read it before deciding how the default link behaves on paper.**
- **`specs/print-identity.md` (BUILD 5) IS PARTLY STALE, AND IT MATTERS HERE.** It lists `print-flow.css` and `print-type.css` as NEW, but `assets.py`'s `_PRINT_ASSETS` at HEAD registers **five** print sheets (`print.css`, `print-flow.css`, `print-type.css`, `print-space.css`, `print-callout.css`). **The split shipped with a different seam than specced** — `print-space.css` and `print-callout.css` exist; the specced `print-identity.css` does **not**, so the letterhead never landed. Read `assets.py` for what exists, never that spec's file table. **Reported, not fixed: another build's document.**
