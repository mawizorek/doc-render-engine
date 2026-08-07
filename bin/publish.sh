#!/usr/bin/env bash
#
# publish -- dispatch a doc-render-engine publish from any terminal.
#
#     publish uritp theme:eos
#     publish prp
#     publish theatre theme:random mode:publish note:"checking the new palette"
#     publish --list
#
# =============================================================================
# WHY THIS FILE EXISTS, AND IT IS NOT A NEW IDEA
# =============================================================================
# Two files in this repo have asserted since 2026-08-05 that this helper was
# already here:
#
#   .github/workflows/publish.yml  "Any wrapper script must lower-case the
#                                   argument; the terminal helper in
#                                   uritp-docs/guides does."
#   docrender/instance.py          "The only CONSUMER of an alias is the
#                                   `publish` shell helper, which resolves a
#                                   typed name to a slug before it dispatches
#                                   the workflow."
#
# Neither was true. Michael typed `publish uritp theme:eos` on 2026-08-07
# expecting it to work, which is exactly what a promised-and-absent tool costs:
# somebody plans against it. Both claims are corrected in the same PR that adds
# this file, and both now point HERE.
#
# THE OLD POINTER NAMED A PLACE THE ARCHITECTURE FORBIDS. `uritp-docs` is a
# CONTENT repo: it holds markdown and no machinery, which is what keeps its
# Download ZIP clean. A shell script in `uritp-docs/guides/` would ship inside
# that ZIP and break the rule the whole family was reverse-engineered from. So
# the helper was never merely missing -- it was described as living somewhere
# it could never have lived.
#
# It belongs HERE because this repo already owns both things it touches: the
# workflow it dispatches, and the `instances/*/site.yml` files it reads names
# out of. When a site is added, this script needs no edit.
#
# =============================================================================
# INSTALL (once)
# =============================================================================
#   curl -fsSL https://raw.githubusercontent.com/mawizorek/doc-render-engine/main/bin/publish.sh -o ~/.publish.sh
#   echo 'source ~/.publish.sh' >> ~/.zshrc
#
# From a checkout instead:
#   echo 'source /path/to/doc-render-engine/bin/publish.sh' >> ~/.zshrc
#
# IT IS DIRECTORY-INDEPENDENT ON PURPOSE. Everything it needs is read over the
# API, so it works from the content repo, from the engine repo, or from your
# home directory. A helper that only works when you are cd'd into the right
# checkout is a helper you stop using.
#
# Requires the GitHub CLI (`gh auth login`). python3 + PyYAML is used for name
# resolution when present; see `_dr_aliases_of` for what happens without it.
#
# =============================================================================
# THE GRAMMAR IS THE WORKFLOW'S OWN INPUT NAMES. THERE IS NO SECOND VOCABULARY.
# =============================================================================
#   publish <site-or-alias> [theme:<name>] [mode:<preview|publish>] [note:<text>]
#
# `site`, `mode`, `theme` and `note` are precisely the four dispatch inputs on
# publish.yml. Nothing here invents a word, abbreviates one, or reorders them,
# so anything you learn at this prompt is true of the web form and the reverse.
# The one positional is the site, because it is the only argument that is
# always required and never ambiguous.
#
# MODE DEFAULTS TO `preview`, WHICH IS THE SAME DEFAULT THE WEB FORM CARRIES
# and the same instruction template-docs/authoring/publishing.md gives in bold:
# always preview first. So a bare `publish uritp` deploys NOTHING. Going live
# is `mode:publish`, typed out, every time. That verbosity is the feature: a
# command named `publish` must not publish by accident.
#
# =============================================================================
# WHAT THIS SCRIPT DELIBERATELY DOES NOT DO
# =============================================================================
# IT DOES NOT VALIDATE THE THEME. The legal set is the live union of
# maw-themes' themes.json, the canonical colour table and theme/themes.tsv,
# resolved inside the build. A check here would be a fourth copy of that union,
# wrong the first time a palette is added upstream, and wrong in the direction
# that REFUSES a legal name. The engine already discards an unknown theme
# loudly, keeps the site's declared one, and lists the legal names -- so a typo
# costs one preview run and produces a better message than this could.
#
# IT DOES NOT KEEP A LIST OF SITES. It reads `instances/` live. Every other
# list of sites in this family is derived from those files; the ONE exception
# is the `choice` dropdown in publish.yml, which is a platform limit rather
# than a decision. This script is not going to become a second exception.

_DR_ENGINE="mawizorek/doc-render-engine"

_dr_say() { printf '%s\n' "$*" >&2; }

_dr_aliases_of() {
  # Every alias declared by one instance, one per line, lower-cased.
  #
  # TWO READERS, AND THE FALLBACK IS THE HONEST-BUT-NARROW ONE. With PyYAML
  # present this parses the file properly. Without it, the grep path handles
  # the FLOW style all four instances currently use -- `aliases: [a, "b c"]` --
  # and will silently miss a block-style list. Stated rather than hidden: if a
  # name stops resolving, this is the first thing to check, and the fix is
  # installing PyYAML rather than writing a better regex.
  local slug="$1" body
  body=$(gh api "repos/$_DR_ENGINE/contents/instances/$slug/site.yml" -H 'Accept: application/vnd.github.raw' 2>/dev/null) || return 1

  if python3 -c 'import yaml' 2>/dev/null; then
    printf '%s' "$body" | python3 -c 'import sys, yaml; d = yaml.safe_load(sys.stdin) or {}; [print(str(a).strip().lower()) for a in (d.get("aliases") or [])]' 2>/dev/null
    return 0
  fi

  printf '%s' "$body" | grep -m1 '^aliases:' | sed 's/^aliases:[[:space:]]*//; s/^\[//; s/\]$//' | tr ',' '\n' | sed 's/^[[:space:]]*//; s/[[:space:]]*$//; s/^"//; s/"$//' | tr '[:upper:]' '[:lower:]' | grep -v '^$'
}

