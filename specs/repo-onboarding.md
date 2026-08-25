# BUILD — onboarding a new content repo without minting a credential

⚠️ **SCOPED, NOT GREENLIT.** 2026-08-25. Scoped by Dev Dexter, convened by Maestro Mira.

🔴 **DELIBERATELY UNNUMBERED, AND THAT IS A FINDING RATHER THAN A STYLE CHOICE.** `specs/` holds SIX files and the index in `next-build-spec.md` knows about FOUR. The two it does not know about **both re-used a number that a later spec then re-used again**: `visibility-split.md` is `BUILD 4` (2026-08-07) and so is `draft-watermark.md` (2026-08-16); `chrome.md` is `BUILD 5` (2026-08-18) and so is `print-identity.md` (2026-08-19). **Taking a number here would be the third collision, not the first.** See §11.

> Michael, 2026-08-25 08:57 ET: *"I wish it was easier for us to stand up new doc repos. I want to be able to create a new private repo for my courses or a new private doc renderer for a specific production without having to add a new key or set up a new license every time. I wish it were easier for a repo to be accessible to the doc renderer. What would that take?"*

One sentence: **make a new content repo reachable by the renderer without editing a secret, and state honestly which parts of "private" this engine can and cannot deliver.**

Decision history: the **doc-render-engine (repo) — Decision Log** subpage in ClickUp.

---

## §0 🔴 THE ASK NAMES TWO PER-REPO COSTS. ONE IS REAL. THE OTHER DOES NOT EXIST.

**"A new key" is real.** `DOCRENDER_TOKEN` is a fine-grained PAT scoped to an explicit repository list, and nothing is ever added to that list automatically. This file's siblings have paid for it four separate times — §1.

