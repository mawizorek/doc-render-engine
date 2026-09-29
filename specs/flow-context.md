# flow context — one strip per page, faces for app binders

🚫 **Claims no build number, deliberately** (see `next-build-spec.md`). Scoped and
built 2026-09-28. Arguments: [`docrender/program-dl.md`](../docrender/program-dl.md) D1.

## Author surface

```
# the binder (owns the list)
id: binder-emergency-handbook
type: program
chain: [emergency-contacts, fire, ...]

# the app face (walks the same list, owns nothing)
id: app-emergency-handbook
type: program
chrome: app
chain: "@binder-emergency-handbook"
```

Body of the face keeps `!!! chain "binder-emergency-handbook"` for its contents list.

## Rules

1. A string `chain:` starting with `@` is a face. The target must be a list chain.
   Alias-of-alias and dead targets are build-report notes.
2. Faces never claim prev/next (`nav._apply` skips them). The face hub gets a Start
   strip with `via=<face id>`.
3. Every page in a flow gets `hide: footer` automatically.
4. Strip links carry `?via=<id>`; the script picks the active strip; no script = all.
5. Under an `app` face the member page gets `html.dr-app` (chrome.CSS is inlined on
   such pages only) and its Finish goes back to the face hub.

## Verify

Emergency Contacts on `uritp-safety`: two server strips (binder, General Safety),
one visible. `?via=app-emergency-handbook` = app chrome + Finish to the app hub.
No footer prev/next on any flow page.
