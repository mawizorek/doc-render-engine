/* The SIDEBAR half of the router. Split out of assets/router.js 2026-08-16 at
 * 22,232 B, past the engine's 22KB hard read limit.
 *
 * A pure MOVE -- every function and every comment below is byte-faithful to what
 * was in router.js, because a split that also edits is two changes wearing one
 * commit and you cannot tell which one broke the render. The behaviour change
 * that motivated the split is the NEXT commit. Same discipline as the nav.css
 * split out of base.css on 2026-08-04.
 *
 * ⚠️ THE ONE UNAVOIDABLE EXCEPTION, stated because "pure move" has to be
 * falsifiable: CSS needs no glue and JS does. router.js gains four calls into
 * the surface below plus a null guard, and loses the functions that moved.
 * Nothing else in either file changed in this commit.
 *
 * WHY THIS IS THE SEAM, and it is not "the leftover bytes that made the file
 * fit": router.js has declared it in its own header since 2026-08-06 --
 *
 *     .dr-router     the FORM. Only where a router is declared or inherited.
 *     .dr-nav-boot   the SEALED SIDEBAR. On every page of the site.
 *
 * Two elements, two lifetimes, two audiences. This file is everything that
 * DRAWS the second one. It holds no crypto and no codes: router.js proves a
 * code, decrypts a manifest, and hands the plaintext here. That is the whole
 * contract, and it is why the split does not need a shared crypto module.
 *
 * ⚠️ LOADS BEFORE router.js. The order is set in docrender/assets.py
 * `_FEATURE_ASSETS` and is NOT alphabetical -- router.js calls into this file
 * during its own IIFE, so a later position makes every call a TypeError on the
 * first paint. Both are published only to a site that has a router.
 *
 * ⭐ AND THE DEPENDENCY IS ONE-WAY AND FAIL-SAFE. router.js reads
 * `window.docrenderNavTree` into a local and checks it, so if this file ever
 * fails to ship the FORM still unlocks the page and only the sidebar goes
 * quiet. The important half is never hostage to the decorative one.
 *
 * PUBLIC SURFACE -- what router.js is allowed to call:
 *
 *     entries()             the sealed nav payload, decoded, or []
 *     drawn()               manifests already decrypted this session
 *     keepDrawn(list)       cache them under this build id
 *     paint(list, animate)  draw them into the sidebar
 *
 * Nothing else is exported, deliberately. A second caller reaching into the
 * internals is how one rendering rule ends up with two interpreters.
 */

