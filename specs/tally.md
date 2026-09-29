# `!!! tally` — a live-math worksheet that hands its numbers to a form

**Scoped and built 2026-09-28.** No build number, on purpose: see the numbering debt in [`../next-build-spec.md`](../next-build-spec.md). Code: [`docrender/tally.py`](../docrender/tally.py) + [`docrender/tally_assets.py`](../docrender/tally_assets.py), composed in [`hooks/05b_program.py`](../hooks/05b_program.py). **One live example:** `uritp-docs` → `app/app-box-office.md`.

## 1. What it is, in one line

A page declares a worksheet in frontmatter (**rows, prices, formulas**), writes `!!! tally "name"` where it should appear, and the engine draws it: inputs, live totals, over/short checks, a draft saved on the device, and a **Send to report** button that prefills the page's ClickUp form.

⭐ **It replaced 12 KB of hand-written HTML and JS inside `app/box-office.md`.** Michael's ruling (2026-09-28): the features were right, the *code in the md page* was the problem. The feature set was kept whole; the machinery moved to the engine, the data stayed in the page.

## 2. Why "tally" and not "sheet"

Three things were already called a sheet: `docrender/sheet.py` (theme stylesheets), the print sheet vocabulary, and Michael's theatre **run sheets**. A fourth would make every conversation ambiguous. `tally` is what the thing does.

## 3. The authoring contract

```yaml
forms:
  foh-report:
    src: https://forms.clickup.com/...
tally:
  box-office:              # the name `!!! tally "box-office"` uses
    form: foh-report       # a slot in THIS page's forms: block
    Door Sales:            # every other key is a SECTION (a boxed group)
      Door Student: count @ 10
      Door General: count @ 20 | hint text after a pipe
      Door: money = Door Student dollars + Door General dollars
      Concessions Total: money
    Receipts:
      Income Cash: money
      Over Short: check money = Income Cash - Door - Concessions Total
```

**Input rows:** `count` · `money` · `number` · `text` · `email` · `notes` (multi-line) · `date` · `datetime` · a YAML list (a pick-one) · `count @ price` (a priced count: quantity in, dollars shown beside it).

**Result rows:** `money|count|number|percent = expression`, or `check <format> = expression` for a row that reads **✓** at zero and **over / short** otherwise.

**Expressions:** row names, numbers, `+ - * /` (also `× ÷ −`), parentheses, unary minus. On a priced count, `Name` is the quantity and `Name dollars` is quantity × price. Longest name wins, so `Door Student dollars` never reads as `Door Student`.

**Hints:** anything after `|` renders small beside the label. ⚠️ Avoid `: ` and ` #` inside a hint: YAML reads those as a key and a comment.

## 4. Rulings, with the reason each one exists

1. **A row name is the label, the expression name, and the ClickUp question label.** One string, so the three cannot drift. 🔴 **The engine cannot see the live form**, so a row whose name matches no question prefills nothing, silently. Rename the question on the form, not the row. ClickUp does not prefill labels containing punctuation, so keep names to letters and spaces.
2. **Math compiles at build time.** Expressions become postfix tokens in `data-expr`. A typo'd or forward-referenced name is a **build note naming the row**, and that row is dropped, rather than a sheet that shows $0.00.
3. **A result may only use rows above it.** One pass in page order; cycles impossible by construction.
4. **Results stay blank until an input they depend on has a value.** An untouched sheet reads empty, not $0.00 everywhere.
5. 🔴 **A comparison waits for both sides.** `check` and `percent` rows go live only when every row they name directly is live, so *Count Vs Expected* stays blank until the house is counted instead of shouting "-50 short" at the first ticket.
6. **Only input rows are sent.** Results are the sheet's working, and ClickUp's own formula fields own the record.
7. **`date` and `datetime` send unix milliseconds; `notes` send `\r\n` line breaks.** What ClickUp prefill expects.
8. **Send replaces the iframe node**, never `iframe.src =`, for the Back-button reason in `forms.py`. It opens a folded form and scrolls to it. With no matching frame on the page, it opens the prefilled form in a new tab. ⚠️ The replaced frame loses ClickUp's height listener and sits at the forms floor (40rem), which is the known forms behaviour after a reload.
9. **Drafts save per page and per worksheet** in `localStorage` until **Clear**, which asks first. Nothing leaves the device until the ClickUp form is submitted.
10. **A missing or non-ClickUp `form:` slot still draws the sheet** and puts a dead **Send** marker where the button would be. An undeclared `!!! tally` name draws a dead **Worksheet** marker. Both land in the build report.
11. **Prices live in the page, not the engine** (Michael, 2026-09-28). ⚠️ **WORKAROUND**: hardcoded until the FileMaker price schema exists. The engine knows no production and no price.
12. **Print** hides the button bar and status line and stacks sections. The sheet prints as a filled record.

## 5. Traps

- 🔴 **No blank line may appear in the emitted HTML.** It would end the raw HTML block and Markdown would rewrite the rest as paragraphs. `_html` joins with single newlines.
- 🔴 `[` and `]` in any author text are entity-escaped so `](` and `]{` can never form before conversion.
- ⚠️ `@media` in the appended CSS is safe **only because this runs at 05b**, after hook 03 resolved every `@id`. Moving tally earlier would break that.
- ⚠️ Order in 05b's markdown composition is free: tally emits no `!!!` and reads no other directive's output. The Send button finds the form **in the browser**, after both have rendered.

## 6. Verified before merge (2026-09-28)

The box-office frontmatter was parsed with a real YAML parser, rendered through `tally.py`, and run in headless Chromium against a scripted show night: 10/5/3 door, 2 rush, 4+1 comps, $50.50 concessions, $200 cash, $105.50 charge, $100 float, 20/10/5 online, 2 unclaimed, house 55 of 100. Door $235.00, door + concessions $285.50, day-of $305.50, **over +$20.00**, drawer $300.00, online $450.00, total $755.50, expected 58, **count vs expected −3 short**, density 55%. Changing cash to $180 flipped over/short to ✓. Send produced the prefilled URL and opened the folded form. Error paths: typo'd name, forward reference, unclosed paren, constant-only expression, bad type, bad format, duplicate row, undeclared tally, missing form slot, and a directive inside a code fence (left untouched).

⚠️ **Not verifiable from the engine:** that each row name matches a live question label, and that the multi-select **Production** field accepts a prefilled option name. Test on a real submission.

## 7. Open, with owners

- **Michael:** does *Expected House* subtract unclaimed online tickets? The example does, as the old page did.
- **Michael:** the form's questions still carry their old labels (19 of 26 differ), so until the rename, Send prefills only the 7 that match.
- **Later, not now:** a `checklist` row type for run sheets is the obvious next step and is deliberately **not** built. `!!! cards` comes first.