🚫 **"A new license every time" is NOT real, and believing it is has been shaping decisions.** GitHub Pages on a private repository requires a paid plan, and the plan is a property of the **ACCOUNT**, not of the repository. GitHub's own docs: *"If the account that owns the repository uses GitHub Free or GitHub Free for organizations, the repository must be public."* ([creating-a-github-pages-site](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site), [GitHub's plans](https://docs.github.com/en/get-started/learning-about-github/githubs-plans))

⭐ **AND WE HAVE LIVE PROOF THE PLAN IS ALREADY PAID.** `uritp-docs` went private on 2026-08-04 and its Pages site kept serving. That could not happen on Free. **So every future private repo under `mawizorek` is already covered, and there is no per-repo license step to remove.** The cost that felt like a licence is the *one-time Pages click* — `build.yml`'s own summary says so: *"The first run CREATES the branch; the setting is a one-time click after."*

⚑ **Worth recording as a class, not an anecdote: a cost that recurs and a cost that is one-time-per-account feel identical when you only ever meet them one repo at a time.** Five repos onboarded, five Pages clicks, and the licence sits behind all five looking like the sixth step.

## §0b 🔴 AND THE WORD "PRIVATE" IS DOING TWO JOBS. ONE OF THEM THIS PLAN CANNOT BUY.

**A private repo does not produce a private site on this account's tier.** Publishing a Pages site *privately* — access restricted to people with read access to the repo — **requires GitHub Enterprise Cloud** ([changing-the-visibility-of-your-github-pages-site](https://docs.github.com/en/enterprise-cloud@latest/pages/getting-started-with-github-pages/changing-the-visibility-of-your-github-pages-site)). Pro does not include it.

**This is already the deliberate design and it is written into `build.yml`:** `uritp-docs` was made private *"so that the repo page 404s to anyone who swaps `github.io` for `github.com` while Pages keeps serving `gh-pages` to the public."* **Private source, public site. On purpose.**

🔴 **THAT IS FINE FOR SAFETY POLICY AND IT IS NOT FINE FOR A COURSE ROSTER, AND THE ASK NAMED COURSES.** "A new private repo for my courses" reads as *a private site*. On this tier it delivers **a private repo with a publicly readable rendered site**. Anyone with the URL reads it; the private flag protects the markdown, not the pages.

🚫 **And the engine has no gate to fall back on.** `README.md` §7 records that `status: gated` is unimplemented and that shipping a gate which merely looks like one is worse than shipping none. `router:` withholds a folder from the *sidebar*; `specs/chrome.md` §8 states plainly that it *"removes nothing a reader could type, guess, or find in search."*

⚑ **The generalisation, and it is the reason this section outranks the rest of the file: the credential work makes it CHEAPER to point the renderer at a repo, and cheaper is exactly what removes the moment where somebody asks whether it should be pointed there at all.** Convenience and blast radius are the same lever pulled in opposite directions. **Ruling 1 is therefore not a config question.**

---

## §1 The true onboarding cost, measured at HEAD `068057c`

The comment in `publish.yml` says adding a site is *"THREE edits — instance, build.yml matrix, this list."* **That undercounts by two, and both of the missing ones live outside the repo, which is why they are the ones that get forgotten.**

| # | Step | Where | Derivable? |
|---|---|---|---|
| 1 | `instances/<slug>/site.yml` (+ `routes.yml`, `theme.css`) | this repo | — it IS the declaration |
| 2 | a row in `build.yml`'s `matrix.include` | this repo | ✅ **yes**, runs inside a job |
| 3 | an option in `publish.yml`'s `site` **choice** list | this repo | 🚫 **NO** — see §4 |
| 4 | add the repo to `DOCRENDER_TOKEN`'s scope | **github.com settings** | 🚫 not a file |
| 5 | switch on Pages → `gh-pages` on the new repo | **github.com settings** | 🚫 not a file |

✅ **Step 1 vs 2 already has a real mechanism and it should be left exactly alone.** `build.yml`'s *"Confirm the matrix agrees with the instance config"* step hard-fails when `matrix.repo` and `site.yml`'s `content_repo` disagree. **That is the correct treatment of a legitimate duplicate: not deleted, but unable to drift silently.** Any change to step 2 must keep it or replace it.

### The four times step 4 has been paid for, from the files

| # | Date | Shape | Symptom |
|---|---|---|---|
| 1 | 2026-08-03 | repo transferred in after the PAT was minted | `exit code 128`, read as a broken build |
| 2 | 2026-08-04 | `uritp-docs` went private | checkout died *exactly as the struck comment predicted* |
| 3 | 2026-08-16 | `uritp-safety` created and transferred in | same cause, third time |
| 4 | 2026-08-18 | secret empty or wrongly scoped | **no loud failure** — the `\|\|` fallback hands over `github.token`, and the 403 reads as a permissions fault on the content repo |

🔴 **INSTANCE 4 IS THE ONE THE BUILD HAS TO FIX, NOT INSTANCE 1.** A confusing error is a bad afternoon. **A silent fallback to a token scoped to the wrong repo is a build that looks green and publishes nothing**, and `poll.yml` already carries the identical trap under a different name: *"a called workflow receives NO secrets by default… Forgetting this does not error: the build goes green, every deploy is skipped."*

---

## §2 The mechanism: a GitHub App, minted per run

Replace the static PAT with an App installed on `mawizorek`, and mint an installation token at run time.

```yaml
- uses: actions/create-github-app-token@v3
  id: app-token
  with:
    client-id: ${{ vars.DOCRENDER_APP_CLIENT_ID }}
    private-key: ${{ secrets.DOCRENDER_APP_KEY }}
    owner: ${{ github.repository_owner }}
```

Then `token: ${{ steps.app-token.outputs.token }}` at the content checkout and `personal_token:` at the deploy.

**What actually changes, and it is smaller than it sounds:**

| | today | after |
|---|---|---|
| granting a new repo | edit the PAT's repository list | **tick a box in the App's installation** (or nothing at all — ruling 1) |
| credential lifetime | until the PAT expires or is rotated | **1 hour**, minted and discarded per run |
| rotation | re-mint, re-paste, re-scope | the App key is set once and outlives every repo |
| failure when unscoped | silent fallback to `github.token` | **the mint step fails** — §3 |

⭐ **`owner` WITH `repositories` OMITTED IS THE WHOLE ANSWER TO "WITHOUT ADDING A NEW KEY."** The action then scopes the token to every repo in that owner's installation ([action.yml](https://github.com/actions/create-github-app-token/blob/main/action.yml)), so a repo created five minutes ago is reachable on the next run with **zero edits in this repo and zero edits to a secret.**

⚠️ **Permissions the App needs, and it is NOT read-only.** `contents: read` covers the content and `maw-themes` checkouts. **The deploy step writes `gh-pages` on the content repo, so `contents: write` is required** — the App is therefore at least as powerful as the PAT it replaces, and "a short-lived token" is a statement about *duration*, never about *authority*.

---

## §3 ⭐ THE REAL WIN IS THAT THE FALLBACK STOPS BEING SILENT

`token: ${{ matrix.publisher == 'matrix' && secrets.DOCRENDER_TOKEN || github.token }}` cannot tell an absent secret from a wrongly-scoped one. Both take the `||` branch, both hand over a token scoped to *this* repo, and the resulting message accuses the content repo.

**An App token has no such branch.** A missing key, a bad key, or a repo outside the installation fails **at the mint step, by name, before any checkout runs.** ⭐ *That converts a class of failure this repo has documented four times from "reads as a broken build" to "reads as the thing that is actually wrong."*

⚠️ **AND IT COSTS SOMETHING REAL THAT MUST BE PRESERVED — the `publisher`-keyed token is not clutter.** `build.yml` argues it precisely: keying the read credential to `publisher: matrix` means the PAT's read access is *"proven by a deploy that works, not assumed from a checkbox nobody has looked at."* **An `owner`-wide App token deletes that proof.** Ruling 2.

---

## §4 🚫 THE DROPDOWN CANNOT BE DERIVED. RETRACTED IN CHAT AND RETRACTED HERE.

Scoping this verbally I suggested generating `publish.yml`'s `site` list from `instances/`. **That is wrong.** A `workflow_dispatch` `choice` list is read **before any job starts**, so no step can compute it. `publish.yml` says so, and `hml` shipped unpublishable on exactly this.

⭐ **The rule was already written down and I walked past it:** *"Platform limits produce legitimate hand-maintained copies — name them as exceptions and state the edit count."* **A hand-maintained list with a stated reason is not the same defect as a hand-maintained list nobody has justified**, and conflating them is how a real constraint gets "fixed" into a bug.

**So the honest reduction is 5 steps → 3**, of which 2 are single clicks in GitHub settings and one is the instance folder itself. **Do not describe this build as removing the dropdown.**

---

## §5 🔴 THE SCOPE PROBLEM, WHICH IS THE PART THE CREDENTIAL WORK DOES NOT TOUCH

*"A new private doc renderer for a specific production"* is not a credential ask and it is not satisfied by anything above.

Both workflows do `actions/checkout` on `content_repo` at `main`, **whole repo**, then render it. There is no subtree knob. So:

- **one production → one repo.** Not one scoped view into `uritp-docs`.
- pointing an instance at an existing repo renders **everything in it**.

🔴 **AND THERE IS A LIVE PII CASE, ALREADY LEAKED TWICE.** `maw-prose` holds theatre docs **and** `apps/hml-llc/` (the family loan business). Real payee name + payment handle shipped into a public repo 2026-07-29 (scrubbed same day, **values still in history at `eb63e88`**), and a second copy surfaced 07-31 in a snapshot row that does not inherit edits from its source. **A `content_root:` key would be the difference between "render the theatre docs" and "render the loan business too."**

⚠️ **NOT SPECCED HERE, AND THE REASON IS THIS REPO'S OWN RULE.** `specs/visibility-split.md` §4: *"Performing surgery on an over-budget file as a side effect of splitting a different one is how a tidy-up becomes an outage."* A subtree key touches `instances/`, both checkouts, `docindex`'s base-URL handling and `sizecheck`'s content walk. **It is its own build.** Named so nobody reads the credential work as having answered it.

---

## §6 What must NOT change

- 🚫 **`publish-default.yml` MUST STILL RUN WITH NO SECRET AT ALL.** Its header is explicit: the gold standard must be live because *"a written specification rots, an executable one cannot,"* and it publishes to this repo's own Pages so `GITHUB_TOKEN` suffices. It already refuses to require `DOCRENDER_TOKEN` for `maw-themes` for exactly this reason. **An App must be an alternative on that path, never a prerequisite.** If the template ever needs a secret to build, this build broke the one site whose job is to be undeniable.
- 🚫 **`template` keeps `github.token`.** Nothing has ever demonstrated the credential can read `template-docs`, and taking that on faith is how the first `128` arrived.
- 🚫 **The `concurrency` group strings stay byte-identical across `build.yml` and `publish.yml`.** That one string is the only thing making them share a deploy queue; rename it on one side and the 2026-08-18 ref race returns silently, **with the symptom appearing in the other file.**
- 🚫 **`secrets: inherit` in `poll.yml` still matters.** The App private key is a secret like any other. Same trap, new name.
- 🚫 **The matrix-vs-`site.yml` agreement check stays.** §1.

---

## §7 Files and sizes

🔴 **NO SIZE TABLE, ON PURPOSE**, per `specs/chrome.md` §6 and the finding it cites: *"A size written into prose is wrong within two days, every time, in this repo."* Measure at the moment you act.

**What gets touched:** `.github/workflows/build.yml` · `.github/workflows/publish.yml` · **NOT** `publish-default.yml` (§6) · `poll.yml` only if the secret name changes · `README.md` §6, which is where the PAT is currently explained and would otherwise become the sixth rotted pointer in this family · `publish-dl.md`, which **already owns this file's rationale** and is where every paragraph of *why* belongs.

⚠️ **`publish.yml` IS 13,960 B OF WHICH MOST IS PROSE, AND THIS BUILD WILL WANT TO ADD MORE.** It was cut 27KB → 10.2KB by moving argument to `publish-dl.md`. **Put the reasoning in the sibling; leave a `§ section` pointer in the workflow.** Do not re-inflate the file whose de-inflation is the standard.

---

## §8 ⏳ Rulings needed (four)

**1. 🔴 App installed on ALL repositories, or on selected ones? THIS IS NOT A TECHNICAL CALL AND ONLY MICHAEL MAKES IT.**

- **All repositories** — the literal ask. A new course repo is renderable the moment it exists, zero edits anywhere. **And the credential reaches `maw-prose`/`apps/hml-llc/` and every future repo, forever, with nobody re-deciding.**
- **Only select repositories** — one checkbox per new repo on github.com. **Not zero friction, but the friction is a checkbox rather than minting, scoping and pasting a PAT.**

⭐ **Recommend SELECT.** The pain named in the ask was *"add a new key"* — and select-scope removes the key entirely while keeping the moment where somebody answers *"should this repo be renderable?"* **Given §0b (a private repo yields a public site) and a domain that has already leaked twice, one checkbox is the correct price.** ⚠️ Mira's note, recorded rather than resolved: **Tutor Tate owns course/student data and Realty Riley owns the HML business, and neither has been seated on this.**

**2. Does the `publisher`-keyed read token survive?** An `owner`-wide App token makes it moot, and §3 says the proof it provided was load-bearing. **Recommend: keep the `publisher` key on the CONTENT checkout even under an App token.** It costs one expression and preserves the property that read access is demonstrated by a working deploy. 🚫 The alternative is defensible only if ruling 1 lands on **select** — in which case the App's installation list *is* the reviewed list, and the `publisher` key becomes the second copy of it.

**3. One App or two?** A single App doing read-content and write-`gh-pages` is simplest. Two (a read App and a deploy App) would let the render path run with no write authority at all. **Recommend ONE.** Two Apps is two installations to keep in step, which is the manifest-pair defect this repo has retired three files over — and the deploy already needs write on the same repos.

**4. Does `DOCRENDER_TOKEN` get deleted, or kept as a fallback?** **Recommend DELETED, in a follow-up commit after one green run of each workflow.** A retained fallback is precisely the `||` branch §3 exists to remove; keeping both means the silent-wrong-token failure survives the build that was meant to kill it. ⚠️ **Not in the same commit** — one green run first, because the ref-race incident proved a red job on the last step can sit on top of perfectly good work.

---

## §9 Sequence

1. **LOOK FIRST, and it is free: does a GitHub App already exist on `mawizorek`?** Nobody has checked. Settings → Developer settings → GitHub Apps. **If one exists, most of step 2 is already done and this spec is half-obsolete.**
2. **Answer ruling 1.** Everything downstream reads differently depending on the answer, and it is the only step that is not reversible by a commit.
3. **Create the App, install it, store the client ID as a `vars` entry and the private key as a secret.** No workflow change yet.
4. **`publish.yml` FIRST, not `build.yml`.** It is the human path with a **preview mode** that deploys nothing, so the credential can be proven end-to-end without a single site moving. `build.yml` is the routine and it publishes on every green run.
5. **`build.yml` second**, one matrix row at a time if the token expression changes shape.
6. **Verify the way this repo verifies:** the **footer stamp** on a live site is how a landed deploy is confirmed. A green job is not evidence.
7. **Then `README.md` §6 and `publish-dl.md`.**
8. **Ruling 4's deletion commit, last.**

🚫 **Do not start at 5.** A routine that fires every 20 minutes is the worst possible place to first learn whether a new credential works.

---

## §10 Known limits, stated now rather than discovered

- **An installation token expires after 1 hour.** Irrelevant here — the longest measured job is ~30s against a 10-minute timeout — but it is a real constraint on anything long-running, and the action's own README flags it.
- **A fine-grained PAT is scoped to ONE resource owner, and so is an App installation.** The whole family living under `mawizorek` is what makes either work. **A repo under a different owner is a different installation and this build does not change that.**
- 🚫 **This does nothing about `status: gated`.** Publication control is `status:`; admission is `router:`; neither is authentication. §0b.
- ⚠️ **Nothing here has been executed.** Every claim about the workflows is read out of the files at `068057c`; every claim about the action is read out of GitHub's published docs. **The App's existence is UNVERIFIED — step 1 of §9.**
- ⚠️ **The five-step count in §1 is measured against the current five instances.** A sixth instance with a different publisher shape could add a step nobody has met yet.

---

## §11 🚩 Found while reading. Flagged, NOT fixed.

**a. 🔴 `specs/` HAS SIX FILES, THE INDEX KNOWS FOUR, AND THE BUILD NUMBERS HAVE COLLIDED TWICE.** `visibility-split.md` and `draft-watermark.md` are both `BUILD 4`; `chrome.md` and `print-identity.md` are both `BUILD 5`. `next-build-spec.md`'s header says **SIX INDEPENDENT BUILDS** and there are **eight** (two in-file plus six specs).

⭐ **Its own header already ruled on this case in advance:** *"The count is kept rather than removed only because there is nowhere here to derive it from; **if it is wrong again, delete it rather than refresh it.**"* It is wrong again. **The instruction is to delete the count, and the numbers themselves are now the same defect one layer down** — a hand-maintained ordering interface with two duplicate keys.

**b. 🔴 AND I CANNOT ADD THE INDEX ROW, WHICH IS ALSO WHY THE OTHER TWO SPECS ARE INVISIBLE.** `next-build-spec.md` is **32,840 B**. The write standard is unambiguous: *"Large files (>~30KB) NEVER go through `create_or_update_file` (LOCKED, 2026-07-02)"* — it corrupted a file four times in one session, and the read path cannot recover the bytes. **So the row is a hand edit or it waits for the split.**

⚑ **`visibility-split.md` §10e reached the same wall on 2026-08-07 and read it as a judgement call** — *"the row goes in when that file is next opened deliberately."* **It is not a judgement call, it is a hard write limit**, and the consequence is that the index has been structurally unable to grow for eighteen days while three specs queued up behind it. ⭐ *A file that cannot be edited stops being an index and becomes a snapshot, and nothing announces the transition.*

✅ **The fix already exists in that file's own header:** *"BUILDS 1 AND 2 SHOULD FOLLOW THEM, leaving this as an index."* Moving builds 1 and 2 to `specs/` takes it under the cap and makes the index writable again. **That is the unblocking build for three specs at once, and it is not this one.**

**c. `sizecheck` still cannot see any of this.** `_ENGINE_SOURCE` is `docrender/*.py` plus `assets/*`; the markdown half walks `DOCRENDER_CONTENT`, the *content* repo. So `README.md`, `next-build-spec.md` and everything in `specs/` are **unbudgeted and unreported** — which is exactly how the index reached 32 KB unremarked. Raised in `visibility-split.md` §10d on 2026-08-07 and still true.

**d. `publish.yml`'s "THREE edits" comment undercounts by two.** §1. **Fix it in whichever commit next touches that file** — it is one line, and the two it omits are the two that live outside the repo and therefore the two that get forgotten.
