# `!!! cards` — a launcher grid the author controls from one line

✅ **BUILT 2026-09-28.** Indexed from `next-build-spec.md`. Code: `docrender/cards.py`, composed in `hooks/05b_program.py`.

> Michael, 2026-09-28: *"I want more control of the card content and the number across and the size of them."* Then, after the Workshop: *"add per-card colors."*

Workshopped on the handoff session task (Mira convening; Frank FOLD-IN; the seven plus Stu and Dara; verdict ADJUST, with the fixes folded into this scope).

---

## The shape

```
!!! cards cols=3 phone=2 size=l style=tiles color=blue
    - 🎟️ [House Reports](@app-foh-report) {color=red badge="Tonight"}
      Submit each performance's report.
    - 📋 @run-sheet-foh {wide}
    - 🧰 Parked idea
      No link yet. It renders as a plain card.
```

**One indented block. Each `- ` bullet is one card.** Its first line is the head, and anything indented under it is the blurb, in any markdown.

### Grid knobs (the directive line)

| key | values | default |
|---|---|---|
| `cols` | 1–6, the most across on a wide screen | 3 (tiles) · 1 (rows) |
| `phone` | 1 or 2, across on a phone | 1 |
| `size` | `s` `m` `l` (or small/medium/large) | `m` |
| `style` | `tiles` (launcher) · `rows` (full-width list with a chevron) | `tiles` |
| `color` | a palette name, the default for every card | none |

`cols` is a ceiling, not a promise: a phone uses `phone`, and a tablet (600–960px) uses at most 2.

### Card knobs (a trailing brace on the head)

`{color=<name> badge="<text>" wide}`: all optional, in any order.
- `badge` is plain text, for time or state ("Doors 7:30", "Tonight").
- `wide` spans two columns wherever there are two.
- **Palette:** red pink purple indigo blue cyan teal green lime yellow amber orange brown grey. Named rather than hex, because the colour reaches the card through a class.

### Card content

- **Icon:** a leading emoji on the head.
- **Title:** the rest of the head.
- **Bare `@id`:** a head that is only `@id` pulls the title from the page, and pulls its `summary` too when no blurb is written.
- **Whole-card tap:** a card with **exactly one** link is tappable anywhere, whether that link is in the head or the blurb. With two or more, the links stay separate. A card with no link is a parked scaffold card.

---

## Rulings baked in (and why)

1. **It compiles to Material's own `grid cards` markup** (Frank's condition). Hover, border and dark mode stay Material's, and a hand-written `grid cards` page is untouched. This is not a second card system.
2. **Content lives in the body, not in frontmatter** (Cleo). Tally needed frontmatter because a worksheet is data. Cards are content.
3. **Per-card knobs ride on an empty `span.dr-k` plus CSS `:has()`.** Markdown gives a list item no attribute hook, and a second parser for one class name is worse. An old browser without `:has()` gets a plain Material card.
4. **A brace naming none of `color`/`badge`/`wide` is left alone for attr_list.** A brace naming any of them is consumed, and its bad tokens are reported (Rhys #4).
5. **Dead references look dead.** A bare `@id` to no built page draws the standard `docrender-dead` span, dims the card, logs a `notes` line, and records the edge with `ok: false` (Rhys #5).
6. **Fences are guarded; inline code is not** — `sub_outside_code` splits text at every backtick span, which would cut a card block in half.
7. **CSS ships with the directive**, once per page that draws cards (Enzo #1). `chrome.py` and `assets.py` are untouched.
8. **Print:** two across, no tint, no stretched-link overlay.

## 🅿️ Futures (Skye's line, not in v1)

- cover images
- per-card size
- live data on a card (counts, status)
- a third style
- hex colours
- checkboxes: those belong to the run sheets, not to cards

## Verified

Headless Chrome ran against the transform's output at 1100 / 700 / 375px.
- Columns per breakpoint, `phone=2`, and `wide` span all behaved.
- Grid colour was overridden by the card colour, and badges showed.
- In rows style the chevron appeared only on linked rows.
- A dead card dimmed with a dashed border.
- A centre-point tap on each linked card resolved to its one link; two-link and unlinked cards did not stretch.
- The unit run also checked that a fenced example stayed verbatim and that a bad colour was reported.