window.docrenderNavTree = (function () {
  var boot = document.querySelector('.dr-nav-boot');

  /* ⚠️ A SECOND COPY OF router.js's READER, AND THE DUPLICATION IS DELIBERATE.
   * A base64-JSON reader is a PRIMITIVE, not a rule -- there is no behaviour in
   * it to drift, which is the test this repo actually applies. Exporting it and
   * letting router.js call in would make the FORM depend on the SIDEBAR: this
   * file failing to ship would throw inside `routes()` and kill the unlock
   * itself. Six lines against that, in the safe direction. */
  function decode(attr) {
    try {
      return JSON.parse(atob(attr)) || [];
    } catch (e) {
      return [];
    }
  }

  var NAV_STORE = boot ? 'docrender.nav.' + (boot.dataset.build || '') : '';

  function navEntries() {
    return boot ? decode(boot.dataset.nav) : [];
  }

  /* A build url resolved against the site root. The seal ships root-relative
   * urls so ONE payload can serve every page; `data-root` is the only
   * page-specific part, and it rides outside the ciphertext. */
  function siteUrl(u) {
    var prefix = (boot && boot.dataset.root) || '.';
    return new URL(prefix + '/' + u, window.location.href).href;
  }

  function pathOf(href) {
    try {
      return new URL(href, window.location.href).pathname;
    } catch (e) {
      return '';
    }
  }

  function drawn() {
    if (!NAV_STORE) return [];
    try {
      var raw = JSON.parse(sessionStorage.getItem(NAV_STORE));
      return Array.isArray(raw) ? raw : [];
    } catch (e) {
      return [];
    }
  }

  function keepDrawn(list) {
    if (!NAV_STORE) return;
    try {
      sessionStorage.setItem(NAV_STORE, JSON.stringify(list));
    } catch (e) { /* private mode: the sidebar still works, per page */ }
  }

  /* ======================================================================
   * THE SIDEBAR
   *
   * Entries were removed from the nav at build time, so there is nothing to
   * un-hide -- they have to be built. Rendered with our own classes rather than
   * Material's nested-nav markup, which needs a <nav>, a <label> and a hidden
   * checkbox per level to work its expand/collapse machinery.
   *
   * WARNING: AND ON MOBILE THAT IS NOT MERELY A PREFERENCE. Material's drawer
   * is a stack of sliding panels: a nested `<nav class="md-nav">` is positioned
   * OFF-CANVAS until its toggle is checked. Injecting one into a section whose
   * children were sealed -- so it is no longer marked `--nested` and has no
   * toggle -- would put the menu somewhere no reader can reach, on phones only.
   *
   * TWO PLACEMENTS, read off each entry's `p`:
   *
   *   in   the folder still has its own row. Find it, hoist to its <li>,
   *        append the list underneath.
   *   at   `nav: routed` -- the folder is not in the sidebar at all, so entry
   *        ZERO of the manifest is the folder itself and we build its row.
   * =================================================================== */

  /* The flat revealed list. Shared by both placements, because a second copy of
   * the depth/label/link rules would drift. */
  function buildList(items, animate) {
    var list = document.createElement('ul');
    list.className = 'dr-nav-revealed' + (animate ? ' dr-nav-revealed--in' : '');

    items.forEach(function (item) {
      var row = document.createElement('li');
      row.className = 'dr-nav-revealed__item';
      row.setAttribute('data-d', String(item.d || 1));

      /* An entry with no url is a folder heading, not a destination. */
      var cell = document.createElement(item.u ? 'a' : 'span');
      cell.className = 'dr-nav-revealed__link';
      cell.textContent = item.t;
      if (item.u) cell.href = siteUrl(item.u);

      row.appendChild(cell);
      list.appendChild(row);
    });

    return list;
  }

  function topList() {
    return document.querySelector('.md-nav--primary > .md-nav__list');
  }

  /* WHERE THE FOLDER GOES BACK. Michael, 2026-08-06: "it needs to appear in its
   * real sort order."
   *
   * Three levels, deliberately, because the good one can go stale: the row
   * named by `b` may itself have left the sidebar since the build. Falling all
   * the way through lands on the END, which is what shipped yesterday -- so the
   * floor is the previous behaviour rather than a broken sidebar. */
  function place(li, entry) {
    var list = topList();
    if (!list) return false;
    var kids = list.children;

    if (entry.b) {
      var want = pathOf(siteUrl(entry.b));
      for (var i = 0; i < kids.length; i++) {
        var link = kids[i].querySelector('a.md-nav__link');
        if (link && pathOf(link.href) === want) {
          list.insertBefore(li, kids[i]);
          return true;
        }
      }
    }

    if (typeof entry.i === 'number' && entry.i >= 0 && entry.i < kids.length) {
      list.insertBefore(li, kids[entry.i]);
      return true;
    }

    list.appendChild(li);
    return true;
  }

  /* `nav: routed`. The folder was never rendered, so there is nothing to find
   * and everything to build.
   *
   * THE ROW BORROWS MATERIAL'S OWN CLASSES AND THE CHILDREN DO NOT, which looks
   * inconsistent and is the point. This row is joining a list of top-level
   * sections and has to read as one of them, so it takes their markup. The
   * children are a flat list with no toggle -- see the warning above about what
   * borrowing the nested structure costs on a phone. */
  function drawSection(entry, animate) {
    var list = topList();
    if (!list || !entry.items.length) return;
    /* Every page under the folder redraws this from its own payload. Without
     * the guard a reader collects another copy on every navigation. */
    if (list.querySelector('.dr-nav-injected')) return;

    var head = entry.items[0];
    var li = document.createElement('li');
    li.className = 'md-nav__item dr-nav-injected'
      + (animate ? ' dr-nav-injected--in' : '');

    var link = document.createElement(head.u ? 'a' : 'span');
    link.className = 'md-nav__link dr-nav-injected__link';
    link.textContent = head.t;
    if (head.u) link.href = siteUrl(head.u);
    li.appendChild(link);

    var rest = entry.items.slice(1);
    if (rest.length) li.appendChild(buildList(rest, animate));

    place(li, entry);
  }

  function drawUnder(entry, animate) {
    if (!entry.a || !entry.items.length) return;

    /* Scoped to the PRIMARY nav on purpose. The secondary nav is the table of
     * contents, whose links are #fragments on the current page -- so on the
     * routed index page itself their pathname matches the anchor exactly, and
     * an unscoped search would inject the menu into the TOC. */
    var want = pathOf(siteUrl(entry.a));
    var links = document.querySelectorAll('.md-nav--primary a.md-nav__link');
    var link = null;
    for (var i = 0; i < links.length; i++) {
      if (pathOf(links[i].href) === want) { link = links[i]; break; }
    }
    if (!link) {
      console.warn('docrender: nav anchor not found, menu not restored');
      return;
    }

    /* THE LIST HANGS OFF THE <li>, NOT OFF THE LINK'S PARENT. Getting this
     * wrong is what shipped in #48 and it looked spectacular on a phone.
     *
     * With `navigation.indexes` enabled, Material wraps a section's index link
     * in `<div class="md-nav__link md-nav__container">`, and that container is
     * `display: flex`. `link.parentNode` IS that container, so appending there
     * made the revealed menu a third FLEX ITEM beside the title and the
     * chevron.
     *
     * WARNING: IT ALSO INHERITED THE WRONG TYPE, FOR FREE, WHICH IS THE PART
     * WORTH REMEMBERING. `text-transform`, `letter-spacing` and `font-weight`
     * are INHERITED, and that container matches base.css's top-level caps rule.
     * So the child pages rendered in bold 700 uppercase, shouting louder than
     * the section above them, with nothing in any stylesheet saying so.
     * Hoisting one level fixes the layout and the typography in one move. */
    var host = link.closest('.md-nav__item') || link.parentNode;
    if (host.querySelector('.dr-nav-revealed')) return;
    host.appendChild(buildList(entry.items, animate));
  }

  /* WHERE THE READER IS. Michael: "notated which page i then nav to."
   *
   * Material's own active class, so an injected row is highlighted exactly like
   * a built one. The SECOND half matters as much as the first: a folder whose
   * CHILD is active is marked too, because clicking into the folder would
   * otherwise take the highlight off the only row that is always on screen. */
  function markActive() {
    var here = window.location.pathname;
    var injected = document.querySelector('.dr-nav-injected');
    var childActive = false;

    var links = document.querySelectorAll(
      '.dr-nav-revealed__link, .dr-nav-injected__link'
    );
    for (var i = 0; i < links.length; i++) {
      var link = links[i];
      if (link.tagName !== 'A' || pathOf(link.href) !== here) continue;
      link.classList.add('md-nav__link--active');
      link.setAttribute('aria-current', 'page');
      if (link.classList.contains('dr-nav-revealed__link')) childActive = true;
    }

    if (childActive && injected) injected.classList.add('dr-nav-injected--here');
  }

  function paint(list, animate) {
    list.forEach(function (entry) {
      if (entry.p === 'at') drawSection(entry, animate);
      else drawUnder(entry, animate);
    });
    markActive();
  }

  return {
    entries: navEntries,
    drawn: drawn,
    keepDrawn: keepDrawn,
    paint: paint
  };
})();