_dr_instances() {
  gh api "repos/$_DR_ENGINE/contents/instances" --jq '.[] | select(.type=="dir") | .name' 2>/dev/null
}

_dr_resolve() {
  # A typed name -> a real instance slug, or nothing.
  #
  # SLUGS ARE CHECKED FIRST, AND THAT ORDER IS LOAD-BEARING. It is the same
  # order instance.py's collision check assumes when it warns that an alias
  # equal to another site's slug "publishes THAT site, not this one." Two
  # resolvers disagreeing about precedence would make that warning a lie.
  #
  # It is also the fast path: one API call for `publish uritp`, and the walk
  # over every site.yml only happens for a name that is not already a slug.
  local want slug alias
  want=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')

  if gh api "repos/$_DR_ENGINE/contents/instances/$want/site.yml" --silent 2>/dev/null; then
    printf '%s' "$want"
    return 0
  fi

  while read -r slug; do
    [ -n "$slug" ] || continue
    while read -r alias; do
      if [ "$alias" = "$want" ]; then
        printf '%s' "$slug"
        return 0
      fi
    done < <(_dr_aliases_of "$slug")
  done < <(_dr_instances)

  return 1
}

_dr_list() {
  local slug
  while read -r slug; do
    [ -n "$slug" ] || continue
    printf '  %-10s %s\n' "$slug" "$(_dr_aliases_of "$slug" | paste -sd', ' -)" >&2
  done < <(_dr_instances)
}

publish() {
  command -v gh >/dev/null 2>&1 || {
    _dr_say "publish: the GitHub CLI is not installed. https://cli.github.com"
    return 1
  }

  if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    _dr_say "usage: publish <site> [theme:<name>] [mode:<preview|publish>] [note:<text>]"
    _dr_say "       publish --list"
    _dr_say ""
    _dr_say "mode defaults to preview, which deploys nothing. Sites and aliases:"
    _dr_list
    return 0
  fi

  if [ "$1" = "--list" ]; then _dr_list; return 0; fi

  local typed="$1"; shift
  local theme="" mode="preview" note="" arg site

  for arg in "$@"; do
    case "$arg" in
      theme:*) theme="${arg#theme:}" ;;
      mode:*)  mode="${arg#mode:}"   ;;
      note:*)  note="${arg#note:}"   ;;
      *)
        # REFUSED RATHER THAN IGNORED. A mistyped `them:eos` that is silently
        # dropped renders the site's own theme and reads as the feature being
        # broken -- the same failure class as a config key that does nothing
        # while appearing to do something.
        _dr_say "publish: don't understand '$arg'. Expected theme:, mode: or note:."
        return 1
        ;;
    esac
  done

  if [ "$mode" != "preview" ] && [ "$mode" != "publish" ]; then
    _dr_say "publish: mode must be 'preview' or 'publish', not '$mode'."
    return 1
  fi

  site=$(_dr_resolve "$typed") || {
    # NEVER GUESS A NEAR MATCH. Publishing the wrong site is not recoverable by
    # re-running: it has already overwritten a live site with another one's
    # content. Printing the whole list is cheaper than a wrong answer.
    _dr_say "publish: '$typed' is not a site or a declared alias. Known:"
    _dr_list
    return 1
  }

  # THE LOWER-CASING publish.yml ASKS FOR HAPPENS IN _dr_resolve, NOT HERE: a
  # `choice` input is case-sensitive, so `-f site=URITP` is rejected before any
  # job starts, with an error about an invalid value rather than about case.
  # Slugs come back from the API already lower-case.

  local args=(-R "$_DR_ENGINE" -f "site=$site" -f "mode=$mode")
  [ -n "$theme" ] && args+=(-f "theme=$theme")
  [ -n "$note" ] && args+=(-f "note=$note")

  gh workflow run publish.yml "${args[@]}" || return 1

  [ "$typed" != "$site" ] && _dr_say "publish: '$typed' -> $site"
  _dr_say "publish: $site / $mode${theme:+ / theme: $theme}"
  [ "$mode" = "preview" ] && _dr_say "publish: preview only -- nothing will deploy."

  # `gh workflow run` RETURNS NO RUN ID, so the URL below is found by asking for
  # the newest run afterwards. THAT IS A RACE: two publishes dispatched within a
  # few seconds and this prints the other one's link. It is a convenience, not a
  # receipt -- the authoritative confirmation is the footer stamp on the live
  # page, per authoring/publishing.md.
  sleep 3
  local url
  url=$(gh run list -R "$_DR_ENGINE" --workflow=publish.yml --limit 1 --json url --jq '.[0].url' 2>/dev/null)
  [ -n "$url" ] && _dr_say "publish: $url"

  if [ -n "$theme" ]; then
    _dr_say "publish: the theme actually used is named in the notice at the top"
    _dr_say "         of that run -- the run title cannot name a random roll."
  fi

  return 0
}
